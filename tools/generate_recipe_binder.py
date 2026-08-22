"""
generate_recipe_binder.py — RB1001, Digital Recipe Binder (Mocha Latte theme).

New product line approved 2026-08-20 (see chat: market research grounded in
real Etsy revenue evidence before committing). Reuses generate_planner_v2.py's
visual primitives (gradient header, drop-shadow boxes, textured background,
spiral binding, smart footer) and generate_planner.py's shared page generators
(_gen_meal_plan_page, _gen_notes_pages, _make_cover_page,
_merge_pdfs) directly -- the genuinely new work is the recipe-card page type
plus a few kitchen-specific reference pages, not a new rendering engine.

Deliberately does NOT reuse planner_page_adder.py's _make_pages() for the
welcome page -- that function hardcodes "+ Undated Edition" copy, which would
be a false claim here (this is a single evergreen PDF, not a dated+undated
pair like the DP-series planners -- recipes aren't year-specific). Welcome/
dashboard/index are custom-written below instead, using the same visual
primitives, so the copy stays accurate.

Run standalone:
    python tools/generate_recipe_binder.py
"""
import sys
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.generate_planner import (
    PRODUCT_FILES_DIR,
    SHOP_NAME,
    _get_fn,
    _bl,
    _panel_ink,
    _new_canvas,
    _page_bg,
    _ML,
    _MR,
    _MB,
    _gen_notes_pages,
    _gen_meal_plan_page,
    _make_cover_page,
    _merge_pdfs,
)
from tools.generate_planner_v2 import (
    _gradient_header,
    _shadow_box,
    _draw_binding,
    _textured_bg,
    _smart_footer,
)

OUT_DIR = Path(PRODUCT_FILES_DIR)

# ---------------------------------------------------------------------------
# Config — Mocha Latte theme, matches the approved cover art palette exactly
# ---------------------------------------------------------------------------

RB1001 = {
    "title": "Digital Recipe Binder",
    "subtitle": "Mocha Latte",
    "year": None,
    "theme": (0.545, 0.369, 0.235),   # #8B5E3C warm mocha
    "accent": (0.831, 0.663, 0.416),  # #D4A96A caramel
    "bg": (0.992, 0.973, 0.941),      # #FDF8F0 cream foam
    "dark": (0.173, 0.102, 0.055),    # #2C1A0E espresso
    "sections": [
        "Welcome & Setup", "Dashboard / Home", "Recipe Index",
        "Recipe Cards — Breakfast × 4", "Recipe Cards — Lunch × 4",
        "Recipe Cards — Dinner × 4", "Recipe Cards — Dessert × 4",
        "Recipe Cards — Snacks × 4", "Recipe Cards — Drinks × 4",
        "Recipe Cards — Holiday × 4",
        "Weekly Meal Planner", "Grocery List × 4",
        "Pantry Inventory", "Freezer Inventory",
        "Kitchen Conversion Chart", "Notes × 4",
        "Sticker Library × 9",
    ],
}

_CATEGORIES = ["Breakfast", "Lunch", "Dinner", "Dessert", "Snacks", "Drinks", "Holiday"]
_CARDS_PER_CATEGORY = 4


# ---------------------------------------------------------------------------
# Custom nav pages (accurate single-evergreen-edition copy)
# ---------------------------------------------------------------------------

def _gen_welcome_page(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    _page_bg(c, BG, PW, PH)
    c.setFillColorRGB(*T)
    c.rect(0, PH - 8, PW, 8, fill=1, stroke=0)
    c.setFillColorRGB(*A)
    c.rect(0, PH - 14, PW, 6, fill=1, stroke=0)

    y = PH - 72
    c.setFillColorRGB(*T)
    c.setFont(fn("bold"), 28)
    c.drawCentredString(PW / 2, y, "Welcome!")
    y -= 24
    c.setFillColorRGB(*DK)
    c.setFont(fn("semibold"), 13)
    c.drawCentredString(PW / 2, y, pcfg["title"])
    y -= 16
    c.setFillColorRGB(*T)
    c.setFont(fn("italic"), 10)
    c.drawCentredString(PW / 2, y, f"{pcfg['subtitle']} — Evergreen Edition (works every year, no dates to update)")

    y -= 14
    c.setFillColorRGB(*A)
    c.rect(_ML + (PW - _ML - _MR) * 0.2, y, (PW - _ML - _MR) * 0.6, 2, fill=1, stroke=0)
    y -= 30

    blocks = [
        ("📥 HOW TO DOWNLOAD YOUR FILES", [
            "Your recipe binder PDF and sticker pack ZIP are in your Etsy Purchases page.",
            "Download both to your device before opening — don't open directly from browser.",
            "Unzip the sticker pack to access all 9 PNG sheets.",
        ]),
        ("📱 HOW TO IMPORT INTO GOODNOTES / NOTABILITY", [
            "Open the recipe binder PDF directly in GoodNotes 6, Notability, or PDF Expert.",
            "For stickers: Elements → Stickers tab → + → select all 9 PNG sheet files.",
            "Tap any recipe card to start typing — write with Apple Pencil or the keyboard.",
        ]),
        ("💬 NEED HELP?", [
            f"Watch the setup tutorial → [link]",
            f"Email {SHOP_NAME} support any time — we're glad to help.",
        ]),
    ]
    for heading, lines in blocks:
        c.setFillColorRGB(*T)
        c.setFont(fn("bold"), 11)
        c.drawString(_ML, y, heading)
        y -= 16
        c.setFillColorRGB(*DK)
        c.setFont(fn("regular"), 9)
        for line in lines:
            c.drawString(_ML + 12, y, line)
            y -= 14
        y -= 10

    _smart_footer(c, T, A, BG, fn, PW, prev_lbl="", next_lbl="DASHBOARD")
    c.showPage()
    c.save()
    return buf.getvalue()


def _gen_dashboard_page(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    _page_bg(c, BG, PW, PH)
    _gradient_header(c, pcfg["title"].upper(), T, A, BG, fn, PW, PH, sub=pcfg["subtitle"])

    buttons = [
        "Recipe Index", "Recipe Cards", "Weekly Meal Planner", "Grocery List",
        "Pantry Inventory", "Freezer Inventory", "Kitchen Conversions",
        "Notes", "Sticker Library",
    ]
    cols, rows = 3, 3
    top = PH - 58 - 20
    gap = 10.0
    bw = (PW - _ML - _MR - gap * (cols - 1)) / cols
    bh = 62.0
    for i, label in enumerate(buttons):
        r, col = divmod(i, cols)
        x = _ML + col * (bw + gap)
        y = top - r * (bh + gap) - bh
        ink = _panel_ink(DK, T)
        c.setFillColorRGB(*_bl(T, 0.85))
        c.roundRect(x, y, bw, bh, 8, fill=1, stroke=0)
        c.setFillColorRGB(*T)
        c.setLineWidth(0.6)
        c.roundRect(x, y, bw, bh, 8, fill=0, stroke=1)
        c.setFillColorRGB(*ink)
        c.setFont(fn("bold"), 9)
        c.drawCentredString(x + bw / 2, y + bh / 2, label)

    _smart_footer(c, T, A, BG, fn, PW, prev_lbl="WELCOME", next_lbl="INDEX")
    c.showPage()
    c.save()
    return buf.getvalue()


def _gen_index_page(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    _page_bg(c, BG, PW, PH)
    _gradient_header(c, "RECIPE BINDER INDEX", T, A, BG, fn, PW, PH)

    y = PH - 58 - 26
    c.setFillColorRGB(*DK)
    c.setFont(fn("regular"), 9.5)
    for section in pcfg["sections"]:
        c.setFillColorRGB(*T)
        c.circle(_ML + 3, y + 3, 2.2, fill=1, stroke=0)
        c.setFillColorRGB(*DK)
        c.drawString(_ML + 14, y, section)
        y -= 17
        if y < 70:
            break

    _smart_footer(c, T, A, BG, fn, PW, prev_lbl="DASHBOARD", next_lbl="RECIPES")
    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# The genuinely new page type: fillable recipe cards
# ---------------------------------------------------------------------------

def _gen_recipe_card_pages(pcfg, categories=_CATEGORIES, per_category=_CARDS_PER_CATEGORY):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    chunks = []
    for cat in categories:
        for n in range(per_category):
            c, buf, PW, PH = _new_canvas()
            _page_bg(c, BG, PW, PH)
            _textured_bg(c, BG, PW, PH)
            _draw_binding(c, BG, PH)
            _gradient_header(c, f"{cat.upper()} RECIPE", T, A, BG, fn, PW, PH,
                              sub=f"Card {n + 1} of {per_category}")

            ML = _ML + 26
            CW = PW - ML - _MR
            top = PH - 58 - 16

            # Title + quick-facts row
            c.setFillColorRGB(*DK)
            c.setFont(fn("bold"), 8.5)
            c.drawString(ML, top, "Recipe Name:")
            c.setStrokeColorRGB(*_bl(DK, 0.5))
            c.setLineWidth(0.6)
            c.line(ML + 78, top - 1, ML + CW, top - 1)
            top -= 20

            facts = ["Prep Time: _______", "Cook Time: _______", "Servings: _______", "Rating: ☆ ☆ ☆ ☆ ☆"]
            fw = CW / len(facts)
            c.setFont(fn("regular"), 7.5)
            for i, f in enumerate(facts):
                c.drawString(ML + i * fw, top, f)
            top -= 22

            # Two-column body: ingredients (left) / instructions (right)
            col_gap = 14.0
            ing_w = CW * 0.36
            inst_w = CW - ing_w - col_gap
            body_bottom = 92.0
            body_h = top - body_bottom

            # Fixed, generously-spaced counts (not "fill all available space") --
            # a recipe card with 30+ cramped 15pt-spaced lines is unusable for
            # actual handwriting (CLAUDE.md's UX rule: min ~0.5in / ~24pt line
            # height for handwriting space). 12 ingredients and 10 steps covers
            # the large majority of real home recipes with real writing room.
            N_INGREDIENTS = 12
            N_STEPS = 10

            _shadow_box(c, ML, body_bottom, ing_w, body_h)
            c.setFillColorRGB(*_bl(T, 0.90))
            c.roundRect(ML, body_bottom, ing_w, body_h, 6, fill=1, stroke=0)
            c.setFillColorRGB(*T)
            c.setFont(fn("bold"), 8.5)
            c.drawString(ML + 10, top - 14, "INGREDIENTS")
            ing_row_h = (top - 30 - (body_bottom + 10)) / N_INGREDIENTS
            c.setFont(fn("regular"), 7.5)
            for row in range(N_INGREDIENTS):
                iy = (top - 30) - row * ing_row_h
                c.setStrokeColorRGB(*_bl(DK, 0.5))
                c.setLineWidth(0.6)
                c.roundRect(ML + 10, iy - 2, 8, 8, 1.6, fill=0, stroke=1)
                c.setStrokeColorRGB(*_bl(DK, 0.75))
                c.line(ML + 26, iy, ML + ing_w - 10, iy)

            ix = ML + ing_w + col_gap
            _shadow_box(c, ix, body_bottom, inst_w, body_h)
            c.setFillColorRGB(*_bl(T, 0.90))
            c.roundRect(ix, body_bottom, inst_w, body_h, 6, fill=1, stroke=0)
            c.setFillColorRGB(*T)
            c.setFont(fn("bold"), 8.5)
            c.drawString(ix + 10, top - 14, "INSTRUCTIONS")
            step_row_h = (top - 30 - (body_bottom + 10)) / N_STEPS
            for row in range(N_STEPS):
                sy = (top - 30) - row * step_row_h
                c.setFillColorRGB(*T)
                c.setFont(fn("bold"), 7.5)
                c.drawString(ix + 10, sy, f"{row + 1}.")
                c.setStrokeColorRGB(*_bl(DK, 0.75))
                c.setLineWidth(0.6)
                c.line(ix + 28, sy, ix + inst_w - 10, sy)

            # Notes strip at bottom
            c.setFillColorRGB(*DK)
            c.setFont(fn("italic"), 7)
            c.drawString(ML, body_bottom - 10, "Notes / substitutions: " + "_" * 70)

            _smart_footer(c, T, A, BG, fn, PW, prev_lbl=cat.upper(), next_lbl=cat.upper())
            c.showPage()
            c.save()
            chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


# ---------------------------------------------------------------------------
# Kitchen-specific reference/tracker pages
# ---------------------------------------------------------------------------

def _gen_checklist_grid_page(pcfg, title, subtitle, n_rows=24, two_col=True):
    """Shared shape for grocery-list / pantry-inventory / freezer-inventory
    pages -- a simple checkbox + item-name + qty grid, same visual language
    as the recipe cards' ingredient checklist."""
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    _page_bg(c, BG, PW, PH)
    _textured_bg(c, BG, PW, PH)
    _draw_binding(c, BG, PH)
    _gradient_header(c, title, T, A, BG, fn, PW, PH, sub=subtitle)

    ML = _ML + 26
    CW = PW - ML - _MR
    top = PH - 58 - 20
    bottom = 40.0

    cols = 2 if two_col else 1
    col_w = (CW - (14.0 if two_col else 0)) / cols
    rows_per_col = -(-n_rows // cols)  # ceil
    row_h = (top - bottom) / rows_per_col

    for i in range(n_rows):
        col = i // rows_per_col
        row = i % rows_per_col
        x = ML + col * (col_w + 14.0)
        y = top - (row + 1) * row_h
        c.setStrokeColorRGB(*_bl(DK, 0.5))
        c.setLineWidth(0.7)
        c.roundRect(x, y + row_h * 0.3, 8, 8, 1.6, fill=0, stroke=1)
        c.setStrokeColorRGB(*_bl(DK, 0.75))
        c.line(x + 16, y + row_h * 0.35, x + col_w - 34, y + row_h * 0.35)
        c.setFillColorRGB(*DK)
        c.setFont(fn("regular"), 6.5)
        c.drawString(x + col_w - 30, y + row_h * 0.35 + 1, "qty:")
        c.setStrokeColorRGB(*_bl(DK, 0.6))
        c.line(x + col_w - 12, y + row_h * 0.35, x + col_w, y + row_h * 0.35)

    _smart_footer(c, T, A, BG, fn, PW, prev_lbl="", next_lbl="")
    c.showPage()
    c.save()
    return buf.getvalue()


def _gen_grocery_list_pages(pcfg, count=4):
    chunks = [
        _gen_checklist_grid_page(pcfg, "GROCERY LIST", f"Shopping trip {i + 1}", n_rows=28)
        for i in range(count)
    ]
    return _merge_pdfs(*chunks)


def _gen_pantry_freezer_pages(pcfg):
    pantry = _gen_checklist_grid_page(pcfg, "PANTRY INVENTORY", "What's in stock — check before you shop", n_rows=30)
    freezer = _gen_checklist_grid_page(pcfg, "FREEZER INVENTORY", "Track what's frozen so nothing gets forgotten", n_rows=24)
    return _merge_pdfs(pantry, freezer)


# Real, standard kitchen conversions -- factual reference data, safe to hardcode
# (never a "customer might be lied to" surface -- these are established units).
_CONVERSIONS = [
    ("3 teaspoons", "1 tablespoon"),
    ("4 tablespoons", "1/4 cup"),
    ("5 tbsp + 1 tsp", "1/3 cup"),
    ("8 tablespoons", "1/2 cup"),
    ("16 tablespoons", "1 cup"),
    ("1 cup", "8 fluid ounces"),
    ("2 cups", "1 pint"),
    ("4 cups", "1 quart"),
    ("4 quarts", "1 gallon"),
    ("1 stick butter", "1/2 cup / 8 tbsp"),
    ("1 ounce", "28 grams"),
    ("1 pound", "16 ounces / 454 grams"),
]
_OVEN_TEMPS = [("275°F", "135°C"), ("300°F", "150°C"), ("325°F", "163°C"), ("350°F", "177°C"),
               ("375°F", "191°C"), ("400°F", "204°C"), ("425°F", "218°C"), ("450°F", "232°C")]


def _gen_kitchen_conversion_chart(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    _page_bg(c, BG, PW, PH)
    _gradient_header(c, "KITCHEN CONVERSION CHART", T, A, BG, fn, PW, PH, sub="Quick reference — keep this page handy")

    ML = _ML + 26
    CW = PW - ML - _MR
    top = PH - 58 - 24

    c.setFillColorRGB(*T)
    c.setFont(fn("bold"), 9)
    c.drawString(ML, top, "VOLUME & WEIGHT")
    top -= 16
    row_h = 15.0
    for a, b in _CONVERSIONS:
        c.setFillColorRGB(*DK)
        c.setFont(fn("regular"), 8)
        c.drawString(ML, top, a)
        c.setFillColorRGB(*T)
        c.drawString(ML + CW * 0.5, top, "=  " + b)
        top -= row_h

    top -= 14
    c.setFillColorRGB(*T)
    c.setFont(fn("bold"), 9)
    c.drawString(ML, top, "OVEN TEMPERATURES (°F ↔ °C)")
    top -= 16
    for i, (f, cel) in enumerate(_OVEN_TEMPS):
        row, col = divmod(i, 2)
        x = ML + col * (CW / 2.0)
        y = top - row * row_h
        c.setFillColorRGB(*DK)
        c.setFont(fn("regular"), 8)
        c.drawString(x, y, f"{f}  =  {cel}")

    _smart_footer(c, T, A, BG, fn, PW, prev_lbl="", next_lbl="")
    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Sticker library reference (real thumbnails, not a generic mockup grid)
# ---------------------------------------------------------------------------

def _sheet_preview_jpeg(sheet_png_path, bg_rgb, max_px=700, cache_suffix="_preview.jpg"):
    """Downsized, background-flattened JPEG for embedding a sticker sheet as
    an in-PDF reference image. The raw sheets are ~0.9-1.1MB transparent PNGs
    each -- embedding all 9 at full res pushed RB1001.pdf from 5MB to 19MB,
    dangerously close to Etsy's 20MB per-file hard limit, for what is only a
    visual reference (the real deliverable is the ZIP). Flattening onto the
    page background + JPEG compression + a 700px cap keeps this page-count
    increase cheap. Cached next to the source PNG so re-running the PDF build
    doesn't redo this work every time."""
    if not sheet_png_path.exists():
        return None
    cache_path = sheet_png_path.with_name(sheet_png_path.stem + cache_suffix)
    if cache_path.exists() and cache_path.stat().st_mtime >= sheet_png_path.stat().st_mtime:
        return str(cache_path)
    from PIL import Image
    im = Image.open(sheet_png_path).convert("RGBA")
    im.thumbnail((max_px, max_px), Image.LANCZOS)
    bg_255 = tuple(int(round(v * 255)) for v in bg_rgb)
    flat = Image.new("RGB", im.size, bg_255)
    flat.paste(im, (0, 0), im)
    flat.save(cache_path, "JPEG", quality=80, optimize=True)
    return str(cache_path)


def _gen_sticker_library_pages(pcfg):
    """Custom to RB1001 -- generate_planner.py's shared _gen_sticker_library()
    hardcodes a fixed 5-sheet generic grid (different sheet names/example
    labels than what RB1001 actually ships: 9 sheets including 4 recipe-
    specific bonus sheets, and different real per-sticker content). Reusing
    it here would put an inaccurate reference page in the PDF -- both under-
    representing what's really in the box (missing 4 real sheets) and
    misstating the import step count ("select all 5 PNG sheets" when there
    are 9). Places the REAL generated sheet thumbnail on each page instead of
    a text mockup, so this page can never drift out of sync with what the
    ZIP actually contains."""
    from tools.generate_recipe_binder_sticker_assets import SHEETS as STICKER_SHEETS, ART as STICKER_ART, PID as STICKER_PID
    from tools.process_sticker_sheets import STICKER_OUT

    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    n_sheets = len(STICKER_SHEETS)
    chunks = []
    for n in sorted(STICKER_SHEETS):
        name, contents = STICKER_SHEETS[n]
        c, buf, PW, PH = _new_canvas()
        _page_bg(c, BG, PW, PH)
        _gradient_header(c, "STICKER LIBRARY", T, A, BG, fn, PW, PH, sub=f"Sheet {n} of {n_sheets}: {name}")

        y = PH - 58 - 16
        tip_h = 34
        c.setFillColorRGB(*_bl(T, 0.88))
        c.roundRect(_ML, y - tip_h, PW - _ML - _MR, tip_h, 5, fill=1, stroke=0)
        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 7.5)
        c.drawString(_ML + 8, y - 12,
                     f"GoodNotes: Elements -> Stickers -> + -> select all {n_sheets} PNG sheets -> stickers appear in library")
        c.setFont(fn("regular"), 7.5)
        c.drawString(_ML + 8, y - 24, "Notability: use Photo Stickers  |  Acrobat/Xodo: tap STICKERS button in binder footer")
        y -= tip_h + 10

        # Prefer the REAL processed/transparent sheet (what buyers actually get in
        # the ZIP) over the raw solid-gray-background source -- otherwise this
        # reference page shows stickers on a gray card, which nobody receives.
        processed_img = STICKER_OUT / STICKER_PID / "png_sheets" / f"{STICKER_PID}_sheet_{n:02d}.png"
        raw_img = STICKER_ART / f"{STICKER_PID}_sticker_sheet_{n}.png"
        sheet_img = processed_img if processed_img.exists() else raw_img
        preview_img = _sheet_preview_jpeg(sheet_img, BG)
        if preview_img is not None:
            from reportlab.lib.utils import ImageReader
            img = ImageReader(preview_img)
            box_w = PW - _ML - _MR
            box_h = y - 44
            c.drawImage(img, _ML, 44, width=box_w, height=box_h, preserveAspectRatio=True, anchor="c")
        else:
            c.setFillColorRGB(*DK)
            c.setFont(fn("italic"), 9)
            c.drawCentredString(PW / 2, PH / 2, "[sheet preview not yet generated]")

        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="STICKERS", next_lbl="STICKERS")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def build_recipe_binder():
    pcfg = RB1001
    cover_cfg = {
        "name": pcfg["title"],
        "subtitle": pcfg["subtitle"],
        "year": pcfg.get("year"),
        "bg_rgb": pcfg["bg"],
        "theme_rgb": pcfg["theme"],
        "dark_rgb": pcfg["dark"],
    }
    cover_img_path = OUT_DIR / "new_product_covers" / "RB1001_recipe_binder_mocha_latte.png"
    cover_pdf_bytes = _make_cover_page(cover_cfg, str(cover_img_path) if cover_img_path.exists() else None)

    chunks = [
        cover_pdf_bytes,
        _gen_welcome_page(pcfg),
        _gen_dashboard_page(pcfg),
        _gen_index_page(pcfg),
        _gen_recipe_card_pages(pcfg),
        _gen_meal_plan_page(pcfg),
        _gen_grocery_list_pages(pcfg),
        _gen_pantry_freezer_pages(pcfg),
        _gen_kitchen_conversion_chart(pcfg),
        _gen_notes_pages(pcfg, count=4),
        _gen_sticker_library_pages(pcfg),
    ]
    full = _merge_pdfs(*chunks)
    out_path = OUT_DIR / "RB1001.pdf"
    out_path.write_bytes(full)
    return out_path


def main():
    path = build_recipe_binder()
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(path))
        print(f"RB1001: {len(reader.pages)} pages, {path.stat().st_size / 1024:.0f} KB -> {path}")
    except Exception as e:
        print(f"RB1001 saved to {path} (stats unavailable: {e})")


if __name__ == "__main__":
    main()
