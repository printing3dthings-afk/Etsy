#!/usr/bin/env bash
# Product gate on each Nesting Cats print. A top or the solid cat is exported
# whole (logs/u_*.stl, every colour in one solid) for the gate: its colour
# parts welded together left open edges where they touch (2026-10-28).
set -uo pipefail
cd "$(dirname "$0")"
export OPENSCADPATH=../../../assets/openscad_libs
G=../../../tools/product_gate.py
for i in 0 1 2 3; do openscad -D fig=$i -D 'part="top"' -o logs/u_cat${i}_top.stl nesting_cats.scad > logs/u_cat${i}_top.log 2>&1 & done
openscad -D fig=4 -D 'part="solid"' -o logs/u_cat4_solid.stl nesting_cats.scad > logs/u_cat4_solid.log 2>&1 &
wait
for i in 0 1 2 3; do
    echo "cat${i}_bottom: $(python3 $G parts/cat${i}_bottom.stl 2>&1 | grep -E '^  FAIL|PASSED|FAILED' | sed 's/;.*//' | tr '\n' ' ')"
    echo "cat${i}_top: $(python3 $G logs/u_cat${i}_top.stl 2>&1 | grep -E '^  FAIL|PASSED|FAILED' | sed 's/;.*//' | tr '\n' ' ')"
done
echo "cat4_solid: $(python3 $G logs/u_cat4_solid.stl 2>&1 | grep -E '^  FAIL|PASSED|FAILED' | sed 's/;.*//' | tr '\n' ' ')"
