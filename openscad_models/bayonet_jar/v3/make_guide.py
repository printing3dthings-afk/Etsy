#!/usr/bin/env python3
"""Bayonet Jar v3: the PDF guide (2026-11-10), from render_v3.py's renders of the real
exported parts (run that first), with the turn drawn on the top view.

    python3 make_guide.py      (Bayonet_Jar_v3_Guide.pdf)
"""
import math
import sys
from pathlib import Path

from PIL import ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from guide_cards import ACCENT, BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def clockwise(im):
    """The closing turn, drawn on the top view: an arc with its head pointing clockwise."""
    im = im.copy()
    d = ImageDraw.Draw(im)
    cx, cy = im.width / 2, im.height / 2
    r = min(im.width, im.height) * 0.46
    w = max(8, int(r / 22))
    # PIL angles run clockwise from 3 o'clock; draw from 10 o'clock round to 2 o'clock
    a0, a1 = 200, 320
    d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=ACCENT, width=w)
    t = math.radians(a1)
    tip = (cx + r * math.cos(t), cy + r * math.sin(t))
    tang = (-math.sin(t), math.cos(t))            # clockwise direction on screen
    norm = (math.cos(t), math.sin(t))
    L = w * 3.2
    d.polygon([(tip[0] + tang[0] * L, tip[1] + tang[1] * L),
               (tip[0] + norm[0] * L * 0.7, tip[1] + norm[1] * L * 0.7),
               (tip[0] - norm[0] * L * 0.7, tip[1] - norm[1] * L * 0.7)], fill=ACCENT)
    return im


def main():
    a = Card("Bayonet Jar: closing the lid", "Push down, twist clockwise. The same on every size.")
    a.step(1, "Line the lid up", [
        "!Set the lid on the jar and turn it gently until it drops, about 8 mm.",
        "Three bumps inside the lid fall into the three notches at the jar's rim.",
    ], crop(IMG / "bayonet_jar_v3_lined_up.png"), pic_h=520)
    a.step(2, "Twist it clockwise", [
        "!A short twist, about 25 degrees, the way you'd close any jar.",
        "It pulls down onto the rim and stops on its own.",
    ], clockwise(crop(IMG / "bayonet_jar_v3_top.png", 60)), pic_h=480)
    a.step(3, "Closed", ["To open: twist it back the other way and lift."],
           crop(IMG / "bayonet_jar_v3_closed.png"), pic_h=440)
    a.box("Good", ["Closes clockwise and stops on its own.", "No rattle when it's shut."], GOOD)
    a.box("Tell me", ["if it's stiff to turn, or rattles shut;", "which size it was."], BAD)
    save_pdf([a], HERE / "Bayonet_Jar_v3_Guide.pdf")


if __name__ == "__main__":
    main()
