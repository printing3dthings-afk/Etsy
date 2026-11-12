#!/usr/bin/env python3
"""Ocarina voicing whistles: the test guide (2026-11-12), from the review renders of the
real exported whistle (images/voicing_whistle_*.png). Times and grams from
checks/slice_whistles.txt.

    python3 make_guide.py      (Ocarina_Voicing_Test_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Ocarina voicing test", "Two small whistles with the ocarina's real mouthpiece and sound edge.")
    a.step(1, "Print both whistles", [
        "!voicing_whistle_1.3mf (one notch on the end) and voicing_whistle_2.3mf (two notches).",
        "Lying flat as they come, no supports. About 25 min and 10 g each.",
        "They differ only in the air slot: 1.0 mm (one notch) and 1.3 mm (two notches).",
    ], crop(IMG / "voicing_whistle_three_quarter.png"), pic_h=470)
    a.step(2, "Blow gently into the slot at the flat end", [
        "!The slot is the thin upright slit at the end nearest the arched window.",
        "The sound comes from that window. The notches at the other end are only labels.",
        "Soft, steady breath. Too hard and it jumps up an octave or squeals.",
    ], crop(IMG / "voicing_whistle_mouthpiece.png"), pic_h=420)
    b = Card("Ocarina voicing test: what to measure", "Any tuner app on your phone. Design-review renders, not photos.")
    b.step(3, "Three notes from each whistle", [
        "!All holes covered: the note and how far off it is (cents), or the Hz.",
        "Small hole (front) open, big hole (back) covered.",
        "Both holes open.",
    ])
    b.box("Tell me, for each whistle", [
        "the three readings (Hz, or note and cents);",
        "which one sounds cleaner and needs less breath;",
        "if either one only hisses or squeals.",
    ], GOOD)
    b.box("Why it matters", [
        "Those six readings set the ocarina's chamber size and all 12 hole sizes.",
        "Its sound edge and air slot will be exactly these.",
    ], BAD)
    save_pdf([a, b], HERE / "Ocarina_Voicing_Test_Guide.pdf",
             note="Design-review renders of the real whistle, not photos.")


if __name__ == "__main__":
    main()
