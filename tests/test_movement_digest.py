"""
Tests for the Weekly "What Changed" Movement Digest (2026-08-06, idea 5/6
of the "significantly improve Frank" roadmap, second batch).

The rule every test here is really checking: every number (views gained,
favorites gained, orders, revenue) traces back to either Frank's own daily
snapshot history (already collected by _snapshot_loop()) or one real,
date-scoped Etsy receipts fetch -- never a guess, and a listing with too
little snapshot history reports a null delta rather than a misleading 0.

Checks:
  1. _movement_window_delta() -- pure function -- returns (None, None) for
     fewer than 2 rows, else the real first-to-last delta.
  2. _compute_movement_digest(): correctly splits a listing's snapshot
     history into this-week/last-week buckets by date; correctly buckets
     real receipts into this-week/last-week by create_timestamp and sums
     revenue/orders per listing; ranks winners (real revenue delta > 0,
     highest first) and decliners (real revenue delta < 0, lowest first)
     separately, each capped at 5; a zero-delta listing appears in neither
     list; an Etsy order-fetch failure is non-fatal (views/favorites still
     computed).
  3. GET /api/movement-digest caches for 1800s.
  4. get_movement_digest is registered in AGENT_TOOLS and dispatches
     correctly through _execute_agent_tool via asyncio.run(), matching the
     existing deep_research precedent.

Run: python tests/test_movement_digest.py
"""
import asyncio
import os
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_movementdigest_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "movementdigest-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_movement_window_delta_needs_two_rows():
    check(server._movement_window_delta([]) == (None, None), "empty list should be (None, None)")
    check(server._movement_window_delta([{"views": 5, "num_favorers": 1}]) == (None, None),
          "a single row can't produce a real delta")


def test_movement_window_delta_computes_real_first_to_last():
    rows = [{"views": 100, "num_favorers": 5}, {"views": 130, "num_favorers": 8}, {"views": 150, "num_favorers": 9}]
    views_delta, favs_delta = server._movement_window_delta(rows)
    check(views_delta == 50, f"first-to-last views delta (150-100), got: {views_delta}")
    check(favs_delta == 4, f"first-to-last favorites delta (9-5), got: {favs_delta}")


_TODAY = date(2026, 8, 6)
_THIS_WEEK_START = date(2026, 7, 30)
_LAST_WEEK_START = date(2026, 7, 23)

_LISTINGS = {
    "listings": [
        {"listing_id": 111, "title": "Winner Planner"},
        {"listing_id": 222, "title": "Decliner Stickers"},
        {"listing_id": 333, "title": "Flat Listing"},
    ],
}


def _snapshot_rows_for(listing_id, start_date, end_date):
    by_listing = {
        111: [
            {"snapshot_date": "2026-07-23", "views": 100, "num_favorers": 5},
            {"snapshot_date": "2026-07-29", "views": 150, "num_favorers": 8},
            {"snapshot_date": "2026-07-30", "views": 160, "num_favorers": 9},
            {"snapshot_date": "2026-08-05", "views": 220, "num_favorers": 15},
        ],
        222: [
            {"snapshot_date": "2026-07-23", "views": 300, "num_favorers": 20},
            {"snapshot_date": "2026-07-29", "views": 350, "num_favorers": 22},
            {"snapshot_date": "2026-07-30", "views": 355, "num_favorers": 22},
            {"snapshot_date": "2026-08-05", "views": 360, "num_favorers": 23},
        ],
        333: [
            {"snapshot_date": "2026-07-30", "views": 50, "num_favorers": 2},
            {"snapshot_date": "2026-08-05", "views": 55, "num_favorers": 2},
        ],
    }
    return by_listing.get(listing_id, [])


def _epoch(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


def _fake_receipts():
    return {"results": [
        # listing 111: $0 last week, $50 this week -> real winner
        {"create_timestamp": _epoch(2026, 8, 2), "transactions": [
            {"listing_id": 111, "quantity": 1, "price": {"amount": 5000, "divisor": 100}},
        ]},
        # listing 222: $80 last week, $20 this week -> real decliner
        {"create_timestamp": _epoch(2026, 7, 25), "transactions": [
            {"listing_id": 222, "quantity": 2, "price": {"amount": 4000, "divisor": 100}},
        ]},
        {"create_timestamp": _epoch(2026, 8, 3), "transactions": [
            {"listing_id": 222, "quantity": 1, "price": {"amount": 2000, "divisor": 100}},
        ]},
        # listing 333: no orders at all -> flat, zero delta
    ]}


def test_compute_movement_digest_winners_and_decliners():
    with patch.object(server, "_shop_today", return_value=_TODAY), \
         patch.object(server, "_listings_sync", return_value=_LISTINGS), \
         patch.object(server.db, "get_listing_snapshot_history", side_effect=_snapshot_rows_for), \
         patch.object(server, "EtsyAPIClient") as mock_client_cls:
        mock_client_cls.return_value.get_orders.return_value = _fake_receipts()
        result = asyncio.run(server._compute_movement_digest())

    winners = {it["listing_id"]: it for it in result["winners"]}
    decliners = {it["listing_id"]: it for it in result["decliners"]}

    check(111 in winners, f"listing 111 went from $0 to $50 -- should be a real winner: {result}")
    check(winners.get(111, {}).get("revenue_delta") == 50.0, f"got: {winners.get(111)}")
    check(winners.get(111, {}).get("this_week_views") == 60, f"160->220 = +60 real views, got: {winners.get(111)}")
    check(winners.get(111, {}).get("last_week_views") == 50, f"100->150 = +50 real views, got: {winners.get(111)}")

    check(222 in decliners, f"listing 222 went from $80 to $20 -- should be a real decliner: {result}")
    check(decliners.get(222, {}).get("revenue_delta") == -60.0, f"got: {decliners.get(222)}")

    check(333 not in winners and 333 not in decliners,
          f"a listing with zero real revenue delta must appear in neither list, got winners={winners} decliners={decliners}")


def test_compute_movement_digest_caps_at_five_each():
    many_listings = {"listings": [{"listing_id": i, "title": f"Listing {i}"} for i in range(1, 13)]}

    def snapshot_rows(listing_id, start, end):
        return [
            {"snapshot_date": "2026-07-30", "views": 10, "num_favorers": 1},
            {"snapshot_date": "2026-08-05", "views": 10, "num_favorers": 1},
        ]

    def fake_receipts():
        # each listing i gets i*$10 revenue this week, $0 last week -- all winners
        return {"results": [
            {"create_timestamp": _epoch(2026, 8, 2), "transactions": [
                {"listing_id": i, "quantity": 1, "price": {"amount": i * 1000, "divisor": 100}},
            ]} for i in range(1, 13)
        ]}

    with patch.object(server, "_shop_today", return_value=_TODAY), \
         patch.object(server, "_listings_sync", return_value=many_listings), \
         patch.object(server.db, "get_listing_snapshot_history", side_effect=snapshot_rows), \
         patch.object(server, "EtsyAPIClient") as mock_client_cls:
        mock_client_cls.return_value.get_orders.return_value = fake_receipts()
        result = asyncio.run(server._compute_movement_digest())

    check(len(result["winners"]) == 5, f"winners must be capped at 5, got {len(result['winners'])}")
    check(result["winners"][0]["listing_id"] == 12, f"the real biggest winner (listing 12, $120) should be first, got: {result['winners'][0]}")


def test_compute_movement_digest_survives_order_fetch_failure():
    with patch.object(server, "_shop_today", return_value=_TODAY), \
         patch.object(server, "_listings_sync", return_value=_LISTINGS), \
         patch.object(server.db, "get_listing_snapshot_history", side_effect=_snapshot_rows_for), \
         patch.object(server, "EtsyAPIClient") as mock_client_cls:
        mock_client_cls.return_value.get_orders.side_effect = RuntimeError("Etsy is down")
        result = asyncio.run(server._compute_movement_digest())
    check(result["winners"] == [] and result["decliners"] == [],
          f"with no real revenue data, nothing should be ranked (never a guessed winner), got: {result}")


def test_compute_movement_digest_survives_listings_fetch_failure():
    """Regression test for a real bug caught live in Playwright verification
    (2026-08-06): the listings fetch was the one Etsy call in the whole
    function not wrapped in try/except, so a missing OAuth token (or any
    Etsy outage) crashed the endpoint into a raw 500 instead of degrading
    to an honest empty digest like every sibling compute function does."""
    with patch.object(server, "_shop_today", return_value=_TODAY), \
         patch.object(server, "_listings_sync", side_effect=RuntimeError("no Etsy token configured")):
        result = asyncio.run(server._compute_movement_digest())
    check(result["winners"] == [] and result["decliners"] == [],
          f"a listings-fetch failure must degrade to an empty digest, never crash the endpoint: {result}")
    check("week_start" in result and "generated_at" in result, f"the degraded response should still be well-formed: {result}")


def test_get_movement_digest_endpoint_caches():
    fake_result = {"winners": [{"listing_id": 1}], "decliners": []}
    call_count = {"n": 0}

    async def _fake_compute():
        call_count["n"] += 1
        return fake_result

    with patch.object(server, "_compute_movement_digest", _fake_compute):
        with server._cache_lock:
            server._cache.pop("movement_digest", None)
        r1 = asyncio.run(server.get_movement_digest(_token="test"))
        r2 = asyncio.run(server.get_movement_digest(_token="test"))
    check(r1 == fake_result, f"got: {r1}")
    check(r1 == r2, "second call within the 1800s window should return the cached value")
    check(call_count["n"] == 1, f"should only compute once due to caching, got {call_count['n']} calls")


def test_tool_registered_and_dispatches():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("get_movement_digest" in names, "get_movement_digest must be registered in AGENT_TOOLS")
    fake_result = {"winners": [], "decliners": []}

    async def _fake_compute():
        return fake_result

    with patch.object(server, "_compute_movement_digest", _fake_compute):
        result = server._execute_agent_tool("get_movement_digest", {})
    check(result == fake_result, f"got: {result}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("MOVEMENT DIGEST TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("MOVEMENT DIGEST TESTS OK — every winner/decliner traces to real snapshot history and real "
          "date-scoped Etsy receipts, a zero-delta listing is never ranked, and an order-fetch failure "
          "never crashes the digest.")


if __name__ == "__main__":
    run()
