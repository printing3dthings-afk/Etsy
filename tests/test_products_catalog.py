#!/usr/bin/env python3
"""
Fixture test for tools/api_server/main.py's _build_products_status()
(2026-07-15 Products screen rebuild) -- GET /api/products used to be
hardcoded to a ~5-product "Core Products" slice (DP1026-1035) left over
from when the shop only had a handful of planners; it never grew with the
catalog, so it looked broken once the shop reached 176 products. This
tests the pure logic that replaced it: given a catalog list and a
file-existence checker, compute per-product/per-file status, including
the "data/digital_products/" prefix-stripping needed to match
_product_file_exists()'s rel convention.

Dependency-light: `import main as server` (same safe import
tests/test_staged_actions.py already relies on), a fake file-exists
function instead of touching real disk -- no live Etsy call.

Run locally:  python tests/test_products_catalog.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a regression (prints which).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_all_files_present():
    catalog = [{
        "product_id": "DP1026", "name": "Ultimate Digital Life Planner",
        "etsy_listing_id": "4509179201", "category": "digital_planner",
        "status": "active", "price": 14.99,
        "files": ["data/digital_products/product_files/DP1026.pdf",
                  "data/digital_products/product_files/DP1026_sticker_pack.zip"],
    }]
    result = server._build_products_status(catalog, lambda rel: True)
    check(len(result) == 1, f"expected 1 product, got {len(result)}")
    p = result[0]
    check(p["id"] == "DP1026", f"expected id DP1026, got {p['id']}")
    check(p["all_files_present"] is True, f"expected all_files_present True, got {p['all_files_present']}")
    check(len(p["files"]) == 2, f"expected 2 files, got {p['files']}")
    check(all(f["exists"] for f in p["files"]), f"expected all files marked existing, got {p['files']}")
    check(p["files"][0]["name"] == "DP1026.pdf", f"expected basename-only file name, got {p['files'][0]}")


def test_some_files_missing():
    catalog = [{
        "product_id": "WA1073", "name": "Some Wall Art", "etsy_listing_id": "123",
        "category": "wall_art", "status": "active", "price": 5.99,
        "files": ["data/digital_products/wall_art/WA1073_print_sizes.zip"],
    }]
    result = server._build_products_status(catalog, lambda rel: False)
    p = result[0]
    check(p["all_files_present"] is False, f"expected all_files_present False, got {p['all_files_present']}")
    check(p["files"][0]["exists"] is False, "the one file should be marked missing")


def test_mixed_present_and_missing():
    catalog = [{
        "product_id": "DP1027", "name": "Student Planner", "etsy_listing_id": "456",
        "category": "digital_planner", "status": "active", "price": 9.99,
        "files": ["data/digital_products/product_files/DP1027.pdf",
                  "data/digital_products/product_files/DP1027_sticker_pack.zip"],
    }]
    # Only the .pdf exists, the .zip doesn't -- exercises real per-file granularity.
    result = server._build_products_status(
        catalog, lambda rel: rel.endswith(".pdf")
    )
    p = result[0]
    check(p["all_files_present"] is False, f"one missing file should mark the whole product False, got {p['all_files_present']}")
    exists_map = {f["name"]: f["exists"] for f in p["files"]}
    check(exists_map["DP1027.pdf"] is True, f"the .pdf should be marked present: {exists_map}")
    check(exists_map["DP1027_sticker_pack.zip"] is False, f"the .zip should be marked missing: {exists_map}")


def test_product_with_no_files_listed():
    catalog = [{
        "product_id": "SS9999", "name": "Draft product", "etsy_listing_id": None,
        "category": "svg_bundle", "status": "draft", "price": None,
        "files": [],
    }]
    result = server._build_products_status(catalog, lambda rel: True)
    p = result[0]
    check(p["all_files_present"] is None,
          f"a product with zero files listed should be None (unknown), not True/False, got {p['all_files_present']}")
    check(p["files"] == [], "files list should be empty")


def test_file_exists_fn_receives_the_raw_catalog_path():
    # 2026-07-18: _build_products_status() no longer strips the
    # data/digital_products/ prefix itself -- most catalog entries (wall_art,
    # coloring_pages, paper_pack, svg_bundle, etc) were never rooted under that
    # prefix at all, so a single strip-and-rejoin convention silently mis-resolved
    # them. The raw path is now handed straight to file_exists_fn, which is
    # responsible for its own resolution strategy -- see
    # server._catalog_file_exists() for the real (three-convention) one.
    seen_paths = []

    def _fake_exists(f):
        seen_paths.append(f)
        return True

    catalog = [{
        "product_id": "DP1026", "name": "x", "etsy_listing_id": "1",
        "category": "digital_planner", "status": "active", "price": 1.0,
        "files": ["data/digital_products/product_files/DP1026.pdf"],
    }]
    server._build_products_status(catalog, _fake_exists)
    check(seen_paths == ["data/digital_products/product_files/DP1026.pdf"],
          f"expected the raw catalog path passed through unchanged, got {seen_paths}")


def test_missing_category_and_status_default_gracefully():
    catalog = [{"product_id": "X1", "name": "y", "files": []}]
    result = server._build_products_status(catalog, lambda rel: True)
    p = result[0]
    check(p["category"] == "uncategorized", f"missing category should default to 'uncategorized', got {p['category']}")
    check(p["status"] == "active", f"missing status should default to 'active', got {p['status']}")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ran = 0
    for t in tests:
        try:
            t()
            ran += 1
        except Exception as exc:
            _failures.append(f"{t.__name__} raised an unexpected error: {exc}")
    if _failures:
        print("PRODUCTS CATALOG TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"PRODUCTS CATALOG TESTS OK — {ran} tests passed "
          f"(_build_products_status()'s file-status logic, no live Etsy call).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
