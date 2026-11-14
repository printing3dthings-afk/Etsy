#!/usr/bin/env python3
"""Pocket Top snap test print: the PDF guide (2026-11-14), from renders of the real parts.
Time and weight from FACTS.md (Bambu Studio slice); forces from checks/snap_budget.txt.

    python3 make_guide.py      (Pocket_Top_Snap_Test_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Pocket Top snap test: printing",
             "The joint every Pocket Top design will use, before the top itself is designed.")
    a.step(1, "Print it flat, as it comes, in matte PLA", [
        "!pocket_top_snap_test.3mf. PLA Matte, 0.2 mm layers, supports off.",
        "Three round hubs and three short hex stems. About 31 min and 7.7 g.",
        "Matte PLA on purpose: it's what the top will be made in, and it cracks more easily "
        "than plain PLA. This is the test of whether it can take it.",
    ], crop(IMG / "snap_plate.png"), pic_h=460)
    a.step(2, "Which goes with which", [
        "!A hub with 1, 2 or 3 notches in its edge goes with the stem with 1, 2 or 3 flats on its grip.",
        "They differ only in how far the hub's three little nubs reach into the stem's groove: "
        "1 = least (0.35 mm), 2 = the design value (0.45), 3 = most (0.55).",
    ])
    b = Card("Pocket Top snap test: what to check", "Design-review renders of the real parts, not photos.")
    b.step(1, "Snap it together", [
        "!Push the stem's narrow end into the hub's top: the face that was facing up on the printer "
        "(the bottom one is smoother, from the plate). Any way round. Push until the grip sits flat on the hub and it clicks.",
        "Into the bottom face it won't click: the groove only lines up from the top.",
        "About 8 N for pair 1, 10 N for pair 2, 12 N for pair 3: a firm press.",
    ], crop(IMG / "snap_section.png"), pic_h=430)
    b.step(2, "Snap it apart and back, 20 times", [
        "!Pull the stem straight out by its grip, then snap it back in. Do that 20 times for each pair.",
        "It comes apart more easily than it goes on (about 4 to 6 N). That's designed in.",
        "After 20, look at the root of each spring beam, where it joins the hub, for white "
        "marks or cracks.",
    ], crop(IMG / "snap_assembled.png"), pic_h=400)
    b.step(3, "Drop it", [
        "!Snapped together, drop each pair onto a table from about 30 cm, five times. Does the hub fall off?",
    ])
    b.box("Good", ["Clicks in and out cleanly all 20 times.", "No white marks or cracks at the beam roots.",
                   "Stays together when dropped; no wobble when you spin the stem in your fingers."], GOOD)
    b.box("Tell me", ["for each pair (1, 2, 3): how many snaps before anything whitened or cracked, if any,",
                      "which felt best going on and staying on,",
                      "and whether any came apart when dropped."], BAD)
    save_pdf([a, b], HERE / "Pocket_Top_Snap_Test_Guide.pdf",
             note="Design-review renders of the real parts, not photos. The colours are only for the pictures. "
                  "Not for children under 3: small parts.")


if __name__ == "__main__":
    main()
