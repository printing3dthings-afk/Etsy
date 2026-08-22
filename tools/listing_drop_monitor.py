#!/usr/bin/env python3
"""
listing_drop_monitor.py

Daily monitor for two silent failure modes:

1. LISTING DISAPPEARANCE — detects when Etsy removes or deactivates listings
   (policy flags, trademark violations, or algorithm action). Compares today's
   active listing IDs against yesterday's baseline and alerts on any drops.

2. PRICE FLOOR VIOLATIONS — detects if any listing price has drifted below the
   product's defined minimum (accidental edits, Etsy sale discounts left on, etc.).

Both checks write to data/listing_drop_state.json.
Any issues are printed with the [listing-drop] prefix so they appear in pipeline_log.txt.

Usage:
  python tools/listing_drop_monitor.py           # run both checks
  python tools/listing_drop_monitor.py --status  # show current state without running

Referenced by tools/api_server/main.py's _WEEKLY_MONITOR_SCRIPTS — restored
2026-07-15 after an unrelated declutter pass deleted this file thinking it
was unreferenced. If removing this file again, grep main.py first.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE))

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

STATE_FILE = BASE / "data" / "listing_drop_state.json"

# Price floors — if a listing title contains the key phrase, its price must be >= the floor.
# These match the pricing strategy in CLAUDE.md.
#
# `target` (5th element) enables an upper-bound check too: flag if price drifts more
# than PRICE_TARGET_DRIFT_PCT above it (a "stuck discount" or config-error signal, not
# just below-floor). Only set for products with ONE documented fixed price (planners) —
# left None for categories CLAUDE.md itself prices as a range/tier (SVG bundles 5-design
# vs 10+-design, sticker packs standalone vs bundle, wall art single vs set-of-N, etc.),
# since a real 10+-design SVG bundle at $14.99 would otherwise false-positive against a
# target sized for the 5-design tier. Floor-only stays correct for those; the added
# protection here is deliberately scoped to where "one true price" actually exists.
PRICE_FLOORS: list[tuple[str, float, float | None, str]] = [
    ("Ultimate Digital Life Planner",     13.99, 14.99, "DP1026 — floor $13.99 / target $14.99"),
    ("Student",                            8.99,  9.99, "DP1027 — floor $8.99 / target $9.99"),
    ("Budget",                            11.99, 12.99, "DP1028 — floor $11.99 / target $12.99"),
    ("Fitness",                           11.99, 12.99, "DP1029 — floor $11.99 / target $12.99"),
    # DP1030-1034 — added 2026-07-09 (weakness audit): none are published yet
    # (product_catalog.json etsy_listing_id == ""), so this is monitoring-ready for
    # when they go live rather than catching anything today. Targets match the prices
    # already set in product_catalog.json / the two authored listing drafts.
    ("ADHD",                              11.99, 12.99, "DP1030 — floor $11.99 / target $12.99"),
    ("Undated Life Planner",              11.99, 12.99, "DP1031 — floor $11.99 / target $12.99"),
    ("Dark Mode Planner",                 13.99, 14.99, "DP1032 — floor $13.99 / target $14.99"),
    ("Teacher Planner",                   13.99, 14.99, "DP1033 — floor $13.99 / target $14.99"),
    ("SVG Bundle",                          8.99, None, "SVG bundles — floor $8.99 (tiered $9.99-$14.99, no single target)"),
    ("SVG Cut File",                        8.99, None, "SVG cut files — floor $8.99 (tiered, no single target)"),
    ("Sublimation",                         6.99, None, "Sublimation — floor $6.99 (tiered, no single target)"),
    ("Commercial License",                 11.99, None, "Commercial licenses — floor $11.99 (tiered, no single target)"),
    ("Coloring Page",                        2.99, None, "Coloring pages — floor $2.99 (tiered, no single target)"),
    ("Kawaii Sticker",                       3.99, None, "Sticker packs — floor $3.99 (standalone/bundle tiers, no single target)"),
    ("Wall Art Print",                      17.99, None, "Printify physical prints — floor $17.99 (size tiers, no single target)"),
    ("Art Print",                           17.99, None, "Printify physical prints — floor $17.99 (size tiers, no single target)"),
]

PRICE_TARGET_DRIFT_PCT = 0.10  # flag if price > target * (1 + this)

# Alert if active listing count drops by this many in one day
DROP_ALERT_THRESHOLD = 2


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {
        "last_run": None,
        "baseline_ids": [],
        "baseline_count": 0,
        "baseline_date": None,
        "drop_events": [],
        "price_events": [],
    }


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def check_listing_drop(client: EtsyAPIClient, state: dict) -> tuple[list[str], list[dict]]:
    """Compare today's active listing IDs against baseline. Return list of alert messages."""
    alerts = []
    listings = client.get_shop_listings_all(state="active")
    today_ids = {l["listing_id"] for l in listings}
    today_count = len(today_ids)
    now = datetime.now(timezone.utc).isoformat()

    baseline_ids = set(state.get("baseline_ids", []))
    baseline_count = state.get("baseline_count", 0)

    if not baseline_ids:
        # First run — establish baseline
        state["baseline_ids"] = list(today_ids)
        state["baseline_count"] = today_count
        state["baseline_date"] = now
        print(f"[listing-drop] Baseline established: {today_count} active listings")
        return [], listings

    drop = baseline_count - today_count
    disappeared = sorted(baseline_ids - today_ids)

    if drop >= DROP_ALERT_THRESHOLD or disappeared:
        msg = (
            f"ALERT: Active listing count dropped {baseline_count} → {today_count} "
            f"({drop} listings missing)"
        )
        alerts.append(msg)
        print(f"[listing-drop] {msg}")

        if disappeared:
            # Try to look up titles of disappeared listings
            print(f"[listing-drop] Missing listing IDs: {disappeared}")
            for lid in disappeared[:5]:  # cap to avoid too many API calls
                try:
                    l = client.get_listing(lid)
                    title = l.get("title", "unknown")[:60]
                    state_val = l.get("state", "unknown")
                    print(f"[listing-drop]   [{lid}] state={state_val} — {title}")
                except EtsyAPIError:
                    print(f"[listing-drop]   [{lid}] — not found (may have been removed by Etsy)")
                time.sleep(0.3)

        state.setdefault("drop_events", []).append({
            "timestamp": now,
            "baseline": baseline_count,
            "current": today_count,
            "missing_ids": disappeared[:20],
        })
        state["drop_events"] = state["drop_events"][-20:]

    else:
        # No significant drop — update baseline to today's IDs
        # (handles new listings being added over time)
        if today_count > baseline_count:
            added = today_count - baseline_count
            print(f"[listing-drop] OK — {today_count} listings (+{added} new since baseline)")
        else:
            print(f"[listing-drop] OK — {today_count} active listings (no suspicious drops)")

        # Only refresh baseline when healthy — preserve alert state so drops
        # are re-flagged on every subsequent run until manually resolved.
        state["baseline_ids"] = list(today_ids)
        state["baseline_count"] = today_count
        state["baseline_date"] = now

    return alerts, listings


def check_price_floors(listings: list[dict], state: dict) -> list[str]:
    """Check all listing prices against defined minimums. Return alert messages."""
    alerts = []
    now = datetime.now(timezone.utc).isoformat()

    for listing in listings:
        title = listing.get("title", "")
        price_data = listing.get("price", {})
        # Price comes back as {amount: int, divisor: int} — amount/divisor = dollars
        amount = price_data.get("amount", 0)
        divisor = price_data.get("divisor", 100) or 100
        price = amount / divisor
        lid = listing["listing_id"]

        for keyword, floor, target, label in PRICE_FLOORS:
            if keyword.lower() in title.lower():
                if price < floor:
                    msg = (
                        f"PRICE BELOW FLOOR: [{lid}] ${price:.2f} < ${floor:.2f} floor "
                        f"({label}) — \"{title[:55]}\""
                    )
                    alerts.append(msg)
                    print(f"[listing-drop] {msg}")
                    state.setdefault("price_events", []).append({
                        "timestamp": now,
                        "listing_id": lid,
                        "title": title[:60],
                        "price": price,
                        "floor": floor,
                        "kind": "below_floor",
                    })
                elif target is not None and price > target * (1 + PRICE_TARGET_DRIFT_PCT):
                    msg = (
                        f"PRICE ABOVE TARGET: [{lid}] ${price:.2f} > ${target:.2f} target "
                        f"(+{PRICE_TARGET_DRIFT_PCT:.0%} tolerance) ({label}) — possible stuck "
                        f"discount or config error — \"{title[:55]}\""
                    )
                    alerts.append(msg)
                    print(f"[listing-drop] {msg}")
                    state.setdefault("price_events", []).append({
                        "timestamp": now,
                        "listing_id": lid,
                        "title": title[:60],
                        "price": price,
                        "target": target,
                        "kind": "above_target",
                    })
                break  # only match first applicable floor per listing

    state["price_events"] = state.get("price_events", [])[-50:]

    if not alerts:
        print(f"[listing-drop] Price floors OK — no violations detected")

    return alerts


def cmd_status(state: dict) -> None:
    print(f"Baseline: {state.get('baseline_count', 0)} listings (set {state.get('baseline_date', 'never')})")
    print(f"Last run: {state.get('last_run', 'never')}")
    print(f"Drop events logged: {len(state.get('drop_events', []))}")
    print(f"Price events logged: {len(state.get('price_events', []))}")
    if state.get("drop_events"):
        print("\nRecent drop events:")
        for e in state["drop_events"][-3:]:
            print(f"  {e['timestamp'][:10]}: {e['baseline']} → {e['current']}")
    if state.get("price_events"):
        print("\nRecent price violations:")
        for e in state["price_events"][-5:]:
            print(f"  {e['timestamp'][:10]}: [{e['listing_id']}] ${e['price']:.2f} < ${e['floor']:.2f} — {e['title']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor listing drops and price floors")
    parser.add_argument("--status", action="store_true", help="Show current state without running")
    args = parser.parse_args()

    state = _load_state()

    if args.status:
        cmd_status(state)
        return

    client = EtsyAPIClient()
    if not client.refresh_access_token():
        print("[listing-drop] ERROR: Could not refresh OAuth token")
        sys.exit(1)

    now = datetime.now(timezone.utc).isoformat()
    state["last_run"] = now

    # Run checks
    drop_result = check_listing_drop(client, state)
    # check_listing_drop returns (alerts, listings) after first run
    if isinstance(drop_result, tuple):
        drop_alerts, listings = drop_result
    else:
        drop_alerts, listings = drop_result, []

    if listings:
        check_price_floors(listings, state)

    _save_state(state)


if __name__ == "__main__":
    main()
