#!/usr/bin/env python3
"""Studio renders of the two clickers, assembled, from the exported parts.

    python3 render_clickers.py tin|jar [--views] [--pressed]

Each print is moved to where it sits on the switch (the upper print onto the
lower, the cap onto the stem) and every colour part goes in as its own
filament. Design-review renders from the real meshes, not photos.
"""
import argparse, subprocess, sys, tempfile
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
R = HERE.parents[1] / "tools" / "blender_render.py"

RED, WHITE, BROWN, GREEN, MINT = "0.70,0.15,0.18", "0.96,0.95,0.92", "0.60,0.36,0.18", "0.24,0.56,0.29", "0.66,0.86,0.78"
S_TIN = 1.6 + 5.0 + 3.3 + 0.6
S_JAR = 30.0
CAP = 1.5 + 6.6 + 3.6 - 3.4          # cap underside above S, at rest
DESIGNS = {
    "tin": ("gingerbread_tin", S_TIN, [
        ("tin", 0, RED), ("tin_snow", 0, WHITE), ("lid", "S", RED),
        ("cookie", "C", BROWN), ("cookie_icing", "C", WHITE), ("cookie_red", "C", RED), ("cookie_green", "C", GREEN)]),
    "jar": ("cookie_jar", S_JAR, [
        ("jar", 0, MINT), ("jar_label", 0, WHITE), ("jar_letters", 0, RED), ("top", "S", MINT), ("top_rim", "S", RED),
        ("gb", "C", BROWN), ("gb_icing", "C", WHITE), ("gb_red", "C", RED)]),
}

ap = argparse.ArgumentParser()
ap.add_argument("design", choices=DESIGNS)
ap.add_argument("--views", action="store_true")
ap.add_argument("--pressed", action="store_true")
a = ap.parse_args()
d, S, parts = DESIGNS[a.design]
with tempfile.TemporaryDirectory() as tmp:
    args = []
    for name, at, rgb in parts:
        z = 0 if at == 0 else S if at == "S" else S + CAP - (4.0 if a.pressed else 0)
        m = trimesh.load(HERE / d / "parts" / f"{name}.stl", force="mesh")
        m.apply_translation([0, 0, z])
        out = Path(tmp) / f"{name}.stl"
        m.export(out)
        args += ["--part", f"{out}:{rgb}"]
    stem = HERE / d / "images" / (a.design + ("_pressed" if a.pressed else ""))
    cmd = [sys.executable, str(R), *args, "--resolution", "1400", "--timeout", "1200",
           "-o", str(stem) + ("" if a.views else ".png")]
    cmd += ["--views"] if a.views else ["--azimuth", "-30", "--elevation", "28"]
    subprocess.run(cmd, check=True)
