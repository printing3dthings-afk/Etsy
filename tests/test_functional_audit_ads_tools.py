"""
Functional-correctness audit — tools/etsy_ads_tools.py's execute_tool()
dispatcher (line 113) and its handlers (_set_daily_budget, _toggle_listing_ad,
_log_ad_spend, _get_roas_report, etc.). These settings are real-money-affecting
(ad daily budget, spend tracking) and had zero genuine prior test coverage.

What this proves:
  1. execute_tool() routes every one of the 8 TOOL_DEFINITIONS tool_names to
     its own distinct handler (not cross-wired to a neighbor's handler).
  2. execute_tool() does not silently no-op for an unknown tool_name -- it
     returns a distinguishable message -- but that message is a bare string,
     not JSON, which breaks the module's own "every return value is
     json.loads()-able" contract that tools/api_server/main.py's real caller
     (_execute_agent_tool, line ~4365: `json.loads(_etsy_ads_tools.execute_tool(...))`)
     relies on unconditionally. Documented as a real (currently unreachable in
     production because main.py pre-filters by _ETSY_ADS_TOOL_NAMES) contract
     defect, not the headline bug.
  3. CONFIRMED BUG: _set_daily_budget only rejects budgets below $1.00
     (`if budget < 1.0`). There is NO upper bound at all -- an absurdly large
     daily budget (e.g. a $50,000/day typo instead of $50.00/day) is accepted
     and persisted with zero pushback, for a real-money-affecting setting.
     Additionally, float('nan') satisfies `nan < 1.0 == False` in Python, so a
     NaN budget is *also* accepted and persisted -- store.save() then writes a
     non-JSON-standard `NaN` token into the same shop_data.json every other
     endpoint reads, and downstream arithmetic (`budget * 30`,
     `total_revenue / total_spend`) silently propagates NaN through every
     ads-overview response until Scott happens to notice.

Safety:
  - DataStore is never touched. A minimal FakeStore duck-types the exact 5
    members etsy_ads_tools.py actually calls on `store` (`get`, `set`, `save`,
    `.listings`, `.analytics`), entirely in memory -- nothing ever reads or
    writes the real data/shop_data.json or its singleton.
  - No network, no Etsy/Anthropic/OpenAI calls are reachable from this module
    at all (pure local dict bookkeeping), so there is nothing else to mock at
    the I/O boundary.
  - Read-only audit: no application code is modified.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_ads_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

# ROOT itself must be on sys.path too: tools/etsy_ads_tools.py does
# `from data_store import DataStore`, and tools/data_store.py in turn does
# `from config import SHOP_DATA_FILE` where config.py lives at the repo root,
# not under tools/ -- without ROOT on sys.path that second import 404s.
for p in (ROOT, ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import etsy_ads_tools as ads_tools  # noqa: E402 -- tools/ is on sys.path

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


class FakeStore:
    """Duck-types the exact members etsy_ads_tools.py calls on `store`:
    get(*keys, default=...), set(value, *keys), save(), .listings, .analytics.
    Entirely in-memory -- never touches config.SHOP_DATA_FILE or the real
    DataStore singleton."""

    def __init__(self, listings=None, analytics=None):
        self._data: dict = {}
        self._listings = listings or []
        self._analytics = analytics or {}
        self.save_calls = 0

    def get(self, *keys, default=None):
        node = self._data
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def set(self, value, *keys):
        node = self._data
        for key in keys[:-1]:
            node = node.setdefault(key, {})
        node[keys[-1]] = value

    def save(self):
        self.save_calls += 1

    @property
    def listings(self):
        return self._listings

    @property
    def analytics(self):
        return self._analytics


def _sample_listings():
    return [
        {"id": "L1", "title": "Kawaii Planner 2026", "price": 14.99, "views": 500, "sales": 20, "favorites": 30},
        {"id": "L2", "title": "Budget Planner 2026", "price": 12.99, "views": 10, "sales": 0, "favorites": 1},
    ]


# ── execute_tool() routing: every tool_name reaches its OWN distinct handler ──

def test_execute_tool_routes_get_ads_overview():
    store = FakeStore()
    result = json.loads(ads_tools.execute_tool("get_ads_overview", {}, store))
    check("all_time_totals" in result, f"get_ads_overview: expected 'all_time_totals' key, got {list(result)}")
    check("daily_budget_usd" in result, "get_ads_overview: expected 'daily_budget_usd' key")


def test_execute_tool_routes_set_daily_budget():
    store = FakeStore()
    result = json.loads(ads_tools.execute_tool("set_daily_budget", {"daily_budget_usd": 5.0}, store))
    check(result.get("success") is True, f"set_daily_budget: expected success=True, got {result}")
    check(result.get("new_daily_budget_usd") == 5.0, f"set_daily_budget: expected new budget 5.0, got {result}")
    check(store.get("etsy_ads", "daily_budget_usd") == 5.0, "set_daily_budget must persist the budget via store.set")
    check(store.save_calls == 1, "set_daily_budget must call store.save() exactly once on success")


def test_execute_tool_routes_get_listing_ad_performance():
    store = FakeStore(listings=_sample_listings())
    result = json.loads(ads_tools.execute_tool("get_listing_ad_performance", {}, store))
    check("listing_ad_performance" in result, f"expected 'listing_ad_performance' key, got {list(result)}")
    check(len(result["listing_ad_performance"]) == 2, "expected one row per listing in FakeStore")


def test_execute_tool_routes_recommend_ad_strategy():
    store = FakeStore(listings=_sample_listings())
    result = json.loads(ads_tools.execute_tool("recommend_ad_strategy", {}, store))
    check("recommendations" in result, f"expected 'recommendations' key, got {list(result)}")
    check("listings_to_advertise" in result, "expected 'listings_to_advertise' key")


def test_execute_tool_routes_log_ad_spend():
    store = FakeStore()
    result = json.loads(ads_tools.execute_tool(
        "log_ad_spend",
        {"date": "2026-08-01", "spend_usd": 10.0, "clicks": 5, "impressions": 100,
         "orders_from_ads": 1, "revenue_from_ads": 30.0},
        store,
    ))
    check(result.get("success") is True, f"log_ad_spend: expected success=True, got {result}")
    check(result.get("roas_this_entry") == 3.0, f"log_ad_spend: expected roas_this_entry 3.0, got {result}")
    logged = store.get("etsy_ads", "spend_log")
    check(isinstance(logged, list) and len(logged) == 1, "log_ad_spend must append to store's spend_log")


def test_execute_tool_routes_get_roas_report():
    store = FakeStore()
    ads_tools.execute_tool(
        "log_ad_spend",
        {"date": "2026-08-01", "spend_usd": 10.0, "revenue_from_ads": 40.0},
        store,
    )
    result = json.loads(ads_tools.execute_tool("get_roas_report", {"period": "all_time"}, store))
    check("roas_rating" in result, f"get_roas_report: expected 'roas_rating' key, got {list(result)}")
    check(result.get("roas") == 4.0, f"get_roas_report: expected roas 4.0, got {result}")


def test_execute_tool_routes_toggle_listing_ad():
    store = FakeStore()
    result = json.loads(ads_tools.execute_tool(
        "toggle_listing_ad", {"listing_id": "L1", "enabled": True, "reason": "testing"}, store
    ))
    check(result.get("success") is True, f"toggle_listing_ad: expected success=True, got {result}")
    check(result.get("ad_enabled") is True, "toggle_listing_ad: expected ad_enabled True")
    stored = store.get("etsy_ads", "listing_ads")
    check(stored is not None and stored.get("L1", {}).get("enabled") is True,
          "toggle_listing_ad must persist the enabled flag for the right listing_id")


def test_execute_tool_routes_get_offsite_ads_summary():
    store = FakeStore(analytics={"revenue": {"this_year": 5000}})
    result = json.loads(ads_tools.execute_tool("get_offsite_ads_summary", {}, store))
    check("offsite_ads_status" in result, f"expected 'offsite_ads_status' key, got {list(result)}")
    check(result.get("fee_tier") == "15% (shop < $10k/yr)", f"expected 15% tier for $5k revenue, got {result.get('fee_tier')}")


def test_execute_tool_each_tool_name_produces_a_DIFFERENT_result_shape():
    """Cross-wiring regression guard: prove no two tool_names silently share a
    handler by checking every result has a distinct top-level key set."""
    store = FakeStore(listings=_sample_listings(), analytics={"revenue": {"this_year": 20000}})
    calls = {
        "get_ads_overview": {},
        "set_daily_budget": {"daily_budget_usd": 3.0},
        "get_listing_ad_performance": {},
        "recommend_ad_strategy": {},
        "log_ad_spend": {"spend_usd": 1.0},
        "get_roas_report": {},
        "toggle_listing_ad": {"listing_id": "L1", "enabled": False},
        "get_offsite_ads_summary": {},
    }
    seen_keysets = {}
    for name, tool_input in calls.items():
        result = json.loads(ads_tools.execute_tool(name, tool_input, store))
        keyset = frozenset(result.keys())
        for other_name, other_keyset in seen_keysets.items():
            check(keyset != other_keyset, f"{name} and {other_name} returned identical key sets {keyset} -- possible cross-wired handler")
        seen_keysets[name] = keyset


# ── execute_tool() unknown tool_name: must not silently no-op ────────────────

def test_execute_tool_unknown_tool_name_is_not_silent_and_not_confused_with_success():
    store = FakeStore()
    result = ads_tools.execute_tool("this_tool_does_not_exist", {}, store)
    check(isinstance(result, str) and "this_tool_does_not_exist" in result,
          f"unknown tool_name should be named in the response, got {result!r}")
    check("Unknown" in result or "unknown" in result,
          f"unknown tool_name response should clearly signal 'unknown', got {result!r}")
    check(store.save_calls == 0, "an unknown tool_name must never trigger a store.save() as a side effect")


def test_execute_tool_unknown_tool_name_breaks_the_modules_own_json_contract():
    """Documented contract defect (not the headline bug): every OTHER
    execute_tool() branch returns json.dumps(...) -- valid, json.loads()-able
    JSON. The unknown-tool_name branch returns a bare f-string instead. main.py
    always does `json.loads(_etsy_ads_tools.execute_tool(...))` (main.py ~line
    4365) with no special-case for this path -- if it were ever reached (e.g.
    a name gets added to TOOL_DEFINITIONS/_ETSY_ADS_TOOL_NAMES without a
    matching execute_tool() branch, or any other direct caller), it would blow
    up as a generic JSONDecodeError instead of surfacing "unknown tool" to the
    caller. Currently unreachable via main.py's real dispatch path only
    because main.py pre-filters tool_name against _ETSY_ADS_TOOL_NAMES before
    ever calling execute_tool()."""
    store = FakeStore()
    result = ads_tools.execute_tool("this_tool_does_not_exist", {}, store)
    try:
        json.loads(result)
        is_json = True
    except json.JSONDecodeError:
        is_json = False
    check(not is_json, "documenting known defect: unknown-tool_name branch returns non-JSON, breaking the module's json.loads()-able contract")


# ── _set_daily_budget: negative / absurdly large / NaN budgets ───────────────

def test_set_daily_budget_rejects_negative():
    store = FakeStore()
    result = json.loads(ads_tools.execute_tool("set_daily_budget", {"daily_budget_usd": -50.0}, store))
    check("error" in result, f"a negative daily budget must be rejected, got {result}")
    check(store.get("etsy_ads", "daily_budget_usd") is None, "a rejected negative budget must not be persisted")
    check(store.save_calls == 0, "a rejected negative budget must not trigger store.save()")


def test_set_daily_budget_rejects_zero():
    store = FakeStore()
    result = json.loads(ads_tools.execute_tool("set_daily_budget", {"daily_budget_usd": 0.0}, store))
    check("error" in result, f"a $0.00 daily budget must be rejected (module's own stated minimum is $1.00), got {result}")


def test_set_daily_budget_CONFIRMED_BUG_accepts_absurdly_large_budget():
    """CONFIRMED BUG: _set_daily_budget has no upper bound. A $50,000/day
    budget (e.g. a plausible typo for $50.00/day, or $5.00/day with an extra
    zero) is accepted and persisted with zero pushback for a real-money-
    affecting setting."""
    store = FakeStore()
    result = json.loads(ads_tools.execute_tool("set_daily_budget", {"daily_budget_usd": 50000.0}, store))
    check(
        "error" in result,
        "BUG: _set_daily_budget accepted a $50,000/day budget with no upper-bound "
        f"validation at all -- got success result {result!r} instead of a rejection. "
        "Any typo (extra digit) in a real-money ad budget silently goes live-config-ready."
    )


def test_set_daily_budget_CONFIRMED_BUG_nan_bypasses_the_minimum_check():
    """CONFIRMED BUG: Python's `nan < 1.0` evaluates to False (NaN compares
    unequal/false to everything), so `if budget < 1.0: return error` does NOT
    catch a NaN budget -- it falls through and gets persisted, after which
    `round(budget * 30, 2)` and every downstream ROAS/budget calculation that
    reads this value silently propagates NaN. json.dumps(nan) emits a bare
    `NaN` token, which is not standard JSON and can break any strict JSON
    consumer (e.g. a JS frontend calling JSON.parse on the persisted value)."""
    store = FakeStore()
    result = json.loads(ads_tools.execute_tool("set_daily_budget", {"daily_budget_usd": float("nan")}, store))
    got_error = "error" in result
    persisted = store.get("etsy_ads", "daily_budget_usd")
    check(
        got_error,
        f"BUG: _set_daily_budget accepted a NaN budget (nan < 1.0 is False in Python, so the "
        f"minimum-budget check silently fails to catch it) -- got {result!r}, persisted value was "
        f"{persisted!r} (is-nan: {isinstance(persisted, float) and persisted != persisted})."
    )


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FUNCTIONAL AUDIT TESTS OK -- etsy_ads_tools.execute_tool() routes every tool_name to its "
          "own distinct handler and fails visibly (not silently) on an unknown tool_name.")


if __name__ == "__main__":
    run()
