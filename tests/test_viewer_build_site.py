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


def _boot_code(js: str) -> str:
    """The boot block with its comments stripped.

    Twice now a test here has matched the prose explaining a rule rather than
    the code obeying it -- the comment above the boot says initScene() used to
    run FIRST, which is exactly the string an ordering check looks for.
    """
    block = js[js.index("} else {", js.index("No jobs found")):]
    return "\n".join(re.sub(r"//.*$", "", ln) for ln in block.split("\n"))


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


def test_real_mode_hides_only_infill_and_skirt():
    """The see-through-shell bug.

    Hiding the inner perimeter and the solid infill looked reasonable -- the
    outer wall is in front of them -- and produced dark speckle all over the
    part, because beads are open tents and a one-bead shell has gaps you can
    see the unlit far wall through. Both walls have to stay.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    m = re.search(r"var REAL_HIDDEN = \{([^}]*)\}", js)
    check(m is not None, "REAL_HIDDEN is gone")
    if m:
        hidden = set(re.findall(r"(\d+)\s*:", m.group(1)))
        check("1" not in hidden,
              "real mode hides the inner perimeter again -- the shell goes "
              "one bead thick and speckles")
        check("4" not in hidden,
              "real mode hides solid infill again -- top and bottom surfaces "
              "lose their backing")
        check(hidden == {"3", "9"},
              "real mode hides %s; it should hide exactly internal infill (3) "
              "and skirt (9)" % sorted(hidden))


def test_solo_framing_survives_the_functions_that_fight_it():
    """Three separate ordering bugs, all of which produced a wrong picture with
    no error at all.

    frameJob() re-shows the gantry and Y rails as part of rescaling the head,
    so anything that calls it has to apply the framing afterwards.
    updateCutaway() runs every frame and re-asserts AMS visibility, so it has
    to know about solo or it undoes the hiding one tick later. And leaving solo
    without re-framing leaves the camera under the bed, because a finished
    print sits a part-height below z=0 once the bed has dropped.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")

    m = re.search(r"function setRealFraming\(f\) \{(.*?)\n\}", js, re.S)
    check(m is not None, "setRealFraming is gone")
    if m:
        body = m.group(1)
        fs, ar = body.find("frameSolo"), body.find("applyRealMode")
        check(fs != -1 and ar != -1 and fs < ar,
              "setRealFraming must call frameSolo BEFORE applyRealMode -- "
              "frameJob/frameSolo re-show the gantry")

    m2 = re.search(r"function updateCutaway\(\) \{(.*?)\n\}", js, re.S)
    check(m2 is not None and "realFraming" in m2.group(1),
          "updateCutaway no longer consults the solo framing -- it will "
          "re-show the AMS every frame")

    m3 = re.search(r"function applyRealMode\(\) \{(.*?)\n\}", js, re.S)
    check(m3 is not None and "_wasSolo" in m3.group(1) and "frameJob" in m3.group(1),
          "applyRealMode no longer re-frames when leaving solo -- the camera "
          "is left below the bed looking at its underside")


def test_layer_banding_is_antialiased_and_measured():
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    check("fwidth(vZmm)" in js,
          "layer banding lost its screen-space fade -- 0.2mm bands at ~1px "
          "alias into surface noise")
    check("function layerPitchMm" in js,
          "layer pitch is no longer measured off the plate's own layers")


def test_the_still_is_never_shown_mid_print():
    """The still is a photograph of the FINISHED part.

    Showing it while the scrub sits at layer 50 would be a picture of
    something the machine has not built yet -- the exact class of thing
    CLAUDE.md's first rule forbids. Verified live too (scrub back from the
    end and the live view returns), but the condition is guarded here so it
    cannot be quietly dropped.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    m = re.search(r"function syncStill\(\) \{(.*?)\n\}", js, re.S)
    check(m is not None, "syncStill is gone")
    if m:
        body = m.group(1)
        check("printIsComplete()" in body,
              "syncStill no longer requires the print to be complete -- the "
              "still could be shown over an unfinished print")
        check("realFraming === 'solo'" in body,
              "the still is no longer restricted to part-only framing")
        check("stillOk[currentId] === true" in body,
              "the still is shown without confirming the image actually loaded")

    m2 = re.search(r"function printIsComplete\(\) \{(.*?)\n\}", js, re.S)
    check(m2 is not None and "play.seg" in m2.group(1) and "nSeg" in m2.group(1),
          "printIsComplete no longer compares the played segment against the "
          "job's total")


def test_the_plate_is_not_offset_twice():
    """The bug that put the build plate a bed-width outside the machine.

    buildBed() used to place a CENTRED box, so it took the (X/2, Y/2) offset
    its caller hands it. plateShape() is authored in plate coordinates -- 0..X,
    0..Y, the same space the toolpath is in -- so applying that offset again
    slides the plate a whole bed clear of the chamber. Nothing errors; the
    plate simply renders out in the room.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    body = re.search(r"function buildBed\(X, Y, ox, oy\) \{(.*?)\n\}", js, re.S)
    check(body is not None, "buildBed is gone")
    if body:
        for name in ("body", "plate"):
            m = re.search(name + r"\.position\.set\(([^,]+),", body.group(1))
            check(m is not None and m.group(1).strip() == "0",
                  "%s.position takes an x offset -- plateShape() is already in "
                  "plate coordinates, so this draws the plate off the machine"
                  % name)


def test_the_plate_normal_map_is_a_normal_map():
    """A height field handed to `normalMap` is not a subtle mistake.

    The shader reads rgb*2-1 as a tangent-space vector. Flat grey decodes to
    (0,0,0) -- degenerate -- and every slightly-lighter blob decodes to a
    steeply tilted facet that catches a hard specular. Every plate rendered as
    light-grey blotches on black, which reads as a colour bug and is not one.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    check("function heightToNormal(" in js,
          "heightToNormal is gone -- something is feeding a raw height canvas "
          "into normalMap again")
    m = re.search(r"new THREE\.CanvasTexture\(heightToNormal\(", js)
    check(m is not None,
          "the normal texture is built straight from the height canvas")


def test_plate_guides_are_annotation_and_say_so():
    """Real-print mode is 'what this looks like in the machine'.

    No Bambu plate has an orange reserved-corner rectangle or a 32 mm ruling
    painted on it, so the guides have to go when the guides would be a lie.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    check("grid.visible = !real" in js,
          "the printable-area guides are no longer hidden in real-print mode")
    check("grid.visible = colorMode !== 'real'" in js,
          "rebuilding the bed (switching plate or machine) would paint the "
          "guides back on in real-print mode")


def test_plate_numbers_match_bambus_own_p1s_profile():
    """256 x 256 printable, 18 x 28 mm reserved at the front-left corner.

    Both read out of Bambu's shipped machine profiles, not from memory. The
    viewer and tools/plate_audit.py have to agree on them -- a viewer drawing
    one reserved corner while the audit checks another is worse than neither.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    check("var EXCLUDE_W = 18, EXCLUDE_D = 28;" in js,
          "the viewer's reserved corner is no longer 18 x 28 mm")
    audit = (ROOT / "tools" / "plate_audit.py").read_text(encoding="utf-8")
    check("EXCLUDE = (0.0, 0.0, 18.0, 28.0)" in audit,
          "plate_audit's reserved corner drifted from the viewer's")
    check("BED = 256.0" in audit, "plate_audit's plate is no longer 256 mm")


def test_every_plate_in_the_table_can_actually_be_drawn():
    """A plate whose grain has no entry renders as the fallback silently."""
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    table = re.search(r"var PLATES = \{(.*?)\n\};", js, re.S)
    grains = re.search(r"var GRAIN = \{(.*?)\n\};", js, re.S)
    check(table is not None and grains is not None, "PLATES or GRAIN is gone")
    if table and grains:
        used = set(re.findall(r"grain: '(\w+)'", table.group(1)))
        have = set(re.findall(r"^\s*(\w+):\s*\{", grains.group(1), re.M))
        check(used <= have, "plates with no grain profile: %s" % (used - have))


def test_the_ams_spool_keeps_the_axis_updateAMS_assumes():
    """updateAMS() scales x/z for the falling coil radius and spins y.

    Both only mean what they are supposed to mean if the coil is a plain
    CylinderGeometry (axis = local Y) under a parent turned onto X. Rebuild it
    as anything else and the spool silently gets NARROWER as it empties
    instead of thinner, and tumbles end over end instead of turning.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    body = re.search(r"function buildAMS\(.*?\n\}", js, re.S)
    check(body is not None, "buildAMS is gone")
    if body:
        b = body.group(0)
        check("hub.rotation.z = Math.PI / 2" in b,
              "the spool parent no longer lays the coil along X")
        m = re.search(r"var fil = new THREE\.(\w+)", b)
        check(m is not None and m.group(1) == "Mesh", "the coil is not a Mesh")
        check("new THREE.CylinderGeometry(99, 99, 54" in b,
              "the coil is no longer a Y-axis cylinder -- updateAMS's scale "
              "and spin stop meaning radius and rotation")
    check("sl.spool.scale.set(k, 1, k)" in js,
          "updateAMS no longer scales the coil radius on x/z")


def test_the_ams_reel_hides_as_one_piece():
    """Three pairs of empty discs hanging in the dome reads as a fault.

    Hiding a slot has to take its flanges with it, not just the coil and the
    core -- which is what happened the first time the flanges were split out
    into their own meshes so they would stop shrinking with the filament.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    check("amsGroup.userData.reels = reels" in js,
          "the flanges are not registered, so nothing can hide them with "
          "their slot")
    check("userData.reels || [])[i] || []).forEach" in js,
          "buildAMSState hides the coil and core but leaves the flanges")


def test_the_ams_has_its_dome():
    """The shape that makes an AMS recognisable.

    A half-cylinder along the spool row, so the arch follows the spool circles.
    It was a flat-lidded box, which from above read as an empty tray.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    body = re.search(r"function buildAMS\(.*?\n\}", js, re.S)
    if body:
        b = body.group(0)
        check("0, Math.PI)" in b and "dome.rotation.z = Math.PI / 2" in b,
              "the dome is no longer a half-cylinder lying along the spool row")
        check("cap.rotation.set(0, Math.PI / 2, Math.PI / 2)" in b,
              "the dome end caps lost the z turn -- rotation.y alone stands "
              "them up as flat sheets off the back instead of closing the arch")
        check("bandShape.holes.push" in b and "lipShape.holes.push" in b,
              "the body's top band is a filled plate again -- it caps the box "
              "and hides the bottom half of every spool")


def test_the_page_says_where_the_ams_was_drawn_from():
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    check("product " in js and "spool colours are illustrative" in js,
          "the Printer panel no longer says the AMS spool colours are "
          "illustrative -- it renders well enough now to be mistaken for a "
          "reading of the real machine")


def test_the_height_readback_is_hinted():
    """The seven-and-a-half-second stall, made impossible to reintroduce.

    heightToNormal() draws a height field on a canvas and reads it straight
    back with getImageData. Without willReadFrequently the canvas is
    GPU-backed and that single read forces a full readback -- measured at
    7,491 ms for ONE plate, inside initScene(), which runs before the plate
    list, the panels or the replay. The page sat on its loading spinner for
    the entire length of a phone screen recording and said nothing, because
    nothing was broken; it was still working.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    reads = [m for m in re.finditer(r"\.getImageData\(", js)]
    check(len(reads) == 1,
          "%d canvas readbacks in app.js -- there is exactly one, in "
          "heightToNormal, and it is hinted. A second one needs the same "
          "hint and its own reason for existing." % len(reads))
    if reads:
        before = js[:reads[0].start()]
        owner = re.findall(r"^function (\w+)\(", before, re.M)
        check(owner and owner[-1] == "heightToNormal",
              "the readback moved out of heightToNormal (now in %s)"
              % (owner[-1] if owner else "?"))
    maker = re.search(r"function grainNormalMap\(.*?\n\}", js, re.S)
    # The literal call, not the word: the comment above it explains why the
    # hint is there and matching that made this test pass with the hint gone.
    hinted = maker is not None and re.search(
        r"getContext\(\s*'2d'\s*,\s*\{\s*willReadFrequently:\s*true", maker.group(0))
    check(bool(hinted),
          "the canvas heightToNormal reads back is no longer created with "
          "willReadFrequently -- that single read becomes a full GPU readback, "
          "measured at 7,491 ms")


def test_the_normal_map_is_built_once_per_grain():
    """It depends on the grain, not the colour, and six plates share five."""
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    check("_NORMAL_MAPS" in js and "if (_NORMAL_MAPS[grain])" in js,
          "the plate normal map is rebuilt on every plate switch again")


def test_a_boot_failure_reaches_the_screen():
    """A viewer that cannot say what went wrong is worse than one that
    crashed visibly.

    initScene() runs first, so anything it throws takes the plate list, the
    panels and the replay with it -- leaving a spinner, three empty panels and
    no explanation anywhere on the page.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    check("function bootFailed(" in js, "there is no boot error reporter")
    boot = _boot_code(js)
    check(boot.count("catch (e) { bootFailed(e); throw e; }") == 2,
          "both halves of the boot -- the UI paint and the scene build -- "
          "have to report, or a failure in either one is a silent spinner")


def test_plate_and_ams_failures_are_not_fatal():
    """Both are decoration. Neither may take the viewer down."""
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    check("plate finish fell back to flat colour" in js,
          "a failure building the plate finish is fatal again")
    check("console.warn('AMS not drawn:'" in js,
          "a failure building the AMS is fatal again")
    check("if (maps) {" in js,
          "buildBed still assumes plateSurface returned textures")


def test_app_js_is_cache_busted_on_its_content():
    """A fix that never reaches the device is not a fix.

    The published path stays "app.js" so an update replaces the file, but a
    webview that cached the old bytes keeps serving them across app restarts.
    On 2026-09-19 a fix shipped, the phone was quit and reopened, and the
    phone was still running the previous build. The query string is the only
    thing that changes the cache key.
    """
    with tempfile.TemporaryDirectory() as td:
        out = _build(Path(td))
        html = (out / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<script src="app\.js\?v=([0-9a-f]{10})">', html)
        check(m is not None, "app.js is loaded without a content version")
        if m:
            import hashlib
            want = hashlib.sha1((ROOT / "tools" / "viewer" / "app.js").read_bytes()
                                ).hexdigest()[:10]
            check(m.group(1) == want,
                  "the version is not app.js's own content hash, so editing "
                  "app.js would not change it")
        check((out / "app.js").exists(),
              "the query string must not change the file's published path")


def test_a_renamed_app_script_tag_fails_the_build():
    """Same trap as the three.js rewrite: a str.replace that no longer matches
    is a silent no-op, and the symptom is a stale page months later."""
    src = (ROOT / "tools" / "viewer" / "virtual_p1s.html").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        broken = Path(td) / "virtual_p1s.html"
        broken.write_text(src.replace('<script src="app.js">',
                                      '<script defer src="app.js">'),
                          encoding="utf-8")
        original = build_site.HERE
        try:
            build_site.HERE = Path(td)
            (Path(td) / "vendor").mkdir()
            shutil.copy2(original / "vendor" / "three.min.js",
                         Path(td) / "vendor" / "three.min.js")
            shutil.copy2(original / "app.js", Path(td) / "app.js")
            raised = False
            try:
                build_site.build(Path(td) / "site")
            except SystemExit:
                raised = True
            check(raised, "a renamed app.js script tag builds silently, which "
                          "ships a page that can never be updated on a device "
                          "that cached it")
        finally:
            build_site.HERE = original


def test_the_ui_paints_before_the_scene_is_built():
    """initScene() is the expensive one and it used to run first.

    A slow or failing scene left the plate list, the panels and the transport
    blank behind a spinner -- the page looked dead when it was only busy.
    Measured under a 6x CPU throttle: the plate list appeared at 14,106 ms
    before this and 540 ms after.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    boot = _boot_code(js)
    ui = boot.index("initUI()")
    scene = boot.index("initScene()")
    check(ui < scene, "initScene runs before the UI is painted again")
    check("function bootStage(" in js and js.count("bootStage(") >= 3,
          "the loading overlay no longer names its stage, so a screenshot of "
          "a stall cannot say where it stalled")
    check("function buildChamber(bed) {\n  // Reachable from the machine and plate"
          in js or "if (!scene) { return; }" in js,
          "nothing guards the frame in which the pickers are live but the "
          "scene does not exist yet")


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
