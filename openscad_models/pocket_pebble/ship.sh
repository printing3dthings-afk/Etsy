#!/usr/bin/env bash
# Pocket Pebble: export the parts (OpenSCAD 2026's manifold engine, then
# clean_parts.py), the hinge and latch check, product gate, print fidelity and
# fragility on each print, and the 3MFs.
#   ./ship.sh            export and check
#   ./ship.sh checks     check only
set -uo pipefail
cd "$(dirname "$0")"
T=../../tools
export OPENSCADPATH="$(cd ../../assets/openscad_libs && pwd)"
FAST=${OPENSCAD_FAST:-/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun}
F=pocket_pebble.scad
PARTS="base lid pin lid_use0 pins_use"
mkdir -p parts logs checks
if [ "${1:-}" != checks ]; then
    for p in $PARTS; do "$FAST" --backend=manifold --export-format binstl -D "part=\"$p\"" -o parts/$p.stl $F > logs/$p.log 2>&1 & done; wait
    grep -l "WARNING\|ERROR" logs/*.log && echo "(warnings above)"
    python3 ../valentine_2027/mailboxes/clean_parts.py $(for p in $PARTS; do echo parts/$p.stl; done) | grep -v "^parts/.*watertight True" || true
fi
python3 check_pebble.py | tee checks/fit.txt
check() {   # print colour
    local p=$1 c=$2
    echo "== gate $p"; python3 $T/product_gate.py parts/$p.stl > checks/gate_$p.txt 2>&1; grep -E "FAIL|support|GATE" checks/gate_$p.txt
    echo "== fidelity $p"; python3 $T/print_fidelity.py --part "parts/$p.stl:$c" --no-supports --json checks/fidelity_$p.json --keep logs/fid_$p > checks/fidelity_$p.txt 2>&1
    grep -E "PRINT FIDELITY|dropped \(|filled  \(|flagged" checks/fidelity_$p.txt
    echo "== fragility $p"; python3 $T/fragility.py parts/$p.stl > checks/fragility_$p.txt 2>&1; grep FRAGILITY checks/fragility_$p.txt
}
WHITE="#F4F1EA"; LILAC="#B79CE0"; PINK="#F6A6C1"
check base $WHITE
check lid $LILAC
check pin $PINK
A=$T/assemble_3mf.py
python3 $A --plate pocket_pebble_base_pins.3mf parts/base.stl:$WHITE + parts/pin.stl:$PINK + parts/pin.stl:$PINK | tail -1
python3 $A --plate pocket_pebble_lid.3mf parts/lid.stl:$LILAC | tail -1
echo SHIP_DONE
