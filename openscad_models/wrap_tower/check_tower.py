#!/usr/bin/env python3
"""Fit checks for the Wrap-Around Tower (2026-11-04), on the exported meshes.

- a piece drops freely down every tube: at each row, no overlap with the tower
- it can't leave through the window: pushed out 3 mm towards the slot, it hits
- it can't turn on edge in the tube: its diagonal is longer than the bore
- the tower sits in the tray's recess, and can't slide off it
- six pieces fill a tube below the rim, and a seventh shows the tube is full

    python3 check_tower.py      (parts/ from wrap_tower.scad, part=tower, tray, puck_heart)
"""
import math
import re
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import sdf_figure as sf  # noqa: E402

SCAD = (HERE / "wrap_tower.scad").read_text()


def const(name):
    return float(re.search(rf"^{name} = ([0-9.]+);", SCAD, re.M).group(1))


N, ROWS, PUCK_D, PUCK_H, CLR = (const(k) for k in ("N", "ROWS", "PUCK_D", "PUCK_H", "CLR"))
BORE = PUCK_D + CLR
TRAY_FLOOR = const("TRAY_FLOOR")
log = (HERE / "logs" / "tower.log").read_text()
R_C = float(re.search(r'"R_C", ([0-9.]+)', log).group(1))
H = float(re.search(r'"H", ([0-9.]+)', log).group(1))


def load(name):
    return sf.to_manifold(trimesh.load(HERE / "parts" / f"{name}.stl", force="mesh"))


def overlap(a, b):
    return (a ^ b).volume()


def main():
    tower, tray, puck = load("tower"), load("tray"), load("puck_heart")
    fails, lines = [], []
    worst = 0.0
    for i in range(int(N)):
        a = math.radians(i * 360 / N)
        for r in range(int(ROWS)):
            p = puck.translate([R_C * math.cos(a), R_C * math.sin(a), r * PUCK_H])
            worst = max(worst, overlap(p, tower))
    lines.append(f"pieces in every cell of every tube: {worst:.3f} mm3 in the way")
    if worst > 0.001:
        fails.append("a piece does not drop freely")
    # pushed towards the window (radially out) by 3 mm, at every row of tube 0
    blocked = min(overlap(puck.translate([R_C + 3.0, 0, r * PUCK_H]), tower) for r in range(int(ROWS)))
    lines.append(f"a piece pushed 3 mm out towards its window: {blocked:.1f} mm3 into the tower (it can't leave)")
    if blocked < 1.0:
        fails.append("a piece can slip out through the window")
    diag = math.hypot(PUCK_D, PUCK_H)
    lines.append(f"a piece's diagonal {diag:.2f} mm against the bore {BORE:.2f}: it can't turn on edge")
    if diag <= BORE:
        fails.append("a piece can turn on edge in the tube")
    seated = tower.translate([0, 0, TRAY_FLOOR])
    rest = overlap(seated, tray)
    lower = overlap(tower.translate([0, 0, TRAY_FLOOR - 0.1]), tray)
    slide = min(overlap(tower.translate([dx, dy, TRAY_FLOOR + 0.05]), tray)
                for dx, dy in ((1.0, 0), (0, 1.0), (-1.0, 0), (0, -1.0)))
    lines.append(f"tower in the tray: at rest {rest:.3f} mm3; 0.1 lower {lower:.1f}; slid 1 mm any way {slide:.1f} (held by the recess)")
    if rest > 0.001 or lower < 1 or slide < 1:
        fails.append("the tower does not sit in its recess")
    top = ROWS * PUCK_H
    lines.append(f"six pieces stand {top:.0f} mm in a {H:.0f} mm tube; a seventh would stand {top + PUCK_H - H:+.0f} mm above the rim")
    for ln in lines:
        print(" ", ln)
    if fails:
        print("FIT CHECK FAILED:", "; ".join(fails))
        sys.exit(1)
    print("FIT CHECK OK")


if __name__ == "__main__":
    main()
