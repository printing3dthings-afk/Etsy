#!/usr/bin/env python3
"""
Regenerate lifestyle room images for all wall art listings.

APPROACH: Fully AI-generated scenes — no compositing.
DALL-E generates the ENTIRE room including the art already on the wall,
described precisely to match the actual product's style and palette.
This produces photorealistic results that look completely natural.

Each listing gets 2 scene images:
  - Scene A: wide lifestyle room shot (sofa, console, or bed visible below art)
  - Scene B: close styled vignette (shelf or table with curated props)
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

client = EtsyAPIClient()
shop_id = client.shop_id
OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key": f"{client.client_id}:{client.client_secret}",
}

def refresh():
    if client.refresh_access_token():
        auth_headers["Authorization"] = f"Bearer {client.access_token}"
        print("  Token refreshed.")


def gen_scene(prompt, out_path):
    """Generate a complete lifestyle scene image via DALL-E."""
    payload = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt.strip(),
        "n": 1,
        "size": "1024x1024",
        "quality": "high",
        "output_format": "jpeg",
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"},
        method="POST",
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


def get_all_images(listing_id):
    url = f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images"
    req = urllib.request.Request(url, headers=auth_headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return {img['rank']: img['listing_image_id'] for img in data.get('results', [])}
    except Exception as e:
        print(f"  WARNING get_images: {e}")
        return {}


def delete_image(listing_id, image_id):
    url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/images/{image_id}"
    req = urllib.request.Request(url, headers=auth_headers, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=30):
            return True
    except urllib.error.HTTPError as e:
        print(f"  DELETE {image_id}: HTTP {e.code}")
        return False


def upload(listing_id, img_path, rank):
    for attempt in range(3):
        try:
            result = client.upload_listing_image(listing_id, img_path, rank=rank)
            print(f"  rank {rank} → id={result.get('listing_image_id')}")
            return True
        except EtsyAPIError as e:
            if e.status == 401:
                refresh()
            elif e.status == 429:
                time.sleep(15)
            elif e.status == 500 and attempt < 2:
                time.sleep(5)
            else:
                print(f"  rank {rank} FAILED: {e}")
                return False
    return False


# ── PROMPT GUIDELINES ─────────────────────────────────────────────────────────
# Scene A: Wide room shot — sofa/console/bench visible below hung art.
#   Shows the art in context of a full room vibe. Best for first impression.
#
# Scene B: Styled vignette — closer shot with shelf, table, or mantel below.
#   Art takes up most of the frame. Curated props. Feels editorial/Pinterest.
#
# Formula that works:
#   "Professional interior design photography, square format.
#    [Specific room style + wall color]. A large framed [exact art description]
#    in a [frame material] frame with wide white mat, hung prominently on the wall.
#    Below: [1-2 styled props matching the art theme].
#    [Lighting direction and quality]. Photorealistic, Architectural Digest
#    editorial quality. No text overlays."
#
# Art description must match the ACTUAL PRODUCT colors, subject, and style.
# ─────────────────────────────────────────────────────────────────────────────

LISTINGS = {

    # ── DP1007 — Amalfi Lemon Window (Mediterranean, impressionist) ───────────
    'DP1007': {
        'listing_id': '4509218152',
        'out_dir': f'{ART_DIR}/DP1007_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A bright Mediterranean-inspired farmhouse dining room with whitewashed walls
             and rustic dark walnut floorboards. Centered on the wall: a large framed
             impressionist painting showing yellow lemons hanging on green branches over
             open teal wooden shutters, revealing a vivid blue Mediterranean sea and
             rocky coastline — warm terracotta and turquoise tones, thick impasto
             oil-painting brushstrokes. Natural dark wood frame, wide white mat.
             Below the print: a rustic dark wood farm table set with a handmade ceramic
             bowl overflowing with fresh lemons, a small green olive oil bottle, and a
             folded linen napkin in natural linen. Warm golden late-afternoon sunlight
             streaming from the left window, casting soft warm shadows.
             Sony A7 35mm lens, f/2.8, shallow depth of field on the props,
             sharp art print. Photorealistic, Architectural Digest quality.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A bright coastal kitchen styled vignette. On a sun-bleached white limewash
             wall: a large framed impressionist oil painting of yellow lemons on vine branches
             over open teal Amalfi shutters with a brilliant blue sea view — vibrant
             turquoise, yellow, and warm terracotta palette, expressive painterly style.
             Rustic natural wood float frame, wide white mat.
             Directly below the print: a white marble-topped console with a terracotta
             plant pot holding fresh rosemary, a small hand-thrown ceramic jug, and a
             short stack of Italian cookbook spines.
             Bright diffused Mediterranean daylight. Linen curtain visible at left edge.
             50mm editorial photography, photorealistic, Pinterest wall art aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1012 — Bold Abstract Geometric (cobalt, terracotta, mid-century) ────
    'DP1012': {
        'listing_id': '4509258172',
        'out_dir': f'{ART_DIR}/DP1012_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A chic modern living room with a dusty rose painted accent wall and
             light oak hardwood floors. Centered on the wall: a large framed
             bold abstract geometric art print with asymmetric shapes and strong
             lines in cobalt blue, warm terracotta orange, and creamy off-white —
             mid-century modern style with graphic impact. Slim matte black metal
             frame, wide white mat.
             Below: a curved cream bouclé sofa with two geometric throw pillows in
             cobalt and terracotta. On the right side: a slim brass floor lamp.
             On the left: a tall fiddle-leaf fig tree in a terracotta pot.
             Bright soft natural daylight from the left. Warm, editorial feel.
             Canon 5D 35mm, f/2.8, photorealistic, Architectural Digest editorial
             quality. No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A styled gallery wall vignette with a warm white plaster wall.
             A large framed abstract art print dominates the center — bold cobalt
             blue rectangles and terracotta wedges with cream negative space,
             geometric and confident — slim matte black frame, generous white mat.
             Below: a slim walnut console table holding a single oversized abstract
             ceramic vase in terracotta, a short stack of architecture books, and a
             small trailing pothos plant in a stone pot.
             Warm neutral ambient light. Clean, minimal, gallery-quality styling.
             50mm lens, photorealistic, Etsy wall art best-seller aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1013 — Soft Floral Watercolor (peach cosmos, pastel botanical) ──────
    'DP1013': {
        'listing_id': '4509258700',
        'out_dir': f'{ART_DIR}/DP1013_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A bright airy bedroom with soft sage green walls and white linen bedding.
             Centered above the bed's headboard: a large framed watercolor botanical
             art print with soft peach and orange cosmos flowers, delicate green stems
             and leaves, on a warm cream background — loose, impressionistic watercolor
             style with beautiful color bleeding. Slim natural ash wood frame, wide
             white mat.
             The bed below has a neatly arranged set of cream and sage linen pillows.
             A small dried pampas grass arrangement in a bud vase sits on the
             nightstand to the right.
             Soft diffused morning light from a large window to the left.
             Canon R5 50mm, f/2.8, photorealistic, Home & Gardens editorial quality.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A bright styled living room corner with a warm cream plaster wall.
             A large framed soft watercolor print centered on the wall — pastel peach
             and coral orange wildflowers with loose green botanical leaves on
             a cream background, delicate and airy watercolor technique.
             Slim white-painted wood frame, wide white mat.
             Below: a white linen sofa with a blush pink textured throw pillow.
             To the right of the sofa: a small rattan side table with a small white
             ceramic pot holding a trailing string-of-pearls succulent.
             Bright spring daylight, warm and cheerful.
             50mm, photorealistic, Pinterest botanical decor aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1014 — "Good Things Take Time" Typography ───────────────────────────
    'DP1014': {
        'listing_id': '4509213345',
        'out_dir': f'{ART_DIR}/DP1014_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A cozy feminine home office with warm white walls and natural light.
             Centered on the wall: a large framed minimalist typography print with
             the words "Good Things Take Time" in elegant thin serif lettering,
             warm cream and soft gold tones on an off-white background — clean,
             sophisticated, and calming. Slim natural wood frame, wide white mat.
             Below: a white wooden floating shelf holding a small succulent in a
             white pot, a cream ceramic mug, and two short candle votives.
             Desk below the shelf with a MacBook, gold pen holder, and fresh flowers.
             Soft warm natural light from the right. Cozy, productive, aspirational mood.
             50mm, f/2.8, photorealistic, Etsy inspirational prints aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A styled bedroom nightstand vignette with a soft warm white wall.
             Hung on the wall above a natural oak nightstand: a framed minimalist
             typography print reading "Good Things Take Time" in elegant serif font —
             cream, warm beige, and soft sand tones, clean and refined.
             Slim champagne gold frame, wide white mat.
             On the nightstand below: a small bedside lamp with warm light glowing,
             a cream ceramic bud vase with a single dried lunaria sprig, and a
             hardcover book. White linen bedding edges visible at the bottom left.
             Warm evening lamp light, soft and intimate.
             50mm, photorealistic, Scandi bedroom decor aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1015 — "She Believed She Could" Quote ───────────────────────────────
    'DP1015': {
        'listing_id': '4509213533',
        'out_dir': f'{ART_DIR}/DP1015_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A bright feminine dressing room or walk-in closet styled as a vanity space.
             Warm cream walls. Centered on the wall: a large framed inspirational
             quote print reading "She Believed She Could So She Did" in flowing
             elegant script lettering with a thin serif accent line — warm gold
             and champagne tones on a soft white background.
             Slim brushed gold frame, wide white mat.
             Below: a slim white vanity shelf with a small makeup brush holder in
             marble, a mini bouquet of blush dried roses in a gold bud vase,
             and a white ceramic ring dish.
             Warm soft natural light. Feminine, empowering, aspirational mood.
             50mm, photorealistic, girls room decor aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A styled home office corner with soft blush pink painted walls.
             A large framed motivational quote print on the wall: "She Believed
             She Could So She Did" in elegant handwritten-style script with delicate
             floral accents — warm gold, blush, and white palette, feminine and bold.
             Slim matte white frame, wide white mat.
             Below: a white lacquer desk with a gold-accented MacBook, a small
             bouquet of pink ranunculus flowers in a clear glass vase, and a
             gold pen cup.
             Natural daylight, clean and bright. Inspiring, professional atmosphere.
             35mm, f/2.8, photorealistic, Etsy printable quote art aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1016 — Cherry Blossom Watercolor (Japanese-inspired, pink, delicate) ─
    'DP1016': {
        'listing_id': '4509213667',
        'out_dir': f'{ART_DIR}/DP1016_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A serene Japandi-inspired bedroom with warm white plastered walls
             and natural linen bedding. Above the low platform bed: a large framed
             delicate watercolor print of cherry blossom branches in soft blush pink
             and white, with graceful arching stems and petals floating gently —
             Japanese sumi-e inspired style, airy and calming.
             Slim pale natural wood frame, wide white mat.
             Low Japanese platform bed below with neatly stacked cream and blush
             linen pillows. To the left: a round washi paper pendant lamp softly
             glowing. To the right: a small ceramic ikebana vase with a single
             dried cherry blossom branch.
             Soft morning light. Peaceful, elegant, minimalist atmosphere.
             50mm, f/2, photorealistic, Japandi bedroom aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A bright styled corner with a soft blush pink limewash wall.
             A large framed cherry blossom art print prominently hung — delicate
             watercolor blush pink sakura flowers on graceful dark branches
             against a soft cream background, petals drifting, Japanese botanical style.
             Slim natural light wood frame, wide white mat.
             Below: a slim rattan console with a white ceramic round pot holding a
             small bonsai tree, a folded cream linen, and a tiny stone pebble dish.
             Soft diffused spring daylight. Tranquil and feminine.
             50mm, photorealistic, Japanese botanical print aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1017 — Bold Abstract Expressionist (mustard, charcoal, taupe) ───────
    'DP1017': {
        'listing_id': '4509259354',
        'out_dir': f'{ART_DIR}/DP1017_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A sophisticated modern living room with warm greige walls and
             polished concrete flooring. Centered on the wall: a large framed
             bold abstract expressionist painting with energetic brushstrokes
             in mustard yellow, warm taupe, and deep charcoal gray — gestural,
             textured, full of movement and confidence. Slim natural walnut wood
             frame, wide white mat.
             Below: a low charcoal gray mid-century modern sofa with a mustard
             yellow textured throw blanket folded over one arm. To the right:
             a tall sculptural black metal floor lamp.
             Natural warm afternoon light, dramatic and editorial.
             35mm, f/2.8, photorealistic, interior design magazine quality.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A styled art-lover's home study or gallery corner.
             Warm white plastered wall. A large framed abstract art print — thick
             expressive brushstrokes in mustard gold and charcoal gray, with taupe
             mid-tones, raw and confident abstract expressionist style.
             Slim dark walnut frame, wide white mat.
             Below: a black lacquered media credenza with a sculptural abstract
             ceramic piece in warm terracotta, two architecture books lying flat,
             and a trailing golden pothos plant in a matte black pot.
             Warm diffused natural light. Bold, gallery-worthy aesthetic.
             50mm, photorealistic, contemporary art collector's home aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1018 — Japandi Minimalist Tree (gray, golden sun, zen) ─────────────
    'DP1018': {
        'listing_id': '4509218860',
        'out_dir': f'{ART_DIR}/DP1018_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A serene Japandi living room with warm greige plaster walls and
             light natural oak flooring. Centered on the wall above a low oak
             bench: a large framed minimalist print of a bare winter tree silhouette
             in muted warm gray, with a large golden amber circle (sun) in the
             background — simple, zen, and deeply calming. Two-tone composition
             of textured gray and warm cream. Slim natural light oak wood frame,
             wide white mat.
             The low oak bench below holds a neatly folded cream linen throw,
             a small glazed ceramic bonsai pot on the right, and a washi paper
             floor lamp glowing softly on the far right.
             Soft warm diffused natural light from the left.
             Sony A7 50mm, f/2, photorealistic, Japandi interior design aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A calm Japandi bedroom styled vignette with warm white textured
             plaster walls. A large framed minimalist tree print hung above
             a natural oak floating shelf — single bare tree silhouette in soft
             gray against a warm cream background with a large amber golden
             circle, meditative and still. Slim pale oak frame, wide white mat.
             On the shelf below: a round white ceramic bowl, a single smooth
             river stone, and a tiny bonsai in a shallow black pot.
             Below the shelf: white linen bedding just visible.
             Soft morning light. Pure and contemplative atmosphere.
             50mm, photorealistic, zen minimalism aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1019 — Mountain Meadow Golden Hour (landscape, ochre, impressionist) ─
    'DP1019': {
        'listing_id': '4509214051',
        'out_dir': f'{ART_DIR}/DP1019_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A warm cozy living room with cream linen walls and honey-toned
             oak herringbone flooring. Centered on the wall: a large framed
             impressionist landscape painting of a mountain meadow at golden hour —
             wildflowers in amber, ochre, and pale lavender, misty mountain ranges
             in the distance, warm glowing light across rolling hills.
             Painterly impressionist style with soft, luminous brushwork.
             Natural walnut wood frame, wide white mat.
             Below: a cream linen tuxedo sofa with two autumn-toned throw pillows
             in ochre and rust. To the right: a tall branchy dried flower arrangement
             in a slim terracotta vase.
             Warm afternoon golden light. Nature-lover's home, cozy and inviting.
             35mm, f/2.8, photorealistic, organic modern home aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A styled nature-lover's reading nook corner with warm cream walls.
             A large framed golden hour mountain meadow painting hung prominently —
             sweeping landscape with amber wildflowers, hazy violet mountain peaks,
             and warm impressionist evening light across a green valley.
             Slim natural wood frame, wide white mat.
             Below: a cozy curved wicker egg chair with a cream knit throw draped
             over it. To the side: a small round wood side table with a steaming
             ceramic mug and an open paperback book.
             Warm late afternoon daylight filtering through sheer linen curtains.
             50mm, photorealistic, cottage-core nature lover aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1020 — Poppy Field Watercolor (pink, orange, impressionist botanical) ─
    'DP1020': {
        'listing_id': '4509214237',
        'out_dir': f'{ART_DIR}/DP1020_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A bright airy living room with warm white plaster walls and
             natural woven jute rug. Centered on the wall: a large framed soft
             watercolor art print of a poppy meadow — loose impressionistic pink
             and orange poppies with green stems on a creamy ivory background,
             petals rendered with beautiful color washes and fluid brushstrokes.
             Slim pale natural wood frame, wide white mat.
             Below: a cream linen sofa with a blush pink velvet throw pillow and
             a soft sage green textured cushion. A tall vase of dried pampas
             grass stands in the left corner.
             Bright natural morning light. Feminine, fresh, and inviting.
             50mm, f/2.8, photorealistic, botanical art lover's home aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A styled kitchen or dining room wall with warm white painted brick.
             A large framed soft watercolor poppy print hung above a slim console —
             pink and coral orange poppies in impressionistic loose watercolor,
             delicate green leaves on cream background. Slim white wood frame,
             wide white mat.
             Below on the console: a clear glass vase with fresh pink ranunculus,
             a small ceramic pitcher, and a worn linen cloth.
             Natural bright window light. Fresh, airy, and botanical.
             50mm, photorealistic, French country kitchen aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1021 — Dog at the Bar Portrait (golden retriever, dark Dutch oil) ───
    'DP1021': {
        'listing_id': '4509214477',
        'out_dir': f'{ART_DIR}/DP1021_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A warm masculine bar or man cave styled space with dark walnut paneling
             and leather furnishings. On a deep espresso brown wall: a large framed
             oil painting portrait in Dutch master style — a golden retriever dog
             wearing round reading glasses, sitting upright at an old wooden pub bar
             with a frothy pint of amber ale in front of him, rich dark tavern
             atmosphere, warm candlelight tones of amber and brown, dignified and
             humorous. Slim dark walnut frame, white mat.
             Below: a dark wood bar cart with crystal whiskey glasses, a bourbon
             decanter, and a small brass bowl of nuts.
             Warm Edison bulb ambient light. Rich, moody, sophisticated-yet-fun.
             35mm, f/2, photorealistic, gentleman's study or bar aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A cozy pub-style corner in a home with warm amber plaster walls.
             A large framed Dutch old master-style painting of a distinguished
             golden retriever wearing spectacles at a tavern bar with a pint —
             dark warm tones of amber, mahogany, and ochre, humorous yet regal
             portrait style. Slim dark wood frame, white mat.
             Below: a slim dark oak floating shelf with a row of vintage books
             by their spines, a small bronze dog figurine, and a whiskey glass.
             Warm lamplight ambiance. Quirky, charming, conversation-starting.
             50mm, photorealistic, eclectic English pub home bar aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1022 — Full Moon Over Ocean (navy, silver, dramatic night) ──────────
    'DP1022': {
        'listing_id': '4509219594',
        'out_dir': f'{ART_DIR}/DP1022_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A calm, moody coastal bedroom with deep navy blue painted walls and
             natural linen bedding. Centered on the wall above the headboard:
             a large framed seascape art print — a dramatic full moon rising high
             over dark rolling ocean waves at night, brilliant silver moonlight
             reflecting across the dark navy water, a single glowing orb in
             a deep midnight sky. Slim brushed silver frame, wide white mat.
             Below: a low upholstered headboard in deep charcoal linen with
             cream and navy pillow arrangement. On each nightstand: a small
             silver geometric table lamp glowing softly.
             Ambient lamp light, moody and serene. Ocean lover's retreat.
             50mm, f/2, photorealistic, coastal luxury bedroom aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A styled meditation or reading nook with dark navy blue walls
             and warm lighting. A large framed night ocean print hung on the wall —
             silver-white full moon glowing above dark churning waves,
             deep navy and midnight tones, dramatic and peaceful simultaneously.
             Slim black metal frame, wide white mat.
             Below: a low rattan pouf ottoman with a cream knit blanket draped on
             it. To the right: a small carved wood side table with a diffuser
             glowing and a smooth white river stone.
             Warm amber candlelight and soft ceiling lamp glow.
             50mm, photorealistic, spiritual coastal decor aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1023 — Astronaut in Cosmos (retro NASA poster, bold vintage) ────────
    'DP1023': {
        'listing_id': '4509214803',
        'out_dir': f'{ART_DIR}/DP1023_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A modern eclectic living room with warm white walls and mid-century
             modern furniture. Centered on the wall: a large framed retro space
             poster-style art print — an astronaut floating weightlessly in colorful
             cosmic space surrounded by vivid nebulae in cobalt blue, magenta,
             and gold, with scattered stars, vintage NASA-inspired poster aesthetic
             with bold graphic design and stylized typography.
             Slim matte black frame, wide white mat.
             Below: a mustard yellow mid-century sofa with a small round walnut
             coffee table. On the table: a small rocket ship model figurine and
             an open coffee table book about space exploration.
             Bright natural daylight. Playful, bold, adventurous atmosphere.
             35mm, f/2.8, photorealistic, modern eclectic home aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A cool teen bedroom or creative studio with blue-grey painted walls.
             A large framed vintage space exploration poster dominates the wall —
             lone astronaut in a white suit floating through a vivid nebula cloud
             of deep blue, purple, and gold cosmic dust, retro screen-print style
             with bold color blocking and starfield background.
             Slim brushed silver frame, white mat.
             Below: a white lacquer floating shelf with a small model of the
             solar system, a potted cactus, and a string of warm Edison fairy lights.
             Bright cool natural light. Creative, inspiring, adventurous mood.
             50mm, photorealistic, space-lover's room aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1024 — 1967 Chevelle Muscle Car (bold poster, automotive graphic) ───
    'DP1024': {
        'listing_id': '4509219904',
        'out_dir': f'{ART_DIR}/DP1024_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A stylish masculine garage-chic or man cave interior with exposed
             dark brick walls and polished concrete floor. On a dark charcoal
             painted wall: a large framed bold automotive art print of a classic
             1967 Chevelle SS muscle car — dramatic graphic poster art style with
             deep black and vivid color accents, American muscle car silhouette,
             bold and powerful. Slim matte black floating frame, white mat.
             Below: a low dark wood media cabinet with a pair of matte black
             ceramic bowls, a vintage metal car-themed sign, and a small cactus
             in a concrete pot.
             Cool industrial lighting. Bold, masculine, collector's aesthetic.
             35mm, photorealistic, automotive man cave decor.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A styled modern living room corner with charcoal gray accent wall.
             A large framed classic muscle car poster art hung prominently —
             bold graphic illustration of a 1967 Chevelle SS, strong lines and
             dramatic color blocking in deep black, vivid red, and chrome accents,
             American automotive heritage style. Slim dark metal frame, white mat.
             Below: a low dark walnut floating shelf with a scaled die-cast model
             car, two short bourbon glasses, and a leather-bound book on
             classic American cars.
             Warm industrial accent lighting, Edison bulbs visible.
             50mm, photorealistic, automotive collector's home aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1025 — Day of the Dead Sugar Skull (vibrant, marigold, Mexican) ─────
    'DP1025': {
        'listing_id': '4509215145',
        'out_dir': f'{ART_DIR}/DP1025_listing_images',
        'lifestyle_ranks': (6, 7),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A vibrant Bohemian living room with warm terracotta orange walls
             and colorful woven textile accents. On the wall: a large framed
             Day of the Dead art print — an ornate female sugar skull portrait
             surrounded by marigold flowers, roses, and traditional decorative
             patterns in vivid magenta, cobalt blue, marigold orange, emerald
             green, and deep purple — celebratory and richly detailed.
             Slim dark walnut frame, wide white mat.
             Below: a colorful Oaxacan textile-covered bench with vibrant
             cushions. To the left: a tall woven basket with dried marigold
             stems. To the right: a small altar-style shelf with a white candle.
             Warm ambient light with accent glow. Bold, cultural, festive.
             35mm, photorealistic, Boho Mexican folk art home aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A colorful eclectic hallway or entry nook with deep teal painted
             walls. A large framed Day of the Dead sugar skull portrait hung
             center — a woman's face transformed into an ornate calavera with
             marigold and rose headdress, intricate decorative patterns, and
             vivid saturated colors of magenta, gold, cobalt, and purple.
             Slim matte black frame, wide white mat.
             Below: a slim painted wood console in deep blue with a clay bowl
             of fresh marigold flowers, two mismatched pillar candles, and
             a decorative painted tile.
             Warm lamp glow and ambient lighting. Festive and bold.
             50mm, photorealistic, Día de los Muertos folk art aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1030 — Moon Phases Chart (celestial, navy, gold) ───────────────────
    'DP1030': {
        'listing_id': '4509598660',
        'out_dir': f'{ART_DIR}/DP1030_listing_images',
        'lifestyle_ranks': (1, 2),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A moody, romantic bedroom with deep navy blue painted walls and
             warm brass accents throughout. Centered on the wall above the bed:
             a large framed celestial art print showing all lunar phases from
             new moon to full moon, arranged in a 2x3 grid with gold line
             illustrations of each moon phase on a deep navy background,
             each labeled in delicate gold serif typography.
             Slim brushed brass frame, wide white mat.
             Below: upholstered navy velvet headboard with cream and champagne
             gold pillow arrangement. On the nightstand: a small brass table
             lamp glowing warmly, an amethyst crystal cluster, and a dried
             lavender sprig in a small bud vase.
             Warm ambient lamp light. Celestial, moody, and sophisticated.
             50mm, f/2, photorealistic, dark academia bedroom aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A styled mystical reading nook with slate gray walls and warm
             candlelight. A large framed moon phases poster hung on the wall —
             six moon phase illustrations from crescent to full moon in gold
             line art on deep navy background, elegant astronomical chart style.
             Slim black metal frame, white mat.
             Below: a wooden floating shelf styled with a small crystal ball,
             a stack of dark hardcover books, a thin white taper candle in
             a brass holder, and a small dried botanical bundle.
             Warm candlelit glow and soft ceiling light. Mystical and serene.
             50mm, photorealistic, witchy celestial home decor aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1031 — Abstract Expressionist Brushstroke (cobalt, terracotta) ──────
    'DP1031': {
        'listing_id': '4509598784',
        'out_dir': f'{ART_DIR}/DP1031_listing_images',
        'lifestyle_ranks': (1, 2),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A sophisticated modern living room with warm linen white walls
             and polished light oak floors. Centered on the wall: a large framed
             abstract expressionist painting with bold, sweeping brushstrokes in
             cobalt blue and warm terracotta, layered with cream and raw linen
             tones — textured, gestural, and full of energy and depth.
             Slim natural walnut frame, wide white mat.
             Below: a long low cream curved sofa with cobalt blue and terracotta
             throw pillows. In the left corner: a tall terracotta amphora vase
             with dried pampas grass stems.
             Bright diffused natural daylight. Modern, gallery-quality setting.
             35mm, f/2.8, photorealistic, organic modern art home.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             An art-lover's gallery hallway with smooth warm off-white walls.
             A large framed abstract canvas print takes center stage — dynamic
             brushwork in cobalt blue sweeping across terracotta orange, with
             creamy off-white revealed underneath, raw and confident mark-making.
             Slim black metal gallery frame, wide white mat.
             Below: a slim travertine console with a cobalt blue ceramic vase,
             a small white sculptural object, and a single dried protea bloom.
             Clean, bright, museum-quality natural light.
             50mm, photorealistic, contemporary art gallery home aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1032 — Vintage Botanical Herbarium (antique, parchment, Victorian) ──
    'DP1032': {
        'listing_id': '4509593487',
        'out_dir': f'{ART_DIR}/DP1032_listing_images',
        'lifestyle_ranks': (1, 2),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A cozy English cottage-inspired study or library with warm cream
             walls and dark wood bookshelves filled with leather-bound books.
             Hung on the wall between two shelves: a large framed antique
             botanical herbarium art print — Victorian-era scientific plant
             illustration with detailed pencil-and-watercolor drawings of
             botanical specimens, Latin species names in italic script, aged
             parchment background in warm sepia and cream tones.
             Slim dark mahogany wood frame, wide white mat.
             Below: a dark wood writing desk with a brass desk lamp glowing,
             an open leather journal, a potted fern, and a glass inkwell.
             Warm incandescent library light. Scholarly, antique, charming.
             35mm, photorealistic, English study library aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A bright Scandinavian living room with warm white walls and
             honey oak furniture. A large framed vintage botanical herbarium
             print hung above a wooden console — antique-style detailed plant
             illustrations with Latin botanical names, warm sepia and cream
             tones on aged parchment, multiple botanical specimens arranged
             in a classic scientific plate layout.
             Slim natural oak frame, wide white mat.
             Below the console: a small potted maidenhair fern, a ceramic
             apothecary jar with dried herbs, and a short stack of botanical
             art books.
             Soft bright natural daylight. Fresh, intellectual, nature-loving.
             50mm, photorealistic, botanical art Scandinavian home aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1033 — Paris Skyline Minimalist (line art, Eiffel, black on white) ──
    'DP1033': {
        'listing_id': '4509593623',
        'out_dir': f'{ART_DIR}/DP1033_listing_images',
        'lifestyle_ranks': (1, 2),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A chic Parisian-inspired living room with warm cream walls and
             herringbone parquet flooring. Centered on the wall: a large framed
             minimalist Paris city art print — elegant line art illustration of
             the Paris skyline including the Eiffel Tower, Sacré-Coeur, and
             classic Haussmann rooftops, drawn in clean thin black lines on
             a pure white background, sophisticated and architectural.
             Slim matte black frame, wide white mat.
             Below: a classic cream linen tuxedo sofa with a black and cream
             striped throw blanket. On the left: a slim marble side table with
             a glass of champagne and a small Eiffel Tower sculptural object.
             Warm Parisian afternoon light. Elegant, romantic, sophisticated.
             50mm, f/2.8, photorealistic, Parisian apartment decor aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A styled feminine home office with soft blush pink walls and
             gold accents. A large framed Paris skyline line art print hung
             prominently — minimalist black line drawing of Eiffel Tower and
             Parisian rooftops on white, clean and elegant.
             Slim brushed gold frame, wide white mat.
             Below: a white lacquer floating shelf with a small gilded Eiffel
             Tower figurine, a pink peony in a slim gold bud vase, and a
             small French perfume bottle.
             Soft warm daylight. Dreamy, romantic, travel-lover's space.
             50mm, photorealistic, Je t'aime Paris girl's room aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1034 — Grand Canyon WPA Retro Poster (vintage travel, bold, orange) ─
    'DP1034': {
        'listing_id': '4509593697',
        'out_dir': f'{ART_DIR}/DP1034_listing_images',
        'lifestyle_ranks': (1, 2),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A warm nature-lover's living room with warm white walls and
             wood-paneled ceiling. Centered on the wall: a large framed
             vintage WPA-style travel poster of the Grand Canyon — bold
             simplified geological formations in deep burnt orange, dusty
             terracotta, and sky blue, with cream and warm white highlights,
             retro 1930s national park poster aesthetic with stylized typography
             and graphic artistry.
             Slim natural wood frame, wide white mat.
             Below: a mid-century modern amber leather sofa with a Navajo-
             patterned throw blanket. On the left: a potted prickly pear cactus
             in a clay pot. On the right: a vintage National Geographic atlas.
             Warm afternoon natural light. Adventure-lover's home, bold and warm.
             35mm, photorealistic, national park collector's home aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A styled southwestern boho living corner with terracotta clay walls.
             A large framed Grand Canyon retro poster art print hung on the wall —
             bold graphic WPA-style landscape with layered canyon formations in
             burnt orange, terracotta, and cobalt blue, retro travel poster style.
             Slim natural rustic wood frame, white mat.
             Below: a slim woven rattan console with a pair of small clay pots
             with succulents, a small Kachina doll, and a rough geode slice.
             Warm terracotta-toned ambient light. Adventurous southwestern feel.
             50mm, photorealistic, desert boho southwestern decor.
             No text overlays."""),
        ],
    },

    # ── DP1035 — Tropical Bold Leaves (Matisse, monstera, jungle green) ───────
    'DP1035': {
        'listing_id': '4509600086',
        'out_dir': f'{ART_DIR}/DP1035_listing_images',
        'lifestyle_ranks': (1, 2),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A vibrant tropical-inspired living room with white plaster walls
             and rattan and bamboo furniture. Centered on the wall: a large
             framed bold tropical leaf art print — oversized monstera, banana
             palm, and philodendron leaves in deep jungle green and golden
             yellow with black outlines, bold flat Matisse-inspired graphic
             style, energetic and lush.
             Slim natural bamboo or rattan-wrapped frame, wide white mat.
             Below: a rattan peacock chair with a sage green linen cushion.
             Flanking the art: two tall live monstera deliciosa plants in
             large wicker baskets.
             Bright tropical natural daylight. Lush, verdant, resort-style living.
             35mm, f/2.8, photorealistic, tropical maximalist home aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A styled bright sun room or porch with whitewashed walls and
             terracotta tile flooring. A large framed tropical leaves art print
             hung prominently — bold oversized jungle foliage in vivid deep green
             with golden yellow highlights, graphic flat illustration style,
             confident and tropical.
             Slim white painted wood frame, wide white mat.
             Below: a cream linen loveseat with jungle green and banana yellow
             throw pillows. To the left: a large bird of paradise plant in a
             woven banana leaf basket.
             Brilliant tropical daylight. Fresh, bold, vacation-home vibes.
             50mm, photorealistic, tropical resort interior aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1036 — Abstract Female Portrait Line Art (feminist, single line) ────
    'DP1036': {
        'listing_id': '4509596017',
        'out_dir': f'{ART_DIR}/DP1036_listing_images',
        'lifestyle_ranks': (1, 2),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A chic feminine bedroom with warm blush pink walls and brass accents.
             Centered on the wall: a large framed minimalist line art portrait of
             a woman's face and flowing hair drawn in a single continuous black
             line on white, with botanical flowers and leaves incorporated into
             the hair — elegant, artistic, feminist, and modern.
             Slim slim matte black frame, wide white mat.
             Below: an upholstered blush velvet headboard with cream and dusty
             pink linen pillows arranged softly. On the nightstand: a small
             brass table lamp glowing warm, a single white peony in a bud vase.
             Warm soft natural light. Feminine, artistic, empowering atmosphere.
             50mm, f/2, photorealistic, feminine art bedroom aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A bright styled art studio or creative corner with warm white walls.
             A large framed abstract female line art print hung center — a woman's
             portrait in a single continuous flowing black line on pure white,
             floral botanical elements integrated into the hair design, clean and
             confident minimalism.
             Slim natural wood frame, wide white mat.
             Below: a slim marble-top console with a white ceramic figure sculpture,
             a glass vase of dried white craspedia, and a paint-stained linen cloth.
             Bright diffused natural studio light. Artistic, clean, inspired.
             50mm, photorealistic, artist's home studio aesthetic.
             No text overlays."""),
        ],
    },

    # ── DP1037 — Italian Kitchen Food Art (watercolor, Mediterranean food) ─────
    'DP1037': {
        'listing_id': '4509597559',
        'out_dir': f'{ART_DIR}/DP1037_listing_images',
        'lifestyle_ranks': (1, 2),
        'scenes': [
            ('lifestyle_room_A.jpg',
             """Professional interior design photography, square format.
             A warm inviting Italian-style kitchen with white subway tile backsplash,
             open wooden shelving, and terracotta tile floors. Hung on the wall above
             open shelving: a large framed Italian kitchen watercolor art print —
             a loose painterly watercolor illustration featuring a glass bottle of
             olive oil, fresh pasta, a bunch of basil, garlic bulbs, a wine glass
             with red wine, and a wedge of parmesan — warm Mediterranean palette
             of olive green, terracotta, burgundy, and cream.
             Slim natural olive wood frame, wide white mat.
             Below: open shelving with olive oil bottles, herb pots, and ceramic dishes.
             On the counter: a wooden pasta board and fresh produce.
             Warm Mediterranean kitchen light. Inviting, rustic Italian comfort.
             35mm, photorealistic, Italian farmhouse kitchen aesthetic.
             No text overlays."""),
            ('lifestyle_room_B.jpg',
             """Professional interior design photography, square format.
             A warm styled dining room corner with warm cream walls and a rustic
             walnut dining table partially visible. On the wall: a large framed
             Italian food watercolor art print — hand-painted watercolor of
             classic Italian ingredients including olive oil bottle, spaghetti,
             fresh basil, garlic, tomatoes, and chianti wine glass, warm
             Mediterranean palette in terracotta, olive green, and cream.
             Slim rustic walnut frame, wide white mat.
             Below: a corner of a rustic dining table set with ceramic plates,
             a linen napkin, and a short candle in a terracotta holder.
             Warm candlelit evening dining ambiance.
             50mm, photorealistic, Italian trattoria home dining aesthetic.
             No text overlays."""),
        ],
    },
}


def run_for(pids):
    refresh()
    results = {}

    for pid in pids:
        info = LISTINGS.get(pid)
        if not info:
            print(f"  Unknown listing: {pid}")
            continue

        lid = info['listing_id']
        out_dir = info['out_dir']
        rank_a, rank_b = info['lifestyle_ranks']
        os.makedirs(out_dir, exist_ok=True)
        results[pid] = {'generated': 0, 'uploaded': 0, 'errors': []}

        print(f"\n{'='*55}")
        print(f"{pid} — listing {lid}  (lifestyle at ranks {rank_a},{rank_b})")

        # Generate scene A — use a temp path so we never upload an old file on failure
        fname_a, prompt_a = info['scenes'][0]
        tmp_a = os.path.join(out_dir, f'_new_{fname_a}')
        path_a = os.path.join(out_dir, fname_a)
        print(f"  Generating scene A: {fname_a}")
        refresh()
        gen_a_ok = gen_scene(prompt_a, tmp_a)
        if gen_a_ok:
            os.replace(tmp_a, path_a)
            results[pid]['generated'] += 1
        else:
            results[pid]['errors'].append('scene A gen failed')
        time.sleep(5)

        # Generate scene B
        fname_b, prompt_b = info['scenes'][1]
        tmp_b = os.path.join(out_dir, f'_new_{fname_b}')
        path_b = os.path.join(out_dir, fname_b)
        print(f"  Generating scene B: {fname_b}")
        gen_b_ok = gen_scene(prompt_b, tmp_b)
        if gen_b_ok:
            os.replace(tmp_b, path_b)
            results[pid]['generated'] += 1
        else:
            results[pid]['errors'].append('scene B gen failed')
        time.sleep(3)

        # Only upload freshly generated images — never upload old composites
        refresh()
        existing = get_all_images(lid)
        print(f"  Existing image ranks: {sorted(existing.keys())}")

        for rank, path, ok in [(rank_a, path_a, gen_a_ok), (rank_b, path_b, gen_b_ok)]:
            if not ok:
                print(f"  SKIP rank {rank} — generation failed, keeping existing image")
                results[pid]['errors'].append(f'rank {rank} skipped (gen failed)')
                continue
            old_id = existing.get(rank)
            if old_id:
                print(f"  Deleting old rank {rank} id={old_id}")
                delete_image(lid, old_id)
                time.sleep(0.5)
            if upload(lid, path, rank):
                results[pid]['uploaded'] += 1
            else:
                results[pid]['errors'].append(f'rank {rank} upload failed')
            time.sleep(1.5)

    print('\n\n' + '=' * 55)
    print('FINAL RESULTS')
    print('=' * 55)
    for pid, r in results.items():
        status = 'OK' if r['generated'] == 2 and r['uploaded'] == 2 else 'FAIL'
        print(f"{status}  {pid}: generated={r['generated']}/2  "
              f"uploaded={r['uploaded']}/2  errors={r['errors'] or 'none'}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--full-run', action='store_true',
                        help='Regenerate all listings')
    parser.add_argument('--listings', nargs='+', metavar='PID',
                        help='Only process these listing IDs (e.g. --listings DP1007 DP1018)')
    parser.add_argument('--test', metavar='PID', default=None,
                        help='Generate scene A for one listing locally without uploading')
    args = parser.parse_args()

    if args.test:
        pid = args.test
        info = LISTINGS.get(pid)
        if not info:
            print(f"Unknown listing: {pid}")
            sys.exit(1)
        os.makedirs(info['out_dir'], exist_ok=True)
        out = os.path.join(info['out_dir'], 'test_scene_A.jpg')
        print(f"Test generating scene A for {pid}...")
        gen_scene(info['scenes'][0][1], out)
        print(f"Saved to: {out}")

    elif args.full_run:
        run_for(list(LISTINGS.keys()))

    elif args.listings:
        run_for(args.listings)

    else:
        print("Use --full-run, --listings DP1007 DP1018 ..., or --test DP1007")
