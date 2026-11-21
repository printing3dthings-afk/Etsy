"""The OBC desk sign's real-print video (2026-11-21): Scott's own P1S chamber timelapse
(`real/obc_sign_p1s_timelapse_2026-11-21.mp4`, 1280 x 720, 37 frames, 1.5 s, from Bambu's cloud
timelapse), framed in the Product posts look so the series stamp and end card fit around it.

The timelapse is slowed to 8 fps (4.6 s), then holds on the last frame with a slow push-in on the
gold letters. It sits as a wide frame below the stamp's area, with "THE REAL PRINT" printed above it
once the stamp has gone. Nothing in the footage is altered; it's scaled and, at the end, cropped in.

    python3 make_real_clip.py OUT.mp4      # the body only; assemble.py adds the stamp and end card
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "business" / "social" / "series_motion"))
from directions import SS, W, H, FPS, prog, ease_out, font, mix  # noqa: E402
from directions import printed_block  # noqa: E402
from kit import SERIES, background  # noqa: E402


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2

SRC = HERE.parent / "real" / "obc_sign_p1s_timelapse_2026-11-21.mp4"
PLAY_FPS = 8            # 37 source frames -> 4.6 s
HOLD = 3.0
VW = 1000               # the footage's width on screen; 16:9
VX, VY = (W - VW) // 2, 880


def main(out):
    sp = SERIES["product"]
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(SRC), f"{td}/s%03d.png"], check=True)
        src = sorted(Path(td).glob("s*.png"))
        n_play = int(round(len(src) / PLAY_FPS * FPS))
        n = n_play + int(HOLD * FPS)
        vh = round(VW * 9 / 16)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                               "-crf", "17", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
        last = Image.open(src[-1]).convert("RGB")
        for i in range(n):
            t = i / FPS
            im = background(sp)
            if i < n_play:
                fr = Image.open(src[min(int(t * PLAY_FPS), len(src) - 1)]).convert("RGB")
            else:
                # hold the finished print and push in slowly on the letters (centre-right of frame)
                z = 1 + 0.35 * ease_in_out(prog(t, n_play / FPS, n / FPS))
                cw, ch = last.width / z, last.height / z
                cx, cy = last.width * 0.47, last.height * 0.60
                fr = last.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2)))
            fr = fr.resize((VW * SS, vh * SS), Image.LANCZOS)
            im.paste(fr, (VX * SS, VY * SS))
            d = ImageDraw.Draw(im)
            d.rounded_rectangle(((VX - 6) * SS, (VY - 6) * SS, (VX + VW + 6) * SS, (VY + vh + 6) * SS), 10 * SS,
                                outline=sp["acc"], width=int(6 * SS))
            # the heading prints on once the 1.5 s stamp above has gone
            printed_block(im, "THE REAL PRINT", font("anton", 120), sp["title_col"], sp["bg"], 540, 700,
                          1.55, 2.5, t, 11, nozzle_col=mix(sp["bg"], sp["text"], 0.55))
            a = 1.0     # the honesty label is on every frame (the stamp repeats it while it covers the top)
            d.text((540 * SS, (VY + vh + 50) * SS), "Real timelapse from our P1S chamber camera",
                   font=font("semi", 32), fill=mix(sp["bg"], sp["text"], 0.9 * a), anchor="mm")
            ff.stdin.write(im.resize((W, H), Image.LANCZOS).tobytes())
        ff.stdin.close()
        ff.wait()
    print(out, f"{n / FPS:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1])
