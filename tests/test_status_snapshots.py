#!/usr/bin/env python3
"""
Regression test for Phase 3 of the mobile Ask-tab redesign (2026-07-22):
Star Seller / Ads & ROAS / COGS & Profit were previously live-recomputed
per request with no stored history. This adds a status_snapshots table
(db.py) upserted daily by an extended _take_snapshot() (main.py), and a new
GET /api/status-history?panel=... route mirroring get_analytics()'s shape.

Covers exactly the failure-isolation guarantee the phase was built around:
a Star-Seller/Ads/COGS compute failure must never break the existing,
working metric_snapshots write, nor the other two panels' writes.

Uses a throwaway temp SQLite DB (DB_PATH env var, set before importing
main/db) so this never touches the real dev database. No network, no live
Etsy -- the three _compute_*_status() functions are patched out.

Run: python tests/test_status_snapshots.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_status_snapshots_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "status-snapshots-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import db  # noqa: E402
import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_record_status_snapshot_upserts_same_day():
    d1 = db.record_status_snapshot("star_seller", {"status": "building", "revenue_90d": 100.0})
    d2 = db.record_status_snapshot("star_seller", {"status": "on_track", "revenue_90d": 350.0})
    check(d1 == d2, f"record_status_snapshot should return the same date on a same-day re-write, got {d1!r} vs {d2!r}")

    rows = db.get_status_history("star_seller", days=30)
    check(len(rows) == 1, f"a same-day re-write must upsert, not duplicate: {len(rows)} rows")
    check(rows[0]["status"] == "on_track", f"the second write should have overwritten status: {rows[0]}")
    import json
    check(json.loads(rows[0]["raw_json"])["revenue_90d"] == 350.0,
          f"the second write should have overwritten raw_json: {rows[0]['raw_json']}")


def test_get_status_history_oldest_first_and_panel_scoped():
    import sqlite3
    conn = sqlite3.connect(os.environ["DB_PATH"])
    conn.execute("DELETE FROM status_snapshots")
    rows = [
        ("2026-07-20", "ads_roas", "ok", '{"used": true, "month_roas": 1.5}'),
        ("2026-07-22", "ads_roas", "ok", '{"used": true, "month_roas": 3.0}'),
        ("2026-07-21", "ads_roas", "ok", '{"used": true, "month_roas": 2.0}'),
        ("2026-07-21", "cogs_margin", "ok", '{"used": true, "avg_margin_pct": 50.0}'),
    ]
    for d, panel, status, raw in rows:
        conn.execute(
            "INSERT INTO status_snapshots (snapshot_date, panel, ts, status, raw_json) VALUES (?,?,?,?,?)",
            (d, panel, d + "T00:00:00+00:00", status, raw),
        )
    conn.commit()
    conn.close()

    ads_hist = db.get_status_history("ads_roas", days=30)
    check([r["snapshot_date"] for r in ads_hist] == ["2026-07-20", "2026-07-21", "2026-07-22"],
          f"get_status_history must return oldest-first: {[r['snapshot_date'] for r in ads_hist]}")
    check(all(r["panel"] == "ads_roas" for r in ads_hist),
          f"get_status_history must be scoped to the requested panel only: {ads_hist}")

    cogs_hist = db.get_status_history("cogs_margin", days=30)
    check(len(cogs_hist) == 1, f"cogs_margin panel must not see ads_roas's rows: {cogs_hist}")


def test_take_snapshot_failure_isolation():
    """The exact scenario Phase 3 was built to guarantee: one panel's compute
    function raising must not break metric_snapshots (the pre-existing write)
    or the other two panels' writes."""
    import sqlite3
    conn = sqlite3.connect(os.environ["DB_PATH"])
    conn.execute("DELETE FROM status_snapshots")
    conn.execute("DELETE FROM metric_snapshots")
    conn.commit()
    conn.close()

    def failing_ads():
        raise RuntimeError("simulated Etsy Ads DataStore blowup")

    with patch.object(server, "_compute_star_seller_status", lambda: {"status": "on_track", "revenue_90d": 350.0}), \
         patch.object(server, "_compute_ads_status", failing_ads), \
         patch.object(server, "_compute_cogs_status", lambda: {"used": True, "avg_margin_pct": 55.5}), \
         patch.object(server, "_metrics_sync", lambda: {"orders": {}, "shop": {}, "reviews": {}}), \
         patch.object(server, "_listings_sync", lambda state: {"listings": []}):
        d = asyncio.run(server._take_snapshot())

    check(bool(d), "_take_snapshot() must still return a date even when one status panel's compute fn raises")
    check(len(db.get_metric_history(30)) == 1,
          "the existing metric_snapshots write must succeed unaffected by a status-panel failure")
    check(len(db.get_status_history("star_seller", 30)) == 1,
          "star_seller (unaffected panel) must still get its snapshot written")
    check(len(db.get_status_history("ads_roas", 30)) == 0,
          "ads_roas (the failing panel) must simply be skipped, not partially written")
    check(len(db.get_status_history("cogs_margin", 30)) == 1,
          "cogs_margin (unaffected panel, computed after the failing one) must still get its snapshot written")


def test_status_history_route_shape_and_validation():
    import sqlite3
    conn = sqlite3.connect(os.environ["DB_PATH"])
    conn.execute("DELETE FROM status_snapshots")
    conn.execute(
        "INSERT INTO status_snapshots (snapshot_date, panel, ts, status, raw_json) VALUES (?,?,?,?,?)",
        ("2026-07-22", "cogs_margin", "2026-07-22T00:00:00+00:00", "ok", '{"used": true, "avg_margin_pct": 42.5}'),
    )
    conn.commit()
    conn.close()

    resp = asyncio.run(server.get_status_history(panel="cogs_margin", days=30, _token="test"))
    check(resp["panel"] == "cogs_margin", f"response must echo the requested panel: {resp}")
    check(resp["dates"] == ["2026-07-22"], f"dates array wrong: {resp}")
    check(resp["trend"] == [42.5], f"trend must extract avg_margin_pct for cogs_margin: {resp}")
    check(resp["latest"].get("avg_margin_pct") == 42.5, f"latest must be the raw dict of the newest row: {resp}")

    try:
        asyncio.run(server.get_status_history(panel="not_a_real_panel", days=30, _token="test"))
        check(False, "an unknown panel must raise HTTPException(400), not silently succeed")
    except Exception as exc:
        check(getattr(exc, "status_code", None) == 400,
              f"unknown panel must raise a 400, got: {exc!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("STATUS SNAPSHOTS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("STATUS SNAPSHOTS TESTS OK — status_snapshots upserts by (date, panel), "
          "get_status_history() is oldest-first and panel-scoped, _take_snapshot() "
          "isolates a failing status panel from metric_snapshots and the other "
          "panels, and /api/status-history validates its panel param and extracts "
          "the right trend field per panel.")


if __name__ == "__main__":
    run()
