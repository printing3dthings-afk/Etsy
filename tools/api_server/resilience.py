"""
Shared retry/backoff/circuit-breaker primitives.

Before this module, retry logic existed in exactly one place in main.py (a
one-off Etsy 403 retry) and every background loop slept a fixed 60-120s
between iterations regardless of whether the last run failed. This module
gives every caller the same jittered-exponential-backoff and
trip/cooldown/half-open circuit-breaker behavior, so a flaky dependency
degrades gracefully instead of either hammering it every minute or needing
a bespoke retry block written by hand each time.

Nothing here ever bypasses the Action Center approval gate -- these
primitives only wrap *how* a call is retried, never *whether* a mutation is
allowed to happen.
"""
from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timezone
from typing import Callable, TypeVar

logger = logging.getLogger("resilience")

T = TypeVar("T")


def retry_with_backoff(
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retryable: Callable[[Exception], bool] = lambda e: True,
    on_retry: Callable[[int, Exception, float], None] | None = None,
) -> T:
    """Call fn() with exponential backoff (full jitter) on retryable failures.

    Re-raises the last exception if max_attempts is exhausted, or
    immediately re-raises if `retryable(e)` returns False (no point
    retrying a permission/validation error).
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - intentionally broad, classified by `retryable`
            if attempt >= max_attempts or not retryable(e):
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            if jitter:
                delay = random.uniform(0, delay)  # full jitter
            if on_retry:
                on_retry(attempt, e, delay)
            else:
                logger.warning(
                    "retry_with_backoff: attempt %d/%d failed (%s), retrying in %.2fs",
                    attempt, max_attempts, e, delay,
                )
            time.sleep(delay)


class ToolError(Exception):
    """Base for agent-tool failures that carry a retry classification.

    `category` is one of "transient" / "permission" / "validation" /
    "not_found" / "terminal" so `_execute_agent_tool`'s closing handler (and
    the model reading its output) can decide whether retrying is worth it,
    rather than treating every failure identically.
    """

    category = "terminal"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class TransientToolError(ToolError):
    """A retryable failure: rate limit, timeout, 5xx, connection drop."""

    category = "transient"


class ValidationToolError(ToolError):
    """Bad input from the model -- retrying with the same args won't help."""

    category = "validation"


class NotFoundToolError(ToolError):
    """The referenced resource (listing, file, command) doesn't exist."""

    category = "not_found"


class TerminalToolError(ToolError):
    """An unclassified or permanent failure -- not worth retrying blindly."""

    category = "terminal"


_RETRYABLE_CATEGORIES = {"transient"}

# Etsy API status codes worth retrying: rate limit + server-side hiccups.
_RETRYABLE_ETSY_STATUSES = {403, 429, 500, 502, 503}


def classify_tool_exception(exc: Exception) -> tuple[str, bool]:
    """Map an arbitrary exception to (category, retryable) for the agent loop.

    Used by `_execute_agent_tool`'s closing exception handler so a tool
    failure reaches the model as a structured `{error, category, retryable}`
    dict instead of a bare string -- the model can then decide to retry a
    transient failure once, or report a terminal one to Scott rather than
    guessing or looping.
    """
    if isinstance(exc, ToolError):
        return exc.category, exc.category in _RETRYABLE_CATEGORIES
    status = getattr(exc, "status", None) or getattr(exc, "status_code", None)
    if status is not None and status in _RETRYABLE_ETSY_STATUSES:
        return "transient", True
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return "transient", True
    return "terminal", False


class CircuitBreakerOpenError(Exception):
    """Raised when a call is rejected because the breaker is open."""


class CircuitBreaker:
    """Per-dependency circuit breaker, persisted via db.py so a trip survives
    a process restart.

    States: closed (normal) -> open (after `failure_threshold` consecutive
    failures, rejects calls for `cooldown_seconds`) -> half_open (one probe
    call allowed) -> closed (probe succeeded) or open again (probe failed).
    """

    def __init__(
        self,
        dep_name: str,
        *,
        failure_threshold: int = 5,
        cooldown_seconds: float = 60.0,
        db_module=None,
    ):
        self.dep_name = dep_name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        # Lazy import to avoid a hard dependency on db.py for callers that
        # only want the in-memory behavior (e.g. unit tests).
        if db_module is None:
            from . import db as db_module  # type: ignore
        self._db = db_module

    def _load(self) -> dict:
        row = self._db.get_circuit_breaker_state(self.dep_name)
        if row:
            return row
        return {"state": "closed", "consecutive_failures": 0, "opened_at": None}

    def _save(self, state: str, consecutive_failures: int, opened_at: str | None) -> None:
        self._db.set_circuit_breaker_state(self.dep_name, state, consecutive_failures, opened_at)

    def allow_request(self) -> bool:
        """Check (and advance) breaker state before making a call. Returns
        True if the call should proceed (closed, or half-open probe)."""
        row = self._load()
        if row["state"] == "closed":
            return True
        if row["state"] == "open":
            opened_at = row.get("opened_at")
            if not opened_at:
                return True
            elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(opened_at)).total_seconds()
            if elapsed >= self.cooldown_seconds:
                self._save("half_open", row["consecutive_failures"], row.get("opened_at"))
                return True
            return False
        # half_open: allow exactly one probe through; caller's success/failure
        # report will resolve it back to closed or open.
        return True

    def record_success(self) -> None:
        self._save("closed", 0, None)

    def record_failure(self) -> None:
        row = self._load()
        failures = row.get("consecutive_failures", 0) + 1
        if row["state"] == "half_open" or failures >= self.failure_threshold:
            self._save("open", failures, datetime.now(timezone.utc).isoformat())
        else:
            self._save("closed", failures, None)

    def call(self, fn: Callable[[], T]) -> T:
        if not self.allow_request():
            raise CircuitBreakerOpenError(
                f"circuit breaker '{self.dep_name}' is open -- skipping call until cooldown elapses"
            )
        try:
            result = fn()
        except Exception:
            self.record_failure()
            raise
        else:
            self.record_success()
            return result
