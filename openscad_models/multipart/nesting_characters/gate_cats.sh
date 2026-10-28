#!/usr/bin/env bash
# Product gate on each Nesting Cats print, its colour parts welded into one
# body first (logs/u_*.stl), as the slicer sees it.
set -uo pipefail
cd "$(dirname "$0")"
M=../../../tools/part_mesh.py
G=../../../tools/product_gate.py
for i in 0 1 2 3; do
    echo "cat${i}_bottom: $(python3 $G parts/cat${i}_bottom.stl 2>&1 | grep -E '^  FAIL|PASSED|FAILED' | sed 's/;.*//' | tr '\n' ' ')"
    python3 $M union logs/u_cat${i}_top.stl parts/cat${i}_top_*.stl > /dev/null 2>&1
    echo "cat${i}_top: $(python3 $G logs/u_cat${i}_top.stl 2>&1 | grep -E '^  FAIL|PASSED|FAILED' | sed 's/;.*//' | tr '\n' ' ')"
done
python3 $M union logs/u_cat4_solid.stl parts/cat4_solid_*.stl > /dev/null 2>&1
echo "cat4_solid: $(python3 $G logs/u_cat4_solid.stl 2>&1 | grep -E '^  FAIL|PASSED|FAILED' | sed 's/;.*//' | tr '\n' ' ')"
