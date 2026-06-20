"""
generate_celestial_assets.py — OpenAI-generated production assets for DP1034
(Ultimate Celestial Life Planner).

Produces, all via gpt-image-1:
  1. A premium illustrated cover  -> DP1034_cover_ai.png (portrait, high quality)
  2. Five transparent kawaii celestial sticker SHEETS (the functional product
     customers import into GoodNotes Elements / Notability) ->
     DP1034_sticker_sheet_1..5.png  (background="transparent", PNG)

It then, with no further API calls:
  3. Auto-crops each sheet into individual transparent PNG stickers (connected
     non-transparent regions) so the pack ships pre-cropped singles too — and so
     the sticker COUNT in the listing is a real measured number, never a guess.
  4. Packages everything into DP1034_sticker_pack.zip with a README, matching the
     ZIP structure in CLAUDE.md (png_sheets/, individual_stickers/).

Run:  python tools/generate_celestial_assets.py            # cover + sheets + zip
      python tools/generate_celestial_assets.py --stickers-only
      python tools/generate_celestial_assets.py --cover-only
"""
import sys
import zipfile
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.image_gen import generate_image, SQUARE, PORTRAIT

ART = _BASE_DIR / "data" / "digital_products" / "product_files"
PID = "DP1034"

_STYLE = (
    "Kawaii chibi sticker sheet, flat vector illustration style, bold clean 2px "
    "dark-indigo outlines, soft cel shading, tiny white catch-light in each eye, "
    "small blush cheeks. Celestial Night palette ONLY: deep indigo #1E1B4B, "
    "twilight purple #6B5FA5, starlight gold #C9A84C, moonbeam off-white #F0EEF8. "
    "Stickers arranged in a neat evenly-spaced grid with clear gaps between each "
    "sticker so they can be cut apart, every sticker fully separated, no overlap. "
    "TRANSPARENT background (no backdrop, no paper, no shadow behind the grid). "
    "Crisp, premium, professional digital planner sticker art."
)

SHEETS = {
    1: ("Functional Planning",
        "About 24 FUNCTIONAL planner stickers on a transparent grid: ribbon header "
        "banners reading 'TODAY', 'THIS WEEK', 'GOALS', 'DON'T FORGET'; small "
        "checkbox rows; a priority star; a due-date flag; date dots numbered; an "
        "arrow; an exclamation 'urgent' badge; a small sticky note; a page flag; "
        "a clock; a tiny calendar pin. Celestial accents (tiny stars, a crescent)."),
    2: ("Widget Trackers",
        "About 20 widget tracker stickers on a transparent grid: a 5-face mood "
        "tracker row, an 8-cup water-intake widget, a moon-phase sleep tracker, a "
        "7-circle habit streak, an energy battery meter, a weekly summary box, a "
        "star-rating widget, a gratitude box. All in celestial indigo and gold."),
    3: ("Planner & Stationery",
        "About 22 cute stationery stickers on a transparent grid: a mini notebook, "
        "a fountain pen, washi tape rolls, paper clips, a highlighter, scissors, a "
        "ruler and pencil, a coffee cup with a moon on it, a desk lamp, bookmarks, "
        "sticky notes, a stack of star-covered books. Celestial indigo + gold."),
    4: ("Cozy Celestial Lifestyle",
        "About 22 cozy celestial stickers on a transparent grid: a sleeping "
        "crescent-moon character with a nightcap, a steaming star-print mug, a "
        "lit candle, fairy lights, an open spellbook of stars, a sleepy cat curled "
        "on a moon, a cozy blanket, tiny potted plants, a teacup, a crystal. "
        "Celestial Night palette, kawaii, dreamy."),
    5: ("Celestial & Seasonal",
        "About 24 celestial motif stickers on a transparent grid: crescent moons "
        "with faces, full moon, stars and shooting stars/comets, tiny planets with "
        "rings, constellations, a sun-and-moon, a crystal ball, a tarot-style 'star' "
        "card, a telescope, clouds with stars, a rainbow of stars. Indigo + gold."),
    6: ("Zodiac & Affirmations",
        "About 45 small stickers on a transparent grid: 12 minimalist zodiac "
        "constellation glyph badges (one per sign, each in a small round starlight-"
        "gold badge), and celestial affirmation ribbon banners reading 'Trust The "
        "Timing', 'Aligned & Calm', 'Made Of Stardust', 'Dream Big', 'Stay Grounded', "
        "'New Moon New Me', 'Written In The Stars' in a soft kawaii script, plus tiny "
        "sparkle and star accents scattered between each badge/banner. Celestial "
        "Night palette only: deep indigo, twilight purple, starlight gold, moonbeam "
        "off-white."),
    7: ("Bonus Celestial Extras",
        "About 45 small stickers on a transparent grid, densely packed in neat rows: "
        "tiny constellation line-art badges (Big Dipper, Orion, Cassiopeia, Southern "
        "Cross), small planet ring icons, a sleepy sun-and-moon pair, a dreamcatcher, "
        "a crystal cluster, a tarot star card, a telescope, a witchy spellbook, a "
        "cauldron with sparkles, tiny shooting stars, a zodiac wheel, a moon-phase "
        "strip (8 phases in a row), and a few celestial wax-seal style stamps. "
        "Celestial Night palette only: deep indigo, twilight purple, starlight gold, "
        "moonbeam off-white."),
    8: ("Date Dots & Labels",
        "About 50 tiny stickers on a transparent grid, very densely packed in small "
        "uniform rows with thin gaps: filled circle date-dot numbers 1 through 31 "
        "(small round gold badges with indigo numerals), plus 8 small color-coded "
        "category label dots, plus a row of small month-abbreviation tab labels "
        "(JAN through DEC, tiny rounded rectangle tags). Celestial Night palette "
        "only: deep indigo, twilight purple, starlight gold, moonbeam off-white."),
    9: ("Mini Icons & Motivational Tags",
        "About 45 tiny stickers on a transparent grid, densely packed in small "
        "uniform rows: small celestial weather icons (starry night, cloudy moon, "
        "clear sky), small mini moon-face expressions (happy, sleepy, excited, "
        "calm), small star-rating rows, small priority flags in three sizes, small "
        "motivational tag stickers reading 'Rest Is Productive', 'One Step At A "
        "Time', 'Cosmic Reset', 'Shine On'. Celestial Night palette only: deep "
        "indigo, twilight purple, starlight gold, moonbeam off-white."),
}


def generate_cover():
    out = ART / f"{PID}_cover_ai.png"
    prompt = (
        "Premium celestial digital planner COVER illustration, portrait. "
        "Deep indigo night-sky background (#1E1B4B) with a soft gradient to twilight "
        "purple (#6B5FA5), a scatter of tiny starlight-gold stars and a delicate gold "
        "constellation line pattern. Center: an elegant crescent moon with a calm, "
        "sleepy kawaii face, ringed by a thin gold celestial border, with tiny orbiting "
        "planets, a comet and a few sparkles. Refined, mystical, high-end. "
        "Leave clear calm space in the lower third for a title to be added later. "
        "No text, no lettering, no words anywhere in the image."
    )
    print(f"  Generating AI cover -> {out.name}")
    generate_image(prompt, out, size=PORTRAIT, quality="high", output_format="png")
    return out


def generate_sheets(nums=range(1, 6)):
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

        # Iterative flood-fill labeling (BFS) over the alpha mask
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


_README = """OnBrandCraftz - Ultimate Celestial Life Planner - Sticker Pack
==============================================================

WHAT'S INSIDE
  png_sheets/          5 full sticker sheets (transparent PNG)
  individual_stickers/ every sticker pre-cropped as its own transparent PNG

HOW TO USE IN GOODNOTES 6
  1. Unzip this pack.
  2. Open GoodNotes 6 -> tap the Elements button (diamond icon).
  3. Stickers tab -> tap + -> select the 5 PNG sheets in png_sheets/.
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
    ap.add_argument("--cover-only", action="store_true")
    ap.add_argument("--stickers-only", action="store_true")
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
        all_sheets = [ART / f"{PID}_sticker_sheet_{n}.png" for n in sorted(SHEETS)]
        n_total = len(list(ind_dir.glob("*.png")))
        build_zip(all_sheets, ind_dir, n_total)
        print(f"Done. Total individual stickers now: {n_total}")
        return

    if not args.stickers_only:
        generate_cover()
    if not args.cover_only:
        sheets = generate_sheets()
        ind_dir = ART / f"{PID}_individual_stickers"
        print("  Auto-cropping individual stickers...")
        n = autocrop_individuals(sheets, ind_dir)
        build_zip(sheets, ind_dir, n)
    print("Done.")


if __name__ == "__main__":
    main()
