#!/usr/bin/env python3
"""
commercial_license_photos.py

Generates professional listing photos for commercial license listings and
uploads them to the draft listings on Etsy.

Creates 2 image types:
  1. Hero badge image (2400×2400) — bold shield/badge design, good for thumbnail
  2. "What's covered" infographic (2400×2400) — checkmarks + what the license allows

Usage:
  python tools/commercial_license_photos.py --generate     # create images only
  python tools/commercial_license_photos.py --upload       # generate + upload to Etsy drafts
  python tools/commercial_license_photos.py --upload-one LICENSE_SVG_FLORAL
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE))

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = BASE / "data" / "commercial_license_photos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Fonts
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Color schemes per category
SVG_COLORS = {
    "bg": (245, 248, 255),           # near-white blue tint
    "primary": (30, 60, 140),        # deep navy
    "accent": (52, 120, 210),        # medium blue
    "shield": (30, 60, 140),         # shield fill
    "shield_inner": (255, 255, 255), # white inner badge
    "text_dark": (20, 30, 60),
    "text_light": (255, 255, 255),
    "green": (34, 160, 80),
    "red": (200, 50, 50),
    "gold": (195, 150, 30),
    "gold_light": (255, 215, 100),
}

STICKER_COLORS = {
    "bg": (255, 248, 255),
    "primary": (140, 60, 160),       # purple
    "accent": (200, 110, 220),
    "shield": (140, 60, 160),
    "shield_inner": (255, 255, 255),
    "text_dark": (50, 20, 60),
    "text_light": (255, 255, 255),
    "green": (34, 160, 80),
    "red": (200, 50, 50),
    "gold": (195, 150, 30),
    "gold_light": (255, 215, 100),
}


def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    env_path = BASE / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _load_catalog() -> list[dict]:
    path = BASE / "data" / "product_catalog.json"
    data = json.loads(path.read_text())
    return data if isinstance(data, list) else data.get("products", [])


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _draw_rounded_rect(draw: ImageDraw.Draw, xy, radius: int, fill, outline=None, width=0):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + 2*radius, y0 + 2*radius], fill=fill)
    draw.ellipse([x1 - 2*radius, y0, x1, y0 + 2*radius], fill=fill)
    draw.ellipse([x0, y1 - 2*radius, x0 + 2*radius, y1], fill=fill)
    draw.ellipse([x1 - 2*radius, y1 - 2*radius, x1, y1], fill=fill)
    if outline and width:
        draw.arc([x0, y0, x0 + 2*radius, y0 + 2*radius], 180, 270, fill=outline, width=width)
        draw.arc([x1 - 2*radius, y0, x1, y0 + 2*radius], 270, 360, fill=outline, width=width)
        draw.arc([x0, y1 - 2*radius, x0 + 2*radius, y1], 90, 180, fill=outline, width=width)
        draw.arc([x1 - 2*radius, y1 - 2*radius, x1, y1], 0, 90, fill=outline, width=width)
        draw.line([x0 + radius, y0, x1 - radius, y0], fill=outline, width=width)
        draw.line([x0 + radius, y1, x1 - radius, y1], fill=outline, width=width)
        draw.line([x0, y0 + radius, x0, y1 - radius], fill=outline, width=width)
        draw.line([x1, y0 + radius, x1, y1 - radius], fill=outline, width=width)


def _draw_shield(draw: ImageDraw.Draw, cx: int, cy: int, size: int, colors: dict):
    """Draw a heraldic shield shape."""
    w = size
    h = int(size * 1.2)
    x0 = cx - w // 2
    y0 = cy - h // 2

    # Shield outline points
    shield_pts = [
        (x0, y0),
        (x0 + w, y0),
        (x0 + w, y0 + int(h * 0.65)),
        (cx, y0 + h),
        (x0, y0 + int(h * 0.65)),
    ]

    # Drop shadow
    shadow_pts = [(x + 12, y + 12) for x, y in shield_pts]
    draw.polygon(shadow_pts, fill=(0, 0, 0, 40))

    # Shield fill (primary color)
    draw.polygon(shield_pts, fill=colors["shield"])

    # Inner shield (slightly smaller, white)
    margin = int(size * 0.08)
    inner_pts = [
        (x0 + margin, y0 + margin),
        (x0 + w - margin, y0 + margin),
        (x0 + w - margin, y0 + int(h * 0.65) - margin // 2),
        (cx, y0 + h - margin),
        (x0 + margin, y0 + int(h * 0.65) - margin // 2),
    ]
    draw.polygon(inner_pts, fill=colors["shield_inner"])

    return x0, y0, w, h


def _centered_text(draw, text, font, y, width, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (width - tw) // 2
    draw.text((x, y), text, font=font, fill=color)
    return bbox[3] - bbox[1]


def generate_hero_image(product_id: str, category: str, short_name: str) -> Path:
    """
    2400×2400 hero image: large shield badge with 'COMMERCIAL LICENSE' text,
    a gold ribbon banner, and brand color scheme.
    """
    SIZE = 2400
    colors = SVG_COLORS if "svg" in category else STICKER_COLORS
    is_svg = "svg" in category

    img = Image.new("RGB", (SIZE, SIZE), colors["bg"])
    draw = ImageDraw.Draw(img, "RGBA")

    # Subtle diagonal stripe background
    stripe_color = tuple(max(0, c - 8) for c in colors["bg"])
    for i in range(0, SIZE * 2, 80):
        draw.line([(i, 0), (0, i)], fill=stripe_color, width=2)

    # Corner decorative squares
    corner_size = 120
    corner_color = colors["accent"] + (30,)  # semi-transparent
    for cx_, cy_ in [(0, 0), (SIZE, 0), (0, SIZE), (SIZE, SIZE)]:
        draw.rectangle([cx_ - corner_size, cy_ - corner_size,
                        cx_ + corner_size, cy_ + corner_size],
                       fill=corner_color)

    # Shield — centered slightly above middle
    shield_cx = SIZE // 2
    shield_cy = SIZE // 2 - 120
    shield_size = 480
    sx, sy, sw, sh = _draw_shield(draw, shield_cx, shield_cy, shield_size, colors)

    # Checkmark inside shield
    check_color = colors["green"]
    check_cx = shield_cx
    check_cy = shield_cy - 20
    cs = 120  # checkmark scale
    # Draw bold checkmark: short arm then long arm
    draw.line(
        [(check_cx - cs // 2, check_cy), (check_cx - cs // 8, check_cy + cs // 2)],
        fill=check_color, width=22
    )
    draw.line(
        [(check_cx - cs // 8, check_cy + cs // 2), (check_cx + cs // 2, check_cy - cs // 2)],
        fill=check_color, width=22
    )

    # Gold star accents beside checkmark
    star_pts_l = _star_points(check_cx - 90, check_cy - 80, 22, 11, 5)
    star_pts_r = _star_points(check_cx + 90, check_cy - 80, 22, 11, 5)
    draw.polygon(star_pts_l, fill=colors["gold"])
    draw.polygon(star_pts_r, fill=colors["gold"])

    # === Top header band ===
    band_h = 180
    _draw_rounded_rect(draw, [60, 60, SIZE - 60, 60 + band_h], radius=30, fill=colors["primary"])

    # Header text
    font_header = _font(FONT_BOLD, 72)
    header_text = "COMMERCIAL USE" if is_svg else "COMMERCIAL USE"
    _centered_text(draw, header_text, font_header, 95, SIZE, colors["text_light"])

    font_sub = _font(FONT_REGULAR, 44)
    sub_text = "SVG Bundle License" if is_svg else "Sticker Pack License"
    _centered_text(draw, sub_text, font_sub, 180, SIZE, (200, 220, 255))

    # === Main title ===
    font_title = _font(FONT_BOLD, 88)
    title_y = shield_cy + sh // 2 + 60
    _centered_text(draw, "COMMERCIAL", font_title, title_y, SIZE, colors["primary"])
    _centered_text(draw, "LICENSE", font_title, title_y + 100, SIZE, colors["primary"])

    # === Gold ribbon banner ===
    ribbon_y = title_y + 230
    ribbon_h = 90
    ribbon_margin = 140
    ribbon_pts = [
        (ribbon_margin, ribbon_y),
        (SIZE - ribbon_margin, ribbon_y),
        (SIZE - ribbon_margin + 30, ribbon_y + ribbon_h // 2),
        (SIZE - ribbon_margin, ribbon_y + ribbon_h),
        (ribbon_margin, ribbon_y + ribbon_h),
        (ribbon_margin - 30, ribbon_y + ribbon_h // 2),
    ]
    draw.polygon(ribbon_pts, fill=colors["gold"])

    font_ribbon = _font(FONT_BOLD, 46)
    _centered_text(draw, "OnBrandCraftz  ·  Official License Certificate",
                   font_ribbon, ribbon_y + 22, SIZE, (30, 20, 0))

    # === Bottom: 3 key bullet points ===
    bottom_y = ribbon_y + ribbon_h + 60
    bullets = [
        ("✓  Sell in your Etsy shop", colors["green"]),
        ("✓  Use on physical products", colors["green"]),
        ("✓  Up to 500 units/year", colors["green"]),
    ]
    font_bullet = _font(FONT_BOLD, 52)
    for i, (text, color) in enumerate(bullets):
        _centered_text(draw, text, font_bullet, bottom_y + i * 80, SIZE, color)

    # === Product name chip ===
    chip_y = bottom_y + 290
    chip_text = short_name[:40] if len(short_name) > 40 else short_name
    font_chip = _font(FONT_REGULAR, 40)
    bbox = draw.textbbox((0, 0), chip_text, font=font_chip)
    tw = bbox[2] - bbox[0]
    chip_x = (SIZE - tw - 60) // 2
    _draw_rounded_rect(draw, [chip_x, chip_y, chip_x + tw + 60, chip_y + 60],
                       radius=30, fill=colors["accent"])
    draw.text((chip_x + 30, chip_y + 10), chip_text, font=font_chip, fill=(255, 255, 255))

    # === Instant Download badge (bottom right) ===
    badge_text = "INSTANT DOWNLOAD"
    font_badge = _font(FONT_BOLD, 38)
    bb = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bb[2] - bb[0]
    bx = SIZE - bw - 100
    by = SIZE - 100
    _draw_rounded_rect(draw, [bx - 20, by - 10, bx + bw + 20, by + 50], radius=20,
                       fill=colors["primary"])
    draw.text((bx, by), badge_text, font=font_badge, fill=(255, 255, 255))

    out_path = OUTPUT_DIR / f"{product_id}_hero.jpg"
    img.save(out_path, "JPEG", quality=92)
    return out_path


def _star_points(cx, cy, r_outer, r_inner, n=5):
    pts = []
    for i in range(n * 2):
        angle = math.pi * i / n - math.pi / 2
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts


def generate_coverage_image(product_id: str, category: str) -> Path:
    """
    2400×2400 infographic: two columns — ✓ INCLUDED and ✗ NOT INCLUDED
    """
    SIZE = 2400
    colors = SVG_COLORS if "svg" in category else STICKER_COLORS
    is_svg = "svg" in category

    img = Image.new("RGB", (SIZE, SIZE), colors["bg"])
    draw = ImageDraw.Draw(img)

    # Background stripe
    stripe_color = tuple(max(0, c - 6) for c in colors["bg"])
    for i in range(0, SIZE * 2, 60):
        draw.line([(i, 0), (0, i)], fill=stripe_color, width=1)

    font_title = _font(FONT_BOLD, 96)
    font_sub = _font(FONT_BOLD, 56)
    font_item = _font(FONT_REGULAR, 52)
    font_col = _font(FONT_BOLD, 68)

    # === Header ===
    _draw_rounded_rect(draw, [60, 60, SIZE - 60, 230], radius=30, fill=colors["primary"])
    _centered_text(draw, "WHAT THIS LICENSE COVERS", font_title, 105, SIZE, (255, 255, 255))

    # === Two columns ===
    col_margin = 80
    col_gap = 60
    col_w = (SIZE - col_margin * 2 - col_gap) // 2
    left_x = col_margin
    right_x = col_margin + col_w + col_gap
    col_top = 280

    included = [
        "Sell on Etsy, craft fairs,",
        "  or your own website",
        "Physical products for sale",
        "  (shirts, mugs, tumblers)",
        "Digital products for sale",
        "  (stickers, planners, etc.)",
        "Up to 500 units / year",
        "  per design",
        "Multiple projects — unlimited",
        "  use of any design",
    ]

    not_included = [
        "Reselling the original",
        "  design files",
        "Claiming designs as",
        "  your own original work",
        "Sublicensing to other",
        "  designers",
        "Mass production > 500 units",
        "  (contact us for extended)",
        "Print-on-demand platforms",
        "  reselling base files",
    ]

    # Left column header
    _draw_rounded_rect(draw, [left_x, col_top, left_x + col_w, col_top + 90],
                       radius=20, fill=(34, 160, 80))
    _centered_text(draw, "✓  INCLUDED", font_col, col_top + 15, SIZE // 2, (255, 255, 255))

    # Right column header
    _draw_rounded_rect(draw, [right_x, col_top, right_x + col_w, col_top + 90],
                       radius=20, fill=(200, 50, 50))
    text_right = "✗  NOT INCLUDED"
    bbox = draw.textbbox((0, 0), text_right, font=font_col)
    tw = bbox[2] - bbox[0]
    draw.text((right_x + (col_w - tw) // 2, col_top + 15), text_right,
              font=font_col, fill=(255, 255, 255))

    # Column items
    item_start_y = col_top + 120
    row_h = 70

    for i, text in enumerate(included):
        y = item_start_y + i * row_h
        color = (34, 160, 80) if not text.startswith(" ") else colors["text_dark"]
        draw.text((left_x + 20, y), text.lstrip(), font=font_item, fill=color)

    for i, text in enumerate(not_included):
        y = item_start_y + i * row_h
        color = (200, 50, 50) if not text.startswith(" ") else colors["text_dark"]
        draw.text((right_x + 20, y), text.lstrip(), font=font_item, fill=color)

    # Divider line between columns
    div_x = left_x + col_w + col_gap // 2
    draw.line([(div_x, col_top), (div_x, col_top + 10 * row_h + 120)],
              fill=colors["accent"], width=3)

    # === Bottom band ===
    bottom_y = item_start_y + 10 * row_h + 80
    _draw_rounded_rect(draw, [60, bottom_y, SIZE - 60, SIZE - 60],
                       radius=30, fill=colors["primary"])

    font_bottom = _font(FONT_BOLD, 52)
    font_small = _font(FONT_REGULAR, 42)
    _centered_text(draw, "Save your Etsy order confirmation as your license proof",
                   font_bottom, bottom_y + 40, SIZE, (255, 255, 255))
    _centered_text(draw, "No approval process · Valid immediately · Non-transferable",
                   font_small, bottom_y + 120, SIZE, (200, 220, 255))
    _centered_text(draw, "© OnBrandCraftz",
                   font_small, bottom_y + 190, SIZE, (160, 180, 220))

    out_path = OUTPUT_DIR / f"{product_id}_coverage.jpg"
    img.save(out_path, "JPEG", quality=92)
    return out_path


def generate_images_for_product(product: dict) -> list[Path]:
    pid = product["product_id"]
    cat = product.get("category", "")
    name = product.get("name", pid)
    # Strip "Commercial License | " prefix for display
    short_name = name.replace("Commercial License | ", "").replace(" | Instant Download", "")
    hero = generate_hero_image(pid, cat, short_name)
    coverage = generate_coverage_image(pid, cat)
    print(f"  Generated: {hero.name}, {coverage.name}")
    return [hero, coverage]


def upload_images(product: dict, image_paths: list[Path]) -> bool:
    from tools.etsy_api import EtsyAPIClient, EtsyAPIError

    listing_id = product.get("etsy_listing_id")
    if not listing_id:
        print(f"  No listing ID for {product['product_id']} — skipping upload")
        return False

    client = EtsyAPIClient()
    pid = product["product_id"]

    for rank, img_path in enumerate(image_paths, start=1):
        print(f"  Uploading rank={rank}: {img_path.name} → listing {listing_id}")
        try:
            result = client.upload_listing_image(listing_id, str(img_path), rank=rank)
            img_id = result.get("listing_image_id", "?")
            print(f"    ✓ Uploaded image_id={img_id}")
            time.sleep(2)  # avoid duplicate rank race condition
        except Exception as e:
            print(f"    ✗ Upload failed: {e}")
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate and upload commercial license photos")
    parser.add_argument("--generate", action="store_true", help="Generate images only")
    parser.add_argument("--upload", action="store_true", help="Generate and upload all 11 listings")
    parser.add_argument("--upload-one", metavar="PRODUCT_ID", help="Generate and upload one listing")
    args = parser.parse_args()

    if not (args.generate or args.upload or args.upload_one):
        parser.print_help()
        return

    catalog = _load_catalog()
    licenses = [p for p in catalog if "LICENSE_" in p.get("product_id", "")
                and p.get("etsy_listing_id")]

    if args.upload_one:
        licenses = [p for p in licenses if p["product_id"] == args.upload_one]
        if not licenses:
            print(f"Product '{args.upload_one}' not found.")
            sys.exit(1)

    print(f"\nProcessing {len(licenses)} commercial license listings...\n")

    generated = 0
    uploaded = 0
    for product in licenses:
        pid = product["product_id"]
        print(f"▸ {pid}")
        images = generate_images_for_product(product)
        generated += 1
        if args.upload or args.upload_one:
            ok = upload_images(product, images)
            if ok:
                uploaded += 1

    print(f"\n✓ Generated images for {generated} listings → {OUTPUT_DIR}")
    if args.upload or args.upload_one:
        print(f"✓ Uploaded photos to {uploaded}/{generated} listings on Etsy")


if __name__ == "__main__":
    main()
