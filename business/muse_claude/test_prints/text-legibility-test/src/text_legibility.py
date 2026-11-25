"""Text Legibility Test: three plates on one build plate, same six text
rows on each - RAISED (0.8 mm relief), ENGRAVED (0.8 mm cut into the top),
FACE DOWN (cut into the bottom face, mirrored, so the build-plate texture
forms the letters and the plate reads correctly when flipped over).
Rows: nominal text heights 10 / 8 / 6 / 5 / 4 / 3 mm, each row leads with
its own size as the label. Line: "<size> QUICK BROWN FOX 0123".
Plates 176 x 78 x 3 mm; zone label engraved in the top margin of each.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
import textgeom as tg
from shapely.ops import unary_union
from shapely.geometry import Polygon

SIZES = [10, 8, 6, 5, 4, 3]
LINE = 'QUICK BROWN FOX 0123'
W, H, T = 216.0, 78.0, 3.0   # 216 wide: the 10 mm row measures 205 mm long
TOPMARGIN = 11.0


def row_layout():
    """[(size, baseline_y)] with y measured from plate bottom edge."""
    bands = []
    y = H - TOPMARGIN
    for s in SIZES:
        band = s + 4.6
        y -= band
        bands.append((s, y + 2.3))   # baseline 2.3 above band bottom
    return bands


def text_at(text, height, depth, cx, baseline_y):
    m, w = tg.text_mesh(text, height, depth)
    m.apply_translation([cx - w / 2.0, baseline_y, 0.0])
    return m


def zone_label(plate, label):
    return tg.engrave(plate, label, 5.0, -W / 2 + 34, H / 2 - 5.5, T, depth=0.7)


def build_plate(kind):
    plate = tg.box(W, H, T, cx=0.0, cy=0.0, zbot=0.0)
    # work in plate-centred coords: box() centres at cx,cy -> plate spans
    # x -88..88, y -39..39. Convert layout y (from bottom) to centred.
    def Y(y_from_bottom):
        return y_from_bottom - H / 2.0
    if kind == 'raised':
        parts = [plate]
        for s, base_y in row_layout():
            m = text_at('%d %s' % (s, LINE), float(s), 0.8, 0.0, Y(base_y))
            m.apply_translation([0, 0, T])
            parts.append(m)
        plate = tg.union(parts)
        plate = zone_label(plate, 'RAISED')
    elif kind == 'engraved':
        for s, base_y in row_layout():
            prism, w = tg.text_mesh('%d %s' % (s, LINE), float(s), 1.3)
            prism.apply_translation([-w / 2.0, Y(base_y), T - 0.8])
            plate = tg.difference(plate, [prism])
        plate = zone_label(plate, 'ENGRAVED')
    elif kind == 'facedown':
        for s, base_y in row_layout():
            prism, w = tg.text_mesh('%d %s' % (s, LINE), float(s), 1.3)
            # mirror in X so the bottom face reads correctly from below
            prism.apply_transform(np.diag([-1.0, 1.0, 1.0, 1.0]))
            if prism.volume < 0:
                prism.invert()
            prism.apply_translation([-w / 2.0, Y(base_y), -0.45])
            plate = tg.difference(plate, [prism])
        plate = zone_label(plate, 'FACE DOWN')
    tg.check(plate, kind)
    return plate


here = os.path.dirname(os.path.abspath(__file__))
sc = trimesh.Scene()
for name, kind in [('PlateRaised', 'raised'), ('PlateEngraved', 'engraved'),
                   ('PlateFaceDown', 'facedown')]:
    m = build_plate(kind)
    m.export(os.path.join(here, '%s.stl' % name))
    sc.add_geometry(m, node_name=name)
out = os.path.join(here, 'TextLegibility_src.3mf')
sc.export(out)
print('wrote', out)
