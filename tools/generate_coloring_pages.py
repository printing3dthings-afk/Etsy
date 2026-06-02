#!/usr/bin/env python3
"""
generate_coloring_pages.py

Converts existing wall art JPG/PNG files into clean black-line-on-white coloring
pages using PIL only (no AI, no OpenAI). Groups output into ZIP sets of 5 and
writes Etsy listing JSON for each set.

Usage:
    python tools/generate_coloring_pages.py              # process all wall art
    python tools/generate_coloring_pages.py --limit 10   # first 10 only
    python tools/generate_coloring_pages.py --preview    # dry-run listing only
"""

import argparse
import json
import re
import sys
import zipfile
from datetime import date
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

# ---------------------------------------------------------------------------
# Paths — never use load_dotenv(), never hardcode
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent.parent.resolve()
PRODUCT_FILES_DIR = BASE / "data" / "digital_products" / "product_files"
COLORING_DIR      = BASE / "data" / "digital_products" / "coloring_pages"
SETS_DIR          = COLORING_DIR / "sets"

# ---------------------------------------------------------------------------
# File selection — patterns that identify non-art variants to exclude
# ---------------------------------------------------------------------------
EXCLUDE_KEYWORDS = (
    "_listing", "_sticker", "_mockup", "_kawaii",
    "_room",    "_size",    "_detail",  "_cover",
    "_sheet",   "_preview",
)

# Exclude files inside the upscaled/ subdirectory
EXCLUDE_SUBDIRS = {"upscaled"}

# Contrast multiplier applied after edge detection
CONTRAST_FACTOR = 3.0

# Threshold for converting to pure B&W (0–255; pixels above become white)
BW_THRESHOLD = 200

# Pages per ZIP set
PAGES_PER_SET = 5


# ---------------------------------------------------------------------------
# File collection
# ---------------------------------------------------------------------------

def collect_source_files(limit: int | None = None) -> list[Path]:
    """Return sorted list of candidate wall-art source files."""
    candidates: list[Path] = []

    for pattern in ("DP*.jpg", "DP*.png"):
        for path in PRODUCT_FILES_DIR.glob(pattern):
            # Skip files in excluded subdirectories
            if any(part in EXCLUDE_SUBDIRS for part in path.parts):
                continue

            name_lower = path.name.lower()
            if any(kw in name_lower for kw in EXCLUDE_KEYWORDS):
                continue

            candidates.append(path)

    # Stable, deterministic order
    candidates.sort(key=lambda p: p.name.lower())

    # De-duplicate by stem (prefer .jpg over .png if both exist for same stem)
    seen_stems: dict[str, Path] = {}
    for p in candidates:
        stem = p.stem.lower()
        if stem not in seen_stems:
            seen_stems[stem] = p
        else:
            # Prefer .jpg
            if p.suffix.lower() == ".jpg":
                seen_stems[stem] = p

    deduplicated = sorted(seen_stems.values(), key=lambda p: p.name.lower())

    if limit is not None:
        deduplicated = deduplicated[:limit]

    return deduplicated


# ---------------------------------------------------------------------------
# Core conversion algorithm
# ---------------------------------------------------------------------------

def convert_to_coloring_page(src: Path, dst: Path) -> None:
    """
    Convert a single source image to a black-line-on-white coloring page.

    Steps:
      1. Open source image
      2. Convert to grayscale
      3. Apply FIND_EDGES filter to extract edge lines
      4. Invert (so lines are black on white)
      5. Enhance contrast × CONTRAST_FACTOR
      6. Threshold to pure B&W (pixels > BW_THRESHOLD → white, else → black)
      7. Save as high-res PNG
    """
    with Image.open(src) as img:
        # Step 1 → 2: grayscale
        gray = img.convert("L")

        # Step 3: edge detection
        edges = gray.filter(ImageFilter.FIND_EDGES)

        # Step 4: invert (lines become black on white background)
        inverted = ImageOps.invert(edges)

        # Step 5: boost contrast so faint lines become distinct
        enhanced = ImageEnhance.Contrast(inverted).enhance(CONTRAST_FACTOR)

        # Step 6: threshold to pure binary B&W
        # pixels > BW_THRESHOLD → 255 (white), else → 0 (black)
        bw = enhanced.point(lambda px: 255 if px > BW_THRESHOLD else 0, "L")

        # Step 7: save as PNG (lossless, printer-friendly)
        bw.save(dst, "PNG")


# ---------------------------------------------------------------------------
# ZIP set builder
# ---------------------------------------------------------------------------

def build_sets(coloring_files: list[Path]) -> list[Path]:
    """
    Group coloring PNGs into ZIP files of PAGES_PER_SET.
    Returns list of created ZIP paths.
    """
    SETS_DIR.mkdir(parents=True, exist_ok=True)
    zip_paths: list[Path] = []

    for i in range(0, len(coloring_files), PAGES_PER_SET):
        batch = coloring_files[i : i + PAGES_PER_SET]
        set_num = (i // PAGES_PER_SET) + 1
        zip_name = f"coloring_set_{set_num:02d}.zip"
        zip_path = SETS_DIR / zip_name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for page in batch:
                zf.write(page, page.name)

        print(f"  ZIP set {set_num:02d}: {zip_path.name}  ({len(batch)} pages)")
        zip_paths.append(zip_path)

    return zip_paths


# ---------------------------------------------------------------------------
# Listing JSON generator
# ---------------------------------------------------------------------------

def generate_listing_json(zip_paths: list[Path]) -> Path:
    """Write a single listing JSON covering all sets generated today."""
    today = date.today().strftime("%Y%m%d")
    json_path = COLORING_DIR / f"listing_{today}.json"

    listing = {
        "title": (
            "Kawaii Coloring Pages Printable | Adult Coloring Book Pages | "
            "Instant Download | Digital Coloring Sheet"
        ),
        "price": 3.99,
        "tags": [
            "adult coloring pages",
            "printable coloring",
            "kawaii coloring",
            "coloring pages pdf",
            "instant download",
            "coloring book",
            "digital coloring",
            "printable art",
            "kawaii art",
            "coloring sheet",
        ],
        "sets": [str(z.relative_to(BASE)) for z in zip_paths],
        "generated_date": today,
        "page_count_per_set": PAGES_PER_SET,
        "format": "PNG, print-ready, black lines on white background",
        "who_made": "i_did",
        "when_made": "made_to_order",
        "is_supply": False,
        "ai_disclosure": (
            "This product was designed using AI image generation tools, with "
            "original prompts, curation, and finishing by the seller. All products "
            "are reviewed for quality before listing."
        ),
    }

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(listing, fh, indent=2)

    return json_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate coloring pages from existing wall art files."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Process first N source files only.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Dry-run: show which files would be processed without converting.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    sources = collect_source_files(limit=args.limit)

    if not sources:
        print("No candidate wall art files found. Nothing to do.")
        sys.exit(0)

    print(f"Found {len(sources)} source file(s) to process.")

    if args.preview:
        print("\n--- Preview (--preview mode, no files written) ---")
        for src in sources:
            print(f"  {src.name}")
        print(f"\nWould generate {len(sources)} coloring page(s) in {COLORING_DIR}")
        sets_count = -(-len(sources) // PAGES_PER_SET)  # ceiling division
        print(f"Would create {sets_count} ZIP set(s) in {SETS_DIR}")
        sys.exit(0)

    # Create output directories
    COLORING_DIR.mkdir(parents=True, exist_ok=True)
    SETS_DIR.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    skipped = 0

    print("\nConverting images...")
    for src in sources:
        stem = src.stem  # e.g. "DP1000"
        dst = COLORING_DIR / f"{stem}_coloring.png"

        # Skip if already up-to-date
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            print(f"  [skip]  {src.name}  (output up-to-date)")
            skipped += 1
            generated.append(dst)
            continue

        try:
            convert_to_coloring_page(src, dst)
            size_kb = dst.stat().st_size // 1024
            print(f"  [ok]    {src.name}  →  {dst.name}  ({size_kb} KB)")
            generated.append(dst)
        except Exception as exc:
            print(f"  [FAIL]  {src.name}  —  {exc}", file=sys.stderr)

    print(f"\nConverted {len(generated) - skipped} new page(s)  "
          f"({skipped} already up-to-date).")

    if not generated:
        print("No coloring pages produced — nothing to ZIP.")
        sys.exit(0)

    # Build ZIP sets
    print("\nBuilding ZIP sets...")
    zip_paths = build_sets(generated)

    # Write listing JSON
    json_path = generate_listing_json(zip_paths)
    print(f"\nListing JSON: {json_path}")

    print(
        f"\nDone.\n"
        f"  Coloring pages : {len(generated)} PNG(s) in {COLORING_DIR}\n"
        f"  ZIP sets       : {len(zip_paths)} set(s) in {SETS_DIR}\n"
        f"  Listing JSON   : {json_path}"
    )


if __name__ == "__main__":
    main()
