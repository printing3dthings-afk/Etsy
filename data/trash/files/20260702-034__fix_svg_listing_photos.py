#!/usr/bin/env python3
"""
fix_svg_listing_photos.py — Replace all wrong wall-art room photos on SVG bundle
listings with correct design-preview photos built from the actual SVG files.

Generates 3 photos per listing (no OpenAI required — pure PIL + cairosvg):
  rank=1  Full design grid (all designs at 4-col grid on cream background)
  rank=2  Spotlight: 3 featured designs at larger scale
  rank=3  Info card: what's included (SVG/PNG/EPS/DXF), compatible machines

Usage:
    python tools/fix_svg_listing_photos.py
    python tools/fix_svg_listing_photos.py --dry-run   # build images, no upload
"""

from __future__ import annotations

import sys, os, time, argparse, math
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import cairosvg
from PIL import Image, ImageDraw, ImageFont
from etsy_api import EtsyAPIClient, EtsyAPIError

# ── Constants ─────────────────────────────────────────────────────────────────

CANVAS      = 2400
BG_COLOR    = (253, 248, 240)   # warm cream #FDF8F0
CELL_BG     = (255, 255, 255)
DARK_TEXT   = (30, 30, 30)
MID_TEXT    = (90, 90, 90)
ACCENT      = (120, 90, 160)    # soft purple accent for info card

FONT_BOLD   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG    = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

REPO_ROOT   = Path(__file__).parent.parent

# ── Bundle definitions ────────────────────────────────────────────────────────
# listing_id = regular bundle | commercial_id = commercial license version

BUNDLES = [
    {
        "slug":          "floral",
        "name":          "Floral Botanical SVG Bundle",
        "listing_id":    4514130045,
        "commercial_id": 4515439743,
        "svg_dir":       "data/svg_pack/SVG",
        "design_count":  10,
    },
    {
        "slug":          "christian_faith",
        "name":          "Christian Faith SVG Bundle",
        "listing_id":    4514134583,
        "commercial_id": 4515439751,
        "svg_dir":       "data/faith_pack/SVG",
        "design_count":  10,
    },
    {
        "slug":          "graduation",
        "name":          "Graduation 2026 SVG Bundle",
        "listing_id":    4514136783,
        "commercial_id": 4515439755,
        "svg_dir":       "data/grad_pack/SVG",
        "design_count":   9,
    },
    {
        "slug":          "mom_life",
        "name":          "Mom Life SVG Bundle",
        "listing_id":    4514392281,
        "commercial_id": 4515437432,
        "svg_dir":       "data/mom_life_pack/SVG",
        "design_count":  20,
    },
    {
        "slug":          "good_vibes",
        "name":          "Good Vibes SVG Bundle",
        "listing_id":    4514536935,
        "commercial_id": 4515439763,
        "svg_dir":       "data/groovy_pack/SVG",
        "design_count":  10,
    },
    {
        "slug":          "western",
        "name":          "Western SVG Bundle",
        "listing_id":    None,
        "commercial_id": 4515437442,
        "svg_dir":       "data/svg_bundles/western/SVG",
        "design_count":  12,
    },
]


# ── Font loader ───────────────────────────────────────────────────────────────

def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


# ── SVG rendering ─────────────────────────────────────────────────────────────

def render_svg(svg_path: Path, size: int) -> Image.Image | None:
    try:
        png = cairosvg.svg2png(url=str(svg_path), output_width=size, output_height=size)
        return Image.open(BytesIO(png)).convert("RGBA")
    except Exception as e:
        print(f"    [WARN] cairosvg failed on {svg_path.name}: {e}")
        return None


# ── Photo 1: Full design grid ─────────────────────────────────────────────────

def build_grid_photo(bundle: dict) -> Path | None:
    """4-col grid showing up to 20 designs (5 rows × 4 cols max)."""
    svg_dir = REPO_ROOT / bundle["svg_dir"]
    name    = bundle["name"]
    count   = bundle["design_count"]
    slug    = bundle["slug"]

    svg_files = sorted(svg_dir.glob("*.svg"))[:20]
    if not svg_files:
        print(f"  [ERROR] No SVG files in {svg_dir}")
        return None

    COLS = 4
    MAX  = min(len(svg_files), 20)
    ROWS = math.ceil(MAX / COLS)

    STRIP_H = 220       # bottom text strip height
    MARGIN  = 40        # outer margin
    GAP     = 18        # gap between cells
    AVAIL_W = CANVAS - 2 * MARGIN
    AVAIL_H = CANVAS - STRIP_H - 2 * MARGIN
    CELL_W  = (AVAIL_W - GAP * (COLS - 1)) // COLS
    CELL_H  = (AVAIL_H - GAP * (ROWS - 1)) // ROWS
    CELL_SZ = min(CELL_W, CELL_H)

    grid_w = COLS * CELL_SZ + GAP * (COLS - 1)
    grid_h = ROWS * CELL_SZ + GAP * (ROWS - 1)

    canvas = Image.new("RGB", (CANVAS, CANVAS), BG_COLOR)
    draw   = ImageDraw.Draw(canvas)

    # Horizontal center, top-aligned with margin
    ox = (CANVAS - grid_w) // 2
    oy = MARGIN

    for i, svgp in enumerate(svg_files[:MAX]):
        row, col = divmod(i, COLS)
        # Last partial row: center cells
        remainder = MAX % COLS
        if row == ROWS - 1 and remainder > 0:
            start_col = (COLS - remainder) // 2
            col = start_col + (i - (ROWS - 1) * COLS)

        x = ox + col * (CELL_SZ + GAP)
        y = oy + row * (CELL_SZ + GAP)

        # White cell background
        draw.rounded_rectangle([x, y, x + CELL_SZ, y + CELL_SZ], radius=8, fill=CELL_BG)

        PAD = 22
        inner = CELL_SZ - 2 * PAD
        img = render_svg(svgp, inner)
        if img:
            # Center design within cell
            iw, ih = img.size
            scale = min(inner / iw, inner / ih)
            iw2, ih2 = int(iw * scale), int(ih * scale)
            img = img.resize((iw2, ih2), Image.LANCZOS)
            px = x + PAD + (inner - iw2) // 2
            py = y + PAD + (inner - ih2) // 2
            canvas.paste(img, (px, py), img)

    # Bottom strip text
    fnt_big = _font(FONT_BOLD, 56)
    fnt_sm  = _font(FONT_REG, 36)

    line1 = name
    line2 = f"{MAX} Designs • SVG PNG EPS DXF • Cricut & Silhouette"

    strip_y = CANVAS - STRIP_H
    bb1 = draw.textbbox((0, 0), line1, font=fnt_big)
    bb2 = draw.textbbox((0, 0), line2, font=fnt_sm)
    draw.text(((CANVAS - (bb1[2] - bb1[0])) // 2, strip_y + 40), line1, font=fnt_big, fill=DARK_TEXT)
    draw.text(((CANVAS - (bb2[2] - bb2[0])) // 2, strip_y + 120), line2, font=fnt_sm, fill=MID_TEXT)

    out = Path(f"/tmp/svg_grid_{slug}.jpg")
    canvas.save(str(out), "JPEG", quality=93)
    print(f"    Grid photo saved: {out} ({out.stat().st_size // 1024} KB)")
    return out


# ── Photo 2: Spotlight — 3 featured designs ───────────────────────────────────

def build_spotlight_photo(bundle: dict) -> Path | None:
    """Three best designs shown large on cream, vertically centered in tall cards."""
    svg_dir = REPO_ROOT / bundle["svg_dir"]
    slug    = bundle["slug"]

    svg_files = sorted(svg_dir.glob("*.svg"))
    if len(svg_files) == 0:
        return None
    elif len(svg_files) < 3:
        picks = svg_files
    else:
        mid = len(svg_files) // 2
        picks = [svg_files[0], svg_files[mid], svg_files[-1]]

    STRIP_H  = 200
    LABEL_H  = 60    # design name label height inside card
    MARGIN   = 50
    N        = len(picks)
    GAP      = 30
    AVAIL_W  = CANVAS - 2 * MARGIN - GAP * (N - 1)
    CELL_W   = AVAIL_W // N
    CARD_H   = CANVAS - STRIP_H - 2 * MARGIN
    INNER_H  = CARD_H - LABEL_H - 60   # design render area
    INNER_W  = CELL_W - 60
    DESIGN_SZ = min(INNER_W, INNER_H)

    canvas = Image.new("RGB", (CANVAS, CANVAS), BG_COLOR)
    draw   = ImageDraw.Draw(canvas)

    fnt_label = _font(FONT_REG, 34)
    fnt_title = _font(FONT_BOLD, 52)
    fnt_sub   = _font(FONT_REG, 34)

    ox = MARGIN
    oy = MARGIN

    for i, svgp in enumerate(picks):
        x = ox + i * (CELL_W + GAP)
        y = oy

        # White card
        draw.rounded_rectangle([x, y, x + CELL_W, y + CARD_H], radius=14, fill=CELL_BG)

        # Render and vertically center design in the card's inner area
        img = render_svg(svgp, DESIGN_SZ)
        if img:
            iw, ih = img.size
            scale = min(INNER_W / iw, INNER_H / ih)
            iw2, ih2 = int(iw * scale), int(ih * scale)
            img = img.resize((iw2, ih2), Image.LANCZOS)
            # Center horizontally and vertically within the card (excluding label area)
            px = x + (CELL_W - iw2) // 2
            inner_top = y + 30
            inner_bot = y + CARD_H - LABEL_H - 30
            inner_center = (inner_top + inner_bot) // 2
            py = inner_center - ih2 // 2
            canvas.paste(img, (px, py), img)

        # Design name label at bottom of card
        label_parts = svgp.stem.split("_")[1:]   # drop the bundle prefix
        label = " ".join(label_parts).upper()
        bb = draw.textbbox((0, 0), label, font=fnt_label)
        lw = bb[2] - bb[0]
        draw.text((x + (CELL_W - lw) // 2, y + CARD_H - LABEL_H + 8),
                  label, font=fnt_label, fill=MID_TEXT)

    # Bottom strip
    strip_y = CANVAS - STRIP_H
    line1 = bundle["name"]
    line2 = "SVG  ·  PNG  ·  EPS  ·  DXF  —  Cricut & Silhouette Ready"
    bb1 = draw.textbbox((0, 0), line1, font=fnt_title)
    bb2 = draw.textbbox((0, 0), line2, font=fnt_sub)
    draw.text(((CANVAS - (bb1[2] - bb1[0])) // 2, strip_y + 30), line1, font=fnt_title, fill=DARK_TEXT)
    draw.text(((CANVAS - (bb2[2] - bb2[0])) // 2, strip_y + 110), line2, font=fnt_sub, fill=MID_TEXT)

    out = Path(f"/tmp/svg_spotlight_{slug}.jpg")
    canvas.save(str(out), "JPEG", quality=93)
    print(f"    Spotlight photo saved: {out} ({out.stat().st_size // 1024} KB)")
    return out


# ── Photo 3: Info card — what's included ─────────────────────────────────────

def build_info_card(bundle: dict) -> Path | None:
    """Full-canvas what's-included card: formats, design count, compatibility."""
    slug   = bundle["slug"]
    name   = bundle["name"]
    count  = bundle["design_count"]

    canvas = Image.new("RGB", (CANVAS, CANVAS), BG_COLOR)
    draw   = ImageDraw.Draw(canvas)

    fnt_huge = _font(FONT_BOLD, 120)
    fnt_big  = _font(FONT_BOLD, 74)
    fnt_med  = _font(FONT_BOLD, 56)
    fnt_reg  = _font(FONT_REG, 46)
    fnt_sm   = _font(FONT_REG, 36)

    # ── Section 1: Title band (y=0..240) ─────────────────────────────────────
    draw.rectangle([0, 0, CANVAS, 240], fill=ACCENT)
    title = "WHAT'S INCLUDED"
    bb = draw.textbbox((0, 0), title, font=fnt_big)
    draw.text(((CANVAS - (bb[2]-bb[0]))//2, (240-(bb[3]-bb[1]))//2),
              title, font=fnt_big, fill=(255, 255, 255))

    # ── Section 2: Design count (y=270..430) ─────────────────────────────────
    ct_text = f"{count} UNIQUE DESIGNS  ·  {name}"
    bb_ct = draw.textbbox((0,0), ct_text, font=fnt_med)
    draw.text(((CANVAS-(bb_ct[2]-bb_ct[0]))//2, 310),
              ct_text, font=fnt_med, fill=DARK_TEXT)
    draw.rectangle([(CANVAS-400)//2, 400, (CANVAS+400)//2, 406], fill=ACCENT)

    # ── Section 3: Format boxes (y=450..1300) ────────────────────────────────
    formats = [
        ("SVG",  "Cricut Design Space", "Silhouette Studio Pro"),
        ("PNG",  "300 DPI Transparent", "All cutters + print"),
        ("EPS",  "Inkscape / Illustrator", "Print shops"),
        ("DXF",  "Silhouette Studio", "Free + Pro editions"),
    ]
    BOX_W, BOX_H = 540, 360
    GAP   = 50
    COLS  = 2
    total_w = COLS * BOX_W + GAP
    start_x = (CANVAS - total_w) // 2
    start_y = 450

    for i, (fmt, sub1, sub2) in enumerate(formats):
        row, col = divmod(i, COLS)
        bx = start_x + col * (BOX_W + GAP)
        by = start_y + row * (BOX_H + GAP)
        draw.rounded_rectangle([bx, by, bx+BOX_W, by+BOX_H], radius=20, fill=CELL_BG)
        draw.rounded_rectangle([bx, by, bx+BOX_W, by+BOX_H], radius=20, outline=ACCENT, width=4)
        # Format type huge
        bb_fmt = draw.textbbox((0,0), fmt, font=fnt_huge)
        draw.text((bx + (BOX_W-(bb_fmt[2]-bb_fmt[0]))//2, by+30), fmt, font=fnt_huge, fill=ACCENT)
        # Sub-lines
        for li, line in enumerate([sub1, sub2]):
            bb_l = draw.textbbox((0,0), line, font=fnt_sm)
            draw.text((bx + (BOX_W-(bb_l[2]-bb_l[0]))//2, by+190+li*52), line, font=fnt_sm, fill=MID_TEXT)

    # ── Section 4: Machine compatibility (y=1380..1760) ──────────────────────
    compat_y = start_y + 2 * (BOX_H + GAP) + 60
    draw.text(((CANVAS-draw.textbbox((0,0),"COMPATIBLE MACHINES",font=fnt_med)[2])//2, compat_y),
              "COMPATIBLE MACHINES", font=fnt_med, fill=DARK_TEXT)

    machines = [
        "✓  Cricut Maker / Explore / Joy",
        "✓  Silhouette Cameo (Free + Pro)",
        "✓  Brother Scan N Cut",
        "✓  Any SVG-compatible cutter",
    ]
    for i, item in enumerate(machines):
        row, col = divmod(i, 2)
        cx = CANVAS // 4 if col == 0 else 3 * CANVAS // 4
        cy = compat_y + 80 + row * 80
        bb_c = draw.textbbox((0,0), item, font=fnt_reg)
        draw.text((cx - (bb_c[2]-bb_c[0])//2, cy), item, font=fnt_reg, fill=DARK_TEXT)

    # ── Section 5: Instant download strip (y=1900..2080) ─────────────────────
    draw.rounded_rectangle([120, 1920, CANVAS-120, 2060], radius=24, fill=ACCENT)
    instant = "INSTANT DIGITAL DOWNLOAD — FILES DELIVERED IMMEDIATELY AT CHECKOUT"
    bb_i = draw.textbbox((0,0), instant, font=fnt_sm)
    draw.text(((CANVAS-(bb_i[2]-bb_i[0]))//2, 1966), instant, font=fnt_sm, fill=(255,255,255))

    # ── Footer ────────────────────────────────────────────────────────────────
    footer = "© OnBrandCraftz — Personal & Commercial License Available"
    bb_f = draw.textbbox((0,0), footer, font=fnt_sm)
    draw.text(((CANVAS-(bb_f[2]-bb_f[0]))//2, CANVAS-60), footer, font=fnt_sm, fill=MID_TEXT)

    out = Path(f"/tmp/svg_info_{slug}.jpg")
    canvas.save(str(out), "JPEG", quality=93)
    print(f"    Info card saved: {out} ({out.stat().st_size // 1024} KB)")
    return out


# ── Etsy upload helpers ───────────────────────────────────────────────────────

def clear_all_images(c: EtsyAPIClient, listing_id: int, label: str) -> None:
    """Delete all images from a listing."""
    try:
        existing = c.get_listing_images(listing_id)
        for img in existing:
            iid = img.get("listing_image_id")
            try:
                c._request("DELETE", f"listings/{listing_id}/images/{iid}")
                time.sleep(0.2)
            except Exception as e:
                print(f"    [WARN] Could not delete image {iid} from {label}: {e}")
        print(f"    Cleared {len(existing)} images from {label} (id={listing_id})")
    except Exception as e:
        print(f"    [ERROR] Could not fetch images for {label}: {e}")


def upload_photo(c: EtsyAPIClient, listing_id: int, path: Path, rank: int, label: str) -> bool:
    try:
        result = c.upload_listing_image(listing_id, str(path), rank=rank)
        iid = result.get("listing_image_id", "?")
        print(f"    Uploaded rank={rank} → {label} (id={listing_id}) image_id={iid}")
        return True
    except EtsyAPIError as e:
        print(f"    [ERROR] Upload rank={rank} to {label} failed: {e}")
        return False
    except Exception as e:
        print(f"    [ERROR] Unexpected: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main(dry_run: bool = False) -> None:
    print("=" * 65)
    print("SVG Listing Photo Fix")
    print("Replacing wrong wall-art photos with real design previews")
    print("=" * 65)

    c = EtsyAPIClient() if not dry_run else None
    if c:
        try:
            c.refresh_access_token()
            print("Token refreshed.\n")
        except Exception:
            pass

    results = {"fixed": [], "errors": []}

    for bundle in BUNDLES:
        slug = bundle["slug"]
        name = bundle["name"]
        print(f"\n{'─'*65}")
        print(f"Bundle: {name}  (slug={slug})")

        # Generate all 3 photos
        photo1 = build_grid_photo(bundle)
        photo2 = build_spotlight_photo(bundle)
        photo3 = build_info_card(bundle)

        photos = [(p, i+1) for i, p in enumerate([photo1, photo2, photo3]) if p is not None]

        if not photos:
            print(f"  [ERROR] All photo generation failed for {name}")
            results["errors"].append(name)
            continue

        if dry_run:
            print(f"  [DRY RUN] Would upload {len(photos)} photos for {name}")
            continue

        # Fix regular listing
        if bundle["listing_id"]:
            lid = bundle["listing_id"]
            print(f"\n  Fixing regular listing {lid}:")
            clear_all_images(c, lid, f"{name} regular")
            time.sleep(0.5)
            ok = all(upload_photo(c, lid, p, rank, f"{name} regular") for p, rank in photos)
            time.sleep(0.3)
            if ok:
                results["fixed"].append(f"{name} regular ({lid})")
            else:
                results["errors"].append(f"{name} regular ({lid})")

        # Fix commercial listing
        if bundle["commercial_id"]:
            cid = bundle["commercial_id"]
            print(f"\n  Fixing commercial listing {cid}:")
            clear_all_images(c, cid, f"{name} commercial")
            time.sleep(0.5)
            ok = all(upload_photo(c, cid, p, rank, f"{name} commercial") for p, rank in photos)
            time.sleep(0.3)
            if ok:
                results["fixed"].append(f"{name} commercial ({cid})")
            else:
                results["errors"].append(f"{name} commercial ({cid})")

    print(f"\n{'='*65}")
    print("SUMMARY")
    print(f"  Fixed: {len(results['fixed'])}")
    for r in results["fixed"]:
        print(f"    ✓  {r}")
    print(f"  Errors: {len(results['errors'])}")
    for r in results["errors"]:
        print(f"    ✗  {r}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="Build photos without uploading")
    args = ap.parse_args()
    main(dry_run=args.dry_run)
