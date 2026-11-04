#!/usr/bin/env bash
# Penny Spinner: export the parts (OpenSCAD 2026's manifold engine, then
# clean_parts.py), the fit and balance check, product gate, print fidelity
# and fragility on each print, and the 3MFs.
#   ./ship.sh            export and check
#   ./ship.sh checks     check only
set -uo pipefail
cd "$(dirname "$0")"
T=../../tools
export OPENSCADPATH="$(cd ../../assets/openscad_libs && pwd)"
FAST=${OPENSCAD_FAST:-/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun}
F=penny_spinner.scad
PARTS="crown base stem crown_use base_use stem_use coins"
mkdir -p parts logs checks
if [ "${1:-}" != checks ]; then
    for p in $PARTS; do "$FAST" --backend=manifold --export-format binstl -D "part=\"$p\"" -o parts/$p.stl $F > logs/$p.log 2>&1 & done; wait
    grep -l "WARNING\|ERROR" logs/*.log && echo "(warnings above)"
    python3 ../valentine_2027/mailboxes/clean_parts.py $(for p in $PARTS; do echo parts/$p.stl; done) | grep -v "^parts/.*watertight True" || true
fi
python3 check_spinner.py | tee checks/fit.txt
check() {   # print colour
    local p=$1 c=$2
    echo "== gate $p"; python3 $T/product_gate.py parts/$p.stl > checks/gate_$p.txt 2>&1; grep -E "FAIL|support|GATE" checks/gate_$p.txt
    echo "== fidelity $p"; python3 $T/print_fidelity.py --part "parts/$p.stl:$c" --no-supports --json checks/fidelity_$p.json --keep logs/fid_$p > checks/fidelity_$p.txt 2>&1
    grep -E "PRINT FIDELITY|dropped \(|filled  \(|flagged" checks/fidelity_$p.txt
    echo "== fragility $p"; python3 $T/fragility.py parts/$p.stl > checks/fragility_$p.txt 2>&1; grep FRAGILITY checks/fragility_$p.txt
}
TEAL="#3B8E8A"; CREAM="#F4F1EA"
check crown $TEAL
check base $CREAM
check stem $CREAM
A=$T/assemble_3mf.py
python3 $A --plate penny_spinner_crown.3mf parts/crown.stl:$TEAL | tail -1
python3 $A --plate penny_spinner_base_stem.3mf parts/base.stl:$CREAM + parts/stem.stl:$CREAM | tail -1
echo SHIP_DONE
