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
    "snowman": ("0.45,0.62,0.80", "0.95,0.93,0.88"),
    "stocking": ("0.70,0.15,0.18", "0.95,0.93,0.88"),
    "gift_box": ("0.20,0.48,0.30", "0.70,0.15,0.18"),
    "snowflake": ("0.45,0.62,0.80", "0.95,0.93,0.88"),
    "santa_hat": ("0.95,0.93,0.88", "0.70,0.15,0.18"),
    "gingerbread_house": ("0.60,0.36,0.18", "0.95,0.93,0.88"),
}


def render(name, size="large"):
    stem = name + ("" if size == "large" else "_small")
    ins = trimesh.load(PARTS / f"{stem}_insert.stl")
    ins.apply_translation([0, 0, FLOOR])
    tmp = PARTS / f"_{stem}_insert_seated.stl"
    ins.export(tmp)
    fc, ic = COLOURS[name]
    out = IMG / f"{stem}_set.png"
    subprocess.run([sys.executable, str(ROOT / "tools" / "blender_render.py"),
                    "--part", f"{PARTS / f'{stem}_frame.stl'}:{fc}", "--part", f"{tmp}:{ic}",
                    "-o", str(out), "--azimuth", "-25", "--elevation", "40", "--resolution", "900",
                    "--timeout", "900"], check=True)
    tmp.unlink()
    return out


def sheet(names, size, title):
    stems = [n + ("" if size == "large" else "_small") for n in names]
    tiles = [Image.open(IMG / f"{s}_set.png").convert("RGB").resize((450, 450)) for s in stems]
    cols = 4
    W = Image.new("RGB", (450 * cols, 450 * ((len(tiles) + cols - 1) // cols) + 110), (246, 244, 240))
    d = ImageDraw.Draw(W)
    f = ImageFont.truetype(str(ROOT / "assets" / "fonts" / "Poppins-SemiBold.ttf"), 34)
    s_ = ImageFont.truetype(str(ROOT / "assets" / "fonts" / "Poppins-Regular.ttf"), 22)
    d.text((W.width / 2, 36), title, fill=(40, 40, 40), font=f, anchor="mm")
    for i, (t, n) in enumerate(zip(tiles, names)):
        x, y = 450 * (i % cols), 70 + 450 * (i // cols)
        W.paste(t, (x, y))
        d.text((x + 225, y + 425), n.replace("_", " "), fill=(70, 70, 70), font=s_, anchor="mm")
    d.text((W.width / 2, W.height - 22), "Design-review renders of the real parts, not photos", fill=(90, 90, 90),
           font=s_, anchor="mm")
    W.save(IMG / f"tray_sheet_{size}.jpg", quality=90)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--size", choices=["large", "small", "both"], default="both")
    a = ap.parse_args()
    names = [a.only] if a.only else list(COLOURS)
    sizes = ["large", "small"] if a.size == "both" else [a.size]
    for size in sizes:
        for n in names:
            print(render(n, size), flush=True)
    if not a.only:
        if "large" in sizes:
            sheet(names, "large", "Trinket trays, large: 148-196 mm")
        if "small" in sizes:
            sheet(names, "small", "Trinket trays, small: 110 mm")
