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
import re
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


def test_the_limits_dot_can_actually_be_cleared():
    """Lives here because this is the viewer's only source-integrity test file.

    The unread dot on the Limits tab is driven by a data-unread attribute in
    the HTML and removed by a querySelector in app.js. Those two strings have
    to agree, and nothing else checks that they do -- rename the tab's
    data-pane value on one side only and the dot sticks forever, silently, on
    the one tab that carries every caveat keeping this page honest. Neither
    file errors; the cue just stops meaning anything.
    """
    viewer = ROOT / "tools" / "viewer"
    html = (viewer / "virtual_p1s.html").read_text(encoding="utf-8")
    js = (viewer / "app.js").read_text(encoding="utf-8")

    check('data-pane="limits" data-unread="1"' in html,
          "the Limits tab no longer carries the unread marker")
    check('[data-unread="1"]::after' in html,
          "nothing renders the unread dot -- the attribute would be invisible")
    check('querySelector(\'[data-pane="limits"]\')' in js,
          "app.js does not target the Limits tab by the selector the HTML uses "
          "-- the dot would never clear")
    check("removeAttribute('data-unread')" in js,
          "app.js never removes the marker")
    check(js.count("localStorage") >= 2 and js.count("catch (e)") >= 2,
          "localStorage use is not guarded -- a private window would throw and "
          "take the tab handler down with it")


def test_every_material_colour_goes_through_the_srgb_conversion():
    """three r128 has no automatic colour management.

    A hex authored in sRGB and handed straight to a material is used as-is in
    linear lighting maths, and the whole scene renders washed out and milky.
    Every colour in app.js goes through lin() for that reason. A future raw
    `{color: 0x...}` would not error, would not look obviously wrong in
    isolation, and would quietly be the wrong brightness.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    raw = re.findall(r"new THREE\.Mesh\w*Material\(\{[^}]*?color:\s*(0x[0-9a-fA-F]+)", js)
    # the backdrop and environment panels are authored in the canvas/CSS space
    # and converted at their own call sites, so 0xffffff (pure white, identical
    # in both spaces) is the only literal allowed through here
    stray = [c for c in raw if c.lower() not in ("0xffffff",)]
    check(not stray,
          "material colours bypassing lin(): %s -- these render at the wrong "
          "brightness with sRGB output" % stray)


def test_renderer_keeps_the_colour_and_shadow_pipeline():
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    for needle, why in [
        ("renderer.outputEncoding = THREE.sRGBEncoding",
         "sRGB output gone -- the whole scene loses its tone response"),
        ("THREE.ACESFilmicToneMapping", "ACES curve gone -- highlights clip flat"),
        ("renderer.shadowMap.enabled = true", "shadows disabled"),
        ("scene.environment", "no environment map -- metal renders near black"),
    ]:
        check(needle in js, why)


def test_shadow_map_is_not_rebuilt_every_frame():
    """The 4.4x frame-time regression, made impossible to reintroduce silently.

    With autoUpdate left on, the shadow pass re-renders the whole
    200k-triangle toolpath every frame and produces a bit-identical map
    between layer changes. Measured at 148ms -> 647ms median. Nothing about
    that failure is visible: the picture is correct, only slow.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    check("renderer.shadowMap.autoUpdate = false" in js,
          "shadowMap.autoUpdate is not disabled -- the per-frame shadow "
          "re-render is back")
    check("shadowDirty" in js and "renderer.shadowMap.needsUpdate = true" in js,
          "autoUpdate is off but nothing schedules an update -- shadows would "
          "freeze at their first frame, which is worse than the regression")


def test_the_page_still_says_the_lighting_is_invented():
    """The better this renders, the easier it is to mistake for a photograph."""
    html = (ROOT / "tools" / "viewer" / "virtual_p1s.html").read_text(encoding="utf-8")
    check("studio rig" in html,
          "the Limits tab no longer says the lighting is an invented studio "
          "rig rather than this machine's actual chamber LED")


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
