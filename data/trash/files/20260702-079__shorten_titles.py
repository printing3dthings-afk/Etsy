#!/usr/bin/env python3
"""
Shorten all active Etsy listing titles to ≤70 characters.

Etsy 2026 algorithm: titles > 70 chars face mobile ranking penalty.
Data: shortened titles saw +34% mobile CTR and +4.2 avg position improvement.

Strategy:
  - Split title on ' | ' separators
  - Keep segments from the front until adding the next would exceed 70 chars
  - Always keep at least the first segment (primary keyword)
  - If first segment alone > 70 chars, trim at last word boundary

Usage:
  python tools/shorten_titles.py --dry-run    # preview only
  python tools/shorten_titles.py               # apply updates
  python tools/shorten_titles.py --lid 12345  # single listing
"""

import os, sys, json, urllib.request, time, argparse
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

MAX_CHARS = 70


def smart_shorten(title: str) -> str:
    """Shorten title to ≤ MAX_CHARS by dropping trailing pipe-segments."""
    if len(title) <= MAX_CHARS:
        return title

    segments = [s.strip() for s in title.split('|')]
    # Always keep segment 0 (primary keyword)
    result = segments[0].strip()
    if len(result) > MAX_CHARS:
        # Trim at last word boundary
        result = result[:MAX_CHARS].rsplit(' ', 1)[0].rstrip(' |')
        return result

    for seg in segments[1:]:
        candidate = result + ' | ' + seg
        if len(candidate) <= MAX_CHARS:
            result = candidate
        else:
            break

    return result.rstrip(' |')


def fetch_active_listings(client) -> list:
    headers = {
        'Authorization': f'Bearer {client.access_token}',
        'x-api-key': f'{client.client_id}:{client.client_secret}',
    }
    listings, offset = [], 0
    while True:
        url = (f'https://openapi.etsy.com/v3/application/shops/{client.shop_id}'
               f'/listings/active?limit=100&offset={offset}')
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        batch = data.get('results', [])
        listings.extend(batch)
        if len(batch) < 100:
            break
        offset += 100
        time.sleep(0.3)
    return listings


def patch_title(client, listing_id: int, new_title: str) -> bool:
    try:
        client.update_listing(listing_id, {'title': new_title})
        return True
    except EtsyAPIError as e:
        if e.status == 429:
            time.sleep(15)
            try:
                client.update_listing(listing_id, {'title': new_title})
                return True
            except EtsyAPIError:
                pass
        print(f'    PATCH failed for {listing_id}: {e}')
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview only')
    parser.add_argument('--lid', type=int, help='Single listing ID')
    args = parser.parse_args()

    client = EtsyAPIClient()
    client.refresh_access_token()

    print('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print('  Title Shortener — Etsy 2026 Algorithm Compliance')
    print('  Target: ≤70 chars per title')
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')

    if args.lid:
        headers = {
            'Authorization': f'Bearer {client.access_token}',
            'x-api-key': f'{client.client_id}:{client.client_secret}',
        }
        url = f'https://openapi.etsy.com/v3/application/listings/{args.lid}'
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            listing = json.loads(resp.read())
        listings = [listing]
    else:
        print('  Fetching all active listings...')
        listings = fetch_active_listings(client)
        print(f'  Found {len(listings)} active listings\n')

    needs_update = []
    already_ok = []

    for lst in listings:
        lid = lst.get('listing_id')
        title = lst.get('title') or ''
        if len(title) <= MAX_CHARS:
            already_ok.append(lid)
        else:
            needs_update.append(lst)

    print(f'  Compliant (≤{MAX_CHARS} chars):  {len(already_ok)} listings')
    print(f'  Needs shortening:        {len(needs_update)} listings\n')

    if not needs_update:
        print('  ✓ All titles already compliant. Nothing to do.')
        return

    updated = failed = 0

    for lst in needs_update:
        lid = lst.get('listing_id')
        old_title = lst.get('title') or ''
        new_title = smart_shorten(old_title)

        if args.dry_run:
            print(f'  [{lid}]')
            print(f'    BEFORE ({len(old_title):3d}): {old_title}')
            print(f'    AFTER  ({len(new_title):3d}): {new_title}')
            print()
        else:
            ok = patch_title(client, lid, new_title)
            if ok:
                print(f'  ✓ [{lid}] ({len(old_title)}→{len(new_title)} chars) {new_title}')
                updated += 1
            else:
                print(f'  ✗ Failed [{lid}]')
                failed += 1
            time.sleep(0.5)

    print(f'\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    if args.dry_run:
        print(f'  DRY RUN — {len(needs_update)} titles would be shortened')
    else:
        print(f'  Updated: {updated}   Failed: {failed}')
        if failed == 0:
            print('  ✓ All titles now compliant with 2026 mobile ranking rules')
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')


if __name__ == '__main__':
    main()
