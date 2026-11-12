#!/usr/bin/env python3
"""Moon Phase Coasters: the PDF guide (2026-11-11), from the renders of the real
exported parts (run render_guide.py and the review renders first). Times and grams
are from checks/slices.txt.

    python3 make_guide.py      (Moon_Phase_Coasters_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Moon Phase Coasters: printing", "Six prints on three plates. Navy, cream and slate.")
    a.step(1, "Print the coasters, two to a plate", [
        "!moon_coasters_crescent_quarter.3mf, then moon_coasters_gibbous_full.3mf.",
        "Face up, no supports. The moon, craters and stars are the top three layers.",
        "About 2 h each plate. Navy 33.8 g, cream 3.6-5.6 g, slate 1.7-3.6 g.",
    ], crop(IMG / "guide_parts.png"), pic_h=520)
    a.step(2, "Print the rack", [
        "!moon_coaster_rack.3mf: the base and the arch panel, both flat.",
        "About 2 h 2 m. Navy 41.1 g, cream 3.2 g.",
        "0.2 mm layers, supports off, for every plate.",
    ])
    b = Card("Moon Phase Coasters: putting it together", "Design-review renders of the real parts, not photos.")
    b.step(1, "Stand the panel in the front groove", [
        "!Stars to the front. Push it down to the bottom of the groove.",
        "It stands on its own, no glue.",
    ], crop(IMG / "guide_panel.png"), pic_h=470)
    b.step(2, "Lower the coasters into the cradles", [
        "!Moon side to the front. Each one rests in its own curved slot.",
        "The front coaster shows through the window. Put any phase in front.",
        "Lift a coaster straight up to take it out.",
    ], crop(IMG / "guide_coaster.png"), pic_h=470)
    b.box("Good", ["Coasters drop in and lift out by hand.", "The panel stands upright in its groove."], GOOD)
    b.box("Tell me", ["if a slot is tight or a coaster rattles,", "or a star, crater or moon edge printed badly."], BAD)
    save_pdf([a, b], HERE / "Moon_Phase_Coasters_Guide.pdf",
             note="Design-review renders of the real parts, not photos. Navy, cream and slate are the print colours.")


if __name__ == "__main__":
    main()
