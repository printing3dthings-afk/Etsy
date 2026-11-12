#!/usr/bin/env python3
"""Iris box (Scott's form A, 2026-11-12): the mechanism budget, before any modelling
(mechanism handbook section 7, steps 1-4).

The mechanism. Six blades on three levels, opposite blades sharing one (blade k on level
k mod 3), so a blade's only same-level neighbour is the one across from it. On two
levels (alternate blades) the same-level blades, 120 deg apart, swept through each
other mid-turn: trimming the blade clear of them left 329 mm2 of it. Each blade turns on a pin fixed in the base
at radius RP. A twist ring above carries six drive pins at radius RD; each sits in a
straight slot in its blade, running out from the pivot. Turning the ring carries the
pin round, and the blade turns to follow it.

The blade's outline is not drawn by hand: it is every point that, in the blade's own
frame, lies (a) in the annulus between the opening and the wall when open and (b) in
its sector of the opening, with an overlap, when closed. Then the script checks:
  - open: no blade inside the opening's radius;
  - closed: the six together cover the opening;
  - all the way between: no blade passes the wall, same-level blades never touch, and
    the slot stays inside the blade with a 1.2 mm wall round it;
plus the joints' clearances against the printer's tolerances (handbook sections 1-2).

    python3 iris_budget.py       (writes checks/budget.txt, blade.json, images/iris_kinematics.png)
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import mechanism_budget as mb  # noqa: E402

# ---- requirement (Benson's brief, Scott's pick) ----
BOX_D, BOX_H = 100.0, 70.0
WALL = 3.0
R_OUT = BOX_D / 2 - WALL - 1.5     # blades stay inside this (1.5 clear of the wall)
N = 6
TWIST = 48.0                       # deg of ring rotation, open to closed. At 60 the blades
                                   # swung too far for any blade point to reach the centre

# ---- the design (tuned by hand against the checks below) ----
RP = 41.0          # base pivot pins' radius
RD = 28.5          # ring drive pins' radius: at 25 they stood inside the opening
PHI_OPEN = -46.0   # ring angle (deg) open; closed = PHI_OPEN + TWIST
R_A = 24.0         # the opening's radius: 48 mm across when open. 60 left ~200 mm2 uncovered
                   # closed at every setting searched; this is the largest that closes
OPEN_A0 = -75.0    # blade 0's share of the annulus when open: SHARE deg from here
CLOSED_C0 = -75.0  # and of the opening when closed (the opposite blade gets the other half)
SHARE = 176.0      # deg: half the circle, less a gap to the opposite blade
LIP = 1.5          # the rim over the opening: the mouth is 2 (R_A - LIP) across
SHARE_GAP = 0.5    # between same-level blades' shares: the smallest open gap plus margin
GAP_MOVE = 0.35    # and between same-level blades while turning
PIN_D = 4.0        # pivot and drive pins
SLOT_W_EXTRA = None  # set from the clearance budget below
EDGE = 1.2         # least material round the slot and pivot hole


def pose(phi_deg, k):
    """Blade k at ring angle phi: (pivot xy, blade angle beta) -- the blade frame's x axis
    points from the pivot to the drive pin."""
    a = math.radians(60 * k)
    px, py = RP * math.cos(a), RP * math.sin(a)
    f = math.radians(60 * k + phi_deg)
    dx, dy = RD * math.cos(f) - px, RD * math.sin(f) - py
    return (px, py), math.atan2(dy, dx), math.hypot(dx, dy)


def to_world(geom, phi, k):
    (px, py), beta, _ = pose(phi, k)
    return affinity.translate(affinity.rotate(geom, beta, origin=(0, 0), use_radians=True), px, py)


def to_blade(geom, phi, k):
    (px, py), beta, _ = pose(phi, k)
    return affinity.rotate(affinity.translate(geom, -px, -py), -beta, origin=(0, 0), use_radians=True)


def disk(r, n=360):
    return Point(0, 0).buffer(r, n // 4)


def sector(a0, a1, r):
    pts = [(0, 0)] + [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
                      for a in np.linspace(a0, a1, 64)]
    return Polygon(pts)


def share(a0, r_out, r_in=0.0):
    """A SHARE deg sector from a0 (the gap to the opposite blade's share is 360 - 2 SHARE)."""
    g, big = SHARE_GAP / 2, 200.0
    def side(ang, sgn):
        a = math.radians(ang)
        n = (-math.sin(a) * sgn, math.cos(a) * sgn)
        d = (math.cos(a), math.sin(a))
        p0 = (n[0] * g, n[1] * g)
        p1 = (p0[0] - d[0] * big, p0[1] - d[1] * big)
        p2 = (p0[0] + d[0] * big, p0[1] + d[1] * big)
        return Polygon([p1, p2, (p2[0] + n[0] * big, p2[1] + n[1] * big), (p1[0] + n[0] * big, p1[1] + n[1] * big)])
    s = sector(a0, a0 + SHARE, r_out + 5).intersection(disk(r_out))
    return s.difference(disk(r_in)) if r_in else s


def synthesize():
    """Blade 0: every point that is in its 120 deg share of the annulus when open AND in its
    120 deg share of the box when closed. Same-level blades (k, k + 2) get disjoint shares
    in both poses; the two levels overlap."""
    phi_c = PHI_OPEN + TWIST
    ann = share(OPEN_A0, R_OUT, R_A + 0.5)
    cl = share(CLOSED_C0, R_OUT)
    b = to_blade(ann, PHI_OPEN, 0).intersection(to_blade(cl, phi_c, 0))
    b = max(getattr(b, "geoms", [b]), key=lambda g: g.area).buffer(0.01).buffer(-0.01)
    # all the way between, too: inside the wall, and clear of the same-level blades
    # (k +/- 2) by the smallest open gap. The two end poses alone left a blade 0.8 mm
    # past the wall mid-turn and same-level blades touching.
    phis = np.linspace(PHI_OPEN, phi_c, 26)
    for phi in phis:
        b = b.intersection(to_blade(disk(R_OUT), phi, 0))
    for _ in range(1):
        cut = []
        for phi in phis:
            for j in (N // 2,):
                cut.append(to_blade(to_world(b, phi, j).buffer(GAP_MOVE), phi, 0))
        b = b.difference(unary_union(cut))
        b = max(getattr(b, "geoms", [b]), key=lambda g: g.area).buffer(0.01).buffer(-0.01)
    # round off every corner sharper than a 1 mm radius: the coupon's first slice dropped
    # the blade's thin tip (0.16 mm at its thinnest)
    b = b.buffer(-1.0, join_style=1).buffer(1.0, join_style=1)
    b = max(getattr(b, "geoms", [b]), key=lambda g: g.area)
    cover = unary_union([to_world(b, phi_c, k).buffer(0) for k in range(N)])
    return disk(R_A - LIP).difference(cover).area, CLOSED_C0, b


def sweep_checks(blade, slot):
    rows, ok = [], True
    worst_r, worst_gap = 0.0, 1e9
    for phi in np.linspace(PHI_OPEN, PHI_OPEN + TWIST, 31):
        w = [to_world(blade, phi, k) for k in range(N)]
        worst_r = max(worst_r, max(max(math.hypot(x, y) for x, y in g.exterior.coords) for g in w))
        for k in range(N // 2):     # same level: k and k + 3
            worst_gap = min(worst_gap, w[k].distance(w[k + N // 2]))
    rows.append(f"sweep: furthest blade point from the centre {worst_r:.2f} mm (limit {R_OUT:.1f})")
    rows.append(f"sweep: closest same-level (opposite) blades {worst_gap:.2f} mm apart (need >= {mb.PROCESS['gap_min']})")
    ok &= worst_r <= R_OUT + 1e-6 and worst_gap >= mb.PROCESS["gap_min"]
    return rows, ok


def main():
    miss, centre, blade = synthesize()
    phi_c = PHI_OPEN + TWIST
    out, ok = [], True
    out.append("IRIS BOX MECHANISM BUDGET (handbook section 7), Scott's form A")
    out.append(f"box {BOX_D:.0f} x {BOX_H:.0f} mm; {N} blades on three levels; ring turns {TWIST:.0f} deg")
    out.append(f"pivots at r {RP}, drive pins at r {RD}, ring {PHI_OPEN:+.0f} -> {phi_c:+.0f} deg; opening {2 * R_A:.0f} mm across")

    # the slot: the drive pin's path in the blade's frame
    dists = [pose(p, 0)[2] for p in np.linspace(PHI_OPEN, phi_c, 61)]
    betas = np.degrees(np.unwrap([pose(p, 0)[1] for p in np.linspace(PHI_OPEN, phi_c, 61)]))
    s0, s1 = min(dists), max(dists)
    out.append(f"blade swing {abs(betas[-1] - betas[0]):.1f} deg; drive pin runs {s0:.1f} -> {s1:.1f} mm from the pivot")

    # clearances (handbook 1-2): a vertical pin in a vertical hole; the slot's width
    pin_hole = mb.stack([("pin radius, XY wall", mb.PROCESS["xy_wall"]), ("hole radius, prints small", mb.PROCESS["hole_vertical"])])
    gap = mb.PROCESS["gap_min"] + pin_hole["worst_case"]
    out.append(f"pivot and drive pins {PIN_D} mm: radial clearance >= {gap:.2f} (0.30 open + {pin_hole['worst_case']:.2f} worst case), "
               f"so holes and slot {PIN_D + 2 * gap:.2f} wide; the coupon tries 0.40 and 0.55")
    level = mb.stack([("blade thickness", mb.PROCESS["z_step"]), ("level height", mb.PROCESS["z_step"])])
    out.append(f"level gaps: >= {mb.PROCESS['gap_min'] + level['worst_case']:.2f} mm between base, the three blade levels and ring (0.30 + {level['worst_case']:.2f}); "
               f"stack {3 * 1.4 + 4 * 0.5:.1f} mm with 1.4 mm blades")
    # pin strength: a 4 mm pin standing in the base, loaded across its layers
    F, L = 5.0, 3.0
    sigma = 32 * F * L / (math.pi * PIN_D ** 3)
    out.append(f"pin bending: {F} N at {L} mm on a {PIN_D} mm pin = {sigma:.1f} MPa (PLA across layers ~20 MPa)")

    slot = box(s0, -PIN_D / 2 - gap, s1, PIN_D / 2 + gap)
    hole = Point(0, 0).buffer(PIN_D / 2 + gap)
    inner = blade.buffer(-EDGE)
    slot_ok = inner.contains(slot.buffer(0.01)) if not inner.is_empty else False
    pivot_ok = blade.buffer(-EDGE).contains(hole) if not blade.buffer(-EDGE).is_empty else False
    out.append(f"slot inside the blade with {EDGE} mm round it: {slot_ok}; pivot hole likewise: {pivot_ok}")
    ok &= slot_ok and pivot_ok

    open_w = unary_union([to_world(blade, PHI_OPEN, k) for k in range(N)])
    intrude = disk(R_A).intersection(open_w).area
    cover = unary_union([to_world(blade, phi_c, k) for k in range(N)])
    out.append(f"open: blade area inside the {2 * R_A:.0f} mm opening {intrude:.2f} mm2 (want 0)")
    pin = [math.hypot(*(lambda f: (RD * math.cos(f), RD * math.sin(f)))(math.radians(p))) for p in (PHI_OPEN,)]
    out.append(f"drive pins stand at r {RD} - {PIN_D / 2 + gap:.2f} = {RD - PIN_D / 2 - gap:.2f}, outside the opening's {R_A}: {RD - PIN_D / 2 - gap > R_A}")
    ok &= RD - PIN_D / 2 - gap > R_A
    miss = disk(R_A - LIP).difference(cover)
    pin_r = max([math.hypot(g.centroid.x, g.centroid.y) for g in getattr(miss, "geoms", [miss]) if g.area > 0.01] or [0])
    out.append(f"closed: uncovered area of the {2 * (R_A - LIP):.0f} mm mouth {miss.area:.2f} mm2 (want under 1: the centre pinhole), "
               f"furthest gap from the centre {pin_r:.1f} mm; "
               f"blade area {blade.area:.0f} mm2")
    ok &= intrude < 1.0 and miss.area < 1.0 and pin_r < 1.0
    rows, sok = sweep_checks(blade, slot)
    out += rows
    ok &= sok
    if not ok:
        out.append("OPEN ITEM: the centre doesn't close. Opposite blades share a level and keep a gap")
        out.append("across the centre, and trimming them clear of each other through the turn leaves the")
        out.append("hole above. Fix: two blade shapes, three of each, one of each opposite pair reaching")
        out.append("past the centre. It changes the blades' outline, not the joints the coupon tests.")
    out.append("PASS" if ok else "FAIL")
    text = "\n".join(out)
    print(text)
    (HERE / "checks" / "budget.txt").write_text(text + "\n")
    json.dump({"blade": [list(p) for p in blade.exterior.coords], "slot": [s0, s1], "gap": gap, "LIP": LIP,
               "RP": RP, "RD": RD, "PHI_OPEN": PHI_OPEN, "TWIST": TWIST, "R_A": R_A, "R_OUT": R_OUT,
               "PIN_D": PIN_D}, open(HERE / "checks" / "blade.json", "w"), indent=1)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.2))
    for ax, phi, name in zip(axs, [PHI_OPEN, PHI_OPEN + TWIST / 2, phi_c], ["open", "half", "closed"]):
        for k in range(N):
            g = to_world(blade, phi, k)
            ax.fill(*g.exterior.xy, alpha=0.45, color=["#c9b48a", "#7a8ca6", "#a6c39b"][k % 3], ec="k", lw=0.6)
        for r, st in ((R_A - LIP, "--"), (R_OUT, "-")):
            t = np.linspace(0, 2 * np.pi, 200)
            ax.plot(r * np.cos(t), r * np.sin(t), "k" + st, lw=0.6)
        ax.set_aspect("equal"); ax.set_xlim(-50, 50); ax.set_ylim(-50, 50); ax.set_title(name); ax.axis("off")
    fig.suptitle("Iris box: the six blades open, half and closed (computed, not a render)")
    fig.savefig(HERE / "images" / "iris_kinematics.png", dpi=110, bbox_inches="tight")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
