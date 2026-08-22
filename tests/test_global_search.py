"""
Tests for GET /api/search (Frank upgrade Wave 3, usability item 3, 2026-07-17).

Original audit finding: the header search box claimed to search "listings,
orders, tools, knowledge base" but the client-only implementation
(frank_hud_mockup.py's old runGlobalSearch) never actually searched orders,
never searched Products at all, only scanned whatever screens happened to
already be cached in the browser that session, and jumped straight to the
first match instead of showing a real results list.

This adds a real backend endpoint that searches six categories fresh every
call (listings, orders, products, tools, tasks, kb docs), each degrading to
an empty list on its own failure so one down data source never takes the
whole search down -- the same lesson learned fixing /api/cogs-status the
same day (this sandbox has no real Etsy credentials, which is exercised here
as a real, not mocked, failure path for listings/orders).

Run: python tests/test_global_search.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_search_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "search-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── per-source search functions ─────────────────────────────────────────────
def test_search_products_finds_a_real_catalog_entry():
    results = server._search_products("planner")
    check(len(results) > 0, "searching 'planner' against the real catalog should find matches")
    check(all(r["category"] == "product" for r in results), f"all results must be category=product, got: {results}")
    check(all("id" in r and "title" in r for r in results), f"each result needs id+title, got: {results}")


def test_search_products_matches_by_product_id_too():
    results = server._search_products("dp1026")
    ids = [r["id"] for r in results]
    check("DP1026" in ids, f"searching the product_id itself should match, got ids: {ids}")


def test_search_products_respects_limit():
    results = server._search_products("a", limit=2)  # 'a' matches almost everything
    check(len(results) <= 2, f"limit=2 must cap results, got {len(results)}")


def test_search_tools_finds_a_known_tool_by_name():
    results = server._search_tools("pinterest")
    names = [r["id"] for r in results]
    check("stage_pinterest_post" in names or "list_pinterest_boards" in names,
          f"searching 'pinterest' should find the Pinterest tools, got: {names}")
    check(all(r["category"] == "tool" for r in results), f"all results must be category=tool, got: {results}")


def test_search_tools_matches_description_not_just_name():
    # execute_command's own name doesn't contain "backend automation" but its description does.
    results = server._search_tools("backend automation")
    check(any(r["id"] == "execute_command" for r in results),
          f"a description-only match should still be found, got: {results}")


def test_search_kb_finds_a_real_doc():
    results = server._search_kb("etsy")
    check(len(results) > 0, "searching 'etsy' against the knowledge base should find matches")
    check(all(r["category"] == "kb" for r in results), f"all results must be category=kb, got: {results}")


def test_search_tasks_returns_task_category_shape():
    results = server._search_tasks("")
    # empty query matches everything via `in` semantics -- just checking shape here
    if results:
        check(all(r["category"] == "task" for r in results), f"all results must be category=task, got: {results}")


def test_search_listings_degrades_to_empty_on_real_credential_failure():
    # Regression pattern from the /api/cogs-status fix the same day: this
    # sandbox genuinely has no Etsy OAuth token, so the real (unmocked) call
    # must degrade to [] rather than raising.
    results = server._search_listings("anything")
    check(results == [], f"with no Etsy credentials, listings search must degrade to [], got: {results}")


def test_search_orders_degrades_to_empty_on_real_credential_failure():
    results = server._search_orders("anything")
    check(results == [], f"with no Etsy credentials, orders search must degrade to [], got: {results}")


def test_search_products_survives_a_missing_catalog_file():
    import json as _json
    orig_read_text = Path.read_text

    def _boom(self, *a, **kw):
        if self.name == "product_catalog.json":
            raise OSError("simulated missing file")
        return orig_read_text(self, *a, **kw)

    Path.read_text = _boom
    try:
        results = server._search_products("planner")
        check(results == [], f"a missing/unreadable catalog file must degrade to [], not raise, got: {results}")
    finally:
        Path.read_text = orig_read_text


# ── the aggregate endpoint (dispatched directly, no HTTP layer needed) ──────
def test_global_search_endpoint_empty_query_returns_no_results():
    import asyncio
    result = asyncio.run(server.global_search(q=""))
    check(result == {"query": "", "results": [], "count": 0}, f"an empty query should short-circuit, got: {result}")


def test_global_search_endpoint_aggregates_across_categories():
    import asyncio
    result = asyncio.run(server.global_search(q="planner"))
    check(result["count"] == len(result["results"]), f"count must match len(results), got: {result}")
    categories = {r["category"] for r in result["results"]}
    # listings/orders will be empty (no creds), but products/tools/kb should
    # plausibly contribute for a broad term like "planner".
    check("product" in categories, f"'planner' should surface at least one product match, got categories: {categories}")


def test_global_search_endpoint_never_500s_even_if_a_subsearch_breaks():
    import asyncio

    def _boom(*a, **kw):
        raise RuntimeError("simulated catastrophic failure")

    orig = server._search_tools
    server._search_tools = _boom
    try:
        # asyncio.gather without return_exceptions propagates the first
        # exception -- the endpoint's own outer try/except must still catch it.
        result = asyncio.run(server.global_search(q="x"))
        check("error" in result, f"an unexpected sub-search failure must degrade to a soft error, not raise, got: {result}")
        check(result["results"] == [], f"expected empty results on total failure, got: {result}")
    finally:
        server._search_tools = orig


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("GLOBAL SEARCH TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("GLOBAL SEARCH TESTS OK — all 6 category searches verified (products by title+id, "
          "tools by name+description, kb docs, tasks shape), real-credential-failure "
          "degradation for listings/orders, a missing-catalog-file degradation, and the "
          "aggregate endpoint's empty-query short-circuit, cross-category aggregation, "
          "and total-failure soft-error handling.")


if __name__ == "__main__":
    run()
