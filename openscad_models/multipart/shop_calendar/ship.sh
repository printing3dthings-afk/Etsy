#!/usr/bin/env bash
# After ./build.sh: fits, product gate on every print, print fidelity on every
# colour part, fragility, the 3MF. Results land in checks/.
set -uo pipefail
cd "$(dirname "$0")"
T=../../../tools
python3 check_calendar.py | tail -1
mkdir -p checks
prints="base facade roof rod drum_day_print drum_tens_print drum_ones_print drum_month_print"
for p in $prints; do
    echo "== gate $p"; python3 $T/product_gate.py parts/$p.stl > checks/gate_$p.txt 2>&1; grep -E "FAIL|GATE" checks/gate_$p.txt
done
objs=("parts/base.stl:#B85C47" "parts/facade.stl:#A9DCC8" "parts/roof.stl:#5A5F66" "parts/rod.stl:#F4F1EA")
for d in day tens ones month; do objs+=("parts/drum_$d.stl:#F4F1EA parts/drum_${d}_text.stl:#2B3A55"); done
i=0
for o in "${objs[@]}"; do
    i=$((i+1)); a=(); for x in $o; do a+=(--part "$x"); done
    echo "== fidelity, print $i ($o)"
    python3 $T/print_fidelity.py "${a[@]}" --no-supports --json checks/fidelity_$i.json --keep logs/fid_$i > checks/fidelity_$i.txt 2>&1
    grep -E "PRINT FIDELITY|dropped \(|filled  \(|flagged" checks/fidelity_$i.txt
    echo "== fragility, print $i"; python3 $T/fragility.py $(for x in $o; do echo ${x%%:*}; done) > checks/fragility_$i.txt 2>&1; tail -2 checks/fragility_$i.txt
done
echo "== 3MF"
python3 $T/assemble_3mf.py --plate shop_calendar.3mf ${objs[0]} + ${objs[1]} + ${objs[2]} + ${objs[3]} + ${objs[4]} + ${objs[5]} + ${objs[6]} + ${objs[7]} | tail -3
echo SHIP_DONE
