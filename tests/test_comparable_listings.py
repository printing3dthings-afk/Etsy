"""
Tests for Frank upgrade Wave 4, item C1 (2026-07-17): get_comparable_listings,
the shop's first real external market-data source exposed as an agent tool.

EtsyAPIClient.search_listings() (tools/etsy_api.py) already existed and was
already correct (real public listings/active v3 endpoint, public API key
only, no OAuth, no scraping/ToS risk) but was never exposed as an agent
tool -- tools/fetch_market_examples.py duplicated its own raw-requests
version instead of reusing it. This wraps the real client method directly.

Run: python tests/test_comparable_listings.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_comparable_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "comparable-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_registered_as_agent_tool():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("get_comparable_listings" in names, "get_comparable_listings must be in AGENT_TOOLS")


def test_requires_keywords():
    result = server._get_comparable_listings({})
    check("error" in result, f"missing keywords must error, got: {result}")


def test_degrades_gracefully_with_no_real_etsy_credentials():
    # This sandbox genuinely has no Etsy credentials -- a real (not mocked)
    # exercise of the failure path, same discipline as the cogs-status fix.
    result = server._get_comparable_listings({"keywords": "kawaii digital planner"})
    check("error" in result, f"with no credentials this must degrade to a clean error, not raise, got: {result}")
    check("comparable-listing search failed" in result["error"], f"got: {result}")


def test_parses_real_listing_results_correctly():
    fake_response = {
        "results": [
            {"listing_id": 111, "title": "Kawaii Planner A", "price": {"amount": 1499, "divisor": 100}, "tags": ["digital planner", "goodnotes"]},
            {"listing_id": 222, "title": "Kawaii Planner B", "price": {"amount": 999, "divisor": 100}, "tags": ["kawaii planner"]},
        ]
    }
    with patch.object(server.EtsyAPIClient, "search_listings", return_value=fake_response):
        result = server._get_comparable_listings({"keywords": "kawaii planner", "limit": 5})
    check("error" not in result, f"expected success, got: {result}")
    check(result["count"] == 2, f"expected 2 listings, got: {result['count']}")
    check(result["listings"][0]["price"] == 14.99, f"expected $14.99 parsed from Money object, got: {result['listings'][0]}")
    check(result["listings"][1]["price"] == 9.99, f"expected $9.99 parsed from Money object, got: {result['listings'][1]}")
    check(result["listings"][0]["url"] == "https://www.etsy.com/listing/111", f"got: {result['listings'][0]}")
    check(result["price_range"] == {"min": 9.99, "max": 14.99, "avg": 12.49}, f"got: {result['price_range']}")


def test_empty_results_has_no_price_range_crash():
    with patch.object(server.EtsyAPIClient, "search_listings", return_value={"results": []}):
        result = server._get_comparable_listings({"keywords": "nonexistent product xyz"})
    check(result["count"] == 0, f"expected 0 results, got: {result}")
    check(result["price_range"] is None, f"expected no price_range for zero results, got: {result['price_range']}")


def test_limit_is_capped_at_25():
    captured = {}

    def fake_search(self, keywords, limit=10, sort_on="score", min_price=None, max_price=None):
        captured["limit"] = limit
        return {"results": []}

    with patch.object(server.EtsyAPIClient, "search_listings", fake_search):
        server._get_comparable_listings({"keywords": "x", "limit": 999})
    check(captured["limit"] == 25, f"expected the limit capped at 25, got: {captured['limit']}")


def test_min_max_price_passed_through():
    captured = {}

    def fake_search(self, keywords, limit=10, sort_on="score", min_price=None, max_price=None):
        captured["min_price"] = min_price
        captured["max_price"] = max_price
        return {"results": []}

    with patch.object(server.EtsyAPIClient, "search_listings", fake_search):
        server._get_comparable_listings({"keywords": "x", "min_price": 5, "max_price": 20})
    check(captured["min_price"] == 5.0, f"got: {captured}")
    check(captured["max_price"] == 20.0, f"got: {captured}")


def test_invalid_price_filters_error_cleanly():
    result = server._get_comparable_listings({"keywords": "x", "min_price": "not-a-number"})
    check("error" in result, f"an invalid min_price must error cleanly, got: {result}")


def test_agent_tool_dispatch():
    with patch.object(server.EtsyAPIClient, "search_listings", return_value={"results": []}):
        out = server._execute_agent_tool("get_comparable_listings", {"keywords": "test"})
    check(out.get("keywords") == "test", f"expected dispatch to reach the real function, got: {out}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("COMPARABLE LISTINGS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COMPARABLE LISTINGS TESTS OK — tool registration, required-field validation, "
          "real credential-less degradation, Money-object price parsing, price_range "
          "computation (and its empty-results edge case), the 25-result cap, min/max "
          "price passthrough, invalid-filter handling, and agent-tool dispatch.")


if __name__ == "__main__":
    run()
