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
SIZE = 6.0                      # OpenSCAD size: caps ~5.9 mm tall, as on the photo (rule 10 wants 3+)
XSCALE = 0.82                   # letters narrowed: the photo's face is more condensed than Playfair
EM = 13.56 * SIZE / 10          # mm per em
TRACK = 0.65                    # extra space between letters, mm
HALF = 5.0                      # the front band's half-height
BAND = (-30.5, 31.0)            # the front band's ends
# the tails, folded behind the band's ends: (inner x, outer x, offset at the inner end,
# how fast they climb outward), as on the photo where the left tail kicks up-left
TAILS = [(-27.0, -44.0, 0.6, 0.12), (27.5, 44.0, 0.3, 0.0)]
TAIL_HALF = 4.4
NOTCH = 3.0                     # depth of the swallowtail notch


def centre(x):
    """The banner's centreline: rising to the right, bowed a little, as on the photo."""
    return -12.0 + 0.12 * x + 0.0012 * x * x


def slope(x):
    return 0.12 + 0.0024 * x


def normal(x):
    a = math.atan(slope(x))
    return -math.sin(a), math.cos(a)


def strip(x0, x1, half, off=lambda x: 0.0, notch=0.0, n=40):
    """A band along the centreline from x0 to x1 (either order), shifted by off(x) along
    the normal; with notch, the x1 end is a swallowtail."""
    xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
    top, bot = [], []
    for x in xs:
        nx, ny = normal(x)
        y, o = centre(x), off(x)
        top.append((x + nx * (o + half), y + ny * (o + half)))
        bot.append((x + nx * (o - half), y + ny * (o - half)))
    pts = top
    if notch:
        xm = x1 - notch * (1 if x1 > x0 else -1)
        nx, ny = normal(xm)
        pts = pts + [(xm + nx * off(x1), centre(xm) + ny * off(x1))]
    pts = pts + bot[::-1]
    # keep it counter-clockwise for OpenSCAD's sake (either works, but be consistent)
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
    return pts if area > 0 else pts[::-1]


def outline():
    return strip(*BAND, HALF)


def tails():
    out = []
    for xi, xo, o0, k in TAILS:
        out.append(strip(xi, xo, TAIL_HALF, off=lambda x, xi=xi, o0=o0, k=k: o0 + k * abs(x - xi), notch=NOTCH))
    return out


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
    lo, hi = -30.0, 0.0
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
             "TAILS = [" + ", ".join("[" + ", ".join(f"[{x:.3f}, {y:.3f}]" for x, y in t) + "]" for t in tails()) + "];",
             "LETTERS = [" + ", ".join(f'["{c}", {x:.3f}, {y:.3f}, {a:.2f}]' for c, x, y, a in letters()) + "];"]
    (HERE / "banner_data.scad").write_text("\n".join(lines) + "\n")
    print(f"{len(pts)} outline points, {len(letters())} letters")


if __name__ == "__main__":
    main()
