#!/usr/bin/env python3
"""Renders for the Fold Stand's how-to guide (2026-11-05).

Scott, with a photo of his first print: "Can you make instruction pdf with
visuals on how to use the phone stand". Every picture is the real exported
parts, posed the way render_stand.py and check_stand.py pose them: the back
plate turned about the hinge axis, the A stood on its two feet, a plain slab
for a phone with its foot in the lip and its back on the barrel.

    python3 render_guide.py        (after ../ship.sh)

Writes guide/images/*.png, one Blender render at a time.
"""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
STAND = HERE.parent
sys.path.insert(0, str(STAND))
import render_stand as rs  # noqa: E402

PARTS = STAND / "parts"
TMP = STAND / "logs" / "guide"
OUT = HERE / "images"
R = STAND.parents[1] / "tools" / "blender_render.py"
LILAC, WHITE, PINK, PHONE, CABLE = rs.LILAC, rs.WHITE, rs.PINK, rs.PHONE, "0.30,0.30,0.33"
AF, LF, W, T = rs.AF, rs.LF, rs.W, rs.T
STOPS = [24, 36, 48, 60, 72]          # fold_stand.scad's STOPS, after the folded click
RX = trimesh.transformations.rotation_matrix


def render(name, parts, az, el, res=1200, lens=None):
    d = TMP / name
    d.mkdir(parents=True, exist_ok=True)
    args = []
    for k, (m, rgb) in enumerate(parts):
        p = d / f"{k}.stl"
        m.export(p)
        args += ["--part", f"{p}:{rgb}"]
    cmd = [sys.executable, str(R), *args, "-o", str(OUT / f"{name}.png"), "--azimuth", str(az),
           "--elevation", str(el), "--resolution", str(res), "--timeout", "1200"]
    if lens:
        cmd += ["--lens", str(lens)]
    subprocess.run(cmd, check=True)


def pins_apart():
    """the two pins, each as it goes in"""
    return trimesh.load(PARTS / "pins_use.stl", force="mesh").split()


def phone_and_cable():
    """In the front plate's frame: the phone (foot in the lip's corner, back on
    the barrel, as render_stand.py has it) and a charging lead through the slot."""
    phone = trimesh.creation.box(extents=[72, 150, 9])
    lip = np.array([-LF + 8.0, T])
    to_c = np.array([0.0, AF]) - lip
    tilt = math.atan2(to_c[1], to_c[0]) + math.asin(rs.V["RK"] / np.linalg.norm(to_c))
    phone.apply_translation([W / 2, 75, 4.5])
    phone.apply_transform(RX(tilt, [1, 0, 0], [0, 0, 0]))
    phone.apply_translation([0, lip[0], lip[1]])
    # the lead leaves the phone's bottom edge straight down its long axis,
    # through the 14 mm slot in the lip, then drops to the table
    ax = np.array([0.0, math.cos(tilt), math.sin(tilt)])
    up = np.array([0.0, -math.sin(tilt), math.cos(tilt)])
    foot = np.array([W / 2, lip[0], lip[1]]) + up * 4.5
    plug = trimesh.creation.box(extents=[10, 14, 5])
    plug.apply_translation([0, -7, 0])
    plug.apply_transform(RX(tilt, [1, 0, 0]))
    plug.apply_translation(foot)
    p0 = foot - ax * 14
    p1 = p0 - ax * 30
    lead = trimesh.creation.cylinder(radius=1.6, segment=[p0, p1], sections=24)
    return phone, trimesh.util.concatenate([plug, lead])


def standing(a, with_phone=True):
    front, back, pins = rs.opened(a)
    extra = list(phone_and_cable()) if with_phone else []
    M = rs.stance(front, back)
    for m in (front, back, pins, *extra):
        m.apply_transform(M)
    z0 = min(m.bounds[0][2] for m in (front, back, pins))
    for m in (front, back, pins, *extra):
        m.apply_translation([0, 0, -z0])
    parts = [(front, LILAC), (back, WHITE), (pins, PINK)]
    if with_phone:
        phone, lead = extra
        # the lead runs on to the table: keep the part above it
        lead = lead.slice_plane([0, 0, 0.5], [0, 0, 1], cap=True)
        parts += [(phone, PHONE), (lead, CABLE)]
    return parts


def end_of(m, x1):
    """the part cut off at x = x1, for a close-up of the hinge's end"""
    return m.slice_plane([x1, 0, 0], [-1, 0, 0], cap=True)


def scenes():
    s = {}
    # 1. what's in the bag: the prints laid out flat
    front = trimesh.load(PARTS / "front.stl", force="mesh")
    back = trimesh.load(PARTS / "back.stl", force="mesh")
    back.apply_translation([92, 0, 0])
    lay = []
    for k, p in enumerate(pins_apart()):
        p = p.copy()
        p.apply_translation(-p.bounds[0])
        p.apply_translation([-56, -62 + 22 * k, 0])
        lay.append((p, PINK))
    s["parts"] = ([(front, LILAC), (back, WHITE), *lay], 0, 58, 1400)
    # 2. fold together: the back plate below the front, its barrel under the gap
    front, back, _ = rs.opened(0)
    lifted = back.copy()
    lifted.apply_translation([0, 0, -26])
    s["fold_apart"] = ([(front, LILAC), (lifted, WHITE)], -35, 30, 1200)
    s["fold_together"] = ([(front, LILAC), (back, WHITE)], -35, 30, 1200)
    # 3. a pin into the end of the hinge: close-ups of the x = 0 end
    p0, p1 = pins_apart()
    if p0.bounds[0][0] > p1.bounds[0][0]:
        p0 = p1
    out = p0.copy()
    out.apply_translation([-26, 0, 0])
    close = [(end_of(front, 30), LILAC), (end_of(back, 30), WHITE)]
    s["pin_apart"] = (close + [(out, PINK)], -62, 24, 1200)
    s["pin_together"] = (close + [(end_of(p0, 30), PINK)], -62, 24, 1200)
    # 4. the five stops, side on, and one hero
    # all five side by side in one scene, so they share one scale
    row = []
    for k, a in enumerate(STOPS):
        for m, rgb in standing(a):
            m = m.copy()
            m.apply_translation([0, 200 * k, 0])
            row.append((m, rgb))
    s["stops"] = (row, 90, 2, 1800)
    s["hero"] = (standing(36), -35, 16, 1400)
    # 5. folded for the bag
    front, back, pins = rs.opened(0)
    s["folded"] = ([(front, LILAC), (back, WHITE), (pins, PINK)], -30, 35, 1200)
    return s


def main():
    OUT.mkdir(exist_ok=True)
    only = set(sys.argv[1:])
    for name, (parts, az, el, res) in scenes().items():
        if only and name not in only:
            continue
        render(name, parts, az, el, res)


if __name__ == "__main__":
    main()
