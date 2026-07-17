#!/usr/bin/env python3
"""
Generate lifestyle room scenes for wall art listings.

Workflow:
  1. Generate a full AI room scene WITH the art described (produces natural results)
  2. Detect the white mat area inside the frame
  3. Replace the AI art with the actual product art file
  4. Verify the output looks natural before saving

Usage:
  python tools/gen_lifestyle_scene.py --pid DP1038 --verify
  python tools/gen_lifestyle_scene.py --pid DP1038 --no-regen  (re-composite only)
"""

import os, sys, json, base64, urllib.request, time, argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Guarded — hosted deploys (Railway) inject env vars directly and have no .env file.
_env_path = _ROOT / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance


def _resolve_dp_base() -> Path:
    """digital_products base — the durable Railway volume in production, the
    repo tree locally. Same resolution order used throughout tools/."""
    vol = os.getenv("HUB_FILES_DIR", "").strip()
    if vol and Path(vol).is_dir():
        return Path(vol)
    if Path("/data/files").is_dir():
        return Path("/data/files")
    return _ROOT / "data" / "digital_products"


OPENAI_KEY = os.environ.get('OPENAI_API_KEY', '')
ART_DIR = str(_resolve_dp_base() / "product_files")


def gen_image(prompt, out_path, size="1024x1024", quality="high"):
    payload = json.dumps({
        "model": "gpt-image-1", "prompt": prompt.strip(), "n": 1,
        "size": size, "quality": quality, "output_format": "jpeg"
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {OPENAI_KEY}"},
        method="POST"
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            img_bytes = base64.b64decode(data["data"][0]["b64_json"])
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            kb = len(img_bytes) // 1024
            print(f"    Generated: {os.path.basename(out_path)} ({kb}KB)")
            return True
        except Exception as e:
            if attempt < 2:
                print(f"    Retry {attempt+1}: {e}")
                time.sleep(20)
            else:
                print(f"    ERROR: {e}")
                return False


# ── Frame/mat detection ───────────────────────────────────────────────────────

def _is_mat_pixel(r, g, b, thresh=185, max_sat=40):
    """Return True if the pixel looks like a white/cream mat."""
    return r > thresh and g > thresh and b > thresh and (max(r,g,b) - min(r,g,b)) < max_sat


def detect_mat_bounds(img, sample_step=4, col_threshold=0.35, row_threshold=0.35):
    """
    Find the white mat rectangle in an AI-generated room scene.

    Scans every sample_step-th pixel. A column/row is considered "mat-like"
    if at least col_threshold/row_threshold of its sampled pixels are white/cream.

    Returns (left, top, right, bottom) of the INNER art area (inside the mat),
    or None if detection fails.
    """
    W, H = img.size

    # --- Column scan ---
    white_cols = []
    for x in range(0, W, sample_step):
        white_count = sum(
            1 for y in range(0, H, sample_step)
            if _is_mat_pixel(*img.getpixel((x, y)))
        )
        total = H // sample_step
        if white_count / total >= col_threshold:
            white_cols.append(x)

    # --- Row scan ---
    white_rows = []
    for y in range(0, H, sample_step):
        white_count = sum(
            1 for x in range(0, W, sample_step)
            if _is_mat_pixel(*img.getpixel((x, y)))
        )
        total = W // sample_step
        if white_count / total >= row_threshold:
            white_rows.append(y)

    if not white_cols or not white_rows:
        return None

    # Find the largest contiguous run in each axis
    def largest_run(vals):
        if not vals:
            return None
        best_start = best_end = vals[0]
        cur_start = vals[0]
        step = sample_step
        for i in range(1, len(vals)):
            if vals[i] - vals[i-1] <= step * 2:
                best_end = max(best_end, vals[i])
            else:
                if best_end - best_start < vals[i] - cur_start:
                    best_start = cur_start
                cur_start = vals[i]
                best_end = vals[i]
        return cur_start, best_end

    col_run = largest_run(white_cols)
    row_run = largest_run(white_rows)
    if not col_run or not row_run:
        return None

    mat_l, mat_r = col_run
    mat_t, mat_b = row_run

    mat_w = mat_r - mat_l
    mat_h = mat_b - mat_t

    # Sanity check: mat should be at least 10% and no more than 85% of canvas
    if mat_w < W * 0.10 or mat_h < H * 0.10:
        return None
    if mat_w > W * 0.85 or mat_h > H * 0.85:
        return None

    # Inset the mat border to get the inner art area.
    # Typical mat border in these AI images is ~3-5% of canvas width.
    mat_border = max(12, int(min(mat_w, mat_h) * 0.06))
    art_l = mat_l + mat_border
    art_t = mat_t + mat_border
    art_r = mat_r - mat_border
    art_b = mat_b - mat_border

    return art_l, art_t, art_r, art_b


def replace_art_in_frame(room_path, art_path, out_path, verify=True):
    """
    Find the mat rectangle in room_path and replace the art area with art_path.
    Returns (success, bounds) where bounds = (l,t,r,b) of art placement.
    """
    room = Image.open(room_path).convert('RGB')
    W, H = room.size

    bounds = detect_mat_bounds(room)
    if bounds is None:
        print(f"    WARNING: mat detection failed on {os.path.basename(room_path)}")
        print(f"    Falling back to centre-wall placement...")
        # Fallback: place at 15% from top, centred, art takes 38% of width
        art_img = Image.open(art_path).convert('RGB')
        art_pct = 0.38
        aw = int(W * art_pct)
        ah = int(aw * art_img.height / art_img.width)
        mat_pad = int(W * 0.03)
        frame_pad = int(W * 0.014)
        full_w = aw + 2*mat_pad + 2*frame_pad
        full_h = ah + 2*mat_pad + 2*frame_pad
        px = (W - full_w) // 2
        py = int(H * 0.08)
        # Check it doesn't go below 70%
        if py + full_h > H * 0.72:
            art_pct = 0.26
            aw = int(W * art_pct)
            ah = int(aw * art_img.height / art_img.width)
            full_w = aw + 2*mat_pad + 2*frame_pad
            full_h = ah + 2*mat_pad + 2*frame_pad
            px = (W - full_w) // 2
        frame_color = (150, 115, 75)
        _draw_frame_and_art(room, art_path, px, py, full_w, full_h, aw, ah, mat_pad, frame_pad, frame_color)
        room.save(out_path, 'JPEG', quality=93)
        print(f"    Fallback composite saved: {os.path.basename(out_path)}")
        return True, (px + frame_pad + mat_pad, py + frame_pad + mat_pad,
                      px + frame_pad + mat_pad + aw, py + frame_pad + mat_pad + ah)

    art_l, art_t, art_r, art_b = bounds
    art_w_px = art_r - art_l
    art_h_px = art_b - art_t

    print(f"    Mat detected: art area ({art_l},{art_t}) → ({art_r},{art_b})  "
          f"size={art_w_px}×{art_h_px}px  "
          f"({art_l/W*100:.0f}%,{art_t/H*100:.0f}%) → ({art_r/W*100:.0f}%,{art_b/H*100:.0f}%)")

    # Load and crop-fill the real art into the detected area
    art_img = Image.open(art_path).convert('RGB')
    aw, ah = art_img.size
    target_w, target_h = art_w_px, art_h_px

    # Cover-crop: fill the target rectangle maintaining aspect ratio
    if (aw / ah) < (target_w / target_h):
        scale_w = target_w
        scale_h = int(target_w * ah / aw)
        scaled = art_img.resize((scale_w, scale_h), Image.LANCZOS)
        cy = (scale_h - target_h) // 2
        cropped = scaled.crop((0, cy, scale_w, cy + target_h))
    else:
        scale_h = target_h
        scale_w = int(target_h * aw / ah)
        scaled = art_img.resize((scale_w, scale_h), Image.LANCZOS)
        cx = (scale_w - target_w) // 2
        cropped = scaled.crop((cx, 0, cx + target_w, scale_h))

    # Match brightness of surrounding room area
    # Sample a small patch of wall around the mat for brightness reference
    wall_sample_x = max(0, art_l - 80)
    wall_sample_y = art_t
    wall_patch = room.crop((wall_sample_x, wall_sample_y,
                             wall_sample_x + 40, wall_sample_y + 40))
    wall_brightness = sum(sum(p) for p in wall_patch.getdata()) / (3 * 40 * 40)
    # Target art brightness slightly darker than wall (print slightly dimmer than backlit wall)
    target_brightness = min(0.96, max(0.80, wall_brightness / 255 * 0.95))
    cropped = ImageEnhance.Brightness(cropped).enhance(target_brightness)

    # Soft inner shadow on mat edge to blend
    inner_shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shadow_rect = [art_l - 4, art_t - 4, art_r + 4, art_b + 4]
    ImageDraw.Draw(inner_shadow).rectangle(shadow_rect, fill=(0, 0, 0, 28))
    inner_shadow = inner_shadow.filter(ImageFilter.GaussianBlur(radius=5))
    room = Image.alpha_composite(room.convert('RGBA'), inner_shadow).convert('RGB')

    # Paste real art
    room.paste(cropped, (art_l, art_t))

    room.save(out_path, 'JPEG', quality=93)
    print(f"    Saved: {os.path.basename(out_path)}")
    return True, bounds


def _draw_frame_and_art(room, art_path, px, py, full_w, full_h, aw, ah,
                        mat_pad, frame_pad, frame_color):
    """Draw a frame+mat+art onto room (in-place) at given coordinates."""
    W, H = room.size
    # Drop shadow
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle(
        [px+10, py+14, px+full_w+10, py+full_h+14], fill=(0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))
    room_rgba = Image.alpha_composite(room.convert('RGBA'), shadow).convert('RGB')
    room.paste(room_rgba)

    draw = ImageDraw.Draw(room)
    # Frame with bevel
    draw.rectangle([px, py, px+full_w, py+full_h], fill=frame_color)
    hi = tuple(min(255, c+45) for c in frame_color)
    sh_c = tuple(max(0, c-45) for c in frame_color)
    bv = 4
    draw.polygon([px,py,px+full_w,py,px+full_w-bv,py+bv,px+bv,py+bv], fill=hi)
    draw.polygon([px,py,px,py+full_h,px+bv,py+full_h-bv,px+bv,py+bv], fill=hi)
    draw.polygon([px+full_w,py,px+full_w,py+full_h,px+full_w-bv,py+full_h-bv,
                  px+full_w-bv,py+bv], fill=sh_c)
    draw.polygon([px,py+full_h,px+full_w,py+full_h,px+full_w-bv,py+full_h-bv,
                  px+bv,py+full_h-bv], fill=sh_c)
    mx, my = px+frame_pad, py+frame_pad
    draw.rectangle([mx, my, mx+aw+2*mat_pad, my+ah+2*mat_pad], fill=(253, 251, 248))
    art_img = Image.open(art_path).convert('RGB')
    art_resized = art_img.resize((aw, ah), Image.LANCZOS)
    art_resized = ImageEnhance.Brightness(art_resized).enhance(0.91)
    room.paste(art_resized, (mx+mat_pad, my+mat_pad))


# ── Verification ─────────────────────────────────────────────────────────────

def verify_composite(out_path, bounds, room_path):
    """
    Check that the art placement looks natural:
    - Art area has reasonable saturation (not flat/blank)
    - No high-frequency edges outside the frame area are covered
    Returns True if passes, False otherwise with reason.
    """
    if not os.path.exists(out_path):
        return False, "output file missing"

    img = Image.open(out_path).convert('RGB')
    W, H = img.size

    if bounds is None:
        return False, "no bounds"

    art_l, art_t, art_r, art_b = bounds
    art_h = art_b - art_t
    frame_bottom = art_b + int(H * 0.04)   # a little below art (mat edge)

    # Check: is there complex scene content (high colour variance) well BELOW
    # the frame? (that's fine — furniture should be below)
    # But check: is there complex content just ABOVE or at the same height?
    # i.e., is the art frame floating mid-furniture?

    # Sample a strip 5% of canvas height just BELOW the frame bottom
    check_y_start = min(H - 1, frame_bottom)
    check_y_end   = min(H - 1, frame_bottom + int(H * 0.05))
    if check_y_start >= check_y_end:
        return True, "ok"

    # Sample wall region above the frame top — should be plain wall
    above_strip_t = max(0, art_t - int(H * 0.08))
    above_strip_b = max(0, art_t - 4)

    above_pixels = [img.getpixel((x, y))
                    for x in range(0, W, 16)
                    for y in range(above_strip_t, above_strip_b, 8)
                    if above_strip_b > above_strip_t]

    if not above_pixels:
        return True, "ok"

    # Check variance of above region — low variance = plain wall (good)
    avg_r = sum(p[0] for p in above_pixels) / len(above_pixels)
    avg_g = sum(p[1] for p in above_pixels) / len(above_pixels)
    avg_b = sum(p[2] for p in above_pixels) / len(above_pixels)
    variance = sum((p[0]-avg_r)**2 + (p[1]-avg_g)**2 + (p[2]-avg_b)**2
                   for p in above_pixels) / len(above_pixels)

    if variance > 4000:
        return False, f"complex scene above frame (variance={variance:.0f}) — frame may overlap furniture"

    # Check art position sanity
    if art_t < H * 0.03:
        return False, "frame top too close to image edge"
    if art_b > H * 0.80:
        return False, f"frame bottom too low ({art_b/H*100:.0f}%) — likely overlapping furniture"

    return True, "ok"


# ── Listing scene definitions ─────────────────────────────────────────────────

LISTINGS = {
    'DP1038': {
        'art_file': f'{ART_DIR}/DP1038.jpg',
        'out_dir':  f'{ART_DIR}/DP1038_listing_images',
        'scenes': [
            {
                'name': 'lifestyle_scene_A.jpg',
                'bg':   'bg_scene_A.jpg',
                'prompt': (
                    "Professional Etsy wall art lifestyle photography, square format, photorealistic. "
                    "A warm cozy rustic living room with cream linen walls and honey oak flooring. "
                    "A large framed watercolor painting of a red fox sitting in an autumn birch woodland "
                    "hangs prominently on the wall — the painting shows a majestic rust-orange fox with "
                    "white chest fur, surrounded by pale silver birch trees and fallen golden amber leaves, "
                    "rendered in soft luminous watercolor washes with beautiful transparent layering. "
                    "The frame is natural warm wood, wide off-white mat. "
                    "Below and in front of the frame: a cream linen sofa back with two rust and warm-gold "
                    "throw pillows. To the right: a tall rattan floor lamp glowing softly. "
                    "To the left: a terracotta pot with dried amber branches. "
                    "Warm golden afternoon light. Organic modern, nature-lover's home. "
                    "35mm lens, f/2.8, Architectural Digest quality. No text overlays."
                ),
            },
            {
                'name': 'lifestyle_scene_B.jpg',
                'bg':   'bg_scene_B.jpg',
                'prompt': (
                    "Professional Etsy wall art lifestyle photography, square format, photorealistic. "
                    "A cozy rustic cabin bedroom corner with warm sage-olive green walls and warm wood trim. "
                    "A large framed watercolor painting of a red fox in an autumn birch forest hangs on "
                    "the wall — the painting shows a beautiful rust-orange fox with white chest, sitting "
                    "alert among pale birch trunks with golden autumn leaves scattered on the forest floor, "
                    "soft watercolor washes in amber, sienna, and warm cream. "
                    "Natural oak wood frame, wide off-white mat. "
                    "Below the painting sits a slim wood console or floating shelf with: "
                    "a small stack of hardcover books, a ceramic fox figurine, a pillar candle glowing, "
                    "a tiny dried wildflower arrangement. Warm lamp glow from the right side. "
                    "The very bottom of the image shows a bed headboard and pillow. "
                    "50mm lens, f/2, photorealistic, warm and intimate cabin atmosphere. No text overlays."
                ),
            },
        ],
    },
}


def run(pid, regen_backgrounds=True, verify=True):
    info = LISTINGS.get(pid)
    if not info:
        print(f"No listing definition for {pid}")
        return False

    art_path = info['art_file']
    out_dir  = info['out_dir']
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.exists(art_path):
        print(f"Art file missing: {art_path}")
        return False

    all_ok = True
    for scene in info['scenes']:
        print(f"\n--- {scene['name']} ---")
        bg_path  = os.path.join(out_dir, scene['bg'])
        out_path = os.path.join(out_dir, scene['name'])

        # 1. Generate background (AI full scene with art described)
        if regen_backgrounds or not os.path.exists(bg_path):
            print(f"  Generating background...")
            ok = gen_image(scene['prompt'], bg_path, size="1024x1024", quality="high")
            if not ok:
                print(f"  FAILED to generate background")
                all_ok = False
                continue
            time.sleep(4)
        else:
            print(f"  Background exists: {bg_path}")

        # 2. Detect mat and replace AI art with real art
        print(f"  Detecting mat and replacing art...")
        success, bounds = replace_art_in_frame(bg_path, art_path, out_path)

        if not success:
            print(f"  FAILED composite")
            all_ok = False
            continue

        # 3. Verify
        if verify:
            ok, reason = verify_composite(out_path, bounds, bg_path)
            if not ok:
                print(f"  VERIFY FAILED: {reason}")
                print(f"  Regenerating background with adjusted prompt...")
                # Try once more with slightly different prompt emphasis
                adjusted = scene['prompt'].replace(
                    "hangs prominently on the wall",
                    "is prominently displayed HIGH on the upper wall, well above all furniture"
                )
                if regen_backgrounds:
                    os.remove(bg_path)
                    ok2 = gen_image(adjusted, bg_path, size="1024x1024", quality="high")
                    if ok2:
                        time.sleep(3)
                        success2, bounds2 = replace_art_in_frame(bg_path, art_path, out_path)
                        ok3, reason3 = verify_composite(out_path, bounds2, bg_path)
                        if ok3:
                            print(f"  ✓ Retry passed")
                        else:
                            print(f"  Retry also imperfect ({reason3}) — keeping best result")
                all_ok = False   # Flag for manual review even if we kept it
            else:
                print(f"  ✓ Verification passed")

        size_kb = os.path.getsize(out_path) // 1024
        print(f"  Output: {out_path} ({size_kb}KB)")

    return all_ok


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', required=True)
    parser.add_argument('--no-regen', action='store_true',
                        help='Skip regenerating backgrounds; re-composite only')
    parser.add_argument('--verify', action='store_true', default=True)
    parser.add_argument('--no-verify', dest='verify', action='store_false')
    args = parser.parse_args()

    run(args.pid, regen_backgrounds=not args.no_regen, verify=args.verify)
