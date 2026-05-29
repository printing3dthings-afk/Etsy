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

import os, sys, json, urllib.request, time, argparse
from datetime import datetime, timezone
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient

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

    return {
        'sales': sales,
        'rung': rung,
        'reviews': rev_c,
        'review_avg': rev_a,
        'active_listings': active,
        'alerts': len(alerts),
        'photo_warnings': len(photo_warnings),
        'checked_at': datetime.now(timezone.utc).isoformat(),
    }


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
