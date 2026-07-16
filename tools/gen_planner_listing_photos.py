#!/usr/bin/env python3
"""
Generate all 10 listing photos for each of the 4 digital planners
using real pages rendered directly from the PDF files.
Photos are then uploaded to the respective Etsy listings.

Usage:
  python tools/gen_planner_listing_photos.py              # all 4
  python tools/gen_planner_listing_photos.py --pid DP1026 # one planner
"""
import os, sys, shutil, argparse, time, json, urllib.request
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from tools.etsy_api import EtsyAPIClient, EtsyAPIError

ART_DIR = '/home/user/Etsy/data/digital_products/product_files'
DP_BASE = '/home/user/Etsy/data/digital_products'  # for the stickers/<pid>/png_sheets fallback
APP_COMPAT_SRC = os.path.join(ART_DIR, '07_app_compatibility.jpg')
CANVAS = 2400

# Pages (1-indexed) for each photo type per planner
PLANNER_PAGES = {
    'DP1030': {
        'cover':    1,
        'monthly':  6,
        'weekly':   30,
        'tracker':  119,  # habit tracker
        'specialty': 113, # pomodoro focus tracker
        'name': 'ADHD Digital Planner 2026',
        'short': 'ADHD Planner',
        'pages': 130,
        'theme': 'Matcha Serenity',
        'color': (126, 200, 164),
        'accent': (184, 204, 142),
        'bg': (247, 249, 243),
        'tracker_label': 'Habit Tracker',
        'specialty_label': 'Pomodoro Focus Tracker',
        'emoji': '🌿',
        'sticker_sheets': [1, 3, 6, 9],
        'sheet_count': 9,
        'sticker_count': 219,  # measured count from the 2026-07-16 rebuild (tools/qc_sweep.py)
    },
    'DP1031': {
        'cover':    1,
        'monthly':  5,
        'weekly':   41,
        'tracker':  130,  # habit tracker
        'specialty': 128, # budget tracker
        'name': 'Undated Life Planner',
        'short': 'Life Planner',
        'pages': 141,
        'theme': 'Sage Garden',
        'color': (139, 168, 136),
        'accent': (200, 221, 181),
        'bg': (246, 248, 242),
        'tracker_label': 'Habit Tracker',
        'specialty_label': 'Budget Tracker',
        'emoji': '🌿',
        'sticker_sheets': [1, 3, 6, 9],
        'sheet_count': 9,
        'sticker_count': 247,  # measured 2026-07-16 rebuild
        'edition_label': 'Undated — Works Any Year, Forever',  # undated-only, no 2026-dated version
    },
    'DP1032': {
        'cover':    1,
        'monthly':  6,
        'weekly':   42,
        'tracker':  129,  # habit tracker
        'specialty': 125, # brain dump
        'name': 'Dark Mode Planner Bundle 2026',
        'short': 'Dark Mode Planner',
        'pages': 140,
        'theme': 'Midnight Kawaii',
        'color': (128, 64, 156),
        'accent': (0, 229, 255),
        'bg': (26, 26, 46),
        'tracker_label': 'Habit Tracker',
        'specialty_label': 'Brain Dump',
        'emoji': '🌙',
        'sticker_sheets': [1, 3, 6, 9],
        'sheet_count': 9,
        'sticker_count': 183,
    },
    'DP1033': {
        'cover':    1,
        'monthly':  6,
        'weekly':   42,   # Lesson Plan Week 1
        'tracker':  96,   # habit tracker
        'specialty': 86,  # class roster
        'name': 'Teacher Planner 2026-2027',
        'short': 'Teacher Planner',
        'pages': 107,
        'theme': 'Sunflower Studio',
        'color': (244, 196, 48),
        'accent': (74, 124, 89),
        'bg': (255, 253, 240),
        'tracker_label': 'Habit Tracker',
        'specialty_label': 'Class Roster',
        'emoji': '🌼',
        'sticker_sheets': [1, 3, 6, 9],
        'sheet_count': 9,
        'sticker_count': 177,
    },
    'DP1026': {
        'cover':    4,
        'monthly':  11,
        'weekly':   47,
        'tracker':  99,   # habit tracker
        'specialty': 101, # budget tracker
        'listing_id': 4509179201,
        'name': 'Ultimate Digital Life Planner 2026',
        'short': 'Life Planner',
        'pages': 104,
        'theme': 'Lavender Dreams',
        'color': (134, 102, 170),
        'accent': (196, 168, 212),
        'bg': (250, 247, 255),
        'tracker_label': 'Habit Tracker',
        'specialty_label': 'Budget Tracker',
        'emoji': '🌸',
        'sticker_sheets': [1, 3, 6, 9],   # sheets to show in showcase
    },
    'DP1027': {
        'cover':    4,
        'monthly':  11,
        'weekly':   35,
        'tracker':  87,   # habit tracker
        'specialty': 98,  # class schedule
        'listing_id': 4509184958,
        'name': 'Kawaii Student Planner 2026',
        'short': 'Student Planner',
        'pages': 90,
        'theme': 'Cotton Candy',
        'color': (222, 151, 198),
        'accent': (151, 198, 222),
        'bg': (255, 247, 253),
        'tracker_label': 'Habit Tracker',
        'specialty_label': 'Class Schedule',
        'emoji': '🩷',
        'sticker_sheets': [1, 3, 6, 8],
    },
    'DP1028': {
        'cover':    4,
        'monthly':  11,
        'weekly':   47,
        'tracker':  99,   # goals page
        'specialty': 100, # budget tracker
        'listing_id': 4509184962,
        'name': 'Digital Budget & Finance Planner 2026',
        'short': 'Budget Planner',
        'pages': 102,
        'theme': 'Midnight Blue',
        'color': (27, 37, 104),
        'accent': (123, 167, 194),
        'bg': (240, 245, 255),
        'tracker_label': 'Goals & Vision',
        'specialty_label': 'Budget Tracker',
        'emoji': '💙',
        'sticker_sheets': [1, 3, 6, 7],
    },
    'DP1029': {
        'cover':    4,
        'monthly':  11,
        'weekly':   35,
        'tracker':  87,   # habit tracker
        'specialty': 89,  # meal planner
        'listing_id': 4509184968,
        'name': 'Fitness & Wellness Planner 2026',
        'short': 'Fitness Planner',
        'pages': 91,
        'theme': 'Coral Peach',
        'color': (253, 108, 73),
        'accent': (245, 184, 120),
        'bg': (255, 248, 244),
        'tracker_label': 'Habit Tracker',
        'specialty_label': 'Meal Planner',
        'emoji': '🍑',
        'sticker_sheets': [1, 3, 6, 7],
    },
}


# ── Fonts ──────────────────────────────────────────────────────────────────────

def fb(size):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
              '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf']:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def fr(size):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
              '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf']:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()


# ── PDF rendering ──────────────────────────────────────────────────────────────

def render_page(pid, page_num, target_w=1800):
    pdf = fitz.open(os.path.join(ART_DIR, f'{pid}.pdf'))
    page = pdf[page_num - 1]
    scale = target_w / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    pdf.close()
    return img


# ── iPad mockup ────────────────────────────────────────────────────────────────

def make_ipad(page_img, ipad_w=760, ipad_h=1010):
    R, BZ = 52, 24
    SILVER, EDGE = (188, 188, 193), (138, 138, 143)
    ipad = Image.new('RGBA', (ipad_w, ipad_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ipad)
    d.rounded_rectangle([0, 0, ipad_w-1, ipad_h-1], radius=R, fill=EDGE)
    d.rounded_rectangle([2, 2, ipad_w-3, ipad_h-3], radius=R-1, fill=SILVER)
    sx, sy = BZ, BZ
    sw, sh = ipad_w - 2*BZ, ipad_h - 2*BZ
    sr = R - BZ + 6
    d.rounded_rectangle([sx, sy, sx+sw-1, sy+sh-1], radius=sr, fill=(18, 18, 20))
    # Fit page into screen
    pr = page_img.width / page_img.height
    cr = sw / sh
    if pr < cr:
        fh, fw = sh, int(sh * pr)
    else:
        fw, fh = sw, int(sw / pr)
    pg = page_img.resize((fw, fh), Image.LANCZOS)
    px, py = sx + (sw-fw)//2, sy + (sh-fh)//2
    mask = Image.new('L', (sw, sh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw-1, sh-1], radius=sr, fill=255)
    canvas = Image.new('RGB', (sw, sh), (18, 18, 20))
    canvas.paste(pg, (px-sx, py-sy))
    ipad.paste(canvas, (sx, sy), mask)
    # Side buttons
    d.rectangle([ipad_w-3, ipad_h//2-30, ipad_w, ipad_h//2+30], fill=(158, 158, 163))
    for off in [-40, 40]:
        d.rectangle([-1, ipad_h//3+off-20, 3, ipad_h//3+off+20], fill=(158, 158, 163))
    return ipad


def drop_shadow(canvas, x, y, w, h, blur=24, opacity=50):
    layer = Image.new('RGBA', canvas.size, (0,0,0,0))
    ImageDraw.Draw(layer).rectangle([x+16, y+16, x+w+16, y+h+16], fill=(0,0,0,opacity))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=blur))
    return Image.alpha_composite(canvas, layer)


def paste_centered(canvas, img, cx, cy):
    """Paste RGBA img centered at (cx, cy) on RGBA canvas."""
    x = cx - img.width // 2
    y = cy - img.height // 2
    canvas = drop_shadow(canvas, x, y, img.width, img.height)
    canvas.paste(img, (x, y), img)
    return canvas


def gradient_bg(color, bg, size=2400):
    """Create a gradient background from light bg to slightly tinted."""
    c = Image.new('RGB', (size, size), bg)
    r, g, b = color
    for y in range(size):
        t = y / size * 0.08  # subtle color wash at bottom
        shade = tuple(int(bg[i] * (1-t) + color[i] * t) for i in range(3))
        ImageDraw.Draw(c).line([(0, y), (size, y)], fill=shade)
    return c


def ipad_on_bg(pid, page_num, cfg, ipad_w=820, ipad_h=1090, label=None):
    """Place a single iPad centered on a clean cream background."""
    bg = gradient_bg(cfg['color'], cfg['bg']).convert('RGBA')
    page = render_page(pid, page_num)
    ipad = make_ipad(page, ipad_w, ipad_h)
    cx, cy = CANVAS // 2, CANVAS // 2
    if label:
        cy -= 60  # shift up slightly for label
    bg = paste_centered(bg, ipad, cx, cy)
    bg = bg.convert('RGB')
    if label:
        d = ImageDraw.Draw(bg)
        tw = 700
        tx, ty = CANVAS//2, cy + ipad_h//2 + 70
        d.rounded_rectangle([tx-tw//2, ty-10, tx+tw//2, ty+70], radius=35, fill=cfg['color'])
        d.text((tx, ty+30), label, font=fb(38), fill=(255,255,255), anchor='mm')
    return bg


# ── Photo 01: Hero ─────────────────────────────────────────────────────────────

def make_hero(pid, cfg, out):
    bg = gradient_bg(cfg['color'], cfg['bg']).convert('RGBA')
    d_bg = ImageDraw.Draw(bg)

    # Decorative dots
    import random; random.seed(42)
    r, g, b = cfg['color']
    for _ in range(18):
        x, y = random.randint(50, CANVAS-50), random.randint(50, CANVAS-50)
        sz = random.randint(12, 40)
        alpha = random.randint(30, 80)
        dot = Image.new('RGBA', (sz*2, sz*2), (0,0,0,0))
        ImageDraw.Draw(dot).ellipse([0,0,sz*2-1,sz*2-1], fill=(r,g,b,alpha))
        bg.paste(dot, (x-sz, y-sz), dot)

    # Large iPad with cover page (centered-left, shifted up)
    cover = render_page(pid, cfg['cover'])
    ipad_main = make_ipad(cover, 900, 1195)
    mx = CANVAS//2 - 80
    my = CANVAS//2 - 30
    bg = paste_centered(bg, ipad_main, mx, my)

    # Small secondary iPad with monthly spread (lower-right, partially behind main)
    monthly = render_page(pid, cfg['monthly'])
    ipad_small = make_ipad(monthly, 520, 690)
    ipad_small_rot = ipad_small.rotate(-8, expand=True, resample=Image.BICUBIC)
    sx = mx + 560
    sy = my + 300
    bg = drop_shadow(bg, sx - ipad_small_rot.width//2 + 14, sy - ipad_small_rot.height//2 + 14,
                     ipad_small_rot.width, ipad_small_rot.height, blur=20, opacity=40)
    bg.paste(ipad_small_rot, (sx - ipad_small_rot.width//2, sy - ipad_small_rot.height//2), ipad_small_rot)

    # Text overlay
    bg = bg.convert('RGB')
    d = ImageDraw.Draw(bg)
    # Semi-transparent banner at top
    banner = Image.new('RGBA', (CANVAS, 240), cfg['color'] + (220,))
    bg_rgba = bg.convert('RGBA')
    bg_rgba.paste(banner, (0, 0), banner)
    bg = bg_rgba.convert('RGB')
    d = ImageDraw.Draw(bg)
    d.text((CANVAS//2, 80), cfg['name'], font=fb(72), fill=(255,255,255), anchor='mm')
    d.text((CANVAS//2, 166), f"GoodNotes · Notability · Instant Download", font=fr(46), fill=(240,235,250), anchor='mm')
    _sc = cfg.get('sticker_count', 200)
    _sc_label = f"{_sc}+ Kawaii Stickers" if _sc >= 200 else f"{_sc} Kawaii Stickers"
    # Edition label is product-specific — an undated-only planner (e.g. DP1031) must
    # NOT claim a "2026 Dated" version it doesn't ship. Default matches the dated
    # products (which include both a 2026-dated and an undated PDF).
    _edition = cfg.get('edition_label', '2026 Dated + Undated Version')
    d.text((CANVAS//2, CANVAS-55), f"✓ {_edition}   ✓ {cfg['pages']} Pages   ✓ {_sc_label}",
           font=fr(42), fill=cfg['color'], anchor='mm')

    bg.save(out, 'JPEG', quality=93)
    print(f"    01_hero.jpg")


# ── Photo 02: What's Included ──────────────────────────────────────────────────

CONTENTS = {
    'DP1026': [
        ("Interactive PDF Planner — 2026 Dated Version",  "104 pages · Lavender Dreams · US Letter"),
        ("Bonus Undated Version — works any year forever", "Same layout, no year dates"),
        ("Kawaii Sticker Pack ZIP",                        "11 illustrated sheets · 200+ stickers · transparent PNG"),
        ("Fully fillable text fields",                     "Type in GoodNotes, Notability, PDF Expert, Acrobat"),
        ("Hyperlinked side tabs",                          "Jump to any section in one tap"),
        ("Dashboard home page",                            "Tappable hub linking every section"),
    ],
    'DP1027': [
        ("Interactive PDF Planner — 2026 Dated Version",  "90 pages · Cotton Candy · US Letter"),
        ("Bonus Undated Version — works any school year", "Same layout, no year dates"),
        ("Kawaii Sticker Pack ZIP",                        "11 illustrated sheets · 200+ stickers · transparent PNG"),
        ("Fully fillable text fields",                     "Type in GoodNotes, Notability, PDF Expert, Acrobat"),
        ("Hyperlinked side tabs",                          "Jump to any section in one tap"),
        ("Dashboard home page",                            "Tappable hub linking every section"),
    ],
    'DP1028': [
        ("Interactive PDF Planner — 2026 Dated Version",  "102 pages · Midnight Blue · US Letter"),
        ("Bonus Undated Version — works any year forever", "Same layout, no year dates"),
        ("Kawaii Sticker Pack ZIP",                        "11 illustrated sheets · 200+ stickers · transparent PNG"),
        ("Fully fillable text fields",                     "Type in GoodNotes, Notability, PDF Expert, Acrobat"),
        ("Hyperlinked side tabs",                          "Jump to any section in one tap"),
        ("Debt payoff & savings trackers",                 "Visual progress tools for financial goals"),
    ],
    'DP1029': [
        ("Interactive PDF Planner — 2026 Dated Version",  "91 pages · Coral Peach · US Letter"),
        ("Bonus Undated Version — works any year forever", "Same layout, no year dates"),
        ("Kawaii Sticker Pack ZIP",                        "11 illustrated sheets · 200+ stickers · transparent PNG"),
        ("Fully fillable text fields",                     "Type in GoodNotes, Notability, PDF Expert, Acrobat"),
        ("Hyperlinked side tabs",                          "Jump to any section in one tap"),
        ("Meal planner + fitness log",                     "Weekly workout + meal planning spreads"),
    ],
    'DP1030': [
        ("Interactive PDF Planner — 2026 Dated Version",  "130 pages · Matcha Serenity · US Letter"),
        ("Bonus Undated Version — works any year forever", "Same layout, no year dates"),
        ("Kawaii Sticker Pack ZIP",                        "9 illustrated sheets · 219 stickers · transparent PNG"),
        ("Fully fillable text fields",                     "Type in GoodNotes, Notability, PDF Expert, Acrobat"),
        ("Hyperlinked side tabs",                           "Jump to any section in one tap"),
        ("Pomodoro focus + habit trackers",                 "ADHD-friendly time-blocking and streak tracking"),
    ],
    'DP1031': [
        ("Interactive PDF Planner — Undated Evergreen",    "141 pages · Sage Garden · US Letter"),
        ("Works any year, forever",                         "No dates to expire — start any month"),
        ("Kawaii Sticker Pack ZIP",                          "9 illustrated sheets · 247 stickers · transparent PNG"),
        ("Fully fillable text fields",                       "Type in GoodNotes, Notability, PDF Expert, Acrobat"),
        ("Hyperlinked side tabs",                             "Jump to any section in one tap"),
        ("Budget tracker + habit tracker",                    "Built-in financial and habit-building tools"),
    ],
    'DP1032': [
        ("Interactive PDF Planner — 2026 Dated Version",    "140 pages · Midnight Kawaii · US Letter"),
        ("Bonus Undated Version — works any year forever",   "Same layout, no year dates"),
        ("Kawaii Sticker Pack ZIP",                           "9 illustrated sheets · 183 stickers · transparent PNG"),
        ("Fully fillable text fields",                        "Type in GoodNotes, Notability, PDF Expert, Acrobat"),
        ("Hyperlinked side tabs",                              "Jump to any section in one tap"),
        ("Dark mode design + brain dump page",                 "Neon-on-dark theme, easy on the eyes at night"),
    ],
    'DP1033': [
        ("Interactive PDF Planner — 2026-2027 School Year", "107 pages · Sunflower Studio · US Letter"),
        ("Bonus Undated Version — works any school year",    "Same layout, no year dates"),
        ("Kawaii Sticker Pack ZIP",                           "9 illustrated sheets · 177 stickers · transparent PNG"),
        ("Fully fillable text fields",                        "Type in GoodNotes, Notability, PDF Expert, Acrobat"),
        ("Hyperlinked side tabs",                              "Jump to any section in one tap"),
        ("Lesson plans + class roster pages",                  "Weekly lesson planning and student roster tracking"),
    ],
}

def make_whats_included(pid, cfg, out):
    bg = Image.new('RGB', (CANVAS, CANVAS), cfg['bg'])
    d = ImageDraw.Draw(bg)
    # Header
    d.rectangle([0, 0, CANVAS, 280], fill=cfg['color'])
    d.text((CANVAS//2, 90), "WHAT'S INCLUDED", font=fb(96), fill=(255,255,255), anchor='mm')
    d.text((CANVAS//2, 208), cfg['name'], font=fr(52), fill=(240,235,250), anchor='mm')

    PAD = 90
    y = 330
    for main, sub in CONTENTS[pid]:
        # Card background
        d.rounded_rectangle([PAD, y, CANVAS-PAD, y+160], radius=18,
                            fill=(255,255,255), outline=cfg['accent'], width=3)
        # Check circle
        d.ellipse([PAD+22, y+35, PAD+90, y+103], fill=cfg['color'])
        d.text((PAD+56, y+69), "✓", font=fb(42), fill=(255,255,255), anchor='mm')
        d.text((PAD+118, y+56), main, font=fb(52), fill=(50,40,70))
        d.text((PAD+118, y+118), sub, font=fr(40), fill=(140,120,160))
        y += 176

    # Footer
    d.rectangle([0, CANVAS-180, CANVAS, CANVAS], fill=cfg['color'])
    d.text((CANVAS//2, CANVAS-90), "Instant Digital Download  ·  No physical item shipped",
           font=fb(52), fill=(255,255,255), anchor='mm')
    bg.save(out, 'JPEG', quality=93)
    print(f"    02_whats_included.jpg")


# ── Photos 03, 04, 09, 10: Spread pages ───────────────────────────────────────

def make_spread(pid, cfg, page_num, label, photo_num, out):
    bg = gradient_bg(cfg['color'], cfg['bg']).convert('RGBA')
    # Title at top
    bg = bg.convert('RGB')
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 0, CANVAS, 160], fill=cfg['color'])
    d.text((CANVAS//2, 80), label, font=fb(72), fill=(255,255,255), anchor='mm')

    bg = bg.convert('RGBA')
    page = render_page(pid, page_num)
    ipad = make_ipad(page, 920, 1220)
    cx, cy = CANVAS//2, CANVAS//2 + 90
    bg = paste_centered(bg, ipad, cx, cy)

    bg = bg.convert('RGB')
    d = ImageDraw.Draw(bg)
    d.text((CANVAS//2, CANVAS-55), f"{cfg['short']}  ·  {cfg['theme']}  ·  OnBrandCraftz",
           font=fr(40), fill=cfg['color'], anchor='mm')
    bg.save(out, 'JPEG', quality=93)
    print(f"    {photo_num:02d}_{label.lower().replace(' ','_')[:25]}.jpg")


# ── Photo 05: Sticker showcase ─────────────────────────────────────────────────

def make_sticker_showcase(pid, cfg, out):
    bg = Image.new('RGB', (CANVAS, CANVAS), cfg['bg'])
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 0, CANVAS, 200], fill=cfg['color'])
    sticker_count = cfg.get('sticker_count', 200)
    d.text((CANVAS//2, 100), f"{sticker_count}+ KAWAII STICKERS INCLUDED" if sticker_count >= 200
           else f"{sticker_count} KAWAII STICKERS INCLUDED",
           font=fb(78), fill=(255,255,255), anchor='mm')

    sheets = cfg['sticker_sheets']
    sheet_size = 960
    positions = [(120, 250), (1320, 250), (120, 1310), (1320, 1310)]

    for i, (sheet_num, (sx, sy)) in enumerate(zip(sheets, positions)):
        # Prefer a flat .jpg sheet, but fall back to the raw .png (the transparent
        # PNG the pack ships) or the processed png_sheets/ copy — so the showcase
        # never renders blank cards just because no .jpg was pre-made.
        src = None
        for cand in (os.path.join(ART_DIR, f'{pid}_sticker_sheet_{sheet_num}.jpg'),
                     os.path.join(ART_DIR, f'{pid}_sticker_sheet_{sheet_num}.png'),
                     os.path.join(DP_BASE, 'stickers', pid, 'png_sheets', f'{pid}_sheet_{sheet_num:02d}.png')):
            if os.path.exists(cand):
                src = cand
                break
        if not src:
            continue
        # Composite over white so a transparent PNG doesn't show as a black square.
        _raw = Image.open(src).convert('RGBA')
        _flat = Image.new('RGBA', _raw.size, (255, 255, 255, 255))
        _flat.alpha_composite(_raw)
        sheet = _flat.convert('RGB').resize((sheet_size, sheet_size), Image.LANCZOS)
        # White card
        card = Image.new('RGB', (sheet_size+16, sheet_size+16), (255,255,255))
        mask = Image.new('L', (sheet_size+16, sheet_size+16), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0,0,sheet_size+15,sheet_size+15], radius=20, fill=255)
        bg_rgba = bg.convert('RGBA')
        shadow = Image.new('RGBA', (CANVAS, CANVAS), (0,0,0,0))
        ImageDraw.Draw(shadow).rectangle([sx+12, sy+12, sx+sheet_size+28, sy+sheet_size+28], fill=(0,0,0,50))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=16))
        bg_rgba = Image.alpha_composite(bg_rgba, shadow)
        bg = bg_rgba.convert('RGB')
        bg.paste(card, (sx-8, sy-8))
        bg.paste(sheet, (sx, sy))
        d = ImageDraw.Draw(bg)

    d = ImageDraw.Draw(bg)
    sheet_count = cfg.get('sheet_count', 11)
    d.text((CANVAS//2, CANVAS-55), f"{sheet_count} illustrated sheets · {cfg['theme']} theme · transparent PNG",
           font=fr(44), fill=cfg['color'], anchor='mm')
    bg.save(out, 'JPEG', quality=93)
    print(f"    05_sticker_showcase.jpg")


# ── Photo 06: GoodNotes how-to ────────────────────────────────────────────────

def make_howto(pid, cfg, out):
    bg = Image.new('RGB', (CANVAS, CANVAS), cfg['bg'])
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 0, CANVAS, 200], fill=cfg['color'])
    d.text((CANVAS//2, 100), "HOW TO USE YOUR STICKERS IN GOODNOTES",
           font=fb(62), fill=(255,255,255), anchor='mm')

    steps = [
        ("Step 1", "Download & Unzip",
         "After purchase, download your files from Etsy.\nUnzip the sticker pack ZIP file."),
        ("Step 2", "Import into GoodNotes 6",
         f"Open GoodNotes 6 → tap Elements (◆)\n→ Stickers tab → tap + → select all {cfg.get('sheet_count', 11)} PNG files"),
        ("Step 3", "Drag Stickers onto Any Page",
         "All stickers appear in your library.\nTap any sticker and drag it onto any planner page!"),
    ]

    panel_w = (CANVAS - 160) // 3
    px = 60
    py = 260

    for i, (step, title, body) in enumerate(steps):
        # Panel card
        d.rounded_rectangle([px, py, px+panel_w, CANVAS-160], radius=24,
                            fill=(255,255,255), outline=cfg['accent'], width=4)
        # Step circle
        cx, cy = px + panel_w//2, py + 120
        d.ellipse([cx-80, cy-80, cx+80, cy+80], fill=cfg['color'])
        d.text((cx, cy), str(i+1), font=fb(90), fill=(255,255,255), anchor='mm')
        d.text((px + panel_w//2, py + 240), step, font=fb(44), fill=cfg['color'], anchor='mm')
        d.text((px + panel_w//2, py + 310), title, font=fb(56), fill=(50,40,70), anchor='mm')

        # Body text (word-wrapped manually)
        lines = body.split('\n')
        ty = py + 410
        for line in lines:
            d.text((px + panel_w//2, ty), line, font=fr(40), fill=(100,85,130), anchor='mm')
            ty += 60

        px += panel_w + 40

    d.rectangle([0, CANVAS-140, CANVAS, CANVAS], fill=cfg['color'])
    d.text((CANVAS//2, CANVAS-70),
           "Also works in Notability · PDF Expert · Xodo · Acrobat Reader",
           font=fb(46), fill=(255,255,255), anchor='mm')
    bg.save(out, 'JPEG', quality=93)
    print(f"    06_goodnotes_howto.jpg")


# ── Photo 08: Cover close-up ──────────────────────────────────────────────────

def make_cover_closeup(pid, cfg, out):
    # Blurred color background
    bg_color = Image.new('RGB', (CANVAS, CANVAS), cfg['color'])
    cover_full = render_page(pid, cfg['cover']).resize((CANVAS, CANVAS), Image.LANCZOS)
    cover_blur = cover_full.filter(ImageFilter.GaussianBlur(radius=60))
    bg = Image.blend(bg_color, cover_blur, alpha=0.3)

    bg = bg.convert('RGBA')
    cover = render_page(pid, cfg['cover'])
    ipad = make_ipad(cover, 1020, 1355)
    bg = paste_centered(bg, ipad, CANVAS//2, CANVAS//2 + 30)

    bg = bg.convert('RGB')
    d = ImageDraw.Draw(bg)
    d.text((CANVAS//2, 60), cfg['name'], font=fb(68), fill=(255,255,255), anchor='mm')
    d.text((CANVAS//2, CANVAS-60), f"{cfg['theme']}  ·  GoodNotes & Notability",
           font=fr(48), fill=(255,255,255), anchor='mm')
    bg.save(out, 'JPEG', quality=93)
    print(f"    08_cover_closeup.jpg")


# ── Upload photos to Etsy ──────────────────────────────────────────────────────

# Human-readable per-photo alt text (2026-07-15 ADA/WCAG audit fix) --
# filenames already encode what each slot shows (see photo_files below),
# so this maps the slug to a real description instead of leaving Etsy
# photos with zero screen-reader alt text. Baseline, not AI-per-photo
# captioning -- a reasonable quick fix, not the full solution.
_PHOTO_ALT_LABELS = {
    'hero': 'lifestyle hero photo on a desk',
    'whats_included': "what's included overview",
    'monthly_spread': 'monthly calendar spread preview',
    'weekly_spread': 'weekly spread preview',
    'sticker_showcase': 'kawaii sticker sheet showcase',
    'goodnotes_howto': 'GoodNotes sticker import how-to steps',
    'app_compatibility': 'compatible apps infographic',
    'cover_closeup': 'cover art close-up',
    'tracker': 'tracker page preview',
    'specialty': 'specialty feature page preview',
}


def _photo_alt_text(product_name, filename):
    slug = os.path.splitext(filename)[0].split('_', 1)[-1] if '_' in filename else filename
    label = _PHOTO_ALT_LABELS.get(slug, slug.replace('_', ' '))
    return f"{product_name} — {label}"[:500]


def upload_photos(listing_id, out_dir, photo_files, client, product_name=''):
    auth_headers = {
        "Authorization": f"Bearer {client.access_token}",
        "x-api-key": f"{client.client_id}:{client.client_secret}",
    }
    shop_id = client.shop_id

    # Clear existing images
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images",
        headers=auth_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        existing = json.loads(resp.read()).get('results', [])
    for img in existing:
        del_req = urllib.request.Request(
            f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/images/{img['listing_image_id']}",
            headers=auth_headers, method="DELETE")
        try:
            urllib.request.urlopen(del_req, timeout=15)
        except:
            pass
        time.sleep(0.3)
    if existing:
        print(f"    Cleared {len(existing)} existing images")

    # Upload new photos
    for rank, filename in enumerate(photo_files, 1):
        path = os.path.join(out_dir, filename)
        if not os.path.exists(path):
            print(f"    WARNING: {filename} not found")
            continue
        for attempt in range(3):
            try:
                alt_text = _photo_alt_text(product_name, filename) if product_name else None
                result = client.upload_listing_image(listing_id, path, rank=rank, alt_text=alt_text)
                print(f"    Uploaded rank {rank}: {filename} (id={result.get('listing_image_id')})")
                time.sleep(0.8)
                break
            except EtsyAPIError as e:
                if e.status == 401:
                    client.refresh_access_token()
                    auth_headers["Authorization"] = f"Bearer {client.access_token}"
                elif e.status == 429:
                    time.sleep(20)
                else:
                    print(f"    Upload failed ({e.status}): {e}")
                    break


# ── Main ──────────────────────────────────────────────────────────────────────

def generate_for_planner(pid, client, upload=True):
    cfg = PLANNER_PAGES[pid]
    out_dir = os.path.join(ART_DIR, f'{pid}_listing_images')
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'='*55}")
    print(f"  {pid} — {cfg['short']}")
    print(f"{'='*55}")

    make_hero(pid, cfg, os.path.join(out_dir, '01_hero.jpg'))
    make_whats_included(pid, cfg, os.path.join(out_dir, '02_whats_included.jpg'))
    make_spread(pid, cfg, cfg['monthly'], 'MONTHLY CALENDAR', 3, os.path.join(out_dir, '03_monthly_spread.jpg'))
    make_spread(pid, cfg, cfg['weekly'], 'WEEKLY SPREAD', 4, os.path.join(out_dir, '04_weekly_spread.jpg'))
    make_sticker_showcase(pid, cfg, os.path.join(out_dir, '05_sticker_showcase.jpg'))
    make_howto(pid, cfg, os.path.join(out_dir, '06_goodnotes_howto.jpg'))
    # Photo 7: app compatibility — copy existing
    app_dest = os.path.join(out_dir, '07_app_compatibility.jpg')
    if os.path.exists(APP_COMPAT_SRC) and os.path.abspath(APP_COMPAT_SRC) != os.path.abspath(app_dest):
        shutil.copy2(APP_COMPAT_SRC, app_dest)
        print(f"    07_app_compatibility.jpg (copied)")
    elif os.path.exists(app_dest):
        print(f"    07_app_compatibility.jpg (already present)")
    make_cover_closeup(pid, cfg, os.path.join(out_dir, '08_cover_closeup.jpg'))
    make_spread(pid, cfg, cfg['tracker'], cfg['tracker_label'], 9, os.path.join(out_dir, '09_tracker.jpg'))
    make_spread(pid, cfg, cfg['specialty'], cfg['specialty_label'], 10, os.path.join(out_dir, '10_specialty.jpg'))

    photo_files = [
        '01_hero.jpg', '02_whats_included.jpg', '03_monthly_spread.jpg',
        '04_weekly_spread.jpg', '05_sticker_showcase.jpg', '06_goodnotes_howto.jpg',
        '07_app_compatibility.jpg', '08_cover_closeup.jpg', '09_tracker.jpg', '10_specialty.jpg',
    ]

    if upload:
        print(f"\n  Uploading to Etsy listing {cfg['listing_id']}...")
        upload_photos(cfg['listing_id'], out_dir, photo_files, client, product_name=cfg['short'])

    print(f"\n  ✓ {pid} done")
    return out_dir, photo_files


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', help='Single PID to process (default: all 4)')
    parser.add_argument('--no-upload', action='store_true', help='Generate only, do not upload')
    args = parser.parse_args()

    client = EtsyAPIClient()
    client.refresh_access_token()

    pids = [args.pid] if args.pid else list(PLANNER_PAGES.keys())
    for pid in pids:
        generate_for_planner(pid, client, upload=not args.no_upload)

    if args.no_upload:
        print("\n✓ All planner photos generated (local only, not uploaded)")
    else:
        print("\n✓ All planner photos generated and uploaded")
