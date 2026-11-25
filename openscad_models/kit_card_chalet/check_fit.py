#!/usr/bin/env python3
"""Fit check for the chalet snap coupon (2026-11-25), on the exported parts, with manifold3d.

The base is turned show-face up (as used), each stub stood in its slot. Seated (shoulder on the
floor), nothing may overlap. Pushed half-way (nubs inside the slot), each nub must overlap the
slot wall by its reach on each side: that's how far the prongs must bend.

    python3 check_fit.py     (writes checks/fit.txt)
"""
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
GRIP, P, PITCH, BW = 3.0, 2.4, 22.0, 18.0
REACH = [0.35, 0.45, 0.55]


def M(mesh):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                                 tri_verts=np.asarray(mesh.faces, np.uint32)))


def load(n):
    return trimesh.load(HERE / "coupon" / f"coupon_{n}.stl", force="mesh")


base = load("base")
# show face up: rotate 180 about x through the floor's mid-plane, so the floor's show face is z = GRIP
base.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0], [0, BW / 2, GRIP / 2]))
B = M(base)
out = []
for i, r in enumerate(REACH):
    st = load(f"stub_{i}")
    # the stub lies in XY with its tab pointing -y, thickness in z: stand it up (tab down) in slot i
    st.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))   # y->z, z->-y
    st.apply_translation([PITCH / 2 + i * PITCH, BW / 2 + P / 2, GRIP])
    seated = (M(st) ^ B).volume()
    lo = st.copy(); lo.apply_translation([0, 0, 0.05])
    lift = (M(lo) ^ B).volume()
    half = st.copy(); half.apply_translation([0, 0, 1.3])          # nubs up inside the slot
    hv = (M(half) ^ B).volume()
    out.append(f"stub {i + 1} (reach {r}): seated overlap {seated:.3f} mm3, 0.05 above {lift:.3f}; "
               f"half-way in {hv:.2f} mm3 (the nubs must bend in)")
(HERE / "checks").mkdir(exist_ok=True)
(HERE / "checks" / "fit.txt").write_text("\n".join(out) + "\n")
print("\n".join(out))
