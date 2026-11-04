#!/usr/bin/env python3
"""Studio renders of the Kawaii Cow from her real exported colour parts.
Design-review renders, not photos.  python3 render_cow.py"""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE.parents[1] / "tools" / "blender_render.py"
PARTS = [("cow_white", "0.96,0.95,0.92"), ("cow_black", "0.17,0.14,0.2"),
         ("cow_pink", "0.96,0.65,0.76"), ("cow_red", "0.84,0.15,0.24")]


def render(out, extra):
    args = []
    for name, rgb in PARTS:
        args += ["--part", f"{HERE / 'parts' / (name + '.stl')}:{rgb}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(HERE / "images" / out),
                    "--resolution", "1400", "--timeout", "1200", *extra], check=True)


render("cow", ["--views"])
render("cow_back.png", ["--azimuth", "155", "--elevation", "18"])
render("cow_side.png", ["--azimuth", "90", "--elevation", "10"])
