"""The home bridge starts an approved print only on an idle printer it can see.

Network edges (Frank, FTPS, MQTT) are mocked; the decisions are real. A busy
or silent printer must fail the job without uploading anything, a start the
printer never acknowledges must be reported as failed, and the MQTT command
must name the plate, the file and the AMS trays Scott approved.
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
for k, v in (("BAMBU_IP", "192.0.2.10"), ("BAMBU_ACCESS_CODE", "12345678"),
             ("BAMBU_SERIAL", "01P00TEST"), ("APP_SECRET_TOKEN", "bridge-test-not-a-real-secret")):
    os.environ[k] = v
sys.path.insert(0, str(ROOT / "tools" / "relay"))

import bambu_p1s_bridge as bridge  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


JOB = {"id": 7, "file_path": "prints/Leland Plaque.gcode.3mf", "label": "LELAND plaque", "plate": 1,
       "ams_mapping": [0, 1, 2, 3], "bed_type": "textured_plate",
       "download": {"root": "volume", "path": "prints/Leland Plaque.gcode.3mf"}}


class _Info:
    rc = 0


class _Client:
    def __init__(self, then_state=None):
        self.sent = []
        self.then_state = then_state

    def publish(self, topic, payload):
        self.sent.append((topic, json.loads(payload)))
        if self.then_state:
            with bridge._state_lock:
                bridge._printer_state.update(state=self.then_state, at=time.time() + 0.01)
        return _Info()


def _run(state, *, age=1.0, client=None, timeout=1.0):
    reports, uploads = [], []
    with bridge._state_lock:
        bridge._printer_state.update(state=state, at=(time.time() - age) if state else 0.0)
    bridge._mqtt_client = client
    with tempfile.TemporaryDirectory() as wd, \
         patch.object(bridge, "_report", lambda jid, st, d: reports.append((jid, st, d))), \
         patch.object(bridge, "_download_job_file", lambda job, dest: Path(dest).write_bytes(b"zip")), \
         patch.object(bridge, "_upload_to_printer", lambda local, name: uploads.append(name)):
        out = bridge._handle_job(dict(JOB), workdir=Path(wd), start_timeout=timeout)
    return out, reports, uploads


def test_busy_printer_fails_without_uploading():
    out, reports, uploads = _run("RUNNING", client=_Client())
    check(out == "failed" and not uploads, "a job was uploaded to a printer that was RUNNING")
    check(reports and "RUNNING" in reports[0][2], f"busy failure not explained: {reports!r}")


def test_silent_printer_fails_without_uploading():
    out, _, uploads = _run("IDLE", age=120, client=_Client())
    check(out == "failed" and not uploads, "a job was started on a printer not heard from for 2 minutes")
    out, _, uploads = _run(None, client=_Client())
    check(out == "failed" and not uploads, "a job was started on a printer that never reported")


def test_idle_printer_gets_the_approved_command():
    c = _Client(then_state="PREPARE")
    out, reports, uploads = _run("FINISH", client=c)
    check(out == "started", f"an acknowledged start was not reported started: {reports!r}")
    check(uploads == ["Leland_Plaque.gcode.3mf"], f"unexpected printer file name: {uploads!r}")
    check(len(c.sent) == 1 and c.sent[0][0] == "device/01P00TEST/request", f"bad publish: {c.sent!r}")
    cmd = c.sent[0][1]["print"]
    check(cmd["command"] == "project_file" and cmd["param"] == "Metadata/plate_1.gcode", f"bad command: {cmd!r}")
    check(cmd["url"] == "ftp:///Leland_Plaque.gcode.3mf" and cmd["file"] == "Leland_Plaque.gcode.3mf", "file not named in command")
    check(cmd["use_ams"] is True and cmd["ams_mapping"] == [0, 1, 2, 3], f"AMS trays not passed: {cmd!r}")


def test_unacknowledged_start_is_a_failure():
    out, reports, _ = _run("IDLE", client=_Client(then_state=None), timeout=1.5)
    check(out == "failed" and reports and "did not start" in reports[-1][2],
          f"a start the printer never acknowledged was not reported failed: {reports!r}")


def test_stale_state_from_before_the_command_does_not_count():
    # the printer said RUNNING before the command was sent: that is the old print, not ours
    c = _Client(then_state=None)
    with bridge._state_lock:
        bridge._printer_state.update(state="IDLE", at=time.time())
    out, _, _ = _run("IDLE", client=c, timeout=1.2)
    check(out == "failed", "a start was assumed without a report after the command")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("BRIDGE PRINT JOB TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("BRIDGE PRINT JOB TESTS OK — prints start only on an idle, reporting printer, with the approved plate and AMS trays, and an unacknowledged start is a failure.")


if __name__ == "__main__":
    run()
