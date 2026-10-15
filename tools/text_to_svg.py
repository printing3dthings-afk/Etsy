#!/usr/bin/env python3
"""Turn text in a font into a TRUE vector SVG -- real bezier outlines, one path.

    python3 tools/text_to_svg.py "OBC" --font /root/.fonts/Montserrat-Bold.ttf \
        --weight 900 --width-mm 20 -o OBC.svg

Why this exists (2026-09-09): the previous OnBrandCraftz logo SVG was a potrace
TRACE of a rendered image. tools/flatten_svg_paths.py's docstring records what
that cost -- 300,000-390,000 facets, and a single CGAL boolean against it ran
past eight minutes without finishing. A trace is pixel data wearing an SVG
costume. Glyph outlines are the real curves the type designer drew: a few dozen
beziers, one path, a couple of KB, and OpenSCAD imports them instantly.

Two traps this handles, both of which silently produce a WRONG logo:

1. VARIABLE FONTS. /root/.fonts/Montserrat-Bold.ttf is named "Bold" and is
   actually a variable font whose default instance is wght=100 -- THIN. Loading
   it naively gives thin outlines while the printed models (which go through
   fontconfig, and do resolve style=Black correctly) are heavy. The font is
   instantiated at the requested weight before a single outline is read.

2. FONT ARTEFACTS THAT ONLY A RASTERISER FORGIVES. Montserrat's "B" is drawn
   as TWO contours, not three: one ring traces the lower counter, steps up 19
   units, traces the upper counter, then closes down a line 5 units to the
   side. That leaves a 5-unit sliver (0.042mm on a 20mm mark) cutting through
   the B's middle bar. FreeType renders it invisibly; OpenSCAD's SVG import
   tessellates it into a visible wedge and the extrusion comes out
   non-manifold -- 12 broken faces, confirmed. So outlines are flattened and
   run through a real polygon boolean, and slots narrower than --heal are
   closed. One extrusion is 0.42mm, so anything that thin could never print
   anyway; healing it is not a liberty, it is the only honest reading of the
   geometry for a print asset.

3. SHAPING. Advance widths alone are not text layout. Both brand faces carry
   their kerning in GPOS, and Caveat is a brush script where the pairs matter
   visibly. Shaping goes through harfbuzz -- the same engine OpenSCAD's text()
   uses -- so the SVG matches what the .scad models render. If uharfbuzz is
   missing this SAYS SO and falls back to raw advances; it never quietly ships
   unkerned type.
"""
from __future__ import annotations

import argparse
import io
import math
import sys
from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from shapely.geometry import Polygon
from shapely.ops import unary_union


def _instantiate(path: str, weight: float | None):
    """Return (TTFont, raw_bytes) pinned to `weight` if the font is variable."""
    font = TTFont(path)
    if "fvar" not in font:
        return font, Path(path).read_bytes()
    from fontTools.varLib import instancer

    axes = {a.axisTag: a for a in font["fvar"].axes}
    if weight is None:
        weight = axes["wght"].maxValue if "wght" in axes else None
    loc = {"wght": weight} if "wght" in axes else {}
    font = instancer.instantiateVariableFont(font, loc, updateFontNames=False)
    buf = io.BytesIO()
    font.save(buf)
    return font, buf.getvalue()


def _shape(raw: bytes, text: str, upm: int, font: TTFont):
    """[(glyph_name, x_offset, y_offset)] in font units, harfbuzz-shaped."""
    order = font.getGlyphOrder()
    try:
        import uharfbuzz as hb
    except ImportError:
        print("WARNING: uharfbuzz not installed -- kerning NOT applied.", file=sys.stderr)
        cmap, hmtx = font.getBestCmap(), font["hmtx"]
        out, x = [], 0.0
        for ch in text:
            gn = cmap.get(ord(ch))
            if gn is None:
                continue
            out.append((gn, x, 0.0))
            x += hmtx[gn][0]
        return out, x

    face = hb.Face(raw)
    hb_font = hb.Font(face)
    hb_font.scale = (upm, upm)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf)
    out, x, y = [], 0.0, 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((order[info.codepoint], x + pos.x_offset, y + pos.y_offset))
        x += pos.x_advance
        y += pos.y_advance
    return out, x


class _FlattenPen(BasePen):
    """Glyph outlines -> closed polylines, subdivided until flat within `tol`."""

    def __init__(self, glyphset, tol):
        super().__init__(glyphset)
        self.tol = tol
        self.contours = []
        self._c = []

    def _moveTo(self, pt):
        self._flush()
        self._c = [pt]

    def _lineTo(self, pt):
        self._c.append(pt)

    def _curveToOne(self, a, b, c):
        self._bez([self._c[-1], a, b, c])

    def _qCurveToOne(self, a, b):
        p0 = self._c[-1]
        self._bez([p0, (p0[0] + 2/3*(a[0]-p0[0]), p0[1] + 2/3*(a[1]-p0[1])),
                   (b[0] + 2/3*(a[0]-b[0]), b[1] + 2/3*(a[1]-b[1])), b])

    def _bez(self, p, depth=0):
        (x0,y0),(x1,y1),(x2,y2),(x3,y3) = p
        dx, dy = x3-x0, y3-y0
        n = math.hypot(dx, dy)
        # flatness = max control-point deviation from the chord
        if n < 1e-12:
            flat = max(math.hypot(x1-x0,y1-y0), math.hypot(x2-x0,y2-y0))
        else:
            flat = max(abs((x1-x0)*dy-(y1-y0)*dx), abs((x2-x0)*dy-(y2-y0)*dx)) / n
        if flat <= self.tol or depth >= 16:
            self._c.append(p[3]); return
        m = lambda a,b: ((a[0]+b[0])/2, (a[1]+b[1])/2)
        p01,p12,p23 = m(p[0],p[1]), m(p[1],p[2]), m(p[2],p[3])
        a,b = m(p01,p12), m(p12,p23)
        mid = m(a,b)
        self._bez([p[0],p01,a,mid], depth+1)
        self._bez([mid,b,p23,p[3]], depth+1)

    def _flush(self):
        if len(self._c) > 2:
            self.contours.append(self._c)
        self._c = []

    _closePath = _endPath = _flush


def _rings_to_polygon(rings):
    """Nest rings by containment: even depth = solid, odd = hole."""
    polys = [Polygon(r) for r in rings if len(r) > 2]
    polys = [p for p in polys if p.area > 0]
    out = []
    for i, p in enumerate(polys):
        depth = sum(1 for j, q in enumerate(polys)
                    if i != j and q.area > p.area and q.contains(p.representative_point()))
        out.append((depth, p))
    solid = unary_union([p.buffer(0) for d, p in out if d % 2 == 0]) if out else None
    holes = [p.buffer(0) for d, p in out if d % 2 == 1]
    if solid is None:
        return None
    return solid.difference(unary_union(holes)) if holes else solid


def _fmt(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def _path_d(geom):
    parts = []
    polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for poly in polys:
        for ring in [poly.exterior, *poly.interiors]:
            pts = list(ring.coords)[:-1]
            parts.append("M" + " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in pts) + "Z")
    return "".join(parts)


def text_to_svg(text: str, font_path: str, weight: float | None = None,
                width_mm: float | None = None, height_mm: float | None = None,
                heal_mm: float = 0.06, tol_mm: float = 0.008) -> str:
    font, raw = _instantiate(font_path, weight)
    upm = font["head"].unitsPerEm
    glyphs = font.getGlyphSet()
    placed, _ = _shape(raw, text, upm, font)

    if width_mm and height_mm:
        raise SystemExit("give --width-mm or --height-mm, not both")

    # Flatten in font units first; scale is not known until the run is measured,
    # so use a tolerance tight enough for any plausible size, then rescale.
    pen = _FlattenPen(glyphs, tol=upm / 20000.0)
    per_glyph = []
    for name, dx, dy in placed:
        pen.contours = []
        glyphs[name].draw(TransformPen(pen, (1, 0, 0, 1, dx, dy)))
        pen._flush()
        g = _rings_to_polygon(pen.contours)
        if g is not None and not g.is_empty:
            per_glyph.append(g)
    if not per_glyph:
        raise SystemExit(f"no drawable outlines for {text!r} in {font_path}")

    geom = unary_union(per_glyph)
    x0, y0, x1, y1 = geom.bounds
    w_u, h_u = x1 - x0, y1 - y0
    scale = (width_mm / w_u) if width_mm else ((height_mm / h_u) if height_mm else 1.0 / upm)

    # Y-flip and move to origin, baked into the coordinates: a transform=
    # attribute is one more thing an importer can mishandle, and this file
    # exists to be imported.
    from shapely import affinity
    geom = affinity.affine_transform(geom, [scale, 0, 0, -scale,
                                            -x0 * scale, y1 * scale])
    if heal_mm > 0:
        e = heal_mm / 2.0
        geom = geom.buffer(e, join_style=2).buffer(-e, join_style=2)
    geom = geom.simplify(tol_mm, preserve_topology=True)

    W, H = w_u * scale, h_u * scale
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{_fmt(W)}mm" height="{_fmt(H)}mm" '
            f'viewBox="0 0 {_fmt(W)} {_fmt(H)}">\n'
            f'  <title>{text}</title>\n'
            f'  <path fill="#000000" fill-rule="nonzero" d="{_path_d(geom)}"/>\n'
            f'</svg>\n')


def main() -> None:
    ap = argparse.ArgumentParser(description="Text -> true vector SVG.")
    ap.add_argument("text")
    ap.add_argument("--font", required=True)
    ap.add_argument("--weight", type=float, default=None,
                    help="variable-font wght axis (900=Black). Ignored on static fonts.")
    ap.add_argument("--width-mm", type=float, default=None)
    ap.add_argument("--height-mm", type=float, default=None)
    ap.add_argument("--heal-mm", type=float, default=0.06,
                    help="close slots narrower than this (font artefacts that "
                         "no 0.4mm nozzle could print). 0 disables.")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    svg = text_to_svg(a.text, a.font, a.weight, a.width_mm, a.height_mm, a.heal_mm)
    Path(a.output).write_text(svg)
    print(f"wrote {a.output}  ({len(svg)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
