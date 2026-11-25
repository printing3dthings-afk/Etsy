"""Panda on the Bench, Ep 002: the BIGTREETECH Panda plate on our P1S (2026-11-25).

OPEN row 35 (main): cut from Scott's six Nov 21 timelapses, all printed on the BIGTREETECH Panda
Build Plate, Dual-side Textured PEI Grid (Scott, 2026-11-21). Scott bought the plate himself.
Ep 001 (posted Nov 20) was the stock-plate baseline.

Only the four identified prints are used (openscad_models/real_timelapses/):
  phone stand, Gingerbread Tin canister plate, fit test plate, Urban Kid v2 head test.
Left out, as the thread says: the blue spaghetti failure (cause unknown: on a sponsor's plate it
would read as the plate's fault) and the unidentified purple disc.

What's on screen is only what the footage shows: four prints on the plate, each run to the end.
Nothing about release, finish or adhesion is claimed: that waits for Scott's own words (SCRIPT.md).

    python3 make_ep002.py OUT.mp4      # the body; assemble.py adds the stamp and end card
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "series_motion"))
from directions import SS, W, H, FPS, prog, ease_out, font, mix, chip, printed_block  # noqa: E402
from kit import SERIES, background  # noqa: E402

TL = ROOT / "openscad_models" / "real_timelapses"
PRINTS = [("phone_stand", "PHONE STAND"), ("gingerbread_tin_canister_plate", "GINGERBREAD TIN"),
          ("fit_test_plate", "FIT TEST PLATE"), ("urban_kid_v2_head_test", "FIGURE HEAD TEST")]
REAL_LABEL = "Real timelapse from our P1S chamber camera"
PLATE = ["BIGTREETECH PANDA BUILD PLATE", "Dual-side Textured PEI Grid"]


def frames(src, td, tag):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(src), f"{td}/{tag}%04d.png"], check=True)
    return sorted(Path(td).glob(f"{tag}*.png"))


def framed(im, pic, x, y, w, h, col, sp, label=REAL_LABEL, tag="REAL"):
    im.paste(pic.resize((w * SS, h * SS), Image.LANCZOS), (x * SS, y * SS))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(((x - 6) * SS, (y - 6) * SS, (x + w + 6) * SS, (y + h + 6) * SS), 10 * SS,
                        outline=col, width=int(6 * SS))
    if tag:
        chip(im, x + 100, y + 44, tag, col, sp["bg"], fill=True, scale=0.8)
    if label:
        d.text(((x + w / 2) * SS, (y + h + 40) * SS), label, font=font("semi", 28),
               fill=mix(sp["bg"], sp["text"], 0.9), anchor="mm")


def main(out):
    sp = SERIES["bench"]
    green, white = sp["acc"], sp["title_col"]
    with tempfile.TemporaryDirectory() as td:
        tl = {k: frames(TL / f"{k}_2026-11-21.mp4", td, k) for k, _ in PRINTS}
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                               "-crf", "17", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)

        def put(im):
            ff.stdin.write(im.resize((W, H), Image.LANCZOS).tobytes())

        def heading(im, s, t, t0, y=700, px=120, col=None):
            printed_block(im, s, font("anton", px), col or white, sp["bg"], 540, y, t0, t0 + 0.45, t, 11,
                          nozzle_col=mix(sp["bg"], sp["text"], 0.55))

        def text(im, s, y, f, col, a):
            ImageDraw.Draw(im).text((540 * SS, y * SS), s, font=f, fill=mix(sp["bg"], col, a), anchor="mm")

        t = 0.0
        # 1. 3 s: the phone stand printing, under the series stamp, then the hook
        n = int(3.0 * FPS)
        src = tl["phone_stand"]
        for i in range(n):
            tt = t + i / FPS
            im = background(sp)
            framed(im, Image.open(src[min(int(i / n * len(src)), len(src) - 1)]).convert("RGB"), 40, 880, 1000, 562,
                   white, sp)
            heading(im, "NEW PLATE.", tt, 1.55, y=640, px=130)
            put(im)
        t += 3.0
        # 2. 3 s: which plate, and how we got it
        n = int(3.0 * FPS)
        for i in range(n):
            tt = t + i / FPS
            im = background(sp)
            heading(im, "EP 002", tt, t, y=420, px=120, col=green)
            for j, (s, f, c, y) in enumerate([
                    ("Ep 001 was the stock plate.", font("semi", 46), white, 620),
                    ("This one:", font("semi", 46), white, 700),
                    (PLATE[0], font("anton", 62), white, 820),
                    (PLATE[1], font("semi", 50), green, 900),
                    ("We bought it ourselves.", font("semi", 40), white, 1060)]):
                text(im, s, y, f, c, ease_out(prog(tt, t + 0.3 + 0.25 * j, t + 0.6 + 0.25 * j)))
            put(im)
        t += 3.0
        # 3. each print, 2.6 s, its timelapse run start to finish
        for k, (key, name) in enumerate(PRINTS):
            n = int(2.6 * FPS)
            src = tl[key]
            for i in range(n):
                tt = t + i / FPS
                im = background(sp)
                heading(im, name, tt, t, y=560, px=110)
                text(im, f"PRINT {k + 1} OF 4", 420, font("bold", 44), green, ease_out(prog(tt, t, t + 0.3)))
                fr = Image.open(src[min(int(i / (n * 0.85) * len(src)), len(src) - 1)]).convert("RGB")
                framed(im, fr, 40, 760, 1000, 562, white, sp)
                put(im)
            t += 2.6
        # 4. 3.5 s: all four, finished
        n = int(3.5 * FPS)
        last = {k: Image.open(tl[k][-1]).convert("RGB") for k, _ in PRINTS}
        for i in range(n):
            tt = t + i / FPS
            im = background(sp)
            heading(im, "4 PRINTS. 4 FINISHED.", tt, t, y=420, px=104)
            for j, (key, name) in enumerate(PRINTS):
                a = ease_out(prog(tt, t + 0.2 + 0.15 * j, t + 0.5 + 0.15 * j))
                if a <= 0:
                    continue
                x, y = 40 + (j % 2) * 510, 620 + (j // 2) * 330
                pic = last[key].resize((490, 276), Image.LANCZOS)
                framed(im, pic, x, y, 490, 276, mix(sp["bg"], white, a), sp, label=None, tag=None)
            text(im, "Last frame of each real timelapse, on the Panda plate", 1300, font("semi", 30), white,
                 ease_out(prog(tt, t + 0.9, t + 1.2)) * 0.9)
            put(im)
        t += 3.5
        ff.stdin.close()
        ff.wait()
    print(out, f"{t:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1])
