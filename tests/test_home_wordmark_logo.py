"""
Test for the 2026-08-15 hand-lettered wordmark replacing the plain styled
"OnBrandCraftz" text in .mobile-shop-header (the mobile Home screen and, via
the same shared class, the mobile Ask/chat screen's header).

Scott uploaded a real logo image (script-font "OnBrandCraftz" wordmark with
a gold underline, on a solid cream background). Two static SVG assets were
generated from it under tools/api_server/static/brand/:
  - onbrandcraftz-wordmark.svg — original dark-navy ink, for light mode
  - onbrandcraftz-wordmark-dark.svg — same artwork with the ink pixels
    recolored to a light cream (gold underline unchanged, already verified
    5.28:1 against the dark bg), for dark mode

Both have the cream background AND the enclosed cream negative-space inside
the "B" loop removed via a global distance-to-sampled-background-color test
(not this codebase's existing remove_white_background(), which only clears
border-CONNECTED background and would have left the enclosed "B" highlight
as a solid patch) with a soft alpha ramp at the boundary for anti-aliasing.

A single fixed ink color would have been illegible in one of the two modes
(confirmed by screenshotting the naive single-variant version in dark mode
before this fix: near-black script text was nearly invisible against a dark
purple panel) -- both variants are always present in the DOM and swapped via
[data-mode], the same attribute-driven pattern every other mode-aware surface
in this file already uses, not JS.

Run: python tests/test_home_wordmark_logo.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUD_PATH = ROOT / "tools" / "api_server" / "frank_hud_mockup.py"
BRAND_DIR = ROOT / "tools" / "api_server" / "static" / "brand"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _source() -> str:
    return HUD_PATH.read_text(encoding="utf-8")


def test_both_svg_assets_exist_on_disk():
    check((BRAND_DIR / "onbrandcraftz-wordmark.svg").is_file(),
          "missing tools/api_server/static/brand/onbrandcraftz-wordmark.svg (light-mode variant)")
    check((BRAND_DIR / "onbrandcraftz-wordmark-dark.svg").is_file(),
          "missing tools/api_server/static/brand/onbrandcraftz-wordmark-dark.svg (dark-mode variant)")


def test_svg_files_are_well_formed_and_reasonably_sized():
    for name in ("onbrandcraftz-wordmark.svg", "onbrandcraftz-wordmark-dark.svg"):
        path = BRAND_DIR / name
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        check(content.startswith("<svg"), f"{name} should start with <svg (well-formed SVG document)")
        check('role="img"' in content and 'aria-label="OnBrandCraftz"' in content,
              f"{name} should be accessibly labeled for screen readers")
        size_kb = path.stat().st_size / 1024
        check(size_kb < 100, f"{name} is {size_kb:.0f}KB -- unexpectedly large for a palette-optimized "
                              f"embedded PNG, check the recolor/save step didn't skip palette optimization")


def test_no_stray_intermediate_files_left_behind():
    """The PNG sources used to build the SVGs (and a local test HTML page) were
    scratch intermediates -- only the final .svg files should be committed."""
    for stray in ("onbrandcraftz-wordmark.png", "onbrandcraftz-wordmark-dark.png"):
        check(not (BRAND_DIR / stray).exists(),
              f"stray intermediate {stray} should not be committed -- the SVG already embeds this data")
    check(not (ROOT / "tools" / "api_server" / "static" / "_logo_test.html").exists(),
          "stray local test HTML page should not be committed")


def test_both_screens_reference_both_variants_with_the_mode_toggle_css():
    source = _source()
    occurrences = re.findall(
        r'<div class="mobile-shop-header">'
        r'<img class="wordmark-light" src="/static/brand/onbrandcraftz-wordmark\.svg" alt="OnBrandCraftz"[^>]*>'
        r'<img class="wordmark-dark" src="/static/brand/onbrandcraftz-wordmark-dark\.svg" alt="OnBrandCraftz"[^>]*>'
        r'</div>',
        source,
    )
    check(len(occurrences) == 2,
          f"expected exactly 2 .mobile-shop-header sites (Home screen + Ask/chat screen's mobile header), "
          f"each with both wordmark variants present, found {len(occurrences)}")

    check(".mobile-shop-header .wordmark-dark{display:none}" in source,
          "the dark variant should be hidden by default (light mode is the CSS default state)")
    check(':root[data-mode="dark"] .mobile-shop-header .wordmark-light{display:none}' in source,
          "dark mode should hide the light variant")
    check(':root[data-mode="dark"] .mobile-shop-header .wordmark-dark{display:inline-block}' in source,
          "dark mode should show the dark variant")


def test_plain_text_wordmark_is_fully_gone():
    source = _source()
    check('<div class="mobile-shop-header">OnBrandCraftz</div>' not in source,
          "the old plain-text wordmark should be fully replaced, not left alongside the new image")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("HOME WORDMARK LOGO TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("HOME WORDMARK LOGO TESTS OK — both light/dark wordmark SVG assets exist and are well-formed, "
          "both .mobile-shop-header sites reference both variants with correct [data-mode] toggle CSS, "
          "no stray intermediate files were committed, and the old plain-text wordmark is fully gone.")


if __name__ == "__main__":
    run()
