"""Digital then real: a Product post that cuts between a print's toolpath simulation and the
real P1S timelapse, matched by stage of the build, then shows both finished (2026-11-21).

Scott liked the OBC sign cut ("I like it") and said he'll upload the timelapses: every printed
product can get one. The OBC sign's own script (openscad_models/brand/obc_desk_sign/social/
make_compare_clip.py) is the first; this is the same thing for any product.

  1. The simulation: render it from the product's viewer job, e.g.
       python3 tools/viewer/make_listing_video.py <job> sim.mp4 --format square
  2. The real one: Scott's Bambu Handy timelapse, as uploaded.
  3. python3 digital_vs_real.py --sim sim.mp4 --real real.mp4 --title "HEX LANTERN" \
         --sim-split 6.2 --real-split 0.6 -o out.mp4
     --sim-split: the second (in the sim) where stage 2 starts; --real-split: the same moment as a
     fraction of the real clip. For a colour change, pick the frame where the new colour first
     shows in each; for one colour, leave both out and the cut is at half way.

Every shot keeps its label (simulation, or real timelapse). Both sources are retimed, scaled and
cropped to 16:9, never altered. The series stamp and end card are added by assemble.py's pieces.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from directions import SS, W, H, FPS, prog, ease_out, font, mix, chip, printed_block
from kit import SERIES, background, endcard, encode
import intros

SIM_LABEL = "Toolpath simulation of the sliced file, not print footage"
REAL_LABEL = "Real timelapse from our P1S chamber camera"


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "default=nw=1", str(path)],
                         capture_output=True, text=True, check=True).stdout
    kv = dict(line.split("=") for line in out.split())
    return int(kv["width"]), int(kv["height"]), float(kv["duration"])


def frames(src, td, tag, crop=None, upto=None):
    """Every frame of src as PNG, centre-cropped to 16:9 (or to an explicit w:h:x:y crop)."""
    w, h, _ = probe(src)
    if crop is None:
        cw, ch = (w, round(w * 9 / 16)) if w * 9 / 16 <= h else (round(h * 16 / 9), h)
        crop = f"{cw}:{ch}:{(w - cw) // 2}:{(h - ch) // 2}"
    args = ["ffmpeg", "-loglevel", "error", "-i", str(src)]
    if upto:
        args += ["-t", str(upto)]
    subprocess.run(args + ["-vf", f"crop={crop}", f"{td}/{tag}%04d.png"], check=True)
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


def body(a, sp, out):
    with tempfile.TemporaryDirectory() as td:
        sim_dur = a.sim_end or probe(a.sim)[2]
        sim = frames(a.sim, td, "s", a.sim_crop, upto=sim_dur)
        real = frames(a.real, td, "r", a.real_crop)
        sfps = len(sim) / sim_dur
        ss = a.sim_split if a.sim_split is not None else sim_dur / 2
        rs = int(round((a.real_split if a.real_split is not None else 0.5) * (len(real) - 1)))
        segs = [("sim", 0.0, ss, 3.0, "ON SCREEN FIRST"), ("real", 0, rs, 2.0, "THEN FOR REAL"),
                ("sim", ss, sim_dur, 2.0, "ON SCREEN"), ("real", rs, len(real) - 1, 1.6, "FOR REAL")]
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                               "-crf", "17", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
        t0 = 0.0
        for kind, s0, s1, dur, heading in segs:
            n = int(round(dur * FPS))
            for i in range(n):
                u = i / max(n - 1, 1)
                t = t0 + i / FPS
                if kind == "sim":
                    fr = Image.open(sim[min(int((s0 + (s1 - s0) * u) * sfps), len(sim) - 1)]).convert("RGB")
                else:
                    fr = Image.open(real[min(int(round(s0 + (s1 - s0) * u)), len(real) - 1)]).convert("RGB")
                im = background(sp)
                box(im, fr, 40, 880, 1000, SIM_LABEL if kind == "sim" else REAL_LABEL, kind, sp)
                start = max(t0, 1.55)          # the first heading waits for the 1.5 s stamp
                printed_block(im, heading, font("anton", 120), sp["acc"] if kind == "sim" else sp["title_col"],
                              sp["bg"], 540, 700, start, start + 0.45, t, 11,
                              nozzle_col=mix(sp["bg"], sp["text"], 0.55))
                ff.stdin.write(im.resize((W, H), Image.LANCZOS).tobytes())
            t0 += dur
        sim_last = Image.open(sim[-1]).convert("RGB")
        real_last = Image.open(real[-1]).convert("RGB")
        n = int(3.5 * FPS)
        for i in range(n):
            t = t0 + i / FPS
            z = 1 + 0.25 * ease_in_out(i / n)
            cw, ch = real_last.width / z, real_last.height / z
            cx, cy = real_last.width * a.zoom_x, real_last.height * a.zoom_y
            rz = real_last.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2)))
            im = background(sp)
            printed_block(im, "THE PLAN. THE PRINT.", font("anton", 100), sp["title_col"], sp["bg"], 540, 250,
                          t0, t0 + 0.5, t, 10, nozzle_col=mix(sp["bg"], sp["text"], 0.55))
            al = ease_out(prog(t, t0, t0 + 0.3))
            box(im, sim_last, 90, 360, 900, SIM_LABEL, "sim", sp, al)
            box(im, rz, 90, 930, 900, REAL_LABEL, "real", sp, al)
            ff.stdin.write(im.resize((W, H), Image.LANCZOS).tobytes())
        ff.stdin.close()
        ff.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", required=True)
    ap.add_argument("--real", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--kicker", default="DIGITAL FIRST, THEN REAL")
    ap.add_argument("--chip", default="PRINTED ON OUR P1S")
    ap.add_argument("--cta", default="FOLLOW ONBRANDCRAFTZ")
    ap.add_argument("--sim-split", type=float, help="seconds into the sim where stage 2 starts")
    ap.add_argument("--real-split", type=float, help="the same moment as a fraction of the real clip")
    ap.add_argument("--sim-end", type=float, help="use the sim only up to here (s), e.g. before an end card")
    ap.add_argument("--sim-crop", help="ffmpeg crop w:h:x:y for the sim (default: centre 16:9)")
    ap.add_argument("--real-crop", help="the same for the real clip")
    ap.add_argument("--zoom-x", type=float, default=0.5, help="where the final push-in centres, 0-1")
    ap.add_argument("--zoom-y", type=float, default=0.6)
    a = ap.parse_args()
    sp = dict(SERIES["product"], title=a.title, kicker=a.kicker, chip=a.chip, cta=a.cta)
    label = "Toolpath simulation first, then the real P1S timelapse"

    def draw(im, sp_, u, cy, k):
        intros.titled(im, sp_, u, cy, k)
        ImageDraw.Draw(im).text((540 * SS, (cy + 300) * SS), label, font=font("semi", 24),
                                fill=mix(sp_["bg"], sp_["text"], 0.85), anchor="mm")

    with tempfile.TemporaryDirectory() as td:
        b, sting, end = Path(td) / "body.mp4", Path(td) / "sting.mov", Path(td) / "end.mp4"
        body(a, sp, b)
        encode(lambda t: intros.frame("product", "sting", t, sp=sp, draw=draw), int(1.5 * FPS), sting, True)
        encode(lambda t: endcard(sp, t), int(4.0 * FPS), end, False)
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(b), "-i", str(sting), "-i", str(end),
            "-filter_complex", "[0:v][1:v]overlay=0:0:eof_action=pass:format=auto[mo];"
            "[mo][2:v]concat=n=2:v=1:a=0,format=yuv420p[v]",
            "-map", "[v]", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-movflags", "+faststart",
            "-an", a.out], check=True)
    print(a.out)


if __name__ == "__main__":
    main()
