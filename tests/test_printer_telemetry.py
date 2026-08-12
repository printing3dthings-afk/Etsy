#!/usr/bin/env python3
"""
Bambu P1S printer telemetry endpoint tests (2026-07-29, extended 2026-08-11).

Covers the 4 original endpoints in main.py (POST/GET /api/printer/telemetry,
POST/GET /api/printer/camera-frame + camera.jpg): in-memory state roundtrip,
the "bridge offline" staleness threshold (never present stale device state
as if it were live), and the oversized-frame rejection. Auth itself isn't
re-tested here -- these endpoints reuse the same shared
_auth_session_or_bearer dependency every other endpoint already uses, and
this file follows this repo's documented pattern of calling route handlers
directly (bypassing FastAPI's Depends) rather than re-exercising auth.

2026-08-11 additions cover the "as close to instant as possible" +
correctness pass: _merge_printer_telemetry() (fixes Scott's "stats keep
going away and random info pops up" -- a partial MQTT delta push must
never clobber fields it didn't report), and the new /ws/printer push
channel (ticket auth via the same single-use mechanism /ws/chat uses,
immediate snapshot on connect, live broadcast on every bridge push). The
WS endpoint is exercised by calling printer_ws()/_broadcast_printer_
telemetry() directly against a minimal fake WebSocket object -- this repo
has no established pattern for a real ASGI WS protocol test (see test_
bambu_p1s_bridge.py's own docstring; neither /ws/chat nor /ws/relay are
protocol-tested either).
"""
import json
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
from fastapi import HTTPException, WebSocketDisconnect  # noqa: E402

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
    with server._printer_ws_lock:
        server._printer_ws_clients.clear()


class _FakeWebSocket:
    """Minimal stand-in for FastAPI's WebSocket -- enough surface for
    printer_ws()/_broadcast_printer_telemetry() to run against directly,
    without needing a real ASGI test client (this repo has no established
    pattern for exercising a real WS handshake -- see test_bambu_p1s_
    bridge.py and the /ws/chat, /ws/relay endpoints themselves, none of
    which are protocol-tested either)."""

    def __init__(self, query_params: dict | None = None, fail_send: bool = False):
        self.query_params = query_params or {}
        self.accepted = False
        self.closed_code = None
        self.sent: list[str] = []
        self._fail_send = fail_send

    async def accept(self):
        self.accepted = True

    async def close(self, code: int | None = None):
        self.closed_code = code

    async def send_text(self, text: str):
        if self._fail_send:
            raise ConnectionError("simulated dead socket")
        self.sent.append(text)

    async def receive_text(self):
        # This channel is server->client only (see printer_ws()'s own
        # docstring) -- the fake client never sends anything, so the very
        # next receive is always treated as a disconnect, exercising the
        # real accept -> send -> disconnect -> cleanup path in one call.
        raise WebSocketDisconnect()


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
    """The bridge stopped pushing 120s ago (> _PRINTER_STALE_SECS=90) -- the
    HUD must show 'bridge offline', never stale numbers presented as live."""
    _reset_printer_state()
    with server._printer_lock:
        server._printer_telemetry = {"state": "RUNNING", "progress_pct": 99}
        server._printer_telemetry_at = time.time() - 120
    status = asyncio.run(server.get_printer_status(_token="test"))
    check(status["online"] is False, f"expected online=False for 120s-stale data, got {status}")
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


# ── Merge, not overwrite (2026-08-11 fix for "stats keep going away") ───────

def test_merge_keeps_existing_fields_not_present_in_new_push():
    existing = {"state": "RUNNING", "nozzle_temp": 210.0, "bed_temp": 60.0}
    incoming = {"bed_temp": 61.0}  # e.g. a partial delta that only reported bed temp
    merged = server._merge_printer_telemetry(existing, incoming)
    check(merged["state"] == "RUNNING", f"got {merged}")
    check(merged["nozzle_temp"] == 210.0, f"got {merged}")
    check(merged["bed_temp"] == 61.0, "the field actually reported this time must update")


def test_merge_skips_none_values_old_bridge_compat():
    """The currently-deployed bridge (before Scott updates it) always sends
    every key, using None for "this delta didn't mention it" -- the merge
    must be safe against that shape too, not just the fixed bridge's."""
    existing = {"state": "RUNNING"}
    incoming = {"state": None, "bed_temp": 60.0}
    merged = server._merge_printer_telemetry(existing, incoming)
    check(merged["state"] == "RUNNING", "a None value must never clobber a known-good value")
    check(merged["bed_temp"] == 60.0, f"got {merged}")


def test_merge_skips_empty_ams_list_old_bridge_compat():
    existing = {"ams": [{"id": "0", "material": "PLA"}]}
    incoming = {"ams": []}
    merged = server._merge_printer_telemetry(existing, incoming)
    check(merged["ams"] == [{"id": "0", "material": "PLA"}],
          f"an empty ams list from a delta that didn't mention AMS must not clear known trays, got {merged}")


def test_merge_accepts_real_nonempty_ams_update():
    existing = {"ams": [{"id": "0", "material": "PLA"}]}
    incoming = {"ams": [{"id": "0", "material": "PETG"}]}
    merged = server._merge_printer_telemetry(existing, incoming)
    check(merged["ams"][0]["material"] == "PETG", f"a real, non-empty ams update must apply, got {merged}")


def test_merge_from_no_prior_state():
    merged = server._merge_printer_telemetry(None, {"state": "RUNNING", "bed_temp": None})
    check(merged == {"state": "RUNNING"}, f"got {merged}")


def test_post_telemetry_endpoint_merges_across_two_pushes():
    """End-to-end reproduction of the exact live production bug found by
    hand: first push has full data, second push is a partial delta, the
    dashboard must still show the fields the delta didn't mention."""
    _reset_printer_state()
    asyncio.run(server.post_printer_telemetry(
        payload={"state": "RUNNING", "nozzle_temp": 210.0, "bed_temp": 60.0}, _token="test"))
    asyncio.run(server.post_printer_telemetry(payload={"bed_temp": 61.0}, _token="test"))
    status = asyncio.run(server.get_printer_status(_token="test"))
    check(status["state"] == "RUNNING", f"a partial delta must not erase state, got {status}")
    check(status["nozzle_temp"] == 210.0, f"a partial delta must not erase nozzle_temp, got {status}")
    check(status["bed_temp"] == 61.0, f"got {status}")


# ── /ws/printer push channel (2026-08-11) ────────────────────────────────────

def test_printer_ws_rejects_missing_ticket():
    _reset_printer_state()
    ws = _FakeWebSocket(query_params={})
    asyncio.run(server.printer_ws(ws))
    check(ws.closed_code == 4001, f"got {ws.closed_code}")
    check(not ws.accepted, "must not accept without a valid ticket")


def test_printer_ws_rejects_invalid_ticket():
    _reset_printer_state()
    ws = _FakeWebSocket(query_params={"ticket": "not-a-real-ticket"})
    asyncio.run(server.printer_ws(ws))
    check(ws.closed_code == 4001, f"got {ws.closed_code}")
    check(not ws.accepted, "must not accept with an invalid ticket")


def test_printer_ws_accepts_valid_ticket_sends_snapshot_then_cleans_up():
    _reset_printer_state()
    with server._printer_lock:
        server._printer_telemetry = {"state": "RUNNING"}
        server._printer_telemetry_at = time.time()
    ticket = server._new_ws_ticket()
    ws = _FakeWebSocket(query_params={"ticket": ticket})
    asyncio.run(server.printer_ws(ws))
    check(ws.accepted, "must accept with a valid ticket")
    check(len(ws.sent) == 1, f"expected exactly 1 initial snapshot push, got {ws.sent}")
    payload = json.loads(ws.sent[0])
    check(payload.get("state") == "RUNNING", f"got {payload}")
    check(ws not in server._printer_ws_clients, "must be pruned from the tracked client set after disconnect")


def test_printer_ws_ticket_is_single_use():
    _reset_printer_state()
    ticket = server._new_ws_ticket()
    ws1 = _FakeWebSocket(query_params={"ticket": ticket})
    asyncio.run(server.printer_ws(ws1))
    check(ws1.accepted, "the first connect with a fresh ticket must succeed")

    ws2 = _FakeWebSocket(query_params={"ticket": ticket})
    asyncio.run(server.printer_ws(ws2))
    check(not ws2.accepted, "a already-spent ticket must not authenticate a second connection")
    check(ws2.closed_code == 4001, f"got {ws2.closed_code}")


def test_broadcast_sends_to_all_connected_clients():
    _reset_printer_state()
    with server._printer_lock:
        server._printer_telemetry = {"state": "RUNNING"}
        server._printer_telemetry_at = time.time()
    ws1, ws2 = _FakeWebSocket(), _FakeWebSocket()
    with server._printer_ws_lock:
        server._printer_ws_clients.add(ws1)
        server._printer_ws_clients.add(ws2)
    asyncio.run(server._broadcast_printer_telemetry())
    check(len(ws1.sent) == 1, f"got {ws1.sent}")
    check(len(ws2.sent) == 1, f"got {ws2.sent}")
    check(json.loads(ws1.sent[0]).get("state") == "RUNNING", f"got {ws1.sent}")


def test_broadcast_prunes_dead_clients_without_raising():
    _reset_printer_state()
    with server._printer_lock:
        server._printer_telemetry = {"state": "RUNNING"}
        server._printer_telemetry_at = time.time()
    good_ws = _FakeWebSocket()
    dead_ws = _FakeWebSocket(fail_send=True)
    with server._printer_ws_lock:
        server._printer_ws_clients.add(good_ws)
        server._printer_ws_clients.add(dead_ws)
    asyncio.run(server._broadcast_printer_telemetry())  # must not raise despite dead_ws failing
    check(len(good_ws.sent) == 1, f"got {good_ws.sent}")
    check(dead_ws not in server._printer_ws_clients, "a client whose send fails must be pruned")
    check(good_ws in server._printer_ws_clients, "a healthy client must stay tracked")


def test_broadcast_noop_with_no_connected_clients():
    _reset_printer_state()
    with server._printer_lock:
        server._printer_telemetry = {"state": "RUNNING"}
        server._printer_telemetry_at = time.time()
    asyncio.run(server._broadcast_printer_telemetry())  # must not raise with zero clients


def test_post_telemetry_broadcasts_to_connected_clients():
    _reset_printer_state()
    ws = _FakeWebSocket()
    with server._printer_ws_lock:
        server._printer_ws_clients.add(ws)
    asyncio.run(server.post_printer_telemetry(payload={"state": "RUNNING"}, _token="test"))
    check(len(ws.sent) == 1, f"a bridge push must immediately broadcast to connected HUD clients, got {ws.sent}")


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
    print("PRINTER TELEMETRY TESTS OK — telemetry/camera in-memory state, staleness threshold, and oversized-frame "
          "rejection all behave correctly; _merge_printer_telemetry() never lets a partial push clobber fields it "
          "didn't report; /ws/printer authenticates via a single-use ticket, pushes an immediate snapshot on "
          "connect, and every bridge push broadcasts live to connected HUD clients.")


if __name__ == "__main__":
    run()
