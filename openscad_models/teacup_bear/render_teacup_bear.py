#!/usr/bin/env python3
"""Studio renders of the Teacup Bear from her real exported colour parts.
Design-review renders, not photos.  python3 render_teacup_bear.py"""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE.parents[1] / "tools" / "blender_render.py"
PARTS = [("cream", "0.96,0.95,0.92"), ("tan", "0.78,0.56,0.37"),
         ("brown", "0.29,0.18,0.13"), ("pink", "0.96,0.65,0.76")]


def render(out, extra):
    args = []
    for name, rgb in PARTS:
        args += ["--part", f"{HERE / 'parts' / f'teacup_bear_{name}.stl'}:{rgb}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(HERE / "images" / out),
                    "--resolution", "1400", "--timeout", "1200", *extra], check=True)


render("teacup_bear", ["--views"])
render("teacup_bear_back.png", ["--azimuth", "155", "--elevation", "18"])
render("teacup_bear_handle.png", ["--azimuth", "60", "--elevation", "12"])
