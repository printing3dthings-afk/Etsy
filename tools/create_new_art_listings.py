#!/usr/bin/env python3
"""
Create 8 new wall art listings covering distinct art categories,
create/organize shop sections, and update existing 15 listings into sections.
"""

import os, sys, json, base64, urllib.request, urllib.error, time
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

client = EtsyAPIClient()
client.refresh_access_token()
shop_id = client.shop_id
OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'
CANVAS = 2400

auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key": f"{client.client_id}:{client.client_secret}",
}

def refresh():
    if client.refresh_access_token():
        auth_headers["Authorization"] = f"Bearer {client.access_token}"
        print("  Token refreshed.")


# ── Image generation ──────────────────────────────────────────────────────────

def gen_image(prompt, out_path, size="1024x1536"):
    payload = json.dumps({
        "model": "gpt-image-1", "prompt": prompt, "n": 1,
        "size": size, "quality": "high", "output_format": "jpeg"
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
            return
        except Exception as e:
            if attempt < 2:
                print(f"  Retry {attempt+1}: {e}")
                time.sleep(15)
            else:
                raise


def composite(bg_path, art_path, out_path, fc, art_pct=0.33):
    """Composite art onto room background with realistic 3D frame."""
    room = Image.open(bg_path).convert('RGB').resize((CANVAS, CANVAS), Image.LANCZOS)
    art = Image.open(art_path).convert('RGB')
    art_w = int(CANVAS * art_pct)
    art_h = int(art_w * art.height / art.width)
    art = art.resize((art_w, art_h), Image.LANCZOS)
    mat_w, frame_w = 44, 20
    full_w = art_w + 2 * mat_w + 2 * frame_w
    full_h = art_h + 2 * mat_w + 2 * frame_w
    px = (CANVAS - full_w) // 2
    py = int(CANVAS * 0.13)
    print(f"  frame: {full_w}x{full_h}, bottom={py+full_h}px ({(py+full_h)/CANVAS*100:.1f}%)")

    ao = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    ao_draw = ImageDraw.Draw(ao)
    for pad in range(50, 0, -5):
        alpha = int(55 * (1 - (pad / 50) ** 1.5))
        ao_draw.rectangle([px-pad, py-pad, px+full_w+pad, py+full_h+pad], fill=(0,0,0,alpha))
    ao = ao.filter(ImageFilter.GaussianBlur(radius=28))
    room = Image.alpha_composite(room.convert('RGBA'), ao).convert('RGB')

    shadow = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle([px+10, py+14, px+full_w+10, py+full_h+14], fill=(0,0,0,65))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=16))
    room = Image.alpha_composite(room.convert('RGBA'), shadow).convert('RGB')

    draw = ImageDraw.Draw(room)
    draw.rectangle([px, py, px+full_w, py+full_h], fill=fc)
    fc_hi = tuple(min(255, c+50) for c in fc)
    fc_sh = tuple(max(0, c-50) for c in fc)
    bv = 4
    draw.polygon([px, py, px+full_w, py, px+full_w-bv, py+bv, px+bv, py+bv], fill=fc_hi)
    draw.polygon([px, py, px, py+full_h, px+bv, py+full_h-bv, px+bv, py+bv], fill=fc_hi)
    draw.polygon([px+full_w, py, px+full_w, py+full_h, px+full_w-bv, py+full_h-bv, px+full_w-bv, py+bv], fill=fc_sh)
    draw.polygon([px, py+full_h, px+full_w, py+full_h, px+full_w-bv, py+full_h-bv, px+bv, py+full_h-bv], fill=fc_sh)

    mx, my = px+frame_w, py+frame_w
    draw.rectangle([mx, my, mx+art_w+2*mat_w, my+art_h+2*mat_w], fill=(253, 251, 248))

    inner = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    art_x, art_y = mx+mat_w, my+mat_w
    ImageDraw.Draw(inner).rectangle([art_x-3, art_y-3, art_x+art_w+3, art_y+art_h+3], fill=(0,0,0,35))
    inner = inner.filter(ImageFilter.GaussianBlur(radius=7))
    room = Image.alpha_composite(room.convert('RGBA'), inner).convert('RGB')

    art_integrated = ImageEnhance.Brightness(art).enhance(0.93)
    room.paste(art_integrated, (art_x, art_y))
    room.save(out_path, 'JPEG', quality=93)
    print(f"  Composite: {os.path.basename(out_path)}")


# ── Etsy helpers ──────────────────────────────────────────────────────────────

def create_listing(listing_data):
    url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings"
    payload = json.dumps(listing_data).encode()
    req = urllib.request.Request(url, data=payload, headers={**auth_headers, "Content-Type": "application/json"}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if e.code == 401: refresh()
            elif e.code == 429: time.sleep(15)
            else:
                print(f"  CREATE {e.code}: {body}")
                if attempt == 2: return None
                time.sleep(3)
    return None

def update_listing(listing_id, updates):
    url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}"
    payload = json.dumps(updates).encode()
    req = urllib.request.Request(url, data=payload, headers={**auth_headers, "Content-Type": "application/json"}, method="PATCH")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            if e.code == 401: refresh()
            elif e.code == 429: time.sleep(15)
            elif e.code == 400:
                print(f"  UPDATE 400: {body}"); return None
            else:
                if attempt == 2: return None
                time.sleep(3)
    return None

def upload_image(listing_id, img_path, rank):
    for attempt in range(3):
        try:
            result = client.upload_listing_image(listing_id, img_path, rank=rank)
            print(f"  img rank={rank} id={result.get('listing_image_id')}")
            return True
        except EtsyAPIError as e:
            if e.status == 401: refresh()
            elif e.status == 429: time.sleep(15)
            elif e.status == 500 and attempt < 2: time.sleep(5)
            else: print(f"  img {rank}: {e}"); return False
    return False

def upload_file(listing_id, file_path, rank=1):
    for attempt in range(3):
        try:
            result = client.upload_listing_file(listing_id, file_path, rank=rank)
            print(f"  file rank={rank} id={result.get('listing_file_id')}")
            return True
        except EtsyAPIError as e:
            if e.status == 401: refresh()
            elif e.status == 429: time.sleep(15)
            else: print(f"  file upload {e.status}: {e}"); return False
    return False

def get_or_create_section(title):
    return client.get_or_create_section(title)


# ── Shop sections plan ────────────────────────────────────────────────────────

SECTION_NAMES = [
    "Botanical and Floral Art",
    "Abstract and Modern Art",
    "Landscape and Nature Art",
    "Celestial and Travel Art",
    "Quote & Inspiration Art",
    "Novelty and Pop Art",
]

# Existing 15 listings → correct sections
EXISTING_SECTION_MAP = {
    # Botanical & Floral
    '4509258700': "Botanical and Floral Art",   # DP1013 Watercolor Botanical
    '4509213667': "Botanical and Floral Art",   # DP1016 White Roses Oil
    '4509214237': "Botanical and Floral Art",   # DP1020 Poppy Field
    # Abstract & Modern
    '4509258172': "Abstract and Modern Art",    # DP1012 Bold Checkerboard
    '4509259354': "Abstract and Modern Art",    # DP1017 Botanical Line Art
    # Landscape & Nature
    '4509218152': "Landscape and Nature Art",   # DP1007 Mediterranean Window
    '4509218860': "Landscape and Nature Art",   # DP1018 Japandi
    '4509214051': "Landscape and Nature Art",   # DP1019 Mountain Meadow
    '4509219594': "Landscape and Nature Art",   # DP1022 Full Moon Ocean
    # Quote & Inspiration
    '4509213345': "Quote & Inspiration Art",  # DP1014 Good Things Take Time
    '4509213533': "Quote & Inspiration Art",  # DP1015 She Believed
    # Novelty & Pop Art
    '4509214477': "Novelty and Pop Art",        # DP1021 Dog at Bar
    '4509214803': "Novelty and Pop Art",        # DP1023 Astronaut
    '4509219904': "Novelty and Pop Art",        # DP1024 Chevelle
    '4509215145': "Novelty and Pop Art",        # DP1025 Day of Dead
}


# ── New listing definitions ───────────────────────────────────────────────────

def make_description(hook, perfect_for_bullets, printing_tips, subject_context):
    return f"""{hook}

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT YOU GET
━━━━━━━━━━━━━━━━━━━━━━━━
• Instant digital download — no waiting, no shipping
• High-resolution JPG file (300 DPI, ready to print)
• Multiple sizes included: 5×7, 8×10, 11×14, 16×20, 18×24, 24×36
• Print at home or send to a print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🏠 PERFECT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
{perfect_for_bullets}

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase and download your files instantly from Etsy
2. Print at home, at Costco, Staples, or your local print shop
3. Frame it and hang — that's it!

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 PRINTING TIPS
━━━━━━━━━━━━━━━━━━━━━━━━
{printing_tips}

━━━━━━━━━━━━━━━━━━━━━━━━
📄 FILE DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: High-resolution JPG
• Resolution: 300 DPI (print quality)
• Sizes: 5×7, 8×10, 11×14, 16×20, 18×24, 24×36 inches
• Color profile: sRGB

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this a physical item?
A: No — this is a digital download only. You receive image files to print yourself.

Q: Can I resize the files?
A: Yes! 300 DPI files scale beautifully to any size. Resize in Canva, Photoshop, or any image editor.

Q: Can I print multiple copies?
A: Yes — for personal use, print as many copies as you like in your own home.

Q: What paper should I use?
A: {subject_context}

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use."""


NEW_LISTINGS = {
    'DP1030': {
        'product_id': 'DP1030',
        'sku': 'OBC-WA-030',
        'title': 'Moon Phases Print | Celestial Wall Art | Lunar Cycle Astronomy Decor | Instant Download Printable | Gold Moon Art Print',
        'tags': [
            'moon phases print',
            'celestial wall art',
            'lunar cycle art',
            'moon wall decor',
            'astrology art',
            'printable wall art',
            'instant download',
            'digital download',
            'bedroom wall art',
            'boho wall decor',
            'gold moon print',
            'night sky art',
            'mystical wall art',
        ],
        'price': 5.99,
        'section': 'Celestial and Travel Art',
        'frame_color': (155, 125, 50),
        'art_prompt': (
            "Elegant celestial art print, portrait orientation. The eight phases of the moon beautifully arranged in two horizontal rows of four: new moon, waxing crescent, first quarter, waxing gibbous (top row), then full moon, waning gibbous, last quarter, waning crescent (bottom row). Each moon rendered in exquisite detail with soft atmospheric texture and a warm golden glow on deep midnight navy background. Fine elegant gold circles frame each moon. Below each: its name in a delicate thin elegant serif font in gold. Wide cream/ivory border margins. Sophisticated luxury art print aesthetic. High resolution, print quality. No other text."
        ),
        'art_size': '1024x1536',
        'rooms': [
            ('bg_lifestyle_room_A.jpg',
             "Etsy product mockup photography, square format. A moody bohemian bedroom. Bottom 40%: a dark upholstered bed headboard with layered charcoal and cream linen pillows, a sleek nightstand with a glowing diffuser and a small crystal cluster, dried pampas grass in a dark vase. Top 60%: smooth deep navy blue wall, completely bare and empty. Warm candlelight and amber lamp glow, mystical atmosphere. No art, no frames on the wall. Professional DSLR, photorealistic. High quality."),
            ('bg_lifestyle_room_B.jpg',
             "Etsy product mockup photography, square format. A chic dark boho living room corner. Bottom 40%: a deep indigo velvet sofa top with a crescent moon throw pillow, a small table with an amethyst crystal and a gold candlestick. Top 60%: smooth charcoal/slate wall, completely bare and empty. Moody warm amber ambient light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality."),
        ],
        'description': make_description(
            hook="Trace the magic of the lunar cycle — this exquisite moon phases print captures all eight phases of the moon in elegant gold detail, perfectly arranged and labeled, making it a dreamy statement piece for any celestial-inspired space. Whether you're an astrology lover, a night sky enthusiast, or simply drawn to the timeless beauty of the moon, this print speaks to you.",
            perfect_for_bullets="• Bedroom or master suite with celestial or boho styling\n• Astrology lover's home or sacred space\n• Meditation room, reading nook, or yoga space\n• Moody dark aesthetic or dark academia interiors\n• Meaningful birthday or graduation gift for moon lovers",
            printing_tips="• Matte paper deepens the dark midnight tones beautifully — avoid glossy for this design\n• Black or dark wood frame elevates the celestial aesthetic\n• 11×14 or 16×20 shows all the moon detail at its best\n• Print on deep matte paper at your local print shop for maximum drama",
            subject_context="Matte or satin paper is ideal — it brings out the dark navy blues and gold tones without glare.",
        ),
    },

    'DP1031': {
        'product_id': 'DP1031',
        'sku': 'OBC-WA-031',
        'title': 'Abstract Brushstroke Print | Blue Terracotta Modern Wall Art | Abstract Home Decor | Instant Download | Contemporary Art Print',
        'tags': [
            'abstract wall art',
            'brushstroke print',
            'modern art print',
            'abstract home decor',
            'contemporary art',
            'printable wall art',
            'instant download',
            'digital download',
            'living room art',
            'blue abstract art',
            'gallery wall art',
            'boho wall art',
            'terracotta art',
        ],
        'price': 5.99,
        'section': 'Abstract and Modern Art',
        'frame_color': (88, 62, 38),
        'art_prompt': (
            "Abstract expressionist art print, portrait orientation. Large, confident, gestural brushstrokes in a sophisticated palette: deep ocean blue, warm terracotta/burnt sienna, dusty sage green, and warm cream on a soft linen/off-white background. The brushstrokes are bold and decisive — some thick impasto, some sweeping and thin — creating a composition that feels alive, emotional, and gallery-worthy. No recognizable subject matter. Clean white border margins. Museum-quality contemporary abstract art. No text, no signature visible."
        ),
        'art_size': '1024x1536',
        'rooms': [
            ('bg_lifestyle_room_A.jpg',
             "Etsy product mockup photography, square format. A modern contemporary living room. Bottom 40%: a curved cream bouclé sofa with terracotta and sage green accent pillows, a slim brass side table with a sculptural vase. Top 60%: smooth warm white wall, completely bare and empty. Bright clean natural daylight. No art, no frames on the wall. Professional DSLR, photorealistic. High quality."),
            ('bg_lifestyle_room_B.jpg',
             "Etsy product mockup photography, square format. A stylish modern apartment living room. Bottom 40%: a low-profile slate blue linen sofa, a small oak coffee table with an art book and a white ceramic bowl. Top 60%: smooth warm greige wall, completely bare and empty. Clean bright natural light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality."),
        ],
        'description': make_description(
            hook="Bold. Emotional. Alive — this abstract expressionist print brings the energy of a high-end art gallery into your home. Rich ocean blue, warm terracotta, and dusty sage green brushstrokes on linen create a composition with movement, depth, and feeling that transforms any room from ordinary to extraordinary.",
            perfect_for_bullets="• Modern and contemporary living rooms\n• Gallery wall centerpiece or statement piece\n• Home office or studio with design-forward aesthetic\n• Bedroom or open-plan space that needs a focal point\n• Housewarming gift for design lovers",
            printing_tips="• Matte paper brings out the rich brushstroke texture — strongly recommended\n• For a true gallery feel, print on canvas or thick art paper at a local print shop\n• 16×20 or 24×36 is spectacular — the larger the better for abstract art\n• Natural wood or brushed brass frame complements the warm tones",
            subject_context="Matte paper or canvas paper is strongly recommended — it preserves the painterly texture of the brushstrokes.",
        ),
    },

    'DP1032': {
        'product_id': 'DP1032',
        'sku': 'OBC-WA-032',
        'title': 'Vintage Botanical Print | Antique Herbarium Wall Art | Latin Botanical Decor | Instant Download Printable | Cottagecore Art',
        'tags': [
            'vintage botanical',
            'herbarium print',
            'antique botanical',
            'botanical wall art',
            'cottagecore art',
            'printable wall art',
            'instant download',
            'digital download',
            'kitchen wall art',
            'science art print',
            'farmhouse wall art',
            'nature art print',
            'library wall art',
        ],
        'price': 5.99,
        'section': 'Botanical and Floral Art',
        'frame_color': (48, 32, 14),
        'art_prompt': (
            "Antique botanical herbarium plate illustration, portrait orientation. An exquisitely detailed 18th-century-style scientific botanical illustration featuring four plants on aged parchment/cream background: lavender (Lavandula angustifolia), rosemary (Rosmarinus officinalis), sage (Salvia officinalis), and wild chamomile (Matricaria chamomilla). Each plant is shown complete with roots, stems, leaves, flowers, and detailed cross-section insets. Handwritten-style Latin species names and annotations in elegant copperplate calligraphy. The parchment has subtle aged yellowing at the edges. Rich botanical illustration detail, ink and watercolor style. Wide cream border margins. Numbered illustrations. Museum-quality antique plate aesthetic."
        ),
        'art_size': '1024x1536',
        'rooms': [
            ('bg_lifestyle_room_A.jpg',
             "Etsy product mockup photography, square format. A cozy cottage library or study corner. Bottom 40%: an antique dark wood writing desk with an open leather-bound journal, a brass inkwell, a stack of old hardcover books, a small potted rosemary plant. Top 60%: smooth warm cream/ivory wall, completely bare and empty. Warm afternoon library light. No art, no frames on the wall. Professional DSLR, photorealistic. High quality."),
            ('bg_lifestyle_room_B.jpg',
             "Etsy product mockup photography, square format. A charming farmhouse kitchen corner. Bottom 40%: a white marble countertop with a small clay pot of fresh herbs, a handwritten recipe card, a linen tea towel, morning light across the counter. Top 60%: smooth warm white shiplap or plaster wall, completely bare and empty. Bright morning light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality."),
        ],
        'description': make_description(
            hook="From the pages of an 18th century naturalist's journal — this antique botanical herbarium print features exquisitely detailed scientific illustrations of lavender, rosemary, sage, and chamomile, complete with handwritten Latin annotations on aged parchment. Perfect for cottagecore homes, libraries, kitchens, and anyone who loves the beauty of old botanical art.",
            perfect_for_bullets="• Kitchen, dining room, or herb garden inspired decor\n• Home library, study, or reading room\n• Cottagecore, farmhouse, or vintage-inspired interiors\n• Science lover, botanist, or herbalist home\n• Thoughtful housewarming or botanical lover gift",
            printing_tips="• Matte or satin paper on a warm cream stock enhances the antique parchment feel\n• Dark wood or antique gold frame makes this look like a genuine botanical specimen plate\n• 8×10 or 11×14 framed looks exceptional on a kitchen or library wall\n• For a truly antique look: print on warm cream or natural parchment paper stock",
            subject_context="Cream or warm white matte paper is ideal — it enhances the aged parchment aesthetic perfectly.",
        ),
    },

    'DP1033': {
        'product_id': 'DP1033',
        'sku': 'OBC-WA-033',
        'title': 'Paris Skyline Print | Minimalist Eiffel Tower Line Art | City Wall Decor | Instant Download Printable | Travel Art Bedroom',
        'tags': [
            'paris print',
            'paris wall art',
            'city skyline print',
            'eiffel tower art',
            'travel wall art',
            'printable wall art',
            'instant download',
            'digital download',
            'line art print',
            'minimalist city',
            'paris bedroom art',
            'france wall decor',
            'wanderlust art',
        ],
        'price': 4.99,
        'section': 'Celestial and Travel Art',
        'frame_color': (28, 28, 28),
        'art_prompt': (
            "Minimalist Paris city skyline print, portrait orientation. An elegant single continuous flowing black ink line drawing traces the iconic Paris skyline: the Eiffel Tower, Notre-Dame Cathedral, the dome of Sacré-Cœur, the Arc de Triomphe, and graceful Seine river bridges, all connected in one beautiful unbroken line. The line is fluid, confident, and perfectly weighted — neither too thick nor too thin. Pure white background. Centered composition with generous white margins on all sides. Sophisticated, romantic, gallery-quality. No color fill, only the single black line. No text, no labels."
        ),
        'art_size': '1024x1536',
        'rooms': [
            ('bg_lifestyle_room_A.jpg',
             "Etsy product mockup photography, square format. A romantic Parisian-inspired bedroom. Bottom 40%: a white upholstered headboard with ivory and blush pillows, a marble bedside table with a small Eiffel Tower figurine, a single pink peony in a bud vase, warm morning light. Top 60%: smooth warm white wall, completely bare and empty. Soft romantic morning light. No art, no frames on the wall. Professional DSLR, photorealistic. High quality."),
            ('bg_lifestyle_room_B.jpg',
             "Etsy product mockup photography, square format. A chic modern apartment living room. Bottom 40%: a sleek cream sofa back, a small marble side table with a coffee table book on Paris, a white ceramic vase with white flowers. Top 60%: smooth light warm grey wall, completely bare and empty. Clean natural daylight. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality."),
        ],
        'description': make_description(
            hook="The city of light, distilled to a single elegant line — this minimalist Paris skyline traces the Eiffel Tower, Notre-Dame, Sacré-Cœur, and the Seine in one continuous flowing stroke, bringing the romance and beauty of Paris to your walls. Whether you've been to Paris or it's your dream destination, this print captures that je ne sais quoi perfectly.",
            perfect_for_bullets="• Bedroom with romantic or Parisian-inspired decor\n• Living room minimalist gallery wall\n• Travel lover's home or apartment\n• Feminine home office or study\n• Housewarming, graduation, or travel-themed gift",
            printing_tips="• Matte paper gives the cleanest, most elegant result for line art\n• Thin black frame or simple white frame is the perfect complement\n• 8×10 or 11×14 is perfect for bedroom walls; 16×20 makes a sophisticated statement\n• Print on bright white smooth cardstock for maximum line contrast",
            subject_context="Bright white matte paper gives the sharpest, most elegant results for line art prints.",
        ),
    },

    'DP1034': {
        'product_id': 'DP1034',
        'sku': 'OBC-WA-034',
        'title': 'Grand Canyon Print | Vintage National Park Poster Art | WPA Style Retro Wall Decor | Instant Download | Outdoor Nature Art',
        'tags': [
            'grand canyon print',
            'national park art',
            'vintage travel art',
            'retro poster print',
            'wpa poster art',
            'printable wall art',
            'instant download',
            'digital download',
            'nature wall art',
            'travel wall decor',
            'living room art',
            'outdoor lover art',
            'american west art',
        ],
        'price': 5.99,
        'section': 'Celestial and Travel Art',
        'frame_color': (55, 38, 18),
        'art_prompt': (
            "Vintage WPA travel poster style art print, portrait orientation. Grand Canyon National Park illustration in authentic 1930s-1940s Works Progress Administration national park poster style. Bold flat graphic illustration: dramatic layered canyon walls in deep terracotta, rust, and burnt orange; cobalt blue sky with stylized white clouds; pale cream rock highlights. Strong geometric horizontal banding of canyon strata. In the foreground: tiny silhouette of pine trees on the canyon rim. At top: 'GRAND CANYON' in bold vintage block capitals. At bottom: 'NATIONAL PARK' and 'ARIZONA' in smaller vintage type. The overall palette is terracotta, cobalt, cream, and deep brown. Authentic retro government poster aesthetic. No photographic elements — purely graphic illustration."
        ),
        'art_size': '1024x1536',
        'rooms': [
            ('bg_lifestyle_room_A.jpg',
             "Etsy product mockup photography, square format. A cozy rustic living room corner. Bottom 40%: a distressed leather sofa arm, a reclaimed wood side table with a small succulent in a terracotta pot, a hiking trail map and a well-worn novel, warm natural light. Top 60%: smooth warm white wall, completely bare and empty. Warm golden afternoon light. No art, no frames on the wall. Professional DSLR, photorealistic. High quality."),
            ('bg_lifestyle_room_B.jpg',
             "Etsy product mockup photography, square format. A modern mountain cabin hallway. Bottom 40%: a slim natural wood bench with hiking boots neatly placed beside it, a small woven basket with a rolled blanket, terracotta floor tiles. Top 60%: smooth warm plaster wall, completely bare and empty. Warm afternoon light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality."),
        ],
        'description': make_description(
            hook="Adventure lives on your wall — this vintage-inspired WPA travel poster captures the magnificent Grand Canyon in bold terracotta, cobalt, and cream, celebrating America's most breathtaking landscape in timeless 1930s poster art style. For hikers, road trippers, national park lovers, and anyone who dreams of standing on that canyon rim.",
            perfect_for_bullets="• Living room with rustic, western, or nature-inspired decor\n• Entryway, hallway, or mudroom of an outdoor-lover's home\n• Cabin, lodge, or mountain house\n• Office or workspace of adventure enthusiasts\n• Birthday, graduation, or travel-themed gift",
            printing_tips="• Matte paper is ideal — it gives authentic poster-print texture\n• Dark wood or raw wood frame adds to the rustic vintage feel\n• 11×14 or 16×20 captures all the poster detail beautifully\n• For the most authentic vintage look: print on warm cream matte paper stock",
            subject_context="Matte paper on warm cream or natural white stock gives the most authentic vintage poster appearance.",
        ),
    },

    'DP1035': {
        'product_id': 'DP1035',
        'sku': 'OBC-WA-035',
        'title': 'Tropical Leaves Print | Bold Monstera Palm Wall Art | Botanical Jungle Decor | Instant Download Printable | Modern Boho Art',
        'tags': [
            'tropical wall art',
            'monstera print',
            'tropical leaves',
            'botanical wall art',
            'palm leaf print',
            'printable wall art',
            'instant download',
            'digital download',
            'boho wall art',
            'living room art',
            'bold leaf art',
            'modern home decor',
            'jungle wall art',
        ],
        'price': 5.99,
        'section': 'Abstract and Modern Art',
        'frame_color': (35, 72, 45),
        'art_prompt': (
            "Bold modern tropical botanical art print, portrait orientation. Large-scale tropical leaf composition: a dramatic monstera deliciosa leaf, palm fronds, and a bird of paradise leaf filling the entire composition, rendered in rich bold jewel tones — deep emerald green, rich cobalt blue, warm terracotta, golden yellow, and deep hunter green. The style is flat graphic with simplified organic shapes and strong color — inspired by Matisse and Henri Rousseau. Cream/off-white background. The leaves have strong graphic silhouettes with simplified but expressive veining. No text. Clean white border margins. Modern gallery-quality botanical art."
        ),
        'art_size': '1024x1536',
        'rooms': [
            ('bg_lifestyle_room_A.jpg',
             "Etsy product mockup photography, square format. A lush modern boho living room. Bottom 40%: a natural rattan sofa with emerald green cushions, a large monstera plant in a woven basket pot on the left, a small wooden side table with a carved ceramic bowl. Top 60%: smooth warm white wall, completely bare and empty. Bright warm natural light. No art, no frames on the wall. Professional DSLR, photorealistic. High quality."),
            ('bg_lifestyle_room_B.jpg',
             "Etsy product mockup photography, square format. A vibrant modern dining room. Bottom 40%: a natural oak dining table with woven rattan placemats, a terracotta ceramic vase of tropical leaves, a woven jute runner. Top 60%: smooth warm cream wall, completely bare and empty. Bright warm natural light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality."),
        ],
        'description': make_description(
            hook="Lush, bold, and alive — this Matisse-inspired tropical leaves print brings the drama of a jungle into your living room. Monstera, palm, and bird of paradise leaves rendered in rich emerald, cobalt, and terracotta create a statement piece with real presence. If your walls need life, this is the print.",
            perfect_for_bullets="• Modern boho living room or dining room\n• Tropical or jungle-themed interiors\n• Bright contemporary spaces that need a statement piece\n• Gallery wall anchor or standalone large-format art\n• Plant lover or biophilia-inspired home decor",
            printing_tips="• Glossy or satin paper makes the jewel-tone greens and cobalts absolutely pop\n• Natural wood frame or bamboo frame looks perfect with this tropical subject\n• 16×20 or 24×36 is breathtaking — go as large as your wall allows\n• Print on canvas for a true gallery piece with depth and texture",
            subject_context="Glossy or satin paper enhances the rich saturated greens and jewel tones — highly recommended for this design.",
        ),
    },

    'DP1036': {
        'product_id': 'DP1036',
        'sku': 'OBC-WA-036',
        'title': 'Abstract Woman Portrait Print | Feminist Line Art Wall Decor | Botanical Face Art | Instant Download | Minimal Art Print',
        'tags': [
            'abstract portrait',
            'woman line art',
            'female face print',
            'feminist wall art',
            'line art portrait',
            'printable wall art',
            'instant download',
            'digital download',
            'bedroom wall art',
            'minimal art print',
            'botanical face art',
            'modern line art',
            'women gift art',
        ],
        'price': 5.99,
        'section': 'Abstract and Modern Art',
        'frame_color': (28, 28, 28),
        'art_prompt': (
            "Elegant minimalist abstract female portrait line art, portrait orientation. A single continuous flowing black ink line traces a woman's profile and face — elegant features, flowing hair, graceful neck — with delicate botanical elements woven through: small roses, leaves, tiny wildflowers, and a vine trailing from her hair. The line art is fluid and confident, with beautiful variation in weight — bold in some areas, delicate in others. Picasso-inspired abstract portraiture combined with romantic botanical illustration. Pure white background. The composition is centered and balanced. Clean generous white margins on all sides. Print-ready, high resolution. No color. No text."
        ),
        'art_size': '1024x1536',
        'rooms': [
            ('bg_lifestyle_room_A.jpg',
             "Etsy product mockup photography, square format. A beautiful minimalist feminine bedroom. Bottom 40%: a white linen headboard with ivory pillows and a blush silk accent pillow, a slim white bedside table with a small vase of white anemones and a gold ring dish. Top 60%: smooth pure white wall, completely bare and empty. Soft clean morning light. No art, no frames on the wall. Professional DSLR, photorealistic. High quality."),
            ('bg_lifestyle_room_B.jpg',
             "Etsy product mockup photography, square format. A sophisticated feminine dressing room corner. Bottom 40%: a white marble vanity top with a gold mirror base visible, a small vase of white tulips, a pearl bracelet on a jewelry tray. Top 60%: smooth warm off-white wall, completely bare and empty. Soft natural morning light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality."),
        ],
        'description': make_description(
            hook="Beautiful, effortless, and deeply elegant — this abstract female portrait weaves a woman's profile with flowing botanical elements in a single continuous line, creating a sophisticated artwork that speaks to modern femininity. It's the kind of art that makes guests stop and look, then look again.",
            perfect_for_bullets="• Bedroom, dressing room, or feminine personal space\n• Minimalist or modern Scandinavian interiors\n• Home office or studio with sophisticated aesthetic\n• Birthday, Mother's Day, or empowerment gift for women\n• Gallery wall feminine anchor piece",
            printing_tips="• Bright white matte paper gives the sharpest line contrast — strongly recommended\n• Thin black or gold frame is the ideal pairing\n• 8×10 or 11×14 is beautiful on a bedside wall; 16×20 as a bedroom statement piece\n• Print on premium smooth white cardstock for the crispest line art results",
            subject_context="Bright white matte paper or smooth cardstock gives the crispest, most elegant results for line art.",
        ),
    },

    'DP1037': {
        'product_id': 'DP1037',
        'sku': 'OBC-WA-037',
        'title': 'Italian Kitchen Print | Olive Oil Pasta Wall Art | Foodie Kitchen Decor | Instant Download Printable | Rustic Food Art',
        'tags': [
            'kitchen wall art',
            'italian food art',
            'olive oil print',
            'pasta wall decor',
            'foodie kitchen art',
            'printable wall art',
            'instant download',
            'digital download',
            'dining room art',
            'rustic kitchen art',
            'food illustration',
            'farmhouse kitchen',
            'cooking gift art',
        ],
        'price': 4.99,
        'section': 'Botanical and Floral Art',
        'frame_color': (88, 62, 38),
        'art_prompt': (
            "Charming Italian kitchen illustration art print, portrait orientation. A joyful composition of Italian culinary ingredients illustrated in warm watercolor with ink outlines: a beautiful olive oil bottle with Italian label, a rustic bunch of ripe tomatoes on the vine, fresh fragrant basil with roots visible, whole garlic bulbs with papery skin, a wooden cutting board, dried spaghetti bundled with twine, a glass of deep red wine with a little splashing, and a sprig of fresh rosemary. The overall palette is warm and rich: golden olive oil tones, deep tomato red, lush basil green, warm wood brown. Illustrated in a charming folk art meets modern illustration style — slightly loose, full of personality and warmth. Generous cream margins. No English text on the art itself."
        ),
        'art_size': '1024x1536',
        'rooms': [
            ('bg_lifestyle_room_A.jpg',
             "Etsy product mockup photography, square format. A bright cheerful Italian-style kitchen. Bottom 40%: a warm terracotta tiled countertop with fresh tomatoes in a ceramic bowl, a bottle of olive oil, a bunch of fresh basil, warm sunlight across the tiles. Top 60%: smooth warm cream/white plaster wall, completely bare and empty. Bright warm Mediterranean-style light. No art, no frames on the wall. Professional DSLR, photorealistic. High quality."),
            ('bg_lifestyle_room_B.jpg',
             "Etsy product mockup photography, square format. A cozy farmhouse dining room. Bottom 40%: a rustic oak dining table with a linen table runner, a small ceramic pitcher of wildflowers, a candle in a terracotta holder, a wine glass. Top 60%: smooth warm white wall, completely bare and empty. Warm afternoon light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality."),
        ],
        'description': make_description(
            hook="La dolce vita on your kitchen wall — this charming Italian kitchen illustration captures the warmth and abundance of olive oil, fresh pasta, ripe tomatoes, fragrant basil, and a glass of red wine in a joyful watercolor painting that brings Italian soul into your home. Perfect for food lovers, home cooks, and anyone who believes the kitchen is the heart of the house.",
            perfect_for_bullets="• Kitchen wall art and dining room decor\n• Italian food lover or home chef's kitchen\n• Farmhouse, rustic, or Mediterranean-inspired interiors\n• Housewarming gift for food and cooking enthusiasts\n• Airbnb or vacation rental kitchen decor",
            printing_tips="• Matte or satin paper brings out the warm watercolor illustration colors beautifully\n• Natural wood frame complements the rustic Italian kitchen aesthetic\n• 8×10 is perfect for most kitchen walls; 11×14 for a statement above a counter\n• Print at a local photo lab for warm, food-photography-quality color reproduction",
            subject_context="Matte or satin paper on warm white stock gives the warmest, most food-magazine-quality results.",
        ),
    },
}


# ── Main execution ────────────────────────────────────────────────────────────

def run_full():
    refresh()
    results = {}

    # ── Step 1: Create/get all sections ───────────────────────────────────────
    print("\n" + "="*60)
    print("STEP 1: Setting up shop sections")
    print("="*60)
    section_ids = {}
    for name in SECTION_NAMES:
        sid = get_or_create_section(name)
        section_ids[name] = sid
        print(f"  Section '{name}': ID={sid}")

    # ── Step 2: Re-section existing 15 listings ────────────────────────────────
    print("\n" + "="*60)
    print("STEP 2: Moving existing 15 listings to correct sections")
    print("="*60)
    for listing_id, section_name in EXISTING_SECTION_MAP.items():
        sid = section_ids[section_name]
        result = update_listing(listing_id, {"shop_section_id": sid})
        if result:
            print(f"  {listing_id} → '{section_name}' (ID={sid})")
        else:
            print(f"  FAILED: {listing_id}")
        time.sleep(0.3)

    # ── Step 3: Create 8 new listings ─────────────────────────────────────────
    print("\n" + "="*60)
    print("STEP 3: Creating 8 new art listings")
    print("="*60)

    for pid, info in NEW_LISTINGS.items():
        print(f"\n{'─'*55}")
        print(f"{pid}: {info['title'][:70]}...")
        results[pid] = {'generated': False, 'listing_id': None, 'images': 0, 'file': False, 'active': False, 'errors': []}

        out_dir = os.path.join(ART_DIR, f"{pid}_listing_images")
        os.makedirs(out_dir, exist_ok=True)
        art_path = os.path.join(ART_DIR, f"{pid}.jpg")

        # ── 3a. Generate art ──────────────────────────────────────────────────
        if not os.path.exists(art_path):
            print(f"  Generating art for {pid}...")
            try:
                gen_image(info['art_prompt'], art_path, size=info['art_size'])
                results[pid]['generated'] = True
            except Exception as e:
                print(f"  ERROR generating art: {e}")
                results[pid]['errors'].append(f'art gen: {e}')
                continue
            time.sleep(3)
        else:
            print(f"  Art exists: {art_path}")
            results[pid]['generated'] = True

        # ── 3b. Generate lifestyle room backgrounds + composite ───────────────
        for filename, room_prompt in info['rooms']:
            bg_path = os.path.join(out_dir, filename)
            comp_path = os.path.join(out_dir, filename.replace('bg_', ''))

            if not os.path.exists(bg_path):
                print(f"  Generating room bg: {filename}...")
                try:
                    gen_image(room_prompt, bg_path, size="1024x1024")
                    time.sleep(2)
                except Exception as e:
                    print(f"  ERROR room bg: {e}")
                    results[pid]['errors'].append(f'{filename}: {e}')
                    continue

            print(f"  Compositing: {filename.replace('bg_', '')}...")
            composite(bg_path, art_path, comp_path, info['frame_color'])

        # ── 3c. Create Etsy listing (draft) ──────────────────────────────────
        refresh()
        section_id = section_ids.get(info['section'])
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

        print(f"  Creating listing...")
        listing = create_listing(listing_body)
        if not listing or not listing.get('listing_id'):
            print(f"  FAILED to create listing")
            results[pid]['errors'].append('create listing failed')
            continue

        lid = listing['listing_id']
        results[pid]['listing_id'] = lid
        print(f"  Created listing_id={lid}")
        time.sleep(1)

        # ── 3d. Upload images ─────────────────────────────────────────────────
        # rank 1 = cover (lifestyle A), rank 2 = lifestyle B, rank 3 = raw art
        img_uploads = [
            (os.path.join(out_dir, 'lifestyle_room_A.jpg'), 1),
            (os.path.join(out_dir, 'lifestyle_room_B.jpg'), 2),
            (art_path, 3),
        ]
        for img_path, rank in img_uploads:
            if os.path.exists(img_path):
                if upload_image(lid, img_path, rank):
                    results[pid]['images'] += 1
                time.sleep(0.8)

        # ── 3e. Upload digital download file ─────────────────────────────────
        if os.path.exists(art_path):
            print(f"  Uploading digital download file...")
            if upload_file(lid, art_path, rank=1):
                results[pid]['file'] = True
            time.sleep(1)

        # ── 3f. Activate listing ──────────────────────────────────────────────
        print(f"  Activating listing...")
        activated = update_listing(lid, {"state": "active"})
        if activated and activated.get('state') == 'active':
            results[pid]['active'] = True
            print(f"  LIVE: https://www.etsy.com/listing/{lid}/")
        else:
            print(f"  WARNING: could not activate — check Etsy dashboard")
        time.sleep(1.5)

    # ── Final summary ─────────────────────────────────────────────────────────
    print("\n\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    for pid, r in results.items():
        status = "✓ LIVE" if r['active'] else ("DRAFT" if r['listing_id'] else "FAILED")
        print(f"{status} {pid}: listing={r['listing_id']} imgs={r['images']} file={r['file']} errors={r['errors'] or 'none'}")

    print("\nSection IDs created:")
    for name, sid in section_ids.items():
        print(f"  {sid}: {name}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true', help='Execute the full run')
    parser.add_argument('--sections-only', action='store_true', help='Only create sections and re-section existing listings')
    args = parser.parse_args()

    if args.sections_only:
        refresh()
        print("Creating/getting sections...")
        section_ids = {}
        for name in SECTION_NAMES:
            sid = get_or_create_section(name)
            section_ids[name] = sid
            print(f"  '{name}': ID={sid}")
        print("\nMoving existing listings to sections...")
        for listing_id, section_name in EXISTING_SECTION_MAP.items():
            sid = section_ids[section_name]
            result = update_listing(listing_id, {"shop_section_id": sid})
            print(f"  {listing_id} → '{section_name}': {'OK' if result else 'FAIL'}")
            time.sleep(0.3)
    elif args.run:
        run_full()
    else:
        print("Use --run to create all new listings, or --sections-only to just organize sections.")
        print("\nNew listings to be created:")
        for pid, info in NEW_LISTINGS.items():
            print(f"  {pid}: {info['title'][:80]}")
            print(f"    Section: {info['section']} | Price: ${info['price']}")
