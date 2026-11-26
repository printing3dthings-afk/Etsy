#!/usr/bin/env python3
"""Pie Drum Caddy v2 (the keeper): the PDF guide (2026-11-26), from renders of the real parts
(make_caddy_v2_images.py). Times and weights from checks_v2/slice_*.txt (Bambu Studio's slices).
The keeper thread was tested at 0.2 clearance (Scott, 2026-11-26: "Test piece was great").

    python3 make_caddy_v2_guide.py      (Pie_Drum_Caddy_v2_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Pie Drum Caddy v2", "A desk caddy in six rising slices that turns on a ring of BBs, "
             "with a keeper cup that holds it together when you pick it up.")
    a.step(1, "In the box", [
        "!The drum (150 mm across, six slices from 45 to 115 mm tall, a round well in the middle).",
        "!The keeper cup (cream here): a tall pen cup with a ridged collar on top and a thread inside its foot.",
        "The base (120 mm across), with a threaded post in the middle and a channel round its edge.",
        "46 airsoft BBs, 6 mm.",
    ], crop(IMG / "caddy_v2_exploded.png"), pic_h=560)
    a.step(2, "Printing it yourself", [
        "!pie_caddy_v2_drum: 8 h 41 min, 211 g. pie_caddy_v2_base: 1 h 47 min, 40 g. "
        "pie_caddy_v2_keeper: 56 min, 23 g.",
        "PLA Matte, 0.2 mm layers, no supports, as they come. The keeper prints standing up on a 3 mm brim: peel it off after.",
        "The drum prints on its smooth underside: that's the face the BBs run on, so keep the plate clean.",
    ])
    b = Card("Putting it together", "Design-review renders of the real parts, not photos.")
    b.step(1, "BBs into the channel", [
        "!Set the base on a flat table and pour the 46 BBs into the channel round its edge. The small gap left in the ring is on purpose, so they can't jam.",
    ])
    b.step(2, "The drum on top", [
        "!Lower the drum straight down over the post until it settles onto the BBs.",
    ])
    b.step(3, "Screw the keeper in", [
        "!Drop the keeper cup into the drum's middle well and turn it clockwise by its collar.",
        "About three turns. It stops firmly by itself: don't force it past the stop.",
    ], crop(IMG / "caddy_v2_keeper_in.png"), pic_h=480)
    b.step(4, "What the keeper does", [
        "!It screws onto the post and stops just above a ledge inside the drum: 0.5 mm clear. The drum still spins freely, but it can't lift off.",
        "Pick the caddy up by the collar or the drum and it comes up in one piece.",
    ], crop(IMG / "caddy_v2_section.png"), pic_h=480)
    c = Card("Using it", "Holds up to about 1 kg of pens, scissors, rulers and tape.")
    c.step(1, "Spin it", ["!A flick of a fingertip turns it. The keeper stays still in the middle: it's a pen cup too."],
           crop(IMG / "caddy_v2_views_three_quarter.png"), pic_h=460)
    c.step(2, "Cleaning", ["!Unscrew the keeper (anticlockwise), then lift the drum off. The BBs stay in their channel unless you tip the base."])
    c.box("Good", ["It turns with a flick and coasts.", "Quiet: no grinding.",
                   "Lifted by the collar, the drum and base come up together."], GOOD)
    c.box("If not", ["It grinds or catches: check for a BB out of the channel, or dust in it.",
                     "The keeper won't reach its stop: check the post's thread for a string of plastic, and run it on and off once.",
                     "Keep the BBs for the base: 6 mm airsoft BBs, any brand."], BAD)
    save_pdf([a, b, c], HERE / "Pie_Drum_Caddy_v2_Guide.pdf",
             note="Design-review renders of the real parts, not photos. Not for children under 3: small parts (the BBs).")


if __name__ == "__main__":
    main()
