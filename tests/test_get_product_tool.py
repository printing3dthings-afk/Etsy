#!/usr/bin/env python3
"""
_resolve_product() / get_product agent tool tests (2026-07-30).

Regression coverage for the exact bug Scott reported: "I put a listing id in
his chat. He didn't know what the product was." Root cause was that the only
ID-lookup tool the CEO agent had (get_listing) queries Etsy directly and
silently fails on anything that isn't a bare numeric Etsy listing_id -- so an
internal product code like 'DP1026' (what this shop's catalog actually uses,
see CLAUDE.md's Product Catalog section) never resolved to anything. This
tests _resolve_product(), the catalog-aware resolver that backs the new
get_product tool: internal product_id match, numeric listing_id match (via
the catalog), name-fragment search (unique + ambiguous), and the live-Etsy
fallback for a listing that exists on Etsy but isn't in the local catalog.

Mocks the narrowest real dependency (server.EtsyAPIClient), passes an
explicit `catalog` list to _resolve_product() so no test depends on real
disk state, and patches server._product_catalog_overrides to a fixed {} so
a real overrides sidecar (if one exists in this environment) can't make a
test's outcome depend on unrelated state.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


_CATALOG = [
    {
        "product_id": "DP1026", "name": "Ultimate Digital Life Planner (Lavender Dreams)",
        "etsy_listing_id": "4509179201", "price": 14.99, "category": "digital_planner",
        "status": "active",
        "files": ["data/digital_products/product_files/DP1026.pdf",
                  "data/digital_products/product_files/DP1026_sticker_pack.zip"],
        "last_updated": "2026-06-18", "note": "Re-uploaded 2026-06-18: fixed nav bug.",
    },
    {
        "product_id": "DP1028", "name": "Budget & Finance Planner 2026 (Midnight Blue)",
        "etsy_listing_id": "4509184962", "price": 12.99, "category": "digital_planner",
        "status": "active", "files": [],
    },
]


def _fake_listing(listing_id, title="Ultimate Digital Life Planner 2026"):
    return {
        "listing_id": listing_id, "title": title, "state": "active", "price": "14.99",
        "views": 500, "num_favorers": 40, "tags": ["digital planner"],
        "url": f"https://www.etsy.com/listing/{listing_id}",
        "description": "A great planner.",
    }


def test_resolves_by_internal_product_code_case_insensitive():
    with patch.object(server, "_product_catalog_overrides", return_value={}), \
         patch.object(server, "_catalog_file_exists", return_value=True), \
         patch.object(server.EtsyAPIClient, "get_listing", return_value=_fake_listing(4509179201)):
        result = server._resolve_product("dp1026", catalog=_CATALOG)
    check(result.get("found") is True, f"expected found=True, got {result}")
    check(result.get("in_catalog") is True, f"expected in_catalog=True, got {result}")
    check(result.get("product_id") == "DP1026", f"expected product_id=DP1026, got {result}")
    check(result.get("category") == "digital_planner", f"got {result}")
    check(result.get("all_files_present") is True, f"got {result}")
    check(result.get("note") == "Re-uploaded 2026-06-18: fixed nav bug.",
          f"the catalog's operational note must be surfaced, got {result}")
    check(result.get("etsy", {}).get("title") == "Ultimate Digital Life Planner 2026",
          f"live Etsy data must be merged in when the catalog entry has a listing_id, got {result}")


def test_resolves_by_numeric_listing_id_via_catalog():
    with patch.object(server, "_product_catalog_overrides", return_value={}), \
         patch.object(server, "_catalog_file_exists", return_value=True), \
         patch.object(server.EtsyAPIClient, "get_listing", return_value=_fake_listing(4509184962, "Budget Planner")):
        result = server._resolve_product("4509184962", catalog=_CATALOG)
    check(result.get("found") is True, f"got {result}")
    check(result.get("product_id") == "DP1028", f"a numeric Etsy ID must resolve via the catalog's etsy_listing_id field, got {result}")


def test_resolves_by_unique_name_fragment():
    with patch.object(server, "_product_catalog_overrides", return_value={}), \
         patch.object(server, "_catalog_file_exists", return_value=True), \
         patch.object(server.EtsyAPIClient, "get_listing", return_value=_fake_listing(4509184962)):
        result = server._resolve_product("Budget & Finance", catalog=_CATALOG)
    check(result.get("found") is True, f"got {result}")
    check(result.get("product_id") == "DP1028", f"got {result}")


def test_ambiguous_name_fragment_returns_candidates_not_a_wrong_guess():
    with patch.object(server, "_product_catalog_overrides", return_value={}), \
         patch.object(server, "_catalog_file_exists", return_value=True):
        result = server._resolve_product("Planner", catalog=_CATALOG)
    check(result.get("found") is False, f"an ambiguous name match must never silently pick one, got {result}")
    check(len(result.get("candidates", [])) == 2, f"expected both matching products listed as candidates, got {result}")


def test_numeric_id_not_in_catalog_falls_back_to_live_etsy():
    with patch.object(server, "_product_catalog_overrides", return_value={}), \
         patch.object(server, "_catalog_file_exists", return_value=True), \
         patch.object(server.EtsyAPIClient, "get_listing", return_value=_fake_listing(9999999999, "Some Un-catalogued Listing")):
        result = server._resolve_product("9999999999", catalog=_CATALOG)
    check(result.get("found") is True, f"a real Etsy listing must never be reported unknown just because it's un-catalogued, got {result}")
    check(result.get("in_catalog") is False, f"got {result}")
    check(result.get("name") == "Some Un-catalogued Listing", f"got {result}")


def test_numeric_id_not_in_catalog_and_etsy_404_reports_not_found_clearly():
    err = server.EtsyAPIError(404, "not found")
    with patch.object(server, "_product_catalog_overrides", return_value={}), \
         patch.object(server, "_catalog_file_exists", return_value=True), \
         patch.object(server.EtsyAPIClient, "get_listing", side_effect=err):
        result = server._resolve_product("1234567890", catalog=_CATALOG)
    check(result.get("found") is False, f"got {result}")
    check("404" in (result.get("note") or ""), f"the 404 must be surfaced plainly, got {result}")


def test_non_numeric_unmatched_identifier_reports_not_found_without_a_network_call():
    mock_get = MagicMock()
    with patch.object(server, "_product_catalog_overrides", return_value={}), \
         patch.object(server, "_catalog_file_exists", return_value=True), \
         patch.object(server.EtsyAPIClient, "get_listing", mock_get):
        result = server._resolve_product("TOTALLY_MADE_UP_CODE", catalog=_CATALOG)
    check(result.get("found") is False, f"got {result}")
    check(mock_get.call_count == 0, "a non-numeric identifier with no catalog match must never hit Etsy (it can't be a listing_id)")


def test_catalog_match_but_etsy_fetch_failure_still_returns_catalog_data():
    with patch.object(server, "_product_catalog_overrides", return_value={}), \
         patch.object(server, "_catalog_file_exists", return_value=True), \
         patch.object(server.EtsyAPIClient, "get_listing", side_effect=Exception("network blip")):
        result = server._resolve_product("DP1026", catalog=_CATALOG)
    check(result.get("found") is True, f"a transient Etsy fetch failure must not blank out the still-useful catalog data, got {result}")
    check(result.get("product_id") == "DP1026", f"got {result}")
    check("etsy_fetch_error" in result, f"the fetch failure must be surfaced, not swallowed, got {result}")


def test_empty_identifier_returns_a_clear_error():
    result = server._resolve_product("   ", catalog=_CATALOG)
    check(result == {"error": "identifier is required"}, f"got {result}")


def test_dispatcher_routes_get_product_to_resolve_product():
    # End-to-end through _execute_agent_tool with the REAL data/product_catalog.json
    # on disk (DP1026 genuinely exists there -- see CLAUDE.md's Product Catalog
    # section) -- only the live Etsy call is mocked, confirming the dispatch branch
    # actually wires through rather than just existing in the AGENT_TOOLS registry.
    with patch.object(server.EtsyAPIClient, "get_listing", return_value=_fake_listing(4509179201)):
        result = server._execute_agent_tool("get_product", {"identifier": "DP1026"})
    check(result.get("found") is True, f"got {result}")
    check(result.get("product_id") == "DP1026", f"got {result}")


def test_get_product_is_registered_in_agent_tools_with_string_schema():
    tool = next((t for t in server.AGENT_TOOLS if t["name"] == "get_product"), None)
    check(tool is not None, "get_product must be registered in AGENT_TOOLS")
    check(tool["input_schema"]["required"] == ["identifier"], f"got {tool['input_schema'] if tool else None}")
    check(tool["input_schema"]["properties"]["identifier"]["type"] == "string",
          "identifier must be a string (not integer like get_listing's listing_id) -- it also accepts product codes/names")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("GET_PRODUCT TOOL TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("GET_PRODUCT TOOL TESTS OK — internal product code, numeric listing ID, name-fragment, "
          "ambiguous-match, and un-catalogued-listing resolution all behave correctly.")


if __name__ == "__main__":
    run()
