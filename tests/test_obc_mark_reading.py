"""
The OBC maker's mark must read "OBC", the right way up, when a piece is
tipped back to look underneath (front edge, -y, away from you).

Scott's first matte-white cottage (2026-10-25) came off the bed reading
"ƆᗺO" the way he turned it over. The library used mirror([1, 0, 0]), which
reads right only when the piece is turned side to side. O, B and C look
almost the same flipped either way, so a code read never caught it. This test
reads the real cut geometry instead: it slices obc_cut() and obc_inlay() at
mid-depth, lays the section out as seen tipped back, and checks letter order,
which way the B faces and which way up it is.

Run: python tests/test_obc_mark_reading.py
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy import ndimage
from shapely import contains_xy
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "openscad_models" / "brand" / "obc_mark.scad"
PX = 40                                   # pixels per mm

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _section(body: str) -> np.ndarray:
    """Slice the 3D body at z, return its ink as seen from ABOVE (row 0 = +y)."""
    with tempfile.TemporaryDirectory() as td:
        src, svg = Path(td) / "m.scad", Path(td) / "m.svg"
        src.write_text(f'include <{LIB}>\n{body}\n')
        env = dict(os.environ, OPENSCADPATH=str(ROOT / "assets" / "openscad_libs"))
        r = subprocess.run(["openscad", "-o", str(svg), str(src)], capture_output=True,
                           text=True, env=env, timeout=300)
        if not svg.exists():
            raise RuntimeError(f"openscad failed:\n{r.stderr[-1500:]}")
        polys = []
        for d in re.findall(r'd="([^"]+)"', svg.read_text()):
            for sub in re.split(r"[Zz]", d):
                n = [float(v) for v in re.findall(r"-?[\d.]+(?:e-?\d+)?", sub)]
                if len(n) >= 6:
                    polys.append(Polygon(list(zip(n[0::2], n[1::2]))))
    xs = np.arange(-20, 20, 1 / PX)
    X, Y = np.meshgrid(xs, xs)
    ink = np.zeros(X.shape, bool)
    for p in polys:                       # SVG y runs down, so sample at -y
        ink ^= contains_xy(p, X, -Y)
    return ink[::-1, :]


def _glyphs(img: np.ndarray):
    """The three letters, left to right, as (mask cropped to the letter, has_hole)."""
    lab, n = ndimage.label(img)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() < 200:
            continue
        rows, cols = np.where(m)
        crop = m[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
        holes = ndimage.label(~np.pad(crop, 1))[1] - 1
        out.append((cols.min(), crop, holes))
    out.sort(key=lambda g: g[0])
    return [(c, h) for _, c, h in out]


def _b_reads_right(b: np.ndarray) -> tuple[bool, bool]:
    """(spine on the left, bigger bowl at the bottom) for a B's mask."""
    h, w = b.shape
    spine_left = b[:, : max(1, w // 8)].mean() > b[:, -max(1, w // 8):].mean()
    def reach(rows):                      # how far the bowl's ink reaches out from the spine
        cols = [np.where(r)[0] for r in rows if r.any()]
        far = [c.max() if spine_left else w - 1 - c.min() for c in cols]
        return np.mean(far)
    bottom_bigger = reach(b[int(h * 0.62):]) > reach(b[: int(h * 0.38)])
    return spine_left, bottom_bigger


def _reads_obc(img: np.ndarray, label: str) -> None:
    g = _glyphs(img)
    check(len(g) == 3, f"{label}: expected 3 letters, found {len(g)}")
    if len(g) != 3:
        return
    (first, h0), (mid, h1), (last, h2) = g
    check(h0 == 1 and h2 == 0, f"{label}: expected O on the left and C on the right "
          f"(holes {h0}, {h1}, {h2}) -- the mark reads backwards")
    check(h1 == 2, f"{label}: the middle letter should be a B with two counters, found {h1}")
    spine_left, bottom_bigger = _b_reads_right(mid)
    check(spine_left, f"{label}: the B's spine is on the right -- mirrored")
    check(bottom_bigger, f"{label}: the B's bigger bowl is on top -- upside down")


def test_reference_text_reads_right_from_above():
    # Calibrates the checks themselves: plain text seen from above IS correct.
    # If this fails, the reader is wrong, not the mark.
    _reads_obc(_section('translate([0,0,-0.3]) projection(cut=true) translate([0,0,-0.3]) '
                        'linear_extrude(1) text("OBC", size=6, font=OBC_FONT, halign="center", valign="center");'),
               "plain text from above")


def test_cut_reads_obc_when_tipped_back():
    above = _section("projection(cut=true) translate([0,0,-0.4]) obc_cut(4.6);")
    _reads_obc(above[::-1, :], "obc_cut tipped back")      # tipped back: y flips, x stays


def test_inlay_reads_obc_when_tipped_back():
    above = _section("projection(cut=true) translate([0,0,-0.4]) obc_inlay(4.6);")
    _reads_obc(above[::-1, :], "obc_inlay tipped back")


def test_engrave_reads_obc_when_tipped_back():
    above = _section("projection(cut=true) translate([0,0,-0.5]) obc_engrave(6, 0.8, ridges=false);")
    _reads_obc(above[::-1, :], "obc_engrave tipped back")


def test_turned_side_to_side_is_the_wrong_way():
    # The old orientation: proves the test can tell the two apart.
    above = _section("projection(cut=true) translate([0,0,-0.4]) obc_cut(4.6);")
    before = len(_failures)
    _reads_obc(above[:, ::-1], "side to side")
    caught = len(_failures) > before
    del _failures[before:]
    check(caught, "turning the piece side to side should read upside down; the checks cannot tell")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("OBC MARK READING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("OBC MARK READING TESTS OK — the cut, inlay and engraved marks read OBC the right "
          "way up when a piece is tipped back to look underneath.")


if __name__ == "__main__":
    run()
