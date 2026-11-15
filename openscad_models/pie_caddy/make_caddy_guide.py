#!/usr/bin/env python3
"""Pie Drum Caddy: the PDF guide (2026-11-15), from renders of the real parts.
Times and weights from checks/slice_drum.txt and slice_base.txt (Bambu Studio's slices).

    python3 make_caddy_guide.py      (Pie_Drum_Caddy_Guide.pdf)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def main():
    a = Card("Pie Drum Caddy", "A desk caddy in six rising slices that turns on a ring of BBs.")
    a.step(1, "In the box", [
        "!The drum (150 mm across, six slices from 45 to 115 mm tall, a round well in the middle).",
        "The base (120 mm across), with a post in the middle and a channel round its edge.",
        "46 airsoft BBs, 6 mm.",
    ], crop(IMG / "caddy_exploded.png"), pic_h=560)
    a.step(2, "Printing it yourself", [
        "!pie_caddy_drum.gcode.3mf: 8 h 42 min, 206 g. pie_caddy_base.gcode.3mf: 1 h 36 min, 36 g.",
        "PLA Matte, 0.2 mm layers, no supports, as they come. The base irons its top so the BBs roll on a smooth floor.",
        "The drum prints on its smooth underside: that's the face the BBs run on, so keep the plate clean.",
    ])
    b = Card("Putting it together", "Design-review renders of the real parts, not photos.")
    b.step(1, "BBs into the channel", [
        "!Set the base on a flat table and pour the 46 BBs into the channel round its edge. They leave a small gap in the ring: that's on purpose, so they can't jam.",
    ], crop(IMG / "caddy_base_balls.png"), pic_h=460)
    b.step(2, "The drum on top", [
        "!Lower the drum straight down over the post. The post finds the hole under the drum's middle, and the drum settles onto the BBs.",
        "Nothing locks it on. It lifts straight off.",
    ])
    b.step(3, "Use it", [
        "!Spin it with a fingertip. It holds up to about 1 kg of pens, scissors, rulers and tape.",
    ], crop(IMG / "caddy_views_front.png"), pic_h=480)
    b.step(4, "Cleaning", [
        "!Lift the drum off. The BBs stay in their channel unless you tip the base.",
    ])
    b.box("Good", ["It turns with a flick and coasts.", "Quiet: no grinding.", "No wobble as it turns."], GOOD)
    b.box("If not", ["It grinds or catches: check for a BB out of the channel, or dust in it.",
                     "Keep the BBs for the base: 6 mm airsoft BBs, any brand."], BAD)
    save_pdf([a, b], HERE / "Pie_Drum_Caddy_Guide.pdf",
             note="Design-review renders of the real parts, not photos. Not for children under 3: small parts (the BBs).")


if __name__ == "__main__":
    main()
