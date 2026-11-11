#!/usr/bin/env bash
# Bayonet Jar v3: gate every part, then one 3MF per size (jar + its lid on one plate),
# sliced with Bambu Studio for time and filament. Run build_sizes.py first.
set -u
cd "$(dirname "$0")"
T=../../../tools
G="#E8B33A"; L="$G"   # one filament: two colours made the AMS swap every layer
mkdir -p checks logs/slices
if [ "${1:-}" != "--no-gates" ]; then
: > checks/gates.txt
for p in parts/lid_D*.stl parts/base_D*.stl; do
  n=$(basename "$p" .stl)
  python3 $T/product_gate.py "$p" > "checks/gate_$n.txt" 2>&1
  echo "$n: $(grep -E 'FAIL|GATE' "checks/gate_$n.txt" | tr '\n' ' ')" >> checks/gates.txt
done
fi
: > checks/slices.txt
for d in 40 50 65 80; do for h in 30 45 70 100; do
  s=D${d}_H${h}
  python3 $T/assemble_3mf.py --plate bayonet_jar_v3_$s.3mf parts/base_$s.stl:$G + parts/lid_D$d.stl:$L > /dev/null
  python3 $T/bambu_slice.py parts/base_$s.stl:$G + parts/lid_D$d.stl:$L -o logs/slices/$s.gcode.3mf --quality standard > logs/slices/$s.txt 2>&1
  echo "$s: $(grep -oE '"(time|filament_g|support_lines)": *"?[^,"]*' logs/slices/$s.txt | tr '\n' ' ')" >> checks/slices.txt
done; done
echo SHIP_DONE >> checks/slices.txt
