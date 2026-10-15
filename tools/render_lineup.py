#!/usr/bin/env python3
"""Join several review renders into one labelled side-by-side lineup image.

Used for a series of buildings (the Haunted Town) and for a style study (the
Christmas village concepts), where the point is to compare the pieces at a
glance. Each render is cropped to the same central band and labelled
underneath. Sizes are NOT comparable across tiles: blender_render.py frames
every model to fill its own image, so a 60 mm cottage and a 140 mm manor
come out the same height.

    python3 tools/render_lineup.py -o lineup.png \\
        a_three_quarter.png:"Dickens Victorian" b_three_quarter.png:Gingerbread
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "fonts" / "Fraunces-SemiBold.ttf"

# blender_render.py frames the model in the middle of a square image with
# empty floor around it; this keeps the model and drops most of the floor.
CROP = (0.12, 0.06, 0.88, 0.84)


def build(pairs, out, tile=520, title=None):
    tiles = []
    for path, _ in pairs:
        im = Image.open(path).convert("RGB")
        w, h = im.size
        box = (int(CROP[0] * w), int(CROP[1] * h), int(CROP[2] * w), int(CROP[3] * h))
        im = im.crop(box)
        tiles.append(im.resize((tile, round(tile * im.height / im.width)), Image.LANCZOS))
    th = max(t.height for t in tiles)
    label_h = 70
    title_h = 90 if title else 0
    sheet = Image.new("RGB", (tile * len(tiles), title_h + th + label_h), tiles[0].getpixel((5, 5)))
    draw = ImageDraw.Draw(sheet)
    ink = (52, 50, 56)
    if title:
        f = ImageFont.truetype(str(FONT), 46)
        draw.text((sheet.width / 2, title_h / 2 + 8), title, font=f, fill=ink, anchor="mm")
    f = ImageFont.truetype(str(FONT), 30)
    for i, (t, (_, label)) in enumerate(zip(tiles, pairs)):
        sheet.paste(t, (i * tile, title_h))
        draw.text((i * tile + tile / 2, title_h + th + label_h / 2 - 6), label,
                  font=f, fill=ink, anchor="mm")
    sheet.save(out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("images", nargs="+", help="IMAGE:LABEL")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--title")
    ap.add_argument("--tile", type=int, default=520)
    a = ap.parse_args()
    pairs = []
    for spec in a.images:
        path, _, label = spec.partition(":")
        pairs.append((path, label or Path(path).stem))
    print(build(pairs, a.output, a.tile, a.title))


if __name__ == "__main__":
    main()
