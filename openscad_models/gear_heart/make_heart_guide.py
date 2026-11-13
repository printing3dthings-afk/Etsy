#!/usr/bin/env python3
"""Gear Heart: the PDF guide (2026-11-13), from renders of the real exported parts
(images/heart_*.png). Times and grams from the Bambu Studio slices,
checks/heart_plate.gcode.3mf and checks/heart_gears.gcode.3mf.

    python3 make_heart_guide.py      (Gear_Heart_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Gear Heart: printing", "Two prints: the heart plate with its posts, and fifteen gears.")
    a.step(1, "Print the plate", [
        "!gear_heart_plate.3mf, flat, supports off. About 2 h 15 m and 40.5 g.",
        "Fifteen posts stand up from it. Each has two springy prongs and a hook on top.",
    ], crop(IMG / "heart_plate_only.png"), pic_h=420)
    a.step(2, "Print the gears", [
        "!gear_heart_gears.3mf, flat, supports off. About 1 h 49 m and 26.6 g.",
        "One big gear with heart holes, one knob gear, seven 16-tooth and six 12-tooth gears.",
    ], crop(IMG / "heart_gears_plate.png"), pic_h=380)
    b = Card("Gear Heart: putting it together", "Design-review renders of the real parts, not photos.")
    b.step(3, "Press the gears on, in this order", [
        "!The heart-hole gear goes on the post in the top dip. The knob gear goes in the middle.",
        "Then work down both sides from the top: a 16-tooth gear, then a 12, then a 16, and so on.",
        "Turn each gear until its teeth slip into its neighbour's, then press straight down until it clicks.",
        "The 16-tooth gear at the bottom point goes on last. Its teeth line up with both sides.",
    ], crop(IMG / "heart_top.png"), pic_h=430)
    b.step(4, "Turn the knob", [
        "!Every gear turns together, each the opposite way to its neighbours.",
    ])
    b.box("Good", ["All fifteen gears turn smoothly from the knob.", "No gear lifts off as it turns."], GOOD)
    b.box("Good to know", ["The posts are made to be pressed on once.", "Pulling gears off and on again and again wears the hooks."], BAD)
    save_pdf([a, b], HERE / "Gear_Heart_Guide.pdf",
             note="Design-review renders of the real parts, not photos. The colours are only for the pictures.")


if __name__ == "__main__":
    main()
