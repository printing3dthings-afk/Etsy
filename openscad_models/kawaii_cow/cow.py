"""Kawaii Cow: a chubby desk-buddy cow hugging a heart (2026-11-04).

Scott picked idea 1 of five (a sitting figurine built with the smooth-min
method from reports/Better 3D character design.md) and "Cow".

She sits like a plush toy: legs out front in a V, a pink heart standing in
her lap on its tip, her front hooves wrapped round it and her chin resting on
its lobes. The pose is the support plan: her muzzle sits on the heart, the
heart stands on the plate between her legs, and every part that would hang
(head, ears, arms) has something under it within the 37 deg the slicer
accepts. tools/sdf_figure.self_support() grows the rest down as smooth cones.

Everything is a distance field joined with smooth-min, so the head flows into
the body like clay; no union() creases. Design units are mm at S = 1; S scales
the whole figure (S = 1.2 makes her about 66 mm tall).

    python3 cow.py            build parts/*.stl
    python3 cow.py --step 0.4 a quick draft
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

S = 1.2          # scale: design mm -> print mm
# steepest overhang grown, from upright. DETAIL_STANDARD rule 7 says design to
# about 37; at 37 the cones' voxel and facet noise still let the slicer (45)
# prop the nostrils and the heart's tip, so 33 leaves margin
ANGLE = 33.0
SHELL = 1.2      # colour skin depth: three beads

# ---------- skeleton (design mm; front is -y, up is +z) ----------
BELLY = ((0, 1, 15), (16, 14.5, 15.5))
SQUISH = ((0, 2, 0), (18.5, 16.5, 8))          # her bottom spread on the plate
CHEST = ((0, -0.5, 26), (12, 10.5, 8.5))
HIP, ANKLE = (8.5, -3, 4.4), (11, -19, 4.4)     # legs out front in a V
LEG_R = (6.8, 5.6)
FOOT = ((11.5, -21.5, 4.6), (5.8, 4.2, 7.2), 10)   # centre, radii, toes-out yaw
HOOF_SOLE = 1.8                                  # black pad on each foot's sole
PAD = 0.72                                       # the pad's size within the sole: a white rim round it
CLEFT = (0.8, 0.7)                               # the hoof's split: groove width, depth
HEART_TIP, HEART_W, HEART_HALF, HEART_ROUND = (0, -23, -1.2), 24, 4.4, 3.2
# arms rest along the tops of her legs, elbows on her knees, hooves on the
# heart's sides
SHOULDER, ELBOW, HAND, ARM_R = (12.5, -4, 20), (12.6, -14, 13.0), (12.2, -24.4, 12.6), (4.2, 3.7)
HOOF_ARM = 2.0                                   # black cap on the end of each arm
# the head group, tilted TILT deg about PIVOT (a head tilt, so she isn't twinned)
TILT, PIVOT = 7.0, (0, -6, 26)
HEAD = ((0, -3, 35), (17, 13.5, 13))
MUZZLE = ((0, -14, 27.0), (10.5, 6.5, 7.3))
EYE = ((6.6, -14.9, 36.6), (2.3, 1.7, 3.1))     # x mirrored
SHINE = ((7.4, -16.3, 37.9), 0.9)
NOSTRIL = ((3.6, -20.6, 28.0), (1.3, 1.9, 1.7))
BLUSH = ((12.4, -10.6, 32.8), 2.4)
HORN = ((8.4, -3.5, 45), (10.2, -2.8, 52.2), (2.7, 1.5))
HORN_TIP = 2.2                                   # black tip on each white horn: it defines them
# along, half-thickness (y), wide. A leaf of even thickness with a round rim:
# as a squashed ellipsoid it thinned to a knife edge round its rim. The ears
# point UP and out, 50 deg above level: hanging down, each ear's tip was its
# lowest point, printed first in mid-air, and the slicer propped both from the
# plate (2026-11-04). A thin leaf can't be held up by a cone either: eroded
# from both faces, it is gone 2 mm down.
# Rooted 1 mm inside the head and tilted 55 deg, so the leaf's lowest point
# (an ellipse's, which sits beside its root, not at it) is inside the head:
# at 50 deg it stood 2 mm proud and the slicer propped it from the plate.
EAR_ROOT, EAR_DROOP, EAR = (13.6, 0.5, 38.6), -55, (6.4, 1.1, 3.6)
# a soft pad between the heart and her belly: the muzzle rests on it, and the
# cone under her chin could not bridge the 5 mm gap that was there
PAD_BEHIND = ((0, -15.5, 14.5), (8.5, 4.5, 9.0))
# a low cushion between her feet that the heart's tip rests in: the V-shaped
# crevice there, between the tip and her right foot, closed over 0.8 mm up
# and the slicer propped it from the plate (2026-11-04)
LAP = ((0, -21.5, 0), (9.5, 6.5, 3.6))
TAIL = [((4, 13.5, 1.3), (10, 17.5, 1.3)), ((10, 17.5, 1.3), (14.5, 15.5, 1.3))]
TAIL_R, TUFT = 2.0, ((15.8, 13.8, 2.2), (3.0, 2.6, 3.4))
SPOTS = [  # black patches: blobs of spheres (head-frame ones marked "head")
    ("body", [((-9, 10, 20), 7.0), ((-13.5, 4, 24), 4.5), ((-5, 13, 12), 5.0)]),
    ("body", [((14, 4, 10), 5.5), ((12, 10.5, 5), 4.5), ((15.5, -1, 14), 3.2)]),
    ("body", [((10.5, -11, 9.5), 3.6), ((12.5, -7.5, 10.5), 3.0)]),
    ("head", [((-10, -1, 44), 5.5), ((-13.5, 3, 40), 4.5), ((-6, 4, 47.5), 3.5)]),
]

# ---------- helpers in design units ----------


def P(v):
    return np.asarray(v, np.float32) * S


def tilt():
    return sf.rot("y", TILT)


def head_pt(c):
    """A head-group point, carried by the tilt."""
    piv = np.asarray(PIVOT, np.float32)
    return piv + tilt() @ (np.asarray(c, np.float32) - piv)


def mirror_pair(c):
    c = np.asarray(c, np.float32)
    return [c, c * np.array([-1, 1, 1], np.float32)]


class Cow:
    def __init__(self, step):
        lo = np.array([-34, -34, -1.5]) * S
        hi = np.array([34, 25, 57]) * S
        self.g = sf.Grid(lo, hi, step)

    # primitives in design units
    def ell(self, c, r, R=None):
        return sf.ellipsoid(self.g, P(c), P(r), R)

    def ball(self, c, r):
        return self.ell(c, (r, r, r))

    def stick(self, a, b, ra, rb):
        return sf.stick(self.g, P(a), P(b), ra * S, rb * S)

    def head_ell(self, c, r, R=None):
        Rt = tilt() if R is None else tilt() @ R
        return self.ell(head_pt(c), r, Rt)

    def ear(self, side):
        """A leaf-shaped ear at the head's side, EAR_DROOP deg below level (negative: up)."""
        root = np.asarray(EAR_ROOT, np.float32) * np.array([side, 1, 1], np.float32)
        # the angle is set in the world, not the head's frame: carried by the
        # head tilt, one ear stood at 48 deg and the other at 62
        Rw = sf.rot("y", EAR_DROOP if side > 0 else 180 - EAR_DROOP) @ sf.rot("x", 180 if side < 0 else 0)
        R = tilt().T @ Rw
        along = R @ np.array([1, 0, 0], np.float32)
        c = root + along * EAR[0] * 0.85
        _, y, _ = self.g.local(P(head_pt(c)), Rw)
        # the leaf stands upright, in the world's x-z plane: draw its outline
        # there, make that outline self-supporting in its own plane, then
        # give it thickness (y) with a round rim
        g = self.g
        cw = P(head_pt(c))
        a, b = EAR[0] * S, EAR[2] * S
        ax_u = Rw @ np.array([1, 0, 0], np.float32)       # along, in x-z
        ax_w = Rw @ np.array([0, 0, 1], np.float32)       # wide, in x-z

        def leaf(U, V):
            du, dv = U - cw[0], V - cw[2]
            p = du * ax_u[0] + dv * ax_u[2]
            q = du * ax_w[0] + dv * ax_w[2]
            return (p / a) ** 2 + (q / b) ** 2 - 1.0

        xs, zs = g.axes[0], g.axes[2]
        ref = 4
        FX, FZ = np.meshgrid(*sf.fine_axes(xs, zs, ref), indexing="ij")
        held = sf.support_rows(leaf(FX, FZ) < 0, g.step / ref, g.step / ref, ANGLE)
        d2 = sf.exact2d(None, xs, zs, refine=ref, inside=held)
        d2 = np.broadcast_to(d2[:, None, :], g.X.shape)
        return sf.puffy(d2, y, EAR[1] * S, EAR[1] * S), (c, R)

    def inner_ear(self, c, R):
        """The pink inside of an ear: a smaller leaf on its front face."""
        return self.head_ell(c + R @ np.array([0.5, -EAR[1] * 0.75, 0], np.float32),
                             (EAR[0] * 0.7, EAR[1], EAR[2] * 0.62), R)

    def heart(self):
        g = self.g
        tip = P(HEART_TIP)
        xs, zs = g.axes[0], g.axes[2]
        d2 = sf.exact2d(lambda u, v: sf.heart2d(u - tip[0], v - tip[2], HEART_W * S, notch_k=5 * S)[0], xs, zs)
        d2 = np.broadcast_to(d2[:, None, :], g.X.shape)
        depth = g.Y - tip[1]
        # a pillow, not a slab: the face domes 1 mm towards the middle
        dome = 1.0 * S * np.clip(-d2 / (7 * S), 0, 1)
        return sf.puffy(d2, depth, HEART_HALF * S, HEART_ROUND * S) - dome

    # ---------- the figure ----------
    def build(self):
        t0 = time.time()
        body = sf.smin(self.ell(*BELLY), self.ell(*SQUISH), 6 * S)
        body = sf.smin(body, self.ell(*CHEST), 6 * S)
        for s in (1, -1):
            m = np.array([s, 1, 1], np.float32)
            leg = self.stick(np.asarray(HIP) * m, np.asarray(ANKLE) * m, *LEG_R)
            foot = self.ell(np.asarray(FOOT[0]) * m, FOOT[1], sf.rot("z", -FOOT[2] * s))
            leg = sf.smin(leg, foot, 3 * S)
            body = sf.smin(body, leg, 5 * S)
            sh, el, ha = (np.asarray(p) * m for p in (SHOULDER, ELBOW, HAND))
            r_el = (ARM_R[0] + ARM_R[1]) / 2
            arm = sf.smin(self.stick(sh, el, ARM_R[0], r_el), self.stick(el, ha, r_el, ARM_R[1]), 1.5 * S)
            body = sf.smin(body, arm, 3.0 * S)
        tail = np.minimum(self.stick(*TAIL[0], TAIL_R, TAIL_R), self.stick(*TAIL[1], TAIL_R, TAIL_R))
        tail = sf.smin(tail, self.ell(*TUFT), 1.5 * S)
        body = sf.smin(body, tail, 2.5 * S)

        head = self.head_ell(*HEAD)
        head = sf.smin(head, self.head_ell(*MUZZLE), 3 * S)
        for s in (1, -1):
            m = np.array([s, 1, 1], np.float32)
            a, b = np.asarray(HORN[0]) * m, np.asarray(HORN[1]) * m
            head = sf.smin(head, self.stick(head_pt(a), head_pt(b), *HORN[2]), 1.5 * S)
            ear, _ = self.ear(s)
            head = sf.smin(head, ear, 2.0 * S)
            head = sf.smin(head, self.head_ell(np.asarray(EYE[0]) * m, EYE[1]), 0.6 * S)
            head = sf.smax(head, -self.head_ell(np.asarray(NOSTRIL[0]) * m, NOSTRIL[1]), 0.5 * S)
        body = sf.smin(body, self.ell(*PAD_BEHIND), 4 * S)
        d = sf.smin(body, head, 7 * S)
        # the heart joins last, with a small fillet: inside the head-to-body
        # blend its join with the muzzle grew a 2 mm white web
        heart = self.heart()
        d = sf.smin(d, self.ell(*LAP), 2.5 * S)
        d = sf.smin(d, heart, 2.5 * S)
        for s in (1, -1):
            m = np.array([s, 1, 1], np.float32)
            c, r = np.asarray(FOOT[0]) * m, FOOT[1]
            Rf = sf.rot("z", -FOOT[2] * s)
            x, y, z = self.g.local(P(c), Rf)
            groove = np.maximum(np.abs(x) - CLEFT[0] / 2 * S, np.abs(z) - r[2] * PAD * 0.8 * S)
            # only the front CLEFT[1] of the sole: inverted, this cut a slot
            # through the whole leg and body (2026-11-04)
            groove = np.maximum(groove, y + (r[1] - CLEFT[1]) * S)
            d = np.maximum(d, -groove)
        d = sf.cut_base(self.g, d)
        self.raw = d
        print(f"  field {d.shape} in {time.time() - t0:.1f}s")
        t0 = time.time()
        self.d, added = sf.self_support(self.g, d, ANGLE)
        self.d = sf.cut_base(self.g, self.d)   # the cones also ran on below the plate
        self.d = sf.base_prism(self.g, self.d, 0.8)
        print(f"  self-support grew {added:.0f} mm3 in {time.time() - t0:.1f}s")
        self.heart_field = heart
        return self.d

    # ---------- colour regions (fields, inside negative) ----------
    def regions(self):
        g, d = self.g, self.d
        skin = -(d + SHELL * S)                     # inside the outer SHELL mm
        reg = {}
        black = []
        for kind, blobs in SPOTS:
            f = None
            for c, r in blobs:
                e = self.head_ell(c, (r, r, r)) if kind == "head" else self.ball(c, r)
                f = e if f is None else sf.smin(f, e, 2 * S)
            black.append(f)
        # her left ear is black, its inner ear still pink
        ear_l, (cl, Rl) = self.ear(-1)
        black.append(np.maximum(ear_l - 0.1 * S, -self.inner_ear(cl, Rl)))
        for s in (1, -1):
            m = np.array([s, 1, 1], np.float32)
            eye = self.head_ell(np.asarray(EYE[0]) * m, EYE[1]) - 0.15 * S
            shine = self.head_ell(np.asarray(SHINE[0]) * m, (SHINE[1],) * 3)
            black.append(np.maximum(eye, -shine))
            # hoof soles: the front HOOF_SOLE of each foot
            c, r = np.asarray(FOOT[0]) * m, FOOT[1]
            Rf = sf.rot("z", -FOOT[2] * s)
            x, y, z = g.local(P(c), Rf)
            pad = self.ell(c, np.asarray(r) * np.array([PAD, 2.0, PAD]), Rf)
            black.append(np.maximum(pad, y + (r[1] - HOOF_SOLE) * S))
            # arm hooves: the hand end of each arm
            a, b = np.asarray(ELBOW) * m, np.asarray(HAND) * m
            ax = (b - a) / np.linalg.norm(b - a)
            cap = self.ball(b, ARM_R[1] + 0.6)
            plane = (g.X - P(b)[0]) * ax[0] + (g.Y - P(b)[1]) * ax[1] + (g.Z - P(b)[2]) * ax[2] - (ARM_R[1] - HOOF_ARM) * S
            black.append(np.maximum(cap, -plane))
        black.append(self.ell(*TUFT) - 0.2 * S)
        for m in (np.array([1, 1, 1], np.float32), np.array([-1, 1, 1], np.float32)):
            a, b = head_pt(np.asarray(HORN[0]) * m), head_pt(np.asarray(HORN[1]) * m)
            ax = (b - a) / np.linalg.norm(b - a)
            beyond = (g.X - P(b)[0]) * ax[0] + (g.Y - P(b)[1]) * ax[1] + (g.Z - P(b)[2]) * ax[2] + (HORN_TIP - HORN[2][1]) * S
            horn_tips = np.maximum(self.stick(a, b, HORN[2][0] + 0.3, HORN[2][1] + 0.3), -beyond)
            black.append(horn_tips)
        # the horns stay white where a spot reaches them (all but their tips)
        horns = np.minimum.reduce([self.stick(head_pt(np.asarray(HORN[0]) * m), head_pt(np.asarray(HORN[1]) * m),
                                              HORN[2][0] + 0.3, HORN[2][1] + 0.3)
                                   for m in (np.array([1, 1, 1], np.float32), np.array([-1, 1, 1], np.float32))])
        spots_only = np.maximum(np.minimum.reduce(black[:-2]), -horns)
        reg["black"] = np.maximum(np.minimum(spots_only, np.minimum(black[-2], black[-1])), skin)

        reg["red"] = np.maximum(self.heart_field - 0.15 * S, skin)
        pink = [self.head_ell(*MUZZLE) - 0.3 * S]
        for s in (1, -1):
            m = np.array([s, 1, 1], np.float32)
            pink.append(self.head_ell(np.asarray(BLUSH[0]) * m, (BLUSH[1],) * 3))
            _, (c, R) = self.ear(s)
            pink.append(self.inner_ear(c, R))
        reg["pink"] = np.maximum(np.minimum.reduce(pink), skin)

        return reg


# Four AMS slots. The heart is red, not pink: in pink it ran into the pink
# muzzle resting on it and the two read as one blob; so the horns, which
# were a fifth colour (cream), are white like her (2026-11-04).
COLOURS = {"white": "#F4F1EA", "black": "#2B2433", "pink": "#F6A6C1", "red": "#D7263D"}
# which region wins where two overlap: eyes and hooves over the heart and pink
PRIORITY = ["black", "red", "pink"]
MARK_AT = (0, 2.5)          # the OBC mark's centre under her (design mm), clear of the heart's tip and the tail
FAST = "/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun"


def mark_meshes(out):
    """The OBC inlay and its cut, from mark.scad (OpenSCAD with the manifold backend)."""
    import os
    import shutil
    import subprocess
    import trimesh
    exe = os.environ.get("OPENSCAD_FAST", FAST)
    if not Path(exe).exists():
        exe = shutil.which("openscad")
    env = dict(os.environ, OPENSCADPATH=str(HERE.parents[1] / "assets" / "openscad_libs"))
    meshes = {}
    for part in ("inlay", "cut"):
        f = out / f"_mark_{part}.stl"
        subprocess.run([exe, "--backend=manifold", "-D", f'part="{part}"', "-o", str(f), str(HERE / "mark.scad")],
                       check=True, capture_output=True, env=env)
        m = trimesh.load(f, force="mesh")
        f.unlink()
        m.apply_translation([MARK_AT[0] * S, MARK_AT[1] * S, 0])
        meshes[part] = sf.to_manifold(m)
    return meshes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=float, default=0.25)
    ap.add_argument("--out", default=str(HERE / "parts"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    cow = Cow(a.step)
    d = cow.build()
    import trimesh
    t0 = time.time()
    whole = sf.mesh(cow.g, d)
    print(f"  mesh {len(whole.faces)} faces, watertight {whole.is_watertight}, "
          f"{whole.extents.round(1)} mm, {whole.volume:.0f} mm3 in {time.time() - t0:.1f}s")
    M = sf.to_manifold(whole)
    regs = cow.regions()
    taken = None
    parts = {}
    for name in PRIORITY:
        V = sf.to_manifold(sf.mesh(cow.g, regs[name]))
        part = M ^ V
        if taken is not None:
            part = part - taken
        taken = V if taken is None else taken + V
        parts[name] = part
    parts["white"] = M - taken
    # the maker's mark, inlaid in black in her base
    mk = mark_meshes(out)
    for name in parts:
        parts[name] = parts[name] - mk["cut"]
    parts["black"] = parts["black"] + mk["inlay"]
    whole = sf.from_manifold(M - mk["cut"] + mk["inlay"])
    stats = {}
    for name, part in parts.items():
        m = sf.from_manifold(part)
        # booleans leave zero-volume sheets where two colours' faces coincide
        keep = [b for b in m.split(only_watertight=False) if abs(b.volume) > 0.05]
        m = trimesh.util.concatenate(keep)
        m.export(out / f"cow_{name}.stl")
        stats[name] = round(float(m.volume), 1)
        print(f"  {name}: {m.volume:.0f} mm3, {len(m.split(only_watertight=False))} bodies")
    whole.export(out / "cow.stl")
    area, _ = sf.overhang_report(whole, 40)
    stats["overhang_over_40_mm2"] = round(area, 1)
    print(f"  faces past 40 deg off the plate: {area:.1f} mm2")
    (out / "build.json").write_text(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
