#!/usr/bin/env python3
"""
Shorten All Listing Titles to ≤140 Characters
==============================================
Etsy's hard platform max for a listing title is 140 characters. (2026-08-10:
this used to enforce a 70-char cap — real competitive research showed every
top-favorited listing in our niches runs 100-140 chars, so the old 70-char
target was dropped. See etsy_api.py's pre_publish_gate() for the evidence.)

Usage:
  python tools/shorten_titles.py --dry-run
  python tools/shorten_titles.py
  python tools/shorten_titles.py --lid 12345
"""
import os, sys, json, time, argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
_env_path = _ROOT / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

MAX_TITLE_LEN = 140


def smart_shorten(title: str, max_len: int = MAX_TITLE_LEN) -> str:
    title = title.strip()
    if len(title) <= max_len:
        return title
    for delim in [' | ', ' - ', ', ']:
        parts = title.split(delim)
        if len(parts) > 1:
            while len(parts) > 1:
                candidate = delim.join(parts)
                if len(candidate) <= max_len:
                    return candidate.rstrip(' |-,')
                parts.pop()
            if len(parts[0]) <= max_len:
                return parts[0].rstrip(' |-,')
    truncated = title[:max_len]
    last_space = truncated.rfind(' ')
    if last_space > max_len * 0.5:
        truncated = truncated[:last_space]
    return truncated.rstrip(' |-,')


def fetch_all_active(client) -> list:
    import urllib.request
    headers = {
        "Authorization": f"Bearer {client.access_token}",
        "x-api-key": f"{client.client_id}:{client.client_secret}",
    }
    listings, offset = [], 0
    while True:
        url = (f"https://openapi.etsy.com/v3/application/shops/{client.shop_id}"
               f"/listings/active?limit=100&offset={offset}")
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"  Fetch error: {e}")
            break
        batch = data.get('results', [])
        listings.extend(batch)
        if len(batch) < 100:
            break
        offset += 100
        time.sleep(0.3)
    return listings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--lid', type=int)
    args = parser.parse_args()

    client = EtsyAPIClient()
    if not client.refresh_access_token():
        print("[shorten-titles] ERROR: Could not refresh OAuth token")
        sys.exit(1)

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Title Length Optimizer")
    print("  Etsy platform max: ≤140 chars")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    if args.lid:
        import urllib.request
        headers = {"Authorization": f"Bearer {client.access_token}",
                   "x-api-key": f"{client.client_id}:{client.client_secret}"}
        url = f"https://openapi.etsy.com/v3/application/listings/{args.lid}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            listings = [json.loads(resp.read())]
    else:
        print("  Fetching all active listings...")
        listings = fetch_all_active(client)
        print(f"  Found {len(listings)} active listings\n")

    too_long = [l for l in listings if len(l.get('title', '')) > MAX_TITLE_LEN]
    ok_count = len(listings) - len(too_long)
    print(f"  Already ≤{MAX_TITLE_LEN}: {ok_count}   Over: {len(too_long)}\n")

    if not too_long:
        print(f"  ✓ All titles are within the {MAX_TITLE_LEN}-character limit.")
        return

    updated, failed = 0, 0
    for lst in too_long:
        lid = lst.get('listing_id')
        old = lst.get('title', '')
        new = smart_shorten(old)
        print(f"  [{lid}] {len(old)} → {len(new)} chars")
        print(f"    OLD: {old}")
        print(f"    NEW: {new}")
        if args.dry_run:
            print(f"    [DRY RUN]")
        else:
            try:
                client.update_listing(lid, {"title": new})
                print(f"    ✓ Updated")
                updated += 1
            except EtsyAPIError as e:
                print(f"    ✗ Failed: {e}")
                failed += 1
            time.sleep(0.5)
        print()

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if args.dry_run:
        print(f"  DRY RUN — {len(too_long)} titles would be shortened")
    else:
        print(f"  Shortened: {updated}   Failed: {failed}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


if __name__ == '__main__':
    main()
