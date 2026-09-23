"""Markings on the P1S model in tools/viewer (2026-09-23).

Measured off Bambu's own product photography: the door handle, the front
wordmark, the side-panel wordmark and the heatbed's warning strip. These pin
what was wrong before and what would be easy to get wrong again.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_viewer_marks_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "viewer-marks-test-not-a-real-secret")

APP = ROOT / "tools" / "viewer" / "app.js"
_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _src():
    js = APP.read_text(encoding="utf-8")
    # comments removed, so a test can never pass on a sentence about the code
    return "\n".join(re.sub(r"//.*$", "", ln) for ln in js.split("\n"))


def test_the_handle_is_a_horizontal_pill_not_the_old_vertical_bar():
    # The grip was BoxGeometry(9, 13, 74) -- 74mm tall and 9 wide -- in
    # blue-grey. Bambu's photo shows a horizontal pill ~56 x 18 mm.
    src = _src()
    check("BoxGeometry(9, 13, 74)" not in src,
          "the vertical 9 x 74 mm grip is back; the real handle is horizontal")
    w = re.search(r"PILL_W = (\d+)", src)
    h = re.search(r"PILL_H = (\d+)", src)
    check(w and h, "could not find the handle's dimensions")
    if w and h:
        check(int(w.group(1)) > 2 * int(h.group(1)),
              "handle must be clearly wider than tall, got %s x %s"
              % (w.group(1), h.group(1)))


def test_the_handle_is_neutral_silver():
    # 0x7b8493 is (123,132,147): 24 levels of blue on a part that photographs
    # neutral. It slipped past the shell guard, which only checks dark colours.
    src = _src()
    check("0x7b8493" not in src, "the blue-grey handle colour is back")
    m = re.search(r"surface\(0x([0-9a-f]{6}), \{roughness: 0\.34", src)
    check(m is not None, "could not find the handle material")
    if m:
        v = int(m.group(1), 16)
        r, g, b = (v >> 16) & 255, (v >> 8) & 255, v & 255
        check(max(r, g, b) - min(r, g, b) <= 2,
              "handle colour %s is not neutral" % m.group(1))


def test_no_logo_artwork_is_reproduced():
    # The line this file has always held: the name as plain text is a fact
    # about the machine; Bambu's logotype and mark are theirs.
    src = _src()
    fn = src[src.index("function machineLabel"):src.index("function faceLabel")]
    check("system-ui" in fn, "machine labels must be set in a plain system face")
    check(not re.search(r"drawImage|new Image\(|\.svg|\.png", fn),
          "machine labels must not draw logo artwork")


def test_labels_are_oriented_by_basis_so_they_cannot_mirror():
    # Text on a face comes out mirrored half the time with Euler angles.
    src = _src()
    fn = src[src.index("function faceLabel"):]
    fn = fn[:fn.index("\n}") + 2]
    check("makeBasis" in fn and "crossVectors" in fn,
          "faceLabel must build its rotation from a basis with normal = text x up")


def test_side_wordmark_is_tone_on_tone():
    # Measured 46 on a matte field of 67: a darker gloss, not a print. A light
    # ink here would misrepresent the machine.
    src = _src()
    m = re.search(r"var side = faceLabel\(machineLabel\(.*?ink: '#([0-9a-f]{6})'", src, re.S)
    check(m is not None, "could not find the side wordmark")
    if m:
        v = int(m.group(1), 16)
        lum = max((v >> 16) & 255, (v >> 8) & 255, v & 255)
        check(lum <= 0x30, "side wordmark ink #%s is too light to be tone-on-tone" % m.group(1))


def test_bed_strip_is_p1s_only_and_derived_from_the_profile():
    src = _src()
    i = src.index("var strip = faceLabel")
    guard = src[max(0, i - 200):i]
    check("printerId === 'p1s'" in guard,
          "the heatbed strip must be P1S-only; other profiles are honest envelopes")
    body = src[i:i + 400]
    check("vol.join(" in body, "build volume must come from the profile, not be typed")
    check("256" not in body, "the build volume is hard-coded into the strip")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("VIEWER MACHINE MARKINGS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIEWER MACHINE MARKINGS TESTS OK — the handle is the real horizontal "
          "silver pill, labels cannot mirror, no logo art is reproduced, the side "
          "mark stays tone-on-tone and the bed strip stays P1S-only.")


if __name__ == "__main__":
    run()
