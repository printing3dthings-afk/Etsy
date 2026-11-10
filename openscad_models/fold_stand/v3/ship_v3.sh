#!/usr/bin/env bash
# Fold Stand v3: export the parts (OpenSCAD 2026's manifold engine, then clean_parts.py),
# the posed fit check, product gate, print fidelity and fragility on each print, the 3MFs.
#   ./ship_v3.sh            export and check
#   ./ship_v3.sh checks     check only
set -uo pipefail
cd "$(dirname "$0")"
T=../../../tools
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
FAST=${OPENSCAD_FAST:-/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun}
F=fold_stand_v3.scad
PARTS="base plate prop coupon_base coupon_plate"
mkdir -p parts logs checks
if [ "${1:-}" != checks ]; then
    for p in $PARTS; do "$FAST" --backend=manifold --export-format binstl -D "part=\"$p\"" -o parts/$p.stl $F > logs/$p.log 2>&1 & done; wait
    grep -l "WARNING\|ERROR:" logs/*.log && echo "(warnings above)"
    python3 ../../valentine_2027/mailboxes/clean_parts.py $(for p in $PARTS; do echo parts/$p.stl; done) | grep -v "watertight True" || true
fi
python3 check_stand_v3.py 2>/dev/null | tee checks/fit.txt
check() {   # part colour
    local p=$1 c=$2
    echo "== gate $p"; python3 $T/product_gate.py parts/$p.stl > checks/gate_$p.txt 2>&1; grep -E "FAIL|support|GATE" checks/gate_$p.txt
    echo "== fidelity $p"; python3 $T/print_fidelity.py --part "parts/$p.stl:$c" --no-supports --json checks/fidelity_$p.json --keep logs/fid_$p > checks/fidelity_$p.txt 2>&1
    grep -E "PRINT FIDELITY|dropped \(|filled  \(|flagged" checks/fidelity_$p.txt
    echo "== fragility $p"; python3 $T/fragility.py parts/$p.stl > checks/fragility_$p.txt 2>&1; grep FRAGILITY checks/fragility_$p.txt
}
LILAC="#B79CE0"; WHITE="#F4F1EA"
check base $WHITE
check plate $LILAC
check prop $WHITE
A=$T/assemble_3mf.py
python3 $A --plate fold_stand_v3_base_prop.3mf parts/base.stl:$WHITE + parts/prop.stl:$WHITE | tail -1
python3 $A --plate fold_stand_v3_plate.3mf parts/plate.stl:$LILAC | tail -1
python3 $A --plate fold_stand_v3_coupon.3mf parts/coupon_base.stl:$WHITE + parts/coupon_plate.stl:$LILAC + parts/prop.stl:$WHITE | tail -1
echo SHIP_DONE
