#!/usr/bin/env python3
"""
fix_printify_shipping.py

Keeps all Printify wall art listings on a free ($0) shipping profile.
Printify occasionally re-syncs products and resets the shipping profile back to the
paid Print Clever profile ($19.79), which triggers Etsy's >$6 shipping ranking penalty.

This script detects and auto-heals that drift.

Modes:
  --auto      Check for drift; fix silently if found. Run by daily cron.
  --fix       Force re-apply free shipping to all Printify listings.
  --dry-run   Preview without making changes.
  --status    Print current shipping state for all Printify listings.

Cron (already registered, runs daily at 8am with health_check):
  0 8 * * * cd /home/user/Etsy && python3 tools/fix_printify_shipping.py --auto >> data/pipeline_log.txt 2>&1
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

STATE_FILE = BASE / "data" / "printify_shipping_state.json"

# Listings with any of these substrings in the title are Printify physical prints
PRINTIFY_MARKERS = ["Art Print", "Physical Print", "Wall Art Print", "Kawaii Wall Art"]

# Printify's Print Clever provider profile IDs — listings on these are "paid" (need fixing)
PAID_PROFILE_IDS = {308270926033, 307647217156}  # Standard + Free Standard (before zeroing)


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_check": None, "last_fix": None, "fix_count": 0, "drift_events": []}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def is_printify_listing(listing: dict) -> bool:
    title = listing.get("title", "")
    return any(m in title for m in PRINTIFY_MARKERS)


def find_printify_free_profile(client: EtsyAPIClient) -> int:
    """Return the Printify 'Free Standard: Print Clever' profile ID."""
    profiles = client.get_shipping_profiles()
    for p in profiles:
        name = p.get("title", "")
        if "free standard" in name.lower() and "print clever" in name.lower():
            return int(p["shipping_profile_id"])
    raise SystemExit(
        "Could not find 'Free Standard: Print Clever' shipping profile. "
        "Has Printify been connected to this shop?"
    )


def zero_out_destinations(client: EtsyAPIClient, profile_id: int) -> int:
    """Set all destination costs to $0. Returns count of destinations zeroed."""
    result = client._request(
        "GET", f"shops/{client.shop_id}/shipping-profiles/{profile_id}/destinations"
    )
    dests = result.get("results", [])
    zeroed = 0
    for d in dests:
        if d.get("primary_cost", {}).get("amount", 0) == 0:
            continue
        dest_id = d["shipping_profile_destination_id"]
        client._request(
            "PUT",
            f"shops/{client.shop_id}/shipping-profiles/{profile_id}/destinations/{dest_id}",
            body={"primary_cost": 0.0, "secondary_cost": 0.0},
        )
        zeroed += 1
        time.sleep(0.25)
    return zeroed


def get_drifted_listings(client: EtsyAPIClient, free_pid: int) -> list[dict]:
    """Return Printify listings that have drifted to a non-free shipping profile."""
    all_listings = client.get_shop_listings_all(state="active")
    printify = [l for l in all_listings if is_printify_listing(l)]
    drifted = [l for l in printify if l.get("shipping_profile_id") != free_pid]
    return drifted, printify


def apply_free_shipping(client: EtsyAPIClient, listings: list[dict], free_pid: int) -> tuple[int, int]:
    """Apply free shipping profile to a list of listings. Returns (updated, errors)."""
    updated = 0
    errors = 0
    for listing in listings:
        lid = listing["listing_id"]
        try:
            client.update_listing(lid, {"shipping_profile_id": free_pid})
            updated += 1
            time.sleep(0.4)
        except EtsyAPIError as e:
            print(f"  ✗  [{lid}] {listing['title'][:55]} — {e}")
            errors += 1
            time.sleep(1.0)
    return updated, errors


def cmd_auto(client: EtsyAPIClient) -> None:
    """Daily cron mode: check for drift, fix silently if needed."""
    state = _load_state()
    now = datetime.now(timezone.utc).isoformat()
    state["last_check"] = now

    free_pid = find_printify_free_profile(client)

    # Check if the free profile's destinations have been reset to non-zero
    result = client._request(
        "GET", f"shops/{client.shop_id}/shipping-profiles/{free_pid}/destinations"
    )
    dests = result.get("results", [])
    nonzero = [d for d in dests if d.get("primary_cost", {}).get("amount", 0) != 0]
    if nonzero:
        print(f"[printify-shipping] Profile drift: {len(nonzero)} destinations reset to non-$0. Re-zeroing...")
        zeroed = zero_out_destinations(client, free_pid)
        print(f"[printify-shipping] Re-zeroed {zeroed} destinations on profile {free_pid}")

    # Check for listing drift
    drifted, all_printify = get_drifted_listings(client, free_pid)
    if not drifted:
        print(f"[printify-shipping] OK — all {len(all_printify)} Printify listings on free shipping profile")
        _save_state(state)
        return

    # Drift detected — fix it
    print(f"[printify-shipping] Drift detected: {len(drifted)}/{len(all_printify)} listings reset to paid shipping. Fixing...")
    updated, errors = apply_free_shipping(client, drifted, free_pid)
    print(f"[printify-shipping] Fixed {updated} listings ({errors} errors)")

    state["last_fix"] = now
    state["fix_count"] = state.get("fix_count", 0) + 1
    state.setdefault("drift_events", []).append({
        "timestamp": now,
        "drifted_count": len(drifted),
        "fixed": updated,
        "errors": errors,
        "listings": [{"id": l["listing_id"], "title": l["title"][:60]} for l in drifted],
    })
    # Keep only last 20 drift events
    state["drift_events"] = state["drift_events"][-20:]
    _save_state(state)


def cmd_fix(client: EtsyAPIClient, dry_run: bool = False) -> None:
    """Force re-apply free shipping to all Printify listings."""
    free_pid = find_printify_free_profile(client)
    print(f"Using 'Free Standard: Print Clever' profile: {free_pid}")

    print("Zeroing destination costs...")
    if not dry_run:
        zeroed = zero_out_destinations(client, free_pid)
        print(f"  Zeroed {zeroed} destination(s)")
    else:
        print("  [DRY RUN] would zero destinations")

    print("\nFetching all active listings...")
    all_listings = client.get_shop_listings_all(state="active")
    printify = [l for l in all_listings if is_printify_listing(l)]
    drifted = [l for l in printify if l.get("shipping_profile_id") != free_pid]
    print(f"Found {len(printify)} Printify listings, {len(drifted)} need updating")

    if dry_run:
        for l in drifted:
            print(f"  DRY-RUN  [{l['listing_id']}] {l['title'][:60]}")
        print(f"\nDRY RUN — would update {len(drifted)} listings")
        return

    updated, errors = apply_free_shipping(client, drifted, free_pid)
    skipped = len(printify) - len(drifted)
    print(f"\nResults: {updated} updated, {skipped} already correct, {errors} errors")

    if updated > 0:
        state = _load_state()
        state["last_fix"] = datetime.now(timezone.utc).isoformat()
        state["fix_count"] = state.get("fix_count", 0) + 1
        _save_state(state)
        print("Ranking penalty will lift within 24-48 hours.")


def cmd_status(client: EtsyAPIClient) -> None:
    """Print current shipping state for all Printify listings."""
    free_pid = find_printify_free_profile(client)
    all_listings = client.get_shop_listings_all(state="active")
    printify = [l for l in all_listings if is_printify_listing(l)]
    on_free = [l for l in printify if l.get("shipping_profile_id") == free_pid]
    drifted = [l for l in printify if l.get("shipping_profile_id") != free_pid]

    print(f"Free Standard profile: {free_pid}")
    print(f"Total Printify listings: {len(printify)}")
    print(f"On free shipping:        {len(on_free)} ✓")
    print(f"Drifted to paid:         {len(drifted)}")

    if drifted:
        print("\nDrifted listings:")
        for l in drifted:
            print(f"  [{l['listing_id']}] profile={l.get('shipping_profile_id')} — {l['title'][:55]}")

    state = _load_state()
    if state.get("last_check"):
        print(f"\nLast check:  {state['last_check']}")
    if state.get("last_fix"):
        print(f"Last fix:    {state['last_fix']}")
        print(f"Total fixes: {state.get('fix_count', 0)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor and fix Printify listing shipping")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--auto", action="store_true", help="Check and auto-fix (daily cron)")
    group.add_argument("--fix", action="store_true", help="Force re-apply free shipping to all listings")
    group.add_argument("--dry-run", action="store_true", help="Preview --fix without changes")
    group.add_argument("--status", action="store_true", help="Show current shipping state")
    args = parser.parse_args()

    client = EtsyAPIClient()
    if not client.refresh_access_token():
        print("ERROR: Could not refresh OAuth token. Run python tools/etsy_oauth.py")
        sys.exit(1)

    if args.auto:
        cmd_auto(client)
    elif args.fix:
        cmd_fix(client, dry_run=False)
    elif args.dry_run:
        cmd_fix(client, dry_run=True)
    elif args.status:
        cmd_status(client)


if __name__ == "__main__":
    main()
