#!/usr/bin/env python3
"""The Fold Stand v3 test-print guide: two phone-sized cards (2026-11-10).
Scott printed the coupon and asked "How do I put it together? Can you give me a visual
to how to test it?". Card 1 puts it together, card 2 tests it. Every picture is a
render of the real coupon parts (render_coupon_guide.py).

    python3 render_coupon_guide.py && python3 build_coupon_guide.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
IMG = HERE / "images"
NOTE = "Design-review renders of the real test-print parts, not photos. Colours are only to tell the parts apart."
sys.path.insert(0, str(HERE.parents[3] / "tools"))
from guide_cards import BAD, BODYB, GOOD, INK, W, Card, crop, fit, save_pdf  # noqa: E402


def main():
    c = Card("Fold Stand v3: put the test piece together",
             "Three pieces, no pins, nothing to force. Every part just drops into place.")
    c.step(1, "The three pieces", [
        "!Base (white here): a round groove at one end, six round notches along the middle.",
        "!Plate (purple), shown upside down: the phone shelf is at one end, the pocket on its back.",
        "!Prop (pink): one end thick (the foot), one end thin (the top).",
        "The big open windows in the base and the plate only save plastic on this test piece. "
        "The pocket is the small one near the plate's end.",
    ], crop(IMG / "parts.png"))
    c.step(2, "Drop the plate into the groove", [
        "Groove nearest you, notches running away from you.",
        "The plate's round bottom edge (beside the shelf) goes in the groove, shelf facing you.",
        "!Tip it back and forth: it should rock freely, not bind and not flop out.",
    ], crop(IMG / "step1_plate.png"))
    c.step(3, "Put the prop in", [
        "Lean the plate back. Push the prop's thin end up into the pocket on the plate's back.",
        "Drop the thick end into a notch. Seen here from behind.",
        "!Nearest notch = steepest (80 deg). Each notch further back lays it 5 deg flatter, to 55.",
    ], crop(IMG / "step2_prop.png"))
    c.step(4, "Stand your phone on the shelf", [
        "Its bottom edge on the shelf, its back against the plate.",
    ], crop(IMG / "step3_phone.png"))
    c.save(IMG / "Fold_Stand_v3_Test_1_Assemble.jpg", NOTE)

    t = Card("Fold Stand v3: test it", "Six notches, six angles. Try each one with your phone on it.")
    cw = (W - 120) // 3
    pics = [fit(crop(IMG / f"angle_{th}.png", 10), cw - 20, 400) for th in (80, 75, 70, 65, 60, 55)]
    ph = max(p.height for p in pics)
    ch = ph + 70
    strip = Image.new("RGB", (W - 120, 2 * ch), "white")
    sd = ImageDraw.Draw(strip)
    for i, (th, p) in enumerate(zip((80, 75, 70, 65, 60, 55), pics)):
        x, y = (i % 3) * cw, (i // 3) * ch
        strip.paste(p, (x + (cw - p.width) // 2, y + (ph - p.height)))
        lab = f"notch {i + 1}: {th} deg"
        sd.text((x + (cw - sd.textlength(lab, font=BODYB)) / 2, y + ch - 52), lab, font=BODYB, fill=INK)
    t.step(1, "Each notch, with your phone on", [
        "!Tap the screen like normal: the angle must not change.",
        "Lift the phone, move the prop to the next notch, put the phone back. It should be easy.",
        "It is only 30 mm wide, so it can rock side to side; the real stand is 76 wide. "
        "What matters is that the angle holds.",
    ], strip, pic_h=2 * ch)
    t.box("Good", [
        "The plate drops into the groove and rocks freely.",
        "The thin end sits snug up in the top of the pocket.",
        "The thick end drops into each notch and stays there.",
        "No angle slips when you tap the screen.",
    ], GOOD)
    t.box("Tell me if", [
        "the plate binds in the groove, or is sloppy there;",
        "the thin end won't stay up in the pocket;",
        "the thick end rides out of a notch, or sits between two;",
        "any angle slips under a normal tap, or the stand slides on your desk.",
    ], BAD)
    t.save(IMG / "Fold_Stand_v3_Test_2_Test.jpg", NOTE)
    save_pdf([c, t], HERE / "Fold_Stand_v3_Test_Guide.pdf")


if __name__ == "__main__":
    main()
