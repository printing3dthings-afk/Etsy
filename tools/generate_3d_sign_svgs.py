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
    "montserrat": "/usr/local/share/fonts/Montserrat-Bold.ttf",
    "bebas":      "/usr/local/share/fonts/BebasNeue-Regular.ttf",
    "cinzel":     "/usr/local/share/fonts/Cinzel-Regular.ttf",
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


def make_a250_flag_plaque() -> Sign:
    """
    US-flag inspired horizontal plaque.
    White base / Red stripes + AMERICA / Blue canton + stars + 250 YEARS + dates
    Size: 260×190mm
    """
    W, H = 260.0, 190.0
    RX = 10.0

    # ── Layer 1: White base plate ─────────────────────────────────────────────
    base = [_p(rrect(0, 0, W, H, RX))]

    # ── Layer 2: RED — flag stripes + "AMERICA" text ──────────────────────────
    red_els = []
    canton_w = W * 0.40   # 104mm
    canton_h = H * 0.58   # ~110mm — covers top 4 stripes

    # 7 horizontal stripes (alt red/white), each H/7 ≈ 27mm
    stripe_h = H / 7
    red_stripe_rows = [0, 2, 4, 6]
    for row in red_stripe_rows:
        sy = row * stripe_h
        sw = W if row >= 4 else W  # full width for bottom 3 red, full for bottom red
        sx = 0
        if row < 4:
            # Top stripes: canton covers left portion — skip the canton area
            sx = canton_w
            sw = W - canton_w
        # Use rrect for the stripe, with rx only on rightmost stripe ends
        red_els.append(_p(f"M{sx:.2f},{sy:.2f}H{W:.2f}V{sy+stripe_h:.2f}H{sx:.2f}Z"))

    # "AMERICA" Anton bold — big, centered in lower half below canton
    america_size = 44.0
    america_w = measure("AMERICA", "anton", america_size)
    # Center in full width, place in lower portion
    america_x = (W - america_w) / 2
    america_y_center = canton_h + (H - canton_h) * 0.48
    red_els.append(_p(text2path("AMERICA", "anton", america_size, america_x, america_y_center + america_size / 2)))

    # ── Layer 3: BLUE — canton + stars + text ─────────────────────────────────
    blue_els = []

    # Canton rectangle (top-left) — even-odd with stars inside to punch them out
    # Instead of punch-out, we do solid canton then add white stars on top...
    # For multi-color print: canton = blue solid, stars will be WHITE stars on canton
    # We use even-odd to carve stars from canton = white stars appear through to white base
    canton_paths = rrect(0, 0, canton_w, canton_h, RX)
    # Stars in canton: 5 rows of 5 stars (simplified, large)
    star_r = 4.5
    star_rows = 5
    star_cols = 5
    for row in range(star_rows):
        n = star_cols if row % 2 == 0 else star_cols - 1
        offset = (canton_w / star_cols) / 2
        for col in range(n):
            extra_off = 0 if row % 2 == 0 else (canton_w / star_cols) / 2
            scx = extra_off + col * (canton_w / star_cols) + offset
            scy = (row + 0.5) * (canton_h / star_rows)
            canton_paths += " " + star(scx, scy, star_r)
    blue_els.append(_p(canton_paths))

    # "250 YEARS" text centered horizontally, in upper middle area
    y250_size = 30.0
    y250_text = "250 YEARS"
    y250_w = measure(y250_text, "anton", y250_size)
    # Place it to the right of the canton, centered in remaining width
    right_x = canton_w
    right_w = W - canton_w
    y250_x = canton_w + (right_w - y250_w) / 2
    y250_cy = canton_h * 0.42
    blue_els.append(_p(text2path(y250_text, "anton", y250_size, y250_x, y250_cy + y250_size / 2)))

    # "1776  ★  2026" centered full width, below AMERICA
    dates_size = 16.0
    dates_text = "1776  ★  2026"
    dates_d = hcenter(dates_text, "montserrat", dates_size, W, H * 0.86)
    blue_els.append(_p(dates_d))

    # Thin border around entire sign
    border_t = 2.0
    border_d = (rrect(0, 0, W, H, RX) + " " +
                rrect(border_t, border_t, W - 2*border_t, H - 2*border_t, RX - border_t))
    blue_els.append(_p(border_d))

    return Sign("01_america250_flag_plaque", W, H, [
        Layer("base", "WHITE", base),
        Layer("red", "RED", red_els),
        Layer("blue", "BLUE", blue_els),
    ])


def make_a250_star_badge() -> Sign:
    """
    Circular badge — "AMERICA" top, huge "250" center, stars ring, dates.
    Size: 220×220mm (circle)
    """
    W = H = 220.0
    CX, CY = W / 2, H / 2
    R_OUTER = 107.0

    # ── Layer 1: White circle base ────────────────────────────────────────────
    base = [_p(circle(CX, CY, R_OUTER))]

    # ── Layer 2: RED — large "250", decorative ring, two horizontal bars ──────
    red_els = []

    # Large "250" centered — extremely bold
    big_size = 68.0
    big_w = measure("250", "anton", big_size)
    big_x = (W - big_w) / 2
    big_cy = CY + 8
    red_els.append(_p(text2path("250", "anton", big_size, big_x, big_cy + big_size / 2)))

    # Two horizontal bars top and bottom of "250"
    bar_t = 3.5
    bar_margin = 20
    red_els.append(_p(rrect(bar_margin, big_cy - 12, W - 2*bar_margin, bar_t)))
    red_els.append(_p(rrect(bar_margin, big_cy + big_size + 4, W - 2*bar_margin, bar_t)))

    # ── Layer 3: BLUE — "AMERICA", star ring, "1776 · 2026", outer ring ──────
    blue_els = []

    # Outer ring border
    blue_els.append(_p(ring(CX, CY, R_OUTER, R_OUTER - 5.0)))

    # "AMERICA" bold, centered, above the bars
    am_size = 26.0
    am_d = hcenter("AMERICA", "anton", am_size, W, CY - big_size * 0.68)
    blue_els.append(_p(am_d))

    # Star ring (13 stars — one per original colony)
    sring_d = star_ring(13, CX, CY, R_OUTER - 14, 5.0)
    blue_els.append(_p(sring_d))

    # "1776  ·  2026" below the bars
    dates_size = 15.0
    dates_d = hcenter("1776  •  2026", "montserrat", dates_size, W,
                      big_cy + big_size + 18)
    blue_els.append(_p(dates_d))

    # "YEARS OF FREEDOM" small subtitle between stars ring and bars
    sub_size = 11.0
    sub_d = hcenter("YEARS OF FREEDOM", "montserrat", sub_size, W, big_cy - 22)
    blue_els.append(_p(sub_d))

    return Sign("02_america250_star_badge", W, H, [
        Layer("base", "WHITE", base),
        Layer("red", "RED", red_els),
        Layer("blue", "BLUE", blue_els),
    ])


def make_a250_freedom_sign() -> Sign:
    """
    Bold horizontal sign: FREEDOM / AMERICA / 1776-2026 with star accents.
    Size: 280×110mm
    """
    W, H = 280.0, 110.0
    RX = 8.0

    base = [_p(rrect(0, 0, W, H, RX))]

    # RED: "FREEDOM" massive + two flanking stars
    red_els = []
    freedom_size = 46.0
    freedom_d = hcenter("FREEDOM", "anton", freedom_size, W, H * 0.50)
    red_els.append(_p(freedom_d))

    # Two large stars flanking (left and right of FREEDOM text)
    freedom_w = measure("FREEDOM", "anton", freedom_size)
    left_x = (W - freedom_w) / 2 - 22
    right_x = (W + freedom_w) / 2 + 10
    for sx in [left_x, right_x]:
        red_els.append(_p(star(sx, H / 2 + freedom_size * 0.1, 8.5)))

    # BLUE: "AMERICA" subtitle, dates, double border, top star row
    blue_els = []

    # Double border
    bw = 2.5
    blue_els.append(_p(rrect(0, 0, W, H, RX) + " " +
                       rrect(bw, bw, W-2*bw, H-2*bw, RX-bw)))

    # "AMERICA" smaller, above FREEDOM
    am_size = 18.0
    am_d = hcenter("AMERICA", "montserrat", am_size, W, H * 0.17)
    blue_els.append(_p(am_d))

    # Thin divider line under AMERICA
    div_y = H * 0.29
    blue_els.append(_p(rrect(W*0.1, div_y, W*0.8, 1.8)))

    # "1776  ★  2026" below FREEDOM
    dates_size = 14.0
    dates_d = hcenter("1776  ★  2026", "montserrat", dates_size, W, H * 0.86)
    blue_els.append(_p(dates_d))

    return Sign("03_america250_freedom_sign", W, H, [
        Layer("base", "WHITE", base),
        Layer("red", "RED", red_els),
        Layer("blue", "BLUE", blue_els),
    ])


def make_a250_welcome_patriotic() -> Sign:
    """
    Round door hanger — WELCOME center, star ring border, patriotic colors.
    Size: 210×240mm (circle 200mm + 40mm hanger slot at top)
    """
    W = 210.0
    H = 245.0
    CX = W / 2
    R = 100.0
    CY = H - R - 5  # circle centered in lower portion

    # Layer 1: WHITE — circle + hanger
    base = []
    base.append(_p(circle(CX, CY, R)))
    # Oval hanger slot
    slot_w, slot_h = 22.0, 30.0
    slot_cx = CX
    slot_cy = CY - R - slot_h / 2 + 2
    base.append(_p(rrect(slot_cx - slot_w/2, slot_cy - slot_h/2, slot_w, slot_h, slot_w/2)))

    # Layer 2: BLUE — outer ring border + star ring + "WELCOME" arc band background
    blue_els = []
    # Outer ring (thick border)
    blue_els.append(_p(ring(CX, CY, R, R - 12)))
    # Star ring (inside the border band)
    sring_d = star_ring(16, CX, CY, R - 6, 4.5)
    blue_els.append(_p(sring_d))
    # Bottom star row strip (bottom 20% of circle)
    strip_y = CY + R * 0.60
    strip_h = R * 0.40
    # Clipped blue strip at bottom — arc chord shape approximated as rect
    strip_path = f"M{CX-R*0.85:.2f},{strip_y:.2f}H{CX+R*0.85:.2f}V{strip_y+strip_h:.2f}H{CX-R*0.85:.2f}Z"
    blue_els.append(_p(strip_path))
    # Small stars on strip
    for i in range(9):
        scx = CX - R*0.8 + i * (R*1.6/8)
        scy = strip_y + strip_h * 0.5
        blue_els.append(_p(star(scx, scy, 4.0)))

    # Layer 3: RED — "WELCOME" large text
    red_els = []
    welcome_size = 28.0
    ww = measure("WELCOME", "anton", welcome_size)
    wx = (W - ww) / 2
    wcy = CY - R * 0.05
    red_els.append(_p(text2path("WELCOME", "anton", welcome_size, wx, wcy + welcome_size / 2)))

    # "HOME" smaller below
    home_size = 18.0
    home_d = hcenter("HOME", "anton", home_size, W, CY + R * 0.25)
    red_els.append(_p(home_d))

    return Sign("04_america250_welcome_patriotic", W, H, [
        Layer("base", "WHITE", base),
        Layer("blue", "BLUE", blue_els),
        Layer("red", "RED", red_els),
    ])


def make_a250_happy_4th() -> Sign:
    """
    Happy 4th of July — bold festive sign, rounded rect with fireworks.
    Size: 250×200mm
    """
    W, H = 250.0, 200.0
    RX = 15.0

    # WHITE base
    base = [_p(rrect(0, 0, W, H, RX))]

    # RED: "HAPPY" in arch banner top + "of JULY" bold bottom + firework bursts
    red_els = []

    # "HAPPY" arch banner
    banner_w = W * 0.65
    banner_h = 35.0
    banner_y = 10.0
    red_els.append(_p(banner_arch(W/2, banner_y, banner_w, banner_h)))

    # "HAPPY" in white-on-red — actually for 3D print, we skip reversed text
    # Instead: "HAPPY" is the band itself, text carved from it via evenodd
    happy_size = 24.0
    happy_w = measure("HAPPY", "anton", happy_size)
    happy_d = (banner_arch(W/2, banner_y, banner_w, banner_h) + " " +
               text2path("HAPPY", "anton", happy_size,
                        (W - happy_w)/2, banner_y + banner_h*0.5 + happy_size/2))
    red_els.append(_p(happy_d))

    # Large "JULY" at bottom
    july_size = 38.0
    july_d = hcenter("JULY", "anton", july_size, W, H * 0.80)
    red_els.append(_p(july_d))

    # Firework bursts — 4 of them in corners area
    for (fx, fy, fr) in [(45, 100, 18), (205, 95, 15), (30, 155, 12), (220, 158, 14)]:
        red_els.append(_p(firework(fx, fy, fr, fr*0.45, 8)))

    # BLUE: "4TH" enormous + stars
    blue_els = []

    # "4" huge
    big4_size = 72.0
    big4_w = measure("4", "anton", big4_size)
    big4_x = W/2 - big4_w * 0.9
    big4_y = H * 0.52
    blue_els.append(_p(text2path("4", "anton", big4_size, big4_x, big4_y + big4_size / 2)))

    # "TH" superscript beside "4"
    th_size = 28.0
    th_x = W/2 + big4_w * 0.1
    th_y = big4_y
    blue_els.append(_p(text2path("TH", "anton", th_size, th_x, th_y + th_size / 2)))

    # "of" small script-style using montserrat italic-ish
    of_size = 22.0
    of_x = th_x + measure("TH", "anton", th_size) + 4
    of_y = H * 0.57
    blue_els.append(_p(text2path("of", "montserrat", of_size, of_x, of_y + of_size / 2)))

    # Stars sprinkled around
    for (sx, sy, sr) in [(18,50,7),(230,45,8),(25,180,6),(238,180,7),(125,175,5),(125,55,6)]:
        blue_els.append(_p(star(sx, sy, sr)))

    # Outer border
    blue_els.append(_p(rrect(0, 0, W, H, RX) + " " +
                       rrect(3, 3, W-6, H-6, RX-3)))

    return Sign("05_america250_happy_4th", W, H, [
        Layer("base", "WHITE", base),
        Layer("red", "RED", red_els),
        Layer("blue", "BLUE", blue_els),
    ])


def make_a250_shield_badge() -> Sign:
    """
    Patriotic shield/crest badge shape.
    Size: 200×240mm
    """
    W, H = 200.0, 240.0
    CX = W / 2

    def shield(x0, y0, w, h, tip_y=None) -> str:
        """Shield shape: flat top, angled sides, point at bottom."""
        if tip_y is None:
            tip_y = y0 + h
        rx = w * 0.08
        x1, x2 = x0, x0 + w
        return (
            f"M{x0+rx:.2f},{y0:.2f}H{x2-rx:.2f}"
            f"Q{x2:.2f},{y0:.2f} {x2:.2f},{y0+rx:.2f}"
            f"V{y0+h*0.55:.2f}L{CX:.2f},{tip_y:.2f}L{x0:.2f},{y0+h*0.55:.2f}"
            f"V{y0+rx:.2f}Q{x0:.2f},{y0:.2f} {x0+rx:.2f},{y0:.2f}Z"
        )

    # WHITE: full shield
    base = [_p(shield(0, 0, W, H))]

    # BLUE: upper half + star ring + "USA" + outer shield border
    blue_els = []

    # Top blue band (upper 40% of shield)
    top_h = H * 0.38
    blue_band = (f"M{0+W*0.08:.2f},{0:.2f}H{W-W*0.08:.2f}"
                 f"Q{W:.2f},{0:.2f} {W:.2f},{0+W*0.08:.2f}"
                 f"V{top_h:.2f}H{0:.2f}V{0+W*0.08:.2f}"
                 f"Q{0:.2f},{0:.2f} {0+W*0.08:.2f},{0:.2f}Z")
    blue_els.append(_p(blue_band))

    # Stars on blue band
    for i in range(7):
        scx = W * 0.12 + i * (W * 0.76 / 6)
        scy = top_h * 0.48
        blue_els.append(_p(star(scx, scy, 6.5)))

    # "USA" centered in middle zone
    usa_size = 40.0
    usa_d = hcenter("USA", "anton", usa_size, W, H * 0.58)
    blue_els.append(_p(usa_d))

    # Outer shield border (thick)
    outer = shield(0, 0, W, H)
    inner = shield(5, 5, W-10, H-10, H-8)
    blue_els.append(_p(outer + " " + inner))

    # RED: center vertical stripe + "250" + date strip
    red_els = []

    # Vertical center stripe (classic shield tricolor divider)
    stripe_w = W * 0.22
    red_els.append(_p(rrect(CX - stripe_w/2, top_h, stripe_w, H*0.30)))

    # "250" large, on white bands beside vertical stripe
    n250_size = 28.0
    n250_d = hcenter("250", "anton", n250_size, W, H * 0.54)
    red_els.append(_p(n250_d))

    # "1776 · 2026" at bottom of shield
    dates_size = 13.0
    dates_d = hcenter("1776  •  2026", "montserrat", dates_size, W, H * 0.85)
    red_els.append(_p(dates_d))

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
        (A250_DIR, make_a250_flag_plaque),
        (A250_DIR, make_a250_star_badge),
        (A250_DIR, make_a250_freedom_sign),
        (A250_DIR, make_a250_welcome_patriotic),
        (A250_DIR, make_a250_happy_4th),
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
