"""
Test for the 2026-08-14 click/tap-to-dismiss addition to showToast() (fourth
item from the visual-research pass). A toast used to be un-interactive --
if it happened to sit over something the user wanted to tap, they had to
wait out the full `ms` auto-dismiss timer (default 4500ms) with no way to
clear it early.

showToast() now marks the toast element role="button" tabindex="0" and
attaches a click listener that runs the exact same exit animation +
removal the auto-dismiss timer already used, extracted into one shared
`dismiss` closure so both paths agree. Keyboard dismissal (Enter/Space)
comes for free from the existing document-level keydown handler that
already activates any role="button" element's .click() -- no separate
keydown listener needed on the toast itself.

Verified end-to-end in real headless Chrome (not just structurally here):
clicking a toast removes it well before its auto-dismiss timer would have
fired, and focusing a toast + pressing Enter does the same via the existing
global keyboard-activation handler. No page-level JS errors either way.

Run: python tests/test_toast_dismiss.py
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


def _show_toast_body() -> str:
    source = _source()
    m = re.search(r"function showToast\(message, type='info', ms=4500\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "could not find function showToast(message, type='info', ms=4500)"
    return m.group(1)


def test_toast_is_marked_as_a_reachable_button():
    body = _show_toast_body()
    check("t.setAttribute('role', 'button')" in body, "toast should be role=\"button\" so it's a real interactive control")
    check("t.setAttribute('tabindex', '0')" in body, "toast should be keyboard-reachable via tabindex=\"0\"")
    check("t.setAttribute('aria-label', 'Dismiss notification')" in body,
          "toast needs an aria-label since its visible text is the message, not the dismiss affordance")


def test_click_and_auto_dismiss_share_one_closure_not_duplicated_logic():
    body = _show_toast_body()
    check("const dismiss = () =>" in body,
          "click-dismiss and auto-dismiss should share one dismiss() closure, not two copies of the "
          "classList.add('out')/remove() sequence that could drift out of sync")
    check("t.addEventListener('click', dismiss)" in body, "toast must listen for click to dismiss early")
    out_count = body.count("classList.add('out')")
    check(out_count == 1,
          f"the exit-animation logic should appear exactly once (inside the shared dismiss() closure), "
          f"found {out_count} occurrences -- duplicated logic could drift")


def test_dismiss_cancels_the_pending_auto_timer_so_it_cant_double_fire():
    body = _show_toast_body()
    check("let autoTimer = null;" in body, "needs a handle on the auto-dismiss timer so a click can cancel it")
    check("if (autoTimer) { clearTimeout(autoTimer); autoTimer = null; }" in body,
          "dismiss() must clear the pending auto-dismiss timeout -- otherwise a manually-dismissed toast "
          "could have its (now-detached) DOM node re-processed by the timer later")
    check("if (ms) autoTimer = setTimeout(dismiss, ms);" in body,
          "the auto-dismiss path should also just call dismiss(), not a separate inline copy")


def test_toast_css_signals_it_is_clickable():
    source = _source()
    m = re.search(r"\.toast\{([^}]*)\}", source)
    assert m, "could not find .toast CSS block"
    check("cursor:pointer" in m.group(1), "the toast needs cursor:pointer so it visually reads as clickable")
    check(".toast:active{transform:scale(.98)}" in source, "needs a press-state affordance on tap/click")
    check("@media (prefers-reduced-motion:reduce){.toast:active{transform:none}}" in source,
          "the press-state scale should be disabled under prefers-reduced-motion, matching every other "
          "press-state affordance in this file")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("TOAST DISMISS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("TOAST DISMISS TESTS OK — toasts are role=\"button\" tabindex=\"0\" with a shared dismiss() "
          "closure for click and auto-dismiss, the pending timer is cancelled on manual dismiss, and the "
          "CSS signals clickability with a reduced-motion-safe press state.")


if __name__ == "__main__":
    run()
