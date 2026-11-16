#!/bin/bash
# Gear Heart v2 (2026-11-16): the heart with clip-v2 axle pins (barb 0.65, Scott's pick).
# Exports, print-ready 3MFs, Bambu Studio slices (P1S 0.4, PLA Basic, 0.20 Standard, the
# shop's retail settings, textured PEI: as v1) and the gates. The v1 files (snap posts, one
# of which snapped on Scott's print) stay as they were: gear_heart_plate.3mf, gear_heart_gears.3mf.
set -e
cd "$(dirname "$0")"
S=heart.scad; T=../../tools
mkdir -p parts/heart_gear checks logs
openscad -o parts/heart_plate_v2.stl -D 'part="plate"' $S > logs/v2_plate.log 2>&1
openscad -o parts/heart_gears_v2.stl -D 'part="gears"' $S > logs/v2_gears.log 2>&1
openscad -o parts/heart_pins_posed.stl -D 'part="pins_posed"' $S > logs/v2_pins.log 2>&1
openscad -o parts/heart_gate_skip.stl -D 'part="gate_skip"' $S > /dev/null 2>&1
openscad -o parts/heart_pin_local.stl -D 'part="pin_local"' $S > logs/v2_pin.log 2>&1
for i in $(seq 0 14); do openscad -o parts/heart_gear/g$i.stl -D 'part="gear_local"' -D idx=$i $S > /dev/null 2>&1; done
python3 $T/assemble_3mf.py gear_heart_plate_v2.3mf parts/heart_plate_v2.stl
python3 $T/assemble_3mf.py gear_heart_gears_v2.3mf parts/heart_gears_v2.stl
json() { python3 -c "import sys; t=sys.stdin.read(); print(t[t.index('{'):t.rindex('}')+1])"; }
python3 $T/bambu_slice.py parts/heart_plate_v2.stl:#E8C9D2 -o checks/heart_plate_v2.gcode.3mf 2>&1 | json > checks/slice_heart_plate_v2.json
python3 $T/bambu_slice.py parts/heart_gears_v2.stl:#C94F6D -o checks/heart_gears_v2.gcode.3mf 2>&1 | json > checks/slice_heart_gears_v2.json
python3 $T/product_gate.py parts/heart_plate_v2.stl > checks/gate_heart_plate_v2.txt 2>&1 || true
python3 $T/product_gate.py parts/heart_gears_v2.stl -c 30 --wall-skip-part parts/heart_gate_skip.stl > checks/gate_heart_gears_v2.txt 2>&1 || true
grep -h -E '"time"|filament_g' checks/slice_heart_*_v2.json
grep -h -E "FAIL|PASSED|FAILED" checks/gate_heart_*_v2.txt
