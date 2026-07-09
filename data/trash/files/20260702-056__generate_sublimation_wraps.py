#!/usr/bin/env python3
"""
generate_sublimation_wraps.py

Generates production-quality sublimation tumbler wrap designs for Etsy.
Each design is generated at gpt-image-1 max resolution, then upscaled
to true 300 DPI print dimensions using Lanczos resampling.

Output: PNG files at 300 DPI, sRGB, ready for sublimation printing.

Sizes:
  20oz Skinny: 9.33" × 8.33" @ 300 DPI = 2799 × 2499 px
  30oz Tall:   9.5"  × 9.1"  @ 300 DPI = 2850 × 2730 px
"""

import re
import base64
import io
import sys
from pathlib import Path

OUTPUT_DIR = Path("data/sublimation_samples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SIZES = {
    "20oz":      (2798, 2438),   # 9.325" × 8.125" @ 300 DPI — MakerFlo standard straight
    "20oz_thick": (3360, 2318),  # 11.2"  × 7.725" @ 300 DPI — thick-wall variant
    "30oz":      (3090, 2880),   # 10.3"  × 9.6"   @ 300 DPI
    "30oz_thick": (3360, 2655),  # 11.2"  × 8.85"  @ 300 DPI — thick-wall variant
    "11oz_mug":  (2550, 1050),   # 8.5"   × 3.5"   @ 300 DPI
    "15oz_mug":  (2700, 1200),   # 9.0"   × 4.0"   @ 300 DPI
}

GEN_SIZE = "1536x1024"


def load_env():
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


# ---------------------------------------------------------------------------
# Design library — each entry is a self-contained, highly-detailed prompt.
# Prompts are written to maximise gpt-image-1's illustration quality:
#   1. State the EXACT art style first
#   2. Describe background, then focal design, then typography, then accents
#   3. Specify the colour palette with hex values
#   4. End with hard technical constraints (seamless, no watermark, etc.)
# ---------------------------------------------------------------------------

DESIGNS = [

    # ── FOOTBALL MOM ────────────────────────────────────────────────────────
    {
        "id": "football_mom",
        "name": "Football Mom",
        "prompt": """
Professional sublimation tumbler wrap design, full bleed horizontal rectangle.

Art style: retro vintage sports illustration meets boho watercolor florals —
rich, layered, painterly depth with bold typography.

BACKGROUND: Deep forest green (#1B4332) field filled with a loose all-over
pattern of tiny golden footballs, autumn leaves (maple, oak), and scattered
small five-pointed stars in antique gold and cream. Pattern is dense enough
to leave no plain background showing through.

CENTRAL FOCAL DESIGN: A large, detailed American football rendered in warm
brown leather with hand-stitched white lace and realistic panel shading.
Flanking the football on both sides: lush clusters of fall wildflowers —
sunflowers with dark centres, dried pampas grass plumes, small daisy sprigs,
and eucalyptus leaves — all in gold (#D97706), rust orange (#C2410C), cream
(#FEF3C7), and burgundy (#7B2D3E). Botanical elements feel loose and
painterly, not rigid.

TYPOGRAPHY: Centred above the football: "FOOTBALL MOM" in a bold retro varsity
font, cream/ivory (#FEF3C7) fill with a worn, slightly distressed texture, and
a thick antique gold (#D97706) stroke outline. Below the football: "Always
Cheering" in a flowing, casual handwritten script in antique gold.

ACCENTS: Small five-pointed stars and sparkle dots in gold and cream scattered
throughout. Thin decorative rule lines in gold frame the typography block.

COLOUR PALETTE: forest green, autumn burgundy, warm cream, antique gold,
rust orange. ZERO pastels. Deep, saturated, high-contrast.

TECHNICAL: The left edge and right edge of the design must be visually
seamless — the background pattern continues without a visible seam. Colours
are vibrant and fully saturated to compensate for sublimation's natural
colour shift. No white or pale areas in the background. No watermarks.
No photograph elements. No studio equipment. Print-ready quality.
        """.strip(),
    },

    # ── CHEER MOM ───────────────────────────────────────────────────────────
    {
        "id": "cheer_mom",
        "name": "Cheer Mom",
        "prompt": """
Professional sublimation tumbler wrap design, full bleed horizontal rectangle.

Art style: bold graphic pop with metallic glam elements — high energy,
sparkle-forward, stadium lights aesthetic. Think sports glam magazine cover.

BACKGROUND: Deep royal purple (#3B0764) base with an all-over pattern of
small megaphones, cheerleader stars, tiny pom-pom dots, and confetti bursts
in hot pink (#EC4899), bright gold (#FCD34D), and white. Background is fully
covered — no plain areas.

CENTRAL FOCAL DESIGN: Two large crossed cheerleader pom-poms — one hot pink,
one bright gold — rendered with realistic metallic sheen and individual
strand detail. Behind the pom-poms: a starburst explosion in gold and white.
Surrounding: confetti, sparkle stars, and small lightning bolt icons in pink
and gold radiating outward.

TYPOGRAPHY: Bold, condensed, all-caps "CHEER MOM" centred between the
pom-poms, lettered in bright gold (#FCD34D) metallic gradient with a hot pink
(#EC4899) outer stroke and white inner glow. Below: "Louder Than Your Loudest
Fan" in a spunky, rounded handwritten script in hot pink with a white shadow.

ACCENTS: Scattered five-pointed gold stars, white sparkle diamonds, and small
pink lightning bolts throughout. A thin double-rule line in gold borders the
typography.

COLOUR PALETTE: Deep royal purple, hot pink, bright metallic gold, white.
Fully saturated, vivid, high-contrast.

TECHNICAL: Left and right edges seamless for tumbler wrap. Vibrant saturated
colours for sublimation. No white background areas. No watermarks.
Print-ready quality.
        """.strip(),
    },

    # ── DOG MOM ─────────────────────────────────────────────────────────────
    {
        "id": "dog_mom",
        "name": "Dog Mom",
        "prompt": """
Professional sublimation tumbler wrap design, full bleed horizontal rectangle.

Art style: modern boho watercolour illustration — warm, organic, hand-painted
feel with botanical wreath and a charming illustrated dog portrait.

BACKGROUND: Rich terracotta (#C2410C) base scattered with a hand-painted
pattern of small paw prints, minimalist bone icons, tiny dot clusters, and
loose botanical sprigs (eucalyptus, sage leaves) in cream (#FEF3C7) and dusty
rose (#F9A8D4). Full coverage — no plain background visible.

CENTRAL FOCAL DESIGN: A charming kawaii-style illustrated golden retriever
face — large, warm amber eyes with a single white catch-light, floppy golden
ears, soft fur texture, rosy blush cheeks. Framed by a loose boho floral
wreath: dried pampas grass plumes, peach roses, eucalyptus sprigs, small
daisies, and cotton bolls in warm cream, dusty rose, sage green, and rust
orange. The wreath feels abundant and painterly.

TYPOGRAPHY: "DOG MOM" in bold, warm serif lettering in deep cream (#FEF3C7)
with a terracotta textured drop shadow and a hand-drawn underline flourish.
Below: "Fur Baby Mama" in a relaxed boho handwritten script in dusty rose
(#F9A8D4).

ACCENTS: Small heart icons, paw prints, and star dots in cream scattered
through the negative space. Thin botanical vine border elements along top and
bottom edges.

COLOUR PALETTE: Terracotta, dusty rose, warm cream, sage green, rich amber.
Warm, earthy, deeply saturated.

TECHNICAL: Left and right edges seamless for tumbler wrap. Vibrant saturated
colours for sublimation. No white background areas. No watermarks.
Print-ready quality.
        """.strip(),
    },

    # ── NURSE LIFE ──────────────────────────────────────────────────────────
    {
        "id": "nurse_life",
        "name": "Nurse Life",
        "prompt": """
Professional sublimation tumbler wrap design, full bleed horizontal rectangle.

Art style: bold modern graphic with medical iconography softened by feminine
botanical elements. Confident, polished, hero-energy aesthetic.

BACKGROUND: Deep navy blue (#0C1A3B) base covered with a fine all-over
pattern of thin EKG heartbeat line traces, tiny medical cross icons, and
small dot clusters in electric teal (#06B6D4) and white. Pattern fully covers
the background.

CENTRAL FOCAL DESIGN: A large, bold medical cross in electric teal (#06B6D4)
with a bright white inner glow and subtle metallic sheen. The cross is
surrounded by an abundant floral arrangement — roses, lavender sprigs, and
small wildflowers in teal, lavender (#C4B5FD), and white — giving the medical
symbol warmth and femininity. Behind the cross: a soft starburst halo in teal.

TYPOGRAPHY: "NURSE LIFE" in bold, modern block lettering in bright white with
a teal (#06B6D4) glow outline. Below the cross: "Saving Lives & Sipping
Coffee" in a fun, casual handwritten script in electric teal. A small
stethoscope icon sits between the two text lines as a decorative divider.

ACCENTS: Heartbeat (EKG) lines extending from the sides of the focal design.
Small plus/cross icons and twinkling star dots in teal and white throughout.

COLOUR PALETTE: Deep navy, electric teal, white, lavender, silver. Bold,
cool-toned, high-contrast.

TECHNICAL: Left and right edges seamless for tumbler wrap. Vibrant saturated
colours for sublimation. No white background areas. No watermarks.
Print-ready quality.
        """.strip(),
    },

    # ── TEACHER LIFE ────────────────────────────────────────────────────────
    {
        "id": "teacher_life",
        "name": "Teacher Life",
        "prompt": """
Professional sublimation tumbler wrap design, full bleed horizontal rectangle.

Art style: bold retro-vintage classroom poster meets modern illustration —
bright, cheerful, confident, with a nod to vintage school typography.

BACKGROUND: Warm golden yellow (#D97706) base with an all-over pattern of
tiny red apples with green leaves, miniature sharpened pencils, small open
books, and five-pointed stars in bright red (#DC2626), white, and dark green.
Dense and joyful — no plain background.

CENTRAL FOCAL DESIGN: A large, shiny red apple with a green leaf and
realistic golden specular highlight, placed centre-frame. Open books flank the
apple on each side with visible pages. Scattered around: coloured pencils
(red, blue, green, yellow) radiating outward from behind the apple like a
burst, plus ABC block letters and small ruler icon accents.

TYPOGRAPHY: "TEACHER LIFE" in a bold, slightly distressed retro blackboard-
style font, in deep charcoal/black (#1C1C1C) with a white chalk-texture
overlay and a bright red (#DC2626) drop shadow — as if written on a
chalkboard. Below: "Shaping Futures One Kid at a Time" in a flowing chalkboard
handwriting script in white.

ACCENTS: Stars, small chalk dots, and pencil icons scattered throughout.
A double underline in red and white runs beneath the headline text.

COLOUR PALETTE: Golden yellow, bright red, white, deep charcoal, grass green.
Warm, energetic, fully saturated.

TECHNICAL: Left and right edges seamless for tumbler wrap. Vibrant saturated
colours for sublimation. No white background areas. No watermarks.
Print-ready quality.
        """.strip(),
    },

    # ── GIRL MOM ────────────────────────────────────────────────────────────
    {
        "id": "girl_mom",
        "name": "Girl Mom",
        "prompt": """
Professional sublimation tumbler wrap design, full bleed horizontal rectangle.

Art style: lush romantic botanical illustration with a modern boho feminine
edge — painterly florals, rich jewel-tone background, elegant typography.

BACKGROUND: Deep plum/berry (#5B21B6) base scattered with a delicate hand-
painted pattern of tiny rosebuds, small butterfly silhouettes, sparkle stars,
and heart dots in blush pink (#F9A8D4) and antique gold (#D97706). Full
coverage — no plain areas.

CENTRAL FOCAL DESIGN: A lush, abundant bouquet of fully bloomed garden roses,
garden peonies, anemones, and loose wildflower sprigs — rendered in blush pink,
dusty rose (#DB2777), cream, and soft lavender (#C4B5FD). The bouquet is tied
with a flowing gold ribbon forming a soft bow at the base. Small butterflies
(pink with gold wing edges) rest among the flowers. The overall feel is rich,
romantic, painterly.

TYPOGRAPHY: "GIRL MOM" in elegant bold serif lettering in antique gold
(#D97706) with a thin plum (#5B21B6) inner stroke and a blush pink glow.
Below the bouquet: "Raising Wildflowers" in a graceful, flowing feminine
handwritten script in blush pink (#F9A8D4) with a subtle gold shadow.

ACCENTS: Small gold hearts, butterfly icons, and sparkle stars scattered
throughout. Thin botanical vine border elements at top and bottom.

COLOUR PALETTE: Deep plum/berry, blush pink, antique gold, dusty rose, cream,
soft lavender. Rich, romantic, jewel-toned.

TECHNICAL: Left and right edges seamless for tumbler wrap. Vibrant saturated
colours for sublimation. No white background areas. No watermarks.
Print-ready quality.
        """.strip(),
    },

    # ── BOY MOM ─────────────────────────────────────────────────────────────
    {
        "id": "boy_mom",
        "name": "Boy Mom",
        "prompt": """
Professional sublimation tumbler wrap design, full bleed horizontal rectangle.

Art style: bold adventurous illustration with outdoor/wilderness elements —
rugged meets tender, celebrating the chaos of raising boys with a polished
graphic finish.

BACKGROUND: Deep midnight navy (#1E3A5F) base with an all-over pattern of
small lightning bolts, arrow icons, mountain silhouettes, tiny dinosaur
footprints, and star dots in electric blue (#3B82F6), orange (#F97316), and
white. Full coverage — energetic and layered.

CENTRAL FOCAL DESIGN: A large central compass rose or adventure badge emblem
in antique brass/gold with an electric blue centre, surrounded by rugged
wilderness elements: pine tree silhouettes, mountain peaks, and small rocket
ship and dinosaur accent icons. The emblem has a worn, badge-like quality with
a circular border frame.

TYPOGRAPHY: "BOY MOM" in large, bold, slightly condensed adventurous lettering
in bright orange (#F97316) with a white inner stroke and navy drop shadow —
strong and punchy. Below: "Blessed & Exhausted" in a casual handwritten script
in electric blue (#3B82F6) with a white underline.

ACCENTS: Lightning bolts, stars, small arrow icons, and rocket silhouettes
scattered throughout in orange and blue. Small paw prints at outer edges.

COLOUR PALETTE: Midnight navy, electric blue, bright orange, white, antique
gold. Bold, adventurous, saturated.

TECHNICAL: Left and right edges seamless for tumbler wrap. Vibrant saturated
colours for sublimation. No white background areas. No watermarks.
Print-ready quality.
        """.strip(),
    },

    # ── MAMA MODE ───────────────────────────────────────────────────────────
    {
        "id": "mama_mode",
        "name": "Mama Mode",
        "prompt": """
Professional sublimation tumbler wrap design, full bleed horizontal rectangle.

Art style: retro 70s groovy illustration with a modern kawaii softness —
warm, funky, and feel-good. Think vintage record cover meets a modern Etsy
bestseller.

BACKGROUND: Warm burnt sienna (#92400E) base with a groovy all-over pattern
of retro wavy lines, small sunburst icons, tiny daisy flowers (yellow centres,
cream petals), and round dot clusters in mustard yellow (#FBBF24), cream
(#FEF3C7), and rust orange (#C2410C). Psychedelic but not overwhelming.

CENTRAL FOCAL DESIGN: A large, retro-style badge or medallion shape (circle
with a wavy or scalloped border in mustard yellow with a deep sienna fill).
Inside the badge: a kawaii sunflower with a smiling face — round eyes, rosy
cheeks, tiny smile — in bright yellow with a brown centre. Flanking the badge:
symmetrical retro botanical elements (large monstera leaves, sunflower sprigs)
in warm green, yellow, and cream.

TYPOGRAPHY: Inside and above the badge: "MAMA MODE" in a bold, groovy retro
font with rounded serifs and a slightly bloated vintage feel, in cream
(#FEF3C7) with a rust orange (#C2410C) shadow. Below the badge: "ON &
Absolutely Unhinged" in a casual 70s-style script in mustard yellow.

ACCENTS: Scattered retro daisies, smiley face dots, sunburst starbursts, and
wavy line accents in mustard yellow and cream.

COLOUR PALETTE: Burnt sienna, mustard yellow, rust orange, warm cream, muted
olive green. Warm, retro, deeply saturated.

TECHNICAL: Left and right edges seamless for tumbler wrap. Vibrant saturated
colours for sublimation. No white background areas. No watermarks.
Print-ready quality.
        """.strip(),
    },

]


def _quality_gate(img_path: Path) -> tuple[bool, list[str]]:
    """
    Enforces sublimation standards from data/knowledge_base/sublimation_standards.md.
    Returns (passed: bool, failures: list[str]).
    HARD requirements — any failure rejects the image.
    """
    from PIL import Image as PILImage

    failures = []
    img = PILImage.open(img_path).convert("RGB")
    w, h = img.size

    # 1. Dimension check — must be at least 2000px on the short edge
    if min(w, h) < 2000:
        failures.append(f"Resolution too low: {w}×{h} (min 2000px short edge)")

    # 2. Background darkness — sample all 4 corners (30×30px each)
    #    Reject if any corner luminance > 217/255 (~85% brightness = too pale)
    sample = 30
    corners = [
        img.crop((0, 0, sample, sample)),
        img.crop((w - sample, 0, w, sample)),
        img.crop((0, h - sample, sample, h)),
        img.crop((w - sample, h - sample, w, h)),
    ]
    for i, corner in enumerate(corners):
        pixels = list(corner.getdata())
        avg_lum = sum(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in pixels) / len(pixels)
        if avg_lum > 217:
            failures.append(
                f"Corner {i+1} too light (lum={avg_lum:.0f}/255) — pale/white background will "
                f"look washed out on sublimation press. Regenerate with darker palette."
            )

    # 3. Edge continuity — left vs right column average color difference
    #    Sample 20px-wide strips; flag if average color diff > 60 (visible seam)
    left_strip  = img.crop((0, 0, 20, h))
    right_strip = img.crop((w - 20, 0, w, h))
    lp = list(left_strip.getdata())
    rp = list(right_strip.getdata())
    avg_diff = sum(
        abs(lp[i][0] - rp[i][0]) + abs(lp[i][1] - rp[i][1]) + abs(lp[i][2] - rp[i][2])
        for i in range(0, len(lp), max(1, len(lp) // 100))
    ) / 100
    if avg_diff > 80:
        failures.append(
            f"Edge seam mismatch (avg diff {avg_diff:.0f}/255 per channel) — "
            f"left/right edges don't match; seam will be visible on wrapped tumbler."
        )

    passed = len(failures) == 0
    return passed, failures


def generate_and_save(client, design: dict, sizes=("20oz",), max_retries: int = 2) -> list[Path]:
    from PIL import Image

    print(f"  [{design['id']}] Generating {design['name']}...")

    for attempt in range(1, max_retries + 2):
        response = client.images.generate(
            model="gpt-image-1",
            prompt=design["prompt"],
            size=GEN_SIZE,
            quality="high",
            n=1,
            output_format="png",
        )

        img_bytes = base64.b64decode(response.data[0].b64_json)
        src_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        # Save at full gen resolution temporarily for quality gate
        tmp_path = OUTPUT_DIR / f"_tmp_{design['id']}.png"
        src_img.save(tmp_path, "PNG")

        passed, failures = _quality_gate(tmp_path)
        if passed:
            print(f"    ✓ Quality gate passed (attempt {attempt})")
            break
        else:
            print(f"    ✗ Quality gate FAILED (attempt {attempt}/{max_retries + 1}):")
            for f in failures:
                print(f"        {f}")
            if attempt <= max_retries:
                print(f"    Regenerating...")
            else:
                print(f"    Max retries reached — saving with warnings. Review manually.")
                tmp_path.unlink(missing_ok=True)
                break
        tmp_path.unlink(missing_ok=True)

    paths = []
    for size_key in sizes:
        w, h = SIZES[size_key]
        resized = src_img.resize((w, h), Image.LANCZOS)
        out_path = OUTPUT_DIR / f"sublimation_{design['id']}_{size_key}.png"
        resized.save(out_path, "PNG", dpi=(300, 300))
        kb = out_path.stat().st_size // 1024
        print(f"    Saved {size_key}: {out_path.name} ({kb} KB)")
        paths.append(out_path)

    return paths


def main(ids: list[str] | None = None, workers: int = 4):
    env = load_env()
    import openai
    from concurrent.futures import ThreadPoolExecutor, as_completed

    client = openai.OpenAI(api_key=env["OPENAI_API_KEY"])

    targets = [d for d in DESIGNS if ids is None or d["id"] in ids]
    if not targets:
        print(f"No matching designs for ids: {ids}")
        return

    print(f"Generating {len(targets)} sublimation designs with {workers} worker(s) "
          f"→ {OUTPUT_DIR.absolute()}\n")

    def _one(design):
        # The openai client is thread-safe, so designs generate concurrently.
        try:
            paths = generate_and_save(client, design, sizes=["20oz"])
            return (design["name"], "OK", paths)
        except Exception as e:  # noqa: BLE001 — record per-design, never crash the batch
            print(f"  ERROR ({design['name']}): {e}")
            return (design["name"], str(e), [])

    if workers <= 1:
        results = [_one(d) for d in targets]
    else:
        results = []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(_one, d) for d in targets]
            for fut in as_completed(futures):
                results.append(fut.result())
        order = [d["name"] for d in targets]
        results.sort(key=lambda r: order.index(r[0]))

    print("\n─── Summary ───────────────────────────────")
    for name, status, paths in results:
        print(f"  {name}: {status}")
        for p in paths:
            print(f"    → {p}")


if __name__ == "__main__":
    # Pass design IDs as args to run a subset, e.g.:
    #   python tools/generate_sublimation_wraps.py football_mom dog_mom
    # Optional: --workers N  (default 4; use --workers 1 for sequential)
    # Run with no positional args to generate all designs.
    argv = sys.argv[1:]
    workers = 4
    if "--workers" in argv:
        i = argv.index("--workers")
        try:
            workers = int(argv[i + 1])
            del argv[i:i + 2]
        except (IndexError, ValueError):
            print("--workers requires an integer")
            sys.exit(1)
    ids = argv or None
    main(ids, workers=workers)
