"""Five Love Lantern forms (2026-10-26, concepts for Scott to pick from).

1 Standing heart   a heart on a plinth, glowing front and back
2 Hex carriage     the Christmas hex lantern's sister: six scenes, heart finial
3 Swan crown       a glowing drum wrapped in a pond at night, two swans on the
                   lid whose necks make a heart
4 Gazebo           an eight-column bandstand, a dancing couple behind the glass
5 Love letter      a standing envelope, flap and wax seal on the glowing front

Every form: battery tealight under it (open base, >= 46 mm across, >= 50 mm
of headroom), panes 0.9 mm so they glow, scenes 1.6 mm out of the pane so
they read dark when lit, names and date raised on the plinth's front.
Parts: frame, glass, art (the scenes), accent (seal, finials, the names).
"""
import math

from shapely import affinity
from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union

import scenes
from geo import M, box, cyl, ext, heart, on_face, prism_y, radial, stroke, text2d

PANE = 0.9          # glowing glass
ART = 1.6           # the scenes, out of the glass
NAMES, DATE = "Emma & James", "02.14.2027"


def names_on(face_origin, angle, z_names, z_date, d0=0.0, w=None):
    """The personalised plaque text, raised 1.2 out of a flat face."""
    t = unary_union([affinity.translate(text2d(NAMES, 5.6), 0, z_names),
                     affinity.translate(text2d(DATE, 3.6), 0, z_date)])
    return on_face(t, face_origin, angle, d0 - 0.01, d0 + 1.2)


def ngon(a, n, rot=0.0):
    """A regular n-gon with apothem a whose first face's normal points to -y."""
    R = a / math.cos(math.pi / n)
    return Polygon([(R * math.sin(math.radians(rot + 180 / n + 360 * k / n)),
                     -R * math.cos(math.radians(rot + 180 / n + 360 * k / n))) for k in range(n)])


def prism_ring(a, n, z0, z1, wall):
    return ext(ngon(a, n).difference(ngon(a - wall, n)), z1 - z0, z0)


# ---- 1 standing heart -------------------------------------------------------------------
def standing_heart():
    PW, PD, PH = 76, 58, 22                          # the plinth
    plinth = box(-PW / 2, -PD / 2, 0, PW / 2, PD / 2, PH) - box(-PW / 2 + 2.4, -PD / 2 + 2.4, -1, PW / 2 - 2.4, PD / 2 - 2.4, PH + 1)
    HW = 108
    hz = 12.0                                        # the heart's point, sunk in the plinth
    H2 = heart(HW, 0, 0)
    b = H2.bounds
    H2 = affinity.translate(H2, 0, hz - b[1])
    inner = H2.buffer(-4.0)
    D = 26                                           # half depth
    outer_p = prism_y(H2, -D, D)
    cavity = prism_y(inner, -D + PANE, D - PANE) + box(-PW / 2 + 2.4, -PD / 2 + 2.4, -1, PW / 2 - 2.4, PD / 2 - 2.4, PH + 1)
    shell = (outer_p - cavity) - box(-200, -200, -50, 200, 200, PH - 0.01)
    glass = shell ^ prism_y(inner, -D - 1, D + 1)
    # the plinth's deck, open only where the heart's hollow meets it
    xs = inner.intersection(sbox(-200, PH - 0.5, 200, PH + 0.5)).bounds
    deck = box(-PW / 2, -PD / 2, PH - 2.4, PW / 2, PD / 2, PH) - box(xs[0], -D + PANE, PH - 3, xs[2], D - PANE, PH + 1)
    frame = (shell - glass) + plinth + deck
    # the scenes, clipped to the glass: the couple on the front, the swans on the back
    pane = inner.buffer(-1.0)
    sw, sh = 60, 72
    front = affinity.translate(scenes.couple_lamppost(sw, sh), 0, PH + 4).intersection(pane)
    back = affinity.translate(scenes.swans_heart(76, 60), 0, PH + 14)
    back = affinity.scale(back, -1, 1, origin=(0, 0)).intersection(pane)
    art = on_face(front, (0, -D), 0, 0, ART)
    art += on_face(affinity.scale(back, -1, 1, origin=(0, 0)), (0, D), 180, 0, ART)
    accent = names_on((0, -PD / 2), 0, 14.5, 6.5)
    return dict(frame=frame, glass=glass, art=art, accent=accent)


# ---- 2 hex carriage ---------------------------------------------------------------------
def hex_carriage():
    a, z0, z1 = 34.0, 15.0, 92.0
    plinth = prism_ring(a + 3, 6, 0, z0, 2.8)
    rail = prism_ring(a + 3.5, 6, z1, z1 + 6, 4.5)
    R = a / math.cos(math.pi / 6)
    posts = M()
    for k in range(6):
        t = math.radians(30 + 60 * k)
        posts += cyl(2.6, z1 - z0 + 0.2, z0 - 0.1).translate([R * math.sin(t), -R * math.cos(t), 0])
    pw = 2 * a * math.tan(math.pi / 6)
    glass = M()
    art = M()
    scs = [scenes.couple_lamppost, scenes.swans_heart, scenes.cottage_heart]
    for k in range(6):
        ang = 60 * k
        t = math.radians(ang)
        o = (a * math.sin(t), -a * math.cos(t))
        glass += on_face(sbox(-pw / 2, z0, pw / 2, z1), o, ang, -PANE, 0)
        w = pw - 6.5
        f = scs[k % 3]
        g = f(w, 64) if f is not scenes.swans_heart else f(w, 52)
        art += on_face(affinity.translate(g, 0, z0 + 3), o, ang, 0, ART)
    roof = cyl(R + 5.0, 40, z1 + 6, 0, fn=6)
    collar = cyl(5, 6, z1 + 40)
    fin = prism_y(affinity.translate(heart(18), 0, z1 + 54), -1.6, 1.6)
    ring = prism_y(affinity.translate(sbox(-1.0, 0, 1.0, 6), 0, z1 + 44), -1.6, 1.6)
    frame = plinth + rail + posts + roof + collar + ring
    accent = names_on((0, -(a + 3)), 0, 9.0, 3.4) + fin
    return dict(frame=frame, glass=glass, art=art, accent=accent)


# ---- 3 swan crown drum ------------------------------------------------------------------
def swan_crown():
    R, z0, z1 = 40.0, 15.0, 80.0
    plinth = cyl(R + 3, z0) - cyl(R - 0.5, z0 + 2, -1)
    glass = cyl(R, z1 - z0, z0, fn=160) - cyl(R - PANE, z1 - z0 + 2, z0 - 1, fn=160)
    rim = cyl(R + 3, 5, z1) - cyl(R - 2.5, 7, z1 - 1)
    lid = cyl(R + 1, 3, z1 + 5) + cyl(R - 4, 4, z1 + 8, R - 14)
    L = 2 * math.pi * R - 6
    art = radial(affinity.translate(scenes.pond_panorama(L, 60), 0, z0 + 2), R, 0, ART, angle=0)
    crown = scenes.swans_heart(74, 64).buffer(0.7)
    crown = crown.difference(sbox(-100, -10, 100, 9.0))              # no water on the crown
    cb = crown.bounds
    crown = affinity.translate(crown, 0, z1 + 11 - cb[1])
    accent = prism_y(crown, -1.8, 1.8)
    t = unary_union([affinity.translate(text2d(NAMES, 5.6), 0, 9.0), affinity.translate(text2d(DATE, 3.4), 0, 3.2)])
    accent += radial(t, R + 3, -0.01, 1.2, angle=0)
    frame = plinth + rim + lid
    return dict(frame=frame, glass=glass, art=art, accent=accent)


# ---- 4 gazebo ---------------------------------------------------------------------------
def gazebo():
    a, z0, z1 = 36.0, 12.0, 80.0
    n = 8
    plinth = prism_ring(a + 6, n, 0, z0, 3.0) + prism_ring(a + 3.5, n, z0 - 0.01, z0 + 3, 3.0)
    R = a / math.cos(math.pi / n)
    cols = M()
    for k in range(n):
        t = math.radians(180 / n + 360 * k / n)
        p = [R * math.sin(t), -R * math.cos(t), 0]
        cols += cyl(2.4, z1 - z0, z0).translate(p) + cyl(3.4, 2.5, z0 + 3).translate(p) + cyl(3.4, 2.5, z1 - 2.5).translate(p)
    pw = 2 * a * math.tan(math.pi / n)
    glass, art = M(), M()
    for k in range(n):
        ang = 360 * k / n
        t = math.radians(ang)
        o = (a * math.sin(t), -a * math.cos(t))
        glass += on_face(sbox(-pw / 2, z0 + 3, pw / 2, z1), o, ang, -PANE, 0)
        g = scenes.dancing_couple(pw - 6, 58) if k % 2 == 0 else \
            affinity.translate(unary_union([heart(9, 0, 36), heart(6, -5, 22), heart(6, 5, 12)]), 0, 0)
        art += on_face(affinity.translate(g, 0, z0 + 4), o, ang, 0, ART)
    eave = prism_ring(a + 6, n, z1, z1 + 4, 8)
    # an ogee dome on eight faces
    prof = Polygon([(0, 0), (a + 6, 0), (a + 4, 4), (a - 4, 12), (a - 14, 22), (14, 30), (6, 36), (2.5, 42), (0, 42)])
    from geo import cs
    dome = M.revolve(cs(prof), n).rotate([0, 0, 180 / n + 90]).translate([0, 0, z1 + 4])
    fin = prism_y(affinity.translate(heart(16), 0, z1 + 52), -1.6, 1.6)
    frame = plinth + cols + eave + dome
    accent = names_on((0, -(a + 6)), 0, 7.4, 2.4) + fin
    return dict(frame=frame, glass=glass, art=art, accent=accent)


# ---- 5 love letter ----------------------------------------------------------------------
def love_letter():
    W, D, z0, z1 = 112.0, 54.0, 12.0, 88.0
    plinth = box(-W / 2 - 4, -D / 2 - 4, 0, W / 2 + 4, D / 2 + 4, z0) - box(-W / 2 + 2, -D / 2 + 2, -1, W / 2 - 2, D / 2 - 2, z0 + 1)
    body = box(-W / 2, -D / 2, z0, W / 2, D / 2, z1)
    cav = box(-W / 2 + 3, -D / 2 + PANE, z0 - 1, W / 2 - 3, D / 2 - PANE, z1 - 3)
    shell = body - cav
    win = box(-W / 2 + 3, -D / 2 - 1, z0 + 3, W / 2 - 3, D / 2 + 1, z1 - 3)
    glass = shell ^ win
    frame = (shell - glass) + plinth
    # the envelope: flap edges from the top corners to the seal, the lower folds
    cx, cy = 0, z0 + (z1 - z0) * 0.46
    lines = unary_union([
        stroke([(-W / 2 + 4, z1 - 4), (cx, cy + 2)], 2.0), stroke([(W / 2 - 4, z1 - 4), (cx, cy + 2)], 2.0),
        stroke([(-W / 2 + 4, z0 + 4), (-W * 0.16, cy - 7)], 1.6), stroke([(W / 2 - 4, z0 + 4), (W * 0.16, cy - 7)], 1.6),
    ])
    stamp = sbox(W / 2 - 24, z1 - 24, W / 2 - 9, z1 - 8).difference(sbox(W / 2 - 22.6, z1 - 22.6, W / 2 - 10.4, z1 - 9.4))
    stamp = stamp.union(heart(8, W / 2 - 16.5, z1 - 16))
    art = on_face(unary_union([lines, stamp]), (0, -D / 2), 0, 0, ART)
    art += on_face(affinity.translate(scenes.couple_lamppost(46, 70), 0, z0 + 3), (0, D / 2), 180, 0, ART)
    seal = on_face(heart(13, cx, cy).buffer(3.2, 32), (0, -D / 2), 0, 0, ART + 1.2)
    seal += on_face(heart(11, cx, cy), (0, -D / 2), 0, ART + 1.2, ART + 2.0)
    accent = names_on((0, -D / 2 - 4), 0, 7.5, 2.6) + seal
    return dict(frame=frame, glass=glass, art=art, accent=accent)


FORMS = {1: ("Standing heart", standing_heart, 30), 2: ("Hex carriage", hex_carriage, 30),
         3: ("Swan crown", swan_crown, 30), 4: ("Gazebo", gazebo, 28), 5: ("Love letter", love_letter, 30)}
