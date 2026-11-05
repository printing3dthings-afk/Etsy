#!/usr/bin/env bash
# After ./build.sh: fits, product gate on every print, print fidelity on every
# colour part, fragility, the 3MFs. Results land in <design>/checks/.
#   ./ship.sh tin|canister|jar
# The gingerbread prints declare their thread teeth, the cookie's switch socket
# and their raised colour detail to the gate's wall floor (wall_regions.py; why,
# in CLICKERS_PRINTING.md). Everything else on them is held to 1.2 mm.
set -uo pipefail
cd "$(dirname "$0")"
T=../../tools
d=$1
skip=no
case $d in
canister) python3 gingerbread_tin/check_canister.py | tee gingerbread_tin/checks/fit_canister.txt ;;
*) python3 check_clickers.py $d ;;
esac
case $d in
tin) D=gingerbread_tin; prints="tin_print lid_print cookie_print"
     objs=("parts/tin.stl:#B3262E parts/tin_snow.stl:#F4F1EA" "parts/lid.stl:#B3262E parts/lid_holly.stl:#3E8E4A parts/lid_snow.stl:#F4F1EA"
           "parts/cookie.stl:#9A5B2E parts/cookie_icing.stl:#F4F1EA parts/cookie_red.stl:#B3262E parts/cookie_green.stl:#3E8E4A")
     loose="parts/cookie_loose.stl:#9A5B2E parts/cookie_icing.stl:#F4F1EA parts/cookie_red.stl:#B3262E parts/cookie_green.stl:#3E8E4A"
     out=gingerbread_tin_clicker; skip=yes ;;
canister) D=gingerbread_tin; prints="canister_print lid_closed_print"
     objs=("parts/canister.stl:#B3262E parts/canister_snow.stl:#F4F1EA"
           "parts/lid_closed.stl:#B3262E parts/lid_closed_holly.stl:#3E8E4A parts/lid_closed_snow.stl:#F4F1EA"
           "parts/cookie.stl:#9A5B2E parts/cookie_icing.stl:#F4F1EA parts/cookie_red.stl:#B3262E parts/cookie_green.stl:#3E8E4A")
     loose=""; out=gingerbread_tin_canister; skip=yes ;;
jar) D=cookie_jar; prints="jar_print top_print gb_print"
     objs=("parts/jar.stl:#A9DCC8 parts/jar_label.stl:#F4F1EA parts/jar_letters.stl:#B3262E" "parts/top.stl:#A9DCC8 parts/top_rim.stl:#B3262E"
           "parts/gb.stl:#9A5B2E parts/gb_icing.stl:#F4F1EA parts/gb_red.stl:#B3262E")
     loose="parts/gb_loose.stl:#9A5B2E parts/gb_icing.stl:#F4F1EA parts/gb_red.stl:#B3262E"
     out=cookie_jar_clicker ;;
esac
cd $D; mkdir -p checks
for p in $prints; do
    flags=""; [ $skip = yes ] && flags=$(python3 ../wall_regions.py $p)
    echo "== gate $p"; python3 ../$T/product_gate.py parts/$p.stl $flags > checks/gate_$p.txt 2>&1; grep -E "FAIL|min_wall|GATE" checks/gate_$p.txt
done
# the canister's own prints are 1 and 2 of its plate; the cookie, 3, is the clicker's
i=0; tag=""; [ $d = canister ] && tag=canister_
for o in "${objs[@]}"; do
    i=$((i+1)); [ $d = canister ] && [ $i = 3 ] && continue
    a=(); for x in $o; do a+=(--part "$x"); done
    echo "== fidelity, print $i"
    n=$tag$i; [ $d = canister ] && { [ $i = 1 ] && n=canister || n=lid_closed; }
    python3 ../$T/print_fidelity.py "${a[@]}" --no-supports --json checks/fidelity_$n.json --keep logs/fid_$n > checks/fidelity_$n.txt 2>&1
    grep -E "PRINT FIDELITY|dropped \(|filled  \(|flagged" checks/fidelity_$n.txt
    echo "== fragility, print $i"; python3 ../$T/fragility.py $(for x in $o; do echo ${x%%:*}; done) > checks/fragility_$n.txt 2>&1; tail -2 checks/fragility_$n.txt
done
echo "== 3MF"
python3 ../$T/assemble_3mf.py --plate $out.3mf ${objs[0]} + ${objs[1]} + ${objs[2]} | tail -2
[ -n "$loose" ] && python3 ../$T/assemble_3mf.py ${out}_loose_cap.3mf $loose | tail -1
echo SHIP_DONE
