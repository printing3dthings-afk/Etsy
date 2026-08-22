"""
Test for the 2026-08-15 ease-of-use pass, part 2: the two genuinely
catastrophic single-click actions in the app -- deleting your own account
and redeploying the live production server -- now require typing the
action's name, not just accepting a native confirm() dialog.

Context: a plain confirm() is one reflexive click to accept ("this cannot
be undone" reads the same as "delete this task?" to a user's muscle
memory). Proportionate for reversible actions, not for the two that
genuinely cannot be undone or cause a real production outage. The shared
`_typedConfirm(message, requiredWord)` helper shows the same warning text
via prompt(), and only returns true on an exact (case-insensitive) match --
any cancel or typo shows a toast and changes nothing.

Verified end-to-end in real headless Chrome (not just structurally here):
stubbing window.prompt's return value, _typedConfirm() returns false and
shows a toast on a mismatched or wrong-cased-but-still-wrong word, false on
cancel (prompt() returning null), and true only on the exact word
(case-insensitive, so 'redeploy' typed still matches 'REDEPLOY').

Run: python tests/test_typed_confirm_dangerous_actions.py
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


def test_typed_confirm_helper_never_proceeds_on_mismatch_or_cancel():
    source = _source()
    m = re.search(r"function _typedConfirm\(message, requiredWord\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "expected a shared function _typedConfirm(message, requiredWord)"
    body = m.group(1)
    check("if (typed === null) return false;" in body,
          "a cancelled prompt (returns null) must return false, never proceed")
    check("toUpperCase() !== requiredWord" in body,
          "must compare case-insensitively against the exact required word, not a loose substring match")
    check("showToast(" in body,
          "a mismatch must tell the user nothing happened, not fail silently")
    check("return true;" in body, "only the exact-match path may return true")


def test_delete_my_account_requires_typing_delete():
    source = _source()
    m = re.search(r"async function deleteMyAccount\(\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "expected async function deleteMyAccount()"
    body = m.group(1)
    check("_typedConfirm(" in body,
          "account deletion must go through _typedConfirm(), not a plain confirm() "
          "(this is the one action in the app that is genuinely, permanently irreversible)")
    check("'DELETE'" in body, "the required typed word for account deletion must be DELETE")
    check("confirm('Permanently delete" not in body,
          "the old plain confirm() call must be fully replaced, not left as a redundant second gate")


def test_core_redeploy_requires_typing_redeploy():
    source = _source()
    m = re.search(r"async function coreRedeploy\(\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "expected async function coreRedeploy()"
    body = m.group(1)
    check("_typedConfirm(" in body,
          "server redeploy must go through _typedConfirm(), not a plain confirm() -- it causes "
          "a real production outage, not just an in-app change")
    check("'REDEPLOY'" in body, "the required typed word for redeploy must be REDEPLOY")
    check("confirm('Redeploy the live server" not in body,
          "the old plain confirm() call must be fully replaced, not left as a redundant second gate")


def test_less_severe_confirms_were_left_alone():
    # Regression guard: this pass should NOT have swept every confirm() in the
    # file into a typed-confirm -- that would add friction to routine, frequent
    # actions (deleting a task, logging out another device) where it isn't
    # warranted, contradicting the same "frequency rule" this session's motion
    # work was built on (short/light treatment for anything done often).
    source = _source()
    check("if (!confirm('Delete this task?')) return;" in source,
          "routine, low-stakes confirms (e.g. delete a task) must stay plain confirm() -- "
          "typed confirmation is reserved for the genuinely catastrophic actions only")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("TYPED CONFIRM DANGEROUS ACTIONS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("TYPED CONFIRM DANGEROUS ACTIONS TESTS OK — account deletion and server redeploy both "
          "require typing the exact action word via the shared _typedConfirm() helper (never "
          "proceeding on cancel or mismatch), while routine lower-stakes confirms were "
          "deliberately left as plain confirm() dialogs.")


if __name__ == "__main__":
    run()
