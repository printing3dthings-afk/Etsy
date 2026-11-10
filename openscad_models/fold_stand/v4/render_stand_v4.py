#!/usr/bin/env python3
"""Studio renders of the Fold Stand v4 from its exported parts, posed as check_stand_v4.py
poses them: standing at 65 deg with a phone (a plain dark slab), three views; side views
at the steepest and shallowest notch; folded flat; going on (tipped to 145 over the lugs);
the two prints as they lie on the plate; the hinge test print. Design-review renders,
not photos.

    python3 render_stand_v4.py
"""
import subprocess
import sys
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_stand_v4 as c  # noqa: E402

PARTS = HERE / "parts"
IMG = HERE / "images"
TMP = HERE / "logs" / "render"
R = HERE.parents[2] / "tools" / "blender_render.py"
LILAC, WHITE, PINK, PHONE = "0.72,0.61,0.88", "0.96,0.95,0.92", "0.96,0.62,0.74", "0.12,0.12,0.14"
n = 0


def save(m):
    global n
    n += 1
    TMP.mkdir(parents=True, exist_ok=True)
    out = TMP / f"_r_{n}.stl"
    m.export(out)
    return out


def render(parts, out, extra):
    args = []
    for path, rgb in parts:
        args += ["--part", f"{path}:{rgb}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out), "--resolution", "1400",
                    "--timeout", "1200", *extra], check=True)


def posed(th, phone=False, lift=0.0):
    T = c.tr(0, 0, lift) @ c.plate_T(th)
    out = [(PARTS / "base.stl", WHITE), (save(c.load("plate_only").apply_transform(T)), LILAC)]
    if th in c.ANGLES:
        fy = c.NOTCH_Y[c.ANGLES.index(th)]
        out.append((save(c.load("prop_only").apply_transform(T @ c.prop_in_plate(c.rho(th, fy)))), PINK))
    else:
        out.append((save(c.load("prop_only").apply_transform(T)), PINK))
    if phone:
        ph = trimesh.creation.box(extents=[72, 160, 10.5])
        ph.apply_translation([0, 10 + 80, 8 + 5.25])
        out.append((save(ph.apply_transform(c.plate_T(th))), PHONE))
    return out


def main():
    IMG.mkdir(exist_ok=True)
    render(posed(65, phone=True), "fold_stand_v4", ["--views"])
    render(posed(65), "fold_stand_v4_back.png", ["--azimuth", "150", "--elevation", "28"])
    render(posed(80), "fold_stand_v4_side_80.png", ["--azimuth", "90", "--elevation", "4"])
    render(posed(55), "fold_stand_v4_side_55.png", ["--azimuth", "90", "--elevation", "4"])
    render(posed(0), "fold_stand_v4_folded.png", ["--azimuth", "-30", "--elevation", "35"])
    render(posed(c.PASS, lift=10), "fold_stand_v4_going_on.png", ["--azimuth", "60", "--elevation", "20"])
    plate = c.load("plate")
    plate.apply_translation([95, 0, 0])
    render([(PARTS / "base.stl", WHITE), (save(plate), LILAC)], "fold_stand_v4_prints.png", ["--azimuth", "-20", "--elevation", "55"])
    cb, cp = c.load("coupon_base"), c.load("coupon_plate")
    cp.apply_translation([50, 0, 0])
    render([(save(cb), WHITE), (save(cp), LILAC)], "fold_stand_v4_hinge_test.png", ["--azimuth", "-20", "--elevation", "50"])
    for f in TMP.glob("_r_*.stl"):
        f.unlink()


if __name__ == "__main__":
    main()
