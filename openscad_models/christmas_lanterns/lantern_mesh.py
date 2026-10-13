#!/usr/bin/env python3
"""Mesh steps the lanterns need that OpenSCAD 2021 does badly (2026-10-13).

    lantern_mesh.py check part.stl ...              each part closed; every pair disjoint
    lantern_mesh.py union out.stl part.stl ...      one body, for product_gate
    lantern_mesh.py wrap flat.stl out.stl --radius R --z Z [--minus m.stl ...]

check and union use manifold3d. CGAL took 3.5 hours to union Santa's
workshop's four parts and would not union imported STLs at all; manifold
does both in seconds and refuses an open mesh rather than guessing.

wrap bends a relief built flat (x along a face, y up, z out of it) round a
cylinder: x becomes the angle x / radius, y height above --z, z the distance
out from --radius. The flat mesh is subdivided first so its long triangles
follow the curve, and anything named by --minus is cut from the result, so a
relief wrapped a hair into its glass comes out touching it, not inside it.
"""
import argparse, itertools, math, sys
import numpy as np
import trimesh
import manifold3d as mf


def to_manifold(m: trimesh.Trimesh, name: str) -> mf.Manifold:
    out = mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                              tri_verts=np.asarray(m.faces, np.uint32)))
    if out.status() != mf.Error.NoError:
        sys.exit(f"{name}: manifold3d refuses it ({out.status()}) -- not a closed mesh")
    return out


def to_trimesh(m: mf.Manifold) -> trimesh.Trimesh:
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)


def load(path: str) -> mf.Manifold:
    return to_manifold(trimesh.load(path, force="mesh"), path)


def check(paths):
    ok = True
    ms = {}
    for p in paths:
        t = trimesh.load(p, force="mesh")
        ms[p] = to_manifold(t, p)
        print(f"  {'ok  ' if t.is_watertight else 'OPEN'}  {p}: {ms[p].volume():.1f} mm3, {len(t.faces)} faces")
        ok &= t.is_watertight
    for a, b in itertools.combinations(paths, 2):
        # parts that only touch come back with float32 noise: the hex lantern's
        # art, built on its glass's face, read 0.06 mm3 over ~1500 mm2 of contact
        v = (ms[a] ^ ms[b]).volume()
        if v > 0.1:
            ok = False
            print(f"  OVERLAP {a} / {b}: {v:.3f} mm3")
    print("PARTS OK: closed, no two overlap" if ok else "PARTS FAIL")
    return ok


def union(out, paths):
    u = mf.Manifold.batch_boolean([load(p) for p in paths], mf.OpType.Add)
    t = to_trimesh(u)
    t.export(out)
    print(f"{out}: {u.volume():.1f} mm3, {len(t.faces)} faces, watertight {t.is_watertight}, bodies {len(t.split(only_watertight=False))}")


def wrap(flat, out, radius, z, minus, step):
    t = trimesh.load(flat, force="mesh")
    v, f = trimesh.remesh.subdivide_to_size(t.vertices, t.faces, max_edge=step)
    x, y, d = v[:, 0], v[:, 1], v[:, 2]
    a, r = x / radius, radius + d
    w = np.column_stack([r * np.cos(a), r * np.sin(a), y + z])
    m = to_manifold(trimesh.Trimesh(w, f, process=True), flat)
    for p in minus:
        m = m - load(p)
    t = to_trimesh(m)
    t.export(out)
    print(f"{out}: {m.volume():.1f} mm3, {len(t.faces)} faces, watertight {t.is_watertight}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("parts", nargs="+")
    u = sub.add_parser("union"); u.add_argument("out"); u.add_argument("parts", nargs="+")
    w = sub.add_parser("wrap"); w.add_argument("flat"); w.add_argument("out")
    w.add_argument("--radius", type=float, required=True); w.add_argument("--z", type=float, default=0)
    w.add_argument("--minus", action="append", default=[]); w.add_argument("--step", type=float, default=1.0)
    a = ap.parse_args()
    if a.cmd == "check":
        sys.exit(0 if check(a.parts) else 1)
    if a.cmd == "union":
        union(a.out, a.parts)
    if a.cmd == "wrap":
        wrap(a.flat, a.out, a.radius, a.z, a.minus, a.step)


if __name__ == "__main__":
    main()
