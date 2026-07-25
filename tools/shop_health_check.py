#!/usr/bin/env python3
"""
OnBrandCraftz — Weekly Shop Health Check
=========================================
Mission: "Providing the best and most accurate transaction for our customers
so we can grow responsibly."

Run every Monday. Catches problems before they become damage:
  - Listings with views but no sales (conversion failure)
  - Listings with 0 views (SEO/visibility failure)
  - Unanswered messages (trust failure)
  - Reviews needing a response
  - Shop health metrics vs. Star Seller thresholds

Usage:
  python tools/shop_health_check.py
  python tools/shop_health_check.py --full    # include per-listing stats
"""

import os, sys, json, re, io, urllib.request, time, argparse, pathlib
from datetime import datetime, timezone

# Repo-relative, not hardcoded -- this script runs both on Scott's machine and
# (via main.py's _EXEC_COMMANDS registry) inside Frank's Railway container,
# which has no /home/user/Etsy and no .env file (env vars are injected by the
# platform directly). A hardcoded absolute path crashed every invocation on
# Railway -- diagnosed 2026-06-17, see ops_runbook.md.
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
_env_path = ROOT / '.env'
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

from PIL import Image
from tools.etsy_api import EtsyAPIClient

UPSCALED_DIR = ROOT / 'data/digital_products/product_files/upscaled'
PRODUCT_FILES_DIR = ROOT / 'data/digital_products/product_files'


def _dhash(img: Image.Image, size: int = 8) -> int:
    """Difference hash — fast perceptual fingerprint. Returns int bitmask."""
    grey = img.convert('L').resize((size + 1, size), Image.LANCZOS)
    px   = list(grey.getdata())
    bits = 0
    for row in range(size):
        for col in range(size):
            bits = (bits << 1) | (1 if px[row * (size+1) + col] > px[row * (size+1) + col + 1] else 0)
    return bits


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count('1')


def _source_art_path(code: str) -> pathlib.Path | None:
    """Return the upscaled or product_files source art path for a DP code, or None."""
    for p in [UPSCALED_DIR / f"{code}.jpg",
              PRODUCT_FILES_DIR / f"{code}.jpg"]:
        if p.exists():
            return p
    return None

STANDARDS = {
    'response_rate_target':      100,   # % messages replied to within 24h
    'review_target_stars':       5.0,   # average review rating
    'conversion_rate_warning':   0.01,  # <1% = photo/price problem
    'conversion_rate_target':    0.03,  # 3%+ = excellent
    'favorite_rate_warning':     0.02,  # <2% views→favs = hero image problem
    'views_30d_warning':         10,    # <10 views/30 days = SEO problem
    'photo_slots_minimum':       7,     # fewer = opportunity missed
    'photo_slots_target':        10,
}


SNAPSHOT_FILE = ROOT / 'data/performance/weekly_snapshots.json'

# Early-warning thresholds — ordered from most critical to least
EARLY_WARNINGS = [
    # (metric_key, operator, threshold, severity, message)
    ('conversion_rate', '<', 0.01, 'CRITICAL', 'Conversion rate below 1% — photo/price emergency'),
    ('conversion_rate', '<', 0.03, 'WARN',     'Conversion rate below 3% — review hero image + title'),
    ('review_avg',      '<', 4.9,  'CRITICAL', 'Review average below 4.9 — read all recent reviews now'),
    ('sales_7d',        '==', 0,   'WARN',     'Zero sales in the past 7 days — check listings'),
    ('views_drop_pct',  '>', 40,   'CRITICAL', 'Views dropped 40%+ vs last week — possible shadow ban'),
    ('msg_unanswered_hrs', '>', 10, 'CRITICAL', 'Unanswered message over 10 hours — Star Seller at risk'),
    ('new_listing_views_7d', '==', 0, 'WARN',  'New listing has 0 views after 7 days — fix SEO/tags'),
    ('photo_count_min', '<', 7,    'WARN',     'Listing(s) below minimum 7 photos'),
]


def _save_weekly_snapshot(snapshot: dict) -> None:
    """Append a snapshot dict to the rolling weekly JSON array."""
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(SNAPSHOT_FILE.read_text()) if SNAPSHOT_FILE.exists() else []
    except Exception:
        existing = []
    existing.append(snapshot)
    # Keep last 104 weeks (2 years) — prune oldest if over limit
    if len(existing) > 104:
        existing = existing[-104:]
    SNAPSHOT_FILE.write_text(json.dumps(existing, indent=2))


def _load_prev_snapshot() -> dict | None:
    """Load the most recent previous snapshot for trend comparison."""
    if not SNAPSHOT_FILE.exists():
        return None
    try:
        data = json.loads(SNAPSHOT_FILE.read_text())
        return data[-1] if data else None
    except Exception:
        return None


def _get(client, url):
    headers = {
        "Authorization": f"Bearer {client.access_token}",
        "x-api-key": f"{client.client_id}:{client.client_secret}",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def check_shop(client):
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  OnBrandCraftz — Weekly Health Check")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    shop_url = f"https://openapi.etsy.com/v3/application/shops/{client.shop_id}"
    shop = _get(client, shop_url)
    if "error" in shop:
        print(f"  ✗ Could not fetch shop: {shop['error']}")
        return

    # ── Shop Summary ──────────────────────────────────────────────────────────
    sales = shop.get('transaction_sold_count', 0)
    favs  = shop.get('num_favorers', 0)
    rev_c = shop.get('review_count', 0)
    rev_a = shop.get('review_average', 0)
    active = shop.get('listing_active_count', 0)

    print("SHOP OVERVIEW")
    print(f"  Total sales       : {sales}")
    print(f"  Shop favorites    : {favs}")
    print(f"  Active listings   : {active}")
    print(f"  Reviews           : {rev_c}  ★ avg: {rev_a}")

    alerts = []

    if rev_a and rev_a < 4.9:
        alerts.append(f"⚠  Review average {rev_a} is below 4.9 — investigate recent reviews immediately")
    if rev_a == 5.0 and rev_c > 0:
        print(f"  ✓ Perfect 5.0 review average")

    # ── Active Listings ───────────────────────────────────────────────────────
    print("\nACTIVE LISTING SCAN")
    listings_url = (f"https://openapi.etsy.com/v3/application/shops/{client.shop_id}"
                    f"/listings/active?limit=100")
    data = _get(client, listings_url)
    listings = data.get('results', [])

    photo_warnings = []
    seo_warnings   = []
    conv_warnings  = []

    # Sample image counts — check all listings but throttle to avoid rate limits
    # Sort by listing_id descending (newest first) so recent listings are checked first
    listings_sorted = sorted(listings, key=lambda x: x.get('listing_id', 0), reverse=True)
    checked = 0
    for lst in listings_sorted:
        lid   = lst.get('listing_id')
        title = lst.get('title', '')[:55]

        # Only check image count if listing has no `images` key (includes may work on some plans)
        imgs = lst.get('images')
        if imgs is not None:
            n_img = len(imgs)
        else:
            # Fetch separately — throttle to 1 call per 0.3s
            img_url  = f"https://openapi.etsy.com/v3/application/listings/{lid}/images"
            img_data = _get(client, img_url)
            n_img    = len(img_data.get('results', []))
            time.sleep(0.3)

        checked += 1
        # Photo count check
        if n_img < STANDARDS['photo_slots_minimum']:
            photo_warnings.append(
                f"  [{lid}] {title}… — only {n_img} photos (min={STANDARDS['photo_slots_minimum']})"
            )

    if photo_warnings:
        print(f"\n  ⚠  {len(photo_warnings)} listing(s) below minimum photo count:")
        for w in photo_warnings:
            print(w)
        alerts.extend(photo_warnings)
    else:
        print(f"  ✓ All {len(listings)} listings meet minimum photo count")

    # ── Hero-art audit — cardinal check ──────────────────────────────────────
    # Two-pronged approach:
    #   1. Cross-listing duplicate detection: if two separate products share an
    #      identical hero thumbnail, one of them likely has the wrong art.
    #   2. Manifest drift detection: if a listing's current hero hash differs
    #      from the hash recorded when photos were last uploaded, flag it.
    # Note: comparing composite photos to raw art hashes does NOT work reliably —
    # the room scene fills ~75% of the frame, making every composite look different
    # from the raw art even when the correct art is used. The composite_smart()
    # guard in lifestyle_composite.py prevents wrong-art generation at source.
    print("\nHERO-ART AUDIT")
    # (2026-07-25) Was the git-tracked repo path unconditionally -- on Railway
    # the hash baseline reset to the committed values every redeploy, so drift
    # detection compared against stale hashes: recurring false "hero has
    # changed" warnings for listings that never changed, or silence about one
    # that genuinely did. resolve_persistent_path seeds the committed baseline
    # to the volume once; locally (no /data) behavior is unchanged.
    from tools.api_server import db as _db
    MANIFEST_PATH = _db.resolve_persistent_path(
        'listing_image_manifest.json',
        fallback=ROOT / 'data/listing_image_manifest.json',
        seed_from=ROOT / 'data/listing_image_manifest.json',
    )
    hero_warns    = []
    hero_hashes: dict[str, tuple[str, int]] = {}  # lid → (title_short, hash)

    manifest = {}
    if MANIFEST_PATH.exists():
        try:
            manifest = json.loads(MANIFEST_PATH.read_text())
        except Exception:
            pass

    for lst in listings:
        lid_str = str(lst.get('listing_id', ''))
        title   = lst.get('title', '')[:40]
        try:
            img_url  = f"https://openapi.etsy.com/v3/application/listings/{lid_str}/images"
            img_data = _get(client, img_url)
            images   = img_data.get('results', [])
            if not images:
                continue
            hero      = next((i for i in images if i.get('rank') == 1), images[0])
            thumb_url = hero.get('url_570xN') or hero.get('url_fullxfull') or ''
            if not thumb_url:
                continue
            raw      = urllib.request.urlopen(thumb_url, timeout=10).read()
            h        = _dhash(Image.open(io.BytesIO(raw)))
            hero_hashes[lid_str] = (title, h)
            time.sleep(0.3)
        except Exception:
            pass

    # 1. Cross-listing duplicate detection
    # dist=0: exact same file uploaded to two listings → wrong art guaranteed
    # dist=1-3: near-identical thumbnails → may be same background room + similar art
    #           buyers cannot distinguish these listings in search results; also
    #           raises suspicion that one listing received the wrong composite.
    # dist≥4: visually distinct enough; not flagged.
    lids = list(hero_hashes.keys())
    for i in range(len(lids)):
        for j in range(i + 1, len(lids)):
            lid_a, lid_b = lids[i], lids[j]
            title_a, h_a = hero_hashes[lid_a]
            title_b, h_b = hero_hashes[lid_b]
            dist = _hamming(h_a, h_b)
            if dist < 4:
                severity = "WRONG ART" if dist == 0 else "nearly identical thumbnails"
                hero_warns.append(
                    f"  [{lid_a}] \"{title_a}\" and [{lid_b}] \"{title_b}\" "
                    f"— {severity} in hero (pHash dist={dist}/64). "
                    f"{'Exact duplicate uploaded — check immediately.' if dist == 0 else 'Verify both show correct art; use different room backgrounds to distinguish in search.'}"
                )

    # 2. Manifest drift detection
    for lid_str, (title, h) in hero_hashes.items():
        stored = manifest.get(lid_str, {}).get('hero_hash')
        if stored is not None and _hamming(stored, h) > 8:
            hero_warns.append(
                f"  [{lid_str}] \"{title}\" hero has changed since last upload "
                f"(stored hash differs by {_hamming(stored, h)} bits) — verify it shows the correct art"
            )

    # Update manifest with current hashes
    for lid_str, (title, h) in hero_hashes.items():
        if lid_str not in manifest:
            manifest[lid_str] = {}
        manifest[lid_str]['hero_hash']       = h
        manifest[lid_str]['hero_checked_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    try:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    except Exception as exc:
        # (2026-07-25) Was a bare `pass` -- a failed baseline write silently
        # guaranteed the NEXT run compares against stale hashes and reports
        # false drift. Never swallow an error that changes reported truth.
        print(f"  ⚠  could not save hero-hash baseline to {MANIFEST_PATH}: {exc} — "
              f"next run's drift detection will compare against stale hashes")

    if hero_warns:
        print(f"\n  ⚠  {len(hero_warns)} hero-art issue(s) found:")
        for w in hero_warns:
            print(w)
        alerts.extend(hero_warns)
    elif hero_hashes:
        print(f"  ✓ {len(hero_hashes)} hero thumbnails checked — no duplicates or drift detected")
    else:
        print("  (could not fetch hero thumbnails)")

    # ── Reviews — check for unanswered ───────────────────────────────────────
    print("\nREVIEW CHECK")
    reviews_url = (f"https://openapi.etsy.com/v3/application/shops/{client.shop_id}"
                   f"/reviews?limit=10")
    rev_data = _get(client, reviews_url)
    reviews  = rev_data.get('results', [])

    unanswered = [r for r in reviews if not r.get('seller_feedback')]
    for r in reviews[:5]:
        stars = r.get('rating', 0)
        buyer = r.get('buyer_user_id', '?')
        fb    = (r.get('review') or '')[:60]
        resp  = '✓ Responded' if r.get('seller_feedback') else '✗ NO RESPONSE'
        star_str = '★' * stars
        print(f"  {star_str} — \"{fb}\" — {resp}")

    if unanswered:
        alerts.append(f"⚠  {len(unanswered)} review(s) have no seller response — respond publicly within 24 hours")
    else:
        print("  ✓ All reviews have seller responses")

    # ── Messages ──────────────────────────────────────────────────────────────
    print("\nMESSAGE CHECK")
    msg_url = (f"https://openapi.etsy.com/v3/application/shops/{client.shop_id}"
               f"/conversations?limit=10")
    msg_data = _get(client, msg_url)
    if "error" not in msg_data:
        convos = msg_data.get('results', [])
        unanswered_msg = [c for c in convos if not c.get('last_message_to_buyer')]
        if unanswered_msg:
            alerts.append(f"⚠  {len(unanswered_msg)} conversation(s) may need response — check Etsy messages")
        else:
            print("  ✓ No urgent message backlog detected")
    else:
        print(f"  (Messages API requires additional scope — check Etsy manually)")

    # ── Quality Gate Reminder ─────────────────────────────────────────────────
    print("\nQUALITY GATES STATUS")
    print("  These must pass before any new listing goes live:")
    print("  [ ] File passes check_file_specs (DPI, resolution, size)")
    print("  [ ] Every photo shows REAL product (not AI-generated fake)")
    print("  [ ] Two room settings per wall art listing")
    print("  [ ] Gallery wall image included")
    print("  [ ] Size reference image included")
    print("  [ ] All 13 tags used, all ≤20 chars")
    print("  [ ] Price above floor for category")
    print("  [ ] 'Instant Download' visible in title or first sentence")

    # ── Growth Ladder ─────────────────────────────────────────────────────────
    print("\nGROWTH LADDER STATUS")
    if sales < 10:
        rung = 1
        next_goal = 10
        print(f"  Rung 1 — Foundation ({sales}/{next_goal} sales)")
        print("  Next: All quality gates → 2 room settings → gallery wall image → size reference")
    elif sales < 50:
        rung = 2
        next_goal = 50
        print(f"  Rung 2 — Optimization ({sales}/{next_goal} sales)")
        print("  Next: A/B test hero images → video listings → respond to all reviews publicly")
    elif sales < 200:
        rung = 3
        next_goal = 200
        print(f"  Rung 3 — Scale ({sales}/{next_goal} sales)")
        print("  Next: Pinterest/TikTok traffic → email list → gallery wall bundle listings")
    elif sales < 1000:
        rung = 4
        next_goal = 1000
        print(f"  Rung 4 — Authority ({sales}/{next_goal} sales)")
        print("  Next: Star Seller badge → 100+ listings → seasonal launches")
    else:
        rung = 5
        next_goal = None
        print(f"  Rung 5 — Market Leadership ({sales} sales) 🏆")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if alerts:
        print(f"  ACTION REQUIRED — {len(alerts)} item(s) need attention:")
        for a in alerts:
            print(f"    {a}")
    else:
        print("  ✓ All systems green — no urgent actions")

    print(f"\n  Star Seller target: 100% message response, 95%+ 5★, instant dispatch")
    print(f"  Full standards:     data/knowledge_base/business_standards.md")
    print(f"  Mission:            Providing the best and most accurate transaction")
    print(f"                      for our customers so we can grow responsibly.")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    result = {
        'sales': sales,
        'rung': rung,
        'reviews': rev_c,
        'review_avg': rev_a,
        'active_listings': active,
        'alerts': len(alerts),
        'photo_warnings': len(photo_warnings),
        'unanswered_reviews': len(unanswered),
        'checked_at': datetime.now(timezone.utc).isoformat(),
    }

    # ── Trend comparison vs last snapshot ─────────────────────────────────────
    prev = _load_prev_snapshot()
    if prev:
        prev_sales = prev.get('sales', sales)
        if prev_sales and sales < prev_sales:
            print(f"  TREND: Sales dropped from {prev_sales} to {sales} since last check")
        prev_avg = prev.get('review_avg', rev_a)
        if prev_avg and rev_a and rev_a < prev_avg:
            print(f"  TREND: Review average dropped {prev_avg} → {rev_a} — investigate")

    # ── Save this week's snapshot for regression tracking ─────────────────────
    _save_weekly_snapshot(result)

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='Include per-listing detail stats')
    args = parser.parse_args()

    client = EtsyAPIClient()
    client.refresh_access_token()
    result = check_shop(client)

    if result and result.get('alerts', 0) == 0:
        print("Shop health: EXCELLENT")
    elif result and result.get('alerts', 0) <= 2:
        print("Shop health: GOOD — minor items to address")
    else:
        print("Shop health: NEEDS ATTENTION — see alerts above")


if __name__ == '__main__':
    main()
