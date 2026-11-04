#!/usr/bin/env python3
"""Studio renders of the Wrap-Around Tower from its exported parts: the tower
on its tray with a game in progress, and the pieces. Design-review renders,
not photos.  python3 render_tower.py"""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE.parents[1] / "tools" / "blender_render.py"
CREAM, LILAC_TRAY, PINK, LILAC = "0.96,0.95,0.92", "0.91,0.83,0.94", "0.96,0.65,0.76", "0.72,0.61,0.88"
GAME = [("tray", LILAC_TRAY), ("tower_use", CREAM), ("game_pink", PINK), ("game_lilac", LILAC)]


def render(parts, out, extra):
    args = []
    for name, rgb in parts:
        args += ["--part", f"{HERE / 'parts' / (name + '.stl')}:{rgb}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(HERE / "images" / out),
                    "--resolution", "1400", "--timeout", "1200", *extra], check=True)


render(GAME, "wrap_tower", ["--views"])
render([("puck_heart", PINK), ], "piece_heart.png", ["--azimuth", "-30", "--elevation", "50"])
render([("puck_star", LILAC), ], "piece_star.png", ["--azimuth", "-30", "--elevation", "50"])
