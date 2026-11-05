"""Kawaii Cow v2: the Santa-style rework, in five prints (2026-11-05).

Scott, after his Santa print from MakerWorld: "Look at how it's split and the
way they shaped it. It looks better than our cow and bear as far as the
details", then "Try the Santa style rework see how it turns out and if it
looks better". v1 (../cow.py) is one piece in four colours, every part
blended into the next with smooth-min, so she reads as one soft blob; her
ears point up because hanging ears had nothing under them; the heart is a
colour skin. v2 keeps her pose and splits her the way the Santa is split:

  body   white, black spots and hooves, a red collar. Prints upright.
  head   white, pink muzzle and cheeks, black spot and eyes. Prints upright
         on its own flat neck, so its underside needs nothing from the body.
  ears   two leaves printed flat, pink inner face up: they can hang out
         sideways like a real cow's, which no single-piece print allowed.
  heart  red, printed flat on its back: one colour, a crisp edge and a
         stitched seam round its face.

Each joint hides under something, as the Santa's neck hides in his beard: the
head sits in the collar (DETAIL_STANDARD rule 8, a band where two forms meet),
the ears' tabs in slots in the head. A
keyed peg locates the head. The heart sits in a pocket in her lap, between her
arms, against a wall behind it, and takes a drop of glue: a peg out of her
chest was tried and dropped (its underside is a cantilever over air: 382
support moves), and a peg out of the heart's back can't print, since that face
lies on the plate.

Shaped, not painted: a forelock of three curls, longer horns, deeper
nostrils, a tail tuft in locks, stitches on the heart. A smile and horn rings
were tried and dropped: their grooves' ceilings hung (see head()).

    python3 cow_v2.py             build parts/*.stl (several minutes)
    python3 cow_v2.py --step 0.5  a quick draft
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
import cow as v1  # noqa: E402  (v1's skeleton; nothing of v1 is rebuilt)

S = v1.S
ANGLE = v1.ANGLE
SHELL = v1.SHELL

# ---------- what changes from v1 (design mm; front is -y, up is +z) ----------
LIFT = 3.5            # the head rides this much higher than v1's, on a neck
HEAD = ((0, -3, v1.HEAD[0][2] + LIFT), (16.5, 13.0, 12.6))
MUZZLE = ((0, -14.5, v1.MUZZLE[0][2] + LIFT), (10.0, 6.5, 7.0))
PIVOT = (0, -6, v1.PIVOT[2] + LIFT)
# print mm: the head's flat bottom and the body's top (a multiple of 0.5).
# Just under the muzzle, and 0.2 over the heart's lobes, which the chin rests on
NECK_Z = 28.0
NECK_H = 13.0         # print mm: how far the neck stands down. At 6 its corners behind the
                      # heart hung over her pad, and the support cones under them ended in keels
                      # the slicer propped (2,017 moves); down to her lap they stand straight
SHOULDER = 11.0       # print mm: the radius her shoulders round over to the collar with
FRONT_GAP = 1.0       # print mm: see body()
LAP_TOP = 21.0        # print mm: in front of the heart's back, nothing of her above this (her arms end under it)
COLLAR_R = 1.9        # print mm: the collar's tube radius
COLLAR_END = 2.5      # print mm: its two ends stop this far behind her front, rounded
CLR = 0.2             # print mm: gap between nesting faces (head in collar, heart in lap)
PEG_CLR = 0.15        # print mm: peg in socket, a glued fit
# the neck peg: a cylinder with a flat, so the head goes on one way only
NECK_PEG = dict(r=3.0, h=6.0, flat=2.0)
NECK_CENTRE = (0, -2.0, 0)            # design mm: where it stands, under the head's middle
# forelock: three curls between the horns (centre, radii, tilt forward deg)
CURLS = [((0, -7.6, 52.0), (2.5, 3.4, 2.4), 40), ((-3.7, -6.4, 51.6), (2.2, 3.1, 2.2), 30),
         ((3.7, -6.4, 51.6), (2.2, 3.1, 2.2), 30)]
# horns: base, bend, tip (design mm, x mirrored), base and tip radius, rings
# They lean 28 deg out, 35 with the head's tilt on her right: past that the
# support cones under them stood proud. Rings round them were tried and
# dropped (2026-11-05): on a leaning horn a groove's ceiling hangs.
HORN = ((7.6, -2.5, 47.0), (10.6, -2.2, 52.6), (11.4, -2.6, 57.4), (2.7, 1.3))
NOSTRIL = ((3.6, -21.0, 30.6), (1.4, 1.6, 1.9))
# ears (print mm): length, widest, thickness, the pink inner's depth, the tab
EAR_L, EAR_W, EAR_T, EAR_CUP = 15.0, 9.0, 2.6, 0.6
TAB = dict(l=3.5, w=4.4, t=2.0)
EAR_ROOT = (15.2, -0.5, 40.2)          # design mm, x mirrored: on the head's side, below the horns
EAR_DROOP, EAR_BACK = 22.0, 15.0      # deg below level, deg swept back
# heart (print mm, as printed: outline in x-y, tip at y = 0, back on the plate)
HEART_W = v1.HEART_W * S
HEART_T, HEART_DOME, HEART_ROUND = 2 * v1.HEART_HALF * S, 1.4, 2.8
STITCH = dict(inset=3.0, n=26, w=0.6, d=0.6)
TAIL_LOCKS = [((15.6, 13.4, 2.4), (2.0, 1.6, 2.4), 20), ((16.6, 15.4, 2.2), (2.0, 1.5, 2.2), -15),
              ((14.3, 15.6, 2.2), (1.8, 1.4, 2.0), 50)]

COLOURS = v1.COLOURS
PARTS = ("body", "head", "ear_r", "ear_l", "heart")


def P(v):
    return np.asarray(v, np.float32) * S


def tilt():
    return sf.rot("y", v1.TILT)


def head_pt(c):
    piv = np.asarray(PIVOT, np.float32)
    return piv + tilt() @ (np.asarray(c, np.float32) - piv)


def mirrored(c, s):
    return np.asarray(c, np.float32) * np.array([s, 1, 1], np.float32)


def rounded_slab(d2, z, t, r):
    """A 2-D shape stood up from the plate to height t, its top edge rounded
    by r and its bottom square to the plate (nothing to prop under it)."""
    qx, qz = d2 + r, z - (t - r)
    top = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qz, 0) ** 2) + np.minimum(np.maximum(qx, qz), 0) - r
    return np.maximum(top, -z)


def ell2d(u, v, a, b):
    k0 = np.sqrt((u / a) ** 2 + (v / b) ** 2)
    k1 = np.sqrt((u / a ** 2) ** 2 + (v / b ** 2) ** 2)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def box2d(u, v, u0, u1, hw):
    du = np.maximum(u0 - u, u - u1)
    dv = np.abs(v) - hw
    return np.sqrt(np.maximum(du, 0) ** 2 + np.maximum(dv, 0) ** 2) + np.minimum(np.maximum(du, dv), 0)


# ---------- the ear, in its own print frame ----------
# x along the ear from its root (x = 0 meets the head), y across, z up from
# the plate; the pink inner face is its top


def ear_field(x, y, z):
    leaf = ell2d(x - EAR_L * 0.55, y, EAR_L * 0.55, EAR_W / 2)
    tab = box2d(x, y, -TAB["l"], EAR_L * 0.3, TAB["w"] / 2)
    d2 = sf.smin(leaf, tab, 2.0)
    # cupped: the inner face dips EAR_CUP in the middle; the tab is thinner,
    # flat on the plate, with a short ramp up to the ear
    cup = ell2d(x - EAR_L * 0.58, y, EAR_L * 0.38, EAR_W * 0.3)
    t = EAR_T - EAR_CUP * np.clip(-cup / 2.0, 0, 1) - (EAR_T - TAB["t"]) * np.clip(-x / 0.6, 0, 1)
    return rounded_slab(d2, z, t, 1.0)


def ear_inner(x, y, z):
    """The pink: the cupped middle of the ear's top, three layers deep."""
    cup = ell2d(x - EAR_L * 0.58, y, EAR_L * 0.4, EAR_W * 0.33)
    # within 0.6 of the top face (a flat cut at EAR_T - 0.6 missed the
    # cupped middle, which dips under it, and left a pink ring)
    return np.maximum(np.maximum(cup, -(ear_field(x, y, z) + 0.6)), EAR_T / 2 - z)


def ear_pose(side):
    """(R, origin): print frame -> assembly. Root at the head's side, along
    outward and drooping, inner face forward."""
    R = sf.rot("z", EAR_BACK) @ sf.rot("y", EAR_DROOP) @ sf.rot("x", 90)
    if side < 0:
        M = np.diag([-1.0, 1.0, 1.0])
        R = M @ R @ np.diag([1.0, -1.0, 1.0])
    root = P(head_pt(mirrored(EAR_ROOT, side)))
    origin = root - R @ np.array([0, 0, EAR_T / 2])
    return R, origin


def ear_on(g, side, off=np.zeros(3)):
    R, o = ear_pose(side)
    x, y, z = g.local(o - off, R)
    return ear_field(x, y, z)


# ---------- the heart, in its own print frame ----------
# x across, y up the heart from its tip, z up from its back (on the plate);
# assembled it stands on its tip, its back against her chest


def heart_pose():
    # x -> x, y -> z, z -> -y
    R = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], np.float64)
    tip = P(v1.HEART_TIP)
    back_y = tip[1] + v1.HEART_HALF * S
    return R, np.array([0.0, back_y, tip[2]])


def heart_2d(us, vs):
    """Exact 2-D distance of the heart's outline on axes us (across), vs (up)."""
    return sf.exact2d(lambda u, v: sf.heart2d(u, v, HEART_W, notch_k=5 * S)[0], us, vs)


def heart_field(d2, x, y, z, stitches=True):
    t = HEART_T + HEART_DOME * np.clip(-d2 / (7 * S), 0, 1)
    f = rounded_slab(d2, z, t, HEART_ROUND)
    if stitches:
        # dashes of a running stitch, STITCH inset from the edge
        hgt = sf.heart2d(np.zeros(1), np.zeros(1), HEART_W)[1]
        th = np.arctan2(y - 0.55 * hgt, x)
        rr = np.hypot(x, y - 0.55 * hgt)
        dash = (0.25 - np.sin(STITCH["n"] * th)) * rr / STITCH["n"]
        band = np.abs(-d2 - STITCH["inset"]) - STITCH["w"] / 2
        cut = np.maximum(np.maximum(band, dash), -(f + STITCH["d"]))
        cut = np.maximum(cut, HEART_T * 0.5 - z)
        f = np.maximum(f, -cut)
    return f


# ---------- the pegs and sockets, as exact solids ----------
# Cut from the fields, a 0.15 mm gap is under the 0.25 mm voxel and came out
# of marching cubes anywhere from 0.08 to 0.6 (2026-11-05). These are added
# and cut after meshing, with manifold3d.


def neck_peg_solid(clr=0.0):
    """The neck peg, in the head's print frame (z = 0 at NECK_Z): a cylinder
    with a flat on its +x side, so the head goes on one way only, and a
    33 deg cone on top, so the socket's roof prints. It starts 1 mm down, in
    her neck."""
    import manifold3d as mf
    p = NECK_PEG
    r, h, flat = p["r"] + clr, p["h"] + clr, p["flat"] + clr
    cx, cy = P(NECK_CENTRE)[:2]
    cone_h = r * np.tan(np.radians(90 - ANGLE))
    peg = mf.Manifold.cylinder(h + 1.0, r, r, 96).translate([0, 0, -1.0])
    peg = peg + mf.Manifold.cylinder(cone_h, r, 0.0, 96).translate([0, 0, h])
    peg = peg ^ mf.Manifold.cube([r + flat, 2 * r + 2, h + cone_h + 4]).translate([-r - 1, -r - 1, -2])
    return peg.translate([cx, cy, 0])


def ear_slot_solid(side, oz=NECK_Z, out_to=3.0):
    """The slot an ear's tab and stalk go into, in the head's print frame:
    their cross-section plus PEG_CLR, run from the tab's end out to `out_to`
    mm along the ear, with a gable roof leaning ANGLE from upright over it.
    Cut from the field, the roof's peak came out of marching cubes as a flat
    strip a voxel wide and the slicer propped it (2026-11-05)."""
    import manifold3d as mf
    from scipy.spatial import ConvexHull
    xs, ys = np.meshgrid(np.linspace(-TAB["l"], out_to, 60), np.linspace(-EAR_W, EAR_W, 801), indexing="ij")
    d2 = sf.smin(ell2d(xs - EAR_L * 0.55, ys, EAR_L * 0.55, EAR_W / 2), box2d(xs, ys, -TAB["l"], EAR_L * 0.3, TAB["w"] / 2), 2.0)
    hw = np.abs(ys[d2 < 0]).max() + PEG_CLR
    rect = np.array([[-hw, -PEG_CLR], [hw, -PEG_CLR], [hw, EAR_T + PEG_CLR], [-hw, EAR_T + PEG_CLR]])
    R, o = ear_pose(side)
    up = (R.T @ np.array([0, 0, 1.0]))[1:]
    up /= np.linalg.norm(up)
    across = np.array([-up[1], up[0]])
    c = rect.mean(axis=0)
    span = (rect @ across).max() - (rect @ across).min()
    apex = c + up * ((rect - c) @ up).max() + up * (span / 2) / np.tan(np.radians(ANGLE))
    pts = np.vstack([rect, apex])
    sec = pts[ConvexHull(pts).vertices]
    length = out_to + TAB["l"] + PEG_CLR
    slot = mf.Manifold.extrude(mf.CrossSection([sec.tolist()]), length).translate([0, 0, -TAB["l"] - PEG_CLR])
    # local (a, b, c) = (y, z, x) of the ear's print frame
    L = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], np.float64)
    return pose_solid(slot, R @ L, o - np.array([0, 0, oz]))


def pose_solid(solid, R, o):
    m = np.c_[np.asarray(R, np.float64), np.asarray(o, np.float64)]
    return solid.transform(m.tolist())


def roofed(g, cut):
    """A cavity's cutter, grown up into a gable no flatter than ANGLE from
    upright: self_support() run upside down, so every ceiling the cut leaves
    prints without support."""
    out, _ = sf.self_support(g, np.ascontiguousarray(cut[:, :, ::-1]), ANGLE)
    return np.ascontiguousarray(out[:, :, ::-1])


# ---------- the figure ----------


class Cow2:
    def __init__(self, step):
        self.step = step
        lo = np.array([-34, -34, -1.5]) * S
        hi = np.array([34, 25, 61]) * S
        self.A = sf.Grid(lo, hi, step)
        assert abs(NECK_Z / step - round(NECK_Z / step)) < 1e-6, "NECK_Z must sit on the grid"
        self.m = int(round(NECK_Z / step))
        # the head's grid: the assembly's, from NECK_Z up, with NECK_Z at z = 0
        self.H = sf.Grid(lo, np.array([hi[0], hi[1], hi[2] - NECK_Z]), step)

    # primitives on grid g, whose z = assembly z - oz
    def ell(self, g, c, r, R=None, oz=0.0):
        return sf.ellipsoid(g, P(c) - [0, 0, oz], P(r), R)

    def stick(self, g, a, b, ra, rb, oz=0.0):
        return sf.stick(g, P(a) - [0, 0, oz], P(b) - [0, 0, oz], ra * S, rb * S)

    def head_ell(self, g, c, r, R=None, oz=0.0):
        Rt = tilt() if R is None else tilt() @ R
        return self.ell(g, head_pt(c), r, Rt, oz)

    # ----- the head -----
    def head(self):
        g, oz = self.H, NECK_Z
        d = self.head_ell(g, *HEAD, oz=oz)
        d = sf.smin(d, self.head_ell(g, *MUZZLE, oz=oz), 3 * S)
        for s in (1, -1):
            # horns: a bent, tapering cone
            a, b, c = (head_pt(mirrored(p, s)) for p in HORN[:3])
            r0, r1 = HORN[3]
            rm = (r0 + r1) / 2 + 0.2
            horn = sf.smin(self.stick(g, a, b, r0, rm, oz), self.stick(g, b, c, rm, r1, oz), 1.0 * S)
            d = sf.smin(d, horn, 1.5 * S)
            d = sf.smin(d, self.head_ell(g, mirrored(v1.EYE[0], s) + [0, 0, LIFT], v1.EYE[1], oz=oz), 0.6 * S)
            d = sf.smax(d, -self.head_ell(g, mirrored(NOSTRIL[0], s), NOSTRIL[1], oz=oz), 0.4 * S)
        # the forelock: curls joined with a small k, so a crease runs between them
        locks = None
        for c, r, fwd in CURLS:
            e = self.head_ell(g, c, r, sf.rot("x", fwd), oz=oz)
            locks = e if locks is None else sf.smin(locks, e, 0.25 * S)
        d = sf.smin(d, locks, 0.8 * S)
        d = np.maximum(d, -g.Z)                             # its flat bottom
        self.head_raw = d
        d, added = sf.self_support(g, d, ANGLE)
        d = sf.base_prism(g, np.maximum(d, -g.Z), 0.8)
        print(f"  head: self-support grew {added:.0f} mm3")
        # A smile was cut here, under the nostrils, as a V groove after the
        # support: on the muzzle's lower face, which looks down, its ceiling
        # hung and put 301 support moves in the head, so it was dropped; so
        # were rings round the horns, whose ceilings hung on the leaning
        # horns (2026-11-05)
        self.head_supported = d.copy()
        # the chin rests on the heart's lobes: nothing of it inside them; the
        # cut roofed no flatter than ANGLE, so its ceiling prints
        d = np.maximum(d, -roofed(g, self.heart_on_A(False, g, oz) - CLR))
        self.head_d = d
        return d

    def head_on_A(self, d):
        out = np.full(self.A.X.shape, 10.0, np.float32)
        n = min(d.shape[2], out.shape[2] - self.m)
        out[:, :, self.m:self.m + n] = d[:, :, :n]
        return out

    # ----- the body -----
    def body(self, head_A):
        g = self.A
        body = sf.smin(self.ell(g, *v1.BELLY), self.ell(g, *v1.SQUISH), 6 * S)
        body = sf.smin(body, self.ell(g, *v1.CHEST), 6 * S)
        for s in (1, -1):
            m = np.array([s, 1, 1], np.float32)
            leg = self.stick(g, np.asarray(v1.HIP) * m, np.asarray(v1.ANKLE) * m, *v1.LEG_R)
            foot = self.ell(g, np.asarray(v1.FOOT[0]) * m, v1.FOOT[1], sf.rot("z", -v1.FOOT[2] * s))
            body = sf.smin(body, sf.smin(leg, foot, 3 * S), 5 * S)
            sh, el, ha = (np.asarray(p) * m for p in (v1.SHOULDER, v1.ELBOW, v1.HAND))
            r_el = sum(v1.ARM_R) / 2
            arm = sf.smin(self.stick(g, sh, el, v1.ARM_R[0], r_el), self.stick(g, el, ha, r_el, v1.ARM_R[1]), 1.5 * S)
            body = sf.smin(body, arm, 3.0 * S)
        tail = np.minimum(self.stick(g, *v1.TAIL[0], v1.TAIL_R, v1.TAIL_R), self.stick(g, *v1.TAIL[1], v1.TAIL_R, v1.TAIL_R))
        tuft = None
        for c, r, yaw in TAIL_LOCKS:
            e = self.ell(g, c, r, sf.rot("z", yaw))
            tuft = e if tuft is None else sf.smin(tuft, e, 0.3 * S)   # small k: a crease between locks
        self.tuft = tuft
        tail = sf.smin(tail, tuft, 1.2 * S)
        body = sf.smin(body, tail, 2.5 * S)
        body = sf.smin(body, self.ell(g, *v1.PAD_BEHIND), 4 * S)
        body = sf.smin(body, self.ell(g, *v1.LAP), 2.5 * S)
        # the neck: the head's footprint behind the heart (the chin in front
        # of that rests on the heart's lobes), stood down onto her shoulders
        j0 = int(np.searchsorted(self.H.axes[2], 0.0))
        heart_back = heart_pose()[1][1]
        # her front above the lap: a plane FRONT_GAP behind the heart's back.
        # At CLR the support cones under her neck left a 0.8 mm wedge there
        # whose ceiling the slicer propped (1,851 moves)
        front = heart_back + CLR + FRONT_GAP
        foot = (head_A[:, :, self.m + j0] < 0) & (g.Y[:, :, 0] > front)
        self.foot = foot
        d2 = sf.exact2d(None, g.axes[0], g.axes[1], refine=1, inside=foot)[:, :, None]
        # her shoulders round down from the collar (a parabola of radius
        # SHOULDER at the collar): cut flat, everything of v1's belly above
        # the neck stood out behind the head as a shelf, and a straight
        # slope read as a box from the side
        dd = np.maximum(d2, 0)
        shoulder = (g.Z - NECK_Z + dd * dd / (2 * SHOULDER)) / np.sqrt(1 + (dd / SHOULDER) ** 2)
        body = sf.smax(body, shoulder, 3 * S)
        # the neck reaches out under the whole collar: under the collar's
        # front corners there was only air over her arms, and the support
        # cones grown there ended in keels the slicer propped (2,018 moves)
        neck = np.maximum(np.maximum(d2 - 2 * COLLAR_R, g.Z - NECK_Z), NECK_Z - NECK_H - g.Z)
        body = sf.smin(body, neck, 3 * S)
        # and a wall behind the heart, from the plate to her lap's height,
        # for the heart's back to rest on (the cones under her chest pad
        # ended in a keel there too)
        hw = HEART_W / 2 - 3.0
        wall = np.maximum(np.maximum(np.abs(g.X) - hw, g.Z - LAP_TOP),
                          np.maximum(front - CLR - FRONT_GAP - g.Y, g.Y - (front + 8.0)))
        body = sf.smin(body, wall, 2 * S)
        body = np.maximum(body, g.Z - NECK_Z)
        # the collar: a tube on her shoulders round the head's footprint
        collar = np.sqrt((d2 - COLLAR_R) ** 2 + (g.Z - NECK_Z) ** 2) - COLLAR_R
        # its ends: rounded, COLLAR_END behind her front. Over the heart's top
        # it was a 1 mm3 speck, and cut flat at her front plane its ends were
        # ragged half-tubes beside the chin in the front view
        collar = sf.smax(collar, front + COLLAR_END - g.Y, COLLAR_R)
        self.collar = collar
        body = np.minimum(body, collar)
        # the hoof clefts, as v1
        for s in (1, -1):
            m = np.array([s, 1, 1], np.float32)
            c, r = np.asarray(v1.FOOT[0]) * m, v1.FOOT[1]
            x, y, z = g.local(P(c), sf.rot("z", -v1.FOOT[2] * s))
            groove = np.maximum(np.abs(x) - v1.CLEFT[0] / 2 * S, np.abs(z) - r[2] * v1.PAD * 0.8 * S)
            groove = np.maximum(groove, y + (r[1] - v1.CLEFT[1]) * S)
            body = np.maximum(body, -groove)
        body = sf.cut_base(g, body)
        # nothing of the head or heart may be inside her: their own shapes,
        # CLR larger, carved out (the collar hugs the head, the lap and arms
        # cradle the heart)
        heart_A = self.heart_on_A(stitches=False)
        self.heart_A = heart_A
        # the heart's pocket, roofed (its lobes are round on top), and nothing
        # of her in front of the heart's back above her lap: there she filled
        # the notch between the lobes and hung over them (2,399 support moves)
        pocket = roofed(g, heart_A - CLR)
        pocket = np.minimum(pocket, np.maximum(g.Y - front, LAP_TOP - g.Z))
        body = np.maximum(body, -(head_A - CLR))
        body = np.maximum(body, -pocket)
        self.body_raw = body
        body, added = sf.self_support(g, body, ANGLE)
        body = sf.cut_base(g, body)
        print(f"  body: self-support grew {added:.0f} mm3")
        # the cones must not grow into the head or heart
        body = np.maximum(body, -(head_A - CLR))
        body = np.maximum(body, -pocket)
        body = sf.base_prism(g, body, 0.8)
        self.body_d = body
        return body

    def heart_on_A(self, stitches=True, g=None, oz=0.0):
        g = self.A if g is None else g
        R, o = heart_pose()
        o = o - [0, 0, oz]
        x, y, z = g.local(o, R)
        # assembled, the heart's outline lies in the x-z plane: x across, z - tip up
        d2 = heart_2d(g.axes[0] - o[0], g.axes[2] - o[2])
        d2 = np.broadcast_to(d2[:, None, :], g.X.shape)
        f = heart_field(d2, x, y, z, stitches)
        return np.maximum(f, -(g.Z + oz))              # its tip stands on the plate

    # ----- colour regions on the body and head (fields, inside negative) -----
    def body_regions(self):
        g, d = self.A, self.body_d
        skin = -(d + SHELL * S)
        black = []
        for kind, blobs in v1.SPOTS:
            if kind != "body":
                continue
            f = None
            for c, r in blobs:
                e = self.ell(g, c, (r, r, r))
                f = e if f is None else sf.smin(f, e, 2 * S)
            black.append(f)
        for s in (1, -1):
            m = np.array([s, 1, 1], np.float32)
            c, r = np.asarray(v1.FOOT[0]) * m, v1.FOOT[1]
            Rf = sf.rot("z", -v1.FOOT[2] * s)
            x, y, z = g.local(P(c), Rf)
            pad = self.ell(g, c, np.asarray(r) * np.array([v1.PAD, 2.0, v1.PAD]), Rf)
            black.append(np.maximum(pad, y + (r[1] - v1.HOOF_SOLE) * S))
            a, b = np.asarray(v1.ELBOW) * m, np.asarray(v1.HAND) * m
            ax = (b - a) / np.linalg.norm(b - a)
            cap = self.ell(g, b, (v1.ARM_R[1] + 0.6,) * 3)
            plane = ((g.X - P(b)[0]) * ax[0] + (g.Y - P(b)[1]) * ax[1] + (g.Z - P(b)[2]) * ax[2]
                     - (v1.ARM_R[1] - v1.HOOF_ARM) * S)
            black.append(np.maximum(cap, -plane))
        black.append(self.tuft - 0.3 * S)
        red = self.collar - 0.05
        return {"red": np.maximum(red, skin), "black": np.maximum(np.minimum.reduce(black), skin)}

    def head_regions(self):
        g, d, oz = self.H, self.head_d, NECK_Z
        skin = -(d + SHELL * S)
        black = []
        f = None
        for c, r in [b for k, bl in v1.SPOTS if k == "head" for b in bl]:
            e = self.head_ell(g, np.asarray(c) + [0, 0, LIFT], (r, r, r), oz=oz)
            f = e if f is None else sf.smin(f, e, 2 * S)
        horns = np.minimum.reduce([self.stick(g, head_pt(mirrored(HORN[0], s)), head_pt(mirrored(HORN[2], s)), 3.5, 3.5, oz)
                                   for s in (1, -1)])
        black.append(np.maximum(f, -horns))
        for s in (1, -1):
            eye = self.head_ell(g, mirrored(v1.EYE[0], s) + [0, 0, LIFT], v1.EYE[1], oz=oz) - 0.15 * S
            shine = self.head_ell(g, mirrored(v1.SHINE[0], s) + [0, 0, LIFT], (v1.SHINE[1],) * 3, oz=oz)
            black.append(np.maximum(eye, -shine))
        pink = [self.head_ell(g, *MUZZLE, oz=oz) - 0.3 * S]
        for s in (1, -1):
            pink.append(self.head_ell(g, mirrored(v1.BLUSH[0], s) + [0, 0, LIFT], (v1.BLUSH[1],) * 3, oz=oz))
        return {"black": np.maximum(np.minimum.reduce(black), skin),
                "pink": np.maximum(np.minimum.reduce(pink), skin)}


def ear_grid(step):
    return sf.Grid(np.array([-TAB["l"] - 1.5, -EAR_W / 2 - 1.5, -1.0]),
                   np.array([EAR_L + 1.5, EAR_W / 2 + 1.5, EAR_T + 1.0]), step)


def heart_grid(step):
    hgt = sf.heart2d(np.zeros(1), np.zeros(1), HEART_W)[1]
    return sf.Grid(np.array([-HEART_W / 2 - 1.5, -1.5, -1.0]),
                   np.array([HEART_W / 2 + 1.5, hgt + 1.5, HEART_T + HEART_DOME + 1.0]), step)


def main():
    import trimesh
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=float, default=0.25)
    ap.add_argument("--out", default=str(HERE / "parts"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    stats = {}
    t0 = time.time()
    cow = Cow2(a.step)
    hd = cow.head()
    head_A = cow.head_on_A(cow.head_supported)
    print(f"  head built in {time.time() - t0:.0f}s")
    bd = cow.body(head_A)
    print(f"  body built in {time.time() - t0:.0f}s")

    # the maker's mark under her, inlaid in black
    mark = sf.obc_mark_meshes(6.0, (v1.MARK_AT[0] * S, v1.MARK_AT[1] * S), out)
    stats["body"] = sf.export_parts(cow.A, bd, cow.body_regions(), ["black", "red"], "white", out, "body",
                                    mark=mark, mark_colour="black")
    # her neck peg, exact, in white
    pegs = neck_peg_solid().translate([0, 0, NECK_Z])
    for stem in ("body_white", "body"):
        m = sf.to_manifold(trimesh.load(out / f"{stem}.stl", force="mesh")) + pegs
        sf.from_manifold(m).export(out / f"{stem}.stl")
    stats["head"] = sf.export_parts(cow.H, hd, cow.head_regions(), ["black", "pink"], "white", out, "head",
                                    cuts=[neck_peg_solid(PEG_CLR), ear_slot_solid(1), ear_slot_solid(-1)])

    # ears, flat: right white, left black, both pink inside
    eg = ear_grid(min(a.step, 0.15))
    ef = ear_field(eg.X, eg.Y, eg.Z)
    inner = np.maximum(ear_inner(eg.X, eg.Y, eg.Z), ef)
    stats["ear_r"] = sf.export_parts(eg, ef, {"pink": inner}, ["pink"], "white", out, "ear_r")
    stats["ear_l"] = sf.export_parts(eg, ef, {"pink": inner}, ["pink"], "black", out, "ear_l")

    # heart, flat on its back
    hg = heart_grid(min(a.step, 0.15))
    d2 = heart_2d(hg.axes[0], hg.axes[1])
    d2 = np.broadcast_to(d2[:, :, None], hg.X.shape)
    hf = heart_field(d2, hg.X, hg.Y, hg.Z)
    hf = np.maximum(hf, -P(v1.HEART_TIP)[2] - hg.Y)    # its tip flat, where it stands on the plate assembled
    stats["heart"] = sf.export_parts(hg, hf, {}, [], "red", out, "heart")
    # the booleans can leave a zero-volume sheet as its own body in a part's
    # union (the head's, after the ear slots): the gate counts it as floating
    for name in PARTS:
        m = trimesh.load(out / f"{name}.stl", force="mesh")
        keep = [b for b in m.split(only_watertight=False) if abs(b.volume) > 0.05]
        if len(keep) < len(m.split(only_watertight=False)):
            trimesh.util.concatenate(keep).export(out / f"{name}.stl")
    (out / "build.json").write_text(json.dumps(stats, indent=1))
    print(f"  done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
