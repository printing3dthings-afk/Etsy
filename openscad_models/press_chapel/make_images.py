#!/usr/bin/env python3
"""Press-to-Light Chapel drop test print: design-review renders of the exported parts
(2026-11-17). The assembly, lifted and at rest, and the plate as it prints.

    python3 make_images.py   (needs make_coupon.sh first; writes images/*.png)
"""
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
P, IMG, TOOLS = HERE / "parts", HERE / "images", HERE.parents[1] / "tools"
FRAME, MOVING, HUB = "0.93,0.93,0.95", "0.62,0.30,0.30", "0.55,0.72,0.92"


def render(parts, out, az, el):
    args = ["python3", str(TOOLS / "blender_render.py"), "-o", str(IMG / out), "--resolution", "1400",
            "--azimuth", str(az), "--elevation", str(el)]
    for path, col in parts:
        args += ["--part", f"{path}:{col}"]
    subprocess.run(args, check=True)


def scad(out, part, **kw):
    args = ["openscad", "-q", "-o", str(out), "-D", f'part="{part}"']
    for k, v in kw.items():
        args += ["-D", f"{k}={v}"]
    subprocess.run(args + [str(HERE / "drop_coupon.scad")], check=True)


def main():
    IMG.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        scad(td / "frame.stl", "frame")
        for name, drop in (("lifted", 0), ("rest", 30)):   # TRAVEL in drop_coupon.scad
            scad(td / f"moving_{name}.stl", "moving", DROP=drop)
            scad(td / f"hub_{name}.stl", "hub_at", DROP=drop, v=2)
            render([(td / "frame.stl", FRAME), (td / f"moving_{name}.stl", MOVING), (td / f"hub_{name}.stl", HUB)],
                   f"drop_{name}.png", -30, 18)
        # the hub cut in half, the shaft lifted: the star, the nut and the bore it falls into
        scad(td / "hub_half.stl", "hub", v=2)
        import trimesh
        h = trimesh.load(td / "hub_half.stl")
        h = trimesh.intersections.slice_mesh_plane(h, [0, 1, 0], [0, 0, 0], cap=True)   # keep the back half: the cut faces the camera
        h.export(td / "hub_half.stl")
        scad(td / "shaft.stl", "shaft")
        render([(td / "hub_half.stl", HUB), (td / "shaft.stl", MOVING)], "drop_section.png", -10, 10)
    plate = [(P / f"{p}.stl", FRAME) for p in ("base", "arch")] + [(P / "shaft.stl", MOVING), (P / "steeple.stl", MOVING)] \
        + [(P / f"hub_{v}.stl", HUB) for v in (1, 2, 3)]
    # each part on its own: the renderer stands every part on the floor at the origin
    for path, col in plate:
        render([(path, col)], f"part_{path.stem}.png", -30, 35)


if __name__ == "__main__":
    main()
