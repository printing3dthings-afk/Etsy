#!/usr/bin/env python3
"""Phone-shaped instruction cards, and a PDF of them (2026-11-10).

Scott: "Any print that has moving parts or parts that need assembled, create a pdf for
it." Every such print gets a guide: what is in the box, putting it together, using it,
testing it, what to report. Each card is a numbered list of steps, a picture per step
(a render of the real exported parts), and boxed "good" / "tell me if" lists. First used
for the Fold Stand v3 test piece (openscad_models/fold_stand/v3/guide/).

    from guide_cards import Card, crop, save_pdf, GOOD, BAD
    c = Card("Title", "one line under it")
    c.step(1, "Head", ["a line", "!a bold line"], crop("render.png"))
    c.box("Good", ["..."], GOOD)
    save_pdf([c, ...], "Guide.pdf")
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

FONTS = Path(__file__).resolve().parents[1] / "assets" / "fonts"
NOTE = "Design-review renders of the real parts, not photos. Colours are only to tell the parts apart."
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
    im = im.crop(box)
    # the studio renders come out grey; lift them halfway to full contrast (as the v1 guide)
    return Image.blend(im, ImageOps.autocontrast(im, cutoff=1), 0.5)


def fit(im, w, h):
    return ImageOps.contain(im, (w, h), Image.LANCZOS)


class Card:
    def __init__(self, title, sub):
        self.im = Image.new("RGB", (W, 6000), "white")
        self.d = ImageDraw.Draw(self.im)
        self.y = 60
        for line in wrap(self.d, title, H1, W - 120):
            self.d.text((60, self.y), line, font=H1, fill=ACCENT)
            self.y += 78
        self.y += 6
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

    def page(self, note=NOTE):
        """The finished card as an image (the footnote under it)."""
        for line in wrap(self.d, note, SMALL, W - 120):
            self.d.text((60, self.y), line, font=SMALL, fill=MUTED)
            self.y += 34
        self.done = self.im.crop((0, 0, W, self.y + 40))
        return self.done

    def save(self, path, note=NOTE):
        self.page(note).save(path, quality=92)


def save_pdf(cards, path, note=NOTE):
    """Every card one page of a PDF, phone-shaped, in order. 150 dpi: a 1080 wide card is
    7.2 in across, so the text reads on a phone and prints on letter at about full width."""
    pages = [c.done if getattr(c, "done", None) is not None else c.page(note) for c in cards]
    pages = [p.convert("RGB") for p in pages]
    pages[0].save(path, save_all=True, append_images=pages[1:], resolution=150.0)


