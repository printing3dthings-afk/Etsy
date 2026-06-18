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
import argparse
from pathlib import Path

import fitz  # PyMuPDF

_BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCT_FILES_DIR = _BASE_DIR / "data" / "digital_products" / "product_files"

PW, PH = 612.0, 792.0  # US Letter, matches _new_canvas() in generate_planner.py

# Celestial Night palette (hex -> 0-255 tuples)
INDIGO_TOP = (20, 18, 46)      # #14122E
SPACE_PURPLE = (45, 43, 85)    # #2D2B55
INDIGO = (30, 27, 75)          # #1E1B4B
GOLD = (201, 168, 76)          # #C9A84C
MOONBEAM = (240, 238, 248)     # #F0EEF8


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


def build_cover_png(out_path, title, subtitle, year, shop="OnBrandCraftz"):
    """Deep night-sky cover: gradient, stars, constellation, crescent moon, gold title."""
    from PIL import Image, ImageDraw, ImageFilter

    S = 2  # supersample factor for crisp edges
    W, H = int(PW) * S, int(PH) * S
    img = Image.new("RGB", (W, H), INDIGO)
    draw = ImageDraw.Draw(img)

    # Vertical gradient: indigo-top -> space purple (middle) -> indigo
    for y in range(H):
        f = y / float(H)
        if f < 0.5:
            g = f / 0.5
            col = tuple(int(INDIGO_TOP[i] + (SPACE_PURPLE[i] - INDIGO_TOP[i]) * g) for i in range(3))
        else:
            g = (f - 0.5) / 0.5
            col = tuple(int(SPACE_PURPLE[i] + (INDIGO[i] - SPACE_PURPLE[i]) * g) for i in range(3))
        draw.line([(0, y), (W, y)], fill=col)

    rng = random.Random(2026)
    # Scattered stars (gold + white), varied size, soft glow on the big ones
    stars = []
    for _ in range(260):
        x, y = rng.randint(0, W), rng.randint(0, int(H * 0.92))
        r = rng.choice([1, 1, 1, 2, 2, 3]) * S
        bright = rng.random()
        col = GOLD if bright > 0.55 else (235, 233, 245)
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
    gold_layer = Image.new("RGB", (W, H), GOLD)
    img.paste(gold_layer, (0, 0), moon)

    # Thin gold double border frame
    m = int(20 * S)
    draw.rectangle([m, m, W - m, H - m], outline=GOLD, width=max(1, S))
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
        centered(ln, ty, title_font, GOLD)
        ty += int(66 * S)

    centered("✦  " + subtitle.upper() + "  ✦", ty + int(10 * S), _font(26 * S), MOONBEAM)
    if year:
        centered(str(year), ty + int(54 * S), _font(40 * S, bold=True), MOONBEAM)
    centered(shop.upper(), H - int(70 * S), _font(20 * S), (170, 160, 200))

    img = img.resize((int(PW), int(PH)), Image.LANCZOS)
    img.save(out_path)
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
    return found


# section label (as it appears in cfg["sections"]) -> detection key
def _label_to_key(label):
    l = label.lower()
    if "welcome" in l: return "welcome"
    if "dashboard" in l: return "dashboard"
    if "index" in l: return "index"
    if "yearly" in l or "year at" in l or "year in" in l: return "yearly"
    if "monthly review" in l: return "monthly_review"
    if "at a glance" in l: return "glance"
    if "monthly cal" in l or l.startswith("monthly"): return "monthly"
    if "weekly" in l: return "weekly"
    if "daily" in l: return "daily"
    if "brain dump" in l or "priority matrix" in l: return "brain_dump"
    if "habit" in l: return "habit"
    if "smart goal" in l or l == "goals" or "goals" in l: return "goals"
    if "budget" in l: return "budget"
    if "meal" in l: return "meal"
    if "note" in l: return "notes"
    if "sticker" in l: return "stickers"
    return None


# ---------------------------------------------------------------------------
# 3. Coordinate helpers (reportlab bottom-left -> fitz top-left)
# ---------------------------------------------------------------------------

def _rl_rect(x, y, w, h):
    """reportlab (x, y_bottom, w, h) -> fitz.Rect."""
    return fitz.Rect(x, PH - (y + h), x + w, PH - y)


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
    ("monthly", "Monthly Calendars"),
    ("monthly_review", "Monthly Reviews"),
    ("glance", "Month at a Glance"),
    ("weekly", "Weekly Spreads"),
    ("daily", "Daily Pages"),
    ("brain_dump", "Brain Dump & Priority Matrix"),
    ("habit", "Habit Tracker"),
    ("goals", "SMART Goals"),
    ("budget", "Budget Tracker"),
    ("meal", "Meal Planner"),
    ("notes", "Notes"),
    ("stickers", "Sticker Library"),
]


def finalize_pdf(src_path, out_path, sections, title, subtitle, year,
                 cover_png=None):
    doc = fitz.open(str(src_path))

    found = _detect_sections(doc)
    dash_page = found.get("dashboard")

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
    return n, len(toc)


def finalize(pid, make_cover=True):
    pcfg_sections, title, subtitle, year = _load_cfg(pid)

    cover_png = None
    if make_cover:
        cover_png = PRODUCT_FILES_DIR / f"{pid}_cover.png"
        build_cover_png(cover_png, title, subtitle, year)
        print(f"  Cover -> {cover_png}")

    results = []
    for suffix, yr in ((f"{pid}_v2.pdf", year), (f"{pid}U_v2.pdf", None)):
        src = PRODUCT_FILES_DIR / suffix
        if not src.exists():
            print(f"  (skip {suffix} — not found)")
            continue
        out = PRODUCT_FILES_DIR / suffix.replace("_v2.pdf", "_v2_final.pdf")
        n, ntoc = finalize_pdf(src, out, pcfg_sections, title, subtitle, yr,
                               cover_png=cover_png)
        print(f"  {out.name}: {n} pages, {ntoc} outline entries, links added")
        results.append(out)
    return results


def _load_cfg(pid):
    if str(_BASE_DIR) not in sys.path:
        sys.path.insert(0, str(_BASE_DIR))
    from tools.generate_planner_v2 import _normalize_cfg
    pcfg, _meta = _normalize_cfg(pid)
    return pcfg["sections"], pcfg["title"], pcfg["subtitle"], pcfg.get("year")


def main():
    ap = argparse.ArgumentParser(description="Add a cover + real hyperlink navigation to a v2 planner PDF.")
    ap.add_argument("pid")
    ap.add_argument("--no-cover", action="store_true")
    args = ap.parse_args()
    finalize(args.pid.upper(), make_cover=not args.no_cover)


if __name__ == "__main__":
    main()
