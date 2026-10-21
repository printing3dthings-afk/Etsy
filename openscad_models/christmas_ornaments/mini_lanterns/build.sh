#!/bin/bash
# Export the six mini-lantern ornaments' colour parts and one-body unions:
#   ./build.sh          (all six)      ./build.sh 3 5    (some)
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
mkdir -p logs
for n in ${*:-1 2 3 4 5 6}; do
  for p in frame glass art snow bow; do
    openscad -D design=$n -D "part=\"$p\"" -o mini_lantern_${n}_$p.stl mini_lanterns.scad > logs/${n}_$p.log 2>&1 &
  done
  openscad -D design=$n -D EMB=0.05 -D 'part="union"' -o mini_lantern_${n}_union.stl mini_lanterns.scad > logs/${n}_union.log 2>&1 &
  wait
done
# CGAL leaves edges shared by four faces where parts touch; welding through
# manifold closes them, as the village's check_building does
python3 -c "
import sys; sys.path.insert(0, '../../../tools'); import part_mesh
for n in '${*:-1 2 3 4 5 6}'.split():
    p = f'mini_lantern_{n}_union.stl'; part_mesh.to_trimesh(part_mesh.load(p)).export(p)"
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
