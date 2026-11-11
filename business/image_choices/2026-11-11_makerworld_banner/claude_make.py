#!/usr/bin/env python3
"""Claude's entry for the MakerWorld banner (3000 x 408): the name on the left, and a
street of Christmas village buildings on the right. The buildings are the renders
business/store_kit/render_covers.py made from the STL files inside the sale ZIPs,
so they show the current designs (Santa's Workshop v2, not v1). Everything that
matters sits in the middle 1800 px.

    python3 claude_make.py     (writes claude.png and claude_phone_crop.png)
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FONTS = ROOT / "assets" / "fonts"
RENDERS = ROOT / "business" / "store_kit" / "images"
W, H = 3000, 408
SAFE = (600, 2400)  # the middle 1800 px
NAVY, GOLD, MUTED = (26, 34, 51), (184, 145, 31), (93, 104, 124)
# a street that alternates styles, tallest in the middle
STREET = ["gingerbread_cottage", "victorian_coaching_inn", "gingerbread_candy_cane_chapel",
          "victorian_church", "gingerbread_cocoa_cafe", "victorian_toy_shop", "gingerbread_sweet_shop"]


def cutout(name):
    """The building trimmed from its render, with its studio background fading out at the edges."""
    im = Image.open(RENDERS / f"{name}.png").convert("RGB")
    a = np.asarray(im).astype(int)
    bg = a[5, 5]
    fg = np.abs(a - bg).sum(axis=2) > 36
    ys, xs = np.where(fg)
    im = im.crop((xs.min() - 6, ys.min() - 6, xs.max() + 6, ys.max() + 6))
    mask = Image.fromarray((fg[ys.min() - 6:ys.max() + 6, xs.min() - 6:xs.max() + 6] * 255).astype("uint8"))
    mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(3))
    return im, mask


def main():
    bg_top, bg_bot = np.array([246, 243, 236]), np.array([233, 236, 242])
    grad = np.linspace(0, 1, H)[:, None, None]
    canvas = Image.fromarray((bg_top * (1 - grad) + bg_bot * grad).repeat(W, axis=1).astype("uint8"))
    d = ImageDraw.Draw(canvas)
    # a low snow bank the street stands on
    d.rectangle([0, H - 46, W, H], fill=(250, 250, 252))
    d.line([0, H - 46, W, H - 46], fill=(222, 226, 234), width=2)
    # the name and one line, left half of the safe zone
    big = ImageFont.truetype(str(FONTS / "Montserrat-ExtraBold.ttf"), 118)
    line = ImageFont.truetype(str(FONTS / "Poppins-SemiBold.ttf"), 40)
    x0 = SAFE[0] + 20
    d.text((x0, 92), "OnBrand", font=big, fill=NAVY)
    d.text((x0 + d.textlength("OnBrand", font=big), 92), "Craftz", font=big, fill=GOLD)
    d.rectangle([x0, 236, x0 + 120, 244], fill=GOLD)
    d.text((x0, 262), "Original 3D print designs: Christmas villages and more", font=line, fill=MUTED)
    # the street, right half of the safe zone, bases on the snow line
    left, right, base = 1560, SAFE[1] - 20, H - 40
    items = [cutout(n) for n in STREET]
    heights = [int(330 * f) for f in (0.62, 0.74, 0.92, 1.0, 0.70, 0.86, 0.78)]
    scaled = []
    for (im, m), h in zip(items, heights):
        k = h / im.height
        scaled.append((im.resize((int(im.width * k), h), Image.LANCZOS), m.resize((int(im.width * k), h), Image.LANCZOS)))
    total = sum(s[0].width for s in scaled)
    gap = max(-40, (right - left - total) / (len(scaled) - 1))
    x = left
    for im, m in scaled:
        canvas.paste(im, (int(x), base - im.height), m)
        x += im.width + gap
    small = ImageFont.truetype(str(FONTS / "Poppins-Regular.ttf"), 22)
    note = "3D renders of the design files"
    d.text((right - d.textlength(note, font=small), H - 34), note, font=small, fill=MUTED)
    canvas.save(HERE / "claude.png")
    canvas.crop((SAFE[0], 0, SAFE[1], H)).save(HERE / "claude_phone_crop.png")


if __name__ == "__main__":
    main()
