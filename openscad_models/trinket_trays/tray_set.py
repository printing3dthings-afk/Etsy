"""Christmas trinket trays: a rippled frame and a drop-in insert (2026-11-24).

Scott showed trays like these ("Examples of what I want to have in our catalog") and picked the
rippled-frame-plus-insert direction (2026-11-24): a tray whose outer wall ripples, and a
second, smooth tray in another colour that drops inside it. Each piece is one colour, so it's
two-tone without an AMS, and buyers mix colours.

Our own shapes, not anyone else's: star, tree, mitten, bauble, bell, and the Tin Clicker's
gingerbread man (the same outline, scaled up).

Each shape makes two parts:
  frame   a floor, and a wall that is smooth inside and rippled outside
  insert  a tray that drops into the frame with CLEAR all round: floor, smooth wall
Both print as they sit, floor on the bed. Every top is flat and faces up (the floor's top, the
rims), so ironing covers them (the shop's rule since the ironing test, 2026-11-22).

    python3 tray_set.py OUT_DIR [--only star]     # STLs per shape, and a parts summary
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import shapely.affinity as aff
import trimesh
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

FLOOR = 1.6         # the frame's floor; the insert's floor too (eight layers)
FRAME_WALL = 3.2    # inside the ripples: eight beads
FRAME_H = 14.0      # the frame's rim above the bed
INSERT_WALL = 1.6   # four beads
INSERT_H = 11.6     # the insert's rim sits FRAME_H - FLOOR - INSERT_H = 0.8 below the frame's
CLEAR = 0.4         # round the insert: a drop-in fit, not a press fit (vertical walls print ~0.1 big)
RIPPLE_A = 2.0      # the ripples stand this far out
RIPPLE_W = 9.0      # about this long each, adjusted so a whole number fits round the outline
ROUND = 4.0         # every corner of an outline is rounded at least this much
RES = 0.25          # sampling along the outline, mm


def rounded(p, r):
    """Round concave and convex corners alike: open then close (shrink, grow, grow, shrink)."""
    return p.buffer(-r, quad_segs=32).buffer(2 * r, quad_segs=32).buffer(-r, quad_segs=32)


def regular_star(n, r_out, r_in, rot=90):
    pts = [((r_out if k % 2 == 0 else r_in) * math.cos(math.radians(rot + 180 * k / n)),
            (r_out if k % 2 == 0 else r_in) * math.sin(math.radians(rot + 180 * k / n))) for k in range(2 * n)]
    return Polygon(pts)


def hull_circles(*cs):
    return unary_union([Point(x, y).buffer(r, quad_segs=32) for x, y, r in cs]).convex_hull


def shapes():
    """Each outline is the insert's cavity in the frame, in mm, centred."""
    s = {}
    s["star"] = rounded(regular_star(5, 86, 44), 9)
    # tree: three tiers, each wider than the one above, on a short trunk
    tiers = [Polygon([(-70, -40), (70, -40), (0, 25)]), Polygon([(-55, -5), (55, -5), (0, 55)]),
             Polygon([(-38, 30), (38, 30), (0, 80)])]
    s["tree"] = rounded(unary_union(tiers + [box(-14, -70, 14, -38)]), 6)
    # mitten: palm, thumb out to the side, a cuff
    palm = hull_circles((0, 20, 46), (0, -20, 44))
    thumb = hull_circles((-44, 0, 18), (-62, 30, 15))
    s["mitten"] = rounded(unary_union([palm, thumb, box(-48, -82, 48, -50)]), 6)
    # bauble: a ball and its cap
    s["bauble"] = rounded(unary_union([Point(0, -10).buffer(72, quad_segs=64), box(-20, 52, 20, 76)]), 4)
    # bell: a flared skirt, a dome, a clapper below the rim
    bell = Polygon([(-78, -40), (78, -40), (64, -26), (46, 10), (40, 40)] +
                   [(40 * math.cos(math.radians(a)), 40 + 40 * math.sin(math.radians(a))) for a in range(0, 181, 5)] +
                   [(-40, 40), (-46, 10), (-64, -26)])
    s["bell"] = rounded(unary_union([bell, Point(0, -52).buffer(14, quad_segs=32)]), 5)
    s["gingerbread"] = gingerbread()
    return s


def gingerbread(scale=3.6):
    """The Tin Clicker's gb_outline() (gingerbread_tin_clicker.scad), scaled up."""
    arm_a, arm_b, leg_a, leg_b = (8, 4.5), (18.5, 8.2), (5.6, -8), (9.2, -19.8)
    cav_w = 16.4   # mx_housing + 0.8 in clicker_lib.scad
    parts = [Point(0, 13).buffer(9.5, quad_segs=32), box(-cav_w / 2, -cav_w / 2, cav_w / 2, cav_w / 2).buffer(1.8),
             hull_circles((-5.5, -7, 4.5), (5.5, -7, 4.5))]
    for sgn in (-1, 1):
        parts.append(hull_circles((sgn * arm_a[0], arm_a[1], 4.4), (sgn * arm_b[0], arm_b[1], 4.2)))
        parts.append(hull_circles((sgn * leg_a[0], leg_a[1], 4.6), (sgn * leg_b[0], leg_b[1], 4.8)))
    g = unary_union(parts).buffer(2, quad_segs=32).buffer(-2, quad_segs=32)   # gb_outline's offset(-2) offset(2)
    return aff.scale(g, scale, scale, origin=(0, 0))


def rippled(p, amp=RIPPLE_A, wave=RIPPLE_W):
    """Push the outline out in rounded scallops: whole ripples round the length, each a half
    sine (|sin|^0.6, so they're full lobes meeting in a crease, as a scalloped pie dish)."""
    ring = LineString(p.exterior.coords)
    L = ring.length
    n = max(8, round(L / wave))
    m = int(L / RES)
    pts = []
    for k in range(m):
        s = L * k / m
        a, b = ring.interpolate(s), ring.interpolate((s + 0.5) % L)
        tx, ty = b.x - a.x, b.y - a.y
        t = math.hypot(tx, ty) or 1.0
        nx, ny = ty / t, -tx / t
        if not p.contains(Point(a.x + nx * 0.05, a.y + ny * 0.05)) is False:   # keep the normal pointing out
            nx, ny = -nx, -ny
        d = amp * abs(math.sin(math.pi * n * s / L)) ** 0.6
        pts.append((a.x + nx * d, a.y + ny * d))
    out = Polygon(pts).buffer(0)
    # the crease between two lobes is sharp: ease it so no wall comes to a knife edge
    return out.buffer(-0.4, quad_segs=16).buffer(0.4, quad_segs=16)


def extrude(poly, h, z=0.0):
    m = trimesh.creation.extrude_polygon(poly, h)
    m.apply_translation([0, 0, z])
    return m


def ring(outer, inner, h, z=0.0):
    return extrude(outer.difference(inner), h, z)


def tray_parts(cav):
    """frame: rippled outer, smooth cavity; insert: cav shrunk by CLEAR."""
    frame_out = rippled(cav.buffer(FRAME_WALL, quad_segs=32))
    frame = trimesh.util.concatenate([extrude(frame_out, FLOOR), ring(frame_out, cav, FRAME_H - FLOOR, FLOOR)])
    frame = boolean_union(frame)
    ins_out = cav.buffer(-CLEAR, quad_segs=32)
    ins_in = ins_out.buffer(-INSERT_WALL, quad_segs=32)
    insert = boolean_union(trimesh.util.concatenate([extrude(ins_out, FLOOR), ring(ins_out, ins_in, INSERT_H - FLOOR, FLOOR)]))
    return frame, insert, frame_out


def boolean_union(m):
    """Merge the stacked extrusions into one watertight body (manifold3d)."""
    import manifold3d as mf
    parts = m.split(only_watertight=False)
    acc = None
    for p in parts:
        q = mf.Manifold(mf.Mesh(vert_properties=np.asarray(p.vertices, np.float32), tri_verts=np.asarray(p.faces, np.uint32)))
        acc = q if acc is None else acc + q
    out = acc.to_mesh()
    return trimesh.Trimesh(out.vert_properties[:, :3], out.tri_verts, process=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--only")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name, cav in shapes().items():
        if a.only and name != a.only:
            continue
        frame, insert, frame_out = tray_parts(cav)
        frame.export(out / f"{name}_frame.stl")
        insert.export(out / f"{name}_insert.stl")
        mnx, mny, mxx, mxy = frame_out.bounds
        summary[name] = {"frame_mm": [round(mxx - mnx, 1), round(mxy - mny, 1), FRAME_H],
                         "insert_mm": [round(v, 1) for v in insert.extents],
                         "frame_watertight": bool(frame.is_watertight), "insert_watertight": bool(insert.is_watertight),
                         "frame_cm3": round(frame.volume / 1000, 1), "insert_cm3": round(insert.volume / 1000, 1)}
        print(name, summary[name])
    (out / "summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
