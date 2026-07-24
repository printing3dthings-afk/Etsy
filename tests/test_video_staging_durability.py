#!/usr/bin/env python3
"""
Video staging durability tests (2026-07-25): the same bug class as the
COLOR1001 incident (see generate_coloring_pages.py's _resolve_dp_base()
fix and tests/test_qc_sweep_coloring.py), found while re-exposing the
Product Video Create-screen tile. `_FILE_ROOTS["videos"]`,
`["studio_uploads"]`, and `["staged_videos"]` (main.py, near :13712) used
to be hardcoded to the ephemeral local `data/social/...` dir unconditionally
-- never checking the persistent Railway volume the way `staged_photos`
correctly does. `staged_videos/{listing_id}/...` is the sole copy of a
video between "Stage for Approval" and Scott actually approving it in the
Action Center, a window that can span a redeploy; when it did, the staged
DB action survived but the file didn't, and approval hit a
FileNotFoundError in the `listing_video` branch of `_execute_staged_action`.

Because these three roots are plain module-level constants computed once
at import time (not a re-callable resolve function like
generate_coloring_pages.py's), the only way to actually exercise the
volume-present branch is to set HUB_FILES_DIR *before* `import main` --
this file does exactly that, matching how tests/run_all.py already runs
every test file as its own subprocess (so this file's env mutation can
never leak into another test file's import of main.py).

Run: python tests/test_video_staging_durability.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_video_durability_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "video-durability-test-not-a-real-secret")

# Must be set before `import main` -- _FILE_ROOTS["volume"] (and everything
# derived from it, including the three roots under test) is computed once
# at module import time, not re-read per call.
_HUB_DIR = tempfile.mkdtemp(prefix="frank_video_durability_test_hub_")
os.environ["HUB_FILES_DIR"] = _HUB_DIR

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_volume_is_mounted_for_this_process():
    # Sanity check on the test's own setup -- if this fails, every other
    # test in this file is meaningless (would be silently exercising the
    # local-fallback branch instead of the volume branch under test).
    check("volume" in server._FILE_ROOTS, "HUB_FILES_DIR was set before import -- _FILE_ROOTS['volume'] must exist")
    check(server._FILE_ROOTS.get("volume") == Path(_HUB_DIR), f"expected volume={_HUB_DIR}, got {server._FILE_ROOTS.get('volume')}")


def test_videos_root_resolves_under_the_volume():
    expected = Path(_HUB_DIR) / "social" / "videos"
    check(server._FILE_ROOTS["videos"] == expected,
          f"videos root must nest under the mounted volume (COLOR1001-class fix), got {server._FILE_ROOTS['videos']}, expected {expected}")


def test_studio_uploads_root_resolves_under_the_volume():
    expected = Path(_HUB_DIR) / "social" / "studio_uploads"
    check(server._FILE_ROOTS["studio_uploads"] == expected,
          f"studio_uploads root must nest under the mounted volume, got {server._FILE_ROOTS['studio_uploads']}, expected {expected}")


def test_staged_videos_root_resolves_under_the_volume():
    # The highest-stakes root: this is the sole copy of a video between
    # staging and Scott's approval in the Action Center.
    expected = Path(_HUB_DIR) / "social" / "staged_videos"
    check(server._FILE_ROOTS["staged_videos"] == expected,
          f"staged_videos root must nest under the mounted volume, got {server._FILE_ROOTS['staged_videos']}, expected {expected}")


def test_staged_videos_matches_staged_photos_pattern():
    # staged_photos was always correct -- both should now resolve the same
    # shape (volume / <name>) relative to the same mounted volume.
    photos_rel = server._FILE_ROOTS["staged_photos"].relative_to(server._FILE_ROOTS["volume"])
    videos_rel = server._FILE_ROOTS["staged_videos"].relative_to(server._FILE_ROOTS["volume"])
    check(str(photos_rel) == "staged_photos", f"got {photos_rel}")
    check(str(videos_rel) == "social/staged_videos", f"got {videos_rel}")


def test_approval_survives_a_simulated_redeploy_window():
    """Literal regression test for the COLOR1001-class scenario: stage a
    video under the (now volume-backed) staged_videos root, then run the
    real `_execute_staged_action` apply path for type=listing_video and
    confirm it finds the file and calls upload_listing_video -- proving a
    video staged before a redeploy is still reachable after one, since the
    volume (unlike the old hardcoded local dir) survives a redeploy."""
    listing_id = 999001
    root = server._FILE_ROOTS["staged_videos"] / str(listing_id)
    root.mkdir(parents=True, exist_ok=True)
    fname = "showcase.mp4"
    (root / fname).write_bytes(b"not a real video, just needs to exist on disk")
    try:
        with patch.object(server, "EtsyAPIClient") as MockClient:
            instance = MockClient.return_value
            instance.upload_listing_video.return_value = {"listing_video_id": 555, "rank": 1}
            result = server._execute_staged_action({
                "type": "listing_video",
                "payload": {"listing_id": listing_id, "path": f"{listing_id}/{fname}", "rank": 1},
            })
        check(result["listing_id"] == listing_id, f"got {result}")
        check(result["etsy"]["listing_video_id"] == 555, f"got {result}")
        check(instance.upload_listing_video.called, "upload_listing_video must actually be invoked once the file resolves")
        called_path = instance.upload_listing_video.call_args[0][1]
        check(str(root / fname) == called_path, f"expected the resolved staged path {root / fname}, got {called_path}")
    finally:
        (root / fname).unlink(missing_ok=True)


def test_missing_staged_video_still_raises_file_not_found():
    # Confirms the fix didn't accidentally weaken the existing "file
    # genuinely absent" guard -- FileNotFoundError must still fire, not
    # silently resolve to some other path.
    listing_id = 999002
    threw = False
    try:
        with patch.object(server, "EtsyAPIClient"):
            server._execute_staged_action({
                "type": "listing_video",
                "payload": {"listing_id": listing_id, "path": f"{listing_id}/does_not_exist.mp4", "rank": 1},
            })
    except FileNotFoundError:
        threw = True
    check(threw, "a genuinely missing staged video must still raise FileNotFoundError")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("VIDEO STAGING DURABILITY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIDEO STAGING DURABILITY TESTS OK — videos/studio_uploads/staged_videos now "
          "resolve under the persistent volume when mounted (the COLOR1001-class fix), "
          "and a video staged before a simulated redeploy is still found and uploaded "
          "by the listing_video approval handler afterward.")


if __name__ == "__main__":
    run()
