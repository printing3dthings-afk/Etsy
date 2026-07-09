"""
generate_sunflower_studio_assets.py — OpenAI-generated sticker pack for DP1033
(Teacher Planner 2026-2027, Sunflower Studio theme).

Produces, all via gpt-image-1:
  Nine transparent kawaii sticker SHEETS (the functional product customers
  import into GoodNotes Elements / Notability) ->
  DP1033_sticker_sheet_1..9.png  (background="transparent", PNG)

It then, with no further API calls:
  1. Auto-crops each sheet into individual transparent PNG stickers (connected
     non-transparent regions) so the pack ships pre-cropped singles too — and so
     the sticker COUNT in the listing is a real measured number, never a guess.
  2. Packages everything into DP1033_sticker_pack.zip with a README, matching the
     ZIP structure in CLAUDE.md (png_sheets/, individual_stickers/).
  3. Quantizes every PNG to a 256-color palette before zipping (keeps the ZIP
     well under Etsy's 20MB hard limit).

Cover art for DP1033 is handled separately by tools/generate_planner_v2.py
(DP1033_cover_ai.png) — this script only handles the sticker pack.

Run:  python tools/generate_sunflower_studio_assets.py            # all 9 sheets + zip
      python tools/generate_sunflower_studio_assets.py --append-sheets 6,7
"""
import sys
import zipfile
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.image_gen import generate_image, SQUARE

ART = _BASE_DIR / "data" / "digital_products" / "product_files"
PID = "DP1033"

_STYLE = (
    "Kawaii chibi sticker sheet, flat vector illustration style, bold clean 2px "
    "seed-brown outlines, soft cel shading, tiny white catch-light in each eye, "
    "small blush cheeks. Sunflower Studio palette ONLY: sunflower yellow #F4C430, "
    "stem green #4A7C59, soft gold #F8E08E, cream petal #FFFDF0, seed brown "
    "#2A1A00. Stickers arranged in a neat evenly-spaced grid with clear gaps "
    "between each sticker so they can be cut apart, every sticker fully "
    "separated, no overlap. TRANSPARENT background (no backdrop, no paper, no "
    "shadow behind the grid). Crisp, premium, professional digital planner "
    "sticker art, bright cheerful botanical classroom aesthetic."
)

SHEETS = {
    1: ("Functional Planning",
        "About 24 FUNCTIONAL planner stickers on a transparent grid: ribbon "
        "header banners reading 'TODAY', 'THIS WEEK', 'TOP 3', 'DON'T FORGET'; "
        "small checkbox rows; a priority star; a due-date flag; date dots "
        "numbered; an action arrow; an exclamation 'urgent' badge; a small "
        "sticky note; a page flag; a tiny clock; an apple-shaped bookmark tab. "
        "Sunflower yellow and stem green."),
    2: ("Widget Trackers",
        "About 20 widget tracker stickers on a transparent grid: a 5-face mood "
        "tracker row, an 8-cup water-intake widget, a sleep-quality moon widget, "
        "a 7-circle habit streak shaped like sunflower petals, an energy battery "
        "meter, a 'brain dump' notepad widget, a weekly summary widget, a "
        "'today's 3 wins' celebration box, a lesson-progress dial. All in "
        "sunflower yellow and stem green."),
    3: ("Planner & Stationery",
        "About 22 cute stationery stickers on a transparent grid: a mini "
        "notebook, a fountain pen, washi tape rolls, paper clips, a highlighter, "
        "scissors, a ruler and pencil, a coffee mug with an apple design, a desk "
        "lamp, bookmarks, sticky notes, a red stamp marked 'GRADED'. Sunflower "
        "yellow + stem green, kawaii."),
    4: ("Cozy Lifestyle",
        "About 22 cozy lifestyle stickers on a transparent grid: a sleeping cat "
        "curled on a stack of books, a steaming tea mug with a sunflower design, "
        "a lit candle, fairy lights, an open book with a sunflower bookmark, a "
        "pair of headphones with a heart, a soft cardigan folded, a small potted "
        "sunflower, a teacup, a bowl of trail mix, a cozy reading chair. "
        "Sunflower Studio palette, kawaii, warm and cheerful."),
    5: ("Seasonal & Holiday",
        "About 24 seasonal motif stickers on a transparent grid: cherry blossom "
        "branch (spring), a sunflower (summer), a pumpkin and falling leaf "
        "(fall), a snowflake and pine sprig (winter), a small gift box, a heart "
        "for valentines, a firework for new year, a candle for any holiday. All "
        "rendered in sunflower yellow and stem green with cream accents."),
    6: ("Classroom Supplies",
        "About 24 classroom-supply stickers on a transparent grid: a stack of "
        "colorful textbooks, a pencil cup full of pencils and scissors, a box of "
        "crayons, a glue stick, a stapler, a globe, an apple for the teacher, a "
        "ruler, a backpack, a chalkboard eraser, a hole punch, a roll of tape, a "
        "name-tag lanyard, a pair of safety scissors. Sunflower yellow, stem "
        "green, soft gold."),
    7: ("Lesson Plan Icons",
        "About 22 lesson-planning stickers on a transparent grid: a lesson-plan "
        "clipboard with a checklist, a small chalkboard reading 'Objectives', a "
        "bell schedule clock, a worksheet stack with a paperclip, a rubric grid "
        "icon, a 'substitute folder' icon, a seating-chart grid icon, a "
        "curriculum binder, a sticky-note 'remember to grade' reminder, a "
        "standards-checklist icon, a unit-plan calendar page. Sunflower Studio "
        "palette only."),
    8: ("Student Rewards & Stickers-for-Students",
        "About 24 reward-sticker stickers on a transparent grid designed to be "
        "given to students: a gold star badge, a 'GREAT JOB!' ribbon banner, a "
        "smiley sun, a 'SUPER STUDENT' rosette, a trophy, a thumbs-up badge, a "
        "'NICE WORK' banner, a sunflower with a smiling face, a high-five icon, a "
        "'A+' badge, a rainbow ribbon, a 'KEEP GROWING' banner with a sprout. "
        "Bright sunflower yellow, stem green, cheerful and encouraging."),
    9: ("School Year Milestones",
        "About 24 small stickers on a transparent grid: a 'First Day of School' "
        "banner with a backpack, a 'Picture Day' camera icon, a 'Parent-Teacher "
        "Conference' calendar icon, a 'Field Trip' bus icon, a 'Report Cards' "
        "folder icon, a 'Winter Break' snowflake banner, a 'Spring Break' "
        "sunflower banner, a 'Standardized Testing' pencil-and-clock icon, a "
        "'Last Day of School' graduation cap banner, a 'Summer Break' sun icon. "
        "Sunflower Studio palette only: sunflower yellow, stem green, soft gold, "
        "cream petal, seed brown."),
}


def generate_sheets(nums=range(1, 10)):
    paths = []
    for n in nums:
        name, contents = SHEETS[n]
        out = ART / f"{PID}_sticker_sheet_{n}.png"
        prompt = f"{_STYLE}\n\nSheet theme: {name}. {contents}"
        print(f"  Generating sticker sheet {n} ({name}) -> {out.name}")
        generate_image(prompt, out, size=SQUARE, quality="high",
                       output_format="png", background="transparent")
        paths.append(out)
    return paths


def autocrop_individuals(sheet_paths, out_dir, min_frac=0.004, pad=6):
    """Split each transparent sheet into individual sticker PNGs via connected
    components of the alpha channel. Returns total sticker count."""
    from PIL import Image
    import numpy as np

    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for sp in sheet_paths:
        im = Image.open(sp).convert("RGBA")
        a = np.array(im)[:, :, 3]
        mask = a > 40
        H, W = mask.shape
        min_area = int(min_frac * H * W)

        labels = np.zeros((H, W), dtype=np.int32)
        cur = 0
        from collections import deque
        for y in range(H):
            for x in range(W):
                if mask[y, x] and labels[y, x] == 0:
                    cur += 1
                    q = deque([(y, x)])
                    labels[y, x] = cur
                    pix = []
                    while q:
                        cy, cx = q.popleft()
                        pix.append((cy, cx))
                        for dy in (-1, 0, 1):
                            for dx in (-1, 0, 1):
                                ny, nx = cy + dy, cx + dx
                                if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and labels[ny, nx] == 0:
                                    labels[ny, nx] = cur
                                    q.append((ny, nx))
                    if len(pix) >= min_area:
                        ys = [p[0] for p in pix]; xs = [p[1] for p in pix]
                        y0, y1 = max(0, min(ys) - pad), min(H, max(ys) + pad)
                        x0, x1 = max(0, min(xs) - pad), min(W, max(xs) + pad)
                        crop = im.crop((x0, y0, x1, y1))
                        total += 1
                        crop.save(out_dir / f"{sp.stem}_{total:03d}.png")
    return total


def quantize_all(sheet_paths, individuals_dir):
    """256-color palette reduction on every sheet + individual PNG, in place.
    Keeps the ZIP well under Etsy's 20MB limit."""
    from PIL import Image
    targets = list(sheet_paths) + sorted(individuals_dir.glob("*.png"))
    for p in targets:
        im = Image.open(p).convert("RGBA")
        q = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
        q.save(p, optimize=True)
    print(f"  Quantized {len(targets)} PNGs to 256 colors")


_README = """OnBrandCraftz - Teacher Planner 2026-2027 - Sticker Pack
==========================================================

WHAT'S INSIDE
  png_sheets/          9 full sticker sheets (transparent PNG)
  individual_stickers/ every sticker pre-cropped as its own transparent PNG

HOW TO USE IN GOODNOTES 6
  1. Unzip this pack.
  2. Open GoodNotes 6 -> tap the Elements button (diamond icon).
  3. Stickers tab -> tap + -> select the 9 PNG sheets in png_sheets/.
  4. Your stickers now live in your library - drag any onto any page, unlimited times.

NOTABILITY / PDF EXPERT / XODO / ACROBAT
  Insert the PNG sheets (or the individual stickers) as images, then resize.

(c) OnBrandCraftz - Personal use only. Not for resale or redistribution.
"""


def build_zip(sheet_paths, individuals_dir, n_individual):
    zip_path = ART / f"{PID}_sticker_pack.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", _README)
        for sp in sheet_paths:
            zf.write(sp, f"png_sheets/{sp.name}")
        if individuals_dir.exists():
            for p in sorted(individuals_dir.glob("*.png")):
                zf.write(p, f"individual_stickers/{p.name}")
    kb = zip_path.stat().st_size // 1024
    print(f"  ZIP -> {zip_path.name} ({kb} KB, {len(sheet_paths)} sheets, {n_individual} individual stickers)")
    return zip_path


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--append-sheets", type=str, default=None,
                     help="Comma-separated new sheet numbers to generate and merge into "
                          "the existing pack/zip without touching sheets already on disk "
                          "(e.g. '6,7').")
    args = ap.parse_args()

    if args.append_sheets:
        nums = [int(n) for n in args.append_sheets.split(",")]
        new_sheets = generate_sheets(nums=nums)
        ind_dir = ART / f"{PID}_individual_stickers"
        print(f"  Auto-cropping new sheets {nums}...")
        autocrop_individuals(new_sheets, ind_dir)
        quantize_all(new_sheets, ind_dir)
        all_sheets = [ART / f"{PID}_sticker_sheet_{n}.png" for n in sorted(SHEETS)]
        n_total = len(list(ind_dir.glob("*.png")))
        build_zip(all_sheets, ind_dir, n_total)
        print(f"Done. Total individual stickers now: {n_total}")
        return

    sheets = generate_sheets()
    ind_dir = ART / f"{PID}_individual_stickers"
    print("  Auto-cropping individual stickers...")
    n = autocrop_individuals(sheets, ind_dir)
    quantize_all(sheets, ind_dir)
    build_zip(sheets, ind_dir, n)
    print("Done.")


if __name__ == "__main__":
    main()
