#!/usr/bin/env python3
"""Gear Heart v2: the PDF guide (2026-11-16), from renders of the real exported parts
(images/heart_v2_*.png). Times and grams from the Bambu Studio slices
(checks/slice_heart_*_v2.json).

    python3 make_heart_v2_guide.py      (Gear_Heart_v2_Guide.pdf)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from guide_cards import BAD, GOOD, Card, crop, save_pdf  # noqa: E402

IMG = HERE / "images"


def sliced(name):
    d = json.loads((HERE / "checks" / f"slice_heart_{name}_v2.json").read_text())
    return d["time"], d["filament_g"]


def main():
    tp, gp = sliced("plate")
    tg, gg = sliced("gears")
    a = Card("Gear Heart v2: printing", "Two prints: the heart plate, and fifteen gears with fifteen axle pins.")
    a.step(1, "Print the plate", [
        f"!gear_heart_plate_v2.3mf, flat, supports off. About {tp} and {gp} g.",
        "Fifteen round bosses, each with a hole through it and a slot for a pin's head underneath.",
    ], crop(IMG / "heart_v2_plate.png"), pic_h=400)
    a.step(2, "Print the gears and pins", [
        f"!gear_heart_gears_v2.3mf, flat, supports off. About {tg} and {gg} g.",
        "Fifteen gears, and fifteen pins lying on their sides. Each pin has a flat head and two springy prongs.",
        "These are the clip-3 pins from your clip test (the 0.65 mm hooks).",
    ], crop(IMG / "heart_v2_gears_plate.png"), pic_h=400)
    b = Card("Gear Heart v2: putting it together", "Design-review renders of the real parts, not photos.")
    b.step(3, "One gear at a time, in this order", [
        "!The heart-hole gear goes on the boss in the top dip. The knob gear goes in the middle.",
        "Then work down both sides from the top: a 16-tooth gear, then a 12, then a 16, and so on.",
        "The 16-tooth gear at the bottom point goes on last. Its teeth line up with both sides.",
    ], crop(IMG / "heart_v2_top.png"), pic_h=400)
    b.step(4, "Pin each gear from underneath", [
        "!Set the gear on its boss, its teeth slipped into its neighbour's.",
        "Hold the plate up, push a pin up through the hole from underneath, prongs first, through the boss and the gear.",
        "Turn the pin's head to line up with its slot and press until the hooks click over the gear's top.",
        "The head sits in its slot under the plate, so the pin can't turn: the gear turns on it.",
    ], crop(IMG / "heart_v2_underside.png"), pic_h=400)
    c = Card("Gear Heart v2: turning it, and what to check", "")
    c.step(5, "Turn the knob", [
        "!Every gear turns together, each the opposite way to its neighbours.",
        "To take a gear off for a repair, pinch the two hooks together above the gear and push the pin down.",
    ], crop(IMG / "heart_v2_three_quarter.png"), pic_h=440)
    c.box("Good", ["All fifteen gears turn smoothly from the knob.",
                   "No gear lifts off as it turns; no pin comes loose.",
                   "No white marks at the root of any pin's prongs."], GOOD)
    c.box("Tell me", ["whether every pin clicked in and stayed,",
                      "whether anything whitened or cracked,",
                      "and whether the knob turns the whole ring smoothly."], BAD)
    save_pdf([a, b, c], HERE / "Gear_Heart_v2_Guide.pdf",
             note="Design-review renders of the real parts, not photos. The colours are only for the pictures.")


if __name__ == "__main__":
    main()
