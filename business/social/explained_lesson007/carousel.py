"""Lesson 007 carousel: five 1080 x 1350 slides cut from the video's own stills
(out/lesson007_<t>s.png, written by animate.py --stills), so the slides and the
video can never disagree. The caption band is left out; the post caption carries it.

    python3 carousel.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
CREAM, INK, ORANGE = (246, 240, 226), (32, 36, 46), (232, 106, 44)
FONTS = HERE.parent / "explained_lesson006" / "fonts"
STILLS = ["5.8", "16.6", "29.4", "40.4", "49.5"]


def main():
    semi = ImageFont.truetype(str(FONTS / "ChakraPetch-SemiBold.ttf"), 30)
    small = ImageFont.truetype(str(FONTS / "ChakraPetch-SemiBold.ttf"), 24)
    out = HERE / "out" / "carousel"
    out.mkdir(parents=True, exist_ok=True)
    k = 0.93
    for i, t in enumerate(STILLS, 1):
        fr = Image.open(HERE / "out" / f"lesson007_{t}s.png")
        crop = fr.crop((0, 170, 1080, 1460))         # title down to the credit line
        crop = crop.resize((int(1080 * k), int(1290 * k)), Image.LANCZOS)
        s = Image.new("RGB", (1080, 1350), CREAM)
        s.paste(crop, ((1080 - crop.width) // 2, 75))
        d = ImageDraw.Draw(s)
        d.text((60, 42), "3D PRINTING, EXPLAINED", font=semi, fill=INK, anchor="lm")
        d.text((1020, 42), f"LESSON 007  ·  {i}/{len(STILLS)}", font=semi, fill=ORANGE, anchor="rm")
        d.text((540, 1316), "ONBRANDCRAFTZ", font=small, fill=INK, anchor="mm")
        s.save(out / f"slide{i}.png")
    print(out)


if __name__ == "__main__":
    main()
