#!/usr/bin/env bash
# Build a bead mesh for every viewer plate and path-trace a still of each.
#
#   tools/render_plate_stills.sh                 # all plates -> data/plate_stills/
#   tools/render_plate_stills.sh vase sauce_tray # just those
#
# Measured on this container: ~14s to build a mesh, ~155s to render one at 64
# samples. All 72 plates is therefore a few hours, unattended, and it only has
# to be redone when a plate is re-sliced. Each step is skipped when its output
# already exists, so an interrupted run resumes instead of starting over.
set -euo pipefail
cd "$(dirname "$0")/.."

JOBS=tools/viewer/jobs
MESH=${MESH_DIR:-/tmp/plate_meshes}
OUT=${OUT_DIR:-data/plate_stills}
COLOR=${COLOR:-0.88,0.30,0.16}
SAMPLES=${SAMPLES:-64}
# 85 (blender_render's default) crops anything much taller than it is wide,
# and plates here run to 120mm tall on a 256mm bed. 38 fits them.
LENS=${LENS:-38}
mkdir -p "$MESH" "$OUT"

if [ $# -gt 0 ]; then
  names=("$@")
else
  names=()
  for f in "$JOBS"/*.js; do
    b=$(basename "$f" .js)
    [ "$b" = "index" ] || names+=("$b")
  done
fi

total=${#names[@]}
i=0
for n in "${names[@]}"; do
  i=$((i+1))
  src="$JOBS/$n.js"
  [ -f "$src" ] || { echo "[$i/$total] $n -- no such plate, skipped"; continue; }
  if [ ! -f "$OUT/$n.png" ]; then
    [ -f "$MESH/$n.ply" ] || python3 tools/gcode_to_mesh.py "$src" -o "$MESH/$n.ply"
    echo "[$i/$total] rendering $n"
    python3 tools/blender_render.py "$MESH/$n.ply" -o "$OUT/$n.png" \
        --color "$COLOR" --samples "$SAMPLES" --lens "$LENS" >/dev/null
  else
    echo "[$i/$total] $n -- already rendered, skipped"
  fi
done
echo "done: $OUT"
