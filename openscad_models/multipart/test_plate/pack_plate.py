#!/usr/bin/env python3
"""Lay the fit test plate's parts out on the P1S bed and write one 3MF
(2026-10-27). assemble_3mf's own plate layout is a row, a column or shelves,
which spends a third of the bed on the gaps beside short parts: 33 parts here
need a real packer. Bottom-left placement on each part's real shadow (its
tab sticks out of its bounding box), largest first, each part tried at four
turns; each part carries its clearance on its tab.

    python3 pack_plate.py <parts dir> <out.3mf>
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import assemble_3mf  # noqa: E402

BED, EDGE, GAP, RES = 256.0, 6.0, 4.0, 0.5   # mm; RES is the packing grid
KINDS = ["screw", "nut", "ball", "socket", "gear_base", "gear20", "gear10", "detent_base", "detent_wheel",
         "bayonet_ring", "bayonet_cap"]
COLOUR = "#F2F0E9"


def footprint(m):
    """The part's shadow on the bed, on the packing grid, holes filled."""
    from PIL import Image, ImageDraw
    lo, hi = m.bounds[0][:2], m.bounds[1][:2]
    w, d = np.ceil((hi - lo) / RES).astype(int) + 1
    img = Image.new("1", (int(w), int(d)), 0)
    dr = ImageDraw.Draw(img)
    for tri in m.triangles[:, :, :2]:
        dr.polygon([tuple(v) for v in (tri - lo) / RES], fill=1, outline=1)
    return np.array(img, bool)          # rows are y, columns x


def place(meshes):
    """Bottom-left on the real footprints, largest first, each part tried at
    0 / 90 / 180 / 270 deg. Returns (rotated mesh, x, y) per part or None."""
    from scipy.ndimage import binary_dilation
    from scipy.signal import fftconvolve
    n = int(BED / RES)
    edge = int(EDGE / RES)
    occ = np.zeros((n, n), bool)
    disk = np.hypot(*np.mgrid[-8:9, -8:9]) <= GAP / RES
    order = sorted(range(len(meshes)), key=lambda i: -meshes[i].area_faces[meshes[i].face_normals[:, 2] < -0.9].sum())
    out = [None] * len(meshes)
    for i in order:
        best = None
        for k in range(4):
            m = meshes[i].copy()
            m.apply_transform(trimesh.transformations.rotation_matrix(k * np.pi / 2, [0, 0, 1]))
            f = footprint(m)
            grown = binary_dilation(np.pad(f, 8), disk)
            hit = fftconvolve(occ.astype(float), grown[::-1, ::-1].astype(float), mode="valid") > 0.5
            fh, fw = f.shape
            ok = ~hit
            # the window's top-left is the padded mask's; the part starts 8 in
            ys, xs = np.nonzero(ok)
            ys, xs = ys + 8, xs + 8
            keep = (ys >= edge) & (xs >= edge) & (ys + fh <= n - edge) & (xs + fw <= n - edge)
            ys, xs = ys[keep], xs[keep]
            if not len(ys):
                continue
            j = np.lexsort((xs, ys + fh))[0]
            key = (ys[j] + fh, xs[j])
            if best is None or key < best[0]:
                best = (key, m, f, ys[j], xs[j])
        if best is None:
            return None
        _, m, f, y, x = best
        occ[y:y + f.shape[0], x:x + f.shape[1]] |= f
        out[i] = (m, x * RES, y * RES)
    return out


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    meshes, names = [], []
    for i in range(3):
        for k in KINDS:
            meshes.append(trimesh.load(src / f"{k}_{i}.stl", force="mesh"))
            names.append(f"{k}_{i}")
    spots = place(meshes)
    if spots is None:
        sys.exit("the parts do not fit on one P1S plate")
    tmp = out.parent / "logs" / "packed"
    tmp.mkdir(parents=True, exist_ok=True)
    for old in tmp.glob("*.stl"):
        old.unlink()
    groups, top = [], 0.0
    for n, (m, x, y) in zip(names, spots):
        m.apply_translation([x - m.bounds[0][0], y - m.bounds[0][1], -m.bounds[0][2]])
        top = max(top, m.bounds[1][1])
        p = tmp / f"{n}.stl"
        m.export(p)
        groups.append([(p, COLOUR)])
    r = assemble_3mf.assemble(out, groups, mode="placed")
    print(f"{r['file']}: {r['layout']}, bed used to y = {top:.0f} of {BED:.0f} mm")


if __name__ == "__main__":
    main()
