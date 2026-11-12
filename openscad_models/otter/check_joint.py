#!/usr/bin/env python3
"""Fit check for the otter joint coupon, on the exported parts (parts/pin*.stl,
parts/ring*.stl). For each gap it measures, by moving the real meshes:

  rest      the two parts don't touch, and the smallest gap between them
  swing     how far the pin side turns about the pin's axis before it touches the
            ring (needs >= 15 deg each way, and a stop before 35)
  lift      how far the pin lifts before the bulge catches (must catch, < 1.5 mm)
  pull      how far the pin pulls straight out of the C before it catches
            (must catch, < 1.5 mm)

    python3 check_joint.py      (writes checks/fit.txt)
"""
import sys
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
PITCH = 24.0
GAPS = [0.30, 0.35, 0.45]


def M(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def overlap(a, b):
    return (a ^ b).volume()


def turned(m, deg, centre):
    return m.translate([-centre[0], -centre[1], 0]).rotate([0, 0, deg]).translate([centre[0], centre[1], 0])


def first_contact(make, steps):
    for s in steps:
        if overlap(*make(s)) > 1e-3:
            return s
    return None


def main():
    rows, ok = [], True
    for i, g in enumerate(GAPS):
        pin_t = trimesh.load(HERE / "parts" / f"pin{i}.stl")
        ring_t = trimesh.load(HERE / "parts" / f"ring{i}.stl")
        pin, ring = M(pin_t), M(ring_t)
        c = (0.0, i * PITCH)
        rest = overlap(pin, ring)
        pts = pin_t.sample(6000)
        gap = float(np.abs(trimesh.proximity.signed_distance(ring_t, pts)).min())
        swing = []
        for sign in (1, -1):
            hit = first_contact(lambda a: (turned(pin, sign * a, c), ring), np.arange(0.5, 40.01, 0.5))
            swing.append(hit)
        lift = first_contact(lambda d: (pin.translate([0, 0, d]), ring), np.arange(0.05, 3.01, 0.05))
        pull = first_contact(lambda d: (pin.translate([-d, 0, 0]), ring), np.arange(0.05, 3.01, 0.05))
        good = (rest < 1e-3 and gap >= g - 0.02 and all(s is not None and 15.0 <= s - 0.5 and s <= 35 for s in swing)
                and lift is not None and lift < 1.5 and pull is not None and pull < 1.5)
        ok &= good
        rows.append(f"gap {g:.2f}: {'ok  ' if good else 'FAIL'}  rest overlap {rest:.4f} mm3, closest {gap:.2f} mm; "
                    f"free swing +{(swing[0] or 99) - 0.5:.1f} / -{(swing[1] or 99) - 0.5:.1f} deg (stops by "
                    f"{swing[0]} / {swing[1]}); lift catches at {lift:.2f} mm; pull catches at {pull:.2f} mm")
    text = "\n".join(["OTTER JOINT COUPON FIT CHECK (exported parts, moved as rigid bodies)"] + rows
                     + ["PASS" if ok else "FAIL"])
    print(text)
    (HERE / "checks" / "fit.txt").write_text(text + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
