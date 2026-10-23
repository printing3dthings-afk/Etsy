#!/bin/bash
# Export the four colour parts (and, with "chk", the six pairwise overlap
# checks). BOSL2 lives in the repo; point OpenSCAD at it.
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../../assets/openscad_libs && pwd)"
name=gingerbread_cocoa_cafe
mkdir -p logs
parts="body roof trim accent"
[ "$1" = "chk" ] && parts="chk_body_roof chk_body_trim chk_body_accent chk_roof_trim chk_roof_accent chk_trim_accent"
for p in $parts; do
  openscad -D "part=\"$p\"" -o "${name}_$p.stl" $name.scad > "logs/$p.log" 2>&1 &
done
wait
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
