"""
Test for the 2026-08-15 desktop :hover coverage pass (continuation of the
"find all the things you can make better" visual-upgrade research, right
after the error-state/retry-button fix).

An earlier round (2026-08-14) added :active press-state feedback to every
primary tap target -- but :active only fires on an actual press (touch, or
mouse button held down), never on a mouse hover with no click. Auditing the
same tap-target set found that most of them (bare/approve/reject .act-btn,
.hub-toggle-btn, .hub-chip-btn, .lc-chip, .hub-prod-card.tappable,
.pcard-tap, .pp-btn, .palert.tappable, .pmore-item, the clickable
.panel-title[role="button"] section headers) had real :active rules but NO
:hover rule at all -- a desktop mouse user got zero visual feedback while
moving the cursor over a clickable element, only right at the moment of
click. `.create-choice` was the one exception that already had this right,
which is what the audit compared everything else against.

Verified end-to-end in real headless Chrome (not just structurally here):
hovering `.panel-title[role="button"]` with a real mouse move changes its
computed color (--cyan2 -> --cyan) with no click involved, and
`tools/playwright_smoke.py` (the real-browser regression check) still
passes clean with zero console errors after this change.

Run: python tests/test_hover_state_coverage.py
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


def test_act_btn_ghost_tier_and_approve_reject_have_hover():
    source = _source()
    check(".act-btn:hover,.hub-act-btn:hover{" in source,
          "the bare ghost-tier .act-btn/.hub-act-btn (used by 11+ buttons with no primary/"
          "secondary/danger modifier) needs a hover rule -- it previously had :active only")
    check(".act-btn.approve:hover{" in source,
          "the Approve button (a high-stakes irreversible action) needs hover feedback")
    check(".act-btn.reject:hover{" in source,
          "the Reject button needs hover feedback")


def test_toggle_and_chip_buttons_have_hover_that_respects_active_state():
    source = _source()
    check(".hub-toggle-btn:not(.active):hover{" in source,
          "toggle-style buttons need hover, scoped with :not(.active) so hovering an "
          "already-selected (gold-filled) toggle doesn't visually fight its own active state")
    check(".hub-chip-btn:not(.active):hover{" in source,
          "chip-style toggle buttons need the same :not(.active)-scoped hover treatment")


def test_chat_chip_has_hover():
    source = _source()
    check(".lc-chip:hover{" in source,
          "chat suggestion chips (.lc-chip) need hover -- previously only :active")


def test_tappable_cards_and_rows_have_hover():
    source = _source()
    checks = [
        (".hub-prod-card.tappable:hover{", "tappable product cards"),
        (".pcard-tap:hover{", "the printer-card tap wrapper"),
        (".palert.tappable:hover{", "tappable priority-alert rows"),
        (".pmore-item:hover{", "the More-screen menu items"),
    ]
    for needle, label in checks:
        check(needle in source, f"{label} need a :hover rule (previously :active only)")


def test_publish_confirm_buttons_have_hover():
    source = _source()
    check(".pp-btn.ok:hover{" in source, "the primary publish-confirm button needs hover feedback")
    check(".pp-btn.no:hover{" in source, "the cancel/no publish button needs hover feedback")


def test_clickable_panel_title_headers_have_hover():
    source = _source()
    m = re.search(r'\.panel-title\[role="button"\]\{([^}]*)\}', source)
    assert m, 'expected a .panel-title[role="button"] base rule'
    check("color" in m.group(1), "the transition property list must include color (added alongside "
          "the existing transform) so the new hover color change animates smoothly")
    check('.panel-title[role="button"]:hover{color:var(--cyan)}' in source,
          "clickable panel-title section headers (Star Seller, Ads & ROAS, COGS & Profit, "
          "Bambu P1S Printer, Shop Performance) need hover feedback -- they only had :active")


def test_create_choice_still_the_reference_pattern_unmodified():
    # The one tappable card that already had this right before this pass --
    # confirms the audit's baseline comparison point wasn't itself broken.
    source = _source()
    check(".create-choice:hover{box-shadow:var(--card-shadow-hover);transform:translateY(-2px)}" in source,
          "the pre-existing .create-choice hover rule (the audit's reference pattern) must be unchanged")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("HOVER STATE COVERAGE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("HOVER STATE COVERAGE TESTS OK — every primary tap target that previously had :active "
          "press-state feedback but no :hover now gives desktop mouse users real visual feedback "
          "on hover, with toggle/chip buttons correctly excluding their own .active selected state.")


if __name__ == "__main__":
    run()
