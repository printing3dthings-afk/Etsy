#!/usr/bin/env python3
"""
Create one new wall art listing end-to-end:
  1. Generate art (gpt-image-1)
  2. Generate 2 AI lifestyle room scenes
  3. Composite art into 3 room templates (living room, kitchen/dining, entryway)
  4. Create size guide graphic
  5. Create What's Included graphic
  6. Show all images (save to listing_images folder)
  7. Optionally create+activate Etsy listing

Usage:
  python tools/create_art_listing_new.py --preview   # generate images only, no Etsy
  python tools/create_art_listing_new.py --post       # generate + post to Etsy
  python tools/create_art_listing_new.py --post --pid DP1039  # use specific product ID
"""

import os, sys, json, base64, urllib.request, urllib.error, time, argparse
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

client = EtsyAPIClient()
shop_id = client.shop_id
OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

# ── Room template frame bounds (confirmed) ────────────────────────────────────
ROOM_BOUNDS = {
    'living_room':    (409, 164, 614, 464),   # L, T, R, B
    'kitchen_dining': (400, 166, 624, 494),
    'entryway':       (430, 147, 593, 365),   # Option C, user confirmed
}

ROOM_TEMPLATES = {
    'living_room':    f'{ART_DIR}/DP1007_room_living_room_natural_wood.jpg',
    'kitchen_dining': f'{ART_DIR}/DP1007_room_kitchen_dining_natural_wood.jpg',
    'entryway':       f'{ART_DIR}/DP1007_room_entryway_natural_wood.jpg',
}

auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key": f"{client.client_id}:{client.client_secret}",
}

def refresh():
    if client.refresh_access_token():
        auth_headers["Authorization"] = f"Bearer {client.access_token}"
        print("  Token refreshed.")


# ── Image generation ──────────────────────────────────────────────────────────

def gen_image(prompt, out_path, size="1024x1536", quality="high"):
    """Generate an image via gpt-image-1 and save to out_path."""
    payload = json.dumps({
        "model": "gpt-image-1", "prompt": prompt.strip(), "n": 1,
        "size": size, "quality": quality, "output_format": "jpeg"
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
            print(f"  Generated: {os.path.basename(out_path)} ({len(img_bytes)//1024}KB)")
            return True
        except Exception as e:
            if attempt < 2:
                print(f"  Retry {attempt+1}: {e}")
                time.sleep(20)
            else:
                print(f"  ERROR: {e}")
                return False


# ── Compositing ───────────────────────────────────────────────────────────────

def paste_fill(bg_img, art_path, l, t, r, b):
    """Fill the frame opening [l,t,r,b] with art, cropped to fill exactly."""
    art = Image.open(art_path).convert('RGB')
    fw, fh = r - l, b - t
    aw, ah = art.size
    # Fit to fill (cover mode)
    if (aw / ah) < (fw / fh):
        sw, sh = fw, int(fw * ah / aw)
        res = art.resize((sw, sh), Image.LANCZOS)
        cy = (sh - fh) // 2
        crop = res.crop((0, cy, sw, cy + fh))
    else:
        sh, sw = fh, int(fh * aw / ah)
        res = art.resize((sw, sh), Image.LANCZOS)
        cx = (sw - fw) // 2
        crop = res.crop((cx, 0, cx + fw, sh))
    # Slight darkening so art reads as lit from room lighting
    crop = ImageEnhance.Brightness(crop).enhance(0.92)
    bg_img.paste(crop, (l, t))
    return bg_img


def create_room_composite(art_path, room_key, out_path):
    """Composite art into a room template using confirmed frame bounds."""
    l, t, r, b = ROOM_BOUNDS[room_key]
    bg = Image.open(ROOM_TEMPLATES[room_key]).convert('RGB')
    bg = paste_fill(bg, art_path, l, t, r, b)
    bg.save(out_path, 'JPEG', quality=93)
    print(f"  Composite ({room_key}): {os.path.basename(out_path)}")


def composite_into_ai_room(bg_path, art_path, out_path, frame_color=(139, 110, 80),
                            art_pct=0.25, top_pct=0.06):
    """Composite real art into an AI-generated empty-wall room background.

    Places a realistically framed version of the art centered horizontally,
    positioned in the upper (empty wall) portion of the room scene.
    """
    CANVAS = 1024
    room = Image.open(bg_path).convert('RGB').resize((CANVAS, CANVAS), Image.LANCZOS)
    art = Image.open(art_path).convert('RGB')

    art_w = int(CANVAS * art_pct)
    art_h = int(art_w * art.height / art.width)
    art_resized = art.resize((art_w, art_h), Image.LANCZOS)

    mat_w, frame_w = 30, 14
    full_w = art_w + 2 * mat_w + 2 * frame_w
    full_h = art_h + 2 * mat_w + 2 * frame_w

    px = (CANVAS - full_w) // 2
    py = int(CANVAS * top_pct)

    # Ambient occlusion / wall darkening behind frame
    ao = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    for pad in range(40, 0, -4):
        alpha = int(40 * (1 - (pad / 40) ** 1.5))
        ImageDraw.Draw(ao).rectangle(
            [px-pad, py-pad, px+full_w+pad, py+full_h+pad], fill=(0, 0, 0, alpha))
    ao = ao.filter(ImageFilter.GaussianBlur(radius=22))
    room = Image.alpha_composite(room.convert('RGBA'), ao).convert('RGB')

    # Drop shadow
    shadow = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle(
        [px+10, py+14, px+full_w+10, py+full_h+14], fill=(0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))
    room = Image.alpha_composite(room.convert('RGBA'), shadow).convert('RGB')

    draw = ImageDraw.Draw(room)

    # Frame with bevel highlights
    draw.rectangle([px, py, px+full_w, py+full_h], fill=frame_color)
    fc_hi = tuple(min(255, c + 45) for c in frame_color)
    fc_sh = tuple(max(0, c - 45) for c in frame_color)
    bv = 4
    draw.polygon([px, py, px+full_w, py, px+full_w-bv, py+bv, px+bv, py+bv], fill=fc_hi)
    draw.polygon([px, py, px, py+full_h, px+bv, py+full_h-bv, px+bv, py+bv], fill=fc_hi)
    draw.polygon([px+full_w, py, px+full_w, py+full_h, px+full_w-bv, py+full_h-bv,
                  px+full_w-bv, py+bv], fill=fc_sh)
    draw.polygon([px, py+full_h, px+full_w, py+full_h, px+full_w-bv, py+full_h-bv,
                  px+bv, py+full_h-bv], fill=fc_sh)

    # White mat
    mx, my = px + frame_w, py + frame_w
    draw.rectangle([mx, my, mx + art_w + 2*mat_w, my + art_h + 2*mat_w], fill=(253, 251, 248))

    # Inner shadow on mat edge
    inner = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    art_x, art_y = mx + mat_w, my + mat_w
    ImageDraw.Draw(inner).rectangle(
        [art_x-3, art_y-3, art_x+art_w+3, art_y+art_h+3], fill=(0, 0, 0, 30))
    inner = inner.filter(ImageFilter.GaussianBlur(radius=6))
    room = Image.alpha_composite(room.convert('RGBA'), inner).convert('RGB')

    # Paste actual art (slightly dimmed for realism)
    art_final = ImageEnhance.Brightness(art_resized).enhance(0.93)
    room.paste(art_final, (art_x, art_y))

    room.save(out_path, 'JPEG', quality=93)
    print(f"  Composite (AI room): {os.path.basename(out_path)}")


def create_size_guide(art_path, out_path):
    """Simple 3-size guide: show art at 3 scale sizes on a neutral background."""
    canvas_size = 1200
    bg_color = (245, 243, 239)   # warm off-white
    frame_color = (139, 110, 80)  # warm natural wood
    mat_color = (252, 250, 247)
    text_color = (60, 55, 50)

    canvas = Image.new('RGB', (canvas_size, canvas_size), bg_color)
    art = Image.open(art_path).convert('RGB')
    draw = ImageDraw.Draw(canvas)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    except Exception:
        font = font_sm = font_title = ImageFont.load_default()

    # Title
    draw.text((canvas_size//2, 38), "AVAILABLE PRINT SIZES", font=font_title,
              fill=text_color, anchor="mm")
    draw.text((canvas_size//2, 68), "Download includes all sizes — print at home or at any print shop",
              font=font_sm, fill=(120, 110, 100), anchor="mm")

    # 3 sizes: 8x10, 16x20, 24x30 (scaled to show relative proportions)
    sizes = [
        ("8\" × 10\"", 0.14),
        ("16\" × 20\"", 0.22),
        ("24\" × 30\"", 0.30),
    ]
    aw, ah = art.size
    aspect = ah / aw

    x_positions = [200, 600, 1000]
    y_top = 110

    for (label, scale), cx in zip(sizes, x_positions):
        w = int(canvas_size * scale)
        h = int(w * aspect)
        mat_pad = 12
        frame_pad = 7
        total_w = w + 2*mat_pad + 2*frame_pad
        total_h = h + 2*mat_pad + 2*frame_pad

        px = cx - total_w // 2
        py = y_top

        # Drop shadow
        shadow = Image.new('RGBA', (canvas_size, canvas_size), (0,0,0,0))
        ImageDraw.Draw(shadow).rectangle(
            [px+8, py+10, px+total_w+8, py+total_h+10], fill=(0,0,0,55))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        canvas = Image.alpha_composite(canvas.convert('RGBA'), shadow).convert('RGB')
        draw = ImageDraw.Draw(canvas)

        # Frame
        draw.rectangle([px, py, px+total_w, py+total_h], fill=frame_color)
        # Mat
        mx, my = px+frame_pad, py+frame_pad
        draw.rectangle([mx, my, mx+w+2*mat_pad, my+h+2*mat_pad], fill=mat_color)
        # Art
        art_resized = art.resize((w, h), Image.LANCZOS)
        canvas.paste(art_resized, (mx+mat_pad, my+mat_pad))
        draw = ImageDraw.Draw(canvas)

        # Label below
        label_y = py + total_h + 18
        draw.text((cx, label_y), label, font=font, fill=text_color, anchor="mm")

    # Footer note
    draw.text((canvas_size//2, canvas_size - 35),
              "All sizes included in your download • 300 DPI • Print-ready JPG files",
              font=font_sm, fill=(120, 110, 100), anchor="mm")

    canvas.save(out_path, 'JPEG', quality=92)
    print(f"  Size guide: {os.path.basename(out_path)}")


def create_whats_included(art_path, out_path, product_title, price):
    """What's Included infographic card."""
    W, H = 1200, 1200
    bg_color = (250, 248, 244)
    accent = (139, 110, 80)
    dark = (45, 38, 32)
    mid = (100, 88, 75)

    canvas = Image.new('RGB', (W, H), bg_color)
    draw = ImageDraw.Draw(canvas)

    try:
        font_h1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
        font_h2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 23)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 19)
        font_price = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
    except Exception:
        font_h1 = font_h2 = font_body = font_sm = font_price = ImageFont.load_default()

    # Art preview (left side, portrait)
    art = Image.open(art_path).convert('RGB')
    preview_w = 380
    preview_h = int(preview_w * art.height / art.width)
    if preview_h > 700:
        preview_h = 700
        preview_w = int(preview_h * art.width / art.height)
    art_small = art.resize((preview_w, preview_h), Image.LANCZOS)

    # Frame around art preview
    mat_pad = 16
    frame_pad = 8
    frame_color = (139, 110, 80)
    mat_color = (252, 250, 247)
    fx = 60
    fy = (H - (preview_h + 2*mat_pad + 2*frame_pad)) // 2
    fw = preview_w + 2*mat_pad + 2*frame_pad
    fh = preview_h + 2*mat_pad + 2*frame_pad

    shadow = Image.new('RGBA', (W, H), (0,0,0,0))
    ImageDraw.Draw(shadow).rectangle([fx+10, fy+12, fx+fw+10, fy+fh+12], fill=(0,0,0,60))
    shadow = shadow.filter(ImageFilter.GaussianBlur(15))
    canvas = Image.alpha_composite(canvas.convert('RGBA'), shadow).convert('RGB')
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([fx, fy, fx+fw, fy+fh], fill=frame_color)
    draw.rectangle([fx+frame_pad, fy+frame_pad, fx+frame_pad+preview_w+2*mat_pad,
                    fy+frame_pad+preview_h+2*mat_pad], fill=mat_color)
    canvas.paste(art_small, (fx+frame_pad+mat_pad, fy+frame_pad+mat_pad))
    draw = ImageDraw.Draw(canvas)

    # Right side — content
    rx = fx + fw + 55
    ry = 80

    # Title
    draw.text((rx, ry), "INSTANT DOWNLOAD", font=font_h1, fill=accent)
    ry += 58

    # Divider
    draw.rectangle([rx, ry, W-50, ry+2], fill=accent)
    ry += 20

    # Price
    draw.text((rx, ry), f"${price:.2f}", font=font_price, fill=dark)
    ry += 80

    # What's included header
    draw.text((rx, ry), "WHAT'S INCLUDED:", font=font_h2, fill=dark)
    ry += 42

    items = [
        "✓  High-res JPG files (300 DPI)",
        "✓  8 print sizes: 4×6 up to 24×36",
        "✓  Instant download after purchase",
        "✓  No waiting — no shipping",
        "✓  Print at home or any print shop",
        "✓  Personal use license included",
    ]
    for item in items:
        draw.text((rx, ry), item, font=font_body, fill=mid)
        ry += 38
    ry += 10

    # Divider
    draw.rectangle([rx, ry, W-50, ry+2], fill=(210, 200, 188))
    ry += 22

    # Sizes line
    draw.text((rx, ry), "SIZES: 4×6 · 5×7 · 8×10 · 11×14 · 16×20 · 18×24 · 24×30 · 24×36\"",
              font=font_sm, fill=mid)
    ry += 38

    draw.text((rx, ry), "FORMAT: JPG • RESOLUTION: 300 DPI • COLOR: sRGB",
              font=font_sm, fill=mid)
    ry += 38

    draw.text((rx, ry), "© OnBrandCraftz  |  Personal use only",
              font=font_sm, fill=(160, 148, 135))

    canvas.save(out_path, 'JPEG', quality=92)
    print(f"  What's Included: {os.path.basename(out_path)}")


# ── Etsy API helpers ──────────────────────────────────────────────────────────

def create_listing(listing_data):
    url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings"
    payload = json.dumps(listing_data).encode()
    req = urllib.request.Request(url, data=payload,
                                  headers={**auth_headers, "Content-Type": "application/json"},
                                  method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            print(f"  CREATE {e.code}: {body}")
            if e.code == 401: refresh()
            elif e.code == 429: time.sleep(15)
            elif attempt == 2: return None
            else: time.sleep(3)
    return None


def update_listing(listing_id, updates):
    url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}"
    payload = json.dumps(updates).encode()
    req = urllib.request.Request(url, data=payload,
                                  headers={**auth_headers, "Content-Type": "application/json"},
                                  method="PATCH")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            if e.code == 401: refresh()
            elif e.code == 429: time.sleep(15)
            elif e.code == 400: print(f"  UPDATE 400: {body}"); return None
            else:
                if attempt == 2: return None
                time.sleep(3)
    return None


def upload_image(listing_id, img_path, rank):
    """Upload one image, removing any rank collision first."""
    # Get current images
    url_imgs = f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images"
    req_get = urllib.request.Request(url_imgs, headers=auth_headers)
    try:
        with urllib.request.urlopen(req_get, timeout=15) as resp:
            existing = {img['rank']: img['listing_image_id']
                        for img in json.loads(resp.read()).get('results', [])}
    except Exception:
        existing = {}

    # Delete any existing image at this rank
    if rank in existing:
        old_id = existing[rank]
        url_del = (f"https://openapi.etsy.com/v3/application/shops/{shop_id}"
                   f"/listings/{listing_id}/images/{old_id}")
        try:
            req_del = urllib.request.Request(url_del, headers=auth_headers, method="DELETE")
            with urllib.request.urlopen(req_del, timeout=15):
                pass
            time.sleep(0.3)
        except Exception as e:
            print(f"  WARNING: could not delete old rank {rank}: {e}")

    for attempt in range(3):
        try:
            result = client.upload_listing_image(listing_id, img_path, rank=rank)
            print(f"  Uploaded rank={rank} id={result.get('listing_image_id')}")
            return True
        except EtsyAPIError as e:
            if e.status == 401: refresh()
            elif e.status == 429: time.sleep(15)
            elif e.status == 500 and attempt < 2: time.sleep(5)
            else: print(f"  Upload rank={rank} failed: {e}"); return False
    return False


def upload_file(listing_id, file_path):
    for attempt in range(3):
        try:
            result = client.upload_listing_file(listing_id, file_path, rank=1)
            print(f"  File uploaded id={result.get('listing_file_id')}")
            return True
        except EtsyAPIError as e:
            if e.status == 401: refresh()
            elif e.status == 429: time.sleep(15)
            else: print(f"  File upload failed: {e}"); return False
    return False


def get_or_create_section(title):
    return client.get_or_create_section(title)


# ── LISTING DEFINITION ────────────────────────────────────────────────────────

LISTING = {
    'product_id': 'DP1038',
    'sku': 'OBC-WA-038',
    'title': 'Autumn Fox Watercolor Print | Woodland Fox Art | Fall Decor Wall Art | Instant Download | Rustic Cabin Printable Art',
    'price': 5.99,
    'section': 'Landscape and Nature Art',
    'tags': [
        'fox wall art',
        'autumn fox print',
        'woodland art print',
        'watercolor fox',
        'fall wall decor',
        'printable wall art',
        'instant download',
        'digital download',
        'rustic cabin art',
        'nature animal art',
        'cottagecore art',
        'fox home decor',
        'wildlife art print',
    ],
    'art_prompt': (
        "Beautiful watercolor painting of a red fox in an autumn woodland, portrait orientation. "
        "A majestic red fox sits alert and dignified among fallen golden and copper autumn leaves, "
        "surrounded by misty birch tree trunks with pale silver bark. The fox's vibrant rust-orange "
        "and white fur is rendered with luminous transparent watercolor washes — rich sienna, burnt "
        "orange, ivory, and deep chestnut. The birch trees and forest floor are painted in warm "
        "autumn palette: golden yellow, amber, copper, and sage green. Soft misty morning atmosphere "
        "with diffused light filtering through the tree canopy, casting subtle dappled shadows. "
        "Authentic watercolor technique: wet-on-wet washes, soft bleeding edges, paper grain visible, "
        "transparent layered glazes, preserved white highlights on the fox's muzzle and chest. "
        "The composition is intimate and serene. Wide cream/ivory border margins. "
        "Museum-quality botanical wildlife watercolor. No text."
    ),
    'art_size': '1024x1536',
    'frame_color': (139, 110, 80),   # warm natural wood

    # Scene A bg: wide room shot with EMPTY wall — real art composited in after
    'scene_a_prompt': (
        "Interior design product photography, square format. "
        "A warm rustic living room with cream linen walls and honey-toned oak flooring. "
        "CRITICAL LAYOUT: The TOP 65% of the image is a completely bare, smooth cream wall — "
        "no art, no shelves, no frames, no objects of any kind on the upper wall. "
        "ONLY the BOTTOM 35% contains furniture: a cream linen sofa with rust and warm gold throw pillows, "
        "a tall rattan floor lamp to the right, a terracotta clay pot with dried amber branches to the left. "
        "The upper wall must be clean and empty to allow digital art placement. "
        "Warm golden afternoon window light from the left. Organic modern, cottagecore home. "
        "35mm, f/2.8, photorealistic. No text."
    ),
    # Scene B bg: styled vignette with EMPTY wall — real art composited in after
    'scene_b_prompt': (
        "Interior design product photography, square format. "
        "A cozy rustic cabin reading nook with warm sage green walls and warm wood accents. "
        "CRITICAL LAYOUT: The TOP 65% of the image is a completely bare, smooth sage green wall — "
        "no art, no shelves, no frames, no objects of any kind on the upper wall. "
        "ONLY the BOTTOM 35% contains decor: a slim natural oak floating shelf holding a stack of "
        "hardcover books, a small ceramic fox figurine, a glowing pillar candle, and dried wildflowers. "
        "Below the shelf a soft armchair is partially visible at the very bottom edge. "
        "The upper wall must be completely empty for digital art placement. "
        "Warm lamp glow and soft natural light. Cottagecore reading retreat. "
        "50mm, photorealistic. No text."
    ),

    'description': """🦊 Bring the magic of autumn into your home — this luminous watercolor fox print captures a majestic red fox at rest among golden birch trees and copper autumn leaves, painted in rich, transparent watercolor washes that glow from within.

Perfect for nature lovers, cabin homes, and anyone who finds beauty in the quiet moments of the forest.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT YOU GET
━━━━━━━━━━━━━━━━━━━━━━━━
• Instant digital download — no waiting, no shipping
• High-resolution JPG files (300 DPI, print-ready)
• 8 sizes included: 4×6, 5×7, 8×10, 11×14, 16×20, 18×24, 24×30, 24×36
• Print at home or send to a print shop (Costco, Walgreens, Staples, any local lab)

━━━━━━━━━━━━━━━━━━━━━━━━
🏠 PERFECT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Living room, bedroom, or cabin with rustic or nature decor
• Cozy reading nook, study, or home office
• Cottagecore, woodland, or farmhouse-inspired interiors
• Nursery or children's bedroom with woodland theme
• Housewarming, birthday, or holiday gift for nature lovers

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase and download your files instantly from Etsy
2. Choose your preferred size (8 sizes included)
3. Print at home, at Costco, Walgreens, Staples, or your local print shop
4. Frame it and hang — that's it!

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 PRINTING TIPS
━━━━━━━━━━━━━━━━━━━━━━━━
• Matte or satin paper is ideal — it preserves the soft watercolor texture beautifully
• Natural wood, rustic wood, or warm gold frame complements the autumn palette perfectly
• 11×14 or 16×20 shows the fox detail at its best
• For the most beautiful watercolor quality: print on matte photo paper or fine art paper at a local photo lab

━━━━━━━━━━━━━━━━━━━━━━━━
📄 FILE DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: High-resolution JPG
• Resolution: 300 DPI (professional print quality)
• Sizes: 4×6, 5×7, 8×10, 11×14, 16×20, 18×24, 24×30, 24×36 inches
• Color profile: sRGB

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this a physical item?
A: No — this is a digital download only. You receive image files to print yourself.

Q: Can I resize the files?
A: Yes! 300 DPI files scale beautifully. Resize in Canva, Photoshop, or any image editor.

Q: Can I print multiple copies?
A: Yes — for personal use in your own home, print as many copies as you like.

Q: What paper should I use?
A: Matte or satin paper is ideal for watercolor art — it captures the soft texture without glare.

Q: Can I use this for commercial purposes?
A: This license covers personal use only. Contact us for commercial licensing.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use."""
}


# ── Main run function ─────────────────────────────────────────────────────────

def run(post_to_etsy=False, pid_override=None):
    info = LISTING.copy()
    if pid_override:
        info['product_id'] = pid_override

    pid = info['product_id']
    out_dir = os.path.join(ART_DIR, f'{pid}_listing_images')
    os.makedirs(out_dir, exist_ok=True)
    art_path = os.path.join(ART_DIR, f'{pid}.jpg')

    print(f"\n{'='*60}")
    print(f"Creating listing: {pid}")
    print(f"Title: {info['title'][:70]}...")
    print(f"Output: {out_dir}")
    print(f"{'='*60}")

    # ── Step 1: Generate art ──────────────────────────────────────────────────
    print(f"\n[1/7] Generating art...")
    if not os.path.exists(art_path):
        ok = gen_image(info['art_prompt'], art_path, size=info['art_size'], quality="high")
        if not ok:
            print("  FAILED to generate art. Aborting.")
            return None
        time.sleep(3)
    else:
        print(f"  Art already exists: {art_path}")

    # ── Step 2: AI lifestyle scene A (empty wall bg + composite real art) ────
    print(f"\n[2/7] Generating lifestyle scene A...")
    bg_a = os.path.join(out_dir, 'bg_lifestyle_scene_A.jpg')
    scene_a = os.path.join(out_dir, 'lifestyle_scene_A.jpg')
    if not os.path.exists(bg_a):
        ok = gen_image(info['scene_a_prompt'], bg_a, size="1024x1024", quality="high")
        if not ok:
            print("  WARNING: scene A background failed")
        time.sleep(3)
    else:
        print(f"  Scene A background exists.")
    if os.path.exists(bg_a):
        composite_into_ai_room(bg_a, art_path, scene_a,
                               frame_color=info.get('frame_color', (139, 110, 80)))
    else:
        print(f"  WARNING: scene A missing — skipping composite")

    # ── Step 3: AI lifestyle scene B (empty wall bg + composite real art) ────
    print(f"\n[3/7] Generating lifestyle scene B...")
    bg_b = os.path.join(out_dir, 'bg_lifestyle_scene_B.jpg')
    scene_b = os.path.join(out_dir, 'lifestyle_scene_B.jpg')
    if not os.path.exists(bg_b):
        ok = gen_image(info['scene_b_prompt'], bg_b, size="1024x1024", quality="high")
        if not ok:
            print("  WARNING: scene B background failed")
        time.sleep(3)
    else:
        print(f"  Scene B background exists.")
    if os.path.exists(bg_b):
        composite_into_ai_room(bg_b, art_path, scene_b,
                               frame_color=info.get('frame_color', (139, 110, 80)))
    else:
        print(f"  WARNING: scene B missing — skipping composite")

    # ── Step 4: Room composites ───────────────────────────────────────────────
    print(f"\n[4/7] Creating room composites...")
    room_outputs = {}
    for room_key in ['living_room', 'kitchen_dining', 'entryway']:
        out = os.path.join(out_dir, f'room_{room_key}.jpg')
        create_room_composite(art_path, room_key, out)
        room_outputs[room_key] = out

    # ── Step 5: Size guide ────────────────────────────────────────────────────
    print(f"\n[5/7] Creating size guide...")
    size_guide_path = os.path.join(out_dir, 'size_guide.jpg')
    create_size_guide(art_path, size_guide_path)

    # ── Step 6: What's Included card ──────────────────────────────────────────
    print(f"\n[6/7] Creating What's Included card...")
    whats_included_path = os.path.join(out_dir, 'whats_included.jpg')
    create_whats_included(art_path, whats_included_path, info['title'].split('|')[0].strip(), info['price'])

    # ── Summary of generated files ────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"Generated files in {out_dir}:")
    all_photos = [
        ('1 - Lifestyle Scene A (hero)', scene_a),
        ('2 - Lifestyle Scene B', scene_b),
        ('3 - Room: Living Room', room_outputs.get('living_room', '')),
        ('4 - Room: Kitchen/Dining', room_outputs.get('kitchen_dining', '')),
        ('5 - Room: Entryway', room_outputs.get('entryway', '')),
        ('6 - Size Guide', size_guide_path),
        ('7 - What\'s Included', whats_included_path),
        ('8 - Raw Art File', art_path),
    ]
    for label, path in all_photos:
        exists = '✓' if os.path.exists(path) else '✗ MISSING'
        size_kb = os.path.getsize(path)//1024 if os.path.exists(path) else 0
        print(f"  {exists} {label}: {os.path.basename(path)} ({size_kb}KB)")

    if not post_to_etsy:
        print(f"\n[PREVIEW MODE] Images saved. Review them, then run with --post to create the Etsy listing.")
        return {'product_id': pid, 'out_dir': out_dir, 'art_path': art_path, 'photos': all_photos}

    # ── Step 7: Post to Etsy ──────────────────────────────────────────────────
    print(f"\n[7/7] Creating Etsy listing...")
    refresh()

    section_id = get_or_create_section(info['section'])
    print(f"  Section '{info['section']}': ID={section_id}")

    listing_body = {
        "quantity": 999,
        "title": info['title'],
        "description": info['description'],
        "price": info['price'],
        "who_made": "i_did",
        "taxonomy_id": 2078,
        "when_made": "made_to_order",
        "type": "download",
        "state": "draft",
        "tags": info['tags'],
        "shop_section_id": section_id,
        "skus": [info['sku']],
        "is_supply": False,
        "is_customizable": False,
        "should_auto_renew": True,
    }

    listing = create_listing(listing_body)
    if not listing or not listing.get('listing_id'):
        print("  FAILED to create listing")
        return None

    lid = listing['listing_id']
    print(f"  Created listing_id={lid}")
    time.sleep(1)

    # Upload images in order
    # Rank 1 = hero (scene A), 2 = scene B, 3 = living room, 4 = kitchen,
    # 5 = entryway, 6 = size guide, 7 = what's included, 8 = raw art
    image_uploads = [
        (scene_a, 1),
        (scene_b, 2),
        (room_outputs['living_room'], 3),
        (room_outputs['kitchen_dining'], 4),
        (room_outputs['entryway'], 5),
        (size_guide_path, 6),
        (whats_included_path, 7),
        (art_path, 8),
    ]
    uploaded = 0
    for img_path, rank in image_uploads:
        if os.path.exists(img_path):
            if upload_image(lid, img_path, rank):
                uploaded += 1
            time.sleep(0.8)
        else:
            print(f"  SKIP rank={rank}: file missing")

    print(f"  Uploaded {uploaded}/{len(image_uploads)} images")
    time.sleep(1)

    # Upload the art file as digital download
    print(f"  Uploading digital download file...")
    upload_file(lid, art_path)
    time.sleep(1)

    # Activate
    print(f"  Activating listing...")
    activated = update_listing(lid, {"state": "active"})
    if activated and activated.get('state') == 'active':
        print(f"  ✓ LIVE: https://www.etsy.com/listing/{lid}/")
    else:
        print(f"  WARNING: activation may have failed — check Etsy dashboard")

    # Save listing data to shop_data.json for tracking
    try:
        import json as _json
        shop_data_path = '/home/user/Etsy/data/shop_data.json'
        with open(shop_data_path) as f:
            shop_data = _json.load(f)
        shop_data.setdefault('listings', []).append({
            'id': str(lid),
            'title': info['title'],
            'price': info['price'],
            'type': 'wall_art',
            'listing_type': 'download',
            'state': 'active',
            'tags': info['tags'],
            'taxonomy_id': 2078,
            'images': [],
            'url': f'https://www.etsy.com/listing/{lid}/',
            'views': 0,
            'quantity': 999,
            'description': info['description'],
        })
        with open(shop_data_path, 'w') as f:
            _json.dump(shop_data, f, indent=2)
        print(f"  Saved to shop_data.json")
    except Exception as e:
        print(f"  WARNING: could not update shop_data.json: {e}")

    return {'product_id': pid, 'listing_id': lid, 'uploaded': uploaded, 'out_dir': out_dir}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', action='store_true',
                        help='Generate images only — do not post to Etsy')
    parser.add_argument('--post', action='store_true',
                        help='Generate images AND create/activate Etsy listing')
    parser.add_argument('--regen-scenes', action='store_true',
                        help='Regenerate only lifestyle scenes A and B (re-composite with real art)')
    parser.add_argument('--pid', default=None,
                        help='Override product ID (default: DP1038)')
    args = parser.parse_args()

    if not args.preview and not args.post and not args.regen_scenes:
        parser.print_help()
        sys.exit(1)

    if args.regen_scenes:
        # Just redo the two lifestyle scenes for the product
        info = LISTING.copy()
        if args.pid:
            info['product_id'] = args.pid
        pid = info['product_id']
        out_dir = os.path.join(ART_DIR, f'{pid}_listing_images')
        art_path = os.path.join(ART_DIR, f'{pid}.jpg')
        os.makedirs(out_dir, exist_ok=True)

        print(f"Regenerating lifestyle scenes for {pid}...")
        for label, bg_name, scene_name in [
            ('A', 'bg_lifestyle_scene_A.jpg', 'lifestyle_scene_A.jpg'),
            ('B', 'bg_lifestyle_scene_B.jpg', 'lifestyle_scene_B.jpg'),
        ]:
            prompt_key = f'scene_{label.lower()}_prompt'
            bg_path = os.path.join(out_dir, bg_name)
            scene_path = os.path.join(out_dir, scene_name)
            # Delete old bg to force regeneration
            if os.path.exists(bg_path):
                os.remove(bg_path)
                print(f"  Deleted old {bg_name}")
            prompt = info[prompt_key]
            print(f"  Generating scene {label} background...")
            ok = gen_image(prompt, bg_path, size="1024x1024", quality="high")
            if ok and os.path.exists(art_path):
                composite_into_ai_room(bg_path, art_path, scene_path,
                                       frame_color=info.get('frame_color', (139, 110, 80)))
                print(f"  ✓ {scene_name}")
            else:
                print(f"  FAILED scene {label}")
            time.sleep(3)
        print("Done.")
        sys.exit(0)

    result = run(post_to_etsy=args.post, pid_override=args.pid)
    if result:
        print(f"\nDone. Product ID: {result['product_id']}")
        print(f"Images in: {result['out_dir']}")
        if 'listing_id' in result:
            print(f"Etsy listing: https://www.etsy.com/listing/{result['listing_id']}/")
