#!/usr/bin/env python3
"""Do the three prints of Teacup Bear v2 go together? (2026-11-05)

Each part is lifted from its print pose to where it sits (the cup stays, the
body stands on the tea, the head on her neck), then:

  - each print is one closed body;
  - no two parts occupy the same space (the gaps are CLR and PEG_CLR);
  - each peg sits wholly inside the part above it, with PEG_CLR round it;
  - her bottom and paws stand on the tea and rim (their faces within CLR
    plus a little of the cup's top).

    python3 check_fit_v2.py [parts_dir]
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "tools"))
import teacup_bear_v2 as b2  # noqa: E402
import sdf_figure as sf  # noqa: E402

LIFT = {"cup": 0.0, "body": b2.TEA_TOP, "head": b2.NECK_Z}
fails = []


def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'}  {text}")
    if not ok:
        fails.append(text)


def peg(M, mesh, p, z0, above):
    """The part of M within the peg's zone above z0, and how much of it the
    part `above` holds, and the gap round it."""
    zone = trimesh.creation.cylinder(radius=p["r"] + 1.0, height=40)
    zone.apply_translation([p["c"][0], p["c"][1], z0 + 0.01 + 20])
    piece = M ^ sf.to_manifold(zone)
    held = (piece ^ sf.to_manifold(mesh[above].convex_hull)).volume()
    pts, _ = trimesh.sample.sample_surface(sf.from_manifold(piece), 4000, seed=1)
    pts = pts[pts[:, 2] > z0 + 0.5]
    _, dist, _ = trimesh.proximity.ProximityQuery(mesh[above]).on_surface(pts)
    return piece.volume(), held, dist


def main():
    parts = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "parts"
    mesh, M = {}, {}
    for name in b2.PARTS:
        m = trimesh.load(parts / f"{name}.stl", force="mesh")
        n = len(m.split(only_watertight=False))
        say(m.is_watertight and n == 1, f"{name}: one closed body ({n}), {m.volume:.0f} mm3, {m.extents.round(1)} mm as printed")
        m.apply_translation([0, 0, LIFT[name]])
        mesh[name], M[name] = m, sf.to_manifold(m)
    names = list(b2.PARTS)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = (M[a] ^ M[b]).volume()
            say(v < 0.5, f"{a} and {b} overlap {v:.2f} mm3")
    for label, part, p, z0, above in (("neck peg", "body", b2.NECK_PEG, b2.NECK_Z, "head"),
                                      ("tea peg", "cup", b2.TEA_PEG, b2.TEA_TOP, "body")):
        vol, held, dist = peg(M[part], mesh, p, z0, above)
        say(vol > 50 and abs(held - vol) < 0.02 * vol, f"{label}: {vol:.0f} mm3 above its base, {held:.0f} of it inside the {above}")
        say(np.percentile(dist, 5) > 0.08 and np.median(dist) < 0.35,
            f"{label} gap: median {np.median(dist):.2f}, 5th pct {np.percentile(dist, 5):.2f} mm (PEG_CLR {b2.PEG_CLR})")
    # her underside on the cup's top: how much of the body's bottom face sits on the cup
    body = mesh["body"]
    pts, fi = trimesh.sample.sample_surface(body, 20000, seed=2)
    down = (body.face_normals[fi][:, 2] < -0.99) & (pts[:, 2] < b2.TEA_TOP + 0.05)
    _, dist, _ = trimesh.proximity.ProximityQuery(mesh["cup"]).on_surface(pts[down])
    near = (dist < b2.CLR + 0.15).mean()
    say(down.sum() > 100 and near > 0.9,
        f"her bottom and paws stand on the tea and rim: {100 * near:.0f}% of {down.sum()} samples within {b2.CLR + 0.15:.2f} mm of the cup")
    allm = trimesh.util.concatenate(list(mesh.values()))
    print(f"  assembled: {allm.extents.round(1)} mm (w x d x h)")
    print("\nTEACUP BEAR V2 FIT " + ("OK" if not fails else "FAILED:\n  " + "\n  ".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
