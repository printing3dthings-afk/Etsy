"""Reusable goal-verification loop (generate → verify against the goal → retry).

This generalises the pattern that already lives, hand-rolled, inside
`tools/listing_photo_pipeline.py::generate_verified_photo`: produce a candidate,
judge it against the *actual goal* with an independent checker, and if it falls
short, feed the specific failures back into the next attempt — stopping only when
it passes or attempts run out.

WHY THIS IS SEPARATE FROM `tools/resilience.py`:
  - resilience.retry_with_backoff / CircuitBreaker retry *transient* failures
    (network, 429, 5xx). The call itself failed.
  - run_until_goal retries *quality* failures: the call SUCCEEDED but the output
    doesn't meet the goal (wrong text on a mockup, a title over 70 chars, a video
    that doesn't match the prompt). Nothing threw — the result is just wrong.
  They compose: `generate` may use retry_with_backoff internally for the network,
  while run_until_goal owns the "is this actually good enough?" loop on top.

THE ONE NON-NEGOTIABLE RULE: never fabricate success. `passed` is True only when a
verify() call actually returned pass=True. On exhaustion the loop returns
passed=False with the last issues — the caller must treat that as a real failure
(surface it, fall back, or block), never as done. This is the code-level
enforcement of the CLAUDE.md "compare to the goal before saying complete" and
"never lie to the customer" rules.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

__all__ = ["LoopResult", "run_until_goal", "format_correction"]


@dataclass
class LoopResult:
    """Outcome of a goal loop.

    passed:   True ONLY if a verify() returned pass=True. Never fabricated.
    output:   the candidate that passed, or None if the loop exhausted.
    attempts: how many generate+verify cycles ran.
    issues:   the unresolved issues from the final attempt (empty on pass).
    history:  per-attempt audit trail: {attempt, stage, pass?, issues}.
    """
    passed: bool
    output: Any = None
    attempts: int = 0
    issues: list = field(default_factory=list)
    history: list = field(default_factory=list)


def format_correction(issues: list) -> str:
    """Render verifier issues into a corrective instruction block appended to the
    next generation prompt. Mirrors the wording generate_verified_photo used so
    behaviour is unchanged when it adopts this loop."""
    if not issues:
        return ""
    return "\n\nPREVIOUS ATTEMPT HAD THESE ERRORS — FIX THEM:\n- " + "\n- ".join(
        str(i) for i in issues
    )


def run_until_goal(
    generate: Callable[[str], Any],
    verify: Callable[[Any], dict],
    *,
    max_attempts: int = 3,
    on_reject: Optional[Callable[[int, Any, list], None]] = None,
    on_attempt: Optional[Callable[[int, Any, dict], None]] = None,
    format_correction_fn: Callable[[list], str] = format_correction,
) -> LoopResult:
    """Generate a candidate, verify it against the goal, and retry with feedback
    until it passes or `max_attempts` is reached.

    Args:
        generate(correction: str) -> candidate
            Produces one candidate. `correction` is "" on the first attempt and,
            on later attempts, a text block describing the previous attempt's
            issues (from format_correction_fn) to fix. If generate() raises, the
            error is recorded and the loop retries with the SAME correction as the
            prior attempt (a generation crash is not a prompt-quality problem, so
            we don't pollute the prompt with it) — matching the original
            hand-rolled behaviour.
        verify(candidate) -> {"pass": bool, "issues": [str, ...]}
            Judges the candidate against the goal. A normal quality failure must
            be returned as {"pass": False, "issues": [...]}, NOT raised. If
            verify() raises, that's captured as an issue and retried.
        max_attempts: hard cap on generate+verify cycles (>=1).
        on_reject(attempt, candidate, issues): optional side effect for a failed
            attempt — e.g. save the rejected artifact for audit.
        on_attempt(attempt, candidate, verdict): optional observer for every
            verified attempt (pass or fail) — e.g. progress logging.

    Returns:
        LoopResult. passed=True only on a real verify pass; otherwise passed=False
        with the final issues and a full per-attempt history.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    issues: list = []
    history: list = []
    correction = ""

    for attempt in range(1, max_attempts + 1):
        # ---- generate -------------------------------------------------------
        try:
            candidate = generate(correction)
        except Exception as exc:  # transient/hard generation failure
            gen_issues = [f"generation error: {exc}"]
            history.append({"attempt": attempt, "stage": "generate",
                            "pass": False, "issues": gen_issues})
            issues = gen_issues
            # Do NOT fold a generation crash into `correction`: retry as-is.
            continue

        # ---- verify ---------------------------------------------------------
        try:
            verdict = verify(candidate)
        except Exception as exc:
            ver_issues = [f"verification error: {exc}"]
            history.append({"attempt": attempt, "stage": "verify",
                            "pass": False, "issues": ver_issues})
            issues = ver_issues
            if on_reject:
                on_reject(attempt, candidate, ver_issues)
            correction = format_correction_fn(ver_issues)
            continue

        passed = bool(verdict.get("pass"))
        issues = list(verdict.get("issues", []) or [])
        history.append({"attempt": attempt, "stage": "verify",
                        "pass": passed, "issues": issues})
        if on_attempt:
            on_attempt(attempt, candidate, verdict)

        if passed:
            return LoopResult(True, candidate, attempt, [], history)

        if on_reject:
            on_reject(attempt, candidate, issues)
        correction = format_correction_fn(issues)

    return LoopResult(False, None, max_attempts, issues, history)
