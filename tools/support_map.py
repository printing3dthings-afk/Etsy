#!/usr/bin/env python3
"""Where does the slicer put support, and why? (2026-11-04, Kawaii Cow)

product_gate says how many support moves a print needs, not where. This
slices with supports on, maps each support column back to the model's own
coordinates, and lists the top of each (the overhang it holds up). With
--layers it also measures the mesh the way the slicer does: each 0.2 mm
layer against the one below grown by 0.2 * tan(limit), and lists every patch
that sticks out further.

Every support the cow drew had a real, locatable cause this way: an ear
leaf's lower edge at 46 deg, a drip under a gap, a crevice closing over 0.8 mm
up, a slot cut by an inverted groove. The slicer adds 1 deg to its threshold
(45 -> 44 from upright), so measure with --limit 44.

    python3 tools/support_map.py model.stl [--layers] [--limit 44] [--plot out.png]
"""
from __future__ import annotations

import argparse
import collections
import re
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
import virtual_printer as vp  # noqa: E402

_NUM = re.compile(r"([XYZE])([-+]?\d*\.?\d+)")


def read_moves(gcode):
    """[(z, type, x0, y0, x1, y1)] for every extruding move."""
    z = 0.0; typ = ""; x = y = 0.0; rows = []
    for ln in open(gcode, errors="replace"):
        if ln.startswith(";TYPE:"):
            typ = ln[6:].strip(); continue
        if ln.startswith(";Z:"):
            z = float(ln[3:]); continue
        if ln.startswith("G1"):
            d = dict((k, float(v)) for k, v in _NUM.findall(ln.split(";")[0]))
            nx, ny = d.get("X", x), d.get("Y", y)
            if d.get("E", 0) > 0:
                rows.append((z, typ, x, y, nx, ny))
            x, y = nx, ny
    return rows


def support_columns(mesh_path, cell=3.0):
    """Slice with supports; return (offset, [(cell_xy, z_low, z_high)]) in model xy."""
    m = trimesh.load(mesh_path, force="mesh")
    with tempfile.TemporaryDirectory() as tmp:
        g = Path(tmp) / "s.gcode"
        vp.slice_model(mesh_path, g, supports=True)
        rows = read_moves(g)
    model = np.array([(r[4], r[5]) for r in rows if "upport" not in r[1] and "kirt" not in r[1]])
    sup = [r for r in rows if "upport" in r[1]]
    # the slicer centres the model on the bed: map back by bounding-box centres
    off = (m.bounds[0][:2] + m.bounds[1][:2]) / 2 - (model.min(0) + model.max(0)) / 2
    cols = collections.defaultdict(lambda: [1e9, -1e9])
    for z, _, _, _, x, y in sup:
        k = (float(np.floor((x + off[0]) / cell) * cell), float(np.floor((y + off[1]) / cell) * cell))
        c = cols[k]; c[0] = min(c[0], z); c[1] = max(c[1], z)
    return off, rows, sorted(((k, lo, hi) for k, (lo, hi) in cols.items()), key=lambda t: -t[2])


def layer_overhangs(mesh_path, limit=44.0, h=0.2, min_area=0.002):
    """Patches of each layer further out than the layer below grown by h*tan(limit)."""
    from shapely.geometry import Polygon
    m = trimesh.load(mesh_path, force="mesh")
    grow = h * np.tan(np.radians(limit))

    def layer(z):
        sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        out = Polygon()
        if sec is None:
            return out
        for ent in sec.discrete:
            if len(ent) >= 4:
                out = out.symmetric_difference(Polygon(ent[:, :2]).buffer(0))
        return out

    prev, found = None, []
    for z in np.arange(h / 2, m.bounds[1][2], h):
        cur = layer(z)
        if prev is not None and not cur.is_empty:
            un = cur.difference(prev.buffer(grow))
            for p in getattr(un, "geoms", [un]):
                if p.area > min_area:
                    found.append((round(float(z), 2), round(p.area, 4), tuple(np.round(p.centroid.coords[0], 1))))
        prev = cur
    return found


def plot(rows, off, out, zs=(0.2, 1.0, 5.0)):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, len(zs), figsize=(6 * len(zs), 6))
    for ax, zz in zip(axs, zs):
        for z, t, a, b, c, d in rows:
            sup = "upport" in t
            if (sup and abs(z - zz) <= 0.21) or (not sup and abs(z - zz) < 0.05):
                ax.plot([a + off[0], c + off[0]], [b + off[1], d + off[1]],
                        color="red" if sup else "0.6", lw=1.5 if sup else 0.4)
        ax.set_aspect("equal"); ax.set_title(f"z {zz}: model grey, support red")
    plt.savefig(out, dpi=80)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mesh")
    ap.add_argument("--layers", action="store_true", help="also measure each layer against the one below")
    ap.add_argument("--limit", type=float, default=44.0)
    ap.add_argument("--plot", help="PNG of support over the layers at z 0.2, 1.0, 5.0")
    a = ap.parse_args()
    off, rows, cols = support_columns(a.mesh)
    print(f"{sum(1 for r in rows if 'upport' in r[1])} support extrusions")
    for (x, y), lo, hi in cols[:40]:
        print(f"  near x {x:6.1f} y {y:6.1f}: support z {lo:.1f} -> {hi:.1f} (holds up what is at ~{hi + 0.4:.1f})")
    if a.plot:
        plot(rows, off, a.plot)
    if a.layers:
        f = layer_overhangs(a.mesh, a.limit)
        for z, area, c in f[:60]:
            print(f"  layer z {z}: {area} mm2 past {a.limit} deg at {c}")
        print(f"{len(f)} patches, {sum(x[1] for x in f):.2f} mm2 past {a.limit} deg")


if __name__ == "__main__":
    main()
