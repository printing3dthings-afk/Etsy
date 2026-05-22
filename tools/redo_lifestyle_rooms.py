#!/usr/bin/env python3
"""Redo lifestyle room background images for 15 wall art Etsy listings."""

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


def gen_room_bg(prompt, out_path):
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
            with open(out_path, "wb") as f: f.write(img_bytes)
            print(f"  Room bg: {os.path.basename(out_path)} ({len(img_bytes)//1024}KB)")
            return
        except Exception as e:
            if attempt < 2:
                print(f"  Retry {attempt+1} after error: {e}")
                time.sleep(15)
            else:
                raise


def composite(bg_path, art_path, out_path, fc, art_pct=0.33):
    """Composite art onto room background with realistic frame, shadow and lighting."""
    room = Image.open(bg_path).convert('RGB').resize((CANVAS, CANVAS), Image.LANCZOS)
    art = Image.open(art_path).convert('RGB')

    # Art size: 33% of canvas width for a substantial, gallery-worthy look
    art_w = int(CANVAS * art_pct)
    art_h = int(art_w * art.height / art.width)
    art = art.resize((art_w, art_h), Image.LANCZOS)

    # Generous mat + substantial frame for a real gallery frame look
    mat_w = 44
    frame_w = 20
    full_w = art_w + 2 * mat_w + 2 * frame_w
    full_h = art_h + 2 * mat_w + 2 * frame_w

    # Centered horizontally; vertically ~13% from top (upper wall area)
    px = (CANVAS - full_w) // 2
    py = int(CANVAS * 0.13)
    frame_bottom_pct = (py + full_h) / CANVAS * 100
    print(f"  frame: {full_w}x{full_h}, top={py}px, bottom={py+full_h}px ({frame_bottom_pct:.1f}%)")

    # ── 1. Ambient occlusion shadow (soft glow behind all 4 edges) ────────────
    ao = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    ao_draw = ImageDraw.Draw(ao)
    for pad in range(50, 0, -5):
        alpha = int(55 * (1 - (pad / 50) ** 1.5))
        ao_draw.rectangle(
            [px - pad, py - pad, px + full_w + pad, py + full_h + pad],
            fill=(0, 0, 0, alpha)
        )
    ao = ao.filter(ImageFilter.GaussianBlur(radius=28))
    room = Image.alpha_composite(room.convert('RGBA'), ao).convert('RGB')

    # ── 2. Directional drop shadow (light from upper-left) ───────────────────
    shadow = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle(
        [px + 10, py + 14, px + full_w + 10, py + full_h + 14],
        fill=(0, 0, 0, 65)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=16))
    room = Image.alpha_composite(room.convert('RGBA'), shadow).convert('RGB')

    draw = ImageDraw.Draw(room)

    # ── 3. Frame with 3D bevel ────────────────────────────────────────────────
    draw.rectangle([px, py, px + full_w, py + full_h], fill=fc)
    # Lighter top/left edges (highlight), darker bottom/right (shadow) for depth
    fc_hi = tuple(min(255, c + 50) for c in fc)
    fc_sh = tuple(max(0, c - 50) for c in fc)
    bv = 4  # bevel width
    draw.polygon([px, py, px + full_w, py, px + full_w - bv, py + bv, px + bv, py + bv], fill=fc_hi)
    draw.polygon([px, py, px, py + full_h, px + bv, py + full_h - bv, px + bv, py + bv], fill=fc_hi)
    draw.polygon([px + full_w, py, px + full_w, py + full_h, px + full_w - bv, py + full_h - bv, px + full_w - bv, py + bv], fill=fc_sh)
    draw.polygon([px, py + full_h, px + full_w, py + full_h, px + full_w - bv, py + full_h - bv, px + bv, py + full_h - bv], fill=fc_sh)

    # ── 4. Mat (slightly warm white to integrate with room ambient) ───────────
    mx, my = px + frame_w, py + frame_w
    draw.rectangle([mx, my, mx + art_w + 2 * mat_w, my + art_h + 2 * mat_w], fill=(253, 251, 248))

    # ── 5. Subtle inner shadow on mat (art appears recessed) ─────────────────
    inner = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    art_x, art_y = mx + mat_w, my + mat_w
    ImageDraw.Draw(inner).rectangle(
        [art_x - 3, art_y - 3, art_x + art_w + 3, art_y + art_h + 3],
        fill=(0, 0, 0, 35)
    )
    inner = inner.filter(ImageFilter.GaussianBlur(radius=7))
    room = Image.alpha_composite(room.convert('RGBA'), inner).convert('RGB')

    # ── 6. Slightly darken art to integrate with room (not pure-white-bright) ─
    art_integrated = ImageEnhance.Brightness(art).enhance(0.93)

    # ── 7. Paste art ──────────────────────────────────────────────────────────
    room.paste(art_integrated, (art_x, art_y))

    room.save(out_path, 'JPEG', quality=93)
    print(f"  Composite saved: {os.path.basename(out_path)}")


def get_rank_ids(listing_id, ranks=(6, 7)):
    url = f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images"
    req = urllib.request.Request(url, headers=auth_headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return {img['rank']: img['listing_image_id'] for img in data.get('results', []) if img.get('rank') in ranks}
    except Exception as e:
        print(f"  WARNING get_rank_ids: {e}")
        return {}

def delete_image(listing_id, image_id):
    url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/images/{image_id}"
    req = urllib.request.Request(url, headers=auth_headers, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=30): return True
    except urllib.error.HTTPError as e:
        print(f"  DELETE {image_id}: {e.code}"); return False

def upload(listing_id, img_path, rank):
    for attempt in range(3):
        try:
            result = client.upload_listing_image(listing_id, img_path, rank=rank)
            print(f"  rank {rank} id={result.get('listing_image_id')}")
            return True
        except EtsyAPIError as e:
            if e.status == 401: refresh()
            elif e.status == 429: time.sleep(15)
            elif e.status == 500 and attempt < 2: time.sleep(5)
            else: print(f"  rank {rank}: {e}"); return False
    return False


# ── Listing definitions ───────────────────────────────────────────────────────
# Prompt template principle:
#   - "Etsy product mockup photography" sets the photorealism expectation
#   - Bottom 40-45% describes styled room furniture/props (like the reference images)
#   - Top 55-60% specifies a clean empty wall where art will be composited
#   - Specific room type matches the art subject
#   - "No wall art, no frames, no paintings on the wall" prevents hallucinated art

LISTINGS = {
    'DP1007': {
        'listing_id': '4509218152',
        'art_file': f'{ART_DIR}/DP1007.jpg',
        'out_dir': f'{ART_DIR}/DP1007_listing_images',
        'frame_color': (65, 40, 18),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A styled Mediterranean-inspired dining nook. Bottom 40% of the image: rustic dark wood farm table surface with a ceramic bowl of lemons, a small olive oil bottle, linen napkins, warm golden sunlight streaming across the table. Left edge: a sheer linen curtain softly blowing. Top 60% of the image: smooth warm ivory plaster wall, completely bare and empty, with soft golden Mediterranean afternoon light falling on it. No art, no decor, no frames on the wall. Professional DSLR 50mm lens, sharp, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A bright coastal kitchen corner. Bottom 40% of the image: white marble countertop with a bowl of fresh lemons, a small terracotta pot with herbs, a linen tea towel draped casually, warm natural light across the counter. Top 60% of the image: smooth white plaster wall with subtle warm texture, completely bare and empty. No art, no frames, no decor on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1012': {
        'listing_id': '4509258172',
        'art_file': f'{ART_DIR}/DP1012.jpg',
        'out_dir': f'{ART_DIR}/DP1012_listing_images',
        'frame_color': (28, 28, 28),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A trendy maximalist living room corner. Bottom 40% of the image: top of a curved mustard velvet sofa with a bold geometric throw pillow, a slim rattan side table holding an abstract ceramic vase and a small potted succulent. Top 60% of the image: smooth dusty rose pink painted wall, completely bare and empty. Warm bright natural light from the left. No art, no frames, no decor on the wall. Professional DSLR, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A stylish eclectic studio corner. Bottom 40%: a lime green designer chair, a small pink round table with an open sketchbook, a tall monstera plant on the right edge. Top 60%: smooth warm white wall, completely bare and empty. Bright modern natural daylight. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1013': {
        'listing_id': '4509258700',
        'art_file': f'{ART_DIR}/DP1013.jpg',
        'out_dir': f'{ART_DIR}/DP1013_listing_images',
        'frame_color': (200, 190, 175),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A soft dreamy nursery. Bottom 40% of the image: white slatted wooden crib top rail with a soft white knit blanket draped over it, a small bunny plush toy on the mattress, a pampas grass arrangement in a small ceramic vase beside it. Top 60% of the image: smooth pale sage green nursery wall, completely bare and empty. Gentle soft diffused morning light. No art, no frames on the wall. Professional DSLR, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A serene feminine bedroom corner. Bottom 40%: top of a white upholstered linen headboard with layered white and blush pillows, a small bedside table with a small vase of pink flowers and a ceramic mug. Top 60%: smooth pale blush cream bedroom wall, completely bare and empty. Soft diffused morning light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1014': {
        'listing_id': '4509213345',
        'art_file': f'{ART_DIR}/DP1014.jpg',
        'out_dir': f'{ART_DIR}/DP1014_listing_images',
        'frame_color': (28, 28, 28),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A clean minimal home office corner. Bottom 40%: light oak desk surface with a ceramic white mug, a closed notebook, a small succulent in a white pot, soft natural light across the desk. Top 60%: smooth pure white wall, completely bare and empty. Bright clean natural daylight. No art, no frames on the wall. Professional DSLR 50mm, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A cozy reading nook corner. Bottom 40%: top of a cream linen sofa cushion back, a small stacked pile of books with spines showing, a folded woven throw blanket, warm table lamp glowing from the right edge. Top 60%: smooth warm cream white wall, completely bare and empty. Warm cozy ambient light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1015': {
        'listing_id': '4509213533',
        'art_file': f'{ART_DIR}/DP1015.jpg',
        'out_dir': f'{ART_DIR}/DP1015_listing_images',
        'frame_color': (168, 138, 78),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A sophisticated feminine bedroom. Bottom 40%: luxurious white linen headboard with ivory and champagne gold accent pillows, a sleek bedside table with a warm glowing gold table lamp and small white orchid in a bud vase. Top 60%: smooth dark charcoal accent wall, completely bare and empty. Warm moody golden lamp light from the right, dramatic and elegant. No art, no frames on the wall. Professional DSLR, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A chic feminine home office. Bottom 40%: white lacquered desk with a rose gold laptop, a coffee mug, a small vase of blush peonies. Top 60%: smooth warm blush pink wall, completely bare and empty. Bright clean natural daylight. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1016': {
        'listing_id': '4509213667',
        'art_file': f'{ART_DIR}/DP1016.jpg',
        'out_dir': f'{ART_DIR}/DP1016_listing_images',
        'frame_color': (78, 56, 36),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A romantic English cottage bedroom. Bottom 40%: white floral duvet with a lace-edged pillow, a small painted bedside table with a vase of fresh white roses and a vintage perfume bottle, soft morning light falling across the bed. Top 60%: smooth warm ivory cream wall, completely bare and empty. Soft romantic morning golden light. No art, no frames on the wall. Professional DSLR, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A cottagecore farmhouse dining room. Bottom 40%: an aged oak dining table with a white linen runner, a ceramic pitcher holding a small bunch of white roses, a flickering pillar candle, afternoon light across the table. Top 60%: smooth warm greige plaster wall, completely bare and empty. Warm afternoon light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1017': {
        'listing_id': '4509259354',
        'art_file': f'{ART_DIR}/DP1017.jpg',
        'out_dir': f'{ART_DIR}/DP1017_listing_images',
        'frame_color': (28, 28, 28),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A pure Scandinavian minimalist living room. Bottom 40%: a low-profile slate grey linen sofa back, a slim round white marble side table with a single small green plant in a white pot, a small stack of design books. Top 60%: smooth bright white wall, completely bare and empty. Clean bright northern daylight. No art, no frames on the wall. Professional DSLR 50mm, photorealistic interior photography. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A serene spa-like bathroom. Bottom 40%: a white freestanding bathtub lip, a folded white waffle towel over the edge, a small wooden tray with a single candle and eucalyptus sprig, soft light. Top 60%: smooth warm white wall with subtle texture, completely bare and empty. Soft diffused natural light. No art, no frames on the wall. Professional DSLR, photorealistic. High quality.'),
        ]
    },
    'DP1018': {
        'listing_id': '4509218860',
        'art_file': f'{ART_DIR}/DP1018.jpg',
        'out_dir': f'{ART_DIR}/DP1018_listing_images',
        'frame_color': (128, 98, 62),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A premium Japandi living room interior, styled like a high-end interior design magazine photo. Bottom 40%: a low natural light oak console bench with a neatly folded beige linen throw, a small ceramic bonsai pot, and a slim washi paper floor lamp glowing softly on the right edge. Top 60%: smooth warm greige plaster wall, completely bare and empty. Soft diffused natural light from the left. No art, no frames on the wall. Professional DSLR 50mm, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A serene Japandi meditation corner. Bottom 40%: a low natural rattan floor cushion, a small wooden tray with a lit candle and smooth river stones, dried pampas grass in a tall minimal ceramic vase. Top 60%: smooth warm linen-toned wall, completely bare and empty. Warm golden side lighting. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1019': {
        'listing_id': '4509214051',
        'art_file': f'{ART_DIR}/DP1019.jpg',
        'out_dir': f'{ART_DIR}/DP1019_listing_images',
        'frame_color': (72, 52, 32),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A cozy mountain cabin living room corner. Bottom 40%: a warm honey-toned oak console table with a small ceramic vase of wildflowers, a lit wooden wick candle, a neatly stacked pile of nature and travel books. Top 60%: smooth warm sand-toned wall, completely bare and empty. Warm golden afternoon sunlight. No art, no frames on the wall. Professional DSLR, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A cozy boho living room. Bottom 40%: top of a cream textured linen sofa, a woven jute throw blanket, a terracotta vase with tall dried pampas grass on the side, warm natural light. Top 60%: smooth warm white wall, completely bare and empty. Bright warm natural light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1020': {
        'listing_id': '4509214237',
        'art_file': f'{ART_DIR}/DP1020.jpg',
        'out_dir': f'{ART_DIR}/DP1020_listing_images',
        'frame_color': (128, 98, 62),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A bright cheerful boho living room. Bottom 40%: top of a white slipcovered sofa with a coral and terracotta lumbar pillow, a slim rattan side table with a vase of fresh orange poppies. Top 60%: smooth warm white wall, completely bare and empty. Bright cheerful natural light. No art, no frames on the wall. Professional DSLR, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A sunny boho dining nook. Bottom 40%: a natural rattan chair back visible, an oak dining table edge with a colorful ceramic vase of wildflowers, a folded mustard linen napkin. Top 60%: smooth pale warm yellow wall, completely bare and empty. Bright airy morning light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1021': {
        'listing_id': '4509214477',
        'art_file': f'{ART_DIR}/DP1021.jpg',
        'out_dir': f'{ART_DIR}/DP1021_listing_images',
        'frame_color': (70, 45, 20),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A sophisticated home bar or gentleman\'s den. Bottom 40%: a polished dark walnut bar counter with a crystal whiskey glass holding amber whiskey, a premium whiskey bottle, a glowing vintage Edison bulb lamp on the far right casting warm amber light. Top 60%: smooth dark walnut wood-paneled wall, completely bare and empty. Warm moody amber Edison bulb lighting. No art, no frames on the wall. Professional DSLR, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A cozy British-style pub den. Bottom 40%: top of a dark green Chesterfield leather sofa arm, a small mahogany side table with a pint glass of golden beer and a worn leather-bound book. Top 60%: smooth dark hunter green wall, completely bare and empty. Warm ambient golden pub lighting. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1022': {
        'listing_id': '4509219594',
        'art_file': f'{ART_DIR}/DP1022.jpg',
        'out_dir': f'{ART_DIR}/DP1022_listing_images',
        'frame_color': (40, 55, 90),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A moody dark-aesthetic bedroom. Bottom 40%: a dark slate upholstered king headboard with white linen and charcoal pillows artfully arranged, a slim bedside table with a warm glowing table lamp and a small lit candle. Top 60%: smooth deep navy blue wall, completely bare and empty. Warm amber lamp glow from the right, dramatic moody atmosphere. No art, no frames on the wall. Professional DSLR, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A dark atmospheric living room corner. Bottom 40%: top of a deep navy velvet sofa with a silver metallic accent pillow and a dark marble side table with a small flickering candle. Top 60%: smooth midnight blue wall, completely bare and empty. Moody low-key dramatic ambient light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1023': {
        'listing_id': '4509214803',
        'art_file': f'{ART_DIR}/DP1023.jpg',
        'out_dir': f'{ART_DIR}/DP1023_listing_images',
        'frame_color': (168, 138, 78),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A modern dark loft bedroom. Bottom 40%: a sleek black platform bed with deep charcoal linen bedding, a small black nightstand with a glowing LED strip casting purple and blue ambient light, a small star projector. Top 60%: smooth dark concrete-textured loft wall, completely bare and empty. Dramatic cool-toned blue-purple ambient light. No art, no frames on the wall. Professional DSLR, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A fun colorful kids bedroom. Bottom 40%: a wooden loft bed frame, a rainbow-colored duvet with star pattern, a glowing star night-light on a small table, small rocket ship toy. Top 60%: smooth deep space-teal wall, completely bare and empty. Warm playful light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1024': {
        'listing_id': '4509219904',
        'art_file': f'{ART_DIR}/DP1024.jpg',
        'out_dir': f'{ART_DIR}/DP1024_listing_images',
        'frame_color': (28, 28, 28),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A premium man cave or home garage showroom. Bottom 40%: polished dark epoxy garage floor with a corner of a glossy red Snap-on tool chest, a chrome socket wrench set on display, a small die-cast classic car model. Top 60%: smooth dark charcoal/gunmetal painted concrete wall, completely bare and empty. Dramatic cool-toned studio spotlighting. No art, no frames on the wall. Professional DSLR, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A stylish masculine den or study. Bottom 40%: top of a dark brown full-grain leather Chesterfield sofa, a solid oak side table with a glass of bourbon, a car magazine, a coaster. Top 60%: smooth dark graphite slate wall, completely bare and empty. Warm dramatic evening light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
    'DP1025': {
        'listing_id': '4509215145',
        'art_file': f'{ART_DIR}/DP1025.jpg',
        'out_dir': f'{ART_DIR}/DP1025_listing_images',
        'frame_color': (28, 28, 28),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Etsy product mockup photography, square format. A vibrant maximalist eclectic living room. Bottom 40%: top of a deep teal velvet sofa with hot pink and saffron yellow cushions, a slim brushed gold side table holding a colorful glazed ceramic cactus sculpture. Top 60%: smooth warm mustard yellow wall, completely bare and empty. Bright vibrant natural light. No art, no frames on the wall. Professional DSLR, photorealistic. High quality.'),
            ('bg_lifestyle_room_B.jpg',
             'Etsy product mockup photography, square format. A bold eclectic Dia de los Muertos inspired dining room. Bottom 40%: a colorful hand-painted Mexican Talavera tiled table surface with marigold flowers in a clay pot, a lit votive candle, vibrant embroidered table runner. Top 60%: smooth terracotta orange wall, completely bare and empty. Warm vibrant afternoon light. No art, no frames on the wall. Professional DSLR, photorealistic interior photography. High quality.'),
        ]
    },
}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-only', action='store_true', help='Run test for one listing without uploading')
    parser.add_argument('--test-listing', default='DP1018', help='Which listing to test (default: DP1018)')
    parser.add_argument('--full-run', action='store_true', help='Run the full loop for all listings')
    parser.add_argument('--composite-only', action='store_true', help='Recomposite existing bg images without regenerating')
    args = parser.parse_args()

    if args.test_only:
        pid = args.test_listing
        info = LISTINGS[pid]
        test_bg = os.path.join(info['out_dir'], info['prompts'][0][0])
        test_comp = os.path.join(info['out_dir'], 'lifestyle_room_A.jpg')

        os.makedirs(info['out_dir'], exist_ok=True)
        print(f"Generating test room background ({pid} A)...")
        gen_room_bg(info['prompts'][0][1], test_bg)
        print("Compositing test...")
        composite(test_bg, info['art_file'], test_comp, info['frame_color'])
        print(f"TEST DONE — composite at: {test_comp}")

    elif args.composite_only:
        # Recomposite all listings using existing bg_ images (skip generation)
        for pid, info in LISTINGS.items():
            out_dir = info['out_dir']
            print(f'\n{"="*50}\n{pid} — composite only')
            for filename, _ in info['prompts']:
                bg_path = os.path.join(out_dir, filename)
                comp_path = os.path.join(out_dir, filename.replace('bg_', ''))
                if not os.path.exists(bg_path):
                    print(f'  SKIP (no bg): {filename}')
                    continue
                composite(bg_path, info['art_file'], comp_path, info['frame_color'])

    elif args.full_run:
        refresh()
        results = {}
        for pid, info in LISTINGS.items():
            lid = info['listing_id']
            out_dir = info['out_dir']
            os.makedirs(out_dir, exist_ok=True)
            print(f'\n{"="*55}\n{pid} — {lid}')
            results[pid] = {'generated': 0, 'uploaded': 0, 'errors': []}
            refresh()

            # Generate new room backgrounds
            for filename, prompt in info['prompts']:
                bg_path = os.path.join(out_dir, filename)
                print(f'  Generating {filename}...')
                try:
                    gen_room_bg(prompt, bg_path)
                    results[pid]['generated'] += 1
                except Exception as e:
                    print(f'  ERROR generating {filename}: {e}')
                    results[pid]['errors'].append(f'{filename} gen: {e}')
                    continue
                time.sleep(3)

            # Composite all generated backgrounds
            for filename, _ in info['prompts']:
                bg_path = os.path.join(out_dir, filename)
                comp_path = os.path.join(out_dir, filename.replace('bg_', ''))
                if not os.path.exists(bg_path):
                    continue
                composite(bg_path, info['art_file'], comp_path, info['frame_color'])

            # Get current rank 6/7 IDs, delete old, upload new
            rank_ids = get_rank_ids(lid)
            print(f'  current: rank6={rank_ids.get(6)}, rank7={rank_ids.get(7)}')

            for rank_offset, (filename, _) in enumerate(info['prompts']):
                rank = 6 + rank_offset
                comp_path = os.path.join(out_dir, filename.replace('bg_', ''))
                if not os.path.exists(comp_path):
                    continue
                old_id = rank_ids.get(rank)
                if old_id:
                    delete_image(lid, old_id)
                    time.sleep(0.4)
                if upload(lid, comp_path, rank):
                    results[pid]['uploaded'] += 1
                else:
                    results[pid]['errors'].append(f'rank {rank} upload failed')
                time.sleep(1.2)

        print('\n\n' + '=' * 60)
        print('FINAL RESULTS')
        print('=' * 60)
        for pid, r in results.items():
            ok = 'OK' if r['uploaded'] == 2 and not r['errors'] else 'FAIL'
            print(f'{ok} {pid}: generated={r["generated"]}/2  uploaded={r["uploaded"]}/2  errors={r["errors"] or "none"}')
    else:
        print("Use --test-only, --composite-only, or --full-run")
