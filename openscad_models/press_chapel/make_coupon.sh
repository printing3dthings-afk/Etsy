#!/bin/bash
# Press-to-Light Chapel drop test print: export the parts laid for printing, then slice
# them with Bambu Studio (2026-11-17). Two plates:
#   drop_coupon.gcode.3mf        everything, with the middle hub (0.4 mm): does the weight drive it?
#   drop_coupon_hubs.gcode.3mf   the 0.3 and 0.5 hubs, only if the middle one binds or rattles
# A test print, so Bambu's own speeds, not the retail finish settings (as the Plinko test).
# The steeple is the weight that drives the drop: printed solid, as the budget's mass assumes.
# The shaft stands 60 mm on a 4.6 mm key: a brim holds it.
set -e
cd "$(dirname "$0")"
T=../../tools
mkdir -p parts checks
for p in base arch shaft steeple; do openscad -q -o parts/$p.stl -D "part=\"print_$p\"" drop_coupon.scad & done
for v in 1 2 3; do openscad -q -o parts/hub_$v.stl -D 'part="print_hub"' -D v=$v drop_coupon.scad & done
wait
python3 $T/bambu_slice.py parts/base.stl:#F4F1EA + parts/arch.stl:#F4F1EA + parts/shaft.stl:#F4F1EA \
  + parts/steeple.stl:#F4F1EA + parts/hub_2.stl:#F4F1EA \
  --filament pla_matte --bambu-defaults --object-set 4:sparse_infill_density=100% \
  --object-set 3:brim_type=outer_only --object-set 3:brim_width=5 \
  -o drop_coupon.gcode.3mf | sed -n '/^{/,$p' > checks/slice.json
python3 $T/bambu_slice.py parts/hub_1.stl:#F4F1EA + parts/hub_3.stl:#F4F1EA \
  --filament pla_matte --bambu-defaults -o drop_coupon_hubs.gcode.3mf | sed -n '/^{/,$p' > checks/slice_hubs.json
grep '"time"\|"filament_g"\|support_lines' checks/slice.json checks/slice_hubs.json
