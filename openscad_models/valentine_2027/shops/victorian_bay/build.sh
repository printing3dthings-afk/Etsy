#!/bin/bash
# Export the Victorian Bay Chocolate Shop's parts:
#   ./build.sh            fast: OpenSCAD 2026 manifold engine, for checking
#   ./build.sh cgal       the shipping export: OpenSCAD 2021.01 CGAL
#   ./build.sh union      the gate's one-body union, from CGAL parts sunk EMB
#                         into each other and welded
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../../assets/openscad_libs && pwd)"
name=$(basename "$(ls *.scad)" .scad)
parts="body roof trim accent glass art"
FAST=${OPENSCAD_FAST:-/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun}
# the fast engine (OpenSCAD 2026, manifold) when it is there, else the installed one
FC=("$FAST" --backend=manifold --export-format binstl); [ -x "$FAST" ] || FC=(openscad)
mkdir -p logs
case "$1" in
  cgal) cmd=(openscad); e=0; out() { echo "${name}_$1.stl"; } ;;
  union) cmd=(openscad); e=0.05; out() { echo "logs/u_$1.stl"; } ;;
  *) cmd=("${FC[@]}"); e=0; out() { echo "${name}_$1.stl"; } ;;
esac
for p in $parts; do
  o=$(out $p)
  ( "${cmd[@]}" -D "part=\"$p\"" -D EMB=$e -o "$o.tmp.stl" $name.scad > "logs/$p.log" 2>&1 && mv "$o.tmp.stl" "$o" ) &
done
wait
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
[ "$1" = union ] && python3 ../../../../tools/part_mesh.py union ${name}_union.stl $(for p in $parts; do out $p; done)
exit 0
