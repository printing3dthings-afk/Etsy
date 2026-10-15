#!/bin/bash
# Export one accessory's colour parts and its one-body union:
#   ./build.sh pillar_box
# Parts with nothing in them (a piece with no slate, say) are dropped.
# tools/part_mesh.py check proves the rest closed and disjoint.
set -e
cd "$(dirname "$0")/$1"
export OPENSCADPATH="$(cd ../../../../assets/openscad_libs && pwd)"
name=victorian_$1
mkdir -p logs
for p in body roof trim accent union; do
  openscad -D "part=\"$p\"" -o "${name}_$p.stl" $name.scad > "logs/$p.log" 2>&1 &
done
wait
for p in body roof trim accent; do
  grep -q "Current top level object is empty" "logs/$p.log" && rm -f "${name}_$p.stl" && echo "$p: empty" || true
done
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
