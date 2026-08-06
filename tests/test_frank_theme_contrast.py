#!/usr/bin/env python3
"""
WCAG AA contrast test for Frank's HUD color themes (tools/api_server/
frank_hud_mockup.py).

Originally added 2026-07-18 alongside 4 new bright/light themes (Sunwashed,
Mermaid Bright, Clubroom Gold, Spring Vivid) requested by Scott: "brighter
colors but make sure text is readable." Updated 2026-08-06 for the 12->5
theme reduction ("take the color selection down to 5") -- kept themes are
Studio Warm (default), Day Mode (light), Ocean Teal, Midnight Kawaii, and
Sunwashed (the sole surviving light-surfaced bright theme); Dark Purple,
Warm Charcoal, Sakura, Matcha, Mermaid Bright, Clubroom Gold, and Spring
Vivid were archived via tools/trash.py (recoverable).

Parses the REAL --text/--muted/--cyan/--gold/--green/--red/--bg/--panel2
values straight out of the shipped `:root{...}` block and every
`html.theme-X{...}` override block via regex, rather than hand-copying them
into a second source of truth that could silently drift from what's
actually deployed. Reuses tools/color_contrast_check.py's real WCAG math
(the same checker already used for the 2026-07-15 dark-theme brightening
pass) rather than reimplementing contrast math a second time.

Checks every theme's text-on-bg and muted-on-bg (AA 4.5:1 floor), plus
text-on-panel2 and muted-on-panel2 for the light-surfaced themes specifically
(panel2 is a more saturated tint a card can actually sit on -- a value that
clears the plain bg can still fail on that tint, which is exactly what
happened once during design and got corrected before shipping).

Run: python tests/test_frank_theme_contrast.py
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from color_contrast_check import contrast_ratio, meets_wcag_aa  # noqa: E402

HUD_PATH = ROOT / "tools" / "api_server" / "frank_hud_mockup.py"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _extract_root_vars(source: str) -> dict:
    m = re.search(r":root\{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find :root{...} block in frank_hud_mockup.py"
    return _parse_var_block(m.group(1))


def _parse_var_block(block: str) -> dict:
    vars_ = {}
    for name, value in re.findall(r"--([a-zA-Z0-9]+):(#[0-9a-fA-F]{3,6}|[^;]+);", block):
        if value.startswith("#"):
            vars_[name] = value
    return vars_


def _extract_theme_blocks(source: str) -> dict:
    """Returns {theme_name: {var: hex}} for every html.theme-X{...} block."""
    themes = {}
    for m in re.finditer(r"html\.theme-([a-zA-Z0-9]+)\{(.*?)\n\}", source, re.DOTALL):
        themes[m.group(1)] = _parse_var_block(m.group(2))
    return themes


# The 5 themes kept after the 2026-08-06 12->5 reduction. "light" and
# "sunwashed" are the two light-surfaced ones -- they get the stricter
# panel2 check too, since that's exactly the surface where a first draft
# (muted on Sunwashed) initially fell short during the original 2026-07-18 pass.
EXPECTED_THEMES = {"default", "light", "ocean", "kawaii", "sunwashed"}
LIGHT_THEMES = {"light", "sunwashed"}


def test_every_theme_text_and_muted_pass_aa_on_bg():
    source = HUD_PATH.read_text(encoding="utf-8")
    root_vars = _extract_root_vars(source)
    theme_blocks = _extract_theme_blocks(source)

    # "default" (the :root block itself) plus every html.theme-X override,
    # each layered on top of root_vars (a theme block only overrides what it declares).
    all_themes = {"default": root_vars}
    for name, overrides in theme_blocks.items():
        merged = dict(root_vars)
        merged.update(overrides)
        all_themes[name] = merged

    check(set(all_themes) == EXPECTED_THEMES,
          f"expected exactly the 5 kept themes {sorted(EXPECTED_THEMES)}, got {sorted(all_themes)}")

    for name, v in all_themes.items():
        bg = v.get("bg")
        text = v.get("text")
        muted = v.get("muted")
        check(bg and text and muted, f"theme '{name}' is missing bg/text/muted: {v}")
        if not (bg and text and muted):
            continue
        r_text = contrast_ratio(text, bg)
        r_muted = contrast_ratio(muted, bg)
        check(meets_wcag_aa(text, bg), f"theme '{name}': text {text} on bg {bg} fails AA ({r_text}:1)")
        check(meets_wcag_aa(muted, bg), f"theme '{name}': muted {muted} on bg {bg} fails AA ({r_muted}:1)")


def test_light_surfaced_themes_pass_aa_on_panel2_too():
    source = HUD_PATH.read_text(encoding="utf-8")
    root_vars = _extract_root_vars(source)
    theme_blocks = _extract_theme_blocks(source)

    for name in LIGHT_THEMES:
        if name == "light":
            merged = dict(root_vars)
            merged.update(theme_blocks.get("light", {}))
        else:
            assert name in theme_blocks, f"theme '{name}' block not found"
            merged = dict(root_vars)
            merged.update(theme_blocks[name])
        panel2 = merged.get("panel2")
        text = merged.get("text")
        muted = merged.get("muted")
        check(panel2 and text and muted, f"theme '{name}' is missing panel2/text/muted: {merged}")
        if not (panel2 and text and muted):
            continue
        check(meets_wcag_aa(text, panel2), f"theme '{name}': text {text} on panel2 {panel2} fails AA ({contrast_ratio(text, panel2)}:1)")
        check(meets_wcag_aa(muted, panel2), f"theme '{name}': muted {muted} on panel2 {panel2} fails AA ({contrast_ratio(muted, panel2)}:1)")


def test_sunwashed_accent_colors_pass_aa_as_text():
    """cyan/gold are used as text/link color in several places (e.g. section
    headers, hub-listing-title accents), not just fills -- both the primary
    and the darker '2' variant must be readable on the theme's own bg."""
    source = HUD_PATH.read_text(encoding="utf-8")
    theme_blocks = _extract_theme_blocks(source)
    v = theme_blocks["sunwashed"]
    bg = v["bg"]
    for role in ("cyan", "cyan2", "gold", "gold2", "green", "red"):
        c = v.get(role)
        check(c is not None, f"theme 'sunwashed' missing --{role}")
        if c is None:
            continue
        check(meets_wcag_aa(c, bg), f"theme 'sunwashed': --{role} {c} on bg {bg} fails AA ({contrast_ratio(c, bg)}:1)")


def test_ui_themes_array_matches_the_kept_five():
    """_UI_THEMES drives the Settings swatch picker -- must list exactly the
    5 kept themes, no more (a stale/removed name would be unreachable CSS-
    wise) and no less (a theme with real CSS but no _UI_THEMES entry would
    be unreachable from the UI)."""
    source = HUD_PATH.read_text(encoding="utf-8")
    m = re.search(r"const _UI_THEMES = \[(.*?)\];", source, re.DOTALL)
    assert m, "could not find const _UI_THEMES = [...] array"
    block = m.group(1)
    names = re.findall(r"name:'([a-zA-Z0-9]+)'", block)
    check(set(names) == EXPECTED_THEMES,
          f"expected _UI_THEMES to list exactly {sorted(EXPECTED_THEMES)}, got {sorted(names)}")
    check(len(names) == len(set(names)), f"duplicate theme names in _UI_THEMES: {names}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FRANK THEME CONTRAST TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FRANK THEME CONTRAST TESTS OK — all 5 kept themes' text/muted pass WCAG AA on both "
          "bg and (for the 2 light-surfaced themes) the more saturated panel2 tint, sunwashed's "
          "accent colors are readable as text too, and _UI_THEMES lists exactly the 5 kept "
          "themes so nothing removed is still reachable from Settings.")


if __name__ == "__main__":
    run()
