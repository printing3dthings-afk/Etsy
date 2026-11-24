"""Christmas trinket trays: a rippled frame and a drop-in insert (2026-11-24).

Scott showed trays like these ("Examples of what I want to have in our catalog") and picked the
rippled-frame-plus-insert direction (2026-11-24): a tray whose outer wall ripples, and a
second, smooth tray in another colour that drops inside it. Each piece is one colour, so it's
two-tone without an AMS, and buyers mix colours.

Our own shapes, not anyone else's: star, tree, mitten, bauble, bell, the Tin Clicker's
gingerbread man (the same outline, scaled up), and from his second round (2026-11-24, "Add 6
more") snowman, stocking, gift box, snowflake, Santa hat and gingerbread house. No shape is
joined to a rectangle: that layout is another maker's MakerWorld exclusive.

Each shape makes two parts, in two sizes (Scott: "Two sizes + scoop"):
  frame   a floor, and a wall that is smooth inside and rippled outside, with one thumb scoop
          in its rim so the insert can be lifted out
  insert  a tray that drops into the frame with CLEAR all round: floor, smooth wall, and
          raised detail on its floor (the gingerbread's face and buttons, the gift's ribbon;
          Scott: "Add raised detail")
  large   as drawn, 131-180 mm across
  small   scaled so the frame is SMALL_MAX across; walls, floors, heights and detail lines
          keep their sizes, only the outline and the detail's layout scale
Both print as they sit, floor on the bed. Every top is flat and faces up (the floor's top, the
detail's tops, the rims), so ironing covers them (the shop's rule since the ironing test).

    python3 tray_set.py OUT_DIR [--only star] [--size large|small]
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import shapely.affinity as aff
import trimesh
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

FLOOR = 1.6         # the frame's floor; the insert's floor too (eight layers)
FRAME_WALL = 3.2    # inside the ripples: eight beads
FRAME_H = 14.0      # the frame's rim above the bed
INSERT_WALL = 1.6   # four beads
INSERT_H = 11.6     # the insert's rim sits FRAME_H - FLOOR - INSERT_H = 0.8 below the frame's
CLEAR = 0.4         # round the insert: a drop-in fit, not a press fit (vertical walls print ~0.1 big)
RIPPLE_A = 2.0      # the ripples stand this far out
RIPPLE_W = 9.0      # about this long each, adjusted so a whole number fits round the outline
RES = 0.25          # sampling along the outline, mm
# raised detail on the insert's floor (DETAIL_STANDARD.md: handled relief >= 1.2 across, a
# separate shape >= 0.8; 0.8 proud is four layers and reads at arm's length)
DET_W = 1.6         # a raised line, four beads
DET_H = 0.8
DET_MARGIN = 2.5    # kept this far in from the insert's inside wall
# the thumb scoop: a round dip in the frame's rim, down to SCOOP_FLOOR above the bed, so a
# finger reaches the insert's side. The insert's rim is at 13.2; 5.0 leaves 8 mm of it to pinch
SCOOP_FLOOR = 5.0
SMALL_MAX = 110.0   # the small frame's longest side, mm


def rounded(p, r):
    """Round concave and convex corners alike: open then close (shrink, grow, grow, shrink)."""
    return p.buffer(-r, quad_segs=32).buffer(2 * r, quad_segs=32).buffer(-r, quad_segs=32)


def regular_star(n, r_out, r_in, rot=90, c=(0, 0)):
    pts = [(c[0] + (r_out if k % 2 == 0 else r_in) * math.cos(math.radians(rot + 180 * k / n)),
            c[1] + (r_out if k % 2 == 0 else r_in) * math.sin(math.radians(rot + 180 * k / n))) for k in range(2 * n)]
    return Polygon(pts)


def hull_circles(*cs):
    return unary_union([Point(x, y).buffer(r, quad_segs=32) for x, y, r in cs]).convex_hull


def arc(cx, cy, r, a0, a1, n=24):
    return LineString([(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                        cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)])


def zigzag(x0, x1, y, amp, n):
    return LineString([(x0 + (x1 - x0) * k / (2 * n), y + (amp if k % 2 else -amp)) for k in range(2 * n + 1)])


def wave(x0, x1, y, amp, n, steps=60):
    return LineString([(x0 + (x1 - x0) * k / steps, y + amp * math.sin(2 * math.pi * n * k / steps)) for k in range(steps + 1)])


def heart(cx, cy, s):
    return unary_union([Point(cx - s * 0.5, cy + s * 0.3).buffer(s * 0.55, quad_segs=24),
                        Point(cx + s * 0.5, cy + s * 0.3).buffer(s * 0.55, quad_segs=24),
                        Polygon([(cx - s * 1.02, cy + s * 0.12), (cx + s * 1.02, cy + s * 0.12), (cx, cy - s * 1.1)])])


def ring(p):
    """A polygon's outline, to be drawn as a raised line."""
    return p.exterior


# ---- the shapes: (cavity outline, detail) in mm, the cavity being the insert's home ----------
# Detail is a list of (geometry, kind): "line" is drawn DET_W wide, "fill" is raised as drawn.
def shapes():
    s = {}
    st = rounded(regular_star(5, 86, 44), 9)
    s["star"] = (st, [(ring(st.buffer(-14)), "line"), (regular_star(4, 12, 4, rot=90), "fill")])

    tiers = [Polygon([(-70, -40), (70, -40), (0, 25)]), Polygon([(-55, -5), (55, -5), (0, 55)]),
             Polygon([(-38, 30), (38, 30), (0, 80)])]
    tree = rounded(unary_union(tiers + [box(-14, -70, 14, -38)]), 6)
    s["tree"] = (tree, [(arc(0, 10, 62, 238, 302), "line"), (arc(0, 40, 44, 236, 304), "line"),
                        (arc(0, 62, 26, 232, 308), "line"),
                        (unary_union([Point(x, y).buffer(3.5) for x, y in
                                      [(-30, -20), (12, -28), (30, -12), (-18, 12), (20, 18), (0, 44)]]), "fill"),
                        (regular_star(5, 8, 3.5, c=(0, 63)), "fill")])

    palm = hull_circles((0, 20, 46), (0, -20, 44))
    thumb = hull_circles((-44, 0, 18), (-62, 30, 15))
    s["mitten"] = (rounded(unary_union([palm, thumb, box(-48, -82, 48, -50)]), 6),
                   [(LineString([(-48, -50), (48, -50)]), "line"), (LineString([(-48, -61), (48, -61)]), "line"),
                    (LineString([(-48, -72), (48, -72)]), "line"), (heart(4, 12, 15), "fill")])

    s["bauble"] = (rounded(unary_union([Point(0, -10).buffer(72, quad_segs=64), box(-20, 52, 20, 76)]), 4),
                   [(LineString([(-20, 56), (20, 56)]), "line"), (wave(-75, 75, 10, 5, 4), "line"),
                    (wave(-75, 75, -30, 5, 4), "line"),
                    (unary_union([Point(x, -10).buffer(3.5) for x in (-45, -22, 0, 22, 45)]), "fill")])

    bell = Polygon([(-78, -40), (78, -40), (64, -26), (46, 10), (40, 40)] +
                   [(40 * math.cos(math.radians(a)), 40 + 40 * math.sin(math.radians(a))) for a in range(0, 181, 5)] +
                   [(-40, 40), (-46, 10), (-64, -26)])
    bow = unary_union([Polygon([(0, 52), (-18, 62), (-18, 42)]), Polygon([(0, 52), (18, 62), (18, 42)]),
                       Point(0, 52).buffer(4.5)])
    s["bell"] = (rounded(unary_union([bell, Point(0, -52).buffer(14, quad_segs=32)]), 5),
                 [(LineString([(-70, -27), (70, -27)]), "line"), (LineString([(-62, -17), (62, -17)]), "line"), (bow, "fill")])

    s["gingerbread"] = gingerbread()

    body = unary_union([Point(0, -38).buffer(46, quad_segs=48), Point(0, 30).buffer(30, quad_segs=48),
                        box(-34, 55, 34, 64), box(-22, 62, 22, 88)])
    s["snowman"] = (rounded(body, 5),
                    [(unary_union([Point(-10, 38).buffer(3.5), Point(10, 38).buffer(3.5)]), "fill"),
                     (Polygon([(-1, 30), (17, 27), (-1, 24)]), "fill"), (arc(0, 30, 14, 215, 325), "line"),
                     (LineString([(-27, 6), (0, 2), (27, 6)]), "line"), (LineString([(-22, 68), (22, 68)]), "line"),
                     (unary_union([Point(0, y).buffer(4) for y in (-18, -38, -58)]), "fill")])

    leg = box(-30, -20, 30, 60)
    foot = hull_circles((0, -30, 30), (48, -42, 27))
    stock = rounded(unary_union([leg, foot, box(-38, 55, 38, 84)]), 6)
    s["stocking"] = (stock, [(LineString([(-38, 55), (38, 55)]), "line"), (arc(0, -30, 20, 180, 270), "line"),
                             (LineString([(52, -15), (60, -68)]), "line"), (heart(0, 70, 7), "fill")])

    giftbox = unary_union([box(-60, -62, 60, 38), Point(-22, 56).buffer(20, quad_segs=32),
                           Point(22, 56).buffer(20, quad_segs=32), Point(0, 44).buffer(10)])
    s["gift box"] = (rounded(giftbox, 5),
                     [(LineString([(-7, -62), (-7, 38)]), "line"), (LineString([(7, -62), (7, 38)]), "line"),
                      (LineString([(-60, -19), (60, -19)]), "line"), (LineString([(-60, -5), (60, -5)]), "line"),
                      (Point(-22, 56).buffer(9).exterior, "line"), (Point(22, 56).buffer(9).exterior, "line")])

    arms, det = [], []
    for k in range(6):
        a = math.radians(90 + 60 * k)
        ca, sa = math.cos(a), math.sin(a)
        arms.append(hull_circles((0, 0, 13), (80 * ca, 80 * sa, 13)))
        for side in (-1, 1):   # a pair of branches on each arm
            b = a + side * math.radians(42)
            arms.append(hull_circles((48 * ca, 48 * sa, 9), (48 * ca + 26 * math.cos(b), 48 * sa + 26 * math.sin(b), 9)))
        det.append((LineString([(20 * ca, 20 * sa), (72 * ca, 72 * sa)]), "line"))
    hexagon = Polygon([(16 * math.cos(math.radians(90 + 60 * k)), 16 * math.sin(math.radians(90 + 60 * k))) for k in range(6)])
    s["snowflake"] = (rounded(unary_union(arms + [Point(0, 0).buffer(30)]), 5), det + [(hexagon.exterior, "line")])

    hat = Polygon([(-62, -30), (62, -30), (40, 20), (52, 52), (58, 62), (40, 66), (18, 46), (-22, 22)])
    santa = unary_union([hat, rounded(box(-72, -58, 72, -26), 8), Point(62, 66).buffer(18, quad_segs=32)])
    s["santa hat"] = (rounded(santa, 6),
                      [(LineString([(-72, -30), (72, -30)]), "line"),
                       (Point(62, 66).buffer(9).exterior, "line"),
                       (unary_union([Point(x, -44).buffer(3) for x in (-50, -25, 0, 25, 50)]), "fill")])

    house = unary_union([box(-60, -72, 60, 8), Polygon([(-76, 4), (76, 4), (0, 80)]), box(28, 30, 48, 80)])
    door = unary_union([box(-14, -72, 14, -40), Point(0, -40).buffer(14)]).intersection(box(-14, -72, 14, -26))
    window = box(18, -40, 44, -16)
    s["gingerbread house"] = (rounded(house, 4),
                              [(door.exterior, "line"), (window.exterior, "line"),
                               (LineString([(31, -40), (31, -16)]), "line"), (LineString([(18, -28), (44, -28)]), "line"),
                               (Point(0, 34).buffer(10).exterior, "line"), (zigzag(-62, 62, 10, 3, 9), "line")])
    return s


def gingerbread(scale=3.6):
    """The Tin Clicker's gb_outline() (gingerbread_tin_clicker.scad), scaled up, with its face,
    buttons and icing at the wrists and ankles."""
    arm_a, arm_b, leg_a, leg_b = (8, 4.5), (18.5, 8.2), (5.6, -8), (9.2, -19.8)
    cav_w = 16.4   # mx_housing + 0.8 in clicker_lib.scad
    parts = [Point(0, 13).buffer(9.5, quad_segs=32), box(-cav_w / 2, -cav_w / 2, cav_w / 2, cav_w / 2).buffer(1.8),
             hull_circles((-5.5, -7, 4.5), (5.5, -7, 4.5))]
    for sgn in (-1, 1):
        parts.append(hull_circles((sgn * arm_a[0], arm_a[1], 4.4), (sgn * arm_b[0], arm_b[1], 4.2)))
        parts.append(hull_circles((sgn * leg_a[0], leg_a[1], 4.6), (sgn * leg_b[0], leg_b[1], 4.8)))
    g = unary_union(parts).buffer(2, quad_segs=32).buffer(-2, quad_segs=32)   # gb_outline's offset(-2) offset(2)
    det = [(unary_union([Point(-3.4, 15).buffer(1.1), Point(3.4, 15).buffer(1.1)]), "fill"),   # eyes (clicker's eyes2d)
           (arc(0, 13.2, 3.6, 215, 325), "line"),                                            # the smile
           (unary_union([Point(0, y).buffer(1.15) for y in (1.0, -2.5, -6.0)]), "fill")]       # gumdrop rows
    for sgn in (-1, 1):   # icing zigzags across each wrist and ankle
        det.append((zigzag_across((sgn * 16.2, 7.6), (sgn * 0.42, -0.91)), "line"))
        det.append((zigzag_across((sgn * 8.6, -17.6), (sgn * 0.95, 0.31)), "line"))
    g = aff.scale(g, scale, scale, origin=(0, 0))
    return g, [(aff.scale(d, scale, scale, origin=(0, 0)), k) for d, k in det]


def zigzag_across(c, u, half=3.2, n=3, amp=0.7):
    """A short zigzag centred on c, running along unit vector u (in clicker units)."""
    ux, uy = u
    nx, ny = -uy, ux
    return LineString([(c[0] + ux * (-half + 2 * half * k / (2 * n)) + nx * (amp if k % 2 else -amp),
                        c[1] + uy * (-half + 2 * half * k / (2 * n)) + ny * (amp if k % 2 else -amp)) for k in range(2 * n + 1)])


def rippled(p, amp=RIPPLE_A, wave_len=RIPPLE_W):
    """Push the outline out in rounded scallops: whole ripples round the length, each a half
    sine (|sin|^0.6, so they're full lobes meeting in a crease, as a scalloped pie dish)."""
    ring_ = LineString(p.exterior.coords)
    L = ring_.length
    n = max(8, round(L / wave_len))
    m = int(L / RES)
    pts = []
    for k in range(m):
        s = L * k / m
        a, b = ring_.interpolate(s), ring_.interpolate((s + 0.5) % L)
        tx, ty = b.x - a.x, b.y - a.y
        t = math.hypot(tx, ty) or 1.0
        nx, ny = ty / t, -tx / t
        if p.contains(Point(a.x + nx * 0.05, a.y + ny * 0.05)):   # keep the normal pointing out
            nx, ny = -nx, -ny
        d = amp * abs(math.sin(math.pi * n * s / L)) ** 0.6
        pts.append((a.x + nx * d, a.y + ny * d))
    out = Polygon(pts).buffer(0)
    # the crease between two lobes is sharp: ease it so no wall comes to a knife edge
    return out.buffer(-0.4, quad_segs=16).buffer(0.4, quad_segs=16)


def scoop_site(cav, half=12.0):
    """Where the thumb scoop goes: the frontmost (lowest y) point among the straightest stretches
    of the outline, `half` mm either side, so the round cut takes an even bite out of the wall.
    A round outline (the bauble) has no straight stretch, so the bar is set by the straightest
    one there is: within 1.5x its bend, or 1.6 mm, whichever is more."""
    ring_ = LineString(cav.exterior.coords)
    L = ring_.length
    cands = []
    for k in range(int(L)):
        s = float(k)
        p0, p, p1 = ring_.interpolate(s - half), ring_.interpolate(s), ring_.interpolate(s + half)
        chord = LineString([p0, p1])
        dev = max(chord.distance(ring_.interpolate(s + d)) for d in np.linspace(-half, half, 9))
        tx, ty = p1.x - p0.x, p1.y - p0.y
        t = math.hypot(tx, ty) or 1.0
        nx, ny = ty / t, -tx / t
        if cav.contains(Point(p.x + nx * 0.5, p.y + ny * 0.5)):
            nx, ny = -nx, -ny
        if cav.contains(Point(p.x - nx * 0.5, p.y - ny * 0.5)) and not cav.contains(Point(p0.x * 0.5 + p1.x * 0.5 - nx * 0.5, p0.y * 0.5 + p1.y * 0.5 - ny * 0.5)):
            continue   # a concave bend: the chord runs outside the cavity
        cands.append((dev, p.y - 0.25 * abs(p.x), (p.x, p.y), (nx, ny)))
    bar = max(1.6, 1.5 * min(c[0] for c in cands))   # 1.6: a bend of r 45 or more (the snowman's body) counts
    best = min((c for c in cands if c[0] <= bar), key=lambda c: c[1])
    return best[2], best[3]


def extrude(poly, h, z=0.0):
    polys = list(poly.geoms) if isinstance(poly, MultiPolygon) else [poly]
    ms = [trimesh.creation.extrude_polygon(q, h) for q in polys if q.area > 0.01]
    m = trimesh.util.concatenate(ms)
    m.apply_translation([0, 0, z])
    return m


def ring_solid(outer, inner, h, z=0.0):
    return extrude(outer.difference(inner), h, z)


def M(m):
    import manifold3d as mf
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def T(man):
    out = man.to_mesh()
    return trimesh.Trimesh(out.vert_properties[:, :3], out.tri_verts, process=True)


def union_all(meshes):
    """Merge stacked extrusions into one watertight body (manifold3d)."""
    acc = None
    for m in meshes:
        for p in m.split(only_watertight=False):
            q = M(p)
            acc = q if acc is None else acc + q
    return acc


def detail_region(cav, det):
    """The raised detail, as one polygon, kept DET_MARGIN in from the insert's inside wall."""
    ins_in = cav.buffer(-CLEAR - INSERT_WALL, quad_segs=32)
    keep = ins_in.buffer(-DET_MARGIN, quad_segs=16)
    parts = []
    for g, kind in det:
        q = g.buffer(DET_W / 2, quad_segs=12) if kind == "line" else g
        parts.append(q)
    raised = unary_union(parts).intersection(keep)
    # drop specks under 0.8 across (DETAIL_STANDARD rule 11) left where a line meets the margin
    if isinstance(raised, MultiPolygon):
        raised = unary_union([q for q in raised.geoms if q.buffer(-0.4).area > 0])
    return raised


def tray_parts(cav, det, scoop_r):
    """frame: rippled outer, smooth cavity, a thumb scoop; insert: cav shrunk by CLEAR, with
    raised detail on its floor."""
    frame_out = rippled(cav.buffer(FRAME_WALL, quad_segs=32))
    frame = union_all([extrude(frame_out, FLOOR), ring_solid(frame_out, cav, FRAME_H - FLOOR, FLOOR)])
    (px, py), (nx, ny) = scoop_site(cav)
    length = 2 * (FRAME_WALL + RIPPLE_A + 4)
    cut = trimesh.creation.cylinder(radius=scoop_r, height=length, sections=96)
    cut.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], [nx, ny, 0]))
    cut.apply_translation([px + nx * (FRAME_WALL / 2), py + ny * (FRAME_WALL / 2), SCOOP_FLOOR + scoop_r])
    frame = T(frame - M(cut))
    ins_out = cav.buffer(-CLEAR, quad_segs=32)
    ins_in = ins_out.buffer(-INSERT_WALL, quad_segs=32)
    raised = detail_region(cav, det)
    insert = T(union_all([extrude(ins_out, FLOOR), ring_solid(ins_out, ins_in, INSERT_H - FLOOR, FLOOR),
                          extrude(raised.buffer(0.01), DET_H + 0.01, FLOOR - 0.01)]))
    return frame, insert, frame_out


def sized(cav, det, size):
    """The small size: outline and detail layout scaled so the frame's longest side is SMALL_MAX."""
    if size == "large":
        return cav, det, 11.0
    mnx, mny, mxx, mxy = cav.buffer(FRAME_WALL + RIPPLE_A).bounds
    f = (SMALL_MAX - 2 * (FRAME_WALL + RIPPLE_A)) / (max(mxx - mnx, mxy - mny) - 2 * (FRAME_WALL + RIPPLE_A))
    return (aff.scale(cav, f, f, origin=(0, 0)), [(aff.scale(g, f, f, origin=(0, 0)), k) for g, k in det], 9.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--only")
    ap.add_argument("--size", choices=["large", "small", "both"], default="both")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sp = out / "summary.json"
    summary = json.loads(sp.read_text()) if sp.exists() else {}
    for name, (cav0, det0) in shapes().items():
        if a.only and name != a.only:
            continue
        for size in (["large", "small"] if a.size == "both" else [a.size]):
            cav, det, scoop_r = sized(cav0, det0, size)
            frame, insert, frame_out = tray_parts(cav, det, scoop_r)
            stem = name.replace(" ", "_") + ("" if size == "large" else "_small")
            frame.export(out / f"{stem}_frame.stl")
            insert.export(out / f"{stem}_insert.stl")
            mnx, mny, mxx, mxy = frame_out.bounds
            summary[stem] = {"frame_mm": [round(mxx - mnx, 1), round(mxy - mny, 1), FRAME_H],
                             "insert_mm": [round(v, 1) for v in insert.extents],
                             "frame_watertight": bool(frame.is_watertight), "insert_watertight": bool(insert.is_watertight),
                             "frame_bodies": len(frame.split(only_watertight=False)),
                             "insert_bodies": len(insert.split(only_watertight=False)),
                             "frame_cm3": round(frame.volume / 1000, 1), "insert_cm3": round(insert.volume / 1000, 1)}
            print(stem, summary[stem], flush=True)
    sp.write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
