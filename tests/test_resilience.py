#!/usr/bin/env python3
"""
Resilience tests — retry/backoff + circuit-breaker primitives.

Why this exists: `tools/api_server/resilience.py` gates how every background
loop and every Etsy/Anthropic call degrades under a flaky dependency —
`retry_with_backoff`, `classify_tool_exception`, and `CircuitBreaker`'s
closed -> open -> half_open -> closed state machine. None of it had test
coverage; a regression here (e.g. a breaker that never re-closes, or a retry
loop that swallows a non-retryable validation error) would silently degrade
or wedge live automation with nothing to catch it before deploy.

Deliberately dependency-light and secret-free: no server, no network, no API
keys, no real sleeps (CircuitBreaker is driven with a fake in-memory
db_module — the same seam the module itself documents as being "for callers
that only want the in-memory behavior (e.g. unit tests)" — and
retry_with_backoff's delays are kept sub-millisecond via base_delay).

Run locally:  python tests/test_resilience.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a gate regressed (prints which).
"""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools" / "api_server",):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

from resilience import (  # noqa: E402
    CircuitBreaker,
    CircuitBreakerOpenError,
    NotFoundToolError,
    TerminalToolError,
    TransientToolError,
    ValidationToolError,
    classify_tool_exception,
    retry_with_backoff,
)

# ── tiny test harness (matches tests/test_quality_gates.py style) ──────────────
_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def expect_raises(exc, fn, msg: str) -> None:
    try:
        fn()
    except exc:
        return
    except Exception as e:  # noqa: BLE001
        _failures.append(f"{msg} (raised {type(e).__name__} instead of {exc.__name__})")
        return
    _failures.append(f"{msg} (no exception raised)")


class _FakeClock:
    """Stand-in for datetime.now(timezone.utc) so cooldown-elapsed logic is
    testable without a real sleep."""

    def __init__(self, start):
        self.now = start

    def advance(self, seconds: float) -> None:
        from datetime import timedelta
        self.now = self.now + timedelta(seconds=seconds)


class _FakeDB:
    """In-memory stand-in for db.py's circuit-breaker persistence — same shape
    as db.get_circuit_breaker_state/set_circuit_breaker_state, but scoped to
    the test instead of a real sqlite file."""

    def __init__(self):
        self._rows: dict[str, dict] = {}

    def get_circuit_breaker_state(self, dep_name: str):
        return self._rows.get(dep_name)

    def set_circuit_breaker_state(self, dep_name, state, consecutive_failures, opened_at):
        self._rows[dep_name] = {
            "state": state,
            "consecutive_failures": consecutive_failures,
            "opened_at": opened_at,
        }


# ── retry_with_backoff ──────────────────────────────────────────────────────
def test_retry_succeeds_on_first_try_without_retrying():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        return "ok"

    result = retry_with_backoff(fn, max_attempts=3, base_delay=0.001)
    check(result == "ok", "successful first call should return its result")
    check(calls["n"] == 1, f"successful first call should not retry, called {calls['n']} times")


def test_retry_retries_transient_failure_then_succeeds():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("flaky")
        return "recovered"

    result = retry_with_backoff(fn, max_attempts=5, base_delay=0.001)
    check(result == "recovered", "should return the eventual success")
    check(calls["n"] == 3, f"should have retried exactly twice before succeeding, got {calls['n']} calls")


def test_retry_exhausts_max_attempts_and_reraises():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise TimeoutError("always fails")

    expect_raises(
        TimeoutError,
        lambda: retry_with_backoff(fn, max_attempts=3, base_delay=0.001),
        "should re-raise the last exception once max_attempts is exhausted",
    )
    check(calls["n"] == 3, f"should stop at max_attempts=3, got {calls['n']} calls")


def test_retry_does_not_retry_when_not_retryable():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise ValueError("bad input, retrying won't help")

    expect_raises(
        ValueError,
        lambda: retry_with_backoff(fn, max_attempts=5, base_delay=0.001, retryable=lambda e: False),
        "should not retry when retryable() returns False",
    )
    check(calls["n"] == 1, f"non-retryable failure should call fn exactly once, got {calls['n']}")


def test_retry_on_retry_callback_fires_with_attempt_and_delay():
    seen = []

    def fn():
        if len(seen) < 2:
            raise ConnectionError("flaky")
        return "ok"

    def on_retry(attempt, exc, delay):
        seen.append((attempt, type(exc).__name__, delay))

    retry_with_backoff(fn, max_attempts=5, base_delay=0.001, on_retry=on_retry)
    check(len(seen) == 2, f"on_retry should fire once per retry, got {len(seen)} calls: {seen}")
    check(seen[0][0] == 1 and seen[1][0] == 2, f"attempt numbers should be 1-indexed and increasing: {seen}")


# ── classify_tool_exception ─────────────────────────────────────────────────
def test_classify_transient_tool_error_is_retryable():
    category, retryable = classify_tool_exception(TransientToolError("rate limited"))
    check(category == "transient", f"expected category 'transient', got {category!r}")
    check(retryable is True, "TransientToolError should be classified retryable")


def test_classify_validation_tool_error_is_not_retryable():
    category, retryable = classify_tool_exception(ValidationToolError("bad args"))
    check(category == "validation", f"expected category 'validation', got {category!r}")
    check(retryable is False, "ValidationToolError should not be retryable")


def test_classify_not_found_tool_error_is_not_retryable():
    category, retryable = classify_tool_exception(NotFoundToolError("no such listing"))
    check(category == "not_found", f"expected category 'not_found', got {category!r}")
    check(retryable is False, "NotFoundToolError should not be retryable")


def test_classify_terminal_tool_error_is_not_retryable():
    category, retryable = classify_tool_exception(TerminalToolError("unclassified"))
    check(category == "terminal", f"expected category 'terminal', got {category!r}")
    check(retryable is False, "TerminalToolError should not be retryable")


def test_classify_connection_error_is_retryable():
    category, retryable = classify_tool_exception(ConnectionError("dropped"))
    check(category == "transient", f"bare ConnectionError should classify as transient, got {category!r}")
    check(retryable is True, "ConnectionError should be retryable")


def test_classify_timeout_error_is_retryable():
    category, retryable = classify_tool_exception(TimeoutError("slow"))
    check(category == "transient", f"bare TimeoutError should classify as transient, got {category!r}")
    check(retryable is True, "TimeoutError should be retryable")


def test_classify_etsy_429_status_is_retryable():
    exc = Exception("rate limited")
    exc.status = 429
    category, retryable = classify_tool_exception(exc)
    check(category == "transient", f"HTTP 429 should classify as transient, got {category!r}")
    check(retryable is True, "HTTP 429 should be retryable")


def test_classify_etsy_403_status_is_retryable():
    # Etsy's PATCH endpoint has a known non-deterministic 403 that's actually
    # a server-side race, not a real permission error (documented in CLAUDE.md).
    exc = Exception("listing is not editable")
    exc.status_code = 403
    category, retryable = classify_tool_exception(exc)
    check(category == "transient", f"HTTP 403 (Etsy quirk) should classify as transient, got {category!r}")
    check(retryable is True, "HTTP 403 should be retryable per the documented Etsy race condition")


def test_classify_generic_exception_is_terminal():
    category, retryable = classify_tool_exception(RuntimeError("unexpected"))
    check(category == "terminal", f"an unclassified exception should default to terminal, got {category!r}")
    check(retryable is False, "an unclassified exception should not be retryable")


def test_classify_etsy_404_status_is_not_retryable():
    exc = Exception("not found")
    exc.status = 404
    category, retryable = classify_tool_exception(exc)
    check(category == "terminal", f"HTTP 404 should not be in the retryable status set, got {category!r}")
    check(retryable is False, "HTTP 404 should not be retryable")


# ── CircuitBreaker state machine ────────────────────────────────────────────
def test_breaker_starts_closed_and_allows_requests():
    breaker = CircuitBreaker("test_dep", db_module=_FakeDB())
    check(breaker.allow_request() is True, "a fresh breaker with no prior state should be closed/allow")


def test_breaker_stays_closed_below_failure_threshold():
    breaker = CircuitBreaker("test_dep", failure_threshold=5, db_module=_FakeDB())
    for _ in range(4):
        breaker.record_failure()
    check(breaker.allow_request() is True, "breaker should stay closed below failure_threshold")
    row = breaker._load()
    check(row["state"] == "closed", f"expected state 'closed' at 4/5 failures, got {row['state']!r}")
    check(row["consecutive_failures"] == 4, f"expected 4 consecutive failures, got {row['consecutive_failures']}")


def test_breaker_opens_at_failure_threshold():
    breaker = CircuitBreaker("test_dep", failure_threshold=3, db_module=_FakeDB())
    for _ in range(3):
        breaker.record_failure()
    row = breaker._load()
    check(row["state"] == "open", f"expected state 'open' at 3/3 failures, got {row['state']!r}")
    check(breaker.allow_request() is False, "an open breaker within its cooldown should reject requests")


def test_breaker_success_resets_failure_count():
    breaker = CircuitBreaker("test_dep", failure_threshold=5, db_module=_FakeDB())
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_success()
    row = breaker._load()
    check(row["state"] == "closed", f"a success should close the breaker, got {row['state']!r}")
    check(row["consecutive_failures"] == 0, f"a success should reset the failure count, got {row['consecutive_failures']}")


def test_breaker_transitions_to_half_open_after_cooldown():
    import resilience as resilience_module

    fake_db = _FakeDB()
    breaker = CircuitBreaker("test_dep", failure_threshold=1, cooldown_seconds=30.0, db_module=fake_db)
    breaker.record_failure()  # trips open immediately (threshold=1)
    check(breaker.allow_request() is False, "should reject immediately after tripping open")

    # Simulate cooldown elapsing by rewriting opened_at into the past directly
    # in the fake store (avoids a real sleep in the test suite).
    row = fake_db.get_circuit_breaker_state("test_dep")
    from datetime import datetime, timedelta, timezone
    past = datetime.now(timezone.utc) - timedelta(seconds=60)
    fake_db.set_circuit_breaker_state("test_dep", "open", row["consecutive_failures"], past.isoformat())

    check(breaker.allow_request() is True, "should allow exactly one probe once cooldown has elapsed")
    row_after = breaker._load()
    check(row_after["state"] == "half_open", f"expected 'half_open' after cooldown probe, got {row_after['state']!r}")


def test_breaker_half_open_only_lets_one_probe_through():
    """2026-07-10 regression test: allow_request() used to return True
    unconditionally for every caller while state was half_open, letting a
    burst of concurrent requests all race through as duplicate probes -- the
    live incident that turned one Etsy rate-limit into a pile-up of hanging
    calls and 504s across several dashboard screens at once (see
    ops_runbook.md). Exactly one caller should win the open->half_open
    transition; every other caller in the same window must be rejected
    until the probe resolves via record_success()/record_failure()."""
    from datetime import datetime, timedelta, timezone

    fake_db = _FakeDB()
    breaker = CircuitBreaker("test_dep", failure_threshold=1, cooldown_seconds=30.0, db_module=fake_db)
    breaker.record_failure()  # trips open
    past = datetime.now(timezone.utc) - timedelta(seconds=60)
    row = fake_db.get_circuit_breaker_state("test_dep")
    fake_db.set_circuit_breaker_state("test_dep", "open", row["consecutive_failures"], past.isoformat())

    first = breaker.allow_request()
    second = breaker.allow_request()
    third = breaker.allow_request()
    check(first is True, "the first caller after cooldown elapses should win the probe")
    check(second is False, "a second caller before the probe resolves must be rejected, not treated as another probe")
    check(third is False, "a third caller before the probe resolves must also be rejected")


def test_breaker_half_open_race_exactly_one_winner_under_concurrency():
    """Same bug as above, proven under real thread concurrency rather than
    sequential calls -- the original bug was a plain read-then-write race
    between threads observing 'open, cooldown elapsed' at the same instant."""
    import threading
    from datetime import datetime, timedelta, timezone

    fake_db = _FakeDB()
    breaker = CircuitBreaker("test_dep", failure_threshold=1, cooldown_seconds=30.0, db_module=fake_db)
    breaker.record_failure()
    past = datetime.now(timezone.utc) - timedelta(seconds=60)
    row = fake_db.get_circuit_breaker_state("test_dep")
    fake_db.set_circuit_breaker_state("test_dep", "open", row["consecutive_failures"], past.isoformat())

    results: list[bool] = []
    results_lock = threading.Lock()
    n = 20
    barrier = threading.Barrier(n)

    def worker():
        barrier.wait()  # maximize the chance every thread hits allow_request() near-simultaneously
        r = breaker.allow_request()
        with results_lock:
            results.append(r)

    threads = [threading.Thread(target=worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    winners = sum(1 for r in results if r is True)
    check(len(results) == n, f"expected {n} results, got {len(results)}")
    check(winners == 1, f"expected exactly one caller to win the half-open probe under concurrency, got {winners} of {n}")


def test_breaker_stuck_half_open_recovers_after_extended_timeout():
    """Safety net: since half_open now unconditionally rejects new callers
    (the fix above), a probe whose caller crashed before reporting
    success/failure must not wedge the breaker open forever -- it should
    eventually allow a fresh probe rather than staying stuck."""
    from datetime import datetime, timedelta, timezone

    fake_db = _FakeDB()
    breaker = CircuitBreaker("test_dep", failure_threshold=1, cooldown_seconds=10.0, db_module=fake_db)
    long_ago = datetime.now(timezone.utc) - timedelta(seconds=10 * 3.5)  # past the 3x safety multiplier
    fake_db.set_circuit_breaker_state("test_dep", "half_open", 1, long_ago.isoformat())
    check(breaker.allow_request() is True, "a half_open state stuck far past 3x cooldown should allow a fresh probe")


def test_breaker_half_open_success_closes_it():
    fake_db = _FakeDB()
    breaker = CircuitBreaker("test_dep", failure_threshold=1, cooldown_seconds=0.0, db_module=fake_db)
    breaker.record_failure()
    fake_db.set_circuit_breaker_state("test_dep", "half_open", 1, None)
    breaker.record_success()
    row = breaker._load()
    check(row["state"] == "closed", f"a successful half-open probe should close the breaker, got {row['state']!r}")


def test_breaker_half_open_failure_reopens_it():
    fake_db = _FakeDB()
    breaker = CircuitBreaker("test_dep", failure_threshold=5, db_module=fake_db)
    fake_db.set_circuit_breaker_state("test_dep", "half_open", 1, None)
    breaker.record_failure()
    row = breaker._load()
    check(row["state"] == "open", f"a failed half-open probe should reopen the breaker, got {row['state']!r}")


def test_breaker_call_wraps_success():
    breaker = CircuitBreaker("test_dep", db_module=_FakeDB())
    result = breaker.call(lambda: "value")
    check(result == "value", "call() should return the wrapped function's result on success")
    row = breaker._load()
    check(row["state"] == "closed", "a successful call() should leave the breaker closed")


def test_breaker_call_records_failure_and_reraises():
    breaker = CircuitBreaker("test_dep", failure_threshold=5, db_module=_FakeDB())

    def boom():
        raise RuntimeError("dependency down")

    expect_raises(RuntimeError, lambda: breaker.call(boom), "call() should re-raise the wrapped exception")
    row = breaker._load()
    check(row["consecutive_failures"] == 1, f"call() should record the failure, got {row['consecutive_failures']}")


def test_breaker_call_raises_circuit_breaker_open_error_when_open():
    fake_db = _FakeDB()
    breaker = CircuitBreaker("test_dep", failure_threshold=1, cooldown_seconds=300.0, db_module=fake_db)
    breaker.record_failure()  # trips open
    expect_raises(
        CircuitBreakerOpenError,
        lambda: breaker.call(lambda: "never runs"),
        "call() on an open breaker (within cooldown) should raise CircuitBreakerOpenError without calling fn",
    )


def test_breaker_state_is_isolated_per_dependency():
    fake_db = _FakeDB()
    etsy_breaker = CircuitBreaker("etsy", failure_threshold=1, db_module=fake_db)
    anthropic_breaker = CircuitBreaker("anthropic", failure_threshold=1, db_module=fake_db)
    etsy_breaker.record_failure()
    check(etsy_breaker.allow_request() is False, "etsy breaker should be open after its own failure")
    check(anthropic_breaker.allow_request() is True, "anthropic breaker should be unaffected by etsy's failure")


# ── runner ────────────────────────────────────────────────────────────────────
def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ran = 0
    for t in tests:
        try:
            t()
            ran += 1
        except Exception:
            _failures.append(f"{t.__name__} raised an unexpected error:\n" + traceback.format_exc())
    if _failures:
        print("RESILIENCE TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"RESILIENCE TESTS OK — {ran} tests passed "
          f"(retry_with_backoff + classify_tool_exception + CircuitBreaker state machine).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
