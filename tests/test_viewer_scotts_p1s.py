"""The P1S model in tools/viewer, checked against Scott's own printer (2026-09-23).

Scott sent ten photos of his P1S. Measured off the straight-on front shot at
0.282 mm/px (389 mm across 1380 px), and read off the interior shots, they
corrected six things the model had wrong. Each test pins one of them so it
cannot quietly drift back to the earlier guess. The last two pin bugs that
rendering the corrected model turned up: a fan lying flat, and a helper
called from outside the function that defines it.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_viewer_scott_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "viewer-scott-test-not-a-real-secret")

APP = ROOT / "tools" / "viewer" / "app.js"
_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _src():
    js = APP.read_text(encoding="utf-8")
    # comments removed, so a test can never pass on a sentence about the code
    return "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))


def _lum_neutral(hexstr):
    v = int(hexstr, 16)
    r, g, b = (v >> 16) & 255, (v >> 8) & 255, v & 255
    return max(r, g, b), max(r, g, b) - min(r, g, b)


def test_case_corners_are_rounded_25mm_and_the_door_sits_between_them():
    # Outer 1380 px, flat face ~1205 px: (389 - 340) / 2 = ~25 mm of corner
    # radius. A square box was the old model, and the door ran edge to edge.
    src = _src()
    m = re.search(r"var CR = (\d+);", src)
    check(m is not None, "the case corner radius is gone")
    if m:
        check(20 <= int(m.group(1)) <= 30, "corner radius %s mm is not ~25" % m.group(1))
    check("var dx0 = x0 + CR, dx1 = x1 - CR;" in src,
          "the door opening must start where the corner curve ends")
    check("roundRect(EXT.w, EXT.d, CR)" in src,
          "the base and lid must be rounded to the same radius as the corners")


def test_door_bezels_are_the_measured_64_top_and_31_bottom():
    # 64 + 360 + 31 = 455 of the 458 mm case, from the front shot.
    src = _src()
    check("var dz0 = zBot + 31, dz1 = zTop - 64;" in src,
          "door bezels are no longer the measured 31 mm bottom / 64 mm top")


def test_control_panel_stands_proud_above_the_lid():
    # The panel's top edge is ~10 mm ABOVE the lid, not recessed into the
    # bezel, and it is 146 x 42 mm.
    src = _src()
    m = re.search(r"var PANEL_W = (\d+), PANEL_H = (\d+),", src)
    check(m is not None, "could not find the control panel size")
    if m:
        check((int(m.group(1)), int(m.group(2))) == (146, 42),
              "panel is %s x %s, measured 146 x 42" % (m.group(1), m.group(2)))
    m = re.search(r"var panelZ = zTop \+ (\d+) - PANEL_H / 2;", src)
    check(m is not None and int(m.group(1)) > 0,
          "the panel's top edge must sit above zTop")


def test_lead_screws_are_at_the_two_front_corners_and_the_rear_centre():
    # The old layout was two at the back and one at the front-right, placed
    # to keep the doorway clear. Scott's interior shots show one beside each
    # front corner of the bed and one in a slot at the back wall's centre.
    src = _src()
    m = re.search(r"var zPosts = \[(.*?)\];", src, re.S)
    check(m is not None, "could not find the lead screw list")
    if not m:
        return
    posts = re.findall(r"\[([^\[\]]+?),\s*([^\[\]]+?)\]", m.group(1))
    check(len(posts) == 3, "expected three lead screws, found %d" % len(posts))
    if len(posts) != 3:
        return
    (ax, ay), (bx, by), (cx, cy) = posts
    check("x0" in ax and "x1" in bx, "the first two screws must be at the left and right")
    check("oy - Y / 2" in ay and "oy - Y / 2" in by,
          "the two side screws must sit at the bed's FRONT edge, not the back")
    check(cx.strip().startswith("ox"), "the third screw must be centred left-to-right")
    check("y1 - t" in cy, "the third screw must stand at the back wall")


def test_toolhead_housings_are_light_grey_over_a_dark_band():
    # Photographed: light grey upper, "Bambu Lab" on the front, dark grey
    # lower band. Every earlier pass drew it near-black with a blue cast.
    src = _src()
    m = re.search(r"var SHELL = 0x([0-9a-f]{6}), SHELL_LOW = 0x([0-9a-f]{6})", src)
    check(m is not None, "could not find the toolhead shell colours")
    if m:
        lum, spread = _lum_neutral(m.group(1))
        check(lum >= 0xb0 and spread <= 3,
              "toolhead shell %s is not a light neutral grey" % m.group(1))
        lum, spread = _lum_neutral(m.group(2))
        check(lum <= 0x40 and spread <= 3,
              "toolhead lower band %s is not a dark neutral grey" % m.group(2))
    fn = src[src.index("function buildToolhead"):src.index("function shellTexture")]
    check("part(25, 17, 26, SHELL," in fn, "the middle housing is not the light shell")
    check("part(25, 8, 25, SHELL," in fn, "the front housing is not the light shell")
    for old in ("0x1b1e25", "0x15181e", "0x2d323c", "0x4b5261"):
        check(old not in fn, "blue-cast toolhead colour %s is back" % old)
    check("'Bambu Lab'" in fn, "the toolhead's front name is missing")


def test_heatbed_is_light_on_the_p1s_only():
    src = _src()
    i = src.index("var carrier = new THREE.Mesh")
    body = src[i:i + 300]
    m = re.search(r"printerId === 'p1s' \? surface\(0x([0-9a-f]{6})", body)
    check(m is not None, "the heatbed colour must be P1S-specific")
    if m:
        lum, spread = _lum_neutral(m.group(1))
        check(lum >= 0x90 and spread <= 3,
              "P1S heatbed %s is not the pale grey photographed" % m.group(1))


def test_the_part_cooling_fan_faces_forward_not_up():
    # A THREE cylinder's own axis is Y, which in this Z-up scene is already
    # front-to-back. The fan carried the rotation.x the vertical parts need,
    # so it lay flat; on the light housing it showed as a black slot.
    src = _src()
    fn = src[src.index("function buildToolhead"):src.index("function shellTexture")]
    for name in ("fan", "hub"):
        check("%s.rotation.x" % name not in fn,
              "the toolhead %s is rotated flat again; it must face out of the front" % name)


def test_no_helper_is_called_outside_the_function_that_defines_it():
    # The rear screw's back-wall slot first called slab(), which lives inside
    # buildChamber, from buildInterior. Every source check here passed and the
    # page threw "slab is not defined" at boot -- caught only by rendering it.
    # A nested function called from another top-level function is exactly that
    # bug, so look for it directly.
    src = _src()
    tops = [(m.start(), m.group(1)) for m in re.finditer(r"^function (\w+)", src, re.M)]
    spans = [(st, tops[i + 1][0] if i + 1 < len(tops) else len(src), name)
             for i, (st, name) in enumerate(tops)]
    top_names = {name for _, _, name in spans}

    def defines(body, n):
        return re.search(r"\bfunction %s\(|\bvar %s\b" % (n, n), body) is not None

    for st, en, owner in spans:
        for n in re.findall(r"^  function (\w+)\(", src[st:en], re.M):
            if n in top_names:
                continue
            for o_st, o_en, other in spans:
                if other == owner:
                    continue
                body = src[o_st:o_en]
                if re.search(r"\b%s\(" % n, body) and not defines(body, n):
                    check(False, "%s() is defined inside %s() but called from %s()"
                          % (n, owner, other))


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("VIEWER SCOTT'S P1S TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIEWER SCOTT'S P1S TESTS OK — rounded corners, measured bezels, a raised "
          "panel, lead screws where his photos put them, a light toolhead and a pale "
          "heatbed.")


if __name__ == "__main__":
    run()
