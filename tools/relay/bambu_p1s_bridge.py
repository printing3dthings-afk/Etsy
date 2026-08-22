#!/usr/bin/env python3
"""
Bambu Lab P1S Printer Bridge — local telemetry relay for Frank

Frank (tools/api_server/main.py) runs as a cloud service on Railway and has
no route to Scott's home network, so it can never open a direct MQTT
connection to the printer. This script is the other end: a small standalone
process that runs ON Scott's own LAN (same machine/network as the printer),
talks to the P1S over its local MQTT broker, and pushes a telemetry
snapshot up to Frank every few seconds via a plain authenticated HTTP POST.
Same deployment shape as frank_relay.py in this same directory — a separate,
"dumb" process that owns no decisions, just reports what it sees.

Config (env vars, or a `.env` file next to this script — shared with
frank_relay.py's own `.env` if you already run that):
  BAMBU_IP              Printer's local IP address (Bambu Handy app -> Settings
                         -> Device -> IP, or your router's device list)
  BAMBU_ACCESS_CODE     LAN-mode Access Code (printer touchscreen -> Settings
                         -> Network -> Access Code)
  BAMBU_SERIAL          Printer serial number (printer touchscreen -> Settings
                         -> Device, or the sticker on the unit)
  FRANK_API_BASE        e.g. https://etsy-production-b2f1.up.railway.app
                         (use http://localhost:8000 for a local Frank server)
  APP_SECRET_TOKEN      same token frank_relay.py / the mobile app use

Run:
  pip install -r tools/relay/bambu_requirements.txt
  python tools/relay/bambu_p1s_bridge.py

Verify the MQTT handshake alone (no push to Frank, prints one parsed report
and exits):
  python tools/relay/bambu_p1s_bridge.py --test

Camera relay pushes a JPEG snapshot to Frank every time the printer sends
one (not true video streaming, but frequent enough to feel live). It uses
the P1S's local camera port, a protocol Bambu Lab has never officially
published; see the "Camera relay" section further down for exactly what was
independently verified before this shipped, and how. Run `--test-camera` to
smoke-test the camera connection alone. Pass `--no-camera` to run telemetry
only.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import ssl
import struct
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

# paho-mqtt is only needed for the telemetry (MQTT) half of this bridge -- the
# camera relay is a plain TLS socket (see "Camera relay" section below) and has
# no dependency on it. Imported lazily inside _build_client() rather than at
# module level so `--test-camera`/`--no-camera` runs, and anything importing
# this module to test its pure functions, don't need it installed.
# ── Config ───────────────────────────────────────────────────────────────────

_HERE = Path(__file__).resolve().parent
_env_file = _HERE / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

BAMBU_IP = os.getenv("BAMBU_IP", "").strip()
BAMBU_ACCESS_CODE = os.getenv("BAMBU_ACCESS_CODE", "").strip()
BAMBU_SERIAL = os.getenv("BAMBU_SERIAL", "").strip()
FRANK_API_BASE = os.getenv("FRANK_API_BASE", "http://localhost:8000").strip().rstrip("/")
APP_TOKEN = os.getenv("APP_SECRET_TOKEN", "").strip()

MQTT_PORT = 8883
# 2026-08-11: was 3s. Real Bambu MQTT delta cadence while printing is close to
# 1/sec, so a 3s debounce was discarding roughly two-thirds of the update
# opportunities the printer already provides for free. Frank's backend now
# merges pushes instead of overwriting (see _merge_printer_telemetry() in
# main.py), so pushing more often no longer risks flickering fields to null
# either -- there's no longer a correctness reason to hold this higher.
PUSH_MIN_INTERVAL_SECS = 1  # debounce -- the printer can send several report deltas/second
RECONNECT_BACKOFF_SECS = 5

# Community-documented (not Bambu-official) mapping -- printed alongside the raw
# value in telemetry so a wrong guess here is visible, not silently trusted.
_SPEED_MODE_BY_LEVEL = {1: "Silent", 2: "Standard", 3: "Sport", 4: "Ludicrous"}

_last_push_at = 0.0
_push_lock = threading.Lock()


def _post_json(path: str, payload: dict) -> bool:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        FRANK_API_BASE + path, data=body, method="POST",
        headers={"Authorization": f"Bearer {APP_TOKEN}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except urllib.error.URLError as exc:
        print(f"[bambu-bridge] push to {path} failed: {exc}", flush=True)
        return False


def _post_bytes(path: str, body: bytes, content_type: str) -> bool:
    req = urllib.request.Request(
        FRANK_API_BASE + path, data=body, method="POST",
        headers={"Authorization": f"Bearer {APP_TOKEN}", "Content-Type": content_type},
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except urllib.error.URLError as exc:
        print(f"[bambu-bridge] camera frame push failed: {exc}", flush=True)
        return False


# (out_key, raw_key) for every scalar field the HUD shows -- shared by
# _parse_report() below.
_SCALAR_FIELDS = [
    ("state", "gcode_state"),
    ("progress_pct", "mc_percent"),
    ("layer_current", "layer_num"),
    ("layer_total", "total_layer_num"),
    ("remaining_minutes", "mc_remaining_time"),
    ("nozzle_temp", "nozzle_temper"),
    ("nozzle_target", "nozzle_target_temper"),
    ("bed_temp", "bed_temper"),
    ("bed_target", "bed_target_temper"),
    ("chamber_temp", "chamber_temper"),
    ("fan_part_raw", "cooling_fan_speed"),
    ("fan_aux_raw", "big_fan1_speed"),
    ("fan_chamber_raw", "big_fan2_speed"),
]


def _parse_report(raw: dict) -> dict | None:
    """Extract the fields Frank's HUD card actually shows from a Bambu MQTT
    `print` report. Confident fields (temps, state, progress, layers, file
    name, remaining time) are well and consistently documented across the
    open-source Bambu ecosystem. Fan-speed scaling and the speed-level->name
    mapping are community-documented, not Bambu-official -- passed through
    with their raw values alongside the best-effort interpretation so a
    wrong guess is visible on the HUD, never silently presented as fact.

    2026-08-11: only includes a key in the returned dict when the raw MQTT
    message actually reported it -- Bambu's `print` topic mixes full
    "pushall" reports with small partial deltas that only carry whatever
    changed, and the old version defaulted every absent field to None/[]
    unconditionally, indistinguishable from "the printer reports this is
    genuinely empty/zero." Frank's backend (_merge_printer_telemetry() in
    main.py) merges pushes into a running snapshot rather than overwriting,
    treating "key absent from this payload" as "no news, keep the last
    known value" -- this is the producing side of that same contract: never
    emit a key this specific message didn't actually carry."""
    p = raw.get("print")
    if not isinstance(p, dict):
        return None

    out: dict = {}
    for out_key, raw_key in _SCALAR_FIELDS:
        if raw_key in p:
            out[out_key] = p[raw_key]
    if "gcode_file" in p:
        out["print_file"] = p["gcode_file"] or None
    if "spd_lvl" in p:
        speed_lvl = p["spd_lvl"]
        out["speed_level_raw"] = speed_lvl
        out["speed_mode"] = _SPEED_MODE_BY_LEVEL.get(speed_lvl)

    if isinstance(p.get("ams"), dict):
        ams_trays = []
        for unit in p["ams"].get("ams", []) or []:
            for tray in unit.get("tray", []) or []:
                color = tray.get("tray_color") or ""
                if len(color) == 8:  # trailing alpha byte, e.g. "FF6B9DFF"
                    color = color[:6]
                ams_trays.append({
                    "id": tray.get("id"),
                    "color": f"#{color}" if color else None,
                    "material": tray.get("tray_type") or None,
                    "remain_pct": tray.get("remain"),
                })
        out["ams"] = ams_trays

    if "hms" in p:
        out["hms"] = [
            {"attr": h.get("attr"), "code": h.get("code")}
            for h in (p.get("hms") or []) if isinstance(h, dict)
        ]

    return out or None


def _on_connect(client, userdata, flags, rc, *_):
    if rc != 0:
        print(f"[bambu-bridge] MQTT connect failed, rc={rc}", flush=True)
        return
    print(f"[bambu-bridge] connected to printer at {BAMBU_IP}", flush=True)
    client.subscribe(f"device/{BAMBU_SERIAL}/report")
    # Ask for a full report immediately instead of waiting for the printer's
    # own next periodic push (documented Bambu LAN-mode request command).
    client.publish(
        f"device/{BAMBU_SERIAL}/request",
        json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}),
    )


def _on_message(client, userdata, msg, test_mode: bool = False, result_holder: list | None = None):
    global _last_push_at
    try:
        raw = json.loads(msg.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return
    parsed = _parse_report(raw)
    if parsed is None:
        return

    if test_mode:
        if result_holder is not None:
            result_holder.append(parsed)
        return

    with _push_lock:
        now = time.time()
        if now - _last_push_at < PUSH_MIN_INTERVAL_SECS:
            return
        _last_push_at = now
    ok = _post_json("/api/printer/telemetry", parsed)
    if ok:
        state = parsed.get("state") or "?"
        pct = parsed.get("progress_pct")
        print(f"[bambu-bridge] pushed telemetry (state={state}, progress={pct}%)", flush=True)


def _build_client(on_message):
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        print("Missing dependency: pip install -r tools/relay/bambu_requirements.txt", file=sys.stderr)
        raise
    client = mqtt.Client()
    client.username_pw_set("bblp", BAMBU_ACCESS_CODE)
    # The P1S's local MQTT broker serves a self-signed certificate -- there is
    # no CA to verify against on a home LAN, same tradeoff every open-source
    # Bambu LAN-mode integration makes (Home Assistant's bambu_lab
    # integration, bambulabs_api, moonraker-bambu all do this).
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)
    client.on_connect = _on_connect
    client.on_message = on_message
    return client


def run_telemetry_loop() -> None:
    client = _build_client(_on_message)
    while True:
        try:
            client.connect(BAMBU_IP, MQTT_PORT, keepalive=30)
            client.loop_forever()
        except (OSError, ConnectionError) as exc:
            print(f"[bambu-bridge] MQTT connection error ({exc}) — retrying in {RECONNECT_BACKOFF_SECS}s", flush=True)
        except Exception as exc:  # never let an unexpected error kill the reconnect loop
            print(f"[bambu-bridge] unexpected error ({exc}) — retrying in {RECONNECT_BACKOFF_SECS}s", flush=True)
        time.sleep(RECONNECT_BACKOFF_SECS)


def run_test(timeout_secs: float = 15.0) -> None:
    result: list = []
    client = _build_client(lambda c, u, m: _on_message(c, u, m, test_mode=True, result_holder=result))
    print(f"[bambu-bridge] connecting to {BAMBU_IP}:{MQTT_PORT} as serial {BAMBU_SERIAL} ...", flush=True)
    client.connect(BAMBU_IP, MQTT_PORT, keepalive=30)
    client.loop_start()
    deadline = time.time() + timeout_secs
    while time.time() < deadline and not result:
        time.sleep(0.5)
    client.loop_stop()
    client.disconnect()
    if not result:
        print(f"[bambu-bridge] TEST FAILED: no report received within {timeout_secs}s.", flush=True)
        print("Check BAMBU_IP/BAMBU_ACCESS_CODE/BAMBU_SERIAL and that the printer is on and on the same network.", flush=True)
        sys.exit(1)
    print("[bambu-bridge] TEST OK — parsed report:", flush=True)
    print(json.dumps(result[0], indent=2), flush=True)


# ── Camera relay ─────────────────────────────────────────────────────────────
#
# The P1S's local camera port has never been officially documented by Bambu
# Lab. An earlier version of this script deliberately shipped without this
# feature rather than guess at the byte layout. 2026-07-30: independently
# verified the real protocol shape by fetching (not trusting an AI summary
# of) the actual source of a real open-source implementation
# (coelacant1/Bambu-Lab-Cloud-API, GPLv3) and reading it directly. That repo
# is GPLv3, which is incompatible with copying its code into this private
# codebase, so nothing below is copied -- this is an independent
# reimplementation of the same (unprotectable) protocol facts:
#   - TLS socket to the printer on port 6000, cert verification disabled
#     (same self-signed-cert tradeoff every LAN-mode Bambu integration makes,
#     see _build_client() above).
#   - An 80-byte auth packet: four little-endian uint32s (0x40 payload size,
#     0x3000 a type/command code, then two reserved/flags words), followed
#     by "bblp" null-padded to 32 bytes, then the Access Code null-padded to
#     32 bytes.
#   - Each frame is a 16-byte little-endian header (payload_size, track
#     index, flags, reserved) immediately followed by payload_size bytes of
#     JPEG data starting with the SOI marker (FF D8) and ending with EOI
#     (FF D9).
# Camera frames arrive much faster than telemetry once connected -- no
# debounce here, every frame received is pushed.

_CAMERA_PORT = 6000
_CAMERA_AUTH_PACKET_SIZE = 80
_CAMERA_HEADER_SIZE = 16
_CAMERA_MAX_FRAME_BYTES = 3_000_000  # matches main.py's _PRINTER_MAX_FRAME_BYTES
_JPEG_SOI = b"\xff\xd8"
_JPEG_EOI = b"\xff\xd9"
CAMERA_RECONNECT_BACKOFF_SECS = 5


def _build_camera_auth_packet(access_code: str) -> bytes:
    packet = struct.pack("<IIII", _CAMERA_AUTH_PACKET_SIZE - 16, 0x3000, 0, 0)
    packet += b"bblp".ljust(32, b"\x00")
    packet += access_code.encode("ascii", errors="ignore")[:32].ljust(32, b"\x00")
    return packet


def _open_camera_socket() -> ssl.SSLSocket:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    raw = socket.create_connection((BAMBU_IP, _CAMERA_PORT), timeout=10)
    sock = ctx.wrap_socket(raw)
    sock.sendall(_build_camera_auth_packet(BAMBU_ACCESS_CODE))
    return sock


def _recv_exact(sock: ssl.SSLSocket, size: int) -> bytes:
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("camera socket closed by printer")
        data += chunk
    return data


def _read_camera_frames(on_frame) -> None:
    sock = _open_camera_socket()
    try:
        while True:
            header = _recv_exact(sock, _CAMERA_HEADER_SIZE)
            payload_size = struct.unpack_from("<I", header, 0)[0]
            if payload_size <= 0 or payload_size > _CAMERA_MAX_FRAME_BYTES:
                raise ConnectionError(f"implausible camera frame size {payload_size} -- desynced")
            frame = _recv_exact(sock, payload_size)
            if not (frame.startswith(_JPEG_SOI) and frame.endswith(_JPEG_EOI)):
                continue  # desynced mid-stream -- drop this frame, keep reading
            on_frame(frame)
    finally:
        sock.close()


def run_camera_loop() -> None:
    def _on_frame(frame: bytes) -> None:
        _post_bytes("/api/printer/camera-frame", frame, "image/jpeg")

    while True:
        try:
            _read_camera_frames(_on_frame)
        except Exception as exc:
            print(f"[bambu-bridge] camera relay error ({exc}) — retrying in {CAMERA_RECONNECT_BACKOFF_SECS}s", flush=True)
        time.sleep(CAMERA_RECONNECT_BACKOFF_SECS)


def run_test_camera(timeout_secs: float = 15.0) -> None:
    got_frame = threading.Event()
    sizes: list[int] = []

    def _on_frame(frame: bytes) -> None:
        sizes.append(len(frame))
        got_frame.set()

    def _try_once() -> None:
        try:
            _read_camera_frames(_on_frame)
        except Exception as exc:
            print(f"[bambu-bridge] camera test connection error: {exc}", flush=True)

    print(f"[bambu-bridge] connecting to {BAMBU_IP}:{_CAMERA_PORT} for camera test ...", flush=True)
    threading.Thread(target=_try_once, daemon=True).start()
    got_frame.wait(timeout=timeout_secs)
    if not got_frame.is_set():
        print(f"[bambu-bridge] CAMERA TEST FAILED: no frame received within {timeout_secs}s.", flush=True)
        print("This is a best-effort, unofficial protocol (see the module docstring) -- report this output back so it can be fixed with real signal.", flush=True)
        sys.exit(1)
    print(f"[bambu-bridge] CAMERA TEST OK — received a {sizes[0]}-byte JPEG frame.", flush=True)


def _require_config() -> None:
    missing = [name for name, val in (
        ("BAMBU_IP", BAMBU_IP), ("BAMBU_ACCESS_CODE", BAMBU_ACCESS_CODE),
        ("BAMBU_SERIAL", BAMBU_SERIAL), ("APP_SECRET_TOKEN", APP_TOKEN),
    ) if not val]
    if missing:
        print(f"Missing required config: {', '.join(missing)} — see this file's docstring.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", action="store_true", help="Verify the MQTT handshake, print one parsed report, exit.")
    parser.add_argument("--test-camera", action="store_true", help="Connect to the camera port alone, print one frame's size, exit.")
    parser.add_argument("--no-camera", action="store_true", help="Run telemetry only -- skip the camera relay thread.")
    args = parser.parse_args()

    _require_config()

    if args.test:
        run_test()
        return
    if args.test_camera:
        run_test_camera()
        return

    if not args.no_camera:
        threading.Thread(target=run_camera_loop, daemon=True).start()

    run_telemetry_loop()


if __name__ == "__main__":
    main()
