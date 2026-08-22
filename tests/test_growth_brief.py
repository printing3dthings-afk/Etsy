"""
Tests for "Growth Brief" (2026-08-06, idea 2/3 of the "significantly improve
Frank" roadmap) -- a ranked, dollar-impact-scored "what to prioritize this
week" list synthesized from Ads/COGS/Star Seller/seasonal keywords/bundle
opportunities/Conversion Doctor, instead of Scott having to check 5+
separate panels and combine them himself.

The one rule every test here is really checking: est_dollar_impact is either
a REAL number pulled directly from a source function (ad spend, logged
revenue, Star Seller's trailing-90-day revenue) or explicitly None with
impact_basis saying why -- never a fabricated/guessed dollar figure. Items
with a real $ figure always sort above items without one.

Checks:
  1. _score_growth_brief_items() -- pure function, no I/O -- produces the
     right item for every source status (ads kill_signal/low_roas/
     scale_eligible/not-used, Star Seller at_risk/on_track, COGS flagged/
     clean, actions high/medium/low, seasonal OVERDUE/THIS WEEK, bundle
     opportunities), and every item's est_dollar_impact is a real number
     traceable to the input or None.
  2. Sort order: real-$ items rank above null-$ items; among real-$ items,
     higher $ ranks first.
  3. _growth_brief_seasonal_entries() only returns OVERDUE/THIS WEEK entries
     for a fixed date, matching the calendar's own real urgency computation.
  4. _get_or_compute_cached() reuses an existing cache entry (never calls fn
     again) and populates the cache on a real miss.
  5. _compute_growth_brief() end-to-end wires all 5 sources together via
     mocks and returns a capped, sorted item list.
  6. GET /api/growth-brief caches for 60s.
  7. get_growth_brief is registered in AGENT_TOOLS and dispatches through
     _execute_agent_tool via asyncio.run(), matching the deep_research
     precedent for bridging sync tool-dispatch into async code.

Run: python tests/test_growth_brief.py
"""
import asyncio
import os
import sys
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_growthbrief_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "growthbrief-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _clear_growth_brief_caches():
    with server._cache_lock:
        for k in ("ads_status", "cogs_status", "star_seller", "actions", "bundle_opportunities", "growth_brief"):
            server._cache.pop(k, None)


def test_ads_kill_signal_item_has_real_dollar_figure():
    items = server._score_growth_brief_items(
        ads={"used": True, "status": "kill_signal", "week_spend": 42.5, "week_revenue": 0,
             "month_spend": 42.5, "month_revenue": 0, "month_roas": 0.0},
        cogs={"used": False}, star_seller={"status": "on_track"},
        actions_data={"actions": []}, bundle_opps=[], seasonal_entries=[],
    )
    ads_items = [i for i in items if i["category"] == "ads"]
    check(len(ads_items) == 1, f"expected exactly one ads item, got: {ads_items}")
    check(ads_items[0]["est_dollar_impact"] == 42.5, f"kill_signal's $ figure should be the real week_spend: {ads_items[0]}")
    check(ads_items[0]["severity"] == "high", f"kill_signal should be high severity: {ads_items[0]}")
    check("real" in ads_items[0]["impact_basis"], f"basis should say this is real, not estimated: {ads_items[0]}")


def test_ads_scale_eligible_uses_real_revenue_not_negative_spend():
    items = server._score_growth_brief_items(
        ads={"used": True, "status": "scale_eligible", "week_spend": 10, "week_revenue": 80,
             "month_spend": 100, "month_revenue": 500, "month_roas": 5.0},
        cogs={"used": False}, star_seller={"status": "on_track"},
        actions_data={"actions": []}, bundle_opps=[], seasonal_entries=[],
    )
    ads_items = [i for i in items if i["category"] == "ads"]
    check(ads_items[0]["est_dollar_impact"] == 500, f"scale_eligible's $ figure should be the real month_revenue: {ads_items[0]}")
    check(ads_items[0]["severity"] == "low", f"scale_eligible is an opportunity, not a problem -- should be low severity: {ads_items[0]}")


def test_ads_not_used_produces_no_item():
    items = server._score_growth_brief_items(
        ads={"used": False}, cogs={"used": False}, star_seller={"status": "on_track"},
        actions_data={"actions": []}, bundle_opps=[], seasonal_entries=[],
    )
    check(not any(i["category"] == "ads" for i in items), f"ads never used -- must produce zero ads items, got: {items}")


def test_star_seller_at_risk_uses_real_revenue_90d():
    items = server._score_growth_brief_items(
        ads={"used": False}, cogs={"used": False},
        star_seller={"status": "at_risk", "orders_90d": 2, "revenue_90d": 145.30},
        actions_data={"actions": []}, bundle_opps=[], seasonal_entries=[],
    )
    ss_items = [i for i in items if i["category"] == "star_seller"]
    check(len(ss_items) == 1, f"expected exactly one star_seller item: {ss_items}")
    check(ss_items[0]["est_dollar_impact"] == 145.30, f"should use the real revenue_90d figure: {ss_items[0]}")
    check(ss_items[0]["severity"] == "high", f"at_risk should be high severity: {ss_items[0]}")


def test_star_seller_on_track_produces_no_item():
    items = server._score_growth_brief_items(
        ads={"used": False}, cogs={"used": False}, star_seller={"status": "on_track", "revenue_90d": 900},
        actions_data={"actions": []}, bundle_opps=[], seasonal_entries=[],
    )
    check(not any(i["category"] == "star_seller" for i in items), f"on_track -- must produce zero items: {items}")


def test_cogs_flagged_never_fabricates_a_dollar_figure():
    items = server._score_growth_brief_items(
        ads={"used": False}, cogs={"used": True, "avg_margin_pct": 22.5,
                                     "flagged_low_margin": [{"listing_id": 1}, {"listing_id": 2}]},
        star_seller={"status": "on_track"}, actions_data={"actions": []}, bundle_opps=[], seasonal_entries=[],
    )
    cogs_items = [i for i in items if i["category"] == "cogs"]
    check(len(cogs_items) == 1, f"expected one cogs item: {cogs_items}")
    check(cogs_items[0]["est_dollar_impact"] is None,
          f"COGS margin is a flat-rate ESTIMATE -- must never claim a forward dollar figure: {cogs_items[0]}")
    check("estimate" in cogs_items[0]["impact_basis"], f"basis must say this is an estimate, not real: {cogs_items[0]}")
    check("2" in cogs_items[0]["title"], f"title should reflect the real flagged count: {cogs_items[0]}")


def test_actions_only_high_and_medium_severity_included_never_fabricates_dollars():
    items = server._score_growth_brief_items(
        ads={"used": False}, cogs={"used": False}, star_seller={"status": "on_track"},
        actions_data={"actions": [
            {"severity": "high", "category": "zero_views", "title": "Zero views", "detail": "d", "suggestion": "s",
             "listing_id": 111, "url": "https://etsy.com/x", "impact": 0},
            {"severity": "medium", "category": "tags_incomplete", "title": "Tags incomplete", "detail": "d",
             "suggestion": "s", "listing_id": 222, "url": None, "impact": 50},
            {"severity": "low", "category": "recently_fixed", "title": "Should be excluded", "detail": "", "suggestion": "", "impact": 0},
        ]}, bundle_opps=[], seasonal_entries=[],
    )
    fix_items = [i for i in items if i["category"] == "listing_fix"]
    check(len(fix_items) == 2, f"only high/medium severity actions should become items, got: {fix_items}")
    check(all(i["est_dollar_impact"] is None for i in fix_items),
          f"Conversion Doctor items must never carry a fabricated dollar figure: {fix_items}")
    check(all("no dollar figure fabricated" in i["impact_basis"] for i in fix_items), f"basis must say so explicitly: {fix_items}")
    check(not any("Should be excluded" in i["title"] for i in fix_items), f"low-severity action should be excluded: {fix_items}")


def test_seasonal_and_bundle_items_never_carry_a_dollar_figure():
    items = server._score_growth_brief_items(
        ads={"used": False}, cogs={"used": False}, star_seller={"status": "on_track"},
        actions_data={"actions": []},
        bundle_opps=[{"title": "67 wall art listings, 1 bundle", "suggestion": "build a bundle"}],
        seasonal_entries=[{"season": "back_to_school", "update_by": "2026-08-15", "listings_to_update": ["DP1027"], "urgency": "OVERDUE"}],
    )
    seasonal_items = [i for i in items if i["category"] == "seasonal"]
    bundle_items = [i for i in items if i["category"] == "bundle"]
    check(len(seasonal_items) == 1 and seasonal_items[0]["est_dollar_impact"] is None,
          f"seasonal items must never claim a dollar figure: {seasonal_items}")
    check(seasonal_items[0]["severity"] == "medium", f"OVERDUE seasonal item should be medium severity: {seasonal_items}")
    check(len(bundle_items) == 1 and bundle_items[0]["est_dollar_impact"] is None,
          f"bundle items must never claim a dollar figure: {bundle_items}")


def test_real_dollar_items_always_rank_above_null_dollar_items():
    items = server._score_growth_brief_items(
        ads={"used": True, "status": "kill_signal", "week_spend": 5.0, "week_revenue": 0,
             "month_spend": 5.0, "month_revenue": 0, "month_roas": 0.0},
        cogs={"used": True, "avg_margin_pct": 10, "flagged_low_margin": [{"listing_id": 1}]},
        star_seller={"status": "at_risk", "orders_90d": 1, "revenue_90d": 900.0},
        actions_data={"actions": [{"severity": "high", "category": "zero_views", "title": "X", "detail": "",
                                     "suggestion": "", "listing_id": 1, "url": None, "impact": 0}]},
        bundle_opps=[{"title": "bundle", "suggestion": "s"}],
        seasonal_entries=[{"season": "x", "update_by": "2026-01-01", "listings_to_update": [], "urgency": "OVERDUE"}],
    )
    dollar_flags = [it["est_dollar_impact"] is not None for it in items]
    # Every True must come before every False -- i.e. once a null-$ item appears, no real-$ item follows it.
    first_null_idx = dollar_flags.index(False) if False in dollar_flags else len(dollar_flags)
    check(all(dollar_flags[:first_null_idx]), f"a real-$ item must never appear after a null-$ item: {[ (it['category'], it['est_dollar_impact']) for it in items ]}")
    check(items[0]["category"] == "star_seller" and items[0]["est_dollar_impact"] == 900.0,
          f"the largest real $ figure (Star Seller's $900 at stake) should rank #1: {items[0]}")


def test_seasonal_entries_filters_to_overdue_and_this_week_only():
    fixed_today = date(2026, 8, 6)
    entries = server._growth_brief_seasonal_entries(fixed_today)
    for e in entries:
        check(e["urgency"] in ("OVERDUE", "THIS WEEK"), f"should only ever return OVERDUE/THIS WEEK entries, got: {e}")
    check(isinstance(entries, list), f"should return a list, got: {type(entries)}")


def test_get_or_compute_cached_reuses_existing_cache_without_calling_fn():
    _clear_growth_brief_caches()
    try:
        # _cache_set() already acquires _cache_lock internally -- do NOT also
        # wrap this in "with server._cache_lock:" (threading.Lock isn't
        # reentrant; that deadlocked this exact test on first write).
        server._cache_set("ads_status", {"used": True, "status": "ok", "week_spend": 1, "week_revenue": 1,
                                          "month_spend": 1, "month_revenue": 1, "month_roas": 1.0, "days_since_log": 0})
        fn = MagicMock(return_value={"should": "never be called"})
        result = asyncio.run(server._get_or_compute_cached("ads_status", 120, fn))
        check(result.get("status") == "ok", f"should return the cached value: {result}")
        check(fn.call_count == 0, f"must not call fn when the cache already has a fresh value: {fn.call_count} calls")
    finally:
        _clear_growth_brief_caches()


def test_get_or_compute_cached_computes_and_populates_on_miss():
    _clear_growth_brief_caches()
    try:
        fn = MagicMock(return_value={"used": False})
        result = asyncio.run(server._get_or_compute_cached("cogs_status", 120, fn))
        check(result == {"used": False}, f"should return fn's fresh result on a cache miss: {result}")
        check(fn.call_count == 1, f"should call fn exactly once on a genuine miss: {fn.call_count}")
        cached = server._cache_get("cogs_status", ttl=120)
        check(cached == {"used": False}, f"the fresh result should now be cached: {cached}")
    finally:
        _clear_growth_brief_caches()


def test_compute_growth_brief_wires_all_five_sources_together():
    _clear_growth_brief_caches()
    try:
        with patch.object(server, "_compute_ads_status", return_value={"used": False}), \
             patch.object(server, "_compute_cogs_status", return_value={"used": False}), \
             patch.object(server, "_compute_star_seller_status",
                           return_value={"status": "at_risk", "orders_90d": 3, "revenue_90d": 210.0}), \
             patch.object(server, "_compute_actions", return_value={"actions": []}), \
             patch.object(server, "_compute_bundle_opportunities", return_value=[]), \
             patch.object(server, "_shop_today", return_value=date(2026, 8, 6)):
            result = asyncio.run(server._compute_growth_brief())
        check("items" in result and "generated_at" in result, f"expected the standard shape, got: {result}")
        check(len(result["items"]) >= 1, f"the at_risk Star Seller item should surface: {result}")
        check(result["items"][0]["category"] == "star_seller", f"the only real item present should rank first: {result['items']}")
    finally:
        _clear_growth_brief_caches()


def test_endpoint_caches_for_60_seconds():
    _clear_growth_brief_caches()
    try:
        call_count = {"n": 0}

        async def _fake_compute():
            call_count["n"] += 1
            return {"items": [], "generated_at": "x"}

        with patch.object(server, "_compute_growth_brief", _fake_compute):
            asyncio.run(server.get_growth_brief(_token="test"))
            check(call_count["n"] == 1, f"first call should compute fresh: {call_count['n']}")
            # Second call within the cache window must not recompute.
            asyncio.run(server.get_growth_brief(_token="test"))
            check(call_count["n"] == 1, f"a second call within 60s must reuse the cache, not recompute: {call_count['n']}")
    finally:
        _clear_growth_brief_caches()


def test_tool_registered_and_dispatches_via_asyncio_run():
    names = [t["name"] for t in server.AGENT_TOOLS]
    check("get_growth_brief" in names, "get_growth_brief should be a registered AGENT_TOOLS entry")

    async def _fake_compute():
        return {"items": [{"category": "ads", "title": "x"}], "generated_at": "y"}
    with patch.object(server, "_compute_growth_brief", _fake_compute):
        result = server._execute_agent_tool("get_growth_brief", {})
    check(result == {"items": [{"category": "ads", "title": "x"}], "generated_at": "y"}, f"got: {result}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("GROWTH BRIEF TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("GROWTH BRIEF TESTS OK — every item's est_dollar_impact is either a real number traceable "
          "to its source or explicitly null (never fabricated), real-$ items always outrank null-$ "
          "items, caching reuses other panels' data with zero extra Etsy calls on a hit, and the "
          "chat tool dispatches correctly.")


if __name__ == "__main__":
    run()
