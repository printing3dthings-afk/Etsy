#!/usr/bin/env python3
"""Clean the manifold engine's STLs in place (2026-10-30).

OpenSCAD 2026's manifold backend leaves zero-area slivers at T-junctions, and
some come out as zero-volume shells beside the real solid (the monster's merged
print read as 53 bodies, 52 of them of volume 0.00). Round-tripping through
manifold3d and dropping every shell under 0.01 mm3 keeps exactly the real
geometry: the volume is printed before and after so a real piece can never be
dropped unnoticed.

    python3 clean_parts.py love_monster/parts/*.stl
"""
import sys
from pathlib import Path

import manifold3d as mf

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from part_mesh import load, to_trimesh  # noqa: E402

for p in sys.argv[1:]:
    m = load(p)
    comps = [c for c in m.decompose() if abs(c.volume()) >= 0.01]
    out = mf.Manifold.batch_boolean(comps, mf.OpType.Add) if len(comps) > 1 else comps[0]
    tm = to_trimesh(out)
    # zero-area faces go only if the mesh stays closed without them: on the fur
    # cap removing them opened 21 edges (2026-10-30)
    keep = tm.copy()
    keep.update_faces(keep.nondegenerate_faces())
    keep.remove_unreferenced_vertices()
    if keep.is_watertight:
        tm = keep
    tm.export(p)
    print(f"{p}: {m.volume():.2f} -> {out.volume():.2f} mm3, {len(comps)} bodies, watertight {tm.is_watertight}")
