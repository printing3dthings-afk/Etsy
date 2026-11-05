#!/usr/bin/env python3
"""Do the five prints of Kawaii Cow v2 go together? (2026-11-05)

Each part is moved from its print pose to where it sits on her (the same
poses render_cow_v2.py uses), then:

  - each print is one closed body;
  - no two parts occupy the same space (the gaps are CLR and PEG_CLR, so
    any overlap is a modelling error, not a tight fit);
  - each joint is engaged: the neck peg sits inside the head, the heart's peg
    inside the heart, each ear's tab inside the head (measured as the part's
    volume inside the other's hull);
  - the gap round each peg, sampled on the peg's surface: about PEG_CLR.

    python3 check_fit_v2.py [parts_dir]
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "tools"))
import cow_v2 as c2  # noqa: E402
import render_cow_v2 as rc  # noqa: E402
import sdf_figure as sf  # noqa: E402

fails = []


def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'}  {text}")
    if not ok:
        fails.append(text)


def main():
    parts = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "parts"
    poses = rc.poses()
    mesh, M = {}, {}
    for name in c2.PARTS:
        m = trimesh.load(parts / f"{name}.stl", force="mesh")
        n = len(m.split(only_watertight=False))
        say(m.is_watertight and n == 1, f"{name}: one closed body ({n}), {m.volume:.0f} mm3, {m.extents.round(1)} mm as printed")
        m.apply_transform(poses[name])
        mesh[name], M[name] = m, sf.to_manifold(m)
    names = list(c2.PARTS)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = (M[a] ^ M[b]).volume()
            say(v < 0.5, f"{a} and {b} overlap {v:.2f} mm3")

    def inside(a, b):
        hull = sf.to_manifold(mesh[b].convex_hull)
        return (M[a] ^ hull).volume()

    # the neck peg: her body above NECK_Z within 4 mm of the peg's axis (the
    # collar also stands above NECK_Z, further out)
    cx, cy = c2.P(c2.NECK_CENTRE)[:2]
    zone = trimesh.creation.cylinder(radius=c2.NECK_PEG["r"] + 1.0, height=40)
    zone.apply_translation([cx, cy, c2.NECK_Z + 0.01 + 20])
    above = M["body"] ^ sf.to_manifold(zone)
    peg = above.volume()
    held = (above ^ sf.to_manifold(mesh["head"].convex_hull)).volume()
    say(peg > 50 and abs(held - peg) < 0.02 * peg,
        f"neck peg {peg:.0f} mm3 above her neck, {held:.0f} of it inside the head")
    # the heart has no peg: it sits in her lap's pocket against the wall
    # behind it. How much of its back is within reach of her (CLR plus a
    # little), and how much of its outline her arms and lap hold
    hb = mesh["heart"]
    pts, fi = trimesh.sample.sample_surface(hb, 20000, seed=2)
    back = hb.face_normals[fi][:, 1] > 0.9                       # its back faces +y, toward her
    _, dist, _ = trimesh.proximity.ProximityQuery(mesh["body"]).on_surface(pts[back])
    near = (dist < c2.CLR + 0.15).mean()
    say(near > 0.25, f"the heart's back rests on her: {100 * near:.0f}% of it within {c2.CLR + 0.15:.2f} mm of her")
    for ear in ("ear_r", "ear_l"):
        v = inside(ear, "head")
        say(v > 20, f"{ear}: {v:.0f} mm3 of its root inside the head")

    # the gap round the neck peg: from points on the peg's surface (above
    # the head's flat bottom) to the head
    pm = sf.from_manifold(above)
    pts, _ = trimesh.sample.sample_surface(pm, 4000, seed=1)
    pts = pts[pts[:, 2] > c2.NECK_Z + 0.5]
    q = trimesh.proximity.ProximityQuery(mesh["head"])
    _, dist, _ = q.on_surface(pts)
    say(np.percentile(dist, 5) > 0.08 and np.median(dist) < 0.35,
        f"neck peg gap: median {np.median(dist):.2f}, 5th pct {np.percentile(dist, 5):.2f} mm (PEG_CLR {c2.PEG_CLR})")
    # assembled height and footprint
    allm = trimesh.util.concatenate(list(mesh.values()))
    print(f"  assembled: {allm.extents.round(1)} mm (w x d x h)")
    print("\nCOW V2 FIT " + ("OK" if not fails else "FAILED:\n  " + "\n  ".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
