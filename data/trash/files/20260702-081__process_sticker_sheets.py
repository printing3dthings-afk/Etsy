#!/usr/bin/env python3
"""
process_sticker_sheets.py
Turn raw AI-generated sticker sheets (white-background JPGs) into production-grade
sticker assets that meet the OnBrandCraftz sticker standards:

  • Transparent background  (white-box JPGs import into GoodNotes as opaque squares —
    this is the #1 sticker quality defect; removing the background is the whole point)
  • 3000×3000px PNG sheets  (300 DPI at 10 inches)
  • Individual pre-cropped sticker PNGs  (one file per sticker, tight transparent crop)
  • A clean ZIP with png_sheets/ + individual_stickers/ + import instructions

Background removal is a BORDER flood-fill: only white that is connected to the edge of
the sheet is made transparent. White *inside* a sticker (eye catch-lights, highlights,
paper) is preserved because it is not connected to the border.

Usage:
    python tools/process_sticker_sheets.py --pid DP1026                 # all sheets found
    python tools/process_sticker_sheets.py --pid DP1030 --sheets 5      # first 5 sheets
    python tools/process_sticker_sheets.py --pid DP1026 --no-individual # sheets only
    python tools/process_sticker_sheets.py --all                        # every DP found
"""

import argparse
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

BASE_DIR = Path(__file__).parent.parent
ART_DIR = BASE_DIR / "data" / "digital_products" / "product_files"
STICKER_OUT = BASE_DIR / "data" / "digital_products" / "stickers"

SHEET_PX = 3000          # final sheet resolution (square)
WHITE_THRESHOLD = 238    # a pixel is "background-white" if all RGB channels >= this
MIN_STICKER_AREA = 2500  # ignore connected blobs smaller than this many px (specks)
CROP_PAD = 12            # transparent padding around each cropped individual sticker
INDIV_MAX_PX = 800       # cap individual sticker longest edge (300 DPI at ~2.7in)

HOW_TO = """HOW TO USE YOUR STICKERS  —  OnBrandCraftz
==========================================

You get TWO formats in this pack:
  • /png_sheets/         — full sticker sheets, transparent background, 3000x3000px
  • /individual_stickers/ — every sticker pre-cut as its own transparent PNG

GoodNotes 6 (recommended):
  1. Download and unzip this pack
  2. Open GoodNotes 6 -> tap Elements (diamond icon) -> Stickers tab -> tap +
  3. Select the sheet PNGs from /png_sheets/  ->  tap Done
  4. Every sticker now lives in your library — drag any one onto any page, unlimited times!
  (Prefer single stickers? Import from /individual_stickers/ instead.)

Notability:
  • Insert a sheet as a photo, or insert single stickers from /individual_stickers/

PDF Expert / Xodo / Adobe Acrobat:
  • Insert individual sticker PNGs as image annotations, then resize

Printing:
  • Sheets are 300 DPI, print-ready on sticker paper for physical use.

(c) OnBrandCraftz - Personal use only - Not for resale or redistribution
"""


def _load_rgb(path: Path) -> Image.Image:
    im = Image.open(path)
    return im.convert("RGB") if im.mode != "RGB" else im


def _save_png(rgba: Image.Image, path: Path, colors: int = 256) -> None:
    """Save an RGBA image as an optimized, palette-quantized transparent PNG.

    Sticker art has a small color count (thick outlines + flat pastel fills), so a
    256-color palette cuts file size ~85% with no visible loss while preserving the
    alpha channel — this is what keeps the pack under Etsy's 20MB per-file limit.
    """
    q = rgba.quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
    q.save(path, "PNG", optimize=True)


def remove_white_background(img: Image.Image) -> Image.Image:
    """Return an RGBA image with edge-connected white made transparent.

    Interior white (catch-lights, highlights) is preserved because the flood
    only removes white regions that touch the sheet border.
    """
    rgb = np.asarray(img, dtype=np.uint8)
    h, w = rgb.shape[:2]

    # Mask of "white-ish" pixels
    white = np.all(rgb >= WHITE_THRESHOLD, axis=2)

    # Label connected white regions (4-connectivity is safer — avoids leaking
    # through 1px diagonal gaps between a sticker and the background)
    structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)
    labeled, n = ndimage.label(white, structure=structure)
    if n == 0:
        # No white at all — fully opaque
        alpha = np.full((h, w), 255, dtype=np.uint8)
        return Image.fromarray(np.dstack([rgb, alpha]))

    # Any label that appears on the border is background
    border_labels = set()
    border_labels.update(np.unique(labeled[0, :]).tolist())
    border_labels.update(np.unique(labeled[-1, :]).tolist())
    border_labels.update(np.unique(labeled[:, 0]).tolist())
    border_labels.update(np.unique(labeled[:, -1]).tolist())
    border_labels.discard(0)  # 0 = non-white, never background by this rule

    background = np.isin(labeled, list(border_labels))

    # Soften the cut edge by 1px to reduce white haloing (erode the opaque area
    # slightly so anti-aliased white fringe pixels are dropped)
    opaque = ~background
    opaque_eroded = ndimage.binary_erosion(opaque, structure=structure, iterations=1)
    # Keep original opaque interior but trimmed boundary
    alpha = np.where(opaque_eroded, 255, 0).astype(np.uint8)

    return Image.fromarray(np.dstack([rgb, alpha]))


def segment_stickers(rgba: Image.Image) -> list[Image.Image]:
    """Split a transparent sheet into individual sticker crops via connected
    components on the alpha channel."""
    arr = np.asarray(rgba)
    alpha = arr[:, :, 3]
    opaque = alpha > 0

    structure = np.ones((3, 3), dtype=bool)  # 8-connectivity for grouping a sticker
    labeled, n = ndimage.label(opaque, structure=structure)
    if n == 0:
        return []

    crops = []
    slices = ndimage.find_objects(labeled)
    for idx, sl in enumerate(slices, start=1):
        if sl is None:
            continue
        ys, xs = sl
        area = int((labeled[sl] == idx).sum())
        if area < MIN_STICKER_AREA:
            continue
        top = max(0, ys.start - CROP_PAD)
        bottom = min(arr.shape[0], ys.stop + CROP_PAD)
        left = max(0, xs.start - CROP_PAD)
        right = min(arr.shape[1], xs.stop + CROP_PAD)

        crop = arr[top:bottom, left:right].copy()
        # Zero out pixels belonging to OTHER components inside this bbox
        local_label = labeled[top:bottom, left:right]
        keep = (local_label == idx) | (local_label == 0)
        crop[~keep, 3] = 0
        crops.append(Image.fromarray(crop))

    # Sort largest-first so file numbering is roughly biggest sticker = 01
    crops.sort(key=lambda im: im.size[0] * im.size[1], reverse=True)
    return crops


def process_pid(pid: str, max_sheets: int | None, make_individual: bool) -> dict:
    out_dir = STICKER_OUT / pid
    sheets_dir = out_dir / "png_sheets"
    indiv_dir = out_dir / "individual_stickers"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    if make_individual:
        indiv_dir.mkdir(parents=True, exist_ok=True)

    # Find source sheets (prefer .jpg, fall back to .png)
    sources = []
    n = 1
    while True:
        if max_sheets and n > max_sheets:
            break
        found = None
        for ext in (".jpg", ".png"):
            p = ART_DIR / f"{pid}_sticker_sheet_{n}{ext}"
            if p.exists():
                found = p
                break
        if found is None:
            if n <= 5:
                # gap in early sheets — keep looking up to 5
                n += 1
                continue
            break
        sources.append((n, found))
        n += 1

    if not sources:
        print(f"  No source sheets found for {pid} in {ART_DIR}")
        return {}

    total_stickers = 0
    sheet_files = []
    indiv_count = 0

    for sheet_num, src in sources:
        print(f"  Sheet {sheet_num}: {src.name}", end="", flush=True)
        rgb = _load_rgb(src)
        rgba = remove_white_background(rgb)
        if rgba.size != (SHEET_PX, SHEET_PX):
            rgba = rgba.resize((SHEET_PX, SHEET_PX), Image.Resampling.LANCZOS)

        out_sheet = sheets_dir / f"{pid}_sheet_{sheet_num:02d}.png"
        _save_png(rgba, out_sheet)
        sheet_files.append(out_sheet)

        if make_individual:
            crops = segment_stickers(rgba)
            for i, crop in enumerate(crops, start=1):
                longest = max(crop.size)
                if longest > INDIV_MAX_PX:
                    scale = INDIV_MAX_PX / longest
                    crop = crop.resize((round(crop.size[0] * scale),
                                        round(crop.size[1] * scale)),
                                       Image.Resampling.LANCZOS)
                _save_png(crop, indiv_dir / f"{pid}_s{sheet_num:02d}_{i:02d}.png")
            total_stickers += len(crops)
            indiv_count += len(crops)
            print(f"  -> transparent PNG + {len(crops)} stickers")
        else:
            print("  -> transparent PNG")

    print(f"  {pid}: {len(sheet_files)} sheets, {indiv_count} individual stickers")
    return {
        "pid": pid,
        "sheets": sheet_files,
        "indiv_dir": indiv_dir if make_individual else None,
        "sticker_count": indiv_count,
    }


ZIP_BUDGET_KB = 19 * 1024   # stay comfortably under Etsy's 20MB hard per-file limit


def _zip_kb(result: dict) -> int:
    pid = result["pid"]
    zip_path = ART_DIR / f"{pid}_sticker_pack.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("HOW_TO_USE_STICKERS.txt", HOW_TO)
        for sheet in result["sheets"]:
            zf.write(sheet, f"png_sheets/{sheet.name}")
        if result.get("indiv_dir") and result["indiv_dir"].exists():
            for png in sorted(result["indiv_dir"].glob("*.png")):
                zf.write(png, f"individual_stickers/{png.name}")
    return zip_path.stat().st_size // 1024


def build_zip(result: dict) -> Path:
    """Build the pack ZIP, adaptively re-quantizing sheets if over the size budget."""
    pid = result["pid"]
    size_kb = _zip_kb(result)

    # If over budget, step the sheet palette down until it fits (sticker art tolerates
    # a smaller palette with no visible loss — outlines + flat fills).
    for colors in (192, 128, 96):
        if size_kb <= ZIP_BUDGET_KB:
            break
        print(f"  ZIP {size_kb} KB over budget — recompressing sheets at {colors} colors")
        for sheet in result["sheets"]:
            with Image.open(sheet) as im:
                _save_png(im.convert("RGBA"), sheet, colors=colors)
        size_kb = _zip_kb(result)

    zip_path = ART_DIR / f"{pid}_sticker_pack.zip"
    print(f"  ZIP: {zip_path.name} ({size_kb} KB)")
    if size_kb > 20 * 1024:
        print(f"  WARNING: ZIP still exceeds Etsy's 20MB per-file limit")
    return zip_path


def main():
    ap = argparse.ArgumentParser(description="Process raw sticker sheets into transparent production assets")
    ap.add_argument("--pid", help="Product ID, e.g. DP1026")
    ap.add_argument("--all", action="store_true", help="Process every DP with sticker sheets")
    ap.add_argument("--sheets", type=int, default=None, help="Max sheet number to process")
    ap.add_argument("--no-individual", action="store_true", help="Skip individual sticker crops")
    ap.add_argument("--no-zip", action="store_true", help="Skip rebuilding the ZIP")
    args = ap.parse_args()

    if args.all:
        pids = sorted({p.name.split("_sticker_sheet_")[0]
                       for p in ART_DIR.glob("DP*_sticker_sheet_*")})
    elif args.pid:
        pids = [args.pid.upper()]
    else:
        ap.error("provide --pid DP#### or --all")

    print(f"Processing sticker sheets for: {', '.join(pids)}\n")
    for pid in pids:
        print(f"== {pid} ==")
        result = process_pid(pid, args.sheets, not args.no_individual)
        if result and not args.no_zip:
            build_zip(result)
        print()


if __name__ == "__main__":
    main()
