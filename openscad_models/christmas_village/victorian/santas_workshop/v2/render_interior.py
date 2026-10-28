#!/usr/bin/env python3
"""Two white renders of v2's inside, from logs/union.stl (ship.sh makes it):

  images/v2_interior_underside.png  turned over, looking into the open base:
                                    the one chamber, the three tealight rings
  images/v2_interior_cutaway.png    cut through the middle bay and seen from
                                    the left: the right-hand inside wall's
                                    opening face on, a ring either side of it

Design-review renders from the real mesh, not photos.
"""
import subprocess, sys, tempfile
from pathlib import Path
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
R = HERE.parents[4] / "tools/blender_render.py"
WHITE = "0.957,0.945,0.918"
m = trimesh.load(HERE / "logs/union.stl", force="mesh")

with tempfile.TemporaryDirectory() as tmp:
    up = m.copy()
    up.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    up.export(Path(tmp) / "under.stl")
    cut = m.slice_plane([-8, 0, 0], [1, 0, 0], cap=True)
    cut.export(Path(tmp) / "cut.stl")
    for src, out, az, el in (("under.stl", "v2_interior_underside.png", 25, 58),
                             ("cut.stl", "v2_interior_cutaway.png", -90, 14)):
        subprocess.run([sys.executable, str(R), str(Path(tmp) / src), "--color", WHITE,
                        "--azimuth", str(az), "--elevation", str(el), "--resolution", "1600",
                        "--timeout", "2400", "-o", str(HERE / "images" / out)], check=True)
