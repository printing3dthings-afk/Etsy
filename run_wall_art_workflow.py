#!/usr/bin/env python3
"""
Wall art listing workflow:
1. Approve DP1000-DP1003 and generate listing drafts
2. Publish listings to Etsy
3. Generate photos (DALL-E for frames/lifestyle, Pillow for size guide)
4. Upload photos to listings
5. Activate listings and assign to Digital Downloads section
6. Set SKUs

Also generates lifestyle photos for 3D printed listings.
"""

import os, sys, json, base64, urllib.request, urllib.error, time
from datetime import date

sys.path.insert(0, '/home/user/Etsy')
from dotenv import load_dotenv
load_dotenv('/home/user/Etsy/.env')

from tools.data_store import DataStore
from tools.etsy_listing_tools import _generate_listing_content, _publish_digital_listing
from tools.etsy_api import EtsyAPIClient, EtsyAPIError

# ── Config ────────────────────────────────────────────────────────────────────

PRODUCT_FILES_DIR = '/home/user/Etsy/data/digital_products/product_files'
DIGITAL_DOWNLOADS_SECTION_ID = 58657103  # confirmed from API

SKUS = {
    'DP1000': 'OBC-DWA-001',
    'DP1001': 'OBC-DWA-002',
    'DP1002': 'OBC-DWA-003',
    'DP1003': 'OBC-DWA-004',
}

WALL_ART = {
    'DP1000': {
        'title': 'Boho Wildflower Botanical Print | Sage Green Wall Art | Watercolor Printable Art | Instant Download | Boho Home Decor',
        'price': 4.99,
        'tags': ['botanical print', 'boho wall art', 'wildflower print', 'printable art', 'instant download', 'digital download', 'watercolor print', 'boho home decor', 'sage green decor', 'wall art print', 'botanical art', 'printable wall art', 'digital art'],
        'art_description': 'watercolor illustration of a boho wildflower bouquet — tall golden pampas grass on the left, purple lavender sprigs, white daisies with yellow centers, round rose hip pods, small sage green eucalyptus leaves — all on a warm cream ivory background with soft watercolor washes',
        'frame_style': 'thin natural wood frame with white mat',
        'room_description': 'a boho watercolor wildflower bouquet with pampas grass, lavender sprigs, white daisies, and eucalyptus leaves on warm ivory background',
    },
    'DP1001': {
        'title': 'Eucalyptus Branch Print | Botanical Wall Art | Sage Green Printable Art | Instant Download | Minimalist Home Decor',
        'price': 3.99,
        'tags': ['eucalyptus print', 'botanical wall art', 'sage green art', 'printable art', 'instant download', 'digital download', 'watercolor print', 'minimalist wall art', 'botanical print', 'wall art print', 'digital art', 'printable wall art', 'boho decor'],
        'art_description': 'single elegant eucalyptus branch arcing diagonally across the frame with round silver-dollar eucalyptus leaves in soft sage green with golden stem and tiny seed pods on warm ivory cream background with subtle watercolor texture',
        'frame_style': 'thin natural wood frame with white mat',
        'room_description': 'a single elegant eucalyptus branch arcing diagonally with sage green silver-dollar leaves and golden stem on warm ivory background',
    },
    'DP1002': {
        'title': 'Sage and Lavender Botanical Print | Dusty Rose Wall Art | Watercolor Printable Art | Instant Download | Boho Home Decor',
        'price': 3.99,
        'tags': ['sage lavender print', 'botanical wall art', 'dusty rose art', 'printable art', 'instant download', 'digital download', 'watercolor print', 'boho wall art', 'botanical print', 'wall art print', 'digital art', 'printable wall art', 'lavender decor'],
        'art_description': 'botanical bouquet of sage leaves with long green and dusty rose mauve leaves with three tall purple lavender sprigs rising above, stems tied together at base, on warm cream background — loose watercolor botanical illustration',
        'frame_style': 'thin black frame with white mat',
        'room_description': 'a sage and lavender botanical bouquet with dusty rose leaves and purple lavender sprigs tied at the stem on warm cream background',
    },
    'DP1003': {
        'title': 'Pampas Grass Print | Neutral Boho Wall Art | Minimalist Printable Art | Instant Download | Boho Home Decor',
        'price': 3.99,
        'tags': ['pampas grass print', 'boho wall art', 'neutral wall art', 'printable art', 'instant download', 'digital download', 'minimalist print', 'boho home decor', 'pampas grass decor', 'wall art print', 'digital art', 'printable wall art', 'neutral decor'],
        'art_description': 'single pampas grass plume — delicate feathery fronds in warm golden-beige wheat tones, centered on a warm cream ivory background — minimalist and elegant watercolor illustration',
        'frame_style': 'thin natural wood frame with white mat',
        'room_description': 'a single minimalist pampas grass plume with delicate feathery fronds in warm golden-beige wheat tones on warm ivory cream background',
    },
}

DESCRIPTIONS = {
    'DP1000': """Bring effortless boho beauty into your home — print and hang in minutes.

This boho wildflower botanical watercolor print features golden pampas grass, purple lavender sprigs, white daisies, and sage green eucalyptus leaves on a warm cream background. The soft, painterly watercolor style gives it that artisan quality that makes guests ask "where did you find that?"

WHAT'S INCLUDED
- High-resolution JPEG file at 300 DPI — print-ready for crisp results at any size
- One versatile file prints beautifully at 5x7, 8x10, 11x14, or 16x20 (simply resize before printing)
- Instant digital download — no waiting, no shipping
- Personal use license

FILE FORMATS & SIZES
- Format: JPEG, 300 DPI
- Recommended print sizes: 5x7, 8x10, 11x14, 16x20
- Color space: RGB (prints true to screen on most home and professional printers)

HOW TO USE
1. Download your file immediately after purchase from your Etsy downloads page
2. Open in any photo editor or send directly to your printer or a print shop
3. For best results, print on matte photo paper or satin cardstock
4. Frame with any standard-size frame from IKEA, Target, or Amazon

PRINTING TIPS
- Home printer: matte photo paper or cardstock gives the warmest finish
- Print shop: Staples, FedEx, or a local print lab all work great
- Standard frames are available in 5x7, 8x10, 11x14 — no custom framing needed
- Frame suggestions: natural wood, white, or thin black for a boho or modern look

FAQ
Q: When will I get my files?
A: Instantly — as soon as payment clears, Etsy delivers your download link.

Q: Can I print multiple copies?
A: Yes — for personal use across your own home, unlimited prints are included.

Q: Can I print this at a copy shop?
A: Absolutely. The file is 300 DPI and sized for professional print quality.

Q: Is this a physical item?
A: No — this is a digital download only. Nothing is shipped.

Q: What frame looks best?
A: Natural wood or white frames complement the warm sage green and dusty rose palette perfectly. A white mat adds a gallery feel.

COPYRIGHT
Personal use only. Not for resale, redistribution, or commercial use. © OnBrandCraftz""",

    'DP1001': """Bring calm, minimalist botanical beauty to any wall — instant download, print at home.

This elegant eucalyptus branch print features a single arcing branch with soft sage green silver-dollar leaves and a warm golden stem on a warm ivory background. The delicate, minimalist watercolor style pairs beautifully with boho, Scandinavian, and modern farmhouse interiors.

WHAT'S INCLUDED
- High-resolution JPEG file at 300 DPI — print-ready and crisp at any size
- Prints beautifully at 5x7, 8x10, 11x14, or 16x20 (resize before printing)
- Instant digital download — no waiting, no shipping
- Personal use license

FILE FORMATS & SIZES
- Format: JPEG, 300 DPI
- Recommended print sizes: 5x7, 8x10, 11x14, 16x20
- Color space: RGB

HOW TO USE
1. Download your file immediately after purchase
2. Open in any photo editor or send directly to a printer or print shop
3. Print on matte photo paper for the most natural, organic finish
4. Frame in natural wood, white, or black — all complement the sage green palette

PRINTING TIPS
- Matte paper gives the most botanical, art-gallery feel
- Pairs beautifully as a companion piece to wildflower and lavender botanicals
- Works as a standalone minimalist piece or in a gallery wall arrangement

FAQ
Q: When will I get my file?
A: Instantly after purchase — Etsy delivers your download link automatically.

Q: Can I print multiple copies?
A: Yes — for personal use in your own home, unlimited prints are included.

Q: Is this a physical item?
A: No — digital download only. Nothing is shipped.

Q: What size frame should I use?
A: Standard 8x10 or 11x14 frames work perfectly. A thin natural wood frame with white mat gives a gallery-quality result.

COPYRIGHT
Personal use only. Not for resale, redistribution, or commercial use. © OnBrandCraftz""",

    'DP1002': """Add a soft, romantic botanical touch to your walls — download instantly, print beautifully.

This sage and lavender botanical print features a loose watercolor bouquet of sage leaves and tall purple lavender sprigs in dusty rose, sage green, and muted lavender on a warm cream background. It pairs perfectly with natural wood, linen, and boho home decor.

WHAT'S INCLUDED
- High-resolution JPEG file at 300 DPI — print-ready and sharp at any size
- Prints beautifully at 5x7, 8x10, 11x14, or 16x20 (resize before printing)
- Instant digital download — no shipping, no waiting
- Personal use license

FILE FORMATS & SIZES
- Format: JPEG, 300 DPI
- Recommended print sizes: 5x7, 8x10, 11x14, 16x20
- Color space: RGB

HOW TO USE
1. Download immediately after purchase from your Etsy downloads page
2. Open in any photo editor or send to your home printer or a print shop
3. Print on matte photo paper or satin cardstock for the richest botanical colors
4. Frame and hang — looks gorgeous in a black thin frame with white mat

PRINTING TIPS
- Dusty rose and lavender tones print truest on matte or satin paper
- Coordinates beautifully with the Boho Wildflower and Eucalyptus prints for a gallery wall set
- Any standard-size frame from IKEA, Target, or Amazon fits perfectly

FAQ
Q: When will I receive my file?
A: Instantly — Etsy delivers your download as soon as payment is confirmed.

Q: Can I print this multiple times?
A: Yes — personal use includes unlimited prints for your own home.

Q: Is this a physical print or a digital file?
A: Digital only — nothing is shipped. You download and print yourself.

Q: What frame goes well with this?
A: A thin black frame with white mat, or a white frame with no mat, both look stunning.

COPYRIGHT
Personal use only. Not for resale, redistribution, or commercial use. © OnBrandCraftz""",

    'DP1003': """Minimal. Serene. Effortlessly boho — this pampas grass print brings warmth to any wall.

A single elegant pampas grass plume in warm golden wheat tones floats on a clean warm ivory background. The minimalist composition makes it a perfect standalone statement piece or neutral anchor in a boho gallery wall arrangement.

WHAT'S INCLUDED
- High-resolution JPEG file at 300 DPI — crisp and print-ready at any size
- Prints beautifully at 5x7, 8x10, 11x14, or 16x20 (resize before printing)
- Instant digital download — no shipping, no waiting
- Personal use license

FILE FORMATS & SIZES
- Format: JPEG, 300 DPI
- Recommended print sizes: 5x7, 8x10, 11x14, 16x20
- Color space: RGB

HOW TO USE
1. Download your file immediately after purchase
2. Open in any photo editor or send to a home printer or print shop
3. Print on matte or satin photo paper for the warmest, most natural finish
4. Frame in natural wood, white, or beige — all complement the neutral warm palette

PRINTING TIPS
- Natural wood frames are especially stunning with the warm golden wheat tones
- Looks beautiful as a single piece above a bed, sofa, or console table
- Pairs perfectly with sage green, terracotta, and linen tones in the room

FAQ
Q: When will I get my file?
A: Instantly — as soon as your payment clears, Etsy sends your download link.

Q: Can I print multiple copies?
A: Yes — personal use includes unlimited home prints.

Q: Is this a physical item?
A: No — digital download only. You download and print it yourself.

Q: What size works best?
A: 11x14 or 16x20 makes the most visual impact. An 8x10 is perfect for a side table or smaller wall.

COPYRIGHT
Personal use only. Not for resale, redistribution, or commercial use. © OnBrandCraftz""",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def gen_image(prompt, out_path):
    """Generate image with DALL-E gpt-image-1 and save to out_path."""
    api_key = os.getenv('OPENAI_API_KEY', '')
    payload = json.dumps({
        'model': 'gpt-image-1',
        'prompt': prompt,
        'n': 1,
        'size': '1024x1024',
        'quality': 'medium'
    }).encode()
    req = urllib.request.Request(
        'https://api.openai.com/v1/images/generations',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    )
    print(f'    Generating image -> {os.path.basename(out_path)}...')
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read())
    img_b64 = data['data'][0]['b64_json']
    with open(out_path, 'wb') as f:
        f.write(base64.b64decode(img_b64))
    size_kb = os.path.getsize(out_path) // 1024
    print(f'    Saved {os.path.basename(out_path)} ({size_kb} KB)')


def gen_size_guide(pid, out_path):
    """Create size guide graphic using Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1024, 1024
    bg = (252, 248, 242)
    img = Image.new('RGB', (W, H), bg)
    draw = ImageDraw.Draw(img)

    # Load fonts
    serif_path = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
    sans_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    try:
        font_title = ImageFont.truetype(serif_path, 40)
        font_sub = ImageFont.truetype(sans_path, 22)
        font_label = ImageFont.truetype(sans_path, 28)
        font_note = ImageFont.truetype(sans_path, 18)
    except:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_label = font_title
        font_note = font_title

    # Title
    title = 'Size Guide'
    draw.text((W//2, 60), title, fill=(60, 50, 40), font=font_title, anchor='mm')

    # Subtitle
    sub = 'Prints to any size — just resize before printing'
    draw.text((W//2, 105), sub, fill=(100, 90, 80), font=font_note, anchor='mm')

    # Proportional rectangles for 5x7, 8x10, 11x14
    # Using ratio relative to 11x14 (tallest)
    sizes = [
        ('5×7"', 5, 7),
        ('8×10"', 8, 10),
        ('11×14"', 11, 14),
    ]
    base_h = 400  # px for the tallest (11x14)
    base_w_unit = base_h / 14  # pixels per inch-unit

    total_w = 0
    rects = []
    gap = 60
    for label, w_in, h_in in sizes:
        rw = int(w_in * base_w_unit)
        rh = int(h_in * base_w_unit)
        rects.append((label, rw, rh))
        total_w += rw
    total_w += gap * (len(rects) - 1)

    x_start = (W - total_w) // 2
    y_top_base = 200  # top of tallest rect
    max_rh = max(r[2] for r in rects)

    x = x_start
    for label, rw, rh in rects:
        # Bottom-align rectangles
        y_top = y_top_base + (max_rh - rh)
        y_bot = y_top_base + max_rh
        # Draw white rect with border
        draw.rectangle([x, y_top, x + rw, y_bot], fill=(255, 255, 255), outline=(180, 170, 160), width=2)
        # Label below
        draw.text((x + rw // 2, y_bot + 20), label, fill=(60, 50, 40), font=font_label, anchor='mt')
        x += rw + gap

    # Note at bottom
    note1 = 'Recommended print sizes: 5×7 • 8×10 • 11×14 • 16×20'
    note2 = '300 DPI • JPEG • Print at home or any print shop'
    draw.text((W//2, 760), note1, fill=(100, 90, 80), font=font_note, anchor='mm')
    draw.text((W//2, 790), note2, fill=(100, 90, 80), font=font_note, anchor='mm')

    img.save(out_path, 'JPEG', quality=92)
    print(f'    Size guide saved: {os.path.basename(out_path)}')


def update_listing_inventory_with_sku(client, listing_id, sku, price):
    """Set SKU on a listing using the inventory endpoint."""
    import urllib.parse
    # First GET to get readiness_state_id
    try:
        url_get = f'https://openapi.etsy.com/v3/application/listings/{listing_id}/inventory'
        req = client._build_request('GET', url_get, None)
        with urllib.request.urlopen(req, timeout=15) as resp:
            inv = json.loads(resp.read().decode())
    except Exception as e:
        print(f'    GET inventory error: {e}')
        return False

    products = inv.get('products', [])
    if not products:
        # Build minimal product
        product = {
            'sku': sku,
            'offerings': [{'price': float(price), 'quantity': 999, 'is_enabled': True}]
        }
        body = {'products': [product]}
    else:
        p = products[0]
        # Remove fields that cause errors
        for drop in ('product_id', 'is_deleted'):
            p.pop(drop, None)
        p['sku'] = sku
        offerings = p.get('offerings', [])
        for o in offerings:
            o.pop('offering_id', None)
            o.pop('is_deleted', None)
            # Keep readiness_state_id if present
            o['price'] = float(price)
            o['quantity'] = 999
            o['is_enabled'] = True
        if not offerings:
            p['offerings'] = [{'price': float(price), 'quantity': 999, 'is_enabled': True}]
        body = {'products': [p]}

    try:
        url_put = f'https://openapi.etsy.com/v3/application/listings/{listing_id}/inventory'
        payload = json.dumps(body).encode()
        req_put = urllib.request.Request(url_put, data=payload, headers={}, method='PUT')
        # Build headers manually
        req_put = client._build_request('PUT', url_put, body)
        with urllib.request.urlopen(req_put, timeout=15) as resp:
            result = json.loads(resp.read().decode())
        print(f'    SKU set: {sku}')
        return True
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f'    SKU PUT error {e.code}: {err_body[:200]}')
        return False
    except Exception as e:
        print(f'    SKU error: {e}')
        return False


# ── Main workflow ─────────────────────────────────────────────────────────────

def main():
    store = DataStore()
    client = EtsyAPIClient()

    results = {}

    print('\n' + '='*60)
    print('STEP 1: Approve products and generate listing drafts')
    print('='*60)

    products = store.get('digital_products', default=[])
    for p in products:
        if p['id'] in WALL_ART:
            p['status'] = 'approved'
            p['qc_status'] = 'approved'
            p['updated_at'] = str(date.today())
    store.set(products, 'digital_products')
    store.save()
    print('Products approved in data store')

    # Generate listing content for each
    for pid, info in WALL_ART.items():
        data = {
            'product_id': pid,
            'title': info['title'],
            'description': DESCRIPTIONS[pid],
            'tags': info['tags'],
            'price': info['price'],
            'quantity': 999,
            'section': 'Digital Downloads',
        }
        result_json = _generate_listing_content(data, store)
        result = json.loads(result_json)
        if result.get('success'):
            print(f'  {pid}: listing content generated OK')
        else:
            print(f'  {pid}: ERROR - {result}')
        results.setdefault(pid, {})['draft_ok'] = result.get('success', False)

    print('\n' + '='*60)
    print('STEP 2: Publish listings to Etsy')
    print('='*60)

    for pid in WALL_ART:
        pub_result_json = _publish_digital_listing({'product_id': pid, 'confirm': True}, store)
        pub = json.loads(pub_result_json)
        if pub.get('success'):
            listing_id = pub['etsy_listing_id']
            print(f'  {pid}: published -> Etsy ID {listing_id}')
            results[pid]['etsy_listing_id'] = listing_id
        else:
            print(f'  {pid}: PUBLISH ERROR -> {pub}')
            results[pid]['etsy_listing_id'] = None

    print('\n' + '='*60)
    print('STEP 3: Generate photos')
    print('='*60)

    for pid, info in WALL_ART.items():
        img_dir = os.path.join(PRODUCT_FILES_DIR, f'{pid}_listing_images')
        os.makedirs(img_dir, exist_ok=True)
        art_desc = info['art_description']
        frame_style = info['frame_style']

        photo_paths = []

        # Photo 1: original art file (no generation)
        orig = os.path.join(PRODUCT_FILES_DIR, f'{pid}.jpg')
        if os.path.exists(orig):
            photo_paths.append(orig)
            print(f'  {pid} Photo 1: using original {pid}.jpg')
        else:
            print(f'  {pid} Photo 1: MISSING {orig}')

        # Photo 2: frame mockup
        p2 = os.path.join(img_dir, f'{pid}_frame_mockup.jpg')
        if not os.path.exists(p2):
            prompt2 = (
                f'Professional interior photography, DSLR camera, 35mm lens, natural light from left window, '
                f'shallow depth of field, f/2.8 aperture. A fine art print mounted in a {frame_style}, '
                f'hanging on a smooth light cream plaster wall. The print shows {art_desc}. '
                f'The frame has thin clean lines, no ornate detail. Soft shadow behind frame. '
                f'Clean, minimal, elegant. Square format. No text anywhere.'
            )
            try:
                gen_image(prompt2, p2)
            except Exception as e:
                print(f'    {pid} Photo 2 FAILED: {e}')
                p2 = None
        else:
            print(f'  {pid} Photo 2: already exists')
        if p2 and os.path.exists(p2):
            photo_paths.append(p2)

        # Photo 3: living room lifestyle
        p3 = os.path.join(img_dir, f'{pid}_living_room.jpg')
        if not os.path.exists(p3):
            prompt3 = (
                f'Professional interior design photography, DSLR 35mm, f/2.8, natural window light. '
                f'Modern boho living room, linen sofa, rattan side table with a small ceramic vase of dried eucalyptus, '
                f'a lit pillar candle. On the wall above, a framed watercolor print showing {art_desc} '
                f'in a {frame_style}. The room feels calm, warm, inviting. Square format. No text anywhere in the image.'
            )
            try:
                gen_image(prompt3, p3)
            except Exception as e:
                print(f'    {pid} Photo 3 FAILED: {e}')
                p3 = None
        else:
            print(f'  {pid} Photo 3: already exists')
        if p3 and os.path.exists(p3):
            photo_paths.append(p3)

        # Photo 4: bedroom lifestyle
        p4 = os.path.join(img_dir, f'{pid}_bedroom.jpg')
        if not os.path.exists(p4):
            prompt4 = (
                f'Professional interior design photography, DSLR 35mm lens, soft morning light. '
                f'Minimalist bedroom with linen bedding in ivory and warm white, a small wooden nightstand '
                f'with a ceramic lamp and a small dried flower arrangement. On the wall, a framed botanical print '
                f'showing {art_desc} in a {frame_style}. Square format. No text anywhere in the image.'
            )
            try:
                gen_image(prompt4, p4)
            except Exception as e:
                print(f'    {pid} Photo 4 FAILED: {e}')
                p4 = None
        else:
            print(f'  {pid} Photo 4: already exists')
        if p4 and os.path.exists(p4):
            photo_paths.append(p4)

        # Photo 5: size guide (Pillow)
        p5 = os.path.join(img_dir, f'{pid}_size_guide.jpg')
        if not os.path.exists(p5):
            try:
                gen_size_guide(pid, p5)
            except Exception as e:
                print(f'    {pid} Photo 5 FAILED: {e}')
                p5 = None
        else:
            print(f'  {pid} Photo 5: already exists')
        if p5 and os.path.exists(p5):
            photo_paths.append(p5)

        results[pid]['photo_paths'] = photo_paths
        print(f'  {pid}: {len(photo_paths)} photos ready')

    print('\n' + '='*60)
    print('STEP 4: Upload photos to listings')
    print('='*60)

    for pid, info in WALL_ART.items():
        listing_id = results[pid].get('etsy_listing_id')
        if not listing_id:
            print(f'  {pid}: skipping upload — no listing ID')
            continue

        photo_paths = results[pid].get('photo_paths', [])
        uploaded = 0
        for rank, img_path in enumerate(photo_paths, start=1):
            if not os.path.exists(img_path):
                print(f'  {pid} rank {rank}: file missing {img_path}')
                continue
            try:
                client.upload_listing_image(listing_id, img_path, rank=rank)
                print(f'  {pid} rank {rank}: uploaded {os.path.basename(img_path)}')
                uploaded += 1
                time.sleep(0.5)  # gentle rate limiting
            except EtsyAPIError as e:
                print(f'  {pid} rank {rank}: UPLOAD ERROR {e}')
        results[pid]['photos_uploaded'] = uploaded

        # Upload digital file (the JPG) as a downloadable file
        art_file = os.path.join(PRODUCT_FILES_DIR, f'{pid}.jpg')
        if os.path.exists(art_file):
            try:
                client.upload_listing_file(listing_id, art_file, rank=1)
                print(f'  {pid}: digital file attached ({os.path.basename(art_file)})')
                results[pid]['file_attached'] = True
            except EtsyAPIError as e:
                print(f'  {pid}: file attach ERROR: {e}')
                results[pid]['file_attached'] = False

    print('\n' + '='*60)
    print('STEP 5: Activate listings and assign to Digital Downloads section')
    print('='*60)

    for pid in WALL_ART:
        listing_id = results[pid].get('etsy_listing_id')
        if not listing_id:
            print(f'  {pid}: skipping — no listing ID')
            continue
        try:
            client.update_listing(listing_id, {
                'state': 'active',
                'shop_section_id': DIGITAL_DOWNLOADS_SECTION_ID,
            })
            print(f'  {pid} ({listing_id}): activated, assigned to Digital Downloads')
            results[pid]['activated'] = True
        except EtsyAPIError as e:
            print(f'  {pid}: activate ERROR: {e}')
            results[pid]['activated'] = False

    print('\n' + '='*60)
    print('STEP 6: Set SKUs via inventory endpoint')
    print('='*60)

    for pid, sku in SKUS.items():
        listing_id = results[pid].get('etsy_listing_id')
        if not listing_id:
            print(f'  {pid}: skipping SKU — no listing ID')
            continue
        ok = update_listing_inventory_with_sku(client, listing_id, sku, WALL_ART[pid]['price'])
        results[pid]['sku'] = sku if ok else 'FAILED'

    print('\n' + '='*60)
    print('STEP 7: Generate 3D printed listing lifestyle photos')
    print('='*60)

    three_d_photos = {
        '4492610660': [
            {
                'out': os.path.join(PRODUCT_FILES_DIR, '4492610660_lifestyle_A.jpg'),
                'prompt': (
                    'Professional interior photography, DSLR 35mm, warm evening light. '
                    'On a rustic wooden side table: two small geometric 3D-printed matte white candle holders, '
                    'each holding a small lit tea light candle casting warm amber glow. '
                    'Background: dark cozy living room, blurred bookshelf. Square format. Photorealistic. No text.'
                ),
            },
            {
                'out': os.path.join(PRODUCT_FILES_DIR, '4492610660_lifestyle_B.jpg'),
                'prompt': (
                    'Professional interior photography, DSLR macro lens, shallow depth of field. '
                    'Overhead flat-lay on a light marble surface: two geometric white matte 3D-printed tea light '
                    'holders with unlit tea lights, surrounded by a few dried eucalyptus sprigs and a small smooth '
                    'river stone. Square format. Photorealistic. No text.'
                ),
            },
        ],
        '4497385915': [
            {
                'out': os.path.join(PRODUCT_FILES_DIR, '4497385915_lifestyle_A.jpg'),
                'prompt': (
                    'Professional interior photography, DSLR 35mm, natural daylight. Center of a round white dining table: '
                    'a geometric 3D-printed matte white decorative centerpiece object, surrounded by a few pillar candles '
                    'and a small vase of dried pampas grass. Bright airy Scandinavian dining room, white walls, wooden floor. '
                    'Square format. Photorealistic. No text.'
                ),
            },
            {
                'out': os.path.join(PRODUCT_FILES_DIR, '4497385915_lifestyle_B.jpg'),
                'prompt': (
                    'Professional interior photography, DSLR 35mm, golden hour window light. On a white fireplace mantel: '
                    'a geometric 3D-printed matte white decorative sculpture as centerpiece, flanked by two taper candles '
                    'in simple brass holders and a small dried flower arrangement. Square format. Photorealistic. No text.'
                ),
            },
        ],
    }

    three_d_results = {}
    for listing_id, photos in three_d_photos.items():
        three_d_results[listing_id] = {'uploaded': 0, 'errors': []}

        # Determine starting rank (after existing images)
        existing_counts = {'4492610660': 2, '4497385915': 3}
        next_rank = existing_counts.get(listing_id, 1) + 1

        for i, photo_info in enumerate(photos):
            out_path = photo_info['out']
            prompt = photo_info['prompt']
            label = 'A' if i == 0 else 'B'

            if not os.path.exists(out_path):
                try:
                    gen_image(prompt, out_path)
                except Exception as e:
                    print(f'  {listing_id} Photo {label} generation FAILED: {e}')
                    three_d_results[listing_id]['errors'].append(str(e))
                    next_rank += 1
                    continue
            else:
                print(f'  {listing_id} Photo {label}: already exists')

            if os.path.exists(out_path):
                try:
                    client.upload_listing_image(listing_id, out_path, rank=next_rank)
                    print(f'  {listing_id} Photo {label}: uploaded at rank {next_rank}')
                    three_d_results[listing_id]['uploaded'] += 1
                    next_rank += 1
                    time.sleep(0.5)
                except EtsyAPIError as e:
                    print(f'  {listing_id} Photo {label}: UPLOAD ERROR {e}')
                    three_d_results[listing_id]['errors'].append(str(e))
                    next_rank += 1

    print('\n' + '='*60)
    print('FINAL RESULTS')
    print('='*60)
    print(f'\n{"PID":<8} {"Etsy ID":<14} {"Photos":<10} {"SKU":<16} {"Status"}')
    print('-'*65)
    for pid in WALL_ART:
        r = results.get(pid, {})
        etsy_id = r.get('etsy_listing_id', 'N/A')
        photos = r.get('photos_uploaded', 0)
        sku = r.get('sku', 'N/A')
        activated = 'ACTIVE' if r.get('activated') else 'NOT ACTIVE'
        print(f'{pid:<8} {str(etsy_id):<14} {str(photos):<10} {sku:<16} {activated}')

    print(f'\n3D Listings:')
    for lid, r in three_d_results.items():
        print(f'  {lid}: {r["uploaded"]} photos uploaded, errors: {r["errors"]}')

    return results, three_d_results


if __name__ == '__main__':
    main()
