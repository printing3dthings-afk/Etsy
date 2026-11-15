#!/usr/bin/env python3
"""Pocket Top UFO: the PDF guide (2026-11-15), from renders of the real parts.
Time and weight from checks/slice_*.json (Bambu Studio's slice); the spin range from
checks/spin_estimate.txt, stated as an estimate.

    python3 make_ufo_guide.py      (Pocket_Top_UFO_Guide.pdf)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def sliced(name):
    d = json.loads((HERE / "checks" / f"slice_{name}.json").read_text())
    return d["time"], d["filament_g"]


def main():
    t, g = sliced("plate")
    a = Card("Pocket Top UFO: printing", "A two-part spinning top: a saucer and a domed stem that snap together.")
    a.step(1, "Print it as it comes", [
        f"!ufo_top.gcode.3mf: PLA Matte, 0.20 mm Standard, supports off. About {t} and {g} g.",
        "Both parts on one plate, in one colour. The saucer lies flat; the stem stands on its dome's flat top.",
        "Two colours (saucer in one, stem in another) means two plates, about 11 minutes.",
    ], crop(IMG / "ufo_plate.png"), pic_h=460)
    a.step(2, "Which part is which", [
        "!The saucer: 34 mm across, nine little lights round its rim, three springy beams round a six-sided hole.",
        "The stem: the dome with the face on one end, a six-sided shaft and a pointed tip on the other.",
    ])

    b = Card("Pocket Top UFO: putting it together", "Design-review renders of the real parts, not photos.")
    b.step(1, "Point the tip down through the saucer", [
        "!Hold the saucer with its lights facing up (the face that was on top on the printer).",
        "Push the stem's tip down through the six-sided hole from above, dome on top.",
    ], crop(IMG / "ufo_exploded.png"), pic_h=520)
    b.step(2, "Line up the six sides and press", [
        "!Turn the stem until its shaft drops into the hole, then press the dome down firmly.",
        "It clicks when the three springs catch the groove. The dome then sits just above the saucer.",
        "To take it apart, hold the saucer and pull the dome straight up.",
    ], crop(IMG / "ufo_three_quarter.png"), pic_h=520)

    c = Card("Pocket Top UFO: spinning it, and what to check", "")
    c.step(1, "Spin it", [
        "!On a smooth, hard table: pinch the dome's flat top and twist hard, letting go as you twist.",
        "Our estimate from a firm twist is roughly 15 to 60 seconds, depending on how hard you spin it. "
        "It's a calculation, not a timed spin: please time yours.",
    ])
    c.box("Good", ["It clicks together and stays together when spun and when dropped on a table.",
                   "The dome turns the saucer: no slipping between them.",
                   "It spins upright without wobbling until it slows down.",
                   "The eyes and mouth are crisp, with no stringy or sagging edges."], GOOD)
    c.box("Tell me", ["how long it spun (best of three firm twists),",
                      "whether it came apart, or anything cracked, after 20 snaps together and apart,",
                      "whether the tip wore or chipped,",
                      "and whether it wobbled from the start (a sign it's off-centre)."], BAD)
    save_pdf([a, b, c], HERE / "Pocket_Top_UFO_Guide.pdf",
             note="Design-review renders of the real parts, not photos. Not for children under 3: small parts.")


if __name__ == "__main__":
    main()
