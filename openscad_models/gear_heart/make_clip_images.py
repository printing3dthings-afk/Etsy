#!/usr/bin/env python3
"""Gear heart clips v2: the review renders for the guide (2026-11-14), from the exported
parts. Run check_clip.py first: it writes the pins and gears in their assembled places
(parts/clip/pin_use_*.stl, gear_use_*.stl).

    python3 make_clip_images.py    (images/clip_plate.png, clip_assembled.png, clip_section.png)
"""
import subprocess
import tempfile
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
P = HERE / "parts" / "clip"
IMG = HERE / "images"
BLENDER = HERE.parents[1] / "tools" / "blender_render.py"
BASE, PIN, GEAR = "0.55,0.52,0.48", "0.80,0.55,0.10", "0.15,0.42,0.50"


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                                 tri_verts=np.asarray(m.faces, np.uint32)))


def tm(mf):
    g = mf.to_mesh()
    return trimesh.Trimesh(g.vert_properties[:, :3], g.tri_verts)


def render(parts, out, az, el):
    args = ["python3", str(BLENDER), "-o", str(IMG / out), "--azimuth", str(az),
            "--elevation", str(el), "--resolution", "1400"]
    for path, col in parts:
        args += ["--part", f"{path}:{col}"]
    subprocess.run(args, check=True)


def main():
    render([(P / "base.stl", BASE), (P / "pins.stl", PIN), (P / "gears.stl", GEAR)], "clip_plate.png", 30, 45)
    render([(P / "base.stl", BASE)] + [(P / f"pin_use_{i}.stl", PIN) for i in range(3)]
           + [(P / f"gear_use_{i}.stl", GEAR) for i in range(3)], "clip_assembled.png", 20, 25)
    # the middle boss (pin 2), cut on the pin's axis: the half at y >= 0, seen from -y
    keep = m3d.Manifold.cube([24, 100, 100]).translate([14, 0, -20])
    with tempfile.TemporaryDirectory() as td:
        parts = []
        for name, col in (("base.stl", BASE), ("pin_use_1.stl", PIN), ("gear_use_1.stl", GEAR)):
            out = Path(td) / name
            tm(man(trimesh.load(P / name)) ^ keep).export(out)
            parts.append((out, col))
        render(parts, "clip_section.png", 0, 8)


if __name__ == "__main__":
    main()
