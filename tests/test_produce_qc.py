"""
Tests for the first one-tap production pipeline exposed to Frank: Quality Check
(POST /api/produce/qc-check + the qc_check_product agent tool). Verifies the
deterministic, zero-API path Claude runs by hand is now callable by Frank —
both when a button hits the endpoint and when the chat agent calls the tool.

Self-contained TestClient-against-the-real-app pattern, same as
tests/test_voice_config.py. Run: python tests/test_produce_qc.py
"""
import os
import re
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import MagicMock, patch

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


# ── Wall Art / Coloring Pages new-art generation flow (2026-07-22) ─────────
# Scott: "every action on this page has to work ... if this doesn't work we
# don't have a business." A genuinely new wall_art/coloring_pages pid with
# no existing source art/catalog entry can now actually be built by passing
# `description` -- these test that path's pre-flight validation and
# successful-kickoff shape (mocked subprocess.Popen, never a real build).

def test_wallart_new_pid_no_source_no_description_rejected_cleanly():
    out = server._produce_build_product({"pid": "WA_TOTALLY_NEW_TEST_PID", "category": "wall_art"})
    check("error" in out, f"a new wall_art pid with no description must error, got {out}")
    check(not out.get("started"), f"must not start, got {out}")
    check("new one" in out["error"].lower() or "describe" in out["error"].lower(),
          f"the error should point at the new-art option, got {out}")


def test_wallart_new_pid_with_description_starts_generation_steps():
    fake_proc = MagicMock()
    fake_proc.pid = 900001
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.object(server, "_product_log_dir", return_value=Path(tmpdir)), \
             patch.object(server.subprocess, "Popen", return_value=fake_proc):
            out = server._produce_build_product({
                "pid": "WA_TOTALLY_NEW_TEST_PID", "category": "wall_art",
                "description": "a boho sun in terracotta and cream watercolor",
            })
    server._LONG_RUNNING_PROCS.pop(900001, None)
    check(out.get("started") is True, f"a new pid with a real description must start, got {out}")
    check("generate art" in out.get("steps", []), f"steps must include the new art-generation step, got {out}")
    check(out.get("needs_visual_qc") is True, f"AI-generated art needs the visual-QC honesty flag, got {out}")
    check(out.get("engine") == "gemini", f"default engine should resolve to gemini, got {out}")


def test_wallart_description_with_bad_engine_rejected_before_spawning():
    with patch.object(server.subprocess, "Popen") as mock_popen:
        out = server._produce_build_product({
            "pid": "WA_TOTALLY_NEW_TEST_PID", "category": "wall_art",
            "description": "some art", "engine": "midjourney",
        })
    check("error" in out and not out.get("started"), f"a bad engine must error without starting, got {out}")
    check(not mock_popen.called, "a bad engine must be caught BEFORE any subprocess spawns")


def test_coloring_new_pid_no_catalog_no_description_rejected_cleanly():
    out = server._produce_build_product({"pid": "COLOR_TOTALLY_NEW_TEST_PID", "category": "coloring_pages"})
    check("error" in out, f"an uncataloged coloring_pages pid with no description must error, got {out}")
    check(not out.get("started"), f"must not start, got {out}")
    check("catalog" in out["error"].lower(), f"got {out}")


def test_coloring_new_pid_with_description_starts_generation_steps():
    # (2026-07-24) main.py's coloring_pages branch now expands the typed theme
    # into NEW_THEME_SET_SIZE distinct subjects itself via _resolve_coloring_subjects()
    # -- a real Anthropic call -- before spawning the build. Mock it so this test
    # stays a pure pre-flight/kickoff-shape check, not an integration test of the
    # subject-generation LLM call (that's covered by test_coloring_theme_registry.py).
    # _record_used_coloring_subjects() is left real (not mocked) here on purpose --
    # it's cheap, synchronous local-file I/O -- but must be pointed at a throwaway
    # registry path, never the real data/coloring_theme_registry.json sidecar.
    fake_proc = MagicMock()
    fake_proc.pid = 900002
    fake_subjects = [f"subject {i}" for i in range(20)]
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "coloring_theme_registry.json"
        with patch.object(server, "_product_log_dir", return_value=Path(tmpdir)), \
             patch.object(server, "_resolve_coloring_subjects", return_value=(fake_subjects, None)), \
             patch.object(server, "_COLORING_THEME_REGISTRY_PATH", registry_path), \
             patch.object(server.subprocess, "Popen", return_value=fake_proc):
            out = server._produce_build_product({
                "pid": "COLOR_TOTALLY_NEW_TEST_PID", "category": "coloring_pages",
                "description": "woodland animals",
            })
    server._LONG_RUNNING_PROCS.pop(900002, None)
    check(out.get("started") is True, f"a new pid with a theme must start, got {out}")
    check("coloring pages (new theme)" in out.get("steps", []), f"steps must flag the new-theme path, got {out}")
    check(out.get("needs_visual_qc") is True, f"got {out}")


def _kickoff_coloring_build(pid, extra_inp):
    """Shared helper for the difficulty->engine default tests below: kicks off
    a new-theme coloring build with mocked subject generation + subprocess,
    returns (out, popen_env) so callers can inspect which engine actually got
    threaded into the spawned subprocess's IMAGE_ENGINE env var -- the real
    signal build_coloring_product.py's own IMAGE_ENGINE-driven engine picks
    up, not just the --engine CLI arg (see _subprocess_env_with_engine)."""
    fake_proc = MagicMock()
    fake_proc.pid = 900010 + abs(hash(pid)) % 1000
    fake_subjects = [f"subject {i}" for i in range(20)]
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "coloring_theme_registry.json"
        with patch.object(server, "_product_log_dir", return_value=Path(tmpdir)), \
             patch.object(server, "_resolve_coloring_subjects", return_value=(fake_subjects, None)), \
             patch.object(server, "_COLORING_THEME_REGISTRY_PATH", registry_path), \
             patch.object(server.subprocess, "Popen", return_value=fake_proc) as mock_popen:
            out = server._produce_build_product({
                "pid": pid, "category": "coloring_pages", "description": "woodland animals",
                **extra_inp,
            })
        server._LONG_RUNNING_PROCS.pop(fake_proc.pid, None)
        popen_env = mock_popen.call_args.kwargs.get("env") or {}
    return out, popen_env


# ── Difficulty -> engine default (2026-08-09) ────────────────────────────────
# Scott: "let's make grok more for teen and adult coloring pages. open ai for
# kids." Confirmed across 3 real side-by-side prompts (cabin/treehouse/monster
# truck, filed in the Reference Photos library) that Grok renders denser,
# more intricate line art and OpenAI renders simpler, kid-friendly line art
# from the identical prompt. main.py's coloring_pages branch now defaults the
# engine by difficulty ONLY when the caller leaves engine blank -- these
# cover both the default and the explicit-override escape hatch.

def test_coloring_kids_difficulty_defaults_engine_to_openai():
    out, env = _kickoff_coloring_build("COLOR_DIFF_ENGINE_KIDS", {"difficulty": "kids"})
    check(out.get("started") is True, f"got {out}")
    check(env.get("IMAGE_ENGINE") == "openai",
          f"difficulty=kids with no explicit engine must default to openai, got env={env}")


def test_coloring_standard_difficulty_defaults_engine_to_grok():
    out, env = _kickoff_coloring_build("COLOR_DIFF_ENGINE_STD", {"difficulty": "standard"})
    check(out.get("started") is True, f"got {out}")
    check(env.get("IMAGE_ENGINE") == "grok",
          f"difficulty=standard with no explicit engine must default to grok, got env={env}")


def test_coloring_adult_difficulty_defaults_engine_to_grok():
    out, env = _kickoff_coloring_build("COLOR_DIFF_ENGINE_ADULT", {"difficulty": "adult"})
    check(out.get("started") is True, f"got {out}")
    check(env.get("IMAGE_ENGINE") == "grok",
          f"difficulty=adult with no explicit engine must default to grok, got env={env}")


def test_coloring_explicit_engine_overrides_difficulty_default():
    """An explicit engine choice (the Create screen's dropdown always sends
    one) must win over the difficulty-based default -- kids must NOT be
    force-locked to openai if Scott hand-picks something else."""
    out, env = _kickoff_coloring_build("COLOR_DIFF_ENGINE_OVERRIDE",
                                        {"difficulty": "kids", "engine": "ideogram"})
    check(out.get("started") is True, f"got {out}")
    check(env.get("IMAGE_ENGINE") == "ideogram",
          f"an explicit engine must override the kids->openai default, got env={env}")


def test_coloring_subject_generation_failure_blocks_build_before_spawn():
    """_resolve_coloring_subjects() returning an error (e.g. the registry
    couldn't produce enough non-repeating subjects, or ANTHROPIC_KEY is unset)
    must reject the build BEFORE any subprocess spawns -- mirrors
    test_wallart_description_with_bad_engine_rejected_before_spawning's shape."""
    with patch.object(server, "_resolve_coloring_subjects",
                       return_value=([], "Could only generate 3/20 distinct new subjects.")), \
         patch.object(server.subprocess, "Popen") as mock_popen:
        out = server._produce_build_product({
            "pid": "COLOR_TOTALLY_NEW_TEST_PID", "category": "coloring_pages",
            "description": "woodland animals",
        })
    check("error" in out and not out.get("started"),
          f"a subject-generation failure must error without starting, got {out}")
    check(not mock_popen.called, "a subject-generation failure must be caught BEFORE any subprocess spawns")


def test_coloring_subjects_recorded_before_spawn():
    """The registry reservation (_record_used_coloring_subjects) must happen
    as part of a successful kickoff, using the exact subjects returned by
    _resolve_coloring_subjects() -- see that function's docstring for why
    eager (not deferred-to-success) recording is the correct tradeoff here."""
    fake_proc = MagicMock()
    fake_proc.pid = 900003
    fake_subjects = [f"subject {i}" for i in range(20)]
    recorded = {}

    def _fake_record(product_id, theme, subjects):
        recorded["product_id"] = product_id
        recorded["theme"] = theme
        recorded["subjects"] = subjects

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.object(server, "_product_log_dir", return_value=Path(tmpdir)), \
             patch.object(server, "_resolve_coloring_subjects", return_value=(fake_subjects, None)), \
             patch.object(server, "_record_used_coloring_subjects", side_effect=_fake_record), \
             patch.object(server.subprocess, "Popen", return_value=fake_proc):
            out = server._produce_build_product({
                "pid": "COLOR_RECORD_TEST_PID", "category": "coloring_pages",
                "description": "woodland animals",
            })
    server._LONG_RUNNING_PROCS.pop(900003, None)
    check(out.get("started") is True, f"got {out}")
    check(recorded.get("product_id") == "COLOR_RECORD_TEST_PID", f"got {recorded}")
    check(recorded.get("theme") == "woodland animals", f"got {recorded}")
    check(recorded.get("subjects") == fake_subjects, f"got {recorded}")


# ── Coloring Pages auto-generated code (2026-07-25) ─────────────────────────
# Scott: "It should auto generate the code" -- the Create screen no longer
# collects a typed pid for a new coloring-pages theme. These cover
# _produce_build_product()'s reordered pid-required logic and
# _next_coloring_pid()'s own scanning behavior.

def test_coloring_auto_generates_pid_when_none_typed():
    fake_proc = MagicMock()
    fake_proc.pid = 900004
    fake_subjects = [f"subject {i}" for i in range(20)]
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "coloring_theme_registry.json"
        with patch.object(server, "_product_log_dir", return_value=Path(tmpdir)), \
             patch.object(server, "_resolve_coloring_subjects", return_value=(fake_subjects, None)), \
             patch.object(server, "_COLORING_THEME_REGISTRY_PATH", registry_path), \
             patch.object(server, "_next_coloring_pid", return_value="COLOR9001"), \
             patch.object(server.subprocess, "Popen", return_value=fake_proc):
            out = server._produce_build_product({
                "category": "coloring_pages", "description": "ocean animals",
            })
    server._LONG_RUNNING_PROCS.pop(900004, None)
    check(out.get("started") is True, f"an auto-generated pid must still start the build, got {out}")
    check(out.get("pid") == "COLOR9001", f"the assigned pid must be echoed back, got {out}")
    check("coloring pages (new theme)" in out.get("steps", []), f"got {out}")


def test_coloring_no_pid_no_description_gets_theme_specific_error():
    with patch.object(server.subprocess, "Popen") as mock_popen:
        out = server._produce_build_product({"category": "coloring_pages"})
    check("error" in out and not out.get("started"), f"got {out}")
    check("theme" in out["error"].lower(), f"the error should point at describing a theme, not a code, got {out}")
    check(not mock_popen.called, "must be caught before any subprocess spawns")


def test_coloring_explicit_pid_bypasses_auto_generation():
    """Regression guard on the reordered top-of-function logic: an explicitly
    typed pid must still be used verbatim, never overridden by the
    auto-generator."""
    fake_proc = MagicMock()
    fake_proc.pid = 900005
    fake_subjects = [f"subject {i}" for i in range(20)]
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "coloring_theme_registry.json"
        with patch.object(server, "_product_log_dir", return_value=Path(tmpdir)), \
             patch.object(server, "_resolve_coloring_subjects", return_value=(fake_subjects, None)), \
             patch.object(server, "_COLORING_THEME_REGISTRY_PATH", registry_path), \
             patch.object(server, "_next_coloring_pid") as mock_next_pid, \
             patch.object(server.subprocess, "Popen", return_value=fake_proc):
            out = server._produce_build_product({
                "pid": "COLOR_EXPLICIT_TEST", "category": "coloring_pages",
                "description": "ocean animals",
            })
    server._LONG_RUNNING_PROCS.pop(900005, None)
    check(out.get("pid") == "COLOR_EXPLICIT_TEST", f"got {out}")
    check(not mock_next_pid.called, "an explicit pid must never trigger auto-generation")


def test_next_coloring_pid_skips_used_codes():
    taken = {"COLOR1001", "COLOR1002"}

    def _fake_find(product_id):
        return {"product_id": product_id} if product_id in taken else None

    with patch.object(server, "_find_catalog_product", side_effect=_fake_find):
        pid = server._next_coloring_pid()
    check(pid == "COLOR1003", f"expected the first free code after the taken ones, got {pid}")


def test_next_coloring_pid_returns_lowest_when_none_taken():
    with patch.object(server, "_find_catalog_product", return_value=None):
        pid = server._next_coloring_pid()
    check(pid == "COLOR1001", f"got {pid}")
    check(re.fullmatch(r"COLOR\d+", pid), f"expected a COLOR#### shape, got {pid!r}")


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
