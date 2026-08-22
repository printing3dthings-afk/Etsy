"""
Tests for the Etsy Listing Files feature (2026-07-19): Scott corrected an
earlier misunderstanding -- he wants the Files tab to show every file
attached to the actual live Etsy listings, not Frank's own local/generated
file storage. Etsy's API can't hand back file bytes (confirmed against this
repo's own prior incidents, ops_runbook.md 2026-06-19/2026-06-20), so this
is a metadata inventory (tools/etsy_file_inventory.py) cross-referenced
against local storage for a real download where a same-named file happens to
exist (main.py's GET /api/etsy-files), refreshed daily via
_calendar_tasks_loop().

Checks:
  1. etsy_file_inventory.sweep() classification against a mocked EtsyAPIClient:
     active+listing_id gets swept, no listing id / API error goes to
     'skipped' (never silently treated as zero files), non-active products
     are excluded entirely.
  2. main.py's _etsy_file_inventory_report() reader degrades to None cleanly
     on a missing/corrupt report file.
  3. _build_etsy_files_response() correctly cross-references each Etsy file
     name against local storage -- local_match/local_url set when a
     same-named file exists, both None/False otherwise -- and never
     confuses a local match for confirmation of what's live on Etsy.
  4. _run_etsy_file_inventory_sweep() (the function wired into the daily
     loop) writes a real, atomically-replaced report file.
  5. _calendar_tasks_loop's daily gate wiring is present (source-level check,
     matching the existing star_seller_check/ads_check pattern).

Run: python tests/test_etsy_file_inventory.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_etsyfileinv_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "etsyfileinv-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import etsy_file_inventory as efi  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


class _FakeEtsyClient:
    def __init__(self, responses: dict):
        self._responses = responses

    def get_listing_files(self, listing_id):
        resp = self._responses.get(str(listing_id))
        if resp == "ERROR":
            raise efi.EtsyAPIError(401, "This action requires OAuth.")
        return resp or []


def test_sweep_classifies_correctly():
    catalog = [
        {"product_id": "INV_LIVE", "name": "Live Listing", "category": "svg_bundle",
         "status": "active", "price": 7.99, "files": [], "etsy_listing_id": "111"},
        {"product_id": "INV_EMPTY", "name": "Empty on Etsy", "category": "svg_bundle",
         "status": "active", "price": 7.99, "files": [], "etsy_listing_id": "222"},
        {"product_id": "INV_NOLISTING", "name": "No Listing Id", "category": "svg_bundle",
         "status": "active", "price": 7.99, "files": []},
        {"product_id": "INV_ERROR", "name": "Etsy Error", "category": "svg_bundle",
         "status": "active", "price": 7.99, "files": [], "etsy_listing_id": "333"},
        {"product_id": "INV_DRAFT", "name": "Not Active", "category": "svg_bundle",
         "status": "draft", "price": 7.99, "files": [], "etsy_listing_id": "444"},
    ]
    client = _FakeEtsyClient({
        "111": [{"filename": "real_file.zip", "listing_file_id": 1, "size_bytes": 5000, "rank": 1}],
        "222": [],
        "333": "ERROR",
    })
    with patch.object(efi, "_catalog", return_value=catalog):
        result = efi.sweep(client=client)

    listed_ids = {l["product_id"] for l in result["listings"]}
    skipped_ids = {s["product_id"] for s in result["skipped"]}

    check("INV_LIVE" in listed_ids, f"an active product with real Etsy files should be inventoried: {result}")
    live = next(l for l in result["listings"] if l["product_id"] == "INV_LIVE")
    check(live["files"] == [{"filename": "real_file.zip", "listing_file_id": 1, "size_bytes": 5000,
                              "rank": 1, "create_timestamp": None}],
          f"file metadata should be captured as-is: {live}")
    check("INV_EMPTY" in listed_ids, f"an active product with zero Etsy files should still be inventoried (empty files list, not skipped): {result}")
    empty = next(l for l in result["listings"] if l["product_id"] == "INV_EMPTY")
    check(empty["files"] == [], f"expected zero files for INV_EMPTY: {empty}")
    check("INV_NOLISTING" in skipped_ids, f"no etsy_listing_id should be skipped: {result}")
    check("INV_ERROR" in skipped_ids, f"an Etsy API error must be skipped, never silently counted as zero files: {result}")
    check("INV_DRAFT" not in listed_ids and "INV_DRAFT" not in skipped_ids,
          f"a non-active product should never be swept at all: {result}")


def test_report_reader_degrades_cleanly():
    with tempfile.TemporaryDirectory() as vol_dir:
        vol = Path(vol_dir)
        had_volume = "volume" in server._FILE_ROOTS
        old_volume = server._FILE_ROOTS.get("volume")
        server._FILE_ROOTS["volume"] = vol
        try:
            check(server._etsy_file_inventory_report() is None, "no report yet should return None, not an error")
            (vol / "etsy_file_inventory_report.json").write_text("{not valid json")
            check(server._etsy_file_inventory_report() is None, "a corrupt report file should degrade to None, not raise")
        finally:
            if had_volume:
                server._FILE_ROOTS["volume"] = old_volume
            else:
                server._FILE_ROOTS.pop("volume", None)


def test_build_etsy_files_response_cross_references_local_storage():
    with tempfile.TemporaryDirectory() as vol_dir:
        vol = Path(vol_dir)
        had_volume = "volume" in server._FILE_ROOTS
        old_volume = server._FILE_ROOTS.get("volume")
        server._FILE_ROOTS["volume"] = vol
        (vol / "product_files").mkdir(parents=True)
        local_name = "TEST_INVENTORY_LOCAL_FIXTURE_a91c.pdf"
        (vol / "product_files" / local_name).write_bytes(b"x")
        report = {
            "swept_at": "2026-07-19T00:00:00Z",
            "listings": [{
                "product_id": "INV_TEST", "title": "Inventory Test Product",
                "category": "digital_planner", "listing_id": "999",
                "files": [
                    {"filename": local_name, "size_bytes": 1234, "rank": 1},
                    {"filename": "no_local_copy_anywhere_xyz.zip", "size_bytes": 5678, "rank": 2},
                ],
            }],
            "skipped": [],
        }
        (vol / "etsy_file_inventory_report.json").write_text(json.dumps(report))
        try:
            resp = server._build_etsy_files_response()
        finally:
            if had_volume:
                server._FILE_ROOTS["volume"] = old_volume
            else:
                server._FILE_ROOTS.pop("volume", None)

    check(len(resp["listings"]) == 1, f"expected one listing in the response: {resp}")
    files = resp["listings"][0]["files"]
    matched = next(f for f in files if f["filename"] == local_name)
    unmatched = next(f for f in files if f["filename"] == "no_local_copy_anywhere_xyz.zip")
    check(matched["local_match"] is True and matched["local_url"] is not None,
          f"a file with a same-named local copy should be marked local_match with a real url: {matched}")
    check(unmatched["local_match"] is False and unmatched["local_url"] is None,
          f"a file with no local copy should have local_match False and no url: {unmatched}")
    check(matched["size_human"] is not None, f"size_bytes should be humanized: {matched}")
    check(resp["swept_at"] == "2026-07-19T00:00:00Z", f"swept_at should pass through: {resp}")


def test_run_etsy_file_inventory_sweep_writes_report():
    with tempfile.TemporaryDirectory() as vol_dir:
        vol = Path(vol_dir)
        had_volume = "volume" in server._FILE_ROOTS
        old_volume = server._FILE_ROOTS.get("volume")
        server._FILE_ROOTS["volume"] = vol
        try:
            detail = server._run_etsy_file_inventory_sweep()
            check(isinstance(detail, str) and "listing" in detail, f"expected a human-readable summary string, got: {detail}")
            report_path = vol / "etsy_file_inventory_report.json"
            check(report_path.exists(), "the sweep must write a report file")
            written = json.loads(report_path.read_text())
            check("listings" in written and "skipped" in written and "swept_at" in written,
                  f"written report missing expected keys: {written}")
        finally:
            if had_volume:
                server._FILE_ROOTS["volume"] = old_volume
            else:
                server._FILE_ROOTS.pop("volume", None)


def test_daily_loop_wiring_present():
    src = (ROOT / "tools" / "api_server" / "main.py").read_text(encoding="utf-8")
    check("_run_etsy_file_inventory_sweep" in src, "the sweep function must be referenced somewhere in main.py")
    check('_get_calendar_task_last_run("etsy_file_inventory")' in src,
          "the daily loop must track its own last-run date for etsy_file_inventory, same pattern as star_seller_check/ads_check")
    check('_set_calendar_task_last_run("etsy_file_inventory"' in src,
          "the daily loop must persist etsy_file_inventory's last-run date")


def test_endpoint_registered():
    src = (ROOT / "tools" / "api_server" / "main.py").read_text(encoding="utf-8")
    check('@app.get("/api/etsy-files")' in src, "GET /api/etsy-files must be registered")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("ETSY FILE INVENTORY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("ETSY FILE INVENTORY TESTS OK — sweep() classifies live/empty/skipped correctly against a mocked "
          "Etsy client, the report reader degrades cleanly, the Files-tab endpoint cross-references local "
          "storage without ever confusing a local copy for what's live on Etsy, the daily sweep writes a "
          "real report, and the calendar-loop + endpoint wiring is present.")


if __name__ == "__main__":
    run()
