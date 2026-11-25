"""Stringing / Retraction Test: a forest of slim tapered pins on a base
plate. Four rows of three pins; within a row the pin centre spacing is
graded 14 / 24 / 34 / 44 mm, so each row is a longer set of travel moves
than the last. Strings (or their absence) between pins are the read.
Pins: truncated cones, base r 2.6, top r 1.1, 30 mm tall.
Base 132 x 96 x 2.5 mm, row gap engraved at the front of each row.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
import textgeom as tg

ROWS = [(14.0, -36.0), (24.0, -12.0), (34.0, 12.0), (44.0, 36.0)]  # (centre spacing, row y)


def pin(cx, cy):
    # revolve profile (r, z) around Z via trimesh revolve (around Y) + rotate
    pts = np.array([[0.0, 0.0], [2.6, 0.0], [2.6, 1.5], [1.1, 29.0], [1.1, 30.0], [0.0, 30.0]])
    # trimesh revolve: profile x -> radius (XY), profile y -> +Z (verified)
    m = trimesh.creation.revolve(pts, sections=40)
    m.apply_translation([cx, cy, 2.5])
    return m


parts = [tg.box(132, 96, 2.5, cx=0.0, cy=0.0, zbot=0.0)]
for spacing, ry in ROWS:
    for dx in (-spacing, 0.0, spacing):
        parts.append(pin(dx, ry))
base = tg.union(parts)
for spacing, ry in ROWS:
    base = tg.engrave(base, 'GAP %d' % spacing, 4.0, -52.0, ry - 8.5, 2.5, depth=0.7)
tg.check(base, 'StringingForest')
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, 'StringingForest.stl')
base.export(out)
print('wrote', out)
