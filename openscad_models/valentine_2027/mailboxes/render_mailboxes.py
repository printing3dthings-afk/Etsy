#!/usr/bin/env python3
"""Studio renders of the two Valentine mailboxes, assembled, from the exported
parts in place (part *_use / body). Design-review renders, not photos.

    python3 render_mailboxes.py
"""
import subprocess, sys, tempfile
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
R = HERE.parents[2] / "tools" / "blender_render.py"
PINK, RED, WHITE, DARK = "0.96,0.65,0.76", "0.84,0.15,0.24", "0.96,0.95,0.92", "0.23,0.16,0.23"
LILAC, FUR, PUPIL = "0.72,0.61,0.88", "0.96,0.55,0.71", "0.17,0.14,0.2"
LETTER = ("love_letter", [("body", PINK, 0), ("body_red", RED, 0), ("body_white", WHITE, 0), ("body_dark", DARK, 0),
                          ("lid_use", PINK, 0)])
MONSTER = ("love_monster", [("body_use", LILAC, 0), ("face_use", LILAC, 0), ("face_white_use", WHITE, 0),
                            ("face_red_use", RED, 0), ("face_dark_use", PUPIL, 0), ("fur_use", FUR, 0)])


def render(design, out, extra, lift=None):
    d, parts = design
    with tempfile.TemporaryDirectory() as tmp:
        args = []
        for name, rgb, _ in parts:
            m = trimesh.load(HERE / d / "parts" / f"{name}.stl", force="mesh")
            if lift and name in lift:
                m.apply_translation(lift[name])
            p = Path(tmp) / f"{name}.stl"
            m.export(p)
            args += ["--part", f"{p}:{rgb}"]
        subprocess.run([sys.executable, str(R), *args, "-o", str(HERE / d / "images" / out),
                        "--resolution", "1400", "--timeout", "1100", *extra], check=True)


for design in (LETTER, MONSTER):
    (HERE / design[0] / "images").mkdir(exist_ok=True)
render(LETTER, "letter", ["--views"])
render(LETTER, "letter_back.png", ["--azimuth", "155", "--elevation", "18"])
render(MONSTER, "monster", ["--views"])
render(MONSTER, "monster_apart.png", ["--azimuth", "-28", "--elevation", "22"],
       lift={"fur_use": [0, 0, 70], "face_use": [0, 0, 35], "face_white_use": [0, 0, 35],
             "face_red_use": [0, 0, 35], "face_dark_use": [0, 0, 35]})
