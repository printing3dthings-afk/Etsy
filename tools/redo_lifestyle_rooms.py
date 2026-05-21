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
from PIL import Image, ImageDraw, ImageFilter

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
        "size": "1024x1024", "quality": "medium", "output_format": "jpeg"
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


def composite(bg_path, art_path, out_path, fc):
    room = Image.open(bg_path).convert('RGB').resize((CANVAS, CANVAS), Image.LANCZOS)
    art = Image.open(art_path).convert('RGB')
    art_w = int(CANVAS * 0.28)          # 672px — was 34% (816px), now smaller
    art_h = int(art_w * art.height / art.width)
    art = art.resize((art_w, art_h), Image.LANCZOS)
    mat_w, frame_w = 32, 12
    full_w = art_w + 2*mat_w + 2*frame_w
    full_h = art_h + 2*mat_w + 2*frame_w
    px = (CANVAS - full_w) // 2
    py = int(CANVAS * 0.15)             # 360px from top — was 10% (240px)
    frame_bottom_pct = (py + full_h) / CANVAS * 100
    print(f"  frame: {full_w}x{full_h}, bottom={py+full_h}px ({frame_bottom_pct:.1f}%)")
    # Drop shadow
    shadow = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle(
        [px+12, py+16, px+full_w+12, py+full_h+16], fill=(0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=18))
    room = Image.alpha_composite(room.convert('RGBA'), shadow).convert('RGB')
    draw = ImageDraw.Draw(room)
    draw.rectangle([px, py, px+full_w, py+full_h], fill=fc)
    mx, my = px+frame_w, py+frame_w
    draw.rectangle([mx, my, mx+art_w+2*mat_w, my+art_h+2*mat_w], fill=(252, 250, 247))
    room.paste(art, (mx+mat_w, my+mat_w))
    room.save(out_path, 'JPEG', quality=92)
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


LISTINGS = {
    'DP1007': {
        'listing_id': '4509218152',
        'art_file': f'{ART_DIR}/DP1007.jpg',
        'out_dir': f'{ART_DIR}/DP1007_listing_images',
        'frame_color': (70, 45, 20),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth warm ivory plaster wall — the wall fills 80% of the image completely bare. Just the top sliver of a rustic wooden console table with a small ceramic lemon bowl peeks in at the very bottom of the frame. Soft warm Mediterranean light. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth whitewashed wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top rim of a slim wooden console table with a tiny ceramic vase. Coastal natural light. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1012': {
        'listing_id': '4509258172',
        'art_file': f'{ART_DIR}/DP1012.jpg',
        'out_dir': f'{ART_DIR}/DP1012_listing_images',
        'frame_color': (30, 30, 30),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth dusty pink painted wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top cushion of a mustard velvet sofa with one rattan side table leg visible. Warm natural light. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth sage green painted wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a slim white floating shelf with a tiny green plant. Bright daylight. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1013': {
        'listing_id': '4509258700',
        'art_file': f'{ART_DIR}/DP1013.jpg',
        'out_dir': f'{ART_DIR}/DP1013_listing_images',
        'frame_color': (140, 110, 72),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth pale sage nursery wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top rail of a white wooden crib barely visible. Soft gentle morning light. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth warm cream bedroom wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a linen headboard barely visible. Soft diffused morning light. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1014': {
        'listing_id': '4509213345',
        'art_file': f'{ART_DIR}/DP1014.jpg',
        'out_dir': f'{ART_DIR}/DP1014_listing_images',
        'frame_color': (30, 30, 30),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth white home office wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top surface of a light oak desk with a ceramic mug. Warm natural light. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth warm cream living room wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top backrest of a white linen sofa. Bright natural daylight. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1015': {
        'listing_id': '4509213533',
        'art_file': f'{ART_DIR}/DP1015.jpg',
        'out_dir': f'{ART_DIR}/DP1015_listing_images',
        'frame_color': (180, 152, 92),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth dark charcoal bedroom wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a cream linen headboard barely peeking in. Soft dramatic side lighting. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth deep charcoal office wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the edge of a black desk surface with a gold lamp base. Warm evening light. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1016': {
        'listing_id': '4509213667',
        'art_file': f'{ART_DIR}/DP1016.jpg',
        'out_dir': f'{ART_DIR}/DP1016_listing_images',
        'frame_color': (82, 60, 40),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth warm ivory living room wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a cream sofa backrest with one ivory pillow visible. Soft natural light. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth pale greige bedroom wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a linen headboard with white pillows barely visible. Warm morning light. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1017': {
        'listing_id': '4509259354',
        'art_file': f'{ART_DIR}/DP1017.jpg',
        'out_dir': f'{ART_DIR}/DP1017_listing_images',
        'frame_color': (30, 30, 30),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth pure white minimalist wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top backrest of a low grey linen sofa barely visible. Clean natural daylight. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth warm white bathroom wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the rim of a white freestanding bathtub just visible. Soft diffused light. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1018': {
        'listing_id': '4509218860',
        'art_file': f'{ART_DIR}/DP1018.jpg',
        'out_dir': f'{ART_DIR}/DP1018_listing_images',
        'frame_color': (140, 110, 72),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth warm greige Japandi wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top surface of a low natural oak bench with a folded linen throw. Soft diffused light. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth light grey Scandinavian wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the surface of a slim white console table with a tiny dried flower arrangement. Clean north light. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1019': {
        'listing_id': '4509214051',
        'art_file': f'{ART_DIR}/DP1019.jpg',
        'out_dir': f'{ART_DIR}/DP1019_listing_images',
        'frame_color': (82, 60, 40),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth warm sand colored living room wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a linen sofa backrest with a woven throw. Warm golden light. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth warm honey-toned wooden cabin wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the arm of a brown leather chair barely visible. Warm firelight from the side. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1020': {
        'listing_id': '4509214237',
        'art_file': f'{ART_DIR}/DP1020.jpg',
        'out_dir': f'{ART_DIR}/DP1020_listing_images',
        'frame_color': (140, 110, 72),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth white boho living room wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a white slipcovered sofa with one coral pillow barely visible. Bright cheerful natural light. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth pale yellow bedroom wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top edge of white bedding with a colorful floral throw just visible. Bright morning light. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1021': {
        'listing_id': '4509214477',
        'art_file': f'{ART_DIR}/DP1021.jpg',
        'out_dir': f'{ART_DIR}/DP1021_listing_images',
        'frame_color': (82, 60, 40),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth dark mahogany wood-paneled wall — the wall fills 80% of the image completely bare. At the very bottom edge only: a dark wooden bar counter top barely visible with a whiskey glass. Warm amber Edison bulb light from the side. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth deep forest green wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a dark velvet sofa arm barely visible. Warm evening ambient light. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1022': {
        'listing_id': '4509219594',
        'art_file': f'{ART_DIR}/DP1022.jpg',
        'out_dir': f'{ART_DIR}/DP1022_listing_images',
        'frame_color': (60, 80, 120),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth deep navy blue wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a white linen headboard with white pillows barely peeking in. Soft moody evening light with a warm lamp glow from the side. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth midnight blue living room wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a navy velvet sofa backrest barely visible. Moody ambient light. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1023': {
        'listing_id': '4509214803',
        'art_file': f'{ART_DIR}/DP1023.jpg',
        'out_dir': f'{ART_DIR}/DP1023_listing_images',
        'frame_color': (180, 152, 92),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth dark concrete loft wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top cushion of a black velvet sofa barely visible. Dramatic moody low-key lighting. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth deep charcoal studio wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top edge of a black drafting table surface barely visible. Moody dramatic side lighting. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1024': {
        'listing_id': '4509219904',
        'art_file': f'{ART_DIR}/DP1024.jpg',
        'out_dir': f'{ART_DIR}/DP1024_listing_images',
        'frame_color': (30, 30, 30),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth dark grey concrete garage wall — the wall fills 80% of the image completely bare. At the very bottom edge only: a polished concrete floor surface with the corner of a red metal toolbox barely visible. Dramatic low-key studio lighting. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth dark charcoal man cave wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a leather sectional sofa backrest barely visible. Warm accent lighting. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
    'DP1025': {
        'listing_id': '4509215145',
        'art_file': f'{ART_DIR}/DP1025.jpg',
        'out_dir': f'{ART_DIR}/DP1025_listing_images',
        'frame_color': (30, 30, 30),
        'prompts': [
            ('bg_lifestyle_room_A.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth mustard yellow living room wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a deep teal velvet sofa with one colorful throw pillow barely visible. Warm vibrant natural light. Professional DSLR, f/2.8. Square format. No text.'),
            ('bg_lifestyle_room_B.jpg',
             'Minimalist interior photography. Camera looking slightly upward at a smooth deep teal studio wall — the wall fills 80% of the image completely bare. At the very bottom edge only: the top of a white shelf surface barely visible. Bright natural light. Professional DSLR, f/2.8. Square format. No text.'),
        ]
    },
}

# === TEST FIRST: DP1022 A ===
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-only', action='store_true', help='Only run the test for DP1022')
    parser.add_argument('--full-run', action='store_true', help='Run the full loop for all listings')
    args = parser.parse_args()

    if args.test_only:
        info = LISTINGS['DP1022']
        test_bg = os.path.join(info['out_dir'], info['prompts'][0][0])
        test_comp = os.path.join(info['out_dir'], 'lifestyle_room_A.jpg')

        os.makedirs(info['out_dir'], exist_ok=True)
        print("Generating test room background (DP1022 A)...")
        gen_room_bg(info['prompts'][0][1], test_bg)
        print("Compositing test...")
        composite(test_bg, info['art_file'], test_comp, info['frame_color'])
        print(f"TEST DONE — composite at: {test_comp}")

    elif args.full_run:
        results = {}
        for pid, info in LISTINGS.items():
            lid = info['listing_id']
            out_dir = info['out_dir']
            os.makedirs(out_dir, exist_ok=True)
            print(f'\n{"="*55}\n{pid} — {lid}')
            results[pid] = {'generated': 0, 'uploaded': 0, 'errors': []}
            refresh()

            # Generate new room backgrounds (overwrite old ones)
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

            # Get current rank 6/7 IDs, delete, upload new
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

        print('\n\n' + '='*60)
        print('FINAL RESULTS')
        print('='*60)
        for pid, r in results.items():
            ok = 'OK' if r['uploaded'] == 2 and not r['errors'] else 'FAIL'
            print(f'{ok} {pid}: generated={r["generated"]}/2  uploaded={r["uploaded"]}/2  errors={r["errors"] or "none"}')
    else:
        print("Use --test-only or --full-run")
