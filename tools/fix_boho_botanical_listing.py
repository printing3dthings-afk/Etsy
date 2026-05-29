#!/usr/bin/env python3
"""
Fix Boho Botanical Wall Art Set of 4 listing (4512301880).

Problems in current listing:
  - Rank 1: AI-generated fake gallery wall (not the real product files)
  - Ranks 2-9: Portrait art (3000×4500) crammed into square frames → distorted/cropped

Fix: Regenerate all 9 listing images using the actual product files (DP1000-DP1003)
     with correctly proportioned PORTRAIT frames.

Usage:
  python tools/fix_boho_botanical_listing.py --preview   # generate images, no upload
  python tools/fix_boho_botanical_listing.py             # generate + upload to Etsy
"""

import os, sys, json, urllib.request, urllib.error, time, argparse
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError
from tools.lifestyle_composite import composite_smart
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

client = EtsyAPIClient()
shop_id = client.shop_id
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'
OUT_DIR = f'{ART_DIR}/BOHO-SET_listing_images'
LISTING_ID = 4512301880

# Actual product art files
ART_FILES = {
    'DP1000': f'{ART_DIR}/DP1000.jpg',   # Botanical bouquet (main piece)
    'DP1001': f'{ART_DIR}/DP1001.jpg',   # Silver eucalyptus branch
    'DP1002': f'{ART_DIR}/DP1002.jpg',   # Sage & lavender stems
    'DP1003': f'{ART_DIR}/DP1003.jpg',   # Pampas grass plume
}
ART_LABELS = {
    'DP1000': 'Botanical Bouquet',
    'DP1001': 'Silver Eucalyptus',
    'DP1002': 'Sage & Lavender',
    'DP1003': 'Pampas Grass',
}

# Room backgrounds - warm boho aesthetics
BG_SOFA_PAMPAS      = f'{ART_DIR}/DP1019_listing_images/bg_lifestyle_room_B.jpg'
BG_BOUCLE_SOFA      = f'{ART_DIR}/DP1031_listing_images/bg_lifestyle_room_A.jpg'
BG_RATTAN_FLOWERS   = f'{ART_DIR}/DP1020_listing_images/bg_lifestyle_room_B.jpg'
BG_GOLDEN_BEDROOM   = f'{ART_DIR}/DP1016_listing_images/bg_lifestyle_room_A.jpg'

# Honey oak frame color - natural wood, boho aesthetic
FRAME_COLOR = (165, 132, 78)

auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key": f"{client.client_id}:{client.client_secret}",
}


def refresh():
    if client.refresh_access_token():
        auth_headers["Authorization"] = f"Bearer {client.access_token}"
        print("  Token refreshed.")


def _load_fonts():
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    bold = paths[0] if os.path.exists(paths[0]) else None
    reg  = paths[1] if os.path.exists(paths[1]) else None
    try:
        return {
            'title': ImageFont.truetype(bold, 34) if bold else ImageFont.load_default(),
            'h2':    ImageFont.truetype(bold, 26) if bold else ImageFont.load_default(),
            'body':  ImageFont.truetype(reg,  22) if reg  else ImageFont.load_default(),
            'label': ImageFont.truetype(reg,  18) if reg  else ImageFont.load_default(),
            'sm':    ImageFont.truetype(reg,  16) if reg  else ImageFont.load_default(),
            'price': ImageFont.truetype(bold, 48) if bold else ImageFont.load_default(),
        }
    except Exception:
        d = ImageFont.load_default()
        return {k: d for k in ['title','h2','body','label','sm','price']}


# ── Image 1: 2×2 Gallery Grid ─────────────────────────────────────────────────

def create_gallery_grid(out_path):
    """2×2 grid showing all 4 art pieces in correctly-proportioned portrait frames."""
    W, H = 1200, 1200
    fonts = _load_fonts()
    canvas = Image.new('RGB', (W, H), (244, 241, 236))
    draw = ImageDraw.Draw(canvas)

    draw.text((W//2, 36), "Boho Botanical Wall Art Set of 4",
              font=fonts['title'], fill=(60, 52, 40), anchor="mm")
    draw.text((W//2, 72), "Pampas Grass  ·  Eucalyptus  ·  Sage & Lavender  ·  Wildflower Bouquet",
              font=fonts['sm'], fill=(110, 95, 75), anchor="mm")

    # Portrait 2:3 frames: art_w=270, art_h=405
    art_w = 270
    art_h = int(art_w * 1.5)  # 405 — exact 2:3 ratio for 3000×4500 art
    mat = 14
    fr  = 8
    fw  = art_w + 2*mat + 2*fr   # 314
    fh  = art_h + 2*mat + 2*fr   # 449
    label_h = 26
    gap = 18

    total_w = 2*fw + gap          # 646
    total_h = 2*(fh + label_h) + gap  # 952
    start_x = (W - total_w) // 2
    start_y = 95

    mat_color = (252, 250, 247)

    pids = ['DP1000', 'DP1001', 'DP1002', 'DP1003']
    for i, pid in enumerate(pids):
        col, row = i % 2, i // 2
        px = start_x + col*(fw + gap)
        py = start_y + row*(fh + label_h + gap)

        art = Image.open(ART_FILES[pid]).convert('RGB')
        art_r = art.resize((art_w, art_h), Image.LANCZOS)
        art_r = ImageEnhance.Brightness(art_r).enhance(0.94)

        # Shadow
        shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rectangle([px+7, py+9, px+fw+7, py+fh+9], fill=(0, 0, 0, 55))
        shadow = shadow.filter(ImageFilter.GaussianBlur(9))
        canvas = Image.alpha_composite(canvas.convert('RGBA'), shadow).convert('RGB')
        draw = ImageDraw.Draw(canvas)

        # Frame
        draw.rectangle([px, py, px+fw, py+fh], fill=FRAME_COLOR)
        # Bevel highlight top/left
        bv = 3
        fc_hi = tuple(min(255, c+40) for c in FRAME_COLOR)
        fc_sh = tuple(max(0, c-40) for c in FRAME_COLOR)
        draw.polygon([px, py, px+fw, py, px+fw-bv, py+bv, px+bv, py+bv], fill=fc_hi)
        draw.polygon([px, py, px, py+fh, px+bv, py+fh-bv, px+bv, py+bv], fill=fc_hi)
        draw.polygon([px+fw, py, px+fw, py+fh, px+fw-bv, py+fh-bv, px+fw-bv, py+bv], fill=fc_sh)
        draw.polygon([px, py+fh, px+fw, py+fh, px+fw-bv, py+fh-bv, px+bv, py+fh-bv], fill=fc_sh)
        # Mat
        draw.rectangle([px+fr, py+fr, px+fr+art_w+2*mat, py+fr+art_h+2*mat], fill=mat_color)
        # Art
        canvas.paste(art_r, (px+fr+mat, py+fr+mat))
        draw = ImageDraw.Draw(canvas)
        # Label
        draw.text((px+fw//2, py+fh+14), ART_LABELS[pid],
                  font=fonts['label'], fill=(100, 88, 75), anchor="mm")

    canvas.save(out_path, 'JPEG', quality=92)
    print(f"  Gallery grid: {os.path.basename(out_path)}")


# ── Image 6/9: Clean Wall Mockup ──────────────────────────────────────────────

def create_clean_mockup(art_path, out_path, wall_color=(245, 241, 234)):
    """Art in a portrait frame centered on a plain textured wall — no furniture."""
    CANVAS = 1024
    # Create warm cream wall background with subtle texture
    room = Image.new('RGB', (CANVAS, CANVAS), wall_color)

    # Slight gradient — slightly lighter at top, slightly darker at bottom
    arr = np.array(room, dtype=np.float32)
    for y in range(CANVAS):
        fade = 1.0 + (y / CANVAS) * 0.04 - 0.02
        arr[y] = np.clip(arr[y] * fade, 0, 255)
    room = Image.fromarray(arr.astype(np.uint8))

    art = Image.open(art_path).convert('RGB')
    art_w = int(CANVAS * 0.30)
    art_h = int(art_w * art.height / art.width)

    mat_w, frame_w = 30, 14
    full_w = art_w + 2*mat_w + 2*frame_w
    full_h = art_h + 2*mat_w + 2*frame_w

    px = (CANVAS - full_w) // 2
    py = (CANVAS - full_h) // 2  # Center on the wall

    # Ambient occlusion shadow behind frame
    ao = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    for pad in range(35, 0, -3):
        alpha = int(35 * (1 - (pad/35) ** 1.5))
        ImageDraw.Draw(ao).rectangle(
            [px-pad, py-pad, px+full_w+pad, py+full_h+pad], fill=(0, 0, 0, alpha))
    ao = ao.filter(ImageFilter.GaussianBlur(radius=18))
    room = Image.alpha_composite(room.convert('RGBA'), ao).convert('RGB')

    # Drop shadow
    shadow = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle(
        [px+8, py+12, px+full_w+8, py+full_h+12], fill=(0, 0, 0, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    room = Image.alpha_composite(room.convert('RGBA'), shadow).convert('RGB')

    draw = ImageDraw.Draw(room)

    # Frame
    draw.rectangle([px, py, px+full_w, py+full_h], fill=FRAME_COLOR)
    bv = 4
    fc_hi = tuple(min(255, c+45) for c in FRAME_COLOR)
    fc_sh = tuple(max(0, c-45) for c in FRAME_COLOR)
    draw.polygon([px, py, px+full_w, py, px+full_w-bv, py+bv, px+bv, py+bv], fill=fc_hi)
    draw.polygon([px, py, px, py+full_h, px+bv, py+full_h-bv, px+bv, py+bv], fill=fc_hi)
    draw.polygon([px+full_w, py, px+full_w, py+full_h, px+full_w-bv, py+full_h-bv, px+full_w-bv, py+bv], fill=fc_sh)
    draw.polygon([px, py+full_h, px+full_w, py+full_h, px+full_w-bv, py+full_h-bv, px+bv, py+full_h-bv], fill=fc_sh)

    # White mat
    mat_color = (253, 251, 248)
    mx, my = px + frame_w, py + frame_w
    draw.rectangle([mx, my, mx + art_w + 2*mat_w, my + art_h + 2*mat_w], fill=mat_color)

    # Inner shadow on mat opening
    inner = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    art_x, art_y = mx + mat_w, my + mat_w
    ImageDraw.Draw(inner).rectangle(
        [art_x-3, art_y-3, art_x+art_w+3, art_y+art_h+3], fill=(0, 0, 0, 25))
    inner = inner.filter(ImageFilter.GaussianBlur(5))
    room = Image.alpha_composite(room.convert('RGBA'), inner).convert('RGB')

    art_resized = art.resize((art_w, art_h), Image.LANCZOS)
    art_resized = ImageEnhance.Brightness(art_resized).enhance(0.93)
    room.paste(art_resized, (art_x, art_y))

    room.save(out_path, 'JPEG', quality=93)
    print(f"  Clean mockup: {os.path.basename(out_path)}")


# ── Image 7: Size Guide ───────────────────────────────────────────────────────

def create_size_guide(art_path, out_path):
    """Size comparison guide showing the art at 3 different print sizes."""
    W = 1200
    bg_color = (245, 243, 239)
    mat_color = (252, 250, 247)
    text_color = (60, 55, 50)

    canvas = Image.new('RGB', (W, W), bg_color)
    draw = ImageDraw.Draw(canvas)
    fonts = _load_fonts()
    art = Image.open(art_path).convert('RGB')

    draw.text((W//2, 38), "AVAILABLE PRINT SIZES", font=fonts['h2'],
              fill=text_color, anchor="mm")
    draw.text((W//2, 68), "Download includes all sizes — print at home or at any print shop",
              font=fonts['sm'], fill=(120, 110, 100), anchor="mm")

    # Portrait sizes: width × actual height to keep 2:3 ratio
    sizes = [("5×7\"", 0.12), ("8×10\"", 0.18), ("11×14\"", 0.26)]
    aw, ah = art.size
    aspect = ah / aw  # ~1.5 for portrait

    x_positions = [200, 600, 1000]
    y_top = 100

    for (label, scale), cx in zip(sizes, x_positions):
        w = int(W * scale)
        h = int(w * aspect)
        mat_pad = 12
        frame_pad = 7
        total_w = w + 2*mat_pad + 2*frame_pad
        total_h = h + 2*mat_pad + 2*frame_pad
        px = cx - total_w // 2
        py = y_top

        shadow = Image.new('RGBA', (W, W), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rectangle(
            [px+8, py+10, px+total_w+8, py+total_h+10], fill=(0, 0, 0, 55))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        canvas = Image.alpha_composite(canvas.convert('RGBA'), shadow).convert('RGB')
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([px, py, px+total_w, py+total_h], fill=FRAME_COLOR)
        draw.rectangle([px+frame_pad, py+frame_pad,
                        px+frame_pad+w+2*mat_pad, py+frame_pad+h+2*mat_pad], fill=mat_color)
        art_resized = art.resize((w, h), Image.LANCZOS)
        canvas.paste(art_resized, (px+frame_pad+mat_pad, py+frame_pad+mat_pad))
        draw = ImageDraw.Draw(canvas)
        draw.text((cx, py + total_h + 18), label, font=fonts['body'],
                  fill=text_color, anchor="mm")

    draw.text((W//2, W - 35),
              "All sizes included in your download  ·  300 DPI  ·  Print-ready JPG files",
              font=fonts['sm'], fill=(120, 110, 100), anchor="mm")

    canvas.save(out_path, 'JPEG', quality=92)
    print(f"  Size guide: {os.path.basename(out_path)}")


# ── Image 8: What's Included ──────────────────────────────────────────────────

def create_whats_included(out_path):
    """Info card showing all 4 pieces and download details."""
    W, H = 1200, 1200
    bg_color = (250, 248, 244)
    accent = FRAME_COLOR
    dark = (45, 38, 28)
    mid = (100, 88, 70)

    canvas = Image.new('RGB', (W, H), bg_color)
    draw = ImageDraw.Draw(canvas)
    fonts = _load_fonts()

    # Show 4 small art thumbnails at the top
    thumb_w = 160
    thumb_h = int(thumb_w * 1.5)  # 240px
    mat_p, fr_p = 8, 5
    fw = thumb_w + 2*mat_p + 2*fr_p  # 186
    fh = thumb_h + 2*mat_p + 2*fr_p  # 266
    gap_x = 20
    total_thumb_w = 4*fw + 3*gap_x
    tx_start = (W - total_thumb_w) // 2
    ty_start = 60

    pids = ['DP1000', 'DP1001', 'DP1002', 'DP1003']
    for i, pid in enumerate(pids):
        px = tx_start + i * (fw + gap_x)
        py = ty_start

        art = Image.open(ART_FILES[pid]).convert('RGB')
        art_r = art.resize((thumb_w, thumb_h), Image.LANCZOS)

        shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rectangle([px+5, py+7, px+fw+5, py+fh+7], fill=(0, 0, 0, 50))
        shadow = shadow.filter(ImageFilter.GaussianBlur(7))
        canvas = Image.alpha_composite(canvas.convert('RGBA'), shadow).convert('RGB')
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([px, py, px+fw, py+fh], fill=accent)
        draw.rectangle([px+fr_p, py+fr_p, px+fr_p+thumb_w+2*mat_p, py+fr_p+thumb_h+2*mat_p],
                       fill=(252, 250, 247))
        canvas.paste(art_r, (px+fr_p+mat_p, py+fr_p+mat_p))
        draw = ImageDraw.Draw(canvas)
        draw.text((px+fw//2, py+fh+14), ART_LABELS[pid],
                  font=fonts['sm'], fill=(110, 95, 75), anchor="mm")

    # Divider
    sep_y = ty_start + fh + 42
    draw.rectangle([80, sep_y, W-80, sep_y+2], fill=accent)
    sep_y += 22

    # Title
    draw.text((W//2, sep_y + 24), "INSTANT DOWNLOAD", font=fonts['title'],
              fill=accent, anchor="mm")
    sep_y += 60

    # Price
    draw.text((W//2, sep_y), "$9.99", font=fonts['price'], fill=dark, anchor="mm")
    sep_y += 70

    # What's included bullets
    draw.text((W//2, sep_y), "WHAT'S INCLUDED:", font=fonts['h2'], fill=dark, anchor="mm")
    sep_y += 42

    items = [
        "✓  4 Botanical Watercolor Art Prints",
        "✓  High-resolution JPG files (300 DPI)",
        "✓  8 print sizes: 4×6 up to 24×36",
        "✓  Instant download after purchase",
        "✓  No waiting — no shipping",
        "✓  Print at home or any print shop",
        "✓  Personal use license included",
    ]
    for item in items:
        draw.text((W//2, sep_y), item, font=fonts['body'], fill=mid, anchor="mm")
        sep_y += 36

    sep_y += 8
    draw.rectangle([80, sep_y, W-80, sep_y+1], fill=(210, 200, 185))
    sep_y += 18
    draw.text((W//2, sep_y),
              "Boho Botanical Collection  ·  Sage Green  ·  Pampas  ·  Eucalyptus  ·  Lavender",
              font=fonts['sm'], fill=mid, anchor="mm")
    sep_y += 32
    draw.text((W//2, sep_y), "© OnBrandCraftz  ·  Personal use only",
              font=fonts['sm'], fill=(160, 148, 130), anchor="mm")

    canvas.save(out_path, 'JPEG', quality=92)
    print(f"  What's included: {os.path.basename(out_path)}")


# ── Etsy upload helpers ───────────────────────────────────────────────────────

def get_existing_images():
    url = f"https://openapi.etsy.com/v3/application/listings/{LISTING_ID}/images"
    req = urllib.request.Request(url, headers=auth_headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {img['rank']: img['listing_image_id']
                    for img in json.loads(resp.read()).get('results', [])}
    except Exception as e:
        print(f"  WARNING get_images: {e}")
        return {}


def delete_image(image_id):
    url = (f"https://openapi.etsy.com/v3/application/shops/{shop_id}"
           f"/listings/{LISTING_ID}/images/{image_id}")
    req = urllib.request.Request(url, headers=auth_headers, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=20):
            return True
    except urllib.error.HTTPError as e:
        print(f"  DELETE {image_id}: HTTP {e.code}")
        return False


def upload_image(img_path, rank):
    existing = get_existing_images()
    if rank in existing:
        delete_image(existing[rank])
        time.sleep(0.4)

    for attempt in range(3):
        try:
            result = client.upload_listing_image(LISTING_ID, img_path, rank=rank)
            print(f"  Uploaded rank={rank} ✓")
            return True
        except EtsyAPIError as e:
            if e.status == 401:
                refresh()
            elif e.status == 429:
                time.sleep(15)
            elif e.status == 500 and attempt < 2:
                time.sleep(5)
            else:
                print(f"  Upload rank={rank} failed: {e}")
                return False
    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', action='store_true',
                        help='Generate images only — do not upload to Etsy')
    args = parser.parse_args()

    client.refresh_access_token()
    auth_headers["Authorization"] = f"Bearer {client.access_token}"

    os.makedirs(OUT_DIR, exist_ok=True)

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Fix: Boho Botanical Wall Art Set of 4")
    print(f"  Listing: {LISTING_ID}")
    print(f"  Mode: {'PREVIEW (no upload)' if args.preview else 'LIVE UPDATE'}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # ── Generate all images ──────────────────────────────────────────────────

    images = {}

    # 1. Gallery grid — primary hero image
    print("[ 1/9 ] Gallery grid (all 4 pieces)...")
    p = f'{OUT_DIR}/01_gallery_grid.jpg'
    create_gallery_grid(p)
    images[1] = p

    # 2. DP1000 (Botanical bouquet) — sofa with pampas vase — warm boho living room
    print("[ 2/9 ] DP1000 Botanical Bouquet — boho living room...")
    p = f'{OUT_DIR}/02_DP1000_room_boho.jpg'
    composite_smart(BG_SOFA_PAMPAS, ART_FILES['DP1000'], p, frame_color=FRAME_COLOR)
    images[2] = p

    # 3. DP1001 (Eucalyptus) — boucle sofa with terracotta/sage pillows
    print("[ 3/9 ] DP1001 Eucalyptus — modern boho living room...")
    p = f'{OUT_DIR}/03_DP1001_room_boucle.jpg'
    composite_smart(BG_BOUCLE_SOFA, ART_FILES['DP1001'], p, frame_color=FRAME_COLOR)
    images[3] = p

    # 4. DP1002 (Sage/Lavender) — rattan chair with wildflowers
    print("[ 4/9 ] DP1002 Sage & Lavender — rattan dining scene...")
    p = f'{OUT_DIR}/04_DP1002_room_rattan.jpg'
    composite_smart(BG_RATTAN_FLOWERS, ART_FILES['DP1002'], p, frame_color=FRAME_COLOR)
    images[4] = p

    # 5. DP1003 (Pampas grass) — golden bedroom with roses
    print("[ 5/9 ] DP1003 Pampas Grass — golden bedroom...")
    p = f'{OUT_DIR}/05_DP1003_room_bedroom.jpg'
    composite_smart(BG_GOLDEN_BEDROOM, ART_FILES['DP1003'], p, frame_color=FRAME_COLOR)
    images[5] = p

    # 6. DP1001 clean wall mockup (eucalyptus on plain wall — very clean/minimal)
    print("[ 6/9 ] DP1001 Eucalyptus — clean wall mockup...")
    p = f'{OUT_DIR}/06_DP1001_clean_mockup.jpg'
    create_clean_mockup(ART_FILES['DP1001'], p, wall_color=(244, 241, 235))
    images[6] = p

    # 7. Size guide (portrait frames with actual art shown)
    print("[ 7/9 ] Size guide with DP1000...")
    p = f'{OUT_DIR}/07_size_guide.jpg'
    create_size_guide(ART_FILES['DP1000'], p)
    images[7] = p

    # 8. What's included card
    print("[ 8/9 ] What's included card...")
    p = f'{OUT_DIR}/08_whats_included.jpg'
    create_whats_included(p)
    images[8] = p

    # 9. DP1000 clean mockup (main piece on warm cream wall — second clean shot)
    print("[ 9/9 ] DP1000 Botanical Bouquet — warm wall mockup...")
    p = f'{OUT_DIR}/09_DP1000_clean_mockup.jpg'
    create_clean_mockup(ART_FILES['DP1000'], p, wall_color=(248, 244, 237))
    images[9] = p

    print(f"\n  All images generated → {OUT_DIR}")
    print("  Checking dimensions...")
    for rank, path in sorted(images.items()):
        img = Image.open(path)
        print(f"    rank {rank}: {os.path.basename(path)} — {img.size[0]}×{img.size[1]}")

    if args.preview:
        print("\n  PREVIEW mode — skipping upload.\n")
        return

    # ── Upload to Etsy ───────────────────────────────────────────────────────
    print("\n  Uploading to Etsy listing...")
    success, failed = 0, 0
    for rank in sorted(images.keys()):
        ok = upload_image(images[rank], rank)
        if ok:
            success += 1
        else:
            failed += 1
        time.sleep(1.0)

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Uploaded: {success}   Failed: {failed}")
    if failed == 0:
        print("  ✓ Boho Botanical listing images fixed!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


if __name__ == '__main__':
    main()
