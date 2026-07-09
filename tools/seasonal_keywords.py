#!/usr/bin/env python3
"""
Seasonal Keyword Updater — shows which keywords to add to listings and when.

Based on CLAUDE.md seasonal calendar: update keywords 6 weeks before each peak.
Can also push keyword updates directly to Etsy listings via the API.

Usage:
  python tools/seasonal_keywords.py              # show upcoming peaks + recommendations
  python tools/seasonal_keywords.py --push       # push keyword updates to Etsy listings
  python tools/seasonal_keywords.py --weeks 8    # look ahead N weeks (default 8)
"""

from __future__ import annotations

import os
import sys
import json
import argparse
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Guarded: Railway has no .env file (env vars are injected by the platform
# directly) -- this is now invoked there via main.py's _EXEC_COMMANDS registry.
_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(_ENV_PATH):
    with open(_ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from tools.etsy_api import EtsyAPIClient, is_configured


# ── Seasonal calendar (peaks + update deadlines + keywords) ──────────────────
# Update: 6 weeks before each peak. Format: (peak_date, season_name, keywords_to_add)

def _build_calendar(year: int) -> list[dict]:
    return [
        {
            "season":       "Back to School",
            "peak":         date(year, 8, 15),         # mid-August
            "update_by":    date(year, 7, 4),           # 6 weeks before = July 4
            "priority":     "HIGH",
            "keywords_add": [
                "student planner 2026",
                "school planner",
                "academic planner",
                "back to school",
                "study planner",
                "homework planner",
            ],
            "listings_to_update": ["DP1027", "DP1030", "DP1033"],
            "tag_slots_to_replace": [
                ("2026 life planner", "student planner 2026"),
                ("printable planner", "school planner"),
            ],
            "description_note": (
                "Add 'back to school' mention to first paragraph. "
                "Update title to include 'School Planner' for DP1027."
            ),
        },
        {
            "season":       "Holiday Gifting / New Year",
            "peak":         date(year, 12, 20),         # holiday shopping peak
            "update_by":    date(year, 11, 8),          # 6 weeks before
            "priority":     "HIGH",
            "keywords_add": [
                f"new year planner {year + 1}",
                f"{year + 1} planner",
                "gift for planner lover",
                "christmas gift digital",
                "new year goals",
                "holiday planner",
            ],
            "listings_to_update": ["DP1026", "DP1027", "DP1028", "DP1029"],
            "tag_slots_to_replace": [
                ("daily planner pdf", f"new year planner {year + 1}"),
                ("2026 life planner", f"{year + 1} planner"),
            ],
            "description_note": (
                "Add gift-giving language to description hook. "
                "Mention 'perfect gift for planner lovers' near the top."
            ),
        },
        {
            "season":       "Valentine's Day",
            "peak":         date(year + 1 if date.today() > date(year, 2, 14) else year, 2, 14),
            "update_by":    None,  # computed below
            "priority":     "MEDIUM",
            "keywords_add": [
                "valentine gift digital",
                "love journal",
                "self care planner",
                "galentines gift",
            ],
            "listings_to_update": ["DP1026", "DP1029"],
            "tag_slots_to_replace": [
                ("planner bundle", "valentine gift digital"),
            ],
            "description_note": "Add self-care / gifting language near top of description.",
        },
        {
            "season":       "Spring Reset",
            "peak":         date(year + 1 if date.today() > date(year, 3, 20) else year, 3, 20),
            "update_by":    None,  # computed below
            "priority":     "MEDIUM",
            "keywords_add": [
                "spring planner",
                "fresh start planner",
                "new beginnings journal",
            ],
            "listings_to_update": ["DP1026", "DP1031"],
            "tag_slots_to_replace": [
                ("habit tracker pdf", "spring planner"),
            ],
            "description_note": "Add 'fresh start' and 'spring goals' language to description.",
        },
        {
            "season":       "Mother's Day",
            "peak":         date(year, 5, 11),          # 2nd Sunday in May
            "update_by":    date(year, 3, 30),
            "priority":     "MEDIUM",
            "keywords_add": [
                "mothers day gift digital",
                "gift for mom",
                "mom planner",
            ],
            "listings_to_update": ["DP1026"],
            "tag_slots_to_replace": [
                ("daily planner pdf", "mothers day gift"),
            ],
            "description_note": "Add gift-giving hook in first paragraph near Mother's Day window.",
        },
        {
            "season":       "Teacher Appreciation",
            "peak":         date(year, 5, 6),           # first week of May
            "update_by":    date(year, 3, 25),
            "priority":     "MEDIUM",
            "keywords_add": [
                "teacher appreciation gift",
                "gift for teacher",
                "teacher digital download",
            ],
            "listings_to_update": ["DP1033"],
            "tag_slots_to_replace": [
                ("school year planner", "teacher gift digital"),
            ],
            "description_note": "Add teacher appreciation gift language in hook.",
        },
    ]


def _update_by(peak: date) -> date:
    return peak - timedelta(weeks=6)


def _urgency(update_by: date, today: date) -> str:
    days_left = (update_by - today).days
    if days_left < 0:
        return "OVERDUE"
    if days_left <= 7:
        return "THIS WEEK"
    if days_left <= 21:
        return "SOON"
    return "UPCOMING"


def show_report(lookahead_weeks: int = 8) -> list[dict]:
    today = date.today()
    year  = today.year
    calendar = _build_calendar(year)

    # Fill in computed update_by dates
    for entry in calendar:
        if entry["update_by"] is None:
            entry["update_by"] = _update_by(entry["peak"])

    # Filter to entries whose peak is within lookahead window or overdue
    cutoff = today + timedelta(weeks=lookahead_weeks)
    relevant = [
        e for e in calendar
        if e["peak"] >= today or (e["update_by"] < today < e["peak"])
    ]
    relevant.sort(key=lambda e: e["update_by"])

    divider = "─" * 68

    print(f"\n{divider}")
    print(f"  SEASONAL KEYWORD CALENDAR  ·  Today: {today}")
    print(f"  Showing next {lookahead_weeks} weeks of action items")
    print(divider)

    actionable = []
    for e in relevant:
        urg = _urgency(e["update_by"], today)
        days_left = (e["update_by"] - today).days
        flag = {"OVERDUE": "🔴", "THIS WEEK": "🟡", "SOON": "🟠", "UPCOMING": "🔵"}.get(urg, "  ")

        print(f"\n  {flag} {e['season'].upper()}  [{e['priority']}]  ·  {urg}")
        print(f"     Peak:      {e['peak']}")
        print(f"     Update by: {e['update_by']}  ({days_left} days from today)")
        print(f"     Listings:  {', '.join(e['listings_to_update'])}")
        print(f"     Add tags:  {', '.join(e['keywords_add'][:3])}{'...' if len(e['keywords_add']) > 3 else ''}")
        print(f"     Note:      {e['description_note'][:70]}...")

        if urg in ("OVERDUE", "THIS WEEK", "SOON"):
            actionable.append(e)

    if not actionable:
        print(f"\n  No urgent action needed in the next {lookahead_weeks} weeks.")

    print(f"\n{divider}")
    print(f"  ACTION SUMMARY ({len(actionable)} items need attention now):")
    for e in actionable:
        print(f"    → {e['season']}: update {', '.join(e['listings_to_update'])}")
    print(divider)
    print()

    return actionable


def _get_listing_data(client: EtsyAPIClient, listing_id: str) -> dict | None:
    """Fetch current listing data."""
    try:
        return client.get_listing(listing_id)
    except Exception as e:
        print(f"    Failed to fetch listing {listing_id}: {e}")
        return None


def push_updates(dry_run: bool = True) -> None:
    """Push keyword updates to Etsy listings for overdue/urgent seasons."""
    if not is_configured():
        print("Etsy API not configured — cannot push updates.")
        return

    client = EtsyAPIClient(
        api_key=os.getenv("ETSY_API_KEY", ""),
        access_token=os.getenv("ETSY_ACCESS_TOKEN", ""),
    )

    today = date.today()
    year  = today.year
    calendar = _build_calendar(year)
    for e in calendar:
        if e["update_by"] is None:
            e["update_by"] = _update_by(e["peak"])

    urgent = [e for e in calendar if _urgency(e["update_by"], today) in ("OVERDUE", "THIS WEEK")]
    if not urgent:
        print("No urgent keyword updates needed right now.")
        return

    # Load product catalog to map product IDs to Etsy listing IDs
    catalog_path = Path(__file__).parent.parent / "data" / "product_catalog.json"
    catalog = {}
    if catalog_path.exists():
        with open(catalog_path) as f:
            for item in json.load(f):
                pid = item.get("product_id", "")
                lid = item.get("etsy_listing_id", "")
                if pid and lid:
                    catalog[pid] = str(lid)

    print(f"\n{'='*60}")
    print(f"  Pushing seasonal keyword updates")
    if dry_run:
        print(f"  DRY RUN — no changes will be made. Pass --push to apply.")
    print(f"{'='*60}\n")

    for season_entry in urgent:
        print(f"  Season: {season_entry['season']}")
        for pid in season_entry["listings_to_update"]:
            listing_id = catalog.get(pid)
            if not listing_id:
                print(f"    {pid}: no Etsy listing ID in product_catalog.json — skip")
                continue

            listing = _get_listing_data(client, listing_id)
            if not listing:
                continue

            current_tags = listing.get("tags", [])
            if not current_tags:
                print(f"    {pid}: no tags returned — skip")
                continue

            # Apply tag swaps
            new_tags = list(current_tags)
            swaps_applied = []
            for (old_tag, new_tag) in season_entry["tag_slots_to_replace"]:
                if old_tag in new_tags and new_tag not in new_tags:
                    idx = new_tags.index(old_tag)
                    new_tags[idx] = new_tag[:20]
                    swaps_applied.append(f"{old_tag} → {new_tag[:20]}")

            if not swaps_applied:
                print(f"    {pid} (listing {listing_id}): no matching tags to swap — skip")
                continue

            print(f"    {pid} (listing {listing_id}):")
            for swap in swaps_applied:
                print(f"      {swap}")

            if not dry_run:
                try:
                    client.update_listing(listing_id, {"tags": new_tags})
                    print(f"      ✓ Tags updated on Etsy")
                except Exception as e:
                    print(f"      ✗ Update failed: {e}")
            else:
                print(f"      (dry run — not applied)")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seasonal keyword calendar and updater")
    parser.add_argument("--push",    action="store_true", help="Push urgent updates to Etsy listings")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be pushed without applying")
    parser.add_argument("--weeks",   type=int, default=10, help="Lookahead window in weeks (default 10)")
    args = parser.parse_args()

    show_report(lookahead_weeks=args.weeks)

    if args.push:
        push_updates(dry_run=False)
    elif args.dry_run:
        push_updates(dry_run=True)
