#!/usr/bin/env python3
"""Plinko v2 BB test print: the fit (manifold3d, on the exported parts) and the check set
(tools/model_checks.py). 2026-11-25.

    python3 check_bb.py            (fit, then parts, gate, 3mf, fidelity, fragility)
    python3 check_bb.py fit
"""
import sys
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from model_checks import run_checks  # noqa: E402

FLOOR, D, TOPWALL, H = 1.4, 6.8, 3.0, 34.0
REACH = [0.35, 0.45, 0.55]


def M(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                                 tri_verts=np.asarray(m.faces, np.uint32)))


def fit():
    board = M(trimesh.load(HERE / "bb_coupon_board.stl"))
    out = []
    for i, r in enumerate(REACH):
        p = trimesh.load(HERE / f"bb_coupon_plug_{i}.stl")
        p.apply_translation([0, H / 2 + TOPWALL, FLOOR + 0.2])          # seated: shoulder on the wall
        seated = (M(p) ^ board).volume()
        up = p.copy(); up.apply_translation([0, 0.05, 0])
        half = p.copy(); half.apply_translation([0, 1.6, 0])            # nubs inside the port
        out.append(f"plug {i + 1} (reach {r}): seated overlap {seated:.3f} mm3, 0.05 out {(M(up) ^ board).volume():.3f}; "
                   f"half-way in {(M(half) ^ board).volume():.2f} mm3 (the prongs must bend in)")
    # a BB down the middle and along each side: does a 6 mm sphere fit the chamber depth?
    bb = trimesh.creation.icosphere(subdivisions=3, radius=3.0)
    for x, y in [(0, 5), (-12, 8), (12, 8), (0, -12)]:
        b = bb.copy(); b.apply_translation([x, y, FLOOR + D / 2])
        out.append(f"BB at ({x}, {y}) mid-depth: overlap {(M(b) ^ board).volume():.3f} mm3")
    (HERE.parent / "checks" / "fit_bb.txt").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    steps = sys.argv[1:]
    if not steps or "fit" in steps:
        fit()
    steps = [s for s in steps if s != "fit"] or ["parts", "gate", "3mf", "fidelity", "fragility"]
    C = "#EDE8DC"
    run_checks(HERE, "bb_coupon", dict(
        label="Plinko v2: BB test", note="The Plinko cage sized for 6 mm airsoft BBs, two peg rows, a loading "
        "port and three snap-in plugs (reach 0.35, 0.45, 0.55). A test print.",
        objects=[[("board", C)], [("plug_0", C)], [("plug_1", C)], [("plug_2", C)]],
        unions=["bb_coupon_board.stl", "bb_coupon_plug_0.stl", "bb_coupon_plug_1.stl", "bb_coupon_plug_2.stl"],
        tags=["_board", "_plug_0", "_plug_1", "_plug_2"], source="plinko/v2/bb_coupon.3mf"), steps)
