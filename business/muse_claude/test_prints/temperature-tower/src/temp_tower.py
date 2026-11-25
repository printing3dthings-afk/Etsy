"""Temperature Tower: five stepped blocks (9 mm each, footprint shrinking
46 -> 30 mm, staircase offset +1.2 mm/step in X). Every step carries the
same three features so the five temperature profiles can be compared
feature-by-feature on one tower each:
- a through window along X (18 mm span in Y, 5 mm tall) -> bridge roof
- a 45-degree notch cut into the front-bottom edge -> overhang underside
- a vertical 6 mm hole through the whole tower
Top step adds three 1.2 mm fins (fine detail / tip read).
Sits on a 58 x 58 x 3 mm slab engraved "TEMP ____ C" - Scott writes the
profile's temperature on the slab with a marker after printing.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
import textgeom as tg
from shapely.geometry import Polygon

STEP_H = 9.0
SIZES = [46.0, 42.0, 38.0, 34.0, 30.0]
XOFF = 1.2

parts = [tg.box(58, 58, 3, cx=0.0, cy=0.0, zbot=0.0)]
z = 3.0
for i, s in enumerate(SIZES):
    cx = XOFF * i
    parts.append(tg.box(s, s, STEP_H, cx=cx, cy=0.0, zbot=z))
    z += STEP_H
# top fins
for fx in (-6.0, 0.0, 6.0):
    parts.append(tg.box(1.2, 20, 6, cx=4 * XOFF + fx, cy=0.0, zbot=z))
tower = tg.union(parts)

def tri_prism(x0, x1, tri_yz):
    """Triangular prism along X from three (y, z) points (convex hull)."""
    pts = [[x, y, z] for x in (x0, x1) for (y, z) in tri_yz]
    return trimesh.Trimesh(vertices=np.array(pts, dtype=float)).convex_hull


cuts = []
for i, s in enumerate(SIZES):
    zb = 3.0 + STEP_H * i
    cx = XOFF * i
    # through window along X: 18 (Y) x 5 (Z), roof = top 4 mm of the step
    cuts.append(tg.box(s + 4, 18, 5, cx=cx, cy=0.0, zbot=zb + 2.0))
    # 45-degree notch into the front (+Y) face: removing the triangle
    # leaves a cavity whose roof slopes at 45 degrees (the overhang read)
    fy = s / 2.0
    cuts.append(tri_prism(cx - (s / 2.0 - 5), cx + (s / 2.0 - 5),
                          [(fy + 1, zb + 0.8), (fy - 6, zb + 0.8), (fy + 1, zb + 7.8)]))
# vertical hole through tower at x=2.4 (covered by every step)
cuts.append(tg.cyl(3.0, 60, cx=2.4, cy=0.0, zbot=0.0))
tower = tg.difference(tower, cuts)
tower = tg.engrave(tower, 'TEMP ____ C', 6.0, 0.0, -22.0, 3.0, depth=0.7)
tg.check(tower, 'TempTower')
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, 'TempTower.stl')
tower.export(out)
print('wrote', out)
