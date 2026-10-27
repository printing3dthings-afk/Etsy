#!/bin/bash
# Export the Standing Heart lantern's parts:
#   ./build.sh            fast: OpenSCAD 2026 manifold engine, for checking
#   ./build.sh cgal       the shipping export: OpenSCAD 2021.01 CGAL
#   ./build.sh union      the gate's one-body union (parts sunk EMB into each other, welded),
#                         from CGAL parts: the fast engine leaves edges pinched where the
#                         art and the names step, and the slicer reads them as holes
#   ./build.sh union fast the same from the fast engine, for a quick look
# Personalise with -D on the command line, e.g.
#   NAMES="Ava & Noah" DATE="06.21.2025" ./build.sh cgal
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
name=standing_heart_lantern
parts="frame glass art lip text"
FAST=${OPENSCAD_FAST:-/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun}
# the fast engine (OpenSCAD 2026, manifold) when it is there, else the installed one
FC=("$FAST" --backend=manifold --export-format binstl); [ -x "$FAST" ] || FC=(openscad)
mkdir -p logs
P=()
[ -n "$NAMES" ] && P+=(-D "NAMES=\"$NAMES\"")
[ -n "$DATE" ] && P+=(-D "DATE=\"$DATE\"")
case "$1" in
  cgal) cmd=(openscad) ;;
  union)
    if [ "$2" = fast ]; then U=("${FC[@]}"); else U=(openscad); fi
    for p in $parts; do "${U[@]}" "${P[@]}" -D "part=\"$p\"" -D EMB=0.05 -o "logs/u_$p.stl" $name.scad > "logs/u_$p.log" 2>&1 & done
    wait
    python3 ../../../tools/part_mesh.py union ${name}_union.stl $(for p in $parts; do echo logs/u_$p.stl; done)
    exit ;;
  *) cmd=("${FC[@]}"); EXP="" ;;
esac
for p in $parts; do
  "${cmd[@]}" "${P[@]}" $EXP -D "part=\"$p\"" -o "${name}_$p.stl" $name.scad > "logs/$p.log" 2>&1 &
done
wait
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
