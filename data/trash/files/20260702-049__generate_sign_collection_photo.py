#!/usr/bin/env python3
"""
generate_sign_collection_photo.py

Builds the SS1001 collection overview photo (photo_06) with GUARANTEED design
accuracy: the five actual design files are pasted pixel-perfect onto an
AI-generated empty flat-lay background.

Why PIL here and images.edit everywhere else: a straight-overhead flat lay has
ZERO perspective distortion, so a direct paste is geometrically exact and the
design text is reproduced character-perfect. images.edit with 5 input designs
garbles small text ("ANNIVERSARY", "FOREVER") — verified June 2026.

The background is generated once (empty linen surface, no signs) and cached;
pass --new-bg to force regeneration.
"""

import re, base64, io, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

DESIGNS_DIR = Path("data/3d_print_signs/america_250/ai_generated")
BG_PATH     = Path("data/3d_print_signs/america_250/listing_photos/flatlay_bg_empty.png")
OUT_PATH    = Path("data/3d_print_signs/america_250/listing_photos/final/photo_06_collection_overview.jpg")
CANVAS      = 2400

DESIGN_FILES = [
    DESIGNS_DIR / "america250_ai_color_raw.jpg",      # main eagle
    DESIGNS_DIR / "america250_design2_medallion.jpg", # medallion
    DESIGNS_DIR / "america250_design3_artdeco.jpg",   # art deco
    DESIGNS_DIR / "america250_design4_stamp.jpg",     # vintage stamp
    DESIGNS_DIR / "america250_design5_shield.jpg",    # heraldic shield
]

# Layout: 2-1-2 quincunx on a 2400x2400 canvas (x, y, size) per sign.
# Rows are vertically separated so NO panel ever overlaps another —
# overlap covers design content (caught June 2026: center panel hid "2026").
PANEL_LAYOUT = [
    (270,  110, 720),   # top-left     — main eagle
    (1410, 110, 720),   # top-right    — medallion
    (840,  840, 720),   # center       — art deco
    (270,  1570, 720),  # bottom-left  — stamp
    (1410, 1570, 720),  # bottom-right — shield
]

BG_PROMPT = """\
Photorealistic overhead product photography background, square. A clean white \
textured linen fabric surface fills the entire frame, photographed directly from \
above. Scattered sparsely near the edges and corners: a few small gold star \
confetti pieces and two short thin red-white-blue striped ribbon segments. \
The CENTER 90% of the frame is completely EMPTY plain linen — no objects, no \
props, nothing in the middle area. Bright even diffused overhead lighting, pure \
neutral white balance, no harsh shadows. No text, no hands, no people, no products.\
"""


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


def generate_background(client) -> Image.Image:
    print("Generating empty flat-lay background...")
    response = client.images.generate(
        model="gpt-image-1",
        prompt=BG_PROMPT,
        size="1024x1024",
        quality="high",
        output_format="png",
    )
    img_bytes = base64.b64decode(response.data[0].b64_json)
    bg = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    bg = bg.resize((CANVAS, CANVAS), Image.LANCZOS)
    BG_PATH.parent.mkdir(parents=True, exist_ok=True)
    bg.save(BG_PATH)
    print(f"  ✓ Background saved: {BG_PATH}")
    return bg


def panel_with_shadow(design_path: Path, size: int) -> tuple[Image.Image, Image.Image]:
    """Return (panel RGBA, shadow RGBA) — flat sign panel with soft drop shadow."""
    design = Image.open(design_path).convert("RGB")
    design = design.resize((size, size), Image.LANCZOS)

    # Rounded corners like a real printed panel (slight radius from slicer)
    radius = size // 60
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)

    panel = Image.new("RGBA", (size, size))
    panel.paste(design, (0, 0))
    panel.putalpha(mask)

    # Soft shadow (offset down-right, blurred) — conveys the 6mm panel thickness
    pad = size // 12
    shadow = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([pad, pad, pad + size - 1, pad + size - 1],
                         radius=radius, fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(size // 80))
    return panel, shadow


def main():
    force_new_bg = "--new-bg" in sys.argv

    if BG_PATH.exists() and not force_new_bg:
        print(f"Using cached background: {BG_PATH}")
        bg = Image.open(BG_PATH).convert("RGB").resize((CANVAS, CANVAS), Image.LANCZOS)
    else:
        env = load_env()
        import openai
        client = openai.OpenAI(api_key=env["OPENAI_API_KEY"])
        bg = generate_background(client)

    canvas = bg.convert("RGBA")

    for design_path, (x, y, size) in zip(DESIGN_FILES, PANEL_LAYOUT):
        if not design_path.exists():
            raise FileNotFoundError(f"Missing design file: {design_path}")
        panel, shadow = panel_with_shadow(design_path, size)
        pad = size // 12
        offset = size // 90  # shadow offset down-right
        canvas.alpha_composite(shadow, (x - pad + offset, y - pad + offset))
        canvas.alpha_composite(panel, (x, y))
        print(f"  ✓ Placed {design_path.stem} at ({x},{y}) size {size}")

    result = canvas.convert("RGB")
    result.save(OUT_PATH, "JPEG", quality=95, dpi=(300, 300))
    print(f"✓ Saved: {OUT_PATH} ({OUT_PATH.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
