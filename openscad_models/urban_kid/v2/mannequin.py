"""Urban Kid v2: the body under the clothes (2026-11-17).

v2's clothes are simulated as cloth (cloth_garments.py), so they need a body to
fall onto: this is v1's pose (kid.py: hands in the pocket, weight even, the
same joints) with the garments taken off. Limbs are thinner than v1's sleeves
and legs by the cloth's ease, so the fabric has room to fold.

v1 assembly frame: mm, front -y, up +z. Writes:
  mannequin.stl   torso, arms, hands, legs, hips and neck, one body
  col_torso.stl   the torso and hands: what the hoodie's body falls onto
  col_arms.stl    the arms and hands: the sleeves
  col_legs.stl    the legs: the trouser legs
  shoes.stl       v1's two sneakers, as assembled, cut at the ankle (the cuffs
                  stack on them; their joint pegs are left off)

    python3 mannequin.py OUT_DIR
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
import sdf_figure as sf  # noqa: E402

v3 = lambda *a: np.array(a, np.float32)  # noqa: E731

# the joints v1's sleeves and legs were drawn round (kid.py, Kid.hoodie / Kid.pants)
ARM = {"sh": (16.0, 1.0, 60.5), "el": (17.2, 2.6, 50.6), "ha": (9.4, -5.6, 47.8)}
LEG = {"hip": (7.4, 1.0, 34.0), "knee": (8.4, -0.4, 25.0), "ank": (9.0, 0.5, 13.0)}


def side(p, s):
    return v3(s * p[0], p[1], p[2])


def body(step, parts=("torso", "arms", "legs"), g=None):
    """The field for the named parts: each garment collides with only its own.
    On its own grid, or on g (assemble.py samples it on the figure's)."""
    g = g or sf.Grid(np.array([-24.0, -14.0, 10.0]), np.array([24.0, 14.0, 72.0]), step)
    far = np.full(g.X.shape, 50.0, np.float32)
    d = far.copy()
    t = sf.ellipsoid(g, v3(0, 0.5, 57.0), v3(13.6, 9.2, 11.8))                           # chest
    t = sf.smin(t, sf.ellipsoid(g, v3(0, 0.3, 46.0), v3(12.4, 8.8, 8.5)), 6.0)          # belly
    t = sf.smin(t, sf.ellipsoid(g, v3(0, 1.2, 36.5), v3(12.6, 8.8, 6.4)), 5.0)          # hips
    t = sf.smin(t, sf.stick(g, v3(0, 1.0, 62.0), v3(0, 1.0, 71.0), 5.4, 5.0), 3.0)      # neck
    for s in (1, -1):
        t = sf.smin(t, sf.ellipsoid(g, v3(s * 12.4, 0.8, 62.0), v3(5.6, 6.6, 4.4)), 4.0)   # shoulders
    if "torso" in parts:
        d = t
    for s in (1, -1):
        sh, el, ha = (side(ARM[k], s) for k in ("sh", "el", "ha"))
        arm = sf.smin(sf.stick(g, sh, el, 3.6, 3.2), sf.stick(g, el, ha, 3.2, 2.6), 1.2)
        arm = sf.smin(arm, sf.ellipsoid(g, ha + v3(-s * 0.8, -0.4, -0.3), v3(2.6, 2.0, 2.8)), 1.0)   # the hand, a fist
        if "arms" in parts:
            d = sf.smin(d, arm, 2.0)
        elif "hands" in parts:
            d = np.minimum(d, sf.ellipsoid(g, ha + v3(-s * 0.8, -0.4, -0.3), v3(2.6, 2.0, 2.8)))
        hip, knee, ank = (side(LEG[k], s) for k in ("hip", "knee", "ank"))
        leg = sf.smin(sf.stick(g, hip, knee, 5.4, 4.3), sf.stick(g, knee, ank, 4.3, 3.0), 1.5)
        if "legs" in parts:
            d = sf.smin(d, leg, 3.0)
    return g, d


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    g, d = body(0.4)
    m = sf.mesh(g, d)
    m.export(out / "mannequin.stl")
    for name, parts in (("torso", ("torso", "hands")), ("arms", ("arms",)), ("legs", ("legs",))):
        sf.mesh(*body(0.5, parts)).export(out / f"col_{name}.stl")
    parts = HERE.parent / "parts" / "assembled"
    shoes = trimesh.util.concatenate([trimesh.load(parts / f"{n}.stl") for n in ("shoe_r", "shoe_l")])
    shoes = shoes.slice_plane([0, 0, 12.6], [0, 0, -1], cap=True)
    shoes.export(out / "shoes.stl")
    print("mannequin", m.bounds.round(1).tolist(), len(m.vertices), "verts; shoes", shoes.bounds.round(1).tolist())


if __name__ == "__main__":
    main(sys.argv[1])
