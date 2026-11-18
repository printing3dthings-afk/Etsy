#!/bin/bash
# Export the name_ring's colour parts and its one-body union. The name and year are
# parameters:  ./build.sh  or  ./build.sh "Olivia" 2026  (an empty year leaves it off)
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
N=${1-Olivia}; Y=${2-2026}
mkdir -p logs
for p in frame accent; do
  openscad -D "part=\"$p\"" -D "NAME=\"$N\"" -D "YEAR=\"$Y\"" -o name_ring_$p.stl name_ring.scad > logs/$p.log 2>&1 &
done
wait
# the one-body union through manifold: CGAL's own union of the touching parts left
# open edges on the ring (2026-11-18)
python3 ../../../tools/part_mesh.py union name_ring_union.stl name_ring_frame.stl name_ring_accent.stl
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
