"""Urban Kid v2: the face on the CC0 stylized head (2026-11-17).

The realistic head read as a neutral adult however it was sculpted
(sculpt_face.py, research/NOTES.md). 'Head - Stylized' from the same CC0 bundle
is young (round face, big eyes, short nose, small mouth), which a designer-toy
teen needs. This gives him his expression and the detail Scott's references
have:
  - heavy, sleepy upper lids over the eyes (half-lidded, unimpressed);
  - brows low and level, drawn down at the inner ends, his left one cocked;
  - a smirk: his left mouth corner pulled up and back into a dimple, the cheek
    lifted over it; his right corner flat;
  - a cut lip line, the upper lip's border, a fuller lower lip, the philtrum;
  - a stronger jaw and chin than the base child's, for a teen;
  - irises ringed and pupils drilled in the eyeballs.

Units are the base mesh's (front -y). The head prints about 55 mm tall, so 1 mm
printed is about 0.0068 here: grooves are kept at 0.0027 or more (0.4 mm).

    python3 sculpt_face_sty.py sty_dense.ply out.ply
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools"))
from mesh_sculpt import Sculpt  # noqa: E402

CX = 2.083
EYES = {+1: np.array([2.1271, -0.0913, 0.7287]), -1: np.array([2.0388, -0.0913, 0.7287])}
EYE_R = 0.0378
# measured on the base mesh (rendered against it: z 0.666 is the crease under the nose)
MOUTH_Z, MOUTH_HW = 0.640, 0.021     # the slit
LID_UP, LID_LO = 0.7415, 0.7125       # the eye opening, at the eye's centre line


def main(src, dst):
    m = trimesh.load(src, process=False)
    s = Sculpt(m)
    # the eyeballs are their own pieces of the mesh: pick them by connection. Picked
    # by distance from their centres, the lids' inner rims (which wrap in round the
    # eyeballs) were frozen too, and lowering the lids tore them into a tooth
    from scipy.sparse.csgraph import connected_components
    import scipy.sparse as sp_
    e = s.F[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
    n = len(s.V)
    _, lab = connected_components(sp_.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    big = np.bincount(lab).argmax()
    eye = lab != big
    s.active = ~eye
    F = s.front

    def X(side, dx):
        return CX + side * dx

    # ---- the teen: jaw squared a little, chin forward and down ----
    for side in (1, -1):
        s.move(F(X(side, 0.052), 0.615), 0.03, (side * 0.004, -0.002, -0.002))
    s.move(F(CX, 0.600), 0.022, (0, -0.004, -0.004))

    # ---- heavy upper lids: the lid's edge drawn down over the eye, most at the outer corner ----
    for side, c in EYES.items():
        ex = c[0]
        # grabbed AT the lid's edge, so the edge moves most and the skin above it
        # stretches. Grabbed on the skin above, the skin moved further than the
        # edge and folded over it in a drip (the three brushes overlap, so these
        # deltas sum to about twice their size at the edge)
        for dx, dz, dy in ((-0.010, -0.0050, -0.0010), (0.0, -0.0075, -0.0014), (0.010, -0.0085, -0.0014)):
            p = F(ex + side * dx, LID_UP - 0.0005)
            s.move(p, 0.016, (0, dy, dz))
        # the lid's fold above: a crease following the lid, and the lid made full
        fold = [F(ex + side * dx, LID_UP + 0.0085 - 0.6 * dx * dx / 0.016) for dx in np.linspace(-0.016, 0.016, 7)]
        s.crease(fold, 0.0042, 0.0016, pinch=0.3)
        s.stroke([F(ex + side * dx, LID_UP + 0.0035) for dx in np.linspace(-0.012, 0.014, 6)], 0.004, 0.0012)
        # the lower lid: a soft rim (a furrow under it too aged him)
        s.stroke([F(ex + side * dx, LID_LO - 0.0025) for dx in np.linspace(-0.012, 0.012, 6)], 0.003, 0.0008)

    # ---- brows: low and level, inner ends drawn down; his left (+x) cocked up at its outer end ----
    for side in (1, -1):
        s.move(F(X(side, 0.020), 0.762), 0.016, (-side * 0.0012, -0.0016, -0.0050))
        s.stroke([F(X(side, 0.012), 0.760), F(X(side, 0.032), 0.764), F(X(side, 0.056), 0.761)], 0.0100, 0.0045)
    s.move(F(X(1, 0.050), 0.764), 0.016, (0, -0.0005, 0.0045))
    s.stroke([F(CX, 0.752), F(CX + 0.0015, 0.764)], 0.0045, -0.0015)          # the furrow between them

    # ---- the smirk ----
    L, R = np.array([CX + MOUTH_HW, 0, MOUTH_Z]), np.array([CX - MOUTH_HW, 0, MOUTH_Z])
    s.move(F(L[0], MOUTH_Z), 0.024, (0.0022, 0.0016, 0.0050))                  # his left corner up, back
    s.move(F(X(1, 0.046), 0.652), 0.022, (0.0010, -0.0020, 0.0028))           # the cheek lifted over it
    s.move(F(R[0], MOUTH_Z), 0.012, (-0.0008, 0.0006, -0.0006))               # his right corner flat
    # the lip line: cut, following the smirk up at his left
    line = [F(CX - MOUTH_HW - 0.002, MOUTH_Z - 0.0005), F(CX - 0.010, MOUTH_Z + 0.0002), F(CX, MOUTH_Z + 0.0004),
            F(CX + 0.011, MOUTH_Z + 0.0016), F(CX + MOUTH_HW + 0.002, MOUTH_Z + 0.0048)]
    s.crease(line, 0.0055, 0.0040, pinch=0.35)      # 0.0040 wide read as a scratch
    # the upper lip's soft border, and its shadow side above the slit
    s.stroke([F(CX - 0.017, MOUTH_Z + 0.0035), F(CX - 0.006, MOUTH_Z + 0.0062), F(CX, MOUTH_Z + 0.0055),
              F(CX + 0.006, MOUTH_Z + 0.0068), F(CX + 0.018, MOUTH_Z + 0.0075)], 0.0035, 0.0010)
    # the dimple at the smirk's end, and a short fold rising from it
    s.dots([F(CX + MOUTH_HW + 0.005, MOUTH_Z + 0.0068)], 0.0060, 0.0026)
    s.stroke([F(CX + MOUTH_HW + 0.007, MOUTH_Z + 0.004), F(CX + 0.031, MOUTH_Z + 0.013), F(CX + 0.030, 0.664)],
             0.0055, -0.0018)
    # the philtrum's two ridges; a fuller lower lip
    for side in (1, -1):
        s.stroke([F(X(side, 0.0040), MOUTH_Z + 0.0050), F(X(side, 0.0034), 0.6630)], 0.0030, 0.0007)
    s.draw(F(CX + 0.001, MOUTH_Z - 0.0085), 0.0140, 0.0032)
    s.draw(F(CX, MOUTH_Z + 0.0060), 0.0120, 0.0016)                             # the upper lip, fuller
    s.stroke([F(CX - 0.012, 0.6205), F(CX, 0.6185), F(CX + 0.012, 0.6205)], 0.0060, -0.0014)   # under the lower lip
    # ---- eyes: iris ring and drilled pupil, looking ahead and a touch to his left ----
    s.active = eye
    for side, c in EYES.items():
        look = np.array([0.18, -1.0, -0.04])
        look /= np.linalg.norm(look)
        front = c + EYE_R * look
        e1 = np.cross(look, [0, 0, 1.0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(e1, look)
        ring = [front + 0.0145 * (np.cos(a) * e1 + np.sin(a) * e2) - look * 0.0028
                for a in np.linspace(0, 2 * np.pi, 49)]
        s.crease(ring, 0.0045, 0.0030, pinch=0.2)
        s.draw(front, 0.0130, -0.0030)
        s.dots([front], 0.0062, 0.0080)
    s.active = None
    out = s.mesh()
    out.export(dst)
    print("sculpted", dst, len(out.vertices))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
