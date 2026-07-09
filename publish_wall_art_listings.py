"""
Publish 12 digital wall art listings to Etsy.
Builds 5-photo packages using Pillow, creates draft listings,
uploads photos + digital file, activates, and sets SKU via inventory API.
"""

import os
import sys
import time
import json
import urllib.request
import urllib.parse
import urllib.error

# ── Load .env ────────────────────────────────────────────────────────────────
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from tools.etsy_api import EtsyAPIClient, EtsyAPIError
from tools.data_store import DataStore

client = EtsyAPIClient()
shop_id = client.shop_id  # 65012858

PRODUCTS_DIR = '/home/user/Etsy/data/digital_products/product_files'
FONT_BOLD = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
FONT_REG  = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf' \
            if os.path.exists('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf') \
            else FONT_BOLD
SECTION_ID = 58657103
CANVAS = 2400

BASE_URL = "https://openapi.etsy.com/v3/application"

# ── Product catalog ────────────────────────────────────────────────────────
PRODUCTS = [
    {
        'pid': 'DP1007', 'sku': 'OBC-DWA-005', 'price': 7.99,
        'title': 'Mediterranean Window with Lemons Print | Amalfi Coast Wall Art | Kitchen Decor | Instant Download',
        'tags': ['wall art print','lemon print','mediterranean art','kitchen wall art','coastal decor',
                 'instant download','printable art','digital download','amalfi coast art',
                 'oil painting print','colorful wall art','home decor print','italy art print'],
        'hook': 'Transform your walls with the warmth of the Mediterranean — instant download, print at home.',
        'art_desc': (
            'This vibrant Amalfi Coast window art print captures the magic of southern Italy: teal louvered shutters '
            'thrown open to a shimmering blue sea, terracotta cliffs dotted with sun-baked villages, and bright yellow '
            'lemons hanging from a branch in the foreground. Rich impasto oil painting style with thick, expressive '
            'brushwork in warm ochre, turquoise, and golden yellow tones.'
        ),
    },
    {
        'pid': 'DP1014', 'sku': 'OBC-DWA-006', 'price': 4.99,
        'title': 'Good Things Take Time Print | Motivational Wall Art | Retro Typography Poster | Instant Download',
        'tags': ['motivational print','quote wall art','typography poster','good things print','retro wall art',
                 'instant download','printable art','digital download','inspirational art',
                 'office wall art','dorm room art','bold art print','home decor print'],
        'hook': 'A bold reminder for every wall — because good things really do take time.',
        'art_desc': (
            'Bold burnt-orange retro block typography on a warm cream background. Clean, graphic, modern motivational '
            'art perfect for an office, studio, or living room.'
        ),
    },
    {
        'pid': 'DP1015', 'sku': 'OBC-DWA-007', 'price': 4.99,
        'title': 'She Believed She Could So She Did Print | Empowerment Wall Art | Inspirational Quote Decor | Instant Download',
        'tags': ['she believed print','empowerment art','quote wall art','motivational print','girl boss art',
                 'instant download','printable art','digital download','inspirational art',
                 'feminist wall art','bedroom wall art','dorm room decor','home decor print'],
        'hook': 'For every woman who dared to believe — and then proved it.',
        'art_desc': (
            'Powerful hand-lettered motivational quote in cream white on a dramatic black background with bronze '
            'brushstroke chevron wings. Bold, empowering, unforgettable wall art.'
        ),
    },
    {
        'pid': 'DP1016', 'sku': 'OBC-DWA-008', 'price': 7.99,
        'title': 'White Roses and Hydrangeas Print | Floral Oil Painting Wall Art | Botanical Home Decor | Instant Download',
        'tags': ['floral wall art','botanical print','roses wall art','oil painting print','white flowers art',
                 'instant download','printable art','digital download','floral home decor',
                 'cottage core art','flower art print','bedroom wall art','home decor print'],
        'hook': 'Bring the beauty of a garden into your home — classic, timeless, and effortlessly elegant.',
        'art_desc': (
            'Lush oil painting of white hydrangeas and cream roses in a rustic brown ceramic vase, rendered in rich '
            'impasto brushwork against a warm golden-tan background.'
        ),
    },
    {
        'pid': 'DP1018', 'sku': 'OBC-DWA-009', 'price': 6.99,
        'title': 'Minimalist Tree and Moon Print | Japandi Wall Art | Neutral Boho Decor | Instant Download',
        'tags': ['minimalist print','japandi wall art','tree wall art','boho moon print','neutral wall art',
                 'instant download','printable art','digital download','minimalist decor',
                 'nature wall art','tree art print','boho home decor','home decor print'],
        'hook': 'Calm, minimal, poetic — this print brings quiet beauty to any space.',
        'art_desc': (
            'A bare winter tree silhouette set against a split grey-and-cream background, with a large amber golden '
            'circle (sun or moon) rising behind it. Japandi/Scandinavian minimalist aesthetic.'
        ),
    },
    {
        'pid': 'DP1019', 'sku': 'OBC-DWA-010', 'price': 7.99,
        'title': 'Mountain Wildflower Meadow Print | Sunset Landscape Art | Nature Wall Decor | Instant Download',
        'tags': ['landscape print','mountain wall art','wildflower meadow','sunset art print','nature wall art',
                 'instant download','printable art','digital download','landscape art',
                 'mountain decor','wildflower art','scenic art print','home decor print'],
        'hook': 'Lose yourself in the golden hour — a sweeping mountain meadow at the magic moment.',
        'art_desc': (
            'Rich oil painting of a wildflower meadow at golden hour — yellow daisies and wildflowers in the '
            'foreground, pine trees backlit by a starburst sunburst, misty blue mountains in the distance.'
        ),
    },
    {
        'pid': 'DP1020', 'sku': 'OBC-DWA-011', 'price': 6.99,
        'title': 'Poppy Field Print | Wildflower Wall Art | Folk Art Floral Decor | Colorful Home Art | Instant Download',
        'tags': ['poppy print','wildflower art','floral wall art','folk art print','colorful wall art',
                 'instant download','printable art','digital download','poppy wall art',
                 'flower art print','cottage core art','bedroom wall art','home decor print'],
        'hook': 'Bright, joyful, and bursting with life — this poppy field print brings summer into any room.',
        'art_desc': (
            'Cheerful folk art-style wildflower garden painting — red poppies, orange ranunculus, yellow buttercups, '
            'and pink cosmos on a soft cream-and-sage background.'
        ),
    },
    {
        'pid': 'DP1021', 'sku': 'OBC-DWA-012', 'price': 7.99,
        'title': 'Pub Dog Print | Funny Dog Wall Art | Golden Retriever Oil Painting | Man Cave Decor | Instant Download',
        'tags': ['dog wall art','pub dog print','golden retriever','funny wall art','man cave decor',
                 'instant download','printable art','digital download','dog lover gift',
                 'pet portrait art','humorous art','bar decor print','home decor print'],
        'hook': "He's cultured. He's distinguished. He's got a pint and he's not sharing.",
        'art_desc': (
            'Impressionist oil painting of a golden retriever wearing round glasses, sitting at a pub bar with a full '
            'pint of amber beer. Warm candlelit pub atmosphere, rich amber and brown tones.'
        ),
    },
    {
        'pid': 'DP1022', 'sku': 'OBC-DWA-013', 'price': 7.99,
        'title': 'Full Moon Over Ocean Print | Celestial Night Sky Wall Art | Lunar Home Decor | Instant Download',
        'tags': ['moon print','celestial art','ocean wall art','full moon print','night sky art',
                 'instant download','printable art','digital download','lunar wall art',
                 'moon wall decor','celestial decor','moody wall art','home decor print'],
        'hook': 'Feel the pull of the tide — a breathtaking full moon rising over a calm, dark sea.',
        'art_desc': (
            "Photorealistic digital art of a massive golden supermoon rising over a still, dark ocean. The moon's "
            'surface detail is crisp and stunning; a ribbon of gold moonlight reflects on the water.'
        ),
    },
    {
        'pid': 'DP1023', 'sku': 'OBC-DWA-014', 'price': 7.99,
        'title': 'Floral Astronaut Print | Dark Fantasy Space Wall Art | Galaxy Decor | Moody Art Poster | Instant Download',
        'tags': ['astronaut print','space wall art','galaxy art print','dark fantasy art','moody wall art',
                 'instant download','printable art','digital download','sci fi art print',
                 'space decor','astronaut decor','dark art print','home decor print'],
        'hook': 'Where the cosmos meets the garden — dark, mysterious, and unforgettable.',
        'art_desc': (
            'A dark fantasy oil painting of an astronaut figure covered in ornate floral relief carvings. The visor '
            'reflects a glowing spiral galaxy in gold and blue. Pink luminous orbs float in the surrounding deep '
            'navy and orange nebula background.'
        ),
    },
    {
        'pid': 'DP1024', 'sku': 'OBC-DWA-015', 'price': 7.99,
        'title': 'Classic Muscle Car Print | Vintage Chevelle Wall Art | Garage Decor | Car Enthusiast Gift | Instant Download',
        'tags': ['muscle car print','vintage car art','garage wall decor','car art print','classic car art',
                 'instant download','printable art','digital download','car lover gift',
                 'man cave decor','automotive art','retro car print','home decor print'],
        'hook': 'Built for legends. Perfect for your wall.',
        'art_desc': (
            'Dramatic studio photography-style art print of a teal Chevrolet Chevelle SS with white racing stripes, '
            'shot in low-key studio lighting against a pure black background. Every chrome detail gleams.'
        ),
    },
    {
        'pid': 'DP1025', 'sku': 'OBC-DWA-016', 'price': 6.99,
        'title': 'Colorful Skull Print | Bold Pop Art Wall Decor | Maximalist Art Poster | Instant Download',
        'tags': ['skull art print','pop art wall art','colorful skull','bold wall art','maximalist decor',
                 'instant download','printable art','digital download','skull wall decor',
                 'edgy home decor','vibrant art print','gallery wall art','home decor print'],
        'hook': 'Bold, vivid, unapologetic — this skull art commands attention.',
        'art_desc': (
            'Expressionist oil painting of a human skull rendered in vivid geometric blocks of red, orange, '
            'cerulean blue, and teal, set against a warm swirling golden-yellow background with thick impasto '
            'brushwork.'
        ),
    },
]


# ── Description builder ─────────────────────────────────────────────────────
def build_description(p: dict) -> str:
    return f"""{p['hook']}

{p['art_desc']}

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT YOU GET
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution digital JPEG file — print-ready at any size
✅ Sizes included: 5×7, 8×10, 11×14, 16×20 inches (all in one file)
✅ 300 DPI — sharp, gallery-quality prints
✅ Instant digital download — no physical item shipped

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ HOW TO PRINT
━━━━━━━━━━━━━━━━━━━━━━━━
• Print at home on your inkjet or laser printer
• Upload to Walmart Photo, Walgreens, CVS, Staples, or Costco for cheap prints
• Use Mpix, Artifact Uprising, or Bay Photo for premium fine art prints
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
A: Yes — the file is 300 DPI, which is professional print quality at all standard sizes up to 20×30 inches.

Q: What paper should I use?
A: Matte photo paper or fine art paper gives the best results. Glossy works too for a vibrant look.

Q: Is this a physical print?
A: No — this is a digital download only. You download and print yourself.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use."""


# ── Pillow mockup builder ───────────────────────────────────────────────────
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


def build_mockup(art_path, out_path, wall_top, wall_bot, mat_col, frame_col,
                 frame_w=14, mat_w=46):
    art = Image.open(art_path).convert('RGB')
    art_w = int(CANVAS * 0.50)
    art_h = int(art_w * art.height / art.width)
    art = art.resize((art_w, art_h), Image.LANCZOS)
    full_w = art_w + 2 * mat_w + 2 * frame_w
    full_h = art_h + 2 * mat_w + 2 * frame_w
    bg = gradient_bg(CANVAS, wall_top, wall_bot)
    # Drop shadow
    shadow = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    sx = (CANVAS - full_w) // 2 + 14
    sy = (CANVAS - full_h) // 2 + 18
    ImageDraw.Draw(shadow).rectangle([sx, sy, sx + full_w, sy + full_h], fill=(0, 0, 0, 100))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=20))
    bg = bg.convert('RGBA')
    bg = Image.alpha_composite(bg, shadow).convert('RGB')
    # Frame
    fx = (CANVAS - full_w) // 2
    fy = (CANVAS - full_h) // 2
    ImageDraw.Draw(bg).rectangle([fx, fy, fx + full_w, fy + full_h], fill=frame_col)
    # Mat
    mx, my = fx + frame_w, fy + frame_w
    ImageDraw.Draw(bg).rectangle([mx, my, mx + art_w + 2 * mat_w, my + art_h + 2 * mat_w], fill=mat_col)
    # Art
    bg.paste(art, (mx + mat_w, my + mat_w))
    # Baseboard
    br = max(wall_bot[0] - 18, 0)
    bg2 = max(wall_bot[1] - 18, 0)
    bb = max(wall_bot[2] - 18, 0)
    ImageDraw.Draw(bg).line([(0, CANVAS - 130), (CANVAS, CANVAS - 130)], fill=(br, bg2, bb), width=3)
    bg.save(out_path, 'JPEG', quality=92)
    print(f'    Saved mockup: {os.path.basename(out_path)}')


# ── Size guide builder ──────────────────────────────────────────────────────
def build_size_guide(out_path):
    W = H = CANVAS
    img = Image.new('RGB', (W, H), (245, 241, 235))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype(FONT_BOLD, 88)
        font_label = ImageFont.truetype(FONT_BOLD, 52)
        font_sub   = ImageFont.truetype(FONT_REG,  40)
    except Exception:
        font_title = font_label = font_sub = ImageFont.load_default()

    charcoal = (44, 44, 42)
    mid_gray = (150, 148, 144)
    frame_col = (140, 118, 90)

    # Title
    title = 'PRINT SIZES INCLUDED'
    draw.text((W // 2, 110), title, font=font_title, fill=charcoal, anchor='mm')

    # Subtitle
    draw.text((W // 2, 210), 'All sizes included in one high-res file  •  300 DPI  •  Print at home or at a print shop',
              font=font_sub, fill=mid_gray, anchor='mm')

    # Divider
    draw.line([(160, 260), (W - 160, 260)], fill=(200, 196, 188), width=3)

    # Sizes: (label, inches_w, inches_h)
    sizes = [('5×7"', 5, 7), ('8×10"', 8, 10), ('11×14"', 11, 14), ('16×20"', 16, 20)]
    # Scale so largest (16×20) fits nicely
    max_w_in = max(s[1] for s in sizes)
    max_h_in = max(s[2] for s in sizes)

    area_top = 310
    area_bot = H - 180
    area_h = area_bot - area_top

    # Proportional scale factor: fit largest box within area
    scale = min((W - 600) / (len(sizes) * max_w_in * 10), area_h / (max_h_in * 10)) * 7.5

    spacing = (W - 300) / len(sizes)
    start_x = 150 + spacing / 2

    for i, (label, w_in, h_in) in enumerate(sizes):
        box_w = int(w_in * scale)
        box_h = int(h_in * scale)
        cx = int(start_x + i * spacing)
        # Align bottoms
        rect_bottom = area_bot - 80
        rect_top = rect_bottom - box_h
        rect_left = cx - box_w // 2
        rect_right = cx + box_w // 2

        # Frame shadow
        draw.rectangle([rect_left + 6, rect_top + 8, rect_right + 6, rect_bottom + 8],
                       fill=(200, 196, 188))
        # Frame
        draw.rectangle([rect_left, rect_top, rect_right, rect_bottom], fill=frame_col)
        # Mat (8px inside frame)
        mat_inset = 8
        draw.rectangle([rect_left + mat_inset, rect_top + mat_inset,
                        rect_right - mat_inset, rect_bottom - mat_inset],
                       fill=(250, 248, 244))
        # Inner art area (another 12px)
        art_inset = mat_inset + 12
        draw.rectangle([rect_left + art_inset, rect_top + art_inset,
                        rect_right - art_inset, rect_bottom - art_inset],
                       fill=(220, 218, 212))

        # Size label below
        draw.text((cx, rect_bottom + 30), label, font=font_label, fill=charcoal, anchor='mm')
        # Inches detail
        draw.text((cx, rect_bottom + 90), f'{w_in}×{h_in} inches', font=font_sub, fill=mid_gray, anchor='mm')

    # Footer
    draw.line([(160, H - 110), (W - 160, H - 110)], fill=(200, 196, 188), width=2)
    draw.text((W // 2, H - 60), '© OnBrandCraftz  •  Personal use only  •  Not for resale',
              font=font_sub, fill=mid_gray, anchor='mm')

    img.save(out_path, 'JPEG', quality=92)
    print(f'    Saved size guide: {os.path.basename(out_path)}')


# ── Etsy API helpers ────────────────────────────────────────────────────────
def api_sleep(secs=1.0):
    time.sleep(secs)


def upload_image_with_retry(listing_id, image_path, rank):
    for attempt in range(2):
        try:
            result = client.upload_listing_image(listing_id, image_path, rank=rank)
            return result
        except EtsyAPIError as e:
            if e.status == 500 and attempt == 0:
                print(f'      500 on image upload, retrying in 5s...')
                time.sleep(5)
                continue
            if e.status == 429:
                print(f'      429 rate limit, waiting 10s...')
                time.sleep(10)
                return client.upload_listing_image(listing_id, image_path, rank=rank)
            raise
    raise EtsyAPIError(500, 'Upload failed after retry')


def upload_file_with_retry(listing_id, file_path, rank=1):
    for attempt in range(2):
        try:
            result = client.upload_listing_file(listing_id, file_path, rank=rank)
            return result
        except EtsyAPIError as e:
            if e.status == 500 and attempt == 0:
                print(f'      500 on file upload, retrying in 5s...')
                time.sleep(5)
                continue
            if e.status == 429:
                print(f'      429 rate limit, waiting 10s...')
                time.sleep(10)
                return client.upload_listing_file(listing_id, file_path, rank=rank)
            raise
    raise EtsyAPIError(500, 'File upload failed after retry')


def set_listing_sku(listing_id, sku):
    """GET inventory, strip read-only fields, set SKU, PUT back."""
    api_sleep()
    inv_url = f"{BASE_URL}/listings/{listing_id}/inventory"
    api_key_header = (f"{client.client_id}:{client.client_secret}"
                      if client.client_secret else client.api_key)
    headers_get = {
        'x-api-key': api_key_header,
        'Authorization': f'Bearer {client.access_token}',
    }
    req = urllib.request.Request(inv_url, headers=headers_get, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            inv = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f'      GET inventory failed {e.code}: {body[:200]}')
        return False

    products = inv.get('products', [])
    readiness = inv.get('readiness_state_id', 0)

    # Clean read-only fields from products/offerings
    clean_products = []
    for prod in products:
        clean_prod = {}
        if 'property_values' in prod:
            clean_pvs = []
            for pv in prod['property_values']:
                cpv = {k: v for k, v in pv.items() if k != 'scale_name'}
                clean_pvs.append(cpv)
            clean_prod['property_values'] = clean_pvs
        offerings = []
        for off in prod.get('offerings', []):
            clean_off = {k: v for k, v in off.items()
                         if k not in ('offering_id', 'is_deleted')}
            # Convert price to float if dict
            if isinstance(clean_off.get('price'), dict):
                p = clean_off['price']
                clean_off['price'] = p.get('amount', 0) / max(p.get('divisor', 100), 1)
            offerings.append(clean_off)
        clean_prod['offerings'] = offerings
        # Set SKU
        clean_prod['sku'] = sku
        # Strip product_id
        # (do NOT include product_id per instructions)
        clean_products.append(clean_prod)

    put_body = json.dumps({
        'products': clean_products,
        'readiness_state_id': readiness,
    }).encode()

    headers_put = {
        'Content-Type': 'application/json',
        'x-api-key': api_key_header,
        'Authorization': f'Bearer {client.access_token}',
    }
    req_put = urllib.request.Request(inv_url, data=put_body, headers=headers_put, method='PUT')
    try:
        with urllib.request.urlopen(req_put, timeout=15) as resp:
            resp.read()
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f'      PUT inventory failed {e.code}: {body[:300]}')
        return False


# ── Main listing loop ───────────────────────────────────────────────────────
results = {}

for p in PRODUCTS:
    pid = p['pid']
    print(f'\n{"="*60}')
    print(f'Processing {pid} — {p["title"][:60]}...')
    result = {'pid': pid, 'listing_id': None, 'photos': 0, 'sku_set': False, 'activated': False, 'error': None}
    results[pid] = result

    try:
        # 1. Build listing images directory
        img_dir = os.path.join(PRODUCTS_DIR, f'{pid}_listing_images')
        os.makedirs(img_dir, exist_ok=True)

        art_path = os.path.join(PRODUCTS_DIR, f'{pid}.jpg')
        if not os.path.exists(art_path):
            raise FileNotFoundError(f'Art file not found: {art_path}')

        # 2. Build 3 frame mockups
        print(f'  Building mockups...')
        mockup_warm = os.path.join(img_dir, f'{pid}_mockup_warm.jpg')
        mockup_sage = os.path.join(img_dir, f'{pid}_mockup_sage.jpg')
        mockup_dark = os.path.join(img_dir, f'{pid}_mockup_dark.jpg')
        size_guide  = os.path.join(img_dir, f'{pid}_size_guide.jpg')

        build_mockup(art_path, mockup_warm,
                     wall_top=(240,234,221), wall_bot=(225,218,204),
                     mat_col=(250,248,244), frame_col=(82,60,40))
        build_mockup(art_path, mockup_sage,
                     wall_top=(192,204,188), wall_bot=(175,187,170),
                     mat_col=(250,249,246), frame_col=(140,110,72))
        build_mockup(art_path, mockup_dark,
                     wall_top=(52,56,62), wall_bot=(40,44,50),
                     mat_col=(252,250,247), frame_col=(180,152,92),
                     frame_w=16, mat_w=52)
        build_size_guide(size_guide)

        # 3. Create listing draft
        print(f'  Creating Etsy listing draft...')
        api_sleep()
        listing_data = {
            'title': p['title'],
            'description': build_description(p),
            'price': p['price'],
            'tags': p['tags'],
            'quantity': 999,
            'type': 'download',
            'who_made': 'i_did',
            'when_made': '2020_2025',
            'taxonomy_id': 2078,
            'shop_section_id': SECTION_ID,
        }
        listing_resp = client.create_listing(listing_data)
        listing_id = listing_resp['listing_id']
        result['listing_id'] = listing_id
        print(f'  Created listing {listing_id}')

        # 4. Upload photos
        print(f'  Uploading photos...')
        photos_uploaded = 0

        # Photo 1: original art (rank 1)
        api_sleep()
        upload_image_with_retry(listing_id, art_path, rank=1)
        photos_uploaded += 1
        print(f'    Photo 1/5 (original art) uploaded')

        # Photo 2: warm mockup (rank 2)
        api_sleep()
        upload_image_with_retry(listing_id, mockup_warm, rank=2)
        photos_uploaded += 1
        print(f'    Photo 2/5 (warm mockup) uploaded')

        # Photo 3: sage mockup (rank 3)
        api_sleep()
        upload_image_with_retry(listing_id, mockup_sage, rank=3)
        photos_uploaded += 1
        print(f'    Photo 3/5 (sage mockup) uploaded')

        # Photo 4: dark mockup (rank 4)
        api_sleep()
        upload_image_with_retry(listing_id, mockup_dark, rank=4)
        photos_uploaded += 1
        print(f'    Photo 4/5 (dark mockup) uploaded')

        # Photo 5: size guide (rank 5)
        api_sleep()
        upload_image_with_retry(listing_id, size_guide, rank=5)
        photos_uploaded += 1
        print(f'    Photo 5/5 (size guide) uploaded')

        result['photos'] = photos_uploaded

        # 5. Attach digital file
        print(f'  Attaching digital file...')
        api_sleep()
        upload_file_with_retry(listing_id, art_path, rank=1)
        print(f'    Digital file attached')

        # 6. Activate listing
        print(f'  Activating listing...')
        api_sleep()
        client.update_listing(listing_id, {'state': 'active'})
        result['activated'] = True
        print(f'  Listing activated')

        # 7. Set SKU via inventory
        print(f'  Setting SKU {p["sku"]}...')
        sku_ok = set_listing_sku(listing_id, p['sku'])
        result['sku_set'] = sku_ok
        print(f'  SKU set: {sku_ok}')

        # 8. Update DataStore
        store = DataStore()
        products_list = store.get('digital_products', default=[])
        found = False
        for prod in products_list:
            if prod.get('id') == pid:
                prod['etsy_listing_id'] = str(listing_id)
                prod['status'] = 'listed'
                found = True
                break
        if not found:
            products_list.append({
                'id': pid,
                'etsy_listing_id': str(listing_id),
                'status': 'listed',
            })
        store.set(products_list, 'digital_products')
        store.save()
        print(f'  DataStore updated')

        print(f'  SUCCESS: {pid} listed at https://www.etsy.com/listing/{listing_id}')

    except Exception as e:
        result['error'] = str(e)
        print(f'  ERROR: {pid}: {e}')

# ── Final summary ────────────────────────────────────────────────────────────
print('\n' + '='*80)
print('FINAL SUMMARY')
print('='*80)
print(f'{"PID":<10} {"Listing ID":<14} {"Photos":<8} {"SKU Set":<10} {"Activated":<12} {"Status"}')
print('-'*80)
for pid, r in results.items():
    status = 'OK' if r['activated'] and not r['error'] else (r['error'] or 'PARTIAL')
    print(f'{r["pid"]:<10} {str(r["listing_id"] or "N/A"):<14} {str(r["photos"])+"/5":<8} '
          f'{str(r["sku_set"]):<10} {str(r["activated"]):<12} {status}')
print('='*80)
