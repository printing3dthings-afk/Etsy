#!/usr/bin/env python3
"""
Batch create and post wall art listings DP1039–DP1047.

Usage:
  python tools/create_art_listings_9.py                   # all listings
  python tools/create_art_listings_9.py --pids DP1039     # specific listings
  python tools/create_art_listings_9.py --preview         # images only, no Etsy
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
from tools.lifestyle_composite import composite_smart, scene_prompt as _scene_prompt
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

client = EtsyAPIClient()
shop_id = client.shop_id
OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

ROOM_BOUNDS = {
    'living_room':    (409, 164, 614, 464),
    'kitchen_dining': (400, 166, 624, 494),
    'entryway':       (430, 147, 593, 365),
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
    art = Image.open(art_path).convert('RGB')
    fw, fh = r - l, b - t
    aw, ah = art.size
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
    crop = ImageEnhance.Brightness(crop).enhance(0.92)
    bg_img.paste(crop, (l, t))
    return bg_img


def create_room_composite(art_path, room_key, out_path):
    l, t, r, b = ROOM_BOUNDS[room_key]
    bg = Image.open(ROOM_TEMPLATES[room_key]).convert('RGB')
    bg = paste_fill(bg, art_path, l, t, r, b)
    bg.save(out_path, 'JPEG', quality=93)
    print(f"  Room ({room_key}): {os.path.basename(out_path)}")


def composite_into_ai_room(bg_path, art_path, out_path, frame_color=(139, 110, 80),
                            art_pct=0.25, top_pct=0.06):
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

    # Ambient occlusion behind frame
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

    # Frame with bevel
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

    # Inner shadow
    inner = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    art_x, art_y = mx + mat_w, my + mat_w
    ImageDraw.Draw(inner).rectangle(
        [art_x-3, art_y-3, art_x+art_w+3, art_y+art_h+3], fill=(0, 0, 0, 30))
    inner = inner.filter(ImageFilter.GaussianBlur(radius=6))
    room = Image.alpha_composite(room.convert('RGBA'), inner).convert('RGB')

    art_final = ImageEnhance.Brightness(art_resized).enhance(0.93)
    room.paste(art_final, (art_x, art_y))

    room.save(out_path, 'JPEG', quality=93)
    print(f"  Lifestyle composite: {os.path.basename(out_path)}")


def create_size_guide(art_path, out_path):
    canvas_size = 1200
    bg_color = (245, 243, 239)
    frame_color = (139, 110, 80)
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

    draw.text((canvas_size//2, 38), "AVAILABLE PRINT SIZES", font=font_title,
              fill=text_color, anchor="mm")
    draw.text((canvas_size//2, 68), "Download includes all sizes — print at home or at any print shop",
              font=font_sm, fill=(120, 110, 100), anchor="mm")

    sizes = [("8\" × 10\"", 0.14), ("16\" × 20\"", 0.22), ("24\" × 30\"", 0.30)]
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

        shadow = Image.new('RGBA', (canvas_size, canvas_size), (0,0,0,0))
        ImageDraw.Draw(shadow).rectangle(
            [px+8, py+10, px+total_w+8, py+total_h+10], fill=(0,0,0,55))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        canvas = Image.alpha_composite(canvas.convert('RGBA'), shadow).convert('RGB')
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([px, py, px+total_w, py+total_h], fill=frame_color)
        draw.rectangle([px+frame_pad, py+frame_pad,
                        px+frame_pad+w+2*mat_pad, py+frame_pad+h+2*mat_pad], fill=mat_color)
        art_resized = art.resize((w, h), Image.LANCZOS)
        canvas.paste(art_resized, (px+frame_pad+mat_pad, py+frame_pad+mat_pad))
        draw = ImageDraw.Draw(canvas)
        draw.text((cx, py + total_h + 18), label, font=font, fill=text_color, anchor="mm")

    draw.text((canvas_size//2, canvas_size - 35),
              "All sizes included in your download • 300 DPI • Print-ready JPG files",
              font=font_sm, fill=(120, 110, 100), anchor="mm")

    canvas.save(out_path, 'JPEG', quality=92)
    print(f"  Size guide: {os.path.basename(out_path)}")


def create_whats_included(art_path, out_path, title_text, price):
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

    art = Image.open(art_path).convert('RGB')
    preview_w = 380
    preview_h = int(preview_w * art.height / art.width)
    if preview_h > 700:
        preview_h = 700
        preview_w = int(preview_h * art.width / art.height)
    art_small = art.resize((preview_w, preview_h), Image.LANCZOS)

    mat_pad, frame_pad = 16, 8
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

    rx, ry = fx + fw + 55, 80
    draw.text((rx, ry), "INSTANT DOWNLOAD", font=font_h1, fill=accent)
    ry += 58
    draw.rectangle([rx, ry, W-50, ry+2], fill=accent)
    ry += 20
    draw.text((rx, ry), f"${price:.2f}", font=font_price, fill=dark)
    ry += 80
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
    draw.rectangle([rx, ry, W-50, ry+2], fill=(210, 200, 188))
    ry += 22
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


# ── Etsy helpers ──────────────────────────────────────────────────────────────

def create_listing(data):
    url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings"
    payload = json.dumps(data).encode()
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


def activate_listing(listing_id):
    url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}"
    payload = json.dumps({"state": "active"}).encode()
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
            elif e.code == 400: print(f"  ACTIVATE 400: {body}"); return None
            else:
                if attempt == 2: return None
                time.sleep(3)
    return None


def upload_image(listing_id, img_path, rank):
    url_imgs = f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images"
    req_get = urllib.request.Request(url_imgs, headers=auth_headers)
    try:
        with urllib.request.urlopen(req_get, timeout=15) as resp:
            existing = {img['rank']: img['listing_image_id']
                        for img in json.loads(resp.read()).get('results', [])}
    except Exception:
        existing = {}

    if rank in existing:
        url_del = (f"https://openapi.etsy.com/v3/application/shops/{shop_id}"
                   f"/listings/{listing_id}/images/{existing[rank]}")
        try:
            urllib.request.urlopen(
                urllib.request.Request(url_del, headers=auth_headers, method="DELETE"), timeout=15)
            time.sleep(0.3)
        except Exception:
            pass

    for attempt in range(3):
        try:
            result = client.upload_listing_image(listing_id, img_path, rank=rank)
            print(f"  Uploaded rank={rank}")
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


# ── Description template ──────────────────────────────────────────────────────

def make_description(hook, perfect_for, printing_tip=None):
    if printing_tip is None:
        printing_tip = (
            "• Matte or satin paper brings out the beautiful soft texture\n"
            "• A white or natural wood frame with wide white mat looks stunning\n"
            "• 11×14 or 16×20 shows the details at their best"
        )
    return f"""{hook}

━━━━━━━━━━━━━━━━━━━━━━━━
\U0001f4e6 WHAT YOU GET
━━━━━━━━━━━━━━━━━━━━━━━━
• Instant digital download — no waiting, no shipping
• High-resolution JPG files (300 DPI, print-ready)
• 8 sizes included: 4×6, 5×7, 8×10, 11×14, 16×20, 18×24, 24×30, 24×36
• Print at home or send to a print shop (Costco, Walgreens, Staples, any local lab)

━━━━━━━━━━━━━━━━━━━━━━━━
\U0001f3e0 PERFECT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
{perfect_for}

━━━━━━━━━━━━━━━━━━━━━━━━
\U0001f5a8️ HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase and download your files instantly from Etsy
2. Choose your preferred size (8 sizes included)
3. Print at home, at Costco, Walgreens, Staples, or your local print shop
4. Frame it and hang — that's it!

━━━━━━━━━━━━━━━━━━━━━━━━
\U0001f3a8 PRINTING TIPS
━━━━━━━━━━━━━━━━━━━━━━━━
{printing_tip}

━━━━━━━━━━━━━━━━━━━━━━━━
\U0001f4c4 FILE DETAILS
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
A: Matte or satin paper is ideal for this art — it captures the texture without glare.

Q: Can I use this for commercial purposes?
A: This license covers personal use only. Contact us for commercial licensing.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use."""


# ── Scene prompt template ─────────────────────────────────────────────────────

def scene_prompt(room_desc, wall_color, furniture_desc, lighting, style):
    return _scene_prompt(room_desc, wall_color, furniture_desc, lighting, style, focal="50mm")


# ── Listing definitions ───────────────────────────────────────────────────────

LISTINGS = {

    # ── DP1039: Ruby-Throated Hummingbird & Pink Garden Flowers ──────────────
    'DP1039': {
        'sku': 'OBC-WA-039',
        'title': 'Hummingbird Watercolor Print | Botanical Bird Art | Floral Wall Decor | Instant Download | Nature Art',
        'price': 5.99,
        'section': 'Botanical Art',
        'tags': [
            'hummingbird print',
            'bird wall art',
            'botanical art',
            'floral wall decor',
            'watercolor bird',
            'nature art print',
            'wildflower art',
            'printable wall art',
            'instant download',
            'digital download',
            'hummingbird decor',
            'bird lover gift',
            'tropical art print',
        ],
        'art_prompt': (
            "Vibrant watercolor painting of a ruby-throated hummingbird hovering mid-flight beside "
            "blooming pink garden flowers, portrait orientation. The hummingbird has brilliant emerald "
            "green wings and back, ruby-red throat patch, and cream-white belly — painted with fine "
            "luminous watercolor washes capturing the iridescent feather detail. The flowers include "
            "large pink foxglove bells, soft coral roses, and delicate pale pink cosmos, rendered in "
            "loose romantic watercolor style. Lush green botanical leaves and stems fill the background. "
            "Rich vibrant palette of emerald green, ruby red, soft coral pink, and warm cream. "
            "Authentic watercolor: wet-on-wet washes, soft color bleeding, visible paper grain, "
            "transparent glazes, preserved white highlights on wings and beak. "
            "Soft natural garden light, impressionistic botanical wildlife style. "
            "Wide cream border margins. Museum-quality. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (130, 100, 70),
        'scene_a_prompt': scene_prompt(
            "A bright airy sunlit living room",
            "warm white",
            "a cream linen loveseat with two blush pink botanical throw pillows, a small rattan side table with a pink peony in a clear glass vase, and a rattan floor lamp glowing softly",
            "Bright soft natural daylight from the left.",
            "Botanical garden home aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A light feminine bedroom",
            "soft blush",
            "a slim white bedside table with a small bouquet of fresh pink garden flowers in a bud vase, a pearl-white ceramic candle, and a linen-covered journal. The edge of white linen bedding is visible",
            "Soft morning natural light.",
            "Romantic botanical feminine retreat."
        ),
        'description': make_description(
            hook=(
                "\U0001f338 Bring the beauty of a sun-drenched garden to your walls — this luminous "
                "watercolor hummingbird print captures a ruby-throated hummingbird hovering beside pink "
                "foxglove and roses, painted with iridescent precision and soft botanical charm.\n\n"
                "Perfect for nature lovers, bird enthusiasts, and anyone who loves the delicate magic of "
                "a summer garden in bloom."
            ),
            perfect_for=(
                "• Living room, bedroom, or sunroom with garden or botanical decor\n"
                "• Feminine home office or reading nook\n"
                "• Cottagecore, farmhouse, or botanical-inspired interiors\n"
                "• Nursery with floral or nature theme\n"
                "• Mother's Day, birthday, or housewarming gift for bird or flower lovers"
            ),
        ),
    },

    # ── DP1040: Baby Bear Nursery Art ────────────────────────────────────────
    'DP1040': {
        'sku': 'OBC-WA-040',
        'title': 'Baby Bear Nursery Print | Woodland Nursery Art | Forest Animal Wall Decor | Instant Download',
        'price': 5.99,
        'section': 'Nursery Art',
        'tags': [
            'nursery wall art',
            'baby bear print',
            'woodland nursery',
            'forest animal art',
            'baby shower gift',
            'kids room decor',
            'nursery decor',
            'printable nursery',
            'instant download',
            'digital download',
            'woodland animals',
            'cute bear art',
            'gender neutral art',
        ],
        'art_prompt': (
            "Adorable sweet illustrated watercolor painting of a baby bear cub in a sunlit forest glade, "
            "portrait orientation. A chubby, round-faced baby bear cub with soft honey-brown fur sits "
            "contentedly among wildflowers and clover in a dappled woodland clearing. The cub has big "
            "dark innocent eyes and small rounded ears, depicted in a gentle storybook watercolor style. "
            "Surrounding the bear: soft pink wildflowers, white daisies, tiny mushrooms, green ferns, "
            "and golden autumn leaves on the forest floor. Background shows soft blurred birch trees "
            "with warm dappled golden light filtering through the canopy. "
            "Soft pastel palette: honey amber, sage green, soft pink, warm cream, gentle sky blue. "
            "Gentle children's book illustration style with soft watercolor washes, rounded friendly "
            "forms, and dreamy atmosphere. Wide cream/ivory border margins. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (139, 110, 80),
        'scene_a_prompt': scene_prompt(
            "A soft dreamy nursery room",
            "warm sage green",
            "a white wooden mini crib with soft cream and sage linen bedding, a small stuffed bear toy propped against the pillow, and a tiny potted fern on the crib ledge",
            "Soft diffused natural light from a nearby window.",
            "Gentle woodland nursery aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A cozy children's room",
            "warm honey cream",
            "a low white wooden toy shelf holding a row of small wooden toys and a plush bear figurine, a small stack of children's picture books, and a tiny trailing ivy plant in a white ceramic pot",
            "Warm soft natural daylight.",
            "Sweet woodland kids room aesthetic."
        ),
        'description': make_description(
            hook=(
                "\U0001f43b Give the little one's room a touch of woodland magic — this dreamy watercolor "
                "baby bear nursery print features a sweet honey-brown bear cub nestled among wildflowers "
                "and ferns in a sunlit forest glade, painted in soft storybook watercolor style.\n\n"
                "Gender-neutral and universally beloved, it's perfect for any nursery or children's room "
                "with a nature, woodland, or forest theme."
            ),
            perfect_for=(
                "• Nursery, baby's room, or toddler's room\n"
                "• Woodland, forest, or nature-themed nursery decor\n"
                "• Gender-neutral nursery (works for any baby!)\n"
                "• Baby shower gift, new baby gift, or birthday gift\n"
                "• Playroom or kids' reading nook"
            ),
        ),
    },

    # ── DP1041: Mountain Lake Reflection at Dusk ──────────────────────────────
    'DP1041': {
        'sku': 'OBC-WA-041',
        'title': 'Mountain Lake Watercolor Print | Landscape Wall Art | Nature Home Decor | Instant Download',
        'price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'mountain wall art',
            'lake art print',
            'landscape print',
            'nature wall art',
            'watercolor scenery',
            'adventure home art',
            'printable wall art',
            'instant download',
            'digital download',
            'cabin wall art',
            'mountain decor',
            'hiking home decor',
            'wilderness print',
        ],
        'art_prompt': (
            "Breathtaking watercolor painting of a serene mountain lake at golden hour dusk, portrait "
            "orientation. Majestic snow-capped mountain peaks glow in warm amber and rose gold, perfectly "
            "reflected in the glassy still surface of an alpine lake below. The sky is painted in "
            "luminous gradient washes from deep violet and purple at the top transitioning through "
            "rose, peach, and golden amber at the horizon. Towering dark pine trees silhouette the "
            "lake shores on both sides, their reflections stretching down into the still water. "
            "A tiny wooden dock extends into the foreground of the lake. "
            "Rich painterly palette: deep violet-purple sky, rose and amber mountains, dark forest "
            "green pines, golden reflections on glassy still water. "
            "Authentic watercolor technique: wet-on-wet sky washes, soft bleeding color transitions, "
            "sharp silhouetted pine tree edges, luminous reflected light on water. "
            "Wide cream/ivory border margins. Museum-quality landscape. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (80, 90, 100),
        'scene_a_prompt': scene_prompt(
            "A sophisticated modern living room",
            "warm charcoal gray",
            "a low dark leather mid-century sofa with two slate blue and cream geometric throw pillows, a slim dark walnut coffee table with an architectural book and a small stone bowl, and a tall sculptural black lamp to the right",
            "Warm amber lamp light from the right, moody and dramatic.",
            "Modern masculine adventure-lover aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A rustic cabin lodge",
            "warm honey pine wood-paneled",
            "a low log-style sofa with plaid cream and navy wool throws, a rough-hewn wood side table with a lantern-style lamp glowing, and a small stack of outdoor adventure books",
            "Warm amber lantern glow, cozy and intimate.",
            "Rustic lodge mountain cabin aesthetic."
        ),
        'description': make_description(
            hook=(
                "⛰️ Capture the breathtaking stillness of the mountains — this luminous watercolor "
                "landscape print shows majestic snow-capped peaks glowing in rose and amber at golden hour, "
                "their perfect reflection stretching across a glassy alpine lake below.\n\n"
                "Ideal for adventure lovers, mountain hikers, and anyone who finds peace in the grandeur of "
                "untouched wilderness."
            ),
            perfect_for=(
                "• Living room, home office, or study with mountain or adventure decor\n"
                "• Cabin, lodge, or vacation home\n"
                "• Bedroom or meditation space (the stillness is deeply calming)\n"
                "• Gift for hikers, climbers, skiers, or outdoor adventurers\n"
                "• Man cave, gentleman's study, or masculine home office"
            ),
        ),
    },

    # ── DP1042: Summer Wildflower Meadow ─────────────────────────────────────
    'DP1042': {
        'sku': 'OBC-WA-042',
        'title': 'Wildflower Meadow Watercolor Print | Botanical Wall Art | Cottage Garden Decor | Instant Download',
        'price': 5.99,
        'section': 'Botanical Art',
        'tags': [
            'wildflower print',
            'botanical wall art',
            'meadow art print',
            'watercolor flowers',
            'cottage garden art',
            'floral wall decor',
            'printable wall art',
            'instant download',
            'digital download',
            'flower art print',
            'cottagecore art',
            'nature wall print',
            'garden home decor',
        ],
        'art_prompt': (
            "Beautiful loose impressionistic watercolor painting of a sun-drenched summer wildflower meadow, "
            "portrait orientation. A profusion of colorful wildflowers fills the canvas: vibrant orange and "
            "red California poppies, soft pink cosmos swaying in the breeze, bright blue cornflowers, "
            "white daisies with golden centers, and tall wild grasses glowing in warm afternoon light. "
            "The flowers tumble and overlap in rich organic abundance — a joyful riot of color and life. "
            "Background fades into a soft golden-warm blur of more distant wildflowers and a soft blue sky. "
            "Luminous palette of orange, coral pink, sky blue, golden yellow, white, and soft sage green. "
            "Authentic watercolor: loose wet-on-wet washes, beautiful color bleeding between petals, "
            "visible paper grain, transparent layered glazes, soft impressionistic brushwork. "
            "Warm afternoon golden sunlight atmosphere. Wide cream/ivory border margins. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (139, 110, 80),
        'scene_a_prompt': scene_prompt(
            "A bright farmhouse kitchen-dining area",
            "clean white shiplap",
            "a round light oak farmhouse dining table with two woven rattan-backed chairs, a small ceramic pitcher holding a few fresh wildflowers, and a linen table runner in warm cream",
            "Bright natural daylight from a large window.",
            "Fresh cottagecore farmhouse kitchen aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A soft airy bedroom",
            "warm cream linen",
            "a slim white painted nightstand with a small bouquet of fresh wildflowers in a clear glass jar, a cream ceramic candle, and a linen-covered journal. The edge of white linen bedding visible below",
            "Soft morning natural light through gauzy curtains.",
            "Romantic botanical cottage bedroom."
        ),
        'description': make_description(
            hook=(
                "\U0001f33c Fill your home with the joy of a sun-drenched summer meadow — this luminous "
                "watercolor wildflower print captures poppies, cosmos, cornflowers, and daisies tumbling "
                "together in a beautiful impressionistic riot of color and natural abundance.\n\n"
                "Perfect for botanical art lovers, cottage-style homes, and anyone who loves the wild "
                "beauty of garden flowers in full summer bloom."
            ),
            perfect_for=(
                "• Kitchen, dining room, or bright farmhouse living space\n"
                "• Bedroom, reading nook, or sunroom\n"
                "• Cottagecore, farmhouse, or garden-inspired interiors\n"
                "• Bathroom with botanical decor or feminine powder room\n"
                "• Mother's Day, birthday, or housewarming gift for flower lovers"
            ),
        ),
    },

    # ── DP1043: Vintage Cat Reading by Firelight ──────────────────────────────
    'DP1043': {
        'sku': 'OBC-WA-043',
        'title': 'Cat Reading Book Art Print | Library Cat Decor | Cozy Bookish Wall Art | Instant Download',
        'price': 5.99,
        'section': 'Humor and Pop Art',
        'tags': [
            'cat wall art',
            'book lover gift',
            'cat lover gift',
            'library art print',
            'cozy home decor',
            'bookish home',
            'printable wall art',
            'instant download',
            'digital download',
            'cat art print',
            'funny cat decor',
            'reading room decor',
            'vintage cat art',
        ],
        'art_prompt': (
            "Charming vintage-style watercolor illustration of a distinguished tabby cat wearing small "
            "round brass reading glasses, sitting contentedly in a worn leather armchair surrounded by "
            "stacked books, portrait orientation. The cat has elegant orange and cream tabby markings, "
            "a fluffy tail curled around its paws, and a refined, slightly pompous expression as it "
            "holds open a small leather-bound book. The setting shows a cozy corner of a home library: "
            "a warm glowing amber table lamp beside the chair, a teetering stack of hardcover books on "
            "the floor, a delicate china teacup with steam rising, and dark wood bookshelves visible "
            "in the soft-focus background. "
            "Rich warm palette of amber, caramel, deep burgundy, dark mahogany, and cream. "
            "Vintage editorial illustration style with loose watercolor washes, fine ink-line details, "
            "warm amber candlelight atmosphere, charming and humorous yet sophisticated. "
            "Wide cream/ivory border margins. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (100, 80, 55),
        'scene_a_prompt': scene_prompt(
            "A warm cozy home library or study",
            "warm cream",
            "a dark wood floating shelf with a row of hardcover books by their spines, a small vintage globe, a brass desk lamp glowing warmly, and a ceramic mug of tea. Dark wood bookshelves visible at the side edges",
            "Warm amber lamp light and late afternoon sun.",
            "Cozy English study library aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A cozy bedroom reading nook",
            "warm amber",
            "a slim natural wood nightstand with a small stack of well-worn paperback books, a glowing brass bedside lamp, and a ceramic mug. The edge of a linen-covered armchair and a folded knit throw visible",
            "Warm amber lamp light, intimate evening reading atmosphere.",
            "Bookish cozy retreat aesthetic."
        ),
        'description': make_description(
            hook=(
                "\U0001f431\U0001f4da The perfect art for book lovers and cat people alike — this charming "
                "vintage watercolor print shows a distinguished tabby cat in reading glasses, sitting in a "
                "leather armchair with a leather-bound book, surrounded by stacked books and a steaming "
                "cup of tea.\n\n"
                "It's sophisticated, a little bit funny, and guaranteed to start a conversation with "
                "every visitor who sees it."
            ),
            perfect_for=(
                "• Home library, study, or reading room\n"
                "• Living room bookshelf wall or bedroom reading nook\n"
                "• Cat lover's home of any style\n"
                "• Bookish home office or academic study\n"
                "• Gift for book lovers, cat lovers, teachers, or academics"
            ),
        ),
    },

    # ── DP1044: Ocean Wave at Sunrise ─────────────────────────────────────────
    'DP1044': {
        'sku': 'OBC-WA-044',
        'title': 'Ocean Wave Watercolor Print | Coastal Wall Art | Beach Home Decor | Instant Download | Seascape Art',
        'price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'ocean wall art',
            'wave art print',
            'coastal wall art',
            'beach home decor',
            'seascape print',
            'watercolor ocean',
            'nautical decor',
            'printable wall art',
            'instant download',
            'beach house art',
            'navy blue wall art',
            'digital download',
            'ocean decor',
        ],
        'art_prompt': (
            "Dramatic and beautiful watercolor painting of a powerful ocean wave cresting at sunrise, "
            "portrait orientation. A magnificent translucent turquoise-aqua wave curls and rises, "
            "its crest caught at the perfect moment just before breaking — golden morning sunlight "
            "shines through the wave, illuminating the water from within with brilliant warm gold "
            "and aqua light. Foamy white sea spray catches the light at the top. The ocean beyond "
            "shows deep navy and teal waves receding into a glowing coral-pink and amber sunrise "
            "horizon. "
            "Luminous palette of translucent aqua-turquoise, deep navy, warm gold sunrise, coral "
            "pink, and sparkling white foam. "
            "Authentic watercolor technique: luminous wet-on-wet transparent washes, preserved white "
            "highlights on foam and wave crest, beautiful color bleeding where aqua meets gold light, "
            "soft atmospheric sunrise glow. "
            "Wide cream/ivory border margins. Museum-quality seascape. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (70, 100, 120),
        'scene_a_prompt': scene_prompt(
            "A calm coastal master bedroom",
            "deep navy blue",
            "a low upholstered headboard in cream linen with a navy and white pillow arrangement visible at the bottom, and a small white nightstand with a brushed silver lamp and a smooth river stone",
            "Soft ambient lamp light, moody coastal atmosphere.",
            "Coastal luxury bedroom aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A bright white coastal living room",
            "clean bright white",
            "a slim white console table with a clear glass vase holding dried sea grass, two smooth white river stones arranged beside it, and a small coiled rope in natural fiber",
            "Bright natural coastal daylight.",
            "Fresh minimal beach house aesthetic."
        ),
        'description': make_description(
            hook=(
                "\U0001f30a Bring the power and beauty of the sea into your home — this luminous "
                "watercolor seascape print captures a magnificent turquoise wave cresting at sunrise, "
                "golden morning light shining through the water and turning it to liquid fire.\n\n"
                "Perfect for coastal homes, ocean lovers, and anyone who finds peace and energy in "
                "the sound of the waves."
            ),
            perfect_for=(
                "• Coastal bedroom, master suite, or beach house living room\n"
                "• Bathroom, hallway, or entryway with nautical decor\n"
                "• Vacation home, lake house, or seaside cottage\n"
                "• Navy blue or coastal color scheme rooms\n"
                "• Gift for surfers, sailors, swimmers, or ocean lovers"
            ),
            printing_tip=(
                "• Matte paper best preserves the luminous watercolor quality\n"
                "• A slim dark navy or driftwood frame with wide white mat looks stunning\n"
                "• 16×20 or larger shows the dramatic wave detail at its best"
            ),
        ),
    },

    # ── DP1045: Lavender Fields of Provence ───────────────────────────────────
    'DP1045': {
        'sku': 'OBC-WA-045',
        'title': 'Lavender Fields Watercolor Print | Provence Wall Art | French Country Decor | Instant Download',
        'price': 5.99,
        'section': 'Botanical Art',
        'tags': [
            'lavender wall art',
            'provence art',
            'french country art',
            'floral landscape',
            'purple wall art',
            'botanical art',
            'cottage decor',
            'printable wall art',
            'instant download',
            'digital download',
            'romantic wall art',
            'watercolor scenery',
            'lavender print',
        ],
        'art_prompt': (
            "Romantic impressionistic watercolor painting of lavender fields in Provence at golden hour, "
            "portrait orientation. Long sweeping rows of purple lavender stretch toward the horizon "
            "beneath a warm golden sky — the lavender blooms painted in loose, vibrant washes of "
            "violet, purple, and soft blue-mauve, punctuated by stems of silver-green sage foliage. "
            "A lone golden cypress tree stands tall on the left, and a rustic stone Provencal farmhouse "
            "with terracotta roof tiles glows warmly in the evening light on the right. "
            "The sky above is a beautiful warm wash of soft gold, peachy amber, and pale cream. "
            "Luminous palette of violet purple lavender, dusty sage green, warm golden amber, "
            "terracotta, and soft cream sky. "
            "Authentic impressionistic watercolor: loose gestural brushwork, beautiful color bleeding, "
            "wet-on-wet sky washes, visible paper grain, warm golden evening light atmosphere. "
            "Wide cream/ivory border margins. Museum-quality. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (130, 105, 75),
        'scene_a_prompt': scene_prompt(
            "A sunny French country kitchen",
            "warm butter yellow",
            "a rustic white-painted farmhouse dining table with a linen table runner, a ceramic pitcher holding fresh lavender sprigs, a round wicker bread basket, and two Windsor-style wooden chairs",
            "Warm golden morning sunlight from the right.",
            "French country Provence kitchen aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A soft romantic bedroom",
            "warm lavender cream",
            "a white bedside table with a small bunch of dried lavender in a cream ceramic vase, a small brass lamp glowing warmly, and a hardcover book with a floral spine. White linen bedding visible below",
            "Soft warm ambient lamp light.",
            "Romantic French country bedroom aesthetic."
        ),
        'description': make_description(
            hook=(
                "\U0001f33f Transport yourself to the south of France — this luminous impressionistic "
                "watercolor print captures the iconic lavender fields of Provence at golden hour, with "
                "sweeping rows of violet blooms stretching toward a warm amber sky and a rustic stone "
                "farmhouse glowing in the evening light.\n\n"
                "Perfect for French country interiors, Provencal decor lovers, and anyone who dreams "
                "of a quiet afternoon among endless purple fields."
            ),
            perfect_for=(
                "• Kitchen, dining room, or French country living space\n"
                "• Bedroom or bathroom with romantic or cottage decor\n"
                "• Purple or warm neutral color scheme rooms\n"
                "• Farmhouse, cottage, or Provence-inspired home\n"
                "• Gift for France lovers, garden lovers, or anyone who loves lavender"
            ),
        ),
    },

    # ── DP1046: Snowy Owl in Winter Birch Forest ──────────────────────────────
    'DP1046': {
        'sku': 'OBC-WA-046',
        'title': 'Snowy Owl Watercolor Print | Winter Wildlife Art | Woodland Bird Decor | Instant Download',
        'price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'owl wall art',
            'snowy owl print',
            'winter wall art',
            'wildlife art print',
            'bird wall art',
            'woodland decor',
            'watercolor owl',
            'printable wall art',
            'instant download',
            'digital download',
            'owl decor',
            'nature art print',
            'winter home decor',
        ],
        'art_prompt': (
            "Majestic and serene watercolor painting of a snowy owl in a moonlit winter birch forest, "
            "portrait orientation. A large, beautifully detailed snowy owl perches on a snow-covered "
            "birch branch, its pure white and pale gray spotted feathers painted with fine luminous "
            "watercolor washes. The owl faces slightly left with large golden eyes gazing with calm "
            "intelligence. Snow falls gently as soft white flurries around the bird. "
            "The winter forest background shows slender pale silver birch trunks with dark branch "
            "markings, dusted in snow, receding into a soft blue-silver misty forest depth. "
            "A soft full moon glows in the upper background, its cool silver light illuminating "
            "the scene with a magical winter atmosphere. "
            "Cool palette of pure white, soft silver-blue, ice blue, cool gray, and warm gold "
            "(owl eyes) on a misty silver-white forest background. "
            "Authentic watercolor: transparent luminous washes, fine feather detail, soft misty "
            "depth, preserved bright highlights on snow and moon. "
            "Wide cream/ivory border margins. Museum-quality wildlife art. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (100, 115, 130),
        'scene_a_prompt': scene_prompt(
            "A warm cozy rustic cabin living room",
            "warm honey pine",
            "a log-style armchair with a cream and blue plaid wool throw draped over the arm, a small wood side table with a lantern candle glowing amber, and a stack of nature books",
            "Warm amber lantern and fireplace glow.",
            "Cozy cabin winter retreat aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A serene cool-toned bedroom",
            "soft blue-gray",
            "a slim white nightstand with a silver geometric lamp glowing softly, a smooth white quartz crystal, and a small white ceramic vase with a single dried white branch. White linen bedding visible below",
            "Cool soft ambient light, serene and peaceful.",
            "Serene winter minimalist bedroom aesthetic."
        ),
        'description': make_description(
            hook=(
                "\U0001f989 Capture the silent magic of winter — this luminous watercolor snowy owl print "
                "shows a majestic white owl perched on a snow-dusted birch branch in a moonlit winter "
                "forest, painted with extraordinary feather detail and a serene, peaceful atmosphere.\n\n"
                "Perfect for nature lovers, bird enthusiasts, and anyone who loves the quiet, magical "
                "beauty of winter woodland scenes."
            ),
            perfect_for=(
                "• Living room, bedroom, or study in a cabin, lodge, or nature-inspired home\n"
                "• Cool-toned bedroom or reading nook\n"
                "• Holiday or winter seasonal decor (beautiful year-round too)\n"
                "• Rustic, Scandinavian, or woodland-themed interiors\n"
                "• Gift for bird lovers, owl fans, or winter nature enthusiasts"
            ),
            printing_tip=(
                "• Matte paper best captures the soft watercolor feather detail\n"
                "• A slim silver, driftwood, or pale birch frame with wide white mat is stunning\n"
                "• 16×20 or larger brings out the beautiful owl feather detail"
            ),
        ),
    },

    # ── DP1047: Farmhouse Rooster in the Garden ───────────────────────────────
    'DP1047': {
        'sku': 'OBC-WA-047',
        'title': 'Farmhouse Rooster Art Print | Kitchen Wall Decor | Country Farm Art | Instant Download | Rustic',
        'price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'rooster wall art',
            'farmhouse kitchen',
            'rooster print',
            'kitchen wall art',
            'farm animal art',
            'rustic home decor',
            'country kitchen',
            'printable wall art',
            'instant download',
            'digital download',
            'farmhouse decor',
            'vintage rooster',
            'dining room art',
        ],
        'art_prompt': (
            "Bold and beautiful watercolor painting of a proud farmhouse rooster in a sunny kitchen "
            "garden, portrait orientation. A magnificent rooster stands tall and confident in the "
            "foreground — vibrant iridescent feathers in rich jewel-toned greens, deep cobalt blue, "
            "warm chestnut red, and brilliant gold, his bright red comb and wattles vivid in the "
            "morning light. The rooster's feathers are painted with loose impressionistic watercolor "
            "washes that capture the iridescent shimmer of each plume. "
            "Behind the rooster: a sun-drenched cottage garden with climbing roses on a whitewashed "
            "fence, red tomatoes on the vine, potted herbs (rosemary, lavender, thyme), and golden "
            "sunflowers. The background is loose, warm, and impressionistic. "
            "Warm vibrant palette of jewel-toned greens and blues (feathers), rich crimson (comb), "
            "warm chestnut, sunflower gold, and soft sage garden greens. "
            "Authentic watercolor: loose gestural brushwork, beautiful color bleeding in the feathers, "
            "warm garden sunlight atmosphere, impressionistic painted style. "
            "Wide cream/ivory border margins. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (130, 100, 65),
        'scene_a_prompt': scene_prompt(
            "A warm rustic farmhouse kitchen",
            "warm white with open wood shelving visible at the sides",
            "a round farm table partially visible with a terracotta bowl of fresh eggs, a small pot of fresh herbs, a red-and-white checked linen cloth, and a ceramic rooster figurine",
            "Warm golden morning kitchen light.",
            "Rustic farmhouse country kitchen aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A warm country dining room",
            "warm cream with subtle rustic texture",
            "a rustic farmhouse dining table with a linen runner, a wooden bread board with a small ceramic dish, and two mason jars holding wildflowers. The backs of farmhouse chairs visible",
            "Warm afternoon natural light.",
            "French country farmhouse dining room aesthetic."
        ),
        'description': make_description(
            hook=(
                "\U0001f413 Give your kitchen or dining room the bold character it deserves — this "
                "vibrant watercolor rooster print captures a proud farmhouse cockerel in jewel-toned "
                "iridescent feathers, standing in a sunny cottage garden painted in warm, impressionistic "
                "brushstrokes.\n\n"
                "A timeless piece of farmhouse kitchen art that brings color, warmth, and a touch of "
                "countryside charm to any wall."
            ),
            perfect_for=(
                "• Kitchen, dining room, or farmhouse living space\n"
                "• Rustic, French country, or cottage-style interiors\n"
                "• Breakfast nook, butler's pantry, or mudroom\n"
                "• Farmhouse, country home, or cottage kitchen\n"
                "• Gift for farmers, country living lovers, or farmhouse decor enthusiasts"
            ),
            printing_tip=(
                "• Matte or satin paper captures the loose watercolor feather detail beautifully\n"
                "• A rustic wood, antique gold, or dark walnut frame suits the farmhouse aesthetic\n"
                "• 11×14 or 16×20 shows the vibrant rooster feathers at their best"
            ),
        ),
    },
}


# ── Main runner ───────────────────────────────────────────────────────────────

def run_listing(pid, info, post_to_etsy=True):
    out_dir = os.path.join(ART_DIR, f'{pid}_listing_images')
    art_path = os.path.join(ART_DIR, f'{pid}.jpg')
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"[{pid}] {info['title'][:65]}...")
    print(f"{'='*60}")

    # 1. Generate art
    print(f"\n[1] Art...")
    if not os.path.exists(art_path):
        ok = gen_image(info['art_prompt'], art_path, size=info['art_size'], quality="high")
        if not ok:
            print(f"  FAILED art generation for {pid} — skipping")
            return None
        time.sleep(4)
    else:
        print(f"  Exists: {os.path.basename(art_path)}")

    # 2. Scene A background + composite
    print(f"\n[2] Scene A...")
    bg_a = os.path.join(out_dir, 'bg_lifestyle_scene_A.jpg')
    scene_a = os.path.join(out_dir, 'lifestyle_scene_A.jpg')
    if not os.path.exists(bg_a):
        ok = gen_image(info['scene_a_prompt'], bg_a, size="1024x1024", quality="high")
        if not ok:
            print(f"  WARNING: scene A background failed")
        else:
            time.sleep(3)
    else:
        print(f"  Background exists.")
    if os.path.exists(bg_a):
        composite_smart(bg_a, art_path, scene_a,
                        frame_color=info.get('frame_color', (139, 110, 80)))

    # 3. Scene B background + composite
    print(f"\n[3] Scene B...")
    bg_b = os.path.join(out_dir, 'bg_lifestyle_scene_B.jpg')
    scene_b = os.path.join(out_dir, 'lifestyle_scene_B.jpg')
    if not os.path.exists(bg_b):
        ok = gen_image(info['scene_b_prompt'], bg_b, size="1024x1024", quality="high")
        if not ok:
            print(f"  WARNING: scene B background failed")
        else:
            time.sleep(3)
    else:
        print(f"  Background exists.")
    if os.path.exists(bg_b):
        composite_smart(bg_b, art_path, scene_b,
                        frame_color=info.get('frame_color', (139, 110, 80)))

    # 4. Room template composites
    print(f"\n[4] Room composites...")
    rooms = {}
    for rk in ['living_room', 'kitchen_dining', 'entryway']:
        out = os.path.join(out_dir, f'room_{rk}.jpg')
        create_room_composite(art_path, rk, out)
        rooms[rk] = out

    # 5. Size guide
    print(f"\n[5] Size guide...")
    sg_path = os.path.join(out_dir, 'size_guide.jpg')
    create_size_guide(art_path, sg_path)

    # 6. What's included
    print(f"\n[6] What's Included...")
    wi_path = os.path.join(out_dir, 'whats_included.jpg')
    create_whats_included(art_path, wi_path,
                          info['title'].split('|')[0].strip(), info['price'])

    all_images = [
        (scene_a, 1), (scene_b, 2),
        (rooms['living_room'], 3), (rooms['kitchen_dining'], 4), (rooms['entryway'], 5),
        (sg_path, 6), (wi_path, 7), (art_path, 8),
    ]

    print(f"\n{'─'*40}")
    for label, (path, rank) in zip(
        ['Scene A', 'Scene B', 'Living Room', 'Kitchen', 'Entryway', 'Size Guide', "What's Incl.", 'Art File'],
        all_images
    ):
        status = f"{'✓' if os.path.exists(path) else '✗ MISSING'} ({os.path.getsize(path)//1024}KB)"
        print(f"  rank {rank}: {label:20s} {status}")

    if not post_to_etsy:
        print(f"\n[PREVIEW] Images saved for {pid}. Not posting to Etsy.")
        return {'pid': pid, 'out_dir': out_dir}

    # 7. Post to Etsy
    print(f"\n[7] Posting to Etsy...")
    refresh()

    section_id = client.get_or_create_section(info['section'])
    print(f"  Section '{info['section']}': id={section_id}")

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
        print(f"  FAILED to create Etsy listing for {pid}")
        return None

    lid = listing['listing_id']
    print(f"  Created listing_id={lid}")
    time.sleep(1)

    uploaded = 0
    for img_path, rank in all_images:
        if os.path.exists(img_path):
            if upload_image(lid, img_path, rank):
                uploaded += 1
            time.sleep(0.8)
        else:
            print(f"  SKIP rank={rank}: missing")
    print(f"  Uploaded {uploaded}/{len(all_images)} images")
    time.sleep(1)

    print(f"  Uploading digital file...")
    upload_file(lid, art_path)
    time.sleep(1)

    print(f"  Activating...")
    activated = activate_listing(lid)
    if activated and activated.get('state') == 'active':
        print(f"  ✓ LIVE: https://www.etsy.com/listing/{lid}/")
    else:
        print(f"  WARNING: check activation on Etsy dashboard")

    # Save to shop_data.json
    try:
        sdp = '/home/user/Etsy/data/shop_data.json'
        with open(sdp) as f:
            sd = json.load(f)
        sd.setdefault('listings', []).append({
            'id': str(lid), 'title': info['title'], 'price': info['price'],
            'type': 'wall_art', 'listing_type': 'download', 'state': 'active',
            'tags': info['tags'], 'taxonomy_id': 2078, 'images': [],
            'url': f'https://www.etsy.com/listing/{lid}/', 'views': 0,
            'quantity': 999, 'description': info['description'],
        })
        with open(sdp, 'w') as f:
            json.dump(sd, f, indent=2)
        print(f"  Saved to shop_data.json")
    except Exception as e:
        print(f"  WARNING: could not update shop_data.json: {e}")

    return {'pid': pid, 'lid': lid, 'uploaded': uploaded}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pids', nargs='+', default=None,
                        help='Only run these product IDs (e.g. DP1039 DP1040)')
    parser.add_argument('--preview', action='store_true',
                        help='Generate images only — do not post to Etsy')
    args = parser.parse_args()

    pids = args.pids if args.pids else list(LISTINGS.keys())
    results = []

    for pid in pids:
        info = LISTINGS.get(pid)
        if not info:
            print(f"Unknown PID: {pid}")
            continue
        try:
            r = run_listing(pid, info, post_to_etsy=not args.preview)
            results.append(r)
        except Exception as e:
            print(f"\nERROR processing {pid}: {e}")
            import traceback; traceback.print_exc()
            results.append({'pid': pid, 'error': str(e)})
        time.sleep(2)

    print(f"\n\n{'='*60}")
    print("BATCH COMPLETE")
    print(f"{'='*60}")
    for r in results:
        if r is None:
            print("  FAILED (None)")
        elif 'error' in r:
            print(f"  {r.get('pid', '?')} — ERROR: {r['error']}")
        elif 'lid' in r:
            print(f"  ✓ {r['pid']} — listing {r['lid']} — https://www.etsy.com/listing/{r['lid']}/")
        else:
            print(f"  {r.get('pid', '?')} — preview only")
