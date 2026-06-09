#!/usr/bin/env python3
"""
Publish the Good Vibes Groovy SVG Pack to Etsy.
Steps:
  1. Build ZIP of all 20 SVGs
  2. Generate 10 listing photos at 2400×2400
  3. Create the Etsy listing (draft)
  4. Upload listing photos
  5. Upload digital ZIP file
  6. Activate listing
  7. Assign to SVG Cut Files shop section
"""
import os, sys, zipfile, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Parse .env manually (never use load_dotenv)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import urllib3
urllib3.disable_warnings()

from PIL import Image, ImageDraw
from etsy_api import EtsyAPIClient, EtsyAPIError

SVG_DIR   = "data/groovy_pack/SVG"
PREV_DIR  = "data/groovy_pack/previews"
PHOTO_DIR = "data/groovy_pack/listing_photos"
ZIP_PATH  = "data/groovy_pack/OnBrandCraftz_GoodVibes_SVG_Bundle_20_Designs.zip"
SVG_SECTION_ID = 58769490   # "SVG Cut Files" section

os.makedirs(PHOTO_DIR, exist_ok=True)

# ─── Step 1: Build ZIP ────────────────────────────────────────────────────────
print("📦 Building SVG ZIP...")
svg_files = sorted(f for f in os.listdir(SVG_DIR) if f.endswith(".svg"))
with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
    for fname in svg_files:
        zf.write(os.path.join(SVG_DIR, fname), arcname=f"OnBrandCraftz_GoodVibes/{fname}")
zip_mb = os.path.getsize(ZIP_PATH) / 1024 / 1024
print(f"   ✓ {len(svg_files)} SVGs → {zip_mb:.2f} MB")
assert zip_mb < 20, f"ZIP too large: {zip_mb:.1f} MB (Etsy limit 20 MB)"

# ─── Step 2: Listing photos ──────────────────────────────────────────────────
print("\n🖼  Building listing photos...")

previews = sorted(f for f in os.listdir(PREV_DIR) if f.endswith(".png"))

def _load_on_white(path):
    """Composite RGBA onto white to prevent transparent → black artifacts."""
    img = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.paste(img, mask=img.split()[3])
    return bg.convert("RGB")

pil_imgs = {f: _load_on_white(os.path.join(PREV_DIR, f)) for f in previews}

TARGET = 2400

def make_collage(files, cols, rows, out_path, bg=(255, 255, 255), padding=16, border=5):
    cell = (TARGET - padding * (cols + 1)) // cols
    canvas = Image.new("RGB", (TARGET, TARGET), bg)
    draw = ImageDraw.Draw(canvas)
    for idx, fname in enumerate(files[:cols * rows]):
        row_i = idx // cols
        col_i = idx % cols
        img = pil_imgs[fname].copy().resize((cell, cell), Image.LANCZOS)
        x = padding + col_i * (cell + padding)
        y = padding + row_i * (cell + padding)
        draw.rectangle([x - border, y - border, x + cell + border, y + cell + border],
                       outline=(220, 220, 220), width=border)
        canvas.paste(img, (x, y))
    canvas.save(out_path, "PNG", optimize=True)
    print(f"   ✓ {os.path.basename(out_path)}")

def make_single(fname, out_path):
    img = pil_imgs[fname].copy().resize((TARGET, TARGET), Image.LANCZOS)
    img.save(out_path, "PNG", optimize=True)
    print(f"   ✓ {os.path.basename(out_path)}")

def make_2up(f1, f2, out_path, gap=24):
    half = (TARGET - gap * 3) // 2
    canvas = Image.new("RGB", (TARGET, TARGET), (255, 255, 255))
    for i, fname in enumerate([f1, f2]):
        img = pil_imgs[fname].copy().resize((half, half), Image.LANCZOS)
        x = gap + i * (half + gap)
        y = (TARGET - half) // 2
        canvas.paste(img, (x, y))
    canvas.save(out_path, "PNG", optimize=True)
    print(f"   ✓ {os.path.basename(out_path)}")

def make_3up(f1, f2, f3, out_path, gap=20):
    third = (TARGET - gap * 4) // 3
    canvas = Image.new("RGB", (TARGET, TARGET), (255, 255, 255))
    for i, fname in enumerate([f1, f2, f3]):
        img = pil_imgs[fname].copy().resize((third, third), Image.LANCZOS)
        x = gap + i * (third + gap)
        y = (TARGET - third) // 2
        canvas.paste(img, (x, y))
    canvas.save(out_path, "PNG", optimize=True)
    print(f"   ✓ {os.path.basename(out_path)}")

# Photo 1 — Hero: 4×5 grid of all 20 designs
make_collage(previews, cols=4, rows=5,
             out_path=f"{PHOTO_DIR}/photo_01_hero_grid.png", padding=20)

# Photo 2 — Spotlight 4: most eye-catching designs
spotlight4 = [
    "groovy_19_bloom.png",
    "groovy_09_peace_love.png",
    "groovy_20_rainbow.png",
    "groovy_01_good_vibes.png",
]
make_collage(spotlight4, cols=2, rows=2,
             out_path=f"{PHOTO_DIR}/photo_02_spotlight_4.png", padding=28)

# Photo 3 — Single: Bloom (most striking minimal design)
make_single("groovy_19_bloom.png", f"{PHOTO_DIR}/photo_03_bloom.png")

# Photo 4 — Single: Peace Love Joy (rainbow colors)
make_single("groovy_09_peace_love.png", f"{PHOTO_DIR}/photo_04_peace_love_joy.png")

# Photo 5 — Single: You Are a Rainbow (multi-color showstopper)
make_single("groovy_20_rainbow.png", f"{PHOTO_DIR}/photo_05_rainbow.png")

# Photo 6 — Single: Good Vibes Only (top search term)
make_single("groovy_01_good_vibes.png", f"{PHOTO_DIR}/photo_06_good_vibes.png")

# Photo 7 — 2-up: Stay Groovy + Choose Happy
make_2up("groovy_02_stay_groovy.png", "groovy_05_choose_happy.png",
         f"{PHOTO_DIR}/photo_07_groovy_happy.png")

# Photo 8 — 3-up: Wild & Free, Flower Power, Soul on Fire
make_3up("groovy_06_wild_free.png", "groovy_08_flower_power.png", "groovy_11_soul_fire.png",
         f"{PHOTO_DIR}/photo_08_3up_bold.png")

# Photo 9 — Bonus 3×2 grid: 6 more designs
bonus6 = [
    "groovy_04_be_weird.png",
    "groovy_07_good_things.png",
    "groovy_10_radiate.png",
    "groovy_12_dream_chaser.png",
    "groovy_16_magic_happens.png",
    "groovy_17_happy_chaos.png",
]
make_collage(bonus6, cols=3, rows=2,
             out_path=f"{PHOTO_DIR}/photo_09_bonus_grid.png", padding=22)

# Photo 10 — Single: Magic Happens Here (crowd favourite phrase)
make_single("groovy_16_magic_happens.png", f"{PHOTO_DIR}/photo_10_magic_happens.png")

photos_ordered = [
    f"{PHOTO_DIR}/photo_01_hero_grid.png",
    f"{PHOTO_DIR}/photo_02_spotlight_4.png",
    f"{PHOTO_DIR}/photo_03_bloom.png",
    f"{PHOTO_DIR}/photo_04_peace_love_joy.png",
    f"{PHOTO_DIR}/photo_05_rainbow.png",
    f"{PHOTO_DIR}/photo_06_good_vibes.png",
    f"{PHOTO_DIR}/photo_07_groovy_happy.png",
    f"{PHOTO_DIR}/photo_08_3up_bold.png",
    f"{PHOTO_DIR}/photo_09_bonus_grid.png",
    f"{PHOTO_DIR}/photo_10_magic_happens.png",
]

# ─── Step 3: Listing content ─────────────────────────────────────────────────
TITLE = "Good Vibes SVG Bundle | 20 Designs Cricut | Instant Download"
assert len(TITLE) <= 70, f"Title {len(TITLE)} chars — over 70 char limit!"
print(f"\n📝 Title ({len(TITLE)} chars): {TITLE}")

TAGS = [
    "motivational svg",
    "inspirational svg",
    "positive quote svg",
    "positive svg bundle",
    "retro svg bundle",
    "shirt svg design",
    "tumbler svg wrap",
    "svg cut file",
    "instant download",
    "cricut svg files",
    "vinyl decal svg",
    "tote bag svg",
    "groovy svg",
]
assert len(TAGS) == 13, f"Need 13 tags, got {len(TAGS)}"
for t in TAGS:
    assert len(t) <= 20, f"Tag too long: '{t}' ({len(t)} chars)"

DESCRIPTION = """\
✂️ 20 bold, colorful Good Vibes SVG designs — instant download, Cricut & Silhouette ready!

This is the feel-good SVG bundle people talk about. Twenty striking, typography-forward designs with big cursive script and vivid contrasting colors — the kind that stop the scroll and make every shirt, tumbler, and tote look like it came from a boutique. White backgrounds, clean cuts, zero fuss.

━━━━━━━━━━━━━━━━━━━━━━━━
✂️ WHAT'S INCLUDED (20 Designs)
━━━━━━━━━━━━━━━━━━━━━━━━
1. Good Vibes Only
2. Stay Groovy
3. Spread Love
4. Be Weird Be Wonderful
5. Choose Happy
6. Wild & Free
7. Good Things Coming
8. Flower Power
9. Peace Love Joy
10. Radiate Positivity
11. Soul on Fire
12. Dream Chaser
13. Wander Often Wonder Always
14. Life Is Colorful
15. Keep Growing
16. Magic Happens Here
17. Happy Chaos
18. Sun Child
19. Bloom
20. You Are a Rainbow

━━━━━━━━━━━━━━━━━━━━━━━━
📁 FILE DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Format: SVG (scalable vector — works at ANY size without quality loss)
✅ 20 individual SVG files, organized in a clean ZIP
✅ Compatible with Cricut Design Space, Silhouette Studio, Adobe Illustrator, Inkscape, CorelDRAW, and more
✅ White background / black design — ready to recolor in your cutting software
✅ Clean single-layer design — easy to cut, weld, or color separately

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 WHAT CAN YOU MAKE?
━━━━━━━━━━━━━━━━━━━━━━━━
★ T-shirts, tanks, hoodies, sweatshirts
★ Stanley tumblers, Yeti cups, water bottles
★ Tote bags and canvas bags
★ Car decals and window stickers
★ Mugs and ceramic cups
★ Pillows, blankets, and home décor
★ Gift tags and paper crafts

━━━━━━━━━━━━━━━━━━━━━━━━
💡 HOW TO USE YOUR FILES
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase and download your ZIP file instantly from Etsy
2. Unzip the folder — 20 SVG files inside, ready to use
3. Open in Cricut Design Space, Silhouette Studio, or your preferred software
4. Resize, recolor, and cut — every design is fully scalable
5. Apply with heat transfer vinyl (HTV), adhesive vinyl, sublimation, or laser engraving

━━━━━━━━━━━━━━━━━━━━━━━━
🖥 COMPATIBLE SOFTWARE
━━━━━━━━━━━━━━━━━━━━━━━━
★ Cricut Design Space (all Cricut machines)
★ Silhouette Studio (all Silhouette machines)
★ Adobe Illustrator
★ Inkscape (free)
★ CorelDRAW
★ Canva Pro
★ Laser engravers (Glowforge, xTool, etc.)

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Will this work with my Cricut?
A: Yes! All 20 SVGs open directly in Cricut Design Space — upload, resize, and cut.

Q: Can I sell items I make with these designs?
A: Yes — commercial use license included. You may sell finished physical products (shirts, tumblers, etc.). You may NOT resell, redistribute, or share the digital SVG files themselves.

Q: What if I need a different format (PNG, DXF, EPS)?
A: Message me! I'm happy to send alternate formats at no extra charge.

Q: Is this a physical item?
A: No — this is a digital download only. Your ZIP file is available immediately after purchase. Nothing is shipped.

Q: I've never used SVG files — is it hard?
A: Not at all! If you can upload a photo to Cricut Design Space, you can use an SVG. You get perfect crisp edges at any size — something PNG files can't do.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Commercial use license included — sell your finished handmade products. Do NOT resell, redistribute, or share the SVG files digitally.

Questions? Message me anytime — I respond within 24 hours. Happy crafting! ✂️"""

LISTING_DATA = {
    "title": TITLE,
    "description": DESCRIPTION,
    "price": 7.99,
    "quantity": 999,
    "tags": TAGS,
    "taxonomy_id": 2078,
    "type": "download",
    "who_made": "i_did",
    "when_made": "made_to_order",
    "is_supply": False,
    "state": "draft",
    "shop_section_id": SVG_SECTION_ID,
}

# ─── Step 4: API client + quality gate ──────────────────────────────────────
client = EtsyAPIClient()
client.refresh_access_token()

print("\n🔍 Running pre-publish quality gate...")
failures = client.pre_publish_gate(LISTING_DATA)
if failures:
    print("❌ Quality gate FAILED:")
    for f in failures:
        print(f"   • {f}")
    sys.exit(1)
print("   ✓ All checks passed")

# ─── Step 5: Create listing ──────────────────────────────────────────────────
print("\n🚀 Creating Etsy listing (draft)...")
result = client.create_listing(LISTING_DATA)
listing_id = result["listing_id"]
print(f"   ✓ Listing created — ID: {listing_id}")

# ─── Step 6: Upload photos ───────────────────────────────────────────────────
print("\n📸 Uploading listing photos...")
for rank, photo_path in enumerate(photos_ordered, start=1):
    try:
        client.upload_listing_image(listing_id, photo_path, rank=rank)
        print(f"   ✓ Photo {rank}: {os.path.basename(photo_path)}")
        time.sleep(1.5)
    except EtsyAPIError as e:
        print(f"   ✗ Photo {rank} failed: {e}")

# ─── Step 7: Upload digital file ─────────────────────────────────────────────
print("\n📁 Uploading digital ZIP file...")
try:
    file_result = client.upload_listing_file(listing_id, ZIP_PATH, rank=1)
    print(f"   ✓ ZIP uploaded: {file_result.get('filename', ZIP_PATH)}")
except EtsyAPIError as e:
    print(f"   ✗ File upload FAILED: {e}")
    print(f"   ⛔ Aborting activation — listing {listing_id} kept as draft to prevent selling without a download file.")
    sys.exit(1)

# ─── Step 8: Activate listing ────────────────────────────────────────────────
print("\n✅ Activating listing...")
try:
    active = client.update_listing(listing_id, {"state": "active"})
    state = active.get("state", "unknown")
    print(f"   ✓ Listing state: {state}")
    url = f"https://www.etsy.com/listing/{listing_id}"
    print(f"\n🎉 LIVE: {url}")
except EtsyAPIError as e:
    print(f"   ✗ Activation failed: {e}")
    print(f"   Listing ID {listing_id} saved as draft — activate manually in Etsy dashboard")
    url = f"https://www.etsy.com/listing/{listing_id}"

# ─── Save record ─────────────────────────────────────────────────────────────
record = {
    "listing_id": listing_id,
    "title": TITLE,
    "price": 7.99,
    "tags": TAGS,
    "zip_path": ZIP_PATH,
    "photo_count": len(photos_ordered),
    "design_count": len(svg_files),
    "etsy_url": url,
    "shop_section_id": SVG_SECTION_ID,
}
record_path = "data/groovy_pack/listing_record.json"
with open(record_path, "w") as f:
    json.dump(record, f, indent=2)
print(f"\n📄 Record saved: {record_path}")
