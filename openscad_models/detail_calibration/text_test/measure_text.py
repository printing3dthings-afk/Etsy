#!/usr/bin/env python3
"""How much of small raised lettering and dots survives the toolpath, on a
0.4 and a 0.2 mm nozzle (2026-10-30).

    python3 measure_text.py            slice text_coupon.stl four ways and measure

Scott asked how to design smaller detail. The coupon in the folder above showed
a 0.4 mm nozzle holds relief depth across a face to the hundredth; what it
doesn't test is small shapes, where the bead's own width is the limit. Here
every letter row and dot is cut out layer by layer, from the model and from the
printed beads (each run buffered by its own ;WIDTH:), and compared:

    kept   = printed inside the model / model
    extra  = printed outside the model / model
    match  = overlap / union (1.0 is perfect)

Toolpath numbers, as for the detail coupon: bead rounding and ooze come on top.
"""
import json, sys
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import LineString, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import virtual_printer  # noqa: E402
from print_fidelity import BED_CENTRE, parse_gcode  # noqa: E402

SIZES = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
DOTS = [0.4, 0.6, 0.8, 1.0, 1.2, 1.6]
ROWY = lambda i: 4 + i * 6
CONFIGS = {   # name: nozzle, line width, layer height
    "0.4 nozzle, 0.20 layers": (0.4, 0.42, 0.20),
    "0.4 nozzle, 0.08 layers": (0.4, 0.42, 0.08),
    "0.2 nozzle, 0.10 layers": (0.2, 0.22, 0.10),
    "0.2 nozzle, 0.08 layers": (0.2, 0.22, 0.08),
}


def items():
    """(name, face, region box in the model's frame, z range) per feature."""
    out = []
    for i, s in enumerate(SIZES):
        out.append((f"text {s}", "top", box(2, ROWY(i) - 3, 34, ROWY(i) + 3), (2.0, 2.4)))
        out.append((f"text {s}", "wall", box(2, 59.0, 34, 59.99), (ROWY(i) - 3, ROWY(i) + 3)))
    for k, d in enumerate(DOTS):
        x = 38 + k * 4
        out.append((f"dot {d}", "top", box(x - 1.5, 38.5, x + 1.5, 41.5), (2.0, 2.4)))
        out.append((f"dot {d}", "wall", box(x - 1.5, 59.0, x + 1.5, 59.99), (38.5, 41.5)))
    return out


def model_section(mesh, z):
    s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        return None
    p, _ = s.to_planar(to_2D=np.eye(4))
    return unary_union(list(p.polygons_full))


def printed(layer, off, region):
    shapes = []
    for (tool, w), runs in layer["beads"].items():
        for r in runs:
            ls = LineString([(x - off[0], y - off[1]) for x, y in r])
            if ls.distance(region) <= w:
                shapes.append(ls.buffer(w / 2))
    return unary_union(shapes).intersection(region) if shapes else None


def measure(gcode, mesh):
    lo, hi = mesh.bounds
    off = (BED_CENTRE[0] - (lo[0] + hi[0]) / 2, BED_CENTRE[1] - (lo[1] + hi[1]) / 2)
    layers = parse_gcode(gcode)
    res = {}
    for name, face, region, (z0, z1) in items():
        m_a = p_in = p_out = u = 0.0
        for L in layers:
            if L["z"] is None:
                continue
            zm = L["z"] - (L["h"] or 0.2) / 2
            if not (z0 < zm < z1):
                continue
            sec = model_section(mesh, zm)
            m = sec.intersection(region) if sec is not None else None
            p = printed(L, off, region)
            ma = m.area if m is not None else 0.0
            pa = p.area if p is not None else 0.0
            inter = m.intersection(p).area if (m is not None and p is not None) else 0.0
            m_a += ma
            p_in += inter
            p_out += pa - inter
            u += ma + pa - inter
        res[f"{name} ({face})"] = {"kept": p_in / m_a if m_a else None, "extra": p_out / m_a if m_a else None,
                                   "match": p_in / u if u else None}
    return res


def main():
    mesh = trimesh.load(HERE / "text_coupon.stl")
    out = {}
    for name, (noz, w, lh) in CONFIGS.items():
        g = HERE / "logs" / (name.replace(" ", "_").replace(",", "") + ".gcode")
        if not g.exists():
            extra = {"nozzle-diameter": str(noz), "extrusion-width": str(w), "layer-height": str(lh),
                     "first-layer-height": str(lh), "center": f"{BED_CENTRE[0]},{BED_CENTRE[1]}"}
            virtual_printer.slice_model(HERE / "text_coupon.stl", g, supports=False, extra=extra)
        out[name] = measure(g, mesh)
        print(name, "done", flush=True)
    (HERE / "logs" / "measured_text.json").write_text(json.dumps(out, indent=1))
    keys = list(next(iter(out.values())))
    print(f"{'feature':24s}" + "".join(f"{n[:22]:>24s}" for n in out))
    for k in keys:
        cells = []
        for n in out:
            r = out[n][k]
            cells.append("-" if r["match"] is None else f"match {r['match']:.2f} kept {r['kept']:.2f}")
        print(f"{k:24s}" + "".join(f"{c:>24s}" for c in cells))


if __name__ == "__main__":
    main()
