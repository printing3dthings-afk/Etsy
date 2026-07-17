"""
Regression test for Frank upgrade Wave 4, item B1 (2026-07-17).

tools/etsy_listing_tools.py's _PLANNER_TEMPLATES dict (and the four
_PLANNER_DESCRIPTION_DP102x constants it references) was a stale earlier
draft: pipe-separated titles over the 70-char mobile limit, and page/sheet/
sticker counts that no longer matched reality after DP1026-1029's sticker
packs were rebuilt from 5 sheets to 11 (CLAUDE.md's Product Catalog section
records the real current numbers: DP1026 143pg/328 stickers, DP1027
131pg/320, DP1028 144pg/419, DP1029 133pg/377). If this template were ever
used to (re)generate a listing, the wrong counts would directly violate the
Cardinal Rule ("page counts, sticker counts... must match the description
exactly").

A subtler bug caught while fixing this: CLAUDE.md's own "Pre-Written Listing
Content" section (the text this fix's first draft copied verbatim) still
said "5 PNG sticker sheets (200+ stickers)" -- stale relative to CLAUDE.md's
own more-recently-updated Product Catalog entries. Fixed by using the
Product Catalog's real current numbers instead, and removing the specific
"Sheet N:" ordinal claims (no verified data maps which of the real 11
physical sheets holds which theme) while keeping the (still-true) theme
descriptions.

Run: python tests/test_planner_templates_accuracy.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import etsy_listing_tools as elt  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# Real current catalog numbers, per CLAUDE.md's Product Catalog section.
_REAL = {
    "DP1026": {"pages": 143, "sheets": 11, "stickers": 328, "price": 14.99},
    "DP1027": {"pages": 131, "sheets": 11, "stickers": 320, "price": 9.99},
    "DP1028": {"pages": 144, "sheets": 11, "stickers": 419, "price": 12.99},
    "DP1029": {"pages": 133, "sheets": 11, "stickers": 377, "price": 12.99},
}


def test_all_four_products_present():
    for pid in _REAL:
        check(pid in elt._PLANNER_TEMPLATES, f"{pid} missing from _PLANNER_TEMPLATES")


def test_page_counts_match_real_catalog():
    for pid, exp in _REAL.items():
        t = elt._PLANNER_TEMPLATES[pid]
        check(t["pages"] == exp["pages"], f"{pid}: template pages={t['pages']}, real={exp['pages']}")
        check(f"{exp['pages']} pages" in t["description"] or f"{exp['pages']} beautifully" in t["description"],
              f"{pid}: description doesn't mention the real page count {exp['pages']}")
        check(f"Pages: {exp['pages']} (each version)" in t["description"],
              f"{pid}: TECHNICAL DETAILS section doesn't state the real page count")


def test_sticker_counts_match_real_catalog():
    for pid, exp in _REAL.items():
        desc = elt._PLANNER_TEMPLATES[pid]["description"]
        check(f"11 PNG sticker sheets ({exp['stickers']}+ stickers" in desc,
              f"{pid}: WHAT'S INCLUDED sticker line doesn't match the real 11-sheet/{exp['stickers']}+ pack")
        check(f"Kawaii Sticker Library × 11 — {exp['stickers']}+" in desc,
              f"{pid}: SECTIONS INCLUDED sticker library line doesn't match")
        check("5 PNG sticker sheets" not in desc, f"{pid}: still claims the stale 5-sheet count")
        check("200+ stickers" not in desc, f"{pid}: still claims the stale 200+ sticker count")


def test_files_included_matches_real_sheet_count():
    for pid, exp in _REAL.items():
        files = elt._PLANNER_TEMPLATES[pid]["files_included"]
        sticker_line = next((f for f in files if "sticker_pack.zip" in f), None)
        check(sticker_line is not None, f"{pid}: no sticker_pack.zip entry in files_included")
        if sticker_line:
            check(f"{exp['sheets']} sheets, {exp['stickers']} individual stickers" in sticker_line,
                  f"{pid}: files_included sticker line wrong, got: {sticker_line!r}")


def test_no_ordinal_sheet_labels_without_verified_mapping():
    for pid in _REAL:
        desc = elt._PLANNER_TEMPLATES[pid]["description"]
        check("Sheet 1:" not in desc and "Sheet 2:" not in desc and "Sheet 5:" not in desc,
              f"{pid}: description still claims a specific Sheet-N-to-theme mapping with no verified data behind it")


def test_titles_use_commas_not_pipes_and_respect_70_char_limit():
    for pid in _REAL:
        title = elt._PLANNER_TEMPLATES[pid]["title"]
        check("|" not in title, f"{pid}: title still uses pipe separators (CLAUDE.md requires commas), got: {title!r}")
        check(len(title) <= 70, f"{pid}: title is {len(title)} chars, over the 70-char mobile limit: {title!r}")
        check("instant download" in title.lower(), f"{pid}: title missing required 'Instant Download' phrase")


def test_prices_match_real_catalog():
    for pid, exp in _REAL.items():
        check(elt._PLANNER_TEMPLATES[pid]["price"] == exp["price"],
              f"{pid}: price {elt._PLANNER_TEMPLATES[pid]['price']} != real {exp['price']}")


def test_titles_match_claude_md_canonical_text_exactly():
    # These are copied verbatim from CLAUDE.md's "Pre-Written Listing Content"
    # section -- the shop's own designated source of truth for exact copy.
    canonical = {
        "DP1026": "Digital Planner 2026 Undated, GoodNotes iPad, Instant Download",
        "DP1027": "Kawaii Student Planner 2026, GoodNotes iPad, Instant Download",
        "DP1028": "Digital Budget Planner 2026 Undated, GoodNotes, Instant Download",
        "DP1029": "Digital Fitness Planner 2026 Undated, GoodNotes, Instant Download",
    }
    for pid, expected_title in canonical.items():
        check(elt._PLANNER_TEMPLATES[pid]["title"] == expected_title,
              f"{pid}: title doesn't match CLAUDE.md's canonical text, got: {elt._PLANNER_TEMPLATES[pid]['title']!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PLANNER TEMPLATES ACCURACY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PLANNER TEMPLATES ACCURACY TESTS OK — all 4 products' page counts, sticker "
          "counts, sheet counts, prices, and titles reconciled against CLAUDE.md's real "
          "current catalog data; no stale ordinal Sheet-N claims remain; titles use "
          "commas (not pipes) and respect the 70-char mobile limit.")


if __name__ == "__main__":
    run()
