#!/usr/bin/env python3
"""The three built lanterns side by side, in colour above and lit below
(2026-10-13): lanterns_built.jpg."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONT = HERE.parents[1] / "fonts" / "Montserrat-Bold.ttf"
ROWS = [("colour_three_quarter", "in colour"), ("night_front", "printed in white, lit by a tealight (render, not a photo)")]
LANTERNS = [("hex_lantern", "Hex carriage lantern"), ("drum_lantern", "Panorama drum"), ("gift_box_lantern", "Gift box")]
T = 700


# The renders frame their object about the middle; the floor's gradient
# defeats any background test, so the crop is a fixed square there.
CROPS = {"colour_three_quarter": (600, 500, 780), "night_front": (550, 520, 900)}


def crop(path, view):
    cx, cy, s = CROPS[view]
    im = Image.open(path).convert("RGB")
    return im.crop((cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2)).resize((T, T), Image.LANCZOS)


if __name__ == "__main__":
    f, g = ImageFont.truetype(str(FONT), 30), ImageFont.truetype(str(FONT), 20)
    sheet = Image.new("RGB", (T * 3, 50 + (T + 30) * 2), (250, 250, 250))
    d = ImageDraw.Draw(sheet)
    for i, (name, label) in enumerate(LANTERNS):
        d.text((i * T + 14, 10), label, font=f, fill=(40, 44, 52))
        for r, (view, cap) in enumerate(ROWS):
            sheet.paste(crop(HERE / name / "images" / f"{name}_{view}.png", view), (i * T, 50 + r * (T + 30)))
    for r, (_, cap) in enumerate(ROWS):
        d.text((14, 50 + r * (T + 30) + T + 4), cap, font=g, fill=(90, 94, 102))
    sheet.save(HERE / "lanterns_built.jpg", quality=88)
    print("->", HERE / "lanterns_built.jpg")
