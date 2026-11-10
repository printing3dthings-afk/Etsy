#!/usr/bin/env python3
"""Studio renders of the Fold Stand v3 (notched easel) from its exported parts, posed the
way check_stand_v3.py poses them: standing at 65 deg with a phone (a plain dark slab) on
the shelf in three views; side views at the steepest and the shallowest notch; the
prints as they lie on the plate; the joint-test coupon. Design-review renders, not photos.

    python3 render_stand_v3.py        (after ./ship_v3.sh)
"""
import subprocess
import sys
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_stand_v3 import ANGLES, NOTCH_Y, plate_T, prop_T  # noqa: E402

PARTS = HERE / "parts"
IMG = HERE / "images"
R = HERE.parents[2] / "tools" / "blender_render.py"
LILAC, WHITE, PHONE = "0.72,0.61,0.88", "0.96,0.95,0.92", "0.12,0.12,0.14"
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


def load(k):
    return trimesh.load(PARTS / f"{k}.stl", force="mesh")


def standing(th, phone=True):
    fy = NOTCH_Y[ANGLES.index(th)]
    plate = load("plate").apply_transform(plate_T(th))
    prop = load("prop").apply_transform(prop_T(th, fy))
    out = [(PARTS / "base.stl", WHITE), (save(plate), LILAC), (save(prop), WHITE)]
    if phone:
        # a 72 x 160 x 10.5 slab: its bottom edge on the shelf, its back on the front face
        ph = trimesh.creation.box(extents=[72, 160, 10.5])
        ph.apply_translation([0, 10 + 80, 5 + 5.25])
        out.append((save(ph.apply_transform(plate_T(th))), PHONE))
    return out


def main():
    IMG.mkdir(exist_ok=True)
    render(standing(65), "fold_stand_v3", ["--views"])
    render(standing(80, phone=False), "fold_stand_v3_side_80.png", ["--azimuth", "90", "--elevation", "5"])
    render(standing(55, phone=False), "fold_stand_v3_side_55.png", ["--azimuth", "90", "--elevation", "5"])
    render(standing(65, phone=False), "fold_stand_v3_back.png", ["--azimuth", "150", "--elevation", "30"])
    prints = [(PARTS / "base.stl", WHITE)]
    p = load("plate"); p.apply_translation([90, 0, 0]); prints.append((save(p), LILAC))
    q = load("prop"); q.apply_translation([-15, -20, 0]); q.apply_transform(trimesh.transformations.rotation_matrix(1.5708, [0, 0, 1], [0, 0, 0]))
    q.apply_translation([-55, 0, 0]); prints.append((save(q), WHITE))
    render(prints, "fold_stand_v3_prints.png", ["--azimuth", "-20", "--elevation", "50"])
    cb, cp = load("coupon_base"), load("coupon_plate")
    cp.apply_translation([50, 0, 0])
    q = load("prop"); q.apply_transform(trimesh.transformations.rotation_matrix(1.5708, [0, 0, 1], [0, 0, 0])); q.apply_translation([-35, 0, 0])
    render([(save(cb), WHITE), (save(cp), LILAC), (save(q), WHITE)], "fold_stand_v3_coupon.png",
           ["--azimuth", "-20", "--elevation", "50"])
    for f in PARTS.glob("_r_*.stl"):
        f.unlink()


if __name__ == "__main__":
    main()
