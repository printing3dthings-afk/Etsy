#!/usr/bin/env python3
"""Snowfall Plinko test print: design-review renders (2026-11-16).

    python3 make_images.py   (images/release_plate.png, release_inside.png, release_as_printed.png)
"""
import subprocess
import tempfile
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
P, IMG, TOOLS = HERE / "parts", HERE / "images", HERE.parents[1] / "tools"
BODY, BALLS = "0.93,0.93,0.95", "0.55,0.72,0.92"


def render(parts, out, az, el):
    args = ["python3", str(TOOLS / "blender_render.py"), "-o", str(IMG / out), "--resolution", "1400",
            "--azimuth", str(az), "--elevation", str(el)]
    for path, col in parts:
        args += ["--part", f"{path}:{col}"]
    subprocess.run(args, check=True)


def main():
    IMG.mkdir(exist_ok=True)
    render([(P / "body.stl", BODY), (P / "balls.stl", BALLS)], "release_plate.png", -30, 50)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # the front taken off (everything above the balls' chamber), to show what's inside
        b = trimesh.load(P / "body.stl")
        keep = m3d.Manifold.cube([200, 200, 8.4]).translate([-100, -100, -0.1])
        m = m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(b.vertices, np.float32),
                                  tri_verts=np.asarray(b.faces, np.uint32))) ^ keep
        g = m.to_mesh()
        trimesh.Trimesh(g.vert_properties[:, :3], g.tri_verts).export(td / "open.stl")
        render([(td / "open.stl", BODY), (P / "balls.stl", BALLS)], "release_inside.png", -20, 62)
        subprocess.run(["python3", str(TOOLS / "print_fidelity.py"), str(P / "coupon.stl"), "--keep", str(td / "f")],
                       check=True, capture_output=True)
        subprocess.run(["python3", str(TOOLS / "as_printed.py"), str(td / "f" / "fidelity.gcode"),
                        "-o", str(IMG / "release_as_printed.png"), "--colour", "#F4F1EA"], check=True)


if __name__ == "__main__":
    main()
