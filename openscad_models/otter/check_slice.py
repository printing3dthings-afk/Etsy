#!/usr/bin/env python3
"""Does each pin print apart from its ring? Counted on the real toolpaths.

The fidelity slice (checks/fidelity/fidelity.gcode, PrusaSlicer, P1S 0.4) is read
layer by layer between its ;Z: markers -- every extrusion move on the layer, from
every object, each bead drawn at its own width (;WIDTH:) -- and the pieces inside
each joint's window are counted. A pin that printed apart from its ring is a
separate piece on every layer; one that fused is not. Also reports the narrowest
air gap between pin and ring on each layer.

tools/gcode_probe.py --scan was tried first and is not usable on this slice: it
splits a layer at every z-hop, so it saw one object at a time (1277 "layers" in a
50-layer print), and a ring alone always counts as one island.

    python3 check_slice.py      (writes checks/slice.txt)
"""
import re
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
G = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "checks" / "fidelity" / "fidelity.gcode"
# where the slicer put each pin (the model centred on the bed): see joint_coupon.scad
OFFSET = (128.5, 103.9)
PITCH, HALF = 24.0, 10.5


def layers():
    z, width, x, y, e_abs = None, 0.45, None, None, False
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


# (gap, waist radius, ring outside radius), as joint_coupon.scad computes them
JOINTS = [(0.30, 4.0, 7.80), (0.35, 4.0, 7.85), (0.45, 4.0, 7.95)]


def main():
    segs = layers()
    rows, ok = [], True
    for i, (g, ra, ro) in enumerate(JOINTS):
        cx, cy = OFFSET[0], OFFSET[1] + i * PITCH
        win = box(cx - HALF, cy - HALF, cx + HALF, cy + HALF)
        # a piece is the pin's if it crosses a circle just inside the pin's waist (inside
        # even its 0.45 foot chamfer), the ring's if it crosses one just inside the ring's
        # outside. Fused = one piece crosses both. (The pin's centre is sparse infill on
        # most layers, so "the piece on the axis" found the pin on 9 layers of 50.)
        pin_c = Point(cx, cy).buffer(ra - 0.8).exterior
        # only the half away from the slot: the pin's fin leaves through the slot and
        # crosses the full circle, which read as "fused" on every layer
        ring_c = Point(cx, cy).buffer(ro - 0.3).exterior.intersection(box(cx + 0.5, cy - 20, cx + 20, cy + 20))
        fused, narrow, seen = [], 99.0, 0
        for z in sorted(segs):
            shape = unary_union([s for s in segs[z] if s.intersects(win)]).intersection(win)
            parts = [shape] if shape.geom_type == "Polygon" else list(getattr(shape, "geoms", []))
            pin = [p for p in parts if p.intersects(pin_c)]
            ring = [p for p in parts if p.intersects(ring_c)]
            if not pin or not ring:
                continue
            seen += 1
            if any(p.intersects(ring_c) for p in pin):
                fused.append(z)
                continue
            narrow = min(narrow, min(a.distance(b) for a in pin for b in ring))
        good = not fused and seen == len(segs)
        ok &= good
        rows.append(f"gap {g:.2f}: {'ok  ' if good else 'FAIL'}  pin and ring separate on {seen - len(fused)} of "
                    f"{len(segs)} layers; narrowest printed air gap {narrow:.2f} mm"
                    + (f"; FUSED on {fused[:10]}" if fused else ""))
    text = "\n".join(["OTTER JOINT: DO THE PINS PRINT APART? (toolpaths of the fidelity slice)"] + rows
                     + ["PASS" if ok else "FAIL"])
    print(text)
    if len(sys.argv) == 1:
        (HERE / "checks" / "slice.txt").write_text(text + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
