#!/usr/bin/env python3
"""The OBC desk sign's TikTok (2026-11-11), Claude's entry for
business/image_choices/2026-11-11_tiktok_obc_sign on main.

Scott asked for a TikTok of the logo sign; Muse makes its own from the same
brief and Scott picks. This is the toolpath clip plus an end card:

1. The plaque's real slice (the print-fidelity slice, wipe tower removed, as a
   single-spool print with a pause has none), played back by the print viewer's
   own export at 1080 x 1920:
       python3 tools/viewer/make_listing_video.py obc_desk_sign <out> --format reel
           --size 1080 --seconds 12 --hold 2 --detail high --facing -157.5
   The turn ends square on to the letters.
2. Text, in the top band, clear of TikTok's own buttons and caption:
   the hook, and on every frame "Toolpath simulation of the sliced file, not
   print footage".
3. An end card: the 3D render of the finished sign standing in its base, labelled
   as a render.

No claim beyond what the files show: nothing says it has been printed.

    python3 make_tiktok.py <toolpath.mp4>     (writes obc_sign_tiktok_claude.mp4 here)
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FONTS = ROOT / "assets" / "fonts"
W, H = 1080, 1920
GOLD, WHITE, SOFT = (212, 166, 58), (245, 242, 235), (200, 204, 214)
HOOK = ["Turning my logo", "into a 3D print"]  # one line ran off both edges at 66 px
LABEL = "Toolpath simulation of the sliced file, not print footage"
END_TITLE = "OBC desk sign"
END_LINES = ["Gold on black, plaque 182 mm wide", "The plaque slides into its base"]
END_NOTE = "3D render of the design, not a photo"
END_SECONDS = 3


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def centred(d, y, text, f, fill, shadow=True):
    w = d.textlength(text, font=f)
    x = (W - w) / 2
    if shadow:
        d.text((x + 3, y + 3), text, font=f, fill=(0, 0, 0, 170))
    d.text((x, y), text, font=f, fill=fill)


def overlay():
    """The text for every toolpath frame, as a transparent PNG."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # a soft dark band behind the text, so it reads on the plate and the chamber
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(band).rectangle([0, 220, W, 560], fill=(8, 10, 18, 150))
    im = Image.alpha_composite(im, band.filter(ImageFilter.GaussianBlur(28)))
    d = ImageDraw.Draw(im)
    for i, line in enumerate(HOOK):
        centred(d, 260 + i * 92, line, font("Montserrat-ExtraBold.ttf", 80), GOLD + (255,))
    centred(d, 470, LABEL, font("Poppins-Regular.ttf", 32), WHITE + (255,))
    return im


def end_card():
    """The finished sign: the review render of the real parts, on the clip's dark ground."""
    bg = Image.new("RGB", (W, H), (14, 17, 27))
    g = ImageDraw.Draw(bg)
    for y in range(H):  # a gentle lift toward the middle
        t = 1 - abs(y - H * 0.5) / (H * 0.5)
        g.line([(0, y), (W, y)], fill=(int(14 + 16 * t), int(17 + 18 * t), int(27 + 22 * t)))
    render = Image.open(HERE.parent / "images" / "obc_desk_sign_three_quarter.png").convert("RGB")
    s = 960
    render = render.resize((s, s), Image.LANCZOS)
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=36, fill=255)
    bg.paste(render, ((W - s) // 2, 560), mask)
    d = ImageDraw.Draw(bg)
    centred(d, 300, END_TITLE, font("Montserrat-ExtraBold.ttf", 92), GOLD, shadow=False)
    for i, line in enumerate(END_LINES):
        centred(d, 420 + i * 58, line, font("Poppins-SemiBold.ttf", 42), WHITE, shadow=False)
    centred(d, 1550, END_NOTE, font("Poppins-Regular.ttf", 32), SOFT, shadow=False)
    return bg


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    clip = Path(sys.argv[1])
    out = HERE / "obc_sign_tiktok_claude.mp4"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        overlay().save(td / "overlay.png")
        end_card().save(td / "end.png")
        enc = ["-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "18", "-r", "30"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-i", str(td / "overlay.png"),
                        "-filter_complex", "[0:v][1:v]overlay=0:0,format=yuv420p", *enc, "-an",
                        str(td / "a.mp4")], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(END_SECONDS), "-i",
                        str(td / "end.png"), "-vf", "fade=t=in:st=0:d=0.4,format=yuv420p", *enc, "-an",
                        str(td / "b.mp4")], check=True)
        (td / "list.txt").write_text(f"file '{td / 'a.mp4'}'\nfile '{td / 'b.mp4'}'\n")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(td / "list.txt"),
                        *enc, "-movflags", "+faststart", "-an", str(out)], check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
