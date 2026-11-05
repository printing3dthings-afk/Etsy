"""Teacup Bear v2: the Santa-style rework, in three prints (2026-11-05).

Scott, after the Kawaii Cow v2: "Try the bear". v1 (../teacup_bear.py) is one
piece: her head blends into her body, and the support grown under her chin
and muzzle shows as a soft cone where a neck should be. v2 keeps her pose and
splits her the way the Santa is split:

  cup    the saucer, cup and handle: cream, the pink rim, ring and heart, the
         brown tea. A keyed peg stands on the tea.
  body   tan, rising out of the tea, paws on the rim, a pink collar and a
         cream patch on her chest. Prints upright on its
         flat bottom, which sits on the tea.
  head   tan, cream muzzle, brown eyes and nose, pink cheeks and inner ears.
         Prints upright on its own flat neck, which sits in the collar
         (DETAIL_STANDARD rule 8: a band where two forms meet), on a keyed peg.

The method is the cow v2's (../../kawaii_cow/v2/cow_v2.py): each part is
grown printable from its own plate, the parts it touches are carved out of it
with a gap, and the pegs and sockets are exact solids added and cut after
meshing.

    python3 teacup_bear_v2.py             build parts/*.stl (several minutes)
    python3 teacup_bear_v2.py --step 0.5  a quick draft
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
sys.path.insert(0, str(HERE.parent))
import sdf_figure as sf  # noqa: E402
import teacup_bear as v1  # noqa: E402  (v1's shapes; nothing of v1 is rebuilt)

ANGLE, SHELL = v1.ANGLE, v1.SHELL
# The tea fills the cup to the brim (v1's was 2 mm below the rim). Printed on
# her own, her paws on the rim had nothing under them: the cones that would
# hold them up stood where the cup's wall goes. With the tea flush, the rim
# and the tea are one level, her body's plate, and her paws' soles and her
# bottom both stand on it
TEA_TOP = v1.RIM                 # 28
# Her head rides LIFT higher than v1's on a taller body: with the tea at the
# brim, v1's body showed only 9 mm above it, a low lump under the head
LIFT = 3.0
BODY = ((0, 1, 28.5), (15.5, 13.5, 13.5))
SHOULDER_PT = (12.0, -4.0, 38.5)
ARM_K = 1.8                      # the arms join her body with a small fillet, so they read as arms
NECK_Z = 40.0                    # the head's flat bottom and the body's top
CLR = 0.2                        # gap between nesting faces
PEG_CLR = 0.15                   # peg in socket, a glued fit
COLLAR_R = 1.6                   # the collar's tube radius
SHOULDER = 9.0                   # the radius her shoulders round over to the collar with
NECK_PEG = dict(c=(0.0, -1.0), r=3.0, h=6.0, flat=2.0)
TEA_PEG = dict(c=(0.0, 1.0), r=3.5, h=5.0, flat=2.3)
# a cream patch on her chest (a colour, on whatever surface her chest has there)
CHEST = ((0, -11.0, 34.5), (5.5, 4.0, 4.5))

COLOURS = v1.COLOURS
PARTS = ("cup", "body", "head")


def tilt():
    return v1.tilt()


def head_pt(c):
    return v1.head_pt(c) + np.array([0, 0, LIFT], np.float32)


def mirrored(c):
    return v1.mirrored(c)


def roofed(g, cut):
    """A cavity's cutter grown up into a gable no flatter than ANGLE
    (self_support upside down): its ceilings print."""
    out, _ = sf.self_support(g, np.ascontiguousarray(cut[:, :, ::-1]), ANGLE)
    return np.ascontiguousarray(out[:, :, ::-1])


def keyed_peg(p, z0, clr=0.0):
    """An exact peg standing up from z0: a cylinder with a flat on its +x
    side, so its part goes on one way only, and a 33 deg cone on top, so the
    socket's roof prints. It starts 1 mm down, in what it stands on."""
    import manifold3d as mf
    r, h, flat = p["r"] + clr, p["h"] + clr, p["flat"] + clr
    cone_h = r * np.tan(np.radians(90 - ANGLE))
    peg = mf.Manifold.cylinder(h + 1.0, r, r, 96).translate([0, 0, -1.0])
    peg = peg + mf.Manifold.cylinder(cone_h, r, 0.0, 96).translate([0, 0, h])
    peg = peg ^ mf.Manifold.cube([r + flat, 2 * r + 2, h + cone_h + 4]).translate([-r - 1, -r - 1, -2])
    return peg.translate([p["c"][0], p["c"][1], z0])


class Bear2:
    def __init__(self, step):
        self.step = step
        self.lo = np.array([-33, -33, -1.5])
        self.hi = np.array([36, 33, 70])
        self.A = sf.Grid(self.lo, self.hi, step)
        for z in (TEA_TOP, NECK_Z):
            assert abs(z / step - round(z / step)) < 1e-6, f"{z} must sit on the grid"

    def grid(self, oz):
        """A part's grid: the assembly's, from oz up, with oz at z = 0."""
        return sf.Grid(self.lo, self.hi - [0, 0, oz], self.step), int(round(oz / self.step))

    def on_A(self, d, m):
        out = np.full(self.A.X.shape, 10.0, np.float32)
        n = min(d.shape[2], out.shape[2] - m)
        out[:, :, m:m + n] = d[:, :, :n]
        return out

    def from_A(self, dA, m, shape):
        out = np.full(shape, 10.0, np.float32)
        n = min(shape[2], dA.shape[2] - m)
        out[:, :, :n] = dA[:, :, m:m + n]
        return out

    # primitives on grid g, whose z = assembly z - oz
    @staticmethod
    def ell(g, c, r, R=None, oz=0.0):
        return sf.ellipsoid(g, np.asarray(c, np.float32) - [0, 0, oz], np.asarray(r, np.float32), R)

    def head_ell(self, g, c, r, oz):
        return self.ell(g, head_pt(c), r, tilt(), oz)

    # ----- the cup, as v1 builds it, with the bear left out -----
    def cup_fields(self, g, oz=0.0):
        rr, z = np.sqrt(g.X ** 2 + g.Y ** 2), g.Z + oz
        side = (rr - v1.cup_radius(z)) / np.sqrt(1 + v1.cup_slope(z) ** 2)
        # the rim 0.15 under her paws' soles (her plate): level with them, the
        # two shared a plane and the fit check read it as 4.6 mm3 of overlap
        solid = sf.smax(np.maximum(side, v1.CUP_Z0 - z), z - (v1.RIM - 0.15), 1.0)
        hollow = np.maximum(rr - (v1.cup_radius(z) - v1.WALL), TEA_TOP - z)
        cup = sf.smax(solid, -hollow, 0.8)
        top = v1.SAUCER_H - v1.WELL_D * np.clip((v1.SAUCER_BAND_R - 2 - rr) / 4.0, 0, 1)
        saucer = sf.smax(rr - v1.SAUCER_R, z - top, 2.0)
        return cup, saucer

    def cup(self):
        g = self.A
        cup, saucer = self.cup_fields(g)
        d = sf.smin(saucer, cup, 1.5)
        old = v1.TeacupBear.__new__(v1.TeacupBear)
        old.g = g
        # the handle's in-plane fill runs across the cup up to v1's rim height:
        # with the top 0.15 lower it stood 0.1 proud of the tea, a strip under
        # her. The handle itself tops out at 26
        d = sf.smin(d, np.maximum(old.handle(), g.Z - (v1.RIM - 1.0)), 1.0)
        d = sf.cut_base(g, d)
        d, added = sf.self_support(g, d, ANGLE)
        d = sf.base_prism(g, sf.cut_base(g, d), 0.8)
        print(f"  cup: self-support grew {added:.0f} mm3")
        self.cup_d, self.cup_only = d, cup
        self.old = old
        return d

    def cup_regions(self):
        g, d = self.A, self.cup_d
        skin = -(d + SHELL)
        rr, z = np.sqrt(g.X ** 2 + g.Y ** 2), g.Z
        inner = v1.cup_radius(v1.RIM) - v1.WALL + 0.3
        tea = np.maximum(rr - inner, np.maximum(z - (TEA_TOP + 0.3), (TEA_TOP - 1.2) - z))
        pink = [np.maximum(self.cup_only - 0.3, (v1.RIM - v1.RIM_BAND) - z),
                np.maximum(np.maximum(v1.SAUCER_BAND_R - rr, (v1.SAUCER_H - 1.2) - z), z - (v1.SAUCER_H + 0.5))]
        tip_z, w = v1.CUP_HEART
        heart, _ = sf.heart2d(g.X, g.Z - tip_z, w)
        pink.append(np.maximum(heart, g.Y))
        return {"brown": np.maximum(tea, skin), "pink": np.maximum(np.minimum.reduce(pink), skin)}

    # ----- the head -----
    def head(self):
        g, m = self.grid(NECK_Z)
        oz = NECK_Z
        self.H, self.mH = g, m
        d = sf.smin(self.head_ell(g, *v1.HEAD, oz), self.head_ell(g, *v1.MUZZLE, oz), 2.5)
        for c in mirrored(v1.EAR[0]):
            d = sf.smin(d, self.ear(g, c, oz), 1.5)
        for c in mirrored(v1.EYE[0]):
            d = sf.smin(d, self.head_ell(g, c, v1.EYE[1], oz), 0.5)
        d = sf.smin(d, self.head_ell(g, *v1.NOSE, oz), 0.6)
        d = np.maximum(d, -g.Z)
        d, added = sf.self_support(g, d, ANGLE)
        d = sf.base_prism(g, np.maximum(d, -g.Z), 0.8)
        print(f"  head: self-support grew {added:.0f} mm3")
        self.head_d = d
        return d

    def ear(self, g, c, oz):
        """v1's ear: a disc standing upright, made printable in its own plane
        down onto the head."""
        cw = head_pt(c)
        r = v1.EAR[1]
        head_c = head_pt(v1.HEAD[0])
        hr = v1.HEAD[1]

        def disc(X, Z):
            return (X - cw[0]) ** 2 + (Z + oz - cw[2]) ** 2 < r * r

        def head_slice(X, Z):
            Rt = tilt()
            dx, dy, dz = X - head_c[0], cw[1] - head_c[1], Z + oz - head_c[2]
            lx = Rt[0, 0] * dx + Rt[2, 0] * dz
            lz = Rt[0, 2] * dx + Rt[2, 2] * dz
            return (lx / hr[0]) ** 2 + (dy / hr[1]) ** 2 + (lz / hr[2]) ** 2 < 1

        return sf.upright_leaf(g, disc, cw[1], v1.EAR[2], head_slice, ANGLE)

    def head_regions(self):
        g, d, oz = self.H, self.head_d, NECK_Z
        skin = -(d + SHELL)
        brown = [self.head_ell(g, *v1.NOSE, oz) - 0.15]
        for c, s in zip(mirrored(v1.EYE[0]), mirrored(v1.SHINE[0])):
            brown.append(np.maximum(self.head_ell(g, c, v1.EYE[1], oz) - 0.15,
                                    -self.head_ell(g, s, (v1.SHINE[1],) * 3, oz)))
        pink = [self.head_ell(g, c, (v1.BLUSH[1],) * 3, oz) for c in mirrored(v1.BLUSH[0])]
        for c in mirrored(v1.EAR[0]):
            cw = head_pt(c)
            pink.append(np.maximum(np.sqrt((g.X - cw[0]) ** 2 + (g.Z + oz - cw[2]) ** 2) - v1.INNER_EAR,
                                   g.Y - (cw[1] - v1.EAR[2] + 0.5)))
        cream = [self.head_ell(g, *v1.MUZZLE, oz) - 0.3] + [self.head_ell(g, s, (v1.SHINE[1],) * 3, oz)
                                                             for s in mirrored(v1.SHINE[0])]
        return {"brown": np.maximum(np.minimum.reduce(brown), skin),
                "pink": np.maximum(np.minimum.reduce(pink), skin),
                "cream": np.maximum(np.minimum.reduce(cream), skin)}

    # ----- the body -----
    def body(self):
        g, m = self.grid(TEA_TOP)
        oz = TEA_TOP
        self.B, self.mB = g, m
        head_B = self.from_A(self.on_A(self.head_d, self.mH), m, g.X.shape)
        d = self.ell(g, *BODY, oz=oz)
        for sh, pw in zip(mirrored(SHOULDER_PT), mirrored(v1.PAW)):
            d = sf.smin(d, sf.stick(g, sh - [0, 0, oz], pw - [0, 0, oz], *v1.ARM_R), ARM_K)
        # her chest patch, standing proud
        # the neck: the head's footprint stood down onto her shoulders, which
        # round over to it; a cut flat at NECK_Z left v1's body top as a shelf
        zn = NECK_Z - oz
        j0 = int(np.searchsorted(self.H.axes[2], 0.0))
        foot = self.head_d[:, :, j0] < 0
        d2 = sf.exact2d(None, g.axes[0], g.axes[1], refine=1, inside=foot)[:, :, None]
        dd = np.maximum(d2, 0)
        shoulder = (g.Z - zn + dd * dd / (2 * SHOULDER)) / np.sqrt(1 + (dd / SHOULDER) ** 2)
        d = sf.smax(d, shoulder, 2.5)
        # the neck narrows ANGLE from upright going down into her: a sloped
        # chest under her chin, with no underside to prop. Cut flat 5 mm down
        # its front hung over air (404 support moves); run straight down to
        # the tea it made her torso a block
        a = np.radians(ANGLE)
        neck = np.maximum((d2 - 2 * COLLAR_R + (zn - g.Z) * np.tan(a)) * np.cos(a), g.Z - zn)
        d = sf.smin(d, neck, 2.5)
        d = np.maximum(d, g.Z - zn)
        # the collar, round the head's footprint. A bow at its front was
        # tried and dropped (2026-11-05): it stood 5 mm out over her chest and
        # the cones under it ended in keels the slicer propped (654 moves)
        collar = np.sqrt((d2 - COLLAR_R) ** 2 + (g.Z - zn) ** 2) - COLLAR_R
        self.collar = collar
        d = np.minimum(d, collar)
        d = np.maximum(d, -g.Z)                                  # her flat bottom on the tea
        # nothing of the head inside her: the collar hugs it
        pocket = head_B - CLR
        d = np.maximum(d, -pocket)
        d, added = sf.self_support(g, d, ANGLE)
        d = np.maximum(np.maximum(d, -g.Z), -pocket)
        d = sf.base_prism(g, d, 0.8)
        print(f"  body: self-support grew {added:.0f} mm3")
        self.body_d = d
        return d

    def body_regions(self):
        g, d, oz = self.B, self.body_d, TEA_TOP
        skin = -(d + SHELL)
        return {"pink": np.maximum(self.collar - 0.05, skin),
                "cream": np.maximum(self.ell(g, *CHEST, oz=oz), skin)}


def main():
    import trimesh
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=float, default=0.25)
    ap.add_argument("--out", default=str(HERE / "parts"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    t0 = time.time()
    b = Bear2(a.step)
    b.cup()
    b.head()
    b.body()
    print(f"  fields in {time.time() - t0:.0f}s")
    stats = {}
    mark = sf.obc_mark_meshes(v1.MARK_H, v1.MARK_AT, out)
    stats["cup"] = sf.export_parts(b.A, b.cup_d, b.cup_regions(), ["brown", "pink"], "cream", out, "cup",
                                   mark=mark, mark_colour="brown", cuts=[b.old.hole_cut()])
    # the tea peg, exact, in cream, on the cup
    peg = keyed_peg(TEA_PEG, TEA_TOP)
    for stem in ("cup_cream", "cup"):
        m = sf.to_manifold(trimesh.load(out / f"{stem}.stl", force="mesh")) + peg
        sf.from_manifold(m).export(out / f"{stem}.stl")
    stats["body"] = sf.export_parts(b.B, b.body_d, b.body_regions(), ["pink", "cream"], "tan", out, "body",
                                    cuts=[keyed_peg(TEA_PEG, 0.0, PEG_CLR)])
    # the neck peg, exact, in tan, up from her neck
    peg = keyed_peg(NECK_PEG, NECK_Z - TEA_TOP)
    for stem in ("body_tan", "body"):
        m = sf.to_manifold(trimesh.load(out / f"{stem}.stl", force="mesh")) + peg
        sf.from_manifold(m).export(out / f"{stem}.stl")
    stats["head"] = sf.export_parts(b.H, b.head_d, b.head_regions(), ["brown", "pink", "cream"], "tan", out, "head",
                                    cuts=[keyed_peg(NECK_PEG, 0.0, PEG_CLR)])
    # booleans can leave a zero-volume sheet as its own body in a union
    for name in PARTS:
        mm = trimesh.load(out / f"{name}.stl", force="mesh")
        keep = [x for x in mm.split(only_watertight=False) if abs(x.volume) > 0.05]
        if len(keep) < len(mm.split(only_watertight=False)):
            trimesh.util.concatenate(keep).export(out / f"{name}.stl")
    (out / "build.json").write_text(json.dumps(stats, indent=1))
    print(f"  done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
