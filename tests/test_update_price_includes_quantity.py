"""
Regression test for the update_price silent-no-op bug (2026-08-20).

Real bug: a blanket price change was approved for 82 listings (71 wall-art
to $4.99, 11 coloring-pages to $1.99). Every one of the 82 staged actions
showed status="executed" with no recorded error -- but re-checking the real
live prices directly against Etsy's own public listings endpoint afterward
showed only 11 of 82 had actually changed. A full re-stage + re-approve
retry of the remaining 71 failed identically the second time, ruling out a
transient blip. Every field the public listing endpoint exposes (has_
variations, skus, taxonomy_id, listing_type, state) was identical between a
listing that succeeded and one that silently didn't -- the PATCH body was
just {"price": X}, no quantity. Etsy's price lives on the same underlying
"offering" record as quantity; a PATCH that touches price without also
resending the listing's current quantity can be silently dropped at Etsy's
business-logic layer even though the HTTP request itself validates and
returns 200.

Fixed by having the update_price branch of _execute_staged_action() fetch
the listing's current quantity first and include it in the same PATCH.

Checks:
  1. The executor calls get_listing() before update_listing() for a price
     change (needs the current quantity).
  2. The PATCH body includes both price and the fetched quantity.
  3. A listing with quantity=0 or missing quantity doesn't get a bogus
     quantity=0 forced into the PATCH (only include when it's a real
     positive int -- matches "don't invent data you don't have").
  4. update_tags/update_title/etc. are unaffected -- they never call
     get_listing() first, only update_price does.

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

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _make_client(quantity):
    client = MagicMock()
    client.get_listing.return_value = {"listing_id": 4519185019, "quantity": quantity, "state": "active"}
    client.update_listing.return_value = {"listing_id": 4519185019, "state": "active"}
    return client


def test_update_price_fetches_quantity_and_includes_it():
    client = _make_client(999)
    with patch.object(server, "EtsyAPIClient", return_value=client):
        server._execute_staged_action({
            "type": "update_price",
            "payload": {"listing_id": 4519185019, "price": 4.99},
        })
    check(client.get_listing.called, "update_price must fetch the current listing (for quantity) before patching")
    check(client.get_listing.call_args[0][0] == 4519185019, f"get_listing called with wrong listing_id: {client.get_listing.call_args}")
    check(client.update_listing.called, "update_price must still call update_listing")
    lid_arg, updates_arg = client.update_listing.call_args[0]
    check(lid_arg == 4519185019, f"update_listing called with wrong listing_id: {lid_arg}")
    check(updates_arg.get("price") == 4.99, f"price missing/wrong in PATCH body: {updates_arg}")
    check(updates_arg.get("quantity") == 999, f"quantity missing/wrong in PATCH body: {updates_arg}")


def test_update_price_omits_quantity_when_zero_or_missing():
    for bad_quantity in (0, None):
        client = _make_client(bad_quantity)
        with patch.object(server, "EtsyAPIClient", return_value=client):
            server._execute_staged_action({
                "type": "update_price",
                "payload": {"listing_id": 4519185019, "price": 4.99},
            })
        updates_arg = client.update_listing.call_args[0][1]
        check("quantity" not in updates_arg,
              f"must not send a fabricated quantity when the real value is {bad_quantity!r}, got: {updates_arg}")
        check(updates_arg.get("price") == 4.99, f"price still must be set: {updates_arg}")


def test_other_action_types_never_call_get_listing():
    client = _make_client(999)
    with patch.object(server, "EtsyAPIClient", return_value=client):
        server._execute_staged_action({
            "type": "update_title",
            "payload": {"listing_id": 4519185019, "title": "New Title"},
        })
    check(not client.get_listing.called, "update_title must not fetch the listing first -- only update_price needs quantity")
    check(client.update_listing.call_args[0][1] == {"title": "New Title"}, f"unexpected PATCH body: {client.update_listing.call_args}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("UPDATE-PRICE QUANTITY-FIX TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("UPDATE-PRICE QUANTITY-FIX TESTS OK — update_price now fetches and resends the listing's "
          "current quantity alongside price, closing the silent-no-op bug that let 71 of 82 approved "
          "price changes report 'executed' while Etsy's real stored price never actually changed.")


if __name__ == "__main__":
    run()
