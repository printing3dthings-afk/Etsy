#!/usr/bin/env python3
"""Snowflake Screen: the PDF guide (2026-11-12), from the renders of the real
exported parts (run render_guide.py and the review renders first). Times and grams
are from checks/slice_screen.txt and checks/slice_coupon.txt.

    python3 make_guide.py      (Snowflake_Screen_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    t = Card("Snowflake Screen: hinge test first", "One hinge at full size, two pin-hole sizes. 24 min, 7.5 g.")
    t.step(1, "Print the test and cut two pins", [
        "!snowflake_hinge_test.3mf, flat, no supports.",
        "Cut two 28 mm pieces of 1.75 mm filament, straight ends.",
        "One notch on the leaf = 2.0 mm hole. Two notches = 2.3 mm.",
    ], crop(IMG / "guide_coupon.png"), pic_h=470)
    t.step(2, "Push a pin into each and try them", [
        "!Push down from the open end until it stops at the closed end.",
        "Fold each one back and forth, about 100° each way.",
        "Stand it on its edge at an angle: does it hold its angle, or flop?",
    ])
    t.box("Good", ["The pins go in by hand, all the way.", "The leaves turn smoothly and never stick together."], GOOD)
    t.box("Tell me", ["which hole you prefer (1 or 2 notches),", "if a pin won't go in, or the leaves were stuck."], BAD)

    a = Card("Snowflake Screen: printing", "Three panels in one print, flat. Ice blue and white.")
    a.step(1, "Print the screen", [
        "!snowflake_screen.3mf: three panels, their hinge knuckles interleaved.",
        "Face up, no supports. The snowflakes are the top three layers.",
        "About 2 h 10 m. Blue 40.7 g, white 2.1 g. 0.2 mm layers.",
    ], crop(IMG / "guide_parts.png"), pic_h=470)
    a.step(2, "Cut two pins", [
        "!Two 88 mm pieces of 1.75 mm filament, straight ends.",
        "Any colour: only the ends show, at the top of each hinge.",
    ])
    b = Card("Snowflake Screen: pinning and standing", "Design-review renders of the real parts, not photos.")
    b.step(1, "Push a pin down each hinge", [
        "!Into the small hole at the top, snowflakes facing up.",
        "Push it all the way down: the hole is closed at the bottom.",
    ], crop(IMG / "guide_pin.png"), pic_h=470)
    b.step(2, "Fold the side panels back and stand it up", [
        "!Snowflakes to the front, the two wings turned back.",
        "It stands best with the wings at about 30 to 60°.",
        "The hinges stop at about 100°: it doesn't fold flat.",
    ], crop(IMG / "snowflake_screen_three_quarter.png"), pic_h=470)
    b.box("Good", ["The panels fold smoothly.", "It stands on its own on a flat shelf."], GOOD)
    b.box("Tell me", ["if a hinge is stiff or loose,", "or a snowflake printed badly."], BAD)
    save_pdf([t, a, b], HERE / "Snowflake_Screen_Guide.pdf",
             note="Design-review renders of the real parts, not photos. Ice blue and white are the print colours.")


if __name__ == "__main__":
    main()
