#!/bin/bash
# Rebuild, then: mesh gate per part, support slice of the union, four-colour fidelity.
cd "$(dirname "$0")"
./build.sh white red blue yellow plate union
for p in white red blue yellow plate; do python3 ../../../../tools/mesh_gate.py pizza_planet_rocket_$p.stl > logs/gate_$p.txt 2>&1; echo "$p: $(tail -n 1 logs/gate_$p.txt)"; done
python3 ../../../../tools/virtual_printer.py pizza_planet_rocket_union.stl -g logs/union_supports.gcode --json > logs/supports.json 2> logs/supports.err
python3 -c "import json;a=json.load(open('logs/supports.json'));print('SUPPORTS', a['support_moves'], 'OVERHANG_PERIMS', a['overhang_perimeters'], 'height', a['printed_height_mm'], a['model_height_mm'], 'g', a['filament_g'])"
python3 ../../../../tools/virtual_printer.py pizza_planet_rocket_plate.stl -g logs/plate.gcode --json > logs/plate_supports.json 2>/dev/null
python3 -c "import json;a=json.load(open('logs/plate_supports.json'));print('PLATE SUPPORTS', a['support_moves'], a['overhang_perimeters'])"
python3 ../../../../tools/print_fidelity.py --part pizza_planet_rocket_white.stl:#F4F1EA --part pizza_planet_rocket_red.stl:#C8312B \
  --part pizza_planet_rocket_blue.stl:#2B5FA8 --part pizza_planet_rocket_yellow.stl:#F2C230 --json logs/fidelity.json --keep logs/fidelity_work > logs/fidelity.txt 2>&1
sed -n '/PRINT FIDELITY/,/smaller/p' logs/fidelity.txt | grep -E 'PRINT|dropped \(|flagged|FLAG'
echo CHECKS_DONE
