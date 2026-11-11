#!/usr/bin/env python3
"""Store pictures for the two Christmas village bundles (2026-11-11), rendered from
the STL parts inside the very ZIPs the buyer downloads, in the colours each
building's own README says its 3MF is set to. So every picture shows exactly the
files on sale. Each building's older renders in openscad_models/ predate its last
design change, and the Victorian group shot shows Santa's Workshop v1, so none of
them are used here.

    python3 render_covers.py         (renders, then the grids)
    python3 render_covers.py --grid  (grids only, from renders already made)

Writes images/<building>.png and images/<style>_village_grid.png. Design-review
renders, not photos: the grid says so on its face.
"""
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
R = ROOT / "tools" / "blender_render.py"
IMG = HERE / "images"
FONTS = ROOT / "assets" / "fonts"
ZIPS = {
    "victorian": HERE / "out" / "OnBrandCraftz_Victorian_Christmas_Village_8_buildings.zip",
    "gingerbread": HERE / "out" / "OnBrandCraftz_Gingerbread_Christmas_Village_7_buildings.zip",
}
TITLES = {"victorian": "Victorian Christmas Village", "gingerbread": "Gingerbread Christmas Village"}


def rgb(h):
    h = h.lstrip("#")
    return ",".join(f"{int(h[i:i + 2], 16) / 255:.3f}" for i in (0, 2, 4))


def buildings(z):
    """Each building folder's STL parts and the colour its README gives each part."""
    out = {}
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
        for folder in sorted({n.split("/")[0] for n in names if "/" in n}):
            readme = zf.read(f"{folder}/README.txt").decode()
            colours = dict(re.findall(r"^\s+(\w+): [^#\n]*(#[0-9A-Fa-f]{6})", readme, re.M))
            title = readme.splitlines()[0].split(" -- ")[0].strip()
            stls = [n for n in names if n.startswith(f"{folder}/stl/") and n.endswith(".stl")]
            parts = []
            for s in stls:
                part = Path(s).stem.rsplit("_", 1)[-1]
                if part not in colours:
                    sys.exit(f"{s}: no colour for part '{part}' in its README")
                parts.append((s, colours[part]))
            out[folder] = (title, parts)
    return out


def render_all():
    IMG.mkdir(exist_ok=True)
    for style, z in ZIPS.items():
        with tempfile.TemporaryDirectory() as td, zipfile.ZipFile(z) as zf:
            for folder, (title, parts) in buildings(z).items():
                args = []
                for s, col in parts:
                    zf.extract(s, td)
                    args += ["--part", f"{Path(td) / s}:{rgb(col)}"]
                out = IMG / f"{folder}.png"
                print("render", folder, flush=True)
                subprocess.run([sys.executable, str(R), *args, "-o", str(out), "--azimuth", "-30", "--elevation", "18",
                                "--resolution", "1000", "--timeout", "1200"], check=True)


def crop(p):
    """Trim the studio background to the building, then lift contrast without shifting its colours."""
    im = Image.open(p).convert("RGB")
    a = np.asarray(im).astype(int)
    ys, xs = np.where(np.abs(a - a[5, 5]).sum(axis=2) > 40)
    im = im.crop((max(xs.min() - 20, 0), max(ys.min() - 20, 0), min(xs.max() + 20, im.width), min(ys.max() + 20, im.height)))
    return Image.blend(im, ImageOps.autocontrast(im, cutoff=1, preserve_tone=True), 0.5)


def grid(style):
    blds = buildings(ZIPS[style])
    n = len(blds)
    cols = 4 if n > 6 else 3
    rows = -(-n // cols)
    W = 2400
    head, foot = 230, 110
    cell_w = W // cols
    cell_h = (W - head - foot) // rows
    canvas = Image.new("RGB", (W, W), (246, 243, 236))
    d = ImageDraw.Draw(canvas)
    big = ImageFont.truetype(str(FONTS / "Nunito-Black.ttf"), 92)
    lab = ImageFont.truetype(str(FONTS / "Poppins-SemiBold.ttf"), 38)
    small = ImageFont.truetype(str(FONTS / "Poppins-Regular.ttf"), 34)
    ink = (40, 34, 46)
    t = f"{TITLES[style]}: all {n} buildings"
    d.text(((W - d.textlength(t, font=big)) / 2, 70), t, font=big, fill=ink)
    for i, (folder, (title, _)) in enumerate(blds.items()):
        im = crop(IMG / f"{folder}.png")
        im = ImageOps.contain(im, (cell_w - 40, cell_h - 80), Image.LANCZOS)
        cx, cy = (i % cols) * cell_w, head + (i // cols) * cell_h
        if i // cols == rows - 1:  # centre a short last row
            cx += (cols - (n - (rows - 1) * cols)) * cell_w // 2
        canvas.paste(im, (cx + (cell_w - im.width) // 2, cy + (cell_h - 70 - im.height)))
        name = title.replace("Victorian ", "").replace("Gingerbread ", "")
        d.text((cx + (cell_w - d.textlength(name, font=lab)) / 2, cy + cell_h - 62), name, font=lab, fill=ink)
    note = "3D renders of the files you download, not photos. Sizes differ; each README gives its own."
    d.text(((W - d.textlength(note, font=small)) / 2, W - foot + 30), note, font=small, fill=(100, 94, 108))
    out = IMG / f"{style}_village_grid.png"
    canvas.save(out)
    print("wrote", out)


if __name__ == "__main__":
    if "--grid" not in sys.argv:
        render_all()
    for style in ZIPS:
        grid(style)
