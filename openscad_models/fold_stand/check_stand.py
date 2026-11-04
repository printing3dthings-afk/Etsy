#!/usr/bin/env python3
"""Fold Stand's hinge and stance (2026-11-04), on the exported parts:

- every print sits on the bed as exported
- at every stop (folded, and the five openings) nothing touches: the back
  plate's ridges sit in the pins' notches; half way between two stops the
  ridges ride up on the pins: the click
- the plates never meet anywhere from folded to fully open, in 1 deg steps
- a pin turned 4 deg in the front plate's barrel hits it: the teardrop keys it
- stance: at each opening it stands on its two feet on a table with a 200 g
  phone on the lip; the phone's lean, and the least friction under the feet
  that holds the A up with a free hinge (the clicks are extra)

    python3 check_stand.py
"""
import math
import re
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from part_mesh import load, to_trimesh  # noqa: E402

LOG = (HERE / "logs" / "front.log").read_text()
V = {k: float(v) for k, v in re.findall(r'"(\w+)", ([0-9.]+)', LOG)}
SCAD = (HERE / "fold_stand.scad").read_text()
STOPS = [float(a) for a in re.search(r"STOPS = \[([0-9, ]+)\]", SCAD).group(1).split(",")]
AF = V["AF"]
PLA = 1.24e-3           # g per mm3, solid (printed with infill it is lighter)
PHONE_G, PHONE_L, PHONE_T = 200.0, 150.0, 9.0
fails = []


def part(name):
    return load(str(HERE / "parts" / f"{name}.stl"))


def ov(a, b):
    return (a ^ b).volume()


def say(ok, text, fail=None):
    print(f"  {'ok  ' if ok else 'FAIL'}  {text}")
    if not ok:
        fails.append(fail or text)


def about_axis(m, deg):
    """turn a manifold about the hinge axis (x, through (0, AF))"""
    return m.translate([0, 0, -AF]).rotate([deg, 0, 0]).translate([0, 0, AF])


print("== on the bed")
for p in ("front", "back", "pin"):
    z = part(p).bounding_box()[2]
    say(abs(z) < 0.01, f"{p}: lowest point z {z:+.3f}", f"{p} off the bed")

front, back0, pins = part("front_use"), part("back_use0"), part("pins_use")
print("== the clicks")
for a in STOPS:
    b = about_axis(back0, a)
    v = ov(b, pins) + ov(b, front)
    say(v <= 0.05, f"open {a:4.0f} deg: the ridges sit in their notches, nothing touches ({v:.3f} mm3)")
for a0, a1 in zip(STOPS, STOPS[1:]):
    m = (a0 + a1) / 2
    v = ov(about_axis(back0, m), pins)
    say(v >= 0.05, f"open {m:4.1f} deg, between stops: the ridges ride up on the pins ({v:.2f} mm3)")
worst = max(ov(about_axis(back0, a), front) for a in np.arange(0, STOPS[-1] + 0.5, 1.0))
say(worst <= 0.05, f"the plates never meet from 0 to {STOPS[-1]:.0f} deg (worst {worst:.3f} mm3)")
say(ov(about_axis(pins, 4), front) >= 0.05, "a pin turned 4 deg hits the front plate's barrel: keyed")
say(ov(pins, front) <= 0.05, f"the pins in the front plate's barrels: {ov(pins, front):.3f} mm3")

print("== stance, with a 200 g phone on the lip")
from scipy.spatial import ConvexHull  # noqa: E402
F = to_trimesh(front)
B0 = to_trimesh(back0)
mF, mB = F.volume * PLA, B0.volume * PLA
axis = np.array([0.0, AF])
# the phone: its foot in the lip's corner on the front plate's outer face (z = T = 4
# in its frame), its back resting on the hinge barrel, which stands proud of the plate,
# so it stands a few degrees steeper than the plate; its centre half its length up from
# the lip and half its thickness out from its back
lip = np.array([-V["LF"] + 8.0, 4.0])
to_c = np.array([0.0, AF]) - lip
tilt = math.atan2(to_c[1], to_c[0]) + math.asin(V["RK"] / np.linalg.norm(to_c))
d_ph = np.array([math.cos(tilt), math.sin(tilt)])
n_ph = np.array([-math.sin(tilt), math.cos(tilt)])
phone_c = lip + d_ph * PHONE_L / 2 + n_ph * PHONE_T / 2
for a in STOPS[1:]:
    B = B0.copy()
    B.apply_transform(trimesh.transformations.rotation_matrix(math.radians(a), [1, 0, 0], [0, 0, AF]))
    pf, pb = F.vertices[:, 1:], B.vertices[:, 1:]
    pts = np.vstack([pf, pb])
    hull = ConvexHull(pts)
    # the table: the hull's edge from a front-plate point to a back-plate one that lies
    # farthest from the hinge (the edges near the barrels join the plates too)
    best = None
    for (i, j), eq in zip(hull.simplices, hull.equations):
        if (i < len(pf)) == (j < len(pf)):
            continue
        n, d = eq[:2], eq[2]
        dist = -(n @ axis + d)          # inside the hull: n.x + d <= 0
        if best is None or dist > best[0]:
            best = (dist, n, pts[i] if i < len(pf) else pts[j], pts[j] if i < len(pf) else pts[i])
    _, n, foot_f, foot_b = best
    # turn the (y, z) plane so the outward normal points down: the table at height 0
    ang = math.atan2(n[1], n[0]) - (-math.pi / 2)
    c, s_ = math.cos(-ang), math.sin(-ang)
    R2 = np.array([[c, -s_], [s_, c]])
    def P(yz):
        return R2 @ (np.asarray(yz) - foot_f)
    fF, fB, apex = P(foot_f), P(foot_b), P(axis)
    d_p = R2 @ d_ph                                 # the phone's own direction
    lean = math.degrees(math.atan2(abs(d_p[1]), abs(d_p[0])))
    gF, gB, gP = P(F.center_mass[1:]), P(B.center_mass[1:]), P(phone_c)
    WP = PHONE_G
    WF = mF + WP                                    # the phone rides on the front plate
    cF = (gF * mF + gP * WP) / WF
    # a three-hinged arch on the table: feet (Hf, Vf) and (Hb, Vb), Hf = -Hb
    Vb = (WF * (cF[0] - fF[0]) + mB * (gB[0] - fF[0])) / (fB[0] - fF[0])
    Vf = WF + mB - Vb
    # the back plate, moments about the apex: its foot's reactions and its weight
    rb, rg = fB - apex, gB - apex
    Hb = (rb[0] * Vb - rg[0] * mB) / rb[1]
    mu = abs(Hb) / min(Vf, Vb)
    over = gP[0] if fF[0] < fB[0] else -gP[0]
    stands = Vf > 0 and Vb > 0
    say(stands, f"open {a:4.0f} deg: the phone leans at {lean:4.1f} deg to the table; feet {abs(fB[0] - fF[0]):3.0f} mm "
                f"apart; on a free hinge it stands where the feet grip at mu {mu:.2f} or more")
print("FIT CHECK OK" if not fails else "FIT CHECK FAILED: " + "; ".join(fails))
sys.exit(1 if fails else 0)
