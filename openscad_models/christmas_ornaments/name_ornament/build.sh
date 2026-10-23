#!/bin/bash
# Export the name ornament's colour parts and its one-body union. The name and
# year are parameters:  ./build.sh  or  ./build.sh "Olivia" 2026
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
N=${1:-Olivia}; Y=${2:-2026}
mkdir -p logs
for p in body inlay union; do
  openscad -D "part=\"$p\"" -D "NAME=\"$N\"" -D "YEAR=\"$Y\"" -o name_ornament_$p.stl name_ornament.scad > logs/$p.log 2>&1 &
done
wait
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
