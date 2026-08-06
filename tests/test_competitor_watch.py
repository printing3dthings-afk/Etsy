"""
Tests for the Competitor Price & Listing Drift Watchdog (2026-08-06, idea
4/6 of the "significantly improve Frank" roadmap, second batch).

The rule every test here is really checking: every number surfaced (my
price, competitor average, comparable count) traces back to a real,
live-fetched Etsy search via _get_comparable_listings() -- never a rule-of-
thumb guess -- and the watchdog NEVER calls an Etsy write endpoint itself.
Price changes stay Scott's call regardless of what this finds (Autonomy
Boundaries).

Checks:
  1. _load_competitor_snapshots()/_save_competitor_snapshots() round-trip
     and tolerate a missing file.
  2. _competitor_watch_keywords() prefers a listing's own top-2 tags,
     falling back to a truncated title only when there are no tags.
  3. _competitor_watch_iteration(): skips listings with no price/keywords;
     excludes the shop's own listing_id from the comparable set; skips
     (records nothing) when fewer than _COMPETITOR_MIN_SAMPLE real
     comparables come back; records a real snapshot entry (date/my_price/
     competitor_avg/competitor_count/keywords) when there's enough data;
     never calls any Etsy write method.
  4. _compute_competitor_drift_items(): only reports listings whose real
     gap meets the threshold, with the correct direction, sorted by the
     size of the real gap.
  5. _score_growth_brief_items() folds competitor-drift findings in with
     est_dollar_impact always None (never a fabricated revenue guess) and
     never outranks a real-$ item from another source.
  6. GET /api/competitor-watch caches for 300s.
  7. get_competitor_drift is registered in AGENT_TOOLS and dispatches
     correctly through _execute_agent_tool.

Run: python tests/test_competitor_watch.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_competitorwatch_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "competitorwatch-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fresh_path(prefix: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(prefix=prefix, suffix=".json", delete=False)
    tmp.close()
    path = Path(tmp.name)
    path.unlink()
    return path


def _swap_snapshots_path():
    orig = server._COMPETITOR_SNAPSHOTS_PATH
    path = _fresh_path("competitor_snapshots_")
    server._COMPETITOR_SNAPSHOTS_PATH = path
    return orig, path


def test_load_missing_file_returns_empty_dict():
    orig, path = _swap_snapshots_path()
    try:
        check(server._load_competitor_snapshots() == {}, "missing file should yield an empty dict")
    finally:
        server._COMPETITOR_SNAPSHOTS_PATH = orig
        path.unlink(missing_ok=True)


def test_save_and_reload_round_trips():
    orig, path = _swap_snapshots_path()
    try:
        server._save_competitor_snapshots({"123": [{"date": "2026-08-06", "my_price": 12.99}]})
        reloaded = server._load_competitor_snapshots()
        check(reloaded["123"][0]["my_price"] == 12.99, f"round-trip should preserve data, got: {reloaded}")
    finally:
        server._COMPETITOR_SNAPSHOTS_PATH = orig
        path.unlink(missing_ok=True)


def test_keywords_prefer_top_two_tags():
    kw = server._competitor_watch_keywords({"tags": ["digital planner", "goodnotes planner", "kawaii"], "title": "x"})
    check(kw == "digital planner goodnotes planner", f"should use the first 2 tags, got: {kw!r}")


def test_keywords_fall_back_to_title_when_no_tags():
    kw = server._competitor_watch_keywords({"tags": [], "title": "Kawaii Digital Planner 2026 GoodNotes"})
    check(kw == "Kawaii Digital Planner 2026 GoodNotes", f"got: {kw!r}")


def _fake_listings(*, own_id=111, price=20.0, tags=("digital planner", "goodnotes planner")):
    return {"listings": [{"listing_id": own_id, "title": "My Planner", "price": price, "tags": list(tags)}]}


def test_iteration_skips_listing_with_no_price():
    orig, path = _swap_snapshots_path()
    try:
        with patch.object(server, "_listings_sync", return_value=_fake_listings(price=0)), \
             patch.object(server, "_get_comparable_listings") as mock_comp:
            result = asyncio.run(server._competitor_watch_iteration())
        check(result["skipped"] == 1, f"a zero-price listing should be skipped, got: {result}")
        check(mock_comp.call_count == 0, "must not call the comparable search for a listing with no price")
    finally:
        server._COMPETITOR_SNAPSHOTS_PATH = orig
        path.unlink(missing_ok=True)


def test_iteration_excludes_own_listing_and_needs_min_sample():
    orig, path = _swap_snapshots_path()
    try:
        # 2 real comparables + 1 self-match -- self must be excluded, leaving
        # only 2, below _COMPETITOR_MIN_SAMPLE (3) -- nothing should be recorded.
        fake_result = {"listings": [
            {"listing_id": 111, "price": 20.0},  # this shop's own listing -- must be excluded
            {"listing_id": 222, "price": 18.0},
            {"listing_id": 333, "price": 22.0},
        ]}
        with patch.object(server, "_listings_sync", return_value=_fake_listings()), \
             patch.object(server, "_get_comparable_listings", return_value=fake_result):
            result = asyncio.run(server._competitor_watch_iteration())
        check(result["checked"] == 1, f"got: {result}")
        snapshots = server._load_competitor_snapshots()
        check(snapshots == {}, f"fewer than _COMPETITOR_MIN_SAMPLE real comparables (after excluding self) must record nothing, got: {snapshots}")
    finally:
        server._COMPETITOR_SNAPSHOTS_PATH = orig
        path.unlink(missing_ok=True)


def test_iteration_records_real_snapshot_with_enough_comparables():
    orig, path = _swap_snapshots_path()
    try:
        fake_result = {"listings": [
            {"listing_id": 111, "price": 20.0},  # self -- excluded
            {"listing_id": 222, "price": 18.0},
            {"listing_id": 333, "price": 22.0},
            {"listing_id": 444, "price": 20.0},
        ]}
        with patch.object(server, "_listings_sync", return_value=_fake_listings(price=30.0)), \
             patch.object(server, "_get_comparable_listings", return_value=fake_result), \
             patch.object(server, "EtsyAPIClient") as mock_client_cls:
            result = asyncio.run(server._competitor_watch_iteration())
        check(mock_client_cls.call_count == 0, "must never construct an EtsyAPIClient directly -- only via _get_comparable_listings")
        check(result["flagged"] == 1, f"my_price $30 vs a real $20 average is a 50% gap, well past the 20% threshold: {result}")
        snapshots = server._load_competitor_snapshots()
        entry = snapshots["111"][-1]
        check(entry["my_price"] == 30.0, f"got: {entry}")
        check(entry["competitor_avg"] == 20.0, f"real average of 18/22/20, got: {entry}")
        check(entry["competitor_count"] == 3, f"self-listing must be excluded from the count, got: {entry}")
        check(entry["keywords"] == "digital planner goodnotes planner", f"got: {entry}")
    finally:
        server._COMPETITOR_SNAPSHOTS_PATH = orig
        path.unlink(missing_ok=True)


def test_compute_drift_items_only_reports_above_threshold():
    orig, path = _swap_snapshots_path()
    try:
        server._save_competitor_snapshots({
            "111": [{"date": "2026-08-06", "my_price": 30.0, "competitor_avg": 20.0,
                      "competitor_count": 5, "keywords": "kw a"}],
            "222": [{"date": "2026-08-06", "my_price": 10.0, "competitor_avg": 10.0,
                      "competitor_count": 5, "keywords": "kw b"}],  # no real gap
        })
        items = server._compute_competitor_drift_items()
        check(len(items) == 1, f"only the listing with a real >=20% gap should be reported, got: {items}")
        check(items[0]["listing_id"] == 111, f"got: {items}")
        check(items[0]["direction"] == "above", f"my_price > competitor_avg should be 'above', got: {items[0]}")
        check(items[0]["gap_pct"] == 50.0, f"got: {items[0]}")
    finally:
        server._COMPETITOR_SNAPSHOTS_PATH = orig
        path.unlink(missing_ok=True)


def test_compute_drift_items_below_direction_and_sort_order():
    orig, path = _swap_snapshots_path()
    try:
        server._save_competitor_snapshots({
            "111": [{"date": "2026-08-06", "my_price": 8.0, "competitor_avg": 20.0,
                      "competitor_count": 5, "keywords": "kw a"}],  # -60%, below
            "222": [{"date": "2026-08-06", "my_price": 25.0, "competitor_avg": 20.0,
                      "competitor_count": 5, "keywords": "kw b"}],  # +25%, above, smaller gap
        })
        items = server._compute_competitor_drift_items()
        check(len(items) == 2, f"got: {items}")
        check(items[0]["listing_id"] == 111, f"the bigger real gap (60%) should sort first, got: {items}")
        check(items[0]["direction"] == "below", f"got: {items[0]}")
        check(items[1]["direction"] == "above", f"got: {items[1]}")
    finally:
        server._COMPETITOR_SNAPSHOTS_PATH = orig
        path.unlink(missing_ok=True)


def test_score_growth_brief_folds_in_competitor_drift_never_fabricating_dollars():
    drift_items = [{
        "listing_id": 111, "my_price": 30.0, "competitor_avg": 20.0,
        "competitor_count": 5, "keywords": "kawaii planner", "date": "2026-08-06",
        "gap_pct": 50.0, "direction": "above", "url": "https://www.etsy.com/listing/111",
    }]
    items = server._score_growth_brief_items(
        ads={"used": False}, cogs={"used": False}, star_seller={"status": "on_track"},
        actions_data={"actions": []}, bundle_opps=[], seasonal_entries=[],
        competitor_drift_items=drift_items,
    )
    drift = [i for i in items if i["category"] == "competitor_drift"]
    check(len(drift) == 1, f"expected exactly one competitor_drift item, got: {drift}")
    check(drift[0]["est_dollar_impact"] is None, f"a price gap must never fabricate a dollar figure, got: {drift[0]}")
    check(drift[0]["severity"] == "medium", f"a 50% gap should be medium severity, got: {drift[0]}")
    check("real:" in drift[0]["impact_basis"], f"basis should say this is real comparable data, got: {drift[0]}")


def test_score_growth_brief_real_dollar_item_still_outranks_competitor_drift():
    drift_items = [{
        "listing_id": 111, "my_price": 30.0, "competitor_avg": 20.0,
        "competitor_count": 5, "keywords": "kawaii planner", "date": "2026-08-06",
        "gap_pct": 50.0, "direction": "above", "url": "x",
    }]
    items = server._score_growth_brief_items(
        ads={"used": True, "status": "kill_signal", "week_spend": 42.5, "week_revenue": 0,
             "month_spend": 42.5, "month_revenue": 0, "month_roas": 0.0},
        cogs={"used": False}, star_seller={"status": "on_track"},
        actions_data={"actions": []}, bundle_opps=[], seasonal_entries=[],
        competitor_drift_items=drift_items,
    )
    check(items[0]["category"] == "ads", f"the real-$ ads item must still rank first, got: {items[0]}")


def test_get_competitor_watch_endpoint_caches():
    with patch.object(server, "_compute_competitor_drift_items", return_value=[{"listing_id": 1}]) as mock_compute:
        with server._cache_lock:
            server._cache.pop("competitor_watch", None)
        r1 = asyncio.run(server.get_competitor_watch(_token="test"))
        r2 = asyncio.run(server.get_competitor_watch(_token="test"))
    check(r1 == {"items": [{"listing_id": 1}]}, f"got: {r1}")
    check(r1 == r2, "second call within the 300s window should return the cached value")
    check(mock_compute.call_count == 1, f"should only compute once due to caching, got {mock_compute.call_count} calls")


def test_tool_registered_and_dispatches():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("get_competitor_drift" in names, "get_competitor_drift must be registered in AGENT_TOOLS")
    with patch.object(server, "_compute_competitor_drift_items", return_value=[{"listing_id": 5}]):
        result = server._execute_agent_tool("get_competitor_drift", {})
    check(result == {"items": [{"listing_id": 5}]}, f"got: {result}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("COMPETITOR WATCHDOG TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COMPETITOR WATCHDOG TESTS OK — every drift finding traces to a real live comparable-listing "
          "search, the shop's own listings are excluded from their own comparables, and no dollar figure "
          "is ever fabricated from a price gap.")


if __name__ == "__main__":
    run()
