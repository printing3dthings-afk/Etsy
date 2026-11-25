"""Shared geometry helpers for the Batch 1 test coupons.
Text: DejaVu Sans Bold glyph outlines via fontTools -> shapely polygons ->
trimesh extrusions. Booleans via manifold engine (exact, watertight)."""
import numpy as np, trimesh
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
_font = TTFont(FONT_PATH)
_gs = _font.getGlyphSet()
_hmtx = _font['hmtx']
_cmap = _font.getBestCmap()
_upem = _font['head'].unitsPerEm

class _RecPen(BasePen):
    def __init__(self, gs):
        super().__init__(gs)
        self.contours = []   # list of list[(x,y)]
        self._cur = None
    def _moveTo(self, p):
        self._cur = [p]; self.contours.append(self._cur)
    def _lineTo(self, p):
        self._cur.append(p)
    def _curveToOne(self, p1, p2, p3):
        p0 = self._cur[-1]
        for i in range(1, 13):
            t = i / 12.0
            mt = 1 - t
            x = mt**3*p0[0] + 3*mt*mt*t*p1[0] + 3*mt*t*t*p2[0] + t**3*p3[0]
            y = mt**3*p0[1] + 3*mt*mt*t*p1[1] + 3*mt*t*t*p2[1] + t**3*p3[1]
            self._cur.append((x, y))
    def _qCurveToOne(self, p1, p2):
        p0 = self._cur[-1]
        for i in range(1, 9):
            t = i / 8.0
            mt = 1 - t
            x = mt*mt*p0[0] + 2*mt*t*p1[0] + t*t*p2[0]
            y = mt*mt*p0[1] + 2*mt*t*p1[1] + t*t*p2[1]
            self._cur.append((x, y))
    def _closePath(self):
        pass
    def _endPath(self):
        pass

def _glyph_polys(ch):
    g = _gs[_cmap[ord(ch)]]
    pen = _RecPen(_gs)
    g.draw(pen)
    polys = []
    for c in pen.contours:
        if len(c) >= 3:
            p = Polygon(c)
            if not p.is_valid:
                p = p.buffer(0)
            if not p.is_empty and p.area > 0:
                polys.append(p)
    if not polys:
        return []
    # nest: largest contour is the shell, contained ones are holes
    polys.sort(key=lambda p: -p.area)
    outer = polys[0]
    holes = [p.exterior.coords for p in polys[1:] if outer.contains(p)]
    return [Polygon(outer.exterior.coords, holes)]

def text_mesh(text, height_mm, depth_mm):
    """Extruded text mesh: origin at left end of baseline, digits ~height_mm tall.
    Returns (mesh, width_mm). Baseline at y=0, extrusion z 0..depth_mm."""
    # measure digit height from '0'
    probe = _glyph_polys('0')[0]
    digit_h = probe.bounds[3] - probe.bounds[1]
    scale = height_mm / digit_h
    polys, xoff, total_w = [], 0.0, 0.0
    for ch in text:
        if ch == ' ':
            adv = _hmtx['space'][0] * scale
            xoff += adv; total_w = xoff
            continue
        gp = _glyph_polys(ch)
        adv = _hmtx[_cmap[ord(ch)]][0] * scale
        for p in gp:
            from shapely.affinity import translate, scale as sscale
            polys.append(translate(sscale(p, xfact=scale, yfact=scale, origin=(0, 0)), xoff=xoff))
        xoff += adv; total_w = xoff
    merged = unary_union(polys)
    if isinstance(merged, Polygon):
        merged = [merged]
    else:
        merged = list(merged.geoms)
    # simplify glyph outlines (0.02 mm, far below the 0.4 nozzle's
    # resolution): raw font outlines carry 3-5x the points the print
    # can express, and the excess density makes downstream raycasts
    # (plate thumbnails) crawl - Batch 4 text plates lesson.
    simplified = []
    for p in merged:
        s = p.simplify(0.05, preserve_topology=True)
        if s.is_empty or not s.is_valid:
            s = p
        if isinstance(s, Polygon):
            simplified.append(s)
        else:
            simplified.extend(list(s.geoms))
    meshes = [trimesh.creation.extrude_polygon(p, height=depth_mm) for p in simplified]
    m = trimesh.util.concatenate(meshes)
    return m, total_w

def engrave(base, text, height_mm, cx, cy, top_z, depth=0.8):
    """Cut text into the horizontal top face at top_z, centred at (cx, cy)."""
    prism, w = text_mesh(text, height_mm, depth + 0.4)
    # centre horizontally; vertically centre on digit band (~0.72*height above baseline approx)
    prism.apply_translation([cx - w / 2.0, cy - height_mm * 0.36, top_z - depth])
    out = trimesh.boolean.difference([base, prism], engine='manifold')
    return out

def box(sx, sy, sz, cx=0.0, cy=0.0, zbot=0.0):
    m = trimesh.creation.box(extents=[sx, sy, sz])
    m.apply_translation([cx, cy, zbot + sz / 2.0])
    return m

def cyl(r, h, cx=0.0, cy=0.0, zbot=0.0, sections=72):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=sections)
    m.apply_translation([cx, cy, zbot + h / 2.0])
    return m

def union(meshes):
    return trimesh.boolean.union(meshes, engine='manifold')

def difference(base, tools):
    return trimesh.boolean.difference([base] + list(tools), engine='manifold')

def check(mesh, name):
    bb = mesh.bounds
    print('%s: watertight=%s winding=%s vol=%.1f mm3 bbox=%s' % (
        name, mesh.is_watertight, mesh.is_winding_consistent, mesh.volume,
        np.round(bb[1] - bb[0], 2)))
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, name
