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
