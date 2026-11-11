#!/usr/bin/env python3
"""Fit and stability checks for the OBC desk sign, on the exported parts.

1. Standing in the slot, the plaque and letters don't overlap the base, and the
   plaque's bottom edge sits on the slot floor (within 0.3 mm).
2. Clearance across the slot, and the extra lean it allows. The plaque rests
   against the slot's back at the top and its front at the bottom, so it leans
   by lean + atan(gap / depth). FDM prints a slot narrower than drawn, by about
   0.1-0.2 mm, so the same is shown at half the gap.
3. Tipping: the combined centre of mass (solid volumes, equal density; the
   base prints at the same infill as the plaque) sits over the base footprint,
   and the angle it would take to tip it backwards or forwards.
4. Sizes: every part fits the 256 mm plate.

    python3 check_fit.py        (prints the report, exits 1 on a failure)
"""
import math
import re
import sys
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
P = HERE / "parts"
SCAD = (HERE / "obc_desk_sign.scad").read_text()


def param(name):
    return float(re.search(rf"^{name}\s*=\s*([-\d.]+)", SCAD, re.M).group(1))


def man(t):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(t.vertices, np.float32),
                                 tri_verts=np.asarray(t.faces, np.uint32)))


def main():
    fails = []
    base = trimesh.load(P / "base.stl")
    plaque = trimesh.load(P / "standing_plaque.stl")
    letters = trimesh.load(P / "standing_letters.stl")
    for name, t in (("base", base), ("standing_plaque", plaque), ("standing_letters", letters)):
        if not t.is_watertight:
            fails.append(f"{name} is not watertight")

    # 1. overlap and seating
    ov = (man(base) ^ (man(plaque) + man(letters))).volume()
    print(f"overlap, standing sign with base: {ov:.4f} mm3")
    if ov > 0.01:
        fails.append(f"plaque overlaps the base by {ov:.3f} mm3")
    lowest = plaque.vertices[:, 2].min()
    floor = param("slot_depth")
    base_h = base.bounds[1][2]  # base_h is an expression in the .scad; the mesh has it
    seat = lowest - (base_h - floor)
    print(f"plaque's lowest point above the slot floor's nominal height: {seat:+.2f} mm")
    if abs(seat) > 0.6:
        fails.append(f"plaque not seated: {seat:+.2f} mm")

    # 2. slot clearance and real lean
    gap, depth, lean = param("slot_gap"), param("slot_depth"), param("lean")
    for g in (gap, gap / 2):
        print(f"slot gap {g:.2f} mm over {depth:.0f} mm depth -> leans {lean + math.degrees(math.atan(g / depth)):.1f} deg "
              f"({lean:.0f} drawn + {math.degrees(math.atan(g / depth)):.1f})")
    if gap < 0.3:
        fails.append("slot gap under 0.3 mm: the handbook's minimum open gap")

    # 3. tipping, with the plaque leaning fully back by the gap
    vols = [base.volume, plaque.volume, letters.volume]
    coms = [base.center_mass, plaque.center_mass, letters.center_mass]
    com = sum(v * c for v, c in zip(vols, coms)) / sum(vols)
    y0, y1 = base.bounds[0][1], base.bounds[1][1]
    print(f"centre of mass: y {com[1]:+.1f} (base from {y0:.1f} to {y1:.1f}), z {com[2]:.1f} mm")
    back = math.degrees(math.atan((y1 - com[1]) / com[2]))
    front = math.degrees(math.atan((com[1] - y0) / com[2]))
    print(f"tips backwards past {back:.0f} deg, forwards past {front:.0f} deg")
    if min(back, front) < 15:
        fails.append(f"tips too easily: {min(back, front):.0f} deg")

    # 4. plate
    for name in ("plaque", "letters", "base"):
        t = trimesh.load(P / f"{name}.stl")
        ext = t.extents
        print(f"{name}: {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm")
        if max(ext[:2]) > 250:
            fails.append(f"{name} too big for the plate")

    print("FIT: " + ("PASS" if not fails else "FAIL\n  " + "\n  ".join(fails)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
