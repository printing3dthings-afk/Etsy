#!/usr/bin/env python3
"""Renders for the fit test plate's instruction guide (2026-10-30).

Each mechanism twice, from the real exported parts of its middle clearance:
"apart" (the moving part turned the way you hold it and lifted above where it
goes) and "together" (put together exactly as check_fits.py checks it). Plus
the whole plate as printed, each mechanism in its own colour, as a key.

    python3 render_guide.py           every render (cached ones are skipped)

Writes guide/images/*.png. Blender one render at a time: two at once time out.
"""
import subprocess, sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
PLATE = HERE.parent
ROOT = PLATE.parents[2]
PARTS = PLATE / "parts"
TMP = PLATE / "logs" / "guide"
OUT = HERE / "images"
R = ROOT / "tools" / "blender_render.py"

WHITE, CORAL = "0.95,0.94,0.91", "0.93,0.47,0.42"
KEY = {"thread": "0.36,0.56,0.84", "ball": "0.93,0.47,0.42", "gears": "0.93,0.72,0.30",
       "detent": "0.40,0.70,0.50", "bayonet": "0.62,0.50,0.82"}
KIND_OF = {"screw": "thread", "nut": "thread", "ball": "ball", "socket": "ball", "gear_base": "gears",
           "gear20": "gears", "gear10": "gears", "detent_base": "detent", "detent_wheel": "detent",
           "bayonet_ring": "bayonet", "bayonet_cap": "bayonet"}

# the plate's own numbers, as check_fits.py uses them
GCD, GO, HC, YH = 22.5, 0.15, 2 + 0.8 + 4.1, 10
I = 1                                   # the middle clearance of each


def T(name, rot=None, move=(0, 0, 0)):
    """name_I.stl, optionally turned (x-axis degrees, then z-axis degrees), then moved."""
    m = trimesh.load(PARTS / f"{name}_{I}.stl", force="mesh")
    if rot:
        rx, rz = rot
        if rx:
            m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rx), [1, 0, 0]))
        if rz:
            m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rz), [0, 0, 1]))
    m.apply_translation(move)
    return m


def scenes():
    lift = 16
    s = {}
    s["thread_apart"] = [(T("screw"), WHITE), (T("nut", move=(0, 0, 2 + lift)), CORAL)]
    s["thread_together"] = [(T("screw"), WHITE), (T("nut", move=(0, 0, 2)), CORAL)]
    s["ball_apart"] = [(T("socket"), WHITE), (T("ball", (180, 0), (0, 0, 12 + HC + lift)), CORAL)]
    s["ball_together"] = [(T("socket"), WHITE), (T("ball", (180, 0), (0, 0, 12 + HC)), CORAL)]
    s["gears_apart"] = [(T("gear_base"), WHITE), (T("gear20", move=(0, 0, 3 + lift)), CORAL),
                        (T("gear10", (0, 18), (GCD + GO, 0, 3 + lift)), CORAL)]
    s["gears_together"] = [(T("gear_base"), WHITE), (T("gear20", move=(0, 0, 3)), CORAL),
                           (T("gear10", (0, 18), (GCD + GO, 0, 3)), CORAL)]
    s["detent_apart"] = [(T("detent_base"), WHITE), (T("detent_wheel", move=(0, 0, 3 + lift)), CORAL)]
    s["detent_together"] = [(T("detent_base"), WHITE), (T("detent_wheel", move=(0, 0, 3)), CORAL)]
    s["bayonet_apart"] = [(T("bayonet_ring"), WHITE), (T("bayonet_cap", (180, 0), (0, 0, YH + 2 + lift)), CORAL)]
    s["bayonet_together"] = [(T("bayonet_ring"), WHITE), (T("bayonet_cap", (180, 24), (0, 0, YH + 2)), CORAL)]
    return s


VIEW = {"thread": (-35, 32), "ball": (-35, 22), "gears": (-25, 40), "detent": (-20, 45), "bayonet": (-35, 34)}


def render(name, parts, az, el, res=1100):
    out = OUT / f"{name}.png"
    args = []
    d = TMP / name
    d.mkdir(parents=True, exist_ok=True)
    for k, (m, rgb) in enumerate(parts):
        p = d / f"{k}.stl"
        m.export(p)
        args += ["--part", f"{p}:{rgb}"]
    cmd = [sys.executable, str(R), *args, "-o", str(out), "--azimuth", str(az), "--elevation", str(el),
           "--resolution", str(res), "--timeout", "1100"]
    subprocess.run(cmd, check=True)


def main():
    OUT.mkdir(exist_ok=True)
    for name, parts in scenes().items():
        az, el = VIEW[name.split("_")[0]]
        render(name, parts, az, el)
    # the key: the plate exactly as packed, each mechanism in its colour
    packed = PLATE / "logs" / "packed"
    by = {k: [] for k in KEY}
    for p in sorted(packed.glob("*.stl")):
        by[KIND_OF[p.stem.rsplit("_", 1)[0]]].append(trimesh.load(p, force="mesh"))
    render("plate_key", [(trimesh.util.concatenate(v), KEY[k]) for k, v in by.items()], 0, 62, 1400)


if __name__ == "__main__":
    main()
