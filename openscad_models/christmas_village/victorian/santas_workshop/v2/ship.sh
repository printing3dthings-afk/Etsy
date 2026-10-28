#!/bin/bash
# After ./build.sh cgal: the shipping checks, the 3MF and the white renders.
# The union for the gate is made with manifold3d from the four CGAL parts: a
# CGAL union of this building took six hours (2026-10-15).
set -u
cd "$(dirname "$0")"
T=../../../../../tools
p=victorian_santas_workshop_v2
mkdir -p logs images
python3 - <<'EOF'
import manifold3d as mf, numpy as np, trimesh
p = "victorian_santas_workshop_v2"
ms = []
for c in ("body", "roof", "trim", "accent"):
    t = trimesh.load(f"{p}_{c}.stl", force="mesh")
    ms.append(mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32))))
u = mf.Manifold.batch_boolean(ms, mf.OpType.Add).to_mesh()
trimesh.Trimesh(np.asarray(u.vert_properties)[:, :3], np.asarray(u.tri_verts)).export("logs/union.stl")
print("union written")
EOF
echo "== product gate (union)";   python3 $T/product_gate.py logs/union.stl 2>&1 | tail -25
echo "== fragility";            python3 $T/fragility.py ${p}_body.stl ${p}_roof.stl ${p}_trim.stl ${p}_accent.stl 2>&1 | tail -3
echo "== print fidelity, matte white, one colour"
python3 $T/print_fidelity.py logs/union.stl --json logs/fidelity_white.json --keep logs/fidelity_white > logs/fidelity_white.txt 2>&1
grep -E "PRINT FIDELITY|dropped \(|filled  \(|flagged" logs/fidelity_white.txt
grep -m2 -E "estimated printing time \(normal|filament used \[g\]" logs/fidelity_white/fidelity.gcode
echo "== 3MF"
python3 $T/assemble_3mf.py $p.3mf ${p}_body.stl:#A8483A ${p}_roof.stl:#2E3440 ${p}_trim.stl:#F4F1EA ${p}_accent.stl:#2F6B45 | tail -3
echo "== as-printed renders, white"
python3 $T/as_printed.py logs/fidelity_white/fidelity.gcode --views --colour "#F4F1EA" --timeout 2400 -o images/v2_as_printed_white 2>&1 | tail -3
echo "== interior renders"
python3 render_interior.py 2>&1 | tail -3
echo SHIP_DONE
