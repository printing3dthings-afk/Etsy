#!/usr/bin/env python3
"""
generate_wall_calendar.py — WC-series printable wall calendar generator.

Produces one themed wall-calendar product: 12 AI-generated seasonal header
illustrations (reused verbatim across the dated/undated/week-start variants
so art cost stays fixed regardless of how many PDF variants ship), a dated
2026 monthly-grid PDF, an undated evergreen monthly-grid PDF, and a
year-at-a-glance poster JPG — packaged into one ZIP per product.

Design decisions worth recording (came out of a real competitive-research +
adversarial-review pass, 2026-08-11, before any of this was built):

  - Reuses generate_planner.py/generate_planner_v2.py's reportlab primitives
    (_new_canvas, _page_bg, _textured_bg, _draw_binding, _gradient_header,
    _smart_footer, _get_fn, _bl, _merge_pdfs, _MONTHS) rather than
    reimplementing page rendering — same visual language as the existing
    planner line, one less rendering system to maintain.
  - Reuses the EXACT existing theme RGB tuples for Sage Garden (DP1031),
    Matcha Serenity (DP1030), and Sunflower Studio (DP1033) from
    generate_planner.py's PLANNER_CONFIGS rather than re-deriving them from
    hex — avoids any color drift between the planner line and this one.
  - Week-start (Sunday vs. Monday) is a REAL, buyer-searched attribute for
    calendars specifically (confirmed in real Etsy title patterns) that the
    existing planner pipeline has never needed — _v2_monthly_pages() is
    hardcoded Monday-start. Built as a local, self-contained parameter here
    rather than retrofitting the shared planner code (which works today and
    ships to buyers; don't destabilize it for a different product's needs).
  - The undated/evergreen monthly grid deliberately renders ZERO day
    numbers — only the weekday column headers (which are calendar-agnostic
    and valid for literally any year). generate_planner_v2._v2_monthly_pages
    (dated=False) still silently computes real weekday alignment from
    date.today().year even in "undated" mode -- correct enough for a
    notebook-style planner page, but a real defect for a WALL CALENDAR
    specifically, where a buyer is actually using the grid to track real
    dates. Caught in review before this shipped; fixed by never rendering
    ANY date-to-weekday alignment in the undated variant instead of
    inheriting that pattern.
  - The monthly-grid PDF is delivered at ONE size (US Letter, matching the
    existing planner convention) and is NOT run through generate_print_
    sizes.py — that tool resizes a single flat image, and a US-Letter-laid-
    out PDF does not correctly re-flow to 18x24/A4/A3 (different aspect
    ratios: 18x24=0.75, Letter=0.773, A4/A3=0.707 — content would crop).
    Only the year-at-a-glance poster (a single flat JPG) goes through the
    real multi-size pipeline. Every size claim in the listing must be true
    of an actual delivered file — this split is what keeps that true.

Run: python tools/generate_wall_calendar.py --pid WC1001 --theme sage_garden
"""
import argparse
import calendar as _cal
import json
import os
import sys
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent.parent.resolve()
for _p in (BASE, BASE / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from tools.generate_planner import (  # noqa: E402
    _new_canvas, _page_bg, _get_fn, _bl, _merge_pdfs, _MONTHS, _ML, _MR, SHOP_NAME,
)
from tools.generate_planner_v2 import (  # noqa: E402
    _gradient_header, _smart_footer, _textured_bg, _draw_binding,
)

NEW_YEAR = 2026  # matches every other 2026-dated product in this shop; bump alongside them


def _resolve_dp_base() -> Path:
    """Same volume-aware resolution as generate_coloring_pages.py's
    _resolve_dp_base() (identical docstring reasoning: Railway's ephemeral
    local filesystem wipes on redeploy, so a build must land on the durable
    volume when one is mounted)."""
    vol = os.getenv("HUB_FILES_DIR", "").strip()
    if vol and Path(vol).is_dir():
        return Path(vol)
    if Path("/data/files").is_dir():
        return Path("/data/files")
    return BASE / "data" / "digital_products"


CALENDAR_DIR = _resolve_dp_base() / "wall_calendars"
ART_DIR = CALENDAR_DIR / "art"
PACKS_DIR = CALENDAR_DIR / "packs"

# ── Theme catalog — reused verbatim from generate_planner.py's PLANNER_CONFIGS
# (DP1031 Sage Garden, DP1030 Matcha Serenity, DP1033 Sunflower Studio) so
# this product line's palette can never drift from the already-shipped one.
CALENDAR_THEMES = {
    "sage_garden": {
        "label": "Sage Garden",
        "theme_rgb": (0.545, 0.659, 0.533),   # #8BA888
        "accent_rgb": (0.784, 0.867, 0.710),  # #C8DDB5
        "bg_rgb": (0.965, 0.973, 0.949),      # #F6F8F2
        "dark_rgb": (0.173, 0.220, 0.157),    # #2C3828
        "hex_primary": "#8BA888",
        "motifs": "tiny mushrooms, herb sprigs, watering cans, garden snails, terracotta flower pots, bees",
        "aesthetic": "cottagecore, botanical, garden, calm nature",
    },
    "matcha_serenity": {
        "label": "Matcha Serenity",
        "theme_rgb": (0.420, 0.561, 0.369),   # #6B8F5E
        "accent_rgb": (0.722, 0.800, 0.557),  # #B8CC8E
        "bg_rgb": (0.969, 0.976, 0.953),      # #F7F9F3
        "dark_rgb": (0.118, 0.176, 0.094),    # #1E2D18
        "hex_primary": "#6B8F5E",
        "motifs": "matcha cups, bamboo, koi fish, zen stones, lotus flowers, tiny bento boxes",
        "aesthetic": "Japanese minimalist, matcha cafe, slow living, mindfulness",
    },
    "sunflower_studio": {
        "label": "Sunflower Studio",
        "theme_rgb": (0.957, 0.769, 0.188),   # #F4C430
        "accent_rgb": (0.290, 0.486, 0.349),  # #4A7C59
        "bg_rgb": (1.000, 0.992, 0.941),      # #FFFDF0
        "dark_rgb": (0.165, 0.102, 0.000),    # #2A1A00
        "hex_primary": "#F4C430",
        "motifs": "sunflowers, bees, garden tools, butterflies, ladybugs, seeds sprouting",
        "aesthetic": "bright botanical, positive, cheerful, nature and sunshine",
    },
}

# Seasonal motif skew per month — keeps the 12 header illustrations feeling
# like a real year's progression rather than 12 identical generic scenes,
# without leaving the theme's own motif vocabulary (never invents new colors
# or subjects outside what CALENDAR_THEMES already documents).
_MONTH_SEASON_NOTE = {
    1: "crisp winter version of", 2: "cozy late-winter version of", 3: "early spring version of",
    4: "fresh spring version of", 5: "blooming late-spring version of", 6: "bright early-summer version of",
    7: "warm midsummer version of", 8: "late-summer version of", 9: "early-autumn version of",
    10: "golden autumn version of", 11: "late-autumn version of", 12: "festive winter version of",
}

_STYLE_ANCHOR = (
    "Flat kawaii illustration style, clean vector-like linework, soft rounded shapes. "
    "Wide horizontal banner composition, subject cluster concentrated in the lower two-thirds "
    "of the frame, generous open space in the upper third for text to be added later. "
    "No text, no numbers, no watermarks, no calendar grids, no dates anywhere in the image. "
    "Consistent flat lighting, no photorealistic rendering."
)

DAYS_MON_START = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
DAYS_SUN_START = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]


def _week_start_days(week_start: str) -> list[str]:
    return DAYS_SUN_START if week_start == "sun" else DAYS_MON_START


def _first_col_index(year: int, month: int, week_start: str) -> int:
    """Column index (0-6) of day 1, in the chosen week_start's column order.
    calendar.monthrange's first weekday is always 0=Monday regardless of
    week_start -- shift it when the display order starts on Sunday."""
    first_wd_mon0, _n_days = _cal.monthrange(year, month)
    if week_start == "sun":
        return (first_wd_mon0 + 1) % 7
    return first_wd_mon0


def month_header_art_path(theme_key: str, month: int) -> Path:
    return ART_DIR / f"{theme_key}_{month:02d}_header.png"


def generate_month_header_art(theme_key: str, month: int, engine: str | None = None, regen: bool = False) -> Path:
    """One AI-generated seasonal header illustration per month (12 per theme,
    cached to disk — a second build for the same theme costs nothing extra).
    Uses the approved-engine pipeline only (tools/image_gen.py), same as
    every other art call in this shop."""
    from tools.image_gen import generate_image, LANDSCAPE, ImageGenError

    dst = month_header_art_path(theme_key, month)
    if dst.exists() and not regen:
        return dst
    theme = CALENDAR_THEMES[theme_key]
    month_name = _MONTHS[month - 1]
    season_note = _MONTH_SEASON_NOTE[month]
    prompt = (
        f"A {season_note} a kawaii illustrated scene featuring {theme['motifs']}. "
        f"Aesthetic: {theme['aesthetic']}. Color palette strictly limited to {theme['hex_primary']} "
        f"and its tonal family — no other dominant colors appear. "
        f"{_STYLE_ANCHOR}"
    )
    ART_DIR.mkdir(parents=True, exist_ok=True)
    try:
        generate_image(prompt, dst, size=LANDSCAPE, output_format="png", engine=engine)
    except ImageGenError as exc:
        print(f"  ✗ {theme_key} {month_name} header art failed: {exc}", file=sys.stderr)
        raise
    print(f"  ✓ {theme_key} {month_name} header art")
    return dst


def build_monthly_grid_pdf(theme_key: str, year: int, week_start: str = "mon", dated: bool = True) -> bytes:
    """12-page monthly grid PDF, one reportlab page per month. dated=True
    renders real day numbers aligned to `year`'s actual weekdays; dated=False
    renders ONLY the weekday column headers (calendar-agnostic, valid for any
    year) with every day cell left blank for the buyer to fill in by hand —
    see this module's docstring for why that's deliberate, not a shortcut."""
    theme = CALENDAR_THEMES[theme_key]
    T, A, BG, DK = theme["theme_rgb"], theme["accent_rgb"], theme["bg_rgb"], theme["dark_rgb"]
    days = _week_start_days(week_start)
    chunks = []
    for month in range(1, 13):
        c, buf, PW, PH = _new_canvas()
        fn = _get_fn()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        mname = _MONTHS[month - 1]
        yr_label = str(year) if dated else ""
        _gradient_header(c, f"{mname} {yr_label}".strip(), T, A, BG, fn, PW, PH)

        header_art = month_header_art_path(theme_key, month)
        art_top = PH - 58 - 14
        art_h = 90.0
        if header_art.exists():
            c.drawImage(str(header_art), _ML, art_top - art_h, width=PW - _ML - _MR,
                        height=art_h, preserveAspectRatio=True, anchor="c", mask="auto")

        ML = _ML
        top = art_top - art_h - 10
        grid_bottom = 40.0
        days_hdr_h = 18.0
        dw = (PW - _MR - ML) / 7.0
        for di, dname in enumerate(days):
            dx = ML + di * dw
            weekend = dname in ("SAT", "SUN")
            c.setFillColorRGB(*(_bl(A, 0.5) if weekend else T))
            c.rect(dx, top - days_hdr_h, dw - 1.2, days_hdr_h, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont(fn("bold"), 8)
            c.drawCentredString(dx + dw / 2.0, top - days_hdr_h + 5, dname)

        n_rows = 6
        row_h = (top - days_hdr_h - grid_bottom) / float(n_rows)
        if dated:
            first_col = _first_col_index(year, month, week_start)
            _n_first, n_days = _cal.monthrange(year, month)
        else:
            first_col = None
            n_days = 0
        day_num = 1
        for r in range(n_rows):
            for col in range(7):
                idx = r * 7 + col
                cx0 = ML + col * dw
                cy0 = top - days_hdr_h - (r + 1) * row_h
                weekend = days[col] in ("SAT", "SUN")
                c.setFillColorRGB(*(_bl(A, 0.92) if weekend else (1, 1, 1)))
                c.rect(cx0, cy0, dw - 1.2, row_h - 1.2, fill=1, stroke=0)
                c.setStrokeColorRGB(*_bl(DK, 0.6))
                c.setLineWidth(0.4)
                c.rect(cx0, cy0, dw - 1.2, row_h - 1.2, fill=0, stroke=1)
                if dated and idx >= first_col and day_num <= n_days:
                    c.setFillColorRGB(*T)
                    c.circle(cx0 + 12, cy0 + row_h - 12, 9, fill=1, stroke=0)
                    c.setFillColorRGB(1, 1, 1)
                    c.setFont(fn("bold"), 8.5)
                    c.drawCentredString(cx0 + 12, cy0 + row_h - 14.5, str(day_num))
                    day_num += 1
                # dated=False: every cell stays blank — no numbers, no weekday
                # alignment baked in, so the grid is genuinely valid for any year.

        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="MONTH", next_lbl="MONTH")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


def _load_font(size: int, bold: bool = False):
    fonts_dir = BASE / "assets" / "fonts"
    name = "Poppins-Bold.ttf" if bold else "Poppins-Regular.ttf"
    fp = fonts_dir / name
    if fp.exists():
        try:
            return ImageFont.truetype(str(fp), size)
        except Exception:
            pass
    return ImageFont.load_default()


def _rgb255(rgb_float: tuple[float, float, float]) -> tuple[int, int, int]:
    return tuple(int(round(v * 255)) for v in rgb_float)


def build_year_at_a_glance_poster(theme_key: str, year: int, week_start: str = "mon") -> Path:
    """Single flat JPG: hero header art + 12 small month-grid thumbnails
    (dated, since an undated year-at-a-glance poster has nothing useful to
    show without a hero art image being repeated 12x). Built with PIL text/
    grid overlay on the AI background — matches the existing wall-art rule
    that no image engine reliably renders small calendar-grid text baked in."""
    theme = CALENDAR_THEMES[theme_key]
    BG = _rgb255(theme["bg_rgb"])
    T = _rgb255(theme["theme_rgb"])
    A = _rgb255(theme["accent_rgb"])
    DK = _rgb255(theme["dark_rgb"])
    days = _week_start_days(week_start)

    W = H = 3000
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    hero_path = month_header_art_path(theme_key, 1)
    if hero_path.exists():
        hero = Image.open(hero_path).convert("RGB")
        hero_h = int(H * 0.16)
        hero_w = W
        hero = hero.resize((hero_w, hero_h))
        img.paste(hero, (0, 0))
        title_y = hero_h + 30
    else:
        title_y = 30

    title_font = _load_font(90, bold=True)
    draw.text((W / 2, title_y), f"{year}", font=title_font, fill=T, anchor="ma")

    grid_top = title_y + 130
    cols, rows = 3, 4
    gap = 24
    cell_w = (W - gap * (cols + 1)) / cols
    cell_h = (H - grid_top - gap * (rows + 1)) / rows
    month_font = _load_font(34, bold=True)
    day_font = _load_font(18)
    day_hdr_font = _load_font(14, bold=True)

    # 15%-lighter-than-cell weekend tint, per CLAUDE.md's Color Design Rule 8
    # ("weekend calendar cells should be 15% lighter than weekday cells") —
    # the reportlab monthly-grid PDF already applies this; this PIL poster
    # didn't until this pass.
    weekend_tint = tuple(min(255, int(v + (255 - v) * 0.15)) for v in BG)

    for month in range(1, 13):
        idx = month - 1
        r, c = divmod(idx, cols)
        x0 = gap + c * (cell_w + gap)
        y0 = grid_top + gap + r * (cell_h + gap)
        draw.rounded_rectangle([x0, y0, x0 + cell_w, y0 + cell_h], radius=18, outline=DK, width=2)
        draw.text((x0 + cell_w / 2, y0 + 10), _MONTHS[idx], font=month_font, fill=T, anchor="ma")
        draw.line([(x0 + 20, y0 + 52), (x0 + cell_w - 20, y0 + 52)], fill=A, width=2)

        hdr_y = y0 + 60
        dw = cell_w / 7.0
        first_col = _first_col_index(year, month, week_start)
        _n_first, n_days = _cal.monthrange(year, month)
        row_h = (cell_h - 90) / 6.0

        for di, dname in enumerate(days):
            weekend_col = dname in ("SAT", "SUN")
            if weekend_col:
                draw.rounded_rectangle(
                    [x0 + di * dw + 2, hdr_y - 6, x0 + (di + 1) * dw - 2, y0 + cell_h - 6],
                    radius=8, fill=weekend_tint,
                )
            draw.text((x0 + di * dw + dw / 2, hdr_y), dname[0], font=day_hdr_font, fill=DK, anchor="ma")

        day_num = 1
        for row in range(6):
            for col in range(7):
                cellidx = row * 7 + col
                if cellidx >= first_col and day_num <= n_days:
                    cx = x0 + col * dw + dw / 2
                    cy = hdr_y + 22 + row * row_h
                    draw.text((cx, cy), str(day_num), font=day_font, fill=DK, anchor="ma")
                    day_num += 1

    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PACKS_DIR / f"{theme_key}_{year}_yearglance_{week_start}.jpg"
    img.save(out_path, "JPEG", quality=92, dpi=(300, 300))
    return out_path


def build_calendar_pack(pid: str, theme_key: str, year: int = NEW_YEAR, engine: str | None = None) -> dict:
    """Full WC-series build: 12 header illustrations, dated + undated monthly
    PDFs (both week-starts), one year-at-a-glance poster, packaged into one
    ZIP. Returns a summary dict; raises on any hard failure (never packages
    a partial/broken product)."""
    if theme_key not in CALENDAR_THEMES:
        raise ValueError(f"unknown theme {theme_key!r} (have: {', '.join(CALENDAR_THEMES)})")

    print(f"[generate_wall_calendar] {pid}: generating 12 header illustrations ({theme_key})")
    for month in range(1, 13):
        generate_month_header_art(theme_key, month, engine=engine)

    print(f"[generate_wall_calendar] {pid}: building monthly-grid PDFs")
    pdfs = {}
    for week_start in ("mon", "sun"):
        pdfs[f"dated_{week_start}"] = build_monthly_grid_pdf(theme_key, year, week_start, dated=True)
        pdfs[f"undated_{week_start}"] = build_monthly_grid_pdf(theme_key, year, week_start, dated=False)

    print(f"[generate_wall_calendar] {pid}: building year-at-a-glance poster")
    poster_path = build_year_at_a_glance_poster(theme_key, year, week_start="mon")

    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = PACKS_DIR / f"{pid.lower()}_calendar_pack.zip"
    readme = (
        f"{SHOP_NAME} — {CALENDAR_THEMES[theme_key]['label']} {year} Wall Calendar\n\n"
        f"dated_2026_monday_start.pdf / dated_2026_sunday_start.pdf\n"
        f"  12-page monthly calendar for {year}, US Letter (8.5x11in), pick the week-start you prefer.\n\n"
        f"undated_evergreen_monday_start.pdf / undated_evergreen_sunday_start.pdf\n"
        f"  Same 12-month layout with blank day cells — write in your own dates, works any year.\n\n"
        f"year_at_a_glance_poster.jpg\n"
        f"  One-page {year} overview poster. Multiple print sizes in the companion print-sizes ZIP.\n\n"
        f"Print at home on any printer, or take the files to any print shop.\n"
        f"Personal use only. Not for resale, redistribution, or commercial use.\n"
        f"© {SHOP_NAME}\n"
    )
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", readme)
        zf.writestr(f"{pid}_dated_{year}_monday_start.pdf", pdfs["dated_mon"])
        zf.writestr(f"{pid}_dated_{year}_sunday_start.pdf", pdfs["dated_sun"])
        zf.writestr(f"{pid}U_undated_monday_start.pdf", pdfs["undated_mon"])
        zf.writestr(f"{pid}U_undated_sunday_start.pdf", pdfs["undated_sun"])
        zf.write(poster_path, f"{pid}_{year}_yearglance_poster.jpg")

    print(f"[generate_wall_calendar] {pid}: DONE -> {zip_path}")
    return {
        "pid": pid, "theme": theme_key, "year": year,
        "zip_path": zip_path, "poster_path": poster_path,
    }


def main():
    ap = argparse.ArgumentParser()
    # Positional pid (not --pid) to match every other one-tap build script's
    # CLI shape -- main.py's _produce_build_product() always invokes as
    # `[script, pid] + extra_args`, same as build_coloring_product.py.
    ap.add_argument("pid")
    ap.add_argument("--theme", required=True, choices=sorted(CALENDAR_THEMES))
    ap.add_argument("--year", type=int, default=NEW_YEAR)
    ap.add_argument("--engine", default=None)
    args = ap.parse_args()
    result = build_calendar_pack(args.pid, args.theme, args.year, args.engine)
    print(json.dumps({k: (str(v) if isinstance(v, Path) else v) for k, v in result.items()}))


if __name__ == "__main__":
    main()
