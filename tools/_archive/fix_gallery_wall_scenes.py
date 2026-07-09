#!/usr/bin/env python3
"""
Fix gallery wall scenes for COASTAL-SET and FOUR-SEASONS-SET bundle listings.

Problems:
  1. gallery_scene_A/B: 2×2 art grid overlaps the sofa — needs art positioned
     clearly above the furniture, not on top of cushions.
  2. Primary photo (rank 1) is the gallery scene — gallery_grid.jpg (clean
     2×2 on neutral background) makes a better, clearer primary.

Fix:
  1. Shift each background DOWN by set-specific amount so sofa lands at ~y=700+
  2. Re-composite real art at art_pct=0.18 (slightly larger pieces)
  3. Swap ranks: gallery_grid → rank 1, gallery_scene_A → rank 2, scene_B → rank 3
  4. Upload to both bundle listings

Usage:
  python tools/fix_gallery_wall_scenes.py --preview   # generate only, no upload
  python tools/fix_gallery_wall_scenes.py             # generate + upload
"""

import os, sys, json, urllib.request, time, argparse
import numpy as np
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from PIL import Image, ImageFilter, ImageDraw
from tools.etsy_api import EtsyAPIClient, EtsyAPIError

ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

SETS = {
    'COASTAL-SET': {
        'listing_id': 4512784817,
        'pids': ['DP1052', 'DP1053', 'DP1054', 'DP1055'],
        'frame_color': (100, 80, 55),   # warm walnut — matches coastal frame
        'bg_shift': 150,                # px to shift background down
    },
    'FOUR-SEASONS-SET': {
        'listing_id': 4512784922,
        'pids': ['DP1048', 'DP1049', 'DP1050', 'DP1051'],
        'frame_color': (100, 80, 55),
        'bg_shift': 230,                # four-seasons sofa is higher, needs more shift
    },
}


def _apply_frame(canvas, px, py, art_path, art_w, mat_w, frame_w, frame_color,
                 ao_radius=14, shadow_radius=9):
    """Paste one framed+matted art piece at (px, py)."""
    art_h = int(art_w * 1.5)
    full_w = art_w + 2 * mat_w + 2 * frame_w
    full_h = art_h + 2 * mat_w + 2 * frame_w

    # Soft drop shadow
    sh = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle(
        [px + 6, py + 8, px + full_w + 6, py + full_h + 8], fill=(0, 0, 0, 55))
    sh = sh.filter(ImageFilter.GaussianBlur(shadow_radius))
    canvas = Image.alpha_composite(canvas.convert('RGBA'), sh).convert('RGB')

    # Ambient occlusion at edges
    ao = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(ao).rectangle([px, py, px + full_w, py + full_h], fill=(0, 0, 0, 35))
    ao = ao.filter(ImageFilter.GaussianBlur(ao_radius))
    canvas = Image.alpha_composite(canvas.convert('RGBA'), ao).convert('RGB')

    draw = ImageDraw.Draw(canvas)
    # Frame
    draw.rectangle([px, py, px + full_w, py + full_h], fill=frame_color)
    # Mat
    mat_color = (252, 250, 247)
    draw.rectangle(
        [px + frame_w, py + frame_w,
         px + frame_w + art_w + 2 * mat_w,
         py + frame_w + art_h + 2 * mat_w],
        fill=mat_color)
    # Art
    art = Image.open(art_path).convert('RGB').resize((art_w, art_h), Image.LANCZOS)
    canvas.paste(art, (px + frame_w + mat_w, py + frame_w + mat_w))
    return canvas


def shift_background_down(bg_path, shift_y):
    """Return new 1024×1024 image with background shifted down by shift_y px.

    Fills the new top area with the sampled wall color from a representative
    mid-section of the original, then blends the seam over 60px so the
    transition from fill to original content is invisible.
    """
    img = Image.open(bg_path).convert('RGB')
    W, H = 1024, 1024
    img = img.resize((W, H), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32)

    # Sample wall color from y=30–150 of original (representative mid-wall,
    # avoids edge/ceiling artifacts at y=0 and furniture texture below y=150)
    sample_y0 = min(30, H // 10)
    sample_y1 = min(150, H // 3)
    wall_color = arr[sample_y0:sample_y1, :, :].mean(axis=(0, 1))  # (R, G, B)

    # Build fill: horizontal rows of wall_color, each row slightly varied by
    # a tiny fraction of the actual color row above the shift point so there
    # is a natural top-to-bottom gradient matching the original wall lighting.
    fill = np.zeros((shift_y, W, 3), dtype=np.float32)
    row0 = arr[0, :, :].mean(axis=0)           # very top of original (ceiling edge)
    row_at_seam = arr[0, :, :].mean(axis=0)    # same start — gradient from top
    for y in range(shift_y):
        t = y / max(shift_y - 1, 1)            # 0 at top → 1 at seam
        fill[y, :, :] = (1 - t) * row0 + t * row_at_seam

    # The seam-side of fill matches the original image top (arr[0]), so the
    # transition is color-correct; now build full canvas
    new_arr = np.zeros((H, W, 3), dtype=np.float32)
    new_arr[:shift_y, :, :] = fill
    visible_h = H - shift_y
    if visible_h > 0:
        new_arr[shift_y:, :, :] = arr[:visible_h, :, :]

    # Blend the seam over ±40px with a Gaussian-style soft transition
    blend = 40
    for dy in range(blend):
        y_fill = shift_y - 1 - dy         # row in the fill region
        y_orig = shift_y + dy              # matching row in the original region
        if y_fill < 0 or y_orig >= H:
            break
        t = (dy + 1) / (blend + 1)        # 0 = pure fill, 1 = pure original
        new_arr[y_fill] = (1 - t) * fill[y_fill] + t * arr[dy]
        new_arr[y_orig] = (1 - t) * arr[dy] + t * arr[dy]  # just original

    # Slight blur along the extended top area to smooth any remaining banding
    result_img = Image.fromarray(np.clip(new_arr, 0, 255).astype(np.uint8))
    # Blur only the top strip (fill area), leave original sharp
    top_region = result_img.crop((0, 0, W, shift_y + blend))
    top_blurred = top_region.filter(ImageFilter.GaussianBlur(2))
    result_img.paste(top_blurred, (0, 0))

    return result_img


def composite_4_gallery(bg_path, art_paths, out_path, frame_color, bg_shift):
    """2×2 gallery wall composited onto a down-shifted background.

    art_pct=0.18 (vs original 0.16) — 12% larger per piece.
    Art positioned starting at y=20, well above the sofa.
    """
    CANVAS = 1024
    art_pct = 0.18
    mat_w, frame_w = 10, 5
    gap = 16
    start_y = 20

    # Shift background so sofa sits at ~y=700
    room = shift_background_down(bg_path, bg_shift)

    # Determine art dimensions from first file
    sample = Image.open(art_paths[0])
    aspect = sample.height / sample.width
    sample.close()

    art_w = int(CANVAS * art_pct)
    art_h = int(art_w * aspect)
    full_w = art_w + 2 * mat_w + 2 * frame_w
    full_h = art_h + 2 * mat_w + 2 * frame_w

    total_grid_w = 2 * full_w + gap
    start_x = (CANVAS - total_grid_w) // 2

    grid_bottom = start_y + 2 * full_h + gap
    print(f"    art_w={art_w}px  full_h={full_h}px  grid_bottom=y{grid_bottom} ({grid_bottom/CANVAS:.1%})")

    for i, art_path in enumerate(art_paths):
        col, row = i % 2, i // 2
        px = start_x + col * (full_w + gap)
        py = start_y + row * (full_h + gap)
        room = _apply_frame(room, px, py, art_path, art_w, mat_w, frame_w,
                            frame_color, ao_radius=12, shadow_radius=8)

    room.save(out_path, 'JPEG', quality=93)
    sz = os.path.getsize(out_path) // 1024
    print(f"    Saved: {os.path.basename(out_path)} ({sz}KB)")
    return True


def get_image_ranks(listing_id, headers):
    url = f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {img['rank']: img['listing_image_id']
                    for img in json.loads(resp.read()).get('results', [])}
    except Exception as e:
        print(f"    Image fetch error: {e}")
        return {}


def upload_image(client, listing_id, img_path, rank):
    headers = {
        "Authorization": f"Bearer {client.access_token}",
        "x-api-key": f"{client.client_id}:{client.client_secret}",
    }
    existing = get_image_ranks(listing_id, headers)
    if rank in existing:
        shop_id = client.shop_id
        url_del = (f"https://openapi.etsy.com/v3/application/shops/{shop_id}"
                   f"/listings/{listing_id}/images/{existing[rank]}")
        try:
            urllib.request.urlopen(
                urllib.request.Request(url_del, headers=headers, method="DELETE"),
                timeout=15)
            print(f"    Deleted old rank={rank}")
            time.sleep(0.5)
        except Exception as e:
            print(f"    Delete failed: {e}")

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
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', action='store_true', help='Generate images only, no upload')
    args = parser.parse_args()

    client = None
    if not args.preview:
        client = EtsyAPIClient()
        client.refresh_access_token()

    results = []

    for set_key, sinfo in SETS.items():
        print(f"\n{'='*60}")
        print(f"  {set_key}  →  listing={sinfo['listing_id']}")
        print(f"{'='*60}")

        out_dir = os.path.join(ART_DIR, f'{set_key}_listing_images')
        art_paths = [os.path.join(ART_DIR, f'{pid}.jpg') for pid in sinfo['pids']]
        missing = [p for p in art_paths if not os.path.exists(p)]
        if missing:
            print(f"  ERROR: missing art files: {missing}")
            results.append((set_key, 'missing_art'))
            continue

        fc = sinfo['frame_color']
        listing_id = sinfo['listing_id']
        grid_path = os.path.join(out_dir, 'gallery_grid.jpg')

        # ── Regenerate scene_A with corrected positioning ─────────────────────
        bg_a = os.path.join(out_dir, 'bg_gallery_scene_A.jpg')
        scene_a = os.path.join(out_dir, 'gallery_scene_A.jpg')
        print(f"\n  [Scene A] bg_shift={sinfo['bg_shift']}px, art_pct=0.18")
        ok_a = composite_4_gallery(bg_a, art_paths, scene_a, fc, sinfo['bg_shift'])

        # ── Regenerate scene_B with corrected positioning ─────────────────────
        bg_b = os.path.join(out_dir, 'bg_gallery_scene_B.jpg')
        scene_b = os.path.join(out_dir, 'gallery_scene_B.jpg')
        print(f"\n  [Scene B] bg_shift={sinfo['bg_shift']}px, art_pct=0.18")
        ok_b = composite_4_gallery(bg_b, art_paths, scene_b, fc, sinfo['bg_shift'])

        if args.preview:
            results.append((set_key, 'previewed'))
            continue

        # ── Upload in new rank order: grid=1, scene_A=2, scene_B=3 ───────────
        print(f"\n  Uploading with new rank order...")
        # Rank 1: gallery_grid.jpg (clean 2×2 — better primary/thumbnail)
        ok1 = upload_image(client, listing_id, grid_path, 1)
        time.sleep(1)
        # Rank 2: gallery_scene_A (corrected room scene)
        ok2 = upload_image(client, listing_id, scene_a, 2) if ok_a else False
        time.sleep(1)
        # Rank 3: gallery_scene_B (second room scene)
        ok3 = upload_image(client, listing_id, scene_b, 3) if ok_b else False
        time.sleep(1)

        status = 'uploaded' if (ok1 and ok2 and ok3) else 'partial'
        results.append((set_key, status))

    print(f"\n{'='*60}")
    print("COMPLETE")
    print(f"{'='*60}")
    for key, status in results:
        icon = '✓' if status in ('uploaded', 'previewed') else '⚠' if status == 'partial' else '✗'
        print(f"  {icon} {key}: {status}")

    if args.preview:
        print("\n  Preview images saved — inspect before uploading:")
        for set_key in SETS:
            d = os.path.join(ART_DIR, f'{set_key}_listing_images')
            print(f"  {d}/gallery_scene_A.jpg")
            print(f"  {d}/gallery_scene_B.jpg")


if __name__ == '__main__':
    main()
