#!/usr/bin/env python3
"""Fold Stand v3, the three exported parts posed together at every angle (2026-11-10).

For each of the six angles, from the parts exactly as they print:
- no two parts overlap (manifold intersection volume);
- the open gaps: tongue to groove, foot to notch, and everything else, against the
  0.3 mm that reliably stays open between printed parts;
- the nose: where it touches the plate, it is in the pocket's top corner (the designed
  bearing) and nowhere else;
- the plate turns from 54 to 90 deg in its groove without touching the base (and, for the
  record, how far it falls back with the prop out).
Then each print lies flat on the bed and fits the P1S.

    python3 check_stand_v3.py
"""
import math
import re
import sys
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
SCAD = (HERE / "fold_stand_v3.scad").read_text()


def num(name):
    return float(re.search(rf"^{name} = (?:COUPON \? [0-9.]+ : )?([0-9.]+);", SCAD, re.M).group(1))


ANGLES = [float(a) for a in re.search(r"ANGLES = \[([0-9, ]+)\]", SCAD).group(1).split(",")]
NOTCH_Y = [float(a) for a in re.search(r"NOTCH_Y = \[([0-9., ]+)\]", SCAD).group(1).split(",")]
PIVOT_Z, TONGUE_R, A_SOCKET = num("PIVOT_Z"), num("TONGUE_R"), num("A_SOCKET")
NOSE_R, NOSE_IN, NOTCH_Z, PROP_W = num("NOSE_R"), num("NOSE_IN"), num("NOTCH_Z"), num("PROP_W")
GAP_MIN = 0.3
_fail = []


def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        _fail.append(msg)


def rx(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]])


def rz(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])


def tr(x, y, z):
    t = np.eye(4)
    t[:3, 3] = [x, y, z]
    return t


def nose(th):
    c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
    off = TONGUE_R - NOSE_IN
    return A_SOCKET * c + off * s, PIVOT_Z + A_SOCKET * s - off * c


def plate_T(th):
    return tr(0, 0, PIVOT_Z) @ rx(th) @ tr(0, 0, -TONGUE_R)


def prop_T(th, fy):
    ny, nz = nose(th)
    pa = math.degrees(math.atan2(nz - NOTCH_Z, ny - fy))
    return tr(0, fy, NOTCH_Z) @ rx(pa) @ rz(90) @ rx(90) @ tr(0, 0, -PROP_W / 2)


def manifold(mesh):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                                 tri_verts=np.asarray(mesh.faces, np.uint32)))


def overlap(a, b):
    return (manifold(a) ^ manifold(b)).volume()


def gap(a, b, n=8000, keep=None):
    """Least distance from points on a's surface to b (with where), optionally only over
    the points keep(p) is true for."""
    pts = a.sample(n, seed=1) if hasattr(a.sample, "__call__") else a.sample(n)
    if keep is not None:
        pts = pts[keep(pts)]
    if not len(pts):
        return float("inf"), None
    q = trimesh.proximity.ProximityQuery(b)
    d = q.signed_distance(pts)      # positive inside b
    i = int(np.argmax(d))
    return -float(d[i]), pts[i]


def main():
    P = {k: trimesh.load(HERE / "parts" / f"{k}.stl") for k in ("base", "plate", "prop")}
    print("== each print, as it lies on the bed")
    for k, m in P.items():
        lo, hi = m.bounds
        size = hi - lo
        check(abs(lo[2]) < 1e-3 and m.is_watertight and max(size[:2]) <= 256,
              f"{k}: {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm, on the bed, watertight")
    base = P["base"]
    print("== posed at each angle (nominal: every joint centred in its clearance)")
    for th, fy in zip(ANGLES, NOTCH_Y):
        plate = P["plate"].copy().apply_transform(plate_T(th))
        prop = P["prop"].copy().apply_transform(prop_T(th, fy))
        ny, nz = nose(th)
        ov = {"plate/base": overlap(plate, base), "prop/base": overlap(prop, base), "prop/plate": overlap(prop, plate)}
        g_pb, _ = gap(plate, base)
        g_fb, _ = gap(prop, base)
        # the prop against the plate, away from the nose (its designed bearing)
        far = lambda p: np.hypot(p[:, 1] - ny, p[:, 2] - nz) > NOSE_R + 0.6
        g_pp, where = gap(prop, plate, keep=far)
        near = lambda p: np.hypot(p[:, 1] - ny, p[:, 2] - nz) <= NOSE_R + 0.05
        g_nose, _ = gap(prop, plate, keep=near)
        worst = max(ov.values())
        print(f" {th:.0f} deg, foot in the notch at y {fy:.1f}")
        check(worst < 0.05, "no overlap: " + ", ".join(f"{k} {v:.3f}" for k, v in ov.items()) + " mm3")
        check(g_pb >= GAP_MIN, f"plate to base: open gap {g_pb:.2f} (tongue in its groove)")
        check(g_fb >= GAP_MIN, f"prop to base: open gap {g_fb:.2f} (foot in its notch)")
        check(g_pp >= GAP_MIN, f"prop to plate away from the nose: open gap {g_pp:.2f}"
              + (f" (nearest at y {where[1]:.1f} z {where[2]:.1f})" if where is not None else ""))
        check(g_nose < 0.05, f"the nose bears in the pocket's top corner (gap {g_nose:.3f})")
    print("== the plate turning in its groove, with the prop out")
    clear = [(th, overlap(P["plate"].copy().apply_transform(plate_T(th)), base)) for th in range(20, 91, 2)]
    hit = [th for th, v in clear if v >= 0.01]
    check(all(v < 0.01 for th, v in clear if th >= min(ANGLES) - 1),
          f"turns freely from {min(ANGLES) - 1:.0f} to 90 deg; with the prop out it falls back to "
          f"{(max(hit) if hit else 20)} deg before it meets the base")
    print("\nV3 CHECK " + ("FAILED: " + "; ".join(_fail) if _fail else "OK"))
    sys.exit(1 if _fail else 0)


if __name__ == "__main__":
    main()
