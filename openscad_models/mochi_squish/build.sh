#!/bin/bash
# Dumpling Bun squish: export, tidy, check. Run from this folder.
set -e
export OPENSCADPATH=../../assets/openscad_libs
mkdir -p parts checks images
for p in bun coupon_1 coupon_2 coupon_3; do
  openscad -o parts/$p.stl -D "part=\"$p\"" dumpling_bun.scad 2> /dev/null
done
# OpenSCAD 2021's CGAL leaves a zero-volume two-triangle speck where two of the
# smile's hulled dimples meet (2026-11-28: 0.000 mm3, one point at the mouth).
# No material, but it counts as a second body, so keep only bodies with volume.
python3 - <<'PY'
import trimesh
for p in ["bun", "coupon_1", "coupon_2", "coupon_3"]:
    m = trimesh.load(f"parts/{p}.stl")
    bodies = [b for b in m.split(only_watertight=False) if abs(b.volume) > 1.0]
    out = trimesh.util.concatenate(bodies)
    out.export(f"parts/{p}.stl")
    print(p, len(bodies), "body", out.is_watertight, out.bounds.round(1).tolist())
PY
