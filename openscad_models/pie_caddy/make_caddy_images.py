#!/usr/bin/env python3
"""Pie Drum Caddy: review renders from the exported parts (2026-11-15). Renders, not photos.

    python3 make_caddy_images.py   (images/caddy_*.png)
"""
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[1] / "tools"
V = {k: float(v) for k, v in re.findall(r"^(\w+) = ([0-9.]+);", (HERE / "pie_caddy.scad").read_text(), re.M)}
DRUM, BASE, BB = "0.91,0.72,0.54", "0.42,0.29,0.23", "0.93,0.80,0.25"


def render(parts, out, *extra):
    cmd = ["python3", str(TOOLS / "blender_render.py"), "-o", str(out), "--resolution", "1100", *extra]
    for p, c in parts:
        cmd += ["--part", f"{p}:{c}"]
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    img = HERE / "images"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        z = V["BASE_T"] + V["BALL"]
        base = trimesh.load(HERE / "parts/pie_caddy_base.stl")
        drum = trimesh.load(HERE / "parts/pie_caddy_drum.stl")
        balls = trimesh.util.concatenate([trimesh.creation.icosphere(subdivisions=2, radius=V["BALL"] / 2).apply_translation(
            [V["RING_R"] * np.cos(a), V["RING_R"] * np.sin(a), V["BASE_T"] + V["BALL"] / 2])
            for a in np.linspace(0, 2 * np.pi, int(V["N_BALLS"]), endpoint=False)])
        base.export(td / "base.stl"); balls.export(td / "balls.stl")
        drum.copy().apply_translation([0, 0, z]).export(td / "drum.stl")
        drum.copy().apply_translation([0, 0, z + 70]).export(td / "drum_up.stl")
        seated = [(td / "base.stl", BASE), (td / "drum.stl", DRUM), (td / "balls.stl", BB)]
        render(seated, img / "caddy_views.png", "--views")
        render([(td / "base.stl", BASE), (td / "drum_up.stl", DRUM), (td / "balls.stl", BB)],
               img / "caddy_exploded.png", "--azimuth", "30", "--elevation", "22")
        render([(td / "base.stl", BASE), (td / "balls.stl", BB)], img / "caddy_base_balls.png",
               "--azimuth", "20", "--elevation", "50")
    print("images ->", img)


if __name__ == "__main__":
    main()
