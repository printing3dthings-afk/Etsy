#!/usr/bin/env python3
"""Fast software shaded render of a mesh -- no Blender, no GPU, no display.

Blender in this container takes >15s just to answer --version, which makes it
useless for the look-at-it-now loop that catches real modelling mistakes. This
is a plain numpy z-buffer rasteriser: orthographic, one directional light plus
ambient. It is not a beauty render; it is for SEEING the form.

    python3 tools/quick_render.py model.stl -o out.png --az 35 --el 25
"""
import argparse, numpy as np, trimesh
from PIL import Image


def rot(az, el):
    a, e = np.radians(az), np.radians(el)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    return Rx @ Rz


def render(mesh, az=35, el=25, res=900, bg=245, light=(-0.4, -0.6, 0.7)):
    R = rot(az, el)
    v = mesh.vertices @ R.T
    n = mesh.face_normals @ R.T
    lo, hi = v.min(0), v.max(0)
    span = (hi - lo)[:2].max() * 1.06
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    sx = (v[:, 0] - cx) / span * res + res / 2
    sy = res / 2 - (v[:, 1] - cy) / span * res
    z = v[:, 2]
    L = np.array(light, float); L /= np.linalg.norm(L)
    shade = np.clip(n @ L, 0, 1) * 0.78 + 0.22
    img = np.full((res, res), float(bg))
    zb = np.full((res, res), -1e18)
    tri = mesh.faces
    # painter-ish: rasterise per triangle with a z-buffer, vectorised over each bbox
    order = np.argsort(z[tri].mean(1))
    for f in order:
        a, b, c = tri[f]
        xs = np.array([sx[a], sx[b], sx[c]]); ys = np.array([sy[a], sy[b], sy[c]])
        x0, x1 = int(max(0, np.floor(xs.min()))), int(min(res - 1, np.ceil(xs.max())))
        y0, y1 = int(max(0, np.floor(ys.min()))), int(min(res - 1, np.ceil(ys.max())))
        if x1 < x0 or y1 < y0:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        d = ((ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2]))
        if abs(d) < 1e-9:
            continue
        w0 = ((ys[1] - ys[2]) * (X - xs[2]) + (xs[2] - xs[1]) * (Y - ys[2])) / d
        w1 = ((ys[2] - ys[0]) * (X - xs[2]) + (xs[0] - xs[2]) * (Y - ys[2])) / d
        w2 = 1 - w0 - w1
        m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not m.any():
            continue
        zz = w0 * z[a] + w1 * z[b] + w2 * z[c]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        upd = m & (zz > sub)
        sub[upd] = zz[upd]
        img[y0:y1 + 1, x0:x1 + 1][upd] = shade[f] * 255
    return Image.fromarray(img.astype(np.uint8))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mesh"); ap.add_argument("-o", "--out", default="render.png")
    ap.add_argument("--az", type=float, default=35); ap.add_argument("--el", type=float, default=25)
    ap.add_argument("--res", type=int, default=900)
    ap.add_argument("--faces", type=int, default=200000, help="decimate above this face count")
    a = ap.parse_args()
    m = trimesh.load(a.mesh, force="mesh")
    if len(m.faces) > a.faces:
        m = m.simplify_quadric_decimation(1.0 - a.faces / len(m.faces))
    render(m, a.az, a.el, a.res).save(a.out)
    print("wrote", a.out, "faces", len(m.faces))
