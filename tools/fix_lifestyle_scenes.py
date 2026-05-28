#!/usr/bin/env python3
"""
Fix specific lifestyle scene backgrounds that have wainscoting/paneling issues.
Regenerates only the problematic bg_ files then re-composites.
"""
import os, sys, json, base64, urllib.request, time
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'


def gen_image(prompt, out_path, size="1024x1024", quality="high"):
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
            if attempt < 2:
                print(f"  Retry {attempt+1}: {e}")
                time.sleep(20)
            else:
                print(f"  ERROR: {e}")
                return False


def composite_into_ai_room(bg_path, art_path, out_path, frame_color=(139,110,80),
                            art_pct=0.25, top_pct=0.06):
    CANVAS = 1024
    room = Image.open(bg_path).convert('RGB').resize((CANVAS, CANVAS), Image.LANCZOS)
    art = Image.open(art_path).convert('RGB')

    art_w = int(CANVAS * art_pct)
    art_h = int(art_w * art.height / art.width)
    art_resized = art.resize((art_w, art_h), Image.LANCZOS)

    mat_w, frame_w = 30, 14
    full_w = art_w + 2*mat_w + 2*frame_w
    full_h = art_h + 2*mat_w + 2*frame_w

    px = (CANVAS - full_w) // 2
    py = int(CANVAS * top_pct)

    ao = Image.new('RGBA', (CANVAS, CANVAS), (0,0,0,0))
    for pad in range(40, 0, -4):
        alpha = int(40 * (1 - (pad/40)**1.5))
        ImageDraw.Draw(ao).rectangle(
            [px-pad, py-pad, px+full_w+pad, py+full_h+pad], fill=(0,0,0,alpha))
    ao = ao.filter(ImageFilter.GaussianBlur(radius=22))
    room = Image.alpha_composite(room.convert('RGBA'), ao).convert('RGB')

    shadow = Image.new('RGBA', (CANVAS, CANVAS), (0,0,0,0))
    ImageDraw.Draw(shadow).rectangle(
        [px+10, py+14, px+full_w+10, py+full_h+14], fill=(0,0,0,80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))
    room = Image.alpha_composite(room.convert('RGBA'), shadow).convert('RGB')

    draw = ImageDraw.Draw(room)
    draw.rectangle([px, py, px+full_w, py+full_h], fill=frame_color)
    hi = tuple(min(255, c+45) for c in frame_color)
    sh = tuple(max(0, c-45) for c in frame_color)
    bv = 4
    draw.polygon([px,py, px+full_w,py, px+full_w-bv,py+bv, px+bv,py+bv], fill=hi)
    draw.polygon([px,py, px,py+full_h, px+bv,py+full_h-bv, px+bv,py+bv], fill=hi)
    draw.polygon([px+full_w,py, px+full_w,py+full_h, px+full_w-bv,py+full_h-bv, px+full_w-bv,py+bv], fill=sh)
    draw.polygon([px,py+full_h, px+full_w,py+full_h, px+full_w-bv,py+full_h-bv, px+bv,py+full_h-bv], fill=sh)

    mx, my = px+frame_w, py+frame_w
    draw.rectangle([mx, my, mx+art_w+2*mat_w, my+art_h+2*mat_w], fill=(253,251,248))

    inner = Image.new('RGBA', (CANVAS, CANVAS), (0,0,0,0))
    art_x, art_y = mx+mat_w, my+mat_w
    ImageDraw.Draw(inner).rectangle(
        [art_x-3, art_y-3, art_x+art_w+3, art_y+art_h+3], fill=(0,0,0,30))
    inner = inner.filter(ImageFilter.GaussianBlur(radius=6))
    room = Image.alpha_composite(room.convert('RGBA'), inner).convert('RGB')

    art_final = ImageEnhance.Brightness(art_resized).enhance(0.93)
    room.paste(art_final, (art_x, art_y))

    room.save(out_path, 'JPEG', quality=93)
    print(f"  Composite saved: {os.path.basename(out_path)}")


# ── Problems identified and new prompts ──────────────────────────────────────
# Common constraint added to all: explicitly forbid wainscoting and wall paneling

def wall_constraint(wall_color, furniture_bottom_pct=32):
    return (
        f"CRITICAL LAYOUT: The TOP {100-furniture_bottom_pct}% of the image is a completely "
        f"plain, smooth, uniform {wall_color} painted wall — "
        "absolutely NO wainscoting, NO chair rail, NO wall paneling, NO beadboard, "
        "NO wood wall trim, NO architectural wall details of any kind on the wall surface. "
        f"The wall is a single solid flat color. "
        f"ONLY the BOTTOM {furniture_bottom_pct}% contains furniture: "
    )


FIXES = [
    # ── DP1051 Scene B: log cabin living room had log-plank wainscoting ────────
    {
        'pid': 'DP1051',
        'scene': 'B',
        'frame_color': (105, 118, 130),
        'prompt': (
            "Interior design product photography, square format. "
            "A cozy rustic cabin living room with warm honey cream smooth painted walls. "
            + wall_constraint("warm honey cream", 32)
            + "a log-style wooden armchair with a cream and pale blue plaid wool throw draped over the arm, "
            "a small round wood side table with a lantern-style candle glowing amber, "
            "and a small stack of nature books with a holly sprig beside them. "
            "Warm amber candle and lantern glow, cozy and intimate. "
            "Cozy winter cabin retreat aesthetic. 50mm, photorealistic. No text."
        ),
    },

    # ── DP1053 Scene A: coastal dining room had chair rail/wainscoting ─────────
    {
        'pid': 'DP1053',
        'scene': 'A',
        'frame_color': (85, 105, 120),
        'prompt': (
            "Interior design product photography, square format. "
            "A warm coastal dining room with smooth warm gray-blue walls. "
            + wall_constraint("warm gray-blue", 32)
            + "a round white pedestal dining table with four navy linen dining chairs arranged around it, "
            "a small centerpiece of a glass lantern holding a pillar candle and two smaller white candles, "
            "and a woven jute rug edge just visible. "
            "Soft warm ambient candlelight. "
            "Coastal cottage dining room aesthetic. 50mm, photorealistic. No text."
        ),
    },

    # ── DP1055 Scene B: beach house sofa back reached too high on the wall ─────
    {
        'pid': 'DP1055',
        'scene': 'B',
        'frame_color': (115, 95, 70),
        'prompt': (
            "Interior design product photography, square format. "
            "A warm rustic beach house living room with smooth warm white walls. "
            + wall_constraint("warm white", 30)
            + "the upper back and arms of a wide cream sailcloth sofa with linen throw pillows "
            "visible at the very bottom of the image. "
            "A woven rope basket sits on the sofa. "
            "The sofa fills only the bottom 30% of the frame — it must stay low. "
            "Warm golden coastal afternoon light. "
            "Rustic beach cottage living room aesthetic. 50mm, photorealistic. No text."
        ),
    },

    # ── DP1056 Scene B: dark academia study had dark wood wainscoting ──────────
    {
        'pid': 'DP1056',
        'scene': 'B',
        'frame_color': (120, 88, 58),
        'prompt': (
            "Interior design product photography, square format. "
            "A cozy home study or library with smooth warm olive-sage painted walls. "
            + wall_constraint("warm olive-sage", 32)
            + "a dark walnut writing desk with a small brass desk lamp glowing warmly, "
            "a stack of three hardcover nature field guide books, "
            "and a small ceramic fox figurine. "
            "Warm amber lamp light, intimate evening study atmosphere. "
            "Cozy dark academia study aesthetic. 50mm, photorealistic. No text."
        ),
    },
]


def run_fix(fix):
    pid = fix['pid']
    scene = fix['scene']
    out_dir = os.path.join(ART_DIR, f'{pid}_listing_images')
    art_path = os.path.join(ART_DIR, f'{pid}.jpg')
    bg_path = os.path.join(out_dir, f'bg_lifestyle_scene_{scene}.jpg')
    composite_path = os.path.join(out_dir, f'lifestyle_scene_{scene}.jpg')

    print(f"\n{'='*50}")
    print(f"Fixing {pid} Scene {scene}")
    print(f"{'='*50}")

    # Delete old background to force regeneration
    if os.path.exists(bg_path):
        os.remove(bg_path)
        print(f"  Deleted old background")

    # Generate new background
    ok = gen_image(fix['prompt'], bg_path, size="1024x1024", quality="high")
    if not ok:
        print(f"  FAILED to generate background for {pid} Scene {scene}")
        return False

    time.sleep(3)

    # Re-composite
    composite_into_ai_room(bg_path, art_path, composite_path,
                           frame_color=fix['frame_color'])
    print(f"  ✓ Fixed {pid} Scene {scene}")
    return True


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pids', nargs='+', default=None, help='Only fix these PIDs e.g. DP1051 DP1053')
    args = parser.parse_args()

    fixes_to_run = FIXES
    if args.pids:
        fixes_to_run = [f for f in FIXES if f['pid'] in args.pids]

    results = []
    for fix in fixes_to_run:
        ok = run_fix(fix)
        results.append((fix['pid'], fix['scene'], ok))
        time.sleep(2)

    print(f"\n{'='*50}")
    print("FIX COMPLETE")
    print(f"{'='*50}")
    for pid, scene, ok in results:
        status = "✓" if ok else "✗ FAILED"
        print(f"  {status} {pid} Scene {scene}")
    print()
    print("Next step: re-upload these images to their Etsy listings.")
    print("Run: python tools/reupload_lifestyle_scenes.py")
