#!/usr/bin/env python3
"""
Retro Good Vibes SVG Pack — REDESIGN
White backgrounds. Big colorful script. Text is the art.
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


def wrap(title, body):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">\n'
            f'  <title>{title}</title>\n'
            f'  <rect width="800" height="800" fill="#FFFFFF"/>\n'
            f'{FONT_DEFS}\n{body}\n</svg>')


# ─── Helpers ──────────────────────────────────────────────────────────────────

def txt(x, y, t, font, size, fill, anchor="middle", ls=0):
    ls_attr = f' letter-spacing="{ls}"' if ls else ""
    return (f'  <text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'font-family="{font}, sans-serif" font-size="{size}" fill="{fill}"{ls_attr}>'
            f'{t}</text>')


def dot(cx, cy, r, fill):
    return f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}"/>'


def dot_row(cx, y, n, gap, r, fill):
    total = (n - 1) * gap
    return "\n".join(dot(cx - total / 2 + i * gap, y, r, fill) for i in range(n))


def hline(cx, y, w, fill, h=5):
    return f'  <rect x="{cx - w//2}" y="{y - h//2}" width="{w}" height="{h}" fill="{fill}" rx="{h//2}"/>'


def diamond_div(cx, y, w, c1, c2):
    """  ——— ◆ ——— in two colors"""
    d = 7
    return "\n".join([
        hline(cx - d - 8 - w // 2, y, w // 2 - d - 8, c1, 4),
        f'  <polygon points="{cx},{y - d} {cx + d},{y} {cx},{y + d} {cx - d},{y}" fill="{c2}"/>',
        hline(cx + d + 8 + w // 4, y, w // 2 - d - 8, c1, 4),
    ])


def star4(cx, cy, r, fill):
    """4-point star."""
    ri = r * 0.35
    pts = []
    for i in range(8):
        rad = r if i % 2 == 0 else ri
        a = math.radians(i * 45 - 90)
        pts.append(f"{cx + rad*math.cos(a):.1f},{cy + rad*math.sin(a):.1f}")
    return f'  <polygon points="{" ".join(pts)}" fill="{fill}"/>'


def corner_stars(r, fills):
    """4-point stars in each corner."""
    corners = [(80, 80), (720, 80), (80, 720), (720, 720)]
    return "\n".join(star4(cx, cy, r, fills[i % len(fills)])
                     for i, (cx, cy) in enumerate(corners))


def dot_ring(cx, cy, r, n, rd, fill):
    out = []
    for i in range(n):
        a = math.radians(360 * i / n)
        out.append(dot(cx + r * math.cos(a), cy + r * math.sin(a), rd, fill))
    return "\n".join(out)


# ─── 20 Designs ──────────────────────────────────────────────────────────────

def d01_good_vibes():
    return wrap("Good Vibes Only", "\n".join([
        corner_stars(18, ["#E8455A", "#7B35B0"]),
        dot_row(400, 220, 7, 28, 6, "#E8455A"),
        txt(400, 356, "Good Vibes", "GreatVibes", 108, "#E8455A"),
        txt(400, 446, "ONLY", "BebasNeue", 80, "#7B35B0", ls=10),
        dot_row(400, 490, 7, 28, 6, "#7B35B0"),
        txt(400, 548, "always &amp; forever", "CormorantItalic", 20, "#AAAAAA", ls=3),
    ]))


def d02_stay_groovy():
    return wrap("Stay Groovy", "\n".join([
        corner_stars(16, ["#E8A020", "#1B9E8A"]),
        txt(400, 248, "S T A Y", "Cormorant", 28, "#1B9E8A", ls=14),
        hline(400, 270, 160, "#1B9E8A", 3),
        txt(400, 408, "Groovy", "GreatVibes", 118, "#E8A020"),
        hline(400, 436, 280, "#E8A020", 5),
        txt(400, 500, "B A B Y", "Cormorant", 26, "#1B9E8A", ls=14),
        dot_row(400, 548, 5, 32, 7, "#E8A020"),
    ]))


def d03_spread_love():
    return wrap("Spread Love", "\n".join([
        corner_stars(16, ["#E84B8A", "#F07A1A"]),
        txt(400, 248, "S P R E A D", "Cormorant", 24, "#F07A1A", ls=12),
        dot_row(400, 275, 5, 24, 5, "#F07A1A"),
        txt(400, 416, "Love", "GreatVibes", 120, "#E84B8A"),
        dot_row(400, 448, 5, 24, 5, "#E84B8A"),
        txt(400, 510, "everywhere you go", "CormorantItalic", 22, "#AAAAAA", ls=3),
        star4(400, 580, 16, "#E84B8A"),
    ]))


def d04_be_weird():
    return wrap("Be Weird Be Wonderful", "\n".join([
        corner_stars(16, ["#1B9E8A", "#7B35B0"]),
        txt(400, 256, "B E", "Cormorant", 26, "#999999", ls=16),
        txt(400, 350, "WEIRD", "BebasNeue", 102, "#1B9E8A", ls=6),
        diamond_div(400, 384, 280, "#7B35B0", "#1B9E8A"),
        txt(400, 434, "be", "GreatVibes", 60, "#7B35B0"),
        txt(400, 528, "Wonderful", "GreatVibes", 100, "#7B35B0"),
        dot_row(400, 572, 5, 28, 6, "#1B9E8A"),
    ]))


def d05_choose_happy():
    return wrap("Choose Happy", "\n".join([
        corner_stars(16, ["#E8A020", "#E8455A"]),
        txt(400, 252, "C H O O S E", "Cormorant", 24, "#BBBBBB", ls=12),
        dot_row(400, 278, 5, 26, 5, "#E8A020"),
        txt(400, 420, "Happy", "GreatVibes", 120, "#E8A020"),
        hline(400, 452, 320, "#E8455A", 5),
        txt(400, 514, "every single day", "CormorantItalic", 22, "#E8455A", ls=3),
        dot_row(400, 562, 7, 28, 6, "#E8A020"),
    ]))


def d06_wild_free():
    return wrap("Wild and Free", "\n".join([
        corner_stars(16, ["#F07A1A", "#1B9E8A"]),
        txt(400, 290, "WILD", "BebasNeue", 110, "#F07A1A", ls=6),
        txt(400, 390, "&amp;", "GreatVibes", 90, "#E8455A"),
        txt(400, 498, "FREE", "BebasNeue", 110, "#1B9E8A", ls=6),
        dot_row(400, 556, 5, 26, 6, "#E8455A"),
        txt(400, 610, "untameable soul", "CormorantItalic", 20, "#AAAAAA", ls=3),
    ]))


def d07_good_things():
    return wrap("Good Things Coming", "\n".join([
        corner_stars(16, ["#0D1B3E", "#E8A020"]),
        txt(400, 288, "good things", "GreatVibes", 88, "#0D1B3E"),
        diamond_div(400, 316, 260, "#E8A020", "#0D1B3E"),
        txt(400, 408, "COMING", "BebasNeue", 96, "#E8A020", ls=6),
        hline(400, 440, 280, "#0D1B3E", 4),
        txt(400, 502, "your way", "GreatVibes", 64, "#0D1B3E"),
        dot_row(400, 556, 5, 26, 6, "#E8A020"),
    ]))


def d08_flower_power():
    return wrap("Flower Power", "\n".join([
        corner_stars(16, ["#E84B8A", "#1B9E8A"]),
        txt(400, 310, "Flower", "GreatVibes", 110, "#E84B8A"),
        hline(400, 342, 300, "#E84B8A", 5),
        txt(400, 440, "POWER", "BebasNeue", 100, "#1B9E8A", ls=6),
        dot_row(400, 488, 9, 28, 6, "#E84B8A"),
        txt(400, 548, "peace · love · plants", "CormorantItalic", 20, "#AAAAAA", ls=3),
    ]))


def d09_peace_love():
    return wrap("Peace Love Joy", "\n".join([
        corner_stars(14, ["#E8455A", "#7B35B0", "#1B9E8A", "#E8A020"]),
        hline(400, 204, 200, "#E8455A", 4),
        txt(400, 308, "Peace", "GreatVibes", 100, "#E8455A"),
        txt(400, 420, "Love", "GreatVibes", 100, "#7B35B0"),
        txt(400, 530, "Joy", "GreatVibes", 100, "#1B9E8A"),
        hline(400, 566, 200, "#1B9E8A", 4),
    ]))


def d10_radiate():
    return wrap("Radiate Positivity", "\n".join([
        corner_stars(16, ["#E8455A", "#7B35B0"]),
        txt(400, 286, "RADIATE", "BebasNeue", 100, "#E8455A", ls=6),
        diamond_div(400, 318, 260, "#7B35B0", "#E8455A"),
        txt(400, 440, "positivity", "GreatVibes", 104, "#7B35B0"),
        dot_row(400, 478, 7, 26, 6, "#E8455A"),
        txt(400, 538, "A L W A Y S", "Cormorant", 22, "#BBBBBB", ls=12),
    ]))


def d11_soul_fire():
    return wrap("Soul on Fire", "\n".join([
        corner_stars(16, ["#C43020", "#E8A020"]),
        dot_row(400, 216, 5, 26, 6, "#E8A020"),
        txt(400, 352, "Soul", "GreatVibes", 116, "#C43020"),
        hline(400, 382, 240, "#E8A020", 5),
        txt(400, 454, "ON FIRE", "BebasNeue", 88, "#E8A020", ls=6),
        hline(400, 486, 240, "#C43020", 4),
        txt(400, 548, "burning bright", "CormorantItalic", 22, "#AAAAAA", ls=3),
    ]))


def d12_dream_chaser():
    return wrap("Dream Chaser", "\n".join([
        corner_stars(16, ["#7B35B0", "#0D1B3E"]),
        txt(400, 256, "D R E A M", "Cormorant", 26, "#BBBBBB", ls=12),
        txt(400, 390, "Dream", "GreatVibes", 110, "#7B35B0"),
        hline(400, 422, 300, "#7B35B0", 5),
        txt(400, 510, "CHASER", "BebasNeue", 96, "#0D1B3E", ls=6),
        dot_row(400, 558, 5, 28, 7, "#7B35B0"),
    ]))


def d13_wander():
    return wrap("Wander Often Wonder Always", "\n".join([
        corner_stars(14, ["#F07A1A", "#1B9E8A"]),
        txt(400, 262, "WANDER", "BebasNeue", 80, "#F07A1A", ls=5),
        hline(400, 288, 240, "#F07A1A", 4),
        txt(400, 376, "often", "GreatVibes", 88, "#F07A1A"),
        dot_row(400, 408, 5, 24, 5, "#1B9E8A"),
        txt(400, 494, "wonder", "GreatVibes", 88, "#1B9E8A"),
        hline(400, 526, 240, "#1B9E8A", 4),
        txt(400, 564, "ALWAYS", "BebasNeue", 80, "#1B9E8A", ls=5),
    ]))


def d14_life_colorful():
    # Each word a different color
    COLORS = ["#D93030", "#E87B2A", "#2B8A3E", "#1E6FCC", "#7B35B0"]
    return wrap("Life Is Colorful", "\n".join([
        corner_stars(14, COLORS),
        txt(400, 264, "life", "GreatVibes", 100, COLORS[0]),
        txt(400, 360, "is", "GreatVibes", 100, COLORS[2]),
        txt(400, 456, "colorful", "GreatVibes", 100, COLORS[4]),
        dot_row(400, 506, 5, 28, 6, COLORS[1]),
        txt(400, 560, "embrace every shade", "CormorantItalic", 20, "#BBBBBB", ls=3),
    ]))


def d15_keep_growing():
    return wrap("Keep Growing", "\n".join([
        corner_stars(16, ["#2B6040", "#C4634F"]),
        txt(400, 284, "KEEP", "BebasNeue", 110, "#2B6040", ls=8),
        diamond_div(400, 316, 260, "#C4634F", "#2B6040"),
        txt(400, 440, "Growing", "GreatVibes", 110, "#C4634F"),
        dot_row(400, 478, 7, 28, 6, "#2B6040"),
        txt(400, 538, "bloom where you're planted", "CormorantItalic", 18, "#AAAAAA", ls=2),
    ]))


def d16_magic_happens():
    return wrap("Magic Happens Here", "\n".join([
        corner_stars(18, ["#7B35B0", "#E8A020"]),
        star4(400, 196, 22, "#E8A020"),
        txt(400, 338, "Magic", "GreatVibes", 112, "#7B35B0"),
        hline(400, 370, 280, "#E8A020", 5),
        txt(400, 460, "HAPPENS HERE", "BebasNeue", 66, "#E8A020", ls=4),
        dot_row(400, 506, 7, 28, 6, "#7B35B0"),
        txt(400, 562, "believe it", "GreatVibes", 48, "#7B35B0"),
    ]))


def d17_happy_chaos():
    return wrap("Happy Chaos", "\n".join([
        corner_stars(16, ["#E84B8A", "#F07A1A"]),
        txt(400, 310, "Happy", "GreatVibes", 112, "#E84B8A"),
        hline(400, 342, 300, "#F07A1A", 5),
        txt(400, 440, "CHAOS", "BebasNeue", 100, "#F07A1A", ls=8),
        dot_row(400, 488, 9, 28, 6, "#E84B8A"),
        txt(400, 548, "it's my superpower", "CormorantItalic", 21, "#AAAAAA", ls=3),
    ]))


def d18_sun_child():
    return wrap("Sun Child", "\n".join([
        corner_stars(16, ["#E8A020", "#F07A1A"]),
        dot_row(400, 216, 5, 30, 8, "#E8A020"),
        txt(400, 376, "Sun", "GreatVibes", 120, "#E8A020"),
        hline(400, 408, 260, "#F07A1A", 5),
        txt(400, 500, "CHILD", "BebasNeue", 100, "#F07A1A", ls=8),
        dot_row(400, 552, 5, 30, 8, "#E8A020"),
        txt(400, 606, "golden &amp; free", "CormorantItalic", 20, "#BBBBBB", ls=3),
    ]))


def d19_bloom():
    return wrap("Bloom", "\n".join([
        corner_stars(16, ["#E84B8A", "#E8A020"]),
        dot_row(400, 190, 9, 32, 7, "#E8A020"),
        txt(400, 430, "Bloom", "GreatVibes", 150, "#E84B8A"),
        dot_row(400, 480, 9, 32, 7, "#E84B8A"),
        txt(400, 556, "be brave · grow wild", "CormorantItalic", 22, "#AAAAAA", ls=3),
    ]))


def d20_rainbow():
    # Each word a different rainbow color
    COLORS = ["#D93030", "#E87B2A", "#2B8A3E", "#1E6FCC", "#7B35B0", "#E84B8A"]
    return wrap("You Are a Rainbow", "\n".join([
        corner_stars(14, COLORS[:4]),
        txt(400, 234, "you", "GreatVibes", 88, COLORS[0]),
        txt(400, 330, "are", "GreatVibes", 88, COLORS[2]),
        txt(400, 426, "a", "GreatVibes", 88, COLORS[3]),
        txt(400, 524, "rainbow", "GreatVibes", 88, COLORS[4]),
        dot_row(400, 570, 7, 26, 6, COLORS[1]),
        txt(400, 624, "brilliant · bold · colorful", "CormorantItalic", 18, "#BBBBBB", ls=3),
    ]))


# ─── Generate ─────────────────────────────────────────────────────────────────

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
    ("groovy_20_rainbow.svg",           d20_rainbow()),
]

os.makedirs(OUT_DIR, exist_ok=True)
for fname, svg in DESIGNS:
    with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"✓ {fname}")

print(f"\n✅ {len(DESIGNS)} designs written to {OUT_DIR}/")
