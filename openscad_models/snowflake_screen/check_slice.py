#!/usr/bin/env python3
"""Do the hinge's two parts print apart? Counted on the real toolpaths of the
fidelity slice (checks/fidelity_coupon/fidelity.gcode), every layer, each bead at its
own width, the same way as openscad_models/otter/check_slice.py.

A piece belongs to the left leaf if it touches that leaf's far end (x < -10), to
the right leaf if it touches the right one's (x > 10). A piece touching both is
fused: on this hinge that would be a knuckle joined to the other leaf across its
0.5 mm gap, along the axis or round the notch.
(Not gcode_probe.py --scan: it splits layers at z-hops.)

    python3 check_slice.py [gcode]      (writes checks/slice.txt for the default gcode)
"""
import re
import sys
from pathlib import Path

import trimesh
from shapely.geometry import LineString, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
G = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "checks" / "fidelity_coupon" / "fidelity.gcode"
STL = HERE / "parts" / "coupon.stl"
BORES, PITCH, C_H = [2.0, 2.3], 36.0, 30.0


def layers():
    z, width, x, y = None, 0.45, None, None
    segs = {}
    for line in G.read_text().splitlines():
        if line.startswith(";Z:"):
            z = round(float(line[3:]), 2)
        elif line.startswith(";WIDTH:"):
            width = float(line[7:])
        elif line.startswith(("G1", "G0")):
            p = dict(re.findall(r"([XYZEF])(-?[\d.]+)", line))
            nx, ny = float(p.get("X", x or 0)), float(p.get("Y", y or 0))
            if "E" in p and float(p["E"]) > 0 and x is not None and z is not None and (nx, ny) != (x, y):
                segs.setdefault(z, []).append(LineString([(x, y), (nx, ny)]).buffer(width / 2, cap_style=2))
            x, y = nx, ny
    return segs


def main():
    lo, hi = trimesh.load(STL).bounds
    off = (128 - (lo[0] + hi[0]) / 2, 128 - (lo[1] + hi[1]) / 2)     # the slicer centres the model
    segs = layers()
    rows, ok = [], True
    for k, g in enumerate(BORES):
        cx, cy = off[0], off[1] + k * PITCH
        win = box(cx - 18, cy - 1, cx + 18, cy + C_H + 1)
        far_l, far_r = box(cx - 18, cy - 1, cx - 10, cy + C_H + 1), box(cx + 10, cy - 1, cx + 18, cy + C_H + 1)
        fused, seen = [], 0
        for z in sorted(segs):
            shape = unary_union([s for s in segs[z] if s.intersects(win)]).intersection(win)
            parts = [shape] if shape.geom_type == "Polygon" else list(getattr(shape, "geoms", []))
            if not any(p.intersects(far_r) for p in parts):
                continue
            seen += 1
            for p in parts:
                if p.intersects(far_l) and p.intersects(far_r):
                    fused.append(z)
                    break
        good = not fused and seen == len(segs)
        ok &= good
        rows.append(f"bore {g:.1f}: {'ok  ' if good else 'FAIL'}  apart on {seen - len(fused)} of {len(segs)} layers"
                    + (f"; FUSED on {fused[:10]}" if fused else ""))
    text = "\n".join(["SNOWFLAKE SCREEN HINGE: DO THE PARTS PRINT APART? (toolpaths)"] + rows + ["PASS" if ok else "FAIL"])
    print(text)
    if len(sys.argv) == 1:
        (HERE / "checks" / "slice.txt").write_text(text + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
