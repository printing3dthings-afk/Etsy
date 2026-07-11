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
    "x-api-key": client.client_id,
}

def refresh_if_needed():
    """Refresh the access token and update auth_headers."""
    if client.refresh_access_token():
        auth_headers["Authorization"] = f"Bearer {client.access_token}"
        print("  Token refreshed.")
    else:
        print("  WARNING: Token refresh failed.")

def gen_room_bg(prompt, out_path):
    payload = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "medium",
        "output_format": "jpeg"
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"},
        method="POST"
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            img_bytes = base64.b64decode(data["data"][0]["b64_json"])
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            print(f"  Room bg: {os.path.basename(out_path)} ({len(img_bytes)//1024}KB)")
            return out_path
        except Exception as e:
            if attempt == 0:
                print(f"  Retry after error: {e}")
                time.sleep(10)
            else:
                raise

from PIL import Image, ImageDraw, ImageFilter

def composite_art_in_room(room_bg_path, art_path, out_path, frame_color=(82, 60, 40)):
    """Resize room bg to 2400x2400, composite actual artwork in a frame on the wall."""
    room = Image.open(room_bg_path).convert('RGB').resize((2400, 2400), Image.LANCZOS)
    art = Image.open(art_path).convert('RGB')

    # Art: 42% of canvas width, preserving aspect ratio
    art_w = int(2400 * 0.42)
    art_h = int(art_w * art.height / art.width)
    art = art.resize((art_w, art_h), Image.LANCZOS)

    mat_w = 36
    frame_w = 13
    full_w = art_w + 2 * mat_w + 2 * frame_w
    full_h = art_h + 2 * mat_w + 2 * frame_w

    # Position: centered horizontally, 7% from top (wall area)
    px = (2400 - full_w) // 2
    py = int(2400 * 0.07)

    # Drop shadow
    shadow = Image.new('RGBA', (2400, 2400), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle(
        [px + 16, py + 20, px + full_w + 16, py + full_h + 20],
        fill=(0, 0, 0, 95)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=22))
    room = Image.alpha_composite(room.convert('RGBA'), shadow).convert('RGB')

    draw = ImageDraw.Draw(room)
    # Frame border
    draw.rectangle([px, py, px + full_w, py + full_h], fill=frame_color)
    # White mat
    mx, my = px + frame_w, py + frame_w
    draw.rectangle([mx, my, mx + art_w + 2*mat_w, my + art_h + 2*mat_w], fill=(252, 250, 247))
    # Paste actual artwork
    room.paste(art, (mx + mat_w, my + mat_w))

    room.save(out_path, 'JPEG', quality=92)
    print(f"  Composite: {os.path.basename(out_path)} ({os.path.getsize(out_path)//1024}KB)")

def get_rank_image_ids(listing_id, ranks=(6, 7)):
    url = f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images"
    req = urllib.request.Request(url, headers=auth_headers, method="GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    rank_map = {}
    for img in data.get('results', []):
        r = img.get('rank')
        if r in ranks:
            rank_map[r] = img.get('listing_image_id')
    return rank_map

def delete_image(listing_id, image_id):
    url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/images/{image_id}"
    req = urllib.request.Request(url, headers=auth_headers, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=30):
            return True
    except urllib.error.HTTPError as e:
        print(f"  DELETE {image_id}: {e.code} {e.read().decode()[:100]}")
        return False

LISTINGS = {
    'DP1007': {
        'listing_id': '4509218152',
        'art_file': f'{ART_DIR}/DP1007.jpg',
        'out_dir': f'{ART_DIR}/DP1007_listing_images',
        'frame_color': (70, 45, 20),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth warm terracotta-tinted plaster wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom of the frame, a glimpse of a white marble countertop with a small lemon in a ceramic bowl. Bright Mediterranean light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth whitewashed wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a slim wooden console table with a small ceramic vase. Warm coastal daylight. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1012': {
        'listing_id': '4509258172',
        'art_file': f'{ART_DIR}/DP1012.jpg',
        'out_dir': f'{ART_DIR}/DP1012_listing_images',
        'frame_color': (30, 30, 30),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth dusty pink painted wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a glimpse of a mustard velvet sofa arm and a rattan side table. Warm natural light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth sage green painted wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a slim white floating shelf with a small plant. Bright natural daylight. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1013': {
        'listing_id': '4509258700',
        'art_file': f'{ART_DIR}/DP1013.jpg',
        'out_dir': f'{ART_DIR}/DP1013_listing_images',
        'frame_color': (140, 110, 72),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth pale sage green nursery wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a white wooden crib rail and a folded ivory knit blanket. Soft gentle morning light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth warm cream bedroom wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a linen headboard and white pillows. Soft diffused morning light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1014': {
        'listing_id': '4509213345',
        'art_file': f'{ART_DIR}/DP1014.jpg',
        'out_dir': f'{ART_DIR}/DP1014_listing_images',
        'frame_color': (30, 30, 30),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth white home office wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a light oak desk surface with a ceramic mug and a small succulent. Warm natural light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth warm cream living room wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, the back of a white linen sofa with one orange throw pillow. Bright natural daylight. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1015': {
        'listing_id': '4509213533',
        'art_file': f'{ART_DIR}/DP1015.jpg',
        'out_dir': f'{ART_DIR}/DP1015_listing_images',
        'frame_color': (180, 152, 92),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth dark charcoal bedroom wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a cream linen headboard and white pillows. Soft dramatic side lighting. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth deep black office wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a black desk with a gold lamp base. Warm ambient evening light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1016': {
        'listing_id': '4509213667',
        'art_file': f'{ART_DIR}/DP1016.jpg',
        'out_dir': f'{ART_DIR}/DP1016_listing_images',
        'frame_color': (82, 60, 40),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth warm ivory living room wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, the top of a cream linen sofa with an ivory throw pillow and a single white peony in a bud vase on a side table. Soft natural light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth pale greige bedroom wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a linen upholstered headboard with white and ivory pillows and a small fresh flower arrangement. Warm morning light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1017': {
        'listing_id': '4509259354',
        'art_file': f'{ART_DIR}/DP1017.jpg',
        'out_dir': f'{ART_DIR}/DP1017_listing_images',
        'frame_color': (30, 30, 30),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth pure white minimalist wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, the edge of a low grey linen sofa and a slim oak side table. Clean natural daylight. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth warm white bathroom wall with white subway tiles fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, the rim of a white freestanding bathtub and a small green plant. Soft diffused light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1018': {
        'listing_id': '4509218860',
        'art_file': f'{ART_DIR}/DP1018.jpg',
        'out_dir': f'{ART_DIR}/DP1018_listing_images',
        'frame_color': (140, 110, 72),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth warm greige Japandi wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a low natural oak bench with a single folded linen throw. Soft diffused natural light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth light grey Scandinavian wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a slim white console table with a single dried branch arrangement in a ceramic vase. Clean north light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1019': {
        'listing_id': '4509214051',
        'art_file': f'{ART_DIR}/DP1019.jpg',
        'out_dir': f'{ART_DIR}/DP1019_listing_images',
        'frame_color': (82, 60, 40),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth warm sand colored living room wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, the top of a linen sofa with a woven throw blanket and a small ceramic vase of dried wildflowers on a side table. Warm golden light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth warm honey-toned wooden wall in a cabin fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, the arm of a brown leather chair and a small wool blanket. Warm firelight from the side. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1020': {
        'listing_id': '4509214237',
        'art_file': f'{ART_DIR}/DP1020.jpg',
        'out_dir': f'{ART_DIR}/DP1020_listing_images',
        'frame_color': (140, 110, 72),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth white boho living room wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, the top of a white slipcovered sofa with coral and sage throw pillows. Bright cheerful natural light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth pale yellow bedroom wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, white bedding with a colorful floral throw blanket and a wood nightstand with a small flower vase. Bright morning light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1021': {
        'listing_id': '4509214477',
        'art_file': f'{ART_DIR}/DP1021.jpg',
        'out_dir': f'{ART_DIR}/DP1021_listing_images',
        'frame_color': (82, 60, 40),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth dark mahogany wood-paneled wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a dark wooden bar counter with a whiskey glass and a leather bar stool. Warm amber Edison bulb light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth deep green wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, the top of a dark velvet sofa arm and a brass side table with a glass. Warm evening ambient light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1022': {
        'listing_id': '4509219594',
        'art_file': f'{ART_DIR}/DP1022.jpg',
        'out_dir': f'{ART_DIR}/DP1022_listing_images',
        'frame_color': (60, 80, 120),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth deep navy blue bedroom wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a white linen headboard with white and navy pillows and a driftwood lamp on a white nightstand. Soft moody evening light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth midnight blue living room wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a navy velvet sofa arm with a brass side table and a candle. Moody ambient light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1023': {
        'listing_id': '4509214803',
        'art_file': f'{ART_DIR}/DP1023.jpg',
        'out_dir': f'{ART_DIR}/DP1023_listing_images',
        'frame_color': (180, 152, 92),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth dark concrete loft wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a black velvet sofa arm and a geometric brass side table with a single candle. Dramatic moody low-key lighting with a deep navy and orange color cast. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth deep charcoal studio wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a black drafting table edge and art supplies. Moody dramatic side lighting. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1024': {
        'listing_id': '4509219904',
        'art_file': f'{ART_DIR}/DP1024.jpg',
        'out_dir': f'{ART_DIR}/DP1024_listing_images',
        'frame_color': (30, 30, 30),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth dark grey concrete garage wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a polished concrete floor with a chrome car jack and a tool box. Dramatic low-key studio lighting. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth dark charcoal man cave wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a leather sectional sofa arm and a reclaimed wood side table with a drink. Warm accent lighting. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
    'DP1025': {
        'listing_id': '4509215145',
        'art_file': f'{ART_DIR}/DP1025.jpg',
        'out_dir': f'{ART_DIR}/DP1025_listing_images',
        'frame_color': (30, 30, 30),
        'prompts': [
            ('lifestyle_room_A.jpg', 'Interior room scene. A smooth mustard yellow maximalist living room wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, the top of a deep velvet sofa with colorful throw pillows. Warm vibrant natural light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
            ('lifestyle_room_B.jpg', 'Interior room scene. A smooth deep teal eclectic studio wall fills 70% of the image — completely bare, no art, no shelves, nothing on the wall. At the very bottom, a white shelf with colorful art supplies and a small sculpture. Bright natural light. Professional interior photography, DSLR 35mm lens, f/2.8. No text visible anywhere. Square format.'),
        ]
    },
}

results = {}

for pid, info in LISTINGS.items():
    listing_id = info['listing_id']
    art_file = info['art_file']
    out_dir = info['out_dir']
    frame_color = info['frame_color']
    os.makedirs(out_dir, exist_ok=True)

    print(f'\n{"="*55}')
    print(f'{pid} — listing {listing_id}')
    results[pid] = {'generated': 0, 'uploaded': 0, 'errors': []}

    # Refresh token before uploads for this product
    refresh_if_needed()

    # Step 1: Get current rank 6 and 7 image IDs
    try:
        rank_ids = get_rank_image_ids(listing_id)
        print(f'  Current rank 6={rank_ids.get(6)}, rank 7={rank_ids.get(7)}')
    except Exception as e:
        print(f'  WARNING: Could not fetch image IDs: {e}')
        rank_ids = {}

    # Step 2 & 3: For each photo (A=rank6, B=rank7)
    for rank_offset, (filename, prompt) in enumerate(info['prompts']):
        rank = 6 + rank_offset
        bg_path = os.path.join(out_dir, f'bg_{filename}')
        composite_path = os.path.join(out_dir, filename)

        # Generate room background
        if not os.path.exists(bg_path):
            print(f'  Generating room bg for rank {rank}...')
            try:
                gen_room_bg(prompt, bg_path)
                results[pid]['generated'] += 1
            except Exception as e:
                print(f'  ERROR generating rank {rank}: {e}')
                results[pid]['errors'].append(f'rank {rank} gen: {e}')
                continue
            time.sleep(3)
        else:
            print(f'  rank {rank} bg exists, skipping generation')
            results[pid]['generated'] += 1

        # Composite actual art onto room background
        if not os.path.exists(composite_path):
            print(f'  Compositing art onto room bg for rank {rank}...')
            try:
                composite_art_in_room(bg_path, art_file, composite_path, frame_color=frame_color)
            except Exception as e:
                print(f'  ERROR compositing rank {rank}: {e}')
                results[pid]['errors'].append(f'rank {rank} composite: {e}')
                continue
        else:
            print(f'  rank {rank} composite exists, skipping compositing')

        # Delete old image at this rank
        old_id = rank_ids.get(rank)
        if old_id:
            print(f'  Deleting old rank {rank} image {old_id}...')
            delete_image(listing_id, old_id)
            time.sleep(0.5)

        # Upload new composite
        print(f'  Uploading composite at rank {rank}...')
        for attempt in range(3):
            try:
                result = client.upload_listing_image(listing_id, composite_path, rank=rank)
                print(f'  OK rank {rank} uploaded: id={result.get("listing_image_id")}')
                results[pid]['uploaded'] += 1
                break
            except EtsyAPIError as e:
                if e.status == 401:
                    print(f'  401 — refreshing token...')
                    refresh_if_needed()
                elif e.status == 429:
                    print(f'  429 — waiting 15s...')
                    time.sleep(15)
                elif e.status == 500 and attempt < 2:
                    print(f'  500 — retrying after 5s...')
                    time.sleep(5)
                else:
                    print(f'  FAIL Upload failed: {e}')
                    results[pid]['errors'].append(f'rank {rank} upload: {e}')
                    break
        else:
            results[pid]['errors'].append(f'rank {rank} all retries failed')

        time.sleep(1.5)

# Final summary
print('\n\n' + '='*60)
print('RESULTS')
print('='*60)
for pid, r in results.items():
    ok = 'OK' if r['uploaded'] == 2 and not r['errors'] else 'FAIL'
    print(f'{ok} {pid}: generated={r["generated"]}/2  uploaded={r["uploaded"]}/2  errors={r["errors"] or "none"}')
