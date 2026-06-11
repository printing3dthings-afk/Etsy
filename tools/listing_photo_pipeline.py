#!/usr/bin/env python3
"""
listing_photo_pipeline.py — Self-verifying lifestyle photo generator

THE standard pipeline for every listing photo, every product category.
Encodes every lesson from the June 2026 SS1001 session so photos come out
right the FIRST time, without human back-and-forth:

  FAILURE MODE                         → AUTOMATED COUNTERMEASURE
  1. Product physics wrong             → physics templates injected per product type
     (raised lettering on flat signs)
  2. Color drift                       → palette auto-EXTRACTED from the design file
     (navy bias from hardcoded colors)   and injected as hex constraints (never hand-typed)
  3. Hallucinated sibling products     → ALL design files passed as edit inputs;
                                          flat lays use pixel-perfect PIL paste instead
  4. Garbled small text                → text auto-extracted via vision model, injected
                                          as character-exact constraint, then VERIFIED
  5. Fine geometry mangled             → post-generation vision verification compares
     (stamp perforations)                render vs source; discrepancies fed back into
                                          an auto-retry (max 3); hard fails are reported
                                          so the scene can fall back to PIL or another design

Usage (library):
    from tools.listing_photo_pipeline import generate_verified_photo, build_flat_lay

    result = generate_verified_photo(
        design_paths=[Path("design.jpg")],
        scene_prompt="mounted on a cream plaster wall above a walnut console...",
        out_path=Path("photo_01.jpg"),
        physics="sign_flat",            # key into PHYSICS templates
    )
    # result.passed → bool; result.issues → unresolved discrepancies if any

Flat lays / collection shots (zero perspective → pixel-perfect, never AI-rendered):
    build_flat_lay(design_paths, layout, bg_prompt_or_path, out_path)
"""

import re, base64, io, json, sys
from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

MOCKUP_SIZE   = 2400
INPUT_MAX_DIM = 1024
MAX_ATTEMPTS  = 3
EXTRACT_MODEL = "gpt-4o-mini"   # cheap, fine for reading text off a design
VERIFY_MODEL  = "gpt-4o"        # mini hallucinated rejections AND missed a real
                                # shape error in testing — verification needs 4o


# ── Product physics templates ─────────────────────────────────────────────────
# What the physical product actually looks like. Add new product types here.
PHYSICS = {
    # 3D-printed sign, printed FACE-DOWN on textured PEI plate
    "sign_flat": (
        "a thin flat 3D-printed panel (about 6mm thick) made from colored PLA "
        "filament, printed face-down on a textured build plate. The entire front "
        "face is PERFECTLY FLAT — the design is NOT raised, NOT embossed, NOT "
        "engraved; all colors are flush in a single smooth plane like an inlaid "
        "graphic, with a very fine uniform matte grain from the textured plate. "
        "FDM layer lines are visible only on the thin side edges."
    ),
    # Sublimation wrap on a 20oz skinny tumbler
    "tumbler_wrap": (
        "a 20oz skinny stainless steel tumbler with the design physically wrapped "
        "around the cylindrical body with proper curvature, subtle metallic "
        "highlights where the curved surface catches light, and the brushed "
        "stainless lid and base visible above and below the wrap."
    ),
    # Framed wall art print
    "framed_print": (
        "a paper art print displayed in a thin frame with a 2.5-3 inch white mat. "
        "The print surface is perfectly flat matte paper behind glass with a "
        "subtle natural reflection. The design fills the print area edge to edge."
    ),
    # Flat printed paper / card
    "flat_paper": (
        "a flat printed sheet of matte paper lying perfectly flat, the design "
        "printed edge to edge with accurate colors and crisp text."
    ),
}


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


def _client():
    import openai
    return openai.OpenAI(api_key=load_env()["OPENAI_API_KEY"])


def _prep(path: Path, max_dim: int = INPUT_MAX_DIM) -> io.BytesIO:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    scale = min(max_dim / w, max_dim / h, 1.0)
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf


def _b64(path_or_img) -> str:
    if isinstance(path_or_img, (str, Path)):
        img = Image.open(path_or_img).convert("RGB")
    else:
        img = path_or_img
    img.thumbnail((768, 768), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()


# ── Step 1: auto-extract palette (kills color drift) ─────────────────────────
def extract_palette(design_path: Path, n: int = 5) -> list[str]:
    """Dominant colors as hex strings, extracted from the actual file."""
    img = Image.open(design_path).convert("RGB").resize((200, 200))
    quantized = img.quantize(colors=n, method=Image.MEDIANCUT).convert("RGB")
    colors = sorted(quantized.getcolors(200 * 200) or [], reverse=True)[:n]
    return ["#%02X%02X%02X" % c for _, c in colors]


# ── Step 1b: measure canvas facts (kills shape/background judgment errors) ───
def canvas_facts(design_path: Path) -> str:
    """Ground-truth facts about the design file, measured programmatically."""
    img = Image.open(design_path).convert("RGB")
    w, h = img.size
    shape = "square" if abs(w - h) / max(w, h) < 0.05 else f"{w}:{h} rectangular"
    # Background = median of the four corner patches
    px = []
    for cx, cy in [(10, 10), (w - 11, 10), (10, h - 11), (w - 11, h - 11)]:
        patch = img.crop((cx - 8, cy - 8, cx + 8, cy + 8)).resize((1, 1))
        px.append(patch.getpixel((0, 0)))
    bg = tuple(sorted(c[i] for c in px)[len(px) // 2] for i in range(3))
    return (f"the design file canvas is {shape}, and its background color "
            f"(at the canvas corners/edges) is #%02X%02X%02X" % bg)


# ── Step 2: auto-extract text (kills garbled lettering) ──────────────────────
def extract_text(client, design_path: Path) -> str:
    """Every piece of text on the design, read by a vision model once."""
    resp = client.chat.completions.create(
        model=EXTRACT_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text":
                    "List every piece of text visible in this design, exactly as "
                    "written, character for character, one item per line. "
                    "Output only the text items, nothing else."},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{_b64(design_path)}"}},
            ],
        }],
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


# ── Step 3: verification (the automated eyeball) ─────────────────────────────
def verify_render(client, design_paths: list[Path], render: Image.Image,
                  physics_desc: str = "", facts: str = "") -> dict:
    """Compare render against source design(s). Returns {pass: bool, issues: [...]}"""
    content = [{"type": "text", "text":
        "You are a product-photo QA inspector. The FIRST image(s) are the "
        "real product design file(s) a customer downloads. The LAST image is a "
        "marketing lifestyle photo that must show the design faithfully.\n\n"
        f"The physical product is: {physics_desc}\n"
        "Appearance traits described there (e.g. fine matte surface grain, panel "
        "thickness, side edges, metallic lid) are INTENDED and are NOT defects.\n\n"
        "FAIL only on MATERIAL fidelity errors:\n"
        "1. TEXT: any word/number that is wrong, garbled, missing, or invented "
        "(character-level check on dates and small print)\n"
        "2. COLORS: a region changed to a different hue category (e.g. cream became "
        "navy, green became blue). Lighting tint, white balance, mild exposure or "
        "saturation shifts from scene lighting are NORMAL and pass.\n"
        "3. ELEMENTS: missing, added, or redesigned design elements (borders, stars, "
        "icons, edge details)\n"
        f"4. SHAPE — use these measured ground-truth facts, do not judge by eye:\n"
        f"{facts}\n"
        "Fail SHAPE only if the photo's product face clearly contradicts those "
        "facts (e.g. facts say square canvas but the panel is cut into a circle "
        "or the background color region is absent).\n"
        "5. SURFACE: individual letters/shapes sticking UP out of the face as 3D "
        "embossing. The panel itself having thickness, a drop shadow, or the "
        "described surface grain is NORMAL and passes.\n\n"
        "Perspective, viewing angle, scale, lighting, shadows, and scene context "
        "are NEVER issues.\n"
        "IMPORTANT: only report an issue if you can see it CLEARLY and are confident. "
        "If you are uncertain whether something is an issue, do NOT report it — "
        "uncertain observations are not defects.\n"
        'Respond with ONLY JSON: {"pass": true/false, "issues": ["specific issue", ...]}'}]
    for dp in design_paths:
        content.append({"type": "image_url", "image_url": {
            "url": f"data:image/jpeg;base64,{_b64(dp)}"}})
    content.append({"type": "image_url", "image_url": {
        "url": f"data:image/jpeg;base64,{_b64(render)}"}})

    resp = client.chat.completions.create(
        model=VERIFY_MODEL,
        messages=[{"role": "user", "content": content}],
        max_tokens=400,
    )
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.M).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"pass": False, "issues": [f"verifier returned unparseable: {raw[:200]}"]}


# ── Main entry: generate with auto-verify + auto-retry ────────────────────────
@dataclass
class PhotoResult:
    passed: bool
    out_path: Path | None
    attempts: int = 0
    issues: list = field(default_factory=list)


def generate_verified_photo(
    design_paths: list[Path],
    scene_prompt: str,
    out_path: Path,
    physics: str = "sign_flat",
    max_attempts: int = MAX_ATTEMPTS,
    client=None,
) -> PhotoResult:
    client = client or _client()
    design_paths = [Path(p) for p in design_paths]
    for p in design_paths:
        if not p.exists():
            raise FileNotFoundError(p)

    # Pre-extract ground truth from the actual files (never hand-typed)
    palette_lines, text_lines, fact_lines = [], [], []
    for i, dp in enumerate(design_paths, 1):
        palette = extract_palette(dp)
        palette_lines.append(f"Design {i} palette (exact): {', '.join(palette)}")
        text = extract_text(client, dp)
        text_lines.append(f"Design {i} contains exactly this text:\n{text}")
        fact_lines.append(f"FACT (measured): for design {i}, {canvas_facts(dp)}. "
                          "The product face is this FULL canvas — same outer shape, "
                          "same background color, edge to edge.")
    print(f"  Extracted palette + text from {len(design_paths)} design(s)")

    n = len(design_paths)
    base_prompt = (
        f"{'This image is' if n == 1 else f'These {n} images are'} the flat design "
        f"graphic{'s' if n > 1 else ''} of a product. Render a single photorealistic "
        f"product photograph where the design appears as {PHYSICS[physics]}\n\n"
        f"Scene: {scene_prompt}\n\n"
        "FIDELITY REQUIREMENTS (most important):\n"
        "- The EXACT design from the input image(s) appears on the product — same "
        "composition, same elements, same edge details. Do not redesign, simplify, "
        "restyle, or invent anything.\n"
        "- The product keeps the FULL canvas of the design including its background "
        "color: a square design file = a square product face, edge to edge. Never "
        "cut the design out into a circle or silhouette shape.\n"
        + "\n".join(fact_lines) + "\n"
        + "\n".join(palette_lines) + "\n"
        + "\n".join(text_lines) + "\n"
        "Every text item must be reproduced character-for-character.\n\n"
        "Photography: professional Etsy product listing photography, square "
        "composition, no text overlays, no hands, no people, no watermarks. "
        "Completely photorealistic."
    )

    corrections = ""
    for attempt in range(1, max_attempts + 1):
        prompt = base_prompt + corrections
        print(f"  Attempt {attempt}/{max_attempts}: generating...")
        images = [(f"design_{i}.png", _prep(dp), "image/png")
                  for i, dp in enumerate(design_paths, 1)]
        try:
            resp = client.images.edit(
                model="gpt-image-1",
                image=images if n > 1 else images[0],
                prompt=prompt,
                size="1024x1024",
                quality="high",
                input_fidelity="high",
                output_format="png",
            )
        except Exception as e:
            print(f"    generation error: {e}")
            continue

        render = Image.open(io.BytesIO(
            base64.b64decode(resp.data[0].b64_json))).convert("RGB")

        print(f"    verifying against source design(s)...")
        verdict = verify_render(client, design_paths, render, PHYSICS[physics],
                                "\n".join(fact_lines))
        if verdict.get("pass"):
            final = render.resize((MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            final.save(out_path, "JPEG", quality=95, dpi=(300, 300))
            print(f"  ✓ PASSED verification (attempt {attempt}) → {out_path}")
            return PhotoResult(True, out_path, attempt, [])

        issues = verdict.get("issues", [])
        reject = out_path.with_name(out_path.stem + f"_reject{attempt}.jpg")
        reject.parent.mkdir(parents=True, exist_ok=True)
        render.save(reject, "JPEG", quality=90)
        print(f"    ✗ verification failed: {issues}")
        print(f"      rejected render saved for audit: {reject}")
        corrections = (
            "\n\nPREVIOUS ATTEMPT HAD THESE ERRORS — FIX THEM:\n- "
            + "\n- ".join(issues)
        )

    print(f"  ✗ FAILED after {max_attempts} attempts. Issues: {issues}")
    print("    → Fall back to pixel-perfect flat lay, or swap to a design that "
          "renders reliably (avoid tiny text / fine repeating geometry).")
    return PhotoResult(False, None, max_attempts, issues)


# ── Flat lays: zero perspective → pixel-perfect PIL, never AI-rendered ────────
def build_flat_lay(
    design_paths: list[Path],
    layout: list[tuple[int, int, int]],   # (x, y, size) per design on 2400px canvas
    background: Path | str,               # cached bg image path OR generation prompt
    out_path: Path,
    client=None,
) -> PhotoResult:
    if isinstance(background, Path) and background.exists():
        bg = Image.open(background).convert("RGB").resize(
            (MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)
    else:
        client = client or _client()
        print("  Generating flat-lay background...")
        resp = client.images.generate(
            model="gpt-image-1", prompt=str(background),
            size="1024x1024", quality="high", output_format="png")
        bg = Image.open(io.BytesIO(
            base64.b64decode(resp.data[0].b64_json))).convert("RGB")
        bg = bg.resize((MOCKUP_SIZE, MOCKUP_SIZE), Image.LANCZOS)

    canvas = bg.convert("RGBA")
    for dp, (x, y, size) in zip(design_paths, layout):
        design = Image.open(dp).convert("RGB").resize((size, size), Image.LANCZOS)
        radius = size // 60
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, size - 1, size - 1], radius=radius, fill=255)
        panel = Image.new("RGBA", (size, size))
        panel.paste(design, (0, 0))
        panel.putalpha(mask)
        pad = size // 12
        shadow = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle(
            [pad, pad, pad + size - 1, pad + size - 1], radius=radius, fill=(0, 0, 0, 90))
        shadow = shadow.filter(ImageFilter.GaussianBlur(size // 80))
        off = size // 90
        canvas.alpha_composite(shadow, (x - pad + off, y - pad + off))
        canvas.alpha_composite(panel, (x, y))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, "JPEG", quality=95, dpi=(300, 300))
    print(f"  ✓ Flat lay saved (pixel-perfect): {out_path}")
    return PhotoResult(True, out_path, 1, [])


if __name__ == "__main__":
    print(__doc__)
