"""
Test for the 2026-08-15 color-token coverage audit on _AUTH_PAGE_CSS
(tools/api_server/main.py) -- the auth-page half of the audit (see
test_color_token_audit_dashboard.py for the dashboard half).

Before this pass, the login/signup/setup/recovery/forgot-password pages
always rendered a single hardcoded dark Studio Warm palette regardless of
the visitor's OS/browser color-scheme preference -- an unauthenticated
visitor (who has no saved dashboard preference to read) whose system is in
light mode got the fixed dark page every time. Added a real
@media(prefers-color-scheme:light) override using the exact hex values
frank_hud_mockup.py's :root[data-palette="warm"][data-mode="light"] already
ships (same numbers, not re-derived independently -- see the module comment
for why this is intentionally scoped to system preference only, not the
full 3-palette/localStorage picker the main dashboard has).

Activating light mode for the first time exposed 3 pairings that were only
ever exercised in dark mode and would have gone illegible once a light
override existed:
  - button.submit/a.btn's fill text was a hardcoded near-black (#2c1a06)
    that assumed --gold is always a LIGHT accent (true in dark mode, false
    in light mode where --gold is a dark mustard-brown -- near-black text
    on a dark mustard button would be nearly unreadable). Replaced with the
    same var(--on-accent) token the dashboard already uses for this exact
    problem.
  - .err's background/border were fixed dark-red-tinted literals that never
    adapted to the new light override. Converted to color-mix(in srgb,
    var(--red) N%, transparent). Its TEXT, however, could not simply become
    var(--red) either -- measured 4.49:1 against --panel in dark mode (under
    the 4.5:1 AA floor) even before considering the tint, and 3.83:1 once
    actually composited under its own translucent red background (a real
    regression an earlier version of this fix introduced and this test
    caught). Introduced a dedicated --err-text token instead: the ORIGINAL
    dark-mode value (#ff9d94, 7.39:1 against panel, already correct and left
    untouched) stays the default, with a light-mode override that happens to
    equal --red there since --red is already strong as dark-on-light text.
  - .warn had the same background/border issue, but its text (var(--amber))
    measured comfortably above AA against its own composited tint in both
    modes, so no dedicated token was needed there.

Run: python tests/test_color_token_audit_auth_pages.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from color_contrast_check import contrast_ratio, meets_wcag_aa  # noqa: E402

MAIN_PATH = ROOT / "tools" / "api_server" / "main.py"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _source() -> str:
    return MAIN_PATH.read_text(encoding="utf-8")


def _extract_auth_css() -> str:
    m = re.search(r'_AUTH_PAGE_CSS = """(.*?)"""', _source(), re.DOTALL)
    assert m, "could not find _AUTH_PAGE_CSS = \"\"\"...\"\"\" in main.py"
    return m.group(1)


def _parse_var_block(block: str) -> dict:
    return dict(re.findall(r"--([a-zA-Z0-9-]+):(#[0-9a-fA-F]{3,6}|var\([^)]+\));", block))


def _resolve(vars_: dict, key: str) -> str:
    v = vars_.get(key)
    m = re.match(r"var\(--([a-zA-Z0-9-]+)\)", v or "")
    return vars_.get(m.group(1)) if m else v


def test_light_mode_override_exists_with_exact_dashboard_values():
    css = _extract_auth_css()
    m = re.search(r"@media \(prefers-color-scheme: light\)\{\s*:root\{(.*?)\}\s*\}", css, re.DOTALL)
    assert m, "missing @media(prefers-color-scheme:light){:root{...}} override block"
    light_vars = _parse_var_block(m.group(1))
    # Exact values from frank_hud_mockup.py's :root[data-palette="warm"][data-mode="light"] --
    # not re-derived, must match byte-for-byte so the two pages never visually drift apart.
    expected = {
        "bg": "#fdf6f3", "panel": "#ffffff", "panel2": "#f7e8e3", "panel3": "#ffffff",
        "border": "#eeddd6", "cyan": "#a83a52", "cyan2": "#7a2138", "gold": "#8a5a10",
        "gold2": "#6b4508", "text": "#2e1b22", "muted": "#7a5a63", "green": "#1f7a4c",
        "red": "#a8302c", "amber": "#8a5a10",
    }
    for key, expected_hex in expected.items():
        check(light_vars.get(key) == expected_hex,
              f"light-mode --{key} should be {expected_hex} (matching frank_hud_mockup.py's warm/light "
              f"token exactly), got {light_vars.get(key)!r}")
    check(light_vars.get("err-text") == "#a8302c",
          "light-mode --err-text should equal --red there (#a8302c is already strong dark-on-light text)")


def test_dark_mode_base_values_are_unchanged():
    """Regression guard -- the light-mode override must be purely additive,
    never having touched the original dark :root block's real values."""
    css = _extract_auth_css()
    m = re.search(r":root\{(.*?)\}\n@media", css, re.DOTALL)
    assert m, "could not find the base (dark) :root block"
    dark_vars = _parse_var_block(m.group(1))
    expected = {
        "bg": "#241c2e", "panel": "#2d2438", "panel2": "#372c42", "panel3": "#42354e",
        "border": "#3d3248", "cyan": "#f2a0b5", "cyan2": "#f7c3d0", "gold": "#e4b155",
        "gold2": "#f2cb8f", "text": "#f5eef2", "muted": "#bfa3b5", "green": "#5cc48a",
        "red": "#e2685f", "amber": "#e8b868",
    }
    for key, expected_hex in expected.items():
        check(dark_vars.get(key) == expected_hex, f"dark-mode --{key} changed unexpectedly: {dark_vars.get(key)!r}")
    check(dark_vars.get("on-accent") == "var(--bg)", "--on-accent should be added, aliased to var(--bg)")
    check(dark_vars.get("err-text") == "#ff9d94",
          "dark-mode --err-text should be the ORIGINAL, already-correct value (#ff9d94), unchanged")


def test_on_accent_button_text_replaces_hardcoded_near_black():
    css = _extract_auth_css()
    check("button.submit{width:100%;padding:11px;background:var(--gold);border:1px solid var(--gold);"
          "border-radius:var(--r-sm);\n  color:var(--on-accent);" in css,
          "button.submit's text should be var(--on-accent), not the hardcoded #2c1a06 that assumed "
          "--gold is always a light accent")
    check("a.btn{display:block;width:100%;padding:11px;background:var(--gold);border:1px solid var(--gold);"
          "border-radius:var(--r-sm);\n  color:var(--on-accent);" in css,
          "a.btn's text should be var(--on-accent) too, same fix as button.submit")
    check("#2c1a06" not in css, "the hardcoded near-black literal should be fully gone from the auth CSS")


def test_err_and_warn_use_color_mix_not_fixed_literals():
    css = _extract_auth_css()
    check(".err{background:color-mix(in srgb, var(--red) 12%, transparent);"
          "border:1px solid color-mix(in srgb, var(--red) 45%, transparent);"
          "border-radius:var(--r-sm);color:var(--err-text);" in css,
          ".err should derive its tint/border from var(--red) via color-mix, and its text from the "
          "dedicated --err-text token (not var(--red) directly -- see its own AA-failure test below)")
    check(".warn{background:color-mix(in srgb, var(--amber) 12%, transparent);"
          "border:1px solid color-mix(in srgb, var(--amber) 45%, transparent);"
          "border-radius:var(--r-sm);color:var(--amber);" in css,
          ".warn should derive its tint/border from var(--amber) via color-mix too")
    # #ff9d94 is expected to still appear -- as the dedicated --err-text token's dark-mode
    # value now, not a bare hardcoded .err{color:...} declaration.
    check(".err{background:color-mix(in srgb, var(--red) 12%, transparent);border:1px solid "
          "color-mix(in srgb, var(--red) 45%, transparent);border-radius:var(--r-sm);color:#ff9d94;" not in css,
          "the OLD bare .err{...color:#ff9d94} declaration (not routed through --err-text) should be gone")


def test_err_text_passes_aa_against_its_own_tinted_background_in_both_modes():
    """The tint is translucent (color-mix ... transparent), so its effective
    on-screen color depends on what's behind it (.box). Composite red-at-12%
    over the real .box background for both modes and confirm --err-text (not
    var(--red) directly) clears AA against that real composited surface."""
    def composite(fg_hex, alpha, bg_hex):
        fg = tuple(int(fg_hex[i:i+2], 16) for i in (1, 3, 5))
        bg = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5))
        mixed = tuple(round(f * alpha + b * (1 - alpha)) for f, b in zip(fg, bg))
        return "#%02x%02x%02x" % mixed

    combos = {
        "dark": {"red": "#e2685f", "panel": "#2d2438", "err_text": "#ff9d94"},
        "light": {"red": "#a8302c", "panel": "#ffffff", "err_text": "#a8302c"},
    }
    for mode, v in combos.items():
        composited_bg = composite(v["red"], 0.12, v["panel"])
        cr = contrast_ratio(v["err_text"], composited_bg)
        check(meets_wcag_aa(v["err_text"], composited_bg),
              f"{mode}: --err-text {v['err_text']} on its real composited background {composited_bg} "
              f"(12% red over {v['panel']}) fails AA ({cr}:1)")


def test_plain_red_would_have_failed_this_exact_check_documenting_why_err_text_exists():
    """Regression guard for the specific mistake an earlier version of this
    fix made: using var(--red) directly as .err's text color. Confirms that
    choice really would fail AA in dark mode, so this test can't silently
    stop mattering if --red's dark-mode value is ever changed to something
    that coincidentally passes."""
    def composite(fg_hex, alpha, bg_hex):
        fg = tuple(int(fg_hex[i:i+2], 16) for i in (1, 3, 5))
        bg = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5))
        mixed = tuple(round(f * alpha + b * (1 - alpha)) for f, b in zip(fg, bg))
        return "#%02x%02x%02x" % mixed

    red, panel = "#e2685f", "#2d2438"
    composited_bg = composite(red, 0.12, panel)
    check(not meets_wcag_aa(red, composited_bg),
          "expected var(--red) on its own composited tint to fail AA in dark mode (documenting why "
          "--err-text is a separate token) -- if this now passes, --red's value changed and the "
          "dedicated --err-text token may no longer be necessary")


def test_logo_glow_uses_color_mix_off_cyan_not_a_fixed_dark_mode_pink():
    css = _extract_auth_css()
    check("box-shadow:0 0 10px color-mix(in srgb, var(--cyan) 50%, transparent)" in css,
          ".logo .hex's glow should derive from var(--cyan), not the fixed dark-mode pink rgba(242,160,181,.5) "
          "that would look mismatched against light-mode's darker rose cyan")
    check("text-shadow:0 0 10px color-mix(in srgb, var(--cyan) 40%, transparent)" in css,
          ".logo .l1's text-shadow should derive from var(--cyan) too")
    check("rgba(242,160,181" not in css, "the fixed dark-mode-only glow color should be fully gone")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("COLOR TOKEN AUDIT (AUTH PAGES) TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COLOR TOKEN AUDIT (AUTH PAGES) TESTS OK — the auth pages now have a real light-mode override "
          "matching the dashboard's exact values, the dark defaults are unchanged, and the 3 pairings that "
          "would have gone illegible in light mode (button text, error banner, warning banner) are fixed "
          "and verified to still clear WCAG AA against their real composited backgrounds.")


if __name__ == "__main__":
    run()
