#!/bin/bash
# Export the Swan Crown lantern's parts and wrap the flat ones round the drum:
#   ./build.sh            fast: OpenSCAD 2026 manifold engine, for checking
#   ./build.sh cgal       the shipping export: OpenSCAD 2021.01 CGAL
#   ./build.sh union      the gate's one-body unions, one per print (drum, lid,
#                         crown), from CGAL parts sunk EMB into each other
#   ./build.sh union fast the same from the fast engine, for a quick look
# Personalise with -D on the command line, e.g.
#   NAMES="Ava & Noah" DATE="06.21.2025" ./build.sh cgal
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
name=swan_crown_lantern
M="python3 ../../../tools/part_mesh.py"
FAST=${OPENSCAD_FAST:-/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun}
# the fast engine (OpenSCAD 2026, manifold) when it is there, else the installed one
FC=("$FAST" --backend=manifold --export-format binstl); [ -x "$FAST" ] || FC=(openscad)
# from swan_crown_lantern.scad: RI = R - PANE, RP, ZA = ZP + 3; ZN the names' foot
RI=39.1; RP=44; ZA=20; ZN=0.6
mkdir -p logs
P=()
[ -n "$NAMES" ] && P+=(-D "NAMES=\"$NAMES\"")
[ -n "$DATE" ] && P+=(-D "DATE=\"$DATE\"")
e=0; [ "$1" = union ] && e=0.05
if [ "$1" = cgal ] || { [ "$1" = union ] && [ "$2" != fast ]; }; then cmd=(openscad); else cmd=("${FC[@]}"); fi
for p in frame glass art_flat text_flat lid crown crown_shown; do
  ( "${cmd[@]}" "${P[@]}" -D "part=\"$p\"" -D EMB=$e -o "logs/$p.tmp.stl" $name.scad > "logs/$p.log" 2>&1 && mv "logs/$p.tmp.stl" "logs/$p.stl" ) &
done
wait
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
# the pond wrapped a hair (0.03) into the glass, the names into the plinth, then
# cut back to touch them; for the union they keep the overlap and are welded
if [ "$1" = union ]; then
  $M wrap logs/art_flat.stl logs/u_art.stl --radius $(echo "$RI + 0.03" | bc) --z $ZA --step 2.5
  $M wrap logs/text_flat.stl logs/u_text.stl --radius $(echo "$RP - 0.03" | bc) --z $ZN --step 1.0
  $M union ${name}_drum_union.stl logs/frame.stl logs/glass.stl logs/u_art.stl logs/u_text.stl
  cp logs/lid.stl ${name}_lid_union.stl
  cp logs/crown.stl ${name}_crown_union.stl
  exit
fi
for p in frame glass lid crown crown_shown; do cp logs/$p.stl ${name}_$p.stl; done
$M wrap logs/art_flat.stl ${name}_art.stl --radius $(echo "$RI + 0.03" | bc) --z $ZA --step 2.5 --minus ${name}_glass.stl --minus ${name}_frame.stl
$M wrap logs/text_flat.stl ${name}_text.stl --radius $(echo "$RP - 0.03" | bc) --z $ZN --step 1.0 --minus ${name}_frame.stl
