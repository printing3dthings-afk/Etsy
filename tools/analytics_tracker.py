#!/usr/bin/env python3
"""
OnBrandCraftz — Analytics Dashboard
=====================================
Pulls live shop stats from Etsy, stores daily snapshots, and shows revenue
trends plus actionable insights. Designed to be run from the Command Center
"View Analytics Dashboard" button.

Data is stored in data/performance/daily_snapshots.json (rolling 365 days).

Usage:
  python tools/analytics_tracker.py              # full dashboard
  python tools/analytics_tracker.py --json       # machine-readable output
  python tools/analytics_tracker.py --days 30    # limit trend window
"""

import os, sys, json, argparse, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
_env_path = ROOT / '.env'
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient

SNAPSHOT_FILE = ROOT / 'data/performance/daily_snapshots.json'
SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)

MONTHLY_TARGET_NET = 5000.0
ETSY_FEE_RATE = 0.25  # blended Etsy fee rate


def _save_snapshot(snapshot: dict) -> None:
    """Append today's snapshot. Keeps last 365 days."""
    try:
        existing = json.loads(SNAPSHOT_FILE.read_text()) if SNAPSHOT_FILE.exists() else []
    except Exception:
        existing = []
    # Deduplicate by date
    today = snapshot.get('date', '')
    existing = [s for s in existing if s.get('date') != today]
    existing.append(snapshot)
    if len(existing) > 365:
        existing = existing[-365:]
    SNAPSHOT_FILE.write_text(json.dumps(existing, indent=2))


def _load_snapshots() -> list:
    if not SNAPSHOT_FILE.exists():
        return []
    try:
        return json.loads(SNAPSHOT_FILE.read_text())
    except Exception:
        return []


def _fetch_shop(client):
    """Fetch shop-level stats."""
    import urllib.request
    url = f"https://openapi.etsy.com/v3/application/shops/{client.shop_id}"
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


def _fetch_listings(client) -> list:
    """Fetch all active listings with pagination."""
    import urllib.request
    headers = {
        "Authorization": f"Bearer {client.access_token}",
        "x-api-key": f"{client.client_id}:{client.client_secret}",
    }
    all_listings = []
    offset = 0
    while True:
        url = (f"https://openapi.etsy.com/v3/application/shops/{client.shop_id}"
               f"/listings/active?limit=100&offset={offset}")
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
        except Exception:
            break
        batch = data.get('results', [])
        all_listings.extend(batch)
        if len(batch) < 100:
            break
        offset += 100
        time.sleep(0.3)
    return all_listings


def run_analytics(days: int = 30, output_json: bool = False) -> dict:
    """Main analytics entry point."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime('%Y-%m-%d')

    client = EtsyAPIClient()
    client.refresh_access_token()

    # ── Fetch live data ──────────────────────────────────────────────────────
    shop = _fetch_shop(client)
    if 'error' in shop:
        print(f"  ✗ Could not fetch shop: {shop['error']}")
        return {}

    listings = _fetch_listings(client)

    # ── Compute metrics ──────────────────────────────────────────────────────
    total_sales = shop.get('transaction_sold_count', 0)
    total_favs = shop.get('num_favorers', 0)
    review_count = shop.get('review_count', 0)
    review_avg = shop.get('review_average', 0)
    active_count = shop.get('listing_active_count', 0)

    total_views = sum(l.get('views', 0) for l in listings)
    total_listing_favs = sum(l.get('num_favorers', 0) for l in listings)

    # Price analysis
    prices = []
    for l in listings:
        p = l.get('price', {})
        if isinstance(p, dict):
            amount = p.get('amount', 0) / max(p.get('divisor', 100), 1)
        else:
            amount = float(p) if p else 0
        if amount > 0:
            prices.append(amount)

    avg_price = sum(prices) / len(prices) if prices else 0
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0

    # Top and bottom performers
    listings_sorted = sorted(listings, key=lambda x: x.get('num_favorers', 0), reverse=True)
    top_5 = listings_sorted[:5]
    bottom_5 = [l for l in listings_sorted if l.get('views', 0) > 0][-5:]

    # ── Save snapshot ────────────────────────────────────────────────────────
    snapshot = {
        'date': today_str,
        'total_sales': total_sales,
        'shop_favorites': total_favs,
        'active_listings': active_count,
        'total_views': total_views,
        'total_listing_favs': total_listing_favs,
        'review_count': review_count,
        'review_avg': review_avg,
        'avg_price': round(avg_price, 2),
    }
    _save_snapshot(snapshot)

    # ── Trend analysis ───────────────────────────────────────────────────────
    all_snapshots = _load_snapshots()
    cutoff = (now - timedelta(days=days)).strftime('%Y-%m-%d')
    trend_window = [s for s in all_snapshots if s.get('date', '') >= cutoff]

    trends = {}
    if len(trend_window) >= 2:
        first = trend_window[0]
        last = trend_window[-1]
        trends['sales_change'] = last.get('total_sales', 0) - first.get('total_sales', 0)
        trends['views_change'] = last.get('total_views', 0) - first.get('total_views', 0)
        trends['favs_change'] = last.get('total_listing_favs', 0) - first.get('total_listing_favs', 0)
        trends['listings_change'] = last.get('active_listings', 0) - first.get('active_listings', 0)
        trends['period_days'] = len(trend_window)

    # ── Action items ─────────────────────────────────────────────────────────
    actions = []

    # Revenue pace
    if total_sales > 0 and avg_price > 0:
        estimated_monthly_gross = (total_sales / max(1, (now - datetime(2025, 1, 1, tzinfo=timezone.utc)).days)) * 30 * avg_price
        estimated_monthly_net = estimated_monthly_gross * (1 - ETSY_FEE_RATE)
        if estimated_monthly_net < MONTHLY_TARGET_NET * 0.5:
            actions.append("🔴 Revenue pace is below 50% of $5K/month target — publish more listings")
        elif estimated_monthly_net < MONTHLY_TARGET_NET:
            actions.append("🟡 Revenue pace is below $5K/month target — continue scaling listings")

    # Listing count
    if active_count < 40:
        actions.append(f"🟡 Only {active_count} active listings — aim for 70+ for sustainable revenue")
    elif active_count < 70:
        actions.append(f"🟢 {active_count} active listings — good progress toward 70 target")

    # Zero-view listings
    zero_views = [l for l in listings if l.get('views', 0) == 0]
    if zero_views:
        actions.append(f"🔴 {len(zero_views)} listings with ZERO views — fix tags/titles immediately")

    # Review average
    if review_avg and review_avg < 4.8:
        actions.append(f"🔴 Review average {review_avg} — investigate recent reviews")

    if not actions:
        actions.append("✓ All metrics look healthy — continue current strategy")

    result = {
        'snapshot': snapshot,
        'trends': trends,
        'top_performers': [
            {'title': l.get('title', '')[:55], 'favorites': l.get('num_favorers', 0),
             'views': l.get('views', 0)}
            for l in top_5
        ],
        'low_performers': [
            {'title': l.get('title', '')[:55], 'favorites': l.get('num_favorers', 0),
             'views': l.get('views', 0)}
            for l in bottom_5
        ],
        'pricing': {'avg': round(avg_price, 2), 'min': round(min_price, 2), 'max': round(max_price, 2)},
        'actions': actions,
        'snapshots_stored': len(all_snapshots),
    }

    if output_json:
        print(json.dumps(result, indent=2))
    else:
        _print_dashboard(result, days)

    return result


def _print_dashboard(data: dict, days: int):
    """Pretty-print the analytics dashboard."""
    snap = data['snapshot']
    trends = data.get('trends', {})

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  OnBrandCraftz — Analytics Dashboard")
    print(f"  {snap['date']}  •  {days}-day trend window")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    print("SHOP OVERVIEW")
    print(f"  Total sales        : {snap['total_sales']}")
    print(f"  Shop favorites     : {snap['shop_favorites']}")
    print(f"  Active listings    : {snap['active_listings']}")
    print(f"  Total views        : {snap['total_views']:,}")
    print(f"  Reviews            : {snap['review_count']}  ★ avg: {snap['review_avg']}")

    print(f"\nPRICING")
    p = data['pricing']
    print(f"  Average price      : ${p['avg']:.2f}")
    print(f"  Price range        : ${p['min']:.2f} – ${p['max']:.2f}")

    if trends:
        print(f"\nTRENDS ({trends.get('period_days', days)} days)")
        _trend = lambda v, label: f"  {label:20s}: {'+' if v >= 0 else ''}{v}"
        print(_trend(trends.get('sales_change', 0), 'Sales change'))
        print(_trend(trends.get('views_change', 0), 'Views change'))
        print(_trend(trends.get('favs_change', 0), 'Favorites change'))
        print(_trend(trends.get('listings_change', 0), 'Listings change'))

    print(f"\nTOP PERFORMERS")
    for i, t in enumerate(data.get('top_performers', []), 1):
        print(f"  {i}. {t['title']}  ({t['favorites']}★, {t['views']:,} views)")

    if data.get('low_performers'):
        print(f"\nNEEDS ATTENTION")
        for t in data.get('low_performers', []):
            if t['views'] < 20:
                print(f"  ⚠ {t['title']}  ({t['views']} views, {t['favorites']}★)")

    print(f"\nACTION ITEMS")
    for a in data.get('actions', []):
        print(f"  {a}")

    print(f"\n  Snapshots stored: {data.get('snapshots_stored', 0)} days of history")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


def main():
    parser = argparse.ArgumentParser(description="OnBrandCraftz Analytics Dashboard")
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--days', type=int, default=30, help='Trend window in days (default: 30)')
    args = parser.parse_args()

    run_analytics(days=args.days, output_json=args.json)


if __name__ == '__main__':
    main()
