#!/bin/sh
# Pie Drum Caddy: export, gate, check, slice (2026-11-15). Run from the repo root.
set -e
D=openscad_models/pie_caddy
openscad -o $D/parts/pie_caddy_base.stl -D 'part="base"' $D/pie_caddy.scad &
openscad -o $D/parts/pie_caddy_drum.stl -D 'part="drum"' $D/pie_caddy.scad &
wait
for n in base drum; do python3 tools/product_gate.py $D/parts/pie_caddy_$n.stl > $D/checks/gate_pie_caddy_$n.txt 2>&1 || true; done
python3 $D/check_caddy.py > /dev/null || true
python3 tools/bambu_slice.py $D/parts/pie_caddy_drum.stl:#E8B98A -o $D/pie_caddy_drum.gcode.3mf --filament pla_matte > $D/checks/slice_drum.txt 2>&1
python3 tools/bambu_slice.py $D/parts/pie_caddy_base.stl:#6B4A3A -o $D/pie_caddy_base.gcode.3mf --filament pla_matte > $D/checks/slice_base.txt 2>&1
grep -H "PRODUCT GATE" $D/checks/gate_pie_caddy_*.txt
tail -n 1 $D/checks/fit_caddy.txt
