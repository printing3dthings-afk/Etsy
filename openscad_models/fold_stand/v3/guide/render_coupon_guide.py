#!/usr/bin/env python3
"""Renders for the Fold Stand v3 test-print guide (2026-11-10), from the exported
coupon parts, posed the way check_stand_v3.py poses the full stand (the coupon has
the same joints, narrower and shorter). Design-review renders, not photos; the parts
are shown in three colours so they read apart, whatever colour Scott printed.

    python3 render_coupon_guide.py && python3 build_coupon_guide.py
"""
import math
import subprocess
import sys
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
sys.path.insert(0, str(V3))
from check_stand_v3 import ANGLES, NOTCH_Y, plate_T, prop_T  # noqa: E402

PARTS = V3 / "parts"
IMG = HERE / "images"
TMP = V3 / "logs" / "guide"
R = V3.parents[2] / "tools" / "blender_render.py"
BASE, PLATE, PROP, PHONE = "0.93,0.92,0.88", "0.72,0.61,0.88", "0.96,0.62,0.74", "0.13,0.13,0.15"
n = 0


def save(m):
    global n
    n += 1
    TMP.mkdir(parents=True, exist_ok=True)
    out = TMP / f"_g_{n}.stl"
    m.export(out)
    return out


def render(parts, out, az, el, res=1000):
    args = []
    for path, rgb in parts:
        args += ["--part", f"{path}:{rgb}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out), "--azimuth", str(az),
                    "--elevation", str(el), "--resolution", str(res), "--timeout", "900"], check=True)


def load(k):
    return trimesh.load(PARTS / f"{k}.stl", force="mesh")


def posed(th, plate=True, prop=True, phone=False):
    out = [(PARTS / "coupon_base.stl", BASE)]
    if plate:
        out.append((save(load("coupon_plate").apply_transform(plate_T(th))), PLATE))
    if prop:
        fy = NOTCH_Y[ANGLES.index(th)]
        out.append((save(load("prop").apply_transform(prop_T(th, fy))), PROP))
    if phone:
        ph = trimesh.creation.box(extents=[72, 160, 9])
        ph.apply_translation([0, 10 + 80, 5 + 4.5])
        out.append((save(ph.apply_transform(plate_T(th))), PHONE))
    return out


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    # 1. the three parts, the plate turned over so its pocket shows
    pl = load("coupon_plate")
    pl.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [0, 1, 0]))
    pl.apply_translation([45, 0, -pl.bounds[0][2]])
    pr = load("prop")
    pr.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 0, 1]))
    pr.apply_translation([-30 - pr.bounds[0][0], 10 - pr.bounds[0][1], 0])
    render([(PARTS / "coupon_base.stl", BASE), (save(pl), PLATE), (save(pr), PROP)], "parts.png", -25, 50)
    # 2. the plate dropped into the groove, no prop yet
    render(posed(80, prop=False), "step1_plate.png", 35, 18)
    # 3. the prop in: thin end in the pocket, thick end in a notch, seen from behind
    render(posed(70), "step2_prop.png", 150, 22)
    # 4. the phone on the shelf
    render(posed(65, phone=True), "step3_phone.png", 30, 15)
    # 5. the six notches, side on
    for th in ANGLES:
        render(posed(th), f"angle_{th:.0f}.png", 90, 3, res=700)
    for f in TMP.glob("_g_*.stl"):
        f.unlink()


if __name__ == "__main__":
    main()
