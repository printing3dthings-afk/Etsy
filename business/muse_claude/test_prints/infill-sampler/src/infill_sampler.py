#!/usr/bin/env python3
"""Infill Sampler geometry: 7 identical solid blocks 40x40x12 on one plate.
The infill difference is per-object slicer settings (applied at build time);
each block gets top_shell_layers=0 so the sparse infill is exposed at the top.
Labels embossed on the front face of each block."""
import os, sys
import numpy as np, trimesh
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_common'))
from textgeom import text_mesh, box, union, check

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'InfillSampler.stl')
SRC3MF = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'InfillSampler_src.3mf')

# (name, label, cx, cy)
BLOCKS = [
    ('BLK_G5',   'GYROID 5%',     57.5,  70),
    ('BLK_G10',  'GYROID 10%',   104.5,  70),
    ('BLK_G15',  'GYROID 15%',   151.5,  70),
    ('BLK_G20',  'GYROID 20%',   198.5,  70),
    ('BLK_G40',  'GYROID 40%',    81.0, 140),
    ('BLK_GRID', 'GRID 15%',     128.0, 140),
    ('BLK_LTG',  'LIGHTNING 15%', 175.0, 140),
]

def emboss_front(base, text, height_mm, cx, cz_base, front_y, depth=0.8, embed=0.3):
    prism, w = text_mesh(text, height_mm, depth)
    if w > 36.0:  # shrink to fit the 40mm face
        s = 36.0 / w
        prism.apply_scale(s); w *= s; height_mm *= s
    prism.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    # after rotX(+90): x same, y in [-depth, 0], z in [0, ~height]
    prism.apply_translation([cx - w / 2.0, front_y + embed, cz_base])
    return union([base, prism])

scene = trimesh.Scene()
for name, label, cx, cy in BLOCKS:
    blk = box(40, 40, 12, cx=0, cy=0, zbot=0)
    blk = emboss_front(blk, label, 4.2, 0, 3.6, -20.0)
    check(blk, name)
    m = np.eye(4); m[0, 3], m[1, 3] = cx, cy
    scene.add_geometry(blk, node_name=name, geom_name=name, transform=m)

scene.export(SRC3MF)
merged = scene.dump(concatenate=True)
merged.export(OUT)
print('wrote', SRC3MF, 'and', OUT, 'merged watertight:', merged.is_watertight)
