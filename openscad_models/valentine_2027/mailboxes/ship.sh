#!/usr/bin/env bash
# The two Valentine mailboxes: export (OpenSCAD 2026's manifold engine, then
# clean_parts.py), fits, product gate on every print, print fidelity on every
# colour part, fragility, the 3MFs. Results land in <design>/checks/.
#   ./ship.sh            export and check both
#   ./ship.sh checks     check only (parts already exported)
#   ONLY="face_print fur" ./ship.sh checks    just those prints' checks
set -uo pipefail
cd "$(dirname "$0")"
T=../../../tools
export OPENSCADPATH="$(cd ../../../assets/openscad_libs && pwd)"
FAST=${OPENSCAD_FAST:-/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun}
L="body body_red body_white body_dark body_print lid lid_use"
M="body body_use face face_white face_red face_dark face_print face_use face_white_use face_red_use face_dark_use fur fur_use"
if [ "${1:-}" != checks ]; then
    for p in $L; do (cd love_letter && "$FAST" --backend=manifold --export-format binstl -D "part=\"$p\"" -o parts/$p.stl love_letter.scad > logs/$p.log 2>&1) & done; wait
    for p in $M; do (cd love_monster && "$FAST" --backend=manifold --export-format binstl -D "part=\"$p\"" -o parts/$p.stl love_monster.scad > logs/$p.log 2>&1) & done; wait
    grep -l "WARNING\|ERROR" */logs/*.log && echo "(warnings above)"
    python3 clean_parts.py $(for p in $L; do echo love_letter/parts/$p.stl; done) $(for p in $M; do echo love_monster/parts/$p.stl; done)
fi
python3 check_mailboxes.py
check() {   # dir print colour-parts...
    local d=$1 p=$2; shift 2
    [ -n "${ONLY:-}" ] && [[ " $ONLY " != *" $p "* ]] && return
    mkdir -p $d/checks
    echo "== $d gate $p"; python3 $T/product_gate.py $d/parts/$p.stl > $d/checks/gate_$p.txt 2>&1; grep -E "FAIL|support|GATE" $d/checks/gate_$p.txt
    local a=(); for x in "$@"; do a+=(--part "$d/parts/$x"); done
    echo "== $d fidelity $p"; python3 $T/print_fidelity.py "${a[@]}" --no-supports --json $d/checks/fidelity_$p.json --keep $d/logs/fid_$p > $d/checks/fidelity_$p.txt 2>&1
    grep -E "PRINT FIDELITY|dropped \(|filled  \(|flagged" $d/checks/fidelity_$p.txt
    echo "== $d fragility $p"; python3 $T/fragility.py $(for x in "$@"; do echo $d/parts/${x%%:*}; done) > $d/checks/fragility_$p.txt 2>&1; tail -1 $d/checks/fragility_$p.txt
}
check love_letter body_print body.stl:#F6A6C1 body_red.stl:#D7263D body_white.stl:#F4F1EA body_dark.stl:#3B2A3A
check love_letter lid lid.stl:#F6A6C1
check love_monster body body.stl:#B79CE0
check love_monster face_print face.stl:#B79CE0 face_white.stl:#F4F1EA face_red.stl:#D7263D face_dark.stl:#2B2433
check love_monster fur fur.stl:#F58CB4
if [ -z "${ONLY:-}" ]; then
    A=$(cd ../../../tools && pwd)/assemble_3mf.py
    (cd love_letter && python3 $A --plate love_letter_mailbox.3mf parts/body.stl:#F6A6C1 parts/body_red.stl:#D7263D parts/body_white.stl:#F4F1EA parts/body_dark.stl:#3B2A3A + parts/lid.stl:#F6A6C1 | tail -1)
    (cd love_monster && python3 $A love_monster_body.3mf parts/body.stl:#B79CE0 | tail -1 &&
        python3 $A love_monster_face.3mf parts/face.stl:#B79CE0 parts/face_white.stl:#F4F1EA parts/face_red.stl:#D7263D parts/face_dark.stl:#2B2433 | tail -1 &&
        python3 $A love_monster_fur.3mf parts/fur.stl:#F58CB4 | tail -1)
fi
echo SHIP_DONE
