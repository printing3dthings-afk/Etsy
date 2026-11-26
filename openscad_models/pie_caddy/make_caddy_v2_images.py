#!/usr/bin/env python3
"""Pie Drum Caddy v2 (the keeper): review renders from the exported parts (2026-11-26).
Renders, not photos. Parts come from parts_v2/ (make them with the v2 export first).

    python3 make_caddy_v2_images.py   (images/caddy_v2_*.png)
"""
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[1] / "tools"
V = {k: float(v) for k, v in re.findall(r"^(\w+) = ([0-9.]+);", (HERE / "pie_caddy_v2.scad").read_text(), re.M)}
DRUM, BASE, BB, KEEP = "0.91,0.72,0.54", "0.42,0.29,0.23", "0.93,0.80,0.25", "0.95,0.92,0.85"


def render(parts, out, *extra):
    cmd = ["python3", str(TOOLS / "blender_render.py"), "-o", str(out), "--resolution", "1100", *extra]
    for p, c in parts:
        cmd += ["--part", f"{p}:{c}"]
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    img, p2 = HERE / "images", HERE / "parts_v2"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        z = V["BASE_T"] + V["BALL"]
        balls = trimesh.util.concatenate([trimesh.creation.icosphere(subdivisions=2, radius=V["BALL"] / 2).apply_translation(
            [V["RING_R"] * np.cos(a), V["RING_R"] * np.sin(a), V["BASE_T"] + V["BALL"] / 2])
            for a in np.linspace(0, 2 * np.pi, int(V["N_BALLS"]), endpoint=False)])
        balls.export(td / "balls.stl")
        trimesh.load(p2 / "base.stl").export(td / "base.stl")
        drum = trimesh.load(p2 / "drum.stl")
        keep = trimesh.load(p2 / "keeper_seated.stl")
        drum.copy().apply_translation([0, 0, z]).export(td / "drum.stl")
        keep.export(td / "keep.stl")
        drum.copy().apply_translation([0, 0, z + 60]).export(td / "drum_up.stl")
        keep.copy().apply_translation([0, 0, 150]).export(td / "keep_up.stl")
        render([(td / "base.stl", BASE), (td / "balls.stl", BB), (td / "drum.stl", DRUM), (td / "keep.stl", KEEP)],
               img / "caddy_v2_views.png", "--views")
        render([(td / "base.stl", BASE), (td / "balls.stl", BB), (td / "drum_up.stl", DRUM), (td / "keep_up.stl", KEEP)],
               img / "caddy_v2_exploded.png", "--azimuth", "30", "--elevation", "18")
        # for the guide: the keeper held above the turned drum, and a cut through the middle
        keep.copy().apply_translation([0, 0, 45]).export(td / "keep_lift.stl")
        render([(td / "base.stl", BASE), (td / "balls.stl", BB), (td / "drum.stl", DRUM), (td / "keep_lift.stl", KEEP)],
               img / "caddy_v2_keeper_in.png", "--azimuth", "30", "--elevation", "28")
        cut = lambda f: trimesh.intersections.slice_mesh_plane(trimesh.load(td / f), [0, 1, 0], [0, 0, 0], cap=True)
        for f in ("base.stl", "balls.stl", "drum.stl", "keep.stl"):
            cut(f).export(td / f"cut_{f}")
        render([(td / "cut_base.stl", BASE), (td / "cut_balls.stl", BB), (td / "cut_drum.stl", DRUM), (td / "cut_keep.stl", KEEP)],
               img / "caddy_v2_section.png", "--azimuth", "0", "--elevation", "6")
    print("images ->", img)


if __name__ == "__main__":
    main()
