#!/usr/bin/env python3
"""Penny Spinner's fit and balance (2026-11-04), on the exported parts:

- every print sits on the bed as exported
- the crown sits on the base and the stem in both, touching nothing; the
  crown 0.1 lower would be into the base, so it rests on it
- the stem's barb catches in the base when it is pulled up, and turned 6 deg
  its hex hits both the crown and the base, so a twirl turns the whole top
- two pennies in each pocket touch nothing; lifted 0.5 or pushed 0.5 out
  they hit the pocket, and a penny is wider than its window, so none can leave
- balance: the spinning body's centre of mass, empty and with 16 pennies,
  against the spin axis
- how far it can lean before anything but the tip touches the table

    python3 check_spinner.py
"""
import math
import re
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from part_mesh import load  # noqa: E402

SCAD = (HERE / "penny_spinner.scad").read_text()


def const(name):
    return float(re.search(rf"\b{name}\s*=\s*([0-9.]+);", SCAD).group(1))


COIN_D, COIN_T, N, STACK = const("COIN_D"), const("COIN_T"), int(const("N")), int(const("STACK"))
WIN_R = const("WIN_R")
COIN_G = 2.5            # a penny since 1982 (US Mint)
OLD_COIN_G = 3.11       # before 1982
PLA = 1.24e-3           # g per mm3, solid
fails = []


def part(name):
    return load(str(HERE / "parts" / f"{name}.stl"))


def tri(name):
    return trimesh.load(HERE / "parts" / f"{name}.stl", force="mesh")


def ov(a, b):
    return (a ^ b).volume()


def say(ok, text, fail=None):
    print(f"  {'ok  ' if ok else 'FAIL'}  {text}")
    if not ok:
        fails.append(fail or text)


def none(name, v):
    say(v <= 0.05, f"{name}: {v:.3f} mm3", name)


def hits(name, v, need=0.5):
    say(v >= need, f"{name}: {v:.2f} mm3", name)


print("== on the bed")
for p in ("crown", "base", "stem"):
    z = part(p).bounding_box()[2]
    say(abs(z) < 0.01, f"{p}: lowest point z {z:+.3f}", f"{p} off the bed")

crown, base, stem = part("crown_use"), part("base_use"), part("stem_use")
print("== crown, base and stem")
none("crown on the base", ov(crown, base))
hits("crown 0.1 lower is into the base", ov(crown.translate([0, 0, -0.1]), base))
none("stem through the crown", ov(stem, crown))
none("stem in the base", ov(stem, base))
hits("stem 0.1 lower: its collar is on the crown's hub", ov(stem.translate([0, 0, -0.1]), crown))
# the barb is a thin ring, so any collision is the catch; at 1.0 it is well
# into the throat
for dz in (0.5, 1.0):
    hits(f"stem pulled {dz} up: the barb catches in the base", ov(stem.translate([0, 0, dz]), base), 0.05)
turned = stem.rotate([0, 0, 6])
# the hex has 0.15 of clearance, so a few degrees of play; at 6 any touch is the key biting
hits("stem turned 6 deg: its hex hits the crown", ov(turned, crown), 0.05)
hits("stem turned 6 deg: its hex hits the base", ov(turned, base), 0.05)

print("== the pennies")
coins = part("coins")
none("16 pennies in their pockets", ov(coins, crown) + ov(coins, base))
# the top penny of each stack, alone, so the lift is the gap above the stack
r_p = float(re.search(r'"R_P", ([0-9.]+)', (HERE / "logs" / "crown_use.log").read_text()).group(1))
top = trimesh.creation.cylinder(radius=COIN_D / 2, height=COIN_T, sections=96)
top.apply_translation([r_p, 0, (STACK - 0.5) * COIN_T])
from part_mesh import to_manifold  # noqa: E402
top_m = to_manifold(top, "penny")
hits("the top penny lifted 1.0 hits the window's bevel", ov(top_m.translate([0, 0, 1.0]), crown), 0.05)
hits("a penny pushed 0.5 out hits the pocket", ov(top_m.translate([0.5, 0, 0]), crown), 0.05)
say(WIN_R < COIN_D / 2 - 1.5, f"window {2 * WIN_R:.1f} across against a penny's {COIN_D:.2f}: a {COIN_D / 2 - WIN_R:.2f} mm lip")

print("== balance and lean")
BODY = ("crown_use", "base_use", "stem_use")
body = trimesh.util.concatenate([tri(n) for n in BODY])
vol = sum(tri(n).volume for n in BODY)
com = sum(tri(n).center_mass * tri(n).volume for n in BODY) / vol
off = math.hypot(com[0], com[1])
say(off < 0.02, f"empty: centre of mass {off:.4f} mm off the axis")
m_body = vol * PLA
m_coins = N * STACK * COIN_G
com_c = (com * m_body + np.array([0, 0, STACK * COIN_T / 2]) * m_coins) / (m_body + m_coins)
tip_z = body.bounds[0][2]
print(f"  note  solid PLA body {m_body:.0f} g (less as printed, with infill); 16 pennies {m_coins:.0f} g")
# one pre-1982 penny among the newer ones: the worst single mismatch
odd = (OLD_COIN_G - COIN_G) * r_p / (m_body + m_coins)
print(f"  note  one pre-1982 penny (3.11 g) among the rest moves the centre {odd:.3f} mm off the axis")
# the spin's inertia, the coins against the body
i_body = sum(tri(n).moment_inertia[2, 2] for n in BODY) / vol * m_body
i_coins = m_coins * (r_p ** 2 + (COIN_D / 2) ** 2 / 2)
print(f"  note  spin inertia: body {i_body / 100:.0f} g cm2 (solid), pennies {i_coins / 100:.0f} g cm2: "
      f"the pennies make it {1 + i_coins / i_body:.1f} times the empty top's")
print(f"  note  centre of mass {com[2] - tip_z:.1f} mm above the tip empty, {com_c[2] - tip_z:.1f} with pennies")
v = body.vertices
r = np.hypot(v[:, 0], v[:, 1])
far = r > 3
lean = np.degrees(np.arctan2(v[far, 2] - tip_z, r[far])).min()
say(lean >= 15, f"it leans {lean:.1f} deg before its rim touches the table")

print("FIT CHECK OK" if not fails else "FIT CHECK FAILED: " + "; ".join(fails))
sys.exit(1 if fails else 0)
