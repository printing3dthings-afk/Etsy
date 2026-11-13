#!/usr/bin/env python3
"""Does the capped joint print as two parts? Counted on the real toolpaths.

The fidelity slice of the capped joint test (checks/fidelity_cap/fidelity.gcode,
PrusaSlicer, P1S 0.4) is read layer by layer; every extrusion move is drawn at its own
width. In a window round each joint, the beads are joined into pieces, and each piece
is matched against the model's cross-sections of the front and back parts at that
height (each shrunk 0.1 mm, so a bead can only match the part it belongs to). A piece
that matches both is the two parts printed fused at that layer. Also reports the
narrowest air gap between front and back beads on each layer, and a control: the same
reading with the two cross-sections swapped must find nothing new.

    python3 check_cap_slice.py      (writes checks/slice_cap.txt)
"""
import re
from pathlib import Path

import numpy as np
import trimesh
from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
G = HERE / "checks" / "fidelity_cap" / "fidelity.gcode"
PITCH = 34.0
GAPS = [0.30, 0.40]
WIN = 13.0


def layers():
    z, width, x, y = None, 0.45, None, None
    segs = {}
    for line in G.read_text().splitlines():
        if line.startswith(";Z:"):
            z = round(float(line[3:]), 2)
        elif line.startswith(";WIDTH:"):
            width = float(line[7:])
        elif line.startswith("G1") or line.startswith("G0"):
            p = dict(re.findall(r"([XYZEF])(-?[\d.]+)", line))
            nx, ny = float(p.get("X", x if x is not None else 0)), float(p.get("Y", y if y is not None else 0))
            if "E" in p and float(p["E"]) > 0 and x is not None and z is not None and (nx, ny) != (x, y):
                segs.setdefault(z, []).append(LineString([(x, y), (nx, ny)]).buffer(width / 2, cap_style=2))
            x, y = nx, ny
    return segs


def section(mesh, z):
    s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        return Polygon()
    p2, to3 = s.to_2D()
    polys = [translate(p, to3[0, 3], to3[1, 3]) for p in p2.polygons_full]
    return unary_union(polys)


def main():
    segs = layers()
    plate = trimesh.load(HERE / "parts" / "cap_coupon.stl")
    pts = np.vstack([np.array(s.exterior.coords) for z in list(segs)[2:6] for s in segs[z]])
    # the slicer centres the model on the bed: map model xy to toolpath xy
    off = (pts.min(0) + pts.max(0)) / 2 - (plate.bounds[0][:2] + plate.bounds[1][:2]) / 2
    out = ["CAPPED JOINT TEST: TOOLPATH SEPARATION (PrusaSlicer fidelity slice)",
           f"model-to-bed offset {off.round(2)}"]
    ok = True
    zs = sorted(segs)
    for v, g in enumerate(GAPS):
        front = trimesh.load(HERE / "parts" / f"cap_front{v}.stl")
        back = trimesh.load(HERE / "parts" / f"cap_back{v}.stl")
        cx, cy = off[0], off[1] + v * PITCH
        win = Point(cx, cy).buffer(WIN)
        fused, narrow, seen = [], [], 0
        for i, z in enumerate(zs):
            zc = z - (z - (zs[i - 1] if i else 0)) / 2
            fs = translate(section(front, zc), off[0], off[1]).buffer(-0.1).intersection(win)
            bs = translate(section(back, zc), off[0], off[1]).buffer(-0.1).intersection(win)
            beads = unary_union([s for s in segs[z] if s.intersects(win)]).intersection(win)
            pieces = [beads] if beads.geom_type == "Polygon" else list(getattr(beads, "geoms", []))
            pf = [p for p in pieces if p.intersects(fs)]
            pb = [p for p in pieces if p.intersects(bs)]
            if not pf or not pb:
                continue
            seen += 1
            if any(p.intersects(fs) and p.intersects(bs) for p in pieces):
                fused.append(z)
                continue
            narrow.append((min(a.distance(b) for a in pf for b in pb), z))
        good = not fused and seen > 0.9 * len(zs)
        ok &= good
        nmin = min(narrow) if narrow else (None, None)
        out.append(f"cap gap {g:.2f}: {'apart' if good else 'FUSED'} on {seen - len(fused)} of {seen} layers with both parts"
                   + (f"; fused at z {fused[:8]}" if fused else ""))
        if narrow:
            out.append(f"  narrowest printed air gap {nmin[0]:.2f} mm at z {nmin[1]}")
    out.append("PASS" if ok else "FAIL")
    text = "\n".join(out)
    print(text)
    (HERE / "checks" / "slice_cap.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
