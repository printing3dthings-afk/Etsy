#!/bin/bash
# After ./build.sh cgal: the shipping checks, the 3MF and the white renders.
#
# Two unions (2026-10-28). manifold3d's (tools/part_mesh.py, a minute) is
# used for slicing and renders, but where two colour parts meet only along an
# edge it leaves edges shared by four faces and slivers the gate counts as
# open and as bodies, and the slicer props them: on the listed v1 parts it
# reads 27 slivers, 161 such edges and 7,665 support moves, where v1's CGAL
# union passed with none. So the gate's verdict is taken on the CGAL union
# (part="union", hours), run last and alone: two CGAL jobs at once ran the
# container out of memory.
set -u
cd "$(dirname "$0")"
T=../../../../../tools
p=victorian_santas_workshop_v2
export OPENSCADPATH="$(cd ../../../../../assets/openscad_libs && pwd)"
mkdir -p logs images
python3 $T/part_mesh.py union logs/union.stl ${p}_body.stl ${p}_roof.stl ${p}_trim.stl ${p}_accent.stl 2>&1 | tail -1
echo "== fragility";  python3 $T/fragility.py ${p}_body.stl ${p}_roof.stl ${p}_trim.stl ${p}_accent.stl 2>&1 | tail -1
echo "== print fidelity, matte white, one colour, supports off"
python3 $T/print_fidelity.py logs/union.stl --no-supports --json logs/fidelity_white.json --keep logs/fidelity_white > logs/fidelity_white.txt 2>&1
grep -E "PRINT FIDELITY|dropped \(|filled  \(|flagged" logs/fidelity_white.txt
grep -m2 -E "estimated printing time \(normal|filament used \[(g|mm)\]" logs/fidelity_white/fidelity.gcode
echo "== 3MF"
python3 $T/assemble_3mf.py $p.3mf ${p}_body.stl:#A8483A ${p}_roof.stl:#2E3440 ${p}_trim.stl:#F4F1EA ${p}_accent.stl:#2F6B45 | tail -3
echo "== as-printed renders, white"
python3 $T/as_printed.py logs/fidelity_white/fidelity.gcode --views --colour "#F4F1EA" --timeout 2400 -o images/v2_as_printed_white 2>&1 | tail -3
echo "== interior renders"
python3 render_interior.py 2>&1 | tail -3
echo "== CGAL union, then the product gate on it"
openscad -D 'part="union"' -o logs/union_cgal.stl $p.scad > logs/union_cgal.log 2>&1
python3 $T/product_gate.py logs/union_cgal.stl 2>&1 | tail -16
echo SHIP_DONE
