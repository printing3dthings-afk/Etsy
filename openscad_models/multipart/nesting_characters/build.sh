#!/usr/bin/env bash
# Nesting Cats: exports every part (figures 0-3: the bottom, and the top in its
# four colours; 4: the solid cat in its four colours),
# checks the fits and writes the 3MF.
#   ./build.sh          everything
#   ./build.sh parts    only the STLs
set -euo pipefail
cd "$(dirname "$0")"
mode=${1:-}
export OPENSCADPATH=../../../assets/openscad_libs
mkdir -p parts logs
todo=()
for i in 0 1 2 3; do todo+=("$i bottom"); for c in body trim dark pink; do todo+=("$i top_$c"); done; done
for c in body trim dark pink; do todo+=("4 solid_$c"); done
for t in "${todo[@]}"; do
    set -- $t; out=parts/cat${1}_$2.stl
    [ -s "$out" ] && [ "$out" -nt nesting_cats.scad ] && [ "$out" -nt ../thread_lib.scad ] && continue
    ( openscad -D fig=$1 -D "part=\"$2\"" -o "$out.tmp.stl" nesting_cats.scad > "logs/cat${1}_$2.log" 2>&1 \
        && mv "$out.tmp.stl" "$out" || echo "FAILED $1 $2" ) &
    while [ "$(jobs -rp | wc -l)" -ge "${JOBS:-3}" ]; do sleep 1; done
done
wait
grep -l "ERROR\|WARNING" logs/cat*.log && echo "(see the logs above)" || true
[ "$mode" = parts ] && exit 0
python3 check_cats.py parts
