#!/usr/bin/env python3
"""Zero-gap joint test: the PDF guide (2026-11-14), from renders of the real parts.
Time and weight from checks/slice.txt.

    python3 make_guide.py      (Zero_Gap_Joint_Test_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Zero-gap joint test: printing",
             "Can a moving part print with NO gap, if the gap is filled with a material that doesn't stick?")
    a.step(1, "Load two materials", [
        "!AMS slot 1: PLA (any colour). AMS slot 2: Bambu Support For PLA.",
        "Open zero_gap_coupon.gcode.3mf and print it as it is: about 1 h 1 min, 15.9 g PLA "
        "and 4.3 g of support material (most of that is purge between colours).",
        "Ironing is off on purpose: smoothing the top could smear across the joint and weld it.",
    ], crop(IMG / "zero_gap_plate.png"), pic_h=420)
    a.step(2, "What's what", [
        "!Three little turntables. Each has a rotor (with a coin slot) inside a ring, held in by a V-shaped ridge.",
        "1 dot: today's way, a 0.3 mm air gap.",
        "2 dots: NO air gap, a one-line sleeve of support material fills the gap.",
        "3 dots: the sleeve plus 0.1 mm of air.",
    ], crop(IMG / "zero_gap_section.png"), pic_h=380)
    b = Card("Zero-gap joint test: what to check", "Design-review renders of the real parts, not photos.")
    b.step(1, "Break each one free", [
        "!Put a coin in the slot and turn. The first turn may need a firm twist to break the sleeve free.",
        "Don't pull the sleeve out: it's meant to stay in the gap as a bearing.",
    ])
    b.step(2, "Compare the wobble", [
        "!Once turning, rock each rotor side to side and up and down with a fingertip.",
        "Turntable 1 should rattle a little (that's the air gap we always need).",
        "If 2 and 3 turn smoothly with less or no rattle, the idea works.",
    ])
    b.box("Good", ["2 or 3 turns all the way round after the first twist.",
                   "Less wobble than 1.", "The sleeve stays in, in one piece."], GOOD)
    b.box("Tell me", ["for 2 and 3: did it turn at all, how hard was the first twist, and how smooth after,",
                      "wobble compared with 1 (more, same, less, none),",
                      "and whether the sleeve came out or crumbled."], BAD)
    save_pdf([a, b], HERE / "Zero_Gap_Joint_Test_Guide.pdf",
             note="Design-review renders of the real parts, not photos. Colours are only for the pictures: orange is the support material.")


if __name__ == "__main__":
    main()
