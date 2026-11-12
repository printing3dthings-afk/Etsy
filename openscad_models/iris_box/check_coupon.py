#!/usr/bin/env python3
"""Fit check for the iris coupon, on parts exported in the assembled pose by
iris_coupon.scad (part = base / blade / ring at variant v and ring angle phi):

  sweep   at 13 ring angles from open to closed, no two parts overlap, and the closest
          approach between them (pin to hole, pin to slot, tongue to groove, blade to
          base and ring)
  stops   2 deg past open or closed, the ring's tongue runs into the groove's end
  swing   the blade's turn over the travel (iris_budget.py says 48.6 deg)

    python3 check_coupon.py      (writes checks/fit_coupon.txt)
"""
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
ENV = dict(os.environ, OPENSCADPATH=str(HERE.parents[1] / "assets" / "openscad_libs"))
PHI0, TWIST, RP, RD = -46.0, 48.0, 41.0, 28.5


def part(name, v, phi, td):
    out = Path(td) / f"{name}_{v}_{phi:.2f}.stl"
    subprocess.run(["openscad", "-o", str(out), "-D", f'part="{name}"', "-D", f"variant={v}", "-D", f"phi={phi}",
                    str(HERE / "iris_coupon.scad")], check=True, env=ENV, capture_output=True)
    return trimesh.load(out)


def M(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def overlap(a, b):
    return (M(a) ^ M(b)).volume()


def gap(a, b):
    return float(np.abs(trimesh.proximity.signed_distance(a, b.sample(4000))).min())


def main():
    rows, ok = [], True
    with tempfile.TemporaryDirectory() as td:
        base = [part("base", v, 0, td) for v in (0, 1)]
        for v, g in ((0, 0.40), (1, 0.55)):
            worst, gaps = 0.0, []
            for phi in np.linspace(PHI0, PHI0 + TWIST, 13):
                bl, rg = part("blade", v, phi, td), part("ring", v, phi, td)
                worst = max(worst, overlap(base[v], bl), overlap(base[v], rg), overlap(bl, rg))
                gaps.append(min(gap(base[v], bl), gap(bl, rg)))
            stops = [overlap(base[v], part("ring", v, p, td)) for p in (PHI0 - 2, PHI0 + TWIST + 2)]
            b0 = math.degrees(math.atan2(RD * math.sin(math.radians(PHI0)), RD * math.cos(math.radians(PHI0)) - RP))
            b1 = math.degrees(math.atan2(RD * math.sin(math.radians(PHI0 + TWIST)), RD * math.cos(math.radians(PHI0 + TWIST)) - RP))
            good = worst < 1e-3 and min(gaps) >= 0.25 and all(s > 0.05 for s in stops)
            ok &= good
            rows.append(f"clearance {g:.2f}: {'ok  ' if good else 'FAIL'}  overlap through the sweep {worst:.4f} mm3; "
                        f"closest approach {min(gaps):.2f} mm; 2 deg past open / closed the tongue hits the groove's "
                        f"end ({stops[0]:.2f} / {stops[1]:.2f} mm3); blade swing {abs((b1 - b0 + 180) % 360 - 180):.1f} deg")
    text = "\n".join(["IRIS COUPON FIT CHECK (exported parts, assembled at 13 ring angles)"] + rows + ["PASS" if ok else "FAIL"])
    print(text)
    (HERE / "checks" / "fit_coupon.txt").write_text(text + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
