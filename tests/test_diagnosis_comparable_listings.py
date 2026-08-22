"""
Tests for Frank upgrade Wave 4, item C2 (2026-07-17): wiring real comparable-
listing data (C1's get_comparable_listings / EtsyAPIClient.search_listings())
into _diagnose_listing_core, so the Conversion Doctor's price guidance cites
real market data instead of only the static .99/.97/.49 psychology-ending rule.

_diagnose_listing_core's internal _gather() now does a best-effort, non-fatal
search_listings() call on the listing's own title, excludes the listing's own
ID from its own comparable set, and (when at least one valid price comes
back) computes count/price_min/price_max/price_avg/sample_titles. That data
is folded into both the returned `stats.comparable_listings` field and the
`user_payload` text actually sent to Claude -- and _CONVERSION_DOCTOR_SYSTEM's
PRICE bullet now instructs the model to cite it directly when present.

This never touches Etsy's write API and never bypasses staging -- it only
enriches what the read-only diagnosis call feeds the LLM.

Run: python tests/test_diagnosis_comparable_listings.py
"""
import asyncio
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_diag_comparable_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "diag-comparable-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


_LISTING_ID = 5551001


def _fake_listing():
    return {
        "listing_id": _LISTING_ID,
        "title": "Digital Planner 2026 Undated, GoodNotes iPad, Instant Download",
        "price": {"amount": 1499, "divisor": 100},
        "tags": ["digital planner", "goodnotes planner"],
        "description": "Some hook.\n\nWHAT'S INCLUDED\nStuff.",
        "views": 500,
        "num_favorers": 20,
        "state": "active",
    }


def _fake_anthropic_response(text: str):
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


def _run_diagnosis_capturing_payload(search_results):
    """Runs _diagnose_listing_core with EtsyAPIClient mocked and captures the
    exact user_payload text sent to Claude, plus the returned result."""
    captured = {}

    def fake_search(self, keywords, limit=10, sort_on="score", min_price=None, max_price=None):
        captured["keywords"] = keywords
        captured["limit"] = limit
        return search_results

    def fake_anthropic_create(client, **kwargs):
        captured["user_payload"] = kwargs["messages"][0]["content"]
        captured["system_prompt"] = kwargs["system"][0]["text"]
        return _fake_anthropic_response(
            '{"primary_issue": "test", "summary": "test", "fixes": []}'
        )

    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server.EtsyAPIClient, "get_listing", return_value=_fake_listing()), \
         patch.object(server.EtsyAPIClient, "get_listing_images", return_value=[1, 2, 3]), \
         patch.object(server, "_sales_by_listing_sync", return_value={_LISTING_ID: 4}), \
         patch.object(server.EtsyAPIClient, "search_listings", fake_search), \
         patch.object(server, "_anthropic_create", fake_anthropic_create):
        result = asyncio.run(server._diagnose_listing_core(_LISTING_ID))
    return result, captured


def test_comparable_data_reaches_stats_and_payload():
    search_results = {
        "results": [
            {"listing_id": 999, "title": "Kawaii Digital Planner GoodNotes 2026", "price": {"amount": 1299, "divisor": 100}},
            {"listing_id": 998, "title": "Cute Digital Planner Instant Download", "price": {"amount": 1699, "divisor": 100}},
        ]
    }
    result, captured = _run_diagnosis_capturing_payload(search_results)

    comparable = result["stats"]["comparable_listings"]
    check(comparable is not None, f"expected comparable data in stats, got: {result['stats']}")
    check(comparable["count"] == 2, f"expected 2 comparables, got: {comparable}")
    check(comparable["price_min"] == 12.99, f"got: {comparable}")
    check(comparable["price_max"] == 16.99, f"got: {comparable}")
    check(comparable["price_avg"] == 14.99, f"got: {comparable}")
    check("Kawaii Digital Planner GoodNotes 2026" in comparable["sample_titles"], f"got: {comparable}")

    check("REAL COMPARABLE LISTINGS" in captured["user_payload"], "the LLM payload must include the comparable section")
    check("$12.99-$16.99" in captured["user_payload"], f"got payload: {captured['user_payload'][:500]}")
    check("average $14.99" in captured["user_payload"], f"got payload: {captured['user_payload'][:500]}")

    check(captured["keywords"] == _fake_listing()["title"], "search must use the listing's own title as the query")


def test_own_listing_excluded_from_its_own_comparables():
    search_results = {
        "results": [
            {"listing_id": _LISTING_ID, "title": "Digital Planner 2026 Undated, GoodNotes iPad, Instant Download", "price": {"amount": 1499, "divisor": 100}},
            {"listing_id": 777, "title": "Other Planner", "price": {"amount": 999, "divisor": 100}},
        ]
    }
    result, captured = _run_diagnosis_capturing_payload(search_results)
    comparable = result["stats"]["comparable_listings"]
    check(comparable["count"] == 1, f"the listing's own ID must be excluded from its own comparables, got: {comparable}")
    check(comparable["price_avg"] == 9.99, f"got: {comparable}")


def test_no_comparables_found_degrades_cleanly():
    result, captured = _run_diagnosis_capturing_payload({"results": []})
    check(result["stats"]["comparable_listings"] is None, f"expected None with zero results, got: {result['stats']}")
    check("REAL COMPARABLE LISTINGS: not available" in captured["user_payload"], f"got: {captured['user_payload'][:400]}")


def test_search_listings_failure_is_non_fatal():
    # A real search_listings() exception (network hiccup, bad response shape)
    # must never break the diagnosis itself -- it just runs without the signal.
    def failing_search(self, keywords, limit=10, sort_on="score", min_price=None, max_price=None):
        raise RuntimeError("simulated network failure")

    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server.EtsyAPIClient, "get_listing", return_value=_fake_listing()), \
         patch.object(server.EtsyAPIClient, "get_listing_images", return_value=[1, 2, 3]), \
         patch.object(server, "_sales_by_listing_sync", return_value={_LISTING_ID: 4}), \
         patch.object(server.EtsyAPIClient, "search_listings", failing_search), \
         patch.object(server, "_anthropic_create",
                       lambda client, **kwargs: _fake_anthropic_response('{"primary_issue": "ok", "fixes": []}')):
        result = asyncio.run(server._diagnose_listing_core(_LISTING_ID))

    check(result["stats"]["comparable_listings"] is None,
          f"a search failure must degrade to None, not raise, got: {result['stats']}")
    check(result["diagnosis"]["primary_issue"] == "ok", "the diagnosis itself must still complete successfully")


def test_system_prompt_instructs_citing_comparable_data():
    _, captured = _run_diagnosis_capturing_payload({"results": []})
    system_prompt = captured["system_prompt"]
    check("COMPARABLE LISTINGS" in system_prompt,
          f"the system prompt's PRICE guidance must reference comparable-listing data, got: {system_prompt[:2000]}")
    check("comparable" in system_prompt.lower(),
          "the system prompt must instruct citing real comparable data, not just the static rule")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("DIAGNOSIS COMPARABLE-LISTINGS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("DIAGNOSIS COMPARABLE-LISTINGS TESTS OK — comparable data reaches both stats "
          "and the LLM payload, the listing's own ID is excluded from its own comparable "
          "set, zero-results and search-failure both degrade cleanly without breaking the "
          "diagnosis, and the system prompt instructs citing real comparable data.")


if __name__ == "__main__":
    run()
