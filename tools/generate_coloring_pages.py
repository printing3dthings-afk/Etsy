#!/usr/bin/env python3
"""
generate_coloring_pages.py

Generates themed coloring pages using gpt-image-1 — clean black line art
on white background, zero fills, suitable for printing and coloring.

Two packs are available:
  kawaii     20 kawaii-cute scenes, intricate, decorative border, fills 85-90% of page
  fun_basic  20 fun/adventure scenes — half "basic" (one big bold simple subject,
             lots of white space, no border, great for young kids/quick coloring)
             and half "fun" (playful action scenes, moderate detail, light border)

The previous PIL edge-detection approach was removed (it produced too much fill and
muddy lines). This version generates original artwork directly.

Usage:
    python tools/generate_coloring_pages.py                       # kawaii pack, all 20
    python tools/generate_coloring_pages.py --pack fun_basic       # fun/basic pack, all 20
    python tools/generate_coloring_pages.py --themes 5            # first 5 themes only
    python tools/generate_coloring_pages.py --regen                # force regenerate cached
    python tools/generate_coloring_pages.py --preview              # listing JSON only, no images
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageEnhance

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent.parent.resolve()
COLORING_DIR = BASE / "data" / "digital_products" / "coloring_pages"
SETS_DIR = COLORING_DIR / "sets"
PAGES_PER_SET = 5
# NEW_THEME_SET_SIZE (2026-07-24): the dynamic Scott-typed-theme path (see
# generate_dynamic_theme_set()) always produces exactly this many pages, packaged
# into exactly one ZIP -- deliberately a SEPARATE constant from PAGES_PER_SET,
# which stays 5 and keeps batching the 2 old fixed kawaii/fun_basic packs into
# 4 ZIPs each, untouched (Scott: leave the old packs exactly as they are). Do
# not merge these two constants -- see build_sets()'s batch_size param, which is
# how the two call sites stopped sharing one global.
NEW_THEME_SET_SIZE = 20

# ---------------------------------------------------------------------------
# Style DNA injected into every prompt for consistency
# ---------------------------------------------------------------------------
_STYLE = (
    "STYLE: Professional coloring book illustration. "
    "ONLY clean black lines on pure white background — absolutely ZERO fills, "
    "ZERO shading, ZERO gray tones, ZERO gradients anywhere. "
    "Line weight 2-3px, confident consistent strokes throughout. "
    "Pure #000000 black outlines on pure #FFFFFF white only. "
    "Suitable for printing on A4/letter paper and coloring with colored pencils or markers. "
    "CONSTRAINT: Black lines only. White background. No color. No gray. No text. No watermarks."
)

# ---------------------------------------------------------------------------
# Style DNA for the "fun_basic" pack — bolder/simpler lines for the "basic" tier
# ---------------------------------------------------------------------------
_STYLE_BOLD = (
    "STYLE: Professional coloring book illustration for young children. "
    "ONLY clean black lines on pure white background — absolutely ZERO fills, "
    "ZERO shading, ZERO gray tones, ZERO gradients anywhere. "
    "Line weight 3-4px, extra bold and simple, very few small details. "
    "Pure #000000 black outlines on pure #FFFFFF white only. "
    "Suitable for printing on A4/letter paper and coloring with crayons, colored pencils, or markers. "
    "CONSTRAINT: Black lines only. White background. No color. No gray. No text. No watermarks."
)


def _basic_theme(id_, title, subject):
    """One big, bold, simple subject — generous white space, no border. For young kids / quick coloring."""
    return {
        "id": id_,
        "title": title,
        "prompt": (
            f"SUBJECT: {subject} "
            "COMPOSITION: ONE large, simple subject centered on the page, fills only 50-60% of "
            "the page, generous white space all around it, NO decorative border, minimal or no "
            "background elements. Bold, very easy to color. "
            + _STYLE_BOLD
        ),
    }


def _fun_theme(id_, title, subject, border):
    """Playful action scene — moderate detail, light border. More of a coloring challenge."""
    return {
        "id": id_,
        "title": title,
        "prompt": (
            f"SUBJECT: {subject} "
            f"COMPOSITION: Playful action scene, fills 75% of the page, moderate detail — "
            f"fun and energetic but not overwhelming. Light decorative {border} border. "
            + _STYLE
        ),
    }


FUN_BASIC_THEMES = [
    _basic_theme("CB001", "Big Friendly Dino", "A huge friendly cartoon T-Rex standing tall, big round eyes, "
                 "stubby little arms, one small fern leaf beside its feet."),
    _fun_theme("CB002", "Race Car Rally", "A sleek race car speeding past a checkered flag, racing stripes, "
               "motion/speed lines trailing behind, a trophy in the background.", "checkered-flag"),
    _basic_theme("CB003", "Friendly Chunky Robot", "One big chunky friendly robot with a square head, round "
                 "antenna, big buttons on its chest, simple little feet."),
    _fun_theme("CB004", "Pirate Treasure Hunt", "A pirate ship sailing toward a small island, an open treasure "
               "chest spilling coins and gems, a parrot on the mast, a palm tree on the island.", "rope-and-anchor"),
    _basic_theme("CB005", "Big Happy Whale", "One large happy whale leaping with a small water spout, a couple "
                 "of simple bubble shapes nearby, nothing else on the page."),
    _fun_theme("CB006", "Superhero Squad", "Two kid superheroes flying side by side with capes flowing, fists "
               "forward, a simple city skyline silhouette below, comic-style motion lines.", "star-burst"),
    _basic_theme("CB007", "Tractor on the Farm", "One big friendly tractor with large wheels, a smiling sun "
                 "overhead, a short simple fence line in the background."),
    _fun_theme("CB008", "Knight and Dragon", "A knight on horseback with a lance facing a small friendly dragon "
               "puffing a heart-shaped breath, a castle with turrets in the background.", "shield-and-banner"),
    _basic_theme("CB009", "Smiling Sun and Clouds", "One giant smiling sun with simple ray lines, two small "
                 "puffy clouds floating beside it, nothing else on the page."),
    _fun_theme("CB010", "Jungle Safari Jeep", "An open safari jeep driving past a friendly elephant, a monkey "
               "swinging from a tree branch, large palm leaves framing the scene.", "leaf-vine"),
    _fun_theme("CB011", "Monster Truck Mania", "A giant monster truck mid-jump over a dirt ramp, dust clouds "
               "and motion lines behind the wheels, a small checkered finish flag in the background.", "tire-tread"),
    _basic_theme("CB012", "Friendly Monster Buddies", "Two simple round friendly monsters with big eyes and "
                 "tiny horns, standing side by side, holding hands, nothing else on the page."),
    _basic_theme("CB013", "Soccer Star", "One kid mid-kick toward a soccer ball, a simple goal net behind them, "
                 "no crowd or background detail."),
    _fun_theme("CB014", "Submarine Deep Dive", "A round-windowed submarine exploring near a sunken treasure "
               "chest, a few curious fish swimming by, bubbles rising, simple coral shapes.", "bubble-and-wave"),
    _fun_theme("CB015", "Camping Under the Stars", "A pointed tent beside a crackling campfire with a "
               "marshmallow on a stick, a few simple pine trees, stars scattered in the sky.", "pine-tree"),
    _basic_theme("CB016", "Big Rocket Blast Off", "One large rocket ship blasting upward with a simple flame "
                 "trail, three or four small stars scattered around it, nothing else on the page."),
    _fun_theme("CB017", "Construction Crew", "A bulldozer, a crane, and a dump truck working together at a "
               "job site, a small pile of dirt and a traffic cone, simple background hills.", "caution-stripe"),
    _basic_theme("CB018", "Sleepy Dragon Nap", "One small dragon curled up asleep with closed eyes, a single "
                 "flower resting beside its tail, nothing else on the page."),
    _fun_theme("CB019", "Circus Big Top Fun", "A circus tent with pennant flags, a clown juggling three balls, "
               "an elephant balancing on a striped ball, simple bunting in the background.", "bunting-flag"),
    _basic_theme("CB020", "Round Owl Friend", "One simple round owl made of big bold circular shapes — big "
                 "eyes, tiny beak, two simple wing shapes — sitting alone with nothing else on the page."),
]


# ---------------------------------------------------------------------------
# 20 kawaii-themed coloring page subjects
# ---------------------------------------------------------------------------
COLORING_THEMES = [
    {
        "id": "CP001",
        "title": "Kawaii Garden Party",
        "prompt": (
            "SUBJECT: Charming kawaii garden scene — adorable flower characters with big sparkly eyes "
            "and rosy cheeks, a tiny watering can with a smile, mushrooms with polka-dot caps, a butterfly "
            "with heart-patterned wings, bumble bees, sunflowers, and a garden gate covered in vines. "
            "COMPOSITION: Subject fills 85% of the page. Decorative floral vine border around all four edges. "
            "Medium detail — satisfying to color but not overwhelming for beginners. "
            + _STYLE
        ),
    },
    {
        "id": "CP002",
        "title": "Kawaii Ocean Friends",
        "prompt": (
            "SUBJECT: Magical underwater kawaii scene — a smiling whale with big round eyes, a cute octopus "
            "with curly tentacles, starfish with kawaii faces, a clownfish peeking from coral, a seahorse "
            "with decorative fin patterns, jellyfish with flowing tendrils, shells, and coral reef details. "
            "COMPOSITION: Fills 85% of the page. Wave and bubble border around all edges. "
            + _STYLE
        ),
    },
    {
        "id": "CP003",
        "title": "Kawaii Cat Café",
        "prompt": (
            "SUBJECT: Cozy café interior with kawaii cats — cats sitting at round tables with steaming mugs, "
            "a cat barista behind the counter, a cat in chef hat holding a pastry tray, windows with curtains, "
            "hanging pendant lights, a menu board, shelves with books and plants, a large espresso machine. "
            "COMPOSITION: Fills 85% of the page. Coffee cup and star border. "
            + _STYLE
        ),
    },
    {
        "id": "CP004",
        "title": "Kawaii Floral Mandala",
        "prompt": (
            "SUBJECT: Intricate circular floral mandala with kawaii elements — center is a large kawaii flower "
            "face surrounded by radiating petal layers, leaves, dots, tiny stars, small hearts, and geometric "
            "patterns. Design is radially symmetrical and highly detailed. "
            "COMPOSITION: Mandala centered, fills 90% of page. Light corner flourishes. "
            + _STYLE
        ),
    },
    {
        "id": "CP005",
        "title": "Kawaii Forest Animals",
        "prompt": (
            "SUBJECT: Enchanted forest with kawaii woodland animals — a fox with a fluffy tail, a deer with "
            "flower antlers, a raccoon holding a tiny lantern, an owl with heart eyes perched on a branch, "
            "mushroom houses, a stream with stepping stones, fireflies, and tall trees with detailed bark. "
            "COMPOSITION: Fills 85% of the page. Forest leaf and acorn border. "
            + _STYLE
        ),
    },
    {
        "id": "CP006",
        "title": "Kawaii Bakery Treats",
        "prompt": (
            "SUBJECT: Magical bakery display with kawaii food characters — a giant layer cake with a happy face, "
            "cupcakes with crown toppings, macarons stacked with blush cheeks, a donut with glaze drips and "
            "sparkle eyes, croissants, cinnamon rolls, and cookie jars with cute expressions. "
            "COMPOSITION: Fills 85% of the page. Bunting banner and star border. "
            + _STYLE
        ),
    },
    {
        "id": "CP007",
        "title": "Kawaii Celestial Night",
        "prompt": (
            "SUBJECT: Magical celestial kawaii scene — a large crescent moon with a sleepy kawaii face, stars "
            "of varying sizes with expressions, a planet with Saturn-style rings, a comet trailing sparkles, "
            "a cute rocket ship, shooting stars, and swirling galaxy patterns. "
            "COMPOSITION: Fills 85% of the page. Star and moon crescent border. "
            + _STYLE
        ),
    },
    {
        "id": "CP008",
        "title": "Kawaii Spring Meadow",
        "prompt": (
            "SUBJECT: Blooming spring meadow — kawaii flower characters with smiling faces, a bunny wearing "
            "a flower crown, butterflies with intricate wing patterns, a dragonfly, a ladybug on a leaf, "
            "sunflowers, cherry blossom branch, detailed grass textures, and a rainbow arc. "
            "COMPOSITION: Fills 85% of the page. Daisy chain border. "
            + _STYLE
        ),
    },
    {
        "id": "CP009",
        "title": "Kawaii Cozy Reading Nook",
        "prompt": (
            "SUBJECT: Cozy interior reading scene — a kawaii girl sitting in a window seat reading a big book, "
            "bookshelves packed with books, a sleeping cat on a pillow, fairy lights along shelves, a teapot "
            "and teacup with steam, potted houseplants, a lantern, and patterned curtains. "
            "COMPOSITION: Fills 85% of the page. Book and star border. "
            + _STYLE
        ),
    },
    {
        "id": "CP010",
        "title": "Kawaii Autumn Harvest",
        "prompt": (
            "SUBJECT: Charming autumn harvest scene — kawaii pumpkin characters with friendly faces, a scarecrow "
            "with patched clothes, apple trees with detailed bark, fallen maple and oak leaves, a basket of "
            "harvest vegetables, acorns, pine cones, a cozy lantern, and a wooden wagon. "
            "COMPOSITION: Fills 85% of the page. Leaf and acorn border. "
            + _STYLE
        ),
    },
    {
        "id": "CP011",
        "title": "Kawaii Mermaid Kingdom",
        "prompt": (
            "SUBJECT: Magical mermaid underwater kingdom — a kawaii mermaid with detailed scale pattern on tail, "
            "a coral castle with shell turrets, treasure chests, schools of small fish with kawaii faces, a "
            "sea turtle with patterned shell, dolphins, pearl clusters, and ornate kelp forest. "
            "COMPOSITION: Fills 85% of the page. Shell and wave border. "
            + _STYLE
        ),
    },
    {
        "id": "CP012",
        "title": "Kawaii Birthday Celebration",
        "prompt": (
            "SUBJECT: Festive birthday party — kawaii characters in party hats, a multi-tier birthday cake with "
            "candles and decorations, balloons with faces, gift boxes with elaborate bows and ribbon patterns, "
            "confetti shapes (stars, hearts, circles), bunting flags, and a kawaii piñata. "
            "COMPOSITION: Fills 85% of the page. Balloon and confetti border. "
            + _STYLE
        ),
    },
    {
        "id": "CP013",
        "title": "Kawaii Magical Witch",
        "prompt": (
            "SUBJECT: Whimsical kawaii witch — a cute witch in a star-covered cloak and pointed hat, a magical "
            "bubbling cauldron, a black cat with moon collar, potion bottles on shelves, a broomstick with "
            "ribbons, ornate spell books, crystals, floating sparkle stars, and a crescent moon window. "
            "COMPOSITION: Fills 85% of the page. Moon and star border. "
            + _STYLE
        ),
    },
    {
        "id": "CP014",
        "title": "Kawaii Botanical Bouquet",
        "prompt": (
            "SUBJECT: Elaborate hand-tied floral bouquet — roses with detailed petal layering, dahlias, peonies, "
            "tulips, wildflowers, eucalyptus sprigs, baby's breath, fern leaves, and decorative ribbon at base. "
            "Some flowers have small kawaii faces peeking from the center. Intricate botanical illustration style. "
            "COMPOSITION: Large bouquet centered, fills 90% of page. Tiny floral sprig corner accents. "
            + _STYLE
        ),
    },
    {
        "id": "CP015",
        "title": "Kawaii Dinosaur World",
        "prompt": (
            "SUBJECT: Kawaii prehistoric scene — a T-Rex with big round eyes and stubby arms, a Brachiosaurus "
            "nibbling a palm tree, a Triceratops with flower crown, a baby Stegosaurus with heart-shaped plates, "
            "a Pterodactyl flying overhead, tropical plants, giant ferns, and a gentle volcano background. "
            "COMPOSITION: Fills 85% of the page. Fossil and tropical leaf border. "
            + _STYLE
        ),
    },
    {
        "id": "CP016",
        "title": "Kawaii Animal Tea Party",
        "prompt": (
            "SUBJECT: Elegant kawaii tea party — a round garden table set with detailed teacups and saucers, "
            "a floral-patterned teapot, kawaii animals in fancy outfits (a bunny, a bear, a fox) sitting in "
            "chairs, a tiered cake stand, flower centerpiece, sandwiches, scones, and garden background. "
            "COMPOSITION: Fills 85% of the page. Teacup and flower border. "
            + _STYLE
        ),
    },
    {
        "id": "CP017",
        "title": "Kawaii Winter Wonderland",
        "prompt": (
            "SUBJECT: Magical winter scene — kawaii snowman with scarf and top hat, a reindeer with ornate "
            "decorated antlers, snow-covered pine trees with detailed branch patterns, a cozy cabin with warm "
            "window glow lines, a mug of hot cocoa with marshmallows, snowflakes with unique crystal patterns. "
            "COMPOSITION: Fills 85% of the page. Snowflake and holly leaf border. "
            + _STYLE
        ),
    },
    {
        "id": "CP018",
        "title": "Kawaii Dragon Fantasy",
        "prompt": (
            "SUBJECT: Cute kawaii dragon scene — a small friendly dragon with detailed scale pattern, wings, and "
            "curly tail perched on a castle tower, blowing tiny heart-shaped fire puffs, magical crystals around, "
            "a princess cat waving from a window, stars, fluffy clouds with kawaii faces, and flowers on stone. "
            "COMPOSITION: Fills 85% of the page. Castle battlement and star border. "
            + _STYLE
        ),
    },
    {
        "id": "CP019",
        "title": "Kawaii Space Adventure",
        "prompt": (
            "SUBJECT: Fun kawaii space exploration — a round kawaii astronaut cat floating in a spacesuit, a "
            "friendly alien with big eyes, a detailed rocket ship with porthole windows, planets with surface "
            "crater details and rings, star clusters, galaxy swirl patterns, and a lunar base on the horizon. "
            "COMPOSITION: Fills 85% of the page. Rocket and star border. "
            + _STYLE
        ),
    },
    {
        "id": "CP020",
        "title": "Kawaii Tropical Paradise",
        "prompt": (
            "SUBJECT: Tropical island — kawaii toucan and parrot on palm tree branches, a smiling pineapple "
            "character, hibiscus and plumeria flowers with detailed petals, palm fronds, a hammock between "
            "trees, a coconut with straw, a kawaii wave with face, starfish, and a rainbow. "
            "COMPOSITION: Fills 85% of the page. Tropical leaf and flower border. "
            + _STYLE
        ),
    },
]


# ---------------------------------------------------------------------------
# Pack registry — id prefix is also used to namespace ZIPs/listing JSON per pack
# ---------------------------------------------------------------------------
PACKS = {
    "kawaii": COLORING_THEMES,
    "fun_basic": FUN_BASIC_THEMES,
}


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

def _gen_image_openai(prompt: str, engine: str | None = None) -> bytes | None:
    """Call the approved image engine (via the shared helper) and return raw
    PNG bytes, or None on failure. `engine` defaults to IMAGE_ENGINE/"openai"
    same as generate_image() itself when not given (2026-07-22: threaded
    through so generate_dynamic_theme_set() can honor an explicit engine
    choice from the Create screen's new-theme flow, same as every other
    category's AI generation call in this app)."""
    try:
        from tools.image_gen import generate_image, SQUARE, ImageGenError
    except ImportError:
        sys.path.insert(0, str(BASE))
        from tools.image_gen import generate_image, SQUARE, ImageGenError
    try:
        tmp_path = generate_image(prompt, BASE / "_tmp_coloring_gen.png", size=SQUARE,
                                   output_format="png", engine=engine)
        data = tmp_path.read_bytes()
        tmp_path.unlink(missing_ok=True)
        return data
    except ImageGenError as exc:
        print(f"  ✗ image engine error: {exc}", file=sys.stderr)
    return None


def _enforce_bw(img: Image.Image) -> Image.Image:
    """Post-process to guarantee pure black lines on pure white — no gray anywhere."""
    gray = img.convert("L")
    # Upscale to 2400px if needed for print quality
    if max(gray.size) < 2400:
        ratio = 2400 / max(gray.size)
        gray = gray.resize(
            (int(gray.width * ratio), int(gray.height * ratio)),
            Image.LANCZOS,
        )
    # Boost contrast before thresholding to capture faint lines
    enhanced = ImageEnhance.Contrast(gray).enhance(2.5)
    # Hard threshold: anything above 185 → pure white, else → pure black
    bw = enhanced.point(lambda px: 255 if px > 185 else 0, "L")
    return bw


# ---------------------------------------------------------------------------
# Per-page generation
# ---------------------------------------------------------------------------

def generate_coloring_page(theme: dict, output_dir: Path, regen: bool = False,
                            engine: str | None = None) -> Path | None:
    """Generate one coloring page PNG. Returns path on success, None on failure."""
    # generate_dynamic_theme_set() calls this directly without going through main()'s
    # own COLORING_DIR.mkdir() -- harmless in a real dev/prod checkout where
    # data/digital_products/ already exists from prior product generation, but a
    # fresh CI checkout (that whole tree is gitignored) has no such directory yet,
    # so bw.save() below raised FileNotFoundError and silently failed CI on every
    # push (confirmed 2026-07-23, blocking every Railway deploy since this function
    # was added 2026-07-22). exist_ok=True makes this a no-op when it already exists.
    output_dir.mkdir(parents=True, exist_ok=True)
    dst = output_dir / f"{theme['id']}_coloring.png"
    if dst.exists() and not regen:
        print(f"  ✓ {theme['id']} cached — skipping (--regen to force)")
        return dst

    print(f"  → {theme['id']}: {theme['title']}")
    img_bytes = _gen_image_openai(theme["prompt"], engine=engine)
    if not img_bytes:
        print(f"  ✗ {theme['id']} generation failed")
        return None

    img = Image.open(BytesIO(img_bytes))
    bw = _enforce_bw(img)
    bw.save(dst, "PNG", dpi=(300, 300))
    kb = dst.stat().st_size // 1024
    print(f"  ✓ {dst.name}  ({kb} KB)")
    return dst


# ---------------------------------------------------------------------------
# Dynamic (Scott-authored) theme sets — 2026-07-22
# ---------------------------------------------------------------------------
# Every product before this was a repackaging of the same 2 fixed 20-prompt
# packs above (PACKS). This is the first real per-product theme generator:
# one page per typed subject, wrapped in the SAME _STYLE/_STYLE_BOLD prompt
# DNA every hardcoded theme already uses (via _fun_theme(), unchanged) --
# no new visual vocabulary invented, so a dynamically-generated set looks
# and feels consistent with the rest of the shop's coloring-page catalog.
_DYNAMIC_BORDER = "subtle"  # generic decorative border text _fun_theme() expects


def generate_dynamic_theme_set(product_id: str, subjects: list[str],
                                engine: str | None = None) -> list[Path]:
    """Generate a brand-new, Scott-typed coloring-page set: one page per
    subject line (each theme id namespaced by product_id so caching via
    generate_coloring_page()'s own dst.exists() check can never collide with
    another product's pages, or with a re-run of the same product). Returns
    the list of successfully generated page paths (skips/omits any subject
    whose generation failed rather than raising -- the caller decides
    whether a partial set is still good enough to package)."""
    themes = [
        _fun_theme(f"{product_id}_{i:02d}", subject[:60], subject, _DYNAMIC_BORDER)
        for i, subject in enumerate(subjects, start=1)
    ]
    generated = [generate_coloring_page(t, COLORING_DIR, regen=False, engine=engine) for t in themes]
    return [p for p in generated if p]


# ---------------------------------------------------------------------------
# ZIP packaging
# ---------------------------------------------------------------------------

def build_sets(coloring_files: list[Path], pack: str = "kawaii",
                batch_size: int | None = None) -> list[Path]:
    """Package coloring PNGs into ZIP sets of `batch_size` pages each. Defaults
    to PAGES_PER_SET (5) -- the old fixed-pack behavior, unchanged. The dynamic
    new-theme path (build_coloring_product.py) passes batch_size=
    NEW_THEME_SET_SIZE (20) explicitly so its 20 pages land in ONE ZIP instead
    of being sliced into 4 like the old packs."""
    batch_size = batch_size or PAGES_PER_SET
    SETS_DIR.mkdir(parents=True, exist_ok=True)
    prefix = "coloring_set" if pack == "kawaii" else f"coloring_{pack}_set"
    zip_paths: list[Path] = []
    for i in range(0, len(coloring_files), batch_size):
        batch = coloring_files[i : i + batch_size]
        set_num = (i // batch_size) + 1
        zip_path = SETS_DIR / f"{prefix}_{set_num:02d}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for page in batch:
                zf.write(page, page.name)
        print(f"  ZIP {set_num:02d}: {zip_path.name} ({len(batch)} pages)")
        zip_paths.append(zip_path)
    return zip_paths


# ---------------------------------------------------------------------------
# Listing JSON
# ---------------------------------------------------------------------------

_LISTING_META = {
    "kawaii": {
        "title": "Kawaii Coloring Pages Printable, Adult Coloring Book, Instant Download",
        "price": 3.99,
        "tags": [
            "adult coloring pages",
            "printable coloring",
            "kawaii coloring book",
            "coloring page download",
            "instant download",
            "printable art kids",
            "coloring sheets",
            "cute coloring pages",
            "kawaii printable",
            "coloring book pdf",
            "kids coloring pages",
            "digital coloring",
            "kawaii art print",
        ],
        "hook": (
            "🎨 Instant download kawaii coloring pages — print and color as many times as you want!\n\n"
            "20 unique kawaii-themed coloring pages with adorable scenes — garden parties, "
            "underwater kingdoms, space adventures, floral mandalas, and more. Each page is a crisp "
            "black outline on white — zero fills — ready to bring to life with your favorite "
            "markers, colored pencils, or watercolors."
        ),
        "whats_included": [
            "20 unique kawaii coloring page PNG files",
            "High resolution 2400×2400px — prints beautifully at 8×8\", 8×10\", or A4",
            "Pure black outline on white background — zero fills, zero shading",
            "Themes: garden, ocean, forest, cats, space, florals, dragons, bakery & more",
            "Instant digital download — no physical item shipped",
        ],
    },
    "fun_basic": {
        "title": "Fun Adventure Coloring Pages, Kids Coloring Book, Instant Download",
        "price": 3.99,
        "tags": [
            "kids coloring pages",
            "printable coloring",
            "easy coloring pages",
            "coloring page download",
            "instant download",
            "boy coloring pages",
            "dinosaur coloring",
            "toddler coloring page",
            "simple coloring book",
            "coloring book pdf",
            "fun coloring pages",
            "digital coloring",
            "preschool coloring",
        ],
        "hook": (
            "🚀 Instant download fun adventure coloring pages — print and color as many times as you want!\n\n"
            "20 unique coloring pages packed with fun — dinosaurs, race cars, pirates, robots, and more. "
            "Half the pages are big, bold, and simple — perfect for toddlers and beginners — and half are "
            "playful action scenes with a bit more detail for older kids. Each page is a crisp "
            "black outline on white — zero fills — ready for crayons, markers, or colored pencils."
        ),
        "whats_included": [
            "20 unique coloring page PNG files — 10 big & bold simple designs, 10 fun action scenes",
            "High resolution 2400×2400px — prints beautifully at 8×8\", 8×10\", or A4",
            "Pure black outline on white background — zero fills, zero shading",
            "Themes: dinosaurs, race cars, pirates, robots, knights, space, animals & more",
            "Instant digital download — no physical item shipped",
        ],
    },
}


def generate_listing_json(zip_paths: list[Path], pack: str = "kawaii") -> Path:
    today = date.today().strftime("%Y%m%d")
    meta = _LISTING_META[pack]
    json_path = COLORING_DIR / f"listing_{pack}_{today}.json"
    listing = {
        "pack": pack,
        "title": meta["title"],
        "price": meta["price"],
        "tags": meta["tags"],
        "description": {
            "hook": meta["hook"],
            "whats_included": meta["whats_included"],
            "disclaimer": (
                "⚠️ DIGITAL DOWNLOAD only — NOT a physical coloring book. "
                "PNG files delivered instantly after purchase. No shipping."
            ),
            "ai_disclosure": (
                "These coloring pages were designed using AI image generation tools with original "
                "prompts, curation, and quality review by the seller."
            ),
        },
        "sets": [{"zip": str(z), "pages": PAGES_PER_SET} for z in zip_paths],
        "generated_at": date.today().isoformat(),
    }
    json_path.write_text(json.dumps(listing, indent=2))
    print(f"\n  ✓ Listing JSON → {json_path.name}")
    return json_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate kawaii coloring pages via gpt-image-1"
    )
    parser.add_argument("--pack", choices=list(PACKS), default="kawaii",
                        help="Which theme pack to generate (default: kawaii)")
    parser.add_argument("--themes", type=int, default=None, metavar="N",
                        help="Generate first N themes only (default: all 20)")
    parser.add_argument("--regen", action="store_true",
                        help="Force regenerate images even if cached files exist")
    parser.add_argument("--preview", action="store_true",
                        help="Dry-run: generate listing JSON only, no API calls")
    args = parser.parse_args()

    COLORING_DIR.mkdir(parents=True, exist_ok=True)
    SETS_DIR.mkdir(parents=True, exist_ok=True)

    pack_themes = PACKS[args.pack]
    themes = pack_themes[: args.themes] if args.themes else pack_themes

    if args.preview:
        print("Preview mode — skipping image generation")
        generate_listing_json([], pack=args.pack)
        return

    print(f"Generating {len(themes)} '{args.pack}' coloring page(s) via gpt-image-1…\n")
    generated: list[Path] = []
    for theme in themes:
        p = generate_coloring_page(theme, COLORING_DIR, regen=args.regen)
        if p:
            generated.append(p)

    if not generated:
        print("\n⚠ No pages generated — check OPENAI_API_KEY")
        sys.exit(1)

    print(f"\nPackaging {len(generated)} pages into ZIP sets…")
    zip_paths = build_sets(generated, pack=args.pack)
    generate_listing_json(zip_paths, pack=args.pack)
    print(f"\n✅ Done — {len(generated)} coloring pages · {len(zip_paths)} ZIP set(s)")


if __name__ == "__main__":
    main()
