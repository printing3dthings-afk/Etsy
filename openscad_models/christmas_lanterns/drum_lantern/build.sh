#!/bin/bash
# Export the parts and wrap the flat ones round the drum; with "union", the
# one-body mesh the gate checks. ../lantern_mesh.py check proves the colour
# parts closed and disjoint. BOSL2 and the village's relief library live in
# the repo.
set -e
cd "$(dirname "$0")"
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
name=drum_lantern
M="python3 ../lantern_mesh.py"
# R, z0, RO and zr from drum_lantern.scad
R=40; Z0=7; RR=43.5; ZR=95
mkdir -p logs
e=0; [ "$1" = "union" ] && e=0.05
for p in frame glass bead art_flat drape_flat; do
  openscad -D "part=\"$p\"" -D EMB=$e -o "logs/$p.stl" $name.scad > "logs/$p.log" 2>&1 &
done
wait
grep -h "WARNING\|ERROR" logs/*.log | sort | uniq -c || true
# wrapped a hair (0.03) into the glass and the rim, then cut back to touch them
if [ "$1" = "union" ]; then
  $M wrap logs/art_flat.stl logs/u_art.stl --radius $(echo "$R - 0.03" | bc) --z $Z0 --step 2.5
  $M wrap logs/drape_flat.stl logs/u_drape.stl --radius $(echo "$RR - 0.03" | bc) --z $ZR --step 2.5
  $M union ${name}_union.stl logs/frame.stl logs/glass.stl logs/bead.stl logs/u_art.stl logs/u_drape.stl
  exit
fi
cp logs/frame.stl ${name}_frame.stl; cp logs/glass.stl ${name}_glass.stl; cp logs/bead.stl ${name}_bead.stl
$M wrap logs/art_flat.stl ${name}_art.stl --radius $(echo "$R - 0.03" | bc) --z $Z0 --step 2.5 --minus ${name}_glass.stl
$M wrap logs/drape_flat.stl ${name}_drape.stl --radius $(echo "$RR - 0.03" | bc) --z $ZR --step 2.5 --minus ${name}_frame.stl --minus ${name}_bead.stl
