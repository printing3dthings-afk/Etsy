#!/usr/bin/env python3
"""Add manifest coverage for listings that exist in product_catalog.json
but are absent from data/listing_manifest.json (and therefore invisible
to listing_integrity_check.py).

build_manifest.py only derives entries from data/dp_listing_map.json,
which only ever tracked DP-coded wall art / planner / SVG products.
Whole product lines added later — 3D-printed physical products, digital
paper packs, coloring pages — were never added to that map, so 43 live
listings had zero integrity-check coverage (found 2026-06-17 while
investigating the Four Seasons truthfulness bug).

For each catalog entry whose etsy_listing_id isn't already a manifest
key, this fetches the listing's *live* file list and photo count from
Etsy and writes them in as expected_files / expected_file_count /
min_photo_count -- a baseline capture, same approach build_manifest.py's
--baseline flag uses, since these categories have no derivable local
filename convention to predict expected files from.

Re-runnable: skips any listing_id already present in the manifest, so it
only ever adds new coverage, never overwrites entries build_manifest.py
or a previous run of this script already populated.

Usage:
    python tools/extend_manifest_from_catalog.py
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "tools"))
from etsy_api import get_client

CATALOG_PATH = BASE_DIR / "data" / "product_catalog.json"
MANIFEST_PATH = BASE_DIR / "data" / "listing_manifest.json"

# catalog `category` -> manifest/rules `type`. Reuses existing rule sets
# where the shape matches (wall_art_bundle behaves like a gallery_bundle;
# svg_3dprint_pack behaves like a generic svg_bundle); 3d_print_physical,
# paper_pack, coloring_pages got their own new rule entries in
# data/listing_rules.json since nothing existing fit.
CATEGORY_TYPE_MAP = {
    "3d_print_physical": "3d_print_physical",
    "paper_pack": "paper_pack",
    "coloring_pages": "coloring_pages",
    "svg_3dprint_pack": "svg_bundle",
    "wall_art": "wall_art",
    "wall_art_bundle": "gallery_bundle",
}

MIN_PHOTO_FLOOR = {
    "3d_print_physical": 8,
    "paper_pack": 5,
    "coloring_pages": 5,
    "svg_bundle": 3,
    "wall_art": 8,
    "gallery_bundle": 5,
}


def main():
    catalog = json.loads(CATALOG_PATH.read_text())
    manifest = json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else {}

    candidates = [
        p for p in catalog
        if p.get("etsy_listing_id")
        and str(p["etsy_listing_id"]) not in manifest
        and p.get("category") in CATEGORY_TYPE_MAP
    ]

    if not candidates:
        print("No uncovered catalog listings found — manifest already complete for known categories.")
        return

    print(f"Found {len(candidates)} catalog listings with no manifest entry. Capturing live baseline …")
    client = get_client()
    added, errors = [], []

    for p in candidates:
        lid = str(p["etsy_listing_id"])
        product_type = CATEGORY_TYPE_MAP[p["category"]]
        try:
            files = client.get_listing_files(lid)
            file_names = sorted(f.get("filename", "") for f in files)
            images = client._request("GET", f"listings/{lid}/images").get("results", [])
            photo_count = len(images)
        except Exception as e:
            errors.append((p["product_id"], lid, str(e)))
            continue

        manifest[lid] = {
            "dp_codes": [p["product_id"]],
            "type": product_type,
            "expected_files": file_names,
            "expected_file_count": len(file_names),
            # NOTE: the actual photo-count gate read by listing_integrity_check.py
            # comes from data/listing_rules.json's per-type "min_photos", not this
            # field -- this is kept only for parity with build_manifest.py's output.
            "min_photo_count": MIN_PHOTO_FLOOR.get(product_type, 3),
            "art_hashes": {},
            "art_sources": {},
            "listing_roles": {p["product_id"]: "listing_id"},
            "last_verified": None,
            "last_status": None,
            "baseline_captured": datetime.now(timezone.utc).isoformat(),
            "baseline_source": "extend_manifest_from_catalog.py",
        }
        added.append((p["product_id"], p["category"], lid, len(file_names), photo_count))
        time.sleep(0.15)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(f"\nAdded {len(added)} new manifest entries:")
    for pid, cat, lid, fc, pc in added:
        print(f"  + {pid:42s} [{cat:20s}] listing {lid}  files={fc} photos={pc}")
    if errors:
        print(f"\n{len(errors)} listing(s) could not be fetched (left uncovered, retry later):")
        for pid, lid, err in errors:
            print(f"  ! {pid} ({lid}): {err}")
    print(f"\nManifest now has {len(manifest)} total listings (was {len(manifest) - len(added)}).")


if __name__ == "__main__":
    main()
