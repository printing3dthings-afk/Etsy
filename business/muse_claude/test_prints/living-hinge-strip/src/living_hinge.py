"""Living Hinge Strip: one flat strip, 24 mm wide, 2.0 mm panels, three hinge
webs in series (0.2 / 0.4 / 0.6 mm thick). Web lengths sized by the hinge
strain formula eps = t*theta/(2L) so ALL THREE sit at ~2.0% strain on a 90
degree fold (L = t*theta/(2*eps), theta = pi/2, eps = 0.02 -> L = 39.27*t,
rounded to 8 / 16 / 24 mm). The variable under test is web thickness itself:
1, 2 and 3 layers at 0.20 mm layer height. Grooves are cut from the top with
45-degree-class ramps blending into the panels (no sharp step). End tabs
carry a 6 mm hole each. PLA living hinges are fold-once / small-angle parts;
this strip measures how many 90-degree cycles each web survives."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
from shapely.geometry import Polygon
import textgeom as tg

THICK = 2.0
WIDTH = 24.0
HINGES = [(0.2, 8.0), (0.4, 16.0), (0.6, 24.0)]   # (web thickness, web floor length)
TAB = 26.0
PANEL = 24.0

# layout along X
segs = []          # (kind, x0, x1, data)
x = 0.0
segs.append(('tab', x, x + TAB, None)); x += TAB
for i, (t, lw) in enumerate(HINGES):
    ramp = THICK - t
    segs.append(('hinge', x, x + ramp + lw + ramp, (t, lw, ramp))); x += ramp + lw + ramp
    if i < 2:
        segs.append(('panel', x, x + PANEL, None)); x += PANEL
    else:
        segs.append(('tab', x, x + TAB, None)); x += TAB
LTOT = x
print('strip length %.1f mm' % LTOT)
for t, lw in HINGES:
    eps = t * (np.pi / 2) / (2 * lw)
    print('web %.1f mm, floor %.0f mm -> strain at 90 deg = %.2f%%' % (t, lw, 100 * eps))

# top profile, walking +X at full thickness, dipping at each hinge
top = [(0.0, THICK)]
for kind, x0, x1, data in segs:
    if kind == 'hinge':
        t, lw, ramp = data
        top.append((x0 + ramp, t))
        top.append((x0 + ramp + lw, t))
        top.append((x1, THICK))
top.append((LTOT, THICK))
pts = [(0.0, 0.0), (LTOT, 0.0)] + top[::-1]
mesh = trimesh.creation.extrude_polygon(Polygon(pts), height=WIDTH)
# rotate: profile plane XY (x=length, y=height), extrusion +Z -> want
# x=length, y=width centred, z=height
mesh.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
mesh.apply_translation([0, -WIDTH / 2.0, THICK])
# tab holes
holes = [tg.cyl(3.0, THICK + 2, cx=TAB / 2.0, cy=0.0, zbot=-1),
         tg.cyl(3.0, THICK + 2, cx=LTOT - TAB / 2.0, cy=0.0, zbot=-1)]
mesh = tg.difference(mesh, holes)
# labels on the segment after each hinge
hx = [s for s in segs if s[0] == 'hinge']
follow = [segs[segs.index(s) + 1] for s in hx]
for (t, lw), seg in zip(HINGES, follow):
    cx = (seg[1] + seg[2]) / 2.0
    mesh = tg.engrave(mesh, 'WEB %.1f' % t, 4.0, cx, 0.0, THICK)
tg.check(mesh, 'LivingHingeStrip')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'LivingHingeStrip.stl')
mesh.export(out)
print('wrote', out)
