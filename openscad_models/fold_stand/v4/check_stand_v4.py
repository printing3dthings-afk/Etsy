#!/usr/bin/env python3
"""Fold Stand v4, the exported parts posed together (2026-11-10).

1. The plate's print: the prop lies in its slot, print-in-place, nowhere closer to the
   plate than the gaps it needs (0.4 sides, 0.45 cones), and it swings out behind the
   plate from folded to the steepest notch's angle and beyond without touching it.
2. At each of the six angles: no part overlaps another; the open gaps; the foot in its
   notch.
3. Folded (plate down on the base, prop flush in it): nothing overlaps.
4. The pivot twist-lock: from folded to 85 deg, the plate pushed 2 mm up the lugs'
   slots hits the lugs (it is captured); at 145 deg it lifts out of them 15 mm free.
   The plate turns from 0 to 90 without touching the base.
5. The prop's hinge: pushed sideways 1 mm either way, the cones stop it.

    python3 check_stand_v4.py
"""
import math
import re
import sys
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
SCAD = (HERE / "fold_stand_v4.scad").read_text()


def num(name):
    return float(re.search(rf"^{name} = (?:COUPON \? [0-9.]+ : )?([0-9.]+);", SCAD, re.M).group(1))


ANGLES = [float(a) for a in re.search(r"ANGLES = \[([0-9, ]+)\]", SCAD).group(1).split(",")]
NOTCH_Y = [float(a) for a in re.search(r"NOTCH_Y = \[([0-9., ]+)\]", SCAD).group(1).split(",")]
PZ, PIN, HIN, A, L = num("PIVOT_Z"), num("PIVOT_IN"), num("HINGE_IN"), num("A"), num("L")
NZ, RF = num("NOTCH_Z"), num("R_FOOT")
PASS = 180 - num("PSI")
fail = []


def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fail.append(msg)


def rx(deg, about=(0, 0, 0)):
    return trimesh.transformations.rotation_matrix(math.radians(deg), [1, 0, 0], about)


def tr(x, y, z):
    t = np.eye(4); t[:3, 3] = [x, y, z]
    return t


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def ov(a, b):
    return (man(a) ^ man(b)).volume()


def gap(a, b, n=8000, keep=None):
    p = a.sample(n, seed=1)
    if keep is not None:
        p = p[keep(p)]
    d = -trimesh.proximity.ProximityQuery(b).signed_distance(p)
    return float(d.min())


def plate_T(th):
    return tr(0, 0, PZ) @ rx(th) @ tr(0, 0, -PIN)


def hinge_at(th):
    c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
    return A * c - (HIN - PIN) * s, PZ + A * s + (HIN - PIN) * c


def rho(th, fy):
    hy, hz = hinge_at(th)
    toward = math.degrees(math.atan2(NZ - hz, fy - hy)) - th
    return toward - math.degrees(math.atan2(RF - HIN, L))


def prop_in_plate(r):
    return rx(r, (0, A, HIN))


def load(k):
    return trimesh.load(HERE / "parts" / f"{k}.stl", force="mesh")


def main():
    base, plate, prop = load("base"), load("plate_only"), load("prop_only")
    print("== the plate's print: the prop in its slot")
    check(ov(plate, prop) < 0.01, f"prop and plate are apart ({ov(plate, prop):.3f} mm3)")
    g = gap(prop, plate)
    check(g >= 0.38, f"least gap prop to plate {g:.2f} (0.4 at its sides, 0.45 at the cones)")
    # it swings out behind the plate from folded through every working angle and 4 past
    # the steepest notch's; the slot's end below the hinge stops it somewhere after that
    work = [rho(th, fy) for th, fy in zip(ANGLES, NOTCH_Y)]
    far = min(work) - 4
    swing = [r for r in np.arange(0, far - 0.1, -2.5) if ov(prop.copy().apply_transform(prop_in_plate(r)), plate) > 0.05]
    stop = next((r for r in range(int(far), -200, -1) if ov(prop.copy().apply_transform(prop_in_plate(r)), plate) > 0.05), None)
    check(not swing, f"it swings out behind the plate from folded to {far:.0f} deg (working {max(work):.0f} to "
          f"{min(work):.0f}) without touching; the slot's end stops it at {stop} deg"
          + (f" (touches at {swing})" if swing else ""))
    for side in (-1, 1):
        hit = ov(prop.copy().apply_translation([side * 1.0, 0, 0]), plate)
        check(hit > 0.5, f"pushed 1 mm {'left' if side < 0 else 'right'}, a cone stops it ({hit:.1f} mm3)")

    print("== at each angle")
    for th, fy in zip(ANGLES, NOTCH_Y):
        P = plate.copy().apply_transform(plate_T(th))
        Q = prop.copy().apply_transform(plate_T(th) @ prop_in_plate(rho(th, fy)))
        o = {"plate/base": ov(P, base), "prop/base": ov(Q, base), "prop/plate": ov(Q, P)}
        check(max(o.values()) < 0.05, f"{th:.0f} deg: no overlap ({', '.join(f'{k} {v:.3f}' for k, v in o.items())})")
        gp = gap(P, base)
        gf = gap(Q, base)
        check(gp >= 0.3 and gf >= 0.3, f"{th:.0f} deg: gaps plate-base {gp:.2f}, prop-base {gf:.2f} (foot in notch {fy:.1f})")
        # the foot sits in its notch: its centre over the trough's
        foot = (plate_T(th) @ prop_in_plate(rho(th, fy)) @ np.array([0, A + L, RF, 1]))[:3]
        check(abs(foot[1] - fy) < 0.05 and abs(foot[2] - NZ) < 0.05, f"{th:.0f} deg: the foot's centre at y {foot[1]:.2f} z {foot[2]:.2f}")

    print("== folded")
    P = plate.copy().apply_transform(plate_T(0))
    Q = prop.copy().apply_transform(plate_T(0))
    check(ov(P, base) < 0.05 and ov(Q, base) < 0.05, f"plate and prop lie on the base without overlap "
          f"({ov(P, base):.3f}, {ov(Q, base):.3f} mm3); plate's back {gap(P, base):.2f} over it at the least")
    hi = max(P.bounds[1][2], Q.bounds[1][2])
    print(f"  folded height {hi:.1f} mm, footprint {base.extents[0]:.0f} x {base.extents[1]:.0f} mm")

    print("== the pivot twist-lock")
    s = (0, 0.0, 1.0)                      # the slots rise straight up
    free = [th for th in range(0, 91, 5) if ov(plate.copy().apply_transform(plate_T(th)), base) > 0.05]
    check(not free, "the plate turns from 0 to 90 deg in its lugs without touching the base"
          + (f" (touches at {free})" if free else ""))
    loose = []
    for th in range(0, 86, 5):
        moved = plate.copy().apply_transform(tr(0, 2 * s[1], 2 * s[2]) @ plate_T(th))
        if ov(moved, base) < 0.5:
            loose.append(th)
    check(not loose, "from folded to 85 deg, lifted 2 mm up the slots it hits the lugs: captured"
          + (f" (free at {loose})" if loose else ""))
    path = [ov(plate.copy().apply_transform(tr(0, d * s[1], d * s[2]) @ plate_T(PASS)), base) for d in (0, 3, 6, 9, 12, 15)]
    check(max(path) < 0.05, f"at {PASS:.0f} deg it lifts 15 mm out of the slots untouched (max {max(path):.3f} mm3): how it goes on")
    print("\nV4 CHECK " + ("FAILED: " + "; ".join(fail) if fail else "OK"))
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
