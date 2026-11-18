#!/bin/bash
# Export the name_globe's colour parts and its one-body union. The name and year are
# parameters:  ./build.sh  or  ./build.sh "Olivia" 2026  (an empty year leaves it off)
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
N=${1-Olivia}; Y=${2-2026}
mkdir -p logs
for p in frame glass snow; do
  openscad -D "part=\"$p\"" -D "NAME=\"$N\"" -D "YEAR=\"$Y\"" -o name_globe_$p.stl name_globe.scad > logs/$p.log 2>&1 &
done
wait
# the one-body union through manifold: CGAL's own union of the touching parts left
# open edges on the ring (2026-11-18)
python3 ../../../tools/part_mesh.py union name_globe_union.stl name_globe_frame.stl name_globe_glass.stl name_globe_snow.stl
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
