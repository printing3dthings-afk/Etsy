"""
planner_hyperlinker.py — turn a flat v2 planner PDF into a genuinely "smart,
easy to use" interactive planner.

The v2 builder (generate_planner_v2.py) produces a beautiful, dimensional
planner, but its navigation is *decorative only*: the dashboard buttons, the
index rows and the "HOME / PREV / NEXT" footer are painted text with no real
links. This module post-processes the PDF with PyMuPDF to add the real thing:

  1. A premium celestial cover image (PIL-generated, no paid API) as page 1.
  2. A PDF outline / table of contents (the "bookmarks" panel) — works in
     GoodNotes, Notability, PDF Expert and Acrobat alike.
  3. Tappable dashboard buttons — each jumps to that section's first page.
  4. Tappable planner-index rows — each jumps to its section.
  5. A working HOME / PREV / NEXT footer on every page.

All link targets are resolved by *scanning the rendered page text*, so this stays
correct even if the page order changes. Cross-app compatible: these are standard
PDF GoTo link annotations and a standard document outline — no JavaScript, which
research confirmed GoodNotes does not execute.

Usage:
    python tools/planner_hyperlinker.py DP1034
    python tools/planner_hyperlinker.py DP1034 --no-cover
"""

import re
import sys
import math
import random
import calendar as _calmod
import argparse
from datetime import date
from pathlib import Path

import fitz  # PyMuPDF

_MONTHS_FULL = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]

_BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCT_FILES_DIR = _BASE_DIR / "data" / "digital_products" / "product_files"

PW, PH = 612.0, 792.0  # US Letter, matches _new_canvas() in generate_planner.py

# Celestial Night palette (hex -> 0-255 tuples) — DEFAULT cover palette, used
# whenever a product doesn't pass its own theme/accent/bg/dark colors through.
INDIGO_TOP = (20, 18, 46)      # #14122E
SPACE_PURPLE = (45, 43, 85)    # #2D2B55
INDIGO = (30, 27, 75)          # #1E1B4B
GOLD = (201, 168, 76)          # #C9A84C
MOONBEAM = (240, 238, 248)     # #F0EEF8


def _to255(rgb01):
    """Convert a 0-1 float RGB tuple (as used in PLANNERS/PLANNER_CONFIGS) to 0-255 ints."""
    return tuple(int(round(c * 255)) for c in rgb01)


def _cover_palette(theme_rgb=None, accent_rgb=None, bg_rgb=None, dark_rgb=None):
    """Build the 5-color palette used by the cover builders below.

    Falls back to the Celestial Night defaults (DP1034's original look) when no
    product-specific colors are supplied, so existing behavior is unchanged for
    callers that don't pass colors.
    """
    if dark_rgb is None:
        indigo_top, space_purple, indigo = INDIGO_TOP, SPACE_PURPLE, INDIGO
    else:
        dark = _to255(dark_rgb)
        mid = _to255(theme_rgb) if theme_rgb else SPACE_PURPLE
        indigo_top, space_purple, indigo = dark, mid, dark
    gold = _to255(accent_rgb) if accent_rgb else GOLD
    moonbeam = _to255(bg_rgb) if bg_rgb else MOONBEAM
    return indigo_top, space_purple, indigo, gold, moonbeam


# ---------------------------------------------------------------------------
# 1. Premium celestial cover (PIL — free, deterministic, no API)
# ---------------------------------------------------------------------------

def _font(size, bold=False):
    from PIL import ImageFont
    candidates = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def build_cover_png(out_path, title, subtitle, year, shop="OnBrandCraftz",
                     theme_rgb=None, accent_rgb=None, bg_rgb=None, dark_rgb=None):
    """Deep night-sky-style cover: gradient, stars, constellation, crescent moon, title.

    Colors default to the Celestial Night palette (DP1034's original look). Pass
    theme_rgb/accent_rgb/bg_rgb/dark_rgb (0-1 float tuples, as used in PLANNERS /
    PLANNER_CONFIGS) to render the same composition in a different product's theme.
    """
    from PIL import Image, ImageDraw, ImageFilter

    indigo_top, space_purple, indigo, gold, moonbeam = _cover_palette(
        theme_rgb, accent_rgb, bg_rgb, dark_rgb)

    S = 2  # supersample factor for crisp edges
    W, H = int(PW) * S, int(PH) * S
    img = Image.new("RGB", (W, H), indigo)
    draw = ImageDraw.Draw(img)

    # Vertical gradient: dark-top -> mid-tone (middle) -> dark
    for y in range(H):
        f = y / float(H)
        if f < 0.5:
            g = f / 0.5
            col = tuple(int(indigo_top[i] + (space_purple[i] - indigo_top[i]) * g) for i in range(3))
        else:
            g = (f - 0.5) / 0.5
            col = tuple(int(space_purple[i] + (indigo[i] - space_purple[i]) * g) for i in range(3))
        draw.line([(0, y), (W, y)], fill=col)

    rng = random.Random(2026)
    # Scattered stars (accent + white), varied size, soft glow on the big ones
    stars = []
    for _ in range(260):
        x, y = rng.randint(0, W), rng.randint(0, int(H * 0.92))
        r = rng.choice([1, 1, 1, 2, 2, 3]) * S
        bright = rng.random()
        col = gold if bright > 0.55 else (235, 233, 245)
        stars.append((x, y, r))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=col)
        if r >= 3 * S:  # 4-point sparkle on the largest stars
            draw.line([(x - r * 3, y), (x + r * 3, y)], fill=col, width=S)
            draw.line([(x, y - r * 3), (x, y + r * 3)], fill=col, width=S)

    # A few constellation lines connecting nearby stars
    rng.shuffle(stars)
    for i in range(0, 14, 2):
        a, b = stars[i], stars[i + 1]
        if abs(a[0] - b[0]) < W * 0.28 and abs(a[1] - b[1]) < H * 0.18:
            draw.line([(a[0], a[1]), (b[0], b[1])], fill=(120, 110, 170), width=S)

    # Crescent moon, upper-center
    mx, my, mr = int(W * 0.5), int(H * 0.30), int(W * 0.13)
    moon = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(moon)
    md.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=255)
    off = int(mr * 0.55)
    md.ellipse([mx - mr + off, my - mr - off * 0.2, mx + mr + off, my + mr - off * 0.2], fill=0)
    moon = moon.filter(ImageFilter.GaussianBlur(S))
    gold_layer = Image.new("RGB", (W, H), gold)
    img.paste(gold_layer, (0, 0), moon)

    # Thin double border frame
    m = int(20 * S)
    draw.rectangle([m, m, W - m, H - m], outline=gold, width=max(1, S))
    m2 = int(27 * S)
    draw.rectangle([m2, m2, W - m2, H - m2], outline=(150, 126, 60), width=max(1, S))

    def centered(text, cy, font, fill):
        bb = draw.textbbox((0, 0), text, font=font)
        w = bb[2] - bb[0]
        draw.text(((W - w) / 2, cy), text, font=font, fill=fill)

    # Title (wrapped), subtitle, year, shop
    title_font = _font(58 * S, bold=True)
    words = title.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=title_font) > W * 0.78 and cur:
            lines.append(cur); cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    ty = int(H * 0.55)
    for ln in lines:
        centered(ln, ty, title_font, gold)
        ty += int(66 * S)

    centered("✦  " + subtitle.upper() + "  ✦", ty + int(10 * S), _font(26 * S), moonbeam)
    if year:
        centered(str(year), ty + int(54 * S), _font(40 * S, bold=True), moonbeam)
    centered(shop.upper(), H - int(70 * S), _font(20 * S), (170, 160, 200))

    img = img.resize((int(PW), int(PH)), Image.LANCZOS)
    img.save(out_path)
    return out_path


def compose_ai_cover(ai_path, out_path, title, subtitle, year, shop="OnBrandCraftz",
                      theme_rgb=None, accent_rgb=None, bg_rgb=None, dark_rgb=None):
    """Place an OpenAI cover illustration onto a letter-ratio canvas and add the
    title text in the lower third. Letter ratio in = no distortion when the page
    inserts it full-bleed.

    Colors default to the Celestial Night palette (DP1034's original look). Pass
    theme_rgb/accent_rgb/bg_rgb/dark_rgb (0-1 float tuples, as used in PLANNERS /
    PLANNER_CONFIGS) to match the composited frame/text colors to the product's
    real theme instead.
    """
    from PIL import Image, ImageDraw

    indigo_top, space_purple, indigo, gold, moonbeam = _cover_palette(
        theme_rgb, accent_rgb, bg_rgb, dark_rgb)
    scrim_rgb = indigo_top

    S = 2
    W, H = int(PW) * S, int(PH) * S
    canvas = Image.new("RGB", (W, H), indigo)
    draw = ImageDraw.Draw(canvas)
    for y in range(H):
        f = y / float(H)
        if f < 0.5:
            g = f / 0.5
            col = tuple(int(indigo_top[i] + (space_purple[i] - indigo_top[i]) * g) for i in range(3))
        else:
            g = (f - 0.5) / 0.5
            col = tuple(int(space_purple[i] + (indigo[i] - space_purple[i]) * g) for i in range(3))
        draw.line([(0, y), (W, y)], fill=col)

    ai = Image.open(ai_path).convert("RGB")
    # fit to height, centered horizontally (illustration's clear lower third sits low)
    scale = H / float(ai.height)
    nw = int(ai.width * scale)
    ai = ai.resize((nw, H), Image.LANCZOS)
    canvas.paste(ai, ((W - nw) // 2, 0))

    # scrim over lower area for title legibility
    region_top = int(H * 0.66)
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    sd.rectangle([0, region_top, W, H], fill=(scrim_rgb[0], scrim_rgb[1], scrim_rgb[2], 165))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), scrim).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # double border
    m = int(20 * S); draw.rectangle([m, m, W - m, H - m], outline=gold, width=max(1, S))
    m2 = int(27 * S); draw.rectangle([m2, m2, W - m2, H - m2], outline=(150, 126, 60), width=max(1, S))

    def centered(text, cy, font, fill):
        bb = draw.textbbox((0, 0), text, font=font); w = bb[2] - bb[0]
        draw.text(((W - w) / 2, cy), text, font=font, fill=fill)

    title_font = _font(40 * S, bold=True)
    words = title.split(); lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=title_font) > W * 0.84 and cur:
            lines.append(cur); cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)

    sub_font = _font(22 * S)
    year_font = _font(30 * S, bold=True)
    shop_font = _font(16 * S)

    # measured, packed stack centered within the lower band
    line_h = int(46 * S)
    block = [(ln, title_font, gold, line_h) for ln in lines]
    block.append(("·   " + subtitle.upper() + "   ·", sub_font, moonbeam, int(38 * S)))
    if year and str(year) not in title:
        block.append((str(year), year_font, moonbeam, int(44 * S)))
    block.append((shop.upper(), shop_font, (185, 175, 215), int(34 * S)))
    total_h = sum(h for _, _, _, h in block)
    band_top, band_bot = region_top + int(18 * S), H - m2 - int(14 * S)
    y = band_top + max(0, ((band_bot - band_top) - total_h) // 2)
    for text, font, fill, h in block:
        centered(text, y, font, fill); y += h

    canvas = canvas.resize((int(PW), int(PH)), Image.LANCZOS)
    canvas.save(out_path)
    return out_path


# ---------------------------------------------------------------------------
# 2. Section detection (scan rendered text -> first page of each section)
# ---------------------------------------------------------------------------

_MONTH_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|October|November|December)\b",
    re.I)
_WEEKDAY_RE = re.compile(r"^(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b", re.I)

# (canonical key, matcher) — first matching page wins per key
def _detect_sections(doc):
    found = {}

    def first(key, pred):
        if key in found:
            return
        for i in range(doc.page_count):
            head = doc[i].get_text("text").strip()
            if pred(head):
                found[key] = i
                return

    first("welcome", lambda h: h.lower().startswith("welcome"))
    first("dashboard", lambda h: "DASHBOARD" in h[:40])
    first("index", lambda h: "PLANNER INDEX" in h[:40])
    first("yearly", lambda h: "YEARLY OVERVIEW" in h[:40])
    first("monthly", lambda h: bool(_MONTH_RE.match(h)) and "AT A GLANCE" not in h[:40] and "REVIEW" not in h[:40])
    first("monthly_review", lambda h: "MONTHLY REVIEW" in h[:40])
    first("glance", lambda h: "MONTH AT A GLANCE" in h[:40])
    first("weekly", lambda h: h.upper().startswith("WEEK "))
    first("daily", lambda h: bool(_WEEKDAY_RE.match(h)) or h.upper().startswith("DAILY PLAN"))
    first("brain_dump", lambda h: "BRAIN DUMP" in h[:40])
    first("budget", lambda h: "BUDGET TRACKER" in h[:40])
    first("meal", lambda h: "MEAL PLANNER" in h[:40])
    first("habit", lambda h: "HABIT TRACKER" in h[:40])
    first("goals", lambda h: "SMART GOALS" in h[:40])
    first("notes", lambda h: h.upper().startswith("NOTES"))
    first("stickers", lambda h: "STICKER LIBRARY" in h[:40])
    first("year_in_pixels", lambda h: "YEAR IN PIXELS" in h[:40])
    first("class_schedule", lambda h: "CLASS SCHEDULE" in h[:40])
    first("priority_matrix", lambda h: "PRIORITY MATRIX" in h[:40])
    first("pomodoro", lambda h: "POMODORO" in h[:40])
    first("debt_payoff", lambda h: "DEBT PAYOFF" in h[:40])
    first("savings_goal", lambda h: "SAVINGS GOAL" in h[:40])
    first("bill_checklist", lambda h: "BILL PAYMENT" in h[:40])
    first("progress_photos", lambda h: "PROGRESS PHOTOS" in h[:40])
    first("water_tracker", lambda h: "WATER INTAKE" in h[:40])
    first("sleep_log", lambda h: "SLEEP QUALITY" in h[:40])
    first("nsv_journal", lambda h: "NON-SCALE VICTORIES" in h[:40])
    return found


# section label (as it appears in cfg["sections"]) -> detection key
def _label_to_key(label):
    l = label.lower()
    if "welcome" in l: return "welcome"
    if "dashboard" in l: return "dashboard"
    if "index" in l: return "index"
    if "year in pixels" in l: return "year_in_pixels"
    if "yearly" in l or "year at" in l or "year in" in l: return "yearly"
    if "monthly review" in l: return "monthly_review"
    if "at a glance" in l: return "glance"
    if "monthly cal" in l or l.startswith("monthly"): return "monthly"
    if "class schedule" in l: return "class_schedule"
    if "weekly" in l: return "weekly"
    if "daily" in l: return "daily"
    if "priority matrix" in l: return "priority_matrix"
    if "brain dump" in l: return "brain_dump"
    if "pomodoro" in l: return "pomodoro"
    if "debt payoff" in l: return "debt_payoff"
    if "savings goal" in l: return "savings_goal"
    if "bill payment" in l or "bill checklist" in l: return "bill_checklist"
    if "habit" in l: return "habit"
    if "smart goal" in l or l == "goals" or "goals" in l: return "goals"
    if "budget" in l: return "budget"
    if "meal" in l: return "meal"
    if "progress photos" in l: return "progress_photos"
    if "water tracker" in l or "water intake" in l: return "water_tracker"
    if "sleep quality" in l or "sleep log" in l: return "sleep_log"
    if "non-scale" in l or "nsv" in l: return "nsv_journal"
    if "note" in l: return "notes"
    if "sticker" in l: return "stickers"
    return None


# ---------------------------------------------------------------------------
# 3. Coordinate helpers (reportlab bottom-left -> fitz top-left)
# ---------------------------------------------------------------------------

def _rl_rect(x, y, w, h):
    """reportlab (x, y_bottom, w, h) -> fitz.Rect."""
    return fitz.Rect(x, PH - (y + h), x + w, PH - y)


# ---------------------------------------------------------------------------
# 2b. Real fillable AcroForm widgets — the v2 page generators only ever draw
# guide-LINES for "fill this in" areas (c.line()/c.roundRect() strokes with no
# underlying form field). That makes "type directly into the planner" false
# for any app that respects real PDF forms (Acrobat, PDF Expert, Xodo,
# Notability). This adds genuine fitz.Widget text/checkbox fields at the exact
# coordinates the v2 generators already draw their guide-lines at, so the
# claim becomes literally true instead of a painted illusion.
# ---------------------------------------------------------------------------

_field_seq = [0]


def _widget(page, rect, fontsize=8, multiline=False, checkbox=False):
    w = fitz.Widget()
    w.rect = rect
    _field_seq[0] += 1
    w.field_name = f"f{_field_seq[0]}"
    if checkbox:
        w.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
    else:
        w.field_type = fitz.PDF_WIDGET_TYPE_TEXT
        w.text_fontsize = fontsize
        if multiline:
            w.field_flags = fitz.PDF_TX_FIELD_IS_MULTILINE
    w.border_color = None
    w.fill_color = None
    page.add_widget(w)


def _daily_field_rects():
    M = ML + 26
    top = PH - 58 - 14
    col_split = M + (PW - MR - M) * 0.66
    box_y = top - 46
    out = []
    for i in range(3):
        cy = box_y + 22 - i * 9
        out.append((_rl_rect(M + 22, cy - 3, (col_split - 16) - (M + 22), 10), 8, False, False))
    sched_top = box_y - 12
    sched_bottom = 96.0
    hours = list(range(6, 23))
    row_h = (sched_top - sched_bottom) / float(len(hours))
    time_col_w = 46.0
    for i in range(len(hours)):
        ry = sched_top - (i + 1) * row_h
        out.append((_rl_rect(M + time_col_w, ry, (PW - MR) - (M + time_col_w), row_h), 7, False, False))
    wy = sched_bottom - 20
    gy = wy - 22
    out.append((_rl_rect(M + 70, gy + 1, (PW - MR) - (M + 70), 10), 8, False, False))
    return out


def _weekly_field_rects():
    M = ML + 26
    top = PH - 58 - 14
    notes_w = (PW - MR - M) * 0.20
    day_area_w = (PW - MR - M) - notes_w - 6
    day_w = day_area_w / 7.0
    grid_top = top - 4
    grid_bottom = 70.0
    hdr_h = 20.0
    body_top = grid_top - hdr_h
    out = []
    for di in range(7):
        dx = M + di * day_w
        out.append((_rl_rect(dx + 2, grid_bottom + 2, day_w - 6, (body_top - 4) - (grid_bottom + 2)),
                    7, True, False))
    nx = M + day_area_w + 6
    for i in range(3):
        cy = grid_top - 30 - i * 14
        out.append((_rl_rect(nx + 18, cy - 3, (nx + notes_w - 6) - (nx + 18), 10), 7, False, False))
    notes_top = grid_top - 90
    out.append((_rl_rect(nx + 6, grid_bottom + 6, notes_w - 12, notes_top - (grid_bottom + 6)),
                7, True, False))
    return out


def _monthly_field_rects(head, year):
    M = ML + 26
    top = PH - 58 - 14
    grid_bottom = 86.0
    days_hdr_h = 18.0
    dw = (PW - MR - M) / 7.0
    n_rows = 6
    row_h = (top - days_hdr_h - grid_bottom) / float(n_rows)

    out = [(_rl_rect(M + 250, grid_bottom - 44, (PW - MR) - (M + 250), 30), 8, True, False)]

    m = _MONTH_RE.match(head.strip())
    if m:
        mi = [s.lower() for s in _MONTHS_FULL].index(m.group(1).lower()) + 1
        cal_year = year if year else date.today().year
        first_wd, n_days = _calmod.monthrange(cal_year, mi)
        day_num = 1
        for r in range(n_rows):
            for col in range(7):
                idx = r * 7 + col
                cx0 = M + col * dw
                cy0 = top - days_hdr_h - (r + 1) * row_h
                if idx >= first_wd and day_num <= n_days:
                    out.append((_rl_rect(cx0 + 3, cy0 + 3, dw - 7.2, row_h - 26.2), 7, True, False))
                    day_num += 1
    return out


def _brain_dump_field_rects():
    M = ML + 26
    top = PH - 58 - 14
    dump_h = (top - MB) * 0.52
    dump_y = top - dump_h
    out = [(_rl_rect(M + 6, dump_y + 6, (PW - MR - M) - 12, dump_h - 12), 8, True, False)]
    mx_top = dump_y - 14
    mx_h = mx_top - MB - 16
    mx_w = PW - MR - M
    qw, qh = mx_w / 2.0, mx_h / 2.0
    for qi in range(4):
        qx = M + (qi % 2) * qw
        qy = mx_top - mx_h + (1 - qi // 2) * qh
        top_y, bot_y = qy + qh - 30, qy + 8
        out.append((_rl_rect(qx + 12, bot_y, qw - 26, top_y - bot_y), 7, True, False))
    return out


def _goals_field_rects():
    M = ML + 26
    top = PH - 58 - 14
    col_w = (PW - MR - M - 14) / 2.0
    gh = top - MB
    row_h = (gh - 26) / 5.0
    out = []
    for gi in range(2):
        gx = M + gi * (col_w + 14)
        for li in range(5):
            ry = MB + gh - 26 - (li + 1) * row_h
            out.append((_rl_rect(gx + 30, ry + 6, (col_w - 10) - 30, row_h - 28), 7, True, False))
    return out


def _habit_field_rects():
    M = ML + 26
    top = PH - 58 - 14
    habit_col_w = 92.0
    n_habits = 8
    grid_top = top - 28
    grid_bottom = 92.0
    day_col_w = (PW - MR - M - habit_col_w) / 31.0
    row_h = (grid_top - grid_bottom) / float(n_habits + 1)
    out = [
        (_rl_rect(110, top - 16, 90, 12), 7, False, False),                       # "Month:" blank
        (_rl_rect(260, top - 16, (PW - MR) - 260, 12), 7, False, False),          # "Goal:" blank
    ]
    for h in range(n_habits):
        ry = grid_top - (h + 2) * row_h
        out.append((_rl_rect(M + 6, ry + 1, habit_col_w - 12, row_h - 6), 7, False, False))
        for d in range(31):
            dx = M + habit_col_w + d * day_col_w
            cx, cy = dx + day_col_w / 2.0, ry + row_h / 2.0
            r = min(day_col_w, row_h) * 0.28
            out.append((_rl_rect(cx - r, cy - r, 2 * r, 2 * r), 6, False, True))
    return out


def _monthly_review_field_rects():
    # geometry mirrors generate_planner.py::_gen_monthly_review_pages
    box_h = (PH - 52 - 20 - MB - 26) / 4 - 6
    y = PH - 52 - 20
    out = []
    for pi in range(4):
        py = y - pi * (box_h + 6)
        li_n = max(1, int((box_h - 38) / 18))
        for li in range(li_n):
            ly = py - 46 - li * 18
            if ly > py - box_h + 8:
                out.append((_rl_rect(ML + 8, ly - 2, CW - 16, 12), 7, False, False))
    return out


def _month_glance_field_rects():
    # geometry mirrors generate_planner.py::_gen_month_at_a_glance
    y = PH - 52 - 18
    avail = y - MB - 26
    top_h = avail * 0.44
    out = []
    for li in range(5):
        ly = y - 34 - li * 20
        if ly > y - top_h + 8:
            out.append((_rl_rect(ML + 10, ly - 2, CW / 2 - 22, 12), 7, False, False))
    fx = ML + CW / 2 + 4
    for li in range(4):
        ly = y - 34 - li * 22
        if ly > y - top_h + 8:
            out.append((_rl_rect(fx + 8, ly - 2, CW / 2 - 20, 12), 7, False, False))
    mid_y = y - top_h - 8
    mid_h = avail * 0.30
    for li in range(3):
        ly = mid_y - 34 - li * 18
        if ly > mid_y - mid_h + 6:
            out.append((_rl_rect(ML + 8, ly - 2, CW * 0.65 - 20, 12), 7, False, False))
    wx = ML + CW * 0.65 + 4
    ww = CW * 0.35 - 4
    out.append((_rl_rect(wx + 8, mid_y - mid_h / 2 - 12, ww - 16, 16), 8, False, False))
    bot_y = mid_y - mid_h - 8
    bot_h = bot_y - MB - 2
    if bot_h > 20:
        for li in range(2):
            ly = bot_y - 28 - li * 18
            if ly > MB + 8:
                out.append((_rl_rect(ML + 8, ly - 2, CW - 16, 12), 7, False, False))
    return out


def _budget_field_rects():
    # geometry mirrors generate_planner.py::_gen_budget_page
    y = PH - 52 - 16
    out = [
        (_rl_rect(ML + 34.25, y - 2, 112.32, 12), 8, False, False),  # Month
        (_rl_rect(ML + 222.82, y - 2, 84.24, 12), 8, False, False),  # Income Goal $
        (_rl_rect(ML + 362.21, y - 2, 84.24, 12), 8, False, False),  # Savings $
    ]
    y -= 22
    col_w = CW / 2 - 4
    row_h = 22

    def col_rows(x, rows):
        for ri in range(len(rows)):
            ry = y - 16 - (ri + 1) * row_h
            out.append((_rl_rect(x + col_w - 44, ry + 2, 38, 12), 7, False, False))

    col_rows(ML, ["Salary / Wages", "Side Income", "Etsy Sales", "Other", "TOTAL INCOME"])
    col_rows(ML + col_w + 8,
             ["Housing / Rent", "Food / Groceries", "Transport", "Utilities", "Entertainment",
              "Health", "Shopping", "Savings", "Other", "TOTAL EXPENSES"])

    n_max = 10
    bal_y = y - 16 - (n_max + 1) * row_h - 6
    if bal_y > MB + 2:
        # "BALANCE (Income - Expenses):  $" prefix is 177.17pt wide at Poppins-Bold 10pt
        out.append((_rl_rect(ML + 8 + 177.17, bal_y - 20, 195.0, 14), 9, False, False))
    return out


def _meal_plan_field_rects():
    # geometry mirrors generate_planner.py::_gen_meal_plan_page
    y_header = PH - 52 - 16
    out = [
        (_rl_rect(ML + 41.46, y_header - 2, 168.48, 12), 8, False, False),  # Week of
        (_rl_rect(ML + 282.46, y_header - 2, 42.12, 12), 8, False, False),  # Calories/day
        (_rl_rect(ML + 365.3, y_header - 2, 42.12, 12), 8, False, False),   # Water
    ]
    y = y_header - 22
    meal_lbl_w = 56.0
    day_col_w = (CW - meal_lbl_w) / 7.0
    day_hdr_h = 16.0
    n_meals = 4
    meal_row_h = (y - MB - 44) / float(n_meals)

    for mi in range(n_meals):
        ry = y - day_hdr_h - (mi + 1) * meal_row_h
        for di in range(7):
            dx = ML + meal_lbl_w + di * day_col_w
            out.append((_rl_rect(dx + 3, ry + 3, day_col_w - 6, meal_row_h - 6), 6, True, False))

    bot_y = y - day_hdr_h - n_meals * meal_row_h - 8
    if bot_y > MB + 2:
        bot_h = bot_y - MB - 2
        cols_n = 3
        items_per = max(1, int(bot_h / 18))
        for gi in range(min(items_per * cols_n, 18)):
            gcol = gi // items_per
            gri = gi % items_per
            gx = ML + 8 + gcol * (CW / cols_n)
            gy = MB + bot_h - 24 - gri * 16
            if gy > MB + 4:
                out.append((_rl_rect(gx + 12, gy - 2, CW / cols_n - 24, 12), 7, False, False))
    return out


def _notes_field_rects():
    # geometry mirrors generate_planner.py::_gen_notes_pages
    y = PH - 52 - 10
    out = [
        (_rl_rect(ML + 22.78, y - 2, 111.42, 12), 7, False, False),   # Date
        (_rl_rect(ML + 168.26, y - 2, 193.51, 12), 7, False, False),  # Topic
    ]
    y -= 20
    out.append((_rl_rect(ML + 4, MB + 20, CW - 8, y - (MB + 20)), 9, True, False))
    return out


def _year_in_pixels_field_rects():
    # geometry mirrors planner_page_adder.py::_draw_specialty_pages "year_in_pixels"
    y = PH - MT - 52 - 16
    y -= 20
    ky2 = y - 24
    out = []
    label_w = 6.930        # "= " @ Poppins 7
    blank_full_w = 63.371  # "= ___________" @ Poppins 7
    for i in range(5):
        bx = ML + 80 + i * 60 + 42 + label_w
        out.append((_rl_rect(bx, ky2 - 8 - 2, blank_full_w - label_w, 10), 6.5, False, False))
    return out


def _class_schedule_field_rects():
    # geometry mirrors planner_page_adder.py::_draw_specialty_pages "class_schedule"
    y = PH - MT - 52 - 16
    y -= 30
    n_days, n_times = 5, 11
    tw = 52.0
    dw = (CW - tw) / n_days
    rh = (y - MB - 30) / n_times
    out = []
    for ri in range(n_times):
        ry = y - 18 - (ri + 1) * rh
        for di in range(n_days):
            cx = ML + tw + di * dw
            out.append((_rl_rect(cx + 2, ry + 2, dw - 4, rh - 4), 6.5, True, False))
    return out


def _priority_matrix_field_rects():
    # geometry mirrors planner_page_adder.py::_draw_specialty_pages "priority_matrix"
    y = PH - MT - 52 - 16
    y -= 20
    out = [(_rl_rect(ML + 41.463, y - 2, 168.48, 12), 8, False, False)]  # Week of
    y -= 22
    qw = CW / 2 - 4
    qh = (y - MB - 30) / 2
    positions = [
        (ML, y - qh),
        (ML + qw + 8, y - qh),
        (ML, y - 2 * qh - 4),
        (ML + qw + 8, y - 2 * qh - 4),
    ]
    line_h = 16
    lines_n = int((qh - 28) / line_h)
    for qx, qy in positions:
        for li in range(lines_n):
            ly = qy + qh - 28 - li * line_h - 4
            out.append((_rl_rect(qx + 10, ly, qw - 20, line_h - 4), 7, False, False))
    return out


def _pomodoro_field_rects():
    # geometry mirrors planner_page_adder.py::_draw_specialty_pages "pomodoro"
    y = PH - MT - 52 - 16
    y -= 22
    session_h = (y - MB - 30) / 8
    out = []
    for si in range(8):
        sy = y - si * session_h
        tx = ML + 66 + 20.738  # "Task: " @ Poppins-Italic 7.5
        out.append((_rl_rect(tx, sy - session_h + 6 - 2, 170.422, 10), 7, False, False))
        for pi in range(4):
            px = ML + CW * 0.42 + 62 + pi * 44
            py = sy - session_h / 2
            r = 13.0
            out.append((_rl_rect(px - r, py - r, 2 * r, 2 * r), 7, False, True))
        bx = ML + CW - 40
        out.append((_rl_rect(bx, sy - session_h + 6, 34, 16), 7, False, True))
    return out


def _debt_payoff_field_rects():
    # geometry mirrors planner_page_adder.py::_draw_specialty_pages "debt_payoff"
    y = PH - MT - 52 - 16
    y -= 22
    col_widths = [90, 70, 55, 65, 55, 60, 50]
    header_h = 18.0
    row_h_debt = 24.0
    rows_n = int((y - MB - 50) / row_h_debt)
    out = []
    for ri in range(rows_n):
        rx = ML
        ry = y - header_h - (ri + 1) * row_h_debt
        for ci, cw2 in enumerate(col_widths):
            if ci == len(col_widths) - 1:
                cx, cy = rx + cw2 / 2.0, ry + row_h_debt / 2.0
                r = min(cw2, row_h_debt) * 0.30
                out.append((_rl_rect(cx - r, cy - r, 2 * r, 2 * r), 7, False, True))
            else:
                out.append((_rl_rect(rx + 3, ry + 3, cw2 - 6, row_h_debt - 6), 7, False, False))
            rx += cw2
    total_y = y - header_h - (rows_n + 1) * row_h_debt
    dollar_x = ML + sum(col_widths[:3]) - 30 + 5.922  # "$" @ Poppins-Bold 9
    out.append((_rl_rect(dollar_x, total_y + 8 - 2, 70.2, 12), 8, False, False))
    vby = total_y - 38
    out.append((_rl_rect(244.807, vby + 16 - 3, 274.56, 14), 9, False, False))  # Debt-Free Date Goal
    return out


_SAVINGS_GOAL_OFFSETS = [
    (39.113, 200.573, 247.274, 331.514, 363.554, 447.794),
    (40.868, 202.328, 249.029, 333.269, 365.309, 449.549),
    (41.174, 202.634, 249.335, 333.575, 365.615, 449.855),
    (41.822, 203.282, 249.983, 334.223, 366.263, 450.503),
]


def _savings_goal_field_rects():
    # geometry mirrors planner_page_adder.py::_draw_specialty_pages "savings_goal"
    y = PH - MT - 52 - 16
    y -= 20
    goal_h = (y - MB - 20) / 4 - 8
    out = []
    for gi in range(4):
        gy = y - gi * (goal_h + 8)
        b1s, b1e, b2s, b2e, b3s, b3e = _SAVINGS_GOAL_OFFSETS[gi]
        base_y = gy - 16
        out.append((_rl_rect(ML + b1s, base_y - 2, b1e - b1s, 12), 8, False, False))
        out.append((_rl_rect(ML + b2s, base_y - 2, b2e - b2s, 12), 8, False, False))
        out.append((_rl_rect(ML + b3s, base_y - 2, b3e - b3s, 12), 8, False, False))
    return out


def _bill_checklist_field_rects():
    # geometry mirrors planner_page_adder.py::_draw_specialty_pages "bill_checklist"
    y = PH - MT - 52 - 16
    y -= 22
    bill_col_w = 110.0
    month_col_w = (CW - bill_col_w) / 12.0
    header_h2 = 16.0
    bill_rows = int((y - MB - 20) / 20)
    out = []
    for ri in range(bill_rows):
        ry = y - header_h2 - (ri + 1) * 20
        out.append((_rl_rect(ML + 3, ry + 3, bill_col_w - 6, 20 - 6), 7, False, False))
        for mi in range(12):
            mx = ML + bill_col_w + mi * month_col_w
            cx, cy = mx + month_col_w / 2.0, ry + 10.0
            r = min(month_col_w, 20) * 0.32
            out.append((_rl_rect(cx - r, cy - r, 2 * r, 2 * r), 6, False, True))
    return out


def _progress_photos_field_rects():
    # geometry mirrors planner_page_adder.py::_draw_specialty_pages "progress_photos"
    y = PH - MT - 52 - 14
    y -= 22
    block_h = (y - MB - 20) / 4 - 8
    label_widths_l = [34.017, 28.883, 27.744, 22.236]   # Weight, Chest, Waist, Hips
    label_widths_r = [26.172, 31.833, 59.373, 54.545]   # Arms, Thighs, Energy, Mood
    BLANK_W = 99.688
    date_label_w = 22.776
    out = []
    for bi in range(4):
        by = y - bi * (block_h + 8)
        out.append((_rl_rect(ML + 160 + date_label_w, by - 16 - 2, BLANK_W, 12), 7, False, False))
        fh = (block_h - 26) / 4.0
        fy = by - 26
        for fi in range(4):
            field_y = fy - fi * fh
            base_y = field_y - fh + 5
            lx = ML + 10 + label_widths_l[fi]
            rx = ML + CW / 2 + 10 + label_widths_r[fi]
            out.append((_rl_rect(lx, base_y - 2, BLANK_W, 12), 7, False, False))
            out.append((_rl_rect(rx, base_y - 2, BLANK_W, 12), 7, False, False))
    return out


def _water_tracker_field_rects():
    # geometry mirrors planner_page_adder.py::_draw_specialty_pages "water_tracker"
    y = PH - MT - 52 - 16
    y -= 20
    out = [
        (_rl_rect(ML + 34.245, y - 2, 209.745 - 34.245, 12), 8, False, False),    # Month
        (_rl_rect(ML + 266.85, y - 2, 315.99 - 266.85, 12), 8, False, False),     # Daily Goal oz
        (_rl_rect(ML + 335.988, y - 2, 385.128 - 335.988, 12), 8, False, False),  # Daily Goal glasses
    ]
    y -= 24
    DROP_ROWS, DROP_COLS = 30, 8
    row_h_w = (y - MB - 30) / DROP_ROWS
    day_label_w = 40.0
    cell_w_w = (CW - day_label_w) / DROP_COLS
    for di in range(DROP_ROWS):
        dy = y - di * row_h_w
        for gi in range(DROP_COLS):
            gx = ML + day_label_w + gi * cell_w_w
            out.append((_rl_rect(gx + 2, dy - row_h_w + 2, cell_w_w - 4, row_h_w - 4), 6, False, True))
    return out


def _sleep_log_field_rects():
    # geometry mirrors planner_page_adder.py::_draw_specialty_pages "sleep_log"
    y = PH - MT - 52 - 16
    y -= 22
    col_ws = [30, 55, 60, 60, 70, 0]
    col_ws[-1] = CW - sum(col_ws[:-1])
    row_h_sl = (y - MB - 20) / 32
    header_h_sl = 18.0
    out = []
    for ri in range(31):
        rx = ML
        ry = y - header_h_sl - (ri + 1) * row_h_sl
        for ci, cw3 in enumerate(col_ws):
            if ci > 0:
                is_notes = ci == len(col_ws) - 1
                out.append((_rl_rect(rx + 3, ry + 3, cw3 - 6, row_h_sl - 6), 8 if is_notes else 7, is_notes, False))
            rx += cw3
    return out


def _nsv_journal_field_rects():
    # geometry mirrors planner_page_adder.py::_draw_specialty_pages "nsv_journal"
    y = PH - MT - 52 - 16
    y -= 22
    n_prompts = 8
    box_h = (y - MB - 20) / n_prompts - 4
    out = []
    for pi in range(n_prompts):
        py = y - pi * (box_h + 4)
        base_y = py - box_h + 8
        out.append((_rl_rect(ML + 8, base_y - 2, 469.12, 12), 8, False, False))
    return out


_FIELD_BUILDERS = {
    "daily": _daily_field_rects,
    "weekly": _weekly_field_rects,
    "brain_dump": _brain_dump_field_rects,
    "goals": _goals_field_rects,
    "habit": _habit_field_rects,
    "monthly_review": _monthly_review_field_rects,
    "month_glance": _month_glance_field_rects,
    "budget": _budget_field_rects,
    "meal_plan": _meal_plan_field_rects,
    "notes": _notes_field_rects,
    "year_in_pixels": _year_in_pixels_field_rects,
    "class_schedule": _class_schedule_field_rects,
    "priority_matrix": _priority_matrix_field_rects,
    "pomodoro": _pomodoro_field_rects,
    "debt_payoff": _debt_payoff_field_rects,
    "savings_goal": _savings_goal_field_rects,
    "bill_checklist": _bill_checklist_field_rects,
    "progress_photos": _progress_photos_field_rects,
    "water_tracker": _water_tracker_field_rects,
    "sleep_log": _sleep_log_field_rects,
    "nsv_journal": _nsv_journal_field_rects,
}


def _classify_page(head):
    h = head.strip()
    if "MONTHLY REVIEW" in h[:40]:
        return "monthly_review"
    if "MONTH AT A GLANCE" in h[:40]:
        return "month_glance"
    if "BUDGET TRACKER" in h[:40]:
        return "budget"
    if "MEAL PLANNER" in h[:40]:
        return "meal_plan"
    if "NOTES" in h[:40] and "PAGE" in h[:40]:
        return "notes"
    if _MONTH_RE.match(h) and "AT A GLANCE" not in h[:40] and "REVIEW" not in h[:40]:
        return "monthly"
    if h.upper().startswith("WEEK "):
        return "weekly"
    if _WEEKDAY_RE.match(h) or h.upper().startswith("DAILY PLAN"):
        return "daily"
    if "BRAIN DUMP" in h[:40]:
        return "brain_dump"
    if "HABIT TRACKER" in h[:40]:
        return "habit"
    if "SMART GOALS" in h[:40]:
        return "goals"
    if "YEAR IN PIXELS" in h[:40]:
        return "year_in_pixels"
    if "CLASS SCHEDULE" in h[:40]:
        return "class_schedule"
    if "PRIORITY MATRIX" in h[:40]:
        return "priority_matrix"
    if "POMODORO" in h[:40]:
        return "pomodoro"
    if "DEBT PAYOFF" in h[:40]:
        return "debt_payoff"
    if "SAVINGS GOAL" in h[:40]:
        return "savings_goal"
    if "BILL PAYMENT" in h[:40]:
        return "bill_checklist"
    if "PROGRESS PHOTOS" in h[:40]:
        return "progress_photos"
    if "WATER INTAKE" in h[:40]:
        return "water_tracker"
    if "SLEEP QUALITY" in h[:40]:
        return "sleep_log"
    if "NON-SCALE VICTORIES" in h[:40]:
        return "nsv_journal"
    return None


def add_fillable_fields(doc, grid_year=None):
    """Add real AcroForm widgets over every guide-line area the v2 generators
    draw. Returns the number of widgets added.

    grid_year: the planner's actual calendar year (always the true year the
    monthly grids were laid out with — even on the "undated" PDF, since the
    generator only hides the year label, not the weekday alignment). Needed
    to place one real field per day cell on monthly pages.
    """
    n = 0
    for i in range(doc.page_count):
        head = doc[i].get_text("text")
        kind = _classify_page(head)
        if kind == "monthly":
            rects = _monthly_field_rects(head, grid_year)
        else:
            builder = _FIELD_BUILDERS.get(kind)
            rects = builder() if builder else []
        page = doc[i]
        for rect, fontsize, multiline, checkbox in rects:
            _widget(page, rect, fontsize=fontsize, multiline=multiline, checkbox=checkbox)
            n += 1
    return n


def _goto(page, rect, target_page0):
    page.insert_link({
        "kind": fitz.LINK_GOTO,
        "from": rect,
        "page": target_page0,
        "to": fitz.Point(0, 0),
    })


# ---------------------------------------------------------------------------
# 4. The dashboard & index geometries (mirrored from planner_page_adder.py)
# ---------------------------------------------------------------------------

ML = MR = 36.0
MT = MB = 32.0
CW = PW - ML - MR


def _dashboard_button_rects(sections_display):
    """Return [(label, fitz.Rect), ...] mirroring the dashboard grid layout."""
    y = PH - 80 - 22 - 18  # = 672
    col_w = (CW - 16) / 3.0
    gap = 8.0
    cols = 3
    x_starts = [ML + i * (col_w + gap) for i in range(cols)]
    row_h = 52.0
    out = []
    for idx, label in enumerate(sections_display):
        col = idx % cols
        row = idx // cols
        bx = x_starts[col]
        by = y - (row + 1) * (row_h + gap)
        out.append((label, _rl_rect(bx, by, col_w, row_h)))
    return out


def _index_row_rects(sections):
    """Return [(label, fitz.Rect), ...] mirroring the two-column index list."""
    y = PH - MT - 52 - 18 - 24  # = 666
    row_h_idx = 20.0
    half = len(sections) // 2 + len(sections) % 2
    col1 = sections[:half]
    col2 = sections[half:]
    col_w = CW / 2 - 8
    out = []
    for i in range(max(len(col1), len(col2))):
        row_y = y - i * row_h_idx
        if i < len(col1):
            out.append((col1[i], fitz.Rect(ML, PH - (row_y + 12), ML + col_w, PH - (row_y - 6))))
        if i < len(col2):
            rx = ML + CW / 2 + 8
            out.append((col2[i], fitz.Rect(rx, PH - (row_y + 12), rx + col_w, PH - (row_y - 6))))
    return out


# ---------------------------------------------------------------------------
# 5. Orchestration
# ---------------------------------------------------------------------------

# Human-friendly outline order + display titles
_TOC_ORDER = [
    ("welcome", "Welcome & Setup"),
    ("dashboard", "Dashboard / Home"),
    ("index", "Planner Index"),
    ("yearly", "Yearly Overview"),
    ("year_in_pixels", "Year in Pixels"),
    ("monthly", "Monthly Calendars"),
    ("monthly_review", "Monthly Reviews"),
    ("glance", "Month at a Glance"),
    ("weekly", "Weekly Spreads"),
    ("daily", "Daily Pages"),
    ("class_schedule", "Class Schedule"),
    ("brain_dump", "Brain Dump"),
    ("priority_matrix", "Priority Matrix"),
    ("pomodoro", "Pomodoro Focus Tracker"),
    ("habit", "Habit Tracker"),
    ("goals", "SMART Goals"),
    ("budget", "Budget Tracker"),
    ("debt_payoff", "Debt Payoff Tracker"),
    ("savings_goal", "Savings Goal Tracker"),
    ("bill_checklist", "Bill Payment Checklist"),
    ("meal", "Meal Planner"),
    ("progress_photos", "Progress Photos Log"),
    ("water_tracker", "30-Day Water Tracker"),
    ("sleep_log", "Sleep Quality Log"),
    ("nsv_journal", "Non-Scale Victories"),
    ("notes", "Notes"),
    ("stickers", "Sticker Library"),
]


def _embed_sticker_sheets(doc, first_sticker_page, sheet_pngs):
    """Replace each Sticker Library page's placeholder grid with the real
    transparent sticker sheet rendered on a clean panel."""
    body = fitz.Rect(ML, 88, PW - MR, 760)  # below header+subtitle, above footer bar
    for offset, png in enumerate(sheet_pngs):
        pno = first_sticker_page + offset
        if pno >= doc.page_count or not Path(png).exists():
            continue
        page = doc[pno]
        # mask the placeholder grid with the moonbeam neutral, then drop the sheet
        page.draw_rect(body, color=None, fill=(MOONBEAM[0] / 255, MOONBEAM[1] / 255, MOONBEAM[2] / 255))
        page.insert_image(body, filename=str(png), keep_proportion=True)


def finalize_pdf(src_path, out_path, sections, title, subtitle, year,
                 cover_png=None, sticker_sheets=None, grid_year=None):
    doc = fitz.open(str(src_path))

    found = _detect_sections(doc)
    dash_page = found.get("dashboard")

    # --- embed real sticker sheets over the placeholder library pages ---
    if sticker_sheets and "stickers" in found:
        _embed_sticker_sheets(doc, found["stickers"], sticker_sheets)

    # --- swap in the celestial cover (delete the text placeholder page 0) ---
    if cover_png and Path(cover_png).exists():
        if doc.page_count and doc[0].get_text("text").strip().lower().startswith(
                ("[cover", "ultimate", "celestial")) or doc.page_count:
            # page 0 from --no-cover is the plain text cover; replace it
            doc.delete_page(0)
        cover = fitz.open()
        cpage = cover.new_page(width=PW, height=PH)
        cpage.insert_image(fitz.Rect(0, 0, PW, PH), filename=str(cover_png))
        doc.insert_pdf(cover, start_at=0)
        cover.close()
        # page indices are preserved (deleted 1, inserted 1 at front)

    # --- build the document outline / TOC ---
    toc = []
    for key, disp in _TOC_ORDER:
        if key in found:
            toc.append([1, disp, found[key] + 1])  # set_toc is 1-based
    if toc:
        doc.set_toc(toc)

    # --- dashboard buttons -> section pages ---
    if dash_page is not None:
        display = [s for s in sections
                   if s not in ("Welcome & Setup", "Dashboard / Home", "Planner Index")]
        for label, rect in _dashboard_button_rects(display):
            key = _label_to_key(label)
            if key and key in found:
                _goto(doc[dash_page], rect, found[key])

    # --- index rows -> section pages ---
    if "index" in found:
        ipage = found["index"]
        for label, rect in _index_row_rects(sections):
            key = _label_to_key(label)
            if key and key in found:
                _goto(doc[ipage], rect, found[key])

    # --- real fillable AcroForm widgets over every guide-line area ---
    n_fields = add_fillable_fields(doc, grid_year=grid_year)

    # --- HOME / PREV / NEXT footer on every non-cover page ---
    last = doc.page_count - 1
    for i in range(1, doc.page_count):  # skip cover (page 0)
        page = doc[i]
        foot = fitz.Rect(0, PH - 24, PW, PH)  # bottom 24px bar
        # left third -> PREV, center third -> HOME, right third -> NEXT
        third = PW / 3.0
        if i > 1:
            _goto(page, fitz.Rect(foot.x0, foot.y0, third, foot.y1), max(1, i - 1))
        if dash_page is not None:
            _goto(page, fitz.Rect(third, foot.y0, 2 * third, foot.y1), dash_page)
        if i < last:
            _goto(page, fitz.Rect(2 * third, foot.y0, foot.x1, foot.y1), i + 1)

    doc.save(str(out_path), garbage=4, deflate=True)
    n = doc.page_count
    doc.close()
    return n, len(toc), n_fields


def finalize(pid, make_cover=True):
    pcfg_sections, title, subtitle, year, theme_rgb, accent_rgb, bg_rgb, dark_rgb = _load_cfg(pid)

    # DP1034 already owns the exact Celestial Night look this gradient was designed
    # for, using a 3-tone gradient that can't be losslessly reconstructed from just
    # the 4 generic theme colors -- so leave it on the hardcoded defaults untouched.
    if pid == "DP1034":
        theme_rgb = accent_rgb = bg_rgb = dark_rgb = None

    cover_png = None
    if make_cover:
        cover_png = PRODUCT_FILES_DIR / f"{pid}_cover.png"
        ai_cover = PRODUCT_FILES_DIR / f"{pid}_cover_ai.png"
        if ai_cover.exists():
            compose_ai_cover(ai_cover, cover_png, title, subtitle, year,
                              theme_rgb=theme_rgb, accent_rgb=accent_rgb,
                              bg_rgb=bg_rgb, dark_rgb=dark_rgb)
            print(f"  Cover (AI-composited) -> {cover_png}")
        else:
            build_cover_png(cover_png, title, subtitle, year,
                             theme_rgb=theme_rgb, accent_rgb=accent_rgb,
                             bg_rgb=bg_rgb, dark_rgb=dark_rgb)
            print(f"  Cover (PIL) -> {cover_png}")

    # real sticker sheets, if they've been generated
    sticker_sheets = [PRODUCT_FILES_DIR / f"{pid}_sticker_sheet_{n}.png" for n in range(1, 6)]
    sticker_sheets = [p for p in sticker_sheets if p.exists()]
    if sticker_sheets:
        print(f"  Embedding {len(sticker_sheets)} real sticker sheets into the library pages")

    results = []
    for suffix, yr in ((f"{pid}_v2.pdf", year), (f"{pid}U_v2.pdf", None)):
        src = PRODUCT_FILES_DIR / suffix
        if not src.exists():
            print(f"  (skip {suffix} — not found)")
            continue
        out = PRODUCT_FILES_DIR / suffix.replace("_v2.pdf", "_v2_final.pdf")
        n, ntoc, nfields = finalize_pdf(src, out, pcfg_sections, title, subtitle, yr,
                               cover_png=cover_png, sticker_sheets=sticker_sheets,
                               grid_year=year)
        print(f"  {out.name}: {n} pages, {ntoc} outline entries, {nfields} real fillable fields")
        results.append(out)
    return results


def _load_cfg(pid):
    if str(_BASE_DIR) not in sys.path:
        sys.path.insert(0, str(_BASE_DIR))
    from tools.generate_planner_v2 import _normalize_cfg
    pcfg, _meta = _normalize_cfg(pid)
    return (pcfg["sections"], pcfg["title"], pcfg["subtitle"], pcfg.get("year"),
            pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"])


def main():
    ap = argparse.ArgumentParser(description="Add a cover + real hyperlink navigation to a v2 planner PDF.")
    ap.add_argument("pid")
    ap.add_argument("--no-cover", action="store_true")
    args = ap.parse_args()
    finalize(args.pid.upper(), make_cover=not args.no_cover)


if __name__ == "__main__":
    main()
