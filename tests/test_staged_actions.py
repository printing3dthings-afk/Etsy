#!/usr/bin/env python3
"""
Staged-action approval tests — the gate that decides whether an Etsy mutation,
a local filesystem write, or a script execution is even allowed to be queued
for Scott's one-tap approval in the Action Center.

Why this exists: `main.py:_validate_staged_action` is the single choke point
every staged action passes through — both when it's first staged and again
(at_approval=True) right before it's applied. It enforces the 2026 title/tag
rules, the listing-photo pale-background CARDINAL CHECK, path-traversal
guards for local file actions, and the forbidden-flag denylist for scripts.
It had zero test coverage — a careless refactor here could silently let a
71-character title or a path-traversal write through, and nothing would
catch it before deploy. These tests lock each branch down.

Deliberately dependency-light and mostly network-free: `import main as
server` (same safe import smoke_test.py already relies on — no server start,
no background loops, no API keys needed) and exercises the pure validation
branches with tiny in-memory/tmp fixtures. The one branch that talks to Etsy
(at_approval=True's live-state reconfirmation) is exercised only far enough
to prove a network/lookup failure is turned into a rejection, not a crash.
`EtsyAPIClient()` reads credentials straight from os.environ and does NOT
raise on construction even with none set — the test explicitly clears every
Etsy credential env var for its own duration (see
_ETSY_CRED_KEYS/save-restore below) rather than assuming the ambient
environment has none, which used to cause an intermittent hang whenever this
sandbox happened to have stale-but-present credentials (2026-07-17 fix — see
data/knowledge_base/ops_runbook.md).

Run locally:  python tests/test_staged_actions.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a gate regressed (prints which).
"""
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

# ── tiny test harness (matches tests/test_quality_gates.py style) ──────────────
_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def validate(action_type: str, payload: dict, **kwargs):
    return server._validate_staged_action({"type": action_type, "payload": payload}, **kwargs)


# ── unsupported type ─────────────────────────────────────────────────────────
def test_unsupported_action_type_rejected():
    ok, msg = validate("delete_the_whole_shop", {})
    check(ok is False, "an unknown action type must never validate")
    check("unsupported action type" in msg, f"expected a clear reason, got: {msg!r}")


# ── update_title ─────────────────────────────────────────────────────────────
def test_update_title_missing_listing_id_rejected():
    ok, msg = validate("update_title", {"title": "A fine title"})
    check(ok is False, "update_title without listing_id must be rejected")


def test_update_title_empty_rejected():
    ok, msg = validate("update_title", {"listing_id": 123, "title": "   "})
    check(ok is False, "an empty/whitespace-only title must be rejected")


def test_update_title_over_70_chars_rejected():
    ok, msg = validate("update_title", {"listing_id": 123, "title": "x" * 71})
    check(ok is False, "a 71-char title must be rejected (mobile ranking rule)")
    check("70" in msg, f"rejection message should mention the 70-char limit, got: {msg!r}")


def test_update_title_70_chars_exactly_passes():
    ok, msg = validate("update_title", {"listing_id": 123, "title": "x" * 70})
    check(ok is True, f"a title at exactly 70 chars should pass, got: {msg!r}")


def test_update_title_valid_passes():
    ok, msg = validate("update_title", {"listing_id": 123, "title": "Digital Planner 2026, GoodNotes"})
    check(ok is True, f"a normal valid title should pass, got: {msg!r}")


# ── update_tags ───────────────────────────────────────────────────────────────
def test_update_tags_missing_listing_id_rejected():
    ok, msg = validate("update_tags", {"tags": ["digital planner"]})
    check(ok is False, "update_tags without listing_id must be rejected")


def test_update_tags_not_a_list_rejected():
    ok, msg = validate("update_tags", {"listing_id": 123, "tags": "digital planner"})
    check(ok is False, "tags as a bare string (not a list) must be rejected")


def test_update_tags_empty_list_rejected():
    ok, msg = validate("update_tags", {"listing_id": 123, "tags": []})
    check(ok is False, "an empty tags list must be rejected")


def test_update_tags_over_13_rejected():
    ok, msg = validate("update_tags", {"listing_id": 123, "tags": [f"tag{i}" for i in range(14)]})
    check(ok is False, "14 tags must be rejected — Etsy allows max 13")
    check("13" in msg, f"rejection message should mention the 13-tag limit, got: {msg!r}")


def test_update_tags_13_exactly_passes():
    ok, msg = validate("update_tags", {"listing_id": 123, "tags": [f"tag{i}" for i in range(13)]})
    check(ok is True, f"exactly 13 valid tags should pass, got: {msg!r}")


def test_update_tags_empty_string_tag_rejected():
    ok, msg = validate("update_tags", {"listing_id": 123, "tags": ["digital planner", "   "]})
    check(ok is False, "a blank tag must be rejected")


def test_update_tags_over_20_chars_rejected():
    ok, msg = validate("update_tags", {"listing_id": 123, "tags": ["x" * 21]})
    check(ok is False, "a tag over 20 characters must be rejected")


def test_update_tags_valid_passes():
    ok, msg = validate("update_tags", {"listing_id": 123, "tags": ["digital planner", "goodnotes planner"]})
    check(ok is True, f"a normal valid tag list should pass, got: {msg!r}")


# ── toggle_listing_state ────────────────────────────────────────────────────
def test_toggle_listing_state_invalid_state_rejected():
    ok, msg = validate("toggle_listing_state", {"listing_id": 123, "new_state": "deleted"})
    check(ok is False, "new_state outside {active, inactive} must be rejected")


def test_toggle_listing_state_valid_passes():
    ok, msg = validate("toggle_listing_state", {"listing_id": 123, "new_state": "inactive"})
    check(ok is True, f"new_state='inactive' should pass, got: {msg!r}")


# ── at_approval=True: live-state reconfirmation ─────────────────────────────
# 2026-07-17 fix: this used to just ASSUME no Etsy credentials were configured
# in the test environment, without enforcing it — EtsyAPIClient() reads
# straight from os.environ at construction (see tools/etsy_api.py) and does NOT
# raise on missing credentials; it always makes a real network call either way.
# With no credentials present, Etsy rejects the malformed/empty-auth request
# fast; with stale-but-present credentials (this exact sandbox, confirmed
# 2026-07-17 reliability audit), the retry/backoff/circuit-breaker logic in
# etsy_api.py kicks in and can take much longer to finally fail -- an
# "intermittent hang" that depended entirely on incidental environment state,
# not a real bug in the gate being tested. Fixed by explicitly clearing every
# Etsy credential env var for the duration of this one test (save/restore),
# so the fast-reject path is guaranteed regardless of what's ambiently
# configured -- CI, a dev laptop with a real .env, or this sandbox.
_ETSY_CRED_KEYS = (
    "ETSY_API_KEY", "ETSY_CLIENT_ID", "ETSY_CLIENT_SECRET",
    "ETSY_ACCESS_TOKEN", "ETSY_SHOP_ID", "ETSY_SHOP_ID_NUMERIC",
)


def test_update_title_at_approval_without_credentials_rejected_not_crashed():
    import os
    saved = {k: os.environ.pop(k, None) for k in _ETSY_CRED_KEYS}
    try:
        ok, msg = validate(
            "update_title", {"listing_id": 123, "title": "A fine title"}, at_approval=True,
        )
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
    check(ok is False, "at_approval=True with no reachable Etsy API must reject, not silently pass")
    check(isinstance(msg, str) and msg, "rejection must carry a human-readable reason")


# ── listing_photo ────────────────────────────────────────────────────────────
def _make_image(path: Path, rgb: tuple) -> None:
    from PIL import Image
    img = Image.new("RGB", (2400, 2400), rgb)
    img.save(path)


def test_listing_photo_missing_listing_id_rejected():
    ok, msg = validate("listing_photo", {"rank": 1, "path": "x.jpg"})
    check(ok is False, "listing_photo without listing_id must be rejected")


def test_listing_photo_invalid_rank_rejected():
    ok, msg = validate("listing_photo", {"listing_id": 123, "rank": 11, "path": "x.jpg"})
    check(ok is False, "rank outside 1-10 must be rejected")


def test_listing_photo_bool_rank_rejected():
    # bool is a subclass of int in Python -- rank=True must not sneak through as rank=1.
    ok, msg = validate("listing_photo", {"listing_id": 123, "rank": True, "path": "x.jpg"})
    check(ok is False, "a bool rank must be rejected even though bool is an int subclass")


def test_listing_photo_missing_path_rejected():
    ok, msg = validate("listing_photo", {"listing_id": 123, "rank": 1, "path": ""})
    check(ok is False, "an empty path must be rejected")


def test_listing_photo_path_traversal_rejected():
    ok, msg = validate("listing_photo", {"listing_id": 123, "rank": 1, "path": "../../etc/passwd"})
    check(ok is False, "a path that escapes the staged_photos root must be rejected")


def test_listing_photo_file_not_found_rejected():
    ok, msg = validate("listing_photo", {"listing_id": 123, "rank": 1, "path": "does_not_exist_xyz.jpg"})
    check(ok is False, "a path that doesn't exist on disk must be rejected")


def test_listing_photo_pale_background_rejected():
    root = server._FILE_ROOTS["staged_photos"]
    root.mkdir(parents=True, exist_ok=True)
    fname = "_test_pale_bg.jpg"
    _make_image(root / fname, (250, 250, 248))  # washed-out near-white
    try:
        ok, msg = validate("listing_photo", {"listing_id": 123, "rank": 1, "path": fname})
        check(ok is False, "a pale/washed-out background must be rejected (CARDINAL CHECK)")
        check("pale" in msg, f"rejection message should explain why, got: {msg!r}")
    finally:
        (root / fname).unlink(missing_ok=True)


def test_listing_photo_valid_passes():
    root = server._FILE_ROOTS["staged_photos"]
    root.mkdir(parents=True, exist_ok=True)
    fname = "_test_valid_bg.jpg"
    _make_image(root / fname, (27, 37, 104))  # midnight blue -- not pale
    try:
        ok, msg = validate("listing_photo", {"listing_id": 123, "rank": 1, "path": fname})
        check(ok is True, f"a non-pale, in-bounds, existing photo should pass, got: {msg!r}")
    finally:
        (root / fname).unlink(missing_ok=True)


# ── listing_video ────────────────────────────────────────────────────────────
def test_listing_video_missing_listing_id_rejected():
    ok, msg = validate("listing_video", {"path": "x.mp4"})
    check(ok is False, "listing_video without listing_id must be rejected")


def test_listing_video_invalid_rank_rejected():
    ok, msg = validate("listing_video", {"listing_id": 123, "rank": 0, "path": "x.mp4"})
    check(ok is False, "rank=0 must be rejected (must be 1-10 when provided)")


def test_listing_video_rank_omitted_is_allowed():
    root = server._FILE_ROOTS["staged_videos"]
    root.mkdir(parents=True, exist_ok=True)
    fname = "_test_video.mp4"
    (root / fname).write_bytes(b"not a real video, just needs to exist")
    try:
        ok, msg = validate("listing_video", {"listing_id": 123, "path": fname})
        check(ok is True, f"listing_video with rank omitted should pass, got: {msg!r}")
    finally:
        (root / fname).unlink(missing_ok=True)


def test_listing_video_path_traversal_rejected():
    ok, msg = validate("listing_video", {"listing_id": 123, "path": "../../etc/passwd"})
    check(ok is False, "a path that escapes the staged_videos root must be rejected")


def test_listing_video_file_not_found_rejected():
    ok, msg = validate("listing_video", {"listing_id": 123, "path": "does_not_exist_xyz.mp4"})
    check(ok is False, "a video path that doesn't exist on disk must be rejected")


# ── local_write_file / local_delete (path-allowlist gated) ─────────────────
def test_local_write_file_missing_path_rejected():
    ok, msg = validate("local_write_file", {"after": "content"})
    check(ok is False, "local_write_file without a path must be rejected")


def test_local_write_file_path_not_allowed_rejected():
    original = server.db.is_path_allowed
    server.db.is_path_allowed = lambda path: False
    try:
        ok, msg = validate("local_write_file", {"path": "/not/an/allowed/folder/file.txt", "after": "x"})
        check(ok is False, "a path outside every Allowed Folder must be rejected")
    finally:
        server.db.is_path_allowed = original


def test_local_write_file_missing_content_rejected():
    original = server.db.is_path_allowed
    server.db.is_path_allowed = lambda path: True
    try:
        ok, msg = validate("local_write_file", {"path": "/data/workspace/file.txt"})
        check(ok is False, "local_write_file with no 'after' content must be rejected")
    finally:
        server.db.is_path_allowed = original


def test_local_write_file_valid_passes():
    original = server.db.is_path_allowed
    server.db.is_path_allowed = lambda path: True
    try:
        ok, msg = validate("local_write_file", {"path": "/data/workspace/file.txt", "after": "hello"})
        check(ok is True, f"a valid, allowed local_write_file should pass, got: {msg!r}")
    finally:
        server.db.is_path_allowed = original


def test_local_delete_path_not_allowed_rejected():
    original = server.db.is_path_allowed
    server.db.is_path_allowed = lambda path: False
    try:
        ok, msg = validate("local_delete", {"path": "/etc/passwd"})
        check(ok is False, "local_delete outside every Allowed Folder must be rejected")
    finally:
        server.db.is_path_allowed = original


# ── local_exec ────────────────────────────────────────────────────────────────
def test_local_exec_unknown_command_rejected():
    ok, msg = validate("local_exec", {"command": "rm_everything_xyz"})
    check(ok is False, "an unregistered local command must be rejected")


def test_local_exec_forbidden_flag_rejected():
    real_command = next(iter(server._LOCAL_EXEC_COMMANDS))
    ok, msg = validate("local_exec", {"command": real_command, "extra_args": "--delete /tmp"})
    check(ok is False, "a forbidden flag in extra_args must be rejected")


def test_local_exec_valid_passes():
    real_command = next(iter(server._LOCAL_EXEC_COMMANDS))
    ok, msg = validate("local_exec", {"command": real_command, "extra_args": ""})
    check(ok is True, f"a registered command with no forbidden flags should pass, got: {msg!r}")


# ── run_script ────────────────────────────────────────────────────────────────
def test_run_script_unknown_command_rejected():
    ok, msg = validate("run_script", {"command": "not_a_real_script_xyz"})
    check(ok is False, "an unregistered script command must be rejected")


def test_run_script_without_requires_approval_rejected():
    # A command that does NOT require approval should never be stageable --
    # it's meant to run directly from Workflows, not queue in the Action Center.
    no_approval_cmd = next(
        (k for k, v in server._EXEC_COMMANDS.items() if not v.get("requires_approval")), None
    )
    check(no_approval_cmd is not None, "test fixture assumption failed: expected at least one "
          "_EXEC_COMMANDS entry without requires_approval")
    if no_approval_cmd:
        ok, msg = validate("run_script", {"command": no_approval_cmd})
        check(ok is False, f"'{no_approval_cmd}' has no requires_approval flag and must be rejected as staged")


def test_run_script_requiring_approval_valid_passes():
    approval_cmd = next(
        (k for k, v in server._EXEC_COMMANDS.items() if v.get("requires_approval")), None
    )
    check(approval_cmd is not None, "test fixture assumption failed: expected at least one "
          "_EXEC_COMMANDS entry with requires_approval=True (e.g. backup_digital_products)")
    if approval_cmd:
        ok, msg = validate("run_script", {"command": approval_cmd, "extra_args": ""})
        check(ok is True, f"'{approval_cmd}' (requires_approval=True) should pass, got: {msg!r}")


def test_run_script_forbidden_flag_rejected():
    approval_cmd = next(
        (k for k, v in server._EXEC_COMMANDS.items() if v.get("requires_approval")), None
    )
    if approval_cmd:
        ok, msg = validate("run_script", {"command": approval_cmd, "extra_args": "--activate"})
        check(ok is False, "a forbidden flag on a staged script command must be rejected")


# ── register_command ─────────────────────────────────────────────────────────
def test_register_command_missing_name_rejected():
    ok, msg = validate("register_command", {"script_path": "tools/api_server/resilience.py", "timeout": 30})
    check(ok is False, "register_command without command_name must be rejected")


def test_register_command_already_registered_rejected():
    existing = next(iter(server._EXEC_COMMANDS))
    ok, msg = validate(
        "register_command",
        {"command_name": existing, "script_path": "tools/api_server/resilience.py", "timeout": 30},
    )
    check(ok is False, f"re-registering the existing command '{existing}' must be rejected")


def test_register_command_missing_script_path_rejected():
    ok, msg = validate("register_command", {"command_name": "brand_new_cmd_xyz", "timeout": 30})
    check(ok is False, "register_command without script_path must be rejected")


def test_register_command_path_traversal_rejected():
    ok, msg = validate(
        "register_command",
        {"command_name": "brand_new_cmd_xyz", "script_path": "../../etc/passwd", "timeout": 30},
    )
    check(ok is False, "a script_path containing '..' must be rejected")


def test_register_command_outside_tools_rejected():
    ok, msg = validate(
        "register_command",
        {"command_name": "brand_new_cmd_xyz", "script_path": "SETUP.bat", "timeout": 30},
    )
    check(ok is False, "a script_path that doesn't resolve under tools/ must be rejected")


def test_register_command_nonexistent_script_rejected():
    ok, msg = validate(
        "register_command",
        {"command_name": "brand_new_cmd_xyz", "script_path": "tools/this_file_does_not_exist_xyz.py",
         "timeout": 30},
    )
    check(ok is False, "a script_path that doesn't exist on disk must be rejected")


def test_register_command_invalid_timeout_rejected():
    ok, msg = validate(
        "register_command",
        {"command_name": "brand_new_cmd_xyz", "script_path": "tools/api_server/resilience.py", "timeout": 0},
    )
    check(ok is False, "timeout must be a positive integer")


def test_register_command_bool_timeout_rejected():
    ok, msg = validate(
        "register_command",
        {"command_name": "brand_new_cmd_xyz", "script_path": "tools/api_server/resilience.py", "timeout": True},
    )
    check(ok is False, "a bool timeout must be rejected even though bool is an int subclass")


def test_register_command_valid_passes():
    ok, msg = validate(
        "register_command",
        {"command_name": "brand_new_cmd_xyz", "script_path": "tools/api_server/resilience.py", "timeout": 30},
    )
    check(ok is True, f"a well-formed new command registration should pass, got: {msg!r}")


# ── runner ────────────────────────────────────────────────────────────────────
def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ran = 0
    for t in tests:
        try:
            t()
            ran += 1
        except Exception:
            _failures.append(f"{t.__name__} raised an unexpected error:\n" + traceback.format_exc())
    if _failures:
        print("STAGED-ACTION TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"STAGED-ACTION TESTS OK — {ran} tests passed (_validate_staged_action across all action types).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
