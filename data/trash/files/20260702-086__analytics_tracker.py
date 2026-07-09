"""
Analytics tracker for the OnBrandCraftz Etsy shop.

Pulls live shop stats via the Etsy API, stores timestamped snapshots in
DataStore under the key ``analytics_snapshots``, and exposes helpers for
trend analysis and a text dashboard.

Usage (standalone):
    python tools/analytics_tracker.py
"""
from __future__ import annotations

import os
import sys
import datetime
from typing import Any

# Allow running directly from the repo root (python tools/analytics_tracker.py)
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from dotenv import load_dotenv
load_dotenv()

from tools.etsy_api import EtsyAPIClient, EtsyAPIError
from tools.data_store import DataStore

# Maximum number of snapshots to retain in DataStore.
_MAX_SNAPSHOTS = 30

# Key used to store the snapshot list in DataStore.
_SNAPSHOT_KEY = "analytics_snapshots"


# ── Snapshot collection ───────────────────────────────────────────────────────

def fetch_and_store_snapshot() -> dict:
    """Pull current shop stats from the Etsy API and persist a timestamped snapshot.

    Snapshot schema::

        {
            "ts": "2026-05-26T14:30:00",
            "shop": {
                "listing_active_count": int,
                "digital_listing_count": int,
                "login_name": str,
            },
            "listings": [
                {
                    "listing_id": int,
                    "title": str,
                    "views": int,
                    "num_favorers": int,
                    "quantity": int,
                },
                ...
            ],
        }

    Keeps only the last 30 snapshots (prunes oldest first).

    Returns the snapshot dict that was stored.
    """
    client = EtsyAPIClient()
    store = DataStore()

    # ── Shop-level stats ──────────────────────────────────────────────────────
    shop_raw = client.get_shop()
    shop_data: dict[str, Any] = {
        "listing_active_count": shop_raw.get("listing_active_count", 0),
        "digital_listing_count": shop_raw.get("digital_listing_count", 0),
        "login_name": shop_raw.get("login_name", ""),
    }

    # ── Per-listing stats ─────────────────────────────────────────────────────
    listings_raw = client.get_shop_listings(limit=100, state="active")
    results = listings_raw.get("results", [])

    listings_data: list[dict[str, Any]] = []
    for item in results:
        listing_id = item.get("listing_id")
        if listing_id is None:
            continue

        # Fetch full listing detail for views and num_favorers
        try:
            detail = client.get_listing(listing_id)
        except EtsyAPIError:
            detail = item  # fall back to the summary record on error

        listings_data.append({
            "listing_id": int(listing_id),
            "title": detail.get("title", item.get("title", "")),
            "views": int(detail.get("views", 0)),
            "num_favorers": int(detail.get("num_favorers", 0)),
            "quantity": int(detail.get("quantity", item.get("quantity", 0))),
        })

    # ── Build and store snapshot ───────────────────────────────────────────────
    snapshot: dict[str, Any] = {
        "ts": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "shop": shop_data,
        "listings": listings_data,
    }

    snapshots: list[dict] = store.get(_SNAPSHOT_KEY, default=[])
    snapshots.append(snapshot)

    # Prune to the most recent _MAX_SNAPSHOTS entries
    if len(snapshots) > _MAX_SNAPSHOTS:
        snapshots = snapshots[-_MAX_SNAPSHOTS:]

    store.set(snapshots, _SNAPSHOT_KEY)
    store.save()

    return snapshot


# ── Trend analysis ────────────────────────────────────────────────────────────

def get_trend(listing_id: int | str, metric: str, days: int = 7) -> dict:
    """Compare the latest snapshot value to one taken approximately *days* ago.

    Args:
        listing_id: The Etsy listing ID to inspect.
        metric:     One of ``"views"``, ``"num_favorers"``, or ``"quantity"``.
        days:       How many days back to look for a comparison snapshot.

    Returns a dict with keys:
        - ``listing_id``
        - ``metric``
        - ``latest_value``    — value in the most recent snapshot
        - ``baseline_value``  — value in the comparison snapshot
        - ``delta``           — latest_value - baseline_value
        - ``pct_change``      — percentage change (None when baseline is 0)
        - ``baseline_ts``     — ISO timestamp of the comparison snapshot
        - ``latest_ts``       — ISO timestamp of the most recent snapshot
        - ``error``           — present only when data is insufficient

    """
    store = DataStore()
    snapshots: list[dict] = store.get(_SNAPSHOT_KEY, default=[])

    if not snapshots:
        return {"error": "No snapshots available. Run fetch_and_store_snapshot() first."}

    listing_id = int(listing_id)

    # Latest snapshot
    latest = snapshots[-1]
    latest_listing = _find_listing_in_snapshot(latest, listing_id)
    if latest_listing is None:
        return {"error": f"Listing {listing_id} not found in the latest snapshot."}

    latest_value = latest_listing.get(metric)
    if latest_value is None:
        return {"error": f"Metric '{metric}' not found in snapshot. Valid metrics: views, num_favorers, quantity."}

    # Find a snapshot close to `days` ago
    cutoff = datetime.datetime.fromisoformat(latest["ts"]) - datetime.timedelta(days=days)
    baseline = _nearest_snapshot_before(snapshots[:-1], cutoff)
    if baseline is None:
        return {
            "error": (
                f"No snapshot found that is ~{days} day(s) old. "
                "Collect more snapshots over time to enable trend analysis."
            )
        }

    baseline_listing = _find_listing_in_snapshot(baseline, listing_id)
    if baseline_listing is None:
        return {"error": f"Listing {listing_id} not found in the baseline snapshot ({baseline['ts']})."}

    baseline_value = baseline_listing.get(metric, 0)
    delta = latest_value - baseline_value
    pct_change = round(delta / baseline_value * 100, 2) if baseline_value else None

    return {
        "listing_id": listing_id,
        "metric": metric,
        "latest_value": latest_value,
        "baseline_value": baseline_value,
        "delta": delta,
        "pct_change": pct_change,
        "baseline_ts": baseline["ts"],
        "latest_ts": latest["ts"],
    }


def _find_listing_in_snapshot(snapshot: dict, listing_id: int) -> dict | None:
    for listing in snapshot.get("listings", []):
        if int(listing.get("listing_id", -1)) == listing_id:
            return listing
    return None


def _nearest_snapshot_before(snapshots: list[dict], cutoff: datetime.datetime) -> dict | None:
    """Return the snapshot whose timestamp is nearest to (and not after) *cutoff*.

    If no snapshot is at or before *cutoff*, return the oldest available one
    (best effort when the history window is shorter than requested).
    """
    candidates = []
    for snap in snapshots:
        try:
            ts = datetime.datetime.fromisoformat(snap["ts"])
        except (KeyError, ValueError):
            continue
        candidates.append((ts, snap))

    if not candidates:
        return None

    at_or_before = [(ts, s) for ts, s in candidates if ts <= cutoff]
    if at_or_before:
        # Closest to cutoff from below
        return max(at_or_before, key=lambda x: x[0])[1]

    # All snapshots are newer than cutoff — return the oldest as best effort
    return min(candidates, key=lambda x: x[0])[1]


# ── Shop summary ──────────────────────────────────────────────────────────────

def get_shop_summary() -> dict:
    """Summarise the latest snapshot into high-level shop metrics.

    Returns a dict with:
        - ``snapshot_ts``                 — ISO timestamp of the snapshot used
        - ``total_active_listings``       — number of active listings
        - ``total_favorites_across_shop`` — sum of num_favorers across all listings
        - ``top_5_by_favorites``          — list of {title, num_favorers}
        - ``listings_with_zero_views``    — list of {listing_id, title}
        - ``error``                       — present only when no data is available
    """
    store = DataStore()
    snapshots: list[dict] = store.get(_SNAPSHOT_KEY, default=[])

    if not snapshots:
        return {"error": "No snapshots available. Run fetch_and_store_snapshot() first."}

    latest = snapshots[-1]
    listings = latest.get("listings", [])

    total_favorites = sum(l.get("num_favorers", 0) for l in listings)

    sorted_by_favorites = sorted(listings, key=lambda l: l.get("num_favorers", 0), reverse=True)
    top_5 = [
        {"title": l.get("title", ""), "num_favorers": l.get("num_favorers", 0)}
        for l in sorted_by_favorites[:5]
    ]

    zero_views = [
        {"listing_id": l.get("listing_id"), "title": l.get("title", "")}
        for l in listings
        if l.get("views", 0) == 0
    ]

    return {
        "snapshot_ts": latest.get("ts", ""),
        "total_active_listings": len(listings),
        "total_favorites_across_shop": total_favorites,
        "top_5_by_favorites": top_5,
        "listings_with_zero_views": zero_views,
    }


# ── Text dashboard ────────────────────────────────────────────────────────────

def print_dashboard() -> None:
    """Print a formatted text dashboard to stdout.

    Shows the shop summary and top performers from the most recent snapshot.
    If no snapshot exists yet, prints an instructional message instead.
    """
    store = DataStore()
    snapshots: list[dict] = store.get(_SNAPSHOT_KEY, default=[])

    _hr = "=" * 58

    print(_hr)
    print("  OnBrandCraftz — Analytics Dashboard")
    print(_hr)

    if not snapshots:
        print("\n  No snapshots yet.")
        print("  Run fetch_and_store_snapshot() to collect your first snapshot.\n")
        print(_hr)
        return

    summary = get_shop_summary()
    if "error" in summary:
        print(f"\n  Error: {summary['error']}\n")
        print(_hr)
        return

    latest = snapshots[-1]
    shop = latest.get("shop", {})

    print(f"\n  Snapshot:  {summary['snapshot_ts']}")
    print(f"  Shop:      {shop.get('login_name', 'onbrandcraftz')}")
    print(f"  Snapshots on record: {len(snapshots)} / {_MAX_SNAPSHOTS}")

    print(f"\n  {'─' * 54}")
    print("  SHOP OVERVIEW")
    print(f"  {'─' * 54}")
    print(f"  Active listings         {summary['total_active_listings']:>6}")
    print(f"  Digital listings        {shop.get('digital_listing_count', 0):>6}")
    print(f"  Total shop favorites    {summary['total_favorites_across_shop']:>6}")
    print(f"  Listings with 0 views   {len(summary['listings_with_zero_views']):>6}")

    print(f"\n  {'─' * 54}")
    print("  TOP 5 LISTINGS BY FAVORITES")
    print(f"  {'─' * 54}")
    top_5 = summary["top_5_by_favorites"]
    if top_5:
        for rank, item in enumerate(top_5, start=1):
            title = item["title"]
            # Truncate long titles for display
            display_title = title[:42] + "…" if len(title) > 43 else title
            print(f"  {rank}. {display_title:<44} {item['num_favorers']:>4} ♥")
    else:
        print("  No listings found.")

    zero_views = summary["listings_with_zero_views"]
    if zero_views:
        print(f"\n  {'─' * 54}")
        print("  LISTINGS WITH ZERO VIEWS (need attention)")
        print(f"  {'─' * 54}")
        for item in zero_views:
            title = item.get("title", "")
            display_title = title[:48] + "…" if len(title) > 49 else title
            print(f"  • [{item['listing_id']}] {display_title}")

    # Show 7-day trend summary for each listing
    listings = latest.get("listings", [])
    if len(snapshots) >= 2 and listings:
        print(f"\n  {'─' * 54}")
        print("  7-DAY VIEW TRENDS")
        print(f"  {'─' * 54}")
        any_trend = False
        for listing in sorted(listings, key=lambda l: l.get("views", 0), reverse=True):
            trend = get_trend(listing["listing_id"], "views", days=7)
            if "error" in trend:
                continue
            any_trend = True
            delta = trend["delta"]
            sign = "+" if delta >= 0 else ""
            title = listing.get("title", "")
            display_title = title[:38] + "…" if len(title) > 39 else title
            pct = trend["pct_change"]
            pct_str = f" ({sign}{pct:.1f}%)" if pct is not None else ""
            print(f"  {display_title:<40} {sign}{delta:>4} views{pct_str}")
        if not any_trend:
            print("  Not enough history for 7-day trends yet.")

    print(f"\n{_hr}\n")

    # ── Action Items ──────────────────────────────────────────────────────────
    _print_action_items(summary, latest)


def _print_action_items(summary: dict, latest: dict) -> None:
    """Print prioritized action items based on current shop state."""
    _hr = "=" * 58
    listings = latest.get("listings", [])

    actions = []

    # Check for planners with 0 reviews (proxy: 0 favorites and low views)
    planner_ids = {4509179201, 4509184958, 4509184962, 4509184968}
    zero_review_planners = [
        l for l in listings
        if l.get("listing_id") in planner_ids and l.get("num_favorers", 0) == 0
    ]
    if zero_review_planners:
        actions.append(("🔴 URGENT", f"{len(zero_review_planners)} planners have 0 favorites/reviews — set up post-purchase message in Etsy Settings"))

    # Check for ads-ready listings (5+ favorites = proxy for reviews)
    ads_ready = [l for l in listings if l.get("num_favorers", 0) >= 5]
    if ads_ready:
        for l in ads_ready[:3]:
            actions.append(("🟡 ADS", f"Run $5/day Etsy Ads on: {l['title'][:50]}… ({l['num_favorers']}♥)"))
    else:
        actions.append(("⚪ ADS", "Not yet — wait for 5+ reviews on a listing before starting Etsy Ads"))

    # Zero view listings
    zero_views = summary.get("listings_with_zero_views", [])
    if zero_views:
        actions.append(("🟠 SEO", f"{len(zero_views)} listings getting 0 views — check tags and hero photo"))

    # Star Seller readiness
    total_favs = summary.get("total_favorites_across_shop", 0)
    if total_favs < 5:
        actions.append(("⚪ STAR", f"Star Seller badge needs 5+ orders + 4.8 rating — currently {total_favs} shop favorites"))
    else:
        actions.append(("🟢 STAR", "Star Seller eligible — confirm 95% message response rate in Shop Manager"))

    # Pinterest reminder
    actions.append(("📌 PIN", "Enable Rich Pins: Etsy Shop Manager → Marketing → Pinterest → Enable Rich Pins"))

    # Coupons reminder
    actions.append(("🎁 CPN", "Set up abandoned cart (10% off) + thank-you (15% off) coupons in Shop Manager → Marketing"))

    if actions:
        print(f"\n  {'─' * 54}")
        print("  ACTION ITEMS")
        print(f"  {'─' * 54}")
        for priority, msg in actions:
            print(f"  {priority}: {msg}")

    print(f"\n{_hr}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Fetching live snapshot from Etsy API…")
    try:
        snapshot = fetch_and_store_snapshot()
        listing_count = len(snapshot.get("listings", []))
        print(f"Snapshot captured at {snapshot['ts']} — {listing_count} active listing(s) recorded.\n")
    except EtsyAPIError as exc:
        print(f"Etsy API error: {exc}\n")
        print("Falling back to dashboard from stored snapshots (if any).\n")

    print_dashboard()
