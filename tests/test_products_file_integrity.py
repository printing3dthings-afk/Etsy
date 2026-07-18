"""
Tests for the 2026-07-18 Products-screen file-integrity fix: Scott reported
only 5/176 catalog products showed "all files present." Root cause was a path
bug -- _product_file_exists() only understood catalog paths starting with
"data/digital_products/"; every other convention (explicit paths elsewhere
under data/, or bare filenames with no directory at all) was silently
mis-resolved and always reported missing. This file tests the fix
(_catalog_file_exists/_catalog_file_abs_path/_catalog_file_url,
_build_products_status()'s new contract, the files_not_applicable gate for
3d_print_physical/*_license categories), tools/audit_product_files.py's
Etsy-first classification, and the generalized _produce_build_product()
dispatch (wall_art/coloring_pages, alongside the original digital_planner).

Uses real, already-on-disk fixtures from this checkout where possible (the
exact regression cases: SVG_FLORAL's explicit-path entry, the svg_3dprint_pack
bare-filename entry whose real file lives in a totally different directory)
rather than fabricating synthetic files, since that's what actually proves
the fix against the real bug.

Run: python tests/test_products_file_integrity.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_fileintegrity_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "fileintegrity-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _real_catalog() -> list[dict]:
    return json.loads((ROOT / "data" / "product_catalog.json").read_text())


# ── _catalog_file_exists() / _catalog_file_abs_path() path conventions ──

def test_legacy_prefixed_path_still_works():
    # Self-contained (not dependent on any real product file being present on
    # disk -- data/digital_products/*.pdf/*.zip are never git-committed, so a
    # fresh CI checkout has none of them, unlike data/svg_pack/ etc used below).
    products_root = server._FILE_ROOTS["products"]
    products_root.mkdir(parents=True, exist_ok=True)
    tmp_name = "TEST_LEGACY_FIXTURE_9f3c.pdf"
    tmp_path = products_root / tmp_name
    tmp_path.write_bytes(b"x")
    try:
        f = f"data/digital_products/{tmp_name}"
        check(server._catalog_file_exists(f), f"a legacy data/digital_products/-prefixed path that's on disk should resolve: {f}")
    finally:
        tmp_path.unlink(missing_ok=True)


def test_explicit_nonprefixed_path_resolves():
    # SVG_FLORAL's file lives at data/svg_pack/... -- outside data/digital_products/,
    # the exact class of entry the old prefix-strip-only logic always mis-resolved.
    entry = next((e for e in _real_catalog() if e["product_id"] == "SVG_FLORAL"), None)
    if entry is None:
        _failures.append("SVG_FLORAL not in the catalog -- test fixture assumption broke")
        return
    f = entry["files"][0]
    check(not f.startswith("data/digital_products/"), f"SVG_FLORAL's path should be the exact non-prefixed regression case, got: {f}")
    check((ROOT / f).exists(), f"expected {f} to exist on disk in this checkout (the fix's proof case)")
    check(server._catalog_file_exists(f), f"an explicit non-prefixed path that's on disk should now resolve: {f}")
    abs_path = server._catalog_file_abs_path(f)
    check(abs_path is not None and abs_path.exists(), f"_catalog_file_abs_path should return a real, existing Path: {abs_path}")


def test_bare_filename_resolves_via_index():
    # SS_AMERICA_250_SVG's files are bare filenames with NO directory at all, and
    # their real location (data/3d_print_signs/america_250/) has nothing to do with
    # the filename -- only the cached basename index can find these.
    entry = next((e for e in _real_catalog() if e["product_id"] == "SS_AMERICA_250_SVG"), None)
    if entry is None:
        _failures.append("SS_AMERICA_250_SVG not in the catalog -- test fixture assumption broke")
        return
    f = entry["files"][0]
    check("/" not in f, f"expected a bare filename (no directory) for this regression case, got: {f}")
    # Force a fresh index build so this test doesn't depend on cache state left by
    # an earlier test/process.
    server._catalog_filename_index_cache["built_at"] = 0.0
    check(server._catalog_file_exists(f), f"a bare-filename catalog entry whose file exists somewhere under data/ should resolve via the index: {f}")


def test_genuinely_absent_file_reports_missing():
    check(not server._catalog_file_exists("data/digital_products/product_files/DOES_NOT_EXIST_XYZ.pdf"),
          "a path that genuinely doesn't exist anywhere must still report missing")
    check(not server._catalog_file_exists("totally_bogus_filename_nobody_has.zip"),
          "a bare filename with no real match anywhere must still report missing")


def test_volume_fallback_for_explicit_path():
    with tempfile.TemporaryDirectory() as vol_dir:
        vol = Path(vol_dir)
        (vol / "data" / "some_pack").mkdir(parents=True)
        (vol / "data" / "some_pack" / "thing.zip").write_bytes(b"x")
        had_volume = "volume" in server._FILE_ROOTS
        old_volume = server._FILE_ROOTS.get("volume")
        server._FILE_ROOTS["volume"] = vol
        try:
            check(server._catalog_file_exists("data/some_pack/thing.zip"),
                  "an explicit-path entry that only exists under the persistent volume should still resolve")
        finally:
            if had_volume:
                server._FILE_ROOTS["volume"] = old_volume
            else:
                server._FILE_ROOTS.pop("volume", None)


# ── _build_products_status() contract ──

def test_files_not_applicable_gate():
    catalog = [
        {"product_id": "P3D_TEST", "name": "Test Koozie", "category": "3d_print_physical",
         "status": "active", "price": 10, "files": []},
        {"product_id": "LIC_TEST", "name": "Test License", "category": "svg_bundle_license",
         "status": "active", "price": 10, "files": []},
    ]
    products = server._build_products_status(catalog, server._catalog_file_exists)
    for p in products:
        check(p["files_not_applicable"] is True, f"{p['id']} is in a no-files-required category and should be flagged files_not_applicable: {p}")
        check(p["all_files_present"] is None, f"{p['id']} should not compute a present/missing verdict at all: {p}")


def test_build_products_status_end_to_end_against_real_catalog():
    # Regression guard for the actual fix: SVG_FLORAL must no longer be a false
    # "missing" (it was, under the pre-fix prefix-only logic).
    catalog = _real_catalog()
    products = server._build_products_status(catalog, server._catalog_file_exists)
    by_id = {p["id"]: p for p in products}
    svg_floral = by_id.get("SVG_FLORAL")
    if svg_floral is not None:
        check(svg_floral["all_files_present"] is True, f"SVG_FLORAL should resolve as fully present post-fix: {svg_floral}")


# ── tools/audit_product_files.py — Etsy-first classification ──

class _FakeEtsyError(Exception):
    def __init__(self, status, message):
        self.status = status
        super().__init__(f"Etsy API {status}: {message}")


class _FakeEtsyClient:
    """Returns canned get_listing_files() results keyed by listing_id."""
    def __init__(self, responses: dict):
        self._responses = responses

    def get_listing_files(self, listing_id):
        resp = self._responses.get(str(listing_id))
        if resp == "ERROR":
            import audit_product_files as apf
            raise apf.EtsyAPIError(401, "This action requires OAuth.")
        return resp or []


def test_audit_classifies_verified_live_missing_and_skipped():
    import audit_product_files as apf

    # Self-contained "already fine locally" fixture (not dependent on any real
    # product file being present on disk -- see test_legacy_prefixed_path_still_works).
    products_root = server._FILE_ROOTS["products"]
    products_root.mkdir(parents=True, exist_ok=True)
    healthy_name = "TEST_AUDIT_HEALTHY_FIXTURE_7ac1.pdf"
    healthy_path = products_root / healthy_name
    healthy_path.write_bytes(b"x")

    catalog = [
        {"product_id": "AUD_LIVE", "name": "Verified Live", "category": "svg_bundle",
         "status": "active", "price": 7.99, "files": [],
         "etsy_listing_id": "111"},
        {"product_id": "AUD_MISSING", "name": "Genuinely Missing", "category": "svg_bundle",
         "status": "active", "price": 7.99, "files": [],
         "etsy_listing_id": "222"},
        {"product_id": "AUD_NOLISTING", "name": "No Listing Id", "category": "svg_bundle",
         "status": "active", "price": 7.99, "files": []},
        {"product_id": "AUD_ERROR", "name": "Etsy Error", "category": "svg_bundle",
         "status": "active", "price": 7.99, "files": [], "etsy_listing_id": "333"},
        {"product_id": "AUD_HEALTHY", "name": "Already Fine Locally", "category": "digital_planner",
         "status": "active", "price": 14.99, "etsy_listing_id": "444",
         "files": [f"data/digital_products/{healthy_name}"]},
        {"product_id": "AUD_DRAFT", "name": "Not Active", "category": "svg_bundle",
         "status": "draft", "price": 7.99, "files": [], "etsy_listing_id": "555"},
    ]
    client = _FakeEtsyClient({
        "111": [{"filename": "real_file.zip"}],
        "222": [],
        "333": "ERROR",
    })
    try:
        with patch.object(apf, "_catalog", return_value=catalog):
            result = apf.audit(client=client)
    finally:
        healthy_path.unlink(missing_ok=True)

    verified_ids = {r["product_id"] for r in result["verified_live"]}
    missing_ids = {r["product_id"] for r in result["genuinely_missing"]}
    skipped_ids = {r["product_id"] for r in result["skipped"]}

    check("AUD_LIVE" in verified_ids, f"a product with real Etsy files should be verified_live: {result}")
    check("AUD_MISSING" in missing_ids, f"a product with an empty Etsy files list should be genuinely_missing: {result}")
    check("AUD_NOLISTING" in skipped_ids, f"a product with no listing id should be skipped, not counted as missing: {result}")
    check("AUD_ERROR" in skipped_ids, f"an Etsy API error must be skipped, never silently counted as missing: {result}")
    check("AUD_HEALTHY" not in verified_ids and "AUD_HEALTHY" not in missing_ids and "AUD_HEALTHY" not in skipped_ids,
          f"a product with all files already present locally should never even reach the Etsy check: {result}")
    check("AUD_DRAFT" not in verified_ids and "AUD_DRAFT" not in missing_ids and "AUD_DRAFT" not in skipped_ids,
          f"a non-active product should never reach the Etsy check: {result}")


# ── GET /api/alerts product_file_integrity source ──

def test_file_audit_alerts_read_the_report():
    with tempfile.TemporaryDirectory() as vol_dir:
        vol = Path(vol_dir)
        had_volume = "volume" in server._FILE_ROOTS
        old_volume = server._FILE_ROOTS.get("volume")
        server._FILE_ROOTS["volume"] = vol
        try:
            check(server._product_file_integrity_alerts() == [], "no report yet should mean no alerts, not an error")
            report = {
                "verified_live": [],
                "genuinely_missing": [{"product_id": "X1", "title": "Thing", "listing_id": "999", "expected_files": ["a.zip"]}],
                "skipped": [],
            }
            (vol / "file_audit_report.json").write_text(json.dumps(report))
            alerts = server._product_file_integrity_alerts()
            check(len(alerts) == 1, f"one genuinely_missing entry should produce one alert: {alerts}")
            check(alerts[0]["source"] == "product_file_integrity", f"wrong alert source: {alerts}")
            check(alerts[0]["severity"] == "critical", f"a genuinely-missing active listing is a compliance issue -- must be critical: {alerts}")
            check("X1" in alerts[0]["title"], f"alert should name the product: {alerts}")

            idx = server._file_audit_index()
            check(idx.get("X1") == "genuinely_missing", f"file audit index should classify X1: {idx}")
        finally:
            if had_volume:
                server._FILE_ROOTS["volume"] = old_volume
            else:
                server._FILE_ROOTS.pop("volume", None)


# ── _produce_build_product() category dispatch ──

def test_unsupported_category_returns_clear_error_no_subprocess():
    with patch("subprocess.Popen") as mock_popen:
        result = server._produce_build_product({"pid": "SVG1001", "category": "svg_bundle"})
    check("error" in result, f"an unsupported category must return an error: {result}")
    check(not mock_popen.called, "no subprocess should ever be spawned for an unsupported category")


def test_category_resolved_from_catalog_when_not_explicit():
    entry = next(e for e in _real_catalog() if e["category"] == "wall_art")
    pid = entry["product_id"]
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.pid = 999999
        result = server._produce_build_product({"pid": pid})
    check(result.get("category") == "wall_art", f"category should be auto-resolved from the catalog by pid: {result}")
    check(mock_popen.called, "a supported category should spawn a build subprocess")
    args = mock_popen.call_args[0][0]
    check("build_wallart_product.py" in args[1], f"wall_art should dispatch to build_wallart_product.py: {args}")
    server._LONG_RUNNING_PROCS.pop(999999, None)


def test_coloring_pages_dispatches_to_its_own_script():
    entry = next(e for e in _real_catalog() if e["category"] == "coloring_pages")
    pid = entry["product_id"]
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.pid = 999998
        result = server._produce_build_product({"pid": pid})
    check(result.get("category") == "coloring_pages", f"expected coloring_pages category: {result}")
    check(mock_popen.called, "coloring_pages should spawn a build subprocess")
    args = mock_popen.call_args[0][0]
    check("build_coloring_product.py" in args[1], f"coloring_pages should dispatch to build_coloring_product.py: {args}")
    server._LONG_RUNNING_PROCS.pop(999998, None)


def test_digital_planner_path_unchanged():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.pid = 999997
        result = server._produce_build_product({"pid": "DP1030", "engine": "gemini"})
    check(result.get("category") == "digital_planner", f"expected digital_planner category: {result}")
    check(result.get("needs_visual_qc") is True, "planner builds must still carry the visual-QC honesty flag")
    args = mock_popen.call_args[0][0]
    check("build_product.py" in args[1], f"digital_planner should still dispatch to the original build_product.py: {args}")
    server._LONG_RUNNING_PROCS.pop(999997, None)


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PRODUCTS FILE INTEGRITY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRODUCTS FILE INTEGRITY TESTS OK — path resolution covers all three catalog "
          "conventions (prefixed/explicit/bare-filename) plus the volume fallback, "
          "3d_print_physical/*_license are correctly excluded from the files gate, "
          "audit_product_files.py classifies verified/missing/skipped correctly against "
          "a mocked Etsy client, product_file_integrity alerts read the audit report, and "
          "_produce_build_product() dispatches wall_art/coloring_pages/digital_planner to "
          "their own scripts with an explicit error for anything unsupported.")


if __name__ == "__main__":
    run()
