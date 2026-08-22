"""
Tests for stage_action's new action_type='listing_photo' path (2026-08-19).

Real bug this closes: a live hero-art false-positive audit (see
tools/shop_health_check.py's _dhash fix, same commit series) led to manually
downloading and inspecting listing 4512783077's actual photos, which surfaced
a genuine defect independent of that false-positive bug -- its rank-1 (hero/
thumbnail) photo showed an unrelated bedroom scene, while the correct "Paris
Cafe" artwork was sitting at rank 3. _stage_photo_action()/_PHOTO_STAGED_
ACTION_TYPES already fully supported staging a photo-rank fix (used by the
AI photo-regeneration pipeline), but stage_action's action_type enum never
included "listing_photo" and its input_schema had no rank/path fields, so
there was no tool-call path to fix a single existing listing's photo order
without the AI pipeline. Fixed with a dedicated early branch in
_execute_agent_tool's stage_action dispatch, same shape as the existing
register_product branch.

Checks:
  1. A well-formed listing_photo call (real file present under staged_photos/)
     stages successfully with the correct payload shape.
  2. A missing/nonexistent path is refused (matches _PHOTO_STAGED_ACTION_TYPES'
     own validate branch -- file must actually exist).
  3. An out-of-range rank is refused.
  4. The staged payload carries no leftover listing-mutation fields (title/
     tags/description/etc.) from the shared dispatch code path.

Run: python3 tests/test_stage_action_listing_photo.py
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_listing_photo_stage_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "listing-photo-stage-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _make_fixture_photo(staged_root: Path, rel_path: str) -> None:
    from PIL import Image
    full = staged_root / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    # Mid-tone colored image, not pale in any corner -- must survive
    # _check_no_pale_background's real corner-sampling gate.
    Image.new("RGB", (600, 600), color=(90, 60, 40)).save(full, "JPEG")


def test_listing_photo_stages_with_correct_payload():
    with tempfile.TemporaryDirectory() as tmp:
        staged_root = Path(tmp)
        _make_fixture_photo(staged_root, "WA_TEST_PRODUCT/hero_fix.jpg")
        with patch.dict(server._FILE_ROOTS, {"staged_photos": staged_root}):
            result = server._execute_agent_tool("stage_action", {
                "action_type": "listing_photo", "summary": "Fix wrong hero photo",
                "listing_id": 4512783077, "rank": 1,
                "path": "WA_TEST_PRODUCT/hero_fix.jpg",
            })
        check(result.get("staged") is True, f"expected a successful stage, got: {result}")
        aid = result.get("action_id")
        pending = server.db.list_actions("pending")
        match = next((a for a in pending if a.get("id") == aid), None)
        check(match is not None, f"staged action {aid} should be in the pending queue")
        if match:
            check(match["type"] == "listing_photo", f"expected type listing_photo, got: {match['type']}")
            payload = match["payload"]
            check(payload.get("listing_id") == 4512783077, f"listing_id mismatch: {payload}")
            check(payload.get("rank") == 1, f"rank mismatch: {payload}")
            check(payload.get("path") == "WA_TEST_PRODUCT/hero_fix.jpg", f"path mismatch: {payload}")


def test_listing_photo_missing_file_refused():
    with tempfile.TemporaryDirectory() as tmp:
        staged_root = Path(tmp)
        with patch.dict(server._FILE_ROOTS, {"staged_photos": staged_root}):
            result = server._execute_agent_tool("stage_action", {
                "action_type": "listing_photo", "summary": "no file here",
                "listing_id": 4512783077, "rank": 1,
                "path": "WA_TEST_PRODUCT/does_not_exist.jpg",
            })
    check(result.get("staged") is not True, f"a nonexistent staged file must be refused, got: {result}")
    check("error" in result, f"expected an error message, got: {result}")


def test_listing_photo_invalid_rank_refused():
    with tempfile.TemporaryDirectory() as tmp:
        staged_root = Path(tmp)
        _make_fixture_photo(staged_root, "WA_TEST_PRODUCT/hero_fix.jpg")
        with patch.dict(server._FILE_ROOTS, {"staged_photos": staged_root}):
            result = server._execute_agent_tool("stage_action", {
                "action_type": "listing_photo", "summary": "bad rank",
                "listing_id": 4512783077, "rank": 99,
                "path": "WA_TEST_PRODUCT/hero_fix.jpg",
            })
    check(result.get("staged") is not True, f"rank outside 1-10 must be refused, got: {result}")
    check("error" in result, f"expected an error message, got: {result}")


def test_listing_photo_payload_has_no_content_mutation_fields():
    with tempfile.TemporaryDirectory() as tmp:
        staged_root = Path(tmp)
        _make_fixture_photo(staged_root, "WA_TEST_PRODUCT/hero_fix.jpg")
        with patch.dict(server._FILE_ROOTS, {"staged_photos": staged_root}):
            result = server._execute_agent_tool("stage_action", {
                "action_type": "listing_photo", "summary": "shape check",
                "listing_id": 4512783077, "rank": 1,
                "path": "WA_TEST_PRODUCT/hero_fix.jpg",
            })
    check(result.get("staged") is True, f"expected a successful stage, got: {result}")
    pending = server.db.list_actions("pending")
    match = next((a for a in pending if a.get("id") == result.get("action_id")), None)
    check(match is not None, "staged action should be in the pending queue")
    if match:
        payload = match["payload"]
        check(set(payload.keys()) == {"listing_id", "rank", "path"},
              f"expected exactly the listing_photo shape, got keys: {sorted(payload.keys())}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("STAGE-ACTION LISTING-PHOTO TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("STAGE-ACTION LISTING-PHOTO TESTS OK — Claude can now stage a single-photo "
          "rank fix (e.g. promoting a correct existing photo to hero) through stage_action "
          "without going through the AI photo-regeneration pipeline, with the same "
          "validation guarantees _PHOTO_STAGED_ACTION_TYPES already enforced.")


if __name__ == "__main__":
    run()
