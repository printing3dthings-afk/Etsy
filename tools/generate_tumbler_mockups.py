#!/usr/bin/env python3
"""
generate_tumbler_mockups.py

Generates realistic 20oz skinny tumbler lifestyle mockup photos for Etsy listings.
Shows the design on a real-looking tumbler in a lifestyle setting — critical for
conversion (flat PNG previews as hero images are a confirmed conversion killer).

Workflow:
  1. Generate empty tumbler on lifestyle background via gpt-image-1
  2. Crop and perspective-warp the flat design to fit the tumbler face
  3. Composite the actual design onto the tumbler (showing the REAL product)
  4. Output: 2400×2400px JPEG at 300 DPI

Usage:
  python tools/generate_tumbler_mockups.py                     # all designs in samples dir
  python tools/generate_tumbler_mockups.py football_mom        # specific design(s)
"""

import re, base64, io, sys, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUTPUT_DIR  = Path("data/sublimation_mockups")
SAMPLES_DIR = Path("data/sublimation_samples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MOCKUP_SIZE = 2400  # square output


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


# ── Per-design lifestyle scene descriptions ───────────────────────────────────
# Each prompt describes the EMPTY scene only — no design on the tumbler.
# The actual design is composited in step 2.
# The scene description should complement each design's color palette.

SCENE_PROMPTS = {
    "football_mom": (
        "forest green", "autumn",
        "Photorealistic lifestyle product photography, square format. "
        "A plain white 20oz skinny stainless steel tumbler standing upright on a rustic "
        "dark oak wood surface. Autumn scene: dried pampas grass in a terracotta vase to "
        "the left, two mini orange pumpkins on the right, a soft plaid blanket corner "
        "visible at bottom edge. Background: warm cream textured plaster wall. "
        "Soft window light from the left, warm amber tones. The tumbler occupies the center "
        "60% of the frame, clearly lit with even illumination showing the full tumbler surface. "
        "No design on the tumbler — the tumbler surface is plain white. "
        "No hands, no people, no text, no watermarks."
    ),
    "cheer_mom": (
        "deep purple", "glam",
        "Photorealistic lifestyle product photography, square format. "
        "A plain white 20oz skinny stainless steel tumbler standing upright on a smooth "
        "dark purple velvet surface. Scene: scattered gold confetti pieces, two gold "
        "star-shaped small decorations, a mini pom-pom in hot pink at the lower right. "
        "Background: deep charcoal-black with a subtle bokeh glow. "
        "Studio glamour lighting from above, metallic highlights on the tumbler. "
        "The tumbler occupies the center 60% of the frame, clearly lit. "
        "No design on the tumbler — the tumbler surface is plain white. "
        "No hands, no people, no text, no watermarks."
    ),
    "dog_mom": (
        "terracotta", "boho",
        "Photorealistic lifestyle product photography, square format. "
        "A plain white 20oz skinny stainless steel tumbler standing upright on a natural "
        "linen cloth surface. Scene: a small terracotta ceramic pot with a trailing pothos "
        "plant to the left, a golden retriever dog collar or paw-print tag charm to the right, "
        "a dried flower sprig. Background: warm cream textured wall. "
        "Soft morning window light from the left, warm earthy tones. "
        "The tumbler occupies the center 60% of the frame, clearly lit. "
        "No design on the tumbler — the tumbler surface is plain white. "
        "No hands, no people, no text, no watermarks."
    ),
    "nurse_life": (
        "navy and teal", "professional",
        "Photorealistic lifestyle product photography, square format. "
        "A plain white 20oz skinny stainless steel tumbler standing upright on a clean "
        "white marble surface. Scene: a stethoscope casually coiled to the left, a small "
        "succulent in a white ceramic pot to the right, a folded teal scrub fabric corner. "
        "Background: clean white hospital-adjacent wall with subtle texture. "
        "Bright clean professional light from above and left. "
        "The tumbler occupies the center 60% of the frame, clearly lit. "
        "No design on the tumbler — the tumbler surface is plain white. "
        "No hands, no people, no text, no watermarks."
    ),
    "teacher_life": (
        "golden yellow", "classroom",
        "Photorealistic lifestyle product photography, square format. "
        "A plain white 20oz skinny stainless steel tumbler standing upright on a light "
        "wood teacher's desk surface. Scene: a shiny red apple to the left, two sharpened "
        "colored pencils (red and yellow) leaning against the tumbler, a small chalkboard "
        "eraser in the background. Background: warm cream wall. "
        "Bright cheerful classroom light. "
        "The tumbler occupies the center 60% of the frame, clearly lit. "
        "No design on the tumbler — the tumbler surface is plain white. "
        "No hands, no people, no text, no watermarks."
    ),
    "girl_mom": (
        "deep plum", "romantic",
        "Photorealistic lifestyle product photography, square format. "
        "A plain white 20oz skinny stainless steel tumbler standing upright on a soft "
        "dusty rose fabric surface. Scene: scattered rose petals in blush pink, a small "
        "butterfly ornament, a gold ribbon tied in a bow at the base. "
        "Background: deep plum-purple wall with soft texture. "
        "Romantic soft window light from left, warm rosy tones. "
        "The tumbler occupies the center 60% of the frame, clearly lit. "
        "No design on the tumbler — the tumbler surface is plain white. "
        "No hands, no people, no text, no watermarks."
    ),
    "boy_mom": (
        "midnight navy", "adventure",
        "Photorealistic lifestyle product photography, square format. "
        "A plain white 20oz skinny stainless steel tumbler standing upright on a rough "
        "reclaimed wood surface. Scene: a small toy dinosaur to the right, a few scattered "
        "stars and arrow-shaped decorative elements, a miniature compass. "
        "Background: dark navy textured wall. "
        "Moody cool-toned side lighting, dramatic shadows. "
        "The tumbler occupies the center 60% of the frame, clearly lit. "
        "No design on the tumbler — the tumbler surface is plain white. "
        "No hands, no people, no text, no watermarks."
    ),
    "mama_mode": (
        "burnt sienna", "retro",
        "Photorealistic lifestyle product photography, square format. "
        "A plain white 20oz skinny stainless steel tumbler standing upright on a warm "
        "mustard yellow ceramic tile surface. Scene: a retro-style sunflower to the left, "
        "two small daisy sprigs, a vintage-looking woven coaster. "
        "Background: warm sienna-orange textured plaster wall. "
        "Warm retro golden-hour lighting from the left. "
        "The tumbler occupies the center 60% of the frame, clearly lit. "
        "No design on the tumbler — the tumbler surface is plain white. "
        "No hands, no people, no text, no watermarks."
    ),
}

DEFAULT_SCENE = (
    "cream", "lifestyle",
    "Photorealistic lifestyle product photography, square format. "
    "A plain white 20oz skinny stainless steel tumbler standing upright on a "
    "light cream linen-textured desk. Background: warm white textured wall. "
    "Soft diffused window light from the left, warm white balance. "
    "The tumbler occupies the center 60% of the frame, clearly lit. "
    "No design on the tumbler — plain white surface. "
    "No hands, no people, no text, no watermarks."
)


# ── Step 1: Generate empty tumbler background ─────────────────────────────────

def generate_empty_tumbler(client, design_id: str) -> Image.Image:
    _, _, prompt = SCENE_PROMPTS.get(design_id, DEFAULT_SCENE)
    print(f"    Generating lifestyle background for {design_id}...")

    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        quality="high",
        n=1,
        output_format="png",
    )
    img_bytes = base64.b64decode(response.data[0].b64_json)
    return Image.open(io.BytesIO(img_bytes)).convert("RGBA")


# ── Step 2: Warp flat design to simulate cylinder face ────────────────────────

def warp_design_to_cylinder(design_img: Image.Image, face_w: int, face_h: int) -> Image.Image:
    """
    Approximates the visible front face of a cylinder:
    - Crops the center 42% of the design (visible arc of ~150° out of 360°)
    - Applies mild horizontal perspective compression at edges to simulate curvature
    - Resizes to (face_w, face_h) to fit the tumbler face area
    """
    dw, dh = design_img.size
    crop_start = int(dw * 0.29)
    crop_end   = int(dw * 0.71)
    face_crop  = design_img.crop((crop_start, 0, crop_end, dh))

    # Perspective warp: squish the left and right edges inward slightly
    # This simulates the way a cylinder curves away at the edges
    src_w, src_h = face_crop.size
    compression = 0.12  # 12% edge compression

    # Four-point perspective transform
    src_pts = [
        (0, 0), (src_w, 0),
        (src_w, src_h), (0, src_h)
    ]
    offset = int(src_w * compression)
    dst_pts = [
        (offset, 0), (src_w - offset, 0),
        (src_w - offset, src_h), (offset, src_h)
    ]

    # PIL perspective needs 8 coefficients — compute via least squares
    coeffs = _find_perspective_coeffs(src_pts, dst_pts)
    warped = face_crop.transform(
        (src_w, src_h), Image.PERSPECTIVE, coeffs, Image.BICUBIC
    )

    # Resize to the target face area
    resized = warped.resize((face_w, face_h), Image.LANCZOS)
    return resized


def _find_perspective_coeffs(src_pts, dst_pts):
    """Compute 8-coefficient perspective transform matrix (PIL PERSPECTIVE format)."""
    import numpy as np
    A, b = [], []
    for (x, y), (X, Y) in zip(src_pts, dst_pts):
        A.append([X, Y, 1, 0, 0, 0, -x * X, -x * Y])
        A.append([0, 0, 0, X, Y, 1, -y * X, -y * Y])
        b.append(x)
        b.append(y)
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    coeffs, *_ = np.linalg.lstsq(A, b, rcond=None)
    return list(coeffs)


# ── Step 3: Composite design onto tumbler ─────────────────────────────────────

def composite_design_on_tumbler(
    bg_img: Image.Image,
    design_img: Image.Image,
    design_id: str,
) -> Image.Image:
    """
    Locates the tumbler face in bg_img and composites the warped design onto it.
    The tumbler is expected to be centered in the bg_img.

    Strategy: the tumbler face occupies approximately:
      - horizontal: bg center ± 14% of width  (28% total)
      - vertical:   12% from top to 88% from top (76% of height)
    These are approximate and work well for center-framed tumbler photos.
    """
    bg = bg_img.convert("RGBA").resize((MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)
    bw, bh = bg.size

    # Tumbler face bounding box (approximate — centered composition)
    face_x1 = int(bw * 0.36)
    face_x2 = int(bw * 0.64)
    face_y1 = int(bh * 0.10)
    face_y2 = int(bh * 0.90)
    face_w  = face_x2 - face_x1
    face_h  = face_y2 - face_y1

    # Warp the design to fit the tumbler face
    flat_design = design_img.convert("RGBA")
    warped = warp_design_to_cylinder(flat_design, face_w, face_h)

    # Create soft-edge mask to blend edges realistically
    mask = Image.new("L", (face_w, face_h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, face_w - 1, face_h - 1], radius=face_w // 12, fill=255)
    # Feather the mask edges
    mask = mask.filter(ImageFilter.GaussianBlur(radius=6))

    # Composite: paste warped design onto bg using the mask
    # Use 75% opacity to let the underlying tumbler highlights/shadows show through
    warped_with_alpha = warped.copy()
    r, g, b, a = warped_with_alpha.split()
    a_adjusted = a.point(lambda p: int(p * 0.82))  # slight transparency for realism
    warped_with_alpha.putalpha(a_adjusted)

    bg.paste(warped_with_alpha, (face_x1, face_y1), mask)

    return bg.convert("RGB")


# ── Main ──────────────────────────────────────────────────────────────────────

def generate_mockup(client, design_id: str, design_path: Path) -> Path | None:
    print(f"\n  [{design_id}] Building tumbler mockup...")

    try:
        bg = generate_empty_tumbler(client, design_id)
    except Exception as e:
        print(f"    ERROR generating background: {e}")
        return None

    design_img = Image.open(design_path).convert("RGBA")
    result = composite_design_on_tumbler(bg, design_img, design_id)

    out_path = OUTPUT_DIR / f"mockup_{design_id}_20oz.jpg"
    result.save(out_path, "JPEG", quality=92, dpi=(300, 300))
    kb = out_path.stat().st_size // 1024
    print(f"    Saved: {out_path.name} ({kb} KB)")
    return out_path


def main(ids: list[str] | None = None):
    env = load_env()
    import openai
    client = openai.OpenAI(api_key=env["OPENAI_API_KEY"])

    # Find all design PNGs
    all_designs = {
        p.stem.replace("sublimation_", "").replace("_20oz", ""): p
        for p in SAMPLES_DIR.glob("sublimation_*_20oz.png")
    }

    targets = {k: v for k, v in all_designs.items() if ids is None or k in ids}
    if not targets:
        print(f"No designs found. Checked: {SAMPLES_DIR}")
        return

    print(f"Generating {len(targets)} tumbler mockups → {OUTPUT_DIR.absolute()}\n")
    results = []
    for design_id, design_path in sorted(targets.items()):
        out = generate_mockup(client, design_id, design_path)
        results.append((design_id, "OK" if out else "FAILED", out))

    print("\n─── Summary ───────────────────────────────")
    for design_id, status, path in results:
        print(f"  {design_id}: {status}")
        if path:
            print(f"    → {path}")


if __name__ == "__main__":
    ids = sys.argv[1:] or None
    main(ids)
