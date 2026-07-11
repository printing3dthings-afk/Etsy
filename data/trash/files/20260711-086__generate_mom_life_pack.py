#!/usr/bin/env python3
"""
Generate Mom Life SVG Pack — 20 designs optimized for Etsy top-seller positioning.
Font stack: Bebas Neue + Great Vibes + Cormorant Garamond
"""
import os, math

FONT_DEFS = '''  <defs>
    <style>
      @font-face { font-family: 'BebasNeue'; src: url('/usr/local/share/fonts/BebasNeue-Regular.ttf'); }
      @font-face { font-family: 'GreatVibes'; src: url('/usr/local/share/fonts/GreatVibes-Regular.ttf'); }
      @font-face { font-family: 'Cormorant'; src: url('/usr/local/share/fonts/CormorantGaramond-Bold.ttf'); }
      @font-face { font-family: 'CormorantItalic'; src: url('/usr/local/share/fonts/CormorantGaramond-BoldItalic.ttf'); }
      @font-face { font-family: 'Cinzel'; src: url('/usr/local/share/fonts/Cinzel-Regular.ttf'); }
      @font-face { font-family: 'CinzelDec'; src: url('/usr/local/share/fonts/CinzelDecorative-Bold.ttf'); }
    </style>
  </defs>'''

OUT_DIR = "data/mom_life_pack/SVG"


def svg_wrap(title, content):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <title>{title}</title>
  <rect width="800" height="800" fill="none"/>
{FONT_DEFS}
{content}
</svg>'''


# ─── Decorative element builders ───────────────────────────────────────────────

def sunburst(cx, cy, r_inner, r_outer, rays, stroke="black", sw=1.5):
    """Alternating long/short sunburst rays."""
    paths = []
    for i in range(rays * 2):
        angle = math.radians(i * 180 / rays - 90)
        r = r_outer if i % 2 == 0 else (r_inner + r_outer) / 2
        x1 = cx + r_inner * math.cos(angle)
        y1 = cy + r_inner * math.sin(angle)
        x2 = cx + r * math.cos(angle)
        y2 = cy + r * math.sin(angle)
        paths.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"/>')
    return "\n".join(paths)


def diamond_border(margin=40, inner_margin=54, stroke="black", sw=2, sw_inner=1):
    """Square frame with corner diamonds."""
    m, i = margin, inner_margin
    lines = [
        f'<rect x="{m}" y="{m}" width="{800-2*m}" height="{800-2*m}" fill="none" stroke="{stroke}" stroke-width="{sw}"/>',
        f'<rect x="{i}" y="{i}" width="{800-2*i}" height="{800-2*i}" fill="none" stroke="{stroke}" stroke-width="{sw_inner}"/>',
    ]
    for cx, cy in [(m, m), (800-m, m), (800-m, 800-m), (m, 800-m)]:
        lines.append(f'<polygon points="{cx},{cy-10} {cx+10},{cy} {cx},{cy+10} {cx-10},{cy}" fill="{stroke}"/>')
    return "\n".join(lines)


def wreath_arc(cx, cy, r, start_deg, end_deg, leaf_count=14, stroke="black", sw=1.2):
    """Arc of small leaf shapes."""
    elems = []
    for k in range(leaf_count):
        t = start_deg + (end_deg - start_deg) * k / (leaf_count - 1)
        rad = math.radians(t)
        x = cx + r * math.cos(rad)
        y = cy + r * math.sin(rad)
        # leaf orientation tangent to circle
        tang = math.radians(t + 90)
        lx1 = x + 7 * math.cos(tang)
        ly1 = y + 7 * math.sin(tang)
        lx2 = x - 7 * math.cos(tang)
        ly2 = y - 7 * math.sin(tang)
        nx = x + 5 * math.cos(rad)
        ny = y + 5 * math.sin(rad)
        elems.append(f'<path d="M {lx1:.1f},{ly1:.1f} Q {nx:.1f},{ny:.1f} {lx2:.1f},{ly2:.1f}" fill="{stroke}" stroke="none"/>')
    return "\n".join(elems)


def circle_dot_ring(cx, cy, r, count=48, r_dot=2, fill="black"):
    dots = []
    for i in range(count):
        a = math.radians(360 * i / count)
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        dots.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r_dot}" fill="{fill}"/>')
    return "\n".join(dots)


def star_burst_ring(cx, cy, r, count=8, fill="black"):
    stars = []
    for i in range(count):
        a = math.radians(360 * i / count - 90)
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        s = 5
        pts = ""
        for j in range(8):
            ra = math.radians(j * 45)
            ri = s if j % 2 == 0 else s * 0.4
            pts += f"{x+ri*math.cos(ra):.1f},{y+ri*math.sin(ra):.1f} "
        stars.append(f'<polygon points="{pts.strip()}" fill="{fill}"/>')
    return "\n".join(stars)


def double_circle(cx, cy, r1=310, r2=295, stroke="black", sw1=2.5, sw2=1):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r1}" fill="none" stroke="{stroke}" stroke-width="{sw1}"/>\n'
            f'<circle cx="{cx}" cy="{cy}" r="{r2}" fill="none" stroke="{stroke}" stroke-width="{sw2}"/>')


def corner_flourish(margin=50, size=30, stroke="black", sw=1.5):
    """L-shaped corner accents with dot."""
    elems = []
    corners = [(margin, margin, 1, 1), (800-margin, margin, -1, 1),
               (800-margin, 800-margin, -1, -1), (margin, 800-margin, 1, -1)]
    for cx, cy, dx, dy in corners:
        elems.append(f'<path d="M {cx+dx*size},{cy} L {cx},{cy} L {cx},{cy+dy*size}" '
                     f'fill="none" stroke="{stroke}" stroke-width="{sw}"/>')
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="3" fill="{stroke}"/>')
    return "\n".join(elems)


def horizontal_rules(y, width=500, cx=400, stroke="black", sw=1):
    x0 = cx - width / 2
    x1 = cx + width / 2
    return f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{stroke}" stroke-width="{sw}"/>'


def diamond_divider(cx, cy, total_w=300, stroke="black", sw=1):
    """  ——— ◆ ——— """
    hw = total_w / 2
    d = 6
    return (f'<line x1="{cx-hw}" y1="{cy}" x2="{cx-d-4}" y2="{cy}" stroke="{stroke}" stroke-width="{sw}"/>'
            f'<polygon points="{cx},{cy-d} {cx+d},{cy} {cx},{cy+d} {cx-d},{cy}" fill="{stroke}"/>'
            f'<line x1="{cx+d+4}" y1="{cy}" x2="{cx+hw}" y2="{cy}" stroke="{stroke}" stroke-width="{sw}"/>')


def dot_divider(cx, cy, total_w=260, count=5, stroke="black", r=2):
    step = total_w / (count - 1)
    dots = []
    for i in range(count):
        x = cx - total_w / 2 + i * step
        dots.append(f'<circle cx="{x:.1f}" cy="{cy}" r="{r}" fill="{stroke}"/>')
    return "\n".join(dots)


def arc_text(text, cx, cy, r, start_deg, end_deg, font_family, font_size,
             fill="black", letter_spacing=2):
    """Place text along a circular arc."""
    chars = list(text)
    n = len(chars)
    span = end_deg - start_deg
    chars_spanned = n - 1
    if chars_spanned == 0:
        chars_spanned = 1
    step = span / chars_spanned
    elems = []
    for i, ch in enumerate(chars):
        angle_deg = start_deg + i * step
        angle_rad = math.radians(angle_deg)
        x = cx + r * math.cos(angle_rad)
        y = cy + r * math.sin(angle_rad)
        rot = angle_deg + 90
        elems.append(
            f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle" '
            f'font-family="{font_family}" font-size="{font_size}" fill="{fill}" '
            f'transform="rotate({rot:.1f},{x:.2f},{y:.2f})">{ch}</text>'
        )
    return "\n".join(elems)


# ─── Individual design functions ────────────────────────────────────────────────

def design_01_blessed_mama():
    content = f"""
  {diamond_border(40, 56)}
  {corner_flourish(60, 22)}
  <text x="400" y="220" text-anchor="middle" font-family="Cormorant, serif" font-size="22" fill="black" letter-spacing="8">✦  EST. THE MOMENT  ✦</text>
  <text x="400" y="256" text-anchor="middle" font-family="Cormorant, serif" font-size="22" fill="black" letter-spacing="8">I BECAME YOUR MOM</text>
  {diamond_divider(400, 278, 320)}
  <text x="400" y="370" text-anchor="middle" font-family="GreatVibes, cursive" font-size="110" fill="black">Blessed</text>
  <text x="400" y="430" text-anchor="middle" font-family="GreatVibes, cursive" font-size="70" fill="black">Mama</text>
  {diamond_divider(400, 452, 320)}
  <text x="400" y="508" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="32" fill="black" letter-spacing="6">GRATEFUL · LOVED · CHOSEN</text>
  <text x="400" y="548" text-anchor="middle" font-family="CormorantItalic, serif" font-size="18" fill="black" letter-spacing="3">motherhood is my greatest blessing</text>
"""
    return svg_wrap("Blessed Mama SVG", content)


def design_02_coffee_chaos():
    content = f"""
  {double_circle(400, 400, 330, 313)}
  {circle_dot_ring(400, 400, 296, 60, 1.5)}
  <text x="400" y="248" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="5">RUNNING ON</text>
  {diamond_divider(400, 266, 200)}
  <text x="400" y="346" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="82" fill="black" letter-spacing="3">COFFEE</text>
  <text x="400" y="396" text-anchor="middle" font-family="GreatVibes, cursive" font-size="54" fill="black">&amp; Chaos</text>
  {diamond_divider(400, 415, 220)}
  <text x="400" y="465" text-anchor="middle" font-family="Cormorant, serif" font-size="22" fill="black" letter-spacing="4">BUT MOSTLY LOVE</text>
  <text x="400" y="500" text-anchor="middle" font-family="CormorantItalic, serif" font-size="16" fill="black" letter-spacing="3">· mama life ·</text>
"""
    return svg_wrap("Coffee and Chaos SVG", content)


def design_03_messy_bun():
    # Pentagon-badge style outer shape
    pts = []
    cx, cy, R = 400, 380, 320
    for i in range(5):
        a = math.radians(-90 + i * 72)
        pts.append(f"{cx + R*math.cos(a):.1f},{cy + R*math.sin(a):.1f}")
    pentagon = " ".join(pts)
    inner_pts = []
    for i in range(5):
        a = math.radians(-90 + i * 72)
        inner_pts.append(f"{cx + (R-18)*math.cos(a):.1f},{cy + (R-18)*math.sin(a):.1f}")
    inner_pentagon = " ".join(inner_pts)

    content = f"""
  <polygon points="{pentagon}" fill="none" stroke="black" stroke-width="2.5"/>
  <polygon points="{inner_pentagon}" fill="none" stroke="black" stroke-width="1"/>
  <text x="400" y="196" text-anchor="middle" font-family="Cormorant, serif" font-size="18" fill="black" letter-spacing="5">★  OFFICIALLY A  ★</text>
  <text x="400" y="304" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="70" fill="black" letter-spacing="2">MESSY BUN</text>
  <text x="400" y="364" text-anchor="middle" font-family="GreatVibes, cursive" font-size="72" fill="black">&amp; getting</text>
  <text x="400" y="424" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="50" fill="black" letter-spacing="4">STUFF DONE</text>
  <text x="400" y="476" text-anchor="middle" font-family="CormorantItalic, serif" font-size="17" fill="black" letter-spacing="4">· mom life ·</text>
  <text x="400" y="560" text-anchor="middle" font-family="Cormorant, serif" font-size="17" fill="black" letter-spacing="3">PROUD MEMBER CLUB</text>
"""
    return svg_wrap("Messy Bun SVG", content)


def design_04_boy_mom():
    content = f"""
  {double_circle(400, 400, 320, 302)}
  {star_burst_ring(400, 400, 285, 12)}
  <text x="400" y="256" text-anchor="middle" font-family="Cormorant, serif" font-size="20" fill="black" letter-spacing="6">PROUD TO BE A</text>
  {diamond_divider(400, 274, 240)}
  <text x="400" y="354" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="82" fill="black" letter-spacing="4">BOY MOM</text>
  {diamond_divider(400, 373, 240)}
  <text x="400" y="424" text-anchor="middle" font-family="GreatVibes, cursive" font-size="58" fill="black">loud &amp; wild</text>
  <text x="400" y="468" text-anchor="middle" font-family="Cormorant, serif" font-size="20" fill="black" letter-spacing="4">AND I WOULDN'T CHANGE</text>
  <text x="400" y="498" text-anchor="middle" font-family="Cormorant, serif" font-size="20" fill="black" letter-spacing="4">A SINGLE THING</text>
"""
    return svg_wrap("Boy Mom SVG", content)


def design_05_girl_mom():
    content = f"""
  {diamond_border(38, 56)}
  {corner_flourish(62, 24)}
  <text x="400" y="200" text-anchor="middle" font-family="GreatVibes, cursive" font-size="42" fill="black">she is</text>
  {dot_divider(400, 220, 260, 7)}
  <text x="400" y="308" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="86" fill="black" letter-spacing="3">GIRL MOM</text>
  {dot_divider(400, 328, 260, 7)}
  <text x="400" y="384" text-anchor="middle" font-family="GreatVibes, cursive" font-size="54" fill="black">glitter, sass</text>
  <text x="400" y="432" text-anchor="middle" font-family="GreatVibes, cursive" font-size="54" fill="black">&amp; a whole lotta love</text>
  {diamond_divider(400, 456, 300)}
  <text x="400" y="506" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="6">RAISING STRONG WOMEN</text>
  <text x="400" y="538" text-anchor="middle" font-family="CormorantItalic, serif" font-size="16" fill="black" letter-spacing="3">one beautiful day at a time</text>
"""
    return svg_wrap("Girl Mom SVG", content)


def design_06_mama_bear():
    content = f"""
  {double_circle(400, 400, 328, 310)}
  {circle_dot_ring(400, 400, 293, 52, 1.8)}
  <text x="400" y="240" text-anchor="middle" font-family="Cormorant, serif" font-size="20" fill="black" letter-spacing="6">DON'T MESS WITH</text>
  {diamond_divider(400, 258, 220)}
  <text x="400" y="360" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="80" fill="black" letter-spacing="3">MAMA</text>
  <text x="400" y="434" text-anchor="middle" font-family="GreatVibes, cursive" font-size="86" fill="black">Bear</text>
  {diamond_divider(400, 454, 220)}
  <text x="400" y="510" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="5">SHE WILL FIND YOU</text>
"""
    return svg_wrap("Mama Bear SVG", content)


def design_07_soccer_mom():
    content = f"""
  {diamond_border(40, 57)}
  {corner_flourish(62, 24)}
  <text x="400" y="186" text-anchor="middle" font-family="CormorantItalic, serif" font-size="22" fill="black" letter-spacing="4">officially a</text>
  {diamond_divider(400, 205, 260)}
  <text x="400" y="288" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="88" fill="black" letter-spacing="2">SOCCER</text>
  <text x="400" y="370" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="88" fill="black" letter-spacing="2">MOM</text>
  {diamond_divider(400, 390, 260)}
  <text x="400" y="448" text-anchor="middle" font-family="GreatVibes, cursive" font-size="52" fill="black">sideline squad</text>
  {dot_divider(400, 470, 200, 5)}
  <text x="400" y="516" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="5">COFFEE · CAMPCHAIR · CARPOOL</text>
  <text x="400" y="550" text-anchor="middle" font-family="CormorantItalic, serif" font-size="15" fill="black" letter-spacing="3">this is my cardio</text>
"""
    return svg_wrap("Soccer Mom SVG", content)


def design_08_minivan_mama():
    content = f"""
  {double_circle(400, 400, 325, 307)}
  {star_burst_ring(400, 400, 290, 16)}
  <text x="400" y="238" text-anchor="middle" font-family="GreatVibes, cursive" font-size="38" fill="black">riding in style in my</text>
  {diamond_divider(400, 257, 200)}
  <text x="400" y="334" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="74" fill="black" letter-spacing="2">MINIVAN</text>
  {diamond_divider(400, 353, 200)}
  <text x="400" y="414" text-anchor="middle" font-family="GreatVibes, cursive" font-size="64" fill="black">Mama</text>
  <text x="400" y="458" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="4">SNACKS · CHAOS · LOVE</text>
  {dot_divider(400, 478, 180, 5)}
  <text x="400" y="522" text-anchor="middle" font-family="CormorantItalic, serif" font-size="16" fill="black" letter-spacing="3">the ultimate family hauler</text>
"""
    return svg_wrap("Minivan Mama SVG", content)


def design_09_tired_but_blessed():
    content = f"""
  {diamond_border(38, 55)}
  {corner_flourish(60, 24)}
  <text x="400" y="202" text-anchor="middle" font-family="Cormorant, serif" font-size="24" fill="black" letter-spacing="7">SHE IS</text>
  {diamond_divider(400, 220, 160)}
  <text x="400" y="312" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="82" fill="black" letter-spacing="2">TIRED</text>
  <text x="400" y="364" text-anchor="middle" font-family="GreatVibes, cursive" font-size="56" fill="black">but oh so</text>
  <text x="400" y="456" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="82" fill="black" letter-spacing="2">BLESSED</text>
  {diamond_divider(400, 476, 280)}
  <text x="400" y="530" text-anchor="middle" font-family="CormorantItalic, serif" font-size="18" fill="black" letter-spacing="4">motherhood is the good stuff</text>
  {dot_divider(400, 552, 200, 5)}
  <text x="400" y="592" text-anchor="middle" font-family="Cormorant, serif" font-size="16" fill="black" letter-spacing="5">· mama life ·</text>
"""
    return svg_wrap("Tired But Blessed SVG", content)


def design_10_wine_time():
    content = f"""
  {double_circle(400, 400, 322, 305)}
  {circle_dot_ring(400, 400, 288, 56, 1.5)}
  <text x="400" y="244" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="5">IT'S OFFICIALLY</text>
  {diamond_divider(400, 262, 190)}
  <text x="400" y="348" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="80" fill="black" letter-spacing="3">WINE</text>
  <text x="400" y="410" text-anchor="middle" font-family="GreatVibes, cursive" font-size="72" fill="black">o'clock</text>
  {diamond_divider(400, 430, 190)}
  <text x="400" y="480" text-anchor="middle" font-family="Cormorant, serif" font-size="20" fill="black" letter-spacing="4">SOMEWHERE IN MOM WORLD</text>
  <text x="400" y="514" text-anchor="middle" font-family="CormorantItalic, serif" font-size="16" fill="black" letter-spacing="3">you deserve it, mama</text>
"""
    return svg_wrap("Wine O'Clock SVG", content)


def design_11_fur_mama():
    content = f"""
  {diamond_border(40, 57)}
  {corner_flourish(62, 26)}
  <text x="400" y="198" text-anchor="middle" font-family="CormorantItalic, serif" font-size="21" fill="black" letter-spacing="5">PROUD TO BE A</text>
  {diamond_divider(400, 218, 240)}
  <text x="400" y="302" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="80" fill="black" letter-spacing="2">FUR MAMA</text>
  {diamond_divider(400, 322, 240)}
  <text x="400" y="384" text-anchor="middle" font-family="GreatVibes, cursive" font-size="58" fill="black">unconditional love</text>
  <text x="400" y="432" text-anchor="middle" font-family="GreatVibes, cursive" font-size="58" fill="black">four paws at a time</text>
  {dot_divider(400, 455, 240, 7)}
  <text x="400" y="502" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="5">DOGS ARE FAMILY</text>
  <text x="400" y="535" text-anchor="middle" font-family="CormorantItalic, serif" font-size="15" fill="black" letter-spacing="3">end of discussion</text>
"""
    return svg_wrap("Fur Mama SVG", content)


def design_12_hot_mess():
    content = f"""
  {double_circle(400, 400, 325, 308)}
  {star_burst_ring(400, 400, 292, 12)}
  <text x="400" y="240" text-anchor="middle" font-family="GreatVibes, cursive" font-size="40" fill="black">warning:</text>
  {diamond_divider(400, 258, 200)}
  <text x="400" y="334" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="74" fill="black" letter-spacing="2">HOT MESS</text>
  <text x="400" y="404" text-anchor="middle" font-family="GreatVibes, cursive" font-size="80" fill="black">Express</text>
  {diamond_divider(400, 424, 200)}
  <text x="400" y="476" text-anchor="middle" font-family="Cormorant, serif" font-size="20" fill="black" letter-spacing="4">BOARDING NOW</text>
  <text x="400" y="514" text-anchor="middle" font-family="CormorantItalic, serif" font-size="15" fill="black" letter-spacing="3">destination: mom life</text>
"""
    return svg_wrap("Hot Mess Express SVG", content)


def design_13_nap_time():
    content = f"""
  {diamond_border(38, 55)}
  {corner_flourish(60, 26)}
  <text x="400" y="196" text-anchor="middle" font-family="Cormorant, serif" font-size="22" fill="black" letter-spacing="6">IS IT</text>
  {diamond_divider(400, 215, 140)}
  <text x="400" y="300" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="86" fill="black" letter-spacing="2">NAP TIME</text>
  <text x="400" y="356" text-anchor="middle" font-family="GreatVibes, cursive" font-size="56" fill="black">yet?</text>
  {diamond_divider(400, 376, 200)}
  <text x="400" y="432" text-anchor="middle" font-family="Cormorant, serif" font-size="20" fill="black" letter-spacing="5">ASKING FOR THE MOM</text>
  {dot_divider(400, 454, 220, 7)}
  <text x="400" y="500" text-anchor="middle" font-family="CormorantItalic, serif" font-size="18" fill="black" letter-spacing="4">who is also the kids</text>
  <text x="400" y="530" text-anchor="middle" font-family="CormorantItalic, serif" font-size="18" fill="black" letter-spacing="4">who needs the nap</text>
  {dot_divider(400, 554, 140, 5)}
  <text x="400" y="590" text-anchor="middle" font-family="Cormorant, serif" font-size="14" fill="black" letter-spacing="4">· same, mom, same ·</text>
"""
    return svg_wrap("Nap Time SVG", content)


def design_14_motherhood():
    content = f"""
  {double_circle(400, 400, 322, 304)}
  {circle_dot_ring(400, 400, 287, 52, 1.8)}
  <text x="400" y="244" text-anchor="middle" font-family="Cormorant, serif" font-size="21" fill="black" letter-spacing="7">THE ART OF</text>
  {diamond_divider(400, 264, 210)}
  <text x="400" y="370" text-anchor="middle" font-family="GreatVibes, cursive" font-size="96" fill="black">Motherhood</text>
  {diamond_divider(400, 392, 210)}
  <text x="400" y="448" text-anchor="middle" font-family="Cormorant, serif" font-size="20" fill="black" letter-spacing="5">LOVE WITHOUT LIMITS</text>
  <text x="400" y="480" text-anchor="middle" font-family="Cormorant, serif" font-size="20" fill="black" letter-spacing="5">GRACE WITHOUT END</text>
  <text x="400" y="516" text-anchor="middle" font-family="CormorantItalic, serif" font-size="16" fill="black" letter-spacing="3">my greatest work</text>
"""
    return svg_wrap("Motherhood SVG", content)


def design_15_chaos_coordinator():
    content = f"""
  {diamond_border(40, 58)}
  {corner_flourish(64, 26)}
  <text x="400" y="196" text-anchor="middle" font-family="CormorantItalic, serif" font-size="20" fill="black" letter-spacing="5">officially certified</text>
  {diamond_divider(400, 216, 280)}
  <text x="400" y="296" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="72" fill="black" letter-spacing="2">CHAOS</text>
  <text x="400" y="356" text-anchor="middle" font-family="GreatVibes, cursive" font-size="64" fill="black">Coordinator</text>
  {diamond_divider(400, 380, 280)}
  <text x="400" y="430" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="5">SNACK PROVIDER</text>
  <text x="400" y="462" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="5">BED-TIME NEGOTIATOR</text>
  <text x="400" y="494" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="5">PROFESSIONAL GOOGLER</text>
  {dot_divider(400, 516, 200, 5)}
  <text x="400" y="556" text-anchor="middle" font-family="GreatVibes, cursive" font-size="32" fill="black">aka mom</text>
"""
    return svg_wrap("Chaos Coordinator SVG", content)


def design_16_wildflower():
    content = f"""
  {double_circle(400, 400, 326, 308)}
  {star_burst_ring(400, 400, 291, 16)}
  <text x="400" y="240" text-anchor="middle" font-family="Cormorant, serif" font-size="20" fill="black" letter-spacing="6">SHE IS A</text>
  {diamond_divider(400, 260, 190)}
  <text x="400" y="362" text-anchor="middle" font-family="GreatVibes, cursive" font-size="96" fill="black">Wildflower</text>
  {diamond_divider(400, 384, 190)}
  <text x="400" y="436" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="44" fill="black" letter-spacing="4">UNTAMEABLE</text>
  <text x="400" y="476" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="44" fill="black" letter-spacing="4">BEAUTIFULLY WILD</text>
  <text x="400" y="516" text-anchor="middle" font-family="CormorantItalic, serif" font-size="16" fill="black" letter-spacing="3">growing exactly where she's planted</text>
"""
    return svg_wrap("Wildflower SVG", content)


def design_17_wine_mom_tribe():
    content = f"""
  {diamond_border(38, 54)}
  {corner_flourish(60, 24)}
  <text x="400" y="192" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="6">MEMBER OF THE</text>
  {diamond_divider(400, 212, 260)}
  <text x="400" y="288" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="76" fill="black" letter-spacing="2">MOM TRIBE</text>
  {diamond_divider(400, 308, 260)}
  <text x="400" y="370" text-anchor="middle" font-family="GreatVibes, cursive" font-size="58" fill="black">coffee in hand</text>
  <text x="400" y="420" text-anchor="middle" font-family="GreatVibes, cursive" font-size="58" fill="black">wine at five</text>
  {dot_divider(400, 444, 260, 7)}
  <text x="400" y="492" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="5">NO JUDGMENT · ALL LOVE</text>
  <text x="400" y="526" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="5">SNACKS ALWAYS WELCOME</text>
  {dot_divider(400, 548, 180, 5)}
  <text x="400" y="588" text-anchor="middle" font-family="CormorantItalic, serif" font-size="15" fill="black" letter-spacing="3">· ride or die ·</text>
"""
    return svg_wrap("Mom Tribe SVG", content)


def design_18_best_job():
    content = f"""
  {double_circle(400, 400, 324, 306)}
  {circle_dot_ring(400, 400, 290, 58, 1.5)}
  <text x="400" y="240" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="5">WORLD'S GREATEST</text>
  {diamond_divider(400, 260, 200)}
  <text x="400" y="352" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="82" fill="black" letter-spacing="2">MOM</text>
  <text x="400" y="404" text-anchor="middle" font-family="GreatVibes, cursive" font-size="54" fill="black">no contest</text>
  {diamond_divider(400, 424, 200)}
  <text x="400" y="474" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="4">BEST JOB I EVER HAD</text>
  <text x="400" y="508" text-anchor="middle" font-family="CormorantItalic, serif" font-size="16" fill="black" letter-spacing="3">hardest, most rewarding,</text>
  <text x="400" y="530" text-anchor="middle" font-family="CormorantItalic, serif" font-size="16" fill="black" letter-spacing="3">most beautiful job of all</text>
"""
    return svg_wrap("Best Job SVG", content)


def design_19_raising_arrows():
    content = f"""
  {diamond_border(38, 56)}
  {corner_flourish(62, 24)}
  <text x="400" y="194" text-anchor="middle" font-family="Cormorant, serif" font-size="20" fill="black" letter-spacing="6">LIKE ARROWS</text>
  {diamond_divider(400, 214, 220)}
  <text x="400" y="304" text-anchor="middle" font-family="GreatVibes, cursive" font-size="78" fill="black">Raising</text>
  <text x="400" y="394" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="76" fill="black" letter-spacing="4">ARROWS</text>
  {diamond_divider(400, 416, 220)}
  <text x="400" y="468" text-anchor="middle" font-family="Cormorant, serif" font-size="19" fill="black" letter-spacing="5">POINTING THEM TOWARD</text>
  <text x="400" y="500" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="32" fill="black" letter-spacing="6">PURPOSE</text>
  {dot_divider(400, 520, 200, 5)}
  <text x="400" y="562" text-anchor="middle" font-family="CormorantItalic, serif" font-size="16" fill="black" letter-spacing="3">psalm 127:4</text>
"""
    return svg_wrap("Raising Arrows SVG", content)


def design_20_mama_needs_coffee():
    content = f"""
  {double_circle(400, 400, 322, 304)}
  {star_burst_ring(400, 400, 288, 14)}
  <text x="400" y="240" text-anchor="middle" font-family="GreatVibes, cursive" font-size="42" fill="black">this mama needs</text>
  {diamond_divider(400, 260, 220)}
  <text x="400" y="360" text-anchor="middle" font-family="BebasNeue, sans-serif" font-size="76" fill="black" letter-spacing="2">COFFEE</text>
  <text x="400" y="418" text-anchor="middle" font-family="GreatVibes, cursive" font-size="58" fill="black">and a nap</text>
  {diamond_divider(400, 438, 220)}
  <text x="400" y="490" text-anchor="middle" font-family="Cormorant, serif" font-size="20" fill="black" letter-spacing="4">IN THAT ORDER</text>
  <text x="400" y="522" text-anchor="middle" font-family="CormorantItalic, serif" font-size="15" fill="black" letter-spacing="3">daily mom life goals</text>
"""
    return svg_wrap("Mama Needs Coffee SVG", content)


# ─── Generate all ────────────────────────────────────────────────────────────────

designs = [
    ("mom_01_blessed_mama.svg",     design_01_blessed_mama()),
    ("mom_02_coffee_chaos.svg",     design_02_coffee_chaos()),
    ("mom_03_messy_bun.svg",        design_03_messy_bun()),
    ("mom_04_boy_mom.svg",          design_04_boy_mom()),
    ("mom_05_girl_mom.svg",         design_05_girl_mom()),
    ("mom_06_mama_bear.svg",        design_06_mama_bear()),
    ("mom_07_soccer_mom.svg",       design_07_soccer_mom()),
    ("mom_08_minivan_mama.svg",     design_08_minivan_mama()),
    ("mom_09_tired_blessed.svg",    design_09_tired_but_blessed()),
    ("mom_10_wine_time.svg",        design_10_wine_time()),
    ("mom_11_fur_mama.svg",         design_11_fur_mama()),
    ("mom_12_hot_mess.svg",         design_12_hot_mess()),
    ("mom_13_nap_time.svg",         design_13_nap_time()),
    ("mom_14_motherhood.svg",       design_14_motherhood()),
    ("mom_15_chaos_coordinator.svg",design_15_chaos_coordinator()),
    ("mom_16_wildflower.svg",       design_16_wildflower()),
    ("mom_17_mom_tribe.svg",        design_17_wine_mom_tribe()),
    ("mom_18_best_job.svg",         design_18_best_job()),
    ("mom_19_raising_arrows.svg",   design_19_raising_arrows()),
    ("mom_20_mama_needs_coffee.svg",design_20_mama_needs_coffee()),
]

os.makedirs(OUT_DIR, exist_ok=True)
for fname, svg in designs:
    path = os.path.join(OUT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"✓ {fname}")

print(f"\n✅ All {len(designs)} designs written to {OUT_DIR}/")
