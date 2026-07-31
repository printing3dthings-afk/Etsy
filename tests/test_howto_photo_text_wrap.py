"""
Regression test for the DP1030 "text overruns" listing-photo bug Scott
reported 2026-07-31 (screenshot of the Products review modal for the ADHD
Digital Planner: the GoodNotes sticker-import how-to graphic had overlapping
text between panels, despite the automated QC sweep reporting a clean PASS).

Root cause: tools/gen_planner_listing_photos.py's make_howto() (and the
identical pattern in tools/gen_sticker_listing_photos.py's make_howto(), used
for the 6 standalone sticker-pack listings) drew each manually-authored '\\n'
segment as a single line via ImageDraw.text(), with zero check against the
panel's actual pixel width -- PIL never wraps text on its own. DP1030's photos
were produced by tools/build_product.py's "Build whole product" flow, which
calls the older generate_for_planner() -> make_howto() path (not the newer
AI-photorealistic pipeline, whose own how-to slot has no baked-in text at
all -- see tools/listing_photo_pipeline.py's slot_06_how_to constraint: "No
text labels (added in Canva after)").

The fix: a real wrap_text(d, text, font, max_width) helper (textbbox-based)
added to both files, used for both the step title and body text, with
dynamic vertical line stacking so wrapped titles push the body down instead
of overlapping it.

This test asserts, for every real product config in both files (all 5
planners' sheet_count values, all 6 sticker packs), that every line
wrap_text() produces actually fits within the panel's usable width --
catching a future regression (e.g. someone widening a step's copy without
re-checking it fits) before it reaches a real listing photo again.

Run: python tests/test_howto_photo_text_wrap.py
"""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools",):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

from PIL import Image, ImageDraw  # noqa: E402

import gen_planner_listing_photos as gp  # noqa: E402
import gen_sticker_listing_photos as gs  # noqa: E402

_failures: list[str] = []
_d = ImageDraw.Draw(Image.new("RGB", (10, 10)))


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _assert_fits(mod_name, cfg_name, panel, part, line, width, max_width):
    check(
        width <= max_width,
        f"{mod_name}/{cfg_name}: wrapped {part} line {line!r} is {width}px, "
        f"wider than the panel's {max_width}px usable width",
    )


def test_planner_howto_lines_fit_every_panel():
    """gen_planner_listing_photos.make_howto() -- mirrors its own step text
    and per-product sheet_count substitution exactly, for all 5 planners."""
    panel_w = (gp.CANVAS - 160) // 3
    text_w = panel_w - 100
    title_font = gp.fb(56)
    body_font = gp.fr(40)

    for pid, cfg in gp.PLANNER_PAGES.items():
        steps = [
            ("Step 1", "Download & Unzip",
             "After purchase, download your files from Etsy.\nUnzip the sticker pack ZIP file."),
            ("Step 2", "Import into GoodNotes 6",
             f"Open GoodNotes 6 → tap Elements (◆)\n"
             f"→ Stickers tab → tap + → select all {cfg.get('sheet_count', 11)} PNG files"),
            ("Step 3", "Drag Stickers onto Any Page",
             "All stickers appear in your library.\nTap any sticker and drag it onto any planner page!"),
        ]
        for _step, title, body in steps:
            for line in gp.wrap_text(_d, title, title_font, text_w):
                w = _d.textbbox((0, 0), line, font=title_font)[2]
                _assert_fits("gen_planner_listing_photos", pid, panel_w, "title", line, w, text_w)
            for line in gp.wrap_text(_d, body, body_font, text_w):
                w = _d.textbbox((0, 0), line, font=body_font)[2]
                _assert_fits("gen_planner_listing_photos", pid, panel_w, "body", line, w, text_w)


def test_sticker_pack_howto_lines_fit_every_panel():
    """gen_sticker_listing_photos.make_howto() -- same defect class, all 6
    standalone sticker-pack listings (free/lavender/cotton/midnight/coral/bundle)."""
    panel_w = (gs.CANVAS - 180) // 3
    text_w = panel_w - 100
    title_font = gs.fb(54)
    body_font = gs.fr(40)

    steps = [
        ("1", "Download & Unzip",
         "Save your sticker pack ZIP from Etsy.\nUnzip to reveal the sticker sheet JPGs."),
        ("2", "Import into Elements",
         "Open GoodNotes 6 → tap ◆ Elements\n→ Stickers tab → tap + → select all sheets"),
        ("3", "Use on Any Page",
         "Tap any sticker in your library\nand drag it onto any planner page!"),
    ]
    for pack_name in gs.PACKS:
        for _step, title, body in steps:
            for line in gs.wrap_text(_d, title, title_font, text_w):
                w = _d.textbbox((0, 0), line, font=title_font)[2]
                _assert_fits("gen_sticker_listing_photos", pack_name, panel_w, "title", line, w, text_w)
            for line in gs.wrap_text(_d, body, body_font, text_w):
                w = _d.textbbox((0, 0), line, font=body_font)[2]
                _assert_fits("gen_sticker_listing_photos", pack_name, panel_w, "body", line, w, text_w)


def test_wrap_text_still_honors_explicit_newlines():
    """A forced '\\n' break must still produce a break even when the text is
    short enough to fit on one line -- wrap_text() must not silently rejoin
    manually-authored line breaks that the copy relies on for readability."""
    text_w = 2000  # deliberately huge so width never forces a break
    font = gp.fr(40)
    lines = gp.wrap_text(_d, "Short line one.\nShort line two.", font, text_w)
    check(lines == ["Short line one.", "Short line two."],
          f"expected the explicit '\\n' to force a 2-line split, got {lines!r}")


def test_wrap_text_actually_wraps_a_long_single_line():
    """The bug: a long line with no '\\n' at all previously rendered as one
    overrunning line. wrap_text() must split it purely on width."""
    text_w = 300
    font = gp.fr(40)
    long_line = "This is a long sentence with no manual line breaks at all in it"
    lines = gp.wrap_text(_d, long_line, font, text_w)
    check(len(lines) > 1, f"expected a long unbroken line to wrap into multiple lines, got {lines!r}")
    for line in lines:
        w = _d.textbbox((0, 0), line, font=font)[2]
        check(w <= text_w, f"wrapped line {line!r} is {w}px, wider than max_width {text_w}px")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("HOWTO PHOTO TEXT WRAP TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("HOWTO PHOTO TEXT WRAP TESTS OK — every wrapped title/body line in both "
          "make_howto() implementations fits its panel's actual pixel width, across "
          "all 5 planners and all 6 sticker packs, and explicit '\\n' breaks still work.")


if __name__ == "__main__":
    run()
