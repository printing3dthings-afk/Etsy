"""Overhang Ladder: six fin blocks on a base plate. Each fin is a solid
block (25 deep x 48 tall) with a triangular notch cut from its front-bottom
corner; the notch's sloped face is the test underside, sitting at
30/40/50/60/70/80 degrees from vertical. Angle labelled on the fin top.
(First version used free-hanging triangle fins resting on a knife edge --
Bambu Studio refuses to slice those degenerate layers, error -100; the
notched-block design keeps every fin flat-footed on the base.)"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
from shapely.geometry import Polygon
import textgeom as tg

ANGLES = [30, 40, 50, 60, 70, 80]
TOP_Z, BASE_T, RUN, WW, PITCH = 52.0, 4.0, 25.0, 24.0, 27.5
part = tg.box(170, 46, BASE_T)
for i, a in enumerate(ANGLES):
    x0 = -80.75 + i * PITCH
    fin = tg.box(WW, RUN, TOP_Z - BASE_T, cx=x0 + WW / 2.0, cy=0, zbot=BASE_T)
    H = RUN / math.tan(math.radians(a))
    # notch prism: triangle (y,z) = (-RUN/2,BASE_T), (RUN/2,BASE_T), (RUN/2,BASE_T+H)
    tri = Polygon([(-RUN / 2, BASE_T), (RUN / 2, BASE_T), (RUN / 2, BASE_T + H)])
    notch = trimesh.creation.extrude_polygon(tri, height=WW + 2)
    M = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=float)
    notch.apply_transform(M)
    notch.apply_translation([x0 - 1, 0, 0])
    fin = tg.difference(fin, [notch])
    part = tg.union([part, fin])
    part = tg.engrave(part, str(a), 7.0, x0 + WW / 2.0, 0, TOP_Z)
tg.check(part, 'OverhangLadder')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'OverhangLadder.stl')
part.export(out)
print('wrote', out)
