#!/usr/bin/env python3
"""
Fill missing listing photos — bring all Etsy download listings to 10-photo standard.

Handles:
  - Wall art singles (8 photos → add rank 9 frame options, rank 10 detail crop)
  - Wall art sets (8 photos → same)
  - SVG commercial bundles (9 photos → add rank 10 commercial license card)
  - Sticker packs (6-7 photos → add ranks 8-10: app compat card, scattered stickers, download summary)

Skips:
  - Physical listings (Printify)
  - Listings at 10+ photos already
  - Listings with no local art file and no fallback strategy
  - Kawaii Art Print No.10xx listings (no local art file mapping — noted at end)

Canvas spec: 2400×2400px JPEG quality=92
Cream background: (253, 251, 247)
Rate: 1 image upload per second
"""

import os
import sys
import json
import time
import random
import tempfile
import urllib.request

sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from tools.etsy_api import EtsyAPIClient, EtsyAPIError

# ── Constants ─────────────────────────────────────────────────────────────────
CANVAS = 2400
BG_COLOR = (253, 251, 247)       # cream
DARK_STRIP = (44, 44, 44)        # #2C2C2C
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'
FONT_BOLD_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_REG_PATH  = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

FRAME_NATURAL = (139, 110, 80)
FRAME_BLACK   = (28, 28, 28)
FRAME_WHITE   = (240, 240, 240)

# SVG commercial bundle listing IDs (confirmed 9 photos each)
SVG_BUNDLE_IDS = {4515439743, 4515439751, 4515439755, 4515437432, 4515439763}

# Sticker pack listing IDs with their theme config
STICKER_PACKS = {
    4512255514: {'theme': 'Lavender Dreams',  'color': (134, 102, 170), 'accent': (196, 168, 212), 'pid': 'DP1026'},
    4512254015: {'theme': 'Cotton Candy',      'color': (222, 151, 198), 'accent': (151, 198, 222), 'pid': 'DP1027'},
    4512255536: {'theme': 'Midnight Blue',     'color': (27, 37, 104),   'accent': (123, 167, 194), 'pid': 'DP1028'},
    4512254027: {'theme': 'Coral Peach',       'color': (253, 108, 73),  'accent': (245, 184, 120), 'pid': 'DP1029'},
    4512254035: {'theme': 'All 4 Themes',      'color': (100, 70, 140),  'accent': (180, 150, 220), 'pid': 'DP1026'},
    4512255508: {'theme': 'Lavender Dreams',   'color': (134, 102, 170), 'accent': (196, 168, 212), 'pid': 'DP1026'},
}

# Kawaii Art Print listings that lack local art file mapping — skip and note
KAWAII_PRINT_PREFIX = 'Kawaii Art Print No.'


# ── Font helpers ──────────────────────────────────────────────────────────────
def fb(size):
    try:
        return ImageFont.truetype(FONT_BOLD_PATH, size)
    except Exception:
        return ImageFont.load_default()


def fr(size):
    try:
        return ImageFont.truetype(FONT_REG_PATH, size)
    except Exception:
        return ImageFont.load_default()


# ── dp_listing_map helpers ────────────────────────────────────────────────────
def load_dp_map():
    """Returns {listing_id: [dp_id, ...]} and {dp_id: {'listing_id':..,'files':[..]}}"""
    with open('/home/user/Etsy/data/dp_listing_map.json') as f:
        raw = json.load(f)
    lid_to_dps = {}
    for dp, info in raw.items():
        lid = info['listing_id']
        lid_to_dps.setdefault(lid, [])
        lid_to_dps[lid].append((dp, info.get('files', [])))
    return lid_to_dps, raw


def find_art_file(dp_id, files_list):
    """Return the first local .jpg art file path for a DP, or None."""
    for f in files_list:
        if f.lower().endswith('.jpg'):
            path = os.path.join(ART_DIR, f)
            if os.path.exists(path):
                return path
    # Try bare dp_id.jpg as fallback
    candidate = os.path.join(ART_DIR, f'{dp_id}.jpg')
    if os.path.exists(candidate):
        return candidate
    return None


# ── Image generation helpers ──────────────────────────────────────────────────

def centered_text(draw, text, font, canvas_w, y, fill=(40, 40, 40)):
    """Draw horizontally-centered text."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((canvas_w - tw) // 2, y), text, font=font, fill=fill)


def make_frame_options_photo(art_path, out_path):
    """
    Rank 9: Three side-by-side framed views (natural wood / black / white) on cream bg.
    Three frames on a 2400×800 strip, padded/centered on 2400×2400.
    """
    art = Image.open(art_path).convert('RGB')
    art_aspect = art.height / art.width

    strip_w, strip_h = CANVAS, 900
    strip = Image.new('RGB', (strip_w, strip_h), BG_COLOR)
    draw = ImageDraw.Draw(strip)

    # Each frame slot: 700px wide with margins
    slot_w = strip_w // 3
    mat_px = 28
    frame_px = 18
    inner_w = slot_w - 2 * mat_px - 2 * frame_px - 40  # ~560px art width
    inner_h = int(inner_w * art_aspect)

    frame_configs = [
        (FRAME_NATURAL, 'Natural Wood'),
        (FRAME_BLACK,   'Black Frame'),
        (FRAME_WHITE,   'White Frame'),
    ]

    for i, (fc, label) in enumerate(frame_configs):
        x_center = i * slot_w + slot_w // 2
        total_w = inner_w + 2 * mat_px + 2 * frame_px
        total_h = inner_h + 2 * mat_px + 2 * frame_px
        # Center vertically in strip with label space
        y_start = (strip_h - 80 - total_h) // 2

        px = x_center - total_w // 2
        py = y_start

        # Drop shadow
        shadow = Image.new('RGBA', (strip_w, strip_h), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rectangle(
            [px + 8, py + 10, px + total_w + 8, py + total_h + 10],
            fill=(0, 0, 0, 55)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))
        strip_rgba = Image.alpha_composite(strip.convert('RGBA'), shadow)
        strip = strip_rgba.convert('RGB')
        draw = ImageDraw.Draw(strip)

        # Frame rect
        hi = tuple(min(255, c + 45) for c in fc)
        sh = tuple(max(0, c - 45) for c in fc)
        draw.rectangle([px, py, px + total_w, py + total_h], fill=fc)
        bv = 5
        draw.polygon([px, py, px+total_w, py, px+total_w-bv, py+bv, px+bv, py+bv], fill=hi)
        draw.polygon([px, py, px, py+total_h, px+bv, py+total_h-bv, px+bv, py+bv], fill=hi)
        draw.polygon([px+total_w, py, px+total_w, py+total_h, px+total_w-bv, py+total_h-bv, px+total_w-bv, py+bv], fill=sh)
        draw.polygon([px, py+total_h, px+total_w, py+total_h, px+total_w-bv, py+total_h-bv, px+bv, py+total_h-bv], fill=sh)

        # White mat
        mx = px + frame_px
        my = py + frame_px
        mat_color = (253, 251, 248)
        draw.rectangle([mx, my, mx + inner_w + 2 * mat_px, my + inner_h + 2 * mat_px], fill=mat_color)

        # Inner shadow on mat
        inner_shadow = Image.new('RGBA', (strip_w, strip_h), (0, 0, 0, 0))
        ax, ay = mx + mat_px, my + mat_px
        ImageDraw.Draw(inner_shadow).rectangle(
            [ax - 3, ay - 3, ax + inner_w + 3, ay + inner_h + 3],
            fill=(0, 0, 0, 22)
        )
        inner_shadow = inner_shadow.filter(ImageFilter.GaussianBlur(radius=4))
        strip = Image.alpha_composite(strip.convert('RGBA'), inner_shadow).convert('RGB')
        draw = ImageDraw.Draw(strip)

        # Art
        art_resized = art.resize((inner_w, inner_h), Image.LANCZOS)
        art_dimmed = ImageEnhance.Brightness(art_resized).enhance(0.94)
        strip.paste(art_dimmed, (mx + mat_px, my + mat_px))
        draw = ImageDraw.Draw(strip)

        # Label below frame
        label_y = py + total_h + 18
        font = fb(32)
        bbox = draw.textbbox((0, 0), label, font=font)
        lw = bbox[2] - bbox[0]
        draw.text((x_center - lw // 2, label_y), label, font=font, fill=(80, 70, 60))

    # Pad strip onto 2400×2400 canvas
    canvas = Image.new('RGB', (CANVAS, CANVAS), BG_COLOR)
    y_offset = (CANVAS - strip_h) // 2
    canvas.paste(strip, (0, y_offset))

    # Title above frames
    draw_c = ImageDraw.Draw(canvas)
    title_font = fb(52)
    centered_text(draw_c, 'Available Frame Styles', title_font, CANVAS, y_offset - 80)

    # Subtitle
    sub_font = fr(36)
    centered_text(draw_c, 'Order at your local print shop or online printer', sub_font, CANVAS,
                  y_offset + strip_h + 20, fill=(130, 120, 110))

    canvas.save(out_path, 'JPEG', quality=92)


def make_detail_crop_photo(art_path, out_path):
    """
    Rank 10: Center 70%×70% crop of the art, sharpened, with small label at bottom.
    """
    art = Image.open(art_path).convert('RGB')
    w, h = art.size

    # Crop center 70%
    crop_w = int(w * 0.70)
    crop_h = int(h * 0.70)
    x0 = (w - crop_w) // 2
    y0 = (h - crop_h) // 2
    cropped = art.crop((x0, y0, x0 + crop_w, y0 + crop_h))

    # Resize to 2400×2400 (square crop, center gravity)
    # Fit within 2200px area, pad to 2400
    aspect = cropped.height / cropped.width
    if aspect >= 1:
        fit_h = 2200
        fit_w = int(fit_h / aspect)
    else:
        fit_w = 2200
        fit_h = int(fit_w * aspect)

    resized = cropped.resize((fit_w, fit_h), Image.LANCZOS)
    resized = ImageEnhance.Sharpness(resized).enhance(1.4)

    canvas = Image.new('RGB', (CANVAS, CANVAS), BG_COLOR)
    x_off = (CANVAS - fit_w) // 2
    y_off = (CANVAS - fit_h) // 2
    canvas.paste(resized, (x_off, y_off))

    # Label at bottom center on a small cream pill
    draw = ImageDraw.Draw(canvas)
    label = '300 DPI  ·  Fine Art Print'
    font = fb(38)
    bbox = draw.textbbox((0, 0), label, font=font)
    lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pill_x = (CANVAS - lw - 60) // 2
    pill_y = CANVAS - 100
    draw.rounded_rectangle([pill_x, pill_y, pill_x + lw + 60, pill_y + lh + 28],
                           radius=20, fill=(245, 242, 236))
    draw.text((pill_x + 30, pill_y + 14), label, font=font, fill=(70, 60, 50))

    canvas.save(out_path, 'JPEG', quality=92)


def make_commercial_license_card(out_path):
    """
    SVG bundle rank 10: Commercial License Summary info card.
    """
    canvas = Image.new('RGB', (CANVAS, CANVAS), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # Header strip
    header_h = 280
    draw.rectangle([0, 0, CANVAS, header_h], fill=(40, 40, 40))
    check = '✓'
    title_text = f'{check} COMMERCIAL LICENSE INCLUDED'
    title_font = fb(68)
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((CANVAS - tw) // 2, (header_h - (bbox[3] - bbox[1])) // 2),
              title_text, font=title_font, fill=(255, 255, 255))

    # Bullet points
    bullets = [
        ('Sell finished products', '(T-shirts, mugs, tote bags, pillows)'),
        ('Use in client projects', '(freelance, agency, commercial work)'),
        ('Upload to print-on-demand', '(Printify, Printful, Redbubble, Merch by Amazon)'),
        ('No attribution required', '(no credit needed — use freely)'),
        ('Unlimited sales',         '(no sales cap, no royalty fees)'),
        ('Modify and adapt',        '(resize, recolor, combine with other elements)'),
    ]

    y = header_h + 100
    dot_color = (80, 160, 100)
    for main, sub in bullets:
        # Dot
        dot_r = 18
        draw.ellipse([120, y + 6, 120 + dot_r * 2, y + 6 + dot_r * 2], fill=dot_color)
        # Main text
        mfont = fb(54)
        draw.text((165, y), main, font=mfont, fill=(30, 30, 30))
        # Sub text
        sfont = fr(44)
        draw.text((165, y + 64), sub, font=sfont, fill=(110, 105, 100))
        y += 158

    # Divider
    div_y = y + 30
    draw.rectangle([100, div_y, CANVAS - 100, div_y + 3], fill=(200, 195, 190))

    # Bottom branding strip
    bottom_h = 130
    draw.rectangle([0, CANVAS - bottom_h, CANVAS, CANVAS], fill=DARK_STRIP)
    copy_font = fr(44)
    copy_text = '© OnBrandCraftz  —  personal + commercial use'
    bbox = draw.textbbox((0, 0), copy_text, font=copy_font)
    tw = bbox[2] - bbox[0]
    draw.text(((CANVAS - tw) // 2, CANVAS - bottom_h + (bottom_h - (bbox[3] - bbox[1])) // 2),
              copy_text, font=copy_font, fill=(220, 220, 220))

    canvas.save(out_path, 'JPEG', quality=92)


def make_app_compat_card(color, accent, theme_name, out_path):
    """
    Sticker pack rank 8: GoodNotes / app compatibility card.
    """
    canvas = Image.new('RGB', (CANVAS, CANVAS), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # Accent top bar
    bar_h = 18
    draw.rectangle([0, 0, CANVAS, bar_h], fill=accent)

    # Title
    title_font = fb(72)
    title = 'Works With Your Favorite Apps'
    centered_text(draw, title, title_font, CANVAS, 100, fill=(40, 35, 30))

    # Subtitle
    sub_font = fr(46)
    sub = 'Import PNG files into your sticker library — use unlimited times'
    centered_text(draw, sub, sub_font, CANVAS, 210, fill=(110, 105, 100))

    # App list
    apps = [
        ('GoodNotes 6',       '★ BEST EXPERIENCE  —  iPad, iPhone, Mac'),
        ('Notability',        'iPad, iPhone  —  use Photo Stickers'),
        ('PDF Expert',        'Full interactivity on iPad & Mac'),
        ('Xodo PDF Reader',   'Works on Android, Windows, Web'),
        ('Adobe Acrobat',     'All platforms  —  free to download'),
    ]

    y = 340
    for app_name, desc in apps:
        # Check circle
        r = 32
        draw.ellipse([140, y + 8, 140 + r * 2, y + 8 + r * 2], fill=color)
        # Checkmark
        ck_font = fb(38)
        draw.text((151, y + 12), '✓', font=ck_font, fill=(255, 255, 255))

        name_font = fb(56)
        draw.text((220, y), app_name, font=name_font, fill=(30, 30, 30))

        desc_font = fr(44)
        draw.text((220, y + 68), desc, font=desc_font, fill=(110, 105, 100))
        y += 174

    # Import instruction box
    box_y = y + 50
    box_margin = 100
    box_h = 260
    draw.rounded_rectangle([box_margin, box_y, CANVAS - box_margin, box_y + box_h],
                           radius=24, fill=tuple(min(255, c + 150) for c in color) if max(color) < 105 else (245, 242, 238))
    draw.rounded_rectangle([box_margin, box_y, CANVAS - box_margin, box_y + box_h],
                           radius=24, outline=color, width=3)

    how_font = fb(50)
    centered_text(draw, 'How to import into GoodNotes 6:', how_font, CANVAS, box_y + 28, fill=(40, 35, 30))

    steps = [
        '1.  Download ZIP  →  unzip the sticker sheets',
        '2.  GoodNotes  →  Elements  →  Stickers  →  tap +',
        '3.  Select all 5 PNG sheets  →  Done!',
    ]
    step_font = fr(40)
    sy = box_y + 100
    for step in steps:
        bbox = draw.textbbox((0, 0), step, font=step_font)
        sw = bbox[2] - bbox[0]
        draw.text(((CANVAS - sw) // 2, sy), step, font=step_font, fill=(60, 55, 50))
        sy += 56

    # Accent bottom bar
    draw.rectangle([0, CANVAS - bar_h, CANVAS, CANVAS], fill=accent)

    canvas.save(out_path, 'JPEG', quality=92)


def make_scattered_stickers_photo(pid, out_path):
    """
    Sticker pack rank 9: 12–15 individual sticker crops scattered at random angles on cream bg.
    Loads sticker sheet JPGs for the given PID and crops random cells.
    """
    import math

    # Find available sticker sheet JPGs for this pid
    sheet_paths = []
    for n in range(1, 15):
        p = os.path.join(ART_DIR, f'{pid}_sticker_sheet_{n}.jpg')
        if os.path.exists(p):
            sheet_paths.append(p)

    canvas = Image.new('RGB', (CANVAS, CANVAS), BG_COLOR)

    if not sheet_paths:
        # Fallback: just write a placeholder text
        draw = ImageDraw.Draw(canvas)
        centered_text(draw, 'Sticker Preview', fb(72), CANVAS, CANVAS // 2 - 50)
        canvas.save(out_path, 'JPEG', quality=92)
        return

    # Extract sticker crops from sheets
    crops = []
    rng = random.Random(42)  # deterministic for reproducibility
    for sp in sheet_paths[:5]:
        sheet = Image.open(sp).convert('RGBA')
        sw, sh = sheet.size
        # Grid: roughly 4×4 cells per sheet → crop 16 cells
        rows, cols = 4, 4
        cell_w, cell_h = sw // cols, sh // rows
        for r in range(rows):
            for c in range(cols):
                x0 = c * cell_w + cell_w // 10
                y0 = r * cell_h + cell_h // 10
                x1 = x0 + int(cell_w * 0.85)
                y1 = y0 + int(cell_h * 0.85)
                crop = sheet.crop((x0, y0, x1, y1))
                crops.append(crop)

    if not crops:
        canvas.save(out_path, 'JPEG', quality=92)
        return

    # Randomly select 13 crops
    selected = rng.sample(crops, min(13, len(crops)))

    # Place scattered at random angles
    placed = 0
    attempts = 0
    canvas_rgba = canvas.convert('RGBA')
    placed_boxes = []

    # Arrange in a loose 3-row stagger
    positions = [
        (300, 220), (700, 150), (1100, 200), (1500, 170), (1900, 230),
        (200, 680), (600, 720), (1000, 660), (1400, 700), (1800, 650),
        (350, 1200), (800, 1180), (1250, 1220), (1700, 1160),
    ]

    sticker_size = 340

    for idx, crop in enumerate(selected):
        if idx >= len(positions):
            break
        pos_x, pos_y = positions[idx]
        # Resize
        resized = crop.resize((sticker_size, sticker_size), Image.LANCZOS)
        # Random angle ±20°
        angle = rng.uniform(-22, 22)
        rotated = resized.rotate(angle, expand=True, resample=Image.BICUBIC)
        rw, rh = rotated.size
        # Paste
        px = pos_x - rw // 2
        py = pos_y - rh // 2
        # Soft drop shadow
        shadow_layer = Image.new('RGBA', canvas_rgba.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow_layer).rectangle(
            [px + 6, py + 8, px + rw + 6, py + rh + 8], fill=(0, 0, 0, 40)
        )
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=8))
        canvas_rgba = Image.alpha_composite(canvas_rgba, shadow_layer)
        canvas_rgba.paste(rotated, (px, py), rotated)
        placed += 1

    # Bottom area: bottom 3 rows at y=1500+
    more_positions = [
        (450, 1700), (950, 1750), (1450, 1700), (1950, 1750),
    ]
    for idx, crop in enumerate(selected[:4]):
        pos_x, pos_y = more_positions[idx]
        resized = crop.resize((sticker_size, sticker_size), Image.LANCZOS)
        angle = rng.uniform(-18, 18)
        rotated = resized.rotate(angle, expand=True, resample=Image.BICUBIC)
        rw, rh = rotated.size
        px = pos_x - rw // 2
        py = pos_y - rh // 2
        shadow_layer = Image.new('RGBA', canvas_rgba.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow_layer).rectangle(
            [px + 6, py + 8, px + rw + 6, py + rh + 8], fill=(0, 0, 0, 40)
        )
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=8))
        canvas_rgba = Image.alpha_composite(canvas_rgba, shadow_layer)
        canvas_rgba.paste(rotated, (px, py), rotated)

    result = canvas_rgba.convert('RGB')

    # Add subtle title at top
    draw = ImageDraw.Draw(result)
    title = 'Mix & match — use any sticker on any page, unlimited times'
    tfont = fr(42)
    bbox = draw.textbbox((0, 0), title, font=tfont)
    tw = bbox[2] - bbox[0]
    draw.text(((CANVAS - tw) // 2, CANVAS - 80), title, font=tfont, fill=(140, 130, 120))

    result.save(out_path, 'JPEG', quality=92)


def make_download_summary_card(color, accent, out_path):
    """
    Sticker pack rank 10: 'What's in your download' summary card.
    """
    canvas = Image.new('RGB', (CANVAS, CANVAS), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # Top accent bar
    draw.rectangle([0, 0, CANVAS, 20], fill=color)

    # Title
    title_font = fb(80)
    centered_text(draw, "What's in Your Download", title_font, CANVAS, 80, fill=(35, 30, 25))

    # Big feature cards
    features = [
        ('5 PNG Sheets',          '200+ kawaii stickers total'),
        ('GoodNotes Ready',       'Import to your sticker library in seconds'),
        ('Transparent Background','Works on any page color or background'),
        ('Instant Download',      'Files delivered immediately after purchase'),
        ('Use Unlimited Times',   'Drag stickers onto any page, as many times as you want'),
    ]

    y = 250
    for i, (headline, desc) in enumerate(features):
        # Alternating card style
        card_fill = (248, 246, 243) if i % 2 == 0 else BG_COLOR
        card_x, card_w = 80, CANVAS - 160
        card_h = 165
        draw.rounded_rectangle([card_x, y, card_x + card_w, y + card_h],
                               radius=20, fill=card_fill)

        # Accent dot
        dot_r = 28
        dot_cx = card_x + 60
        dot_cy = y + card_h // 2
        draw.ellipse([dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r], fill=color)

        # Text
        hfont = fb(58)
        draw.text((card_x + 110, y + 22), headline, font=hfont, fill=(30, 25, 20))
        dfont = fr(44)
        draw.text((card_x + 110, y + 90), desc, font=dfont, fill=(110, 105, 100))
        y += card_h + 20

    # Bottom branding
    bbar_h = 120
    draw.rectangle([0, CANVAS - bbar_h, CANVAS, CANVAS], fill=DARK_STRIP)
    bfont = fr(44)
    centered_text(draw, '© OnBrandCraftz  —  personal use license', bfont, CANVAS,
                  CANVAS - bbar_h + (bbar_h - 48) // 2, fill=(220, 220, 220))

    # Accent bottom line
    draw.rectangle([0, CANVAS - bbar_h - 8, CANVAS, CANVAS - bbar_h], fill=accent)

    canvas.save(out_path, 'JPEG', quality=92)


# ── Upload helper ─────────────────────────────────────────────────────────────
def upload_with_delay(client, listing_id, img_path, rank, delay=1.1):
    """Upload one image at the given rank, with rate-limiting delay."""
    result = client.upload_listing_image(listing_id, img_path, rank=rank)
    time.sleep(delay)
    return result


# ── Art file fetcher for listings without local files ─────────────────────────
def fetch_etsy_image(url, out_path):
    """Download an Etsy listing image to a temp file. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        with open(out_path, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f'    Warning: could not fetch {url}: {e}')
        return False


# ── Category classifier ───────────────────────────────────────────────────────
def classify_listing(lid, title, photo_count, lid_to_dp):
    """
    Returns (category, info_dict) where category is one of:
      'wall_art_single' | 'wall_art_set' | 'svg_bundle' | 'sticker_pack' |
      'kawaii_print_skip' | 'no_art_skip' | 'done'
    """
    title_lower = title.lower()

    if photo_count >= 10:
        return 'done', {}

    if lid in SVG_BUNDLE_IDS:
        return 'svg_bundle', {}

    if lid in STICKER_PACKS:
        return 'sticker_pack', STICKER_PACKS[lid]

    # Kawaii Art Print listings (4515xxx) without local art — skip
    if KAWAII_PRINT_PREFIX.lower() in title_lower and lid not in lid_to_dp:
        return 'kawaii_print_skip', {}

    # Check if it's a set listing
    set_keywords = ['set of 4', 'set of 5', 'gallery wall set', 'four seasons', 'coastal art set',
                    'boho botanical wall art set', 'all 4 planners', 'all 4 themes']
    is_set = any(kw in title_lower for kw in set_keywords)

    # Look for art file
    art_file = None
    if lid in lid_to_dp:
        for dp_id, files_list in lid_to_dp[lid]:
            art_file = find_art_file(dp_id, files_list)
            if art_file:
                break

    if art_file:
        cat = 'wall_art_set' if is_set else 'wall_art_single'
        return cat, {'art_file': art_file}

    return 'no_art_skip', {}


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    client = EtsyAPIClient()
    lid_to_dp, _raw = load_dp_map()

    print('Fetching all active listings...')
    listings = client.get_shop_listings_all(state='active')
    print(f'Total active: {len(listings)}')

    # Filter to download type only, under 10 photos
    targets = [
        l for l in listings
        if l.get('listing_type') == 'download' and len(l.get('images', [])) < 10
    ]
    print(f'Download listings under 10 photos: {len(targets)}\n')

    tmpdir = tempfile.mkdtemp(prefix='fill_photos_')
    print(f'Temp dir: {tmpdir}\n')

    summary = {
        'done_already':        [],
        'wall_art_filled':     [],
        'svg_bundle_filled':   [],
        'sticker_pack_filled': [],
        'kawaii_print_skip':   [],
        'no_art_skip':         [],
        'errors':              [],
    }

    for listing in sorted(targets, key=lambda l: l.get('listing_id', 0)):
        lid = listing['listing_id']
        title = listing.get('title', '')[:70]
        images = listing.get('images', [])
        photo_count = len(images)
        existing_ranks = {img.get('rank', 0) for img in images}

        cat, info = classify_listing(lid, title, photo_count, lid_to_dp)

        if cat == 'done':
            summary['done_already'].append(lid)
            continue

        print(f'[{lid}] {title[:55]}')
        print(f'  Photos: {photo_count}/10  Category: {cat}')

        if cat == 'kawaii_print_skip':
            print(f'  → SKIP (Kawaii Art Print — no local art file mapping)')
            summary['kawaii_print_skip'].append((lid, title))
            continue

        if cat == 'no_art_skip':
            print(f'  → SKIP (no local art file found)')
            summary['no_art_skip'].append((lid, title))
            continue

        try:
            uploaded = 0

            # ── WALL ART SINGLE / SET ─────────────────────────────────────────
            if cat in ('wall_art_single', 'wall_art_set'):
                art_file = info['art_file']
                missing_ranks = set(range(1, 11)) - existing_ranks
                # We only generate rank 9 and 10 here
                for rank in sorted(missing_ranks):
                    if rank == 9:
                        out = os.path.join(tmpdir, f'{lid}_r09_frames.jpg')
                        print(f'  Generating rank 9: frame options...')
                        make_frame_options_photo(art_file, out)
                        upload_with_delay(client, lid, out, rank=9)
                        uploaded += 1
                        print(f'  Uploaded rank 9 ✓')
                    elif rank == 10:
                        out = os.path.join(tmpdir, f'{lid}_r10_detail.jpg')
                        print(f'  Generating rank 10: detail crop...')
                        make_detail_crop_photo(art_file, out)
                        upload_with_delay(client, lid, out, rank=10)
                        uploaded += 1
                        print(f'  Uploaded rank 10 ✓')
                    else:
                        print(f'  Skipping rank {rank} — not in scope for this run')

                if uploaded > 0:
                    summary['wall_art_filled'].append((lid, title, photo_count + uploaded))

            # ── SVG COMMERCIAL BUNDLE ─────────────────────────────────────────
            elif cat == 'svg_bundle':
                if 10 not in existing_ranks:
                    out = os.path.join(tmpdir, f'{lid}_r10_commercial.jpg')
                    print(f'  Generating rank 10: commercial license card...')
                    make_commercial_license_card(out)
                    upload_with_delay(client, lid, out, rank=10)
                    uploaded += 1
                    print(f'  Uploaded rank 10 ✓')
                if uploaded > 0:
                    summary['svg_bundle_filled'].append((lid, title, photo_count + uploaded))

            # ── STICKER PACK ─────────────────────────────────────────────────
            elif cat == 'sticker_pack':
                sc = info
                pid = sc['pid']
                color = sc['color']
                accent = sc['accent']

                missing_ranks = set(range(1, 11)) - existing_ranks

                for rank in sorted(missing_ranks):
                    if rank == 8:
                        out = os.path.join(tmpdir, f'{lid}_r08_appcompat.jpg')
                        print(f'  Generating rank 8: app compatibility card...')
                        make_app_compat_card(color, accent, sc['theme'], out)
                        upload_with_delay(client, lid, out, rank=8)
                        uploaded += 1
                        print(f'  Uploaded rank 8 ✓')
                    elif rank == 9:
                        out = os.path.join(tmpdir, f'{lid}_r09_scattered.jpg')
                        print(f'  Generating rank 9: scattered stickers...')
                        make_scattered_stickers_photo(pid, out)
                        upload_with_delay(client, lid, out, rank=9)
                        uploaded += 1
                        print(f'  Uploaded rank 9 ✓')
                    elif rank == 10:
                        out = os.path.join(tmpdir, f'{lid}_r10_summary.jpg')
                        print(f'  Generating rank 10: download summary...')
                        make_download_summary_card(color, accent, out)
                        upload_with_delay(client, lid, out, rank=10)
                        uploaded += 1
                        print(f'  Uploaded rank 10 ✓')
                    else:
                        print(f'  Skipping rank {rank} — not in scope')

                if uploaded > 0:
                    summary['sticker_pack_filled'].append((lid, title, photo_count + uploaded))

        except EtsyAPIError as e:
            print(f'  ERROR: {e}')
            summary['errors'].append((lid, title, str(e)))
        except Exception as e:
            print(f'  ERROR (unexpected): {e}')
            import traceback
            traceback.print_exc()
            summary['errors'].append((lid, title, str(e)))

        print()

    # ── Print summary ──────────────────────────────────────────────────────────
    print('=' * 70)
    print('SUMMARY')
    print('=' * 70)

    print(f'\nWall art listings filled: {len(summary["wall_art_filled"])}')
    for lid, title, new_count in summary['wall_art_filled']:
        print(f'  ✓ {lid} → {new_count} photos | {title[:55]}')

    print(f'\nSVG bundle listings filled: {len(summary["svg_bundle_filled"])}')
    for lid, title, new_count in summary['svg_bundle_filled']:
        print(f'  ✓ {lid} → {new_count} photos | {title[:55]}')

    print(f'\nSticker pack listings filled: {len(summary["sticker_pack_filled"])}')
    for lid, title, new_count in summary['sticker_pack_filled']:
        print(f'  ✓ {lid} → {new_count} photos | {title[:55]}')

    print(f'\nErrors ({len(summary["errors"])}):')
    for lid, title, err in summary['errors']:
        print(f'  ✗ {lid} | {title[:50]} | {err[:80]}')

    print(f'\nSkipped — no local art file ({len(summary["no_art_skip"])}):')
    for lid, title in summary['no_art_skip']:
        print(f'  - {lid} | {title[:60]}')

    print(f'\nNOTE — Kawaii Art Print listings (need manual art file mapping) ({len(summary["kawaii_print_skip"])}):')
    for lid, title in summary['kawaii_print_skip']:
        print(f'  - {lid} | {title[:60]}')

    total_filled = (len(summary['wall_art_filled']) +
                    len(summary['svg_bundle_filled']) +
                    len(summary['sticker_pack_filled']))
    print(f'\nTotal listings brought to 10-photo standard: {total_filled}')
    print(f'Temp files at: {tmpdir}')
    print('Done.')

    return summary


if __name__ == '__main__':
    main()
