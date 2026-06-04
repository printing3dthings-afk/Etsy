#!/usr/bin/env python3
"""
Create TWO new images for every SVG bundle listing:
  rank=1 → 3-product flat lay hero (actual SVG designs composited onto product mockups)
  rank=2 → full bundle grid collage (every design the buyer receives)

Replaces the existing AI-generated fakes with real product composites.
"""

import sys
import os
import time
import json
import base64
import urllib.request
import math
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from etsy_api import EtsyAPIClient, EtsyAPIError

# ── Constants ─────────────────────────────────────────────────────────────────

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
CANVAS = 2400
BG_COLOR = "#FDF8F0"
DARK_STRIP = "#2C2C2C"

FONT_BOLD   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG    = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BASE_PRODUCT_PATHS = {
    "tshirt": Path("/tmp/base_tshirt.png"),
    "hoodie": Path("/tmp/base_hoodie.png"),
    "tote":   Path("/tmp/base_tote.png"),
}

# Design placement on 750×750px product crops (cx, cy of design center)
DESIGN_PLACEMENT = {
    "tshirt": (375, 280),
    "hoodie": (375, 300),
    "tote":   (375, 380),
}

PRODUCT_PROMPTS = {
    "tshirt": (
        "Professional product flat lay photography. A white cotton crew neck t-shirt laid "
        "perfectly flat on a warm cream linen surface. The shirt is smooth with no wrinkles, "
        "front facing up. The center chest area is completely plain and empty. No designs, "
        "logos, text or graphics on the shirt. Clean even natural daylight from above. "
        "Minimal style. No people. Square format, product centered, 20% margin around edges."
    ),
    "hoodie": (
        "Professional product flat lay photography. A white pullover hoodie laid perfectly "
        "flat on a warm cream linen surface. Front facing up, hood folded neatly at top. "
        "Center chest area is completely plain and empty. No designs, logos, text or graphics. "
        "Clean even natural daylight from above. Minimal style. No people. Square format, "
        "product centered, 20% margin around edges."
    ),
    "tote": (
        "Professional product flat lay photography. A natural undyed canvas tote bag lying "
        "flat on a warm cream linen surface. Front face up, handles folded down. The front "
        "panel is completely plain and empty. No designs, logos, text or graphics. Clean even "
        "natural daylight from above. Minimal style. No people. Square format, product "
        "centered, 20% margin around edges."
    ),
}

# Bundle config: name → (svg_dir, listing_id, commercial_listing_id, design_indices, products)
BUNDLES = [
    {
        "slug":         "floral",
        "name":         "Floral SVG Bundle",
        "svg_dir":      "data/svg_pack/SVG",
        "listing_id":   4514130045,
        "commercial_id": 4515439743,
        "design_idx":   [0, 3, 6],
        "products":     ["tote", "tshirt", "hoodie"],
    },
    {
        "slug":         "christian_faith",
        "name":         "Christian Faith SVG Bundle",
        "svg_dir":      "data/faith_pack/SVG",
        "listing_id":   4514134583,
        "commercial_id": 4515439751,
        "design_idx":   [0, 2, 5],
        "products":     ["hoodie", "tote", "tshirt"],
    },
    {
        "slug":         "graduation",
        "name":         "Graduation SVG Bundle 2026",
        "svg_dir":      "data/grad_pack/SVG",
        "listing_id":   4514136783,
        "commercial_id": 4515439755,
        "design_idx":   [0, 2, 4],
        "products":     ["hoodie", "tshirt", "tote"],
    },
    {
        "slug":         "mom_life",
        "name":         "Mom Life SVG Bundle",
        "svg_dir":      "data/mom_life_pack/SVG",
        "listing_id":   4514392281,
        "commercial_id": 4515437432,
        "design_idx":   [0, 1, 4],
        "products":     ["tshirt", "tote", "hoodie"],
    },
    {
        "slug":         "good_vibes",
        "name":         "Good Vibes SVG Bundle",
        "svg_dir":      "data/groovy_pack/SVG",
        "listing_id":   4514536935,
        "commercial_id": 4515439763,
        "design_idx":   [0, 1, 3],
        "products":     ["tshirt", "hoodie", "tote"],
    },
]

REPO_ROOT = Path(__file__).parent.parent


# ── Helpers ───────────────────────────────────────────────────────────────────

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def generate_base_product(product_type: str) -> bool:
    """Call gpt-image-1 to generate a blank product flat lay. Returns True on success."""
    out_path = BASE_PRODUCT_PATHS[product_type]
    if out_path.exists():
        print(f"  [SKIP] Base {product_type} already exists at {out_path}")
        return True

    print(f"  Generating base {product_type} via gpt-image-1 …")
    prompt = PRODUCT_PROMPTS[product_type]
    payload = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "high",
        "output_format": "png",
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_KEY}",
        },
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            img_bytes = base64.b64decode(data["data"][0]["b64_json"])
            out_path.write_bytes(img_bytes)
            print(f"    Saved: {out_path} ({len(img_bytes)//1024} KB)")
            return True
        except Exception as e:
            print(f"    Attempt {attempt+1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(5)
    return False


def render_svg(svg_path: Path, size: int) -> Image.Image | None:
    """Render SVG to RGBA PIL image at `size`×`size`."""
    try:
        png = cairosvg.svg2png(url=str(svg_path), output_width=size, output_height=size)
        return Image.open(BytesIO(png)).convert("RGBA")
    except Exception as e:
        print(f"    [WARN] cairosvg failed on {svg_path.name}: {e}")
        return None


def remove_white_bg(img: Image.Image, threshold: int = 240) -> Image.Image:
    """Make near-white pixels transparent."""
    data = np.array(img)
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    is_white = (r > threshold) & (g > threshold) & (b > threshold)
    data[is_white, 3] = 0
    return Image.fromarray(data, "RGBA")


def composite_design_onto_product(
    product_img: Image.Image,
    svg_img: Image.Image,
    product_type: str,
    panel_size: int = 750,
) -> Image.Image:
    """
    Resize product to panel_size×panel_size, place SVG design at the correct chest/front
    position, return the composited image in RGBA.
    """
    product = product_img.convert("RGBA").resize((panel_size, panel_size), Image.LANCZOS)

    # Design size: ~250px for chest area
    design_size = 250
    cx, cy = DESIGN_PLACEMENT[product_type]

    # Fit design into design_size×design_size preserving aspect ratio
    dw, dh = svg_img.size
    scale = min(design_size / dw, design_size / dh)
    new_w, new_h = int(dw * scale), int(dh * scale)
    design = svg_img.resize((new_w, new_h), Image.LANCZOS)
    design = remove_white_bg(design)

    # Center design at placement point
    px = cx - new_w // 2
    py = cy - new_h // 2

    product.paste(design, (px, py), design)
    return product


# ── Phase 1: Generate base product images ────────────────────────────────────

def phase1_generate_bases() -> bool:
    print("\n" + "=" * 60)
    print("PHASE 1 — Generating base product images")
    print("=" * 60)
    all_ok = True
    for ptype in ["tshirt", "hoodie", "tote"]:
        ok = generate_base_product(ptype)
        if not ok:
            print(f"  [ERROR] Failed to generate base {ptype}")
            all_ok = False
    return all_ok


# ── Phase 2: Build hero flat-lay composite ────────────────────────────────────

def build_hero(bundle: dict) -> Path | None:
    """Build 2400×2400 3-product flat lay hero. Returns path or None."""
    slug = bundle["slug"]
    name = bundle["name"]
    svg_dir = REPO_ROOT / bundle["svg_dir"]
    products = bundle["products"]     # e.g. ["tote", "tshirt", "hoodie"]
    indices  = bundle["design_idx"]   # e.g. [0, 3, 6]

    print(f"\n  [HERO] {name}")

    all_svgs = sorted(svg_dir.glob("*.svg"))
    if len(all_svgs) == 0:
        print(f"    [ERROR] No SVG files found in {svg_dir}")
        return None

    # Load base product images
    bases = {}
    for ptype in set(products):
        p = BASE_PRODUCT_PATHS[ptype]
        if not p.exists():
            print(f"    [ERROR] Base image missing: {p}")
            return None
        bases[ptype] = Image.open(p).convert("RGBA")

    # Canvas: 2400×2400, cream background
    bg = hex_to_rgb(BG_COLOR)
    canvas = Image.new("RGB", (CANVAS, CANVAS), bg)

    panel_size = 750
    gap = 75
    # 3 panels × 750px + 2 gaps × 75px + side margins = 3×750 + 2×75 = 2400 → perfect
    # side margin = (2400 - 3*750 - 2*75) / 2 = (2400 - 2250 - 150) / 2 = 0
    # So panels start at x=0, 825, 1650 with 75px gaps
    panel_xs = [0, panel_size + gap, 2 * (panel_size + gap)]
    panel_y  = (CANVAS - panel_size) // 2  # vertically centered (= 825)

    caption_h = 120
    # We'll draw the caption strip at the bottom

    for i in range(3):
        ptype = products[i]
        idx   = indices[i]

        if idx >= len(all_svgs):
            print(f"    [WARN] Index {idx} out of range ({len(all_svgs)} SVGs), using last")
            idx = len(all_svgs) - 1
        svg_path = all_svgs[idx]

        # Render SVG
        svg_img = render_svg(svg_path, 350)
        if svg_img is None:
            # Try adjacent indices
            for fallback_idx in range(len(all_svgs)):
                svg_img = render_svg(all_svgs[fallback_idx], 350)
                if svg_img is not None:
                    print(f"    Using fallback SVG: {all_svgs[fallback_idx].name}")
                    break
        if svg_img is None:
            print(f"    [ERROR] No SVG could be rendered for panel {i}")
            return None

        print(f"    Panel {i}: {ptype} + {svg_path.name}")

        panel = composite_design_onto_product(bases[ptype], svg_img, ptype, panel_size)

        x = panel_xs[i]
        y = panel_y
        canvas.paste(panel.convert("RGB"), (x, y))

    # Caption strip
    draw = ImageDraw.Draw(canvas)
    strip_y = CANVAS - caption_h
    dark_rgb = hex_to_rgb(DARK_STRIP)
    draw.rectangle([(0, strip_y), (CANVAS, CANVAS)], fill=dark_rgb)

    total_designs = len(all_svgs)
    caption_text = f"{name}  •  {total_designs} Designs Included  •  Cut Files for Cricut & Silhouette"

    try:
        font = ImageFont.truetype(FONT_BOLD, 38)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), caption_text, font=font)
    tw = bbox[2] - bbox[0]
    tx = (CANVAS - tw) // 2
    ty = strip_y + (caption_h - (bbox[3] - bbox[1])) // 2
    draw.text((tx, ty), caption_text, font=font, fill=(255, 255, 255))

    out_path = Path(f"/tmp/svg_hero_{slug}.jpg")
    canvas.save(str(out_path), "JPEG", quality=92)
    print(f"    Saved hero: {out_path} ({out_path.stat().st_size // 1024} KB)")
    return out_path


# ── Phase 3: Build grid collage ───────────────────────────────────────────────

def build_grid(bundle: dict) -> Path | None:
    """Build 2400×2400 full-bundle grid. Returns path or None."""
    slug    = bundle["slug"]
    name    = bundle["name"]
    svg_dir = REPO_ROOT / bundle["svg_dir"]

    print(f"\n  [GRID] {name}")

    all_svgs = sorted(svg_dir.glob("*.svg"))
    if not all_svgs:
        print(f"    [ERROR] No SVG files in {svg_dir}")
        return None

    n = len(all_svgs)

    # Grid dimensions
    if n <= 12:
        cols, rows = 4, 3
    else:  # 13–20
        cols, rows = 5, 4

    print(f"    {n} designs → {cols}×{rows} grid")

    bottom_strip = 80
    available_h = CANVAS - bottom_strip
    cell_gap = 16

    # Cell size: fit cols×rows cells with gaps into available area
    cell_w = (CANVAS - (cols + 1) * cell_gap) // cols
    cell_h = (available_h - (rows + 1) * cell_gap) // rows
    cell_size = min(cell_w, cell_h)

    # Recalculate margins for centering
    total_grid_w = cols * cell_size + (cols - 1) * cell_gap
    total_grid_h = rows * cell_size + (rows - 1) * cell_gap
    margin_x = (CANVAS - total_grid_w) // 2
    margin_y = (available_h - total_grid_h) // 2

    bg = hex_to_rgb(BG_COLOR)
    canvas = Image.new("RGB", (CANVAS, CANVAS), bg)

    inner_size = cell_size - 20  # padding inside cell

    full_rows  = n // cols
    remainder  = n % cols

    for i, svg_path in enumerate(all_svgs):
        if i >= cols * rows:
            break  # skip extras beyond grid capacity

        svg_img = render_svg(svg_path, inner_size)
        if svg_img is None:
            # Draw a placeholder cell
            svg_img = Image.new("RGBA", (inner_size, inner_size), (220, 220, 220, 255))

        row = i // cols
        col = i % cols

        # Center last partial row
        if row == full_rows and remainder > 0:
            start_col = (cols - remainder) // 2
            col = start_col + (i - full_rows * cols)

        cx = margin_x + col * (cell_size + cell_gap)
        cy = margin_y + row * (cell_size + cell_gap)

        # White cell background
        cell_bg = Image.new("RGB", (cell_size, cell_size), (255, 255, 255))
        canvas.paste(cell_bg, (cx, cy))

        # Fit SVG into inner area
        dw, dh = svg_img.size
        scale = min(inner_size / dw, inner_size / dh)
        sw, sh = int(dw * scale), int(dh * scale)
        resized = svg_img.resize((sw, sh), Image.LANCZOS).convert("RGBA")

        # Center within cell
        ox = cx + (cell_size - sw) // 2
        oy = cy + (cell_size - sh) // 2
        # Composite RGBA over white cell
        r, g, b, a = resized.split()
        canvas.paste(resized.convert("RGB"), (ox, oy), a)

    # Bottom strip
    draw = ImageDraw.Draw(canvas)
    strip_y = CANVAS - bottom_strip
    draw.rectangle([(0, strip_y), (CANVAS, CANVAS)], fill=hex_to_rgb(DARK_STRIP))

    caption = f"{name}  •  {n} Designs  •  Commercial License Available"
    try:
        font = ImageFont.truetype(FONT_REG, 32)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), caption, font=font)
    tw = bbox[2] - bbox[0]
    tx = (CANVAS - tw) // 2
    ty = strip_y + (bottom_strip - (bbox[3] - bbox[1])) // 2
    draw.text((tx, ty), caption, font=font, fill=(255, 255, 255))

    out_path = Path(f"/tmp/svg_grid_{slug}.jpg")
    canvas.save(str(out_path), "JPEG", quality=92)
    print(f"    Saved grid: {out_path} ({out_path.stat().st_size // 1024} KB)")
    return out_path


# ── Phase 4: Upload to Etsy ───────────────────────────────────────────────────

def upload_image(client: EtsyAPIClient, listing_id: int, image_path: Path, rank: int, label: str) -> bool:
    """Upload image to listing at given rank. Returns True on success."""
    for attempt in range(2):
        try:
            result = client.upload_listing_image(listing_id, str(image_path), rank=rank)
            img_id = result.get("listing_image_id", "?")
            print(f"      Uploaded rank={rank} → {label} (listing {listing_id}) image_id={img_id}")
            return True
        except EtsyAPIError as e:
            status = getattr(e, "status_code", None)
            if status == 429:
                wait = 10
                print(f"      429 rate limit — waiting {wait}s …")
                time.sleep(wait)
                continue
            print(f"      [ERROR] EtsyAPIError uploading rank={rank} to {label}: {e}")
            return False
        except Exception as e:
            print(f"      [ERROR] Unexpected error uploading rank={rank} to {label}: {e}")
            return False
    return False


def main():
    print("=" * 60)
    print("SVG Bundle Product Hero + Grid Image Generator")
    print("=" * 60)

    if not OPENAI_KEY:
        print("[FATAL] OPENAI_API_KEY not set in .env")
        sys.exit(1)

    client = EtsyAPIClient()
    try:
        client.refresh_access_token()
        print("Etsy token refreshed OK")
    except Exception as e:
        print(f"[WARN] Token refresh: {e}")

    # Phase 1: Generate base product images (once, reused across all bundles)
    bases_ok = phase1_generate_bases()
    if not bases_ok:
        print("\n[FATAL] Could not generate all base product images — aborting")
        sys.exit(1)

    results = {}  # slug → {"hero": bool, "grid": bool, "uploads": int}

    for bundle in BUNDLES:
        slug = bundle["slug"]
        name = bundle["name"]
        print(f"\n{'=' * 60}")
        print(f"Bundle: {name}")

        results[slug] = {"hero_ok": False, "grid_ok": False, "uploads": 0, "upload_total": 4}

        # Phase 2: Hero
        hero_path = build_hero(bundle)
        if hero_path is None:
            print(f"  [SKIP] Hero build failed for {name}")
        else:
            results[slug]["hero_ok"] = True

        # Phase 3: Grid
        grid_path = build_grid(bundle)
        if grid_path is None:
            print(f"  [SKIP] Grid build failed for {name}")
        else:
            results[slug]["grid_ok"] = True

        # Phase 4: Upload to both listing IDs
        print(f"\n  Uploading images …")
        listing_ids = [
            (bundle["listing_id"],   "regular"),
            (bundle["commercial_id"], "commercial"),
        ]

        for lid, label in listing_ids:
            if lid is None:
                results[slug]["upload_total"] -= 2
                continue

            if hero_path is not None:
                ok = upload_image(client, lid, hero_path, rank=1, label=label)
                if ok:
                    results[slug]["uploads"] += 1
                time.sleep(1)

            if grid_path is not None:
                ok = upload_image(client, lid, grid_path, rank=2, label=label)
                if ok:
                    results[slug]["uploads"] += 1
                time.sleep(1)

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    for slug, r in results.items():
        hero_s = "OK" if r["hero_ok"] else "FAIL"
        grid_s = "OK" if r["grid_ok"] else "FAIL"
        up = r["uploads"]
        total = r["upload_total"]
        print(f"  {slug:20s}  hero={hero_s}  grid={grid_s}  uploads={up}/{total}")

    print("\nGenerated files:")
    for slug in [b["slug"] for b in BUNDLES]:
        for prefix in ("svg_hero", "svg_grid"):
            p = Path(f"/tmp/{prefix}_{slug}.jpg")
            if p.exists():
                print(f"  {p}  ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
