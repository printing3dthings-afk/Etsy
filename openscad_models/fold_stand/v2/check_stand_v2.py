#!/usr/bin/env python3
"""Fold Stand v2's ratchet hinge and stance (2026-11-06), on the exported parts:

- every print sits on the bed as exported
- the ratchet, measured on the pin's real sections under the blade's ridge: how
  far the ridge must lift off the pin at each angle (the blade's bend)
  - at every stop it seats (only its 0.1 preload);
  - folding toward upright it rides up a ramp and drops into the next notch:
    the click;
  - opening it meets a radial face it can't ride up: the lock;
  - with the buttons pressed the lift is the same at every angle: it turns
    free, and the ridge sits on the release cone's slope, so it springs back;
  - pulled outward, the pin's wall makes the ridge lift: it stays in
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
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from part_mesh import load, to_trimesh  # noqa: E402

LOG = (HERE / "logs" / "front.log").read_text()
V = {k: float(v) for k, v in re.findall(r'"(\w+)", ([0-9.]+)', LOG)}
SCAD = (HERE / "fold_stand_v2.scad").read_text()
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
pressed = part("pins_pressed")
from shapely.geometry import Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from shapely import affinity  # noqa: E402

PR, CLR_RUN = 4.0, 0.15
RB = PR + CLR_RUN
num = lambda k: float(re.search(rf"\b{k} = ([0-9.]+);", SCAD).group(1))
R_FREE, RIDGE_L = num("R_FREE"), num("RIDGE_L")
RX0, REST = V["RX0"], V["REST"]
lo = (RB - R_FREE) / math.tan(math.radians(37))
# the ridge in the back plate's own (y, z) about the axis, pointing along +y at angle 0
RIDGE = Polygon([(RB + 0.5, -lo - 0.3), (RB, -lo), (R_FREE, 0), (RB + 0.5, 0)])
TM_PINS, TM_PRESSED = to_trimesh(pins), to_trimesh(pressed)


def pin_sections(tm, shift=0.0):
    """the left pin's sections, about the axis, under the ridge, with the pin moved out by
    shift: the left pin goes out toward -x, so the ridge then sits over its point x + shift"""
    out = []
    for x in np.linspace(RX0 + 0.05, RX0 + RIDGE_L - 0.05, 7):
        sec = tm.section(plane_origin=[x + shift, 0, 0], plane_normal=[1, 0, 0])
        polys = [Polygon(l[:, 1:] - [0, AF]) for l in sec.discrete if len(l) > 3]
        out.append(unary_union([q.buffer(0) for q in polys if q.centroid.x ** 2 + q.centroid.y ** 2 < 100]))
    return out


def lift(secs, a):
    """how far the ridge must move out along its own axis to clear the pin at opening a"""
    r = affinity.rotate(RIDGE, a, origin=(0, 0))
    d = (math.cos(math.radians(a)), math.sin(math.radians(a)))
    lo_, hi = 0.0, 2.5
    if all(r.intersection(s).area < 1e-5 for s in secs):
        return 0.0
    for _ in range(30):
        mid = (lo_ + hi) / 2
        rr = affinity.translate(r, d[0] * mid, d[1] * mid)
        if any(rr.intersection(s).area >= 1e-5 for s in secs):
            lo_ = mid
        else:
            hi = mid
    return hi


print("== the ratchet (the ridge's lift off the pin, mm; the blade bends this far)")
rest = pin_sections(TM_PINS)
CR = num("CREST")
full = CR - R_FREE                      # riding on a crest
for a in STOPS:
    L = lift(rest, a)
    say(L <= 0.12, f"at {a:4.0f} deg it seats: lift {L:.2f} (the preload is {num('ROOT') - R_FREE:.2f})")
    up, dn = lift(rest, a + 0.75), lift(rest, a - 0.75)
    say(up >= 0.85 * full, f"  opening from {a:.0f}: within 0.75 deg it needs {up:.2f}, the full face: LOCKED")
    say(dn <= L + 0.25, f"  folding from {a:.0f}: 0.75 deg on it needs only {dn:.2f}, up the ramp")
for a0, a1 in zip(STOPS, STOPS[1:]):
    pk = max(lift(rest, a) for a in np.arange(a0 + 1, a1, 0.5))
    say(0.4 <= pk <= full + 0.05, f"folding {a1:.0f} -> {a0:.0f}: rides over at {pk:.2f}, then drops in: the click")
prs = pin_sections(TM_PRESSED)
ls = [lift(prs, a) for a in np.arange(0, STOPS[-1] + 0.1, 1.0)]
say(max(ls) - min(ls) <= 0.03 and min(ls) > full,
    f"buttons pressed: lift {min(ls):.2f}-{max(ls):.2f} at every angle, above the crests ({full:.2f}): turns FREE")
back_out = pin_sections(TM_PRESSED, 0.2)
L2 = lift(back_out, 30)
say(L2 < ls[30] - 0.05, f"  0.2 mm back out from pressed the lift falls {ls[30]:.2f} -> {L2:.2f}: the blade pushes it back")
pull = max(lift(pin_sections(TM_PINS, d), a) for d in (1.0, 1.5, 2.0) for a in (30, 45))
say(pull >= PR - R_FREE - 0.1, f"pulled 1-2 mm outward the ridge must lift {pull:.2f} up the wall: the pin stays in")
worst = max(ov(about_axis(back0, a), front) for a in np.arange(0, STOPS[-1] + 0.5, 1.0))
say(worst <= 0.05, f"the plates never meet from 0 to {STOPS[-1]:.0f} deg (worst {worst:.3f} mm3)")
say(ov(about_axis(pins, 4), front) >= 0.05, "a pin turned 4 deg hits the front plate's barrel: keyed")
say(ov(pins, front) <= 0.05, f"the pins at rest in the front plate's barrels: {ov(pins, front):.3f} mm3")
say(ov(pressed, front) <= 0.05, f"pressed, the heads stop on the barrels' ends: {ov(pressed, front):.3f} mm3")
nb = len(pressed.decompose())
say(nb == 2, f"pressed, the two pins don't meet in the middle ({nb} bodies)")

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
