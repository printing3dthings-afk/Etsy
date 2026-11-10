#!/usr/bin/env python3
"""Studio renders of the Bayonet Jar v3 from its exported parts, posed as build_sizes.py
poses them: the size range, the lid going on, and closed. Design-review renders, not
photos.

    python3 render_v3.py
"""
import math
import subprocess
import sys
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_sizes as b  # noqa: E402

PARTS = HERE / "parts"
IMG = HERE / "images"
TMP = HERE / "logs" / "render"
R = HERE.parents[2] / "tools" / "blender_render.py"
GOLD, LID = "0.93,0.72,0.22", "0.96,0.80,0.36"
n = 0


def save(m):
    global n
    n += 1
    TMP.mkdir(parents=True, exist_ok=True)
    p = TMP / f"_r_{n}.stl"
    m.export(p)
    return p


def render(parts, out, az, el, res=1400):
    args = []
    for p, col in parts:
        args += ["--part", f"{p}:{col}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out), "--azimuth", str(az), "--elevation", str(el),
                    "--resolution", str(res), "--timeout", "1200"], check=True)


def lid(d, h, turn=0.0, dz=0.0, dx=0.0):
    t = trimesh.transformations.rotation_matrix(math.radians(turn), [0, 0, 1])
    t[:3, 3] = [dx, 0, dz]
    return trimesh.load(PARTS / f"lidA_D{d}_H{h}.stl").apply_transform(t)


def base(d, h, dx=0.0):
    return trimesh.load(PARTS / f"base_D{d}_H{h}.stl").apply_translation([dx, 0, 0])


def main():
    IMG.mkdir(exist_ok=True)
    entry = -b.TWIST * b.LOCK
    # every diameter at H45, closed, side by side; then every height of D50
    parts, x = [], 0.0
    for d in b.DIAMETERS:
        x += d / 2 + 3
        parts += [(save(base(d, 45, x)), GOLD), (save(lid(d, 45, dx=x)), LID)]
        x += d / 2 + 3
    render(parts, "bayonet_jar_v3_diameters.png", 0, 12)
    parts, x = [], 0.0
    for h in b.HEIGHTS:
        x += 31
        parts += [(save(base(50, h, x)), GOLD), (save(lid(50, h, dx=x)), LID)]
        x += 31
    render(parts, "bayonet_jar_v3_heights.png", 0, 12)
    # D50 H45: going on (lined up at the entry, lifted), half way round, closed
    render([(save(base(50, 45)), GOLD), (save(lid(50, 45, entry, 14)), LID)], "bayonet_jar_v3_lined_up.png", -20, 18)
    render([(save(base(50, 45)), GOLD), (save(lid(50, 45)), LID)], "bayonet_jar_v3_closed.png", -20, 18)
    render([(save(base(50, 45)), GOLD), (save(lid(50, 45)), LID)], "bayonet_jar_v3_top.png", 0, 89)
    for f in TMP.glob("_r_*.stl"):
        f.unlink()


if __name__ == "__main__":
    main()
