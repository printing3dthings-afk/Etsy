"""
Test for the 2026-07-19 fix to _warm_suggestions()'s race with the
_suggestions_warming guard flag.

The manual POST /api/suggestions path already checked `_suggestions_warming`
before spawning a background compute (so a second dashboard visitor hitting a
cold cache wouldn't kick off a redundant one), but the SCHEDULED
_warm_suggestions() loop's own per-tick function never checked it -- if the
loop's timer fired at the same moment a manual request was already computing,
both could run the ~25s Anthropic synthesis concurrently: double spend for
that tick. Fixed by adding the same guard to the scheduled path.

Run: python tests/test_warm_suggestions_race.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_warmsugg_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "warmsugg-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _run_one_warm_suggestions_iteration():
    """Drives _warm_suggestions() through exactly one scheduled tick: the boot
    `asyncio.sleep(5)` must succeed (call #1), the iteration runs, then the
    loop's trailing `asyncio.sleep(delay)` (call #2) is where we stop it."""
    call_count = {"n": 0}

    async def _fake_sleep(_secs):
        call_count["n"] += 1
        if call_count["n"] >= 2:
            raise asyncio.CancelledError("stop after one iteration")

    with patch("asyncio.sleep", _fake_sleep):
        try:
            asyncio.run(server._warm_suggestions())
        except asyncio.CancelledError:
            pass


def test_scheduled_tick_skips_when_already_warming():
    with patch.object(server, "ANTHROPIC_KEY", "fake-key-for-test"), \
         patch.object(server, "_suggestions_warming", True), \
         patch.object(server, "_compute_suggestions") as mock_compute:
        _run_one_warm_suggestions_iteration()
    check(not mock_compute.called,
          "the scheduled tick must NOT call _compute_suggestions() while a compute is already in flight "
          "(_suggestions_warming=True) -- this is exactly the race that caused double Anthropic spend")


def test_scheduled_tick_runs_normally_when_not_warming():
    async def _fake_compute():
        return {"headline": "ok", "suggestions": []}

    with patch.object(server, "ANTHROPIC_KEY", "fake-key-for-test"), \
         patch.object(server, "_suggestions_warming", False), \
         patch.object(server, "_compute_suggestions", side_effect=_fake_compute) as mock_compute:
        _run_one_warm_suggestions_iteration()
    check(mock_compute.called,
          "the scheduled tick must still run normally (call _compute_suggestions()) when nothing else "
          "is already warming the cache -- the fix must not break the normal warm-cache path")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("WARM SUGGESTIONS RACE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("WARM SUGGESTIONS RACE TESTS OK — the scheduled cache-warm tick now skips when a compute is "
          "already in flight (no more double Anthropic spend), and still runs normally otherwise.")


if __name__ == "__main__":
    run()
