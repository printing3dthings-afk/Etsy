#!/usr/bin/env python3
"""Studio renders of Teacup Bear v2, assembled from her real exported parts
(each moved from its print pose to where it sits). Design-review renders, not
photos.

    python3 render_teacup_bear_v2.py [parts_dir]            assembled views
    python3 render_teacup_bear_v2.py [parts_dir] --plate    the three prints as they lie
    python3 render_teacup_bear_v2.py [parts_dir] --quick    one small three-quarter view
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import teacup_bear_v2 as b2  # noqa: E402

R = HERE.parents[2] / "tools" / "blender_render.py"
RGB = {"cream": "0.96,0.95,0.92", "tan": "0.78,0.56,0.37", "brown": "0.29,0.18,0.13", "pink": "0.96,0.65,0.76"}
LIFT = {"cup": 0.0, "body": b2.TEA_TOP, "head": b2.NECK_Z}
PLATE = {"cup": (0, 0), "body": (65, 0), "head": (-60, 0)}


def collect(parts, dest, place):
    dest.mkdir(exist_ok=True)
    by = {}
    for part in b2.PARTS:
        for f in sorted(parts.glob(f"{part}_*.stl")):
            colour = f.stem[len(part) + 1:]
            if colour not in RGB:
                continue
            m = trimesh.load(f, force="mesh")
            m.apply_translation(place(part))
            by.setdefault(colour, []).append(m)
    out = {}
    for colour, ms in by.items():
        p = dest / f"bear_{colour}.stl"
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
        files = collect(parts, parts / "plate", lambda p: [*PLATE[p], 0])
        render(files, img / "teacup_bear_v2_plate.png", ["--azimuth", "20", "--elevation", "50"])
    else:
        files = collect(parts, parts / "assembled", lambda p: [0, 0, LIFT[p]])
        if "--quick" in sys.argv:
            render(files, img / "teacup_bear_v2_quick.png",
                   ["--azimuth", "-30", "--elevation", "15", "--resolution", "700", "--samples", "32"])
        else:
            render(files, img / "teacup_bear_v2", ["--views"])
            render(files, img / "teacup_bear_v2_side.png", ["--azimuth", "90", "--elevation", "10"])
