#!/usr/bin/env python3
"""
Batch create and post wall art listings DP1048–DP1057 plus two set bundle listings.

Sets:
  Four Seasons Collection: DP1048 Spring, DP1049 Summer, DP1050 Autumn, DP1051 Winter
  Coastal Dreams Collection: DP1052 Sea Turtle, DP1053 Lighthouse, DP1054 Coral Reef, DP1055 Pelican
  Standalone: DP1056 Red Fox, DP1057 Paris Café

Usage:
  python tools/create_art_listings_10.py              # all individuals + set bundles
  python tools/create_art_listings_10.py --pids DP1048
  python tools/create_art_listings_10.py --sets-only  # set bundle listings only
  python tools/create_art_listings_10.py --preview    # images only, no Etsy
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


# ── Compositing helpers ───────────────────────────────────────────────────────

def _load_fonts():
    base = "/usr/share/fonts/truetype/dejavu/"
    try:
        return {
            'h1':    ImageFont.truetype(base + "DejaVuSans-Bold.ttf", 38),
            'h2':    ImageFont.truetype(base + "DejaVuSans-Bold.ttf", 26),
            'body':  ImageFont.truetype(base + "DejaVuSans.ttf", 23),
            'sm':    ImageFont.truetype(base + "DejaVuSans.ttf", 19),
            'price': ImageFont.truetype(base + "DejaVuSans-Bold.ttf", 52),
            'title': ImageFont.truetype(base + "DejaVuSans-Bold.ttf", 32),
            'label': ImageFont.truetype(base + "DejaVuSans.ttf", 18),
        }
    except Exception:
        d = ImageFont.load_default()
        return {k: d for k in ('h1','h2','body','sm','price','title','label')}


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


def _apply_frame(room, px, py, art_path, art_w, mat_w, frame_w, frame_color, ao_radius=22, shadow_radius=14):
    """Composite one framed piece onto room image. Returns updated room."""
    art = Image.open(art_path).convert('RGB')
    art_h = int(art_w * art.height / art.width)
    art_resized = art.resize((art_w, art_h), Image.LANCZOS)
    full_w = art_w + 2*mat_w + 2*frame_w
    full_h = art_h + 2*mat_w + 2*frame_w

    ao = Image.new('RGBA', room.size, (0,0,0,0))
    for pad in range(int(ao_radius*1.8), 0, -3):
        alpha = int(38 * (1 - (pad/(ao_radius*1.8))**1.5))
        ImageDraw.Draw(ao).rectangle([px-pad, py-pad, px+full_w+pad, py+full_h+pad], fill=(0,0,0,alpha))
    ao = ao.filter(ImageFilter.GaussianBlur(radius=ao_radius))
    room = Image.alpha_composite(room.convert('RGBA'), ao).convert('RGB')

    shadow = Image.new('RGBA', room.size, (0,0,0,0))
    ImageDraw.Draw(shadow).rectangle([px+8, py+10, px+full_w+8, py+full_h+10], fill=(0,0,0,75))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_radius))
    room = Image.alpha_composite(room.convert('RGBA'), shadow).convert('RGB')

    draw = ImageDraw.Draw(room)
    draw.rectangle([px, py, px+full_w, py+full_h], fill=frame_color)
    hi = tuple(min(255, c+40) for c in frame_color)
    sh = tuple(max(0, c-40) for c in frame_color)
    bv = 4
    draw.polygon([px,py, px+full_w,py, px+full_w-bv,py+bv, px+bv,py+bv], fill=hi)
    draw.polygon([px,py, px,py+full_h, px+bv,py+full_h-bv, px+bv,py+bv], fill=hi)
    draw.polygon([px+full_w,py, px+full_w,py+full_h, px+full_w-bv,py+full_h-bv, px+full_w-bv,py+bv], fill=sh)
    draw.polygon([px,py+full_h, px+full_w,py+full_h, px+full_w-bv,py+full_h-bv, px+bv,py+full_h-bv], fill=sh)

    mx, my = px+frame_w, py+frame_w
    draw.rectangle([mx, my, mx+art_w+2*mat_w, my+art_h+2*mat_w], fill=(253,251,248))

    inner = Image.new('RGBA', room.size, (0,0,0,0))
    art_x, art_y = mx+mat_w, my+mat_w
    ImageDraw.Draw(inner).rectangle([art_x-3, art_y-3, art_x+art_w+3, art_y+art_h+3], fill=(0,0,0,28))
    inner = inner.filter(ImageFilter.GaussianBlur(radius=5))
    room = Image.alpha_composite(room.convert('RGBA'), inner).convert('RGB')

    art_final = ImageEnhance.Brightness(art_resized).enhance(0.93)
    room.paste(art_final, (art_x, art_y))
    return room


def composite_into_ai_room(bg_path, art_path, out_path, frame_color=(139,110,80),
                            art_pct=0.25, top_pct=0.06):
    CANVAS = 1024
    room = Image.open(bg_path).convert('RGB').resize((CANVAS, CANVAS), Image.LANCZOS)
    art_w = int(CANVAS * art_pct)
    mat_w, frame_w = 30, 14
    px = (CANVAS - (art_w + 2*mat_w + 2*frame_w)) // 2
    py = int(CANVAS * top_pct)
    room = _apply_frame(room, px, py, art_path, art_w, mat_w, frame_w, frame_color, ao_radius=22, shadow_radius=14)
    room.save(out_path, 'JPEG', quality=93)
    print(f"  Lifestyle composite: {os.path.basename(out_path)}")


def composite_4_into_room(bg_path, art_paths, out_path, frame_color=(139,110,80)):
    """2×2 gallery wall of 4 framed pieces composited into a room background."""
    CANVAS = 1024
    room = Image.open(bg_path).convert('RGB').resize((CANVAS, CANVAS), Image.LANCZOS)

    # Each piece: 16% canvas width, mat=11, frame=6
    art_pct = 0.16
    mat_w, frame_w = 11, 6
    gap = 18
    top_pct = 0.04

    sample = Image.open(art_paths[0])
    aspect = sample.height / sample.width
    sample.close()

    art_w = int(CANVAS * art_pct)           # ~164px
    art_h = int(art_w * aspect)             # ~246px
    full_w = art_w + 2*mat_w + 2*frame_w   # ~198px
    full_h = art_h + 2*mat_w + 2*frame_w   # ~280px

    total_grid_w = 2*full_w + gap           # ~414px
    start_x = (CANVAS - total_grid_w) // 2
    start_y = int(CANVAS * top_pct)        # 41px; grid bottom ~ 41+2*280+18=619px=60.4% ✓

    for i, art_path in enumerate(art_paths):
        col, row = i % 2, i // 2
        px = start_x + col*(full_w + gap)
        py = start_y + row*(full_h + gap)
        room = _apply_frame(room, px, py, art_path, art_w, mat_w, frame_w, frame_color,
                            ao_radius=14, shadow_radius=9)

    room.save(out_path, 'JPEG', quality=93)
    print(f"  Gallery wall composite: {os.path.basename(out_path)}")


def create_gallery_grid(art_paths, labels, out_path, set_title, subtitle=""):
    """Clean 2×2 grid of all 4 art pieces on a neutral background."""
    W, H = 1200, 1200
    fonts = _load_fonts()
    canvas = Image.new('RGB', (W, H), (244, 241, 236))
    draw = ImageDraw.Draw(canvas)

    draw.text((W//2, 38), set_title, font=fonts['title'], fill=(60,55,50), anchor="mm")
    if subtitle:
        draw.text((W//2, 72), subtitle, font=fonts['sm'], fill=(100,88,75), anchor="mm")

    # Layout: art_w=300, mat=12, frame=7 → full_w=338, full_h=488 (for 1.5 ratio)
    art_w = 300
    mat = 12
    fr = 7
    art_h = int(art_w * 1.5)  # 450
    fw = art_w + 2*mat + 2*fr   # 338
    fh = art_h + 2*mat + 2*fr   # 488
    label_h = 28
    gap = 20

    total_w = 2*fw + gap          # 696
    total_h = 2*(fh+label_h) + gap  # 1052
    start_x = (W - total_w) // 2   # 252
    start_y = 92

    frame_color = (139, 110, 80)
    mat_color = (252, 250, 247)

    for i, (art_path, label) in enumerate(zip(art_paths, labels)):
        col, row = i % 2, i // 2
        px = start_x + col*(fw + gap)
        py = start_y + row*(fh + label_h + gap)

        art = Image.open(art_path).convert('RGB')
        art_r = art.resize((art_w, art_h), Image.LANCZOS)

        shadow = Image.new('RGBA', (W, H), (0,0,0,0))
        ImageDraw.Draw(shadow).rectangle([px+8, py+10, px+fw+8, py+fh+10], fill=(0,0,0,55))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        canvas = Image.alpha_composite(canvas.convert('RGBA'), shadow).convert('RGB')
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([px, py, px+fw, py+fh], fill=frame_color)
        draw.rectangle([px+fr, py+fr, px+fr+art_w+2*mat, py+fr+art_h+2*mat], fill=mat_color)
        canvas.paste(art_r, (px+fr+mat, py+fr+mat))
        draw = ImageDraw.Draw(canvas)
        draw.text((px+fw//2, py+fh+14), label, font=fonts['label'], fill=(100,88,75), anchor="mm")

    canvas.save(out_path, 'JPEG', quality=92)
    print(f"  Gallery grid: {os.path.basename(out_path)}")


def create_size_guide(art_path, out_path):
    canvas_size = 1200
    bg_color = (245, 243, 239)
    frame_color = (139, 110, 80)
    mat_color = (252, 250, 247)
    text_color = (60, 55, 50)
    canvas = Image.new('RGB', (canvas_size, canvas_size), bg_color)
    art = Image.open(art_path).convert('RGB')
    draw = ImageDraw.Draw(canvas)
    fonts = _load_fonts()

    draw.text((canvas_size//2, 38), "AVAILABLE PRINT SIZES", font=fonts['h2'],
              fill=text_color, anchor="mm")
    draw.text((canvas_size//2, 68), "Download includes all sizes — print at home or at any print shop",
              font=fonts['sm'], fill=(120,110,100), anchor="mm")

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
        ImageDraw.Draw(shadow).rectangle([px+8, py+10, px+total_w+8, py+total_h+10], fill=(0,0,0,55))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        canvas = Image.alpha_composite(canvas.convert('RGBA'), shadow).convert('RGB')
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([px, py, px+total_w, py+total_h], fill=frame_color)
        draw.rectangle([px+frame_pad, py+frame_pad,
                        px+frame_pad+w+2*mat_pad, py+frame_pad+h+2*mat_pad], fill=mat_color)
        art_resized = art.resize((w, h), Image.LANCZOS)
        canvas.paste(art_resized, (px+frame_pad+mat_pad, py+frame_pad+mat_pad))
        draw = ImageDraw.Draw(canvas)
        draw.text((cx, py+total_h+18), label, font=fonts['body'], fill=text_color, anchor="mm")

    draw.text((canvas_size//2, canvas_size-35),
              "All sizes included • 300 DPI • Print-ready JPG files",
              font=fonts['sm'], fill=(120,110,100), anchor="mm")
    canvas.save(out_path, 'JPEG', quality=92)
    print(f"  Size guide: {os.path.basename(out_path)}")


def create_whats_included(art_path, out_path, title_text, price):
    W, H = 1200, 1200
    fonts = _load_fonts()
    accent = (139, 110, 80)
    dark = (45, 38, 32)
    mid = (100, 88, 75)

    canvas = Image.new('RGB', (W, H), (250, 248, 244))
    draw = ImageDraw.Draw(canvas)

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

    rx, ry = fx+fw+55, 80
    draw.text((rx, ry), "INSTANT DOWNLOAD", font=fonts['h1'], fill=accent)
    ry += 58
    draw.rectangle([rx, ry, W-50, ry+2], fill=accent)
    ry += 20
    draw.text((rx, ry), f"${price:.2f}", font=fonts['price'], fill=dark)
    ry += 80
    draw.text((rx, ry), "WHAT'S INCLUDED:", font=fonts['h2'], fill=dark)
    ry += 42
    for item in [
        "✓  High-res JPG files (300 DPI)",
        "✓  8 print sizes: 4×6 up to 24×36",
        "✓  Instant download after purchase",
        "✓  No waiting — no shipping",
        "✓  Print at home or any print shop",
        "✓  Personal use license included",
    ]:
        draw.text((rx, ry), item, font=fonts['body'], fill=mid)
        ry += 38
    ry += 10
    draw.rectangle([rx, ry, W-50, ry+2], fill=(210,200,188))
    ry += 22
    draw.text((rx, ry), "SIZES: 4×6 · 5×7 · 8×10 · 11×14 · 16×20 · 18×24 · 24×30 · 24×36\"",
              font=fonts['sm'], fill=mid)
    ry += 38
    draw.text((rx, ry), "FORMAT: JPG • RESOLUTION: 300 DPI • COLOR: sRGB", font=fonts['sm'], fill=mid)
    ry += 38
    draw.text((rx, ry), "© OnBrandCraftz  |  Personal use only", font=fonts['sm'], fill=(160,148,135))
    canvas.save(out_path, 'JPEG', quality=92)
    print(f"  What's Included: {os.path.basename(out_path)}")


def create_set_whats_included(art_paths, labels, out_path, set_title, price, save_amount):
    """What's included card showing all 4 pieces for a set listing."""
    W, H = 1200, 1200
    fonts = _load_fonts()
    accent = (139, 110, 80)
    dark = (45, 38, 32)
    mid = (100, 88, 75)
    frame_color = (139, 110, 80)
    mat_color = (252, 250, 247)

    canvas = Image.new('RGB', (W, H), (250, 248, 244))
    draw = ImageDraw.Draw(canvas)

    # Left: 2×2 mini grid of all 4 pieces
    art_w = 190
    mat = 8
    fr = 5
    art_h = int(art_w * 1.5)  # 285
    fw = art_w + 2*mat + 2*fr   # 216
    fh = art_h + 2*mat + 2*fr   # 311
    gap = 14
    lx_start = 45
    ly_start = (H - (2*fh+gap)) // 2

    for i, art_path in enumerate(art_paths):
        col, row = i % 2, i // 2
        px = lx_start + col*(fw+gap)
        py = ly_start + row*(fh+gap)
        art = Image.open(art_path).convert('RGB')
        art_r = art.resize((art_w, art_h), Image.LANCZOS)
        shadow = Image.new('RGBA', (W, H), (0,0,0,0))
        ImageDraw.Draw(shadow).rectangle([px+6, py+8, px+fw+6, py+fh+8], fill=(0,0,0,50))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        canvas = Image.alpha_composite(canvas.convert('RGBA'), shadow).convert('RGB')
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([px, py, px+fw, py+fh], fill=frame_color)
        draw.rectangle([px+fr, py+fr, px+fr+art_w+2*mat, py+fr+art_h+2*mat], fill=mat_color)
        canvas.paste(art_r, (px+fr+mat, py+fr+mat))
        draw = ImageDraw.Draw(canvas)

    # Right: text
    rx = lx_start + 2*fw + gap + 40
    ry = 75
    draw.text((rx, ry), "SET OF 4 PRINTS", font=fonts['h1'], fill=accent)
    ry += 58
    draw.rectangle([rx, ry, W-40, ry+2], fill=accent)
    ry += 20
    draw.text((rx, ry), f"${price:.2f}", font=fonts['price'], fill=dark)
    ry += 55
    draw.text((rx, ry), f"(Save ${save_amount:.2f} vs buying separately)", font=fonts['sm'], fill=(140,125,110))
    ry += 40
    draw.text((rx, ry), "WHAT'S INCLUDED:", font=fonts['h2'], fill=dark)
    ry += 40
    for label in labels:
        draw.text((rx, ry), f"✓  {label}", font=fonts['body'], fill=mid)
        ry += 36
    ry += 8
    draw.text((rx, ry), "Each print: 8 sizes from 4×6 to 24×36\"", font=fonts['body'], fill=mid)
    ry += 38
    draw.rectangle([rx, ry, W-40, ry+2], fill=(210,200,188))
    ry += 20
    draw.text((rx, ry), "FORMAT: JPG • 300 DPI • Instant Download • No shipping", font=fonts['sm'], fill=mid)
    ry += 36
    draw.text((rx, ry), "© OnBrandCraftz  |  Personal use only", font=fonts['sm'], fill=(160,148,135))

    canvas.save(out_path, 'JPEG', quality=92)
    print(f"  Set What's Included: {os.path.basename(out_path)}")


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
    try:
        with urllib.request.urlopen(urllib.request.Request(url_imgs, headers=auth_headers), timeout=15) as resp:
            existing = {img['rank']: img['listing_image_id']
                        for img in json.loads(resp.read()).get('results', [])}
    except Exception:
        existing = {}
    if rank in existing:
        url_del = (f"https://openapi.etsy.com/v3/application/shops/{shop_id}"
                   f"/listings/{listing_id}/images/{existing[rank]}")
        try:
            urllib.request.urlopen(urllib.request.Request(url_del, headers=auth_headers, method="DELETE"), timeout=15)
            time.sleep(0.3)
        except Exception:
            pass
    for attempt in range(3):
        try:
            client.upload_listing_image(listing_id, img_path, rank=rank)
            print(f"  Uploaded rank={rank}")
            return True
        except EtsyAPIError as e:
            if e.status == 401: refresh()
            elif e.status == 429: time.sleep(15)
            elif e.status == 500 and attempt < 2: time.sleep(5)
            else: print(f"  Upload rank={rank} failed: {e}"); return False
    return False


def upload_file(listing_id, file_path, rank=1):
    for attempt in range(3):
        try:
            result = client.upload_listing_file(listing_id, file_path, rank=rank)
            print(f"  File uploaded rank={rank} id={result.get('listing_file_id')}")
            return True
        except EtsyAPIError as e:
            if e.status == 401: refresh()
            elif e.status == 429: time.sleep(15)
            else: print(f"  File upload rank={rank} failed: {e}"); return False
    return False


def save_to_shop_data(lid, info):
    try:
        sdp = '/home/user/Etsy/data/shop_data.json'
        with open(sdp) as f:
            sd = json.load(f)
        sd.setdefault('listings', []).append({
            'id': str(lid), 'title': info['title'], 'price': info['price'],
            'type': 'wall_art', 'listing_type': 'download', 'state': 'active',
            'tags': info['tags'], 'taxonomy_id': 2078,
            'url': f'https://www.etsy.com/listing/{lid}/', 'views': 0,
            'quantity': 999, 'description': info['description'],
        })
        with open(sdp, 'w') as f:
            json.dump(sd, f, indent=2)
        print(f"  Saved to shop_data.json")
    except Exception as e:
        print(f"  WARNING: could not update shop_data.json: {e}")


# ── Description templates ─────────────────────────────────────────────────────

def make_description(hook, perfect_for, printing_tip=None, set_note=None):
    pt = printing_tip or (
        "• Matte or satin paper brings out the beautiful soft texture\n"
        "• A white or natural wood frame with wide white mat looks stunning\n"
        "• 11×14 or 16×20 shows the details at their best"
    )
    sn = ""
    if set_note:
        sn = f"""
━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ ALSO AVAILABLE AS A SET
━━━━━━━━━━━━━━━━━━━━━━━━
{set_note}
"""
    return f"""{hook}
{sn}
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
{perfect_for}

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
{pt}

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
A: Matte or satin paper is ideal for this art — it captures the texture without glare.

Q: Can I use this for commercial purposes?
A: This license covers personal use only. Contact us for commercial licensing.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use."""


def make_set_description(hook, piece_names, perfect_for, total_value, set_price):
    save = total_value - set_price
    pieces_list = "\n".join(f"✅ {n}" for n in piece_names)
    return f"""{hook}

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED IN THIS SET
━━━━━━━━━━━━━━━━━━━━━━━━
This set includes all 4 prints as instant digital downloads:
{pieces_list}

Total value if purchased separately: ${total_value:.2f}
You save ${save:.2f} with this bundle!

Each print includes 8 sizes: 4×6, 5×7, 8×10, 11×14, 16×20, 18×24, 24×30, 24×36"

━━━━━━━━━━━━━━━━━━━━━━━━
🏠 PERFECT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
{perfect_for}

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase and download your files instantly from Etsy
2. Choose your preferred size for each print (8 sizes per print)
3. Print at home, at Costco, Walgreens, Staples, or your local print shop
4. Frame all 4 in matching frames and hang as a gallery wall set

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 GALLERY WALL TIPS
━━━━━━━━━━━━━━━━━━━━━━━━
• For a gallery wall: print all 4 at 8×10 and use matching frames with wide white mats
• Arrange in a 2×2 square layout with 2–3 inches between frames
• All 4 pieces are designed to hang as a cohesive set with matching style and borders
• Each piece also looks beautiful displayed individually

━━━━━━━━━━━━━━━━━━━━━━━━
📄 FILE DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: High-resolution JPG (4 files, one per print)
• Resolution: 300 DPI (professional print quality)
• Sizes per print: 4×6, 5×7, 8×10, 11×14, 16×20, 18×24, 24×30, 24×36 inches
• Color profile: sRGB
• Delivery: Instant digital download — no physical item shipped

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this a physical item?
A: No — this is a digital download. You receive 4 JPG files to print yourself.

Q: Can I buy the prints individually?
A: Yes! Each print is also available separately in our shop if you only want one or two.

Q: What frame size should I use for a gallery wall?
A: 8×10 or 11×14 prints in matching frames work beautifully. Use frames with wide white mats for a gallery look.

Q: Can I print multiple copies of each?
A: Yes — for personal use in your own home, print as many copies of each print as you like.

Q: Can I use these for commercial purposes?
A: This license covers personal use only. Contact us for commercial licensing.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use."""


# ── Scene prompt helpers ──────────────────────────────────────────────────────

def scene_prompt(room_desc, wall_color, furniture_desc, lighting, style, focal="50mm"):
    return _scene_prompt(room_desc, wall_color, furniture_desc, lighting, style, focal=focal)


# ── Individual listing definitions ───────────────────────────────────────────

FOUR_SEASONS_SET_NOTE = (
    "This print is part of the Four Seasons Collection — a set of 4 coordinating prints "
    "(Spring, Summer, Autumn, Winter) designed to hang together as a beautiful gallery wall. "
    "Buy all 4 as a bundle and save — search 'Four Seasons Wall Art Set' in our shop."
)

COASTAL_SET_NOTE = (
    "This print is part of the Coastal Dreams Collection — a set of 4 coordinating ocean prints "
    "designed to hang together as a gallery wall. "
    "Buy all 4 as a bundle and save — search 'Coastal Dreams Wall Art Set' in our shop."
)

LISTINGS = {

    # ── DP1048: Spring Cherry Blossoms (Four Seasons Set — Spring) ────────────
    'DP1048': {
        'sku': 'OBC-WA-048',
        'title': 'Cherry Blossom Watercolor Print | Spring Wall Art | Botanical Floral Decor | Instant Download',
        'price': 5.99,
        'section': 'Botanical Art',
        'tags': [
            'cherry blossom art',
            'spring wall art',
            'botanical art print',
            'floral watercolor',
            'four seasons art',
            'japanese art print',
            'pink wall art',
            'printable wall art',
            'instant download',
            'digital download',
            'seasonal wall art',
            'flower art print',
            'gallery wall art',
        ],
        'art_prompt': (
            "Luminous watercolor painting of cherry blossom branches in full spring bloom, portrait orientation. "
            "Elegant arching boughs of sakura heavy with pale pink and white blossoms fill the composition — "
            "soft five-petaled flowers cluster in dense bouquets, some petals beginning to drift gently downward. "
            "A single plump honey bee visits a blossom cluster in the foreground. "
            "The background is a soft wash of pale blue sky and gentle misty green. "
            "Delicate palette: shell pink, soft white, blush rose, mint green, warm pale blue. "
            "Authentic watercolor: transparent luminous washes, soft wet-on-wet bleeding, visible paper texture, "
            "preserved white highlights on petals. Impressionistic, romantic, Japanese botanical style. "
            "Wide cream/ivory border margins. This is ONE of a cohesive four-print series — spring theme. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (140, 110, 85),
        'scene_a_prompt': scene_prompt(
            "A soft bright airy living room",
            "warm white",
            "a slim cream linen sofa with blush pink and sage botanical throw pillows, a small marble side table with a glass vase holding fresh cherry blossom branches, and a rattan floor lamp",
            "Bright soft natural window light from the left.",
            "Spring botanical home aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A feminine bedroom",
            "soft blush pink",
            "a low white nightstand with a small white ceramic vase holding one cherry blossom sprig, a pearl candle, and a linen-covered journal. White linen bedding visible below",
            "Soft morning natural light.",
            "Romantic spring bedroom aesthetic."
        ),
        'description': make_description(
            hook=(
                "🌸 Welcome spring into your home — this luminous watercolor cherry blossom print captures "
                "the fleeting beauty of sakura in full bloom, with soft pink petals and a visiting bee, "
                "painted in a romantic impressionistic watercolor style.\n\n"
                "Part of the Four Seasons Collection — beautiful alone or displayed as a set of four with "
                "Summer, Autumn, and Winter for a stunning gallery wall."
            ),
            perfect_for=(
                "• Living room, bedroom, or entryway with spring or botanical decor\n"
                "• Japanese or Asian-inspired interiors\n"
                "• Feminine spaces, nurseries, or reading nooks\n"
                "• Gallery wall as part of a Four Seasons collection\n"
                "• Mother's Day, birthday, or housewarming gift"
            ),
            set_note=FOUR_SEASONS_SET_NOTE,
        ),
    },

    # ── DP1049: Summer Sunflowers (Four Seasons Set — Summer) ─────────────────
    'DP1049': {
        'sku': 'OBC-WA-049',
        'title': 'Sunflower Watercolor Print | Summer Wall Art | Botanical Floral Decor | Instant Download',
        'price': 5.99,
        'section': 'Botanical Art',
        'tags': [
            'sunflower wall art',
            'summer wall art',
            'botanical art print',
            'floral watercolor',
            'four seasons art',
            'yellow wall art',
            'sunflower decor',
            'printable wall art',
            'instant download',
            'digital download',
            'seasonal wall art',
            'flower art print',
            'gallery wall art',
        ],
        'art_prompt': (
            "Vibrant luminous watercolor painting of sunflowers in full summer bloom, portrait orientation. "
            "Tall proud sunflowers with rich golden-yellow petals and dark velvety brown centers fill the composition "
            "— two large blooms dominate the foreground, smaller buds and green leaves fill the space behind. "
            "A yellow-and-black bumblebee rests on one of the large central petals. Bright warm summer sunlight "
            "glows through the petals making them luminous and translucent with golden warmth. "
            "The background fades into a soft warm blue summer sky with loose hints of green foliage. "
            "Radiant palette: sunflower gold, deep amber-brown, vibrant leaf green, warm sky blue, warm cream. "
            "Authentic watercolor: luminous transparent washes, rich golden petal tones, soft wet-on-wet background. "
            "Wide cream/ivory border margins. One of a four-print seasonal series — summer theme. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (135, 105, 70),
        'scene_a_prompt': scene_prompt(
            "A sunny farmhouse kitchen",
            "warm white shiplap",
            "a round light wood farmhouse dining table with a linen runner, a ceramic pitcher holding three large fresh sunflowers, a woven rattan bowl with lemons, and two cross-back wooden chairs",
            "Warm golden morning sunlight from a large window.",
            "Fresh bright farmhouse kitchen aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A cheerful bright living room",
            "warm cream",
            "a cream linen sofa with warm yellow and terracotta throw pillows, a small light oak side table with a sunflower in a clear glass bottle, and a wicker basket below",
            "Bright warm natural afternoon light.",
            "Sunny cottagecore living room aesthetic."
        ),
        'description': make_description(
            hook=(
                "🌻 Capture the radiant energy of summer — this luminous watercolor sunflower print shows "
                "proud golden blooms glowing in warm summer sunlight, painted with rich translucent washes "
                "and a visiting bumblebee.\n\n"
                "Part of the Four Seasons Collection — beautiful alone or hung as a set of four with "
                "Spring, Autumn, and Winter for a stunning gallery wall."
            ),
            perfect_for=(
                "• Kitchen, dining room, or sunny living space\n"
                "• Farmhouse, cottagecore, or country-inspired interiors\n"
                "• Bright rooms needing a warm pop of golden color\n"
                "• Gallery wall as part of a Four Seasons collection\n"
                "• Housewarming, birthday, or Mother's Day gift"
            ),
            set_note=FOUR_SEASONS_SET_NOTE,
        ),
    },

    # ── DP1050: Autumn Maple Forest (Four Seasons Set — Autumn) ───────────────
    'DP1050': {
        'sku': 'OBC-WA-050',
        'title': 'Autumn Maple Watercolor Print | Fall Wall Art | Nature Home Decor | Instant Download',
        'price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'autumn wall art',
            'fall wall decor',
            'maple tree art',
            'nature art print',
            'four seasons art',
            'watercolor fall',
            'orange wall art',
            'printable wall art',
            'instant download',
            'digital download',
            'seasonal wall art',
            'forest art print',
            'gallery wall art',
        ],
        'art_prompt': (
            "Breathtaking watercolor painting of autumn maple trees in peak fall color, portrait orientation. "
            "A sun-dappled forest path winds through glorious maple trees ablaze with color — fiery crimson, "
            "burnt orange, golden amber, and deep burgundy leaves fill the canopy overhead. "
            "Fallen leaves carpet the forest path below in warm russet and gold. Soft warm amber light filters "
            "through the canopy creating a magical dappled glow on the path. Two or three leaves drift gently "
            "downward in the foreground. The mood is peaceful, warm, and deeply autumnal. "
            "Rich warm palette: crimson red, burnt orange, golden amber, deep burgundy, warm brown, soft cream path. "
            "Authentic watercolor: luminous wet-on-wet sky color through canopy, loose gestural leaf shapes, "
            "layered transparent glazes building rich color depth. "
            "Wide cream/ivory border margins. One of a four-print seasonal series — autumn theme. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (120, 88, 58),
        'scene_a_prompt': scene_prompt(
            "A warm cozy living room",
            "warm terracotta orange",
            "a rust-colored velvet sofa with warm amber and cream throw pillows, a slim dark walnut side table with a beeswax candle and a small ceramic pumpkin, and a woven jute rug edge visible",
            "Warm late afternoon amber light.",
            "Cozy autumn home aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A rustic warm bedroom",
            "warm honey amber",
            "a dark walnut nightstand with a small brass lamp glowing warmly, a ceramic mug, and a few autumn leaves pressed in a small book. Warm linen bedding visible below",
            "Warm amber lamp and late afternoon light.",
            "Cozy autumn bedroom retreat."
        ),
        'description': make_description(
            hook=(
                "🍂 Bring the magic of peak autumn into your home — this luminous watercolor maple forest "
                "print captures a sun-dappled path through trees ablaze with crimson, amber, and gold, "
                "painted with rich layered watercolor depth.\n\n"
                "Part of the Four Seasons Collection — beautiful alone or hung as a set of four with "
                "Spring, Summer, and Winter for a stunning gallery wall."
            ),
            perfect_for=(
                "• Living room, study, or bedroom with warm autumn tones\n"
                "• Rustic, farmhouse, or nature-inspired interiors\n"
                "• Fall seasonal decor (beautiful year-round too)\n"
                "• Gallery wall as part of a Four Seasons collection\n"
                "• Housewarming, birthday, or autumn gift"
            ),
            printing_tip=(
                "• Matte paper best captures the rich autumn color depth\n"
                "• A dark walnut, antique gold, or warm wood frame is stunning\n"
                "• 16×20 or larger shows the beautiful forest path detail"
            ),
            set_note=FOUR_SEASONS_SET_NOTE,
        ),
    },

    # ── DP1051: Winter Birch & Snow (Four Seasons Set — Winter) ───────────────
    'DP1051': {
        'sku': 'OBC-WA-051',
        'title': 'Winter Birch Tree Watercolor Print | Snow Wall Art | Woodland Decor | Instant Download',
        'price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'winter wall art',
            'birch tree art',
            'snow art print',
            'nature art print',
            'four seasons art',
            'watercolor winter',
            'white wall art',
            'printable wall art',
            'instant download',
            'digital download',
            'seasonal wall art',
            'woodland art print',
            'gallery wall art',
        ],
        'art_prompt': (
            "Serene and beautiful watercolor painting of silver birch trees in a peaceful winter snowfall, "
            "portrait orientation. Slender white-silver birch trunks with characteristic dark markings rise "
            "elegantly through the composition, their bare delicate branches dusted with fresh white snow. "
            "Clusters of bright red holly berries and waxy green holly leaves provide the only color "
            "accent against the serene winter palette. Soft white snowflakes fall gently through the air. "
            "The background fades into soft cool blue-silver winter mist, creating beautiful aerial depth. "
            "Cool serene palette: pure white snow, silver-white birch bark, cool blue-silver sky, "
            "deep forest green holly, vivid crimson holly berries. "
            "Authentic watercolor: transparent cool washes, fine dark birch bark details, preserved bright "
            "white snow highlights, soft misty background depth. "
            "Wide cream/ivory border margins. One of a four-print seasonal series — winter theme. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (105, 118, 130),
        'scene_a_prompt': scene_prompt(
            "A serene cool-toned bedroom",
            "soft blue-gray",
            "a slim white nightstand with a silver lamp glowing softly, a smooth white quartz crystal, and a small white ceramic vase with a single bare silver birch twig. White linen bedding visible below",
            "Cool soft ambient light, peaceful and serene.",
            "Serene Scandinavian winter bedroom aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A cozy rustic cabin living room",
            "warm cream",
            "a log-style armchair with a cream and pale blue plaid wool throw, a small wood side table with a lantern candle glowing amber, and a small stack of nature books with a sprig of holly beside them",
            "Warm amber candle and lantern glow.",
            "Cozy winter cabin retreat aesthetic."
        ),
        'description': make_description(
            hook=(
                "❄️ Bring the peaceful stillness of winter into your home — this luminous watercolor birch "
                "tree print captures elegant silver birch trunks dusted in fresh snow, with vivid red holly "
                "berries as the only color accent in a serene winter forest.\n\n"
                "Part of the Four Seasons Collection — beautiful alone or hung as a set of four with "
                "Spring, Summer, and Autumn for a stunning gallery wall."
            ),
            perfect_for=(
                "• Bedroom, living room, or hallway in a cool-toned or Scandinavian-style home\n"
                "• Rustic cabin, lodge, or winter retreat\n"
                "• Holiday and winter seasonal decor (beautiful year-round)\n"
                "• Gallery wall as part of a Four Seasons collection\n"
                "• Holiday gift, Christmas gift, or winter housewarming"
            ),
            printing_tip=(
                "• Matte paper best captures the soft, cool watercolor quality\n"
                "• A slim silver, white, or pale birch frame with wide white mat is stunning\n"
                "• 16×20 or larger brings out the beautiful birch bark detail"
            ),
            set_note=FOUR_SEASONS_SET_NOTE,
        ),
    },

    # ── DP1052: Sea Turtle (Coastal Dreams Set) ───────────────────────────────
    'DP1052': {
        'sku': 'OBC-WA-052',
        'title': 'Sea Turtle Watercolor Print | Ocean Wall Art | Coastal Home Decor | Instant Download',
        'price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'sea turtle art',
            'ocean wall art',
            'coastal wall decor',
            'turtle art print',
            'coastal art set',
            'beach home decor',
            'underwater art',
            'printable wall art',
            'instant download',
            'digital download',
            'marine life art',
            'aqua wall art',
            'gallery wall art',
        ],
        'art_prompt': (
            "Luminous watercolor painting of a beautiful sea turtle gliding through clear tropical ocean water, "
            "portrait orientation. A large graceful green sea turtle swims directly toward the viewer, its "
            "beautifully patterned shell rendered in rich olive, amber, and warm brown tones, spotted flippers "
            "outstretched as it glides effortlessly. Soft shafts of golden sunlight pierce the turquoise water "
            "above, creating shimmering light patterns on the turtle and ocean floor below. "
            "Small tropical fish in bright orange and yellow dart past in the background. Loose hints of "
            "soft coral and sea grass in the far background. "
            "Luminous palette: crystal turquoise-aqua water, warm olive-amber shell, golden sunbeams, "
            "vivid small fish accents, soft coral hint. "
            "Authentic watercolor: luminous transparent water washes, glowing sunlight rays, loose painterly style. "
            "Wide cream/ivory border margins. One of a four-print coastal series. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (70, 110, 120),
        'scene_a_prompt': scene_prompt(
            "A bright coastal living room",
            "clean bright white",
            "a natural fiber linen sofa with aqua and cream coastal throw pillows, a small driftwood side table with a glass bowl of smooth sea glass pebbles, and a tall sea grass floor lamp",
            "Bright natural coastal daylight.",
            "Fresh coastal beach house aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A calm master bedroom",
            "deep navy blue",
            "a low upholstered headboard in cream linen with aqua and navy pillow arrangement visible, and a slim white nightstand with a brushed brass lamp and a small white coral piece",
            "Soft warm ambient lamp light.",
            "Coastal luxury bedroom aesthetic."
        ),
        'description': make_description(
            hook=(
                "🐢 Bring the serene beauty of the ocean deep into your home — this luminous watercolor "
                "print captures a graceful sea turtle gliding through crystal turquoise water, golden "
                "sunbeams streaming down through the surface above.\n\n"
                "Part of the Coastal Dreams Collection — beautiful alone or hung as a set of four with "
                "Lighthouse, Coral Reef, and Pelican prints for a stunning coastal gallery wall."
            ),
            perfect_for=(
                "• Coastal bedroom, master suite, or beach house living room\n"
                "• Bathroom, hallway, or entryway with nautical or ocean decor\n"
                "• Vacation home, lake house, or seaside cottage\n"
                "• Gallery wall as part of the Coastal Dreams collection\n"
                "• Gift for ocean lovers, divers, snorkelers, or sea turtle fans"
            ),
            printing_tip=(
                "• Matte paper best preserves the luminous watercolor water quality\n"
                "• A slim navy, driftwood, or natural wood frame with white mat looks stunning\n"
                "• 16×20 or larger shows the turtle shell pattern and water detail at its best"
            ),
            set_note=COASTAL_SET_NOTE,
        ),
    },

    # ── DP1053: Lighthouse at Dawn (Coastal Dreams Set) ───────────────────────
    'DP1053': {
        'sku': 'OBC-WA-053',
        'title': 'Lighthouse Watercolor Print | Coastal Wall Art | Nautical Home Decor | Instant Download',
        'price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'lighthouse wall art',
            'coastal wall art',
            'nautical decor',
            'lighthouse print',
            'coastal art set',
            'beach house art',
            'seascape print',
            'printable wall art',
            'instant download',
            'digital download',
            'ocean decor',
            'maritime art',
            'gallery wall art',
        ],
        'art_prompt': (
            "Romantic and beautiful watercolor painting of a classic lighthouse on a rocky coastal shore at dawn, "
            "portrait orientation. A tall white-painted lighthouse with a red lantern cap stands on jagged granite "
            "rocks at the water's edge, its warm beam of light just beginning to fade as morning breaks. "
            "The sky is painted in gorgeous soft dawn gradients: deep violet at the top melting through rose pink, "
            "peach, and warm golden amber at the horizon where the sun is just rising over the ocean. "
            "The ocean below reflects the dawn colors in shimmering warm gold and pink waves. A small wooden "
            "sailing skiff rests on the rocks in the foreground. "
            "Luminous palette: deep violet-blue sky, rose and peach dawn, golden amber horizon, "
            "white lighthouse with red top, dark granite rocks, warm golden water reflections. "
            "Authentic watercolor: luminous wet-on-wet sky washes, dawn color bleeds, "
            "clean architectural lighthouse edges. "
            "Wide cream/ivory border margins. One of a four-print coastal series. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (85, 105, 120),
        'scene_a_prompt': scene_prompt(
            "A warm coastal dining room",
            "warm gray-blue",
            "a round white dining table with four navy linen chairs, a small centerpiece of a glass lantern with a candle and two white pillar candles beside it, and a woven jute rug edge visible below",
            "Soft warm ambient light.",
            "Coastal cottage dining room aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A bright airy hallway or entryway",
            "clean white",
            "a slim natural wood console table with a small ship wheel decorative piece, a round glass vase with dried sea grass, and a smooth white river stone",
            "Bright natural light from a side window.",
            "Clean coastal entryway aesthetic."
        ),
        'description': make_description(
            hook=(
                "🏠 Capture the romantic beauty of the coast — this luminous watercolor lighthouse print "
                "shows a classic white lighthouse standing on rocky granite shores as gorgeous violet, "
                "rose, and golden dawn colors fill the sky behind it.\n\n"
                "Part of the Coastal Dreams Collection — beautiful alone or hung as a set of four with "
                "Sea Turtle, Coral Reef, and Pelican prints for a stunning coastal gallery wall."
            ),
            perfect_for=(
                "• Living room, dining room, or hallway with coastal or nautical decor\n"
                "• Vacation home, beach cottage, or lake house\n"
                "• Navy or coastal color scheme rooms\n"
                "• Gallery wall as part of the Coastal Dreams collection\n"
                "• Gift for sailors, boaters, coastal lovers, or New England enthusiasts"
            ),
            set_note=COASTAL_SET_NOTE,
        ),
    },

    # ── DP1054: Coral Reef Tropical Fish (Coastal Dreams Set) ─────────────────
    'DP1054': {
        'sku': 'OBC-WA-054',
        'title': 'Coral Reef Watercolor Print | Tropical Fish Ocean Art | Coastal Decor | Instant Download',
        'price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'coral reef art',
            'tropical fish art',
            'ocean wall art',
            'coastal wall decor',
            'coastal art set',
            'underwater art',
            'beach house art',
            'printable wall art',
            'instant download',
            'digital download',
            'marine art print',
            'colorful wall art',
            'gallery wall art',
        ],
        'art_prompt': (
            "Vibrant and beautiful watercolor painting of a colorful coral reef underwater scene, portrait orientation. "
            "A thriving shallow coral reef bursts with life and color — soft pink and orange branching corals, "
            "sea anemones waving gently, bright purple fan coral, golden brain coral, and vivid orange sponges. "
            "Among the coral swim a school of bright orange-and-white clownfish, a blue tang with vivid electric "
            "blue and yellow, a yellow butterflyfish, and a parrotfish in turquoise and green. "
            "Sunlight streams down from the surface above, creating shimmering caustic light patterns across the reef. "
            "The water above shades from deep aqua-blue to lighter turquoise near the surface. "
            "Vibrant palette: electric turquoise-aqua water, vivid orange clownfish, royal blue tang, "
            "pink-coral corals, golden sunbeams, purple sea fans. "
            "Authentic watercolor: luminous water washes, vibrant tropical fish colors, painterly coral forms. "
            "Wide cream/ivory border margins. One of a four-print coastal series. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (75, 115, 115),
        'scene_a_prompt': scene_prompt(
            "A bright tropical-inspired living room",
            "clean white",
            "a white linen sofa with aqua, coral, and white tropical throw pillows, a small bleached wood side table with a glass bowl holding colorful sea glass pieces, and a trailing pothos plant in a white ceramic pot",
            "Bright natural tropical light.",
            "Bright coastal tropical aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A cheerful kids room or playroom",
            "soft sky blue",
            "a low white bookshelf with colorful children's books, a small plush sea turtle toy on top, and a cheerful aqua beanbag chair beside it",
            "Bright soft natural light.",
            "Fun colorful kids coastal room."
        ),
        'description': make_description(
            hook=(
                "🐠 Dive into a world of color — this vibrant watercolor coral reef print captures a thriving "
                "underwater kingdom of clownfish, blue tangs, rainbow corals, and sea fans in a sun-drenched "
                "tropical reef, painted with luminous watercolor vibrancy.\n\n"
                "Part of the Coastal Dreams Collection — beautiful alone or hung as a set of four with "
                "Sea Turtle, Lighthouse, and Pelican prints for a stunning coastal gallery wall."
            ),
            perfect_for=(
                "• Living room, bathroom, or bedroom with tropical or ocean decor\n"
                "• Kids room, playroom, or nursery with ocean theme\n"
                "• Vacation home, beach house, or sunroom\n"
                "• Gallery wall as part of the Coastal Dreams collection\n"
                "• Gift for divers, snorkelers, marine biologists, or ocean enthusiasts"
            ),
            printing_tip=(
                "• Matte paper best captures the luminous watercolor vibrancy\n"
                "• A slim driftwood or natural wood frame lets the colors shine\n"
                "• 16×20 or larger shows the individual fish and coral detail at its best"
            ),
            set_note=COASTAL_SET_NOTE,
        ),
    },

    # ── DP1055: Brown Pelican at Golden Hour (Coastal Dreams Set) ─────────────
    'DP1055': {
        'sku': 'OBC-WA-055',
        'title': 'Pelican Watercolor Print | Coastal Bird Art | Beach Wall Decor | Instant Download',
        'price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'pelican wall art',
            'coastal bird art',
            'beach wall decor',
            'bird art print',
            'coastal art set',
            'watercolor bird',
            'nautical wall art',
            'printable wall art',
            'instant download',
            'digital download',
            'golden hour art',
            'coastal home art',
            'gallery wall art',
        ],
        'art_prompt': (
            "Beautiful and atmospheric watercolor painting of a brown pelican perched on a weathered wooden pier "
            "post at golden hour, portrait orientation. A large magnificent pelican sits with calm dignity on "
            "the top of a salt-worn wooden dock post — its rich brown-and-cream feathers painted with fine "
            "luminous watercolor detail, distinctive long orange-yellow beak with throat pouch, white neck "
            "and crown catching the warm evening light. "
            "Behind the pelican: a gorgeous glowing golden hour ocean sunset — the sky painted in rich warm "
            "washes of deep amber, burnt orange, coral pink, and soft violet, their colors reflected as "
            "shimmering ribbons of golden light on the calm evening ocean below. "
            "The wooden pier post and two weathered ropes leading away create diagonal leading lines. "
            "Warm glowing palette: rich amber-golden sunset, coral-pink sky, soft violet upper sky, "
            "warm brown pelican, golden ocean reflections. "
            "Authentic watercolor: luminous wet-on-wet sunset washes, fine bird feather detail. "
            "Wide cream/ivory border margins. One of a four-print coastal series. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (115, 95, 70),
        'scene_a_prompt': scene_prompt(
            "A warm coastal bedroom",
            "warm sandy beige",
            "a natural linen upholstered headboard with cream and amber throw pillows, and a slim light driftwood nightstand with a woven rattan lamp glowing warm and a small smooth beach stone",
            "Warm amber sunset lamp light.",
            "Coastal sunset bedroom aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A warm rustic beach house living room",
            "warm white with wood plank ceiling visible at the top edge",
            "a weathered driftwood coffee table with a woven rope basket, a small piece of white coral, and two pillar candles. A cream sailcloth sofa edge visible at the sides",
            "Warm golden afternoon coastal light.",
            "Rustic beach cottage living room."
        ),
        'description': make_description(
            hook=(
                "🦅 Capture the soulful beauty of the coast at golden hour — this luminous watercolor print "
                "shows a magnificent brown pelican perched on a weathered pier post against a spectacular "
                "amber, coral, and violet sunset sky reflected in the still ocean below.\n\n"
                "Part of the Coastal Dreams Collection — beautiful alone or hung as a set of four with "
                "Sea Turtle, Lighthouse, and Coral Reef prints for a stunning coastal gallery wall."
            ),
            perfect_for=(
                "• Coastal bedroom, living room, or beach house of any style\n"
                "• Warm-toned rooms, sunset or golden hour aesthetic spaces\n"
                "• Vacation home, beach cottage, or Florida/Gulf Coast inspired decor\n"
                "• Gallery wall as part of the Coastal Dreams collection\n"
                "• Gift for birdwatchers, coastal lovers, or pelican fans"
            ),
            printing_tip=(
                "• Matte paper best captures the warm sunset watercolor tones\n"
                "• A driftwood, natural rope-wrapped, or warm wood frame is stunning\n"
                "• 16×20 or larger shows the golden pelican and sunset detail beautifully"
            ),
            set_note=COASTAL_SET_NOTE,
        ),
    },

    # ── DP1056: Red Fox in Autumn Forest (standalone) ─────────────────────────
    'DP1056': {
        'sku': 'OBC-WA-056',
        'title': 'Red Fox Watercolor Print | Woodland Animal Art | Autumn Forest Decor | Instant Download',
        'price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'fox wall art',
            'red fox print',
            'woodland animal',
            'autumn wall art',
            'nature art print',
            'fox decor',
            'forest animal art',
            'printable wall art',
            'instant download',
            'digital download',
            'wildlife art',
            'fox lover gift',
            'rustic home art',
        ],
        'art_prompt': (
            "Stunning and atmospheric watercolor painting of a red fox sitting in an autumn forest at golden hour, "
            "portrait orientation. A beautiful red fox with brilliant russet-orange fur, white chest, and black "
            "legs sits alert and graceful among fallen autumn leaves, looking directly at the viewer with "
            "intelligent amber eyes. The fox's fur is painted with fine luminous watercolor strokes capturing "
            "the rich texture and warmth of each flame-colored hair. "
            "Surrounding the fox: a carpet of fallen maple leaves in crimson, amber, and gold. "
            "The forest background shows soft-focus birch and oak trees in warm autumnal hues — orange, gold, "
            "and rust red — with golden afternoon light filtering through the canopy. "
            "A single orange maple leaf falls gently in the foreground. "
            "Rich warm palette: brilliant fox orange-red, pure white, jet black, amber-golden forest, "
            "crimson and gold fallen leaves. "
            "Authentic watercolor: luminous transparent washes, fine fur texture, loose atmospheric forest background. "
            "Wide cream/ivory border margins. Museum-quality wildlife art. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (120, 88, 58),
        'scene_a_prompt': scene_prompt(
            "A warm rustic living room",
            "warm honey amber",
            "a low dark leather sofa with warm rust orange and cream throw pillows, a small walnut side table with a beeswax candle and a small decorative fox figurine, and a plaid wool throw draped over one arm",
            "Warm amber late afternoon light.",
            "Cozy rustic cabin living room aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A cozy study or home office",
            "warm cream with dark wood panel trim visible at side edges",
            "a dark walnut desk with a small brass lamp glowing warmly, a stack of hardcover nature field guides, and a small ceramic animal figurine",
            "Warm amber desk lamp light.",
            "Cozy dark academia study aesthetic."
        ),
        'description': make_description(
            hook=(
                "🦊 Bring the wild beauty of the forest into your home — this luminous watercolor fox print "
                "captures a brilliant red fox sitting in a golden autumn forest, painted with extraordinary "
                "fur detail and warm, atmospheric light filtering through the leaf canopy.\n\n"
                "A stunning piece for nature lovers, fox enthusiasts, and anyone who loves the rich, warm "
                "magic of autumn woodland life."
            ),
            perfect_for=(
                "• Living room, study, or bedroom in a rustic, cabin, or nature-inspired home\n"
                "• Autumn-themed decor or warm-toned rooms\n"
                "• Gift for fox lovers, wildlife enthusiasts, or nature art collectors\n"
                "• Nursery or children's room with woodland or forest theme\n"
                "• Farmhouse, cottagecore, or dark academia aesthetic spaces"
            ),
            printing_tip=(
                "• Matte paper best captures the warm fox fur and autumn leaf detail\n"
                "• A dark walnut, rustic wood, or antique gold frame suits the woodland aesthetic\n"
                "• 16×20 or larger brings out the luminous fox fur and fallen leaf detail"
            ),
        ),
    },

    # ── DP1057: Vintage Paris Café at Dusk (standalone) ───────────────────────
    'DP1057': {
        'sku': 'OBC-WA-057',
        'title': 'Paris Café Watercolor Print | French Wall Art | Romantic Home Decor | Instant Download',
        'price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'paris wall art',
            'french cafe art',
            'paris art print',
            'romantic wall art',
            'france home decor',
            'french country art',
            'travel art print',
            'printable wall art',
            'instant download',
            'digital download',
            'eiffel tower art',
            'parisian decor',
            'city art print',
        ],
        'art_prompt': (
            "Romantic and atmospheric watercolor painting of a classic Parisian café at blue dusk, portrait orientation. "
            "A charming French café with a dark forest green awning and gold lettering faces a cobblestone Paris "
            "street — two small round bistro tables with wicker chairs sit on the sidewalk outside, each with "
            "a small candle in a glass and a glass of wine glowing amber in the warm café light. "
            "Through the café windows, warm amber interior light spills out onto the damp cobblestones. "
            "A chestnut tree with autumn-gold leaves frames the upper left. In the soft-focus background, "
            "the silhouette of the Eiffel Tower glows softly in the dusk sky. "
            "The sky is a gorgeous Parisian blue-hour gradient: deep blue-violet at the top, soft teal-blue "
            "at the horizon, with the last warm amber glow of sunset behind the Eiffel Tower. "
            "Romantic palette: deep teal-blue evening sky, warm amber café lights, forest green awning, "
            "golden autumn leaves, soft cobblestone gray, glowing violet dusk sky. "
            "Authentic watercolor: luminous wet-on-wet blue-hour sky, warm glowing interior light, "
            "loose impressionistic café scene, romantic and painterly atmosphere. "
            "Wide cream/ivory border margins. Museum-quality romantic city scene. No text."
        ),
        'art_size': '1024x1536',
        'frame_color': (95, 85, 70),
        'scene_a_prompt': scene_prompt(
            "A romantic French-inspired dining room",
            "warm cream with ornate molding visible at ceiling edge",
            "a round marble-top bistro table with two rattan bistro chairs, a small vase of fresh red roses, a gold candle holder with a lit taper candle, and a glass of red wine",
            "Warm amber candlelight and evening lamp light.",
            "Romantic Parisian bistro dining room aesthetic."
        ),
        'scene_b_prompt': scene_prompt(
            "A cozy romantic bedroom",
            "soft dove gray",
            "a slim black iron nightstand with a small French table lamp glowing warmly, a red hardcover novel, and a white ceramic espresso cup on a saucer. White linen bedding visible below",
            "Warm romantic amber lamp light.",
            "Romantic Parisian bedroom aesthetic."
        ),
        'description': make_description(
            hook=(
                "🗼 Bring the romance of Paris into your home — this luminous watercolor print captures a "
                "classic Parisian café at blue dusk, warm amber light spilling onto rain-damp cobblestones, "
                "the Eiffel Tower glowing softly in the violet twilight behind.\n\n"
                "Perfect for Francophiles, travel art lovers, and anyone who dreams of a quiet evening "
                "at a candlelit café in the City of Light."
            ),
            perfect_for=(
                "• Dining room, living room, or romantic bedroom with French or travel decor\n"
                "• Kitchen or breakfast nook with a Parisian café aesthetic\n"
                "• French country, eclectic, or romantic-styled interiors\n"
                "• Office, studio, or creative space needing a European romantic touch\n"
                "• Gift for Paris lovers, travelers, Francophiles, or romantic art collectors"
            ),
            printing_tip=(
                "• Matte paper best captures the moody blue-hour watercolor atmosphere\n"
                "• A slim black iron, dark antique gold, or dark walnut frame is stunning\n"
                "• 16×20 or larger shows the atmospheric café scene and Eiffel Tower detail beautifully"
            ),
        ),
    },
}


# ── Set bundle definitions ────────────────────────────────────────────────────

SETS = {
    'FOUR-SEASONS-SET': {
        'sku': 'OBC-WA-SET-FS',
        'pids': ['DP1048', 'DP1049', 'DP1050', 'DP1051'],
        'labels': ['Spring', 'Summer', 'Autumn', 'Winter'],
        'title': 'Four Seasons Wall Art Set | Set of 4 Watercolor Prints | Gallery Wall Bundle | Instant Download',
        'price': 17.99,
        'individual_price': 5.99,
        'section': 'Botanical Art',
        'tags': [
            'four seasons art',
            'wall art set of 4',
            'seasonal wall art',
            'botanical art set',
            'watercolor bundle',
            'gallery wall art',
            'printable art set',
            'instant download',
            'digital download',
            'nature art bundle',
            'set of 4 prints',
            'home decor set',
            'wall art bundle',
        ],
        'gallery_title': 'Four Seasons Collection',
        'gallery_subtitle': 'Spring · Summer · Autumn · Winter',
        'frame_color': (135, 108, 78),
        'scene_a_prompt': scene_prompt(
            "A warm elegant living room",
            "warm cream linen",
            "a cream linen sofa with botanical green and warm amber throw pillows, a light oak coffee table with a small stack of art books and a glass vase of mixed seasonal flowers, and a slim brass floor lamp",
            "Warm soft natural daylight from the left.",
            "Warm botanical home, gallery wall aesthetic.",
            focal="35mm"
        ),
        'scene_b_prompt': scene_prompt(
            "A cozy dining room",
            "warm sage green",
            "a round light oak dining table with four linen chairs, a small centerpiece of a wooden candle holder with a beeswax pillar candle and a few seasonal botanical sprigs, and a rattan pendant lamp partially visible",
            "Warm natural afternoon light.",
            "Cottagecore botanical dining room, gallery wall aesthetic.",
            focal="35mm"
        ),
        'piece_names': [
            'Spring Cherry Blossoms — Watercolor Print',
            'Summer Sunflowers — Watercolor Print',
            'Autumn Maple Forest — Watercolor Print',
            'Winter Birch & Snow — Watercolor Print',
        ],
        'description': None,  # built below
    },
    'COASTAL-SET': {
        'sku': 'OBC-WA-SET-CO',
        'pids': ['DP1052', 'DP1053', 'DP1054', 'DP1055'],
        'labels': ['Sea Turtle', 'Lighthouse', 'Coral Reef', 'Pelican'],
        'title': 'Coastal Dreams Art Set | Set of 4 Ocean Prints | Beach Gallery Wall Bundle | Instant Download',
        'price': 17.99,
        'individual_price': 5.99,
        'section': 'Landscape and Nature Art',
        'tags': [
            'coastal art set',
            'wall art set of 4',
            'beach art bundle',
            'ocean art prints',
            'gallery wall art',
            'nautical art set',
            'printable art set',
            'instant download',
            'digital download',
            'beach house decor',
            'set of 4 prints',
            'coastal home art',
            'wall art bundle',
        ],
        'gallery_title': 'Coastal Dreams Collection',
        'gallery_subtitle': 'Sea Turtle · Lighthouse · Coral Reef · Pelican',
        'frame_color': (80, 108, 120),
        'scene_a_prompt': scene_prompt(
            "A bright white coastal living room",
            "bright white",
            "a natural linen sofa with aqua, navy, and cream coastal pillows, a small driftwood and glass coffee table with a bowl of sea glass and two white pillar candles, and a sea grass floor lamp to the right",
            "Bright natural coastal daylight.",
            "Fresh beach house, gallery wall aesthetic.",
            focal="35mm"
        ),
        'scene_b_prompt': scene_prompt(
            "A calm coastal master bedroom",
            "deep navy blue",
            "a low cream upholstered headboard with navy and white linen pillows, and a slim white nightstand with a driftwood lamp, a small piece of white coral, and a smooth river stone",
            "Soft ambient lamp light, moody coastal atmosphere.",
            "Coastal luxury bedroom, gallery wall aesthetic.",
            focal="35mm"
        ),
        'piece_names': [
            'Sea Turtle in Turquoise Ocean — Watercolor Print',
            'Lighthouse at Dawn — Watercolor Print',
            'Coral Reef & Tropical Fish — Watercolor Print',
            'Brown Pelican at Golden Hour — Watercolor Print',
        ],
        'description': None,
    },
}

# Build set descriptions
for set_key, s in SETS.items():
    total_value = s['individual_price'] * 4
    if set_key == 'FOUR-SEASONS-SET':
        hook = (
            "🌸🌻🍂❄️ Celebrate every season — this complete Four Seasons watercolor print set includes all 4 "
            "beautifully coordinated prints (Spring Cherry Blossoms, Summer Sunflowers, Autumn Maple Forest, "
            "Winter Birch & Snow), designed to hang together as a stunning seasonal gallery wall.\n\n"
            "Each print is painted in a cohesive watercolor style with wide cream borders — perfect together, "
            "beautiful individually. Save $6 versus buying each print separately."
        )
        perfect_for = (
            "• Gallery wall in a living room, hallway, staircase, or bedroom\n"
            "• Any room that celebrates nature and the changing seasons\n"
            "• Botanical, cottagecore, farmhouse, or nature-inspired interiors\n"
            "• A complete, ready-to-hang art collection — no hunting for matching pieces\n"
            "• Housewarming, birthday, Mother's Day, or nature lover's gift"
        )
    else:
        hook = (
            "🐢🏠🐠🦅 Bring the full beauty of the coast into your home — this complete Coastal Dreams "
            "watercolor print set includes all 4 beautifully coordinated ocean prints (Sea Turtle, Lighthouse, "
            "Coral Reef, and Pelican at Golden Hour), designed to hang together as a stunning coastal gallery wall.\n\n"
            "Each print is painted in a cohesive watercolor style with wide cream borders — perfect together, "
            "beautiful individually. Save $6 versus buying each print separately."
        )
        perfect_for = (
            "• Gallery wall in a coastal living room, bedroom, hallway, or beach house\n"
            "• Any room with ocean, nautical, or beach-inspired decor\n"
            "• Vacation home, lake house, or seaside cottage\n"
            "• A complete, ready-to-hang coastal art collection\n"
            "• Housewarming, birthday, or ocean lover's gift"
        )
    s['description'] = make_set_description(
        hook=hook,
        piece_names=s['piece_names'],
        perfect_for=perfect_for,
        total_value=total_value,
        set_price=s['price'],
    )


# ── Individual listing runner ─────────────────────────────────────────────────

def run_listing(pid, info, post_to_etsy=True):
    out_dir = os.path.join(ART_DIR, f'{pid}_listing_images')
    art_path = os.path.join(ART_DIR, f'{pid}.jpg')
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"[{pid}] {info['title'][:65]}...")
    print(f"{'='*60}")

    # 1. Art
    print(f"\n[1] Art...")
    if not os.path.exists(art_path):
        ok = gen_image(info['art_prompt'], art_path, size=info['art_size'], quality="high")
        if not ok:
            print(f"  FAILED art generation for {pid} — skipping")
            return None
        time.sleep(4)
    else:
        print(f"  Exists: {os.path.basename(art_path)}")

    # 2. Scene A
    print(f"\n[2] Scene A...")
    bg_a = os.path.join(out_dir, 'bg_lifestyle_scene_A.jpg')
    scene_a = os.path.join(out_dir, 'lifestyle_scene_A.jpg')
    if not os.path.exists(bg_a):
        ok = gen_image(info['scene_a_prompt'], bg_a, size="1024x1024", quality="high")
        if ok: time.sleep(3)
    else:
        print(f"  Background exists.")
    if os.path.exists(bg_a):
        composite_smart(bg_a, art_path, scene_a, frame_color=info.get('frame_color', (139,110,80)))

    # 3. Scene B
    print(f"\n[3] Scene B...")
    bg_b = os.path.join(out_dir, 'bg_lifestyle_scene_B.jpg')
    scene_b = os.path.join(out_dir, 'lifestyle_scene_B.jpg')
    if not os.path.exists(bg_b):
        ok = gen_image(info['scene_b_prompt'], bg_b, size="1024x1024", quality="high")
        if ok: time.sleep(3)
    else:
        print(f"  Background exists.")
    if os.path.exists(bg_b):
        composite_smart(bg_b, art_path, scene_b, frame_color=info.get('frame_color', (139,110,80)))

    # 4. Room templates
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
    create_whats_included(art_path, wi_path, info['title'].split('|')[0].strip(), info['price'])

    all_images = [
        (scene_a, 1), (scene_b, 2),
        (rooms['living_room'], 3), (rooms['kitchen_dining'], 4), (rooms['entryway'], 5),
        (sg_path, 6), (wi_path, 7), (art_path, 8),
    ]

    print(f"\n{'─'*40}")
    for label, (path, rank) in zip(
        ['Scene A','Scene B','Living Room','Kitchen','Entryway','Size Guide',"What's Incl.",'Art File'],
        all_images
    ):
        sz = os.path.getsize(path)//1024 if os.path.exists(path) else 0
        ok = '✓' if os.path.exists(path) else '✗ MISSING'
        print(f"  rank {rank}: {label:20s} {ok} ({sz}KB)")

    if not post_to_etsy:
        print(f"\n[PREVIEW] Images saved for {pid}. Not posting to Etsy.")
        return {'pid': pid, 'out_dir': out_dir}

    # 7. Post to Etsy
    print(f"\n[7] Posting to Etsy...")
    refresh()

    section_id = client.get_or_create_section(info['section'])
    print(f"  Section '{info['section']}': id={section_id}")

    listing_body = {
        "quantity": 999, "title": info['title'], "description": info['description'],
        "price": info['price'], "who_made": "i_did", "taxonomy_id": 2078,
        "when_made": "made_to_order", "type": "download", "state": "draft",
        "tags": info['tags'], "shop_section_id": section_id,
        "skus": [info['sku']], "is_supply": False, "is_customizable": False,
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
            if upload_image(lid, img_path, rank): uploaded += 1
            time.sleep(0.8)
        else:
            print(f"  SKIP rank={rank}: missing")
    print(f"  Uploaded {uploaded}/{len(all_images)} images")
    time.sleep(1)

    print(f"  Uploading digital file...")
    upload_file(lid, art_path, rank=1)
    time.sleep(1)

    print(f"  Activating...")
    activated = activate_listing(lid)
    if activated and activated.get('state') == 'active':
        print(f"  ✓ LIVE: https://www.etsy.com/listing/{lid}/")
    else:
        print(f"  WARNING: check activation on Etsy dashboard")

    save_to_shop_data(lid, info)
    return {'pid': pid, 'lid': lid, 'uploaded': uploaded}


# ── Set bundle listing runner ─────────────────────────────────────────────────

def run_set_listing(set_key, sinfo, post_to_etsy=True):
    out_dir = os.path.join(ART_DIR, f'{set_key}_listing_images')
    os.makedirs(out_dir, exist_ok=True)

    art_paths = [os.path.join(ART_DIR, f'{pid}.jpg') for pid in sinfo['pids']]
    for p in art_paths:
        if not os.path.exists(p):
            print(f"  ERROR: missing art file {p} — run individual listings first")
            return None

    print(f"\n{'='*60}")
    print(f"[{set_key}] {sinfo['title'][:65]}...")
    print(f"{'='*60}")

    fc = sinfo.get('frame_color', (139,110,80))

    # 1. Gallery wall scene A
    print(f"\n[1] Gallery wall scene A...")
    bg_a = os.path.join(out_dir, 'bg_gallery_scene_A.jpg')
    scene_a = os.path.join(out_dir, 'gallery_scene_A.jpg')
    if not os.path.exists(bg_a):
        ok = gen_image(sinfo['scene_a_prompt'], bg_a, size="1024x1024", quality="high")
        if ok: time.sleep(3)
    else:
        print(f"  Background exists.")
    if os.path.exists(bg_a):
        composite_4_into_room(bg_a, art_paths, scene_a, frame_color=fc)

    # 2. Gallery wall scene B
    print(f"\n[2] Gallery wall scene B...")
    bg_b = os.path.join(out_dir, 'bg_gallery_scene_B.jpg')
    scene_b = os.path.join(out_dir, 'gallery_scene_B.jpg')
    if not os.path.exists(bg_b):
        ok = gen_image(sinfo['scene_b_prompt'], bg_b, size="1024x1024", quality="high")
        if ok: time.sleep(3)
    else:
        print(f"  Background exists.")
    if os.path.exists(bg_b):
        composite_4_into_room(bg_b, art_paths, scene_b, frame_color=fc)

    # 3. Clean 2×2 gallery grid on neutral background
    print(f"\n[3] Gallery grid...")
    grid_path = os.path.join(out_dir, 'gallery_grid.jpg')
    create_gallery_grid(art_paths, sinfo['labels'], grid_path,
                       sinfo['gallery_title'], sinfo['gallery_subtitle'])

    # 4–7. Individual piece close-ups (reuse from individual listing images)
    print(f"\n[4-7] Individual piece previews...")
    individual_images = []
    for pid in sinfo['pids']:
        ind_dir = os.path.join(ART_DIR, f'{pid}_listing_images')
        scene_path = os.path.join(ind_dir, 'lifestyle_scene_A.jpg')
        if not os.path.exists(scene_path):
            scene_path = os.path.join(ART_DIR, f'{pid}.jpg')
        individual_images.append(scene_path)
        print(f"  Individual: {pid} → {os.path.basename(scene_path)}")

    # 8. Set What's Included
    print(f"\n[8] Set What's Included...")
    wi_path = os.path.join(out_dir, 'set_whats_included.jpg')
    total_value = sinfo['individual_price'] * 4
    save_amount = total_value - sinfo['price']
    create_set_whats_included(art_paths, sinfo['labels'], wi_path,
                              sinfo['gallery_title'], sinfo['price'], save_amount)

    all_images = [
        (scene_a, 1), (scene_b, 2), (grid_path, 3),
        (individual_images[0], 4), (individual_images[1], 5),
        (individual_images[2], 6), (individual_images[3], 7),
        (wi_path, 8),
    ]

    labels_8 = ['Gallery Wall A','Gallery Wall B','2×2 Grid','Piece 1','Piece 2','Piece 3','Piece 4',"What's Incl."]
    print(f"\n{'─'*40}")
    for label, (path, rank) in zip(labels_8, all_images):
        sz = os.path.getsize(path)//1024 if os.path.exists(path) else 0
        ok = '✓' if os.path.exists(path) else '✗ MISSING'
        print(f"  rank {rank}: {label:20s} {ok} ({sz}KB)")

    if not post_to_etsy:
        print(f"\n[PREVIEW] Images saved for {set_key}. Not posting to Etsy.")
        return {'set_key': set_key, 'out_dir': out_dir}

    # Post to Etsy
    print(f"\n[9] Posting set to Etsy...")
    refresh()

    section_id = client.get_or_create_section(sinfo['section'])
    print(f"  Section '{sinfo['section']}': id={section_id}")

    listing_body = {
        "quantity": 999, "title": sinfo['title'], "description": sinfo['description'],
        "price": sinfo['price'], "who_made": "i_did", "taxonomy_id": 2078,
        "when_made": "made_to_order", "type": "download", "state": "draft",
        "tags": sinfo['tags'], "shop_section_id": section_id,
        "skus": [sinfo['sku']], "is_supply": False, "is_customizable": False,
        "should_auto_renew": True,
    }

    listing = create_listing(listing_body)
    if not listing or not listing.get('listing_id'):
        print(f"  FAILED to create Etsy listing for {set_key}")
        return None

    lid = listing['listing_id']
    print(f"  Created listing_id={lid}")
    time.sleep(1)

    uploaded = 0
    for img_path, rank in all_images:
        if os.path.exists(img_path):
            if upload_image(lid, img_path, rank): uploaded += 1
            time.sleep(0.8)
        else:
            print(f"  SKIP rank={rank}: missing")
    print(f"  Uploaded {uploaded}/{len(all_images)} images")
    time.sleep(1)

    # Upload all 4 art files as digital downloads
    print(f"  Uploading 4 digital files...")
    for file_rank, art_path in enumerate(art_paths, start=1):
        upload_file(lid, art_path, rank=file_rank)
        time.sleep(0.5)
    time.sleep(1)

    print(f"  Activating...")
    activated = activate_listing(lid)
    if activated and activated.get('state') == 'active':
        print(f"  ✓ LIVE: https://www.etsy.com/listing/{lid}/")
    else:
        print(f"  WARNING: check activation on Etsy dashboard")

    try:
        sdp = '/home/user/Etsy/data/shop_data.json'
        with open(sdp) as f:
            sd = json.load(f)
        sd.setdefault('listings', []).append({
            'id': str(lid), 'title': sinfo['title'], 'price': sinfo['price'],
            'type': 'wall_art_set', 'listing_type': 'download', 'state': 'active',
            'tags': sinfo['tags'], 'taxonomy_id': 2078,
            'url': f'https://www.etsy.com/listing/{lid}/', 'views': 0,
            'quantity': 999,
        })
        with open(sdp, 'w') as f:
            json.dump(sd, f, indent=2)
        print(f"  Saved to shop_data.json")
    except Exception as e:
        print(f"  WARNING: could not update shop_data.json: {e}")

    return {'set_key': set_key, 'lid': lid, 'uploaded': uploaded}


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pids', nargs='+', default=None)
    parser.add_argument('--sets-only', action='store_true', help='Run set bundle listings only')
    parser.add_argument('--preview', action='store_true', help='Generate images only, no Etsy')
    args = parser.parse_args()

    results = []

    if not args.sets_only:
        pids = args.pids if args.pids else list(LISTINGS.keys())
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

    # Run set bundle listings (only if no specific --pids filter or --sets-only)
    if args.sets_only or (not args.pids):
        for set_key, sinfo in SETS.items():
            try:
                r = run_set_listing(set_key, sinfo, post_to_etsy=not args.preview)
                results.append(r)
            except Exception as e:
                print(f"\nERROR processing set {set_key}: {e}")
                import traceback; traceback.print_exc()
                results.append({'set_key': set_key, 'error': str(e)})
            time.sleep(2)

    print(f"\n\n{'='*60}")
    print("BATCH COMPLETE")
    print(f"{'='*60}")
    for r in results:
        if r is None:
            print("  FAILED (None)")
        elif 'error' in r:
            key = r.get('pid') or r.get('set_key', '?')
            print(f"  {key} — ERROR: {r['error']}")
        elif 'lid' in r:
            key = r.get('pid') or r.get('set_key', '?')
            print(f"  ✓ {key} — listing {r['lid']} — https://www.etsy.com/listing/{r['lid']}/")
        else:
            key = r.get('pid') or r.get('set_key', '?')
            print(f"  {key} — preview only")
