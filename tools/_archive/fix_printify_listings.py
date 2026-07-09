#!/usr/bin/env python3
"""
fix_printify_listings.py

Fixes all 54 Printify-published Etsy listings:
  - Rewrites titles to SEO formula (≤70 chars)
  - Adds all 13 tags (currently zero on every listing)
  - Adds AI disclosure to description

Usage:
  python tools/fix_printify_listings.py --dry-run   # preview changes
  python tools/fix_printify_listings.py --fix        # apply to Etsy
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE))

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

AI_DISCLOSURE = (
    "\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "🤖 ABOUT THIS DESIGN\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "This design was created using AI image generation tools, with original "
    "prompts, curation, and finishing by the seller. "
    "All designs are reviewed for quality before printing.\n\n"
    "© OnBrandCraftz. Personal use only. Not for resale or redistribution."
)

# SEO title formula: [Subject + Style] | Kawaii Wall Art | [Room] | Multiple Sizes
# Max 70 chars. Physical print — no "Instant Download", no "Printable"
LISTING_DATA: dict[str, dict] = {
    "Boho Botanical Floral": {
        "title": "Boho Botanical Floral Wall Art Print | Multiple Sizes",
        "tags": ["boho wall art", "botanical print", "floral wall art", "bedroom wall art",
                 "living room art", "boho home decor", "gallery wall art", "housewarming gift",
                 "gift for her", "nature lover gift", "art print poster", "kawaii wall art",
                 "floral art print"],
    },
    "Minimalist Line Art": {
        "title": "Minimalist Line Art Print | Modern Wall Decor | Multiple Sizes",
        "tags": ["minimalist wall art", "line art print", "modern wall decor", "bedroom wall art",
                 "living room art", "office wall art", "gallery wall art", "housewarming gift",
                 "gift for her", "abstract art print", "art print poster", "minimal home decor",
                 "black white art"],
    },
    "Abstract Watercolor": {
        "title": "Abstract Watercolor Art Print | Boho Wall Decor | Multiple Sizes",
        "tags": ["watercolor print", "abstract wall art", "boho wall art", "bedroom wall art",
                 "living room art", "colorful wall art", "gallery wall art", "housewarming gift",
                 "gift for her", "watercolor poster", "art print poster", "kawaii wall art",
                 "abstract art print"],
    },
    "Cottagecore Botanical": {
        "title": "Cottagecore Botanical Art Print | Nature Wall Decor | Multiple Sizes",
        "tags": ["cottagecore wall art", "botanical print", "nature wall art", "bedroom wall art",
                 "living room art", "cottage home decor", "gallery wall art", "housewarming gift",
                 "gift for her", "nature lover gift", "art print poster", "botanical poster",
                 "floral wall decor"],
    },
    "Kawaii Celestial": {
        "title": "Kawaii Celestial Art Print | Moon Stars Wall Decor | Multiple Sizes",
        "tags": ["celestial wall art", "kawaii wall art", "moon wall art", "bedroom wall art",
                 "living room art", "astrology art", "gallery wall art", "housewarming gift",
                 "gift for her", "moon lover gift", "art print poster", "stars wall decor",
                 "kawaii art print"],
    },
    "Pastel Abstract": {
        "title": "Pastel Abstract Art Print | Kawaii Wall Decor | Multiple Sizes",
        "tags": ["pastel wall art", "abstract wall art", "kawaii wall art", "bedroom wall art",
                 "living room art", "pastel home decor", "gallery wall art", "housewarming gift",
                 "gift for her", "pastel art print", "art print poster", "colorful wall art",
                 "kawaii art print"],
    },
    "Modern Geometric": {
        "title": "Modern Geometric Art Print | Minimal Wall Decor | Multiple Sizes",
        "tags": ["geometric wall art", "modern wall art", "minimalist wall art", "bedroom wall art",
                 "living room art", "office wall art", "gallery wall art", "housewarming gift",
                 "gift for her", "geometric poster", "art print poster", "modern home decor",
                 "abstract art print"],
    },
    "Watercolor Floral": {
        "title": "Watercolor Floral Art Print | Boho Wall Decor | Multiple Sizes",
        "tags": ["watercolor floral", "floral wall art", "watercolor print", "bedroom wall art",
                 "living room art", "boho wall art", "gallery wall art", "housewarming gift",
                 "gift for her", "floral poster", "art print poster", "botanical print",
                 "kawaii wall art"],
    },
    "Boho Mandala": {
        "title": "Boho Mandala Art Print | Spiritual Wall Decor | Multiple Sizes",
        "tags": ["mandala wall art", "boho wall art", "spiritual wall art", "bedroom wall art",
                 "living room art", "meditation decor", "gallery wall art", "housewarming gift",
                 "gift for her", "mandala poster", "art print poster", "boho home decor",
                 "kawaii art print"],
    },
    "Kawaii Character": {
        "title": "Kawaii Character Art Print | Cute Wall Decor | Multiple Sizes",
        "tags": ["kawaii wall art", "cute wall art", "kawaii art print", "bedroom wall art",
                 "kids room decor", "kawaii home decor", "gallery wall art", "gift for her",
                 "anime wall art", "kawaii poster", "art print poster", "cute anime art",
                 "kawaii character"],
    },
    "Tropical Botanical": {
        "title": "Tropical Botanical Art Print | Jungle Wall Decor | Multiple Sizes",
        "tags": ["tropical wall art", "botanical print", "jungle wall art", "bedroom wall art",
                 "living room art", "tropical home decor", "gallery wall art", "housewarming gift",
                 "gift for her", "nature lover gift", "art print poster", "tropical poster",
                 "botanical wall art"],
    },
    "Minimalist Typography": {
        "title": "Minimalist Typography Art Print | Quote Wall Decor | Multiple Sizes",
        "tags": ["typography wall art", "quote wall art", "minimalist wall art", "bedroom wall art",
                 "living room art", "office wall art", "gallery wall art", "housewarming gift",
                 "gift for her", "inspirational art", "art print poster", "quote poster",
                 "word art print"],
    },
    "Abstract Landscape": {
        "title": "Abstract Landscape Art Print | Nature Wall Decor | Multiple Sizes",
        "tags": ["landscape wall art", "abstract wall art", "nature wall art", "bedroom wall art",
                 "living room art", "scenic wall art", "gallery wall art", "housewarming gift",
                 "gift for her", "nature lover gift", "art print poster", "landscape poster",
                 "abstract art print"],
    },
    "Floral Wreath": {
        "title": "Floral Wreath Art Print | Botanical Wall Decor | Multiple Sizes",
        "tags": ["floral wreath print", "botanical print", "floral wall art", "bedroom wall art",
                 "living room art", "cottage home decor", "gallery wall art", "housewarming gift",
                 "gift for her", "wreath wall art", "art print poster", "kawaii wall art",
                 "floral art print"],
    },
    "Kawaii Stationery": {
        "title": "Kawaii Stationery Art Print | Cute Desk Decor | Multiple Sizes",
        "tags": ["kawaii wall art", "stationery art", "cute wall art", "bedroom wall art",
                 "office wall art", "desk decor print", "gallery wall art", "gift for her",
                 "kawaii art print", "stationery poster", "art print poster", "cute office art",
                 "kawaii character"],
    },
    "Pastel Celestial": {
        "title": "Pastel Celestial Art Print | Moon Stars Decor | Multiple Sizes",
        "tags": ["pastel wall art", "celestial wall art", "moon wall art", "bedroom wall art",
                 "living room art", "astrology art", "gallery wall art", "housewarming gift",
                 "gift for her", "pastel art print", "art print poster", "kawaii wall art",
                 "stars wall decor"],
    },
    "Wildflower Meadow": {
        "title": "Wildflower Meadow Art Print | Botanical Wall Decor | Multiple Sizes",
        "tags": ["wildflower wall art", "botanical print", "floral wall art", "bedroom wall art",
                 "living room art", "cottagecore art", "gallery wall art", "housewarming gift",
                 "gift for her", "nature lover gift", "art print poster", "meadow poster",
                 "wildflower print"],
    },
    "Celestial Moon": {
        "title": "Celestial Moon Art Print | Moon Phase Wall Decor | Multiple Sizes",
        "tags": ["moon phase wall art", "celestial wall art", "moon wall art", "bedroom wall art",
                 "living room art", "astrology art", "gallery wall art", "housewarming gift",
                 "gift for her", "moon lover gift", "art print poster", "stars wall decor",
                 "kawaii wall art"],
    },
    "Vintage Botanical": {
        "title": "Vintage Botanical Art Print | Antique Floral Decor | Multiple Sizes",
        "tags": ["vintage botanical", "botanical print", "vintage wall art", "bedroom wall art",
                 "living room art", "antique home decor", "gallery wall art", "housewarming gift",
                 "gift for her", "nature lover gift", "art print poster", "botanical poster",
                 "vintage art print"],
    },
    "Botanical Herbs": {
        "title": "Botanical Herbs Art Print | Kitchen Wall Decor | Multiple Sizes",
        "tags": ["botanical print", "herb wall art", "kitchen wall art", "bedroom wall art",
                 "dining room art", "cottage home decor", "gallery wall art", "housewarming gift",
                 "gift for her", "nature lover gift", "art print poster", "herb garden art",
                 "botanical wall art"],
    },
    "Kawaii Animals": {
        "title": "Kawaii Animals Art Print | Cute Animal Wall Decor | Multiple Sizes",
        "tags": ["kawaii wall art", "animal wall art", "cute wall art", "bedroom wall art",
                 "kids room decor", "kawaii home decor", "gallery wall art", "gift for her",
                 "animal lover gift", "kawaii art print", "art print poster", "cute animal art",
                 "kawaii character"],
    },
    "Boho Dreamcatcher": {
        "title": "Boho Dreamcatcher Art Print | Spiritual Wall Decor | Multiple Sizes",
        "tags": ["dreamcatcher art", "boho wall art", "spiritual wall art", "bedroom wall art",
                 "living room art", "boho home decor", "gallery wall art", "housewarming gift",
                 "gift for her", "boho art print", "art print poster", "native art print",
                 "dreamcatcher print"],
    },
}

# Default tags for unnamed / generic Kawaii Art Print Design XXXX listings
DEFAULT_TAGS = [
    "kawaii wall art", "art print poster", "kawaii art print", "bedroom wall art",
    "living room art", "kawaii home decor", "gallery wall art", "housewarming gift",
    "gift for her", "kawaii poster", "cute wall art", "kawaii character",
    "boho wall art",
]


def _match_listing(title: str) -> dict:
    """Match an Etsy listing title to its SEO data."""
    # Strip "Art Print" suffix for matching
    clean = title.replace(" Art Print", "").replace(" Art Print ", " ").strip()
    for key, data in LISTING_DATA.items():
        if key.lower() in clean.lower():
            return data
    return {}


def _build_generic_title(title: str) -> str:
    """Build a ≤70 char title for generic listings."""
    # "Kawaii Art Print Design 1030" → "Kawaii Wall Art Print Design No.30 | Home Decor"
    num = title.replace("Kawaii Art Print Design ", "").strip()
    t = f"Kawaii Art Print No.{num} | Kawaii Wall Decor | Multiple Sizes"
    if len(t) > 70:
        t = f"Kawaii Wall Art Print No.{num} | Multiple Sizes"
    return t


def _needs_ai_disclosure(desc: str) -> bool:
    return "AI image generation" not in desc and "🤖" not in desc


def get_printify_listings(client: EtsyAPIClient) -> list[dict]:
    listings = client.get_shop_listings_all(state="active", limit=100)
    return [l for l in listings
            if "Art Print" in l.get("title", "") or "Physical Print" in l.get("title", "")]


def preview_changes(listings: list[dict]) -> None:
    print(f"\nPreview: {len(listings)} Printify listings to fix\n")
    print(f"{'Listing ID':<15} {'Old Title':<45} {'New Title':<55} {'Tags'}")
    print("-" * 130)
    for l in listings:
        old_title = l["title"]
        data = _match_listing(old_title)
        if data:
            new_title = data["title"]
            tags = len(data["tags"])
        elif "Kawaii Art Print Design" in old_title:
            new_title = _build_generic_title(old_title)
            tags = len(DEFAULT_TAGS)
        else:
            new_title = old_title
            tags = len(DEFAULT_TAGS)
        flag = "⚠" if len(new_title) > 70 else "✓"
        print(f"{l['listing_id']:<15} {old_title[:44]:<45} {flag} {new_title[:54]:<55} {tags} tags")


def fix_listings(listings: list[dict], client: EtsyAPIClient, dry_run: bool = False) -> None:
    fixed = 0
    skipped = 0
    errors = 0

    for i, l in enumerate(listings, 1):
        lid = l["listing_id"]
        old_title = l["title"]
        desc = l.get("description", "")

        data = _match_listing(old_title)
        if data:
            new_title = data["title"]
            tags = data["tags"][:13]
        elif "Kawaii Art Print Design" in old_title:
            new_title = _build_generic_title(old_title)
            tags = DEFAULT_TAGS[:13]
        else:
            new_title = old_title
            tags = DEFAULT_TAGS[:13]

        # Validate
        if len(new_title) > 70:
            print(f"  [{i}/{len(listings)}] WARNING title too long ({len(new_title)}): {new_title}")

        # Add AI disclosure if missing
        if _needs_ai_disclosure(desc):
            new_desc = desc.rstrip() + AI_DISCLOSURE
        else:
            new_desc = desc

        updates: dict = {}
        if new_title != old_title:
            updates["title"] = new_title
        if not l.get("tags"):
            updates["tags"] = tags
        if new_desc != desc:
            updates["description"] = new_desc

        if not updates:
            print(f"  [{i}/{len(listings)}] SKIP {lid} — already optimized")
            skipped += 1
            continue

        print(f"  [{i}/{len(listings)}] {lid}  '{old_title}' → '{new_title}'  ({len(tags)} tags)")

        if dry_run:
            print(f"    [DRY RUN]")
            continue

        try:
            client.update_listing(lid, updates)
            fixed += 1
            time.sleep(0.4)
        except EtsyAPIError as e:
            print(f"    ✗ Error: {e}")
            errors += 1

    print(f"\n{'[DRY RUN] Would fix' if dry_run else 'Fixed'}: {fixed}  Skipped: {skipped}  Errors: {errors}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args()

    if not args.dry_run and not args.fix:
        parser.print_help()
        return

    client = EtsyAPIClient()
    listings = get_printify_listings(client)
    print(f"Found {len(listings)} Printify listings on Etsy")

    if args.dry_run:
        preview_changes(listings)
    else:
        fix_listings(listings, client)


if __name__ == "__main__":
    main()
