#!/bin/bash
# Export the four colour parts (and, with "chk", the six pairwise overlap
# checks). BOSL2 lives in the repo; point OpenSCAD at it.
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
name=haunted_post_office
mkdir -p logs
parts="body trim accent lid"
[ "$1" = "chk" ] && parts="chk_body_trim chk_body_accent chk_trim_accent chk_lid_house"
for p in $parts; do
  openscad -D "part=\"$p\"" -o "${name}_$p.stl" $name.scad > "logs/$p.log" 2>&1 &
done
wait
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
