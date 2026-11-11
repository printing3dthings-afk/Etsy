#!/usr/bin/env python3
"""Claude's entry for the MakerWorld profile picture: the OBC mark from the links
page (navy disc, gold ring, OBC over CRAFTZ), in Montserrat ExtraBold, the face of
the OBC mark inlaid under the prints. Drawn at 4x and scaled down for clean edges.

    python3 claude_make.py      (writes claude.png, and claude_preview.png at real sizes)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = HERE.parents[2] / "assets" / "fonts"
NAVY, NAVY2, GOLD, PALE = (26, 34, 51), (35, 45, 68), (212, 175, 55), (203, 211, 226)
S = 4000  # drawn at 4x, saved at 1000


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def centred(d, y, text, f, fill, spacing=0):
    w = sum(d.textlength(c, font=f) for c in text) + spacing * (len(text) - 1)
    x = (S - w) / 2
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + spacing


def main():
    im = Image.new("RGB", (S, S), NAVY)
    d = ImageDraw.Draw(im)
    # a soft lighter centre, so the disc doesn't read as a flat hole at small sizes
    for i in range(60):
        r = S * 0.5 * (1 - i / 60)
        t = i / 60
        c = tuple(int(NAVY[k] + (NAVY2[k] - NAVY[k]) * t) for k in range(3))
        d.ellipse([S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r], fill=c)
    # the gold ring sits inside the circle crop with a margin
    m, w = S * 0.08, S * 0.035
    d.ellipse([m, m, S - m, S - m], outline=GOLD, width=int(w))
    big = font("Montserrat-ExtraBold.ttf", int(S * 0.25))
    small = font("Montserrat-ExtraBold.ttf", int(S * 0.075))
    bb = d.textbbox((0, 0), "OBC", font=big)
    centred(d, S * 0.45 - (bb[3] - bb[1]) / 2 - bb[1], "OBC", big, GOLD, spacing=S * 0.01)
    centred(d, S * 0.62, "CRAFTZ", small, PALE, spacing=S * 0.018)
    out = im.resize((1000, 1000), Image.LANCZOS)
    out.save(HERE / "claude.png")
    # how it reads where MakerWorld shows it: circle-cropped at 160, 80 and 40 px
    prev = Image.new("RGB", (420, 180), (245, 245, 245))
    x = 10
    mask_full = Image.new("L", (1000, 1000), 0)
    ImageDraw.Draw(mask_full).ellipse([0, 0, 999, 999], fill=255)
    for size in (160, 80, 40):
        a = out.resize((size, size), Image.LANCZOS)
        prev.paste(a, (x, (180 - size) // 2), mask_full.resize((size, size), Image.LANCZOS))
        x += size + 30
    prev.save(HERE / "claude_preview.png")


if __name__ == "__main__":
    main()
