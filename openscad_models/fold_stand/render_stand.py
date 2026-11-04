#!/usr/bin/env python3
"""Studio renders of the Fold Stand from its exported parts: standing at its
second stop with a phone (a plain dark slab) on the lip, in three views;
folded flat; and the prints as they lie on the plate. The stance is worked
out the way check_stand.py does it: the A stands on the hull edge between its
two feet. Design-review renders, not photos.

    python3 render_stand.py        (after ./ship.sh)
"""
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import ConvexHull

HERE = Path(__file__).resolve().parent
PARTS = HERE / "parts"
IMG = HERE / "images"
R = HERE.parents[1] / "tools" / "blender_render.py"
LILAC, WHITE, PINK, PHONE = "0.72,0.61,0.88", "0.96,0.95,0.92", "0.96,0.65,0.76", "0.12,0.12,0.14"
V = {k: float(v) for k, v in re.findall(r'"(\w+)", ([0-9.]+)', (HERE / "logs" / "front.log").read_text())}
AF, LF = V["AF"], V["LF"]
W, T = 76.0, 4.0
OPEN = 36.0
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


def opened(a):
    front = trimesh.load(PARTS / "front_use.stl", force="mesh")
    back = trimesh.load(PARTS / "back_use0.stl", force="mesh")
    pins = trimesh.load(PARTS / "pins_use.stl", force="mesh")
    back.apply_transform(trimesh.transformations.rotation_matrix(math.radians(a), [1, 0, 0], [0, 0, AF]))
    return front, back, pins


def stance(front, back):
    """the 4x4 that stands the A on its feet on the table, z = 0"""
    pf, pb = front.vertices[:, 1:], back.vertices[:, 1:]
    pts = np.vstack([pf, pb])
    hull = ConvexHull(pts)
    axis = np.array([0.0, AF])
    best = None
    for (i, j), eq in zip(hull.simplices, hull.equations):
        if (i < len(pf)) == (j < len(pf)):
            continue
        dist = -(eq[:2] @ axis + eq[2])
        if best is None or dist > best[0]:
            best = (dist, eq[:2], pts[i])
    _, nrm, foot = best
    ang = math.atan2(nrm[1], nrm[0]) + math.pi / 2       # turn the outward normal to -z
    M = trimesh.transformations.rotation_matrix(-ang, [1, 0, 0], [0, foot[0], foot[1]])
    return M


def main():
    IMG.mkdir(exist_ok=True)
    front, back, pins = opened(OPEN)
    # the phone: a slab on the lip, leaning on the front plate's outer face
    phone = trimesh.creation.box(extents=[72, 150, 9])
    # the phone's foot in the lip's corner, its back on the barrel, as check_stand.py has it
    lip = np.array([-LF + 8.0, T])
    to_c = np.array([0.0, AF]) - lip
    tilt = math.atan2(to_c[1], to_c[0]) + math.asin(V["RK"] / np.linalg.norm(to_c))
    phone.apply_translation([W / 2, 75, 4.5])
    phone.apply_transform(trimesh.transformations.rotation_matrix(tilt, [1, 0, 0], [0, 0, 0]))
    phone.apply_translation([0, lip[0], lip[1]])
    M = stance(front, back)
    for m in (front, back, pins, phone):
        m.apply_transform(M)
    z0 = min(m.bounds[0][2] for m in (front, back, pins))
    for m in (front, back, pins, phone):
        m.apply_translation([0, 0, -z0])
    standing = [(save(front), LILAC), (save(back), WHITE), (save(pins), PINK)]
    render(standing + [(save(phone), PHONE)], "fold_stand", ["--views"])
    render(standing, "fold_stand_side.png", ["--azimuth", "75", "--elevation", "12"])
    # folded flat: the back plate against the front's inner face
    front, back, pins = opened(0)
    z0 = min(m.bounds[0][2] for m in (front, back, pins))
    for m in (front, back, pins):
        m.apply_translation([0, 0, -z0])
    render([(save(front), LILAC), (save(back), WHITE), (save(pins), PINK)], "fold_stand_folded.png",
           ["--azimuth", "-30", "--elevation", "35"])
    # the prints
    plate = [(PARTS / "front.stl", LILAC)]
    b = trimesh.load(PARTS / "back.stl", force="mesh"); b.apply_translation([90, 0, 0]); plate.append((save(b), WHITE))
    for k in (0, 1):
        p = trimesh.load(PARTS / "pin.stl", force="mesh"); p.apply_translation([-25 - 16 * k, -20, 0]); plate.append((save(p), PINK))
    render(plate, "fold_stand_prints.png", ["--azimuth", "-20", "--elevation", "50"])
    for p in PARTS.glob("_r_*.stl"):
        p.unlink()


if __name__ == "__main__":
    main()
