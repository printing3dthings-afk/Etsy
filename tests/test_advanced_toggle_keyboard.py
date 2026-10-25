"""
Test for the 2026-08-14 keyboard-reachability fix on .cd-advanced-toggle and
.cd-newcode-link (sixth item from the visual-research pass). Both are plain
<span onclick="..."> controls -- clickable with a mouse, but with no way for
a keyboard-only user to reach or activate them (no tabindex, so Tab skips
right over them; no role, so even a screen reader wouldn't announce them as
interactive).

Fix: role="button" tabindex="0" added to all 5 real call sites (1 static in
the template, 4 built via JS string concatenation in _createXxx() render
functions). This reuses machinery that already exists elsewhere in the file
rather than adding anything new:
  - the document-level keydown listener that activates any role="button"
    element's .click() on Enter/Space (originally added 2026-07-08, already
    covers every other role="button" control in this file)
  - the [role="button"]:focus-visible{outline:2px solid var(--cyan);...} CSS
    rule (line ~332), which already themes the focus ring for any element
    with role="button" -- no new CSS needed for these two specifically

Verified end-to-end in real headless Chrome (not just structurally here):
navigated to the real Create screen (the toggle is inside #screen-create,
display:none until navigated to -- .focus() silently no-ops on a display:none
descendant, so this had to be tested against the real visible screen, not a
bare page load), focused the toggle, and confirmed a real keyboard Enter
press invokes the same _createToggleAdvanced() handler a mouse click would.

Run: python tests/test_advanced_toggle_keyboard.py
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


def test_every_call_site_is_keyboard_reachable():
    # 2026-10-25: the digital-builder panels went, taking two of the three
    # advanced toggles and both "+ new one" links with them. The static
    # template toggle remains.
    source = _source()
    advanced_toggle_sites = re.findall(r'class="cd-advanced-toggle"[^>]*', source)
    newcode_link_sites = re.findall(r'class="cd-newcode-link"[^>]*', source)
    check(len(advanced_toggle_sites) >= 1, "expected the static .cd-advanced-toggle call site to remain")
    check(not newcode_link_sites, f"the .cd-newcode-link sites went with the digital builders, found {len(newcode_link_sites)}")
    for site in advanced_toggle_sites:
        check('role="button"' in site, f"call site missing role=\"button\": {site!r}")
        check('tabindex="0"' in site, f"call site missing tabindex=\"0\": {site!r}")


def test_onclick_handlers_are_unchanged():
    """The fix should be purely additive -- the same onclick handlers must
    still be wired, not replaced or duplicated."""
    source = _source()
    toggles = len(re.findall(r'class="cd-advanced-toggle"', source))
    check(source.count('onclick="_createToggleAdvanced(this)"') == toggles,
          "every .cd-advanced-toggle must keep its onclick=\"_createToggleAdvanced(this)\" handler")
    check("function _createToggleAdvanced(" in source, "the _createToggleAdvanced handler must still be defined")
    check("_createToggleNewCode" not in source, "no call may remain to the removed _createToggleNewCode")


def test_reuses_the_existing_global_role_button_machinery_not_new_handlers():
    """No new keydown listener or new focus CSS should be needed -- both the
    activation machinery and the focus-visible styling already exist and
    apply to any role="button" element generically."""
    source = _source()
    check('[role="button"]:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}' in source,
          "the generic [role=\"button\"]:focus-visible rule must still exist -- this fix relies on it "
          "rather than adding dedicated focus CSS for these two classes")
    check("t.getAttribute('role') === 'button'" in source,
          "the generic document-level keydown handler (Enter/Space -> .click() for any role=\"button\" "
          "element) must still exist -- this fix relies on it rather than adding its own keydown listener")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("ADVANCED TOGGLE KEYBOARD TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("ADVANCED TOGGLE KEYBOARD TESTS OK — every .cd-advanced-toggle call site "
          "is role=\"button\" tabindex=\"0\" with its onclick handler wired, reusing the existing "
          "generic role=\"button\" keyboard-activation and focus-visible machinery.")


if __name__ == "__main__":
    run()
