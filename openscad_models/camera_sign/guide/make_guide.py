#!/usr/bin/env python3
"""The gap gauge's visual guide (Scott, 2026-11-18: "Make a visual pdf of what I need to
do"): print the gauge, measure the two gaps behind the toolhead and the bed, send the
numbers. The gauge picture is the as-printed render of the real sliced part; the three
printer pictures are labelled diagrams, not to scale, since no measured model of the
P1S's chamber exists here.

    python3 make_guide.py      (Gap_Gauge_Guide.pdf)
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from guide_cards import BAD, GOOD, INK, MUTED, Card, crop, font, save_pdf  # noqa: E402

IMG = HERE.parent / "images"
ORANGE, GREY, DARK, WALL, PLATE = (242, 140, 40), (200, 200, 205), (80, 80, 88), (60, 60, 66), (150, 150, 158)
LAB, LABB = font("Poppins-SemiBold.ttf", 26), font("Nunito-ExtraBold.ttf", 30)
DW, DH = 960, 500


def gauge(d, x, top, bottom):
    """The gauge seen edge on, hanging thin end down into a gap: it widens upward."""
    n = 12
    for i in range(n):
        y0 = bottom - (i + 1) * (bottom - top) / n
        y1 = bottom - i * (bottom - top) / n
        w = 6 + i * 2
        d.rectangle((x - w / 2, y0, x + w / 2, y1), fill=ORANGE, outline=(180, 95, 20))


def arrow(d, a, b, colour=INK, width=5):
    d.line((a, b), fill=colour, width=width)
    import math
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-1, 1):
        d.line((b, (b[0] - 22 * math.cos(ang + s * 0.45), b[1] - 22 * math.sin(ang + s * 0.45))), fill=colour, width=width)


def gap_mark(d, x0, x1, y, text):
    d.line((x0, y, x1, y), fill=(176, 64, 64), width=4)
    for x in (x0, x1):
        d.line((x, y - 14, x, y + 14), fill=(176, 64, 64), width=4)
    d.text((x0 - 20, y), text, font=LABB, fill=(176, 64, 64), anchor="rm")


def wall(d):
    d.rectangle((830, 20, 870, DH - 20), fill=WALL)
    d.text((880, 40), "BACK", font=LAB, fill=INK)
    d.text((880, 72), "WALL", font=LAB, fill=INK)


def toolhead_diagram():
    im = Image.new("RGB", (DW, DH), "white")
    d = ImageDraw.Draw(im)
    wall(d)
    d.rectangle((40, 60, 830, 90), fill=DARK)                       # the rail
    d.text((60, 30), "the toolhead's rail", font=LAB, fill=MUTED)
    d.rounded_rectangle((560, 90, 790, 330), radius=18, fill=GREY, outline=DARK, width=4)
    d.polygon([(660, 330), (690, 330), (675, 360)], fill=DARK)      # nozzle
    d.text((675, 210), "TOOLHEAD", font=LABB, fill=INK, anchor="mm")
    d.text((60, 160), "moved all the way back", font=LAB, fill=MUTED)
    arrow(d, (380, 210), (545, 210))
    gauge(d, 810, 120, 330)
    gap_mark(d, 790, 830, 380, "GAP 1")
    d.text((40, DH - 50), "Side view. A diagram, not to scale.", font=LAB, fill=MUTED)
    return im


def bed_diagram():
    im = Image.new("RGB", (DW, DH), "white")
    d = ImageDraw.Draw(im)
    wall(d)
    d.rounded_rectangle((540, 60, 700, 170), radius=14, fill=GREY, outline=DARK, width=4)
    d.text((620, 115), "toolhead", font=LAB, fill=INK, anchor="mm")
    d.rectangle((60, 220, 790, 250), fill=PLATE, outline=DARK, width=4)   # the bed, raised
    d.text((330, 290), "BED, raised to the top", font=LABB, fill=INK)
    d.text((330, 330), "(build plate empty)", font=LAB, fill=MUTED)
    arrow(d, (200, 420), (200, 265))
    gauge(d, 810, 110, 330)
    gap_mark(d, 790, 830, 380, "GAP 2")
    d.text((40, DH - 50), "Side view. A diagram, not to scale.", font=LAB, fill=MUTED)
    return im


def wall_diagram():
    im = Image.new("RGB", (DW, DH), "white")
    d = ImageDraw.Draw(im)
    d.rectangle((60, 40, 900, 460), fill=(235, 235, 238), outline=DARK, width=4)
    d.text((480, 70), "THE BACK WALL, seen through the door", font=LABB, fill=INK, anchor="ma")
    d.rectangle((465, 110, 495, 440), fill=WALL)                    # the lead screw's slot
    d.text((510, 400), "centre slot:", font=LAB, fill=(176, 64, 64))
    d.text((510, 430), "keep clear", font=LAB, fill=(176, 64, 64))
    sf = font("Poppins-SemiBold.ttf", 21)
    for x0 in (90, 545):
        d.rounded_rectangle((x0, 170, x0 + 330, 260), radius=12, fill=(28, 28, 31), outline=ORANGE, width=4)
        d.text((x0 + 165, 200), "FOLLOW", font=sf, fill=ORANGE, anchor="mm")
        d.text((x0 + 165, 232), "@onbrandcraftz2026", font=sf, fill=ORANGE, anchor="mm")
    d.text((90, 290), "the sign: either side,", font=LAB, fill=MUTED)
    d.text((90, 322), "not both", font=LAB, fill=MUTED)
    return im


def main():
    a = Card("Camera sign: measure two gaps",
             "Before the sign is printed: how thin it has to be to clear the bed and the toolhead.")
    a.step(1, "Print the gap gauge", [
        "!gap_gauge.gcode.3mf: 27 min, 8.3 g, any colour, supports off. Print it flat as it lies.",
        "Twelve steps, 1.6 to 6.0 mm thick. Each step's thickness is printed on it.",
    ], crop(IMG / "gap_gauge_as_printed_three_quarter.png"), pic_h=330)
    a.step(2, "Gap 1: behind the toolhead", [
        "!Build plate empty, printer idle.",
        "In Bambu Handy, Controls: move the toolhead all the way to the back.",
        "Slide the gauge down between the back of the toolhead and the back wall, thin end first.",
        "!The thickest step that slides in without forcing is gap 1.",
    ], toolhead_diagram(), pic_h=470)
    b = Card("Camera sign: measure two gaps", "Then the bed, and send me both numbers.")
    b.step(3, "Gap 2: behind the bed", [
        "!Take the gauge out first.",
        "In Handy, Controls: raise the bed to the top.",
        "Slide the gauge down between the bed's back edge and the back wall, away from the centre slot.",
        "!The thickest step that slides in without forcing is gap 2.",
    ], bed_diagram(), pic_h=470)
    b.box("Never move the printer with the gauge in", [
        "Take it out before you move the toolhead or the bed again.",
        "If even the 1.6 end won't go in, stop: that spot is too tight for a sign.",
    ], BAD)
    c = Card("Camera sign: send me the numbers", "And where the sign will go.")
    c.box("Send me", [
        "Gap 1 (toolhead): the step number, for example 3.2.",
        "Gap 2 (bed): the step number.",
    ], GOOD)
    c.step(4, "Where the sign goes", [
        "On the back wall, to one side of the centre slot (the back bed screw runs in it).",
        "!Never over the slot.",
        "I'll make the sign about 1 mm thinner than the smaller gap.",
        "It sticks on with double-sided tape on its flat back.",
    ], wall_diagram(), pic_h=470)
    save_pdf([a, b, c], HERE / "Gap_Gauge_Guide.pdf",
             note="The gauge picture is a render of the real sliced part, not a photo. The printer pictures are diagrams, not to scale.")
    print("wrote", HERE / "Gap_Gauge_Guide.pdf")


if __name__ == "__main__":
    main()
