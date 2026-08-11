"""
Tests for qc_sweep.py's WC-series wall-calendar gate (2026-08-11): every
claim a calendar listing makes must be literally true of what's inside the
ZIP -- exactly 12 pages per monthly-grid PDF, a dated PDF that actually
contains real day numbers (not a silently-blank build), an undated PDF that
contains ZERO year digits (the whole point of generate_wall_calendar.py
rendering it with no baked-in weekday alignment), and a year-at-a-glance
poster meeting the shop's print-resolution floor.

generate_wall_calendar.py's own generation logic (PDF page rendering, date
math, the poster's PIL layout) is covered directly in
tests/test_generate_wall_calendar.py; this file covers the QC gate that
reads its OUTPUT.

Run: python tests/test_qc_sweep_calendar.py
"""
import io
import sys
import tempfile
import traceback
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import tools.qc_sweep as qc_sweep  # noqa: E402
from PIL import Image  # noqa: E402

# sweep() normally imports PIL into this module's global namespace lazily
# (see qc_sweep.py's own docstring on why) -- tests call check_wall_calendar_
# zip() directly, so mirror that setup once here.
qc_sweep.Image = Image

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _rows_collector():
    rows = []

    def add(sev, f, chk, detail=""):
        rows.append({"severity": sev, "file": f, "check": chk, "detail": detail})
    return rows, add


def _make_pdf_bytes(n_pages: int, with_day_numbers: bool, year: int | None) -> bytes:
    """A minimal real PDF (via reportlab) with n_pages, each containing either
    real-looking day-number text (1-31) or none, and optionally a year label
    -- enough for PyPDF2 to parse and for the QC regexes to exercise for real,
    without depending on generate_wall_calendar.py's full rendering pipeline."""
    from reportlab.pdfgen import canvas as pdf_canvas
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=(612, 792))
    for _ in range(n_pages):
        if year:
            c.drawString(50, 700, f"January {year}")
        else:
            c.drawString(50, 700, "January")
        if with_day_numbers:
            for d in range(1, 15):
                c.drawString(50 + d * 10, 600, str(d))
        c.showPage()
    c.save()
    return buf.getvalue()


def _make_poster_bytes(w: int, h: int) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (200, 200, 200)).save(buf, "JPEG")
    return buf.getvalue()


def _make_calendar_zip(path: Path, *, dated_pages=12, undated_pages=12,
                        dated_has_days=True, undated_year_leak=False,
                        poster_size=(3000, 3000), include_poster=True,
                        include_readme=True) -> None:
    dated = _make_pdf_bytes(dated_pages, with_day_numbers=dated_has_days, year=2026)
    undated = _make_pdf_bytes(undated_pages, with_day_numbers=False,
                               year=2026 if undated_year_leak else None)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        if include_readme:
            zf.writestr("README.txt", "test pack")
        zf.writestr("WC1001_dated_2026_monday_start.pdf", dated)
        zf.writestr("WC1001U_undated_monday_start.pdf", undated)
        if include_poster:
            zf.writestr("WC1001_2026_yearglance_poster.jpg", _make_poster_bytes(*poster_size))


def test_wall_calendar_zip_passes_a_correct_pack():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "wc1001_calendar_pack.zip"
        _make_calendar_zip(zpath)
        rows, add = _rows_collector()
        qc_sweep.check_wall_calendar_zip(zpath, add)
    fails = [r for r in rows if r["severity"] == "FAIL"]
    check(fails == [], f"a correct pack must have zero FAILs, got {fails}")
    check(any(r["check"] == "page_count" and r["severity"] == "PASS" for r in rows), f"got {rows}")
    check(any(r["check"] == "undated_no_year_leak" and r["severity"] == "PASS" for r in rows), f"got {rows}")
    check(any(r["check"] == "poster_resolution" and r["severity"] == "PASS" for r in rows), f"got {rows}")


def test_wall_calendar_zip_fails_wrong_page_count():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "wc1001_calendar_pack.zip"
        _make_calendar_zip(zpath, dated_pages=11)
        rows, add = _rows_collector()
        qc_sweep.check_wall_calendar_zip(zpath, add)
    fails = [r for r in rows if r["severity"] == "FAIL" and r["check"] == "page_count"]
    check(len(fails) == 1, f"expected exactly 1 page_count FAIL, got {rows}")
    check("11 pages" in fails[0]["detail"], f"got {fails}")


def test_wall_calendar_zip_fails_when_dated_pdf_has_no_day_numbers():
    """A build that silently produced the blank/undated template but named
    it as the dated file must be caught -- page count alone can't tell the
    difference, so this checks for real day-number content."""
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "wc1001_calendar_pack.zip"
        _make_calendar_zip(zpath, dated_has_days=False)
        rows, add = _rows_collector()
        qc_sweep.check_wall_calendar_zip(zpath, add)
    fails = [r for r in rows if r["severity"] == "FAIL" and r["check"] == "dated_content"]
    check(len(fails) == 1, f"expected a dated_content FAIL, got {rows}")


def test_wall_calendar_zip_fails_undated_pdf_leaking_a_real_year():
    """The exact defect class generate_wall_calendar.py's undated variant is
    designed to structurally avoid (see its own docstring) -- if it ever
    regresses, this must catch it, not just trust the filename."""
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "wc1001_calendar_pack.zip"
        _make_calendar_zip(zpath, undated_year_leak=True)
        rows, add = _rows_collector()
        qc_sweep.check_wall_calendar_zip(zpath, add)
    fails = [r for r in rows if r["severity"] == "FAIL" and r["check"] == "undated_no_year_leak"]
    check(len(fails) == 1, f"expected an undated_no_year_leak FAIL, got {rows}")
    check("2026" in fails[0]["detail"], f"got {fails}")


def test_wall_calendar_zip_fails_missing_poster():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "wc1001_calendar_pack.zip"
        _make_calendar_zip(zpath, include_poster=False)
        rows, add = _rows_collector()
        qc_sweep.check_wall_calendar_zip(zpath, add)
    fails = [r for r in rows if r["severity"] == "FAIL" and r["check"] == "poster_present"]
    check(len(fails) == 1, f"expected a poster_present FAIL, got {rows}")


def test_wall_calendar_zip_warns_low_poster_resolution():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "wc1001_calendar_pack.zip"
        _make_calendar_zip(zpath, poster_size=(1200, 1200))
        rows, add = _rows_collector()
        qc_sweep.check_wall_calendar_zip(zpath, add)
    warns = [r for r in rows if r["severity"] == "WARN" and r["check"] == "poster_resolution"]
    check(len(warns) == 1, f"expected a poster_resolution WARN, got {rows}")


def test_wall_calendar_zip_warns_missing_readme():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "wc1001_calendar_pack.zip"
        _make_calendar_zip(zpath, include_readme=False)
        rows, add = _rows_collector()
        qc_sweep.check_wall_calendar_zip(zpath, add)
    warns = [r for r in rows if r["severity"] == "WARN" and r["check"] == "readme"]
    check(len(warns) == 1, f"expected a readme WARN, got {rows}")


def test_sweep_dispatch_routes_wall_calendar_packs_dir():
    """sweep() must actually scan wall_calendars/packs/*.zip through
    check_wall_calendar_zip(), not just have the function exist unwired."""
    with tempfile.TemporaryDirectory() as tmp:
        dp_base = Path(tmp)
        packs_dir = dp_base / "wall_calendars" / "packs"
        packs_dir.mkdir(parents=True)
        _make_calendar_zip(packs_dir / "wc1001_calendar_pack.zip")
        orig_base = qc_sweep.DP_BASE
        qc_sweep.DP_BASE = dp_base
        try:
            rows = qc_sweep.sweep(only="wc1001")
        finally:
            qc_sweep.DP_BASE = orig_base
    check(any(r["check"] == "page_count" for r in rows),
          f"sweep() must route wall-calendar ZIPs through the page_count check, got {rows}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("QC SWEEP CALENDAR TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("QC SWEEP CALENDAR TESTS OK — check_wall_calendar_zip() hard-gates page count, "
          "dated-content presence, undated year-leak, and poster resolution; sweep() "
          "correctly dispatches wall_calendars/packs/*.zip through it.")


if __name__ == "__main__":
    run()
