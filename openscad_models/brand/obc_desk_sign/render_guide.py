#!/usr/bin/env python3
"""Pictures for the OBC desk sign's guide, rendered from the real exported parts.
Design-review renders, not photos.

    python3 render_guide.py     (images/guide_parts.png, images/guide_insert.png)

The finished sign is images/obc_desk_sign_three_quarter.png, from the review renders.
"""
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
import blender_render as br  # noqa: E402

P = HERE / "parts"
IMG = HERE / "images"
BLACK, GOLD = (0.09, 0.09, 0.10), (0.83, 0.62, 0.18)


def moved(name, td, offset=(0, 0, 0), along_lean=0.0):
    """A copy of a part, shifted; along_lean lifts the standing plaque out along its own slope."""
    t = trimesh.load(P / f"{name}.stl")
    lean = math.radians(8)
    off = np.array(offset, float) + along_lean * np.array([0, math.sin(lean), math.cos(lean)])
    t.apply_translation(off)
    out = Path(td) / f"{name}_{len(list(Path(td).iterdir()))}.stl"
    t.export(out)
    return out


def main():
    with tempfile.TemporaryDirectory() as td:
        # the two prints, as they come off the plate: plaque face up, base beside it
        parts = [(moved("plaque", td, (0, 30, 0)), BLACK), (moved("letters", td, (0, 30, 0)), GOLD),
                 (moved("base", td, (0, -50, 0)), BLACK)]
        br.render_review(parts, IMG / "guide_parts.png", azimuth=0, elevation=55, resolution=1000, timeout=1500)
        # the plaque lifted 30 mm out of its slot, letters to the front
        parts = [(P / "base.stl", BLACK), (moved("standing_plaque", td, along_lean=30), BLACK),
                 (moved("standing_letters", td, along_lean=30), GOLD)]
        br.render_review(parts, IMG / "guide_insert.png", azimuth=-35, elevation=22, resolution=1000, timeout=1500)
    for f in IMG.glob("*.rendercache"):
        f.unlink()


if __name__ == "__main__":
    main()
