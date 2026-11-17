"""Urban Kid: a designer-toy figure in seven one-colour prints (2026-11-17).

Scott: "a very detailed character figure. Make it a fun urban character. Wearing
a OBC chain pendant. Baggy pants and a hoodie." He picked forms 1 and 5: the
designer-toy kid standing, hands in his hoodie pocket, split into one print per
colour so it is full colour without an AMS.

  base     a round plinth, the OBC mark engraved under it      (base.scad)
  shoes    two chunky sneakers, upright on their soles
  pants    baggy cargos, upright on their stacked cuffs
  hoodie   torso, arms and the hood down as a collar roll, upright on its hem
  head     printed UPSIDE DOWN on the flat the cap sits on: so the round face
           and the chin, which hang under a head printed upright, are its top
  cap      worn backwards, upright, its brim flat on the plate
  chain    the chain and OBC pendant, flat on its back           (chain.scad)

Each joint hides under the next colour (DETAIL_STANDARD rule 8, a band where
forms meet): the cuffs over the sneakers, the hem over the waist, the collar
roll round the neck, the cap's band round its own seam. The joints are D-shaped
pins printed lying down (pins.scad): push-fit, and a drop of glue to keep.

Built as signed-distance fields (tools/sdf_figure.py), as the Kawaii Cow and the
Teacup Bear, each print on its own grid in assembly coordinates (mm, front -y,
up +z), made self-supporting in its own print pose.

    python3 kid.py               parts/*.stl, final (0.25 mm grid)
    python3 kid.py --step 0.5    a quick draft
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

ANGLE = 37.0          # deg from upright: every overhang (DETAIL_STANDARD rule 7)
CONE = 28.0           # the self-support cones, well inside ANGLE: PrusaSlicer at threshold 45 still propped
                      # steps of 0.17 mm a layer (40 deg) on these meshes, measured 2026-11-17
TRIM = 31.0           # the last pass: no layer steps out more than this past the one below

# ---------- joint planes (assembly z, mm) ----------
Z_BASE = 5.0          # the base's top: the sneakers stand here
Z_ANKLE = 12.0        # the sneakers' tops, the cuffs' bottoms
Z_WAIST = 40.0        # the pants' top, the hoodie's hem
Z_NECK = 68.0         # the hoodie's neck platform, the head's neck
HS = 1.28             # the head and cap, drawn at 1/HS round the neck: a designer toy's big head
CAP_S = 92.0          # the cap plane as drawn (head-scaled coordinates)
Z_CAP = Z_NECK + (CAP_S - Z_NECK) * HS   # ... and where it really is: the head's top flat

SHOE_X = 9.0          # the sneakers' centres, either side
SHOE_TOE_OUT = 8.0    # deg

CHEST_Y = -9.0        # the hoodie's flat chest, where the chain lies
COLOURS = {"base": "black", "pin": "black", "shoe_r": "white", "shoe_l": "white", "pants": "charcoal", "hoodie": "red",
           "head": "skin", "cap": "black", "chain": "gold"}
SDF_PARTS = ("shoe_r", "shoe_l", "pants", "hoodie", "head", "cap")


def v3(*a):
    return np.asarray(a, np.float32)


def groove(d, band, w=0.35, depth=0.6, where=None):
    """Cut a V groove into field d along the zero set of `band` (a distance-like
    field across the groove line): half-width w at the surface, `depth` deep.
    where: a field, cut only where it is negative."""
    v = np.abs(band) - w * np.clip(1.0 + d / depth, 0.0, 1.0)
    cut = np.maximum(v, -(d + depth))
    if where is not None:
        cut = np.maximum(cut, where)
    return np.maximum(d, -cut)


def slab_box(g, lo, hi, r=0.0):
    """An axis box with rounded edges r."""
    c = (np.asarray(lo) + np.asarray(hi)) / 2
    h = (np.asarray(hi) - np.asarray(lo)) / 2 - r
    qx, qy, qz = np.abs(g.X - c[0]) - h[0], np.abs(g.Y - c[1]) - h[1], np.abs(g.Z - c[2]) - h[2]
    out = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
    return out + np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0) - r


def torus_z(g, c, R, r, sy=1.0):
    """A torus round a vertical axis at c, ring radius R (y scaled by sy), tube r."""
    x, y, z = g.X - c[0], (g.Y - c[1]) / sy, g.Z - c[2]
    q = np.sqrt(x * x + y * y) - R
    return np.sqrt(q * q + z * z) - r


def foot(g, d, z0, height=0.8):
    """sf.base_prism for a part whose plate is at z0, not 0: the bottom `height`
    mm stood straight up, so elephant-foot compensation leaves nothing hanging."""
    zs = g.axes[2]
    k = int(np.searchsorted(zs, z0 + height))
    ref = d[:, :, k]
    for j in range(k):
        if zs[j] > z0:
            d[:, :, j] = np.minimum(d[:, :, j], np.maximum(ref, z0 - zs[j]))
    return d


def under_chamfer(g, f, base, zb, down=-1):
    """A patch f standing on the surface `base`, its underside cut back to ANGLE:
    a point d mm out from base is kept only at zb + d / tan(90 - ANGLE) or
    higher, so the patch's bottom edge leans in toward the cloth instead of
    overhanging it. down=+1 for a part printed upside down (the head)."""
    # at CONE, not ANGLE: cut exactly at 37 deg, voxel noise left specks of
    # 0.01 mm2 under the pocket flaps and the slicer propped every one
    rise = np.tan(np.radians(90 - CONE)) * np.maximum(base, 0.0)
    if down < 0:
        return np.maximum(f, zb + rise - g.Z)
    return np.maximum(f, g.Z - (zb - rise))


def wall_wedge(f, into, length, down=-1):
    """A feature on a wall, with a 37 deg wedge under it running back into the
    wall: the union of copies of f moved 3 voxels toward the wall and 4 down
    (atan 3/4 = 36.9 deg), `length` mm of wall travel.

    self_support() grows cones that shrink every way, so under a bump narrower
    than it stands proud (a drawstring's aglet) the cone thinned out before it
    reached the wall and ended in a point in mid-air, which the slicer propped
    (2026-11-17, 400 support moves on the hoodie). Copies keep the bump's width.
    into: (axis, +1 or -1), the wall's direction; down: -1 for a part printed
    upright, +1 for one printed upside down (the head)."""
    ax, sgn = into
    out = f.copy()
    k, step = 1, None
    while True:
        sh = [0, 0, 0]
        sh[ax] = 3 * k * sgn
        sh[2] = 4 * k * down
        g = np.full_like(f, 1e3)
        src = tuple(slice(max(0, -s_), f.shape[i] - max(0, s_)) for i, s_ in enumerate(sh))
        dst = tuple(slice(max(0, s_), f.shape[i] - max(0, -s_)) for i, s_ in enumerate(sh))
        g[dst] = f[src]
        out = np.minimum(out, g)
        k += 1
        if step is None:
            step = 1
        if 3 * (k - 1) * VOX >= length:
            break
    return out


VOX = 0.25            # the grid step these wedges are counted in (kid.py's final step)


def torus_drop(g, c, R, r):
    """torus_z with its lower half a teardrop: below the tube's centre its two
    sides run down at ANGLE to a point, so the roll's underside never overhangs."""
    x, y, z = g.X - c[0], g.Y - c[1], g.Z - c[2]
    q = np.sqrt(x * x + y * y) - R
    circ = np.sqrt(q * q + z * z) - r
    a = np.radians(ANGLE)
    wedge = np.abs(q) * np.cos(a) - (z + r / np.sin(a)) * np.sin(a)
    return np.minimum(circ, np.maximum(wedge, z))


def trim_up(g, d, angle=TRIM, z0=None):
    """The last pass on an upright part: each layer clipped to within `angle` of
    the one below (in true 2-D distance, as self_support grows), from the plate
    up. self_support grows cones under every overhang; what is left after it is
    voxel noise on faces cut at the limit, specks of 0.002-0.2 mm2 the slicer
    propped every time (2026-11-17). Returns (field, removed mm3); the removed
    volume is printed, so a cone that ended in mid-air (whose whole column this
    would shave away) shows up as a big number instead of a quiet change."""
    step = g.step
    r = step * np.tan(np.radians(angle))
    out = d.copy()
    before = int((d < 0).sum())
    k0 = 0 if z0 is None else int(np.searchsorted(g.axes[2], z0 + 0.9))
    solid = np.where((d < 0).any(axis=(0, 1)))[0]
    k0 = max(k0, int(solid[0]) + 1 if len(solid) else d.shape[2])   # from the first layer on the plate
    for k in range(max(k0, 1), d.shape[2]):
        s2 = sf._layer_sd2(out[:, :, k - 1], step, 4)
        if s2 is None:
            out[:, :, k] = np.maximum(out[:, :, k], 1.0)
            continue
        out[:, :, k] = np.maximum(out[:, :, k], s2 - r)
    return out, (before - int((out < 0).sum())) * step ** 3


def trim_down(g, d, angle=TRIM):
    """trim_up for a part printed upside down (the head)."""
    f, removed = trim_up(g, np.ascontiguousarray(d[:, :, ::-1]), angle)
    return np.ascontiguousarray(f[:, :, ::-1]), removed


def support_up(g, d):
    """Self-support for a part printed upright: cones of ANGLE under overhangs."""
    d, added = sf.self_support(g, d, CONE)
    return d, added


def support_flipped(g, d):
    """Self-support for a part printed upside down (the head): the field's z
    order reversed, supported, and reversed back."""
    f = np.ascontiguousarray(d[:, :, ::-1])
    f, added = sf.self_support(g, f, CONE)
    return np.ascontiguousarray(f[:, :, ::-1]), added


class Scaled:
    """A Grid seen from a frame scaled 1/s about pivot: features drawn here come
    out s times bigger, and a field built on it times s is a real distance."""

    def __init__(self, g, pivot, s):
        self.step, self.axes, self.origin = g.step / s, g.axes, g.origin
        self.X = (g.X - pivot[0]) / s + pivot[0]
        self.Y = (g.Y - pivot[1]) / s + pivot[1]
        self.Z = (g.Z - pivot[2]) / s + pivot[2]

    local = sf.Grid.local


PIVOT = (0.0, 1.0, Z_NECK)


class Kid:
    def __init__(self, step):
        self.step = step
        s = step

        def grid(lo, hi):
            return sf.Grid(np.array(lo, float), np.array(hi, float), s)
        self.G = {
            "shoe": grid([-8.5, -18.5, Z_BASE - 1.0], [8.5, 11.0, Z_ANKLE + 1.0]),
            "pants": grid([-20.0, -13.0, Z_ANKLE - 1.0], [20.0, 13.5, Z_WAIST + 1.0]),
            "hoodie": grid([-26.5, -17.5, Z_WAIST - 1.0], [26.5, 17.0, 74.0]),
            "head": grid([-27.5, -25.5, Z_NECK - 1.0], [27.5, 25.5, Z_CAP + 1.0]),
            "cap": grid([-27.5, -25.5, Z_CAP - 1.0], [27.5, 43.0, Z_NECK + 41.0 * HS]),
        }

    # ------------------------------------------------------------- head
    SKULL = (v3(0, 0.5, 86.5), v3(17.5, 16.2, 16.5))
    JAW = (v3(0, -3.0, 79.0), v3(14.2, 11.8, 9.8))

    def face_base(self, g):
        """Skull, jaw, chin and cheeks: the face the features sit on (drawn frame)."""
        d = sf.ellipsoid(g, *self.SKULL)
        d = sf.smin(d, sf.ellipsoid(g, *self.JAW), 5.0)
        d = sf.smin(d, sf.ellipsoid(g, v3(0, -10.0, 74.6), v3(5.2, 3.6, 3.0)), 2.0)        # chin
        for s in (1, -1):
            d = sf.smin(d, sf.ellipsoid(g, v3(s * 8.2, -11.2, 77.6), v3(4.2, 3.0, 3.0)), 2.5)   # cheeks
        return d

    def surf(self, x, z):
        """The front of the face at (x, z): where face_base crosses zero along -y."""
        class Line:
            pass
        L = Line()
        L.Y = np.linspace(-25.0, 0.0, 2501).astype(np.float32)
        L.X, L.Z = np.full_like(L.Y, x), np.full_like(L.Y, z)
        L.local = lambda c, R=None: sf.Grid.local(L, c, R)
        f = self.face_base(L)
        return v3(x, float(L.Y[np.argmax(f < 0)]), z)

    def head(self):
        G = self.G["head"]
        g = Scaled(G, PIVOT, HS)
        d = self.face_base(g)
        S = self.surf
        d = sf.smin(d, sf.ellipsoid(g, S(0, 79.4) + v3(0, 0.6, 0), v3(2.4, 1.9, 2.0)), 1.2)   # nose
        for s in (1, -1):
            # ears, with a shallow bowl
            ear = sf.ellipsoid(g, v3(s * 16.8, 1.8, 81.5), v3(2.5, 4.1, 5.0))
            ear = sf.smax(ear, -sf.ellipsoid(g, v3(s * 19.0, 1.4, 81.5), v3(1.0, 2.3, 3.0)), 0.4)
            d = sf.smin(d, ear, 1.2)
            # eyes, heavy-lidded: an almond carved only below the lid line, so the lid
            # is the face itself and cuts straight across the pupil standing in it
            e = S(s * 6.6, 82.6)
            # bevelled: the socket deepens at ANGLE from its rim, to 1.3, so printed
            # upside down its rim is no ceiling (a round socket's was, and the cones
            # under it thinned to slivers the slicer would not print, 2026-11-17)
            ex, ez = g.X - e[0], g.Z - e[2]
            ca, sa = np.cos(np.radians(8 * s)), np.sin(np.radians(8 * s))
            u, w = ca * ex - sa * ez, sa * ex + ca * ez
            outline = (np.sqrt((u / 4.5) ** 2 + (w / 3.3) ** 2) - 1.0) * 3.3
            depth = np.minimum(1.3, -outline * np.tan(np.radians(90 - ANGLE)))
            sock = np.maximum(np.maximum(outline, -(d + depth)), g.Z - (e[2] + 0.9))
            d = np.maximum(d, -sock)
            pup = sf.ellipsoid(g, e + v3(-0.45 * s, 1.25, -0.35), v3(2.35, 1.15, 2.6))
            d = np.minimum(d, np.maximum(pup, g.Z - (e[2] + 0.9)))
            # a crease over the lid
            lid = sf.stick(g, S(s * 2.8, 85.0) + v3(0, 0.15, 0), S(s * 10.4, 84.4) + v3(0, 0.15, 0), 0.0, 0.0)
            d = groove(d, lid, 0.35, 0.45)
            # brows: thick, straight, low at the inner end
            # (printed upside down, a brow's top is an overhang; its wedge runs up
            # into the forehead, a brow ridge, or the slicer propped it)
            brow = sf.stick(g, S(s * 2.6, 87.0), S(s * 10.0, 88.4) + v3(0, 0.2, 0), 1.45, 1.2)
            d = sf.smin(d, wall_wedge(brow, (1, 1), 2.5, down=1), 0.5)
        # the grin: lopsided, up at his left, a dimple at that end
        p0, p1, p2 = S(-4.6, 75.9), S(1.2, 75.2), S(5.0, 76.6)
        smile = np.minimum(sf.stick(g, p0, p1, 0.0, 0.0), sf.stick(g, p1, p2, 0.0, 0.0))
        d = groove(d, smile, 0.55, 0.9)
        d = groove(d, sf.stick(g, p2 + v3(0.7, 0, -0.9), p2 + v3(0.9, 0, 0.6), 0.0, 0.0), 0.4, 0.6)
        d = d * HS
        g = G
        d = sf.smin(d, sf.stick(g, v3(0, 1.0, Z_NECK - 1.0), v3(0, 1.0, Z_NECK + 10.0), 6.0, 6.0), 2.5)   # neck
        d = np.maximum(d, g.Z - Z_CAP)                       # the flat the cap sits on
        d = np.maximum(d, Z_NECK - g.Z)                      # the neck's flat bottom
        self.head_raw = d
        d, added = support_flipped(g, d)
        d = np.maximum(d, g.Z - Z_CAP)                       # the cones grow toward the plate: stop them at it
        d, gone = trim_down(g, d)
        print(f"  head: trim took {gone:.1f} mm3")
        print(f"  head: self-support grew {added:.0f} mm3")
        return d

    # ------------------------------------------------------------- cap (backwards)
    def cap(self):
        G = self.G["cap"]
        g = Scaled(G, PIVOT, HS)
        zc = CAP_S              # the cap plane, in the drawn frame
        c, r = self.SKULL
        crown = sf.ellipsoid(g, c + v3(0, 0.4, 0.6), r + v3(0.9, 0.9, 1.6))
        d = np.maximum(crown, zc - g.Z)
        # the brim, at the back, flat on the plate: an ellipse in plan, rounded edge
        e = sf.ellipsoid(g, v3(0, 12.0, zc + 1.0), v3(13.5, 20.0, 1.0))
        brim = np.maximum(e, zc - g.Z)
        brim = np.maximum(brim, 8.0 - g.Y)
        d = sf.smin(d, brim, 1.0)
        # the button on top
        top = c[2] + 0.6 + r[2] + 1.6
        button = sf.ellipsoid(g, v3(0, 0.9, top + 0.2), v3(1.7, 1.7, 1.2))
        d = sf.smin(d, under_chamfer(g, button, crown, top - 1.2), 0.3)    # its rim leans in: no ledge
        # the sweatband: the crown above it stands 0.4 in, stepping in at ANGLE, so
        # the band's edge needs nothing under it (a groove there was propped)
        d = d + 0.4 * np.clip((g.Z - (zc + 3.0)) / (0.4 / np.tan(np.radians(ANGLE))), 0.0, 1.0)
        # six panel seams, meridians through the button, above the band
        crown_only = zc + 3.6 - g.Z
        for k in range(6):
            a = np.radians(30 + 60 * k)
            band = (g.X - 0) * np.cos(a) + (g.Y - 0.9) * np.sin(a)
            # only on one side of the axis (a meridian, not a full great circle)
            half = -((g.X) * -np.sin(a) + (g.Y - 0.9) * np.cos(a))
            off_button = 2.6 - np.sqrt(g.X ** 2 + (g.Y - 0.9) ** 2)     # they stop at the button
            d = groove(d, band, 0.32, 0.5, np.maximum(np.maximum(crown_only, half), off_button))
        # worn backwards: the snapback's opening is over his forehead. A recess with
        # bevelled sides (its ceiling leans in at ANGLE: a square recess was propped),
        # a strap across its foot with three studs
        arch = np.maximum(np.abs(g.X) - 5.5, np.sqrt(g.X ** 2 + np.maximum(g.Z - (zc + 3.5), 0) ** 2) - 5.5)
        depth = np.minimum(1.2, -arch * np.tan(np.radians(90 - ANGLE)))
        carve = np.maximum(np.maximum(arch, -(crown + depth)), np.maximum(g.Y + 5.0, zc - g.Z))
        d = np.maximum(d, -carve)
        strap = np.maximum(slab_box(g, (-6.2, -30, zc), (6.2, 30, zc + 1.8)), crown)
        strap = np.maximum(strap, np.maximum(-(crown + 1.4), g.Y + 5.0))
        d = np.minimum(d, strap)
        cc, rr = c + v3(0, 0.4, 0.6), r + v3(0.9, 0.9, 1.6)
        y_front = cc[1] - rr[1] * np.sqrt(1 - ((zc + 0.9 - cc[2]) / rr[2]) ** 2)
        for xs in (-3.0, 0.0, 3.0):
            stud = sf.ellipsoid(g, v3(xs, y_front - 0.1, zc + 0.9), v3(0.75, 0.6, 0.75))
            stud = under_chamfer(g, np.maximum(stud, zc - g.Z), crown, zc)   # from the plate: no first-layer ledge
            d = np.minimum(d, stud)
        d = np.maximum(d, zc - g.Z) * HS
        d, added = support_up(G, d)
        d = np.maximum(d, Z_CAP - G.Z)
        d, gone = trim_up(G, d, z0=Z_CAP)
        print(f"  cap: trim took {gone:.1f} mm3")
        print(f"  cap: self-support grew {added:.0f} mm3")
        return d

    # ------------------------------------------------------------- hoodie
    def hoodie(self):
        g = self.G["hoodie"]
        d = sf.ellipsoid(g, v3(0, 0.0, 57.0), v3(16.8, 11.8, 13.5))                       # chest
        d = sf.smin(d, sf.ellipsoid(g, v3(0, -0.4, 46.5), v3(16.2, 11.8, 9.0)), 6.0)       # belly
        for s in (1, -1):
            d = sf.smin(d, sf.ellipsoid(g, v3(s * 12.5, 0.6, 62.5), v3(7.5, 8.8, 6.2)), 4.0)   # shoulders
        # a flat chest for the chain to lie on
        d = sf.smax(d, CHEST_Y - g.Y, 2.0)
        # the hem band: tighter than the body, ribbed
        hem_top = Z_WAIST + 3.2
        # (the band is marked by its ribs alone: set 0.45 in, its step met the cones
        # under the forearms and the pocket in specks the slicer propped)
        # arms: shoulder, elbow out a little, hands into the pocket's side openings
        for s in (1, -1):
            sh, el, ha = v3(s * 16.6, 1.0, 60.0), v3(s * 17.4, 2.6, 50.6), v3(s * 9.4, -5.6, 47.8)
            arm = sf.smin(sf.stick(g, sh, el, 4.7, 4.4), sf.stick(g, el, ha, 4.4, 3.9), 1.5)
            # the cuff: a band near the wrist
            cuff_c = el + 0.72 * (ha - el)
            ax = (ha - el) / np.linalg.norm(ha - el)
            along = (g.X - cuff_c[0]) * ax[0] + (g.Y - cuff_c[1]) * ax[1] + (g.Z - cuff_c[2]) * ax[2]
            # the seam grooved only above the elbow: along the forearm it faces down onto
            # the belly, and the cones refilling it left slivers the slicer propped
            d = sf.joined(d, arm, 3.0, (0.6, 1.0), where=(el[2] + 1.0) - g.Z)
            d = groove(d, along, 0.3, 0.45, arm - 0.6)
            # elbow folds: two short creases on the outside of the elbow
            for k in (-1.3, 1.3):
                e2 = el + v3(s * 1.2, 0, k)
                fold = sf.stick(g, e2 + v3(0, -2.2, 0), e2 + v3(0, 2.2, 0), 0.0, 0.0) - 0.0
                d = groove(d, fold, 0.3, 0.45)
        # the collar roll: the hood down, a thick roll round the neck, fuller at the back
        roll = torus_z(g, v3(0, 2.0, 67.6), 10.0, 3.3, 1.0)       # set back: the cone under its front cleared the chain
        roll = sf.smin(roll, sf.ellipsoid(g, v3(0, 10.5, 68.0), v3(10.5, 4.6, 5.4)), 2.5)    # the hood, at the back
        # ... draped down onto his back and shoulders: below their middles the roll and
        # the hood fall straight, so neither hangs over air (the slicer propped the
        # roll's back, where its underside stood clear of his shoulders)
        q = np.sqrt(g.X ** 2 + (g.Y - 2.0) ** 2) - 10.0
        drape = np.maximum(np.maximum(np.abs(q) - 3.3, g.Z - 67.6), np.maximum(55.0 - g.Z, -(g.Y - 2.0)))
        hx, hy = g.X / 10.5, (g.Y - 10.5) / 4.6
        hood2 = (np.sqrt(hx * hx + hy * hy) - 1.0) * 4.6
        drape = np.minimum(drape, np.maximum(np.maximum(hood2, g.Z - 68.0), 55.0 - g.Z))
        roll = sf.smin(roll, drape, 1.5)
        d = sf.smin(d, roll, 1.5)
        d = groove(d, np.sqrt(g.X ** 2 + (g.Y - 1.0) ** 2) - 13.1, 0.3, 0.5, 63.5 - g.Z)   # under the roll
        # drawstrings from under the collar, outside the chain: cords that sink
        # into the chest at their lower end. A cord standing proud to its tip
        # (round, then flat with an aglet, then with a wedge under it) left a
        # tip in mid-air that the slicer propped every time (2026-11-17)
        for s in (1, -1):
            a, b = v3(s * 7.6, CHEST_Y - 0.25, 64.8), v3(s * 8.6, CHEST_Y + 0.95, 56.4)
            d = sf.smin(d, sf.stick(g, a, b, 0.95, 0.95), 0.4)
            d = groove(d, (g.Z - 58.6) - 0.12 * s * (g.X - s * 8.4), 0.25, 0.35,
                       np.maximum(np.abs(g.X - s * 8.4) - 1.6, g.Y - CHEST_Y))      # the aglet's end
        # raglan seams, collar to underarm
        for s in (1, -1):
            seam = sf.stick(g, v3(s * 8.5, -9.0, 64.0), v3(s * 15.5, -9.0, 53.0), 0.0, 0.0)
            d = groove(d, seam, 0.3, 0.45)
        # the kangaroo pocket: a panel standing 0.9 proud of the flat front, its
        # slanted sides open: the forearms run in under them, the hands hidden
        top_z, bot_z = 49.4, Z_WAIST + 3.6
        x_edge = 7.0 + (top_z - g.Z) / (top_z - bot_z) * 4.5
        side = (np.abs(g.X) - x_edge) * 0.86                  # cos of the slant
        panel = np.maximum(np.maximum(g.Z - top_z, bot_z - g.Z), side)
        panel = np.maximum(panel, np.abs(g.Y - (CHEST_Y - 0.9 + 1.5)) - 1.5)   # front 0.9 proud
        d = sf.smin(d, under_chamfer(g, panel, d, bot_z), 0.25)     # its bottom edge leans in
        # hem ribs: upright grooves every 1.6 mm round the band
        # (their depth fades to nothing over their top 0.55 mm, at ANGLE: cut square,
        # each groove's top was a little ceiling the slicer propped)
        th = np.arctan2(g.Y, g.X) * 15.0
        rib = np.abs(np.mod(th, 1.6) - 0.8)
        rib_d = 0.4 * np.clip((hem_top - 0.3 - g.Z) / 0.55, 0.0, 1.0)
        cut = np.maximum(rib - 0.25 * np.clip(1.0 + d / 0.4, 0.0, 1.0), -(d + rib_d))
        cut = np.maximum(cut, np.maximum(g.Z - (hem_top - 0.3), Z_WAIST + 0.4 - g.Z))
        d = np.maximum(d, -cut)
        # the jaw settles into the collar: the roll and hood give way round the
        # head, 0.3 clear of it (the fit check found them 180 mm3 into each other)
        head = self.face_base(Scaled(g, PIVOT, HS)) * HS
        head = sf.smin(head, sf.stick(g, v3(0, 1.0, Z_NECK - 1.0), v3(0, 1.0, Z_NECK + 10.0), 6.0, 6.0), 2.5)
        d = np.maximum(d, -np.maximum(head - 0.3, Z_NECK - g.Z))
        # the roll's fillet ran down onto the flat chest where the chain lies: keep it flat up to the chain's top
        d = np.maximum(d, -np.maximum(np.maximum(g.Y - CHEST_Y, np.abs(g.Z - 62.0) - 2.0), np.abs(g.X) - 7.5))
        # ... and under the nameplate: the hands' blend into the chest stood 0.1 proud at its corners
        d = np.maximum(d, -np.maximum(np.maximum(g.Y - CHEST_Y, np.abs(g.Z - 54.3) - 4.4), np.abs(g.X) - 7.4))
        # the neck platform: inside the roll, flat at Z_NECK
        d = np.maximum(d, -np.maximum(Z_NECK - g.Z, np.sqrt(g.X ** 2 + (g.Y - 1.0) ** 2) - 6.4))
        d = np.maximum(d, Z_WAIST - g.Z)
        d, added = support_up(g, d)
        d = np.maximum(d, Z_WAIST - g.Z)
        d = foot(g, d, Z_WAIST)
        d, gone = trim_up(g, d, z0=Z_WAIST)
        print(f"  hoodie: self-support grew {added:.0f} mm3, trim took {gone:.1f}")
        return d

    # ------------------------------------------------------------- pants
    def pants(self):
        g = self.G["pants"]
        d = sf.ellipsoid(g, v3(0, 1.0, 37.0), v3(14.6, 10.6, 7.0))                        # hips
        legs = None
        for s in (1, -1):
            hip, knee, ank = v3(s * 7.6, 1.0, 34.0), v3(s * 8.6, -0.4, 25.0), v3(s * SHOE_X, 0.5, 13.8)
            leg = sf.smin(sf.stick(g, hip, knee, 7.2, 7.3), sf.stick(g, knee, ank, 7.3, 7.9), 2.0)
            # bunched over the sneaker: soft rolls stacked and a little off-centre
            for k, (z, dx, R, t) in enumerate(((13.6, 0.2, 7.0, 1.75), (15.9, -0.4, 6.8, 1.6),
                                                (18.2, 0.3, 6.7, 1.55), (20.5, -0.2, 6.6, 1.5))):
                leg = sf.smin(leg, torus_z(g, v3(s * (SHOE_X + dx), 0.5 - 0.3 * k, z), R, t, 1.0), 1.4)   # soft valleys: sharp ones left slivers under each roll
            # cargo pocket on the outer thigh, and its flap: patches that follow the
            # cloth, 1.0 and 1.5 proud. Boxes standing 4 mm off it (the back pockets
            # first) ended their support cones in mid-air, and the slicer propped them
            pc = v3(s * 15.4, 1.2, 27.0)
            outer = -s * (g.X - s * 9.0)                       # the outer half of the leg only
            pocket = np.maximum(slab_box(g, pc - v3(9.0, 4.0, 4.6), pc + v3(9.0, 4.0, 4.6), 1.0), outer)
            cloth = leg
            leg = np.minimum(leg, under_chamfer(g, np.maximum(cloth - 1.0, pocket), cloth, pc[2] - 4.6))
            flap = np.maximum(slab_box(g, pc + v3(-9.0, -4.0, 2.0), pc + v3(9.0, 4.0, 5.0), 0.8), outer)
            leg = np.minimum(leg, under_chamfer(g, np.maximum(cloth - 1.5, flap), cloth, pc[2] + 2.0))
            snap = sf.ellipsoid(g, pc + v3(0, 0, 3.4), v3(9.0, 0.95, 0.95))
            leg = np.minimum(leg, under_chamfer(g, np.maximum(cloth - 2.1, np.maximum(snap, outer)), cloth - 1.5,
                                                pc[2] + 2.6))   # its snap
            legs = leg if legs is None else sf.joined(legs, leg, 1.2, (0.5, 1.0))
        # the hips' seam, grooved at the front and sides only: behind, its lower lip
        # left a sliver the slicer propped
        d = sf.joined(d, legs, 4.0, (0.55, 0.9), where=g.Y - 4.0)
        # a web between the legs, set well back: the cuffs' rolls met at x = 0 in a
        # 2 mm bridge whose underside the slicer propped (2026-11-17)
        web = slab_box(g, (-2.4, -1.0, Z_ANKLE - 1.0), (2.4, 4.0, 33.0), 0.6)
        # its faces lean out at ANGLE to meet the crotch, front and back: a notch with a
        # V-shaped roof between the legs was propped from the plate up
        lean = np.tan(np.radians(ANGLE)) * np.maximum(g.Z - 21.0, 0.0)
        web = np.minimum(web, np.maximum(np.maximum(np.abs(g.X) - 2.4, Z_ANKLE - g.Z),
                                         np.maximum((-1.0 - lean) - g.Y, g.Y - (4.0 + lean))))
        web = np.maximum(web, g.Z - 33.0)
        d = sf.smin(d, web, 0.6)
        for s in (1, -1):
            # a crease down the front of each leg (the flap's edge groove went: its
            # upper flank was a ceiling the slicer propped)
            d = groove(d, g.X - s * 8.4, 0.28, 0.45, np.maximum(g.Y + 2.0, np.maximum(g.Z - 33.0, 21.5 - g.Z)))
            # back pockets, below the hem: patches 0.8 proud of the seat
            bp = np.maximum(slab_box(g, v3(s * 6.5 - 3.3, 0.0, 31.5), v3(s * 6.5 + 3.3, 20.0, 37.6), 0.0), 4.0 - g.Y)
            d = np.minimum(d, under_chamfer(g, np.maximum(d - 0.8, bp), d, 31.5))
        d = np.maximum(d, g.Z - Z_WAIST)
        d = np.maximum(d, Z_ANKLE - g.Z)
        d, added = support_up(g, d)
        d = np.maximum(d, Z_ANKLE - g.Z)
        d = foot(g, d, Z_ANKLE)
        d, gone = trim_up(g, d, z0=Z_ANKLE)
        print(f"  pants: self-support grew {added:.0f} mm3, trim took {gone:.1f}")
        return d

    # ------------------------------------------------------------- a sneaker (local x = 0)
    SOLE = dict(cy=-3.5, hx=6.6, hy=13.1, rc=5.5, h=3.4)

    def shoe(self, side):
        """A chunky cupsole sneaker. The sole's outline is a rounded rectangle and
        the upper stands inside it, leaning in as it rises, so nothing overhangs."""
        g = self.G["shoe"]
        R = sf.rot("z", -SHOE_TOE_OUT * side)
        S = self.SOLE
        x, y, z = g.local(R @ v3(0, S["cy"], 0), R)
        qx, qy = np.abs(x) - (S["hx"] - S["rc"]), np.abs(y) - (S["hy"] - S["rc"])
        out2 = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - S["rc"]
        z0 = Z_BASE + S["h"]
        sole = sf.smax(np.maximum(out2, Z_BASE - g.Z), g.Z - z0, 0.7)
        # the upper: the outline 0.9 in, leaning in 0.45 per mm up; its top rises
        # from the toe to the collar and is rounded over
        yl = y + S["cy"]                                      # along the shoe, 0 at its centre line origin
        top = np.interp(yl, [-17.0, -13.0, -5.5, 12.0], [Z_BASE + 6.6, Z_BASE + 7.6, Z_ANKLE + 0.5, Z_ANKLE + 0.5])
        upper = sf.smax(out2 + 0.9 + 0.45 * np.maximum(g.Z - z0, 0), g.Z - top, 1.8)
        d = sf.smin(sole, upper, 0.4)
        # the midsole line round the sole, and the toe cap's seam across the toe
        d = groove(d, g.Z - (Z_BASE + 1.7), 0.3, 0.45)
        d = groove(d, np.sqrt(x ** 2 + ((yl + 12.6) * 1.15) ** 2) - 5.2, 0.28, 0.4,
                   np.maximum(z0 + 0.6 - g.Z, yl + 11.0))
        # laces: four bars across the tongue, lying on the rising top
        for k in range(4):
            yy = -10.6 + 1.9 * k
            zt = float(np.interp(yy, [-17.0, -13.0, -5.5, 12.0], [Z_BASE + 6.6, Z_BASE + 7.6, Z_ANKLE + 0.5, Z_ANKLE + 0.5]))
            a_, b_ = R @ v3(-2.3, yy, zt - 0.35), R @ v3(2.3, yy, zt - 0.35)
            d = sf.smin(d, sf.stick(g, a_, b_, 0.7, 0.7), 0.3)
        # the side flash: a band standing 0.6 proud on the outer side, rising to the heel
        line = g.Z - (Z_BASE + 5.1 + 0.16 * (yl + 9.0))
        flash = np.maximum(np.maximum(upper - 0.6, np.abs(line) - 0.9), -side * x + 2.0)
        flash = np.maximum(flash, np.maximum(-(yl + 9.5), yl - 5.0))
        flash = under_chamfer(g, flash, upper, Z_BASE + 5.1 + 0.16 * (yl + 9.0) - 0.9)   # its lower edge leans in
        d = np.minimum(d, flash)
        # (no heel tab: under the cuff it can't be seen, and chamfered to print it
        # came out a 0.2 mm sliver the wall check failed)
        d = np.maximum(d, g.Z - Z_ANKLE)
        d = np.maximum(d, Z_BASE - g.Z)
        d, added = support_up(g, d)
        d = np.maximum(d, Z_BASE - g.Z)
        d = foot(g, d, Z_BASE)
        d, gone = trim_up(g, d, z0=Z_BASE)
        print(f"  shoe: self-support grew {added:.0f} mm3, trim took {gone:.1f}")
        return d


# ---------- joints: exact solids, added and cut after meshing (as the cow's) ----------
CLR = 0.15            # peg in socket, all round: a push fit, glue to keep
PIN = dict(r=2.5, half=4.4, flat=0.55)   # the cap's loose pin: radius, half length, flat at r*flat
SOCKET_D = 4.65       # each socket the pin goes into, to its cone


def peg(cx, cy, z0, r, h, clr=0.0, flat=None):
    """A peg standing up from z0 (from 1 mm below it), h tall, then a cone at
    ANGLE from upright, so a socket cut with clr prints its own roof. flat: a
    flat on its +x side at x = cx + r*flat, so it goes in one way."""
    import manifold3d as mf
    R = r + clr
    cone_h = R * np.tan(np.radians(90 - ANGLE))
    m = mf.Manifold.cylinder(h + clr + 1.0, R, R, 96).translate([0, 0, -1.0])
    if clr > 0:
        m = m + mf.Manifold.cylinder(cone_h, R, 0.0, 96).translate([0, 0, h + clr])
    else:
        # the peg's own tip stops at 40 % of its radius: a point is finer than a
        # layer and the slicer drops it (the base came out 0.25 short, 2026-11-17)
        m = m + mf.Manifold.cylinder(cone_h * 0.6, R, 0.4 * R, 96).translate([0, 0, h + clr])
    if flat is not None:
        m = m ^ mf.Manifold.cube([R + 1 + r * flat + clr, 2 * R + 2, h + cone_h + 4]).translate([-R - 1, -R - 1, -2])
    return m.translate([cx, cy, z0])


def pose(m, T):
    return m.transform(np.asarray(T, np.float64)[:3].tolist())


def shoe_peg_xy(side):
    """Where the base's peg goes into a sneaker: under its arch."""
    p = sf.rot("z", -SHOE_TOE_OUT * side) @ v3(0, -3.0, 0)
    return float(p[0] + side * SHOE_X), float(p[1])


def joints():
    """part -> (solids to add, solids to cut), in assembly coordinates."""
    add = {k: [] for k in ("base", "shoe_r", "shoe_l", "pants", "hoodie", "head", "cap")}
    cut = {k: [] for k in add}
    for side, shoe in ((1, "shoe_r"), (-1, "shoe_l")):
        x, y = shoe_peg_xy(side)
        # round: a D-flat socket here read as 0.1-0.3 mm walls to the gate's rays
        # grazing along its flat. The pants hold the sneakers square.
        add["base"].append(peg(x, y, Z_BASE, 2.0, 3.0))
        cut[shoe].append(peg(x, y, Z_BASE, 2.0, 3.0, CLR))
        add[shoe].append(peg(side * SHOE_X, 1.5, Z_ANKLE, 2.2, 4.0))
        cut["pants"].append(peg(side * SHOE_X, 1.5, Z_ANKLE, 2.2, 4.0, CLR))
    for x in (6.0, -6.0):
        add["pants"].append(peg(x, 1.0, Z_WAIST, 2.8, 5.0))
        cut["hoodie"].append(peg(x, 1.0, Z_WAIST, 2.8, 5.0, CLR))
    # the head turns on its neck peg: round, so he can look where you like
    add["hoodie"].append(peg(0.0, 1.0, Z_NECK, 3.0, 5.0))
    cut["head"].append(peg(0.0, 1.0, Z_NECK, 3.0, 5.0, CLR))
    # head and cap: both sides of that joint lie on the plate, so a loose pin
    sock = peg(0.0, 1.0, Z_CAP, PIN["r"], SOCKET_D - CLR, CLR, flat=PIN["flat"])
    cut["cap"].append(sock)
    # the head's: drawn in its print frame (it lies on that face too), where y is
    # mirrored: at y = -1 there is at y = +1 on him. Its print pose is its own inverse
    sock = peg(0.0, -1.0, 0.0, PIN["r"], SOCKET_D - CLR, CLR, flat=PIN["flat"])
    cut["head"].append(pose(sock, print_pose("head")))
    return add, cut


def pin_solid():
    """The cap's pin, as printed: lying on its flat, chamfered ends."""
    import manifold3d as mf
    r, L, f = PIN["r"], 2 * PIN["half"], PIN["flat"]
    c = 0.4
    m = mf.Manifold.cylinder(L - 2 * c, r, r, 96).translate([0, 0, c])
    m = m + mf.Manifold.cylinder(c, r - c, r, 96) + mf.Manifold.cylinder(c, r, r - c, 96).translate([0, 0, L - c])
    m = m ^ mf.Manifold.cube([r + 1 + r * f, 2 * r + 2, L + 2]).translate([-r - 1, -r - 1, -1])
    # lying on its flat: the axis along x, the flat (x = r*f) turned down onto z = 0
    T = np.eye(4)
    T[:3, :3] = sf.rot("y", 90)
    T[2, 3] = r * f
    return pose(m, T)


def chain_pose():
    """4x4 from the chain's print pose (back on z = 0, drawn in his x and z) to
    the assembly: its back on his flat chest, y = CHEST_Y."""
    T = np.eye(4)
    T[:3, :3] = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]
    T[1, 3] = CHEST_Y - 0.05      # a hair off the chest: coplanar faces read as overlap to a boolean
    return T


def print_pose(name):
    """4x4 from assembly to print pose (the inverse puts a print back on him)."""
    T = np.eye(4)
    if name == "head":
        T[:3, :3] = sf.rot("x", 180)
        T[2, 3] = Z_CAP
        return T
    z0 = {"shoe_r": Z_BASE, "shoe_l": Z_BASE, "pants": Z_ANKLE, "hoodie": Z_WAIST, "cap": Z_CAP, "base": 0.0}[name]
    T[2, 3] = -z0
    if name in ("shoe_r", "shoe_l"):
        T[0, 3] = -SHOE_X if name == "shoe_r" else SHOE_X
    return T


def scad_part(name, workdir):
    """The base or the chain, from its .scad, in assembly coordinates."""
    import subprocess
    import trimesh
    import tempfile
    stl = Path(tempfile.mkdtemp()) / f"{name}_scad.stl"
    subprocess.run(["openscad", "-o", str(stl), str(HERE / f"{name}.scad")], check=True, capture_output=True)
    m = trimesh.load(stl, force="mesh")
    if name == "chain":
        m.apply_transform(chain_pose())
    return m


def main():
    import trimesh
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=float, default=0.25)
    ap.add_argument("--out", default=str(HERE / "parts"))
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args()
    out = Path(a.out)
    (out / "assembled").mkdir(parents=True, exist_ok=True)
    kid = Kid(a.step)
    t0 = time.time()
    stats = {}
    add, cut = joints()
    for name in ("base",) + SDF_PARTS + ("chain",):
        if a.only and name not in a.only:
            continue
        if name in ("base", "chain"):
            m = scad_part(name, out)
        else:
            if name.startswith("shoe"):
                g, d = kid.G["shoe"], kid.shoe(1 if name == "shoe_r" else -1)
            else:
                g = kid.G[name]
                d = getattr(kid, name)()
            m = sf.mesh(g, d)
            if name.startswith("shoe"):
                m.apply_translation([SHOE_X if name == "shoe_r" else -SHOE_X, 0, 0])
        M = sf.to_manifold(m)
        for j in add.get(name, []):
            M = M + j
        for j in cut.get(name, []):
            M = M - j
        m = sf.from_manifold(M)
        # a boolean can leave a zero-volume sliver as its own body: the gate counts it as floating
        bodies = m.split(only_watertight=False)
        if len(bodies) > 1:
            m = trimesh.util.concatenate([b for b in bodies if abs(b.volume) > 0.05])
        m.export(out / "assembled" / f"{name}.stl")
        p = m.copy()
        if name == "chain":
            p.apply_transform(np.linalg.inv(chain_pose()))
        else:
            p.apply_transform(print_pose(name))
        p.export(out / f"{name}.stl")
        stats[name] = {"colour": COLOURS[name], "mm3": round(float(m.volume), 1), "watertight": bool(m.is_watertight),
                       "bodies": len(m.split(only_watertight=False)),
                       "print_extent": [round(float(e), 1) for e in p.extents]}
        print(f"  {name}: {m.volume:.0f} mm3, watertight {m.is_watertight}, bodies {stats[name]['bodies']}, "
              f"as printed {p.extents.round(1)} mm ({time.time() - t0:.0f}s)")
    if not a.only or "pin" in a.only:
        pin = sf.from_manifold(pin_solid())
        pin.export(out / "pin.stl")
        stats["pin"] = {"colour": "black", "mm3": round(float(pin.volume), 1), "watertight": bool(pin.is_watertight),
                        "print_extent": [round(float(e), 1) for e in pin.extents]}
    (out / "build.json").write_text(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
