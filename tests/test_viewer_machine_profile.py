"""The virtual printer's machine profile must stay true to the real hardware.

Written after nearly shipping the wrong box: a search for "AMS dimensions"
returns the AMS HT (114 x 280 x 245 mm) first, which is a different product
from the standard 4-slot AMS Scott owns, and the AMS 2 Pro (372 x 280 x 226)
is a third. All three are "the AMS" in casual speech and only one of them is
the unit sitting on top of the P1S on screen. The figures below are Bambu
Lab's own "AMS Tech Specs" table (us.store.bambulab.com, 2026-09-16); this
test exists so a future edit cannot quietly swap in a neighbouring product's
numbers, which the page would then state as fact in its printer panel.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "tools" / "viewer" / "app.js"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _profile(key: str) -> str:
    src = APP.read_text(encoding="utf-8")
    m = re.search(r"\n  " + key + r":\s*\{(.*?)\n  \}", src, re.S)
    if m is None:
        m = re.search(r"\n  " + key + r":\s*\{(.*?)\},\n", src, re.S)
    assert m, "no %s profile found in app.js" % key
    return m.group(1)


def _ams_fields(body: str) -> dict:
    m = re.search(r"ams:\s*\{([^}]*)\}", body)
    if not m:
        return {}
    out = {}
    for k, v in re.findall(r"(\w+):\s*([0-9.]+)", m.group(1)):
        out[k] = float(v)
    return out


def test_p1s_ams_is_the_standard_four_slot_unit():
    ams = _ams_fields(_profile("p1s"))
    check(ams.get("slots") == 4, "P1S profile should carry a 4-slot AMS, got %r" % ams)
    check((ams.get("w"), ams.get("d"), ams.get("h")) == (368.0, 283.0, 224.0),
          "AMS size must be 368 x 283 x 224 mm (Bambu's own spec table), got %r"
          % ((ams.get("w"), ams.get("d"), ams.get("h")),))
    check(ams.get("kg") == 2.5, "AMS net weight is 2.5 kg, got %r" % ams.get("kg"))


def test_ams_is_not_a_neighbouring_product():
    ams = _ams_fields(_profile("p1s"))
    got = (ams.get("w"), ams.get("d"), ams.get("h"))
    check(got != (114.0, 280.0, 245.0), "these are the AMS HT's dimensions, not the AMS's")
    check(got != (372.0, 280.0, 226.0), "these are the AMS 2 Pro's dimensions, not the AMS's")


def test_only_profiles_with_a_real_ams_declare_one():
    # AMS Lite is a different unit and is not compatible with P-series machines,
    # so the A-series profile must not inherit a P-series AMS by accident.
    for key in ("a2l", "custom"):
        check("ams:" not in _profile(key),
              "%s must not declare an AMS -- nothing verified is drawn for it" % key)


def test_every_declared_ams_is_complete():
    src = APP.read_text(encoding="utf-8")
    for body in re.findall(r"ams:\s*\{([^}]*)\}", src):
        have = set(re.findall(r"(\w+):", body))
        check({"slots", "w", "d", "h", "kg"} <= have,
              "an AMS declaration is missing fields: %r" % sorted(have))


def test_external_case_matches_the_published_p1s_footprint():
    src = APP.read_text(encoding="utf-8")
    m = re.search(r"var EXT = \{w:\s*(\d+), d:\s*(\d+), h:\s*(\d+)", src)
    check(m is not None, "EXT (the printer's outside dimensions) went missing")
    if m:
        check(tuple(int(g) for g in m.groups()) == (389, 389, 458),
              "P1S outside dimensions are 389 x 389 x 458 mm, got %r" % (m.groups(),))


def test_the_door_is_clickable_and_says_why():
    src = APP.read_text(encoding="utf-8")
    check("userData.door" in src, "door meshes lost their hit-test flag")
    check(src.count("userData.door = true") >= 3,
          "the glass, the frame and the grip all need to be hit targets")
    check("pickDoor" in src and "setDoor(!doorOpen)" in src,
          "tapping the door itself must still toggle it, not just the button")


def test_z_axis_has_three_lead_screws():
    # Bambu's own P1 introduction: "The Z-axis is comprised of three lead screws
    # that are connected to a single stepper motor using a belt." The first pass
    # drew two, which is a machine that does not exist.
    src = APP.read_text(encoding="utf-8")
    m = re.search(r"var zPosts = \[(.*?)\];", src, re.S)
    check(m is not None, "the Z stage's post list went missing")
    if m:
        check(m.group(1).count("[") == 3,
              "the P1S Z axis has three lead screws, found %d" % m.group(1).count("["))
    check("zPosts.forEach" in src, "all three posts must be built from the one list")


def test_chamber_led_is_on_the_left_beam():
    # Bambu's P1 service guide reaches the LED and the chamber camera through
    # the LEFT panel, both on the AP board, close enough that the LED "will get
    # caught by the camera" -- so it is a bar down the left side, not a strip
    # across the front, which is where the first pass put it.
    src = APP.read_text(encoding="utf-8")
    m = re.search(r"bar\.position\.set\(([^)]*)\)", src)
    check(m is not None, "the LED bar went missing")
    if m:
        check(m.group(1).strip().startswith("x0 +"),
              "the chamber LED sits on the left beam, got %r" % m.group(1))


def test_the_chamber_lamp_can_actually_light_something():
    # The real defect this reproduces: the interior liner is the largest surface
    # in the chamber, and while it was MeshBasicMaterial the chamber lamp changed
    # a rendered frame by 0.79 of a level out of 255 -- a light that was not a
    # light. An unlit liner makes the lamp decorative again, silently.
    src = APP.read_text(encoding="utf-8")
    m = re.search(r"var liner = new THREE\.Mesh\((.*?)\);", src, re.S)
    check(m is not None, "the chamber liner went missing")
    if m:
        check("MeshBasicMaterial" not in m.group(1),
              "the liner must respond to light or the chamber LED does nothing")


def test_toolhead_is_a_p1s_not_an_x1_carbon():
    src = APP.read_text(encoding="utf-8")
    head = src[src.index("function buildToolhead"):]
    head = head[:head.index("\n}\n")]
    check("lidar" not in head.lower(), "the P1S has no LiDAR -- that is the X1 Carbon")
    for piece in ("rear housing", "middle housing", "front housing", "cutter"):
        check(piece in head, "toolhead is missing its %s" % piece)


def test_screen_is_the_real_2_7_inch_panel():
    # 2.7-inch 192x64 is a 3:1 letterbox; the first pass drew it nearly square.
    src = APP.read_text(encoding="utf-8")
    m = re.search(r"slab\((\d+), 2, (\d+), 0x0b0d10", src)
    check(m is not None, "the front screen went missing")
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        check(2.6 <= w / h <= 3.4, "screen aspect should be about 3:1, got %.1f" % (w / h))


def test_camera_damping_is_time_based_not_per_frame():
    # A flat per-frame damping factor means a device rendering at 9fps takes a
    # second and a half to catch up with a finger that already stopped. Measured
    # 9fps in the container's software renderer, so this is not hypothetical.
    src = APP.read_text(encoding="utf-8")
    check("Math.pow(1 - DAMP, frames)" in src,
          "damping must be converted against the real frame time")
    check("Math.pow(SPIN_DECAY, frames)" in src,
          "fling decay must be converted against the real frame time")
    check(re.search(r"view\[k\] \+= d \* DAMP", src) is None,
          "the raw per-frame constant must never be applied directly")


def test_only_the_p1s_is_drawn_as_itself():
    # The defect this reproduces: selecting the A2L drew a fully enclosed case
    # with a smoked glass door, while the panel beside it read "Enclosed: No /
    # Chamber: None (open frame)". A viewer that teaches how a machine works
    # cannot contradict its own caption.
    src = APP.read_text(encoding="utf-8")
    check("var detailed = printerId === 'p1s'" in src,
          "the detailed portrait must be gated to the one machine it was researched for")
    check("buildOpenFrame" in src, "non-P1S profiles need the honest envelope")
    frame = src[src.index("function buildOpenFrame"):]
    frame = frame[:frame.index("\n}\n")]
    for forbidden in ("doorGroup", "liner", "knob", "chamberLamp"):
        check(forbidden not in frame,
              "buildOpenFrame must not draw %s -- nothing is known about it "
              "for another machine" % forbidden)


def test_a_machine_without_a_door_does_not_offer_one():
    src = APP.read_text(encoding="utf-8")
    check("function syncDoorControl" in src, "the door control must follow the machine")
    check("b.hidden = !doorGroup" in src,
          "the Open door button has to disappear when there is no door")


def test_a2l_is_an_open_frame_bedslinger_at_its_real_footprint():
    body = _profile("a2l")
    check("enclosed:false" in body.replace(" ", ""), "the A2L has no enclosure")
    check("bedslinger:true" in body.replace(" ", ""), "the A2L is a bed-slinger")
    m = re.search(r"footprint:\s*\[(\d+),\s*(\d+),\s*(\d+)\]", body)
    check(m is not None, "the A2L needs its published footprint to draw an envelope")
    if m:
        check(tuple(int(g) for g in m.groups()) == (544, 529, 505),
              "A2L footprint is 544 x 529 x 505 mm, got %r" % (m.groups(),))


def test_the_two_kinematics_are_actually_different():
    # A bed-slinger moves the BED in Y and climbs the gantry in Z; the P1S holds
    # the gantry and drops the bed. Replaying one machine's motion on the other
    # is the same class of lie as drawing it with the wrong case.
    src = APP.read_text(encoding="utf-8")
    seg = src[src.index("function setSeg"):]
    seg = seg[:seg.index("\n}\n")]
    check("PRINTERS[printerId].bedslinger" in seg,
          "setSeg must branch on the machine's kinematics")
    check("bedGroup.position.set(0, -slide, 0)" in seg,
          "a bed-slinger moves its bed in Y")
    check("bedGroup.position.set(0, 0, -drop)" in seg,
          "a descending bed moves in Z")


def test_ams_usage_comes_from_measured_per_layer_filament():
    # The exact bug: attributing filament to a slot by segment-index fraction
    # charged slot 1 with 24.4 g against its real 17.0 g, because the purge is a
    # lot of filament laid over very few moves. Layer boundaries are measured by
    # the exporter and are exact.
    src = APP.read_text(encoding="utf-8")
    check("filByToolLayer" in src, "the viewer must use the per-layer measurement")
    usage = src[src.index("function amsUsage"):]
    usage = usage[:usage.index("\n}\n")]
    check("filToolCum" in usage,
          "per-slot usage must accumulate the measured layer rows")
    check("toolRuns" not in src,
          "the segment-index approximation must be gone, not merely unused")


def test_spool_shrinks_and_spins_on_the_right_axes():
    # A cylinder's own axis is local Y, so the radius is x and z. Scaling y made
    # the spool narrower instead of emptier, and spinning x tumbled it end over
    # end. Both were wrong in the first pass and both are invisible in a still.
    src = APP.read_text(encoding="utf-8")
    check("sl.spool.scale.set(k, 1, k)" in src,
          "the spool empties on its radius (x and z), not its width")
    check("sl.spool.rotation.y" in src,
          "the spool turns about its own axis, which is local y")


def test_the_ams_is_not_conditional_on_the_plate_being_multi_colour():
    # It feeds the nozzle on every job. A single-filament plate is one slot
    # doing all the work, not a special case to skip.
    src = APP.read_text(encoding="utf-8")
    state = src[src.index("function buildAMSState"):]
    state = state[:state.index("\n}\n")]
    check("toolChanges" not in state and "> 1" not in state,
          "buildAMSState must not gate itself on a multi-colour job")
    check("Math.max(1, totals.length)" in state,
          "a single-filament job still gets one slot")


def test_wipe_tower_has_a_colour_and_an_explanation():
    src = APP.read_text(encoding="utf-8")
    check("'Wipe tower'" in src, "the purge block needs its own legend entry")
    m = re.search(r"var N_TYPE = TYPE_COLOR\.length;", src)
    check(m is not None, "the shader array size must follow the palette length")
    check("uniform vec3 uColor[13];" in src,
          "the shader colour array has to cover every type id")


HTML = ROOT / "tools" / "viewer" / "virtual_p1s.html"


def test_the_plate_list_does_not_hide_plates_behind_a_fade():
    # The exact report: "when I open it I can't see the rest of the prints".
    # The list was a 236px box holding 702px of cards, its bottom faded out by a
    # mask, inside a rail that also scrolled -- 3 plates of 11 reachable without
    # discovering a nested scrollbar this browser draws as a 0px overlay.
    css = HTML.read_text(encoding="utf-8")
    jobs = css[css.index("#jobs{"):]
    jobs = jobs[:jobs.index("}")]
    check("max-height:236px" not in jobs,
          "the plate list must not be capped at a fixed 236px, got %r" % jobs)
    check("mask-image" not in jobs,
          "a fade at the bottom tells the reader the list has ended when it has not")
    check("vh" in jobs,
          "the cap should follow the viewport, not a hard-coded pixel count")


def test_the_plate_list_says_how_many_are_out_of_view():
    # A scrollbar cannot carry this: the browser reports a 0px scrollbar gutter
    # for this element, i.e. an overlay bar invisible until you already know to
    # scroll. So the count is stated in words instead.
    src = APP.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")
    check('id="platemore"' in html, "the out-of-view hint element went missing")
    check('id="platecount"' in html, "the N / total counter went missing")
    check("function platesOutOfView" in src,
          "the hint must measure what is actually out of view, not guess")
    check("more plate" in src, "the hint has to name how many are hidden")
    check("updatePlateMore" in src and "addEventListener('scroll'" in src,
          "the hint has to follow scrolling, not just the first render")


def test_the_selected_plate_is_scrolled_into_view():
    src = APP.read_text(encoding="utf-8")
    check("current.scrollIntoView({block: 'nearest'})" in src,
          "picking plate 11 of 11 must not leave it off the top of the list")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append("%s raised:\n%s" % (fn.__name__, traceback.format_exc()))
    if _failures:
        print("VIEWER MACHINE PROFILE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIEWER MACHINE PROFILE TESTS OK -- the machine on screen states only "
          "dimensions that came from the manufacturer, for the right product.")


if __name__ == "__main__":
    run()
