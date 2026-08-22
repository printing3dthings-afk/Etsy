"""
Agents screen audit fixes (2026-08-05).

Covers:
- sku_taxonomy_backfill is a real background loop that was missing from
  _AGENT_LOOP_LABELS -- it never got a tile on the Agents screen even though
  /api/alerts already surfaces its heartbeat errors. Now it's registered like
  every other interval loop.
- running_count used to count anything except "error" as running, so a
  freshly-seeded "started" tile (never run yet) or a disconnected relay's
  "offline" status both inflated the aggregate "N/N running" figure shown on
  the Home mini-panel, AI Core screen, and the header status pill -- while
  the individual tile itself rendered idle/grey. Now only "ok"/"warning"/
  "running" count as active.

Same pattern as tests/test_workflows_screen.py: direct db import + real
SQLite temp file, no mocking of the DB layer itself.
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_agents_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "agents-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import db  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_sku_taxonomy_backfill_is_a_registered_loop():
    check("sku_taxonomy_backfill" in server._AGENT_LOOP_LABELS,
          f"sku_taxonomy_backfill must be in _AGENT_LOOP_LABELS, got keys: "
          f"{list(server._AGENT_LOOP_LABELS.keys())}")


def test_sku_taxonomy_backfill_gets_a_real_tile_and_is_counted():
    db.init_db()
    db.set_agent_heartbeat("sku_taxonomy_backfill", "SKU + Category Backfill", "ok", "12 staged")
    snap = asyncio.run(server._agents_status_snapshot())
    names = [a["name"] for a in snap["agents"]]
    check("sku_taxonomy_backfill" in names,
          f"sku_taxonomy_backfill must appear as a tile in the snapshot, got: {names}")
    tile = next(a for a in snap["agents"] if a["name"] == "sku_taxonomy_backfill")
    check(tile["status"] == "ok", f"expected status 'ok', got: {tile['status']}")


def _seed_all_loops_and_compactor(status: str, detail: str) -> None:
    """Set every interval loop AND context_compactor to a known status, so
    running_count assertions don't depend on context_compactor's own
    heartbeat-absent default (which is "ok", separately from the loops under
    test) or on state left over from an earlier test in this file."""
    db.init_db()
    for name, label in server._AGENT_LOOP_LABELS.items():
        db.set_agent_heartbeat(name, label, status, detail)
    db.set_agent_heartbeat("context_compactor", "Context Compactor", status, detail)


def test_running_count_excludes_started_and_offline():
    _seed_all_loops_and_compactor("started", "waiting for first run")
    snap = asyncio.run(server._agents_status_snapshot())
    started_agents = [a for a in snap["agents"] if a["name"] in server._AGENT_LOOP_LABELS]
    check(all(a["status"] == "started" for a in started_agents),
          f"expected every seeded loop to read 'started', got: {[a['status'] for a in started_agents]}")
    # relay defaults to "offline" (no relay connected) in this test env -- confirm
    # it's excluded from running_count too, not just the interval loops.
    relay_tile = next(a for a in snap["agents"] if a["name"] == "local_relay")
    check(relay_tile["status"] == "offline",
          f"expected the relay to read 'offline' with no relay connected, got: {relay_tile['status']}")
    check(snap["running_count"] == 0,
          f"a freshly-seeded/never-run registry (loops AND context_compactor "
          f"both 'started') must report 0 running, not count 'started'/'offline' "
          f"as active (the exact bug: 'N/N running' while every tile is still "
          f"idle), got running_count={snap['running_count']} of "
          f"total_count={snap['total_count']}")


def test_running_count_includes_warning_and_running_as_active():
    _seed_all_loops_and_compactor("ok", "fine")
    # Flip two loops to non-"ok" active statuses that still represent real activity.
    names = list(server._AGENT_LOOP_LABELS.items())
    db.set_agent_heartbeat(names[0][0], names[0][1], "warning", "completed with a skip")
    db.set_agent_heartbeat(names[1][0], names[1][1], "running", "actively executing")
    snap = asyncio.run(server._agents_status_snapshot())
    loop_and_compactor = [a for a in snap["agents"]
                           if a["name"] in server._AGENT_LOOP_LABELS or a["name"] == "context_compactor"]
    check(all(a["status"] in ("ok", "warning", "running") for a in loop_and_compactor),
          f"unexpected statuses in fixture: {[(a['name'], a['status']) for a in loop_and_compactor]}")
    check(snap["running_count"] == len(loop_and_compactor),
          f"'warning' (completed-but-flagged) and 'running' (actively executing) "
          f"loops must both count as active alongside 'ok', not get demoted to "
          f"the same 'not running' bucket as a loop that never fired, got "
          f"running_count={snap['running_count']} for {len(loop_and_compactor)} "
          f"ok/warning/running tiles")


def test_running_count_excludes_error():
    _seed_all_loops_and_compactor("ok", "fine")
    first_name = next(iter(server._AGENT_LOOP_LABELS))
    db.set_agent_heartbeat(first_name, server._AGENT_LOOP_LABELS[first_name], "error", "boom")
    snap = asyncio.run(server._agents_status_snapshot())
    loop_and_compactor = [a for a in snap["agents"]
                           if a["name"] in server._AGENT_LOOP_LABELS or a["name"] == "context_compactor"]
    check(snap["running_count"] == len(loop_and_compactor) - 1,
          f"an errored loop must not count as running, got running_count="
          f"{snap['running_count']} for {len(loop_and_compactor)} ok tiles (1 errored)")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("AGENTS SCREEN TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("AGENTS SCREEN TESTS OK — sku_taxonomy_backfill is registered and "
          "running_count only counts genuinely active loop statuses.")


if __name__ == "__main__":
    run()
