#!/usr/bin/env python3
"""
upscale_art.py
Upscale every art file in data/digital_products/product_files/ that is smaller
than 3000px wide to 4x resolution using Lanczos resampling, then apply
UnsharpMask sharpening. Results saved to .../upscaled/ with the same filename.
"""

import os
import sys
import re
from pathlib import Path
from PIL import Image, ImageFilter

# Paths
BASE_DIR = Path(__file__).parent.parent
PRODUCT_FILES_DIR = BASE_DIR / "data" / "digital_products" / "product_files"
UPSCALED_DIR = PRODUCT_FILES_DIR / "upscaled"

# Thresholds and settings
MIN_WIDTH = 3000        # Files below this width will be upscaled
SCALE_FACTOR = 4        # 4x upscale → 1024→4096, 1536→6144
UNSHARP_RADIUS = 2
UNSHARP_PERCENT = 150
UNSHARP_THRESHOLD = 3
JPEG_QUALITY = 95       # High quality for the upscaled master


def upscale_file(src_path: Path, dst_path: Path) -> tuple[int, int]:
    """Upscale a single image file. Returns (new_width, new_height)."""
    with Image.open(src_path) as img:
        orig_w, orig_h = img.size
        new_w = orig_w * SCALE_FACTOR
        new_h = orig_h * SCALE_FACTOR

        # Upscale with Lanczos (best quality for upscaling)
        upscaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Apply UnsharpMask to recover edges lost during upscaling
        sharpened = upscaled.filter(
            ImageFilter.UnsharpMask(
                radius=UNSHARP_RADIUS,
                percent=UNSHARP_PERCENT,
                threshold=UNSHARP_THRESHOLD,
            )
        )

        # Ensure RGB (drop alpha if present; JPEG doesn't support it)
        if sharpened.mode != "RGB":
            sharpened = sharpened.convert("RGB")

        sharpened.save(dst_path, "JPEG", quality=JPEG_QUALITY)
        return new_w, new_h


def main():
    UPSCALED_DIR.mkdir(parents=True, exist_ok=True)

    # Collect candidate files: any DP*.jpg matching the naming pattern
    candidates = sorted(
        p for p in PRODUCT_FILES_DIR.glob("*.jpg")
        if re.match(r"^DP1\d+\.jpg$", p.name)
    )

    upscaled_count = 0
    skipped_count = 0
    error_files = []

    for src_path in candidates:
        dst_path = UPSCALED_DIR / src_path.name

        # Quick-check width without fully loading the image
        try:
            with Image.open(src_path) as img:
                width, height = img.size
        except Exception as e:
            print(f"  ERROR reading {src_path.name}: {e}")
            error_files.append((src_path.name, str(e)))
            continue

        if width >= MIN_WIDTH:
            print(f"  SKIP  {src_path.name}  ({width}x{height} — already ≥ {MIN_WIDTH}px wide)")
            skipped_count += 1
            continue

        print(f"  Upscaling {src_path.name}  ({width}x{height} → ", end="", flush=True)
        try:
            new_w, new_h = upscale_file(src_path, dst_path)
            size_mb = dst_path.stat().st_size / (1024 * 1024)
            print(f"{new_w}x{new_h})  saved {size_mb:.1f} MB → {dst_path.name}")
            upscaled_count += 1
        except Exception as e:
            print(f"FAILED: {e}")
            error_files.append((src_path.name, str(e)))

    print()
    print("=" * 60)
    print(f"Upscale complete: {upscaled_count} upscaled, {skipped_count} skipped")
    if error_files:
        print(f"Errors ({len(error_files)}):")
        for fname, err in error_files:
            print(f"  {fname}: {err}")
    print("=" * 60)

    return upscaled_count, skipped_count, error_files


if __name__ == "__main__":
    main()
