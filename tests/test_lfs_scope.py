"""Git LFS takes the big media, and nothing that can't follow a pointer (2026-10-29).

Three readers fetch the repo without LFS and would get a 130-byte pointer
instead of the file: Railway's build of the server (the voice model in
tools/api_server/static), the public print viewer on GitHub Pages
(tools/viewer/, data/plate_stills/), and the desktop build (desktop/). Tests
read the 3MF fixtures at the top of openscad_models/. This checks
.gitattributes routes none of those to LFS, still routes the media it is for,
and that the pre-push hook that uploads LFS files is in the hooks directory
git actually runs (.githooks, core.hooksPath).
"""
import os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_failures: list[str] = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


def lfs(path):
    out = subprocess.run(["git", "check-attr", "filter", "--", path], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return out.strip().endswith(": lfs")


def test_what_cannot_follow_a_pointer_stays_ordinary():
    for p in ["tools/api_server/static/vendor/piper-voices/en/en_US/amy/medium/en_US-amy-medium.onnx",
              "tools/api_server/static/x.png", "tools/viewer/jobs/x.js", "tools/viewer/x.png",
              "data/plate_stills/x.jpg", "desktop/build/icon.png", "desktop/x.mp4",
              "openscad_models/label_tile.3mf", "openscad_models/dumpling_clicker.3mf",
              "openscad_models/x/model.stl", "tests/fixtures/x.png", "assets/fonts/x.ttf"]:
        check(not lfs(p), f"{p} would go to LFS, and its reader can't follow a pointer")


def test_the_media_it_is_for_goes_to_lfs():
    for p in ["openscad_models/clickers/gingerbread_tin/images/tin_top.png",
              "openscad_models/christmas_village/x/v2/model.3mf", "openscad_models/video/a.mp4",
              "openscad_models/x/images/a.jpg", "business/listing-videos/a.mp4", "data/social/a.mp4"]:
        check(lfs(p), f"{p} should go to LFS")


def test_lfs_hooks_are_where_git_runs_them():
    for h in ["pre-push", "post-checkout", "post-commit", "post-merge"]:
        f = ROOT / ".githooks" / h
        check(f.exists() and os.access(f, os.X_OK), f".githooks/{h} missing or not executable")
        check(f.exists() and f"git lfs {h}" in f.read_text(), f".githooks/{h} does not call git lfs {h}")


def run():
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("LFS SCOPE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("LFS SCOPE TESTS OK -- big media goes to LFS, nothing the deploy, the viewer, the desktop build or the tests read does, and the upload hook is where git runs it.")


if __name__ == "__main__":
    run()
