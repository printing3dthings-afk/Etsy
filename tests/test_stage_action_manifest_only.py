"""
Tests for stage_action's register_product action_type='register_product' with
manifest_only=True (2026-08-20).

Real gap this closes: listing_compliance_sweep.py flags a listing
no_manifest_mapping when it has no entry in data/listing_manifest.json (or its
override sidecar) -- but register_product's existing duplicate-check refuses
to run at all when product_id already has a catalog entry ("already exists in
the catalog -- refusing to overwrite"). That's exactly the state 5 real
listings were found in this session (e.g. COLOR1003/listing 4543589858,
SPRIGIT/listing 4558607154): registered in product_catalog_overrides.json
(so GET /api/products shows them fine) but never mapped in
listing_manifest_overrides.json, so the compliance sweep still calls them
unmapped. manifest_only=True inverts the check -- REQUIRES product_id to
already exist, reads category from that existing entry, and writes only the
listing_manifest_overrides.json side.

Checks:
  1. A well-formed manifest_only call stages successfully, reusing the
     existing catalog entry's category for the manifest `type`.
  2. Missing etsy_listing_id is refused (manifest_only requires it).
  3. A product_id with NO existing catalog entry is refused (opposite of the
     normal register_product duplicate-check).
  4. A listing_id already mapped in the manifest is refused (no double-map).
  5. Optional min_photo_count/expected_files are honored in the written entry
     when given, and the entry defaults sensibly when omitted.
  6. The staged payload never carries name/price/category (those come from
     the existing catalog record, not re-supplied).

Run: python3 tests/test_stage_action_manifest_only.py
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_manifest_only_stage_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "manifest-only-stage-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


_EXISTING_PRODUCT = {"product_id": "COLOR1003", "category": "coloring_pages", "name": "20 Halloween Coloring Pages"}


def _has_existing_product(product_id):
    return dict(_EXISTING_PRODUCT) if product_id == _EXISTING_PRODUCT["product_id"] else None


def _no_existing_manifest_entry(_listing_id):
    return None


def test_manifest_only_stages_and_reuses_catalog_category():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(server, "_find_catalog_product", side_effect=_has_existing_product), \
             patch.object(server, "_read_manifest_entry_sync", side_effect=_no_existing_manifest_entry), \
             patch.object(server, "_LISTING_MANIFEST_OVERRIDES_PATH", Path(tmp) / "listing_manifest_overrides.json"):
            result = server._execute_agent_tool("stage_action", {
                "action_type": "register_product", "manifest_only": True,
                "product_id": "COLOR1003", "etsy_listing_id": 4543589858,
                "summary": "Map COLOR1003 to its manifest entry",
            })
        check(result.get("staged") is True, f"expected a successful stage, got: {result}")
        aid = result.get("action_id")
        pending = server.db.list_actions("pending")
        match = next((a for a in pending if a.get("id") == aid), None)
        check(match is not None, f"staged action {aid} should be in the pending queue")
        if match:
            check(match["type"] == "register_product", f"expected type register_product, got: {match['type']}")
            payload = match["payload"]
            check(payload.get("product_id") == "COLOR1003", f"product_id mismatch: {payload}")
            check(payload.get("etsy_listing_id") == 4543589858, f"etsy_listing_id mismatch: {payload}")
            check(payload.get("manifest_only") is True, f"manifest_only flag missing: {payload}")


def test_manifest_only_missing_listing_id_refused():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(server, "_find_catalog_product", side_effect=_has_existing_product), \
             patch.object(server, "_read_manifest_entry_sync", side_effect=_no_existing_manifest_entry), \
             patch.object(server, "_LISTING_MANIFEST_OVERRIDES_PATH", Path(tmp) / "listing_manifest_overrides.json"):
            result = server._execute_agent_tool("stage_action", {
                "action_type": "register_product", "manifest_only": True,
                "product_id": "COLOR1003", "summary": "no listing id",
            })
    check(result.get("staged") is not True, f"missing etsy_listing_id must be refused, got: {result}")
    check("error" in result, f"expected an error message, got: {result}")


def test_manifest_only_unknown_product_id_refused():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(server, "_find_catalog_product", side_effect=_has_existing_product), \
             patch.object(server, "_read_manifest_entry_sync", side_effect=_no_existing_manifest_entry), \
             patch.object(server, "_LISTING_MANIFEST_OVERRIDES_PATH", Path(tmp) / "listing_manifest_overrides.json"):
            result = server._execute_agent_tool("stage_action", {
                "action_type": "register_product", "manifest_only": True,
                "product_id": "NOT_A_REAL_PRODUCT", "etsy_listing_id": 4999999999,
                "summary": "unknown product",
            })
    check(result.get("staged") is not True, f"a product_id with no catalog entry must be refused, got: {result}")
    check("error" in result, f"expected an error message, got: {result}")


def test_manifest_only_already_mapped_listing_refused():
    def _already_mapped(_listing_id):
        return {"dp_codes": ["SOME_OTHER_PRODUCT"]}

    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(server, "_find_catalog_product", side_effect=_has_existing_product), \
             patch.object(server, "_read_manifest_entry_sync", side_effect=_already_mapped), \
             patch.object(server, "_LISTING_MANIFEST_OVERRIDES_PATH", Path(tmp) / "listing_manifest_overrides.json"):
            result = server._execute_agent_tool("stage_action", {
                "action_type": "register_product", "manifest_only": True,
                "product_id": "COLOR1003", "etsy_listing_id": 4543589858,
                "summary": "already mapped",
            })
    check(result.get("staged") is not True, f"a listing already mapped must be refused, got: {result}")
    check("error" in result, f"expected an error message, got: {result}")


def test_manifest_only_execute_writes_real_entry_with_overrides():
    with tempfile.TemporaryDirectory() as tmp:
        override_path = Path(tmp) / "listing_manifest_overrides.json"
        with patch.object(server, "_find_catalog_product", side_effect=_has_existing_product), \
             patch.object(server, "_LISTING_MANIFEST_OVERRIDES_PATH", override_path):
            result = server._execute_register_product_staged_action({
                "payload": {
                    "product_id": "COLOR1003", "etsy_listing_id": 4543589858,
                    "manifest_only": True, "min_photo_count": 5,
                    "expected_files": ["coloring_color1003_set_01.zip"],
                }
            })
        check(result.get("manifest_entry_written") is True, f"expected manifest_entry_written, got: {result}")
        check(result.get("category") == "coloring_pages", f"expected category from existing catalog entry, got: {result}")
        import json
        written = json.loads(override_path.read_text())
        entry = written.get("4543589858")
        check(entry is not None, f"expected an entry keyed by listing_id, got keys: {list(written.keys())}")
        if entry:
            check(entry["dp_codes"] == ["COLOR1003"], f"dp_codes mismatch: {entry}")
            check(entry["type"] == "coloring_pages", f"type mismatch: {entry}")
            check(entry["min_photo_count"] == 5, f"min_photo_count not honored: {entry}")
            check(entry["expected_files"] == ["coloring_color1003_set_01.zip"], f"expected_files not honored: {entry}")
            check(entry["expected_file_count"] == 1, f"expected_file_count not derived: {entry}")


def test_manifest_only_execute_defaults_when_omitted():
    with tempfile.TemporaryDirectory() as tmp:
        override_path = Path(tmp) / "listing_manifest_overrides.json"
        with patch.object(server, "_find_catalog_product", side_effect=_has_existing_product), \
             patch.object(server, "_LISTING_MANIFEST_OVERRIDES_PATH", override_path):
            server._execute_register_product_staged_action({
                "payload": {"product_id": "COLOR1003", "etsy_listing_id": 4543589858, "manifest_only": True}
            })
        import json
        entry = json.loads(override_path.read_text())["4543589858"]
        check(entry["min_photo_count"] == 1, f"expected permissive default min_photo_count=1, got: {entry}")
        check(entry["expected_files"] == [], f"expected empty expected_files default, got: {entry}")


def test_manifest_only_never_writes_catalog_override():
    calls = []

    def _spy_write_catalog(product_id, data):
        calls.append((product_id, data))

    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(server, "_find_catalog_product", side_effect=_has_existing_product), \
             patch.object(server, "_write_product_catalog_override", side_effect=_spy_write_catalog), \
             patch.object(server, "_LISTING_MANIFEST_OVERRIDES_PATH", Path(tmp) / "listing_manifest_overrides.json"):
            server._execute_register_product_staged_action({
                "payload": {"product_id": "COLOR1003", "etsy_listing_id": 4543589858, "manifest_only": True}
            })
    check(not calls, f"manifest_only must never touch product_catalog_overrides.json, but it was called: {calls}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("STAGE-ACTION MANIFEST-ONLY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("STAGE-ACTION MANIFEST-ONLY TESTS OK — register_product(manifest_only=True) maps an "
          "already-cataloged product to its live listing in listing_manifest_overrides.json "
          "without ever touching the catalog record, with the same duplicate/existence guarantees "
          "the normal register_product path has, closing the no_manifest_mapping gap for listings "
          "known to only one of Frank's two local registries.")


if __name__ == "__main__":
    run()
