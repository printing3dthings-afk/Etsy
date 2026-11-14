#!/usr/bin/env python3
"""Trophy Rack medallion: the banner's outline and its lettering laid along the banner's
curve (2026-11-14). OpenSCAD can't measure text, so the letters' advances come from the
font file (PIL) and each letter is placed and turned on the curve here, then written to
banner_data.scad for trophy_rack.scad to include.

Scale: Playfair Display at OpenSCAD size 10 advances an "H" 10.85 mm, 800 font units of
1000, measured by rendering "HH" (so 1 em = 13.56 mm at size 10).

    python3 make_banner.py
"""
import math
from pathlib import Path

from PIL import ImageFont

HERE = Path(__file__).resolve().parent
FONT = HERE.parents[1] / "fonts" / "PlayfairDisplay-Bold.ttf"
TEXT = "TROPHY RACK"
SIZE = 7.0                      # OpenSCAD size: caps ~6.9 mm tall (rule 10 wants 3+)
XSCALE = 0.82                   # letters narrowed: the photo's face is more condensed than Playfair
EM = 13.56 * SIZE / 10          # mm per em
TRACK = 0.25                    # extra space between letters, mm
HALF = 6.2                      # the banner's half-height
X0, X1 = -43.0, 43.0            # the banner's tips
TAIL = 3.2                      # depth of the swallowtail notch


def centre(x):
    """The banner's centreline: rising to the right, bowed a little, as on the photo."""
    return -14.0 + 0.10 * x + 0.0012 * x * x


def slope(x):
    return 0.10 + 0.0024 * x


def normal(x):
    a = math.atan(slope(x))
    return -math.sin(a), math.cos(a)


def outline():
    xs = [X0 + (X1 - X0) * i / 60 for i in range(61)]
    top, bot = [], []
    for x in xs:
        nx, ny = normal(x)
        y = centre(x)
        top.append((x + nx * HALF, y + ny * HALF))
        bot.append((x - nx * HALF, y - ny * HALF))
    # swallowtail notches at both tips
    rx, ry = X1 - TAIL, centre(X1 - TAIL)
    lx, ly = X0 + TAIL, centre(X0 + TAIL)
    return top + [(rx, ry)] + bot[::-1] + [(lx, ly)]


def letters():
    f = ImageFont.truetype(str(FONT), 1000)
    adv = [f.getlength(ch) / 1000 * EM * XSCALE + TRACK for ch in TEXT]
    total = sum(adv) - TRACK
    # walk the curve by arc length so the spacing stays even where it bends
    def arc_x(x_from, dist):
        x, d = x_from, 0.0
        while d < dist:
            step = 0.02
            d += step * math.sqrt(1 + slope(x) ** 2)
            x += step
        return x
    # centre the word on the banner by arc length
    xs, x = [], None
    lo, hi = -40.0, 0.0
    for _ in range(40):
        mid = (lo + hi) / 2
        end = arc_x(mid, total)
        if end > -mid:
            hi = mid
        else:
            lo = mid
    x = (lo + hi) / 2
    out = []
    for ch, a in zip(TEXT, adv):
        xc = arc_x(x, (a - TRACK) / 2)          # the letter's centre
        if ch != " ":
            nx, ny = normal(xc)
            base = -0.49 * SIZE                  # caps are 0.98 x SIZE tall (measured): centred on the line
            out.append((ch, xc + nx * base, centre(xc) + ny * base, math.degrees(math.atan(slope(xc)))))
        x = arc_x(x, a)
    return out


def main():
    pts = outline()
    lines = ["// written by make_banner.py: do not edit", f'FONT = "Playfair Display";', f"SIZE = {SIZE};", f"XSCALE = {XSCALE};",
             "BANNER = [" + ", ".join(f"[{x:.3f}, {y:.3f}]" for x, y in pts) + "];",
             "LETTERS = [" + ", ".join(f'["{c}", {x:.3f}, {y:.3f}, {a:.2f}]' for c, x, y, a in letters()) + "];"]
    (HERE / "banner_data.scad").write_text("\n".join(lines) + "\n")
    print(f"{len(pts)} outline points, {len(letters())} letters")


if __name__ == "__main__":
    main()
