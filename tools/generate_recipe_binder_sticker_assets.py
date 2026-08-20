"""
generate_recipe_binder_sticker_assets.py — sticker pack for RB1001 (Digital
Recipe Binder, Mocha Latte theme).

Follows the exact proven per-product pattern in generate_sunflower_studio_
assets.py / generate_adhd_assets.py / etc. (module-level PID, _STYLE, SHEETS)
rather than inventing a new structure -- same gpt-image-1 transparent-sheet
generation, same connected-component autocrop, same 256-color quantize, same
ZIP layout (png_sheets/, individual_stickers/, README.txt).

Built 2026-08-20 specifically because the recipe binder PDF's Sticker Library
reference page describes a sticker pack that, until this script runs, does not
exist as real files -- the cardinal "never lie to the customer" rule means
that page cannot ship without this ZIP actually being built and verified.

9 sheets: the 5 required by CLAUDE.md's sticker system (Functional Planning,
Widget Trackers, Planner & Stationery, Cozy Lifestyle, Seasonal & Holiday) plus
4 recipe-binder-specific bonus sheets (Kitchen Tools & Cookware, Ingredients &
Pantry Icons, Recipe Wins & Ratings, Food & Drink Motifs) -- matching the
bonus-sheet-count precedent set by DP1033 (Teacher Planner, 4 classroom bonus
sheets on top of the same 5-sheet base).

Run:  python tools/generate_recipe_binder_sticker_assets.py
      python tools/generate_recipe_binder_sticker_assets.py --append-sheets 6,7
"""
import sys
import zipfile
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.image_gen import generate_image, SQUARE

ART = _BASE_DIR / "data" / "digital_products" / "product_files"
PID = "RB1001"

_STYLE = (
    "Kawaii chibi sticker sheet, flat vector illustration style, bold clean 2px "
    "espresso-brown outlines, soft cel shading, tiny white catch-light in each "
    "eye, small blush cheeks. Mocha Latte palette ONLY: warm mocha #8B5E3C, "
    "caramel #D4A96A, latte beige #C8A882, cream foam #FDF8F0, espresso "
    "#2C1A0E. Stickers arranged in a neat evenly-spaced grid with clear gaps "
    "between each sticker so they can be cut apart, every sticker fully "
    "separated, no overlap. TRANSPARENT background (no backdrop, no paper, no "
    "shadow behind the grid). Crisp, premium, professional digital planner "
    "sticker art, cozy café aesthetic."
)

SHEETS = {
    1: ("Functional Planning",
        "About 24 FUNCTIONAL planner stickers on a transparent grid: ribbon "
        "header banners reading 'MEAL PREP', 'THIS WEEK', 'TOP 3', 'DON'T "
        "FORGET'; small checkbox rows; a priority star; a due-date flag; date "
        "dots numbered; an action arrow; an exclamation 'urgent' badge; a small "
        "sticky note; a page flag; a tiny clock; a coffee-bean bookmark tab. "
        "Warm mocha and caramel."),
    2: ("Widget Trackers",
        "About 20 widget tracker stickers on a transparent grid: a 5-face mood "
        "tracker row, an 8-cup water-intake widget, a sleep-quality moon "
        "widget, a 7-circle habit streak shaped like coffee beans, an energy "
        "battery meter, a 'meal prepped' notepad widget, a weekly grocery "
        "budget widget, a 'today's wins' celebration box, a calorie-goal dial. "
        "All in warm mocha and caramel."),
    3: ("Planner & Stationery",
        "About 22 cute stationery stickers on a transparent grid: a mini "
        "recipe notebook, a fountain pen, washi tape rolls, paper clips, a "
        "highlighter, scissors, a ruler and pencil, a latte cup with a heart "
        "in the foam, a desk lamp, bookmarks, sticky notes, a red stamp marked "
        "'TESTED & APPROVED'. Mocha and caramel, kawaii."),
    4: ("Cozy Lifestyle",
        "About 22 cozy lifestyle stickers on a transparent grid: a sleeping "
        "cat curled by a warm oven, a steaming latte mug with foam art, a lit "
        "candle, fairy lights, an open cookbook with a ribbon bookmark, a pair "
        "of oven mitts, a soft apron folded, a small potted herb plant, a "
        "croissant, a bowl of coffee beans, a cozy kitchen nook chair. Mocha "
        "Latte palette, kawaii, warm and inviting."),
    5: ("Seasonal & Holiday",
        "About 24 seasonal motif stickers on a transparent grid: cherry "
        "blossom branch (spring), a sun and lemonade glass (summer), a pumpkin "
        "and falling leaf (fall), a snowflake and gingerbread man (winter), a "
        "small gift box, a heart for valentines, a firework for new year, a "
        "candle for any holiday. All rendered in warm mocha and caramel with "
        "cream accents."),
    6: ("Kitchen Tools & Cookware",
        "About 22 kitchen-tool stickers on a transparent grid: a whisk, a "
        "rolling pin, a chef's knife and cutting board, a mixing bowl with a "
        "spoon, a stand mixer, measuring cups nested together, a cast-iron "
        "skillet, a saucepan, an oven mitt, a colander, a cheese grater, a "
        "spatula, a kitchen timer shaped like a tomato, a ladle. Warm mocha "
        "and caramel, kawaii chibi style with cute little faces on a few "
        "items."),
    7: ("Ingredients & Pantry Icons",
        "About 24 ingredient stickers on a transparent grid: a wedge of "
        "cheese, a bunch of carrots, an egg with a smiling face, a loaf of "
        "bread, a jar of honey, a bag of flour, a cluster of grapes, a "
        "tomato, a garlic bulb, a jar of spices, a stick of butter, a bottle "
        "of olive oil, a bunch of herbs tied with twine, a bowl of berries. "
        "Mocha Latte palette, kawaii, appetizing and cute."),
    8: ("Recipe Wins & Ratings",
        "About 20 recipe-review stickers on a transparent grid designed to "
        "rate and celebrate recipes: a 5-star rating row, a 'FAMILY "
        "FAVORITE' ribbon banner, a 'MAKE AGAIN!' badge, a thumbs-up icon, a "
        "'NAILED IT' banner, a chef's-hat badge, a 'NEEDS TWEAKING' flag, a "
        "heart-eyes emoji face, a 'FIRST TRY!' badge, a trophy cup, a "
        "'CROWD PLEASER' ribbon. Warm mocha, caramel, cheerful and "
        "encouraging."),
    9: ("Food & Drink Motifs",
        "About 24 small food and drink stickers on a transparent grid: a "
        "steaming coffee cup, a slice of pie, a stack of pancakes with syrup, "
        "a taco, a bowl of soup, a cupcake with frosting, a pizza slice, a "
        "smoothie in a glass, a donut, a sandwich, a plate of pasta, a "
        "cookie, a milkshake with a straw, a basket of muffins. Mocha Latte "
        "palette only: warm mocha, caramel, latte beige, cream foam, "
        "espresso."),
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


_README = """OnBrandCraftz - Digital Recipe Binder (Mocha Latte) - Sticker Pack
====================================================================

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
