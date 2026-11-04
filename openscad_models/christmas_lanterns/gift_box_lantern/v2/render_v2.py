#!/usr/bin/env python3
"""Studio renders of the gift box lantern v2 from its exported parts:
assembled (three views), pulled apart along its assembly order, and the nine
prints as they come off the plate. Design-review renders, not photos.

    python3 render_v2.py        (after ./ship.sh)
"""
import subprocess
import sys
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
PARTS = HERE / "parts"
IMG = HERE / "images"
R = HERE.parents[3] / "tools" / "blender_render.py"
GREEN, WHITE, RED = "0.18,0.42,0.27", "0.96,0.95,0.92", "0.78,0.18,0.23"


def moved(name, dx=0.0, dy=0.0, dz=0.0, tag=""):
    """A copy of an exported part, shifted, for a layout render."""
    out = PARTS / f"_r_{name}{tag}.stl"
    m = trimesh.load(PARTS / f"{name}.stl", force="mesh")
    m.apply_translation([dx, dy, dz])
    m.export(out)
    return out


def render(parts, out, extra):
    args = []
    for path, rgb in parts:
        args += ["--part", f"{path}:{rgb}"]
    subprocess.run([sys.executable, str(R), *args, "-o", str(IMG / out),
                    "--resolution", "1400", "--timeout", "1200", *extra], check=True)


def main():
    IMG.mkdir(exist_ok=True)
    panels = [(PARTS / f"panel_glass_{k}_use.stl", WHITE) for k in range(4)] + \
             [(PARTS / f"panel_art_{k}_use.stl", GREEN) for k in range(4)]
    assembled = [(PARTS / "frame.stl", GREEN), (PARTS / "top_use.stl", GREEN),
                 (PARTS / "lid_use.stl", GREEN), (PARTS / "ribbon_use.stl", RED),
                 (PARTS / "bow_use.stl", RED)] + panels
    render(assembled, "gift_box_v2", ["--views"])

    # pulled apart, in the order it goes together: glass, top, lid, ribbon, bow
    exploded = [(PARTS / "frame.stl", GREEN),
                (moved("top_use", dz=30, tag="_x"), GREEN),
                (moved("lid_use", dz=55, tag="_x"), GREEN),
                (moved("ribbon_use", dz=75, tag="_x"), RED),
                (moved("bow_use", dz=95, tag="_x"), RED)]
    for k in range(4):
        exploded += [(moved(f"panel_glass_{k}_use", dz=12, tag="_x"), WHITE),
                     (moved(f"panel_art_{k}_use", dz=12, tag="_x"), GREEN)]
    render(exploded, "gift_box_v2_exploded.png", ["--azimuth", "-35", "--elevation", "18"])

    # the nine prints, as they lie on the plate
    g = 88
    kit = [(moved("frame", -g, g, tag="_k"), GREEN), (moved("top", 0, g, tag="_k"), GREEN),
           (moved("lid", g, g, tag="_k"), GREEN), (moved("ribbon", -g, 0, tag="_k"), RED),
           (moved("bow", 0, 0, tag="_k"), RED)]
    spots = [(g, 0), (-g, -g), (0, -g), (g, -g)]
    for k, (x, y) in enumerate(spots):
        kit += [(moved(f"panel_glass_{k}", x, y - 27, tag="_k"), WHITE),
                (moved(f"panel_art_{k}", x, y - 27, tag="_k"), GREEN)]
    render(kit, "gift_box_v2_prints.png", ["--azimuth", "-20", "--elevation", "55"])
    for p in PARTS.glob("_r_*.stl"):
        p.unlink()


if __name__ == "__main__":
    main()
