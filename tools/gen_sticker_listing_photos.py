#!/usr/bin/env python3
"""
Generate and upload listing photos for the 6 standalone sticker pack listings.
Uses the actual sticker sheet JPGs — no AI generation needed.
"""
import os, sys, json, time, urllib.request
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

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from tools.etsy_api import EtsyAPIClient, EtsyAPIError


def _resolve_dp_base() -> Path:
    """digital_products base — the durable Railway volume in production, the
    repo tree locally. Same resolution order used throughout tools/."""
    vol = os.getenv("HUB_FILES_DIR", "").strip()
    if vol and Path(vol).is_dir():
        return Path(vol)
    if Path("/data/files").is_dir():
        return Path("/data/files")
    return _ROOT / "data" / "digital_products"


ART_DIR = str(_resolve_dp_base() / "product_files")
CANVAS = 2400

PACKS = {
    'free':     {'pid': 'DP1026', 'listing_id': 4512255508, 'name': 'Free Kawaii Sticker Sheet',
                 'color': (134,102,170), 'accent': (196,168,212), 'bg': (250,247,255),
                 'sheets': [4], 'price': 'FREE', 'theme': 'Lavender Dreams'},
    'lavender': {'pid': 'DP1026', 'listing_id': 4512255514, 'name': 'Lavender Dreams Sticker Pack',
                 'color': (134,102,170), 'accent': (196,168,212), 'bg': (250,247,255),
                 'sheets': [1,4,6,9,11], 'price': '$4.99', 'theme': 'Lavender Dreams'},
    'cotton':   {'pid': 'DP1027', 'listing_id': 4512254015, 'name': 'Cotton Candy Sticker Pack',
                 'color': (222,151,198), 'accent': (151,198,222), 'bg': (255,247,253),
                 'sheets': [1,4,6,8,11], 'price': '$4.99', 'theme': 'Cotton Candy'},
    'midnight': {'pid': 'DP1028', 'listing_id': 4512255536, 'name': 'Midnight Blue Sticker Pack',
                 'color': (27,37,104), 'accent': (123,167,194), 'bg': (240,245,255),
                 'sheets': [1,4,6,7,11], 'price': '$4.99', 'theme': 'Midnight Blue'},
    'coral':    {'pid': 'DP1029', 'listing_id': 4512254027, 'name': 'Coral Peach Sticker Pack',
                 'color': (253,108,73), 'accent': (245,184,120), 'bg': (255,248,244),
                 'sheets': [1,4,6,7,11], 'price': '$4.99', 'theme': 'Coral Peach'},
    'bundle':   {'pid': None, 'listing_id': 4512254035, 'name': 'All 4 Sticker Packs Bundle',
                 'color': (100,70,140), 'accent': (180,150,220), 'bg': (250,247,255),
                 'sheets': [], 'price': '$12.99', 'theme': 'All 4 Themes'},
}


def fb(size):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
              '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf']:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def fr(size):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
              '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf']:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def drop_shadow(canvas, x, y, w, h, blur=20, opacity=45):
    layer = Image.new('RGBA', canvas.size, (0,0,0,0))
    ImageDraw.Draw(layer).rectangle([x+14,y+14,x+w+14,y+h+14], fill=(0,0,0,opacity))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=blur))
    return Image.alpha_composite(canvas, layer)


def sheet_img(pid, n, size):
    path = os.path.join(ART_DIR, f'{pid}_sticker_sheet_{n}.jpg')
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert('RGB').resize((size,size), Image.LANCZOS)
    return img


def card_wrap(img, radius=20, border_color=None):
    """Wrap a PIL image in a white rounded card."""
    w, h = img.size
    card = Image.new('RGBA', (w+20, h+20), (255,255,255,255))
    mask = Image.new('L', (w+20, h+20), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0,0,w+19,h+19], radius=radius+4, fill=255)
    card.putalpha(mask)
    card.paste(img, (10, 10))
    return card


# ── Photo 01: Hero — large featured sheet + name ──────────────────────────────

def make_hero(cfg, out):
    bg = Image.new('RGB', (CANVAS, CANVAS), cfg['bg'])
    # Gradient
    for y in range(CANVAS):
        t = y/CANVAS * 0.07
        r,g,b = cfg['bg']
        cr,cg,cb = cfg['color']
        shade = (int(r*(1-t)+cr*t), int(g*(1-t)+cg*t), int(b*(1-t)+cb*t))
        ImageDraw.Draw(bg).line([(0,y),(CANVAS,y)], fill=shade)

    bg = bg.convert('RGBA')

    pid = cfg['pid'] or 'DP1026'
    sheets_to_show = cfg['sheets'] if cfg['sheets'] else [1,4,6,9]

    # Hero sheet — large center
    hero_n = sheets_to_show[0] if sheets_to_show else 4
    hero_size = 1500
    hero = sheet_img(pid, hero_n, hero_size)
    if hero:
        hcard = card_wrap(hero, radius=24)
        bg = drop_shadow(bg, CANVAS//2 - hcard.width//2 + 10, 300,
                         hcard.width, hcard.height, blur=32, opacity=55)
        bg.paste(hcard, (CANVAS//2 - hcard.width//2, 300), hcard)

    # Small accent sheets scattered
    small_size = 420
    offsets = [(-750, 200, -12), (750, 280, 10), (-700, 1300, 8), (700, 1200, -10)]
    for i, (dx, sy, rot) in enumerate(offsets):
        if i+1 >= len(sheets_to_show):
            break
        sm = sheet_img(pid, sheets_to_show[i+1], small_size)
        if sm is None:
            continue
        scard = card_wrap(sm, radius=16)
        if rot:
            scard = scard.rotate(rot, expand=True, resample=Image.BICUBIC)
        sx = CANVAS//2 + dx - scard.width//2
        bg = drop_shadow(bg, sx+10, sy+10, scard.width, scard.height, blur=16, opacity=40)
        bg.paste(scard, (sx, sy), scard)

    bg = bg.convert('RGB')
    d = ImageDraw.Draw(bg)

    # Top header band
    header = Image.new('RGBA', (CANVAS, 230), cfg['color'] + (230,))
    bg_rgba = bg.convert('RGBA')
    bg_rgba.paste(header, (0,0), header)
    bg = bg_rgba.convert('RGB')
    d = ImageDraw.Draw(bg)
    d.text((CANVAS//2, 75), cfg['name'], font=fb(72), fill=(255,255,255), anchor='mm')
    d.text((CANVAS//2, 168), f"200+ kawaii stickers  ·  GoodNotes Ready  ·  Instant Download",
           font=fr(44), fill=(240,235,250), anchor='mm')

    # Bottom tag
    d.rounded_rectangle([CANVAS//2-400, CANVAS-110, CANVAS//2+400, CANVAS-30],
                        radius=40, fill=cfg['color'])
    d.text((CANVAS//2, CANVAS-70), cfg['price'], font=fb(52), fill=(255,255,255), anchor='mm')

    bg.save(out, 'JPEG', quality=93)


# ── Photo 02: All sheets overview ─────────────────────────────────────────────

def make_all_sheets(cfg, out):
    pid = cfg['pid'] or 'DP1026'
    sheets = cfg['sheets'] if cfg['sheets'] else list(range(1, 12))
    if not sheets:
        sheets = list(range(1, 12))

    bg = Image.new('RGB', (CANVAS, CANVAS), cfg['bg'])
    d = ImageDraw.Draw(bg)
    d.rectangle([0,0,CANVAS,180], fill=cfg['color'])
    d.text((CANVAS//2, 90), "ALL STICKER SHEETS INCLUDED", font=fb(72), fill=(255,255,255), anchor='mm')

    # Lay out sheets in a grid — up to 4 per row
    n = len(sheets)
    cols = min(n, 4)
    rows = (n + cols - 1) // cols
    PAD = 70
    GAP = 24
    cell_w = (CANVAS - 2*PAD - GAP*(cols-1)) // cols
    cell_h = (CANVAS - 200 - 2*PAD - GAP*(rows-1)) // rows

    for i, sn in enumerate(sheets):
        row, col = divmod(i, cols)
        x = PAD + col*(cell_w+GAP)
        y = 200 + PAD + row*(cell_h+GAP)
        sm = sheet_img(pid, sn, min(cell_w, cell_h))
        if sm is None:
            continue
        sm = sm.resize((cell_w, cell_h), Image.LANCZOS)
        d.rounded_rectangle([x-4,y-4,x+cell_w+4,y+cell_h+4], radius=12, fill=cfg['color'])
        bg.paste(sm, (x, y))

    bg.save(out, 'JPEG', quality=93)


# ── Photo 03: Close-up of functional stickers ─────────────────────────────────

def make_closeup(cfg, sheet_num, label, out):
    pid = cfg['pid'] or 'DP1026'
    bg = Image.new('RGB', (CANVAS, CANVAS), cfg['bg'])
    d = ImageDraw.Draw(bg)
    d.rectangle([0,0,CANVAS,180], fill=cfg['color'])
    d.text((CANVAS//2,90), label, font=fb(72), fill=(255,255,255), anchor='mm')

    sm = sheet_img(pid, sheet_num, 2000)
    if sm:
        x, y = (CANVAS-2000)//2, 220
        d.rounded_rectangle([x-8,y-8,x+2008,y+2008], radius=20, fill=cfg['accent'])
        bg.paste(sm, (x,y))

    d.text((CANVAS//2, CANVAS-55), f"{cfg['theme']}  ·  200+ stickers per pack  ·  OnBrandCraftz",
           font=fr(42), fill=cfg['color'], anchor='mm')
    bg.save(out, 'JPEG', quality=93)


# ── Photo 04: GoodNotes how-to ────────────────────────────────────────────────

def make_howto(cfg, out):
    bg = Image.new('RGB', (CANVAS, CANVAS), cfg['bg'])
    d = ImageDraw.Draw(bg)
    d.rectangle([0,0,CANVAS,180], fill=cfg['color'])
    d.text((CANVAS//2,90), "HOW TO IMPORT INTO GOODNOTES 6", font=fb(66), fill=(255,255,255), anchor='mm')

    steps = [
        ("1", "Download & Unzip", "Save your sticker pack ZIP from Etsy.\nUnzip to reveal the sticker sheet JPGs."),
        ("2", "Import into Elements", "Open GoodNotes 6 → tap ◆ Elements\n→ Stickers tab → tap + → select all sheets"),
        ("3", "Use on Any Page", "Tap any sticker in your library\nand drag it onto any planner page!"),
    ]
    panel_w = (CANVAS-180)//3
    px = 60
    for step, title, body in steps:
        d.rounded_rectangle([px, 220, px+panel_w, CANVAS-140], radius=24,
                            fill=(255,255,255), outline=cfg['accent'], width=4)
        cx = px + panel_w//2
        d.ellipse([cx-75, 310, cx+75, 460], fill=cfg['color'])
        d.text((cx, 385), step, font=fb(86), fill=(255,255,255), anchor='mm')
        d.text((cx, 510), title, font=fb(54), fill=(50,40,70), anchor='mm')
        for j, line in enumerate(body.split('\n')):
            d.text((cx, 610+j*60), line, font=fr(40), fill=(110,90,140), anchor='mm')
        px += panel_w+30

    d.rectangle([0,CANVAS-130,CANVAS,CANVAS], fill=cfg['color'])
    d.text((CANVAS//2, CANVAS-65), "Also works in Notability · PDF Expert · Xodo · Acrobat",
           font=fb(46), fill=(255,255,255), anchor='mm')
    bg.save(out, 'JPEG', quality=93)


# ── Photo 05: What's included card ────────────────────────────────────────────

def make_whats_included(cfg, out):
    is_free = cfg['price'] == 'FREE'
    is_bundle = cfg['pid'] is None

    bg = Image.new('RGB', (CANVAS, CANVAS), cfg['bg'])
    d = ImageDraw.Draw(bg)
    d.rectangle([0,0,CANVAS,260], fill=cfg['color'])
    d.text((CANVAS//2,90), "WHAT'S INCLUDED", font=fb(90), fill=(255,255,255), anchor='mm')
    d.text((CANVAS//2,198), cfg['name'], font=fr(52), fill=(240,235,250), anchor='mm')

    PAD = 90
    if is_bundle:
        lines = [
            ("Lavender Dreams Pack",    "11 illustrated sheets · 200+ stickers"),
            ("Cotton Candy Pack",        "11 illustrated sheets · 200+ stickers"),
            ("Midnight Blue Pack",       "11 illustrated sheets · 200+ stickers"),
            ("Coral Peach Pack",         "11 illustrated sheets · 200+ stickers"),
            ("44 sticker sheets total",  "800+ kawaii stickers included"),
            ("GoodNotes sticker book",   "Import all packs at once"),
            ("Instant digital download", "Delivered as organized ZIP folders"),
        ]
    elif is_free:
        lines = [
            ("1 kawaii sticker sheet",   "Cozy lifestyle theme · transparent background"),
            ("PNG format",               "Compatible with GoodNotes, Notability, and more"),
            ("Print-ready",              "300 DPI — print on sticker paper too"),
            ("GoodNotes ready",          "Import via Elements → Stickers → +"),
            ("Instant download",         "Delivered immediately after purchase"),
        ]
    else:
        lines = [
            (f"11 illustrated sticker sheets", f"{cfg['theme']} theme · unique kawaii designs"),
            ("200+ individual sticker items", "Functional + decorative styles"),
            ("Transparent PNG background",   "No white borders — drop onto any page"),
            ("GoodNotes Elements ready",      "Import all sheets in one step"),
            ("Also works in Notability",      "And PDF Expert, Xodo, Acrobat"),
            ("Print-ready quality",           "300 DPI — print on sticker paper"),
            ("Instant digital download",      "Delivered immediately after purchase"),
        ]

    y = 310
    for main, sub in lines:
        d.rounded_rectangle([PAD, y, CANVAS-PAD, y+145], radius=16,
                            fill=(255,255,255), outline=cfg['accent'], width=3)
        d.ellipse([PAD+18,y+28,PAD+78,y+88], fill=cfg['color'])
        d.text((PAD+48, y+58), "✓", font=fb(38), fill=(255,255,255), anchor='mm')
        d.text((PAD+105, y+46), main, font=fb(50), fill=(50,40,70))
        d.text((PAD+105, y+102), sub, font=fr(40), fill=(140,120,160))
        y += 162

    d.rectangle([0,CANVAS-170,CANVAS,CANVAS], fill=cfg['color'])
    d.text((CANVAS//2, CANVAS-85), f"{cfg['price']}  ·  Instant Digital Download  ·  OnBrandCraftz",
           font=fb(50), fill=(255,255,255), anchor='mm')
    bg.save(out, 'JPEG', quality=93)


# ── Bundle-specific: 4-theme grid ─────────────────────────────────────────────

def make_bundle_grid(out):
    pids  = ['DP1026','DP1027','DP1028','DP1029']
    colors = [(134,102,170),(222,151,198),(27,37,104),(253,108,73)]
    names  = ['Life Planner','Student Planner','Budget Planner','Fitness Planner']
    bg = Image.new('RGB', (CANVAS,CANVAS), (250,247,255))
    d = ImageDraw.Draw(bg)
    d.rectangle([0,0,CANVAS,180], fill=(100,70,140))
    d.text((CANVAS//2,90), "ALL 4 STICKER PACKS — 800+ STICKERS",
           font=fb(68), fill=(255,255,255), anchor='mm')

    PAD, GAP = 80, 50
    CELL = (CANVAS-2*PAD-GAP)//2
    pos = [(PAD,200),(PAD+CELL+GAP,200),(PAD,200+CELL+GAP),(PAD+CELL+GAP,200+CELL+GAP)]
    for i,(pid,color,name) in enumerate(zip(pids,colors,names)):
        x,y = pos[i]
        d.rectangle([x-6,y-6,x+CELL+6,y+CELL+6], fill=color)
        sm = sheet_img(pid, 4, CELL)
        if sm:
            bg.paste(sm, (x,y))
        ribbon_h = 60
        d.rectangle([x,y+CELL-ribbon_h,x+CELL,y+CELL], fill=color)
        d.text((x+CELL//2,y+CELL-ribbon_h//2), name, font=fb(32), fill=(255,255,255), anchor='mm')
    bg.save(out, 'JPEG', quality=93)


# ── Upload ────────────────────────────────────────────────────────────────────

# Human-readable per-photo alt text (2026-07-15 ADA/WCAG audit fix) --
# baseline slug->description mapping, not AI-per-photo captioning.
_PHOTO_ALT_LABELS = {
    '01_hero': 'sticker sheets flat-lay hero photo',
    '02_all_sheets': 'all sticker sheets overview',
    '03_four_themes': 'four planner themes preview',
    '03_functional': 'functional planning stickers close-up',
    '04_howto': 'GoodNotes sticker import how-to steps',
    '05_whats_included': "what's included summary",
    '06_illustrated': 'illustrated kawaii stickers close-up',
}


def _photo_alt_text(product_name, label):
    desc = _PHOTO_ALT_LABELS.get(label, label.replace('_', ' '))
    return f"{product_name} — {desc}"[:500]


def upload_photos(listing_id, files, client, product_name=''):
    shop_id = client.shop_id
    auth_headers = {"Authorization": f"Bearer {client.access_token}",
                    "x-api-key": f"{client.client_id}:{client.client_secret}"}

    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images",
        headers=auth_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        existing = json.loads(resp.read()).get('results', [])
    for img in existing:
        try:
            urllib.request.urlopen(urllib.request.Request(
                f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/images/{img['listing_image_id']}",
                headers=auth_headers, method="DELETE"), timeout=15)
        except: pass
        time.sleep(0.3)
    if existing:
        print(f"    Cleared {len(existing)} old images")

    for rank, (path, label) in enumerate(files, 1):
        if not os.path.exists(path):
            print(f"    SKIP: {label}")
            continue
        for attempt in range(3):
            try:
                alt_text = _photo_alt_text(product_name, label) if product_name else None
                result = client.upload_listing_image(listing_id, path, rank=rank, alt_text=alt_text)
                print(f"    Uploaded rank {rank}: {label}")
                time.sleep(0.8)
                break
            except EtsyAPIError as e:
                if e.status == 401:
                    client.refresh_access_token()
                    auth_headers["Authorization"] = f"Bearer {client.access_token}"
                elif e.status == 429:
                    time.sleep(20)
                else:
                    print(f"    Failed {label}: {e}"); break


# ── Per-pack workflow ─────────────────────────────────────────────────────────

def process_pack(key, cfg, client):
    pid = cfg['pid'] or 'DP1026'
    out_dir = os.path.join(ART_DIR, f'sticker_listing_{key}')
    os.makedirs(out_dir, exist_ok=True)
    sheets = cfg['sheets']

    print(f"\n{'='*50}")
    print(f"  {cfg['name']}")

    f = lambda name: os.path.join(out_dir, name)

    make_hero(cfg, f('01_hero.jpg'));                                    print("    01_hero")
    make_all_sheets(cfg, f('02_all_sheets.jpg'));                        print("    02_all_sheets")

    if key == 'bundle':
        make_bundle_grid(f('03_four_themes.jpg'));                       print("    03_four_themes")
    elif sheets:
        make_closeup(cfg, sheets[0], "FUNCTIONAL PLANNING STICKERS",
                     f('03_functional.jpg'));                            print("    03_functional")

    make_howto(cfg, f('04_howto.jpg'));                                  print("    04_howto")
    make_whats_included(cfg, f('05_whats_included.jpg'));                print("    05_whats_included")

    # Extra sheet close-up if we have enough sheets
    if len(sheets) >= 3 and key != 'bundle':
        make_closeup(cfg, sheets[2], "ILLUSTRATED KAWAII STICKERS",
                     f('06_illustrated.jpg'));                           print("    06_illustrated")

    photo_files = [
        (f('01_hero.jpg'), '01_hero'),
        (f('02_all_sheets.jpg'), '02_all_sheets'),
        (f('03_four_themes.jpg') if key=='bundle' else f('03_functional.jpg'),
         '03_four_themes' if key=='bundle' else '03_functional'),
        (f('04_howto.jpg'), '04_howto'),
        (f('05_whats_included.jpg'), '05_whats_included'),
        (f('06_illustrated.jpg'), '06_illustrated'),
    ]

    print(f"\n  Uploading to listing {cfg['listing_id']}...")
    upload_photos(cfg['listing_id'], photo_files, client, product_name=cfg['name'])
    print(f"  ✓ Done")


if __name__ == '__main__':
    client = EtsyAPIClient()
    client.refresh_access_token()

    for key, cfg in PACKS.items():
        process_pack(key, cfg, client)

    print("\n✓ All sticker pack listings updated with photos")
