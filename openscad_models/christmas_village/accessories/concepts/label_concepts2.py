#!/usr/bin/env python3
"""Crop the second accessory batch's three-quarter render to the scene and
name each piece (2026-10-13); the render frames the whole floor plane, so the
scene sits small in it. Positions are read off that render's 1200 px frame.
Also saves the three views as JPG next to the PNGs render_concepts2.py wrote."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONT = HERE.parents[3] / "fonts" / "Montserrat-Bold.ttf"
X0, Y0, X1, Y1, K = 260, 470, 1000, 960, 2
LABELS = [("Carolers", 350, 735), ("Bandstand", 478, 560), ("Frozen fountain", 412, 790), ("Signpost", 500, 665),
          ("Pillar box", 625, 728), ("Town tree", 792, 505), ("Well", 722, 752), ("Chestnut cart", 895, 800),
          ("Steam train", 405, 905), ("Horse sleigh", 705, 895), ("(cottage for scale)", 605, 600)]

if __name__ == "__main__":
    f = ImageFont.truetype(str(FONT), 26)
    im = Image.open(HERE / "images" / "accessories2_three_quarter.png").convert("RGB").crop((X0, Y0, X1, Y1))
    im = im.resize((im.width * K, im.height * K), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    for t, x, y in LABELS:
        X, Y = (x - X0) * K, (y - Y0) * K
        w = d.textlength(t, font=f)
        d.rectangle([X - w / 2 - 8, Y - 4, X + w / 2 + 8, Y + 30], fill=(255, 255, 255))
        d.text((X - w / 2, Y - 2), t, font=f, fill=(40, 44, 52))
    im.save(HERE / "accessories2_scene.jpg", quality=90)
    for v in ("front", "three_quarter", "top"):
        Image.open(HERE / "images" / f"accessories2_{v}.png").convert("RGB").save(
            HERE / "images" / f"accessories2_{v}.jpg", quality=88, optimize=True)
    print("labelled ->", HERE / "accessories2_scene.jpg")
