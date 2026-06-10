#!/usr/bin/env python3
"""
Generate 20 SVG cut files for 3D-printable signs.

Each SVG has:
- Outlined text (paths, no live <text> elements) suitable for Bambu Studio SVG import
- Dimensions in mm (1 user unit = 1 mm)
- Clean closed paths with proper Y-axis orientation

Usage: python tools/generate_3d_sign_svgs.py
Output: data/3d_print_signs/SVG/
"""

import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "3d_print_signs" / "SVG"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONTS = {
    "bebas":      "/usr/local/share/fonts/BebasNeue-Regular.ttf",
    "cinzel":     "/usr/local/share/fonts/Cinzel-Regular.ttf",
    "montserrat": "/usr/local/share/fonts/Montserrat-Bold.ttf",
    "oswald":     "/usr/local/share/fonts/Montserrat-Bold.ttf",  # Oswald.ttf is corrupt; Montserrat-Bold is visually similar
    "raleway":    "/usr/local/share/fonts/Raleway-Bold.ttf",
}

_font_cache: dict[str, TTFont] = {}


def load_font(name: str) -> TTFont:
    if name not in _font_cache:
        _font_cache[name] = TTFont(FONTS[name])
    return _font_cache[name]


def cap_height_units(font: TTFont) -> int:
    try:
        ch = font["OS/2"].sCapHeight
        if ch and ch > 0:
            return ch
    except (AttributeError, KeyError):
        pass
    return int(font["head"].unitsPerEm * 0.70)


def measure_text(text: str, font: TTFont, scale: float) -> float:
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    total = 0.0
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname and gname in gs:
            total += gs[gname].width * scale
        elif ch == " ":
            total += upm * 0.28 * scale
        else:
            total += upm * 0.28 * scale
    return total


def text_to_path(
    text: str, font: TTFont, size_mm: float, x: float, y_baseline: float
) -> str:
    """
    Render text as SVG path d string.
    size_mm:     desired cap height in mm
    x:           left edge x in mm
    y_baseline:  SVG baseline y (positive = down) in mm
    Returns:     path d string (empty string if no glyphs)
    """
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    ch = cap_height_units(font)
    scale = size_mm / ch  # mm per font unit

    parts = []
    cursor = x
    for char in text:
        if char == " ":
            cursor += upm * 0.28 * scale
            continue
        gname = cmap.get(ord(char))
        if gname is None or gname not in gs:
            cursor += upm * 0.28 * scale
            continue
        glyph = gs[gname]
        pen = SVGPathPen(gs)
        # Y-axis flip: font Y goes up, SVG Y goes down
        t_pen = TransformPen(pen, (scale, 0, 0, -scale, cursor, y_baseline))
        glyph.draw(t_pen)
        d = pen.getCommands()
        if d and d.strip():
            parts.append(d)
        cursor += glyph.width * scale

    return " ".join(parts)


def centered_line(
    text: str, font_name: str, size_mm: float,
    sign_w: float, cy: float
) -> str:
    """Return path d for text centered horizontally at vertical center cy."""
    font = load_font(font_name)
    ch = cap_height_units(font)
    scale = size_mm / ch
    total_w = measure_text(text, font, scale)
    x = (sign_w - total_w) / 2
    y_baseline = cy + size_mm / 2  # baseline below cap-height center
    return text_to_path(text, font, size_mm, x, y_baseline)


# ── SVG assembly ──────────────────────────────────────────────────────────────

def _rect(x, y, w, h, sw=0.8, fill="none") -> str:
    return (
        f'  <rect x="{x:.2f}" y="{y:.2f}" w="{w:.2f}" h="{h:.2f}" '
        f'fill="{fill}" stroke="black" stroke-width="{sw}"/>'
    )


def svg_rect(x, y, w, h, sw=0.8, fill="none") -> str:
    return (
        f'  <rect x="{x:.2f}" y="{y:.2f}" '
        f'width="{w:.2f}" height="{h:.2f}" '
        f'fill="{fill}" stroke="black" stroke-width="{sw}"/>'
    )


def svg_line(x1, y1, x2, y2, sw=0.8) -> str:
    return (
        f'  <line x1="{x1:.2f}" y1="{y1:.2f}" '
        f'x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="black" stroke-width="{sw}"/>'
    )


def svg_circle(cx, cy, r, fill="black") -> str:
    return f'  <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}"/>'


def svg_diamond(cx, cy, hw=2.0, hh=3.0) -> str:
    """Small diamond centred at cx, cy with half-width hw and half-height hh."""
    pts = (
        f"{cx:.2f},{cy-hh:.2f} "
        f"{cx+hw:.2f},{cy:.2f} "
        f"{cx:.2f},{cy+hh:.2f} "
        f"{cx-hw:.2f},{cy:.2f}"
    )
    return f'  <polygon fill="black" points="{pts}"/>'


def svg_star(cx, cy, r=3.0) -> str:
    """5-pointed star."""
    import math
    pts_list = []
    for i in range(10):
        angle = math.radians(-90 + i * 36)
        radius = r if i % 2 == 0 else r * 0.4
        px = cx + radius * math.cos(angle)
        py = cy + radius * math.sin(angle)
        pts_list.append(f"{px:.2f},{py:.2f}")
    pts = " ".join(pts_list)
    return f'  <polygon fill="black" points="{pts}"/>'


def svg_cross(cx, cy, size=5.0, sw=1.5) -> str:
    """Simple thin cross (+) shape."""
    h = size / 2
    return (
        f'  <line x1="{cx:.2f}" y1="{cy-h:.2f}" '
        f'x2="{cx:.2f}" y2="{cy+h:.2f}" stroke="black" stroke-width="{sw}"/>'
        f'  <line x1="{cx-h:.2f}" y1="{cy:.2f}" '
        f'x2="{cx+h:.2f}" y2="{cy:.2f}" stroke="black" stroke-width="{sw}"/>'
    )


def svg_path(d: str) -> str:
    if not d or not d.strip():
        return ""
    return f'  <path fill="black" d="{d}"/>'


def build_svg(w: float, h: float, elements: list[str]) -> str:
    """Assemble final SVG string from a list of element strings."""
    body = "\n".join(e for e in elements if e)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg"\n'
        f'     width="{w:.0f}mm" height="{h:.0f}mm"\n'
        f'     viewBox="0 0 {w:.0f} {h:.0f}">\n'
        f'{body}\n'
        '</svg>'
    )


def save(name: str, w: float, h: float, elements: list[str]) -> None:
    path = OUTPUT_DIR / f"{name}.svg"
    content = build_svg(w, h, elements)
    path.write_text(content, encoding="utf-8")
    print(f"  ✓  {path.name}  ({w:.0f}×{h:.0f}mm)")


# ── Sign definitions ──────────────────────────────────────────────────────────

def make_welcome_home():
    """WELCOME / HOME — two-line stacked with divider line."""
    w, h = 200.0, 80.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m),           # outer border
        svg_rect(m+2, m+2, w-2*(m+2), h-2*(m+2), sw=0.5),  # inner border
    ]
    # "WELCOME" centered at 30% height, ~20mm cap
    els.append(svg_path(centered_line("WELCOME", "bebas", 22, w, h * 0.35)))
    # divider line
    els.append(svg_line(w*0.2, h*0.52, w*0.8, h*0.52))
    els.append(svg_diamond(w/2, h*0.52))
    # "HOME" centered at 70% height
    els.append(svg_path(centered_line("HOME", "bebas", 20, w, h * 0.72)))
    save("welcome_home", w, h, els)


def make_home_sweet_home():
    """HOME SWEET HOME — single large line, double border."""
    w, h = 220.0, 70.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m),
        svg_rect(m+3, m+3, w-2*(m+3), h-2*(m+3), sw=0.5),
    ]
    els.append(svg_path(centered_line("HOME SWEET HOME", "cinzel", 22, w, h/2)))
    save("home_sweet_home", w, h, els)


def make_gather():
    """GATHER — large single word, farmhouse minimal style."""
    w, h = 200.0, 75.0
    m = 6.0
    els = [
        svg_line(m, m+2, w-m, m+2),      # top line
        svg_line(m, h-m-2, w-m, h-m-2),  # bottom line
    ]
    # Flanking dots
    cy = h / 2
    for x in [m+8, m+14]:
        els.append(svg_circle(x, cy, 1.2))
    for x in [w-m-8, w-m-14]:
        els.append(svg_circle(x, cy, 1.2))
    els.append(svg_path(centered_line("GATHER", "oswald", 32, w, cy)))
    save("gather", w, h, els)


def make_blessed():
    """BLESSED — with decorative cross and lines."""
    w, h = 180.0, 70.0
    m = 5.0
    cx = w / 2
    els = [
        svg_rect(m, m, w-2*m, h-2*m),
    ]
    # Small cross above text
    els.append(svg_cross(cx, h*0.25, size=7, sw=1.8))
    els.append(svg_path(centered_line("BLESSED", "cinzel", 22, w, h * 0.66)))
    save("blessed", w, h, els)


def make_wine_oclock():
    """WINE / O'CLOCK — bold two-line with diamond divider."""
    w, h = 200.0, 80.0
    m = 5.0
    els = [svg_rect(m, m, w-2*m, h-2*m)]
    els.append(svg_path(centered_line("WINE", "bebas", 24, w, h * 0.37)))
    els.append(svg_diamond(w/2, h * 0.535, hw=2.5, hh=3.5))
    els.append(svg_path(centered_line("O'CLOCK", "bebas", 18, w, h * 0.72)))
    save("wine_oclock", w, h, els)


def make_family_kitchen():
    """FAMILY KITCHEN — with top and bottom thin rule lines."""
    w, h = 210.0, 70.0
    m = 6.0
    els = [
        svg_line(m, h * 0.18, w - m, h * 0.18),
        svg_line(m, h * 0.82, w - m, h * 0.82),
    ]
    # Corner diamond accents on lines
    for x in [m + 5, w - m - 5]:
        els.append(svg_diamond(x, h * 0.18))
        els.append(svg_diamond(x, h * 0.82))
    els.append(svg_path(centered_line("FAMILY KITCHEN", "oswald", 22, w, h / 2)))
    save("family_kitchen", w, h, els)


def make_laundry_room():
    """LAUNDRY ROOM / wash dry fold repeat — two-line."""
    w, h = 220.0, 80.0
    m = 5.0
    els = [svg_rect(m, m, w-2*m, h-2*m, sw=1.2)]
    els.append(svg_path(centered_line("LAUNDRY ROOM", "oswald", 22, w, h * 0.38)))
    els.append(svg_line(w*0.15, h*0.54, w*0.85, h*0.54, sw=0.6))
    els.append(svg_path(centered_line("WASH · DRY · FOLD · REPEAT", "montserrat", 9, w, h * 0.73)))
    save("laundry_room", w, h, els)


def make_be_kind():
    """BE KIND — large, bold, minimal with thick border."""
    w, h = 160.0, 70.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m, sw=2.0),
    ]
    # Small heart-like diamond above
    els.append(svg_star(w/2, h * 0.22, r=4))
    els.append(svg_path(centered_line("BE KIND", "bebas", 28, w, h * 0.65)))
    save("be_kind", w, h, els)


def make_live_laugh_love():
    """LIVE · LAUGH · LOVE — single line, classic."""
    w, h = 240.0, 65.0
    m = 5.0
    els = [
        svg_line(m, m+1, w-m, m+1),
        svg_line(m, h-m-1, w-m, h-m-1),
    ]
    els.append(svg_path(centered_line("LIVE · LAUGH · LOVE", "cinzel", 20, w, h/2)))
    save("live_laugh_love", w, h, els)


def make_mom_boss():
    """MOM BOSS — bold two-line stacked."""
    w, h = 160.0, 90.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m, sw=1.5),
        svg_rect(m+3, m+3, w-2*(m+3), h-2*(m+3), sw=0.6),
    ]
    els.append(svg_path(centered_line("MOM", "bebas", 30, w, h * 0.40)))
    els.append(svg_line(w*0.25, h*0.55, w*0.75, h*0.55))
    els.append(svg_path(centered_line("BOSS", "bebas", 24, w, h * 0.75)))
    save("mom_boss", w, h, els)


def make_family_name_plate():
    """[SMITH] FAMILY / EST. 2024 — name plate style."""
    w, h = 200.0, 70.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m, sw=1.2),
    ]
    # Three diamond row divider
    cx = w / 2
    for dx in [-12, 0, 12]:
        els.append(svg_diamond(cx + dx, h * 0.56, hw=1.5, hh=2.0))
    els.append(svg_path(centered_line("YOUR NAME FAMILY", "raleway", 18, w, h * 0.38)))
    els.append(svg_path(centered_line("EST.  2024", "cinzel", 13, w, h * 0.77)))
    save("family_name_plate", w, h, els)


def make_established_year():
    """ESTABLISHED / ·2024· — decorative frame."""
    w, h = 180.0, 80.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m),
        svg_rect(m+2.5, m+2.5, w-2*(m+2.5), h-2*(m+2.5), sw=0.5),
    ]
    els.append(svg_path(centered_line("ESTABLISHED", "cinzel", 14, w, h * 0.36)))
    # Big year centered
    els.append(svg_path(centered_line("· 2024 ·", "montserrat", 22, w, h * 0.72)))
    save("established_year", w, h, els)


def make_dream_big():
    """DREAM / BIG — vertical sign, stacked large."""
    w, h = 90.0, 200.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m),
        svg_rect(m+3, m+3, w-2*(m+3), h-2*(m+3), sw=0.5),
    ]
    els.append(svg_star(w/2, h*0.16, r=6))
    els.append(svg_path(centered_line("DREAM", "bebas", 26, w, h * 0.43)))
    els.append(svg_line(w*0.15, h*0.56, w*0.85, h*0.56))
    els.append(svg_path(centered_line("BIG", "bebas", 34, w, h * 0.74)))
    save("dream_big", w, h, els)


def make_adventure_awaits():
    """ADVENTURE / AWAITS — horizontal bold two-line."""
    w, h = 220.0, 80.0
    m = 5.0
    els = [svg_line(m, m+1, w-m, m+1), svg_line(m, h-m-1, w-m, h-m-1)]
    els.append(svg_path(centered_line("ADVENTURE", "oswald", 24, w, h * 0.40)))
    # Row of 5 diamonds as divider
    for i in range(5):
        x = w/2 + (i - 2) * 12
        els.append(svg_diamond(x, h * 0.555, hw=2, hh=2.5))
    els.append(svg_path(centered_line("AWAITS", "oswald", 20, w, h * 0.75)))
    save("adventure_awaits", w, h, els)


def make_in_this_house():
    """IN THIS HOUSE [rules] — vertical list sign."""
    w, h = 120.0, 210.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m, sw=1.5),
        svg_rect(m+3, m+3, w-2*(m+3), h-2*(m+3), sw=0.7),
    ]
    els.append(svg_path(centered_line("IN THIS", "montserrat", 13, w, h * 0.12)))
    els.append(svg_path(centered_line("HOUSE", "bebas", 20, w, h * 0.22)))
    els.append(svg_line(m+8, h*0.28, w-m-8, h*0.28))

    rules = ["WE DO LOVE", "WE DO GRACE", "WE DO REAL", "WE DO MISTAKES", "WE DO FAMILY"]
    for i, rule in enumerate(rules):
        cy = h * (0.38 + i * 0.116)
        els.append(svg_path(centered_line(rule, "montserrat", 9.5, w, cy)))

    els.append(svg_line(m+8, h*0.945, w-m-8, h*0.945))
    els.append(svg_path(centered_line("& WE DO US", "cinzel", 10, w, h * 0.965)))
    save("in_this_house", w, h, els)


def make_wash_your_hands():
    """WASH YOUR HANDS / before leaving — bathroom sign."""
    w, h = 170.0, 80.0
    m = 5.0
    els = [svg_rect(m, m, w-2*m, h-2*m)]
    els.append(svg_path(centered_line("WASH YOUR HANDS", "oswald", 20, w, h * 0.40)))
    els.append(svg_line(w*0.2, h*0.56, w*0.8, h*0.56, sw=0.6))
    els.append(svg_path(centered_line("before you leave", "raleway", 11, w, h * 0.74)))
    save("wash_your_hands", w, h, els)


def make_game_room():
    """GAME ROOM — bold large, thick border."""
    w, h = 180.0, 70.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m, sw=2.2),
    ]
    # Small stars flanking
    for x in [m+14, w-m-14]:
        els.append(svg_star(x, h/2, r=4))
    els.append(svg_path(centered_line("GAME ROOM", "bebas", 28, w, h/2)))
    save("game_room", w, h, els)


def make_man_cave():
    """MAN CAVE — bold, framed, rugged."""
    w, h = 180.0, 70.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m, sw=2.5),
    ]
    els.append(svg_path(centered_line("MAN CAVE", "oswald", 30, w, h/2)))
    save("man_cave", w, h, els)


def make_hello_beautiful():
    """HELLO / BEAUTIFUL — nursery / feminine, double border."""
    w, h = 160.0, 100.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m),
        svg_rect(m+3, m+3, w-2*(m+3), h-2*(m+3), sw=0.5),
    ]
    els.append(svg_star(w/2, h*0.18, r=5))
    els.append(svg_path(centered_line("HELLO", "raleway", 22, w, h * 0.48)))
    els.append(svg_path(centered_line("BEAUTIFUL", "cinzel", 16, w, h * 0.73)))
    save("hello_beautiful", w, h, els)


def make_be_brave():
    """BE BRAVE / BE KIND / BE YOU — triple motivational."""
    w, h = 130.0, 180.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m),
        svg_rect(m+2.5, m+2.5, w-2*(m+2.5), h-2*(m+2.5), sw=0.5),
    ]
    els.append(svg_star(w/2, h*0.12, r=5))
    els.append(svg_path(centered_line("BE BRAVE", "bebas", 24, w, h * 0.35)))
    els.append(svg_line(w*0.2, h*0.46, w*0.8, h*0.46))
    els.append(svg_path(centered_line("BE KIND", "bebas", 24, w, h * 0.58)))
    els.append(svg_line(w*0.2, h*0.68, w*0.8, h*0.68))
    els.append(svg_path(centered_line("BE YOU", "bebas", 24, w, h * 0.81)))
    save("be_brave", w, h, els)


def make_address_plaque():
    """123 MAIN ST — address plaque style."""
    w, h = 200.0, 60.0
    m = 5.0
    els = [
        svg_rect(m, m, w-2*m, h-2*m, sw=2.0),
    ]
    els.append(svg_path(centered_line("123 MAPLE STREET", "oswald", 22, w, h * 0.55)))
    save("address_plaque", w, h, els)


def make_joy():
    """JOY — oversized single word, holiday."""
    w, h = 130.0, 80.0
    m = 6.0
    els = [
        svg_line(m, m+1.5, w-m, m+1.5, sw=1.5),
        svg_line(m, h-m-1.5, w-m, h-m-1.5, sw=1.5),
        svg_line(m, m+5, w-m, m+5, sw=0.5),
        svg_line(m, h-m-5, w-m, h-m-5, sw=0.5),
    ]
    els.append(svg_path(centered_line("JOY", "cinzel", 38, w, h / 2)))
    save("joy", w, h, els)


# ── Main ──────────────────────────────────────────────────────────────────────

SIGNS = [
    ("welcome_home",       make_welcome_home),
    ("home_sweet_home",    make_home_sweet_home),
    ("gather",             make_gather),
    ("blessed",            make_blessed),
    ("wine_oclock",        make_wine_oclock),
    ("family_kitchen",     make_family_kitchen),
    ("laundry_room",       make_laundry_room),
    ("be_kind",            make_be_kind),
    ("live_laugh_love",    make_live_laugh_love),
    ("mom_boss",           make_mom_boss),
    ("family_name_plate",  make_family_name_plate),
    ("established_year",   make_established_year),
    ("dream_big",          make_dream_big),
    ("adventure_awaits",   make_adventure_awaits),
    ("in_this_house",      make_in_this_house),
    ("wash_your_hands",    make_wash_your_hands),
    ("game_room",          make_game_room),
    ("man_cave",           make_man_cave),
    ("hello_beautiful",    make_hello_beautiful),
    ("be_brave",           make_be_brave),
    ("address_plaque",     make_address_plaque),
    ("joy",                make_joy),
]


def main():
    print(f"Generating 3D print sign SVGs → {OUTPUT_DIR}")
    print("=" * 55)
    ok = 0
    for slug, fn in SIGNS:
        try:
            fn()
            ok += 1
        except Exception as e:
            print(f"  ✗  {slug}: {e}")
    print("=" * 55)
    print(f"Generated {ok}/{len(SIGNS)} signs")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
