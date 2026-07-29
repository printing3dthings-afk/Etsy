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

Camera relay (the live snapshot on the HUD card) is NOT implemented in this
version — the P1S's local camera stream uses a protocol Bambu Lab has never
published, and guessing at it would mean sending fabricated bytes to a raw
socket on the real printer. Telemetry (temps, progress, layers, AMS, HMS,
state) works fully without it. Run `--test-camera` for a short explanation
of what's missing and why; see the "Camera relay — NOT IMPLEMENTED" comment
further down in this file for the real follow-up path.
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Missing dependency: pip install -r tools/relay/bambu_requirements.txt", file=sys.stderr)
    raise

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
PUSH_MIN_INTERVAL_SECS = 3  # debounce -- the printer can send several report deltas/second
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


def _parse_report(raw: dict) -> dict | None:
    """Extract the fields Frank's HUD card actually shows from a Bambu MQTT
    `print` report. Confident fields (temps, state, progress, layers, file
    name, remaining time) are well and consistently documented across the
    open-source Bambu ecosystem. Fan-speed scaling and the speed-level->name
    mapping are community-documented, not Bambu-official -- passed through
    with their raw values alongside the best-effort interpretation so a
    wrong guess is visible on the HUD, never silently presented as fact."""
    p = raw.get("print")
    if not isinstance(p, dict):
        return None

    speed_lvl = p.get("spd_lvl")
    ams_trays = []
    ams_root = p.get("ams", {}) if isinstance(p.get("ams"), dict) else {}
    for unit in ams_root.get("ams", []) or []:
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

    hms = [
        {"attr": h.get("attr"), "code": h.get("code")}
        for h in (p.get("hms") or []) if isinstance(h, dict)
    ]

    return {
        "state": p.get("gcode_state"),
        "print_file": p.get("gcode_file") or None,
        "progress_pct": p.get("mc_percent"),
        "layer_current": p.get("layer_num"),
        "layer_total": p.get("total_layer_num"),
        "remaining_minutes": p.get("mc_remaining_time"),
        "speed_level_raw": speed_lvl,
        "speed_mode": _SPEED_MODE_BY_LEVEL.get(speed_lvl),
        "nozzle_temp": p.get("nozzle_temper"),
        "nozzle_target": p.get("nozzle_target_temper"),
        "bed_temp": p.get("bed_temper"),
        "bed_target": p.get("bed_target_temper"),
        "chamber_temp": p.get("chamber_temper"),
        "fan_part_raw": p.get("cooling_fan_speed"),
        "fan_aux_raw": p.get("big_fan1_speed"),
        "fan_chamber_raw": p.get("big_fan2_speed"),
        "ams": ams_trays,
        "hms": hms,
    }


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


def _build_client(on_message) -> "mqtt.Client":
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


# ── Camera relay — NOT IMPLEMENTED ──────────────────────────────────────────
#
# The P1S's local camera stream uses a protocol Bambu Lab has never publicly
# documented. Community tools (Home Assistant's bambu_lab integration,
# bambulabs_api, various go2rtc-based bridges) do relay it, but their exact
# byte-level framing was not something this script could verify against real
# hardware while being written, and guessing at magic bytes/packet layout
# would mean sending fabricated data to a raw socket on Scott's real printer
# with no way to confirm it's correct or even harmless. Rather than ship
# invented protocol constants dressed up as documented behavior, telemetry
# (well-documented, high-confidence) ships alone in this version; camera
# support is a real follow-up once either (a) the exact framing is confirmed
# against one of the community references above, or (b) Scott points this at
# a known-working relay tool directly. Frank's backend already exposes
# POST /api/printer/camera-frame + GET /api/printer/camera.jpg for whichever
# of those happens first — see tools/api_server/main.py.


def run_test_camera() -> None:
    print("[bambu-bridge] Camera relay is not implemented in this version.", flush=True)
    print("See the 'Camera relay — NOT IMPLEMENTED' comment in this file for why and what's needed to add it.", flush=True)
    print("Telemetry (temps/progress/AMS/HMS/state) works fully without it via the default run mode.", flush=True)
    sys.exit(1)


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
    parser.add_argument("--test-camera", action="store_true", help="Print why camera relay isn't implemented yet, exit.")
    args = parser.parse_args()

    _require_config()

    if args.test:
        run_test()
        return
    if args.test_camera:
        run_test_camera()
        return

    run_telemetry_loop()


if __name__ == "__main__":
    main()
