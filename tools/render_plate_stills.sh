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
# Deliberately NOT `set -e`: this is a multi-hour unattended run over 72
# plates, and one plate failing is not a reason to abandon the other 71. Each
# failure is recorded and reported at the end instead.
set -uo pipefail
cd "$(dirname "$0")/.."

JOBS=tools/viewer/jobs
MESH=${MESH_DIR:-/tmp/plate_meshes}
OUT=${OUT_DIR:-data/plate_stills}
COLOR=${COLOR:-0.88,0.30,0.16}
SAMPLES=${SAMPLES:-64}
# One lens for every plate. Framing no longer depends on it -- blender_render
# scales camera distance with focal length now, so the lens sets perspective
# and nothing else, and the per-plate lens guessing this script used to do is
# gone with the coupling that made it necessary.
LENS=${LENS:-55}
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
failed=()
for n in "${names[@]}"; do
  i=$((i+1))
  src="$JOBS/$n.js"
  [ -f "$src" ] || { echo "[$i/$total] $n -- no such plate, skipped"; continue; }
  if [ ! -f "$OUT/$n.png" ]; then
    [ -f "$MESH/$n.ply" ] || python3 tools/gcode_to_mesh.py "$src" -o "$MESH/$n.ply"
    echo "[$i/$total] rendering $n"
    if ! python3 tools/blender_render.py "$MESH/$n.ply" -o "$OUT/$n.png" \
        --color "$COLOR" --samples "$SAMPLES" --lens "$LENS" >/dev/null; then
      echo "[$i/$total] FAILED: $n"
      failed+=("$n")
    fi
    # 72 meshes at ~19MB each is 1.4GB of scratch nobody needs once the still
    # exists, and disk here is a fixed per-session allowance.
    rm -f "$MESH/$n.ply"
  else
    echo "[$i/$total] $n -- already rendered, skipped"
  fi
done
if [ ${#failed[@]} -gt 0 ]; then
  echo "done with ${#failed[@]} failure(s): ${failed[*]}"
  echo "re-run the same command to retry just those -- finished plates are skipped"
else
  echo "done: all $total plates rendered into $OUT"
fi
