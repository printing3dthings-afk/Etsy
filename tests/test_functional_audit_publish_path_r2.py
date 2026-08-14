"""
ROUND 2 functional-correctness audit of the "publish a real Etsy listing"
pipeline:
  - _publish_digital_listing   (tools/etsy_listing_tools.py)
  - _attach_digital_file       (tools/etsy_listing_tools.py)
  - set_listing_state          (tools/api_server/main.py, POST /api/listings/{id}/state)

Round 1 (tests/test_functional_audit_publish_path.py) already confirmed and
verified-fixed: malformed-response success=True bug, FileContentError
propagating unhandled, confirm-flag gating, unknown-product rejection, QC gate
blocking, happy-path record consistency, genuine EtsyAPIError leaving no
phantom record, attach rejecting unlisted/placeholder products, attach using
the exact registered file, and set_listing_state's invalid-state/foreign-id/
retry-bound behavior.

This round looks for something NEW: whether _publish_digital_listing is safe
to call a SECOND time against a product that has already been published once
(status flipped back to "approved" with an etsy_listing_id already on
record -- a real, reachable state; see run_wall_art_workflow.py's Step 1,
which unconditionally sets p['status'] = 'approved' for every product in its
WALL_ART list with no check for an existing etsy_listing_id, and would do
exactly this on a re-run or on a product resubmitted for edits after its
first publish).

EtsyAPIClient is mocked entirely at every call site -- no real network call is
ever made. This is a READ-testing audit: no application code is modified.
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_publish_path_r2_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT, ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import tools.etsy_listing_tools as listing_tools  # noqa: E402
import tools.etsy_api as tools_etsy_api  # noqa: E402
import tools.data_store as tools_data_store  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fresh_store(tmpdir: str):
    shop_data_path = os.path.join(tmpdir, "shop_data.json")
    tools_data_store.SHOP_DATA_FILE = shop_data_path
    tools_data_store.DataStore._instance = None
    store = tools_data_store.DataStore()
    return store


def _make_product(pid: str, file_path: str, **overrides) -> dict:
    product = {
        "id": pid,
        "title": f"{pid} Test Product",
        "product_type": "wall_art",
        "status": "approved",
        "qc_status": "approved",
        "spec_check_result": "PASS",
        "is_placeholder": False,
        "file_path": file_path,
        "listing_draft": {
            "title": "A" * 40 + " Printable Wall Art, Instant Download, Boho Decor" + "z" * 40,
            "description": "D" * 320,
            "tags": [f"tag{i} phrase" for i in range(13)],
            "price": 7.99,
            "quantity": 999,
            "taxonomy_id": 2097,
        },
    }
    product.update(overrides)
    return product


# ── _publish_digital_listing — re-publish / duplicate-listing scenario ──────

def test_republish_already_listed_product_creates_duplicate_etsy_listing():
    """CONFIRMED BUG: _publish_digital_listing gates ONLY on
    product.status == "approved" plus the QC fields. It never checks whether
    the product already carries a real etsy_listing_id from a prior
    successful publish. If anything resets status back to "approved" while
    etsy_listing_id is still populated -- exactly what run_wall_art_
    workflow.py's Step 1 does unconditionally, with no existing-listing
    guard, for every product id in its WALL_ART list -- a second call
    happily calls client.create_listing() again, creating a SECOND real,
    billable Etsy listing for a product the shop already sells once.

    Worse than just a duplicate: the product record's single etsy_listing_id
    field gets silently overwritten with the NEW id, so the original listing
    id (111111 below) is dropped from the product record entirely -- Frank
    loses all ability to find, fix, or deactivate that first listing ever
    again. It stays live on Etsy, unlisted in any local catalog, silently
    orphaned. Meanwhile _add_to_main_listings unconditionally APPENDS
    (never replaces), so store["listings"] now carries two separate rows for
    the same digital_product_id -- one for each real Etsy listing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _fresh_store(tmpdir)
        f = os.path.join(tmpdir, "DPX.pdf")
        with open(f, "wb") as fh:
            fh.write(b"%PDF-1.4 fake")

        # Simulate: product was already published once (etsy_listing_id set,
        # status flipped to "listed" by a prior successful publish) and then
        # something (a workflow re-run, a resubmission-for-edits flow) reset
        # status back to "approved" without clearing etsy_listing_id.
        product = _make_product(
            "DPX", f,
            status="approved",
            etsy_listing_id="111111",
            listed_at="2026-01-01",
        )
        store.set([product], "digital_products")
        # Also simulate the main-listings record the first publish created.
        store.set([{
            "id": "DL111111",
            "etsy_listing_id": "111111",
            "digital_product_id": "DPX",
            "title": "original title",
            "price": 7.99,
            "quantity": 999,
            "views": 0, "favorites": 0, "sales": 0,
            "tags": [], "category": "Digital Downloads", "status": "active",
            "processing_days": 0, "description": "orig", "type": "digital",
            "listed_at": "2026-01-01",
        }], "listings")
        store.save()

        class FakeClientSecondPublish:
            def __init__(self, *a, **kw):
                self.access_token = "fake-token"

            def create_listing(self, listing_data):
                # A genuinely new Etsy listing id, distinct from the
                # product's existing 111111.
                return {"listing_id": 222222}

        with patch.object(listing_tools, "EtsyAPIClient", FakeClientSecondPublish), \
             patch.object(listing_tools, "is_configured", lambda: True):
            result = json.loads(
                listing_tools._publish_digital_listing({"product_id": "DPX", "confirm": True}, store)
            )

        saved = store.get("digital_products", default=[])[0]
        listings = store.get("listings", default=[])

        duplicate_created = (
            result.get("success") is True
            and result.get("etsy_listing_id") == "222222"
        )
        old_id_lost = saved.get("etsy_listing_id") == "222222"  # 111111 overwritten, not preserved
        dup_row_count = sum(1 for l in listings if l.get("digital_product_id") == "DPX")

        check(
            not duplicate_created,
            "CONFIRMED BUG: _publish_digital_listing has no guard against "
            "re-publishing a product that already carries a real "
            "etsy_listing_id ('111111'). It happily called create_listing() "
            "again and reported success=True with a brand-new listing id "
            f"('222222'), meaning a genuine duplicate live Etsy listing now "
            f"exists for product DPX. Full result: {result}",
        )
        check(
            not old_id_lost,
            "CONFIRMED BUG: the product record's original etsy_listing_id "
            "('111111') was silently overwritten by the second publish's "
            f"new id ('222222') with no trace left anywhere on the product "
            f"record -- Frank can no longer find, fix, or deactivate the "
            f"first live listing. saved.etsy_listing_id={saved.get('etsy_listing_id')!r}",
        )
        check(
            dup_row_count <= 1,
            "CONFIRMED BUG: _add_to_main_listings unconditionally appends a "
            "new row instead of checking for/replacing an existing row for "
            f"the same digital_product_id -- store['listings'] now has "
            f"{dup_row_count} rows for digital_product_id='DPX' (one per "
            "real Etsy listing), not the 1 a single logical product should "
            f"ever have. Rows: {listings}",
        )


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT R2 TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print(
        "FUNCTIONAL AUDIT R2 TESTS OK -- publish path is safe against "
        "re-publishing an already-listed product."
    )


if __name__ == "__main__":
    run()
