#!/bin/bash
# Colour renders of the horse sleigh as it stands assembled: the sleigh piece
# with the whole horse in its sockets (model_checks renders pieces as they lie
# on the plate). Run ./build.sh first.
cd "$(dirname "$0")"
args=()
for piece in sleigh horse; do
  for pc in "roof:0.180,0.204,0.251" "accent:0.184,0.420,0.271" "trim:0.957,0.945,0.918" "body:0.659,0.282,0.227"; do
    p=${pc%%:*}; [ -f "hs_${piece}_$p.stl" ] && args+=(--part "hs_${piece}_$p.stl:${pc#*:}")
  done
done
python3 ../../../../tools/blender_render.py "${args[@]}" -o images/victorian_horse_sleigh_colour.png \
  --views --front=-y --samples 96 --timeout 1800 > logs/render.txt 2>&1
