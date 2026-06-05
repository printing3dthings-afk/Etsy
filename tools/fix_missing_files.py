#!/usr/bin/env python3
"""
fix_missing_files.py — Attach correct digital download files to the 74 listings
that currently have no files attached. Customers buying those listings receive nothing.

Rules (applied in order):
  1. Physical product IDs → SKIP
  2. "Kawaii Art Print No.XXXX" → DP{XXXX}_print_sizes.zip
  3. Sticker pack titles → matching sticker zip
  4. SVG bundle titles → matching SVG zip
  5. dp_listing_map.json matches → print zip by DP number
  6. Remaining generic art prints → dhash match against upscaled/ dir

Rate limit: 2 s between uploads.
"""

import json
import os
import sys
import time
import urllib.request
import re

# ── Add project root to path ──────────────────────────────────────────────────
PROJECT_ROOT = "/home/user/Etsy"
sys.path.insert(0, PROJECT_ROOT)
from tools.etsy_api import EtsyAPIClient

# ── Paths ─────────────────────────────────────────────────────────────────────
LISTINGS_JSON      = "/tmp/no_files_listings.json"
PRINT_ZIPS_DIR     = f"{PROJECT_ROOT}/data/digital_products/print_zips"
PRODUCT_FILES_DIR  = f"{PROJECT_ROOT}/data/digital_products/product_files"
UPSCALED_DIR       = f"{PRODUCT_FILES_DIR}/upscaled"
DP_MAP_FILE        = f"{PROJECT_ROOT}/data/dp_listing_map.json"
RESULTS_JSON       = "/tmp/fix_results.json"

# ── Physical product listing IDs (SKIP — no digital file needed) ──────────────
PHYSICAL_IDS = {
    4506555435, 4507783049, 4506562262, 4506559866, 4506557906,
    4497769840, 4497392795, 4497385915, 4492610660, 4490472707,
    4488666558, 4488532602, 4488477854,
}

# ── Sticker pack title → zip file ─────────────────────────────────────────────
STICKER_MAP = {
    "lavender":    f"{PRODUCT_FILES_DIR}/DP1026_sticker_pack.zip",
    "cotton can":  f"{PRODUCT_FILES_DIR}/DP1027_sticker_pack.zip",
    "midnight b":  f"{PRODUCT_FILES_DIR}/DP1028_sticker_pack.zip",
    "coral peac":  f"{PRODUCT_FILES_DIR}/DP1029_sticker_pack.zip",
    "bundle all":  f"{PRODUCT_FILES_DIR}/All_4_Sticker_Packs.zip",
}

# ── SVG bundle title → zip file ───────────────────────────────────────────────
SVG_MAP = {
    "good vibes svg":       f"{PROJECT_ROOT}/data/groovy_pack/OnBrandCraftz_GoodVibes_SVG_Bundle_20_Designs.zip",
    "mom life svg":         f"{PROJECT_ROOT}/data/mom_life_pack/OnBrandCraftz_MomLife_SVG_Bundle_20_Designs.zip",
    "graduation":           f"{PROJECT_ROOT}/data/grad_pack/Graduation2026_SVG_Bundle.zip",
    "christian faith":      f"{PROJECT_ROOT}/data/faith_pack/ChristianFaith_SVG_Bundle.zip",
    "floral botanical":     f"{PROJECT_ROOT}/data/svg_pack/FlowerBotanical_Bundle.zip",
    "western svg":          f"{PROJECT_ROOT}/data/svg_bundles/western/OnBrandCraftz_western_SVG_Bundle.zip",
}


def dhash(image_path: str, hash_size: int = 16) -> int | None:
    """Compute difference hash for an image. Returns integer or None on error."""
    try:
        from PIL import Image
        img = Image.open(image_path).convert("L").resize(
            (hash_size + 1, hash_size), Image.LANCZOS
        )
        pixels = list(img.getdata())
        bits = []
        for row in range(hash_size):
            for col in range(hash_size):
                idx = row * (hash_size + 1) + col
                bits.append(1 if pixels[idx] > pixels[idx + 1] else 0)
        value = 0
        for bit in bits:
            value = (value << 1) | bit
        return value
    except Exception as e:
        print(f"    [dhash error] {image_path}: {e}")
        return None


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def fetch_listing_image_url(client: EtsyAPIClient, listing_id: int) -> str | None:
    """Fetch the first listing image URL from the Etsy API."""
    try:
        result = client._request("GET", f"listings/{listing_id}/images")
        images = result.get("results", [])
        if images:
            return images[0].get("url_570xN") or images[0].get("url_fullxfull")
        return None
    except Exception as e:
        print(f"    [image fetch error] listing {listing_id}: {e}")
        return None


def download_image(url: str, dest_path: str) -> bool:
    """Download an image to dest_path. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(dest_path, "wb") as f:
                f.write(resp.read())
        return True
    except Exception as e:
        print(f"    [download error] {url}: {e}")
        return False


def get_print_zip(dp_num: str) -> str | None:
    """Return path to print ZIP for a DP number, or None if not found."""
    path = f"{PRINT_ZIPS_DIR}/DP{dp_num}_print_sizes.zip"
    return path if os.path.exists(path) else None


def load_dp_listing_map() -> dict:
    """Load dp_listing_map.json. Returns {listing_id -> dp_key}."""
    if not os.path.exists(DP_MAP_FILE):
        return {}
    with open(DP_MAP_FILE) as f:
        raw = json.load(f)
    # Build reverse map: listing_id -> dp_key (e.g. "DP1030")
    reverse = {}
    for dp_key, info in raw.items():
        lid = info.get("listing_id")
        if lid:
            reverse[int(lid)] = dp_key
    return reverse


def build_upscaled_hashes() -> list[tuple[str, int]]:
    """Build list of (file_path, dhash_int) for all files in upscaled dir."""
    results = []
    if not os.path.isdir(UPSCALED_DIR):
        return results
    for fname in sorted(os.listdir(UPSCALED_DIR)):
        fpath = os.path.join(UPSCALED_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        h = dhash(fpath)
        if h is not None:
            results.append((fpath, h))
    return results


def match_sticker_title(title_lower: str) -> str | None:
    """Match sticker pack listing title → zip path."""
    for key, path in STICKER_MAP.items():
        if key in title_lower:
            return path
    return None


def match_svg_title(title_lower: str) -> str | None:
    """Match SVG bundle listing title → zip path."""
    for key, path in SVG_MAP.items():
        if key in title_lower:
            if os.path.exists(path):
                return path
            print(f"    [SVG ZIP missing on disk] {path}")
            return None
    return None


def main():
    print("=" * 70)
    print("fix_missing_files.py — Attaching digital files to 74 listings")
    print("=" * 70)

    # Load listings
    with open(LISTINGS_JSON) as f:
        listings = json.load(f)
    print(f"\nLoaded {len(listings)} listings from {LISTINGS_JSON}\n")

    # Load dp_listing_map
    dp_map = load_dp_listing_map()
    print(f"Loaded dp_listing_map with {len(dp_map)} entries\n")

    # Init API client
    client = EtsyAPIClient()
    client.refresh_access_token()
    print(f"Etsy API client ready. Shop ID: {client.shop_id}\n")

    # Pre-build upscaled hashes (only used for rule 6, lazy)
    upscaled_hashes = None  # deferred

    # Results tracking
    fixed = []
    skipped_physical = []
    missing_zip = []
    unmatched = []

    print("-" * 70)

    for listing in listings:
        lid = int(listing["listing_id"])
        title = listing.get("title", "")
        title_lower = title.lower()

        print(f"\nListing {lid}: {title[:70]}")

        # ── Rule 1: Physical products ──────────────────────────────────────────
        if lid in PHYSICAL_IDS:
            print(f"  → SKIP - physical product")
            skipped_physical.append({"listing_id": lid, "title": title})
            continue

        file_to_upload = None
        match_reason = None

        # ── Rule 2: "Kawaii Art Print No.XXXX" ────────────────────────────────
        m = re.search(r'kawaii art print no\.(\d+)', title_lower)
        if m:
            dp_num = m.group(1)
            zip_path = get_print_zip(dp_num)
            if zip_path:
                file_to_upload = zip_path
                match_reason = f"Rule 2 - Kawaii Art Print No.{dp_num}"
            else:
                print(f"  → MISSING ZIP - DP{dp_num}_print_sizes.zip not found")
                missing_zip.append({"listing_id": lid, "title": title, "reason": f"DP{dp_num}_print_sizes.zip missing"})
                continue

        # ── Rule 3: Sticker pack listings ─────────────────────────────────────
        if file_to_upload is None and ("sticker pack" in title_lower or "sticker" in title_lower):
            zip_path = match_sticker_title(title_lower)
            if zip_path:
                if os.path.exists(zip_path):
                    file_to_upload = zip_path
                    match_reason = f"Rule 3 - Sticker pack"
                else:
                    print(f"  → MISSING ZIP - {zip_path} not on disk")
                    missing_zip.append({"listing_id": lid, "title": title, "reason": f"{os.path.basename(zip_path)} missing"})
                    continue

        # ── Rule 4: SVG bundle listings ────────────────────────────────────────
        if file_to_upload is None and ("svg" in title_lower or "bundle" in title_lower and any(k in title_lower for k in ["good vibes", "mom life", "graduation", "christian", "floral", "western"])):
            zip_path = match_svg_title(title_lower)
            if zip_path:
                file_to_upload = zip_path
                match_reason = f"Rule 4 - SVG bundle"
            else:
                # Check if it looks like an SVG listing that just didn't match
                if "svg" in title_lower:
                    print(f"  → MISSING SVG ZIP - no SVG match found in title")
                    missing_zip.append({"listing_id": lid, "title": title, "reason": "No SVG ZIP matched"})
                    continue

        # ── Rule 5: dp_listing_map.json ────────────────────────────────────────
        if file_to_upload is None and lid in dp_map:
            dp_key = dp_map[lid]
            # Extract number from key like "DP1030"
            dm = re.match(r'DP(\d+)', dp_key)
            if dm:
                dp_num = dm.group(1)
                zip_path = get_print_zip(dp_num)
                if zip_path:
                    file_to_upload = zip_path
                    match_reason = f"Rule 5 - dp_listing_map ({dp_key})"
                else:
                    # Try to generate it? For now log as missing
                    print(f"  → MISSING ZIP - {dp_key}_print_sizes.zip not found (from dp_listing_map)")
                    missing_zip.append({"listing_id": lid, "title": title, "reason": f"DP{dp_num}_print_sizes.zip missing (dp_map)"})
                    continue

        # ── Rule 6: dhash match against upscaled/ ─────────────────────────────
        if file_to_upload is None:
            print(f"  → Attempting dhash match (Rule 6)...")
            if upscaled_hashes is None:
                print(f"    Building upscaled image hashes...")
                upscaled_hashes = build_upscaled_hashes()
                print(f"    Built {len(upscaled_hashes)} hashes from upscaled/")

            img_url = fetch_listing_image_url(client, lid)
            time.sleep(0.5)  # small delay for image fetch

            if img_url:
                tmp_img = f"/tmp/listing_{lid}_photo.jpg"
                if download_image(img_url, tmp_img):
                    listing_hash = dhash(tmp_img)
                    if listing_hash is not None and upscaled_hashes:
                        best_dist = 9999
                        best_file = None
                        for upscaled_path, up_hash in upscaled_hashes:
                            dist = hamming_distance(listing_hash, up_hash)
                            if dist < best_dist:
                                best_dist = dist
                                best_file = upscaled_path

                        print(f"    Best match: {os.path.basename(best_file) if best_file else 'None'} (distance={best_dist})")

                        if best_dist < 50 and best_file:
                            # Extract DP number from filename
                            dm = re.match(r'DP(\d+)', os.path.basename(best_file))
                            if dm:
                                dp_num = dm.group(1)
                                zip_path = get_print_zip(dp_num)
                                if zip_path:
                                    file_to_upload = zip_path
                                    match_reason = f"Rule 6 - dhash match to DP{dp_num} (distance={best_dist})"
                                else:
                                    print(f"  → MISSING ZIP - DP{dp_num}_print_sizes.zip (from dhash match)")
                                    missing_zip.append({"listing_id": lid, "title": title, "reason": f"DP{dp_num} matched by dhash but print zip missing"})
                                    continue
                        else:
                            print(f"  → UNMATCHED - dhash best distance {best_dist} >= 50, needs manual review")
                            unmatched.append({"listing_id": lid, "title": title, "reason": f"dhash best={best_dist}"})
                            continue
                    else:
                        print(f"  → UNMATCHED - could not compute hash for listing image")
                        unmatched.append({"listing_id": lid, "title": title, "reason": "hash computation failed"})
                        continue
                else:
                    print(f"  → UNMATCHED - image download failed")
                    unmatched.append({"listing_id": lid, "title": title, "reason": "image download failed"})
                    continue
            else:
                print(f"  → UNMATCHED - no image URL found for listing")
                unmatched.append({"listing_id": lid, "title": title, "reason": "no image URL"})
                continue

        # ── Upload the file ────────────────────────────────────────────────────
        if file_to_upload:
            if not os.path.exists(file_to_upload):
                print(f"  → MISSING ZIP - file not on disk: {file_to_upload}")
                missing_zip.append({"listing_id": lid, "title": title, "reason": f"File not on disk: {os.path.basename(file_to_upload)}"})
                continue

            file_size_mb = os.path.getsize(file_to_upload) / (1024 * 1024)
            print(f"  → UPLOADING ({match_reason})")
            print(f"     File: {os.path.basename(file_to_upload)} ({file_size_mb:.1f} MB)")

            try:
                result = client.upload_listing_file(lid, file_to_upload)
                file_id = result.get("listing_file_id") or result.get("file_id") or "?"
                print(f"  ✓ FIXED - file_id={file_id}")
                fixed.append({
                    "listing_id": lid,
                    "title": title,
                    "file": os.path.basename(file_to_upload),
                    "match_reason": match_reason,
                    "file_id": file_id,
                })
            except Exception as e:
                print(f"  ✗ UPLOAD FAILED - {e}")
                missing_zip.append({
                    "listing_id": lid,
                    "title": title,
                    "reason": f"Upload failed: {e}",
                })

            time.sleep(2)  # rate limit: 2s between uploads

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  FIXED:             {len(fixed)}")
    print(f"  SKIPPED (physical): {len(skipped_physical)}")
    print(f"  MISSING ZIP:       {len(missing_zip)}")
    print(f"  UNMATCHED:         {len(unmatched)}")
    print(f"  TOTAL:             {len(fixed) + len(skipped_physical) + len(missing_zip) + len(unmatched)}")
    print()

    if missing_zip:
        print("MISSING / FAILED:")
        for item in missing_zip:
            print(f"  [{item['listing_id']}] {item['title'][:60]} — {item['reason']}")

    if unmatched:
        print("\nUNMATCHED (manual review needed):")
        for item in unmatched:
            print(f"  [{item['listing_id']}] {item['title'][:60]} — {item['reason']}")

    # ── Write results JSON ─────────────────────────────────────────────────────
    results = {
        "fixed": fixed,
        "skipped_physical": skipped_physical,
        "missing_zip": missing_zip,
        "unmatched": unmatched,
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
