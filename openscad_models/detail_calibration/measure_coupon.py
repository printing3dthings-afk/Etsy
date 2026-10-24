#!/usr/bin/env python3
"""What the printer keeps of each feature on detail_coupon.scad (2026-10-24).

    python3 measure_coupon.py logs/slice_0.20/fidelity.gcode 0.20

print_fidelity counts a miss only where it holds above and below a slicing
plane, so a ridge thinner than one layer is a tie to it, not a miss: on this
coupon it flagged nothing at 0.12 mm layers. This reads the beads instead.
Every layer's printed area is rebuilt from the toolpath at each bead's own
;WIDTH:, cut along a line through the middle of each feature, and the
frontmost printed point on that line is compared with the model's.
"""
import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import LineString
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
from print_fidelity import BED_CENTRE, parse_gcode  # noqa: E402

# Must match detail_coupon.scad.
P, pitch, x0, fw = 0.6, 12, 9, 8
row_z = [3, 9, 15, 21, 27, 33, 39]
rows = {
    "square ridge, 0.6 proud: height": ([0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.2], 0, "h"),
    "chamfered ridge, 0.6 proud: height": ([0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.2], 1, "h"),
    "groove, 0.6 deep: height": ([0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.2], 2, "g"),
    "chamfered ridge, 1.0 tall: proud": ([0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 1.0], 3, "p"),
    "boss: diameter": ([0.6, 0.8, 1.0, 1.2, 1.6, 2.0, 2.6], 4, "d"),
    "vertical groove 0.4 wide: depth": ([0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0], 5, "v"),
    "vertical rib, 0.6 proud: width": ([0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0], 6, "w"),
}


def printed_front(layers, off, x):
    """For each layer, the frontmost printed y (model frame) on the line at x."""
    out = []
    probe = LineString([(x + off[0], -3 + off[1]), (x + off[0], 2 + off[1])])
    for L in layers:
        shapes = []
        for (tool, w), runs in L["beads"].items():
            for r in runs:
                ls = LineString(r)
                if ls.distance(probe) <= w:
                    shapes.append(ls.buffer(w / 2))
        cut = unary_union(shapes).intersection(probe) if shapes else None
        y = None if cut is None or cut.is_empty else cut.bounds[1] - off[1]
        out.append((L["z"], L["h"], y))
    return out


def main():
    gcode, lh = Path(sys.argv[1]), sys.argv[2]
    mesh = trimesh.load(HERE / "detail_coupon.stl")
    lo, hi = mesh.bounds
    off = (BED_CENTRE[0] - (lo[0] + hi[0]) / 2, BED_CENTRE[1] - (lo[1] + hi[1]) / 2)
    layers = [L for L in parse_gcode(gcode) if L["z"] is not None]
    report = {}
    for name, (sizes, r, kind) in rows.items():
        z0 = row_z[r]
        res = []
        for i, s in enumerate(sizes):
            cx = x0 + i * pitch
            prof = printed_front(layers, off, cx)
            if kind in ("h", "g"):
                # height of the band standing proud (or sunk) by at least half
                band = [h for z, h, y in prof if y is not None and z0 - 0.3 < z < z0 + s + 1.5 and
                        (y <= -P / 2 if kind == "h" else y >= P / 2)]
                res.append({"size": s, "printed_height": round(sum(band), 2), "layers": len(band)})
            elif kind == "p":
                ys = [y for z, h, y in prof if y is not None and z0 + 0.2 < z < z0 + 1.0]
                res.append({"size": s, "printed_proud": round(-min(ys), 2) if ys else 0.0})
            elif kind == "d":
                zc = z0 + 1.5
                band = [(z, -y) for z, h, y in prof if y is not None and abs(z - zc) < s and y < -0.1]
                res.append({"size": s, "printed_proud": round(max((p for _, p in band), default=0.0), 2),
                            "layers_proud": len(band)})
            elif kind == "v":
                ys = [y for z, h, y in prof if y is not None and z0 + 0.5 < z < z0 + 3.5]
                res.append({"size": s, "printed_depth": round(float(np.median(ys)), 2) if ys else None})
            elif kind == "w":
                ys = [y for z, h, y in prof if y is not None and z0 + 0.5 < z < z0 + 4.5]
                res.append({"size": s, "printed_proud": round(-float(np.median(ys)), 2) if ys else None})
        report[name] = res
        print(f"{lh} mm layers | {name}")
        for e in res:
            print("   ", e)
    (HERE / "logs" / f"measured_{lh}.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
