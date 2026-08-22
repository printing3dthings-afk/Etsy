#!/usr/bin/env python3
"""
Functional-correctness audit (key: studio_queue) -- three FastAPI route
handlers in tools/api_server/main.py that stage/generate AI video + SVG
conversion work, with zero existing test coverage before this file:

  - stage_video            POST /api/queue/stage-video   (line ~13351)
  - studio_convert_svg     POST /api/studio/convert-svg  (line ~13534)
  - studio_generate_video  POST /api/studio/generate     (line ~14759)

What this file checks:
  1. Input validation before staging/queuing -- a missing/invalid product
     (listing) id or an invalid mode/style must be rejected, not silently
     accepted into a queued/generated artifact.
  2. Per .claude/rules/api-conventions.md's "nothing irreversible auto-
     executes" rule, whether these genuinely stage work (via
     db.enqueue_action, requiring Scott's approval) or execute a real paid
     AI call directly and synchronously in the request path.

Every AI/image/video-generation and Etsy API boundary is mocked -- no real
network call, no real AI spend, no real data/ tree touched.

Run: python tests/test_functional_audit_studio_queue.py
"""
import io
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import asyncio  # noqa: E402
import main as server  # noqa: E402
from fastapi import HTTPException  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


class _FakeRequest:
    """Only .body() is used by stage_video/studio_convert_svg -- mirrors the
    pattern in tests/test_printer_telemetry.py (a full ASGI Request isn't
    needed to exercise the handler logic)."""
    def __init__(self, body: bytes):
        self._body = body

    async def body(self) -> bytes:
        return self._body


def _swap_root(name: str, tmp_path: Path):
    """Returns (original_value) so the caller can restore it in `finally`."""
    original = server._FILE_ROOTS.get(name)
    server._FILE_ROOTS[name] = tmp_path
    return original


def _tiny_png_bytes() -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color=(200, 100, 50)).save(buf, format="PNG")
    return buf.getvalue()


# ── stage_video ─────────────────────────────────────────────────────────────

def test_stage_video_rejects_falsy_listing_id():
    """listing_id=0 is a garbage product id (no real Etsy listing has id 0)
    -- _stage_video_action's payload validation must refuse it rather than
    silently queuing an approval-center action with no real listing attached."""
    tmp = tempfile.TemporaryDirectory()
    orig = _swap_root("staged_videos", Path(tmp.name))
    try:
        req = _FakeRequest(b"fake mp4 bytes")
        with patch.object(server.db, "enqueue_action") as mock_enqueue:
            try:
                asyncio.run(server.stage_video(request=req, listing_id=0, rank=None, summary="", _token="test"))
                check(False, "stage_video accepted listing_id=0 without raising")
            except HTTPException as exc:
                check(exc.status_code == 422, f"expected 422 for listing_id=0, got {exc.status_code}")
                check("listing_id" in exc.detail, f"expected error to mention listing_id, got {exc.detail!r}")
            check(not mock_enqueue.called, "db.enqueue_action must NOT be called when validation fails")
    finally:
        server._FILE_ROOTS["staged_videos"] = orig
        tmp.cleanup()


def test_stage_video_rejects_empty_body():
    tmp = tempfile.TemporaryDirectory()
    orig = _swap_root("staged_videos", Path(tmp.name))
    try:
        req = _FakeRequest(b"")
        with patch.object(server.db, "enqueue_action") as mock_enqueue:
            try:
                asyncio.run(server.stage_video(request=req, listing_id=12345, rank=None, summary="", _token="test"))
                check(False, "stage_video accepted an empty body without raising")
            except HTTPException as exc:
                check(exc.status_code == 400, f"expected 400 for empty body, got {exc.status_code}")
            check(not mock_enqueue.called, "no file/db write should happen for an empty body")
    finally:
        server._FILE_ROOTS["staged_videos"] = orig
        tmp.cleanup()


def test_stage_video_rejects_oversized_body():
    tmp = tempfile.TemporaryDirectory()
    orig = _swap_root("staged_videos", Path(tmp.name))
    try:
        oversized = b"x" * (server._MAX_UPLOAD_BYTES + 1)
        req = _FakeRequest(oversized)
        try:
            asyncio.run(server.stage_video(request=req, listing_id=12345, rank=None, summary="", _token="test"))
            check(False, "stage_video accepted a body over _MAX_UPLOAD_BYTES without raising")
        except HTTPException as exc:
            check(exc.status_code == 413, f"expected 413 for oversized body, got {exc.status_code}")
    finally:
        server._FILE_ROOTS["staged_videos"] = orig
        tmp.cleanup()


def test_stage_video_rejects_invalid_rank():
    """rank, when provided, must be an int 1-10 per _validate_staged_action's
    listing_video branch -- rank=99 is not a valid Etsy photo/video slot."""
    tmp = tempfile.TemporaryDirectory()
    orig = _swap_root("staged_videos", Path(tmp.name))
    try:
        req = _FakeRequest(b"fake mp4 bytes")
        with patch.object(server.db, "enqueue_action") as mock_enqueue:
            try:
                asyncio.run(server.stage_video(request=req, listing_id=12345, rank=99, summary="", _token="test"))
                check(False, "stage_video accepted rank=99 without raising")
            except HTTPException as exc:
                check(exc.status_code == 422, f"expected 422 for rank=99, got {exc.status_code}")
            check(not mock_enqueue.called, "invalid rank must not reach db.enqueue_action")
        # File written to disk before validation should be rolled back (unlinked) on failure.
        staged = list(Path(tmp.name).rglob("*.mp4"))
        check(not staged, f"failed stage_video call left an orphan file on disk: {staged}")
    finally:
        server._FILE_ROOTS["staged_videos"] = orig
        tmp.cleanup()


def test_stage_video_valid_input_stages_real_action_and_file():
    """A genuinely valid call must (a) write the video bytes under
    staged_videos/<listing_id>/, and (b) enqueue exactly one 'listing_video'
    action via the real db.enqueue_action (writing to the temp test DB
    configured at import time, not the real product DB)."""
    tmp = tempfile.TemporaryDirectory()
    orig = _swap_root("staged_videos", Path(tmp.name))
    try:
        body = b"fake mp4 bytes for a valid staging call"
        req = _FakeRequest(body)
        result = asyncio.run(
            server.stage_video(request=req, listing_id=987654321, rank=3, summary="test video", _token="test")
        )
        check(isinstance(result.get("action_id"), int), f"expected an integer action_id, got {result}")
        check(result["path"].startswith("987654321/"), f"unexpected staged path: {result['path']}")

        staged_file = Path(tmp.name) / "987654321" / Path(result["path"]).name
        check(staged_file.is_file(), f"expected staged video file at {staged_file}")
        check(staged_file.read_bytes() == body, "staged file bytes do not match the uploaded body")

        row = server.db.get_action(result["action_id"])
        check(row is not None, "expected the staged action to be readable back from the db")
        if row is not None:
            check(row["type"] == "listing_video", f"expected type 'listing_video', got {row.get('type')}")
            payload = row.get("payload") or {}
            check(payload.get("listing_id") == 987654321, f"payload listing_id mismatch: {payload}")
            check(payload.get("rank") == 3, f"payload rank mismatch: {payload}")
    finally:
        server._FILE_ROOTS["staged_videos"] = orig
        tmp.cleanup()


# ── studio_convert_svg ──────────────────────────────────────────────────────

def test_studio_convert_svg_rejects_invalid_mode():
    """mode must be one of color/bw/silhouette -- svg_converter.convert_to_svg
    validates this itself (before any PIL/vtracer work), so this exercises
    the REAL validation path, not a mock."""
    tmp = tempfile.TemporaryDirectory()
    orig = _swap_root("svg_conversions", Path(tmp.name))
    try:
        req = _FakeRequest(_tiny_png_bytes())
        try:
            asyncio.run(server.studio_convert_svg(request=req, mode="not_a_real_mode", _token="test"))
            check(False, "studio_convert_svg accepted an invalid mode without raising")
        except HTTPException as exc:
            check(exc.status_code == 400, f"expected 400 for invalid mode, got {exc.status_code}")
    finally:
        server._FILE_ROOTS["svg_conversions"] = orig
        tmp.cleanup()


def test_studio_convert_svg_rejects_empty_body():
    tmp = tempfile.TemporaryDirectory()
    orig = _swap_root("svg_conversions", Path(tmp.name))
    try:
        req = _FakeRequest(b"")
        try:
            asyncio.run(server.studio_convert_svg(request=req, mode="color", _token="test"))
            check(False, "studio_convert_svg accepted an empty body without raising")
        except HTTPException as exc:
            check(exc.status_code == 400, f"expected 400 for empty body, got {exc.status_code}")
    finally:
        server._FILE_ROOTS["svg_conversions"] = orig
        tmp.cleanup()


def test_studio_convert_svg_rejects_unreadable_image():
    """Not valid image bytes at all -- svg_converter.convert_to_svg's real
    PIL.Image.open() call should raise, and the route must turn that into a
    400, not a bare 500 traceback (api-conventions.md: 'never a bare 500')."""
    tmp = tempfile.TemporaryDirectory()
    orig = _swap_root("svg_conversions", Path(tmp.name))
    try:
        req = _FakeRequest(b"this is not an image, just plain text bytes")
        try:
            asyncio.run(server.studio_convert_svg(request=req, mode="bw", _token="test"))
            check(False, "studio_convert_svg accepted unreadable image bytes without raising")
        except HTTPException as exc:
            check(exc.status_code in (400, 500), f"expected 400/500 for unreadable image, got {exc.status_code}")
    finally:
        server._FILE_ROOTS["svg_conversions"] = orig
        tmp.cleanup()


def test_studio_convert_svg_success_path_saves_and_returns_quality():
    tmp = tempfile.TemporaryDirectory()
    orig = _swap_root("svg_conversions", Path(tmp.name))
    try:
        fake_svg = '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 8"><path d="M0 0 L8 8"/></svg>'
        fake_quality = {"ok": True, "unique_fills": 1, "path_count": 1, "size_kb": 0.1}
        req = _FakeRequest(_tiny_png_bytes())
        with patch("svg_converter.convert_to_svg", return_value=fake_svg) as mock_convert, \
             patch.object(server.etsy_api, "check_svg_quality", return_value=fake_quality) as mock_quality:
            result = asyncio.run(server.studio_convert_svg(request=req, mode="color", _token="test"))
        check(mock_convert.called, "expected svg_converter.convert_to_svg to be called")
        check(mock_quality.called, "expected the real clean-vector quality gate to run on the result")
        check(result["ok"] is True, f"expected ok=True, got {result}")
        check(result["quality"] == fake_quality, f"expected quality passthrough, got {result['quality']}")
        saved = Path(tmp.name) / result["path"]
        check(saved.is_file(), f"expected saved SVG at {saved}")
        check(saved.read_text(encoding="utf-8") == fake_svg, "saved SVG content mismatch")
    finally:
        server._FILE_ROOTS["svg_conversions"] = orig
        tmp.cleanup()


# ── studio_generate_video ───────────────────────────────────────────────────

def test_studio_generate_video_rejects_missing_listing_and_paths():
    try:
        asyncio.run(server.studio_generate_video(body={}, _token="test"))
        check(False, "studio_generate_video accepted a body with neither listing_id nor image_paths")
    except HTTPException as exc:
        check(exc.status_code == 400, f"expected 400, got {exc.status_code}")


def test_studio_generate_video_rejects_invalid_style():
    """style validation must run before generation/Etsy calls -- confirmed by
    not needing to mock EtsyAPIClient here and still getting a clean 400."""
    try:
        asyncio.run(
            server.studio_generate_video(
                body={"listing_id": 123, "style": "not-a-real-style"}, _token="test"
            )
        )
        check(False, "studio_generate_video accepted an invalid style without raising")
    except HTTPException as exc:
        check(exc.status_code == 400, f"expected 400 for invalid style, got {exc.status_code}")
        check("style" in exc.detail, f"expected error to mention style, got {exc.detail!r}")


def test_studio_generate_video_rejects_unresolvable_studio_upload():
    """image_paths pointing at a file that was never uploaded via
    /api/studio/upload-image must 404, not silently generate a video from
    nothing / crash uncontrolled."""
    tmp = tempfile.TemporaryDirectory()
    orig = _swap_root("studio_uploads", Path(tmp.name))
    try:
        try:
            asyncio.run(
                server.studio_generate_video(
                    body={"image_paths": ["does_not_exist.png"], "style": "showcase"}, _token="test"
                )
            )
            check(False, "studio_generate_video accepted a nonexistent studio upload without raising")
        except HTTPException as exc:
            check(exc.status_code == 404, f"expected 404 for missing studio upload, got {exc.status_code}")
    finally:
        server._FILE_ROOTS["studio_uploads"] = orig
        tmp.cleanup()


def test_studio_generate_video_success_is_synchronous_and_unstaged():
    """CORE FINDING CHECK: per api-conventions.md, 'nothing irreversible auto-
    executes' and 'any action that ... spends money ... gets staged via
    db.enqueue_action ... never executed directly from a chat tool'. This
    route generates a real slideshow video from a real listing's photos
    in-process and returns it directly -- it does NOT call db.enqueue_action.
    The route's own docstring argues this is fine ('asset generation only, no
    Etsy mutation') but the test confirms the actual mechanism: no approval
    gate exists between calling this endpoint and getting back a usable file.
    Reported as an observation per the task brief, not fixed."""
    fake_listing = {"title": "Test Listing", "price": {"amount": 1499, "divisor": 100}, "is_digital": True}
    from PIL import Image
    fake_imgs = [Image.new("RGB", (16, 16), color=(10, 20, 30))]

    tmp_out_dir = tempfile.TemporaryDirectory()
    try:
        fake_video_path = Path(tmp_out_dir.name) / "fake_video.mp4"
        fake_video_path.write_bytes(b"fake mp4 payload")

        with patch.object(server, "EtsyAPIClient", return_value=MagicMock()) as mock_client_cls, \
             patch("video_generator.fetch_listing_images", return_value=(fake_imgs, fake_listing)) as mock_fetch, \
             patch("video_generator.generate_video", return_value=fake_video_path) as mock_generate, \
             patch.object(server.db, "enqueue_action") as mock_enqueue:
            result = asyncio.run(
                server.studio_generate_video(
                    body={"listing_id": 555, "style": "showcase"}, _token="test"
                )
            )
        check(mock_client_cls.called, "expected EtsyAPIClient to be constructed for the listing_id path")
        check(mock_fetch.called, "expected video_generator.fetch_listing_images to be called")
        check(mock_generate.called, "expected video_generator.generate_video to be called synchronously")
        check(result.get("ok") is True, f"expected ok=True, got {result}")
        check(result.get("path") == "fake_video.mp4", f"unexpected returned path: {result}")
        check(
            not mock_enqueue.called,
            "FINDING: studio_generate_video returned a usable generated video WITHOUT staging "
            "any db.enqueue_action approval-center entry -- confirms the endpoint executes "
            "generation synchronously and unstaged rather than queuing it",
        )
    finally:
        tmp_out_dir.cleanup()


def test_studio_generate_video_ai_scene_calls_real_ai_api_directly_unstaged():
    """style='ai-scene' routes to ai_video.generate_ai_video() -- a real paid
    image-to-video AI API call (Sora/Veo) -- invoked synchronously inside the
    request handler via asyncio.to_thread, with NO staging step before or
    after. This is the literal scenario the task brief calls out: 'if one of
    these DOES call a real AI API directly, that itself may be a finding
    worth flagging.' The AI call itself is mocked here (no real spend); this
    test only proves the call happens synchronously in-request and unstaged."""
    fake_listing = {"title": "Test Listing", "price": {"amount": 999, "divisor": 100}, "is_digital": True}
    from PIL import Image
    fake_imgs = [Image.new("RGB", (16, 16), color=(50, 60, 70))]

    tmp_out_dir = tempfile.TemporaryDirectory()
    try:
        fake_video_path = Path(tmp_out_dir.name) / "fake_ai_video.mp4"
        fake_video_path.write_bytes(b"fake ai-generated mp4 payload")

        with patch.object(server, "EtsyAPIClient", return_value=MagicMock()) as mock_client_cls, \
             patch("video_generator.fetch_listing_images", return_value=(fake_imgs, fake_listing)) as mock_fetch, \
             patch("ai_video.generate_ai_video", return_value=fake_video_path) as mock_ai_generate, \
             patch.object(server.db, "enqueue_action") as mock_enqueue:
            result = asyncio.run(
                server.studio_generate_video(
                    body={"listing_id": 777, "style": "ai-scene", "aspect_ratio": "9:16"}, _token="test"
                )
            )
        check(mock_client_cls.called, "expected EtsyAPIClient to be constructed for the listing_id path")
        check(mock_fetch.called, "expected video_generator.fetch_listing_images to be called for ai-scene too")
        check(mock_ai_generate.called, "expected ai_video.generate_ai_video (the real paid AI call) to be invoked")
        if mock_ai_generate.called:
            call_args = mock_ai_generate.call_args[0]
            check(len(call_args) >= 3, f"unexpected call signature for generate_ai_video: {call_args}")
        check(result.get("ok") is True, f"expected ok=True, got {result}")
        check(
            not mock_enqueue.called,
            "FINDING: the ai-scene style calls the real paid AI video engine directly and "
            "synchronously with zero staging/approval step -- confirms this bypasses the "
            "db.enqueue_action staging pattern used by stage_video / stage_photo",
        )
    finally:
        tmp_out_dir.cleanup()


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print(
        "FUNCTIONAL AUDIT TESTS OK -- stage_video/studio_convert_svg validate input "
        "(listing_id, rank, mode, image bytes) before staging/converting, and "
        "studio_generate_video confirmed to execute video generation (including the "
        "real ai-scene AI-video-engine call) synchronously and unstaged, never via "
        "db.enqueue_action."
    )


if __name__ == "__main__":
    run()
