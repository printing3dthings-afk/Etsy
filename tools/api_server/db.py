#!/usr/bin/env python3
"""
Persistence layer for the OnBrandCraftz hub.

SQLite, intentionally simple: one connection per operation (thread-safe across
FastAPI's to_thread calls), WAL mode for concurrency, upsert-by-day so repeated
writes on the same calendar day update a single row instead of duplicating.

Storage location resolution (in priority order):
  1. $DB_PATH                       — explicit override
  2. /data/hub.db                   — a Railway Volume mounted at /data (persists)
  3. <module>/hub_data/hub.db       — local fallback (ephemeral on Railway)

To make data survive deploys on Railway: attach a Volume with mount path /data.
Without it the code still works — it just resets when the container restarts.

Tables:
  metric_snapshots   — one shop-level row per day (revenue, orders, ratings…)
  listing_snapshots  — per-listing daily views/favorites/price (for conversion)
  action_queue       — staged actions awaiting Scott's approval (next layer)
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


def _resolve_db_path() -> str:
    env = os.getenv("DB_PATH")
    if env:
        p = Path(env)
    else:
        vol = Path("/data")
        if vol.is_dir() and os.access(vol, os.W_OK):
            p = vol / "hub.db"
        else:
            p = Path(__file__).parent / "hub_data" / "hub.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


DB_PATH = _resolve_db_path()


def resolve_persistent_path(relative: str, fallback: Path, seed_from: Path | None = None) -> Path:
    """Resolve `relative` under the persistent /data volume if one is mounted
    and writable, else fall back to `fallback` (ephemeral, wiped on redeploy).
    Mirrors _resolve_db_path()'s own /data detection so every subsystem agrees
    on what counts as durable — added 2026-07-09 for the knowledge-base files
    (ops_runbook.md, ceo_learnings.md, registered_commands.json), which were a
    second, separate persistence gap from hub.db: they live at a repo-relative
    path, not under /data, so attaching a Volume alone didn't fix them.

    If `seed_from` is given and the resolved /data path doesn't exist yet,
    copies its current content over once (e.g. the image's baked-in
    ops_runbook.md history) so switching to persistent storage doesn't look
    like the history vanished."""
    vol = Path("/data")
    if vol.is_dir() and os.access(vol, os.W_OK):
        p = vol / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        if seed_from is not None and not p.exists() and seed_from.exists():
            p.write_text(seed_from.read_text())
        return p
    return fallback


_init_lock = threading.Lock()
_initialized = False

_SCHEMA = """
CREATE TABLE IF NOT EXISTS metric_snapshots (
  snapshot_date   TEXT PRIMARY KEY,   -- YYYY-MM-DD, one row/day (upserted)
  ts              TEXT NOT NULL,
  revenue_7d      REAL,
  revenue_30d     REAL,
  orders_7d       INTEGER,
  orders_30d      INTEGER,
  active_listings INTEGER,
  total_sales     INTEGER,
  avg_rating      REAL,
  total_reviews   INTEGER,
  raw_json        TEXT
);
CREATE TABLE IF NOT EXISTS listing_snapshots (
  snapshot_date TEXT NOT NULL,
  listing_id    INTEGER NOT NULL,
  title         TEXT,
  state         TEXT,
  price         REAL,
  views         INTEGER,
  num_favorers  INTEGER,
  PRIMARY KEY (snapshot_date, listing_id)
);
CREATE TABLE IF NOT EXISTS action_queue (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at   TEXT NOT NULL,
  type         TEXT NOT NULL,
  summary      TEXT,
  payload_json TEXT,
  status       TEXT NOT NULL DEFAULT 'pending',  -- pending/approved/rejected/executed/failed
  result_json  TEXT,
  decided_at   TEXT
);
-- Composite index satisfies both list_actions(status=...)'s WHERE and its
-- ORDER BY created_at DESC from the index directly (2026-07-08 performance pass —
-- this table previously did a full scan on every /api/queue and /api/actions poll).
CREATE INDEX IF NOT EXISTS idx_action_queue_status ON action_queue(status, created_at DESC);
CREATE TABLE IF NOT EXISTS chat_messages (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  TEXT NOT NULL,
  role        TEXT NOT NULL,   -- 'user' | 'assistant'
  content     TEXT NOT NULL,   -- plain text only; tool_use/tool_result blocks are NOT persisted
  created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id, id);
CREATE TABLE IF NOT EXISTS chat_summaries (
  session_id  TEXT PRIMARY KEY,
  summary     TEXT NOT NULL,
  through_id  INTEGER NOT NULL,  -- highest chat_messages.id folded into `summary`
  updated_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS quality_audits (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  ts          TEXT NOT NULL,
  passed      INTEGER,
  warned      INTEGER,
  failed      INTEGER,
  summary     TEXT     -- short text: which listings failed and why
);
CREATE TABLE IF NOT EXISTS etsy_rate_limit_log (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  ts                    TEXT NOT NULL,
  remaining_today       INTEGER,
  remaining_this_second INTEGER,
  limit_per_day         INTEGER,
  limit_per_second      INTEGER
);
CREATE INDEX IF NOT EXISTS idx_rate_limit_ts ON etsy_rate_limit_log(ts);
CREATE TABLE IF NOT EXISTS etsy_tokens (
  id                    INTEGER PRIMARY KEY CHECK (id = 1),  -- singleton row
  access_token          TEXT NOT NULL,
  refresh_token         TEXT NOT NULL,
  parent_refresh_token  TEXT,   -- the refresh_token this one rotated FROM (lineage check)
  updated_at            TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS todos (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  text          TEXT NOT NULL,
  added_by      TEXT NOT NULL DEFAULT 'scott',  -- 'scott' | 'frank' — who created it
  done          INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT NOT NULL,
  completed_at  TEXT
);
CREATE TABLE IF NOT EXISTS allowed_folders (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  path       TEXT NOT NULL UNIQUE,
  added_at   TEXT NOT NULL,
  added_by   TEXT NOT NULL DEFAULT 'system'
);
CREATE TABLE IF NOT EXISTS activity_log (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  ts           TEXT NOT NULL,
  actor        TEXT NOT NULL,
  action_type  TEXT NOT NULL,
  detail       TEXT,
  payload_json TEXT,
  outcome      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_activity_ts ON activity_log(ts);
-- Satisfies list_activity(action_type=...)'s WHERE + ORDER BY id DESC (2026-07-08
-- performance pass).
CREATE INDEX IF NOT EXISTS idx_activity_action_type ON activity_log(action_type, id DESC);
CREATE TABLE IF NOT EXISTS relay_state (
  id             INTEGER PRIMARY KEY CHECK (id = 1),  -- singleton row
  last_heartbeat TEXT,
  killed         INTEGER NOT NULL DEFAULT 0,
  killed_at      TEXT,
  killed_by      TEXT
);
CREATE TABLE IF NOT EXISTS agent_heartbeats (
  name       TEXT PRIMARY KEY,   -- loop identifier, e.g. 'snapshot', 'autoresponder'
  label      TEXT NOT NULL,      -- human-readable display name for the HUD
  status     TEXT NOT NULL,      -- 'started' | 'ok' | 'error'
  detail     TEXT,               -- short free-text result of the last run
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS circuit_breaker_state (
  dep_name        TEXT PRIMARY KEY,  -- 'etsy_api' | 'anthropic_api' | 'relay' | ...
  state           TEXT NOT NULL DEFAULT 'closed',  -- 'closed' | 'open' | 'half_open'
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  opened_at       TEXT,
  updated_at      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS user_profile (
  id         INTEGER PRIMARY KEY CHECK (id = 1),  -- singleton row
  name       TEXT,
  email      TEXT,
  phone      TEXT,
  timezone   TEXT,
  updated_at TEXT
);
CREATE TABLE IF NOT EXISTS hub_users (
  username   TEXT PRIMARY KEY,        -- lowercase
  pw_hash    TEXT NOT NULL,           -- pbkdf2:sha256:<salt>$<dk_hex>
  role       TEXT NOT NULL DEFAULT 'admin',  -- 'owner' | 'admin'
  created_at TEXT NOT NULL,
  recovery_code_hash TEXT             -- same pbkdf2 format as pw_hash; shown once at
                                       -- creation, lets "Forgot password?" reset without email
);
CREATE TABLE IF NOT EXISTS hub_sessions (
  session_id TEXT PRIMARY KEY,
  username   TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_hub_sessions_user ON hub_sessions(username);
CREATE TABLE IF NOT EXISTS settings (
  key        TEXT PRIMARY KEY,   -- e.g. 'agent_name', 'image_engine', 'model_primary'
  value      TEXT,               -- string value; NULL/absent = fall back to env/default
  updated_at TEXT
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    # synchronous is a per-connection session setting (unlike journal_mode, which is a
    # persistent file property set once in init_db()) -- it resets to SQLite's FULL
    # default on every new connection, and this codebase opens one connection per
    # operation, so it belongs here. NORMAL is the standard safe pairing with WAL:
    # committed transactions remain durable, only protection against an OS-level crash
    # mid-write is relaxed (2026-07-08 performance pass).
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db() -> None:
    global _initialized
    with _init_lock:
        if _initialized:
            return
        conn = _connect()
        try:
            # WAL mode is a persistent file-level property — set once at init, not per connection
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(_SCHEMA)
            try:
                conn.execute("ALTER TABLE todos ADD COLUMN due_date TEXT")
            except sqlite3.OperationalError:
                pass  # column already exists
            try:
                conn.execute("ALTER TABLE hub_users ADD COLUMN recovery_code_hash TEXT")
            except sqlite3.OperationalError:
                pass  # column already exists
            conn.commit()
        finally:
            conn.close()
        _initialized = True


def is_persistent() -> bool:
    """True when the DB lives on a mounted volume (survives redeploys)."""
    return DB_PATH.startswith("/data") or bool(os.getenv("DB_PATH"))


def record_metric_snapshot(metrics: dict, listings: list) -> str:
    """Upsert today's shop snapshot + per-listing rows. Returns the date string."""
    init_db()
    d = date.today().isoformat()
    ts = datetime.now(timezone.utc).isoformat()
    o = metrics.get("orders", {}) or {}
    sh = metrics.get("shop", {}) or {}
    rev = metrics.get("reviews", {}) or {}

    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO metric_snapshots
                 (snapshot_date, ts, revenue_7d, revenue_30d, orders_7d, orders_30d,
                  active_listings, total_sales, avg_rating, total_reviews, raw_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(snapshot_date) DO UPDATE SET
                 ts=excluded.ts, revenue_7d=excluded.revenue_7d, revenue_30d=excluded.revenue_30d,
                 orders_7d=excluded.orders_7d, orders_30d=excluded.orders_30d,
                 active_listings=excluded.active_listings, total_sales=excluded.total_sales,
                 avg_rating=excluded.avg_rating, total_reviews=excluded.total_reviews,
                 raw_json=excluded.raw_json""",
            (
                d, ts, o.get("revenue_7d"), o.get("revenue_30d"),
                o.get("last_7_days"), o.get("last_30_days"),
                sh.get("active_listing_count"), sh.get("total_sales"),
                rev.get("avg_rating"), rev.get("total_count"),
                json.dumps(metrics),
            ),
        )
        for l in listings:
            conn.execute(
                """INSERT INTO listing_snapshots
                     (snapshot_date, listing_id, title, state, price, views, num_favorers)
                   VALUES (?,?,?,?,?,?,?)
                   ON CONFLICT(snapshot_date, listing_id) DO UPDATE SET
                     title=excluded.title, state=excluded.state, price=excluded.price,
                     views=excluded.views, num_favorers=excluded.num_favorers""",
                (
                    d, l.get("listing_id"), l.get("title"), l.get("state"),
                    l.get("price"), l.get("views"), l.get("num_favorers"),
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return d


def get_metric_history(days: int = 30) -> list:
    """Most recent `days` shop snapshots, oldest-first (ready for charting)."""
    init_db()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM metric_snapshots ORDER BY snapshot_date DESC LIMIT ?",
            (days,),
        ).fetchall()
        return [dict(r) for r in rows][::-1]
    finally:
        conn.close()


def get_listing_history(listing_id: int, days: int = 30) -> list:
    init_db()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM listing_snapshots WHERE listing_id=? ORDER BY snapshot_date DESC LIMIT ?",
            (listing_id, days),
        ).fetchall()
        return [dict(r) for r in rows][::-1]
    finally:
        conn.close()


# ── Action queue (staged changes awaiting Scott's approval) ──────────────────────


def enqueue_action(action_type: str, summary: str, payload: dict) -> int:
    """Stage a proposed change. Returns the new queue id. Status starts 'pending'."""
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO action_queue (created_at, type, summary, payload_json, status) "
            "VALUES (?,?,?,?, 'pending')",
            (ts, action_type, summary, json.dumps(payload or {})),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _row_to_action(r) -> dict:
    d = dict(r)
    d["payload"] = json.loads(d.pop("payload_json") or "{}")
    if d.get("result_json"):
        try:
            d["result"] = json.loads(d["result_json"])
        except Exception:
            d["result"] = {"raw": d["result_json"]}
    d.pop("result_json", None)
    return d


def list_actions(status: str | None = "pending", limit: int = 100) -> list:
    init_db()
    conn = _connect()
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM action_queue WHERE status=? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM action_queue ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [_row_to_action(r) for r in rows]
    finally:
        conn.close()


def get_action(action_id: int) -> dict | None:
    init_db()
    conn = _connect()
    try:
        r = conn.execute("SELECT * FROM action_queue WHERE id=?", (action_id,)).fetchone()
        return _row_to_action(r) if r else None
    finally:
        conn.close()


def set_action_status(action_id: int, status: str, result: dict | None = None) -> bool:
    """Update an action's status (+ optional result). Sets decided_at. Returns True if a row changed."""
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        cur = conn.execute(
            "UPDATE action_queue SET status=?, result_json=?, decided_at=? WHERE id=?",
            (status, json.dumps(result) if result is not None else None, ts, action_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Chat memory (Frank's conversation survives reconnects & restarts) ─────────────
#
# Only plain text is persisted — never the assistant's tool_use blocks or their
# matching tool_result messages. Persisting half of a tool_use/tool_result pair
# would make a reloaded history 400 at the Anthropic API ("tool_use ids without
# tool_result"). Text-only history is always valid to replay and still gives
# Frank the full thread of what was said, so he never "forgets" after a mobile
# socket drop. Tools are simply re-called live if he needs fresh data.


def append_chat_message(session_id: str, role: str, content: str) -> int:
    """Persist one chat turn (plain text). Returns the new row id."""
    if not session_id or not content:
        return 0
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (?,?,?,?)",
            (session_id, role, content, ts),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def load_chat_history(session_id: str, limit: int = 40) -> list:
    """Most recent `limit` messages for a session, oldest-first, as Anthropic
    message dicts: [{"role": ..., "content": <text>}]. Empty list for unknown
    sessions. `limit` bounds replayed context so a long-lived session can't grow
    the prompt without bound."""
    if not session_id:
        return []
    init_db()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows][::-1]
    finally:
        conn.close()


# ── Context compactor ────────────────────────────────────────────────────────
#
# load_chat_history()'s `limit` is a hard cutoff — anything older just vanishes
# from replay, same blind spot the KB-rotation work (_summarize_and_rotate_kb_file)
# closed for ops_runbook.md/ceo_learnings.md. chat_summaries gives a long-running
# session a real (if lossy) memory of everything before the replayed tail instead
# of silently forgetting it. One row per session — each compaction pass advances
# `through_id` and replaces the prior summary with a new one that folds it in.


def get_chat_summary(session_id: str) -> dict | None:
    """The session's running condensed summary, or None if it's never been
    compacted yet."""
    if not session_id:
        return None
    init_db()
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT summary, through_id, updated_at FROM chat_summaries WHERE session_id=?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return {"summary": row["summary"], "through_id": row["through_id"], "updated_at": row["updated_at"]}
    finally:
        conn.close()


def set_chat_summary(session_id: str, summary: str, through_id: int) -> None:
    """Upsert the session's running summary. `through_id` is the highest
    chat_messages.id folded into `summary` so far."""
    if not session_id:
        return
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO chat_summaries (session_id, summary, through_id, updated_at) VALUES (?,?,?,?) "
            "ON CONFLICT(session_id) DO UPDATE SET summary=excluded.summary, "
            "through_id=excluded.through_id, updated_at=excluded.updated_at",
            (session_id, summary, through_id, ts),
        )
        conn.commit()
    finally:
        conn.close()


def list_chat_summaries() -> list:
    """All sessions that have ever been compacted, newest-first. Backs the
    context_compactor tile on /api/agents/status."""
    init_db()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT session_id, through_id, updated_at FROM chat_summaries ORDER BY updated_at DESC"
        ).fetchall()
        return [{"session_id": r["session_id"], "through_id": r["through_id"], "updated_at": r["updated_at"]} for r in rows]
    finally:
        conn.close()


def load_chat_messages_since(session_id: str, after_id: int = 0, limit: int = 1000) -> list:
    """Messages for a session with id > after_id, ascending (oldest-first), as
    [{"id":, "role":, "content":}]. Used by the context compactor to pull the
    not-yet-summarized tail; `after_id=0` (the default) returns the whole session."""
    if not session_id:
        return []
    init_db()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, role, content FROM chat_messages WHERE session_id=? AND id>? ORDER BY id ASC LIMIT ?",
            (session_id, after_id, limit),
        ).fetchall()
        return [{"id": r["id"], "role": r["role"], "content": r["content"]} for r in rows]
    finally:
        conn.close()


def list_chat_sessions() -> list:
    """One row per distinct session_id, most-recently-active first. Each row:
    {"session_id", "message_count", "started_at", "last_at", "last_role", "last_snippet"}.
    "Sessions" here are long-lived per-device threads (one per browser/device Scott
    uses), not short discrete conversations — there will typically be very few of
    them, each potentially holding many messages. The "last message" is found via
    a derived-table join on a GROUP BY subquery rather than a window function,
    matching the plain-SQL style used everywhere else in this file."""
    init_db()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT
              s.session_id,
              s.message_count,
              s.started_at,
              s.last_at,
              m.role AS last_role,
              m.content AS last_content
            FROM (
              SELECT session_id,
                     COUNT(*) AS message_count,
                     MIN(created_at) AS started_at,
                     MAX(created_at) AS last_at,
                     MAX(id) AS last_id
              FROM chat_messages
              GROUP BY session_id
            ) s
            JOIN chat_messages m ON m.id = s.last_id
            ORDER BY s.last_at DESC
            """
        ).fetchall()
        out = []
        for r in rows:
            snippet = (r["last_content"] or "").strip().replace("\n", " ")
            if len(snippet) > 140:
                snippet = snippet[:140].rstrip() + "…"
            out.append({
                "session_id": r["session_id"],
                "message_count": r["message_count"],
                "started_at": r["started_at"],
                "last_at": r["last_at"],
                "last_role": r["last_role"],
                "last_snippet": snippet,
            })
        return out
    finally:
        conn.close()


def get_chat_session(session_id: str, limit: int = 500) -> dict:
    """Full message history for one session, ascending (oldest-first) — distinct
    from load_chat_history(), which is newest-N-then-reversed and built only to
    seed live agent context. Returns {"messages": [...], "truncated": bool}.
    `limit` is a safety cap, not a UX page size."""
    if not session_id:
        return {"messages": [], "truncated": False}
    init_db()
    conn = _connect()
    try:
        total = conn.execute(
            "SELECT COUNT(*) AS n FROM chat_messages WHERE session_id=?",
            (session_id,),
        ).fetchone()["n"]
        rows = conn.execute(
            "SELECT id, role, content, created_at FROM chat_messages "
            "WHERE session_id=? ORDER BY id ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return {
            "messages": [
                {"id": r["id"], "role": r["role"], "content": r["content"], "created_at": r["created_at"]}
                for r in rows
            ],
            "truncated": total > limit,
        }
    finally:
        conn.close()


def search_chat_messages(query: str, limit: int = 50) -> list:
    """Substring search across all sessions' message content, newest-first, capped
    at `limit`. SQLite's LIKE is case-insensitive for ASCII by default, so no
    LOWER() wrapping is needed. LIKE wildcard characters (% and _) in the user's
    query are escaped so a literal search like "50% off" behaves correctly
    instead of being interpreted as a wildcard."""
    query = (query or "").strip()
    if not query:
        return []
    init_db()
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, session_id, role, content, created_at FROM chat_messages "
            "WHERE content LIKE ? ESCAPE '\\' ORDER BY id DESC LIMIT ?",
            (f"%{escaped}%", limit),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "session_id": r["session_id"],
                "role": r["role"],
                "content": r["content"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()


# ── Quality audit history (automated daily listing_integrity_check runs) ─────


def record_quality_audit(passed: int, warned: int, failed: int, summary: str = "") -> int:
    """Log one automated quality-audit run. Append-only — gives Frank and Scott
    a trend line instead of only the latest snapshot. Returns the new row id."""
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO quality_audits (ts, passed, warned, failed, summary) VALUES (?,?,?,?,?)",
            (ts, passed, warned, failed, summary),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_quality_audit_history(limit: int = 30) -> list:
    """Most recent `limit` audit runs, oldest-first."""
    init_db()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM quality_audits ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows][::-1]
    finally:
        conn.close()


# ── Etsy rate-limit history (2026-07-10: before this, `EtsyAPIClient`
# captured Etsy's x-remaining-today/x-remaining-this-second headers into an
# in-memory dict only — lost on every restart, never logged anywhere, so
# "what's our real daily Etsy call volume" had no measured answer, only
# code-derived estimates. Wired via etsy_api.py's set_rate_limit_sample_hook
# so etsy_api.py itself never imports this module directly (same duck-typed
# hook pattern as set_circuit_breaker_hook — keeps standalone scripts that
# use EtsyAPIClient outside the FastAPI server working unchanged). ─────────


def record_rate_limit_sample(
    remaining_today: int | None,
    remaining_this_second: int | None,
    limit_per_day: int | None,
    limit_per_second: int | None,
) -> None:
    """Append one rate-limit snapshot. Called on every Etsy response that
    carries an x-remaining-today header (i.e. most calls) — cheap at the
    current (much-reduced) call volume; pruned to 30 days by
    prune_rate_limit_log(), piggybacked on the daily snapshot loop."""
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO etsy_rate_limit_log "
            "(ts, remaining_today, remaining_this_second, limit_per_day, limit_per_second) "
            "VALUES (?,?,?,?,?)",
            (ts, remaining_today, remaining_this_second, limit_per_day, limit_per_second),
        )
        conn.commit()
    finally:
        conn.close()


def get_rate_limit_history(limit: int = 500) -> list:
    """Most recent `limit` rate-limit samples, oldest-first."""
    init_db()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM etsy_rate_limit_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows][::-1]
    finally:
        conn.close()


def prune_rate_limit_log(days: int = 30) -> int:
    """Delete rate-limit samples older than `days`. Returns rows deleted."""
    init_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    conn = _connect()
    try:
        cur = conn.execute("DELETE FROM etsy_rate_limit_log WHERE ts < ?", (cutoff,))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


# ── Etsy token durability (survives Railway restarts) ────────────────────────
#
# Railway's filesystem is ephemeral: every restart re-injects whatever
# ETSY_ACCESS_TOKEN / ETSY_REFRESH_TOKEN the dashboard has stored, but Etsy
# rotates the refresh token on every use and invalidates the old one. If the
# live server refreshes the token and then restarts before anyone updates the
# dashboard, the next refresh attempt 401s with invalid_grant on a token that
# no longer exists anywhere. This table is the durable side of the fix: the
# server persists each rotation here, and on boot prefers this row over the
# (possibly stale) env var — but only when it's provably a forward rotation of
# the current env token (see parent_refresh_token), so a genuine manual
# re-authorization (tools/etsy_oauth.py + a fresh dashboard update) still wins.


def save_etsy_tokens(access_token: str, refresh_token: str, parent_refresh_token: str | None = None) -> None:
    """Persist the latest known-good Etsy OAuth token pair. Singleton row (id=1)."""
    if not access_token or not refresh_token:
        return
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO etsy_tokens (id, access_token, refresh_token, parent_refresh_token, updated_at)
               VALUES (1, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 access_token=excluded.access_token, refresh_token=excluded.refresh_token,
                 parent_refresh_token=excluded.parent_refresh_token, updated_at=excluded.updated_at""",
            (access_token, refresh_token, parent_refresh_token, ts),
        )
        conn.commit()
    finally:
        conn.close()


def get_etsy_tokens() -> dict | None:
    """The last persisted Etsy token pair, or None if nothing has been saved yet."""
    init_db()
    conn = _connect()
    try:
        r = conn.execute("SELECT * FROM etsy_tokens WHERE id=1").fetchone()
        return dict(r) if r else None
    finally:
        conn.close()


def db_info() -> dict:
    """Lightweight stats for the diagnostics endpoint."""
    try:
        init_db()
        conn = _connect()
        try:
            ms = conn.execute("SELECT COUNT(*) c FROM metric_snapshots").fetchone()["c"]
            ls = conn.execute("SELECT COUNT(*) c FROM listing_snapshots").fetchone()["c"]
            aq = conn.execute("SELECT COUNT(*) c FROM action_queue WHERE status='pending'").fetchone()["c"]
            latest = conn.execute(
                "SELECT snapshot_date FROM metric_snapshots ORDER BY snapshot_date DESC LIMIT 1"
            ).fetchone()
            return {
                "path": DB_PATH,
                "persistent": is_persistent(),
                "metric_snapshots": ms,
                "listing_snapshots": ls,
                "pending_actions": aq,
                "latest_snapshot": latest["snapshot_date"] if latest else None,
            }
        finally:
            conn.close()
    except Exception as exc:  # never let diagnostics crash the caller
        return {"path": DB_PATH, "error": str(exc)}


# ── Shared to-do list (Scott + Frank, always visible on the dashboard) ───────


def add_todo(text: str, added_by: str = "scott", due_date: str | None = None) -> int:
    """Add one to-do item. added_by is 'scott' or 'frank'. Returns the new id."""
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO todos (text, added_by, done, created_at, due_date) VALUES (?,?,0,?,?)",
            (text.strip(), added_by, ts, due_date),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_todos(include_done: bool = True, limit: int = 200) -> list:
    """Open items first (oldest first), then done items (most recently completed first)."""
    init_db()
    conn = _connect()
    try:
        open_rows = conn.execute(
            "SELECT * FROM todos WHERE done=0 ORDER BY created_at ASC LIMIT ?", (limit,)
        ).fetchall()
        items = [dict(r) for r in open_rows]
        if include_done:
            done_rows = conn.execute(
                "SELECT * FROM todos WHERE done=1 ORDER BY completed_at DESC LIMIT ?", (limit,)
            ).fetchall()
            items += [dict(r) for r in done_rows]
        return items
    finally:
        conn.close()


def set_todo_done(todo_id: int, done: bool) -> bool:
    init_db()
    ts = datetime.now(timezone.utc).isoformat() if done else None
    conn = _connect()
    try:
        cur = conn.execute(
            "UPDATE todos SET done=?, completed_at=? WHERE id=?",
            (1 if done else 0, ts, todo_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_todo(todo_id: int) -> bool:
    init_db()
    conn = _connect()
    try:
        cur = conn.execute("DELETE FROM todos WHERE id=?", (todo_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Allowed Folders (server-side staging-time check; relay re-checks at execution
# time with os.path.realpath against Scott's actual filesystem — that relay-side
# check is the real security boundary, this one is fast UX feedback only) ───────


def add_allowed_folder(path: str, added_by: str = "system") -> int:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO allowed_folders (path, added_at, added_by) VALUES (?,?,?)",
            (path, ts, added_by),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_allowed_folders() -> list:
    init_db()
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM allowed_folders ORDER BY added_at ASC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def remove_allowed_folder(folder_id: int) -> bool:
    init_db()
    conn = _connect()
    try:
        cur = conn.execute("DELETE FROM allowed_folders WHERE id=?", (folder_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def is_path_allowed(path: str) -> bool:
    """Best-effort string-prefix check against the allow-list. NOT the security
    boundary — this gives fast UX feedback at staging time only. The relay
    performs the real check at execution time using os.path.realpath against
    Scott's actual filesystem (this server never sees that filesystem)."""
    if not path:
        return False
    norm = path.replace("\\", "/").rstrip("/").lower()
    for f in list_allowed_folders():
        root = f["path"].replace("\\", "/").rstrip("/").lower()
        if norm == root or norm.startswith(root + "/"):
            return True
    return False


def ensure_default_sandbox_folder() -> None:
    """Seed the default sandbox folder on first run if the allow-list is empty."""
    init_db()
    if not list_allowed_folders():
        add_allowed_folder("/data/workspace", added_by="system")


_CORRECTION_PLAN_MARKER = "[Correction plan 2026-07-08]"

_CORRECTION_PLAN_TODOS = [
    # (text, added_by) -- added_by='frank' = Claude will do this without Scott.
    # added_by='scott' = genuinely requires Scott's own account/identity/payment access,
    # not something Frank can do via any existing tool or API key.
    (
        f"{_CORRECTION_PLAN_MARKER} URGENT: Rotate the leaked Etsy Client ID + Secret at "
        "etsy.com/developers/your-apps -> your app -> reveal + copy Keystring and Shared "
        "Secret -> paste into ETSY_CLIENT_ID / ETSY_CLIENT_SECRET in Railway env vars and "
        "local .env -> redeploy. This is not hypothetical: it is causing live 403 errors on "
        "listing sync and review checks right now. Frank cannot do this -- it requires your "
        "Etsy Developer Console login.",
        "scott",
    ),
    (
        f"{_CORRECTION_PLAN_MARKER} Attach a Railway Volume at /data (or upgrade to a plan "
        "that includes one, ~$5/mo) so the database survives redeploys. Right now /health "
        "reports persistent=false -- every push wipes every login, chat history, setting, "
        "and this very todo list back to empty. Frank cannot purchase or attach this -- it "
        "requires your Railway billing access.",
        "scott",
    ),
    (
        f"{_CORRECTION_PLAN_MARKER} Optional, your call: decide whether to pursue a second "
        "sales channel (Shopify, Gumroad, etc.) so revenue isn't 100% dependent on Etsy's "
        "cascade-penalty risk. Frank can research options and draft a comparison if you want "
        "one -- the platform choice and account setup still need to be yours.",
        "scott",
    ),
    (
        f"{_CORRECTION_PLAN_MARKER} Build a git-committed backup of the live database's "
        "non-secret state (todos, settings, action history, user list minus password "
        "hashes) so a redeploy wipe has a real recovery path even before a Volume exists.",
        "frank",
    ),
    (
        f"{_CORRECTION_PLAN_MARKER} Add a code-enforced check that a listing description's "
        "claimed page/sticker counts actually match the real uploaded file's contents, "
        "instead of resting only on the AI's self-report and manual review.",
        "frank",
    ),
    (
        f"{_CORRECTION_PLAN_MARKER} Add real HTTP-level tests (not just pure-function tests) "
        "for the highest-risk routes -- login/session handling and the staged-action "
        "approve/reject flow -- since currently zero of the 89+ live routes have request-level "
        "test coverage.",
        "frank",
    ),
    (
        f"{_CORRECTION_PLAN_MARKER} Fix 3 places where a failed session-revocation after a "
        "password change is silently swallowed instead of logged, so a real failure is "
        "actually visible instead of invisible.",
        "frank",
    ),
    (
        f"{_CORRECTION_PLAN_MARKER} Add a one-click 'recheck Etsy credentials now' action so "
        "credential status doesn't wait on the 5-minute health loop -- makes it fast for "
        "Scott to confirm his credential rotation (item above) actually worked.",
        "frank",
    ),
]


def seed_correction_plan_todos() -> int:
    """One-time seed of the post-audit correction-plan todos (2026-07-08), split into
    what Frank can do unassisted vs. what genuinely requires Scott's own account access.
    Idempotent by marker prefix so it's safe to call on every boot -- important because
    the production DB currently has no persistent volume and gets wiped on every
    redeploy (see the Scott-list item about attaching one), so without this the whole
    list would silently vanish after the very next push. Returns how many rows were
    inserted (0 if the marker is already present, i.e. not the first boot since wipe)."""
    init_db()
    conn = _connect()
    try:
        existing = conn.execute(
            "SELECT COUNT(*) FROM todos WHERE text LIKE ?", (f"{_CORRECTION_PLAN_MARKER}%",)
        ).fetchone()[0]
        if existing:
            return 0
    finally:
        conn.close()
    for text, added_by in _CORRECTION_PLAN_TODOS:
        add_todo(text, added_by=added_by)
    return len(_CORRECTION_PLAN_TODOS)


# ── Activity log (permanent, append-only — separate from action_queue, which
# clears once a pending item is decided). Gives a durable "everything Frank
# has done" history for review, queryable by type/date/actor for an audit UI. ──


def log_activity(actor: str, action_type: str, detail: str = "", payload: dict | None = None, outcome: str = "ok") -> int:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO activity_log (ts, actor, action_type, detail, payload_json, outcome) "
            "VALUES (?,?,?,?,?,?)",
            (ts, actor, action_type, detail, json.dumps(payload) if payload is not None else None, outcome),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_activity(limit: int = 200, action_type: str | None = None) -> list:
    init_db()
    conn = _connect()
    try:
        if action_type:
            rows = conn.execute(
                "SELECT * FROM activity_log WHERE action_type=? ORDER BY id DESC LIMIT ?",
                (action_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM activity_log ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            if d.get("payload_json"):
                try:
                    d["payload"] = json.loads(d.pop("payload_json"))
                except Exception:
                    d["payload"] = None
            else:
                d.pop("payload_json", None)
            out.append(d)
        return out
    finally:
        conn.close()


def anthropic_usage_since(since_iso: str, limit: int = 20000) -> list:
    """Every logged Anthropic call (activity_log action_type='anthropic_usage',
    see main.py's _log_anthropic_usage) at/after `since_iso` (ISO-8601 UTC).
    Used by /api/system/costs to sum real token usage into an estimated $ figure
    from Frank's own data. `limit` is a sane upper bound, not real pagination --
    this table only grows one row per Anthropic call, never per-request traffic."""
    init_db()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT payload_json FROM activity_log WHERE action_type='anthropic_usage' AND ts>=? "
            "ORDER BY id DESC LIMIT ?",
            (since_iso, limit),
        ).fetchall()
        out = []
        for r in rows:
            if r["payload_json"]:
                try:
                    out.append(json.loads(r["payload_json"]))
                except Exception:
                    pass
        return out
    finally:
        conn.close()


# ── Relay state (singleton row, same pattern as etsy_tokens — the kill switch
# must survive a server restart without silently un-killing) ─────────────────


def get_relay_state() -> dict:
    init_db()
    conn = _connect()
    try:
        r = conn.execute("SELECT * FROM relay_state WHERE id=1").fetchone()
        if r:
            return dict(r)
        return {"id": 1, "last_heartbeat": None, "killed": 0, "killed_at": None, "killed_by": None}
    finally:
        conn.close()


def set_relay_heartbeat(cpu: float | None = None, ram_pct: float | None = None) -> None:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO relay_state (id, last_heartbeat, killed)
               VALUES (1, ?, 0)
               ON CONFLICT(id) DO UPDATE SET last_heartbeat=excluded.last_heartbeat""",
            (ts,),
        )
        conn.commit()
    finally:
        conn.close()


def set_kill_switch(active: bool, by: str = "scott") -> None:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO relay_state (id, killed, killed_at, killed_by)
               VALUES (1, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 killed=excluded.killed, killed_at=excluded.killed_at, killed_by=excluded.killed_by""",
            (1 if active else 0, ts if active else None, by if active else None),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_profile() -> dict:
    init_db()
    conn = _connect()
    try:
        r = conn.execute("SELECT * FROM user_profile WHERE id=1").fetchone()
        if r:
            return dict(r)
        return {"id": 1, "name": None, "email": None, "phone": None, "timezone": None, "updated_at": None}
    finally:
        conn.close()


def save_user_profile(name: str | None, email: str | None, phone: str | None, tz: str | None) -> dict:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO user_profile (id, name, email, phone, timezone, updated_at)
               VALUES (1, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, email=excluded.email, phone=excluded.phone,
                 timezone=excluded.timezone, updated_at=excluded.updated_at""",
            (name, email, phone, tz, ts),
        )
        conn.commit()
    finally:
        conn.close()
    return get_user_profile()


# ── Runtime settings (key-value overrides for env-driven config) ───────────────
# A value here OVERRIDES the corresponding env var / default at runtime, so the
# Settings UI can change things like the agent name or AI engine without a
# redeploy. Absent/empty → the caller falls back to env/default. Reads are cached
# per-key in-process (invalidated on set) so hot paths (per-request config lookups)
# don't hit SQLite every time.
_settings_cache: dict = {}


def get_setting(key: str, default: str | None = None) -> str | None:
    """Return the stored override for `key`, or `default` if unset. Cached."""
    if key in _settings_cache:
        val = _settings_cache[key]
        return val if val is not None else default
    init_db()
    conn = _connect()
    try:
        r = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    finally:
        conn.close()
    val = r["value"] if r else None
    _settings_cache[key] = val
    return val if val is not None else default


def set_setting(key: str, value: str | None) -> None:
    """Upsert an override. value=None/'' clears it (falls back to env/default)."""
    init_db()
    value = (value or "").strip() or None
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        if value is None:
            conn.execute("DELETE FROM settings WHERE key=?", (key,))
        else:
            conn.execute(
                """INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value,
                     updated_at=excluded.updated_at""",
                (key, value, ts),
            )
        conn.commit()
    finally:
        conn.close()
    _settings_cache[key] = value


def all_settings() -> dict:
    """Return every stored override as a plain dict (for the Settings screen)."""
    init_db()
    conn = _connect()
    try:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    finally:
        conn.close()
    return {r["key"]: r["value"] for r in rows}


# ── Agent heartbeats (live-status registry) — each of the 5 real background
# loops (and the relay/compactor once built) upserts its own row here on every
# run so the HUD's Agents screen and Command Center tiles show real state
# instead of a hardcoded "Running" label. ───────────────────────────────────


def set_agent_heartbeat(name: str, label: str, status: str, detail: str = "") -> None:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO agent_heartbeats (name, label, status, detail, updated_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(name) DO UPDATE SET
                 label=excluded.label, status=excluded.status,
                 detail=excluded.detail, updated_at=excluded.updated_at""",
            (name, label, status, detail, ts),
        )
        conn.commit()
    finally:
        conn.close()


def list_agent_heartbeats() -> list:
    init_db()
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM agent_heartbeats ORDER BY name").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_agent_heartbeat(name: str) -> None:
    """Remove a loop's row entirely -- for a retired loop that will never run again,
    so it doesn't sit on the Agents HUD forever frozen at its last status."""
    init_db()
    conn = _connect()
    try:
        conn.execute("DELETE FROM agent_heartbeats WHERE name = ?", (name,))
        conn.commit()
    finally:
        conn.close()


# ── Circuit breaker state (per named dependency: 'etsy_api', 'anthropic_api',
# 'relay'...) — persisted so a trip survives a process restart instead of
# silently resetting to closed and immediately re-hammering a dependency that
# was failing right before the restart. ────────────────────────────────────


def get_circuit_breaker_state(dep_name: str) -> dict | None:
    init_db()
    conn = _connect()
    try:
        r = conn.execute(
            "SELECT * FROM circuit_breaker_state WHERE dep_name = ?", (dep_name,)
        ).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()


def set_circuit_breaker_state(
    dep_name: str, state: str, consecutive_failures: int, opened_at: str | None
) -> None:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO circuit_breaker_state
                 (dep_name, state, consecutive_failures, opened_at, updated_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(dep_name) DO UPDATE SET
                 state=excluded.state, consecutive_failures=excluded.consecutive_failures,
                 opened_at=excluded.opened_at, updated_at=excluded.updated_at""",
            (dep_name, state, consecutive_failures, opened_at, ts),
        )
        conn.commit()
    finally:
        conn.close()


# ── Hub user accounts (multi-user login: owner + admins) ────────────────────


def get_hub_user(username: str) -> dict | None:
    init_db()
    conn = _connect()
    try:
        r = conn.execute(
            "SELECT username, pw_hash, role, created_at, recovery_code_hash FROM hub_users WHERE username = ?",
            (username.lower(),),
        ).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()


def list_hub_users() -> list[dict]:
    init_db()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT username, role, created_at FROM hub_users ORDER BY created_at"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create_hub_user(username: str, pw_hash: str, role: str = "admin", recovery_code_hash: str | None = None) -> None:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO hub_users (username, pw_hash, role, created_at, recovery_code_hash) VALUES (?, ?, ?, ?, ?)",
            (username.lower(), pw_hash, role, ts, recovery_code_hash),
        )
        conn.commit()
    finally:
        conn.close()


def update_hub_user_password(username: str, pw_hash: str) -> None:
    init_db()
    conn = _connect()
    try:
        conn.execute(
            "UPDATE hub_users SET pw_hash = ? WHERE username = ?",
            (pw_hash, username.lower()),
        )
        conn.commit()
    finally:
        conn.close()


def delete_hub_user(username: str) -> None:
    init_db()
    conn = _connect()
    try:
        conn.execute("DELETE FROM hub_users WHERE username = ?", (username.lower(),))
        conn.commit()
    finally:
        conn.close()


def hub_users_empty() -> bool:
    init_db()
    conn = _connect()
    try:
        n = conn.execute("SELECT COUNT(*) FROM hub_users").fetchone()[0]
        return n == 0
    finally:
        conn.close()


# ── Hub sessions (persisted so sessions survive Railway restarts) ─────────────


def create_session(session_id: str, username: str, expires_at: float) -> None:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    exp_iso = datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO hub_sessions (session_id, username, expires_at, created_at) VALUES (?,?,?,?)",
            (session_id, username.lower(), exp_iso, ts),
        )
        conn.commit()
    finally:
        conn.close()


def get_session(session_id: str) -> dict | None:
    """Return {"session_id", "username", "expires_at"} or None if missing/expired."""
    if not session_id:
        return None
    init_db()
    conn = _connect()
    try:
        r = conn.execute(
            "SELECT session_id, username, expires_at FROM hub_sessions WHERE session_id=?",
            (session_id,),
        ).fetchone()
        if not r:
            return None
        now_iso = datetime.now(timezone.utc).isoformat()
        if r["expires_at"] < now_iso:
            conn.execute("DELETE FROM hub_sessions WHERE session_id=?", (session_id,))
            conn.commit()
            return None
        return dict(r)
    finally:
        conn.close()


def delete_session(session_id: str) -> None:
    if not session_id:
        return
    init_db()
    conn = _connect()
    try:
        conn.execute("DELETE FROM hub_sessions WHERE session_id=?", (session_id,))
        conn.commit()
    finally:
        conn.close()


def delete_sessions_for_user(username: str) -> int:
    """Delete all sessions for a user (e.g. after password reset). Returns row count."""
    if not username:
        return 0
    init_db()
    conn = _connect()
    try:
        cur = conn.execute(
            "DELETE FROM hub_sessions WHERE username=?", (username.lower(),)
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def purge_expired_sessions() -> int:
    """Delete all expired sessions. Returns the number of rows deleted."""
    init_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        cur = conn.execute("DELETE FROM hub_sessions WHERE expires_at < ?", (now_iso,))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def prune_old_actions(days: int = 90) -> int:
    """Delete executed/rejected action_queue rows older than `days`. Pending/approved
    rows are never touched regardless of age -- this only stops the table from growing
    unbounded (2026-07-08 performance pass; the table had no index-backed cleanup at all
    before this). Returns the number of rows deleted."""
    init_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    conn = _connect()
    try:
        cur = conn.execute(
            "DELETE FROM action_queue WHERE status IN ('executed','rejected') AND created_at < ?",
            (cutoff,),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
