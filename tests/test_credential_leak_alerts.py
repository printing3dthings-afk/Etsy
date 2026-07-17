"""
Tests for the standing Etsy/TikTok credential-leak alerts (Frank upgrade Wave 1,
reliability item 5, 2026-07-17). Both credentials were confirmed leaked and still
unrotated across weeks of ops_runbook entries, previously surfaced only as a
one-off todo Scott could dismiss/scroll past once. GET /api/alerts now includes a
standing "critical" alert for each, present every session until a settings flag
(etsy_credential_leak_resolved / tiktok_credential_leak_resolved) confirms
rotation happened -- gated so clearing it is a one-line db.set_setting() call,
not a code change.

Self-contained TestClient-against-the-real-app pattern, same as
tests/test_produce_qc.py. Run: python tests/test_credential_leak_alerts.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_credleak_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "credleak-test-not-a-real-secret")
os.environ["ENABLE_TEST_LOGIN"] = "true"
os.environ["TEST_LOGIN_USERNAME"] = "credleaktest"
os.environ["TEST_LOGIN_PASSWORD"] = "CredLeakTest!2026Only"

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import db  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _logged_in_client() -> TestClient:
    c = TestClient(server.app, base_url="https://testserver")
    r = c.post("/login", data={
        "username": os.environ["TEST_LOGIN_USERNAME"],
        "password": os.environ["TEST_LOGIN_PASSWORD"],
        "next": "/frank",
    }, follow_redirects=False)
    check(r.status_code in (302, 303), f"login should redirect, got {r.status_code}")
    return c


def _alert_titles(data: dict) -> list[str]:
    return [a["title"] for a in data.get("alerts", [])]


def test_both_leaks_present_by_default():
    db.set_setting("etsy_credential_leak_resolved", None)
    db.set_setting("tiktok_credential_leak_resolved", None)
    c = _logged_in_client()
    r = c.get("/api/alerts")
    check(r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:200]}")
    titles = _alert_titles(r.json())
    check(any("Etsy Client ID/Secret leaked" in t for t in titles),
          f"expected the Etsy leak alert present by default, got {titles}")
    check(any("TikTok Client Key/Secret leaked" in t for t in titles),
          f"expected the TikTok leak alert present by default, got {titles}")
    etsy_alert = next(a for a in r.json()["alerts"] if "Etsy Client ID/Secret leaked" in a["title"])
    check(etsy_alert["severity"] == "critical", f"expected critical severity, got {etsy_alert['severity']}")


def test_etsy_leak_clears_independently_when_resolved():
    db.set_setting("etsy_credential_leak_resolved", "true")
    db.set_setting("tiktok_credential_leak_resolved", None)
    c = _logged_in_client()
    r = c.get("/api/alerts")
    titles = _alert_titles(r.json())
    check(not any("Etsy Client ID/Secret leaked" in t for t in titles),
          f"Etsy leak alert should be cleared once resolved, got {titles}")
    check(any("TikTok Client Key/Secret leaked" in t for t in titles),
          f"TikTok leak alert should still be present (resolved independently), got {titles}")
    db.set_setting("etsy_credential_leak_resolved", None)  # restore for other tests


def test_both_leaks_clear_when_both_resolved():
    db.set_setting("etsy_credential_leak_resolved", "true")
    db.set_setting("tiktok_credential_leak_resolved", "true")
    c = _logged_in_client()
    r = c.get("/api/alerts")
    titles = _alert_titles(r.json())
    check(not any("leaked" in t.lower() for t in titles),
          f"both leak alerts should be cleared once both resolved, got {titles}")
    db.set_setting("etsy_credential_leak_resolved", None)  # restore for other tests
    db.set_setting("tiktok_credential_leak_resolved", None)


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("CREDENTIAL-LEAK ALERT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("CREDENTIAL-LEAK ALERT TESTS OK — both standing alerts present by default, "
          "each clears independently once its settings flag confirms rotation.")


if __name__ == "__main__":
    run()
