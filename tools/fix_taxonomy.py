#!/usr/bin/env python3
"""
fix_taxonomy.py — Audit and fix taxonomy (seller_taxonomy_id) for all active listings.

Correct taxonomy IDs:
  2078  Art & Collectibles > Prints > Digital Prints    ← digital wall art
  354   Paper & Party Supplies > Paper > Calendars & Planners
  1326  Paper & Party Supplies > Stickers
  12394 Craft Supplies > Patterns > Cutting Machine Files (SVGs)

Wrong IDs found in shop:
  1027  Home & Living > Home Decor > Wall Decor  (physical — wrong for digital prints)
  2097  Art & Collectibles > Dolls & Miniatures > Art Dolls  (completely wrong)

Usage:
    python tools/fix_taxonomy.py --dry-run   # preview without changes
    python tools/fix_taxonomy.py             # apply fixes
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from tools.etsy_api import EtsyAPIClient  # noqa: E402

SHOP_ID = 65012858

# Target taxonomy IDs
TAX_DIGITAL_PRINTS  = 2078   # Art & Collectibles > Prints > Digital Prints
TAX_PLANNERS        = 354    # Paper & Party Supplies > Paper > Calendars & Planners
TAX_STICKERS        = 1326   # Paper & Party Supplies > Stickers
TAX_SVG_CUT_FILES   = 12394  # Craft Supplies > Patterns > Cutting Machine Files

# Wrong taxonomy IDs to fix
WRONG_PHYSICAL_WALL_ART = 1027   # Home & Living > Home Decor > Wall Decor
WRONG_ART_DOLLS         = 2097   # Art & Collectibles > Dolls & Miniatures


def _classify(title: str) -> tuple[int, str] | None:
    """
    Return (correct_taxonomy_id, product_type_label) for a listing title,
    or None if the listing type cannot be determined.
    """
    t = title.lower()

    # SVG cut files — check first (some SVGs also say "printable")
    if re.search(r"\bsvg\b|\bcut file\b|\bcricut\b|\bsilhouette\b", t):
        return TAX_SVG_CUT_FILES, "SVG Cut File"

    # Digital planners
    if re.search(r"\bplanner\b|\bplanning\b", t) and re.search(r"\bdigital\b|\bgoodnotes\b|\bnotability\b|\bipad\b|\bpdf\b", t):
        return TAX_PLANNERS, "Digital Planner"

    # Sticker packs
    if re.search(r"\bsticker\b", t) and re.search(r"\bpack\b|\bsheet\b|\bkit\b|\bset\b|\bdigital\b|\bpng\b|\bprintable\b", t):
        return TAX_STICKERS, "Sticker Pack"

    # Digital / printable wall art — anything else digital
    if re.search(r"\bprintable\b|\binstant download\b|\bdigital\b|\bwall art\b|\bprint\b|\bposter\b", t):
        return TAX_DIGITAL_PRINTS, "Digital Wall Art"

    return None


def run(dry_run: bool) -> None:
    c = EtsyAPIClient()

    # Pull all active listings (paginate)
    print("Fetching active listings...")
    all_listings: list[dict] = []
    offset = 0
    while True:
        r = c._request(
            "GET",
            f"shops/{SHOP_ID}/listings",
            params={"state": "active", "limit": 100, "offset": offset},
        )
        batch = r.get("results", [])
        all_listings.extend(batch)
        if len(batch) < 100:
            break
        offset += 100

    print(f"  {len(all_listings)} active listings\n")

    # Tally current taxonomy distribution
    tax_counts: dict[int, int] = {}
    for l in all_listings:
        tid = l.get("taxonomy_id") or l.get("seller_taxonomy_id") or 0
        tax_counts[tid] = tax_counts.get(tid, 0) + 1

    print("Current taxonomy distribution:")
    tax_labels = {
        2078: "Digital Prints (correct for digital art)",
        354:  "Calendars & Planners (correct for planners)",
        1326: "Stickers (correct for sticker packs)",
        12394: "Cutting Machine Files (correct for SVGs)",
        1027: "⚠ WRONG: Wall Decor (physical home decor)",
        2097: "⚠ WRONG: Art Dolls",
        0:    "No taxonomy set",
    }
    for tid, cnt in sorted(tax_counts.items(), key=lambda x: -x[1]):
        label = tax_labels.get(tid, f"taxonomy_id={tid}")
        print(f"  {tid:>6}  {cnt:>4} listings  {label}")
    print()

    # Identify listings that need fixing
    fixes: list[tuple[dict, int, str, str]] = []  # (listing, old_tax, new_tax_label, product_type)

    for l in all_listings:
        lid   = l["listing_id"]
        title = l["title"]
        tid   = l.get("taxonomy_id") or l.get("seller_taxonomy_id") or 0

        classified = _classify(title)
        if classified is None:
            continue
        correct_tid, ptype = classified

        if tid == correct_tid:
            continue  # already correct

        fixes.append((l, tid, correct_tid, ptype))

    if not fixes:
        print("All listings are in the correct taxonomy category. Nothing to fix.")
        return

    # Group fixes by direction for reporting
    print(f"{'=' * 65}")
    print(f"{'DRY RUN: ' if dry_run else ''}TAXONOMY FIXES NEEDED: {len(fixes)}")
    print(f"{'=' * 65}\n")

    by_change: dict[tuple[int, int], list] = {}
    for listing, old, new, ptype in fixes:
        key = (old, new)
        by_change.setdefault(key, []).append((listing, ptype))

    for (old, new), items in sorted(by_change.items()):
        old_lbl = tax_labels.get(old, f"tax={old}")
        new_lbl = tax_labels.get(new, f"tax={new}")
        print(f"  {old_lbl}  →  {new_lbl}  ({len(items)} listings)")
        for listing, ptype in items[:5]:
            print(f"    {listing['listing_id']}  [{ptype}]  {listing['title'][:60]}")
        if len(items) > 5:
            print(f"    ... and {len(items) - 5} more")
        print()

    if dry_run:
        print("[DRY RUN] No changes made.")
        return

    # Apply fixes
    results = {"fixed": [], "errors": []}

    print("Applying taxonomy fixes...")
    for listing, old_tid, new_tid, ptype in fixes:
        lid   = listing["listing_id"]
        title = listing["title"]
        try:
            c.update_listing(lid, {"taxonomy_id": new_tid})
            time.sleep(0.35)
            results["fixed"].append({"id": lid, "title": title[:65], "old": old_tid, "new": new_tid})
            print(f"  ✓  {lid}  {old_tid} → {new_tid}  {title[:55]}")
        except Exception as exc:
            results["errors"].append({"id": lid, "error": str(exc)})
            print(f"  ERROR {lid}: {exc}")

    # Summary
    print(f"\n{'=' * 65}")
    print("SUMMARY")
    print(f"{'=' * 65}")
    print(f"  Fixed:   {len(results['fixed'])}")
    print(f"  Errors:  {len(results['errors'])}")

    if results["errors"]:
        print("\nErrors:")
        for e in results["errors"]:
            print(f"  {e['id']}: {e['error']}")

    # Save report
    report_path = ROOT / "data" / "reports" / "taxonomy_fix_report_2026-06-10.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull report → {report_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="Preview fixes without making API calls")
    args = ap.parse_args()
    run(dry_run=args.dry_run)
