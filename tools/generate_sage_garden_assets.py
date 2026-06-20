"""
generate_sage_garden_assets.py — OpenAI-generated sticker pack for DP1031
(Undated Life Planner, Sage Garden theme).

Produces, all via gpt-image-1:
  Nine transparent kawaii sticker SHEETS (the functional product customers
  import into GoodNotes Elements / Notability) ->
  DP1031_sticker_sheet_1..9.png  (background="transparent", PNG)

It then, with no further API calls:
  1. Auto-crops each sheet into individual transparent PNG stickers (connected
     non-transparent regions) so the pack ships pre-cropped singles too — and so
     the sticker COUNT in the listing is a real measured number, never a guess.
  2. Packages everything into DP1031_sticker_pack.zip with a README, matching the
     ZIP structure in CLAUDE.md (png_sheets/, individual_stickers/).
  3. Quantizes every PNG to a 256-color palette before zipping (keeps the ZIP
     well under Etsy's 20MB hard limit).

Cover art for DP1031 is handled separately by tools/generate_planner_v2.py
(DP1031_cover_ai.png) — this script only handles the sticker pack.

Run:  python tools/generate_sage_garden_assets.py            # all 9 sheets + zip
      python tools/generate_sage_garden_assets.py --append-sheets 6,7
"""
import sys
import zipfile
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.image_gen import generate_image, SQUARE

ART = _BASE_DIR / "data" / "digital_products" / "product_files"
PID = "DP1031"

_STYLE = (
    "Kawaii chibi sticker sheet, flat vector illustration style, bold clean 2px "
    "deep-forest outlines, soft cel shading, tiny white catch-light in each eye, "
    "small blush cheeks. Sage Garden palette ONLY: sage green #8BA888, soft fern "
    "#C8DDB5, forest sage #556B50, morning dew #F6F8F2, deep forest #2C3828. "
    "Stickers arranged in a neat evenly-spaced grid with clear gaps between each "
    "sticker so they can be cut apart, every sticker fully separated, no overlap. "
    "TRANSPARENT background (no backdrop, no paper, no shadow behind the grid). "
    "Crisp, premium, professional digital planner sticker art, cottagecore aesthetic."
)

SHEETS = {
    1: ("Functional Planning",
        "About 24 FUNCTIONAL planner stickers on a transparent grid: ribbon header "
        "banners reading 'TODAY', 'THIS WEEK', 'TOP 3', 'DON'T FORGET'; small "
        "checkbox rows; a priority star; a due-date flag; date dots numbered; an "
        "action arrow; an exclamation 'urgent' badge; a small sticky note; a page "
        "flag; a tiny clock; a leaf-shaped bookmark tab. Sage green and soft fern."),
    2: ("Widget Trackers",
        "About 20 widget tracker stickers on a transparent grid: a 5-face mood "
        "tracker row, an 8-cup water-intake widget shaped like watering cans, a "
        "sleep-quality moon widget, a 7-circle habit streak, an energy battery "
        "meter shaped like a leaf, a 'brain dump' notepad widget, a weekly summary "
        "widget, a 'today's 3 wins' celebration box, a growth-progress dial. All "
        "in sage green and soft fern."),
    3: ("Planner & Stationery",
        "About 22 cute stationery stickers on a transparent grid: a mini notebook, "
        "a fountain pen, washi tape rolls, paper clips, a highlighter, scissors, a "
        "ruler and pencil, a herbal tea cup with a leaf design, a desk lamp, "
        "bookmarks, sticky notes, a magnifying glass, a stack of books. Sage green "
        "+ soft fern, kawaii."),
    4: ("Cozy Lifestyle",
        "About 22 cozy lifestyle stickers on a transparent grid: a sleeping cat "
        "curled in a flower basket, a steaming herbal tea mug with a leaf design, a "
        "lit candle, fairy lights strung on a vine, an open book with a pressed "
        "flower bookmark, a knit blanket folded, a small potted herb, a teacup, a "
        "basket of dried flowers, a terrarium. Sage Garden palette, kawaii, calm "
        "and grounding."),
    5: ("Seasonal & Holiday",
        "About 24 seasonal motif stickers on a transparent grid: cherry blossom "
        "branch (spring), a sunflower (summer), a pumpkin and falling leaf (fall), "
        "a snowflake and pine sprig (winter), a small gift box, a heart for "
        "valentines, a firework for new year, a candle for any holiday. All "
        "rendered in sage green and soft fern with cream accents."),
    6: ("Garden Tools & Herbs",
        "About 24 cottagecore garden stickers on a transparent grid: a brass "
        "watering can with a smiling face, a trowel and hand fork, a wicker garden "
        "trug full of herbs, terracotta pots with sprouting seedlings, a pair of "
        "garden gloves, a herb bundle tied with twine (lavender, rosemary, mint), "
        "a ladybug, a garden gnome, a wheelbarrow with flowers, a packet of seeds, "
        "a sun hat, a butterfly net. Sage green, soft fern, forest sage."),
    7: ("Cozy Reading Nook",
        "About 22 cottagecore reading-nook stickers on a transparent grid: a "
        "window seat with cushions, a stack of well-loved books, a pair of round "
        "reading glasses, a steaming mug resting on a book, a knit throw blanket, "
        "a basket of yarn with knitting needles, a small reading lamp, a cat "
        "napping on a book, a candle beside an open journal, a pressed-flower "
        "bookmark, a rocking chair silhouette. Sage Garden palette only."),
    8: ("Seasons of the Garden",
        "About 24 stickers on a transparent grid showing a garden through four "
        "seasons: spring sprouts pushing through soil, summer sunflowers in full "
        "bloom, autumn pumpkins and falling leaves on a vine, winter dormant "
        "garden bed under a light dusting of snow with a small evergreen sprig. "
        "Include a small compost bin, a rain barrel, a bee hotel, and a trellis "
        "with climbing vines. Sage green, soft fern, forest sage, morning dew."),
    9: ("Evergreen Goal-Setting",
        "About 24 small stickers on a transparent grid, kawaii ribbon affirmation "
        "banners reading 'Bloom At Your Own Pace', 'Plant The Seed', 'Slow Growth "
        "Is Still Growth', 'Rooted And Grounded', 'Tend To Yourself Too', plus a "
        "growth-chart sprout-to-flower progression icon, a milestone trellis "
        "marker, a seed-packet goal tracker, a small trophy made of leaves, a "
        "sun-and-rain weather pair for 'good days and hard days'. Sage Garden "
        "palette only: sage green, soft fern, forest sage, morning dew, deep "
        "forest."),
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


_README = """OnBrandCraftz - Undated Life Planner - Sticker Pack
=====================================================

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
