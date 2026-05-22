#!/usr/bin/env python3
"""
Generate all listing images for wall art products.

Every listing gets exactly:
  Rank 1 — Lifestyle A  : inpainting (exact art in AI-generated room scene)
  Rank 2 — Lifestyle B  : inpainting (second room / angle)
  Rank 3 — Mockup warm  : PIL flat wall, warm cream background
  Rank 4 — Mockup sage  : PIL flat wall, sage green background
  Rank 5 — Mockup dark  : PIL flat wall, dark charcoal background
  Rank 6 — Size guide   : PIL graphic, 5×7 / 8×10 / 11×14 / 16×20

Downloads: ZIP with print-ready JPEGs at 300 DPI
  - 5×7    (1500×2100 px)
  - 8×10   (2400×3000 px)
  - 11×14  (3300×4200 px)
  - Full   (max quality, ≈4096×6144 px upscaled)

Workflow
  --preview  PID   → generate locally, show for review, NO upload
  --upload   PID   → generate + upload to Etsy
  --all            → all 23 listings (combine with --preview or --upload)

Example:
  python tools/gen_listing_images.py --preview DP1007
  python tools/gen_listing_images.py --upload  DP1007
"""

import os, sys, io, json, base64, urllib.request, urllib.error, time, zipfile, shutil
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from tools.etsy_api import EtsyAPIClient, EtsyAPIError

OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR    = '/home/user/Etsy/data/digital_products/product_files'
client     = EtsyAPIClient()
shop_id    = client.shop_id

auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key":     f"{client.client_id}:{client.client_secret}",
}

def refresh():
    if client.refresh_access_token():
        auth_headers["Authorization"] = f"Bearer {client.access_token}"


# ── Background / frame palette ─────────────────────────────────────────────
BG_WARM  = (245, 240, 230)   # warm cream
BG_SAGE  = (172, 188, 172)   # sage green
BG_DARK  = (38,  38,  42)    # dark charcoal

# Mat colour (same for all)
MAT_COLOR = (255, 253, 249)

# Standard print sizes at 300 DPI (pixels)
PRINT_SIZES = [
    ("5x7",  1500, 2100),
    ("8x10", 2400, 3000),
    ("11x14",3300, 4200),
]
FULL_SCALE = 4   # upscale factor for "full resolution" file


# ══════════════════════════════════════════════════════════════════════════════
#  PIL GENERATORS  (no API calls needed)
# ══════════════════════════════════════════════════════════════════════════════

def make_flat_mockup(art_path: str, bg_color: tuple, frame_color: tuple, out_path: str,
                     canvas: int = 2000):
    """Exact art on flat coloured wall with drop shadow. Purely PIL."""
    bg = Image.new('RGB', (canvas, canvas), bg_color)

    art = Image.open(art_path).convert('RGB')
    art_w = int(canvas * 0.60)
    art_h = int(art_w * art.height / art.width)
    art = art.resize((art_w, art_h), Image.LANCZOS)

    mat_px, frm_px = 28, 10
    fw = art_w + 2 * mat_px + 2 * frm_px
    fh = art_h + 2 * mat_px + 2 * frm_px
    fx = (canvas - fw) // 2
    fy = (canvas - fh) // 2

    # Soft drop shadow
    shadow = Image.new('RGBA', (canvas, canvas), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle(
        [fx + 10, fy + 16, fx + fw + 10, fy + fh + 16], fill=(0, 0, 0, 60))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=22))
    bg = Image.alpha_composite(bg.convert('RGBA'), shadow).convert('RGB')

    draw = ImageDraw.Draw(bg)
    # Frame
    draw.rectangle([fx, fy, fx + fw, fy + fh], fill=frame_color)
    # Mat
    mx, my = fx + frm_px, fy + frm_px
    draw.rectangle([mx, my, mx + art_w + 2 * mat_px, my + art_h + 2 * mat_px],
                   fill=MAT_COLOR)
    # Art
    bg.paste(art, (mx + mat_px, my + mat_px))

    bg.save(out_path, 'JPEG', quality=95)
    size_kb = os.path.getsize(out_path) // 1024
    print(f"  Mockup: {os.path.basename(out_path)} ({size_kb}KB)")


def make_size_guide(art_path: str, out_path: str, product_id: str,
                    frame_color: tuple, canvas: int = 2400):
    """Size guide graphic showing print at 5×7, 8×10, 11×14, 16×20."""
    bg = Image.new('RGB', (canvas, canvas), (248, 246, 242))

    sizes = [
        ("5×7\"",  5,  7),
        ("8×10\"", 8, 10),
        ("11×14\"",11, 14),
        ("16×20\"",16, 20),
    ]

    mat_frac = 0.06
    gap = int(canvas * 0.025)   # gap between frames

    # Reserved areas
    header_h = int(canvas * 0.13)   # title
    label_h  = int(canvas * 0.12)   # labels + footer
    avail_h  = canvas - header_h - label_h
    avail_w  = int(canvas * 0.94)   # 3% side margin each side

    # Frame overhead factor: fw ≈ disp_w * (1 + 2*mat_frac + 2*mat_frac/3)
    overhead = 1 + 2 * mat_frac + 2 * (mat_frac / 3)

    # Compute px_per_in: take the MINIMUM of height and width constraints
    px_per_in_h = avail_h / (20 * overhead)   # tallest (20") fits in avail_h
    total_gap_w = gap * (len(sizes) - 1)
    px_per_in_w = (avail_w - total_gap_w) / (sum(s[1] for s in sizes) * overhead)
    px_per_in = min(px_per_in_h, px_per_in_w)

    # Compute actual frame dimensions for each size
    frame_dims = []
    for label, w_in, h_in in sizes:
        disp_w = int(w_in * px_per_in)
        disp_h = int(h_in * px_per_in)
        mat_px = max(4, int(disp_w * mat_frac))
        frm_px = max(2, mat_px // 3)
        fw = disp_w + 2 * mat_px + 2 * frm_px
        fh = disp_h + 2 * mat_px + 2 * frm_px
        frame_dims.append((label, w_in, h_in, disp_w, disp_h, mat_px, frm_px, fw, fh))

    # Center the group horizontally
    total_fw = sum(d[7] for d in frame_dims)
    start_x = (canvas - total_fw - total_gap_w) // 2
    base_y = header_h + avail_h   # bottom-align prints to this y

    draw = ImageDraw.Draw(bg)
    art = Image.open(art_path).convert('RGB')
    cur_x = start_x

    try:
        font    = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 36)
        font_sm = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
        font_hdr = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 52)
        font_sub = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30)
    except Exception:
        font = font_sm = font_hdr = font_sub = ImageFont.load_default()

    for label, w_in, h_in, disp_w, disp_h, mat_px, frm_px, fw, fh in frame_dims:
        fx = cur_x
        fy = base_y - fh   # bottom-align

        # Shadow
        shadow = Image.new('RGBA', (canvas, canvas), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rectangle(
            [fx + 4, fy + 6, fx + fw + 4, fy + fh + 6], fill=(0, 0, 0, 45))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))
        bg = Image.alpha_composite(bg.convert('RGBA'), shadow).convert('RGB')
        draw = ImageDraw.Draw(bg)

        # Frame + mat + art
        draw.rectangle([fx, fy, fx + fw, fy + fh], fill=frame_color)
        mx, my = fx + frm_px, fy + frm_px
        draw.rectangle([mx, my, mx + disp_w + 2 * mat_px, my + disp_h + 2 * mat_px],
                       fill=MAT_COLOR)
        art_resized = art.resize((disp_w, disp_h), Image.LANCZOS)
        bg.paste(art_resized, (mx + mat_px, my + mat_px))

        # Labels below frame
        label_y = base_y + 18
        lx = fx + fw // 2
        draw.text((lx, label_y), label, fill=(60, 55, 50), font=font, anchor='mt')
        draw.text((lx, label_y + 46), f'{w_in}×{h_in} inches', fill=(140, 130, 120),
                  font=font_sm, anchor='mt')

        cur_x += fw + gap

    # Header
    draw.text((canvas // 2, 60), "AVAILABLE PRINT SIZES",
              fill=(60, 55, 50), font=font_hdr, anchor='mt')
    draw.text((canvas // 2, 128),
              "Print at home or at any local or online print shop at 300 DPI",
              fill=(140, 130, 120), font=font_sub, anchor='mt')

    # Footer
    draw.text((canvas // 2, canvas - 50),
              "Instant digital download — no physical item shipped",
              fill=(160, 155, 145), font=font_sub, anchor='mb')

    bg.save(out_path, 'JPEG', quality=95)
    size_kb = os.path.getsize(out_path) // 1024
    print(f"  Size guide: {os.path.basename(out_path)} ({size_kb}KB)")


def make_download_zip(art_path: str, product_id: str, out_path: str):
    """
    Create a ZIP with print-ready JPEGs at 300 DPI.
    Standard Etsy wall art download format.
    """
    art = Image.open(art_path).convert('RGB')
    orig_w, orig_h = art.size

    # Upscale to high resolution base (~4096 wide)
    target_base_w = 4096
    scale = target_base_w / orig_w
    base_w = int(orig_w * scale)
    base_h = int(orig_h * scale)
    art_hires = art.resize((base_w, base_h), Image.LANCZOS)
    print(f"  Upscaling art {orig_w}×{orig_h} → {base_w}×{base_h}")

    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Full resolution file
        buf = io.BytesIO()
        art_hires.save(buf, 'JPEG', quality=97, dpi=(300, 300))
        zf.writestr(f'{product_id}_FullResolution_Print.jpg', buf.getvalue())
        print(f"    Full res: {base_w}×{base_h}px ({len(buf.getvalue())//1024}KB)")

        # Standard print sizes at 300 DPI, cropped/padded to exact ratio
        for (label, pw, ph) in PRINT_SIZES:
            target_w, target_h = pw, ph
            # Scale to fit within target, preserving aspect ratio (letterbox with white)
            ratio = min(target_w / base_w, target_h / base_h)
            fit_w = int(base_w * ratio)
            fit_h = int(base_h * ratio)
            resized = art_hires.resize((fit_w, fit_h), Image.LANCZOS)
            # Place on white canvas at exact size
            canvas_img = Image.new('RGB', (target_w, target_h), (255, 255, 255))
            paste_x = (target_w - fit_w) // 2
            paste_y = (target_h - fit_h) // 2
            canvas_img.paste(resized, (paste_x, paste_y))
            buf = io.BytesIO()
            canvas_img.save(buf, 'JPEG', quality=95, dpi=(300, 300))
            fname = f'{product_id}_{label}_300dpi.jpg'
            zf.writestr(fname, buf.getvalue())
            print(f"    {label}: {target_w}×{target_h}px ({len(buf.getvalue())//1024}KB)")

        # Instructions text file
        instructions = f"""PRINTING INSTRUCTIONS — {product_id}
================================

INCLUDED FILES:
  {product_id}_FullResolution_Print.jpg   — Best quality, print at any size
  {product_id}_5x7_300dpi.jpg            — 5×7 inch print (1500×2100 px, 300 DPI)
  {product_id}_8x10_300dpi.jpg           — 8×10 inch print (2400×3000 px, 300 DPI)
  {product_id}_11x14_300dpi.jpg          — 11×14 inch print (3300×4200 px, 300 DPI)

HOW TO PRINT:
  1. Home printer: Open JPEG in photo viewer and print at actual size.
     Select "High quality / Best" print setting and photo paper.
  2. Print lab: Upload the JPEG to Walgreens, Costco, Shutterfly, Nations Photo Lab,
     or any local print shop. Order as a "Photo Print" or "Art Print."
  3. Online: PrintingForLess, MPix, or Canvaspop for premium art paper options.

RECOMMENDED PAPER:
  Matte photo paper for a fine-art look (no glare).
  Lustre/satin paper for a slightly glossy finish.
  Canvas (stretched or rolled) for a gallery wall feel.

FRAME SIZES:
  Standard US frames fit these prints perfectly:
  5×7, 8×10, 11×14, 16×20 — available at IKEA, Target, Michaels, and Amazon.

© OnBrandCraftz — Personal use only. Not for resale or redistribution.
"""
        zf.writestr('PRINTING_INSTRUCTIONS.txt', instructions)

    size_kb = os.path.getsize(out_path) // 1024
    print(f"  Download ZIP: {os.path.basename(out_path)} ({size_kb}KB)")


# ══════════════════════════════════════════════════════════════════════════════
#  AI INPAINTING GENERATOR  (requires OpenAI billing)
# ══════════════════════════════════════════════════════════════════════════════

def _build_inpaint_canvas(art_path: str, frame_color: tuple,
                           canvas_size: int = 1024) -> bytes:
    """
    Creates RGBA PNG: framed art in upper-center, everything else transparent.
    Transparent areas = where DALL-E generates the room.
    Art pixels are 100% opaque = preserved exactly by the edit endpoint.
    """
    art = Image.open(art_path).convert('RGB')

    # Size art to 45% of canvas width, keep aspect ratio
    art_w = int(canvas_size * 0.45)
    art_h = int(art_w * art.height / art.width)

    # If portrait art is too tall, constrain height to 65% of canvas
    if art_h > int(canvas_size * 0.65):
        art_h = int(canvas_size * 0.65)
        art_w = int(art_h * art.width / art.height)

    art = art.resize((art_w, art_h), Image.LANCZOS)

    mat_px, frm_px = 15, 7
    fw = art_w + 2 * mat_px + 2 * frm_px
    fh = art_h + 2 * mat_px + 2 * frm_px
    fx = (canvas_size - fw) // 2
    fy = int(canvas_size * 0.08)   # 8% from top

    canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Frame (opaque — preserved by DALL-E)
    draw.rectangle([fx, fy, fx + fw, fy + fh], fill=(*frame_color, 255))
    # Mat (pure white, opaque)
    mx, my = fx + frm_px, fy + frm_px
    draw.rectangle([mx, my, mx + art_w + 2 * mat_px, my + art_h + 2 * mat_px],
                   fill=(255, 255, 255, 255))
    # Art pixels (opaque — preserved exactly)
    art_rgba = Image.new('RGBA', (art_w, art_h), (255, 255, 255, 255))
    art_rgba.paste(art, (0, 0))
    canvas.paste(art_rgba, (mx + mat_px, my + mat_px))

    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    return buf.getvalue()


def gen_inpaint(art_path: str, frame_color: tuple, room_prompt: str,
                out_path: str) -> bool:
    """
    Call OpenAI /v1/images/edits with framed art on transparent canvas.
    DALL-E fills the transparent area with the room scene.
    Art pixels are preserved exactly (opaque = kept by the API).
    """
    png_bytes = _build_inpaint_canvas(art_path, frame_color)

    boundary = b'----OAIBoundary9k2m'
    body = b''

    def field(name, val):
        nonlocal body
        body += (b'--' + boundary +
                 b'\r\nContent-Disposition: form-data; name="' + name.encode() +
                 b'"\r\n\r\n' + val.encode() + b'\r\n')

    def file_part(name, fname, data, ctype):
        nonlocal body
        body += (b'--' + boundary +
                 b'\r\nContent-Disposition: form-data; name="' + name.encode() +
                 b'"; filename="' + fname.encode() +
                 b'"\r\nContent-Type: ' + ctype.encode() +
                 b'\r\n\r\n' + data + b'\r\n')

    field('model',         'gpt-image-1')
    field('prompt',        room_prompt.strip())
    field('n',             '1')
    field('size',          '1024x1024')
    field('quality',       'high')
    field('output_format', 'jpeg')
    file_part('image', 'art_frame.png', png_bytes, 'image/png')
    body += b'--' + boundary + b'--\r\n'

    req = urllib.request.Request(
        'https://api.openai.com/v1/images/edits',
        data=body,
        headers={
            'Authorization':  f'Bearer {OPENAI_KEY}',
            'Content-Type':   f'multipart/form-data; boundary={boundary.decode()}',
        },
        method='POST',
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            img_bytes = base64.b64decode(data['data'][0]['b64_json'])
            with open(out_path, 'wb') as f:
                f.write(img_bytes)
            print(f"  Lifestyle: {os.path.basename(out_path)} ({len(img_bytes)//1024}KB)")
            return True
        except urllib.error.HTTPError as e:
            body_err = e.read().decode()[:300]
            print(f"  HTTP {e.code}: {body_err}")
            if 'billing' in body_err:
                print("  ⚠ OpenAI billing limit — top up at platform.openai.com/billing")
                return False
            if attempt < 2:
                time.sleep(20)
        except Exception as e:
            if attempt < 2:
                print(f"  Retry {attempt+1}: {e}")
                time.sleep(20)
            else:
                print(f"  ERROR: {e}")
    return False


# ══════════════════════════════════════════════════════════════════════════════
#  ETSY UPLOAD HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_image_ranks(listing_id):
    url = f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images"
    req = urllib.request.Request(url, headers=auth_headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {img['rank']: img['listing_image_id']
                    for img in json.loads(resp.read()).get('results', [])}
    except Exception as e:
        print(f"  WARNING get_images: {e}")
        return {}

def delete_image(listing_id, image_id):
    url = (f"https://openapi.etsy.com/v3/application/shops/{shop_id}"
           f"/listings/{listing_id}/images/{image_id}")
    req = urllib.request.Request(url, headers=auth_headers, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=30): return True
    except urllib.error.HTTPError as e:
        print(f"  DELETE {image_id}: {e.code}"); return False

def upload_image(listing_id, img_path, rank):
    for attempt in range(3):
        try:
            result = client.upload_listing_image(listing_id, img_path, rank=rank)
            print(f"  rank {rank} → id={result.get('listing_image_id')}")
            return True
        except EtsyAPIError as e:
            if e.status == 401: refresh()
            elif e.status == 429: time.sleep(15)
            elif e.status == 500 and attempt < 2: time.sleep(5)
            else: print(f"  rank {rank} FAILED: {e}"); return False
    return False

def upload_file(listing_id, file_path, rank=1):
    for attempt in range(3):
        try:
            result = client.upload_listing_file(listing_id, file_path, rank=rank)
            print(f"  file rank {rank} → id={result.get('listing_file_id')}")
            return True
        except EtsyAPIError as e:
            if e.status == 401: refresh()
            elif e.status == 429: time.sleep(15)
            else: print(f"  file upload FAILED: {e}"); return False
    return False


# ══════════════════════════════════════════════════════════════════════════════
#  LISTING DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════
# inpaint_prompt_A / B: Describe the ROOM and FURNITURE only.
# Do NOT describe the art — it's already in the canvas, DALL-E sees it and
# generates the room around it. The art pixels are preserved exactly.
#
# frame_color: RGB tuple matching the frame rendered around the art.
# lifestyle_ranks: (rank_A, rank_B) — which Etsy ranks hold lifestyle shots.
# ─────────────────────────────────────────────────────────────────────────────

LISTINGS = {

    'DP1007': {
        'listing_id':    '4509218152',
        'art_file':      f'{ART_DIR}/DP1007.jpg',
        'out_dir':       f'{ART_DIR}/DP1007_listing_images',
        'frame_color':   (139, 90, 43),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Bright Mediterranean farmhouse dining room, warm cream plaster walls.
            Below the framed painting on the wall: a rustic dark walnut farm table
            with rush-seat dining chairs either side, a large handmade ceramic bowl
            overflowing with fresh yellow lemons, a small green olive oil bottle,
            and a folded natural linen napkin on the table surface.
            Warm golden afternoon sunlight streaming from a tall window at the left edge.
            Sheer linen curtain catching the breeze. Photorealistic, Architectural Digest
            editorial quality. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Bright coastal kitchen styled vignette. Warm white limewash walls.
            Below the framed wall print: a white marble-topped console table
            with a terracotta pot of fresh rosemary on the left, a small hand-thrown
            ceramic jug in the center, and a short stack of Italian cookbook spines.
            Bright Mediterranean daylight. Linen curtain at left edge.
            Photorealistic, Pinterest wall art editorial style. No text overlays.
        """,
    },

    'DP1012': {
        'listing_id':    '4509258172',
        'art_file':      f'{ART_DIR}/DP1012.jpg',
        'out_dir':       f'{ART_DIR}/DP1012_listing_images',
        'frame_color':   (28, 28, 28),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Chic modern living room, dusty rose painted accent wall, light oak flooring.
            Below the framed art print: a curved cream bouclé sofa with two geometric
            throw pillows in cobalt and terracotta. To the right: a slim brass floor lamp.
            To the left: a tall fiddle-leaf fig tree in a terracotta pot.
            Bright soft natural daylight from the left. Warm, editorial feel.
            Photorealistic, Architectural Digest quality. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Warm white plaster gallery wall. Below the framed art print: a slim
            walnut console table holding a single oversized terracotta ceramic vase,
            a short stack of architecture coffee table books, and a small trailing
            pothos plant in a stone pot. Warm neutral ambient light, clean styling.
            Photorealistic, gallery-quality aesthetic. No text overlays.
        """,
    },

    'DP1013': {
        'listing_id':    '4509258700',
        'art_file':      f'{ART_DIR}/DP1013.jpg',
        'out_dir':       f'{ART_DIR}/DP1013_listing_images',
        'frame_color':   (160, 118, 68),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Bright airy bedroom, soft sage green walls, white linen bedding.
            Below the framed wall print: a neatly made bed with cream and sage linen
            pillows stacked against a simple white headboard. On the nightstand to
            the right: a small dried pampas grass bud vase. Natural morning light
            from a large left window. Photorealistic, Home & Gardens editorial quality.
            No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Bright spring living room corner, warm cream plaster wall.
            Below the framed print: a white linen sofa with a blush pink velvet throw
            pillow and a sage textured cushion. To the right: a small rattan side table
            with a small white ceramic pot of trailing string-of-pearls.
            Bright spring daylight. Photorealistic, botanical decor aesthetic.
            No text overlays.
        """,
    },

    'DP1014': {
        'listing_id':    '4509213345',
        'art_file':      f'{ART_DIR}/DP1014.jpg',
        'out_dir':       f'{ART_DIR}/DP1014_listing_images',
        'frame_color':   (160, 118, 68),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Cozy feminine home office, warm white walls, natural light.
            Below the framed wall print: a white wooden floating shelf holding a small
            succulent in a white pot, a cream ceramic mug, and two short candle votives.
            Partially visible: a white wooden desk with a MacBook, gold pen holder,
            and a small vase of fresh white flowers. Soft warm natural light from the right.
            Photorealistic, inspirational prints aesthetic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Styled bedroom nightstand vignette, soft warm white wall.
            Below the framed wall print: a natural oak nightstand with a small bedside
            lamp glowing warmly, a cream ceramic bud vase with a dried lunaria sprig,
            and a hardcover book. White linen bedding edges at the lower left.
            Warm evening lamp light, soft and intimate. Photorealistic, Scandi
            bedroom aesthetic. No text overlays.
        """,
    },

    'DP1015': {
        'listing_id':    '4509213533',
        'art_file':      f'{ART_DIR}/DP1015.jpg',
        'out_dir':       f'{ART_DIR}/DP1015_listing_images',
        'frame_color':   (160, 130, 60),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Bright feminine dressing room, warm cream walls.
            Below the framed wall print: a slim white vanity shelf with a small
            marble makeup brush holder, a mini bouquet of blush dried roses in a
            gold bud vase, and a white ceramic ring dish. Warm soft natural light.
            Feminine, aspirational mood. Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Styled home office, soft blush pink painted walls.
            Below the framed wall print: a white lacquer desk with a gold-accented
            MacBook, a small bouquet of pink ranunculus in a clear glass vase, and
            a gold pen cup. Natural daylight. Inspiring atmosphere.
            Photorealistic, Etsy printable quote art aesthetic. No text overlays.
        """,
    },

    'DP1016': {
        'listing_id':    '4509213667',
        'art_file':      f'{ART_DIR}/DP1016.jpg',
        'out_dir':       f'{ART_DIR}/DP1016_listing_images',
        'frame_color':   (175, 140, 88),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Serene Japandi bedroom, warm white plastered walls.
            Below the framed wall print: a low Japanese platform bed with cream and
            blush linen pillows neatly stacked. To the left: a round washi paper
            pendant lamp softly glowing. To the right: a small ceramic ikebana vase
            with a single dried branch. Soft morning light. Peaceful, minimalist.
            Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Bright styled corner, soft blush pink limewash wall.
            Below the framed wall print: a slim rattan console with a white ceramic
            round pot holding a small bonsai tree, a folded cream linen, and a tiny
            stone pebble dish. Soft diffused spring daylight. Tranquil, feminine.
            Photorealistic. No text overlays.
        """,
    },

    'DP1017': {
        'listing_id':    '4509259354',
        'art_file':      f'{ART_DIR}/DP1017.jpg',
        'out_dir':       f'{ART_DIR}/DP1017_listing_images',
        'frame_color':   (55, 35, 18),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Sophisticated modern living room, warm greige walls, polished concrete floor.
            Below the framed wall art: a low charcoal gray mid-century modern sofa with
            a mustard yellow textured throw blanket folded over one arm. To the right:
            a tall sculptural black metal floor lamp. Natural warm afternoon light,
            dramatic and editorial. Photorealistic, interior magazine quality.
            No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Art-lover's home study corner, warm white plastered wall.
            Below the framed wall art: a black lacquered media credenza with a sculptural
            terracotta ceramic piece, two architecture books lying flat, and a trailing
            golden pothos plant in a matte black pot. Warm diffused natural light.
            Bold, gallery-worthy. Photorealistic. No text overlays.
        """,
    },

    'DP1018': {
        'listing_id':    '4509218860',
        'art_file':      f'{ART_DIR}/DP1018.jpg',
        'out_dir':       f'{ART_DIR}/DP1018_listing_images',
        'frame_color':   (160, 128, 75),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Serene Japandi living room, warm greige plaster walls, natural oak floor.
            Below the framed wall print: a low solid oak bench with a neatly folded
            cream linen throw draped on the left, a small glazed ceramic bonsai pot
            in the center-right. A tall washi paper floor lamp glowing softly at the
            far right. Soft warm diffused light from the left. Photorealistic,
            Japandi interior aesthetic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Calm Japandi bedroom, warm white textured plaster walls.
            Below the framed wall print: a natural oak floating shelf with a round
            white ceramic bowl, a single smooth river stone, and a tiny bonsai in a
            shallow black pot. Below the shelf: white linen bedding just visible.
            Soft morning light. Pure, contemplative. Photorealistic. No text overlays.
        """,
    },

    'DP1019': {
        'listing_id':    '4509214051',
        'art_file':      f'{ART_DIR}/DP1019.jpg',
        'out_dir':       f'{ART_DIR}/DP1019_listing_images',
        'frame_color':   (128, 88, 48),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Warm cozy living room, cream linen walls, honey-toned oak herringbone floor.
            Below the framed wall art: a cream linen tuxedo sofa with two autumn-toned
            throw pillows in ochre and rust. To the right: a tall branchy dried flower
            arrangement in a slim terracotta vase. Warm afternoon golden light.
            Nature-lover's home, cozy and inviting. Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Nature-lover's reading nook, warm cream walls.
            Below the framed wall art: a cozy curved wicker egg chair with a cream
            knit throw draped over it. To the side: a small round wood side table
            with a steaming ceramic mug and an open paperback book.
            Warm afternoon daylight through sheer linen curtains.
            Photorealistic, cottage-core aesthetic. No text overlays.
        """,
    },

    'DP1020': {
        'listing_id':    '4509214237',
        'art_file':      f'{ART_DIR}/DP1020.jpg',
        'out_dir':       f'{ART_DIR}/DP1020_listing_images',
        'frame_color':   (165, 128, 80),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Bright airy living room, warm white plaster walls, natural woven jute rug.
            Below the framed wall print: a cream linen sofa with a blush pink velvet
            throw pillow and a soft sage green textured cushion. A tall vase of dried
            pampas grass stands in the left corner. Bright spring morning light.
            Feminine, fresh. Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Bright kitchen or dining area, warm white painted brick wall.
            Below the framed wall print: a slim white console with a clear glass vase
            of fresh pink ranunculus, a small ceramic pitcher, and a worn linen cloth.
            Natural bright window light. Fresh, airy. Photorealistic, French country
            kitchen aesthetic. No text overlays.
        """,
    },

    'DP1021': {
        'listing_id':    '4509214477',
        'art_file':      f'{ART_DIR}/DP1021.jpg',
        'out_dir':       f'{ART_DIR}/DP1021_listing_images',
        'frame_color':   (45, 28, 14),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Warm masculine bar or man cave, dark walnut-paneled walls.
            Below the framed wall art: a dark wood bar cart with two crystal whiskey
            glasses, a bourbon decanter, and a small brass bowl of mixed nuts.
            Edison bulb pendant light above. Warm amber ambient light, rich and moody.
            Photorealistic, gentleman's bar aesthetic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Cozy pub-style corner, warm amber plaster walls.
            Below the framed wall art: a slim dark oak floating shelf with a row of
            vintage books by their spines, a small bronze dog figurine, and a whiskey
            glass. Warm lamplight ambiance. Quirky, charming.
            Photorealistic, English pub home bar aesthetic. No text overlays.
        """,
    },

    'DP1022': {
        'listing_id':    '4509219594',
        'art_file':      f'{ART_DIR}/DP1022.jpg',
        'out_dir':       f'{ART_DIR}/DP1022_listing_images',
        'frame_color':   (155, 158, 162),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Calm moody coastal bedroom, deep navy blue walls, natural linen bedding.
            Below the framed wall art: a low bed with a charcoal linen upholstered
            headboard and cream and navy pillow arrangement. On each nightstand:
            a small silver geometric table lamp glowing softly. Ambient lamp light,
            moody and serene. Photorealistic, coastal luxury aesthetic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Styled meditation or reading nook, dark navy blue walls, warm lighting.
            Below the framed wall art: a low rattan pouf ottoman with a cream knit
            blanket draped on it. To the right: a small carved wood side table with
            a diffuser glowing and a smooth white river stone. Warm amber candlelight
            and soft ceiling lamp. Photorealistic, spiritual coastal decor. No text overlays.
        """,
    },

    'DP1023': {
        'listing_id':    '4509214803',
        'art_file':      f'{ART_DIR}/DP1023.jpg',
        'out_dir':       f'{ART_DIR}/DP1023_listing_images',
        'frame_color':   (28, 28, 28),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Modern eclectic living room, warm white walls, mid-century furniture.
            Below the framed wall art: a mustard yellow mid-century modern sofa with
            a small round walnut coffee table. On the table: a small rocket ship model
            figurine and an open space exploration coffee table book. Bright natural
            daylight. Playful, adventurous. Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Cool teen bedroom or creative studio, blue-grey painted walls.
            Below the framed wall art: a white lacquer floating shelf with a small
            solar system model, a potted cactus, and a string of warm Edison fairy
            lights draped along the shelf edge. Bright cool natural light. Creative,
            inspiring. Photorealistic, space-lover's room. No text overlays.
        """,
    },

    'DP1024': {
        'listing_id':    '4509219904',
        'art_file':      f'{ART_DIR}/DP1024.jpg',
        'out_dir':       f'{ART_DIR}/DP1024_listing_images',
        'frame_color':   (28, 28, 28),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Masculine garage-chic man cave, exposed dark brick wall, polished concrete.
            Below the framed wall art: a low dark wood media cabinet with a matte black
            ceramic bowl, a vintage metal automotive sign, and a small cactus in a
            concrete pot. Cool industrial lighting. Bold, masculine.
            Photorealistic, automotive man cave aesthetic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Styled modern living room, charcoal gray accent wall.
            Below the framed wall art: a low dark walnut floating shelf with a scaled
            die-cast model car, two short bourbon glasses, and a leather-bound book
            on classic American cars. Warm industrial accent lighting with Edison bulbs.
            Photorealistic, automotive collector's home. No text overlays.
        """,
    },

    'DP1025': {
        'listing_id':    '4509215145',
        'art_file':      f'{ART_DIR}/DP1025.jpg',
        'out_dir':       f'{ART_DIR}/DP1025_listing_images',
        'frame_color':   (55, 35, 18),
        'lifestyle_ranks': (6, 7),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Vibrant bohemian living room, warm terracotta orange walls, woven textiles.
            Below the framed wall art: a colorful Oaxacan textile-covered bench with
            vibrant cushions. To the left: a tall woven basket with dried marigold stems.
            To the right: a small altar shelf with a white pillar candle. Warm ambient
            light. Bold, cultural, festive. Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Colorful eclectic hallway or entry nook, deep teal painted walls.
            Below the framed wall art: a slim painted wood console in deep blue with
            a clay bowl of fresh marigold flowers, two mismatched pillar candles in
            different heights, and a decorative hand-painted ceramic tile.
            Warm lamp glow. Festive and bold. Photorealistic, Day of the Dead folk
            art aesthetic. No text overlays.
        """,
    },

    'DP1030': {
        'listing_id':    '4509598660',
        'art_file':      f'{ART_DIR}/DP1030.jpg',
        'out_dir':       f'{ART_DIR}/DP1030_listing_images',
        'frame_color':   (155, 128, 55),
        'lifestyle_ranks': (1, 2),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Romantic moody bedroom, deep navy blue walls, warm brass accents.
            Below the framed wall art: an upholstered navy velvet headboard with
            cream and champagne gold pillow arrangement on the bed. On the nightstand:
            a small brass table lamp glowing warmly, an amethyst crystal cluster,
            a dried lavender sprig in a small bud vase. Warm ambient lamp light.
            Celestial, moody, sophisticated. Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Mystical reading nook, slate gray walls, warm candlelight.
            Below the framed wall art: a wooden floating shelf styled with a small
            crystal ball, a stack of dark hardcover books, a thin white taper candle
            in a brass holder, and a small dried botanical bundle. Warm candlelit glow
            and soft ceiling light. Mystical and serene. Photorealistic. No text overlays.
        """,
    },

    'DP1031': {
        'listing_id':    '4509598784',
        'art_file':      f'{ART_DIR}/DP1031.jpg',
        'out_dir':       f'{ART_DIR}/DP1031_listing_images',
        'frame_color':   (120, 85, 48),
        'lifestyle_ranks': (1, 2),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Sophisticated modern living room, warm linen white walls, polished oak floor.
            Below the framed canvas: a long low curved cream sofa with cobalt blue and
            terracotta throw pillows. In the left corner: a tall terracotta amphora vase
            with dried pampas grass stems. Bright diffused natural daylight. Modern,
            gallery-quality. Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Art-lover's gallery hallway, smooth warm off-white walls.
            Below the framed canvas: a slim travertine console with a cobalt blue
            ceramic vase, a small white sculptural object, and a single dried protea
            bloom. Clean bright museum-quality natural light.
            Photorealistic, contemporary gallery home. No text overlays.
        """,
    },

    'DP1032': {
        'listing_id':    '4509593487',
        'art_file':      f'{ART_DIR}/DP1032.jpg',
        'out_dir':       f'{ART_DIR}/DP1032_listing_images',
        'frame_color':   (80, 40, 22),
        'lifestyle_ranks': (1, 2),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            English cottage study or library, warm cream walls, dark wood bookshelves.
            Below the framed wall print: a dark wood writing desk with a brass desk lamp
            glowing warmly, an open leather journal, and a potted maidenhair fern.
            Warm incandescent library light. Scholarly, antique, charming.
            Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Bright Scandinavian living room, warm white walls, honey oak furniture.
            Below the framed wall print: a small potted maidenhair fern on a slim oak
            console, a ceramic apothecary jar with dried herbs, and a short stack of
            botanical art books. Soft bright natural daylight. Fresh, intellectual.
            Photorealistic, botanical art home. No text overlays.
        """,
    },

    'DP1033': {
        'listing_id':    '4509593623',
        'art_file':      f'{ART_DIR}/DP1033.jpg',
        'out_dir':       f'{ART_DIR}/DP1033_listing_images',
        'frame_color':   (28, 28, 28),
        'lifestyle_ranks': (1, 2),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Chic Parisian-inspired living room, warm cream walls, herringbone parquet floor.
            Below the framed wall print: a classic cream linen tuxedo sofa with a black
            and cream striped throw blanket draped on the arm. To the left: a slim marble
            side table with a glass of champagne and a small sculptural object.
            Warm Parisian afternoon light. Elegant, romantic. Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Feminine home office, soft blush pink walls, gold accents.
            Below the framed wall print: a white lacquer floating shelf with a small
            gilded decorative tower figurine, a pink peony in a slim gold bud vase,
            and a small French perfume bottle. Soft warm daylight. Dreamy, romantic.
            Photorealistic, travel-lover's room. No text overlays.
        """,
    },

    'DP1034': {
        'listing_id':    '4509593697',
        'art_file':      f'{ART_DIR}/DP1034.jpg',
        'out_dir':       f'{ART_DIR}/DP1034_listing_images',
        'frame_color':   (145, 98, 50),
        'lifestyle_ranks': (1, 2),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Nature-lover's living room, warm white walls and wood-paneled ceiling.
            Below the framed wall poster: a mid-century modern amber leather sofa
            with a Navajo-patterned woven throw blanket. To the left: a potted prickly
            pear cactus in a clay pot. To the right: a vintage National Geographic atlas
            on a side table. Warm afternoon natural light. Adventure-lover's home.
            Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Southwestern boho living corner, terracotta clay-painted walls.
            Below the framed wall poster: a slim woven rattan console with a pair of
            small clay pots with succulents, a small Kachina doll, and a rough geode
            slice. Warm terracotta-toned ambient light. Adventurous, southwestern feel.
            Photorealistic. No text overlays.
        """,
    },

    'DP1035': {
        'listing_id':    '4509600086',
        'art_file':      f'{ART_DIR}/DP1035.jpg',
        'out_dir':       f'{ART_DIR}/DP1035_listing_images',
        'frame_color':   (138, 110, 60),
        'lifestyle_ranks': (1, 2),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Vibrant tropical-inspired living room, white plaster walls.
            Below the framed wall art: a rattan peacock chair with a sage green linen
            cushion. Flanking the art on both sides: two tall live monstera deliciosa
            plants in large wicker baskets. Bright tropical natural daylight. Lush,
            resort-style living. Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Bright sunroom or porch, whitewashed walls, terracotta tile flooring.
            Below the framed wall art: a cream linen loveseat with jungle green and
            banana yellow throw pillows. To the left: a large bird of paradise plant
            in a woven banana leaf basket. Brilliant tropical daylight. Fresh, bold,
            vacation-home vibes. Photorealistic. No text overlays.
        """,
    },

    'DP1036': {
        'listing_id':    '4509596017',
        'art_file':      f'{ART_DIR}/DP1036.jpg',
        'out_dir':       f'{ART_DIR}/DP1036_listing_images',
        'frame_color':   (28, 28, 28),
        'lifestyle_ranks': (1, 2),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Chic feminine bedroom, warm blush pink walls, brass accents.
            Below the framed wall art: an upholstered blush velvet headboard with
            cream and dusty pink linen pillows arranged softly on the bed.
            On the nightstand: a small brass table lamp glowing warm, a single white
            peony in a bud vase. Warm soft natural light. Feminine, artistic.
            Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Bright art studio or creative corner, warm white walls.
            Below the framed wall art: a slim marble-top console with a white ceramic
            figure sculpture, a glass vase of dried white craspedia, and a paint-stained
            linen cloth casually draped. Bright diffused natural studio light.
            Artistic, clean, inspired. Photorealistic. No text overlays.
        """,
    },

    'DP1037': {
        'listing_id':    '4509597559',
        'art_file':      f'{ART_DIR}/DP1037.jpg',
        'out_dir':       f'{ART_DIR}/DP1037_listing_images',
        'frame_color':   (98, 88, 48),
        'lifestyle_ranks': (1, 2),
        'inpaint_prompt_A': """
            Professional interior design photography, square format.
            Italian-style kitchen, white subway tile backsplash, open wooden shelving.
            Below the framed wall art: open wooden shelves with olive oil bottles,
            small terracotta herb pots of basil and rosemary, and ceramic serving
            dishes. On the marble countertop below: a wooden pasta board and fresh
            Italian produce. Warm Mediterranean kitchen light. Inviting, rustic.
            Photorealistic. No text overlays.
        """,
        'inpaint_prompt_B': """
            Professional interior design photography, square format.
            Warm Italian farmhouse dining room, cream painted walls, rustic walnut table.
            Below the framed wall art: a corner of a rustic dining table set with
            white ceramic plates, a folded linen napkin, a short candle in a
            terracotta holder, and a small olive oil pourer. Warm candlelit evening
            dining ambiance. Inviting, romantic. Photorealistic. No text overlays.
        """,
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ORCHESTRATION
# ══════════════════════════════════════════════════════════════════════════════

def process_listing(pid: str, do_upload: bool) -> dict:
    info   = LISTINGS[pid]
    lid    = info['listing_id']
    art    = info['art_file']
    out    = info['out_dir']
    fc     = info['frame_color']
    rA, rB = info['lifestyle_ranks']

    os.makedirs(out, exist_ok=True)
    result = dict(lifestyle_A=False, lifestyle_B=False,
                  mockups=0, size_guide=False,
                  download_zip=False, uploaded=0, errors=[])

    print(f"\n{'='*60}")
    print(f"{pid}  listing={lid}")
    print(f"{'='*60}")

    # ── 1. Lifestyle A (inpainting) ───────────────────────────────────────────
    path_A = os.path.join(out, 'lifestyle_room_A.jpg')
    tmp_A  = os.path.join(out, '_new_lifestyle_room_A.jpg')
    print("  [1/6] Lifestyle A (inpaint)…")
    if gen_inpaint(art, fc, info['inpaint_prompt_A'], tmp_A):
        os.replace(tmp_A, path_A)
        result['lifestyle_A'] = True
    else:
        result['errors'].append('lifestyle_A failed')

    time.sleep(4)

    # ── 2. Lifestyle B (inpainting) ───────────────────────────────────────────
    path_B = os.path.join(out, 'lifestyle_room_B.jpg')
    tmp_B  = os.path.join(out, '_new_lifestyle_room_B.jpg')
    print("  [2/6] Lifestyle B (inpaint)…")
    if gen_inpaint(art, fc, info['inpaint_prompt_B'], tmp_B):
        os.replace(tmp_B, path_B)
        result['lifestyle_B'] = True
    else:
        result['errors'].append('lifestyle_B failed')

    time.sleep(3)

    # ── 3-5. Flat mockups (PIL — no API) ─────────────────────────────────────
    mockup_paths = []
    for idx, (bg, label) in enumerate([(BG_WARM, 'warm'), (BG_SAGE, 'sage'), (BG_DARK, 'dark')]):
        path = os.path.join(out, f'mockup_{label}.jpg')
        print(f"  [{3+idx}/6] Mockup {label}…")
        try:
            make_flat_mockup(art, bg, fc, path)
            mockup_paths.append(path)
            result['mockups'] += 1
        except Exception as e:
            result['errors'].append(f'mockup_{label}: {e}')

    # ── 6. Size guide (PIL — no API) ─────────────────────────────────────────
    sg_path = os.path.join(out, 'size_guide.jpg')
    print("  [6/6] Size guide…")
    try:
        make_size_guide(art, sg_path, pid, fc)
        result['size_guide'] = True
    except Exception as e:
        result['errors'].append(f'size_guide: {e}')

    # ── Download ZIP ──────────────────────────────────────────────────────────
    zip_path = os.path.join(out, f'{pid}_PrintReady.zip')
    print("  [ZIP] Download package…")
    try:
        make_download_zip(art, pid, zip_path)
        result['download_zip'] = True
    except Exception as e:
        result['errors'].append(f'download_zip: {e}')

    if not do_upload:
        print(f"\n  PREVIEW COMPLETE — files in {out}")
        print("  Review images before uploading.")
        return result

    # ── Upload to Etsy ────────────────────────────────────────────────────────
    print("\n  Uploading to Etsy…")
    refresh()
    existing = get_image_ranks(lid)
    print(f"  Existing ranks: {sorted(existing.keys())}")

    upload_map = []
    if result['lifestyle_A']:
        upload_map.append((rA, path_A))
    if result['lifestyle_B']:
        upload_map.append((rB, path_B))
    for rank_offset, mp in enumerate(mockup_paths):
        upload_map.append((3 + rank_offset, mp))
    if result['size_guide']:
        upload_map.append((6, sg_path))

    for rank, path in upload_map:
        old_id = existing.get(rank)
        if old_id:
            delete_image(lid, old_id)
            time.sleep(0.4)
        if upload_image(lid, path, rank):
            result['uploaded'] += 1
        time.sleep(1.2)

    # Upload download ZIP (replace existing file slot 1)
    if result['download_zip']:
        print("  Uploading download ZIP…")
        try:
            upload_file(lid, zip_path, rank=1)
        except Exception as e:
            result['errors'].append(f'zip upload: {e}')

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', metavar='PID', nargs='*',
                        help='Generate locally for review (no upload)')
    parser.add_argument('--upload',  metavar='PID', nargs='*',
                        help='Generate and upload to Etsy')
    parser.add_argument('--all', action='store_true',
                        help='Process all listings (combine with --preview or --upload)')
    args = parser.parse_args()

    if args.all:
        pids = list(LISTINGS.keys())
    elif args.preview is not None:
        pids = args.preview if args.preview else list(LISTINGS.keys())
    elif args.upload is not None:
        pids = args.upload if args.upload else list(LISTINGS.keys())
    else:
        parser.print_help()
        return

    do_upload = args.upload is not None

    results = {}
    for pid in pids:
        if pid not in LISTINGS:
            print(f"Unknown listing: {pid}")
            continue
        results[pid] = process_listing(pid, do_upload)

    print('\n\n' + '=' * 60)
    print('SUMMARY')
    print('=' * 60)
    for pid, r in results.items():
        status = ('OK' if r['lifestyle_A'] and r['lifestyle_B']
                  and r['mockups'] == 3 and r['size_guide'] else 'PARTIAL')
        print(f"{status}  {pid}:  lifestyle={r['lifestyle_A']}/{r['lifestyle_B']}  "
              f"mockups={r['mockups']}/3  size_guide={r['size_guide']}  "
              f"zip={r['download_zip']}  uploaded={r['uploaded']}  "
              f"errors={r['errors'] or 'none'}")


if __name__ == '__main__':
    main()
