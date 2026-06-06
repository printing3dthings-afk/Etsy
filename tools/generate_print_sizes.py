#!/usr/bin/env python3
"""
generate_print_sizes.py
For every base art file (DP1000–DP1057, matching ^DP1\d+\.jpg$), create a
multi-size print ZIP containing all standard print sizes at 300 DPI.

Usage:
    python tools/generate_print_sizes.py

Output:
    data/digital_products/print_zips/DP1030_print_sizes.zip  (etc.)
"""

import io
import os
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
PRODUCT_FILES_DIR = BASE_DIR / "data" / "digital_products" / "product_files"
UPSCALED_DIR = PRODUCT_FILES_DIR / "upscaled"
PRINT_ZIPS_DIR = BASE_DIR / "data" / "digital_products" / "print_zips"

# ---------------------------------------------------------------------------
# Print-size definitions
# All sizes expressed as (width_inches, height_inches, subfolder, label)
# Pixel dims = inches * 300
# ---------------------------------------------------------------------------
PRINT_SIZES = [
    # 2:3 ratio
    (4,  6,  "2x3", "4x6_300dpi"),
    (8,  12, "2x3", "8x12_300dpi"),
    (12, 18, "2x3", "12x18_300dpi"),
    (16, 24, "2x3", "16x24_300dpi"),
    # 4:5 ratio
    (8,  10, "4x5", "8x10_300dpi"),
    (16, 20, "4x5", "16x20_300dpi"),
    # A-series (already in pixels at 300 DPI: A4=2480x3508, A3=3508x4961)
    (None, None, "a_series", "A4_300dpi"),   # special-cased below
    (None, None, "a_series", "A3_300dpi"),   # special-cased below
    # Square
    (8,  8,  "square", "8x8_300dpi"),
    (12, 12, "square", "12x12_300dpi"),
]

# A-series pixel dimensions at 300 DPI
A_SERIES_DIMS = {
    "A4_300dpi": (2480, 3508),
    "A3_300dpi": (3508, 4961),
}

ASPECT_TOLERANCE = 0.15   # 15% tolerance for aspect-ratio match
JPEG_QUALITY_PRIMARY = 85
JPEG_QUALITY_FALLBACK = 75
MAX_ZIP_BYTES = 20 * 1024 * 1024  # 20 MB


README_TEXT = """\
PRINT SIZES — OnBrandCraftz
===========================

This ZIP contains your digital art print files at all standard sizes, ready
to send to any professional print lab or home printer.

FILES INCLUDED
--------------
2x3/      4x6, 8x12, 12x18, 16x24 inches  (classic photo ratio)
4x5/      8x10, 16x20 inches               (standard frame ratio)
a_series/ A4, A3                            (international paper sizes)
square/   8x8, 12x12 inches                (square frame ratio)

All files are 300 DPI JPEG, ready for professional printing.

HOW TO PRINT
------------
1. Choose the size that matches your frame.
2. Upload the file to your print lab (Mpix, Nations Photo Lab, Printful,
   Canvera, or your local print shop).
3. Select "Print at 100% — do not scale / crop" for best results.
4. Use matte or lustre finish for wall art. Glossy shows fingerprints.

NOTES
-----
- Files smaller than your chosen canvas have white letterbox/pillarbox
  borders. This is intentional — trim to art area or choose a matching ratio.
- For canvas prints, ask your lab to "wrap" the edges.

Questions? Email: Printing3dthings@outlook.com
© OnBrandCraftz — Personal use only. Not for resale or redistribution.
"""


def is_lifestyle_composite(img: Image.Image) -> tuple[bool, str]:
    """
    Detect if an image is a lifestyle room scene rather than raw printable art.
    Returns (is_composite: bool, reason: str).
    Blocks room scenes from being used as print source files.
    """
    arr = np.array(img.convert('RGB'), dtype=float)
    h, w = arr.shape[:2]

    top = arr[:h//2]

    # Warm/cream wall pixels: R>190, G>165, B>120, and R > B (warm not cool)
    warm_mask = (top[:,:,0] > 190) & (top[:,:,1] > 165) & (top[:,:,2] > 120) & (top[:,:,0] > top[:,:,2])
    warm_ratio = float(warm_mask.mean())

    # Dark furniture/floor pixels in bottom quarter: mean brightness < 140
    bot_bright = arr[3*h//4:].mean(axis=2)
    dark_ratio = float((bot_bright < 140).mean())

    # Low variance in top half = plain wall (uniform color)
    top_std = float(arr[:h//2].mean(axis=2).std())

    is_composite = warm_ratio > 0.40 and dark_ratio > 0.25 and top_std < 65
    reason = f"warm_top={warm_ratio:.2f}, dark_bot={dark_ratio:.2f}, top_std={top_std:.1f}"
    return is_composite, reason


def get_canvas_dims(label: str, w_in, h_in) -> tuple[int, int]:
    """Return canvas pixel dimensions (width, height) for a given size entry."""
    if label in A_SERIES_DIMS:
        return A_SERIES_DIMS[label]
    return (w_in * 300, h_in * 300)


def aspect_ratio(w: int, h: int) -> float:
    return w / h


def fit_art_to_canvas(art: Image.Image, canvas_w: int, canvas_h: int) -> Image.Image:
    """
    Resize art to fill the canvas if aspect ratios are close (within tolerance).
    Otherwise centre the art on a white canvas (letterbox / pillarbox).
    """
    art_w, art_h = art.size
    art_ar = aspect_ratio(art_w, art_h)
    canvas_ar = aspect_ratio(canvas_w, canvas_h)

    ratio_diff = abs(art_ar - canvas_ar) / canvas_ar

    if ratio_diff <= ASPECT_TOLERANCE:
        # Aspect ratios are close enough — resize to fill the canvas exactly
        resized = art.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
        return resized
    else:
        # Letterbox / pillarbox: fit within canvas, centre on white background
        canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))

        # Scale art to fit within canvas while preserving aspect ratio
        scale = min(canvas_w / art_w, canvas_h / art_h)
        new_w = int(art_w * scale)
        new_h = int(art_h * scale)
        resized = art.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Paste centred
        x_off = (canvas_w - new_w) // 2
        y_off = (canvas_h - new_h) // 2
        canvas.paste(resized, (x_off, y_off))
        return canvas


def make_zip(dp_id: str, source_path: Path, quality: int) -> bytes:
    """Build the ZIP in memory and return the raw bytes."""
    buf = io.BytesIO()

    from tools.srgb import ensure_srgb, SRGB_ICC

    with Image.open(source_path) as art:
        # True ICC -> sRGB transform (NOT a bare convert) so AdobeRGB/CMYK sources don't
        # color-shift at the print lab — the top-3 review complaint per CLAUDE.md Gate 1.
        art = ensure_srgb(art)
        art_w, art_h = art.size

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # README
            zf.writestr("README.txt", README_TEXT)

            for (w_in, h_in, subfolder, label) in PRINT_SIZES:
                canvas_w, canvas_h = get_canvas_dims(label, w_in, h_in)
                output = fit_art_to_canvas(art, canvas_w, canvas_h)

                # Encode to JPEG in memory, embedding the sRGB profile
                img_buf = io.BytesIO()
                output.save(img_buf, "JPEG", quality=quality, dpi=(300, 300),
                            icc_profile=SRGB_ICC)
                img_bytes = img_buf.getvalue()

                filename = f"{subfolder}/{dp_id}_{label}.jpg"
                zf.writestr(filename, img_bytes)

    return buf.getvalue()


def process_file(src_path: Path, dp_id: str) -> dict:
    """Create the print-size ZIP for one art file. Returns a result dict."""
    zip_path = PRINT_ZIPS_DIR / f"{dp_id}_print_sizes.zip"

    # Skip if ZIP is newer than source
    if zip_path.exists():
        if zip_path.stat().st_mtime >= src_path.stat().st_mtime:
            size_mb = zip_path.stat().st_size / (1024 * 1024)
            print(f"  SKIP  {dp_id}  (ZIP up-to-date, {size_mb:.1f} MB)")
            return {"id": dp_id, "status": "skipped", "zip_path": zip_path, "size_mb": size_mb}

    # GATE: reject lifestyle composite room scenes before generating print ZIPs
    with Image.open(src_path) as check_img:
        flagged, reason = is_lifestyle_composite(check_img)
    if flagged:
        msg = f"lifestyle composite detected: {reason}"
        print(f"  BLOCKED {dp_id} — source file looks like a lifestyle room scene, not raw art.")
        print(f"          {reason}")
        print(f"          Fix: replace {src_path.name} with the actual raw art file, then re-run.")
        return {"id": dp_id, "status": "error", "error": msg}

    print(f"  Processing {dp_id}  (source: {src_path.name}) ...", end="", flush=True)

    try:
        zip_bytes = make_zip(dp_id, src_path, JPEG_QUALITY_PRIMARY)

        # Step quality down until the ZIP fits Etsy's 20 MB limit. Detailed/large art can
        # blow past it even at the first fallback, so loop rather than try a single level.
        for q in (JPEG_QUALITY_FALLBACK, 70, 65, 60, 55, 50):
            if len(zip_bytes) <= MAX_ZIP_BYTES:
                break
            print(f" {len(zip_bytes)/(1024*1024):.1f} MB > 20 MB, retrying at q={q} ...",
                  end="", flush=True)
            zip_bytes = make_zip(dp_id, src_path, q)

        size_mb = len(zip_bytes) / (1024 * 1024)
        if len(zip_bytes) > MAX_ZIP_BYTES:
            print(f" still {size_mb:.1f} MB after max compression — NOT saved")
            return {"id": dp_id, "status": "error",
                    "error": f"cannot fit under 20 MB ({size_mb:.1f} MB at q=50)"}

        zip_path.write_bytes(zip_bytes)
        print(f" done  ({size_mb:.1f} MB)")
        return {"id": dp_id, "status": "created", "zip_path": zip_path, "size_mb": size_mb}

    except Exception as e:
        print(f" ERROR: {e}")
        return {"id": dp_id, "status": "error", "error": str(e)}


def main():
    PRINT_ZIPS_DIR.mkdir(parents=True, exist_ok=True)

    # Discover all base art files matching the naming convention
    candidates = sorted(
        p for p in PRODUCT_FILES_DIR.glob("*.jpg")
        if re.match(r"^DP1\d+\.jpg$", p.name)
    )

    results = []
    for src_path in candidates:
        dp_id = src_path.stem  # e.g. "DP1030"

        # Prefer the upscaled version if it exists
        upscaled_path = UPSCALED_DIR / src_path.name
        effective_source = upscaled_path if upscaled_path.exists() else src_path

        result = process_file(effective_source, dp_id)
        results.append(result)

    # Summary
    created = [r for r in results if r["status"] == "created"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors  = [r for r in results if r["status"] == "error"]

    print()
    print("=" * 60)
    print(f"ZIP generation complete:")
    print(f"  Created : {len(created)}")
    print(f"  Skipped : {len(skipped)}")
    print(f"  Errors  : {len(errors)}")
    if errors:
        for r in errors:
            print(f"    {r['id']}: {r.get('error')}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    main()
