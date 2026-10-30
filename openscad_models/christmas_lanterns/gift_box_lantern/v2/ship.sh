#!/usr/bin/env bash
# Gift box lantern v2: export every part (OpenSCAD 2026's manifold engine,
# then clean_parts.py), the fit check, product gate on every print, print
# fidelity on every colour part, fragility, the 3MFs (one plate per colour).
#   ./ship.sh            export and check
#   ./ship.sh checks     check only
set -uo pipefail
cd "$(dirname "$0")"
T=../../../../tools
export OPENSCADPATH="$(cd ../../../../assets/openscad_libs && pwd)"
FAST=${OPENSCAD_FAST:-/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun}
F=gift_box_lantern_v2.scad
PARTS="frame top lid ribbon bow top_use lid_use ribbon_use bow_use"
for k in 0 1 2 3; do PARTS="$PARTS panel_$k panel_glass_$k panel_art_$k panel_${k}_use"; done
mkdir -p parts logs checks
if [ "${1:-}" != checks ]; then
    for p in $PARTS; do "$FAST" --backend=manifold --export-format binstl -D "part=\"$p\"" -o parts/$p.stl $F > logs/$p.log 2>&1 & done; wait
    grep -l "WARNING\|ERROR" logs/*.log && echo "(warnings above)"
    python3 ../../../valentine_2027/mailboxes/clean_parts.py $(for p in $PARTS; do echo parts/$p.stl; done) | grep -v "^parts/.*watertight True" || true
fi
python3 check_v2.py
check() {   # print colour-parts...
    local p=$1; shift
    echo "== gate $p"; python3 $T/product_gate.py parts/$p.stl > checks/gate_$p.txt 2>&1; grep -E "FAIL|support|GATE" checks/gate_$p.txt
    local a=(); for x in "$@"; do a+=(--part "parts/$x"); done
    echo "== fidelity $p"; python3 $T/print_fidelity.py "${a[@]}" --no-supports --json checks/fidelity_$p.json --keep logs/fid_$p > checks/fidelity_$p.txt 2>&1
    grep -E "PRINT FIDELITY|dropped \(|filled  \(|flagged" checks/fidelity_$p.txt
    echo "== fragility $p"; python3 $T/fragility.py $(for x in "$@"; do echo parts/${x%%:*}; done) > checks/fragility_$p.txt 2>&1; tail -1 checks/fragility_$p.txt
}
G="#2F6B45"; W="#F4F1EA"; R="#C62F3A"
check frame frame.stl:$G
check top top.stl:$G
check lid lid.stl:$G
check ribbon ribbon.stl:$R
check bow bow.stl:$R
for k in 0 1 2 3; do check panel_$k panel_glass_$k.stl:$W panel_art_$k.stl:$G; done
A=$T/assemble_3mf.py
python3 $A --plate gift_box_lantern_v2_green.3mf parts/frame.stl:$G + parts/top.stl:$G + parts/lid.stl:$G | tail -1
python3 $A --plate gift_box_lantern_v2_glass.3mf $(for k in 0 1 2 3; do [ $k -gt 0 ] && echo +; echo parts/panel_glass_$k.stl:$W parts/panel_art_$k.stl:$G; done) | tail -1
python3 $A --plate gift_box_lantern_v2_red.3mf parts/ribbon.stl:$R + parts/bow.stl:$R | tail -1
echo SHIP_DONE
