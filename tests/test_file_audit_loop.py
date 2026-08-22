"""
Tests for the 2026-07-21 fix: the live-Etsy file-integrity audit
(tools/audit_product_files.py's audit()) was fully built -- the function
itself, the /api/alerts "product_file_integrity" critical-alert source, and
the Products-screen per-card file_audit badge all shipped in earlier rounds
-- but NOTHING ever scheduled it to actually run in production. It only ran
if someone manually typed `python tools/audit_product_files.py` from a
machine with real Etsy credentials, which never happened live. So
data/file_audit_report.json never existed, _file_audit_report() always
returned None, and every consumer of that data was silently dead from launch.

Fix: a new `_file_audit_loop()` background loop (registered alongside the
other 7 real loops) runs the audit once a day via `_run_loop_iteration()`
(same shared retry/backoff/heartbeat policy every other loop uses) and
writes the report atomically. A new POST /api/file-audit/run lets Scott
force an immediate refresh from the dashboard too, matching the existing
/api/calendar-tasks/run and /api/brief/run manual-trigger pattern.

Checks:
  1. _file_audit_iteration() writes the report atomically (via .tmp + replace)
     to the path tools/audit_product_files.py's own _report_path() expects,
     with the shape _file_audit_report()/_product_file_integrity_alerts()
     already know how to read.
  2. _file_audit_loop, driven through exactly one iteration, reports "error"
     when genuinely_missing is non-empty (the real compliance-risk case),
     "warning" when the audit itself hit skips (API/auth errors) but nothing
     is genuinely missing, and "ok" on a fully clean run.
  3. POST /api/file-audit/run requires the X-App-Token header and returns a
     summary shape; a genuinely_missing hit is reflected in the response.

Run: python tests/test_file_audit_loop.py
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_fileauditloop_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "fileauditloop-test-not-a-real-secret")
os.environ["ENABLE_TEST_LOGIN"] = "true"
os.environ["TEST_LOGIN_USERNAME"] = "fileauditlooptest"
os.environ["TEST_LOGIN_PASSWORD"] = "FileAuditLoopTest!2026Only"

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import db  # noqa: E402
import audit_product_files  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _heartbeat(name: str) -> dict | None:
    for hb in db.list_agent_heartbeats():
        if hb["name"] == name:
            return hb
    return None


def _fake_audit_result(verified_live=None, genuinely_missing=None, skipped=None) -> dict:
    return {
        "verified_live": verified_live or [],
        "genuinely_missing": genuinely_missing or [],
        "skipped": skipped or [],
    }


def _run_loop_one_iteration(loop_coro_fn, sleeps_before_loop_body: int = 0):
    call_count = {"n": 0}

    async def _fake_sleep(_secs):
        call_count["n"] += 1
        if call_count["n"] > sleeps_before_loop_body:
            raise asyncio.CancelledError("stop after one iteration")

    with patch("asyncio.sleep", _fake_sleep):
        try:
            asyncio.run(loop_coro_fn())
        except asyncio.CancelledError:
            pass


def test_iteration_writes_report_atomically_to_the_expected_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "file_audit_report.json"
        with patch.object(audit_product_files, "audit",
                           return_value=_fake_audit_result(verified_live=[{"product_id": "DP1"}])), \
             patch.object(audit_product_files, "_report_path", return_value=report_path):
            result = asyncio.run(server._file_audit_iteration())

        check(report_path.exists(), "the report file must exist after one iteration")
        on_disk = json.loads(report_path.read_text())
        check(on_disk["verified_live"] == [{"product_id": "DP1"}],
              f"the written report must match the audit result, got: {on_disk}")
        check("audited_at" in on_disk, "the report must be stamped with audited_at")
        check(result["verified_live"] == [{"product_id": "DP1"}], "the returned result should match too")
        # no leftover .tmp file
        check(not report_path.with_suffix(".json.tmp").exists(),
              "the atomic-write temp file must not be left behind")


def test_loop_reports_error_when_genuinely_missing_is_non_empty():
    fake = _fake_audit_result(genuinely_missing=[{"product_id": "DP2", "listing_id": 2}])
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "file_audit_report.json"
        with patch.object(audit_product_files, "audit", return_value=fake), \
             patch.object(audit_product_files, "_report_path", return_value=report_path), \
             patch.object(server._anthropic_breaker, "allow_request", return_value=True):
            _run_loop_one_iteration(server._file_audit_loop, sleeps_before_loop_body=1)

    hb = _heartbeat("file_audit")
    check(hb is not None, "file_audit heartbeat should exist after one iteration")
    check(hb["status"] == "error",
          f"a genuinely-missing listing is the real compliance risk -- must report 'error', got: {hb['status']!r}")
    check("genuinely_missing:1" in hb["detail"], f"expected the count in the detail, got: {hb['detail']!r}")


def test_loop_reports_warning_when_only_skips_and_nothing_missing():
    fake = _fake_audit_result(skipped=[{"product_id": "DP3", "reason": "401"}])
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "file_audit_report.json"
        with patch.object(audit_product_files, "audit", return_value=fake), \
             patch.object(audit_product_files, "_report_path", return_value=report_path), \
             patch.object(server._anthropic_breaker, "allow_request", return_value=True):
            _run_loop_one_iteration(server._file_audit_loop, sleeps_before_loop_body=1)

    hb = _heartbeat("file_audit")
    check(hb["status"] == "warning",
          f"skips with nothing genuinely missing should be 'warning' (couldn't fully verify), got: {hb['status']!r}")


def test_loop_reports_ok_on_a_fully_clean_run():
    fake = _fake_audit_result(verified_live=[{"product_id": "DP4"}])
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "file_audit_report.json"
        with patch.object(audit_product_files, "audit", return_value=fake), \
             patch.object(audit_product_files, "_report_path", return_value=report_path), \
             patch.object(server._anthropic_breaker, "allow_request", return_value=True):
            _run_loop_one_iteration(server._file_audit_loop, sleeps_before_loop_body=1)

    hb = _heartbeat("file_audit")
    check(hb["status"] == "ok", f"a fully clean run should be 'ok', got: {hb['status']!r}")


def _logged_in_client() -> TestClient:
    c = TestClient(server.app, base_url="https://testserver")
    r = c.post("/login", data={
        "username": os.environ["TEST_LOGIN_USERNAME"],
        "password": os.environ["TEST_LOGIN_PASSWORD"],
        "next": "/frank",
    }, follow_redirects=False)
    check(r.status_code in (302, 303), f"login should redirect, got {r.status_code}")
    return c


def test_manual_endpoint_requires_app_token():
    resp = _logged_in_client().post("/api/file-audit/run")
    check(resp.status_code == 401, f"missing X-App-Token must 401, got {resp.status_code}")


def test_manual_endpoint_returns_summary_and_reflects_genuinely_missing():
    fake = _fake_audit_result(
        verified_live=[{"product_id": "DP5"}],
        genuinely_missing=[{"product_id": "DP6", "listing_id": 6}],
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "file_audit_report.json"
        with patch.object(audit_product_files, "audit", return_value=fake), \
             patch.object(audit_product_files, "_report_path", return_value=report_path):
            resp = _logged_in_client().post("/api/file-audit/run", headers={"X-App-Token": server.APP_TOKEN})
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    check(body.get("verified_live") == 1, f"expected verified_live count 1, got: {body}")
    check(body.get("genuinely_missing") == 1, f"expected genuinely_missing count 1, got: {body}")
    check("audited_at" in body, f"expected audited_at in response, got: {body}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FILE AUDIT LOOP TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FILE AUDIT LOOP TESTS OK — the live-Etsy file-integrity audit is now actually scheduled "
          "(daily loop + manual trigger endpoint), writes its report atomically, and reports "
          "'error'/'warning'/'ok' heartbeat status correctly based on what the audit found.")


if __name__ == "__main__":
    run()
