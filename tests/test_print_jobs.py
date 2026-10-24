"""start_print: staged, approved by Scott, queued, claimed once by the bridge.

Starting a print is physical and irreversible from here, so these pin the
gate: a model file or an unsliced project can never be staged, nothing is
queued without approval, the kill switch stops both approval and the
bridge's claim, a job is handed out exactly once, and a stale approval
expires instead of starting a day late.
"""
import asyncio
import os
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_print_jobs_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "print-jobs-test-not-a-real-secret")
_vol = tempfile.TemporaryDirectory(prefix="frank_print_jobs_vol_")
os.environ["HUB_FILES_DIR"] = _vol.name

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import db  # noqa: E402
from fastapi import HTTPException  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _sliced(name: str, plates=(1,)) -> str:
    path = Path(_vol.name) / "prints" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("3D/3dmodel.model", "<model/>")
        for n in plates:
            z.writestr(f"Metadata/plate_{n}.gcode", "; HEADER_BLOCK_START\nG28\n")
    return f"prints/{name}"


def _stage(**body):
    return asyncio.run(server.stage_print_job(body, _token="t"))


def _status_code(fn) -> int | None:
    try:
        fn()
    except HTTPException as exc:
        return exc.status_code
    return None


def _set_killed(on: bool) -> None:
    db.set_kill_switch(on)


def _drain_queue() -> None:
    while db.claim_next_print_job():
        pass


def test_rejects_anything_but_a_sliced_project():
    stl = Path(_vol.name) / "prints" / "rocket.stl"
    stl.parent.mkdir(parents=True, exist_ok=True)
    stl.write_bytes(b"solid x")
    check(_status_code(lambda: _stage(file_path="prints/rocket.stl")) == 422, "a model file was accepted as a print")
    unsliced = Path(_vol.name) / "prints" / "unsliced.gcode.3mf"
    with zipfile.ZipFile(unsliced, "w") as z:
        z.writestr("3D/3dmodel.model", "<model/>")
    check(_status_code(lambda: _stage(file_path="prints/unsliced.gcode.3mf")) == 422,
          "a 3MF with no plate G-code was accepted")
    check(_status_code(lambda: _stage(file_path="prints/missing.gcode.3mf")) == 422, "a missing file was accepted")
    check(_status_code(lambda: _stage(file_path="../../etc/passwd.gcode.3mf")) == 422, "a path outside the volume was accepted")
    ok = _sliced("one_plate.gcode.3mf")
    check(_status_code(lambda: _stage(file_path=ok, plate=2)) == 422, "plate 2 of a one-plate project was accepted")
    check(_status_code(lambda: _stage(file_path=ok, ams_mapping=[0, 16])) == 422, "AMS tray 16 was accepted")
    check(_status_code(lambda: _stage(file_path=ok, ams_mapping=[True])) == 422, "a bool AMS tray was accepted")
    check(_status_code(lambda: _stage(file_path=ok, bed_type="glass")) == 422, "an unknown bed type was accepted")


def test_staging_queues_nothing_until_approved():
    _drain_queue()
    f = _sliced("plaque.gcode.3mf")
    res = _stage(file_path=f, label="LELAND plaque", ams_mapping=[0, 1, 2, 3])
    check(res.get("staged") is True, f"staging failed: {res!r}")
    a = db.get_action(res["action_id"])
    check(a and a["type"] == "start_print" and a["status"] == "pending", f"bad staged action: {a!r}")
    check(db.claim_next_print_job() is None, "a job was claimable before Scott approved anything")
    out = asyncio.run(server.approve_action(res["action_id"], _token="t"))
    check(out.get("status") == "executed", f"approval did not execute: {out!r}")
    job = asyncio.run(server.get_next_print_job(_token="t"))["job"]
    check(job is not None and job["file_path"] == f and job["ams_mapping"] == [0, 1, 2, 3],
          f"approved job not handed to the bridge intact: {job!r}")
    check(job and job["download"] == {"root": "volume", "path": f}, "job carries no download location")
    again = asyncio.run(server.get_next_print_job(_token="t"))["job"]
    check(again is None, "the same job was handed out twice")
    r = asyncio.run(server.report_print_job_status(job["id"], {"status": "started"}, _token="t"))
    check(r["status"] == "started" and db.get_print_job(job["id"])["status"] == "started", "start not recorded")
    check(_status_code(lambda: asyncio.run(server.report_print_job_status(job["id"], {"status": "failed"}, _token="t"))) == 409,
          "a started job could be re-reported")


def test_kill_switch_blocks_approval_and_claim():
    _drain_queue()
    res = _stage(file_path=_sliced("kill.gcode.3mf"))
    _set_killed(True)
    try:
        check(_status_code(lambda: asyncio.run(server.approve_action(res["action_id"], _token="t"))) == 409,
              "a print was approved with the kill switch engaged")
        job_id = db.create_print_job(None, "prints/kill.gcode.3mf", "k", 1, None, "textured_plate")
        nxt = asyncio.run(server.get_next_print_job(_token="t"))
        check(nxt["job"] is None, "the bridge was handed a job with the kill switch engaged")
        check(db.get_print_job(job_id)["status"] == "queued", "the kill switch consumed the queued job")
    finally:
        _set_killed(False)
    _drain_queue()


def test_stale_approval_expires_instead_of_starting():
    _drain_queue()
    job_id = db.create_print_job(None, "prints/old.gcode.3mf", "old", 1, None, "textured_plate")
    old = (datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat()
    conn = db._connect()
    try:
        conn.execute("UPDATE print_jobs SET created_at=? WHERE id=?", (old, job_id))
        conn.commit()
    finally:
        conn.close()
    check(db.claim_next_print_job() is None, "a 45-minute-old approval was handed to the bridge")
    j = db.get_print_job(job_id)
    check(j["status"] == "failed" and "expired" in (j["detail"] or ""), f"stale job not expired: {j!r}")


def test_cancel_only_before_claim():
    _drain_queue()
    a = db.create_print_job(None, "prints/c.gcode.3mf", "c", 1, None, "textured_plate")
    asyncio.run(server.cancel_print_job(a, _token="t"))
    check(db.get_print_job(a)["status"] == "cancelled", "queued job not cancelled")
    check(db.claim_next_print_job() is None, "a cancelled job was claimed")
    b = db.create_print_job(None, "prints/c.gcode.3mf", "c", 1, None, "textured_plate")
    db.claim_next_print_job()
    check(_status_code(lambda: asyncio.run(server.cancel_print_job(b, _token="t"))) == 409,
          "a job already sent to the printer was 'cancelled' here")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PRINT JOB TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRINT JOB TESTS OK — only an approved, sliced project reaches the bridge, once, while the kill switch is off and the approval is fresh.")


if __name__ == "__main__":
    run()
