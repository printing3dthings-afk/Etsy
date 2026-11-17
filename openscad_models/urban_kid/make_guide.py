#!/usr/bin/env python3
"""Urban Kid: the PDF guide (2026-11-17), printing and putting him together,
from renders of the real exported parts. Times and weights from
checks/slices.json (Bambu Studio's own slices).

    python3 make_guide.py      (Urban_Kid_Guide.pdf)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"
PLATES = [("skin", "skin_head", "the head"), ("red", "red_hoodie", "the hoodie"),
          ("charcoal", "charcoal_pants", "the cargo pants"), ("white", "white_sneakers", "both sneakers"),
          ("black", "black_cap_base_pin", "the cap, the base and the cap's pin"),
          ("gold", "gold_chain", "the chain and nameplate")]


def main():
    s = json.loads((HERE / "checks" / "slices.json").read_text())
    mins = sum(int(t.split("h")[0]) * 60 + int(t.split("h")[1].split("m")[0]) if "h" in t
               else int(t.split("m")[0]) for t in (v["time"] for v in s.values()))
    grams = sum(float(v["filament_g"]) for v in s.values())
    a = Card("Urban Kid: printing", "Seven prints in six colours, one plate per colour: no AMS needed.")
    a.step(1, "Print the six plates", [
        f"!PLA, 0.12 mm layers, supports off. About {mins // 60} h {mins % 60} min and {grams:.0f} g in all.",
        *[f"urban_kid_{f}.gcode.3mf: {what}, about {s[c]['time']} and {float(s[c]['filament_g']):.1f} g."
          for c, f, what in PLATES],
        "Nothing to clean up: every print comes off the plate as it is.",
    ], crop(IMG / "kid_plate.png"), pic_h=420)
    b = Card("Urban Kid: putting him together", "Design-review renders of the real parts, not photos.")
    b.step(2, "Stack him up from the base", [
        "!Every joint is a peg in a socket: push each part down until it seats. A drop of glue in each socket keeps him together for good.",
        "Sneakers onto the base's two pegs, toes to the front. Pants onto the sneakers' pegs. Hoodie onto the pants' two pegs.",
        "Head onto the hoodie's neck peg. It turns on it, so you can set where he's looking before you glue it, or leave it loose.",
        "The black pin: flat side to the flat side of the head's top socket. Then the cap on top, worn backwards: brim at the back.",
        "Chain: a thin line of glue on its back, the nameplate centred on his flat chest, the chain's ends just under the hood.",
    ], crop(IMG / "kid_exploded.png"), pic_h=560)
    c = Card("Urban Kid: the finished figure", "Design-review render of the real parts, not a photo.")
    c.step(3, "Check him over", [
        "!He stands about 117 mm tall on a 56 mm base.",
        "Look along each joint: the hem covers the waist, the cuffs cover the sneakers' tops, the cap's band covers its joint.",
    ], crop(IMG / "kid_front.png"), pic_h=560)
    c.box("Good", ["Each part pushes on by hand and stays.",
                   "He stands straight, nothing rocks on the base.",
                   "The nameplate reads OBC and lies flat."], GOOD)
    c.box("Tell me (test print)", [
        "any joint too tight to push on, or loose enough to fall off,",
        "whether the cap's pin fits both sockets,",
        "and any print that came off rough: which part, and where."], BAD)
    save_pdf([a, b, c], HERE / "Urban_Kid_Guide.pdf",
             note="Design-review renders of the real parts, not photos.")


if __name__ == "__main__":
    main()
