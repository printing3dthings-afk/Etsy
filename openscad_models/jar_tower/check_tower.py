#!/usr/bin/env python3
"""The Stacking Jar Tower's joints, checked on the exported parts (2026-11-13), the same
four checks the thread test print passed (check_thread_coupon.py), at 0.2 clearance:

  jar on jar   a jar's spigot screwed into the mouth at another jar's top
  jar on foot  the bottom jar into the foot
  cap on jar   the cap into the top jar

- seated: 0.05 mm short of home nothing touches; 0.1 past, the cones overlap;
- held: pulled straight up 1.0 mm (a quarter tooth), the teeth hit;
- open gap at the teeth when home;
- unscrews: turned back 90 to 720 deg along the thread, it touches nothing.

    python3 check_tower.py      (writes checks/fit_tower.txt)
"""
import math
import re
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
V = {k: float(v) for k, v in re.findall(r"\b(\w+) = ([0-9.]+);", (HERE / "jar_tower_coupon.scad").read_text())}
T = {k: float(v) for k, v in re.findall(r"\b(\w+) = ([0-9.]+);", (HERE / "jar_tower.scad").read_text())}
P, TA = V["TH_P"], math.tan(math.radians(V["TH_A"]))
CL = T["CL"]
out, fails = [], []


def check(ok, msg):
    out.append(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def joint(name, upper, lower, rim):
    """upper's spigot (its base at z=0) into lower's mouth, whose rim is at z=rim."""
    cs_depth = (V["R_OUT"] - V["CS"] - (V["TH_R"] + CL)) / TA
    mz = rim - V["H_MOUTH"]
    z0 = mz + V["H_MOUTH"] - cs_depth - V["TH_H"] - P
    zs = mz + V["H_MOUTH"] - cs_depth - CL / TA - V["TH_H"]
    lm = man(lower)

    def at(z, turn=None):
        t = trimesh.transformations.rotation_matrix(math.radians(360 * (z - z0) / P if turn is None else turn), [0, 0, 1])
        t[2, 3] = z
        return upper.copy().apply_transform(t)
    out.append(f"== {name}")
    short = (man(at(zs + 0.05)) ^ lm).volume()
    past = (man(at(zs - 0.1)) ^ lm).volume()
    check(short < 0.05 and past > 5, f"seated: 0.05 short {short:.2f} mm3, 0.1 past {past:.1f} mm3")
    up = (man(at(zs + 1.0, 360 * (zs - z0) / P)) ^ lm).volume()
    check(up > 1, f"held: pulled straight up 1.0 the teeth hit ({up:.1f} mm3)")
    s = at(zs)
    pts = s.sample(30000, seed=2)
    r = np.hypot(pts[:, 0], pts[:, 1])
    teeth = pts[(r > V["TH_R"] - V["TH_D"] - 0.05) & (r < V["TH_R"] + 0.05) & (pts[:, 2] < zs + V["TH_H"] - 2.0) & (pts[:, 2] > zs + 1.8)]
    d = -trimesh.proximity.ProximityQuery(lower).signed_distance(teeth)
    check(d.min() > 0, f"open gap at the teeth: least {d.min():.2f} mm")
    free = [k * 90 for k in range(1, 9) if (man(at(zs + k * P / 4)) ^ lm).volume() > 0.5]
    check(not free, "unscrews: turned back 90..720 deg it touches nothing" + (f" (touches at {free})" if free else ""))


def main():
    jar = trimesh.load(HERE / "parts" / "tower_jar.stl")
    foot = trimesh.load(HERE / "parts" / "tower_foot.stl")
    cap = trimesh.load(HERE / "parts" / "tower_cap_up.stl")
    out.append(f"STACKING JAR TOWER: JOINTS (exported parts, {CL} clearance)")
    joint("jar on jar", jar, jar, T["H_JAR"])
    joint("jar on foot", jar, foot, T["FOOT_FLOOR"] + V["H_MOUTH"])
    joint("cap on jar", cap, jar, T["H_JAR"])
    out.append("PASS" if not fails else "FAIL: " + "; ".join(fails))
    text = "\n".join(out)
    print(text)
    (HERE / "checks" / "fit_tower.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
