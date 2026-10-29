#!/usr/bin/env python3
"""Studio renders of the Shop Calendar, assembled, from the exported parts.

    python3 render_calendar.py [--views] [--back]

Each print is moved to where it sits, the drums turned to THU 29 OCT, and
every colour part goes in as its own filament. Design-review renders from the
real meshes, not photos.
"""
import argparse, re, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
R = HERE.parents[2] / "tools" / "blender_render.py"

BRICK, MINT, ROOF, CREAM, NAVY = "0.72,0.36,0.28", "0.66,0.86,0.78", "0.35,0.37,0.40", "0.96,0.95,0.92", "0.17,0.23,0.33"
NAMES = ["day", "tens", "ones", "month"]
TURN = [3, 2, 9, 9]           # THU, 2, 9, OCT

ap = argparse.ArgumentParser()
ap.add_argument("--views", action="store_true")
ap.add_argument("--back", action="store_true", help="from behind, where the drums are turned")
a = ap.parse_args()

n = [float(x) for x in re.findall(r"-?[\d.]+", (HERE / "logs" / "dims.echo").read_text().split("DIMS =")[1])]
za, y_fac, z_roof, in_w, wall = n[:5]
drums = [n[6 + 4 * i: 10 + 4 * i] for i in range(4)]


def rot(axis, deg):
    return trimesh.transformations.rotation_matrix(np.radians(deg), axis)


def tr(v):
    return trimesh.transformations.translation_matrix(v)


def load(name, *mats):
    m = trimesh.load(HERE / "parts" / f"{name}.stl", force="mesh")
    for M in mats:
        m.apply_transform(M)
    return m


parts = [(load("base"), BRICK),
         (load("facade", rot([1, 0, 0], 90), tr([0, y_fac, 0])), MINT),
         (load("roof", tr([0, 0, z_roof])), ROOF),
         (load("rod", rot([0, 1, 0], 90), tr([-wall, 0, za])), CREAM)]
for i, nm in enumerate(NAMES):
    x0, ln, side, faces = drums[i]
    turn = TURN[i] * 360 / faces
    place = [rot([0, 0, 1], -turn)] + ([rot([0, 1, 0], 90), tr([x0, 0, za])] if side < 0
                                       else [rot([0, 1, 0], -90), tr([x0 + ln, 0, za])])
    parts += [(load(f"drum_{nm}", *place), CREAM), (load(f"drum_{nm}_text", *place), NAVY)]

with tempfile.TemporaryDirectory() as tmp:
    args = []
    for k, (m, rgb) in enumerate(parts):
        out = Path(tmp) / f"p{k}.stl"
        m.export(out)
        args += ["--part", f"{out}:{rgb}"]
    stem = HERE / "images" / ("calendar_back" if a.back else "calendar")
    cmd = [sys.executable, str(R), *args, "--resolution", "1400", "--timeout", "1800",
           "-o", str(stem) + ("" if a.views else ".png")]
    if a.views:
        cmd += ["--views"]
    else:
        cmd += ["--azimuth", "150" if a.back else "-30", "--elevation", "22"]
    subprocess.run(cmd, check=True)
