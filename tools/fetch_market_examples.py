#!/usr/bin/env python3
"""
Fetch market reference images from Etsy for each art category.

For each of the 20 scheduled art categories, searches Etsy for the top 10
listings, downloads the primary listing photo, and saves to:
  data/design_references/{category_id}/

Also saves a manifest.json in each category folder with:
  - listing URL, title, price, shop, image path

Usage:
  python tools/fetch_market_examples.py              # all 20 categories
  python tools/fetch_market_examples.py --cat coastal_ocean   # one category
  python tools/fetch_market_examples.py --refresh    # re-download all (overwrite)
"""

import os, sys, json, time, argparse, re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_ENV_PATH = _ROOT / ".env"

import requests
import urllib3
urllib3.disable_warnings()

# ── Env ───────────────────────────────────────────────────────────────────────
# This script's token-refresh mechanic rewrites .env in place (see refresh_token()
# below), which only makes sense against a real local .env file — hosted deploys
# (Railway) inject env vars directly and have no .env file at all, so this script
# is inherently a sandbox/local-only tool. Still guarded + made path-portable
# (matching the fix applied throughout tools/) rather than hardcoded to one
# specific machine's absolute path.
if not _ENV_PATH.exists():
    print(f"ERROR: {_ENV_PATH} not found — this script reads/rewrites a local .env "
          f"file (Etsy token refresh) and only runs against a real sandbox checkout.")
    sys.exit(1)
env = {}
with open(_ENV_PATH) as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()

session = requests.Session()
session.verify = False
session.headers.update({
    'x-api-key': f"{env['ETSY_CLIENT_ID']}:{env['ETSY_CLIENT_SECRET']}",
    'Authorization': f"Bearer {env['ETSY_ACCESS_TOKEN']}"
})

REFS_DIR = str(_ROOT / "data" / "design_references")
SCHEDULE_PATH = str(_ROOT / "data" / "art_schedule.json")

# ── Per-category search keywords ──────────────────────────────────────────────
# 2-3 targeted phrases per category to surface the best-performing listings

CATEGORY_KEYWORDS = {
    'watercolor_botanical': 'watercolor botanical printable wall art instant download',
    'coastal_ocean':        'coastal ocean printable wall art instant download beach',
    'quote_typography':     'motivational quote printable wall art typography instant download',
    'vintage_botanical':    'vintage botanical herbarium printable wall art instant download',
    'celestial_mystical':   'celestial moon phases printable wall art mystical instant download',
    'landscape_nature':     'landscape nature printable wall art mountains instant download',
    'nursery_woodland':     'woodland nursery printable wall art animal baby room download',
    'abstract_modern':      'abstract modern printable wall art boho neutral instant download',
    'cottagecore_japandi':  'cottagecore japandi printable wall art botanical instant download',
    'kitchen_food':         'kitchen food printable wall art farmhouse instant download',
    'romantic_feminine':    'romantic floral roses printable wall art feminine instant download',
    'wildlife_birds':       'wildlife birds printable wall art watercolor instant download',
    'travel_cultural':      'travel architecture printable wall art city instant download',
    'minimalist_line_art':  'minimalist line art printable wall art instant download boho',
    'watercolor_animals':   'watercolor animal pet printable wall art instant download',
    'botanical_herbs':      'botanical herbs plants printable wall art instant download',
    'retro_midcentury':     'retro mid century modern printable wall art vintage instant download',
    'seasonal_holiday':     'seasonal holiday printable wall art instant download autumn',
    'humor_novelty':        'funny novelty printable wall art humorous instant download',
    'dark_academia':        'dark academia gothic moody printable wall art instant download',
}


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower())[:50].strip('_')


def refresh_token():
    resp = requests.post(
        'https://api.etsy.com/v3/public/oauth/token',
        data={'grant_type': 'refresh_token',
              'client_id': env['ETSY_CLIENT_ID'],
              'refresh_token': env['ETSY_REFRESH_TOKEN']},
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        verify=False
    )
    if resp.status_code == 200:
        new_token = resp.json()['access_token']
        session.headers.update({'Authorization': f'Bearer {new_token}'})
        with open(_ENV_PATH, 'r') as f:
            content = f.read()
        content = content.replace(env['ETSY_ACCESS_TOKEN'], new_token)
        with open(_ENV_PATH, 'w') as f:
            f.write(content)
        env['ETSY_ACCESS_TOKEN'] = new_token
        return True
    return False


def api_get(url, params=None):
    resp = session.get(url, params=params)
    if resp.status_code == 401:
        if refresh_token():
            resp = session.get(url, params=params)
    return resp


def search_listings(keywords, limit=25):
    """Search all of Etsy for active listings matching keywords."""
    resp = api_get(
        'https://api.etsy.com/v3/application/listings/active',
        params={
            'keywords': keywords,
            'limit': limit,
            'sort_on': 'score',
            'sort_order': 'desc'
        }
    )
    if resp.status_code != 200:
        print(f"  Search failed: {resp.status_code} {resp.text[:100]}")
        return []
    return resp.json().get('results', [])


def get_listing_images(listing_id):
    """Fetch all images for a listing, return primary (rank=1) first."""
    resp = api_get(f'https://api.etsy.com/v3/application/listings/{listing_id}/images')
    if resp.status_code != 200:
        return []
    images = resp.json().get('results', [])
    images.sort(key=lambda x: x.get('rank', 99))
    return images


def download_image(url, out_path):
    """Download an image from etsystatic.com."""
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=20, verify=False,
                                headers={'User-Agent': 'Mozilla/5.0'})
            if resp.status_code == 200 and len(resp.content) > 5000:
                with open(out_path, 'wb') as f:
                    f.write(resp.content)
                return True
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
    return False


def process_category(cat_id, cat_label, refresh=False):
    cat_dir = os.path.join(REFS_DIR, cat_id)
    os.makedirs(cat_dir, exist_ok=True)
    manifest_path = os.path.join(cat_dir, 'manifest.json')

    # Load existing manifest if present
    if os.path.exists(manifest_path) and not refresh:
        with open(manifest_path) as f:
            manifest = json.load(f)
        existing = len([e for e in manifest.get('examples', []) if e.get('downloaded')])
        if existing >= 10:
            print(f"  [{cat_id}] Already have {existing} examples — skipping (use --refresh to re-download)")
            return manifest

    manifest = {
        'category_id': cat_id,
        'category_label': cat_label,
        'search_keywords': CATEGORY_KEYWORDS.get(cat_id, ''),
        'examples': []
    }

    keywords = CATEGORY_KEYWORDS.get(cat_id, f'{cat_label} printable wall art instant download')
    print(f"\n{'─'*60}")
    print(f"[{cat_id}] {cat_label}")
    print(f"  Keywords: {keywords}")

    # Search Etsy
    listings = search_listings(keywords, limit=25)
    print(f"  Found {len(listings)} listings")
    time.sleep(0.5)

    downloaded = 0
    skipped = 0

    for listing in listings:
        if downloaded >= 10:
            break

        lid = listing['listing_id']
        title = listing.get('title', 'untitled')
        price_data = listing.get('price', {})
        price = price_data.get('amount', 0) / price_data.get('divisor', 100)
        shop_id = listing.get('shop_id', '')

        # Skip our own shop
        if str(shop_id) == env.get('ETSY_SHOP_ID_NUMERIC', ''):
            skipped += 1
            continue

        # Fetch images
        images = get_listing_images(lid)
        time.sleep(0.3)

        if not images:
            skipped += 1
            continue

        primary_img = images[0]
        img_url = primary_img.get('url_570xN', primary_img.get('url_fullxfull', ''))
        if not img_url:
            skipped += 1
            continue

        # Download
        filename = f"{downloaded+1:02d}_{lid}_{slugify(title[:35])}.jpg"
        out_path = os.path.join(cat_dir, filename)

        if os.path.exists(out_path) and not refresh:
            print(f"  {downloaded+1:02d}. EXISTS  ${price:.2f}  {title[:45]}")
            downloaded += 1
            manifest['examples'].append({
                'rank': downloaded,
                'listing_id': lid,
                'title': title,
                'price': price,
                'shop_id': shop_id,
                'etsy_url': f'https://www.etsy.com/listing/{lid}/',
                'image_url': img_url,
                'local_file': filename,
                'downloaded': True
            })
            continue

        ok = download_image(img_url, out_path)
        if ok:
            kb = os.path.getsize(out_path) // 1024
            print(f"  {downloaded+1:02d}. ✓ {kb:3d}KB  ${price:.2f}  {title[:45]}")
            downloaded += 1
            manifest['examples'].append({
                'rank': downloaded,
                'listing_id': lid,
                'title': title,
                'price': price,
                'shop_id': shop_id,
                'etsy_url': f'https://www.etsy.com/listing/{lid}/',
                'image_url': img_url,
                'local_file': filename,
                'downloaded': True
            })
        else:
            print(f"  ✗ Download failed for listing {lid}")
            skipped += 1

        time.sleep(0.4)

    print(f"  Done: {downloaded} downloaded, {skipped} skipped")

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    return manifest


def generate_index(all_manifests):
    """Generate a summary index HTML for easy visual browsing."""
    index_path = os.path.join(REFS_DIR, 'index.html')

    rows = []
    for m in all_manifests:
        cat_id = m['category_id']
        cat_label = m['category_label']
        examples = m.get('examples', [])
        n = len([e for e in examples if e.get('downloaded')])

        thumbs = ''
        for e in examples[:10]:
            if e.get('downloaded') and e.get('local_file'):
                url = e['etsy_url']
                img = f"{cat_id}/{e['local_file']}"
                title_safe = e['title'][:40].replace('"', '&quot;')
                thumbs += (f'<a href="{url}" target="_blank">'
                           f'<img src="{img}" title="{title_safe} ${e["price"]:.2f}" '
                           f'width="140" height="140" style="object-fit:cover;margin:3px;border-radius:4px;">'
                           f'</a>')

        rows.append(f"""
<div style="margin-bottom:32px;border-bottom:1px solid #ddd;padding-bottom:24px;">
  <h2 style="font-family:sans-serif;font-size:16px;color:#333;margin:0 0 8px 0;">
    {cat_label} <span style="color:#888;font-weight:normal;">({n} examples)</span>
  </h2>
  <div>{thumbs}</div>
</div>""")

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>OnBrandCraftz — Market Reference Examples</title>
  <style>body{{background:#fafaf8;padding:24px;max-width:1400px;margin:0 auto;}}</style>
</head>
<body>
  <h1 style="font-family:sans-serif;font-size:22px;color:#222;">
    Market Reference Examples — OnBrandCraftz
    <span style="font-size:13px;color:#888;font-weight:normal;display:block;margin-top:4px;">
      {len(all_manifests)} categories · click any image to view on Etsy
    </span>
  </h1>
  {''.join(rows)}
</body>
</html>"""

    with open(index_path, 'w') as f:
        f.write(html)
    print(f"\nIndex saved: {index_path}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cat',     help='Process one category by ID only')
    parser.add_argument('--refresh', action='store_true', help='Re-download existing images')
    args = parser.parse_args()

    os.makedirs(REFS_DIR, exist_ok=True)

    with open(SCHEDULE_PATH) as f:
        schedule = json.load(f)
    categories = schedule['categories']

    if args.cat:
        cats = [c for c in categories if c['id'] == args.cat]
        if not cats:
            print(f"Category '{args.cat}' not found. Valid IDs:")
            for c in categories:
                print(f"  {c['id']}")
            return
    else:
        cats = categories

    all_manifests = []
    for cat in cats:
        m = process_category(cat['id'], cat['label'], refresh=args.refresh)
        if m:
            all_manifests.append(m)
        time.sleep(1)  # polite pause between categories

    # Load any existing manifests not in current run
    if not args.cat:
        generate_index(all_manifests)
        total = sum(len([e for e in m.get('examples', []) if e.get('downloaded')])
                    for m in all_manifests)
        print(f"\n{'='*60}")
        print(f"Complete: {total} reference images across {len(all_manifests)} categories")
        print(f"Browse: data/design_references/index.html")
        print(f"{'='*60}")


if __name__ == '__main__':
    main()
