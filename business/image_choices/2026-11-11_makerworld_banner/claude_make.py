#!/usr/bin/env python3
"""Claude's entry for the MakerWorld banner (3000 x 408): the name on the left, and a
street of Christmas village buildings on the right. The buildings are rendered by
cutouts.py from the STL files inside the sale ZIPs, on a transparent background,
so they show the current designs. The name and line sit in the middle 1800 px
that a phone keeps; the street starts inside it and runs on to the right.

    python3 cutouts.py         (once: the building renders)
    python3 claude_make.py     (writes claude.png and claude_phone_crop.png)
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FONTS = ROOT / "assets" / "fonts"
CUTOUTS = HERE / "cutouts"
W, H = 3000, 408
SAFE = (600, 2400)  # the middle 1800 px
NAVY, GOLD, MUTED = (26, 34, 51), (184, 145, 31), (93, 104, 124)
# a street that alternates styles, tallest in the middle
STREET = ["gingerbread_cottage", "victorian_coaching_inn", "gingerbread_candy_cane_chapel",
          "victorian_church", "gingerbread_cocoa_cafe", "victorian_toy_shop", "gingerbread_sweet_shop"]


def cutout(name):
    """The building and its contact shadow, trimmed to what the transparent render holds,
    with the same contrast lift as the store pictures (render_covers.crop), measured on
    the building alone so the empty pixels don't skew it."""
    im = Image.open(CUTOUTS / f"{name}.png").convert("RGBA")
    a = np.asarray(im)[:, :, 3]
    # the shadow catcher leaves a faint shadow over the whole frame, so trim to the
    # building itself plus a margin, and fade the shadow out across that margin
    ys, xs = np.where(a > 250)
    pad = int(0.06 * (ys.max() - ys.min()))
    box = (max(xs.min() - pad, 0), ys.min(), min(xs.max() + pad, im.width - 1) + 1, min(ys.max() + pad, im.height - 1) + 1)
    im = im.crop(box)
    h, w = im.height, im.width
    fx = np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / pad, 0, 1)
    fy = np.clip((h - 1 - np.arange(h)) / pad, 0, 1)
    fade = np.minimum(fx[None, :], fy[:, None])
    alpha_a = np.asarray(im.getchannel("A")).astype(float)
    # below ~50 the shadow is only the floor's faint tint, which reads as a pale panel
    alpha_a = np.where(alpha_a > 250, alpha_a, np.clip((alpha_a - 50) / 200, 0, 1) * 250 * fade)
    rgb, alpha = im.convert("RGB"), Image.fromarray(alpha_a.astype("uint8"))
    solid = alpha.point(lambda v: 255 if v > 250 else 0)
    rgb = Image.blend(rgb, ImageOps.autocontrast(rgb, cutoff=1, preserve_tone=True, mask=solid), 0.5)
    return rgb, alpha


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
    line = ImageFont.truetype(str(FONTS / "Poppins-SemiBold.ttf"), 34)
    x0 = SAFE[0] + 20
    d.text((x0, 92), "OnBrand", font=big, fill=NAVY)
    d.text((x0 + d.textlength("OnBrand", font=big), 92), "Craftz", font=big, fill=GOLD)
    d.rectangle([x0, 236, x0 + 120, 244], fill=GOLD)
    d.text((x0, 262), "Original 3D print designs: Christmas villages and more", font=line, fill=MUTED)
    # the street, right half of the safe zone, bases on the snow line
    left = x0 + d.textlength("Original 3D print designs: Christmas villages and more", font=line) + 60
    right, base = W - 90, H - 34
    items = [cutout(n) for n in STREET]
    heights = [int(330 * f) for f in (0.62, 0.74, 0.92, 1.0, 0.70, 0.86, 0.78)]
    scaled = []
    for (im, m), h in zip(items, heights):
        k = h / im.height
        scaled.append((im.resize((int(im.width * k), h), Image.LANCZOS), m.resize((int(im.width * k), h), Image.LANCZOS)))
    total = sum(s[0].width for s in scaled)
    gap = min(30, max(-30, (right - left - total) / (len(scaled) - 1)))
    x = left
    for im, m in scaled:
        canvas.paste(im, (int(x), base - im.height), m)
        x += im.width + gap
    small = ImageFont.truetype(str(FONTS / "Poppins-Regular.ttf"), 22)
    note = "3D renders of the design files"
    d.text((SAFE[1] - 20 - d.textlength(note, font=small), H - 32), note, font=small, fill=MUTED)
    canvas.save(HERE / "claude.png")
    canvas.crop((SAFE[0], 0, SAFE[1], H)).save(HERE / "claude_phone_crop.png")


if __name__ == "__main__":
    main()
