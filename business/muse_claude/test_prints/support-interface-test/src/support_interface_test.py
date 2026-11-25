#!/usr/bin/env python3
"""Support Interface Test geometry: two legs + a flat roof slab. The flat
underside of the roof (36mm clear span, 14mm above the plate) needs support;
that underside is the judged surface after support removal."""
import os, sys
import numpy as np, trimesh
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_common'))
from textgeom import box, union, check

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SupportInterfaceTest.stl')

leg_l = box(14, 30, 14, cx=-25, cy=0, zbot=0)
leg_r = box(14, 30, 14, cx=25, cy=0, zbot=0)
roof = box(64, 30, 4, cx=0, cy=0, zbot=14)
part = union([leg_l, leg_r, roof])
check(part, 'SupportInterfaceTest')
part.apply_translation([128, 128, 0])
part.export(OUT)
print('wrote', OUT)
