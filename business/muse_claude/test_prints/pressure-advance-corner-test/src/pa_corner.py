"""Pressure Advance Corner Test: two hollow square towers with dead
sharp 90-degree corners (44 x 44 and 26 x 26, walls 2.4 mm, 40 tall) on
a shared base plate. Corner bulge / rounding at speed is the PA read:
too little advance fattens the corner, too much starves it. The base is
engraved with the test ladder - PA on a Bambu is set per print (device
calibration / filament dialog), so one file serves all three values.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
import textgeom as tg


def tube(size, wall, h, cx, cy):
    outer = tg.box(size, size, h, cx=cx, cy=cy, zbot=2.5)
    inner = tg.box(size - 2 * wall, size - 2 * wall, h + 2, cx=cx, cy=cy, zbot=2.5 - 1)
    return tg.difference(outer, [inner])


parts = [tg.box(118, 62, 2.5, cx=0.0, cy=0.0, zbot=0.0),
         tube(44, 2.4, 40, -28.0, 0.0),
         tube(26, 2.4, 40, 32.0, 0.0)]
m = tg.union(parts)
m = tg.engrave(m, 'PA CORNER TEST', 5.0, 0.0, -26.5, 2.5, depth=0.7)
tg.check(m, 'PACorner')
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, 'PACorner.stl')
m.export(out)
print('wrote', out)
