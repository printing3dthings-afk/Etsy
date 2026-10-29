#!/usr/bin/env bash
# After ./build.sh: fits, product gate on every print, print fidelity on every
# colour part, fragility, the 3MFs. Results land in <design>/checks/.
#   ./ship.sh tin|jar
set -uo pipefail
cd "$(dirname "$0")"
T=../../tools
d=$1
python3 check_clickers.py $d
case $d in
tin) D=gingerbread_tin; prints="tin_print lid_print cookie_print"
     objs=("parts/tin.stl:#B3262E parts/tin_snow.stl:#F4F1EA" "parts/lid.stl:#B3262E parts/lid_holly.stl:#3E8E4A parts/lid_snow.stl:#F4F1EA"
           "parts/cookie.stl:#9A5B2E parts/cookie_icing.stl:#F4F1EA parts/cookie_red.stl:#B3262E parts/cookie_green.stl:#3E8E4A")
     loose="parts/cookie_loose.stl:#9A5B2E parts/cookie_icing.stl:#F4F1EA parts/cookie_red.stl:#B3262E parts/cookie_green.stl:#3E8E4A"
     out=gingerbread_tin_clicker ;;
jar) D=cookie_jar; prints="jar_print top_print gb_print"
     objs=("parts/jar.stl:#A9DCC8 parts/jar_label.stl:#F4F1EA parts/jar_letters.stl:#B3262E" "parts/top.stl:#A9DCC8 parts/top_rim.stl:#B3262E"
           "parts/gb.stl:#9A5B2E parts/gb_icing.stl:#F4F1EA parts/gb_red.stl:#B3262E")
     loose="parts/gb_loose.stl:#9A5B2E parts/gb_icing.stl:#F4F1EA parts/gb_red.stl:#B3262E"
     out=cookie_jar_clicker ;;
esac
cd $D; mkdir -p checks
for p in $prints; do
    echo "== gate $p"; python3 ../$T/product_gate.py parts/$p.stl > checks/gate_$p.txt 2>&1; grep -E "FAIL|GATE" checks/gate_$p.txt
done
i=0
for o in "${objs[@]}"; do
    i=$((i+1)); a=(); for x in $o; do a+=(--part "$x"); done
    echo "== fidelity, print $i"
    python3 ../$T/print_fidelity.py "${a[@]}" --no-supports --json checks/fidelity_$i.json --keep logs/fid_$i > checks/fidelity_$i.txt 2>&1
    grep -E "PRINT FIDELITY|dropped \(|filled  \(|flagged" checks/fidelity_$i.txt
    echo "== fragility, print $i"; python3 ../$T/fragility.py $(for x in $o; do echo ${x%%:*}; done) > checks/fragility_$i.txt 2>&1; tail -2 checks/fragility_$i.txt
done
echo "== 3MF"
python3 ../$T/assemble_3mf.py --plate $out.3mf ${objs[0]} + ${objs[1]} + ${objs[2]} | tail -2
python3 ../$T/assemble_3mf.py ${out}_loose_cap.3mf $loose | tail -1
echo SHIP_DONE
