"""
Tests for the Etsy order webhook receiver (2026-08-22) --
POST /api/webhooks/etsy and its HMAC signature verification.

Checks:
  1. _verify_etsy_webhook_signature() accepts a correctly-computed
     signature and rejects a tampered body, a wrong secret, a stale
     timestamp, and a missing header -- using the exact scheme documented
     at developers.etsy.com/documentation/essentials/webhooks/ (HMAC-SHA256
     over "{id}.{timestamp}.{raw_body}", secret is base64 after stripping
     "whsec_").
  2. It also accepts a Svix-style "v1,<sig>" token, not just a bare
     signature, since Etsy's own docs didn't specify which shape the
     header uses.
  3. post_etsy_webhook() (the real route function) rejects a bad signature
     with 401 and logs a valid one via db.log_activity with the real
     event_type as action_type.

Run: python tests/test_etsy_webhook.py
"""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_etsywebhook_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "etsywebhook-test-not-a-real-secret")

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


SECRET_RAW = base64.b64encode(b"a-real-32-byte-secret-key-here!").decode()
SECRET = "whsec_" + SECRET_RAW
WEBHOOK_ID = "msg_test123"


def _sign(raw_body: bytes, ts: str, secret_b64: str = SECRET_RAW) -> str:
    signed_content = f"{WEBHOOK_ID}.{ts}.".encode() + raw_body
    secret_bytes = base64.b64decode(secret_b64)
    return base64.b64encode(hmac.new(secret_bytes, signed_content, hashlib.sha256).digest()).decode()


def test_valid_signature_accepted():
    os.environ["ETSY_WEBHOOK_SECRET"] = SECRET
    body = json.dumps({"event_type": "order.paid", "shop_id": "1"}).encode()
    ts = str(int(time.time()))
    sig = _sign(body, ts)
    ok, reason = server._verify_etsy_webhook_signature(body, WEBHOOK_ID, ts, sig)
    check(ok, f"expected a correctly-signed request to verify, got reason={reason!r}")


def test_v1_prefixed_signature_accepted():
    os.environ["ETSY_WEBHOOK_SECRET"] = SECRET
    body = json.dumps({"event_type": "order.paid"}).encode()
    ts = str(int(time.time()))
    sig = "v1," + _sign(body, ts)
    ok, _ = server._verify_etsy_webhook_signature(body, WEBHOOK_ID, ts, sig)
    check(ok, "expected a 'v1,<sig>' formatted header to verify")


def test_tampered_body_rejected():
    os.environ["ETSY_WEBHOOK_SECRET"] = SECRET
    body = json.dumps({"event_type": "order.paid"}).encode()
    ts = str(int(time.time()))
    sig = _sign(body, ts)
    tampered = json.dumps({"event_type": "order.canceled"}).encode()
    ok, reason = server._verify_etsy_webhook_signature(tampered, WEBHOOK_ID, ts, sig)
    check(not ok, "expected a tampered body to fail signature verification")
    check(reason == "signature mismatch", f"expected 'signature mismatch', got {reason!r}")


def test_wrong_secret_rejected():
    os.environ["ETSY_WEBHOOK_SECRET"] = SECRET
    body = json.dumps({"event_type": "order.paid"}).encode()
    ts = str(int(time.time()))
    wrong_secret_b64 = base64.b64encode(b"a-totally-different-secret-key!!").decode()
    sig = _sign(body, ts, secret_b64=wrong_secret_b64)
    ok, reason = server._verify_etsy_webhook_signature(body, WEBHOOK_ID, ts, sig)
    check(not ok, "expected a signature made with the wrong secret to fail")


def test_stale_timestamp_rejected():
    os.environ["ETSY_WEBHOOK_SECRET"] = SECRET
    body = json.dumps({"event_type": "order.paid"}).encode()
    old_ts = str(int(time.time()) - 999)
    sig = _sign(body, old_ts)
    ok, reason = server._verify_etsy_webhook_signature(body, WEBHOOK_ID, old_ts, sig)
    check(not ok, "expected a 999s-old timestamp to be rejected as replay")
    check("replay" in reason, f"expected a replay-window reason, got {reason!r}")


def test_missing_secret_rejected():
    os.environ.pop("ETSY_WEBHOOK_SECRET", None)
    body = json.dumps({"event_type": "order.paid"}).encode()
    ts = str(int(time.time()))
    ok, reason = server._verify_etsy_webhook_signature(body, WEBHOOK_ID, ts, "anything")
    check(not ok, "expected verification to fail with no ETSY_WEBHOOK_SECRET configured")
    check("not configured" in reason, f"expected a 'not configured' reason, got {reason!r}")


def test_route_rejects_bad_signature_with_401():
    os.environ["ETSY_WEBHOOK_SECRET"] = SECRET
    body = json.dumps({"event_type": "order.paid"}).encode()
    req = MagicMock()
    req.headers = {"webhook-id": WEBHOOK_ID, "webhook-timestamp": str(int(time.time())), "webhook-signature": "bogus"}

    async def _body():
        return body

    req.body = _body

    from fastapi import HTTPException
    try:
        asyncio.run(server.post_etsy_webhook(req))
        check(False, "expected post_etsy_webhook to raise HTTPException for a bad signature")
    except HTTPException as exc:
        check(exc.status_code == 401, f"expected 401, got {exc.status_code}")


def test_route_logs_valid_event():
    os.environ["ETSY_WEBHOOK_SECRET"] = SECRET
    body = json.dumps({
        "event_type": "order.delivered",
        "shop_id": "999",
        "resource_url": "https://api.etsy.com/v3/application/shops/999/receipts/123",
    }).encode()
    ts = str(int(time.time()))
    sig = _sign(body, ts)
    req = MagicMock()
    req.headers = {"webhook-id": WEBHOOK_ID, "webhook-timestamp": ts, "webhook-signature": sig}

    async def _body():
        return body

    req.body = _body

    before = len(db.list_activity(limit=1000, action_type="order.delivered"))
    result = asyncio.run(server.post_etsy_webhook(req))
    check(result == {"ok": True}, f"expected {{'ok': True}}, got {result!r}")
    after = db.list_activity(limit=1000, action_type="order.delivered")
    check(len(after) == before + 1, "expected exactly one new order.delivered activity_log row")
    check(after[0]["actor"] == "etsy_webhook", f"expected actor='etsy_webhook', got {after[0]['actor']!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("ETSY WEBHOOK TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("ETSY WEBHOOK TESTS OK -- HMAC signature verification (valid/tampered/wrong-secret/replay/missing-secret) "
          "and the real route's accept/reject + activity-log behavior all work as documented.")


if __name__ == "__main__":
    run()
