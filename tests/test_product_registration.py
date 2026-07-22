"""
Tests for the new-product registration infrastructure (2026-07-22): Scott
reported that typing a genuinely new Wall Art or Coloring Pages code on the
Create screen could never actually build a real, reviewable product --
there was no mechanism anywhere in this codebase that could register a
wholly new product_id. Publishing an existing catalog entry to Etsy already
worked (create_listing/stage-publish), but nothing could introduce a NEW
entry that didn't already exist in data/product_catalog.json.

This tests the fix: _register_new_product_overlay() durably writes an
`is_new_product: true` record into the SAME overrides sidecar the existing
create_listing patch flow already uses, and _find_catalog_product() falls
back to it when the base catalog has no match -- which is what makes
GET /api/products/{id}/review and stage-publish work for a freshly-built
product with zero other code changes.

Self-contained TestClient-against-the-real-app pattern, same as
tests/test_produce_qc.py. Run: python tests/test_product_registration.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_productreg_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "product-registration-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_find_catalog_product_none_for_truly_unknown_pid():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "product_catalog_overrides.json"
        with patch.object(server, "_PRODUCT_CATALOG_OVERRIDES_PATH", fake_path):
            result = server._find_catalog_product("TOTALLY_MADE_UP_PID_12345")
    check(result is None, f"a pid with no base-catalog entry and no overlay must return None, got {result}")


def test_find_catalog_product_resolves_is_new_product_overlay():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "product_catalog_overrides.json"
        with patch.object(server, "_PRODUCT_CATALOG_OVERRIDES_PATH", fake_path):
            server._write_product_catalog_override("WA9001", {
                "is_new_product": True, "product_id": "WA9001", "name": "Test art",
                "category": "wall_art", "price": None, "status": "draft",
                "etsy_listing_id": "", "files": ["data/digital_products/print_zips/WA9001_print_sizes.zip"],
            })
            result = server._find_catalog_product("WA9001")
    check(result is not None, "a registered is_new_product pid must resolve")
    check(result.get("name") == "Test art", f"got: {result}")
    check(result.get("category") == "wall_art", f"got: {result}")
    check(result.get("status") == "draft", f"got: {result}")


def test_find_catalog_product_ignores_patch_only_overlay_for_unknown_pid():
    # A plain patch-only overlay entry (no is_new_product marker) for a pid
    # NOT in the base catalog must not be mistaken for a real product.
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "product_catalog_overrides.json"
        with patch.object(server, "_PRODUCT_CATALOG_OVERRIDES_PATH", fake_path):
            server._write_product_catalog_override("DP9999", {"etsy_listing_id": "1", "status": "listed_draft"})
            result = server._find_catalog_product("DP9999")
    check(result is None, f"a patch-only overlay entry for an unknown pid must not resolve as a product, got {result}")


def test_register_new_product_overlay_writes_expected_shape():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "product_catalog_overrides.json"
        with patch.object(server, "_PRODUCT_CATALOG_OVERRIDES_PATH", fake_path):
            server._register_new_product_overlay(
                "COLOR8001", "coloring_pages", "Sleepy fox theme", None,
                ["data/digital_products/coloring_pages/sets/coloring_color8001_set_01.zip"],
                "A sleepy fox under an oak tree",
            )
            overrides = server._product_catalog_overrides()
    entry = overrides.get("COLOR8001")
    check(entry is not None, f"expected an overlay entry, got {overrides}")
    check(entry.get("is_new_product") is True, f"got: {entry}")
    check(entry.get("status") == "draft", f"a freshly registered product must never be pre-published, got: {entry}")
    check(entry.get("etsy_listing_id") == "", f"a freshly registered product must have no listing id yet, got: {entry}")
    check(entry.get("category") == "coloring_pages", f"got: {entry}")
    check(entry.get("price") is None, f"price must be left blank (Scott's choice), got: {entry}")
    check(entry.get("source") == "create_screen_new_code", f"got: {entry}")
    check("created_at" in entry, f"got: {entry}")


def test_register_new_product_overlay_refuses_to_shadow_real_catalog_entry():
    # A pid collision with an existing REAL base-catalog product must never
    # silently get an is_new_product overlay welded on top.
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "product_catalog_overrides.json"
        with patch.object(server, "_PRODUCT_CATALOG_OVERRIDES_PATH", fake_path), \
             patch.object(server, "_find_catalog_product", return_value={"product_id": "DP1026"}):
            with patch.object(server, "_write_product_catalog_override") as mock_write:
                server._register_new_product_overlay("DP1026", "digital_planner", "x", None, [], "")
            check(not mock_write.called, "must never write an overlay for a pid that already resolves to a real product")


def test_register_new_product_overlay_is_idempotent_on_retry():
    # Calling this twice for the same already-registered pid (e.g. Scott taps
    # "Regenerate" later) must be a safe no-op the second time, not a clobber
    # or duplicate.
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "product_catalog_overrides.json"
        with patch.object(server, "_PRODUCT_CATALOG_OVERRIDES_PATH", fake_path):
            server._register_new_product_overlay("WA8002", "wall_art", "First name", None, ["a.zip"], "d1")
            server._register_new_product_overlay("WA8002", "wall_art", "Should not overwrite", None, ["b.zip"], "d2")
            overrides = server._product_catalog_overrides()
    check(overrides["WA8002"]["name"] == "First name",
          f"a second registration call for the same pid must not overwrite the first, got: {overrides['WA8002']}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PRODUCT REGISTRATION TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRODUCT REGISTRATION TESTS OK — _find_catalog_product() resolves is_new_product "
          "overlay entries, _register_new_product_overlay() writes the expected shape, "
          "never shadows a real catalog entry, and is idempotent on retry.")


if __name__ == "__main__":
    run()
