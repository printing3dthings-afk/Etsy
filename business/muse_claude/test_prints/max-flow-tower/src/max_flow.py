"""Max Flow Tower: four stacked slabs (76 mm long walls - long enough
for the toolhead to reach full speed and sit on the volumetric cap),
each 8 mm tall, back faces flush, depth stepping 36 -> 27 mm so each
slab's front-bottom edge is exposed. That edge is chamfered at 45
degrees: the sloped underside is where a cap set higher than the
filament can melt shows first (matte, rough, under-extruded). Read band
by band across the three cap profiles (12 / 18 / 24 mm3/s).
On a 92 x 52 x 3 mm base engraved "MAX FLOW".
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
import textgeom as tg


def tri_prism(x0, x1, tri_yz):
    """Triangular prism along X from three (y, z) points (convex hull)."""
    pts = [[x, y, z] for x in (x0, x1) for (y, z) in tri_yz]
    return trimesh.Trimesh(vertices=np.array(pts, dtype=float)).convex_hull


parts = [tg.box(92, 52, 3, cx=0.0, cy=0.0, zbot=0.0)]
z = 3.0
slabs = []
for i in range(4):
    d = 36.0 - 3.0 * i
    cy = -18.0 + d / 2.0          # back faces flush at y = -18
    parts.append(tg.box(76, d, 8, cx=0.0, cy=cy, zbot=z))
    slabs.append((d, z))
    z += 8.0
tower = tg.union(parts)

cuts = []
for i, (d, zb) in enumerate(slabs):
    fy = -18.0 + d                # this slab's front face
    # remove the front-bottom corner triangle -> 45 deg underside
    cuts.append(tri_prism(-30, 30, [(fy + 1, zb - 0.5), (fy - 6, zb - 0.5), (fy + 1, zb + 6)]))
tower = tg.difference(tower, cuts)
tower = tg.engrave(tower, 'MAX FLOW', 6.0, 0.0, -21.0, 3.0, depth=0.7)
tg.check(tower, 'MaxFlow')
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, 'MaxFlowTower.stl')
tower.export(out)
print('wrote', out)
