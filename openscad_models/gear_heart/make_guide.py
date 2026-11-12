#!/usr/bin/env python3
"""Gear heart test print: the PDF guide (2026-11-11), from renders of the real
exported parts. Times from checks/slices.txt; forces from checks/budget.txt.

    python3 make_guide.py      (Gear_Heart_Test_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Gear heart test: printing", "One plate, about 37 minutes. Before the heart is built around these parts.")
    a.step(1, "Print it flat, as it comes", [
        "!gear_heart_test.3mf, any one colour. 0.2 mm layers, supports off.",
        "Two bars with snap posts, and one pair of the heart's gears (16 and 12 teeth).",
        "The bars differ only in how far apart their posts are. 1 notch = tighter, 2 = looser.",
        "About 37 min and 9.1 g in Bambu Studio.",
    ], crop(IMG / "gear_test_three_quarter.png"), pic_h=470)
    b = Card("Gear heart test: what to check", "Design-review renders of the real parts, not photos.")
    b.step(1, "Press the gears onto the 1-notch bar", [
        "!Line a gear's hole up with a post and press straight down until it clicks.",
        "It takes a firm push, about 11 N: a little more than the weight of a 1 kg bag of sugar. The post's two prongs squeeze in, then spring back.",
        "Turn one gear: the other should turn with it, smoothly, all the way round.",
    ], crop(IMG / "gear_test_assembled.png"), pic_h=430)
    b.step(2, "Pull them off, press them onto the 2-notch bar", [
        "!Pull each gear straight up, hard: about 14 N. That tests the barb.",
        "Do this once only: the prongs are made to go on and stay on.",
        "Turn them again and compare with the first bar.",
    ])
    b.box("Good", ["Clicks on, then spins freely.", "Turns its partner smoothly, no catching.",
                   "Doesn't lift off when you turn it."], GOOD)
    b.box("Tell me", ["which bar meshes better (1 or 2 notches),", "if a gear was too hard to press on, or came off too easily,",
                      "and if a prong cracked."], BAD)
    save_pdf([a, b], HERE / "Gear_Heart_Test_Guide.pdf",
             note="Design-review renders of the real parts, not photos. The colour is only for the pictures.")


if __name__ == "__main__":
    main()
