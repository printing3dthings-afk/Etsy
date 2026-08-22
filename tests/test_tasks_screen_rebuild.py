"""
Test for the 2026-08-16 Tasks screen rebuild (frontend rendering side).
Scott's feedback: "the question task doesn't seem to do anything," "I need
simpler action for completing the task," "give it more ability." Backend
changes (auto-complete on answer + real headless follow-through, the
frank_can_do background queue) are tested in test_todo_question_
autocomplete.py / test_headless_agent_task.py / test_frank_can_do_loop.py --
this file checks the frontend actually surfaces all of it: each category
gets the primary action that matches what it needs, instead of one generic
checkbox for all four.

Run: python tests/test_tasks_screen_rebuild.py
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


def _render_tasks_body() -> str:
    source = _source()
    m = re.search(r"function _renderTasks\(d, list, offlineNote\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "expected function _renderTasks(d, list, offlineNote)"
    return m.group(1)


def test_answered_question_renders_resolved_state_not_a_bare_open_task():
    body = _render_tasks_body()
    check("isQuestion && answered" in body,
          "must distinguish an answered question from an unanswered one -- this is the exact "
          "state that used to render identically to an unanswered task and read as 'did nothing'")
    check("followUp" in body, "the answered-question branch must surface Frank's real follow_up note")
    check("is following up" in body,
          "before the follow-up note arrives, the UI must say so explicitly -- silence here is "
          "exactly the 'doesn't seem to do anything' symptom Scott reported")


def test_frank_can_do_open_todos_get_a_real_action_not_just_a_checkbox():
    body = _render_tasks_body()
    check("isFrankCanDo" in body, "frank_can_do must be its own render branch, not folded into the generic case")
    check("runFrankCanDoNow(" in body,
          "an open frank_can_do todo must offer a real 'send to Frank now' action -- previously "
          "this category behaved identically to 'general', a label with nothing behind it")
    check("checks this queue" in body,
          "must also communicate the background-queue behavior (Scott's second requirement) so "
          "the manual button doesn't read as the ONLY way it gets done")


def test_needs_attention_escalation_is_visible():
    body = _render_tasks_body()
    check("needsAttention" in body, "the frontend must read the needs_attention flag from the API")
    check("Couldn" in body and "input" in body,
          "a stuck frank_can_do todo (hit the retry cap) must show a distinct, visible escalation "
          "state -- Scott's 'make sure it gets done' ask means a genuinely-stuck task has to "
          "surface to him, not vanish into silent retries")


def test_attempt_count_is_shown_for_transparency():
    body = _render_tasks_body()
    check("attempted" in body and "attempts" in body,
          "attempt_count should be visible ('attempted Nx') so Scott can tell a fresh item from "
          "one Frank has already tried and failed on, without needing to guess")


def test_run_frank_can_do_now_function_exists_and_hits_the_right_endpoint():
    source = _source()
    m = re.search(r"async function runFrankCanDoNow\(id, ?btn\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "expected async function runFrankCanDoNow(id, btn)"
    body = m.group(1)
    check("/api/todos/'+id+'/run-now" in body, "must call the real POST /api/todos/{id}/run-now endpoint")
    check("method:'POST'" in body or 'method: "POST"' in body or "method: 'POST'" in body,
          "must POST, not GET, since this triggers a real action")
    check("90000" in body,
          "a real headless agent call can genuinely take a while (possibly several tool "
          "round-trips) -- must use a generous timeout, not the usual 15-20s CRUD default")
    check("btn.disabled = true" in body, "the button must disable itself while running so a "
          "double-click can't fire two attempts at once")


def test_general_and_scott_only_categories_are_unaffected():
    # Regression guard: this rebuild should only change Question and Frank Can
    # Do's rendering -- General/Only You must keep behaving exactly as before
    # (plain checkbox, no new primary-action branch).
    body = _render_tasks_body()
    m = re.search(r"if \(isQuestion && answered\) \{(.*?)\} else \{\s*primaryAction = '';\s*\}", body, re.DOTALL)
    assert m, "expected an if/else if/else chain ending in a plain empty-string fallback for "
    "everything that isn't Question or Frank Can Do"


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("TASKS SCREEN REBUILD TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("TASKS SCREEN REBUILD TESTS OK — answered questions render a real resolved state with "
          "Frank's follow-up, frank_can_do todos get a real 'send to Frank now' action plus a "
          "visible retry-cap escalation state, attempt counts are shown for transparency, and "
          "General/Only You are unaffected.")


if __name__ == "__main__":
    run()
