"""
Generate Christian & Faith SVG Bundle — 10 designs
Based on market research: #1 best-selling SVG category on Etsy 2026.
Retro/boho decorative style with scripture and faith quotes.
"""

import os, math, zipfile
from pathlib import Path

OUT = Path("/home/user/Etsy/data/faith_pack")
OUT.mkdir(exist_ok=True)
for d in ["SVG", "PNG", "PDF", "previews"]:
    (OUT / d).mkdir(exist_ok=True)

# ── SVG helpers ───────────────────────────────────────────────────────────────

def pt(x, y): return f"{x:.3f},{y:.3f}"

def circle_path(cx, cy, r):
    return (f"M {cx-r},{cy} "
            f"A {r},{r} 0 1,0 {cx+r},{cy} "
            f"A {r},{r} 0 1,0 {cx-r},{cy} Z")

def ring(cx, cy, r1, r2, dashcount=60):
    """Dashed/dotted ring between r1 and r2."""
    paths = []
    for i in range(dashcount):
        a0 = 2*math.pi * i / dashcount
        a1 = 2*math.pi * (i + 0.55) / dashcount
        p = []
        for a in [a0, a1]:
            p.append((cx + r1*math.cos(a), cy + r1*math.sin(a)))
        for a in [a1, a0]:
            p.append((cx + r2*math.cos(a), cy + r2*math.sin(a)))
        paths.append(f"M {pt(*p[0])} L {pt(*p[1])} L {pt(*p[2])} L {pt(*p[3])} Z")
    return " ".join(paths)

def star_path(cx, cy, r_outer, r_inner, points=5):
    pts = []
    for i in range(points * 2):
        r = r_outer if i % 2 == 0 else r_inner
        a = math.pi * i / points - math.pi / 2
        pts.append(f"{'M' if i==0 else 'L'} {cx+r*math.cos(a):.3f},{cy+r*math.sin(a):.3f}")
    return " ".join(pts) + " Z"

def leaf(cx, cy, r, angle):
    """Single teardrop leaf."""
    a = math.radians(angle)
    # tip
    tx, ty = cx + r*math.cos(a), cy + r*math.sin(a)
    # base
    bx, by = cx - r*0.3*math.cos(a), cy - r*0.3*math.sin(a)
    # control points (perpendicular)
    pa = a + math.pi/2
    c1x = bx + r*0.5*math.cos(pa); c1y = by + r*0.5*math.sin(pa)
    c2x = bx - r*0.5*math.cos(pa); c2y = by - r*0.5*math.sin(pa)
    return f"M {pt(bx,by)} Q {pt(c1x,c1y)} {pt(tx,ty)} Q {pt(c2x,c2y)} {pt(bx,by)} Z"

def petal(cx, cy, r, angle, width=0.35):
    a = math.radians(angle)
    tx, ty = cx + r*math.cos(a), cy + r*math.sin(a)
    bx, by = cx, cy
    pa = a + math.pi/2
    c1x = bx + r*width*math.cos(pa); c1y = by + r*width*math.sin(pa)
    c2x = tx + r*0.15*math.cos(pa); c2y = ty + r*0.15*math.sin(pa)
    c3x = tx - r*0.15*math.cos(pa); c3y = ty - r*0.15*math.sin(pa)
    c4x = bx - r*width*math.cos(pa); c4y = by - r*width*math.sin(pa)
    return f"M {pt(bx,by)} C {pt(c1x,c1y)} {pt(c2x,c2y)} {pt(tx,ty)} C {pt(c3x,c3y)} {pt(c4x,c4y)} {pt(bx,by)} Z"

def wreath_leaves(cx, cy, r_inner, r_outer, count=28):
    paths = []
    for i in range(count):
        a = 360 * i / count
        # alternate sides for realistic wreath
        r_mid = (r_inner + r_outer) / 2
        a_rad = math.radians(a)
        lx = cx + r_mid * math.cos(a_rad)
        ly = cy + r_mid * math.sin(a_rad)
        paths.append(leaf(lx, ly, (r_outer-r_inner)*0.7, a + 90))
    return " ".join(paths)

def ornate_border_rect(x, y, w, h, corner_r=18):
    """Rounded rectangle with small decorative notch in center of each side."""
    # simple rounded rect
    return (f"M {x+corner_r},{y} L {x+w-corner_r},{y} "
            f"Q {x+w},{y} {x+w},{y+corner_r} "
            f"L {x+w},{y+h-corner_r} Q {x+w},{y+h} {x+w-corner_r},{y+h} "
            f"L {x+corner_r},{y+h} Q {x},{y+h} {x},{y+h-corner_r} "
            f"L {x},{y+corner_r} Q {x},{y} {x+corner_r},{y} Z")

def banner_path(cx, cy, w, h):
    """Classic swallowtail banner."""
    hw = w/2; hh = h/2
    notch = hh * 0.4
    return (f"M {cx-hw},{cy-hh} L {cx+hw},{cy-hh} L {cx+hw},{cy+hh} "
            f"L {cx+hw*0.3},{cy+hh-notch} L {cx},{cy+hh} "
            f"L {cx-hw*0.3},{cy+hh-notch} L {cx-hw},{cy+hh} Z")

def cross_path(cx, cy, h, arm_ratio=0.6, thickness=0.18):
    """Simple Latin cross."""
    vw = h * thickness; hw = h * arm_ratio
    vt = cy - h/2; vb = cy + h/2
    hl = cx - hw/2; hr = cx + hw/2
    ay = cy - h * 0.1  # arm y position (slightly above center)
    return (f"M {cx-vw/2},{vt} L {cx+vw/2},{vt} L {cx+vw/2},{ay-vw/2} "
            f"L {hr},{ay-vw/2} L {hr},{ay+vw/2} L {cx+vw/2},{ay+vw/2} "
            f"L {cx+vw/2},{vb} L {cx-vw/2},{vb} L {cx-vw/2},{ay+vw/2} "
            f"L {hl},{ay+vw/2} L {hl},{ay-vw/2} L {cx-vw/2},{ay-vw/2} Z")

def sunburst(cx, cy, r_inner, r_outer, rays=24):
    """Sunburst / radial rays."""
    paths = []
    for i in range(rays):
        a0 = 2*math.pi * i / rays - math.pi/rays*0.4
        a1 = 2*math.pi * i / rays + math.pi/rays*0.4
        am = 2*math.pi * i / rays
        px = cx + r_outer*math.cos(am); py = cy + r_outer*math.sin(am)
        p1x = cx + r_inner*math.cos(a0); p1y = cy + r_inner*math.sin(a0)
        p2x = cx + r_inner*math.cos(a1); p2y = cy + r_inner*math.sin(a1)
        paths.append(f"M {pt(p1x,p1y)} L {pt(px,py)} L {pt(p2x,p2y)} Z")
    return " ".join(paths)

def svg_header(title, w=800, h=800):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <title>{title}</title>
  <rect width="{w}" height="{h}" fill="none"/>
'''

# ── Design 1: "Be Still" — wreath + cross ────────────────────────────────────

def design_be_still():
    s = svg_header("Be Still Faith SVG")
    cx, cy = 400, 400
    # outer dot ring
    for i in range(72):
        a = 2*math.pi*i/72
        rx = cx + 360*math.cos(a); ry = cy + 360*math.sin(a)
        s += f'  <circle cx="{rx:.1f}" cy="{ry:.1f}" r="2.5" fill="black"/>\n'
    # wreath
    s += f'  <path d="{wreath_leaves(cx, cy, 220, 300, 36)}" fill="black"/>\n'
    # inner ring
    s += f'  <path d="{ring(cx, cy, 195, 210, 48)}" fill="black"/>\n'
    # cross
    s += f'  <path d="{cross_path(cx, cy-40, 120)}" fill="black"/>\n'
    # text area suggestion lines (decorative)
    for dy in [-10, 10]:
        s += f'  <line x1="{cx-90}" y1="{cy+80+dy}" x2="{cx+90}" y2="{cy+80+dy}" stroke="black" stroke-width="1.5"/>\n'
    # main text
    s += f'''  <text x="{cx}" y="{cy+60}" text-anchor="middle" font-family="Georgia, serif"
        font-size="52" font-weight="bold" fill="black" letter-spacing="4">BE STILL</text>
  <text x="{cx}" y="{cy+105}" text-anchor="middle" font-family="Georgia, serif"
        font-size="18" fill="black" letter-spacing="6">AND KNOW THAT I AM GOD</text>
  <text x="{cx}" y="{cy+135}" text-anchor="middle" font-family="Georgia, serif"
        font-size="14" fill="black" letter-spacing="3">PSALM 46:10</text>\n'''
    s += "</svg>"
    return s

# ── Design 2: "Faith Over Fear" — bold with cross + banner ───────────────────

def design_faith_over_fear():
    s = svg_header("Faith Over Fear SVG")
    cx, cy = 400, 400
    # sunburst background
    s += f'  <path d="{sunburst(cx, cy, 130, 370, 36)}" fill="black" opacity="0.12"/>\n'
    # outer decorative ring
    s += f'  <path d="{ring(cx, cy, 355, 375, 80)}" fill="black"/>\n'
    # cross behind text
    s += f'  <path d="{cross_path(cx, cy, 300, arm_ratio=0.55, thickness=0.14)}" fill="black" opacity="0.08"/>\n'
    # bold banner top
    s += f'  <path d="{banner_path(cx, cy-90, 440, 70)}" fill="black"/>\n'
    s += f'  <text x="{cx}" y="{cy-75}" text-anchor="middle" font-family="Georgia, serif" font-size="44" font-weight="bold" fill="white" letter-spacing="6">FAITH</text>\n'
    # divider cross small
    s += f'  <path d="{cross_path(cx, cy+5, 55)}" fill="black"/>\n'
    # bottom banner
    s += f'  <path d="{banner_path(cx, cy+100, 380, 68)}" fill="black"/>\n'
    s += f'  <text x="{cx}" y="{cy+115}" text-anchor="middle" font-family="Georgia, serif" font-size="44" font-weight="bold" fill="white" letter-spacing="6">FEAR</text>\n'
    # OVER text
    s += f'  <text x="{cx}" y="{cy+62}" text-anchor="middle" font-family="Georgia, serif" font-size="26" fill="black" letter-spacing="10">OVER</text>\n'
    s += "</svg>"
    return s

# ── Design 3: "Blessed" — sunburst circular badge ────────────────────────────

def design_blessed():
    s = svg_header("Blessed SVG Badge")
    cx, cy = 400, 400
    # sunburst
    s += f'  <path d="{sunburst(cx, cy, 170, 360, 40)}" fill="black"/>\n'
    # white circle mask (simulated with fill=none, stroke)
    s += f'  <circle cx="{cx}" cy="{cy}" r="168" fill="white"/>\n'
    # inner ring
    s += f'  <circle cx="{cx}" cy="{cy}" r="168" fill="none" stroke="black" stroke-width="4"/>\n'
    s += f'  <circle cx="{cx}" cy="{cy}" r="155" fill="none" stroke="black" stroke-width="1.5"/>\n'
    # dots on inner ring
    for i in range(48):
        a = 2*math.pi*i/48
        rx = cx + 155*math.cos(a); ry = cy + 155*math.sin(a)
        s += f'  <circle cx="{rx:.1f}" cy="{ry:.1f}" r="2" fill="black"/>\n'
    # stars
    for i, angle in enumerate(range(0, 360, 45)):
        a = math.radians(angle)
        sx = cx + 120*math.cos(a); sy = cy + 120*math.sin(a)
        s += f'  <path d="{star_path(sx, sy, 8, 4, 4)}" fill="black"/>\n'
    # main text
    s += f'''  <text x="{cx}" y="{cy+22}" text-anchor="middle" font-family="Georgia, serif"
        font-size="86" font-weight="bold" fill="black" letter-spacing="2">BLESSED</text>\n'''
    s += "</svg>"
    return s

# ── Design 4: "Grace Upon Grace" — floral frame ──────────────────────────────

def design_grace():
    s = svg_header("Grace Upon Grace SVG")
    cx, cy = 400, 400
    # floral corner ornaments  
    for (ox, oy, flip_x, flip_y) in [(135,135,1,1),(665,135,-1,1),(135,665,1,-1),(665,665,-1,-1)]:
        for i in range(8):
            a = 360*i/8
            s += f'  <path d="{petal(ox, oy, 55, a)}" fill="black"/>\n'
        s += f'  <circle cx="{ox}" cy="{oy}" r="12" fill="black"/>\n'
        for j in range(5):
            la = 45 * (j - 2)
            s += f'  <path d="{leaf(ox + flip_x*35*math.cos(math.radians(la+90)), oy + flip_y*35*math.sin(math.radians(la+90)), 22, la+90+45)}" fill="black"/>\n'
    # border frame
    s += f'  <path d="{ornate_border_rect(90, 90, 620, 620, 25)}" fill="none" stroke="black" stroke-width="3"/>\n'
    s += f'  <path d="{ornate_border_rect(110, 110, 580, 580, 20)}" fill="none" stroke="black" stroke-width="1.5"/>\n'
    # decorative side vines
    for x_pos, flip in [(65, 1), (735, -1)]:
        for j in range(7):
            ly = 200 + j*60
            s += f'  <path d="{leaf(x_pos, ly, 20, flip*30)}" fill="black"/>\n'
    # text
    s += f'''  <text x="{cx}" y="{cy-55}" text-anchor="middle" font-family="Georgia, serif" font-style="italic" font-size="32" fill="black" letter-spacing="3">grace</text>
  <text x="{cx}" y="{cy}" text-anchor="middle" font-family="Georgia, serif" font-size="72" font-weight="bold" fill="black" letter-spacing="5">UPON</text>
  <text x="{cx}" y="{cy+60}" text-anchor="middle" font-family="Georgia, serif" font-style="italic" font-size="32" fill="black" letter-spacing="3">grace</text>
  <text x="{cx}" y="{cy+120}" text-anchor="middle" font-family="Georgia, serif" font-size="14" fill="black" letter-spacing="6">JOHN  1:16</text>\n'''
    s += "</svg>"
    return s

# ── Design 5: "She Is Clothed" — oval wreath ─────────────────────────────────

def design_she_is_clothed():
    s = svg_header("She Is Clothed SVG")
    cx, cy = 400, 400
    # oval wreath using ellipse leaf placement
    leaf_paths = []
    for i in range(36):
        t = 2*math.pi*i/36
        rx, ry = 280, 200  # ellipse radii
        lx = cx + rx * math.cos(t); ly = cy + ry * math.sin(t)
        angle = math.degrees(math.atan2(ry*math.cos(t), -rx*math.sin(t))) + 90
        leaf_paths.append(leaf(lx, ly, 28, angle))
    s += f'  <path d="{" ".join(leaf_paths)}" fill="black"/>\n'
    # inner oval
    s += f'  <ellipse cx="{cx}" cy="{cy}" rx="250" ry="170" fill="none" stroke="black" stroke-width="2.5"/>\n'
    s += f'  <ellipse cx="{cx}" cy="{cy}" rx="235" ry="155" fill="none" stroke="black" stroke-width="1"/>\n'
    # ribbon bow at bottom
    bow_y = cy + 215
    s += f'  <path d="M {cx},{bow_y} Q {cx-60},{bow_y-25} {cx-90},{bow_y+5} Q {cx-60},{bow_y+20} {cx},{bow_y} Z" fill="black"/>\n'
    s += f'  <path d="M {cx},{bow_y} Q {cx+60},{bow_y-25} {cx+90},{bow_y+5} Q {cx+60},{bow_y+20} {cx},{bow_y} Z" fill="black"/>\n'
    s += f'  <ellipse cx="{cx}" cy="{bow_y}" rx="8" ry="8" fill="black"/>\n'
    # text
    s += f'''  <text x="{cx}" y="{cy-65}" text-anchor="middle" font-family="Georgia, serif" font-size="21" fill="black" letter-spacing="2">SHE IS CLOTHED IN</text>
  <text x="{cx}" y="{cy-18}" text-anchor="middle" font-family="Georgia, serif" font-size="56" font-weight="bold" fill="black">STRENGTH</text>
  <text x="{cx}" y="{cy+32}" text-anchor="middle" font-family="Georgia, serif" font-size="22" fill="black" letter-spacing="8">AND DIGNITY</text>
  <text x="{cx}" y="{cy+75}" text-anchor="middle" font-family="Georgia, serif" font-size="15" fill="black" letter-spacing="4">PROVERBS  31:25</text>\n'''
    s += "</svg>"
    return s

# ── Design 6: "With God All Things" — mountain silhouette ────────────────────

def design_with_god():
    s = svg_header("With God All Things Are Possible SVG")
    cx, cy = 400, 400
    # starfield dots top half
    import random; random.seed(42)
    for _ in range(55):
        sx = random.uniform(50, 750); sy = random.uniform(50, 300)
        sr = random.uniform(1.5, 3.5)
        s += f'  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" fill="black"/>\n'
    # mountain silhouette
    mtn = "M 0,620 L 0,480 L 120,280 L 240,420 L 320,300 L 400,160 L 480,300 L 560,380 L 660,260 L 760,400 L 800,480 L 800,620 Z"
    s += f'  <path d="{mtn}" fill="black"/>\n'
    # cross on peak
    s += f'  <path d="{cross_path(400, 80, 80, 0.5, 0.16)}" fill="black"/>\n'
    # sun rays above mountain
    s += f'  <path d="{sunburst(400, 170, 40, 90, 16)}" fill="black" opacity="0.7"/>\n'
    s += f'  <circle cx="400" cy="170" r="32" fill="black"/>\n'
    s += f'  <circle cx="400" cy="170" r="22" fill="white"/>\n'
    # text box
    s += f'  <rect x="80" y="630" width="640" height="130" rx="12" fill="none" stroke="black" stroke-width="2"/>\n'
    s += f'''  <text x="{cx}" y="677" text-anchor="middle" font-family="Georgia, serif" font-size="22" fill="black" letter-spacing="1">WITH GOD</text>
  <text x="{cx}" y="718" text-anchor="middle" font-family="Georgia, serif" font-size="34" font-weight="bold" fill="black" letter-spacing="3">ALL THINGS</text>
  <text x="{cx}" y="748" text-anchor="middle" font-family="Georgia, serif" font-size="16" fill="black" letter-spacing="5">ARE POSSIBLE  ·  MATTHEW 19:26</text>\n'''
    s += "</svg>"
    return s

# ── Design 7: "Joy of the Lord" — radial flower badge ────────────────────────

def design_joy():
    s = svg_header("Joy of the Lord SVG")
    cx, cy = 400, 400
    # outer petal ring (large)
    for i in range(12):
        s += f'  <path d="{petal(cx, cy, 330, 360*i/12, 0.28)}" fill="black"/>\n'
    # second ring
    for i in range(12):
        s += f'  <path d="{petal(cx, cy, 240, 360*i/12+15, 0.32)}" fill="black"/>\n'
    # white reveal
    s += f'  <circle cx="{cx}" cy="{cy}" r="195" fill="white"/>\n'
    # inner decorative ring
    s += f'  <circle cx="{cx}" cy="{cy}" r="195" fill="none" stroke="black" stroke-width="3"/>\n'
    s += f'  <path d="{ring(cx, cy, 175, 193, 56)}" fill="black"/>\n'
    # small flowers on inner ring
    for i in range(8):
        a = 2*math.pi*i/8
        fx = cx + 155*math.cos(a); fy = cy + 155*math.sin(a)
        for j in range(6):
            s += f'  <path d="{petal(fx, fy, 14, 60*j)}" fill="black"/>\n'
        s += f'  <circle cx="{fx:.1f}" cy="{fy:.1f}" r="4" fill="white"/>\n'
    # text
    s += f'''  <text x="{cx}" y="{cy-35}" text-anchor="middle" font-family="Georgia, serif" font-size="26" fill="black" letter-spacing="6">THE</text>
  <text x="{cx}" y="{cy+28}" text-anchor="middle" font-family="Georgia, serif" font-size="68" font-weight="bold" fill="black">JOY</text>
  <text x="{cx}" y="{cy+68}" text-anchor="middle" font-family="Georgia, serif" font-size="22" fill="black" letter-spacing="3">OF THE LORD</text>
  <text x="{cx}" y="{cy+102}" text-anchor="middle" font-family="Georgia, serif" font-size="17" fill="black" letter-spacing="2">IS MY STRENGTH</text>
  <text x="{cx}" y="{cy+133}" text-anchor="middle" font-family="Georgia, serif" font-size="13" fill="black" letter-spacing="4">NEHEMIAH  8:10</text>\n'''
    s += "</svg>"
    return s

# ── Design 8: "I Can Do All Things" — bold retro arc ─────────────────────────

def design_i_can():
    s = svg_header("I Can Do All Things SVG")
    cx, cy = 400, 400
    W, H = 800, 800
    # retro arc text path definition
    s += f'  <defs>\n'
    s += f'    <path id="topArc" d="M 100,400 A 300,300 0 0,1 700,400"/>\n'
    s += f'    <path id="botArc" d="M 130,470 A 270,270 0 0,0 670,470"/>\n'
    s += f'  </defs>\n'
    # outer badge shape — distressed circle with zig-zag edge
    pts = []
    for i in range(120):
        t = 2*math.pi*i/120
        r = 360 + (8 if i%2==0 else -8)
        pts.append(f"{cx+r*math.cos(t):.1f},{cy+r*math.sin(t):.1f}")
    s += f'  <polygon points="{" ".join(pts)}" fill="black"/>\n'
    # white inner circle
    s += f'  <circle cx="{cx}" cy="{cy}" r="340" fill="white"/>\n'
    # thick ring
    s += f'  <circle cx="{cx}" cy="{cy}" r="338" fill="none" stroke="black" stroke-width="5"/>\n'
    s += f'  <circle cx="{cx}" cy="{cy}" r="315" fill="none" stroke="black" stroke-width="2"/>\n'
    # star dividers
    for a in [0, 90, 180, 270]:
        aa = math.radians(a)
        sx = cx + 300*math.cos(aa); sy = cy + 300*math.sin(aa)
        s += f'  <path d="{star_path(sx, sy, 10, 4.5, 4)}" fill="black"/>\n'
    # arc text top
    s += f'  <text font-family="Georgia, serif" font-size="30" font-weight="bold" fill="black" letter-spacing="3">\n'
    s += f'    <textPath href="#topArc" startOffset="50%" text-anchor="middle">I CAN DO ALL THINGS</textPath>\n'
    s += f'  </text>\n'
    # arc text bottom
    s += f'  <text font-family="Georgia, serif" font-size="18" fill="black" letter-spacing="2">\n'
    s += f'    <textPath href="#botArc" startOffset="50%" text-anchor="middle">PHILIPPIANS 4:13</textPath>\n'
    s += f'  </text>\n'
    # center text
    s += f'''  <text x="{cx}" y="{cy-25}" text-anchor="middle" font-family="Georgia, serif" font-size="24" fill="black" letter-spacing="3">THROUGH CHRIST</text>
  <text x="{cx}" y="{cy+32}" text-anchor="middle" font-family="Georgia, serif" font-size="52" font-weight="bold" fill="black" letter-spacing="2">WHO</text>
  <text x="{cx}" y="{cy+85}" text-anchor="middle" font-family="Georgia, serif" font-size="28" fill="black" letter-spacing="5">STRENGTHENS ME</text>\n'''
    s += "</svg>"
    return s

# ── Design 9: "Proverbs 31 Woman" — floral crown ─────────────────────────────

def design_proverbs31():
    s = svg_header("Proverbs 31 Woman SVG")
    cx, cy = 400, 400
    # floral crown arc (top half)
    crown_r = 240
    flower_count = 11
    for i in range(flower_count):
        t = math.pi * (0.15 + 0.7 * i / (flower_count-1))
        fx = cx + crown_r * math.cos(t - math.pi/2 + math.pi)
        fy = cy - crown_r * math.sin(t) + 80
        # flower petals
        petals_n = 6 if i % 3 != 1 else 8
        for j in range(petals_n):
            s += f'  <path d="{petal(fx, fy, 28 + (i%3)*4, 360*j/petals_n)}" fill="black"/>\n'
        s += f'  <circle cx="{fx:.1f}" cy="{fy:.1f}" r="7" fill="white"/>\n'
        # stems / leaves
        if i < flower_count-1:
            next_t = math.pi * (0.15 + 0.7 * (i+1) / (flower_count-1))
            nx = cx + crown_r * math.cos(next_t - math.pi/2 + math.pi)
            ny = cy - crown_r * math.sin(next_t) + 80
            mx, my = (fx+nx)/2, (fy+ny)/2 + 18
            s += f'  <path d="M {pt(fx,fy)} Q {pt(mx,my)} {pt(nx,ny)}" fill="none" stroke="black" stroke-width="3"/>\n'
            s += f'  <path d="{leaf(mx, my, 18, 270)}" fill="black"/>\n'
    # divider lines
    for dy in [0, 6]:
        s += f'  <line x1="90" y1="{cy+120+dy}" x2="710" y2="{cy+120+dy}" stroke="black" stroke-width="{"3" if dy==0 else "1"}"/>\n'
    # text
    s += f'''  <text x="{cx}" y="{cy+20}" text-anchor="middle" font-family="Georgia, serif" font-size="28" fill="black" letter-spacing="3">PROVERBS 31</text>
  <text x="{cx}" y="{cy+75}" text-anchor="middle" font-family="Georgia, serif" font-size="62" font-weight="bold" fill="black">WOMAN</text>
  <text x="{cx}" y="{cy+155}" text-anchor="middle" font-family="Georgia, serif" font-size="15" fill="black" letter-spacing="5">VIRTUOUS · STRONG · CHOSEN</text>\n'''
    s += "</svg>"
    return s

# ── Design 10: "Trust In The Lord" — boho diamond badge ──────────────────────

def design_trust():
    s = svg_header("Trust In The Lord SVG")
    cx, cy = 400, 400
    # diamond shape outer
    diamond = f"M {cx},{cy-360} L {cx+360},{cy} L {cx},{cy+360} L {cx-360},{cy} Z"
    s += f'  <path d="{diamond}" fill="black"/>\n'
    # white diamond inner
    r2 = 320
    diamond2 = f"M {cx},{cy-r2} L {cx+r2},{cy} L {cx},{cy+r2} L {cx-r2},{cy} Z"
    s += f'  <path d="{diamond2}" fill="white"/>\n'
    # decorative ring
    for i in range(4):
        a = math.pi/2 * i + math.pi/4
        px = cx + 290*math.cos(a); py = cy + 290*math.sin(a)
        for j in range(6):
            s += f'  <path d="{petal(px, py, 22, 60*j)}" fill="black"/>\n'
        s += f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="6" fill="white"/>\n'
    # inner diamond border
    r3 = 280
    diamond3 = f"M {cx},{cy-r3} L {cx+r3},{cy} L {cx},{cy+r3} L {cx-r3},{cy} Z"
    s += f'  <path d="{diamond3}" fill="none" stroke="black" stroke-width="2"/>\n'
    r4 = 265
    diamond4 = f"M {cx},{cy-r4} L {cx+r4},{cy} L {cx},{cy+r4} L {cx-r4},{cy} Z"
    s += f'  <path d="{diamond4}" fill="none" stroke="black" stroke-width="1"/>\n'
    # text
    s += f'''  <text x="{cx}" y="{cy-85}" text-anchor="middle" font-family="Georgia, serif" font-size="26" fill="black" letter-spacing="4">TRUST IN</text>
  <text x="{cx}" y="{cy-30}" text-anchor="middle" font-family="Georgia, serif" font-size="30" fill="black" letter-spacing="3">THE LORD</text>
  <text x="{cx}" y="{cy+28}" text-anchor="middle" font-family="Georgia, serif" font-size="58" font-weight="bold" fill="black">WITH ALL</text>
  <text x="{cx}" y="{cy+88}" text-anchor="middle" font-family="Georgia, serif" font-size="28" fill="black" letter-spacing="4">YOUR HEART</text>
  <text x="{cx}" y="{cy+145}" text-anchor="middle" font-family="Georgia, serif" font-size="14" fill="black" letter-spacing="5">PROVERBS  3:5</text>\n'''
    s += "</svg>"
    return s

# ── Generate all 10 ───────────────────────────────────────────────────────────

designs = [
    ("faith_01_be_still",          "Be Still Psalm 46:10",           design_be_still()),
    ("faith_02_faith_over_fear",   "Faith Over Fear",                 design_faith_over_fear()),
    ("faith_03_blessed",           "Blessed Sunburst Badge",          design_blessed()),
    ("faith_04_grace_upon_grace",  "Grace Upon Grace John 1:16",      design_grace()),
    ("faith_05_she_is_clothed",    "She Is Clothed Proverbs 31:25",   design_she_is_clothed()),
    ("faith_06_with_god",          "With God All Things Matthew 19",  design_with_god()),
    ("faith_07_joy",               "Joy of the Lord Nehemiah 8:10",   design_joy()),
    ("faith_08_i_can",             "I Can Do All Things Phil 4:13",   design_i_can()),
    ("faith_09_proverbs31",        "Proverbs 31 Woman",               design_proverbs31()),
    ("faith_10_trust",             "Trust In The Lord Proverbs 3:5",  design_trust()),
]

print("Generating 10 faith SVG designs...")
for name, title, svg_content in designs:
    # SVG
    svg_path = OUT / "SVG" / f"{name}.svg"
    svg_path.write_text(svg_content)
    print(f"  ✓ {name}.svg ({len(svg_content)//1024}KB)")

print("\nSVGs generated. Now converting to PNG + PDF...")
