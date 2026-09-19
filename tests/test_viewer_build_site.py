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


def _page_hash() -> str:
    """Everything that decides what the built page is, including the builder."""
    import hashlib
    viewer = ROOT / "tools" / "viewer"
    return hashlib.sha1(
        (viewer / "app.js").read_bytes()
        + (viewer / "virtual_p1s.html").read_bytes()
        + (viewer / "build_site.py").read_bytes()).hexdigest()[:10]


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
    # 2026-09-19: this used to require the literal string "realFraming" here.
    # It asked for the right thing in the wrong way -- the condition was
    # inlined in three places and updateCutaway's copy did not know about
    # part-only, so the AMS came back one tick after being hidden. It is one
    # predicate now, and the guard is that updateCutaway consults it rather
    # than that it spells the condition out itself.
    check(m2 is not None and "machineHidden()" in m2.group(1),
          "updateCutaway no longer consults machineHidden() -- it runs every "
          "frame and will re-show the AMS one tick after it is hidden")

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


def test_the_app_is_an_external_script_at_a_content_hashed_name():
    """Three approaches, two of which failed on real hardware (2026-09-19).

    ``app.js``          a phone kept the cached file across a force-quit, so a
                        shipped fix never ran.
    ``app.js?v=hash``   untestable -- the page was cached too, so we never
                        learned whether the query worked.
    inlined in the page the script is served intact (verified by reading the
                        published HTML back) and does not execute. The host
                        does not run inline script in a multi-file artifact.

    A new filename is the one option with no ambiguity: a URL that has never
    been requested cannot come from a cache, and an external file is what
    demonstrably executes here.
    """
    viewer = ROOT / "tools" / "viewer"
    want = _page_hash()
    with tempfile.TemporaryDirectory() as td:
        out = _build(Path(td))
        # A previous build's bundle, standing in for the real case: the output
        # folder is reused and every stale copy is a file the host would still
        # serve and nothing would ever refresh.
        (out / "app.deadbeef00.js").write_text("// stale", encoding="utf-8")
        out = _build(Path(td))
        html = (out / "index.html").read_text(encoding="utf-8")
        names = sorted(p.name for p in out.glob("app*.js"))
    check('<script src="app.%s.js"></script>' % want in html,
          "the app script is not loaded from a content-hashed filename")
    check(names == ["app.%s.js" % want],
          "expected exactly one app bundle in the build, got %s -- every "
          "earlier copy is a file the host would still serve and nothing "
          "would ever refresh" % names)
    check("function initScene" not in html,
          "the app is inlined into the page again -- the host does not "
          "execute inline script in a multi-file artifact, so the page would "
          "render and do nothing at all")
    m = re.search(r'id="buildchip">build ([0-9a-f]{10})<', html)
    check(m is not None and m.group(1) == want,
          "the page no longer carries a static build stamp matching the page "
          "source, so a screenshot of a broken page cannot say which build "
          "it is -- and that chip is how we finally learned a fix had landed")
    check("three.min.js" in html,
          "three.js should stay external and unhashed -- 600 KB that genuinely "
          "never changes is exactly what you want a cache to keep")


def test_a_renamed_app_script_tag_fails_the_build():
    """Same trap as the three.js rewrite: a str.replace that no longer matches
    is a silent no-op. Here it would ship a page with no application at all."""
    viewer = ROOT / "tools" / "viewer"
    src = (viewer / "virtual_p1s.html").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "virtual_p1s.html").write_text(
            src.replace('<script src="app.js"></script>',
                        '<script defer src="app.js"></script>'), encoding="utf-8")
        (tmp / "vendor").mkdir()
        shutil.copy2(viewer / "vendor" / "three.min.js", tmp / "vendor" / "three.min.js")
        shutil.copy2(viewer / "app.js", tmp / "app.js")
        (tmp / "jobs").mkdir()
        shutil.copy2(viewer / "jobs" / "index.js", tmp / "jobs" / "index.js")
        original = build_site.HERE
        try:
            build_site.HERE = tmp
            raised = False
            try:
                build_site.build(tmp / "site")
            except SystemExit:
                raised = True
            check(raised, "a renamed app.js script tag builds silently, and "
                          "the page it ships has no application in it")
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


def test_the_build_stamp_identifies_the_built_page_and_survives_the_app():
    """The one tool meant to end the guessing, and it had two defects.

    It hashed app.js and the HTML but not build_site.py -- so the inlined
    build and the hashed-filename build that replaced it, which differed
    ONLY in build_site.py, both stamped b9dd3ff2a2 and a photograph of the
    header could not say which one was on screen.

    And paintJobList() overwrote the chip with the plate counts the moment
    the app ran, destroying the version exactly when it was still wanted.
    The counts have their own span now.
    """
    viewer = ROOT / "tools" / "viewer"
    want = _page_hash()
    with tempfile.TemporaryDirectory() as td:
        html = (_build(Path(td)) / "index.html").read_text(encoding="utf-8")
    check('id="buildchip">build %s<' % want in html,
          "the build stamp does not cover everything that decides what the "
          "built page is -- two different pages can carry the same stamp")

    js = (viewer / "app.js").read_text(encoding="utf-8")
    check("$('buildchip')" not in js,
          "app.js writes to the build chip -- it is the only thing that says "
          "which build is on screen when the page is broken, so nothing in "
          "the app may overwrite it")
    check("$('platechip')" in js, "the plate counts lost their own span")


def test_the_app_announces_that_it_ran():
    """Two states look identical in a photo of a screen: 'the page updated but
    the script never executed' and 'the page did not update'. Telling them
    apart cost three round trips. The chip says which."""
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    head = js[:js.index("var TYPE_COLOR")]
    check("getElementById('buildchip')" in head and "running" in head,
          "the proof-of-life stamp is gone from the top of app.js")
    check("try {" in head and "catch" in head,
          "the proof-of-life stamp is not guarded -- a missing chip must "
          "never be the thing that stops the page")


def test_nothing_touches_THREE_before_the_guard_that_checks_for_it():
    """The friendly "three.js did not load" message was unreachable.

    `var _ray = new THREE.Raycaster()` sat at top level, so when three.js was
    missing the page threw a bare ReferenceError there -- before the boot
    block's `if (!window.THREE)` ever ran. The artifact was served without
    three.min.js for an entire evening and the only symptom anyone could see
    was a stuck spinner.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    # The whole file lives inside one IIFE, so its statements sit at brace
    # depth 1, not 0. Counting from 0 made the first version of this test pass
    # with the bug put straight back in -- caught by mutation, not by reading.
    lines = js.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("(function ()"))
    depth, bad = 0, []
    for n, line in enumerate(lines[start + 1:], start + 2):
        if line.strip().startswith("//"):
            depth += line.count("{") - line.count("}")
            continue
        # Char by char, because depth has to be measured AT the use site: a
        # one-line `function lin(h) { return new THREE.Color(h); }` opens and
        # closes on the same line and is not top-level code.
        for i, ch in enumerate(line):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            elif depth == 0 and line.startswith("new THREE.", i):
                bad.append("%d: %s" % (n, line.strip()[:70]))
    check(not bad,
          "THREE is used at top level, so the guard that reports it missing "
          "can never run: %s" % bad)


def test_any_uncaught_error_reaches_the_screen():
    """The boot block's try/catch cannot see a top-level throw."""
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    head = js[:js.index("var TYPE_COLOR")]
    check("addEventListener('error'" in head,
          "no global error handler at the top of app.js -- a throw before the "
          "boot block leaves the page on its spinner saying nothing")


def test_the_build_refuses_to_ship_without_three_js():
    """It is the one dependency the page cannot start without."""
    viewer = ROOT / "tools" / "viewer"
    with tempfile.TemporaryDirectory() as td:
        out = _build(Path(td))
        check((out / "three.min.js").exists(),
              "the build does not place three.min.js beside the page")
        size = (out / "three.min.js").stat().st_size
        check(size > 100_000,
              "three.min.js is %d bytes -- that is not the library" % size)


def test_the_bead_has_a_flat_top_not_a_ridge():
    """The "missed areas after printing" defect, reported 2026-09-19.

    The bead's cross-section was a tent: two shoulders at the layer floor, an
    apex at the layer top. That makes the top of every extrusion a zero-width
    RIDGE, and the shoulder normals exactly horizontal -- so seen from above,
    half of every bead shades from lit at the ridge to black at the shoulder
    and a solid top face renders as corduroy with gaps in it.

    Measured on the label tile's top face, the share of pixels dark enough to
    read as a gap rather than a tool mark: 15.0% with the ridge, 5.6% with a
    stadium profile, 2.2% with the fused profile that shipped.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    body = re.search(r"function buildJob\(raw\) \{.*?\n\}", js, re.S)
    check(body is not None, "buildJob is gone")
    if not body:
        return
    b = body.group(0)
    check("BEAD_PTS = 4" in b,
          "the bead is not four points across any more -- three is the tent "
          "whose ridge caused the defect")
    # 2026-09-19: was BEAD_IDX = 18 (three bands, an open trough). The bead is
    # a closed tube now -- see test_the_bead_is_a_closed_tube for why. What
    # this test is really about is the flat TOP, which is unchanged.
    check("BEAD_IDX = 24" in b, "the bead is not four bands any more")
    # two vertices sitting at ztop is what makes the top flat rather than a point
    tops = re.findall(r"vPos\[vi \* 3 \+ \d+\] *= ztop;", b)
    check(len(tops) == 2,
          "expected exactly two vertices at the layer top (the flat), found %d"
          % len(tops))
    check("var kf = " in b and "2.6 * hw" in b,
          "the flat-top fraction is gone or no longer derived from the layer "
          "height")
    # and the shoulders must still be the full bead width, or the part gets thin
    check("vPos[vi * 3]      = x + ax;" in b and "vPos[vi * 3 + 9]  = x - ax;" in b,
          "the bead's shoulders are no longer at the full half-width")


def test_the_draw_range_matches_the_bead():
    """Playback reveals the print by index count.

    setDrawRange(0, seg * N) and the index writer have to agree on N or the
    replay shows the wrong amount of print -- silently, and only part way
    through, which is the worst way to find out.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    m = re.search(r"setDrawRange\(0, seg \* (\d+)\)", js)
    check(m is not None, "the draw range no longer scales with the segment count")
    if m:
        check(m.group(1) == "24",
              "draw range steps by %s indices per segment but the bead writes "
              "18" % m.group(1))


def test_full_screen_takes_the_whole_tool_not_just_the_canvas():
    """A bare canvas is a picture; the transport and the plate list are what
    make it a tool, so #app is what goes fullscreen."""
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    html = (ROOT / "tools" / "viewer" / "virtual_p1s.html").read_text(encoding="utf-8")
    check('id="fullscreen"' in html, "there is no full screen button")
    check("getElementById('app')" in js and "requestFullscreen" in js,
          "full screen no longer targets the whole app grid")
    check("webkitRequestFullscreen" in js,
          "no webkit fallback -- Safari is the browser this is for")
    check("fsBtn.hidden = true" in js,
          "a browser without the Fullscreen API would be left with a button "
          "that does nothing")
    check("fullscreenchange" in js,
          "the button's label follows the call rather than the event, so a "
          "refused request would leave it lying")



def test_each_bead_squishes_into_the_layer_below():
    """The second half of "missed areas after printing", found 2026-09-19.

    A bead spanning exactly its own layer only touches its neighbour where the
    wall is vertical. On the cable clip's sloped top, consecutive beads step
    sideways and a wedge of nothing opens between them: measured straight-on at
    7.4px per band, 20 of 426 rows rendered pure black (mean under 25/255
    across a 300px span), while the vertical wall lower on the same part had no
    dark rows at all. Extending the bead 18% into the layer below -- the real
    squish of a 0.42mm extrusion into a 0.2mm gap -- took that to 4.

    The clamp matters as much as the overlap: the first layer has nothing to
    squish into, and without Math.max(0, ...) it sits behind the plate surface
    and z-fights the bed.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    body = re.search(r"function buildJob\(raw\) \{.*?\n\}", js, re.S)
    check(body is not None, "buildJob is gone")
    if not body:
        return
    b = "\n".join(re.sub(r"//.*$", "", ln) for ln in body.group(0).split("\n"))
    m = re.search(r"var zlow = ([^;]+);", b)
    check(m is not None, "the bead's floor is no longer computed as zlow")
    if not m:
        return
    expr = m.group(1)
    check("1.18" in expr,
          "the bead no longer reaches below its own layer, so a sloped wall "
          "opens a gap between every pair of layers again: %r" % expr)
    check("Math.max(0," in expr.replace(" ", "").replace("Math.max(0,", "Math.max(0,"),
          "the first layer is not clamped to the plate -- it will dip below "
          "z=0 and z-fight the bed: %r" % expr)
    # kf must be measured against the LAYER, not against the bead's new (taller)
    # extent -- the 2.2% top-face figure above was measured with lh, and reading
    # ztop-zlow here would silently widen the flat by 18% and re-smooth the top.
    kf = re.search(r"var kf = ([^;]+);", b)
    check(kf is not None and "ztop - zlow" not in kf.group(1),
          "kf is measured against the bead's overlapped extent instead of the "
          "layer height, which moves the top-face flat off its measured value")


def test_a_still_frame_is_rendered_at_full_resolution():
    """The harsh jagged layer lines, reported 2026-09-19.

    adaptResolution trades pixels for frame rate, which is right while
    something moves. But the loop renders every frame forever, so a device that
    once measured slow stayed ratcheted down on a STILL frame too -- the only
    frame anyone studies. Measured headless on the cable clip: an 884x426
    canvas backed by a 618x298 buffer, upscaled by the browser.

    Two halves, and the test guards both: settle to full resolution when
    nothing has moved, and do NOT sample frame time while settled -- an
    expensive still frame that ratchets dprScale down makes the next still
    frame worse, a loop that ends at DPR_MIN and stays there.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))

    ap = re.search(r"function applyPixelRatio\(\) \{(.*?)\n\}", src, re.S)
    check(ap is not None, "applyPixelRatio is gone")
    if ap:
        check("hiRes ?" in ap.group(1) or "hiRes?" in ap.group(1),
              "the still-frame pixel ratio no longer bypasses dprScale, so a "
              "device that measured slow once renders every still frame low")

    ad = re.search(r"function adaptResolution\(now, dt\) \{(.*?)\n\}", src, re.S)
    check(ad is not None, "adaptResolution is gone")
    if ad:
        first = [ln.strip() for ln in ad.group(1).split("\n") if ln.strip()][:1]
        check(first and first[0] == "if (hiRes) { return; }",
              "adaptResolution samples frame time while settled -- the "
              "expensive still frame ratchets dprScale down and the next still "
              "frame is worse: %r" % (first,))

    sr = re.search(r"function setResolution\(now\) \{(.*?)\n\}", src, re.S)
    check(sr is not None, "setResolution is gone")
    if sr:
        check("SETTLE_MS" in sr.group(1),
              "setResolution no longer waits out a settle window before going "
              "to full resolution")
        check("_ft.length = 0" in sr.group(1),
              "the frame-time samples are not cleared on a resolution change, "
              "so the next decision is made on a stale median from the other "
              "resolution")


def test_a_keyboard_scrub_does_not_stick_the_scrubbing_flag():
    """Found 2026-09-19 while the settle pass above refused to fire.

    The scrub's `input` handler sets play.scrubbing = true on every value
    change, including an arrow key -- and an arrow key never produces a
    pointerup. The flag stuck true for the rest of the session, which silently
    froze playback (tick() skips advancing while scrubbing) and pinned the
    render at low resolution. `change` fires on both a pointer release and a
    keyboard commit.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))
    m = re.search(r"\[([^\]]*?)\]\.forEach\(function \(t\) \{\s*"
                  r"sc\.addEventListener\(t, function \(\) \{ play\.scrubbing = false; \}\);",
                  src, re.S)
    check(m is not None, "nothing clears play.scrubbing any more")
    if m:
        check("'change'" in m.group(1),
              "play.scrubbing is only cleared by pointer events, so an arrow "
              "key leaves it stuck true forever: %r" % m.group(1))


def test_the_layer_darkening_fades_out_sooner_than_the_rounding():
    """Two fade curves, not one (2026-09-19).

    lp is the layer period in pixels, inverted: lp 0.5 is two pixels per layer,
    dead on Nyquist. Running the darkening and the normal bulge on one window
    of 0.30..0.85 left a hard albedo stripe at 60% strength at 1.8px per layer,
    which beats against the pixel grid into a diagonal crosshatch rather than
    reading as layer lines.

    They alias differently, so they get different windows. The darkening is a
    pure high-frequency albedo signal and must go first; the bulge is modulated
    by the lighting before it reaches the pixel, which costs it most of its
    contrast, and it is the half that makes a wall look printed.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))
    fade = re.search(r"lyFade = 1\.0 - smoothstep\(([0-9.]+), ([0-9.]+), lp\)", src)
    band = re.search(r"lyBand = 1\.0 - smoothstep\(([0-9.]+), ([0-9.]+), lp\)", src)
    check(fade is not None, "the normal bulge's fade curve is gone")
    check(band is not None,
          "the darkening shares the bulge's fade curve again -- it is the one "
          "that crosshatches, and it has to fade out first")
    if not (fade and band):
        return
    check(float(band.group(2)) < float(fade.group(2)),
          "the darkening now outlives the rounding (%s vs %s) -- backwards: a "
          "flat stripe survives past the zoom where a camera could resolve it"
          % (band.group(2), fade.group(2)))
    check(float(fade.group(2)) <= 0.5,
          "the rounding is carried past Nyquist (%s): below two pixels per "
          "layer there is nothing honest left to draw" % fade.group(2))
    check("mix(1.0, lb, lyBand)" in src,
          "the darkening is not applied on its own curve any more")


def test_part_only_hides_the_supports_not_just_the_machine():
    """The fourth view, asked for 2026-09-19.

    Real-print mode keeps supports on purpose -- they are printed plastic
    standing on the plate until you snap them off. Part-only answers a
    different question and must hide them, and the difference is not marginal:
    measured on the fairy house by extrusion move count, support material
    (34.4%) plus support interface (9.9%) is 44.3% of the whole plate. Looking
    at its roof with them on, nearly half of what is on screen is scaffolding,
    which is what "doesn't look like a real print" turned out to mean.

    Indices are into the slicer's own type list, which the payloads carry:
    3 internal infill, 7 support material, 8 support interface, 9 skirt/brim.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))
    m = re.search(r"var PART_HIDDEN = \{([^}]*)\}", src)
    check(m is not None, "PART_HIDDEN is gone -- part-only no longer hides "
                         "anything the plate does not keep")
    if not m:
        return
    hidden = set(re.findall(r"(\d+)\s*:", m.group(1)))
    for idx, what in (("3", "sparse infill"), ("7", "support material"),
                      ("8", "support interface"), ("9", "the skirt")):
        check(idx in hidden,
              "part-only no longer hides %s (type %s), so it is not showing "
              "the finished object any more" % (what, idx))
    # and real-print mode must NOT have quietly inherited this
    r = re.search(r"var REAL_HIDDEN = \{([^}]*)\}", src)
    check(r is not None and "7" not in set(re.findall(r"(\d+)\s*:", r.group(1))),
          "real-print mode now hides supports too -- that mode answers 'what "
          "is on the plate right now' and supports genuinely are")


def test_only_one_thing_decides_whether_the_machine_is_on_screen():
    """The AMS leak, found 2026-09-19 by listing the visible scene.

    updateCutaway() recomputed `solo` itself, every frame, and did not know
    about part-only -- so a 371mm AMS unit re-appeared one tick after
    setPartOnly() hid it, in the one view whose entire job is to show nothing
    but the part. The function's own comment warned about that exact trap and
    the trap still caught the next mode added.

    So there is one predicate now. This fails if a second copy of the
    condition reappears anywhere outside it.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))

    check("function machineHidden()" in src,
          "machineHidden() is gone; the machine-visibility condition has been "
          "inlined again")
    body = re.search(r"function machineHidden\(\) \{(.*?)\n\}", src, re.S)
    check(body is not None and "partOnly" in body.group(1),
          "machineHidden() no longer accounts for part-only")

    # every other occurrence of the raw condition is a re-inlining, except the
    # still, which is deliberately real-mode-only and says so.
    raw = [ln.strip() for ln in src.split("\n")
           if "realFraming === 'solo'" in ln and "function machineHidden" not in ln]
    own = body.group(1).strip() if body else ""
    stray = [ln for ln in raw
             if ln != own and "machineHidden" not in ln and "stillOk" not in ln
             and "!partOnly" not in ln and "setRealFraming" not in ln
             and "f === 'solo'" not in ln]
    check(not stray,
          "the machine-visibility condition is inlined again outside "
          "machineHidden(), which is how the AMS leaked back in: %r" % (stray,))


def test_part_only_brings_its_own_light():
    """Hiding the machine hides the chamber lamp with it.

    chamberLamp is a CHILD of the chamber group -- it has to be, it moves with
    the enclosure -- so switching the chamber off removes a 1.55-intensity
    point light that was doing most of the illumination. The first render of
    part-only came out dark slate blue and read as a different material
    entirely, lit by nothing but a 1.05 key, a 0.32 rim and a dark env map.

    The light from BELOW is the point of the mode rather than a nicety: every
    light in the real rig points down or across, so a first layer viewed from
    underneath renders near black.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))
    body = re.search(r"function setPartOnly\(on\) \{(.*?)\n\}", src, re.S)
    check(body is not None, "setPartOnly is gone")
    if not body:
        return
    b = body.group(1)
    check("partRig" in b, "part-only no longer builds its own lighting, so it "
                          "inherits a scene whose main lamp it just switched off")
    lights = re.findall(r"new THREE\.DirectionalLight\([^)]*\)", b)
    check(len(lights) >= 2,
          "part-only is down to %d light(s); it needs a fill for the body and "
          "one from below for the first layer" % len(lights))
    below = re.findall(r"\.position\.set\([^)]*,\s*-(\d+)\)", b)
    check(any(int(v) > 100 for v in below),
          "nothing in the part-only rig is below the part any more -- the "
          "underside is the one surface this view exists to show")
    check("chamberLamp" not in b,
          "setPartOnly is reaching into the chamber's own lamp instead of "
          "carrying its own rig; that lamp belongs to the enclosure")


def test_the_sheen_runs_along_the_bead_not_across_it():
    """Anisotropic reflection, added 2026-09-19.

    An extruded bead is a half-cylinder lying on its side and a wall is a
    stack of them running parallel, so the surface reflects directionally --
    the highlight is a band along the beads, not a round spot. That is a
    measured property of FDM parts (AnisoTag, arXiv 2301.10599, encodes data
    on printed surfaces using reflection anisotropy alone), not a stylisation.

    The tangent is taken as cross(worldUp, normal), which is free: a bead runs
    horizontally, perpendicular to its own outward normal. Taking it from a
    vertex attribute instead would put a third attribute on a mesh already
    carrying 800k triangles, so if this stops being a cross product that is a
    real memory regression worth failing on.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))
    check("lights_fragment_end" in src,
          "the anisotropic lobe is gone -- the surface is back to an isotropic "
          "highlight, which is what makes a print read as a smooth object with "
          "stripes painted on it")
    check("cross(upS, normal)" in src,
          "the bead tangent is no longer derived from the normal; if it now "
          "comes from a vertex attribute that is a third attribute on an 800k "
          "triangle mesh")
    check(re.search(r"sl \* sv - tdl \* tdv", src) is not None,
          "the Kajiya-Kay lobe has been replaced by something else; a standard "
          "isotropic pow(dot(N,H)) highlight is exactly what this replaced")
    check("uSheen" in src and "wallA" in src,
          "the sheen is no longer gated on the wall factor, so it fires where "
          "the cross product degenerates (a vertical normal)")


def test_the_bead_is_a_closed_tube():
    """The hollow bead, found 2026-09-19 on the third report about layer lines.

    The cross-section had three bands -- point 0 to 1 to 2 to 3 -- and never
    joined 3 back to 0. So every bead was an open TROUGH with no floor, and
    looking at the part from underneath showed the INSIDE of the first layer
    rather than its bottom. That made the part-only underside view, shipped
    the same day, structurally wrong.

    Measured A/B on the pumpkin's underside, same camera, open vs closed:
    mean luma 95.2 -> 115.0 and standard deviation 14.4 -> 29.4, with 19.6% of
    pixels changed. The contrast doubling is the point: flat mush became real
    bead structure.

    It costs no vertices -- the four points already exist -- so the price is
    six more indices per segment and nothing at all in the vertex buffers,
    which is where the memory actually is. Verified: 501,812 vertices before
    and after; triangles 669,906 -> 893,208.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    body = re.search(r"function buildJob\(raw\) \{.*?\n\}", js, re.S)
    check(body is not None, "buildJob is gone")
    if not body:
        return
    b = "\n".join(re.sub(r"//.*$", "", ln) for ln in body.group(0).split("\n"))
    check("BEAD_IDX = 24" in b,
          "the bead is back to fewer than four bands -- it is an open trough "
          "again and the underside shows the inside of the first layer")
    check(re.search(r"index\[ii\+\+\] = a \+ 3;\s*index\[ii\+\+\] = b \+ 3;\s*index\[ii\+\+\] = a;", b),
          "the floor quad joining point 3 back to point 0 is gone")
    check("BEAD_PTS = 4" in b,
          "closing the bead must not have cost extra vertices; four points "
          "is the whole reason this was cheap")
    # the draw range walks the same stride or the reveal desyncs from the mesh
    dr = re.search(r"setDrawRange\(0, seg \* (\d+)\)", js)
    check(dr is not None and dr.group(1) == "24",
          "setDrawRange still strides by the old index count, so the print "
          "reveals the wrong number of segments: %r" % (dr and dr.group(1),))


def test_the_degenerate_floor_normal_is_caught():
    """The floor quad spans two exactly opposite normals.

    Point 3's normal is (-u, 0) and point 0's is (+u, 0), so interpolated
    across the new floor they cancel and vNormal's length reaches zero at
    mid-span. normalize() there amplifies numerical noise into a random
    direction -- a black speckle stripe down the middle of every bead's
    underside, in the one view built to inspect undersides.

    Giving the floor its own vertices would fix it at +50% on the vertex
    buffers. Detecting the degenerate span costs one length().
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))
    check("length(vNormal)" in src,
          "nothing guards the floor's degenerate normal any more; the bead "
          "underside will speckle where the two opposite normals cancel")
    check(re.search(r"vec4\(0\.0, 0\.0, -1\.0, 0\.0\)", src) is not None,
          "the degenerate floor normal is no longer replaced with a downward "
          "one -- a bead's floor faces down, that is the whole substitution")


def test_the_sheen_does_not_wash_the_colour_out():
    """Measured, not picked (2026-09-19).

    The anisotropic lobe shipped at 0.85 and was neutralising saturated
    feature colours into hard grey bands -- the same failure the tone-mapping
    notes describe, from specular instead of ACES. Share of the mushroom cap
    at layer 295 rendering as bright desaturated grey (sat < 0.18, luma > 110):

        0.85 -> 4.21%   mean saturation 0.839
        0.35 -> 1.12%   mean saturation 0.875
        0    -> 0.00%   mean saturation 0.913

    A highlight on satin PLA brightens the colour, it does not neutralise it.
    This fails if the value is raised back into the range that did.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))
    m = re.search(r"uSheen:\s*\{value:\s*([0-9.]+)\}", src)
    check(m is not None, "the sheen strength uniform is gone")
    if not m:
        return
    v = float(m.group(1))
    check(v <= 0.5,
          "sheen is back up to %s; at 0.85 it washed 4.21%% of the cap to "
          "neutral grey. Re-measure the desaturated share before raising it"
          % m.group(1))
    check(v > 0.0,
          "sheen is off entirely -- the surface is back to an isotropic "
          "highlight and stops reading as extruded")


def test_real_print_mode_is_exposed_like_a_photograph():
    """Why layer lines did not read, measured 2026-09-19.

    Real macro photographs of white/silver FDM walls (Simplify3D's own
    print-quality reference set) sit at mean luminance 63-117 out of 255. This
    viewer rendered the same kind of surface at 195. At that exposure the
    surface is already in the top fifth of the range, so there is no headroom
    for a bright ridge crest and the layer modulation compresses to nothing.

    Ridge amplitude at the layer frequency, as a share of local mean:

        exposure 1.00   mean 195   ridge 3.83%
        exposure 0.65   mean 179   ridge 5.32%
        exposure 0.45   mean 162   ridge 6.87%
        real prints                ridge 13.7-20.7%

    Nine times the normal-perturbation strength moved that from 3.36% to
    4.78%. Halving exposure nearly doubled it. The lever was never the layer
    model, which is why this guard is on exposure and not on the shader.

    Diagnostic modes stay bright on purpose -- they are a colour key read
    against a legend, not a photograph.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))
    m = re.search(r"toneMappingExposure = real \? ([0-9.]+) : ([0-9.]+)", src)
    check(m is not None,
          "real-print mode no longer drops the exposure; a white part renders "
          "at mean luminance ~195 where real photographs sit at 63-117, and "
          "the layer ridges have no headroom to show in")
    if not m:
        return
    real_e, diag_e = float(m.group(1)), float(m.group(2))
    check(real_e < diag_e,
          "real mode is not darker than the diagnostic modes (%s vs %s)"
          % (m.group(1), m.group(2)))
    check(real_e <= 0.6,
          "real-mode exposure is back up to %s; measured, anything above ~0.6 "
          "puts the surface where ridge contrast compresses away" % m.group(1))


def test_the_layer_bulge_is_continuous_across_the_boundary():
    """The bulge was a sawtooth.

    (lyPos - 0.5) * 2.0 runs +1 at the top of one layer and jumps straight to
    -1 at the bottom of the next. That discontinuity draws a hard line at
    every single layer boundary, which is the opposite of a real wall, where
    beads meet in a smooth valley. A sine is continuous across the boundary by
    construction.

    The strength is a uniform so it can be swept against a reference
    photograph rather than guessed -- that sweep is what established exposure,
    not amplitude, as the real lever.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))
    check("sin(6.28318" in src,
          "the layer bulge is not a full-period sine any more; if it is back "
          "to a sawtooth it draws a hard step at every layer boundary")
    check("(lyPos - 0.5) * 2.0" not in src,
          "the sawtooth bulge is back")
    check("uLayerAmp" in src,
          "the bulge strength is hardcoded again, so it cannot be swept "
          "against a reference photograph")
    m = re.search(r"uLayerAmp:\s*\{value:\s*([0-9.]+)\}", src)
    check(m is not None and float(m.group(1)) > 0.0,
          "the layer bulge is switched off entirely")


def test_the_plate_can_never_occlude_the_print_sitting_on_it():
    """"Any plate hides the first few layers", reported 2026-09-19.

    The plate face sits 0.045mm under the first layer and carried
    polygonOffset -2/-2, which pulls it TOWARD the camera. Two depth units at
    24-bit precision with near=1/far=4000 is roughly 0.02mm at 400mm of camera
    distance and 0.076mm at 800mm, so past about 600mm the bias exceeded the
    gap and the plate swallowed the first layer or two of every print.

    Flipping the sign was worse and is the more interesting half: the offset
    was never fighting the print, it was fighting the steel body underneath,
    whose top sits FIVE MICRONS below the face (depth 2.0 extruded from
    -2.05 tops out at -0.05). Pushing the face away handed the surface to the
    body and the plate rendered as bare dark steel -- measured, the plate went
    from #976a38 to #394156.

    So the fix is real Z separation, not bias in either direction. This guards
    both halves: no negative offset, and a body top far enough below the face
    that no bias is needed.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))
    bed = re.search(r"function buildBed\(X, Y, ox, oy\) \{(.*?)\n\}", src, re.S)
    check(bed is not None, "buildBed is gone")
    if not bed:
        return
    b = bed.group(1)

    neg = re.search(r"polygonOffsetFactor:\s*-", b)
    check(neg is None,
          "the plate face pulls itself toward the camera again; it sits under "
          "the first layer and will hide it at any real camera distance")

    body = re.search(r"body\.position\.set\(0, 0, (-[0-9.]+)\)", b)
    face = re.search(r"plate\.position\.set\(0, 0, (-[0-9.]+)\)", b)
    depth = re.search(r"depth:\s*([0-9.]+)", b)
    check(body and face and depth,
          "cannot find the plate body/face placement any more")
    if not (body and face and depth):
        return
    body_top = float(body.group(1)) + float(depth.group(1))
    face_z = float(face.group(1))
    check(body_top < face_z - 0.15,
          "the steel body's top (%.3f) is within %.3fmm of the plate face "
          "(%.3f). That is below depth-buffer resolution, so the face will "
          "z-fight it and something will reach for a polygon offset again"
          % (body_top, face_z - body_top, face_z))
    check(face_z < 0,
          "the plate face is at or above z=0, so the first layer is inside it")


def test_the_plate_grain_is_a_real_size_in_millimetres():
    """"The plate is completely wrong texture", reported 2026-09-19.

    The grain canvas covered the whole 256mm plate in 512px -- 2 px/mm. A real
    textured-PEI grain is well under a millimetre, so at 2 px/mm it is one
    pixel: not representable. The octaves had therefore been authored large
    enough to survive, and the coarse one was a 15px radius, which over 256mm
    is a 7.5mm radius. Fifteen-millimetre blobs on a surface whose real grain
    is sub-millimetre.

    Measured on Bambu's own product photograph of the plate (1010px across
    256mm, 3.95 px/mm): the speckle is uniform and fine, sd 5.09 on mean
    177.7 -- about 2.9% modulation, with no large-scale structure at all.

    The normal map tiles at PLATE_TILE_MM now, so the same canvas is 16 px/mm
    and a 0.5mm grain is 8px. The colour map stays 1:1 because the printed
    markings have to land at real plate coordinates.
    """
    js = (ROOT / "tools" / "viewer" / "app.js").read_text(encoding="utf-8")
    src = "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))

    m = re.search(r"var PLATE_TILE_MM = ([0-9.]+)", src)
    check(m is not None,
          "the grain no longer tiles at a real millimetre size; it is being "
          "stretched over the whole bed again at 2 px/mm")
    px = re.search(r"var PLATE_PX = (\d+)", src)
    if not (m and px):
        return
    per_mm = float(px.group(1)) / float(m.group(1))
    check(per_mm >= 8,
          "the grain canvas is %.1f px/mm; a sub-millimetre stipple needs at "
          "least ~8 to survive mipmapping" % per_mm)

    # Scoped to grainNormalMap on purpose: an unscoped search for
    # "wrapS = ...RepeatWrapping" also matches the chamber panel texture at
    # the top of the file, and passed even with the plate's own line deleted.
    # Caught by mutation, which is the only way that false pass ever shows up.
    gnm = re.search(r"function grainNormalMap\(grain, g\) \{(.*?)\n\}", src, re.S)
    check(gnm is not None, "grainNormalMap is gone")
    check(gnm and "RepeatWrapping" in gnm.group(1),
          "the grain texture does not repeat, so tiling it does nothing")
    check("repeat.set(X / PLATE_TILE_MM" in src,
          "the grain repeat is no longer derived from the real plate size")

    # every stipple octave must be sub-millimetre at the tile scale
    g = re.search(r"stipple:\s*\{[^}]*octaves:\s*\[(.*?)\]\}", src)
    check(g is not None, "the stipple grain is gone")
    if g:
        radii = [float(x) for x in re.findall(r"\[\s*([0-9.]+),", g.group(1))]
        worst = max(radii) * float(px.group(1)) / 1024.0 / per_mm
        check(worst < 1.0,
              "the coarsest stipple feature is %.2fmm across at the tile "
              "scale; the real plate has no structure that large" % (worst * 2))

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
