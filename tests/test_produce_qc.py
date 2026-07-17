"""
Tests for the first one-tap production pipeline exposed to Frank: Quality Check
(POST /api/produce/qc-check + the qc_check_product agent tool). Verifies the
deterministic, zero-API path Claude runs by hand is now callable by Frank —
both when a button hits the endpoint and when the chat agent calls the tool.

Self-contained TestClient-against-the-real-app pattern, same as
tests/test_voice_config.py. Run: python tests/test_produce_qc.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_produceqc_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "produce-qc-test-not-a-real-secret")
os.environ["ENABLE_TEST_LOGIN"] = "true"
os.environ["TEST_LOGIN_USERNAME"] = "produceqctest"
os.environ["TEST_LOGIN_PASSWORD"] = "ProduceQcTest!2026Only"

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
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


# A product whose files exist in this repo/deploy; DP1030 was rebuilt + validated.
# If its files aren't present in this environment the verdict is "no_files", which
# is still a valid, well-formed response — the tests assert on shape + contract,
# not on a specific product being present.
_PID = "DP1030"


def test_helper_returns_structured_verdict():
    out = server._qc_check_product({"pid": _PID})
    check(isinstance(out, dict), "helper must return a dict")
    check(out.get("pid") == _PID, f"pid echoed, got {out.get('pid')}")
    check(out.get("verdict") in ("pass", "warn", "fail", "no_files"),
          f"verdict must be one of pass/warn/fail/no_files, got {out.get('verdict')}")
    summ = out.get("summary") or {}
    for k in ("pass", "warn", "fail", "files"):
        check(k in summ and isinstance(summ[k], int), f"summary.{k} must be an int, got {summ.get(k)}")
    check(isinstance(out.get("rows"), list), "rows must be a list")


def test_helper_requires_pid():
    out = server._qc_check_product({})
    check("error" in out, f"missing pid must return an error, got {out}")


def test_agent_tool_dispatch_matches_helper():
    # The path that fires when the owner tells Frank "check DP1030".
    out = server._execute_agent_tool("qc_check_product", {"pid": _PID})
    check(isinstance(out, dict) and out.get("pid") == _PID,
          f"agent tool dispatch should return the QC result, got {out}")
    check(out.get("verdict") in ("pass", "warn", "fail", "no_files"),
          "agent tool must return a valid verdict")


def test_tool_is_registered():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("qc_check_product" in names, "qc_check_product must be in AGENT_TOOLS so the agent can call it")


def test_http_endpoint():
    c = _logged_in_client()
    r = c.post("/api/produce/qc-check", json={"pid": _PID})
    check(r.status_code == 200, f"endpoint should 200, got {r.status_code}: {r.text[:200]}")
    data = r.json()
    check(data.get("pid") == _PID, f"endpoint echoes pid, got {data.get('pid')}")
    check("summary" in data and "verdict" in data, f"endpoint returns summary+verdict, got keys {list(data)}")


def test_listing_photos_tool_registered():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("generate_listing_photos" in names,
          "generate_listing_photos must be in AGENT_TOOLS so the agent can call it")


def test_listing_photos_requires_pid():
    out = server._produce_listing_photos({})
    check("error" in out, f"missing pid must error, got {out}")


def test_listing_photos_rejects_non_planner():
    out = server._produce_listing_photos({"pid": "ZZ9999"})
    check("error" in out and "planner" in out["error"].lower(),
          f"a non-planner code must be rejected clearly, got {out}")


def test_listing_photos_endpoint_contract():
    # Don't force a full 10-photo render in the test (slow, writes files); just assert
    # the endpoint is wired and returns a well-formed result or a clear error.
    c = _logged_in_client()
    r = c.post("/api/produce/listing-photos", json={"pid": "ZZ9999"})
    check(r.status_code == 200, f"endpoint should 200 with a JSON error body, got {r.status_code}")
    data = r.json()
    check("error" in data, f"non-planner pid should return a JSON error, got {data}")


def test_print_zip_tool_registered():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("generate_print_zip" in names,
          "generate_print_zip must be in AGENT_TOOLS so the agent can call it")


def test_print_zip_requires_pid():
    out = server._produce_print_zip({})
    check("error" in out, f"missing pid must error, got {out}")


def test_print_zip_missing_source():
    out = server._produce_print_zip({"pid": "WA9999"})
    check("error" in out and "source" in out["error"].lower(),
          f"missing source art must be reported clearly, got {out}")


def test_print_zip_endpoint_contract():
    c = _logged_in_client()
    r = c.post("/api/produce/print-zip", json={"pid": "WA9999"})
    check(r.status_code == 200, f"endpoint should 200 with a JSON error body, got {r.status_code}")
    check("error" in r.json(), f"missing-source pid should return a JSON error, got {r.json()}")


def test_build_planner_tool_registered():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("build_planner" in names,
          "build_planner must be in AGENT_TOOLS so the agent can build a planner on request")


def test_build_planner_requires_pid():
    out = server._produce_build_planner({})
    check("error" in out, f"missing pid must error, got {out}")


def test_build_planner_rejects_unconfigured():
    out = server._produce_build_planner({"pid": "DP9999"})
    check("error" in out, f"an unconfigured planner code must be rejected, got {out}")
    # must NOT have spawned a build for a bad code
    check(not out.get("started"), f"must not start a build for an unconfigured code, got {out}")


def test_build_sticker_pack_tool_registered():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("build_sticker_pack" in names,
          "build_sticker_pack must be in AGENT_TOOLS so the agent can build a pack on request")


def test_build_sticker_pack_requires_pid():
    out = server._produce_build_sticker_pack({})
    check("error" in out, f"missing pid must error, got {out}")


def test_build_sticker_pack_rejects_unspecced():
    out = server._produce_build_sticker_pack({"pid": "DP9999"})
    check("error" in out, f"a code with no sticker spec must be rejected, got {out}")
    check(not out.get("started"), f"must not start a build for an unspecced code, got {out}")


def test_build_sticker_pack_agent_dispatch():
    # Same clean rejection through the agent path (no build spawned).
    out = server._execute_agent_tool("build_sticker_pack", {"pid": "DP9999"})
    check(isinstance(out, dict) and "error" in out,
          f"agent dispatch of build_sticker_pack should reject an unspecced code, got {out}")


def test_art_engine_defaults_to_gemini():
    eng, err = server._resolve_art_engine({})
    check(err is None and eng == "gemini",
          f"no engine specified must default to gemini, got ({eng!r},{err!r})")
    eng, err = server._resolve_art_engine({"engine": ""})
    check(err is None and eng == "gemini", f"blank engine must default to gemini, got ({eng!r},{err!r})")


def test_art_engine_accepts_approved():
    for name in ("gemini", "openai", "gpt-image-2", "ideogram", "GEMINI"):
        eng, err = server._resolve_art_engine({"engine": name})
        check(err is None and eng == name.lower(), f"{name} should be accepted, got ({eng!r},{err!r})")


def test_art_engine_rejects_unknown():
    eng, err = server._resolve_art_engine({"engine": "midjourney"})
    check(eng is None and err and "unknown art engine" in err,
          f"an unapproved engine must be rejected, got ({eng!r},{err!r})")


def test_build_planner_rejects_bad_engine():
    # A bad engine must be caught BEFORE any build is spawned.
    out = server._produce_build_planner({"pid": "DP1030", "engine": "stablediffusion"})
    check("error" in out and not out.get("started"),
          f"bad engine must error without starting a build, got {out}")


def test_build_product_tool_registered():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("build_product" in names,
          "build_product must be in AGENT_TOOLS so the agent can build a whole product")


def test_build_product_requires_pid():
    out = server._produce_build_product({})
    check("error" in out, f"missing pid must error, got {out}")


def test_build_product_rejects_unconfigured():
    out = server._produce_build_product({"pid": "DP9999"})
    check("error" in out and not out.get("started"),
          f"an unconfigured planner code must be rejected without starting, got {out}")


def test_build_product_rejects_bad_engine():
    out = server._produce_build_product({"pid": "DP1030", "engine": "midjourney"})
    check("error" in out and not out.get("started"),
          f"bad engine must error without starting a build, got {out}")


def test_build_product_agent_dispatch():
    out = server._execute_agent_tool("build_product", {"pid": "DP9999"})
    check(isinstance(out, dict) and "error" in out,
          f"agent dispatch of build_product should reject an unconfigured code, got {out}")


def run():
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PRODUCE-QC TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRODUCE-QC TESTS OK — helper, agent-tool dispatch, registration, and "
          "POST /api/produce/qc-check all verified.")


if __name__ == "__main__":
    run()
