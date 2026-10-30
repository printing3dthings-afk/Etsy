#!/usr/bin/env bash
# Chubby Axolotl: export every part (OpenSCAD's CGAL), each in the pose it
# prints in, four at a time. An export is skipped while it is newer than the
# .scad. Each goes through manifold3d once to drop CGAL's zero-area slivers;
# "mesh is not closed" in a log fails the part, since it means CGAL dropped
# a piece of it.
set -uo pipefail
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
mkdir -p parts logs
all="head gills eye s1 s2 s3 s4 tail leg_front_l leg_front_r leg_rear_l leg_rear_r"
one() {
    local p=$1 out=parts/$1.stl
    [ -s "$out" ] && [ "$out" -nt chubby_axolotl.scad ] && return
    openscad --export-format binstl -D "part=\"$p\"" -o "$out.tmp.stl" chubby_axolotl.scad > logs/$p.log 2>&1 \
        && ! grep -q "not closed" logs/$p.log \
        && python3 ../../../tools/part_mesh.py union "$out" "$out.tmp.stl" > /dev/null \
        && rm "$out.tmp.stl" && echo "  $p" || { echo "FAILED $p"; tail -3 logs/$p.log; }
}
n=0
for p in ${@:-$all}; do one $p & n=$((n+1)); [ $((n % 4)) -eq 0 ] && wait; done
wait
grep -l "ERROR\|WARNING" logs/*.log 2>/dev/null && echo "(warnings in the logs above)" || true
