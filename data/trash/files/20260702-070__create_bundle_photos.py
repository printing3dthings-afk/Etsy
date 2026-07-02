#!/usr/bin/env python3
"""
Generate listing photos for the All 4 Planners Bundle (listing 4512188970).
All planner content uses real pages rendered directly from the actual PDF files.
NO AI-generated planner imagery — what you see is exactly what the customer receives.
"""
import os, sys, shutil
import fitz  # pymupdf
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ART_DIR = '/home/user/Etsy/data/digital_products/product_files'
OUT_DIR = os.path.join(ART_DIR, 'bundle_listing_images')
os.makedirs(OUT_DIR, exist_ok=True)

CANVAS = 2400
PAD = 90
GAP = 60
CELL = (CANVAS - 2 * PAD - GAP) // 2   # ~1080 px per cell

PIDS = ['DP1026', 'DP1027', 'DP1028', 'DP1029']
THEME_COLORS = {
    'DP1026': (134, 102, 170),   # lavender
    'DP1027': (222, 151, 198),   # cotton candy pink
    'DP1028': ( 27,  37, 104),   # midnight blue
    'DP1029': (253, 108,  73),   # coral peach
}
NAMES = {
    'DP1026': 'Life Planner',
    'DP1027': 'Student Planner',
    'DP1028': 'Budget Planner',
    'DP1029': 'Fitness Planner',
}
PRICES = {
    'DP1026': '$14.99',
    'DP1027': '$9.99',
    'DP1028': '$12.99',
    'DP1029': '$12.99',
}
PAGES = {
    'DP1026': {'monthly': 11, 'weekly': 47},
    'DP1027': {'monthly': 11, 'weekly': 35},
    'DP1028': {'monthly': 11, 'weekly': 47},
    'DP1029': {'monthly': 11, 'weekly': 35},
}
# Page 4 is the illustrated cover for all planners
COVER_PAGE = 4
STICKER_SHEET = {pid: os.path.join(ART_DIR, f'{pid}_sticker_sheet_4.jpg') for pid in PIDS}
APP_COMPAT_SRC = os.path.join(ART_DIR, 'DP1028_listing_images', '07_app_compatibility.jpg')


# ── PDF rendering ─────────────────────────────────────────────────────────────

def render_pdf_page(pid, page_num, target_width=1800):
    """Render a page from the real planner PDF. page_num is 1-indexed."""
    pdf_path = os.path.join(ART_DIR, f'{pid}.pdf')
    pdf = fitz.open(pdf_path)
    page = pdf[page_num - 1]
    # Scale so the rendered width matches target_width
    scale = target_width / page.rect.width
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    # Convert to PIL
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    pdf.close()
    return img


# ── Fonts ──────────────────────────────────────────────────────────────────────

def font_bold(size):
    for path in [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def font_reg(size):
    for path in [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ── iPad mockup compositor ─────────────────────────────────────────────────────

def make_ipad_mockup(planner_img, ipad_w=680, ipad_h=900):
    """
    Composite a planner page image into a simple silver iPad frame.
    Returns an RGBA PIL image.
    """
    RADIUS = 48
    BEZEL = 22
    SILVER = (190, 190, 194)
    DARK_EDGE = (140, 140, 145)

    ipad = Image.new('RGBA', (ipad_w, ipad_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ipad)

    # Outer frame (dark edge for depth)
    draw.rounded_rectangle([0, 0, ipad_w - 1, ipad_h - 1],
                           radius=RADIUS, fill=DARK_EDGE)
    # Main silver body
    draw.rounded_rectangle([2, 2, ipad_w - 3, ipad_h - 3],
                           radius=RADIUS - 1, fill=SILVER)

    # Screen area (black background first)
    sx, sy = BEZEL, BEZEL
    sw, sh = ipad_w - 2 * BEZEL, ipad_h - 2 * BEZEL
    screen_radius = RADIUS - BEZEL + 4
    draw.rounded_rectangle([sx, sy, sx + sw - 1, sy + sh - 1],
                           radius=screen_radius, fill=(20, 20, 22))

    # Fit planner page into screen keeping aspect ratio
    page_ratio = planner_img.width / planner_img.height
    screen_ratio = sw / sh
    if page_ratio < screen_ratio:
        # Page is taller — fit by height
        fit_h = sh
        fit_w = int(sh * page_ratio)
    else:
        fit_w = sw
        fit_h = int(sw / page_ratio)

    page_resized = planner_img.resize((fit_w, fit_h), Image.LANCZOS)
    px = sx + (sw - fit_w) // 2
    py = sy + (sh - fit_h) // 2

    # Create mask for rounded screen
    screen_mask = Image.new('L', (sw, sh), 0)
    ImageDraw.Draw(screen_mask).rounded_rectangle(
        [0, 0, sw - 1, sh - 1], radius=screen_radius, fill=255)

    page_canvas = Image.new('RGB', (sw, sh), (20, 20, 22))
    page_canvas.paste(page_resized, (px - sx, py - sy))
    ipad.paste(page_canvas, (sx, sy), screen_mask)

    # Home/power button nub on right edge
    btn_w, btn_h = 4, 60
    bx = ipad_w - 3
    by = ipad_h // 2 - btn_h // 2
    draw.rectangle([bx, by, bx + btn_w, by + btn_h], fill=(160, 160, 165))

    # Volume buttons on left edge
    for offset in [ipad_h // 3 - 30, ipad_h // 3 + 30]:
        draw.rectangle([-1, offset, 3, offset + 40], fill=(160, 160, 165))

    return ipad


def drop_shadow(canvas_rgba, x, y, w, h, blur=24, opacity=55):
    layer = Image.new('RGBA', canvas_rgba.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rectangle([x + 14, y + 14, x + w + 14, y + h + 14],
                                    fill=(0, 0, 0, opacity))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=blur))
    return Image.alpha_composite(canvas_rgba, layer)


def grid_positions():
    positions = []
    for row in range(2):
        for col in range(2):
            x = PAD + col * (CELL + GAP)
            y = PAD + row * (CELL + GAP)
            positions.append((x, y))
    return positions   # TL, TR, BL, BR


def paste_fit(canvas, src_img, x, y, w, h, round_corners=0):
    """Paste src_img (PIL Image or path) into canvas at (x,y) fitted to w×h."""
    if isinstance(src_img, str):
        src_img = Image.open(src_img).convert('RGB')
    img = src_img.convert('RGB')
    # Crop to fill the cell (center crop)
    src_ratio = img.width / img.height
    dst_ratio = w / h
    if src_ratio > dst_ratio:
        # Wider than needed — crop sides
        new_w = int(img.height * dst_ratio)
        offset = (img.width - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, img.height))
    else:
        # Taller than needed — crop top/bottom
        new_h = int(img.width / dst_ratio)
        offset = (img.height - new_h) // 2
        img = img.crop((0, offset, img.width, offset + new_h))
    img = img.resize((w, h), Image.LANCZOS)
    if round_corners:
        mask = Image.new('L', (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1],
                                               radius=round_corners, fill=255)
        canvas.paste(img, (x, y), mask)
    else:
        canvas.paste(img, (x, y))


# ── Photo 01: Hero — 4 iPads with real planner pages ──────────────────────────

def make_hero(out_path):
    # Warm cream background
    bg = Image.new('RGBA', (CANVAS, CANVAS), (252, 249, 244, 255))
    # Subtle warm gradient
    for y in range(CANVAS):
        shade = max(235, 252 - int(y * 17 / CANVAS))
        ImageDraw.Draw(bg).line([(0, y), (CANVAS, y)],
                                fill=(shade, shade - 3, shade - 9, 255))

    ipad_w, ipad_h = 700, 930
    # Positions for 2×2 arrangement with slight offsets for natural feel
    positions = [
        (PAD + 20,              PAD + 30),              # TL — DP1026
        (PAD + CELL + GAP - 20, PAD + 10),              # TR — DP1027
        (PAD + 10,              PAD + CELL + GAP + 20), # BL — DP1028
        (PAD + CELL + GAP + 20, PAD + CELL + GAP + 10), # BR — DP1029
    ]
    rotations = [-3, 3, 3, -3]

    for i, pid in enumerate(PIDS):
        # Render the monthly calendar page from the real PDF
        page_img = render_pdf_page(pid, PAGES[pid]['monthly'])
        ipad = make_ipad_mockup(page_img, ipad_w, ipad_h)
        if rotations[i]:
            ipad = ipad.rotate(rotations[i], expand=True, resample=Image.BICUBIC)

        x, y = positions[i]
        # Shadow
        bg = drop_shadow(bg, x, y, ipad.width, ipad.height, blur=28, opacity=50)
        # Paste iPad
        bg.paste(ipad, (x, y), ipad)

        # Color badge below each iPad
        draw = ImageDraw.Draw(bg)
        color = THEME_COLORS[pid]
        badge_w, badge_h = 280, 52
        bx = x + ipad.width // 2 - badge_w // 2
        by = y + ipad.height + 12
        draw.rounded_rectangle([bx, by, bx + badge_w, by + badge_h],
                               radius=26, fill=color)
        draw.text((bx + badge_w // 2, by + badge_h // 2), NAMES[pid],
                  font=font_bold(28), fill=(255, 255, 255), anchor='mm')

    # Title at top
    draw = ImageDraw.Draw(bg)
    draw.text((CANVAS // 2, 38), "ALL 4 PLANNERS BUNDLE",
              font=font_bold(80), fill=(60, 40, 80, 255), anchor='mt')
    draw.text((CANVAS // 2, 128), "Instant Download  ·  GoodNotes & Notability",
              font=font_reg(48), fill=(130, 100, 160, 255), anchor='mt')

    bg.convert('RGB').save(out_path, 'JPEG', quality=93)
    print("  01_hero.jpg — 4 real planner pages in iPad frames")


# ── Photo 02: Four themes — real cover pages in 2×2 grid ──────────────────────

def make_four_themes(out_path):
    bg = Image.new('RGB', (CANVAS, CANVAS), (250, 248, 245))
    draw = ImageDraw.Draw(bg)

    # Title bar
    draw.rectangle([0, 0, CANVAS, 140], fill=(60, 40, 80))
    draw.text((CANVAS // 2, 70), "MEET YOUR 4 PLANNERS",
              font=font_bold(72), fill=(255, 255, 255), anchor='mm')

    pos = grid_positions()
    cell_h = CELL - 60  # reduce cell height a bit to leave room for labels

    for i, pid in enumerate(PIDS):
        x, y_base = pos[i]
        y = y_base + 160  # push grid down below title

        color = THEME_COLORS[pid]
        # Color border
        draw.rectangle([x - 8, y - 8, x + CELL + 8, y + cell_h + 8], fill=color)
        # Render actual cover page
        cover = render_pdf_page(pid, COVER_PAGE)
        paste_fit(bg, cover, x, y, CELL, cell_h, round_corners=10)
        # Name ribbon
        ribbon_h = 64
        draw.rectangle([x, y + cell_h - ribbon_h, x + CELL, y + cell_h],
                       fill=color)
        draw.text((x + CELL // 2, y + cell_h - ribbon_h // 2), NAMES[pid],
                  font=font_bold(36), fill=(255, 255, 255), anchor='mm')

    bg.save(out_path, 'JPEG', quality=93)
    print("  02_four_themes.jpg — real cover pages")


# ── Photo 03: Monthly spreads — real pages 2×2 ───────────────────────────────

def make_grid_real(page_key, title_top, title_bottom, out_path):
    bg = Image.new('RGB', (CANVAS, CANVAS), (250, 248, 245))
    draw = ImageDraw.Draw(bg)

    draw.text((CANVAS // 2, 36), title_top,
              font=font_bold(68), fill=(60, 40, 80), anchor='mt')

    pos = grid_positions()
    for i, pid in enumerate(PIDS):
        x, y = pos[i]
        y += 120  # push below title

        color = THEME_COLORS[pid]
        draw.rectangle([x - 6, y - 6, x + CELL + 6, y + CELL + 6], fill=color)
        # Render real PDF page
        page_img = render_pdf_page(pid, PAGES[pid][page_key])
        paste_fit(bg, page_img, x, y, CELL, CELL, round_corners=10)
        # Small color tab with planner name
        draw.rounded_rectangle([x, y + CELL - 52, x + CELL, y + CELL],
                               radius=10, fill=color)
        draw.text((x + CELL // 2, y + CELL - 26), NAMES[pid],
                  font=font_bold(28), fill=(255, 255, 255), anchor='mm')

    draw.text((CANVAS // 2, CANVAS - 36), title_bottom,
              font=font_reg(46), fill=(120, 100, 140), anchor='mb')
    bg.save(out_path, 'JPEG', quality=93)
    print(f"  {os.path.basename(out_path)} — real PDF {page_key} pages")


# ── Photo 05: Sticker showcase — real sticker sheets ──────────────────────────

def make_sticker_showcase(out_path):
    bg = Image.new('RGB', (CANVAS, CANVAS), (255, 252, 247))
    for y in range(CANVAS):
        shade = int(255 - y * 8 / CANVAS)
        ImageDraw.Draw(bg).line([(0, y), (CANVAS, y)],
                                fill=(shade, shade - 4, shade - 10))

    bg = bg.convert('RGBA')

    # Hero sheet: DP1027 sheet_4 (cozy lifestyle)
    hero_size = 1680
    hero_x = (CANVAS - hero_size) // 2
    hero_y = 280
    bg = drop_shadow(bg, hero_x - 20, hero_y - 20,
                     hero_size + 40, hero_size + 40, blur=30, opacity=60)
    card = Image.new('RGBA', (hero_size + 40, hero_size + 40), (255, 255, 255, 255))
    mask = Image.new('L', (hero_size + 40, hero_size + 40), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, hero_size + 39, hero_size + 39],
                                           radius=28, fill=255)
    card.putalpha(mask)
    bg.paste(card, (hero_x - 20, hero_y - 20), card)
    hero = Image.open(STICKER_SHEET['DP1027']).convert('RGBA').resize(
        (hero_size, hero_size), Image.LANCZOS)
    bg.paste(hero, (hero_x, hero_y), hero)

    # Three small sheets fanned
    small_size = 480
    small_sheets = [
        (os.path.join(ART_DIR, 'DP1026_sticker_sheet_4.jpg'), -18, 60, 140),
        (os.path.join(ART_DIR, 'DP1028_sticker_sheet_4.jpg'),  12,
         CANVAS - small_size - 140, 140),
        (os.path.join(ART_DIR, 'DP1029_sticker_sheet_3.jpg'),  -8,
         CANVAS // 2 - small_size // 2, CANVAS - small_size - 140),
    ]
    for sheet_path, rot, sx, sy in small_sheets:
        sheet = Image.open(sheet_path).convert('RGBA').resize(
            (small_size, small_size), Image.LANCZOS)
        card_s = Image.new('RGBA', (small_size + 16, small_size + 16), (255, 255, 255, 245))
        mask_s = Image.new('L', (small_size + 16, small_size + 16), 0)
        ImageDraw.Draw(mask_s).rounded_rectangle(
            [0, 0, small_size + 15, small_size + 15], radius=16, fill=255)
        card_s.putalpha(mask_s)
        if rot:
            card_r = card_s.rotate(rot, expand=True, resample=Image.BICUBIC)
            sheet_r = sheet.rotate(rot, expand=True, resample=Image.BICUBIC)
            bg.paste(card_r, (sx, sy), card_r)
            bg.paste(sheet_r, (sx + 8, sy + 8), sheet_r)
        else:
            bg.paste(card_s, (sx, sy), card_s)
            bg.paste(sheet, (sx + 8, sy + 8), sheet)

    bg = bg.convert('RGB')
    draw = ImageDraw.Draw(bg)
    draw.text((CANVAS // 2, 100), "800+ KAWAII STICKERS INCLUDED",
              font=font_bold(86), fill=(80, 50, 110), anchor='mm')
    draw.text((CANVAS // 2, 190), "11 illustrated sheets per planner  ·  4 planners",
              font=font_reg(50), fill=(150, 120, 180), anchor='mm')

    badges = [
        ("Cozy Lifestyle",      THEME_COLORS['DP1026']),
        ("Seasonal & Holiday",  THEME_COLORS['DP1027']),
        ("Functional Planning", THEME_COLORS['DP1028']),
        ("GoodNotes Ready",     THEME_COLORS['DP1029']),
    ]
    badge_w, badge_h = 480, 72
    total_w = len(badges) * badge_w + (len(badges) - 1) * 24
    bx = (CANVAS - total_w) // 2
    by = CANVAS - 110
    for label, color in badges:
        draw.rounded_rectangle([bx, by, bx + badge_w, by + badge_h],
                               radius=36, fill=color)
        draw.text((bx + badge_w // 2, by + badge_h // 2), label,
                  font=font_bold(34), fill=(255, 255, 255), anchor='mm')
        bx += badge_w + 24

    bg.save(out_path, 'JPEG', quality=93)
    print("  05_sticker_showcase.jpg — real sticker sheets")


# ── Photo 06: Savings graphic ──────────────────────────────────────────────────

def make_savings(out_path):
    bg = Image.new('RGB', (CANVAS, CANVAS), (250, 248, 245))
    draw = ImageDraw.Draw(bg)
    draw.rectangle([0, 0, CANVAS, 360], fill=(134, 102, 170))
    draw.text((CANVAS // 2, 120), "BUNDLE & SAVE",
              font=font_bold(110), fill=(255, 255, 255), anchor='mm')
    draw.text((CANVAS // 2, 270), "All 4 Planners + 800+ Stickers",
              font=font_reg(60), fill=(230, 220, 245), anchor='mm')

    items = [
        ('Life Planner (104 pages)',    '$14.99', THEME_COLORS['DP1026']),
        ('Student Planner (90 pages)',  '$9.99',  THEME_COLORS['DP1027']),
        ('Budget Planner (102 pages)',  '$12.99', THEME_COLORS['DP1028']),
        ('Fitness Planner (91 pages)',  '$12.99', THEME_COLORS['DP1029']),
    ]
    y = 430
    for name, price, color in items:
        draw.rectangle([PAD, y, CANVAS - PAD, y + 184], fill=(245, 242, 255),
                       outline=color, width=4)
        draw.ellipse([PAD + 20, y + 62, PAD + 84, y + 122], fill=color)
        draw.text((PAD + 110, y + 92), name, font=font_reg(68),
                  fill=(60, 40, 80), anchor='lm')
        draw.text((CANVAS - PAD - 20, y + 92), price, font=font_bold(68),
                  fill=color, anchor='rm')
        y += 200

    draw.line([PAD, y + 10, CANVAS - PAD, y + 10], fill=(180, 160, 200), width=4)
    y += 30
    draw.text((PAD + 110, y + 60), "If bought separately:", font=font_reg(68),
              fill=(150, 130, 170), anchor='lm')
    draw.text((CANVAS - PAD - 20, y + 60), "$50.96", font=font_bold(68),
              fill=(180, 160, 200), anchor='rm')
    bbox = draw.textbbox((CANVAS - PAD - 20, y + 60), "$50.96",
                         font=font_bold(68), anchor='rm')
    mid = (bbox[1] + bbox[3]) // 2
    draw.line([bbox[0] - 4, mid, bbox[2] + 4, mid], fill=(200, 100, 100), width=6)
    y += 140

    draw.rectangle([PAD, y, CANVAS - PAD, y + 200], fill=(134, 102, 170))
    draw.text((CANVAS // 2, y + 60), "BUNDLE PRICE",
              font=font_bold(56), fill=(220, 210, 240), anchor='mm')
    draw.text((CANVAS // 2, y + 150), "$39.99  —  Save $10.97!",
              font=font_bold(88), fill=(255, 255, 255), anchor='mm')

    bg.save(out_path, 'JPEG', quality=93)
    print("  06_savings.jpg")


# ── Photo 07: App compatibility ────────────────────────────────────────────────

def copy_app_compat(out_path):
    if os.path.exists(APP_COMPAT_SRC):
        shutil.copy2(APP_COMPAT_SRC, out_path)
        print("  07_app_compatibility.jpg copied")
    else:
        print(f"  WARNING: source not found: {APP_COMPAT_SRC}")


# ── Photo 08: What's included card ────────────────────────────────────────────

def make_whats_included(out_path):
    bg = Image.new('RGB', (CANVAS, CANVAS), (250, 248, 245))
    draw = ImageDraw.Draw(bg)
    draw.rectangle([0, 0, CANVAS, 300], fill=(134, 102, 170))
    draw.text((CANVAS // 2, 150), "WHAT'S INCLUDED",
              font=font_bold(100), fill=(255, 255, 255), anchor='mm')
    lines = [
        ("✅  Life Planner 2026 + Undated Version",   "(104 pages · Lavender Dreams)"),
        ("✅  Student Planner 2026 + Undated Version", "(90 pages · Cotton Candy)"),
        ("✅  Budget Planner 2026 + Undated Version",  "(102 pages · Midnight Blue)"),
        ("✅  Fitness Planner 2026 + Undated Version", "(91 pages · Coral Peach)"),
        ("✅  4 Kawaii Sticker Packs",                 "(800+ stickers · 44 illustrated sheets)"),
        ("✅  8 PDF Files Total",                      "(4 dated 2026 + 4 undated versions)"),
        ("✅  Instant Digital Download",               "No physical item shipped"),
    ]
    y = 360
    for main, sub in lines:
        draw.text((PAD + 20, y), main, font=font_bold(58), fill=(60, 40, 80))
        y += 78
        draw.text((PAD + 60, y), sub, font=font_reg(48), fill=(140, 120, 160))
        y += 86

    draw.rectangle([0, CANVAS - 200, CANVAS, CANVAS], fill=(60, 40, 80))
    draw.text((CANVAS // 2, CANVAS - 100),
              "387 pages  ·  800+ stickers  ·  $39.99",
              font=font_bold(72), fill=(220, 200, 255), anchor='mm')

    bg.save(out_path, 'JPEG', quality=93)
    print("  08_whats_included.jpg")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Generating bundle listing photos using real PDF content...\n")

    print("1/8 — Hero (4 iPads with real planner pages)...")
    make_hero(os.path.join(OUT_DIR, '01_hero.jpg'))

    print("2/8 — Four themes (real cover pages)...")
    make_four_themes(os.path.join(OUT_DIR, '02_four_themes.jpg'))

    print("3/8 — Monthly spreads (real PDF pages)...")
    make_grid_real('monthly', "SEE INSIDE — MONTHLY VIEW",
                   "12 monthly calendars per planner × 4 planners",
                   os.path.join(OUT_DIR, '03_monthly_spreads.jpg'))

    print("4/8 — Weekly spreads (real PDF pages)...")
    make_grid_real('weekly', "SEE INSIDE — WEEKLY VIEW",
                   "52 weekly spreads per planner × 4 planners",
                   os.path.join(OUT_DIR, '04_weekly_spreads.jpg'))

    print("5/8 — Sticker showcase (real sticker sheets)...")
    make_sticker_showcase(os.path.join(OUT_DIR, '05_sticker_showcase.jpg'))

    print("6/8 — Savings graphic...")
    make_savings(os.path.join(OUT_DIR, '06_savings.jpg'))

    print("7/8 — App compatibility...")
    copy_app_compat(os.path.join(OUT_DIR, '07_app_compatibility.jpg'))

    print("8/8 — What's included card...")
    make_whats_included(os.path.join(OUT_DIR, '08_whats_included.jpg'))

    print("\nDone! Photos saved to:", OUT_DIR)
    for f in sorted(os.listdir(OUT_DIR)):
        size = os.path.getsize(os.path.join(OUT_DIR, f)) // 1024
        print(f"  {f}  ({size}KB)")


if __name__ == '__main__':
    main()
