#!/usr/bin/env python3
"""
Digital Planner Generator — creates complete planner PDFs from CLAUDE.md configs.

Generates:
  • Full planner PDF (dated 2026)
  • Undated evergreen version
  • Cover image via gpt-image-1 (requires OpenAI API key)
  • All pages via reportlab (cover, welcome, dashboard, index, monthly ×12,
    weekly ×52, specialty pages, habit tracker, goals, notes, sticker library)
  • Packages everything for Etsy upload

Usage:
  python tools/generate_planner.py DP1030             # ADHD Planner
  python tools/generate_planner.py DP1031             # Undated Life Planner
  python tools/generate_planner.py DP1032             # Dark Mode Bundle
  python tools/generate_planner.py DP1033             # Teacher Planner
  python tools/generate_planner.py --list             # show all configs
  python tools/generate_planner.py DP1030 --no-cover  # skip OpenAI, use placeholder
"""

from __future__ import annotations

import os
import sys
import json
import argparse
import io
import calendar as _cal
import shutil
from datetime import date, timedelta, date as _date_cls
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
with open(_ENV_PATH) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

BASE_DIR = Path(__file__).parent.parent
PRODUCT_FILES_DIR = BASE_DIR / "data" / "digital_products" / "product_files"
PRODUCT_FILES_DIR.mkdir(parents=True, exist_ok=True)

SHOP_NAME     = "OnBrandCraftz"
SUPPORT_EMAIL = "Printing3dthings@outlook.com"

_MONTHS    = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]
_DAYS_S    = ["MON","TUE","WED","THU","FRI","SAT","SUN"]

# ── Planner configs (from CLAUDE.md theme catalog) ───────────────────────────

PLANNER_CONFIGS = {
    "DP1034": {
        "name":        "Ultimate Celestial Life Planner 2026",
        "subtitle":    "Celestial Night",
        "year":        2026,
        "specialty":   "life",
        "page_count":  140,
        # Celestial Night palette (from CLAUDE.md theme catalog — top-rated celestial aesthetic)
        "theme_rgb":   (0.1176, 0.1059, 0.2941),   # #1E1B4B deep indigo
        "accent_rgb":  (0.7882, 0.6588, 0.2980),   # #C9A84C starlight gold
        "bg_rgb":      (0.9412, 0.9333, 0.9725),   # #F0EEF8 moonbeam white
        "dark_rgb":    (0.0784, 0.0706, 0.1804),   # #14122E near-black indigo
        "price":       16.99,
        "tags": [
            "digital planner",    "celestial planner",  "goodnotes planner",
            "ipad planner",       "fillable planner",   "2026 life planner",
            "moon phase planner", "instant download",   "notability planner",
            "daily planner pdf",  "habit tracker pdf",  "hyperlinked planner",
            "celestial sticker",
        ],
        "cover_prompt": (
            "Celestial digital planner cover art, square 2400x2400px. "
            "Deep indigo night-sky background (#1E1B4B) with a soft gradient to "
            "twilight purple, scattered tiny starlight-gold stars and a delicate "
            "constellation line pattern. Center: an elegant crescent moon with a "
            "calm sleepy kawaii face, ringed by a thin gold celestial border and "
            "tiny orbiting planets and comets. Subtle gold sparkle accents. "
            "Typography: 'Ultimate Celestial Life Planner 2026' in an elegant "
            "rounded serif, starlight gold (#C9A84C). Premium, mystical, polished."
        ),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Yearly Overview", "Monthly Calendars × 12",
            "Monthly Reviews × 12", "Month at a Glance × 12",
            "Weekly Spreads × 52", "Daily Pages",
            "Brain Dump & Priority Matrix", "Habit Tracker",
            "SMART Goals", "Budget Tracker", "Meal Planner",
            "Notes × 4", "Sticker Library × 5",
        ],
        "description_hook": (
            "Plan your whole life by the stars. The Ultimate Celestial Life "
            "Planner 2026 is a fully hyperlinked, fillable GoodNotes & Notability "
            "planner with everything you need in one place — yearly, monthly, "
            "weekly and daily layouts, habit and mood tracking, budgeting, meal "
            "planning, SMART goals and brain-dump pages — wrapped in a premium "
            "Celestial Night palette of deep indigo and starlight gold."
        ),
        "listing_title": "Celestial Digital Planner 2026, GoodNotes iPad, Instant Download",
    },
    "DP1030": {
        "name":        "ADHD Digital Planner 2026",
        "subtitle":    "Matcha Serenity",
        "year":        2026,
        "specialty":   "adhd",
        "page_count":  110,
        "theme_rgb":   (0.420, 0.561, 0.369),
        "accent_rgb":  (0.722, 0.800, 0.557),
        "bg_rgb":      (0.969, 0.976, 0.953),
        "dark_rgb":    (0.118, 0.176, 0.094),
        "price":       12.99,
        "tags": [
            "adhd planner",      "digital planner",    "adhd digital",
            "goodnotes planner", "focus planner",      "ipad planner",
            "adhd tools adult",  "kawaii planner",     "fillable planner",
            "instant download",  "pomodoro planner",   "brain dump journal",
            "habit tracker pdf",
        ],
        "cover_prompt": (
            "Kawaii digital planner cover art, square 2400x2400px. "
            "Matcha green background with soft rice paper texture. "
            "Center: large kawaii matcha cup with cream swirl and tiny steam curls, "
            "surrounded by zen garden elements — smooth stones, bamboo sprigs, tiny lotus flower. "
            "Small kawaii brain character with stars around it, calm sleepy expression. "
            "Typography: 'ADHD Digital Planner 2026' in rounded sans-serif font. "
            "Soft kawaii illustration style, pastel palette."
        ),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Yearly Overview", "Monthly Calendars × 12",
            "Monthly Reviews × 12", "Weekly Spreads × 52",
            "Pomodoro Focus Sheets × 4", "Brain Dump Pages × 12",
            "Habit Tracker", "Priority Matrix", "Goals",
            "Notes × 4", "Sticker Library × 5",
        ],
        "description_hook": (
            "Your brain works differently — and your planner should too. "
            "Introducing the ADHD Digital Planner 2026, designed specifically "
            "for the ADHD brain: visual time-blocking, Pomodoro focus sheets, "
            "brain dump pages, and a priority matrix — all in a calming Matcha Serenity "
            "color palette that reduces overwhelm while keeping you on track."
        ),
        "listing_title": "ADHD Digital Planner 2026 | GoodNotes Focus Planner | Kawaii Instant Download",
    },
    "DP1031": {
        "name":        "Undated Life Planner",
        "subtitle":    "Sage Garden",
        "year":        None,
        "specialty":   "life",
        "page_count":  100,
        "theme_rgb":   (0.545, 0.659, 0.533),
        "accent_rgb":  (0.784, 0.867, 0.710),
        "bg_rgb":      (0.965, 0.973, 0.949),
        "dark_rgb":    (0.173, 0.220, 0.157),
        "price":       12.99,
        "tags": [
            "undated planner",   "digital planner",    "goodnotes planner",
            "life planner",      "notability planner", "ipad planner",
            "kawaii planner",    "fillable planner",   "instant download",
            "printable planner", "daily planner pdf",  "habit tracker pdf",
            "evergreen planner",
        ],
        "cover_prompt": (
            "Kawaii digital planner cover art, square 2400x2400px. "
            "Sage green background with soft morning dew texture. "
            "Center: kawaii garden scene — tiny mushrooms, watering can, herb sprigs, "
            "garden snail with bow, potted succulents, small bee. "
            "Cottagecore aesthetic, soft botanical illustration. "
            "Typography: 'Undated Life Planner' in flowing rounded font."
        ),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Undated Monthly Calendars × 12", "Monthly Reviews × 12",
            "Month at a Glance × 12", "Undated Weekly Spreads × 52",
            "Habit Tracker", "Goals", "Budget Tracker",
            "Meal Planner", "Notes × 4", "Sticker Library × 5",
        ],
        "description_hook": (
            "No expiry date. No wasted pages. The Undated Life Planner in Sage Garden "
            "is your forever planner — start any month, any week, any time."
        ),
        "listing_title": "Undated Digital Life Planner | GoodNotes Notability | Kawaii Instant Download",
    },
    "DP1032": {
        "name":        "Dark Mode Planner Bundle 2026",
        "subtitle":    "Midnight Kawaii",
        "year":        2026,
        "specialty":   "dark_mode",
        "page_count":  108,
        "theme_rgb":   (0.502, 0.251, 0.612),   # electric violet toned down for dark bg
        "accent_rgb":  (0.000, 0.898, 1.000),   # neon aqua
        "bg_rgb":      (0.102, 0.102, 0.180),   # deep midnight
        "dark_rgb":    (0.941, 0.902, 1.000),   # starlight text
        "price":       14.99,
        "tags": [
            "dark mode planner", "digital planner",    "goodnotes dark",
            "dark planner pdf",  "kawaii dark",        "ipad planner",
            "night mode planner","fillable planner",   "instant download",
            "aesthetic planner", "y2k planner",        "dark kawaii",
            "goodnotes planner",
        ],
        "cover_prompt": (
            "Kawaii digital planner cover art, square 2400x2400px. "
            "Deep midnight navy background with subtle star field. "
            "Center: kawaii space cat with neon violet glow, holographic elements, "
            "pixel art stars, glowing crescent moon, neon-outlined kawaii ghost. "
            "Electric violet and neon aqua accent glows. "
            "Typography: 'Dark Mode Planner 2026' in neon glow font effect."
        ),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Yearly Overview", "Monthly Calendars × 12",
            "Monthly Reviews × 12", "Month at a Glance × 12",
            "Weekly Spreads × 52", "Night Owl Habit Tracker",
            "Goals", "Brain Dump × 4", "Notes × 4", "Sticker Library × 5",
        ],
        "description_hook": (
            "Finally — a planner for night owls, gamers, and dark aesthetic lovers. "
            "The Dark Mode Planner 2026 in Midnight Kawaii brings Y3K neon-on-dark "
            "design to your GoodNotes and Notability workflow."
        ),
        "listing_title": "Dark Mode Digital Planner 2026 | GoodNotes Dark Kawaii | Instant Download",
    },
    "DP1033": {
        "name":        "Teacher Planner 2026-2027",
        "subtitle":    "Sunflower Studio",
        "year":        2026,
        "specialty":   "teacher",
        "page_count":  115,
        "theme_rgb":   (0.957, 0.769, 0.188),
        "accent_rgb":  (0.290, 0.486, 0.349),
        "bg_rgb":      (1.000, 0.992, 0.941),
        "dark_rgb":    (0.165, 0.102, 0.000),
        "price":       14.99,
        "tags": [
            "teacher planner",   "digital planner",    "teacher goodnotes",
            "classroom planner", "teacher ipad",       "lesson plan pdf",
            "teacher gift",      "kawaii teacher",     "fillable planner",
            "instant download",  "academic planner",   "school year planner",
            "teacher organizer",
        ],
        "cover_prompt": (
            "Kawaii digital planner cover art, square 2400x2400px. "
            "Warm cream background with subtle grid texture. "
            "Center: kawaii teacher scene — sunflowers in a mason jar, tiny apple, "
            "mini chalkboard with 'Hello Students', pencils in a cup, books stacked, "
            "kawaii bee with graduation cap, butterflies, small ruler. "
            "Sunflower yellow and stem green color palette. "
            "Typography: 'Teacher Planner 2026-2027' in cheerful rounded font."
        ),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Academic Year at a Glance (Aug 2026-Jul 2027)",
            "Monthly Calendars x 12 (Aug-Jul)", "Monthly Reviews x 12",
            "Weekly Lesson Plans x 44", "Class Roster x 6 classes",
            "Seating Chart Templates", "Parent Communication Log",
            "Habit Tracker (self-care for teachers)", "Goals",
            "Sub Plans Template x 2", "Notes x 4", "Sticker Library x 5",
        ],
        "description_hook": (
            "The most complete teacher planner for GoodNotes and Notability — "
            "built around the academic year August 2026 through July 2027."
        ),
        "listing_title": "Teacher Planner 2026-2027 | GoodNotes Digital | Kawaii Instant Download",
    },
}


# ── Shared drawing helpers ────────────────────────────────────────────────────

_FONT_MAP: dict[str, str] = {}
_FONTS_REGISTERED = False

def _get_fn():
    global _FONT_MAP, _FONTS_REGISTERED
    if not _FONTS_REGISTERED:
        _FONTS_REGISTERED = True
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            fonts_dir = BASE_DIR / "assets" / "fonts"
            for fname, ffile in {
                "Poppins": "Poppins-Regular.ttf",
                "Poppins-Bold": "Poppins-Bold.ttf",
                "Poppins-SemiBold": "Poppins-SemiBold.ttf",
                "Poppins-Italic": "Poppins-Italic.ttf",
            }.items():
                fp = fonts_dir / ffile
                if fp.exists():
                    try:
                        pdfmetrics.registerFont(TTFont(fname, str(fp)))
                        _FONT_MAP[fname] = fname
                    except Exception:
                        pass
        except Exception:
            pass

    def fn(variant="regular"):
        v = variant.lower()
        if v in ("bold", "b"):
            return _FONT_MAP.get("Poppins-Bold", "Helvetica-Bold")
        if v in ("semibold", "sb"):
            return _FONT_MAP.get("Poppins-SemiBold", _FONT_MAP.get("Poppins-Bold", "Helvetica-Bold"))
        if v in ("italic", "i"):
            return _FONT_MAP.get("Poppins-Italic", "Helvetica-Oblique")
        return _FONT_MAP.get("Poppins", "Helvetica")

    return fn


def _bl(rgb, f):
    """Blend rgb toward white by factor f."""
    return tuple(min(1.0, x + (1.0 - x) * f) for x in rgb)


def _new_canvas():
    from reportlab.pdfgen import canvas as pdf_canvas
    buf = io.BytesIO()
    PW, PH = 612.0, 792.0
    c = pdf_canvas.Canvas(buf, pagesize=(PW, PH))
    return c, buf, PW, PH


_ML = _MR = 36.0
_MT = _MB = 32.0


def _page_bg(c, BG, PW, PH):
    c.setFillColorRGB(*BG)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)


def _header_band(c, label, T, BG, fn, PW, PH, sub=""):
    h = 52
    c.setFillColorRGB(*T)
    c.rect(0, PH - h, PW, h, fill=1, stroke=0)
    c.setFillColorRGB(*BG)
    if sub:
        c.setFont(fn("bold"), 16)
        c.drawCentredString(PW / 2, PH - 32, label)
        c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2, PH - 46, sub)
    else:
        c.setFont(fn("bold"), 18)
        c.drawCentredString(PW / 2, PH - 32, label)


def _footer(c, T, BG, fn, PW):
    c.setFillColorRGB(*T)
    c.rect(0, 0, PW, 22, fill=1, stroke=0)
    c.setFillColorRGB(*BG)
    c.setFont(fn("regular"), 7)
    c.drawCentredString(PW / 2, 7, f"© {SHOP_NAME} — Personal use only")


# ── Page generator functions ──────────────────────────────────────────────────

def _gen_yearly_overview(pcfg: dict, dated: bool = True) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    year = (pcfg.get("year") or 2026) if dated else 2026
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR
    _page_bg(c, BG, PW, PH)
    lbl = f"YEARLY OVERVIEW — {year}" if dated else "YEARLY OVERVIEW"
    _header_band(c, lbl, T, BG, fn, PW, PH)

    y = PH - 52 - 18
    col_w = CW / 4 - 6
    row_h = (y - _MB - 26) / 3 - 8

    for mi in range(12):
        mc = mi % 4
        mr = mi // 4
        mx = _ML + mc * (col_w + 8)
        my = y - mr * (row_h + 8)

        c.setFillColorRGB(*T)
        c.rect(mx, my - 16, col_w, 16, fill=1, stroke=0)
        c.setFillColorRGB(*BG)
        c.setFont(fn("bold"), 8)
        c.drawCentredString(mx + col_w / 2, my - 12, _MONTHS[mi][:3].upper())

        mini_cw = col_w / 7
        days_short = ["M","T","W","T","F","S","S"]
        for di, dl in enumerate(days_short):
            c.setFillColorRGB(*_bl(T, 0.65))
            c.setFont(fn("bold"), 5)
            c.drawCentredString(mx + di * mini_cw + mini_cw / 2, my - 26, dl)

        first_wd, days_in = _cal.monthrange(year, mi + 1)
        mini_rh = (row_h - 30) / 6
        day_num = 1
        for cell in range(42):
            r, col = cell // 7, cell % 7
            cy = my - 30 - r * mini_rh
            cx = mx + col * mini_cw
            if cell >= first_wd and day_num <= days_in:
                is_we = col >= 5
                c.setFillColorRGB(*(_bl(T, 0.88) if is_we else (1, 1, 1)))
                c.setLineWidth(0.2)
                c.setStrokeColorRGB(*_bl(T, 0.70))
                c.rect(cx, cy - mini_rh, mini_cw, mini_rh, fill=1, stroke=1)
                c.setFillColorRGB(*DK)
                c.setFont(fn("regular"), 5)
                c.drawCentredString(cx + mini_cw / 2, cy - mini_rh + 2, str(day_num))
                day_num += 1

    _footer(c, T, BG, fn, PW)
    c.showPage()
    c.save()
    return buf.getvalue()


def _gen_monthly_pages(pcfg: dict, dated: bool = True) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    year = (pcfg.get("year") or 2026) if dated else 2026
    specialty = pcfg.get("specialty", "")
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR

    teacher = "teacher" in str(specialty).lower()
    month_order = (list(range(8, 13)) + list(range(1, 8))) if teacher else list(range(1, 13))

    for month_num in month_order:
        disp_year = (year + 1) if (teacher and month_num < 8) else year
        month_name = _MONTHS[month_num - 1]

        _page_bg(c, BG, PW, PH)
        hdr_h = 56
        c.setFillColorRGB(*T)
        c.rect(0, PH - hdr_h, PW, hdr_h, fill=1, stroke=0)
        c.setFillColorRGB(*BG)
        c.setFont(fn("bold"), 20)
        title = f"{month_name.upper()} {disp_year}" if dated else month_name.upper()
        c.drawCentredString(PW / 2, PH - 36, title)

        col_w = CW / 7
        y_top = PH - hdr_h
        day_hdr_h = 20

        for di, day in enumerate(_DAYS_S):
            dx = _ML + di * col_w
            is_we = di >= 5
            c.setFillColorRGB(*(_bl(T, 0.60) if is_we else _bl(T, 0.80)))
            c.rect(dx, y_top - day_hdr_h, col_w, day_hdr_h, fill=1, stroke=0)
            c.setFillColorRGB(*BG)
            c.setFont(fn("bold"), 8)
            c.drawCentredString(dx + col_w / 2, y_top - day_hdr_h + 6, day)

        notes_h = 50
        grid_top = y_top - day_hdr_h
        grid_h = grid_top - _MB - notes_h - 4
        row_h = grid_h / 6

        first_wd, days_in = _cal.monthrange(disp_year, month_num)
        day_num = 1
        for row in range(6):
            for col in range(7):
                cell_idx = row * 7 + col
                cx = _ML + col * col_w
                cy = grid_top - (row + 1) * row_h
                is_we = col >= 5
                c.setFillColorRGB(*(_bl(T, 0.92) if is_we else (1, 1, 1)))
                c.setLineWidth(0.3)
                c.setStrokeColorRGB(*_bl(T, 0.65))
                c.rect(cx, cy, col_w, row_h, fill=1, stroke=1)
                if cell_idx >= first_wd and day_num <= days_in:
                    c.setFillColorRGB(*T)
                    c.circle(cx + 10, cy + row_h - 10, 8, fill=1, stroke=0)
                    c.setFillColorRGB(*BG)
                    c.setFont(fn("bold"), 7)
                    c.drawCentredString(cx + 10, cy + row_h - 13, str(day_num))
                    day_num += 1

        notes_y = _MB + 2
        c.setFillColorRGB(*_bl(T, 0.92))
        c.roundRect(_ML, notes_y, CW, notes_h - 4, 4, fill=1, stroke=0)
        c.setFillColorRGB(*T)
        c.setFont(fn("bold"), 7.5)
        c.drawString(_ML + 8, notes_y + notes_h - 16, "NOTES")
        c.setLineWidth(0.35)
        c.setStrokeColorRGB(*_bl(T, 0.60))
        for li in range(2):
            c.line(_ML + 8, notes_y + notes_h - 30 - li * 16, _ML + CW - 8, notes_y + notes_h - 30 - li * 16)

        _footer(c, T, BG, fn, PW)
        c.showPage()

    c.save()
    return buf.getvalue()


def _gen_monthly_review_pages(pcfg: dict) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR

    prompts = [
        ("TOP WINS THIS MONTH", "What did you accomplish? What are you proud of?"),
        ("LESSONS LEARNED", "What would you do differently?"),
        ("FOCUS FOR NEXT MONTH", "Your top 3 priorities for the coming month:"),
        ("GRATITUDE", "Three things you are grateful for this month:"),
    ]
    box_h = (PH - 52 - 20 - _MB - 26) / 4 - 6

    for mi in range(12):
        _page_bg(c, BG, PW, PH)
        _header_band(c, f"MONTHLY REVIEW — {_MONTHS[mi].upper()}", T, BG, fn, PW, PH)
        y = PH - 52 - 20

        for pi, (title, sub) in enumerate(prompts):
            py = y - pi * (box_h + 6)
            c.setFillColorRGB(*_bl(T, 0.91))
            c.roundRect(_ML, py - box_h, CW, box_h, 5, fill=1, stroke=0)
            c.setFillColorRGB(*T)
            c.setLineWidth(0.6)
            c.roundRect(_ML, py - box_h, CW, box_h, 5, fill=0, stroke=1)
            c.setFillColorRGB(*T)
            c.roundRect(_ML, py - 22, CW, 22, 5, fill=1, stroke=0)
            c.setFillColorRGB(*BG)
            c.setFont(fn("bold"), 9)
            c.drawString(_ML + 8, py - 16, title)
            c.setFillColorRGB(*_bl(DK, 0.30))
            c.setFont(fn("italic"), 7.5)
            c.drawString(_ML + 8, py - 32, sub)
            c.setLineWidth(0.35)
            c.setStrokeColorRGB(*_bl(T, 0.65))
            li_n = max(1, int((box_h - 38) / 18))
            for li in range(li_n):
                ly = py - 46 - li * 18
                if ly > py - box_h + 8:
                    c.line(_ML + 8, ly, _ML + CW - 8, ly)

        _footer(c, T, BG, fn, PW)
        c.showPage()

    c.save()
    return buf.getvalue()


def _gen_month_at_a_glance(pcfg: dict) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR

    for mi in range(12):
        _page_bg(c, BG, PW, PH)
        _header_band(c, f"MONTH AT A GLANCE — {_MONTHS[mi].upper()}", T, BG, fn, PW, PH)
        y = PH - 52 - 18
        avail = y - _MB - 26

        top_h = avail * 0.44
        # Priorities box
        c.setFillColorRGB(*_bl(T, 0.90))
        c.roundRect(_ML, y - top_h, CW / 2 - 4, top_h, 5, fill=1, stroke=0)
        c.setFillColorRGB(*T)
        c.rect(_ML, y - 20, CW / 2 - 4, 20, fill=1, stroke=0)
        c.setFillColorRGB(*BG)
        c.setFont(fn("bold"), 9)
        c.drawString(_ML + 8, y - 15, "TOP PRIORITIES")
        c.setLineWidth(0.35)
        c.setStrokeColorRGB(*_bl(T, 0.55))
        for li in range(5):
            ly = y - 34 - li * 20
            if ly > y - top_h + 8:
                c.line(_ML + 10, ly, _ML + CW / 2 - 12, ly)

        # Focus box
        fx = _ML + CW / 2 + 4
        c.setFillColorRGB(*_bl(A, 0.88))
        c.roundRect(fx, y - top_h, CW / 2 - 4, top_h, 5, fill=1, stroke=0)
        c.setFillColorRGB(*A)
        c.rect(fx, y - 20, CW / 2 - 4, 20, fill=1, stroke=0)
        c.setFillColorRGB(*BG)
        c.setFont(fn("bold"), 9)
        c.drawString(fx + 8, y - 15, "FOCUS AREAS")
        c.setStrokeColorRGB(*_bl(A, 0.55))
        for li in range(4):
            ly = y - 34 - li * 22
            if ly > y - top_h + 8:
                c.line(fx + 8, ly, fx + CW / 2 - 12, ly)

        # Intention box
        mid_y = y - top_h - 8
        mid_h = avail * 0.30
        c.setFillColorRGB(*_bl(T, 0.93))
        c.roundRect(_ML, mid_y - mid_h, CW * 0.65 - 4, mid_h, 5, fill=1, stroke=0)
        c.setFillColorRGB(*T)
        c.rect(_ML, mid_y - 20, CW * 0.65 - 4, 20, fill=1, stroke=0)
        c.setFillColorRGB(*BG)
        c.setFont(fn("bold"), 9)
        c.drawString(_ML + 8, mid_y - 15, "MONTHLY INTENTION")
        c.setStrokeColorRGB(*_bl(T, 0.55))
        for li in range(3):
            ly = mid_y - 34 - li * 18
            if ly > mid_y - mid_h + 6:
                c.line(_ML + 8, ly, _ML + CW * 0.65 - 12, ly)

        # Word of month
        wx = _ML + CW * 0.65 + 4
        ww = CW * 0.35 - 4
        c.setFillColorRGB(*_bl(A, 0.90))
        c.roundRect(wx, mid_y - mid_h, ww, mid_h, 5, fill=1, stroke=0)
        c.setFillColorRGB(*A)
        c.rect(wx, mid_y - 20, ww, 20, fill=1, stroke=0)
        c.setFillColorRGB(*BG)
        c.setFont(fn("bold"), 8)
        c.drawCentredString(wx + ww / 2, mid_y - 15, "WORD OF MONTH")
        c.setFillColorRGB(*DK)
        c.setFont(fn("italic"), 9)
        c.drawCentredString(wx + ww / 2, mid_y - mid_h / 2 - 4, "________________")

        # Notes bar
        bot_y = mid_y - mid_h - 8
        bot_h = bot_y - _MB - 2
        if bot_h > 20:
            c.setFillColorRGB(*_bl(T, 0.93))
            c.roundRect(_ML, _MB + 2, CW, bot_h, 5, fill=1, stroke=0)
            c.setFillColorRGB(*T)
            c.rect(_ML, _MB + 2 + bot_h - 20, CW, 20, fill=1, stroke=0)
            c.setFillColorRGB(*BG)
            c.setFont(fn("bold"), 9)
            c.drawString(_ML + 8, _MB + 2 + bot_h - 15, "NOTES & REMINDERS")
            c.setStrokeColorRGB(*_bl(T, 0.55))
            for li in range(2):
                ly = bot_y - 28 - li * 18
                if ly > _MB + 8:
                    c.line(_ML + 8, ly, _ML + CW - 8, ly)

        _footer(c, T, BG, fn, PW)
        c.showPage()

    c.save()
    return buf.getvalue()


def _gen_weekly_pages(pcfg: dict, dated: bool = True) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    year = (pcfg.get("year") or 2026) if dated else 2026
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR

    if dated:
        jan1 = _date_cls(year, 1, 1)
        wd = jan1.weekday()
        first_mon = jan1 + timedelta(days=(7 - wd) % 7)
        week_starts = [first_mon + timedelta(weeks=i) for i in range(52)]
    else:
        week_starts = [None] * 52

    SECTIONS = ["Morning", "Afternoon", "Evening"]
    notes_col_w = CW * 0.22
    day_area_w = CW - notes_col_w - 4
    day_col_w = day_area_w / 7

    for wk_idx in range(52):
        wn = wk_idx + 1
        start = week_starts[wk_idx]

        if dated and start:
            end = start + timedelta(days=6)
            wk_lbl = f"WEEK {wn}  ·  {start.strftime('%b %-d')} – {end.strftime('%b %-d, %Y')}"
        else:
            wk_lbl = f"WEEK {wn}"

        _page_bg(c, BG, PW, PH)
        hdr_h = 44
        c.setFillColorRGB(*T)
        c.rect(0, PH - hdr_h, PW, hdr_h, fill=1, stroke=0)
        c.setFillColorRGB(*BG)
        c.setFont(fn("bold"), 13)
        c.drawCentredString(PW / 2, PH - 28, wk_lbl)

        # Day headers
        day_hdr_h = 22
        grid_top = PH - hdr_h - day_hdr_h
        for di, day in enumerate(_DAYS_S):
            dx = _ML + di * day_col_w
            is_we = di >= 5
            c.setFillColorRGB(*(_bl(T, 0.62) if is_we else _bl(T, 0.80)))
            c.rect(dx, grid_top, day_col_w, day_hdr_h, fill=1, stroke=0)
            c.setFillColorRGB(*BG)
            c.setFont(fn("bold"), 8)
            if dated and start:
                dd = start + timedelta(days=di)
                c.drawCentredString(dx + day_col_w / 2, grid_top + 14, day)
                c.setFont(fn("regular"), 6)
                c.drawCentredString(dx + day_col_w / 2, grid_top + 4, dd.strftime('%m/%d'))
            else:
                c.drawCentredString(dx + day_col_w / 2, grid_top + 8, day)

        section_h = (grid_top - _MB) / len(SECTIONS)
        for si, sect in enumerate(SECTIONS):
            sy = grid_top - (si + 1) * section_h
            # Section label (left margin)
            c.setFillColorRGB(*(_bl(A, 0.75) if si % 2 else _bl(T, 0.75)))
            c.rect(0, sy, _ML - 2, section_h, fill=1, stroke=0)
            c.setFillColorRGB(*BG)
            c.setFont(fn("bold"), 7)
            c.saveState()
            c.translate(_ML / 2, sy + section_h / 2)
            c.rotate(90)
            c.drawCentredString(0, 0, sect)
            c.restoreState()

            for di in range(7):
                dx = _ML + di * day_col_w
                is_we = di >= 5
                c.setFillColorRGB(*(_bl(T, 0.95) if is_we else (1.0, 1.0, 1.0)))
                c.setLineWidth(0.3)
                c.setStrokeColorRGB(*_bl(T, 0.68))
                c.rect(dx, sy, day_col_w, section_h, fill=1, stroke=1)
                c.setLineWidth(0.2)
                c.setStrokeColorRGB(*_bl(T, 0.82))
                ln_sp = 14
                ln_n = int((section_h - 4) / ln_sp)
                for li in range(ln_n):
                    ly = sy + section_h - 8 - li * ln_sp
                    if ly > sy + 4:
                        c.line(dx + 3, ly, dx + day_col_w - 3, ly)

        # Notes column
        nx = _ML + day_area_w + 4
        nh = grid_top - _MB
        c.setFillColorRGB(*_bl(T, 0.92))
        c.roundRect(nx, _MB, notes_col_w, nh, 4, fill=1, stroke=0)
        c.setFillColorRGB(*T)
        c.setFont(fn("bold"), 8)
        c.drawCentredString(nx + notes_col_w / 2, grid_top - 12, "NOTES")
        c.setFont(fn("bold"), 7.5)
        c.drawString(nx + 5, grid_top - 28, "TOP 3")
        for pi in range(3):
            py = grid_top - 42 - pi * 18
            c.setFillColorRGB(*T)
            c.roundRect(nx + 5, py - 2, 10, 10, 2, fill=0, stroke=1)
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(*_bl(T, 0.50))
            c.line(nx + 18, py + 3, nx + notes_col_w - 5, py + 3)
        c.setLineWidth(0.2)
        c.setStrokeColorRGB(*_bl(T, 0.68))
        yl = grid_top - 42 - 3 * 18 - 10
        while yl > _MB + 8:
            c.line(nx + 5, yl, nx + notes_col_w - 5, yl)
            yl -= 14

        _footer(c, T, BG, fn, PW)
        c.showPage()

    c.save()
    return buf.getvalue()


def _gen_habit_tracker(pcfg: dict) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR
    _page_bg(c, BG, PW, PH)
    _header_band(c, "HABIT TRACKER", T, BG, fn, PW, PH)

    y = PH - 52 - 16
    c.setFillColorRGB(*DK)
    c.setFont(fn("bold"), 9)
    c.drawString(_ML, y, "Month: ________________    Goal: _________________________________")
    y -= 22

    habit_col_w = 88
    day_col_w = (CW - habit_col_w) / 31
    header_h = 18
    n_habits = 8
    row_h = (y - _MB - 32) / (n_habits + 1)

    c.setFillColorRGB(*T)
    c.rect(_ML + habit_col_w, y - header_h, CW - habit_col_w, header_h, fill=1, stroke=0)
    c.setFillColorRGB(*BG)
    c.setFont(fn("bold"), 7)
    for di in range(31):
        dx = _ML + habit_col_w + di * day_col_w
        c.drawCentredString(dx + day_col_w / 2, y - 13, str(di + 1))

    for hi in range(n_habits):
        ry = y - header_h - (hi + 1) * row_h
        c.setFillColorRGB(*_bl(T if hi % 2 == 0 else A, 0.83))
        c.setLineWidth(0.4)
        c.setStrokeColorRGB(*_bl(T, 0.60))
        c.rect(_ML, ry, habit_col_w, row_h, fill=1, stroke=1)
        c.setFillColorRGB(*DK)
        c.setFont(fn("regular"), 7)
        c.drawString(_ML + 4, ry + row_h / 2 - 4, "__________________")
        for di in range(31):
            dx = _ML + habit_col_w + di * day_col_w
            c.setFillColorRGB(*(_bl(T, 0.93) if di % 2 == 0 else (1, 1, 1)))
            c.rect(dx, ry, day_col_w, row_h, fill=1, stroke=1)

    key_y = y - header_h - (n_habits + 1) * row_h - 6
    if key_y > _MB + 2:
        c.setFillColorRGB(*DK)
        c.setFont(fn("italic"), 8)
        c.drawString(_ML, key_y, "Key:  ")
        kx = _ML + 32
        for lbl, col in [("Done", T), ("Partial", A), ("Missed", (0.65, 0.65, 0.65))]:
            c.setFillColorRGB(*col)
            c.rect(kx, key_y - 2, 10, 10, fill=1, stroke=0)
            c.setFillColorRGB(*DK)
            c.drawString(kx + 13, key_y + 1, lbl)
            kx += 68

    _footer(c, T, BG, fn, PW)
    c.showPage()
    c.save()
    return buf.getvalue()


def _gen_goals_page(pcfg: dict) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR
    _page_bg(c, BG, PW, PH)
    _header_band(c, "GOALS", T, BG, fn, PW, PH)

    y = PH - 52 - 18
    goals = [
        ("GOAL 1 — PERSONAL", A),
        ("GOAL 2 — PROFESSIONAL", T),
        ("GOAL 3 — GROWTH", _bl(T, 0.25)),
        ("GOAL 4 — WILDCARD", _bl(A, 0.25)),
    ]
    box_h = (y - _MB - 26) / 4 - 6

    for gi, (label, col) in enumerate(goals):
        gy = y - gi * (box_h + 6)
        c.setFillColorRGB(*_bl(col, 0.90))
        c.roundRect(_ML, gy - box_h, CW, box_h, 6, fill=1, stroke=0)
        c.setFillColorRGB(*col)
        c.setLineWidth(0.7)
        c.roundRect(_ML, gy - box_h, CW, box_h, 6, fill=0, stroke=1)
        c.setFillColorRGB(*col)
        c.roundRect(_ML, gy - 22, CW, 22, 6, fill=1, stroke=0)
        c.setFillColorRGB(*BG)
        c.setFont(fn("bold"), 9)
        c.drawString(_ML + 8, gy - 16, label)
        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 8)
        c.drawString(_ML + 8, gy - 34, "Goal:")
        c.setLineWidth(0.4)
        c.setStrokeColorRGB(*_bl(col, 0.50))
        c.line(_ML + 42, gy - 31, _ML + CW - 8, gy - 31)
        c.setFont(fn("regular"), 8)
        c.drawString(_ML + 8, gy - 50, "Why it matters:")
        c.line(_ML + 88, gy - 47, _ML + CW - 8, gy - 47)
        c.setFont(fn("bold"), 8)
        c.drawString(_ML + 8, gy - 64, "Steps:")
        steps = max(2, int((box_h - 72) / 18))
        for si in range(steps):
            sy = gy - 78 - si * 18
            if sy > gy - box_h + 8:
                c.setFillColorRGB(*col)
                c.circle(_ML + 18, sy + 4, 5, fill=1, stroke=0)
                c.setFillColorRGB(*BG)
                c.setFont(fn("bold"), 7.5)
                c.drawCentredString(_ML + 18, sy + 1, str(si + 1))
                c.setStrokeColorRGB(*_bl(col, 0.50))
                c.line(_ML + 28, sy, _ML + CW - 8, sy)

    _footer(c, T, BG, fn, PW)
    c.showPage()
    c.save()
    return buf.getvalue()


def _gen_notes_pages(pcfg: dict, count: int = 4) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR

    for pi in range(count):
        _page_bg(c, BG, PW, PH)
        _header_band(c, f"NOTES — PAGE {pi + 1}", T, BG, fn, PW, PH)
        y = PH - 52 - 10
        c.setFillColorRGB(*DK)
        c.setFont(fn("regular"), 8)
        c.drawString(_ML, y, "Date: ___________________    Topic: _________________________________")
        y -= 20
        dot_sp = 18
        dy = y
        while dy > _MB + 28:
            dx = _ML
            while dx <= _ML + CW:
                c.setFillColorRGB(*_bl(T, 0.50))
                c.circle(dx, dy, 0.8, fill=1, stroke=0)
                dx += dot_sp
            dy -= dot_sp
        c.setLineWidth(0.35)
        c.setStrokeColorRGB(*_bl(T, 0.75))
        ly = y - 14
        while ly > _MB + 28:
            c.line(_ML, ly, _ML + CW, ly)
            ly -= 24
        _footer(c, T, BG, fn, PW)
        c.showPage()

    c.save()
    return buf.getvalue()


def _gen_sticker_library(pcfg: dict) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR

    SHEETS = [
        ("Sheet 1: Functional Planning", "Headers, checklists, flags, date dots, priority labels", T,
         ["Header Banner","Checkbox Row","Due Date Flag","Priority Star","Date Dot",
          "Action Arrow","Urgent Badge","Monthly Label","Week Tab","Checklist Strip",
          "Category Dot","Ribbon Banner","Scroll Label","Page Flag","Sticky Note",
          "Appointment Pin","Clock Icon","Alarm Badge","Task Flag","Section Divider"]),
        ("Sheet 2: Widget Trackers", "Mood tracker, water intake, sleep log, habit tracker, energy", A,
         ["Mood Tracker","Water: 8 cups","Sleep Bubbles","Habit Streak","Energy Level",
          "Weekly Summary","Steps Counter","Macro Tracker","Monthly Mood","Gratitude Box",
          "Focus Timer","Water Drop","Zzz Sleep","Flame Streak","Progress Bar",
          "Star Rating","Weather Mood","Mindful Min","Calorie Note","Brain Dump"]),
        ("Sheet 3: Planner & Stationery", "Notebooks, pens, washi tape, stars, coffee cups", _bl(T, 0.25),
         ["Mini Notebook","Fountain Pen","Washi Tape","Paper Clips","Sticky Note",
          "Ruler + Pencil","Scissors","Highlighter","Bookmarks","Eraser",
          "Pencil Cup","Notebook Stack","Paper Star","Binder Clip","Index Cards",
          "Coffee Cup","Desk Lamp","Inbox Tray","Stamp","Letter Opener"]),
        ("Sheet 4: Cozy Lifestyle", "Mugs, candles, books, fairy lights, sleeping cat", _bl(A, 0.25),
         ["Steaming Mug","Candle Trio","Open Book","Fairy Lights","Sleeping Cat",
          "Ramen Bowl","Matcha Latte","Headphones","Cozy Blanket","Indoor Plant",
          "Succulent Pot","Window Rain","Snuggle Socks","Tea Pot","Biscuits",
          "Pillow Set","Hammock","Journal+Pen","Reading Nook","Scented Candle"]),
        ("Sheet 5: Seasonal & Holiday", "Cherry blossoms, pumpkins, snowflakes, valentines", _bl(T, 0.50),
         ["Cherry Blossom","Easter Egg","Sunflower","Back-to-School","Halloween Bat",
          "Pumpkin","Thanksgiving","Snowflakes","Christmas Tree","New Year Fireworks",
          "Valentine Heart","St Patricks","Graduation Cap","4th of July","Birthday Cake",
          "Anniversary","Spring Rain","Summer Sun","Autumn Leaf","Winter Star"]),
    ]

    for si, (title, desc, col, examples) in enumerate(SHEETS):
        _page_bg(c, BG, PW, PH)
        _header_band(c, f"STICKER LIBRARY", T, BG, fn, PW, PH, sub=title)
        y = PH - 52 - 18
        c.setFillColorRGB(*DK)
        c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2, y, desc)
        y -= 18

        # Import tip
        tip_h = 38
        c.setFillColorRGB(*_bl(col, 0.88))
        c.roundRect(_ML, y - tip_h, CW, tip_h, 5, fill=1, stroke=0)
        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 8)
        c.drawString(_ML + 8, y - 12, "GoodNotes: Elements → Stickers → + → select all 5 PNG sheets → stickers appear in library")
        c.setFont(fn("regular"), 8)
        c.drawString(_ML + 8, y - 26, "Notability: use Photo Stickers  |  Acrobat/Xodo: tap STICKERS button in planner footer")
        y -= tip_h + 8

        # 4-col × 5-row sticker grid
        COLS, ROWS = 4, 5
        cw = CW / COLS - 5
        rh = (y - _MB - 26) / ROWS - 5

        for ri in range(ROWS):
            for ci in range(COLS):
                idx = ri * COLS + ci
                if idx >= len(examples):
                    break
                cx = _ML + ci * (cw + 5)
                cy = y - (ri + 1) * (rh + 5)
                c.setFillColorRGB(*_bl(col, 0.90))
                c.roundRect(cx, cy, cw, rh, 4, fill=1, stroke=0)
                c.setFillColorRGB(*col)
                c.setLineWidth(0.4)
                c.roundRect(cx, cy, cw, rh, 4, fill=0, stroke=1)
                c.setFillColorRGB(*DK)
                c.setFont(fn("regular"), 7)
                c.drawCentredString(cx + cw / 2, cy + rh / 2 - 4, examples[idx])

        _footer(c, T, BG, fn, PW)
        c.showPage()

    c.save()
    return buf.getvalue()


def _gen_budget_page(pcfg: dict) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR
    _page_bg(c, BG, PW, PH)
    _header_band(c, "BUDGET TRACKER", T, BG, fn, PW, PH)

    y = PH - 52 - 16
    c.setFillColorRGB(*DK)
    c.setFont(fn("bold"), 9)
    c.drawString(_ML, y, "Month: ________________    Income Goal: $____________    Savings: $____________")
    y -= 22

    col_w = CW / 2 - 4
    row_h = 22

    def col_block(x, title, rows, col):
        c.setFillColorRGB(*_bl(col, 0.82))
        c.rect(x, y - 16, col_w, 16, fill=1, stroke=0)
        c.setFillColorRGB(*BG)
        c.setFont(fn("bold"), 9)
        c.drawCentredString(x + col_w / 2, y - 12, title)
        for ri, lbl in enumerate(rows):
            ry = y - 16 - (ri + 1) * row_h
            is_tot = lbl.startswith("TOTAL")
            c.setFillColorRGB(*(_bl(col, 0.75) if is_tot else (_bl(col, 0.92) if ri % 2 == 0 else (1, 1, 1))))
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(*_bl(col, 0.55))
            c.rect(x, ry, col_w, row_h, fill=1, stroke=1)
            c.setFillColorRGB(*DK)
            c.setFont(fn("bold" if is_tot else "regular"), 8)
            c.drawString(x + 6, ry + 7, lbl)
            c.drawString(x + col_w - 50, ry + 7, "$")
            c.setLineWidth(0.4)
            c.line(x + col_w - 44, ry + 5, x + col_w - 6, ry + 5)

    col_block(_ML, "INCOME", ["Salary / Wages","Side Income","Etsy Sales","Other","TOTAL INCOME"], T)
    col_block(_ML + col_w + 8, "EXPENSES",
              ["Housing / Rent","Food / Groceries","Transport","Utilities","Entertainment",
               "Health","Shopping","Savings","Other","TOTAL EXPENSES"], A)

    n_max = 10
    bal_y = y - 16 - (n_max + 1) * row_h - 6
    if bal_y > _MB + 2:
        c.setFillColorRGB(*_bl(T, 0.75))
        c.roundRect(_ML, bal_y - 28, CW, 28, 4, fill=1, stroke=0)
        c.setFillColorRGB(*BG)
        c.setFont(fn("bold"), 10)
        c.drawString(_ML + 8, bal_y - 18, "BALANCE (Income - Expenses):  $_________________________")

    _footer(c, T, BG, fn, PW)
    c.showPage()
    c.save()
    return buf.getvalue()


def _gen_meal_plan_page(pcfg: dict) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR
    _page_bg(c, BG, PW, PH)
    _header_band(c, "MEAL PLANNER", T, BG, fn, PW, PH)

    y = PH - 52 - 16
    c.setFillColorRGB(*DK)
    c.setFont(fn("bold"), 9)
    c.drawString(_ML, y, "Week of: ________________________    Calories/day: ______    Water: ______oz")
    y -= 22

    DAYS = ["MON","TUE","WED","THU","FRI","SAT","SUN"]
    MEALS = ["Breakfast", "Lunch", "Dinner", "Snacks"]
    meal_lbl_w = 56
    day_col_w = (CW - meal_lbl_w) / 7
    day_hdr_h = 16
    meal_row_h = (y - _MB - 44) / 4

    c.setFillColorRGB(*T)
    c.rect(_ML + meal_lbl_w, y - day_hdr_h, CW - meal_lbl_w, day_hdr_h, fill=1, stroke=0)
    c.setFillColorRGB(*BG)
    c.setFont(fn("bold"), 8)
    for di, day in enumerate(DAYS):
        dx = _ML + meal_lbl_w + di * day_col_w
        c.drawCentredString(dx + day_col_w / 2, y - 12, day)

    for mi, meal in enumerate(MEALS):
        ry = y - day_hdr_h - (mi + 1) * meal_row_h
        c.setFillColorRGB(*_bl(A if mi % 2 else T, 0.80))
        c.rect(_ML, ry, meal_lbl_w, meal_row_h, fill=1, stroke=0)
        c.setFillColorRGB(*BG)
        c.setFont(fn("bold"), 7.5)
        c.saveState()
        c.translate(_ML + meal_lbl_w / 2, ry + meal_row_h / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, meal)
        c.restoreState()
        for di in range(7):
            dx = _ML + meal_lbl_w + di * day_col_w
            c.setFillColorRGB(*(_bl(T, 0.95) if di % 2 == 0 else (1, 1, 1)))
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(*_bl(T, 0.65))
            c.rect(dx, ry, day_col_w, meal_row_h, fill=1, stroke=1)
            c.setLineWidth(0.2)
            c.setStrokeColorRGB(*_bl(T, 0.80))
            for li in range(int(meal_row_h / 14)):
                ly = ry + meal_row_h - 10 - li * 14
                if ly > ry + 4:
                    c.line(dx + 2, ly, dx + day_col_w - 2, ly)

    # Grocery list
    bot_y = y - day_hdr_h - 4 * meal_row_h - 8
    if bot_y > _MB + 2:
        bot_h = bot_y - _MB - 2
        c.setFillColorRGB(*_bl(T, 0.90))
        c.roundRect(_ML, _MB + 2, CW, bot_h, 4, fill=1, stroke=0)
        c.setFillColorRGB(*T)
        c.setFont(fn("bold"), 9)
        c.drawString(_ML + 8, _MB + bot_h - 10, "GROCERY LIST")
        cols_n = 3
        items_per = max(1, int(bot_h / 18))
        for gi in range(min(items_per * cols_n, 18)):
            gcol = gi // items_per
            gri = gi % items_per
            gx = _ML + 8 + gcol * (CW / cols_n)
            gy = _MB + bot_h - 24 - gri * 16
            if gy > _MB + 4:
                c.setFillColorRGB(*T)
                c.circle(gx + 4, gy + 4, 3, fill=1, stroke=0)
                c.setLineWidth(0.3)
                c.setStrokeColorRGB(*_bl(T, 0.55))
                c.line(gx + 12, gy, gx + CW / cols_n - 12, gy)

    _footer(c, T, BG, fn, PW)
    c.showPage()
    c.save()
    return buf.getvalue()


def _gen_lesson_plan_pages(pcfg: dict, dated: bool = True) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    year = (pcfg.get("year") or 2026) if dated else 2026
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR

    if dated:
        aug1 = _date_cls(year, 8, 1)
        wd = aug1.weekday()
        first_mon = aug1 + timedelta(days=(7 - wd) % 7 if wd else 0)
        week_starts = [first_mon + timedelta(weeks=i) for i in range(44)]
    else:
        week_starts = [None] * 44

    DAYS = ["MON","TUE","WED","THU","FRI"]
    SUBJECTS = ["Period 1", "Period 2", "Period 3", "Period 4", "Period 5"]
    subj_w = 68
    day_col_w = (CW - subj_w) / 5
    hdr_h = 18
    row_h_val = (PH - 52 - 28 - _MB - 30) / len(SUBJECTS)

    for wk_idx in range(44):
        wn = wk_idx + 1
        start = week_starts[wk_idx]
        if dated and start:
            end = start + timedelta(days=4)
            wk_lbl = f"LESSON PLAN — WEEK {wn}  ·  {start.strftime('%b %-d')} – {end.strftime('%b %-d, %Y')}"
        else:
            wk_lbl = f"LESSON PLAN — WEEK {wn}"

        _page_bg(c, BG, PW, PH)
        _header_band(c, wk_lbl, T, BG, fn, PW, PH)

        y = PH - 52 - 10
        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 8)
        c.drawString(_ML, y, "Objective:")
        c.setLineWidth(0.4)
        c.setStrokeColorRGB(*_bl(T, 0.55))
        c.line(_ML + 58, y + 3, _ML + CW, y + 3)
        y -= 18

        # Day headers
        c.setFillColorRGB(*T)
        c.rect(_ML + subj_w, y - hdr_h, CW - subj_w, hdr_h, fill=1, stroke=0)
        c.setFillColorRGB(*BG)
        c.setFont(fn("bold"), 9)
        for di, day in enumerate(DAYS):
            dx = _ML + subj_w + di * day_col_w
            if dated and start:
                dd = start + timedelta(days=di)
                c.drawCentredString(dx + day_col_w / 2, y - 13, f"{day} {dd.strftime('%m/%d')}")
            else:
                c.drawCentredString(dx + day_col_w / 2, y - 13, day)

        for si, subj in enumerate(SUBJECTS):
            ry = y - hdr_h - (si + 1) * row_h_val
            c.setFillColorRGB(*_bl(A if si % 2 else T, 0.80))
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(*_bl(T, 0.60))
            c.rect(_ML, ry, subj_w, row_h_val, fill=1, stroke=1)
            c.setFillColorRGB(*BG)
            c.setFont(fn("bold"), 7.5)
            c.drawCentredString(_ML + subj_w / 2, ry + row_h_val / 2 - 4, subj)
            for di in range(5):
                dx = _ML + subj_w + di * day_col_w
                c.setFillColorRGB(*(_bl(T, 0.95) if di % 2 == 0 else (1, 1, 1)))
                c.rect(dx, ry, day_col_w, row_h_val, fill=1, stroke=1)
                c.setLineWidth(0.2)
                c.setStrokeColorRGB(*_bl(T, 0.80))
                for li in range(int(row_h_val / 14)):
                    ly = ry + row_h_val - 10 - li * 14
                    if ly > ry + 4:
                        c.line(dx + 2, ly, dx + day_col_w - 2, ly)

        notes_y = y - hdr_h - len(SUBJECTS) * row_h_val - 4
        if notes_y > _MB + 2:
            nh = notes_y - _MB - 2
            c.setFillColorRGB(*_bl(T, 0.90))
            c.roundRect(_ML, _MB + 2, CW, nh, 4, fill=1, stroke=0)
            c.setFillColorRGB(*T)
            c.setFont(fn("bold"), 8)
            c.drawString(_ML + 8, _MB + nh - 10, "NOTES / HOMEWORK DUE / REMINDERS:")

        _footer(c, T, BG, fn, PW)
        c.showPage()

    c.save()
    return buf.getvalue()


def _gen_class_roster_pages(pcfg: dict) -> bytes:
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    CW = PW - _ML - _MR

    for ci in range(6):
        _page_bg(c, BG, PW, PH)
        _header_band(c, f"CLASS ROSTER — PERIOD {ci + 1}", T, BG, fn, PW, PH)
        y = PH - 52 - 16
        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 9)
        c.drawString(_ML, y, "Class: ___________________   Room: _______   Period: ___   Time: _________")
        y -= 20

        COLS = ["#", "Student Name", "Email / Contact", "Notes"]
        col_ws = [22, 138, 160, 0]
        col_ws[-1] = CW - sum(col_ws[:-1])
        hdr_h = 18
        row_h_r = (y - _MB - 26) / 35

        hx = _ML
        for cw_v, cl in zip(col_ws, COLS):
            c.setFillColorRGB(*T)
            c.rect(hx, y - hdr_h, cw_v, hdr_h, fill=1, stroke=0)
            c.setFillColorRGB(*BG)
            c.setFont(fn("bold"), 8)
            c.drawCentredString(hx + cw_v / 2, y - 13, cl)
            hx += cw_v

        for ri in range(35):
            ry = y - hdr_h - (ri + 1) * row_h_r
            rx = _ML
            c.setFillColorRGB(*(_bl(T, 0.93) if ri % 2 == 0 else (1, 1, 1)))
            c.setLineWidth(0.3)
            c.setStrokeColorRGB(*_bl(T, 0.65))
            for cw_v in col_ws:
                c.rect(rx, ry, cw_v, row_h_r, fill=1, stroke=1)
                rx += cw_v
            c.setFillColorRGB(*DK)
            c.setFont(fn("regular"), 7)
            c.drawCentredString(_ML + col_ws[0] / 2, ry + row_h_r / 2 - 3, str(ri + 1))

        _footer(c, T, BG, fn, PW)
        c.showPage()

    c.save()
    return buf.getvalue()


# ── Main page assembler ───────────────────────────────────────────────────────

def _make_planner_pages(cfg: dict, dated: bool = True) -> bytes:
    """Generate all non-cover pages for a planner config entry."""
    from tools.planner_page_adder import _make_pages

    year = cfg.get("year") if dated else None
    specialty = cfg.get("specialty", "life")
    sections = cfg.get("sections", [])

    # planner_page_adder expects these key names
    pcfg = {
        "title":    cfg["name"],
        "subtitle": cfg["subtitle"],
        "year":     year,
        "theme":    cfg["theme_rgb"],
        "accent":   cfg["accent_rgb"],
        "bg":       cfg["bg_rgb"],
        "dark":     cfg["dark_rgb"],
        "sections": sections,
        "specialty": specialty,
        "specialty_pages": [],
    }

    def _sec_has(keyword):
        return any(keyword.lower() in s.lower() for s in sections)

    all_chunks: list[bytes] = []

    def _try(label, fn_call):
        try:
            result = fn_call()
            if result:
                all_chunks.append(result)
        except Exception as e:
            print(f"    Warning: {label} failed: {e}")

    # Navigation pages (always)
    for nav in ("welcome", "dashboard", "index"):
        _try(nav, lambda n=nav: _make_pages(pcfg, n))

    # Yearly overview
    if _sec_has("yearly") or _sec_has("year at"):
        _try("yearly overview", lambda: _gen_yearly_overview(pcfg, dated))

    # Monthly calendars (always)
    _try("monthly calendars", lambda: _gen_monthly_pages(pcfg, dated))

    # Monthly reviews
    if _sec_has("monthly review"):
        _try("monthly reviews", lambda: _gen_monthly_review_pages(pcfg))

    # Month at a glance
    if _sec_has("at a glance"):
        _try("month at a glance", lambda: _gen_month_at_a_glance(pcfg))

    # Weekly pages or teacher lesson plans
    if specialty == "teacher":
        _try("lesson plans", lambda: _gen_lesson_plan_pages(pcfg, dated))
        _try("class rosters", lambda: _gen_class_roster_pages(pcfg))
    else:
        _try("weekly spreads", lambda: _gen_weekly_pages(pcfg, dated))

    # ADHD specialty pages
    if specialty == "adhd":
        for sp in ("pomodoro", "brain_dump", "priority_matrix"):
            _try(sp, lambda s=sp: _make_pages(pcfg, "specialty", specialty=s))

    # Dark mode brain dump
    if specialty == "dark_mode":
        _try("brain_dump", lambda: _make_pages(pcfg, "specialty", specialty="brain_dump"))

    # Budget tracker
    if _sec_has("budget"):
        _try("budget page", lambda: _gen_budget_page(pcfg))

    # Meal planner
    if _sec_has("meal"):
        _try("meal plan page", lambda: _gen_meal_plan_page(pcfg))

    # Habit tracker (always)
    _try("habit tracker", lambda: _gen_habit_tracker(pcfg))

    # Goals (always)
    _try("goals page", lambda: _gen_goals_page(pcfg))

    # Notes pages
    _try("notes pages", lambda: _gen_notes_pages(pcfg, count=4))

    # Sticker library pages
    _try("sticker library", lambda: _gen_sticker_library(pcfg))

    return _merge_pdfs(*all_chunks)


# ── Cover page & image ────────────────────────────────────────────────────────

def _make_cover_page(cfg: dict, cover_image_path: str | None) -> bytes:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import LETTER
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=LETTER)
    PW, PH = LETTER
    bg = cfg["bg_rgb"]
    theme = cfg["theme_rgb"]
    dark = cfg["dark_rgb"]

    c.setFillColorRGB(*bg)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)

    if cover_image_path and os.path.exists(cover_image_path):
        from reportlab.lib.utils import ImageReader
        img = ImageReader(cover_image_path)
        margin = 40
        c.drawImage(img, margin, margin + 80, width=PW - 2*margin, height=PH - 2*margin - 160,
                    preserveAspectRatio=True, anchor="c", mask="auto")
    else:
        c.setFillColorRGB(*theme)
        c.rect(40, 120, PW - 80, PH - 200, fill=1, stroke=0)
        c.setFillColorRGB(*bg)
        c.setFont("Helvetica", 11)
        c.drawCentredString(PW / 2, PH / 2 + 20, "[Cover illustration — add via Canva or gpt-image-1]")

    c.setFillColorRGB(*dark)
    c.rect(0, 0, PW, 100, fill=1, stroke=0)
    c.setFillColorRGB(*bg)
    c.setFont("Helvetica-Bold", 16)
    year_label = str(cfg.get("year") or "")
    title_text = cfg["name"] + (f" {year_label}" if year_label and year_label not in cfg["name"] else "")
    c.drawCentredString(PW / 2, 68, title_text)
    c.setFont("Helvetica", 11)
    c.drawCentredString(PW / 2, 45, cfg["subtitle"])
    c.setFont("Helvetica", 9)
    c.drawCentredString(PW / 2, 22, "OnBrandCraftz · Instant Digital Download")

    c.showPage()
    c.save()
    return buf.getvalue()


def _generate_cover_image(cfg: dict, out_path: str) -> bool:
    from tools.image_gen import generate_image, ImageGenError, PORTRAIT
    prompt = cfg.get("cover_prompt", "Kawaii digital planner cover illustration")
    try:
        generate_image(prompt, out_path, size=PORTRAIT, quality="high")
        print(f"    Cover image saved → {out_path}")
        return True
    except ImageGenError as e:
        print(f"    [generate_planner] Cover generation failed: {e}")
        return False


def _merge_pdfs(*pdf_bytes_list: bytes) -> bytes:
    from PyPDF2 import PdfWriter, PdfReader
    writer = PdfWriter()
    for pdf_bytes in pdf_bytes_list:
        if pdf_bytes:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ── Orchestrator ──────────────────────────────────────────────────────────────

def generate_planner(pid: str, no_cover: bool = False) -> Path:
    cfg = PLANNER_CONFIGS.get(pid)
    if not cfg:
        print(f"Unknown planner ID '{pid}'. Run with --list to see options.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Generating {pid}: {cfg['name']}")
    print(f"  Theme: {cfg['subtitle']}")
    print(f"{'='*60}")

    out_dir = PRODUCT_FILES_DIR

    # ── Step 1: Cover image ───────────────────────────────────────────────
    cover_img_path = str(out_dir / f"{pid}_cover.png")
    if no_cover:
        cover_img_path = None
        print("  [1/5] Cover generation skipped (--no-cover)")
    else:
        print("  [1/5] Generating cover image with gpt-image-1...")
        if not _generate_cover_image(cfg, cover_img_path):
            cover_img_path = None
            print("        Continuing without cover image.")

    # ── Step 2: Cover page PDF ────────────────────────────────────────────
    print("  [2/5] Building cover page PDF...")
    try:
        cover_pdf_bytes = _make_cover_page(cfg, cover_img_path)
        print(f"        Cover page: OK")
    except Exception as e:
        print(f"        Cover page failed: {e}")
        cover_pdf_bytes = b""

    # ── Step 3: Dated content pages ───────────────────────────────────────
    print("  [3/5] Building dated content pages...")
    try:
        content_bytes = _make_planner_pages(cfg, dated=True)
        print(f"        Content pages: OK")
    except Exception as e:
        print(f"        Content pages failed: {e}")
        content_bytes = b""

    # ── Step 4: Assemble dated PDF ────────────────────────────────────────
    print("  [4/5] Assembling dated PDF...")
    dated_path = None
    try:
        full_pdf = _merge_pdfs(cover_pdf_bytes, content_bytes)
        dated_path = out_dir / f"{pid}.pdf"
        with open(dated_path, "wb") as f:
            f.write(full_pdf)
        from PyPDF2 import PdfReader as _PR
        n_pages = len(_PR(io.BytesIO(full_pdf)).pages)
        size_mb = len(full_pdf) / 1024 / 1024
        print(f"        Dated PDF → {dated_path}  ({n_pages} pages, {size_mb:.1f} MB)")
    except Exception as e:
        print(f"        PDF assembly failed: {e}")

    # ── Step 5: Undated version ───────────────────────────────────────────
    print("  [5/5] Building undated (evergreen) version...")
    try:
        content_undated = _make_planner_pages(cfg, dated=False)
        undated_pdf = _merge_pdfs(cover_pdf_bytes, content_undated)
        undated_path = out_dir / f"{pid}U.pdf"
        with open(undated_path, "wb") as f:
            f.write(undated_pdf)
        from PyPDF2 import PdfReader as _PR2
        n_pages_u = len(_PR2(io.BytesIO(undated_pdf)).pages)
        size_mb_u = len(undated_pdf) / 1024 / 1024
        print(f"        Undated PDF → {undated_path}  ({n_pages_u} pages, {size_mb_u:.1f} MB)")
    except Exception as e:
        print(f"        Undated PDF failed: {e}")

    print(f"\n  {'─'*56}")
    print(f"  {pid} generation complete.")
    print(f"  Listing title: {cfg['listing_title']}")
    print(f"  Price: ${cfg['price']:.2f}")
    print(f"  Next steps:")
    print(f"    1. Review PDF in GoodNotes — verify all pages render correctly")
    print(f"    2. Generate sticker pack:  python tools/gen_sticker_sheet.py {pid}")
    print(f"    3. Generate listing photos: python tools/gen_planner_listing_photos.py --pid {pid}")
    print(f"    4. Create Etsy listing via the publisher pipeline")
    if not cover_img_path:
        print(f"    NOTE: Cover image not generated — add manually in Canva")
    print(f"  {'─'*56}\n")

    return dated_path


def list_configs() -> None:
    print("\nAvailable planner configs:\n")
    for pid, cfg in PLANNER_CONFIGS.items():
        year = cfg.get("year") or "Undated"
        print(f"  {pid}  {cfg['name']}  ({cfg['subtitle']})")
        print(f"        Price: ${cfg['price']:.2f}  ·  ~{cfg['page_count']} pages  ·  Year: {year}")
        print(f"        {cfg['description_hook'][:80]}...")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a new digital planner product")
    parser.add_argument("planner_id", nargs="?", help="e.g. DP1030")
    parser.add_argument("--list",     action="store_true", help="List all planner configs")
    parser.add_argument("--no-cover", action="store_true", help="Skip gpt-image-1 cover generation")
    args = parser.parse_args()

    if args.list or not args.planner_id:
        list_configs()
    else:
        generate_planner(args.planner_id.upper(), no_cover=args.no_cover)
