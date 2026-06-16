#!/usr/bin/env python3
"""
publish_coloring_drafts.py — Create Etsy DRAFT listings for the fun_basic and
kawaii coloring page packs using the pre-written content in
listing_fun_basic_20260616.json / listing_kawaii_20260616.json.

All 10 listing photos per pack are generated with OpenAI gpt-image-1 via
tools/listing_photo_pipeline.py (the CLAUDE.md-mandated standard):
  - 6 single-design lifestyle/detail shots via generate_verified_photo()
    (images.edit on the REAL coloring page PNG, physics="flat_paper",
    self-verified against the source file)
  - 2 multi-design collection flat lays via build_flat_lay() (AI-generated
    background + pixel-perfect paste of the REAL PNGs — never AI-rendered,
    per the "garbles small text with 5+ inputs" rule)
  - 2 informational cards (what's included / how to print) — AI-generated
    background + a real page thumbnail pasted in + PIL text overlay,
    matching the SS-series "infographics: images.generate background + PIL
    text overlay" rule

Listings are created with state="draft" and this script NEVER calls
update_listing(..., {"state": "active"}) — Scott reviews photos, title,
description, and price before anything goes live.

Usage:
    python tools/publish_coloring_drafts.py --dry-run     # build photos only, no API calls
    python tools/publish_coloring_drafts.py                # build photos + create both drafts
    python tools/publish_coloring_drafts.py --pack kawaii  # just one pack
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont

from tools.etsy_api import EtsyAPIClient
from tools.listing_photo_pipeline import (
    PhotoResult,
    _client,
    build_flat_lay,
    generate_verified_photo,
)

CP_DIR = ROOT / "data" / "digital_products" / "coloring_pages"
SETS_DIR = CP_DIR / "sets"
PHOTO_ROOT = CP_DIR / "_listing_photos"

PRICE_FLOOR = 4.99  # etsy_api.pre_publish_gate enforces this minimum — the
                     # pre-written $3.99 in the listing JSONs is bumped up to
                     # this floor (still ends in .99) so the listing can be created.

PACKS = {
    "fun_basic": {
        "json": CP_DIR / "listing_fun_basic_20260616.json",
        "prefix": "CB",
        "hero_pages": [1, 5, 10, 15, 3, 8],
        "grid_a": [2, 4, 6, 7, 9, 12],
        "grid_b": [11, 13, 14, 16, 18, 20],
        "card_thumb": 1,
        "lifestyle_props": (
            "a few scattered crayons in primary colors (red, blue, yellow, green), "
            "a small wooden crayon box, a child's light wood desk"
        ),
        "bg_prompt": (
            "Overhead flat-lay background photo: warm light wood desk surface, "
            "a loose scatter of bright primary-colored crayons along the edges "
            "of the frame, a couple of small wooden alphabet blocks in a corner. "
            "Bright clean natural daylight, no text, no watermark, no logos, "
            "center area left clean and uncluttered."
        ),
    },
    "kawaii": {
        "json": CP_DIR / "listing_kawaii_20260616.json",
        "prefix": "CP",
        "hero_pages": [1, 5, 10, 15, 3, 8],
        "grid_a": [2, 4, 6, 7, 9, 12],
        "grid_b": [11, 13, 14, 16, 18, 20],
        "card_thumb": 1,
        "lifestyle_props": (
            "a tin of colored pencils fanned open, a small watercolor palette, "
            "a sprig of dried baby's breath, a cream linen-textured desk"
        ),
        "bg_prompt": (
            "Overhead flat-lay background photo: soft cream linen-textured desk "
            "surface, a tin of colored pencils and a small watercolor palette "
            "tucked in one corner, a sprig of dried flowers in another corner. "
            "Bright soft natural daylight, no text, no watermark, no logos, "
            "center area left clean and uncluttered."
        ),
    },
}


def page_path(prefix: str, n: int) -> Path:
    return CP_DIR / f"{prefix}{n:03d}_coloring.png"


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def load_font_regular(size: int) -> ImageFont.FreeTypeFont:
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def build_description(content: dict) -> str:
    d = content["description"]
    lines: list[str] = [d["hook"], ""]
    lines += ["━━━━━━━━━━━━━━━━━━━━━━━━", "📦 WHAT'S INCLUDED", "━━━━━━━━━━━━━━━━━━━━━━━━"]
    lines += [f"✅ {item}" for item in d["whats_included"]]
    lines += ["", d["disclaimer"], ""]
    lines += ["━━━━━━━━━━━━━━━━━━━━━━━━", "🖨️ HOW TO PRINT & COLOR", "━━━━━━━━━━━━━━━━━━━━━━━━"]
    lines += [
        "1. Download the ZIP files instantly from Etsy after purchase",
        "2. Unzip and open any page on your computer, tablet, or phone",
        '3. Print at home on standard 8.5x11" paper, or at any print shop',
        "4. Color with crayons, markers, colored pencils, or watercolors",
        "5. Re-print and color again as many times as you like",
        "",
    ]
    lines += ["━━━━━━━━━━━━━━━━━━━━━━━━", "❓ FAQ", "━━━━━━━━━━━━━━━━━━━━━━━━"]
    lines += [
        "Q: Is this a physical coloring book?",
        "A: No — this is a digital download only. You'll receive PNG files instantly "
        "after purchase, ready to print at home.",
        "",
        "Q: How many times can I print these?",
        "A: Unlimited! Print as many copies as you want for personal or family use.",
        "",
        "Q: What size should I print at?",
        'A: Each file is 2400×2400px, which prints beautifully at 8x8", 8x10", or A4.',
        "",
        "Q: Can I use these for a classroom or event?",
        "A: This license is for personal use only. For classroom or group use, please "
        "send a custom order request.",
        "",
        "Q: Can I sell prints made from these files?",
        "A: No — personal use only, not for resale or redistribution.",
        "",
    ]
    lines += ["━━━━━━━━━━━━━━━━━━━━━━━━", "🤖 ABOUT THIS DESIGN", "━━━━━━━━━━━━━━━━━━━━━━━━"]
    lines += [d["ai_disclosure"], ""]
    lines += ["━━━━━━━━━━━━━━━━━━━━━━━━", "© COPYRIGHT", "━━━━━━━━━━━━━━━━━━━━━━━━"]
    lines += ["© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use."]
    return "\n".join(lines)


GRID_LAYOUT_6 = [
    (60, 390, 720), (840, 390, 720), (1620, 390, 720),
    (60, 1170, 720), (840, 1170, 720), (1620, 1170, 720),
]


def _wrap_draw(draw, xy, text, font, fill, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + 10
    return y


def build_info_card(
    bg_path: Path,
    thumb_path: Path,
    title: str,
    bullets: list[str],
    out_path: Path,
    accent=(120, 90, 200),
) -> Path:
    """AI-generated background + a real coloring-page thumbnail + PIL text overlay."""
    canvas = Image.open(bg_path).convert("RGB").resize((2400, 2400), Image.LANCZOS)

    # Paste a real page thumbnail, bottom-left, with rounded corner + shadow
    thumb_size = 700
    thumb = Image.open(thumb_path).convert("RGB").resize((thumb_size, thumb_size), Image.LANCZOS)
    tx, ty = 160, 2400 - thumb_size - 160
    canvas.paste(thumb, (tx, ty))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([tx - 6, ty - 6, tx + thumb_size + 6, ty + thumb_size + 6], outline=accent, width=6)

    # Semi-transparent text panel, right side
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    panel = [1020, 160, 2240, 2240]
    odraw.rounded_rectangle(panel, radius=40, fill=(255, 255, 255, 235))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    title_font = load_font(78)
    body_font = load_font_regular(54)

    y = 240
    _wrap_draw(draw, (1080, y), title, title_font, accent, panel[2] - 1080 - 60)
    y += 160

    for b in bullets:
        draw.ellipse([1080, y + 14, 1110, y + 44], fill=accent)
        y = _wrap_draw(draw, (1140, y), b, body_font, (40, 30, 30), panel[2] - 1140 - 60)
        y += 30

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, "JPEG", quality=95, dpi=(300, 300))
    print(f"  ✓ Info card saved: {out_path}")
    return out_path


def generate_pack_photos(pack_name: str, cfg: dict, client) -> list[Path]:
    out_dir = PHOTO_ROOT / pack_name
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = cfg["prefix"]
    photos: list[Path] = []

    print(f"\n=== Generating photos for pack: {pack_name} ===")

    # Slots 1,2,3,4,9,10 — single real design, AI-rendered lifestyle/detail shots
    hero_scenes = [
        (
            "SUBJECT: a single printed coloring page lying perfectly flat, centered, "
            "on the desk surface, filling 65% of the frame.\n"
            f"PROPS (3 max): {cfg['lifestyle_props']}.\n"
            "LIGHTING: soft diffused natural window light from the LEFT, warm white "
            "balance, gentle shadow to the right.\n"
            "CAMERA: 50mm equivalent, 20-degree elevated angle.\n"
            "CONSTRAINT: the page must remain a plain black-outline line drawing on "
            "white, completely UNCOLORED — no crayon marks or fills on the page "
            "itself. No hands, no people, no text overlays, no watermarks."
        ),
        (
            "SUBJECT: a single printed coloring page lying flat on the desk, angled "
            "slightly, filling 60% of the frame.\n"
            f"PROPS (3 max): {cfg['lifestyle_props']}.\n"
            "LIGHTING: bright even natural daylight, no harsh shadows.\n"
            "CAMERA: 50mm equivalent, eye-level angle, slight depth of field on props.\n"
            "CONSTRAINT: the page remains a plain black-outline line drawing on white, "
            "completely UNCOLORED. No hands, no people, no text overlays."
        ),
        (
            "SUBJECT: extreme close-up / macro detail shot of the printed coloring "
            "page, camera close enough that the crisp black linework fills 85% of "
            "the frame, page lying perfectly flat.\n"
            "PROPS: none — just the page and desk surface at the edges.\n"
            "LIGHTING: bright even studio-style light, sharp focus across the whole page.\n"
            "CAMERA: macro lens equivalent, straight-on overhead angle.\n"
            "CONSTRAINT: the page remains a plain black-outline line drawing on white, "
            "completely UNCOLORED. No hands, no people, no text overlays."
        ),
        (
            "SUBJECT: a single printed coloring page resting on the desk next to an "
            "open box/tin of coloring supplies, page filling 55% of the frame.\n"
            f"PROPS (3 max): {cfg['lifestyle_props']}.\n"
            "LIGHTING: warm cozy afternoon light from the upper-left.\n"
            "CAMERA: 50mm equivalent, 25-degree elevated angle.\n"
            "CONSTRAINT: the page remains a plain black-outline line drawing on white, "
            "completely UNCOLORED. No hands, no people, no text overlays."
        ),
        (
            "SUBJECT: close-up detail shot of a different printed coloring page, "
            "linework filling 80% of frame, page lying perfectly flat.\n"
            "PROPS: none beyond the desk surface visible at the edges.\n"
            "LIGHTING: bright clean daylight, even illumination.\n"
            "CAMERA: macro lens equivalent, slight 10-degree angle.\n"
            "CONSTRAINT: the page remains a plain black-outline line drawing on white, "
            "completely UNCOLORED. No hands, no people, no text overlays."
        ),
        (
            "SUBJECT: a single printed coloring page lying flat on the desk, "
            "filling 60% of the frame, styled as a final beauty shot.\n"
            f"PROPS (3 max): {cfg['lifestyle_props']}.\n"
            "LIGHTING: soft golden-hour side light, long gentle shadow.\n"
            "CAMERA: 50mm equivalent, 20-degree elevated angle.\n"
            "CONSTRAINT: the page remains a plain black-outline line drawing on white, "
            "completely UNCOLORED. No hands, no people, no text overlays."
        ),
    ]

    for i, (pg, scene) in enumerate(zip(cfg["hero_pages"], hero_scenes), start=1):
        design = page_path(prefix, pg)
        out_path = out_dir / f"photo_{i:02d}.jpg"
        result = generate_verified_photo(
            design_paths=[design],
            scene_prompt=scene,
            out_path=out_path,
            physics="flat_paper",
            client=client,
        )
        if result.passed:
            photos.append(result.out_path)
        else:
            print(f"  ⚠ slot {i} failed verification after retries — using best-effort last render unavailable, skipping")

    # Slot 5: collection flat lay A
    bg_a = out_dir / "_bg_collection.jpg"
    if not bg_a.exists():
        print("  Generating shared collection background...")
        resp = client.images.generate(
            model="gpt-image-1", prompt=cfg["bg_prompt"],
            size="1024x1024", quality="high", output_format="png",
        )
        import base64
        Image.open(io.BytesIO(base64.b64decode(resp.data[0].b64_json))).convert("RGB").resize(
            (2400, 2400), Image.LANCZOS
        ).save(bg_a, "JPEG", quality=95)

    grid_a_paths = [page_path(prefix, n) for n in cfg["grid_a"]]
    r = build_flat_lay(grid_a_paths, GRID_LAYOUT_6, bg_a, out_dir / "photo_07.jpg", client=client)
    photos.append(r.out_path)

    grid_b_paths = [page_path(prefix, n) for n in cfg["grid_b"]]
    r = build_flat_lay(grid_b_paths, GRID_LAYOUT_6, bg_a, out_dir / "photo_08.jpg", client=client)
    photos.append(r.out_path)

    # Info cards: what's included + how to print
    thumb = page_path(prefix, cfg["card_thumb"])
    card1 = build_info_card(
        bg_a, thumb, "What's Included",
        [
            "20 unique coloring page PNG files",
            "High resolution 2400×2400px",
            'Prints beautifully at 8x8", 8x10", or A4',
            "Pure black outline on white — zero fills",
            "Instant digital download",
        ],
        out_dir / "photo_09.jpg",
    )
    photos.append(card1)

    card2 = build_info_card(
        bg_a, thumb, "How To Print & Color",
        [
            "1. Download your ZIP files instantly",
            "2. Unzip and open any page",
            "3. Print at home or at a print shop",
            "4. Color with crayons, markers, or pencils",
            "5. Re-print and color again, unlimited",
        ],
        out_dir / "photo_10.jpg",
        accent=(60, 140, 110),
    )
    photos.append(card2)

    print(f"  → {len(photos)}/10 photos generated for {pack_name}")
    return photos


def create_draft_listing(pack_name: str, cfg: dict, photos: list[Path], api: EtsyAPIClient, dry_run: bool) -> dict:
    content = json.loads(cfg["json"].read_text())
    title = content["title"]
    assert len(title) <= 70, f"Title too long ({len(title)}): {title}"

    description = build_description(content)
    listing_body = {
        "title": title,
        "description": description,
        "price": PRICE_FLOOR,
        "quantity": 999,
        "who_made": "i_did",
        "when_made": "made_to_order",
        "is_supply": False,
        "taxonomy_id": 2078,
        "tags": content["tags"],
        "materials": ["digital download", "PNG file", "instant download"],
        "state": "draft",
        "type": "download",
    }

    print(f"\n=== Creating DRAFT listing: {pack_name} ===")
    print(f"  Title ({len(title)} chars): {title}")
    print(f"  Price: ${PRICE_FLOOR} (bumped from ${content['price']} to clear the $4.99 gate floor)")

    if dry_run:
        print("  [DRY] Would create listing + upload 10 photos + 4 ZIPs (draft only, no activation)")
        return {"pack": pack_name, "dry_run": True}

    resp = api.create_listing(listing_body)
    lid = resp["listing_id"]
    print(f"  Created DRAFT listing {lid}")

    for rank, photo in enumerate(photos, start=1):
        try:
            api.upload_listing_image(lid, str(photo), rank=rank)
            time.sleep(2.0)
            print(f"  Photo {rank} uploaded")
        except Exception as exc:
            print(f"  WARN photo {rank}: {exc}")

    for rank, s in enumerate(content["sets"], start=1):
        zip_path = Path(s["zip"])
        try:
            api.upload_listing_file(lid, str(zip_path), rank=rank)
            time.sleep(1.0)
            print(f"  ZIP {rank} uploaded: {zip_path.name}")
        except Exception as exc:
            print(f"  ERROR uploading ZIP {zip_path.name}: {exc}")

    print(f"  ✓ Listing {lid} left in DRAFT state — NOT activated. Scott review required before publish.")
    return {"pack": pack_name, "listing_id": lid, "title": title, "state": "draft"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pack", choices=list(PACKS.keys()))
    ap.add_argument("--skip-photos", action="store_true", help="reuse already-generated photos")
    args = ap.parse_args()

    pack_names = [args.pack] if args.pack else list(PACKS.keys())
    client = None if args.dry_run else _client()
    api = None
    if not args.dry_run:
        api = EtsyAPIClient()

    results = []
    for pack_name in pack_names:
        cfg = PACKS[pack_name]
        out_dir = PHOTO_ROOT / pack_name
        existing = sorted(out_dir.glob("photo_*.jpg")) if args.skip_photos else []
        if existing and len(existing) >= 10:
            photos = existing[:10]
            print(f"\n=== Reusing {len(photos)} existing photos for {pack_name} ===")
        elif args.dry_run:
            print(f"\n=== [DRY] Skipping photo generation for {pack_name} (no OpenAI calls in dry-run) ===")
            photos = []
        else:
            photos = generate_pack_photos(pack_name, cfg, client)

        result = create_draft_listing(pack_name, cfg, photos, api, args.dry_run)
        results.append(result)

    print("\n=== SUMMARY ===")
    for r in results:
        print(r)


if __name__ == "__main__":
    main()
