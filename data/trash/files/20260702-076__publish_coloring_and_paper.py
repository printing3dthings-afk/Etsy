#!/usr/bin/env python3
"""
publish_coloring_and_paper.py — Create, photo, upload, and activate listings for:
  • 11 Kawaii Coloring Page sets (5 pages/ZIP each) at $3.99
  • 12 Digital Paper Packs (5 patterns/ZIP each) at $4.99

Photos are generated with PIL (product grids, close-ups, info graphics) plus one
AI-generated flat-lay background per product type (reused across all listings in
that type) to satisfy the lifestyle hero photo requirement.

Usage:
    python tools/publish_coloring_and_paper.py --dry-run    # preview, no API calls
    python tools/publish_coloring_and_paper.py --type coloring  # coloring only
    python tools/publish_coloring_and_paper.py --type paper     # paper only
    python tools/publish_coloring_and_paper.py              # both
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont, ImageOps
from tools.etsy_api import EtsyAPIClient
from tools.image_gen import generate_image, SQUARE

SHOP_ID = 65012858

COLORING_DIR = ROOT / "data" / "digital_products" / "coloring_pages"
SETS_DIR     = COLORING_DIR / "sets"
PAPER_DIR    = ROOT / "data" / "digital_products" / "digital_paper"
MOCKUPS_DIR  = ROOT / "data" / "digital_products" / "listing_mockups"
MOCKUPS_DIR.mkdir(parents=True, exist_ok=True)

PHOTO_SIZE = (2400, 2400)

# ─── Shared listing constants ──────────────────────────────────────────────────

COLORING_TAGS = [
    # No tag may duplicate a phrase already in the title
    # Title: "Kawaii Coloring Pages Set XX, 5 Printable, Instant Download"
    # Removed duplicates: kawaii coloring, instant download, coloring pages set
    "adult coloring pages", "printable coloring", "coloring sheet pdf",
    "coloring book pdf",    "digital coloring",   "kawaii art print",
    "printable art page",   "black white art",    "line art print",
    "coloring book gift",   "diy coloring pages", "art therapy print",
    "kawaii line art",
]

PAPER_TAGS = [
    # Title: "{Theme} Digital Paper Pack, Scrapbook, Instant Download"
    # Removed duplicates: digital paper pack, instant download
    "scrapbook paper",      "printable paper",    "goodnotes background",
    "digital background",   "pattern paper",      "digital planner",
    "scrapbook digital",    "background paper",   "paper printable",
    "kawaii paper",         "digital download",   "digital paper kit",
    "scrapbooking kit",
]

AI_DISCLOSURE = (
    "\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "🤖 ABOUT THIS DESIGN\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "This product was designed using AI image generation tools, with original prompts, "
    "curation, and finishing by the seller. All products are reviewed for quality before listing."
)

THEME_DISPLAY = {
    "lavender_dreams": "Lavender Dreams",
    "cherry_blossom": "Cherry Blossom",
    "coral_peach": "Coral Peach",
    "cotton_candy": "Cotton Candy",
    "celestial_night": "Celestial Night",
    "matcha_serenity": "Matcha Serenity",
    "mermaidcore": "Mermaidcore",
    "midnight_blue": "Midnight Blue",
    "mocha_latte": "Mocha Latte",
    "ocean_breeze": "Ocean Breeze",
    "sage_garden": "Sage Garden",
    "sunflower_studio": "Sunflower Studio",
}

THEME_COLORS = {
    "lavender_dreams":  ("#8666AA", "#FAF7FF"),
    "cherry_blossom":   ("#F4A7B9", "#FFF5F7"),
    "coral_peach":      ("#FD6C49", "#FFF8F4"),
    "cotton_candy":     ("#DE97C6", "#FFF6FC"),
    "celestial_night":  ("#1E1B4B", "#F0EEF8"),
    "matcha_serenity":  ("#6B8F5E", "#F7F9F3"),
    "mermaidcore":      ("#4ABFBF", "#F0FAFF"),
    "midnight_blue":    ("#1B2568", "#F0F5FF"),
    "mocha_latte":      ("#8B5E3C", "#FDF8F0"),
    "ocean_breeze":     ("#3B8E8A", "#F0FAFA"),
    "sage_garden":      ("#8BA888", "#F6F8F2"),
    "sunflower_studio": ("#F4C430", "#FFFDF0"),
}


# ─── PIL helpers ──────────────────────────────────────────────────────────────

def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _make_grid(pages: list[Path], out_path: Path, bg_color=(248, 248, 248), label: str = "") -> Path:
    """5-page grid: 2 top, 3 bottom (or 3+2 if 5 items). 2400×2400px."""
    n = len(pages)
    canvas = Image.new("RGB", PHOTO_SIZE, bg_color)
    draw = ImageDraw.Draw(canvas)

    margin = 80
    gap = 40
    cols_top, cols_bot = (2, 3) if n == 5 else (3, 3)

    # Row heights
    usable_w = PHOTO_SIZE[0] - 2 * margin
    usable_h = PHOTO_SIZE[1] - 2 * margin - gap - (80 if label else 0)
    row_h = (usable_h - gap) // 2

    positions = []
    # Top row
    cell_w_top = (usable_w - (cols_top - 1) * gap) // cols_top
    for c in range(cols_top):
        x = margin + c * (cell_w_top + gap)
        positions.append((x, margin, cell_w_top, row_h))
    # Bottom row
    cell_w_bot = (usable_w - (cols_bot - 1) * gap) // cols_bot
    for c in range(cols_bot):
        x = margin + c * (cell_w_bot + gap)
        positions.append((x, margin + row_h + gap, cell_w_bot, row_h))

    for i, p in enumerate(pages[:n]):
        if i >= len(positions):
            break
        x, y, w, h = positions[i]
        try:
            img = Image.open(p).convert("RGB")
        except Exception:
            continue
        img.thumbnail((w, h), Image.LANCZOS)
        # Center in cell
        ox = x + (w - img.width) // 2
        oy = y + (h - img.height) // 2
        # Thin border
        border_img = ImageOps.expand(img, border=3, fill=(180, 180, 180))
        canvas.paste(border_img, (ox - 3, oy - 3))

    if label:
        font = _load_font(48)
        draw.text((PHOTO_SIZE[0] // 2, PHOTO_SIZE[1] - 50), label,
                  fill=(80, 80, 80), font=font, anchor="ms")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(out_path), "JPEG", quality=90)
    return out_path


def _make_closeup(page: Path, out_path: Path, accent_hex: str = "#888888") -> Path:
    """Single page close-up with accent border, padded to 2400×2400."""
    img = Image.open(page).convert("RGB")
    img.thumbnail((2000, 2000), Image.LANCZOS)
    canvas = Image.new("RGB", PHOTO_SIZE, _hex_to_rgb("#F8F7F5"))
    ox = (PHOTO_SIZE[0] - img.width) // 2
    oy = (PHOTO_SIZE[1] - img.height) // 2
    # Accent shadow
    shadow = Image.new("RGB", (img.width + 12, img.height + 12), _hex_to_rgb(accent_hex))
    canvas.paste(shadow, (ox - 4, oy + 4))
    canvas.paste(img, (ox, oy))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(out_path), "JPEG", quality=90)
    return out_path


def _make_info_card(lines: list[str], out_path: Path,
                    bg_hex: str = "#FAF7FF", accent_hex: str = "#8666AA") -> Path:
    """Clean text info card (what's included, specs, etc.) at 2400×2400."""
    canvas = Image.new("RGB", PHOTO_SIZE, _hex_to_rgb(bg_hex))
    draw = ImageDraw.Draw(canvas)
    accent_rgb = _hex_to_rgb(accent_hex)

    # Accent bar at top
    draw.rectangle([(0, 0), (PHOTO_SIZE[0], 20)], fill=accent_rgb)
    draw.rectangle([(0, PHOTO_SIZE[1] - 20), (PHOTO_SIZE[0], PHOTO_SIZE[1])], fill=accent_rgb)

    font_lg = _load_font(80)
    font_md = _load_font(56)
    font_sm = _load_font(44)

    y = 160
    for line in lines:
        if line.startswith("##"):
            text = line[2:].strip()
            draw.text((PHOTO_SIZE[0] // 2, y), text, fill=accent_rgb, font=font_lg, anchor="mt")
            y += 110
        elif line.startswith("#"):
            text = line[1:].strip()
            draw.text((200, y), text, fill=(40, 40, 40), font=font_md, anchor="lt")
            y += 85
        elif line.strip():
            draw.text((240, y), line, fill=(80, 80, 80), font=font_sm, anchor="lt")
            y += 70
        else:
            y += 30

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(out_path), "JPEG", quality=90)
    return out_path


def _composite_pages_on_bg(bg_path: Path, pages: list[Path], out_path: Path) -> Path:
    """Composite 3 real product pages onto an AI-generated flat lay background."""
    canvas = Image.open(bg_path).convert("RGB").resize(PHOTO_SIZE, Image.LANCZOS)
    n_pages = min(3, len(pages))
    positions = [
        (180, 200, -12),    # left, slight tilt
        (820, 120, 3),      # center-left
        (1460, 250, -6),    # right, tilt
    ]
    for i in range(n_pages):
        p = pages[i]
        try:
            img = Image.open(p).convert("RGBA")
        except Exception:
            continue
        img.thumbnail((650, 980), Image.LANCZOS)
        rotated = img.rotate(positions[i][2], expand=True, resample=Image.BICUBIC)
        # Add a subtle drop shadow by pasting a gray version slightly offset
        shadow = Image.new("RGBA", rotated.size, (0, 0, 0, 0))
        shadow_layer = Image.new("RGBA", rotated.size, (150, 150, 150, 80))
        mask = rotated.split()[3] if rotated.mode == "RGBA" else None
        if mask:
            shadow.paste(shadow_layer, mask=mask)
        canvas.paste(shadow.convert("RGB"), (positions[i][0] + 8, positions[i][1] + 8),
                     shadow.split()[3] if shadow.mode == "RGBA" else None)
        canvas.paste(rotated.convert("RGB"), (positions[i][0], positions[i][1]),
                     rotated.split()[3] if rotated.mode == "RGBA" else None)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(out_path), "JPEG", quality=90)
    return out_path


def _make_pattern_grid(pattern_files: list[Path], out_path: Path,
                       bg_hex: str = "#F8F8F8", accent_hex: str = "#888888") -> Path:
    """3×2 grid of pattern tiles (5 patterns + 1 title tile)."""
    canvas = Image.new("RGB", PHOTO_SIZE, _hex_to_rgb(bg_hex))
    draw = ImageDraw.Draw(canvas)
    margin, gap = 60, 30
    cols = 3
    cell_size = (PHOTO_SIZE[0] - 2 * margin - (cols - 1) * gap) // cols

    for i, pf in enumerate(pattern_files[:6]):
        col = i % cols
        row = i // cols
        x = margin + col * (cell_size + gap)
        y = margin + row * (cell_size + gap)
        try:
            pat = Image.open(pf).convert("RGB")
        except Exception:
            continue
        pat = pat.resize((cell_size, cell_size), Image.LANCZOS)
        # Thin accent border
        bordered = ImageOps.expand(pat, border=4, fill=_hex_to_rgb(accent_hex))
        canvas.paste(bordered, (x - 4, y - 4))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(out_path), "JPEG", quality=90)
    return out_path


# ─── AI background generation (one per product type) ─────────────────────────

def _get_or_generate_bg(key: str, prompt: str) -> Path:
    bg_path = MOCKUPS_DIR / f"_bg_{key}.jpg"
    if bg_path.exists():
        print(f"  [bg] Reusing existing background: {bg_path.name}")
        return bg_path
    print(f"  [bg] Generating AI background: {key} ...")
    generate_image(prompt, bg_path, size=SQUARE, quality="medium")
    print(f"       Saved {bg_path.name}")
    return bg_path


COLORING_BG_PROMPT = (
    "Photorealistic overhead flat lay, warm cream background with subtle linen texture. "
    "Art supplies arranged artfully: colored pencils fanned out in a rainbow arc, "
    "a set of fine-tip markers uncapped beside them, one open sketchbook (blank pages visible), "
    "a small cup holding paintbrushes, dried flower sprigs in the upper-left corner. "
    "Soft even natural light from above, warm white balance, gentle shadows. "
    "Large open area in center (60% of frame) — completely empty and clear for product placement. "
    "Photography style: clean editorial flat lay. No coloring pages, no artwork, no text. "
    "Square format. No hands, no people, no text overlays."
)

PAPER_BG_PROMPT = (
    "Photorealistic overhead flat lay, crisp white background with subtle texture. "
    "Stationery and craft supplies arranged around the edges: "
    "a rose gold scissors, a small washi tape dispenser with patterned tape, "
    "a few glue sticks, a ruler, tiny alphabet stamps in a tray, "
    "a craft knife, thin ribbon bow, dried lavender sprig. "
    "Soft bright even natural light from above, cool-neutral white balance. "
    "Large open area in center (60% of frame) — completely empty for product placement. "
    "Photography style: clean craft flat lay. No paper patterns, no text. "
    "Square format. No hands, no people."
)


# ─── Description builders ─────────────────────────────────────────────────────

def _coloring_description(set_num: int, page_names: list[str]) -> str:
    pages_list = "\n".join(f"   • Page {i+1}: {n}" for i, n in enumerate(page_names))
    return f"""🖍 Print, color, and frame your own kawaii art — 5 unique coloring pages, instant digital download.

This set of 5 hand-rendered kawaii coloring pages prints beautifully at home or at any print shop. Every design starts from original kawaii artwork — converted to clean black-line-on-white for you to color however you like.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 5 unique kawaii coloring page PNG files
✅ High resolution: 3000×4500px, 300 DPI — crisp at any print size
✅ Clean black lines on pure white — works with any medium
✅ Perfect for: colored pencils, markers, watercolors, digital coloring apps
✅ Instant digital download — files delivered immediately after purchase

Pages in this set:
{pages_list}

━━━━━━━━━━━━━━━━━━━━━━━━
🖨 HOW TO PRINT
━━━━━━━━━━━━━━━━━━━━━━━━
1. Download your PNG files instantly from Etsy
2. Print at home on regular printer paper or cardstock
3. Or upload to a print shop (Walgreens, Staples, FedEx) for poster-size prints
4. Recommended paper: 80–100 lb cardstock for markers/watercolors

━━━━━━━━━━━━━━━━━━━━━━━━
📐 RECOMMENDED PRINT SIZES
━━━━━━━━━━━━━━━━━━━━━━━━
• 4×6" (postcard size — perfect for detailed coloring)
• 5×7" (greeting card size)
• 8×12" (print and frame)
• 12×18" (large poster size)

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: PNG (300 DPI, 3000×4500px, 2:3 portrait ratio)
• Color: Black line art on white background
• Pages: 5 unique designs
• Delivery: Instant digital download (ZIP file)
• No physical item will be shipped

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Can I print these multiple times?
A: Yes! Your license is for personal use — print as many copies as you like for yourself.

Q: Do these work with digital coloring apps?
A: Absolutely! Open the PNG in Procreate, Sketchbook, GoodNotes, or any drawing app and color digitally.

Q: What paper should I use for watercolors?
A: Watercolor paper 90–140 lb for best results. Standard cardstock also works well with colored pencils and markers.

Q: Is this a physical item?
A: No — this is a digital download only. Files are delivered instantly after purchase.

Q: Can I share these with friends?
A: Personal use only. Please don't redistribute or resell the files.
{AI_DISCLOSURE}

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale or redistribution.
"""


def _paper_description(theme_key: str, theme_display: str, pattern_names: list[str], colors: tuple) -> str:
    primary_hex, bg_hex = colors
    patterns_list = "\n".join(f"   • {n}" for n in pattern_names)
    return f"""✨ Beautiful patterned digital paper in the {theme_display} color palette — perfect for GoodNotes backgrounds, Canva designs, scrapbooking, and card making.

Elevate your digital planner pages, journal spreads, and scrapbook projects with 5 seamlessly tiling patterns, all perfectly matched to the {theme_display} color theme.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 5 seamless pattern designs as high-resolution JPG files
✅ Resolution: 3600×3600px, 300 DPI — sharp at any print or screen size
✅ Color theme: {theme_display} (primary {primary_hex})
✅ Instant digital download — ZIP file delivered immediately after purchase

Patterns included:
{patterns_list}

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━
• GoodNotes 6: Settings → Notebook Templates → Import → select JPG → set as page background
• Notability: Paper menu → Custom → import JPG
• Canva: Upload as background image → drag to design
• Print: Use as decorative border, scrapbook backing, card insert
• Digital crafting: Import into Cricut Design Space or Silhouette Studio as background

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: JPG (sRGB, 300 DPI, 3600×3600px square)
• Patterns: 5 unique seamlessly tiling designs
• Color theme: {theme_display}
• Delivery: Instant digital download (ZIP file with 5 JPG files)
• No physical item will be shipped

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Do these tile seamlessly?
A: Yes — all 5 patterns repeat seamlessly so they can be tiled at any size without visible seams.

Q: What apps can I use these in?
A: GoodNotes 6, Notability, Canva, Cricut, Silhouette Studio, Procreate, Affinity Designer, Adobe Illustrator — any app that accepts JPG images.

Q: Can I use these in commercial projects?
A: This listing is for personal use only. For commercial license (Etsy shop, client work), search our shop for the commercial license version.

Q: Is this a physical item?
A: No — this is a digital download. Files are delivered instantly after purchase.
{AI_DISCLOSURE}

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale or redistribution.
"""


# ─── Coloring pages pipeline ──────────────────────────────────────────────────

def _coloring_page_names(zip_path: Path) -> list[str]:
    """Map DP codes in a coloring ZIP to human-readable page names."""
    name_map = {
        "DP1000": "Celestial Moon and Stars",   "DP1001": "Butterfly Garden",
        "DP1002": "Floral Wreath",               "DP1003": "Mushroom Cottage",
        "DP1005": "Cherry Blossom Branch",       "DP1007": "Sunflower Field",
        "DP1008": "Mediterranean Lemon Window",  "DP1009": "Amalfi Coast Village",
        "DP1010": "Mediterranean Terrace",       "DP1011": "Abstract Waves",
        "DP1012": "Vintage Botanical Herbs",     "DP1013": "Tropical Leaves",
        "DP1014": "Wildflower Meadow",           "DP1015": "Lavender Fields",
        "DP1016": "Forest Mushrooms",            "DP1017": "Ocean Waves",
        "DP1018": "Mountain Landscape",          "DP1019": "Autumn Leaves",
        "DP1020": "Boho Feathers",               "DP1021": "Celestial Sun",
        "DP1022": "Rose Garden",                 "DP1023": "Cactus Garden",
        "DP1024": "Woodland Animals",            "DP1025": "Abstract Flowers",
        "DP1026": "Kawaii Pastel Sky",           "DP1030": "Matcha Tea Garden",
        "DP1031": "Sage Botanical",              "DP1032": "Midnight Stars",
        "DP1033": "Sunflower Studio",            "DP1034": "Hummingbird",
        "DP1035": "Koi Pond",                    "DP1036": "Pressed Flowers",
        "DP1037": "Boho Mandala",                "DP1038": "Sea Turtle",
        "DP1039": "Coastal Lighthouse",          "DP1040": "Fox Portrait",
        "DP1041": "Deer in Forest",              "DP1042": "Owl on Branch",
        "DP1043": "Floral Skull",                "DP1044": "Geometric Bear",
        "DP1045": "Succulent Cluster",           "DP1046": "Moon Phases",
        "DP1047": "Paris Skyline",               "DP1048": "Autumn Fox",
        "DP1049": "Spring Robin",                "DP1050": "Winter Fox",
        "DP1051": "Summer Deer",                 "DP1052": "Kawaii Panda",
        "DP1053": "Kawaii Cat",                  "DP1054": "Kawaii Bunny",
        "DP1055": "Coastal Lighthouse",         "DP1056": "Fox in Woodland",
        "DP1057": "Paris Café Scene",            "DP999":  "Kawaii Portrait",
    }
    with zipfile.ZipFile(zip_path) as z:
        files = z.namelist()
    names = []
    for f in files:
        code = Path(f).stem.replace("_coloring", "").upper()
        names.append(name_map.get(code, code))
    return names


def publish_coloring_sets(c: EtsyAPIClient, dry_run: bool) -> list[dict]:
    """Create Etsy listings for all 11 coloring page ZIP sets."""
    zip_files = sorted(SETS_DIR.glob("coloring_set_*.zip"))
    if not zip_files:
        print("No coloring set ZIPs found in", SETS_DIR)
        return []

    # One shared AI flat-lay background for all coloring listings
    coloring_bg = _get_or_generate_bg("coloring_pencils", COLORING_BG_PROMPT)

    results = []
    for i, zip_path in enumerate(zip_files, start=1):
        set_num  = i
        set_label = f"Set {set_num:02d}"
        title = f"Kawaii Coloring Pages {set_label}, 5 Printable, Instant Download"
        assert len(title) <= 70, f"Title too long: {len(title)} chars: {title}"

        # Extract pages from ZIP to get actual PNGs
        extract_dir = MOCKUPS_DIR / f"coloring_{set_label}"
        extract_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(extract_dir)
        page_paths = sorted(extract_dir.glob("*.png"))
        page_names = _coloring_page_names(zip_path)

        # Generate 5 mockup photos
        mdir = MOCKUPS_DIR / f"coloring_set_{set_num:02d}"
        mdir.mkdir(exist_ok=True)

        p1 = _composite_pages_on_bg(coloring_bg, page_paths, mdir / "01_lifestyle.jpg")
        p2 = _make_grid(page_paths, mdir / "02_grid_all.jpg",
                        bg_color=(248, 247, 245),
                        label=f"5 Kawaii Coloring Pages — Set {set_num}")
        p3 = _make_closeup(page_paths[0], mdir / "03_closeup_1.jpg", "#555555")
        p4 = _make_closeup(page_paths[1], mdir / "04_closeup_2.jpg", "#777777")
        p5 = _make_info_card([
            f"## Kawaii Coloring Pages — Set {set_num}",
            "",
            "# 📦 WHAT'S INCLUDED",
            "  5 unique kawaii coloring page PNG files",
            "  High-resolution: 3000×4500px, 300 DPI",
            "  Print-ready: 4×6, 5×7, 8×12, 12×18 inch",
            "  Works with pencils, markers, watercolors",
            "",
            "# ✉ DELIVERY",
            "  Instant digital download after purchase",
            "  ZIP file containing all 5 PNG files",
        ], mdir / "05_info_card.jpg", bg_hex="#FAF7F4", accent_hex="#7A6055")

        photos = [p1, p2, p3, p4, p5]
        print(f"\n[Coloring Set {set_num:02d}] {title}")
        print(f"  Photos: {len(photos)} generated")

        description = _coloring_description(set_num, page_names)
        listing_body = {
            "title": title,
            "description": description,
            "price": 4.99,
            "quantity": 999,
            "who_made": "i_did",
            "when_made": "made_to_order",
            "is_supply": False,
            "taxonomy_id": 2078,
            "tags": COLORING_TAGS,
            "materials": ["digital download", "PNG file", "instant download"],
            "state": "draft",
            "type": "download",
        }

        if dry_run:
            print(f"  [DRY] Would create listing: {title}")
            results.append({"set": set_label, "title": title, "dry_run": True})
            continue

        # Create listing
        try:
            resp = c.create_listing(listing_body)
            lid  = resp["listing_id"]
            print(f"  Created listing {lid}")
        except Exception as exc:
            print(f"  ERROR creating listing: {exc}")
            results.append({"set": set_label, "error": str(exc)})
            continue

        # Upload photos
        for rank, photo in enumerate(photos, start=1):
            try:
                c.upload_listing_image(lid, str(photo), rank=rank)
                time.sleep(2.0)
                print(f"  Photo {rank} uploaded")
            except Exception as exc:
                print(f"  WARN photo {rank}: {exc}")

        # Upload ZIP digital file
        try:
            c.upload_listing_file(lid, str(zip_path), rank=1)
            time.sleep(1.0)
            print(f"  ZIP uploaded: {zip_path.name}")
        except Exception as exc:
            print(f"  ERROR uploading ZIP: {exc}")

        # Activate
        try:
            c.update_listing(lid, {"state": "active"})
            time.sleep(0.5)
            print(f"  ✓ ACTIVATED")
            results.append({"set": set_label, "listing_id": lid, "title": title})
        except Exception as exc:
            print(f"  ERROR activating: {exc}")
            results.append({"set": set_label, "listing_id": lid, "error_activate": str(exc)})

    return results


# ─── Digital paper pipeline ───────────────────────────────────────────────────

def publish_paper_packs(c: EtsyAPIClient, dry_run: bool) -> list[dict]:
    """Create Etsy listings for all 12 digital paper pack ZIPs."""
    theme_dirs = sorted([d for d in PAPER_DIR.iterdir() if d.is_dir()])
    if not theme_dirs:
        print("No theme directories found in", PAPER_DIR)
        return []

    paper_bg = _get_or_generate_bg("paper_stationery", PAPER_BG_PROMPT)

    results = []
    for theme_dir in theme_dirs:
        theme_key = theme_dir.name
        if theme_key not in THEME_DISPLAY:
            continue

        theme_display = THEME_DISPLAY[theme_key]
        zip_path = PAPER_DIR / f"{theme_key}_paper_pack.zip"
        if not zip_path.exists():
            print(f"  SKIP {theme_key}: no ZIP found")
            continue

        primary_hex, bg_hex = THEME_COLORS.get(theme_key, ("#888888", "#F8F8F8"))

        pattern_files = sorted(theme_dir.glob("pattern_*.jpg"))
        if not pattern_files:
            print(f"  SKIP {theme_key}: no pattern files found")
            continue

        pattern_names = [
            p.stem.replace("pattern_", "").replace("_", " ").title()
            for p in pattern_files
        ]

        title = f"{theme_display} Digital Paper Pack, Scrapbook, Instant Download"
        if len(title) > 70:
            title = title[:70].rstrip(",").strip()
        assert len(title) <= 70, f"Title too long: {len(title)}: {title}"

        # Generate 5 mockup photos
        mdir = MOCKUPS_DIR / f"paper_{theme_key}"
        mdir.mkdir(exist_ok=True)

        p1 = _composite_pages_on_bg(paper_bg, pattern_files[:3], mdir / "01_lifestyle.jpg")
        p2 = _make_pattern_grid(pattern_files, mdir / "02_pattern_grid.jpg",
                                bg_hex=bg_hex, accent_hex=primary_hex)
        p3 = _make_closeup(pattern_files[0], mdir / "03_closeup_1.jpg", primary_hex)
        p4 = _make_closeup(pattern_files[1] if len(pattern_files) > 1 else pattern_files[0],
                           mdir / "04_closeup_2.jpg", primary_hex)
        p5 = _make_info_card([
            f"## {theme_display}",
            "## Digital Paper Pack",
            "",
            "# 📦 WHAT'S INCLUDED",
            "  5 seamless pattern designs (JPG)",
            "  3600×3600px, 300 DPI",
            "  GoodNotes, Notability, Canva, Procreate",
            "  Scrapbooking & card making",
            "",
            "# ✉ DELIVERY",
            "  Instant digital download after purchase",
        ], mdir / "05_info_card.jpg", bg_hex=bg_hex, accent_hex=primary_hex)

        photos = [p1, p2, p3, p4, p5]
        print(f"\n[Paper Pack] {theme_display}  — {title}")
        print(f"  Photos: {len(photos)} generated")

        description = _paper_description(theme_key, theme_display, pattern_names,
                                         (primary_hex, bg_hex))
        listing_body = {
            "title": title,
            "description": description,
            "price": 4.99,
            "quantity": 999,
            "who_made": "i_did",
            "when_made": "made_to_order",
            "is_supply": False,
            "taxonomy_id": 2078,
            "tags": PAPER_TAGS,
            "materials": ["digital download", "JPG file", "instant download"],
            "state": "draft",
            "type": "download",
        }

        if dry_run:
            print(f"  [DRY] Would create listing: {title}")
            results.append({"theme": theme_key, "title": title, "dry_run": True})
            continue

        # Create listing
        try:
            resp = c.create_listing(listing_body)
            lid  = resp["listing_id"]
            print(f"  Created listing {lid}")
        except Exception as exc:
            print(f"  ERROR creating listing: {exc}")
            results.append({"theme": theme_key, "error": str(exc)})
            continue

        # Upload photos
        for rank, photo in enumerate(photos, start=1):
            try:
                c.upload_listing_image(lid, str(photo), rank=rank)
                time.sleep(2.0)
                print(f"  Photo {rank} uploaded")
            except Exception as exc:
                print(f"  WARN photo {rank}: {exc}")

        # Upload ZIP digital file
        try:
            c.upload_listing_file(lid, str(zip_path), rank=1)
            time.sleep(1.0)
            print(f"  ZIP uploaded: {zip_path.name}")
        except Exception as exc:
            print(f"  ERROR uploading ZIP: {exc}")

        # Activate
        try:
            c.update_listing(lid, {"state": "active"})
            time.sleep(0.5)
            print(f"  ✓ ACTIVATED")
            results.append({"theme": theme_key, "listing_id": lid, "title": title})
        except Exception as exc:
            print(f"  ERROR activating: {exc}")
            results.append({"theme": theme_key, "listing_id": lid, "error_activate": str(exc)})

    return results


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--type", choices=["coloring", "paper", "both"], default="both")
    args = ap.parse_args()

    c = EtsyAPIClient()
    all_results = {}

    if args.type in ("coloring", "both"):
        print("\n" + "=" * 65)
        print("COLORING PAGES (11 sets × 5 pages = 55 pages)")
        print("=" * 65)
        all_results["coloring"] = publish_coloring_sets(c, dry_run=args.dry_run)

    if args.type in ("paper", "both"):
        print("\n" + "=" * 65)
        print("DIGITAL PAPER PACKS (12 themes × 5 patterns)")
        print("=" * 65)
        all_results["paper"] = publish_paper_packs(c, dry_run=args.dry_run)

    # Summary
    print("\n" + "=" * 65)
    print(f"SUMMARY {'(DRY RUN)' if args.dry_run else ''}")
    print("=" * 65)
    for key, results in all_results.items():
        activated = [r for r in results if "listing_id" in r and "error" not in r]
        errors    = [r for r in results if "error" in r]
        print(f"  {key}: {len(activated)} activated, {len(errors)} errors")

    # Save report
    report = ROOT / "data" / "reports" / "coloring_paper_publish_2026-06-10.json"
    report.parent.mkdir(exist_ok=True)
    with open(report, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nReport → {report}")


if __name__ == "__main__":
    main()
