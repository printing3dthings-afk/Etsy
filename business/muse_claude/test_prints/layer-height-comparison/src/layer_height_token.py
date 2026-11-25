#!/usr/bin/env python3
"""Layer Height Comparison token: one part with a curved dome, a sloped
frustum and fine engraved text, so layer height differences show on every
kind of surface. Sliced at 5 layer heights with everything else constant.
Built as a single revolved profile (base disc + frustum + dome)."""
import os, sys
import numpy as np, trimesh
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_common'))
from textgeom import engrave, check

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'LayerHeightToken.stl')

prof = [(0.0, 0.0), (32.0, 0.0), (32.0, 3.0), (22.0, 3.0), (14.0, 11.0)]
for a in np.linspace(4.0, 90.0, 24):                    # dome: r14 sphere, centre z=10.7
    prof.append((max(14.0 * np.cos(np.radians(a)), 0.0), 10.7 + 14.0 * np.sin(np.radians(a))))
prof.append((0.0, 0.0))
part = trimesh.creation.revolve(np.array(prof), sections=96)
assert part.is_watertight and part.is_winding_consistent
# fine detail: 2.8mm engraved text on the flat top annulus of the base (front)
part = engrave(part, 'FINE 123', 2.8, 0, -27, 3.0, depth=0.6)
check(part, 'LayerHeightToken')
part.apply_translation([128, 128, 0])
part.export(OUT)
print('wrote', OUT)
