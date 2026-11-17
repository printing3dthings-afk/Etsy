#!/usr/bin/env python3
"""Studio renders of the Urban Kid, from his real exported parts in assembly
coordinates (parts/assembled/). Design-review renders, not photos.

    python3 render_kid.py                 three views of him assembled -> images/kid_*.png
    python3 render_kid.py --plate         the prints as they lie        -> images/kid_plate.png
    python3 render_kid.py --closeup       his face and chain            -> images/kid_closeup.png
    python3 render_kid.py --exploded      pulled apart, for the guide   -> images/kid_exploded.png
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
R = HERE.parents[1] / "tools" / "blender_render.py"
RGB = {"black": "0.11,0.11,0.12", "white": "0.93,0.93,0.91", "charcoal": "0.27,0.28,0.30",
       "red": "0.78,0.11,0.13", "skin": "0.86,0.64,0.48", "gold": "0.85,0.64,0.18"}
COLOURS = {"base": "black", "shoe_r": "white", "shoe_l": "white", "pants": "charcoal", "hoodie": "red",
           "head": "skin", "cap": "black", "chain": "gold", "pin": "black"}


def parts_args(folder):
    return sum((["--part", f"{folder / (n + '.stl')}:{RGB[c]}"] for n, c in COLOURS.items()
                if (folder / (n + ".stl")).exists()), [])


def plate():
    """The prints laid out in rows on one picture, as they come off the plate."""
    out = Path(tempfile.gettempdir()) / "urban_kid_plate_parts"
    out.mkdir(parents=True, exist_ok=True)
    order = ["head", "hoodie", "cap", "pants", "base", "shoe_r", "shoe_l", "chain", "pin"]
    x, y, row_h, args = 0.0, 0.0, 0.0, []
    for n in order:
        m = trimesh.load(HERE / "parts" / f"{n}.stl", force="mesh")
        m.apply_translation(-m.bounds[0] + [x, y, 0])
        x += m.extents[0] + 8
        row_h = max(row_h, m.extents[1])
        if x > 150:
            x, y, row_h = 0.0, y + row_h + 8, 0.0
        p = out / f"{n}.stl"
        m.export(p)
        args += ["--part", f"{p}:{RGB[COLOURS[n]]}"]
    return args


def exploded():
    """Each print lifted off the one under it, the chain out in front, the pin
    between the head and the cap: how they go together."""
    import sys as _s
    _s.path.insert(0, str(HERE))
    import kid as K
    from check_fit import pin_assembled
    out = Path(tempfile.gettempdir()) / "urban_kid_exploded_parts"
    out.mkdir(parents=True, exist_ok=True)
    lift = {"base": 0, "shoe_r": 7, "shoe_l": 7, "pants": 15, "hoodie": 24, "head": 34, "cap": 50, "chain": 24}
    args = []
    for n, dz in lift.items():
        m = trimesh.load(HERE / "parts" / "assembled" / f"{n}.stl", force="mesh")
        m.apply_translation([0, -14 if n == "chain" else 0, dz])
        p = out / f"{n}.stl"
        m.export(p)
        args += ["--part", f"{p}:{RGB[COLOURS[n]]}"]
    pin = pin_assembled()
    pin.apply_translation([0, 0, 42])
    pin.export(out / "pin.stl")
    args += ["--part", f"{out / 'pin.stl'}:{RGB['black']}"]
    return args


def main():
    img = HERE / "images"
    img.mkdir(exist_ok=True)
    if "--plate" in sys.argv:
        cmd = [sys.executable, str(R), *plate(), "--elevation", "55", "--azimuth", "-30", "-o", str(img / "kid_plate.png")]
    elif "--exploded" in sys.argv:
        cmd = [sys.executable, str(R), *exploded(), "--azimuth", "-35", "--elevation", "12", "-o", str(img / "kid_exploded.png")]
    elif "--closeup" in sys.argv:
        cmd = [sys.executable, str(R), *parts_args(HERE / "parts" / "assembled"), "--azimuth", "-25", "--elevation", "6",
               "--lens", "120", "-o", str(img / "kid_closeup.png")]
    else:
        cmd = [sys.executable, str(R), *parts_args(HERE / "parts" / "assembled"), "--views", "--front=-y",
               "-o", str(img / "kid")]
    cmd += ["--samples", "96", "--resolution", "1100"]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
