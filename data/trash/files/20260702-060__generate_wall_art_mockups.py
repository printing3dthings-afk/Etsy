#!/usr/bin/env python3
"""
generate_wall_art_mockups.py

Generates catalog-quality wall art lifestyle mockups using gpt-image-1's
image editing endpoint. The actual art file is passed as input — the model
places it inside a real picture frame already in the room scene, rendering
a single coherent photorealistic image.

This replaces the old PIL composite method (lifestyle_composite.py) which
placed AI-generated art into AI-generated rooms via perspective warping.
The images.edit approach passes the REAL art file and produces a single
coherent render with natural lighting, correct frame shadows, and
perspective-correct art placement.

Each product gets two room types (living room + bedroom by default) in a
chosen frame style. All outputs are 2400×2400px JPEG for Etsy.

Usage:
  python tools/generate_wall_art_mockups.py              # all products
  python tools/generate_wall_art_mockups.py DP1000       # one product
  python tools/generate_wall_art_mockups.py DP1000 DP1007 DP1013
"""

import re, base64, io, sys
from pathlib import Path
from PIL import Image

ART_DIR    = Path("data/digital_products/product_files")
OUTPUT_DIR = Path("data/wall_art_mockups")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MOCKUP_SIZE = 2400   # square JPEG output
INPUT_MAX   = 1024   # max dimension to send to API


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


# ── Frame styles ──────────────────────────────────────────────────────────────
# Each style defines the physical frame description used in the prompt.
# "natural_wood" = warm living rooms / bohemian
# "black_minimal" = modern / contemporary / dark academia
# "white_gallery" = bright / Scandinavian / nursery

FRAME_STYLES = {
    "natural_wood": (
        "natural light oak wood frame with a 2.5-inch white linen mat surrounding the artwork, "
        "thin carved moulding profile, matte warm finish"
    ),
    "black_minimal": (
        "thin 0.75-inch flat matte black metal frame with a crisp white mat, "
        "modern gallery-style profile, no ornamentation"
    ),
    "white_gallery": (
        "clean 1-inch flat white painted wood frame with a wide 3-inch bright white mat, "
        "gallery wall style, simple square profile"
    ),
}


# ── Room scenes ───────────────────────────────────────────────────────────────
# Each scene describes the room, surface, props, and lighting.
# The art frame is already present in the scene — the model places the input
# artwork INSIDE that existing frame.

ROOM_SCENES = {

    "living_room": {
        "room": (
            "warm cream textured plaster wall. A boucle fabric sofa with sage green and "
            "terracotta throw pillows sits below the frame. A natural rattan side table with "
            "a small terracotta ceramic pot is beside the sofa. "
            "Natural light oak hardwood floors. "
            "Trailing pothos plant in a terracotta pot on the left side of the scene."
        ),
        "light": "soft diffused morning window light from the left, warm white balance, gentle shadow to the right of the frame",
        "style": "bright airy editorial Etsy lifestyle, warm cream and natural linen tones throughout, IKEA catalog quality",
    },

    "bedroom": {
        "room": (
            "off-white linen-textured wall. A low platform bed in natural light oak with "
            "cream linen bedding and two stacked throw pillows sits below the frame. "
            "A small ceramic table lamp on a nightstand to the right emits warm amber glow. "
            "A trailing pothos plant on the windowsill at the left edge of frame."
        ),
        "light": "soft warm evening atmosphere, amber lamp glow from the right, gentle diffused window light from the left, intimate mood",
        "style": "Japandi bedroom editorial photography, calm, serene, cozy, warm neutrals",
    },

    "home_office": {
        "room": (
            "warm white smooth wall. A floating light oak desk with minimal items: "
            "a small white ceramic succulent pot, a matte black adjustable desk lamp, "
            "two thin hardcover books stacked flat. "
            "Clean and modern, no clutter."
        ),
        "light": "bright clean natural daylight from a window on the left, cool-neutral white balance, even illumination, no harsh shadows",
        "style": "clean modern home office lifestyle photography, Scandinavian minimal aesthetic, crisp and professional",
    },

    "dining_room": {
        "room": (
            "warm cream-white wall with subtle linen texture. A natural oak dining table "
            "with cream linen chair visible at the lower edge. "
            "A small terracotta vase with dried pampas grass on the table. "
            "Woven rattan pendant lamp partially visible at the top of frame."
        ),
        "light": "warm midday window light from the left, golden-warm white balance, soft shadow on the right side",
        "style": "boho dining room lifestyle, warm earthy tones, editorial Etsy product photography",
    },

}


# ── Per-product config ────────────────────────────────────────────────────────
# "art_style"     — brief visual description of the art (helps model render it accurately)
# "frame_style"   — key from FRAME_STYLES (natural_wood / black_minimal / white_gallery)
# "rooms"         — list of 2 room keys from ROOM_SCENES (first = primary Etsy photo)
# "orientation"   — "portrait" (2:3) or "landscape" (3:2) or "square"
#
# Products DP1000–DP1026 are the wall art catalog.
# Products DP1030+ are planner covers — separate system.

PRODUCTS = {

    "DP1000": {
        "art_style": "boho botanical art — soft watercolor botanicals with flowing organic shapes in muted sage green, terracotta, and cream",
        "frame_style": "natural_wood",
        "rooms": ["living_room", "bedroom"],
        "orientation": "portrait",
    },
    "DP1001": {
        "art_style": "minimalist botanical line art — delicate black line drawing of botanical plants on a cream white background",
        "frame_style": "white_gallery",
        "rooms": ["living_room", "home_office"],
        "orientation": "portrait",
    },
    "DP1002": {
        "art_style": "watercolor botanical art — soft pastel flowers in blush pink, sage green, and cream, delicate watercolor technique",
        "frame_style": "natural_wood",
        "rooms": ["bedroom", "living_room"],
        "orientation": "portrait",
    },
    "DP1003": {
        "art_style": "abstract nature-inspired art — flowing organic shapes in earthy terracotta, warm cream, and deep sage",
        "frame_style": "natural_wood",
        "rooms": ["living_room", "bedroom"],
        "orientation": "portrait",
    },
    "DP1007": {
        "art_style": "abstract modern art — bold brushstroke shapes in cobalt blue and warm terracotta on a cream background",
        "frame_style": "black_minimal",
        "rooms": ["living_room", "home_office"],
        "orientation": "portrait",
    },
    "DP1008": {
        "art_style": "celestial moon phases art — elegant moon cycle illustration in gold and navy on a deep indigo background",
        "frame_style": "black_minimal",
        "rooms": ["bedroom", "living_room"],
        "orientation": "portrait",
    },
    "DP1009": {
        "art_style": "minimalist botanical line drawing — simple elegant black ink line art of tropical leaves on white",
        "frame_style": "white_gallery",
        "rooms": ["home_office", "living_room"],
        "orientation": "portrait",
    },
    "DP1010": {
        "art_style": "watercolor floral art — impressionist-style orange and coral poppies with lush green foliage",
        "frame_style": "natural_wood",
        "rooms": ["dining_room", "living_room"],
        "orientation": "portrait",
    },
    "DP1011": {
        "art_style": "landscape art — golden hour mountain meadow with wildflowers in warm amber and sage green, painterly style",
        "frame_style": "natural_wood",
        "rooms": ["living_room", "home_office"],
        "orientation": "portrait",
    },
    "DP1012": {
        "art_style": "bold maximalist checkerboard and floral pop art — vibrant checkered pattern with oversized blooms in red, yellow, and white",
        "frame_style": "black_minimal",
        "rooms": ["living_room", "home_office"],
        "orientation": "portrait",
    },
    "DP1013": {
        "art_style": "vintage national park poster — WPA-style Grand Canyon retro travel art in muted desert ochre, rust, and sky blue",
        "frame_style": "natural_wood",
        "rooms": ["home_office", "living_room"],
        "orientation": "portrait",
    },
    "DP1014": {
        "art_style": "Japandi zen art — minimalist Japanese tree and rising sun in soft blush, sage, and warm ivory, peaceful aesthetic",
        "frame_style": "white_gallery",
        "rooms": ["bedroom", "living_room"],
        "orientation": "portrait",
    },
    "DP1015": {
        "art_style": "romantic floral oil painting — abundant white roses in creamy impasto technique on a warm ivory background, cottagecore style",
        "frame_style": "natural_wood",
        "rooms": ["bedroom", "dining_room"],
        "orientation": "portrait",
    },
    "DP1016": {
        "art_style": "funny pet portrait — golden retriever dog at a bar illustrated in a humorous vintage oil painting style, rich warm tones",
        "frame_style": "natural_wood",
        "rooms": ["living_room", "home_office"],
        "orientation": "portrait",
    },
    "DP1017": {
        "art_style": "moody seascape art — full moon over a dark ocean with dramatic clouds and silver moonlight on water",
        "frame_style": "black_minimal",
        "rooms": ["bedroom", "living_room"],
        "orientation": "portrait",
    },
    "DP1018": {
        "art_style": "colorful cosmic space art — vivid nebula galaxy with an astronaut floating in space in electric purples and teals",
        "frame_style": "black_minimal",
        "rooms": ["home_office", "living_room"],
        "orientation": "portrait",
    },
    "DP1019": {
        "art_style": "vintage muscle car illustration — 1970 Chevelle SS in cobalt blue, detailed technical line art with warm gold accents, man cave style",
        "frame_style": "black_minimal",
        "rooms": ["home_office", "living_room"],
        "orientation": "portrait",
    },
    "DP1020": {
        "art_style": "Day of the Dead skull art — colorful ornate sugar skull with bold maximalist floral patterns in vibrant coral, teal, and gold",
        "frame_style": "black_minimal",
        "rooms": ["living_room", "home_office"],
        "orientation": "portrait",
    },
    "DP1021": {
        "art_style": "abstract feminist line art — elegant minimalist portrait of a woman with botanical flowers in simple black line on cream",
        "frame_style": "white_gallery",
        "rooms": ["bedroom", "living_room"],
        "orientation": "portrait",
    },
    "DP1022": {
        "art_style": "tropical monstera leaves art — bold vibrant tropical botanical print in deep emerald green and sage with graphic illustration style",
        "frame_style": "natural_wood",
        "rooms": ["living_room", "bedroom"],
        "orientation": "portrait",
    },
    "DP1023": {
        "art_style": "vintage antique herbarium botanical art — detailed scientific illustration of pressed dried plants in aged sepia and warm parchment tones",
        "frame_style": "natural_wood",
        "rooms": ["living_room", "dining_room"],
        "orientation": "portrait",
    },
    "DP1024": {
        "art_style": "Paris Eiffel Tower line art — minimalist geometric line drawing of Paris skyline in simple black on clean white, city art style",
        "frame_style": "black_minimal",
        "rooms": ["home_office", "living_room"],
        "orientation": "square",
    },
    "DP1025": {
        "art_style": "Italian kitchen wall art — illustrated olive oil, pasta, and wine with warm Mediterranean colors and hand-lettered text, foodie art",
        "frame_style": "natural_wood",
        "rooms": ["dining_room", "living_room"],
        "orientation": "portrait",
    },
    "DP1026": {
        "art_style": "nature landscape watercolor — soft organic shapes and botanical elements in earthy sage green, terracotta, and warm cream",
        "frame_style": "natural_wood",
        "rooms": ["living_room", "bedroom"],
        "orientation": "portrait",
    },

}


# ── Edit prompt template ──────────────────────────────────────────────────────

EDIT_PROMPT_TEMPLATE = """\
This image is a high-resolution digital wall art print. \
Place this exact artwork inside a {frame_desc} that is already hanging on the wall \
in the room scene described below. Produce a single photorealistic lifestyle product \
photograph at professional catalog quality (think Pottery Barn, CB2, or West Elm catalog photography).

The artwork content: {art_style}

Frame and placement requirements:
— The EXACT artwork from this image must appear inside the frame, preserving all colors, \
composition, and visual elements accurately
— The frame is mounted on the wall at comfortable eye level, centered horizontally
— Show the frame with realistic drop shadow and ambient light reflection on the wall below
— The mat (if present) surrounds the art with clean white margins inside the frame
— Slight perspective and vanishing point consistent with room depth
— Frame should occupy approximately 25–35% of the frame width

Room scene:
{room_scene}

Lighting: {light}

Photography direction: {style}. \
The framed artwork is the hero product — it fills the upper-center 35% of the image. \
The furniture and props anchor the lower portion. \
Upper 60% of the wall behind the frame is completely bare — no other decor or objects on the wall. \
Sharp commercial product photography. Completely photorealistic — no AI artifact look. \
Square 1:1 composition, subject centered. \
No hands, no people, no watermarks, no text added to the image.\
"""


def generate_mockup(
    client,
    product_id: str,
    art_path: Path,
    room_key: str,
    frame_key: str,
    retries: int = 2,
) -> Path | None:
    cfg = PRODUCTS.get(product_id, {})
    art_style = cfg.get("art_style", "fine art print with vibrant colors and detailed composition")
    frame_desc = FRAME_STYLES[frame_key]
    room_cfg = ROOM_SCENES[room_key]

    prompt = EDIT_PROMPT_TEMPLATE.format(
        frame_desc=frame_desc,
        art_style=art_style,
        room_scene=room_cfg["room"],
        light=room_cfg["light"],
        style=room_cfg["style"],
    )

    # Resize art for API input (1024px max on either dimension)
    art_img = Image.open(art_path).convert("RGB")
    aw, ah = art_img.size
    scale = min(INPUT_MAX / aw, INPUT_MAX / ah, 1.0)
    if scale < 1.0:
        art_img = art_img.resize((int(aw * scale), int(ah * scale)), Image.LANCZOS)

    buf = io.BytesIO()
    art_img.save(buf, "PNG")
    buf.seek(0)

    for attempt in range(1, retries + 2):
        print(f"  [{product_id}] {room_key} / {frame_key} (attempt {attempt})...")
        try:
            response = client.images.edit(
                model="gpt-image-1",
                image=("art.png", buf, "image/png"),
                prompt=prompt,
                size="1024x1024",
                quality="high",
                output_format="png",
            )
            buf.seek(0)

            img_bytes = base64.b64decode(response.data[0].b64_json)
            result = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            result = result.resize((MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)

            out_path = OUTPUT_DIR / f"{product_id}_{room_key}_{frame_key}.jpg"
            result.save(out_path, "JPEG", quality=95, dpi=(300, 300))
            kb = out_path.stat().st_size // 1024
            print(f"    ✓ Saved: {out_path.name} ({kb} KB)")
            return out_path

        except Exception as e:
            print(f"    Attempt {attempt} failed: {e}")
            if attempt >= retries + 1:
                print(f"    Giving up on {product_id}/{room_key}")
                return None
            buf.seek(0)

    return None


def find_art_file(product_id: str) -> Path | None:
    for ext in (".jpg", ".png"):
        p = ART_DIR / f"{product_id}{ext}"
        if p.exists():
            return p
    return None


def main(ids: list[str] | None = None):
    env = load_env()
    import openai
    client = openai.OpenAI(api_key=env["OPENAI_API_KEY"])

    if ids:
        targets = {pid: PRODUCTS.get(pid, {}) for pid in ids}
    else:
        targets = PRODUCTS

    # Filter to products with art files on disk
    valid = {}
    for pid in targets:
        art_path = find_art_file(pid)
        if art_path:
            valid[pid] = art_path
        else:
            print(f"  [SKIP] {pid}: no art file found in {ART_DIR}")

    if not valid:
        print("No valid products found.")
        return

    print(f"Generating wall art mockups for {len(valid)} products\n")
    results = []

    for product_id, art_path in sorted(valid.items()):
        cfg = PRODUCTS.get(product_id, {})
        rooms = cfg.get("rooms", ["living_room", "bedroom"])
        frame_key = cfg.get("frame_style", "natural_wood")

        product_results = []
        for room_key in rooms:
            out = generate_mockup(client, product_id, art_path, room_key, frame_key)
            product_results.append((room_key, "OK" if out else "FAILED", out))

        results.append((product_id, product_results))

    print("\n─── Summary ────────────────────────────────────────")
    for product_id, room_results in results:
        print(f"  {product_id}:")
        for room_key, status, path in room_results:
            mark = "✓" if status == "OK" else "✗"
            print(f"    {mark} {room_key}: {status}")
            if path:
                print(f"        → {path}")


if __name__ == "__main__":
    ids = sys.argv[1:] or None
    main(ids)
