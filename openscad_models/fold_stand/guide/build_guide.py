#!/usr/bin/env python3
"""The Fold Stand's how-to guide, as a PDF (2026-11-05).

Scott: "Can you make instruction pdf with visuals on how to use the phone
stand". Every picture is a Blender render of the real exported parts
(render_guide.py), and every number is the .scad's or FOLD_STAND_PRINTING.md's.

    python3 render_guide.py && python3 build_guide.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
IMG = HERE / "images"
TMP = HERE.parent / "logs" / "guide"
OUT = HERE / "Fold_Stand_Guide.pdf"

pdfmetrics.registerFont(TTFont("Head", str(ROOT / "fonts" / "Fredoka-SemiBold.ttf")))
pdfmetrics.registerFont(TTFont("Body", str(ROOT / "assets" / "fonts" / "Poppins-Regular.ttf")))
pdfmetrics.registerFont(TTFont("BodyB", str(ROOT / "assets" / "fonts" / "Poppins-SemiBold.ttf")))
pdfmetrics.registerFont(TTFont("BodyI", str(ROOT / "assets" / "fonts" / "Poppins-Italic.ttf")))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyB", italic="BodyI", boldItalic="BodyB")

INK, MUTED, LINE, PANEL = HexColor("#22202B"), HexColor("#615C6E"), HexColor("#DEDAE6"), HexColor("#F4F2F8")
ACCENT = HexColor("#6E52B0")            # a deeper lilac than the print, so text on white reads
LILAC, WHITE_P, PINK = HexColor("#B79CE0"), HexColor("#E9E5DA"), HexColor("#F6A6C1")
WARN = HexColor("#B97A12")

W, H = letter
M = 46

BODY = ParagraphStyle("b", fontName="Body", fontSize=9.8, leading=14, textColor=INK)
SMALL = ParagraphStyle("s", parent=BODY, fontSize=8.4, leading=11.8, textColor=MUTED)
LEDE = ParagraphStyle("l", parent=BODY, fontSize=12, leading=17, textColor=MUTED)

STOPS = [(1, 81), (2, 75), (3, 69), (4, 63), (5, 57)]     # click, the phone's lean to the table


def para(c, text, x, y, w, style=BODY):
    """Draws text with its top at y; returns its height."""
    p = Paragraph(text, style)
    _, h = p.wrap(w, 1000)
    p.drawOn(c, x, y - h)
    return h


def _box(a, thresh=30):
    corner = np.median(np.concatenate([a[:20, :20].reshape(-1, 3), a[:20, -20:].reshape(-1, 3)]), axis=0)
    return np.abs(a - corner).sum(axis=2) > thresh


def crop(name, pad=0.04):
    """A render cropped to the parts and their shadow, contrast stretched for print."""
    im = Image.open(IMG / f"{name}.png").convert("RGB")
    ys, xs = np.nonzero(_box(np.asarray(im).astype(int)))
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    p = int(pad * max(x1 - x0, y1 - y0))
    box = (max(0, x0 - p), max(0, y0 - p), min(im.width, x1 + p), min(im.height, y1 + p))
    out = TMP / f"{name}_crop.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    # the studio renders come out pale; a full autocontrast turns the lilac blue-violet, so
    # stretch them only halfway
    im = im.crop(box)
    Image.blend(im, ImageOps.autocontrast(im, cutoff=0.3, preserve_tone=True), 0.5).save(out, quality=90)
    return out


def image_in(c, path, x, y, w, h, top=0, panel=True):
    """Fits an image inside the box (x, y bottom-left), centred, leaving `top`
    points clear above it. Returns where it landed: (x, y, w, h)."""
    if panel:
        c.setFillColor(PANEL)
        c.roundRect(x, y, w, h, 8, stroke=0, fill=1)
    r = ImageReader(str(path))
    iw, ih = r.getSize()
    s = min((w - 12) / iw, (h - top - 12) / ih)
    dw, dh = iw * s, ih * s
    dx, dy = x + (w - dw) / 2, y + (h - top - dh) / 2
    c.drawImage(r, dx, dy, dw, dh)
    return dx, dy, dw, dh


def footer(c, n):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(M, 34, W - M, 34)
    c.setFont("Body", 7.8)
    c.setFillColor(MUTED)
    c.drawString(M, 22, "Fold Stand  ·  OnBrandCraftz")
    c.drawRightString(W - M, 22, str(n))


def heading(c, text, y, size=24):
    c.setFillColor(INK)
    c.setFont("Head", size)
    c.drawString(M, y, text)


def step(c, n, text, x, y, w):
    c.setFillColor(ACCENT)
    c.circle(x + 9, y - 8, 9, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("BodyB", 9.4)
    c.drawCentredString(x + 9, y - 11.3, str(n))
    return max(18, para(c, text, x + 28, y - 1, w - 28))


def arrow(c, x0, x1, y):
    c.setStrokeColor(ACCENT)
    c.setFillColor(ACCENT)
    c.setLineWidth(3)
    c.line(x0, y, x1 - 8, y)
    p = c.beginPath()
    p.moveTo(x1, y)
    p.lineTo(x1 - 11, y + 7)
    p.lineTo(x1 - 11, y - 7)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def pair(c, left, right, y, h, caps):
    """Two pictures with an arrow between: before, then after. Top at y."""
    iw = (W - 2 * M - 40) / 2
    for x, name, (a, b) in ((M, left, caps[0]), (W - M - iw, right, caps[1])):
        image_in(c, crop(name), x, y - h, iw, h, top=34)
        c.setFont("BodyB", 9.2)
        c.setFillColor(ACCENT)
        c.drawString(x + 12, y - 18, a)
        c.setFont("Body", 8.2)
        c.setFillColor(MUTED)
        c.drawString(x + 12, y - 30, b)
    arrow(c, M + iw + 8, W - M - iw - 8, y - h / 2)
    return y - h


def dot_row(c, x, y, col, name, what):
    c.setFillColor(col)
    c.setStrokeColor(HexColor("#BDB6C9"))
    c.setLineWidth(0.6)
    c.circle(x + 5, y + 3.5, 5, stroke=1, fill=1)
    c.setFillColor(INK)
    c.setFont("BodyB", 9.8)
    c.drawString(x + 16, y, name)
    c.setFont("Body", 9.6)
    c.setFillColor(MUTED)
    c.drawString(x + 16 + pdfmetrics.stringWidth(name, "BodyB", 9.8) + 6, y, what)


# ---------------------------------------------------------------------------------------------
def cover(c):
    heading(c, "Fold Stand", H - 92, 42)
    para(c, "A phone stand that clicks to <b>five angles</b> and <b>folds flat</b> for your bag. "
            "Put it together once, then it's open, phone on, done.", M, H - 108, W - 2 * M - 40, LEDE)
    box_h = 372
    y = H - 160 - box_h
    image_in(c, crop("hero", 0.03), M, y, W - 2 * M, box_h)
    c.setFont("BodyI", 8)
    c.setFillColor(MUTED)
    c.drawCentredString(W / 2, y - 13, "Pictures in this guide are renders of the real parts, not photos. "
                                       "The colours just tell the parts apart: yours may all be one colour.")

    top = y - 44
    col_w = (W - 2 * M - 28) / 2
    heading(c, "In the bag", top, 15)
    yy = top - 22
    for col, name, what in ((LILAC, "Front plate", "the one with the lip"), (WHITE_P, "Back plate", "the leg"),
                            (PINK, "Two pins", "they hold the hinge together")):
        dot_row(c, M, yy, col, name, what)
        yy -= 18
    image_in(c, crop("parts"), M, 48, col_w, yy - 48 + 6)

    x2 = M + col_w + 28
    c.setFillColor(INK)
    c.setFont("Head", 15)
    c.drawString(x2, top, "At a glance")
    para(c, "• Five click-stops: the phone leans 81°, 75°, 69°, 63° or 57°.<br/>"
            "• Folded: 80 × 113 × 20 mm, and it clicks shut.<br/>"
            "• The lip takes a phone in a case up to about 10.5 mm thick.<br/>"
            "• A 14 mm slot in the lip for a charging lead.",
         x2, top - 12, col_w)
    footer(c, 1)


def assemble(c):
    pill_text = "Once only"
    tw = pdfmetrics.stringWidth(pill_text, "BodyB", 8.5)
    c.setFillColor(ACCENT)
    c.roundRect(M, H - 62, tw + 14, 16.5, 8, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("BodyB", 8.5)
    c.drawString(M + 7, H - 57.5, pill_text)
    heading(c, "Put it together", H - 94, 28)
    para(c, "Two steps, about a minute. After this the pins stay in: you never take it apart to use it.",
         M, H - 106, W - 2 * M, LEDE)

    y = H - 140
    y -= 8 + step(c, 1, "<b>Fold the back plate onto the front plate.</b> Lay the front plate down, lip side up. "
                   "Bring the back plate up under it, flat face to flat face, so the back plate's barrel "
                   "slots into the gap between the front plate's two barrels.", M, y, W - 2 * M)
    y = pair(c, "fold_apart", "fold_together", y - 4, 196,
             (("Line up", "the back plate's barrel under the gap"), ("Together", "three barrels in a row")))

    y -= 24
    y -= 8 + step(c, 2, "<b>Push a pin into each end of the hinge.</b> The hole is teardrop-shaped, and so is the "
                   "pin just under its head, so it only goes in one way: <b>point toward the lip side</b>. "
                   "Press it in until the head sits flat on the end of the barrel. Then the other end.",
             M, y, W - 2 * M)
    y = pair(c, "pin_apart", "pin_together", y - 4, 196,
             (("Line up", "teardrop point toward the lip side"), ("Pressed home", "head flat on the barrel")))

    y -= 16
    c.setFillColor(PANEL)
    c.roundRect(M, y - 50, W - 2 * M, 50, 8, stroke=0, fill=1)
    para(c, "<b>Won't start?</b> Turn the pin until its point lines up with the hole's point. It's a snug fit "
            "on purpose, so the pins don't fall out: press firmly and evenly.", M + 14, y - 10, W - 2 * M - 28)
    footer(c, 2)


def angles(c):
    heading(c, "Stand it up", H - 76, 28)
    para(c, "Stand it like an A, lip toward you. Pull the back leg away from the front plate: "
            "it clicks at each stop. <b>The more clicks, the further back your phone leans.</b>",
         M, H - 90, W - 2 * M, LEDE)

    # the five stops, one render, one scale: label each stand under its own feet
    path = crop("stops", 0.02)
    y_top = H - 150
    dx, dy, dw, dh = image_in(c, path, M, y_top - 210, W - 2 * M, 210)
    a = _box(np.asarray(Image.open(path).convert("RGB")).astype(int), 40)
    cols = a.any(axis=0)
    runs, start = [], None
    for i, on in enumerate(list(cols) + [False]):
        if on and start is None:
            start = i
        elif not on and start is not None:
            runs.append((start, i))
            start = None
    runs = sorted(sorted(runs, key=lambda r: r[1] - r[0])[-5:])
    iw = Image.open(path).width
    ly = y_top - 210 - 20
    for (r0, r1), (n, lean) in zip(runs, STOPS):
        cx = dx + (r0 + r1) / 2 / iw * dw
        c.setFillColor(ACCENT)
        c.setFont("Head", 17)
        c.drawCentredString(cx, ly, f"{lean}°")
        c.setFont("Body", 8.2)
        c.setFillColor(MUTED)
        c.drawCentredString(cx, ly - 13, f"click {n}")

    y = ly - 44
    heading(c, "Put your phone on", y, 15)
    y -= 12
    lw = W - 2 * M
    for i, s in enumerate([
        "Choose an angle: open the leg to that click.",
        "<b>Charging?</b> Thread the lead up through the slot in the middle of the lip first. "
        "The slot is 14 mm wide.",
        "Stand the phone in the lip, screen toward you, and let it lean back onto the hinge. "
        "It sits a little steeper than the front plate because it rests on the hinge.",
    ], 1):
        y -= step(c, i, s, M, y, lw) + 8

    y -= 8
    c.setFillColor(PANEL)
    h = 74
    c.roundRect(M, y - h, W - 2 * M, h, 8, stroke=0, fill=1)
    c.setFillColor(WARN)
    c.roundRect(M, y - h, 4, h, 2, stroke=0, fill=1)
    para(c, "<b>On a shiny surface, use the steeper clicks.</b> Standing up, an A is held mostly by the "
            "grip under its feet. The flatter it opens, the more grip it needs, so the two flattest clicks "
            "(63° and 57°) may slide open on glass or gloss. On wood, a mat or a desk pad they should "
            "be fine. There is no click past the fifth, so don't open it further.",
         M + 16, y - 10, W - 2 * M - 30)
    footer(c, 3)


def fold_and_help(c):
    heading(c, "Fold it away", H - 76, 28)
    para(c, "Lift the phone off and push the leg back against the front plate. It clicks shut, so it "
            "stays folded in a bag or a pocket: 80 × 113 × 20 mm.", M, H - 90, W - 2 * M - 10, LEDE)
    image_in(c, crop("folded"), M, H - 400, W - 2 * M, 270)

    y = H - 432
    heading(c, "If something's not right", y, 15)
    y -= 14
    items = [
        ("A pin came out.", "Push it back in, point toward the lip side. If it keeps working loose, put a small "
         "drop of glue in the end of the front plate's barrel only: the part of the pin past it turns inside the "
         "leg and has to stay free, or the clicks stop."),
        ("It slides open.", "Use a steeper click, or stand it on something with more grip than glass."),
        ("My phone won't fit in the lip.", "It takes a phone in a case up to about 10.5 mm thick. A thicker "
         "case won't sit in it."),
        ("The click is too weak or too stiff.", "Let us know. The click's strength is set by one number in the "
         "design, and it can be tuned."),
    ]
    for q, a in items:
        h = para(c, f"<b>{q}</b>  {a}", M, y, W - 2 * M)
        y -= h + 10

    y -= 6
    c.setFillColor(PANEL)
    c.roundRect(M, y - 44, W - 2 * M, 44, 8, stroke=0, fill=1)
    para(c, "<b>Keep it out of the heat.</b> It's printed in PLA, which softens in a hot car or on a sunny "
            "dashboard.", M + 14, y - 12, W - 2 * M - 28)
    footer(c, 4)


def main():
    c = canvas.Canvas(str(OUT), pagesize=letter)
    c.setTitle("Fold Stand: how to use it")
    c.setAuthor("OnBrandCraftz")
    c.setSubject("Putting together and using the Fold Stand phone stand")
    for page in (cover, assemble, angles, fold_and_help):
        page(c)
        c.showPage()
    c.save()
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
