#!/usr/bin/env python3
"""
add_digital_badge.py — corner badge for SS1001 lifestyle photos (slots 1-6)

Adds a clean "DIGITAL FILE — SVG DOWNLOAD" pill badge to the top-left corner
of every lifestyle photo so a printed-sign scene can never be mistaken for a
physical product. Deterministic PIL — same badge, same position, every photo.

Badged copies are written to listing_photos/final/badged/ — originals untouched.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FINAL  = Path("data/3d_print_signs/america_250/listing_photos/final")
OUT    = FINAL / "badged"
FONTS  = Path("assets/fonts")

NAVY = (27, 37, 80)
GOLD = (200, 148, 62)

PHOTOS = [
    "photo_01_hero_gallery_wall.jpg",
    "photo_02_porch_sign.jpg",
    "photo_03_mantel_sign.jpg",
    "photo_04_tieredtray_sign.jpg",
    "photo_05_yard_sign.jpg",
    "photo_06_collection_overview.jpg",
]

BADGE_TEXT = "DIGITAL FILE — SVG DOWNLOAD"


def add_badge(path: Path) -> Path:
    img = Image.open(path).convert("RGBA")
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(str(FONTS / "Poppins-SemiBold.ttf"), 54)

    pad_x, pad_y = 44, 26
    tw = d.textlength(BADGE_TEXT, font=f)
    th = 54
    x0, y0 = 60, 60
    x1 = x0 + tw + 2 * pad_x
    y1 = y0 + th + 2 * pad_y

    # navy pill with thin gold outline — readable on any scene background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([x0, y0, x1, y1], radius=(y1 - y0) // 2,
                         fill=NAVY + (230,), outline=GOLD + (255,), width=4)
    img.alpha_composite(overlay)
    d = ImageDraw.Draw(img)
    d.text((x0 + pad_x, y0 + pad_y - 6), BADGE_TEXT, font=f, fill=(255, 255, 255))

    out = OUT / path.name
    img.convert("RGB").save(out, "JPEG", quality=95, dpi=(300, 300))
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name in PHOTOS:
        out = add_badge(FINAL / name)
        print(f"✓ {out}")
