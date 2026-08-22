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
  - (2026-07-25) generate_coloring_pages._resolve_dp_base(): the real fix for
    the COLOR1001 incident (a live-built product's ZIP silently vanished on
    the next redeploy because COLORING_DIR hardcoded the ephemeral local
    path instead of checking the persistent volume like every sibling
    generator does). Verifies the env-override/volume-mount/local-fallback
    precedence, and that COLORING_DIR/SETS_DIR stay in lockstep with
    qc_sweep.py's own scan path.

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


def test_check_coloring_zip_honors_manifest_for_a_merged_bundle():
    """2026-08-10: a multi-source bundle (generate_coloring_pages.merge_
    existing_sets_into_bundle()) legitimately has more than NEW_THEME_SET_SIZE
    pages -- its `.manifest.json` sidecar records the real total, and the
    page_count gate must PASS against THAT count, not the single-batch
    default, or every real bundle would false-FAIL forever."""
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "coloring_color1006_set_01.zip"
        _write_fake_zip(zpath, 100)
        zpath.with_suffix(".manifest.json").write_text(
            '{"bundle_pid": "COLOR1006", "total_pages": 100, "included": []}')
        rows = []
        with patch.object(qc_sweep, "validate_digital_file", return_value={"path": str(zpath)}):
            qc_sweep.check_coloring_zip(zpath, lambda sev, f, c, d="": rows.append(
                {"severity": sev, "file": f, "check": c, "detail": d}))
    page_rows = [r for r in rows if r["check"] == "page_count"]
    check(len(page_rows) == 1, f"got {rows}")
    check(page_rows[0]["severity"] == "PASS",
          f"100 real pages matching the manifest's claimed total must PASS, got {page_rows}")


def test_check_coloring_zip_manifest_mismatch_still_fails():
    """The manifest changes the EXPECTED count, not the enforcement -- if the
    actual ZIP contents don't match what the manifest itself claims, that's
    still a real mismatch and must still FAIL."""
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "coloring_color1006_set_01.zip"
        _write_fake_zip(zpath, 99)  # one short of what the manifest claims
        zpath.with_suffix(".manifest.json").write_text(
            '{"bundle_pid": "COLOR1006", "total_pages": 100, "included": []}')
        rows = []
        with patch.object(qc_sweep, "validate_digital_file", return_value={"path": str(zpath)}):
            qc_sweep.check_coloring_zip(zpath, lambda sev, f, c, d="": rows.append(
                {"severity": sev, "file": f, "check": c, "detail": d}))
    page_rows = [r for r in rows if r["check"] == "page_count"]
    check(page_rows[0]["severity"] == "FAIL", f"got {page_rows}")


def test_check_coloring_zip_malformed_manifest_falls_back_to_standard_size():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "coloring_color_broken_set_01.zip"
        _write_fake_zip(zpath, gcp.NEW_THEME_SET_SIZE)
        zpath.with_suffix(".manifest.json").write_text("not valid json{{{")
        rows = []
        with patch.object(qc_sweep, "validate_digital_file", return_value={"path": str(zpath)}):
            qc_sweep.check_coloring_zip(zpath, lambda sev, f, c, d="": rows.append(
                {"severity": sev, "file": f, "check": c, "detail": d}))
    page_rows = [r for r in rows if r["check"] == "page_count"]
    check(page_rows[0]["severity"] == "PASS",
          f"a malformed manifest must fall back to the standard NEW_THEME_SET_SIZE check, got {page_rows}")


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


def test_resolve_dp_base_prefers_hub_files_dir_env_override():
    # (2026-07-25) Regression for the real COLOR1001 incident: COLORING_DIR
    # used to hardcode the ephemeral local path unconditionally, unlike every
    # sibling generator (generate_print_sizes.py, qc_sweep.py, main.py). A
    # coloring-pages product built live on the dashboard would write its ZIP
    # there, survive until the next redeploy wiped it, while its catalog
    # registration (durably volume-backed) lived on -- exactly the "product
    # exists but no deliverable files found" ghost state Scott reported.
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict("os.environ", {"HUB_FILES_DIR": tmp}):
            base = gcp._resolve_dp_base()
    check(base == Path(tmp), f"HUB_FILES_DIR must win when set and it's a real dir, got {base}")


def test_resolve_dp_base_falls_back_to_data_files_volume_mount():
    # Only /data/files "exists" in this simulated environment -- no need to
    # mock the Path constructor itself, just the one is_dir() check the
    # function actually makes.
    def _is_dir_stub(self):
        return str(self) == "/data/files"
    with patch.dict("os.environ", {"HUB_FILES_DIR": ""}), \
         patch.object(Path, "is_dir", _is_dir_stub):
        base = gcp._resolve_dp_base()
    check(str(base) == "/data/files", f"must resolve to the Railway volume mount when present, got {base}")


def test_resolve_dp_base_uses_local_repo_dir_when_nothing_else_present():
    with patch.dict("os.environ", {"HUB_FILES_DIR": ""}), \
         patch.object(Path, "is_dir", lambda self: False):
        base = gcp._resolve_dp_base()
    check(base == gcp.BASE / "data" / "digital_products",
          f"local dev fallback must match the pre-fix hardcoded path exactly, got {base}")


def test_coloring_dir_and_sets_dir_derive_from_resolved_base():
    check(gcp.COLORING_DIR == gcp._resolve_dp_base() / "coloring_pages",
          f"COLORING_DIR must be derived from _resolve_dp_base(), got {gcp.COLORING_DIR}")
    check(gcp.SETS_DIR == gcp.COLORING_DIR / "sets", f"got {gcp.SETS_DIR}")
    # This is the exact directory qc_sweep.sweep() scans for coloring ZIPs
    # (DP_BASE / "coloring_pages" / "sets") -- must stay in lockstep or a
    # correctly-written file would still never be found by QC/Files.
    check(gcp.SETS_DIR == qc_sweep.resolve_dp_base() / "coloring_pages" / "sets",
          f"must match qc_sweep's own scan path exactly, got {gcp.SETS_DIR}")


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
          "new-theme ZIP on exact page count, sweep()'s dispatch correctly routes "
          "old fixed packs to the generic content-only gate while dynamic packs get "
          "the exact-count gate, and generate_coloring_pages' output path is now "
          "volume-aware (the COLOR1001 fix) and stays in lockstep with qc_sweep's scan path.")


if __name__ == "__main__":
    run()
