"""Maker's Blueprint: the ironing test reel (2026-11-24).

Benson's four-tile ironing coupon, printed by Scott on the P1S. Scott: "C is the best"; he
asked for "a video for one of the series using this". Details are from Benson's pack
(business/muse_claude/threads/2026-11-22_ironing-test-pack.md on main): A = no ironing,
B = 0.10 mm spacing / 10% flow / 15 mm/s, C = 0.15 / 10% / 30 (Bambu's stock values),
D = 0.20 / 15% / 20. Everything else the same: 0.20 mm layers, matte PLA (Bambu PLA Matte), one plate.

Only real footage and Scott's own photo, each shot labelled:
  1. the P1S timelapse of the four tiles (30 frames, slowed)
  2. each tile, cropped from Scott's photo, with its settings: A, B, D, then C
  3. C, the winner, and why it matters: it's Bambu's own stock values
  4. the rule Scott set: iron every flat face a customer sees
  5. Scott's clip of the tiles popping off the plate

    python3 make_reel.py OUT.mp4      # the body; assemble.py adds the stamp and end card
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "series_motion"))
from directions import SS, W, H, FPS, prog, ease_out, font, mix, chip, printed_block  # noqa: E402
from kit import SERIES, background  # noqa: E402

REAL = HERE / "real"
PHOTO = REAL / "ironing_tiles_on_plate_2026-11-21.jpg"
TIMELAPSE = REAL / "ironing_tiles_timelapse_2026-11-21.mp4"
POPOFF = REAL / "ironing_tiles_pop_off_2026-11-21.mov"

# the tiles in Scott's photo (after its EXIF turn), each cropped square round the tile.
# Benson's map, looking down: back-left C, back-right A, front-left D, front-right B; the photo's
# top is the back of the plate, and the engraved letters agree.
TILES = {
    "A": ((815, 535, 1375, 1025), "NO IRONING", "the baseline"),
    "B": ((830, 1030, 1470, 1660), "0.10 MM SPACING", "10% flow · 15 mm/s"),
    "D": ((185, 1020, 825, 1660), "0.20 MM SPACING", "15% flow · 20 mm/s"),
    "C": ((255, 525, 815, 1025), "0.15 MM SPACING", "10% flow · 30 mm/s"),
}
PHOTO_LABEL = "Scott's photo of the printed tiles"
REAL_LABEL = "Real timelapse from our P1S chamber camera"
CLIP_LABEL = "Real clip: the tiles coming off the plate"


def frames(src, td, tag, extra=()):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(src), *extra, f"{td}/{tag}%04d.png"], check=True)
    return sorted(Path(td).glob(f"{tag}*.png"))


def framed(im, pic, x, y, w, h, col, tag, label, sp, label_y=None):
    im.paste(pic.resize((w * SS, h * SS), Image.LANCZOS), (x * SS, y * SS))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(((x - 6) * SS, (y - 6) * SS, (x + w + 6) * SS, (y + h + 6) * SS), 10 * SS,
                        outline=col, width=int(6 * SS))
    if tag:
        chip(im, x + 100, y + 44, tag, col, sp["bg"], fill=True, scale=0.8)
    d.text(((x + w / 2) * SS, (label_y or y + h + 40) * SS), label, font=font("semi", 28),
           fill=mix(sp["bg"], sp["text"], 0.9), anchor="mm")


def crop_16_9(im):
    h = round(im.width * 9 / 16)
    return im.crop((0, (im.height - h) // 2, im.width, (im.height - h) // 2 + h))


def main(out):
    sp = SERIES["blueprint"]
    gold, white = sp["acc"], sp["title_col"]
    photo = ImageOps.exif_transpose(Image.open(PHOTO)).convert("RGB")
    tiles = {k: photo.crop(b) for k, (b, _, _) in TILES.items()}
    with tempfile.TemporaryDirectory() as td:
        tl = frames(TIMELAPSE, td, "t")
        pop = frames(POPOFF, td, "p", ["-vf", "fps=30"])
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                               "-crf", "17", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)

        def put(im):
            ff.stdin.write(im.resize((W, H), Image.LANCZOS).tobytes())

        def heading(im, s, t, t0, y=700, px=120, col=None):
            printed_block(im, s, font("anton", px), col or white, sp["bg"], 540, y, t0, t0 + 0.45, t, 11,
                          nozzle_col=mix(sp["bg"], sp["text"], 0.55))

        t = 0.0
        # 1. the timelapse, 3 s: four tiles, one plate (the heading waits for the 1.5 s stamp)
        n = int(3.0 * FPS)
        for i in range(n):
            im = background(sp)
            fr = Image.open(tl[min(int(i / n * len(tl)), len(tl) - 1)]).convert("RGB")
            framed(im, fr, 40, 880, 1000, 562, white, "REAL", REAL_LABEL, sp)
            heading(im, "4 TOPS. 1 WINNER.", t + i / FPS, 1.55)
            put(im)
        t += 3.0
        # 2. each tile, 2 s: A, B, D, then C
        for k in ("A", "B", "D", "C"):
            _, big, small = TILES[k]
            n = int(2.0 * FPS)
            for i in range(n):
                tt = t + i / FPS
                im = background(sp)
                heading(im, f"TILE {k}", tt, t, y=300, px=130, col=gold)
                z = 1 + 0.06 * (i / n)
                pic = tiles[k]
                cw, ch = pic.width / z, pic.height / z
                pic = pic.crop((int((pic.width - cw) / 2), int((pic.height - ch) / 2),
                                int((pic.width + cw) / 2), int((pic.height + ch) / 2)))
                framed(im, pic, 160, 430, 760, int(760 * pic.height / pic.width), white, "PHOTO", PHOTO_LABEL, sp)
                d = ImageDraw.Draw(im)
                a = ease_out(prog(tt, t + 0.3, t + 0.6))
                d.text((540 * SS, 1430 * SS), big, font=font("anton", 92), fill=mix(sp["bg"], white, a), anchor="mm")
                d.text((540 * SS, 1530 * SS), small, font=font("semi", 52), fill=mix(sp["bg"], gold, a), anchor="mm")
                put(im)
            t += 2.0
        # 3. the winner, 3.5 s
        n = int(3.5 * FPS)
        for i in range(n):
            tt = t + i / FPS
            im = background(sp)
            heading(im, "C WINS", tt, t, y=290, px=150, col=gold)
            framed(im, tiles["C"], 230, 420, 620, int(620 * tiles["C"].height / tiles["C"].width), gold,
                   "PHOTO", PHOTO_LABEL, sp)
            d = ImageDraw.Draw(im)
            for j, (s, f, c, y) in enumerate([
                    ("THE SMOOTHEST TOP", font("anton", 80), white, 1240),
                    ("It's Bambu Studio's own stock ironing:", font("semi", 44), white, 1340),
                    ("0.15 mm spacing · 10% flow · 30 mm/s", font("semi", 48), gold, 1410)]):
                a = ease_out(prog(tt, t + 0.4 + 0.25 * j, t + 0.7 + 0.25 * j))
                d.text((540 * SS, y * SS), s, font=f, fill=mix(sp["bg"], c, a), anchor="mm")
            put(im)
        t += 3.5
        # 4. the rule, 2.5 s
        n = int(2.5 * FPS)
        for i in range(n):
            tt = t + i / FPS
            im = background(sp)
            heading(im, "OUR RULE", tt, t, y=640, px=110, col=gold)
            d = ImageDraw.Draw(im)
            for j, s in enumerate(["IRON EVERY", "FLAT FACE A", "CUSTOMER SEES."]):
                a = ease_out(prog(tt, t + 0.4 + 0.15 * j, t + 0.7 + 0.15 * j))
                d.text((540 * SS, (820 + 120 * j) * SS), s, font=font("anton", 110), fill=mix(sp["bg"], white, a),
                       anchor="mm")
            a = ease_out(prog(tt, t + 1.0, t + 1.3))
            d.text((540 * SS, 1260 * SS), "All four tiles: 0.2 mm layers, matte PLA, one plate on our P1S.",
                   font=font("semi", 32), fill=mix(sp["bg"], sp["text"], 0.85 * a), anchor="mm")
            put(im)
        t += 2.5
        # 5. Scott's clip of the tiles coming off, about 3.5 s
        n = int(3.5 * FPS)
        for i in range(n):
            tt = t + i / FPS
            im = background(sp)
            heading(im, "OFF THE PLATE", tt, t, y=700, px=110)
            fr = crop_16_9(Image.open(pop[min(int(i / n * len(pop)), len(pop) - 1)]).convert("RGB"))
            framed(im, fr, 40, 880, 1000, 562, white, "REAL", CLIP_LABEL, sp)
            put(im)
        t += 3.5
        ff.stdin.close()
        ff.wait()
    print(out, f"{t:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1])
