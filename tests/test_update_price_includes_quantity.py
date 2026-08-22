"""
Regression tests for the update_price silent-no-op bug (2026-08-20) --
covers both the disproven first fix and the confirmed real fix.

Real bug: a blanket price change was approved for 82 listings (71 wall-art
to $4.99, 11 coloring-pages to $1.99). Every one of the 82 staged actions
showed status="executed" with no recorded error -- but re-checking the real
live prices directly against Etsy's own public listings endpoint afterward
showed only 11 of 82 had actually changed.

First hypothesis (tried and DISPROVEN): sending {"price": X} alone was
silently dropped because quantity wasn't included in the same PATCH.
Fetching quantity and resending it alongside price was deployed and
independently re-tested against a real still-broken listing -- it also
failed. Kept only as the fallback path below, not the real fix.

Confirmed real root cause (via Etsy's own developer community -- the
etsy-api-v2 Google Group and etsy/open-api discussions #977/#691, with
Etsy staff responses): the top-level `price` field on updateListing is
silently ignored once a listing has a real Inventory API "offering"
record, which most listings created through the standard API flow have
even when has_variations=False. The correct path is the Inventory API:
read the full inventory, mutate price, write the whole structure back
(see EtsyAPIClient.update_price_via_inventory()).

update_price now tries the Inventory API path first and only falls back
to the legacy top-level-field-plus-quantity path if the listing genuinely
has no inventory products at all.

Checks:
  1. The primary path calls update_price_via_inventory(lid, price) and
     never touches get_listing()/update_listing() directly when it
     succeeds.
  2. If update_price_via_inventory raises "no inventory products",
     execution falls back to get_listing() + update_listing() with
     quantity included in the same PATCH (the original, disproven fix,
     preserved as the fallback path since it's cheap and can't hurt).
  3. The fallback still omits a fabricated quantity when the real value
     is 0 or missing.
  4. Any OTHER EtsyAPIError from update_price_via_inventory (a genuine
     network/5xx failure, not the specific "no products" case) propagates
     instead of being silently absorbed into the fallback.
  5. update_tags/update_title/etc. are unaffected -- they never call
     get_listing() or update_price_via_inventory, only update_price does.

Run: python3 tests/test_update_price_includes_quantity.py
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_update_price_quantity_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "update-price-quantity-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
from etsy_api import EtsyAPIError  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _make_client(quantity=999, inventory_error: str | None = None):
    client = MagicMock()
    client.get_listing.return_value = {"listing_id": 4519185019, "quantity": quantity, "state": "active"}
    client.update_listing.return_value = {"listing_id": 4519185019, "state": "active"}
    if inventory_error is not None:
        client.update_price_via_inventory.side_effect = EtsyAPIError(0, inventory_error)
    else:
        client.update_price_via_inventory.return_value = {"listing_id": 4519185019}
    return client


def test_update_price_prefers_inventory_api():
    client = _make_client()
    with patch.object(server, "EtsyAPIClient", return_value=client):
        server._execute_staged_action({
            "type": "update_price",
            "payload": {"listing_id": 4519185019, "price": 4.99},
        })
    check(client.update_price_via_inventory.called, "update_price must try the Inventory API path first")
    check(client.update_price_via_inventory.call_args[0] == (4519185019, 4.99),
          f"wrong args to update_price_via_inventory: {client.update_price_via_inventory.call_args}")
    check(not client.get_listing.called, "must not fetch via get_listing when the inventory path succeeds")
    check(not client.update_listing.called, "must not fall back to update_listing when the inventory path succeeds")


def test_update_price_falls_back_when_no_inventory_products():
    client = _make_client(quantity=999, inventory_error="listing 4519185019 has no inventory products -- not an offering-backed listing")
    with patch.object(server, "EtsyAPIClient", return_value=client):
        server._execute_staged_action({
            "type": "update_price",
            "payload": {"listing_id": 4519185019, "price": 4.99},
        })
    check(client.update_price_via_inventory.called, "must still try the inventory path first")
    check(client.get_listing.called, "a no-products failure must fall back to fetching the listing for quantity")
    check(client.update_listing.called, "a no-products failure must fall back to the legacy update_listing path")
    lid_arg, updates_arg = client.update_listing.call_args[0]
    check(lid_arg == 4519185019, f"update_listing called with wrong listing_id: {lid_arg}")
    check(updates_arg.get("price") == 4.99, f"price missing/wrong in fallback PATCH body: {updates_arg}")
    check(updates_arg.get("quantity") == 999, f"quantity missing/wrong in fallback PATCH body: {updates_arg}")


def test_fallback_omits_quantity_when_zero_or_missing():
    for bad_quantity in (0, None):
        client = _make_client(quantity=bad_quantity, inventory_error="listing X has no inventory products -- not an offering-backed listing")
        with patch.object(server, "EtsyAPIClient", return_value=client):
            server._execute_staged_action({
                "type": "update_price",
                "payload": {"listing_id": 4519185019, "price": 4.99},
            })
        updates_arg = client.update_listing.call_args[0][1]
        check("quantity" not in updates_arg,
              f"must not send a fabricated quantity when the real value is {bad_quantity!r}, got: {updates_arg}")
        check(updates_arg.get("price") == 4.99, f"price still must be set: {updates_arg}")


def test_other_inventory_errors_propagate_not_silently_absorbed():
    client = _make_client(inventory_error="Etsy API 503: server error")
    with patch.object(server, "EtsyAPIClient", return_value=client):
        try:
            server._execute_staged_action({
                "type": "update_price",
                "payload": {"listing_id": 4519185019, "price": 4.99},
            })
            check(False, "a genuine inventory-API failure (not 'no products') must propagate, not fall back silently")
        except Exception as exc:
            check("server error" in str(exc), f"expected the real error to propagate, got: {exc}")
    check(not client.get_listing.called, "must not fall back to the legacy path for a non-'no products' error")


def test_other_action_types_never_touch_inventory_or_get_listing():
    client = _make_client()
    with patch.object(server, "EtsyAPIClient", return_value=client):
        server._execute_staged_action({
            "type": "update_title",
            "payload": {"listing_id": 4519185019, "title": "New Title"},
        })
    check(not client.get_listing.called, "update_title must not fetch the listing first -- only update_price does")
    check(not client.update_price_via_inventory.called, "update_title must never touch the Inventory API")
    check(client.update_listing.call_args[0][1] == {"title": "New Title"}, f"unexpected PATCH body: {client.update_listing.call_args}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("UPDATE-PRICE INVENTORY-FIX TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("UPDATE-PRICE INVENTORY-FIX TESTS OK — update_price now routes through Etsy's Inventory API "
          "first (the confirmed real fix for the silent-no-op bug), falling back to the legacy "
          "top-level-price-plus-quantity path only when a listing genuinely has no inventory products, "
          "and never silently absorbs an unrelated Inventory API failure into that fallback.")


if __name__ == "__main__":
    run()
