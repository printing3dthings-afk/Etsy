#!/bin/bash
# Export the six mini-lantern ornaments' colour parts and one-body unions:
#   ./build.sh          (all six)      ./build.sh 3      (one)
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
mkdir -p logs
for n in ${1:-1 2 3 4 5 6}; do
  for p in frame glass art snow bow; do
    openscad -D design=$n -D "part=\"$p\"" -o mini_lantern_${n}_$p.stl mini_lanterns.scad > logs/${n}_$p.log 2>&1 &
  done
  openscad -D design=$n -D EMB=0.05 -D 'part="union"' -o mini_lantern_${n}_union.stl mini_lanterns.scad > logs/${n}_union.log 2>&1 &
  wait
done
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
