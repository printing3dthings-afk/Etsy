#!/usr/bin/env python3
"""
generate_coloring_pages.py

Generates kawaii-themed coloring pages using gpt-image-1 — clean black line art
on white background, zero fills, suitable for printing and coloring.

The previous PIL edge-detection approach was removed (it produced too much fill and
muddy lines). This version generates original artwork directly.

Usage:
    python tools/generate_coloring_pages.py              # generate all 20 themes
    python tools/generate_coloring_pages.py --themes 5  # first 5 themes only
    python tools/generate_coloring_pages.py --regen      # force regenerate cached
    python tools/generate_coloring_pages.py --preview    # listing JSON only, no images
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
# Image generation
# ---------------------------------------------------------------------------

def _gen_image_openai(prompt: str) -> bytes | None:
    """Call gpt-image-1 (via the shared helper) and return raw PNG bytes, or None on failure."""
    try:
        from tools.image_gen import generate_image, SQUARE, ImageGenError
    except ImportError:
        sys.path.insert(0, str(BASE))
        from tools.image_gen import generate_image, SQUARE, ImageGenError
    try:
        tmp_path = generate_image(prompt, BASE / "_tmp_coloring_gen.png", size=SQUARE, output_format="png")
        data = tmp_path.read_bytes()
        tmp_path.unlink(missing_ok=True)
        return data
    except ImageGenError as exc:
        print(f"  ✗ OpenAI error: {exc}", file=sys.stderr)
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

def generate_coloring_page(theme: dict, output_dir: Path, regen: bool = False) -> Path | None:
    """Generate one coloring page PNG. Returns path on success, None on failure."""
    dst = output_dir / f"{theme['id']}_coloring.png"
    if dst.exists() and not regen:
        print(f"  ✓ {theme['id']} cached — skipping (--regen to force)")
        return dst

    print(f"  → {theme['id']}: {theme['title']}")
    img_bytes = _gen_image_openai(theme["prompt"])
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
# ZIP packaging
# ---------------------------------------------------------------------------

def build_sets(coloring_files: list[Path]) -> list[Path]:
    """Package coloring PNGs into ZIP sets of PAGES_PER_SET."""
    SETS_DIR.mkdir(parents=True, exist_ok=True)
    zip_paths: list[Path] = []
    for i in range(0, len(coloring_files), PAGES_PER_SET):
        batch = coloring_files[i : i + PAGES_PER_SET]
        set_num = (i // PAGES_PER_SET) + 1
        zip_path = SETS_DIR / f"coloring_set_{set_num:02d}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for page in batch:
                zf.write(page, page.name)
        print(f"  ZIP {set_num:02d}: {zip_path.name} ({len(batch)} pages)")
        zip_paths.append(zip_path)
    return zip_paths


# ---------------------------------------------------------------------------
# Listing JSON
# ---------------------------------------------------------------------------

def generate_listing_json(zip_paths: list[Path]) -> Path:
    today = date.today().strftime("%Y%m%d")
    json_path = COLORING_DIR / f"listing_{today}.json"
    listing = {
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
        "description": {
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
    parser.add_argument("--themes", type=int, default=None, metavar="N",
                        help="Generate first N themes only (default: all 20)")
    parser.add_argument("--regen", action="store_true",
                        help="Force regenerate images even if cached files exist")
    parser.add_argument("--preview", action="store_true",
                        help="Dry-run: generate listing JSON only, no API calls")
    args = parser.parse_args()

    COLORING_DIR.mkdir(parents=True, exist_ok=True)
    SETS_DIR.mkdir(parents=True, exist_ok=True)

    themes = COLORING_THEMES[: args.themes] if args.themes else COLORING_THEMES

    if args.preview:
        print("Preview mode — skipping image generation")
        generate_listing_json([])
        return

    print(f"Generating {len(themes)} coloring page(s) via gpt-image-1…\n")
    generated: list[Path] = []
    for theme in themes:
        p = generate_coloring_page(theme, COLORING_DIR, regen=args.regen)
        if p:
            generated.append(p)

    if not generated:
        print("\n⚠ No pages generated — check OPENAI_API_KEY")
        sys.exit(1)

    print(f"\nPackaging {len(generated)} pages into ZIP sets…")
    zip_paths = build_sets(generated)
    generate_listing_json(zip_paths)
    print(f"\n✅ Done — {len(generated)} coloring pages · {len(zip_paths)} ZIP set(s)")


if __name__ == "__main__":
    main()
