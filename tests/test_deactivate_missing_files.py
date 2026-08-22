#!/usr/bin/env python3
"""
Tests for tools/deactivate_missing_files.py -- the script that deactivates
ACTIVE digital listings with no hard file behind them (per Scott's request,
"Deactivate all digital listings that we do not have hard files for").

Deliberately does NOT re-verify tools/audit_product_files.py's own
classification logic (that already has no dedicated test file and is out of
scope here) -- these tests inject a fake audit_result to isolate run()'s own
behavior: does it correctly no-op on dry run, correctly call
update_listing(state="inactive") only for genuinely_missing targets, correctly
update the local catalog only on a successful Etsy call, and correctly
distinguish success from failure per listing without one failure blocking
the rest of the batch.

Run: python tests/test_deactivate_missing_files.py
"""
import json
import sys
import tempfile
import traceback
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools", ROOT):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import os
os.environ.setdefault("APP_SECRET_TOKEN", "deactivate-test-not-a-real-secret")
os.environ.setdefault("DB_PATH", str(ROOT / "data" / "hub.db"))

import deactivate_missing_files as dmf  # noqa: E402
from etsy_api import EtsyAPIError  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_audit_result(targets: list[dict], verified_live_count: int = 0, skipped: list | None = None) -> dict:
    return {
        "genuinely_missing": targets,
        "verified_live": [{"product_id": f"VL{i}"} for i in range(verified_live_count)],
        "skipped": skipped or [],
    }


def _tmp_catalog(entries: list[dict]) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir=str(ROOT / "tests"))
    json.dump(entries, f)
    f.close()
    return Path(f.name)


def test_dry_run_makes_no_etsy_calls_and_no_catalog_writes():
    catalog_path = _tmp_catalog([
        {"product_id": "DP9001", "status": "active", "category": "wall_art"},
    ])
    targets = [{"product_id": "DP9001", "listing_id": 111, "title": "Broken Listing", "category": "wall_art"}]
    audit_result = _fake_audit_result(targets)

    mock_client = mock.MagicMock()
    result = dmf.run(execute=False, client=mock_client, catalog_path=catalog_path, audit_result=audit_result)

    check(result["executed"] is False, "dry run must report executed=False")
    check(len(result["deactivated"]) == 1 and result["deactivated"][0]["dry_run"] is True,
          f"dry run should list the target with dry_run=True, got: {result['deactivated']}")
    check(not mock_client.update_listing.called, "a dry run must never call update_listing()")

    catalog_after = json.loads(catalog_path.read_text())
    check(catalog_after[0]["status"] == "active",
          f"dry run must not touch the local catalog, got status: {catalog_after[0]['status']}")
    catalog_path.unlink()


def test_execute_deactivates_on_etsy_and_updates_local_catalog():
    catalog_path = _tmp_catalog([
        {"product_id": "DP9002", "status": "active", "category": "coloring_pages", "files": []},
    ])
    targets = [{"product_id": "DP9002", "listing_id": 222, "title": "Ghost Listing", "category": "coloring_pages"}]
    audit_result = _fake_audit_result(targets)

    mock_client = mock.MagicMock()
    result = dmf.run(execute=True, client=mock_client, catalog_path=catalog_path, audit_result=audit_result)

    check(mock_client.update_listing.called, "execute must call update_listing()")
    call_args = mock_client.update_listing.call_args
    check(call_args.args[0] == 222, f"expected listing_id 222, got {call_args.args}")
    check(call_args.args[1] == {"state": "inactive"},
          f"must PATCH state=inactive, got: {call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs}")
    check(len(result["deactivated"]) == 1 and len(result["failed"]) == 0,
          f"expected 1 success 0 failures, got: {result}")

    catalog_after = json.loads(catalog_path.read_text())
    check(catalog_after[0]["status"] == "inactive",
          f"execute must flip the local catalog status to inactive, got: {catalog_after[0]['status']}")
    check("Auto-deactivated" in catalog_after[0].get("note", ""),
          f"execute should leave an explanatory note on the catalog entry, got: {catalog_after[0].get('note')}")
    catalog_path.unlink()


def test_execute_records_failure_without_touching_catalog_for_that_product():
    catalog_path = _tmp_catalog([
        {"product_id": "DP9003", "status": "active", "category": "sticker_pack"},
    ])
    targets = [{"product_id": "DP9003", "listing_id": 333, "title": "Ghost Listing 2", "category": "sticker_pack"}]
    audit_result = _fake_audit_result(targets)

    mock_client = mock.MagicMock()
    mock_client.update_listing.side_effect = EtsyAPIError(403, "auth expired")
    result = dmf.run(execute=True, client=mock_client, catalog_path=catalog_path, audit_result=audit_result)

    check(len(result["failed"]) == 1 and len(result["deactivated"]) == 0,
          f"expected the failure recorded and NOT counted as deactivated, got: {result}")
    check("auth expired" in result["failed"][0]["error"], f"expected the real error surfaced, got: {result['failed'][0]}")

    catalog_after = json.loads(catalog_path.read_text())
    check(catalog_after[0]["status"] == "active",
          f"a failed Etsy call must leave the local catalog status untouched, got: {catalog_after[0]['status']}")
    catalog_path.unlink()


def test_one_failure_does_not_block_other_targets_in_the_batch():
    catalog_path = _tmp_catalog([
        {"product_id": "DP9004", "status": "active", "category": "wall_art"},
        {"product_id": "DP9005", "status": "active", "category": "wall_art"},
    ])
    targets = [
        {"product_id": "DP9004", "listing_id": 444, "title": "Fails", "category": "wall_art"},
        {"product_id": "DP9005", "listing_id": 555, "title": "Succeeds", "category": "wall_art"},
    ]
    audit_result = _fake_audit_result(targets)

    mock_client = mock.MagicMock()

    def _side_effect(listing_id, updates):
        if listing_id == 444:
            raise EtsyAPIError(500, "transient")
        return {}

    mock_client.update_listing.side_effect = _side_effect
    result = dmf.run(execute=True, client=mock_client, catalog_path=catalog_path, audit_result=audit_result)

    check(len(result["failed"]) == 1 and result["failed"][0]["product_id"] == "DP9004",
          f"expected exactly the failing product recorded, got: {result['failed']}")
    check(len(result["deactivated"]) == 1 and result["deactivated"][0]["product_id"] == "DP9005",
          f"expected the succeeding product recorded, got: {result['deactivated']}")

    catalog_after = {p["product_id"]: p for p in json.loads(catalog_path.read_text())}
    check(catalog_after["DP9004"]["status"] == "active", "the failed product's catalog entry must stay active")
    check(catalog_after["DP9005"]["status"] == "inactive", "the succeeding product's catalog entry must flip to inactive")
    catalog_path.unlink()


def test_no_targets_makes_no_calls_and_writes_nothing():
    catalog_path = _tmp_catalog([{"product_id": "DP9006", "status": "active"}])
    audit_result = _fake_audit_result([], verified_live_count=3)

    mock_client = mock.MagicMock()
    result = dmf.run(execute=True, client=mock_client, catalog_path=catalog_path, audit_result=audit_result)

    check(result["deactivated"] == [] and result["failed"] == [],
          f"no genuinely_missing targets should mean nothing happens, got: {result}")
    check(not mock_client.update_listing.called, "no targets means update_listing() should never be called")
    check(result["verified_live_untouched"] == 3, "verified_live count should pass through for visibility")
    catalog_path.unlink()


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ran = 0
    for t in tests:
        try:
            t()
            ran += 1
        except Exception:
            _failures.append(f"{t.__name__} raised an unexpected error:\n" + traceback.format_exc())
    if _failures:
        print("DEACTIVATE MISSING FILES TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"DEACTIVATE MISSING FILES TESTS OK — {ran} tests passed (dry run makes no live calls, --execute "
          f"deactivates only genuinely-missing listings and syncs the local catalog only on Etsy success, "
          f"one failure never blocks the rest of the batch -- no live Etsy call).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
