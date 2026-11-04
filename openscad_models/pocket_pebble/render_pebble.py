#!/usr/bin/env python3
"""Studio renders of the Pocket Pebble from its exported parts: shut, in three
views; open with its tongue and lip showing; and the prints as they lie on the
plate. Design-review renders, not photos.

    python3 render_pebble.py        (after ./ship.sh)
"""
import re
import subprocess
import sys
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
PARTS = HERE / "parts"
IMG = HERE / "images"
R = HERE.parents[1] / "tools" / "blender_render.py"
WHITE, LILAC, PINK = "0.96,0.95,0.92", "0.72,0.61,0.88", "0.96,0.65,0.76"
V = {k: float(v) for k, v in re.findall(r'"(\w+)", (-?[0-9.]+)', (HERE / "logs" / "base.log").read_text())}
AY, HB = V["AY"], V["HB"]
OPEN = 110
n = 0


def save(m):
    global n
    n += 1
    out = PARTS / f"_r_{n}.stl"
    m.export(out)
    return out


def render(parts, out, extra):
    args = []
    for path, rgb in parts:
        args += ["--part", f"{path}:{rgb}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out),
                    "--resolution", "1400", "--timeout", "1200", *extra], check=True)


def main():
    IMG.mkdir(exist_ok=True)
    base = PARTS / "base.stl"
    pins = PARTS / "pins_use.stl"
    # shut, its front toward the camera
    render([(base, WHITE), (PARTS / "lid_use0.stl", LILAC), (pins, PINK)], "pocket_pebble", ["--views"])
    # open: the lid turned about the hinge's axis, the front lifting
    lid = trimesh.load(PARTS / "lid_use0.stl", force="mesh")
    lid.apply_transform(trimesh.transformations.rotation_matrix(-OPEN * 3.14159265 / 180, [1, 0, 0], [0, AY, HB]))
    render([(base, WHITE), (save(lid), LILAC), (pins, PINK)], "pocket_pebble_open.png",
           ["--azimuth", "-25", "--elevation", "40"])
    # the prints
    plate = [(base, WHITE)]
    l = trimesh.load(PARTS / "lid.stl", force="mesh"); l.apply_translation([66, 0, 0]); plate.append((save(l), LILAC))
    for k in (0, 1):
        p = trimesh.load(PARTS / "pin.stl", force="mesh"); p.apply_translation([-42, -10 + 12 * k, 0]); plate.append((save(p), PINK))
    render(plate, "pocket_pebble_prints.png", ["--azimuth", "-20", "--elevation", "50"])
    for p in PARTS.glob("_r_*.stl"):
        p.unlink()


if __name__ == "__main__":
    main()
