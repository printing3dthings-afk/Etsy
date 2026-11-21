"""OBC desk sign, digital then real (2026-11-21). Scott: "I want the simulated video included with
this one. Maybe a bounce back and forth to show how we pre print digital then the real print for
quality."

Cuts between the toolpath simulation of the sliced file (`obc_sign_tiktok_claude.mp4`, its build
section with the text cropped off) and Scott's real P1S chamber timelapse
(`real/obc_sign_p1s_timelapse_2026-11-21.mp4`), matched by stage of the build:

  A  on screen, the black plaque      sim 0 -> 7.5 s     in 3.0 s
  B  for real,  the black plaque      real frames 0 -> 24 in 2.0 s
  C  on screen, the gold letters      sim 7.5 -> 10.5 s  in 2.0 s
  D  for real,  the gold letters      real frames 24 -> 36 in 1.6 s
  E  both finished, stacked           3.5 s

Every shot carries its own label: simulation or real timelapse. Nothing in either source is
altered; they're retimed, scaled and cropped. assemble.py adds the stamp and the end card.

    python3 make_compare_clip.py OUT.mp4
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "business" / "social" / "series_motion"))
from directions import SS, W, H, FPS, prog, ease_out, font, mix, chip, printed_block  # noqa: E402
from kit import SERIES, background  # noqa: E402

SIM = HERE / "obc_sign_tiktok_claude.mp4"
REAL = HERE.parent / "real" / "obc_sign_p1s_timelapse_2026-11-21.mp4"
SIM_CROP_Y = 520            # the sim is 1080 x 1920 with its own text above y 500; take 16:9 below it
SIM_LABEL = "Toolpath simulation of the sliced file, not print footage"
REAL_LABEL = "Real timelapse from our P1S chamber camera"

# (kind, source start, source end, seconds on screen, heading)
SEGMENTS = [("sim", 0.0, 7.5, 3.0, "ON SCREEN FIRST"),
            ("real", 0, 24, 2.0, "THEN FOR REAL"),
            ("sim", 7.5, 10.5, 2.0, "ON SCREEN"),
            ("real", 24, 36, 1.6, "FOR REAL")]
FINAL = 3.5


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def frames(src, td, tag, extra=()):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(src), *extra, f"{td}/{tag}%04d.png"], check=True)
    return sorted(Path(td).glob(f"{tag}*.png"))


def box(im, fr, x, y, w, label_txt, kind, sp, label_alpha=1.0):
    h = round(w * 9 / 16)
    im.paste(fr.resize((w * SS, h * SS), Image.LANCZOS), (x * SS, y * SS))
    d = ImageDraw.Draw(im)
    col = sp["acc"] if kind == "sim" else sp["title_col"]
    d.rounded_rectangle(((x - 6) * SS, (y - 6) * SS, (x + w + 6) * SS, (y + h + 6) * SS), 10 * SS,
                        outline=col, width=int(6 * SS))
    chip(im, x + 110, y + 44, "DIGITAL" if kind == "sim" else "REAL", col, sp["bg"], fill=True, scale=0.8)
    d.text(((x + w / 2) * SS, (y + h + 40) * SS), label_txt, font=font("semi", 28),
           fill=mix(sp["bg"], sp["text"], 0.9 * label_alpha), anchor="mm")
    return h


def main(out):
    sp = SERIES["product"]
    with tempfile.TemporaryDirectory() as td:
        sim = frames(SIM, td, "s", ["-t", "12", "-vf", f"crop=1080:608:0:{SIM_CROP_Y}"])
        real = frames(REAL, td, "r")
        sim_fps = 30.0
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                               "-crf", "17", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
        t0 = 0.0
        for kind, a, b, dur, heading in SEGMENTS:
            n = int(round(dur * FPS))
            for i in range(n):
                u = i / max(n - 1, 1)
                t = t0 + i / FPS
                if kind == "sim":
                    fr = Image.open(sim[min(int((a + (b - a) * u) * sim_fps), len(sim) - 1)]).convert("RGB")
                else:
                    fr = Image.open(real[min(int(round(a + (b - a) * u)), len(real) - 1)]).convert("RGB")
                im = background(sp)
                box(im, fr, 40, 880, 1000, SIM_LABEL if kind == "sim" else REAL_LABEL, kind, sp)
                # the heading prints on at each cut (the first only once the 1.5 s stamp has gone)
                start = max(t0, 1.55)
                printed_block(im, heading, font("anton", 120), sp["acc"] if kind == "sim" else sp["title_col"],
                              sp["bg"], 540, 700, start, start + 0.45, t, 11,
                              nozzle_col=mix(sp["bg"], sp["text"], 0.55))
                ff.stdin.write(im.resize((W, H), Image.LANCZOS).tobytes())
            t0 += dur
        # both finished: the plan above, the print below, then a slow push-in on the real letters
        sim_last = Image.open(sim[min(int(11.9 * sim_fps), len(sim) - 1)]).convert("RGB")
        real_last = Image.open(real[-1]).convert("RGB")
        n = int(FINAL * FPS)
        for i in range(n):
            t = t0 + i / FPS
            z = 1 + 0.25 * ease_in_out(i / n)
            cw, ch = real_last.width / z, real_last.height / z
            cx, cy = real_last.width * 0.47, real_last.height * 0.60
            rz = real_last.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2)))
            im = background(sp)
            printed_block(im, "THE PLAN. THE PRINT.", font("anton", 100), sp["title_col"], sp["bg"], 540, 250,
                          t0, t0 + 0.5, t, 10, nozzle_col=mix(sp["bg"], sp["text"], 0.55))
            a = ease_out(prog(t, t0, t0 + 0.3))
            box(im, sim_last, 90, 360, 900, SIM_LABEL, "sim", sp, a)
            box(im, rz, 90, 930, 900, REAL_LABEL, "real", sp, a)
            ff.stdin.write(im.resize((W, H), Image.LANCZOS).tobytes())
        ff.stdin.close()
        ff.wait()
    print(out, f"{t0 + FINAL:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1])
