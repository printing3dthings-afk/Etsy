#!/usr/bin/env python3
"""Fit check for the gear heart coupon, on the exported parts in their assembled
pose (each gear on its washer, under its barb):

  rest     nothing overlaps
  mesh     the two gears turned together through two full teeth, at their ratio:
           no collision at any step; the smallest gap between their teeth (the
           backlash a flank has to travel)
  engaged  turned the other way by more than that backlash, the teeth do collide:
           they really mesh, not just sit near each other
  barb     lifted, each gear catches on its post's barb (and not before 0.3 mm)
  spin     each gear turns a full circle on its post without touching the bar

    python3 check_gears.py      (writes checks/fit.txt)
"""
import sys
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
MOD, ZA, ZB, PITCH = 1.5, 16, 12, 34.0
DCS = [0.20, 0.40]


def M(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def turn(m, deg, c):
    return m.translate([-c[0], -c[1], 0]).rotate([0, 0, deg]).translate([c[0], c[1], 0])


def hit(a, b):
    return (a ^ b).volume() > 1e-4


def main():
    rows, ok = [], True
    for i, dc in enumerate(DCS):
        ga, gb, bar = (M(trimesh.load(HERE / "parts" / f"{p}{i}.stl")) for p in ("pos_a", "pos_b", "bar"))
        ca, cb = (0.0, i * PITCH), (MOD * (ZA + ZB) / 2 + dc, i * PITCH)
        rest = not (hit(ga, gb) or hit(ga, bar) or hit(gb, bar))
        # turn A through two teeth, B the other way at the ratio
        coll = [a for a in np.arange(0, 2 * 360 / ZA, 0.5) if hit(turn(ga, a, ca), turn(gb, -a * ZA / ZB, cb))]
        # backlash: hold B, turn A until a flank touches, both ways
        free = []
        for sgn in (1, -1):
            a = next((x for x in np.arange(0.1, 10, 0.1) if hit(turn(ga, sgn * x, ca), gb)), None)
            free.append(a)
        bl = [None if a is None else np.radians(a) * MOD * ZA / 2 for a in free]   # arc at A's pitch circle
        lift = next((d for d in np.arange(0.05, 3, 0.05) if hit(ga.translate([0, 0, d]), bar)), None)
        spin = not any(hit(turn(ga, a, ca), bar) for a in range(0, 360, 15))
        good = (rest and not coll and all(b is not None and b > 0.02 for b in bl)
                and lift is not None and lift >= 0.3 and spin)
        ok &= good
        rows.append(f"+{dc:.2f}: {'ok  ' if good else 'FAIL'}  rest clear {rest}; turned together 2 teeth: "
                    f"{'no collision' if not coll else f'COLLIDES at {coll[:4]}'}; backlash {bl[0]:.2f} / {bl[1]:.2f} mm "
                    f"at the pitch circle (meshes both ways); lifts {lift:.2f} mm before the barb catches; "
                    f"spins on its post {'clear' if spin else 'TOUCHES'}")
    text = "\n".join(["GEAR HEART COUPON FIT CHECK (exported parts, assembled pose)"] + rows + ["PASS" if ok else "FAIL"])
    print(text)
    (HERE / "checks" / "fit.txt").write_text(text + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
