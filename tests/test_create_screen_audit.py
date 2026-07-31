"""
Tests for the Create screen UX audit (2026-07-31, sixth screen in the
screen-by-screen audit after Login/Home/Ask-Chat/Approvals/Today). This screen
had already been through multiple redesigns this session, so the audit found
comparatively few real gaps:

  1. A missing API key for the listing-photo generator's chosen engine was
     misreported as a transient "the image service had a temporary error —
     please try again in a moment" -- false, since retrying with no key
     configured fails identically forever. `_svc`/`failure_kind` classification
     (main.py) now special-cases the ImageGenError message signature used only
     for missing-key cases ("_API_KEY not set") into a new "config_error" kind,
     and the frontend (frank_hud_mockup.py) points the user at Settings instead
     of telling them to just retry.
  2. A stale doc comment above the reference-images routes claimed nothing used
     them for AI generation -- false since Wall Art's reference-style wiring
     shipped 2026-07-30.
  3. A leftover "only one with transparent background" clause on the listing-
     photo engine dropdown label didn't apply to that tool (an edit-style
     compositing call, never a transparent-background output).

Vision-QA extension to Coloring Pages / Planner covers (the other half of this
audit) is covered separately in test_coloring_planner_verify_retry.py, mirroring
test_wall_art_verify_retry.py's existing pattern for generate_wall_art_master().

Run: python tests/test_create_screen_audit.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_create_audit_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "create-audit-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import listing_photo_pipeline  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _run_lifestyle_photo_with_result(photo_result):
    """Drives studio_generate_lifestyle_photo() directly (bypassing FastAPI's
    dependency injection, per this repo's testing convention) with a real
    uploaded file and a mocked generate_verified_photo() so only the
    failure_kind classification logic under test actually runs."""
    with tempfile.TemporaryDirectory() as vol_dir:
        vol = Path(vol_dir)
        old_roots = dict(server._FILE_ROOTS)
        server._FILE_ROOTS["studio_uploads"] = vol / "studio_uploads"
        server._FILE_ROOTS["lifestyle_photos"] = vol / "lifestyle_photos"
        server._FILE_ROOTS["studio_uploads"].mkdir(parents=True)
        (server._FILE_ROOTS["studio_uploads"] / "design.png").write_bytes(b"fake-png-bytes")
        try:
            with patch.object(listing_photo_pipeline, "generate_verified_photo", return_value=photo_result):
                return asyncio.run(server.studio_generate_lifestyle_photo(
                    {"design_paths": ["design.png"], "scene_prompt": "on a desk", "category": "sign_flat"},
                    _token="test",
                ))
        finally:
            server._FILE_ROOTS.clear()
            server._FILE_ROOTS.update(old_roots)


def test_missing_api_key_classified_as_config_error():
    result = SimpleNamespace(
        passed=False, out_path=None, attempts=1,
        issues=["verification error: GEMINI_API_KEY not set (needed for engine='gemini')"],
    )
    body = _run_lifestyle_photo_with_result(result)
    check(body.get("failure_kind") == "config_error",
          f"a missing-API-key issue should classify as config_error, got: {body}")


def test_genuine_transient_error_still_classified_as_service_error():
    result = SimpleNamespace(
        passed=False, out_path=None, attempts=2,
        issues=["generation error: 500 Internal Server Error from image provider"],
    )
    body = _run_lifestyle_photo_with_result(result)
    check(body.get("failure_kind") == "service_error",
          f"a genuine transient failure should stay classified as service_error, got: {body}")


def test_real_mismatch_still_classified_as_mismatch():
    result = SimpleNamespace(
        passed=False, out_path=None, attempts=2,
        issues=["the rendered product does not match the source file's color"],
    )
    body = _run_lifestyle_photo_with_result(result)
    check(body.get("failure_kind") == "mismatch",
          f"a real product-mismatch rejection should stay classified as mismatch, got: {body}")


def test_frontend_renders_a_config_error_message_pointing_at_settings():
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text(encoding="utf-8")
    check("d.failure_kind === 'config_error'" in src,
          "expected a config_error branch in the lifestyle-photo failure handler")
    check("add it in Settings" in src,
          "the config_error message should point the user at the real fix (Settings), not 'try again'")


def test_reference_images_comment_no_longer_stale():
    src = (ROOT / "tools" / "api_server" / "main.py").read_text(encoding="utf-8")
    check("nothing here is wired into any AI generation call" not in src,
          "the stale claim should be gone now that Wall Art uses reference images (2026-07-30)")
    check("_reference_image_style_notes" in src,
          "sanity check: the actual wiring this comment was stale about should still be present")


def test_engine_label_no_longer_claims_transparent_background():
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text(encoding="utf-8")
    check("only one with transparent background" not in src,
          "the lifestyle-photo engine dropdown never produces a transparent background -- "
          "this leftover clause should be removed")


def main() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("CREATE SCREEN AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("CREATE SCREEN AUDIT TESTS OK — a missing API key now classifies as config_error "
          "(not a misleading 'temporary error, try again'), the stale reference-images "
          "comment is fixed, and the engine dropdown no longer claims a transparent "
          "background it never produces.")


if __name__ == "__main__":
    main()
