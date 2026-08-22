#!/usr/bin/env python3
"""
Regression test for the AI-disclosure manual-step reminder on create_listing
actions (main.py / db.py, 2026-08-22).

Why this exists: Etsy's Jan 2026 AI-disclosure enforcement tightened to
require a structured "This listing uses AI generative technology" toggle +
"Designed by" (not "Made by") categorization in the listing editor.
Confirmed (developer.etsy.com + an unanswered etsy/open-api GitHub
discussion, #1340) that NO public API v3 field sets this — who_made="i_did"
and the description-text disclosure paragraph do NOT set it. Since every
listing in this shop is AI-generated content, every create_listing action
needs a human follow-up step that's easy to silently miss if it's buried in
a payload field nothing renders. `db.enqueue_action()` now prepends a short
reminder directly onto the action's `summary` — the one field every Action
Center card actually displays — and `main.py`'s create_listing validation
branch attaches the same reminder as a structured payload field. This test
locks both halves down so a future refactor can't quietly drop either one.

Run locally: python tests/test_ai_disclosure_reminder.py
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_ai_disclosure_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "ai-disclosure-test-not-a-real-secret")

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


def test_create_listing_summary_gets_manual_step_reminder():
    action_id = db.enqueue_action("create_listing", "Publish DP9999 — \"Test Planner\" — $9.99", {})
    row = db.get_action(action_id) if hasattr(db, "get_action") else None
    if row is None:
        # Fall back to list_actions if get_action isn't available under that name.
        pending = db.list_actions("pending")
        row = next((a for a in pending if a.get("id") == action_id), None)
    check(row is not None, "could not read back the enqueued action")
    if row is not None:
        summary = row.get("summary", "")
        check("AI-disclosure" in summary, f"summary missing AI-disclosure reminder: {summary!r}")
        check(summary.endswith("Publish DP9999 — \"Test Planner\" — $9.99"),
              f"original summary text was not preserved verbatim: {summary!r}")


def test_other_action_types_are_not_touched():
    action_id = db.enqueue_action("update_title", "Update title on 12345", {"listing_id": "12345", "title": "x"})
    pending = db.list_actions("pending")
    row = next((a for a in pending if a.get("id") == action_id), None)
    check(row is not None, "could not read back the enqueued update_title action")
    if row is not None:
        check("AI-disclosure" not in row.get("summary", ""),
              "update_title summary should NOT get the create_listing-only reminder")


def test_validate_staged_action_attaches_structured_field():
    # Use a real product from the catalog if one exists locally; if not,
    # this test only needs the payload dict to be inspected after the call
    # returns (mutated in place), not for validation to actually succeed --
    # a real product_id would make this network-dependent, so instead call
    # the create_listing branch's specific mutation logic path directly via
    # a payload shaped just enough to reach the trademark/_ai_disclosure
    # assignment lines before any file-existence check would fail.
    payload = {
        "product_id": "DOES_NOT_EXIST_TEST_ID",
        "listing_data": {
            "title": "Kawaii Test Planner 2026, GoodNotes iPad, Instant Download",
            "tags": ["test tag " + str(i) for i in range(13)],
            "description": "A real test description long enough to pass the gate. " * 8,
            "price": 9.99,
        },
        "photo_paths": [],
        "file_paths": [],
    }
    candidate = {"type": "create_listing", "payload": payload}
    ok, msg = server._validate_staged_action(candidate)
    # Expected to fail validation (no real files/product) -- but the
    # AI-disclosure field must already be attached by the time that failure
    # is raised, since it's assigned before the file-existence checks run.
    check("_ai_disclosure_manual_step" in payload,
          f"payload missing _ai_disclosure_manual_step field (validation result: ok={ok}, msg={msg!r})")
    if "_ai_disclosure_manual_step" in payload:
        check("API" in payload["_ai_disclosure_manual_step"] or "toggle" in payload["_ai_disclosure_manual_step"],
              "the _ai_disclosure_manual_step text doesn't look like the intended reminder")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("AI DISCLOSURE REMINDER TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("AI DISCLOSURE REMINDER TESTS OK — create_listing actions carry the manual "
          "AI-disclosure-toggle reminder in both summary and payload; other action types don't.")


if __name__ == "__main__":
    run()
