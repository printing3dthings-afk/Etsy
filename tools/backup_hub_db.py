"""
Exports the non-secret state of the live hub.db (todos, action history, activity
log, settings, user list, relay heartbeat) to a JSON snapshot — a defense-in-depth
copy distinct from hub.db itself, protecting against volume-level accidents
(corruption, accidental deletion, a bad migration) rather than the original
"no Volume attached" scenario this script was built for.

Durability (2026-07-17, updated): a persistent Railway Volume was attached
2026-07-09 (confirmed live: /health reports persistent:true, files_volume:true),
so hub.db itself is no longer wiped on redeploy — the original catastrophic-loss
scenario this script guarded against is closed. OUT_PATH now resolves via
db.resolve_persistent_path(), the same /data-detection every other durable-state
file in this codebase uses (ops_runbook.md, ceo_learnings.md,
registered_commands.json) — when a volume is mounted, the snapshot lands there
directly and survives redeploys on its own, no git commit/push required. Falls
back to the repo-relative path (git-committed, as before) when no volume is
present, e.g. a local sandbox run. Added to _WEEKLY_MONITOR_SCRIPTS in main.py so
this actually runs automatically now instead of depending on someone remembering
an approval-gated command (the reliability audit found the JSON snapshot had
gone a week stale — see ops_runbook.md 2026-07-17).

Manual runs still work exactly as before:
  python tools/backup_hub_db.py
If you want an off-Railway copy too (e.g. before a risky migration), commit +
push the output file same as always — just no longer required for it to survive
an ordinary redeploy.

What's excluded, and why:
  - etsy_tokens (access/refresh tokens) — the exact category of secret already
    leaked once via a git-committed file (see CLAUDE.md's Etsy OAuth Status /
    security review history). Never again.
  - hub_sessions (session ids) — short-lived and meaningless to resurrect.
  - pw_hash / recovery_code_hash — list_hub_users() already excludes these at the
    SQL level; a restored user keeps their username/role but must use "Forgot
    password?" to regain access. Slightly less convenient than restoring the hash
    (which is one-way and arguably safe to store), but keeps this file free of
    anything that looks like a credential, which is the more defensible default
    for a script whose whole job is producing a file meant to be committed.
  - any settings key containing token/secret/key/password (case-insensitive) —
    defense in depth; no such key is expected to exist in the settings table today,
    but the filter costs nothing and closes the door if one ever does.

Run:  python tools/backup_hub_db.py
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "api_server"))
import db  # noqa: E402

_REPO_OUT_PATH = ROOT / "data" / "hub_db_backups" / "hub_db_state.json"
OUT_PATH = db.resolve_persistent_path(
    "hub_db_backups/hub_db_state.json", fallback=_REPO_OUT_PATH, seed_from=_REPO_OUT_PATH
)
OUT_DIR = OUT_PATH.parent

_SECRET_KEY_PATTERN = re.compile(r"token|secret|password|api_key|client_id", re.IGNORECASE)


def _safe_settings() -> dict:
    return {k: v for k, v in db.all_settings().items() if not _SECRET_KEY_PATTERN.search(k)}


def export_state() -> dict:
    db.init_db()
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "note": "Non-secret state only. See tools/backup_hub_db.py docstring for what's "
                "excluded and why. Restore is manual (re-insert rows) -- there is no "
                "automated restore script, since a wipe is rare enough that a hand-checked "
                "restore is safer than a blind automated one.",
        "todos": db.list_todos(include_done=True, limit=1000),
        "hub_users": db.list_hub_users(),
        "settings": _safe_settings(),
        "action_queue": db.list_actions(status=None, limit=500),
        "activity_log": db.list_activity(limit=500),
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    state = export_state()
    with open(OUT_PATH, "w") as f:
        json.dump(state, f, indent=2, default=str)
    counts = {k: len(v) if isinstance(v, list) else "n/a" for k, v in state.items() if k not in ("exported_at", "note")}
    print(f"Exported hub.db state -> {OUT_PATH}")
    print(f"Row counts: {counts}")
    if OUT_PATH != _REPO_OUT_PATH:
        print("On the durable volume — survives a redeploy on its own, no commit/push needed.")
    else:
        print("No volume detected here — remember to commit + push this file if you want it "
              "to survive (e.g. a local sandbox run).")
    return OUT_PATH


if __name__ == "__main__":
    main()
