#!/usr/bin/env python3
"""The Fold Stand v3 test-print guide: two phone-sized cards (2026-11-10).
Scott printed the coupon and asked "How do I put it together? Can you give me a visual
to how to test it?". Card 1 puts it together, card 2 tests it. Every picture is a
render of the real coupon parts (render_coupon_guide.py).

    python3 render_coupon_guide.py && python3 build_coupon_guide.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
IMG = HERE / "images"
FONTS = HERE.parents[3] / "assets" / "fonts"
W = 1080
INK, MUTED, ACCENT, PANEL, LINE = (34, 32, 43), (97, 92, 110), (110, 82, 176), (244, 242, 248), (222, 218, 230)
GOOD, BAD = (46, 125, 80), (176, 64, 64)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


H1, H2, BODY, BODYB, SMALL = (font("Nunito-Black.ttf", 64), font("Nunito-ExtraBold.ttf", 40),
                              font("Poppins-Regular.ttf", 30), font("Poppins-SemiBold.ttf", 30),
                              font("Poppins-Regular.ttf", 24))


def wrap(d, text, f, width):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


def crop(path, pad=30):
    """Trim the studio background to the subject, plus a margin."""
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    bg = a[5, 5]
    mask = np.abs(a - bg).sum(axis=2) > 40
    ys, xs = np.where(mask)
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, im.width), min(ys.max() + pad, im.height))
    return im.crop(box)


def fit(im, w, h):
    return ImageOps.contain(im, (w, h), Image.LANCZOS)


class Card:
    def __init__(self, title, sub):
        self.im = Image.new("RGB", (W, 6000), "white")
        self.d = ImageDraw.Draw(self.im)
        self.y = 60
        self.d.text((60, self.y), title, font=H1, fill=ACCENT)
        self.y += 84
        for line in wrap(self.d, sub, BODY, W - 120):
            self.d.text((60, self.y), line, font=BODY, fill=MUTED)
            self.y += 42
        self.y += 20

    def step(self, num, head, lines, pic=None, pic_h=520):
        d = self.d
        d.ellipse((60, self.y, 124, self.y + 64), fill=ACCENT)
        tw = d.textlength(str(num), font=H2)
        d.text((92 - tw / 2, self.y + 6), str(num), font=H2, fill="white")
        d.text((150, self.y + 6), head, font=H2, fill=INK)
        self.y += 84
        if pic is not None:
            p = fit(pic, W - 120, pic_h)
            self.im.paste(p, ((W - p.width) // 2, self.y))
            self.y += p.height + 20
        for item in lines:
            bold = item.startswith("!")
            text = item.lstrip("!")
            for i, line in enumerate(wrap(d, text, BODYB if bold else BODY, W - 170)):
                if i == 0:
                    d.ellipse((92, self.y + 16, 102, self.y + 26), fill=ACCENT)
                d.text((120, self.y), line, font=BODYB if bold else BODY, fill=INK)
                self.y += 42
        self.y += 36

    def box(self, head, lines, colour):
        d = self.d
        top = self.y
        y = top + 24
        rows = []
        for item in lines:
            rows.append(wrap(d, item, BODY, W - 220))
        hgt = 24 + 56 + sum(42 * len(r) for r in rows) + 24
        d.rounded_rectangle((60, top, W - 60, top + hgt), radius=24, fill=PANEL, outline=colour, width=4)
        d.text((90, y), head, font=H2, fill=colour)
        y += 56
        for r in rows:
            for i, line in enumerate(r):
                if i == 0:
                    d.ellipse((96, y + 16, 106, y + 26), fill=colour)
                d.text((124, y), line, font=BODY, fill=INK)
                y += 42
        self.y = top + hgt + 36

    def save(self, path):
        self.d.text((60, self.y), "Design-review renders of the real test-print parts, not photos. "
                    "Colours are only to tell the parts apart.", font=SMALL, fill=MUTED)
        self.im.crop((0, 0, W, self.y + 70)).save(path, quality=92)


def main():
    c = Card("Fold Stand v3: put the test piece together",
             "Three pieces, no pins, nothing to force. Every part just drops into place.")
    c.step(1, "The three pieces", [
        "!Base (white here): a round groove at one end, six round notches along the middle.",
        "!Plate (purple), shown upside down: the phone shelf is at one end, the pocket on its back.",
        "!Prop (pink): one end thick (the foot), one end thin (the top).",
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
    c.save(IMG / "Fold_Stand_v3_Test_1_Assemble.jpg")

    t = Card("Fold Stand v3: test it", "Six notches, six angles. Try each one with your phone on it.")
    strip = Image.new("RGB", (W - 120, 900), "white")
    sd = ImageDraw.Draw(strip)
    cw, ch = (W - 120) // 3, 450
    for i, th in enumerate([80, 75, 70, 65, 60, 55]):
        p = fit(crop(IMG / f"angle_{th}.png", 10), cw - 20, ch - 60)
        x, y = (i % 3) * cw, (i // 3) * ch
        strip.paste(p, (x + (cw - p.width) // 2, y + (ch - 60 - p.height)))
        lab = f"notch {i + 1}: {th} deg"
        sd.text((x + (cw - sd.textlength(lab, font=BODYB)) / 2, y + ch - 52), lab, font=BODYB, fill=INK)
    t.step(1, "Each notch, with your phone on", [
        "!Tap the screen like normal: the angle must not change.",
        "Lift the phone, move the prop to the next notch, put the phone back. It should be easy.",
        "It is only 30 mm wide, so it can rock side to side; the real stand is 76 wide. "
        "What matters is that the angle holds.",
    ], strip, pic_h=900)
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
    t.save(IMG / "Fold_Stand_v3_Test_2_Test.jpg")


if __name__ == "__main__":
    main()
