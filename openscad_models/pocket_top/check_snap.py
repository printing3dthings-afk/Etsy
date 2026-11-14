#!/usr/bin/env python3
"""Pocket Top snap test print: the fit, on the exported parts (2026-11-14).

For each pair (reach 0.35, 0.45, 0.55), the stem turned over and pushed home against the hub:
- the hub without its nubs touches nothing: the hex and the groove clear it;
- the nubs press into the groove's floor by the preload only (about 0.05 deep);
- the stem turned 10 deg hits the hub's hex: the hex drives the spin (with 0.15 a side it
  turns about 6.6 deg free first: its corners at r 2.89 meet the hole's faces at 2.65);
- the stem pulled 1.0 out by its grip hits the nubs: it's held; pushed further, the grip's
  shoulder stops it;
- the stem half in (its full hex at the nubs) bends each nub out by its reach: the
  overlap's depth is measured, so the nubs really are pushed over on the way in.

    python3 check_snap.py      (writes checks/fit_snap.txt)
"""
import subprocess
import tempfile
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
REACH = (0.35, 0.45, 0.55)
B, GRIP_H, NUB_H = 3.4, 2.4, 1.6
out, fails = [], []


def check(ok, msg):
    out.append(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)


def scad(body):
    with tempfile.TemporaryDirectory() as td:
        src, stl = Path(td) / "m.scad", Path(td) / "m.stl"
        src.write_text(f'include <{HERE / "snap_coupon.scad"}>\n{body}\n')
        subprocess.run(["openscad", "-o", str(stl), "-D", 'part="none"', str(src)], capture_output=True, timeout=600)
        return trimesh.load(stl)


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def ov(a, b):
    return (man(a) ^ man(b)).volume()


def depth_x(a, b):
    """the overlap's extent across the stem's axis, for one nub's region"""
    g = (man(a) ^ man(b)).to_mesh()
    return 0.0 if len(g.vert_properties) == 0 else float(np.ptp(g.vert_properties[:, 0]))


def moved(m, dz=0.0, deg=0.0):
    t = trimesh.transformations.rotation_matrix(np.radians(deg), [0, 0, 1])
    t[2, 3] = dz
    return m.copy().apply_transform(t)


def main():
    out.append("POCKET TOP SNAP TEST: FIT (exported geometry, each pair at the origin)")
    for i, reach in enumerate(REACH):
        hub = scad(f"hub({i});")
        body = scad(f"hub({i}, false);")
        nubs = scad(f"intersection() {{ hub({i}); linear_extrude({NUB_H}) for (k = [0 : 2]) rotate(120 * k) nub({i}); }}")
        nub0 = scad(f"intersection() {{ hub({i}); linear_extrude({NUB_H}) nub({i}); }}")
        stem = scad(f"translate([0, 0, {B + GRIP_H}]) mirror([0, 0, 1]) stem({i});")
        out.append(f"== pair {i + 1} (reach {reach})")
        check(ov(stem, body) < 0.01, f"seated, the hub's body clear: {ov(stem, body):.3f} mm3")
        pre = ov(stem, nubs)
        # the nub's flat tip on the groove's round floor: 0.05 deep at its middle, about none
        # at its edges, so less than the full 0.05 x 1.4 x NUB_H x 3 (0.34)
        check(0.05 < pre < 0.34, f"seated, the nubs press the groove's floor by the preload: {pre:.2f} mm3 "
                                 f"(0.05 deep at each nub's middle)")
        free = ov(moved(stem, deg=6), body)
        drive = ov(moved(stem, deg=10), body)
        check(free < 0.01 and drive > 0.05, f"turned 6 deg it is still free ({free:.2f} mm3); turned 10 deg the hex "
                                            f"bears on the hub: {drive:.2f} mm3 (it drives)")
        pull = ov(moved(stem, dz=+1.0), nubs)
        check(pull > pre + 0.5, f"pulled 1.0 out by its grip, it hits the nubs: {pull:.2f} mm3 (held)")
        push = ov(moved(stem, dz=-0.1), body)
        check(push > 0.5, f"pushed 0.1 further, the grip's shoulder meets the hub: {push:.2f} mm3 (it stops)")
        half = moved(stem, dz=+3.0)                # half out: the full hex where the nubs are
        dx = depth_x(half, nub0)
        check(abs(dx - reach) < 0.06, f"on the way in, the hex bends each nub out by {dx:.2f} (reach {reach})")
    out.append("PASS" if not fails else "FAIL: " + "; ".join(fails))
    text = "\n".join(out)
    print(text)
    (HERE / "checks" / "fit_snap.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
