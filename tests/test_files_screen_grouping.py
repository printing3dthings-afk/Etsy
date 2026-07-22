"""
Tests for the Files screen's listing-attachment grouping fix (2026-07-22).

Root cause: the Files tab's "PRODUCT FILES" grouping was a pure filename
regex (_productKeyFromPath in frank_hud_mockup.py) with no awareness of the
real product catalog. Concretely broken for coloring pages: raw per-page
source images (CB001_coloring.png, ... generate_coloring_pages.py's internal
theme IDs) matched the regex and were mistaken for individual products,
while the REAL deliverable ZIPs customers actually receive
(coloring_set_01.zip, genuinely attached to live Etsy listings) didn't match
the regex at all and fell into a generic leftover bucket instead of their
real product folder.

Fix: /api/files (list_files()/_scan(), tools/api_server/main.py) now
annotates each "products"-root file with catalog_match ({product_id,
category, attached} or None), resolved via the new _build_file_owner_index()
-- which reuses _build_products_status(), the SAME resolution /api/products
already uses, so the two screens can never disagree. Each "reference_images"
file gets its real category from the existing reference_images_meta.json
sidecar. Plain-text build logs (*.log) are excluded from the scan entirely.

Checks:
  1. _build_file_owner_index() marks a file attached/unattached correctly
     based on the owning product's real listing_id, and resolves duplicate
     basenames to the first match (documented setdefault policy).
  2. list_files()'s scan excludes .log files from every root.
  3. list_files() attaches catalog_match to "products"-root files (and only
     that root).
  4. list_files() attaches the real category to "reference_images"-root
     files from the sidecar metadata.

Run: python tests/test_files_screen_grouping.py
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_filesgroup_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "filesgroup-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── _build_file_owner_index() ──

def test_owner_index_marks_attached_when_listing_id_present():
    rows = [{"id": "WA1030", "category": "wall_art", "listing_id": "4500000001",
             "files": [{"name": "WA1030_print_sizes.zip", "exists": True}]}]
    with patch.object(server, "_build_products_status", return_value=rows):
        idx = server._build_file_owner_index()
    entry = idx.get("WA1030_print_sizes.zip")
    check(entry is not None, "expected the file to resolve to an owner")
    if entry:
        check(entry["product_id"] == "WA1030", f"expected product_id WA1030, got {entry}")
        check(entry["category"] == "wall_art", f"expected category wall_art, got {entry}")
        check(entry["attached"] is True, f"expected attached=True (real listing_id present), got {entry}")


def test_owner_index_marks_unattached_when_no_listing_id():
    rows = [{"id": "DP1030", "category": "digital_planner", "listing_id": "",
             "files": [{"name": "DP1030_v2.pdf", "exists": True}]}]
    with patch.object(server, "_build_products_status", return_value=rows):
        idx = server._build_file_owner_index()
    entry = idx.get("DP1030_v2.pdf")
    check(entry is not None, "expected the file to resolve to an owner")
    if entry:
        check(entry["attached"] is False, f"expected attached=False (empty listing_id, draft product), got {entry}")


def test_owner_index_no_match_for_unlisted_basename():
    rows = [{"id": "DP1030", "category": "digital_planner", "listing_id": "",
             "files": [{"name": "DP1030_v2.pdf", "exists": True}]}]
    with patch.object(server, "_build_products_status", return_value=rows):
        idx = server._build_file_owner_index()
    check("CB001_coloring.png" not in idx,
          "a loose file no product lists should have no owner -- the exact CB001 case")


def test_owner_index_first_match_wins_on_duplicate_basename():
    rows = [
        {"id": "FIRST", "category": "wall_art", "listing_id": "1", "files": [{"name": "dup.zip", "exists": True}]},
        {"id": "SECOND", "category": "wall_art", "listing_id": "", "files": [{"name": "dup.zip", "exists": True}]},
    ]
    with patch.object(server, "_build_products_status", return_value=rows):
        idx = server._build_file_owner_index()
    check(idx["dup.zip"]["product_id"] == "FIRST",
          f"expected setdefault (first match wins) policy, got {idx['dup.zip']}")


# ── list_files() / _scan() ──

def _swap_root(root_key: str, new_path: Path):
    had = root_key in server._FILE_ROOTS
    old = server._FILE_ROOTS.get(root_key)
    server._FILE_ROOTS[root_key] = new_path
    def _restore():
        if had:
            server._FILE_ROOTS[root_key] = old
        else:
            server._FILE_ROOTS.pop(root_key, None)
    return _restore


def test_scan_excludes_log_files():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "DP1030_v2.pdf").write_bytes(b"fake pdf")
        (tdp / "DP1030_product_build.log").write_text("Building DP1030... QC PASS")
        restore = _swap_root("products", tdp)
        try:
            with patch.object(server, "_file_owner_index", return_value={}):
                result = asyncio.run(server.list_files(_token="test"))
        finally:
            restore()
    products_group = next((g for g in result["groups"] if g["root"] == "products"), None)
    check(products_group is not None, "expected a products group")
    paths = [f["path"] for f in products_group["files"]] if products_group else []
    check("DP1030_v2.pdf" in paths, f"expected the real deliverable to still be listed, got {paths}")
    check("DP1030_product_build.log" not in paths, f".log files must be excluded, got {paths}")


def test_scan_annotates_catalog_match_for_products_root_only():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "coloring_set_01.zip").write_bytes(b"fake zip")
        (tdp / "CB001_coloring.png").write_bytes(b"fake png")
        restore = _swap_root("products", tdp)
        fake_index = {
            "coloring_set_01.zip": {"product_id": "COLOR_KAWAII_COLORING_PAGES_SET_01",
                                     "category": "coloring_pages", "attached": True},
        }
        try:
            with patch.object(server, "_file_owner_index", return_value=fake_index):
                result = asyncio.run(server.list_files(_token="test"))
        finally:
            restore()
    products_group = next((g for g in result["groups"] if g["root"] == "products"), None)
    by_path = {f["path"]: f for f in products_group["files"]} if products_group else {}

    attached_entry = by_path.get("coloring_set_01.zip", {})
    check(attached_entry.get("catalog_match") is not None,
          f"expected the real deliverable to carry a catalog_match, got {attached_entry}")
    if attached_entry.get("catalog_match"):
        check(attached_entry["catalog_match"]["attached"] is True,
              f"expected attached=True, got {attached_entry['catalog_match']}")
        check(attached_entry["catalog_match"]["product_id"] == "COLOR_KAWAII_COLORING_PAGES_SET_01",
              f"expected the real product id, got {attached_entry['catalog_match']}")

    orphan_entry = by_path.get("CB001_coloring.png", {})
    check(orphan_entry.get("catalog_match") is None,
          f"expected the raw source image with no catalog listing to have catalog_match=None (the CB001 bug), got {orphan_entry}")


def test_scan_annotates_reference_images_category():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "ab12cd34_moodboard.jpg").write_bytes(b"fake jpg")
        restore = _swap_root("reference_images", tdp)
        fake_meta = [{"id": "1", "filename": "ab12cd34_moodboard.jpg", "category": "wall_art"}]
        try:
            with patch.object(server, "_file_owner_index", return_value={}), \
                 patch.object(server, "_reference_images_meta", return_value=fake_meta):
                result = asyncio.run(server.list_files(_token="test"))
        finally:
            restore()
    refimg_group = next((g for g in result["groups"] if g["root"] == "reference_images"), None)
    check(refimg_group is not None, "expected a reference_images group")
    entry = next((f for f in refimg_group["files"] if f["path"] == "ab12cd34_moodboard.jpg"), None) if refimg_group else None
    check(entry is not None, "expected the reference image to be listed")
    if entry:
        check(entry.get("category") == "wall_art", f"expected category wall_art from sidecar metadata, got {entry}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FILES SCREEN GROUPING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FILES SCREEN GROUPING TESTS OK — the Files tab now resolves listing-attachment status "
          "against the real product catalog (agreeing with the Products screen) instead of guessing "
          "from filenames, and build-log noise is excluded from the scan.")


if __name__ == "__main__":
    run()
