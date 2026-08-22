"""
Functional audit of this repo's core Quality Gate functions (CLAUDE.md's
"Quality gate rule" — "If any gate fails -> listing is blocked. Fix first.
Publish never comes before truth."):

  - listing_qc.check_listing()   — ZERO existing test coverage before this
    file, despite being the actual title/tag/price/category validator
    CLAUDE.md's SS-Series/wall-art/planner pre-publish checklists describe.
  - tools/qc_sweep.py's check_sticker_zip() / check_print_zip() /
    check_planner_pdf() — real gaps found between what CLAUDE.md says these
    gates must catch and what tests/test_qc_sweep_coloring.py,
    tests/test_qc_sweep_calendar.py, and tests/test_listing_content_
    generator.py actually exercise:
      * check_sticker_zip(): only the PASS path (>=200 individual stickers)
        had a test. The documented hard-FAIL rule ("an individual-sticker
        count under 50 is now a hard FAIL... not just a warning" —
        CLAUDE.md's DP1030-1034 sticker-ZIP note) and the WARN band
        (50-199) and the transparent-background check ("Sticker PNG sheets
        have transparent backgrounds (not white fill)" — Quality Check
        Checklist) had NO test at all.
      * check_print_zip() (the wall-art multi-size ZIP gate — Gate 2 in
        CLAUDE.md's Wall Art Production Pipeline) had ZERO tests of any kind.
      * check_planner_pdf() (enforces "Page counts... match the description
        exactly" from the top-of-file Quality gate rule) had ZERO tests.

This file only ADDS coverage for real gaps -- it does not rewrite any
passing existing test, and (per audit results below) required no changes
to application code: every function audited already behaves correctly
against what CLAUDE.md documents.

Run: python tests/test_functional_audit_qc_gate_audit.py
"""
import io
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import tools.qc_sweep as qc_sweep  # noqa: E402
from tools.listing_qc import check_listing  # noqa: E402
from PIL import Image  # noqa: E402

# qc_sweep.py deliberately lazy-imports PIL as a module global inside
# sweep() so the module imports fine without PIL present -- check_sticker_
# zip()/check_print_zip() reference that global directly, so tests calling
# them without going through sweep() first must set it up once (same
# pattern as test_qc_sweep_calendar.py and test_listing_content_generator.py).
qc_sweep.Image = Image

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── listing_qc.check_listing() ──────────────────────────────────────────────
# No existing test coverage anywhere in tests/ before this file (confirmed by
# grep). This is the Maker/Checker QC gate CLAUDE.md's SS-Series/wall-art/
# planner "Pre-Publish Quality Gate Checklist" sections describe in prose.

def _good_planner_listing() -> dict:
    """A digital_planner listing that should pass every automated check --
    baseline other tests mutate one field of."""
    return {
        "title": "Digital Budget Planner 2026 Undated, GoodNotes iPad, Instant Download",
        "tags": [
            "budgeting tips", "finance planner", "money tracker", "savings planner",
            "ipad organizer", "fillable pdf", "debt payoff plan", "expense tracker",
            "kawaii stationery", "monthly budget", "cash envelopes", "digital download",
            "printable pdf",
        ],
        "description": (
            "A complete kawaii budget planner, instant download.\n\n"
            "WHAT'S INCLUDED\n- 144 pages\n\n"
            "COMPATIBLE APPS\n- GoodNotes, Notability\n\n"
            "HOW TO USE\n- tap to fill\n\n"
            "TECHNICAL DETAILS\n- PDF, US Letter\n\n"
            "FAQ\n- Q: printable? A: yes\n\n"
            "COPYRIGHT\n- personal use only\n"
        ),
        "price": 12.99,
    }


def test_baseline_planner_listing_passes_with_no_errors():
    result = check_listing(**_good_planner_listing())
    check(result["passed"] is True, f"baseline good planner listing must pass, got errors: {result['errors']}")
    check(result["errors"] == [], f"baseline should have zero errors, got: {result['errors']}")
    check(result["product_type"] == "digital_planner", f"got {result['product_type']}")


def test_title_over_140_chars_flagged_as_error():
    d = _good_planner_listing()
    d["title"] = "A" * 130 + " Instant Download"  # 148 chars, well over Etsy's hard 140 max
    check(len(d["title"]) > 140, "test fixture bug: title not actually over 140")
    result = check_listing(**d)
    matches = [e for e in result["errors"] if e["check"] == "Title ≤ 140 chars"]
    check(len(matches) == 1, f"title >140 chars must be flagged as an error, got errors: {result['errors']}")
    check(matches[0]["severity"] == "error", f"got {matches}")
    check(result["passed"] is False, "a listing with a >140 char title must not pass")


def test_title_at_exactly_140_chars_does_not_trip_length_rule():
    d = _good_planner_listing()
    suffix = ", Instant Download"
    base = "Digital Budget Planner 2026 Undated for GoodNotes iPad, Fillable Hyperlinked Kawaii Finance Tracker Bonus Sticker Pack Filler"
    d["title"] = base[: 140 - len(suffix)] + suffix
    check(len(d["title"]) == 140, f"test fixture bug: title is {len(d['title'])} chars, not 140")
    result = check_listing(**d)
    matches = [e for e in result["errors"] if e["check"] == "Title ≤ 140 chars"]
    check(matches == [], f"a title of exactly 140 chars must NOT trip the >140 rule, got: {matches}")


def test_title_length_field_reported_accurately():
    d = _good_planner_listing()
    result = check_listing(**d)
    check(result["title_length"] == len(d["title"]),
          f"title_length must reflect the real title, got {result['title_length']} vs {len(d['title'])}")


def test_tag_duplicating_title_phrase_is_flagged():
    d = _good_planner_listing()
    # "budget planner" appears verbatim in the title -- CLAUDE.md's Wall Art
    # Gate 4 calls this "the #1 tag mistake" and it applies to tag hygiene
    # generally, not just wall art.
    d["title"] = "Budget Planner 2026 Undated for iPad, Instant Download GoodNotes Kawaii"
    d["tags"][0] = "budget planner"
    result = check_listing(**d)
    dupe_issues = [i for i in (result["errors"] + result["warnings"])
                   if i["check"] == "No tags duplicate title phrases"]
    check(len(dupe_issues) == 1, f"a tag duplicating a title phrase must be flagged, got: {result}")
    check("budget planner" in dupe_issues[0]["actual"].lower(), f"got {dupe_issues}")


def test_tag_not_duplicating_title_is_not_flagged():
    # Sanity check for the positive case, to prove the duplicate-detector
    # isn't just always firing.
    result = check_listing(**_good_planner_listing())
    dupe_issues = [i for i in (result["errors"] + result["warnings"])
                   if i["check"] == "No tags duplicate title phrases"]
    check(dupe_issues == [], f"none of the baseline tags duplicate the title, must not be flagged: {dupe_issues}")


def test_price_not_ending_99_97_49_is_flagged_as_error():
    d = _good_planner_listing()
    d["price"] = 12.50  # not .99/.97/.49
    result = check_listing(**d)
    matches = [e for e in result["errors"] if e["check"] == "Price ends in .99 / .97 / .49"]
    check(len(matches) == 1, f"a price not ending in .99/.97/.49 must be flagged as an error, got: {result['errors']}")
    check("$12.50" in matches[0]["actual"], f"got {matches}")
    check(result["passed"] is False, "a listing with a bad price ending must not pass")


def test_price_ending_97_is_accepted():
    d = _good_planner_listing()
    d["price"] = 9.97
    result = check_listing(**d)
    matches = [e for e in result["errors"] if e["check"] == "Price ends in .99 / .97 / .49"]
    check(matches == [], f"a price ending in .97 must be accepted, got: {matches}")


def test_price_ending_49_is_accepted():
    d = _good_planner_listing()
    d["price"] = 14.49
    result = check_listing(**d)
    matches = [e for e in result["errors"] if e["check"] == "Price ends in .99 / .97 / .49"]
    check(matches == [], f"a price ending in .49 must be accepted, got: {matches}")


def test_price_round_dollar_is_flagged():
    d = _good_planner_listing()
    d["price"] = 10.00
    result = check_listing(**d)
    matches = [e for e in result["errors"] if e["check"] == "Price ends in .99 / .97 / .49"]
    check(len(matches) == 1, f"a round-dollar price must be flagged (CLAUDE.md: 'round numbers underperform'), got: {result['errors']}")


def test_tag_count_below_13_is_flagged_as_error():
    d = _good_planner_listing()
    d["tags"] = d["tags"][:12]
    result = check_listing(**d)
    matches = [e for e in result["errors"] if e["check"] == "All 13 tags used"]
    check(len(matches) == 1, f"12 tags (missing a slot) must be flagged, got: {result['errors']}")
    check(result["tag_count"] == 12, f"got {result['tag_count']}")


def test_tag_count_above_13_is_flagged_as_error():
    d = _good_planner_listing()
    d["tags"] = d["tags"] + ["one tag too many"]
    result = check_listing(**d)
    matches = [e for e in result["errors"] if e["check"] == "Max 13 tags"]
    check(len(matches) == 1, f"14 tags must be flagged, got: {result['errors']}")


def test_tag_over_20_chars_is_flagged_as_error():
    d = _good_planner_listing()
    d["tags"][0] = "this specific tag is way over twenty characters"
    result = check_listing(**d)
    matches = [e for e in result["errors"] if e["check"] == "Each tag ≤ 20 chars"]
    check(len(matches) == 1, f"a tag over 20 chars must be flagged, got: {result['errors']}")


def test_svg_pack_split_by_color_is_flagged():
    # tools/etsy_api.py/CLAUDE.md's SVG pipeline: "Split by Color" does not
    # exist in Bambu Studio -- a description mentioning it must be blocked.
    desc = (
        "SPLIT BY COLOR your SVG in Bambu Studio.\n\n"
        "WHAT'S INCLUDED\n- 3mf files\n\n"
        "HOW TO PRINT\n- import, split by color, slice\n\n"
        "TECHNICAL DETAILS\n- svg + 3mf\n\n"
        "FAQ\n- Q: physical? A: no, digital download only\n\n"
        "COPYRIGHT\n- personal use\n"
    )
    result = check_listing(
        title="Kawaii Cat SVG, 3D Print Sign, Instant Download",
        tags=["3d print svg"] * 13,
        description=desc,
        price=9.99,
        product_type="svg_pack",
    )
    matches = [e for e in result["errors"] if e["check"] == "Description: no 'Split by Color'"]
    check(len(matches) == 1, f"'Split by Color' in the description must be flagged, got: {result['errors']}")


def test_wall_art_title_with_pipe_separator_is_flagged():
    result = check_listing(
        title="Boho Wall Art Printable | Instant Download | Living Room Decor",
        tags=["boho wall art"] * 13,
        description="Instant download printable wall art, digital download.",
        price=6.99,
        product_type="wall_art",
    )
    matches = [e for e in result["errors"] if e["check"] == "Title: comma separators only (no pipes)"]
    check(len(matches) == 1, f"a pipe-separated wall-art title must be flagged, got: {result['errors']}")


def test_missing_all_required_planner_sections_is_flagged():
    d = _good_planner_listing()
    d["description"] = "A nice planner, instant download, buy now!"
    result = check_listing(**d)
    matches = [e for e in result["errors"] if e["check"] == "Description: all required sections present"]
    check(len(matches) == 1, f"a description missing every required section must be flagged, got: {result['errors']}")


def test_product_type_auto_detects_svg_pack_from_title():
    result = check_listing(
        title="Kawaii Cat SVG, 3D Print Sign, Instant Download",
        tags=["3d print svg"] * 13,
        description="x" * 300,
        price=9.99,
        product_type="auto",
    )
    check(result["product_type"] == "svg_pack", f"got {result['product_type']}")


# ── qc_sweep.check_sticker_zip() gap-fill ───────────────────────────────────
# Existing coverage (test_listing_content_generator.py) only exercised the
# PASS path (250 individual stickers, RGBA sheet). The documented hard-FAIL
# threshold and WARN band, and the transparent-background check, had none.

def _make_png_bytes(rgba: bool, size=(20, 20)) -> bytes:
    buf = io.BytesIO()
    mode = "RGBA" if rgba else "RGB"
    color = (255, 0, 0, 255) if rgba else (255, 0, 0)
    Image.new(mode, size, color).save(buf, "PNG")
    return buf.getvalue()


def _make_sticker_zip(path: Path, *, sheet_count=5, individual_count=250,
                       sheets_rgba=True) -> None:
    members = {f"png_sheets/s{i}.png": _make_png_bytes(rgba=sheets_rgba) for i in range(sheet_count)}
    members.update({f"individual_stickers/i{i}.png": _make_png_bytes(rgba=True) for i in range(individual_count)})
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name, data)


def _rows_collector():
    rows = []

    def add(sev, f, chk, detail=""):
        rows.append({"severity": sev, "file": f, "check": chk, "detail": detail})
    return rows, add


def test_sticker_zip_under_50_individual_is_hard_fail():
    # CLAUDE.md, DP1030-1034 sticker-pack note: "an individual-sticker count
    # under 50 is now a hard FAIL (this exact defect class), not just a
    # warning" -- the real 2026-07-09 background-removal-blob defect
    # (9 sheets x 1 sticker each).
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "TEST_sticker_pack.zip"
        _make_sticker_zip(zpath, individual_count=9)
        rows, add = _rows_collector()
        qc_sweep.check_sticker_zip(zpath, add)
    sticker_rows = [r for r in rows if r["check"] == "sticker_count"]
    check(len(sticker_rows) == 1, f"expected exactly 1 sticker_count row, got {rows}")
    check(sticker_rows[0]["severity"] == "FAIL",
          f"9 individual stickers (<50) must be a hard FAIL per CLAUDE.md, got {sticker_rows}")


def test_sticker_zip_between_50_and_199_is_warn_not_fail():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "TEST_sticker_pack.zip"
        _make_sticker_zip(zpath, individual_count=120)
        rows, add = _rows_collector()
        qc_sweep.check_sticker_zip(zpath, add)
    sticker_rows = [r for r in rows if r["check"] == "sticker_count"]
    check(len(sticker_rows) == 1, f"got {rows}")
    check(sticker_rows[0]["severity"] == "WARN",
          f"120 individual stickers (50-199 band) must be a soft WARN, not FAIL/PASS, got {sticker_rows}")


def test_sticker_zip_opaque_sheet_fails_transparency_check():
    # CLAUDE.md Quality Check Checklist: "Sticker PNG sheets have transparent
    # backgrounds (not white fill)". An RGB (no alpha) sheet must be caught,
    # not silently accepted as "imports as a white box".
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "TEST_sticker_pack.zip"
        _make_sticker_zip(zpath, sheets_rgba=False)
        rows, add = _rows_collector()
        qc_sweep.check_sticker_zip(zpath, add)
    transparency_rows = [r for r in rows if r["check"] == "transparency"]
    check(len(transparency_rows) == 1, f"expected exactly 1 transparency row, got {rows}")
    check(transparency_rows[0]["severity"] == "FAIL",
          f"an opaque (RGB, no alpha) sticker sheet must FAIL the transparency check, got {transparency_rows}")


def test_sticker_zip_transparent_sheet_passes_transparency_check():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "TEST_sticker_pack.zip"
        _make_sticker_zip(zpath, sheets_rgba=True)
        rows, add = _rows_collector()
        qc_sweep.check_sticker_zip(zpath, add)
    transparency_rows = [r for r in rows if r["check"] == "transparency"]
    check(len(transparency_rows) == 1 and transparency_rows[0]["severity"] == "PASS",
          f"an RGBA sticker sheet must PASS the transparency check, got {transparency_rows}")


# ── qc_sweep.check_print_zip() gap-fill ─────────────────────────────────────
# ZERO existing tests of any kind before this file, despite being Gate 2 of
# CLAUDE.md's Wall Art Production Pipeline ("Never upload a single JPG...").

def _make_print_zip(path: Path, *, folders=("2x3", "4x5", "a_series", "square"),
                     include_readme=True, srgb=True) -> None:
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), (10, 20, 30))
    if srgb:
        # A minimal but real ICC profile blob is overkill for this gate --
        # the check only tests `"icc_profile" in im.info`, so any non-empty
        # bytes under that key exercises the real code path faithfully.
        img.save(buf, "JPEG", icc_profile=b"fake-srgb-icc-profile-bytes")
    else:
        img.save(buf, "JPEG")
    jpg_bytes = buf.getvalue()

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder in folders:
            zf.writestr(f"{folder}/DP1030_8x10_300dpi.jpg", jpg_bytes)
        if include_readme:
            zf.writestr("README.txt", "printing instructions")


def test_print_zip_all_subfolders_present_passes():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "DP1030_print_sizes.zip"
        _make_print_zip(zpath)
        rows, add = _rows_collector()
        qc_sweep.check_print_zip(zpath, add)
    folder_rows = [r for r in rows if r["check"] == "size_folders"]
    check(len(folder_rows) == 1 and folder_rows[0]["severity"] == "PASS",
          f"all 4 required size subfolders present must PASS, got {folder_rows}")


def test_print_zip_missing_subfolder_warns():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "DP1030_print_sizes.zip"
        _make_print_zip(zpath, folders=("2x3", "4x5", "square"))  # a_series missing
        rows, add = _rows_collector()
        qc_sweep.check_print_zip(zpath, add)
    folder_rows = [r for r in rows if r["check"] == "size_folders"]
    check(len(folder_rows) == 1 and folder_rows[0]["severity"] == "WARN",
          f"a missing required size subfolder must WARN, got {folder_rows}")
    check("a_series" in folder_rows[0]["detail"], f"missing folder name should be named in the detail, got {folder_rows}")


def test_print_zip_missing_readme_warns():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "DP1030_print_sizes.zip"
        _make_print_zip(zpath, include_readme=False)
        rows, add = _rows_collector()
        qc_sweep.check_print_zip(zpath, add)
    readme_rows = [r for r in rows if r["check"] == "readme"]
    check(len(readme_rows) == 1 and readme_rows[0]["severity"] == "WARN",
          f"a missing README.txt must WARN, got {readme_rows}")


def test_print_zip_srgb_profile_present_passes():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "DP1030_print_sizes.zip"
        _make_print_zip(zpath, srgb=True)
        rows, add = _rows_collector()
        qc_sweep.check_print_zip(zpath, add)
    srgb_rows = [r for r in rows if r["check"] == "srgb"]
    check(len(srgb_rows) == 1 and srgb_rows[0]["severity"] == "PASS",
          f"a JPEG with an embedded ICC profile must PASS the srgb check, got {srgb_rows}")


def test_print_zip_no_color_profile_warns():
    # CLAUDE.md Gate 1: "Never AdobeRGB or CMYK -- Etsy auto-converts and
    # color shifts on print are a top-3 review complaint." A JPEG with no
    # embedded profile at all can't be verified as sRGB, so it must WARN.
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "DP1030_print_sizes.zip"
        _make_print_zip(zpath, srgb=False)
        rows, add = _rows_collector()
        qc_sweep.check_print_zip(zpath, add)
    srgb_rows = [r for r in rows if r["check"] == "srgb"]
    check(len(srgb_rows) == 1 and srgb_rows[0]["severity"] == "WARN",
          f"a JPEG with no embedded color profile must WARN, got {srgb_rows}")


# ── qc_sweep.check_planner_pdf() gap-fill ───────────────────────────────────
# ZERO existing tests before this file. Enforces CLAUDE.md's top-of-file
# Quality gate rule item #2: "Page counts... match the description exactly"
# for the actual planner PDF deliverable (as opposed to check_description_
# count_claims(), already tested, which only checks claim-vs-fact text
# matching, not the file-vs-catalog check this function performs).

def _make_planner_pdf_bytes(n_pages: int) -> bytes:
    from reportlab.pdfgen import canvas as pdf_canvas
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=(612, 792))
    for i in range(n_pages):
        c.drawString(50, 700, f"Page {i}")
        c.showPage()
    c.save()
    return buf.getvalue()


def test_planner_pdf_matching_catalog_page_count_passes():
    with tempfile.TemporaryDirectory() as tmp:
        # DP1026's real catalog page count per CLAUDE.md / qc_sweep.PLANNER_PAGES is 143.
        pdf_path = Path(tmp) / "DP1026.pdf"
        pdf_path.write_bytes(_make_planner_pdf_bytes(143))
        rows, add = _rows_collector()
        qc_sweep.check_planner_pdf(pdf_path, add)
    page_rows = [r for r in rows if r["check"] == "page_count"]
    check(len(page_rows) == 1 and page_rows[0]["severity"] == "PASS",
          f"143 pages matching DP1026's catalog figure must PASS, got {page_rows}")


def test_planner_pdf_page_count_far_off_catalog_warns():
    with tempfile.TemporaryDirectory() as tmp:
        # Catalog says 143; ship a PDF wildly short of that (>PAGE_TOLERANCE=8 off).
        pdf_path = Path(tmp) / "DP1026.pdf"
        pdf_path.write_bytes(_make_planner_pdf_bytes(90))
        rows, add = _rows_collector()
        qc_sweep.check_planner_pdf(pdf_path, add)
    page_rows = [r for r in rows if r["check"] == "page_count"]
    check(len(page_rows) == 1 and page_rows[0]["severity"] == "WARN",
          f"90 pages vs. catalog 143 (55 off) must WARN, got {page_rows}")


def test_planner_pdf_undated_variant_matches_same_catalog_entry():
    # dp_code_from_stem() must strip the trailing 'U' so DP1026U.pdf is
    # checked against the same 143-page catalog figure as DP1026.pdf.
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "DP1026U.pdf"
        pdf_path.write_bytes(_make_planner_pdf_bytes(143))
        rows, add = _rows_collector()
        qc_sweep.check_planner_pdf(pdf_path, add)
    page_rows = [r for r in rows if r["check"] == "page_count"]
    check(len(page_rows) == 1 and page_rows[0]["severity"] == "PASS",
          f"undated variant DP1026U.pdf must be checked against DP1026's catalog figure, got {page_rows}")


# ── runner ────────────────────────────────────────────────────────────────────
def run() -> None:
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
    print("FUNCTIONAL AUDIT TESTS OK -- listing_qc.check_listing() correctly enforces title "
          "length, tag-duplicates-title, and price-ending rules (previously zero coverage); "
          "qc_sweep.check_sticker_zip()'s hard-FAIL-under-50 and transparency checks, "
          "check_print_zip()'s full behavior, and check_planner_pdf()'s catalog page-count "
          "cross-check (all previously untested gaps) all behave correctly per CLAUDE.md.")


if __name__ == "__main__":
    run()
