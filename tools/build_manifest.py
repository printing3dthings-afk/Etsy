#!/usr/bin/env python3
"""
build_manifest.py
Generates/updates data/listing_manifest.json from dp_listing_map.json
and live Etsy listing state.

The manifest is the ground truth for listing_integrity_check.py.
Each key is an Etsy listing_id (string). The value records:
  - expected_files: filename substrings that must appear in the listing's
    digital files (e.g. "DP1094_print_sizes.zip")
  - min_photo_count: minimum accepted listing images
  - type: product type used to pick the right rule set
  - art_hashes: {dp_code: dhash16_hex} for photo-level verification
  - last_verified: ISO timestamp from the last integrity check run

Run this whenever dp_listing_map.json is updated, or to rebuild hashes
after source art files change.

Usage:
    python tools/build_manifest.py            # build / update manifest
    python tools/build_manifest.py --hash     # recompute all art hashes
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

BASE_DIR = Path(__file__).parent.parent
MAP_PATH = BASE_DIR / "data" / "dp_listing_map.json"
MANIFEST_PATH = BASE_DIR / "data" / "listing_manifest.json"
UPSCALED_DIR = BASE_DIR / "data" / "digital_products" / "product_files" / "upscaled"
PRODUCT_FILES_DIR = BASE_DIR / "data" / "digital_products" / "product_files"

# ---------------------------------------------------------------------------
# Minimum photo counts by product type
# ---------------------------------------------------------------------------
PHOTO_MIN = {
    "wall_art":          8,   # goal 10; accept ≥8
    "planner":           8,
    "sticker_pack":      8,
    "gallery_bundle":    5,   # set-of-4 listings often have fewer photos
    "gallery_set":       5,
    "svg_bundle":        3,
    "commercial_license":2,
    "bundle":            5,
    "sublimation":       3,
    "sticker_bundle":    5,
    "unknown":           3,   # catch-all lower bar
}

# ---------------------------------------------------------------------------
# Expected downloadable file count by product type
# ---------------------------------------------------------------------------
FILE_COUNT = {
    "wall_art":          1,   # one print ZIP
    "planner":           3,   # dated PDF + undated PDF + sticker ZIP
    "sticker_pack":      1,   # sticker ZIP
    "gallery_bundle":    1,   # bundle ZIP
    "gallery_set":       1,
    "svg_bundle":        1,
    "commercial_license":1,
    "bundle":            1,
    "sublimation":       1,
    "sticker_bundle":    1,
    "unknown":           1,
}

# ---------------------------------------------------------------------------
# Perceptual hash helpers
# ---------------------------------------------------------------------------

def dhash16(image_path: Path) -> str | None:
    """Compute 256-bit difference hash (16×16 grid) as a hex string."""
    if not PIL_OK:
        return None
    try:
        with Image.open(image_path) as img:
            gray = img.convert("L").resize((17, 16), Image.Resampling.LANCZOS)
            pixels = list(gray.getdata())
            bits = []
            for row in range(16):
                for col in range(16):
                    left = pixels[row * 17 + col]
                    right = pixels[row * 17 + col + 1]
                    bits.append("1" if left > right else "0")
            return hex(int("".join(bits), 2))[2:].zfill(64)
    except Exception:
        return None


def find_art_file(dp_code: str) -> Path | None:
    """Return the best available source art file for a DP code."""
    # Check upscaled first
    for ext in ("jpg", "jpeg", "png"):
        p = UPSCALED_DIR / f"{dp_code}.{ext}"
        if p.exists():
            return p
    # Then product_files directory
    for ext in ("jpg", "jpeg", "png"):
        p = PRODUCT_FILES_DIR / f"{dp_code}.{ext}"
        if p.exists():
            return p
    return None


# ---------------------------------------------------------------------------
# Manifest builder
# ---------------------------------------------------------------------------

def derive_expected_files(dp_code: str, entry: dict) -> list[str]:
    """Return list of expected filename substrings for this entry.

    Only Etsy-deliverable file patterns (ZIPs, PDFs) are included.
    Source art paths (.jpg/.jpeg/.png) are intentionally excluded —
    they live locally and are never uploaded as Etsy digital files.
    """
    IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp")

    raw: list[str] = []

    if "file" in entry:
        raw = [entry["file"]]
    elif "files" in entry:
        f = entry["files"]
        raw = f if isinstance(f, list) else [f]

    # Strip image paths and overly-long paths that look like local file refs
    filtered = [
        p for p in raw
        if p and not any(p.lower().endswith(ext) for ext in IMAGE_EXTS)
        and "/" not in p   # local path separator means it's a source art path
        and "\\" not in p
    ]

    # Normalize legacy _PrintReady.zip patterns → _print_sizes.zip
    normalized = []
    for p in filtered:
        if p.endswith("_PrintReady.zip"):
            p = p.replace("_PrintReady.zip", "_print_sizes.zip")
        normalized.append(p)
    filtered = normalized

    if filtered:
        return filtered

    # Auto-derive sensible patterns from DP code + product type
    t = entry.get("type", "unknown")
    if t == "wall_art":
        return [f"{dp_code}_print_sizes.zip"]
    if t == "planner":
        # Dated PDF + undated PDF + sticker ZIP — all must exist
        return [f"{dp_code}.pdf", f"{dp_code}U.pdf", f"{dp_code}_sticker_pack.zip"]
    if t in ("svg_bundle", "sticker_pack", "sticker_bundle", "commercial_license",
             "gallery_bundle", "gallery_set", "bundle", "sublimation"):
        return [dp_code]   # file name must contain the DP code

    return []   # unknown type — no file expectation enforced


def resolve_product_type(dp_code: str, entry: dict) -> str:
    """Map entry to a canonical product type string."""
    t = entry.get("type", "unknown")
    if t != "unknown":
        return t

    code = dp_code.upper()

    # True planners: only DP1026-DP1029 are confirmed live planners on Etsy.
    # DP1030-DP1033 appear in the product roadmap but their current Etsy listings
    # are wall art prints (title "Kawaii Art Print No.103x") — classify as wall_art.
    planner_codes = {"DP1026", "DP1027", "DP1028", "DP1029"}
    if code in planner_codes:
        return "planner"

    # SVG bundles: DP1073-DP1093
    if code.startswith("DP"):
        try:
            num = int(code[2:])
            if 1073 <= num <= 1093:
                return "svg_bundle"
            if 1000 <= num <= 1072 or 1094 <= num <= 1200:
                return "wall_art"
        except ValueError:
            pass

    # Non-DP keys by keyword
    if "BUNDLE" in code:
        return "bundle"
    if "STICKER" in code:
        return "sticker_pack"
    if "COMMERCIAL" in code:
        return "commercial_license"
    if "SUBLIMATION" in code:
        return "sublimation"
    if "GALLERY" in code:
        return "gallery_bundle"

    return "unknown"


def collect_all_listing_ids(entry: dict, dp_code: str) -> dict[str, str]:
    """
    Return {listing_id_str: id_field_name} for every listing ID in this entry.
    The id_field_name describes which role this listing plays (primary, kawaii, etc.)
    """
    ids = {}
    for field in ("listing_id", "kawaii_listing_id", "planner_listing_id",
                  "individual_listing_id", "secondary_listing_id"):
        lid = entry.get(field)
        if lid:
            ids[str(lid)] = field
    return ids


def build_manifest(recompute_hashes: bool = False) -> dict:
    print("Building listing manifest from dp_listing_map.json …")

    with open(MAP_PATH) as f:
        mapping = json.load(f)

    # Load existing manifest (to preserve last_verified and art_hashes)
    existing: dict = {}
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            existing = json.load(f)

    manifest: dict = {}

    for dp_code, entry in mapping.items():
        if not isinstance(entry, dict):
            continue

        product_type = resolve_product_type(dp_code, entry)
        expected_files = derive_expected_files(dp_code, entry)
        all_ids = collect_all_listing_ids(entry, dp_code)

        # Art hash
        art_hash = None
        art_source = None
        art_file = find_art_file(dp_code)
        if art_file:
            art_source = str(art_file.relative_to(BASE_DIR))
            prev_hash = (existing.get(str(entry.get("listing_id", "")), {})
                         .get("art_hashes", {})
                         .get(dp_code))
            if recompute_hashes or not prev_hash:
                art_hash = dhash16(art_file)
            else:
                art_hash = prev_hash

        for lid_str, id_field in all_ids.items():
            if lid_str not in manifest:
                manifest[lid_str] = {
                    "dp_codes": [],
                    "type": product_type,
                    "expected_files": [],
                    "min_photo_count": PHOTO_MIN.get(product_type, 3),
                    "expected_file_count": FILE_COUNT.get(product_type, 1),
                    "art_hashes": {},
                    "art_sources": {},
                    "listing_roles": {},
                    "last_verified": existing.get(lid_str, {}).get("last_verified"),
                    "last_status": existing.get(lid_str, {}).get("last_status"),
                }

            m = manifest[lid_str]

            # Merge dp codes and expected files (sets of 4 share one listing)
            if dp_code not in m["dp_codes"]:
                m["dp_codes"].append(dp_code)
            for ef in expected_files:
                if ef not in m["expected_files"]:
                    m["expected_files"].append(ef)

            if art_hash:
                m["art_hashes"][dp_code] = art_hash
            if art_source:
                m["art_sources"][dp_code] = art_source

            m["listing_roles"][dp_code] = id_field

            # A listing shared across many DP codes is a bundle/set
            if len(m["dp_codes"]) > 1 and m["type"] not in ("gallery_bundle", "gallery_set", "bundle"):
                m["type"] = "gallery_set"
                m["min_photo_count"] = PHOTO_MIN["gallery_set"]

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    print(f"✓  Manifest written: {len(manifest)} listings → {MANIFEST_PATH.name}")

    # Print summary stats
    type_counts: dict[str, int] = {}
    hashed = 0
    for entry in manifest.values():
        type_counts[entry["type"]] = type_counts.get(entry["type"], 0) + 1
        if entry["art_hashes"]:
            hashed += 1

    print("\nBy type:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")
    print(f"\nListings with art hash (photo verification enabled): {hashed}")

    return manifest


def capture_baseline(manifest: dict) -> None:
    """
    Fetch live Etsy state for every listing and record it in the manifest
    as the authoritative expected baseline.

    This is a one-time (or periodic) operation that 'locks in' the current
    state as the ground truth. After running this, the integrity checker will
    compare against actual Etsy file names rather than derived patterns.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env")
    except ImportError:
        pass

    import sys
    sys.path.insert(0, str(BASE_DIR / "tools"))
    from etsy_api import EtsyAPIClient

    api = EtsyAPIClient()
    print("\nCapturing live Etsy baseline for all listed listings …")
    total = 0
    errors = 0

    for lid_str, entry in manifest.items():
        print(f"  [{lid_str}] fetching …", end=" ", flush=True)
        try:
            files_resp = api._request("GET", f"shops/{api.shop_id}/listings/{lid_str}/files")
            files = files_resp.get("results", [])
            file_names = sorted(f.get("filename", "") for f in files)

            images_resp = api._request("GET", f"listings/{lid_str}/images")
            images = images_resp.get("results", [])

            # Record current state as the baseline
            entry["baseline_files"] = file_names
            entry["baseline_photo_count"] = len(images)
            entry["expected_files"] = file_names   # overwrite derived patterns
            entry["min_photo_count"] = len(images) if len(images) > 0 else entry.get("min_photo_count", 3)
            entry["expected_file_count"] = len(files)
            entry["baseline_captured"] = datetime.now(timezone.utc).isoformat()

            print(f"OK ({len(files)} files, {len(images)} photos)")
            total += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

    print(f"\nBaseline capture complete: {total} listings updated, {errors} errors")

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    print(f"✓ Manifest updated with baseline → {MANIFEST_PATH.name}")


def main():
    parser = argparse.ArgumentParser(description="Build listing manifest from dp_listing_map.json")
    parser.add_argument("--hash", action="store_true", help="Recompute all art hashes from source files")
    parser.add_argument("--baseline", action="store_true",
                        help="Capture live Etsy file/photo state as the expected baseline")
    args = parser.parse_args()

    manifest = build_manifest(recompute_hashes=args.hash)

    if args.baseline:
        capture_baseline(manifest)


if __name__ == "__main__":
    main()
