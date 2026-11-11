#!/usr/bin/env python3
"""Trace Scott's OBC logo (openscad_models/brand/icons/obc_logo_master_1600.png)
into a clean outline SVG in millimetres, and measure its stripes.

Scott, 2026-11-11: "I'm not changing the logo", then "a 3d print designed of my
logo so I can print a real one". The vector OBC in assets/brand/ is Montserrat
Black, which overlaps this logo's letters by only 85% (best weight and spacing):
the logo's letters sit closer together. So the letters are traced from the logo
itself. They are bold, about 500 px tall, so a trace is good to about 0.1 mm at
sign size.

The gold has dark horizontal stripes. They're closed over (vertically only, so
letters and counters are untouched) to get the letter outline, and measured
separately: three groups of four, each a faint line then three strong ones.

The gold's 2D shapes for the sign are made here too, at the sign's real size,
with shapely: the letters with the stripes cut out, and any gold narrower than
MIN_GOLD removed. OpenSCAD's own offsets left the gold touching itself at single
points, which made non-manifold edges in the mesh; shapely resolves those.

    python3 trace_obc.py        (writes obc_outline.svg, stripes.json, letters_2d.scad,
                                 trace_check.png)
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import Polygon
from shapely.ops import unary_union
from skimage import measure

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "icons" / "obc_logo_master_1600.png"
WIDTH_MM = 100.0  # the SVG is written at this width; the .scad scales it
LOGO_W = 150.0    # the sign's letters, left to right (mm); the .scad checks it matches
MIN_LINE = 0.4    # no stripe narrower than this (DETAIL_STANDARD rule 5)
MIN_GOLD = 1.2    # no gold narrower than this: it stands 2.4 proud, so 3 beads


def gold_mask(a):
    # by warmth, not brightness: the dark stripes are a deep brown (r-b >= 42) and the
    # background is neutral (r-b <= 2), so this keeps the stripe pixels and the
    # dim bevel round each letter's bottom (r-b about 10-20), which is its real edge
    return (a[:, :, 0] - a[:, :, 2] > 9) & (a[:, :, 0] > 30)


def main():
    a = np.asarray(Image.open(SRC).convert("RGB")).astype(int)
    gold = gold_mask(a)
    ys, xs = np.where(gold)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    solid = ndimage.binary_closing(gold, structure=np.ones((17, 1)))
    solid = ndimage.binary_opening(solid, structure=np.ones((3, 3)))
    field = ndimage.gaussian_filter(solid.astype(float), 1.2)
    contours = measure.find_contours(field, 0.5)
    polys = [Polygon([(c[1], c[0]) for c in con]) for con in contours if len(con) > 40]
    # even-odd: outer outlines minus counters
    shape = Polygon()
    for p in sorted(polys, key=lambda p: -p.area):
        p = p.buffer(0)
        shape = shape.symmetric_difference(p)
    shape = shape.simplify(0.35)
    k = WIDTH_MM / (x1 - x0)
    H = (y1 - y0) * k
    # SVG in mm, y down, origin at the letters' top-left
    def ring(r):
        return "M" + " ".join(f"{(x - x0) * k:.4f},{(y - y0) * k:.4f}" for x, y in r.coords) + "Z"
    paths = []
    for g in getattr(shape, "geoms", [shape]):
        paths.append(ring(g.exterior) + "".join(ring(i) for i in g.interiors))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH_MM}mm" height="{H:.4f}mm" '
           f'viewBox="0 0 {WIDTH_MM} {H:.4f}">\n<title>OBC traced from obc_logo_master_1600.png</title>\n'
           f'<path fill="#000" fill-rule="evenodd" d="{" ".join(paths)}"/>\n</svg>\n')
    (HERE / "obc_outline.svg").write_text(svg)

    # stripes: dark rows through the B's left stem (solid gold there), as fractions of letter height
    br = a[y0:y1 + 1, 650:700].sum(axis=2).mean(axis=1)
    med = np.median(br)
    rows = []
    for lim, kind in ((0.55, "any"),):
        dark = br < lim * med
        s = None
        for i, d in enumerate(np.append(dark, False)):
            if d and s is None:
                s = i
            if not d and s is not None:
                lo, hi = s / (y1 - y0), (i - 1 + 1) / (y1 - y0)
                depth = float(1 - br[s:i].min() / med)
                rows.append({"top": round(lo, 4), "bottom": round(hi, 4), "darkness": round(depth, 3)})
                s = None
    # the letters' own top and bottom bevels read as dark rows too; they are edges, not stripes
    rows = [r for r in rows if 0.02 < r["top"] and r["bottom"] < 0.98]
    json.dump({"height_over_width": round(H / WIDTH_MM, 5), "stripes": rows}, open(HERE / "stripes.json", "w"), indent=1)
    # the same, for the .scad: [top, bottom, strong?] as fractions of letter height from the top.
    # Strong lines (darker than 0.65) read as black in the logo; the faint first line of each
    # group reads as a shadow.
    with open(HERE / "stripes.scad", "w") as f:
        f.write("// written by trace_obc.py from obc_logo_master_1600.png -- do not edit\n")
        f.write(f"logo_h_over_w = {H / WIDTH_MM:.5f};\n")
        f.write("stripes = [\n" + ",\n".join(
            f"  [{r['top']}, {r['bottom']}, {'true' if r['darkness'] > 0.65 else 'false'}]" for r in rows) + "\n];\n")

    write_gold(shape, x0, y0, x1, y1, rows)

    # check: the traced outline drawn over the logo
    im = Image.open(SRC).convert("RGB")
    d = ImageDraw.Draw(im)
    for g in getattr(shape, "geoms", [shape]):
        for r in [g.exterior, *g.interiors]:
            d.line(list(r.coords), fill=(0, 255, 255), width=2)
    im.crop((x0 - 20, y0 - 20, x1 + 20, y1 + 20)).save(HERE / "trace_check.png")
    print(f"{len(paths)} letters, {sum(len(g.interiors) for g in getattr(shape, 'geoms', [shape]))} counters, "
          f"H/W {H / WIDTH_MM:.4f}, {len(rows)} stripes")


def write_gold(shape, x0, y0, x1, y1, rows):
    """letters_2d.scad: gold_deep() (letters less the strong stripes) and gold_top()
    (less the faint ones too), centred on the origin, y up, in mm at LOGO_W."""
    from shapely import affinity
    from shapely.geometry import box
    k = LOGO_W / (x1 - x0)
    H = (y1 - y0) * k
    L = affinity.affine_transform(shape, [k, 0, 0, -k, -(x0 * k) - LOGO_W / 2, y0 * k + H / 2])

    def bars(strong):
        out = []
        for r in rows:
            if (r["darkness"] > 0.65) != strong:
                continue
            top = H / 2 - r["top"] * H
            w = max(MIN_LINE, (r["bottom"] - r["top"]) * H)
            out.append(box(-LOGO_W / 2 - 1, top - w, LOGO_W / 2 + 1, top))
        return unary_union(out)

    def opened(g):
        r = MIN_GOLD / 2
        g = g.buffer(-r, join_style="round").buffer(r, join_style="round")
        return g.buffer(-0.01, join_style="mitre").simplify(0.01).buffer(0)

    deep = opened(L.difference(bars(True)))
    top = opened(L.difference(bars(True)).difference(bars(False))).intersection(deep).buffer(0)

    def scad_module(name, g):
        pts, paths = [], []
        for poly in getattr(g, "geoms", [g]):
            # pieces under 4 mm2 are scraps the sliver filter leaves (two 1.2 mm dots in the
            # B's lower counter), not part of the logo
            if poly.is_empty or poly.geom_type != "Polygon" or poly.area < 4.0:
                continue
            for ring in [poly.exterior, *poly.interiors]:
                c = list(ring.coords)[:-1]
                paths.append(list(range(len(pts), len(pts) + len(c))))
                pts += c
        P = ",".join(f"[{x:.4f},{y:.4f}]" for x, y in pts)
        Q = ",".join("[" + ",".join(map(str, p)) + "]" for p in paths)
        return f"module {name}() polygon(points=[{P}], paths=[{Q}]);\n"

    with open(HERE / "letters_2d.scad", "w") as f:
        f.write("// written by trace_obc.py -- do not edit\n")
        f.write(f"letters_2d_logo_w = {LOGO_W};\nletters_2d_logo_h = {H:.4f};\n")
        f.write(scad_module("gold_deep", deep))
        f.write(scad_module("gold_top", top))
    print(f"gold: {deep.area:.0f} mm2 deep, {top.area:.0f} mm2 top, {len(getattr(deep, 'geoms', [deep]))} pieces")


if __name__ == "__main__":
    main()
