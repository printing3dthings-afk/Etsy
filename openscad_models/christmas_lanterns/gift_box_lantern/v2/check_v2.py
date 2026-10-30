#!/usr/bin/env python3
"""Gift box lantern v2's fits (2026-10-30), on the exported prints in place:

- every print sits on the bed as exported
- the four panels stand in the frame's grooves touching nothing; pushed 0.5
  out or in they hit the groove, so the frame holds them
- the top sits on the posts touching nothing, its sockets round the snap pins;
  0.1 lower it would be into the posts, so it rests on them; pulled 0.5 up the
  pins' barbs catch, so it is held; and it holds each panel down
- the lid sits on the top, the ribbon on the lid, the bow on the ribbon round
  the lid's pin, touching nothing; the bow pulled 0.5 up is caught by the pin

    python3 check_v2.py
"""
import sys
from pathlib import Path

import manifold3d as mf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "tools"))
from part_mesh import load  # noqa: E402

fails = []


def part(name):
    return load(str(HERE / "parts" / f"{name}.stl"))


def ov(a, b):
    return (a ^ b).volume()


def none(name, v):
    ok = v <= 0.05
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {v:.3f} mm3")
    if not ok:
        fails.append(name)


def hits(name, v, need=0.5):
    ok = v >= need
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {v:.2f} mm3")
    if not ok:
        fails.append(name)


print("== on the bed")
for p in ["frame", "top", "lid", "ribbon", "bow"] + [f"panel_{k}" for k in range(4)]:
    z = part(p).bounding_box()[2]
    ok = abs(z) < 0.01
    print(f"  {'ok  ' if ok else 'FAIL'}  {p}: lowest point z {z:+.3f}")
    if not ok:
        fails.append(f"{p} off the bed")

frame, top, lid = part("frame"), part("top_use"), part("lid_use")
ribbon, bow = part("ribbon_use"), part("bow_use")
panels = [part(f"panel_{k}_use") for k in range(4)]
# a panel's outward direction: face k is at 90 k deg
OUT = [(1, 0), (0, 1), (-1, 0), (0, -1)]

print("== the glass in the frame")
for k, pn in enumerate(panels):
    none(f"panel {k} in its grooves", ov(frame, pn))
    ox, oy = OUT[k]
    hits(f"panel {k} pushed 0.5 out hits the groove", ov(frame, pn.translate([0.5 * ox, 0.5 * oy, 0])))
    hits(f"panel {k} pushed 0.5 in hits the groove", ov(frame, pn.translate([-0.5 * ox, -0.5 * oy, 0])))
    none(f"panel {k} under the top", ov(top, pn))
    hits(f"panel {k} lifted 0.5 hits the top", ov(top, pn.translate([0, 0, 0.5])))

print("== the top on the posts")
none("top at rest", ov(frame, top))
hits("top 0.1 lower is into the posts", ov(frame, top.translate([0, 0, -0.1])))
# a barb is a thin ring, so any collision at all is the catch; at 1.0 it is
# well into the throat
for dz in (0.5, 1.0):
    hits(f"top pulled {dz} up: the barbs catch", ov(frame, top.translate([0, 0, dz])), 0.05)

print("== the lid, the ribbon and the bow")
none("lid on the top", ov(top, lid))
none("ribbon on the lid", ov(lid, ribbon))
none("ribbon clear of the top", ov(top, ribbon))
none("bow on the ribbon and the pin", ov(lid, bow) + ov(ribbon, bow))
for dz in (0.5, 1.0):
    hits(f"bow pulled {dz} up: the barb catches", ov(lid, bow.translate([0, 0, dz])), 0.05)
hits("ribbon lifted 0.5: the bow holds it", ov(bow, ribbon.translate([0, 0, 0.5])))

print("FIT CHECK OK" if not fails else "FIT CHECK FAILED: " + "; ".join(fails))
sys.exit(1 if fails else 0)
