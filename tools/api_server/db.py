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
CREATE TABLE IF NOT EXISTS etsy_tokens (
  id                    INTEGER PRIMARY KEY CHECK (id = 1),  -- singleton row
  access_token          TEXT NOT NULL,
  refresh_token         TEXT NOT NULL,
  parent_refresh_token  TEXT,   -- the refresh_token this one rotated FROM (lineage check)
  updated_at            TEXT NOT NULL
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
