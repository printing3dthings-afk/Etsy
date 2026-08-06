"""
Files screen deep audit (page-by-page campaign round 2, 2026-08-06).

The Files screen's "Download everything from GitHub" link used to hardcode
this exact dev session's branch name
(archive/refs/heads/claude/etsy-automation-agents-WFAPU.zip) directly in
frank_hud_mockup.py. tools/check_default_branch.py already exists as the
documented single source of truth for "which branch is the real active one"
(EXPECTED_DEFAULT_BRANCH -- see that module's docstring on the 2026-07-10
incident where GitHub's configured default_branch silently drifted to a
stale branch and cron jobs ran old code for an unknown period). Two
independent hardcoded copies of the same fact -- one in the CI drift-check
constant, one baked into the HTML template -- could silently diverge:
Scott updates EXPECTED_DEFAULT_BRANCH when the active branch legitimately
changes (per that module's own instructions), with nothing forcing him to
remember the frontend link too, so the download button would 404 the next
time the branch changes or gets deleted after a merge.

Fix: render_frank_hud() now substitutes %%GITHUB_DEFAULT_BRANCH%% from
check_default_branch.EXPECTED_DEFAULT_BRANCH, the same constant the CI
check already treats as authoritative -- one source of truth instead of two.

Run: python tests/test_github_download_link_branch_sync.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import check_default_branch  # noqa: E402
import frank_hud_mockup  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_no_hardcoded_branch_literal_remains_in_the_source():
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text(encoding="utf-8")
    check("archive/refs/heads/%%GITHUB_DEFAULT_BRANCH%%.zip" in src,
          "expected the GitHub download link to use the %%GITHUB_DEFAULT_BRANCH%% placeholder")
    check("archive/refs/heads/claude/etsy-automation-agents-WFAPU.zip" not in src,
          "found a hardcoded branch name literal baked into the template -- this is exactly "
          "the two-copies-of-the-same-fact bug this test guards against")


def test_render_frank_hud_substitutes_the_real_default_branch():
    frank_hud_mockup._frank_html_cache = None  # force a fresh render
    html = frank_hud_mockup.render_frank_hud()
    check("%%GITHUB_DEFAULT_BRANCH%%" not in html, "placeholder must not leak into rendered output")
    expected_url = (
        "https://github.com/printing3dthings-afk/Etsy/archive/refs/heads/"
        f"{check_default_branch.EXPECTED_DEFAULT_BRANCH}.zip"
    )
    check(expected_url in html,
          f"expected the download link to use check_default_branch.EXPECTED_DEFAULT_BRANCH "
          f"({check_default_branch.EXPECTED_DEFAULT_BRANCH!r}), url not found in rendered HTML")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("GITHUB DOWNLOAD LINK BRANCH SYNC TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("GITHUB DOWNLOAD LINK BRANCH SYNC TESTS OK — the Files screen's download-everything "
          "link derives its branch name from check_default_branch.EXPECTED_DEFAULT_BRANCH, the "
          "same source of truth the CI drift-check already uses, instead of an independently "
          "hardcoded literal that could silently diverge from it.")


if __name__ == "__main__":
    run()
