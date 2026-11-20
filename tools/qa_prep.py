"""QA prep for a finished master: word transcript + review frames.

Usage: python tools/qa_prep.py <final.mp4> [--edit-log edit_log.md] [--out DIR] [--model small.en] [--every 2]
Writes into --out (default: the video's folder):
  transcript_words.json  {"model", "words": [{word,start,end}], "segments": [{start,end,text}]}  (faster-whisper)
  frames/t0000.0.jpg …   one 1920x1080 JPG (q 3) every 2 s
  frames/S09_start.jpg   first frame of every scene, from the "Scene → start timecode" table in edit_log.md
Audio is decoded with the ffmpeg CLI (not PyAV), so it works on Windows and Linux.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np


def sh(args):
    p = subprocess.run([str(a) for a in args], capture_output=True)
    if p.returncode != 0:
        sys.exit(f"failed: {' '.join(map(str, args))[:300]}\n{p.stderr.decode(errors='replace')[-2000:]}")
    return p.stdout


def scene_starts(edit_log: Path):
    out = []
    for line in edit_log.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(S\d+[A-Za-z0-9-]*)\s*\|[^|]*\|\s*(\d+):(\d+(?:\.\d+)?)\s*\|\s*\d+\s*\|", line)
        if m:
            out.append((m.group(1), int(m.group(2)) * 60 + float(m.group(3))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--edit-log")
    ap.add_argument("--out")
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--every", type=float, default=2.0)
    ap.add_argument("--no-transcript", action="store_true")
    a = ap.parse_args()
    video = Path(a.video).resolve()
    out = Path(a.out).resolve() if a.out else video.parent
    frames = out / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    edit_log = Path(a.edit_log) if a.edit_log else video.parent / "edit_log.md"

    # ---- frames every N s (exact timestamps: frame at t = k*N)
    dur = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video]).decode().strip())
    for old in frames.glob("t*.jpg"):
        old.unlink()
    sh(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps=1/{a.every}:start_time=0:round=down,scale=1920:1080",
        "-q:v", "3", str(frames / "tmp_%05d.jpg")])
    for f in sorted(frames.glob("tmp_*.jpg")):
        k = int(f.stem.split("_")[1]) - 1
        f.rename(frames / f"t{k * a.every:06.1f}.jpg")
    n_grid = len(list(frames.glob("t*.jpg")))

    # ---- first frame of every scene
    starts = scene_starts(edit_log) if edit_log.exists() else []
    for sid, t in starts:
        sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{t + 0.001:.3f}", "-i", video, "-frames:v", "1",
            "-vf", "scale=1920:1080", "-q:v", "3", frames / f"{sid}_start.jpg"])
    print(f"frames: {n_grid} grid (every {a.every:g} s of {dur:.1f} s) + {len(starts)} scene starts -> {frames}")

    # ---- transcript
    if not a.no_transcript:
        from faster_whisper import WhisperModel
        pcm = sh(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"])
        audio = np.frombuffer(pcm, dtype="<f4").copy()
        model = WhisperModel(a.model, device="cpu", compute_type="int8")
        segs, _ = model.transcribe(audio, language="en", word_timestamps=True, beam_size=5, vad_filter=False)
        words, segments = [], []
        for s in segs:
            segments.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
            for w in s.words or []:
                words.append({"start": round(w.start, 2), "end": round(w.end, 2), "word": w.word.strip()})
        (out / "transcript_words.json").write_text(json.dumps(
            {"model": a.model, "source": video.name, "words": words, "segments": segments}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"transcript: {len(words)} words, {len(segments)} segments -> {out / 'transcript_words.json'}")


if __name__ == "__main__":
    main()
