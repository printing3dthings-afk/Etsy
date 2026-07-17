"""
Tests for Wave 2 capabilities item 3 (2026-07-17): order_notifier.py /
etsy_autoresponder.py made agent-callable, plus a real bug found and fixed
while wiring them in.

Findings this covers:
  1. order_notifier.py read .env with no existence guard -- the exact crash
     class already fixed once in etsy_autoresponder.py for the same reason
     (Railway injects env vars directly, no .env file ships there). Verified
     by literally hiding .env and running the script as a subprocess.
  2. execute_command's chat-tool dispatch never checked requires_approval --
     unlike /api/workflows/{id}/run, which does. A requires_approval command
     (e.g. backup_digital_products) called from chat would have run
     immediately, bypassing the Action Center approval every other mutation
     in this codebase goes through. Fixed to stage via run_script instead.
  3. check_new_orders / send_order_notifications (order_notifier.py, a real
     working endpoint -- shops/{id}/receipts) and check_buyer_messages
     (etsy_autoresponder.py, whose conversations endpoint Etsy's public API
     does not expose to third-party apps -- ops_runbook.md 2026-06-19)
     registered in _EXEC_COMMANDS, agent-callable via the existing
     execute_command tool.

Run: python tests/test_order_notifier_wiring.py
"""
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_order_notifier_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "order-notifier-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── _EXEC_COMMANDS registration ─────────────────────────────────────────────
def test_new_commands_registered():
    for name in ("check_new_orders", "send_order_notifications", "check_buyer_messages"):
        check(name in server._EXEC_COMMANDS, f"{name} must be registered in _EXEC_COMMANDS")


def test_check_new_orders_uses_dry_flag_and_no_approval():
    cfg = server._EXEC_COMMANDS["check_new_orders"]
    check(cfg["script"] == "tools/order_notifier.py", f"wrong script: {cfg['script']}")
    check(cfg.get("args") == ["--dry"], f"check_new_orders must pass --dry (read-only), got {cfg.get('args')}")
    check(not cfg.get("requires_approval"), "check_new_orders is read-only, must not require approval")


def test_send_order_notifications_no_args_no_approval():
    cfg = server._EXEC_COMMANDS["send_order_notifications"]
    check(cfg["script"] == "tools/order_notifier.py", f"wrong script: {cfg['script']}")
    check(not cfg.get("args"), f"send_order_notifications should run the real (non-dry) path, got args={cfg.get('args')}")
    check(not cfg.get("requires_approval"),
          "send_order_notifications only emails the shop owner (never a buyer) -- matches its existing "
          "unattended weekly run, so it must not require approval")


def test_check_buyer_messages_registered_honestly():
    cfg = server._EXEC_COMMANDS["check_buyer_messages"]
    check(cfg["script"] == "tools/etsy_autoresponder.py", f"wrong script: {cfg['script']}")
    check("--send" not in (cfg.get("args") or []),
          "check_buyer_messages must never pass --send/--send-all -- that endpoint doesn't exist on Etsy's side")
    desc = cfg["description"].lower()
    check("limitation" in desc or "does not" in desc.lower() or "no buyer-messaging" in desc.lower(),
          f"the description must be honest about the known API gap, got: {cfg['description']!r}")


def test_no_send_command_is_registered_anywhere():
    # A --send/--send-all path is a real, unstaged buyer-facing mutation on an
    # endpoint that (per ops_runbook.md 2026-06-19) doesn't even exist for
    # third-party apps -- confirms nothing wires it in, intentionally.
    for name, cfg in server._EXEC_COMMANDS.items():
        args = cfg.get("args") or []
        check("--send" not in args and "--send-all" not in args,
              f"{name} must not wire etsy_autoresponder's --send/--send-all path, got args={args}")


# ── execute_command requires_approval bug fix ───────────────────────────────
def test_execute_command_stages_a_requires_approval_command():
    # backup_digital_products is a real, pre-existing requires_approval=True
    # entry -- confirms the chat tool now stages it instead of running it
    # immediately (the bug: this branch used to call _run_exec_command()
    # unconditionally regardless of requires_approval).
    check(server._EXEC_COMMANDS["backup_digital_products"].get("requires_approval") is True,
          "sanity check: backup_digital_products must still be requires_approval=True")
    before = len(server.db.list_actions(status="pending"))
    out = server._execute_agent_tool("execute_command", {"command": "backup_digital_products"})
    check(out.get("staged") is True, f"a requires_approval command must stage, not run, got: {out}")
    check(isinstance(out.get("action_id"), int), f"expected a real action_id, got: {out}")
    after = len(server.db.list_actions(status="pending"))
    check(after == before + 1, f"expected exactly one new pending action, before={before} after={after}")
    queued = server.db.get_action(out["action_id"])
    check(queued["type"] == "run_script", f"expected type=run_script, got: {queued['type']}")
    check(queued["payload"]["command"] == "backup_digital_products",
          f"expected the staged payload to carry the command name, got: {queued['payload']}")


def test_execute_command_still_runs_non_approval_commands_directly():
    # Regression: the fix must not accidentally start requiring approval for
    # every command -- only ones explicitly marked requires_approval=True.
    check(not server._EXEC_COMMANDS["check_new_orders"].get("requires_approval"),
          "sanity check: check_new_orders must not require approval")
    out = server._execute_agent_tool("check_new_orders", {})
    # check_new_orders isn't a registered tool NAME (it's an _EXEC_COMMANDS
    # entry reached via execute_command) -- dispatching it directly by that
    # name should fall through main.py's tool router without staging
    # anything, proving the fix is scoped to the requires_approval branch only.
    check("staged" not in out or out.get("staged") is not True,
          f"a bare unregistered tool name must not accidentally stage anything, got: {out}")


def test_execute_command_direct_dispatch_for_non_approval_still_runs():
    out = server._execute_agent_tool("execute_command", {"command": "check_new_orders"})
    check("staged" not in out, f"a non-approval command must run directly, not stage, got keys: {list(out.keys())}")
    check("returncode" in out, f"expected direct execution output, got: {out}")


# ── order_notifier.py .env guard (real production bug) ─────────────────────
def test_order_notifier_survives_a_missing_env_file():
    env_path = ROOT / ".env"
    had_env = env_path.exists()
    backup = env_path.read_bytes() if had_env else None
    try:
        if had_env:
            env_path.unlink()
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "order_notifier.py"), "--dry"],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT),
        )
        combined = (result.stdout or "") + (result.stderr or "")
        check("FileNotFoundError" not in combined,
              f"order_notifier.py must not crash on a missing .env file (Railway has none), got:\n{combined[:500]}")
        check(".env" not in combined or "No such file" not in combined,
              f"no missing-.env traceback expected, got:\n{combined[:500]}")
    finally:
        if had_env and backup is not None:
            env_path.write_bytes(backup)
        check(env_path.exists() == had_env, "the real .env file must be restored after this test")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("ORDER NOTIFIER / AUTORESPONDER WIRING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("ORDER NOTIFIER / AUTORESPONDER WIRING TESTS OK — new _EXEC_COMMANDS entries "
          "registered correctly (real dry/live order_notifier paths, honest "
          "check_buyer_messages description, no --send path wired anywhere), the "
          "execute_command requires_approval staging fix verified end-to-end, and "
          "order_notifier.py's real missing-.env crash confirmed fixed via an actual "
          "subprocess run with .env hidden.")


if __name__ == "__main__":
    run()
