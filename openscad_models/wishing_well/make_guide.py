#!/usr/bin/env python3
"""Wishing Well windlass test print: the PDF guide (2026-11-15), from renders of the real parts.
Time and weight from checks/slice.txt (Bambu Studio's slice); forces from checks/windlass_budget.txt;
directions from checks/fit_windlass.txt.

    python3 make_guide.py      (Wishing_Well_Windlass_Test_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Wishing Well windlass test: printing",
             "The crank, ratchet and bearings for the Stone Wishing Well, tested before the well is built round them.")
    a.step(1, "Print it as it comes", [
        "!windlass_test.gcode.3mf: PLA Matte, 0.2 mm layers, supports off. About 46 min and 17 g.",
        "It uses Bambu's own speeds, not the slower retail outer walls: it's a test of how it works, not how it looks.",
        "Eight parts: a stand, three posts, the axle, the crank wheel, the pawl (the little hook) and a bucket.",
    ], crop(IMG / "windlass_plate.png"), pic_h=460)
    a.step(2, "Which post is which", [
        "!Notches on a post's edge, near its foot, say how hard it grips the axle:",
        "1 notch = the lightest grip (0.40 mm), 2 = the design value (0.55), 3 = the firmest (0.70).",
        "The post with the tall arm and the pin is the crank side (2 notches). The other two are far-side posts to swap between.",
    ], crop(IMG / "windlass_cradle.png"), pic_h=420)
    a.step(3, "You'll also need", [
        "About 40 cm of thin twine or thread (up to 1.5 mm).",
    ])

    b = Card("Wishing Well windlass test: putting it together",
             "Design-review renders of the real parts, not photos.")
    b.step(1, "Posts into the stand", [
        "!The crank post goes in one socket with its arm and pin facing OUT, away from the other socket. "
        "A far post goes in the other socket. Both with their open tops up.",
    ])
    b.step(2, "The wheel onto the axle", [
        "!Push the wheel onto the axle's six-sided end, smooth face first (the face that was on the plate), "
        "handle peg facing out. Push until it clicks down onto the round collar.",
        "It's the same snap as your Pocket Top test: three little springs grip a groove.",
    ])
    b.step(3, "Twine on the drum", [
        "!Thread the twine through the small hole across the drum (the fat middle of the axle) and knot it.",
    ])
    b.step(4, "Snap the axle into the posts", [
        "!Wheel on the crank post's side. Set each round end in a post's open top and press straight down until it clicks into the round seat.",
        "About 17 N (a firm press) for the 2-notch posts; less for 1 notch, more for 3.",
    ], crop(IMG / "windlass_assembled.png"), pic_h=480)
    b.step(5, "Hang the pawl", [
        "!Turn the pawl so it points straight up, line its slot up with the pin's flat head, slide it on, "
        "then swing it down over the wheel. Its tip drops between two teeth.",
        "Once it's down it can't come off: the slot only lines up with the head when the pawl points straight up.",
    ], crop(IMG / "windlass_ratchet.png"), pic_h=480)
    b.step(6, "The bucket", [
        "!Thread the twine's free end down through each of the bucket's two ears and knot it under each one, as a handle.",
        "The twine must leave the drum on the pawl's side: on the right, looking at the wheel from outside.",
        "On this short test stand the bucket is wider than the gap between the posts, so stand it at the "
        "edge of a table, twine side out, and let the bucket hang over the edge.",
    ])

    c = Card("Wishing Well windlass test: what to check", "")
    c.step(1, "Wind it up", [
        "!Looking at the wheel from outside, turn the handle anticlockwise (top of the wheel moving away from the pawl).",
        "It should click every 15 degrees, about 1.3 mm of twine per click, and the bucket rises.",
    ])
    c.step(2, "Let go", [
        "!The bucket should stay exactly where you left it. Then pull the bucket down hard by hand: the pawl should hold.",
    ])
    c.step(3, "Let it down", [
        "!Lift the pawl's tip off the teeth with a fingertip and let the bucket down slowly.",
    ])
    c.step(4, "Try to break it", [
        "!Crank hard, pushing the handle up, down and sideways. The axle must not pop out of its posts.",
        "Pull the wheel straight off by its rim. It should be hard to pull off.",
        "Swap the far post for the other two (1 and 3 notches): press the axle in and out of each a few times.",
    ])
    c.box("Good", ["Clicks cleanly every 15 degrees, winds smoothly.",
                   "The bucket stays up on its own and the pawl never slips.",
                   "The axle stays seated however you crank it; the wheel stays on.",
                   "No white marks at the base of the posts' springy fingers (the slots beside each seat)."], GOOD)
    c.box("Tell me", ["which post grip (1, 2 or 3 notches) felt best going in, and held best,",
                      "whether the pawl ever slipped or missed a tooth,",
                      "whether the wheel or the axle ever came loose,",
                      "and anything that whitened or cracked."], BAD)
    save_pdf([a, b, c], HERE / "Wishing_Well_Windlass_Test_Guide.pdf",
             note="Design-review renders of the real parts, not photos. Not for children under 3: small parts.")


if __name__ == "__main__":
    main()
