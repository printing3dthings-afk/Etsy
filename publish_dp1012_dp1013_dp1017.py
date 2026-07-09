"""
Publish DP1012, DP1013, DP1017 wall art listings to Etsy with full 7-photo packages.
"""

import os, sys, json, base64, urllib.request, urllib.error, time

sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from tools.etsy_api import EtsyAPIClient, EtsyAPIError
from tools.data_store import DataStore

client = EtsyAPIClient()
shop_id = client.shop_id  # 65012858
OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

# ─── CONSTANTS ─────────────────────────────────────────────────────────────────

CANVAS = 2400

PRODUCTS = [
    {
        'pid': 'DP1012',
        'file': 'DP1012.jpg',
        'title': 'Checkerboard Vase Floral Print | Bold Retro Wall Art | Maximalist Home Decor | Instant Download',
        'price': 6.99,
        'sku': 'OBC-DWA-017',
        'tags': [
            'retro floral print', 'bold wall art', 'checkerboard vase', 'maximalist decor',
            'graphic art print', 'instant download', 'printable art', 'digital download',
            'retro home decor', 'eclectic wall art', 'floral illustration', 'colorful art',
            'home decor print'
        ],
        'description': """Bold, graphic, and impossibly fun — this retro floral print brings instant personality to any wall.

A striking illustration of drooping coral flowers in a bold black-and-white checkerboard vase, set against a cheerful pink striped background with a rich magenta base. Retro-inspired graphic art with a modern maximalist edge — perfect for an eclectic living room, a fun kitchen, or anywhere that needs a burst of personality.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT YOU GET
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital JPEG — print-ready at any size
✅ Sizes included: 5×7, 8×10, 11×14, 16×20 inches
✅ 300 DPI — sharp, gallery-quality prints
✅ Instant digital download — no physical item shipped

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ HOW TO PRINT
━━━━━━━━━━━━━━━━━━━━━━━━
• Print at home on any inkjet or laser printer
• Upload to Walmart Photo, Walgreens, CVS, or Costco for affordable prints
• Use Mpix or Artifact Uprising for premium fine art prints
• Frame with any standard-size frame from IKEA, Target, or Amazon

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: JPEG (high resolution)
• Color mode: RGB
• Resolution: 300 DPI
• Delivery: Instant digital download

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will this look good printed large?
A: Yes — 300 DPI is professional print quality at all standard sizes up to 20×30.

Q: Is this a physical print?
A: No — digital download only. You download and print yourself.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.""",
        'lifestyle_A': "An eclectic maximalist kitchen with retro checkerboard floor tiles, bold colored cabinets in sage green, open shelving with colorful ceramic bowls, a large framed bold graphic art print in pink and coral tones on the wall. Professional interior photography, DSLR 35mm lens, f/2.8, bright natural light. No text visible anywhere. Square format.",
        'lifestyle_B': "A fun retro-inspired living room with a mustard yellow sofa, a shag rug, vintage brass lamp, colorful throw pillows. On the wall, a large framed bold graphic floral art print in pink, coral and black tones in a thin black frame. Professional interior photography, DSLR 35mm lens, f/2.8, warm natural light. No text visible anywhere. Square format.",
    },
    {
        'pid': 'DP1013',
        'file': 'DP1013.jpg',
        'title': 'Soft Watercolor Flowers Print | Peach Botanical Wall Art | Nursery Floral Decor | Instant Download',
        'price': 5.99,
        'sku': 'OBC-DWA-018',
        'tags': [
            'watercolor print', 'botanical art', 'floral wall art', 'peach flowers art',
            'soft wall art', 'instant download', 'printable art', 'digital download',
            'nursery wall art', 'pastel art print', 'watercolor flowers', 'gentle floral art',
            'home decor print'
        ],
        'description': """Soft, gentle, and full of quiet beauty — this watercolor floral print brings calm to any space.

Delicate peach and orange flowers with soft sage-green leaves, painted in loose watercolor on a pale yellow-green background. The gentle washes of color create a dreamy, botanical feel perfect for a nursery, bedroom, or any room that needs a touch of softness.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT YOU GET
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital JPEG — print-ready at any size
✅ Sizes included: 5×7, 8×10, 11×14, 16×20 inches
✅ 300 DPI — sharp, gallery-quality prints
✅ Instant digital download — no physical item shipped

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ HOW TO PRINT
━━━━━━━━━━━━━━━━━━━━━━━━
• Print at home on any inkjet or laser printer
• Upload to Walmart Photo, Walgreens, CVS, or Costco for affordable prints
• Use Mpix or Artifact Uprising for premium fine art prints
• Frame with any standard-size frame from IKEA, Target, or Amazon

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: JPEG (high resolution)
• Color mode: RGB
• Resolution: 300 DPI
• Delivery: Instant digital download

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this good for a nursery?
A: Yes — the soft pastel palette is perfect for a baby or toddler room.

Q: Is this a physical print?
A: No — digital download only.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.""",
        'lifestyle_A': "A soft and serene nursery room with pale sage walls, a white crib with ivory bedding, a rocking chair with a pastel knit blanket, a small wooden shelf with stuffed animals. On the wall, a large framed soft watercolor art print in peach and sage green tones. Professional interior photography, DSLR 35mm lens, f/2.8, gentle morning light. No text visible anywhere. Square format.",
        'lifestyle_B': "A cozy feminine bedroom with cream walls, linen bedding in peach and sage tones, a wooden nightstand with a small vase of fresh peach flowers, a rattan pendant light. On the wall, a large framed soft watercolor botanical print in peach and sage tones. Professional interior photography, DSLR 35mm lens, f/2.8, warm soft light. No text visible anywhere. Square format.",
    },
    {
        'pid': 'DP1017',
        'file': 'DP1017.jpg',
        'title': 'Black Line Art Flower Print | Minimalist Botanical Wall Art | Modern Home Decor | Instant Download',
        'price': 5.99,
        'sku': 'OBC-DWA-019',
        'tags': [
            'line art print', 'minimalist print', 'botanical wall art', 'black white art',
            'modern wall art', 'instant download', 'printable art', 'digital download',
            'minimalist decor', 'flower line art', 'contemporary art', 'black white print',
            'home decor print'
        ],
        'description': """Clean. Bold. Timeless. This minimalist line art flower print goes with everything.

A single large poppy rendered in intricate concentric black line work on a warm cream background — the kind of print that looks effortlessly sophisticated in any room, from a modern apartment to a farmhouse kitchen. Inspired by linocut and woodblock printing traditions, updated for contemporary interiors.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT YOU GET
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital JPEG — print-ready at any size
✅ Sizes included: 5×7, 8×10, 11×14, 16×20 inches
✅ 300 DPI — sharp, gallery-quality prints
✅ Instant digital download — no physical item shipped

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ HOW TO PRINT
━━━━━━━━━━━━━━━━━━━━━━━━
• Print at home on any inkjet or laser printer
• Upload to Walmart Photo, Walgreens, CVS, or Costco for affordable prints
• Use Mpix or Artifact Uprising for premium fine art prints
• Looks stunning in a simple black or natural wood frame from IKEA or Amazon

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: JPEG (high resolution)
• Color mode: RGB (prints beautifully in black and white too)
• Resolution: 300 DPI
• Delivery: Instant digital download

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Can I print this in black and white?
A: It's already black on cream — it will look great on any paper.

Q: Is this a physical print?
A: No — digital download only.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.""",
        'lifestyle_A': "A sleek minimalist modern living room with white walls, a low charcoal grey sofa, a minimal oak coffee table with a single ceramic vase, concrete floor. On the wall, a large framed black and cream minimalist line art print in a slim black frame as the sole decor statement. Professional interior photography, DSLR 35mm lens, f/2.8, clean natural daylight. No text visible anywhere. Square format.",
        'lifestyle_B': "A bright modern bathroom with white subway tiles, a freestanding white soaking tub, a small potted plant on the window ledge. On the wall, a large framed bold black and cream botanical line art print in a simple black frame. Professional interior photography, DSLR 35mm lens, f/2.8, soft diffused light. No text visible anywhere. Square format.",
    },
]

# ─── IMAGE GENERATION HELPERS ──────────────────────────────────────────────────

def gradient_bg(size, top_rgb, bot_rgb):
    img = Image.new('RGB', (size, size), top_rgb)
    draw = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        r = int(top_rgb[0] + (bot_rgb[0] - top_rgb[0]) * t)
        g = int(top_rgb[1] + (bot_rgb[1] - top_rgb[1]) * t)
        b = int(top_rgb[2] + (bot_rgb[2] - top_rgb[2]) * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b))
    return img


def build_mockup(art_path, out_path, wall_top, wall_bot, mat_col, frame_col, frame_w=14, mat_w=46):
    art = Image.open(art_path).convert('RGB')
    art_w = int(CANVAS * 0.50)
    art_h = int(art_w * art.height / art.width)
    art = art.resize((art_w, art_h), Image.LANCZOS)
    full_w = art_w + 2 * mat_w + 2 * frame_w
    full_h = art_h + 2 * mat_w + 2 * frame_w
    bg = gradient_bg(CANVAS, wall_top, wall_bot)
    shadow = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    sx = (CANVAS - full_w) // 2 + 14
    sy = (CANVAS - full_h) // 2 + 18
    ImageDraw.Draw(shadow).rectangle([sx, sy, sx + full_w, sy + full_h], fill=(0, 0, 0, 100))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=20))
    bg = bg.convert('RGBA')
    bg = Image.alpha_composite(bg, shadow).convert('RGB')
    fx = (CANVAS - full_w) // 2
    fy = (CANVAS - full_h) // 2
    ImageDraw.Draw(bg).rectangle([fx, fy, fx + full_w, fy + full_h], fill=frame_col)
    mx, my = fx + frame_w, fy + frame_w
    ImageDraw.Draw(bg).rectangle([mx, my, mx + art_w + 2*mat_w, my + art_h + 2*mat_w], fill=mat_col)
    bg.paste(art, (mx + mat_w, my + mat_w))
    br = max(wall_bot[0]-18, 0)
    bg2 = max(wall_bot[1]-18, 0)
    bb = max(wall_bot[2]-18, 0)
    ImageDraw.Draw(bg).line([(0, CANVAS-130), (CANVAS, CANVAS-130)], fill=(br, bg2, bb), width=3)
    bg.save(out_path, 'JPEG', quality=92)
    print(f'  Mockup saved: {os.path.basename(out_path)} ({os.path.getsize(out_path)//1024}KB)')


def build_size_guide(out_path):
    W = H = 2400
    bg_color = (245, 241, 235)
    text_color = (44, 44, 42)
    frame_color = (82, 60, 40)
    img = Image.new('RGB', (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    font_path_bold = None
    for fp in ['/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
               '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']:
        if os.path.exists(fp):
            font_path_bold = fp
            break

    title_font = ImageFont.truetype(font_path_bold, 80) if font_path_bold else ImageFont.load_default()
    label_font = ImageFont.truetype(font_path_bold, 52) if font_path_bold else ImageFont.load_default()
    sub_font   = ImageFont.truetype(font_path_bold, 38) if font_path_bold else ImageFont.load_default()

    title = "PRINT SIZES INCLUDED"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W-tw)//2, 80), title, fill=text_color, font=title_font)

    sizes = [("5x7\"", 5, 7), ("8x10\"", 8, 10), ("11x14\"", 11, 14), ("16x20\"", 16, 20)]
    scale = 55
    gap = 60
    rects = [(int(w*scale), int(h*scale)) for _, w, h in sizes]
    total_w = sum(r[0] for r in rects) + gap * (len(rects)-1)
    start_x = (W - total_w) // 2
    top_y = 260

    x = start_x
    for i, ((label, _, _), (rw, rh)) in enumerate(zip(sizes, rects)):
        ry = top_y + (max(r[1] for r in rects) - rh)
        draw.rectangle([x, ry, x+rw, ry+rh], outline=frame_color, width=4)
        bbox = draw.textbbox((0, 0), label, font=label_font)
        lw = bbox[2] - bbox[0]
        draw.text((x+(rw-lw)//2, ry+rh+20), label, fill=text_color, font=label_font)
        sub = f"{sizes[i][1]}x{sizes[i][2]} in"
        sbbox = draw.textbbox((0, 0), sub, font=sub_font)
        sw = sbbox[2] - sbbox[0]
        draw.text((x+(rw-sw)//2, ry+rh+85), sub, fill=(120, 110, 100), font=sub_font)
        x += rw + gap

    note = "All sizes included in one download"
    nbbox = draw.textbbox((0, 0), note, font=sub_font)
    nw = nbbox[2] - nbbox[0]
    draw.text(((W-nw)//2, H-120), note, fill=(120, 110, 100), font=sub_font)

    img.save(out_path, 'JPEG', quality=92)
    print(f'  Size guide saved: {os.path.basename(out_path)}')


def gen_image(prompt, out_path, retries=2):
    payload = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1536",
        "quality": "medium",
        "output_format": "jpeg"
    }).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                "https://api.openai.com/v1/images/generations",
                data=payload,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read())
            img_bytes = base64.b64decode(data["data"][0]["b64_json"])
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            print(f'  DALL-E: {os.path.basename(out_path)} ({len(img_bytes)//1024}KB)')
            return
        except Exception as e:
            print(f'  DALL-E attempt {attempt+1} failed: {e}')
            if attempt < retries - 1:
                time.sleep(10)
    raise RuntimeError(f'DALL-E failed after {retries} attempts for {out_path}')


def upload_with_retry(func, *args, **kwargs):
    """Call func(*args, **kwargs), retry once on 500 (5s) or 429 (15s), refresh on 401."""
    for attempt in range(3):
        try:
            return func(*args, **kwargs)
        except EtsyAPIError as e:
            if e.status == 401 and attempt == 0:
                print(f'  401 — refreshing token...')
                client.refresh_access_token()
                time.sleep(2)
            elif e.status == 429 and attempt < 2:
                print(f'  429 — rate limited, waiting 15s...')
                time.sleep(15)
            elif e.status >= 500 and attempt < 2:
                print(f'  {e.status} server error, waiting 5s...')
                time.sleep(5)
            else:
                raise
    raise RuntimeError('upload_with_retry exhausted attempts')


def set_sku(listing_id, sku):
    """Fetch inventory, patch in SKU (product-level), PUT back."""
    base = "https://openapi.etsy.com/v3/application"
    url = f"{base}/listings/{listing_id}/inventory"
    api_key_hdr = f"{client.client_id}:{client.client_secret}"
    req = urllib.request.Request(url, headers={
        "x-api-key": api_key_hdr,
        "Authorization": f"Bearer {client.access_token}",
    }, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        inv = json.loads(resp.read())

    products = inv.get("products", [])
    for prod in products:
        # Strip read-only fields from product
        prod.pop("product_id", None)
        prod.pop("is_deleted", None)
        # SKU lives at the product level, not offering level
        prod["sku"] = sku
        # Clean property_values
        for pv in prod.get("property_values", []):
            pv.pop("scale_name", None)
        # Clean offering read-only fields; convert price dict to float
        for offering in prod.get("offerings", []):
            offering.pop("offering_id", None)
            offering.pop("is_deleted", None)
            offering.pop("readiness_state_id", None)
            p = offering.get("price")
            if isinstance(p, dict):
                offering["price"] = float(p.get("amount", 0)) / float(p.get("divisor", 100))
            elif p is not None:
                offering["price"] = float(p)

    body = json.dumps({
        "products": products,
        "price_on_property": inv.get("price_on_property", []),
        "quantity_on_property": inv.get("quantity_on_property", []),
        "sku_on_property": inv.get("sku_on_property", []),
    }).encode()
    put_req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "x-api-key": api_key_hdr,
        "Authorization": f"Bearer {client.access_token}",
    }, method="PUT")
    try:
        with urllib.request.urlopen(put_req, timeout=30) as resp:
            result = json.loads(resp.read())
        print(f'  SKU set: {sku}')
        return result
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        print(f'  SKU PUT error {e.code}: {body_text[:300]}')
        raise


# ─── MAIN WORKFLOW ─────────────────────────────────────────────────────────────

results = []

for product in PRODUCTS:
    pid = product['pid']
    art_file = os.path.join(ART_DIR, product['file'])
    out_dir = os.path.join(ART_DIR, f'{pid}_listing_images')
    os.makedirs(out_dir, exist_ok=True)

    print(f'\n{"="*60}')
    print(f'Processing {pid}...')
    print(f'{"="*60}')

    # ── STEP 1: Build 3 Pillow mockups ─────────────────────────────────────────
    print('\n[Step 1] Building Pillow mockups...')

    mockup_warm = os.path.join(out_dir, 'mockup_warm.jpg')
    build_mockup(art_file, mockup_warm,
                 wall_top=(240, 234, 221), wall_bot=(225, 218, 204),
                 mat_col=(250, 248, 244), frame_col=(82, 60, 40))

    mockup_sage = os.path.join(out_dir, 'mockup_sage.jpg')
    build_mockup(art_file, mockup_sage,
                 wall_top=(192, 204, 188), wall_bot=(175, 187, 170),
                 mat_col=(250, 249, 246), frame_col=(140, 110, 72))

    mockup_dark = os.path.join(out_dir, 'mockup_dark.jpg')
    build_mockup(art_file, mockup_dark,
                 wall_top=(52, 56, 62), wall_bot=(40, 44, 50),
                 mat_col=(252, 250, 247), frame_col=(180, 152, 92),
                 frame_w=16, mat_w=52)

    # ── STEP 2: Build size guide ────────────────────────────────────────────────
    print('\n[Step 2] Building size guide...')
    size_guide = os.path.join(out_dir, 'size_guide.jpg')
    build_size_guide(size_guide)

    # ── STEP 3: Generate DALL-E lifestyle photos ────────────────────────────────
    print('\n[Step 3] Generating DALL-E lifestyle photos...')
    lifestyle_a = os.path.join(out_dir, 'lifestyle_A.jpg')
    lifestyle_b = os.path.join(out_dir, 'lifestyle_B.jpg')

    gen_image(product['lifestyle_A'], lifestyle_a)
    time.sleep(2)
    gen_image(product['lifestyle_B'], lifestyle_b)

    # ── STEP 4: Create draft Etsy listing ──────────────────────────────────────
    print('\n[Step 4] Creating Etsy listing (draft)...')
    listing = upload_with_retry(client.create_listing, {
        'title': product['title'],
        'description': product['description'],
        'price': float(product['price']),
        'quantity': 999,
        'tags': product['tags'],
        'who_made': 'i_did',
        'when_made': '2020_2025',
        'taxonomy_id': 2078,
        'type': 'download',
        'shop_section_id': 58657103,
    })
    listing_id = str(listing['listing_id'])
    print(f'  Listing created: {listing_id}')

    # ── STEP 5: Upload 7 photos ─────────────────────────────────────────────────
    print('\n[Step 5] Uploading photos...')
    photo_files = [
        (art_file, 1),
        (mockup_warm, 2),
        (mockup_sage, 3),
        (mockup_dark, 4),
        (size_guide, 5),
        (lifestyle_a, 6),
        (lifestyle_b, 7),
    ]
    photos_uploaded = 0
    for img_path, rank in photo_files:
        try:
            upload_with_retry(client.upload_listing_image, listing_id, img_path, rank)
            print(f'  Photo rank {rank} uploaded: {os.path.basename(img_path)}')
            photos_uploaded += 1
        except Exception as e:
            print(f'  ERROR uploading rank {rank} ({os.path.basename(img_path)}): {e}')
        time.sleep(1)

    # ── STEP 6: Attach digital file ─────────────────────────────────────────────
    print('\n[Step 6] Attaching digital file...')
    try:
        upload_with_retry(client.upload_listing_file, listing_id, art_file, 1)
        print(f'  Digital file attached: {product["file"]}')
    except Exception as e:
        print(f'  ERROR attaching digital file: {e}')

    # ── STEP 7: Activate listing ────────────────────────────────────────────────
    print('\n[Step 7] Activating listing...')
    upload_with_retry(client.update_listing, listing_id, {'state': 'active'})
    print(f'  Listing activated!')

    # ── STEP 8: Set SKU via inventory ───────────────────────────────────────────
    print('\n[Step 8] Setting SKU...')
    try:
        set_sku(listing_id, product['sku'])
    except Exception as e:
        print(f'  WARNING: SKU set failed: {e}')

    # ── STEP 9: Update DataStore ────────────────────────────────────────────────
    print('\n[Step 9] Updating DataStore...')
    try:
        store = DataStore()
        products_list = store.get('digital_products', default=[])
        found = False
        for p in products_list:
            if p.get('id') == pid:
                p['etsy_listing_id'] = listing_id
                p['status'] = 'listed'
                found = True
                break
        if not found:
            # Add new entry if not present
            products_list.append({
                'id': pid,
                'etsy_listing_id': listing_id,
                'status': 'listed',
                'sku': product['sku'],
            })
        store.set(products_list, 'digital_products')
        store.save()
        print(f'  DataStore updated for {pid}')
    except Exception as e:
        print(f'  WARNING: DataStore update failed: {e}')

    results.append({
        'pid': pid,
        'listing_id': listing_id,
        'sku': product['sku'],
        'photos_uploaded': photos_uploaded,
        'activated': True,
    })

# ─── SUMMARY TABLE ─────────────────────────────────────────────────────────────

print('\n\n' + '='*70)
print(f'{"PID":<10} {"listing_id":<15} {"SKU":<18} {"photos":>8} {"activated":>10}')
print('-'*70)
for r in results:
    print(f'{r["pid"]:<10} {r["listing_id"]:<15} {r["sku"]:<18} {r["photos_uploaded"]:>8} {"YES" if r["activated"] else "NO":>10}')
print('='*70)
