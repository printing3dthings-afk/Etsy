#!/usr/bin/env python3
"""Colour renders of the Nesting Cats, laid out as the concept render:
the largest opened, its top lifted off, the other four closed beside it.

  python3 render_cats.py            the line-up, from the exported parts
  python3 render_cats.py --each     also one three-view set of the 72 mm cat

These are design-review renders from the real parts (tools/blender_render.py),
not listing photos.
"""
import subprocess, sys, tempfile
from pathlib import Path
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HS = [90, 72, 57, 43, 30]
# the concept's five bodies, and its cream, dark and cheek pink
BODY = ["0.73,0.65,0.84", "0.94,0.70,0.78", "0.66,0.86,0.78", "0.95,0.79,0.60", "0.66,0.80,0.92"]
COL = {"trim": "0.97,0.95,0.89", "dark": "0.29,0.16,0.19", "pink": "0.94,0.56,0.63"}


def parts(i):
    """(stl, colour, the z it sits at assembled) for cat i."""
    zs = 0.30 * HS[i]
    if i == 4:
        return [(HERE / f"parts/cat4_solid_{c}.stl", BODY[4] if c == "body" else COL[c], 0)
                for c in ("body", "trim", "dark", "pink")]
    out = [(HERE / f"parts/cat{i}_bottom.stl", BODY[i], 0)]
    out += [(HERE / f"parts/cat{i}_top_{c}.stl", BODY[i] if c == "body" else COL[c], zs)
            for c in ("body", "trim", "dark", "pink")]
    return out


def lineup(tmp, lift=0.42):
    args, x = [], 0.0
    for i, h in enumerate(HS):
        r = 0.37 * h
        x += r if i else 0
        for k, (stl, col, z) in enumerate(parts(i)):
            m = trimesh.load(stl)
            # the largest opened: its top raised clear of its bottom
            m.apply_translation([x, 0, z + (lift * h if i == 0 and k else 0)])
            p = Path(tmp) / f"{i}_{k}.stl"
            m.export(p)
            args += ["--part", f"{p}:{col}"]
        x += r + 0.18 * h
    return args


def blender(args, out, *extra):
    cmd = [sys.executable, str(ROOT / "tools/blender_render.py"), *args, "-o", str(out), *extra]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    img = HERE / "images"
    img.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        blender(lineup(tmp), img / "nesting_cats_lineup.png",
                "--azimuth", "18", "--elevation", "14", "--resolution", "1600", "--lens", "70")
        if "--each" in sys.argv:
            args = []
            for k, (stl, col, z) in enumerate(parts(1)):
                m = trimesh.load(stl); m.apply_translation([0, 0, z])
                p = Path(tmp) / f"one_{k}.stl"; m.export(p)
                args += ["--part", f"{p}:{col}"]
            blender(args, img / "nesting_cats_72mm.png", "--views", "--front=-y", "--resolution", "1200")
