#!/bin/sh
# Urban Kid: one plate per filament colour (no AMS), Bambu Studio itself, P1S,
# 0.12 mm (fine) for the detail, PLA Basic. One at a time: two Bambu Studio
# CLIs side by side fail (2026-11-16).
set -e
cd "$(dirname "$0")"
mkdir -p gcode logs
S="python3 ../../tools/bambu_slice.py --quality fine"
$S parts/head.stl:#DCA37A -o gcode/urban_kid_skin_head.gcode.3mf > logs/slice_skin.out 2>&1
$S parts/hoodie.stl:#C21D21 -o gcode/urban_kid_red_hoodie.gcode.3mf > logs/slice_red.out 2>&1
$S parts/pants.stl:#45474C -o gcode/urban_kid_charcoal_pants.gcode.3mf > logs/slice_charcoal.out 2>&1
$S parts/shoe_r.stl:#EDEDE8 + parts/shoe_l.stl:#EDEDE8 -o gcode/urban_kid_white_sneakers.gcode.3mf > logs/slice_white.out 2>&1
$S parts/cap.stl:#1C1C1F + parts/base.stl:#1C1C1F + parts/pin.stl:#1C1C1F -o gcode/urban_kid_black_cap_base_pin.gcode.3mf > logs/slice_black.out 2>&1
$S parts/chain.stl:#D9A32E -o gcode/urban_kid_gold_chain.gcode.3mf > logs/slice_gold.out 2>&1
