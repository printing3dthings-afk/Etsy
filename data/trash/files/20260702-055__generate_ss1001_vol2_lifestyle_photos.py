#!/usr/bin/env python3
"""
Generate 5 Vol 2 lifestyle photos for SS1001 America 250 3D Sign Pack.

Photo plan:
  1. Hero gallery wall (Banner center + Seal left + Shield right)
  2. Banner living room (Banner above linen sofa)
  3. Seal mantel (Seal circular medallion on fireplace mantel)
  4. Burst tiered tray (Burst disc on farmhouse tiered tray)
  5. Stamp entryway (Stamp rectangle on shiplap entryway wall)

Then update Etsy listing 4520524435, deleting ranks 1-5 and uploading the new photos.

Uses images.edit with the actual preview.jpg files as input per CLAUDE.md cardinal rule.
"""

from __future__ import annotations
import base64
import io
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

# Add tools dir to path for etsy_api import
TOOLS_DIR = Path(__file__).parent
ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

from etsy_api import EtsyAPIClient

client = OpenAI()

DESIGN_DIR = ROOT / "data" / "3d_print_signs" / "america_250"
OUT_DIR = DESIGN_DIR / "listing_photos" / "final_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Vol 2 design previews
BANNER = DESIGN_DIR / "07_america250_banner_4c" / "preview.jpg"
BURST  = DESIGN_DIR / "08_america250_burst_4c"  / "preview.jpg"
SEAL   = DESIGN_DIR / "09_america250_seal_4c"   / "preview.jpg"
SHIELD = DESIGN_DIR / "10_america250_shield_4c" / "preview.jpg"
STAMP  = DESIGN_DIR / "11_america250_stamp_4c"  / "preview.jpg"

FINAL_SIZE = 2400
LISTING_ID = 4520524435

# ── Shared descriptors ─────────────────────────────────────────────────────────

STYLE = (
    "Photography style: bright warm editorial Etsy product photography. "
    "Warm cream walls and natural linen/oak surfaces. "
    "Soft diffused window light from the left, warm white balance, gentle shadow to right. "
    "No people, no hands, no text overlays, no watermarks. Square 1:1 format. "
    "Subject fills center 65% of frame. 5% neutral padding at all edges."
)

SIGN_RENDER_4C = (
    "The input image shows the flat 2D design of a 4-color 3D printed patriotic "
    "America 250th Anniversary sign. Render it as a physical multi-color FDM 3D printed sign: "
    "cream/off-white PLA base plate 4mm thick with subtle beveled edges; "
    "design elements raised 2mm above the base in deep navy blue PLA, patriotic red PLA, "
    "and antique gold PLA. Face is perfectly smooth (printed face-down on textured PEI plate). "
    "Subtle layer lines on side edges only. "
    "Preserve the EXACT colors, text, and proportions from the input image."
)


# ── Fonts ──────────────────────────────────────────────────────────────────────

def _badge_font():
    try:
        return ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf", 42)
    except Exception:
        return ImageFont.load_default()


# ── Badge overlay (required on every lifestyle slot 1-6) ──────────────────────

def add_digital_badge(img: Image.Image) -> Image.Image:
    """Stamp 'DIGITAL FILE — SVG DOWNLOAD' badge in top-left corner."""
    draw = ImageDraw.Draw(img)
    NAVY = (27, 58, 104)
    bdg = _badge_font()
    text = "DIGITAL FILE — SVG DOWNLOAD"
    bbox = draw.textbbox((0, 0), text, font=bdg)
    pad_x, pad_y = 22, 12
    w = (bbox[2] - bbox[0]) + 2 * pad_x
    h = (bbox[3] - bbox[1]) + 2 * pad_y
    draw.rectangle([28, 28, 28 + w, 28 + h], fill=NAVY)
    draw.text((28 + pad_x, 28 + pad_y), text, fill="white", font=bdg)
    return img


# ── images.edit helper ─────────────────────────────────────────────────────────

def generate(images: list[Path], prompt: str, out_path: Path) -> Path:
    """Call images.edit with real product files, resize to 2400×2400, add badge, save."""
    print(f"  Generating {out_path.name} ...")
    img_files = [open(p, "rb") for p in images]
    try:
        result = client.images.edit(
            model="gpt-image-1",
            image=img_files if len(img_files) > 1 else img_files[0],
            prompt=prompt,
            size="1024x1024",
            quality="high",
        )
    finally:
        for f in img_files:
            f.close()

    raw = base64.b64decode(result.data[0].b64_json)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = img.resize((FINAL_SIZE, FINAL_SIZE), Image.LANCZOS)
    img = add_digital_badge(img)
    img.save(out_path, "JPEG", quality=92)
    size_kb = out_path.stat().st_size // 1024
    print(f"    → saved {out_path.name} ({size_kb} KB)")
    return out_path


# ── Photo 1 — Hero gallery wall ────────────────────────────────────────────────

def photo_01():
    return generate(
        [BANNER, SEAL, SHIELD],
        f"{SIGN_RENDER_4C} "
        "Render THREE 3D printed patriotic signs displayed as a gallery wall arrangement on a warm cream "
        "textured plaster wall. CENTER (largest): the horizontal rectangle BANNER sign (landscape orientation). "
        "LEFT: the circular SEAL medallion sign. RIGHT: the pentagon SHIELD sign. "
        "All three signs mounted at the same height, evenly spaced, centered in frame. "
        "Below the signs: a natural oak console table with a terracotta vase containing dried pampas "
        "grass on the left, and a folded navy linen cloth on the right. "
        f"{STYLE}",
        OUT_DIR / "photo_01_hero_gallery_wall_v2.jpg",
    )


# ── Photo 2 — Banner living room ───────────────────────────────────────────────

def photo_02():
    return generate(
        [BANNER],
        f"{SIGN_RENDER_4C} "
        "Render the horizontal rectangle BANNER 3D printed sign hung on a warm cream linen textured plaster "
        "wall above a light cream linen sofa. The sign is centered horizontally above the sofa back. "
        "One sage green throw pillow visible on the sofa. "
        "A small trailing pothos plant on a natural oak side table at the right edge of frame. "
        "Morning window light from the left, warm white balance. "
        f"{STYLE}",
        OUT_DIR / "photo_02_banner_living_room.jpg",
    )


# ── Photo 3 — Seal mantel ─────────────────────────────────────────────────────

def photo_03():
    return generate(
        [SEAL],
        f"{SIGN_RENDER_4C} "
        "Render the circular SEAL medallion 3D printed sign displayed upright, centered on a fireplace mantel. "
        "The mantel is cream stone or white-painted brick. "
        "Props: a small cream ceramic candle on the left side of the mantel, "
        "a tiny dried eucalyptus sprig in a narrow white ceramic vase on the right side. "
        "Warm ambient light, cozy living room atmosphere. "
        f"{STYLE}",
        OUT_DIR / "photo_03_seal_mantel.jpg",
    )


# ── Photo 4 — Burst tiered tray ───────────────────────────────────────────────

def photo_04():
    return generate(
        [BURST],
        f"{SIGN_RENDER_4C} "
        "Render the circular BURST disc 3D printed sign displayed on the top tier of a white farmhouse "
        "tiered tray sitting on a kitchen counter. The sign leans slightly against the back of the top tier. "
        "On the lower tier: a small American flag pick, a tiny red berry sprig, a cream pillar candle. "
        "Bright clean natural light from the left. Kitchen counter surface visible below. "
        f"{STYLE}",
        OUT_DIR / "photo_04_burst_tieredtray.jpg",
    )


# ── Photo 5 — Stamp entryway ──────────────────────────────────────────────────

def photo_05():
    return generate(
        [STAMP],
        f"{SIGN_RENDER_4C} "
        "Render the upright rectangle STAMP 3D printed sign mounted on a white shiplap entryway wall "
        "beside a door. The sign is at eye level on the wall. "
        "A small potted red geranium visible on a wooden bench below at the base. "
        "Bright outdoor-adjacent natural light, clean welcoming atmosphere. "
        f"{STYLE}",
        OUT_DIR / "photo_05_stamp_entryway.jpg",
    )


# ── Etsy listing update ────────────────────────────────────────────────────────

def update_etsy_listing(photo_paths: list[Path]) -> None:
    """Delete ranks 1-5 from the listing and upload the 5 new Vol 2 photos."""
    etsy = EtsyAPIClient()

    print(f"\n  Fetching current images for listing {LISTING_ID} ...")
    images = etsy.get_listing_images(LISTING_ID)
    print(f"  Found {len(images)} existing images.")

    # Sort by rank so we delete in order
    images_sorted = sorted(images, key=lambda x: x.get("rank", 99))

    # Delete images at ranks 1-5
    deleted = 0
    for img in images_sorted:
        rank = img.get("rank", 99)
        if rank <= 5:
            img_id = img["listing_image_id"]
            print(f"  Deleting image rank={rank} id={img_id} ...")
            etsy.delete_listing_image(LISTING_ID, img_id)
            deleted += 1
            time.sleep(1)

    print(f"  Deleted {deleted} old lifestyle photos.")

    # Upload new photos at ranks 1-5
    for rank, photo_path in enumerate(photo_paths, start=1):
        print(f"  Uploading {photo_path.name} at rank {rank} ...")
        result = etsy.upload_listing_image(LISTING_ID, str(photo_path), rank=rank)
        print(f"    → uploaded listing_image_id={result.get('listing_image_id')}")
        time.sleep(2)  # Required delay between uploads (per CLAUDE.md)

    print("  Etsy listing update complete.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=== SS1001 Vol 2 Lifestyle Photos — Generating 5 photos ===\n")

    photos = []
    photos.append(photo_01())
    photos.append(photo_02())
    photos.append(photo_03())
    photos.append(photo_04())
    photos.append(photo_05())

    print(f"\nAll 5 photos generated in {OUT_DIR}")
    for p in photos:
        print(f"  {p.name}")

    print(f"\n=== Updating Etsy listing {LISTING_ID} ===")
    update_etsy_listing(photos)

    print("\nDone.")


if __name__ == "__main__":
    main()
