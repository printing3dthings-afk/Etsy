#!/usr/bin/env python3
"""
Generate all 10 listing photos for SS1001 America 250 3D Sign Pack.

Uses gpt-image-1 images.edit with the actual design previews as input
(per CLAUDE.md cardinal rule: every photo must show the real product).

Photos generated:
  1. Hero gallery wall (3 signs)
  2. Interior mantel / living room
  3. Front porch / outdoor
  4. Tiered tray farmhouse
  5. Yard / garden stake sign
  6. Collection overview (all 5 designs — PIL flat lay)
  7. HOW-TO graphic (Bambu Studio workflow — PIL text)
  8. Detail close-up (one sign)
  9. What's included / specs (PIL text)
  10. Design lineup (all 5 previews — PIL composite)

Output: data/3d_print_signs/america_250/listing_photos/final_v2/
"""

from __future__ import annotations
import base64
import io
import os
import sys
import textwrap
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

client = OpenAI()

ROOT = Path(__file__).parent.parent
DESIGN_DIR = ROOT / "data" / "3d_print_signs" / "america_250"
OUT_DIR = DESIGN_DIR / "listing_photos" / "final_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DESIGNS = {
    # Vol 1 — original 5 (3-color: White/Navy/Red)
    "america_bold": DESIGN_DIR / "01_america250_america_bold" / "preview.jpg",
    "star_badge":   DESIGN_DIR / "02_america250_star_badge"   / "preview.jpg",
    "freedom_sign": DESIGN_DIR / "03_america250_freedom_sign" / "preview.jpg",
    "happy_4th":    DESIGN_DIR / "04_america250_happy_4th"    / "preview.jpg",
    "land_free":    DESIGN_DIR / "05_america250_land_free"    / "preview.jpg",
    # Vol 2 — 4-color originals (Cream/Navy/Red/Gold)
    "banner":       DESIGN_DIR / "07_america250_banner_4c"    / "preview.jpg",
    "burst":        DESIGN_DIR / "08_america250_burst_4c"     / "preview.jpg",
    "seal":         DESIGN_DIR / "09_america250_seal_4c"      / "preview.jpg",
    "shield_4c":    DESIGN_DIR / "10_america250_shield_4c"    / "preview.jpg",
    "stamp":        DESIGN_DIR / "11_america250_stamp_4c"     / "preview.jpg",
}

DESIGNS_VOL1 = {k: v for k, v in list(DESIGNS.items())[:5]}
DESIGNS_VOL2 = {k: v for k, v in list(DESIGNS.items())[5:]}

FINAL_SIZE = 2400

# ── Shared language ────────────────────────────────────────────────────────────

STYLE = (
    "Photography style: bright warm editorial Etsy product photography. "
    "Warm cream walls and natural linen/oak surfaces. "
    "Soft diffused window light from the left, warm white balance, gentle shadow to right. "
    "No people, no hands, no text overlays, no watermarks. Square 1:1 format."
)

SIGN_RENDER = (
    "The input image shows the flat 2D design layout for a 3D printed wall sign. "
    "Render it as a physical multi-color FDM 3D printed sign with these exact properties: "
    "cream/off-white PLA base plate 4mm thick with a slight bevel on all edges; "
    "the text and design elements are raised 2mm above the base in "
    "deep navy blue PLA and deep patriotic red PLA, exactly matching the layout in the input image. "
    "The face of the sign is perfectly smooth (printed face-down on textured PEI). "
    "Subtle layer lines visible on the side edges only. "
    "Preserve the EXACT design: same text content, same star positions, same color regions as the input."
)


# ── Fonts ─────────────────────────────────────────────────────────────────────

def _fonts():
    try:
        lg  = ImageFont.truetype("/usr/local/share/fonts/google/Anton-Regular.ttf",  90)
        md  = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf",  56)
        sm  = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf",  44)
        xs  = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf",  34)
        bdg = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf",  42)
    except Exception:
        lg = md = sm = xs = bdg = ImageFont.load_default()
    return lg, md, sm, xs, bdg


# ── Badge overlay (required on every lifestyle slot 1-6) ──────────────────────

def add_digital_badge(img: Image.Image) -> Image.Image:
    """Stamp 'DIGITAL FILE — SVG DOWNLOAD' badge in top-left corner."""
    draw = ImageDraw.Draw(img)
    NAVY = (27, 58, 104)
    _, _, _, _, bdg = _fonts()
    text = "DIGITAL FILE — SVG DOWNLOAD"
    bbox = draw.textbbox((0, 0), text, font=bdg)
    pad_x, pad_y = 22, 12
    w = (bbox[2] - bbox[0]) + 2 * pad_x
    h = (bbox[3] - bbox[1]) + 2 * pad_y
    draw.rectangle([28, 28, 28 + w, 28 + h], fill=NAVY)
    draw.text((28 + pad_x, 28 + pad_y), text, fill="white", font=bdg)
    return img


# ── AI background generator (gpt-image-1 images.generate) ─────────────────────

def generate_bg(prompt: str) -> Image.Image:
    """Return a 2400×2400 AI-generated background image."""
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        quality="medium",
        n=1,
    )
    raw = base64.b64decode(result.data[0].b64_json)
    return Image.open(io.BytesIO(raw)).convert("RGB").resize((FINAL_SIZE, FINAL_SIZE), Image.LANCZOS)


# ── API helper (images.edit — lifestyle shots) ────────────────────────────────

def generate(images: list[Path], prompt: str, out_path: Path, badge: bool = False) -> Path:
    """images.edit call → save at 2400×2400. Set badge=True for lifestyle slots 1-6."""
    print(f"  Generating {out_path.name}...")
    img_files = [open(p, "rb") for p in images]
    try:
        result = client.images.edit(
            model="gpt-image-1",
            image=img_files if len(img_files) > 1 else img_files[0],
            prompt=prompt,
            size="1024x1024",
        )
    finally:
        for f in img_files:
            f.close()

    raw = base64.b64decode(result.data[0].b64_json)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = img.resize((FINAL_SIZE, FINAL_SIZE), Image.LANCZOS)
    if badge:
        img = add_digital_badge(img)
    img.save(out_path, "JPEG", quality=92)
    print(f"    → {out_path.stat().st_size // 1024} KB")
    return out_path


# ── Photo 1 — Hero gallery wall ────────────────────────────────────────────────

def photo_01():
    return generate(
        [DESIGNS["america_bold"], DESIGNS["star_badge"], DESIGNS["freedom_sign"]],
        f"{SIGN_RENDER} "
        "Render THREE 3D printed signs displayed as a gallery wall arrangement on a warm cream "
        "textured plaster wall. LEFT: the rectangular AMERICA BOLD sign (wider, landscape). "
        "CENTER: the circular STAR BADGE sign. RIGHT: the rectangular FREEDOM SIGN (wider, landscape). "
        "Signs are mounted at the same height, evenly spaced, centered in the frame. "
        "Below: a natural oak console table with one small terracotta vase containing dried pampas "
        "grass on the left, and a folded dark navy linen cloth on the right. "
        "Subject fills center 70% of frame. 5% neutral padding at all edges. "
        f"{STYLE}",
        OUT_DIR / "photo_01_hero_gallery_wall.jpg",
        badge=True,
    )


# ── Photo 2 — Interior mantel ──────────────────────────────────────────────────

def photo_02():
    return generate(
        [DESIGNS["land_free"]],
        f"{SIGN_RENDER} "
        "Render ONE 3D printed sign displayed on a fireplace mantel in a cozy living room. "
        "The LAND OF THE FREE sign stands upright, centered on the mantel. "
        "Mantel props: a small potted succulent on the left, a white ceramic pillar candle on the right. "
        "Warm cream plaster wall behind. Warm ambient light. "
        "Subject fills center 65% of frame. "
        f"{STYLE}",
        OUT_DIR / "photo_02_mantel_sign.jpg",
        badge=True,
    )


# ── Photo 3 — Front porch ─────────────────────────────────────────────────────

def photo_03():
    return generate(
        [DESIGNS["happy_4th"]],
        f"{SIGN_RENDER} "
        "Render ONE 3D printed sign mounted on a white painted wood front porch wall beside a door. "
        "The HAPPY 4TH sign is hung at eye level on the exterior wall. "
        "Props visible: a small potted red geranium on porch railing, American flag bunting hint in corner. "
        "Bright natural outdoor summer daylight. "
        "Subject fills center 65% of frame. "
        f"{STYLE}",
        OUT_DIR / "photo_03_porch_sign.jpg",
        badge=True,
    )


# ── Photo 4 — Tiered tray ─────────────────────────────────────────────────────

def photo_04():
    return generate(
        [DESIGNS["star_badge"]],
        f"{SIGN_RENDER} "
        "Render the circular STAR BADGE 3D printed sign displayed on the second tier of a white "
        "farmhouse tiered tray on a kitchen counter. "
        "The sign leans slightly against the tray back. "
        "Other tray items: small American flag pick, a tiny red berry stem, a cream pillar candle. "
        "Bright clean natural light. "
        "Subject fills center 65% of frame. "
        f"{STYLE}",
        OUT_DIR / "photo_04_tieredtray_sign.jpg",
        badge=True,
    )


# ── Photo 5 — Yard / stake sign ───────────────────────────────────────────────

def photo_05():
    return generate(
        [DESIGNS["america_bold"]],
        f"{SIGN_RENDER} "
        "Render the AMERICA BOLD 3D printed sign mounted on a wooden garden stake in a front yard. "
        "Sign is at standing height, green grass around the base of the stake, "
        "suburban home with white porch slightly blurred in background. "
        "Bright summer daylight. "
        "Subject fills center 65% of frame. "
        f"{STYLE}",
        OUT_DIR / "photo_05_yard_sign.jpg",
        badge=True,
    )


# ── Photo 6 — Collection overview (AI bg + PIL flat lay) ─────────────────────

def photo_06():
    """OpenAI background + PIL flat lay of all 10 design previews — 2 rows of 5."""
    out_path = OUT_DIR / "photo_06_collection_overview.jpg"
    print(f"  Generating {out_path.name} (AI bg + PIL flat lay — 10 designs)...")

    NAVY = (27, 58, 104)
    RED  = (178, 34, 52)
    CANVAS = FINAL_SIZE
    BORDER = 50
    GAP = 18

    canvas = generate_bg(
        "Warm cream natural linen textured flat lay background, overhead photography, "
        "soft even diffused lighting, no objects, no shadows. Square format."
    )
    draw = ImageDraw.Draw(canvas)

    # Header band
    draw.rectangle([0, 0, CANVAS, 130], fill=NAVY)
    try:
        font_hdr = ImageFont.truetype("/usr/local/share/fonts/google/Anton-Regular.ttf", 70)
        font_sub = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf", 36)
        font_lbl = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf", 28)
    except Exception:
        font_hdr = font_sub = font_lbl = ImageFont.load_default()
    BG_COLOR = (245, 240, 230)  # fallback (not used when AI bg is active)

    draw.text((CANVAS // 2, 50), "10 DESIGNS INCLUDED",
              fill="white", font=font_hdr, anchor="mm")
    draw.text((CANVAS // 2, 105), "America 250th Anniversary · 1776–2026",
              fill=RED, font=font_sub, anchor="mm")

    designs_list = list(DESIGNS.values())
    names_vol1 = ["America Bold", "Star Badge", "Freedom Sign", "Happy 4th", "Land of the Free"]
    names_vol2 = ["Banner", "Burst", "Seal", "Shield", "Stamp"]

    # 2 rows of 5
    col_w = (CANVAS - 2 * BORDER - 4 * GAP) // 5
    col_h = int(col_w * 0.75)
    label_h = 40

    for row in range(2):
        y = 150 + row * (col_h + label_h + GAP + 20)
        names = names_vol1 if row == 0 else names_vol2
        vol_label = "VOL 1" if row == 0 else "VOL 2"
        draw.text((BORDER, y - 5), vol_label, fill=RED, font=font_lbl)
        for col in range(5):
            idx = row * 5 + col
            x = BORDER + col * (col_w + GAP)
            img = Image.open(designs_list[idx]).convert("RGB")
            img = img.resize((col_w, col_h), Image.LANCZOS)
            canvas.paste(img, (x, y))
            draw.text((x + col_w // 2, y + col_h + 22), names[col],
                      fill=NAVY, font=font_lbl, anchor="mm")

    # Footer
    draw.rectangle([0, CANVAS - 80, CANVAS, CANVAS], fill=RED)
    draw.text((CANVAS // 2, CANVAS - 40),
              "Delivered in 2 ZIP files  ·  .3mf + SVG layers  ·  Instant Download",
              fill="white", font=font_lbl, anchor="mm")

    canvas = add_digital_badge(canvas)
    canvas.save(out_path, "JPEG", quality=92)
    print(f"    → {out_path.stat().st_size // 1024} KB")
    return out_path


# ── Photo 7 — How-To Bambu Studio (AI bg + PIL overlay) ──────────────────────

def photo_07():
    """3-step Bambu Studio workflow infographic — OpenAI background + PIL text overlay."""
    out_path = OUT_DIR / "photo_07_bambu_howto.jpg"
    print(f"  Generating {out_path.name} (AI bg + PIL HOW-TO)...")

    NAVY = (27, 58, 104)
    RED = (178, 34, 52)

    canvas = generate_bg(
        "Clean professional white and warm cream presentation background, subtle paper texture, "
        "soft even lighting, no objects. Suitable for an instructional step-by-step infographic. Square format."
    )
    draw = ImageDraw.Draw(canvas)

    try:
        font_lg = ImageFont.truetype("/usr/local/share/fonts/google/Anton-Regular.ttf", 90)
        font_md = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf", 56)
        font_sm = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf", 44)
        font_xs = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf", 34)
    except Exception:
        font_lg = font_md = font_sm = font_xs = ImageFont.load_default()

    # Title
    draw.text((FINAL_SIZE // 2, 110), "HOW TO PRINT IN BAMBU STUDIO",
              fill=NAVY, font=font_md, anchor="mm")
    draw.line([(200, 160), (FINAL_SIZE - 200, 160)], fill=RED, width=4)

    # 3 step boxes
    steps = [
        ("1", "OPEN .3MF FILE", "File → Open → select\n[design].3mf\nAll 3 color parts appear,\npre-positioned at correct Z heights"),
        ("2", "ASSIGN AMS COLORS", "Click each part in Objects panel:\n• base_WHITE → White PLA\n• layer_RED → Deep Red PLA\n• layer_BLUE → Navy Blue PLA"),
        ("3", "SLICE & PRINT", "Click Slice → verify color\nmapping in print dialog\nPress Print!\n(Tip: flip face-down on\ntextured PEI for smooth face)"),
    ]

    box_w = 680
    box_h = 800
    y_box = 220
    x_starts = [(FINAL_SIZE // 2) - box_w - 30,
                (FINAL_SIZE // 2) - box_w // 2,
                (FINAL_SIZE // 2) + 30]
    # 3 columns
    col_w = (FINAL_SIZE - 200) // 3
    for i, (num, title, body) in enumerate(steps):
        x0 = 100 + i * col_w
        x_center = x0 + col_w // 2

        # Circle number
        r = 70
        draw.ellipse([x_center - r, y_box, x_center + r, y_box + r * 2], fill=NAVY)
        draw.text((x_center, y_box + r), num, fill="white", font=font_lg, anchor="mm")

        # Title
        draw.text((x_center, y_box + r * 2 + 50), title, fill=RED, font=font_sm, anchor="mm")

        # Body
        y_body = y_box + r * 2 + 120
        for line in body.split("\n"):
            draw.text((x_center, y_body), line.strip(), fill=(50, 50, 70),
                      font=font_xs, anchor="mm")
            y_body += 52

    # Footer note
    draw.line([(200, FINAL_SIZE - 180), (FINAL_SIZE - 200, FINAL_SIZE - 180)], fill=RED, width=3)
    draw.text((FINAL_SIZE // 2, FINAL_SIZE - 130),
              "✓ Use Color Painting Fill tool (press N) to adjust any color region",
              fill=NAVY, font=font_xs, anchor="mm")
    draw.text((FINAL_SIZE // 2, FINAL_SIZE - 75),
              "America 250 · OnBrandCraftz",
              fill=(150, 120, 90), font=font_xs, anchor="mm")

    canvas.save(out_path, "JPEG", quality=92)
    print(f"    → {out_path.stat().st_size // 1024} KB")
    return out_path


# ── Photo 8 — Detail close-up ────────────────────────────────────────────────

def photo_08():
    return generate(
        [DESIGNS["star_badge"]],
        f"{SIGN_RENDER} "
        "Render a macro close-up photograph of the circular STAR BADGE 3D printed sign. "
        "Sign fills 80% of the frame, photographed straight-on. "
        "The raised navy blue and red design elements clearly show the 2mm height difference "
        "above the cream base. Focus on the crisp layer detail and color separation. "
        "Clean neutral cream background, extreme shallow depth of field at edges. "
        f"{STYLE}",
        OUT_DIR / "photo_08_detail_closeup.jpg",
    )


# ── Photo 9 — What's included (AI bg + PIL overlay) ──────────────────────────

def photo_09():
    """What's included specs graphic — OpenAI background + PIL text overlay."""
    out_path = OUT_DIR / "photo_09_whats_included.jpg"
    print(f"  Generating {out_path.name} (AI bg + PIL specs)...")

    NAVY = (27, 58, 104)
    RED = (178, 34, 52)

    canvas = generate_bg(
        "Clean cream white professional product spec sheet background, "
        "subtle warm linen texture, soft even flat lighting, no objects. Square format."
    )
    draw = ImageDraw.Draw(canvas)

    try:
        font_title = ImageFont.truetype("/usr/local/share/fonts/google/Anton-Regular.ttf", 110)
        font_lg = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf", 62)
        font_md = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf", 50)
        font_sm = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf", 40)
    except Exception:
        font_title = font_lg = font_md = font_sm = ImageFont.load_default()

    # Header
    draw.rectangle([0, 0, FINAL_SIZE, 200], fill=NAVY)
    draw.text((FINAL_SIZE // 2, 100), "WHAT'S INCLUDED", fill="white",
              font=font_title, anchor="mm")

    items = [
        ("✅", "10 America 250 Sign Designs", "Vol 1: America Bold · Star Badge · Freedom Sign · Happy 4th · Land of the Free\nVol 2 (4-color): Banner · Burst · Seal · Shield · Stamp"),
        ("✅", "10 × .3MF FILES", "Pre-assembled — open in Bambu Studio,\nassign AMS colors, slice & print"),
        ("✅", "35 × LAYER SVG FILES", "3–4 color layers per design\n(Cream/Navy/Red/Gold) for custom sizing"),
        ("✅", "2 ZIP FILES", "Vol 1 (designs 1–5) + Vol 2 (designs 6–10)\nBoth instantly downloaded"),
        ("❗", "DIGITAL DOWNLOAD ONLY", "No physical sign included.\nYou print it yourself on your 3D printer."),
    ]

    y = 240
    for icon, title, sub in items:
        # Icon circle
        draw.text((170, y + 40), icon, fill=NAVY, font=font_lg, anchor="mm")
        # Title
        draw.text((230, y + 10), title, fill=NAVY, font=font_md)
        # Sub
        for line in sub.split("\n"):
            y += 50
            draw.text((230, y + 10), line, fill=(80, 80, 100), font=font_sm)
        y += 90
        # Divider
        if icon != "❗":
            draw.line([(100, y - 20), (FINAL_SIZE - 100, y - 20)],
                      fill=(200, 190, 180), width=2)

    # Footer
    draw.rectangle([0, FINAL_SIZE - 100, FINAL_SIZE, FINAL_SIZE], fill=RED)
    draw.text((FINAL_SIZE // 2, FINAL_SIZE - 50),
              "Instant Download · Personal Use + Gifts · OnBrandCraftz",
              fill="white", font=font_sm, anchor="mm")

    canvas.save(out_path, "JPEG", quality=92)
    print(f"    → {out_path.stat().st_size // 1024} KB")
    return out_path


# ── Photo 10 — Design lineup (AI bg + PIL) ────────────────────────────────────

def photo_10():
    """All 10 designs labeled side by side — OpenAI background + PIL paste."""
    out_path = OUT_DIR / "photo_10_design_lineup.jpg"
    print(f"  Generating {out_path.name} (AI bg + PIL lineup)...")

    NAVY = (27, 58, 104)
    RED = (178, 34, 52)

    canvas = generate_bg(
        "Warm cream natural linen textured flat lay background, overhead photography, "
        "even diffused soft lighting, no objects, no shadows. Square format."
    )
    draw = ImageDraw.Draw(canvas)

    try:
        font_title = ImageFont.truetype("/usr/local/share/fonts/google/Anton-Regular.ttf", 100)
        font_sub = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf", 44)
        font_name = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf", 38)
    except Exception:
        font_title = font_sub = font_name = ImageFont.load_default()

    # Header
    draw.rectangle([0, 0, FINAL_SIZE, 190], fill=NAVY)
    draw.text((FINAL_SIZE // 2, 70), "10 DESIGNS IN THIS PACK",
              fill="white", font=font_title, anchor="mm")
    draw.text((FINAL_SIZE // 2, 150), "America 250th Anniversary  ·  1776–2026",
              fill=RED, font=font_sub, anchor="mm")

    all_names = [
        "America Bold", "Star Badge", "Freedom Sign", "Happy 4th", "Land of the Free",
        "Banner", "Burst", "Seal", "Shield", "Stamp",
    ]
    designs_list = list(DESIGNS.values())

    # 2 rows of 5
    BORDER = 50
    GAP = 18
    col_w = (FINAL_SIZE - 2 * BORDER - 4 * GAP) // 5
    col_h = int(col_w * 0.75)
    label_h = 38

    for row in range(2):
        y = 210 + row * (col_h + label_h + GAP)
        row_label = "VOL 1 (Designs 1–5)" if row == 0 else "VOL 2 (Designs 6–10)"
        draw.text((BORDER, y - 4), row_label, fill=RED, font=font_name)
        for col in range(5):
            idx = row * 5 + col
            x = BORDER + col * (col_w + GAP)
            img = Image.open(designs_list[idx]).convert("RGB")
            img = img.resize((col_w, col_h), Image.LANCZOS)
            canvas.paste(img, (x, y))
            draw.text((x + col_w // 2, y + col_h + 22), all_names[idx],
                      fill=NAVY, font=font_name, anchor="mm")

    # Footer
    draw.rectangle([0, FINAL_SIZE - 95, FINAL_SIZE, FINAL_SIZE], fill=RED)
    draw.text((FINAL_SIZE // 2, FINAL_SIZE - 48),
              "All ten included  ·  .3mf + SVG layers  ·  2 ZIP files  ·  Instant Download",
              fill="white", font=font_name, anchor="mm")

    canvas.save(out_path, "JPEG", quality=92)
    print(f"    → {out_path.stat().st_size // 1024} KB")
    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    photos = [
        ("01 Hero gallery wall",   photo_01),
        ("02 Mantel interior",     photo_02),
        ("03 Front porch",         photo_03),
        ("04 Tiered tray",         photo_04),
        ("05 Yard stake sign",     photo_05),
        ("06 Collection overview", photo_06),
        ("07 Bambu how-to",        photo_07),
        ("08 Detail close-up",     photo_08),
        ("09 What's included",     photo_09),
        ("10 Design lineup",       photo_10),
    ]

    which = sys.argv[1:] if len(sys.argv) > 1 else []  # e.g. "1" "2" for specific photos

    print(f"SS1001 Photo Generation — {len(photos)} photos")
    print("=" * 60)
    ok, fail = 0, []

    for label, fn in photos:
        num = label[:2]
        if which and num not in which:
            continue
        try:
            fn()
            ok += 1
        except Exception as e:
            import traceback
            print(f"  ERROR {label}: {e}")
            traceback.print_exc()
            fail.append(label)

    print("=" * 60)
    print(f"  ✓ {ok} photos generated → {OUT_DIR}")
    if fail:
        print(f"  ✗ {len(fail)} failed: {fail}")


if __name__ == "__main__":
    main()
