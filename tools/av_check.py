"""Technical AV report for a rendered lesson (used by qa-av and editor).

Usage: .venv/Scripts/python.exe tools/av_check.py <video.mp4> [--short]
Prints specs, decode errors, loudness, black/freeze/silence segments, and PASS/FAIL per spec item.
"""
import json
import re
import subprocess
import sys


def run(args: list[str]) -> str:
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.stdout + p.stderr


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    short = "--short" in sys.argv
    want = (1080, 1920, 30) if short else (1920, 1080, 24)

    info = json.loads(run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path]) or "{}")
    v = next((s for s in info.get("streams", []) if s["codec_type"] == "video"), {})
    a = next((s for s in info.get("streams", []) if s["codec_type"] == "audio"), {})
    num, den = (v.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    fps = round(int(num) / int(den or 1), 3) if int(den or 1) else 0
    dur = float(info.get("format", {}).get("duration", 0))
    results = []

    def check(name: str, ok: bool, detail: str) -> None:
        results.append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    check("resolution", (v.get("width"), v.get("height")) == want[:2], f"{v.get('width')}x{v.get('height')}")
    check("fps", abs(fps - want[2]) < 0.01, str(fps))
    check("video codec", v.get("codec_name") == "h264" and v.get("pix_fmt") == "yuv420p", f"{v.get('codec_name')} {v.get('profile')} {v.get('pix_fmt')}")
    check("audio", a.get("codec_name") == "aac" and a.get("sample_rate") == "48000", f"{a.get('codec_name')} {a.get('sample_rate')} Hz ch={a.get('channels')}")
    print(f"duration: {dur:.2f}s ({int(dur // 60)}:{dur % 60:05.2f})")

    errs = run(["ffmpeg", "-v", "error", "-i", path, "-f", "null", "-"]).strip()
    check("decode errors", not errs, "0" if not errs else errs[:300])

    ln = run(["ffmpeg", "-hide_banner", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", ln, re.S)
    if m:
        j = json.loads(m.group(0))
        i, tp = float(j["input_i"]), float(j["input_tp"])
        check("loudness", -15.0 <= i <= -13.0, f"{i} LUFS")
        check("true peak", tp <= -1.0, f"{tp} dBTP")

    det = run(["ffmpeg", "-hide_banner", "-i", path, "-vf", "blackdetect=d=1:pix_th=0.10,freezedetect=n=0.003:d=3",
               "-af", "silencedetect=n=-45dB:d=2", "-f", "null", "-"])
    blacks = re.findall(r"black_start:(\S+) black_end:(\S+)", det)
    freezes = re.findall(r"freeze_start: (\S+)", det)
    silences = re.findall(r"silence_start: (\S+)", det)
    check("black > 1s", not blacks, str(blacks) if blacks else "none")
    print(f"[INFO] freezes > 3s at: {freezes or 'none'} (OK only if they are planned pauses or static slides)")
    print(f"[INFO] silences > 2s at: {silences or 'none'} (OK only during quiz/homework pauses)")
    print("OVERALL:", "PASS" if all(results) else "FAIL")


if __name__ == "__main__":
    main()
