#!/usr/bin/env python3
"""Iris box coupon: the test guide (2026-11-12), from the review renders of the real
exported parts (images/iris_coupon_*.png). Times and grams from the Bambu slices in
checks/iris_coupon_{0,1}.gcode.3mf.

    python3 make_guide.py      (Iris_Coupon_Test_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Iris box: blade test", "One real blade, its pivot and a piece of the twist ring, at full size.")
    a.step(1, "Print both test pieces", [
        "!iris_coupon_1.3mf (one notch on the base's edge) and iris_coupon_2.3mf (two notches).",
        "Flat as they come, no supports. About 30 min and 8.6 g each.",
        "Each is three parts: the base, the blade, and the ring piece (pin and tongue facing up).",
        "They differ only in the gap round the pins and in the groove: 0.40 mm and 0.55 mm.",
    ], crop(IMG / "iris_coupon_plate.png"), pic_h=420)
    a.step(2, "Put it together", [
        "!Blade over the base's pin, through the round hole, either side up.",
        "Turn the ring piece over: its tongue goes in the base's curved groove,",
        "and its pin drops into the blade's long slot. Nothing is glued.",
    ], crop(IMG / "iris_coupon_open.png"), pic_h=420)
    b = Card("Iris box: blade test, sliding it", "Design-review renders of the real parts, not photos.")
    b.step(3, "Slide the ring piece along the groove", [
        "!From one end of the groove to the other, with one finger, pressing lightly down.",
        "The blade swings about 49° from tucked against the rim to across the middle.",
        "Each end of the groove stops it. Try it slowly, then quickly, a dozen times.",
    ], crop(IMG / "iris_coupon_closed.png"), pic_h=420)
    b.box("Good", [
        "The blade swings the whole way without catching or tipping up.",
        "It doesn't rattle loose, and it doesn't need pushing hard.",
    ], GOOD)
    b.box("Tell me, for each test piece", [
        "smooth, a little stiff, or sticks (and where in the swing);",
        "loose or wobbly; if the pin left the slot or the tongue the groove;",
        "which of the two you'd rather have six of in a box.",
    ], BAD)
    save_pdf([a, b], HERE / "Iris_Coupon_Test_Guide.pdf",
             note="Design-review renders of the real parts, not photos.")


if __name__ == "__main__":
    main()
