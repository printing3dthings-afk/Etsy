#!/usr/bin/env python3
"""Read what the SLICER actually decided, not what the model says.

A 0.2mm modelled gap is a hypothesis until a slicer turns it into toolpaths.
This rasterises the real extrusion moves of a layer and counts connected
islands of material -- the toolpath equivalent of a connected-component check
on a mesh. If two parts that should be free come out as one island, the joint
prints fused no matter what the geometry says.

    python3 tools/gcode_probe.py file.gcode --summary
    python3 tools/gcode_probe.py file.gcode --layer-z 12.4 --window 0,156,20
"""
import argparse, re, sys
import numpy as np


def parse(path):
    """Extrusion segments per layer: [(z, [(x0,y0,x1,y1), ...]), ...]."""
    layers = []
    x = y = z = 0.0
    e_abs = True
    e_last = 0.0
    cur = []
    curz = None
    for line in open(path, "r", errors="ignore"):
        s = line.split(";")[0].strip()
        if not s:
            continue
        if s.startswith("M83"):
            e_abs = False
        elif s.startswith("M82"):
            e_abs = True
        if not (s.startswith("G0") or s.startswith("G1")):
            continue
        nx, ny, nz, ne = x, y, z, None
        for tok in s.split()[1:]:
            c, v = tok[0], tok[1:]
            try:
                f = float(v)
            except ValueError:
                continue
            if c == "X": nx = f
            elif c == "Y": ny = f
            elif c == "Z": nz = f
            elif c == "E": ne = f
        if nz != z:
            if cur:
                layers.append((z, cur)); cur = []
            z = nz
        moved = (nx != x or ny != y)
        if ne is not None and moved:
            # A wipe-while-retracting move has XY motion and FALLING E -- count
            # it as extrusion and a travel becomes a phantom wall.
            forward = (ne > 0) if not e_abs else (ne > e_last)
            if forward:
                cur.append((x, y, nx, ny))
        if ne is not None:
            e_last = ne
        x, y = nx, ny
    if cur:
        layers.append((z, cur))
    return layers


def islands(segs, width=0.42, px=0.06, window=None, dilate=True):
    """Rasterise extrusions and count separate blobs of material."""
    from scipy import ndimage
    if not segs:
        return 0, []
    a = np.array(segs)
    if window:
        cx, cy, half = window
        keep = ((np.minimum(a[:, 0], a[:, 2]) > cx - half) & (np.maximum(a[:, 0], a[:, 2]) < cx + half) &
                (np.minimum(a[:, 1], a[:, 3]) > cy - half) & (np.maximum(a[:, 1], a[:, 3]) < cy + half))
        a = a[keep]
        if not len(a):
            return 0, []
    lo = np.array([min(a[:, 0].min(), a[:, 2].min()), min(a[:, 1].min(), a[:, 3].min())]) - 2
    hi = np.array([max(a[:, 0].max(), a[:, 2].max()), max(a[:, 1].max(), a[:, 3].max())]) + 2
    shape = np.ceil((hi - lo) / px).astype(int)[::-1]
    grid = np.zeros(shape, bool)
    r = max(int(round(width / 2 / px)), 1)
    for x0, y0, x1, y1 in a:
        n = max(int(np.hypot(x1 - x0, y1 - y0) / px) + 1, 2)
        xs = np.linspace(x0, x1, n); ys = np.linspace(y0, y1, n)
        cc = ((xs - lo[0]) / px).astype(int); rr = ((ys - lo[1]) / px).astype(int)
        ok = (rr >= 0) & (rr < shape[0]) & (cc >= 0) & (cc < shape[1])
        grid[rr[ok], cc[ok]] = True
    if dilate:
        grid = ndimage.binary_dilation(grid, ndimage.generate_binary_structure(2, 2), iterations=r)
    lab, n = ndimage.label(grid, structure=np.ones((3, 3)))
    areas = sorted((lab == i).sum() * px * px for i in range(1, n + 1))[::-1]
    return n, [round(v, 2) for v in areas[:12]]


def summary(path):
    txt = open(path, "r", errors="ignore").read()
    out = {}
    for key, pat in [
        ("estimated_time", r"estimated printing time.*?=\s*(.+)"),
        ("filament_g", r"filament used \[g\]\s*=\s*([\d.]+)"),
        ("filament_mm", r"filament used \[mm\]\s*=\s*([\d.]+)"),
        ("filament_cost", r"filament cost\s*=\s*([\d.]+)"),
        ("layer_height", r"; layer_height = ([\d.]+)"),
        ("perimeters", r"; perimeters = (\d+)"),
    ]:
        m = re.search(pat, txt)
        if m:
            out[key] = m.group(1).strip()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gcode")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--layer-z", type=float, default=None)
    ap.add_argument("--window", default=None, help="cx,cy,half in mm")
    ap.add_argument("--scan", action="store_true", help="island count for every layer")
    ap.add_argument("--px", type=float, default=0.06, help="raster pixel size in mm -- coarser than ~0.1mm can falsely merge a real gap under ~0.15mm (found on a gear-mesh print, see SKILL.md)")
    ap.add_argument("--plot", default=None, help="write a PNG of this layer's toolpaths")
    a = ap.parse_args()
    if a.summary:
        for k, v in summary(a.gcode).items():
            print(f"  {k:16s} {v}")
    if a.layer_z is None and not a.scan:
        return
    layers = parse(a.gcode)
    print(f"  layers parsed: {len(layers)}  z {layers[0][0]:.2f} .. {layers[-1][0]:.2f}")
    win = tuple(float(v) for v in a.window.split(",")) if a.window else None
    if a.scan:
        for z, segs in layers[::max(len(layers) // 25, 1)]:
            n, areas = islands(segs, window=win, px=a.px)
            print(f"   z={z:7.2f}  islands={n:3d}  areas={areas[:6]}")
    else:
        best = min(layers, key=lambda t: abs(t[0] - a.layer_z))
        n, areas = islands(best[1], window=win, px=a.px)
        print(f"   z={best[0]:.2f}  islands={n}  areas(mm2)={areas}")
        if a.plot:
            import matplotlib; matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(11, 11))
            for x0, y0, x1, y1 in best[1]:
                ax.plot([x0, x1], [y0, y1], lw=2.6, solid_capstyle="round", color="#2b6cb0")
            if win:
                ax.set_xlim(win[0] - win[2], win[0] + win[2]); ax.set_ylim(win[1] - win[2], win[1] + win[2])
            ax.set_aspect("equal"); ax.grid(alpha=.3)
            ax.set_title(f"toolpaths at z={best[0]:.2f}  ({n} islands)")
            fig.tight_layout(); fig.savefig(a.plot, dpi=130); print("   wrote", a.plot)


if __name__ == "__main__":
    main()
