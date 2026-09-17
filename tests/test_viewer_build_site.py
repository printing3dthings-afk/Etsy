"""Guards the standalone-site build, which has two ways to fail silently.

1. The three.js <script src> in virtual_p1s.html is rewritten to a local copy
   so the built folder works with no network. If that URL ever changes, a
   plain str.replace() becomes a no-op and the build keeps succeeding while
   quietly shipping a site that needs the internet. build_site.py raises
   instead; this proves it.
2. The page is wrapped in a real document because the Artifact host supplies
   the doctype/charset/viewport that virtual_p1s.html omits. Without the
   viewport tag a phone lays the page out at 980px -- the exact fiction that
   made every local mobile measurement wrong earlier in this project.
"""
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "viewer"))

import build_site  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _build(tmp: Path) -> Path:
    out = tmp / "site"
    build_site.build(out)
    return out


def test_built_page_has_the_head_the_artifact_host_would_have_supplied():
    with tempfile.TemporaryDirectory() as td:
        html = (_build(Path(td)) / "index.html").read_text(encoding="utf-8")
    check(html.startswith("<!doctype html>"), "built page has no doctype")
    check('name="viewport"' in html,
          "no viewport meta -- a phone will lay this out at 980px")
    check('charset="utf-8"' in html, "no charset meta")


def test_three_js_is_local_not_the_cdn():
    with tempfile.TemporaryDirectory() as td:
        out = _build(Path(td))
        html = (out / "index.html").read_text(encoding="utf-8")
        check((out / "three.min.js").exists(),
              "three.min.js was not copied into the site")
        check("cdnjs.cloudflare.com" not in html,
              "built page still points at the three.js CDN -- not offline")
        check('src="three.min.js"' in html,
              "built page does not load the vendored three.js")


def test_a_changed_cdn_url_fails_the_build_instead_of_no_opping():
    """The real regression: rewrite silently matching nothing."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        real = build_site.CDN_THREE
        build_site.CDN_THREE = "https://example.invalid/three.min.js"
        try:
            _build(tmp)
        except SystemExit as e:
            check("silently did nothing" in str(e),
                  "build failed, but not with the explanation: %s" % e)
        else:
            _failures.append(
                "build succeeded with a CDN_THREE that matches nothing -- the "
                "rewrite no-opped and the site would need the network")
        finally:
            build_site.CDN_THREE = real


def test_missing_vendor_copy_is_a_hard_failure():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        vendor = build_site.HERE / "vendor" / "three.min.js"
        stash = tmp / "three.stashed.js"
        shutil.move(str(vendor), str(stash))
        try:
            _build(tmp)
        except SystemExit as e:
            check("missing" in str(e) and "offline" in str(e),
                  "vendor-missing error does not say why it matters: %s" % e)
        else:
            _failures.append(
                "build succeeded without vendor/three.min.js -- the site would "
                "fall back to the CDN with no warning")
        finally:
            shutil.move(str(stash), str(vendor))


def test_build_refuses_to_ship_a_site_with_no_plates():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        idx = build_site.HERE / "jobs" / "index.js"
        stash = tmp / "index.stashed.js"
        shutil.move(str(idx), str(stash))
        try:
            _build(tmp)
        except SystemExit as e:
            check("no plate payloads" in str(e),
                  "empty-jobs error is not the expected one: %s" % e)
        else:
            _failures.append(
                "build succeeded with no jobs/index.js -- the page would load "
                "and then have nothing to draw")
        finally:
            shutil.move(str(stash), str(idx))


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append("%s raised:\n%s" % (fn.__name__, traceback.format_exc()))
    if _failures:
        print("VIEWER BUILD SITE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIEWER BUILD SITE TESTS OK -- the standalone site is a real document "
          "and really runs offline, and both claims fail loudly if they stop "
          "being true.")


if __name__ == "__main__":
    run()
