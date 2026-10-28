#!/usr/bin/env python3
"""The Nesting Cats' fits (2026-10-28), measured on the exported halves:

- each cat closes: the top screwed down onto its bottom, and at points up the
  thread on the way, overlaps the bottom nowhere
- each cat nests: the next one, closed, stood on the floor inside, overlaps the
  outer cat nowhere
- each cat goes in: the next one's widest point, paws and all, passes the
  outer's neck bore with room to spare

    python3 check_cats.py <dir with the exported parts>

Numbers are mm3 of overlap, and mm of radial room. The sizes and seam mirror
nesting_cats.scad.
"""
import sys
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

D = Path(sys.argv[1] if len(sys.argv) > 1 else "parts")
HS = [90, 72, 57, 43, 30]
FL, TP = 1.8, 3.0
ROOM = 0.3          # the least radial room for a cat going through a neck


def load(name):
    t = trimesh.load(D / f"{name}.stl", force="mesh")
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32),
                               tri_verts=np.asarray(t.faces, np.uint32))), t


def colours(stem):
    """A part in its colours (body, trim, dark, pink), as one solid and one mesh."""
    ms = [load(p.stem) for p in sorted(D.glob(f"{stem}_*.stl"))]
    return mf.Manifold.batch_boolean([m for m, _ in ms], mf.OpType.Add), trimesh.util.concatenate([t for _, t in ms])


def top(i):
    return colours(f"cat{i}_top")


def closed(i):
    """Figure i as it stands, the top screwed on (the top is exported standing
    on its rim, so it goes back up by the seam's height)."""
    if i == 4:
        return colours("cat4_solid")
    b, tb = load(f"cat{i}_bottom")
    t, tt = top(i)
    zs = 0.30 * HS[i]
    return b + t.translate([0, 0, zs]), trimesh.util.concatenate([tb, tt.copy().apply_translation([0, 0, zs])])


def bore(i):
    """The neck's bore: the least radius of the bottom's opening, measured
    across the neck."""
    _, tb = load(f"cat{i}_bottom")
    zs = 0.30 * HS[i]
    s = tb.section([0, 0, 1], [0, 0, zs + 2.5])
    p, _ = s.to_2D(to_2D=np.eye(4))
    return min(np.hypot(*np.array(h.coords).T).min() for poly in p.polygons_full for h in poly.interiors)


bad = 0
for i in range(4):
    b, _ = load(f"cat{i}_bottom")
    t, _ = top(i)
    zs = 0.30 * HS[i]
    # closed, and part way on: turned by a and lifted a / 360 of a pitch (the thread rises with the angle)
    worst = max((b ^ t.rotate([0, 0, a]).translate([0, 0, zs + TP * a / 360])).volume() for a in (0, 90, 180, 360))
    _, inner_mesh = closed(i + 1)
    inner_r = np.hypot(inner_mesh.vertices[:, 0], inner_mesh.vertices[:, 1]).max()
    room = bore(i) - inner_r
    outer, _ = closed(i)
    inner, _ = closed(i + 1)
    nest = (outer ^ inner.translate([0, 0, FL])).volume()
    print(f"cat {i}: top on bottom {worst:.3f}   cat {i + 1} through the neck: room {room:+.2f} mm   "
          f"cat {i + 1} inside {nest:.3f}")
    # 0.01 mm3: where the top's rim sits on the bottom's shoulder the faces
    # touch, and the boolean reads 0.001 there on cats 1 and 2 (2026-10-28)
    bad += (worst > 1e-2) + (room < ROOM) + (nest > 1e-2)
print("CATS FIT" if not bad else f"CATS: {bad} problem(s)")
sys.exit(1 if bad else 0)
