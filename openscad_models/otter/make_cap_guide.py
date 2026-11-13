#!/usr/bin/env python3
"""Otter capped joint test: the PDF guide (2026-11-13), from renders of the real
exported parts (images/cap_coupon.png, cap_swung.png, cap_cutaway.png). Time and grams
from the Bambu Studio slice, checks/cap_coupon.gcode.3mf.

    python3 make_cap_guide.py      (Otter_Capped_Joint_Test_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Otter capped joint test", "Your number 1 joint, with a cap on top that hides it.")
    a.step(1, "Print it flat, as it comes", [
        "!otter_capped_joint_test.3mf, any one colour. 0.2 mm layers, supports off.",
        "Two joints, each two blocks already joined. About 40 min and 14.6 g.",
        "The joint inside is your 0.30 mm one. Only the gap under the cap differs:",
        "1 notch on the block = 0.30 mm under the cap, 2 notches = 0.40 mm.",
    ], crop(IMG / "cap_coupon.png"), pic_h=430)
    a.step(2, "What's inside (cut through the middle)", [
        "!The pin goes up into a round cap. The cap sits in a cone-shaped dip in the other block.",
        "From the top you see only a thin circle. The otter's joints will look like this.",
    ], crop(IMG / "cap_cutaway.png"), pic_h=380)
    b = Card("Otter capped joint test: what to check", "Design-review renders of the real parts, not photos.")
    b.step(3, "Free it, then swing it", [
        "!Hold both blocks and wiggle gently side to side, a few times.",
        "It should swing about 20 degrees each way, then stop firmly.",
        "Then try to pull the blocks apart, and to lift one off the other.",
    ], crop(IMG / "cap_swung.png"), pic_h=430)
    b.box("Good", ["Swings as freely as your number 1 joint did.", "The cap turns with no scraping.",
                   "Won't pull apart or lift off."], GOOD)
    b.box("Tell me", ["which one (1 or 2 notches) feels better,", "if either stayed stuck at the cap, or scrapes,",
                      "and how the top looks: does the circle seam show much?"], BAD)
    save_pdf([a, b], HERE / "Otter_Capped_Joint_Test_Guide.pdf",
             note="Design-review renders of the real parts, not photos. The colours are only for the pictures.")


if __name__ == "__main__":
    main()
