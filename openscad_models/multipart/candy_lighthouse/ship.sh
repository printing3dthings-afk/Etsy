#!/usr/bin/env bash
# After ./build.sh: fits, product gate on every print, print fidelity on every
# colour part, fragility, the 3MFs. Results land in checks/.
set -uo pipefail
cd "$(dirname "$0")"
T=../../../tools
python3 check_lighthouse.py | tail -1
mkdir -p checks
for p in tower_print wheel lantern roof head; do
    echo "== gate $p"; python3 $T/product_gate.py parts/$p.stl > checks/gate_$p.txt 2>&1; grep -E "FAIL|GATE" checks/gate_$p.txt
done
objs=("parts/tower.stl:#F4F1EA parts/tower_red.stl:#C8312B parts/tower_blue.stl:#3A6EA5" "parts/wheel.stl:#F4F1EA"
      "parts/lantern.stl:#CFE8F0" "parts/roof.stl:#C8312B" "parts/head.stl:#F4F1EA")
i=0
for o in "${objs[@]}"; do
    i=$((i+1)); a=(); for x in $o; do a+=(--part "$x"); done
    echo "== fidelity, print $i"
    python3 $T/print_fidelity.py "${a[@]}" --no-supports --json checks/fidelity_$i.json --keep logs/fid_$i > checks/fidelity_$i.txt 2>&1
    grep -E "PRINT FIDELITY|dropped \(|filled  \(|flagged" checks/fidelity_$i.txt
    echo "== fragility, print $i"; python3 $T/fragility.py $(for x in $o; do echo ${x%%:*}; done) > checks/fragility_$i.txt 2>&1; tail -2 checks/fragility_$i.txt
done
echo "== 3MF"
python3 $T/assemble_3mf.py --plate candy_lighthouse.3mf ${objs[0]} + ${objs[1]} + ${objs[2]} + ${objs[3]} | tail -2
python3 $T/assemble_3mf.py candy_lighthouse_head_test.3mf ${objs[4]} | tail -1
echo SHIP_DONE
