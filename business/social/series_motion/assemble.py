"""Put a finished video into a series' Printed look (2026-11-20): the series' 1.5 s stamp over
the first shot, then the series' end card. Scott: "You are now making all animated and
regular videos" (STANDARDS 21), and the house style is the Printed kit he picked that day.

    python3 assemble.py MAIN.mp4 OUT.mp4 --series product --title "GINGERBREAD VILLAGE" \
        --kicker "AT NIGHT" --chip "DESIGNED BY US" --cta "LINK IN BIO" [--intro titled]

The stamp is the series' signature intro unless --intro titled, the title-only one. The main
video must be 1080 x 1920; it's re-timed to 30 fps if it isn't.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import ImageDraw

from directions import FPS, W, H, SS, font
from kit import SERIES, endcard, encode
import intros


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("main")
    ap.add_argument("out")
    ap.add_argument("--series", required=True, choices=list(SERIES))
    ap.add_argument("--title")
    ap.add_argument("--kicker")
    ap.add_argument("--chip")
    ap.add_argument("--cta")
    ap.add_argument("--intro", choices=["signature", "titled"], default="signature")
    ap.add_argument("--label", help="the video's own honesty label, e.g. '3D animation of the design "
                    "files'. The stamp covers the top of the frame, so the label is repeated inside it.")
    a = ap.parse_args()
    sp = dict(SERIES[a.series], **intros.INTRO_TEXT.get(a.series, {}))
    sp.update({k: v for k, v in dict(title=a.title, kicker=a.kicker, chip=a.chip, cta=a.cta).items() if v})
    base = intros.titled if a.intro == "titled" else intros.INTROS[a.series]

    def draw(im, sp_, u, cy, k):
        base(im, sp_, u, cy, k)
        if a.label:
            # every frame of a render or simulation says what it is (STANDARDS 9, CLAUDE.md top
            # rule); the stamp would otherwise hide the video's own label for 1.5 s
            ImageDraw.Draw(im).text((540 * SS, (cy + 300) * SS), a.label, font=font("semi", 24),
                                    fill=intros.mix(sp_["bg"], sp_["text"], 0.85), anchor="mm")
    with tempfile.TemporaryDirectory() as td:
        sting, end = Path(td) / "sting.mov", Path(td) / "end.mp4"
        encode(lambda t: intros.frame(a.series, "sting", t, sp=sp, draw=draw), int(1.5 * FPS), sting, True)
        encode(lambda t: endcard(sp, t), int(4.0 * FPS), end, False)
        # main at 30 fps with the stamp over its first 1.5 s, then the end card; silent
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", a.main, "-i", str(sting), "-i", str(end),
            "-filter_complex",
            f"[0:v]fps={FPS},scale={W}:{H},setsar=1[m];[m][1:v]overlay=0:0:eof_action=pass:format=auto[mo];"
            f"[2:v]fps={FPS},setsar=1[e];[mo][e]concat=n=2:v=1:a=0,format=yuv420p[v]",
            "-map", "[v]", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-movflags", "+faststart",
            "-an", a.out], check=True)
    print(a.out)


if __name__ == "__main__":
    main()
