#!/usr/bin/env python3
"""Snowfall Plinko test print: the PDF guide (2026-11-16), from renders of the real parts.
Time and weight from checks/slice.json (Bambu Studio's slice).

    python3 make_guide.py      (Plinko_Release_Test_Guide.pdf)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    s = json.loads((HERE / "checks" / "slice.json").read_text())
    a = Card("Snowfall Plinko test: printing", "Do balls print loose inside a closed board? One print, nothing to assemble.")
    a.step(1, "Print it as it comes", [
        f"!plinko_release_test.gcode.3mf: PLA Matte, 0.2 mm layers, supports off. About {s['time']} and {s['filament_g']} g.",
        "It prints on its back. The grid on top is the front, and the balls print underneath it, inside.",
    ], crop(IMG / "release_plate.png"), pic_h=430)
    a.step(2, "Which is which", [
        "!Notches on the outside wall say how each set of balls was printed:",
        "1 notch (the small top pocket): balls hang 0.2 mm above the floor.",
        "2 notches (the hourglass): 0.4 mm above the floor.",
        "3 notches (the small bottom pocket): balls printed onto the floor through a thin neck.",
    ], crop(IMG / "release_inside.png"), pic_h=400)
    b = Card("Snowfall Plinko test: what to check", "Design-review renders of the real parts, not photos.")
    b.step(1, "Free the balls", [
        "!Shake it. Then tap it on the table. Count how many balls rattle free in each part.",
        "Any that won't: poke them sideways through the grid with a toothpick. The 3-notch ones need this; it snaps their necks.",
    ])
    b.step(2, "Play with the hourglass", [
        "!Stand it up on its end. The balls should fall through the neck and the pegs into the bins at the bottom.",
        "Flip it over: they should fall back through the other set of pegs. Try it a few times.",
    ])
    b.box("Good", ["Every ball comes free with a shake, a tap or a poke.",
                   "They roll smoothly and never get stuck between pegs or in the neck.",
                   "The grid front is straight and doesn't touch the balls."], GOOD)
    b.box("Tell me", ["which set came free most easily (1, 2 or 3 notches), and how,",
                      "whether any ball got stuck, and where,",
                      "how the grid front looks: any sagging or stringing,",
                      "and whether the balls look and roll like balls."], BAD)
    save_pdf([a, b], HERE / "Plinko_Release_Test_Guide.pdf",
             note="Design-review renders of the real parts, not photos. Not for children under 3: small parts.")


if __name__ == "__main__":
    main()
