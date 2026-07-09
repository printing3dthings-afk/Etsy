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

# Prompts for images.edit() — we pass the SVG design PNG and ask for a realistic product photo
PRODUCT_EDIT_PROMPTS = {
    "tshirt": (
        "Take the graphic design shown in this image and apply it as a screen-printed or "
        "heat-transfer vinyl graphic onto a plain cream-white crew-neck t-shirt laid flat. "
        "PLACEMENT RULES (must follow exactly): "
        "(1) The design must be horizontally centered on the shirt chest. "
        "(2) The design must sit at mid-chest — the vertical center of the design should be "
        "approximately 45% down from the top collar, NOT near the neckline or shoulders. "
        "(3) The design should be about 35-40% of the shirt width. "
        "Reproduce all design colors, text, and graphic elements exactly as shown — do not alter "
        "or simplify the design. "
        "Product setting: flat lay photography on warm cream linen surface, soft even natural "
        "daylight from above, no harsh shadows. Fabric cotton texture visible. Realistic "
        "screen-printed appearance — not floating or pasted. No hands, no mannequin. "
        "Professional Etsy product photography."
    ),
    "hoodie": (
        "Take the graphic design shown in this image and apply it as a screen-printed or "
        "heat-transfer vinyl graphic onto a plain cream-white pullover hoodie laid flat "
        "with the hood folded at the top. "
        "PLACEMENT RULES (must follow exactly): "
        "(1) The design must be horizontally centered on the hoodie chest. "
        "(2) The design must sit at mid-chest level — the vertical center of the design should "
        "be approximately 50-55% down from the very top of the folded hood, well below the hood "
        "opening and kangaroo pocket. NOT near the collar, NOT near the hood. "
        "(3) The design should be about 35-40% of the hoodie width. "
        "Reproduce all design colors, text, and graphic elements exactly as shown. "
        "Product setting: flat lay photography on warm cream linen surface, soft even natural "
        "daylight from above. Fleece fabric texture visible. Realistic screen-printed "
        "appearance. No hands, no mannequin. Professional Etsy product photography."
    ),
    "tote": (
        "Take the graphic design shown in this image and apply it as a screen-printed or "
        "vinyl design onto the front panel of a natural canvas tote bag. "
        "PLACEMENT RULES (must follow exactly): "
        "(1) The design must be horizontally centered on the tote front panel. "
        "(2) The design must be vertically centered on the main body of the bag — centered "
        "between the bottom seam and the handle attachment points, NOT near the handles. "
        "(3) The design should fill about 55-65% of the bag panel width. "
        "Reproduce all design colors, text, and graphic elements exactly as shown. "
        "Product setting: tote bag upright on warm cream linen surface, handles hanging "
        "naturally, soft natural side-lighting from the left. Woven canvas texture visible. "
        "Realistic screen-printed appearance. No hands. Professional Etsy product photography."
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
    {
        "slug":         "western",
        "name":         "Western SVG Bundle",
        "svg_dir":      "data/svg_bundles/western/SVG",
        "listing_id":   None,
        "commercial_id": 4515437442,
        "design_idx":   [0, 3, 7],
        "products":     ["tshirt", "tote", "hoodie"],
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


def generate_product_panel(svg_path: Path, product_type: str, panel_idx: int, slug: str) -> Image.Image | None:
    """
    Use gpt-image-1 images.edit() to generate a realistic product photo with the SVG
    design centered and integrated into the fabric — NOT PIL-pasted at hardcoded coords.
    Returns a 1024×1024 PIL Image or None on failure.
    """
    # Render SVG to PNG bytes
    try:
        png_bytes = cairosvg.svg2png(url=str(svg_path), output_width=800, output_height=800)
    except Exception as e:
        print(f"    [ERROR] cairosvg failed on {svg_path.name}: {e}")
        return None

    prompt = PRODUCT_EDIT_PROMPTS[product_type]

    import io as _io
    import multipart as _mp  # not available; use manual multipart

    # Build multipart form data manually
    boundary = b"----FormBoundary7MA4YWxkTrZu0gW"

    def field(name, value):
        return (
            b"--" + boundary + b"\r\n"
            b'Content-Disposition: form-data; name="' + name.encode() + b'"\r\n\r\n'
            + value.encode() + b"\r\n"
        )

    def file_field(name, filename, content_type, data):
        return (
            b"--" + boundary + b"\r\n"
            + f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
            + f"Content-Type: {content_type}\r\n\r\n".encode()
            + data + b"\r\n"
        )

    body = (
        field("model", "gpt-image-1")
        + field("prompt", prompt)
        + field("size", "1024x1024")
        + field("quality", "high")
        + field("output_format", "png")
        + file_field("image", "design.png", "image/png", png_bytes)
        + b"--" + boundary + b"--\r\n"
    )

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/edits",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": f"multipart/form-data; boundary={boundary.decode()}",
        },
        method="POST",
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read())
            img_bytes = base64.b64decode(data["data"][0]["b64_json"])
            img = Image.open(BytesIO(img_bytes)).convert("RGB")
            print(f"    Panel {panel_idx} ({product_type}): generated via images.edit()")
            return img
        except Exception as e:
            print(f"    Attempt {attempt+1}/3 failed for panel {panel_idx}: {e}")
            if attempt < 2:
                time.sleep(8)
    return None


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


# ── Phase 2: Build hero flat-lay composite via images.edit() ─────────────────

def build_hero(bundle: dict) -> Path | None:
    """
    Build 2400×2400 3-product hero using gpt-image-1 images.edit() for each panel.
    Each panel is a realistic product photo generated by passing the actual SVG design
    to the API — designs are centered at mid-chest, fabric-integrated, not PIL-pasted.
    """
    slug     = bundle["slug"]
    name     = bundle["name"]
    svg_dir  = REPO_ROOT / bundle["svg_dir"]
    products = bundle["products"]   # e.g. ["tote", "tshirt", "hoodie"]
    indices  = bundle["design_idx"] # e.g. [0, 3, 6]

    print(f"\n  [HERO] {name}")

    all_svgs = sorted(svg_dir.glob("*.svg"))
    if not all_svgs:
        print(f"    [ERROR] No SVG files found in {svg_dir}")
        return None

    # Generate 3 product panels via images.edit()
    panels = []
    for i in range(3):
        ptype = products[i]
        idx   = min(indices[i], len(all_svgs) - 1)
        svg_path = all_svgs[idx]
        print(f"    Panel {i}: {ptype} ← {svg_path.name}")

        panel_img = generate_product_panel(svg_path, ptype, i, slug)
        if panel_img is None:
            # Try next SVG as fallback
            for fi in range(len(all_svgs)):
                if fi == idx:
                    continue
                panel_img = generate_product_panel(all_svgs[fi], ptype, i, slug)
                if panel_img is not None:
                    print(f"    Used fallback SVG: {all_svgs[fi].name}")
                    break
        if panel_img is None:
            print(f"    [ERROR] Could not generate panel {i} for {name}")
            return None

        panels.append(panel_img)
        time.sleep(2)  # avoid burst rate limiting between panels

    # Composite 3 panels into 2400×2400 canvas
    # Each panel resized to 800×800, arranged side by side (800×3=2400)
    panel_size = 800
    bg = hex_to_rgb(BG_COLOR)
    canvas = Image.new("RGB", (CANVAS, CANVAS), bg)

    caption_h = 100
    available_h = CANVAS - caption_h
    panel_y = (available_h - panel_size) // 2  # vertically centered in non-caption area

    for i, panel_img in enumerate(panels):
        resized = panel_img.resize((panel_size, panel_size), Image.LANCZOS)
        canvas.paste(resized, (i * panel_size, panel_y))

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

def clear_all_images(client: EtsyAPIClient, listing_id: int, label: str) -> None:
    """Delete all existing images from a listing before uploading fresh ones."""
    try:
        images = client.get_listing_images(listing_id)
        if not images:
            print(f"      No existing images on {label} ({listing_id})")
            return
        print(f"      Clearing {len(images)} image(s) from {label} ({listing_id})")
        for img in images:
            img_id = img.get("listing_image_id")
            if img_id:
                try:
                    client.delete_listing_image(listing_id, img_id)
                    time.sleep(0.4)
                except Exception as e:
                    print(f"      [WARN] delete {img_id}: {e}")
    except Exception as e:
        print(f"      [WARN] clear_all_images failed for {label}: {e}")


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

    results = {}  # slug → {"hero": bool, "grid": bool, "info": bool, "uploads": int}

    for bundle in BUNDLES:
        slug = bundle["slug"]
        name = bundle["name"]
        print(f"\n{'=' * 60}")
        print(f"Bundle: {name}")

        results[slug] = {"hero_ok": False, "grid_ok": False, "info_ok": False,
                         "uploads": 0, "upload_total": 0}

        # Phase 2: Hero — use cached file if already generated
        hero_path = Path(f"/tmp/svg_hero_{slug}.jpg")
        if hero_path.exists():
            print(f"  [CACHE] Hero already at {hero_path} ({hero_path.stat().st_size // 1024} KB)")
            results[slug]["hero_ok"] = True
        else:
            hero_path = build_hero(bundle)
            if hero_path is None:
                print(f"  [SKIP] Hero build failed for {name}")
            else:
                results[slug]["hero_ok"] = True

        # Phase 3: Grid — use cached file if already generated
        grid_path = Path(f"/tmp/svg_grid_{slug}.jpg")
        if grid_path.exists():
            print(f"  [CACHE] Grid already at {grid_path} ({grid_path.stat().st_size // 1024} KB)")
            results[slug]["grid_ok"] = True
        else:
            grid_path = build_grid(bundle)
            if grid_path is None:
                print(f"  [SKIP] Grid build failed for {name}")
                grid_path = None
            else:
                results[slug]["grid_ok"] = True

        # Phase 3b: Info card — re-use from fix_svg_listing_photos.py if available
        info_path = Path(f"/tmp/svg_info_{slug}.jpg")
        if info_path.exists():
            print(f"  [CACHE] Info card at {info_path} ({info_path.stat().st_size // 1024} KB)")
            results[slug]["info_ok"] = True
        else:
            info_path = None

        # Count expected uploads (hero + grid + optional info, per listing)
        img_count = sum([
            hero_path is not None and results[slug]["hero_ok"],
            grid_path is not None and results[slug]["grid_ok"],
            info_path is not None,
        ])

        # Phase 4: Upload to both listing IDs
        print(f"\n  Uploading {img_count} image(s) per listing …")
        listing_ids = [
            (bundle["listing_id"],    "regular"),
            (bundle["commercial_id"], "commercial"),
        ]

        for lid, label in listing_ids:
            if lid is None:
                continue
            results[slug]["upload_total"] += img_count

            # Clear existing images first
            clear_all_images(client, lid, label)
            time.sleep(1)

            if hero_path is not None and results[slug]["hero_ok"]:
                ok = upload_image(client, lid, hero_path, rank=1, label=label)
                if ok:
                    results[slug]["uploads"] += 1
                time.sleep(1.5)

            if grid_path is not None and results[slug]["grid_ok"]:
                ok = upload_image(client, lid, grid_path, rank=2, label=label)
                if ok:
                    results[slug]["uploads"] += 1
                time.sleep(1.5)

            if info_path is not None:
                ok = upload_image(client, lid, info_path, rank=3, label=label)
                if ok:
                    results[slug]["uploads"] += 1
                time.sleep(1.5)

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    for slug, r in results.items():
        hero_s = "OK" if r["hero_ok"] else "FAIL"
        grid_s = "OK" if r["grid_ok"] else "FAIL"
        info_s = "OK" if r["info_ok"] else "no-cache"
        up = r["uploads"]
        total = r["upload_total"]
        print(f"  {slug:20s}  hero={hero_s}  grid={grid_s}  info={info_s}  uploads={up}/{total}")

    print("\nGenerated files:")
    for slug in [b["slug"] for b in BUNDLES]:
        for prefix in ("svg_hero", "svg_grid", "svg_info"):
            p = Path(f"/tmp/{prefix}_{slug}.jpg")
            if p.exists():
                print(f"  {p}  ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
