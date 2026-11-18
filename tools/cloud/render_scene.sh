#!/usr/bin/env bash
# Render ONE scene of an episode exactly like the local pipeline does.
# Usage: bash tools/cloud/render_scene.sh <episode-id> <scene-id> <manim|slide|hyperframes> <out-dir>
# Uses the pushed inputs as-is (slide props and the episode's HyperFrames copy are not regenerated).
set -euo pipefail
EPID=$1; SID=$2; TYPE=$3; OUT=$(realpath -m "$4")
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
EP="$ROOT/episodes/$EPID"; VIS="$EP/02_visuals"
mkdir -p "$OUT"
echo "runner: nproc=$(nproc) $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2) mem=$(free -g | awk '/Mem/{print $2}')G"
T0=$(date +%s)

case "$TYPE" in
  manim)
    FILE=$(grep -l -E "^class ${SID}\(" "$VIS"/manim/*.py | head -1)
    [ -n "$FILE" ] || { echo "no class $SID in $VIS/manim/*.py"; exit 1; }
    MEDIA="${RUNNER_TEMP:-/tmp}/manim"
    (cd "$ROOT" && python -m manim render -qh --fps 24 --media_dir "$MEDIA" "$FILE" "$SID")
    SRC="$MEDIA/videos/$(basename "$FILE" .py)/1080p24/$SID.mp4"
    cp "$SRC" "$OUT/$SID.mp4"
    ;;
  slide)
    PROPS="$VIS/slides/$SID.json"
    [ -f "$PROPS" ] || { echo "missing $PROPS"; exit 1; }
    (cd "$ROOT/remotion" && npx remotion render src/index.ts Scene "$OUT/$SID.mp4" --props="$PROPS" --muted --log=error)
    ;;
  hyperframes)
    BLOCK=$(python3 -c "import json,sys; s={x['id']:x for x in json.load(open(sys.argv[1],encoding='utf-8'))['scenes']}[sys.argv[2]]; print(s.get('block',''))" "$EP/01_script/scenes.json" "$SID")
    case "$BLOCK" in intro) T=intro ;; outro) T=outro ;; *) echo "$SID: block '$BLOCK' is not intro/outro"; exit 1 ;; esac
    HF="$VIS/hyperframes"; [ -d "$HF/$T" ] || HF="$ROOT/hyperframes"
    [ -f "$HF/${T}_vars.json" ] || { echo "missing $HF/${T}_vars.json"; exit 1; }
    (cd "$HF" && npx --yes hyperframes@0.9.59 render "$T" --fps 24 --quality delivery \
       --variables-file "${T}_vars.json" --strict-variables -o "$OUT/$SID.mp4")
    ;;
  *) echo "unknown type $TYPE"; exit 1 ;;
esac

T1=$(date +%s)
DUR=""
command -v ffprobe >/dev/null && DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/$SID.mp4")
echo "RENDERED $SID type=$TYPE seconds=$((T1-T0)) duration=$DUR nproc=$(nproc)"
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && echo "| $SID | $TYPE | $((T1-T0)) s | $DUR s | $(nproc) |" >> "$GITHUB_STEP_SUMMARY"
exit 0
