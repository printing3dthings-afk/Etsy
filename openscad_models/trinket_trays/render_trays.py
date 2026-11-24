"""Design-review renders of the trinket trays (2026-11-24): each frame with its insert dropped in
(the insert's floor on the frame's, as it sits in use), one at a time (parallel Blender runs
failed), then one contact sheet.

    python3 render_trays.py [--only star]
"""
import argparse
import subprocess
import sys
from pathlib import Path

import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARTS, IMG = HERE / "parts", HERE / "images"
FLOOR = 1.6   # tray_set.py

# frame, insert: two filaments each, Christmas pairs
COLOURS = {
    "star": ("0.85,0.66,0.22", "0.95,0.93,0.88"),
    "tree": ("0.20,0.48,0.30", "0.95,0.93,0.88"),
    "mitten": ("0.70,0.15,0.18", "0.95,0.93,0.88"),
    "bauble": ("0.70,0.15,0.18", "0.85,0.66,0.22"),
    "bell": ("0.85,0.66,0.22", "0.70,0.15,0.18"),
    "gingerbread": ("0.60,0.36,0.18", "0.95,0.93,0.88"),
}


def render(name):
    ins = trimesh.load(PARTS / f"{name}_insert.stl")
    ins.apply_translation([0, 0, FLOOR])
    tmp = PARTS / f"_{name}_insert_seated.stl"
    ins.export(tmp)
    fc, ic = COLOURS[name]
    out = IMG / f"{name}_set.png"
    subprocess.run([sys.executable, str(ROOT / "tools" / "blender_render.py"),
                    "--part", f"{PARTS / f'{name}_frame.stl'}:{fc}", "--part", f"{tmp}:{ic}",
                    "-o", str(out), "--azimuth", "-25", "--elevation", "40", "--resolution", "900",
                    "--timeout", "900"], check=True)
    tmp.unlink()
    return out


def sheet(names):
    tiles = [Image.open(IMG / f"{n}_set.png").convert("RGB").resize((600, 600)) for n in names]
    W = Image.new("RGB", (1800, 600 * ((len(tiles) + 2) // 3) + 60), (246, 244, 240))
    for i, t in enumerate(tiles):
        W.paste(t, (600 * (i % 3), 600 * (i // 3)))
    d = ImageDraw.Draw(W)
    try:
        f = ImageFont.truetype(str(ROOT / "assets" / "fonts" / "Poppins-Regular.ttf"), 26)
    except OSError:
        f = ImageFont.load_default()
    d.text((900, W.height - 30), "Design-review renders of the real parts, not photos", fill=(90, 90, 90),
           font=f, anchor="mm")
    W.save(IMG / "tray_sheet.jpg", quality=90)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    names = [a.only] if a.only else list(COLOURS)
    for n in names:
        print(render(n), flush=True)
    if not a.only:
        sheet(names)
