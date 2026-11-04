"""Teacup Bear: a chubby bear peeking over the rim of a teacup (2026-11-04).

Scott's pick, shape 1 of five: "a round bear sitting inside a classic teacup
on a saucer, paws and chin on the rim. One solid piece, with the cup as the
base."

Built like the Kawaii Cow (tools/sdf_figure.py, Technique 84), with one
lesson from her: the cow's four colours ran her whole height and cost about
600 filament changes. Here each colour keeps to a band. The saucer and cup are
cream with a pink band at the rim and one pink heart; the bear above is tan;
the dark brown (eyes, nose, the tea) and her pink cheeks and inner ears sit in
the band of her face.

The pose is the support plan. Her body rises out of the tea that fills the
cup to 2 mm under the rim, so her head sits on her body, not over air. Her
paws rest on the rim. The cup widens 0.63 mm per mm at most (32 deg from
upright). The handle and her round ears stand in the x-z plane and are made
printable in that plane (sf.upright_leaf), the handle's hole a teardrop
pointing up.

    python3 teacup_bear.py            build parts/*.stl (about 4 min)
    python3 teacup_bear.py --step 0.4 a quick draft
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import sdf_figure as sf  # noqa: E402

ANGLE = 33.0          # overhang grown under hanging parts, from upright (Technique 84)
SHELL = 1.2           # colour skin depth: three beads

# ---------- the saucer and cup (mm; front is -y, up is +z) ----------
SAUCER_R, SAUCER_H, WELL_R, WELL_D = 29.0, 4.5, 19.0, 1.0
CUP_Z0, CUP_H, CUP_R0, CUP_R = 3.5, 24.5, 11.0, 22.0       # foot radius, rim radius
RIM = CUP_Z0 + CUP_H                                       # 28
WALL, TEA = 2.4, 2.0                                       # rim lip; tea surface below the rim
RIM_BAND = 2.4                                             # pink band round the rim
SAUCER_BAND_R = 25.5                                       # pink ring on the saucer's rim
CUP_HEART = (10.5, 9.0)                                    # pink heart on the cup front: tip height, width
# the handle, in the x-z plane: an outer oval and a teardrop hole pointing up
HANDLE = ((24.0, 17.5), (6.5, 8.5))
HANDLE_HOLE = ((24.5, 16.5), 3.4)
HANDLE_HALF = 1.6
HOLE_ROOF = 28.0

# ---------- the bear ----------
BODY = ((0, 1, 27), (15.5, 13.5, 12.5))
TILT, PIVOT = 6.0, (0, -1, 38)                              # head tilt, so she isn't twinned
HEAD = ((0, -1, 48), (15, 13, 13.5))
MUZZLE = ((0, -12.4, 44.8), (5.4, 3.3, 4.0))
NOSE = ((0, -15.5, 46.6), (2.1, 1.3, 1.5))
EYE = ((6.2, -12.4, 49.5), (1.9, 1.2, 2.4))                # x mirrored
SHINE = ((6.8, -13.4, 50.4), 0.75)
BLUSH = ((10.5, -10.0, 45.0), 2.3)
EAR = ((11.5, -1.0, 59.5), 5.2, 1.4)                        # centre (x mirrored), radius, half-thickness
INNER_EAR = 3.0
SHOULDER, PAW, ARM_R = (12.0, -4.0, 36.0), (10.5, -15.8, 30.6), (4.0, 3.4)

MARK_AT, MARK_H = (0.0, 0.0), 7.0                          # the OBC mark, centred under the saucer
COLOURS = {"cream": "#F4F1EA", "tan": "#C68E5E", "brown": "#4A2E22", "pink": "#F6A6C1"}
# Her face's pink and cream win over her tan; her tan (paws on the rim) wins
# over the cup's pink band. The rest is cream: the cup and saucer.
PRIORITY = ["brown", "pink_face", "cream_muzzle", "tan", "pink_cup"]


def tilt():
    return sf.rot("y", TILT)


def head_pt(c):
    piv = np.asarray(PIVOT, np.float32)
    return piv + tilt() @ (np.asarray(c, np.float32) - piv)


def mirrored(c):
    c = np.asarray(c, np.float32)
    return (c, c * np.array([-1, 1, 1], np.float32))


def cup_radius(z):
    t = np.clip((z - CUP_Z0) / CUP_H, 0, 1)
    return CUP_R0 + (CUP_R - CUP_R0) * t * (1.4 - 0.4 * t)


def cup_slope(z):
    t = np.clip((z - CUP_Z0) / CUP_H, 0, 1)
    return (CUP_R - CUP_R0) * (1.4 - 0.8 * t) / CUP_H


class TeacupBear:
    def __init__(self, step):
        self.g = sf.Grid((-33, -33, -1.5), (36, 33, 70), step)

    def ell(self, c, r, R=None):
        return sf.ellipsoid(self.g, np.asarray(c, np.float32), np.asarray(r, np.float32), R)

    def head_ell(self, c, r):
        return self.ell(head_pt(c), r, tilt())

    # ---------- the cup ----------
    def rr(self):
        return np.sqrt(self.g.X ** 2 + self.g.Y ** 2)

    def cup(self):
        g = self.g
        rr, z = self.rr(), g.Z
        side = (rr - cup_radius(z)) / np.sqrt(1 + cup_slope(z) ** 2)
        solid = sf.smax(np.maximum(side, CUP_Z0 - z), z - RIM, 1.0)
        hollow = np.maximum(rr - (cup_radius(z) - WALL), (RIM - TEA) - z)
        return sf.smax(solid, -hollow, 0.8)

    def saucer(self):
        g = self.g
        rr, z = self.rr(), g.Z
        # the top: the rim ring at SAUCER_H, the well WELL_D lower, a slope between
        top = SAUCER_H - WELL_D * np.clip((SAUCER_BAND_R - 2 - rr) / 4.0, 0, 1)
        return sf.smax(rr - SAUCER_R, z - top, 2.0)

    def handle(self):
        (cx, cz), (ax, az) = HANDLE

        def outer(X, Z):
            return ((X - cx) / ax) ** 2 + ((Z - cz) / az) ** 2 < 1

        def cup_slice(X, Z):
            # the cup and the saucer: the fill under the handle lands on the
            # saucer; held to the cup alone it stopped 0.5 mm above it, a
            # point in mid-air the slicer propped
            cup = (np.abs(X) < cup_radius(Z)) & (Z > CUP_Z0) & (Z < RIM)
            return cup | ((np.abs(X) < SAUCER_R - 2) & (Z < SAUCER_H - 0.3))

        # its hole is cut exactly, after meshing (hole_cut()): cut in the field,
        # marching cubes softened its point and edges and the slicer propped it
        return sf.upright_leaf(self.g, outer, 0.0, HANDLE_HALF, cup_slice, ANGLE)

    def hole_cut(self):
        """The handle's hole: a teardrop pointing up, its roof HOLE_ROOF from
        upright, steeper than ANGLE so the handle over it is no ceiling."""
        (hx, hz), hr = HANDLE_HOLE
        return sf.teardrop_prism(hx, hz, hr, HOLE_ROOF)

    # ---------- the bear ----------
    def bear(self):
        g = self.g
        b = sf.smin(self.ell(*BODY), self.head_ell(*HEAD), 6)
        for sh, pw in zip(mirrored(SHOULDER), mirrored(PAW)):
            b = sf.smin(b, sf.stick(g, sh, pw, *ARM_R), 3)
        b = sf.smin(b, self.head_ell(*MUZZLE), 2.5)
        for c in mirrored(EAR[0]):
            b = sf.smin(b, self.ear(c), 1.5)
        for c in mirrored(EYE[0]):
            b = sf.smin(b, self.head_ell(c, EYE[1]), 0.5)
        b = sf.smin(b, self.head_ell(*NOSE), 0.6)
        return b

    def ear(self, c):
        cw = head_pt(c)
        r = EAR[1]

        def disc(X, Z):
            return (X - cw[0]) ** 2 + (Z - cw[2]) ** 2 < r * r

        head_c = head_pt(HEAD[0])
        hr = HEAD[1]

        def head_slice(X, Z):
            # the head's section in the ear's plane (its tilt is in this plane)
            Rt = tilt()
            dx, dy, dz = X - head_c[0], cw[1] - head_c[1], Z - head_c[2]
            lx = Rt[0, 0] * dx + Rt[2, 0] * dz
            lz = Rt[0, 2] * dx + Rt[2, 2] * dz
            return (lx / hr[0]) ** 2 + (dy / hr[1]) ** 2 + (lz / hr[2]) ** 2 < 1

        return sf.upright_leaf(self.g, disc, cw[1], EAR[2], head_slice, ANGLE)

    def build(self):
        t0 = time.time()
        d = sf.smin(self.saucer(), self.cup(), 1.5)
        d = sf.smin(d, self.handle(), 1.0)
        d = sf.smin(d, self.bear(), 1.5)
        d = sf.cut_base(self.g, d)
        print(f"  field {d.shape} in {time.time() - t0:.1f}s")
        t0 = time.time()
        d, added = sf.self_support(self.g, d, ANGLE)
        d = sf.cut_base(self.g, d)
        self.d = sf.base_prism(self.g, d, 0.8)
        print(f"  self-support grew {added:.0f} mm3 in {time.time() - t0:.1f}s")
        return self.d

    # ---------- colour regions (inside negative) ----------
    def regions(self):
        g, d = self.g, self.d
        skin = -(d + SHELL)
        rr, z = self.rr(), g.Z
        reg = {}

        brown = [self.head_ell(*NOSE) - 0.15]
        for c, s in zip(mirrored(EYE[0]), mirrored(SHINE[0])):
            brown.append(np.maximum(self.head_ell(c, EYE[1]) - 0.15, -self.head_ell(s, (SHINE[1],) * 3)))
        # the tea: the surface inside the rim, and a hair up her body where she
        # comes out of it
        inner = cup_radius(RIM) - WALL + 0.3
        tea_top = RIM - TEA
        brown.append(np.maximum(rr - inner, np.maximum(z - (tea_top + 0.3), (tea_top - 1.2) - z)))
        reg["brown"] = np.maximum(np.minimum.reduce(brown), skin)

        # the saucer's ring is held under SAUCER_H + 0.5: unbounded above, it
        # took in the whole handle
        cup_pink = [np.maximum(self.cup() - 0.3, (RIM - RIM_BAND) - z),
                    np.maximum(np.maximum(SAUCER_BAND_R - rr, (SAUCER_H - 1.2) - z), z - (SAUCER_H + 0.5))]
        tip_z, w = CUP_HEART
        heart, _ = sf.heart2d(g.X, g.Z - tip_z, w)
        cup_pink.append(np.maximum(heart, g.Y))
        reg["pink_cup"] = np.maximum(np.minimum.reduce(cup_pink), skin)
        pink = []
        for c in mirrored(BLUSH[0]):
            pink.append(self.head_ell(c, (BLUSH[1],) * 3))
        for c in mirrored(EAR[0]):
            cw = head_pt(c)
            # the inner ear: a disc on the ear's front face
            pink.append(np.maximum(np.sqrt((g.X - cw[0]) ** 2 + (g.Z - cw[2]) ** 2) - INNER_EAR,
                                   g.Y - (cw[1] - EAR[2] + 0.5)))
        reg["pink_face"] = np.maximum(np.minimum.reduce(pink), skin)

        cream = [self.head_ell(*MUZZLE) - 0.3] + [self.head_ell(s, (SHINE[1],) * 3) for s in mirrored(SHINE[0])]
        reg["cream_muzzle"] = np.maximum(np.minimum.reduce(cream), skin)
        # her: her own shapes, everything inside the rim above the tea, and
        # everything above the rim -- the support grown under her muzzle and
        # arms is hers too. "Above the tea and not cup" also took in support
        # round the handle and outside the cup: 219 tan slivers.
        inside_rim = np.maximum(rr - (cup_radius(RIM) - WALL + 0.2), (RIM - TEA - 0.6) - z)
        reg["tan"] = np.minimum(np.minimum(self.bear() - 0.2, inside_rim), (RIM + 0.6) - z)
        return reg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=float, default=0.25)
    ap.add_argument("--out", default=str(HERE / "parts"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    bear = TeacupBear(a.step)
    d = bear.build()
    mark = sf.obc_mark_meshes(MARK_H, MARK_AT, out)
    stats = sf.export_parts(bear.g, d, bear.regions(), PRIORITY, "cream", out, "teacup_bear",
                            mark=mark, mark_colour="brown", cuts=[bear.hole_cut()])
    (out / "build.json").write_text(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
