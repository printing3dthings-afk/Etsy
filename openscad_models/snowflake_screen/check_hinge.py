#!/usr/bin/env python3
"""Fit check for the Snowflake Screen's hinge, on the exported coupon leaves
(parts/coupon_l_<bore>.stl, coupon_r_<bore>.stl; the hinge axis runs along y at
x = 0, z = 2.8, the leaves printed flat):

  rest    the leaves don't touch, and the smallest gap between them
  swing   how far the right leaf turns each way about the axis before it touches
          the left (>= 90 deg each way: standing, the screen's wings sit at 30-60)
  pin     a 1.75 mm filament pin, 0.15 oversize for a filament's tolerance and
          the hole printing small, on the axis from the hole's floor to the top,
          clears both leaves
  floor   the hole is closed at the bottom: the pin can't drop out

    python3 check_hinge.py      (writes checks/fit_hinge.txt)
"""
import sys
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
BORES = ["2.0", "2.3"]
AXIS_Z, H, FLOOR = 2.8, 30.0, 1.2
PIN_D = 1.75 + 0.15


def M(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def hit(a, b):
    return (a ^ b).volume() > 1e-4


def turn(m, deg):
    # about the axis (along y, at x = 0, z = AXIS_Z)
    return m.translate([0, 0, -AXIS_Z]).rotate([0, deg, 0]).translate([0, 0, AXIS_Z])


def pin(y0, y1, d):
    c = mf.Manifold.cylinder(y1 - y0, d / 2, d / 2, 48)
    return c.rotate([-90, 0, 0]).translate([0, y0, AXIS_Z])


def main():
    rows, ok = [], True
    for b in BORES:
        lt, rt = (trimesh.load(HERE / "parts" / f"coupon_{s}_{b}.stl") for s in ("l", "r"))
        L, R = M(lt), M(rt)
        rest = not hit(L, R)
        gap = float(np.abs(trimesh.proximity.signed_distance(lt, rt.sample(8000))).min())
        swing = [next((a for a in range(1, 181) if hit(L, turn(R, s * a))), None) for s in (1, -1)]
        p = pin(FLOOR + 0.05, H + 1, PIN_D)
        pin_ok = not hit(L, p) and not hit(R, p)
        floor_ok = hit(L, pin(0.2, FLOOR - 0.2, 1.0)) or hit(R, pin(0.2, FLOOR - 0.2, 1.0))
        free = [(a or 181) - 1 for a in swing]
        good = rest and gap >= 0.45 and min(free) >= 90 and pin_ok and floor_ok
        ok &= good
        rows.append(f"bore {b}: {'ok  ' if good else 'FAIL'}  rest clear {rest}, closest {gap:.2f}; free swing "
                    f"{free[0]} deg one way, {free[1]} the other; pin {PIN_D:.2f} clears {pin_ok}; "
                    f"hole closed at the bottom {floor_ok}")
    text = "\n".join(["SNOWFLAKE SCREEN HINGE FIT CHECK (exported coupon leaves)"] + rows + ["PASS" if ok else "FAIL"])
    print(text)
    (HERE / "checks" / "fit_hinge.txt").write_text(text + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
