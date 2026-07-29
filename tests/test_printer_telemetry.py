#!/usr/bin/env python3
"""
Bambu P1S printer telemetry endpoint tests (2026-07-29).

Covers the 4 new endpoints in main.py (POST/GET /api/printer/telemetry,
POST/GET /api/printer/camera-frame + camera.jpg): in-memory state roundtrip,
the "bridge offline" staleness threshold (never present stale device state
as if it were live), and the oversized-frame rejection. Auth itself isn't
re-tested here -- these endpoints reuse the same shared
_auth_session_or_bearer dependency every other endpoint already uses, and
this file follows this repo's documented pattern of calling route handlers
directly (bypassing FastAPI's Depends) rather than re-exercising auth.
"""
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_printer_telemetry_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "printer-telemetry-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import asyncio  # noqa: E402

import main as server  # noqa: E402
from fastapi import HTTPException  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


class _FakeRequest:
    """Only .body() is used by post_printer_camera_frame -- a full Request isn't needed."""
    def __init__(self, body: bytes):
        self._body = body

    async def body(self) -> bytes:
        return self._body


def _reset_printer_state():
    with server._printer_lock:
        server._printer_telemetry = None
        server._printer_telemetry_at = 0.0
        server._printer_frame = None
        server._printer_frame_at = 0.0


def test_status_before_any_telemetry_reports_offline_not_seen():
    _reset_printer_state()
    result = asyncio.run(server.get_printer_status(_token="test"))
    check(result["online"] is False, f"expected online=False, got {result}")
    check(result["bridge_seen"] is False, f"expected bridge_seen=False, got {result}")


def test_telemetry_post_then_get_roundtrips_fields():
    _reset_printer_state()
    payload = {"state": "RUNNING", "progress_pct": 42, "nozzle_temp": 219.4}
    post_result = asyncio.run(server.post_printer_telemetry(payload=payload, _token="test"))
    check(post_result == {"ok": True}, f"unexpected post response: {post_result}")

    status = asyncio.run(server.get_printer_status(_token="test"))
    check(status["online"] is True, f"expected online=True right after a fresh push, got {status}")
    check(status["bridge_seen"] is True, f"expected bridge_seen=True, got {status}")
    check(status["state"] == "RUNNING", f"expected state=RUNNING, got {status.get('state')}")
    check(status["progress_pct"] == 42, f"expected progress_pct=42, got {status.get('progress_pct')}")
    check(status["nozzle_temp"] == 219.4, f"expected nozzle_temp=219.4, got {status.get('nozzle_temp')}")
    check("age_seconds" in status, "expected age_seconds in a bridge_seen=True response")


def test_stale_telemetry_reports_offline_never_lies_as_live():
    """The bridge stopped pushing 40s ago (> _PRINTER_STALE_SECS=30) -- the
    HUD must show 'bridge offline', never stale numbers presented as live."""
    _reset_printer_state()
    with server._printer_lock:
        server._printer_telemetry = {"state": "RUNNING", "progress_pct": 99}
        server._printer_telemetry_at = time.time() - 40
    status = asyncio.run(server.get_printer_status(_token="test"))
    check(status["online"] is False, f"expected online=False for 40s-stale data, got {status}")
    check(status["bridge_seen"] is True, "bridge_seen should stay True -- it HAS reported before, just not recently")
    check(status.get("state") == "RUNNING", "stale data should still be returned alongside online=False for context")


def test_camera_frame_post_then_get_roundtrips_bytes():
    _reset_printer_state()
    fake_jpeg = b"\xff\xd8\xff\xe0" + b"fake jpeg bytes" * 10
    post_result = asyncio.run(
        server.post_printer_camera_frame(request=_FakeRequest(fake_jpeg), _token="test")
    )
    check(post_result == {"ok": True}, f"unexpected camera post response: {post_result}")

    response = asyncio.run(server.get_printer_camera_frame(_token="test"))
    check(response.body == fake_jpeg, "camera.jpg should return the exact bytes just posted")
    check(response.media_type == "image/jpeg", f"expected image/jpeg, got {response.media_type}")


def test_camera_frame_missing_returns_404():
    _reset_printer_state()
    try:
        asyncio.run(server.get_printer_camera_frame(_token="test"))
        check(False, "expected HTTPException(404) when no frame has ever been posted")
    except HTTPException as exc:
        check(exc.status_code == 404, f"expected 404, got {exc.status_code}")


def test_camera_frame_stale_returns_404_not_a_stale_image():
    _reset_printer_state()
    with server._printer_lock:
        server._printer_frame = b"old frame bytes"
        server._printer_frame_at = time.time() - 40
    try:
        asyncio.run(server.get_printer_camera_frame(_token="test"))
        check(False, "expected HTTPException(404) for a 40s-stale frame, never a stale image shown as live")
    except HTTPException as exc:
        check(exc.status_code == 404, f"expected 404, got {exc.status_code}")


def test_oversized_camera_frame_rejected_with_413():
    _reset_printer_state()
    oversized = b"x" * (server._PRINTER_MAX_FRAME_BYTES + 1)
    try:
        asyncio.run(server.post_printer_camera_frame(request=_FakeRequest(oversized), _token="test"))
        check(False, "expected HTTPException(413) for an oversized frame")
    except HTTPException as exc:
        check(exc.status_code == 413, f"expected 413, got {exc.status_code}")
    with server._printer_lock:
        check(server._printer_frame is None, "an oversized frame must never be stored")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
        finally:
            _reset_printer_state()
    if _failures:
        print("PRINTER TELEMETRY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRINTER TELEMETRY TESTS OK — telemetry/camera in-memory state, staleness threshold, and oversized-frame rejection all behave correctly.")


if __name__ == "__main__":
    run()
