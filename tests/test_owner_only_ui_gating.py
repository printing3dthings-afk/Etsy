"""
Test for the 2026-08-15 ease-of-use pass: owner-only buttons are now
disabled up front for non-owner users, instead of being fully clickable
and only failing after a confirm() dialog + a real network round trip.

Context: Redeploy Server, Refresh Etsy Token Now, and Download Backup all
call endpoints gated server-side by main.py's _require_owner_or_automation()
-- a non-owner admin account (the only kind self-service signup or Google/
Apple OAuth can create, per CLAUDE.md) could always see and click these
buttons, click through a scary confirm() ("this causes a brief real
outage"), and only then discover from a bare error toast that it was never
going to work. downloadFullBackup() already had a good after-the-fact
error message for this ("Download Backup is an owner-only action — ask the
shop owner to run it.") -- this pass makes the same information available
*before* the click, consistently, across all three buttons.

`_applyRoleGating()` reads the existing `_myRole` client-side variable
(already fetched from /api/me, previously unused beyond displaying the
role badge) and disables every `[data-owner-only]` <button> for a
non-owner, with a title/tooltip explaining why, matching the same "ask the
shop owner" phrasing already established.

Verified end-to-end in real headless Chrome (not just structurally here):
logged in as a real non-owner admin account, confirmed all three buttons
render disabled with the explanatory title; promoted that same account to
owner directly in the database and confirmed the identical buttons
re-render fully enabled with no title override.

Run: python tests/test_owner_only_ui_gating.py
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


_OWNER_ONLY_BUTTON_IDS = [
    "core-btn-redeploy",
    "core-btn-refresh-token",
    "core-btn-download-backup",
]


def test_all_three_owner_only_buttons_are_marked():
    source = _source()
    for btn_id in _OWNER_ONLY_BUTTON_IDS:
        m = re.search(r'id="' + re.escape(btn_id) + r'"[^>]*', source)
        assert m, f"could not find button #{btn_id}"
        tag = m.group(0)
        check('data-owner-only="1"' in tag,
              f"#{btn_id} must carry data-owner-only=\"1\" so _applyRoleGating() finds it")


def test_apply_role_gating_only_touches_real_buttons():
    source = _source()
    m = re.search(r"function _applyRoleGating\(\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "expected a function _applyRoleGating()"
    body = m.group(1)
    check("querySelectorAll('[data-owner-only]')" in body,
          "must select every element marked data-owner-only, not a hardcoded id list "
          "(so a future button just needs the attribute, no JS change)")
    check("el.tagName !== 'BUTTON'" in body,
          "must only actually gate real <button> elements -- .disabled is meaningless "
          "on other tags and would silently no-op instead of protecting anything")
    check("el.disabled = !isOwner" in body,
          "must use the native disabled property so the onclick handler cannot fire at "
          "all for a non-owner, not a custom click-interception hack")
    check("Owner-only action" in body,
          "the disabled title must explain WHY, not just that the button doesn't work")


def test_role_gating_runs_after_role_is_known():
    source = _source()
    m = re.search(r"async function loadOperatorChip\(\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "expected async function loadOperatorChip()"
    body = m.group(1)
    check("_myRole = d.role" in body, "loadOperatorChip() must still set the real _myRole from /api/me")
    role_set_idx = body.index("_myRole = d.role")
    gating_call_idx = body.index("_applyRoleGating()")
    check(gating_call_idx > role_set_idx,
          "_applyRoleGating() must run AFTER _myRole is set from the real API response, "
          "never before (it would gate everyone as non-owner using the stale default)")


def test_bell_and_gear_icons_now_have_hover_tooltips():
    # Small companion fix from the same pass: two of the four header icon-only
    # buttons (orb switcher, tour) already had title= tooltips; the bell and
    # gear did not, leaving a sighted mouse user with zero hint what they do
    # until clicking. Matches the other two now.
    source = _source()
    bell_idx = source.index('id="bell-btn"')
    check('title="Alerts"' in source[bell_idx:bell_idx + 150],
          "the alert bell icon-btn needs a title=\"Alerts\" tooltip")
    gear_idx = source.index("onclick=\"showScreen('settings')\"")
    check('title="Settings"' in source[gear_idx:gear_idx + 150],
          "the settings gear icon-btn needs a title=\"Settings\" tooltip")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("OWNER-ONLY UI GATING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("OWNER-ONLY UI GATING TESTS OK — Redeploy/Refresh-Token/Download-Backup are all "
          "marked data-owner-only, _applyRoleGating() disables them with an explanatory title "
          "for non-owner accounts using the native disabled property, runs after the real role "
          "is known, and the bell/gear header icons now have hover tooltips matching their "
          "siblings.")


if __name__ == "__main__":
    run()
