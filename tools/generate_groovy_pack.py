#!/usr/bin/env python3
"""
Retro Groovy Good Vibes SVG Pack — 20 bold, colorful, quirky designs.
Every design has a solid colored background and 3-5 vivid fill colors.
"""
import os, math

FONT_DEFS = """  <defs>
    <style>
      @font-face { font-family: 'BebasNeue'; src: url('/usr/local/share/fonts/BebasNeue-Regular.ttf'); }
      @font-face { font-family: 'GreatVibes'; src: url('/usr/local/share/fonts/GreatVibes-Regular.ttf'); }
      @font-face { font-family: 'Cormorant'; src: url('/usr/local/share/fonts/CormorantGaramond-Bold.ttf'); }
      @font-face { font-family: 'CormorantItalic'; src: url('/usr/local/share/fonts/CormorantGaramond-BoldItalic.ttf'); }
    </style>
  </defs>"""

OUT_DIR = "data/groovy_pack/SVG"


def wrap(title, bg, body):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">\n'
            f'  <title>{title}</title>\n'
            f'  <rect width="800" height="800" fill="{bg}"/>\n'
            f'{FONT_DEFS}\n{body}\n</svg>')


# ─── Geometry helpers ─────────────────────────────────────────────────────────

def sunburst(cx, cy, r, n, colors, r_in=0):
    out, step = [], 360 / n
    for i in range(n):
        a1 = math.radians(-90 + i * step)
        a2 = math.radians(-90 + (i + 1) * step)
        c = colors[i % len(colors)]
        lf = 1 if step >= 180 else 0
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
        if r_in:
            x0, y0 = cx + r_in * math.cos(a1), cy + r_in * math.sin(a1)
            x3, y3 = cx + r_in * math.cos(a2), cy + r_in * math.sin(a2)
            d = (f"M {x0:.1f},{y0:.1f} L {x1:.1f},{y1:.1f} "
                 f"A {r},{r} 0 {lf},1 {x2:.1f},{y2:.1f} "
                 f"L {x3:.1f},{y3:.1f} A {r_in},{r_in} 0 {lf},0 {x0:.1f},{y0:.1f} Z")
        else:
            d = f"M {cx},{cy} L {x1:.1f},{y1:.1f} A {r},{r} 0 {lf},1 {x2:.1f},{y2:.1f} Z"
        out.append(f'  <path d="{d}" fill="{c}"/>')
    return "\n".join(out)


def arch(cx, cy, r_out, band, colors):
    """Filled semicircular arch bands — rainbow style."""
    out = []
    for i, c in enumerate(colors):
        r1 = r_out - i * band
        r2 = r1 - band
        if r2 < 0:
            break
        d = (f"M {cx - r1:.1f},{cy} A {r1:.1f},{r1:.1f} 0 0,1 {cx + r1:.1f},{cy} "
             f"L {cx + r2:.1f},{cy} A {r2:.1f},{r2:.1f} 0 0,0 {cx - r2:.1f},{cy} Z")
        out.append(f'  <path d="{d}" fill="{c}"/>')
    return "\n".join(out)


def circ(cx, cy, r, fill, stroke=None, sw=4):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"{s}/>'


def star(cx, cy, ro, ri, n, fill):
    pts = []
    for i in range(n * 2):
        r = ro if i % 2 == 0 else ri
        a = math.radians(-90 + i * 180 / n)
        pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
    return f'  <polygon points="{" ".join(pts)}" fill="{fill}"/>'


def ring_dots(cx, cy, r, n, rd, fill):
    out = []
    for i in range(n):
        a = math.radians(360 * i / n)
        out.append(circ(cx + r * math.cos(a), cy + r * math.sin(a), rd, fill))
    return "\n".join(out)


def petal_flower(cx, cy, rp, np_, petal, center, rc=None):
    rc = rc or rp * 0.35
    out = []
    for i in range(np_):
        a = 360 * i / np_
        out.append(f'  <ellipse cx="{cx:.0f}" cy="{cy - rp * 0.52:.0f}" '
                   f'rx="{rp * 0.32:.0f}" ry="{rp * 0.56:.0f}" fill="{petal}" '
                   f'transform="rotate({a},{cx:.0f},{cy:.0f})"/>')
    out.append(circ(cx, cy, rc, center))
    return "\n".join(out)


def heart(cx, cy, s, fill):
    p = (f"M {cx},{cy + s * 0.28:.1f} "
         f"C {cx:.1f},{cy + s:.1f} {cx - s * 1.2:.1f},{cy + s * 0.55:.1f} "
         f"{cx - s * 1.2:.1f},{cy:.1f} "
         f"C {cx - s * 1.2:.1f},{cy - s * 0.55:.1f} {cx - s * 0.55:.1f},{cy - s * 0.8:.1f} "
         f"{cx:.1f},{cy - s * 0.22:.1f} "
         f"C {cx + s * 0.55:.1f},{cy - s * 0.8:.1f} {cx + s * 1.2:.1f},{cy - s * 0.55:.1f} "
         f"{cx + s * 1.2:.1f},{cy:.1f} "
         f"C {cx + s * 1.2:.1f},{cy + s * 0.55:.1f} {cx:.1f},{cy + s:.1f} "
         f"{cx},{cy + s * 0.28:.1f} Z")
    return f'  <path d="{p}" fill="{fill}"/>'


def cloud(cx, cy, r, fill):
    parts = [(cx, cy, r), (cx - r * .7, cy + r * .28, r * .65),
             (cx + r * .7, cy + r * .28, r * .65),
             (cx - r * .38, cy + r * .42, r * .8), (cx + r * .38, cy + r * .42, r * .8)]
    return "\n".join(circ(x, y, ri, fill) for x, y, ri in parts)


def txt(x, y, t, font, size, fill, anchor="middle", ls=0):
    ls_attr = f' letter-spacing="{ls}"' if ls else ""
    return (f'  <text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'font-family="{font}, sans-serif" font-size="{size}" fill="{fill}"{ls_attr}>'
            f'{t}</text>')


def checker_border(margin, cell, c1, c2, w=800):
    out = []
    bw = margin // cell
    cols = rows = w // cell
    for r in range(rows):
        for c in range(cols):
            if not (r < bw or r >= rows - bw or c < bw or c >= cols - bw):
                continue
            color = c1 if (r + c) % 2 == 0 else c2
            out.append(f'  <rect x="{c * cell}" y="{r * cell}" '
                       f'width="{cell}" height="{cell}" fill="{color}"/>')
    return "\n".join(out)


def stripe_bg(colors, horizontal=True):
    out, n, band = [], len(colors), 800 // len(colors)
    for i, c in enumerate(colors):
        if horizontal:
            out.append(f'  <rect x="0" y="{i * band}" width="800" height="{band + 2}" fill="{c}"/>')
        else:
            out.append(f'  <rect x="{i * band}" y="0" width="{band + 2}" height="800" fill="{c}"/>')
    return "\n".join(out)


def flame(cx, cy, h, w, fill):
    p = (f"M {cx},{cy} "
         f"C {cx - w:.1f},{cy - h * .3:.1f} {cx - w * .4:.1f},{cy - h * .75:.1f} {cx},{cy - h:.1f} "
         f"C {cx + w * .4:.1f},{cy - h * .75:.1f} {cx + w:.1f},{cy - h * .3:.1f} {cx},{cy} Z")
    return f'  <path d="{p}" fill="{fill}"/>'


def diamond(cx, cy, w, h, fill):
    return (f'  <polygon points="{cx},{cy - h} {cx + w},{cy} '
            f'{cx},{cy + h} {cx - w},{cy}" fill="{fill}"/>')


# ─── 20 Designs ──────────────────────────────────────────────────────────────

def d01_good_vibes():
    body = "\n".join([
        # Sunburst bg
        sunburst(400, 680, 780, 28, ["#E87B2A", "#F5E060"]),
        # Rainbow arch (center at bottom, arches upward)
        arch(400, 660, 360, 48, ["#D93030","#E87B2A","#F5D030","#2B8A3E","#1E6FCC","#7B35B0"]),
        # White fill inside smallest arch
        circ(400, 660, 48, "#F5E060"),
        # Clouds flanking base
        cloud(110, 660, 52, "#FFFFFF"),
        cloud(690, 660, 52, "#FFFFFF"),
        # Stars scattered upper area
        star(140, 170, 28, 11, 5, "#D93030"),
        star(660, 150, 22, 9, 5, "#7B35B0"),
        star(700, 420, 18, 7, 5, "#1E6FCC"),
        star(100, 430, 20, 8, 5, "#2B8A3E"),
        star(400, 100, 26, 10, 5, "#E87B2A"),
        star(260, 200, 14, 6, 4, "#1E6FCC"),
        star(540, 210, 16, 6, 4, "#D93030"),
        # Text — center of canvas
        txt(400, 420, "GOOD VIBES", "BebasNeue", 78, "#1A1A2E", ls=3),
        txt(400, 490, "ONLY", "BebasNeue", 64, "#D93030", ls=6),
        txt(400, 540, "always &amp; forever", "CormorantItalic", 18, "#1A1A2E", ls=2),
    ])
    return wrap("Good Vibes Only", "#F5E060", body)


def d02_stay_groovy():
    body = "\n".join([
        sunburst(400, 400, 420, 32, ["#F5D030", "#F0A020"]),
        circ(400, 400, 280, "#5B2080"),
        circ(400, 400, 265, "#F5D030", stroke="#F5D030", sw=0),
        ring_dots(400, 400, 265, 36, 5, "#F5D030"),
        circ(400, 400, 255, "#5B2080"),
        # Stars on ring
        star(400, 140, 20, 8, 5, "#F0A020"),
        star(400, 660, 20, 8, 5, "#F0A020"),
        star(140, 400, 20, 8, 5, "#E84B8A"),
        star(660, 400, 20, 8, 5, "#E84B8A"),
        star(205, 205, 16, 6, 5, "#F5D030"),
        star(595, 205, 16, 6, 5, "#F5D030"),
        star(205, 595, 16, 6, 5, "#F5D030"),
        star(595, 595, 16, 6, 5, "#F5D030"),
        txt(400, 340, "stay", "GreatVibes", 58, "#E84B8A"),
        txt(400, 418, "GROOVY", "BebasNeue", 90, "#F5D030", ls=2),
        txt(400, 462, "baby", "GreatVibes", 40, "#FFFFFF"),
        txt(400, 500, "✦  good times only  ✦", "CormorantItalic", 16, "#F0A020", ls=1),
    ])
    return wrap("Stay Groovy", "#5B2080", body)


def d03_spread_love():
    body = "\n".join([
        # Dot ring border
        ring_dots(400, 400, 360, 72, 6, "#F5D030"),
        ring_dots(400, 400, 340, 60, 4, "#FFB3C6"),
        # Hearts scattered
        heart(180, 180, 30, "#F5D030"),
        heart(620, 160, 26, "#FFB3C6"),
        heart(660, 560, 30, "#F5D030"),
        heart(140, 580, 24, "#FFB3C6"),
        heart(400, 130, 22, "#FFFFFF"),
        heart(400, 670, 22, "#F5D030"),
        heart(100, 370, 20, "#F5D030"),
        heart(700, 390, 20, "#FFB3C6"),
        heart(240, 680, 18, "#FFFFFF"),
        heart(560, 680, 18, "#FFFFFF"),
        heart(260, 120, 18, "#FFFFFF"),
        heart(540, 120, 18, "#FFB3C6"),
        # Center white circle
        circ(400, 400, 230, "#FFFFFF"),
        txt(400, 310, "SPREAD", "Cormorant", 26, "#E0245C", ls=8),
        txt(400, 416, "Love", "GreatVibes", 108, "#E0245C"),
        txt(400, 472, "everywhere you go", "CormorantItalic", 17, "#E0245C", ls=3),
        txt(400, 510, "✦  ✦  ✦", "Cormorant", 14, "#E0245C"),
    ])
    return wrap("Spread Love", "#E0245C", body)


def d04_be_weird():
    body = "\n".join([
        sunburst(400, 400, 420, 40, ["#F07A1A", "#F5D030"], r_in=280),
        circ(400, 400, 278, "#1B9E8A"),
        circ(400, 400, 265, "#F07A1A", stroke=None),
        ring_dots(400, 400, 265, 48, 5, "#F5D030"),
        circ(400, 400, 255, "#1B9E8A"),
        # Corner stars
        star(80, 80, 26, 10, 6, "#F5D030"),
        star(720, 80, 26, 10, 6, "#F07A1A"),
        star(80, 720, 26, 10, 6, "#F07A1A"),
        star(720, 720, 26, 10, 6, "#F5D030"),
        star(400, 60, 18, 7, 5, "#FFFFFF"),
        star(60, 400, 18, 7, 5, "#FFFFFF"),
        star(740, 400, 18, 7, 5, "#FFFFFF"),
        star(400, 740, 18, 7, 5, "#FFFFFF"),
        txt(400, 322, "BE", "Cormorant", 26, "#F5D030", ls=14),
        txt(400, 390, "WEIRD", "BebasNeue", 86, "#FFFFFF", ls=2),
        txt(400, 434, "be", "GreatVibes", 34, "#F07A1A"),
        txt(400, 494, "WONDERFUL", "BebasNeue", 52, "#F5D030", ls=2),
    ])
    return wrap("Be Weird Be Wonderful", "#1B9E8A", body)


def d05_choose_happy():
    body = "\n".join([
        # Sun spikes (triangular rays)
        sunburst(400, 400, 400, 20, ["#F5D030", "#FFE870"], r_in=220),
        circ(400, 400, 218, "#F5D030"),
        # Smiley face
        circ(356, 376, 18, "#E07A00"),  # left eye
        circ(444, 376, 18, "#E07A00"),  # right eye
        # Smile arc approximated with path
        '  <path d="M 340,430 Q 400,475 460,430" stroke="#E07A00" stroke-width="9" fill="none" stroke-linecap="round"/>',
        # Rosy cheeks
        circ(330, 418, 22, "#FFB3A0"),
        circ(470, 418, 22, "#FFB3A0"),
        # Outer decorative ring
        ring_dots(400, 400, 360, 56, 5, "#F07A1A"),
        # Corner elements
        star(120, 120, 24, 9, 5, "#D93030"),
        star(680, 120, 24, 9, 5, "#5B2080"),
        star(120, 680, 22, 9, 5, "#5B2080"),
        star(680, 680, 22, 9, 5, "#D93030"),
        # Text below sun
        txt(400, 560, "CHOOSE", "Cormorant", 22, "#1A1A2E", ls=10),
        txt(400, 636, "HAPPY", "BebasNeue", 78, "#D93030", ls=4),
        txt(400, 682, "every single day", "GreatVibes", 28, "#5B2080"),
    ])
    return wrap("Choose Happy", "#F07A1A", body)


def d06_wild_free():
    body = "\n".join([
        # Starburst in terracotta/cream
        sunburst(400, 400, 400, 36, ["#C4634F", "#E8C09A"], r_in=0),
        circ(400, 400, 290, "#2B6040"),
        circ(400, 400, 274, "#C4634F", stroke=None),
        ring_dots(400, 400, 274, 44, 5, "#E8C09A"),
        circ(400, 400, 264, "#2B6040"),
        # Scattered stars in cream/terracotta
        star(400, 168, 22, 8, 6, "#E8C09A"),
        star(400, 632, 22, 8, 6, "#E8C09A"),
        star(168, 400, 22, 8, 6, "#C4634F"),
        star(632, 400, 22, 8, 6, "#C4634F"),
        star(230, 230, 16, 6, 5, "#E8C09A"),
        star(570, 230, 16, 6, 5, "#E8C09A"),
        star(230, 570, 14, 5, 5, "#C4634F"),
        star(570, 570, 14, 5, 5, "#C4634F"),
        txt(400, 318, "WILD", "BebasNeue", 90, "#E8C09A", ls=4),
        txt(400, 378, "&amp;", "GreatVibes", 50, "#C4634F"),
        txt(400, 452, "FREE", "BebasNeue", 90, "#FFFFFF", ls=4),
        txt(400, 498, "untameable soul", "CormorantItalic", 19, "#E8C09A", ls=3),
    ])
    return wrap("Wild and Free", "#2B6040", body)


def d07_good_things():
    body = "\n".join([
        # Dense gold stars on navy — milky way feel
        *[star(400 + 280 * math.cos(math.radians(a)), 400 + 280 * math.sin(math.radians(a)),
               16, 6, 5, "#F5D030")
          for a in range(0, 360, 22)],
        *[star(400 + 340 * math.cos(math.radians(a)), 400 + 340 * math.sin(math.radians(a)),
               12, 5, 5, "#E8A030")
          for a in range(11, 360, 22)],
        *[star(400 + 200 * math.cos(math.radians(a)), 400 + 200 * math.sin(math.radians(a)),
               10, 4, 5, "#F5D030")
          for a in range(5, 360, 30)],
        # Inner circle bg
        circ(400, 400, 185, "#151E3F"),
        # Moon crescent suggestion (two circles)
        circ(430, 340, 70, "#F5D030"),
        circ(455, 330, 62, "#151E3F"),
        # Text
        txt(400, 434, "GOOD THINGS", "Cormorant", 24, "#F5D030", ls=5),
        txt(400, 492, "coming", "GreatVibes", 56, "#C47AE8"),
        txt(400, 536, "your way", "CormorantItalic", 22, "#F5D030", ls=4),
        # Tiny stars in corners
        star(70, 70, 20, 8, 5, "#F5D030"),
        star(730, 70, 20, 8, 5, "#C47AE8"),
        star(70, 730, 18, 7, 5, "#C47AE8"),
        star(730, 730, 18, 7, 5, "#F5D030"),
    ])
    return wrap("Good Things Coming", "#151E3F", body)


def d08_flower_power():
    body = "\n".join([
        # Multiple flowers scattered
        petal_flower(400, 400, 130, 8, "#F5D030", "#E84B8A", rc=38),
        # Smaller surrounding flowers
        petal_flower(200, 200, 72, 6, "#FFFFFF", "#F5D030", rc=22),
        petal_flower(600, 200, 72, 6, "#F0A020", "#FFFFFF", rc=22),
        petal_flower(200, 600, 72, 6, "#F5D030", "#1B9E8A", rc=22),
        petal_flower(600, 600, 72, 6, "#FFFFFF", "#E84B8A", rc=22),
        petal_flower(400, 130, 54, 5, "#F0A020", "#FFFFFF", rc=18),
        petal_flower(400, 670, 54, 5, "#FFFFFF", "#F0A020", rc=18),
        petal_flower(130, 400, 54, 5, "#E84B8A", "#F5D030", rc=18),
        petal_flower(670, 400, 54, 5, "#F5D030", "#E84B8A", rc=18),
        # White circle over center
        circ(400, 400, 90, "#FFFFFF"),
        txt(400, 382, "FLOWER", "BebasNeue", 34, "#E84B8A", ls=2),
        txt(400, 426, "POWER", "BebasNeue", 34, "#F0A020", ls=2),
    ])
    return wrap("Flower Power", "#FF6B51", body)


def d09_peace_love():
    body = "\n".join([
        sunburst(400, 400, 420, 60, ["#E84B8A", "#F5D030", "#1B9E8A", "#7B35B0"]),
        circ(400, 400, 290, "#7CC644"),
        ring_dots(400, 400, 273, 48, 6, "#FFFFFF"),
        circ(400, 400, 262, "#7CC644"),
        # Peace symbol simplified — circle + lines
        circ(400, 400, 150, "#FFFFFF"),
        '  <line x1="400" y1="250" x2="400" y2="550" stroke="#7CC644" stroke-width="14" stroke-linecap="round"/>',
        '  <line x1="400" y1="400" x2="294" y2="503" stroke="#7CC644" stroke-width="14" stroke-linecap="round"/>',
        '  <line x1="400" y1="400" x2="506" y2="503" stroke="#7CC644" stroke-width="14" stroke-linecap="round"/>',
        # Text stacked inside circle band
        txt(400, 308, "PEACE", "BebasNeue", 36, "#FFFFFF", ls=4),
        txt(400, 372, "·  LOVE  ·", "GreatVibes", 32, "#F5D030"),
        txt(400, 418, "JOY", "BebasNeue", 36, "#FFFFFF", ls=4),
        # Corner stars
        star(80, 80, 22, 9, 6, "#F5D030"),
        star(720, 80, 22, 9, 6, "#E84B8A"),
        star(80, 720, 22, 9, 6, "#E84B8A"),
        star(720, 720, 22, 9, 6, "#F5D030"),
    ])
    return wrap("Peace Love Joy", "#7CC644", body)


def d10_radiate():
    body = "\n".join([
        sunburst(400, 400, 420, 30, ["#F5D030", "#F0B820"]),
        circ(400, 400, 285, "#D94830"),
        ring_dots(400, 400, 268, 44, 5, "#F5D030"),
        circ(400, 400, 258, "#D94830"),
        circ(400, 400, 200, "#FFFFFF"),
        circ(400, 400, 186, "#D94830"),
        ring_dots(400, 400, 186, 30, 4, "#F5D030"),
        circ(400, 400, 178, "#FFFFFF"),
        txt(400, 368, "RADIATE", "BebasNeue", 58, "#D94830", ls=2),
        txt(400, 428, "positivity", "GreatVibes", 50, "#F5D030"),
        txt(400, 472, "ALWAYS", "Cormorant", 20, "#D94830", ls=8),
        star(120, 120, 22, 9, 5, "#F5D030"),
        star(680, 120, 22, 9, 5, "#FFFFFF"),
        star(120, 680, 22, 9, 5, "#FFFFFF"),
        star(680, 680, 22, 9, 5, "#F5D030"),
        star(400, 80, 18, 7, 5, "#FFFFFF"),
        star(80, 400, 18, 7, 5, "#FFFFFF"),
        star(720, 400, 18, 7, 5, "#FFFFFF"),
        star(400, 720, 18, 7, 5, "#FFFFFF"),
    ])
    return wrap("Radiate Positivity", "#D94830", body)


def d11_soul_fire():
    body = "\n".join([
        # Multiple flame layers, largest (darkest red) at back
        flame(400, 680, 480, 140, "#8B1A1A"),
        flame(360, 680, 400, 100, "#C43020"),
        flame(440, 680, 390, 100, "#C43020"),
        flame(390, 680, 440, 80, "#E06020"),
        flame(410, 680, 430, 80, "#E06020"),
        flame(400, 680, 460, 60, "#F5A020"),
        flame(400, 680, 480, 40, "#F5D030"),
        # Inner dark circle for text
        circ(400, 480, 195, "#1A0808"),
        circ(400, 480, 180, "#8B1A1A", stroke=None),
        ring_dots(400, 480, 180, 28, 5, "#F5A020"),
        circ(400, 480, 170, "#1A0808"),
        # Stars
        star(120, 120, 20, 8, 5, "#F5D030"),
        star(680, 120, 20, 8, 5, "#E06020"),
        star(120, 680, 16, 6, 5, "#F5A020"),
        star(680, 680, 16, 6, 5, "#F5D030"),
        # Text
        txt(400, 432, "SOUL", "BebasNeue", 72, "#F5D030", ls=3),
        txt(400, 490, "on", "GreatVibes", 40, "#F5A020"),
        txt(400, 540, "FIRE", "BebasNeue", 72, "#F0603A", ls=3),
    ])
    return wrap("Soul on Fire", "#1A0808", body)


def d12_dream_chaser():
    body = "\n".join([
        # Gold star field
        *[star(400 + 300 * math.cos(math.radians(a)), 400 + 300 * math.sin(math.radians(a)),
               14, 5, 5, "#F5D030")
          for a in range(0, 360, 18)],
        *[star(400 + 370 * math.cos(math.radians(a)), 400 + 370 * math.sin(math.radians(a)),
               10, 4, 5, "#C47AE8")
          for a in range(9, 360, 18)],
        # Arch top — dream arch
        arch(400, 520, 300, 46,
             ["#C47AE8", "#9B59E8", "#7B35B0", "#5B1080", "#3D0060"]),
        circ(400, 520, 72, "#0D1B3E"),
        # Text
        txt(400, 296, "DREAM", "BebasNeue", 70, "#C47AE8", ls=3),
        txt(400, 368, "chaser", "GreatVibes", 72, "#F5D030"),
        txt(400, 428, "✦  reach for the stars  ✦", "CormorantItalic", 16, "#C47AE8", ls=2),
        # Tiny scattered stars everywhere
        star(80, 120, 12, 5, 4, "#F5D030"),
        star(720, 140, 14, 5, 5, "#C47AE8"),
        star(100, 680, 12, 5, 4, "#C47AE8"),
        star(700, 660, 14, 5, 5, "#F5D030"),
        star(400, 80, 18, 7, 5, "#F5D030"),
        star(150, 400, 14, 5, 5, "#C47AE8"),
        star(650, 400, 14, 5, 5, "#F5D030"),
    ])
    return wrap("Dream Chaser", "#0D1B3E", body)


def d13_wander():
    body = "\n".join([
        sunburst(400, 400, 420, 24, ["#1B9E8A", "#148070"]),
        circ(400, 400, 300, "#F07A1A"),
        circ(400, 400, 284, "#1B9E8A"),
        # Compass rose — 4 points as diamonds
        diamond(400, 290, 24, 110, "#FFFFFF"),
        diamond(400, 510, 24, 110, "#FFFFFF"),
        diamond(290, 400, 110, 24, "#FFFFFF"),
        diamond(510, 400, 110, 24, "#FFFFFF"),
        # Compass center
        circ(400, 400, 36, "#F07A1A"),
        circ(400, 400, 22, "#FFFFFF"),
        # Small diagonal points
        diamond(306, 306, 14, 14, "#F5D030"),
        diamond(494, 306, 14, 14, "#F5D030"),
        diamond(306, 494, 14, 14, "#F5D030"),
        diamond(494, 494, 14, 14, "#F5D030"),
        ring_dots(400, 400, 260, 36, 5, "#F5D030"),
        # Text outside compass
        txt(400, 186, "WANDER", "BebasNeue", 46, "#FFFFFF", ls=4),
        txt(400, 218, "OFTEN", "BebasNeue", 46, "#F5D030", ls=4),
        txt(400, 594, "WONDER", "BebasNeue", 46, "#FFFFFF", ls=4),
        txt(400, 626, "ALWAYS", "BebasNeue", 46, "#F5D030", ls=4),
        star(80, 80, 20, 8, 5, "#F5D030"),
        star(720, 80, 20, 8, 5, "#FFFFFF"),
        star(80, 720, 20, 8, 5, "#FFFFFF"),
        star(720, 720, 20, 8, 5, "#F5D030"),
    ])
    return wrap("Wander Often Wonder Always", "#1B9E8A", body)


def d14_life_colorful():
    # Horizontal rainbow stripe background then white text
    STRIPES = ["#D93030","#E87B2A","#F5D030","#2B8A3E","#1E6FCC","#7B35B0","#E84B8A"]
    body = "\n".join([
        stripe_bg(STRIPES, horizontal=True),
        # White semi-transparent band for text
        '  <rect x="60" y="310" width="680" height="200" fill="#FFFFFF" opacity="0.88" rx="14"/>',
        txt(400, 378, "LIFE IS", "BebasNeue", 60, "#1A1A2E", ls=4),
        txt(400, 458, "COLORFUL", "BebasNeue", 72, "#D93030", ls=3),
        # Stars in white at left and right
        star(50, 50, 22, 9, 5, "#FFFFFF"),
        star(750, 50, 22, 9, 5, "#FFFFFF"),
        star(50, 750, 22, 9, 5, "#FFFFFF"),
        star(750, 750, 22, 9, 5, "#FFFFFF"),
        star(50, 400, 16, 6, 5, "#FFFFFF"),
        star(750, 400, 16, 6, 5, "#FFFFFF"),
        txt(400, 530, "embrace every shade", "GreatVibes", 32, "#1A1A2E"),
    ])
    return wrap("Life Is Colorful", "#F5D030", body)


def d15_keep_growing():
    body = "\n".join([
        sunburst(400, 400, 420, 28, ["#8BA888", "#6B8A5E"]),
        circ(400, 400, 290, "#F5EDD6"),
        ring_dots(400, 400, 273, 44, 5, "#8BA888"),
        circ(400, 400, 263, "#F5EDD6"),
        # Leaf shapes as rotated ellipses in a ring
        *[f'  <ellipse cx="{400 + 200 * math.cos(math.radians(a)):.0f}" '
          f'cy="{400 + 200 * math.sin(math.radians(a)):.0f}" '
          f'rx="18" ry="36" fill="#6B8A5E" '
          f'transform="rotate({a + 90},{400 + 200 * math.cos(math.radians(a)):.0f},'
          f'{400 + 200 * math.sin(math.radians(a)):.0f})"/>'
          for a in range(0, 360, 36)],
        circ(400, 400, 175, "#F5EDD6"),
        txt(400, 344, "KEEP", "BebasNeue", 64, "#6B8A5E", ls=3),
        txt(400, 408, "growing", "GreatVibes", 68, "#C4634F"),
        txt(400, 460, "BLOOM WHERE YOU'RE PLANTED", "Cormorant", 14, "#6B8A5E", ls=3),
        # Tiny terracotta dots in corners
        circ(100, 100, 14, "#C4634F"),
        circ(700, 100, 14, "#C4634F"),
        circ(100, 700, 14, "#C4634F"),
        circ(700, 700, 14, "#C4634F"),
        star(400, 76, 18, 7, 5, "#C4634F"),
        star(76, 400, 18, 7, 5, "#C4634F"),
        star(724, 400, 18, 7, 5, "#C4634F"),
        star(400, 724, 18, 7, 5, "#C4634F"),
    ])
    return wrap("Keep Growing", "#6B8A5E", body)


def d16_magic_happens():
    body = "\n".join([
        sunburst(400, 400, 420, 40, ["#F5D030", "#E8A020"], r_in=0),
        circ(400, 400, 290, "#4A1A80"),
        ring_dots(400, 400, 272, 44, 5, "#F5D030"),
        circ(400, 400, 262, "#4A1A80"),
        # 4-point sparkle stars scattered
        star(400, 180, 30, 8, 4, "#F5D030"),
        star(400, 620, 30, 8, 4, "#F5D030"),
        star(180, 400, 30, 8, 4, "#E84B8A"),
        star(620, 400, 30, 8, 4, "#E84B8A"),
        star(240, 240, 22, 6, 4, "#F5D030"),
        star(560, 240, 22, 6, 4, "#E84B8A"),
        star(240, 560, 22, 6, 4, "#E84B8A"),
        star(560, 560, 22, 6, 4, "#F5D030"),
        # Tiny stars
        star(160, 310, 12, 4, 4, "#F5D030"),
        star(640, 310, 12, 4, 4, "#E84B8A"),
        star(160, 490, 12, 4, 4, "#E84B8A"),
        star(640, 490, 12, 4, 4, "#F5D030"),
        txt(400, 334, "MAGIC", "BebasNeue", 76, "#F5D030", ls=3),
        txt(400, 394, "happens", "GreatVibes", 56, "#E84B8A"),
        txt(400, 440, "HERE", "BebasNeue", 76, "#FFFFFF", ls=3),
        txt(400, 486, "✦  believe  ✦", "CormorantItalic", 18, "#F5D030", ls=3),
    ])
    return wrap("Magic Happens Here", "#4A1A80", body)


def d17_happy_chaos():
    body = "\n".join([
        # Scattered colorful shapes — confetti feel
        checker_border(40, 40, "#E84B8A", "#F5D030"),
        # Scatter colorful circles and stars inside
        circ(200, 200, 44, "#1B9E8A"),
        circ(600, 200, 38, "#D93030"),
        circ(180, 600, 40, "#7B35B0"),
        circ(620, 600, 42, "#F07A1A"),
        circ(400, 180, 32, "#E84B8A"),
        circ(400, 620, 32, "#1B9E8A"),
        circ(170, 400, 36, "#F5D030"),
        circ(630, 400, 36, "#D93030"),
        star(280, 280, 28, 11, 5, "#D93030"),
        star(520, 280, 26, 10, 5, "#7B35B0"),
        star(280, 520, 26, 10, 5, "#F07A1A"),
        star(520, 520, 28, 11, 5, "#1B9E8A"),
        # White center
        circ(400, 400, 210, "#FAFAFA"),
        txt(400, 358, "HAPPY", "BebasNeue", 70, "#E84B8A", ls=3),
        txt(400, 418, "chaos", "GreatVibes", 72, "#F07A1A"),
        txt(400, 466, "it's my superpower", "CormorantItalic", 18, "#1A1A2E", ls=2),
    ])
    return wrap("Happy Chaos", "#F5D030", body)


def d18_sun_child():
    body = "\n".join([
        # 16-ray sunburst
        sunburst(400, 400, 420, 16, ["#F5D030", "#FFE870"]),
        circ(400, 400, 250, "#D44A1A"),
        ring_dots(400, 400, 233, 36, 5, "#F5D030"),
        circ(400, 400, 222, "#D44A1A"),
        # Big sun face
        circ(400, 350, 140, "#F5D030"),
        circ(362, 326, 16, "#D44A1A"),   # left eye
        circ(438, 326, 16, "#D44A1A"),   # right eye
        '  <path d="M 356,372 Q 400,404 444,372" stroke="#D44A1A" stroke-width="8" fill="none" stroke-linecap="round"/>',
        circ(336, 360, 18, "#F0A020"),  # left cheek
        circ(464, 360, 18, "#F0A020"),  # right cheek
        # Text
        txt(400, 548, "SUN", "BebasNeue", 70, "#F5D030", ls=4),
        txt(400, 606, "CHILD", "BebasNeue", 70, "#FFFFFF", ls=4),
        # Corner stars
        star(90, 90, 24, 9, 5, "#F5D030"),
        star(710, 90, 24, 9, 5, "#FFFFFF"),
        star(90, 710, 22, 9, 5, "#FFFFFF"),
        star(710, 710, 22, 9, 5, "#F5D030"),
    ])
    return wrap("Sun Child", "#D44A1A", body)


def d19_bloom():
    body = "\n".join([
        # Flower border ring
        *[petal_flower(
            400 + 320 * math.cos(math.radians(a)),
            400 + 320 * math.sin(math.radians(a)),
            40, 5,
            ["#F5D030","#FFFFFF","#F0A020","#FFB3C6","#7CC644"][i % 5],
            "#E84B8A", rc=13)
          for i, a in enumerate(range(0, 360, 30))],
        circ(400, 400, 270, "#E85C8C"),
        ring_dots(400, 400, 252, 40, 5, "#FFFFFF"),
        circ(400, 400, 242, "#E85C8C"),
        # Central flower
        petal_flower(400, 380, 100, 6, "#F5D030", "#FFFFFF", rc=30),
        # Text
        txt(400, 508, "BLOOM", "BebasNeue", 76, "#FFFFFF", ls=4),
        txt(400, 558, "be brave, grow wild", "GreatVibes", 32, "#F5D030"),
        txt(400, 600, "✦  ✦  ✦", "Cormorant", 16, "#FFFFFF"),
        # Corner mini flowers
        petal_flower(82, 82, 40, 5, "#F5D030", "#FFFFFF", rc=12),
        petal_flower(718, 82, 40, 5, "#FFFFFF", "#F5D030", rc=12),
        petal_flower(82, 718, 40, 5, "#F5D030", "#FFFFFF", rc=12),
        petal_flower(718, 718, 40, 5, "#FFFFFF", "#F5D030", rc=12),
    ])
    return wrap("Bloom", "#E84B8A", body)


def d20_you_are_rainbow():
    body = "\n".join([
        # Clouds flanking the base of the rainbow
        cloud(110, 620, 70, "#FFFFFF"),
        cloud(690, 620, 70, "#FFFFFF"),
        # Full rainbow arch — center at (400, 620), 7 colors, band=46
        arch(400, 620, 394, 52,
             ["#D93030","#E87B2A","#F5D030","#2B8A3E","#1E6FCC","#7B35B0","#E84B8A"]),
        # Sky fill — white circle under rainbow
        circ(400, 620, 30, "#F5F5FF"),
        # Clouds on arch
        cloud(400, 280, 56, "#FFFFFF"),
        # Corner stars
        star(80, 100, 24, 9, 5, "#F5D030"),
        star(720, 100, 22, 9, 5, "#E84B8A"),
        star(80, 650, 16, 6, 5, "#1E6FCC"),
        star(720, 650, 16, 6, 5, "#D93030"),
        star(400, 90, 20, 8, 5, "#7B35B0"),
        # Small dot stars
        *[circ(400 + 340 * math.cos(math.radians(a)), 400 + 340 * math.sin(math.radians(a)),
               4, "#F5D030")
          for a in range(200, 340, 12)],
        # Bold text below arch
        txt(400, 540, "YOU ARE A", "Cormorant", 26, "#1A1A2E", ls=6),
        txt(400, 618, "RAINBOW", "BebasNeue", 80, "#D93030", ls=3),
        txt(400, 672, "brilliant, bold, and full of color", "GreatVibes", 26, "#7B35B0"),
    ])
    return wrap("You Are a Rainbow", "#F0F8FF", body)


# ─── Generate all ─────────────────────────────────────────────────────────────

DESIGNS = [
    ("groovy_01_good_vibes.svg",       d01_good_vibes()),
    ("groovy_02_stay_groovy.svg",       d02_stay_groovy()),
    ("groovy_03_spread_love.svg",       d03_spread_love()),
    ("groovy_04_be_weird.svg",          d04_be_weird()),
    ("groovy_05_choose_happy.svg",      d05_choose_happy()),
    ("groovy_06_wild_free.svg",         d06_wild_free()),
    ("groovy_07_good_things.svg",       d07_good_things()),
    ("groovy_08_flower_power.svg",      d08_flower_power()),
    ("groovy_09_peace_love.svg",        d09_peace_love()),
    ("groovy_10_radiate.svg",           d10_radiate()),
    ("groovy_11_soul_fire.svg",         d11_soul_fire()),
    ("groovy_12_dream_chaser.svg",      d12_dream_chaser()),
    ("groovy_13_wander.svg",            d13_wander()),
    ("groovy_14_life_colorful.svg",     d14_life_colorful()),
    ("groovy_15_keep_growing.svg",      d15_keep_growing()),
    ("groovy_16_magic_happens.svg",     d16_magic_happens()),
    ("groovy_17_happy_chaos.svg",       d17_happy_chaos()),
    ("groovy_18_sun_child.svg",         d18_sun_child()),
    ("groovy_19_bloom.svg",             d19_bloom()),
    ("groovy_20_rainbow.svg",           d20_you_are_rainbow()),
]

os.makedirs(OUT_DIR, exist_ok=True)
for fname, svg in DESIGNS:
    path = os.path.join(OUT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"✓ {fname}")

print(f"\n✅ All {len(DESIGNS)} designs written to {OUT_DIR}/")
