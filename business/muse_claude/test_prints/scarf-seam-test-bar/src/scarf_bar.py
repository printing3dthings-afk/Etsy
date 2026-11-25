"""Scarf Seam Test Bar: two smooth curved solids whose only job is to
show the seam - a plain cylinder (36 dia x 45) and a capsule bar
(18 dia, 36 straight + hemispherical top, revolved profile so the dome
is a true arc). No corners, no texture: wherever the seam sits, and
however it is laid down (aligned / random / scarf), is the whole read.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
import textgeom as tg

cyl = trimesh.creation.cylinder(radius=18, height=45, sections=128)
cyl.apply_translation([0, 0, 22.5])
tg.check(cyl, 'cylinder')

# capsule via revolve: straight wall then a 90-degree arc of r=9 to the axis
arc = [(9.0 * np.cos(a), 36.0 + 9.0 * np.sin(a)) for a in np.linspace(0, np.pi / 2, 13)]
pts = np.array([[0.0, 0.0], [9.0, 0.0]] + arc + [[0.0, 45.0]])
bar = trimesh.creation.revolve(pts, sections=96)  # profile y -> +Z natively
tg.check(bar, 'capsule')
print('capsule bbox', bar.bounds)

here = os.path.dirname(os.path.abspath(__file__))
cyl.export(os.path.join(here, 'Cylinder.stl'))
bar.export(os.path.join(here, 'Capsule.stl'))
sc = trimesh.Scene()
sc.add_geometry(cyl, node_name='Cylinder')
sc.add_geometry(bar, node_name='Capsule')
out = os.path.join(here, 'ScarfBar_src.3mf')
sc.export(out)
print('wrote', out)
