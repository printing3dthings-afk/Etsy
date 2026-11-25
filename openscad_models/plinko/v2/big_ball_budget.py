#!/usr/bin/env python3
"""Plinko: bigger print-in-place balls, the neck's numbers (2026-11-25).

v1's 5 mm teardrops broke loose during the print (Scott: "everything is too small for that"). Scott
asked to test bigger balls printed inside the cage alongside the 6 mm BB test. Each ball here is a
10 mm teardrop standing on a short neck to the floor:
  - while printing, the neck must hold against the nozzle's sideways drag on the growing ball;
  - after, a toothpick through the cage must snap it.
The neck is printed upright, so it breaks across its layers: interlayer strength (z_factor).

    python3 big_ball_budget.py      (writes ../checks/big_ball_budget.txt)
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from mechanism_budget import PLA  # noqa: E402

R = 5.0                       # the ball
SIGMA = 40.0 * PLA["z_factor"]   # MPa across layers: ~40 in-layer for printed PLA, x 0.55
DRAG = 0.5                    # N, a nozzle's sideways brush on a printed part (a rough figure, not measured)
TIP = R * math.sqrt(2)        # the 45 deg point, below the ball's centre
out = []
line = out.append
line(f"BIG BALL: {2 * R:.0f} mm teardrop, centre {TIP:.2f} above its point; interlayer strength ~{SIGMA:.0f} MPa")
for d in (1.6, 2.0, 2.4):      # 1.2 holds only 0.3 N: under the drag figure, so not tried
    Z = math.pi * d ** 3 / 32                      # section modulus, mm^3
    M = SIGMA * Z                                  # N mm the neck takes
    top = TIP + R                                  # the ball's top, above the neck: the worst lever while printing
    hold = M / top                                 # N at the ball's top that snaps it
    poke = M / TIP                                 # N at the ball's centre (a toothpick)
    line(f"  neck {d}: holds {hold:.2f} N at the ball's top while printing (vs ~{DRAG} N of drag, "
         f"{hold / DRAG:.1f}x); a toothpick at the centre snaps it at {poke:.2f} N")
v1 = SIGMA * math.pi * 0.6 ** 3 / 32 / (2.5 * math.sqrt(2) + 2.5)
line(f"  v1's 0.6 neck on a 5 mm ball held about {v1:.2f} N at its top; its floating balls held nothing."
     " Both far under a nozzle's drag, which fits Scott's result.")
line("  The drag figure is a rough one: the test print is what decides the neck.")
(HERE.parent / "checks" / "big_ball_budget.txt").write_text("\n".join(out) + "\n")
print("\n".join(out))
