#!/usr/bin/env python3
"""Pocket Top UFO: design-review renders from the exported parts (2026-11-15).

One colour is the product the brief's budget is for (one plate, 9 min 29 s). The two-colour
picture is the option of printing each part in its own colour, on two plates (11 min 9 s).

    python3 make_ufo_images.py   (needs make_ufo.sh run first; writes images/ufo_*.png)
"""
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
P, IMG = HERE / "parts", HERE / "images"
TOOLS = HERE.parents[1] / "tools"
MINT, PINK = "0.42,0.76,0.70", "0.93,0.58,0.72"


def run(args):
    subprocess.run(["python3"] + [str(a) for a in args], check=True)


def render(parts, out, extra):
    args = [TOOLS / "blender_render.py", "-o", IMG / out, "--resolution", "1400"] + extra
    for path, col in parts:
        args += ["--part", f"{path}:{col}"]
    run(args)


def main():
    IMG.mkdir(exist_ok=True)
    one = [(P / "ufo_saucer.stl", MINT), (P / "ufo_stem_in_use.stl", MINT)]
    render(one, "ufo.png", ["--views", "--front=-y"])                        # ufo_front/three_quarter/top
    render([(P / "ufo_saucer.stl", MINT), (P / "ufo_stem_exploded.stl", MINT)], "ufo_exploded.png",
           ["--azimuth", "-70", "--elevation", "18"])
    subprocess.run(["openscad", "-o", str(P / "ufo_plate.stl"), "-D", 'part="plate"', str(HERE / "ufo_top.scad")],
                   check=True, capture_output=True)
    render([(P / "ufo_plate.stl", MINT)], "ufo_plate.png", ["--azimuth", "-60", "--elevation", "45"])
    render([(P / "ufo_saucer.stl", MINT), (P / "ufo_stem_in_use.stl", PINK)], "ufo_two_colour.png",
           ["--azimuth", "-65", "--elevation", "22"])
    # as printed: rendered from the toolpath of print_fidelity's slice of the plate (the slice
    # the checks ran on; as_printed reads plain G-code, not Bambu's .gcode.3mf)
    with tempfile.TemporaryDirectory() as td:
        run([TOOLS / "print_fidelity.py", P / "ufo_plate.stl", "--keep", td])
        run([TOOLS / "as_printed.py", Path(td) / "fidelity.gcode", "-o", IMG / "ufo_as_printed.png",
             "--colour", "#6CC2B3"])


if __name__ == "__main__":
    main()
