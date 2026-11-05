"""tools/sdf_figure.py: the figurine tool's printability helpers, on the real
defects found building the Kawaii Cow (2026-11-04).

- self_support() re-thresholded each layer to whole pixels before eroding it,
  so its cones shrank a whole 0.25 mm pixel per 0.25 mm layer: 45 deg, not the
  37 asked for, and the slicer propped them (12,222 support moves).
- base_prism() copied the field from 0.8 mm into the layer just above the
  plate, and marching cubes put the bottom face at z = -0.13: the slicer
  lifted the whole figure and the maker's mark slid off its layers.
- heart2d() as a plain union of fields read near zero along an internal line,
  and the puffy heart's face had a fold across it; exact2d() measures instead.
- a thin upright leaf (an ear) can't be held up by 3-D cones, which erode
  through it from both faces; support_rows() makes its outline printable in
  its own plane.
- the Teacup Bear's handle hole: cut in the field, marching cubes softened its
  edges and the slicer propped it; teardrop_prism() cuts it exactly. Its arc
  must stop where the roof touches it: run on to 90 - roof deg it is a
  ceiling (a first draft did, and drew 841 support moves).
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import sdf_figure as sf  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _layer_radius(g, d, k):
    """Equivalent radius of layer k's solid, from its area (mm)."""
    area = (d[:, :, k] < 0).sum() * g.step ** 2
    return np.sqrt(area / np.pi)


def test_self_support_cone_keeps_its_angle():
    # a ball floating above the plate: everything under it is grown as a cone
    g = sf.Grid((-12, -12, 0), (12, 12, 24), 0.25)
    d = sf.ellipsoid(g, (0, 0, 16), (6, 6, 6))
    out, added = sf.self_support(g, d, angle=37.0)
    check(added > 0, "a floating ball should grow a cone under it")
    # below the ball's 37 deg latitude the layers shrink at tan(37) per mm
    # the cone runs from the 37 deg latitude (z 12.4) to its tip (z 6.0)
    ks = [k for k, z in enumerate(g.axes[2]) if 7 < z < 10]
    r = np.array([_layer_radius(g, out, k) for k in ks])
    z = g.axes[2][ks]
    slope = np.polyfit(z, r, 1)[0]
    check(abs(slope - np.tan(np.radians(37))) < 0.06,
          f"cone should widen {np.tan(np.radians(37)):.3f} mm per mm, got {slope:.3f} (45 deg reads 1.0)")


def test_base_prism_leaves_the_base_on_the_plate():
    g = sf.Grid((-10, -10, -1.5), (10, 10, 10), 0.25)
    # a ball sunk into the plate, cut flat: its sides lean out above z = 0
    d = sf.cut_base(g, sf.ellipsoid(g, (0, 0, 3), (6, 6, 6)))
    d = sf.base_prism(g, d, 0.8)
    m = sf.mesh(g, d)
    check(abs(m.bounds[0][2]) < 0.02, f"the base should sit at z = 0, got {m.bounds[0][2]:.3f}")
    check(m.is_watertight, "the prism-footed ball should mesh closed")


def test_heart_sides_lean_37_and_face_has_no_internal_seam():
    us = np.arange(-15, 15.01, 0.1)
    vs = np.arange(-2, 26.01, 0.1)
    U, V = np.meshgrid(us, vs, indexing="ij")
    d, h = sf.heart2d(U, V, 22)
    inside = d < 0
    for v0, v1 in ((3, 9),):
        w0 = U[:, np.argmin(abs(vs - v0))][inside[:, np.argmin(abs(vs - v0))]].max()
        w1 = U[:, np.argmin(abs(vs - v1))][inside[:, np.argmin(abs(vs - v1))]].max()
        slope = (w1 - w0) / (v1 - v0)
        check(abs(slope - 0.7536) < 0.03, f"heart side should lean 37 deg (0.754 per mm), got {slope:.3f}")
    # the true distance has no near-zero line inside: where the lobes meet
    # the V, the union of fields read about 0 deep inside the heart
    exact = sf.exact2d(lambda u, v: sf.heart2d(u, v, 22)[0], us, vs)
    k = np.argmin(abs(vs - (h * 0.45)))
    i = np.argmin(abs(us - 0.0))
    check(exact[i, k] < -3.0, f"middle of the heart should be well inside, exact distance {exact[i, k]:.2f}")


def test_support_rows_holds_up_a_leaf():
    # an upright leaf pointing up and out at 50 deg: its lower outline is
    # flatter than 37 deg from upright near its lowest point
    step = 0.05
    us = np.arange(0, 20, step)
    vs = np.arange(0, 20, step)
    U, V = np.meshgrid(us, vs, indexing="ij")
    a, b, t = 6.0, 3.6, np.radians(50)
    du, dv = U - 10, V - 10
    p = du * np.cos(t) + dv * np.sin(t)
    q = -du * np.sin(t) + dv * np.cos(t)
    leaf = (p / a) ** 2 + (q / b) ** 2 < 1
    held = sf.support_rows(leaf, step, step, 37.0)
    lim = step * np.tan(np.radians(37)) + step
    worst = 0.0
    rows = [k for k in range(held.shape[1]) if held[:, k].any()]
    for k in rows[1:]:
        below, here = held[:, k - 1], held[:, k]
        if not below.any():
            continue
        lo_b, hi_b = us[below].min(), us[below].max()
        lo_h, hi_h = us[here].min(), us[here].max()
        worst = max(worst, lo_b - lo_h, hi_h - hi_b)
    check(worst <= lim + 1e-6, f"each row should overhang the one below by <= {lim:.3f} mm, worst {worst:.3f}")
    # and the raw leaf did not, so the test means something
    raw_worst = 0.0
    rows = [k for k in range(leaf.shape[1]) if leaf[:, k].any()]
    for k in rows[1:]:
        below, here = leaf[:, k - 1], leaf[:, k]
        if below.any():
            raw_worst = max(raw_worst, us[below].min() - us[here].min(), us[here].max() - us[below].max())
    check(raw_worst > lim, f"the raw leaf should overhang (worst {raw_worst:.3f}), or this test proves nothing")


def test_teardrop_hole_never_ceilings():
    from shapely.geometry import Polygon
    roof = 28.0
    P = sf.teardrop_prism(0.0, 10.0, 3.4, roof, length=4.0)
    m = sf.from_manifold(P)
    # its section in the x-z plane, at y = 0
    sec = m.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
    poly = Polygon(max(sec.discrete, key=len)[:, [0, 2]])
    zs = np.arange(10.0, poly.bounds[3], 0.05)
    widths = []
    for z in zs:
        line = poly.intersection(Polygon([(-9, z), (9, z), (9, z + 1e-4), (-9, z + 1e-4)]))
        widths.append(line.bounds[2] - line.bounds[0] if not line.is_empty else 0.0)
    shrink = -np.diff(widths) / 2 / 0.05          # per side, per mm of height
    worst = float(shrink.max())
    check(worst <= np.tan(np.radians(roof)) + 0.05,
          f"above its middle the hole should close no faster than tan({roof}) = "
          f"{np.tan(np.radians(roof)):.3f} a side per mm; it closes {worst:.3f} somewhere (a ceiling)")


def test_joined_grooves_the_seam_on_top_only():
    """2026-11-05, Scott on the cow v2 body in one colour: "I need more
    defined separation of body parts". joined() keeps the blend (the
    structure under a limb) and cuts a V along the seam, but only where the
    surface faces sideways or up, and only where `where` allows: grooves
    under her hooves and out through her feet's fronts opened ceilings the
    slicer propped."""
    g = sf.Grid((-12, -6, -10), (12, 6, 10), 0.2)
    a = sf.ellipsoid(g, np.array([-4.5, 0, 0], np.float32), np.array([5, 5, 5], np.float32))
    b = sf.ellipsoid(g, np.array([4.5, 0, 0], np.float32), np.array([5, 5, 5], np.float32))
    blend = sf.smin(a, b, 3.0)
    j = sf.joined(a, b, 3.0, (0.7, 1.1))
    zs = g.axes[2]
    ix, iy = np.argmin(abs(g.axes[0])), np.argmin(abs(g.axes[1]))
    col_b, col_j = blend[ix, iy, :], j[ix, iy, :]
    top_b, top_j = zs[col_b < 0].max(), zs[col_j < 0].max()
    bot_b, bot_j = zs[col_b < 0].min(), zs[col_j < 0].min()
    check(top_b - top_j > 0.8, f"the seam's top should be grooved about 1.1 deep: {top_b:.2f} -> {top_j:.2f}")
    check(abs(bot_b - bot_j) < 0.25, f"the seam's underside must keep the blend: {bot_b:.2f} -> {bot_j:.2f}")
    # away from the seam, nothing changes
    ia = np.argmin(abs(g.axes[0] + 6.0))
    check(np.array_equal(blend[ia] < 0, j[ia] < 0), "joined() changed the parts away from their seam")
    # where says no: no groove
    n = sf.joined(a, b, 3.0, (0.7, 1.1), where=np.ones_like(a))
    check(np.array_equal(n < 0, blend < 0), "where=positive everywhere must leave the plain blend")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("SDF FIGURE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("SDF FIGURE TESTS OK — cones keep 37 deg, the base stays on the plate, the heart's "
          "face has no seam, and a thin leaf is held up in its own plane.")


if __name__ == "__main__":
    run()
