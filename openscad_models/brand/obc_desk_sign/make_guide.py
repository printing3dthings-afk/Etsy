#!/usr/bin/env python3
"""OBC desk sign: the PDF guide (2026-11-11), from the renders of the real exported
parts (run render_guide.py and the review renders first). Times and grams are from
checks/slices.txt.

    python3 make_guide.py      (OBC_Desk_Sign_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("OBC desk sign: printing", "Two prints: the plaque (black, then gold) and the base (black).")
    a.step(1, "Print the plaque face up", [
        "!obc_desk_sign_plaque.3mf. Black for the plaque, gold for the letters.",
        "With an AMS it swaps to gold once, at 5.2 mm, and prints gold to the top.",
        "With one spool: in the preview, add a pause at 5.0 mm, then load gold.",
        "About 2 h 20 m. 43.9 g black, 10.6 g gold.",
    ], crop(IMG / "guide_parts.png"), pic_h=560)
    a.step(2, "Print the base", [
        "!obc_desk_sign_base.3mf, in black. About 1 h 36 m, 46.6 g.",
        "0.2 mm layers, supports off, for both prints.",
    ])
    b = Card("OBC desk sign: putting it together", "Design-review renders of the real parts, not photos.")
    b.step(1, "Slide the plaque into the slot", [
        "!Letters to the front. Push it all the way down.",
        "It leans back about 10 degrees on its own. No glue needed.",
    ], crop(IMG / "guide_insert.png"), pic_h=560)
    b.step(2, "Done", [], crop(IMG / "obc_desk_sign_three_quarter.png"), pic_h=520)
    b.box("Good", ["Slides in by hand and stands steady.", "Every stripe is a clean black line."], GOOD)
    b.box("Tell me", ["if the slot is tight or loose,", "or any stripe or letter edge printed badly."], BAD)
    save_pdf([a, b], HERE / "OBC_Desk_Sign_Guide.pdf",
             note="Design-review renders of the real parts, not photos. Black and gold are the print colours.")


if __name__ == "__main__":
    main()
