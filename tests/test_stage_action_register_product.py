"""
Tests for stage_action's new action_type='register_product' path (2026-08-14).

CLAUDE.md's Listing Agent Workflow says: "For a product whose files/photos
already exist outside this pipeline (e.g. a physical/manually-produced
item), use `register_product` instead to register it into the catalog
first." register_product was already a real, fully-supported staged-action
type on the backend (_validate_staged_action's register_product branch,
_execute_register_product_staged_action) -- but stage_action's action_type
enum never included it, and its input_schema had no product_id/name/
category/etsy_listing_id fields, so Claude had no tool-call path to ever
select it. Fixed by adding a dedicated early branch in _execute_agent_tool's
stage_action dispatch that builds register_product's real payload shape
(distinct from every other action_type's listing_id-centric payload) and
routes through the same _validate_staged_action/db.enqueue_action pair the
Create-screen's register_product_directly route uses.

Checks:
  1. A well-formed register_product call stages successfully with an
     auto-generated product_id (3d_print_physical -> P3D-prefixed slug).
  2. An explicit product_id is honored instead of being auto-generated.
  3. Missing name is refused (matches _validate_staged_action's own gate).
  4. An invalid category is refused.
  5. A duplicate product_id (already in the catalog) is refused.
  6. The staged action's payload is exactly the register_product shape
     (product_id, name, category, price, etsy_listing_id) -- no leftover
     listing_id-centric fields (title/tags/description/new_state/sku/
     taxonomy_id) leak in from the shared dispatch code path.

Run: python3 tests/test_stage_action_register_product.py
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_register_product_stage_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "register-product-stage-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _no_catalog_collision(_product_id):
    return None  # never a pre-existing catalog entry, unless a test overrides it


def test_register_product_stages_with_auto_product_id():
    with patch.object(server, "_find_catalog_product", side_effect=_no_catalog_collision):
        result = server._execute_agent_tool("stage_action", {
            "action_type": "register_product", "summary": "Register new koozie SKU",
            "name": "Silk PLA Koozie — Sunset Fade", "category": "3d_print_physical",
            "price": 14.99,
        })
    check(result.get("staged") is True, f"expected a successful stage, got: {result}")
    aid = result.get("action_id")
    pending = server.db.list_actions("pending")
    match = next((a for a in pending if a.get("id") == aid), None)
    check(match is not None, f"staged action {aid} should be in the pending queue")
    if match:
        check(match["type"] == "register_product", f"expected type register_product, got: {match['type']}")
        payload = match["payload"]
        check(bool(payload.get("product_id")) and payload["product_id"].startswith("P3D"),
              f"3d_print_physical should get an auto-generated P3D-prefixed product_id, got: {payload}")
        check(payload.get("name") == "Silk PLA Koozie — Sunset Fade", f"name mismatch: {payload}")
        check(payload.get("category") == "3d_print_physical", f"category mismatch: {payload}")
        check(payload.get("price") == 14.99, f"price mismatch: {payload}")


def test_register_product_honors_explicit_product_id():
    with patch.object(server, "_find_catalog_product", side_effect=_no_catalog_collision):
        result = server._execute_agent_tool("stage_action", {
            "action_type": "register_product", "summary": "Register WA1099",
            "product_id": "WA1099", "name": "Sunset Mountain Print",
            "category": "wall_art", "price": 6.99,
        })
    check(result.get("staged") is True, f"expected a successful stage, got: {result}")
    pending = server.db.list_actions("pending")
    match = next((a for a in pending if a.get("id") == result.get("action_id")), None)
    check(match is not None and match["payload"].get("product_id") == "WA1099",
          f"explicit product_id must be honored as-is, got: {match}")


def test_register_product_missing_name_refused():
    with patch.object(server, "_find_catalog_product", side_effect=_no_catalog_collision):
        result = server._execute_agent_tool("stage_action", {
            "action_type": "register_product", "summary": "no name given",
            "category": "3d_print_physical", "price": 9.99,
        })
    check(result.get("staged") is not True, f"missing name must be refused, got: {result}")
    check("error" in result, f"expected an error message, got: {result}")


def test_register_product_invalid_category_refused():
    with patch.object(server, "_find_catalog_product", side_effect=_no_catalog_collision):
        result = server._execute_agent_tool("stage_action", {
            "action_type": "register_product", "summary": "bad category",
            "name": "Mystery Item", "category": "not_a_real_category", "price": 9.99,
        })
    check(result.get("staged") is not True, f"invalid category must be refused, got: {result}")
    check("error" in result, f"expected an error message, got: {result}")


def test_register_product_duplicate_product_id_refused():
    def _collision(product_id):
        return {"product_id": product_id} if product_id == "WA1050" else None

    with patch.object(server, "_find_catalog_product", side_effect=_collision):
        result = server._execute_agent_tool("stage_action", {
            "action_type": "register_product", "summary": "duplicate",
            "product_id": "WA1050", "name": "Already Exists", "category": "wall_art", "price": 6.99,
        })
    check(result.get("staged") is not True, f"a colliding product_id must be refused, got: {result}")
    check("error" in result, f"expected an error message, got: {result}")


def test_register_product_payload_has_no_listing_centric_fields():
    with patch.object(server, "_find_catalog_product", side_effect=_no_catalog_collision):
        result = server._execute_agent_tool("stage_action", {
            "action_type": "register_product", "summary": "shape check",
            "product_id": "WA1077", "name": "Ocean Waves Print",
            "category": "wall_art", "price": 6.99,
        })
    check(result.get("staged") is True, f"expected a successful stage, got: {result}")
    pending = server.db.list_actions("pending")
    match = next((a for a in pending if a.get("id") == result.get("action_id")), None)
    check(match is not None, "staged action should be in the pending queue")
    if match:
        payload = match["payload"]
        leaked = [k for k in ("listing_id", "title", "tags", "description", "new_state",
                               "sku", "taxonomy_id", "_state_at_staging")
                  if k in payload]
        check(not leaked, f"register_product payload must not carry listing-mutation fields, "
                           f"found: {leaked} in {payload}")
        check(set(payload.keys()) == {"product_id", "name", "category", "price", "etsy_listing_id"},
              f"expected exactly the register_product shape, got keys: {sorted(payload.keys())}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("STAGE-ACTION REGISTER-PRODUCT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("STAGE-ACTION REGISTER-PRODUCT TESTS OK — Claude can now actually stage a "
          "register_product action through stage_action, matching CLAUDE.md's documented "
          "workflow, with the correct payload shape and the same validation guarantees as "
          "the Create-screen's manual form.")


if __name__ == "__main__":
    run()
