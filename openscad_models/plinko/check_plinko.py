#!/usr/bin/env python3
"""Snowfall Plinko test print: the fit, on the exported parts, and the slice (2026-11-16).

On the model:
- the floating balls (variants 1, 2) touch nothing: not the floor, not the lattice, not each
  other; variant 3's balls are joined to the floor only through their 0.6 necks;
- the lattice is at least 0.6 over every ball, and its openings are too narrow for a ball;
- every gap a ball meets in the hourglass, measured square to the surfaces at mid-depth, is a
  pass (>= 6.5) or a stop (<= 3.5), never between, where a ball could wedge;
- a ball can get from one end of the hourglass to the other (through the neck);
On Bambu Studio's slice (checks/release_coupon.gcode.3mf):
- under each ball, how many layers of air the printer leaves between the floor's last layer
  and the ball's first extrusion.

    python3 check_plinko.py      (writes checks/fit_plinko.txt)
"""
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
FLOOR, BALL, LAYER = 1.2, 5.0, 0.2
PASS, STOP = BALL + 1.5, BALL - 1.5
out, fails = [], []


def check(ok, msg):
    out.append(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)


def scad(part, **kw):
    with tempfile.TemporaryDirectory() as td:
        stl = Path(td) / "m.stl"
        args = ["openscad", "-o", str(stl), "-D", f'part="{part}"']
        for k, v in kw.items():
            args += ["-D", f"{k}={v}"]
        subprocess.run(args + [str(HERE / "release_coupon.scad")], capture_output=True, timeout=600, check=True)
        return trimesh.load(stl)


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def section(m, z):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        from shapely.geometry import Polygon
        return Polygon()
    p2, to3 = s.to_2D()
    from shapely import affinity
    return affinity.translate(unary_union(list(p2.polygons_full)), to3[0, 3], to3[1, 3])


def model_checks():
    body = trimesh.load(HERE / "parts" / "body.stl")
    B = man(body)
    names = ["variant 1 (0.2 float)", "variant 2 (0.4 float, the hourglass)", "variant 3 (0.6 neck)"]
    allballs = []
    for v in range(3):
        balls = scad("variant", v=v).split(only_watertight=True)
        allballs += balls
        ov = sum((man(b) ^ B).volume() for b in balls)
        low = min(b.bounds[0][2] for b in balls)
        if v < 2:
            d = min(trimesh.proximity.closest_point(body, b.vertices[b.vertices[:, 2] < low + 0.05])[1].min() for b in balls)
            check(ov < 1e-4 and abs(low - FLOOR - [0.2, 0.4][v]) < 0.02,
                  f"{names[v]}: {len(balls)} balls, touching the body {ov:.4f} mm3; their points {low - FLOOR:.2f} above "
                  f"the floor (nearest the body {d:.2f})")
        else:
            check(0.0 < ov < 0.3, f"{names[v]}: {len(balls)} balls joined to the floor only through their necks "
                                  f"({ov:.3f} mm3 overlap: the necks' 0.01 into the floor)")
    tops = max(b.bounds[1][2] for b in allballs)
    base = section(body, tops).area
    z_lat = min(z for z in np.arange(tops, tops + 2.0, 0.02) if section(body, z).area > base + 50)
    check(z_lat - tops >= 0.58, f"the lattice's underside {z_lat - tops:.2f} above the tallest ball (>= 0.6)")
    cs = [b.centroid for b in allballs]
    dmin = min(np.hypot(*(cs[i][:2] - cs[j][:2])) - BALL for i in range(len(cs)) for j in range(i + 1, len(cs)))
    check(dmin >= 0.6, f"balls printed {dmin:.2f} apart at the closest (>= 0.6)")
    # the lattice's openings: the largest circle that fits in any of them
    holes = section(body, FLOOR / 2).difference(section(body, z_lat + 0.5))
    inscribed = max(_inscribed(h) for h in getattr(holes, "geoms", [holes]))
    check(2 * inscribed <= STOP, f"lattice openings at most {2 * inscribed:.2f} across (a ball is {BALL}): none gets out")
    # the hourglass at mid-depth. Where a ball's centre can go is the free space shrunk by its
    # radius (C). A gap a ball fits through but wedges in (between 5 and 6.5) shows as part of
    # C that a 6.5 ball's centre region, grown back by the 0.75 difference, doesn't reach.
    # A plain corner leaves only a sliver of that (about 0.1 mm2); a wedging gap leaves a strip
    obst = section(body, FLOOR + 3.5)
    free = obst.envelope.difference(obst)
    hg = max(getattr(free, "geoms", [free]), key=lambda g: g.area)
    c = hg.buffer(-BALL / 2)
    wide = hg.buffer(-PASS / 2).buffer((PASS - BALL) / 2)
    wedge = c.difference(wide)
    bits = [w for w in getattr(wedge, "geoms", [wedge]) if not w.is_empty]
    big = [w for w in bits if w.area > 0.3]
    check(not big, f"hourglass at mid-depth: every gap a ball meets is a pass (>= {PASS}) or a stop (<= {STOP}); "
                   f"largest left-over sliver {max([w.area for w in bits] + [0]):.2f} mm2 (corners leave ~0.1)"
                   + ("" if not big else f": wedging gaps at {[tuple(np.round(w.centroid.coords[0], 1)) for w in big]}"))
    # a ball's centre can go from the top bins to the bottom bins
    pieces = getattr(c, "geoms", [c])
    top = [p for p in pieces if p.bounds[3] > 15]
    bot = [p for p in pieces if p.bounds[1] < -15]
    through = any(p in bot for p in top)
    check(through, f"a 5 mm ball's centre can go from one end of the hourglass to the other "
                   f"({len(pieces)} region(s) a ball's centre can reach)")
    narrow = hg.buffer(-PASS / 2)
    check(not narrow.is_empty and any(p.bounds[3] > 15 and p.bounds[1] < -15 for p in getattr(narrow, 'geoms', [narrow])),
          f"and a {PASS} ball could too: the path has no gap under {PASS}")
    return allballs


def _inscribed(poly, step=0.05):
    r = 0.0
    while not poly.buffer(-(r + step)).is_empty:
        r += step
    return r


def slice_checks(balls):
    """The air under each ball in Bambu Studio's slice: the floor's last layer, and the lowest
    layer that extrudes inside each ball's footprint."""
    g = zipfile.ZipFile(HERE / "checks" / "release_coupon.gcode.3mf").read("Metadata/plate_1.gcode").decode()
    z, feat, x, y = 0.0, "", 0.0, 0.0
    pts = []
    for ln in g.splitlines():
        if ln.startswith("; Z_HEIGHT:"):
            z = float(ln.split(":")[1])
        elif ln.startswith("; FEATURE:"):
            feat = ln[10:].strip()
        elif ln.startswith(("G1", "G2", "G3")):
            m = dict(re.findall(r"([XYE])(-?[\d.]+)", ln))
            nx, ny = float(m.get("X", x)), float(m.get("Y", y))
            if "E" in m and float(m["E"]) > 0 and feat not in ("Custom", "Prime tower"):
                pts.append((nx, ny, z))
            x, y = nx, ny
    P = np.array(pts)
    body = trimesh.load(HERE / "parts" / "coupon.stl")
    off = (P[:, :2].min(0) + P[:, :2].max(0)) / 2 - (body.bounds[0][:2] + body.bounds[1][:2]) / 2
    P[:, :2] -= off
    out.append("SLICE (Bambu Studio, PLA Matte, 0.20): air under each ball")
    labels = ["0.2 float", "0.4 float", "0.6 neck"]
    for v, rng in enumerate([range(0, 4), range(4, 8), range(8, 12)]):
        firsts = []
        for i in rng:
            c = balls[i].centroid
            near = P[np.hypot(P[:, 0] - c[0], P[:, 1] - c[1]) < 0.6]
            above = np.unique(np.round(near[near[:, 2] > FLOOR + 0.01][:, 2], 2))
            firsts.append(above.min() if len(above) else float("nan"))
        gaps = [round((f - LAYER) - FLOOR, 2) for f in firsts]
        out.append(f"  {labels[v]}: first extrusion under each ball's centre at z {sorted(set(float(round(f, 2)) for f in firsts))}; "
                   f"floor's top 1.20: air {sorted(set(float(x) for x in gaps))} mm")


def main():
    out.append("SNOWFALL PLINKO TEST PRINT: FIT (exported geometry)")
    balls = model_checks()
    slice_checks(balls)
    out.append("PASS" if not fails else "FAIL: " + "; ".join(fails))
    text = "\n".join(out)
    print(text)
    (HERE / "checks" / "fit_plinko.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
