#!/usr/bin/env python3
"""
fix_descriptions.py
Rewrites wall-art listing descriptions that wrongly claim a PHYSICAL shipped
item into correct DIGITAL instant-download descriptions (CLAUDE.md Gate 6).

PREVIEW (default): generates corrected descriptions and writes them to
review_batches/corrected_descriptions.json + a human-readable .txt. No live
changes. Review these before applying.

APPLY (--apply): for each listing, fixes the quantity quirk (2997 → 999 via the
inventory endpoint) then PATCHes the corrected description. Only run after the
listings are deactivated and Scott has reviewed the preview.

Usage:
    python tools/fix_descriptions.py                 # preview all flagged listings
    python tools/fix_descriptions.py --id <LID>      # preview one listing
    python tools/fix_descriptions.py --apply          # apply after approval
    python tools/fix_descriptions.py --apply --id <LID>
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass
from etsy_api import EtsyAPIClient

REPORT_DIR = BASE_DIR / "review_batches"
PULL_PATH = REPORT_DIR / "etsy_digital_files_pull.json"
OUT_JSON = REPORT_DIR / "corrected_descriptions.json"
OUT_TXT = REPORT_DIR / "corrected_descriptions.txt"

# Phrases that mark a description as wrongly claiming physical fulfillment
PHYSICAL_PHRASES = [
    "physical print shipped", "shipped directly to you", "arrives at your door",
    "no printing or downloading", "no downloading needed", "ships in",
    "will be shipped", "shipped to you", "ships to your",
]

AI_DISCLOSURE = (
    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "🤖 ABOUT THIS DESIGN\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "This product was designed using AI image generation tools, with original "
    "prompts, curation, and finishing by the seller. All products are reviewed "
    "for quality before listing."
)


def clean_title(title: str) -> str:
    """Drop trailing ' | Multiple Sizes' etc. and pipe noise for the hook."""
    return title.split("|")[0].split(",")[0].strip()


def build_description(title: str) -> str:
    """Produce a correct digital instant-download wall-art description."""
    art = clean_title(title)
    art_lower = art.lower()
    return f"""Instant download printable {art_lower} — digital download delivered immediately after purchase, ready to print at home or at any print shop.

Decorate your space in minutes: download, print, and frame. No physical item is shipped — you receive high-resolution print-ready files instantly.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution printable files (300 DPI, sRGB)
✅ Multiple print sizes in one ZIP:
   • 2:3 ratio — 4x6, 8x12, 12x18, 16x24 in
   • 4:5 ratio — 8x10, 16x20 in
   • A-series — A4, A3
   • Square — 8x8, 12x12 in
✅ README with printing instructions

━━━━━━━━━━━━━━━━━━━━━━━━
🖨 HOW TO PRINT
━━━━━━━━━━━━━━━━━━━━━━━━
1. Download and unzip your files instantly from Etsy
2. Choose the size that matches your frame
3. Print at home, or upload to a print shop (Staples, Walgreens, Mpix, or local)
4. Select "print at 100% / do not scale" and use matte or lustre paper for best results

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this a physical item?
A: No — this is a digital download only. Nothing is shipped. You'll receive print-ready files instantly after purchase.

Q: What sizes can I print?
A: The ZIP includes 2:3, 4:5, A-series, and square ratios so you can print everything from 4x6 up to 16x24 inches.

Q: Can I print at a print shop?
A: Yes! The files are 300 DPI and ready for home printers or professional print labs.

Q: Can I share or resell the files?
A: This license is for personal use only. Please don't share, resell, or redistribute the files.

{AI_DISCLOSURE}

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use."""


def needs_fix(description: str) -> list[str]:
    dl = description.lower()
    return [p for p in PHYSICAL_PHRASES if p in dl]


def fix_quantity(api: EtsyAPIClient, lid: int) -> bool:
    """Set offering quantity to 999 via the listing-level inventory endpoint."""
    try:
        inv = api._request("GET", f"listings/{lid}/inventory")
    except Exception as e:
        print(f"    quantity GET error: {e}")
        return False
    products = inv.get("products", [])
    clean = {"products": []}
    for p in products:
        offerings = []
        for o in p.get("offerings", []):
            pr = o.get("price", {})
            price = pr.get("amount", 0) / pr.get("divisor", 100) if isinstance(pr, dict) else pr
            offerings.append({"quantity": 999, "is_enabled": o.get("is_enabled", True), "price": price})
        clean["products"].append({
            "sku": p.get("sku", ""),
            "offerings": offerings,
            "property_values": p.get("property_values", []),
        })
    try:
        api._request("PUT", f"listings/{lid}/inventory", body=clean)
        return True
    except Exception as e:
        print(f"    quantity PUT error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Fix physical→digital wall-art descriptions")
    parser.add_argument("--apply", action="store_true", help="Apply fixes to Etsy (after approval)")
    parser.add_argument("--id", type=int, help="Only this listing ID")
    args = parser.parse_args()

    api = EtsyAPIClient()

    # Determine candidate listings
    if args.id:
        candidates = [args.id]
    else:
        if not PULL_PATH.exists():
            print(f"ERROR: {PULL_PATH} not found. Run the listings pull first.")
            sys.exit(1)
        pull = json.load(open(PULL_PATH))
        candidates = [r["listing_id"] for r in pull if r.get("file_count", 0) > 0 and "error" not in r]

    print(f"Scanning {len(candidates)} listings for physical→digital description fixes "
          f"({'APPLY' if args.apply else 'PREVIEW'} mode)…\n")

    results = []
    txt_lines = []
    for i, lid in enumerate(candidates, 1):
        try:
            listing = api.get_listing(lid)
        except Exception as e:
            print(f"  [{i}/{len(candidates)}] {lid} fetch error: {e}")
            continue
        title = listing.get("title", "")
        desc = listing.get("description", "")
        hits = needs_fix(desc)
        if not hits:
            continue

        new_desc = build_description(title)
        rec = {"listing_id": lid, "title": title, "matched_phrases": hits,
               "old_description": desc, "new_description": new_desc}
        results.append(rec)

        txt_lines.append("=" * 70)
        txt_lines.append(f"[{lid}] {title}")
        txt_lines.append(f"matched: {hits}")
        txt_lines.append("-" * 70)
        txt_lines.append("NEW DESCRIPTION:")
        txt_lines.append(new_desc)
        txt_lines.append("")

        print(f"  [{i}/{len(candidates)}] {lid} — {title[:50]} → needs fix {hits}")

        if args.apply:
            if fix_quantity(api, lid):
                time.sleep(1)
            try:
                api.update_listing(lid, {"description": new_desc})
                print(f"      ✓ description updated")
            except Exception as e:
                print(f"      ✗ description update error: {e}")
            time.sleep(0.6)
        time.sleep(0.2)

    REPORT_DIR.mkdir(exist_ok=True)
    json.dump(results, open(OUT_JSON, "w"), indent=2)
    OUT_TXT.write_text("\n".join(txt_lines))

    print(f"\n{'Applied' if args.apply else 'Previewed'} {len(results)} description fixes.")
    print(f"  Review: {OUT_TXT}")
    print(f"  Data:   {OUT_JSON}")
    if not args.apply and results:
        print("\nThis was PREVIEW only — no live listings changed.")
        print("After deactivating + reviewing, run with --apply to push the fixes.")


if __name__ == "__main__":
    main()
