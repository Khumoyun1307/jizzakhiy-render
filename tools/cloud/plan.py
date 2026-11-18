"""Build the GitHub Actions render matrix for one episode.

Usage: python tools/cloud/plan.py <episode-id> [S02,S11,...]
Prints GITHUB_OUTPUT lines: matrix=<json>, count=<n>, episode=<id>.
Scene types come from 01_script/scenes.json `visual` (manim | slide | hyperframes).
Longest kinds first (manim, then slide, then hyperframes) so they start first.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORDER = {"manim": 0, "slide": 1, "hyperframes": 2}


def main() -> None:
    ep = sys.argv[1].strip()
    want = [s.strip().upper() for s in (sys.argv[2] if len(sys.argv) > 2 else "").replace(" ", ",").split(",") if s.strip()]
    epdir = ROOT / "episodes" / ep
    scenes = json.loads((epdir / "01_script/scenes.json").read_text(encoding="utf-8"))["scenes"]
    known = {s["id"]: s for s in scenes}
    bad = [s for s in want if s not in known]
    if bad:
        sys.exit(f"unknown scene ids: {bad}")
    items = []
    for s in scenes:
        if want and s["id"] not in want:
            continue
        kind = s.get("visual")
        if kind not in ORDER:
            sys.exit(f"{s['id']}: visual '{kind}' cannot be rendered in the cloud")
        items.append({"id": s["id"], "type": kind})
    items.sort(key=lambda x: (ORDER[x["type"]], x["id"]))
    by_type = {}
    for it in items:
        by_type.setdefault(it["type"], []).append(it["id"])
    for k, v in by_type.items():
        print(f"{k}: {' '.join(v)}", file=sys.stderr)
    print(f"matrix={json.dumps({'include': items})}")
    print(f"count={len(items)}")
    print(f"episode={ep}")
    print(f"groups={json.dumps(by_type)}")


if __name__ == "__main__":
    main()
