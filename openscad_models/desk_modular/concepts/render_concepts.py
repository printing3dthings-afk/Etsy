"""Renders of the five connection concepts (2026-11-24), one at a time, then a labelled sheet.
Module colours: cream and sage; the connecting piece in red, so the joint reads.

    python3 render_concepts.py
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STL, IMG = HERE / "stl", HERE / "images"
A, B, C, J = "0.93,0.91,0.86", "0.62,0.72,0.60", "0.80,0.76,0.66", "0.78,0.20,0.22"

OPTIONS = [
    ("dovetail", "1  Drop-in dovetail", [("dovetail_a", A), ("dovetail_tails", J), ("dovetail_b", B)]),
    ("butterfly", "2  Butterfly keys", [("butterfly_a", A), ("butterfly_b", B), ("butterfly_key", J)]),
    ("grid", "3  Base grid", [("grid_plate", J), ("grid_a", A), ("grid_b", B)]),
    ("rail", "4  Back rail", [("rail_rail", J), ("rail_a", A), ("rail_b", B), ("rail_c", C)]),
    ("magnet", "5  Magnets", [("magnet_a", A), ("magnet_b", B), ("magnet_discs", "0.55,0.56,0.58")]),
]


ANGLE = {"rail": 210, "dovetail": 30}


def render(key, parts):
    args = []
    for p, c in parts:
        args += ["--part", f"{STL / (p + '.stl')}:{c}"]
    out = IMG / f"{key}.png"
    subprocess.run([sys.executable, str(ROOT / "tools" / "blender_render.py"), *args, "-o", str(out),
                    "--azimuth", str(ANGLE.get(key, -30)), "--elevation", "32", "--resolution", "900", "--timeout", "900"], check=True)
    return out


def sheet():
    f = ImageFont.truetype(str(ROOT / "assets" / "fonts" / "Poppins-SemiBold.ttf"), 34)
    s = ImageFont.truetype(str(ROOT / "assets" / "fonts" / "Poppins-Regular.ttf"), 24)
    W = Image.new("RGB", (1800, 1260), (246, 244, 240))
    d = ImageDraw.Draw(W)
    for i, (key, label, _) in enumerate(OPTIONS):
        t = Image.open(IMG / f"{key}.png").convert("RGB").resize((560, 560))
        x, y = 20 + 600 * (i % 3), 20 + 600 * (i // 3)
        W.paste(t, (x, y))
        d.text((x + 16, y + 12), label, fill=(40, 40, 40), font=f)
    d.text((1500, 900), "Red = the joint", fill=(150, 40, 45), font=s, anchor="mm")
    d.text((1500, 940), "Sketches, not finished designs", fill=(90, 90, 90), font=s, anchor="mm")
    d.text((900, 1235), "Design-review renders of concept models, not photos", fill=(90, 90, 90), font=s, anchor="mm")
    W.save(IMG / "concept_sheet.jpg", quality=90)


if __name__ == "__main__":
    IMG.mkdir(exist_ok=True)
    for key, _, parts in OPTIONS:
        print(render(key, parts), flush=True)
    sheet()
