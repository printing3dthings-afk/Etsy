#!/usr/bin/env bash
# Shop Calendar: export every part (CGAL, one at a time), each in the pose it
# prints in. An export is skipped while it is newer than the .scad. Each goes
# through manifold3d once: CGAL left zero-area slivers where the drums'
# lettering meets a face, and the round trip drops them, volume unchanged.
# CGAL's "mesh is not closed" fails the part: it means a piece was dropped
# from the export (the awning, then the facade's pegs, 2026-10-29).
set -uo pipefail
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
mkdir -p parts logs
all="base facade roof rod"
for d in day tens ones month; do all="$all drum_$d drum_${d}_text drum_${d}_print"; done
for p in ${@:-$all}; do
    out=parts/$p.stl
    [ -s "$out" ] && [ "$out" -nt shop_calendar.scad ] && continue
    echo "  $p"
    openscad --export-format binstl -D "part=\"$p\"" -o "$out.tmp.stl" shop_calendar.scad > logs/$p.log 2>&1 \
        && ! grep -q "not closed" logs/$p.log \
        && python3 ../../../tools/part_mesh.py union "$out" "$out.tmp.stl" > /dev/null \
        && rm "$out.tmp.stl" || { echo "FAILED $p"; tail -3 logs/$p.log; }
done
grep -l "ERROR\|WARNING" logs/*.log 2>/dev/null && echo "(warnings in the logs above)" || true
