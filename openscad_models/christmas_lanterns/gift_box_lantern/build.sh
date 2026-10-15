#!/bin/bash
# Export the colour parts, or with "union" the two one-body meshes the gate
# checks (the box, the lid). tools/part_mesh.py check proves the colour parts
# closed and disjoint. BOSL2 and the village's relief library live in the repo.
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
name=gift_box_lantern
mkdir -p logs
parts="frame glass art lid ribbon"
if [ "$1" = "union" ]; then
  # the parts again, sunk into each other, then welded by manifold3d
  for p in $parts; do
    openscad -D "part=\"$p\"" -D EMB=0.05 -o "logs/u_$p.stl" $name.scad > "logs/u_$p.log" 2>&1 &
  done
  wait
  python3 ../../../tools/part_mesh.py union ${name}_box_union.stl logs/u_frame.stl logs/u_glass.stl logs/u_art.stl
  python3 ../../../tools/part_mesh.py union ${name}_lid_union.stl logs/u_lid.stl logs/u_ribbon.stl
  exit
fi
for p in $parts; do
  openscad -D "part=\"$p\"" -o "${name}_$p.stl" $name.scad > "logs/$p.log" 2>&1 &
done
wait
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
