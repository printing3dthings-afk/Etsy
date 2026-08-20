#!/usr/bin/env python3
"""
Tests for EtsyAPIClient.update_price_via_inventory() (2026-08-20) -- the
confirmed real fix for the update_price silent-no-op incident.

Root cause (confirmed via Etsy's own developer community -- the etsy-api-v2
Google Group and etsy/open-api discussions #977/#691, Etsy staff responses):
the top-level `price` field on updateListing is silently ignored once a
listing has a real Inventory API "offering" record. The correct pattern,
per Etsy staff: read the full current inventory via getListingInventory,
mutate only the field(s) you want to change, and PUT the whole structure
back via updateListingInventory -- submitting fewer products than exist
deletes the missing ones, so this must never be a partial patch.

Checks:
  1. update_price_via_inventory() reads the full inventory, sets price on
     every offering of every product, and PUTs the complete structure back
     unchanged otherwise (price_on_property/quantity_on_property/
     sku_on_property preserved verbatim).
  2. A listing with multiple products/offerings gets every single one
     updated to the new price, not just the first.
  3. A listing with zero inventory products raises a specific, matchable
     EtsyAPIError ("no inventory products") rather than silently doing
     nothing or crashing with an unrelated exception -- this is the exact
     signal _execute_staged_action's fallback branch keys off of.
  4. update_listing_inventory() is a pure passthrough PUT -- doesn't mutate
     the caller's dict shape, just forwards it.

Run: python tests/test_etsy_inventory_price_update.py
"""
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools", ROOT):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import etsy_api  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _make_client() -> "etsy_api.EtsyAPIClient":
    c = etsy_api.EtsyAPIClient(api_key="test-key", access_token="fake-token")
    c.client_id = "test-client-id"
    c.client_secret = "test-client-secret"
    c.shop_id = "12345"
    return c


def test_update_price_via_inventory_updates_every_offering():
    client = _make_client()
    inventory = {
        "products": [
            {"sku": "SKU1", "offerings": [{"offering_id": 1, "price": 5.99, "quantity": 999, "is_enabled": True}]},
        ],
        "price_on_property": [],
        "quantity_on_property": [],
        "sku_on_property": [],
    }
    calls = []

    def fake_request(method, path, params=None, body=None):
        calls.append((method, path, body))
        if method == "GET":
            return inventory
        return {"products": body["products"]}

    with mock.patch.object(client, "_request", side_effect=fake_request):
        result = client.update_price_via_inventory(4519185019, 4.99)

    check(calls[0] == ("GET", "listings/4519185019/inventory", None), f"expected a GET of the real inventory first, got: {calls[0]}")
    check(calls[1][0] == "PUT" and calls[1][1] == "listings/4519185019/inventory", f"expected a PUT back to the same endpoint, got: {calls[1]}")
    put_body = calls[1][2]
    check(put_body["products"][0]["offerings"][0]["price"] == 4.99, f"price not updated in the PUT body: {put_body}")
    check(put_body["products"][0]["sku"] == "SKU1", f"unrelated fields must be preserved verbatim: {put_body}")
    check(put_body["products"][0]["offerings"][0]["quantity"] == 999, f"quantity must be preserved, not touched: {put_body}")
    check(result == {"products": put_body["products"]}, f"should return whatever the PUT call returns: {result}")


def test_update_price_via_inventory_updates_all_products_and_offerings():
    client = _make_client()
    inventory = {
        "products": [
            {"sku": "A", "offerings": [{"offering_id": 1, "price": 5.99, "quantity": 10}, {"offering_id": 2, "price": 6.99, "quantity": 5}]},
            {"sku": "B", "offerings": [{"offering_id": 3, "price": 7.99, "quantity": 20}]},
        ],
        "price_on_property": [111],
        "quantity_on_property": [222],
        "sku_on_property": [333],
    }

    def fake_request(method, path, params=None, body=None):
        if method == "GET":
            return inventory
        return body

    with mock.patch.object(client, "_request", side_effect=fake_request):
        client.update_price_via_inventory(999, 9.99)

    for product in inventory["products"]:
        for offering in product["offerings"]:
            check(offering["price"] == 9.99, f"every offering across every product must be updated, got: {inventory}")


def test_update_price_via_inventory_preserves_property_arrays():
    client = _make_client()
    inventory = {
        "products": [{"sku": "A", "offerings": [{"offering_id": 1, "price": 1.0}]}],
        "price_on_property": [111],
        "quantity_on_property": [222],
        "sku_on_property": [333],
    }
    captured = {}

    def fake_request(method, path, params=None, body=None):
        if method == "GET":
            return inventory
        captured["body"] = body
        return {}

    with mock.patch.object(client, "_request", side_effect=fake_request):
        client.update_price_via_inventory(999, 2.0)

    check(captured["body"]["price_on_property"] == [111], f"price_on_property must be forwarded unchanged: {captured['body']}")
    check(captured["body"]["quantity_on_property"] == [222], f"quantity_on_property must be forwarded unchanged: {captured['body']}")
    check(captured["body"]["sku_on_property"] == [333], f"sku_on_property must be forwarded unchanged: {captured['body']}")


def test_no_inventory_products_raises_matchable_error():
    client = _make_client()
    with mock.patch.object(client, "_request", return_value={"products": []}):
        try:
            client.update_price_via_inventory(4519185019, 4.99)
            check(False, "must raise when the listing has zero inventory products")
        except etsy_api.EtsyAPIError as exc:
            check("no inventory products" in str(exc), f"error message must be matchable by callers deciding whether to fall back, got: {exc}")


def test_update_listing_inventory_is_a_pure_passthrough_put():
    client = _make_client()
    payload = {"products": [{"sku": "X"}], "price_on_property": [], "quantity_on_property": [], "sku_on_property": []}
    with mock.patch.object(client, "_request", return_value={"ok": True}) as m:
        result = client.update_listing_inventory(4519185019, payload)
    m.assert_called_once_with("PUT", "listings/4519185019/inventory", body=payload)
    check(result == {"ok": True}, f"should return whatever the client returns, got: {result}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("ETSY INVENTORY PRICE UPDATE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("ETSY INVENTORY PRICE UPDATE TESTS OK — update_price_via_inventory() correctly reads the full "
          "inventory, updates price on every offering across every product, preserves every unrelated "
          "field verbatim (a partial PUT would delete missing products per Etsy's own confirmed "
          "behavior), and raises a matchable error for a listing with no inventory products so the "
          "caller can fall back deliberately instead of guessing.")


if __name__ == "__main__":
    run()
