#!/usr/bin/env python3
"""Fold Stand v4's hinge test print, checked on its own exported parts (2026-11-10):
the same twist-lock pivot and print-in-place prop hinge as the full stand, on a short,
narrow plate (W 34, hinge 14 up it, a 22 mm prop) and a base with just the lugs.

    python3 check_hinge_test.py
"""
import math
import sys

import check_stand_v4 as c

A, PIN, HIN = 14.0, c.PIN, c.HIN
fail = []


def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    fail.append(msg) if not ok else None


def hinge(r):
    return c.rx(r, (0, A, HIN))


base, plate = c.load("coupon_base"), c.load("coupon_plate")
parts = plate.split(only_watertight=False)
parts = sorted(parts, key=lambda m: m.volume)
prop, plate = parts[0], parts[1]
print("== the plate's print")
check(c.ov(plate, prop) < 0.01, "the prop and the plate print apart")
g = c.gap(prop, plate)
check(g >= 0.38, f"least gap {g:.2f}")
# its slot runs only 12 below the hinge (26 on the stand), so it stops sooner: it only has
# to show the hinge turns freely and holds
swing = [r for r in range(0, -136, -5) if c.ov(prop.copy().apply_transform(hinge(r)), plate) > 0.05]
stop = next((r for r in range(-135, -200, -1) if c.ov(prop.copy().apply_transform(hinge(r)), plate) > 0.05), None)
check(not swing, f"the prop swings out behind the plate to 135 deg untouched; the short test slot stops it at {stop}"
      + (f" (touches at {swing})" if swing else ""))
for side in (-1, 1):
    check(c.ov(prop.copy().apply_translation([side, 0, 0]), plate) > 0.5, f"pushed 1 mm {'left' if side < 0 else 'right'}, a cone stops it")
print("== the pivot")
free = [th for th in range(0, 91, 5) if c.ov(plate.copy().apply_transform(c.plate_T(th)), base) > 0.05]
check(not free, "turns 0-90 in the lugs untouched" + (f" (touches at {free})" if free else ""))
loose = [th for th in range(0, 86, 5) if c.ov(plate.copy().apply_transform(c.tr(0, 0, 2) @ c.plate_T(th)), base) < 0.5]
check(not loose, "0-85 deg, lifted 2 mm it hits the lugs: captured" + (f" (free at {loose})" if loose else ""))
path = max(c.ov(plate.copy().apply_transform(c.tr(0, 0, d) @ c.plate_T(c.PASS)), base) for d in (0, 3, 6, 9, 12, 15))
check(path < 0.05, f"at {c.PASS:.0f} deg it lifts out untouched ({path:.3f} mm3)")
print("\nHINGE TEST " + ("FAILED" if fail else "OK"))
sys.exit(1 if fail else 0)
