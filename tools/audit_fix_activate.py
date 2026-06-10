#!/usr/bin/env python3
"""
audit_fix_activate.py — Audit all inactive/edit listings, auto-fix issues, activate passing ones.

Checks:
  1. Title: pipes → commas, add "Printable"+"Instant Download", fix generic "No.XXXX" names,
     enforce ≤70 chars
  2. Description: add AI disclosure block if missing
  3. Photo count: must have ≥5 photos
  4. Not a test listing

Usage:
    python tools/audit_fix_activate.py --dry-run    # preview fixes, no API calls
    python tools/audit_fix_activate.py              # apply fixes + activate
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

# Listings to never touch
SKIP_IDS = {
    4509593049,  # Test listing
}

# These active-listing duplicates exist for DP1052-1054 — don't activate the extra copies
SKIP_DUPLICATE_ART_CODES = {"DP1052", "DP1053", "DP1054"}

AI_DISCLOSURE = (
    "\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "🤖 ABOUT THIS DESIGN\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "This product was designed using AI image generation tools, with original prompts, "
    "curation, and finishing by the seller. All products are reviewed for quality before listing."
)


# ─── Load cross-reference data ────────────────────────────────────────────────

def _load_references():
    """Returns (lid_to_dp, dp_to_canonical_title)."""
    with open(ROOT / "data" / "listing_manifest.json") as f:
        manifest = json.load(f)
    with open(ROOT / "data" / "dp_listing_map.json") as f:
        dp_map = json.load(f)

    lid_to_dp: dict[str, str] = {}
    for lid, v in manifest.items():
        sources = v.get("art_sources", {})
        for code in sources:
            lid_to_dp[lid] = code.upper()
            break  # take first

    dp_to_title: dict[str, str] = {}
    for code, entry in dp_map.items():
        if isinstance(entry, dict):
            t = entry.get("title") or entry.get("planner_title", "")
            if t:
                dp_to_title[code.upper()] = t

    return lid_to_dp, dp_to_title


# ─── Title fixers ─────────────────────────────────────────────────────────────

def _fix_pipes(title: str) -> str:
    """Replace ' | ' and ' |' with ', '."""
    return re.sub(r"\s*\|\s*", ", ", title).strip().rstrip(",").strip()


def _ensure_keywords(title: str) -> str:
    """Add 'Printable' and 'Instant Download' if missing and title allows room."""
    has_printable = re.search(r"\bprintable\b|\bdigital\b|\bsvg\b|\bpdf\b", title, re.I)
    has_instant = re.search(r"\binstant download\b", title, re.I)

    parts = []
    if not has_printable and len(title) + len(", Printable") <= 70:
        parts.append("Printable")
    if not has_instant and len(title) + len(", ".join(parts)) + len(", Instant Download") <= 70:
        parts.append("Instant Download")

    if parts:
        title = title.rstrip(",") + ", " + ", ".join(parts)
    return title[:70].strip().rstrip(",")


def _fix_title(
    raw_title: str,
    listing_id: int,
    lid_to_dp: dict,
    dp_to_title: dict,
) -> tuple[str, list[str]]:
    """
    Returns (fixed_title, list_of_changes_made).
    """
    changes: list[str] = []
    title = raw_title

    # 1. Replace generic "Kawaii Art Print No.XXXX" with canonical title from dp_map
    if re.match(r"Kawaii Art Print No\.\d+", title, re.I):
        dp_code = lid_to_dp.get(str(listing_id))
        canonical = dp_to_title.get(dp_code, "") if dp_code else ""
        if canonical:
            title = canonical
            changes.append(f"renamed from generic No.XXXX → canonical '{canonical[:50]}'")
        else:
            changes.append("WARN: no canonical title found for generic No.XXXX listing")

    # 2. Fix pipe separators
    if "|" in title:
        old = title
        title = _fix_pipes(title)
        if title != old:
            changes.append("pipes → commas")

    # 3. Ensure "Printable"/"Digital" and "Instant Download"
    old = title
    title = _ensure_keywords(title)
    if title != old:
        changes.append("added missing keywords (Printable/Instant Download)")

    # 4. Hard-trim to 70 chars
    if len(title) > 70:
        title = title[:70].strip().rstrip(",")
        changes.append("trimmed to 70 chars")

    return title, changes


# ─── Description fixer ────────────────────────────────────────────────────────

def _needs_ai_disclosure(description: str) -> bool:
    markers = ["🤖", "AI image", "ai image", "ABOUT THIS DESIGN", "AI tools", "artificial intelligence"]
    return not any(m.lower() in description.lower() for m in markers)


# ─── Main audit loop ──────────────────────────────────────────────────────────

def run(dry_run: bool) -> None:
    c = EtsyAPIClient()
    lid_to_dp, dp_to_title = _load_references()

    # Pull all inactive (edit) listings
    print("Fetching inactive listings...")
    all_inactive: list[dict] = []
    offset = 0
    while True:
        r = c._request(
            "GET",
            f"shops/{SHOP_ID}/listings?state=edit&limit=100&offset={offset}&includes[]=images",
        )
        batch = r.get("results", [])
        all_inactive.extend(batch)
        if len(batch) < 100:
            break
        offset += 100

    # Also pull drafts (0 photos — want to report them)
    r2 = c._request("GET", f"shops/{SHOP_ID}/listings?state=draft&limit=100&includes[]=images")
    all_drafts = r2.get("results", [])

    print(f"  {len(all_inactive)} inactive, {len(all_drafts)} draft\n")

    results = {
        "activated": [],
        "fixed_only": [],       # fixes applied but couldn't activate (e.g. photo < 5)
        "skipped": [],
        "errors": [],
    }

    def _report_skip(lid, title, reason):
        results["skipped"].append({"id": lid, "title": title[:65], "reason": reason})
        print(f"  [SKIP] {lid} — {reason}")

    # Process drafts first (just report — no action)
    print("=== DRAFT LISTINGS (no photos — cannot activate) ===")
    for l in all_drafts:
        lid = l["listing_id"]
        title = l["title"]
        imgs = len(l.get("images", []))
        _report_skip(lid, title, f"draft with {imgs} photos — needs photos before activating")
    print()

    print("=== PROCESSING INACTIVE LISTINGS ===\n")

    for listing in all_inactive:
        lid = listing["listing_id"]
        title = listing["title"]
        description = listing.get("description", "")
        images = listing.get("images", [])
        photo_count = len(images)
        state = listing.get("state", "")

        print(f"--- {lid} [{photo_count} photos] {title[:60]}")

        # Hard skips
        if lid in SKIP_IDS:
            _report_skip(lid, title, "test listing — never activate")
            print()
            continue

        dp_code = lid_to_dp.get(str(lid))
        if dp_code and dp_code in SKIP_DUPLICATE_ART_CODES:
            _report_skip(lid, title, f"duplicate of active listing for {dp_code}")
            print()
            continue

        if photo_count == 0:
            _report_skip(lid, title, "0 photos — needs photos first")
            print()
            continue

        # Collect all needed fixes
        patch: dict = {}
        fix_log: list[str] = []

        # Title fixes
        new_title, title_changes = _fix_title(title, lid, lid_to_dp, dp_to_title)
        if new_title != title:
            patch["title"] = new_title
            fix_log.extend(title_changes)
            print(f"  TITLE FIX: {title[:55]}")
            print(f"          → {new_title[:55]}")

        # Description fixes
        if _needs_ai_disclosure(description):
            patch["description"] = description + AI_DISCLOSURE
            fix_log.append("added AI disclosure")
            print(f"  DESC FIX: added AI disclosure")

        # Photo check (warn only, don't block activation if ≥5)
        if photo_count < 5:
            print(f"  WARN: only {photo_count} photos (target 10, minimum 5 to activate)")

        # Apply patch (title + description fixes)
        if patch and not dry_run:
            try:
                c.update_listing(lid, patch)
                time.sleep(0.4)  # rate limit buffer
                print(f"  PATCHED: {', '.join(fix_log)}")
            except Exception as exc:
                results["errors"].append({"id": lid, "error": str(exc)})
                print(f"  ERROR patching: {exc}")
                print()
                continue
        elif patch and dry_run:
            print(f"  [DRY] would patch: {', '.join(fix_log)}")

        # Activate (need ≥5 photos)
        if photo_count >= 5:
            final_title = new_title if "title" in patch else title
            if not dry_run:
                try:
                    c.update_listing(lid, {"state": "active"})
                    time.sleep(0.4)
                    results["activated"].append({"id": lid, "title": final_title[:65], "fixes": fix_log})
                    print(f"  ✓ ACTIVATED")
                except Exception as exc:
                    results["errors"].append({"id": lid, "error": f"activate failed: {exc}"})
                    print(f"  ERROR activating: {exc}")
            else:
                results["activated"].append({"id": lid, "title": final_title[:65], "fixes": fix_log})
                print(f"  [DRY] would activate")
        else:
            results["fixed_only"].append({"id": lid, "title": title[:65], "reason": f"only {photo_count} photos"})
            print(f"  → not activating: only {photo_count} photos (need ≥5)")

        print()

    # Summary
    print("\n" + "=" * 65)
    print(f"SUMMARY {'(DRY RUN)' if dry_run else ''}")
    print("=" * 65)
    print(f"  Activated:     {len(results['activated'])}")
    print(f"  Fixed (not activated): {len(results['fixed_only'])}")
    print(f"  Skipped:       {len(results['skipped'])}")
    print(f"  Errors:        {len(results['errors'])}")

    if results["errors"]:
        print("\nErrors:")
        for e in results["errors"]:
            print(f"  {e['id']}: {e['error']}")

    if results["fixed_only"]:
        print("\nFixed but not activated (need more photos):")
        for f in results["fixed_only"]:
            print(f"  {f['id']}: {f['reason']} — {f['title']}")

    if results["skipped"]:
        print("\nSkipped:")
        for s in results["skipped"]:
            print(f"  {s['id']}: {s['reason']} — {s['title']}")

    # Save report
    report_path = ROOT / "data" / "reports" / "activate_report_2026-06-10.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull report → {report_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="Preview fixes without making API calls")
    args = ap.parse_args()
    run(dry_run=args.dry_run)
