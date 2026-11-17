"""Urban Kid v2: the hoodie, v1's shape with sculpted folds (2026-11-17).

v1's hoodie (kid.py) has the shape, pocket, collar roll, cords and seams but
reads stiff: cloth with no folds. These are the folds a figure sculptor puts on
a hoodie worn with the hands in the pocket (folds.py has the why):

  elbows    compression folds stacked inside each bend, curling round the arm
  forearms  the sleeve bunched above the cuff
  front     tension folds from each shoulder down to the pocket's corners,
            where the hands drag the front down
  armpits   short folds from under the arm forward onto the chest
  hem       gathers above the ribbed band, all round but the pocket
  back      long folds hanging from under the hood to the hem
  hood      creases in the rolled-down hood

All in v1's design frame (mm, front -y, up +z); hoodie_field() builds on any
grid, so the same folds come out at 190 mm on a DesignGrid.

    python3 hoodie_v2.py OUT.stl [--step 0.25]
"""
import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import sdf_figure as sf  # noqa: E402
import kid  # noqa: E402
from folds import fold, on_surface, stroke  # noqa: E402

ARM = {"sh": (16.6, 1.0, 60.0), "el": (17.4, 2.6, 50.6), "ha": (9.4, -5.6, 47.8)}
rng = np.random.default_rng(7)


def v1_hoodie(g):
    """v1's hoodie field as drawn, before it's made printable."""
    keep = kid.support_up, kid.trim_up, kid.foot
    kid.support_up = lambda g_, d: (d, 0.0)
    kid.trim_up = lambda g_, d, **k: (d, 0.0)
    kid.foot = lambda g_, d, z0, **k: d
    try:
        k = kid.Kid(0.5)
        k.G["hoodie"] = g
        return k.hoodie()
    finally:
        kid.support_up, kid.trim_up, kid.foot = keep


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def arc(c, axis, ref, radius, a0, a1, n=9, tilt=0.0, along=None):
    """Points on a circle round axis through c, from angle a0 to a1 (deg) about
    ref (the angle-0 direction); tilt leans the circle's plane (a spiral fold)."""
    axis, ref = unit(axis), unit(ref)
    ref = unit(ref - axis * (ref @ axis))
    other = np.cross(axis, ref)
    pts = []
    for a in np.radians(np.linspace(a0, a1, n)):
        u = np.cos(a) * ref + np.sin(a) * other
        pts.append(c + radius * u + axis * np.tan(np.radians(tilt)) * radius * np.sin(a))
    return np.array(pts), [unit(np.cos(a) * ref + np.sin(a) * other) for a in np.radians(np.linspace(a0, a1, n))]


def elbow_folds(g, d, s):
    sh, el, ha = (np.array([s * ARM[k][0], ARM[k][1], ARM[k][2]]) for k in ("sh", "el", "ha"))
    up, fore = unit(sh - el), unit(ha - el)
    inner = unit(up + fore)                       # the inside of the bend
    # compression folds: arcs on the inside of the bend, alternating tilt, the
    # middle ones deepest; on the forearm first then the upper arm
    for k, (t, axis, tilt, h) in enumerate(((1.0, fore, 18, 0.55), (2.6, fore, -14, 0.5), (4.2, fore, 20, 0.4),
                                            (1.2, up, -16, 0.5), (2.8, up, 14, 0.4))):
        c = el + axis * t
        pts, outs = arc(c, axis, inner, 4.2, -80 + 10 * k % 30, 80, n=11, tilt=tilt * s)
        d = fold(g, d, pts, 0.9, h, np.array(outs))
    # the forearm bunched above the cuff: two near-rings, the far side shallower
    for t, tilt in ((0.52, 10), (0.62, -12)):
        c = el + (ha - el) * t
        pts, outs = arc(c, fore, inner, 4.0, -150, 150, n=17, tilt=tilt * s)
        d = fold(g, d, pts, 0.75, 0.42, np.array(outs))
    # the outside of the elbow stretched: one long soft fold along it
    out_dir = unit(-inner)
    a = el + up * 3.5 + out_dir * 4.2
    b = el + fore * 3.0 + out_dir * 4.0
    d = fold(g, d, [a, el + out_dir * 4.4, b], 1.2, 0.3, out_dir, ridge=False)
    return d


def front_folds(g, d, s):
    fwd = np.array([0.0, -1.0, 0.0])
    # tension folds, shoulder to the pocket's top corner, two per side
    for x0, z0, x1, z1, h in ((12.8, 60.0, 8.6, 50.6, 0.55), (15.0, 56.5, 11.0, 50.0, 0.45)):
        path = [np.array([s * (x0 + (x1 - x0) * t), -9.0, z0 + (z1 - z0) * t]) for t in np.linspace(0, 1, 7)]
        d = fold(g, d, path, 1.0, h, fwd)
    # armpit folds: from under the arm forward onto the chest
    for z, dz in ((54.5, -1.2), (52.4, -0.8)):
        path = [np.array([s * x, -6.0 - 3.0 * (15.5 - x) / 4.0, z + dz * (15.5 - x) / 4.0])
                for x in np.linspace(15.5, 11.5, 5)]
        outs = [unit([s * 0.6, -1.0, 0.0])] * len(path)
        d = fold(g, d, path, 0.8, 0.4, np.array(outs))
    # the pocket: short pulls from each opening in toward the middle
    for z in (47.6, 45.9):
        path = [np.array([s * x, -9.9, z - 0.3 * (9.0 - x)]) for x in np.linspace(9.0, 5.0, 5)]
        d = fold(g, d, path, 0.6, 0.25, fwd, ridge=False)
    return d


def hem_gathers(g, d):
    """Short upright folds above the ribbed band all round, uneven in spacing
    and depth, none on the pocket (it lies flat over the hands)."""
    z0, z1 = kid.Z_WAIST + 3.6, kid.Z_WAIST + 8.0
    for th in np.radians(np.arange(0, 360, 17) + rng.uniform(-5, 5, len(np.arange(0, 360, 17)))):
        x, y = 16.0 * np.cos(th), 0.8 + 11.8 * np.sin(th)
        if y < -4.0 and abs(x) < 12.5:
            continue
        out = unit([np.cos(th), np.sin(th) * 0.7, 0.0])
        top = z0 + rng.uniform(2.8, 4.4)
        path = [np.array([x, y, z]) for z in np.linspace(z0 - 0.2, top, 5)]
        d = fold(g, d, path, 0.75, rng.uniform(0.32, 0.5), out, gap=1.0)
    return d


def back_folds(g, d):
    back = np.array([0.0, 1.0, 0.0])
    for x, wob, h in ((-7.0, 0.8, 0.5), (0.8, -0.6, 0.45), (7.5, 0.7, 0.5)):
        path = [np.array([x + wob * np.sin(t * 3.0), 12.0, 62.0 - 17.0 * t]) for t in np.linspace(0, 1, 8)]
        d = fold(g, d, path, 1.3, h, back)
    # the hood: two creases in its rolled mass, and one in the roll at each side
    for x in (-4.5, 3.5):
        path = [np.array([x + 1.2 * t, 15.0, 70.5 - 4.0 * t]) for t in np.linspace(0, 1, 5)]
        d = fold(g, d, path, 0.8, 0.45, back)
    return d


def hoodie_field(g):
    d = v1_hoodie(g)
    for s in (1, -1):
        d = elbow_folds(g, d, s)
        d = front_folds(g, d, s)
    d = hem_gathers(g, d)
    d = back_folds(g, d)
    d = np.maximum(d, kid.Z_WAIST - g.Z)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--step", type=float, default=0.25)
    a = ap.parse_args()
    g = sf.Grid(np.array([-26.5, -17.5, kid.Z_WAIST - 1.0]), np.array([26.5, 17.0, 74.0]), a.step)
    d = hoodie_field(g)
    m = sf.mesh(g, d)
    m = max(m.split(only_watertight=False), key=lambda b: abs(b.volume))
    m.export(a.out)
    print("hoodie", round(m.volume), "mm3, watertight", m.is_watertight)


if __name__ == "__main__":
    main()
