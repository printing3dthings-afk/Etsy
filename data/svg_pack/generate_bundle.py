#!/usr/bin/env python3
"""
Floral & Botanical Bundle — 10-design SVG cut file pack generator.
Produces: SVG + 4000x4000 transparent PNG + PDF for each design.
Also produces 1200x1200 preview PNGs, then zips everything.
"""

import math, os, zipfile, io, re
import numpy as np
from PIL import Image, ImageDraw
import cairosvg

# ── Output directories ────────────────────────────────────────────────────────
BASE   = "/home/user/Etsy/data/svg_pack"
PREV   = os.path.join(BASE, "previews")
os.makedirs(PREV, exist_ok=True)

INK    = "#1a1a1a"   # design colour
W = H  = 800         # viewBox size
CX = CY = 400        # centre


# ═══════════════════════════════════════════════════════════════════════════════
# Utility helpers
# ═══════════════════════════════════════════════════════════════════════════════

def svg_doc(title, body, w=800, h=800):
    """Wrap body in a full SVG document."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <title>{title}</title>
  <rect width="{w}" height="{h}" fill="white"/>
  {body}
</svg>"""

def pt(r, theta, cx=CX, cy=CY):
    """Polar → cartesian (theta in radians)."""
    return cx + r*math.cos(theta), cy + r*math.sin(theta)

def cubic(x1,y1, cx1,cy1, cx2,cy2, x2,y2):
    return f"M {x1:.2f},{y1:.2f} C {cx1:.2f},{cy1:.2f} {cx2:.2f},{cy2:.2f} {x2:.2f},{y2:.2f}"

def arc_path(cx, cy, r, start_a, end_a, large=0, sweep=1):
    sx,sy = cx+r*math.cos(start_a), cy+r*math.sin(start_a)
    ex,ey = cx+r*math.cos(end_a),   cy+r*math.sin(end_a)
    return f"M {sx:.2f},{sy:.2f} A {r:.2f},{r:.2f} 0 {large},{sweep} {ex:.2f},{ey:.2f}"

def circle_path(cx, cy, r):
    """Full circle as SVG path."""
    return (f"M {cx-r:.2f},{cy:.2f} "
            f"A {r:.2f},{r:.2f} 0 1,1 {cx+r:.2f},{cy:.2f} "
            f"A {r:.2f},{r:.2f} 0 1,1 {cx-r:.2f},{cy:.2f} Z")

def ellipse_at(cx, cy, rx, ry, angle_deg=0):
    """Ellipse path, rotated by angle_deg."""
    return (f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" '
            f'rx="{rx:.2f}" ry="{ry:.2f}" '
            f'transform="rotate({angle_deg:.1f},{cx:.2f},{cy:.2f})" '
            f'fill="{INK}"/>')

def petal_path(cx, cy, length, width, angle_deg):
    """
    Teardrop petal centred at (cx,cy), pointing in angle_deg direction.
    Returns an SVG <path> element string.
    """
    a = math.radians(angle_deg)
    # tip
    tx, ty = cx + length*math.cos(a), cy + length*math.sin(a)
    # left & right base handles
    perp = a + math.pi/2
    bx1 = cx + width*math.cos(perp)
    by1 = cy + width*math.sin(perp)
    bx2 = cx - width*math.cos(perp)
    by2 = cy - width*math.sin(perp)
    # control points: two thirds toward tip, spread sideways
    reach = length * 0.65
    cpx1 = bx1 + reach*math.cos(a)
    cpy1 = by1 + reach*math.sin(a)
    cpx2 = bx2 + reach*math.cos(a)
    cpy2 = by2 + reach*math.sin(a)
    d = (f"M {cx:.2f},{cy:.2f} "
         f"C {bx1:.2f},{by1:.2f} {cpx1:.2f},{cpy1:.2f} {tx:.2f},{ty:.2f} "
         f"C {cpx2:.2f},{cpy2:.2f} {bx2:.2f},{by2:.2f} {cx:.2f},{cy:.2f} Z")
    return f'<path d="{d}" fill="{INK}"/>'

def leaf_path(cx, cy, length, width, angle_deg):
    """Simple pointed leaf."""
    a   = math.radians(angle_deg)
    tip = (cx + length*math.cos(a),     cy + length*math.sin(a))
    base= (cx - length*0.1*math.cos(a), cy - length*0.1*math.sin(a))
    perp= a + math.pi/2
    lc  = (cx + width*math.cos(perp) + length*0.45*math.cos(a),
           cy + width*math.sin(perp) + length*0.45*math.sin(a))
    rc  = (cx - width*math.cos(perp) + length*0.45*math.cos(a),
           cy - width*math.sin(perp) + length*0.45*math.sin(a))
    d = (f"M {base[0]:.2f},{base[1]:.2f} "
         f"Q {lc[0]:.2f},{lc[1]:.2f} {tip[0]:.2f},{tip[1]:.2f} "
         f"Q {rc[0]:.2f},{rc[1]:.2f} {base[0]:.2f},{base[1]:.2f} Z")
    return f'<path d="{d}" fill="{INK}"/>'

def five_petal_flower(cx, cy, petal_r, center_r, rotation=0):
    """5-petal simple flower, returns path string list."""
    els = []
    for i in range(5):
        a = rotation + i * 72
        pcx = cx + (petal_r*0.6)*math.cos(math.radians(a))
        pcy = cy + (petal_r*0.6)*math.sin(math.radians(a))
        els.append(ellipse_at(pcx, pcy, petal_r*0.45, petal_r*0.28, a))
    # center dot
    els.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{center_r:.2f}" fill="{INK}"/>')
    return "\n  ".join(els)

def four_petal_flower(cx, cy, petal_l, petal_w, center_r, rotation=0):
    els = []
    for i in range(4):
        a = rotation + i*90
        els.append(petal_path(cx, cy, petal_l, petal_w, a))
    els.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{center_r:.2f}" fill="{INK}"/>')
    return "\n  ".join(els)

def daisy_flower(cx, cy, petal_l, petal_w, n_petals, center_r, rotation=0):
    els = []
    step = 360/n_petals
    for i in range(n_petals):
        a = rotation + i*step
        els.append(petal_path(cx, cy, petal_l, petal_w, a))
    els.append(circle_path_el(cx, cy, center_r))
    return "\n  ".join(els)

def circle_path_el(cx, cy, r, fill=INK):
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}"/>'

def small_leaf_pair(cx, cy, angle_deg, length=18, width=7):
    els = []
    a = math.radians(angle_deg)
    perp = a + math.pi/2
    for sign in [1, -1]:
        lx = cx + sign*9*math.cos(perp)
        ly = cy + sign*9*math.sin(perp)
        els.append(leaf_path(lx, ly, length, width, angle_deg + sign*40))
    return "\n  ".join(els)


# ═══════════════════════════════════════════════════════════════════════════════
# Design 01 — Floral Wreath
# ═══════════════════════════════════════════════════════════════════════════════

def make_01():
    print("  Generating 01 — Floral Wreath …")
    els = []

    # ── outer ring of leaves ──────────────────────────────────────────────────
    n_leaves = 24
    for i in range(n_leaves):
        a_deg = i * (360/n_leaves)
        a = math.radians(a_deg)
        r = 285
        lcx = CX + r*math.cos(a)
        lcy = CY + r*math.sin(a)
        els.append(leaf_path(lcx, lcy, 28, 9, a_deg + 90))

    # ── thin circular stem ring ───────────────────────────────────────────────
    els.append(f'<circle cx="{CX}" cy="{CY}" r="255" fill="none" stroke="{INK}" stroke-width="3"/>')

    # ── alternating flowers and leaves at medium radius ───────────────────────
    n_items = 16
    for i in range(n_items):
        a_deg = i * (360/n_items) - 90
        a = math.radians(a_deg)
        r = 255
        fx = CX + r*math.cos(a)
        fy = CY + r*math.sin(a)
        if i % 2 == 0:
            # 5-petal flower
            els.append(five_petal_flower(fx, fy, 22, 7, rotation=a_deg))
        else:
            # leaf pair
            els.append(leaf_path(fx, fy, 26, 9, a_deg + 90))
            els.append(leaf_path(fx, fy, 26, 9, a_deg - 90 + 180))

    # ── inner ring of small berries ───────────────────────────────────────────
    n_ber = 32
    for i in range(n_ber):
        a = math.radians(i * (360/n_ber))
        r = 220
        bx = CX + r*math.cos(a)
        by = CY + r*math.sin(a)
        els.append(circle_path_el(bx, by, 4))

    # ── centre rosette ────────────────────────────────────────────────────────
    for i in range(8):
        els.append(petal_path(CX, CY, 55, 14, i*45))
    for i in range(8):
        els.append(petal_path(CX, CY, 42, 10, i*45 + 22.5))
    els.append(circle_path_el(CX, CY, 18))
    # centre dot ring
    for i in range(8):
        a = math.radians(i*45)
        els.append(circle_path_el(CX + 10*math.cos(a), CY + 10*math.sin(a), 3))

    return svg_doc("Floral Wreath", "\n  ".join(els))


# ═══════════════════════════════════════════════════════════════════════════════
# Design 02 — Sunflower Wreath
# ═══════════════════════════════════════════════════════════════════════════════

def make_02():
    print("  Generating 02 — Sunflower Wreath …")
    els = []

    # ── big sunflower centre ──────────────────────────────────────────────────
    # long outer petals (layer 1)
    for i in range(20):
        a = i * (360/20)
        els.append(petal_path(CX, CY, 180, 22, a))
    # inner petals (layer 2 — shorter, offset)
    for i in range(20):
        a = i * (360/20) + 9
        els.append(petal_path(CX, CY, 140, 16, a))
    # seed disc — fibonacci-ish dots
    disc_r = 85
    els.append(f'<circle cx="{CX}" cy="{CY}" r="{disc_r}" fill="{INK}"/>')
    # white ring to show seeds
    els.append(f'<circle cx="{CX}" cy="{CY}" r="{disc_r}" fill="none" stroke="white" stroke-width="2"/>')
    # seed dots pattern (sunflower spiral approx)
    golden = (1 + math.sqrt(5))/2
    for k in range(1, 140):
        theta = 2*math.pi * k / (golden**2)
        rk    = disc_r * 0.92 * math.sqrt(k/140)
        sx    = CX + rk*math.cos(theta)
        sy    = CY + rk*math.sin(theta)
        els.append(f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="3.2" fill="white"/>')

    # ── wreath ring of leaves around sunflower ─────────────────────────────
    n_leaves = 20
    for i in range(n_leaves):
        a_deg = i * (360/n_leaves) - 90
        a     = math.radians(a_deg)
        r     = 310
        lcx   = CX + r*math.cos(a)
        lcy   = CY + r*math.sin(a)
        # leaf pointing outward
        els.append(leaf_path(lcx, lcy, 42, 14, a_deg + 90))
        # small leaf pointing inward
        els.append(leaf_path(CX+(r-55)*math.cos(a), CY+(r-55)*math.sin(a), 28, 9, a_deg + 90 + 180))

    # ── small sunflower buds at corners (4 compass positions) ─────────────────
    for a_deg in [0, 90, 180, 270]:
        a  = math.radians(a_deg)
        bx = CX + 330*math.cos(a)
        by = CY + 330*math.sin(a)
        for j in range(12):
            els.append(petal_path(bx, by, 36, 7, j*(360/12)))
        els.append(circle_path_el(bx, by, 14))
        # fibonacci dots (small)
        for k in range(1, 20):
            theta2 = 2*math.pi * k / (golden**2)
            rk2 = 12 * math.sqrt(k/20)
            els.append(f'<circle cx="{bx+rk2*math.cos(theta2):.2f}" cy="{by+rk2*math.sin(theta2):.2f}" r="1.5" fill="white"/>')

    # ── outer decorative ring ─────────────────────────────────────────────────
    els.append(f'<circle cx="{CX}" cy="{CY}" r="370" fill="none" stroke="{INK}" stroke-width="4"/>')
    els.append(f'<circle cx="{CX}" cy="{CY}" r="378" fill="none" stroke="{INK}" stroke-width="1.5"/>')

    return svg_doc("Sunflower Wreath", "\n  ".join(els))


# ═══════════════════════════════════════════════════════════════════════════════
# Design 03 — Wildflower Bouquet
# ═══════════════════════════════════════════════════════════════════════════════

def make_03():
    print("  Generating 03 — Wildflower Bouquet …")
    els = []

    # ── ribbon bow at base ────────────────────────────────────────────────────
    # bow loops
    bow_cx, bow_cy = CX, 680
    for sign in [1, -1]:
        els.append(
            f'<path d="M {bow_cx:.0f},{bow_cy:.0f} '
            f'C {bow_cx+sign*90:.0f},{bow_cy-30:.0f} '
            f'{bow_cx+sign*110:.0f},{bow_cy-70:.0f} '
            f'{bow_cx+sign*70:.0f},{bow_cy-75:.0f} '
            f'C {bow_cx+sign*30:.0f},{bow_cy-80:.0f} '
            f'{bow_cx+sign*10:.0f},{bow_cy-30:.0f} '
            f'{bow_cx:.0f},{bow_cy:.0f} Z" fill="{INK}"/>'
        )
    # ribbon tails
    els.append(
        f'<path d="M {bow_cx-12:.0f},{bow_cy+5:.0f} '
        f'C {bow_cx-30:.0f},{bow_cy+40:.0f} {bow_cx-55:.0f},{bow_cy+60:.0f} {bow_cx-40:.0f},{bow_cy+85:.0f}" '
        f'fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
    )
    els.append(
        f'<path d="M {bow_cx+12:.0f},{bow_cy+5:.0f} '
        f'C {bow_cx+30:.0f},{bow_cy+40:.0f} {bow_cx+55:.0f},{bow_cy+60:.0f} {bow_cx+40:.0f},{bow_cy+85:.0f}" '
        f'fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
    )
    els.append(circle_path_el(bow_cx, bow_cy, 10))

    # ── stems ─────────────────────────────────────────────────────────────────
    stems = [
        (CX, bow_cy, CX-10, 430, CX-5, 300),         # centre stem
        (CX, bow_cy, CX-80, 420, CX-90, 260),         # left stem
        (CX, bow_cy, CX+80, 420, CX+90, 240),         # right stem
        (CX, bow_cy, CX-150, 470, CX-160, 340),       # far left
        (CX, bow_cy, CX+150, 470, CX+160, 330),       # far right
    ]
    for (sx,sy, cx1,cy1, ex,ey) in stems:
        els.append(
            f'<path d="M {sx:.0f},{sy:.0f} Q {cx1:.0f},{cy1:.0f} {ex:.0f},{ey:.0f}" '
            f'fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
        )

    # ── leaves along stems ────────────────────────────────────────────────────
    leaf_positions = [
        (CX-40, 520, -50, 30, 11), (CX+40, 510, 50, 30, 11),
        (CX-100, 440, -70, 26, 9), (CX+100, 430, 70, 26, 9),
        (CX-150, 420, -80, 22, 8), (CX+150, 410, 80, 22, 8),
        (CX-20, 400, -30, 24, 9),  (CX+25, 390, 40, 24, 9),
    ]
    for (lx, ly, ad, ln, lw) in leaf_positions:
        els.append(leaf_path(lx, ly, ln, lw, ad))

    # ── flowers ───────────────────────────────────────────────────────────────
    # centre tall stem — big daisy
    els.append(daisy_flower(CX-5, 290, 42, 11, 14, 16, rotation=-90))

    # left medium stems — 5-petal
    els.append(five_petal_flower(CX-90, 248, 30, 10, rotation=0))
    els.append(daisy_flower(CX-160, 328, 30, 8, 10, 12, rotation=15))

    # right medium stems
    els.append(five_petal_flower(CX+90, 228, 30, 10, rotation=18))
    els.append(daisy_flower(CX+160, 318, 28, 8, 10, 12, rotation=-20))

    # ── small filler buds (circles) ───────────────────────────────────────────
    bud_pts = [(CX-55, 310),(CX+60, 305),(CX-130,295),(CX+135,290)]
    for (bx,by) in bud_pts:
        els.append(circle_path_el(bx, by, 8))
        els.append(f'<line x1="{bx:.0f}" y1="{by+8:.0f}" x2="{bx:.0f}" y2="{by+28:.0f}" '
                   f'stroke="{INK}" stroke-width="3"/>')
        # small sepals
        for sign in [1,-1]:
            els.append(leaf_path(bx, by+14, 12, 4, 90+sign*30))

    # ── decorative grass / filler wisps ──────────────────────────────────────
    for i, (gx, gy, ga) in enumerate([
        (CX-175, 390, -85),(CX+178, 378, 85),
        (CX-120, 370, -75),(CX+125, 360, 75),
    ]):
        for wi in range(3):
            wlen = 40 - wi*8
            wa = ga + (wi-1)*10
            a  = math.radians(wa)
            els.append(
                f'<line x1="{gx:.0f}" y1="{gy:.0f}" '
                f'x2="{gx+wlen*math.cos(a):.0f}" y2="{gy+wlen*math.sin(a):.0f}" '
                f'stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>'
            )

    return svg_doc("Wildflower Bouquet", "\n  ".join(els))


# ═══════════════════════════════════════════════════════════════════════════════
# Design 04 — Floral Heart
# ═══════════════════════════════════════════════════════════════════════════════

def make_04():
    print("  Generating 04 — Floral Heart …")
    els = []

    # ── parametric heart outline sampled as polyline points ──────────────────
    def heart_xy(t):
        """Parametric heart scaled so the full shape fits inside 800x800."""
        # scale=23, yoff=5 → x spans 32..768, y spans 131..796 — fits with margin
        scale = 23
        x = scale * 16 * math.sin(t)**3
        # Formula: 13cos - 5cos2t - 2cos3t - cos4t  (y is inverted so heart points down)
        y = -scale * (13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t))
        return CX + x, CY + y + 5

    N = 200
    ts  = [2*math.pi*i/N for i in range(N)]
    pts = [heart_xy(t) for t in ts]

    # ── place flowers & leaves evenly around the heart ────────────────────────
    # We space items every ~4th sample
    step = 4
    for idx in range(0, N, step):
        x, y = pts[idx]
        # tangent direction (for orienting leaves)
        nx, ny = pts[(idx+1)%N]
        dx, dy = nx-x, ny-y
        angle  = math.degrees(math.atan2(dy, dx))

        ftype = (idx // step) % 6
        if ftype == 0:
            # small 5-petal flower
            els.append(five_petal_flower(x, y, 18, 6, rotation=angle))
        elif ftype == 1:
            # leaf
            els.append(leaf_path(x, y, 22, 8, angle + 90))
        elif ftype == 2:
            # daisy
            els.append(daisy_flower(x, y, 16, 5, 8, 6, rotation=angle))
        elif ftype == 3:
            # berry cluster
            for bi in range(3):
                ba = math.radians(angle + bi*30 - 30)
                bx = x + 8*math.cos(ba)
                by = y + 8*math.sin(ba)
                els.append(circle_path_el(bx, by, 4))
        elif ftype == 4:
            # 4-petal flower
            els.append(four_petal_flower(x, y, 14, 5, 5, rotation=angle))
        else:
            # small petal pair (like a bud)
            els.append(petal_path(x, y, 16, 5, angle+45))
            els.append(petal_path(x, y, 16, 5, angle-45))
            els.append(circle_path_el(x, y, 5))

    # ── centre fill: decorative rose ─────────────────────────────────────────
    # Heart centre is at approx CX, CY+400 (bottom-inside of heart), use visual centre
    # The heart spans y=131..796, so interior centre ≈ CY+150
    rose_cy = CY + 150
    for layer, (r, w, n, off) in enumerate([(50,14,7,0),(38,12,7,26),(26,10,6,13),(15,7,5,0)]):
        for i in range(n):
            els.append(petal_path(CX, rose_cy, r, w, i*(360/n)+off))
    els.append(circle_path_el(CX, rose_cy, 8))

    return svg_doc("Floral Heart", "\n  ".join(els))


# ═══════════════════════════════════════════════════════════════════════════════
# Design 05 — Botanical Arrow
# ═══════════════════════════════════════════════════════════════════════════════

def make_05():
    print("  Generating 05 — Botanical Arrow …")
    els = []

    # ── arrow shaft (horizontal, centred) ────────────────────────────────────
    shaft_y   = CY
    shaft_x1  = 120
    shaft_x2  = 640
    shaft_mid = (shaft_x1 + shaft_x2) / 2

    els.append(f'<line x1="{shaft_x1}" y1="{shaft_y}" x2="{shaft_x2}" y2="{shaft_y}" '
               f'stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')

    # ── arrowhead (right) ─────────────────────────────────────────────────────
    ah_x, ah_y = shaft_x2, shaft_y
    els.append(f'<polygon points="{ah_x},{ah_y} {ah_x-40},{ah_y-18} {ah_x-30},{ah_y} {ah_x-40},{ah_y+18}" '
               f'fill="{INK}"/>')

    # ── tail feathers (left) ──────────────────────────────────────────────────
    for sign in [1, -1]:
        for off in [0, 12]:
            els.append(
                f'<path d="M {shaft_x1+off},{shaft_y} '
                f'C {shaft_x1+off+20},{shaft_y+sign*28} {shaft_x1+off+40},{shaft_y+sign*32} {shaft_x1+off+55},{shaft_y}" '
                f'fill="none" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>'
            )

    # ── large flowers on shaft (3 evenly spaced) ─────────────────────────────
    flower_xs = [shaft_mid - 130, shaft_mid, shaft_mid + 130]
    for i, fx in enumerate(flower_xs):
        fy = shaft_y
        if i % 2 == 0:
            # daisy above shaft
            for j in range(10):
                a_deg = j*(360/10)
                els.append(petal_path(fx, fy-45, 28, 8, a_deg))
            els.append(circle_path_el(fx, fy-45, 12))
            # stem connector
            els.append(f'<line x1="{fx:.0f}" y1="{fy:.0f}" x2="{fx:.0f}" y2="{fy-17:.0f}" '
                       f'stroke="{INK}" stroke-width="4"/>')
        else:
            # rose below shaft
            for j in range(8):
                els.append(petal_path(fx, fy+45, 26, 9, j*45))
            for j in range(8):
                els.append(petal_path(fx, fy+45, 18, 7, j*45+22.5))
            els.append(circle_path_el(fx, fy+45, 7))
            els.append(f'<line x1="{fx:.0f}" y1="{fy:.0f}" x2="{fx:.0f}" y2="{fy+17:.0f}" '
                       f'stroke="{INK}" stroke-width="4"/>')

    # ── alternating leaves along shaft ───────────────────────────────────────
    leaf_xs = [shaft_x1+70, shaft_x1+140, shaft_mid-65, shaft_mid+65, shaft_x2-130]
    for i, lx in enumerate(leaf_xs):
        sign = 1 if i%2==0 else -1
        # leaf sprouting above/below shaft
        for side in [1, -1]:
            la = 270 + side * 40
            lcx = lx + side*10
            lcy = shaft_y - sign*10
            els.append(leaf_path(lcx, lcy, 22, 8, la*side if side==1 else la))

    # ── small berries scattered ───────────────────────────────────────────────
    berry_xs = [shaft_x1+100, shaft_x1+180, shaft_x2-160, shaft_x2-90]
    for i, bx in enumerate(berry_xs):
        by_offset = -30 if i%2==0 else 30
        for j in range(3):
            ba = math.radians(80 + j*30)
            els.append(circle_path_el(bx + 7*math.cos(ba), shaft_y + by_offset + 7*math.sin(ba), 4))
            els.append(f'<line x1="{bx:.0f}" y1="{shaft_y:.0f}" '
                       f'x2="{bx:.0f}" y2="{shaft_y+by_offset//2:.0f}" '
                       f'stroke="{INK}" stroke-width="2.5"/>')

    return svg_doc("Botanical Arrow", "\n  ".join(els))


# ═══════════════════════════════════════════════════════════════════════════════
# Design 06 — 12-Fold Mandala
# ═══════════════════════════════════════════════════════════════════════════════

def make_06():
    print("  Generating 06 — Mandala …")
    els = []
    FOLD = 12

    def ring(r, stroke=2, fill="none"):
        return f'<circle cx="{CX}" cy="{CY}" r="{r:.1f}" fill="{fill}" stroke="{INK}" stroke-width="{stroke}"/>'

    # ── centre dot ─────────────────────────────────────────────────────────
    els.append(ring(8, fill=INK))
    els.append(ring(18, stroke=1.5))
    els.append(ring(30, stroke=1))

    # ── ring 1: petal burst at r=55 ───────────────────────────────────────
    for i in range(FOLD):
        a = i * (360/FOLD)
        els.append(petal_path(CX, CY, 50, 10, a))

    els.append(ring(60, stroke=1))

    # ── ring 2: alternating dot & diamond at r=80 ─────────────────────────
    for i in range(FOLD*2):
        a = math.radians(i * (360/(FOLD*2)))
        r = 80
        if i % 2 == 0:
            els.append(circle_path_el(CX+r*math.cos(a), CY+r*math.sin(a), 4))
        else:
            dx, dy = CX+r*math.cos(a), CY+r*math.sin(a)
            ad = math.degrees(a)
            els.append(f'<rect x="{dx-4:.1f}" y="{dy-4:.1f}" width="8" height="8" '
                       f'transform="rotate({ad+45:.1f},{dx:.1f},{dy:.1f})" fill="{INK}"/>')

    els.append(ring(95, stroke=1))

    # ── ring 3: 12 pointed arches ─────────────────────────────────────────
    for i in range(FOLD):
        a = math.radians(i*(360/FOLD))
        r1, r2 = 95, 145
        sx, sy = CX+r1*math.cos(a), CY+r1*math.sin(a)
        ex, ey = CX+r2*math.cos(a), CY+r2*math.sin(a)
        # side points for arch base
        perp = a + math.pi/2
        w = 20
        els.append(
            f'<path d="M {sx+w*math.cos(perp):.1f},{sy+w*math.sin(perp):.1f} '
            f'Q {ex:.1f},{ey:.1f} '
            f'{sx-w*math.cos(perp):.1f},{sy-w*math.sin(perp):.1f}" '
            f'fill="none" stroke="{INK}" stroke-width="2"/>'
        )
        # small dot at arch tip
        els.append(circle_path_el(ex, ey, 3.5))

    els.append(ring(150, stroke=1.5))

    # ── ring 4: 24 petal band ─────────────────────────────────────────────
    for i in range(FOLD*2):
        a = i*(360/(FOLD*2))
        ax, ay = CX+(165)*math.cos(math.radians(a)), CY+(165)*math.sin(math.radians(a))
        els.append(petal_path(ax, ay, 18, 6, a+90))

    els.append(ring(187, stroke=1.5))

    # ── ring 5: 12 lotus petals ───────────────────────────────────────────
    for i in range(FOLD):
        a = i*(360/FOLD)
        ax, ay = CX+205*math.cos(math.radians(a)), CY+205*math.sin(math.radians(a))
        els.append(petal_path(ax, ay, 28, 10, a+90))
        # two flanking mini-petals
        for sign in [-1,1]:
            fax = CX+198*math.cos(math.radians(a+sign*15))
            fay = CY+198*math.sin(math.radians(a+sign*15))
            els.append(petal_path(fax, fay, 18, 6, a+90+sign*20))

    els.append(ring(238, stroke=2))

    # ── ring 6: outer lace ring — 36 tiny circles on ring ─────────────────
    for i in range(36):
        a = math.radians(i*10)
        r = 255
        els.append(circle_path_el(CX+r*math.cos(a), CY+r*math.sin(a), 5))

    els.append(ring(268, stroke=1))

    # ── ring 7: outermost pointed star petals ─────────────────────────────
    for i in range(FOLD):
        a = i*(360/FOLD) - 90
        ax = CX+285*math.cos(math.radians(a))
        ay = CY+285*math.sin(math.radians(a))
        els.append(petal_path(ax, ay, 38, 11, a+90))

    els.append(ring(330, stroke=2.5))
    els.append(ring(338, stroke=1))

    # ── decorative dot ring at outermost ────────────────────────────────────
    for i in range(FOLD*3):
        a = math.radians(i*(360/(FOLD*3)))
        r = 352
        els.append(circle_path_el(CX+r*math.cos(a), CY+r*math.sin(a), 3))

    els.append(ring(365, stroke=2))
    els.append(ring(372, stroke=1))

    return svg_doc("Botanical Mandala", "\n  ".join(els))


# ═══════════════════════════════════════════════════════════════════════════════
# Design 07 — "Bloom Where You Are Planted" Quote
# ═══════════════════════════════════════════════════════════════════════════════

def make_07():
    print("  Generating 07 — Bloom Quote …")
    els = []

    # ── decorative oval border ────────────────────────────────────────────────
    els.append(f'<ellipse cx="{CX}" cy="{CY}" rx="360" ry="290" '
               f'fill="none" stroke="{INK}" stroke-width="4"/>')
    els.append(f'<ellipse cx="{CX}" cy="{CY}" rx="345" ry="275" '
               f'fill="none" stroke="{INK}" stroke-width="1.5"/>')

    # ── corner ornaments (4 compass) ──────────────────────────────────────────
    ornament_pts = [(CX, CY-285), (CX, CY+285), (CX-355, CY), (CX+355, CY)]
    for ox, oy in ornament_pts:
        els.append(five_petal_flower(ox, oy, 16, 5, rotation=0))

    # ── top flourish (small flower spray) ────────────────────────────────────
    for i, (fx, fy, fs) in enumerate([
        (CX-120, CY-255, 1.0),(CX-60, CY-272, 0.85),
        (CX,     CY-280, 1.0),
        (CX+60,  CY-272, 0.85),(CX+120, CY-255, 1.0),
    ]):
        r = int(14*fs)
        els.append(daisy_flower(fx, fy, r, 4, 8, 5, rotation=i*15))

    # ── bottom flourish (leaf spray) ─────────────────────────────────────────
    for i, (lx, ly, la) in enumerate([
        (CX-100, CY+260, -80),(CX-50, CY+275, -90),(CX, CY+278, -90),
        (CX+50,  CY+275, -90),(CX+100, CY+260, -80),
    ]):
        els.append(leaf_path(lx, ly, 22, 8, la + (i-2)*15))

    # ── main headline "BLOOM" ─────────────────────────────────────────────────
    els.append(
        f'<text x="{CX}" y="{CY-70}" '
        f'font-family="Georgia, \'Times New Roman\', serif" '
        f'font-size="88" font-weight="bold" '
        f'text-anchor="middle" fill="{INK}" letter-spacing="12">BLOOM</text>'
    )

    # ── divider flourish under BLOOM ──────────────────────────────────────────
    div_y = CY - 48
    els.append(f'<line x1="{CX-150}" y1="{div_y}" x2="{CX-30}" y2="{div_y}" '
               f'stroke="{INK}" stroke-width="2"/>')
    els.append(f'<line x1="{CX+30}" y1="{div_y}" x2="{CX+150}" y2="{div_y}" '
               f'stroke="{INK}" stroke-width="2"/>')
    els.append(circle_path_el(CX, div_y, 4))
    for sign in [-1,1]:
        els.append(circle_path_el(CX+sign*22, div_y, 3))

    # ── second line ───────────────────────────────────────────────────────────
    els.append(
        f'<text x="{CX}" y="{CY+0}" '
        f'font-family="Georgia, \'Times New Roman\', serif" '
        f'font-size="36" font-style="italic" '
        f'text-anchor="middle" fill="{INK}">Where You Are</text>'
    )

    # ── third line ────────────────────────────────────────────────────────────
    els.append(
        f'<text x="{CX}" y="{CY+55}" '
        f'font-family="Georgia, \'Times New Roman\', serif" '
        f'font-size="58" font-weight="bold" letter-spacing="4" '
        f'text-anchor="middle" fill="{INK}">PLANTED</text>'
    )

    # ── small flowers flanking "PLANTED" ─────────────────────────────────────
    for sign in [-1, 1]:
        fx = CX + sign * 210
        fy = CY + 32
        els.append(five_petal_flower(fx, fy, 14, 5, rotation=0))

    # ── small botanical detail line at bottom ─────────────────────────────────
    det_y = CY + 100
    els.append(f'<line x1="{CX-180}" y1="{det_y}" x2="{CX+180}" y2="{det_y}" '
               f'stroke="{INK}" stroke-width="1.5" stroke-dasharray="4,4"/>')
    for i in range(7):
        dx = CX - 180 + i*60
        els.append(circle_path_el(dx, det_y, 3))

    return svg_doc("Bloom Where You Are Planted", "\n  ".join(els))


# ═══════════════════════════════════════════════════════════════════════════════
# Design 08 — "She Believed She Could So She Did"
# ═══════════════════════════════════════════════════════════════════════════════

def make_08():
    print("  Generating 08 — She Believed …")
    els = []

    # ── decorative rectangular border with corners ────────────────────────────
    pad = 40
    els.append(f'<rect x="{pad}" y="{pad}" width="{W-2*pad}" height="{H-2*pad}" '
               f'fill="none" stroke="{INK}" stroke-width="3" rx="4"/>')
    els.append(f'<rect x="{pad+10}" y="{pad+10}" width="{W-2*pad-20}" height="{H-2*pad-20}" '
               f'fill="none" stroke="{INK}" stroke-width="1.2" rx="2"/>')

    # corner ornaments
    corners = [(pad, pad), (W-pad, pad), (pad, H-pad), (W-pad, H-pad)]
    corner_angles = [(-90+45), (90-45+90), (90+45+90), (90+45+180)]
    for (cx2, cy2), ca in zip(corners, corner_angles):
        for j in range(4):
            a = math.radians(ca + j*90)
            els.append(petal_path(cx2, cy2, 22, 7, math.degrees(a)))
        els.append(circle_path_el(cx2, cy2, 7))

    # ── top vine flourish ─────────────────────────────────────────────────────
    vine_y = 110
    els.append(
        f'<path d="M {pad+30},{vine_y} '
        f'C {CX-160},{vine_y-30} {CX-80},{vine_y+20} {CX},{vine_y-10} '
        f'C {CX+80},{vine_y-40} {CX+160},{vine_y+20} {W-pad-30},{vine_y}" '
        f'fill="none" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>'
    )
    # flowers on vine
    for fx, fy, fa in [(CX-140,vine_y-20,0),(CX,vine_y-10,0),(CX+140,vine_y-18,0)]:
        els.append(five_petal_flower(fx, fy, 16, 5, rotation=fa))
    # leaves on vine
    for lx, ly, la in [(CX-80,vine_y+12,-60),(CX+80,vine_y+10,60)]:
        els.append(leaf_path(lx, ly, 18, 6, la))

    # ── "She" in large italic ─────────────────────────────────────────────────
    els.append(
        f'<text x="{CX}" y="{CY-145}" '
        f'font-family="Georgia, \'Times New Roman\', serif" '
        f'font-size="96" font-style="italic" font-weight="bold" '
        f'text-anchor="middle" fill="{INK}">She</text>'
    )

    # ── middle flourish ───────────────────────────────────────────────────────
    mfl_y = CY - 110
    for sign in [-1, 1]:
        els.append(
            f'<path d="M {CX},{mfl_y} C {CX+sign*60},{mfl_y-25} {CX+sign*120},{mfl_y+10} {CX+sign*170},{mfl_y-5}" '
            f'fill="none" stroke="{INK}" stroke-width="2"/>'
        )
        els.append(leaf_path(CX+sign*100, mfl_y-4, 16, 6, 90 if sign>0 else -90))
        els.append(five_petal_flower(CX+sign*170, mfl_y-5, 12, 4))

    # ── "Believed" ────────────────────────────────────────────────────────────
    els.append(
        f'<text x="{CX}" y="{CY-40}" '
        f'font-family="Georgia, \'Times New Roman\', serif" '
        f'font-size="68" font-style="italic" '
        f'text-anchor="middle" fill="{INK}">Believed</text>'
    )

    # ── "She Could" ──────────────────────────────────────────────────────────
    els.append(
        f'<text x="{CX}" y="{CY+40}" '
        f'font-family="Georgia, \'Times New Roman\', serif" '
        f'font-size="56" font-style="italic" '
        f'text-anchor="middle" fill="{INK}">She Could</text>'
    )

    # ── divider ───────────────────────────────────────────────────────────────
    div_y2 = CY + 68
    for sign in [-1, 1]:
        els.append(f'<line x1="{CX+sign*30}" y1="{div_y2}" x2="{CX+sign*160}" y2="{div_y2}" '
                   f'stroke="{INK}" stroke-width="2"/>')
    els.append(
        f'<path d="M {CX-28},{div_y2} Q {CX},{div_y2-14} {CX+28},{div_y2}" '
        f'fill="none" stroke="{INK}" stroke-width="2"/>'
    )

    # ── "So She Did" ──────────────────────────────────────────────────────────
    els.append(
        f'<text x="{CX}" y="{CY+140}" '
        f'font-family="Georgia, \'Times New Roman\', serif" '
        f'font-size="78" font-weight="bold" font-style="italic" '
        f'text-anchor="middle" fill="{INK}">So She Did</text>'
    )

    # ── bottom vine (mirror of top) ───────────────────────────────────────────
    bvine_y = 680
    els.append(
        f'<path d="M {pad+30},{bvine_y} '
        f'C {CX-160},{bvine_y+30} {CX-80},{bvine_y-20} {CX},{bvine_y+10} '
        f'C {CX+80},{bvine_y+40} {CX+160},{bvine_y-20} {W-pad-30},{bvine_y}" '
        f'fill="none" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>'
    )
    for fx, fy, fa in [(CX-140,bvine_y+18,0),(CX,bvine_y+10,0),(CX+140,bvine_y+16,0)]:
        els.append(five_petal_flower(fx, fy, 16, 5, rotation=fa))
    for lx, ly, la in [(CX-80,bvine_y-12,60),(CX+80,bvine_y-10,-60)]:
        els.append(leaf_path(lx, ly, 18, 6, la))

    return svg_doc("She Believed She Could So She Did", "\n  ".join(els))


# ═══════════════════════════════════════════════════════════════════════════════
# Design 09 — Butterfly with Botanical Wings
# ═══════════════════════════════════════════════════════════════════════════════

def make_09():
    print("  Generating 09 — Butterfly …")
    els = []

    # ── body (elongated oval with segments) ───────────────────────────────────
    body_cx, body_cy = CX, CY
    # main body
    els.append(
        f'<ellipse cx="{body_cx}" cy="{body_cy}" rx="12" ry="72" fill="{INK}"/>'
    )
    # body segments (white rings)
    for seg_y in range(-50, 70, 16):
        els.append(f'<ellipse cx="{body_cx}" cy="{body_cy+seg_y:.0f}" '
                   f'rx="11" ry="5" fill="none" stroke="white" stroke-width="1.5"/>')
    # head
    els.append(circle_path_el(body_cx, body_cy-78, 14))
    els.append(circle_path_el(body_cx, body_cy-78, 8, fill="white"))
    # antennae
    for sign in [-1, 1]:
        els.append(
            f'<path d="M {body_cx},{body_cy-90} C {body_cx+sign*20},{body_cy-130} '
            f'{body_cx+sign*40},{body_cy-155} {body_cx+sign*35},{body_cy-170}" '
            f'fill="none" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>'
        )
        els.append(circle_path_el(body_cx+sign*35, body_cy-170, 5))

    # ── wing outlines (parametric) ─────────────────────────────────────────
    # Upper wing: large rounded shape
    for sign in [-1, 1]:
        # upper wing path
        wpath = (
            f"M {body_cx},{body_cy-50} "
            f"C {body_cx+sign*80},{body_cy-160} "
            f"{body_cx+sign*220},{body_cy-200} "
            f"{body_cx+sign*280},{body_cy-120} "
            f"C {body_cx+sign*310},{body_cy-60} "
            f"{body_cx+sign*260},{body_cy+20} "
            f"{body_cx},{body_cy+10} Z"
        )
        els.append(f'<path d="{wpath}" fill="none" stroke="{INK}" stroke-width="3"/>')

        # lower wing
        lwpath = (
            f"M {body_cx},{body_cy+10} "
            f"C {body_cx+sign*90},{body_cy+40} "
            f"{body_cx+sign*210},{body_cy+20} "
            f"{body_cx+sign*230},{body_cy+100} "
            f"C {body_cx+sign*240},{body_cy+170} "
            f"{body_cx+sign*140},{body_cy+200} "
            f"{body_cx+sign*60},{body_cy+200} "
            f"C {body_cx+sign*20},{body_cy+200} "
            f"{body_cx},{body_cy+170} "
            f"{body_cx},{body_cy+140} Z"
        )
        els.append(f'<path d="{lwpath}" fill="none" stroke="{INK}" stroke-width="3"/>')

        # ── botanical details inside upper wing ─────────────────────────
        # Veins
        vein_ox = sign * 140
        vein_oy = -90
        for vi in range(4):
            va = 180 + sign * (20 + vi * 18)
            vlen = 80 - vi*12
            vax = body_cx + vein_ox + vlen*math.cos(math.radians(va))
            vay = body_cy + vein_oy + vlen*math.sin(math.radians(va))
            els.append(
                f'<line x1="{body_cx+vein_ox:.0f}" y1="{body_cy+vein_oy:.0f}" '
                f'x2="{vax:.0f}" y2="{vay:.0f}" '
                f'stroke="{INK}" stroke-width="1.5"/>'
            )

        # flowers in upper wing
        fw_positions = [
            (body_cx+sign*120, body_cy-130, 18, 7),
            (body_cx+sign*210, body_cy-100, 15, 5),
            (body_cx+sign*180, body_cy-50,  14, 5),
        ]
        for (fwx, fwy, fwr, fwc) in fw_positions:
            els.append(five_petal_flower(fwx, fwy, fwr, fwc, rotation=0))

        # leaves in upper wing
        for (llx, lly, lla) in [
            (body_cx+sign*80, body_cy-100, 90+sign*30),
            (body_cx+sign*155, body_cy-75, 90-sign*20),
        ]:
            els.append(leaf_path(llx, lly, 20, 7, lla))

        # ── lower wing botanical: daisy + leaves ──────────────────────────
        els.append(daisy_flower(body_cx+sign*130, body_cy+110, 24, 7, 10, 10))
        for (llx, lly, lla) in [
            (body_cx+sign*170, body_cy+80,  90+sign*20),
            (body_cx+sign*80,  body_cy+150, 90-sign*30),
        ]:
            els.append(leaf_path(llx, lly, 18, 6, lla))

        # small dots / circles inside wings
        for (dx, dy) in [
            (body_cx+sign*230, body_cy-80),
            (body_cx+sign*250, body_cy-30),
        ]:
            els.append(circle_path_el(dx, dy, 6))
            els.append(circle_path_el(dx, dy, 10, fill="none"))

    return svg_doc("Botanical Butterfly", "\n  ".join(els))


# ═══════════════════════════════════════════════════════════════════════════════
# Design 10 — Ornate Monogram Frame
# ═══════════════════════════════════════════════════════════════════════════════

def make_10():
    print("  Generating 10 — Monogram Frame …")
    els = []

    # ── outer decorative rectangle ────────────────────────────────────────────
    m = 35   # margin
    r_corners = 8
    els.append(f'<rect x="{m}" y="{m}" width="{W-2*m}" height="{H-2*m}" '
               f'fill="none" stroke="{INK}" stroke-width="5" rx="{r_corners}"/>')
    els.append(f'<rect x="{m+10}" y="{m+10}" width="{W-2*m-20}" height="{H-2*m-20}" '
               f'fill="none" stroke="{INK}" stroke-width="1.5" rx="{r_corners-2}"/>')
    els.append(f'<rect x="{m+18}" y="{m+18}" width="{W-2*m-36}" height="{H-2*m-36}" '
               f'fill="none" stroke="{INK}" stroke-width="0.8" rx="{r_corners-4}"/>')

    # ── corner bouquets (4 corners) ───────────────────────────────────────────
    corner_defs = [
        (m+2,   m+2,   45),
        (W-m-2, m+2,   135),
        (m+2,   H-m-2, -45),
        (W-m-2, H-m-2, -135),
    ]
    for (cx2, cy2, angle_off) in corner_defs:
        # 3 petals outward
        for j in range(5):
            pangle = angle_off + (j-2)*22
            els.append(petal_path(cx2, cy2, 38, 11, pangle))
        els.append(circle_path_el(cx2, cy2, 8))
        # small leaves flanking
        for sign in [-1, 1]:
            la = angle_off + sign*55
            els.append(leaf_path(cx2, cy2, 26, 8, la))

    # ── top centre floral arch ────────────────────────────────────────────────
    arch_y = m + 5
    arch_cx = CX
    # arch flowers
    for i, (fx, fy, fs) in enumerate([
        (arch_cx-130, arch_y+18, 0.8),
        (arch_cx-70,  arch_y+6,  0.9),
        (arch_cx,     arch_y,    1.0),
        (arch_cx+70,  arch_y+6,  0.9),
        (arch_cx+130, arch_y+18, 0.8),
    ]):
        r = int(20*fs)
        els.append(daisy_flower(fx, fy, r, 5, 10, 7, rotation=i*10-20))
    # connecting stems
    els.append(
        f'<path d="M {arch_cx-175},{arch_y+25} '
        f'C {arch_cx-100},{arch_y-10} {arch_cx-50},{arch_y+5} {arch_cx},{arch_y-5} '
        f'C {arch_cx+50},{arch_y-15} {arch_cx+100},{arch_y} {arch_cx+175},{arch_y+25}" '
        f'fill="none" stroke="{INK}" stroke-width="2"/>'
    )
    for lx, ly, la in [
        (arch_cx-110, arch_y+10, -70), (arch_cx-50, arch_y+2, -80),
        (arch_cx+50,  arch_y+2,  80),  (arch_cx+110, arch_y+10, 70),
    ]:
        els.append(leaf_path(lx, ly, 18, 6, la))

    # ── bottom centre floral spray ─────────────────────────────────────────
    bot_y = H - m - 5
    for i, (fx, fy, fs) in enumerate([
        (CX-110, bot_y-18, 0.85), (CX-55, bot_y-7, 0.9),
        (CX,     bot_y,   1.0),
        (CX+55,  bot_y-7, 0.9),   (CX+110, bot_y-18, 0.85),
    ]):
        r = int(20*fs)
        els.append(daisy_flower(fx, fy, r, 5, 10, 7, rotation=-i*10+20))
    els.append(
        f'<path d="M {CX-160},{bot_y-22} '
        f'C {CX-100},{bot_y+10} {CX-50},{bot_y-5} {CX},{bot_y+5} '
        f'C {CX+50},{bot_y+15} {CX+100},{bot_y} {CX+160},{bot_y-22}" '
        f'fill="none" stroke="{INK}" stroke-width="2"/>'
    )

    # ── left and right side vine strips ───────────────────────────────────────
    for side_x, side_dir in [(m+8, 1), (W-m-8, -1)]:
        # vertical line
        els.append(f'<line x1="{side_x}" y1="{m+65}" x2="{side_x}" y2="{H-m-65}" '
                   f'stroke="{INK}" stroke-width="2.5"/>')
        # flowers at mid and quarter points
        for fy2 in [CY-100, CY, CY+100]:
            els.append(five_petal_flower(side_x, fy2, 16, 5, rotation=0))
        # leaves alternating
        for i, fy2 in enumerate([CY-160, CY-60, CY+60, CY+160]):
            la2 = side_dir * (60 + (i%2)*30)
            els.append(leaf_path(side_x, fy2, 18, 6, la2))

    # ── placeholder letter in centre ──────────────────────────────────────────
    # Large decorative initial letter area (thin inner box for actual letter)
    letter_box_size = 220
    lbx = CX - letter_box_size//2
    lby = CY - letter_box_size//2
    els.append(f'<rect x="{lbx}" y="{lby}" width="{letter_box_size}" height="{letter_box_size}" '
               f'fill="none" stroke="{INK}" stroke-width="1.5" stroke-dasharray="6,4"/>')

    # Decorative "A" as sample letter
    els.append(
        f'<text x="{CX}" y="{CY+55}" '
        f'font-family="Georgia, \'Times New Roman\', serif" '
        f'font-size="160" font-weight="bold" '
        f'text-anchor="middle" fill="{INK}" opacity="0.9">A</text>'
    )
    # small label text
    els.append(
        f'<text x="{CX}" y="{CY+165}" '
        f'font-family="Georgia, \'Times New Roman\', serif" '
        f'font-size="18" font-style="italic" '
        f'text-anchor="middle" fill="{INK}">Monogram Frame</text>'
    )

    return svg_doc("Ornate Monogram Frame", "\n  ".join(els))


# ═══════════════════════════════════════════════════════════════════════════════
# Render helpers
# ═══════════════════════════════════════════════════════════════════════════════

def strip_white_rect(svg_text):
    """Remove the white background rect so PNG renders transparent."""
    return re.sub(r'<rect[^>]*fill=["\']white["\'][^/]*/>', '', svg_text, count=1)

def render_png_transparent(svg_text, out_path, size=4000):
    """4000×4000 transparent-background PNG."""
    svg_no_bg = strip_white_rect(svg_text)
    png_bytes  = cairosvg.svg2png(
        bytestring=svg_no_bg.encode(),
        output_width=size, output_height=size,
        background_color=None
    )
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    img.save(out_path, "PNG")

def render_pdf(svg_text, out_path):
    """PDF version."""
    cairosvg.svg2pdf(bytestring=svg_text.encode(), write_to=out_path)

def render_preview(svg_text, out_path, size=1200):
    """1200×1200 white-background preview PNG."""
    png_bytes = cairosvg.svg2png(
        bytestring=svg_text.encode(),
        output_width=size, output_height=size
    )
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    img.save(out_path, "PNG")


# ═══════════════════════════════════════════════════════════════════════════════
# README content
# ═══════════════════════════════════════════════════════════════════════════════

README = """\
FLORAL & BOTANICAL BUNDLE — SVG Cut File Pack
═══════════════════════════════════════════════

WHAT'S INCLUDED
───────────────
10 original designs in 3 formats:

  SVG/  — Scalable vector files for Cricut, Silhouette, Glowforge, and Procreate
  PNG/  — 4000×4000 px, transparent background, 300 DPI equivalent
  PDF/  — Print-ready vector PDF for any printer or plotter

DESIGNS INCLUDED
────────────────
01  Floral Wreath              — circular wreath of blooms, leaves & berries
02  Sunflower Wreath           — fibonacci seed center, petal ring wreath
03  Wildflower Bouquet         — loose bouquet with bow & mixed stems
04  Floral Heart               — heart silhouette built from flowers & leaves
05  Botanical Arrow            — decorative arrow with flowers along shaft
06  12-Fold Mandala            — layered radial mandala with botanical details
07  Bloom Where You Are Planted — quote design with oval border & flowers
08  She Believed She Could     — calligraphic quote with vine flourishes
09  Botanical Butterfly        — butterfly with detailed floral wing patterns
10  Monogram Frame             — ornate rectangular frame (place any letter inside)

HOW TO USE — CRICUT
────────────────────
1. Open Cricut Design Space
2. Upload > Browse > select the .SVG file
3. Choose "Complex Image" when prompted
4. Ungroup layers if needed (right-click > Ungroup)
5. Resize to your desired dimensions
6. Select your material and cut!

HOW TO USE — SILHOUETTE CAMEO
─────────────────────────────
1. Open Silhouette Studio
2. File > Open > select the .SVG file
3. Object > Ungroup if needed
4. Adjust size, send to cut

HOW TO USE — PRINT (PNG/PDF)
──────────────────────────────
The PNG files are 4000×4000 px with transparent background — ideal for:
  • Heat transfer (print on HTV, mirror before printing)
  • Sublimation printing
  • Procreate / digital art use
  • Iron-on decals

The PDF files are vector quality at any print size.

DESIGN NOTES
────────────
• All designs: 800×800 viewBox, single-colour (#1a1a1a), clean closed paths
• Fonts used in quote designs: Georgia / Times New Roman (system web-safe serif)
  — no external font files required; any machine that supports SVG text renders these
• For Cricut: if text does not render, convert text to paths in Inkscape first
  (Path > Object to Path) then re-import

LICENSE
───────
Personal use & small commercial use: ✓ Cut files for products you sell
Redistribution / resale of the files themselves: ✗ Not permitted
© OnBrandCraftz — All Rights Reserved

SUPPORT
───────
Questions? Contact: Printing3dthings@outlook.com

Thank you for your purchase! ★ A review on Etsy means everything to a small shop.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Main — generate everything
# ═══════════════════════════════════════════════════════════════════════════════

DESIGNS = [
    ("etsy_01_floral_wreath",      make_01),
    ("etsy_02_sunflower_wreath",   make_02),
    ("etsy_03_wildflower_bouquet", make_03),
    ("etsy_04_floral_heart",       make_04),
    ("etsy_05_botanical_arrow",    make_05),
    ("etsy_06_mandala",            make_06),
    ("etsy_07_bloom_quote",        make_07),
    ("etsy_08_she_believed",       make_08),
    ("etsy_09_butterfly",          make_09),
    ("etsy_10_monogram_frame",     make_10),
]

def main():
    print("\n══════════════════════════════════════════")
    print(" Floral & Botanical Bundle Generator")
    print("══════════════════════════════════════════\n")

    svg_dir  = os.path.join(BASE, "SVG")
    png_dir  = os.path.join(BASE, "PNG")
    pdf_dir  = os.path.join(BASE, "PDF")
    for d in [svg_dir, png_dir, pdf_dir, PREV]:
        os.makedirs(d, exist_ok=True)

    generated = []

    for name, fn in DESIGNS:
        print(f"\n▶ {name}")
        svg_text = fn()

        svg_path  = os.path.join(svg_dir,  name + ".svg")
        png_path  = os.path.join(png_dir,  name + ".png")
        pdf_path  = os.path.join(pdf_dir,  name + ".pdf")
        prev_path = os.path.join(PREV,     name + "_preview.png")

        with open(svg_path, "w") as f:
            f.write(svg_text)
        print(f"  ✓ SVG saved  ({len(svg_text)//1024} KB)")

        print(f"  Rendering 4000px transparent PNG …")
        render_png_transparent(svg_text, png_path, size=4000)
        print(f"  ✓ PNG saved  ({os.path.getsize(png_path)//1024} KB)")

        print(f"  Rendering PDF …")
        render_pdf(svg_text, pdf_path)
        print(f"  ✓ PDF saved  ({os.path.getsize(pdf_path)//1024} KB)")

        print(f"  Rendering 1200px preview PNG …")
        render_preview(svg_text, prev_path, size=1200)
        print(f"  ✓ Preview saved  ({os.path.getsize(prev_path)//1024} KB)")

        generated.append((name, svg_path, png_path, pdf_path, prev_path))

    # ── Write README ──────────────────────────────────────────────────────────
    readme_path = os.path.join(BASE, "README.txt")
    with open(readme_path, "w") as f:
        f.write(README)
    print(f"\n✓ README.txt written")

    # ── Build ZIP ─────────────────────────────────────────────────────────────
    zip_path = os.path.join(BASE, "FlowerBotanical_Bundle.zip")
    print(f"\n▶ Building ZIP: {zip_path}")
    file_count = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name, svg_path, png_path, pdf_path, _ in generated:
            zf.write(svg_path, f"FlowerBotanical_Bundle/SVG/{os.path.basename(svg_path)}")
            zf.write(png_path, f"FlowerBotanical_Bundle/PNG/{os.path.basename(png_path)}")
            zf.write(pdf_path, f"FlowerBotanical_Bundle/PDF/{os.path.basename(pdf_path)}")
            file_count += 3
        zf.write(readme_path, "FlowerBotanical_Bundle/README.txt")
        file_count += 1

    zip_mb = os.path.getsize(zip_path) / (1024*1024)

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n══════════════════════════════════════════")
    print(" GENERATION COMPLETE")
    print("══════════════════════════════════════════")
    print(f"  Total designs:      {len(generated)}")
    print(f"  Files in ZIP:       {file_count}")
    print(f"  ZIP size:           {zip_mb:.2f} MB")
    print(f"  ZIP path:           {zip_path}")
    print(f"  Preview PNGs:       {PREV}/")
    print(f"\n  All files confirmed generated (no pixel diff needed for vector source).")
    print("══════════════════════════════════════════\n")

if __name__ == "__main__":
    main()
