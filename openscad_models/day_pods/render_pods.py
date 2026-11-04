#!/usr/bin/env python3
"""Studio renders of Day Pods from its exported parts: the week on its stand
(three views), Wednesday lifted off with its lid slid half open, and the
prints as they lie on the plate. Design-review renders, not photos.

    python3 render_pods.py        (after ./ship.sh)
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
WHITE, LILAC = "0.96,0.95,0.92", "0.72,0.61,0.88"
V = {k: float(v) for k, v in re.findall(r'"(\w+)", ([0-9.]+)', (HERE / "logs" / "pod.log").read_text())}
SCAD = (HERE / "day_pods.scad").read_text()
FLOOR = float(re.search(r"\bFLOOR = ([0-9.]+);", SCAD).group(1))
IN_H = float(re.search(r"\bIN_H = ([0-9.]+);", SCAD).group(1))
BASE_T = float(re.search(r"\bBASE_T = ([0-9.]+);", SCAD).group(1))
LB, LT, PITCH = FLOOR + IN_H, 2.4, V["PITCH"]
n = 0


def placed(name, dx=0.0, dy=0.0, dz=0.0, flip=False):
    """A copy of an exported part, moved (and turned the right way up)."""
    global n
    n += 1
    m = trimesh.load(PARTS / f"{name}.stl", force="mesh")
    if flip:    # a lid is exported upside down; turn it back over its own thickness
        m.apply_transform(trimesh.transformations.reflection_matrix([0, 0, LT / 2], [0, 0, 1]))
    m.apply_translation([dx, dy, dz])
    out = PARTS / f"_r_{n}.stl"
    m.export(out)
    return out


def render(parts, out, extra):
    args = []
    for path, rgb in parts:
        args += ["--part", f"{path}:{rgb}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out),
                    "--resolution", "1400", "--timeout", "1200", *extra], check=True)


def week(lift=None):
    parts = [(PARTS / "stand.stl", WHITE)]
    for i in range(7):
        x = (i - 3) * PITCH
        if i == lift:
            parts += [(placed("pod", x, -55, 0), WHITE), (placed(f"lid_{i}", x, -55 - 12, LB, flip=True), LILAC)]
        else:
            parts += [(placed("pod", x, 0, BASE_T), WHITE), (placed(f"lid_{i}", x, 0, BASE_T + LB, flip=True), LILAC)]
    return parts


def main():
    IMG.mkdir(exist_ok=True)
    render(week(), "day_pods", ["--views"])
    render(week(lift=2), "day_pods_wednesday.png", ["--azimuth", "-25", "--elevation", "32"])
    plate = [(placed("pod", (i % 4 - 1.5) * 38, (i // 4) * 40), WHITE) for i in range(7)]
    plate += [(placed(f"lid_{k}", (k % 4 - 1.5) * 36, 90 + (k // 4) * 38), LILAC) for k in range(7)]
    render(plate, "day_pods_prints.png", ["--azimuth", "-20", "--elevation", "55"])
    for p in PARTS.glob("_r_*.stl"):
        p.unlink()


if __name__ == "__main__":
    main()
