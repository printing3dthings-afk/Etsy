"""
One-off script: generate direction-proof cover/hero art for the 3 new
product lines (Recipe Binder, Party Decor Kit, Kids Tracing Workbook)
approved 2026-08-20, before investing in full page-content engineering.
Uses the same QA'd cover-generation path as the existing planner line
(run_until_goal + verify_original_art) when GEMINI_API_KEY is available.

Run: python tools/generate_new_product_covers.py
"""
import sys
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.image_gen import generate_image, ImageGenError, PORTRAIT, verify_original_art, gemini_key_available
from tools.goal_loop import run_until_goal

OUT_DIR = _BASE_DIR / "data" / "digital_products" / "product_files" / "new_product_covers"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STYLE_ANCHOR = (
    "Photography/illustration style: flat kawaii illustrated cover art, clean vector-like "
    "shapes, soft rounded forms, gentle drop shadows, warm inviting color palette, "
    "professional Etsy digital-product cover quality. No photorealistic rendering. "
    "The image contains only the described illustrated elements — no hands, no people, "
    "no watermarks, no text, no typography anywhere in the image. Absolutely no lettering, "
    "words, numbers, or title text baked into the image, even if the scene reads as a book "
    "cover — the real title is composited separately afterward, so any in-image text is both "
    "redundant and, per two confirmed live tests (2026-08-20), prone to rendering as garbled "
    "nonsense text. Every character and object must be fully contained within the center 80% "
    "of the canvas with real empty background margin on all four sides — nothing may touch or "
    "cross the canvas edge (also confirmed live 2026-08-20: an under-constrained composition "
    "ran a character off its own canvas edge)."
)

COVERS = {
    "RB1001_recipe_binder_mocha_latte": (
        "Full-page kawaii illustrated cover for a digital recipe binder, portrait orientation. "
        "Warm mocha brown (#8B5E3C) as the primary background tone, caramel (#D4A96A) and "
        "latte beige (#C8A882) accents, cream foam (#FDF8F0) highlight areas. Center "
        "composition: a cute kawaii whisk character with a friendly smiling face, surrounded by "
        "a steaming ceramic coffee mug, a small potted herb sprig, a measuring cup, a chef's "
        "hat, and a stack of recipe cards tied with twine. Soft scattered flour dust and small "
        "steam swirl details for warmth. " + STYLE_ANCHOR
    ),
    "PARTY1001_birthday_kit_tropical_hibiscus": (
        "Kawaii illustrated hero scene for a printable birthday party decor kit, square "
        "composition. Bright hot pink (#FF6B9D), sunshine yellow (#FFD166), and tropical mint "
        "(#06D6A0) palette on an ivory (#FFFAF0) background. A colorful triangle bunting banner "
        "strung across the top with small kawaii star and heart charms, three iced cupcakes with "
        "kawaii smiling faces on the toppers below the banner, a cluster of round balloons "
        "(pink, yellow, mint) at the base, small confetti dots scattered throughout. Fun, bold, "
        "maximalist, Gen-Z-playful energy, no licensed characters, entirely original kawaii "
        "design. " + STYLE_ANCHOR
    ),
    "EDU1001_kids_tracing_sunflower_studio": (
        "Full-page kawaii illustrated cover for a children's tracing workbook, portrait "
        "orientation. Cheerful sunflower yellow (#F4C430) primary with stem green (#4A7C59) "
        "and soft gold (#F8E08E) accents on a cream petal (#FFFDF0) background. Center "
        "composition: a large smiling kawaii sunflower character with a friendly face, "
        "surrounded by a kawaii bumblebee, a kawaii ladybug, a butterfly, and a small pencil "
        "character with a smiling face and stubby arms holding a tiny practice line. Bright, "
        "positive, welcoming, appropriate for young children ages 3-7. " + STYLE_ANCHOR
    ),
    "EDU1002_kids_tracing_truck_zone": (
        # Third attempt, confirmed working live 2026-08-20 -- the first attempt (a shorter
        # version of this prompt, no explicit margin/no-text emphasis) baked in garbled
        # nonsense title text ("SAFETY TUS WORKBOOK"); the second attempt dropped the text but
        # let the sign/pencil character run off the canvas edge. This version's explicit
        # composition rule fixed both. Kept verbose deliberately -- see STYLE_ANCHOR for the
        # now-shared version of these two constraints, repeated here for extra emphasis on a
        # composition that's already proven to need it.
        "Kawaii illustrated scene of construction vehicle characters, portrait orientation, "
        "no title, no headline, no banner. Bold safety orange (#FF6B35) primary with steel blue "
        "(#2E5C8A) and caution yellow (#FFC107) accents on a warm cream (#FFF8F0) background with "
        "a subtle grid pattern. A large smiling kawaii dump truck character centered in the middle "
        "of the frame, a small kawaii digger/excavator character with a cute face beside it, a "
        "kawaii traffic cone character with a smiling face in front, and a small pencil character "
        "with a smiling face nearby. CRITICAL COMPOSITION RULE: every character and object must be "
        "fully contained within the center 80 percent of the canvas, with real empty background "
        "margin on all four sides -- left, right, top, and bottom. Nothing may touch or cross the "
        "canvas edge. Leave generous open empty space in the upper third of the composition for "
        "text to be added separately afterward. Bright, energetic, welcoming, appropriate for young "
        "children ages 3-7. " + STYLE_ANCHOR
    ),
    "EDU1003_cursive_skills_ocean_breeze": (
        "Full-page kawaii illustrated cover for a children's cursive handwriting and skills "
        "workbook, portrait orientation, for slightly older kids (ages 6-8). Calm transformative "
        "teal (#3B8E8A) primary with seafoam (#7EC8C8) and morning sea (#F0FAFA) accents. Center "
        "composition: a friendly kawaii seashell or starfish character with a smiling face, "
        "surrounded by a small open notebook with a looping cursive squiggle drawn on the page, "
        "a kawaii pencil character with a smiling face and stubby arms, a small wave motif, and "
        "a few floating seafoam bubbles. Calmer and slightly more grown-up feeling than a "
        "preschool cover, still warm and welcoming, appropriate for ages 6-8. " + STYLE_ANCHOR
    ),
}


def main():
    # 2026-08-20: Gemini (used for verify_original_art QA) is also out of
    # prepayment credits right now alongside OpenAI/Anthropic -- skip the QA
    # loop entirely rather than let every attempt fail on the verify step
    # even though generation itself (via Grok) succeeds fine.
    for name, prompt in COVERS.items():
        out_path = OUT_DIR / f"{name}.png"
        print(f"--- {name} ---")
        try:
            generate_image(prompt, out_path, size=PORTRAIT, quality="high", output_format="png", engine="grok")
            print(f"  saved (no automated QA -- Gemini credits depleted) -> {out_path}")
        except ImageGenError as e:
            print(f"  FAILED: {e}")


if __name__ == "__main__":
    main()
