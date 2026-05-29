#!/usr/bin/env python3
"""
Regenerate bare-wall backgrounds for specific products that have
either full-scene bgs or furniture placed too high.

Targets:
  DP1025-A and B  — full scene bgs (std>55), need bare wall
  DP1032-B        — furniture too high in existing bg
  DP1036-B        — furniture too high in existing bg
"""

import os, sys, json, base64, urllib.request, time
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.lifestyle_composite import composite_smart, scene_prompt, qc_check
from tools.etsy_api import EtsyAPIClient, EtsyAPIError

ART_DIR = '/home/user/Etsy/data/digital_products/product_files'
OPENAI_KEY = os.environ['OPENAI_API_KEY']

FRAME_COLORS = {
    'DP1025': ( 80,  60,  40),
    'DP1032': ( 80,  55,  40),
    'DP1036': ( 55,  55,  55),
}

LISTING_IDS = {
    'DP1025': 4509215145,
    'DP1032': 4509593487,
    'DP1036': 4509596017,
}

RANKS = {
    'DP1025': {'A': 6, 'B': 7},
    'DP1032': {'A': 1, 'B': 2},
    'DP1036': {'A': 1, 'B': 2},
}

# Bare-wall background prompts for each scene
BG_PROMPTS = {
    'DP1025': {
        'A': scene_prompt(
            room_desc="Bohemian living room",
            wall_color="warm terracotta orange limewash plaster wall",
            furniture_desc="a colorful Oaxacan-textile-covered bench with vibrant cushions and a tall woven basket in lower-right corner",
            lighting="warm ambient Boho accent light from left",
            style="bold, cultural, festive Boho Mexican folk art home",
        ),
        'B': scene_prompt(
            room_desc="colorful eclectic entry nook or hallway",
            wall_color="deep teal painted smooth wall",
            furniture_desc="a slim painted wood console table in deep blue with a clay bowl and two mismatched pillar candles",
            lighting="warm lamp glow from lower left, ambient ceiling light",
            style="festive and bold Día de los Muertos folk art aesthetic",
        ),
    },
    'DP1032': {
        'B': scene_prompt(
            room_desc="bright Scandinavian living room",
            wall_color="warm white smooth plaster wall",
            furniture_desc="a slim honey oak console table with a small potted maidenhair fern, ceramic apothecary jar, and short stack of botanical art books",
            lighting="soft bright natural daylight from left window",
            style="fresh, intellectual, botanical art Scandinavian home aesthetic",
        ),
    },
    'DP1036': {
        'B': scene_prompt(
            room_desc="bright creative art studio corner",
            wall_color="warm white smooth painted wall",
            furniture_desc="a slim marble-top console with a white ceramic figure sculpture, glass vase of dried white craspedia, and paint-stained linen cloth",
            lighting="bright diffused natural studio light from left",
            style="artistic, clean, modern artist's home studio aesthetic",
        ),
    },
}


def gen_bg(prompt, out_path):
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


def upload_image(client, listing_id, img_path, rank):
    headers = {
        "Authorization": f"Bearer {client.access_token}",
        "x-api-key": f"{client.client_id}:{client.client_secret}",
    }
    shop_id = client.shop_id
    url = f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            imgs = json.loads(resp.read()).get('results', [])
        existing = {img['rank']: img['listing_image_id'] for img in imgs}
    except Exception:
        existing = {}

    if rank in existing:
        url_del = (f"https://openapi.etsy.com/v3/application/shops/{shop_id}"
                   f"/listings/{listing_id}/images/{existing[rank]}")
        try:
            urllib.request.urlopen(
                urllib.request.Request(url_del, headers=headers, method="DELETE"), timeout=15)
            print(f"    Deleted old rank={rank}")
            time.sleep(0.5)
        except Exception as e:
            print(f"    Could not delete: {e}")

    for attempt in range(3):
        try:
            client.upload_listing_image(listing_id, img_path, rank=rank)
            print(f"    Uploaded rank={rank}: {os.path.basename(img_path)}")
            return True
        except EtsyAPIError as e:
            if e.status == 401:
                client.refresh_access_token()
            elif e.status == 429:
                time.sleep(15)
            elif e.status == 500 and attempt < 2:
                time.sleep(5)
            else:
                print(f"    Upload failed: {e}")
                return False
    return False


def main():
    client = EtsyAPIClient()
    client.refresh_access_token()

    jobs = [
        ('DP1025', 'A'),
        ('DP1025', 'B'),
        ('DP1032', 'B'),
        ('DP1036', 'B'),
    ]

    results = []
    for pid, scene in jobs:
        out_dir  = os.path.join(ART_DIR, f'{pid}_listing_images')
        art_path = os.path.join(ART_DIR, f'{pid}.jpg')
        bg_path  = os.path.join(out_dir, f'bg_lifestyle_room_{scene}.jpg')
        out_path = os.path.join(out_dir, f'lifestyle_room_{scene}.jpg')
        rank     = RANKS[pid][scene]
        listing_id = LISTING_IDS[pid]
        prompt   = BG_PROMPTS[pid][scene]

        print(f"\n{'='*60}")
        print(f"  {pid}-{scene}  →  listing={listing_id}  rank={rank}")
        print(f"{'='*60}")

        # Generate new bare-wall background
        print(f"  Generating bg_lifestyle_room_{scene}.jpg ...")
        if not gen_bg(prompt, bg_path):
            print(f"  SKIP {pid}-{scene}: background generation failed")
            results.append((pid, scene, 'bg_gen_failed'))
            continue
        time.sleep(3)

        # Composite real art onto new background
        frame_color = FRAME_COLORS.get(pid, (139, 110, 80))
        ok, furniture_y, frame_bottom = composite_smart(
            bg_path, art_path, out_path,
            frame_color=frame_color,
            art_pct=0.25,
            min_clearance=60,
        )
        if not ok:
            print(f"  Composite failed")
            results.append((pid, scene, 'composite_failed'))
            continue

        print(f"  Composited: furniture_y={furniture_y}  frame_bottom={frame_bottom}")
        pass_qc, reason = qc_check(out_path, 0, frame_bottom, clearance_min=40)
        if not pass_qc:
            print(f"  QC note: {reason}")

        # Upload
        ok = upload_image(client, listing_id, out_path, rank)
        results.append((pid, scene, 'uploaded' if ok else 'upload_failed'))
        time.sleep(1)

    print(f"\n{'='*60}")
    print("REGEN COMPLETE")
    print(f"{'='*60}")
    for pid, scene, status in results:
        icon = '✓' if status == 'uploaded' else '✗'
        print(f"  {icon} {pid}-{scene}: {status}")


if __name__ == '__main__':
    main()
