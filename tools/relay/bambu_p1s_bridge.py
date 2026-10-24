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

Approved prints: Scott approves a start_print action in Frank's Action
Center, and this bridge uploads that sliced file to the P1S and starts it --
only if the printer is idle, and only within 30 minutes of the approval. The
printer must be in LAN Only mode with Developer Mode on (see "Print jobs"
below). `--test-ftp` checks the upload path alone; `--no-print-jobs` turns
the feature off.

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
import ftplib
import json
import os
import socket
import ssl
import struct
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
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
# the printer's last reported gcode_state, for the print-job thread
_printer_state: dict = {"state": None, "at": 0.0}
_state_lock = threading.Lock()
_mqtt_client = None


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

    if parsed.get("state"):
        with _state_lock:
            _printer_state["state"] = parsed["state"]
            _printer_state["at"] = time.time()

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
    global _mqtt_client
    client = _build_client(_on_message)
    _mqtt_client = client
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


# ── Print jobs (2026-10-24) ───────────────────────────────────────────────────
# Scott approves a start_print action in Frank's Action Center; Frank queues a
# job; this thread claims it, uploads the sliced .gcode.3mf to the printer and
# starts it. Frank never reaches the printer itself. Protocol: FTPS (implicit
# TLS, port 990, user bblp) into the printer's storage, then a "project_file"
# command on the same MQTT request topic the telemetry uses. Reimplemented from
# the protocol as bambulabs_api documents it, not copied.
#
# The printer has to accept LAN commands: on current P1S firmware that means
# LAN Only mode with Developer Mode switched on (printer screen -> Settings ->
# LAN Only, then Developer Mode). Without it the printer ignores the start
# command, and the job is reported failed after START_TIMEOUT_SECS.

JOB_POLL_SECS = 10
START_TIMEOUT_SECS = 90
STATE_FRESH_SECS = 30
FTPS_PORT = 990
# a print can start only from these; FINISH and FAILED mean the last job is
# over, and Scott's approval is what says the plate has been cleared since
_IDLE_STATES = ("IDLE", "FINISH", "FAILED")
_STARTED_STATES = ("PREPARE", "RUNNING", "SLICING")


def _get_json(path: str) -> dict | None:
    req = urllib.request.Request(FRANK_API_BASE + path, headers={"Authorization": f"Bearer {APP_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError) as exc:
        print(f"[bambu-bridge] GET {path} failed: {exc}", flush=True)
        return None


def _download_job_file(job: dict, dest: Path) -> None:
    d = job["download"]
    q = urllib.parse.urlencode({"root": d["root"], "path": d["path"]})
    req = urllib.request.Request(f"{FRANK_API_BASE}/api/files/download?{q}",
                                 headers={"Authorization": f"Bearer {APP_TOKEN}"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)


def _report(job_id: int, status: str, detail: str) -> None:
    print(f"[bambu-bridge] print job #{job_id}: {status} -- {detail}", flush=True)
    _post_json(f"/api/print-jobs/{job_id}/status", {"status": status, "detail": detail})


class _ImplicitFTPS(ftplib.FTP_TLS):
    """ftplib speaks explicit FTPS (AUTH TLS); the printer wants TLS from the
    first byte, and wants the data channel to reuse the control channel's TLS
    session, which ftplib doesn't do on its own."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None

    @property
    def sock(self):
        return self._sock

    @sock.setter
    def sock(self, value):
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value

    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(conn, session=self.sock.session)
        return conn, size


def _ftps() -> _ImplicitFTPS:
    ctx = ssl.create_default_context()
    # the printer's certificate is self-signed, same as its MQTT broker (see _build_client)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ftp = _ImplicitFTPS(context=ctx, timeout=30)
    ftp.connect(BAMBU_IP, FTPS_PORT)
    ftp.login("bblp", BAMBU_ACCESS_CODE)
    ftp.prot_p()
    return ftp


def _upload_to_printer(local: Path, remote_name: str) -> None:
    ftp = _ftps()
    try:
        with open(local, "rb") as f:
            ftp.storbinary(f"STOR {remote_name}", f)
    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()


def _printer_file_name(job: dict) -> str:
    base = Path(job["file_path"]).name
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in base)
    return safe if safe.endswith(".gcode.3mf") else safe + ".gcode.3mf"


def _start_command(job: dict, remote_name: str) -> dict:
    ams = job.get("ams_mapping")
    return {"print": {
        "sequence_id": str(int(time.time())),
        "command": "project_file",
        "param": f"Metadata/plate_{int(job.get('plate') or 1)}.gcode",
        "subtask_name": job.get("label") or remote_name,
        "file": remote_name,
        "url": f"ftp:///{remote_name}",
        "project_id": "0", "profile_id": "0", "task_id": "0", "subtask_id": "0",
        "bed_type": job.get("bed_type") or "textured_plate",
        "bed_leveling": True,
        "flow_cali": True,
        "vibration_cali": True,
        "layer_inspect": False,
        "timelapse": False,
        "use_ams": bool(ams),
        "ams_mapping": ams or [],
        "skip_objects": None,
    }}


def _current_state() -> tuple[str | None, float]:
    with _state_lock:
        st, at = _printer_state["state"], _printer_state["at"]
    return st, (time.time() - at) if at else float("inf")


def _handle_job(job: dict, *, workdir: Path, start_timeout: float = START_TIMEOUT_SECS) -> str:
    """Run one claimed job to 'started' or 'failed', reporting either to Frank."""
    jid = job["id"]
    state, age = _current_state()
    if state is None or age > STATE_FRESH_SECS:
        _report(jid, "failed", "no recent report from the printer, so it could not be checked idle; stage it again once the bridge shows it online")
        return "failed"
    if state not in _IDLE_STATES:
        _report(jid, "failed", f"the printer was {state}, not idle, when the job arrived; stage it again once the plate is clear")
        return "failed"
    if _mqtt_client is None:
        _report(jid, "failed", "the bridge has no MQTT connection to the printer")
        return "failed"
    local = workdir / f"job_{jid}.gcode.3mf"
    remote = _printer_file_name(job)
    try:
        _download_job_file(job, local)
        _upload_to_printer(local, remote)
    except Exception as exc:
        _report(jid, "failed", f"could not get the file onto the printer: {exc}")
        return "failed"
    finally:
        local.unlink(missing_ok=True)
    info = _mqtt_client.publish(f"device/{BAMBU_SERIAL}/request", json.dumps(_start_command(job, remote)))
    if getattr(info, "rc", 0) != 0:
        _report(jid, "failed", f"MQTT publish of the start command failed (rc={info.rc})")
        return "failed"
    sent_at = time.time()
    while time.time() - sent_at < start_timeout:
        with _state_lock:
            st, at = _printer_state["state"], _printer_state["at"]
        if at > sent_at and st in _STARTED_STATES:
            _report(jid, "started", f"{remote} plate {job.get('plate') or 1} is {st} on the printer")
            return "started"
        time.sleep(1)
    st, _ = _current_state()
    _report(jid, "failed", f"uploaded {remote} but the printer did not start within {start_timeout:.0f}s "
                           f"(last state {st}); is Developer Mode on? see the bridge's print-jobs notes")
    return "failed"


def run_print_job_loop() -> None:
    """Poll Frank for approved jobs. Frank hands out nothing while its kill switch is engaged."""
    workdir = Path(tempfile.mkdtemp(prefix="bambu_jobs_"))
    while True:
        try:
            # Claim nothing while the printer is silent: the job stays queued
            # (and expires after 30 min) instead of failing on a reconnect.
            # A BUSY printer is different: _handle_job fails that job at once,
            # because waiting for the print to end would start the new one on
            # a plate that still holds the old one.
            if _current_state()[1] > STATE_FRESH_SECS:
                time.sleep(JOB_POLL_SECS)
                continue
            res = _get_json("/api/print-jobs/next")
            job = (res or {}).get("job")
            if job:
                print(f"[bambu-bridge] claimed print job #{job['id']} ({job.get('label')})", flush=True)
                _handle_job(job, workdir=workdir)
        except Exception as exc:  # never let one bad job kill the poller
            print(f"[bambu-bridge] print-job loop error: {exc}", flush=True)
        time.sleep(JOB_POLL_SECS)


def run_test_ftp() -> None:
    """Log in to the printer's storage over FTPS and list it. Uploads and starts nothing."""
    try:
        ftp = _ftps()
        names = ftp.nlst()
        ftp.quit()
    except Exception as exc:
        print(f"[bambu-bridge] FTPS TEST FAILED: {exc}", flush=True)
        sys.exit(1)
    print(f"[bambu-bridge] FTPS TEST OK -- {len(names)} entries on the printer's storage: {', '.join(names[:12])}", flush=True)


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
    parser.add_argument("--test-ftp", action="store_true", help="Log in to the printer's storage over FTPS, list it, exit. Prints nothing.")
    parser.add_argument("--no-print-jobs", action="store_true", help="Never start prints -- skip the approved-print-job poller.")
    args = parser.parse_args()

    _require_config()

    if args.test:
        run_test()
        return
    if args.test_camera:
        run_test_camera()
        return
    if args.test_ftp:
        run_test_ftp()
        return

    if not args.no_camera:
        threading.Thread(target=run_camera_loop, daemon=True).start()
    if not args.no_print_jobs:
        threading.Thread(target=run_print_job_loop, daemon=True).start()

    run_telemetry_loop()


if __name__ == "__main__":
    main()
