#!/usr/bin/env python3
"""
generate_tumbler_mockups.py

Generates magazine-quality 20oz tumbler lifestyle mockups using gpt-image-1's
image editing endpoint. The actual flat design is passed as input — the model
renders it physically wrapped on the tumbler with proper cylinder curvature,
metallic reflections, and natural lighting as a single coherent render.

This is the correct approach for catalog-level realism. The old PIL composite
method (perspective warp onto a separately generated background) was discarded
because it looked AI-generated. The edit approach treats the design as source
material and produces a photorealistic output.

Usage:
  python tools/generate_tumbler_mockups.py                   # all 8 designs
  python tools/generate_tumbler_mockups.py football_mom      # one design
  python tools/generate_tumbler_mockups.py football_mom dog_mom nurse_life
"""

import re, base64, io, sys
from pathlib import Path
from PIL import Image

OUTPUT_DIR  = Path("data/sublimation_mockups")
SAMPLES_DIR = Path("data/sublimation_samples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MOCKUP_SIZE = 2400   # square JPEG output
INPUT_MAX_W = 1536   # resize input to this width before sending to API


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


# ── Per-design edit prompts ───────────────────────────────────────────────────
# Structure:
#   "design_description" — what's ON the wrap (helps model render accurately)
#   "scene"              — lifestyle context (surface, props, background, light)
# Both feed into the final edit prompt template at the bottom of this file.

DESIGNS = {

    "football_mom": {
        "design_description": (
            "deep forest green background with tiny scattered gold footballs and autumn maple "
            "leaves, a large brown leather football with white lace stitching in the center "
            "surrounded by lush autumn wildflowers in gold, rust orange, and burgundy, "
            "bold cream varsity-font 'FOOTBALL MOM' lettering above the football, "
            "'Always Cheering' in flowing gold script below"
        ),
        "scene": (
            "rustic dark oak wood surface, dried pampas grass in a terracotta vase to the left, "
            "two small orange pumpkins to the right, a folded plaid blanket corner at the bottom, "
            "warm cream textured plaster wall background, soft warm amber window light from left"
        ),
    },

    "cheer_mom": {
        "design_description": (
            "deep royal purple background with tiny hot pink megaphones and gold star pattern, "
            "two large crossed cheerleader pom-poms — one hot pink, one bright gold — with "
            "metallic sheen, radiating gold starburst behind the pom-poms, "
            "bold gold metallic 'CHEER MOM' lettering, "
            "'Louder Than Your Loudest Fan' in hot pink handwritten script below"
        ),
        "scene": (
            "smooth dark purple velvet surface, scattered small gold confetti pieces, "
            "a mini hot pink pom-pom to the lower right, a small gold star decoration, "
            "deep charcoal background with subtle bokeh glow, "
            "glamour studio lighting from above with metallic highlights"
        ),
    },

    "dog_mom": {
        "design_description": (
            "rich terracotta background with scattered cream paw prints and botanical sprigs, "
            "a charming kawaii golden retriever face with warm amber eyes and floppy ears "
            "in the center framed by a lush boho floral wreath of dried pampas, peach roses, "
            "eucalyptus, and cream daisies, bold cream serif 'DOG MOM' lettering above, "
            "'Fur Baby Mama' in dusty rose handwritten script below"
        ),
        "scene": (
            "natural linen cloth surface, small terracotta pot with trailing pothos to the left, "
            "a dried flower sprig and a golden retriever collar tag charm to the right, "
            "warm cream textured wall background, "
            "soft morning window light from the left, warm earthy tones"
        ),
    },

    "nurse_life": {
        "design_description": (
            "deep navy blue background with thin electric teal EKG heartbeat lines and tiny "
            "cross icons scattered throughout, a large bold electric teal medical cross with "
            "white inner glow in the center surrounded by roses, lavender, and wildflowers, "
            "bold white 'NURSE LIFE' lettering with teal glow outline, "
            "'Saving Lives & Sipping Coffee' in electric teal handwritten script below"
        ),
        "scene": (
            "clean white marble surface, a stethoscope casually coiled to the left, "
            "a small succulent in a white ceramic pot to the right, "
            "a folded teal scrub fabric corner at the base, "
            "clean white professional background, bright even natural light"
        ),
    },

    "teacher_life": {
        "design_description": (
            "warm golden yellow background with tiny red apples, pencils, and star icons, "
            "a large shiny red apple with a green leaf and golden highlight in the center, "
            "open books and colorful pencils radiating outward, ABC block letter accents, "
            "bold retro blackboard-style 'TEACHER LIFE' lettering in deep charcoal with "
            "white chalk texture and red drop shadow, "
            "'Shaping Futures One Kid at a Time' in white chalkboard script below"
        ),
        "scene": (
            "light wood teacher's desk surface, a shiny red apple to the left, "
            "two sharpened pencils (red and yellow) leaning against the tumbler, "
            "a small chalkboard eraser in the background, "
            "warm cream wall, bright cheerful classroom light"
        ),
    },

    "girl_mom": {
        "design_description": (
            "deep plum berry background with tiny rosebuds and gold sparkle dots, "
            "a lush abundant bouquet of garden roses, peonies, and wildflowers in blush pink, "
            "dusty rose, cream, and lavender tied with a flowing gold ribbon in the center, "
            "small pink butterflies with gold wing edges among the flowers, "
            "elegant antique gold 'GIRL MOM' serif lettering above, "
            "'Raising Wildflowers' in graceful blush pink handwritten script below"
        ),
        "scene": (
            "soft dusty rose fabric surface, scattered blush rose petals, "
            "a small butterfly ornament, a gold ribbon bow at the tumbler base, "
            "deep plum-purple wall with soft texture, "
            "romantic soft window light from the left, warm rosy tones"
        ),
    },

    "boy_mom": {
        "design_description": (
            "midnight navy blue background with tiny lightning bolts, arrows, and mountain "
            "silhouettes, a large antique brass compass rose or adventure badge emblem "
            "with electric blue center, pine trees and mountain peaks surrounding it, "
            "small rocket and dinosaur accent icons, bold orange 'BOY MOM' lettering with "
            "white stroke, 'Blessed & Exhausted' in electric blue handwritten script below"
        ),
        "scene": (
            "rough reclaimed dark wood surface, a small toy dinosaur to the right, "
            "scattered decorative star and arrow elements, a miniature compass, "
            "dark navy textured wall background, "
            "cool-toned moody side lighting with dramatic shadows"
        ),
    },

    "mama_mode": {
        "design_description": (
            "warm burnt sienna background with groovy retro wavy lines, tiny sunburst icons, "
            "and daisy flowers in mustard yellow and cream, a large retro medallion badge "
            "with scalloped mustard yellow border, a kawaii smiling sunflower with big eyes "
            "and rosy cheeks inside the badge, flanking monstera leaves and sunflower sprigs, "
            "groovy rounded serif 'MAMA MODE' lettering in cream with rust shadow, "
            "'ON & Absolutely Unhinged' in 70s mustard yellow script below"
        ),
        "scene": (
            "warm mustard yellow ceramic tile surface, a retro-style sunflower to the left, "
            "two small daisy sprigs, a vintage-looking woven coaster, "
            "warm sienna-orange textured plaster wall background, "
            "golden-hour warm lighting from the left"
        ),
    },

}


# ── Core generation function ──────────────────────────────────────────────────

EDIT_PROMPT_TEMPLATE = """\
This image is a flat sublimation tumbler wrap design. \
Render it as a single photorealistic product photograph at professional catalog quality \
(think Yeti, Stanley, or RTIC product catalog photography).

The wrap design shows: {design_description}

Transform this flat wrap so it is physically wrapped around a 20oz skinny stainless \
steel tumbler. The tumbler is upright, centered in frame. Requirements:
— The EXACT design from this image must appear on the tumbler with all colors, \
text, and illustrated elements preserved accurately
— Proper cylinder curvature: the design wraps realistically around the round tumbler body
— Natural metallic highlights and shadows on the stainless steel tumbler lid and base
— The design has subtle ambient reflections where the curved tumbler catches light
— The brushed stainless steel lid and base are visible above and below the wrap

Scene: {scene}

Photography direction: soft natural window light from the left, warm white balance, \
gentle shadow to the right, slight depth of field on background props. \
Sharp commercial product photography. The tumbler fills the center 65% of the frame. \
Completely photorealistic — no AI artifact look, no cartoon rendering. \
No hands, no people, no watermarks, no text outside the design itself.\
"""


def generate_mockup(client, design_id: str, design_path: Path, retries: int = 2) -> Path | None:
    if design_id not in DESIGNS:
        print(f"  [{design_id}] No scene config — using generic prompt")
        design_cfg = {
            "design_description": "a colorful tumbler wrap design",
            "scene": "clean cream surface with soft natural props, warm light from the left"
        }
    else:
        design_cfg = DESIGNS[design_id]

    prompt = EDIT_PROMPT_TEMPLATE.format(**design_cfg)

    # Resize design for API input
    design_img = Image.open(design_path).convert("RGB")
    dw, dh = design_img.size
    scale = min(INPUT_MAX_W / dw, 1024 / dh, 1.0)
    if scale < 1.0:
        design_img = design_img.resize((int(dw * scale), int(dh * scale)), Image.LANCZOS)

    buf = io.BytesIO()
    design_img.save(buf, "PNG")
    buf.seek(0)

    for attempt in range(1, retries + 2):
        print(f"  [{design_id}] Generating mockup (attempt {attempt})...")
        try:
            response = client.images.edit(
                model="gpt-image-1",
                image=("design.png", buf, "image/png"),
                prompt=prompt,
                size="1024x1024",
                quality="high",
                output_format="png",
            )
            buf.seek(0)  # reset for potential retry

            img_bytes = base64.b64decode(response.data[0].b64_json)
            result = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            result = result.resize((MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)

            out_path = OUTPUT_DIR / f"mockup_{design_id}_20oz.jpg"
            result.save(out_path, "JPEG", quality=95, dpi=(300, 300))
            kb = out_path.stat().st_size // 1024
            print(f"    ✓ Saved: {out_path.name} ({kb} KB)")
            return out_path

        except Exception as e:
            print(f"    Attempt {attempt} failed: {e}")
            if attempt >= retries + 1:
                print(f"    Giving up on {design_id}")
                return None
            buf.seek(0)

    return None


def main(ids: list[str] | None = None):
    env = load_env()
    import openai
    client = openai.OpenAI(api_key=env["OPENAI_API_KEY"])

    all_designs = {
        p.stem.replace("sublimation_", "").replace("_20oz", ""): p
        for p in SAMPLES_DIR.glob("sublimation_*_20oz.png")
    }

    targets = {k: v for k, v in all_designs.items() if ids is None or k in ids}
    if not targets:
        print(f"No designs found in {SAMPLES_DIR}")
        return

    print(f"Generating {len(targets)} catalog-quality tumbler mockups\n")
    results = []
    for design_id, design_path in sorted(targets.items()):
        out = generate_mockup(client, design_id, design_path)
        results.append((design_id, "OK" if out else "FAILED", out))

    print("\n─── Summary ───────────────────────────────")
    for design_id, status, path in results:
        mark = "✓" if status == "OK" else "✗"
        print(f"  {mark} {design_id}: {status}")
        if path:
            print(f"    → {path}")


if __name__ == "__main__":
    ids = sys.argv[1:] or None
    main(ids)
