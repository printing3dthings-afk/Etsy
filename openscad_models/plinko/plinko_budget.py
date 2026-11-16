#!/usr/bin/env python3
"""Snowfall Plinko (hourglass): the hand calculations before modelling (2026-11-16,
mechanism handbook section 7). Writes checks/plinko_budget.txt.

The balls print loose inside a closed board, under a lattice front. They are teardrops: a
round ball with a 45 deg point underneath, so nothing hangs past 45 deg. In use the board
stands up with the point facing its back, so each ball rolls in the board's plane as a
true circle.
"""
from math import sqrt
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from mechanism_budget import PROCESS  # noqa: E402

BALL = 5.0                 # equator diameter
TIP = BALL / 2 * sqrt(2)   # the point, below the ball's centre (45 deg cone tangent to the ball)
BALL_H = BALL / 2 + TIP    # 6.04 tall as it prints
LAYER = 0.2
FLOAT = [0.2, 0.4]         # variants 1 and 2: the point this far above the floor (1 and 2 layers)
NECK = 0.6                 # variant 3: the point printed onto the floor, a 0.6 neck to snap
LAT_GAP_MIN = 0.6          # the lattice's underside above the tallest ball's top
LAT_BAR, LAT_OPEN = 1.2, 3.2
XY_GAP = 0.8               # ball to ball, ball to wall or peg, as printed
PEG = 2.4
PASS_MIN = BALL + 1.5      # a gap a ball goes through: wide enough not to wedge
STOP_MAX = BALL - 1.5      # a gap a ball must not enter
PLA = 1.24                 # g/cm3


def main():
    out, fails = [], []

    def line(ok, msg):
        out.append(("  ok   " if ok else "  FAIL ") + msg)
        if not ok:
            fails.append(msg)

    g = PROCESS["gap_min"]
    out.append("SNOWFALL PLINKO: BUDGET (hand calculations, before modelling)")
    out.append(f"ball: {BALL} across, {BALL_H:.2f} tall as printed (point {TIP:.2f} below its centre)")
    vol = 3.14159 / 6 * BALL ** 3 * 1.08          # the sphere plus its cone, about 8 % more
    out.append(f"  mass about {vol * PLA / 1000:.3f} g each (solid; as sliced, less)")
    for f in FLOAT:
        out.append(f"  variant float {f}: the point hangs {f / LAYER:.0f} layer(s) of air above the floor, "
                   + (f"under the handbook's {g} open gap: exploratory, it may tack to the floor"
                      if f < g else f"over the handbook's {g} open gap")
                   + ". Its first layers print over air and drop; a shake or a poke frees it. The test print decides")
    m = 50.0 * 3.14159 * (NECK / 2) ** 2           # PLA ~50 MPa across a 0.6 neck
    out.append(f"  variant neck {NECK}: the point printed onto the floor; it snaps at about {m:.0f} N in pure "
               f"tension, but a sideways poke at the ball's centre ({TIP:.1f} above the neck) bends it: "
               f"about {50 * 3.14159 * NECK ** 3 / 32 / TIP:.2f} N breaks it. A toothpick through the lattice")
    line(LAT_GAP_MIN >= g, f"lattice {LAT_GAP_MIN} above the tallest ball (>= {g}, and its bars are bridges that sag "
                           f"~0.1-0.2)")
    line(LAT_OPEN <= STOP_MAX, f"lattice openings {LAT_OPEN} <= {STOP_MAX}: no ball gets out")
    line(LAT_BAR >= 1.2, f"lattice bars {LAT_BAR} wide (3 beads)")
    line(XY_GAP >= g, f"balls printed {XY_GAP} from each other and from every wall and peg (>= {g})")
    out.append(f"every gap in the board is either a stop (<= {STOP_MAX}) or a pass (>= {PASS_MIN}); none between, "
               f"where a ball could wedge. The fit check measures them on the model")
    out.append("PASS" if not fails else "FAIL: " + "; ".join(fails))
    text = "\n".join(out)
    print(text)
    (Path(__file__).resolve().parent / "checks" / "plinko_budget.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
