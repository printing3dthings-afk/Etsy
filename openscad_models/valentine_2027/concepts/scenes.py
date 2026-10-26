"""Silhouette scenes for the glowing panels (2026-10-26, concepts).

Each returns a shapely drawing for a panel w wide and h tall, origin at the
panel's bottom centre (u right, v up). On the lanterns these stand out of a
thin glowing pane, so lit from inside they read dark on the glow, the way the
Christmas lantern scenes do. Strokes are kept at 1.3 mm or more.
"""
import math

import numpy as np
from shapely import affinity
from shapely.geometry import Point, Polygon, box as sbox
from shapely.ops import unary_union

from geo import heart, heart_curve, stroke

SW = 1.4   # thinnest stroke


def ground(w, y, amp=1.2):
    u = np.linspace(-w / 2, w / 2, 40)
    top = y + amp * np.sin(u / w * 2 * math.pi * 1.5)
    return Polygon(list(zip(u, top)) + [(w / 2, 0), (-w / 2, 0)])


def figure(x, y, s, dress=False, lean=0.0):
    """A standing person, feet at (x, y), s = height."""
    head = Point(x + lean * s * 0.1, y + s * 0.89).buffer(s * 0.11, 24)
    if dress:
        body = Polygon([(x - s * 0.20, y + s * 0.02), (x + s * 0.20, y + s * 0.02), (x + s * 0.07, y + s * 0.72),
                        (x - s * 0.07, y + s * 0.72)])
    else:
        body = Polygon([(x - s * 0.13, y + s * 0.38), (x + s * 0.13, y + s * 0.38), (x + s * 0.11, y + s * 0.74),
                        (x - s * 0.11, y + s * 0.74)])
        legs = unary_union([stroke([(x - s * 0.06, y), (x - s * 0.05, y + s * 0.40)], s * 0.09),
                            stroke([(x + s * 0.06, y), (x + s * 0.05, y + s * 0.40)], s * 0.09)])
        body = body.union(legs)
    neck = sbox(x - s * 0.04, y + s * 0.70, x + s * 0.04, y + s * 0.80)
    return unary_union([head, body, neck])


def lamppost(x, y, h):
    post = stroke([(x, y), (x, y + h * 0.82)], SW + 0.4)
    base = Polygon([(x - 2.4, y), (x + 2.4, y), (x + 1.2, y + 3.5), (x - 1.2, y + 3.5)])
    head = Polygon([(x - 3.2, y + h * 0.82), (x + 3.2, y + h * 0.82), (x + 4.0, y + h * 0.95), (x - 4.0, y + h * 0.95)])
    cap = Polygon([(x - 4.4, y + h * 0.95), (x + 4.4, y + h * 0.95), (x, y + h)])
    # the lamp's glass left open so it glows in the dark post
    glass = sbox(x - 2.0, y + h * 0.84, x + 2.0, y + h * 0.93)
    return unary_union([post, base, head.difference(glass), cap])


def couple_lamppost(w, h):
    g = [ground(w, 6.0), lamppost(w * 0.25, 5.0, h * 0.86)]
    s = h * 0.48
    g += [figure(-w * 0.12, 5.6, s), figure(w * 0.04, 5.6, s * 0.94, dress=True)]
    g.append(stroke([(-w * 0.12 + s * 0.12, 5.6 + s * 0.55), (w * 0.04 - s * 0.10, 5.6 + s * 0.55)], SW))   # holding hands
    g.append(heart(w * 0.16, -w * 0.04, 5.6 + s * 1.22))
    # falling snow
    for u, v in ((-0.36, 0.86), (-0.28, 0.62), (0.40, 0.70), (0.08, 0.92), (-0.40, 0.40), (0.38, 0.40)):
        g.append(Point(u * w, v * h).buffer(0.9, 12))
    return unary_union(g).intersection(sbox(-w / 2, 0, w / 2, h))


def swans_heart(w, h):
    """Two swans facing, their necks drawing a heart, on rippled water."""
    hw = w * 0.56
    cy = h * 0.58
    # the necks: the heart's two upper lobes, down to the breasts
    neck = heart_curve(hw, 0, cy, t0=0.18, t1=2 * math.pi - 0.18).buffer(SW * 0.85, cap_style=1)
    hb = heart_curve(hw, 0, cy).bounds
    low = hb[1]
    bodies = []
    for sgn in (-1, 1):
        b = Point(sgn * w * 0.20, low + 2.5).buffer(1, 48)
        b = affinity.scale(b, w * 0.20, 5.2)
        tail = Polygon([(sgn * w * 0.30, low + 1.5), (sgn * w * 0.44, low + 9.5), (sgn * w * 0.36, low + 6.0)])
        wing = stroke([(sgn * w * 0.08, low + 5.5), (sgn * w * 0.22, low + 8.2), (sgn * w * 0.34, low + 6.4)], SW)
        bodies += [b, tail, wing]
    # heads where the lobes dip, beaks touching
    heads = [Point(sgn * hw * 0.10, hb[3] - hw * 0.20).buffer(hw * 0.07, 24) for sgn in (-1, 1)]
    beak = sbox(-hw * 0.06, hb[3] - hw * 0.25, hw * 0.06, hb[3] - hw * 0.21)
    water = [stroke([(u, low - 1.0 - 2.4 * k), (u + w * 0.12, low - 1.0 - 2.4 * k)], SW)
             for k in range(3) for u in np.linspace(-w * 0.44 + k * 3, w * 0.30, 3)]
    g = unary_union([neck, *bodies, *heads, beak, *water, heart(w * 0.10, 0, h * 0.92)])
    return g.intersection(sbox(-w / 2, 0, w / 2, h))


def cottage_heart(w, h):
    """A cottage in silhouette whose round window holds a glowing heart."""
    cw, ch = w * 0.70, h * 0.42
    walls = sbox(-cw / 2, 4, cw / 2, 4 + ch)
    roof = Polygon([(-cw / 2 - 3, 4 + ch), (cw / 2 + 3, 4 + ch), (0, 4 + ch + cw * 0.48)])
    chim = sbox(cw * 0.22, 4 + ch + cw * 0.10, cw * 0.32, 4 + ch + cw * 0.42)
    door = sbox(-cw * 0.32, 4, -cw * 0.14, 4 + ch * 0.62)
    win_c = (cw * 0.14, 4 + ch * 0.55)
    win = Point(*win_c).buffer(ch * 0.30, 48)
    hrt = heart(ch * 0.38, win_c[0], win_c[1] - 0.6)
    # the window glows; the heart in it stays dark
    house = unary_union([walls, roof, chim]).difference(door).difference(win).union(hrt)
    mull = stroke([(win_c[0], win_c[1] - ch * 0.30), (win_c[0], win_c[1] - ch * 0.24)], SW)
    house = house.union(mull)
    smoke = [Point(cw * 0.27 + 1.5 * k, 4 + ch + cw * 0.48 + 3.4 * k).buffer(1.2 + 0.3 * k, 16) for k in range(3)]
    g = unary_union([ground(w, 4.5), house, *smoke])
    return g.intersection(sbox(-w / 2, 0, w / 2, h))


def dancing_couple(w, h):
    """A couple dancing under a garland of hearts."""
    s = h * 0.55
    man = figure(-s * 0.13, 5.0, s, lean=-0.5)
    woman = figure(s * 0.13, 5.0, s * 0.94, dress=True, lean=0.5)
    arms = stroke([(-s * 0.06, 5 + s * 0.66), (s * 0.08, 5 + s * 0.70)], SW)
    raised = stroke([(-s * 0.10, 5 + s * 0.62), (-s * 0.30, 5 + s * 0.86)], SW)
    garland = [heart(w * 0.09, u, h * 0.86 - 2.5 * math.cos(u / w * math.pi * 2)) for u in np.linspace(-w * 0.36, w * 0.36, 5)]
    swag = stroke([(u, h * 0.90 - 2.5 * math.cos(u / w * math.pi * 2)) for u in np.linspace(-w * 0.45, w * 0.45, 30)], SW)
    g = unary_union([ground(w, 5.5, 0.5), man, woman, arms, raised, swag, *garland])
    return g.intersection(sbox(-w / 2, 0, w / 2, h))


def pond_panorama(L, h):
    """A long frieze for a drum: moon, reeds, two swans gliding to meet, hearts drifting."""
    g = [ground(L, 5.0, 0.8)]
    for u in (-L * 0.46, -L * 0.42, -L * 0.07, L * 0.30, L * 0.34, L * 0.44):
        for k, (du, top) in enumerate(((0, 0.46), (2.2, 0.36), (-2.0, 0.30))):
            g.append(stroke([(u + du, 4), (u + du * 1.4, h * top)], SW))
            if k == 0:
                g.append(stroke([(u, h * top - 6), (u, h * top)], SW + 1.2))
    for u, sgn in ((-L * 0.22, 1), (L * 0.10, -1)):
        body = affinity.scale(Point(u, 9.5).buffer(1, 48), 13, 5.0)
        tail = Polygon([(u - sgn * 11, 9), (u - sgn * 17, 17), (u - sgn * 13, 12)])
        neck = stroke([(u + sgn * 8, 11), (u + sgn * 12.5, 20), (u + sgn * 10.5, 28), (u + sgn * 12.5, 31)], SW + 0.6)
        head = Point(u + sgn * 13, 31.5).buffer(2.0, 16)
        beak = Polygon([(u + sgn * 14.5, 32.2), (u + sgn * 18, 31.0), (u + sgn * 14.5, 30.4)])
        g += [body, tail, neck, head, beak]
    g.append(heart(9, -L * 0.06, 34))
    g.append(Point(L * 0.22, h * 0.80).buffer(7, 48).difference(Point(L * 0.22 + 3.4, h * 0.82).buffer(6, 48)))
    g += [heart(5.5, u, v) for u, v in ((-L * 0.36, h * 0.74), (-L * 0.15, h * 0.88), (L * 0.40, h * 0.66))]
    for u, v in ((-L * 0.30, h * 0.90), (L * 0.05, h * 0.92), (L * 0.32, h * 0.88), (-L * 0.44, h * 0.84)):
        g.append(Point(u, v).buffer(0.9, 12))
    return unary_union(g).intersection(sbox(-L / 2, 0, L / 2, h))
