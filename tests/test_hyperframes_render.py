"""
Tests for tools/hyperframes_render.py and its render_hyperframes_video chat
tool (tools/api_server/main.py, added 2026-08-14).

hyperframes is a Node.js CLI (npm package `hyperframes`) that needs Node.js,
ffmpeg, and a one-time Chrome Headless Shell download -- none guaranteed on
wherever this test runs (it wasn't in this dev sandbox until installed by
hand for verification, and none of it is in the Railway server image or CI
runner by default). Same two-group split as test_openscad_render.py:

  1. Always run, regardless of whether hyperframes is ready: input
     validation, the "cleanly reports unavailable" path, and media-file
     path resolution -- all exercised via check_hyperframes_available()
     mocked to False (or a deliberately-missing file), so they never
     depend on environment state.
  2. Real end-to-end render checks -- skipped with a printed note (not a
     failure) when hyperframes_render.check_hyperframes_available()
     reports unavailable. When it IS available, these run for real.
     Confirmed working end-to-end during development (2026-08-14): a real
     GSAP fade-in title composition rendered a genuine 1080x1920 H.264
     MP4; a real product-photo <img> reference rendered correctly via a
     copied-in media file; a malformed composition (no GSAP timeline, no
     data-duration) reliably hangs past HyperFrames' own internal timeouts
     and is only caught by this wrapper's own subprocess timeout -- a real
     observed failure mode, not a hypothetical one.

Run: python3 tests/test_hyperframes_render.py
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_hyperframes_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "hyperframes-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import hyperframes_render as hfr  # noqa: E402

_HAS_HYPERFRAMES = hfr.check_hyperframes_available()[0]

_SIMPLE_COMPOSITION = """<!doctype html><html><head>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>*{margin:0;padding:0}html,body{width:1080px;height:1920px;background:#241c2e}
#t{font-size:80px;color:#e4b155;padding:800px 60px;text-align:center;font-weight:700}</style>
</head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="2" data-width="1080" data-height="1920">
<div id="t" class="clip" data-start="0" data-duration="2" data-track-index="1">Test</div>
</div>
<script>window.__timelines = window.__timelines || {};
const tl = gsap.timeline({paused:true}); tl.from("#t", {opacity:0, duration:0.6}, 0);
window.__timelines["main"] = tl;</script></body></html>"""

_MALFORMED_COMPOSITION = "<html><body>not a real composition at all</body></html>"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── Always-run: input validation, never touches the real binary ────────────

def test_missing_html_source_refused():
    result = server._execute_agent_tool("render_hyperframes_video", {"output_name": "thing"})
    check(result.get("error") is not None, f"expected an error for missing html_source, got: {result}")


def test_missing_output_name_refused():
    result = server._execute_agent_tool("render_hyperframes_video", {"html_source": "<html></html>"})
    check(result.get("error") is not None, f"expected an error for missing output_name, got: {result}")


def test_bad_media_files_type_refused():
    result = server._execute_agent_tool("render_hyperframes_video", {
        "html_source": "<html></html>", "output_name": "thing", "media_files": "not a dict",
    })
    check(result.get("error") is not None, f"expected an error for non-dict media_files, got: {result}")


def test_unavailable_dependency_reports_cleanly_not_a_crash():
    with patch.object(hfr, "check_hyperframes_available",
                       return_value=(False, "hyperframes needs Node.js 22+ installed.")):
        result = server._execute_agent_tool("render_hyperframes_video", {
            "html_source": _SIMPLE_COMPOSITION, "output_name": "test_video",
        })
    check(result.get("error") is not None, f"expected a clean error, got: {result}")
    check("Node.js" in result.get("error", ""), f"expected the actual unavailable-reason to pass through, got: {result}")


def test_missing_media_file_refused_before_any_render_attempt():
    """resolve_media_file_path must catch a nonexistent media file BEFORE
    ever spawning hyperframes -- otherwise a typo'd path wastes a real
    render attempt only to fail deep inside the composition."""
    result = server._execute_agent_tool("render_hyperframes_video", {
        "html_source": _SIMPLE_COMPOSITION, "output_name": "thing",
        "media_files": {"assets/photo.jpg": "product_files/definitely_does_not_exist_12345.jpg"},
    })
    check(result.get("error") is not None, f"expected a clean error for missing media, got: {result}")
    check("not found" in result.get("error", "").lower(), f"expected a 'not found' message, got: {result}")


def test_resolve_media_file_path_checks_digital_products_base():
    """The digital_products-base resolution path specifically -- a relative
    path like a Files-tab entry (e.g. product_files/X/photo.jpg) must
    resolve against _product_log_dir().parent, not just cwd or an absolute
    path."""
    base = server._product_log_dir().parent
    test_dir = base / "product_files" / "_hyperframes_test_fixture"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "fixture.txt"
    test_file.write_text("fixture")
    try:
        resolved = server._resolve_media_file_path("product_files/_hyperframes_test_fixture/fixture.txt")
        check(resolved is not None and resolved.exists(),
              f"expected the digital_products-relative path to resolve, got: {resolved}")
    finally:
        test_file.unlink(missing_ok=True)
        test_dir.rmdir()


# ── Real end-to-end: only when hyperframes is actually ready ───────────────

def test_real_render_produces_a_genuine_video():
    if not _HAS_HYPERFRAMES:
        print("  [skip: hyperframes not available in this environment]")
        return
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "test.mp4"
        result = hfr.render_composition(_SIMPLE_COMPOSITION, out, quality="draft")
        check(result == out, f"expected render_composition to return {out}, got {result}")
        check(out.exists() and out.stat().st_size > 0, "expected a real non-empty MP4 file on disk")


def test_real_media_file_renders_into_the_video():
    if not _HAS_HYPERFRAMES:
        print("  [skip: hyperframes not available in this environment]")
        return
    from PIL import Image
    with tempfile.TemporaryDirectory() as td:
        photo = Path(td) / "photo.jpg"
        Image.new("RGB", (400, 400), (242, 160, 181)).save(photo)
        html = """<!doctype html><html><head>
        <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
        <style>*{margin:0;padding:0}html,body{width:1080px;height:1920px;background:#000}
        img{width:1080px;height:1080px;object-fit:cover;position:absolute;top:420px}</style></head>
        <body><div id="root" data-composition-id="main" data-start="0" data-duration="2" data-width="1080" data-height="1920">
        <img id="p" class="clip" data-start="0" data-duration="2" data-track-index="1" src="assets/photo.jpg" />
        </div><script>window.__timelines = window.__timelines || {};
        const tl = gsap.timeline({paused:true}); tl.from("#p", {opacity:0, duration:0.6}, 0);
        window.__timelines["main"] = tl;</script></body></html>"""
        out = Path(td) / "media.mp4"
        hfr.render_composition(html, out, media_files={"assets/photo.jpg": photo}, quality="draft")
        check(out.exists() and out.stat().st_size > 0, "expected a real non-empty MP4 with the photo composited in")


def test_real_malformed_composition_times_out_cleanly_not_a_hang():
    if not _HAS_HYPERFRAMES:
        print("  [skip: hyperframes not available in this environment]")
        return
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "bad.mp4"
        try:
            hfr.render_composition(_MALFORMED_COMPOSITION, out, timeout=25)
            check(False, "expected HyperframesError for a malformed composition, got no exception")
        except hfr.HyperframesError as exc:
            check(len(str(exc)) > 10, f"expected an actionable error message, got: {exc!r}")
        except Exception as exc:  # noqa: BLE001
            check(False, f"expected HyperframesError specifically, got unwrapped {type(exc).__name__}: {exc!r}")


def test_end_to_end_via_chat_tool_dispatch():
    """The exact path Frank actually uses: a full round-trip through
    _execute_agent_tool, not the module function directly."""
    if not _HAS_HYPERFRAMES:
        print("  [skip: hyperframes not available in this environment]")
        return
    result = server._execute_agent_tool("render_hyperframes_video", {
        "html_source": _SIMPLE_COMPOSITION,
        "output_name": "chat tool dispatch test!!",
        "quality": "draft",
    })
    check(result.get("error") is None, f"expected a successful render, got: {result}")
    check("chat_tool_dispatch_test" in result.get("output_name", ""),
          f"expected the sanitized output_name to keep the readable parts, got: {result}")
    full = server._product_log_dir().parent / result.get("path", "")
    check(full.exists() and full.stat().st_size > 0,
          f"expected the reported path {full} to be a real non-empty file")
    full.unlink(missing_ok=True)  # clean up -- data/digital_products/ is gitignored but no reason to litter it


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("HYPERFRAMES RENDER TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    note = "" if _HAS_HYPERFRAMES else " (real-render checks skipped -- hyperframes not available here)"
    print(f"HYPERFRAMES RENDER TESTS OK{note} -- render_hyperframes_video validates input, resolves media "
          f"files against the digital_products base, reports a missing dependency cleanly instead of "
          f"crashing, and (when hyperframes is available) really renders an HTML/GSAP composition to a "
          f"genuine MP4 end to end, including a real product photo and a malformed-composition timeout.")


if __name__ == "__main__":
    run()
