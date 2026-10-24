#!/bin/bash
# Before/after renders: v1 (the listed file) and v2, same tool, same settings.
cd "$(dirname "$0")/.."
R=../../../../tools/blender_render.py
col() { echo "--part $1_body.stl:0.659,0.282,0.227 --part $1_roof.stl:0.18,0.204,0.251 --part $1_trim.stl:0.957,0.945,0.918 --part $1_accent.stl:0.184,0.42,0.271"; }
python3 $R $(col v2/victorian_santas_workshop_v2) --views --resolution 1600 --timeout 2400 -o v2/images/v2_colour
python3 $R $(col victorian_santas_workshop) --views --resolution 1600 --timeout 2400 -o v2/images/v1_colour
echo RENDERS_DONE
