#!/usr/bin/env python3
"""Printed 6 mm balls for the Pie Caddy bearing test: the PDF guide (2026-11-12).
Pictures: the toolpath render of the real slice (images/printed_bbs_as_printed.png),
one ball as modelled (images/printed_bb_side.png), and the bearing test's own
balls-in render (guide/images/balls_in.png). Time and grams from Bambu Studio's slice
(printed_bbs_fine_0.12mm.gcode.3mf).

    python3 make_printed_bb_guide.py      (Printed_BB_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PC = HERE.parent
sys.path.insert(0, str(PC.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402


def main():
    a = Card("Printed 6 mm balls", "30 balls for the Pie Caddy bearing test: 27 go in, 3 are spares.")
    a.step(1, "Print them", [
        "!printed_bbs_fine_0.12mm.gcode.3mf: already sliced, send it straight to the printer.",
        "0.12 mm layers, no supports, a 3 mm brim round each ball. About 29 min and 4.2 g.",
        "Each ball stands on a small flat (3 mm across) so its first layers don't sag.",
        "Snap each ball off its brim ring: there's a 0.1 mm gap, so it breaks clean."
    ], crop(PC / "images" / "printed_bbs_as_printed.png"), pic_h=430)
    a.step(2, "Tidy them (optional, 2 minutes)", [
        "!Each ball has a seam up one side, where every layer starts. It's the main bump.",
        "Roll them between two sheets of fine sandpaper, or shake them in a jar with a strip of it.",
    ], crop(PC / "images" / "printed_bb_side.png"), pic_h=330)
    b = Card("Printed 6 mm balls: in the bearing test", "Design-review renders, not photos.")
    b.step(3, "Put 27 in the bearing test", [
        "!Drop them into the channel, then set the top on. Flat side any way up.",
        "Put a mug on top and give it a flick.",
    ], crop(HERE / "images" / "balls_in.png"), pic_h=430)
    b.box("Good", [
        "It spins with a flick and coasts for a turn or more.",
        "No wobble, and no balls climbing out of the channel.",
    ], GOOD)
    b.box("Tell me", [
        "spins and coasts, rough or rumbly, or stops dead;",
        "if any ball stuck flat-side down and slid instead of rolling;",
        "if you try airsoft BBs too, which one turned better.",
    ], BAD)
    save_pdf([a, b], PC / "Printed_BB_Guide.pdf",
             note="Design-review renders and a toolpath render of the real slice, not photos.")


if __name__ == "__main__":
    main()
