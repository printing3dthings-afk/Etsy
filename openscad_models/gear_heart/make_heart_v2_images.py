#!/usr/bin/env python3
"""Gear Heart v2: design-review renders from the exported parts (2026-11-16).

    python3 make_heart_v2_images.py   (needs make_heart_v2.sh first; writes images/heart_v2_*.png)
"""
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
P, IMG = HERE / "parts", HERE / "images"
TOOLS = HERE.parents[1] / "tools"
PLATE, GEAR, PIN = "0.91,0.79,0.82", "0.79,0.31,0.43", "0.85,0.68,0.25"


def render(parts, out, extra):
    args = ["python3", str(TOOLS / "blender_render.py"), "-o", str(IMG / out), "--resolution", "1400"] + extra
    for path, col in parts:
        args += ["--part", f"{path}:{col}"]
    subprocess.run(args, check=True)


def scad(part, out):
    subprocess.run(["openscad", "-o", str(out), "-D", f'part="{part}"', str(HERE / "heart.scad")],
                   check=True, capture_output=True)


def main():
    IMG.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        scad("gears_posed", td / "gears.stl")
        scad("gears_only", td / "gears_only.stl")
        scad("pins", td / "pins.stl")
        assembled = [(P / "heart_plate_v2.stl", PLATE), (td / "gears.stl", GEAR), (P / "heart_pins_posed.stl", PIN)]
        render(assembled, "heart_v2.png", ["--views", "--front=-y"])          # heart_v2_front/three_quarter/top
        render([(P / "heart_plate_v2.stl", PLATE)], "heart_v2_plate.png", ["--azimuth", "-30", "--elevation", "50"])
        render([(td / "gears_only.stl", GEAR), (td / "pins.stl", PIN)], "heart_v2_gears_plate.png",
               ["--azimuth", "-30", "--elevation", "55"])
        # from underneath: the pins' heads sit in their pockets in the plate's bed face. The
        # renderer stands a part on a floor, so the plate and pins are turned over instead
        flip = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
        for name, src in (("plate_flip", P / "heart_plate_v2.stl"), ("pins_flip", P / "heart_pins_posed.stl")):
            trimesh.load(src).apply_transform(flip).export(td / f"{name}.stl")
        render([(td / "plate_flip.stl", PLATE), (td / "pins_flip.stl", PIN)], "heart_v2_underside.png",
               ["--azimuth", "-30", "--elevation", "50"])


if __name__ == "__main__":
    main()
