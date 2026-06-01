#!/usr/bin/env python3
"""
Generate "Retro Moms & Sports Bundle" — 20 SVG designs.

Research-backed design principles:
- Sports Mom Identity designs: arch text + sport icon + profession (largest niche)
- Professional Identity: Bold word + script phrase ("Teacher Fuel", "Nurse Life")
- "In My ___ Era" retro wavy font designs
- 3-layer text hierarchy: LARGE BOLD + flowing script + small caps
- Arch/badge layouts for shirts & tumblers
- Clean negative space — less is more
- No gradients (cutting machine incompatible)
- White backgrounds, strong silhouettes
"""
import os, sys, math
from pathlib import Path

OUT_DIR = Path("data/retro_moms_pack/SVG")
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 800, 800


# ─────────────── SVG primitives ───────────────

def wrap(name, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}">'
        f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>'
        f'{body}'
        f'</svg>'
    )


def txt(x, y, text, font, size, fill, anchor="middle", ls=0, weight="normal"):
    style = f"font-family:'{font}',sans-serif;font-size:{size}px;fill:{fill};"
    if weight != "normal":
        style += f"font-weight:{weight};"
    if ls:
        style += f"letter-spacing:{ls}px;"
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'style="{style}">{text}</text>')


def arc_text(cx, cy, r, text, font, size, fill, start_deg=200, end_deg=340, upward=True):
    """Render text along an arc path."""
    # Convert to radians for path
    start_rad = math.radians(start_deg)
    end_rad = math.radians(end_deg)
    # Large arc flag
    large = 1 if (end_deg - start_deg) > 180 else 0
    sx = cx + r * math.cos(start_rad)
    sy = cy + r * math.sin(start_rad)
    ex = cx + r * math.cos(end_rad)
    ey = cy + r * math.sin(end_rad)
    sweep = 1 if upward else 0
    path_d = f"M {sx:.1f},{sy:.1f} A {r},{r} 0 {large},{sweep} {ex:.1f},{ey:.1f}"
    pid = f"arc_{abs(hash(text)) % 99999}"
    return (
        f'<defs><path id="{pid}" d="{path_d}"/></defs>'
        f'<text style="font-family:\'{font}\',sans-serif;font-size:{size}px;'
        f'fill:{fill};font-weight:bold;letter-spacing:4px;">'
        f'<textPath href="#{pid}" startOffset="50%" text-anchor="middle">{text}</textPath>'
        f'</text>'
    )


def circle_arc(cx, cy, r, fill="none", stroke="#333", sw=2.5):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')


def hline(y, x1=120, x2=680, color="#333", sw=1.5):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="{sw}"/>'


def dot_row(cx, cy, n, spacing, r, fill):
    dots = ""
    start_x = cx - ((n - 1) * spacing) / 2
    for i in range(n):
        x = start_x + i * spacing
        dots += f'<circle cx="{x:.1f}" cy="{cy}" r="{r}" fill="{fill}"/>'
    return dots


def star(cx, cy, r, fill, n=5, inner_ratio=0.4):
    pts = []
    for i in range(n * 2):
        angle = math.radians(i * 180 / n - 90)
        rad = r if i % 2 == 0 else r * inner_ratio
        pts.append(f"{cx + rad * math.cos(angle):.1f},{cy + rad * math.sin(angle):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}"/>'


def football(cx, cy, w=160, h=105, fill="#7B3F00"):
    """Detailed American football — pointed oval with stripe and laces."""
    rx, ry = w / 2, h / 2
    # Pointed oval using bezier curves for realistic football shape
    shape = (f'<path d="M{cx - rx:.1f},{cy:.1f} '
             f'Q{cx - rx * 0.35:.1f},{cy - ry * 1.18:.1f} {cx:.1f},{cy - ry:.1f} '
             f'Q{cx + rx * 0.35:.1f},{cy - ry * 1.18:.1f} {cx + rx:.1f},{cy:.1f} '
             f'Q{cx + rx * 0.35:.1f},{cy + ry * 1.18:.1f} {cx:.1f},{cy + ry:.1f} '
             f'Q{cx - rx * 0.35:.1f},{cy + ry * 1.18:.1f} {cx - rx:.1f},{cy:.1f} Z" '
             f'fill="{fill}"/>')
    # White horizontal seam bands (two curved arcs, top and bottom half)
    shape += (f'<path d="M{cx - rx * 0.8:.1f},{cy:.1f} '
              f'Q{cx:.1f},{cy - ry * 0.42:.1f} {cx + rx * 0.8:.1f},{cy:.1f}" '
              f'fill="none" stroke="#F5F0E8" stroke-width="6"/>')
    shape += (f'<path d="M{cx - rx * 0.8:.1f},{cy:.1f} '
              f'Q{cx:.1f},{cy + ry * 0.42:.1f} {cx + rx * 0.8:.1f},{cy:.1f}" '
              f'fill="none" stroke="#F5F0E8" stroke-width="6"/>')
    # Center lace stitching
    lace_h = ry * 0.62
    shape += (f'<line x1="{cx:.1f}" y1="{cy - lace_h:.1f}" '
              f'x2="{cx:.1f}" y2="{cy + lace_h:.1f}" '
              f'stroke="#F5F0E8" stroke-width="3"/>')
    for dy in [-lace_h * 0.5, 0, lace_h * 0.5]:
        shape += (f'<line x1="{cx - 16:.1f}" y1="{cy + dy:.1f}" '
                  f'x2="{cx + 16:.1f}" y2="{cy + dy:.1f}" '
                  f'stroke="#F5F0E8" stroke-width="4" stroke-linecap="round"/>')
    return shape


def baseball(cx, cy, r=75, fill="#FAFAFA", stitch="#CC2200"):
    """Baseball with clear stitching curves."""
    shape = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="#E8E8E8" stroke-width="2"/>'
    # Left curved stitches (double lines for realism)
    for sw, col in [(5, stitch), (2, "#FFFFFF")]:
        shape += (f'<path d="M{cx - r + 12},{cy - r * 0.28:.1f} '
                  f'C{cx - r * 0.45:.1f},{cy - r * 0.1:.1f} '
                  f'{cx - r * 0.45:.1f},{cy + r * 0.1:.1f} '
                  f'{cx - r + 12},{cy + r * 0.28:.1f}" '
                  f'fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round"/>')
    # Right curved stitches
    for sw, col in [(5, stitch), (2, "#FFFFFF")]:
        shape += (f'<path d="M{cx + r - 12},{cy - r * 0.28:.1f} '
                  f'C{cx + r * 0.45:.1f},{cy - r * 0.1:.1f} '
                  f'{cx + r * 0.45:.1f},{cy + r * 0.1:.1f} '
                  f'{cx + r - 12},{cy + r * 0.28:.1f}" '
                  f'fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round"/>')
    # Small stitch tick marks
    for side, base_x in [(-1, cx - r + 22), (1, cx + r - 22)]:
        for dy in [-r * 0.18, 0, r * 0.18]:
            shape += (f'<line x1="{base_x:.1f}" y1="{cy + dy - 6:.1f}" '
                      f'x2="{base_x + side * 8:.1f}" y2="{cy + dy + 6:.1f}" '
                      f'stroke="{stitch}" stroke-width="2.5" stroke-linecap="round"/>')
    return shape


def coffee_cup(cx, cy, w=70, h=75, fill="#4A2C2A"):
    # Cup body (trapezoid)
    top_w, bot_w = w, w * 0.75
    tx1, tx2 = cx - top_w // 2, cx + top_w // 2
    bx1, bx2 = cx - bot_w // 2, cx + bot_w // 2
    pts = f"{tx1},{cy - h // 2} {tx2},{cy - h // 2} {bx2},{cy + h // 2} {bx1},{cy + h // 2}"
    cup = f'<polygon points="{pts}" fill="{fill}"/>'
    # Handle
    cup += (f'<path d="M{cx + top_w // 2},{cy - 10} Q{cx + top_w // 2 + 30},{cy} {cx + top_w // 2},{cy + 15}" '
            f'fill="none" stroke="{fill}" stroke-width="8" stroke-linecap="round"/>')
    # Steam
    for i, ox in enumerate([-12, 0, 12]):
        cup += (f'<path d="M{cx + ox},{cy - h // 2 - 8} Q{cx + ox + 6},{cy - h // 2 - 18} {cx + ox},{cy - h // 2 - 28}" '
                f'fill="none" stroke="#999" stroke-width="2" stroke-linecap="round"/>')
    return cup


def heart(cx, cy, size=40, fill="#E84040"):
    s = size / 40
    return (f'<path d="M{cx},{cy + 12 * s} '
            f'C{cx},{cy + 6 * s} {cx - 20 * s},{cy - 15 * s} {cx - 20 * s},{cy - 5 * s} '
            f'A{10 * s},{10 * s} 0 0,1 {cx},{cy + 3 * s} '
            f'A{10 * s},{10 * s} 0 0,1 {cx + 20 * s},{cy - 5 * s} '
            f'C{cx + 20 * s},{cy - 15 * s} {cx},{cy + 6 * s} {cx},{cy + 12 * s}" '
            f'fill="{fill}"/>')


def wavy_text_group(x, y, text, font, size, fill, wave_amp=6, segments=None):
    """Approximate wavy text by rendering chars individually with sine offset."""
    if segments is None:
        segments = list(text)
    char_w = size * 0.58
    total_w = len(segments) * char_w
    start_x = x - total_w / 2
    parts = []
    for i, ch in enumerate(segments):
        cx = start_x + i * char_w + char_w / 2
        cy_off = wave_amp * math.sin(i * math.pi * 2 / max(len(segments), 4))
        parts.append(
            f'<text x="{cx:.1f}" y="{y + cy_off:.1f}" text-anchor="middle" '
            f'style="font-family:\'{font}\';font-size:{size}px;fill:{fill};font-weight:bold;">'
            f'{ch}</text>'
        )
    return "".join(parts)


def badge_circle(cx, cy, r_outer, r_inner, stroke, sw=3):
    """Double ring badge border."""
    c1 = circle_arc(cx, cy, r_outer, stroke=stroke, sw=sw)
    c2 = circle_arc(cx, cy, r_inner, stroke=stroke, sw=sw - 0.5)
    return c1 + c2


def small_stars_row(cx, cy, n, spacing, size, fill):
    s = ""
    start_x = cx - (n - 1) * spacing / 2
    for i in range(n):
        s += star(start_x + i * spacing, cy, size, fill)
    return s


# ─────────────── 20 designs ───────────────

def d01_football_mom():
    """FOOTBALL MOM — badge layout. Strict zone separation:
       Top arc (text) | Divider | Graphic (football) | Divider | Bottom text | Bottom arc
    """
    body = badge_circle(400, 400, 310, 278, "#2D5A27", sw=3)

    # ZONE 1 — top arch text (sits in ring between r=278 and r=310, top half)
    body += arc_text(400, 400, 294, "FOOTBALL MOM", "BebasNeue", 40, "#2D5A27",
                     start_deg=212, end_deg=328, upward=False)

    # Thin divider line separating text zone from graphic zone
    body += hline(195, 200, 600, "#2D5A27", 1.5)

    # ZONE 2 — football graphic, centered vertically in upper half of badge interior
    # Badge interior spans y=90 to y=710 (r=310 from center y=400)
    # Graphic zone: y=195 to y=460 (upper interior, well below arch text)
    body += football(400, 330, w=200, h=132)

    # Thin divider below football
    body += hline(460, 200, 600, "#2D5A27", 1.5)

    # ZONE 3 — bottom text, clearly below football and divider
    body += small_stars_row(400, 505, 5, 38, 10, "#C9952A")
    body += txt(400, 558, "EST. 2016", "BebasNeue", 34, "#2D5A27", ls=6)

    # ZONE 4 — bottom arch text
    body += arc_text(400, 400, 294, "ALWAYS CHEERING", "BebasNeue", 33, "#C9952A",
                     start_deg=32, end_deg=148, upward=True)
    return wrap("football_mom", body)


def d02_baseball_mama():
    """BASEBALL MAMA — navy/red badge. Clear 4-zone layout."""
    body = badge_circle(400, 400, 310, 278, "#1B2A6B", sw=3)

    # ZONE 1 — top arch text
    body += arc_text(400, 400, 294, "BASEBALL MAMA", "BebasNeue", 39, "#1B2A6B",
                     start_deg=215, end_deg=325, upward=False)

    # Thin divider below arch text zone
    body += hline(195, 200, 600, "#1B2A6B", 1.5)

    # ZONE 2 — baseball graphic, upper interior
    # Baseball centered at y=340, r=75 → top edge y=265, bottom edge y=415
    body += baseball(400, 340, r=75)

    # Divider below graphic zone (below baseball bottom + 50px clearance)
    body += hline(475, 200, 600, "#CC2200", 2)

    # ZONE 3 — bottom text zone, clearly below baseball
    body += txt(400, 528, "BATTER UP", "BebasNeue", 46, "#1B2A6B", ls=6)
    body += dot_row(400, 570, 5, 36, 5, "#CC2200")

    # ZONE 4 — bottom arch text
    body += arc_text(400, 400, 294, "DUGOUT CREW SINCE 2019", "BebasNeue", 27, "#CC2200",
                     start_deg=35, end_deg=145, upward=True)
    return wrap("baseball_mama", body)


def d03_cheer_mom():
    """CHEER MOM — hot pink, retro pom-pom stars design."""
    body = ""
    # Burst background stars
    for i in range(8):
        angle = i * 45
        r = 270
        bx = 400 + r * math.cos(math.radians(angle))
        by = 400 + r * math.sin(math.radians(angle))
        body += star(bx, by, 18, "#FFD1E8")
    body += txt(400, 230, "CHEER", "BebasNeue", 130, "#CC1F6A", ls=8)
    body += hline(265, 130, 670, "#CC1F6A", 2.5)
    body += txt(400, 380, "Mom", "GreatVibes", 115, "#FF6BAD")
    body += hline(420, 130, 670, "#CC1F6A", 2.5)
    body += dot_row(400, 450, 7, 36, 5, "#CC1F6A")
    body += txt(400, 510, "FOREVER LOUD", "BebasNeue", 44, "#CC1F6A", ls=6)
    body += txt(400, 565, "FOREVER PROUD", "BebasNeue", 36, "#FF6BAD", ls=5)
    return wrap("cheer_mom", body)


def d04_soccer_mama():
    """SOCCER MAMA — teal/lime badge. Clean 4-zone layout."""
    body = badge_circle(400, 400, 310, 278, "#0A7A5E", sw=3)

    # ZONE 1 — top arch text
    body += arc_text(400, 400, 294, "SOCCER MAMA", "BebasNeue", 42, "#0A7A5E",
                     start_deg=216, end_deg=324, upward=False)
    body += hline(195, 200, 600, "#0A7A5E", 1.5)

    # ZONE 2 — soccer ball graphic (classic black/white pentagon pattern)
    bx, by, br = 400, 335, 82
    # White base circle
    body += f'<circle cx="{bx}" cy="{by}" r="{br}" fill="white" stroke="#222" stroke-width="2.5"/>'
    # Center black pentagon (hexagon approx as circle)
    body += f'<circle cx="{bx}" cy="{by}" r="26" fill="#1A1A1A"/>'
    # 5 surrounding black patches (pentagons approximated as circles)
    for i in range(5):
        ang = math.radians(i * 72 - 90)
        px = bx + 47 * math.cos(ang)
        py = by + 47 * math.sin(ang)
        body += f'<circle cx="{px:.1f}" cy="{py:.1f}" r="19" fill="#1A1A1A"/>'
    # Outer ring seam
    body += f'<circle cx="{bx}" cy="{by}" r="{br}" fill="none" stroke="#CCC" stroke-width="1"/>'

    body += hline(460, 200, 600, "#A0D82B", 2)

    # ZONE 3 — bottom text
    body += txt(400, 518, "GAME DAY READY", "BebasNeue", 36, "#0A7A5E", ls=5)
    body += dot_row(400, 562, 5, 36, 5, "#A0D82B")

    # ZONE 4 — bottom arch text
    body += arc_text(400, 400, 294, "WIN OR LOSE WE CHEER", "BebasNeue", 28, "#A0D82B",
                     start_deg=35, end_deg=145, upward=True)
    return wrap("soccer_mama", body)


def d05_teacher_fuel():
    """TEACHER FUEL — coffee cup identity design, clean 3-layer layout."""
    body = ""
    body += txt(400, 175, "TEACHER", "BebasNeue", 102, "#1B3A6B", ls=8)
    body += hline(195, 160, 640, "#1B3A6B", 2.5)
    body += coffee_cup(400, 390, w=130, h=130, fill="#4A2C2A")
    body += hline(480, 200, 600, "#1B3A6B", 1.5)
    body += txt(400, 540, "fuel", "GreatVibes", 100, "#C9952A")
    body += txt(400, 610, "NEEDS COFFEE TO FUNCTION", "BebasNeue", 28, "#1B3A6B", ls=4)
    body += dot_row(400, 660, 5, 40, 5, "#C9952A")
    return wrap("teacher_fuel", body)


def d06_nurse_life():
    """NURSE LIFE — bold red + white, cross icon, 3-layer layout."""
    body = ""
    # Background cross shape (subtle)
    body += f'<rect x="360" y="200" width="80" height="230" fill="#FFE8E8" rx="8"/>'
    body += f'<rect x="270" y="285" width="260" height="80" fill="#FFE8E8" rx="8"/>'
    body += txt(400, 190, "NURSE", "BebasNeue", 118, "#CC1515", ls=8)
    # Cross icon
    body += f'<rect x="368" y="230" width="64" height="185" fill="#CC1515" rx="6"/>'
    body += f'<rect x="280" y="290" width="240" height="65" fill="#CC1515" rx="6"/>'
    body += txt(400, 510, "life", "GreatVibes", 110, "#CC1515")
    body += hline(548, 180, 620, "#333", 1.5)
    body += txt(400, 590, "SAVING LIVES &amp; SIPPING COFFEE", "BebasNeue", 24, "#333", ls=3)
    return wrap("nurse_life", body)


def d07_mama_mode():
    """MAMA MODE — wavy retro era-style layout."""
    body = ""
    # Retro concentric arcs as decoration
    for r in [330, 310]:
        body += circle_arc(400, 750, r, stroke="#F5A623", sw=1.5)
    body += txt(400, 195, "MAMA", "BebasNeue", 145, "#1A1A2A", ls=6)
    body += hline(220, 100, 700, "#F5A623", 3)
    body += txt(400, 370, "mode", "GreatVibes", 145, "#F5A623")
    body += hline(405, 100, 700, "#F5A623", 3)
    body += txt(400, 480, "ACTIVATED", "BebasNeue", 72, "#1A1A2A", ls=8)
    body += txt(400, 555, "24/7 — NO DAYS OFF", "BebasNeue", 32, "#777", ls=5)
    body += dot_row(400, 620, 7, 38, 5, "#F5A623")
    return wrap("mama_mode", body)


def d08_in_my_mama_era():
    """IN MY MAMA ERA — retro wavy design, the #1 trending phrase format."""
    body = ""
    # Wavy decorative lines top
    body += f'<path d="M 80,190 Q 200,170 320,190 Q 440,210 560,190 Q 680,170 720,190" fill="none" stroke="#E84080" stroke-width="3"/>'
    body += f'<path d="M 80,200 Q 200,180 320,200 Q 440,220 560,200 Q 680,180 720,200" fill="none" stroke="#E84080" stroke-width="1.5"/>'
    body += txt(400, 290, "IN MY", "BebasNeue", 72, "#333", ls=12)
    body += txt(400, 430, "Mama", "GreatVibes", 155, "#E84080")
    body += txt(400, 500, "ERA", "BebasNeue", 90, "#333", ls=18)
    # Wavy lines bottom
    body += f'<path d="M 80,570 Q 200,550 320,570 Q 440,590 560,570 Q 680,550 720,570" fill="none" stroke="#E84080" stroke-width="3"/>'
    body += f'<path d="M 80,580 Q 200,560 320,580 Q 440,600 560,580 Q 680,560 720,580" fill="none" stroke="#E84080" stroke-width="1.5"/>'
    body += txt(400, 650, "THRIVING IN CHAOS SINCE DAY ONE", "BebasNeue", 22, "#777", ls=3)
    return wrap("in_my_mama_era", body)


def d09_in_my_teacher_era():
    """IN MY TEACHER ERA — matching retro wavy format."""
    body = ""
    body += f'<path d="M 80,190 Q 200,170 320,190 Q 440,210 560,190 Q 680,170 720,190" fill="none" stroke="#2563EB" stroke-width="3"/>'
    body += f'<path d="M 80,200 Q 200,180 320,200 Q 440,220 560,200 Q 680,180 720,200" fill="none" stroke="#2563EB" stroke-width="1.5"/>'
    body += txt(400, 290, "IN MY", "BebasNeue", 72, "#333", ls=12)
    body += txt(400, 435, "Teacher", "GreatVibes", 140, "#2563EB")
    body += txt(400, 503, "ERA", "BebasNeue", 90, "#333", ls=18)
    body += f'<path d="M 80,570 Q 200,550 320,570 Q 440,590 560,570 Q 680,550 720,570" fill="none" stroke="#2563EB" stroke-width="3"/>'
    body += f'<path d="M 80,580 Q 200,560 320,580 Q 440,600 560,580 Q 680,560 720,580" fill="none" stroke="#2563EB" stroke-width="1.5"/>'
    body += txt(400, 650, "SHAPING FUTURES ONE STUDENT AT A TIME", "BebasNeue", 20, "#777", ls=2)
    return wrap("in_my_teacher_era", body)


def d10_game_day_vibes():
    """GAME DAY VIBES — diagonal stripe sports energy layout."""
    body = ""
    # Diagonal stripes
    for i in range(-5, 12):
        x1 = i * 80 - 50
        body += f'<line x1="{x1}" y1="0" x2="{x1 + 400}" y2="{H}" stroke="#FFF3CD" stroke-width="40"/>'
    body += txt(400, 210, "GAME", "BebasNeue", 145, "#CC1515", ls=6)
    body += hline(235, 80, 720, "#CC1515", 4)
    body += txt(400, 395, "Day", "GreatVibes", 155, "#1A1A2A")
    body += hline(435, 80, 720, "#CC1515", 4)
    body += txt(400, 530, "VIBES", "BebasNeue", 115, "#CC1515", ls=8)
    body += small_stars_row(400, 620, 5, 45, 12, "#CC1515")
    body += txt(400, 680, "ALL DAY EVERY DAY", "BebasNeue", 32, "#333", ls=5)
    return wrap("game_day_vibes", body)


def d11_blessed_mama():
    """BLESSED MAMA — clean cross + script, Christian identity crossover."""
    body = ""
    # Subtle circular halo
    body += circle_arc(400, 340, 180, stroke="#D4B483", sw=1.5)
    # Cross
    body += f'<rect x="384" y="150" width="32" height="180" fill="#8B5E3C" rx="4"/>'
    body += f'<rect x="320" y="200" width="160" height="32" fill="#8B5E3C" rx="4"/>'
    body += txt(400, 520, "Blessed", "GreatVibes", 130, "#8B5E3C")
    body += hline(558, 170, 630, "#D4B483", 2)
    body += txt(400, 610, "MAMA", "BebasNeue", 80, "#8B5E3C", ls=10)
    body += txt(400, 670, "PROVERBS 31:25", "BebasNeue", 28, "#B09060", ls=5)
    return wrap("blessed_mama", body)


def d12_dog_mom():
    """DOG MOM — paw print + bold identity, #4 bestselling niche."""
    body = ""
    # Paw print (circle + 4 toe beans)
    body += f'<circle cx="400" cy="340" r="70" fill="#333"/>'
    offsets = [(-55, -80, 28), (55, -80, 28), (-80, -30, 22), (80, -30, 22)]
    for ox, oy, r in offsets:
        body += f'<circle cx="{400 + ox}" cy="{340 + oy}" r="{r}" fill="#333"/>'
    body += txt(400, 195, "DOG", "BebasNeue", 130, "#333", ls=8)
    body += txt(400, 560, "Mom", "GreatVibes", 130, "#C9502A")
    body += hline(595, 160, 640, "#333", 2)
    body += txt(400, 645, "BECAUSE KIDS WERE TOO EASY", "BebasNeue", 25, "#555", ls=3)
    body += dot_row(400, 700, 5, 38, 5, "#C9502A")
    return wrap("dog_mom", body)


def d13_sunshine_hurricane():
    """SUNSHINE MIXED WITH A LITTLE HURRICANE — top relatable phrase."""
    body = ""
    # Sun rays
    for i in range(12):
        angle = math.radians(i * 30)
        r1, r2 = 100, 145
        x1 = 400 + r1 * math.cos(angle)
        y1 = 220 + r1 * math.sin(angle)
        x2 = 400 + r2 * math.cos(angle)
        y2 = 220 + r2 * math.sin(angle)
        body += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#F5A623" stroke-width="3"/>'
    body += f'<circle cx="400" cy="220" r="65" fill="#F5A623"/>'
    body += txt(400, 395, "Sunshine", "GreatVibes", 100, "#F5A623")
    body += txt(400, 460, "MIXED WITH A LITTLE", "BebasNeue", 36, "#333", ls=4)
    body += txt(400, 555, "HURRICANE", "BebasNeue", 95, "#CC4B1A", ls=6)
    body += dot_row(400, 620, 7, 36, 5, "#F5A623")
    body += txt(400, 680, "THAT'S JUST HOW SHE ROLLS", "BebasNeue", 24, "#777", ls=3)
    return wrap("sunshine_hurricane", body)


def d14_it_too_peopley():
    """IT'S TOO PEOPLEY OUTSIDE — sarcasm/humor phrase, #1 category."""
    body = ""
    # Simple door/house shape (outline)
    body += f'<rect x="285" y="220" width="230" height="260" fill="none" stroke="#1A1A1A" stroke-width="4" rx="4"/>'
    body += f'<path d="M270,220 L400,130 L530,220" fill="none" stroke="#1A1A1A" stroke-width="4"/>'
    body += f'<circle cx="480" cy="348" r="10" fill="#C9952A"/>'
    body += txt(400, 180, "IT'S", "BebasNeue", 72, "#333", ls=8)
    # Text sits below house
    body += txt(400, 545, "Too", "GreatVibes", 115, "#CC4B1A")
    body += txt(400, 614, "PEOPLEY", "BebasNeue", 88, "#1A1A2A", ls=6)
    body += txt(400, 672, "OUTSIDE", "BebasNeue", 60, "#555", ls=10)
    body += txt(400, 730, "STAYING IN FOREVER", "BebasNeue", 22, "#AAA", ls=3)
    return wrap("it_too_peopley", body)


def d15_boho_christian_svg():
    """BOHO CHRISTIAN — #1 bestselling Etsy SVG niche — boho + Bible verse combo."""
    body = ""
    # Boho wreath (simplified botanical arcs)
    for i, (r, angle, length) in enumerate([
        (155, -70, 70), (155, -50, 80), (155, -30, 65), (155, -10, 75),
        (155, 10, 70), (155, 30, 65), (155, 250, 70), (155, 270, 80),
        (155, 290, 65), (155, 310, 75), (155, 330, 70), (155, 350, 65)
    ]):
        ax = 400 + r * math.cos(math.radians(angle))
        ay = 400 + r * math.sin(math.radians(angle))
        # Leaf elongated ellipse
        la = math.radians(angle + 90)
        body += (f'<ellipse cx="{ax:.1f}" cy="{ay:.1f}" rx="{length // 3}" ry="{length // 6 + 2}" '
                 f'fill="#7A9A6A" transform="rotate({angle + 90},{ax:.1f},{ay:.1f})"/>')
    body += txt(400, 310, "She Is", "GreatVibes", 95, "#5A3E28")
    body += txt(400, 415, "STRONG", "BebasNeue", 115, "#5A3E28", ls=8)
    body += hline(440, 230, 570, "#9C7B3A", 1.5)
    body += txt(400, 490, "PROVERBS 31:25", "BebasNeue", 30, "#9C7B3A", ls=5)
    body += txt(400, 560, "SHE IS CLOTHED WITH STRENGTH", "BebasNeue", 22, "#777", ls=2)
    body += txt(400, 600, "AND DIGNITY", "BebasNeue", 22, "#777", ls=2)
    return wrap("boho_christian_svg", body)


def d16_girl_mom():
    """GIRL MOM — hearts + glam, identity design."""
    body = ""
    # Hearts scattered
    for (hx, hy, hs) in [(180, 150, 22), (620, 180, 18), (140, 580, 16), (660, 560, 20), (150, 370, 14)]:
        body += heart(hx, hy, size=hs, fill="#FF9AB2")
    body += txt(400, 220, "GIRL", "BebasNeue", 140, "#CC1F6A", ls=8)
    body += hline(245, 120, 680, "#FF9AB2", 2.5)
    body += txt(400, 395, "Mom", "GreatVibes", 150, "#CC1F6A")
    body += hline(432, 120, 680, "#FF9AB2", 2.5)
    body += dot_row(400, 470, 5, 38, 5, "#CC1F6A")
    body += txt(400, 535, "RAISING ROYALTY", "BebasNeue", 50, "#CC1F6A", ls=6)
    body += txt(400, 600, "SERVING FIERCE SINCE DAY ONE", "BebasNeue", 25, "#AA5577", ls=3)
    body += small_stars_row(400, 660, 5, 38, 10, "#FF9AB2")
    return wrap("girl_mom", body)


def d17_boy_mom():
    """BOY MOM — bold navy/orange, energetic stacked layout."""
    body = ""
    # Lightning bolt
    pts = "420,120 370,340 410,340 360,580 440,320 400,320 450,120"
    body += f'<polygon points="{pts}" fill="#F5A623"/>'
    body += txt(400, 198, "BOY", "BebasNeue", 130, "#1B2A6B", ls=8)
    body += hline(218, 140, 660, "#1B2A6B", 3)
    body += txt(400, 390, "Mom", "GreatVibes", 148, "#F5A623")
    body += hline(425, 140, 660, "#1B2A6B", 3)
    body += txt(400, 500, "BRAVE + BOLD + LOUD", "BebasNeue", 40, "#1B2A6B", ls=5)
    body += txt(400, 570, "LIVING FOR THE CHAOS", "BebasNeue", 30, "#888", ls=4)
    return wrap("boy_mom", body)


def d18_bonus_mom():
    """BONUS MOM — growing step-family niche, heart-centered."""
    body = ""
    # Large heart outline
    s = 80
    cx, cy = 400, 295
    body += (f'<path d="M{cx},{cy + 12 * s // 40} '
             f'C{cx},{cy + 6 * s // 40} {cx - 20 * s // 40},{cy - 15 * s // 40} {cx - 20 * s // 40},{cy - 5 * s // 40} '
             f'A{10 * s // 40},{10 * s // 40} 0 0,1 {cx},{cy + 3 * s // 40} '
             f'A{10 * s // 40},{10 * s // 40} 0 0,1 {cx + 20 * s // 40},{cy - 5 * s // 40} '
             f'C{cx + 20 * s // 40},{cy - 15 * s // 40} {cx},{cy + 6 * s // 40} {cx},{cy + 12 * s // 40}" '
             f'fill="#FFD5E0" stroke="#E84080" stroke-width="3"/>')
    body += txt(400, 225, "NOT STEP", "BebasNeue", 44, "#E84080", ls=5)
    body += txt(400, 285, "Bonus", "GreatVibes", 120, "#E84080")
    body += txt(400, 330, "MOM", "BebasNeue", 70, "#E84080", ls=10)
    body += hline(400, 190, 610, "#E84080", 2)
    body += txt(400, 455, "chosen, not given", "GreatVibes", 68, "#CC1F6A")
    body += txt(400, 530, "LOVE MAKES A FAMILY", "BebasNeue", 36, "#AA3366", ls=4)
    body += small_stars_row(400, 600, 5, 40, 10, "#E84080")
    body += txt(400, 660, "SHOWING UP EVERY SINGLE DAY", "BebasNeue", 22, "#888", ls=2)
    return wrap("bonus_mom", body)


def d19_chaos_coordinator():
    """CHAOS COORDINATOR — mom humor, clipboard/crown vibe."""
    body = ""
    # Crown at top
    crown_pts = "300,200 300,150 340,175 380,120 420,175 460,150 500,175 500,200"
    body += f'<polygon points="{crown_pts}" fill="#C9952A"/>'
    body += f'<rect x="298" y="198" width="204" height="16" fill="#C9952A" rx="4"/>'
    body += txt(400, 330, "CHAOS", "BebasNeue", 112, "#1A1A2A", ls=6)
    body += txt(400, 440, "Coordinator", "GreatVibes", 92, "#C9952A")
    body += hline(468, 170, 630, "#1A1A2A", 2)
    body += txt(400, 530, "OFFICIALLY LICENSED", "BebasNeue", 36, "#333", ls=5)
    body += txt(400, 595, "PROFESSIONAL MOM", "BebasNeue", 44, "#1A1A2A", ls=4)
    body += dot_row(400, 655, 7, 36, 5, "#C9952A")
    body += txt(400, 710, "NO TRAINING REQUIRED", "BebasNeue", 22, "#888", ls=3)
    return wrap("chaos_coordinator", body)


def d20_mini_mom_badge():
    """MINI ME MAMA — badge, clean 4-zone layout."""
    body = badge_circle(400, 400, 310, 278, "#CC1F6A", sw=3)

    # ZONE 1 — top arch
    body += arc_text(400, 400, 294, "RAISING MY MINI ME", "BebasNeue", 35, "#CC1F6A",
                     start_deg=215, end_deg=325, upward=False)
    body += hline(195, 200, 600, "#CC1F6A", 1.5)

    # ZONE 2 — large heart graphic, upper interior
    body += heart(400, 330, size=140, fill="#CC1F6A")

    body += hline(460, 200, 600, "#CC1F6A", 1.5)

    # ZONE 3 — text below heart
    body += small_stars_row(400, 502, 5, 38, 9, "#FF6BAD")
    body += txt(400, 555, "MAMA &amp; MINI", "BebasNeue", 46, "#CC1F6A", ls=6)

    # ZONE 4 — bottom arch
    body += arc_text(400, 400, 294, "TWINNING IS WINNING", "BebasNeue", 30, "#FF6BAD",
                     start_deg=35, end_deg=145, upward=True)
    return wrap("mini_mom_badge", body)


# ─────────────── Generate all ───────────────

designs = [
    ("retro_01_football_mom", d01_football_mom),
    ("retro_02_baseball_mama", d02_baseball_mama),
    ("retro_03_cheer_mom", d03_cheer_mom),
    ("retro_04_soccer_mama", d04_soccer_mama),
    ("retro_05_teacher_fuel", d05_teacher_fuel),
    ("retro_06_nurse_life", d06_nurse_life),
    ("retro_07_mama_mode", d07_mama_mode),
    ("retro_08_in_my_mama_era", d08_in_my_mama_era),
    ("retro_09_in_my_teacher_era", d09_in_my_teacher_era),
    ("retro_10_game_day_vibes", d10_game_day_vibes),
    ("retro_11_blessed_mama", d11_blessed_mama),
    ("retro_12_dog_mom", d12_dog_mom),
    ("retro_13_sunshine_hurricane", d13_sunshine_hurricane),
    ("retro_14_too_peopley", d14_it_too_peopley),
    ("retro_15_boho_christian", d15_boho_christian_svg),
    ("retro_16_girl_mom", d16_girl_mom),
    ("retro_17_boy_mom", d17_boy_mom),
    ("retro_18_bonus_mom", d18_bonus_mom),
    ("retro_19_chaos_coordinator", d19_chaos_coordinator),
    ("retro_20_mini_mom_badge", d20_mini_mom_badge),
]

for fname, fn in designs:
    path = OUT_DIR / f"{fname}.svg"
    svg = fn()
    path.write_text(svg, encoding="utf-8")
    print(f"  ✓ {fname}.svg")

print(f"\n✅ Generated {len(designs)} SVG designs → {OUT_DIR}")
