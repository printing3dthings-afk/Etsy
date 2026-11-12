#!/usr/bin/env python3
"""The gear heart, by the numbers, before it is modelled (handbook section 7).

Scott picked 9A (2026-11-11): "the heart's outline is made of meshing gears, all of
them turning together from a knob in the middle."

The concept:
- A flat heart-shaped backplate carries the gears on posts. The gears ring the
  outline, each meshing with its neighbours.
- The loop is an even number of gears, so it can turn: an odd loop locks solid.
- The centre gear carries the knob and meshes with the gear at the heart's top dip.
- The gears print flat on their own and press onto split posts with a barb, which
  holds them. Printed in place, a gear would print on the plate and fuse to it.

What this script settles:
- layout: the gears' centres on a heart curve, scaled until the loop of meshing
  distances closes exactly;
- clearance: every pair of gears that should not touch is clear;
- mesh: backlash, and what it keeps under the error stack;
- snap: prong strain against PLA's limit, and the barb's engagement against the
  stack (the 3 x RSS rule).

    python3 gear_budget.py        (prints the budget; writes checks/budget.txt, layout.json)
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from mechanism_budget import PROCESS, cantilever, engagement, mating_force  # noqa: E402

# ---- the gears ----
MOD = 1.5            # mm; teeth 4.7 mm apart at the pitch circle, big enough to read and print
PA = 20.0            # pressure angle, deg
DC = 0.30            # centre distance added to every mesh (backlash); the coupon tries 0.15/0.30/0.45
SIDE = [16, 12]      # teeth on the outline gears, alternating, starting next to the top gear
TOP_Z = 20           # the gear in the heart's top dip: big, so its neighbours clear each other across it
BOTTOM_Z = 16        # the gear at the heart's point
KNOB_Z = 16          # the centre gear; the knob is a handle raised on it, so it can be any size
                     # (a 24-tooth centre gear overlapped the outline gears low on each side)
PER_SIDE = 6         # outline gears on each side between top and bottom -> loop of 2 + 2*PER_SIDE
                     # (4 made a 95 mm heart with no room in the middle; a sweep of 288
                     # layouts picked this one: 126 mm, every non-meshing pair 2.3 mm clear)
TIP_CLEAR = 1.0      # gears that don't mesh: tip circles at least this far apart

# ---- the posts (snap) ----
# Two rectangular prongs, constant section, their outer corners on a circle the gear's
# hub turns on. A round post split by a slot left half-round prongs that tapered to
# an edge at the slot (gate min wall 0.58), and a "tapered" prong the model didn't
# actually draw: drawn straight, 2.0 thick bent 0.9 is 1.7 % strain, over PLA's 1.4.
POST_R = 3.5         # the circle the prongs' outer corners sit on: the gear's hub turns on them
PRONG_W = 4.0        # each prong across the slot's direction
PRONG_T = 1.6        # each prong's thickness, in the direction it bends
BORE_GAP = 0.35      # running gap, hub to post, drawn, each side
BARB = 0.9           # how far the barb stands past the bore
STRAIN_MAX = 1.2     # % going on: the once-only limit is 1.4; keep a margin
GEAR_T = 6.0
WASHER = 1.0
FLOOR = 1.5          # plate left under the pocket the post rises from
UNDER = 37.0         # barb underside, deg from the post's axis: 45 got 10,330 support moves from the gate's slicer
PULL_MIN = 10.0      # N a gear must resist before it pulls off its post
X_OUT = math.sqrt(POST_R ** 2 - (PRONG_W / 2) ** 2)     # where a prong's outer face sits
SLOT = 2 * (X_OUT - PRONG_T)
# the flexing length that keeps strain at STRAIN_MAX (constant section: eps = 1.5 t y / L^2)
PRONG_L = math.ceil(math.sqrt(1.5 * PRONG_T * BARB / (STRAIN_MAX / 100)) * 2) / 2
RELIEF = PRONG_L - WASHER - GEAR_T                       # how far the post's root sits below the plate top
PLATE_T = RELIEF + FLOOR


def r_pitch(z):
    return MOD * z / 2


def r_tip(z):
    return r_pitch(z) + MOD


def heart(t, s):
    """The classic parametric heart, t from 0 (top dip) to pi (point), right half."""
    x = 16 * math.sin(t) ** 3
    y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
    return (s * x, s * y)


def march(s, zs):
    """Place gears along the right half of the heart from the top dip, each at its
    meshing distance from the last. Returns their centres and the leftover: the
    distance still to the point gear minus the distance it needs."""
    pts, t = [heart(0, s)], 0.0
    for i in range(1, len(zs) - 1):
        need = MOD * (zs[i - 1] + zs[i]) / 2 + DC
        lo, hi = t, math.pi
        for _ in range(60):                       # bisect along the curve for the chord
            mid = (lo + hi) / 2
            d = math.dist(pts[-1], heart(mid, s))
            lo, hi = (mid, hi) if d < need else (lo, mid)
        t = (lo + hi) / 2
        pts.append(heart(t, s))
    bottom = heart(math.pi, s)
    need = MOD * (zs[-2] + zs[-1]) / 2 + DC
    return pts + [bottom], math.dist(pts[-1], bottom) - need


def layout():
    zs = [TOP_Z] + [SIDE[i % 2] for i in range(PER_SIDE)] + [BOTTOM_Z]
    lo, hi = 1.0, 10.0
    for _ in range(80):                           # scale the heart until the loop closes
        mid = (lo + hi) / 2
        _, res = march(mid, zs)
        lo, hi = (mid, hi) if res < 0 else (lo, mid)
    s = (lo + hi) / 2
    right, res = march(s, zs)
    gears = [{"name": "top", "z": zs[0], "at": right[0]}]
    for i in range(1, len(zs) - 1):
        gears.append({"name": f"right{i}", "z": zs[i], "at": right[i]})
        gears.append({"name": f"left{i}", "z": zs[i], "at": (-right[i][0], right[i][1])})
    gears.append({"name": "bottom", "z": zs[-1], "at": right[-1]})
    # the knob gear, on the axis below the top gear, meshing with it
    top = right[0]
    knob_y = top[1] - (MOD * (TOP_Z + KNOB_Z) / 2 + DC)
    gears.append({"name": "knob", "z": KNOB_Z, "at": (0.0, knob_y)})
    return s, res, gears


def meshes(gears):
    by = {g["name"]: g for g in gears}
    pairs = [("top", "right1"), ("top", "left1"), ("knob", "top")]
    for i in range(1, PER_SIDE):
        pairs += [(f"right{i}", f"right{i + 1}"), (f"left{i}", f"left{i + 1}")]
    pairs += [(f"right{PER_SIDE}", "bottom"), (f"left{PER_SIDE}", "bottom")]
    return [(by[a], by[b]) for a, b in pairs]


def main():
    lines = ["GEAR HEART BUDGET (handbook section 7; values from mechanism_budget.PROCESS)", ""]
    ok = True
    s, res, gears = layout()
    xs = [g["at"][0] for g in gears]
    ys = [g["at"][1] for g in gears]
    loop = 2 + 2 * PER_SIDE
    lines.append(f"layout: heart scale {s:.3f}, loop of {loop} gears ({'even: turns' if loop % 2 == 0 else 'ODD: LOCKS'}), "
                 f"closes to {res:+.4f} mm; module {MOD}, +{DC} on every centre distance")
    span_x = max(x + r_tip(g["z"]) for x, g in zip(xs, gears)) - min(x - r_tip(g["z"]) for x, g in zip(xs, gears))
    span_y = max(y + r_tip(g["z"]) for y, g in zip(ys, gears)) - min(y - r_tip(g["z"]) for y, g in zip(ys, gears))
    lines.append(f"  gears span {span_x:.1f} x {span_y:.1f} mm (P1S plate 256)")
    ok &= loop % 2 == 0 and abs(res) < 0.01 and span_x < 240 and span_y < 240
    pairs = meshes(gears)
    for a, b in pairs:
        d = math.dist(a["at"], b["at"])
        want = MOD * (a["z"] + b["z"]) / 2 + DC
        if abs(d - want) > 0.01:
            ok = False
            lines.append(f"  FAIL mesh {a['name']}-{b['name']}: {d:.3f} vs {want:.3f}")
    lines.append(f"  {len(pairs)} meshes, each at its pitch distance + {DC}: checked")
    meshed = {frozenset((a["name"], b["name"])) for a, b in pairs}
    worst = 99.0
    for i, a in enumerate(gears):
        for b in gears[i + 1:]:
            if frozenset((a["name"], b["name"])) in meshed:
                continue
            gap = math.dist(a["at"], b["at"]) - r_tip(a["z"]) - r_tip(b["z"])
            worst = min(worst, gap)
            if gap < TIP_CLEAR:
                ok = False
                lines.append(f"  FAIL {a['name']} and {b['name']} too close: tips {gap:.2f} apart")
    lines.append(f"  gears that don't mesh: tips at least {worst:.2f} apart (need {TIP_CLEAR})")

    # mesh: backlash from the added centre distance, and the stack that eats it
    backlash = 2 * DC * math.tan(math.radians(PA))
    stack_c = [("post A position, XY", PROCESS["xy_wall"]), ("post B position, XY", PROCESS["xy_wall"]),
               ("tooth flank A, XY wall", PROCESS["xy_wall"]), ("tooth flank B, XY wall", PROCESS["xy_wall"])]
    e = engagement(DC, stack_c, 1.0)
    lines.append("")
    lines.append(f"mesh: +{DC} centre distance = {backlash:.2f} mm backlash; the stack that can close it: worst "
                 f"{e['worst_case']:.2f}, RSS {e['rss']:.2f} -> {'free at RSS' if DC > e['rss'] else 'MAY BIND'}, "
                 f"{'free at worst case' if DC >= e['worst_case'] else 'binds only if every error lines up'}")
    ok &= DC > e["rss"]
    lines.append(f"  hub play {BORE_GAP} each side lets a gear drift up to {2 * BORE_GAP:.2f}; driving pushes meshing "
                 f"gears apart, so play opens the mesh rather than closing it")

    # snap: prong strain going on, and the barb's engagement
    c = cantilever(t=PRONG_T, L=PRONG_L, b=PRONG_W, y=BARB, taper=False, repeated=False)
    lines.append("")
    lines.append(f"snap: two prongs {PRONG_T} thick x {PRONG_W} wide, corners on a {2 * POST_R} circle, slot {SLOT:.2f}; "
                 f"flexing length {PRONG_L} (the post rises from a pocket {RELIEF:.1f} deep: plate {PLATE_T:.1f} thick)")
    lines.append(f"  bent {BARB} going on: strain {c['strain_pct']:.2f} % vs once-only {c['limit_pct']:.2f} % -> "
                 f"{'ok' if c['ok'] else 'FAIL'}; {c['tip_force_N']:.1f} N each prong")
    ok &= c["ok"]
    c2 = cantilever(t=PRONG_T, L=PRONG_L, b=PRONG_W, y=BARB, taper=False, repeated=True)
    lines.append(f"  vs the repeated-flexing limit {c2['limit_pct']:.2f} %: "
                 f"{'ok' if c2['ok'] else 'over: fine to put on once, not to take on and off often'}")
    if SLOT < 2 * BARB + 0.6:
        ok = False
        lines.append(f"  FAIL the slot {SLOT:.2f} can't close {2 * BARB} with 0.6 to spare")
    else:
        lines.append(f"  the slot {SLOT:.2f} closes {2 * BARB} going on, {SLOT - 2 * BARB:.2f} to spare")
    stack_b = [("barb lip standing out of the post", PROCESS["overhang_lip"]),
               ("hub bore, vertical hole", PROCESS["hole_vertical"]),
               ("post radius, XY wall", PROCESS["xy_wall"]),
               ("barb height, layer quantised", PROCESS["z_step"])]
    eb = engagement(BARB, stack_b, 3.0)
    lines.append(f"  barb engagement {BARB}: RSS {eb['rss']:.2f}, worst {eb['worst_case']:.2f}, ratio {eb['ratio']:.1f} "
                 f"-> {'ok' if eb['ok'] else 'FAIL'}")
    ok &= eb["ok"]
    m = mating_force(2 * c["tip_force_N"], 30)
    lines.append(f"  push-on force with a 30 deg lead-in: about {m['W_N']:.0f} N")
    # The barb's underside is 45 deg, not square: a square ledge 0.9 wide would print in
    # mid-air. So it holds by friction on a slope, and the pull-off force is finite:
    off = mating_force(2 * c["tip_force_N"], UNDER)
    lines.append(f"  pull-off force with its {UNDER:.0f} deg underside: about {off['W_N']:.0f} N "
                 f"({'self-locking' if off['self_locking'] else 'not self-locking'}; a square underside would be, "
                 f"but can't print)")
    ok &= off["W_N"] >= PULL_MIN
    lines.append(f"  -> {'ok' if off['W_N'] >= PULL_MIN else 'FAIL'}: needs >= {PULL_MIN:.0f} N so a gear isn't pulled off "
                 f"by turning or brushing it")
    free = BORE_GAP - (PROCESS["xy_wall"] + PROCESS["hole_vertical"])
    lines.append(f"  hub running gap {BORE_GAP} less the worst case closing it = {free:.2f} -> "
                 f"{'turns' if free > 0 else 'MAY RUB'}")
    ok &= free > 0
    lines.append("")
    lines.append("PASS: build the coupon" if ok else "FAIL: change the design before modelling")
    text = "\n".join(lines)
    print(text)
    (HERE / "checks").mkdir(exist_ok=True)
    (HERE / "checks" / "budget.txt").write_text(text + "\n")
    (HERE / "layout.json").write_text(json.dumps({"scale": s, "module": MOD, "pa": PA, "dc": DC,
                                                  "gears": gears}, indent=1))


if __name__ == "__main__":
    main()
