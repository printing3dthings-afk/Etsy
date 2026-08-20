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

**Second bug found and fixed the same day** (action #750, live listing
4519185019): the *shape* of that fix (read-full, mutate, write-full-back)
was correct, but the GET response and PUT request schemas are NOT
identical. Sending the GET response straight back failed with "Etsy API
400: Array contains invalid keys: product_id,is_deleted" -- Etsy's own
migration guidance confirms `product_id`, `offering_id`, `scale_name`,
`is_deleted`, and `value_pairs` are GET-response-only fields that the PUT
schema rejects outright. This test file's fixtures now use realistic GET
response shapes (including those exact fields, plus price as a Money
object -- {amount, divisor, currency_code} -- which GET returns and PUT
also does not accept as-is) specifically so a regression here reproduces
the real failure instead of a sanitized one that would have passed while
the real bug shipped.

Checks:
  1. update_price_via_inventory() reads the full inventory, strips every
     PUT-invalid field (product_id/is_deleted at the product level,
     offering_id/is_deleted at the offering level), and PUTs a clean
     structure -- price_on_property/quantity_on_property/sku_on_property
     preserved verbatim (those ARE valid at the top level).
  2. A listing with multiple products/offerings gets every single one
     updated to the new price (as a plain float, never the Money object
     shape), not just the first.
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


def _real_shaped_offering(offering_id, price_amount, quantity):
    """A GET-response-shaped offering -- price as a Money object, plus the
    offering_id/is_deleted fields that are real but PUT-invalid."""
    return {
        "offering_id": offering_id,
        "quantity": quantity,
        "is_enabled": True,
        "is_deleted": False,
        "price": {"amount": price_amount, "divisor": 100, "currency_code": "USD"},
    }


def test_update_price_via_inventory_strips_put_invalid_fields():
    client = _make_client()
    inventory = {
        "products": [
            {
                "product_id": 111222333,
                "sku": "SKU1",
                "is_deleted": False,
                "offerings": [_real_shaped_offering(999888777, 599, 999)],
            },
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
    put_product = calls[1][2]["products"][0]
    check("product_id" not in put_product, f"product_id must be stripped (PUT-invalid), got: {put_product}")
    check("is_deleted" not in put_product, f"is_deleted must be stripped from the product (PUT-invalid), got: {put_product}")
    check(put_product["sku"] == "SKU1", f"unrelated valid fields must be preserved verbatim: {put_product}")
    put_offering = put_product["offerings"][0]
    check("offering_id" not in put_offering, f"offering_id must be stripped (PUT-invalid), got: {put_offering}")
    check("is_deleted" not in put_offering, f"is_deleted must be stripped from the offering (PUT-invalid), got: {put_offering}")
    check(put_offering["price"] == 4.99, f"price must be a plain float, not the Money object, got: {put_offering}")
    check(put_offering["quantity"] == 999, f"quantity must be preserved, not touched: {put_offering}")
    check(result == {"products": calls[1][2]["products"]}, f"should return whatever the PUT call returns: {result}")


def test_update_price_via_inventory_updates_all_products_and_offerings():
    client = _make_client()
    inventory = {
        "products": [
            {
                "product_id": 1, "sku": "A", "is_deleted": False,
                "offerings": [_real_shaped_offering(10, 599, 10), _real_shaped_offering(11, 699, 5)],
            },
            {
                "product_id": 2, "sku": "B", "is_deleted": False,
                "offerings": [_real_shaped_offering(12, 799, 20)],
            },
        ],
        "price_on_property": [111],
        "quantity_on_property": [222],
        "sku_on_property": [333],
    }
    captured = {}

    def fake_request(method, path, params=None, body=None):
        if method == "GET":
            return inventory
        captured["body"] = body
        return body

    with mock.patch.object(client, "_request", side_effect=fake_request):
        client.update_price_via_inventory(999, 9.99)

    for product in captured["body"]["products"]:
        for offering in product["offerings"]:
            check(offering["price"] == 9.99, f"every offering across every product must be updated, got: {captured['body']}")
    check(captured["body"]["price_on_property"] == [111], f"price_on_property must be forwarded unchanged: {captured['body']}")
    check(captured["body"]["quantity_on_property"] == [222], f"quantity_on_property must be forwarded unchanged: {captured['body']}")
    check(captured["body"]["sku_on_property"] == [333], f"sku_on_property must be forwarded unchanged: {captured['body']}")
    # The original GET response object must be untouched -- confirms the fix builds a
    # fresh cleaned structure rather than mutating (and thereby corrupting) the GET result.
    check(inventory["products"][0]["offerings"][0]["price"] == {"amount": 599, "divisor": 100, "currency_code": "USD"},
          f"the original GET response must not be mutated in place: {inventory}")


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
          "inventory, strips every PUT-invalid field (product_id/offering_id/is_deleted) instead of "
          "echoing the raw GET response back, converts price to a plain float on every offering across "
          "every product (never the Money object shape), preserves every other valid field verbatim (a "
          "partial PUT would delete missing products per Etsy's own confirmed behavior), never mutates "
          "the original GET response in place, and raises a matchable error for a listing with no "
          "inventory products so the caller can fall back deliberately instead of guessing.")


if __name__ == "__main__":
    run()
