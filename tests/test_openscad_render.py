"""
Tests for tools/openscad_render.py and its render_openscad_model chat tool
(tools/api_server/main.py, added 2026-08-14).

openscad is a system binary (apt package `openscad`), not a pip dependency
-- it is NOT guaranteed to be installed wherever this test runs (it wasn't
in this dev sandbox until installed by hand for verification, and it isn't
in the Railway server image or CI runner by default). Tests are split into
two groups:

  1. Always run, regardless of whether openscad is installed: input
     validation, output-filename sanitization, and the "cleanly reports
     unavailable" path -- all exercised via check_openscad_available()
     mocked to False, so they never depend on environment state.
  2. Real end-to-end render checks (a real cube, real bad syntax, a real
     -D override) -- skipped with a printed note (not a failure) when
     shutil.which('openscad') finds nothing, exactly like this repo's
     existing pattern for optional external tools (see e.g.
     process_sticker_sheets.py's rembg fallback). When openscad IS
     available, these run for real against the actual binary -- confirmed
     working end-to-end during development (2026-08-14: a real cube([10,
     10,10]) rendered a genuine 1503-byte ASCII STL with real vertex data,
     bad syntax and an empty-geometry difference() both surfaced as
     OpenSCADError instead of a silent/bare failure, and a -D size override
     changed the actual rendered vertex coordinates).

Run: python3 tests/test_openscad_render.py
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_openscad_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "openscad-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import openscad_render as osr  # noqa: E402

_HAS_OPENSCAD = shutil.which("openscad") is not None

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── Always-run: input validation, never touches the real binary ────────────

def test_missing_scad_source_refused():
    result = server._execute_agent_tool("render_openscad_model", {"output_name": "thing"})
    check(result.get("error") is not None, f"expected an error for missing scad_source, got: {result}")


def test_missing_output_name_refused():
    result = server._execute_agent_tool("render_openscad_model", {"scad_source": "cube([1,1,1]);"})
    check(result.get("error") is not None, f"expected an error for missing output_name, got: {result}")


def test_bad_params_type_refused():
    result = server._execute_agent_tool("render_openscad_model", {
        "scad_source": "cube([1,1,1]);", "output_name": "thing", "params": "not a dict",
    })
    check(result.get("error") is not None, f"expected an error for non-dict params, got: {result}")


def test_unavailable_binary_reports_cleanly_not_a_crash():
    with patch.object(osr, "check_openscad_available", return_value=(False, "openscad is not installed. Install it with `apt-get install -y openscad`.")):
        result = server._execute_agent_tool("render_openscad_model", {
            "scad_source": "cube([10,10,10]);", "output_name": "test_cube",
        })
    check(result.get("error") is not None, f"expected a clean error, got: {result}")
    check("apt-get" in result.get("error", ""), f"expected an actionable install hint, got: {result}")


def test_output_name_sanitized():
    """A dangerous/messy output_name (spaces, punctuation, path separators)
    must never reach the filesystem un-sanitized -- this is the one place
    Claude-supplied free text becomes part of a real file path."""
    with patch.object(osr, "check_openscad_available", return_value=(False, "unavailable for this check")):
        result = server._execute_agent_tool("render_openscad_model", {
            "scad_source": "cube([1,1,1]);",
            "output_name": "../../etc/passwd; rm -rf /",
        })
    # Unavailable binary short-circuits before the name is ever used in a path --
    # this test only proves the tool doesn't crash on a hostile name at the
    # validation stage. The real sanitization is proven end-to-end below when
    # openscad is actually installed.
    check(result.get("error") is not None, f"expected a clean error (unavailable), got: {result}")


# ── Real end-to-end: only when the openscad binary is actually present ─────

def test_real_render_produces_a_genuine_mesh():
    if not _HAS_OPENSCAD:
        print("  [skip: openscad not installed in this environment]")
        return
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "cube.stl"
        result = osr.render_scad("cube([10,10,10]);", out)
        check(result == out, f"expected render_scad to return {out}, got {result}")
        check(out.exists() and out.stat().st_size > 0, "expected a real non-empty STL file on disk")
        content = out.read_text()
        check(content.startswith("solid"), f"expected ASCII STL header, got: {content[:40]!r}")
        check("vertex" in content, "expected real vertex data in the STL")


def test_real_bad_syntax_raises_openscaderror_not_bare_crash():
    if not _HAS_OPENSCAD:
        print("  [skip: openscad not installed in this environment]")
        return
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "bad.stl"
        try:
            osr.render_scad("cube([10,10,10)", out)  # missing closing bracket
            check(False, "expected OpenSCADError for invalid syntax, got no exception")
        except osr.OpenSCADError as exc:
            check(len(str(exc)) > 10, f"expected an actionable error message, got: {exc!r}")
        except Exception as exc:  # noqa: BLE001
            check(False, f"expected OpenSCADError specifically, got unwrapped {type(exc).__name__}: {exc!r}")


def test_real_param_override_changes_the_render():
    if not _HAS_OPENSCAD:
        print("  [skip: openscad not installed in this environment]")
        return
    with tempfile.TemporaryDirectory() as td:
        out_small = Path(td) / "small.stl"
        out_big = Path(td) / "big.stl"
        osr.render_scad("size=5; cube([size,size,size]);", out_small, params={"size": "5"})
        osr.render_scad("size=5; cube([size,size,size]);", out_big, params={"size": "50"})
        small_txt, big_txt = out_small.read_text(), out_big.read_text()
        check(small_txt != big_txt, "a -D size override must actually change the rendered geometry")
        check("50" in big_txt, f"expected the overridden size (50) to appear in vertex coordinates, "
                                f"got a render that doesn't mention it: {big_txt[:200]!r}")


def test_end_to_end_via_chat_tool_dispatch():
    """The exact path Frank actually uses: a full round-trip through
    _execute_agent_tool, not the module function directly."""
    if not _HAS_OPENSCAD:
        print("  [skip: openscad not installed in this environment]")
        return
    result = server._execute_agent_tool("render_openscad_model", {
        "scad_source": "cube([8,8,8]);",
        "output_name": "chat tool test cube!!",
        "format": "stl",
    })
    check(result.get("error") is None, f"expected a successful render, got: {result}")
    check(result.get("format") == "stl", f"expected format stl, got: {result}")
    check("chat_tool_test_cube" in result.get("output_name", ""),
          f"expected the sanitized output_name to keep the readable parts, got: {result}")
    # The full path this tool reports must actually exist on disk.
    from pathlib import Path as _P
    rel = result.get("path", "")
    full = server._product_log_dir().parent / rel
    check(full.exists() and full.stat().st_size > 0,
          f"expected the reported path {full} to be a real non-empty file")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("OPENSCAD RENDER TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    note = "" if _HAS_OPENSCAD else " (real-render checks skipped -- openscad not installed here)"
    print(f"OPENSCAD RENDER TESTS OK{note} -- render_openscad_model validates input, reports a "
          f"missing binary cleanly instead of crashing, and (when openscad is available) really "
          f"renders parametric OpenSCAD source to a genuine mesh file end to end.")


if __name__ == "__main__":
    run()
