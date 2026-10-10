"""The "Detail: ultra" tier in tools/viewer/app.js (2026-10-10).

Scott asked for the viewer to look a lot more real. Ultra renders the scene
into an off-screen buffer and adds ambient occlusion, bloom and still-frame
supersampling; the part view gained a studio floor with a fitted shadow. Each
test below pins a defect that was actually seen in a screenshot while building
it, so none of them can come back quietly:

- black outlines round every silhouette (a 1e5 sentinel overflowed the
  half-float AO buffer to infinity, and the blur turned that into NaN);
- the floor and the far machine twice as bright, and the smoked door milky
  enough to hide the print (blending moved into linear space);
- the whole orange print glowing like a lamp (bloom keyed on max channel);
- the sky shell shaded grey as if it were a crease;
- depth too coarse at a 1 mm near plane for the occlusion pass to tell a flat
  floor from a corner.

The tier cycle and the automatic step-down are run for real under node.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "tools" / "viewer" / "app.js"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _src():
    return APP.read_text(encoding="utf-8")


def _function(name):
    m = re.search(r"^function %s\(.*?^\}$" % re.escape(name), _src(), re.S | re.M)
    if not m:
        raise AssertionError("function %s not found in app.js" % name)
    return m.group(0)


def _shader(name):
    m = re.search(r"^var %s = .*?\]\.join\('\\n'\);$" % re.escape(name), _src(), re.S | re.M)
    if not m:
        raise AssertionError("shader %s not found in app.js" % name)
    return m.group(0)


def test_the_background_sentinel_fits_in_a_half_float():
    # Half float tops out at 65504. 1e5 became +inf, |inf - z0| / inf is NaN,
    # and NaN in the blur painted a black outline round every silhouette.
    ao = _shader("POST_AO_FRAG")
    vals = [float(v) for v in re.findall(r"vec4\(1\.0, ([0-9.e+]+), 0\.0, 1\.0\)", ao)]
    check(vals, "the AO pass must write a far sentinel for background pixels")
    for v in vals:
        check(v < 65504, "AO background sentinel %g overflows a half-float buffer" % v)


def test_the_scene_buffer_blends_in_display_space():
    # Linear blending lifted the door glass into a haze over the print and
    # mixed the fog (which three adds after encoding) at twice its brightness.
    build = _function("buildPost")
    check("scn.texture.encoding = THREE.sRGBEncoding" in build,
          "the post scene buffer must be sRGB-encoded so transparent surfaces "
          "and fog blend exactly as they do on the canvas")
    check("toneMapping" not in _function("renderPost"),
          "renderPost must not switch tone mapping off: the materials keep "
          "applying the curve so high and ultra match underneath the passes")


def test_bloom_is_keyed_on_luminance_not_the_brightest_channel():
    bright = _shader("POST_BRIGHT_FRAG")
    check("dot(c, vec3(0.2126, 0.7152, 0.0722))" in bright,
          "bloom must threshold on luminance")
    check("max(c.r, max(c.g, c.b))" not in bright,
          "max-channel bloom made a saturated orange print glow like a lamp")


def test_the_sky_is_not_shaded_as_a_crease():
    body = _function("buildBackdrop")
    check("depthWrite = false" in body,
          "the backdrop shell must write no depth, or occlusion darkens its "
          "concave inside")


def test_the_near_plane_follows_the_zoom():
    body = _function("updateCamera")
    m = re.search(r"nearWant = Math\.max\(1, Math\.min\(40, view\.r \* ([0-9.]+)\)\)", body)
    check(m is not None, "updateCamera must scale the near plane with the orbit radius")
    if m:
        k = float(m.group(1))
        # The camera always looks at a target r away; anything inside k*r of
        # the lens is clipped, so k has to stay small.
        check(k <= 0.05, "near plane at %.0f%% of the radius clips too much" % (k * 100))


def test_every_frame_goes_through_one_guarded_call():
    tick = _function("tick")
    check("renderFrame();" in tick, "tick must render through renderFrame")
    check("renderer.render(scene, camera)" not in tick,
          "tick must not bypass renderFrame's fallback")
    rf = _function("renderFrame")
    check(re.search(r"catch \(e\) \{[^}]*postBroken = true", rf, re.S) is not None,
          "a failure in the post path must fall back to the plain render for the session")


def test_supersampling_is_still_frames_only_and_capped():
    rp = _function("renderPost")
    check(re.search(r"if \(hiRes\) \{\s*ss = Math\.min\(POST_SS_MAX, Math\.sqrt\(POST_SS_PIXELS", rp) is not None,
          "supersampling must only run on a settled frame and be capped by total pixels")
    m = re.search(r"var POST_SS_MAX = ([0-9.]+), POST_SS_PIXELS = ([0-9.e]+);", _src())
    check(m is not None, "supersampling limits must be named constants")
    if m:
        check(float(m.group(1)) <= 2, "more than 2x per axis is 4x+ the fill for nothing")
        check(float(m.group(2)) <= 8e6, "a supersampled buffer over 8 MP is too much for a tablet")


def test_the_part_floor_cannot_hide_the_first_layer_from_below():
    mat = _function("partFloorMaterial")
    check("side:" not in mat,
          "the part floor must stay front-face only so orbiting underneath "
          "looks straight through it at the first layer")
    sync = _function("syncPartStudio")
    check(re.search(r"partFloor\.position\.set\(cx, cy, z0 - 0\.0\d+\)", sync) is not None,
          "the floor must sit a hair below the first layer, not coplanar with it")
    check("machineHidden()" in sync, "the floor shows only when the machine is hidden")


_TIER_HARNESS = """
var richShading = true, postWanted = true, postBroken = false, supported = %s;
var autoQualityDone = false, shadowDirty = false, note = {innerHTML: ''};
var disposed = 0;
var keyLight = {shadow: {map: {dispose: function () { disposed++; }},
  mapSize: {x: 1536, set: function (a) { this.x = a; }}}};
var btn = {attrs: {}, textContent: '', setAttribute: function (k, v) { this.attrs[k] = v; }};
function $(id) { return id === 'quality' ? btn : id === 'legnote' ? note : null; }
function postSupported() { return supported; }
var freed = 0;
function postDispose() { freed++; }
function setQuality(rich) { richShading = rich; paintQuality(); }
var clock = 0, frames = [];
var performance = {now: function () { return clock; }};
function requestAnimationFrame(f) { frames.push(f); }
%s
%s
%s
%s
%s
var seen = [btn.textContent], maps = [];
paintQuality(); seen = [btn.textContent]; maps = [keyLight.shadow.mapSize.x];
for (var i = 0; i < 3; i++) {
  cycleQuality(); seen.push(btn.textContent); maps.push(keyLight.shadow.mapSize.x);
  if (!keyLight.shadow.map) keyLight.shadow.map = {dispose: function () { disposed++; }};
}
// Auto step-down at 10 fps: ultra goes to high first, then to fast.
richShading = true; postWanted = true; paintQuality();
autoQuality();
var steps = [];
while (frames.length && steps.length < 2000) {
  clock += 100; var f = frames.shift(); f();
  if (!steps.length || steps[steps.length - 1] !== btn.textContent) steps.push(btn.textContent);
}
console.log(JSON.stringify({seen: seen, steps: steps, maps: maps, disposed: disposed, freed: freed,
                            pressed: btn.attrs['aria-pressed']}));
"""


def _run_tiers(supported):
    node = shutil.which("node")
    if not node:
        return None
    js = _TIER_HARNESS % ("true" if supported else "false", _function("postActive"),
                          _function("syncShadowRes"), _function("paintQuality"),
                          _function("cycleQuality"), _function("autoQuality"))
    r = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node failed:\n" + r.stderr)
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_the_detail_button_cycles_ultra_high_fast():
    out = _run_tiers(True)
    if out is None:
        print("  (skipped: no node on PATH)")
        return
    check(out["seen"] == ["Detail: ultra", "Detail: high", "Detail: fast", "Detail: ultra"],
          "the button must cycle ultra -> high -> fast -> ultra, got %r" % out["seen"])
    check(out["maps"] == [3072, 1536, 1536, 3072],
          "the shadow map must be 3072 in ultra and 1536 otherwise, got %r" % out["maps"])
    check(out["disposed"] >= 3,
          "a shadow map must be disposed when its size changes, %d disposed" % out["disposed"])
    check(out["freed"] >= 1, "leaving ultra must free the post-processing buffers")
    check(out["steps"] == ["Detail: ultra", "Detail: high", "Detail: fast"],
          "a slow device must lose ultra first and only then the rich materials, got %r"
          % out["steps"])


def test_a_device_without_float_buffers_never_claims_ultra():
    out = _run_tiers(False)
    if out is None:
        print("  (skipped: no node on PATH)")
        return
    check("Detail: ultra" not in out["seen"],
          "without WebGL2 float buffers the button must never say ultra, got %r" % out["seen"])


def test_heat_constants_are_bambus_pla_profile_and_the_derivation():
    src = _src()
    m = re.search(r"var HEAT = \{nozzle: (\d+), chamber: (\d+), bed: (\d+), tauFan: ([0-9.]+), "
                  r"tauNoFan: ([0-9.]+), tauSoak: ([0-9.]+),\s*soften: (\d+), partFan: (\d+), auxFan: (\d+)\}", src)
    check(m is not None, "HEAT constants must be declared in one place")
    if not m:
        return
    noz, cham, bed, tf, tn, ts, soft, pf, af = (float(x) for x in m.groups())
    # fdm_filament_pla: nozzle_temperature 220, textured_plate_temp 55,
    # temperature_vitrification 45, fan_min_speed 100, additional_cooling_fan_speed 70
    check((noz, bed, soft, pf, af) == (220, 55, 45, 100, 70),
          "HEAT must hold Bambu's PLA profile values, got %r" % ((noz, bed, soft, pf, af),))
    # Lumped capacitance, as worked in the README: C/(hA) per mm of bead.
    area_mm2 = 0.0754
    cap = area_mm2 * 1.26e-3 * 1.8          # J/K per mm (rho g/mm3, cp J/gK)
    surf_m2 = 0.82e-6                        # m2 per mm
    for h, tau, name in [(100, tf, "fan"), (10, tn, "no fan")]:
        want = cap / (h * surf_m2)
        check(abs(tau - want) / want < 0.05,
              "tau with %s should be %.1f s from the derivation, got %s" % (name, want, tau))


def test_every_bead_carries_when_it_was_laid():
    body = _function("buildJob")
    check("g.setAttribute('aDep'" in body, "beads need a deposition-time attribute")
    check("segDone ? segDone[k] : segCum[k + 1]" in body,
          "a point is laid when its segment is DONE, not when the next starts")
    check("uNow.value = play.t" in _function("tick"), "the cooling clock must follow playback")


def test_motion_toggle_keeps_part_only_framed_on_the_part():
    body = _function("setMotion")
    check(re.search(r"if \(machineHidden\(\)\) \{ frameSolo\(JOB\);", body) is not None,
          "toggling bed motion in Part only must frame the part, not the machine")


def test_the_studio_sits_inside_the_cube_cameras_far_plane():
    # r128's PMREMGenerator.fromScene renders the cube with far = 100. The old
    # softbox room sat 300-420 units out and never reached a pixel; a frame lit
    # by it was identical to one lit by its background colour alone.
    body = _function("applyStudioEnvironment")
    m = re.search(r"new THREE\.SphereGeometry\(([0-9.]+),", body)
    check(m is not None, "the captured studio must be drawn on a sphere")
    if m:
        check(float(m.group(1)) < 100,
              "studio sphere radius %s is outside fromScene's far plane of 100 "
              "-- it would be clipped, exactly as the old softboxes were" % m.group(1))
    check("pmrem.fromScene(room, 0)" in body, "the studio must go through PMREM")
    check("rotation.x = Math.PI / 2" in body,
          "the capture is Y-up and this scene is Z-up; unrotated, the floor of "
          "the studio would light the machine from the side")


def test_the_captured_studio_ships_and_decodes():
    import base64, json as _json, zlib
    path = ROOT / "tools" / "viewer" / "hdri" / "studio.js"
    check(path.exists(), "hdri/studio.js is missing")
    if not path.exists():
        return
    src = path.read_text()
    check(src.startswith("window.__ENV_LOADED(") and src.rstrip().endswith(");"),
          "the studio file must call the loader app.js installs")
    env = _json.loads(src[len("window.__ENV_LOADED("):src.rstrip().rindex(")")])
    check(env.get("license") == "CC0" and "polyhaven.com" in env.get("source", ""),
          "the studio must say where it came from and under what licence")
    raw = zlib.decompress(base64.b64decode(env["data"]))
    check(len(raw) == env["w"] * env["h"] * 4,
          "decoded studio is %d bytes, expected w*h*4 = %d" % (len(raw), env["w"] * env["h"] * 4))
    check("'hdri/studio.js'" in _src(), "app.js must load the file the build ships")
    build = (ROOT / "tools" / "viewer" / "build_site.py").read_text()
    check('HERE / "hdri" / "studio.js"' in build, "build_site.py must ship the studio")


def test_a_browser_without_decompression_keeps_the_placeholder():
    body = _function("loadStudioEnvironment")
    check("typeof DecompressionStream === 'undefined'" in body,
          "an older browser must fall back to the placeholder, not throw")
    check(".catch(function (e)" in body, "a failed decode must not take the page down")


def run() -> None:
    import sys
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("VIEWER REALISM TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIEWER REALISM TESTS OK — ultra keeps the plain path's colours and "
          "blending, its passes cannot NaN or bloom a print, and the detail tiers "
          "step down in the right order.")


if __name__ == "__main__":
    run()
