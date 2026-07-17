"""
Tests for the broadened _health_check_iteration() checks (Frank upgrade Wave 1,
reliability item 4, 2026-07-17): OpenAI/Gemini key presence, durable-volume
writability, and hub_db_state.json staleness. Before this, the health loop only
ever looked at Etsy + Anthropic -- a dead art-engine key, a detached/unwritable
volume, or a silently-stale weekly backup would all go unnoticed until something
downstream actually broke.

Each check is exercised against a deliberately-broken case (missing keys, an
unwritable "volume" dir, a backdated snapshot file) to confirm it actually fires,
not just that the code parses. Self-contained, same pattern as
tests/test_health_check_reap.py. Run:
    python tests/test_health_check_broadened.py
"""
import asyncio
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_healthbroad_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "healthbroad-test-not-a-real-secret")

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


async def _run_all_checks() -> None:
    # --- 1) Both art-engine keys missing -> should alert (status=error). ---
    saved_openai = os.environ.pop("OPENAI_API_KEY", None)
    saved_gemini = os.environ.pop("GEMINI_API_KEY", None)
    try:
        await server._health_check_iteration()
        hb = {h["name"]: h for h in await asyncio.to_thread(db.list_agent_heartbeats)}
        art = hb.get("health:art_keys")
        check(art is not None and art["status"] == "error",
              f"both art keys missing should heartbeat status=error, got {art}")
    finally:
        if saved_openai is not None:
            os.environ["OPENAI_API_KEY"] = saved_openai
        if saved_gemini is not None:
            os.environ["GEMINI_API_KEY"] = saved_gemini

    # --- 2) Only one art-engine key present -> should heartbeat "warn", not
    #        "error" (deliberately sub-alert-threshold; Gemini alone is fine). ---
    os.environ["GEMINI_API_KEY"] = "fake-key-for-test"
    os.environ.pop("OPENAI_API_KEY", None)
    try:
        await server._health_check_iteration()
        hb = {h["name"]: h for h in await asyncio.to_thread(db.list_agent_heartbeats)}
        art = hb.get("health:art_keys")
        check(art is not None and art["status"] == "warn",
              f"one art key present should heartbeat status=warn (sub-alert), got {art}")
    finally:
        os.environ.pop("GEMINI_API_KEY", None)

    # --- 3) Both keys present -> "ok". ---
    os.environ["OPENAI_API_KEY"] = "fake-key-for-test"
    os.environ["GEMINI_API_KEY"] = "fake-key-for-test"
    try:
        await server._health_check_iteration()
        hb = {h["name"]: h for h in await asyncio.to_thread(db.list_agent_heartbeats)}
        art = hb.get("health:art_keys")
        check(art is not None and art["status"] == "ok", f"both keys present should be ok, got {art}")
    finally:
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("GEMINI_API_KEY", None)

    # --- 4) Unwritable "volume" -> should heartbeat error + ops_runbook entry.
    #        Points "volume" at a PATH THAT IS ALREADY A FILE, not a directory, so
    #        vol.mkdir(parents=True, exist_ok=True) raises regardless of privilege
    #        level -- chmod-based read-only simulation doesn't work reliably here
    #        since this suite often runs as root, which bypasses Unix permission
    #        bits entirely (confirmed while writing this test). ---
    with tempfile.TemporaryDirectory() as tmp_root:
        fake_vol = Path(tmp_root) / "not_actually_a_dir"
        fake_vol.write_text("i am a file, not a directory")
        saved_volume = server._FILE_ROOTS.get("volume")
        server._FILE_ROOTS["volume"] = fake_vol
        try:
            await server._health_check_iteration()
            hb = {h["name"]: h for h in await asyncio.to_thread(db.list_agent_heartbeats)}
            vol_hb = hb.get("health:volume")
            check(vol_hb is not None and vol_hb["status"] == "error",
                  f"unwritable volume should heartbeat status=error, got {vol_hb}")
        finally:
            if saved_volume is not None:
                server._FILE_ROOTS["volume"] = saved_volume
            else:
                server._FILE_ROOTS.pop("volume", None)

    # --- 5) Writable volume -> "ok", and the probe file doesn't leak. ---
    with tempfile.TemporaryDirectory() as tmp_root:
        good_vol = Path(tmp_root) / "writable_vol"
        good_vol.mkdir()
        saved_volume = server._FILE_ROOTS.get("volume")
        server._FILE_ROOTS["volume"] = good_vol
        try:
            await server._health_check_iteration()
            hb = {h["name"]: h for h in await asyncio.to_thread(db.list_agent_heartbeats)}
            vol_hb = hb.get("health:volume")
            check(vol_hb is not None and vol_hb["status"] == "ok", f"writable volume should be ok, got {vol_hb}")
            leftover = list(good_vol.glob(".health_check_write_probe"))
            check(not leftover, f"the write-probe file should be cleaned up, found {leftover}")
        finally:
            if saved_volume is not None:
                server._FILE_ROOTS["volume"] = saved_volume
            else:
                server._FILE_ROOTS.pop("volume", None)

    # --- 6) Stale hub_db_state.json (backdated mtime) -> should alert. ---
    import backup_hub_db
    saved_out_path = backup_hub_db.OUT_PATH
    with tempfile.TemporaryDirectory() as tmp_root:
        stale_path = Path(tmp_root) / "hub_db_state.json"
        stale_path.write_text("{}")
        old_time = 20 * 86400  # 20 days ago, well past the 10-day threshold
        os.utime(stale_path, (stale_path.stat().st_atime - old_time, stale_path.stat().st_mtime - old_time))
        backup_hub_db.OUT_PATH = stale_path
        try:
            await server._health_check_iteration()
            hb = {h["name"]: h for h in await asyncio.to_thread(db.list_agent_heartbeats)}
            snap = hb.get("health:hub_db_backup")
            check(snap is not None and snap["status"] == "error",
                  f"a 20-day-stale hub_db snapshot should heartbeat status=error, got {snap}")
        finally:
            backup_hub_db.OUT_PATH = saved_out_path

    # --- 7) Fresh hub_db_state.json -> "ok". ---
    with tempfile.TemporaryDirectory() as tmp_root:
        fresh_path = Path(tmp_root) / "hub_db_state.json"
        fresh_path.write_text("{}")
        backup_hub_db.OUT_PATH = fresh_path
        try:
            await server._health_check_iteration()
            hb = {h["name"]: h for h in await asyncio.to_thread(db.list_agent_heartbeats)}
            snap = hb.get("health:hub_db_backup")
            check(snap is not None and snap["status"] == "ok", f"a fresh hub_db snapshot should be ok, got {snap}")
        finally:
            backup_hub_db.OUT_PATH = saved_out_path


def run() -> None:
    try:
        asyncio.run(_run_all_checks())
    except Exception:  # noqa: BLE001
        _failures.append(f"unhandled exception:\n{traceback.format_exc()}")
    if _failures:
        print("HEALTH-CHECK BROADENING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("HEALTH-CHECK BROADENING TESTS OK — art-key presence, volume writability, "
          "and hub_db backup staleness all verified against deliberately-broken cases.")


if __name__ == "__main__":
    run()
