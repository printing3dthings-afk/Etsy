#!/usr/bin/env python3
"""
Create bundle grid hero images for SVG bundle Etsy listings.
Renders actual SVG files to PNG, builds a grid collage, uploads as rank=1 image.
"""

import sys
import os
import time
import math
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent))

import dotenv
dotenv.load_dotenv(Path(__file__).parent.parent / ".env")

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from etsy_api import EtsyAPIClient, EtsyAPIError

# ── Config ────────────────────────────────────────────────────────────────────

CANVAS_SIZE = 2400
BACKGROUND_COLOR = "#FDF8F0"  # warm cream
CELL_BG_COLOR = "#FFFFFF"     # white cell background
CELL_SIZE = 550               # each cell is 550×550
CELL_PADDING = 20             # gap between cell edge and design
CELL_GAP = 20                 # gap between cells
BOTTOM_STRIP_HEIGHT = 200     # px for text area at bottom
COLS = 4
ROWS = 3
MAX_DESIGNS = 12

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Bundle definitions
BUNDLES = [
    {
        "listing_id": 4514130045,
        "commercial_listing_id": 4515439743,
        "name": "Floral SVG Bundle",
        "svg_folder": "data/svg_pack/SVG",
        "total_designs": 10,
        "line2_count": "10 Designs Included",
    },
    {
        "listing_id": 4514134583,
        "commercial_listing_id": 4515439751,
        "name": "Christian SVG Bundle",
        "svg_folder": "data/faith_pack/SVG",
        "total_designs": 10,
        "line2_count": "10 Designs Included",
    },
    {
        "listing_id": 4514136783,
        "commercial_listing_id": 4515439755,
        "name": "Graduation SVG Bundle 2026",
        "svg_folder": "data/grad_pack/SVG",
        "total_designs": 10,
        "line2_count": "10 Designs Included",
    },
    {
        "listing_id": 4514392281,
        "commercial_listing_id": 4515437432,
        "name": "Mom Life SVG Bundle",
        "svg_folder": "data/mom_life_pack/SVG",
        "total_designs": 20,
        "line2_count": "20 Designs Included",
    },
    {
        "listing_id": 4514536935,
        "commercial_listing_id": 4515439763,
        "name": "Good Vibes SVG Bundle",
        "svg_folder": "data/groovy_pack/SVG",
        "total_designs": 20,
        "line2_count": "20 Designs Included",
    },
    {
        "listing_id": None,  # commercial only
        "commercial_listing_id": 4515437442,
        "name": "Western SVG Bundle",
        "svg_folder": "data/svg_bundles/western/SVG",
        "total_designs": 12,
        "line2_count": "12 Designs Included",
    },
]

REPO_ROOT = Path(__file__).parent.parent


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def render_svg_to_pil(svg_path: Path, target_size: int) -> Image.Image | None:
    """Render an SVG file to a PIL RGBA image at target_size×target_size."""
    try:
        png_bytes = cairosvg.svg2png(
            url=str(svg_path),
            output_width=target_size,
            output_height=target_size,
        )
        img = Image.open(BytesIO(png_bytes)).convert("RGBA")
        return img
    except Exception as e:
        print(f"    [WARN] Failed to render {svg_path.name}: {e}")
        return None


def create_cell(svg_img: Image.Image) -> Image.Image:
    """
    Create a CELL_SIZE×CELL_SIZE cell:
    - White background with 8px gap on each side
    - SVG image rendered inside with CELL_PADDING on all sides
    """
    cell = Image.new("RGBA", (CELL_SIZE, CELL_SIZE), (255, 255, 255, 0))

    # White rectangle (leave 8px gap from edge for visual breathing room)
    gap = 8
    white_rect = Image.new("RGBA", (CELL_SIZE - gap * 2, CELL_SIZE - gap * 2), (255, 255, 255, 255))
    cell.paste(white_rect, (gap, gap), white_rect)

    # Calculate inner area for the design
    inner_w = CELL_SIZE - gap * 2 - CELL_PADDING * 2
    inner_h = CELL_SIZE - gap * 2 - CELL_PADDING * 2

    # Scale SVG image to fit inner area preserving aspect ratio
    svg_w, svg_h = svg_img.size
    scale = min(inner_w / svg_w, inner_h / svg_h)
    new_w = int(svg_w * scale)
    new_h = int(svg_h * scale)
    resized = svg_img.resize((new_w, new_h), Image.LANCZOS)

    # Center within inner area
    offset_x = gap + CELL_PADDING + (inner_w - new_w) // 2
    offset_y = gap + CELL_PADDING + (inner_h - new_h) // 2

    cell.paste(resized, (offset_x, offset_y), resized)
    return cell


def create_bundle_hero(bundle: dict) -> Path | None:
    """
    Build the 2400×2400 grid hero image for a bundle.
    Returns the path to the saved JPEG, or None on failure.
    """
    name = bundle["name"]
    svg_folder = REPO_ROOT / bundle["svg_folder"]
    line2_count = bundle["line2_count"]

    print(f"\n  Building grid for: {name}")
    print(f"  SVG folder: {svg_folder}")

    # Collect SVG files (sorted alphabetically, up to MAX_DESIGNS)
    svg_files = sorted(svg_folder.glob("*.svg"))[:MAX_DESIGNS]
    if not svg_files:
        print(f"  [ERROR] No SVG files found in {svg_folder}")
        return None

    print(f"  Found {len(svg_files)} SVG files (showing up to {MAX_DESIGNS})")

    # Render each SVG to a cell image
    design_size = CELL_SIZE - 16 - CELL_PADDING * 2  # inner design area
    cells = []
    for svg_path in svg_files:
        svg_img = render_svg_to_pil(svg_path, design_size)
        if svg_img is None:
            continue
        cell = create_cell(svg_img)
        cells.append(cell)
        print(f"    Rendered: {svg_path.name}")

    if not cells:
        print(f"  [ERROR] No cells could be rendered for {name}")
        return None

    n = len(cells)
    print(f"  Successfully rendered {n} designs")

    # Calculate grid dimensions
    # Always use 4 cols × 3 rows layout
    grid_w = COLS * CELL_SIZE + (COLS - 1) * CELL_GAP
    grid_h = ROWS * CELL_SIZE + (ROWS - 1) * CELL_GAP

    # Calculate total canvas needed (grid + margins + bottom strip)
    available_height = CANVAS_SIZE - BOTTOM_STRIP_HEIGHT
    # Center grid in available area
    margin_x = (CANVAS_SIZE - grid_w) // 2
    margin_y = (available_height - grid_h) // 2

    # Create canvas
    bg_rgb = hex_to_rgb(BACKGROUND_COLOR)
    canvas = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), bg_rgb)

    # Place cells in grid (centered, empty cells remain background)
    # For 10 designs: rows 0,1 full (4 each), row 2 has 2 cells — center them
    # For 12 designs: full 4×3 grid
    # For fewer: fill top-to-bottom, left-to-right, center last partial row

    total_slots = COLS * ROWS  # 12

    # Determine fill order: top-to-bottom, left-to-right for full rows
    # Last row: center remaining cells
    full_rows = n // COLS
    remainder = n % COLS

    for i, cell in enumerate(cells):
        row = i // COLS
        col = i % COLS

        # If this is the last partial row, center the cells
        if row == full_rows and remainder > 0:
            # Center the remainder cells in this row
            start_col = (COLS - remainder) // 2
            col = start_col + (i - full_rows * COLS)

        x = margin_x + col * (CELL_SIZE + CELL_GAP)
        y = margin_y + row * (CELL_SIZE + CELL_GAP)

        # Paste cell (cell is RGBA, canvas is RGB — composite over bg)
        canvas.paste(cell.convert("RGB"), (x, y))

    # Draw bottom strip
    draw = ImageDraw.Draw(canvas)
    strip_y = CANVAS_SIZE - BOTTOM_STRIP_HEIGHT
    strip_color = hex_to_rgb(BACKGROUND_COLOR)

    # Bottom strip is already background color — just draw text
    text_color = (30, 30, 30)  # dark charcoal

    try:
        font_bold = ImageFont.truetype(FONT_BOLD, 48)
        font_regular = ImageFont.truetype(FONT_REGULAR, 32)
    except Exception:
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()

    # Line 1: Bundle name
    line1 = name
    line2 = f"{line2_count} • Cricut & Silhouette Compatible"

    # Get text bounding boxes for centering
    bbox1 = draw.textbbox((0, 0), line1, font=font_bold)
    text1_w = bbox1[2] - bbox1[0]
    text1_h = bbox1[3] - bbox1[1]

    bbox2 = draw.textbbox((0, 0), line2, font=font_regular)
    text2_w = bbox2[2] - bbox2[0]
    text2_h = bbox2[3] - bbox2[1]

    total_text_h = text1_h + 16 + text2_h
    text_start_y = strip_y + (BOTTOM_STRIP_HEIGHT - total_text_h) // 2

    x1 = (CANVAS_SIZE - text1_w) // 2
    x2 = (CANVAS_SIZE - text2_w) // 2

    draw.text((x1, text_start_y), line1, font=font_bold, fill=text_color)
    draw.text((x2, text_start_y + text1_h + 16), line2, font=font_regular, fill=text_color)

    # Save as JPEG
    bundle_slug = name.lower().replace(" ", "_").replace("-", "_")
    output_path = Path(f"/tmp/svg_hero_{bundle_slug}.jpg")
    canvas.save(str(output_path), "JPEG", quality=92)
    print(f"  Saved: {output_path} ({output_path.stat().st_size // 1024}KB)")

    return output_path


def upload_hero_image(client: EtsyAPIClient, listing_id: int, image_path: Path, label: str) -> bool:
    """Upload image as rank=1 to a listing. Returns True on success."""
    try:
        # Get existing images and delete rank=1 if it exists
        existing = client.get_listing_images(listing_id)
        for img in existing:
            if img.get("rank") == 1:
                try:
                    client.delete_listing_image(listing_id, img["listing_image_id"])
                    print(f"    Deleted existing rank=1 image from {label} (id={listing_id})")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"    [WARN] Could not delete old rank=1 image: {e}")

        result = client.upload_listing_image(listing_id, str(image_path), rank=1)
        print(f"    Uploaded to {label} (id={listing_id}) → image_id={result.get('listing_image_id', 'unknown')}")
        return True
    except EtsyAPIError as e:
        print(f"    [ERROR] Upload to {label} (id={listing_id}) failed: {e}")
        return False
    except Exception as e:
        print(f"    [ERROR] Unexpected error uploading to {label} (id={listing_id}): {e}")
        return False


def main():
    print("=" * 60)
    print("SVG Bundle Hero Image Creator")
    print("=" * 60)

    # Initialize Etsy client
    client = EtsyAPIClient()

    # Refresh token if needed
    try:
        client.refresh_access_token()
        print("Token refreshed successfully")
    except Exception as e:
        print(f"[WARN] Token refresh failed (may still be valid): {e}")

    success_count = 0
    total_count = 0

    for bundle in BUNDLES:
        print(f"\n{'=' * 60}")
        print(f"Bundle: {bundle['name']}")

        # Generate hero image
        image_path = create_bundle_hero(bundle)
        if image_path is None:
            print(f"  [SKIP] Failed to create hero image for {bundle['name']}")
            # Count how many listings we were supposed to update
            if bundle["listing_id"]:
                total_count += 2
            else:
                total_count += 1
            continue

        print(f"\n  Uploading to Etsy...")

        # Upload to regular listing (if exists)
        if bundle["listing_id"]:
            total_count += 1
            ok = upload_hero_image(client, bundle["listing_id"], image_path, "regular listing")
            if ok:
                success_count += 1
            time.sleep(0.5)

        # Upload to commercial listing
        if bundle["commercial_listing_id"]:
            total_count += 1
            ok = upload_hero_image(client, bundle["commercial_listing_id"], image_path, "commercial listing")
            if ok:
                success_count += 1
            time.sleep(0.5)

    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {success_count}/{total_count} listings updated successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()
