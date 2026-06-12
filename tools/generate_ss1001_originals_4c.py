#!/usr/bin/env python3
"""
Rebuild the original 5 SS1001 AI concepts as clean 4-color programmatic SVGs.

4 colors:
  Cream — base plate (background, 0–4 mm)
  Navy  — raised elements (4–6 mm)
  Red   — raised elements (4–6 mm)
  Gold  — raised elements (4–6 mm)

All three raised layers must occupy non-overlapping XY footprints.

Output folders (data/3d_print_signs/america_250/):
  07_america250_banner_4c    AMERICA 250 banner  (navy base)
  08_america250_burst_4c     Art-deco sunburst   (cream base)
  09_america250_seal_4c      Circular seal       (cream base)
  10_america250_shield_4c    Shield / eagle      (navy base)
  11_america250_stamp_4c     Liberty stamp       (cream base)

Run: python tools/generate_ss1001_originals_4c.py
"""

from __future__ import annotations
import io
import math
import re
from pathlib import Path

import cairosvg
from PIL import Image

ROOT       = Path(__file__).parent.parent
DESIGNS_DIR = ROOT / "data" / "3d_print_signs" / "america_250"

DESIGNS = [
    ("07_america250_banner_4c",  "America 250 Banner"),
    ("08_america250_burst_4c",   "America 250 Burst"),
    ("09_america250_seal_4c",    "America 250 Seal"),
    ("10_america250_shield_4c",  "America 250 Shield"),
    ("11_america250_stamp_4c",   "America 250 Stamp"),
]

# ── SVG helpers ──────────────────────────────────────────────────────────────

ANTON = "Anton, Impact, 'Arial Black', sans-serif"
MONT  = "Montserrat, 'Arial', sans-serif"

def doc(w: float, h: float, *els: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">\n'
        + "".join(els)
        + "</svg>\n"
    )

def R(x, y, w, h, rx=0) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="black"/>\n'

def C(cx, cy, r) -> str:
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="black"/>\n'

def P(d: str, fr: str = "") -> str:
    fr_a = f' fill-rule="{fr}"' if fr else ""
    return f'<path d="{d}" fill="black"{fr_a}/>\n'

def T(x, y, fs, text, fam=ANTON, anc="middle", fw="") -> str:
    fw_a = f' font-weight="{fw}"' if fw else ""
    return (
        f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{fs}"{fw_a}'
        f' text-anchor="{anc}" dominant-baseline="central" fill="black">'
        f'{text}</text>\n'
    )

def TM(x, y, fs, text, anc="middle") -> str:
    return T(x, y, fs, text, fam=MONT, anc=anc, fw="900")

def star(cx, cy, ro, ri=None, n=5, rot=-90) -> str:
    ri = ri if ri is not None else ro * 0.40
    pts = []
    for i in range(2 * n):
        a = math.radians(rot + 180 * i / n)
        r = ro if i % 2 == 0 else ri
        pts.append(f"{cx + r*math.cos(a):.2f},{cy + r*math.sin(a):.2f}")
    return P("M" + "L".join(pts) + "Z")

def ring(cx, cy, ro, ri) -> str:
    """Annulus (ring) via even-odd fill rule."""
    def cpth(r):
        return (
            f"M{cx - r:.2f},{cy:.2f} "
            f"A{r:.2f},{r:.2f} 0 1,1 {cx + r:.2f},{cy:.2f} "
            f"A{r:.2f},{r:.2f} 0 1,1 {cx - r:.2f},{cy:.2f} Z"
        )
    return P(cpth(ro) + " " + cpth(ri), fr="evenodd")

def pie(cx, cy, r, a1_deg, a2_deg) -> str:
    """Filled pie slice."""
    a1, a2 = math.radians(a1_deg), math.radians(a2_deg)
    x1 = cx + r * math.cos(a1);  y1 = cy + r * math.sin(a1)
    x2 = cx + r * math.cos(a2);  y2 = cy + r * math.sin(a2)
    large = 1 if (a2_deg - a1_deg) % 360 > 180 else 0
    return P(
        f"M{cx:.2f},{cy:.2f} L{x1:.2f},{y1:.2f} "
        f"A{r:.2f},{r:.2f} 0 {large},1 {x2:.2f},{y2:.2f} Z"
    )

def annular_pie(cx: float, cy: float, r_in: float, r_out: float,
                a1_deg: float, a2_deg: float) -> str:
    """Filled donut-sector from r_in to r_out, angle a1..a2 degrees (clockwise)."""
    a1, a2 = math.radians(a1_deg), math.radians(a2_deg)
    da = abs(a2_deg - a1_deg)
    large = 1 if da >= 180 else 0
    ox1 = cx + r_out * math.cos(a1);  oy1 = cy + r_out * math.sin(a1)
    ox2 = cx + r_out * math.cos(a2);  oy2 = cy + r_out * math.sin(a2)
    ix1 = cx + r_in  * math.cos(a1);  iy1 = cy + r_in  * math.sin(a1)
    ix2 = cx + r_in  * math.cos(a2);  iy2 = cy + r_in  * math.sin(a2)
    d = (f"M{ox1:.2f},{oy1:.2f} A{r_out:.1f},{r_out:.1f} 0 {large},1 {ox2:.2f},{oy2:.2f} "
         f"L{ix2:.2f},{iy2:.2f} A{r_in:.1f},{r_in:.1f} 0 {large},0 {ix1:.2f},{iy1:.2f} Z")
    return P(d)


# ── Design 07 — America 250 Banner ──────────────────────────────────────────
# Navy base (dark background).
# GOLD: border frame, "AMERICA", divider rules, stars, footer text.
# RED:  top band, bottom band, two thin horizontal ribbons.
# CREAM: "250", "1776 · 2026"  (sits between the red ribbons — no overlap).

def banner() -> list[tuple[str, str]]:
    # Matches the original "Main" AI design:
    #   NAVY base, GOLD "AMERICA" (prominent, at top), CREAM huge "250" (center),
    #   RED accent bands + "1776 – 2026" dates.
    # Zone layout prevents cross-layer XY overlap:
    #   GOLD:  "AMERICA" Y=30–62, border frame edges, 5 stars Y=148–168
    #   CREAM: "250"     Y=80–150
    #   RED:   top band Y=0–22, bottom band Y=178–200, ribbon Y=63–72, dates Y=155–170
    W, H = 280, 200

    base = doc(W, H, R(0, 0, W, H, rx=8))

    # GOLD: thin border frame + large "AMERICA" + 5 corner/flanking stars
    gold = doc(W, H,
        P(f"M5,5 H{W-5} V{H-5} H5 Z  M9,9 H{W-9} V{H-9} H9 Z", fr="evenodd"),
        T(W/2, 47, 44, "AMERICA"),      # Y=25-69  (zone 25–69)
        # 5 evenly spaced stars below "AMERICA" text and above cream zone
        *[star(28 + 56*i, 158, 7, 3, 5) for i in range(5)],
    )

    # RED: top band (Y=0–22), thin accent ribbon (Y=63–72), dates (Y=155-168), bottom band
    # Dates (Y=155–168) are below CREAM zone (Y=80–150) — gap = 5px ✓
    red = doc(W, H,
        R(0,   0, W, 22, rx=8),       # top band
        R(0,  63, W,  9),             # accent ribbon between "AMERICA" and "250"
        TM(W/2, 155, 15, "1776  –  2026"),   # Y=148-163 — below CREAM (150) by gap
        R(0, 178, W, 22, rx=8),       # bottom band
    )

    # CREAM: large "250" center — Y=80–150 (font_size=72, height≈50px, centered at Y=105)
    cream = doc(W, H,
        T(W/2, 105, 72, "250"),
    )

    return [
        ("layer01_base_NAVY.svg",   base),
        ("layer02_gold_GOLD.svg",   gold),
        ("layer03_red_RED.svg",     red),
        ("layer04_cream_CREAM.svg", cream),
    ]


# ── Design 08 — America 250 Burst (Artdeco) ─────────────────────────────────
# Matches the original "Artdeco" AI design:
#   NAVY base disc (dark background).
#   GOLD: 16 annular sunburst rays from inner_r to outer_r.
#   CREAM: "AMERICA" + large "250" in the inner circle zone.
#   RED: "1776 · 2026" dates at the bottom of the inner zone.
# Non-overlapping: all CREAM/RED text is within inner_r; GOLD rays are annular (outside inner_r).

def burst() -> list[tuple[str, str]]:
    W, H    = 260, 260
    cx, cy  = 130, 130
    r_in    = 62           # inner text circle: all text pixels must be within this radius
    r_out   = 122          # outer edge of sunburst rays
    N_RAYS  = 16
    step    = 360 / N_RAYS
    gap     = 1.8          # degrees of gap between each ray

    # NAVY base: full disc
    base = doc(W, H,
        P(f"M{cx-r_out:.1f},{cy:.1f} "
          f"A{r_out},{r_out} 0 1,1 {cx+r_out:.1f},{cy:.1f} "
          f"A{r_out},{r_out} 0 1,1 {cx-r_out:.1f},{cy:.1f} Z"),
    )

    # GOLD: 16 annular ray slices (r_in → r_out), slightly gapped for crispness
    gold_els = []
    for i in range(N_RAYS):
        center_a = i * step - 90      # offset so first ray points up
        a1 = center_a - (step - gap) / 2
        a2 = center_a + (step - gap) / 2
        gold_els.append(annular_pie(cx, cy, r_in, r_out, a1, a2))
    gold = doc(W, H, *gold_els)

    # CREAM: "AMERICA" at top of inner zone + large "250" at center
    # Zone layout (all within r_in=62 from center):
    #   "AMERICA" font_size=12 at Y=93  → bbox Y=87-99,  X≈100-160 (r_max≈55 ✓)
    #   "250"     font_size=42 at Y=130 → bbox Y=109-151, X≈88-172 (r_max≈52 ✓)
    cream = doc(W, H,
        T(cx, cy - 37, 12, "AMERICA"),
        T(cx, cy,       42, "250"),
    )

    # RED: "1776 · 2026" at bottom of inner zone
    # Y=168 → bbox Y=162-174, X≈95-165 (r_max≈59 ✓)
    red = doc(W, H,
        TM(cx, cy + 38, 11, "1776  ·  2026"),
    )

    return [
        ("layer01_base_NAVY.svg",   base),
        ("layer02_gold_GOLD.svg",   gold),
        ("layer03_cream_CREAM.svg", cream),
        ("layer04_red_RED.svg",     red),
    ]


# ── Design 09 — America 250 Seal ────────────────────────────────────────────
# Cream disc base.
# NAVY: outer ring + 13 stars in ring.
# RED: "AMERICA" text + two thin rule lines.
# GOLD: "250" (large) + "1776 · 2026".
# All text inside the cream inner circle — no overlap with navy ring.

def seal() -> list[tuple[str, str]]:
    W, H = 230, 230
    cx, cy = 115, 115
    r_disc  = 112    # full disc
    r_ring_o = 110   # outer edge of navy ring
    r_ring_i = 86    # inner edge of navy ring
    r_star   = 98    # star orbit in navy ring

    # Cream base: full disc
    base = doc(W, H,
        P(f"M{cx - r_disc:.1f},{cy:.1f} "
          f"A{r_disc},{r_disc} 0 1,1 {cx + r_disc:.1f},{cy:.1f} "
          f"A{r_disc},{r_disc} 0 1,1 {cx - r_disc:.1f},{cy:.1f} Z")
    )

    # Navy: outer ring + 13 stars evenly spaced in it
    navy_els = [ring(cx, cy, r_ring_o, r_ring_i)]
    for i in range(13):
        a = math.radians(-90 + i * 360 / 13)
        sx, sy = cx + r_star * math.cos(a), cy + r_star * math.sin(a)
        navy_els.append(star(sx, sy, 5, 2, 5))
    navy = doc(W, H, *navy_els)

    # Red: "AMERICA" + thin rule lines (zone Y ≈ 76–96, clear of gold below)
    red = doc(W, H,
        R(cx - 60, cy - 38, 120, 2),   # rule line above AMERICA
        T(cx, cy - 26, 20, "AMERICA"),
        R(cx - 60, cy - 14, 120, 2),   # rule below AMERICA / above 250
    )

    # Gold: "250" (zone Y ≈ cy–cy+32) + dates below
    gold = doc(W, H,
        T(cx, cy + 16, 46, "250"),
        R(cx - 55, cy + 42, 110, 2),   # rule between 250 and dates
        TM(cx, cy + 54, 13, "1776  ·  2026"),
    )

    return [
        ("layer01_base_CREAM.svg", base),
        ("layer02_navy_NAVY.svg",  navy),
        ("layer03_red_RED.svg",    red),
        ("layer04_gold_GOLD.svg",  gold),
    ]


# ── Design 10 — America 250 Shield ──────────────────────────────────────────
# Matches original "Shield" AI design:
#   CREAM base pentagon/shield shape (ivory background).
#   NAVY: thick border ring + eagle silhouette (center).
#   GOLD: horizontal banner stripe + "AMERICA" text.
#   RED: 7 stars row (near top) + "250" text (center-lower area).
# Zone layout keeps all layers non-overlapping in XY.

def shield() -> list[tuple[str, str]]:
    W, H = 220, 255
    cx = W / 2   # 110

    # Shield outline path (flat top, pointed bottom at Y=H)
    def shield_path(inset: float = 0) -> str:
        i = inset
        return (
            f"M{10+i:.1f},{i:.1f} H{W-10-i:.1f} "
            f"Q{W-i:.1f},{i:.1f} {W-i:.1f},{10+i:.1f} V{110-i:.1f} "
            f"L{cx:.1f},{H-i:.1f} "
            f"L{i:.1f},{110-i:.1f} V{10+i:.1f} Q{i:.1f},{i:.1f} {10+i:.1f},{i:.1f} Z"
        )

    # CREAM base: full shield
    base = doc(W, H, P(shield_path(0)))

    # NAVY border ring (evenodd outer + inner shield paths) + eagle
    EX, EY = cx, 148     # eagle center
    def eagle_parts() -> str:
        parts = [
            # Body oval
            P(f"M{EX-12:.1f},{EY:.1f} A12,15 0 1,1 {EX+12:.1f},{EY:.1f} "
              f"A12,15 0 1,1 {EX-12:.1f},{EY:.1f} Z"),
            # Left wing  (swept upward)
            P(f"M{EX-10:.1f},{EY-6:.1f} L{EX-57:.1f},{EY-22:.1f} "
              f"L{EX-54:.1f},{EY+8:.1f} L{EX-10:.1f},{EY+7:.1f} Z"),
            # Right wing
            P(f"M{EX+10:.1f},{EY-6:.1f} L{EX+57:.1f},{EY-22:.1f} "
              f"L{EX+54:.1f},{EY+8:.1f} L{EX+10:.1f},{EY+7:.1f} Z"),
            # Head
            C(EX, EY - 24, 9),
            # Tail feather fan
            P(f"M{EX-11:.1f},{EY+15:.1f} L{EX-7:.1f},{EY+30:.1f} "
              f"L{EX:.1f},{EY+16:.1f} L{EX+7:.1f},{EY+30:.1f} "
              f"L{EX+11:.1f},{EY+15:.1f} Z"),
        ]
        return "".join(parts)

    navy = doc(W, H,
        # Shield border: outer shield evenodd inner-shield
        P(shield_path(0) + "  " + shield_path(9), fr="evenodd"),
        eagle_parts(),
    )

    # GOLD: ribbon banner (Y=72–102) with "AMERICA" + dates below eagle
    # Banner is a wide stripe spanning the shield at that Y level.
    gold = doc(W, H,
        R(16, 72,  W - 32, 3),       # top banner rule
        T(cx, 86,  22, "AMERICA"),   # banner text (Y=76–96)
        R(16, 100, W - 32, 3),       # bottom banner rule
    )

    # RED: 7 small stars near top of shield (Y=22-34) + "250" (Y=190-210)
    # Non-overlap with GOLD banner (Y=72-103) and NAVY eagle (Y=116-178):
    #   Stars (Y=22-34) → gap to GOLD banner (Y=72) = 38px ✓
    #   "250" (Y=190-210) → gap from NAVY eagle tail (Y=178) = 12px ✓
    red = doc(W, H,
        *[star(18 + 30*i, 28, 6, 2.5, 5) for i in range(7)],
        T(cx, 200, 28, "250"),
    )

    return [
        ("layer01_base_CREAM.svg", base),
        ("layer02_navy_NAVY.svg",  navy),
        ("layer03_gold_GOLD.svg",  gold),
        ("layer04_red_RED.svg",    red),
    ]


# ── Design 11 — America 250 Stamp ───────────────────────────────────────────
# Cream base.
# NAVY: outer frame + perforation circles + Statue of Liberty silhouette
#       + "UNITED STATES" + "1776  2026" (top text).
# RED:  "AMERICA" + "250".
# GOLD: "FOREVER" + inner frame accent + small star.

def stamp() -> list[tuple[str, str]]:
    W, H = 210, 250

    base = doc(W, H, R(0, 0, W, H))   # cream rectangle

    # ── Liberty silhouette ───────────────────────────────────────────────
    # Centered at x=105, crown tip at y=60, pedestal base at y=175
    LX, LB = 105, 175   # centerX, bottom Y

    def liberty_parts() -> str:
        parts = []
        # Pedestal (base)
        parts.append(R(LX-14, LB-15, 28, 15))
        # Wide plinth
        parts.append(R(LX-20, LB-22, 40,  7))
        # Lower robe (wide trapezoid)
        parts.append(P(
            f"M{LX-15:.0f},{LB-22:.0f} L{LX-8:.0f},{LB-65:.0f} "
            f"H{LX+8:.0f} L{LX+15:.0f},{LB-22:.0f} Z"
        ))
        # Upper body
        parts.append(P(
            f"M{LX-8:.0f},{LB-65:.0f} L{LX-4:.0f},{LB-82:.0f} "
            f"H{LX+4:.0f} L{LX+8:.0f},{LB-65:.0f} Z"
        ))
        # Head
        parts.append(C(LX, LB - 89, 7))
        # Crown — 3 spikes
        parts.append(P(f"M{LX-3:.0f},{LB-96:.0f} L{LX:.0f},{LB-112:.0f} L{LX+3:.0f},{LB-96:.0f} Z"))
        parts.append(P(f"M{LX-11:.0f},{LB-93:.0f} L{LX-8:.0f},{LB-106:.0f} L{LX-5:.0f},{LB-93:.0f} Z"))
        parts.append(P(f"M{LX+5:.0f},{LB-93:.0f} L{LX+8:.0f},{LB-106:.0f} L{LX+11:.0f},{LB-93:.0f} Z"))
        # Raised right arm
        parts.append(P(
            f"M{LX+5:.0f},{LB-78:.0f} L{LX+22:.0f},{LB-98:.0f} "
            f"L{LX+26:.0f},{LB-93:.0f} L{LX+9:.0f},{LB-73:.0f} Z"
        ))
        # Torch body
        parts.append(R(LX+21, LB-103, 5, 6))
        # Torch flame
        parts.append(P(
            f"M{LX+23:.0f},{LB-109:.0f} L{LX+21:.0f},{LB-103:.0f} "
            f"L{LX+26:.0f},{LB-103:.0f} Z"
        ))
        # Left arm (holding tablet)
        parts.append(P(
            f"M{LX-5:.0f},{LB-76:.0f} L{LX-18:.0f},{LB-68:.0f} "
            f"L{LX-21:.0f},{LB-73:.0f} L{LX-8:.0f},{LB-81:.0f} Z"
        ))
        # Tablet
        parts.append(R(LX-25, LB-72, 8, 14))
        return "".join(parts)

    # Perforation dots — circles along inner edge of stamp frame
    PERF_R    = 3.5
    PERF_INSET = 7
    def perf_row_h(y, count=17):
        """Horizontal row of perforation circles."""
        gap = (W - 2 * PERF_INSET) / (count - 1)
        return "".join(C(PERF_INSET + i * gap, y, PERF_R) for i in range(count))
    def perf_col_v(x, count=19):
        """Vertical column of perforation circles."""
        gap = (H - 2 * PERF_INSET) / (count - 1)
        return "".join(C(x, PERF_INSET + i * gap, PERF_R) for i in range(count))

    navy_els = [
        # Outer frame ring (thick border)
        P(f"M0,0 H{W} V{H} H0 Z  M14,14 H{W-14} V{H-14} H14 Z", fr="evenodd"),
        # Perforation circles (override solid frame with cutouts by same color = keeps holes visual)
        perf_row_h(7, 17),       # top edge
        perf_row_h(H - 7, 17),  # bottom edge
        perf_col_v(7, 19),       # left edge
        perf_col_v(W - 7, 19),  # right edge
        # "UNITED STATES" header text — zone Y ≈ 24–40
        T(W/2, 30, 16, "UNITED STATES"),
        # "1776  ·  2026" — zone Y ≈ 40–54
        TM(W/2, 48, 12, "1776          2026"),
        # Liberty silhouette
        liberty_parts(),
    ]
    navy = doc(W, H, *navy_els)

    # Red: "AMERICA" (Y ≈ 185–205) and "250" (Y ≈ 205–225)
    # Note: perforation frame is navy at edges — red text is in inner cream zone, no overlap
    red = doc(W, H,
        T(W/2, 192, 22, "AMERICA"),
        T(W/2, 218, 20, "250"),
    )

    # Gold: "FOREVER" label (small, Y ≈ 230–242) + inner frame accent line
    gold = doc(W, H,
        R(20, 58, W - 40, 1.5),    # thin accent line below header
        TM(W/2, 236, 11, "F O R E V E R"),
        star(W/2, 176, 5, 2, 5),    # small gold star between Liberty and red text
    )

    return [
        ("layer01_base_CREAM.svg", base),
        ("layer02_navy_NAVY.svg",  navy),
        ("layer03_red_RED.svg",    red),
        ("layer04_gold_GOLD.svg",  gold),
    ]


# ── Preview compositor ────────────────────────────────────────────────────────

COLOR_MAP = {
    "NAVY":  (27,  58, 104),
    "RED":   (183, 34,  46),
    "GOLD":  (201, 168, 76),
    "CREAM": (245, 237, 214),
}

def make_preview(folder: Path, layers: list[tuple[str, str]]) -> None:
    composited: Image.Image | None = None
    for i, (name, svg_text) in enumerate(layers):
        m = re.search(r'viewBox="0 0 (\S+) (\S+)"', svg_text)
        if not m:
            continue
        wm, hm = float(m.group(1)), float(m.group(2))
        SCALE = 4
        wp, hp = int(wm * SCALE), int(hm * SCALE)

        key = "CREAM"
        for k in COLOR_MAP:
            if k in name.upper():
                key = k
                break
        col = COLOR_MAP[key]

        png = cairosvg.svg2png(bytestring=svg_text.encode(),
                                output_width=wp, output_height=hp)
        layer = Image.open(io.BytesIO(png)).convert("RGBA")

        if i == 0:
            composited = Image.new("RGB", (wp, hp), col)
        else:
            overlay = Image.new("RGBA", (wp, hp), col + (255,))
            overlay.putalpha(layer.split()[3])
            comp = composited.convert("RGBA")
            comp.paste(overlay, (0, 0), overlay)
            composited = comp.convert("RGB")

    if composited:
        out = folder / "preview.jpg"
        composited.save(out, "JPEG", quality=90)
        print(f"    preview.jpg  {out.stat().st_size // 1024} KB")


# ── Validate SVG layers ───────────────────────────────────────────────────────

def validate(name: str, content: str) -> bool:
    fills  = len(set(re.findall(r'fill="#([0-9a-fA-F]{3,6})"', content)))
    paths  = len(re.findall(r'<path', content))
    size_k = len(content.encode()) // 1024
    ok = fills <= 20 and paths <= 200 and size_k <= 150
    status = "✓" if ok else "✗"
    print(f"    {status} {name}: {fills} fills, {paths} paths, {size_k} KB")
    return ok


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    generators = {
        "07_america250_banner_4c":  banner,
        "08_america250_burst_4c":   burst,
        "09_america250_seal_4c":    seal,
        "10_america250_shield_4c":  shield,
        "11_america250_stamp_4c":   stamp,
    }

    print("Generating 4-color America 250 designs")
    print("=" * 60)
    all_ok = True

    for slug, display_name in DESIGNS:
        print(f"\n  {display_name}  ({slug})")
        folder = DESIGNS_DIR / slug
        folder.mkdir(parents=True, exist_ok=True)

        # Remove stale layer SVGs before writing new ones
        for old in folder.glob("layer*.svg"):
            old.unlink()

        layers = generators[slug]()

        for fname, content in layers:
            ok = validate(fname, content)
            if not ok:
                all_ok = False
            (folder / fname).write_text(content, encoding="utf-8")

        make_preview(folder, layers)

    print("\n" + "=" * 60)
    print("All designs generated" + (" ✓" if all_ok else " — check warnings above"))


if __name__ == "__main__":
    main()
