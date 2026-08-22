"""
Test for the 2026-08-15 restoration of the Security screen's Team Access
(add/list/remove teammate) UI.

Context: this ease-of-use audit found loadUsers()/addUser()/deleteUser()/
resetUserPw() and their /api/admin/users backend (owner-only,
_require_owner) were real and fully working, but had been left with no DOM
container to render into at all -- #user-list, #new-user-name, #new-user-pw
had zero matches anywhere in the markup. A stale nearby comment ("Security
screen is a static checklist + admin user management") confirms this UI
used to exist and was dropped at some point without the JS/backend being
cleaned up alongside it. Scott asked for it back, gated correctly.

renderSecurityPosture() now appends a "Team Access" section -- but ONLY
when `_myRole === 'owner'`, and the check hides the section from the DOM
entirely rather than rendering it disabled: the list itself would 403 for
a non-owner (GET /api/admin/users is _require_owner too), so showing an
error state would be worse UX than not showing it at all, consistent with
how this same audit pass gated the AI Core screen's owner-only buttons.

Verified end-to-end in real headless Chrome (not just structurally here):
a non-owner test account sees no "Team Access" heading and no #user-list
element anywhere on the Security screen; the same account promoted to
owner sees the full section, adding a real teammate via the real form
actually shows it in the list with working Reset PW / Remove buttons, and
removing it actually drops it from the list -- the full real round trip
against the real /api/admin/users backend, not just presence checks.

Run: python tests/test_team_access_restored.py
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


def test_team_access_section_only_appended_for_owner():
    source = _source()
    m = re.search(r"function renderSecurityPosture\(\) \{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "expected function renderSecurityPosture()"
    body = m.group(1)
    check("if (_myRole === 'owner')" in body,
          "the Team Access section must be conditionally built, not always included")
    # The conditional block containing the section markup must appear before
    # the innerHTML assignment (built into `html`, not appended after render).
    cond_idx = body.index("if (_myRole === 'owner')")
    html_assign_idx = body.index("el.innerHTML = html;")
    check(cond_idx < html_assign_idx,
          "the owner check must gate what gets built into html BEFORE it's assigned to the DOM -- "
          "appending it after render would flash the non-owner state first")


def test_team_access_wires_the_real_existing_functions_not_new_ones():
    source = _source()
    m = re.search(r"function renderSecurityPosture\(\) \{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "expected function renderSecurityPosture()"
    body = m.group(1)
    check('id="new-user-name"' in body, "must provide the exact input id addUser() already reads")
    check('id="new-user-pw"' in body, "must provide the exact input id addUser() already reads")
    check('id="user-add-status"' in body, "must provide the exact status element id addUser() already writes to")
    check('id="user-list"' in body, "must provide the exact container id loadUsers() already renders into")
    check('onclick="addUser()"' in body, "must wire the real existing addUser(), not a new function")
    check("loadUsers()" in body, "renderSecurityPosture() must actually call loadUsers() to populate the "
          "list once it renders the container, not just build an empty shell")


def test_user_list_rows_still_use_the_real_reset_and_delete_functions():
    # Confirms loadUsers() (unchanged by this restoration) still wires the
    # real per-user action buttons correctly -- this restoration only needed
    # to give it somewhere to render, not touch its own template logic.
    source = _source()
    m = re.search(r"async function loadUsers\(\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "expected async function loadUsers()"
    body = m.group(1)
    check("onclick=\"resetUserPw('${u.username}')\"" in body,
          "each real (non-owner) row must offer Reset PW")
    check("onclick=\"deleteUser('${u.username}')\"" in body,
          "each real (non-owner) row must offer Remove")
    check("u.role!=='owner'" in body,
          "the owner's own row must never offer Reset PW/Remove on itself (no self-lockout path)")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("TEAM ACCESS RESTORED TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("TEAM ACCESS RESTORED TESTS OK — the Security screen's Team Access section is built "
          "only for the owner role, wires the real pre-existing addUser()/loadUsers()/"
          "resetUserPw()/deleteUser() functions to their exact expected element ids, and "
          "per-user rows still correctly exclude the owner's own row from self-management.")


if __name__ == "__main__":
    run()
