"""
Test for the 2026-08-14 native View Transitions wiring on showScreen() --
the foundation item from the second visual-research pass (the one flagged
as "highest-leverage" since every navigation in the app funnels through this
one function: phoneOpenScreen(), phoneTab()'s ask/create branches, every bare
onclick="showScreen(...)" in the header/sidebar/nav, and search-result routing
all call it, directly or indirectly).

showScreen() was split into a plain _showScreenInner(name, viaViewTransition)
(the actual DOM mutation, unchanged in substance from before this pass) and a
thin showScreen(name) wrapper that runs it inside document.startViewTransition()
when the browser supports the API and the user hasn't asked for reduced motion,
falling straight through to the old direct-mutation behavior otherwise.

Verified end-to-end in real headless Chrome (chromium-1194) before shipping,
not just asserted structurally here:
  - a real user click on a .nav-item fires exactly one startViewTransition()
    call and lands on the correct screen, repeatably across multiple navs
  - with prefers-reduced-motion: reduce emulated, startViewTransition() is
    never called at all and navigation still works via the plain fallback
  - no page-level JS errors either way
That live-browser check isn't re-runnable from this harness (no Node/browser
dependency in the standard test suite), so this file locks in the structural
contract instead: the split exists, the feature-detect + reduced-motion gate
is real, and the double-motion guard (skip the CSS screen-in keyframe on the
VT path only, since the native crossfade already animates that swap) doesn't
leak into the non-VT fallback path.

Run: python tests/test_view_transitions.py
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


def test_show_screen_inner_holds_the_real_dom_mutation():
    source = _source()
    m = re.search(r"function _showScreenInner\(name, viaViewTransition\)\{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find function _showScreenInner(name, viaViewTransition)"
    body = m.group(1)
    for expected in (
        "document.body.classList.remove('phone-home-open')",
        "document.querySelectorAll('.nav-item')",
        "document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'))",
        "_activeScreen = name",
        "_fireScreenLoaders(name)",
    ):
        check(expected in body, f"_showScreenInner is missing expected DOM-mutation logic: {expected!r}")


def test_show_screen_wraps_inner_in_a_feature_detected_reduced_motion_gated_transition():
    source = _source()
    m = re.search(r"function showScreen\(name\)\{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find function showScreen(name)"
    body = m.group(1)
    check("typeof document.startViewTransition === 'function'" in body,
          "must feature-detect startViewTransition rather than assuming support (Safari/Firefox lack it)")
    check("!_reducedMotion" in body,
          "must also gate on _reducedMotion -- a forced whole-page crossfade is exactly the kind of "
          "motion prefers-reduced-motion asks to skip")
    check("document.startViewTransition(() => _showScreenInner(name, true))" in body,
          "the VT path should mark the call as viaViewTransition so the double-motion guard can engage")
    check("_showScreenInner(name, false)" in body,
          "the fallback path must still call the real mutation logic directly for unsupported browsers")


def test_double_motion_guard_is_scoped_to_the_view_transition_path_only():
    source = _source()
    m = re.search(r"function _showScreenInner\(name, viaViewTransition\)\{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find function _showScreenInner(name, viaViewTransition)"
    body = m.group(1)
    check("if(viaViewTransition) el.style.animation = 'none'" in body,
          "the CSS screen-in keyframe should only be suppressed when the native VT crossfade is already "
          "animating the swap -- the non-VT fallback path must keep its existing screen-in entrance intact")


def test_all_showscreen_call_sites_still_use_the_single_public_entry_point():
    source = _source()
    # phoneOpenScreen() is the other real navigation choke point (mobile) --
    # confirm it still funnels through showScreen(), not _showScreenInner()
    # directly, so it keeps getting the VT treatment for free.
    m = re.search(r"function phoneOpenScreen\(name\)\{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find function phoneOpenScreen(name)"
    check("showScreen(name);" in m.group(1),
          "phoneOpenScreen must call the public showScreen() wrapper, not _showScreenInner() directly, "
          "or mobile navigation would silently skip the view transition")
    # No other call site in the file should call _showScreenInner directly --
    # showScreen() must stay the only entry point, or a future navigation
    # path could bypass the transition/reduced-motion gate entirely. One
    # reference is the `function _showScreenInner(...)` definition itself;
    # the rest must be exactly the two calls inside showScreen().
    all_refs = len(re.findall(r"[^_a-zA-Z]_showScreenInner\(", source))
    call_count = all_refs - 1  # minus the function definition line
    check(call_count == 2,
          f"_showScreenInner should be called from exactly two places, both inside showScreen() itself "
          f"(the VT branch and the fallback branch), found {call_count} call sites -- a stray direct "
          f"call elsewhere would bypass the VT/reduced-motion gate")


def test_root_crossfade_css_exists_and_is_reduced_motion_gated():
    source = _source()
    check("::view-transition-old(root),\n::view-transition-new(root){" in source,
          "should tune the UA default root crossfade duration/easing rather than leaving the browser default")
    m = re.search(
        r"@media \(prefers-reduced-motion: reduce\)\{\n"
        r"  ::view-transition-group\(\*\),\n"
        r"  ::view-transition-old\(\*\),\n"
        r"  ::view-transition-new\(\*\)\{\n"
        r"    animation:none !important;\n"
        r"  \}\n\}",
        source,
    )
    check(m is not None,
          "needs a CSS-level prefers-reduced-motion guard on the view-transition pseudo-elements too, as "
          "defense-in-depth alongside the JS _reducedMotion gate (same double-gating pattern already used "
          "for the orb's idle rotation elsewhere in this file)")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("VIEW TRANSITIONS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIEW TRANSITIONS TESTS OK — showScreen() wraps its DOM swap in a feature-detected, "
          "reduced-motion-gated document.startViewTransition(), the CSS screen-in double-motion guard "
          "only engages on that path, phoneOpenScreen() still funnels through the same public entry "
          "point, and the root crossfade has both JS and CSS reduced-motion gating.")


if __name__ == "__main__":
    run()
