#!/usr/bin/env python3
"""
Tests for the Etsy API call log (2026-08-20) -- added after the
update_price silent-no-op incident (data/knowledge_base/ops_runbook.md's
2026-08-20 entry) made clear that diagnosing "which calls did we actually
make, and which ones failed" required manually re-checking 82 listings one
at a time, because nothing durable recorded per-call outcomes. The
existing etsy_rate_limit_log only ever recorded quota headers.

Covers both halves of the wiring:
  1. db.py: record_api_call() inserts correctly (including listing_id
     extraction from the path), get_api_call_summary() groups by
     method/path-template/action_type/ok with counts, get_api_calls_for_
     listing() returns one listing's history most-recent-first, and
     prune_api_call_log() respects the age cutoff.
  2. etsy_api.py: EtsyAPIClient._request() calls the hook (if set) exactly
     once per call with the right (method, path, status, ok, error,
     duration_ms, action_type) on both success and failure, and never
     raises if the hook itself throws (logging must not break a live
     Etsy call). A client with no action_type passed logs action_type=None.

Uses a throwaway temp SQLite DB (DB_PATH env var, set before importing db)
so this never touches the real dev database, matching every other db.py
test in this repo (see test_db_ranking_recovery.py).

Run: python tests/test_etsy_api_call_log.py
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_test_api_call_log_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import db  # noqa: E402
import etsy_api  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _reset():
    db.init_db()
    conn = db._connect()
    try:
        conn.execute("DELETE FROM etsy_api_call_log")
        conn.commit()
    finally:
        conn.close()


def _make_client(action_type=None):
    c = etsy_api.EtsyAPIClient(api_key="test-key", access_token="fake-token", action_type=action_type)
    return c


# ── db.py: record_api_call / listing_id extraction ───────────────────────────

def test_record_api_call_extracts_listing_id_from_path():
    _reset()
    db.record_api_call("GET", "listings/4519185019", 200, True, None, 120)
    db.record_api_call("GET", "listings/4519185019/inventory", 200, True, None, 90)
    db.record_api_call("GET", "shops/65012858/listings", 200, True, None, 200)  # no listing id
    rows = db.get_api_calls_for_listing(4519185019)
    check(len(rows) == 2, f"expected 2 rows for listing 4519185019, got {len(rows)}")
    other = db.get_api_calls_for_listing(65012858)
    check(len(other) == 0, f"a shop id in the path must not be mistaken for a listing id, got {other}")


def test_record_api_call_stores_action_type_and_error():
    _reset()
    db.record_api_call("PATCH", "listings/123", 404, False, "Etsy API 404: listing not found", 50,
                        action_type="update_price")
    rows = db.get_api_calls_for_listing(123)
    check(len(rows) == 1, f"expected 1 row, got {rows}")
    r = rows[0]
    check(r["ok"] == 0, f"ok must be stored as 0 for a failure, got {r['ok']!r}")
    check(r["action_type"] == "update_price", f"action_type not stored: {r}")
    check("listing not found" in (r["error"] or ""), f"error message not stored: {r}")
    check(r["status_code"] == 404, f"status_code not stored: {r}")


def test_get_api_calls_for_listing_most_recent_first():
    _reset()
    db.record_api_call("GET", "listings/999", 200, True, None, 10)
    db.record_api_call("PATCH", "listings/999", 200, True, None, 20)
    rows = db.get_api_calls_for_listing(999)
    check([r["method"] for r in rows] == ["PATCH", "GET"],
          f"expected most-recent-first order (PATCH then GET), got {[r['method'] for r in rows]}")


# ── db.py: get_api_call_summary grouping ──────────────────────────────────────

def test_get_api_call_summary_groups_by_path_template_and_ok():
    _reset()
    # Same endpoint shape across 3 different listings -- must roll up together
    for lid, ok in [(1001, True), (1002, False), (1003, False)]:
        db.record_api_call("PATCH", f"listings/{lid}", 200 if ok else 500, ok,
                            None if ok else "server error", 100, action_type="update_price")
    summary = db.get_api_call_summary(hours=24)
    update_price_rows = [r for r in summary if r["action_type"] == "update_price"]
    check(len(update_price_rows) == 2,
          f"expected 2 grouped rows (ok=1 and ok=0) for update_price, got {update_price_rows}")
    by_ok = {r["ok"]: r["n"] for r in update_price_rows}
    check(by_ok.get(1) == 1, f"expected 1 successful update_price call, got {by_ok}")
    check(by_ok.get(0) == 2, f"expected 2 failed update_price calls, got {by_ok}")
    for r in update_price_rows:
        check("{id}" in r["path_template"], f"listing id must be templated out for grouping, got {r}")


def test_get_api_call_summary_preserves_path_for_calls_with_no_listing_id():
    # Regression: SQLite's REPLACE(path, CAST(listing_id AS TEXT), '{id}') returns NULL
    # when listing_id is NULL (any NULL arg -> NULL result) -- confirmed live 2026-08-20
    # when a real incident's summary showed path_template: null for every non-listing
    # call (shop-level GETs, health checks), hiding exactly the calls that needed
    # diagnosing. path must fall back to the raw path, never collapse to null.
    _reset()
    db.record_api_call("GET", "shops/65012858/listings", 200, True, None, 50)
    db.record_api_call("GET", "shops/65012858", 500, False, "server error", 50)
    summary = db.get_api_call_summary(hours=24)
    check(all(r["path_template"] is not None for r in summary),
          f"a call with no listing_id must never collapse path_template to null, got {summary}")
    paths = {r["path_template"] for r in summary}
    check("shops/65012858/listings" in paths, f"raw path must be preserved when there's no listing id to template, got {summary}")
    check("shops/65012858" in paths, f"raw path must be preserved when there's no listing id to template, got {summary}")


def test_get_api_call_summary_respects_hours_window():
    _reset()
    import datetime as _dt
    conn = db._connect()
    try:
        old_ts = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=48)).isoformat()
        conn.execute(
            "INSERT INTO etsy_api_call_log (ts, method, path, listing_id, action_type, status_code, ok, error, duration_ms) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (old_ts, "GET", "listings/1", 1, None, 200, 1, None, 10),
        )
        conn.commit()
    finally:
        conn.close()
    db.record_api_call("GET", "listings/2", 200, True, None, 10)
    summary = db.get_api_call_summary(hours=24)
    total = sum(r["n"] for r in summary)
    check(total == 1, f"a call older than the window must be excluded, got total={total}: {summary}")


# ── db.py: prune_api_call_log ─────────────────────────────────────────────────

def test_prune_api_call_log_deletes_old_rows_only():
    _reset()
    import datetime as _dt
    conn = db._connect()
    try:
        old_ts = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=45)).isoformat()
        conn.execute(
            "INSERT INTO etsy_api_call_log (ts, method, path, listing_id, action_type, status_code, ok, error, duration_ms) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (old_ts, "GET", "listings/1", 1, None, 200, 1, None, 10),
        )
        conn.commit()
    finally:
        conn.close()
    db.record_api_call("GET", "listings/2", 200, True, None, 10)
    deleted = db.prune_api_call_log(days=30)
    check(deleted == 1, f"expected exactly 1 old row pruned, got {deleted}")
    remaining = db.get_api_calls_for_listing(2)
    check(len(remaining) == 1, f"the recent row must survive pruning, got {remaining}")


# ── etsy_api.py: hook wiring on _request() ────────────────────────────────────

def test_request_calls_hook_on_success_with_action_type():
    calls = []
    etsy_api.set_call_log_hook(lambda *a: calls.append(a))
    try:
        client = _make_client(action_type="update_price")
        with mock.patch.object(client, "_request_impl", return_value={"ok": True}):
            client._request("PATCH", "listings/4519185019")
    finally:
        etsy_api.set_call_log_hook(None)
    check(len(calls) == 1, f"expected exactly one hook call, got {len(calls)}")
    method, path, status, ok, error, duration_ms, action_type = calls[0]
    check(method == "PATCH" and path == "listings/4519185019", f"wrong method/path logged: {calls[0]}")
    check(ok is True, f"a successful call must log ok=True, got {ok}")
    check(action_type == "update_price", f"action_type not threaded through: {action_type}")
    check(isinstance(duration_ms, int) and duration_ms >= 0, f"duration_ms must be a real measurement: {duration_ms}")


def test_request_calls_hook_on_failure_with_error_and_status():
    calls = []
    etsy_api.set_call_log_hook(lambda *a: calls.append(a))
    try:
        client = _make_client()
        with mock.patch.object(client, "_request_impl", side_effect=etsy_api.EtsyAPIError(404, "not found")):
            try:
                client._request("GET", "listings/999")
            except etsy_api.EtsyAPIError:
                pass
    finally:
        etsy_api.set_call_log_hook(None)
    check(len(calls) == 1, f"expected exactly one hook call on failure, got {len(calls)}")
    method, path, status, ok, error, duration_ms, action_type = calls[0]
    check(ok is False, f"a failed call must log ok=False, got {ok}")
    check(status == 404, f"status must be the real EtsyAPIError.status, got {status}")
    check("not found" in (error or ""), f"error message must be logged, got {error!r}")
    check(action_type is None, f"a client with no action_type set must log None, got {action_type}")


def test_request_never_raises_when_hook_itself_fails():
    def _broken_hook(*a):
        raise RuntimeError("logging backend down")
    etsy_api.set_call_log_hook(_broken_hook)
    try:
        client = _make_client()
        with mock.patch.object(client, "_request_impl", return_value={"ok": True}):
            result = client._request("GET", "listings/1")
        check(result == {"ok": True}, "a broken log hook must not affect the real call's return value")
    except Exception as exc:
        check(False, f"a broken log hook must never break a live Etsy call, but raised: {exc}")
    finally:
        etsy_api.set_call_log_hook(None)


def test_request_with_no_hook_set_is_a_no_op():
    etsy_api.set_call_log_hook(None)
    client = _make_client()
    with mock.patch.object(client, "_request_impl", return_value={"ok": True}):
        result = client._request("GET", "listings/1")  # must not raise with no hook configured
    check(result == {"ok": True}, f"unexpected result with no hook set: {result}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("ETSY API CALL LOG TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("ETSY API CALL LOG TESTS OK — record_api_call()/get_api_call_summary()/"
          "get_api_calls_for_listing()/prune_api_call_log() all behave correctly, and "
          "EtsyAPIClient._request() logs every call's real outcome (success or failure, "
          "with action_type threaded through) via the hook without ever letting a broken "
          "logging backend break a live Etsy call.")


if __name__ == "__main__":
    run()
