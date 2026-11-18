#!/bin/bash
# Export both camera signs' colour parts and their one-body unions.
#   ./build.sh          THICK as in the .scad (a placeholder until Scott's gaps)
#   ./build.sh 2.0      a total thickness in mm
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../assets/openscad_libs && pwd)"
T=${1:-}
mkdir -p logs
for st in neon plaque; do
  for p in base letters; do
    openscad -D "style=\"$st\"" -D "part=\"$p\"" ${T:+-D THICK=$T} -o camera_sign_${st}_$p.stl camera_sign.scad > logs/${st}_$p.log 2>&1 &
  done
done
wait
for st in neon plaque; do
  python3 ../../tools/part_mesh.py union camera_sign_${st}_union.stl camera_sign_${st}_base.stl camera_sign_${st}_letters.stl
done
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
