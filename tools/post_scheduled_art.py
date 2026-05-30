#!/usr/bin/env python3
"""
Scheduled art poster — generates and publishes one new wall art listing to Etsy
every other day, cycling through 20 art categories in order.

State file: data/art_schedule.json
  - queue_position  : index of the next category to post
  - next_post_date  : ISO date string of the next scheduled post
  - post_history    : log of every post made
  - categories      : 20 ordered categories, each with subjects list

Usage:
  python tools/post_scheduled_art.py            # run if due today
  python tools/post_scheduled_art.py --force    # post now regardless of schedule
  python tools/post_scheduled_art.py --preview  # generate images only, no Etsy post
  python tools/post_scheduled_art.py --status   # show queue and next post date
  python tools/post_scheduled_art.py --list     # show full category rotation

Add to crontab (runs at 10am every other day):
  0 10 */2 * * cd /home/user/Etsy && python tools/post_scheduled_art.py >> logs/art_schedule.log 2>&1
"""

import os
import sys
import json
import time
import base64
import argparse
import datetime
import urllib.request
import urllib.error

sys.path.insert(0, '/home/user/Etsy')

# Load .env manually — never use load_dotenv
_env = {}
with open('/home/user/Etsy/.env') as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            _env[_k.strip()] = _v.strip()

for k, v in _env.items():
    os.environ.setdefault(k, v)

from PIL import Image, ImageFilter, ImageEnhance
from tools.etsy_api import EtsyAPIClient, EtsyAPIError

# ── Paths ─────────────────────────────────────────────────────────────────────
SCHEDULE_PATH  = '/home/user/Etsy/data/art_schedule.json'
ART_DIR        = '/home/user/Etsy/data/digital_products/product_files'
LOG_DIR        = '/home/user/Etsy/logs'
OPENAI_KEY     = os.environ.get('OPENAI_API_KEY', '')

os.makedirs(LOG_DIR, exist_ok=True)

# ── Room compositing helpers (from create_art_listing_new.py) ─────────────────
ROOM_BOUNDS = {
    'living_room':    (409, 164, 614, 464),
    'kitchen_dining': (400, 166, 624, 494),
    'entryway':       (430, 147, 593, 365),
}
ROOM_TEMPLATES = {
    'living_room':    f'{ART_DIR}/DP1007_room_living_room_natural_wood.jpg',
    'kitchen_dining': f'{ART_DIR}/DP1007_room_kitchen_dining_natural_wood.jpg',
    'entryway':       f'{ART_DIR}/DP1007_room_entryway_natural_wood.jpg',
}


# ── Schedule I/O ──────────────────────────────────────────────────────────────

def load_schedule():
    with open(SCHEDULE_PATH) as f:
        return json.load(f)


def save_schedule(schedule):
    with open(SCHEDULE_PATH, 'w') as f:
        json.dump(schedule, f, indent=2)


# ── Image generation ──────────────────────────────────────────────────────────

def gen_image(prompt, out_path, size="1024x1536", quality="high"):
    payload = json.dumps({
        "model": "gpt-image-1", "prompt": prompt.strip(), "n": 1,
        "size": size, "quality": quality, "output_format": "jpeg"
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
            return True
        except Exception as e:
            print(f"  Gen attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
    return False


# ── Room compositing ──────────────────────────────────────────────────────────

def composite_into_ai_room(bg_path, art_path, out_path,
                            frame_color=(139, 110, 80), min_clearance=80):
    """Composite art into a generated AI room background with auto-scaling."""
    bg = Image.open(bg_path).convert('RGB').resize((2400, 2400), Image.LANCZOS)
    art = Image.open(art_path).convert('RGB')

    # Find a reasonable wall area (upper-center 60%)
    W, H = bg.size
    wall_left   = int(W * 0.15)
    wall_right  = int(W * 0.85)
    wall_top    = int(H * 0.05)
    wall_bottom = int(H * 0.62)

    wall_w = wall_right - wall_left
    wall_h = wall_bottom - wall_top

    art_w, art_h = art.size
    scale = min((wall_w - min_clearance * 2) / art_w,
                (wall_h - min_clearance * 2) / art_h, 0.55)
    new_w = int(art_w * scale)
    new_h = int(art_h * scale)

    art_resized = art.resize((new_w, new_h), Image.LANCZOS)

    # Add white mat
    mat_px = max(12, int(min(new_w, new_h) * 0.06))
    matted_w = new_w + mat_px * 2
    matted_h = new_h + mat_px * 2
    matted = Image.new('RGB', (matted_w, matted_h), (250, 248, 244))
    matted.paste(art_resized, (mat_px, mat_px))

    # Add thin frame
    frame_px = max(4, int(min(new_w, new_h) * 0.02))
    framed_w = matted_w + frame_px * 2
    framed_h = matted_h + frame_px * 2
    framed = Image.new('RGB', (framed_w, framed_h), frame_color)
    framed.paste(matted, (frame_px, frame_px))

    # Center on wall
    paste_x = wall_left + (wall_w - framed_w) // 2
    paste_y = wall_top  + int((wall_h - framed_h) * 0.35)

    bg.paste(framed, (paste_x, paste_y))
    bg.save(out_path, 'JPEG', quality=90)
    return True


def composite_room_template(art_path, room_key, out_path):
    """Composite art into one of the fixed room template photos."""
    if not os.path.exists(ROOM_TEMPLATES[room_key]):
        return False
    bg = Image.open(ROOM_TEMPLATES[room_key]).convert('RGB')
    art = Image.open(art_path).convert('RGB')
    l, t, r, b = ROOM_BOUNDS[room_key]
    art_resized = art.resize((r - l, b - t), Image.LANCZOS)
    bg.paste(art_resized, (l, t))
    bg = bg.resize((2400, 2400), Image.LANCZOS)
    bg.save(out_path, 'JPEG', quality=90)
    return True


# ── Etsy helpers ──────────────────────────────────────────────────────────────

def get_or_create_section(client, section_title):
    try:
        sections = client._request('GET', f'/shops/{client.shop_id}/sections').get('results', [])
        for s in sections:
            if s.get('title', '').lower() == section_title.lower():
                return s['shop_section_id']
        new_sec = client._request('POST', f'/shops/{client.shop_id}/sections',
                                  json={'title': section_title})
        return new_sec.get('shop_section_id')
    except Exception as e:
        print(f"  WARNING: section lookup failed: {e}")
        return None


def upload_image_raw(client, listing_id, img_path, rank):
    import requests
    import urllib3
    urllib3.disable_warnings()

    url = f"https://api.etsy.com/v3/application/shops/{client.shop_id}/listings/{listing_id}/images"
    headers = {
        "Authorization": f"Bearer {client.access_token}",
        "x-api-key": f"{client.client_id}:{client.client_secret}"
    }
    with open(img_path, 'rb') as f:
        files = {'image': (os.path.basename(img_path), f, 'image/jpeg')}
        data = {'rank': rank}
        resp = requests.post(url, headers=headers, files=files, data=data, verify=False)
    if resp.status_code in (200, 201):
        return True
    print(f"    Image upload failed rank={rank}: {resp.status_code} {resp.text[:120]}")
    return False


def upload_file_raw(client, listing_id, file_path):
    import requests
    import urllib3
    urllib3.disable_warnings()

    url = f"https://api.etsy.com/v3/application/shops/{client.shop_id}/listings/{listing_id}/files"
    headers = {
        "Authorization": f"Bearer {client.access_token}",
        "x-api-key": f"{client.client_id}:{client.client_secret}"
    }
    with open(file_path, 'rb') as f:
        mime = 'image/jpeg' if file_path.lower().endswith('.jpg') else 'application/zip'
        files = {'file': (os.path.basename(file_path), f, mime)}
        data = {'name': os.path.basename(file_path), 'rank': 1}
        resp = requests.post(url, headers=headers, files=files, data=data, verify=False)
    return resp.status_code in (200, 201)


# ── Description builder ───────────────────────────────────────────────────────

DESCRIPTION_TEMPLATE = """\
{hook}

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ High-resolution JPG at 300 DPI — professional print quality
✅ 8 print sizes in one download: 4×6, 5×7, 8×10, 11×14, 16×20, 18×24, 24×30, 24×36 inches
✅ sRGB color profile — accurate color on every home printer and print lab
✅ Instant download — files available immediately after purchase

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ PERFECT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• {room_context}
• Gallery wall groupings — pairs beautifully with other pieces from our shop
• Housewarming, birthday, and holiday gifts — instant, no shipping wait
• Anyone who loves beautiful affordable art for their home

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase and download your files instantly from Etsy
2. Choose your preferred size (8 sizes included)
3. Print at home, or at Costco, Walgreens, Staples, or any local print shop
4. Frame it and hang — done!

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 PRINTING TIPS
━━━━━━━━━━━━━━━━━━━━━━━━
• Matte or satin paper gives the best finish for {description_niche} art
• 11×14 or 16×20 shows the detail beautifully
• Natural wood, black, or white frames all complement this style perfectly

━━━━━━━━━━━━━━━━━━━━━━━━
📄 FILE DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: High-resolution JPG
• Resolution: 300 DPI (professional print quality)
• Sizes included: 4×6, 5×7, 8×10, 11×14, 16×20, 18×24, 24×30, 24×36 inches
• Color profile: sRGB

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Is this a physical item?
A: No — this is a digital download only. You receive image files to print yourself.

Q: Can I resize the files?
A: Yes! 300 DPI files scale beautifully. Resize in Canva, Photoshop, or any image editor.

Q: Can I print multiple copies for my own home?
A: Yes — personal use means printing for yourself, family, or as a gift.

Q: What paper should I use?
A: Matte or satin photo paper gives the most beautiful finish.

Q: Can I use this commercially?
A: This is a personal use license only. Contact us for commercial licensing options.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use."""


def build_description(subject, category):
    hook = (
        f"Instant download printable wall art — add {subject.lower()} to your home today, "
        f"delivered immediately after purchase, ready to print at home or at any print shop.\n\n"
        f"This {category['description_niche']} print brings timeless beauty to your space. "
        f"Download, print, frame — it's that simple."
    )
    return DESCRIPTION_TEMPLATE.format(
        hook=hook,
        room_context=category['room_context'],
        description_niche=category['description_niche']
    )


# ── Size guide and What's Included graphics ───────────────────────────────────

def create_size_guide(art_path, out_path):
    W, H = 2400, 2400
    canvas = Image.new('RGB', (W, H), (245, 241, 235))
    art = Image.open(art_path).convert('RGB')
    # Paste art at 40% size centered top
    scale = 0.38
    aw = int(art.width * scale)
    ah = int(art.height * scale)
    if ah > 900:
        ah = 900
        aw = int(art.width * ah / art.height)
    art_small = art.resize((aw, ah), Image.LANCZOS)
    canvas.paste(art_small, ((W - aw) // 2, 120))
    canvas.save(out_path, 'JPEG', quality=88)


def create_whats_included(art_path, out_path, title, price):
    W, H = 2400, 2400
    canvas = Image.new('RGB', (W, H), (245, 241, 235))
    art = Image.open(art_path).convert('RGB')
    scale = 0.32
    aw = int(art.width * scale)
    ah = int(art.height * scale)
    art_small = art.resize((aw, ah), Image.LANCZOS)
    canvas.paste(art_small, ((W - aw) // 2, 80))
    canvas.save(out_path, 'JPEG', quality=88)


# ── Core: pick next subject ───────────────────────────────────────────────────

def pick_subject(category):
    """Return next unused subject for the category, cycling when all used."""
    used = set(category.get('subjects_used', []))
    available = [s for s in category['subjects'] if s not in used]
    if not available:
        # All subjects used — reset and start over
        category['subjects_used'] = []
        available = category['subjects']
    subject = available[0]
    category['subjects_used'].append(subject)
    return subject


# ── Main pipeline ─────────────────────────────────────────────────────────────

def post_art(preview_only=False):
    schedule = load_schedule()
    categories = schedule['categories']
    pos = schedule['queue_position'] % len(categories)
    category = categories[pos]

    subject = pick_subject(category)
    subject_lower = subject.lower()

    print(f"\n{'='*60}")
    print(f"Category [{pos+1}/{len(categories)}]: {category['label']}")
    print(f"Subject: {subject}")
    print(f"{'='*60}")

    # Build product ID: SCHED_YYYYMMDD
    today_str = datetime.date.today().strftime('%Y%m%d')
    pid = f"SCHED_{today_str}_{category['id'][:8].upper()}"
    out_dir = os.path.join(ART_DIR, f'{pid}_listing_images')
    os.makedirs(out_dir, exist_ok=True)
    art_path = os.path.join(ART_DIR, f'{pid}.jpg')

    # ── Step 1: Generate art ──────────────────────────────────────────────────
    print(f"\n[1/7] Generating art...")
    art_prompt = category['art_prompt_template'].replace('{subject_lower}', subject_lower).replace('{subject}', subject)
    if not os.path.exists(art_path):
        ok = gen_image(art_prompt, art_path, size="1024x1536", quality="high")
        if not ok:
            print("  FAILED to generate art. Aborting.")
            return None
        time.sleep(3)
    else:
        print(f"  Art exists: {art_path}")

    # ── Step 2: Lifestyle scene A ─────────────────────────────────────────────
    print(f"\n[2/7] Generating lifestyle scene A...")
    bg_a = os.path.join(out_dir, 'bg_scene_A.jpg')
    scene_a = os.path.join(out_dir, 'scene_A.jpg')
    if not os.path.exists(bg_a):
        ok = gen_image(category['scene_a_prompt'], bg_a, size="1024x1024", quality="high")
        if not ok:
            print("  WARNING: scene A failed")
        time.sleep(3)
    if os.path.exists(bg_a):
        composite_into_ai_room(bg_a, art_path, scene_a,
                               frame_color=tuple(category.get('frame_color', [139, 110, 80])))
    else:
        print("  Skipping scene A composite")

    # ── Step 3: Lifestyle scene B ─────────────────────────────────────────────
    print(f"\n[3/7] Generating lifestyle scene B...")
    bg_b = os.path.join(out_dir, 'bg_scene_B.jpg')
    scene_b = os.path.join(out_dir, 'scene_B.jpg')
    if not os.path.exists(bg_b):
        ok = gen_image(category['scene_b_prompt'], bg_b, size="1024x1024", quality="high")
        if not ok:
            print("  WARNING: scene B failed")
        time.sleep(3)
    if os.path.exists(bg_b):
        composite_into_ai_room(bg_b, art_path, scene_b,
                               frame_color=tuple(category.get('frame_color', [139, 110, 80])))
    else:
        print("  Skipping scene B composite")

    # ── Step 4: Room template composites ─────────────────────────────────────
    print(f"\n[4/7] Creating room template composites...")
    room_outputs = {}
    for room_key in ['living_room', 'kitchen_dining', 'entryway']:
        out = os.path.join(out_dir, f'room_{room_key}.jpg')
        if composite_room_template(art_path, room_key, out):
            room_outputs[room_key] = out
            print(f"  ✓ {room_key}")
        else:
            print(f"  ✗ {room_key} template missing")

    # ── Step 5: Size guide ────────────────────────────────────────────────────
    print(f"\n[5/7] Creating size guide...")
    size_guide = os.path.join(out_dir, 'size_guide.jpg')
    create_size_guide(art_path, size_guide)

    # ── Step 6: What's included ───────────────────────────────────────────────
    print(f"\n[6/7] Creating What's Included card...")
    whats_included = os.path.join(out_dir, 'whats_included.jpg')
    create_whats_included(art_path, whats_included, subject, category['price'])

    # ── Print summary ─────────────────────────────────────────────────────────
    all_photos = [
        ('Hero (scene A)',    scene_a),
        ('Scene B',          scene_b),
        ('Room: Living',     room_outputs.get('living_room', '')),
        ('Room: Kitchen',    room_outputs.get('kitchen_dining', '')),
        ('Room: Entryway',   room_outputs.get('entryway', '')),
        ('Size guide',       size_guide),
        ("What's included",  whats_included),
        ('Raw art',          art_path),
    ]
    print(f"\n{'─'*60}")
    print(f"Generated files:")
    for label, path in all_photos:
        exists = '✓' if path and os.path.exists(path) else '✗ MISSING'
        kb = os.path.getsize(path)//1024 if path and os.path.exists(path) else 0
        print(f"  {exists} {label}: {kb}KB")

    if preview_only:
        print(f"\n[PREVIEW] Images saved to {out_dir}")
        print("[PREVIEW] Run with --force to post to Etsy.")
        return {'pid': pid, 'out_dir': out_dir}

    # ── Step 7: Post to Etsy ──────────────────────────────────────────────────
    print(f"\n[7/7] Posting to Etsy...")
    client = EtsyAPIClient()

    # Build title — enforce ≤70 chars (2026 algorithm rule)
    title_raw = category['title_template'].replace('{subject}', subject)
    title = title_raw[:70].rstrip(',').rstrip()
    if len(title) < len(title_raw):
        print(f"  Title trimmed to 70 chars: {title!r}")

    description = build_description(subject, category)
    tags = category['tags'][:13]

    # Validate tags
    for tag in tags:
        if len(tag) > 20:
            print(f"  WARNING: tag too long ({len(tag)} chars): {tag!r}")

    section_id = get_or_create_section(client, 'Wall Art Prints')

    listing_body = {
        "quantity": 999,
        "title": title,
        "description": description,
        "price": category['price'],
        "who_made": "i_did",
        "taxonomy_id": 2078,
        "when_made": "made_to_order",
        "type": "download",
        "state": "draft",
        "tags": tags,
        "is_supply": False,
        "is_customizable": False,
        "should_auto_renew": True,
    }
    if section_id:
        listing_body["shop_section_id"] = section_id

    try:
        listing = client._request('POST', f'/shops/{client.shop_id}/listings',
                                  json=listing_body)
    except Exception as e:
        print(f"  FAILED to create listing: {e}")
        return None

    lid = listing.get('listing_id')
    if not lid:
        print(f"  FAILED: no listing_id returned")
        return None
    print(f"  Created listing_id={lid}")
    time.sleep(1)

    # Upload images
    image_slots = [
        (scene_a, 1), (scene_b, 2),
        (room_outputs.get('living_room', ''), 3),
        (room_outputs.get('kitchen_dining', ''), 4),
        (room_outputs.get('entryway', ''), 5),
        (size_guide, 6), (whats_included, 7), (art_path, 8),
    ]
    uploaded = 0
    for img_path, rank in image_slots:
        if img_path and os.path.exists(img_path):
            if upload_image_raw(client, lid, img_path, rank):
                uploaded += 1
            time.sleep(0.8)

    print(f"  Uploaded {uploaded} images")
    time.sleep(1)

    # Upload art file as digital download
    upload_file_raw(client, lid, art_path)

    # Activate
    try:
        result = client._request('PATCH', f'/listings/{lid}', json={"state": "active"})
        state = result.get('state', 'unknown')
        if state == 'active':
            print(f"  ✓ LIVE: https://www.etsy.com/listing/{lid}/")
        else:
            print(f"  State: {state} — may need manual activation")
    except Exception as e:
        print(f"  Activation error: {e}")

    # ── Advance the schedule ──────────────────────────────────────────────────
    schedule['last_posted_date'] = today_str
    next_date = (datetime.date.today() +
                 datetime.timedelta(days=schedule['interval_days'])).isoformat()
    schedule['next_post_date'] = next_date
    schedule['queue_position'] = (pos + 1) % len(categories)
    schedule.setdefault('post_history', []).append({
        'date': today_str,
        'category_id': category['id'],
        'category_label': category['label'],
        'subject': subject,
        'listing_id': lid,
        'title': title,
        'pid': pid
    })

    # Update subjects_used in the saved schedule
    schedule['categories'][pos] = category
    save_schedule(schedule)

    print(f"\n  Schedule advanced → next post: {next_date}")
    print(f"  Next category: {categories[(pos+1) % len(categories)]['label']}")

    return {'pid': pid, 'listing_id': lid, 'uploaded': uploaded}


# ── Status display ────────────────────────────────────────────────────────────

def show_status():
    schedule = load_schedule()
    categories = schedule['categories']
    pos = schedule['queue_position'] % len(categories)
    cat = categories[pos]
    used_subjects = cat.get('subjects_used', [])
    remaining = [s for s in cat['subjects'] if s not in set(used_subjects)]

    print(f"\n{'='*60}")
    print(f"Art Posting Schedule — OnBrandCraftz")
    print(f"{'='*60}")
    print(f"Interval:        every {schedule['interval_days']} days")
    print(f"Last posted:     {schedule.get('last_posted_date', 'never')}")
    print(f"Next post:       {schedule.get('next_post_date', 'unset')}")
    print(f"Queue position:  {pos+1} of {len(categories)}")
    print(f"\nUp next:         [{cat['id']}] {cat['label']}")
    print(f"  Next subject:  {remaining[0] if remaining else cat['subjects'][0] + ' (reset)'}")
    print(f"  Price:         ${cat['price']:.2f}")
    print(f"\nPost history ({len(schedule.get('post_history', []))}):")
    for h in schedule.get('post_history', [])[-5:]:
        print(f"  {h['date']}  [{h['category_label']}]  {h['subject'][:35]}  "
              f"listing={h.get('listing_id', 'N/A')}")


def show_list():
    schedule = load_schedule()
    categories = schedule['categories']
    pos = schedule['queue_position'] % len(categories)
    print(f"\nArt Category Rotation — {len(categories)} categories")
    print(f"{'─'*60}")
    for i, cat in enumerate(categories):
        marker = ' ← NEXT' if i == pos else ''
        used = len(cat.get('subjects_used', []))
        total = len(cat['subjects'])
        print(f"  {i+1:2d}. [{cat['id'][:20]:<20}] {cat['label']:<35} "
              f"${cat['price']:.2f}  ({used}/{total} subjects used){marker}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Scheduled art poster for OnBrandCraftz Etsy shop')
    parser.add_argument('--force',   action='store_true', help='Post now regardless of schedule')
    parser.add_argument('--preview', action='store_true', help='Generate images only, no Etsy post')
    parser.add_argument('--status',  action='store_true', help='Show queue and schedule')
    parser.add_argument('--list',    action='store_true', help='Show full category rotation list')
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.list:
        show_list()
        return

    schedule = load_schedule()
    today = datetime.date.today()
    next_post = datetime.date.fromisoformat(schedule.get('next_post_date', '2000-01-01'))

    if args.force or args.preview:
        print(f"[{'PREVIEW' if args.preview else 'FORCED'}] Running now (scheduled: {next_post})")
        post_art(preview_only=args.preview)
    elif today >= next_post:
        print(f"[SCHEDULED] Due today ({today}) — posting now")
        post_art(preview_only=False)
    else:
        days_until = (next_post - today).days
        print(f"[SCHEDULED] Not due yet — next post in {days_until} day(s) on {next_post}")
        print("  Use --force to post now, --status to see the queue.")


if __name__ == '__main__':
    main()
