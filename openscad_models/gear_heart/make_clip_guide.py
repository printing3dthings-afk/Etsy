#!/usr/bin/env python3
"""Gear heart clips v2 test print: the PDF guide (2026-11-14, Brief E), from renders of
the real exported parts. Time and weight from checks/slices.txt; forces from
checks/clip_budget.txt; end play from checks/fit_clip.txt.

    python3 make_clip_guide.py      (Gear_Heart_Clip_Test_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Gear heart clips v2: printing",
             "The new axle pins, at the heart's real size, before the heart is rebuilt around them.")
    a.step(1, "Print it flat, as it comes", [
        "!gear_heart_clip_test.3mf, any one colour. 0.2 mm layers, supports off.",
        "One bar with three bosses, three pins lying on their sides, three of the heart's gears.",
        "About 37 min and 8.8 g in Bambu Studio.",
        "The pins print on their sides on purpose. The old posts stood upright and bent across "
        "their layers, which is why one snapped. These bend along the layers.",
    ], crop(IMG / "clip_plate.png"), pic_h=470)
    a.step(2, "Which pin goes where", [
        "!The three pins differ only in how far their barbs reach over the gear.",
        "1 dimple on the pin's head = the smallest barb. It goes in the boss with 1 groove on the bar's front edge.",
        "2 dimples = the design value, 2 grooves. 3 dimples = the biggest barb, 3 grooves.",
    ])

    b = Card("Gear heart clips v2: what to check", "Design-review renders of the real parts, not photos.")
    b.step(1, "Fit each pin", [
        "!Set a gear on a boss. Push the pin up from underneath, through the boss and the gear, "
        "until its head sits flush in the slot on the bar's underside.",
        "The two prongs squeeze together on the way up, then the barbs click out over the gear.",
        "Expect a firm push: about 18 N for pin 1, 22 N for pin 2, 26 N for pin 3 "
        "(roughly lifting a 2 to 2.5 kg bag).",
    ], crop(IMG / "clip_section.png"), pic_h=520)
    b.step(2, "Spin, then pull", [
        "!Spin each gear: it should turn freely, all the way round.",
        "It can rattle up and down a little, about 0.8 mm. That's designed in.",
        "Pull each gear straight up, hard. It should not come off: the barbs' catch is square.",
    ], crop(IMG / "clip_assembled.png"), pic_h=430)
    b.step(3, "Take one off", [
        "!Pinch the two barbs together and push the pin back down and out.",
        "Then fit it again. The pins are meant to come out for cleaning or a repair.",
    ])
    b.box("Good", ["Clicks on with a firm push, no cracking sound.",
                   "Spins freely and doesn't lift off when pulled.",
                   "Comes out when you pinch the barbs, and goes back in."], GOOD)
    b.box("Tell me", ["which pin felt best (1, 2 or 3 dimples): going on, and holding on,",
                      "if any prong cracked or went white at its root (where it meets the head),",
                      "if a gear came off when pulled, or was too hard to fit."], BAD)
    save_pdf([a, b], HERE / "Gear_Heart_Clip_Test_Guide.pdf",
             note="Design-review renders of the real parts, not photos. The colours are only for the pictures.")


if __name__ == "__main__":
    main()
