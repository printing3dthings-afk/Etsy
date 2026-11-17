"""Urban Kid v2: the face on the CC0 stylized head (2026-11-17).

The realistic head read as a neutral adult however it was sculpted
(sculpt_face.py, research/NOTES.md). 'Head - Stylized' from the same CC0 bundle
is young (round face, big eyes, short nose, small mouth), which a designer-toy
teen needs. This gives him his expression and the detail Scott's references
have. Scott, on the first pass's sleepy smirk: "Maybe a devilish smile or smirk.
A fun up to no good look." So:
  - a sly, lopsided closed-lip smile (then "Grin bigger like a sly smile"): his
    left corner pulled far up and back into a deep dimple and smile line, his
    right only a little;
  - cheeks lifted, pushing the lower lids up: the sly squint of a grin that
    means it;
  - upper lids a little lowered (scheming, not sleepy);
  - brows in a V: inner ends low and close, outer ends flicked up, his left
    cocked higher;
  - eyes glancing to his left, as if checking nobody's looking;
  - a cut lip line, the upper lip's border, fuller lips, the philtrum;
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

    # ---- the sly smile (Scott: "Grin bigger like a sly smile"): lopsided. His left
    # corner pulled far up and back into a deep dimple, his right only a little ----
    s.move(F(CX + MOUTH_HW, MOUTH_Z), 0.026, (0.0060, 0.0040, 0.0150))
    s.move(F(CX + MOUTH_HW + 0.008, MOUTH_Z + 0.012), 0.022, (0.0024, 0.0020, 0.0035))
    s.move(F(CX - MOUTH_HW, MOUTH_Z), 0.020, (-0.0030, 0.0020, 0.0040))
    # the cheek bunched hard over the high corner, the other barely lifted
    s.move(F(X(1, 0.042), 0.660), 0.026, (0.0015, -0.0045, 0.0065))
    s.draw(F(X(1, 0.044), 0.684), 0.016, 0.0026)
    s.move(F(X(-1, 0.042), 0.656), 0.022, (-0.0010, -0.0020, 0.0020))
    # the lip line: nearly level on his right, sweeping up to his left
    line = [F(CX - MOUTH_HW - 0.004, MOUTH_Z + 0.0035), F(CX - 0.010, MOUTH_Z + 0.0006), F(CX, MOUTH_Z + 0.0010),
            F(CX + 0.012, MOUTH_Z + 0.0040), F(CX + 0.021, MOUTH_Z + 0.0095), F(CX + 0.027, MOUTH_Z + 0.0130)]
    # (run on to z + 0.0165 the line hooked straight up at its end, like a scar)
    s.crease(line, 0.0055, 0.0042, pinch=0.35)      # 0.0040 wide read as a scratch
    # the upper lip's soft border, following it
    s.stroke([F(CX - 0.018, MOUTH_Z + 0.0055), F(CX - 0.006, MOUTH_Z + 0.0060), F(CX, MOUTH_Z + 0.0062),
              F(CX + 0.010, MOUTH_Z + 0.0090), F(CX + 0.020, MOUTH_Z + 0.0160)], 0.0035, 0.0010)
    # the dimple at the high corner deep, a hint at the other; smile lines, his left's deep
    s.dots([F(CX + 0.032, MOUTH_Z + 0.0155)], 0.0065, 0.0034)
    s.dots([F(CX - MOUTH_HW - 0.006, MOUTH_Z + 0.0040)], 0.0050, 0.0016)
    s.stroke([F(X(1, 0.019), 0.6745), F(X(1, 0.029), 0.6665), F(X(1, 0.037), 0.6580), F(X(1, 0.038), 0.6500)],
             0.0070, -0.0030)
    s.stroke([F(X(-1, 0.019), 0.6745), F(X(-1, 0.026), 0.663), F(X(-1, 0.029), 0.650)], 0.0060, -0.0012)

    # ---- eyes narrowed by the grin: upper lids a little down, lower lids pushed up ----
    for side, c in EYES.items():
        ex = c[0]
        # grabbed AT the lid's edge, so the edge moves most and the skin above it
        # stretches. Grabbed on the skin above, the skin moved further than the
        # edge and folded over it in a drip (the three brushes overlap, so these
        # deltas sum to about twice their size at the edge)
        for dx, dz, dy in ((-0.010, -0.0030, -0.0008), (0.0, -0.0045, -0.0010), (0.010, -0.0050, -0.0010)):
            s.move(F(ex + side * dx, LID_UP - 0.0005), 0.016, (0, dy, dz))
        # the lower lid pushed up by the cheek, most at its outer half (the squint)
        squint = 1.4 if side == 1 else 1.0          # more on the smile's high side
        for dx, dz in ((-0.008, 0.0022), (0.002, 0.0034), (0.011, 0.0040)):
            s.move(F(ex + side * dx, LID_LO + 0.0004), 0.014, (0, -0.0010, dz * squint))
        # the lid's fold above: a crease following the lid, and the lid made full
        fold = [F(ex + side * dx, LID_UP + 0.0085 - 0.6 * dx * dx / 0.016) for dx in np.linspace(-0.016, 0.016, 7)]
        s.crease(fold, 0.0042, 0.0016, pinch=0.3)
        s.stroke([F(ex + side * dx, LID_UP + 0.0035) for dx in np.linspace(-0.012, 0.014, 6)], 0.004, 0.0012)
        # the lower lid's rim, and a little laugh line at the outer corner
        s.stroke([F(ex + side * dx, LID_LO - 0.0020) for dx in np.linspace(-0.012, 0.012, 6)], 0.003, 0.0010)
        s.stroke([F(ex + side * 0.020, 0.7240), F(ex + side * 0.027, 0.7190)], 0.0035, -0.0010)

    # ---- brows in a V: inner ends low and close, outer ends flicked up, his left cocked ----
    for side, outer in ((1, 0.0070), (-1, 0.0045)):
        s.move(F(X(side, 0.013), 0.759), 0.013, (0, -0.0016, -0.0050))   # drawn in toward the middle too, they bunched into a knob
        s.move(F(X(side, 0.052), 0.763), 0.016, (side * 0.0008, -0.0005, outer))
        s.stroke([F(X(side, 0.010), 0.755), F(X(side, 0.030), 0.763), F(X(side, 0.054), 0.769)], 0.0100, 0.0045)
    s.stroke([F(CX, 0.748), F(CX + 0.0008, 0.762)], 0.0065, -0.0022)            # one soft crease between them

    # the philtrum's two ridges; a fuller lower lip
    for side in (1, -1):
        s.stroke([F(X(side, 0.0040), MOUTH_Z + 0.0050), F(X(side, 0.0034), 0.6630)], 0.0030, 0.0007)
    s.draw(F(CX + 0.001, MOUTH_Z - 0.0085), 0.0140, 0.0014)       # the lower lip: stretched by the grin, not pouting
    s.stroke([F(CX - 0.012, 0.6205), F(CX, 0.6185), F(CX + 0.012, 0.6205)], 0.0060, -0.0014)   # under the lower lip
    # ---- eyes: new eyeballs, not the base mesh's. Its eyes are layered (a clear
    # cornea dome over a sunken iris) for rendering; carved for a print they came
    # out a crater beside a blister. A plain ball each, glancing to his left, the
    # iris ringed and the pupil dished deep, so it prints as a shadow ----
    s.active = None
    head = s.mesh()
    keep = ~eye
    remap = -np.ones(len(head.vertices), int)
    remap[keep] = np.arange(keep.sum())
    fk = keep[head.faces].all(1)
    head = trimesh.Trimesh(head.vertices[keep], remap[head.faces[fk]], process=False)
    th = np.radians(17.0)
    look = np.array([np.sin(th), -np.cos(th), 0.0])
    balls = []
    for side, c in EYES.items():
        b = trimesh.creation.icosphere(subdivisions=6, radius=EYE_R)
        P = np.asarray(b.vertices)
        u = P / np.linalg.norm(P, axis=1)[:, None]
        ang = np.degrees(np.arccos(np.clip(u @ look, -1, 1)))
        cut = np.exp(-((ang - 21.0) / 2.4) ** 2) * 0.0026 + np.clip(1.0 - (ang / 8.5) ** 2, 0, 1) ** 1.5 * 0.0085
        cut -= np.clip(1.0 - (ang / 19.0) ** 2, 0, 1) * 0.0012 * (ang > 8.5)    # the iris a touch domed
        b.vertices = c + P - cut[:, None] * u
        balls.append(b)
    out = trimesh.util.concatenate([head] + balls)
    out.export(dst)
    print("sculpted", dst, len(out.vertices))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
