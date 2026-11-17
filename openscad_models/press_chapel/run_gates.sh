#!/bin/bash
# Press-to-Light Chapel drop test print: every check on the exported parts (2026-11-17).
#   ./run_gates.sh     (after make_coupon.sh; writes checks/)
# The shaft declares two bands to the wall check, both thin on purpose and carrying no load:
# the taper above the star, where the teeth shrink into the rod, and the pointed tip. Their
# heights (print z) come from drop_coupon.scad's echo.
set -e
cd "$(dirname "$0")"
T=../../tools
python3 check_coupon.py > /dev/null; tail -1 checks/fit_coupon.txt
python3 chapel_budget.py > /dev/null; grep "RESULT" checks/budget.txt
: > checks/gate_parts.txt
for p in base arch steeple hub_1 hub_2 hub_3; do
  echo "== $p" >> checks/gate_parts.txt; python3 $T/product_gate.py parts/$p.stl >> checks/gate_parts.txt 2>&1 || true
done
echo "== shaft" >> checks/gate_parts.txt
# the bands' heights from the .scad's own echo, so they follow any change to the shaft
read t0 t1 p0 p1 < <(openscad -o /tmp/_shaft_$$.stl -D 'part="print_shaft"' drop_coupon.scad 2>&1 | \
  python3 -c "import re,sys; e=[float(x) for x in re.findall(r'-?\d+\.?\d*', sys.stdin.read().split('taper print z')[1])[:4]]; print(e[0]-0.1, e[1]+0.1, e[2]-0.1, e[3]+0.1)")
rm -f /tmp/_shaft_$$.stl
python3 $T/product_gate.py parts/shaft.stl --wall-skip-band 0,3.4,$t0,$t1 --wall-skip-band 0,3.4,$p0,$p1 >> checks/gate_parts.txt 2>&1 || true
grep "^==\|FAIL\|PASSED\|FAILED" checks/gate_parts.txt
python3 $T/fragility.py parts/shaft.stl parts/hub_2.stl parts/arch.stl parts/base.stl > checks/fragility_parts.txt 2>&1
grep FRAGILITY checks/fragility_parts.txt
