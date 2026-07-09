#!/usr/bin/env python3
"""
listing_performance_monitor.py

Scans all active listings for quality issues that hurt ranking:
  - Title > 70 chars (mobile ranking penalty)
  - Title missing "Instant Download" (digital products)
  - Fewer than 5 photos (algorithm penalty)
  - Fewer than 13 tags
  - Tags with special characters or over 20 chars
  - Missing description

Saves a dated report to data/reports/listing_health_YYYY-MM-DD.txt
and prints a summary to stdout.

Usage:
  python tools/listing_performance_monitor.py
  python tools/listing_performance_monitor.py --save-only   (no console output)
  python tools/listing_performance_monitor.py --category digital   (filter by title keyword)
"""

from __future__ import annotations

import os
import sys
import re
import json
import argparse
from datetime import date
from pathlib import Path

_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
with open(_env_path) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etsy_api import EtsyAPIClient, EtsyAPIError

REPORTS_DIR = Path("data/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

_SPECIAL = re.compile(r"[,;!?@#$%^&*()\[\]{}'\"<>/\\|=+]")

DIGITAL_KEYWORDS = {"planner", "sticker", "digital", "printable", "svg", "sublimation", "download"}


def _is_digital(title: str) -> bool:
    tl = title.lower()
    return any(k in tl for k in DIGITAL_KEYWORDS)


def audit_listing(listing: dict) -> list[str]:
    issues = []
    title = listing.get("title") or ""
    desc = listing.get("description") or ""
    tags = listing.get("tags") or []
    images = listing.get("images") or []

    if len(title) > 70:
        issues.append(f"Title {len(title)} chars (>70 mobile penalty)")
    if _is_digital(title) and "instant download" not in title.lower():
        issues.append("Missing 'Instant Download' in title")
    if len(tags) < 13:
        issues.append(f"Only {len(tags)}/13 tags")
    for tag in tags:
        if len(tag) > 20:
            issues.append(f"Tag too long: '{tag}' ({len(tag)} chars)")
        if _SPECIAL.search(tag):
            issues.append(f"Tag has special chars: '{tag}'")
    if len(images) < 5:
        issues.append(f"Only {len(images)} photos (target: 10)")
    if not desc:
        issues.append("Missing description")
    elif len(desc) < 300:
        issues.append(f"Description too short ({len(desc)} chars)")

    return issues


def run(category_filter: str = "", save_only: bool = False) -> dict:
    client = EtsyAPIClient()
    if not client.shop_id:
        print("ERROR: ETSY_SHOP_ID not set in .env")
        sys.exit(1)

    if not save_only:
        print("Fetching all active listings...")

    try:
        listings = client.get_shop_listings_all(state="active")
    except EtsyAPIError as e:
        print(f"ERROR fetching listings: {e}")
        sys.exit(1)

    if category_filter:
        listings = [l for l in listings if category_filter.lower() in (l.get("title") or "").lower()]

    clean = []
    flagged = []

    for listing in listings:
        issues = audit_listing(listing)
        entry = {
            "listing_id": listing.get("listing_id"),
            "title": listing.get("title", "")[:70],
            "state": listing.get("state"),
            "issues": issues,
        }
        if issues:
            flagged.append(entry)
        else:
            clean.append(entry)

    total = len(listings)
    report_lines = [
        f"# Listing Health Report — {date.today()}",
        f"Total active listings: {total}",
        f"Clean: {len(clean)}  |  Flagged: {len(flagged)}",
        "",
    ]

    if flagged:
        report_lines.append(f"## Flagged Listings ({len(flagged)})\n")
        for entry in flagged:
            report_lines.append(f"### [{entry['listing_id']}] {entry['title']}")
            for issue in entry["issues"]:
                report_lines.append(f"  ✗ {issue}")
            report_lines.append("")

    if clean:
        report_lines.append(f"\n## Clean Listings ({len(clean)})")
        for entry in clean:
            report_lines.append(f"  ✓ [{entry['listing_id']}] {entry['title']}")

    report_text = "\n".join(report_lines)

    report_path = REPORTS_DIR / f"listing_health_{date.today()}.txt"
    report_path.write_text(report_text)

    if not save_only:
        print(f"\n{'='*70}")
        print(f"LISTING HEALTH REPORT — {date.today()}")
        print(f"{'='*70}")
        print(f"Total: {total}   Clean: {len(clean)}   Flagged: {len(flagged)}")
        if flagged:
            print(f"\n⚠️  FLAGGED ({len(flagged)} listings):")
            for entry in flagged:
                print(f"\n  [{entry['listing_id']}] {entry['title']}")
                for issue in entry["issues"]:
                    print(f"    ✗ {issue}")
        else:
            print("\n✓ All listings pass quality checks.")
        print(f"\nFull report saved: {report_path}")

    return {"total": total, "clean": len(clean), "flagged": len(flagged), "report_path": str(report_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit all active Etsy listings for quality issues")
    parser.add_argument("--category", default="", help="Filter listings by title keyword")
    parser.add_argument("--save-only", action="store_true", help="Save report without printing to console")
    args = parser.parse_args()
    run(category_filter=args.category, save_only=args.save_only)


if __name__ == "__main__":
    main()
