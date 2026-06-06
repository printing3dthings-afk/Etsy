#!/usr/bin/env python3
"""
reactivate_listings.py
Reactivate deactivated Etsy listings in a controlled batch with rate-limit handling.

Waves:
  --wave 1  PASS + WARN listings, excluding wrong-source-file and duplicate holds
  --wave 2  The 8 wrong-source-file listings (run AFTER fix_wrong_source_files.py succeeds)
  --ids     Comma-separated listing IDs (custom set)
  --preview Show what would be reactivated without making any API calls

Usage:
    python tools/reactivate_listings.py --preview
    python tools/reactivate_listings.py --wave 1
    python tools/reactivate_listings.py --wave 2
    python tools/reactivate_listings.py --ids 4509213667,4509218860
"""

import argparse
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
from tools.etsy_api import EtsyAPIClient

# ---------------------------------------------------------------------------
# Wave definitions
# ---------------------------------------------------------------------------

# Wave 1: PASS listings (29) — clean, no issues
PASS_LISTINGS = [
    4509213667, 4509218860, 4512188970, 4512301880, 4512770031,
    4512772452, 4512772539, 4512774863, 4512776173, 4512784817,
    4512784922, 4513713044, 4513713106, 4513713142, 4514130045,
    4514134583, 4514136783, 4514392281, 4514536935, 4514777212,
    4515672496, 4515672588, 4515672972, 4515673064, 4515674042,
    4515674144, 4515674594, 4515676185, 4515676301,
]

# Wave 1: WARN listings (66) — warnings fixed (AI disclosure, keywords)
# Excludes the 8 wrong-source-file listings (handled in wave 2)
WARN_LISTINGS = [
    4509179201, 4509184962, 4509184968, 4509213345, 4509213533,
    4509214051, 4509214237, 4509214803, 4509215145, 4509218152,
    4509219594, 4509219904, 4509259354, 4509593623, 4509596441,
    4509596607, 4509597067, 4509597473, 4509598342, 4509599020,
    4509599208, 4509600086, 4509600276, 4509601324, 4509601462,
    4512254015, 4512254027, 4512254035, 4512255508, 4512255514,
    4512255536, 4512747600, 4512750191, 4512753302, 4512755568,
    4512756952, 4512758123, 4512758458, 4512760671, 4512760918,
    4512763302, 4512768858, 4512780869, 4512783077, 4513713514,
    4513713712, 4513713805, 4513713922, 4513713936, 4513713945,
    4513713962, 4513713984, 4513714013, 4513714191, 4514130357,
    4514134895, 4514137271, 4514393029, 4514537345, 4514778084,
    4515668698, 4515669140, 4515669246, 4515669370, 4515669596,
    4515670946,
]

# Wave 1 hold-outs: wrong source files — reactivate ONLY after fix_wrong_source_files.py
WRONG_SOURCE_FILE_LISTINGS = [
    4509193237,  # DP1059 Pampas Grass
    4509198434,  # DP1060 Boho Wildflower
    4509198446,  # DP1061 Eucalyptus Branch
    4509214477,  # DP1062 Funny Dog (customer complaint)
    4509258700,  # DP1063 Orange Floral
    4509600086,  # DP1064 Tropical Botanical
    4512768858,  # DP1067 Cherry Blossom
    4513713936,  # DP1078 Hummingbird
]

# DO NOT REACTIVATE — duplicate 4515xxx listings that should be closed instead
# (These are covered by FAIL listings starting with 4515xxx)
DUPLICATE_CLOSE_ONLY = [
    4515671216, 4515671336, 4515671458, 4515671558, 4515671764,
    4515671951, 4515672065, 4515672204, 4515672331, 4515672435,
    4515672499, 4515672895, 4515673828, 4515675145, 4515675373,
    4515675481, 4515675583, 4515675813, 4515675887, 4515678198,
    4515678344, 4515682013,
]

# Listings failing art-in-photos that need manual photo review before reactivating
FAIL_NEEDS_REVIEW = [
    4509184958,  # DP1027 — tag count + art fail
    4509258172,  # DP1012 — art_in_photos fail
    4509593487,  # DP1032 — art_in_photos fail
    4509593697,  # DP1034 — art_in_photos fail
    4509596017,  # DP1036 — art_in_photos fail
    4509597559,  # DP1037 — art_in_photos fail
    4509598660,  # art_in_photos fail
    4509598784,  # art_in_photos fail
]

WAVE1_IDS = sorted(set(PASS_LISTINGS + WARN_LISTINGS) - set(WRONG_SOURCE_FILE_LISTINGS))
WAVE2_IDS = WRONG_SOURCE_FILE_LISTINGS

# Delay between API calls (seconds) — stay well under per-second limit
INTER_CALL_DELAY = 0.5


def reactivate_listing(api: "EtsyAPIClient", lid: int, preview: bool) -> str:
    """Attempt to set listing state to active. Returns status string."""
    if preview:
        return "preview"
    try:
        api._request(
            "PATCH",
            f"shops/{api.shop_id}/listings/{lid}",
            json={"state": "active"},
        )
        return "ok"
    except Exception as e:
        err = str(e)
        if "429" in err:
            return "rate_limited"
        if "not editable" in err.lower() or "403" in err:
            return f"error: {err[:80]}"
        return f"error: {err[:80]}"


def run(ids: list[int], preview: bool, label: str):
    api = EtsyAPIClient()

    ok = 0
    skipped = 0
    rate_limited = 0
    errors = []

    print(f"\n{'PREVIEW' if preview else 'APPLY'} — {label} ({len(ids)} listings)\n")

    for i, lid in enumerate(ids, 1):
        status = reactivate_listing(api, lid, preview)

        if status == "preview":
            print(f"  [{i:3d}/{len(ids)}] {lid} — would reactivate")
            skipped += 1
        elif status == "ok":
            print(f"  [{i:3d}/{len(ids)}] {lid} ✓ reactivated")
            ok += 1
        elif status == "rate_limited":
            print(f"  [{i:3d}/{len(ids)}] {lid} ✗ rate limited — stopping")
            rate_limited += 1
            break
        else:
            print(f"  [{i:3d}/{len(ids)}] {lid} ✗ {status}")
            errors.append((lid, status))

        if not preview:
            time.sleep(INTER_CALL_DELAY)

    print(f"\n{'=' * 55}")
    if preview:
        print(f"Preview complete: {skipped} listings would be reactivated")
    else:
        print(f"Done: {ok} reactivated, {rate_limited} rate-limited, {len(errors)} errors")
    if errors:
        print("Errors:")
        for lid, err in errors:
            print(f"  {lid}: {err}")
    if rate_limited:
        print("Rate limit hit — re-run after the 24h window resets (~02:54 AM tomorrow)")
    print("=" * 55)

    return ok, errors, rate_limited


def main():
    parser = argparse.ArgumentParser(description="Reactivate deactivated Etsy listings")
    parser.add_argument("--wave", type=int, choices=[1, 2], help="Run a predefined wave")
    parser.add_argument("--ids", type=str, help="Comma-separated listing IDs")
    parser.add_argument("--preview", action="store_true", help="Dry run — no API writes")
    args = parser.parse_args()

    if args.ids:
        ids = [int(x.strip()) for x in args.ids.split(",")]
        label = "custom set"
    elif args.wave == 1:
        ids = WAVE1_IDS
        label = "Wave 1 (PASS + WARN, excluding wrong-source-file listings)"
    elif args.wave == 2:
        ids = WAVE2_IDS
        label = "Wave 2 (wrong-source-file listings — run AFTER fix_wrong_source_files.py)"
    else:
        parser.print_help()
        print("\nNote: listings excluded from all waves (require separate action):")
        print(f"  Wrong source files (Wave 2): {len(WRONG_SOURCE_FILE_LISTINGS)} listings")
        print(f"  Duplicates to close:         {len(DUPLICATE_CLOSE_ONLY)} listings")
        print(f"  Failing art review:          {len(FAIL_NEEDS_REVIEW)} listings")
        sys.exit(0)

    run(ids, args.preview, label)


if __name__ == "__main__":
    main()
