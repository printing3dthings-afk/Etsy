#!/usr/bin/env python3
"""The whole Snowflake Screen, on the exported print (parts/snowflake_screen_screen.stl:
three panels, printed flat, hinge axes along y at x = 45 and 90, z = 2.8):

  rest     the three panels don't touch
  swing    each outer panel's free turn about its hinge, each way, against the
           middle panel (>= 90 deg each way)
  pins     a 1.9 mm pin (1.75 filament, 0.15 over) down each hinge clears every panel
  stands   at the display pose (both wings turned back FOLD deg) nothing touches,
           and the centre of mass sits inside the footprint, with margin

    python3 check_screen.py     (writes checks/fit_screen.txt)
"""
import sys
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh
from shapely.geometry import MultiPoint, Point

HERE = Path(__file__).resolve().parent
AXIS_Z, W, H, FLOOR, FOLD = 2.8, 45.0, 90.0, 1.2, 40


def M(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def hit(a, b):
    return (a ^ b).volume() > 1e-4


def turn(m, hx, deg):
    return m.translate([-hx, 0, -AXIS_Z]).rotate([0, deg, 0]).translate([hx, 0, AXIS_Z])


def main():
    bodies = sorted(trimesh.load(HERE / "parts" / "snowflake_screen_screen.stl").split(only_watertight=False),
                    key=lambda b: b.centroid[0])
    P = [M(b) for b in bodies]
    rows, ok = [], True

    rest = not any(hit(P[i], P[j]) for i, j in ((0, 1), (1, 2), (0, 2)))
    rows.append(f"rest: panels clear of each other {rest}")
    ok &= rest

    for k, hx in ((0, W), (2, 2 * W)):
        free = [next((a for a in range(1, 181) if hit(P[1], turn(P[k], hx, s * a))), 181) - 1 for s in (1, -1)]
        good = min(free) >= 90
        ok &= good
        rows.append(f"swing: panel {k} about x = {hx:.0f} turns {free[0]} deg one way, {free[1]} the other "
                    f"{'ok' if good else 'FAIL'}")

    for hx in (W, 2 * W):
        pin = mf.Manifold.cylinder(H + 1 - FLOOR, 0.95, 0.95, 48).rotate([-90, 0, 0]).translate([hx, FLOOR + 0.05, AXIS_Z])
        clear = not any(hit(p, pin) for p in P)
        ok &= clear
        rows.append(f"pins: a 1.9 pin down x = {hx:.0f} clears every panel {clear}")

    # the display pose, wings back: the same turns as posed() in the .scad
    pose = [turn(P[0], W, -FOLD), P[1], turn(P[2], 2 * W, FOLD)]
    clear = not any(hit(pose[i], pose[j]) for i, j in ((0, 1), (1, 2), (0, 2)))
    mesh = trimesh.util.concatenate([trimesh.Trimesh(*(lambda g: (g.vert_properties[:, :3], g.tri_verts))(p.to_mesh()))
                                     for p in pose])
    # standing, printed y is up: the footprint is the panels' bottom edges in x-z
    v = mesh.vertices
    foot = MultiPoint([(x, z) for x, y, z in v[v[:, 1] < 0.3]]).convex_hull
    com = mesh.center_mass
    margin = foot.exterior.distance(Point(com[0], com[2])) if foot.contains(Point(com[0], com[2])) else -1
    good = clear and margin >= 5
    ok &= good
    rows.append(f"stands: at {FOLD} deg the panels are clear {clear}; centre of mass {margin:.1f} mm inside "
                f"the footprint {'ok' if good else 'FAIL'}")

    text = "\n".join(["SNOWFLAKE SCREEN FIT CHECK (exported print)"] + rows + ["PASS" if ok else "FAIL"])
    print(text)
    (HERE / "checks" / "fit_screen.txt").write_text(text + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
