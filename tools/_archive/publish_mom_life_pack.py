#!/usr/bin/env python3
"""
Publish the Mom Life SVG Pack to Etsy.
Steps:
  1. Build ZIP of all 20 SVGs
  2. Generate listing hero collage + grid images
  3. Create the Etsy listing (draft)
  4. Upload listing photos (10 slots)
  5. Upload digital ZIP file
  6. Activate listing
"""
import os, sys, zipfile, json, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Parse .env manually (no load_dotenv)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import urllib3
urllib3.disable_warnings()

from PIL import Image, ImageDraw, ImageFont
from etsy_api import EtsyAPIClient, EtsyAPIError

SVG_DIR   = "data/mom_life_pack/SVG"
PREV_DIR  = "data/mom_life_pack/previews"
PHOTO_DIR = "data/mom_life_pack/listing_photos"
ZIP_PATH  = "data/mom_life_pack/OnBrandCraftz_MomLife_SVG_Bundle_20_Designs.zip"

os.makedirs(PHOTO_DIR, exist_ok=True)

# ─── Step 1: Build ZIP ────────────────────────────────────────────────────────
print("📦 Building SVG ZIP...")
svg_files = sorted(f for f in os.listdir(SVG_DIR) if f.endswith(".svg"))
with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
    for fname in svg_files:
        zf.write(os.path.join(SVG_DIR, fname), arcname=f"OnBrandCraftz_MomLife/{fname}")
zip_mb = os.path.getsize(ZIP_PATH) / 1024 / 1024
print(f"   ✓ {len(svg_files)} SVGs → {zip_mb:.2f} MB")
assert zip_mb < 20, f"ZIP too large: {zip_mb:.1f} MB (Etsy limit 20 MB)"

# ─── Step 2: Listing photos ──────────────────────────────────────────────────
print("\n🖼  Building listing photos...")

previews = sorted(f for f in os.listdir(PREV_DIR) if f.endswith(".png"))
def _load_on_white(path):
    """Composite RGBA image onto white — prevents transparent → black artifacts."""
    img = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.paste(img, mask=img.split()[3])
    return bg.convert("RGB")

pil_imgs = {f: _load_on_white(os.path.join(PREV_DIR, f)) for f in previews}

TARGET = 2400  # square px

def make_collage(files, cols, rows, out_path, bg=(255,255,255), padding=16, border=6):
    """Grid collage of preview images."""
    cell = (TARGET - padding * (cols + 1)) // cols
    canvas = Image.new("RGB", (TARGET, TARGET), bg)
    for idx, fname in enumerate(files[:cols*rows]):
        row = idx // cols
        col = idx % cols
        img = pil_imgs[fname].copy()
        img = img.resize((cell, cell), Image.LANCZOS)
        x = padding + col * (cell + padding)
        y = padding + row * (cell + padding)
        # thin border
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([x-border, y-border, x+cell+border, y+cell+border], outline=(20,20,20), width=border)
        canvas.paste(img, (x, y))
    canvas.save(out_path, "PNG", optimize=True)
    print(f"   ✓ {os.path.basename(out_path)}")

def make_single(fname, out_path, label=None):
    """Single preview at full 2400×2400."""
    img = pil_imgs[fname].copy().resize((TARGET, TARGET), Image.LANCZOS)
    if label:
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, TARGET-54, TARGET, TARGET], fill=(255,255,255))
        draw.text((TARGET//2, TARGET-27), label, fill=(40,40,40), anchor="mm")
    img.save(out_path, "PNG", optimize=True)
    print(f"   ✓ {os.path.basename(out_path)}")

def make_2up(f1, f2, out_path):
    """Side-by-side two designs."""
    half = TARGET // 2 - 12
    canvas = Image.new("RGB", (TARGET, TARGET), (255,255,255))
    for i, fname in enumerate([f1, f2]):
        img = pil_imgs[fname].copy().resize((half, half), Image.LANCZOS)
        x = 8 + i * (half + 16)
        y = (TARGET - half) // 2
        canvas.paste(img, (x, y))
    canvas.save(out_path, "PNG", optimize=True)
    print(f"   ✓ {os.path.basename(out_path)}")

# Photo 1: Hero — 4×5 grid of all 20 designs
make_collage(previews, cols=4, rows=5,
             out_path=f"{PHOTO_DIR}/photo_01_hero_grid.png", padding=18)

# Photo 2: 2×2 spotlight — top 4 most popular concepts
spotlight4 = [
    "mom_02_coffee_chaos.png",
    "mom_03_messy_bun.png",
    "mom_06_mama_bear.png",
    "mom_15_chaos_coordinator.png",
]
make_collage(spotlight4, cols=2, rows=2,
             out_path=f"{PHOTO_DIR}/photo_02_spotlight_4.png", padding=24)

# Photo 3: single — Coffee & Chaos (high search volume)
make_single("mom_02_coffee_chaos.png", f"{PHOTO_DIR}/photo_03_coffee_chaos.png")

# Photo 4: single — Messy Bun (top search term)
make_single("mom_03_messy_bun.png", f"{PHOTO_DIR}/photo_04_messy_bun.png")

# Photo 5: single — Chaos Coordinator (viral phrase)
make_single("mom_15_chaos_coordinator.png", f"{PHOTO_DIR}/photo_05_chaos_coordinator.png")

# Photo 6: single — Blessed Mama
make_single("mom_01_blessed_mama.png", f"{PHOTO_DIR}/photo_06_blessed_mama.png")

# Photo 7: 2-up — Boy Mom + Girl Mom
make_2up("mom_04_boy_mom.png", "mom_05_girl_mom.png",
         f"{PHOTO_DIR}/photo_07_boy_girl_mom.png")

# Photo 8: single — Wildflower (broad appeal beyond mom niche)
make_single("mom_16_wildflower.png", f"{PHOTO_DIR}/photo_08_wildflower.png")

# Photo 9: 3×2 bonus grid — 6 more designs
bonus6 = [
    "mom_09_tired_blessed.png",
    "mom_12_hot_mess.png",
    "mom_13_nap_time.png",
    "mom_17_mom_tribe.png",
    "mom_19_raising_arrows.png",
    "mom_20_mama_needs_coffee.png",
]
make_collage(bonus6, cols=3, rows=2,
             out_path=f"{PHOTO_DIR}/photo_09_bonus_grid.png", padding=20)

# Photo 10: single — Motherhood (emotional close)
make_single("mom_14_motherhood.png", f"{PHOTO_DIR}/photo_10_motherhood.png")

photos_ordered = [
    f"{PHOTO_DIR}/photo_01_hero_grid.png",
    f"{PHOTO_DIR}/photo_02_spotlight_4.png",
    f"{PHOTO_DIR}/photo_03_coffee_chaos.png",
    f"{PHOTO_DIR}/photo_04_messy_bun.png",
    f"{PHOTO_DIR}/photo_05_chaos_coordinator.png",
    f"{PHOTO_DIR}/photo_06_blessed_mama.png",
    f"{PHOTO_DIR}/photo_07_boy_girl_mom.png",
    f"{PHOTO_DIR}/photo_08_wildflower.png",
    f"{PHOTO_DIR}/photo_09_bonus_grid.png",
    f"{PHOTO_DIR}/photo_10_motherhood.png",
]

# ─── Step 3: Listing content ─────────────────────────────────────────────────
TITLE = "Mom Life SVG Bundle | 20 Designs Cricut Silhouette | Instant Download"
assert len(TITLE) <= 70, f"Title {len(TITLE)} chars — over 70!"
print(f"\n📝 Title ({len(TITLE)} chars): {TITLE}")

TAGS = [
    "mom life svg",
    "mama svg bundle",
    "cricut svg files",
    "mom svg bundle",
    "messy bun svg",
    "mama bear svg",
    "boy mom svg",
    "girl mom svg",
    "coffee mom svg",
    "mom shirt svg",
    "blessed mama svg",
    "instant download",
    "silhouette svg",
]
assert len(TAGS) == 13
for t in TAGS:
    assert len(t) <= 20, f"Tag too long: '{t}' ({len(t)})"

DESCRIPTION = """✂️ 20 stunning Mom Life SVG designs — instant download, Cricut & Silhouette ready!

This is the mom life SVG bundle you've been searching for. Twenty bold, beautifully crafted designs covering every kind of mama — from Coffee & Chaos to Blessed Mama, Messy Bun to Mama Bear — with a premium hand-lettered look that stands out on shirts, tumblers, totes, car decals, and more.

━━━━━━━━━━━━━━━━━━━━━━━━
✂️ WHAT'S INCLUDED (20 Designs)
━━━━━━━━━━━━━━━━━━━━━━━━
1. Blessed Mama
2. Coffee & Chaos (But Mostly Love)
3. Messy Bun & Getting Stuff Done
4. Boy Mom — Loud & Wild
5. Girl Mom — Glitter, Sass & A Whole Lotta Love
6. Don't Mess With Mama Bear
7. Soccer Mom — Sideline Squad
8. Minivan Mama — Snacks, Chaos, Love
9. Tired But Blessed
10. Wine O'Clock (Somewhere in Mom World)
11. Fur Mama — Unconditional Love, Four Paws at a Time
12. Hot Mess Express — Boarding Now
13. Is It Nap Time Yet?
14. The Art of Motherhood
15. Chaos Coordinator — Officially Certified
16. She Is a Wildflower
17. Member of the Mom Tribe — Coffee in Hand, Wine at Five
18. World's Greatest Mom — Best Job I Ever Had
19. Raising Arrows
20. This Mama Needs Coffee (And a Nap)

━━━━━━━━━━━━━━━━━━━━━━━━
📁 FILE DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Format: SVG (scalable vector — works at ANY size without quality loss)
✅ 20 individual SVG files, neatly organized in a ZIP
✅ Compatible with Cricut Design Space, Silhouette Studio, Adobe Illustrator, Inkscape, CorelDRAW, and more
✅ Clean single-layer design — easy to cut, weld, or color separately
✅ Black on transparent/white — ready to apply your own colors in your cutting software

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 WHAT CAN YOU MAKE?
━━━━━━━━━━━━━━━━━━━━━━━━
★ T-shirts, tanks, and sweatshirts
★ Stanley tumblers, Yeti cups, water bottles
★ Tote bags, diaper bags, grocery bags
★ Car decals and window stickers
★ Mugs and ceramic tumblers
★ Pillows, blankets, and home décor
★ Gift tags, cards, and paper crafts
★ Scrapbooking and journaling

━━━━━━━━━━━━━━━━━━━━━━━━
💡 HOW TO USE YOUR FILES
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase and download your ZIP file instantly from Etsy
2. Unzip the folder — 20 SVG files are inside, ready to use
3. Open your SVG in Cricut Design Space, Silhouette Studio, or your preferred software
4. Resize, recolor, and cut — each design is fully scalable
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
A: Yes! All 20 SVGs open directly in Cricut Design Space. Upload → resize → cut.

Q: Can I sell items I make with these designs?
A: Yes — this is a commercial use license. You may sell finished physical products you make using these designs. You may NOT resell, redistribute, or share the digital SVG files themselves.

Q: What if I need a different format (PNG, DXF, EPS)?
A: Message me! I'm happy to send alternate formats at no extra charge.

Q: Is this a physical item?
A: No — this is a digital download only. Your ZIP file is available immediately after purchase. No physical item is shipped.

Q: I've never used SVG files before — is it hard?
A: Not at all! If you can upload a photo to Cricut Design Space, you can use an SVG. The format gives you perfect edges at any size, which PNG files can't do.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Commercial use license included — sell your finished handmade products. Do NOT resell, redistribute, or share the SVG files digitally.

Questions? Message me anytime — I respond within 24 hours. Happy crafting! ✂️"""

LISTING_DATA = {
    "title": TITLE,
    "description": DESCRIPTION,
    "price": 9.99,
    "quantity": 999,
    "tags": TAGS,
    "taxonomy_id": 2078,          # Craft Supplies > Patterns & How To > Digital Files
    "type": "download",
    "who_made": "i_did",
    "when_made": "made_to_order",
    "is_supply": False,
    "state": "draft",
    "shop_section_id": 58769490,  # SVG Cut Files section
}

# ─── Step 4: API client + gate ───────────────────────────────────────────────
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
        time.sleep(1.5)  # polite rate limiting
    except EtsyAPIError as e:
        print(f"   ✗ Photo {rank} failed: {e}")

# ─── Step 7: Upload digital file ─────────────────────────────────────────────
print("\n📁 Uploading digital ZIP file...")
zip_uploaded = False
try:
    file_result = client.upload_listing_file(listing_id, ZIP_PATH, rank=1)
    zip_uploaded = True
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
    "price": 9.99,
    "tags": TAGS,
    "zip_path": ZIP_PATH,
    "photo_count": len(photos_ordered),
    "design_count": len(svg_files),
    "etsy_url": f"https://www.etsy.com/listing/{listing_id}",
}
record_path = "data/mom_life_pack/listing_record.json"
with open(record_path, "w") as f:
    json.dump(record, f, indent=2)
print(f"\n📄 Record saved: {record_path}")
