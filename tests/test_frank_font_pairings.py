#!/usr/bin/env python3
"""
Test for the 2026-07-18 font-pairing picker added to Frank's Settings screen
(_FONT_PAIRINGS / _setFontPairing() in tools/api_server/frank_hud_mockup.py),
from the same visual-design-research pass as the 4 new bright color themes.

Checks:
  1. Every @font-face src url actually resolves to a real file on disk in
     tools/api_server/static/vendor/fonts/ -- a typo'd filename here would
     silently fall back to the browser default font with no error anywhere.
  2. Every font family referenced by a _FONT_PAIRINGS entry's display/body
     value has a matching @font-face declaration -- a pairing that names a
     font never actually loaded would silently render in a system font.
  3. #font-swatch-row exists in the Settings screen markup (the picker's
     mount point), and _FONT_PAIRINGS/_UI_THEMES are independent arrays
     (no accidental coupling between color theme and font pairing).

Run: python tests/test_frank_font_pairings.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUD_PATH = ROOT / "tools" / "api_server" / "frank_hud_mockup.py"
FONTS_DIR = ROOT / "tools" / "api_server" / "static" / "vendor" / "fonts"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_every_font_face_src_resolves_to_a_real_file():
    source = HUD_PATH.read_text(encoding="utf-8")
    urls = re.findall(r"src:url\('(/static/vendor/fonts/[^']+\.woff2)'\)", source)
    check(len(urls) >= 14, f"expected at least 14 @font-face declarations (4 original + 10 new), found {len(urls)}: {urls}")
    for url in urls:
        rel = url.replace("/static/vendor/fonts/", "")
        path = FONTS_DIR / rel
        check(path.is_file(), f"@font-face references '{url}' but no such file exists at {path}")


def test_font_pairings_reference_real_font_faces():
    source = HUD_PATH.read_text(encoding="utf-8")
    face_families = set(re.findall(r"@font-face\{font-family:'([^']+)'", source))
    check(len(face_families) >= 7, f"expected at least 7 distinct font families declared, got {len(face_families)}: {face_families}")

    m = re.search(r"const _FONT_PAIRINGS = \[(.*?)\n\];", source, re.DOTALL)
    assert m, "could not find const _FONT_PAIRINGS = [...] array"
    block = m.group(1)
    entries = re.findall(r"\{name:'([a-z]+)'.*?display:\"([^\"]+)\".*?body:\"([^\"]+)\"\}", block, re.DOTALL)
    check(len(entries) == 5, f"expected 5 font pairings (default + 4 new), got {len(entries)}: {[e[0] for e in entries]}")

    for name, display, body in entries:
        for role, value in [("display", display), ("body", body)]:
            first_family = value.split(",")[0].strip().strip("'")
            check(first_family in face_families,
                  f"pairing '{name}' {role} references font family '{first_family}' with no matching @font-face: {sorted(face_families)}")

    names = [e[0] for e in entries]
    for expected in ("default", "editorial", "geometric", "rounded", "precision"):
        check(expected in names, f"expected pairing '{expected}' missing from _FONT_PAIRINGS: {names}")


def test_font_swatch_row_mount_point_exists_and_is_independent_of_theme():
    source = HUD_PATH.read_text(encoding="utf-8")
    check('id="font-swatch-row"' in source, "Settings screen is missing the #font-swatch-row mount point")
    check('id="theme-swatch-row"' in source, "Settings screen is missing the #theme-swatch-row mount point (regression check)")
    # The picker sets CSS custom properties directly, not a theme-* class --
    # confirms it can't accidentally collide with _setTheme()'s class toggling.
    check("_setFontPairing" in source and "setProperty('--font-display'" in source and "setProperty('--font-body'" in source,
          "_setFontPairing() should set --font-display/--font-body directly, independent of the theme-* class system")


def test_font_pairing_localstorage_key_is_distinct_from_theme_key():
    source = HUD_PATH.read_text(encoding="utf-8")
    check("frankFontPairing" in source, "font pairing should persist under its own localStorage key, not reuse frankTheme")
    check("frankTheme" in source, "regression check: theme localStorage key should still exist")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FRANK FONT PAIRING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FRANK FONT PAIRING TESTS OK — every @font-face src resolves to a real file, "
          "every pairing's display/body references a font that's actually loaded, the "
          "picker's mount point exists independent of the color-theme system, and font "
          "pairing persists under its own localStorage key.")


if __name__ == "__main__":
    run()
