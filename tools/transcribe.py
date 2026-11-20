"""Transcribe audio with faster-whisper, decoding via ffmpeg (avoids PyAV issues).
Usage: python tools/transcribe.py <audio_or_video> [--words] [--model small.en]
"""
import subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)

args = sys.argv[1:]
model = args[args.index("--model") + 1] if "--model" in args else "small.en"
words = "--words" in args
m = WhisperModel(model, device="cpu", compute_type="int8")
segs, _ = m.transcribe(load(args[0]), beam_size=5, word_timestamps=words)
for s in segs:
    if words:
        for w in s.words:
            print(f"{w.start:.2f}\t{w.end:.2f}\t{w.word.strip()}")
    else:
        print(f"[{s.start:.2f}-{s.end:.2f}] {s.text.strip()}")
