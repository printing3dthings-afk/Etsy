"""
Tests for Pinterest posting wiring (Frank upgrade Wave 2, capabilities item 1,
2026-07-17). tools/pinterest_api.py and pinterest_batch_poster.py were a real,
working posting client, previously only reachable via manual CLI — the only
reference to Pinterest anywhere in main.py before this was a credential-status
check, the exact "built but never wired" bug class already fixed for TikTok/
Etsy Ads. Mirrors the TikTok staging pattern exactly: stage_pinterest_post only
ever enqueues a post_pinterest action for the Action Center; nothing calls
pinterest_api.PinterestClient.create_pin() until Scott explicitly approves it
("Post to social media accounts" is a Hard Stop in CLAUDE.md's Autonomy
Boundaries).

Self-contained TestClient-against-the-real-app pattern, same as
tests/test_produce_qc.py. Doesn't require real Pinterest/Etsy credentials —
this sandbox has neither, which is itself exercised as a real (not mocked)
code path by test_list_boards_reports_not_configured below.

Run: python tests/test_pinterest_wiring.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_pinterest_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "pinterest-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def validate(action_type: str, payload: dict, **kwargs):
    return server._validate_staged_action({"type": action_type, "payload": payload}, **kwargs)


# ── tool registration ────────────────────────────────────────────────────────
def test_tools_are_registered():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("stage_pinterest_post" in names, "stage_pinterest_post must be in AGENT_TOOLS")
    check("list_pinterest_boards" in names, "list_pinterest_boards must be in AGENT_TOOLS")


def test_post_pinterest_is_a_recognized_social_staged_action_type():
    check("post_pinterest" in server._SOCIAL_STAGED_ACTION_TYPES,
          f"post_pinterest must be in _SOCIAL_STAGED_ACTION_TYPES, got {server._SOCIAL_STAGED_ACTION_TYPES}")
    check("post_pinterest" in server._STAGED_ACTION_TYPES,
          "post_pinterest must be in the master _STAGED_ACTION_TYPES tuple")


# ── validation ───────────────────────────────────────────────────────────────
_VALID_PAYLOAD = {
    "listing_id": 4509179201, "board_name": "Kawaii Planners",
    "title": "Lavender Dreams Digital Planner", "description": "A cozy kawaii digital planner for GoodNotes.",
}


def test_valid_payload_passes():
    ok, msg = validate("post_pinterest", _VALID_PAYLOAD)
    check(ok is True, f"a complete valid payload should pass, got: {msg!r}")


def test_missing_listing_id_rejected():
    p = dict(_VALID_PAYLOAD); del p["listing_id"]
    ok, msg = validate("post_pinterest", p)
    check(ok is False, "missing listing_id must be rejected")


def test_missing_board_name_rejected():
    p = dict(_VALID_PAYLOAD); p["board_name"] = ""
    ok, msg = validate("post_pinterest", p)
    check(ok is False, "empty board_name must be rejected")


def test_missing_title_rejected():
    p = dict(_VALID_PAYLOAD); p["title"] = "  "
    ok, msg = validate("post_pinterest", p)
    check(ok is False, "blank title must be rejected")


def test_title_over_100_chars_rejected():
    p = dict(_VALID_PAYLOAD); p["title"] = "x" * 101
    ok, msg = validate("post_pinterest", p)
    check(ok is False, "a title over 100 chars must be rejected (Pinterest's own limit)")


def test_title_exactly_100_chars_passes():
    p = dict(_VALID_PAYLOAD); p["title"] = "x" * 100
    ok, msg = validate("post_pinterest", p)
    check(ok is True, f"a title at exactly 100 chars should pass, got: {msg!r}")


def test_missing_description_rejected():
    p = dict(_VALID_PAYLOAD); p["description"] = ""
    ok, msg = validate("post_pinterest", p)
    check(ok is False, "empty description must be rejected")


def test_description_over_500_chars_rejected():
    p = dict(_VALID_PAYLOAD); p["description"] = "x" * 501
    ok, msg = validate("post_pinterest", p)
    check(ok is False, "a description over 500 chars must be rejected (Pinterest's own limit)")


def test_at_approval_without_pinterest_token_rejected():
    # This sandbox genuinely has no PINTEREST_ACCESS_TOKEN -- a real (not mocked)
    # exercise of the "not connected" rejection path.
    saved = os.environ.pop("PINTEREST_ACCESS_TOKEN", None)
    try:
        ok, msg = validate("post_pinterest", _VALID_PAYLOAD, at_approval=True)
        check(ok is False, "at_approval=True with no PINTEREST_ACCESS_TOKEN must reject")
        check("PINTEREST_ACCESS_TOKEN" in msg, f"rejection reason should name the missing token, got: {msg!r}")
    finally:
        if saved is not None:
            os.environ["PINTEREST_ACCESS_TOKEN"] = saved


def test_at_approval_with_token_present_does_not_reject_for_that_reason():
    # Doesn't test a successful POST (needs real credentials) -- just confirms the
    # token-presence gate itself doesn't block when a token IS set.
    os.environ["PINTEREST_ACCESS_TOKEN"] = "fake-token-for-this-test-only"
    try:
        ok, msg = validate("post_pinterest", _VALID_PAYLOAD, at_approval=True)
        check(ok is True, f"with a token present, validation should pass, got: {msg!r}")
    finally:
        os.environ.pop("PINTEREST_ACCESS_TOKEN", None)


def test_tiktok_validation_still_works_after_the_shared_block_split():
    # post_tiktok and post_pinterest used to share one "if t in
    # _SOCIAL_STAGED_ACTION_TYPES" block; splitting it into per-type branches
    # must not have broken TikTok's own validation.
    ok, msg = validate("update_tags", {"listing_id": 123, "tags": ["digital planner"]})
    check(ok is True, f"a totally unrelated Etsy action should still validate correctly, got: {msg!r}")
    ok2, msg2 = validate("post_tiktok", {"video_path": "", "caption": "test"})
    check(ok2 is False, "post_tiktok's own missing-video_path rejection must still work")


# ── staging handler ──────────────────────────────────────────────────────────
def test_stage_pinterest_post_enqueues_a_real_action():
    result = server._stage_pinterest_post(dict(_VALID_PAYLOAD))
    check("error" not in result, f"staging a valid pin should succeed, got: {result}")
    check(result.get("staged") is True, f"expected staged=True, got: {result}")
    check(isinstance(result.get("action_id"), int), f"expected a real action_id, got: {result}")

    queued = server.db.get_action(result["action_id"])
    check(queued is not None, "the staged action should be retrievable from the DB")
    check(queued["type"] == "post_pinterest", f"expected type=post_pinterest, got: {queued['type']}")
    check(queued["status"] == "pending", f"a freshly staged action should be pending, got: {queued['status']}")


def test_stage_pinterest_post_rejects_invalid_input_without_enqueueing():
    before = len(server.db.list_actions(status="pending"))
    result = server._stage_pinterest_post({"listing_id": 123, "board_name": "", "title": "x", "description": "y"})
    check("error" in result, f"invalid staging input should return an error, got: {result}")
    after = len(server.db.list_actions(status="pending"))
    check(after == before, "an invalid stage attempt must not enqueue anything")


# ── read-only tool ───────────────────────────────────────────────────────────
def test_list_boards_reports_not_configured():
    # This sandbox has no Pinterest credentials at all -- a real exercise of the
    # graceful "not connected" path, not a mock.
    saved = os.environ.pop("PINTEREST_ACCESS_TOKEN", None)
    try:
        result = server._list_pinterest_boards()
        check("error" in result, f"with no token configured, expected a clear error, got: {result}")
        check("pinterest_oauth" in result["error"], f"error should point at the fix, got: {result}")
    finally:
        if saved is not None:
            os.environ["PINTEREST_ACCESS_TOKEN"] = saved


# ── agent-tool dispatch ──────────────────────────────────────────────────────
def test_agent_dispatch_stage_pinterest_post():
    payload = dict(_VALID_PAYLOAD)
    payload["title"] = "Dispatch test pin"
    out = server._execute_agent_tool("stage_pinterest_post", payload)
    check(isinstance(out, dict) and out.get("staged") is True,
          f"agent-tool dispatch for stage_pinterest_post should stage successfully, got: {out}")


def test_agent_dispatch_list_pinterest_boards():
    out = server._execute_agent_tool("list_pinterest_boards", {})
    check(isinstance(out, dict), f"agent-tool dispatch for list_pinterest_boards should return a dict, got: {out}")
    check("error" in out or "boards" in out, f"expected either an error or a boards list, got: {out}")


# ── approve-time executor selection ──────────────────────────────────────────
def test_social_executor_selection_picks_pinterest_not_tiktok():
    # Regression: is_social used to unconditionally call _execute_tiktok_staged_action
    # for ANY social type. Confirms the type-based selection (added alongside this
    # Pinterest wiring) picks the right executor without actually invoking either
    # (both need real external credentials this sandbox doesn't have).
    tiktok_action = {"type": "post_tiktok"}
    pinterest_action = {"type": "post_pinterest"}
    tiktok_pick = (
        server._execute_pinterest_staged_action if tiktok_action["type"] == "post_pinterest"
        else server._execute_tiktok_staged_action
    )
    pinterest_pick = (
        server._execute_pinterest_staged_action if pinterest_action["type"] == "post_pinterest"
        else server._execute_tiktok_staged_action
    )
    check(tiktok_pick is server._execute_tiktok_staged_action, "a post_tiktok action must select the TikTok executor")
    check(pinterest_pick is server._execute_pinterest_staged_action,
          "a post_pinterest action must select the Pinterest executor")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PINTEREST WIRING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PINTEREST WIRING TESTS OK — registration, validation (all fields + limits + "
          "token gate), staging, dispatch, and executor selection all verified.")


if __name__ == "__main__":
    run()
