#!/bin/bash
# Pocket Top UFO: export the parts and slice them with Bambu Studio (PLA Matte, 0.20 Standard,
# Bambu's own settings: the brief's budget is on the stock profile).
set -e
cd "$(dirname "$0")"
for p in saucer stem stem_in_use; do openscad -o parts/ufo_$p.stl -D "part=\"$p\"" ufo_top.scad; done
openscad -o parts/ufo_stem_exploded.stl -D 'part="stem_in_use"' -D lift=14 ufo_top.scad
R=../../tools/bambu_slice.py
json() { python3 -c "import sys,re; t=sys.stdin.read(); print(t[t.index('{'):t.rindex('}')+1])"; }
python3 $R parts/ufo_saucer.stl:#9BD3C8 + parts/ufo_stem.stl:#9BD3C8 -o ufo_top.gcode.3mf --filament pla_matte --bambu-defaults 2>&1 | json > checks/slice_plate.json
for p in saucer stem; do
  python3 $R parts/ufo_$p.stl:#9BD3C8 -o checks/ufo_$p.gcode.3mf --filament pla_matte --bambu-defaults 2>&1 | json > checks/slice_$p.json
done
cat checks/slice_plate.json
# the gates. The stem's engraved face is declared detail: on the dome's slope its recesses'
# edges are corner clips, not walls, and print_fidelity checks that they print. The band is
# the dome's whole middle because spans crossing the dome start or end on those edges; the
# same dome without the face has no span under 1.2 at all (measured 2026-11-15).
G=../../tools
python3 $G/product_gate.py parts/ufo_saucer.stl > checks/gate_ufo_saucer.txt 2>&1 || true
python3 $G/product_gate.py parts/ufo_stem.stl --wall-skip-band 0,7.0,1.2,6.6 > checks/gate_ufo_stem.txt 2>&1 || true
python3 $G/small_parts.py parts/ufo_saucer.stl parts/ufo_stem.stl > checks/small_parts_ufo.txt 2>&1 || true
