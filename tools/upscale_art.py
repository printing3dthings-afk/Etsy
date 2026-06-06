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
import numpy as np
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


def is_lifestyle_composite(img: Image.Image) -> tuple[bool, str]:
    """
    Detect if an image is a lifestyle room scene composite rather than raw printable art.
    Returns (is_composite: bool, reason: str).

    Lifestyle composites have: large warm/cream wall area in top half + darker furniture
    band at bottom + the subject art appears only as a small framed element on the wall.
    Raw art fills the frame with the actual subject.
    """
    arr = np.array(img.convert('RGB'), dtype=float)
    h, w = arr.shape[:2]

    top = arr[:h//2]
    bot = arr[3*h//4:]

    # Warm/cream wall pixels: R>190, G>165, B>120, and R > B (warm not cool)
    warm_mask = (top[:,:,0] > 190) & (top[:,:,1] > 165) & (top[:,:,2] > 120) & (top[:,:,0] > top[:,:,2])
    warm_ratio = float(warm_mask.mean())

    # Dark furniture/floor pixels in bottom quarter: mean brightness < 140
    bot_bright = arr[3*h//4:].mean(axis=2)
    dark_ratio = float((bot_bright < 140).mean())

    # Low variance in top half = plain wall (uniform color)
    top_std = float(arr[:h//2].mean(axis=2).std())

    # Flag if: mostly warm wall above + furniture below + low variance
    is_composite = warm_ratio > 0.40 and dark_ratio > 0.25 and top_std < 65
    reason = f"warm_top={warm_ratio:.2f}, dark_bot={dark_ratio:.2f}, top_std={top_std:.1f}"
    return is_composite, reason


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

        # GATE: reject lifestyle composite room scenes before upscaling
        with Image.open(src_path) as check_img:
            flagged, reason = is_lifestyle_composite(check_img)
        if flagged:
            print(f"  BLOCKED {src_path.name} — looks like a lifestyle composite (room scene), "
                  f"not raw art. {reason}")
            print(f"          Fix: save the raw art file (no room/furniture) then re-run.")
            error_files.append((src_path.name, f"lifestyle composite detected: {reason}"))
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
