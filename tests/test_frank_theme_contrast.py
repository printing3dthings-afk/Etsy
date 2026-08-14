#!/usr/bin/env python3
"""
WCAG AA contrast test for Frank's HUD color themes (tools/api_server/
frank_hud_mockup.py).

Rewritten 2026-08-14 for the new PALETTE x MODE system (Scott: "change the
color scheme... 3 that will actually be 6 because of light/dark"), replacing
the old flat 5-theme system this test used to check (default/light/ocean/
kawaii/sunwashed -- itself a 2026-08-06 trim from 12, archived ledger ids
20260806-001/002; the flat system itself archived 2026-08-14, ledger id
20260814-001). 3 named palettes (Studio Warm, Transformative Teal, Clubroom
Contrast) x 2 modes (dark/light) = 6 total token sets, selected via
[data-palette]/[data-mode] on <html> instead of a single theme-* class.

Parses the REAL --text/--muted/--cyan/--gold/--on-accent/--bg/--panel2 values
straight out of the shipped :root{...} block (Studio Warm dark, the bare
fallback) and every :root[data-palette="X"][data-mode="Y"]{...} override
block via regex, rather than hand-copying them into a second source of truth
that could silently drift from what's actually deployed. Reuses
tools/color_contrast_check.py's real WCAG math (the same checker already used
for the 2026-07-15 dark-theme brightening pass) rather than reimplementing
contrast math a second time.

Checks every combination's text-on-bg and muted-on-bg (AA 4.5:1 floor), plus
text-on-panel2/muted-on-panel2 for every LIGHT-mode combination specifically
(panel2 is a more saturated tint a card can actually sit on -- a value that
clears the plain bg can still fail on that tint), plus --cyan/--gold-as-text
on bg for every combination (both accents are used as text/link color in
several places, not just fills) and --on-accent (the "text/icon color for use
ON an accent-colored background" token, introduced this same pass to replace
~26 scattered hardcoded near-black hex literals) against both --cyan and
--gold specifically, since that's its entire job.

Run: python tests/test_frank_theme_contrast.py
"""
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


def _parse_var_block(block: str) -> dict:
    vars_ = {}
    for name, value in re.findall(r"--([a-zA-Z0-9-]+):(#[0-9a-fA-F]{3,6}|var\([^)]+\)|[^;]+);", block):
        vars_[name] = value
    return vars_


def _resolve(vars_: dict, key: str, root_vars: dict) -> str | None:
    """Resolve a token that may be a literal hex or `var(--other)` (only
    --on-accent uses this, aliased to --bg -- one level of indirection is
    all this needs to handle)."""
    v = vars_.get(key)
    if v is None:
        return None
    m = re.match(r"var\(--([a-zA-Z0-9-]+)\)", v)
    if m:
        return vars_.get(m.group(1)) or root_vars.get(m.group(1))
    return v if v.startswith("#") else None


def _extract_root_vars(source: str) -> dict:
    m = re.search(r":root\{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find :root{...} block in frank_hud_mockup.py"
    return _parse_var_block(m.group(1))


def _extract_palette_mode_blocks(source: str) -> dict:
    """Returns {(palette, mode): {var: hex}} for every
    :root[data-palette="X"][data-mode="Y"]{...} override block."""
    blocks = {}
    for m in re.finditer(
        r':root\[data-palette="([a-z]+)"\]\[data-mode="([a-z]+)"\]\{(.*?)\n\}',
        source, re.DOTALL,
    ):
        blocks[(m.group(1), m.group(2))] = _parse_var_block(m.group(3))
    return blocks


EXPECTED_PALETTES = {"warm", "teal", "contrast"}
EXPECTED_COMBOS = {(p, m) for p in EXPECTED_PALETTES for m in ("dark", "light")}


def _all_combos(source: str) -> dict:
    """{(palette, mode): merged_vars} for all 6 combinations. warm/dark is
    the bare :root block itself (no override block needed, same as the old
    'default' theme needing no html.theme-X class)."""
    root_vars = _extract_root_vars(source)
    override_blocks = _extract_palette_mode_blocks(source)
    combos = {}
    for combo in EXPECTED_COMBOS:
        merged = dict(root_vars)
        merged.update(override_blocks.get(combo, {}))
        combos[combo] = merged
    return combos, root_vars


def test_all_6_combinations_present_with_text_and_muted_passing_aa_on_bg():
    source = HUD_PATH.read_text(encoding="utf-8")
    override_blocks = _extract_palette_mode_blocks(source)
    # warm/dark needs no override block (bare :root covers it); the other 5 must exist explicitly.
    found_combos = set(override_blocks) | {("warm", "dark")}
    check(found_combos == EXPECTED_COMBOS,
          f"expected exactly the 6 palette x mode combinations {sorted(EXPECTED_COMBOS)}, got {sorted(found_combos)}")

    combos, _ = _all_combos(source)
    for (palette, mode), v in combos.items():
        bg, text, muted = v.get("bg"), v.get("text"), v.get("muted")
        check(bg and text and muted, f"{palette}/{mode} is missing bg/text/muted: {v}")
        if not (bg and text and muted):
            continue
        check(meets_wcag_aa(text, bg), f"{palette}/{mode}: text {text} on bg {bg} fails AA ({contrast_ratio(text, bg)}:1)")
        check(meets_wcag_aa(muted, bg), f"{palette}/{mode}: muted {muted} on bg {bg} fails AA ({contrast_ratio(muted, bg)}:1)")


def test_light_mode_combinations_pass_aa_on_panel2_too():
    source = HUD_PATH.read_text(encoding="utf-8")
    combos, _ = _all_combos(source)
    for (palette, mode), v in combos.items():
        if mode != "light":
            continue
        panel2, text, muted = v.get("panel2"), v.get("text"), v.get("muted")
        check(panel2 and text and muted, f"{palette}/{mode} is missing panel2/text/muted: {v}")
        if not (panel2 and text and muted):
            continue
        check(meets_wcag_aa(text, panel2),
              f"{palette}/{mode}: text {text} on panel2 {panel2} fails AA ({contrast_ratio(text, panel2)}:1)")
        check(meets_wcag_aa(muted, panel2),
              f"{palette}/{mode}: muted {muted} on panel2 {panel2} fails AA ({contrast_ratio(muted, panel2)}:1)")


def test_accent_colors_pass_aa_as_text_in_every_combination():
    """cyan/gold are used as text/link color in several places (e.g. section
    headers, hub-listing-title accents), not just fills -- both the primary
    and the darker/lighter '2' variant must be readable on that combination's
    own bg. This is exactly the class of thing that broke silently in a
    naive light-mode design: a dark-mode-tuned bright accent reused as-is on
    a white background."""
    source = HUD_PATH.read_text(encoding="utf-8")
    combos, _ = _all_combos(source)
    for (palette, mode), v in combos.items():
        bg = v.get("bg")
        for role in ("cyan", "cyan2", "gold", "gold2", "green", "red"):
            c = v.get(role)
            check(c is not None, f"{palette}/{mode} missing --{role}")
            if c is None:
                continue
            check(meets_wcag_aa(c, bg),
                  f"{palette}/{mode}: --{role} {c} on bg {bg} fails AA ({contrast_ratio(c, bg)}:1)")


def test_on_accent_token_passes_aa_against_both_accent_colors():
    """--on-accent (2026-08-14, replaces ~26 hardcoded near-black hex literals
    used as text/icon color on top of a --cyan or --gold background, e.g.
    .act-btn.primary, .badge, .pp-btn.ok) is aliased to var(--bg) -- verify
    that resolves to something readable against BOTH accent colors in every
    one of the 6 combinations, not just the dark ones where a near-black
    literal always happened to work by coincidence."""
    source = HUD_PATH.read_text(encoding="utf-8")
    combos, root_vars = _all_combos(source)
    for (palette, mode), v in combos.items():
        on_accent = _resolve(v, "on-accent", root_vars)
        check(on_accent is not None, f"{palette}/{mode}: --on-accent did not resolve to a real hex value")
        if on_accent is None:
            continue
        for role in ("cyan", "gold"):
            accent = v.get(role)
            if not accent:
                continue
            check(meets_wcag_aa(on_accent, accent),
                  f"{palette}/{mode}: --on-accent {on_accent} on --{role} {accent} fails AA "
                  f"({contrast_ratio(on_accent, accent)}:1)")


def test_no_hardcoded_on_accent_hex_literals_remain():
    """Regression guard for the exact defect this pass fixed: #0D1B2A/#06141f/
    #04121b/#0a1420 (four different near-black literals, all serving the same
    "text on a --cyan/--gold background" role) used to be scattered across
    ~26 call sites -- fine when every palette's accent was light-on-dark, but
    Studio Warm/Teal/Clubroom Contrast's LIGHT variants deliberately deepen
    their accent colors to clear AA against a white/cream page, which makes a
    hardcoded near-black text color dark-on-dark. Every occurrence was
    replaced with var(--on-accent); this guards against a new one creeping
    back in."""
    source = HUD_PATH.read_text(encoding="utf-8")
    for literal in ("#0D1B2A", "#0d1b2a", "#06141F", "#06141f", "#04121B", "#04121b", "#0A1420", "#0a1420"):
        check(literal not in source, f"a hardcoded on-accent near-black literal ({literal}) has crept back in -- use var(--on-accent) instead")


def test_ui_palettes_array_matches_the_3_named_palettes():
    """_UI_PALETTES drives the Settings swatch picker -- must list exactly the
    3 named palettes (a stale/removed name would be unreachable CSS-wise, a
    palette with real CSS but no _UI_PALETTES entry would be unreachable from
    the UI)."""
    source = HUD_PATH.read_text(encoding="utf-8")
    m = re.search(r"const _UI_PALETTES = \[(.*?)\];", source, re.DOTALL)
    assert m, "could not find const _UI_PALETTES = [...] array"
    block = m.group(1)
    names = re.findall(r"name:'([a-zA-Z0-9]+)'", block)
    check(set(names) == EXPECTED_PALETTES,
          f"expected _UI_PALETTES to list exactly {sorted(EXPECTED_PALETTES)}, got {sorted(names)}")
    check(len(names) == len(set(names)), f"duplicate palette names in _UI_PALETTES: {names}")


def test_early_anti_flash_script_lists_the_same_3_palettes():
    """The tiny synchronous script right after </style> (applies data-palette/
    data-mode before first paint) hand-maintains its own palette allowlist
    since it runs before _UI_PALETTES is even defined -- must stay in sync by
    hand, this test is the tripwire for that."""
    source = HUD_PATH.read_text(encoding="utf-8")
    m = re.search(r"var palettes = \[([^\]]+)\];", source)
    assert m, "could not find the early anti-flash script's palettes allowlist"
    names = set(re.findall(r"'([a-zA-Z0-9]+)'", m.group(1)))
    check(names == EXPECTED_PALETTES,
          f"early anti-flash script's palette allowlist {sorted(names)} is out of sync with "
          f"_UI_PALETTES's {sorted(EXPECTED_PALETTES)}")


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
    print("FRANK THEME CONTRAST TESTS OK — all 6 palette x mode combinations' text/muted/accent "
          "colors pass WCAG AA on bg (and, for light modes, the more saturated panel2 tint too), "
          "--on-accent resolves and passes AA against both accents in every combination, no "
          "hardcoded on-accent hex literal has crept back in, and both _UI_PALETTES and the early "
          "anti-flash script agree on exactly the 3 named palettes.")


if __name__ == "__main__":
    run()
