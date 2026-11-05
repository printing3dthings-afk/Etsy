#!/usr/bin/env python3
"""Studio renders of Kawaii Cow v2, assembled from her real exported parts
(each moved from its print pose to where it sits on her). Design-review
renders, not photos.

    python3 render_cow_v2.py [parts_dir]            assembled views
    python3 render_cow_v2.py [parts_dir] --plate    the five prints as they lie
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cow_v2 as c2  # noqa: E402

R = HERE.parents[2] / "tools" / "blender_render.py"
RGB = {"white": "0.96,0.95,0.92", "black": "0.17,0.14,0.2", "pink": "0.96,0.65,0.76", "red": "0.84,0.15,0.24"}


def poses():
    """part -> 4x4 from its print pose to the assembly."""
    out = {"body": np.eye(4)}
    T = np.eye(4)
    T[2, 3] = c2.NECK_Z
    out["head"] = T
    for side, name in ((1, "ear_r"), (-1, "ear_l")):
        Rm, o = c2.ear_pose(side)
        T = np.eye(4)
        T[:3, :3], T[:3, 3] = Rm, o
        out[name] = T
    Rm, o = c2.heart_pose()
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = Rm, o
    out["heart"] = T
    return out


def assemble(parts, dest):
    """Write one STL per colour of the assembled cow; return their paths."""
    dest.mkdir(exist_ok=True)
    by_colour = {}
    for part, T in poses().items():
        for f in sorted(parts.glob(f"{part}_*.stl")):
            colour = f.stem[len(part) + 1:]
            if colour not in RGB:
                continue
            m = trimesh.load(f, force="mesh")
            m.apply_transform(T)
            by_colour.setdefault(colour, []).append(m)
    out = {}
    for colour, ms in by_colour.items():
        p = dest / f"cow_v2_{colour}.stl"
        trimesh.util.concatenate(ms).export(p)
        out[colour] = p
    return out


def plate(parts, dest):
    """The five prints laid out side by side, as they print."""
    dest.mkdir(exist_ok=True)
    offs = {"body": (0, 0), "head": (50, 0), "heart": (-45, -10), "ear_r": (-45, 25), "ear_l": (-45, 38)}
    by_colour = {}
    for part, (dx, dy) in offs.items():
        for f in sorted(parts.glob(f"{part}_*.stl")):
            colour = f.stem[len(part) + 1:]
            if colour not in RGB:
                continue
            m = trimesh.load(f, force="mesh")
            m.apply_translation([dx, dy, 0])
            by_colour.setdefault(colour, []).append(m)
    out = {}
    for colour, ms in by_colour.items():
        p = dest / f"plate_{colour}.stl"
        trimesh.util.concatenate(ms).export(p)
        out[colour] = p
    return out


def render(files, out, extra):
    args = []
    for colour, p in files.items():
        args += ["--part", f"{p}:{RGB[colour]}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(out), "--resolution", "1400",
                    "--timeout", "1500", *extra], check=True)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    parts = Path(a[0]) if a else HERE / "parts"
    img = HERE / "images"
    img.mkdir(exist_ok=True)
    if "--plate" in sys.argv:
        render(plate(parts, parts / "plate"), img / "cow_v2_plate.png", ["--azimuth", "20", "--elevation", "50"])
    else:
        files = assemble(parts, parts / "assembled")
        if "--quick" in sys.argv:
            render(files, img / "cow_v2_quick.png", ["--azimuth", "-30", "--elevation", "15", "--resolution", "700", "--samples", "32"])
        else:
            render(files, img / "cow_v2", ["--views"])
            render(files, img / "cow_v2_back.png", ["--azimuth", "155", "--elevation", "18"])
            render(files, img / "cow_v2_side.png", ["--azimuth", "90", "--elevation", "10"])
