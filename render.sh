#!/usr/bin/env bash
# Render all layout-algebra animations into ./videos/
#   ./render.sh            720p30  (default, ~2 min on 8 cores)
#   ./render.sh -ql        480p15  quick preview
#   ./render.sh -qh        1080p60
# manim lives in ./.manim_pkgs (numpy 2) so it doesn't break the main env (numpy 1.26).
set -euo pipefail
cd "$(dirname "$0")"
Q="${1:--qm}"
mkdir -p videos
export PYTHONPATH="$PWD/.manim_pkgs:$PWD/scenes"
for f in scenes/s0*.py; do
  python -m manim "$Q" --media_dir .media "$f" -a >".media_$(basename "$f" .py).log" 2>&1 &
done
wait
find .media/videos -path '*partial*' -prune -o -name '*.mp4' -print | while read -r v; do cp "$v" videos/; done
rm -f .media_*.log
ls -1 videos
