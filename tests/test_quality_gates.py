#!/usr/bin/env python3
"""
Quality-gate tests — the executable enforcement of OnBrandCraftz's #1 rule:
"NEVER lie to the customer / quality never decreases as volume increases."

Why this exists: `EtsyAPIClient.pre_publish_gate()` and `validate_digital_file()`
are the code that stops a bad listing or a broken file from ever reaching a buyer
(title >140 chars, missing "Instant Download", wrong tag count, sub-$4.99 price,
mislabeled/corrupt/empty ZIP, traced-raster SVGs, near-empty PDFs). That logic had
ZERO tests — a careless edit could silently disable a check and let a violating
listing ship, and nothing would catch it. These tests lock each rule down so a
regression fails CI before it can auto-deploy.

Deliberately dependency-light and secret-free: it imports `etsy_api` (which needs
no token or network) and exercises the pure gate + validator with tiny in-memory /
tmp fixtures. No server, no API keys, no spend.

Run locally:  python tests/test_quality_gates.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a gate regressed (prints which).
"""
import io
import os
import sys
import tempfile
import traceback
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools",):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import etsy_api  # noqa: E402
from etsy_api import EtsyAPIClient, validate_digital_file, FileContentError  # noqa: E402

# ── tiny test harness (no pytest dependency, matches smoke_test.py style) ──────
_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def expect_raises(exc, fn, msg: str) -> None:
    try:
        fn()
    except exc:
        return
    except Exception as e:  # wrong exception type is still a failure
        _failures.append(f"{msg} — raised {type(e).__name__} instead of {exc.__name__}")
        return
    _failures.append(f"{msg} — expected {exc.__name__}, nothing raised")


# ── fixtures ──────────────────────────────────────────────────────────────────
def good_listing() -> dict:
    """A listing that MUST pass every gate — the baseline. Each test below mutates
    one field to prove the corresponding check fires."""
    return {
        "title": "Digital Budget Planner 2026 Undated, GoodNotes, Instant Download",
        "description": "x" * 500,
        # None of these may be a substring of the title above (that would trip the
        # tag-duplicates-title rule — see test_gate_tag_duplicates_title).
        "tags": [
            "budgeting tips", "finance planner", "money tracker", "savings planner",
            "ipad organizer", "fillable pdf", "debt payoff plan", "expense tracker",
            "kawaii stationery", "monthly budget", "cash envelopes", "digital download",
            "printable pdf",
        ],
        "price": 12.99,
        "who_made": "i_did",
        "is_supply": False,
    }


# ── pre_publish_gate tests ────────────────────────────────────────────────────
def test_gate_baseline_passes():
    fails = EtsyAPIClient.pre_publish_gate(good_listing())
    check(fails == [], f"baseline good listing should pass, got: {fails}")


def test_gate_title_too_long():
    d = good_listing()
    d["title"] = "A" * 141 + " Instant Download"  # >140
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(any("TITLE" in f and "140" in f for f in fails),
          f"title >140 chars must fail, got: {fails}")


def test_gate_title_at_limit_ok():
    d = good_listing()
    # exactly 140 chars, contains the required phrase — must NOT trip the length rule.
    # Built to hit exactly 140 while keeping "Instant Download" intact at the end
    # (truncating a longer string with [:140] risks slicing mid-word through it).
    suffix = ", Instant Download"
    base = "Budget Planner 2026 Undated GoodNotes iPad, Fillable Hyperlinked Planner, Daily Weekly Monthly, Kawaii Sticker Pack Filler"
    d["title"] = (base[:140 - len(suffix)] + suffix)
    check(len(d["title"]) == 140, f"test fixture bug: title is {len(d['title'])} chars, not 140")
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(not any("TITLE" in f and "140" in f for f in fails),
          f"title of exactly 140 chars must not trip the >140 rule, got: {fails}")


def test_gate_title_missing_instant_download():
    d = good_listing()
    d["title"] = "Digital Budget Planner 2026 Undated, GoodNotes iPad Kawaii"
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(any("Instant Download" in f for f in fails),
          f"missing 'Instant Download' must fail, got: {fails}")


def test_gate_title_too_short():
    d = good_listing()
    d["title"] = "Planner, Instant Download"  # <30 chars but has phrase
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(any("under 30" in f for f in fails),
          f"title <30 chars must fail, got: {fails}")


def test_gate_tag_count_low():
    d = good_listing()
    d["tags"] = d["tags"][:12]  # only 12
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(any("TAGS" in f and "12/13" in f for f in fails),
          f"12 tags must fail, got: {fails}")


def test_gate_tag_count_high():
    d = good_listing()
    d["tags"] = d["tags"] + ["extra tag"]  # 14
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(any("TAGS" in f and "14" in f for f in fails),
          f"14 tags must fail, got: {fails}")


def test_gate_tag_too_wide():
    d = good_listing()
    d["tags"][0] = "this tag is way too long"  # >20 chars
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(any("chars (max 20)" in f for f in fails),
          f"tag >20 chars must fail, got: {fails}")


def test_gate_tag_special_chars():
    d = good_listing()
    d["tags"][0] = "budget!planner"  # illegal char
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(any("special characters" in f for f in fails),
          f"tag with special char must fail, got: {fails}")


def test_gate_tag_duplicates_title():
    d = good_listing()
    # "budget planner" phrase also appears in the title → wasted ranking slot
    d["title"] = "Budget Planner 2026 Undated for iPad, Instant Download Kawaii"
    d["tags"][0] = "budget planner"
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(any("duplicates a title phrase" in f for f in fails),
          f"tag duplicating a title phrase must fail, got: {fails}")


def test_gate_desc_too_short():
    d = good_listing()
    d["description"] = "too short"
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(any("DESC" in f for f in fails),
          f"short description must fail, got: {fails}")


def test_gate_price_below_floor():
    d = good_listing()
    d["price"] = 3.99
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(any("below the $4.99 floor" in f for f in fails),
          f"price below $4.99 must fail, got: {fails}")


def test_gate_price_bad_ending():
    d = good_listing()
    d["price"] = 12.50  # not .99/.97/.49
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(any(".99/.97/.49" in f for f in fails),
          f"price not ending in .99/.97/.49 must fail, got: {fails}")


def test_gate_price_over_100_dollars_trusted_as_dollars():
    # 2026-08-05 full-Etsy-audit fix: this test used to assert the OPPOSITE --
    # that a price >100 gets auto-divided by 100 as "probably cents". That
    # heuristic was a real bug: every actual caller (stage_product_publish,
    # etsy_listing_tools.py, the create_listing staged-action executor) always
    # passes price in dollars, confirmed by grep -- there is no legitimate
    # cents-unit caller anywhere in this codebase. A real $149.99 bundle
    # listing (CLAUDE.md explicitly documents ZIP bundles as a real strategy
    # for working around the 5-digital-file limit) would have been silently
    # mangled into "$1.50" and false-failed both the price-floor and the
    # .99/.97/.49-ending checks. The gate now trusts dollars at face value.
    d = good_listing()
    d["title"] = "Complete OnBrandCraftz Planner Mega Bundle, GoodNotes, Instant Download"
    d["price"] = 149.99
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(not any("PRICE" in f for f in fails),
          f"a real $149.99 dollar price must be trusted as-is, got: {fails}")


def test_gate_is_supply_true_fails():
    d = good_listing()
    d["is_supply"] = True
    fails = EtsyAPIClient.pre_publish_gate(d)
    check(any("is_supply" in f for f in fails),
          f"is_supply=True must fail, got: {fails}")


# ── validate_digital_file tests ───────────────────────────────────────────────
def _write(tmp: str, name: str, data: bytes) -> str:
    p = os.path.join(tmp, name)
    with open(p, "wb") as fh:
        fh.write(data)
    return p


def _zip_bytes(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return buf.getvalue()


PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64  # valid PNG magic + filler


def test_validate_missing_file():
    with tempfile.TemporaryDirectory() as tmp:
        expect_raises(FileContentError,
                      lambda: validate_digital_file(os.path.join(tmp, "nope.zip")),
                      "missing file must raise")


def test_validate_empty_file():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "empty.zip", b"")
        expect_raises(FileContentError, lambda: validate_digital_file(p),
                      "empty file must raise")


def test_validate_extension_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "thing.png", PNG)
        expect_raises(FileContentError,
                      lambda: validate_digital_file(p, expected_ext=".zip"),
                      "extension mismatch must raise")


def test_validate_unsupported_type():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "thing.exe", b"MZ" + b"\x00" * 32)
        expect_raises(FileContentError, lambda: validate_digital_file(p),
                      "unsupported extension must raise")


def test_validate_magic_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        # named .png but content is not a PNG — a mislabeled/corrupt file that
        # would ship the wrong product
        p = _write(tmp, "fake.png", b"not really a png at all")
        expect_raises(FileContentError, lambda: validate_digital_file(p),
                      "content not matching extension magic must raise")


def test_validate_good_png():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "real.png", PNG)
        facts = validate_digital_file(p)
        check(facts.get("ext") == ".png", f"valid png should return facts, got: {facts}")


def test_validate_good_zip():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "pack.zip", _zip_bytes({"sheet1.png": PNG, "readme.txt": b"hi"}))
        facts = validate_digital_file(p)
        check(facts.get("zip_members", 0) >= 1,
              f"valid zip with content should pass, got: {facts}")


def test_validate_empty_zip():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "empty.zip", _zip_bytes({}))
        expect_raises(FileContentError, lambda: validate_digital_file(p),
                      "zip with no files must raise")


def test_validate_zip_no_product_files():
    with tempfile.TemporaryDirectory() as tmp:
        # a zip that contains only a stray unrelated file, no real deliverable
        p = _write(tmp, "junk.zip", _zip_bytes({"notes.md": b"nothing shippable"}))
        expect_raises(FileContentError, lambda: validate_digital_file(p),
                      "zip with no recognizable product files must raise")


def test_validate_zip_path_traversal():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "evil.zip", _zip_bytes({"../escape.png": PNG}))
        expect_raises(FileContentError, lambda: validate_digital_file(p),
                      "zip with path-traversal member must raise")


def test_validate_oversize():
    with tempfile.TemporaryDirectory() as tmp:
        # 21 MB PNG — over Etsy's 20 MB per-file limit
        big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (21 * 1024 * 1024)
        p = _write(tmp, "huge.png", big)
        expect_raises(FileContentError, lambda: validate_digital_file(p),
                      "file over 20 MB must raise")


# ── SVG quality tests (documented rule: no traced-raster SVGs in a pack) ───────
def _clean_svg() -> bytes:
    # a clean vector: few fills, few paths — the print-ready standard
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        b'<path d="M10 10 H90 V90 H10 Z" fill="#8666AA"/>'
        b'<path d="M20 20 H80 V80 H20 Z" fill="#C4A8D4"/>'
        b'</svg>'
    )


def _traced_raster_svg() -> bytes:
    # simulate a traced raster: hundreds of paths, each a distinct fill color
    parts = [b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">']
    for i in range(600):
        c = f"#{(i * 811) % 0xFFFFFF:06x}".encode()
        parts.append(b'<path d="M%d %d h1 v1 h-1 Z" fill="%s"/>' % (i % 100, i % 100, c))
    parts.append(b'</svg>')
    return b"".join(parts)


def test_validate_clean_svg_pack_passes():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "svg_pack.zip",
                   _zip_bytes({"layer01_base_WHITE.svg": _clean_svg(),
                               "readme.txt": b"how to print"}))
        facts = validate_digital_file(p)
        check(facts.get("svg_count", 0) == 1,
              f"clean-vector SVG pack should pass, got: {facts}")


def test_validate_traced_raster_svg_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "bad_svg_pack.zip",
                   _zip_bytes({"traced.svg": _traced_raster_svg(),
                               "readme.txt": b"how to print"}))
        expect_raises(FileContentError, lambda: validate_digital_file(p),
                      "traced-raster SVG must be rejected as not clean vector art")


# ── check_description_count_claims (2026-07-08 correction pass) ────────────────
from etsy_api import check_description_count_claims  # noqa: E402


def test_page_claim_matching_real_pages_passes():
    desc = "A complete planner.\n\nTECHNICAL DETAILS\n• Pages: 143 (each version)\n"
    problems = check_description_count_claims(desc, {"pdf_pages": 143})
    check(problems == [], f"a page claim matching the real PDF should pass, got: {problems}")


def test_page_claim_mismatching_real_pages_fails():
    desc = "TECHNICAL DETAILS\n• Pages: 143 (each version)\n"
    problems = check_description_count_claims(desc, {"pdf_pages": 88})
    check(len(problems) == 1, f"a claimed 143 pages vs. real 88 must be flagged, got: {problems}")
    check("143" in problems[0] and "88" in problems[0], f"message should cite both numbers: {problems}")


def test_unrelated_page_mentions_are_not_false_positives():
    # "365 Daily Pages" is a section name, not a total-page-count claim -- must not
    # match the loose "\d+ pages" shape, only the anchored "Pages: N" label format.
    desc = "Includes 365 Daily Pages and 52 Weekly Spreads.\n• Pages: 143 (each version)\n"
    problems = check_description_count_claims(desc, {"pdf_pages": 143})
    check(problems == [], f"unrelated 'N Daily Pages' mentions must not false-positive, got: {problems}")


def test_no_page_claim_present_is_not_flagged():
    problems = check_description_count_claims("A lovely planner with no page count listed.",
                                                {"pdf_pages": 143})
    check(problems == [], f"absence of a claim should never be flagged, got: {problems}")


def test_sticker_claim_within_zip_file_count_passes():
    desc = "Includes a Kawaii Sticker Pack ZIP — 5 PNG sticker sheets (200+ stickers)."
    problems = check_description_count_claims(desc, {"zip_members": 250})
    check(problems == [], f"a claim the ZIP can back up should pass, got: {problems}")


def test_sticker_claim_exceeding_zip_file_count_fails():
    desc = "Kawaii Sticker Pack ZIP — 200+ stickers, transparent background."
    problems = check_description_count_claims(desc, {"zip_members": 21})
    check(len(problems) == 1, f"a 200+ claim against only 21 real files must be flagged, got: {problems}")
    check("200" in problems[0] and "21" in problems[0], f"message should cite both numbers: {problems}")


def test_sticker_claim_takes_max_of_multiple_mentions():
    # Two different sticker-count mentions in the same description (e.g. hook + bullet)
    # -- the check must use the larger claim, since that's the one that would be false.
    desc = "150 stickers in the hook, but the bullet says 400+ stickers included."
    problems = check_description_count_claims(desc, {"zip_members": 200})
    check(len(problems) == 1, f"should flag against the larger (400) claim, got: {problems}")
    check("400" in problems[0], f"message should cite the larger claim: {problems}")


def test_no_facts_available_skips_check_gracefully():
    # A .zip-only listing (no PDF) has no 'pdf_pages' fact -- a page claim in the
    # description must not be flagged against a fact that doesn't exist.
    problems = check_description_count_claims("Pages: 143", {"zip_members": 50})
    check(problems == [], f"missing fact key should skip that check, not fail it, got: {problems}")


def test_empty_description_returns_no_problems():
    problems = check_description_count_claims("", {"pdf_pages": 143, "zip_members": 50})
    check(problems == [], f"empty description should never be flagged, got: {problems}")


# ── runner ────────────────────────────────────────────────────────────────────
def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ran = 0
    for t in tests:
        try:
            t()
            ran += 1
        except Exception:
            _failures.append(f"{t.__name__} raised an unexpected error:\n"
                             + traceback.format_exc())
    if _failures:
        print("QUALITY-GATE TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"QUALITY GATES OK — {ran} tests passed "
          f"(pre_publish_gate + validate_digital_file + SVG quality).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
