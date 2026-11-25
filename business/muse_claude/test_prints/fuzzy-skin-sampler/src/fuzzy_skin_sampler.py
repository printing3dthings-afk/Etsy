#!/usr/bin/env python3
"""Fuzzy Skin Sampler geometry: 4 identical open-top cups (outer Ø46, cavity
Ø40, floor 3, height 42) + engraved label plates in front of each cup.
The fuzzy difference is per-object slicer settings applied at build time."""
import os, sys
import numpy as np, trimesh
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_common'))
from textgeom import box, cyl, engrave, difference, check

D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, 'FuzzySkinSampler.stl')
SRC3MF = os.path.join(D, 'FuzzySkinSampler_src.3mf')

CUPS = [  # (name, label, cx)
    ('CUP_OFF', 'OFF',  41),
    ('CUP_006', '0.06', 99),
    ('CUP_012', '0.12', 157),
    ('CUP_018', '0.18', 215),
]
CY = 140

def cup():
    outer = cyl(23, 42, zbot=0, sections=96)
    cavity = cyl(20, 42 - 3, zbot=3, sections=96)
    return difference(outer, [cavity])

scene = trimesh.Scene()
for name, label, cx in CUPS:
    c = cup(); check(c, name)
    m = np.eye(4); m[0, 3], m[1, 3] = cx, CY
    scene.add_geometry(c, node_name=name, geom_name=name, transform=m)
    plate = box(36, 12, 2, cx=0, cy=0, zbot=0)
    plate = engrave(plate, label, 5.0, 0, 0, 2.0, depth=0.7)
    check(plate, name + '_label')
    m2 = np.eye(4); m2[0, 3], m2[1, 3] = cx, CY - 35
    scene.add_geometry(plate, node_name='LBL_' + name.split('_')[1], geom_name='LBL_' + name.split('_')[1], transform=m2)

scene.export(SRC3MF)
merged = scene.dump(concatenate=True)
merged.export(OUT)
print('wrote', SRC3MF, 'and', OUT, 'merged watertight:', merged.is_watertight)
