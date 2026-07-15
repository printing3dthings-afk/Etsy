#!/usr/bin/env python3
"""
listing_compliance_sweep.py
Full-shop compliance sweep, going beyond listing_integrity_check.py's
manifest-scoped coverage: pulls EVERY currently-active Etsy listing and
cross-references it against data/listing_manifest.json. A listing with zero
manifest mapping is treated as its own FAIL (fail-closed — the quality gate
never ran for it, so it can't be assumed compliant just because no rule
caught it. Matches the DP1030-1034 wall-art/planner code-collision precedent:
unmapped/unresolved must block, never silently pass).

For mapped listings, reuses listing_integrity_check.audit_listing() verbatim
(FAST mode only — no photo download/hashing — to keep a full-shop run to a
few minutes; --full mode's photo-hash check is a separate, slower pass and
out of scope for this sweep).

Every FAIL gets:
  - a staged `deactivate_listing` action in the Action Center (via
    db.enqueue_action) for Scott's one-tap approve/reject — this script never
    deactivates anything itself
  - a linked todo describing exactly what's wrong and pointing at the queue

Every WARN gets a todo only (no takedown stage) — matches the severity
handling already used elsewhere (WARN = worth fixing, not worth pulling a
live, selling listing over).

Usage:
    python tools/listing_compliance_sweep.py            # run + stage + report
    python tools/listing_compliance_sweep.py --dry-run   # report only, stage nothing
"""

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

from etsy_api import EtsyAPIClient
import listing_integrity_check as lic
from tools.api_server import db as _db

REPORT_DIR = BASE_DIR / "review_batches"


def _unmapped_result(listing: dict) -> dict:
    """Synthesize an audit_listing()-shaped result for a listing Etsy shows
    as active but that has no entry in data/listing_manifest.json — fail
    closed rather than silently skipping it."""
    listing_id = str(listing.get("listing_id", ""))
    return {
        "listing_id": listing_id,
        "dp_codes": [],
        "type": "unmapped",
        "issues": [{
            "severity": "FAIL",
            "check": "no_manifest_mapping",
            "detail": (
                "Listing is active on Etsy but has no entry in "
                "data/listing_manifest.json — the quality gate has never run "
                "against it. Needs manual mapping/review before it can be "
                "verified compliant."
            ),
        }],
        "status": "FAIL",
        "title": listing.get("title", ""),
        "photo_count": 0,
        "file_count": 0,
        "tag_count": len(listing.get("tags", []) or []),
    }


def run_sweep(dry_run: bool = False) -> list[dict]:
    manifest = lic._load_json(lic.MANIFEST_PATH)
    rules = lic._load_json(lic.RULES_PATH)
    approvals = lic._load_json(lic.APPROVALS_PATH)
    registry = lic._load_json(lic.REGISTRY_PATH)

    api = EtsyAPIClient()

    print("Fetching every active listing from the live shop…")
    active_listings = api.get_shop_listings_all(state="active")
    print(f"  {len(active_listings)} active listings found on Etsy.\n")

    results = []
    start = time.time()
    for i, listing in enumerate(active_listings, 1):
        listing_id = str(listing.get("listing_id", ""))
        entry = manifest.get(listing_id)
        if entry is None:
            r = _unmapped_result(listing)
        else:
            r = lic.audit_listing(api, listing_id, entry, rules, approvals, registry,
                                  full_mode=False)
        results.append(r)
        icon = lic.SEVERITY_ICON.get(r["status"], "?")
        print(f"  {icon} [{i}/{len(active_listings)}] {listing_id} — {r['status']}")
        time.sleep(0.3)

    elapsed = time.time() - start
    print("\n" + lic.render_report(results, elapsed))

    REPORT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    report_path = REPORT_DIR / f"compliance_sweep_{stamp}.txt"
    report_path.write_text(lic.render_report(results, elapsed))
    print(f"\nReport saved -> {report_path}")

    staged, todoed = 0, 0
    if not dry_run:
        for r in results:
            if r["status"] == "FAIL":
                fail_details = "; ".join(
                    i["detail"] for i in r["issues"] if i["severity"] == "FAIL"
                )
                title_short = r["title"][:60] if r["title"] else "(no title)"
                summary = f"Deactivate listing {r['listing_id']} ({title_short}) — {fail_details}"[:500]
                queue_id = _db.enqueue_action(
                    "deactivate_listing",
                    summary,
                    {"listing_id": int(r["listing_id"]), "_state_at_staging": "active"},
                )
                staged += 1
                _db.add_todo(
                    f"Compliance FAIL — listing {r['listing_id']} ({title_short}): "
                    f"{fail_details} [staged deactivate_listing, queue #{queue_id} — "
                    f"review in Action Center]",
                    added_by="frank", category="question",
                )
                todoed += 1
            elif r["status"] == "WARN":
                warn_details = "; ".join(
                    i["detail"] for i in r["issues"] if i["severity"] == "WARN"
                )
                title_short = r["title"][:60] if r["title"] else "(no title)"
                _db.add_todo(
                    f"Compliance WARN — listing {r['listing_id']} ({title_short}): {warn_details}",
                    added_by="frank", category="frank_can_do",
                )
                todoed += 1

    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    print(f"\n{'DRY RUN — nothing staged. ' if dry_run else ''}"
          f"FAIL={fail_count} (staged {staged} takedowns) WARN={warn_count} "
          f"(todoed {todoed - staged if not dry_run else 0}) PASS={pass_count}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Full-shop Etsy listing compliance sweep")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report only — stage nothing, add no todos")
    args = parser.parse_args()
    results = run_sweep(dry_run=args.dry_run)
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    if fail_count:
        sys.exit(1)
    if warn_count:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
