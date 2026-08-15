"""
Test for the 2026-08-15 desktop sidebar nav sliding pill (the "Flow" motion
thesis, validated via a live artifact comparing three candidate motion
languages — see the session's own comparison at that time). Extends the
already-shipped mobile tab bar's #ptab-pill technique (same curve/duration,
`transition:transform .38s cubic-bezier(.34,1.56,.64,1)`, proven in
production first) to the desktop sidebar, which previously only did an
instant flat background-color swap on `.nav-item.active` with no motion at
all.

Uses offsetTop/offsetHeight (not getBoundingClientRect, unlike the mobile
pill) since `.sidebar` is both the pill's positioned offsetParent AND the
scroll container — an absolutely-positioned child's translateY tracks
sidebar scroll for free that way, no separate scroll-position correction
needed the way the (non-scrolling) mobile tab bar requires.

Verified end-to-end in real headless Chrome (not just structurally here):
clicking a nav item moves #nav-pill's translateY to exactly the new active
item's real offsetTop, height matches offsetHeight, opacity stays 1
throughout, and forcing `prefers-reduced-motion: reduce` (Playwright's
`reduced_motion="reduce"` context option) zeroes the pill's computed
transition-duration to 0s.

Run: python tests/test_desktop_nav_pill.py
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


def test_pill_element_present_as_first_child_of_sidebar():
    source = _source()
    sidebar_idx = source.index('<div class="sidebar" role="navigation"')
    pill_idx = source.index('<div class="nav-pill" id="nav-pill"')
    first_nav_item_idx = source.index('data-screen="cmd"')
    check(pill_idx > sidebar_idx, "the pill must be inside .sidebar")
    check(pill_idx < first_nav_item_idx,
          "the pill should precede the nav items in the DOM (renders behind them)")
    check('aria-hidden="true"' in source[pill_idx:pill_idx + 80],
          "the pill is purely decorative and must be hidden from assistive tech")


def test_pill_css_reuses_the_proven_mobile_curve():
    source = _source()
    m = re.search(r"\.nav-pill\{([^}]*)\}", source)
    assert m, "could not find the .nav-pill CSS block"
    block = m.group(1)
    check("position:absolute" in block, "the pill must be positioned absolutely to slide via transform")
    check("cubic-bezier(.34,1.56,.64,1)" in block,
          "must reuse the exact curve already proven on the mobile #ptab-pill, not a new untested one")
    check(".38s" in block, "must reuse the exact duration already proven on the mobile #ptab-pill")
    check("transition:transform" in block,
          "must animate transform (GPU-composited), never top/left/height directly (layout-triggering)")
    check("var(--panel3)" in block and "var(--cyan)" in block,
          "the pill should carry the exact background/border-left treatment .nav-item.active used to own directly")


def test_nav_item_active_no_longer_hardcodes_background_itself():
    source = _source()
    m = re.search(r"\.nav-item\.active\{([^}]*)\}", source)
    assert m, "could not find the .nav-item.active CSS block"
    block = m.group(1)
    check("background" not in block,
          "background must now live on the animated .nav-pill, not duplicated on .nav-item.active "
          "(duplicating it would make the flat background flash instantly while the pill is still sliding)")
    check("color:var(--cyan2)" in block,
          ".nav-item.active must still set the active text color directly (instant, CSS-only, "
          "independent of whether the pill's JS positioning succeeds)")


def test_reduced_motion_block_covers_the_nav_pill():
    source = _source()
    # Anchor on .status-pill .dot (unique to the big general reduced-motion
    # block) rather than a bare first-match search -- this file has multiple
    # small single-purpose @media(prefers-reduced-motion) blocks scattered
    # around (e.g. .btn-spin's own one-liner earlier in the file), and a
    # naive search grabs whichever comes first in source order, not
    # necessarily the block .nav-pill actually lives in.
    m = re.search(
        r"@media \(prefers-reduced-motion: reduce\)\{\n  \.status-pill \.dot\{animation:none\}(.*?)\n\}\n",
        source, re.S,
    )
    assert m, "could not find the general prefers-reduced-motion block"
    block = m.group(1)
    check(".nav-pill" in block,
          "the nav pill's transition must be silenced under prefers-reduced-motion, same as the "
          "mobile .ptab-pill it's modeled on")


def test_js_observer_uses_offset_geometry_not_bounding_rect():
    source = _source()
    m = re.search(r"function moveNavPill\(\)\{(.*?)\n  \}", source, re.S)
    assert m, "could not find moveNavPill()"
    body = m.group(1)
    check("offsetTop" in body and "offsetHeight" in body,
          "must use offsetTop/offsetHeight (tracks .sidebar's own scroll for free) rather than "
          "getBoundingClientRect(), which would need a separate scroll-position correction since "
          "unlike the mobile tab bar, .sidebar actually scrolls")
    check("getBoundingClientRect" not in body,
          "moveNavPill() should not need getBoundingClientRect() at all -- offsetTop/offsetHeight "
          "relative to the positioned .sidebar ancestor is sufficient and scroll-safe by construction")


def test_js_observer_watches_class_mutations_decoupled_from_call_sites():
    source = _source()
    m = re.search(r"\(function\(\)\{\s*const sidebar = document\.querySelector\('\.sidebar'\);.*?\n\}\)\(\);", source, re.S)
    assert m, "could not find the desktop nav pill IIFE"
    body = m.group(0)
    check("new MutationObserver(scheduleNavPillMove).observe(sidebar" in body,
          "must use a MutationObserver on .sidebar (same pattern as the mobile pill's IIFE) so it "
          "stays in sync with every current and future showScreen() call site, with zero coupling")
    check("attributeFilter: ['class']" in body, "must watch specifically for class attribute changes")
    check("requestAnimationFrame" in body,
          "position updates should be scheduled via requestAnimationFrame, not run synchronously "
          "inside the mutation callback")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("DESKTOP NAV PILL TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("DESKTOP NAV PILL TESTS OK — the desktop sidebar nav now has a sliding pill indicator "
          "reusing the mobile tab bar's exact proven curve/duration, positioned via scroll-safe "
          "offset geometry, decoupled from call sites via a MutationObserver, with the active-item "
          "text color staying CSS-only/instant and the pill's motion silenced under reduced motion.")


if __name__ == "__main__":
    run()
