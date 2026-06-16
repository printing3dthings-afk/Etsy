"""
generate_planner_v2.py — Redesigned, "smart", dimensional digital planner builder.

Why this exists: the v1 planners (generate_planner.py + planner_page_adder.py)
are functional but flat — solid color blocks, blank lined boxes, no sense of a
physical notebook, and no real life-improvement tooling beyond static grids.
This v2 module keeps every v1 page generator that is already good (yearly
overview, monthly review, month-at-a-glance, budget, meal plan, lesson plans,
class rosters, notes, sticker library, cover page/image, nav pages) and
replaces or adds the weak spots:

  - Weekly + monthly pages get a gradient header, spiral-binding rings down
    the left margin, drop-shadowed boxes, and built-in mood/water/energy
    tracker widgets (visual depth + "smart planner" functionality).
  - Brand-new daily (hour-by-hour) pages — the single most requested missing
    feature across every product.
  - Brand-new universal Brain Dump → Priority Matrix pages.
  - Goals page upgraded to a full SMART framework (Specific / Measurable /
    Achievable / Relevant / Time-bound) across 2 pages, 4 goals total.
  - Habit tracker upgraded with binding/shadow treatment to match the rest.

Run standalone, e.g.:
    python tools/generate_planner_v2.py DP1026
    python tools/generate_planner_v2.py --all
    python tools/generate_planner_v2.py --list
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import calendar as _cal

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.generate_planner import (
    PLANNER_CONFIGS,
    PRODUCT_FILES_DIR,
    SHOP_NAME,
    _MONTHS,
    _DAYS_S,
    _get_fn,
    _bl,
    _new_canvas,
    _page_bg,
    _ML,
    _MR,
    _MB,
    _gen_yearly_overview,
    _gen_monthly_review_pages,
    _gen_month_at_a_glance,
    _gen_notes_pages,
    _gen_sticker_library,
    _gen_budget_page,
    _gen_meal_plan_page,
    _gen_lesson_plan_pages,
    _gen_class_roster_pages,
    _make_cover_page,
    _generate_cover_image,
    _merge_pdfs,
)
from tools.planner_page_adder import PLANNERS, _make_pages


# ---------------------------------------------------------------------------
# Visual helpers — these are what make v2 look "physical" and "smart"
# ---------------------------------------------------------------------------

def _gradient_header(c, label, T, A, BG, fn, PW, PH, sub="", h=58.0):
    """Theme->accent gradient band (depth) instead of v1's flat single-color band."""
    y0 = PH - h
    steps = 28
    seg_w = PW / float(steps)
    for i in range(steps):
        f = i / float(steps - 1)
        rgb = tuple(T[j] + (A[j] - T[j]) * f for j in range(3))
        c.setFillColorRGB(*rgb)
        c.rect(i * seg_w, y0, seg_w + 0.5, h, fill=1, stroke=0)
    if hasattr(c, "setFillAlpha"):
        c.setFillAlpha(0.16)
    c.setFillColorRGB(0, 0, 0)
    c.rect(0, y0 - 5, PW, 5, fill=1, stroke=0)
    if hasattr(c, "setFillAlpha"):
        c.setFillAlpha(1.0)
    c.setFillColorRGB(1, 1, 1)
    if sub:
        c.setFont(fn("bold"), 16)
        c.drawCentredString(PW / 2.0, y0 + h * 0.60, label)
        c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2.0, y0 + h * 0.28, sub)
    else:
        c.setFont(fn("bold"), 18)
        c.drawCentredString(PW / 2.0, y0 + h * 0.40, label)


def _shadow_box(c, x, y, w, h, r=6.0):
    """Soft drop shadow behind a box — gives the page a sense of depth/dimension."""
    if hasattr(c, "setFillAlpha"):
        c.setFillAlpha(0.10)
        c.setFillColorRGB(0, 0, 0)
        c.roundRect(x + 2.2, y - 2.2, w, h, r, fill=1, stroke=0)
        c.setFillAlpha(1.0)
    else:
        c.setFillColorRGB(0.85, 0.85, 0.85)
        c.roundRect(x + 2.2, y - 2.2, w, h, r, fill=1, stroke=0)


def _draw_binding(c, BG, PH, x=15.0, top=78.0, bottom=40.0, spacing=26.0):
    """Simulated spiral-bound ring holes down the left margin — makes the page
    look like a physical notebook you could hold, not a flat PDF."""
    if hasattr(c, "setFillAlpha"):
        c.setFillAlpha(0.07)
    c.setFillColorRGB(0, 0, 0)
    c.rect(x + 8, bottom, 10, PH - top - bottom, fill=1, stroke=0)
    if hasattr(c, "setFillAlpha"):
        c.setFillAlpha(1.0)
    y = PH - top
    while y > bottom:
        c.setFillColorRGB(1, 1, 1)
        c.circle(x, y, 4.2, fill=1, stroke=0)
        c.setLineWidth(0.8)
        c.setStrokeColorRGB(0.55, 0.55, 0.55)
        c.circle(x, y, 4.2, fill=0, stroke=1)
        c.setFillColorRGB(0.75, 0.75, 0.75)
        c.circle(x, y, 1.6, fill=1, stroke=0)
        y -= spacing


def _textured_bg(c, BG, PW, PH, step=22.0):
    """Extremely subtle dot texture over the page background — paper feel."""
    shade = tuple(max(0.0, v - 0.012) for v in BG)
    c.setFillColorRGB(*shade)
    y = 0.0
    while y < PH:
        x = 0.0
        while x < PW:
            c.circle(x, y, 0.5, fill=1, stroke=0)
            x += step
        y += step


def _section_tag(c, fn, x, y, w, h, text, fill_rgb, text_rgb=None, size=7.0):
    c.setFillColorRGB(*fill_rgb)
    c.roundRect(x, y, w, h, h / 2.0, fill=1, stroke=0)
    c.setFillColorRGB(*(text_rgb or (1, 1, 1)))
    c.setFont(fn("bold"), size)
    c.drawCentredString(x + w / 2.0, y + h / 2.0 - size * 0.35, text)


def _mood_faces(c, fn, x, y, w, T, DK, r=8.5):
    """A row of 5 simple mood-face circles — daily/weekly emotional check-in."""
    labels = ["SAD", "MEH", "OK", "GOOD", "GREAT"]
    n = len(labels)
    gap = w / float(n)
    for i, lbl in enumerate(labels):
        cx = x + gap * i + gap / 2.0
        c.setLineWidth(1.1)
        c.setStrokeColorRGB(*T)
        c.setFillColorRGB(1, 1, 1)
        c.circle(cx, y, r, fill=1, stroke=1)
        c.setFillColorRGB(*DK)
        c.circle(cx - r * 0.35, y + r * 0.2, 0.7, fill=1, stroke=0)
        c.circle(cx + r * 0.35, y + r * 0.2, 0.7, fill=1, stroke=0)
        c.setLineWidth(0.7)
        c.setStrokeColorRGB(*DK)
        c.line(cx - r * 0.35, y - r * 0.25, cx, y - r * 0.45)
        c.line(cx, y - r * 0.45, cx + r * 0.35, y - r * 0.25)
        c.setFont(fn("default"), 5.2)
        c.setFillColorRGB(*T)
        c.drawCentredString(cx, y - r - 8, lbl)


def _water_drops(c, x, y, w, n, T):
    """Outline teardrops to check off — daily water-intake tracker."""
    gap = w / float(n)
    r = min(6.0, gap * 0.32)
    for i in range(n):
        cx = x + gap * i + gap / 2.0
        c.setFillColorRGB(*T)
        c.setStrokeColorRGB(*T)
        c.setLineWidth(0.8)
        p = c.beginPath()
        p.moveTo(cx, y + r * 1.8)
        p.lineTo(cx - r * 0.85, y + r * 0.55)
        p.lineTo(cx + r * 0.85, y + r * 0.55)
        p.close()
        c.drawPath(p, fill=0, stroke=1)
        c.circle(cx, y - r * 0.15, r * 0.85, fill=0, stroke=1)


def _energy_bolts(c, x, y, w, n, T):
    """Outline lightning bolts to check off — daily/weekly energy-level tracker."""
    gap = w / float(n)
    s = min(10.0, gap * 0.5)
    for i in range(n):
        cx = x + gap * i + gap / 2.0
        c.setFillColorRGB(*T)
        c.setStrokeColorRGB(*T)
        c.setLineWidth(0.8)
        p = c.beginPath()
        p.moveTo(cx + s * 0.18, y + s)
        p.lineTo(cx - s * 0.35, y + s * 0.15)
        p.lineTo(cx + s * 0.05, y + s * 0.15)
        p.lineTo(cx - s * 0.18, y - s)
        p.lineTo(cx + s * 0.35, y + s * 0.05)
        p.lineTo(cx - s * 0.05, y + s * 0.05)
        p.close()
        c.drawPath(p, fill=0, stroke=1)


def _smart_footer(c, T, A, BG, fn, PW, prev_lbl="", next_lbl=""):
    """Replaces v1's plain copyright footer with PREV / HOME / NEXT nav styling."""
    h = 24.0
    c.setFillColorRGB(*T)
    c.rect(0, 0, PW, h, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(fn("default"), 7.5)
    c.drawString(10, h / 2.0 - 2.6, "<  " + (prev_lbl or "PREV"))
    c.drawCentredString(PW / 2.0, h / 2.0 - 2.6, "HOME  -  " + SHOP_NAME)
    c.drawRightString(PW - 10, h / 2.0 - 2.6, (next_lbl or "NEXT") + "  >")


# ---------------------------------------------------------------------------
# New / upgraded page generators
# ---------------------------------------------------------------------------

def _v2_weekly_pages(pcfg, dated=True):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    title = pcfg["title"]
    year = pcfg.get("year")
    chunks = []
    week_starts = [None] * 52
    if dated and year:
        jan1 = date(year, 1, 1)
        first_monday = jan1 - timedelta(days=jan1.weekday())
        week_starts = [first_monday + timedelta(weeks=w) for w in range(52)]

    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    for w in range(52):
        c, buf, PW, PH = _new_canvas()
        fn = _get_fn()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        sub = ""
        if week_starts[w]:
            ws = week_starts[w]
            we = ws + timedelta(days=6)
            sub = f"{ws.strftime('%b %d')} - {we.strftime('%b %d, %Y')}"
        _gradient_header(c, f"WEEK {w + 1}", T, A, BG, fn, PW, PH, sub=sub or title)

        ML = _ML + 26
        top = PH - 58 - 14
        notes_w = (PW - _MR - ML) * 0.20
        day_area_w = (PW - _MR - ML) - notes_w - 6
        day_w = day_area_w / 7.0
        grid_top = top - 4
        grid_bottom = 70.0
        hdr_h = 20.0

        for di, dname in enumerate(days):
            dx = ML + di * day_w
            weekend = di >= 5
            c.setFillColorRGB(*(_bl(A, 0.55) if weekend else T))
            c.rect(dx, grid_top - hdr_h, day_w - 1.5, hdr_h, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont(fn("bold"), 7.5)
            label = dname
            if week_starts[w]:
                dd = week_starts[w] + timedelta(days=di)
                label = f"{dname} {dd.day}"
            c.drawCentredString(dx + day_w / 2.0, grid_top - hdr_h + 6, label)

        body_top = grid_top - hdr_h
        body_h = body_top - grid_bottom
        for di in range(7):
            dx = ML + di * day_w
            weekend = di >= 5
            c.setFillColorRGB(*(_bl(A, 0.93) if weekend else (1, 1, 1)))
            c.rect(dx, grid_bottom, day_w - 1.5, body_h, fill=1, stroke=0)
            c.setStrokeColorRGB(*_bl(DK, 0.7))
            c.setLineWidth(0.4)
            yy = grid_bottom + 14
            while yy < body_top - 4:
                c.line(dx + 2, yy, dx + day_w - 4, yy)
                yy += 14
            c.setStrokeColorRGB(*T)
            c.setLineWidth(0.8)
            c.line(dx + day_w - 1.5, grid_bottom, dx + day_w - 1.5, body_top)

        nx = ML + day_area_w + 6
        full_h = grid_top - grid_bottom
        _shadow_box(c, nx, grid_bottom, notes_w, full_h)
        c.setFillColorRGB(*_bl(T, 0.88))
        c.roundRect(nx, grid_bottom, notes_w, full_h, 6, fill=1, stroke=0)
        c.setFillColorRGB(*T)
        c.setFont(fn("bold"), 8)
        c.drawString(nx + 6, grid_top - 16, "TOP 3")
        for i in range(3):
            cy = grid_top - 30 - i * 14
            c.setStrokeColorRGB(*T)
            c.setLineWidth(0.9)
            c.roundRect(nx + 6, cy - 4, 7, 7, 1.5, fill=0, stroke=1)
            c.setStrokeColorRGB(*_bl(DK, 0.5))
            c.line(nx + 18, cy, nx + notes_w - 6, cy)
        c.setFont(fn("bold"), 8)
        c.drawString(nx + 6, grid_top - 84, "NOTES")
        yy = grid_top - 98
        while yy > grid_bottom + 6:
            c.setStrokeColorRGB(*_bl(DK, 0.5))
            c.setLineWidth(0.4)
            c.line(nx + 6, yy, nx + notes_w - 6, yy)
            yy -= 13

        wy = grid_bottom - 30
        c.setFillColorRGB(*T)
        c.setFont(fn("bold"), 7.5)
        c.drawString(ML, wy + 14, "MOOD")
        _mood_faces(c, fn, ML + 38, wy + 8, 150, T, DK, r=6.0)
        c.drawString(ML + 210, wy + 14, "WATER")
        _water_drops(c, ML + 254, wy + 8, 90, 7, T)
        c.drawString(ML + 360, wy + 14, "ENERGY")
        _energy_bolts(c, ML + 410, wy + 12, 80, 5, T)

        _smart_footer(c, T, A, BG, fn, PW, prev_lbl=f"WK {w}", next_lbl=f"WK {w + 2}")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


def _v2_monthly_pages(pcfg, dated=True):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    year = pcfg.get("year")
    specialty = pcfg.get("specialty", "")
    teacher = "teacher" in str(specialty).lower()
    month_order = (list(range(8, 13)) + list(range(1, 8))) if teacher else list(range(1, 13))
    chunks = []
    for mi in month_order:
        c, buf, PW, PH = _new_canvas()
        fn = _get_fn()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        mname = _MONTHS[mi - 1]
        yr_label = str(year) if (dated and year) else ""
        _gradient_header(c, f"{mname} {yr_label}".strip(), T, A, BG, fn, PW, PH)

        ML = _ML + 26
        top = PH - 58 - 14
        grid_bottom = 86.0
        days_hdr_h = 18.0
        dw = (PW - _MR - ML) / 7.0
        for di, dname in enumerate(_DAYS_S):
            dx = ML + di * dw
            weekend = di >= 5
            c.setFillColorRGB(*(_bl(A, 0.5) if weekend else T))
            c.rect(dx, top - days_hdr_h, dw - 1.2, days_hdr_h, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont(fn("bold"), 7.5)
            c.drawCentredString(dx + dw / 2.0, top - days_hdr_h + 5, dname)

        cal_year = year if year else date.today().year
        first_wd, n_days = _cal.monthrange(cal_year, mi)
        n_rows = 6
        row_h = (top - days_hdr_h - grid_bottom) / float(n_rows)
        day_num = 1
        for r in range(n_rows):
            for col in range(7):
                idx = r * 7 + col
                cx0 = ML + col * dw
                cy0 = top - days_hdr_h - (r + 1) * row_h
                weekend = col >= 5
                c.setFillColorRGB(*(_bl(A, 0.92) if weekend else (1, 1, 1)))
                c.rect(cx0, cy0, dw - 1.2, row_h - 1.2, fill=1, stroke=0)
                c.setStrokeColorRGB(*_bl(DK, 0.6))
                c.setLineWidth(0.4)
                c.rect(cx0, cy0, dw - 1.2, row_h - 1.2, fill=0, stroke=1)
                if idx >= first_wd and day_num <= n_days:
                    c.setFillColorRGB(*T)
                    c.circle(cx0 + 11, cy0 + row_h - 11, 8, fill=1, stroke=0)
                    c.setFillColorRGB(1, 1, 1)
                    c.setFont(fn("bold"), 7.5)
                    c.drawCentredString(cx0 + 11, cy0 + row_h - 13.5, str(day_num))
                    day_num += 1

        c.setFillColorRGB(*T)
        c.setFont(fn("bold"), 8)
        c.drawString(ML, grid_bottom - 14, "MONTH MOOD")
        _mood_faces(c, fn, ML + 76, grid_bottom - 20, 160, T, DK, r=6.0)
        c.setFont(fn("bold"), 8)
        c.drawString(ML + 250, grid_bottom - 14, "NOTES")
        c.setStrokeColorRGB(*_bl(DK, 0.55))
        c.setLineWidth(0.5)
        c.line(ML + 250, grid_bottom - 24, PW - _MR, grid_bottom - 24)
        c.line(ML + 250, grid_bottom - 40, PW - _MR, grid_bottom - 40)

        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="MONTH", next_lbl="MONTH")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


def _v2_daily_pages(pcfg, dated=True, count=31):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    title = pcfg["title"]
    year = pcfg.get("year")
    chunks = []
    start = date(year, 1, 1) if (dated and year) else None
    hours = list(range(6, 23))  # 6am - 10pm

    for d in range(count):
        c, buf, PW, PH = _new_canvas()
        fn = _get_fn()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        date_label = "DAILY PLAN"
        if start:
            day = start + timedelta(days=d)
            date_label = day.strftime("%A, %B %d").upper()
        _gradient_header(c, date_label, T, A, BG, fn, PW, PH, sub=title)

        ML = _ML + 26
        top = PH - 58 - 14
        col_split = ML + (PW - _MR - ML) * 0.66

        box_y = top - 46
        _shadow_box(c, ML, box_y, col_split - ML - 8, 46)
        c.setFillColorRGB(*_bl(T, 0.88))
        c.roundRect(ML, box_y, col_split - ML - 8, 46, 6, fill=1, stroke=0)
        c.setFillColorRGB(*T)
        c.setFont(fn("bold"), 9)
        c.drawString(ML + 8, box_y + 34, "TOP 3 PRIORITIES")
        for i in range(3):
            cy = box_y + 22 - i * 9
            c.setStrokeColorRGB(*T)
            c.setLineWidth(0.9)
            c.roundRect(ML + 8, cy - 4, 8, 8, 1.5, fill=0, stroke=1)
            c.setStrokeColorRGB(*_bl(DK, 0.5))
            c.line(ML + 22, cy, col_split - 16, cy)

        rx = col_split
        rw = PW - _MR - rx
        c.setFillColorRGB(*_bl(A, 0.85))
        c.roundRect(rx, box_y, rw, 46, 6, fill=1, stroke=0)
        c.setFillColorRGB(*T)
        c.setFont(fn("bold"), 7.5)
        c.drawCentredString(rx + rw / 2.0, box_y + 36, "MOOD")
        _mood_faces(c, fn, rx + 6, box_y + 14, rw - 12, T, DK, r=6.0)

        sched_top = box_y - 12
        sched_bottom = 96.0
        row_h = (sched_top - sched_bottom) / float(len(hours))
        time_col_w = 46.0
        for i, hr in enumerate(hours):
            ry = sched_top - (i + 1) * row_h
            if i % 2 == 0:
                c.setFillColorRGB(*_bl(T, 0.93))
                c.rect(ML, ry, PW - _MR - ML, row_h, fill=1, stroke=0)
            label = f"{hr if hr <= 12 else hr - 12}:00 {'AM' if hr < 12 else 'PM'}"
            c.setFillColorRGB(*DK)
            c.setFont(fn("default"), 7)
            c.drawString(ML + 4, ry + row_h / 2.0 - 2.5, label)
            c.setStrokeColorRGB(*_bl(DK, 0.6))
            c.setLineWidth(0.5)
            c.line(ML + time_col_w, ry, PW - _MR, ry)
        c.setStrokeColorRGB(*T)
        c.setLineWidth(1.0)
        c.line(ML + time_col_w, sched_bottom, ML + time_col_w, sched_top)

        wy = sched_bottom - 20
        c.setFillColorRGB(*T)
        c.setFont(fn("bold"), 7.5)
        c.drawString(ML, wy + 14, "WATER")
        _water_drops(c, ML + 46, wy + 8, 130, 8, T)
        c.drawString(ML + 200, wy + 14, "ENERGY")
        _energy_bolts(c, ML + 250, wy + 12, 90, 5, T)

        gy = wy - 22
        c.setFillColorRGB(*A)
        c.setFont(fn("italic"), 8)
        c.drawString(ML, gy + 8, "Grateful for:")
        c.setStrokeColorRGB(*_bl(DK, 0.55))
        c.setLineWidth(0.6)
        c.line(ML + 70, gy + 6, PW - _MR, gy + 6)

        _smart_footer(c, T, A, BG, fn, PW, prev_lbl=f"DAY {d}", next_lbl=f"DAY {d + 2}")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


def _v2_brain_dump_pages(pcfg, count=4):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    chunks = []
    quads = [
        ("DO NOW", "Urgent + Important", T),
        ("SCHEDULE", "Important, Not Urgent", A),
        ("DELEGATE", "Urgent, Not Important", _bl(T, 0.3)),
        ("ELIMINATE", "Neither", _bl(A, 0.3)),
    ]
    for i in range(count):
        c, buf, PW, PH = _new_canvas()
        fn = _get_fn()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        _gradient_header(c, "BRAIN DUMP", T, A, BG, fn, PW, PH, sub="Get it all out, then sort it below")

        ML = _ML + 26
        top = PH - 58 - 14
        dump_h = (top - _MB) * 0.52
        dump_y = top - dump_h
        _shadow_box(c, ML, dump_y, PW - _MR - ML, dump_h)
        c.setFillColorRGB(1, 1, 1)
        c.roundRect(ML, dump_y, PW - _MR - ML, dump_h, 8, fill=1, stroke=0)
        c.setStrokeColorRGB(*T)
        c.setLineWidth(1.2)
        c.roundRect(ML, dump_y, PW - _MR - ML, dump_h, 8, fill=0, stroke=1)
        dot_sp = 16.0
        c.setFillColorRGB(*_bl(T, 0.85))
        yy = dump_y + dump_h - 14
        while yy > dump_y + 8:
            xx = ML + 10
            while xx < PW - _MR - 10:
                c.circle(xx, yy, 0.6, fill=1, stroke=0)
                xx += dot_sp
            yy -= dot_sp

        mx_top = dump_y - 14
        mx_h = mx_top - _MB - 16
        mx_w = PW - _MR - ML
        qw, qh = mx_w / 2.0, mx_h / 2.0
        c.setFillColorRGB(*T)
        c.setFont(fn("bold"), 9)
        c.drawString(ML, mx_top + 2, "SORT IT: PRIORITY MATRIX")
        for qi, (label, sub, color) in enumerate(quads):
            qx = ML + (qi % 2) * qw
            qy = mx_top - mx_h + (1 - qi // 2) * qh
            c.setFillColorRGB(*_bl(color, 0.82))
            c.roundRect(qx + 3, qy + 3, qw - 6, qh - 6, 6, fill=1, stroke=0)
            c.setStrokeColorRGB(*color)
            c.setLineWidth(1.0)
            c.roundRect(qx + 3, qy + 3, qw - 6, qh - 6, 6, fill=0, stroke=1)
            c.setFillColorRGB(*DK)
            c.setFont(fn("bold"), 8.5)
            c.drawString(qx + 12, qy + qh - 18, label)
            c.setFont(fn("italic"), 6.5)
            c.drawString(qx + 12, qy + qh - 28, sub)
            for li in range(3):
                ly = qy + qh - 42 - li * 11
                c.setStrokeColorRGB(*_bl(DK, 0.55))
                c.setLineWidth(0.5)
                c.line(qx + 12, ly, qx + qw - 14, ly)

        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="DUMP", next_lbl="DUMP")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


def _v2_smart_goals_pages(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    letters = [
        ("S", "SPECIFIC", "What exactly do you want to achieve?"),
        ("M", "MEASURABLE", "How will you know you got there?"),
        ("A", "ACHIEVABLE", "Is this realistic with your resources?"),
        ("R", "RELEVANT", "Why does this goal matter to you?"),
        ("T", "TIME-BOUND", "What is your target date?"),
    ]
    goal_groups = [
        [("GOAL 1", T), ("GOAL 2", A)],
        [("GOAL 3", _bl(T, 0.25)), ("GOAL 4", _bl(A, 0.25))],
    ]

    def quad_page(pair, page_no):
        c, buf, PW, PH = _new_canvas()
        fn = _get_fn()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        _gradient_header(c, "SMART GOALS", T, A, BG, fn, PW, PH, sub=f"Page {page_no} of 2")
        ML = _ML + 26
        top = PH - 58 - 14
        col_w = (PW - _MR - ML - 14) / 2.0
        for gi, (gname, gcolor) in enumerate(pair):
            gx = ML + gi * (col_w + 14)
            gh = top - _MB
            _shadow_box(c, gx, _MB, col_w, gh)
            c.setFillColorRGB(1, 1, 1)
            c.roundRect(gx, _MB, col_w, gh, 8, fill=1, stroke=0)
            c.setStrokeColorRGB(*gcolor)
            c.setLineWidth(1.3)
            c.roundRect(gx, _MB, col_w, gh, 8, fill=0, stroke=1)
            c.setFillColorRGB(*gcolor)
            c.roundRect(gx, _MB + gh - 26, col_w, 26, 8, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont(fn("bold"), 11)
            c.drawCentredString(gx + col_w / 2.0, _MB + gh - 18, gname)
            row_h = (gh - 26) / float(len(letters))
            for li, (letter, label, prompt) in enumerate(letters):
                ry = _MB + gh - 26 - (li + 1) * row_h
                c.setFillColorRGB(*_bl(gcolor, 0.9))
                c.circle(gx + 16, ry + row_h - 12, 9, fill=1, stroke=0)
                c.setFillColorRGB(1, 1, 1)
                c.setFont(fn("bold"), 9)
                c.drawCentredString(gx + 16, ry + row_h - 15, letter)
                c.setFillColorRGB(*DK)
                c.setFont(fn("bold"), 7.5)
                c.drawString(gx + 30, ry + row_h - 10, label)
                c.setFont(fn("italic"), 6)
                c.drawString(gx + 30, ry + row_h - 19, prompt)
                c.setStrokeColorRGB(*_bl(DK, 0.55))
                c.setLineWidth(0.5)
                c.line(gx + 30, ry + 6, gx + col_w - 10, ry + 6)
        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="GOALS", next_lbl="GOALS")
        c.showPage()
        c.save()
        return buf.getvalue()

    chunk1 = quad_page(goal_groups[0], 1)
    chunk2 = quad_page(goal_groups[1], 2)
    return _merge_pdfs(chunk1, chunk2)


def _v2_habit_tracker(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    c, buf, PW, PH = _new_canvas()
    fn = _get_fn()
    _page_bg(c, BG, PW, PH)
    _textured_bg(c, BG, PW, PH)
    _draw_binding(c, BG, PH)
    _gradient_header(c, "HABIT TRACKER", T, A, BG, fn, PW, PH, sub="Small daily wins, big monthly change")

    ML = _ML + 26
    top = PH - 58 - 14
    c.setFillColorRGB(*DK)
    c.setFont(fn("default"), 8)
    c.drawString(ML, top - 10, "Month: __________      Goal: __________________________")

    habit_col_w = 92.0
    n_habits = 8
    grid_top = top - 28
    grid_bottom = 92.0
    day_col_w = (PW - _MR - ML - habit_col_w) / 31.0
    row_h = (grid_top - grid_bottom) / float(n_habits + 1)

    c.setFillColorRGB(*T)
    c.rect(ML, grid_top - row_h, habit_col_w, row_h, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(fn("bold"), 7.5)
    c.drawCentredString(ML + habit_col_w / 2.0, grid_top - row_h + row_h / 2.0 - 3, "HABIT")
    for d in range(31):
        dx = ML + habit_col_w + d * day_col_w
        c.setFillColorRGB(*(_bl(A, 0.6) if d % 7 in (5, 6) else T))
        c.rect(dx, grid_top - row_h, day_col_w - 0.6, row_h, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(fn("bold"), 5.6)
        c.drawCentredString(dx + day_col_w / 2.0, grid_top - row_h + row_h / 2.0 - 2, str(d + 1))

    for h in range(n_habits):
        ry = grid_top - (h + 2) * row_h
        shade = _bl(T, 0.93) if h % 2 == 0 else (1, 1, 1)
        c.setFillColorRGB(*shade)
        c.rect(ML, ry, habit_col_w, row_h, fill=1, stroke=0)
        c.setStrokeColorRGB(*_bl(DK, 0.5))
        c.setLineWidth(0.4)
        c.line(ML + 6, ry + 4, ML + habit_col_w - 6, ry + 4)
        for d in range(31):
            dx = ML + habit_col_w + d * day_col_w
            c.setFillColorRGB(*shade)
            c.rect(dx, ry, day_col_w - 0.6, row_h, fill=1, stroke=0)
            c.setStrokeColorRGB(*_bl(DK, 0.4))
            c.setLineWidth(0.3)
            c.circle(dx + day_col_w / 2.0, ry + row_h / 2.0, min(day_col_w, row_h) * 0.28, fill=0, stroke=1)

    legend_y = grid_bottom - 24
    c.setFillColorRGB(*DK)
    c.setFont(fn("default"), 7)
    c.drawString(ML, legend_y + 10, "Key:")
    swatches = [("Done", T), ("Partial", A), ("Missed", (0.65, 0.65, 0.65))]
    sx = ML + 32
    for lbl, col in swatches:
        c.setFillColorRGB(*col)
        c.circle(sx, legend_y + 13, 5, fill=1, stroke=0)
        c.setFillColorRGB(*DK)
        c.setFont(fn("default"), 7)
        c.drawString(sx + 9, legend_y + 10, lbl)
        sx += 70

    _smart_footer(c, T, A, BG, fn, PW, prev_lbl="HABIT", next_lbl="GOALS")
    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Config normalization — bridges PLANNER_CONFIGS (DP1030-1033) and
# PLANNERS (DP1026-1029) into one pcfg shape used by every generator above.
# ---------------------------------------------------------------------------

_LEGACY_PIDS = {"DP1026", "DP1027", "DP1028", "DP1029"}

_LEGACY_META = {
    "DP1026": {"price": 14.99, "listing_title": "Digital Planner 2026 Undated, GoodNotes iPad, Instant Download"},
    "DP1027": {"price": 9.99, "listing_title": "Kawaii Student Planner 2026, GoodNotes iPad, Instant Download"},
    "DP1028": {"price": 12.99, "listing_title": "Digital Budget Planner 2026 Undated, GoodNotes, Instant Download"},
    "DP1029": {"price": 12.99, "listing_title": "Digital Fitness Planner 2026 Undated, GoodNotes, Instant Download"},
}

_NEW_SPECIALTY_PAGES = {
    "adhd": ["pomodoro", "priority_matrix", "brain_dump"],
    "dark_mode": ["brain_dump"],
    "teacher": [],
    "life": [],
}

# v2 draws its own universal brain-dump pages, so skip the legacy "brain_dump"
# specialty page dispatch to avoid generating it twice.
SKIP_SPECIALTY = {"brain_dump"}

_ALL_V2_PIDS = ["DP1026", "DP1027", "DP1028", "DP1029", "DP1030", "DP1031", "DP1032", "DP1033"]


def _normalize_cfg(pid):
    if pid in _LEGACY_PIDS:
        raw = PLANNERS[pid]
        pcfg = {
            "title": raw["title"],
            "subtitle": raw["subtitle"],
            "year": raw["year"],
            "theme": raw["theme"],
            "accent": raw["accent"],
            "bg": raw["bg"],
            "dark": raw["dark"],
            "sections": raw["sections"],
            "specialty": "",
            "specialty_pages": raw.get("specialty_pages", []),
        }
        meta = dict(_LEGACY_META.get(pid, {"price": 12.99, "listing_title": raw["title"]}))
        meta["raw"] = raw
        return pcfg, meta

    raw = PLANNER_CONFIGS[pid]
    specialty = raw.get("specialty", "")
    pcfg = {
        "title": raw["name"],
        "subtitle": raw["subtitle"],
        "year": raw.get("year"),
        "theme": raw["theme_rgb"],
        "accent": raw["accent_rgb"],
        "bg": raw["bg_rgb"],
        "dark": raw["dark_rgb"],
        "sections": raw["sections"],
        "specialty": specialty,
        "specialty_pages": _NEW_SPECIALTY_PAGES.get(specialty, []),
    }
    meta = {"price": raw.get("price", 12.99), "listing_title": raw.get("listing_title", raw["name"])}
    meta["raw"] = raw
    return pcfg, meta


# ---------------------------------------------------------------------------
# Assembly + orchestration
# ---------------------------------------------------------------------------

def build_planner_v2(pid, dated=True):
    pcfg, meta = _normalize_cfg(pid)
    legacy_cfg = dict(pcfg)  # _make_pages() from planner_page_adder expects this exact key shape

    chunks = []

    def _try(label, fn_call):
        try:
            return fn_call()
        except Exception as e:
            print(f"    Warning: {label} failed: {e}")
            return None

    for nav in ("welcome", "dashboard", "index"):
        chunks.append(_try(nav, lambda n=nav: _make_pages(legacy_cfg, n)))

    sections = pcfg.get("sections", [])

    def _sec_has(keyword):
        return any(keyword.lower() in str(s).lower() for s in sections)

    if _sec_has("yearly") or _sec_has("year at"):
        chunks.append(_try("yearly_overview", lambda: _gen_yearly_overview(pcfg, dated=dated)))

    chunks.append(_try("monthly", lambda: _v2_monthly_pages(pcfg, dated=dated)))

    if _sec_has("monthly review"):
        chunks.append(_try("monthly_review", lambda: _gen_monthly_review_pages(pcfg)))
    if _sec_has("at a glance"):
        chunks.append(_try("month_at_a_glance", lambda: _gen_month_at_a_glance(pcfg)))

    specialty = pcfg.get("specialty", "")
    if specialty == "teacher":
        chunks.append(_try("lesson_plans", lambda: _gen_lesson_plan_pages(pcfg, dated=dated)))
        chunks.append(_try("class_rosters", lambda: _gen_class_roster_pages(pcfg)))
    else:
        chunks.append(_try("weekly", lambda: _v2_weekly_pages(pcfg, dated=dated)))
        chunks.append(_try("daily", lambda: _v2_daily_pages(pcfg, dated=dated)))

    for sp in pcfg.get("specialty_pages", []):
        if sp in SKIP_SPECIALTY:
            continue
        chunks.append(_try(sp, lambda s=sp: _make_pages(legacy_cfg, "specialty", specialty=s)))

    chunks.append(_try("brain_dump", lambda: _v2_brain_dump_pages(pcfg)))

    if _sec_has("budget"):
        chunks.append(_try("budget", lambda: _gen_budget_page(pcfg)))
    if _sec_has("meal"):
        chunks.append(_try("meal_plan", lambda: _gen_meal_plan_page(pcfg)))

    chunks.append(_try("habit_tracker", lambda: _v2_habit_tracker(pcfg)))
    chunks.append(_try("smart_goals", lambda: _v2_smart_goals_pages(pcfg)))
    chunks.append(_try("notes", lambda: _gen_notes_pages(pcfg, count=4)))
    chunks.append(_try("sticker_library", lambda: _gen_sticker_library(pcfg)))

    return _merge_pdfs(*chunks)


def _log_pdf_stats(label, path):
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(path))
        size_kb = path.stat().st_size / 1024.0
        print(f"  {label}: {len(reader.pages)} pages, {size_kb:.0f} KB -> {path}")
    except Exception as e:
        print(f"  {label}: saved to {path} (stats unavailable: {e})")


def generate_planner_v2(pid, no_cover=False):
    pcfg, meta = _normalize_cfg(pid)
    raw = meta["raw"]
    out_dir = PRODUCT_FILES_DIR

    cover_cfg = {
        "name": pcfg["title"],
        "subtitle": pcfg["subtitle"],
        "year": pcfg.get("year"),
        "bg_rgb": pcfg["bg"],
        "theme_rgb": pcfg["theme"],
        "dark_rgb": pcfg["dark"],
    }

    cover_img_path = out_dir / f"{pid}_cover.png"
    if not no_cover:
        if not cover_img_path.exists() and raw.get("cover_prompt"):
            print(f"  Generating cover image for {pid}...")
            _generate_cover_image(raw, cover_img_path)

    cover_pdf_bytes = _make_cover_page(cover_cfg, cover_img_path if cover_img_path.exists() else None)

    print(f"  Building {pid} v2 dated content...")
    dated_bytes = build_planner_v2(pid, dated=True)
    dated_full = _merge_pdfs(cover_pdf_bytes, dated_bytes)
    dated_path = out_dir / f"{pid}_v2.pdf"
    dated_path.write_bytes(dated_full)
    _log_pdf_stats(pid, dated_path)

    print(f"  Building {pid} v2 undated content...")
    undated_bytes = build_planner_v2(pid, dated=False)
    undated_full = _merge_pdfs(cover_pdf_bytes, undated_bytes)
    undated_path = out_dir / f"{pid}U_v2.pdf"
    undated_path.write_bytes(undated_full)
    _log_pdf_stats(pid + "U", undated_path)

    return dated_path


def list_configs_v2():
    print(f"{'ID':<8} {'Title':<42} {'Specialty':<12} {'Price'}")
    for pid in _ALL_V2_PIDS:
        pcfg, meta = _normalize_cfg(pid)
        print(f"{pid:<8} {pcfg['title']:<42} {pcfg.get('specialty', ''):<12} ${meta['price']}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate v2 (redesigned, smart, dimensional) planner PDFs.")
    parser.add_argument("product_id", nargs="?", help="Product ID, e.g. DP1026")
    parser.add_argument("--list", action="store_true", help="List all v2-eligible products")
    parser.add_argument("--all", action="store_true", help="Generate v2 for all products")
    parser.add_argument("--no-cover", action="store_true", help="Skip cover image/page generation")
    args = parser.parse_args()

    if args.list:
        list_configs_v2()
        return

    if args.all:
        for pid in _ALL_V2_PIDS:
            print(f"\n=== {pid} ===")
            generate_planner_v2(pid, no_cover=args.no_cover)
        return

    if not args.product_id:
        parser.print_help()
        return

    pid = args.product_id.upper()
    if pid not in _ALL_V2_PIDS:
        print(f"Unknown product id: {pid}")
        sys.exit(1)

    generate_planner_v2(pid, no_cover=args.no_cover)


if __name__ == "__main__":
    main()
