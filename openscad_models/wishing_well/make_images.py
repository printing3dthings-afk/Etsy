#!/usr/bin/env python3
"""Wishing Well windlass test print: review renders from the exported parts (2026-11-15).
Design-review renders, not photos.

    python3 make_images.py   (images/windlass_plate.png, windlass_assembled.png,
                              windlass_ratchet.png, windlass_cradle.png)
"""
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMG = HERE / "images"
TOOLS = HERE.parents[1] / "tools"
WOOD, DARK, AXLE, PAWL, BASE = "0.80,0.62,0.42", "0.55,0.30,0.18", "0.62,0.42,0.26", "0.25,0.22,0.20", "0.72,0.70,0.66"

PIECES = {
    "base": "base(span);",
    "posts": ("translate([span / 2, 0, 0]) rotate([90, 0, 90]) post(0.55, HC_C, true);"
              "translate([-span / 2, 0, 0]) mirror([1, 0, 0]) rotate([90, 0, 90]) post(0.55, HC_C, false);"),
    "axle": "translate([-span / 2 - FT - 1.0 + COLLAR_G, 0, HC_C]) rotate([0, 90, 0]) rotate(90) axle(span);",
    "wheel": "translate([span / 2 + FT + WHEEL_W0, 0, HC_C]) rotate([90, 0, 90]) wheel();",
    "pawl": "translate([span / 2 + FT + WHEEL_W0 + 0.2, 0, HC_C]) rotate([90, 0, 90]) pawl();",
}


def scad(body, out):
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "m.scad"
        src.write_text(f'include <{HERE / "windlass.scad"}>\npart = "none";\nspan = SPAN_C;\n{body}\n')
        subprocess.run(["openscad", "-o", str(out), str(src)], check=True, capture_output=True)


def render(parts, out, **kw):
    cmd = ["python3", str(TOOLS / "blender_render.py"), "-o", str(out), "--resolution", "1100"]
    for path, col in parts:
        cmd += ["--part", f"{path}:{col}"]
    for k, v in kw.items():
        cmd += [f"--{k}", str(v)]
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    IMG.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for name, body in PIECES.items():
            scad(body, td / f"{name}.stl")
        scad("coupon();", td / "plate.stl")
        cols = {"base": BASE, "posts": WOOD, "axle": AXLE, "wheel": DARK, "pawl": PAWL}
        allp = [(td / f"{n}.stl", cols[n]) for n in PIECES]
        render([(td / "plate.stl", WOOD)], IMG / "windlass_plate.png", azimuth=20, elevation=55)
        render(allp, IMG / "windlass_assembled.png", azimuth=50, elevation=22)
        # from outside the crank side, along -X: the view the guide's "clockwise" means
        render(allp, IMG / "windlass_ratchet.png", azimuth=90, elevation=8)
        scad("post(0.55, HC_C, false);", td / "post.stl")
        render([(td / "post.stl", WOOD)], IMG / "windlass_cradle.png", azimuth=0, elevation=89)
    print("images ->", IMG)


if __name__ == "__main__":
    main()
