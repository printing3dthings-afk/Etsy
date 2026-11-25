#!/usr/bin/env python3
"""Urban Kid: the one-piece print option (2026-11-25).

Scott: "Urban kid will have both print options": the split colour kit (v1's seven prints) and one
piece printed upright on organic tree supports. This builds the one piece from the kit's parts as
they stand assembled (../../parts/assembled/), so the two can never drift apart: every part joined
into one body, the gaps the pegs sit in filled, then scaled to Scott's 190 mm (v1 is 116.8).

The v2 head waits on head test 2 (../head_test_2/); until then this uses v1's head. When the v2
parts land, point PARTS at them and re-run.

    python3 make_one_piece.py [OUT.stl]
"""
import sys
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
PARTS = HERE.parents[1] / "parts" / "assembled"
NAMES = ["base", "shoe_r", "shoe_l", "pants", "hoodie", "head", "cap", "chain"]
HEIGHT = 190.0
SEAT = 0.4


def M(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                                 tri_verts=np.asarray(m.faces, np.uint32)))


def main(out):
    acc = None
    for n in NAMES:
        t = trimesh.load(PARTS / f"{n}.stl")
        if n == "chain":
            # in the kit the chain is glued on and stands a hair off the chest; here it's seated
            # 0.4 into it (+y is into the body), or it prints as a separate, floating piece
            t.apply_translation([0, SEAT, 0])
        p = M(t)
        acc = p if acc is None else acc + p
    mo = acc.to_mesh()
    m = trimesh.Trimesh(mo.vert_properties[:, :3], mo.tri_verts, process=True)
    bodies = m.split(only_watertight=False)
    # the 0.15 clearances round the pegs close into sealed pockets inside the union; they come
    # out as inside-out shells (negative volume). Dropped, the inside is solid.
    keep = [b for b in bodies if b.volume > 0]
    print(f"union: {len(bodies)} shells, {len(bodies) - len(keep)} sealed pockets dropped, "
          f"{len(keep)} solid bodies {[round(b.volume) for b in keep]}")
    m = trimesh.util.concatenate(keep)
    s = HEIGHT / m.extents[2]
    m.apply_scale(s)
    m.apply_translation(-m.bounds[0] * [0, 0, 1])
    m.export(out)
    print(f"scaled x{s:.3f} to {m.extents.round(1)} mm, {m.volume / 1000:.1f} cm3, watertight {m.is_watertight}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(HERE / "urban_kid_one_piece_190.stl"))
