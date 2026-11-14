#!/usr/bin/env python3
"""Does a part fit the US small-parts test cylinder? (2026-11-14, Pocket Top.)

The cylinder is 16 CFR 1501.4, Figure 1 (read from the figure itself, 2026-11-14, via the
Cornell LII reproduction of the CFR, law.cornell.edu/cfr/text/16/1501.4):
  inside diameter 1.25 in (31.7 mm); depth 1.00 in (25.4 mm) on one side and 2.25 in
  (57.1 mm) on the other, the bottom a plane slanting between them.
The test (1501.4(b)(1)): "Place the article, without compressing it, into the cylinder. If
the article fits entirely within the cylinder, in any orientation, it fails." Detached
components are tested the same way. The rule covers articles for children under 3
(1501.2(a)). A part too big for the cylinder still has to survive the use-and-abuse tests of
16 CFR 1500.51-52 first (1501.4(b)(2)); this tool can't do that part.

This is a geometric search, not a certification. It tries a few thousand orientations of
the part's convex hull; for each, the smallest circle round its outline must fit the bore,
and the part, pushed as deep as the slanted floor lets it, must sit wholly below the rim.
If any orientation fits, the part is a small part. A part this finds "too big" by a margin
of a millimetre or two should still be treated as borderline.

    python3 tools/small_parts.py part.stl [more.stl ...]
"""
import argparse
import sys

import numpy as np
import shapely
import trimesh
from shapely.geometry import MultiPoint

R = 31.7 / 2
SHALLOW, DEEP = 25.4, 57.1


def _rotations(n, seed=1):
    """n rotations spread over SO(3) (random unit quaternions), plus the 24 axis-aligned ones."""
    rng = np.random.default_rng(seed)
    q = rng.normal(size=(n, 4))
    q /= np.linalg.norm(q, axis=1)[:, None]
    mats = [trimesh.transformations.quaternion_matrix(v)[:3, :3] for v in q]
    for ax in np.eye(3):
        for k in range(4):
            for up in (1, -1):
                m = trimesh.transformations.rotation_matrix(k * np.pi / 2, ax)[:3, :3]
                if up < 0:
                    m = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])[:3, :3] @ m
                mats.append(m)
    return mats


def fit(points, n=3000):
    """(fits, depth, bore): depth is how far below the rim the part's top sits in the best
    orientation that passes the bore (negative: it sticks out; None if none passes the bore);
    bore is the best bore slack found (negative: never passes)."""
    best_depth, best_bore = None, -1e9
    for M in _rotations(n):
        p = points @ M.T
        mp = MultiPoint(p[:, :2])
        slack = R - shapely.minimum_bounding_radius(mp)
        best_bore = max(best_bore, slack)
        if slack < 0:
            continue
        q = p.copy()
        q[:, :2] -= np.array(shapely.minimum_bounding_circle(mp).centroid.coords[0])
        q[:, 0] += slack                        # the floor deepens toward +x: go that way
        floor = SHALLOW + (q[:, 0] + R) / (2 * R) * (DEEP - SHALLOW)
        # the part's top at depth t below the rim puts each point at t + (top - z) down;
        # the deepest t with every point above the floor:
        t = np.min(floor - (q[:, 2].max() - q[:, 2]))
        best_depth = t if best_depth is None else max(best_depth, t)
    return (best_depth is not None and best_depth >= 0), best_depth, best_bore


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("parts", nargs="+")
    ap.add_argument("-n", type=int, default=3000, help="orientations to try")
    a = ap.parse_args()
    any_small = False
    for path in a.parts:
        m = trimesh.load(path, force="mesh")
        for i, body in enumerate(m.split(only_watertight=False) if m.body_count > 1 else [m]):
            pts = body.convex_hull.vertices
            ok, depth, bore = fit(pts, a.n)
            name = path if m.body_count == 1 else f"{path} body {i + 1}"
            if ok:
                any_small = True
                print(f"SMALL PART  {name}: fits the cylinder, its top {depth:.1f} mm below the rim")
            elif depth is None:
                print(f"too big     {name}: never fits the 31.7 mm bore (by {-bore:.1f} mm at best)")
            else:
                print(f"too big     {name}: fits the bore but sticks {-depth:.1f} mm above the rim at best")
    print("16 CFR 1501.4 cylinder (31.7 mm bore, 25.4-57.1 mm slanted floor); geometric search, not a certification.")
    return 1 if any_small else 0


if __name__ == "__main__":
    sys.exit(main())
