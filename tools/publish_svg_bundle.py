#!/usr/bin/env python3
"""
publish_svg_bundle.py

Publishes a generated SVG bundle to Etsy as a digital listing.
Reads the manifest.json from a completed generate_svg_designs.py run,
creates the listing, uploads all 10 listing photos, uploads the buyer ZIP,
then activates the listing.

Usage:
  python tools/publish_svg_bundle.py western
  python tools/publish_svg_bundle.py floral_wreath mama_scripts
  python tools/publish_svg_bundle.py --all
"""

import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Parse .env manually — never use load_dotenv()
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
with open(_env_path) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from pathlib import Path
from etsy_api import EtsyAPIClient, EtsyAPIError

BUNDLES_DIR = Path("data/svg_bundles")

# ── Per-bundle listing content ────────────────────────────────────────────────

LISTING_CONTENT = {

    "western": {
        "title": "Western SVG Bundle 20 Designs Cricut Silhouette Cut Files Instant Download",
        "tags": [
            "western svg bundle",   "cricut svg files",      "silhouette cut file",
            "western cut file",     "cowgirl svg",           "country svg bundle",
            "cowboy hat svg",       "svg bundle cricut",     "vinyl cut file",
            "western shirt design", "tote bag svg",          "instant download svg",
            "svg for cricut",
        ],
        "price": 7.99,
        "description": """\
🤠 20 stunning western cut file designs in one instant download — ready for your Cricut, Silhouette, and every project you love!

Meet the Wild West SVG Bundle, a collection of 20 professionally designed cut files for t-shirts, tote bags, mugs, wood signs, and more. Every design is fully scalable vector art with crisp clean edges — no jagged lines, no cleanup needed.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 20 SVG files — Cricut Design Space & Silhouette Studio compatible
✅ 20 PNG files — high-resolution 300 DPI for sublimation & print use
✅ Designs include: Wild Heart, Yeehaw, Cowgirl Up, Desert Rose, Prairie Girl, Southern Soul, Rodeo Queen, Boot Scootin, Blessed Country, Howdy, Free Spirit, Ranch Wife, Country Roads, Sunflower Farm, Wild and Free, Roping Hearts, Simple Life, Good Ol Days, True Grit, Home Grown
✅ README with full usage instructions
✅ Instant digital download — no waiting, no shipping

━━━━━━━━━━━━━━━━━━━━━━━━
✂️ COMPATIBLE SOFTWARE
━━━━━━━━━━━━━━━━━━━━━━━━
★ Cricut Design Space (all Cricut machines)
★ Silhouette Studio (all Silhouette machines)
★ Adobe Illustrator
★ Inkscape (free)
★ Canva Pro

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 PERFECT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Iron-on vinyl t-shirts and sweatshirts
• Canvas tote bags and market bags
• Ceramic mugs and tumblers with vinyl decals
• Wood signs and home decor
• Sublimation projects (use the PNG files)
• Stickers, decals, and car graphics

━━━━━━━━━━━━━━━━━━━━━━━━
⚡ HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase and download your ZIP file instantly from Etsy
2. Unzip to find your SVG and PNG folders
3. Open SVG in Cricut Design Space or Silhouette Studio
4. Resize to your project size and cut!
💡 Pro tip: Mirror your design when using iron-on vinyl!

━━━━━━━━━━━━━━━━━━━━━━━━
📜 LICENSE
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Personal use — unlimited personal projects
✅ Small commercial use — sell finished physical items you make (up to 100 units per design)
❌ Not for resale as digital files or templates
❌ Not for Print-on-Demand platforms (Merch by Amazon, Redbubble, etc.)
❌ Not for sharing, redistributing, or sublicensing

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Which Cricut machines work with these files?
A: All of them — Cricut Maker, Maker 3, Explore Air 2, Explore 3, Joy, and Joy Xtra.

Q: Do these work with Silhouette Cameo?
A: Yes! Open the SVG file directly in Silhouette Studio Designer Edition or higher.

Q: Can I use these on a sublimation tumbler?
A: Yes — use the PNG files for sublimation. The designs are pre-colored at 300 DPI.

Q: Is this a physical item?
A: No — this is a digital download only. You receive the ZIP file instantly after purchase.

Q: Can I sell items I make with these designs?
A: Yes, up to 100 finished physical items per design. You cannot resell the digital files.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal and small commercial use. Not for digital resale or redistribution.
""",
    },

    "floral_wreath": {
        "title": "Floral Wreath SVG Bundle 20 Designs Cricut Botanical Cut Files Instant Download",
        "tags": [
            "floral wreath svg",    "botanical svg bundle",  "cricut svg files",
            "silhouette cut file",  "flower wreath svg",     "boho svg bundle",
            "wildflower svg",       "svg bundle cricut",     "wreath svg cricut",
            "floral cut file",      "tote bag svg",          "instant download svg",
            "svg for cricut",
        ],
        "price": 7.99,
        "description": """\
🌸 20 gorgeous botanical wreath cut file designs in one instant download — perfect for every floral project!

Meet the Boho Floral Wreath SVG Bundle, a collection of 20 beautifully detailed botanical cut files featuring peonies, eucalyptus, lavender, wildflowers, and more. Every design is clean vector art that cuts beautifully on any machine.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 20 SVG files — Cricut Design Space & Silhouette Studio compatible
✅ 20 PNG files — high-resolution 300 DPI for sublimation & print use
✅ Designs include: Gather Here, Wildflower Ring, Eucalyptus Crown, Sunflower Circle, Lavender Dreams, Garden Party, Bloom Where Planted, She Blossoms, Flower Market, Pampas and Roses, Morning Glory, Wild Garden, Botanical Crown, Honey Bee Garden, Spring Forward, Dusty Blooms, Monogram Frame, Garden Gate, Meadow Ring, Forever Blooming
✅ README with full usage instructions
✅ Instant digital download — no waiting, no shipping

━━━━━━━━━━━━━━━━━━━━━━━━
✂️ COMPATIBLE SOFTWARE
━━━━━━━━━━━━━━━━━━━━━━━━
★ Cricut Design Space (all Cricut machines)
★ Silhouette Studio (all Silhouette machines)
★ Adobe Illustrator
★ Inkscape (free)
★ Canva Pro

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 PERFECT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• T-shirts, sweatshirts, and tote bags with iron-on vinyl
• Mugs and tumblers with vinyl decals
• Wedding and bridal party gifts
• Nursery and home decor wood signs
• Sublimation projects (use the PNG files)
• Paper crafting, scrapbooking, card making

━━━━━━━━━━━━━━━━━━━━━━━━
⚡ HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase and download your ZIP file instantly from Etsy
2. Unzip to find your SVG and PNG folders
3. Open SVG in Cricut Design Space or Silhouette Studio
4. Resize to your project size and cut!
💡 Pro tip: Mirror your design when using iron-on vinyl!

━━━━━━━━━━━━━━━━━━━━━━━━
📜 LICENSE
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Personal use — unlimited personal projects
✅ Small commercial use — sell finished physical items you make (up to 100 units per design)
❌ Not for resale as digital files or templates
❌ Not for Print-on-Demand platforms
❌ Not for sharing, redistributing, or sublicensing

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Which Cricut machines work with these files?
A: All of them — Cricut Maker, Maker 3, Explore Air 2, Explore 3, Joy, and Joy Xtra.

Q: Are these good for layered vinyl projects?
A: Yes — the SVG layers are separated by color, making layered vinyl projects easy.

Q: Can I use the Monogram Frame design with my own letter?
A: Absolutely! Open in Cricut or Illustrator and add any letter in the center.

Q: Is this a physical item?
A: No — digital download only. ZIP file delivered instantly after purchase.

Q: Can I sell items I make with these designs?
A: Yes, up to 100 finished physical items per design. You cannot resell the digital files.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal and small commercial use. Not for digital resale or redistribution.
""",
    },

    "mama_scripts": {
        "title": "Mama SVG Bundle 20 Mom Life Designs Cricut Silhouette Cut Files Instant Download",
        "tags": [
            "mama svg bundle",      "mom life svg",          "cricut svg files",
            "silhouette cut file",  "mama cut file",         "mom svg bundle",
            "mom shirt svg",        "svg bundle cricut",     "mama shirt design",
            "mom tshirt svg",       "tote bag svg",          "instant download svg",
            "svg for cricut",
        ],
        "price": 7.99,
        "description": """\
💕 20 heartfelt mama and mom life cut file designs in one instant download — because every mama deserves a cute shirt!

Meet the Mama SVG Bundle, a collection of 20 beautifully hand-lettered cut files perfect for t-shirts, sweatshirts, tote bags, mugs, and every mama craft project imaginable.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 20 SVG files — Cricut Design Space & Silhouette Studio compatible
✅ 20 PNG files — high-resolution 300 DPI for sublimation & print use
✅ Designs include: Mama, Blessed Mama, Mom Life, World's Best Mom, Motherhood, She is Strong, Mama Bear, Mom Boss, Love You to the Moon, Favorite People, Raising Good Humans, Mom Fuel, Chaos Coordinator, Tired but Grateful, Girl Mama, Boy Mama, Bonus Mom, Fur Mama, Plant Mama, Cool Mom
✅ README with full usage instructions
✅ Instant digital download — no waiting, no shipping

━━━━━━━━━━━━━━━━━━━━━━━━
✂️ COMPATIBLE SOFTWARE
━━━━━━━━━━━━━━━━━━━━━━━━
★ Cricut Design Space (all Cricut machines)
★ Silhouette Studio (all Silhouette machines)
★ Adobe Illustrator
★ Inkscape (free)
★ Canva Pro

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 PERFECT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Iron-on vinyl t-shirts and sweatshirts
• Canvas tote bags (a mama's best friend!)
• Mugs and tumblers — mama's coffee is sacred
• Mother's Day and birthday gifts
• Sublimation projects (use the PNG files)
• Wood signs, pillows, and home decor

━━━━━━━━━━━━━━━━━━━━━━━━
⚡ HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase and download your ZIP file instantly from Etsy
2. Unzip to find your SVG and PNG folders
3. Open SVG in Cricut Design Space or Silhouette Studio
4. Resize to your project size and cut!
💡 Pro tip: Mirror your design when using iron-on vinyl!

━━━━━━━━━━━━━━━━━━━━━━━━
📜 LICENSE
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Personal use — unlimited personal projects
✅ Small commercial use — sell finished physical items you make (up to 100 units per design)
❌ Not for resale as digital files or templates
❌ Not for Print-on-Demand platforms
❌ Not for sharing, redistributing, or sublicensing

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Which Cricut machines work with these files?
A: All of them — Cricut Maker, Maker 3, Explore Air 2, Explore 3, Joy, and Joy Xtra.

Q: Are these good for weeding? Some mama designs have fine text.
A: Yes — all designs are optimized for clean weeding. Fine text is kept at a readable stroke weight.

Q: Can I make these into gifts to sell?
A: Yes! You can sell finished physical items like shirts, mugs, and totes you make with these designs.

Q: Is this a physical item?
A: No — digital download only. ZIP file delivered instantly after purchase.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal and small commercial use. Not for digital resale or redistribution.
""",
    },

    "retro_groovy": {
        "title": "Retro Groovy SVG Bundle 20 Vintage 70s Cut Files Cricut Silhouette Instant Download",
        "tags": [
            "retro svg bundle",     "groovy svg",            "cricut svg files",
            "silhouette cut file",  "vintage svg bundle",    "70s retro svg",
            "retro shirt design",   "svg bundle cricut",     "groovy cut file",
            "retro tshirt svg",     "tote bag svg",          "instant download svg",
            "svg for cricut",
        ],
        "price": 7.99,
        "description": """\
✌️ 20 retro groovy 70s-inspired cut file designs in one instant download — bring the good vibes to every project!

Meet the Retro Groovy SVG Bundle, a collection of 20 boldly illustrated vintage-style cut files featuring sunbursts, peace signs, mushrooms, rainbows, and all the groovy typography your crafting heart desires.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 20 SVG files — Cricut Design Space & Silhouette Studio compatible
✅ 20 PNG files — high-resolution 300 DPI for sublimation & print use
✅ Designs include: Stay Groovy, Good Vibes Only, Far Out, Peace Love Sunshine, Soul Shine, Flower Power, Cosmic Dreamer, Electric Dreams, Sunshine Always, Groovy Baby, Chill Vibes, Magic Mushroom, Together We Rise, Born Wild, Ride the Wave, Rock and Roll, Wild Child, Summer Lovin, Life is Groovy, Happy Camper
✅ README with full usage instructions
✅ Instant digital download — no waiting, no shipping

━━━━━━━━━━━━━━━━━━━━━━━━
✂️ COMPATIBLE SOFTWARE
━━━━━━━━━━━━━━━━━━━━━━━━
★ Cricut Design Space (all Cricut machines)
★ Silhouette Studio (all Silhouette machines)
★ Adobe Illustrator
★ Inkscape (free)
★ Canva Pro

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 PERFECT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Vintage-style iron-on t-shirts and sweatshirts
• Canvas tote bags and market bags
• Mugs, tumblers, and water bottles with vinyl
• Festival and concert merch projects
• Sublimation tumblers and shirts (use PNG files)
• Retro-themed party decor and signs

━━━━━━━━━━━━━━━━━━━━━━━━
⚡ HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase and download your ZIP file instantly from Etsy
2. Unzip to find your SVG and PNG folders
3. Open SVG in Cricut Design Space or Silhouette Studio
4. Resize to your project size and cut!
💡 Pro tip: Mirror your design when using iron-on vinyl!

━━━━━━━━━━━━━━━━━━━━━━━━
📜 LICENSE
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Personal use — unlimited personal projects
✅ Small commercial use — sell finished physical items you make (up to 100 units per design)
❌ Not for resale as digital files or templates
❌ Not for Print-on-Demand platforms
❌ Not for sharing, redistributing, or sublicensing

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Which Cricut machines work with these files?
A: All of them — Cricut Maker, Maker 3, Explore Air 2, Explore 3, Joy, and Joy Xtra.

Q: Do these work with glitter vinyl?
A: Absolutely — the bold outlines in these retro designs look amazing with glitter HTV.

Q: Can I use these for a small Etsy shop selling shirts?
A: Yes — small commercial use (up to 100 finished items per design) is included.

Q: Is this a physical item?
A: No — digital download only. ZIP file delivered instantly after purchase.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal and small commercial use. Not for digital resale or redistribution.
""",
    },

    "dark_floral": {
        "title": "Dark Floral Gothic SVG Bundle 20 Cut Files Cricut Silhouette Instant Download",
        "tags": [
            "dark floral svg",      "gothic svg bundle",     "cricut svg files",
            "silhouette cut file",  "dark rose svg",         "gothic cut file",
            "dark aesthetic svg",   "svg bundle cricut",     "gothic shirt design",
            "dark floral shirt",    "tote bag svg",          "instant download svg",
            "svg for cricut",
        ],
        "price": 7.99,
        "description": """\
🖤 20 dark floral gothic cut file designs in one instant download — bold, feminine, and unapologetically dramatic!

Meet the Dark Floral Gothic SVG Bundle, a collection of 20 ornately detailed cut files featuring dark roses, thorned vines, gothic frames, luna moths, ravens, and more. Every design is crisp clean vector art ready for your darkest craft projects.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 20 SVG files — Cricut Design Space & Silhouette Studio compatible
✅ 20 PNG files — high-resolution 300 DPI for sublimation & print use
✅ Designs include: She is Fierce, Wicked Bloom, Midnight Garden, Queen of Thorns, Dark Beauty, Haunted Flora, Enchanted Rose, Black Rose Society, Thorns and Roses, Dark Academia, Witchy Blooms, Luna Moth, Gothic Garden, Death Blooms, Shadow and Light, Thorn Crown, Night Owl, Raven and Roses, Dark Forest, Femme Fatale
✅ README with full usage instructions
✅ Instant digital download — no waiting, no shipping

━━━━━━━━━━━━━━━━━━━━━━━━
✂️ COMPATIBLE SOFTWARE
━━━━━━━━━━━━━━━━━━━━━━━━
★ Cricut Design Space (all Cricut machines)
★ Silhouette Studio (all Silhouette machines)
★ Adobe Illustrator
★ Inkscape (free)
★ Canva Pro

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 PERFECT FOR
━━━━━━━━━━━━━━━━━━━━━━━━
• Dark-style iron-on t-shirts and sweatshirts
• Gothic and alternative fashion accessories
• Canvas tote bags with dramatic flair
• Mugs and tumblers with dark vinyl decals
• Halloween and spooky season projects (but gorgeous year-round!)
• Sublimation projects (use the PNG files)

━━━━━━━━━━━━━━━━━━━━━━━━
⚡ HOW TO USE
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase and download your ZIP file instantly from Etsy
2. Unzip to find your SVG and PNG folders
3. Open SVG in Cricut Design Space or Silhouette Studio
4. Resize to your project size and cut!
💡 Pro tip: Mirror your design when using iron-on vinyl!

━━━━━━━━━━━━━━━━━━━━━━━━
📜 LICENSE
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Personal use — unlimited personal projects
✅ Small commercial use — sell finished physical items you make (up to 100 units per design)
❌ Not for resale as digital files or templates
❌ Not for Print-on-Demand platforms
❌ Not for sharing, redistributing, or sublicensing

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Are these good for intricate cutting with fine details?
A: Yes — all designs are optimized for clean cuts. For very fine details, use a fresh blade and slow your cut speed slightly.

Q: Do these work for black HTV on dark shirts?
A: The SVG layers are color-separated, so you can choose any vinyl color. Many customers cut these in white or silver on black shirts for a stunning effect.

Q: Can I use these for Halloween products to sell?
A: Yes — small commercial use is included. These designs sell beautifully year-round, not just at Halloween.

Q: Is this a physical item?
A: No — digital download only. ZIP file delivered instantly after purchase.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal and small commercial use. Not for digital resale or redistribution.
""",
    },
}


# ── Pre-publish quality gate ──────────────────────────────────────────────────

def validate_bundle(bundle_id: str, bundle_dir: Path) -> list[str]:
    errors = []
    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.exists():
        errors.append("manifest.json missing — run generate_svg_designs.py first")
        return errors

    with open(manifest_path) as f:
        manifest = json.load(f)

    if manifest.get("design_count", 0) < 20:
        errors.append(f"Only {manifest.get('design_count')} designs — need 20")

    zip_path = Path(manifest.get("zip_path", ""))
    if not zip_path.exists():
        errors.append(f"ZIP not found: {zip_path}")
    elif zip_path.stat().st_size > 20 * 1024 * 1024:
        errors.append(f"ZIP too large: {zip_path.stat().st_size // 1024 // 1024}MB (Etsy limit 20MB)")

    listing_dir = bundle_dir / "listing_photos"
    photos = sorted(listing_dir.glob("*.jpg"))
    if len(photos) < 2:
        errors.append(f"Only {len(photos)} listing photos — need at least 2")

    content = LISTING_CONTENT.get(bundle_id)
    if not content:
        errors.append(f"No listing content defined for bundle_id '{bundle_id}'")
        return errors

    title = content["title"]
    if len(title) > 70:
        errors.append(f"Title too long: {len(title)} chars (max 70 for mobile ranking)")

    tags = content["tags"]
    if len(tags) < 13:
        errors.append(f"Only {len(tags)} tags — need exactly 13")
    for tag in tags:
        if len(tag) > 20:
            errors.append(f"Tag too long: '{tag}' ({len(tag)} chars, max 20)")

    return errors


# ── Publisher ─────────────────────────────────────────────────────────────────

def publish_bundle(bundle_id: str) -> dict | None:
    bundle_dir = BUNDLES_DIR / bundle_id

    print(f"\n{'='*60}")
    print(f"  Publishing: {bundle_id}")
    print(f"{'='*60}")

    # Validate
    errors = validate_bundle(bundle_id, bundle_dir)
    if errors:
        print(f"\n  ✗ Quality gate FAILED:")
        for e in errors:
            print(f"    — {e}")
        return None

    with open(bundle_dir / "manifest.json") as f:
        manifest = json.load(f)

    content = LISTING_CONTENT[bundle_id]
    zip_path = Path(manifest["zip_path"])
    listing_photos = sorted((bundle_dir / "listing_photos").glob("*.jpg"))

    # Build Etsy client
    client = EtsyAPIClient()

    # Get or create Digital Downloads section
    print("  Getting shop section...")
    section_id = client.get_or_create_section("Digital Downloads")
    print(f"    Section ID: {section_id}")

    # Create the listing as draft
    print("  Creating Etsy listing (draft)...")
    listing_data = {
        "title": content["title"],
        "description": content["description"],
        "price": content["price"],
        "quantity": 999,
        "tags": [t[:20] for t in content["tags"][:13]],
        "materials": [],
        "shipping_profile_id": None,
        "state": "draft",
        "type": "download",
        "who_made": "i_did",
        "when_made": "made_to_order",
        "taxonomy_id": 2078,   # Craft Supplies > Patterns > Digital Files
        "shop_section_id": section_id,
        "is_digital": True,
    }

    listing = client.create_listing(listing_data)
    listing_id = listing["listing_id"]
    print(f"    Listing created: {listing_id}")

    # Upload listing photos
    print(f"  Uploading {len(listing_photos)} listing photos...")
    for rank, photo_path in enumerate(listing_photos[:10], start=1):
        try:
            client.upload_listing_image(listing_id, str(photo_path), rank=rank)
            print(f"    ✓ Photo {rank}: {photo_path.name}")
            time.sleep(0.5)
        except EtsyAPIError as e:
            print(f"    ✗ Photo {rank} failed: {e}")

    # Upload buyer ZIP
    print(f"  Uploading buyer ZIP ({zip_path.stat().st_size // 1024} KB)...")
    try:
        client.upload_listing_file(listing_id, str(zip_path), rank=1)
        print(f"    ✓ ZIP uploaded")
    except EtsyAPIError as e:
        print(f"    ✗ ZIP upload failed: {e}")

    # Activate listing
    print("  Activating listing...")
    try:
        client.update_listing(listing_id, {"state": "active"})
        print(f"    ✓ Listing live: https://www.etsy.com/listing/{listing_id}")
    except EtsyAPIError as e:
        print(f"    ✗ Activation failed: {e} — listing remains as draft")

    # Update manifest
    manifest["etsy_listing_id"] = listing_id
    manifest["status"] = "published"
    manifest["published_url"] = f"https://www.etsy.com/listing/{listing_id}"
    with open(bundle_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n  ✓ {bundle_id} published → listing {listing_id}")
    return manifest


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    run_all = "--all" in sys.argv[1:]

    if not args and not run_all:
        print("Usage: python tools/publish_svg_bundle.py <bundle_id> [bundle_id ...]")
        print("       python tools/publish_svg_bundle.py --all")
        print(f"\nAvailable bundles: western, floral_wreath, mama_scripts, retro_groovy, dark_floral")
        return

    target_ids = list(LISTING_CONTENT.keys()) if run_all else args

    for bundle_id in target_ids:
        if bundle_id not in LISTING_CONTENT:
            print(f"Unknown bundle: {bundle_id}")
            continue
        publish_bundle(bundle_id)


if __name__ == "__main__":
    main()
