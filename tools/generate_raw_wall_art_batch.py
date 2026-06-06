#!/usr/bin/env python3
"""
Generate raw printable wall art images for 7 DP codes.
Steps per code:
  1. Generate 1024x1536 PNG via gpt-image-1
  2. Upscale 4x (Lanczos + UnsharpMask) → save as upscaled/DP{CODE}.jpg @ quality=95
  3. Generate multi-size print ZIP → save as print_zips/DP{CODE}_print_sizes.zip
"""

import os
import sys
import zipfile
import io
import math
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageFilter

# ── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = Path("/home/user/Etsy")
PRODUCT_FILES = BASE_DIR / "data/digital_products/product_files"
UPSCALED_DIR  = PRODUCT_FILES / "upscaled"
PRINT_ZIPS    = BASE_DIR / "data/digital_products/print_zips"

UPSCALED_DIR.mkdir(parents=True, exist_ok=True)
PRINT_ZIPS.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ── Print size definitions ────────────────────────────────────────────────────
# (folder, filename, width_px, height_px) at 300 DPI
PRINT_SIZES = [
    # 2x3 ratio
    ("2x3",   "4x6_300dpi",   1200,  1800),
    ("2x3",   "8x12_300dpi",  2400,  3600),
    ("2x3",   "12x18_300dpi", 3600,  5400),
    ("2x3",   "16x24_300dpi", 4800,  7200),
    # 4x5 ratio
    ("4x5",   "8x10_300dpi",  2400,  3000),
    ("4x5",   "16x20_300dpi", 4800,  6000),
    # A series (standard pixel sizes at 300 DPI)
    ("a_series", "A4_300dpi",  2481,  3507),
    ("a_series", "A3_300dpi",  3507,  4962),
    # Square
    ("square", "8x8_300dpi",   2400,  2400),
    ("square", "12x12_300dpi", 3600,  3600),
]

README_TEXT = """OnBrandCraftz — Print Size Guide
=================================

This ZIP contains your art in multiple print-ready sizes at 300 DPI.

Folders:
  2x3/       → 4x6", 8x12", 12x18", 16x24" prints
  4x5/       → 8x10", 16x20" prints
  a_series/  → A4, A3 prints (international standard)
  square/    → 8x8", 12x12" square prints

Printing Tips:
• Use the size closest to your frame size
• Print on matte or lustre photo paper for best results
• "Fit to page" or "Actual size" — do NOT use "Shrink to fit"
• sRGB color space is set for accurate home and lab printing

Questions? Email: Printing3dthings@outlook.com
© OnBrandCraftz — Personal use only. Not for resale.
"""

# ── Art prompts ──────────────────────────────────────────────────────────────
ARTWORKS = [
    {
        "code": "DP1059",
        "prompt": (
            "A minimalist botanical art print of a single dried pampas grass plume in soft watercolor style. "
            "Warm cream/ivory background. The pampas grass is centered, rendered in muted golden and beige tones "
            "with delicate feathery texture. Modern boho aesthetic. No room, no frame, no furniture — just the art "
            "itself on a plain cream background. Portrait orientation."
        ),
    },
    {
        "code": "DP1060",
        "prompt": (
            "A delicate botanical art print showing a loose bouquet of wildflowers in watercolor style. "
            "Includes pampas grass, small white daisies, lavender sprigs, and rosehip berries. "
            "Soft warm cream/white background. Muted natural colors — sage green stems, dusty pink petals, "
            "pale lavender, warm ivory. Modern cottagecore botanical illustration. No room, no frame — "
            "just the art on a plain background. Portrait orientation."
        ),
    },
    {
        "code": "DP1061",
        "prompt": (
            "A clean minimalist watercolor botanical print of a single eucalyptus branch with round silver-dollar "
            "leaves in soft blue-green tones. Simple cream/white background. Delicate watercolor texture, soft sage "
            "and mint green tones. Modern minimalist botanical art print style. No room, no frame — just the "
            "eucalyptus branch centered on a plain light background. Portrait orientation."
        ),
    },
    {
        "code": "DP1063",
        "prompt": (
            "A vibrant watercolor art print of tropical orange and peach flowers with teal green leaves. "
            "Bold, painterly watercolor style. Bright warm orange blossoms (like hibiscus or cosmos) with lush "
            "green foliage on a soft light background. Fresh, energetic botanical art. No room, no frame — "
            "just the floral art on a plain light background. Portrait orientation."
        ),
    },
    {
        "code": "DP1064",
        "prompt": (
            "A bold graphic art print of tropical leaves — monstera leaf, palm fronds, and banana leaf — in a "
            "Matisse-inspired flat illustration style. Rich colors: deep forest green, cobalt blue, burnt orange. "
            "Cream or warm white background. Modern, graphic, bold. No room, no frame — just the leaf art on a "
            "plain background. Portrait orientation."
        ),
    },
    {
        "code": "DP1067",
        "prompt": (
            "A soft impressionist painting of cherry blossom branches in full bloom. Delicate pink sakura flowers "
            "against a pale blue-grey sky background. Painterly brushwork, gentle pastel tones — pale pink petals, "
            "dusty rose, soft green. Japanese spring aesthetic. No room, no frame — just the cherry blossom "
            "painting. Portrait orientation."
        ),
    },
    {
        "code": "DP1078",
        "prompt": (
            "A detailed watercolor art print of a ruby-throated hummingbird hovering among garden flowers — "
            "foxglove, roses, cosmos. Lush green garden background. Vivid natural colors: emerald green hummingbird "
            "with ruby red throat, pink and peach roses, lavender foxglove. Detailed botanical illustration style. "
            "No room, no frame — just the art on a warm light background. Portrait orientation."
        ),
    },
]


def generate_image(code: str, prompt: str) -> Path:
    """Generate 1024x1536 PNG via gpt-image-1 and save as DP{code}_raw.png."""
    raw_path = PRODUCT_FILES / f"{code}_raw.png"
    print(f"  [{code}] Generating image via gpt-image-1 ...")
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1536",
        quality="high",
        output_format="png",
        n=1,
    )
    # gpt-image-1 returns base64 by default
    import base64
    b64_data = response.data[0].b64_json
    png_bytes = base64.b64decode(b64_data)
    raw_path.write_bytes(png_bytes)
    print(f"  [{code}] Raw PNG saved → {raw_path} ({len(png_bytes)/1024:.0f} KB)")
    return raw_path


def upscale_image(code: str, raw_path: Path) -> Path:
    """4x Lanczos upscale + UnsharpMask → save as upscaled/DP{code}.jpg @ q=95."""
    out_path = UPSCALED_DIR / f"{code}.jpg"
    print(f"  [{code}] Upscaling 4x ...")
    img = Image.open(raw_path).convert("RGB")
    w, h = img.size
    new_w, new_h = w * 4, h * 4
    img_up = img.resize((new_w, new_h), Image.LANCZOS)
    img_sharp = img_up.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    img_sharp.save(out_path, "JPEG", quality=95, optimize=True)
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"  [{code}] Upscaled JPG saved → {out_path} ({size_mb:.1f} MB, {new_w}x{new_h}px)")
    return out_path, img_sharp


def center_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Center-crop image to exact target dimensions, scaling first if needed."""
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    tgt_ratio = target_w / target_h

    if src_ratio > tgt_ratio:
        # Source is wider → scale by height
        scale = target_h / src_h
    else:
        # Source is taller → scale by width
        scale = target_w / src_w

    scaled_w = max(target_w, math.ceil(src_w * scale))
    scaled_h = max(target_h, math.ceil(src_h * scale))
    img_scaled = img.resize((scaled_w, scaled_h), Image.LANCZOS)

    left = (scaled_w - target_w) // 2
    top  = (scaled_h - target_h) // 2
    return img_scaled.crop((left, top, left + target_w, top + target_h))


def build_zip(code: str, upscaled_img: Image.Image, quality: int = 70) -> tuple[Path, int]:
    """Build multi-size print ZIP from the upscaled image."""
    zip_path = PRINT_ZIPS / f"{code}_print_sizes.zip"
    print(f"  [{code}] Building print ZIP (quality={quality}) ...")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("README.txt", README_TEXT)
        for folder, filename, tw, th in PRINT_SIZES:
            cropped = center_crop(upscaled_img, tw, th)
            img_buf = io.BytesIO()
            cropped.save(img_buf, "JPEG", quality=quality, optimize=True)
            arcname = f"{folder}/{code}_{filename}.jpg"
            zf.writestr(arcname, img_buf.getvalue())

    zip_bytes = buf.getvalue()
    zip_mb = len(zip_bytes) / (1024 * 1024)
    print(f"  [{code}] ZIP size: {zip_mb:.1f} MB")
    return zip_bytes, zip_mb


def generate_print_zip(code: str, upscaled_img: Image.Image) -> Path:
    """Build ZIP, reduce quality if over 20 MB."""
    zip_path = PRINT_ZIPS / f"{code}_print_sizes.zip"

    for quality in [70, 65, 60]:
        zip_bytes, zip_mb = build_zip(code, upscaled_img, quality)
        if zip_mb <= 20.0:
            zip_path.write_bytes(zip_bytes)
            print(f"  [{code}] ZIP saved → {zip_path} ({zip_mb:.1f} MB)")
            return zip_path
        print(f"  [{code}] ZIP {zip_mb:.1f} MB > 20 MB, retrying at lower quality ...")

    # Last resort: just save at q=60 even if slightly over
    zip_path.write_bytes(zip_bytes)
    print(f"  [{code}] WARNING: ZIP saved at {zip_mb:.1f} MB (may exceed Etsy limit) → {zip_path}")
    return zip_path


def process_one(artwork: dict) -> dict:
    code   = artwork["code"]
    prompt = artwork["prompt"]
    result = {"code": code, "status": "ok", "errors": []}

    try:
        raw_path = generate_image(code, prompt)
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Image generation failed: {e}")
        return result

    try:
        upscaled_path, upscaled_img = upscale_image(code, raw_path)
        result["upscaled_path"] = str(upscaled_path)
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Upscale failed: {e}")
        return result

    try:
        zip_path = generate_print_zip(code, upscaled_img)
        result["zip_path"] = str(zip_path)
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"ZIP generation failed: {e}")

    return result


def main():
    import argparse
    from concurrent.futures import ThreadPoolExecutor, as_completed

    ap = argparse.ArgumentParser(description="Generate raw printable wall art batch")
    ap.add_argument("--workers", type=int, default=4,
                    help="Parallel workers (default 4; use 1 for sequential)")
    args = ap.parse_args()

    print(f"Processing {len(ARTWORKS)} DP codes with {args.workers} worker(s)\n{'='*60}")

    # process_one() is self-contained and I/O-bound (API + image work), so a small
    # thread pool cuts wall-clock time roughly Nx without changing results.
    if args.workers <= 1:
        results = [process_one(a) for a in ARTWORKS]
    else:
        results = []
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(process_one, a): a["code"] for a in ARTWORKS}
            for fut in as_completed(futures):
                code = futures[fut]
                try:
                    results.append(fut.result())
                except Exception as e:  # noqa: BLE001 — record, never crash the batch
                    results.append({"code": code, "status": "error", "errors": [str(e)]})
                print(f"  [{code}] done ({sum(1 for r in results)}/{len(ARTWORKS)})")
        results.sort(key=lambda r: [a["code"] for a in ARTWORKS].index(r["code"]))

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    ok_count  = sum(1 for r in results if r["status"] == "ok")
    err_count = sum(1 for r in results if r["status"] != "ok")
    for r in results:
        status = "OK" if r["status"] == "ok" else "ERROR"
        print(f"  {r['code']}: {status}")
        if r.get("upscaled_path"):
            print(f"    Upscaled → {r['upscaled_path']}")
        if r.get("zip_path"):
            print(f"    ZIP      → {r['zip_path']}")
        for err in r.get("errors", []):
            print(f"    ERROR: {err}")
    print(f"\nCompleted: {ok_count} OK, {err_count} errors")


if __name__ == "__main__":
    main()
