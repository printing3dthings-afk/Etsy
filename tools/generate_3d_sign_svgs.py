#!/usr/bin/env python3
"""
Generate multi-layer SVG sign files for 3D printing on Bambu P1S with AMS.

Each sign is a folder containing one SVG per color layer.
Bambu Studio: import each layer SVG as a separate Part, assign to AMS slot,
stack in Z (base 3mm → raised layer 2mm on top).

Design rules:
  - Minimum stroke/feature width: 1.5mm (3× nozzle diameter for 0.4mm nozzle)
  - Anton font for all bold display text — thick strokes, high impact
  - All text converted to paths (no live <text> elements)
  - Coordinates in mm (1 SVG user unit = 1 mm)
  - Layer SVGs share identical viewBox — same origin, same sign dimensions

America 250 official colors:
  Red   #F90000  (Pantone 485 C — official US250 brand, brighter than flag red)
  Blue  #3250FF  (Pantone 2935 C)
  White #FFFFFF

Output: data/3d_print_signs/
"""

import math
import sys
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

OUT_ROOT = Path(__file__).parent.parent / "data" / "3d_print_signs"
OUT_ROOT.mkdir(parents=True, exist_ok=True)

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_PATHS = {
    "anton":      "/usr/local/share/fonts/google/Anton-Regular.ttf",
    "blackops":   "/usr/local/share/fonts/google/BlackOpsOne-Regular.ttf",
    "bebas":      "/usr/local/share/fonts/google/BebasNeue-Regular.ttf",
    "montserrat": "/usr/local/share/fonts/google/Montserrat-VF.ttf",
    "archivo":    "/usr/local/share/fonts/google/ArchivoBlack-Regular.ttf",
    "lilita":     "/usr/local/share/fonts/google/LilitaOne-Regular.ttf",
}
_fcache: dict = {}


def _font(name: str) -> TTFont:
    if name not in _fcache:
        _fcache[name] = TTFont(FONT_PATHS[name])
    return _fcache[name]


def _cap_h(font: TTFont) -> int:
    try:
        ch = font["OS/2"].sCapHeight
        if ch and ch > 0:
            return ch
    except Exception:
        pass
    return int(font["head"].unitsPerEm * 0.72)


def measure(text: str, fname: str, size_mm: float) -> float:
    """Return total advance width of text rendered at size_mm cap height."""
    font = _font(fname)
    scale = size_mm / _cap_h(font)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    total = 0.0
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname and gname in gs:
            total += gs[gname].width * scale
        else:
            total += upm * 0.28 * scale
    return total


def text2path(text: str, fname: str, size_mm: float, x: float, y_baseline: float) -> str:
    """Convert text to SVG path d string. y_baseline is the baseline in mm (SVG positive-down)."""
    font = _font(fname)
    cap_h = _cap_h(font)
    scale = size_mm / cap_h
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    parts, cursor = [], x
    for ch in text:
        if ch == " ":
            cursor += upm * 0.28 * scale
            continue
        gname = cmap.get(ord(ch))
        if gname is None or gname not in gs:
            cursor += upm * 0.28 * scale
            continue
        glyph = gs[gname]
        pen = SVGPathPen(gs)
        t_pen = TransformPen(pen, (scale, 0, 0, -scale, cursor, y_baseline))
        glyph.draw(t_pen)
        d = pen.getCommands()
        if d and d.strip():
            parts.append(d)
        cursor += glyph.width * scale
    return " ".join(parts)


def hcenter(text: str, fname: str, size_mm: float, sign_w: float, cy: float) -> str:
    """Return path d for text horizontally centered in sign_w, vertically at cy."""
    tw = measure(text, fname, size_mm)
    x = (sign_w - tw) / 2
    return text2path(text, fname, size_mm, x, cy + size_mm / 2)


# ── SVG geometry helpers ──────────────────────────────────────────────────────

def _p(d: str, fr: str = "evenodd") -> str:
    if not d or not d.strip():
        return ""
    return f'<path fill="black" fill-rule="{fr}" d="{d}"/>'


def rrect(x: float, y: float, w: float, h: float, rx: float = 0) -> str:
    """Rounded rectangle as path d string."""
    if rx <= 0:
        return f"M{x:.2f},{y:.2f}H{x+w:.2f}V{y+h:.2f}H{x:.2f}Z"
    r = min(rx, w / 2, h / 2)
    return (
        f"M{x+r:.2f},{y:.2f}H{x+w-r:.2f}Q{x+w:.2f},{y:.2f} {x+w:.2f},{y+r:.2f}"
        f"V{y+h-r:.2f}Q{x+w:.2f},{y+h:.2f} {x+w-r:.2f},{y+h:.2f}"
        f"H{x+r:.2f}Q{x:.2f},{y+h:.2f} {x:.2f},{y+h-r:.2f}"
        f"V{y+r:.2f}Q{x:.2f},{y:.2f} {x+r:.2f},{y:.2f}Z"
    )


def circle(cx: float, cy: float, r: float) -> str:
    """Circle as SVG path (two arcs)."""
    return (f"M{cx+r:.2f},{cy:.2f}"
            f"A{r:.2f},{r:.2f} 0 1 0 {cx-r:.2f},{cy:.2f}"
            f"A{r:.2f},{r:.2f} 0 1 0 {cx+r:.2f},{cy:.2f}Z")


def ring(cx: float, cy: float, r_out: float, r_in: float) -> str:
    """Annular ring using even-odd rule."""
    outer = (f"M{cx+r_out:.2f},{cy:.2f}"
             f"A{r_out:.2f},{r_out:.2f} 0 1 0 {cx-r_out:.2f},{cy:.2f}"
             f"A{r_out:.2f},{r_out:.2f} 0 1 0 {cx+r_out:.2f},{cy:.2f}Z")
    inner = (f"M{cx+r_in:.2f},{cy:.2f}"
             f"A{r_in:.2f},{r_in:.2f} 0 1 0 {cx-r_in:.2f},{cy:.2f}"
             f"A{r_in:.2f},{r_in:.2f} 0 1 0 {cx+r_in:.2f},{cy:.2f}Z")
    return outer + " " + inner


def star(cx: float, cy: float, r_out: float, r_in: float = None) -> str:
    """5-pointed star path."""
    if r_in is None:
        r_in = r_out * 0.382
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return "M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + "Z"


def star_row(n: int, y: float, sign_w: float, r: float, margin: float = 8) -> str:
    """Row of n stars evenly spaced horizontally, centered in sign_w."""
    spacing = (sign_w - 2 * margin) / max(n - 1, 1)
    parts = []
    for i in range(n):
        cx = margin + i * spacing
        parts.append(star(cx, y, r))
    return " ".join(parts)


def star_ring(n: int, cx: float, cy: float, r: float, star_r: float) -> str:
    """n stars arranged in a ring of radius r, centered at cx, cy."""
    parts = []
    for i in range(n):
        a = math.radians(-90 + i * 360 / n)
        sx = cx + r * math.cos(a)
        sy = cy + r * math.sin(a)
        parts.append(star(sx, sy, star_r))
    return " ".join(parts)


def starburst(cx: float, cy: float, r_out: float, r_in: float, n: int = 16) -> str:
    """Starburst/sun shape."""
    pts = []
    for i in range(n * 2):
        a = math.radians(i * 180 / n)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return "M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + "Z"


def firework(cx: float, cy: float, r_out: float, r_in: float, n: int = 8) -> str:
    """Firework burst as starburst."""
    return starburst(cx, cy, r_out, r_in, n)


def canton(x: float, y: float, w: float, h: float,
           rows, cols, sr: float) -> str:
    """Star field: alternating rows of cols and cols-1 stars filling rectangle."""
    parts = [rrect(x, y, w, h)]  # filled canton background (will be cut by even-odd)
    for row in range(rows):
        n = cols if row % 2 == 0 else cols - 1
        offset = 0 if row % 2 == 0 else (w / cols) / 2
        for col in range(n):
            cx = x + offset + col * (w / cols) + (w / cols) / 2
            cy = y + (row + 0.5) * (h / rows)
            parts.append(star(cx, cy, sr))
    return " ".join(parts)


def hline(x1: float, y: float, x2: float, thickness: float) -> str:
    """Solid horizontal bar (as filled rectangle)."""
    return rrect(x1, y - thickness / 2, x2 - x1, thickness)


def vline(x: float, y1: float, y2: float, thickness: float) -> str:
    """Solid vertical bar."""
    return rrect(x - thickness / 2, y1, thickness, y2 - y1)


def banner_arch(cx: float, y_top: float, w: float, h: float) -> str:
    """Rectangular banner with slight arch (rounded top corners only)."""
    r = h * 0.3
    x = cx - w / 2
    return (
        f"M{x:.2f},{y_top+r:.2f}"
        f"Q{x:.2f},{y_top:.2f} {x+r:.2f},{y_top:.2f}"
        f"H{x+w-r:.2f}Q{x+w:.2f},{y_top:.2f} {x+w:.2f},{y_top+r:.2f}"
        f"V{y_top+h:.2f}H{x:.2f}Z"
    )


# ── SVG file builder ──────────────────────────────────────────────────────────

def make_svg(w: float, h: float, elements: list[str]) -> str:
    body = "\n  ".join(e for e in elements if e)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg"\n'
        f'     width="{w:.0f}mm" height="{h:.0f}mm"\n'
        f'     viewBox="0 0 {w:.0f} {h:.0f}">\n'
        f'  {body}\n'
        '</svg>'
    )


class Layer:
    def __init__(self, name: str, color_hint: str, elements: list[str]):
        self.name = name          # e.g. "base", "red", "blue"
        self.color_hint = color_hint  # e.g. "WHITE", "RED", "BLUE NAVY"
        self.elements = elements

    def svg(self, w: float, h: float) -> str:
        return make_svg(w, h, self.elements)


class Sign:
    def __init__(self, slug: str, w: float, h: float, layers: list[Layer]):
        self.slug = slug
        self.w = w
        self.h = h
        self.layers = layers

    def save(self, parent_dir: Path) -> Path:
        d = parent_dir / self.slug
        d.mkdir(parents=True, exist_ok=True)
        for i, layer in enumerate(self.layers, 1):
            fname = f"layer{i:02d}_{layer.name}_{layer.color_hint}.svg"
            (d / fname).write_text(layer.svg(self.w, self.h), encoding="utf-8")
        _make_preview(self, d)
        return d


# ── Preview composite ─────────────────────────────────────────────────────────

PREVIEW_COLORS = {
    "WHITE":  (245, 245, 240),
    "CREAM":  (240, 230, 205),
    "RED":    (249,   0,   0),
    "BLUE":   ( 50,  80, 255),
    "NAVY":   (  0,  40, 104),
    "BLACK":  ( 30,  30,  30),
    "BROWN":  ( 80,  50,  25),
    "YELLOW": (255, 200,  30),
    "NATURAL":(210, 175, 125),
    "DARK":   ( 40,  40,  40),
    "TEAL":   ( 30, 130, 130),
    "GREEN":  ( 60, 140,  60),
    "PURPLE": (120,  60, 160),
}


def _make_preview(sign: Sign, sign_dir: Path) -> None:
    """Composite all layers into a single preview PNG."""
    SCALE = 4  # px per mm
    pw = int(sign.w * SCALE)
    ph = int(sign.h * SCALE)
    canvas = Image.new("RGB", (pw, ph), (200, 200, 200))

    for layer in sign.layers:
        color_key = layer.color_hint.split()[0].upper()
        fill_rgb = PREVIEW_COLORS.get(color_key, (180, 180, 180))

        # Render the layer SVG to PNG using cairosvg
        svg_content = layer.svg(sign.w, sign.h).encode("utf-8")
        try:
            png_bytes = cairosvg.svg2png(bytestring=svg_content,
                                          output_width=pw, output_height=ph)
            layer_img = Image.open(__import__("io").BytesIO(png_bytes)).convert("RGBA")
        except Exception:
            continue

        # Colorize: black pixels → fill_rgb, transparent stays transparent
        import numpy as np
        data = np.array(layer_img)
        # Pixels where alpha > 32 (dark/filled) get the layer color
        mask = data[:, :, 3] > 32
        colored = Image.new("RGB", (pw, ph), fill_rgb)
        # Composite colored layer onto canvas where mask is True
        canvas_arr = np.array(canvas)
        canvas_arr[mask] = fill_rgb
        canvas = Image.fromarray(canvas_arr)

    # Save preview
    preview_path = sign_dir / "preview.jpg"
    canvas.save(str(preview_path), "JPEG", quality=90)


# ═══════════════════════════════════════════════════════════════════════════════
#  AMERICA 250 PACKAGE
# ═══════════════════════════════════════════════════════════════════════════════

A250_DIR = OUT_ROOT / "america_250"
A250_DIR.mkdir(parents=True, exist_ok=True)


def make_a250_america_bold() -> Sign:
    """
    Giant "AMERICA" fills the width — the simplest, most eye-catching format.
    Star rows frame the text top and bottom. "1776 · 2026" sits below as the footer.
    280 × 165 mm
    """
    W, H, RX = 280.0, 165.0, 8.0
    bw = 3.0

    base = [_p(rrect(0, 0, W, H, RX))]

    # RED: top star row + bottom star row + dates footer
    red_els = []
    red_els.append(_p(star_row(11, 14.0, W, 5.5)))
    red_els.append(_p(star_row(11, 151.0, W, 5.5)))
    # Dates: cy=116 → baseline=123mm, cap_top=111mm
    # AMERICA baseline=92mm → gap 19mm; star top at 145.5mm → gap 22.5mm ✓
    red_els.append(_p(hcenter("1776  •  2026", "bebas", 14.0, W, 116.0)))

    # BLUE: "AMERICA" giant 60mm + double border
    # cy=62 → baseline=92mm, cap_top=40.4mm; star bottom=19.5mm → gap 20.9mm ✓
    blue_els = []
    blue_els.append(_p(hcenter("AMERICA", "anton", 60.0, W, 62.0)))
    blue_els.append(_p(rrect(0, 0, W, H, RX) + " " + rrect(bw, bw, W-2*bw, H-2*bw, RX-bw)))

    return Sign("01_america250_america_bold", W, H, [
        Layer("base", "WHITE", base),
        Layer("red", "RED", red_els),
        Layer("blue", "BLUE", blue_els),
    ])


def make_a250_star_badge() -> Sign:
    """
    Circular badge — "AMERICA" top, huge "250" center, 13-star ring, dates.
    Horizontal bars removed — they were crossing through the "250" text.
    220 × 220 mm
    """
    W = H = 220.0
    CX, CY = W / 2, H / 2   # = 110
    R_OUTER = 107.0
    R_IN = R_OUTER - 22.0    # inner radius = 85mm

    base = [_p(circle(CX, CY, R_OUTER))]

    # RED: large "250" — sole element, no bars, no subtitle
    red_els = []
    big_size = 68.0
    big_w = measure("250", "anton", big_size)
    big_x = (W - big_w) / 2
    big_cy = CY - 2.0   # = 108mm
    # baseline=142mm, cap_top=83.6mm — inside inner circle (25..195mm) ✓
    red_els.append(_p(text2path("250", "anton", big_size, big_x, big_cy + big_size / 2)))

    # BLUE: outer ring border + "AMERICA" above + 13-star ring + dates below
    blue_els = []
    blue_els.append(_p(ring(CX, CY, R_OUTER, R_OUTER - 5.0)))

    # "AMERICA" — cy=56: baseline=68mm, cap_top=47mm; gap to 250 cap_top(83.6mm)=15.6mm ✓
    blue_els.append(_p(hcenter("AMERICA", "anton", 24.0, W, 56.0)))

    # 13 stars (one per original colony) carved white into ring via even-odd
    blue_els.append(_p(star_ring(13, CX, CY, R_OUTER - 14, 5.0)))

    # dates — cy=162: baseline=169.5mm, cap_top=156.6mm; gap to 250 baseline(142mm)=14.6mm ✓
    # at y=169.5, hw=sqrt(85²-58.5²)=61.7mm → 123mm available, fits ✓
    blue_els.append(_p(hcenter("1776  •  2026", "montserrat", 15.0, W, 162.0)))

    return Sign("02_america250_star_badge", W, H, [
        Layer("base", "WHITE", base),
        Layer("red", "RED", red_els),
        Layer("blue", "BLUE", blue_els),
    ])


def make_a250_freedom_sign() -> Sign:
    """
    LET FREEDOM RING — vintage poster energy.
    Blue bands top/bottom carved white. Red FREEDOM hero center. Stars flanking.
    280 × 182 mm
    """
    W, H, RX = 280.0, 182.0, 8.0
    bw = 2.5
    top_h, bot_start = 55.0, 127.0   # blue bands; white zone = y 55..127 (72mm)
    CY_white = (top_h + bot_start) / 2   # = 91mm

    base = [_p(rrect(0, 0, W, H, RX))]

    # RED: "FREEDOM" Anton 58mm + 2 side stars flanking in white zone
    red_els = []
    # cy=91mm (center of white zone) → baseline=91+29=120mm, cap_top=120-49.8=70.2mm
    # zone top=55mm → gap 15.2mm ✓; zone bottom=127mm → gap 7mm ✓
    red_els.append(_p(hcenter("FREEDOM", "anton", 58.0, W, CY_white)))
    red_els.append(_p(star(12.0, CY_white, 7.0)))
    red_els.append(_p(star(268.0, CY_white, 7.0)))

    # BLUE: top band carved, bottom band carved, double border
    blue_els = []

    # Top band: rrect top-only shape + "LET" BlackOps 34mm + flanking stars (even-odd)
    # "LET" at 34mm BlackOps ≈ 101mm wide → left edge at (280-101)/2=89.5mm
    # cy=top_h*0.46=25.3mm → baseline=25.3+17=42.3mm, cap_top=42.3-22.0=20.3mm ✓
    band_top = rrect(0, 0, W, top_h, RX)
    let_d = hcenter("LET", "blackops", 34.0, W, top_h * 0.46)
    stars_top = star(42.0, top_h * 0.46, 7.0) + " " + star(238.0, top_h * 0.46, 7.0)
    blue_els.append(_p(band_top + " " + let_d + " " + stars_top))

    # Bottom band + "RING" carved + flanking stars
    # "RING" BlackOps 34mm ≈ 122mm → left edge at (280-122)/2=79mm
    # cy=bot_start+top_h*0.46=127+25.3=152.3mm → baseline=152.3+17=169.3mm, cap_top=147.3mm ✓
    band_bot = rrect(0, bot_start, W, top_h, RX)
    ring_d = hcenter("RING", "blackops", 34.0, W, bot_start + top_h * 0.46)
    stars_bot = star(42.0, bot_start + top_h * 0.46, 7.0) + " " + star(238.0, bot_start + top_h * 0.46, 7.0)
    blue_els.append(_p(band_bot + " " + ring_d + " " + stars_bot))

    # Double border
    blue_els.append(_p(rrect(0, 0, W, H, RX) + " " + rrect(bw, bw, W-2*bw, H-2*bw, RX-bw)))

    return Sign("03_america250_freedom_sign", W, H, [
        Layer("base", "WHITE", base),
        Layer("red", "RED", red_els),
        Layer("blue", "BLUE", blue_els),
    ])


def make_a250_happy_4th() -> Sign:
    """
    HAPPY 4TH OF JULY — dramatic size hierarchy.
    Red bands top/bottom carved white. Blue "4TH" dominates the center.
    260 × 180 mm
    """
    W, H, RX = 260.0, 180.0, 8.0
    bw = 2.5
    top_h = 46.0
    bot_h = 42.0
    bot_start = H - bot_h    # = 138mm; white zone y=46..138 (92mm)
    CY_white = (top_h + bot_start) / 2   # = 92mm

    base = [_p(rrect(0, 0, W, H, RX))]

    # RED: top band "HAPPY" carved + flanking stars; bottom band "OF JULY" carved + flanking stars
    red_els = []

    # "HAPPY" BlackOps 24mm ≈ 130mm → left edge at (260-130)/2=65mm
    # cy=top_h*0.46=21.2mm → baseline=21.2+12=33.2mm, cap_top=33.2-15.5=17.7mm ✓
    band_top = rrect(0, 0, W, top_h, RX)
    happy_d = hcenter("HAPPY", "blackops", 24.0, W, top_h * 0.46)
    stars_top = star(38.0, top_h * 0.46, 7.0) + " " + star(222.0, top_h * 0.46, 7.0)
    red_els.append(_p(band_top + " " + happy_d + " " + stars_top))

    # "OF JULY" Anton 30mm ≈ 101mm → left edge at (260-101)/2=79.5mm
    # cy=bot_start+bot_h*0.46=138+19.3=157.3mm → baseline=157.3+15=172.3mm, cap_top=146.5mm ✓
    band_bot = rrect(0, bot_start, W, bot_h, RX)
    ofjuly_d = hcenter("OF JULY", "anton", 30.0, W, bot_start + bot_h * 0.46)
    stars_bot = star(38.0, bot_start + bot_h * 0.46, 7.0) + " " + star(222.0, bot_start + bot_h * 0.46, 7.0)
    red_els.append(_p(band_bot + " " + ofjuly_d + " " + stars_bot))

    # BLUE: "4TH" Anton 84mm solid + corner stars + double border
    blue_els = []

    # "4TH" at 84mm ≈ 136mm wide → left edge at (260-136)/2=62mm
    # cy=CY_white=92mm → baseline=92+42=134mm, cap_top=134-72.1=61.9mm
    # zone top=46mm → gap 15.9mm ✓; zone bottom=138mm → gap 4mm ✓
    blue_els.append(_p(hcenter("4TH", "anton", 84.0, W, CY_white)))

    # Corner stars at upper corners of white zone (above "4TH" cap_top)
    # y=50: star bottom=58mm < cap_top(61.9mm) → 3.9mm gap ✓
    blue_els.append(_p(star(18.0, 50.0, 8.0)))
    blue_els.append(_p(star(242.0, 50.0, 8.0)))

    # Double border
    blue_els.append(_p(rrect(0, 0, W, H, RX) + " " + rrect(bw, bw, W-2*bw, H-2*bw, RX-bw)))

    return Sign("04_america250_happy_4th", W, H, [
        Layer("base", "WHITE", base),
        Layer("red", "RED", red_els),
        Layer("blue", "BLUE", blue_els),
    ])


def make_a250_land_free() -> Sign:
    """
    LAND OF THE FREE / HOME OF THE BRAVE — opening of the national anthem.
    Red top band / white "250" hero center / blue bottom band. Three-zone impact.
    280 × 185 mm
    """
    W, H, RX = 280.0, 185.0, 8.0
    bw = 2.5
    top_h = 60.0
    bot_h = 55.0
    bot_start = H - bot_h   # = 130mm; white zone y=60..130 (70mm)

    base = [_p(rrect(0, 0, W, H, RX))]

    # RED: top band "LAND OF THE FREE" carved + flanking stars + "250" hero in white zone
    red_els = []

    # "LAND OF THE FREE" Anton 18mm — wide phrase fills band
    # cy=top_h*0.44=26.4mm → baseline=35.4mm, cap_top=19.9mm ✓
    # Flanking stars clear of text (text ≈110mm wide, left edge ≈85mm; stars at x=52 and x=228) ✓
    band_top = rrect(0, 0, W, top_h, RX)
    lotf_d = hcenter("LAND OF THE FREE", "anton", 18.0, W, top_h * 0.44)
    stars_top = star(52.0, top_h * 0.44, 6.0) + " " + star(228.0, top_h * 0.44, 6.0)
    red_els.append(_p(band_top + " " + lotf_d + " " + stars_top))

    # "250" Anton 64mm — hero element in white zone
    # cy=92mm → baseline=124mm, cap_top=69.1mm; zone top=60mm → gap 9mm ✓; zone bot=130mm → gap 6mm ✓
    red_els.append(_p(hcenter("250", "anton", 64.0, W, 92.0)))

    # BLUE: bottom band "HOME OF THE BRAVE" carved + flanking stars + double border
    blue_els = []

    # "HOME OF THE BRAVE" Anton 18mm
    # cy=bot_start+bot_h*0.44=130+24.2=154.2mm → baseline=163.2mm, cap_top=147.7mm > 130mm ✓
    band_bot = rrect(0, bot_start, W, bot_h, RX)
    hotb_d = hcenter("HOME OF THE BRAVE", "anton", 18.0, W, bot_start + bot_h * 0.44)
    stars_bot = star(52.0, bot_start + bot_h * 0.44, 6.0) + " " + star(228.0, bot_start + bot_h * 0.44, 6.0)
    blue_els.append(_p(band_bot + " " + hotb_d + " " + stars_bot))

    # Double border
    blue_els.append(_p(rrect(0, 0, W, H, RX) + " " + rrect(bw, bw, W-2*bw, H-2*bw, RX-bw)))

    return Sign("05_america250_land_free", W, H, [
        Layer("base", "WHITE", base),
        Layer("red", "RED", red_els),
        Layer("blue", "BLUE", blue_els),
    ])


def make_a250_shield_badge() -> Sign:
    """
    Patriotic shield. Blue top: "AMERICA" + 7 stars carved white (even-odd).
    White zone: "250" red, sole hero — no vertical stripe crossing it.
    200 × 240 mm
    """
    W, H = 200.0, 240.0
    CX = W / 2

    def shield(x0, y0, w, h, tip_y=None) -> str:
        if tip_y is None:
            tip_y = y0 + h
        rx = w * 0.08
        x2 = x0 + w
        return (
            f"M{x0+rx:.2f},{y0:.2f}H{x2-rx:.2f}"
            f"Q{x2:.2f},{y0:.2f} {x2:.2f},{y0+rx:.2f}"
            f"V{y0+h*0.55:.2f}L{CX:.2f},{tip_y:.2f}L{x0:.2f},{y0+h*0.55:.2f}"
            f"V{y0+rx:.2f}Q{x0:.2f},{y0:.2f} {x0+rx:.2f},{y0:.2f}Z"
        )

    base = [_p(shield(0, 0, W, H))]

    # BLUE: top band with "AMERICA" + 7 stars all carved white via even-odd + shield border
    blue_els = []
    top_h = H * 0.40   # = 96mm

    blue_band = (f"M{W*0.08:.2f},{0:.2f}H{W-W*0.08:.2f}"
                 f"Q{W:.2f},{0:.2f} {W:.2f},{W*0.08:.2f}"
                 f"V{top_h:.2f}H{0:.2f}V{W*0.08:.2f}"
                 f"Q{0:.2f},{0:.2f} {W*0.08:.2f},{0:.2f}Z")

    # "AMERICA" — cy=top_h*0.28=26.9mm → baseline=37.8mm, cap_top=18.8mm ✓
    am_d = hcenter("AMERICA", "anton", 22.0, W, top_h * 0.28)

    # 7 stars carved into band — cy=top_h*0.70=67.2mm; gap from AMERICA baseline(37.8) = 23mm ✓
    stars_d = " ".join(
        star(W * 0.12 + i * (W * 0.76 / 6), top_h * 0.70, 6.5)
        for i in range(7)
    )
    blue_els.append(_p(blue_band + " " + am_d + " " + stars_d))

    # Shield border (even-odd outer+inner = frame)
    blue_els.append(_p(shield(0, 0, W, H) + " " + shield(5, 5, W-10, H-10, H-8)))

    # RED: "250" large + dates — no vertical stripe
    red_els = []

    # "250" 50mm — cy=top_h+(H-top_h)*0.35=146.4mm → baseline=171.4mm, cap_top=128.4mm > 96mm ✓
    # At baseline y=171.4: shield width = 200-2*(171.4-132)/108*100 = 127mm > "250"(86mm) ✓
    red_els.append(_p(hcenter("250", "anton", 50.0, W, top_h + (H - top_h) * 0.35)))

    # "1776 · 2026" 11mm — cy=top_h+(H-top_h)*0.60=182.4mm → baseline=187.9mm
    # shield width at y=187.9: 96.5mm > "1776·2026"(~66mm) ✓
    # gap from 250 baseline(171.4) to dates cap_top(178.4mm) = 7mm ✓
    red_els.append(_p(hcenter("1776  •  2026", "montserrat", 11.0, W, top_h + (H - top_h) * 0.60)))

    return Sign("06_america250_shield_badge", W, H, [
        Layer("base", "WHITE", base),
        Layer("blue", "BLUE", blue_els),
        Layer("red", "RED", red_els),
    ])



# ═══════════════════════════════════════════════════════════════════════════════
#  IMPROVED HOME / FARMHOUSE SIGNS
# ═══════════════════════════════════════════════════════════════════════════════

HOME_DIR = OUT_ROOT / "home_signs"
HOME_DIR.mkdir(parents=True, exist_ok=True)


def make_h_welcome_bold() -> Sign:
    """WELCOME — huge bold, double border, two stars."""
    W, H = 250.0, 90.0
    RX = 8.0

    base = [_p(rrect(0, 0, W, H, RX))]
    text_els = []

    # Double border
    text_els.append(_p(rrect(0, 0, W, H, RX) + " " + rrect(4, 4, W-8, H-8, RX-4)))

    # "WELCOME" Anton huge
    wsize = 42.0
    ww = measure("WELCOME", "anton", wsize)
    wx = (W - ww) / 2
    text_els.append(_p(text2path("WELCOME", "anton", wsize, wx, H/2 + wsize/2)))

    # Two flanking stars
    for sx in [wx - 18, wx + ww + 6]:
        text_els.append(_p(star(sx, H/2 + 3, 8.0)))

    return Sign("01_welcome_bold", W, H, [
        Layer("base", "CREAM", base),
        Layer("text", "BLACK", text_els),
    ])


def make_h_gather() -> Sign:
    """GATHER — single massive word, farmhouse minimal."""
    W, H = 220.0, 75.0

    base = [_p(rrect(0, 0, W, H, 0))]
    text_els = []

    # Top & bottom thick bars
    bar_t = 3.5
    text_els.append(_p(rrect(0, 0, W, bar_t)))
    text_els.append(_p(rrect(0, H - bar_t, W, bar_t)))
    # Thin inner lines
    text_els.append(_p(rrect(0, 8, W, 1.5)))
    text_els.append(_p(rrect(0, H-9.5, W, 1.5)))

    # "GATHER" Anton very large
    gsize = 42.0
    text_els.append(_p(hcenter("GATHER", "anton", gsize, W, H/2)))

    return Sign("02_gather", W, H, [
        Layer("base", "CREAM", base),
        Layer("text", "BLACK", text_els),
    ])


def make_h_family_name() -> Sign:
    """Family name plate — [FAMILY NAME] / EST. YEAR — modern."""
    W, H = 240.0, 85.0
    RX = 6.0

    base = [_p(rrect(0, 0, W, H, RX))]
    text_els = []

    # Single solid border
    text_els.append(_p(rrect(0, 0, W, H, RX) + " " + rrect(4, 4, W-8, H-8, RX-4)))

    # Family name large
    name_size = 34.0
    text_els.append(_p(hcenter("YOUR NAME FAMILY", "anton", name_size, W, H * 0.44)))

    # Divider: line + diamonds + line
    div_y = H * 0.60
    text_els.append(_p(rrect(W*0.08, div_y, W*0.35, 2.0)))
    text_els.append(_p(rrect(W*0.57, div_y, W*0.35, 2.0)))
    for dx in [-12, 0, 12]:
        text_els.append(_p(star(W/2 + dx, div_y + 1, 4.5, 2.0)))

    # Est. year
    est_size = 14.0
    text_els.append(_p(hcenter("EST.  2024", "montserrat", est_size, W, H * 0.82)))

    return Sign("03_family_name", W, H, [
        Layer("base", "CREAM", base),
        Layer("text", "BLACK", text_els),
    ])


def make_h_blessed() -> Sign:
    """BLESSED — circular badge, bold cross accent, navy + cream."""
    W = H = 200.0
    CX, CY = W/2, H/2
    R = 96.0

    base = [_p(circle(CX, CY, R))]

    # NAVY layer: thick ring border + star ring
    navy_els = []
    navy_els.append(_p(ring(CX, CY, R, R - 13)))
    navy_els.append(_p(star_ring(12, CX, CY, R - 7, 5.0)))

    # Cross accent above text
    cross_cx, cross_cy = CX, CY * 0.50
    arm_w = 5.5
    navy_els.append(_p(rrect(cross_cx - arm_w/2, cross_cy - 14, arm_w, 28)))   # vertical
    navy_els.append(_p(rrect(cross_cx - 14, cross_cy - arm_w/2, 28, arm_w)))   # horizontal

    # Text
    text_els = []
    bsize = 40.0
    text_els.append(_p(hcenter("BLESSED", "anton", bsize, W, CY + 16)))

    return Sign("04_blessed_circle", W, H, [
        Layer("base", "CREAM", base),
        Layer("navy", "NAVY", navy_els),
        Layer("text", "BLACK", text_els),
    ])


def make_h_game_room() -> Sign:
    """GAME ROOM — dark base with bright star/starburst accents."""
    W, H = 220.0, 90.0
    RX = 8.0

    base = [_p(rrect(0, 0, W, H, RX))]

    # YELLOW: starburst accents + "ROOM" text
    yellow_els = []
    # Two starburst decorations
    for (sx, sy) in [(H*0.5, H/2), (W-H*0.5, H/2)]:
        yellow_els.append(_p(starburst(sx, sy, H*0.38, H*0.24, 12)))
    # "ROOM" smaller below
    room_size = 22.0
    yellow_els.append(_p(hcenter("ROOM", "anton", room_size, W, H*0.76)))

    # RED: "GAME" large top
    red_els = []
    game_size = 36.0
    red_els.append(_p(hcenter("GAME", "anton", game_size, W, H*0.48)))

    # Double border
    red_els.append(_p(rrect(0, 0, W, H, RX) + " " + rrect(4, 4, W-8, H-8, RX-4)))

    return Sign("05_game_room", W, H, [
        Layer("base", "BLACK", base),
        Layer("yellow", "YELLOW", yellow_els),
        Layer("red", "RED", red_els),
    ])


def make_h_laundry_rules() -> Sign:
    """LAUNDRY ROOM / WASH DRY FOLD REPEAT — two-line with accents."""
    W, H = 250.0, 85.0
    RX = 6.0

    base = [_p(rrect(0, 0, W, H, RX))]
    text_els = []

    # Border
    text_els.append(_p(rrect(0, 0, W, H, RX) + " " + rrect(3.5, 3.5, W-7, H-7, RX-3.5)))

    # "LAUNDRY ROOM" Anton large
    lr_size = 30.0
    text_els.append(_p(hcenter("LAUNDRY ROOM", "anton", lr_size, W, H*0.40)))

    # Divider with 3 stars
    div_y = H * 0.58
    text_els.append(_p(rrect(W*0.06, div_y, W*0.33, 2.0)))
    text_els.append(_p(rrect(W*0.61, div_y, W*0.33, 2.0)))
    for dx in [-9, 0, 9]:
        text_els.append(_p(star(W/2 + dx, div_y + 1, 4.0, 1.8)))

    # "WASH · DRY · FOLD · REPEAT" subtext
    sub_size = 12.0
    text_els.append(_p(hcenter("WASH · DRY · FOLD · REPEAT",
                               "montserrat", sub_size, W, H*0.80)))

    return Sign("06_laundry_rules", W, H, [
        Layer("base", "CREAM", base),
        Layer("text", "BLACK", text_els),
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    signs = [
        # America 250 package
        (A250_DIR, make_a250_america_bold),
        (A250_DIR, make_a250_star_badge),
        (A250_DIR, make_a250_freedom_sign),
        (A250_DIR, make_a250_happy_4th),
        (A250_DIR, make_a250_land_free),
        (A250_DIR, make_a250_shield_badge),
        # Home signs
        (HOME_DIR, make_h_welcome_bold),
        (HOME_DIR, make_h_gather),
        (HOME_DIR, make_h_family_name),
        (HOME_DIR, make_h_blessed),
        (HOME_DIR, make_h_game_room),
        (HOME_DIR, make_h_laundry_rules),
    ]

    print(f"Generating {len(signs)} multi-layer 3D print sign packages")
    print("=" * 60)
    ok = 0
    for parent_dir, fn in signs:
        try:
            sign = fn()
            out = sign.save(parent_dir)
            layer_files = list(out.glob("layer*.svg"))
            preview = out / "preview.jpg"
            print(f"  ✓  {sign.slug}  {sign.w:.0f}×{sign.h:.0f}mm  "
                  f"{len(layer_files)} layers  "
                  f"{'preview OK' if preview.exists() else 'no preview'}")
            ok += 1
        except Exception as e:
            import traceback
            print(f"  ✗  {fn.__name__}: {e}")
            traceback.print_exc()

    print("=" * 60)
    print(f"Generated {ok}/{len(signs)} sign packages")
    print(f"\nOutput folders:")
    print(f"  America 250: {A250_DIR}")
    print(f"  Home signs:  {HOME_DIR}")
    print("\nPrinting instructions per layer:")
    print("  Import each layer_NN_*.svg into Bambu Studio as a separate Part")
    print("  Set base layer height: 3mm")
    print("  Set raised layers height: 2mm, Z-offset: 3mm")
    print("  Assign each Part to an AMS color slot matching the _COLOR suffix")


if __name__ == "__main__":
    main()
