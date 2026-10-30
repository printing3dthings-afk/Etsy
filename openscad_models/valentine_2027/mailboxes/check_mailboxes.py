#!/usr/bin/env python3
"""The two Valentine mailboxes' fits (2026-10-30), on the exported prints:

- the lid (letter) and the fur cap (monster) at rest touch the body and do not
  overlap it; 0.1 mm lower they would, so they rest on the rim; lifted 0.2 and
  slid 0.15 they touch nothing, so they come off without binding
- a kids' valentine in its envelope (the common 2.75 x 4 in, 70 x 102 mm, here
  3 mm thick for a card with a sticker or a flat lollipop) goes in: pushed
  through the slot or the mouth along its whole path it meets no plastic
- what each holds

    python3 check_mailboxes.py
"""
import re, sys
from pathlib import Path

import manifold3d as mf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from part_mesh import load  # noqa: E402

fails = []


def num(src, name):
    return float(re.search(rf"(?<![\w.]){name}\s*=\s*([-\d.]+)\s*;", src).group(1))


def box(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def ov(a, b):
    return (a ^ b).volume()


def on_bed(name, m):
    z0 = m.bounding_box()[2]
    print(f"  {name}: lowest point z {z0:+.3f}")
    if abs(z0) > 0.01:
        fails.append(f"{name} reaches below the bed (z {z0:.2f})")


def cap_fit(name, body, cap):
    rest, low = ov(body, cap), ov(body, cap.translate([0, 0, -0.1]))
    lift = max(ov(body, cap.translate([dx, dy, 0.2])) for dx, dy in [(0.15, 0), (-0.15, 0), (0, 0.15), (0, -0.15)])
    print(f"  {name} at rest {rest:.3f} mm3; 0.1 lower {low:.1f}; lifted 0.2 and slid 0.15 {lift:.3f}")
    if rest > 0.05:
        fails.append(f"{name} overlaps the body")
    if low < 1:
        fails.append(f"{name} does not rest on the rim")
    if lift > 0.05:
        fails.append(f"{name} binds")


def main():
    # the letter
    d = HERE / "love_letter"
    s = (d / "love_letter.scad").read_text()
    HB, D, WALL, FLOOR = num(s, "HB"), num(s, "D"), num(s, "WALL"), num(s, "FLOOR")
    body, lid = load(str(d / "parts/body_print.stl")), load(str(d / "parts/lid_use.stl"))
    print("Giant Love Letter")
    on_bed("body", body)
    on_bed("lid, as printed", load(str(d / "parts/lid.stl")))
    cap_fit("lid", body, lid)
    # the envelope, upright (102 across, 3 thick), pushed down through the slot
    # from above the lid to the floor
    card = box(-51, 51, -1.5, 1.5, 0, 70)
    worst = max(ov(lid, card.translate([0, 0, z])) + ov(body, card.translate([0, 0, z]))
                for z in [HB + 6, HB - 10, HB - 40, FLOOR + 0.5])
    print(f"  a 102 x 70 x 3 envelope down the slot: {worst:.3f} mm3 in the way")
    if worst > 0.01:
        fails.append("the letter's slot blocks an envelope")
    inside = box(-200, 200, -200, 200, FLOOR, HB) - body
    inside = inside ^ box(-89, 89, -D / 2 + WALL - 0.1, D / 2 - WALL + 0.1, FLOOR, HB)
    print(f"  holds {inside.volume() / 1e6:.2f} L")

    # the monster
    d = HERE / "love_monster"
    s = (d / "love_monster.scad").read_text()
    HB, B, MZ, CLEAR = num(s, "HB"), num(s, "B"), num(s, "MZ"), num(s, "CLEAR")
    body, fur = load(str(d / "parts/body_print.stl")), load(str(d / "parts/fur_use.stl"))
    print("Hungry Love Monster")
    on_bed("body", body)
    on_bed("fur cap, as printed", load(str(d / "parts/fur.stl")))
    cap_fit("fur cap", body, fur)
    # the envelope lying flat (102 across, 70 deep, 3 thick), fed into the mouth
    # at the height of the straight gap's middle, from outside to fully inside
    zc = MZ + 3 + (CLEAR - 3) / 2           # corners 3 higher; the gap is CLEAR - 3 straight
    card = box(-51, 51, 0, 70, zc - 1.5, zc + 1.5)
    worst = max(ov(body, card.translate([0, y, 0])) + ov(fur, card.translate([0, y, 0]))
                for y in [-B - 80, -B - 40, -B - 10, -B + 10])
    print(f"  a 102 x 70 x 3 envelope into the mouth at z {zc:.1f}: {worst:.3f} mm3 in the way")
    if worst > 0.01:
        fails.append("the monster's mouth blocks an envelope")
    print(f"  (the straight gap through the mouth is {CLEAR - 3:.1f} mm)")

    if fails:
        print("FIT CHECK FAILED: " + "; ".join(fails))
        return 1
    print("FIT CHECK OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
