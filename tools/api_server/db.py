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
from datetime import date, datetime, timezone
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
CREATE TABLE IF NOT EXISTS chat_messages (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  TEXT NOT NULL,
  role        TEXT NOT NULL,   -- 'user' | 'assistant'
  content     TEXT NOT NULL,   -- plain text only; tool_use/tool_result blocks are NOT persisted
  created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id, id);
CREATE TABLE IF NOT EXISTS quality_audits (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  ts          TEXT NOT NULL,
  passed      INTEGER,
  warned      INTEGER,
  failed      INTEGER,
  summary     TEXT     -- short text: which listings failed and why
);
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
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db() -> None:
    global _initialized
    with _init_lock:
        if _initialized:
            return
        conn = _connect()
        try:
            conn.executescript(_SCHEMA)
            try:
                conn.execute("ALTER TABLE todos ADD COLUMN due_date TEXT")
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
        add_allowed_folder(r"C:\Users\<you>\frank_sandbox", added_by="system")


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
