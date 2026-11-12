#!/usr/bin/env python3
"""Fit check for the Moon Phase Coasters, on the exported parts in their places.

The coasters stand in curved cradles 0.4 mm bigger than they are, so in the model
they float; each is dropped 0.4 mm to rest on its cradle's floor before checking.
Checks: nothing overlaps; the gaps between neighbours; each coaster rests on its
cradle; each lifts straight out without touching anything; the front coaster
cannot fall forward through the panel's window.
"""
import subprocess, sys
from pathlib import Path
import numpy as np, trimesh, manifold3d as mf

HERE = Path(__file__).resolve().parent
SCAD = HERE / "moon_coasters.scad"
OUT = HERE / "parts" / "placed"
CLEAR, N = 0.4, 4

def export(part, **kw):
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / (part + "".join(f"_{v}" for v in kw.values()) + ".stl")
    args = ["openscad", "-o", str(f), "-D", f'part="{part}"'] + sum([["-D", f"{k}={v}"] for k, v in kw.items()], [])
    subprocess.run(args + [str(SCAD)], check=True, capture_output=True,
                   env={"OPENSCADPATH": str(HERE.parents[1] / "assets" / "openscad_libs"), "PATH": "/usr/bin:/bin"})
    return trimesh.load(f)

def M(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))

def overlap(a, b):
    return (M(a) ^ M(b)).volume()

def gap(a, b, n=4000):
    pts = a.sample(n)
    return float(np.abs(trimesh.proximity.signed_distance(b, pts)).min())

def moved(m, dz=0.0, dy=0.0):
    c = m.copy(); c.apply_translation([0, dy, dz]); return c

def main():
    base = trimesh.load(HERE / "parts" / "base_print.stl")
    panel = export("placed_panel")
    coasters = [moved(export("placed_coaster", slot=i), dz=-CLEAR) for i in range(N)]
    rows, ok = [], True
    def rec(name, good, val):
        nonlocal ok
        ok &= good; rows.append(f"  {'ok  ' if good else 'FAIL'}  {name}: {val}")
    rec("panel overlaps base", overlap(panel, base) < 1e-3, f"{overlap(panel, base):.4f} mm3")
    for i, c in enumerate(coasters):
        v = overlap(c, base)
        rec(f"coaster {i} overlaps base (resting on its cradle)", v < 1e-3, f"{v:.4f} mm3")
        rec(f"coaster {i} rests on its cradle", gap(c, base) < 0.05, f"closest {gap(c, base):.3f} mm")
        up = moved(c, dz=0.2)
        rec(f"coaster {i} lifts clear of the base", overlap(up, base) < 1e-3, f"{overlap(up, base):.4f} mm3 after 0.2 up")
    for i in range(N - 1):
        g = gap(coasters[i], coasters[i + 1])
        rec(f"coasters {i}/{i + 1} apart", g >= 0.3, f"{g:.2f} mm")
    g = gap(coasters[0], panel)
    rec("front coaster to the panel", g >= 0.3, f"{g:.2f} mm")
    # tip the front coaster forward against the panel: it must meet the panel, not pass the window
    fwd = moved(coasters[0], dy=-(g + 0.5))
    rec("front coaster cannot fall through the window", overlap(fwd, panel) > 1.0,
        f"{overlap(fwd, panel):.1f} mm3 of panel in the way when pushed {g + 0.5:.1f} mm forward")
    lines = ["MOON COASTERS FIT CHECK (exported parts, coasters dropped 0.4 mm onto their cradles)"] + rows
    lines.append("PASS" if ok else "FAIL")
    print("\n".join(lines))
    (HERE / "checks" / "fit.txt").write_text("\n".join(lines) + "\n")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
