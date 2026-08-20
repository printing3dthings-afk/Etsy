"""
generate_tracing_workbook.py — EDU1001, Kawaii Interactive Tracing Workbook
for Kids (Sunflower Studio theme).

New product line approved 2026-08-20 (market research grounded in real Etsy
revenue evidence). Research explicitly flagged kawaii kids' worksheets as a
SATURATED category where kawaii styling alone is not a differentiator --
genuine interactivity is. This is what separates EDU1001 from the existing
COLOR-series: real dashed-outline letter/number/word tracing extracted from
actual font glyph paths (tools/glyph_trace.py), not a static coloring page.

Reuses generate_planner_v2.py's visual primitives, same as RB1001. Custom
welcome/dashboard/index for the same reason as RB1001 (accurate single-
evergreen-PDF copy, no year/undated dual-version claim -- letters and
numbers don't expire).

Sight words: the first 20 of the standard, well-established Dolch
pre-primer list (kindergarten level) -- real, not invented, since this is
educational content for children and factual/pedagogical accuracy matters
the same way product-truthfulness matters everywhere else in this shop.

Run standalone:
    python tools/generate_tracing_workbook.py
"""
import random
import sys
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.generate_planner import (
    PRODUCT_FILES_DIR,
    SHOP_NAME,
    _get_fn,
    _bl,
    _panel_ink,
    _new_canvas,
    _page_bg,
    _ML,
    _MR,
    _MB,
    _make_cover_page,
    _merge_pdfs,
)
from tools.generate_planner_v2 import (
    _gradient_header,
    _shadow_box,
    _draw_binding,
    _textured_bg,
    _smart_footer,
)
from tools.glyph_trace import draw_dashed_text, text_width, dashed_glyph_group
from reportlab.graphics.shapes import Drawing, Group
from reportlab.graphics import renderPDF
from reportlab.lib.colors import Color

OUT_DIR = Path(PRODUCT_FILES_DIR)

EDU1001 = {
    "title": "Kawaii Tracing Workbook",
    "subtitle": "Sunflower Studio",
    "year": None,
    "theme": (0.957, 0.769, 0.188),    # #F4C430 sunflower yellow
    "accent": (0.290, 0.486, 0.349),   # #4A7C59 stem green
    "bg": (1.0, 0.992, 0.941),         # #FFFDF0 cream petal
    "dark": (0.165, 0.102, 0.0),       # #2A1A00 seed brown
    "sections": [
        "Welcome & Setup", "Dashboard / Home", "Workbook Index",
        "For Parents & Teachers",
        "Letter Tracing A-Z × 26", "Number Tracing 1-20 × 20",
        "Shape Tracing × 8", "Sight Words × 5",
        "Coloring & Counting Math × 4", "Reward Chart",
        "Practice Pages × 2",
    ],
}

_LETTER_WORDS = {
    "A": "Apple", "B": "Bee", "C": "Cat", "D": "Duck", "E": "Egg",
    "F": "Fish", "G": "Grapes", "H": "Hat", "I": "Ice Cream", "J": "Jam",
    "K": "Kite", "L": "Leaf", "M": "Moon", "N": "Nest", "O": "Owl",
    "P": "Pig", "Q": "Queen", "R": "Rainbow", "S": "Sun", "T": "Tree",
    "U": "Umbrella", "V": "Van", "W": "Whale", "X": "Xylophone", "Y": "Yarn",
    "Z": "Zebra",
}

# Real, standard Dolch pre-primer sight words -- not invented. First 20 of
# the widely-used 40-word kindergarten list.
_SIGHT_WORDS = [
    "a", "and", "away", "big", "blue", "can", "come", "down", "find", "for",
    "funny", "go", "help", "here", "I", "in", "is", "it", "jump", "little",
]

_SHAPES = ["Circle", "Square", "Triangle", "Rectangle", "Star", "Heart", "Oval", "Diamond"]

_SHAPE_EXAMPLES = {
    "Circle": "a clock, a ball, or the sun",
    "Square": "a window, a napkin, or a cracker",
    "Triangle": "a slice of pizza, a tent, or a mountain",
    "Rectangle": "a door, a book, or a phone",
    "Star": "the night sky, a sheriff's badge, or a starfish",
    "Heart": "a valentine card, a love note, or a strawberry's top",
    "Oval": "an egg, a football, or a watermelon",
    "Diamond": "a kite, a baseball field, or a gem",
}

_NUMBER_WORDS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
    8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
    14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen",
    19: "nineteen", 20: "twenty",
}


# ---------------------------------------------------------------------------
# Custom nav pages
# ---------------------------------------------------------------------------

def _gen_welcome_page(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    _page_bg(c, BG, PW, PH)
    c.setFillColorRGB(*T)
    c.rect(0, PH - 8, PW, 8, fill=1, stroke=0)
    c.setFillColorRGB(*A)
    c.rect(0, PH - 14, PW, 6, fill=1, stroke=0)

    y = PH - 72
    c.setFillColorRGB(*T)
    c.setFont(fn("bold"), 28)
    c.drawCentredString(PW / 2, y, "Welcome!")
    y -= 24
    c.setFillColorRGB(*DK)
    c.setFont(fn("semibold"), 13)
    c.drawCentredString(PW / 2, y, pcfg["title"])
    y -= 16
    c.setFillColorRGB(*T)
    c.setFont(fn("italic"), 10)
    c.drawCentredString(PW / 2, y, f"{pcfg['subtitle']} — Evergreen Edition (no dates, use anytime)")

    y -= 14
    c.setFillColorRGB(*A)
    c.rect(_ML + (PW - _ML - _MR) * 0.2, y, (PW - _ML - _MR) * 0.6, 2, fill=1, stroke=0)
    y -= 30

    blocks = [
        ("📥 HOW TO DOWNLOAD YOUR FILES", [
            "Your tracing workbook PDF is in your Etsy Purchases page.",
            "Download it to your device before opening — don't open directly from browser.",
        ]),
        ("✏️ HOW TO TRACE WITH APPLE PENCIL", [
            "Open the PDF in GoodNotes 6, Notability, or PDF Expert.",
            "Each dashed outline is a real letter/number/shape — trace right over it.",
            "Use a bright color pen so tracing is easy to see and check.",
        ]),
        ("🖨️ WANT TO PRINT IT INSTEAD?", [
            "This workbook prints beautifully too — great for repeated practice on paper.",
            "Print single-sided if your child likes to trace with crayons or markers.",
        ]),
        ("💬 NEED HELP?", [
            f"Email {SHOP_NAME} support any time — we're glad to help.",
        ]),
    ]
    for heading, lines in blocks:
        c.setFillColorRGB(*T)
        c.setFont(fn("bold"), 11)
        c.drawString(_ML, y, heading)
        y -= 16
        c.setFillColorRGB(*DK)
        c.setFont(fn("regular"), 9)
        for line in lines:
            c.drawString(_ML + 12, y, line)
            y -= 14
        y -= 10

    _draw_nav_tabs(c, pcfg, fn, PW, PH, None)
    _smart_footer(c, T, A, BG, fn, PW, prev_lbl="", next_lbl="DASHBOARD")
    c.showPage()
    c.save()
    return buf.getvalue()


def _gen_dashboard_page(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    _page_bg(c, BG, PW, PH)
    _gradient_header(c, pcfg["title"].upper(), T, A, BG, fn, PW, PH, sub=pcfg["subtitle"])

    buttons = [
        "For Parents", "Letter Tracing", "Number Tracing",
        "Shape Tracing", "Sight Words", "Math & Coloring",
        "Reward Chart", "Practice Pages", "Workbook Index",
    ]
    cols = 3
    top = PH - 58 - 20
    gap = 10.0
    bw = (PW - _ML - _MR - gap * (cols - 1)) / cols
    bh = 62.0
    for i, label in enumerate(buttons):
        r, col = divmod(i, cols)
        x = _ML + col * (bw + gap)
        y = top - r * (bh + gap) - bh
        ink = _panel_ink(DK, T)
        c.setFillColorRGB(*_bl(T, 0.85))
        c.roundRect(x, y, bw, bh, 8, fill=1, stroke=0)
        c.setFillColorRGB(*T)
        c.setLineWidth(0.6)
        c.roundRect(x, y, bw, bh, 8, fill=0, stroke=1)
        c.setFillColorRGB(*ink)
        c.setFont(fn("bold"), 9)
        c.drawCentredString(x + bw / 2, y + bh / 2, label)

    _draw_nav_tabs(c, pcfg, fn, PW, PH, "dashboard")
    _smart_footer(c, T, A, BG, fn, PW, prev_lbl="WELCOME", next_lbl="INDEX")
    c.showPage()
    c.save()
    return buf.getvalue()


def _gen_index_page(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    _page_bg(c, BG, PW, PH)
    _gradient_header(c, "WORKBOOK INDEX", T, A, BG, fn, PW, PH)

    y = PH - 58 - 26
    c.setFillColorRGB(*DK)
    c.setFont(fn("regular"), 9.5)
    for section in pcfg["sections"]:
        c.setFillColorRGB(*T)
        c.circle(_ML + 3, y + 3, 2.2, fill=1, stroke=0)
        c.setFillColorRGB(*DK)
        c.drawString(_ML + 14, y, section)
        y -= 17
        if y < 70:
            break

    _draw_nav_tabs(c, pcfg, fn, PW, PH, None)
    _smart_footer(c, T, A, BG, fn, PW, prev_lbl="DASHBOARD", next_lbl="PARENTS")
    c.showPage()
    c.save()
    return buf.getvalue()


def _gen_parents_page(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    _page_bg(c, BG, PW, PH)
    _gradient_header(c, "FOR PARENTS & TEACHERS", T, A, BG, fn, PW, PH)

    tips = [
        "Trace with your child the first time on each new page — model the stroke direction, don't just watch.",
        "Little hands tire fast. 10-15 minutes per sitting is plenty — this workbook is built for many short sessions, not one long one.",
        "Celebrate effort over neatness at first. A wobbly line traced independently beats a perfect one traced by an adult's hand over theirs.",
        "Letters are grouped A-Z (not by stroke difficulty) so this pairs naturally with whatever order your curriculum already teaches.",
        "The dashed outlines are real letterforms, not simplified shapes — this is the same shape your child will write for the rest of their life.",
        "Use the Reward Chart page after each completed section — a simple checkmark or sticker is enough positive reinforcement for this age.",
        "This is a single evergreen PDF — reuse pages by printing extras, or trace-and-erase digitally in GoodNotes/Notability for unlimited practice.",
    ]
    y = PH - 58 - 24
    c.setFillColorRGB(*DK)
    c.setFont(fn("regular"), 9.5)
    for tip in tips:
        c.setFillColorRGB(*T)
        c.circle(_ML + 3, y + 3, 2.2, fill=1, stroke=0)
        c.setFillColorRGB(*DK)
        words = tip.split(" ")
        line = ""
        max_w = PW - _ML - _MR - 16
        for w in words:
            test = (line + " " + w).strip()
            if c.stringWidth(test, fn("regular"), 9.5) > max_w:
                c.drawString(_ML + 14, y, line)
                y -= 13
                line = w
            else:
                line = test
        if line:
            c.drawString(_ML + 14, y, line)
        y -= 22

    _draw_nav_tabs(c, pcfg, fn, PW, PH, None)
    _smart_footer(c, T, A, BG, fn, PW, prev_lbl="INDEX", next_lbl="LETTERS")
    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tracing pages (the real differentiator)
# ---------------------------------------------------------------------------

def _trace_row(c, text, x_center, y, size_pt, color_rgb, count=3, gap=14):
    """Draw `count` dashed-outline repetitions of `text` centered around
    x_center at height y, for repeat-tracing practice (real workbook
    convention: trace several times before writing independently)."""
    w = text_width(text, size_pt)
    total_w = w * count + gap * (count - 1)
    x = x_center - total_w / 2
    for _ in range(count):
        draw_dashed_text(c, text, x, y, size_pt, stroke_rgb=color_rgb, dash=(5, 4), stroke_w=2.0)
        x += w + gap


def _practice_line(c, x, y, w, dk_rgb, n_boxes=5):
    """A 3-rule handwriting guide (top rule, dashed midline, base rule) with
    n_boxes light dividers -- real blank space for the "now try it on your
    own" independent-writing step the page text promises. Without this the
    page instructs a step it gives no room to actually do."""
    c.setStrokeColorRGB(*_bl(dk_rgb, 0.35))
    c.setLineWidth(0.8)
    c.line(x, y, x + w, y)
    c.line(x, y - 30, x + w, y - 30)
    c.setStrokeColorRGB(*_bl(dk_rgb, 0.55))
    c.setLineWidth(0.6)
    c.setDash(2, 2)
    c.line(x, y - 15, x + w, y - 15)
    c.setDash()
    box_w = w / n_boxes
    c.setStrokeColorRGB(*_bl(dk_rgb, 0.7))
    c.setLineWidth(0.5)
    for i in range(1, n_boxes):
        c.line(x + i * box_w, y, x + i * box_w, y - 30)


def _gen_letter_hunt(c, upper, ML, CW, top, T, DK, fn, n_letters=42, n_target=10):
    """Circle-the-letter activity -- fills the real remaining page space with
    a genuine letter-recognition exercise tied to THIS page's letter, not
    generic filler. Seeded per-letter so rebuilds are reproducible rather
    than shuffling differently every run."""
    rng = random.Random(f"hunt-{upper}")
    pool = [ch for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if ch != upper]
    letters = [upper] * n_target + [rng.choice(pool) for _ in range(n_letters - n_target)]
    rng.shuffle(letters)

    c.setFillColorRGB(*DK)
    c.setFont(fn("bold"), 9)
    c.drawString(ML, top, f"Letter Hunt — circle every {upper} you find:")
    top -= 26

    cols = 14
    cell_w = CW / cols
    cell_h = 30
    c.setFont(fn("bold"), 13)
    for i, ch in enumerate(letters):
        row, col = divmod(i, cols)
        cx = ML + col * cell_w + cell_w / 2
        cy = top - row * cell_h
        c.setFillColorRGB(*DK)
        c.drawCentredString(cx, cy, ch)
    rows = -(-n_letters // cols)
    return top - (rows - 1) * cell_h - 20


def _gen_letter_pages(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    chunks = []
    for i, upper in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        lower = upper.lower()
        word = _LETTER_WORDS[upper]
        c, buf, PW, PH = _new_canvas()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        _gradient_header(c, f"LETTER {upper}{lower}", T, A, BG, fn, PW, PH,
                          sub=f"Letter {i + 1} of 26 — {word} starts with {upper}")

        ML = _ML + 26
        CW = PW - ML - _MR
        top = PH - 58 - 26

        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 9)
        c.drawString(ML, top, "Uppercase — trace it:")
        top -= 46
        _trace_row(c, upper, ML + CW / 2, top, 88, T, count=4, gap=18)
        top -= 26
        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 9)
        c.drawString(ML, top, "Now write it yourself:")
        top -= 14
        _practice_line(c, ML, top, CW, DK, n_boxes=5)
        top -= 42

        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 9)
        c.drawString(ML, top, "Lowercase — trace it:")
        top -= 46
        _trace_row(c, lower, ML + CW / 2, top, 88, A, count=4, gap=18)
        top -= 26
        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 9)
        c.drawString(ML, top, "Now write it yourself:")
        top -= 14
        _practice_line(c, ML, top, CW, DK, n_boxes=5)
        top -= 34

        box_h = 62
        c.setFillColorRGB(*_bl(T, 0.88))
        c.roundRect(ML, top - box_h, CW, box_h, 6, fill=1, stroke=0)
        c.setFillColorRGB(*DK)
        c.setFont(fn("italic"), 9)
        c.drawCentredString(ML + CW / 2, top - 16, f"{upper} is for {word}! Trace the word:")
        word_w = text_width(word, 22)
        draw_dashed_text(c, word, ML + CW / 2 - word_w / 2, top - 50, 22, stroke_rgb=DK, dash=(4, 3), stroke_w=1.4)
        top -= box_h + 18

        top = _gen_letter_hunt(c, upper, ML, CW, top, T, DK, fn)

        _draw_nav_tabs(c, pcfg, fn, PW, PH, "letters")
        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="LETTERS", next_lbl="LETTERS")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


def _gen_number_pages(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    chunks = []
    for n in range(1, 21):
        digits = str(n)
        c, buf, PW, PH = _new_canvas()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        _gradient_header(c, f"NUMBER {n}", T, A, BG, fn, PW, PH, sub=f"Number {n} of 20")

        ML = _ML + 26
        CW = PW - ML - _MR
        top = PH - 58 - 26

        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 9)
        c.drawString(ML, top, "Trace it:")
        top -= 50
        _trace_row(c, digits, ML + CW / 2, top, 92, T, count=4, gap=20)
        top -= 26
        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 9)
        c.drawString(ML, top, "Now write it yourself:")
        top -= 14
        _practice_line(c, ML, top, CW, DK, n_boxes=5)
        top -= 40

        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 9)
        c.drawString(ML, top, f"Count and color {n} sun{'s' if n != 1 else ''}:")
        top -= 30
        cols = min(n, 8)
        r_ = 16
        gap_x = (CW - 2 * r_) / max(cols, 1)
        gap_y = 46
        for i in range(n):
            row, col = divmod(i, 8)
            cx = ML + r_ + 4 + col * gap_x
            cy = top - row * gap_y
            c.setStrokeColorRGB(*_bl(DK, 0.4))
            c.setLineWidth(1.4)
            c.setDash(3, 2)
            c.circle(cx, cy, r_, fill=0, stroke=1)
            c.setDash()
        count_rows = -(-n // 8)
        top -= (count_rows - 1) * gap_y + 40

        word = _NUMBER_WORDS[n]
        box_h = 62
        c.setFillColorRGB(*_bl(T, 0.88))
        c.roundRect(ML, top - box_h, CW, box_h, 6, fill=1, stroke=0)
        c.setFillColorRGB(*DK)
        c.setFont(fn("italic"), 9)
        c.drawCentredString(ML + CW / 2, top - 16, f"{n} is written \"{word}\" in words! Trace it:")
        word_w = text_width(word, 22)
        draw_dashed_text(c, word, ML + CW / 2 - word_w / 2, top - 50, 22, stroke_rgb=DK, dash=(4, 3), stroke_w=1.4)
        top -= box_h + 18

        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 9)
        before = n - 1 if n > 1 else None
        after = n + 1 if n < 20 else None
        prompt = "What number comes before and after " + digits + "?"
        c.drawString(ML, top, prompt)
        top -= 24
        blanks = [str(before) if before is not None else "___", digits, str(after) if after is not None else "___"]
        bw = 60
        gap = 24
        total_w = bw * 3 + gap * 2
        bx = ML + CW / 2 - total_w / 2
        for i, val in enumerate(blanks):
            is_given = (i == 1)
            c.setStrokeColorRGB(*_bl(DK, 0.5))
            c.setLineWidth(1.0)
            c.roundRect(bx, top - 34, bw, 34, 5, fill=0, stroke=1)
            c.setFillColorRGB(*(T if is_given else DK))
            c.setFont(fn("bold"), 16)
            c.drawCentredString(bx + bw / 2, top - 24, val if is_given else "")
            bx += bw + gap

        _draw_nav_tabs(c, pcfg, fn, PW, PH, "numbers")
        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="NUMBERS", next_lbl="NUMBERS")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


def _dashed_shape(c, kind, cx, cy, size, stroke_rgb, dash=(5, 4), stroke_w=2.2):
    color = Color(*stroke_rgb)
    c.setStrokeColor(color)
    c.setLineWidth(stroke_w)
    c.setDash(list(dash))
    r = size / 2
    if kind == "Circle":
        c.circle(cx, cy, r, fill=0, stroke=1)
    elif kind == "Square":
        c.rect(cx - r, cy - r, size, size, fill=0, stroke=1)
    elif kind == "Rectangle":
        c.rect(cx - r * 1.3, cy - r * 0.75, size * 1.3, size * 0.75, fill=0, stroke=1)
    elif kind == "Oval":
        c.ellipse(cx - r * 1.25, cy - r * 0.8, cx + r * 1.25, cy + r * 0.8, fill=0, stroke=1)
    elif kind == "Triangle":
        p = c.beginPath()
        p.moveTo(cx, cy + r)
        p.lineTo(cx - r, cy - r)
        p.lineTo(cx + r, cy - r)
        p.close()
        c.drawPath(p, fill=0, stroke=1)
    elif kind == "Diamond":
        p = c.beginPath()
        p.moveTo(cx, cy + r)
        p.lineTo(cx + r, cy)
        p.lineTo(cx, cy - r)
        p.lineTo(cx - r, cy)
        p.close()
        c.drawPath(p, fill=0, stroke=1)
    elif kind == "Star":
        import math
        p = c.beginPath()
        for i in range(10):
            ang = math.pi / 2 + i * math.pi / 5
            rad = r if i % 2 == 0 else r * 0.4
            px, py = cx + rad * math.cos(ang), cy + rad * math.sin(ang)
            if i == 0:
                p.moveTo(px, py)
            else:
                p.lineTo(px, py)
        p.close()
        c.drawPath(p, fill=0, stroke=1)
    elif kind == "Heart":
        p = c.beginPath()
        p.moveTo(cx, cy - r * 0.8)
        p.curveTo(cx - r * 1.4, cy + r * 0.5, cx - r * 0.5, cy + r * 1.1, cx, cy + r * 0.4)
        p.curveTo(cx + r * 0.5, cy + r * 1.1, cx + r * 1.4, cy + r * 0.5, cx, cy - r * 0.8)
        p.close()
        c.drawPath(p, fill=0, stroke=1)
    c.setDash()


def _gen_shape_pages(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    chunks = []
    for i, shape in enumerate(_SHAPES):
        c, buf, PW, PH = _new_canvas()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        _gradient_header(c, shape.upper(), T, A, BG, fn, PW, PH, sub=f"Shape {i + 1} of {len(_SHAPES)}")

        ML = _ML + 26
        CW = PW - ML - _MR
        top = PH - 58 - 30
        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 8.5)
        c.drawString(ML, top, "Trace each shape:")
        top -= 30

        size = 110
        positions = [(ML + CW * 0.22, top - size * 0.6), (ML + CW * 0.78, top - size * 0.6),
                     (ML + CW * 0.22, top - size * 1.9), (ML + CW * 0.78, top - size * 1.9)]
        colors = [T, A, A, T]
        for (px, py), col in zip(positions, colors):
            _dashed_shape(c, shape, px, py, size, col)
        top -= size * 2.5

        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 8.5)
        c.drawString(ML, top, "Now draw your own:")
        top -= 14
        box_w = (CW - 2 * 14) / 3
        box_h = 90
        for i in range(3):
            bx = ML + i * (box_w + 14)
            c.setStrokeColorRGB(*_bl(DK, 0.5))
            c.setLineWidth(0.8)
            c.roundRect(bx, top - box_h, box_w, box_h, 6, fill=0, stroke=1)
        top -= box_h + 22

        c.setFillColorRGB(*_bl(A, 0.85))
        c.roundRect(ML, top - 34, CW, 34, 6, fill=1, stroke=0)
        c.setFillColorRGB(*DK)
        c.setFont(fn("italic"), 8.5)
        c.drawCentredString(ML + CW / 2, top - 20, f"Look around! A {shape.lower()} looks like...")
        c.setFont(fn("bold"), 8.5)
        c.drawCentredString(ML + CW / 2, top - 30, _SHAPE_EXAMPLES[shape])

        _draw_nav_tabs(c, pcfg, fn, PW, PH, "shapes")
        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="SHAPES", next_lbl="SHAPES")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


def _gen_sight_word_pages(pcfg, words_per_page=4):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    chunks = []
    n_pages = -(-len(_SIGHT_WORDS) // words_per_page)
    for pi in range(n_pages):
        page_words = _SIGHT_WORDS[pi * words_per_page:(pi + 1) * words_per_page]
        c, buf, PW, PH = _new_canvas()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        _gradient_header(c, "SIGHT WORDS", T, A, BG, fn, PW, PH, sub=f"Page {pi + 1} of {n_pages}")

        ML = _ML + 26
        CW = PW - ML - _MR
        top = PH - 58 - 30
        row_h = (top - 60) / len(page_words)
        for word in page_words:
            c.setFillColorRGB(*DK)
            c.setFont(fn("bold"), 9)
            c.drawString(ML, top - 6, word)
            _trace_row(c, word, ML + CW / 2 + 20, top - 24, 34, T, count=3, gap=20)
            _practice_line(c, ML, top - 44, CW, DK, n_boxes=4)
            top -= row_h

        _draw_nav_tabs(c, pcfg, fn, PW, PH, "words")
        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="WORDS", next_lbl="WORDS")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


def _gen_math_coloring_pages(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    # Real, correct addition facts, sums increasing across the 4 pages (2-4,
    # 4-6, 6-8, 8-10) -- genuine progression, not random filler.
    problems_by_page = [
        [(1, 1), (2, 1), (1, 2), (1, 3), (3, 1), (2, 2)],
        [(3, 2), (1, 4), (4, 1), (2, 4), (3, 3), (5, 1)],
        [(2, 5), (4, 3), (6, 1), (3, 5), (4, 4), (6, 2)],
        [(5, 4), (6, 3), (7, 2), (5, 5), (6, 4), (8, 2)],
    ]
    chunks = []
    for pi, problems in enumerate(problems_by_page):
        c, buf, PW, PH = _new_canvas()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        _gradient_header(c, "MATH & COLORING", T, A, BG, fn, PW, PH, sub=f"Page {pi + 1} of {len(problems_by_page)}")

        ML = _ML + 26
        CW = PW - ML - _MR
        top = PH - 58 - 30
        cell_h = (top - 60) / 3
        for i, (a, b) in enumerate(problems):
            row, col = divmod(i, 2)
            x = ML + col * (CW / 2)
            y = top - row * cell_h
            answer = a + b
            c.setFillColorRGB(*DK)
            c.setFont(fn("bold"), 22)
            c.drawString(x + 10, y - 40, f"{a} + {b} =")
            c.setStrokeColorRGB(*_bl(DK, 0.4))
            c.setLineWidth(1.2)
            c.roundRect(x + CW / 2 - 70, y - 62, 40, 32, 5, fill=0, stroke=1)
            c.setFillColorRGB(*_bl(T, 0.5))
            c.setFont(fn("italic"), 7)
            c.drawString(x + 10, y - 78, f"Now color {answer} sunflower petals below")
            for k in range(answer):
                cx = x + 16 + k * 18
                cy = y - 96
                c.setStrokeColorRGB(*_bl(A, 0.5))
                c.setLineWidth(1.0)
                c.setDash(2, 2)
                c.circle(cx, cy, 7, fill=0, stroke=1)
                c.setDash()

        _draw_nav_tabs(c, pcfg, fn, PW, PH, "math")
        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="MATH", next_lbl="MATH")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


def _gen_reward_chart_page(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    c, buf, PW, PH = _new_canvas()
    _page_bg(c, BG, PW, PH)
    _gradient_header(c, "MY REWARD CHART", T, A, BG, fn, PW, PH,
                      sub="Color or check a star each time you finish a page!")

    ML = _ML + 20
    CW = PW - ML - _MR
    top = PH - 58 - 30
    cols, rows = 6, 8
    cell = min(CW / cols, (top - 60) / rows) - 6
    for r in range(rows):
        for col in range(cols):
            cx = ML + col * (cell + 6) + cell / 2
            cy = top - r * (cell + 6) - cell / 2
            _dashed_shape(c, "Star", cx, cy, cell * 0.9, T, dash=(3, 2), stroke_w=1.4)

    c.setFillColorRGB(*DK)
    c.setFont(fn("italic"), 8)
    c.drawCentredString(PW / 2, 46,
                         "Love stickers? Check out OnBrandCraftz's kawaii digital sticker packs to decorate this chart!")

    _draw_nav_tabs(c, pcfg, fn, PW, PH, "rewards")
    _smart_footer(c, T, A, BG, fn, PW, prev_lbl="MATH", next_lbl="PRACTICE")
    c.showPage()
    c.save()
    return buf.getvalue()


def _gen_practice_pages(pcfg, count=2):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    chunks = []
    for pi in range(count):
        c, buf, PW, PH = _new_canvas()
        _page_bg(c, BG, PW, PH)
        _gradient_header(c, "PRACTICE PAGE", T, A, BG, fn, PW, PH, sub=f"Page {pi + 1} of {count} — write anything you'd like")
        ML = _ML + 20
        CW = PW - ML - _MR
        top = PH - 58 - 30
        row_h = 30
        while top > 60:
            c.setStrokeColorRGB(*_bl(DK, 0.55))
            c.setLineWidth(0.7)
            c.line(ML, top, ML + CW, top)
            top -= row_h
        _draw_nav_tabs(c, pcfg, fn, PW, PH, None)
        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="REWARDS", next_lbl="")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Persistent nav-tab strip -- a real, working substitute for "floating while
# scrolling." A PDF has no notion of scroll-position-relative overlays (that's
# an HTML/CSS concept -- pages are static, and PDF JavaScript can't create a
# fixed-during-scroll widget). What a PDF genuinely supports is real internal
# link annotations (GoToActions) stamped at the SAME position on every page,
# so the same tap gets you to the same section from anywhere in the document
# -- the honest, working equivalent of a floating nav button.
#
# Drawn directly into each page's own canvas (not merge_page()'d on as a
# separate overlay afterward) -- confirmed live that merge_page() badly
# duplicates resources on pages that already carry many Form XObjects (every
# letter/number tracing page has dozens, one per dashed glyph): merging even
# a ~2KB overlay onto a single 78KB letter page ballooned it to 294KB, and
# across all 71 pages that took the whole PDF from 7MB to 20MB, right at
# Etsy's hard limit. Drawing on the same canvas that's already drawing the
# rest of the page shares its existing font/resource references instead of
# duplicating them, so this costs nothing per page.
# ---------------------------------------------------------------------------

_NAV_TABS = [
    ("HOME", "dashboard"),
    ("Aa", "letters"),
    ("123", "numbers"),
    ("SHP", "shapes"),
    ("WRD", "words"),
    ("1+1", "math"),
    ("FUN", "rewards"),
]


def _assert_nav_labels_renderable():
    """A symbol character silently outside the font's glyph set doesn't
    raise -- drawCentredString just renders nothing, and the tab ships
    visibly blank (confirmed live: an original "star"/"diamond" label pair
    wasn't in Poppins-Bold's cmap and rendered as an empty colored box with
    no text at all, easy to miss without a real device check). Checking
    every label's characters against the font's real cmap at import time
    turns that into a loud failure instead of a silent one.
    """
    from tools import glyph_trace
    glyph_trace._ensure_loaded()
    for label, key in _NAV_TABS:
        for ch in label:
            if ch != " " and ord(ch) not in glyph_trace._cmap:
                raise ValueError(
                    f"nav tab {key!r}'s label {label!r} contains {ch!r} (U+{ord(ch):04X}), "
                    f"which is not in Poppins-Bold's glyph set -- it would render blank."
                )


_assert_nav_labels_renderable()

_NAV_TAB_H = 54.0
_NAV_TAB_X = 8.0
_NAV_TAB_W = 34.0
_NAV_TAB_TOP_MARGIN = 90.0


def _nav_tab_rects(PH):
    """Pure coordinate function -- both the drawing code (per page, at
    generation time) and the link-annotation code (post-process, on the
    final merged doc) must agree on exact pixel rects, so this is the one
    place either of them may compute them."""
    rects = {}
    y = PH - _NAV_TAB_TOP_MARGIN
    for label, key in _NAV_TABS:
        rects[key] = (_NAV_TAB_X, y - _NAV_TAB_H, _NAV_TAB_X + _NAV_TAB_W, y)
        y -= _NAV_TAB_H + 6
    return rects


def _draw_nav_tabs(c, pcfg, fn, PW, PH, current_section):
    """Call once per page, right before c.showPage(). Draws the tab strip
    directly on the page's own canvas. `current_section` is dimmed/skipped
    (no point linking a page to its own section)."""
    T, A = pcfg["theme"], pcfg["accent"]
    colors = [T, A]
    rects = _nav_tab_rects(PH)
    for i, (label, key) in enumerate(_NAV_TABS):
        x0, y0, x1, y1 = rects[key]
        is_current = key == current_section
        col = _bl(colors[i % 2], 0.55) if is_current else colors[i % 2]
        c.setFillColorRGB(*col)
        c.roundRect(x0, y0, x1 - x0, y1 - y0, 6, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(fn("bold"), 8 if len(label) <= 3 else 6.5)
        c.saveState()
        c.translate((x0 + x1) / 2, (y0 + y1) / 2)
        c.rotate(90)
        c.drawCentredString(0, -3, label)
        c.restoreState()


def _stamp_nav_links(pdf_bytes: bytes, section_start_pages: dict, section_of_page: dict) -> bytes:
    """Lightweight post-process: add ONLY the clickable link annotations
    (small dictionary entries, not page content) -- safe, no merge_page()
    resource duplication, since annotations reference existing page objects
    rather than adding new content streams."""
    from PyPDF2 import PdfReader, PdfWriter
    from PyPDF2.generic import AnnotationBuilder
    import io as _io

    reader = PdfReader(_io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    PH = float(reader.pages[0].mediabox.height)
    rects = _nav_tab_rects(PH)
    for i in range(len(writer.pages)):
        current = section_of_page.get(i)
        for key, rect in rects.items():
            if key == current:
                continue
            target = section_start_pages.get(key)
            if target is None:
                continue
            annot = AnnotationBuilder.link(rect=rect, target_page_index=target)
            writer.add_annotation(page_number=i, annotation=annot)

    out = _io.BytesIO()
    writer.write(out)
    return out.getvalue()


def build_tracing_workbook():
    pcfg = EDU1001
    cover_cfg = {
        "name": pcfg["title"], "subtitle": pcfg["subtitle"], "year": pcfg.get("year"),
        "bg_rgb": pcfg["bg"], "theme_rgb": pcfg["theme"], "dark_rgb": pcfg["dark"],
    }
    cover_img_path = OUT_DIR / "new_product_covers" / "EDU1001_kids_tracing_sunflower_studio.png"
    cover_pdf_bytes = _make_cover_page(cover_cfg, str(cover_img_path) if cover_img_path.exists() else None)

    named_chunks = [
        ("cover", cover_pdf_bytes),
        ("welcome", _gen_welcome_page(pcfg)),
        ("dashboard", _gen_dashboard_page(pcfg)),
        ("index", _gen_index_page(pcfg)),
        ("parents", _gen_parents_page(pcfg)),
        ("letters", _gen_letter_pages(pcfg)),
        ("numbers", _gen_number_pages(pcfg)),
        ("shapes", _gen_shape_pages(pcfg)),
        ("words", _gen_sight_word_pages(pcfg)),
        ("math", _gen_math_coloring_pages(pcfg)),
        ("rewards", _gen_reward_chart_page(pcfg)),
        ("practice", _gen_practice_pages(pcfg)),
    ]

    from PyPDF2 import PdfReader
    import io as _io
    section_start_pages = {}
    section_of_page = {}
    running = 0
    for name, data in named_chunks:
        section_start_pages[name] = running
        n = len(PdfReader(_io.BytesIO(data)).pages)
        for p in range(running, running + n):
            section_of_page[p] = name
        running += n

    full = _merge_pdfs(*(data for _, data in named_chunks))
    full = _stamp_nav_links(full, section_start_pages, section_of_page)
    out_path = OUT_DIR / "EDU1001.pdf"
    out_path.write_bytes(full)
    return out_path


def main():
    path = build_tracing_workbook()
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(path))
        print(f"EDU1001: {len(reader.pages)} pages, {path.stat().st_size / 1024:.0f} KB -> {path}")
    except Exception as e:
        print(f"EDU1001 saved to {path} (stats unavailable: {e})")


if __name__ == "__main__":
    main()
