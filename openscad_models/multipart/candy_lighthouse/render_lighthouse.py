#!/usr/bin/env python3
"""Studio renders of the Candy Lighthouse, assembled, from the exported parts.

    python3 render_lighthouse.py [--views]

Each print is moved to where it sits (the wheel on the gallery floor, the
lantern in its groove, the roof on the lantern) and every colour part goes in
as its own filament. Design-review renders from the real meshes, not photos.
"""
import argparse, re, subprocess, sys, tempfile
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
R = HERE.parents[2] / "tools" / "blender_render.py"

WHITE, RED, BLUE, CLEAR = "0.96,0.95,0.92", "0.78,0.19,0.17", "0.23,0.43,0.65", "0.80,0.91,0.94"

ap = argparse.ArgumentParser()
ap.add_argument("--views", action="store_true")
a = ap.parse_args()

nums = [float(x) for x in re.findall(r"-?[\d.]+", (HERE / "logs" / "dims.echo").read_text().split("DIMS =")[1])]
zg, lan_z, roof_z = nums[0], nums[1], nums[2]
parts = [("tower", 0, WHITE), ("tower_red", 0, RED), ("tower_blue", 0, BLUE),
         ("wheel", zg, WHITE), ("lantern_up", lan_z, CLEAR), ("roof", roof_z, RED)]
with tempfile.TemporaryDirectory() as tmp:
    args = []
    for name, z, rgb in parts:
        m = trimesh.load(HERE / "parts" / f"{name}.stl", force="mesh")
        m.apply_translation([0, 0, z])
        out = Path(tmp) / f"{name}.stl"
        m.export(out)
        args += ["--part", f"{out}:{rgb}"]
    stem = HERE / "images" / "lighthouse"
    cmd = [sys.executable, str(R), *args, "--resolution", "1400", "--timeout", "1800",
           "-o", str(stem) + ("" if a.views else ".png")]
    cmd += ["--views"] if a.views else ["--azimuth", "-40", "--elevation", "18"]
    subprocess.run(cmd, check=True)
