#!/usr/bin/env python3
"""The fit test plate's instruction guide, as a PDF for MakerWorld (2026-10-30).

Scott: "Make a pdf for the test plate ... showing visual instructions on how to
test everything. I want to upload that to makers world."

Every picture is real: the cover is Scott's own print off his P1S, and the
mechanism pictures are Blender renders of the exported parts, apart and put
together the way check_fits.py checks them (render_guide.py). Every number
is the .scad's.

    python3 render_guide.py && python3 build_guide.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
IMG = HERE / "images"
OUT = HERE / "Fit_Test_Plate_Guide.pdf"
PHOTO = HERE.parent / "images" / "printed_plate_2026-10-29.jpg"

pdfmetrics.registerFont(TTFont("Head", str(ROOT / "fonts" / "Fredoka-SemiBold.ttf")))
pdfmetrics.registerFont(TTFont("Body", str(ROOT / "assets" / "fonts" / "Poppins-Regular.ttf")))
pdfmetrics.registerFont(TTFont("BodyB", str(ROOT / "assets" / "fonts" / "Poppins-SemiBold.ttf")))
pdfmetrics.registerFont(TTFont("BodyI", str(ROOT / "assets" / "fonts" / "Poppins-Italic.ttf")))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyB", italic="BodyI", boldItalic="BodyB")

INK, MUTED, LINE, PANEL = HexColor("#20242C"), HexColor("#5E6573"), HexColor("#DCE0E5"), HexColor("#F3F5F7")
TIGHT, GOOD, LOOSE = HexColor("#B97A12"), HexColor("#2F8A57"), HexColor("#3B6CB0")
MECH = {   # the colours of the plate key render (render_guide.py's KEY)
    "thread": HexColor("#5C8FD6"), "ball": HexColor("#ED7869"), "gears": HexColor("#E0A93A"),
    "detent": HexColor("#66B380"), "bayonet": HexColor("#9E80D1")}

W, H = letter
M = 46                                  # page margin, points

BODY = ParagraphStyle("b", fontName="Body", fontSize=9.6, leading=13.6, textColor=INK, alignment=TA_LEFT)
SMALL = ParagraphStyle("s", parent=BODY, fontSize=8.4, leading=11.6, textColor=MUTED)
STEP = ParagraphStyle("st", parent=BODY, leftIndent=0)
LEDE = ParagraphStyle("l", parent=BODY, fontSize=11.5, leading=16, textColor=MUTED)


def para(c, text, x, y, w, style=BODY):
    """Draws text with its top at y; returns its height."""
    p = Paragraph(text, style)
    _, h = p.wrap(w, 1000)
    p.drawOn(c, x, y - h)
    return h


def crop(path, pad=0.04):
    """A render cropped to the parts and their shadow, as a JPEG reader."""
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    corner = np.median(np.concatenate([a[:20, :20].reshape(-1, 3), a[:20, -20:].reshape(-1, 3)]), axis=0)
    diff = np.abs(a - corner).sum(axis=2)
    ys, xs = np.nonzero(diff > 30)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    p = int(pad * max(x1 - x0, y1 - y0))
    box = (max(0, x0 - p), max(0, y0 - p), min(im.width, x1 + p), min(im.height, y1 + p))
    out = HERE.parent / "logs" / "guide" / (Path(path).stem + "_crop.jpg")
    out.parent.mkdir(parents=True, exist_ok=True)
    # the studio renders come out pale; stretch them to full range for print
    ImageOps.autocontrast(im.crop(box), cutoff=0.4, preserve_tone=True).save(out, quality=90)
    return out


def image_in(c, path, x, y, w, h, round_=8, top=0):
    """Fits an image inside the box (x, y bottom-left), centred, on a panel,
    leaving `top` points clear above it for a caption."""
    c.setFillColor(PANEL)
    c.roundRect(x, y, w, h, round_, stroke=0, fill=1)
    r = ImageReader(str(path))
    iw, ih = r.getSize()
    s = min((w - 12) / iw, (h - top - 12) / ih)
    dw, dh = iw * s, ih * s
    c.drawImage(r, x + (w - dw) / 2, y + (h - top - dh) / 2, dw, dh)


def pill(c, x, y, text, col, size=8.5, fg=white):
    tw = pdfmetrics.stringWidth(text, "BodyB", size)
    c.setFillColor(col)
    c.roundRect(x, y - 4, tw + 14, size + 8, (size + 8) / 2, stroke=0, fill=1)
    c.setFillColor(fg)
    c.setFont("BodyB", size)
    c.drawString(x + 7, y + 0.5, text)
    return tw + 14


def footer(c, n):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(M, 34, W - M, 34)
    c.setFont("Body", 7.8)
    c.setFillColor(MUTED)
    c.drawString(M, 22, "Fit Test Plate  ·  OnBrandCraftz")
    c.drawRightString(W - M, 22, str(n))


def arrow(c, x0, x1, y, col):
    c.setStrokeColor(col)
    c.setFillColor(col)
    c.setLineWidth(3)
    c.line(x0, y, x1 - 8, y)
    p = c.beginPath()
    p.moveTo(x1, y)
    p.lineTo(x1 - 11, y + 7)
    p.lineTo(x1 - 11, y - 7)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


# ---------------------------------------------------------------------------------------------
def cover(c):
    c.setFillColor(INK)
    c.setFont("Head", 40)
    c.drawString(M, H - 92, "Fit Test Plate")
    para(c, "Find the clearances that work on <b>your</b> printer, with <b>your</b> filament, in one print. "
            "Five mechanisms, each printed at three clearances. Put each pair together, feel which one is "
            "right, and use that number in everything you design.", M, H - 108, W - 2 * M - 10, LEDE)
    # the real print, cropped to the plate
    ph = Image.open(PHOTO).convert("RGB")
    ph = ph.crop((0, int(ph.height * 0.235), ph.width, int(ph.height * 0.985)))
    tmp = HERE.parent / "logs" / "guide" / "cover_photo.jpg"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    ph.save(tmp, quality=88)
    box_w = W - 2 * M
    box_h = 360
    y = H - 196 - box_h
    r = ImageReader(str(tmp))
    iw, ih = r.getSize()
    s = min(box_w / iw, box_h / ih)
    c.drawImage(r, M + (box_w - iw * s) / 2, y + (box_h - ih * s) / 2, iw * s, ih * s)
    c.setFont("BodyI", 8.2)
    c.setFillColor(MUTED)
    c.drawCentredString(W / 2, y - 13, "A real print of this plate, straight off a Bambu Lab P1S: 33 parts, no supports.")

    # what's on it
    top = y - 40
    col_w = (W - 2 * M - 24) / 2
    c.setFillColor(INK)
    c.setFont("Head", 15)
    c.drawString(M, top, "Five mechanisms")
    rows = [("thread", "Thread", "24 mm screw and nut, pitch 3"), ("ball", "Ball joint", "8 mm ball, snap-in socket"),
            ("gears", "Gears", "module 1.5, 20 and 10 teeth"), ("detent", "Detent", "12-click wheel on a spring arm"),
            ("bayonet", "Bayonet", "twist-lock cap and ring")]
    yy = top - 22
    for k, name, what in rows:
        c.setFillColor(MECH[k])
        c.circle(M + 5, yy + 3.5, 5, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont("BodyB", 9.6)
        c.drawString(M + 16, yy, name)
        c.setFont("Body", 9.6)
        c.setFillColor(MUTED)
        c.drawString(M + 16 + pdfmetrics.stringWidth(name, "BodyB", 9.6) + 6, yy, what)
        yy -= 17

    x2 = M + col_w + 24
    c.setFillColor(INK)
    c.setFont("Head", 15)
    c.drawString(x2, top, "Print it like this")
    settings = ("• PLA you'll use for real parts. One colour is fine.<br/>"
                "• 0.20 mm layers, 0.4 mm nozzle, default 2 walls.<br/>"
                "• <b>Supports off.</b> None of the 33 parts needs any.<br/>"
                "• <b>Don't scale it.</b> The clearances are real millimetres.<br/>"
                "• Sliced estimate: about 3 h 40 min and 93 g. 16 mm tall.")
    para(c, settings, x2, top - 12, col_w, BODY)
    footer(c, 1)


def overview(c):
    c.setFillColor(INK)
    c.setFont("Head", 24)
    c.drawString(M, H - 76, "What's on the plate")
    lh = para(c, "Each colour below is one mechanism: three pairs, one at each clearance. In every pair "
                 "<b>one part changes and the other is the same in all three</b>. The part that changes carries "
                 "its clearance, engraved on a little tab or in its base. Some fixed parts carry a matching "
                 "label too, just to keep pairs together.", M, H - 90, W - 2 * M, LEDE)
    key = crop(IMG / "plate_key.png", 0.02)
    image_in(c, key, M, H - 462, W - 2 * M, 362 - lh - 12)

    # the key's table
    y = H - 476
    cols = [M, M + 88, M + 240, M + 352]
    c.setFont("BodyB", 8.4)
    c.setFillColor(MUTED)
    for x, t in zip(cols, ["Mechanism", "The part that changes", "Its labels", "What the number means"]):
        c.drawString(x, y, t)
    rows = [("thread", "Thread", "the octagonal nut", "0.2 · 0.3 · 0.4", "gap all round the thread"),
            ("ball", "Ball joint", "the split socket", "0.4 · 0.6 · 0.8", "mouth this much under the ball"),
            ("gears", "Gears", "the pear-shaped base", "+0 · +0.15 · +0.3", "extra gap between gear centres"),
            ("detent", "Detent", "the square base", "0.8 · 1.0 · 1.2", "thickness of the spring arm"),
            ("bayonet", "Bayonet", "the cap with lugs", "0.2 · 0.3 · 0.4", "gap round the lugs")]
    y -= 8
    for k, name, part, labels, mean in rows:
        y -= 19
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(M, y + 13, W - M, y + 13)
        c.setFillColor(MECH[k])
        c.circle(M + 4.5, y + 3.3, 4.5, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont("BodyB", 9.2)
        c.drawString(M + 13, y, name)
        c.setFont("Body", 9.2)
        c.drawString(cols[1], y, part)
        c.setFont("BodyB", 9.2)
        c.drawString(cols[2], y, labels)
        c.setFont("Body", 8.6)
        c.setFillColor(MUTED)
        c.drawString(cols[3], y, mean)

    y -= 34
    c.setFillColor(INK)
    c.setFont("Head", 15)
    c.drawString(M, y, "Before you start")
    steps = [
        "Take everything off the plate and sort it into the five mechanisms. Three of the small 10-tooth gears "
        "were packed inside the bayonet rings to save space: pop them out.",
        "Line up each mechanism's three pairs by the labels on the parts that change.",
        "<b>Don't sand, trim or force anything.</b> The point is how they come off your printer. If something "
        "only sticks on a squashed first layer (elephant's foot), try the part the other way up and note it.",
        "Test the three clearances of one mechanism back to back, so you compare like with like. Tick the "
        "results sheet on page 8 as you go.",
    ]
    y -= 12
    for i, s in enumerate(steps, 1):
        h = step(c, i, s, M, y, W - 2 * M, INK)
        y -= h + 6
    footer(c, 2)


def step(c, n, text, x, y, w, col):
    c.setFillColor(col)
    c.circle(x + 8, y - 7.5, 8, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("BodyB", 8.6)
    c.drawCentredString(x + 8, y - 10.5, str(n))
    return max(16, para(c, text, x + 24, y - 1, w - 24, STEP))


def judge(c, x, y, w, items):
    """Three verdict boxes stacked, tops at y. Returns the bottom."""
    for label, col, text in items:
        p = Paragraph(text, BODY)
        _, h = p.wrap(w - 22, 500)
        bh = h + 26
        c.setFillColor(PANEL)
        c.roundRect(x, y - bh, w, bh, 6, stroke=0, fill=1)
        c.setFillColor(col)
        c.roundRect(x, y - bh, 4, bh, 2, stroke=0, fill=1)
        c.setFont("BodyB", 9.4)
        c.drawString(x + 14, y - 15, label)
        p.drawOn(c, x + 14, y - 20 - h)
        y -= bh + 7
    return y


def mech_page(c, n, k, title, tests, label_note, steps, verdicts, tip, apart_cap, together_cap):
    col = MECH[k]
    pill(c, M, H - 58, f"{n - 2} of 5", col)
    c.setFillColor(INK)
    c.setFont("Head", 28)
    c.drawString(M, H - 92, title)
    h = para(c, tests, M, H - 104, W - 2 * M, LEDE)
    y = H - 110 - h
    para(c, label_note, M, y, W - 2 * M, SMALL)

    # the pictures: apart, then together
    iy, ih = H - 412, 250
    iw = (W - 2 * M - 46) / 2
    image_in(c, crop(IMG / f"{k}_apart.png"), M, iy, iw, ih, top=36)
    image_in(c, crop(IMG / f"{k}_together.png"), W - M - iw, iy, iw, ih, top=36)
    arrow(c, M + iw + 9, W - M - iw - 9, iy + ih / 2, col)
    for x, cap in ((M, apart_cap), (W - M - iw, together_cap)):
        c.setFont("BodyB", 9)
        c.setFillColor(col)
        c.drawString(x + 10, iy + ih - 18, cap[0])
        c.setFont("Body", 8.2)
        c.setFillColor(MUTED)
        c.drawString(x + 10, iy + ih - 30, cap[1])

    # steps on the left, verdicts on the right
    top = iy - 22
    lw = (W - 2 * M) * 0.58
    c.setFillColor(INK)
    c.setFont("Head", 14)
    c.drawString(M, top, "Steps")
    yy = top - 12
    for i, s in enumerate(steps, 1):
        yy -= step(c, i, s, M, yy, lw, col) + 6
    rx, rw = M + lw + 20, W - 2 * M - lw - 20
    c.setFillColor(INK)
    c.setFont("Head", 14)
    c.drawString(rx, top, "How to judge it")
    bottom = judge(c, rx, top - 12, rw, verdicts)
    if tip:
        ty = min(yy, bottom) - 6
        p = Paragraph(tip, SMALL)
        _, th = p.wrap(W - 2 * M - 28, 300)
        c.setFillColor(PANEL)
        c.roundRect(M, ty - th - 16, W - 2 * M, th + 16, 6, stroke=0, fill=1)
        p.drawOn(c, M + 14, ty - th - 8)
    footer(c, n)


def results(c):
    c.setFillColor(INK)
    c.setFont("Head", 24)
    c.drawString(M, H - 76, "Results sheet")
    para(c, "Print this page, or keep it on screen and mark it up. Tick one box per clearance, "
            "then circle your pick for each mechanism.", M, H - 90, W - 2 * M, LEDE)
    rows = [("thread", "Thread", ["0.2", "0.3", "0.4"]), ("ball", "Ball joint", ["0.4", "0.6", "0.8"]),
            ("gears", "Gears", ["+0", "+0.15", "+0.3"]), ("detent", "Detent", ["0.8", "1.0", "1.2"]),
            ("bayonet", "Bayonet", ["0.2", "0.3", "0.4"])]
    heads = [("Too tight", TIGHT), ("Just right", GOOD), ("Too loose", LOOSE), ("Broke", HexColor("#B23A3A"))]
    x_val, x_box0, box_dx = M + 110, M + 170, 58
    x_note = x_box0 + 4 * box_dx + 6
    y = H - 140
    c.setFont("BodyB", 8.2)
    for i, (t, col) in enumerate(heads):
        c.setFillColor(col)
        c.drawCentredString(x_box0 + i * box_dx + 9, y, t)
    c.setFillColor(MUTED)
    c.drawString(x_note, y, "Notes")
    y -= 10
    for k, name, vals in rows:
        block = 3 * 26 + 30
        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.line(M, y, W - M, y)
        c.setFillColor(MECH[k])
        c.circle(M + 6, y - 20, 6, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont("Head", 13)
        c.drawString(M + 18, y - 24, name)
        for j, v in enumerate(vals):
            ry = y - 24 - j * 26
            c.setFillColor(PANEL)
            c.roundRect(x_val - 6, ry - 6, 46, 20, 4, stroke=0, fill=1)
            c.setFillColor(INK)
            c.setFont("BodyB", 9.6)
            c.drawCentredString(x_val + 17, ry, v)
            for i, (_, col) in enumerate(heads):
                c.setStrokeColor(col)
                c.setLineWidth(1.1)
                c.roundRect(x_box0 + i * box_dx + 2, ry - 4, 14, 14, 3, stroke=1, fill=0)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.6)
            c.line(x_note, ry - 4, W - M, ry - 4)
        c.setFont("Body", 8.4)
        c.setFillColor(MUTED)
        c.drawString(M + 18, y - block + 12, "My pick:")
        for j, v in enumerate(vals + ["none"]):
            c.setFillColor(INK)
            c.setFont("BodyB", 9)
            c.drawString(M + 64 + j * 52, y - block + 12, v)
        y -= block + 4
    c.setStrokeColor(LINE)
    c.line(M, y, W - M, y)
    c.setFont("Body", 8.4)
    c.setFillColor(MUTED)
    c.drawString(M, y - 22, "Printer, filament and settings, so the numbers mean something later:")
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(M + 300, y - 24, W - M, y - 24)
    footer(c, 8)


def using(c):
    c.setFillColor(INK)
    c.setFont("Head", 24)
    c.drawString(M, H - 76, "Using your numbers")
    para(c, "Each pick is a clearance your printer really produces, not a guess from a forum. Use it the next time "
            "you design that kind of part, for the same filament and settings.", M, H - 90, W - 2 * M, LEDE)
    items = [
        ("thread", "Thread", "Grow the nut (or shrink the screw) by your pick, all round. This plate's thread is "
         "24 mm across with a 3 mm pitch and a coarse 0.8 mm tooth; a finer thread may want a little more room."),
        ("ball", "Ball joint", "Make the socket's mouth narrower than the ball by your pick. The cup needs slits to "
         "flex over the ball: these sockets have four, 0.8 mm wide, round an 8 mm ball."),
        ("gears", "Gears", "Add your pick to the gears' theoretical centre distance (the sum of their pitch radii). "
         "Here that's 22.5 mm for module 1.5 with 20 and 10 teeth, so +0.15 means 22.65 mm."),
        ("detent", "Detent", "Make a spring arm about your pick thick, in the same orientation. These arms print "
         "flat, 19 mm long, and flex 0.6 mm per click. An arm standing upright is weaker across its layers: "
         "if your pick whitened at all, use the next one down for upright arms."),
        ("bayonet", "Bayonet", "Leave your pick as the gap round the lugs, in the slot and on the way in. These "
         "lugs are 1.4 mm deep in a 32 mm bore, and lock with a 24° counterclockwise twist."),
    ]
    y = H - 140
    for k, name, text in items:
        c.setFillColor(MECH[k])
        c.roundRect(M, y - 4, 6, 18, 3, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont("Head", 13)
        c.drawString(M + 14, y, name)
        h = para(c, text, M + 14, y - 8, W - 2 * M - 14, BODY)
        y -= h + 30

    c.setFillColor(INK)
    c.setFont("Head", 15)
    c.drawString(M, y, "If none of the three worked")
    y -= 10
    h = para(c, "Note which way they all failed: all too tight, or all too loose. Then step past the end of the "
                "range by the same step (for a thread that was too tight at 0.4, try 0.5). "
                "A problem in every mechanism at once usually means the printer itself: calibrate flow and "
                "pressure advance for the filament, check for elephant's foot, and print again.",
             M, y, W - 2 * M, BODY)
    y -= h + 22
    c.setFillColor(PANEL)
    c.roundRect(M, y - 54, W - 2 * M, 54, 8, stroke=0, fill=1)
    para(c, "<b>Share your numbers in the comments.</b> Say which printer, nozzle and filament. "
            "Every report helps the next person start closer to right.", M + 14, y - 12, W - 2 * M - 28, BODY)
    footer(c, 9)


def main():
    c = canvas.Canvas(str(OUT), pagesize=letter)
    c.setTitle("Fit Test Plate: how to test it")
    c.setAuthor("OnBrandCraftz")
    c.setSubject("Instructions for the five-mechanism fit test plate")
    cover(c); c.showPage()
    overview(c); c.showPage()

    v = lambda t, g, l: [("Too tight", TIGHT, t), ("Just right", GOOD, g), ("Too loose", LOOSE, l)]
    mech_page(c, 3, "thread", "Thread",
              "Tests how much gap a printed thread needs to turn by hand.",
              "Labels on the <b>nut</b>: 0.2 · 0.3 · 0.4, the gap all round the thread in mm. The screws are labelled too, to keep pairs together, but all three are the same.",
              ["Hold the screw by its flange, post up. Either face of the nut can go down: both ends have a lead-in.",
               "Set the nut on the post and turn it <b>clockwise</b> (an ordinary right-hand thread). It should catch within half a turn.",
               "Keep turning with fingertips only, all the way down to the flange: just over two turns.",
               "Back it off a turn and rock the nut side to side. Note how much it tilts or clunks.",
               "Run it on and off five times. Does it get smoother or rougher? Any shavings?"],
              v("Needs a hard grip, squeaks, or stops partway.",
                "Turns all the way by fingertip, no grinding, only a little rock.",
                "Tilts visibly, or could jump a thread if you pulled it."),
              "If two values both pass, the tighter one that still turns by fingertip is usually the better pick: "
              "it lines up more accurately when it closes.",
              ("1  Line up", "the nut over the post"), ("2  Screw it down", "clockwise, by fingertip"))
    c.showPage()
    mech_page(c, 4, "ball", "Ball joint",
              "Tests how hard a ball joint should snap in to hold a pose.",
              "Labels on the <b>socket</b>: 0.4 · 0.6 · 0.8, how much narrower its mouth is than the 8 mm ball. "
              "The bigger the number, the harder the snap. The balls are labelled too, but all three are the same.",
              ["Stand the socket on the table, cup up. Turn the ball part upside down so the ball points into the cup.",
               "Press straight down with your thumb until it snaps in. If a hard thumb press won't do it, stop: that's too tight.",
               "Hold the socket's disc and tilt the stem to about 30°. Let go. Does it stay? Give it a gentle shake.",
               "Swivel the stem round in a circle. Smooth, or does it catch?",
               "Pull the two straight apart. Then look at the cup's four fingers for white stress marks or a crack."],
              v("Won't go in by thumb, or the fingers turn white.",
                "A firm snap, holds 30° without drooping, pulls out with real effort.",
                "Droops from 30°, or falls out when shaken."),
              "For posable figures, holding the angle matters more than how easily it goes in.",
              ("1  Line up", "ball turned over, above the cup"), ("2  Snap it in", "straight down, by thumb"))
    c.showPage()
    mech_page(c, 5, "gears", "Gears",
              "Tests how far apart two printed gears should sit to turn smoothly without skipping.",
              "Labels on the <b>base</b>: +0 · +0.15 · +0.3, extra space between the gears' centres in mm. "
              "All the gears are the same.",
              ["Press a 20-tooth gear onto the pin at the wide, round end of a base. It should spin freely on its own.",
               "Press a 10-tooth gear onto the other pin, turning it slightly so its teeth drop into the big gear's.",
               "Turn the big gear slowly through one full turn (the small one makes two). Feel for a tight spot.",
               "Hold the big gear still and wiggle the small one. A small tick of play is normal.",
               "Drive it from the small gear while pushing it toward the big one. Do the teeth ever skip?"],
              v("Binds or drags somewhere in the turn.",
                "One smooth turn, a little play, never skips.",
                "Clacks, rattles, or skips teeth under a push."),
              "If a gear is stiff on its pin before it meshes with anything, that's the pin, not the mesh: note "
              "it separately.",
              ("1  Line up", "both gears over their pins"), ("2  Mesh and turn", "teeth into teeth"))
    c.showPage()
    mech_page(c, 6, "detent", "Detent",
              "Tests how thick a printed spring arm should be to give a crisp click that lasts.",
              "Labels engraved in the <b>base</b>: 0.8 · 1.0 · 1.2, the thickness of the spring arm in mm. "
              "The three notched wheels are the same.",
              ["Set a wheel over the pin, dot up. Turn it so a notch faces the arm's bump (or push the arm back with a fingernail) and press it flat.",
               "Turn the wheel one full turn by its edge: 12 clicks, counted by the dot. It should never rest between two notches.",
               "Note the feel: a crisp click, a mushy one, or too stiff for a fingertip.",
               "Turn it three full turns each way. Watch where the arm meets its post for white marks or a crack.",
               "With the wheel in a notch, tap the base on the table. The wheel shouldn't move."],
              v("Hard to turn, or the arm turns white.",
                "A crisp click on all 12, turns by fingertip, no whitening.",
                "A faint click, or the wheel drifts off a notch."),
              None,
              ("1  Line up", "the wheel over the pin"), ("2  Press down and turn", "12 clicks a turn"))
    c.showPage()
    mech_page(c, 7, "bayonet", "Bayonet",
              "Tests how much room a twist-lock lid needs to drop in, turn and hold.",
              "Labels on the <b>cap</b>: 0.2 · 0.3 · 0.4, the gap round its three lugs in mm. The rings are labelled too, but all three are the same.",
              ["Turn the cap over, plug down. Look into the ring from above and find its three openings.",
               "Line the cap's three lugs up with the openings and push it straight down until it stops.",
               "Twist it <b>counterclockwise</b> (left, seen from above) to the stop. It's a short twist, about 24°.",
               "Locked, try to lift the cap straight up. It shouldn't come out. Does it rattle or tilt?",
               "Twist back to the openings, lift it out, and repeat five times. Then check the lugs for chips."],
              v("Won't drop in, or the twist needs force.",
                "Drops in, twists smoothly to a firm stop, won't lift, barely rattles.",
                "Rattles, tilts, or lifts while locked."),
              None,
              ("1  Line up", "lugs over the three openings"), ("2  Push down, twist left", "about 24°, to the stop"))
    c.showPage()
    results(c); c.showPage()
    using(c); c.showPage()
    c.save()
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
