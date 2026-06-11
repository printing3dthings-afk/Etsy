#!/usr/bin/env python3
"""
generate_sign_collection_photo.py

Regenerates the SS1001 collection overview photo (photo_06) the CORRECT way:
ALL FIVE actual design files are passed as input images to gpt-image-1's edit
endpoint, so every sign in the flat lay is the real downloadable design —
never an AI-invented stand-in.

CARDINAL RULE: every listing photo must show the real product. A multi-product
photo must receive ALL product files as input.
"""

import re, base64, io
from pathlib import Path
from PIL import Image

DESIGNS_DIR = Path("data/3d_print_signs/america_250/ai_generated")
OUT_PATH    = Path("data/3d_print_signs/america_250/listing_photos/final/photo_06_collection_overview.jpg")
MOCKUP_SIZE = 2400

# Order matters — referenced by number in the prompt
DESIGN_FILES = [
    ("main eagle",       DESIGNS_DIR / "america250_ai_color_raw.jpg"),
    ("medallion",        DESIGNS_DIR / "america250_design2_medallion.jpg"),
    ("art deco",         DESIGNS_DIR / "america250_design3_artdeco.jpg"),
    ("vintage stamp",    DESIGNS_DIR / "america250_design4_stamp.jpg"),
    ("heraldic shield",  DESIGNS_DIR / "america250_design5_shield.jpg"),
]

PROMPT = """\
These five images are the five flat graphics of a set of 3D-printed patriotic wall signs \
called 'America 250th Anniversary Signs'. Render a single photorealistic overhead flat lay \
product photograph showing ALL FIVE signs together.

Each sign is a square 3D-printed panel made from colored PLA filament (Bambu Lab AMS \
4-color printing), approximately 9.25x9.25 inches and 6mm thick, printed face-down on a \
textured build plate. Each panel's front face is PERFECTLY FLAT — the design is NOT \
raised, NOT embossed, NOT engraved; all colors sit flush in a single smooth plane like \
an inlaid graphic, with a very fine uniform matte grain texture from the textured plate. \
FDM layer lines are visible only on the thin side edges. Each panel's face must \
reproduce its source image EXACTLY — identical colors, identical text, identical \
composition, identical details. Do not redesign, restyle, simplify, or invent any sign. \
The five signs are: image 1 (eagle design), image 2 (circular medallion), \
image 3 (art deco sunburst), image 4 (vintage stamp), image 5 (heraldic shield).

CRITICAL TEXT ACCURACY: every piece of lettering must be copied character-for-character \
from the source images. The dates read exactly "1776" and "2026" — never 2028 or any \
other year. The stamp's small bottom-right word reads exactly "FOREVER". \
"AMERICA", "250", "UNITED STATES", "UNITED STATES OF AMERICA", "ANNIVERSARY" — \
all spelled exactly as shown in the sources. No invented words, no garbled letters.

Scene: the five square signs are laid flat on a clean white textured linen surface, \
arranged neatly — one in the center, four around it (or a tidy 2-1-2 layout), evenly \
spaced with small gaps. A few small decorative gold stars and a thin red-white-blue \
ribbon accent the spaces between signs. Nothing covers any part of any sign face.

Photography: directly overhead camera, bright even diffused lighting, pure neutral white \
balance, soft minimal shadows under each plaque edge showing thickness. Square composition. \
No text overlays, no hands, no people, no watermarks. Professional Etsy product catalog \
flat lay. Completely photorealistic.\
"""


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


def prep_image(path: Path, max_dim: int = 1024) -> io.BytesIO:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    scale = min(max_dim / w, max_dim / h, 1.0)
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf


def main():
    env = load_env()
    import openai
    client = openai.OpenAI(api_key=env["OPENAI_API_KEY"])

    images = []
    for name, path in DESIGN_FILES:
        if not path.exists():
            raise FileNotFoundError(f"Missing design file: {path}")
        print(f"Loading design: {name} ({path.name})")
        images.append((f"{path.stem}.png", prep_image(path), "image/png"))

    print("Generating collection flat lay with ALL 5 real designs as input...")
    response = client.images.edit(
        model="gpt-image-1",
        image=images,
        prompt=PROMPT,
        size="1024x1024",
        quality="high",
        input_fidelity="high",
        output_format="png",
    )

    img_bytes = base64.b64decode(response.data[0].b64_json)
    result = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    result = result.resize((MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)
    result.save(OUT_PATH, "JPEG", quality=95, dpi=(300, 300))
    print(f"✓ Saved: {OUT_PATH} ({OUT_PATH.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
