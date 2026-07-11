#!/usr/bin/env python3
"""
close_duplicate_listings.py
Close the 28 duplicate 4515xxx listings that were created as newer versions of
already-live 4509xxx / 4512xxx / 4513xxx originals.

These duplicates:
  - Fail art_in_photos (lifestyle-composite-only photos, no flat preview)
  - Have the same DP code as an existing original listing that passes or warns
  - Should be permanently closed (state=inactive / deleted), not reactivated

The originals (45090xxx-4513xxx range) are the keeper listings.

Usage:
    python tools/close_duplicate_listings.py --preview
    python tools/close_duplicate_listings.py
    python tools/close_duplicate_listings.py --ids 4515668698,4515669140
"""

import argparse
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
from tools.etsy_api import EtsyAPIClient

# 28 duplicate 4515xxx listings — mapped to their DP codes for clarity
# These are the FAIL listings from the integrity check that should be CLOSED
DUPLICATES = {
    4515668698:  "DP1030",
    4515669140:  "DP1031",
    4515669246:  "DP1032",
    4515669370:  "DP1034",
    4515669596:  "DP1035",
    4515670946:  "DP1036",
    4515671216:  "DP1037",
    4515671336:  "DP1038",
    4515671458:  "DP1039",
    4515671558:  "DP1040",
    4515671764:  "DP1041",
    4515671951:  "DP1042",
    4515672065:  "DP1043",
    4515672204:  "DP1044",
    4515672331:  "DP1045",
    4515672435:  "DP1046",
    4515672499:  "DP1047",
    4515672895:  "DP1048",
    4515673828:  "DP1049",
    4515675145:  "DP1050",
    4515675373:  "DP1051",
    4515675481:  "DP1052",
    4515675583:  "DP1053",
    4515675813:  "DP1054",
    4515675887:  "DP1055",
    4515678198:  "DP1056",
    4515678344:  "DP1057",
    4515682013:  "DP1058",
}

INTER_CALL_DELAY = 0.5


def close_listing(api, lid: int, preview: bool) -> str:
    if preview:
        return "preview"
    try:
        # Set state to inactive (Etsy's way of closing/deleting a listing)
        api._request(
            "PATCH",
            f"shops/{api.shop_id}/listings/{lid}",
            json={"state": "inactive"},
        )
        return "ok"
    except Exception as e:
        err = str(e)
        if "429" in err:
            return "rate_limited"
        return f"error: {err[:80]}"


def main():
    parser = argparse.ArgumentParser(description="Close duplicate 4515xxx Etsy listings")
    parser.add_argument("--preview", action="store_true", help="Dry run — no API writes")
    parser.add_argument("--ids", type=str, help="Comma-separated listing IDs (subset)")
    args = parser.parse_args()

    if args.ids:
        custom_ids = [int(x.strip()) for x in args.ids.split(",")]
        targets = {lid: DUPLICATES.get(lid, "unknown") for lid in custom_ids}
    else:
        targets = DUPLICATES

    api = EtsyAPIClient()

    ok = 0
    rate_limited = 0
    errors = []

    print(f"\n{'PREVIEW' if args.preview else 'APPLY'} — closing {len(targets)} duplicate listings\n")

    for i, (lid, dp) in enumerate(sorted(targets.items()), 1):
        status = close_listing(api, lid, args.preview)

        if status == "preview":
            print(f"  [{i:2d}/{len(targets)}] {lid} ({dp}) — would close")
        elif status == "ok":
            print(f"  [{i:2d}/{len(targets)}] {lid} ({dp}) ✓ closed")
            ok += 1
        elif status == "rate_limited":
            print(f"  [{i:2d}/{len(targets)}] {lid} ({dp}) ✗ rate limited — stopping")
            rate_limited += 1
            break
        else:
            print(f"  [{i:2d}/{len(targets)}] {lid} ({dp}) ✗ {status}")
            errors.append((lid, status))

        if not args.preview:
            time.sleep(INTER_CALL_DELAY)

    print(f"\n{'=' * 55}")
    if args.preview:
        print(f"Preview complete: {len(targets)} listings would be closed")
    else:
        print(f"Done: {ok} closed, {rate_limited} rate-limited, {len(errors)} errors")
    if errors:
        print("Errors:")
        for lid, err in errors:
            print(f"  {lid}: {err}")
    if rate_limited:
        print("Rate limit hit — re-run after the 24h window resets (~02:54 AM tomorrow)")
    print("=" * 55)


if __name__ == "__main__":
    main()
