"""
Test for the 2026-08-15 color-token coverage audit on frank_hud_mockup.py
(the dashboard half of the audit -- see test_color_token_audit_auth_pages.py
for the auth-page half). Systematic sweep of every hex-literal color outside
the real :root token blocks and the legitimate non-adaptive uses (product
theme-catalog swatch data, the Studio Warm/Teal/Contrast preview swatches in
_UI_PALETTES, brand icon fills, the video letterbox background, and the
persist-warning banner -- all deliberately excluded, see the report given to
Scott for the full reasoning on each).

Confirmed real findings, all fixed here:
  1. .toast-check svg's stroke was a flat #fff -- a real WCAG failure
     (2.16:1, below the 3:1 non-text floor) in every DARK-mode combination,
     where --green is a bright, light-toned color meant to be read AS text
     on the dark bg, not painted under white. var(--on-accent) passes
     4.97-8.99:1 in all 6 combinations (measured, not assumed).
  2. .act-btn.approve's fill text and its JS twin (batchStageTags' success
     state) hardcoded the exact near-black #06140d that var(--on-accent) was
     built to replace -- missed by the original on-accent sweep because that
     one only searched the 4 literals used against --cyan/--gold, not this
     fifth one against --green.
  3. .refimg-tile .refimg-cat paired a FIXED dark overlay background with an
     ADAPTING var(--text) foreground -- correct in every dark mode (light
     text), illegible in light mode (dark text on a still-dark overlay,
     since the overlay is intentionally fixed for photo-caption legibility
     regardless of app theme). Fixed to a fixed light color, matching its
     sibling .refimg-del's already-correct fixed+fixed pairing.
  4. An entire status-pill family (.hub-lstate, .hub-qbadge, .act-sev,
     .act-card's left-border accents, .act-btn.danger/.reject, the Brand
     Kit LIVE/PLANNED pill, .ss-status.*, and the JS-side _SEV_COLORS map)
     was hardcoded to the ORIGINAL single dark Studio Warm palette -- none
     of it adapted to any of the 6 real combinations. Converted to
     color-mix(in srgb, var(--X) N%, transparent), the exact formula the
     sliding tab-bar pill already established (test_motion_flow_audit.py's
     F1 checks it), so the tint now tracks the same token the text does
     instead of a fixed RGB triple that happened to look close in one
     palette. "low" severity had no real token at all (an arbitrary blue,
     never matching any palette) -- reused var(--muted) instead of
     inventing a 4th accent color no palette defines.
  5. <meta name="theme-color"> was a stale hex matching none of the 6 real
     bg values and never updated on a palette/mode switch (Android status
     bar / installed-PWA chrome tint). Now synced from the real resolved
     --bg both at first paint (the early anti-flash script) and on every
     _applyTheme() call.

Verified end-to-end in real headless Chrome (not just structurally here):
color-mix() results resolve to the exact expected RGB+alpha for the active
combination (spot-checked warm/light and warm/dark), var(--on-accent)
renders the correct near-black/near-white against --green specifically in
both a synthetic toast-check element and a real .act-btn.approve, and
document.getElementById('meta-theme-color').content tracks --bg exactly
after a runtime palette/mode switch. No page-level JS errors.

Run: python tests/test_color_token_audit_dashboard.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUD_PATH = ROOT / "tools" / "api_server" / "frank_hud_mockup.py"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _source() -> str:
    return HUD_PATH.read_text(encoding="utf-8")


def test_toast_check_stroke_uses_on_accent():
    source = _source()
    check(".toast-check svg{width:11px;height:11px;stroke:var(--on-accent);" in source,
          "toast-check's icon stroke should be var(--on-accent), not a hardcoded #fff that fails "
          "AA against --green in dark mode")
    check("stroke:#fff" not in source, "no toast-related element should still hardcode a white stroke")


def test_approve_button_uses_on_accent_not_hardcoded_near_black():
    source = _source()
    check(".act-btn.approve{background:var(--green);color:var(--on-accent);border-color:var(--green)}" in source,
          ".act-btn.approve's text should be var(--on-accent), matching every other accent-fill button")
    check("btn.style.color='var(--on-accent)'" in source,
          "the JS-side batchStageTags() success-state color should also use var(--on-accent)")
    check("#06140d" not in source, "the near-black literal --on-accent was built to replace should be fully gone")


def test_refimg_cat_no_longer_pairs_fixed_bg_with_adapting_text():
    source = _source()
    check(".refimg-tile .refimg-cat{position:absolute;left:4px;bottom:4px;font-size:9px;font-weight:700;"
          "padding:2px 6px;border-radius:var(--r-pill);background:rgba(6,20,31,.75);color:#fff}" in source,
          ".refimg-cat should pair its fixed dark overlay with fixed light text, not var(--text) "
          "(which goes dark in light mode and becomes illegible against the still-dark overlay)")


def test_status_pill_family_uses_color_mix_not_hardcoded_tints():
    source = _source()
    for needle in (
        ".hub-lstate.draft{background:var(--panel3);color:var(--muted);border:1px solid var(--border)}",
        ".hub-lstate.active{background:color-mix(in srgb, var(--green) 18%, transparent);color:var(--green);"
        "border:1px solid color-mix(in srgb, var(--green) 40%, transparent)}",
        ".hub-qbadge.pass{background:color-mix(in srgb, var(--green) 18%, transparent);color:var(--green);"
        "border:1px solid color-mix(in srgb, var(--green) 40%, transparent)}",
        ".hub-qbadge.warn{background:color-mix(in srgb, var(--gold) 18%, transparent);color:var(--gold2);"
        "border:1px solid color-mix(in srgb, var(--gold) 40%, transparent)}",
        ".hub-qbadge.fail{background:color-mix(in srgb, var(--red) 18%, transparent);color:var(--red);"
        "border:1px solid color-mix(in srgb, var(--red) 40%, transparent)}",
        ".act-sev.high{background:color-mix(in srgb, var(--red) 18%, transparent);color:var(--red)}",
        ".act-sev.medium{background:color-mix(in srgb, var(--gold) 18%, transparent);color:var(--gold2)}",
        ".act-sev.approval{background:color-mix(in srgb, var(--green) 18%, transparent);color:var(--green);"
        "border:1px solid color-mix(in srgb, var(--green) 40%, transparent)}",
        ".ss-status.on_track{background:color-mix(in srgb, var(--green) 18%, transparent);color:var(--green)}",
        ".ss-status.building{background:color-mix(in srgb, var(--gold) 18%, transparent);color:var(--gold)}",
        ".ss-status.at_risk{background:color-mix(in srgb, var(--red) 18%, transparent);color:var(--red)}",
    ):
        check(needle in source, f"missing expected color-mix rule: {needle!r}")


def test_low_severity_reuses_muted_instead_of_an_arbitrary_blue():
    source = _source()
    check(".act-card.low{border-left-color:var(--muted)}" in source,
          "'low' severity should reuse var(--muted), not an arbitrary hardcoded blue with no palette token")
    check(".act-sev.low{background:var(--panel3);color:var(--muted)}" in source,
          ".act-sev.low should also reuse var(--muted)/var(--panel3)")
    check("low:'var(--muted)'" in source, "_SEV_COLORS.low should be var(--muted), not a hardcoded hex")
    # The old literals are still mentioned inside this pass's own root-cause comments
    # (this file's documented convention for dated fix-site notes) -- check they don't
    # appear as a live CSS/JS color declaration specifically, not that the substring
    # is absent from the whole file.
    for stray in ("border-left-color:#4a6b8a", "background:#1a2330;color:#7ba0c2", "low:'#7ba0c2'"):
        check(stray not in source, f"stray hardcoded low-severity blue declaration {stray!r} should be fully gone")


def test_danger_and_reject_buttons_reuse_the_red_token():
    source = _source()
    check(".act-btn.danger,.hub-act-btn.danger{background:none;"
          "border-color:color-mix(in srgb, var(--red) 40%, transparent);color:var(--red)}" in source,
          ".act-btn.danger should reuse var(--red), not hardcoded #5a2d3a/#e0808f")
    check(".act-btn.reject{color:var(--red);border-color:color-mix(in srgb, var(--red) 40%, transparent)}" in source,
          ".act-btn.reject should reuse var(--red), not hardcoded #e08585/#5a2d2d")


def test_brand_kit_live_planned_pill_uses_color_mix():
    source = _source()
    check("'background:color-mix(in srgb, var(--green) 18%, transparent);color:var(--green)' : "
          "'background:color-mix(in srgb, var(--amber) 18%, transparent);color:var(--amber)'" in source,
          "the Brand Kit theme-catalog LIVE/PLANNED pill should use color-mix off the real tokens, "
          "not fixed rgba(92,196,138,.18)/rgba(232,184,104,.18)")


def test_meta_theme_color_tracks_the_live_palette():
    source = _source()
    check('<meta name="theme-color" id="meta-theme-color" content="#241c2e">' in source,
          "the static default should match Studio Warm dark's real --bg (#241c2e), not the stale #070d16")
    check("const metaTheme = document.getElementById('meta-theme-color');" in source,
          "_applyTheme() should update the meta tag on every palette/mode switch")
    check("getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();" in source,
          "should read the REAL resolved --bg off the DOM rather than a hand-maintained lookup table "
          "that could drift from the actual CSS")
    check("var metaTheme = document.getElementById('meta-theme-color');" in source,
          "the early anti-flash script should also sync the meta tag before first paint, not just later")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("COLOR TOKEN AUDIT (DASHBOARD) TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COLOR TOKEN AUDIT (DASHBOARD) TESTS OK — the toast-check WCAG failure and 4 other confirmed "
          "coverage gaps (missed on-accent usage, a fixed/adapting color mismatch, an entire hardcoded "
          "status-pill family, and a stale theme-color meta tag) are all fixed and verified.")


if __name__ == "__main__":
    run()
