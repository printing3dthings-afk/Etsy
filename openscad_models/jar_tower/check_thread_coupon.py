#!/usr/bin/env python3
"""Stacking Jar Tower thread test print, checked on the exported parts (2026-11-10).

For each mouth (0.2, 0.3, 0.4 radial clearance), with the spigot screwed home:
- seated: the cones meet (the seat), and nothing else touches;
- the open gap at the thread's flanks and crests, against the 0.3 that stays open;
- pulled straight up 1.0 mm (a quarter of a tooth) the teeth hit: it is held by the thread;
- turned back along the thread a quarter turn at a time it touches nothing: it unscrews.

    python3 check_thread_coupon.py
"""
import math
import re
import sys
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
SCAD = (HERE / "jar_tower_coupon.scad").read_text()
V = {k: float(v) for k, v in re.findall(r"\b(\w+) = ([0-9.]+);", SCAD)}
P, TA = V["TH_P"], math.tan(math.radians(V["TH_A"]))
_fail = []


def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        _fail.append(msg)


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def placed(sp, z, turn):
    t = trimesh.transformations.rotation_matrix(math.radians(turn), [0, 0, 1])
    t[2, 3] = z
    return man(sp.copy().apply_transform(t))


def main():
    sp = trimesh.load(HERE / "parts" / "spigot.stl")
    for C in (0.2, 0.3, 0.4):
        mo = trimesh.load(HERE / "parts" / f"mouth_{C}.stl")
        mm = man(mo)
        cs_depth = (V["R_OUT"] - V["CS"] - (V["TH_R"] + C)) / TA
        z0 = V["H_MOUTH"] - cs_depth - V["TH_H"] - P
        zs = V["H_MOUTH"] - cs_depth - C / TA - V["TH_H"]
        turn = lambda z: 360 * (z - z0) / P
        print(f"== mouth with {C} clearance")
        # the cones touch by design: 0.05 short of home nothing touches, and pressed
        # 0.1 further they overlap (the faceted cones meet within ~0.005)
        short = (placed(sp, zs + 0.05, turn(zs + 0.05)) ^ mm).volume()
        past = (placed(sp, zs - 0.1, turn(zs - 0.1)) ^ mm).volume()
        check(short < 0.05 and past > 5, f"screwed home, the cones seat: 0.05 short {short:.2f} mm3, 0.1 past {past:.1f} mm3")
        # the spigot 1.0 up along the axis without turning (a quarter of a tooth) hits the teeth
        up = (placed(sp, zs + 1.0, turn(zs)) ^ mm).volume()
        check(up > 1, f"pulled straight up 1.0: the teeth hit ({up:.1f} mm3), so it is held by the thread; "
              f"axial play {C / TA:.2f}")
        # least gap at the teeth, measured from the spigot's tooth surface
        s = sp.copy()
        t = trimesh.transformations.rotation_matrix(math.radians(turn(zs)), [0, 0, 1]); t[2, 3] = zs
        s.apply_transform(t)
        pts = s.sample(30000, seed=2)
        r = np.hypot(pts[:, 0], pts[:, 1])
        teeth = pts[(r > V["TH_R"] - V["TH_D"] - 0.05) & (pts[:, 2] < zs + V["TH_H"] - 2.0) & (pts[:, 2] > zs + 1.8)]
        d = -trimesh.proximity.ProximityQuery(mo).signed_distance(teeth)
        check(d.min() > 0, f"open gap at the teeth: least {d.min():.2f} (flanks C cos 35 = {C * math.cos(math.radians(35)):.2f})"
              + ("" if C >= 0.3 else " -- under the 0.3 rule: this is the tight variant"))
        free = [k * 90 for k in range(1, 9) if (placed(sp, zs + k * P / 4, turn(zs + k * P / 4)) ^ mm).volume() > 0.5]
        check(not free, "unscrews: turned back 90..720 deg along the thread it touches nothing"
              + (f" (touches at {free})" if free else ""))
    print("\nJAR THREAD COUPON " + ("FAILED: " + "; ".join(_fail) if _fail else "OK"))
    sys.exit(1 if _fail else 0)


if __name__ == "__main__":
    main()
