"""
Functional audit: tools/gen_lifestyle_scene.py -- _is_mat_pixel() and
detect_mat_bounds(), the pixel-detection logic that locates the white/cream
mat rectangle in an AI-generated room scene so the real product art can be
composited into it.

Pure image-processing logic (PIL Image in, tuple/None out) -- no external
I/O, so this is tested directly against synthetic images with a known mat
region, no mocking required for the function under test itself. The DB/
env setup below still follows this repo's standard harness because
`gen_lifestyle_scene` is imported as a normal module (it does read
OPENAI_API_KEY at import time but never calls out to it at import time --
no live network call is made by importing or by calling detect_mat_bounds).
"""
import os, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402  (imported per repo convention; not used directly by these tests)
from PIL import Image  # noqa: E402
import gen_lifestyle_scene as gls  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


def _make_mat_image(w, h, mat_box, bg=(20, 20, 20), mat=(240, 240, 235)):
    """Solid dark background with a solid light rectangular 'mat' region."""
    img = Image.new('RGB', (w, h), bg)
    l, t, r, b = mat_box
    for y in range(t, b):
        for x in range(l, r):
            img.putpixel((x, y), mat)
    return img


def _expected_inner(mat_box):
    """Mirror the module's own inset formula so tolerance is about
    sampling discretization, not about re-deriving the border math."""
    l, t, r, b = mat_box
    w, h = r - l, b - t
    border = max(12, int(min(w, h) * 0.06))
    return l + border, t + border, r - border, b - border


def _assert_close(actual, expected, tol, label):
    check(actual is not None, f"{label}: expected bounds, got None")
    if actual is None:
        return
    for a, e, name in zip(actual, expected, ("left", "top", "right", "bottom")):
        check(abs(a - e) <= tol,
              f"{label}: {name} off by {abs(a-e)}px (got {a}, expected ~{e}, tol={tol})")


# ── Positive cases: mat spans >=35% of both axes (the col/row scan's own
#    requirement -- see test_narrow_mat_relative_to_canvas_returns_none
#    below for the documented limitation when it doesn't) ──────────────────

def test_detects_centered_square_mat():
    box = (100, 100, 300, 300)  # 200x200 in 400x400 = 50%
    img = _make_mat_image(400, 400, box)
    bounds = gls.detect_mat_bounds(img)
    _assert_close(bounds, _expected_inner(box), tol=10, label="centered 200x200/400x400")


def test_detects_mat_upper_left_quadrant():
    box = (20, 20, 180, 180)  # 160x160 in 400x400 = 40%, off-center
    img = _make_mat_image(400, 400, box)
    bounds = gls.detect_mat_bounds(img)
    _assert_close(bounds, _expected_inner(box), tol=10, label="upper-left 160x160/400x400")


def test_detects_mat_bottom_right_quadrant():
    box = (220, 220, 380, 380)  # 160x160 in 400x400, opposite corner
    img = _make_mat_image(400, 400, box)
    bounds = gls.detect_mat_bounds(img)
    _assert_close(bounds, _expected_inner(box), tol=10, label="bottom-right 160x160/400x400")


def test_detects_mat_different_size_37pct():
    box = (125, 125, 275, 275)  # 150x150 in 400x400 = 37.5%
    img = _make_mat_image(400, 400, box)
    bounds = gls.detect_mat_bounds(img)
    _assert_close(bounds, _expected_inner(box), tol=10, label="centered 150x150/400x400 (37.5%)")


def test_returned_bounds_are_ordered_and_inside_canvas():
    box = (100, 100, 300, 300)
    img = _make_mat_image(400, 400, box)
    l, t, r, b = gls.detect_mat_bounds(img)
    check(0 <= l < r <= 400, f"left/right not sane: l={l} r={r}")
    check(0 <= t < b <= 400, f"top/bottom not sane: t={t} b={b}")


# ── Sanity: no crash, no nonsense bounds, when there's no clear mat ────────

def test_solid_dark_background_returns_none():
    img = Image.new('RGB', (400, 400), (20, 20, 20))
    check(gls.detect_mat_bounds(img) is None, "solid dark image should yield no mat detected")


def test_dark_random_noise_returns_none():
    import random
    rnd = random.Random(1)
    img = Image.new('RGB', (400, 400))
    px = img.load()
    for y in range(400):
        for x in range(400):
            px[x, y] = (rnd.randint(0, 80), rnd.randint(0, 80), rnd.randint(0, 80))
    check(gls.detect_mat_bounds(img) is None, "dark noise image should yield no mat detected")


def test_gray_region_below_brightness_threshold_returns_none():
    # (150,150,150) is neutral (zero saturation) but below thresh=185 -- must
    # not be mistaken for a white/cream mat.
    box = (100, 100, 300, 300)
    img = _make_mat_image(400, 400, box, mat=(150, 150, 150))
    check(gls.detect_mat_bounds(img) is None,
          "gray region below brightness threshold should not be detected as mat")


def test_bright_saturated_color_returns_none():
    # Bright red is "light" in the sense of high R, but far too saturated
    # to be a white/cream mat -- must not be mistaken for one.
    box = (100, 100, 300, 300)
    img = _make_mat_image(400, 400, box, mat=(250, 50, 50))
    check(gls.detect_mat_bounds(img) is None,
          "saturated bright-red region should not be detected as mat")


def test_mat_covering_almost_entire_canvas_returns_none():
    box = (10, 10, 390, 390)  # 95% of 400x400 -- exceeds the 85% sanity cap
    img = _make_mat_image(400, 400, box)
    check(gls.detect_mat_bounds(img) is None,
          "mat spanning >85% of canvas should be rejected by the sanity check")


def test_uniform_white_canvas_returns_none():
    img = Image.new('RGB', (400, 400), (250, 250, 250))
    check(gls.detect_mat_bounds(img) is None,
          "an entirely white canvas (100% mat-colored) should be rejected, not treated as a giant mat")


def test_tiny_image_does_not_crash():
    img = Image.new('RGB', (10, 10), (20, 20, 20))
    try:
        result = gls.detect_mat_bounds(img)
    except Exception as e:
        check(False, f"detect_mat_bounds crashed on a 10x10 image: {e!r}")
    else:
        check(result is None, "10x10 image has no room for a valid mat; expected None")


def test_narrow_mat_relative_to_canvas_returns_none_not_wrong_bounds():
    """Documented limitation, not exercised as a bug: the row scan requires
    >=35% of the FULL canvas width to be mat-colored (row_threshold), and the
    column scan requires >=35% of the full canvas height. A mat that is a
    real, valid rectangle (10-85% of canvas by area, per the function's own
    sanity check) but narrow on one axis relative to the *other* axis's full
    span will fail one of the two scans and return None rather than a
    partial/incorrect box. This asserts that failure mode is a clean None,
    never a silently wrong box -- which is the actual safety property this
    audit is checking."""
    box = (50, 150, 150, 350)  # 100x200 in 400x400: width is only 25% of W
    img = _make_mat_image(400, 400, box)
    bounds = gls.detect_mat_bounds(img)
    check(bounds is None,
          f"expected None for a mat too narrow on one axis relative to canvas, got {bounds}")


# ── _is_mat_pixel direct edge-case checks ──────────────────────────────────

def test_is_mat_pixel_thresholds():
    check(gls._is_mat_pixel(200, 200, 190) is True,
          "bright neutral pixel (200,200,190) should be a mat pixel")
    check(gls._is_mat_pixel(185, 185, 185) is False,
          "exactly-at-threshold brightness (185,185,185) should NOT count (strict >)")
    check(gls._is_mat_pixel(186, 186, 186) is True,
          "just-above-threshold brightness (186,186,186) should count")
    check(gls._is_mat_pixel(200, 200, 160) is False,
          "saturation of exactly max_sat (40) should NOT count (strict <)")
    check(gls._is_mat_pixel(225, 225, 186) is True,
          "saturation just under max_sat (39), all channels above brightness thresh, should count")
    check(gls._is_mat_pixel(255, 0, 0) is False,
          "pure red (bright but fully saturated) must not count as a mat pixel")
    check(gls._is_mat_pixel(0, 0, 0) is False,
          "black must not count as a mat pixel")


def run():
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FUNCTIONAL AUDIT TESTS OK -- detect_mat_bounds() correctly locates a light "
          "rectangular mat against a dark background at several sizes/positions when the "
          "mat spans enough of both axes, and safely returns None (never a crash, never a "
          "wrong/nonsense box) when no clear mat region exists, including the documented "
          "narrow-mat-relative-to-canvas limitation of the column/row threshold scan.")


if __name__ == "__main__":
    run()
