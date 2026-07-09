#!/usr/bin/env python3
"""
build_art_registry.py
Scans data/digital_products/product_files/upscaled/ for DP*.jpg files,
computes dhash16 for each, and writes data/product_art_registry.json.

After building from files, cross-references data/dp_listing_map.json to
populate listing_ids for each DP code.

Usage:
    python tools/build_art_registry.py           # build/update full registry
    python tools/build_art_registry.py --update  # add new files only, skip existing
"""

import argparse
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

BASE_DIR = Path(__file__).parent.parent
UPSCALED_DIR = BASE_DIR / "data" / "digital_products" / "product_files" / "upscaled"
REGISTRY_PATH = BASE_DIR / "data" / "product_art_registry.json"
MAP_PATH = BASE_DIR / "data" / "dp_listing_map.json"


def dhash16(image_bytes: bytes) -> str | None:
    """
    Compute dhash16 of an image, square-normalizing first.

    All wall art source files are portrait (2:3). Listing photos are square (1:1).
    Computing dhash on a portrait vs a square produces high distances even when the
    art is the same — the 17×16 grid captures different content at different aspect
    ratios. Square-normalizing both sides before hashing gives distances of 0-10 for
    matching art, vs 90+ for unrelated images or room-scene composites.
    """
    if not PIL_OK:
        return None
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Center-crop to square before hashing (normalizes portrait vs square comparison)
            w, h = img.size
            s = min(w, h)
            left = (w - s) // 2
            top = (h - s) // 2
            img = img.crop((left, top, left + s, top + s))
            gray = img.convert("L").resize((17, 16), Image.Resampling.LANCZOS)
            pixels = list(gray.getdata())
            bits = []
            for row in range(16):
                for col in range(16):
                    bits.append("1" if pixels[row * 17 + col] > pixels[row * 17 + col + 1] else "0")
            return hex(int("".join(bits), 2))[2:].zfill(64)
    except Exception:
        return None


def get_image_dimensions(image_bytes: bytes) -> list[int]:
    if not PIL_OK:
        return [0, 0]
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            return list(img.size)
    except Exception:
        return [0, 0]


def build_listing_id_map(map_path: Path) -> dict[str, list[int]]:
    """Return {dp_code: [listing_id, ...]} from dp_listing_map.json."""
    if not map_path.exists():
        return {}
    with open(map_path) as f:
        dp_map = json.load(f)

    result: dict[str, list[int]] = {}
    id_fields = ("listing_id", "kawaii_listing_id", "planner_listing_id",
                 "individual_listing_id", "secondary_listing_id")
    for dp_code, entry in dp_map.items():
        if not isinstance(entry, dict):
            continue
        ids = set()
        for key in id_fields:
            val = entry.get(key)
            if val:
                ids.add(int(val))
        if ids:
            result[dp_code] = sorted(ids)
    return result


def main():
    parser = argparse.ArgumentParser(description="Build/update product art registry")
    parser.add_argument("--update", action="store_true",
                        help="Add new files only; skip DP codes already in the registry")
    args = parser.parse_args()

    if not PIL_OK:
        print("ERROR: Pillow is not installed. Run: pip install Pillow")
        sys.exit(1)

    if not UPSCALED_DIR.exists():
        print(f"ERROR: Upscaled directory not found: {UPSCALED_DIR}")
        sys.exit(1)

    # Load existing registry
    registry: dict = {}
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH) as f:
            registry = json.load(f)

    # Build listing ID map from dp_listing_map.json
    listing_id_map = build_listing_id_map(MAP_PATH)

    art_files = sorted(UPSCALED_DIR.glob("DP*.jpg"))
    if not art_files:
        print(f"No DP*.jpg files found in {UPSCALED_DIR}")
        sys.exit(0)

    added = 0
    skipped = 0
    updated = 0

    for art_path in art_files:
        dp_code = art_path.stem  # e.g. "DP1094"

        if args.update and dp_code in registry:
            skipped += 1
            continue

        image_bytes = art_path.read_bytes()
        source_hash = dhash16(image_bytes)
        if not source_hash:
            print(f"  WARN: Could not hash {art_path.name} — skipping")
            continue

        dims = get_image_dimensions(image_bytes)
        file_size_mb = round(art_path.stat().st_size / (1024 * 1024), 2)

        was_existing = dp_code in registry
        registry[dp_code] = {
            "source_file": str(art_path.relative_to(BASE_DIR)),
            "source_hash": source_hash,
            "file_size_mb": file_size_mb,
            "image_dimensions": dims,
            "registered_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "listing_ids": listing_id_map.get(dp_code, []),
        }

        if was_existing:
            updated += 1
        else:
            added += 1
        print(f"  {'Updated' if was_existing else 'Added'} {dp_code}: {source_hash[:16]}… "
              f"({dims[0]}x{dims[1]}, {file_size_mb}MB)")

    # Also update listing_ids for existing entries that may have been skipped
    if args.update:
        for dp_code, entry in registry.items():
            new_ids = listing_id_map.get(dp_code, [])
            if new_ids != entry.get("listing_ids", []):
                entry["listing_ids"] = new_ids

    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2, sort_keys=True)

    print(f"\nRegistry written to {REGISTRY_PATH}")
    print(f"  {added} added, {updated} updated, {skipped} skipped")
    print(f"  Total entries: {len(registry)}")


if __name__ == "__main__":
    main()
