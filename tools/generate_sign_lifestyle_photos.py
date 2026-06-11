#!/usr/bin/env python3
"""
generate_sign_lifestyle_photos.py

Generates lifestyle mockups for 3D-printed wall sign listings using gpt-image-1's
image editing endpoint — the same approach used for the tumbler mockups.

The flat design JPG is passed as input. gpt-image-1 renders it as a physical
3D-printed sign displayed in a real-world scene, with proper lighting, shadows,
and depth — no manual PIL compositing needed.

Usage:
  python tools/generate_sign_lifestyle_photos.py               # all photos
  python tools/generate_sign_lifestyle_photos.py hero porch    # specific shots
"""

import re, base64, io, sys
from pathlib import Path
from PIL import Image

DESIGNS_DIR = Path("data/3d_print_signs/america_250/ai_generated")
OUTPUT_DIR  = Path("data/3d_print_signs/america_250/listing_photos/final")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MOCKUP_SIZE  = 2400
INPUT_MAX_DIM = 1024


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


# ── Design files ──────────────────────────────────────────────────────────────
DESIGN_FILES = {
    "main":      DESIGNS_DIR / "america250_ai_color_raw.jpg",
    "medallion": DESIGNS_DIR / "america250_design2_medallion.jpg",
    "artdeco":   DESIGNS_DIR / "america250_design3_artdeco.jpg",
    "stamp":     DESIGNS_DIR / "america250_design4_stamp.jpg",
    "shield":    DESIGNS_DIR / "america250_design5_shield.jpg",
}

# ── Sign description shared across all scenes ─────────────────────────────────
SIGN_DESCRIPTION = (
    "a square 3D-printed patriotic wall sign made from colored PLA filament, "
    "printed with a Bambu Lab 3D printer using 4-color AMS system. "
    "The sign has visible fine layer lines characteristic of FDM 3D printing, "
    "a slightly matte surface texture, and a flat back. "
    "Colors are bold navy blue, deep red, gold, and cream. "
    "The sign is approximately 10×10 inches (250×250mm) square."
)

# ── Scene configs ─────────────────────────────────────────────────────────────
SCENES = {

    "hero": {
        "design_id": "main",
        "out_name":  "photo_01_hero_gallery_wall.jpg",
        "prompt": f"""\
This is the flat graphic of a 3D-printed patriotic wall sign. Render it as a \
single photorealistic product photograph of {SIGN_DESCRIPTION}

Scene: The sign is mounted on a warm cream plaster wall as the centerpiece of a small \
gallery wall arrangement. Two smaller coordinating frames (no art — just natural wood \
empty frames) flank it on each side, slightly smaller. The wall has warm cream textured \
plaster. Below the sign grouping: a narrow dark walnut console table with a small \
terracotta pot holding dried pampas grass on the left, and a folded navy linen on \
the right. A few loose dried eucalyptus stems lean against the wall.

The 3D-printed sign itself occupies the CENTER of the frame, filling approximately \
60% of the image width. It is mounted flat against the wall with a subtle drop shadow \
showing depth. The design from this image is faithfully reproduced on the sign face — \
same colors, same composition, same details — rendered with the matte surface texture \
of FDM-printed PLA plastic. The sign is perfectly centered and level.

Photography: warm cream and neutral tones, soft diffused natural window light from the \
left, warm white balance, gentle shadow to the right. 50mm lens, eye-level, square \
2400×2400px composition. No text overlays. No hands. Professional Etsy product listing \
photography style. Completely photorealistic.""",
    },

    "porch": {
        "design_id": "artdeco",
        "out_name":  "photo_02_porch_sign.jpg",
        "prompt": f"""\
This is the flat graphic of a 3D-printed patriotic wall sign. Render it as a \
single photorealistic product photograph of {SIGN_DESCRIPTION}

Scene: The sign is mounted on a white-painted wooden front porch wall, centered between \
two porch columns. A small American flag is displayed to one side in a bracket. \
A simple wooden bench with a navy blue cushion sits below. A potted red geranium \
plant sits on the porch floor. Bright summer daylight, American patriotic porch setting.

The 3D-printed sign is mounted flat and level on the porch wall, centered in the frame, \
filling approximately 55% of the image. The design from this image is faithfully \
reproduced on the sign face with the matte FDM-printed PLA surface texture visible. \
The sign is perfectly centered.

Photography: bright clean natural daylight, slightly warm white balance, no harsh \
shadows. 35mm lens, eye-level. Square composition. No text overlays. No hands. \
Professional Etsy product listing photography style. Completely photorealistic.""",
    },

    "mantel": {
        "design_id": "medallion",
        "out_name":  "photo_03_mantel_sign.jpg",
        "prompt": f"""\
This is the flat graphic of a 3D-printed patriotic wall sign. Render it as a \
single photorealistic product photograph of {SIGN_DESCRIPTION}

Scene: The sign is the centerpiece displayed on a white-painted fireplace mantel. \
It leans against the wall slightly (not mounted flat — just displayed standing). \
Flanking it on the mantel: two white pillar candles in clear glass hurricane holders, \
and small sprigs of dried lavender in a cream ceramic bud vase. The fireplace surround \
is white-painted wood with classic molding. Soft warm interior lighting.

The 3D-printed sign stands centered on the mantel, filling approximately 50% of the \
frame height. The design from this image is faithfully reproduced on the sign face \
with matte FDM-printed PLA surface texture. The sign is perfectly upright and centered.

Photography: warm interior ambient light, soft shadows, warm white balance. 50mm lens, \
slightly above eye-level angled down. Square composition. No text overlays. No hands. \
Professional Etsy product listing photography style. Completely photorealistic.""",
    },

    "tieredtray": {
        "design_id": "stamp",
        "out_name":  "photo_04_tieredtray_sign.jpg",
        "prompt": f"""\
This is the flat graphic of a 3D-printed patriotic wall sign. Render it as a \
single photorealistic product photograph of {SIGN_DESCRIPTION}

Scene: A smaller version of the sign (scaled to about 6×6 inches / 150mm) is displayed \
on the middle tier of a three-tier farmhouse serving tray with black metal frame and \
rustic wood tiers. The tray also holds: a small glass votive candle, a mini American \
flag pick, and a few decorative stars. The tray sits on a cream-colored farmhouse \
kitchen counter. White shiplap wall background. Soft neutral farmhouse aesthetic.

The 3D-printed sign is centered on its tier, the most prominent item. The design from \
this image is faithfully reproduced on the sign face with matte FDM-printed PLA surface \
texture. The sign is perfectly upright and centered in the overall frame.

Photography: bright clean natural daylight, neutral-warm white balance, soft even \
lighting. 50mm lens, eye-level. Square composition. No text overlays. No hands. \
Farmhouse kitchen Etsy lifestyle photography. Completely photorealistic.""",
    },

    "yardsign": {
        "design_id": "shield",
        "out_name":  "photo_05_yard_sign.jpg",
        "prompt": f"""\
This is the flat graphic of a 3D-printed patriotic wall sign. Render it as a \
single photorealistic product photograph of {SIGN_DESCRIPTION}

Scene: The sign is mounted to a simple wooden stake and displayed in a garden or front \
yard. It is pushed into green grass. A garden border with red and white flowers \
(petunias or impatiens) is visible behind it. A white picket fence is slightly blurred \
in the background. Bright patriotic summer outdoor setting. Blue sky with light clouds.

The sign is upright on its stake, centered in the frame, filling approximately 55% \
of the frame. The design from this image is faithfully reproduced on the sign face \
with matte FDM-printed PLA surface texture. The sign is perfectly upright and centered.

Photography: bright natural sunlight, slightly warm, gentle shadows. 50mm lens, \
slightly below eye-level to show sky. Square composition. No text overlays. No hands. \
Outdoor garden Etsy product photography. Completely photorealistic.""",
    },

    "collection": {
        "design_id": "main",
        "out_name":  "photo_06_collection_overview.jpg",
        "prompt": f"""\
This is one of five 3D-printed patriotic wall sign designs in a set called \
'America 250th Anniversary Signs'. Render a photorealistic flat lay product photograph.

Scene: Five square 3D-printed signs (each {SIGN_DESCRIPTION}) are laid flat on \
a clean white linen surface, arranged in a neat 2-3 grid or cross pattern. \
They are evenly spaced with small gaps between them. The signs have slightly varying \
patriotic designs (eagle, medallion, art deco sunburst, vintage stamp, heraldic shield) \
but all use the same navy/red/gold/cream palette. A few scattered decorative gold stars \
and a small American flag ribbon decorate the spaces between the signs. \
The surface is clean white textured linen. Bright even overhead lighting.

Photography: bright clean overhead diffused light, pure white balance, no shadows, \
product catalog style. Camera directly overhead, square composition. No text overlays. \
No hands. Professional Etsy multi-product flat lay. Completely photorealistic.""",
    },

}


def generate_mockup(client, scene_id: str, scene_cfg: dict) -> Path | None:
    design_path = DESIGN_FILES[scene_cfg["design_id"]]
    out_path    = OUTPUT_DIR / scene_cfg["out_name"]

    print(f"[{scene_id}] Loading design: {design_path.name}")
    img = Image.open(design_path).convert("RGB")
    w, h = img.size
    scale = min(INPUT_MAX_DIM / w, INPUT_MAX_DIM / h, 1.0)
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)

    print(f"[{scene_id}] Generating lifestyle mockup...")
    try:
        response = client.images.edit(
            model="gpt-image-1",
            image=("design.png", buf, "image/png"),
            prompt=scene_cfg["prompt"],
            size="1024x1024",
            quality="high",
            output_format="png",
        )

        img_bytes = base64.b64decode(response.data[0].b64_json)
        result = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        result = result.resize((MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)

        result.save(out_path, "JPEG", quality=95, dpi=(300, 300))
        kb = out_path.stat().st_size // 1024
        print(f"  ✓ Saved: {out_path.name} ({kb} KB)")
        return out_path

    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return None


def main(ids: list[str] | None = None):
    env = load_env()
    import openai
    client = openai.OpenAI(api_key=env["OPENAI_API_KEY"])

    targets = {k: v for k, v in SCENES.items() if ids is None or k in ids}
    if not targets:
        print(f"Unknown scene IDs: {ids}. Available: {list(SCENES.keys())}")
        return

    print(f"Generating {len(targets)} lifestyle mockup(s) for SS1001 America 250 signs\n")
    results = []
    for scene_id, scene_cfg in targets.items():
        out = generate_mockup(client, scene_id, scene_cfg)
        results.append((scene_id, "OK" if out else "FAILED", out))

    print("\n─── Summary ─────────────────────────────────")
    for scene_id, status, path in results:
        mark = "✓" if status == "OK" else "✗"
        print(f"  {mark} {scene_id}: {status}")
        if path:
            print(f"    → {path}")


if __name__ == "__main__":
    ids = sys.argv[1:] or None
    main(ids)
