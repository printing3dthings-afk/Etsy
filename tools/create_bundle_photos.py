#!/usr/bin/env python3
"""
Generate listing photos for the All 4 Planners Bundle (listing 4512188970).
1 AI-generated hero + 7 PIL composites from existing planner assets.
"""
import os, sys, json, base64, urllib.request, time, shutil
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from PIL import Image, ImageDraw, ImageFont, ImageFilter

OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'
OUT_DIR = os.path.join(ART_DIR, 'bundle_listing_images')
os.makedirs(OUT_DIR, exist_ok=True)

CANVAS = 2400
PAD = 80
GAP = 60
CELL = (CANVAS - 2*PAD - GAP) // 2   # 1090 px per cell

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
    'DP1026': '104 pages',
    'DP1027': '90 pages',
    'DP1028': '102 pages',
    'DP1029': '91 pages',
}

# DP1026 has different numbering for some files
LIFESTYLE = {pid: os.path.join(ART_DIR, f'{pid}_listing_images', '01_main_ipad_lifestyle.jpg') for pid in PIDS}
MONTHLY = {
    'DP1026': os.path.join(ART_DIR, 'DP1026_listing_images', '06_monthly_spread.jpg'),
    'DP1027': os.path.join(ART_DIR, 'DP1027_listing_images', '03_monthly_spread.jpg'),
    'DP1028': os.path.join(ART_DIR, 'DP1028_listing_images', '03_monthly_spread.jpg'),
    'DP1029': os.path.join(ART_DIR, 'DP1029_listing_images', '03_monthly_spread.jpg'),
}
WEEKLY = {
    'DP1026': os.path.join(ART_DIR, 'DP1026_listing_images', '07_weekly_spread.jpg'),
    'DP1027': os.path.join(ART_DIR, 'DP1027_listing_images', '04_weekly_spread.jpg'),
    'DP1028': os.path.join(ART_DIR, 'DP1028_listing_images', '04_weekly_spread.jpg'),
    'DP1029': os.path.join(ART_DIR, 'DP1029_listing_images', '04_weekly_spread.jpg'),
}
STICKER_SHEET = {pid: os.path.join(ART_DIR, f'{pid}_sticker_sheet_4.jpg') for pid in PIDS}
APP_COMPAT_SRC = os.path.join(ART_DIR, 'DP1028_listing_images', '07_app_compatibility.jpg')


def find_font(size):
    for path in [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def find_font_reg(size):
    for path in [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def grid_positions():
    """Return (x, y) top-left corners for a 2×2 grid."""
    positions = []
    for row in range(2):
        for col in range(2):
            x = PAD + col * (CELL + GAP)
            y = PAD + row * (CELL + GAP)
            positions.append((x, y))
    return positions  # TL, TR, BL, BR


def paste_fit(canvas, img_path, x, y, w, h, round_corners=0):
    img = Image.open(img_path).convert('RGB')
    img = img.resize((w, h), Image.LANCZOS)
    if round_corners:
        mask = Image.new('L', (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w-1, h-1], radius=round_corners, fill=255)
        canvas.paste(img, (x, y), mask)
    else:
        canvas.paste(img, (x, y))


# ── Photo 01: Hero (AI-generated) ─────────────────────────────────────────────

def gen_hero(out_path):
    prompt = (
        "Professional Etsy product photography, square format. "
        "Four Silver iPad Pro 12.9-inch tablets arranged together on a light cream linen-textured desk in a loose cluster. "
        "Top-left iPad shows a lavender purple kawaii planner open to a monthly calendar page. "
        "Top-right iPad shows a cotton candy pink kawaii student planner open to a weekly layout. "
        "Bottom-left iPad shows a deep midnight blue finance planner open to a budget tracking page. "
        "Bottom-right iPad shows a warm coral pink fitness planner open to a habit tracker page. "
        "Props scattered between the iPads: a small succulent, a steaming latte mug, washi tape roll, "
        "dried lavender sprig, fine-tip pen, a few loose kawaii stickers. "
        "Soft diffused natural window light from the left, warm white balance. "
        "Photography style: bright airy editorial Etsy lifestyle. "
        "All four iPad screens clearly visible and sharp. No hands. No text overlays."
    )
    payload = json.dumps({
        "model": "gpt-image-1", "prompt": prompt, "n": 1,
        "size": "1024x1024", "quality": "high", "output_format": "jpeg"
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"},
        method="POST"
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            img_bytes = base64.b64decode(data["data"][0]["b64_json"])
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            # Upscale to 2400×2400
            img = Image.open(out_path).convert('RGB').resize((CANVAS, CANVAS), Image.LANCZOS)
            img.save(out_path, 'JPEG', quality=93)
            print(f"  01_hero.jpg generated ({len(img_bytes)//1024}KB)")
            return True
        except Exception as e:
            if attempt < 2:
                print(f"  Retry {attempt+1}: {e}")
                time.sleep(20)
            else:
                print(f"  ERROR generating hero: {e}")
                return False


# ── Photo 02: Four Themes (2×2 lifestyle grid) ────────────────────────────────

def make_four_themes(out_path):
    bg = Image.new('RGB', (CANVAS, CANVAS), (250, 248, 245))
    draw = ImageDraw.Draw(bg)
    pos = grid_positions()
    for i, pid in enumerate(PIDS):
        x, y = pos[i]
        color = THEME_COLORS[pid]
        # Color accent border
        draw.rectangle([x-8, y-8, x+CELL+8, y+CELL+8], fill=color)
        paste_fit(bg, LIFESTYLE[pid], x, y, CELL, CELL, round_corners=12)
        # Label ribbon at bottom of each cell
        ribbon_h = 70
        ribbon = Image.new('RGBA', (CELL, ribbon_h), color + (200,))
        bg_rgba = bg.convert('RGBA')
        bg_rgba.paste(ribbon, (x, y + CELL - ribbon_h), ribbon)
        bg = bg_rgba.convert('RGB')
        draw = ImageDraw.Draw(bg)
        font = find_font(34)
        label = NAMES[pid]
        draw.text((x + CELL//2, y + CELL - ribbon_h//2), label,
                  font=font, fill=(255,255,255), anchor='mm')

    # Title at bottom
    font_title = find_font(72)
    draw.text((CANVAS//2, CANVAS - 48), "ALL 4 PLANNERS BUNDLE",
              font=font_title, fill=(60, 40, 80), anchor='mb')
    bg.save(out_path, 'JPEG', quality=93)
    print("  02_four_themes.jpg saved")


# ── Photo 03: Monthly Spreads 2×2 ─────────────────────────────────────────────

def make_grid(src_dict, title_top, title_bottom, out_path):
    bg = Image.new('RGB', (CANVAS, CANVAS), (250, 248, 245))
    draw = ImageDraw.Draw(bg)
    pos = grid_positions()
    for i, pid in enumerate(PIDS):
        x, y = pos[i]
        color = THEME_COLORS[pid]
        draw.rectangle([x-6, y-6, x+CELL+6, y+CELL+6], fill=color)
        paste_fit(bg, src_dict[pid], x, y, CELL, CELL, round_corners=10)
    font_top = find_font(70)
    font_bot = find_font_reg(48)
    draw.text((CANVAS//2, 36), title_top, font=font_top, fill=(60,40,80), anchor='mt')
    draw.text((CANVAS//2, CANVAS - 36), title_bottom, font=font_bot, fill=(120,100,140), anchor='mb')
    bg.save(out_path, 'JPEG', quality=93)
    print(f"  {os.path.basename(out_path)} saved")


# ── Photo 05: Sticker Showcase ─────────────────────────────────────────────────

def drop_shadow(canvas_rgba, x, y, w, h, blur=20, opacity=70):
    layer = Image.new('RGBA', (CANVAS, CANVAS), (0,0,0,0))
    ImageDraw.Draw(layer).rectangle([x+12, y+12, x+w+12, y+h+12], fill=(0,0,0,opacity))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=blur))
    return Image.alpha_composite(canvas_rgba, layer)


def make_sticker_showcase(out_path):
    # Warm cream gradient background
    bg = Image.new('RGB', (CANVAS, CANVAS), (255, 252, 247))
    # Subtle gradient
    for y in range(CANVAS):
        shade = int(255 - y * 8 / CANVAS)
        ImageDraw.Draw(bg).line([(0, y), (CANVAS, y)], fill=(shade, shade - 4, shade - 10))

    bg = bg.convert('RGBA')

    # ── Hero sheet: DP1027 sheet_4 (cleanest cozy lifestyle) ────────────────
    # Show it large and centered-left so individual stickers are clearly visible
    hero_size = 1680
    hero_x = (CANVAS - hero_size) // 2
    hero_y = 280

    # White card with rounded shadow
    bg = drop_shadow(bg, hero_x - 20, hero_y - 20, hero_size + 40, hero_size + 40, blur=30, opacity=60)
    card = Image.new('RGBA', (hero_size + 40, hero_size + 40), (255, 255, 255, 255))
    mask = Image.new('L', (hero_size + 40, hero_size + 40), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, hero_size + 39, hero_size + 39], radius=28, fill=255)
    card.putalpha(mask)
    bg.paste(card, (hero_x - 20, hero_y - 20), card)

    hero = Image.open(STICKER_SHEET['DP1027']).convert('RGBA').resize((hero_size, hero_size), Image.LANCZOS)
    bg.paste(hero, (hero_x, hero_y), hero)

    # ── Three small sheets fanned behind the hero (top-left, top-right, bottom) ─
    small_size = 480
    small_sheets = [
        (os.path.join(ART_DIR, 'DP1026_sticker_sheet_4.jpg'), -18, 60,  140),
        (os.path.join(ART_DIR, 'DP1028_sticker_sheet_4.jpg'),  12, CANVAS - small_size - 140, 140),
        (os.path.join(ART_DIR, 'DP1029_sticker_sheet_3.jpg'),  -8, CANVAS//2 - small_size//2, CANVAS - small_size - 140),
    ]
    for sheet_path, rot, sx, sy in small_sheets:
        sheet = Image.open(sheet_path).convert('RGBA').resize((small_size, small_size), Image.LANCZOS)
        card_s = Image.new('RGBA', (small_size + 16, small_size + 16), (255, 255, 255, 245))
        mask_s = Image.new('L', (small_size + 16, small_size + 16), 0)
        ImageDraw.Draw(mask_s).rounded_rectangle([0, 0, small_size + 15, small_size + 15], radius=16, fill=255)
        card_s.putalpha(mask_s)
        if rot != 0:
            card_r = card_s.rotate(rot, expand=True, resample=Image.BICUBIC)
            sheet_r = sheet.rotate(rot, expand=True, resample=Image.BICUBIC)
            bg.paste(card_r, (sx, sy), card_r)
            bg.paste(sheet_r, (sx + 8, sy + 8), sheet_r)
        else:
            bg.paste(card_s, (sx, sy), card_s)
            bg.paste(sheet, (sx + 8, sy + 8), sheet)

    bg = bg.convert('RGB')
    draw = ImageDraw.Draw(bg)

    # ── Top header ────────────────────────────────────────────────────────────
    font_h1  = find_font(88)
    font_h2  = find_font_reg(52)
    draw.text((CANVAS//2, 100), "800+ KAWAII STICKERS INCLUDED",
              font=font_h1, fill=(80, 50, 110), anchor='mm')
    draw.text((CANVAS//2, 190), "5 illustrated sheets per planner  ·  4 planners",
              font=font_h2, fill=(150, 120, 180), anchor='mm')

    # ── Bottom pill badges ────────────────────────────────────────────────────
    badges = [
        ("Cozy Lifestyle",     THEME_COLORS['DP1026']),
        ("Seasonal & Holiday", THEME_COLORS['DP1027']),
        ("Functional Planning",THEME_COLORS['DP1028']),
        ("GoodNotes Ready",    THEME_COLORS['DP1029']),
    ]
    badge_w, badge_h = 480, 72
    total_badge_w = len(badges) * badge_w + (len(badges)-1) * 24
    bx = (CANVAS - total_badge_w) // 2
    by = CANVAS - 110
    for label, color in badges:
        draw.rounded_rectangle([bx, by, bx+badge_w, by+badge_h], radius=36, fill=color)
        font_b = find_font(34)
        draw.text((bx + badge_w//2, by + badge_h//2), label,
                  font=font_b, fill=(255,255,255), anchor='mm')
        bx += badge_w + 24

    bg.save(out_path, 'JPEG', quality=93)
    print("  05_sticker_showcase.jpg saved")


# ── Photo 06: Savings Graphic ──────────────────────────────────────────────────

def make_savings(out_path):
    bg = Image.new('RGB', (CANVAS, CANVAS), (250, 248, 245))
    draw = ImageDraw.Draw(bg)

    # Header block
    header_h = 360
    draw.rectangle([0, 0, CANVAS, header_h], fill=(134, 102, 170))
    font_h1 = find_font(110)
    font_h2 = find_font_reg(60)
    draw.text((CANVAS//2, 120), "BUNDLE & SAVE", font=font_h1, fill=(255,255,255), anchor='mm')
    draw.text((CANVAS//2, 270), "All 4 Planners + 800+ Stickers", font=font_h2, fill=(230,220,245), anchor='mm')

    # Line items
    items = [
        ('🌸 Life Planner (104 pages)', '$14.99', THEME_COLORS['DP1026']),
        ('🩷 Student Planner (90 pages)', '$9.99',  THEME_COLORS['DP1027']),
        ('💙 Budget Planner (102 pages)', '$12.99', THEME_COLORS['DP1028']),
        ('🍑 Fitness Planner (91 pages)', '$12.99', THEME_COLORS['DP1029']),
    ]
    font_item = find_font_reg(68)
    font_price = find_font(68)
    y = 430
    row_h = 200
    for name, price, color in items:
        # Row background
        draw.rectangle([PAD, y, CANVAS-PAD, y+row_h-16], fill=(245,242,255), outline=color, width=4)
        # Color dot
        draw.ellipse([PAD+20, y+row_h//2-28, PAD+76, y+row_h//2+28], fill=color)
        draw.text((PAD+110, y+row_h//2), name, font=font_item, fill=(60,40,80), anchor='lm')
        draw.text((CANVAS-PAD-20, y+row_h//2), price, font=font_price, fill=color, anchor='rm')
        y += row_h

    # Divider
    draw.line([PAD, y+10, CANVAS-PAD, y+10], fill=(180,160,200), width=4)
    y += 30

    # Subtotal (crossed out)
    font_sub = find_font_reg(68)
    draw.text((PAD+110, y+60), "If bought separately:", font=font_sub, fill=(150,130,170), anchor='lm')
    draw.text((CANVAS-PAD-20, y+60), "$50.96", font=font_price, fill=(180,160,200), anchor='rm')
    # Strikethrough
    bbox = draw.textbbox((CANVAS-PAD-20, y+60), "$50.96", font=font_price, anchor='rm')
    mid = (bbox[1] + bbox[3]) // 2
    draw.line([bbox[0]-4, mid, bbox[2]+4, mid], fill=(200,100,100), width=6)
    y += 140

    # Bundle price
    draw.rectangle([PAD, y, CANVAS-PAD, y+200], fill=(134,102,170))
    font_bundle = find_font(88)
    draw.text((CANVAS//2, y+60), "BUNDLE PRICE", font=find_font(56), fill=(220,210,240), anchor='mm')
    draw.text((CANVAS//2, y+150), "$39.99  —  Save $10.97!", font=font_bundle, fill=(255,255,255), anchor='mm')

    bg.save(out_path, 'JPEG', quality=93)
    print("  06_savings.jpg saved")


# ── Photo 07: App Compatibility (copy) ────────────────────────────────────────

def copy_app_compat(out_path):
    if os.path.exists(APP_COMPAT_SRC):
        shutil.copy2(APP_COMPAT_SRC, out_path)
        print("  07_app_compatibility.jpg copied")
    else:
        print(f"  WARNING: app compat source not found: {APP_COMPAT_SRC}")


# ── Photo 08: What's Included Card ────────────────────────────────────────────

def make_whats_included(out_path):
    bg = Image.new('RGB', (CANVAS, CANVAS), (250, 248, 245))
    draw = ImageDraw.Draw(bg)

    # Header
    draw.rectangle([0, 0, CANVAS, 300], fill=(134, 102, 170))
    font_hdr = find_font(100)
    draw.text((CANVAS//2, 150), "WHAT'S INCLUDED", font=font_hdr, fill=(255,255,255), anchor='mm')

    lines = [
        ("✅  Kawaii Life Planner 2026 + Undated", "(104 pages, Lavender Dreams)"),
        ("✅  Student Planner 2026 + Undated",      "(90 pages, Cotton Candy)"),
        ("✅  Budget Planner 2026 + Undated",        "(102 pages, Midnight Blue)"),
        ("✅  Fitness Planner 2026 + Undated",       "(91 pages, Coral Peach)"),
        ("✅  4 Kawaii Sticker Packs",               "(800+ stickers, 20 PNG sheets)"),
        ("✅  8 PDF Files Total",                    "(4 dated 2026 + 4 undated)"),
        ("✅  Instant Digital Download",              "No physical item shipped"),
    ]
    font_line = find_font(60)
    font_sub  = find_font_reg(50)
    y = 360
    for main, sub in lines:
        draw.text((PAD+20, y), main, font=font_line, fill=(60,40,80))
        y += 80
        draw.text((PAD+60, y), sub, font=font_sub, fill=(140,120,160))
        y += 90

    # Footer
    draw.rectangle([0, CANVAS-200, CANVAS, CANVAS], fill=(60,40,80))
    font_ft = find_font(72)
    draw.text((CANVAS//2, CANVAS-100), "387 pages  •  800+ stickers  •  $39.99",
              font=font_ft, fill=(220,200,255), anchor='mm')

    bg.save(out_path, 'JPEG', quality=93)
    print("  08_whats_included.jpg saved")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Generating bundle listing photos...")
    print()

    print("1/8 — Hero image (AI generation)...")
    gen_hero(os.path.join(OUT_DIR, '01_hero.jpg'))
    time.sleep(2)

    print("2/8 — Four themes grid...")
    make_four_themes(os.path.join(OUT_DIR, '02_four_themes.jpg'))

    print("3/8 — Monthly spreads grid...")
    make_grid(MONTHLY, "SEE INSIDE — MONTHLY VIEW",
              "12 monthly calendars per planner × 4 planners",
              os.path.join(OUT_DIR, '03_monthly_spreads.jpg'))

    print("4/8 — Weekly spreads grid...")
    make_grid(WEEKLY, "SEE INSIDE — WEEKLY VIEW",
              "52 weekly spreads per planner × 4 planners",
              os.path.join(OUT_DIR, '04_weekly_spreads.jpg'))

    print("5/8 — Sticker showcase...")
    make_sticker_showcase(os.path.join(OUT_DIR, '05_sticker_showcase.jpg'))

    print("6/8 — Savings graphic...")
    make_savings(os.path.join(OUT_DIR, '06_savings.jpg'))

    print("7/8 — App compatibility...")
    copy_app_compat(os.path.join(OUT_DIR, '07_app_compatibility.jpg'))

    print("8/8 — What's included card...")
    make_whats_included(os.path.join(OUT_DIR, '08_whats_included.jpg'))

    print()
    print("Done! All 8 photos saved to:", OUT_DIR)
    files = sorted(os.listdir(OUT_DIR))
    for f in files:
        size = os.path.getsize(os.path.join(OUT_DIR, f)) // 1024
        print(f"  {f}  ({size}KB)")


if __name__ == '__main__':
    main()
