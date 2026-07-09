#!/usr/bin/env python3
"""
Upload sticker pack images + digital files to draft Etsy listings, then activate them.
"""
import sys
import os
import time

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, os.path.dirname(__file__))
from etsy_api import EtsyAPIClient, EtsyAPIError

FILES_DIR = "/home/user/Etsy/data/digital_products/product_files"

# ── Listing definitions ───────────────────────────────────────────────────────

LISTINGS = [
    {
        "name": "Free Sticker Sheet (DP1026 sample)",
        "listing_id": 4512255508,
        "images": [
            f"{FILES_DIR}/DP1026_sticker_sheet_1.jpg",
        ],
        "files": [
            f"{FILES_DIR}/DP1026_sticker_pack.zip",  # sample — sheet 1 only per instructions
        ],
    },
    {
        "name": "Lavender Dreams Sticker Pack (DP1026)",
        "listing_id": 4512255514,
        "images": [
            f"{FILES_DIR}/DP1026_sticker_sheet_1.jpg",
            f"{FILES_DIR}/DP1026_sticker_sheet_2.jpg",
            f"{FILES_DIR}/DP1026_sticker_sheet_3.jpg",
            f"{FILES_DIR}/DP1026_sticker_sheet_4.jpg",
            f"{FILES_DIR}/DP1026_sticker_sheet_5.jpg",
        ],
        "files": [
            f"{FILES_DIR}/DP1026_sticker_pack.zip",
        ],
    },
    {
        "name": "Cotton Candy Sticker Pack (DP1027)",
        "listing_id": 4512254015,
        "images": [
            f"{FILES_DIR}/DP1027_sticker_sheet_1.jpg",
            f"{FILES_DIR}/DP1027_sticker_sheet_2.jpg",
            f"{FILES_DIR}/DP1027_sticker_sheet_3.jpg",
            f"{FILES_DIR}/DP1027_sticker_sheet_4.jpg",
            f"{FILES_DIR}/DP1027_sticker_sheet_5.jpg",
        ],
        "files": [
            f"{FILES_DIR}/DP1027_sticker_pack.zip",
        ],
    },
    {
        "name": "Midnight Blue Sticker Pack (DP1028)",
        "listing_id": 4512255536,
        "images": [
            f"{FILES_DIR}/DP1028_sticker_sheet_1.jpg",
            f"{FILES_DIR}/DP1028_sticker_sheet_2.jpg",
            f"{FILES_DIR}/DP1028_sticker_sheet_3.jpg",
            f"{FILES_DIR}/DP1028_sticker_sheet_4.jpg",
            f"{FILES_DIR}/DP1028_sticker_sheet_5.jpg",
        ],
        "files": [
            f"{FILES_DIR}/DP1028_sticker_pack.zip",
        ],
    },
    {
        "name": "Coral Peach Sticker Pack (DP1029)",
        "listing_id": 4512254027,
        "images": [
            f"{FILES_DIR}/DP1029_sticker_sheet_1.jpg",
            f"{FILES_DIR}/DP1029_sticker_sheet_2.jpg",
            f"{FILES_DIR}/DP1029_sticker_sheet_3.jpg",
            f"{FILES_DIR}/DP1029_sticker_sheet_4.jpg",
            f"{FILES_DIR}/DP1029_sticker_sheet_5.jpg",
        ],
        "files": [
            f"{FILES_DIR}/DP1029_sticker_pack.zip",
        ],
    },
    {
        "name": "All 4 Sticker Packs Bundle",
        "listing_id": 4512254035,
        # 2 sheets from each pack = 8 images, upload sheets 1+2 from each
        "images": [
            f"{FILES_DIR}/DP1026_sticker_sheet_1.jpg",
            f"{FILES_DIR}/DP1026_sticker_sheet_2.jpg",
            f"{FILES_DIR}/DP1027_sticker_sheet_1.jpg",
            f"{FILES_DIR}/DP1027_sticker_sheet_2.jpg",
            f"{FILES_DIR}/DP1028_sticker_sheet_1.jpg",
            f"{FILES_DIR}/DP1028_sticker_sheet_2.jpg",
            f"{FILES_DIR}/DP1029_sticker_sheet_1.jpg",
            f"{FILES_DIR}/DP1029_sticker_sheet_2.jpg",
        ],
        "files": [
            f"{FILES_DIR}/DP1026_sticker_pack.zip",
            f"{FILES_DIR}/DP1027_sticker_pack.zip",
            f"{FILES_DIR}/DP1028_sticker_pack.zip",
            f"{FILES_DIR}/DP1029_sticker_pack.zip",
        ],
    },
]


def process_listing(api, listing):
    lid = listing["listing_id"]
    name = listing["name"]
    print(f"\n{'='*60}")
    print(f"Processing: {name}  (ID: {lid})")
    print(f"{'='*60}")

    images_ok = 0
    images_fail = 0
    files_ok = 0
    files_fail = 0

    # ── Step 1: Upload images ─────────────────────────────────────────────────
    print(f"\n  [IMAGES] Uploading {len(listing['images'])} image(s)...")
    for rank, img_path in enumerate(listing["images"], start=1):
        fname = os.path.basename(img_path)
        try:
            result = api.upload_listing_image(lid, img_path, rank=rank)
            img_id = result.get("listing_image_id", "?")
            print(f"    rank={rank} {fname} -> OK (image_id={img_id})")
            images_ok += 1
        except EtsyAPIError as e:
            print(f"    rank={rank} {fname} -> FAILED: {e}")
            images_fail += 1
        except FileNotFoundError:
            print(f"    rank={rank} {fname} -> FAILED: file not found at {img_path}")
            images_fail += 1
        # Small delay to respect rate limits
        time.sleep(0.5)

    # ── Step 2: Upload digital files ──────────────────────────────────────────
    print(f"\n  [FILES] Uploading {len(listing['files'])} digital file(s)...")
    for rank, file_path in enumerate(listing["files"], start=1):
        fname = os.path.basename(file_path)
        size_mb = os.path.getsize(file_path) / 1024 / 1024 if os.path.exists(file_path) else 0
        print(f"    rank={rank} {fname} ({size_mb:.1f} MB) uploading...", end="", flush=True)
        try:
            result = api.upload_listing_file(lid, file_path, rank=rank)
            file_id = result.get("listing_file_id", "?")
            print(f" OK (file_id={file_id})")
            files_ok += 1
        except EtsyAPIError as e:
            print(f" FAILED: {e}")
            files_fail += 1
        except FileNotFoundError:
            print(f" FAILED: file not found at {file_path}")
            files_fail += 1
        time.sleep(1)

    # ── Step 3: Activate listing ──────────────────────────────────────────────
    print(f"\n  [ACTIVATE] Setting state to active...")
    try:
        result = api.update_listing(lid, {"state": "active"})
        state = result.get("state", "?")
        print(f"    -> State now: {state}")
        activated = True
    except EtsyAPIError as e:
        print(f"    -> FAILED to activate: {e}")
        activated = False

    return {
        "name": name,
        "listing_id": lid,
        "images_ok": images_ok,
        "images_fail": images_fail,
        "files_ok": files_ok,
        "files_fail": files_fail,
        "activated": activated,
    }


def main():
    api = EtsyAPIClient()
    print(f"Using shop_id: {api.shop_id}")
    print(f"Access token present: {'yes' if api.access_token else 'NO'}")

    results = []
    for listing in LISTINGS:
        r = process_listing(api, listing)
        results.append(r)

    # ── Final summary ─────────────────────────────────────────────────────────
    print(f"\n\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status = "ACTIVATED" if r["activated"] else "NOT ACTIVATED"
        img_status = f"images {r['images_ok']}/{r['images_ok']+r['images_fail']} OK"
        file_status = f"files {r['files_ok']}/{r['files_ok']+r['files_fail']} OK"
        print(f"  [{status}] {r['name']} (ID: {r['listing_id']}) | {img_status} | {file_status}")

    activated_count = sum(1 for r in results if r["activated"])
    print(f"\nActivated {activated_count}/{len(results)} listings.")


if __name__ == "__main__":
    main()
