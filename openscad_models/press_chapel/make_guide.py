#!/usr/bin/env python3
"""Press-to-Light Chapel drop test print: the PDF guide (2026-11-17), from renders of the
real parts. Time and weight from checks/slice.json (Bambu Studio's slice).

    python3 make_guide.py      (Chapel_Drop_Test_Guide.pdf)
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
    g = s["filament_g"]
    a = Card("Chapel drop test: printing and what's in it",
             "Lift the steeple, let go: its weight should spin the hub. No spring.")
    h = json.loads((HERE / "checks" / "slice_hubs.json").read_text())
    a.step(1, "Print the plate", [
        f"!drop_coupon.gcode.3mf: PLA Matte, 0.2 mm layers, supports off. About {s['time']} and {g} g.",
        "Five parts: the base, the arch, the shaft (with a brim), the steeple (printed solid: it's the weight) and one hub (2 notches in its flag, 0.4 mm).",
        f"Only if that hub binds or rattles: drop_coupon_hubs.gcode.3mf, a looser and a tighter one (1 and 3 notches), about {h['time']}.",
    ], crop(IMG / "drop_section.png"), pic_h=380)
    a.step(2, "Put it together", [
        "!Push the shaft's square end up through the arch's diamond hole from underneath, until its collar stops it. The twisted part hangs below.",
        "Set the hub on the base's point. Lower the arch onto the base, the twisted end going into the hub: the hub turns as it goes in.",
        "Press the arch's two feet into the base's sockets, then press the steeple onto the square end on top.",
    ], crop(IMG / "drop_rest.png"), pic_h=380)
    b = Card("Chapel drop test: trying it", "Design-review renders of the real parts, not photos.")
    b.step(3, "Lift and let go", [
        "!Lift the steeple until it stops. Let go: it drops, and the hub should spin and keep spinning after it lands.",
        "Count the hub's turns from letting go to stopping (the flag's windows make them easy to see).",
        "Do it about 50 times. To swap hubs, lift the arch off the base (step 2 backwards).",
    ], crop(IMG / "drop_lifted.png"), pic_h=420)
    b.box("Good", ["Let go, and the steeple drops by itself without a push.",
                   "The hub turns at least once, and runs on after the steeple lands.",
                   "Lifting always finds its way back in; nothing catches or wears."], GOOD)
    b.box("Tell me (for each hub you tried)", [
        "whether it drops by itself, and about how many turns in all,",
        "whether the lift ever catches or the hub sticks part-way,",
        "and any white marks or wear on the twisted part after 50 goes."], BAD)
    save_pdf([a, b], HERE / "Chapel_Drop_Test_Guide.pdf",
             note="Design-review renders of the real parts, not photos. Battery LED tea lights only in the chapel itself.")


if __name__ == "__main__":
    main()
