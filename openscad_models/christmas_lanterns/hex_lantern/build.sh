#!/bin/bash
# Export the colour parts, or with "union" the one-body mesh the gate checks.
# ../lantern_mesh.py check *_{frame,glass,art,snow,bow}.stl proves the parts
# closed and disjoint.
# BOSL2 and the village's relief library live in the repo.
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
name=hex_lantern
mkdir -p logs
parts="frame glass art snow bow"
if [ "$1" = "union" ]; then
  # the parts again, sunk into each other, then welded by manifold3d
  for p in $parts; do
    openscad -D "part=\"$p\"" -D EMB=0.05 -o "logs/u_$p.stl" $name.scad > "logs/u_$p.log" 2>&1 &
  done
  wait
  python3 ../lantern_mesh.py union ${name}_union.stl $(for p in $parts; do echo logs/u_$p.stl; done)
  exit
fi
for p in $parts; do
  openscad -D "part=\"$p\"" -o "${name}_$p.stl" $name.scad > "logs/$p.log" 2>&1 &
done
wait
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
