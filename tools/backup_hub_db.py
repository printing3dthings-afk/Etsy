"""
Exports the non-secret state of the live hub.db (todos, action history, activity
log, settings, user list, relay heartbeat) to a single git-committed JSON file, so a
Railway redeploy wiping the ephemeral database (confirmed: /health reports
persistent=false until a Volume is attached, see ops_runbook.md 2026-07-03) has a real
recovery path instead of total data loss.

IMPORTANT — this only helps if the output file actually gets committed and pushed.
Writing it to disk inside the running container does NOT survive a redeploy any more
than hub.db itself does; the container's whole filesystem resets together. Run this,
then commit + push data/hub_db_backups/hub_db_state.json (or hand it to Scott to do
so), the same way tools/backup_digital_products.py's ZIP gets handed to Scott for his
own cloud storage. The real fix is the Railway Volume (correction-plan todo, Scott);
this script is the interim safety net until that's attached.

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

OUT_DIR = ROOT / "data" / "hub_db_backups"
OUT_PATH = OUT_DIR / "hub_db_state.json"

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
    print("Remember: this file must be committed + pushed to actually survive a redeploy.")
    return OUT_PATH


if __name__ == "__main__":
    main()
