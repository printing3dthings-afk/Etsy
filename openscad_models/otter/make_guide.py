#!/usr/bin/env python3
"""Otter joint test print: the PDF guide (2026-11-11), from renders of the real
exported parts. Times from checks/slices.txt.

    python3 make_guide.py      (Otter_Joint_Test_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Otter joint test: printing", "One plate, about 28 minutes. Before the otter is built around this joint.")
    a.step(1, "Print it flat, as it comes", [
        "!otter_joint_test.3mf, any one colour. 0.2 mm layers, supports off.",
        "Three joints, each a pin in a C-shaped ring. They print already joined.",
        "The notches on the left block say which gap: 1 = 0.30 mm, 2 = 0.35, 3 = 0.45.",
        "About 28 min and 8.4 g in Bambu Studio.",
    ], crop(IMG / "otter_joint_test_three_quarter.png"), pic_h=480)
    b = Card("Otter joint test: what to check", "Design-review renders of the real parts, not photos.")
    b.step(1, "Free each joint", [
        "!Hold both blocks and wiggle gently side to side, a few times.",
        "Each should swing about 20 degrees each way, then stop firmly.",
    ], crop(IMG / "otter_joint_test_swung.png"), pic_h=460)
    b.step(2, "Try to pull it apart", [
        "!Pull the blocks straight apart, then try to lift one off the other.",
        "Neither should come apart. Don't force it past a firm tug.",
    ])
    b.box("Good", ["Swings freely, no grinding.", "Stops at the same angle both ways.",
                   "Won't pull apart or lift off."], GOOD)
    b.box("Tell me", ["which gap (1, 2 or 3 notches) feels best,", "any that stayed stuck, or are loose and floppy,",
                      "and any that came apart."], BAD)
    save_pdf([a, b], HERE / "Otter_Joint_Test_Guide.pdf",
             note="Design-review renders of the real parts, not photos. The colour is only for the pictures.")


if __name__ == "__main__":
    main()
