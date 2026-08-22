"""
Tests for the post-execution verification step added to approve_action()
(2026-08-20) -- closes the update_price silent-no-op incident logged in
ops_runbook.md's 2026-08-20 entry.

Real bug: 82 approved Etsy price-update actions all recorded
status="executed" with zero errors, but independently re-checking Etsy's
real data afterward found only 11 of 82 had actually changed -- Etsy
returned 200 and silently dropped the field on the rest. Nothing in the
approval path itself ever asked "did this actually work," only "did the
HTTP call not error." Two independent GitHub/production-pattern research
passes converged on the same fix: an unconditional, code-level
re-fetch-and-diff immediately after execution and before the action is
marked executed -- not a skill a human has to remember to run.

`_verify_etsy_mutation()` is deliberately NOT wired to introduce a new
action status -- frank_hud_mockup.py's `_actionOutcomeSummary()` only
special-cases 'failed'/'rejected' and silently renders any other status
as success, which is the exact bug being closed here. A verification
mismatch must reuse the existing 'failed' status.

Checks:
  1. A verified match (Etsy's live value equals what was requested)
     still marks the action executed, unchanged from before this fix.
  2. A verification mismatch marks the action 'failed' (not a new
     status), with the real expected-vs-actual values in the error.
  3. A mismatch auto-logs an ops_runbook.md entry -- the "memory" half
     of the fix: Frank's own incident log picks this up without a human
     having to notice and write it down.
  4. update_price, update_title, update_tags, and the three state-change
     types (toggle_listing_state/publish_listing/deactivate_listing) are
     all covered by _VERIFIABLE_ETSY_FIELDS.
  5. An action_type NOT in _VERIFIABLE_ETSY_FIELDS (e.g. update_shop_section)
     is left alone -- no verification attempted, executes exactly as before
     this fix (silence here means "unverified", not "confirmed wrong").
  6. A fetch failure during verification (can't even reach Etsy to check)
     is treated as a verification failure, not silently ignored as if it
     were success.

Run: python3 tests/test_approve_action_verifies_mutation.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_verify_mutation_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "verify-mutation-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import db  # noqa: E402

# Redirect the real ops_runbook.md target for the whole module -- several tests
# below deliberately trigger a verification mismatch, which calls the real
# _append_ops_runbook_entry(). Without this, those calls write directly into the
# git-tracked data/knowledge_base/ops_runbook.md (confirmed happening in this
# exact test file before this line was added -- see the 2026-08-20 ops_runbook.md
# commit history for the cleanup). Redirect once here rather than mocking
# _append_ops_runbook_entry per-test, so a future test added to this file can't
# reintroduce the same leak by forgetting the mock.
_tmp_runbook = tempfile.NamedTemporaryFile(prefix="frank_verify_mutation_runbook_", suffix=".md", delete=False)
_tmp_runbook.close()
server._OPS_RUNBOOK_PATH = Path(_tmp_runbook.name)

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_matching_price_marks_executed():
    action_id = db.enqueue_action("update_price", "price fix", {"listing_id": 111, "price": 4.99})
    client = MagicMock()
    client.get_listing.return_value = {"price": {"amount": 499, "divisor": 100, "currency_code": "USD"}}
    with patch.object(server, "_validate_staged_action", return_value=(True, "")), \
         patch.object(server, "_execute_staged_action", return_value={"listing_id": 111}), \
         patch.object(server, "EtsyAPIClient", return_value=client):
        result = asyncio.run(server.approve_action(action_id, _token="test"))
    check(result["status"] == "executed", f"a verified matching price must mark executed, got: {result}")
    row = db.get_action(action_id)
    check(row["status"] == "executed", f"db row must also show executed, got: {row['status']}")


def test_mismatched_price_marks_failed_not_a_new_status():
    action_id = db.enqueue_action("update_price", "price fix", {"listing_id": 222, "price": 4.99})
    client = MagicMock()
    # Etsy returns 200 but the real stored price is still the old one -- the exact
    # real incident shape.
    client.get_listing.return_value = {"price": {"amount": 599, "divisor": 100, "currency_code": "USD"}}
    with patch.object(server, "_validate_staged_action", return_value=(True, "")), \
         patch.object(server, "_execute_staged_action", return_value={"listing_id": 222}), \
         patch.object(server, "EtsyAPIClient", return_value=client):
        try:
            asyncio.run(server.approve_action(action_id, _token="test"))
            check(False, "a verification mismatch must raise, not return success")
        except Exception as exc:
            check("didn't take effect" in str(exc) or "verification failed" in str(exc),
                  f"expected a verification-failure error, got: {exc}")
    row = db.get_action(action_id)
    check(row["status"] == "failed", f"a mismatch must reuse the existing 'failed' status (never a new one the UI doesn't render), got: {row['status']!r}")
    check("4.99" in str(row["result"]) and "5.99" in str(row["result"]),
          f"the failure result should carry the real expected/actual values, got: {row['result']}")


def test_mismatch_auto_logs_to_ops_runbook():
    action_id = db.enqueue_action("update_title", "title fix", {"listing_id": 333, "title": "Correct Title"})
    client = MagicMock()
    client.get_listing.return_value = {"title": "Stale Old Title"}
    logged = []
    with patch.object(server, "_validate_staged_action", return_value=(True, "")), \
         patch.object(server, "_execute_staged_action", return_value={"listing_id": 333}), \
         patch.object(server, "EtsyAPIClient", return_value=client), \
         patch.object(server, "_append_ops_runbook_entry", side_effect=lambda h, b: logged.append((h, b))):
        try:
            asyncio.run(server.approve_action(action_id, _token="test"))
        except Exception:
            pass
    check(len(logged) == 1, f"a verification mismatch must auto-log to ops_runbook.md without a human noticing, got {len(logged)} entries")
    if logged:
        heading, body = logged[0]
        check("update_title" in heading and "333" in heading, f"heading should identify the action/listing: {heading!r}")
        check("Correct Title" in body and "Stale Old Title" in body, f"body should carry expected/actual: {body!r}")


def test_verifiable_fields_cover_the_expected_action_types():
    covered = set(server._VERIFIABLE_ETSY_FIELDS.keys())
    expected = {"update_price", "update_title", "update_tags", "toggle_listing_state", "publish_listing", "deactivate_listing"}
    check(expected.issubset(covered), f"expected at least {expected} covered, got {covered}")


def test_unverifiable_action_type_executes_without_verification_call():
    action_id = db.enqueue_action("update_shop_section", "section move", {"listing_id": 444, "shop_section_id": 123})
    client = MagicMock()
    with patch.object(server, "_validate_staged_action", return_value=(True, "")), \
         patch.object(server, "_execute_staged_action", return_value={"listing_id": 444}), \
         patch.object(server, "EtsyAPIClient", return_value=client):
        result = asyncio.run(server.approve_action(action_id, _token="test"))
    check(result["status"] == "executed", f"an action_type with no verification spec must still execute normally, got: {result}")
    check(not client.get_listing.called, "an unverifiable action_type must not trigger a verification fetch at all")


def test_verification_fetch_failure_is_treated_as_failure_not_silently_ignored():
    action_id = db.enqueue_action("update_price", "price fix", {"listing_id": 555, "price": 4.99})
    client = MagicMock()
    client.get_listing.side_effect = Exception("Etsy API 0: circuit breaker open for etsy_api -- skipping call until cooldown elapses")
    with patch.object(server, "_validate_staged_action", return_value=(True, "")), \
         patch.object(server, "_execute_staged_action", return_value={"listing_id": 555}), \
         patch.object(server, "EtsyAPIClient", return_value=client):
        try:
            asyncio.run(server.approve_action(action_id, _token="test"))
            check(False, "an unfetchable verification must not silently succeed")
        except Exception:
            pass
    row = db.get_action(action_id)
    check(row["status"] == "failed", f"a fetch failure during verification must not be reported as executed, got: {row['status']!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("APPROVE-ACTION VERIFY-MUTATION TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("APPROVE-ACTION VERIFY-MUTATION TESTS OK — approve_action now independently re-fetches "
          "and diffs the real Etsy value before ever marking an action executed, closing the "
          "silent-no-op gap that let 71 of 82 real price changes report success while never "
          "actually applying, with a matching mismatch auto-logged to Frank's own incident memory.")


if __name__ == "__main__":
    run()
