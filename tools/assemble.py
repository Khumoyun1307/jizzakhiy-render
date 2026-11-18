"""Assemble a lesson master from rendered scenes + narration clips (reproduces the Lesson 38 edit).

Usage:
  python tools/assemble.py <episode_dir> [--scenes-dir DIR] [--fallback-dir DIR] [--out DIR] [--no-check]

Inputs (episode folder):
  01_script/scenes.json          scene order (+ optional 01_script/chapters.json: [{"scene": "S05", "title": "..."}])
  02_visuals/scenes/<id>.mp4     (or --scenes-dir, then --fallback-dir)
  03_audio/blocks.json           clip ids per scene, caption text, pause_after_seconds
  03_audio/clips/<clip>.wav      narration; 03_audio/words/<clip>.json  whisper word times (captions)
  03_audio/caption_fixes.json    optional {"spoken form": "caption form"}
Outputs (--out, default <episode>/04_edit): final.mp4, captions.srt, chapters.txt, edit_log.md, av_check.txt

Edit model (same as the L38 editor):
- scene start = sum of the previous scenes' real frame counts / 24; hard cuts, no time-stretch.
- in each scene the first clip starts at offset 0, each next clip at prev offset + duration + pause_after.
- if a scene's audio is longer than its video, the last frame is held (tpad clone).
- clips placed sample-exact on one timeline at their native rate, then 48 kHz stereo,
  alimiter -6 dBFS, two-pass loudnorm I=-14 TP=-1.5 LRA=11 (linear).
- video: scale to tv range yuv420p, concat, fps 24; libx264 High preset slow CRF 18, bt709; AAC-LC 192k 48k stereo; faststart.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import math
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

FPS = 24
HERE = Path(__file__).resolve().parent


def sh(args, **kw):
    p = subprocess.run([str(a) for a in args], capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if p.returncode != 0:
        sys.exit(f"command failed ({p.returncode}): {' '.join(map(str, args))[:400]}\n{p.stderr[-3000:]}")
    return p.stdout + p.stderr


def tc(s: float) -> str:
    m = int(s // 60)
    return f"{m}:{s - 60 * m:06.3f}"


def srt_tc(s: float) -> str:
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def frame_count(mp4: Path) -> int:
    out = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
              "-show_entries", "stream=nb_read_packets,r_frame_rate", "-of", "json", mp4])
    st = json.loads(out[out.index("{"):])["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    if abs(int(num) / int(den) - FPS) > 0.01:
        sys.exit(f"{mp4.name}: {st['r_frame_rate']} fps, expected {FPS}")
    return int(st["nb_read_packets"])


def read_wav(p: Path):
    with wave.open(str(p)) as w:
        sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    if sw != 2:
        sys.exit(f"{p.name}: only 16-bit PCM wav supported")
    a = np.frombuffer(raw, dtype="<i2").astype(np.int32)
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1).astype(np.int32)
    return sr, a


# ------------------------------------------------------------------------------------------ captions
DIGITS = {w: str(i) for i, w in enumerate("zero one two three four five six seven eight nine".split())}
REF = r"(Lemma|Theorem|Definition|Example|Corollary|Exercise|Problem|Section|Figure|Chapter)"


def caption_text(t: str, fixes: dict) -> str:
    for a, b in fixes.items():
        t = t.replace(a, b)
    t = re.sub(r"\b[A-Z](?: [A-Z]\b)+(?: s\b)?", lambda m: m.group(0).replace(" ", ""), t)

    def num(m):
        ws = m.group(2).split()
        return m.group(1) + " " + "".join("." if w == "point" else DIGITS[w] for w in ws)
    dw = "|".join(DIGITS)
    t = re.sub(REF + r" ((?:%s)(?: (?:%s|point))*)\b" % (dw, dw), num, t)
    return re.sub(r"\s+", " ", t).strip()


def norm_chars(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def align_words(text: str, wdata) -> list[tuple[str, float, float]]:
    """Give every display word of `text` a (start, end) from whisper words, by character alignment."""
    disp = text.split()
    ws = [w for w in (wdata.get("words", wdata) if isinstance(wdata, dict) else wdata)]
    a_chars, a_owner = [], []
    for i, w in enumerate(disp):
        for c in norm_chars(w):
            a_chars.append(c); a_owner.append(i)
    b_chars, b_time = [], []
    for w in ws:
        cs = norm_chars(str(w.get("word", w.get("text", ""))))
        s, e = float(w["start"]), float(w["end"])
        for k, c in enumerate(cs):
            b_chars.append(c)
            b_time.append((s + (e - s) * k / len(cs), s + (e - s) * (k + 1) / len(cs)))
    times = [[None, None] for _ in disp]
    sm = difflib.SequenceMatcher(None, "".join(a_chars), "".join(b_chars), autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            i = a_owner[blk.a + k]
            s, e = b_time[blk.b + k]
            if times[i][0] is None or s < times[i][0]:
                times[i][0] = s
            if times[i][1] is None or e > times[i][1]:
                times[i][1] = e
    # interpolate words with no matched characters
    known = [i for i, t in enumerate(times) if t[0] is not None]
    t_end = float(ws[-1]["end"]) if ws else 1.0
    for i, t in enumerate(times):
        if t[0] is not None:
            continue
        prev = max([k for k in known if k < i], default=None)
        nxt = min([k for k in known if k > i], default=None)
        a = times[prev][1] if prev is not None else 0.0
        b = times[nxt][0] if nxt is not None else t_end
        lo = prev if prev is not None else -1
        hi = nxt if nxt is not None else len(disp)
        f0 = (i - lo) / (hi - lo)
        f1 = (i - lo + 1) / (hi - lo)
        t[0], t[1] = a + (b - a) * f0 * 0.98, a + (b - a) * f1 * 0.98
    return [(disp[i], times[i][0], max(times[i][1], times[i][0] + 0.05)) for i in range(len(disp))]


def wrap2(text: str, width: int = 42):
    if len(text) <= width:
        return [text]
    words = text.split(" ")
    best = None
    for k in range(1, len(words)):
        a, b = " ".join(words[:k]), " ".join(words[k:])
        if len(a) > width or len(b) > width:
            continue
        score = max(len(a), len(b)) - (8 if a[-1] in ",.;:?!" else 0)
        if best is None or score < best[0]:
            best = (score, [a, b])
    return best[1] if best else None


def make_cues(words, clip_end: float):
    cues, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        text = " ".join(x[0] for x in cur)
        dur = w[2] - cur[0][1]
        last = i == len(words) - 1
        if last:
            cues.append(cur); break
        nxt = words[i + 1]
        cand = text + " " + nxt[0]
        sentence = w[0][-1] in ".?!" or w[0].endswith('."')
        clause = w[0][-1] in ",;"
        if (sentence and dur >= 1.0) or wrap2(cand) is None or (nxt[2] - cur[0][1]) > 6.0 \
                or (clause and len(text) >= 45 and dur >= 1.0):
            cues.append(cur); cur = []
    if len(cues) > 1 and cues[-1][-1][2] - cues[-1][0][1] < 1.0 and wrap2(" ".join(x[0] for x in cues[-2] + cues[-1])):
        tail = cues.pop()
        cues[-1] = cues[-1] + tail
    out = []
    for c in cues:
        out.append([c[0][1], c[-1][2] + 0.15, " ".join(x[0] for x in c)])
    for k, c in enumerate(out):
        limit = out[k + 1][0] - 0.04 if k + 1 < len(out) else clip_end
        c[1] = min(c[1], limit)
        if c[1] - c[0] < 1.0:
            c[1] = min(c[0] + 1.0, limit)
        c[1] = min(c[1], c[0] + 6.0)
    return out


# ------------------------------------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--scenes-dir")
    ap.add_argument("--fallback-dir")
    ap.add_argument("--out")
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--keep-work", action="store_true")
    a = ap.parse_args()

    ep = Path(a.episode).resolve()
    out = Path(a.out).resolve() if a.out else ep / "04_edit"
    out.mkdir(parents=True, exist_ok=True)
    work = out / "work"
    work.mkdir(exist_ok=True)
    dirs = [Path(d).resolve() for d in (a.scenes_dir, a.fallback_dir) if d] or [ep / "02_visuals/scenes"]
    meta = json.loads((ep / "01_script/scenes.json").read_text(encoding="utf-8"))
    scenes = meta["scenes"]
    blocks = json.loads((ep / "03_audio/blocks.json").read_text(encoding="utf-8"))
    fixes_p = ep / "03_audio/caption_fixes.json"
    fixes = json.loads(fixes_p.read_text(encoding="utf-8")) if fixes_p.exists() else {}

    # ---- scene videos and clip placement
    rows, clips, t = [], [], 0.0
    sr_all = None
    for s in scenes:
        sid = s["id"]
        mp4 = next((d / f"{sid}.mp4" for d in dirs if (d / f"{sid}.mp4").exists()), None)
        if mp4 is None:
            sys.exit(f"missing scene video {sid}.mp4 in {[str(d) for d in dirs]}")
        frames = frame_count(mp4)
        vlen = frames / FPS
        off = 0.0
        for b in [b for b in blocks if b["scene"] == sid]:
            sr, data = read_wav(ep / "03_audio/clips" / f"{b['id']}.wav")
            if sr_all is None:
                sr_all = sr
            if sr != sr_all:
                sys.exit(f"{b['id']}: {sr} Hz, other clips are {sr_all} Hz")
            clips.append({"id": b["id"], "scene": sid, "start": t + off, "len": len(data) / sr, "data": data, "block": b})
            off += len(data) / sr + float(b.get("pause_after_seconds", 0) or 0)
        hold = 0
        if off > vlen + 1e-6:
            hold = math.ceil((off - vlen) * FPS)
        rows.append({"id": sid, "block": s.get("block", ""), "mp4": mp4, "start": t, "frames": frames + hold,
                     "hold": hold, "vlen": (frames + hold) / FPS, "alen": off})
        t += (frames + hold) / FPS
    total = t
    total_frames = sum(r["frames"] for r in rows)
    print(f"{len(rows)} scenes, {total_frames} frames = {total:.3f} s, {len(clips)} clips @ {sr_all} Hz")

    # ---- narration timeline (sample exact)
    n = int(round(total * sr_all))
    buf = np.zeros(n, dtype=np.int32)
    for c in clips:
        i0 = int(round(c["start"] * sr_all))
        d = c["data"][: max(0, n - i0)]
        buf[i0:i0 + len(d)] += d
    buf = np.clip(buf, -32768, 32767).astype("<i2")
    nar = work / "narration.wav"
    with wave.open(str(nar), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr_all); w.writeframes(buf.tobytes())

    pre = "aresample=48000,pan=stereo|c0=c0|c1=c0,alimiter=limit=0.5:attack=3:release=60:level=false"
    p1 = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", nar, "-af", pre + ",loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m1 = json.loads(re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", p1, re.S)[-1])
    ln2 = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
           "measured_thresh={input_thresh}:offset={target_offset}:linear=true:print_format=json").format(**m1)
    anorm = work / "audio_norm.wav"
    p2 = sh(["ffmpeg", "-y", "-hide_banner", "-nostats", "-i", nar, "-af", pre + "," + ln2 + ",aresample=48000",
             "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", anorm])
    m2 = json.loads(re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", p2, re.S)[-1])
    print(f"loudnorm pass1 I {m1['input_i']} TP {m1['input_tp']} LRA {m1['input_lra']}; pass2 {m2.get('normalization_type')}")

    # ---- video
    args = ["ffmpeg", "-y", "-hide_banner", "-nostats"]
    for r in rows:
        args += ["-i", r["mp4"]]
    args += ["-i", anorm]
    fc = []
    for i, r in enumerate(rows):
        f = f"[{i}:v]scale=in_range=auto:out_range=tv,format=yuv420p,setsar=1"
        if r["hold"]:
            f += f",tpad=stop_mode=clone:stop={r['hold']}"
        fc.append(f + f"[v{i}]")
    fc.append("".join(f"[v{i}]" for i in range(len(rows))) + f"concat=n={len(rows)}:v=1:a=0,fps={FPS}[vout]")
    final = out / "final.mp4"
    args += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", f"{len(rows)}:a",
             "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
             "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
             "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
             "-frames:v", str(total_frames), "-movflags", "+faststart", final]
    print("encoding final.mp4 ...", flush=True)
    sh(args)

    # ---- captions
    cues = []
    for c in clips:
        text = caption_text(c["block"]["text"], fixes)
        wp = ep / "03_audio/words" / f"{c['id']}.json"
        wd = json.loads(wp.read_text(encoding="utf-8")) if wp.exists() else []
        if not (wd.get("words") if isinstance(wd, dict) else wd):
            wd = [{"word": x, "start": c["len"] * i / len(text.split()), "end": c["len"] * (i + 1) / len(text.split())}
                  for i, x in enumerate(text.split())]
        ws = align_words(text, wd)
        for s0, s1, txt in make_cues(ws, c["len"]):
            cues.append((c["start"] + s0, c["start"] + s1, wrap2(txt) or [txt]))
    with open(out / "captions.srt", "w", encoding="utf-8", newline="\n") as f:
        for k, (s0, s1, lines) in enumerate(cues, 1):
            f.write(f"{k}\n{srt_tc(s0)} --> {srt_tc(s1)}\n" + "\n".join(lines) + "\n\n")

    # ---- chapters
    chp = ep / "01_script/chapters.json"
    if chp.exists():
        spec = {x["scene"]: x["title"] for x in json.loads(chp.read_text(encoding="utf-8"))}
        marks = [(r["start"], spec[r["id"]]) for r in rows if r["id"] in spec]
    else:
        names = {"intro": "Intro", "hook": None, "recap": "Recap", "build-up": "Key ideas", "quiz": "Quiz",
                 "worked-example": "Worked example", "homework": "Homework", "outro": None}
        marks = []
        for r in rows:
            name = names.get(r["block"], r["block"].replace("-", " ").capitalize() or None)
            if name and (not marks or marks[-1][1] != name):
                marks.append((r["start"], name))
    if not marks or marks[0][0] > 0:
        marks.insert(0, (0.0, marks[0][1] if marks and marks[0][0] < 1 else "Intro"))
    marks[0] = (0.0, marks[0][1])
    merged = []
    for i, (s0, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else total
        if merged and end - s0 < 10:
            continue
        merged.append((s0, name))
    chap_lines = [f"{int(s0 // 60)}:{int(s0 % 60):02d} {name}" for s0, name in merged]
    (out / "chapters.txt").write_text("\n".join(chap_lines) + "\n", encoding="utf-8")

    # ---- av check
    av = ""
    if not a.no_check:
        p = subprocess.run([sys.executable, str(HERE / "av_check.py"), str(final)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        av = p.stdout + p.stderr
        (out / "av_check.txt").write_text(av, encoding="utf-8")
        print(av)

    # ---- edit log
    size = final.stat().st_size / 1e6
    L = [f"# Edit log: {meta.get('title', ep.name)} ({ep.name})", "",
         f"Assembled {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC by `tools/assemble.py`. "
         f"Output `final.mp4`: **{tc(total)} ({total:.3f} s, {total_frames} frames)**, {size:.1f} MB.", "",
         "## Timing model",
         "- First clip at scene offset 0.0 s; each next clip at previous offset + duration + pause_after. "
         "Scene start = sum of the previous scenes' frame counts / 24. Hard cuts, no time-stretch, no music bed.",
         f"- Held last frames: {', '.join(f'{r['id']} +{r['hold']} f' for r in rows if r['hold']) or 'none'}.", "",
         "## Scene → start timecode", "| Scene | Block | Start | Frames | Video s | Audio s (incl. pauses) |",
         "|---|---|---|---|---|---|"]
    L += [f"| {r['id']} | {r['block']} | {tc(r['start'])} | {r['frames']} | {r['vlen']:.3f} | {r['alen']:.2f} |" for r in rows]
    L += ["", "## Clip placement", "| Clip | Start | Length s |", "|---|---|---|"]
    L += [f"| {c['id']} | {tc(c['start'])} | {c['len']:.2f} |" for c in clips]
    L += ["", "## Settings",
          f"- Narration: clips ({sr_all} Hz) placed sample-exact on one timeline, aresample 48 kHz, duplicated to stereo.",
          "- Peak control: `alimiter=limit=0.5:attack=3:release=60:level=false` (-6 dBFS).",
          f"- Two-pass loudnorm I=-14, TP=-1.5, LRA=11. Pass 1 measured I {m1['input_i']}, TP {m1['input_tp']}, "
          f"LRA {m1['input_lra']}, thresh {m1['input_thresh']}, offset {m1['target_offset']}. "
          f"Pass 2 linear=true → normalization_type **{m2.get('normalization_type')}**.",
          "- Video: `scale=in_range=auto:out_range=tv,format=yuv420p,setsar=1` per scene, concat, fps=24.",
          "- Encode: libx264 High, preset slow, CRF 18, yuv420p, tv range, bt709, 24 fps; AAC-LC 192 kbps 48 kHz stereo; +faststart.",
          "", f"## Captions (`captions.srt`, {len(cues)} cues)",
          "- Text from `03_audio/blocks.json` (spelled letters joined: N F A → NFA; spoken numbers after Lemma/Theorem/... → digits; "
          "plus `03_audio/caption_fixes.json` if present), aligned at character level to `words/<clip>.json`.",
          "- ≤ 2 lines × 42 chars, 1–6 s, cues never cross a clip boundary, end ≤ 0.15 s after the last word.",
          "", "## Chapters (`chapters.txt`)",
          "- From `01_script/chapters.json`." if chp.exists() else "- Auto from scene blocks (hook folded into Intro, outro into the last chapter, chapters < 10 s merged).",
          *[f"  - {x}" for x in chap_lines], ""]
    if av:
        L += ["## Checks (`tools/av_check.py final.mp4`)", "```", av.strip(), "```", ""]
    (out / "edit_log.md").write_text("\n".join(L), encoding="utf-8")
    if not a.keep_work:
        shutil.rmtree(work, ignore_errors=True)
    print(f"done: {final} {tc(total)}")


if __name__ == "__main__":
    main()
