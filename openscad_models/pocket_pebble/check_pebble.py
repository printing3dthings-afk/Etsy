#!/usr/bin/env python3
"""Pocket Pebble's hinge and latch (2026-11-04), on the exported parts:

- every print sits on the bed as exported
- shut, nothing touches: lid, base and pins
- opening: the lid swings clear of the base from shut to its stop, in 1 deg
  steps, leaving out the latch's bump; the stop is where the lid's back first
  meets the base's
- the latch: as the lid lifts, how far the tongue's tip must bend in to pass
  the lip. Zero shut (it rests unstressed), more than zero on the way up (the
  click), and zero again once past
- the pins turn freely in the lid's knuckle at every angle; a pin turned
  4 deg in the base's knuckle hits it (the teardrop keys it), and pushed
  0.5 past home its key meets the lid's knuckle (it stops there)

    python3 check_pebble.py
"""
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from part_mesh import load  # noqa: E402
from manifold3d import Manifold  # noqa: E402

V = {k: float(v) for k, v in re.findall(r'"(\w+)", (-?[0-9.]+)', (HERE / "logs" / "base.log").read_text())}
AY, HB, YP, LIP_TOP = V["AY"], V["HB"], V["YP"], V["LIP_TOP"]
fails = []


def part(name):
    return load(str(HERE / "parts" / f"{name}.stl"))


def ov(a, b):
    return (a ^ b).volume()


def say(ok, text, fail=None):
    print(f"  {'ok  ' if ok else 'FAIL'}  {text}")
    if not ok:
        fails.append(fail or text)


def opened(m, deg):
    """turn a manifold about the hinge axis, the lid's front lifting"""
    return m.translate([0, -AY, -HB]).rotate([-deg, 0, 0]).translate([0, AY, HB])


print("== on the bed")
for p in ("base", "lid", "pin"):
    z = part(p).bounding_box()[2]
    say(abs(z) < 0.01, f"{p}: lowest point z {z:+.3f}", f"{p} off the bed")

base, lid, pins = part("base"), part("lid_use0"), part("pins_use")
print("== shut")
say(ov(lid, base) <= 0.01, f"lid and base: {ov(lid, base):.3f} mm3")
say(ov(pins, base) <= 0.01, f"pins and base: {ov(pins, base):.3f} mm3")
say(ov(pins, lid) <= 0.01, f"pins and lid: {ov(pins, lid):.3f} mm3")

# the latch's working end: the tongue below the lip's top, bump and all
tip_box = Manifold.cube([12, 8, LIP_TOP + 0.3]).translate([-6, YP - 1, 0])
tip = lid ^ tip_box
rest = lid - tip_box

print("== opening")
stop = None
for a in range(1, 181):
    v = ov(opened(rest, a), base)
    if v > 0.05:
        stop = a
        break
say(stop is not None and stop >= 95, f"the lid swings clear of the base to {stop - 1 if stop else 180} deg "
    f"(its back meets the base's at {stop} deg)")
worst = max(ov(opened(lid, a), pins) for a in range(0, (stop or 180), 5))
say(worst <= 0.01, f"the pins turn freely in the lid's knuckle to the stop (worst {worst:.3f} mm3)")
say(ov(pins.translate([0, -AY, -HB]).rotate([4, 0, 0]).translate([0, AY, HB]), base) >= 0.05,
    "a pin turned 4 deg hits the base's knuckle: keyed")

left, right = (pins ^ Manifold.cube([40, 40, 40]).translate([-40, 0, 0])), (pins ^ Manifold.cube([40, 40, 40]))
pushed = left.translate([0.5, 0, 0]) + right.translate([-0.5, 0, 0])
say(ov(pushed, lid) >= 0.05, "pushed 0.5 past home, a pin's key meets the lid's knuckle: it stops there")

print("== the latch: how far the tongue's tip bends in as the lid lifts")


def bend(a):
    """the least shift in +y (toward the middle) that frees the tip at opening a"""
    t = opened(tip, a)
    if ov(t, base) <= 0.01:
        return 0.0
    lo, hi = 0.0, 3.0
    if ov(t.translate([0, hi, 0]), base) > 0.01:
        return hi
    for _ in range(14):
        mid = (lo + hi) / 2
        if ov(t.translate([0, mid, 0]), base) > 0.01:
            lo = mid
        else:
            hi = mid
    return hi


prof = [(a, bend(a)) for a in np.arange(0, 14.01, 0.5)]
for a, d in prof:
    print(f"        {a:4.1f} deg  {d:.2f} mm  " + "#" * int(round(d * 20)))
dmax = max(d for _, d in prof)
first_free = next((a for a, d in prof if a > 0 and d == 0 and any(dd > 0 for aa, dd in prof if aa < a)), None)
say(prof[0][1] == 0.0, "shut, the tongue rests unbent")
say(0.3 <= dmax <= 1.0, f"lifting, it bends in up to {dmax:.2f} mm to pass the lip: the click")
say(first_free is not None, f"past {first_free} deg it is free")

print("\nFIT CHECK " + ("OK" if not fails else "FAILED:\n  " + "\n  ".join(fails)))
sys.exit(1 if fails else 0)
