#!/usr/bin/env bash
# Nesting Cats: exports every half (figures 0-3: bottom and top; 4: solid),
# checks the fits and writes the 3MF.
#   ./build.sh          everything
#   ./build.sh parts    only the STLs
set -euo pipefail
cd "$(dirname "$0")"
mode=${1:-}
export OPENSCADPATH=../../../assets/openscad_libs
mkdir -p parts logs
todo=()
for i in 0 1 2 3; do todo+=("$i bottom" "$i top"); done
todo+=("4 solid")
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
