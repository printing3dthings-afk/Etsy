#!/usr/bin/env bash
# Fold Stand: export the parts (OpenSCAD 2026's manifold engine, then
# clean_parts.py), the hinge and stance check, product gate, print fidelity
# and fragility on each print, and the 3MFs.
#   ./ship.sh            export and check
#   ./ship.sh checks     check only
set -uo pipefail
cd "$(dirname "$0")"
T=../../tools
export OPENSCADPATH="$(cd ../../assets/openscad_libs && pwd)"
FAST=${OPENSCAD_FAST:-/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun}
F=fold_stand.scad
PARTS="front back pin front_use back_use0 pins_use"
mkdir -p parts logs checks
if [ "${1:-}" != checks ]; then
    for p in $PARTS; do "$FAST" --backend=manifold --export-format binstl -D "part=\"$p\"" -o parts/$p.stl $F > logs/$p.log 2>&1 & done; wait
    grep -l "WARNING\|ERROR" logs/*.log && echo "(warnings above)"
    python3 ../valentine_2027/mailboxes/clean_parts.py $(for p in $PARTS; do echo parts/$p.stl; done) | grep -v "^parts/.*watertight True" || true
fi
python3 check_stand.py | tee checks/fit.txt
check() {   # print colour
    local p=$1 c=$2
    echo "== gate $p"; python3 $T/product_gate.py ${BODIES:+-c $BODIES} parts/$p.stl > checks/gate_$p.txt 2>&1; grep -E "FAIL|support|GATE" checks/gate_$p.txt
    echo "== fidelity $p"; python3 $T/print_fidelity.py --part "parts/$p.stl:$c" --no-supports --json checks/fidelity_$p.json --keep logs/fid_$p > checks/fidelity_$p.txt 2>&1
    grep -E "PRINT FIDELITY|dropped \(|filled  \(|flagged" checks/fidelity_$p.txt
    echo "== fragility $p"; python3 $T/fragility.py parts/$p.stl > checks/fragility_$p.txt 2>&1; grep FRAGILITY checks/fragility_$p.txt
}
LILAC="#B79CE0"; WHITE="#F4F1EA"; PINK="#F6A6C1"
check front $LILAC
check back $WHITE
check pin $PINK
A=$T/assemble_3mf.py
python3 $A --plate fold_stand_front.3mf parts/front.stl:$LILAC | tail -1
python3 $A --plate fold_stand_back_pins.3mf parts/back.stl:$WHITE + parts/pin.stl:$PINK + parts/pin.stl:$PINK | tail -1
echo SHIP_DONE
