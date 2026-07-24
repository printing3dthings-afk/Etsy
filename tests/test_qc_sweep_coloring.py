"""
Tests for qc_sweep.py's coloring-pages gate (2026-07-24): the dynamic
new-theme path (Scott types one theme, Frank generates
NEW_THEME_SET_SIZE distinct subjects, packages them into exactly one ZIP)
must be hard-gated on exact page count, since the listing copy literally
promises "N individual coloring pages" -- CLAUDE.md's top rule is never lie
to the customer. The 2 old fixed kawaii/fun_basic packs must be completely
unaffected (Scott: "leave the old packs exactly as they are").

Covers:
  - check_coloring_zip() PASS on exactly NEW_THEME_SET_SIZE flat PNGs, FAIL
    on one short.
  - sweep()'s dispatch: an old-pack-prefixed ZIP (5 pages) goes to
    check_other_zip() (content gate only, no page_count check at all) while
    a dynamically-named ZIP goes to check_coloring_zip() (hard page-count gate).

Run: python tests/test_qc_sweep_coloring.py
"""
import sys
import tempfile
import traceback
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import tools.qc_sweep as qc_sweep  # noqa: E402
import generate_coloring_pages as gcp  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _write_fake_zip(path: Path, n_pages: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for i in range(n_pages):
            zf.writestr(f"page_{i:02d}_coloring.png", b"fake png bytes")


def test_check_coloring_zip_passes_on_exact_new_theme_set_size():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "coloring_color_forest_set_01.zip"
        _write_fake_zip(zpath, gcp.NEW_THEME_SET_SIZE)
        rows = []
        with patch.object(qc_sweep, "validate_digital_file", return_value={"path": str(zpath)}):
            qc_sweep.check_coloring_zip(zpath, lambda sev, f, c, d="": rows.append(
                {"severity": sev, "file": f, "check": c, "detail": d}))
    page_rows = [r for r in rows if r["check"] == "page_count"]
    check(len(page_rows) == 1, f"expected exactly 1 page_count row, got {rows}")
    check(page_rows[0]["severity"] == "PASS", f"exact NEW_THEME_SET_SIZE must PASS, got {page_rows}")


def test_check_coloring_zip_fails_on_undercount():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "coloring_color_forest_set_01.zip"
        _write_fake_zip(zpath, gcp.NEW_THEME_SET_SIZE - 1)
        rows = []
        with patch.object(qc_sweep, "validate_digital_file", return_value={"path": str(zpath)}):
            qc_sweep.check_coloring_zip(zpath, lambda sev, f, c, d="": rows.append(
                {"severity": sev, "file": f, "check": c, "detail": d}))
    page_rows = [r for r in rows if r["check"] == "page_count"]
    check(len(page_rows) == 1, f"got {rows}")
    check(page_rows[0]["severity"] == "FAIL",
          f"one page short of NEW_THEME_SET_SIZE must hard FAIL (never lie to the customer), got {page_rows}")


def test_sweep_dispatch_routes_old_pack_to_generic_gate_not_page_count():
    with tempfile.TemporaryDirectory() as tmp:
        dp_base = Path(tmp)
        sets_dir = dp_base / "coloring_pages" / "sets"
        old_pack = sets_dir / "coloring_set_01.zip"
        _write_fake_zip(old_pack, 5)  # the real old-pack batch size, PAGES_PER_SET
        with patch.object(qc_sweep, "DP_BASE", dp_base), \
             patch.object(qc_sweep, "PF_DIR", dp_base / "product_files"), \
             patch.object(qc_sweep, "PRINT_ZIP_DIR", dp_base / "print_zips"), \
             patch.object(qc_sweep, "validate_digital_file", return_value={"path": str(old_pack)}):
            rows = qc_sweep.sweep(only="coloring_set_01")
    page_rows = [r for r in rows if r["check"] == "page_count"]
    check(page_rows == [], f"an old fixed-pack ZIP must never get the page_count hard gate, got {page_rows}")
    content_rows = [r for r in rows if r["check"] == "content_gate"]
    check(len(content_rows) == 1 and content_rows[0]["severity"] == "PASS",
          f"the old pack must still pass the generic content gate, got {content_rows}")


def test_sweep_dispatch_routes_dynamic_pack_to_page_count_gate():
    with tempfile.TemporaryDirectory() as tmp:
        dp_base = Path(tmp)
        sets_dir = dp_base / "coloring_pages" / "sets"
        dynamic_pack = sets_dir / "coloring_color_forest_set_01.zip"
        _write_fake_zip(dynamic_pack, gcp.NEW_THEME_SET_SIZE)
        with patch.object(qc_sweep, "DP_BASE", dp_base), \
             patch.object(qc_sweep, "PF_DIR", dp_base / "product_files"), \
             patch.object(qc_sweep, "PRINT_ZIP_DIR", dp_base / "print_zips"), \
             patch.object(qc_sweep, "validate_digital_file", return_value={"path": str(dynamic_pack)}):
            rows = qc_sweep.sweep(only="coloring_color_forest_set_01")
    page_rows = [r for r in rows if r["check"] == "page_count"]
    check(len(page_rows) == 1, f"a dynamically-named ZIP must get the page_count gate, got {rows}")
    check(page_rows[0]["severity"] == "PASS", f"got {page_rows}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("QC SWEEP COLORING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("QC SWEEP COLORING TESTS OK — check_coloring_zip() hard-gates the dynamic "
          "new-theme ZIP on exact page count, and sweep()'s dispatch correctly routes "
          "old fixed packs to the generic content-only gate while dynamic packs get "
          "the exact-count gate.")


if __name__ == "__main__":
    run()
