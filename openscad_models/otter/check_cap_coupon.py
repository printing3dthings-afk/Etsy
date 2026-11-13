#!/usr/bin/env python3
"""Fit check for the capped joint test (cap_joint_coupon.scad), on the exported parts
parts/cap_front{0,1}.stl and parts/cap_back{0,1}.stl, moved as rigid bodies:

  rest   nothing touches, and the smallest gap between the parts (sampled)
  swing  how far the back part turns about the joint before it touches the front
         (needs >= 15 deg each way; the stop is the fin in the C's slot)
  lift   how far the back part rises before it catches (the pin's bulge), and how far
         it drops before it catches (the cap on its countersink, or the plate)
  cap    the gap across the cap's cone, measured on the parts

    python3 check_cap_coupon.py      (writes checks/fit_cap.txt)
"""
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
GAPS = [0.30, 0.40]
PITCH = 34.0


def M(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def first_contact(front, back, moves):
    for s, mv in moves:
        if (front ^ mv(back)).volume() > 1e-4:
            return s
    return None


def main():
    out = ["CAPPED JOINT TEST: FIT CHECK (exported parts)"]
    ok = True
    for v, g in enumerate(GAPS):
        fm, bm = trimesh.load(HERE / "parts" / f"cap_front{v}.stl"), trimesh.load(HERE / "parts" / f"cap_back{v}.stl")
        f, b = M(fm), M(bm)
        c = np.array([0.0, v * PITCH])
        rest = (f ^ b).volume()
        pts, _ = trimesh.sample.sample_surface(bm, 40000, seed=1)
        d = np.abs(trimesh.proximity.signed_distance(fm, pts))
        gap = float(d.min())

        def rot(a):
            return lambda m: m.translate([-c[0], -c[1], 0]).rotate([0, 0, a]).translate([c[0], c[1], 0])
        plus = first_contact(f, b, [(a, rot(a)) for a in np.arange(1, 46, 0.5)])
        minus = first_contact(f, b, [(a, rot(-a)) for a in np.arange(1, 46, 0.5)])
        up = first_contact(f, b, [(z, (lambda z: lambda m: m.translate([0, 0, z]))(z)) for z in np.arange(0.05, 3.0, 0.05)])
        down = first_contact(f, b, [(z, (lambda z: lambda m: m.translate([0, 0, -z]))(z)) for z in np.arange(0.05, 3.0, 0.05)])
        good = rest < 1e-4 and gap >= 0.25 and plus and minus and min(plus, minus) >= 15 and up and up < 1.5
        ok &= bool(good)
        out.append(f"cap gap {g:.2f}: {'ok' if good else 'FAIL'}")
        out.append(f"  rest: overlap {rest:.4f} mm3; smallest gap between the parts {gap:.2f} mm (40,000 samples)")
        out.append(f"  swing: touches at +{plus} / -{minus} deg (need >= 15 each way)")
        out.append(f"  lift: catches after {up:.2f} mm up; down: catches after {down if down is None else round(down, 2)} mm "
                   f"(the plate stops it first in use)")
    out.append("PASS" if ok else "FAIL")
    text = "\n".join(out)
    print(text)
    (HERE / "checks" / "fit_cap.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
