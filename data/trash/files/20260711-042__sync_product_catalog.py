#!/usr/bin/env python3
"""Backfill data/product_catalog.json from live Etsy listings.

CLAUDE.md requires product_catalog.json to be the source of truth for every
product (product_id, etsy_listing_id, price, file_paths, status,
last_updated) and automation scripts to read from it rather than hardcoding
listing IDs. This script closes drift between that file and what is
actually live on Etsy:

  - Any active/draft listing not yet tracked (matched by etsy_listing_id) is
    appended as a new entry, with category inferred from the title and a
    product_id generated from the title slug (collision-safe).
  - Any tracked entry whose price has drifted from Etsy is corrected and
    reported (does not touch hand-curated fields like product_id or files).
  - Existing hand-maintained entries (e.g. unlisted DP1030-1033 placeholders
    with no etsy_listing_id) are left untouched since nothing on Etsy can
    match them.

Read-only against Etsy (only GET calls) — safe to run anytime. Writes only
to data/product_catalog.json.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from etsy_api import get_client

CATALOG_PATH = Path(__file__).parent.parent / "data" / "product_catalog.json"

# (pattern, category, product_id prefix) — first match wins.
CATEGORY_RULES = [
    (re.compile(r"3D Printed", re.I), "3d_print_physical", "P3D"),
    (re.compile(r"Commercial License", re.I), "svg_bundle_license", "LICENSE_SYNC"),
    (re.compile(r"Digital Paper Pack", re.I), "paper_pack", "PAPER"),
    (re.compile(r"Coloring Pages?|Coloring Book", re.I), "coloring_pages", "COLOR"),
    (re.compile(r"SVG.*3D Print Signs|3D Print Signs", re.I), "svg_3dprint_pack", "SS"),
    (re.compile(r"Sublimation", re.I), "sublimation", "SUBLIM_SYNC"),
    (re.compile(r"\bSVG\b", re.I), "svg_bundle", "SVG_SYNC"),
    (re.compile(r"Sticker", re.I), "sticker_pack", "STICKER_SYNC"),
    (re.compile(r"Planner", re.I), "digital_planner", "DP_SYNC"),
    (re.compile(r"Wall Art|Printable|Nursery|Gallery Wall", re.I), "wall_art", "WA"),
]
DEFAULT_CATEGORY, DEFAULT_PREFIX = "uncategorized", "MISC"


def infer_category(title: str):
    for pattern, category, prefix in CATEGORY_RULES:
        if pattern.search(title):
            return category, prefix
    return DEFAULT_CATEGORY, DEFAULT_PREFIX


def slugify(title: str, max_words: int = 5) -> str:
    head = re.split(r"[,|]", title)[0]
    words = re.findall(r"[A-Za-z0-9]+", head)[:max_words]
    return "_".join(w.upper() for w in words) or "ITEM"


def main():
    catalog = json.loads(CATALOG_PATH.read_text())
    known_ids = {str(p["etsy_listing_id"]) for p in catalog if p.get("etsy_listing_id")}
    used_product_ids = {p["product_id"] for p in catalog}
    today = date.today().isoformat()

    client = get_client()
    listings = client.get_shop_listings_all(state="active") + client.get_shop_listings_all(state="draft")

    added, drift = [], []

    for listing in listings:
        lid = str(listing["listing_id"])
        price = round(listing["price"]["amount"] / listing["price"]["divisor"], 2)
        title = listing["title"]
        state = listing["state"]

        if lid in known_ids:
            entry = next(p for p in catalog if str(p.get("etsy_listing_id")) == lid)
            changed = False
            if entry.get("price") != price:
                drift.append((entry["product_id"], entry.get("price"), price))
                entry["price"] = price
                changed = True
            if entry.get("status") in ("active", "draft") and entry["status"] != state:
                entry["status"] = state
                changed = True
            if changed:
                entry["last_updated"] = today
            continue

        category, prefix = infer_category(title)
        base_id = f"{prefix}_{slugify(title)}"
        product_id, n = base_id, 1
        while product_id in used_product_ids:
            n += 1
            product_id = f"{base_id}_{n}"
        used_product_ids.add(product_id)

        try:
            files = [f["filename"] for f in client.get_listing_files(listing["listing_id"])]
        except Exception:
            files = []

        catalog.append({
            "product_id": product_id,
            "name": title,
            "etsy_listing_id": lid,
            "price": price,
            "category": category,
            "status": state,
            "files": files,
            "last_updated": today,
            "source": "etsy_sync",
        })
        added.append((product_id, category, lid))

    CATALOG_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")

    print(f"Catalog entries before: {len(known_ids)} tracked / {len(json.loads(CATALOG_PATH.read_text())) - len(added)} total rows")
    print(f"Live Etsy listings checked: {len(listings)}")
    print(f"New entries added: {len(added)}")
    for pid, cat, lid in added:
        print(f"  + {pid:45s} [{cat:20s}] listing {lid}")
    print(f"Price drift corrected: {len(drift)}")
    for pid, old, new in drift:
        print(f"  ~ {pid}: {old} -> {new}")
    print(f"Catalog entries after: {len(catalog)}")


if __name__ == "__main__":
    main()
