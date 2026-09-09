#!/usr/bin/env python3
"""Measure the real printed stroke width of engraved or raised text.

    python3 tools/glyph_probe.py "J" --font "Fredoka:style=Regular" --size 18
    python3 tools/glyph_probe.py --alphabet --font "Poppins:style=SemiBold" --size 18

Width against the available flat run says nothing about whether text can print.
"OnBrandCraftz" in Caveat Bold cleared every width check this shop had and its
thinnest strokes measured 0.48-1.08 extrusions -- under one extrusion the slicer
emits nothing, so three of four models carried a mark that would have come out
blank (2026-09-06). Stroke width is the number that decides it, and it can only
be had by measuring the actual glyph outline the font produces.

Method: extrude the text, take a horizontal section, rasterise it, distance-
transform, and read the ridge -- the local maxima of the transform are the
centreline of every stroke, and twice the smallest ridge value is the thinnest
stroke anywhere in the text.

Written 2026-09-09, the third time this measurement was needed by hand.
"""
import argparse
import json
import string
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from scipy import ndimage
from shapely import contains_xy

ROOT = Path(__file__).resolve().parent.parent
_LIBS = ROOT / "assets" / "openscad_libs"
_EXTRUSION_MM = 0.42          # one bead on the 0.4mm nozzle, 0.2mm layer profile
_MIN_EXTRUSIONS = 2.0         # the standing rule for a maker's mark


def _glyph_polygons(text: str, font: str, size: float):
    """Extrude the text in OpenSCAD and return its cross-section polygons."""
    # json.dumps, never repr: Python's !r emits SINGLE quotes and OpenSCAD only
    # accepts double-quoted strings, so every call was a silent parser error.
    scad = (f'linear_extrude(2) text({json.dumps(text)}, size={size}, '
            f'font={json.dumps(font)}, halign="center", valign="center");')
    with tempfile.TemporaryDirectory() as td:
        src, stl = Path(td) / "g.scad", Path(td) / "g.stl"
        src.write_text(scad)
        env = {"OPENSCADPATH": str(_LIBS), "PATH": "/usr/bin:/bin:/usr/local/bin",
               "HOME": str(Path.home())}
        r = subprocess.run(["openscad", "-o", str(stl), str(src)],
                           capture_output=True, text=True, env=env, timeout=180)
        if not stl.exists() or stl.stat().st_size == 0:
            raise RuntimeError(f"openscad produced nothing for {text!r}: {r.stderr[-300:]}")
        mesh = trimesh.load(str(stl), force="mesh")
    section = mesh.section(plane_origin=[0, 0, 1], plane_normal=[0, 0, 1])
    if section is None:
        raise RuntimeError(f"no cross-section for {text!r} -- empty glyph?")
    return section.to_2D()[0].polygons_full


def stroke_widths(text: str, font: str, size: float, px: float = 0.02):
    polys = _glyph_polygons(text, font, size)
    bounds = np.array([p.bounds for p in polys])
    minx, miny = bounds[:, 0].min(), bounds[:, 1].min()
    maxx, maxy = bounds[:, 2].max(), bounds[:, 3].max()
    w = int((maxx - minx) / px) + 8
    h = int((maxy - miny) / px) + 8
    ys, xs = np.mgrid[0:h, 0:w]
    X, Y = minx + (xs - 4) * px, miny + (ys - 4) * px
    grid = np.zeros((h, w), bool)
    for p in polys:
        grid |= contains_xy(p, X, Y)
    dt = ndimage.distance_transform_edt(grid) * px
    # THE DECISION NUMBER IS frac_thin, NOT THE MINIMUM. The minimum picks up a
    # single-pixel local maximum wherever two strokes meet at an acute angle or
    # a stroke terminates, and reports it as the stroke width. Measured
    # 2026-09-09: that scored Poppins SemiBold's G, K, Q, R and V at 0.04mm
    # (0.10 extrusions) and would have rejected a perfectly printable font,
    # while rounded Fredoka passed only because it has no sharp corners to
    # trip over. Technique 53 already documents exactly this for inlay_probe --
    # "read frac_thin, never min_width" -- and the same applies to a glyph.
    #
    # What actually matters is whether a MEANINGFUL AREA of the glyph is under
    # one extrusion, because that is the area the slicer drops. A one-pixel
    # corner is not.
    # WHAT SURVIVES A BRUSH ONE BEAD WIDE. Two earlier metrics were wrong and
    # both looked plausible:
    #   * min of the distance-transform ridge -- picks up a single-pixel local
    #     maximum where two strokes meet at an acute angle and calls it the
    #     stroke width. Scored Poppins SemiBold's G at 0.04mm.
    #   * fraction of area within half a bead of an edge -- that is just the
    #     boundary band, structurally ~2*(bead/2)/stroke for ANY shape, so every
    #     font landed near 12% regardless of how thick it was.
    #
    # The real question is morphological: erode the glyph by half a bead, dilate
    # it back, and see what did not come back. That is an OPENING, and it is
    # exactly what an extruder physically does -- it cannot lay a line narrower
    # than its own bead, so anything that vanishes under the opening is area the
    # slicer will simply not emit.
    half_extrusion = _EXTRUSION_MM / 2.0
    inside = dt > 0
    core = dt >= half_extrusion                       # what a bead centre can reach
    if not core.any():
        return {"text": text, "font": font, "size": size,
                "extent_mm": (round(float(maxx - minx), 2), round(float(maxy - miny), 2)),
                "frac_lost": 1.0, "typical_mm": 0.0, "typical_extrusions": 0.0,
                "min_mm_unreliable": 0.0}
    reach = ndimage.distance_transform_edt(~core) * px
    reproduced = inside & (reach <= half_extrusion)    # dilate the core back
    frac_lost = 1.0 - float(reproduced.sum()) / float(inside.sum())

    ridge = (dt == ndimage.maximum_filter(dt, size=3)) & (dt > 0)
    half = dt[ridge]
    return {
        "text": text, "font": font, "size": size,
        "extent_mm": (round(float(maxx - minx), 2), round(float(maxy - miny), 2)),
        "frac_lost": round(frac_lost, 4),
        "typical_mm": round(float(2 * np.median(half)), 3),
        "typical_extrusions": round(float(2 * np.median(half) / _EXTRUSION_MM), 2),
        "min_mm_unreliable": round(float(2 * half.min()), 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Measure real stroke width of text.")
    ap.add_argument("text", nargs="?", default="A")
    ap.add_argument("--font", default="Caveat:style=Bold")
    ap.add_argument("--size", type=float, default=15.0)
    ap.add_argument("--alphabet", action="store_true",
                    help="sweep A-Z and report the worst letter -- a monogram "
                         "product is only as printable as its weakest glyph")
    ap.add_argument("--max-thin", type=float, default=0.05,
                    help="max fraction of the glyph allowed to vanish under a one-bead opening")
    a = ap.parse_args()

    if a.alphabet:
        rows = []
        for ch in string.ascii_uppercase:
            try:
                rows.append(stroke_widths(ch, a.font, a.size))
            except Exception as exc:
                print(f"  {ch}: FAILED -- {exc}")
        rows.sort(key=lambda r: -r["frac_lost"])
        print(f'{a.font} @ size {a.size}')
        for r in rows[:5]:
            print(f'  worst: {r["text"]}  {r["frac_lost"]*100:5.2f}% of the glyph lost   (typical stroke {r["typical_mm"]:.2f} mm)')
        worst = rows[0]
        thinnest = min(rows, key=lambda r: r["typical_extrusions"])
        print(f'  thinnest typical stroke: {thinnest["text"]!r} at '
              f'{thinnest["typical_extrusions"]:.2f} extrusions')
        ok = worst["frac_lost"] <= a.max_thin and thinnest["typical_extrusions"] >= 2.0
        print(f'  -> weakest glyph {worst["text"]!r} at {worst["frac_lost"]*100:.2f}% lost; '
              f'allow {a.max_thin*100:.0f}% -> {"PASS" if ok else "FAIL"}')
        sys.exit(0 if ok else 1)

    r = stroke_widths(a.text, a.font, a.size)
    print(f'{r["text"]!r} in {r["font"]} @ {r["size"]}')
    print(f'  glyph        : {r["extent_mm"][0]} x {r["extent_mm"][1]} mm')
    print(f'  typical stroke: {r["typical_mm"]} mm = {r["typical_extrusions"]} extrusions')
    print(f'  lost to bead : {r["frac_lost"]*100:.2f}% of the glyph')
    # BOTH conditions, validated against real ground truth 2026-09-09:
    #   "OnBrandCraftz" @5.5 -- the mark that actually printed blank -- loses
    #   only 0.46% of its area, so frac_lost alone PASSES it. Its typical stroke
    #   is 1.56 extrusions. "OBC" @15.3, the fix that printed legibly, is 4.46.
    #   frac_lost catches whole strokes vanishing; typical stroke catches a mark
    #   that is uniformly too fine. A real check needs both.
    ok = r["frac_lost"] <= a.max_thin and r["typical_extrusions"] >= 2.0
    print(f'  allow {a.max_thin*100:.0f}% -> {"PASS" if ok else "FAIL"}')
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
