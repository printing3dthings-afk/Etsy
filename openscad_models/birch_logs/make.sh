#!/bin/sh
# Birch Log Tea-Light Trio: export the colour parts and slice the plate (2026-11-15).
# Run from the repo root. See FACTS.md.
set -e
D=openscad_models/birch_logs
for w in 0 1 2; do
  for p in body marks top; do
    openscad -o $D/parts/log${w}_$p.stl -D "part=\"$p\"" -D which=$w $D/birch_logs.scad &
  done
done
wait
W=#EDE8DC   # bark: matte ivory white
K=#2B2A28   # marks: matte charcoal
T=#C9A877   # cut face: matte latte / tan
# The bark texture is the slicer's: Perlin fuzzy skin on the outer walls, 0.3 deep, points
# 0.6 apart, scale 3 (the texture sampler's settings, data/knowledge_base/fdm_only_techniques.md).
FS=""
for n in 1 2 3; do FS="$FS --object-set $n:fuzzy_skin=external --object-set $n:fuzzy_skin_noise_type=perlin"; done
P=$D/parts
python3 tools/bambu_slice.py \
  $P/log0_body.stl:$W $P/log0_marks.stl:$K $P/log0_top.stl:$T + \
  $P/log1_body.stl:$W $P/log1_marks.stl:$K $P/log1_top.stl:$T + \
  $P/log2_body.stl:$W $P/log2_marks.stl:$K $P/log2_top.stl:$T \
  -o $D/birch_logs_trio.gcode.3mf --filament pla_matte \
  --set fuzzy_skin_thickness=0.3 --set fuzzy_skin_point_distance=0.6 --set fuzzy_skin_scale=3 $FS
