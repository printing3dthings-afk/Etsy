#!/usr/bin/env python3
"""Pocket Top snap test print: review renders from the exported parts (2026-11-14).

    python3 make_images.py   (images/snap_plate.png, snap_assembled.png, snap_section.png)
"""
import os
import subprocess
import tempfile
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
P, IMG = HERE / "parts", HERE / "images"
TOOLS = HERE.parents[1] / "tools"
HUB, STEM = "0.85,0.45,0.55", "0.20,0.40,0.55"
ENV = dict(os.environ, OPENSCADPATH=str(HERE.parents[1] / "assets" / "openscad_libs"))


def scad(body, out):
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "m.scad"
        src.write_text(f'include <{HERE / "snap_coupon.scad"}>\n{body}\n')
        subprocess.run(["openscad", "-o", str(out), "-D", 'part="none"', str(src)], check=True,
                       capture_output=True, env=ENV)


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                                 tri_verts=np.asarray(m.faces, np.uint32)))


def render(parts, out, az, el):
    args = ["python3", str(TOOLS / "blender_render.py"), "-o", str(IMG / out), "--azimuth", str(az),
            "--elevation", str(el), "--resolution", "1400"]
    for path, col in parts:
        args += ["--part", f"{path}:{col}"]
    subprocess.run(args, check=True)


def main():
    IMG.mkdir(exist_ok=True)
    render([(P / "hubs.stl", HUB)] + [(P / f"stem_{i}.stl", STEM) for i in (1, 2, 3)], "snap_plate.png", 30, 50)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        scad("for (i = [0 : 2]) translate([i * 36, 0, 0]) hub(i);", td / "hubs.stl")
        scad("for (i = [0 : 2]) translate([i * 36, 0, B + GRIP_H]) mirror([0, 0, 1]) stem(i);", td / "stems.stl")
        render([(td / "hubs.stl", HUB), (td / "stems.stl", STEM)], "snap_assembled.png", 25, 35)
        # pair 2, cut through one nub (y = 0) and seen from -y: the nub in the groove
        keep = m3d.Manifold.cube([40, 40, 40]).translate([-20, 0, -15])
        for name, body in (("h", "hub(1);"), ("s", "translate([0, 0, B + GRIP_H]) mirror([0, 0, 1]) stem(1);")):
            scad(body, td / f"{name}.stl")
            g = (man(trimesh.load(td / f"{name}.stl")) ^ keep).to_mesh()
            trimesh.Trimesh(g.vert_properties[:, :3], g.tri_verts).export(td / f"{name}_cut.stl")
        render([(td / "h_cut.stl", HUB), (td / "s_cut.stl", STEM)], "snap_section.png", 0, 10)


if __name__ == "__main__":
    main()
