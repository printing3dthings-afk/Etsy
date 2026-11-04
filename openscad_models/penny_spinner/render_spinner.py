#!/usr/bin/env python3
"""Studio renders of the Penny Spinner from its exported parts: assembled with
16 pennies (three views), pulled apart in the order it goes together, and the
three prints as they lie on the plate. The pennies are drawn as plain discs.
Design-review renders, not photos.

    python3 render_spinner.py        (after ./ship.sh)
"""
import subprocess
import sys
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
PARTS = HERE / "parts"
IMG = HERE / "images"
R = HERE.parents[1] / "tools" / "blender_render.py"
TEAL, CREAM, COPPER = "0.23,0.56,0.54", "0.96,0.95,0.92", "0.72,0.45,0.20"


def moved(name, dx=0.0, dy=0.0, dz=0.0, tag=""):
    out = PARTS / f"_r_{name}{tag}.stl"
    m = trimesh.load(PARTS / f"{name}.stl", force="mesh")
    m.apply_translation([dx, dy, dz])
    m.export(out)
    return out


def render(parts, out, extra):
    args = []
    for path, rgb in parts:
        args += ["--part", f"{path}:{rgb}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out),
                    "--resolution", "1400", "--timeout", "1200", *extra], check=True)


def main():
    IMG.mkdir(exist_ok=True)
    render([(PARTS / "crown_use.stl", TEAL), (PARTS / "base_use.stl", CREAM),
            (PARTS / "stem_use.stl", CREAM), (PARTS / "coins.stl", COPPER)], "penny_spinner", ["--views"])
    render([(PARTS / "base_use.stl", CREAM), (moved("coins", dz=14, tag="_x"), COPPER),
            (moved("crown_use", dz=26, tag="_x"), TEAL), (moved("stem_use", dz=52, tag="_x"), CREAM)],
           "penny_spinner_exploded.png", ["--azimuth", "-35", "--elevation", "16"])
    render([(moved("crown", -45, 0, tag="_k"), TEAL), (moved("base", 45, 0, tag="_k"), CREAM),
            (moved("stem", 0, 50, tag="_k"), CREAM)],
           "penny_spinner_prints.png", ["--azimuth", "-20", "--elevation", "50"])
    for p in PARTS.glob("_r_*.stl"):
        p.unlink()


if __name__ == "__main__":
    main()
