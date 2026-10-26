"""Five Chocolate Shop forms for the village (2026-10-26, concepts).

Same scale language as the Christmas Victorian and Gingerbread buildings:
about 52 mm square, an 8 mm snowy base, hollow and open underneath over a
46 mm battery tealight, windows glazed thin so they glow. Every form has heart
windows, a raised CHOCOLATES sign, and a display window or striped awning.

1 Victorian bay      brick, a canted bay display window under a striped
                     awning, slate mansard with a heart dormer
2 Chocolate box      gingerbread walls under a lid tied with a ribbon and bow
3 Truffle turret     a gabled shop with a round corner turret capped by a
                     chocolate-kiss cupola
4 Parisian           a narrow three-storey chocolatier, arched display window,
                     heart balcony, mansard with round heart windows
5 Cocoa cottage      half-timbered, steep roof, bay window, big chimney
                     puffing a heart, hanging sign

Parts: body (walls), roof, trim (white: base, frames, icing), accent (red:
awnings, ribbon, hearts, the sign's letters), glass (the glowing panes).
"""
import math

from shapely import affinity
from shapely.geometry import Point, Polygon, box as sbox
from shapely.ops import unary_union

from geo import M, arch, box, cs, cyl, ext, heart, on_face, prism_x, prism_y, stroke, text2d

PANE = 0.9
T = 1.8                 # walls
FACES = {0: lambda w, d: (0, -d / 2), 90: lambda w, d: (w / 2, 0), 180: lambda w, d: (0, d / 2),
         270: lambda w, d: (-w / 2, 0)}


def snow_base(w=66, d=66, h=7.0):
    g = sbox(-w / 2, -d / 2, w / 2, d / 2).buffer(-6).buffer(6, 24)
    drift = [Point(-w * 0.36, d * 0.30).buffer(5), Point(w * 0.38, -d * 0.12).buffer(4)]
    base = ext(g, h) + ext(unary_union(drift), h + 2.2)
    return base - box(-24, -24, -1, 24, 24, h + 5)


def shell(w, d, z0, z1):
    return box(-w / 2, -d / 2, z0, w / 2, d / 2, z1) - box(-w / 2 + T, -d / 2 + T, z0 - 1, w / 2 - T, d / 2 - T, z1 + 1)


class Shop:
    """Collects the parts while windows and details are cut into the walls."""

    def __init__(self, w, d):
        self.w, self.d = w, d
        self.cut = M()
        self.p = {k: M() for k in ("body", "roof", "trim", "accent", "glass")}

    def face(self, ang):
        return FACES[ang](self.w, self.d)

    def window(self, ang, g, frame=1.4, bars=None, out=1.0):
        """A glazed opening of shape g (u along the face, v up), with a white
        frame round it and optional bars (also white, standing out of the pane)."""
        o = self.face(ang)
        self.cut += on_face(g, o, ang, -T - 1, 1)
        self.p["glass"] += on_face(g.buffer(0.3), o, ang, -0.6 - PANE, -0.6)
        self.p["trim"] += on_face(g.buffer(frame).difference(g), o, ang, -0.2, out)
        if bars is not None:
            self.p["trim"] += on_face(bars.intersection(g), o, ang, -0.7, 0.3)

    def relief(self, part, ang, g, d0=0.0, d1=1.0):
        self.p[part] += on_face(g, self.face(ang), ang, d0, d1)

    def sign(self, ang, text, v, w, h=7.0, letter=4.2):
        board = sbox(-w / 2, v - h / 2, w / 2, v + h / 2).buffer(0.8, 8)
        self.relief("trim", ang, board, 0, 1.2)
        self.relief("accent", ang, affinity.translate(text2d(text, letter), 0, v), 1.19, 2.2)

    def done(self):
        self.p["body"] = self.p["body"] - self.cut
        for k in ("trim", "accent", "roof"):
            self.p[k] = self.p[k] - self.p["glass"]
        return self.p


def heart_bars(g):
    b = g.bounds
    cx = (b[0] + b[2]) / 2
    return unary_union([sbox(cx - 0.55, b[1], cx + 0.55, b[3]), sbox(b[0], (b[1] + b[3]) / 2 - 0.55, b[2], (b[1] + b[3]) / 2 + 0.55)])


def awning(x0, x1, y_wall, z_top, depth=9.0, drop=7.0, n=7, scallop=True):
    """A striped awning on the front wall (y = y_wall), its stripes alternating
    accent / trim; returns (accent, trim)."""
    prof = Polygon([(y_wall + 0.5, z_top), (y_wall - depth, z_top - drop), (y_wall - depth, z_top - drop - 1.2),
                    (y_wall + 0.5, z_top - 1.2)])
    acc, tri = M(), M()
    step = (x1 - x0) / n
    for i in range(n):
        piece = prism_x(prof, x0 + i * step, x0 + (i + 1) * step)
        if scallop:
            sc = Point(0, 0).buffer(step / 2, 24).intersection(sbox(-step, -step, step, 0))
            sc = affinity.translate(sc, x0 + (i + 0.5) * step, z_top - drop)
            piece += prism_y(sc, y_wall - depth - 0.6, y_wall - depth + 0.6)
        if i % 2 == 0:
            acc += piece
        else:
            tri += piece
    return acc, tri


# ---- 1 Victorian bay ---------------------------------------------------------------------
def victorian_bay():
    w, d, z0, H = 52.0, 50.0, 6.0, 62.0
    s = Shop(w, d)
    s.p["trim"] += snow_base()
    s.p["body"] += shell(w, d, z0, H)
    # the canted bay: three glazed faces standing 7 out of the front
    by, bw, bz0, bz1 = -d / 2, 34.0, z0 + 3, z0 + 26
    bay = Polygon([(-bw / 2, 0), (bw / 2, 0), (bw / 2 - 6, -7), (-bw / 2 + 6, -7)])
    bay_solid = ext(affinity.translate(bay, 0, by), bz1 - bz0, bz0)
    s.p["trim"] += bay_solid - ext(affinity.translate(bay.buffer(-1.2), 0, by), bz1 - bz0 + 2, bz0 - 1)
    s.cut += box(-bw / 2 + 1.5, -d / 2 - 1, bz0 + 2, bw / 2 - 1.5, -d / 2 + T + 1, bz1 - 1)
    s.p["trim"] = s.p["trim"] - box(-bw / 2 + 1.5, -d / 2 - 1.3, bz0 + 2, bw / 2 - 1.5, -d / 2 + T + 1, bz1 - 1)   # the bay opens into the shop
    # the bay's glass: its three faces
    g_front = sbox(-bw / 2 + 7.5, bz0 + 2, bw / 2 - 7.5, bz1 - 2)
    s.p["glass"] += on_face(g_front, (0, by - 7), 0, -1.2 - 0.1, -1.2 + PANE)
    s.cut += on_face(g_front, (0, by - 7), 0, -2, 1)
    side_len = math.hypot(6, 7)
    for sgn, ang in ((-1, -math.degrees(math.atan2(6, 7))), (1, math.degrees(math.atan2(6, 7)))):
        cxy = (sgn * (bw / 2 - 3), by - 3.5)
        gg = sbox(-side_len / 2 + 1.6, bz0 + 2, side_len / 2 - 1.6, bz1 - 2)
        s.p["glass"] += on_face(gg, cxy, ang, -1.3, -1.3 + PANE)
        s.p["trim"] = s.p["trim"] - on_face(gg, cxy, ang, -2, 1)
    s.p["trim"] = s.p["trim"] - on_face(g_front, (0, by - 7), 0, -2, 1)
    # hearts on the display glass
    hearts = unary_union([heart(6, u, bz0 + 12) for u in (-6, 0, 6)] + [heart(4, u, bz0 + 18) for u in (-3, 3)])
    s.p["accent"] += on_face(hearts, (0, by - 7), 0, -1.2 + PANE, -1.2 + PANE + 1.0)
    acc, tri = awning(-bw / 2 - 2, bw / 2 + 2, -d / 2, bz1 + 9, depth=12, drop=7)
    s.p["accent"] += acc
    s.p["trim"] += tri
    s.sign(0, "CHOCOLATES", H - 22, 40)
    # door at the side of the bay, upper windows with heart transoms
    door = affinity.translate(arch(6.5, 17), w / 2 - 4.6, z0)
    s.relief("roof", 0, door, -0.6, 0.6)
    for u in (-13, 13):
        g = affinity.translate(arch(9, 14), u, H - 16)
        s.window(0, g, bars=heart_bars(g))
    for ang in (90, 270):
        s.window(ang, affinity.translate(heart(14), 0, 26))
        s.window(ang, affinity.translate(arch(10, 15), 0, H - 18), bars=heart_bars(affinity.translate(arch(10, 15), 0, H - 18)))
    s.window(180, affinity.translate(heart(16), 0, 30))
    # mansard roof, a heart dormer, a chimney
    roof = M.extrude(cs(sbox(-w / 2 - 2, -d / 2 - 2, w / 2 + 2, d / 2 + 2)), 16, 0, 0, (0.62, 0.6)).translate([0, 0, H])
    roof += M.extrude(cs(sbox(-w / 2 * 0.62, -d / 2 * 0.6, w / 2 * 0.62, d / 2 * 0.6)), 8, 0, 0, (0.3, 0.3)).translate([0, 0, H + 16])
    roof -= box(-w / 2 + T + 1, -d / 2 + T + 1, H - 1, w / 2 - T - 1, d / 2 - T - 1, H + 3)
    dormer = box(-7, -d / 2 + 1, H + 2, 7, -d / 2 + 12, H + 15)
    droof = prism_x(Polygon([(-d / 2 - 0.5, H + 15), (-d / 2 + 12, H + 15), (-d / 2 + 12, H + 21)]), -8, 8)
    s.p["roof"] += roof + droof
    s.p["body"] += dormer
    hd = affinity.translate(heart(9), 0, H + 8.5)
    s.cut += on_face(hd, (0, -d / 2 + 1), 0, -3, 1)
    s.p["glass"] += on_face(hd.buffer(0.3), (0, -d / 2 + 1), 0, -1.6, -0.7)
    s.p["trim"] += on_face(hd.buffer(1.2).difference(hd), (0, -d / 2 + 1), 0, -0.2, 0.8)
    s.p["roof"] += box(12, 6, H + 4, 19, 13, H + 30)
    s.p["trim"] += box(11.4, 5.4, H + 30, 19.6, 13.6, H + 32)
    return s.done()


# ---- 2 chocolate box ---------------------------------------------------------------------
def chocolate_box():
    w, d, z0, H = 54.0, 54.0, 6.0, 52.0
    s = Shop(w, d)
    s.p["trim"] += snow_base()
    s.p["body"] += shell(w, d, z0, H)
    # icing piping on every edge
    for x in (-w / 2, w / 2):
        for y in (-d / 2, d / 2):
            s.p["trim"] += cyl(1.6, H - z0, z0).translate([x, y, 0])
    for z in (z0 + 1, H - 1):
        s.p["trim"] += box(-w / 2 - 1.2, -d / 2 - 1.2, z - 1, w / 2 + 1.2, d / 2 + 1.2, z + 1) - box(-w / 2 + 1, -d / 2 + 1, z - 2, w / 2 - 1, d / 2 - 1, z + 2)
    # the lid: overhanging, a ribbon crossing it and down the walls, a bow
    LH = 11
    s.p["roof"] += box(-w / 2 - 2.5, -d / 2 - 2.5, H, w / 2 + 2.5, d / 2 + 2.5, H + LH) - box(-w / 2 + 2, -d / 2 + 2, H - 1, w / 2 - 2, d / 2 - 2, H + LH - 3)
    RW = 7
    s.p["accent"] += box(-RW / 2, -d / 2 - 3.4, H - 0.01, RW / 2, d / 2 + 3.4, H + LH + 0.9)
    s.p["accent"] += box(-w / 2 - 3.4, -RW / 2, H - 0.01, w / 2 + 3.4, RW / 2, H + LH + 0.9)
    for ang in (90, 270, 180):
        s.relief("accent", ang, sbox(-RW / 2, z0 + 2, RW / 2, H), 0, 1.0)
    loop = Point(0, 0).buffer(1, 48)
    for sgn in (-1, 1):
        L = affinity.scale(loop, 10, 6.5)
        L = affinity.rotate(L, sgn * 28, origin=(0, 0))
        L = affinity.translate(L, sgn * 9, 7).difference(affinity.translate(affinity.scale(Point(0, 0).buffer(1, 48), 6, 3.2), sgn * 9, 7))
        s.p["accent"] += prism_y(affinity.translate(L, 0, H + LH), -3, 3)
        tail = Polygon([(sgn * 2, 0), (sgn * 9, -9), (sgn * 6, -10), (sgn * 0.5, -1)])
        s.p["accent"] += prism_y(affinity.translate(tail, 0, H + LH + 4), -2.4, 2.4)
    s.p["accent"] += prism_y(affinity.translate(Point(0, 7).buffer(3.4, 24), 0, H + LH), -3.4, 3.4)
    # heart windows that glow, a door, the sign
    for ang in (0, 90, 180, 270):
        for u in ((-14, 14) if ang != 0 else (-15, 15)):
            g = affinity.translate(heart(12), u, 30 if ang else 32)
            s.window(ang, g, frame=1.6)
    door = affinity.translate(arch(11, 21), 0, z0)
    s.relief("roof", 0, door, -0.6, 0.6)
    s.relief("trim", 0, door.buffer(1.4).difference(door).intersection(sbox(-20, z0, 20, 60)), 0, 1.2)
    s.relief("accent", 0, heart(4, 0, z0 + 13), 0.6, 1.4)
    s.sign(0, "CHOCOLATES", 44, 34, h=6.4, letter=3.6)
    return s.done()


# ---- 3 truffle turret --------------------------------------------------------------------
def truffle_turret():
    w, d, z0, H = 50.0, 48.0, 6.0, 46.0
    s = Shop(w, d)
    s.p["trim"] += snow_base()
    s.p["body"] += shell(w, d, z0, H)
    # side-gabled roof
    s.p["roof"] += prism_x(Polygon([(-d / 2 - 3, H - 0.5), (d / 2 + 3, H - 0.5), (0, H + 22)]), -w / 2 - 2, w / 2 + 2) - \
        prism_x(Polygon([(-d / 2 + 2, H - 1), (d / 2 - 2, H - 1), (0, H + 18)]), -w / 2 + 2, w / 2 - 2)
    for x in (-w / 2, w / 2):
        s.p["body"] += prism_x(Polygon([(-d / 2, H - 0.5), (d / 2, H - 0.5), (0, H + 19)]), x - (T if x > 0 else 0), x + (0 if x > 0 else T))
    # the corner turret
    tx, ty, tr = -w / 2 + 3, -d / 2 + 3, 12.0
    tower = cyl(tr, 70 - z0, z0).translate([tx, ty, 0]) - cyl(tr - T, 72, z0 - 1).translate([tx, ty, 0])
    s.p["body"] += tower
    s.cut += cyl(tr - 0.5, 80, z0 - 1).translate([tx, ty, 0]) - tower
    kiss = Polygon([(0, 0), (tr + 2.5, 0), (tr + 1.5, 4), (tr - 3, 12), (5, 21), (1.8, 27), (0.6, 33), (0, 33)])
    s.p["roof"] += M.revolve(cs(kiss), 96).translate([tx, ty, 70])
    s.p["trim"] += prism_y(affinity.translate(Polygon([(0, 0), (6, 3), (6, 5), (0, 2.5)]), tx, 70 + 31), ty - 0.6, ty + 0.6)
    s.p["trim"] += cyl(tr + 1.2, 2.4, 68).translate([tx, ty, 0])
    for k, z in enumerate((22, 42, 58)):
        a = math.radians(-45)
        o = (tx + (tr) * math.sin(a), ty - tr * math.cos(a))
        g = affinity.translate(heart(8.5), 0, z)
        s.cut += on_face(g, o, -45, -T - 2, 2)
        s.p["glass"] += on_face(g.buffer(0.3), o, -45, -1.2, -1.2 + PANE)
        s.p["trim"] += on_face(g.buffer(1.2).difference(g), o, -45, -0.4, 0.8)
    # the shopfront: display window with heart bars, striped awning, sign, door
    g = sbox(-6, z0 + 4, 18, z0 + 22)
    bars = unary_union([sbox(5.45, z0 + 4, 6.55, z0 + 22)] + [heart(5, u, z0 + 13).boundary.buffer(0.6) for u in (0, 12)])
    s.window(0, g, bars=bars)
    acc, tri = awning(-8, 22, -d / 2, z0 + 31, depth=9, drop=6, n=6)
    s.p["accent"] += acc
    s.p["trim"] += tri
    s.sign(0, "CHOCOLATES", z0 + 36, 30, h=6.0, letter=3.6)
    door = affinity.translate(arch(8, 18), w / 2 - 7, z0)
    s.relief("roof", 0, door, -0.6, 0.6)
    s.window(90, affinity.translate(heart(14), 0, 26))
    s.window(180, affinity.translate(heart(14), -10, 26))
    s.window(180, affinity.translate(heart(14), 10, 26))
    s.window(270, affinity.translate(heart(12), 6, 26))
    return s.done()


# ---- 4 Parisian -------------------------------------------------------------------------
def parisian():
    w, d, z0, H = 46.0, 48.0, 6.0, 76.0
    s = Shop(w, d)
    s.p["trim"] += snow_base()
    s.p["body"] += shell(w, d, z0, H)
    for z in (z0 + 28, z0 + 48):
        s.p["trim"] += box(-w / 2 - 1, -d / 2 - 1, z, w / 2 + 1, d / 2 + 1, z + 1.6) - box(-w / 2 + 1, -d / 2 + 1, z - 1, w / 2 - 1, d / 2 - 1, z + 3)
    g = affinity.translate(arch(26, 22), 0, z0 + 2)
    bars = unary_union([sbox(-0.55, z0, 0.55, z0 + 30)] + [heart(6, u, z0 + 10) for u in (-6.5, 6.5)] +
                       [sbox(-14, z0 + 15, 14, z0 + 16.1)])
    s.window(0, g, bars=bars)
    acc, tri = awning(-16, 16, -d / 2, z0 + 27.5, depth=8, drop=4.5, n=8)
    s.p["accent"] += acc
    s.p["trim"] += tri
    s.sign(0, "CHOCOLATES", z0 + 33.5, 36, h=6.0, letter=3.6)
    # the balcony: a slab and a railing of hearts
    s.p["trim"] += box(-17, -d / 2 - 6, z0 + 48, 17, -d / 2, z0 + 49.6)
    rail = unary_union([sbox(-17, 0, 17, 1.4), sbox(-17, 6.6, 17, 8)] + [heart(5, u, 4).boundary.buffer(0.55) for u in range(-14, 15, 7)]
                       + [sbox(u - 0.6, 0, u + 0.6, 8) for u in (-17, 17)])
    s.p["accent"] += on_face(affinity.translate(rail, 0, z0 + 49.6), (0, -d / 2 - 5), 0, 0, 1.2)
    for u in (-11, 11):
        g = affinity.translate(arch(8, 15), u, z0 + 50)
        s.window(0, g, bars=heart_bars(g))
    for ang in (90, 270, 180):
        for z in (z0 + 10, z0 + 33, z0 + 52):
            g = affinity.translate(arch(8, 13), 0, z)
            s.window(ang, g, bars=heart_bars(g) if z > z0 + 30 else None)
    roof = M.extrude(cs(sbox(-w / 2 - 1.5, -d / 2 - 1.5, w / 2 + 1.5, d / 2 + 1.5)), 18, 0, 0, (0.78, 0.8)).translate([0, 0, H])
    roof += M.extrude(cs(sbox(-w / 2 * 0.78, -d / 2 * 0.8, w / 2 * 0.78, d / 2 * 0.8)), 6, 0, 0, (0.4, 0.4)).translate([0, 0, H + 18])
    roof -= box(-w / 2 + 3, -d / 2 + 3, H - 1, w / 2 - 3, d / 2 - 3, H + 3)
    s.p["roof"] += roof
    for u in (-9, 9):
        c = Point(u, H + 8.5).buffer(4.2, 48)
        o = (0, -d / 2 + 1.5)
        s.p["roof"] = s.p["roof"] - on_face(c, o, 0, -4, 3)
        s.p["glass"] += on_face(c.buffer(0.3), o, 0, -2.0, -2.0 + PANE)
        s.p["trim"] += on_face(c.buffer(1.3).difference(c), o, 0, -0.6, 1.4)
        s.p["accent"] += on_face(heart(4.4, u, H + 8.3), o, 0, -2.0 + PANE, -2.0 + PANE + 1.0)
    for x in (-10, 10):
        s.p["body"] += box(x - 3, 8, H + 6, x + 3, 14, H + 26)
    return s.done()


# ---- 5 cocoa cottage ---------------------------------------------------------------------
def cocoa_cottage():
    w, d, z0, H = 52.0, 46.0, 6.0, 40.0
    s = Shop(w, d)
    s.p["trim"] += snow_base()
    s.p["body"] += shell(w, d, z0, H)
    # half timbering on the walls (roof colour)
    beams = unary_union([sbox(-26, z0, -24, H), sbox(24, z0, 26, H), sbox(-26, H - 2, 26, H), sbox(-26, z0 + 18, 26, z0 + 20),
                         stroke([(-24, z0 + 20), (-14, H - 2)], 1.8), stroke([(24, z0 + 20), (14, H - 2)], 1.8)])
    for ang in (90, 270, 180):
        s.relief("roof", ang, beams.intersection(sbox(-d / 2 if ang in (90, 270) else -w / 2, 0,
                                                       d / 2 if ang in (90, 270) else w / 2, 100)), 0, 0.9)
    s.relief("roof", 0, beams.difference(sbox(-12, z0, 12, z0 + 30)), 0, 0.9)
    # steep front-gabled roof
    s.p["roof"] += prism_y(Polygon([(-w / 2 - 3, H - 0.5), (w / 2 + 3, H - 0.5), (0, H + 34)]), -d / 2 - 3, d / 2 + 3) - \
        prism_y(Polygon([(-w / 2 + 2, H - 1), (w / 2 - 2, H - 1), (0, H + 29)]), -d / 2 + 2, d / 2 - 2)
    for y, a in ((-d / 2, 0), (d / 2, 180)):
        s.p["body"] += prism_y(Polygon([(-w / 2, H - 0.5), (w / 2, H - 0.5), (0, H + 31)]), y - (0 if y < 0 else T), y + (T if y < 0 else 0))
    # bay window with heart panes, door, gable heart window
    g = sbox(-11, z0 + 6, 11, z0 + 22)
    bars = unary_union([sbox(-0.55, z0 + 6, 0.55, z0 + 22), sbox(-11, z0 + 13.45, 11, z0 + 14.55)] +
                       [heart(5, u, z0 + 18).boundary.buffer(0.55) for u in (-5.5, 5.5)])
    s.window(0, g, bars=bars)
    s.p["trim"] += box(-13, -d / 2 - 5, z0 + 4, 13, -d / 2, z0 + 6)
    s.p["roof"] += prism_x(Polygon([(-d / 2 + 0.5, z0 + 24), (-d / 2 - 6, z0 + 22), (-d / 2 - 6, z0 + 23.5), (-d / 2 + 0.5, z0 + 26)]), -13, 13)
    door = affinity.translate(arch(8, 17), w / 2 - 8, z0)
    s.relief("roof", 0, door, -0.6, 0.6)
    s.window(0, affinity.translate(heart(11), 0, H + 12))
    for ang in (90, 270):
        for u in (-10, 10):
            g = sbox(u - 4, z0 + 8, u + 4, z0 + 16)
            s.window(ang, g, bars=heart_bars(g))
    s.window(180, affinity.translate(heart(13), 0, 24))
    # the chimney puffing a heart
    s.p["body"] += box(10, 4, H + 8, 18, 12, H + 34)
    s.p["trim"] += box(9.4, 3.4, H + 34, 18.6, 12.6, H + 36)
    puff = unary_union([Point(14, H + 40).buffer(2.6, 24), Point(16, H + 45).buffer(3, 24), heart(10, 19, H + 54)])
    s.p["trim"] += prism_y(puff, 6.5, 9.5)
    # the hanging sign on its bracket
    s.p["roof"] += box(-w / 2 - 0.5, -d / 2 - 14, H - 6, -w / 2 + 1.5, -d / 2, H - 4.6)
    sign = sbox(-w / 2 - 1.2, -d / 2 - 13, -w / 2 + 0.6, -d / 2 - 1)
    board = prism_x(affinity.translate(sbox(-6, -4, 6, 4), -d / 2 - 7, H - 12), -w / 2 - 0.9, -w / 2 + 0.9)
    s.p["trim"] += board
    s.p["accent"] += on_face(affinity.translate(heart(6.5), 0, H - 12), (-w / 2 - 0.9, -d / 2 - 7), 270, 0, 0.8)
    s.p["accent"] += on_face(affinity.translate(heart(6.5), 0, H - 12), (-w / 2 + 0.9, -d / 2 - 7), 90, 0, 0.8)
    s.sign(0, "CHOCOLATES", z0 + 28, 30, h=6, letter=3.6)
    return s.done()


PAL = {1: {"body": "#A8483A", "roof": "#2E3440"}, 2: {"body": "#B9783F", "roof": "#5A3825"},
       3: {"body": "#E9B7BC", "roof": "#5A3825"}, 4: {"body": "#EADBC8", "roof": "#3B4250"},
       5: {"body": "#F1E7DA", "roof": "#4A3328"}}
FORMS = {1: ("Victorian bay", victorian_bay, 22), 2: ("Chocolate box", chocolate_box, 22),
         3: ("Truffle turret", truffle_turret, 22), 4: ("Parisian", parisian, 24), 5: ("Cocoa cottage", cocoa_cottage, 22)}
