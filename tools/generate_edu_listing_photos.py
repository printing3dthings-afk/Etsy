"""
generate_edu_listing_photos.py — 10 real listing photos per EDU-series
tracing workbook (EDU1001/EDU1002/EDU1003), built 2026-08-21.

Why this isn't listing_photo_pipeline.py's build_planner_photo_set(): that
helper is shaped for DP-series planners specifically (monthly/weekly
spreads, sticker sheets) -- these tracing workbooks have neither, so
force-fitting that function's slot list would produce photos claiming
content (stickers, monthly calendars) these products don't have. This
module defines its own 10-slot plan using the SAME underlying primitive
(tools.image_gen.edit_image, the real "images.edit"-style call using the
actual rendered PDF page as input, per CLAUDE.md's cardinal photo rule)
just with EDU-appropriate content: letter/number/shape/word/cursive/
sentence/math tracing pages instead of planner spreads.

Does NOT use listing_photo_pipeline.generate_verified_photo()'s automated
GPT-4o-mini/4o text-extraction+verification loop -- that loop is
hardcoded to OpenAI's vision models for the extract/verify steps
regardless of which engine generates the image, and OpenAI has zero
credits this session (confirmed live, HTTP 429 insufficient_quota) same
as Gemini (also confirmed 429 RESOURCE_EXHAUSTED). Only engine="grok" is
funded. Every photo here is generated via edit_image(engine="grok") and
must be manually inspected against its real source render before
acceptance -- same manual-verification discipline already used for this
session's cover art (which caught 2 real bugs that an automated loop
would also have needed a working OpenAI/Gemini call to catch).

Run standalone:
    python tools/generate_edu_listing_photos.py EDU1001
"""
import sys
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

import fitz
from tools.image_gen import edit_image, ImageGenError, SQUARE

SRC_DIR = _BASE_DIR / "data" / "digital_products" / "product_files" / "listing_photo_src"
OUT_DIR = _BASE_DIR / "data" / "digital_products" / "product_files" / "listing_photos"
PDF_DIR = _BASE_DIR / "data" / "digital_products" / "product_files"

# Per-product page-finder predicates + prop/style language for the scene prompts.
PRODUCTS = {
    "EDU1001": {
        "pdf": "EDU1001.pdf",
        "pages": {
            "cover": lambda t, i: i == 0,
            "dashboard": lambda t, i: t.startswith("KAWAII TRACING WORKBOOK"),
            "letter": lambda t, i: t.startswith("LETTER Ff"),
            "number": lambda t, i: t.startswith("NUMBER 7"),
            "shape": lambda t, i: t.startswith("STAR"),
            "words": lambda t, i: t.startswith("SIGHT WORDS") and "Page 1" in t,
            "math": lambda t, i: t.startswith("MATH & COLORING") and "Page 2" in t,
            "rewards": lambda t, i: t.startswith("MY REWARD CHART"),
        },
        "props": "a warm ceramic mug, a small eucalyptus sprig in a bud vase, a strip of yellow washi tape",
        "desk": "a cream linen-textured desk",
        "theme_words": "sunflower yellow and soft green kawaii",
    },
    "EDU1002": {
        "pdf": "EDU1002.pdf",
        "pages": {
            "cover": lambda t, i: i == 0,
            "dashboard": lambda t, i: t.startswith("KAWAII TRACING WORKBOOK"),
            "letter": lambda t, i: t.startswith("LETTER Tt"),
            "number": lambda t, i: t.startswith("NUMBER 7"),
            "shape": lambda t, i: t.startswith("TRIANGLE"),
            "words": lambda t, i: t.startswith("SIGHT WORDS") and "Page 1" in t,
            "math": lambda t, i: t.startswith("MATH & COLORING") and "Page 2" in t,
            "rewards": lambda t, i: t.startswith("MY REWARD CHART"),
        },
        "props": "a toy dump truck figurine, a small stack of wooden building blocks, a construction-orange pencil",
        "desk": "a light wood desk",
        "theme_words": "safety orange and steel blue construction-themed kawaii",
    },
    "EDU1003": {
        "pdf": "EDU1003.pdf",
        "pages": {
            "cover": lambda t, i: i == 0,
            "dashboard": lambda t, i: t.startswith("CURSIVE & SKILLS WORKBOOK"),
            "letter": lambda t, i: t.startswith("CURSIVE Ff"),
            "words": lambda t, i: t.startswith("GRADE 1 SIGHT WORDS") and "Page 1" in t,
            "sentence": lambda t, i: t.startswith("SENTENCE WRITING") and "Page 1" in t,
            "addsub": lambda t, i: t.startswith("ADDITION WITH REGROUPING") and "Page 1" in t,
            "mult": lambda t, i: t.startswith("MULTIPLICATION FACTS") and "Page 1" in t,
            "rewards": lambda t, i: t.startswith("MY REWARD CHART"),
        },
        "props": "a small seashell, a teal fine-tip pen, a folded sea-glass-blue notebook",
        "desk": "a light coastal-white desk",
        "theme_words": "ocean teal and seafoam kawaii",
    },
}


def render_sources(pid: str) -> dict[str, Path]:
    cfg = PRODUCTS[pid]
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(PDF_DIR / cfg["pdf"]))
    found: dict[str, Path] = {}
    for key, predicate in cfg["pages"].items():
        idx = None
        for i in range(len(doc)):
            if predicate(doc[i].get_text(), i):
                idx = i
                break
        if idx is None:
            print(f"  ⚠ {pid}: no page matched for slot {key!r}")
            continue
        out = SRC_DIR / f"{pid}_{key}.png"
        doc[idx].get_pixmap(dpi=170).save(str(out))
        found[key] = out
    doc.close()
    return found


def _ipad_scene(cfg: dict, screen_desc: str, angle: str = "30-degree") -> str:
    return (
        f"This image is a real page from a children's tracing workbook PDF. Render it as a "
        f"single photorealistic product photograph: a silver Apple iPad Pro 12.9-inch at a "
        f"{angle} angle on {cfg['desk']}, screen displaying {screen_desc} — the exact page "
        f"content from the input image, sharp and legible. An Apple Pencil rests nearby. "
        f"Props in soft-focus background: {cfg['props']}. Soft natural window light from the "
        f"left, warm white balance. {cfg['theme_words']} color palette. Professional Etsy "
        f"product photography, square composition, no hands, no people, no watermarks."
    )


SLOTS_BASE = [
    # (slot_num, filename_suffix, source_key(s), scene builder)
    (1, "hero", "cover", lambda cfg: _ipad_scene(cfg, "the kawaii illustrated cover")),
    (2, "included", "dashboard", lambda cfg: _ipad_scene(
        cfg, "the Dashboard / Home page with its grid of section buttons, showing the "
             "workbook's real table of contents / section list")),
    (3, "letter", "letter", lambda cfg: _ipad_scene(
        cfg, "a real letter-tracing page with dashed-outline uppercase and lowercase letters "
             "to trace")),
]

SLOTS_1001_1002 = SLOTS_BASE + [
    (4, "number", "number", lambda cfg: _ipad_scene(cfg, "a real number-tracing page")),
    (5, "shape", "shape", lambda cfg: _ipad_scene(cfg, "a real shape-tracing page")),
    (6, "words", "words", lambda cfg: _ipad_scene(cfg, "a real sight-word tracing page")),
    (7, "dashboard2", "dashboard", lambda cfg: _ipad_scene(
        cfg, "the Dashboard / Home page", angle="15-degree")),
    (8, "math", "math", lambda cfg: _ipad_scene(cfg, "a real math and coloring page")),
    (9, "coverclose", "cover", lambda cfg: _ipad_scene(
        cfg, "the kawaii illustrated cover, filling most of the frame", angle="straight-on")),
    (10, "rewards", "rewards", lambda cfg: _ipad_scene(cfg, "the real star reward chart page")),
]

SLOTS_1003 = SLOTS_BASE + [
    (4, "words", "words", lambda cfg: _ipad_scene(cfg, "a real Grade 1 sight-word tracing page")),
    (5, "sentence", "sentence", lambda cfg: _ipad_scene(cfg, "a real sentence-writing page")),
    (6, "addsub", "addsub", lambda cfg: _ipad_scene(
        cfg, "a real addition-with-regrouping math page")),
    (7, "dashboard2", "dashboard", lambda cfg: _ipad_scene(
        cfg, "the Dashboard / Home page", angle="15-degree")),
    (8, "mult", "mult", lambda cfg: _ipad_scene(cfg, "a real multiplication-facts page")),
    (9, "coverclose", "cover", lambda cfg: _ipad_scene(
        cfg, "the kawaii illustrated cover, filling most of the frame", angle="straight-on")),
    (10, "rewards", "rewards", lambda cfg: _ipad_scene(cfg, "the real star reward chart page")),
]


def build(pid: str) -> None:
    cfg = PRODUCTS[pid]
    sources = render_sources(pid)
    slots = SLOTS_1003 if pid == "EDU1003" else SLOTS_1001_1002
    out_dir = OUT_DIR / pid
    out_dir.mkdir(parents=True, exist_ok=True)

    for num, suffix, src_key, scene_fn in slots:
        src = sources.get(src_key)
        if not src or not src.exists():
            print(f"  ⚠ {pid} slot {num} ({suffix}): source {src_key!r} missing, skipping")
            continue
        out_path = out_dir / f"photo_{num:02d}_{suffix}.jpg"
        prompt = scene_fn(cfg)
        print(f"  {pid} slot {num:02d} ({suffix}) <- {src.name} ...", flush=True)
        try:
            edit_image(prompt, [src], out_path, size=SQUARE, quality="high", engine="grok")
            print(f"    OK -> {out_path}")
        except ImageGenError as e:
            print(f"    FAILED: {e}")


def main():
    pids = sys.argv[1:] or list(PRODUCTS)
    for pid in pids:
        print(f"=== {pid} ===")
        build(pid)


if __name__ == "__main__":
    main()
