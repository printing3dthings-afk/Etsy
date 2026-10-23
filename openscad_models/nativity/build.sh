#!/bin/bash
# Export the nativity's parts:  ./build.sh [union]
#   nativity_<piece>_body.stl for every piece, nativity_<piece>_gold.stl for
#   the kings and the stable; with "union", the one-body unions the gate reads.
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../assets/openscad_libs && pwd)"
mkdir -p logs
PIECES="mary joseph baby king1 king2 king3 shepherd ox donkey sheep stable"
if [ "$1" = union ]; then
  for pc in $PIECES; do
    openscad -D "piece=\"$pc\"" -D 'part="union"' -o nativity_${pc}_union.stl nativity.scad > logs/${pc}_union.log 2>&1 &
  done
  wait
  python3 -c "
import sys; sys.path.insert(0, '../../tools'); import part_mesh
for pc in '$PIECES'.split():
    p = f'nativity_{pc}_union.stl'; part_mesh.to_trimesh(part_mesh.load(p)).export(p)"
  exit
fi
for pc in $PIECES; do
  openscad -D "piece=\"$pc\"" -D 'part="body"' -o nativity_${pc}_body.stl nativity.scad > logs/${pc}_body.log 2>&1 &
done
for pc in king1 king2 king3 stable; do
  openscad -D "piece=\"$pc\"" -D 'part="gold"' -o nativity_${pc}_gold.stl nativity.scad > logs/${pc}_gold.log 2>&1 &
done
wait
grep -h "WARNING\|ERROR" logs/*_body.log logs/*_gold.log | sort | uniq -c || true
