#!/usr/bin/env python3
"""The clickers' fits (2026-10-29), measured on the exported prints:

- the upper print's spigot sits in the lower print's lip, overlapping nowhere
- the cap, at rest and at 1, 2, 3 and 4 mm of travel, touches neither print
- the cap never meets the switch housing, a 15.6 mm square 6.6 tall on the
  plate, with a 3.2 mm opening where the socket post rides down into it
- the switch fits below the plate: its body (13.9 square, 5.0 down), its clips
  (15.4 square, the plate's 1.5) and its pins (6.5 round, 3.3 below the body)
  meet nothing in the lower print
- the plate is there: solid just outside the 14 mm cutout, open just inside
- the socket is open where the stem goes and closed above it
- the tin's lid screws on (2026-10-30): pulled straight up it hits the tin's
  thread, so it can't lift off; turned back along the thread it touches nothing

    python3 check_clickers.py            both
    python3 check_clickers.py tin|jar

Overlaps are mm3. Heights mirror clicker_lib.scad and the two .scad files.
"""
import sys
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from part_mesh import load  # noqa: E402

TRAVEL = 4.0
fails = []


def box(x0, y0, z0, x1, y1, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl(r, z0, z1):
    return mf.Manifold.cylinder(z1 - z0, r, r, 96).translate([0, 0, z0])


def overlap(a, b):
    return (a ^ b).volume()


def report(name, v, limit=0.01):
    ok = v <= limit
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {v:.3f} mm3")
    if not ok:
        fails.append(name)


def contains(mesh, pt):
    return bool(trimesh.load(mesh, force="mesh").contains([pt])[0])


def point(name, mesh, pt, want):
    got = contains(mesh, pt)
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {'solid' if got else 'open'} at {pt}")
    if not ok:
        fails.append(name)


def check(d, lower, upper, cap, S, CZ):
    P = S + 1.5
    print(f"== {d}  (S {S}, plate top {P}, cap at {CZ})")
    lo = load(str(HERE / d / "parts" / f"{lower}.stl"))
    up = load(str(HERE / d / "parts" / f"{upper}.stl")).translate([0, 0, S])
    cp = load(str(HERE / d / "parts" / f"{cap}.stl"))
    report("spigot in lip", overlap(lo, up))
    housing = box(-7.8, -7.8, P, 7.8, 7.8, P + 6.6) - cyl(3.2, P - 1, P + 7)
    for t in [0, 1, 2, 3, TRAVEL]:
        c = cp.translate([0, 0, CZ - t])
        report(f"cap at {t} mm vs upper", overlap(c, up))
        report(f"cap at {t} mm vs lower", overlap(c, lo))
        report(f"cap at {t} mm vs housing", overlap(c, housing))
    switch = (box(-6.95, -6.95, S - 5.0, 6.95, 6.95, S) + box(-7.7, -7.7, S - 1.5, 7.7, 7.7, S)
              + cyl(6.5, S - 8.3, S - 5.0))
    report("switch below the plate vs lower", overlap(switch, lo))
    um = HERE / d / "parts" / f"{upper}.stl"
    point("plate outside the cutout", um, [7.4, 0.0, 0.75], True)
    point("cutout open", um, [6.6, 0.0, 0.75], False)
    cm = HERE / d / "parts" / f"{cap}.stl"
    point("socket open (arm)", cm, [1.8, 0.0, 1.5], False)
    point("socket open (centre, top)", cm, [0.0, 0.0, 3.3], False)
    point("socket open under the gable ridge", cm, [0.0, 0.0, 3.9], False)
    point("gable closed near the slot's edge", cm, [1.5, 0.6, 3.6], True)
    point("post wall beside the socket", cm, [2.5, 0.0, 1.5], True)


which = sys.argv[1] if len(sys.argv) > 1 else "all"
if which in ("all", "tin"):
    S = 1.6 + 5.0 + 3.3 + 0.6
    check("gingerbread_tin", "tin_print", "lid_print", "cookie_print", S, S + 1.5 + 6.8)
    # the screw lid, against gingerbread_tin_clicker.scad's TH_P (right hand: the
    # lid rises TH_P a turn as it turns anticlockwise, seen from above)
    TH_P = 2.7
    lo = load(str(HERE / "gingerbread_tin" / "parts" / "tin_print.stl"))
    up = load(str(HERE / "gingerbread_tin" / "parts" / "lid_print.stl")).translate([0, 0, S])
    for dz in (0.5, 1.0):
        v = overlap(lo, up.translate([0, 0, dz]))
        ok = v > 1.0
        print(f"  {'ok  ' if ok else 'FAIL'}  lid pulled {dz} mm straight up hits the thread: {v:.1f} mm3")
        if not ok:
            fails.append(f"lid lifts {dz} mm without the thread holding it")
    for a in (30, 90, 180, 360, 540):
        report(f"lid unscrewed {a} deg along the thread", overlap(lo, up.rotate([0, 0, a]).translate([0, 0, a / 360 * TH_P])))
    # and the control: turned the other way while rising, it does collide, so the
    # zeros above are the thread's path, not a lid that clears the tin anyway
    v = overlap(lo, up.rotate([0, 0, -30]).translate([0, 0, 30 / 360 * TH_P]))
    print(f"  {'ok  ' if v > 1.0 else 'FAIL'}  lid turned 30 deg the wrong way while rising collides: {v:.1f} mm3")
    if v <= 1.0:
        fails.append("the unscrew check would pass without a thread")
if which in ("all", "jar"):
    S = 30.0
    check("cookie_jar", "jar_print", "top_print", "gb_print", S, S + 1.5 + 6.8)
print("FITS OK" if not fails else f"FITS FAILED: {', '.join(fails)}")
sys.exit(1 if fails else 0)
