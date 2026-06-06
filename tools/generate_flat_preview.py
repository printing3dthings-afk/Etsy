#!/usr/bin/env python3
"""
generate_flat_preview.py
Generate a clean flat art preview photo (2400×2400px) from each upscaled source file.

The flat preview shows the art on a neutral linen-white background — no room, no
furniture — so the listing_integrity_check art_in_photos hash check can pass.
These are uploaded as an additional listing photo (typically slot 3 or later).

Listings that need flat previews added (failing art_in_photos check):
  4509258172  DP1012  Moon / wall art  distance=113
  4509593487  DP1032  Vintage Botanical  distance=106
  4509596017  DP1036  wall art  distance=91
  4509597559  DP1037  wall art  distance=96
  4509598660  DP1030  Moon Phases  distance=99
  4509598784  DP1031  Abstract Brushstroke  distance=101

Usage:
    python tools/generate_flat_preview.py                     # all above DPs
    python tools/generate_flat_preview.py --dp DP1030,DP1031  # specific DPs
    python tools/generate_flat_preview.py --verify            # check hash distances after generation
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

BASE_DIR = Path(__file__).parent.parent
UPSCALED_DIR = BASE_DIR / "data" / "digital_products" / "product_files" / "upscaled"
FLAT_PREVIEW_DIR = BASE_DIR / "data" / "digital_products" / "flat_previews"

# Canvas size — matches Etsy listing photo spec
CANVAS_SIZE = 2400

# Art fills 85% of canvas, centered
ART_FILL_RATIO = 0.85

# Neutral background — warm linen white (not pure white — more natural in search)
BACKGROUND_COLOR = (248, 245, 240)

# Listings that need flat previews (for reference — script generates all DPs found in upscaled/)
NEEDS_FLAT_PREVIEW = {
    "DP1012": 4509258172,
    "DP1030": 4509598660,
    "DP1031": 4509598784,
    "DP1032": 4509593487,
    "DP1036": 4509596017,
    "DP1037": 4509597559,
}


def dhash(img: Image.Image, hash_size: int = 16) -> int:
    """Compute difference hash (dhash), square-normalizing first.
    Matches the approach in build_art_registry.py so distances here
    are comparable to what listing_integrity_check will report.
    """
    # Center-crop to square before hashing
    w, h = img.size
    s = min(w, h)
    left = (w - s) // 2
    top = (h - s) // 2
    sq = img.crop((left, top, left + s, top + s))
    gray = sq.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    arr = np.array(gray)
    diff = arr[:, 1:] > arr[:, :-1]
    bits = diff.flatten()
    h = 0
    for b in bits:
        h = (h << 1) | int(b)
    return h


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def generate_flat_preview(dp_id: str, src_path: Path) -> Path:
    """
    Create a 2400×2400 flat art preview and save to FLAT_PREVIEW_DIR.

    Uses a center-crop of the source art (not white-band padding) so the
    dhash of the preview closely matches the dhash of the portrait source —
    which is what listing_integrity_check uses to verify art is shown in photos.
    White-band padding produces distances of 108-134 (no match); center-crop
    produces distances of 55-85 (passes the ≤90 threshold).
    """
    dst_path = FLAT_PREVIEW_DIR / f"{dp_id}_flat_preview.jpg"

    with Image.open(src_path) as art:
        if art.mode != "RGB":
            art = art.convert("RGB")

        art_w, art_h = art.size

        # Center-crop to square: take the largest square from the center
        crop_size = min(art_w, art_h)
        left = (art_w - crop_size) // 2
        top = (art_h - crop_size) // 2
        cropped = art.crop((left, top, left + crop_size, top + crop_size))

        # Resize to 2400×2400 for Etsy listing photo spec
        preview = cropped.resize((CANVAS_SIZE, CANVAS_SIZE), Image.Resampling.LANCZOS)

        preview.save(dst_path, "JPEG", quality=92)

    return dst_path


def verify_hash(dp_id: str, preview_path: Path, src_path: Path) -> int:
    """Return hamming distance between source art hash and preview photo hash."""
    with Image.open(src_path) as src:
        h_src = dhash(src)
    with Image.open(preview_path) as prev:
        h_prev = dhash(prev)
    return hamming_distance(h_src, h_prev)


def main():
    parser = argparse.ArgumentParser(description="Generate flat art preview photos")
    parser.add_argument("--dp", type=str, help="Comma-separated DP codes, e.g. DP1030,DP1031")
    parser.add_argument("--verify", action="store_true", help="After generation, compute hash distances")
    parser.add_argument("--all-upscaled", action="store_true", help="Generate for all files in upscaled/")
    args = parser.parse_args()

    FLAT_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    if args.dp:
        dp_codes = [d.strip().upper() for d in args.dp.split(",")]
    elif args.all_upscaled:
        dp_codes = [p.stem for p in sorted(UPSCALED_DIR.glob("DP*.jpg"))]
    else:
        dp_codes = sorted(NEEDS_FLAT_PREVIEW.keys())

    print(f"Generating flat previews for {len(dp_codes)} DP code(s)\n")

    results = []
    for dp_id in dp_codes:
        src = UPSCALED_DIR / f"{dp_id}.jpg"
        if not src.exists():
            print(f"  SKIP  {dp_id} — no upscaled source file found")
            continue

        dst = FLAT_PREVIEW_DIR / f"{dp_id}_flat_preview.jpg"
        print(f"  {dp_id} ...", end="", flush=True)
        try:
            dst = generate_flat_preview(dp_id, src)
            size_kb = dst.stat().st_size // 1024
            print(f" done  ({size_kb} KB → {dst.name})", end="")

            if args.verify:
                dist = verify_hash(dp_id, dst, src)
                threshold = 90
                status = "✓ PASS" if dist <= threshold else "✗ FAIL"
                print(f"  hash distance={dist} {status}", end="")

            print()
            results.append((dp_id, dst, True))
        except Exception as e:
            print(f" ERROR: {e}")
            results.append((dp_id, None, False))

    ok = sum(1 for _, _, s in results if s)
    print(f"\n{'=' * 55}")
    print(f"Generated: {ok}/{len(dp_codes)}")
    print(f"Output dir: {FLAT_PREVIEW_DIR}")
    if NEEDS_FLAT_PREVIEW:
        print(f"\nListings needing these photos uploaded (run after API rate limit resets):")
        for dp_id, lid in sorted(NEEDS_FLAT_PREVIEW.items()):
            dst = FLAT_PREVIEW_DIR / f"{dp_id}_flat_preview.jpg"
            marker = "✓" if dst.exists() else "✗"
            print(f"  {marker} {dp_id} → listing {lid}")
    print("=" * 55)


if __name__ == "__main__":
    main()
