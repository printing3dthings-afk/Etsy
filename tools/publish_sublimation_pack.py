#!/usr/bin/env python3
"""
publish_sublimation_pack.py

Builds the Mom Life Sublimation Tumbler Wrap Bundle and publishes it to Etsy.
Steps:
  1. Build ZIP (8 PNG files + README)
  2. Generate 10 listing photos at 2400×2400
  3. Create Etsy listing (draft)
  4. Upload photos
  5. Upload ZIP
  6. Activate listing
  7. Assign to Digital Downloads section
"""
import os, sys, zipfile, io, re, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Parse .env manually — never use load_dotenv()
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
with open(_env_path) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from PIL import Image, ImageDraw, ImageFont
from etsy_api import EtsyAPIClient, EtsyAPIError

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.join(os.path.dirname(__file__), "..")
SAMPLES_DIR  = os.path.join(BASE_DIR, "data", "sublimation_samples")
OUT_DIR      = os.path.join(BASE_DIR, "data", "sublimation_pack")
PHOTOS_DIR   = os.path.join(OUT_DIR, "listing_photos")
ZIP_PATH     = os.path.join(OUT_DIR, "OnBrandCraftz_MomLife_Sublimation_Bundle.zip")
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# ── Design inventory ─────────────────────────────────────────────────────────
DESIGNS = [
    ("Football Mom",   "sublimation_football_mom_20oz.png"),
    ("Cheer Mom",      "sublimation_cheer_mom_20oz.png"),
    ("Dog Mom",        "sublimation_dog_mom_20oz.png"),
    ("Nurse Life",     "sublimation_nurse_life_20oz.png"),
    ("Teacher Life",   "sublimation_teacher_life_20oz.png"),
    ("Girl Mom",       "sublimation_girl_mom_20oz.png"),
    ("Boy Mom",        "sublimation_boy_mom_20oz.png"),
    ("Mama Mode",      "sublimation_mama_mode_20oz.png"),
]

# ── Etsy listing content ─────────────────────────────────────────────────────
TITLE = "Mom Life Sublimation Tumbler Wrap Bundle PNG 20oz Instant Download"  # 65 chars

TAGS = [
    "sublimation tumbler",   # 20
    "tumbler wrap png",      # 16
    "sublimation design",    # 18
    "mom life sublimation",  # 20
    "20oz tumbler wrap",     # 17
    "football mom tumbler",  # 21 → trim
    "dog mom sublimation",   # 20
    "nurse sublimation",     # 18
    "teacher sublimation",   # 20
    "tumbler wrap bundle",   # 19
    "sublimation bundle",    # 18
    "mom tumbler wrap",      # 16
    "instant download png",  # 20
]
# Enforce 20-char max
TAGS = [t[:20].strip() for t in TAGS]

PRICE   = 9.99
SECTION = "Digital Downloads"  # shop section name (created if needed)

DESCRIPTION = """\
🎨 Eight stunning sublimation tumbler wrap designs in one instant download — print, press, and sell!

Meet the Mom Life Sublimation Tumbler Wrap Bundle, a collection of 8 professionally designed, \
print-ready PNG wrap files sized for the 20oz skinny tumbler. Each design is a full-bleed, \
seamless wrap with rich saturated colors built to look gorgeous after sublimation printing.

━━━━━━━━━━━━━━━━━━━━━━━━
🗂️ WHAT'S INCLUDED (8 Designs)
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Football Mom — forest green with autumn florals & retro varsity text
✅ Cheer Mom — deep purple with gold pom-poms & sparkle accents
✅ Dog Mom — terracotta boho with golden retriever portrait & floral wreath
✅ Nurse Life — navy with teal medical cross & botanical elements
✅ Teacher Life — golden yellow with retro apple & classroom icons
✅ Girl Mom — deep plum with lush rose bouquet & butterfly accents
✅ Boy Mom — midnight navy with adventure badge & lightning bolts
✅ Mama Mode — burnt sienna 70s groovy with kawaii sunflower badge

Each file: PNG, 2798×2438px (9.325×8.125 inches), 300 DPI, sRGB, ready to print.

━━━━━━━━━━━━━━━━━━━━━━━━
📐 SIZING & COMPATIBILITY
━━━━━━━━━━━━━━━━━━━━━━━━
★ 20oz Skinny Tumbler — perfectly sized (9.33" × 8.33" @ 300 DPI)
★ Compatible with Sawgrass, Epson EcoTank/F170, and any sublimation printer
★ Works with all sublimation blanks: Tumbler Guys, TumblerPro, ORCA, Libbey
★ Resize in Photoshop or Canva for 30oz, 40oz, mug, or can cooler

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━
1. Download and unzip your files instantly after purchase
2. Open in Photoshop, Canva, or any image editor — crop/resize as needed
3. Print on sublimation paper using a sublimation printer
4. Heat press onto your sublimation blank tumbler at 400°F for 60 seconds
5. Peel, reveal, enjoy your gorgeous tumbler!

━━━━━━━━━━━━━━━━━━━━━━━━
🏷️ COMMERCIAL USE LICENSE
━━━━━━━━━━━━━━━━━━━━━━━━
✅ You MAY sell finished physical products (tumblers, mugs, shirts) made with these designs
✅ You MAY use for Cricut/heat press small business production
❌ You may NOT resell, redistribute, or share the digital PNG files
❌ You may NOT use to create other digital products for resale

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: PNG (8 files)
• Size: 2798 × 2438 px (9.325 × 8.125 inches) — MakerFlo / standard 20oz straight template
• Resolution: 300 DPI
• Color profile: sRGB
• Delivery: Instant digital download via Etsy — ZIP file

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Can I resize these for a 30oz tumbler?
A: Yes! Open in Canva, Photoshop, or any editor and resize to your blank's dimensions. The 300 DPI resolution gives you plenty of quality to scale up.

Q: Do these work with Cricut Mug Press?
A: Yes — these PNGs can be used with any sublimation printer and blank. Size to fit your specific blank.

Q: Can I sell the finished tumblers?
A: Absolutely — commercial use is included. Sell unlimited finished physical products.

Q: What's NOT included?
A: Physical tumblers, sublimation paper, ink, or heat press equipment. Digital file only.

Q: Do I need to mirror the image before printing?
A: Yes! Always mirror/flip your image horizontally before printing on sublimation paper. This is true for ALL sublimation designs — the transfer reverses the image during pressing.

Q: I'm new to sublimation — will these work with my setup?
A: Yes! These files are sized to the standard 20oz skinny template. If you can print and press, these will work. Remember to mirror-print before pressing.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Commercial use license included for physical finished goods only. \
Digital files may not be shared, resold, or redistributed.
"""


README_TEXT = """\
OnBrandCraftz — Mom Life Sublimation Tumbler Wrap Bundle
=========================================================

Thank you for your purchase! This ZIP contains 8 PNG sublimation wrap designs.

FILES INCLUDED
--------------
1. sublimation_football_mom_20oz.png
2. sublimation_cheer_mom_20oz.png
3. sublimation_dog_mom_20oz.png
4. sublimation_nurse_life_20oz.png
5. sublimation_teacher_life_20oz.png
6. sublimation_girl_mom_20oz.png
7. sublimation_boy_mom_20oz.png
8. sublimation_mama_mode_20oz.png

SPECIFICATIONS
--------------
- Size: 2799 x 2499 pixels (9.33" x 8.33" @ 300 DPI)
- Fits: 20oz Skinny Tumbler (standard template)
- Format: PNG, sRGB color profile
- Resolution: 300 DPI — print-ready

HOW TO PRINT
------------
1. Open PNG in Photoshop or any image editor
2. Set print size to 9.33" x 8.33" at 300 DPI
3. Print on sublimation paper (mirror image if required by your setup)
4. Heat press onto sublimation-coated tumbler at 400°F / 205°C for 60 seconds
5. Remove paper while warm for best color transfer

RESIZING FOR OTHER BLANKS
--------------------------
- 30oz tumbler:  9.5" x 9.1" (resize in Photoshop/Canva)
- 40oz tumbler:  9.5" x 12"  (resize as needed)
- 11oz mug:      3.8" x 8.5" (resize as needed)
- 15oz mug:      4.2" x 9.5" (resize as needed)

LICENSE
-------
✅ Personal use: YES
✅ Sell finished physical products (tumblers, mugs): YES — unlimited
❌ Resell or share digital files: NOT PERMITTED

Questions? Email: Printing3dthings@outlook.com

© OnBrandCraftz — All rights reserved.
"""


# ── Step 1: Build ZIP ─────────────────────────────────────────────────────────
def build_zip():
    print("Building ZIP...")
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", README_TEXT)
        for name, filename in DESIGNS:
            src = os.path.join(SAMPLES_DIR, filename)
            if not os.path.exists(src):
                raise FileNotFoundError(f"Missing design file: {src}")
            zf.write(src, filename)
            print(f"  Added: {filename}")
    size_mb = os.path.getsize(ZIP_PATH) / 1024 / 1024
    print(f"ZIP built: {ZIP_PATH} ({size_mb:.1f} MB)")
    if size_mb > 20:
        print("WARNING: ZIP exceeds Etsy's 20MB limit — compression needed")
    return ZIP_PATH


# ── Step 2: Generate listing photos ──────────────────────────────────────────
def make_collage_photo(designs: list[tuple], out_path: str, size=2400):
    """
    Photo 1 — Hero collage: 2×4 grid of all 8 designs at thumbnail scale,
    arranged on a deep charcoal background with the bundle title as text.
    """
    img = Image.new("RGB", (size, size), color="#1A1A1A")
    draw = ImageDraw.Draw(img)

    cols, rows = 4, 2
    pad = 28
    cell_w = (size - pad * (cols + 1)) // cols
    cell_h = (size - pad * (rows + 1) - 200) // rows  # 200px for title area

    for i, (name, filename) in enumerate(designs):
        src_path = os.path.join(SAMPLES_DIR, filename)
        wrap = Image.open(src_path).convert("RGB")
        wrap_thumb = wrap.resize((cell_w, cell_h), Image.LANCZOS)
        col = i % cols
        row = i // cols
        x = pad + col * (cell_w + pad)
        y = 160 + pad + row * (cell_h + pad)
        img.paste(wrap_thumb, (x, y))

        # Design name label beneath each thumbnail
        try:
            font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        except Exception:
            font_sm = ImageFont.load_default()
        label_y = y + cell_h + 6
        bbox = draw.textbbox((0, 0), name, font=font_sm)
        lw = bbox[2] - bbox[0]
        draw.text((x + (cell_w - lw) // 2, label_y), name, fill="#CCCCCC", font=font_sm)

    # Title banner at top
    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except Exception:
        font_lg = font_sub = ImageFont.load_default()

    title = "MOM LIFE SUBLIMATION BUNDLE"
    subtitle = "8 Designs · 20oz Skinny · 300 DPI · Instant Download"

    tb = draw.textbbox((0, 0), title, font=font_lg)
    draw.text(((size - (tb[2]-tb[0])) // 2, 28), title, fill="#FFFFFF", font=font_lg)
    sb = draw.textbbox((0, 0), subtitle, font=font_sub)
    draw.text(((size - (sb[2]-sb[0])) // 2, 96), subtitle, fill="#AAAAAA", font=font_sub)

    img.save(out_path, "JPEG", quality=92, dpi=(300, 300))
    print(f"  Photo saved: {os.path.basename(out_path)}")
    return out_path


def make_single_showcase(design_name: str, filename: str, out_path: str, size=2400):
    """Individual design showcase on dark background with name and specs."""
    img = Image.new("RGB", (size, size), color="#111111")
    draw = ImageDraw.Draw(img)

    src = os.path.join(SAMPLES_DIR, filename)
    wrap = Image.open(src).convert("RGB")

    # Fit the wrap inside the square with 5% padding, centered
    pad = int(size * 0.05)
    max_w = size - pad * 2
    ow, oh = wrap.size
    scale = min(max_w / ow, (size - 200) / oh)
    nw, nh = int(ow * scale), int(oh * scale)
    wrap_resized = wrap.resize((nw, nh), Image.LANCZOS)
    x = (size - nw) // 2
    y = (size - nh - 60) // 2
    img.paste(wrap_resized, (x, y))

    # Label
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except Exception:
        font = font_sm = ImageFont.load_default()

    label_y = y + nh + 18
    tb = draw.textbbox((0, 0), design_name.upper(), font=font)
    draw.text(((size - (tb[2]-tb[0])) // 2, label_y), design_name.upper(),
              fill="#FFFFFF", font=font)
    spec = "20oz Skinny · 2799×2499px · 300 DPI · PNG"
    sb = draw.textbbox((0, 0), spec, font=font_sm)
    draw.text(((size - (sb[2]-sb[0])) // 2, label_y + 58), spec,
              fill="#888888", font=font_sm)

    img.save(out_path, "JPEG", quality=92, dpi=(300, 300))
    print(f"  Photo saved: {os.path.basename(out_path)}")
    return out_path


def generate_listing_photos():
    print("Generating listing photos...")
    photos = []

    # Photo 1: Full grid collage (hero)
    p = os.path.join(PHOTOS_DIR, "photo_01_hero_collage.jpg")
    make_collage_photo(DESIGNS, p)
    photos.append(p)

    # Photos 2–9: Individual design showcases
    for i, (name, filename) in enumerate(DESIGNS, start=2):
        p = os.path.join(PHOTOS_DIR, f"photo_{i:02d}_{name.lower().replace(' ', '_')}.jpg")
        make_single_showcase(name, filename, p)
        photos.append(p)

    # Photo 10: Specs/what's included graphic
    p = os.path.join(PHOTOS_DIR, "photo_10_specs.jpg")
    _make_specs_photo(p)
    photos.append(p)

    return photos


def _make_specs_photo(out_path: str, size=2400):
    img = Image.new("RGB", (size, size), color="#0F0F0F")
    draw = ImageDraw.Draw(img)
    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except Exception:
        font_lg = font_md = font_sm = ImageFont.load_default()

    y = 180
    title = "WHAT YOU GET"
    tb = draw.textbbox((0, 0), title, font=font_lg)
    draw.text(((size - (tb[2]-tb[0])) // 2, y), title, fill="#FFFFFF", font=font_lg)
    y += 130

    specs = [
        ("8 PNG Wrap Designs",       "#F59E0B"),
        ("2799 × 2499 px Each",      "#34D399"),
        ("300 DPI — Print Ready",    "#34D399"),
        ("sRGB Color Profile",       "#34D399"),
        ("20oz Skinny Template",     "#34D399"),
        ("Commercial Use Included",  "#34D399"),
        ("Instant Download — ZIP",   "#F59E0B"),
    ]
    for spec_text, color in specs:
        tb = draw.textbbox((0, 0), f"✓  {spec_text}", font=font_md)
        draw.text(((size - (tb[2]-tb[0])) // 2, y), f"✓  {spec_text}",
                  fill=color, font=font_md)
        y += 90

    y += 40
    footer = "OnBrandCraftz"
    fb = draw.textbbox((0, 0), footer, font=font_sm)
    draw.text(((size - (fb[2]-fb[0])) // 2, y), footer, fill="#555555", font=font_sm)

    img.save(out_path, "JPEG", quality=92)
    print(f"  Photo saved: {os.path.basename(out_path)}")


# ── Step 3–6: Publish to Etsy ────────────────────────────────────────────────
def publish(photos: list[str], zip_path: str):
    client = EtsyAPIClient()

    # Validate tag lengths
    for tag in TAGS:
        assert len(tag) <= 20, f"Tag too long ({len(tag)}): '{tag}'"
    assert len(TITLE) <= 140, f"Title too long: {len(TITLE)}"

    print("\nCreating Etsy listing draft...")
    listing = client.create_listing({
        "title":       TITLE,
        "description": DESCRIPTION,
        "price":       PRICE,
        "quantity":    999,
        "tags":        TAGS,
        "taxonomy_id": 2078,   # Digital Files (Craft Supplies & Tools > Patterns & How To)
        "type":        "download",
        "is_digital":  True,
    })
    listing_id = listing["listing_id"]
    print(f"  Listing created: {listing_id}")

    print("Uploading listing photos...")
    for rank, photo_path in enumerate(photos, start=1):
        try:
            client.upload_listing_image(listing_id, photo_path, rank=rank)
            print(f"  Photo {rank}/10 uploaded")
            time.sleep(0.5)
        except Exception as e:
            print(f"  WARNING photo {rank}: {e}")

    print("Uploading ZIP digital file...")
    client.upload_listing_file(listing_id, zip_path)
    print("  ZIP uploaded")

    print("Activating listing...")
    client.update_listing(listing_id, {"state": "active"})
    print(f"\n✅ Listing live: https://www.etsy.com/listing/{listing_id}")
    return listing_id


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("OnBrandCraftz — Sublimation Pack Publisher")
    print("=" * 60)

    zip_path  = build_zip()
    photos    = generate_listing_photos()
    listing_id = publish(photos, zip_path)

    print(f"\nDone. Listing ID: {listing_id}")
    print(f"ZIP: {zip_path}")
    print(f"Photos: {PHOTOS_DIR}")


if __name__ == "__main__":
    main()
