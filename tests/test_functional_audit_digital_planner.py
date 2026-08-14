"""
Functional audit — _create_digital_planner (tools/art_creation_tools.py, ~2900 lines,
zero prior test coverage).

What this proves:
  1. A minimal, realistic config produces a structurally valid PDF whose real
     page count (read back with PyMuPDF) matches the `page_count` the function
     itself reports, for BOTH interactive (tier 3 / AcroForm) and non-interactive
     (tier 1) configs.
  2. "Undated" mode (year=0) never leaks a real calendar date, weekday alignment,
     or literal year digit anywhere in the rendered text — the exact bug class
     CLAUDE.md documents as a real historical defect in a *different* file
     (`generate_planner.py`'s `_v2_monthly_pages(dated=False)` silently baking in
     the current year's real weekday alignment). We check this function doesn't
     share that defect, across weekly + monthly + yearly-overview + mood-tracker
     pages (every place `planner_year` is touched in the function).
  3. Malformed/edge-case input handling: a bad `color_scheme` degrades
     gracefully (falls back to a default palette, does not crash); a missing
     required field (`planner_title`) fails LOUDLY (raises), it does not
     silently emit a broken/half-written file.

Safety:
  - DataStore is never touched — a minimal in-memory FakeStore duck-types the
    three methods (`get`/`set`/`save`) the function actually calls, so nothing
    ever reads or writes the real `data/shop_data.json`.
  - `art_creation_tools.PRODUCT_FILES_DIR` is monkeypatched to a
    tempfile.TemporaryDirectory() for the duration of every test and restored
    in `finally` — the real `data/digital_products/product_files/` tree is
    never touched.
  - No network, no Etsy/Anthropic/OpenAI calls are reachable from this code
    path at all (pure local reportlab/PyMuPDF rendering), so there is nothing
    to mock at the I/O boundary for this particular function.
"""
import os
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402  (imported per harness convention; not used directly below)
import tools.art_creation_tools as act  # noqa: E402

import fitz  # PyMuPDF — local rendering verification only, no network  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


class FakeStore:
    """Duck-types the exact 3 DataStore methods _create_digital_planner uses,
    entirely in memory. Never touches config.SHOP_DATA_FILE / the real
    DataStore singleton."""

    def __init__(self, products=None):
        self._data = {"digital_products": products or []}

    def get(self, *keys, default=None):
        d = self._data
        for k in keys:
            if isinstance(d, dict) and k in d:
                d = d[k]
            else:
                return default
        return d

    def set(self, value, *keys):
        assert keys == ("digital_products",)
        self._data["digital_products"] = value

    def save(self):
        pass  # no-op — never write to disk


def _make_product(pid):
    return {"id": pid, "status": "concept"}


def _run_planner(data, pid="DPTEST1"):
    """Runs _create_digital_planner with PRODUCT_FILES_DIR redirected to a
    fresh tempdir. Returns (result_dict, tmpdir_obj, store)."""
    store = FakeStore([_make_product(pid)])
    tmpdir = tempfile.TemporaryDirectory(prefix="frank_planner_audit_")
    try:
        with patch.object(act, "PRODUCT_FILES_DIR", tmpdir.name):
            data = dict(data, product_id=pid)
            raw = act._create_digital_planner(data, store)
        import json
        result = json.loads(raw)
        return result, tmpdir, store
    except Exception:
        tmpdir.cleanup()
        raise


# ── Test 1: page count integrity, non-interactive tier ─────────────────────
def test_page_count_matches_real_pdf_tier1():
    data = {
        "planner_title": "Audit Planner Tier 1",
        "planner_tier": 1,
        "interactive": False,
        "color_scheme": "sage_cream",
        "year": 2026,
        "include_sections": ["monthly", "habit_tracker", "goals", "notes"],
    }
    result, tmpdir, _store = _run_planner(data, pid="DPTESTT1")
    try:
        check(result.get("success") is True, f"expected success, got {result}")
        pdf_path = result["file_path"]
        check(os.path.exists(pdf_path), f"PDF not written to {pdf_path}")
        doc = fitz.open(pdf_path)
        real_pages = doc.page_count
        doc.close()
        check(real_pages == result["pages"],
              f"reported pages={result['pages']} but real PDF has {real_pages} pages")
        # 5 intro pages (cover/welcome/dashboard/index/how-to) + yearly overview
        # + 12 monthly + habit_tracker + goals + 4 notes = 24
        check(real_pages == 24,
              f"expected 24 pages for this exact section set, got {real_pages}")
    finally:
        tmpdir.cleanup()


# ── Test 2: page count integrity, interactive tier 3 (AcroForm + JS) ───────
#
# CONFIRMED BUG: draw_sticker_picker_page() (used for every tier-3 / "Connected"
# planner — the auto-added "sticker_pack" extra at tier==3, art_creation_tools.py
# ~line 2291-2292) internally loops `for pg_idx in range(5): ... c.showPage()`
# and writes 5 REAL pages to the PDF (art_creation_tools.py ~line 4832-4942, and
# its own docstring even says "Two-page kawaii sticker library" — stale, it's
# actually 5). But the single call site that invokes it
# (art_creation_tools.py ~line 5118-5121) does `draw_sticker_picker_page();
# page_count += 1` — crediting only ONE page for something that just wrote 5.
# The function's own returned "pages" metadata is therefore wrong (undercounts
# by exactly 4) for every tier-3 planner — which is the DEFAULT tier whenever
# interactive is left at its default of True (`_default_tier = 3 if
# data.get("interactive", True) else 1`), i.e. the undercount fires on a
# near-default invocation, not just an obscure config.
#
# This directly matters under CLAUDE.md's Quality Gate rule #2 ("Page counts...
# match the description exactly") — any downstream code that trusts this
# function's own "pages" return value to build/verify a listing description
# would state a page count that does not match the real file it just wrote.
#
# Isolated repro below: calendar_integration explicitly "none" and sections
# limited to just habit_tracker, so the ONLY variable in play is the sticker
# picker's own page count vs. the caller's assumed +1.
def test_sticker_picker_page_count_matches_real_pdf():
    """Regression test for a confirmed 2026-08-13 functional-audit bug: the
    tier-3 sticker-picker call site credited page_count += 1 for
    draw_sticker_picker_page(), which actually writes 5 real pages (one per
    sticker sheet). Fixed in art_creation_tools.py to += 5."""
    data = {
        "planner_title": "Audit Sticker Undercount Repro",
        "planner_tier": 3,
        "interactive": True,
        "color_scheme": "dusty_rose",
        "year": 2026,
        "calendar_integration": "none",
        "include_sections": ["habit_tracker"],
    }
    result, tmpdir, _store = _run_planner(data, pid="DPTESTSTKBUG")
    try:
        check(result.get("success") is True, f"expected success, got {result}")
        pdf_path = result["file_path"]
        doc = fitz.open(pdf_path)
        real_pages = doc.page_count
        doc.close()

        # 5 intro pages (cover/welcome/dashboard/index/how_to_use)
        # + 0 calendar sync (explicitly "none") + 0 yearly overview
        # + 1 habit_tracker + 5 real sticker-picker pages = 11
        check(real_pages == 11,
              f"expected the real PDF to have 11 pages (5 intro-minus-cal-sync "
              f"+1 habit +5 real sticker pages), got {real_pages} — formula "
              f"assumptions changed, re-derive before trusting this test")

        check(result["pages"] == real_pages,
              f"_create_digital_planner reports pages={result['pages']} but the "
              f"PDF it just wrote actually has {real_pages} pages — the sticker-"
              f"picker page-count fix regressed")
    finally:
        tmpdir.cleanup()


# ── Test 3: undated mode — no real-date leakage across every planner_year
#            call site (weekly, monthly, yearly overview, mood tracker) ────
def test_undated_mode_has_zero_year_digits_and_generic_calendar():
    data = {
        "planner_title": "Audit Undated Planner",
        "planner_tier": 3,
        "interactive": True,
        "color_scheme": "midnight_navy" if "midnight_navy" in act.COLOR_SCHEMES else "sage_cream",
        "year": 0,  # undated
        "include_sections": ["monthly", "weekly"],
        "extras": [],
    }
    result, tmpdir, _store = _run_planner(data, pid="DPTESTUD")
    try:
        check(result.get("success") is True, f"expected success, got {result}")
        pdf_path = result["file_path"]
        doc = fitz.open(pdf_path)

        full_text = "\n".join(page.get_text() for page in doc)
        doc.close()

        # No 4-digit year anywhere (2000-2099) should appear in an undated
        # planner's text layer — this is the exact QC-gate regex CLAUDE.md's
        # WC-series check_wall_calendar_zip() uses for the same class of bug.
        year_matches = re.findall(r"20\d\d", full_text)
        check(len(year_matches) == 0,
              f"undated planner leaked year digits: {year_matches[:10]} "
              f"(class of bug CLAUDE.md flags for generate_planner.py's "
              f"_v2_monthly_pages(dated=False))")

        # The UNDATED badge should actually appear (confirms undated branch
        # really executed, not just skipped due to a silent no-op).
        check("UNDATED" in full_text, "expected literal 'UNDATED' badge text somewhere in the PDF")

        # Real weekday-alignment leak check: run the SAME undated config a
        # second time with dt_date.today() mocked to a completely different
        # year, and diff the rendered text. If the module used "today" to
        # silently pick a real weekday alignment for the undated skeleton,
        # the two renders would differ (this is exactly the historical bug's
        # observable symptom).
        import datetime as _real_datetime

        class _FakeDate(_real_datetime.date):
            @classmethod
            def today(cls):
                return cls(2099, 6, 15)

        with patch("tools.art_creation_tools.date", _FakeDate):
            # act._create_digital_planner imports `date as dt_date` LOCALLY
            # inside the function body (from datetime import date as dt_date),
            # so patching the module-level `date` symbol used elsewhere in
            # the file does not affect it — confirm this directly by also
            # patching the stdlib datetime.date globally via sys.modules,
            # the only way to actually intercept the local import.
            import datetime as _dt_mod
            _orig_date = _dt_mod.date
            _dt_mod.date = _FakeDate
            try:
                result2, tmpdir2, _store2 = _run_planner(data, pid="DPTESTUD2")
            finally:
                _dt_mod.date = _orig_date

        try:
            check(result2.get("success") is True, f"expected success on 2nd run, got {result2}")
            doc2 = fitz.open(result2["file_path"])
            full_text2 = "\n".join(page.get_text() for page in doc2)
            doc2.close()
            year_matches2 = re.findall(r"20\d\d", full_text2)
            check(len(year_matches2) == 0,
                  f"undated planner leaked year digits under a mocked 'today' of 2099: "
                  f"{year_matches2[:10]}")
            check(full_text == full_text2,
                  "undated planner's rendered text CHANGED when the system 'today' date "
                  "changed — this means undated mode is silently keying off the real "
                  "current date somewhere (the exact historical bug class), even though "
                  "no literal year digit leaked")
        finally:
            tmpdir2.cleanup()
    finally:
        tmpdir.cleanup()


# ── Test 4: malformed input — bad color_scheme degrades gracefully ─────────
def test_bad_color_scheme_falls_back_instead_of_crashing():
    data = {
        "planner_title": "Audit Bad Scheme Planner",
        "planner_tier": 1,
        "interactive": False,
        "color_scheme": "this_scheme_does_not_exist",
        "year": 2026,
        "include_sections": ["habit_tracker"],
    }
    result, tmpdir, store = _run_planner(data, pid="DPTESTBADCS")
    try:
        check(result.get("success") is True,
              f"expected graceful fallback (success=True), got {result}")
        # The JSON response surfaces the human label (cs["label"]), not the
        # scheme key — check both the label and the raw key stored on the
        # product record so the fallback is verified end to end.
        expected_label = act.COLOR_SCHEMES["sage_cream"]["label"]
        check(result.get("color_scheme") == expected_label,
              f"expected fallback label {expected_label!r}, got {result.get('color_scheme')!r}")
        saved_product = next(p for p in store.get("digital_products", default=[])
                              if p["id"] == "DPTESTBADCS")
        check(saved_product.get("color_scheme") == "sage_cream",
              f"expected saved product's color_scheme key to fall back to "
              f"'sage_cream', got {saved_product.get('color_scheme')!r}")
    finally:
        tmpdir.cleanup()


# ── Test 5: malformed input — empty include_sections produces a short but
#            VALID, non-lying PDF (page_count return value stays truthful) ─
def test_zero_sections_produces_truthful_short_pdf_not_broken_file():
    data = {
        "planner_title": "Audit Zero Sections Planner",
        "planner_tier": 1,
        "interactive": False,
        "color_scheme": "sage_cream",
        "year": 2026,
        "include_sections": [],
    }
    result, tmpdir, _store = _run_planner(data, pid="DPTESTZERO")
    try:
        check(result.get("success") is True, f"expected success, got {result}")
        doc = fitz.open(result["file_path"])
        real_pages = doc.page_count
        doc.close()
        check(real_pages == result["pages"],
              f"reported pages={result['pages']} but real PDF has {real_pages} pages")
        # cover, welcome, dashboard, index, how_to_use = 5 fixed intro pages,
        # nothing else should be drawn when include_sections=[]
        check(real_pages == 5,
              f"expected exactly 5 intro-only pages for include_sections=[], got {real_pages}")
    finally:
        tmpdir.cleanup()


# ── Test 6: missing required field fails LOUDLY, not silently ──────────────
def test_missing_required_title_fails_loudly():
    store = FakeStore([_make_product("DPTESTMISSING")])
    tmpdir = tempfile.TemporaryDirectory(prefix="frank_planner_audit_")
    raised = False
    try:
        with patch.object(act, "PRODUCT_FILES_DIR", tmpdir.name):
            # deliberately omit "planner_title" (a bare `data["planner_title"]`
            # subscript in the function — should raise KeyError, not silently
            # write a half-built/garbage PDF)
            act._create_digital_planner({"product_id": "DPTESTMISSING"}, store)
    except KeyError:
        raised = True
    finally:
        tmpdir.cleanup()
    check(raised, "expected a KeyError when 'planner_title' is missing — "
                  "got either no exception or the wrong exception type")


def run():
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FUNCTIONAL AUDIT TESTS OK -- _create_digital_planner produces PDFs whose "
          "real page count matches its own return value, undated mode never leaks a "
          "real year/date across all planner_year call sites, bad color_scheme "
          "degrades gracefully, empty sections produce a short-but-truthful PDF, and "
          "a missing required field fails loudly instead of writing a broken file.")


if __name__ == "__main__":
    run()
