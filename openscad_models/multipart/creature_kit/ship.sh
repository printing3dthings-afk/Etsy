#!/usr/bin/env bash
# After ./build.sh: fits, product gate and print fidelity on every print,
# fragility, the 3MF. Results land in checks/.
set -uo pipefail
cd "$(dirname "$0")"
T=../../../tools
PINK="#F4B2C5"; GILL="#D9508A"; EYE="#2A2630"
python3 check_axolotl.py | tail -1
mkdir -p checks
prints="head gills eye s1 s2 s3 s4 tail leg_front_l leg_front_r leg_rear_l leg_rear_r"
colour() { case $1 in gills) echo $GILL;; eye) echo $EYE;; *) echo $PINK;; esac; }
for p in $prints; do
    echo "== gate $p"; python3 $T/product_gate.py parts/$p.stl > checks/gate_$p.txt 2>&1; grep -E "^  FAIL|GATE" checks/gate_$p.txt
    echo "== fidelity $p"
    python3 $T/print_fidelity.py --part parts/$p.stl:$(colour $p) --no-supports --json checks/fidelity_$p.json --keep logs/fid_$p > checks/fidelity_$p.txt 2>&1
    grep -E "dropped \(|filled  \(|flagged" checks/fidelity_$p.txt
done
echo "== fragility"; python3 $T/fragility.py $(for p in $prints; do echo parts/$p.stl; done) > checks/fragility.txt 2>&1; tail -3 checks/fragility.txt
echo "== 3MF"
python3 $T/assemble_3mf.py --plate chubby_axolotl.3mf \
    parts/head.stl:$PINK + parts/s1.stl:$PINK + parts/s2.stl:$PINK + parts/s3.stl:$PINK + parts/s4.stl:$PINK + parts/tail.stl:$PINK \
    + parts/leg_front_l.stl:$PINK + parts/leg_front_r.stl:$PINK + parts/leg_rear_l.stl:$PINK + parts/leg_rear_r.stl:$PINK \
    + parts/gills.stl:$GILL + parts/eye.stl:$EYE + parts/eye.stl:$EYE | tail -3
echo SHIP_DONE
