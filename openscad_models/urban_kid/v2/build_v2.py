"""Urban Kid v2: the figure, built on v1's pipeline with the simulated pants (2026-11-25).

Scott: "Urban kid will have both print options" (a split colour kit and one piece on tree
supports), then "Start what you can without messing things up." What's settled and what isn't:
  - the pants: Blender's cloth solver (cloth_garments.py pants) gives real folds; the one v2 piece
    that worked (research/NOTES.md, "What works");
  - the hoodie: every v2 hoodie try read worse than v1's (NOTES.md, "What didn't work"), so v1's
    hoodie stays;
  - the head: waits on Scott's upright head test (head_test_2/), so v1's head stays for now.
So this subclasses kid.Kid and replaces only pants(): the cloth legs, filled solid, with v1's
seat, cargo and back pockets, creases and the web between the legs added back, then v1's own
self-support passes, joints, print poses and checks. v1's files are not touched: output goes to
v2/build/ (or --out).

    blender -b --python cloth_garments.py -- SIM pants 60      (the cloth; mannequin.py SIM first)
    python3 build_v2.py SIM [--step 0.25] [--only pants ...] [--out DIR]
"""
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import sdf_figure as sf  # noqa: E402
import kid  # noqa: E402
import mannequin  # noqa: E402
from assemble import CLOTH_T, shell_field  # noqa: E402
from kid import (ANGLE, SHOE_X, Z_ANKLE, Z_WAIST, foot, groove, slab_box, support_up, trim_up,  # noqa: E402
                 under_chamfer, v3)


class KidV2(kid.Kid):
    SIM = None

    def pants(self):
        g = self.G["pants"]
        cloth = trimesh.load(self.SIM / "cloth_pants.stl")
        # the solver's finest wrinkles are a ring or two wide: spikes at this size, not folds
        trimesh.smoothing.filter_taubin(cloth, lamb=0.5, nu=-0.53, iterations=6)
        shell = shell_field(g, cloth, CLOTH_T)
        body = mannequin.body(self.step, g=g)[1]
        # the seat: hips and thigh tops with 2 mm of ease, tapering into the cloth legs at the
        # crotch (the legs' waist rings are hidden inside it), as assemble.py
        seat = mannequin.body(self.step, ("torso", "legs"), g=g)[1] - 2.0
        seat = seat + 0.8 * np.maximum(29.5 - g.Z, 0.0)
        seat = np.maximum(seat, g.Z - (Z_WAIST + 1.5))
        low = sf.smin(shell, seat, 1.5)
        occ = (low < 0) | (body < 0)
        occ[:, :, 0] = True
        occ = ndimage.binary_fill_holes(occ)
        occ[:, :, 0] = False
        d = np.where(occ, np.minimum(low, -0.01), np.maximum(low, 0.01))
        # v1's details, on the cloth: cargo pocket and flap on each outer thigh, back pockets
        for s in (1, -1):
            pc = v3(s * 15.4, 1.2, 27.0)
            outer = -s * (g.X - s * 9.0)
            cl = d
            pocket = np.maximum(slab_box(g, pc - v3(9.0, 4.0, 4.6), pc + v3(9.0, 4.0, 4.6), 1.0), outer)
            d = np.minimum(d, under_chamfer(g, np.maximum(cl - 1.0, pocket), cl, pc[2] - 4.6))
            flap = np.maximum(slab_box(g, pc + v3(-9.0, -4.0, 2.0), pc + v3(9.0, 4.0, 5.0), 0.8), outer)
            d = np.minimum(d, under_chamfer(g, np.maximum(cl - 1.5, flap), cl, pc[2] + 2.0))
            snap = sf.ellipsoid(g, pc + v3(0, 0, 3.4), v3(9.0, 0.95, 0.95))
            d = np.minimum(d, under_chamfer(g, np.maximum(cl - 2.1, np.maximum(snap, outer)), cl - 1.5, pc[2] + 2.6))
            bp = np.maximum(slab_box(g, v3(s * 6.5 - 3.3, 0.0, 31.5), v3(s * 6.5 + 3.3, 20.0, 37.6), 0.0), 4.0 - g.Y)
            d = np.minimum(d, under_chamfer(g, np.maximum(d - 0.8, bp), d, 31.5))
        # v1's web between the legs, leaning out at ANGLE: it keeps the inner cuffs printable
        web = slab_box(g, (-2.4, -1.0, Z_ANKLE - 1.0), (2.4, 4.0, 33.0), 0.6)
        lean = np.tan(np.radians(ANGLE)) * np.maximum(g.Z - 21.0, 0.0)
        web = np.minimum(web, np.maximum(np.maximum(np.abs(g.X) - 2.4, Z_ANKLE - g.Z),
                                         np.maximum((-1.0 - lean) - g.Y, g.Y - (4.0 + lean))))
        web = np.maximum(web, g.Z - 33.0)
        d = sf.smin(d, web, 0.6)
        # the cuffs must cover the sneakers' joints: no thinner than v1's at the ankle
        for s in (1, -1):
            cuff = sf.stick(g, v3(s * SHOE_X, 0.5, Z_ANKLE - 1.0), v3(s * SHOE_X, 0.5, Z_ANKLE + 3.0), 7.0, 6.8)
            d = np.minimum(d, cuff)
        d = np.maximum(d, g.Z - Z_WAIST)
        d = np.maximum(d, Z_ANKLE - g.Z)
        d, added = support_up(g, d)
        d = np.maximum(d, Z_ANKLE - g.Z)
        d = foot(g, d, Z_ANKLE)
        d, gone = trim_up(g, d, z0=Z_ANKLE)
        print(f"  pants (v2, cloth): self-support grew {added:.0f} mm3, trim took {gone:.1f}")
        return d


def main():
    sim = Path(sys.argv[1])
    KidV2.SIM = sim
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    if "--out" not in sys.argv:
        sys.argv += ["--out", str(HERE / "build")]
    kid.Kid = KidV2
    kid.main()


if __name__ == "__main__":
    main()
