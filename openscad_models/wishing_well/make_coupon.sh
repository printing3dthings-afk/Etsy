#!/bin/sh
# Wishing Well windlass test print: export the parts, gate them, slice the plate (2026-11-15).
# Run from the repo root. See FACTS.md and ENGINEERING.md.
set -e
D=openscad_models/wishing_well
mkdir -p $D/parts $D/checks
exp() { openscad -o $D/parts/$1.stl -D "part=\"$2\"" $3 $D/windlass.scad; }
exp post_crank post "-D e_sel=0.55 -D pawl_sel=true" &
exp post_far_040 post "-D e_sel=0.40 -D pawl_sel=false" &
exp post_far_070 post "-D e_sel=0.70 -D pawl_sel=false" &
exp axle axle "" &
exp wheel wheel "" &
exp pawl pawl "" &
exp bucket bucket "" &
exp base base "" &
wait
for n in post_crank post_far_040 post_far_070 axle pawl bucket base; do
  python3 tools/product_gate.py $D/parts/$n.stl > $D/checks/gate_$n.txt 2>&1 || true
done
# the ratchet teeth's tips are sharp by design (checked by the fit check and print_fidelity),
# so the tooth ring is left out of the wall floor, as thread teeth are
python3 tools/product_gate.py $D/parts/wheel.stl --wall-skip-band 15.2,17.2,-1,4 > $D/checks/gate_wheel.txt 2>&1 || true
python3 $D/check_windlass.py > /dev/null
grep -H "PRODUCT GATE" $D/checks/gate_*.txt
tail -n 1 $D/checks/fit_windlass.txt
