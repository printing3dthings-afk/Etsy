#!/usr/bin/env bash
# Candy Lighthouse: export every part (CGAL, one at a time), each in the pose it
# prints in. An export is skipped while it is newer than the .scad.
set -uo pipefail
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
mkdir -p parts logs
for p in ${@:-tower_print tower tower_red tower_blue wheel lantern lantern_up roof head}; do
    out=parts/$p.stl
    [ -s "$out" ] && [ "$out" -nt candy_lighthouse.scad ] && continue
    echo "  $p"
    openscad --export-format binstl -D "part=\"$p\"" -o "$out.tmp.stl" candy_lighthouse.scad > logs/$p.log 2>&1 \
        && mv "$out.tmp.stl" "$out" || { echo "FAILED $p"; tail -3 logs/$p.log; }
done
grep -l "ERROR\|WARNING" logs/*.log 2>/dev/null && echo "(warnings in the logs above)" || true
