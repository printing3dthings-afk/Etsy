"""
generate_grade2_workbook.py — EDU1003, Cursive & Skills Workbook (Ocean
Breeze theme), the 1st-2nd grade (ages 6-8) step-up sibling of EDU1001/
EDU1002.

Built 2026-08-20 after Scott asked for "a higher grade level or age level
for slightly older kids" alongside EDU1002's boys-themed request. Reuses
generate_tracing_workbook.py's proven low-level primitives (_trace_row,
_practice_line, _dashed_shape, the nav-tab strip/link-annotation apparatus,
welcome/dashboard/index/parents page generators, the reward-chart and
practice-page generators) rather than duplicating them -- those are already
real-device-verified across two shipped products. What's genuinely new here
is the CONTENT tier: cursive-style letter tracing (a second font, Caveat
Bold -- see tools/glyph_trace.py's font registry, added specifically for
this), grade-1 sight words (a real, distinct, harder Dolch tier from
EDU1001/EDU1002's pre-primer list, not a repeat), sentence tracing/copying,
and 2-digit addition/subtraction WITH REGROUPING plus single-digit
multiplication -- none of which the shared engine's original page types
cover, so those get new generator functions in this module.

Labeling note (Scott's call, 2026-08-20): no free, commercially-licensed
font matches official school-taught D'Nealian/Zaner-Bloser cursive with
correct connector strokes -- Caveat Bold is a clean, fully-joined, bold
casual-cursive style, genuinely traceable at kid size, but not a classroom
curriculum standard. Listing copy must describe this as "cursive-style
handwriting," never claim curriculum-standard accuracy -- this is a real
truthfulness constraint, same as every compatibility claim elsewhere in
this shop.

Run standalone:
    python tools/generate_grade2_workbook.py
"""
import sys
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.generate_planner import (
    SHOP_NAME,
    _get_fn,
    _bl,
    _new_canvas,
    _page_bg,
    _ML,
    _MR,
    _make_cover_page,
    _merge_pdfs,
)
from tools.generate_planner_v2 import (
    _gradient_header,
    _draw_binding,
    _textured_bg,
    _smart_footer,
)
from tools.glyph_trace import draw_dashed_text, text_width
from tools.generate_tracing_workbook import (
    OUT_DIR,
    CML,
    _trace_row,
    _practice_line,
    _gen_letter_hunt,
    _gen_welcome_page,
    _gen_dashboard_page,
    _gen_index_page,
    _gen_parents_page,
    _gen_reward_chart_page,
    _gen_practice_pages,
    _draw_nav_tabs,
    _stamp_nav_links,
    _assert_nav_labels_renderable,
)

EDU1003 = {
    "title": "Cursive & Skills Workbook",
    "subtitle": "Ocean Breeze — Grade 1-2 Edition",
    "year": None,
    "theme": (0.231, 0.557, 0.541),      # #3B8E8A transformative teal
    "accent": (0.494, 0.784, 0.784),     # #7EC8C8 seafoam
    "bg": (0.941, 0.980, 0.980),         # #F0FAFA morning sea
    "dark": (0.051, 0.208, 0.208),       # #0D3535 deep teal
    "sections": [
        "Welcome & Setup", "Dashboard / Home", "Workbook Index",
        "For Parents & Teachers",
        "Cursive-Style Letter Tracing A-Z × 26", "Grade 1 Sight Words × 5",
        "Sentence Writing × 4", "Addition & Subtraction with Regrouping × 3",
        "Multiplication Facts × 2", "Reward Chart", "Practice Pages × 2",
    ],
    "dashboard_buttons": [
        "For Parents", "Cursive Letters", "Sight Words",
        "Sentences", "Add & Subtract", "Multiplication",
        "Reward Chart", "Practice Pages", "Workbook Index",
    ],
    "nav_tabs": [
        ("HOME", "dashboard"),
        ("Cur", "cursive"),
        ("SPL", "spelling"),
        ("SEN", "sentences"),
        ("+-", "addsub"),
        ("MULT", "mult"),
        ("FUN", "rewards"),
    ],
    # More grown-up nouns than EDU1001/EDU1002's pre-primer set -- real
    # words, matched to a 1st-2nd grader's wider vocabulary rather than
    # reusing the younger-kid set verbatim.
    "letter_words": {
        "A": "Astronaut", "B": "Butterfly", "C": "Castle", "D": "Dolphin",
        "E": "Eagle", "F": "Forest", "G": "Giraffe", "H": "Horse",
        "I": "Island", "J": "Jungle", "K": "Kangaroo", "L": "Lighthouse",
        "M": "Mountain", "N": "Notebook", "O": "Ocean", "P": "Penguin",
        "Q": "Quilt", "R": "Rainbow", "S": "Squirrel", "T": "Turtle",
        "U": "Unicorn", "V": "Volcano", "W": "Whale", "X": "Xylophone",
        "Y": "Yo-yo", "Z": "Zebra",
    },
}

_assert_nav_labels_renderable(EDU1003["nav_tabs"])

CURSIVE_FONT = "caveat"

# Real, standard Dolch FIRST GRADE sight words -- a genuinely distinct,
# harder tier than EDU1001/EDU1002's pre-primer list (not a repeat, not
# invented). First 20 of the well-established 41-word list.
_SIGHT_WORDS_G1 = [
    "after", "again", "any", "ask", "by", "could", "every", "fly", "from",
    "give", "had", "has", "her", "him", "his", "know", "live", "may", "of",
    "old",
]

# Real, grammatically correct, grade-1-2 appropriate sentences using common
# sight words -- not invented facts, just simple correct English.
_SENTENCES = [
    "I can see the sun.",
    "She has a red ball.",
    "We like to play outside.",
    "The dog ran fast today.",
    "My friend is very kind.",
    "He will read a book.",
    "They went to the park.",
    "I know how to swim.",
    "The cat sat on the mat.",
    "We had fun at school.",
    "I love my family.",
    "The sky is very blue.",
]

# Real, correct 2-digit addition/subtraction WITH regrouping (carrying /
# borrowing) -- verified by hand, not generated. Increasing across 3 pages,
# 6 problems/page (3x2 grid) -- the first render used a 4-problem 2x2 grid
# and left roughly two-thirds of the page blank below it, the same "large
# unused blank space" issue Scott caught on EDU1001's letter pages earlier
# this session; 6/page matches the density of every other math page type in
# this shop's tracing-workbook line.
_ADD_REGROUP_PAGES = [
    [(27, 15), (38, 24), (19, 26), (46, 17), (29, 13), (47, 26)],
    [(35, 48), (27, 39), (58, 16), (24, 67), (18, 37), (26, 48)],
]
_SUB_REGROUP_PAGE = [(52, 28), (71, 35), (63, 27), (90, 46), (82, 57), (44, 19)]

# Real, correct single-digit multiplication facts, increasing across 2 pages.
_MULT_PAGES = [
    [(2, 2), (2, 3), (2, 4), (2, 5), (3, 2), (3, 3)],
    [(3, 4), (3, 5), (4, 3), (4, 4), (5, 3), (5, 4)],
]


# ---------------------------------------------------------------------------
# Cursive letter pages
# ---------------------------------------------------------------------------

def _gen_cursive_letter_pages(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    letter_words = pcfg["letter_words"]
    fn = _get_fn()
    chunks = []
    for i, upper in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        lower = upper.lower()
        word = letter_words[upper]
        c, buf, PW, PH = _new_canvas()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        _gradient_header(c, f"CURSIVE {upper}{lower}", T, A, BG, fn, PW, PH,
                          sub=f"Letter {i + 1} of 26 — {word} starts with {upper}")

        ML = CML
        CW = PW - ML - _MR
        top = PH - 58 - 26

        # Real bug caught on the first render of this page (Letter F, uppercase
        # cursive trace overlapping its own "trace it:" label) -- measured
        # Caveat Bold's real glyph bounding boxes via fontTools rather than
        # guess again after EDU1001's earlier ascender/descender bugs: at
        # size_pt=84 its tallest uppercase glyph (N) reaches 62.0pt above
        # baseline and its tallest lowercase glyph reaches 56.4pt -- both
        # MORE than the 46pt gap this page originally used (copied from
        # EDU1001's letter-label-to-trace-row gap, which was fine for
        # Poppins Bold's much shorter caps but not for a script font's tall
        # decorative entry loops). 68pt / 62pt below give real margin above
        # those measured maximums, not just enough to clear one letter.
        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 9)
        c.drawString(ML, top, "Uppercase (cursive-style) — trace it:")
        top -= 68
        _trace_row(c, upper, ML + CW / 2, top, 84, T, DK, count=4, gap=22, font=CURSIVE_FONT)
        top -= 40
        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 9)
        c.drawString(ML, top, "Now write it yourself:")
        top -= 14
        _practice_line(c, ML, top, CW, DK, n_boxes=5)
        top -= 68

        c.setFillColorRGB(*DK)
        c.setFont(fn("bold"), 9)
        c.drawString(ML, top, "Lowercase (cursive-style) — trace it:")
        top -= 62
        _trace_row(c, lower, ML + CW / 2, top, 84, A, DK, count=4, gap=22, font=CURSIVE_FONT)
        top -= 40
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
        c.drawCentredString(ML + CW / 2, top - 16, f"{upper} is for {word}! Trace it in cursive:")
        word_w = text_width(word, 24, font=CURSIVE_FONT)
        draw_dashed_text(c, word, ML + CW / 2 - word_w / 2, top - 50, 24,
                          stroke_rgb=DK, dash=(4, 3), stroke_w=2.0, font=CURSIVE_FONT)
        top -= box_h + 18

        top = _gen_letter_hunt(c, upper, ML, CW, top, T, DK, fn)

        _draw_nav_tabs(c, pcfg, fn, PW, PH, "cursive")
        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="CURSIVE", next_lbl="CURSIVE")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


# ---------------------------------------------------------------------------
# Grade 1 sight words (cursive-style trace + independent write)
# ---------------------------------------------------------------------------

# Real bug found on first render: tracing a whole WORD (not a single big
# letter) in cursive with _trace_row's Poppins-tuned defaults (stroke_w=3.0,
# dash=(6,3)) produced an illegible dark smear -- Caveat's curvy, closely-set
# cursive letterforms overwhelm a stroke that reads fine on one large block
# letter. Two dashed-stroke tuning attempts (a thin 0.9pt hairline, then a
# thicker 1.4pt stroke with wider gaps) both looked clean in this repo's own
# PyMuPDF renders at every DPI tested, but Scott reported BOTH back as
# illegible/choppy on a real iPhone (iOS Quick Look/PDFKit) -- PDF viewers
# are known to handle dashed strokes inconsistently across rendering
# engines, especially at small multi-letter scale where many short dash
# segments sit close together. Rather than keep tuning dash parameters
# blind to how they'll actually render on iOS, switched word/sentence-level
# cursive traces to a SOLID outline (dash=None -- see glyph_trace.py) --
# there's no dash pattern left to fragment or merge, so this sidesteps the
# whole class of problem instead of chasing it. Single large individual
# letters (the actual letter-tracing pages) keep their dashed outline,
# which is the more standard "trace this letterform" convention and has
# never shown this issue.
_CURSIVE_WORD_TRACE = dict(stroke_w=1.6, dash=None, letter_spacing=3.0)


def _gen_sight_word_pages(pcfg, words_per_page=4):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    chunks = []
    n_pages = -(-len(_SIGHT_WORDS_G1) // words_per_page)
    for pi in range(n_pages):
        page_words = _SIGHT_WORDS_G1[pi * words_per_page:(pi + 1) * words_per_page]
        c, buf, PW, PH = _new_canvas()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        _gradient_header(c, "GRADE 1 SIGHT WORDS", T, A, BG, fn, PW, PH,
                          sub=f"Page {pi + 1} of {n_pages} — real Dolch First Grade list")

        ML = CML
        CW = PW - ML - _MR
        top = PH - 58 - 30
        row_h = (top - 60) / len(page_words)
        for word in page_words:
            c.setFillColorRGB(*DK)
            c.setFont(fn("bold"), 9)
            c.drawString(ML, top - 6, word)
            _trace_row(c, word, ML + CW / 2 + 20, top - 26, 34, T, DK, count=3, gap=26,
                       font=CURSIVE_FONT, **_CURSIVE_WORD_TRACE)
            _practice_line(c, ML, top - 46, CW, DK, n_boxes=4)
            top -= row_h

        _draw_nav_tabs(c, pcfg, fn, PW, PH, "spelling")
        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="WORDS", next_lbl="WORDS")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


# ---------------------------------------------------------------------------
# Sentence writing (trace a full sentence in cursive-style, then copy it)
# ---------------------------------------------------------------------------

def _fit_size(text, max_w, start_size, font, min_size=14, letter_spacing=2.0):
    """Shrink start_size until text fits max_w -- text_width scales linearly
    with size_pt for a fixed font, so one division gets the exact fit
    instead of guessing (a hardcoded size would either overflow a long
    sentence off the page or waste space on a short one). letter_spacing
    must match whatever the actual draw call uses, or the fitted size would
    be computed against the wrong width."""
    w = text_width(text, start_size, font=font, letter_spacing=letter_spacing)
    if w <= max_w:
        return start_size
    return max(min_size, start_size * max_w / w)


def _gen_sentence_pages(pcfg, sentences_per_page=3):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    chunks = []
    n_pages = -(-len(_SENTENCES) // sentences_per_page)
    for pi in range(n_pages):
        page_sentences = _SENTENCES[pi * sentences_per_page:(pi + 1) * sentences_per_page]
        c, buf, PW, PH = _new_canvas()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        _gradient_header(c, "SENTENCE WRITING", T, A, BG, fn, PW, PH,
                          sub=f"Page {pi + 1} of {n_pages} — trace it, then write it yourself")

        ML = CML
        CW = PW - ML - _MR
        top = PH - 58 - 30
        block_h = (top - 60) / len(page_sentences)
        for sentence in page_sentences:
            c.setFillColorRGB(*DK)
            c.setFont(fn("bold"), 9)
            c.drawString(ML, top, "Trace it:")
            size = _fit_size(sentence, CW - 20, 28, CURSIVE_FONT,
                              letter_spacing=_CURSIVE_WORD_TRACE["letter_spacing"])
            draw_dashed_text(c, sentence, ML, top - 20 - size * 0.7, size,
                              stroke_rgb=DK, font=CURSIVE_FONT,
                              dash=_CURSIVE_WORD_TRACE["dash"], stroke_w=_CURSIVE_WORD_TRACE["stroke_w"],
                              letter_spacing=_CURSIVE_WORD_TRACE["letter_spacing"])
            y2 = top - 20 - size * 0.7 - 24
            c.setFillColorRGB(*DK)
            c.setFont(fn("bold"), 9)
            c.drawString(ML, y2, "Now write it yourself:")
            _practice_line(c, ML, y2 - 14, CW, DK, n_boxes=1)
            top -= block_h

        _draw_nav_tabs(c, pcfg, fn, PW, PH, "sentences")
        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="SENTENCES", next_lbl="SENTENCES")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


# ---------------------------------------------------------------------------
# Addition & subtraction with regrouping (vertical stacked format)
# ---------------------------------------------------------------------------

def _draw_regroup_problem(c, x, y, a, b, op, fn, DK, T):
    """Standard vertical stacked problem: two right-aligned operands, an
    operator, a rule, and a blank bordered answer box below -- the real
    format regrouping/borrowing is taught in, not a horizontal '=' layout
    (which doesn't leave room to show the carry/borrow work)."""
    w = 90
    c.setFillColorRGB(*DK)
    c.setFont(fn("bold"), 22)
    c.drawRightString(x + w, y, str(a))
    c.drawString(x, y - 32, op)
    c.drawRightString(x + w, y - 32, str(b))
    c.setStrokeColorRGB(*DK)
    c.setLineWidth(1.5)
    c.line(x, y - 42, x + w, y - 42)
    c.setStrokeColorRGB(*_bl(DK, 0.4))
    c.setLineWidth(1.0)
    c.roundRect(x + w / 2 - 30, y - 88, 60, 36, 5, fill=0, stroke=1)


def _gen_regroup_pages(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    pages = [("Addition with Regrouping", "+", probs) for probs in _ADD_REGROUP_PAGES]
    pages.append(("Subtraction with Regrouping", "-", _SUB_REGROUP_PAGE))
    chunks = []
    for pi, (label, op, problems) in enumerate(pages):
        c, buf, PW, PH = _new_canvas()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        _gradient_header(c, label.upper(), T, A, BG, fn, PW, PH, sub=f"Page {pi + 1} of {len(pages)} — solve it")

        ML = CML
        CW = PW - ML - _MR
        top = PH - 58 - 50
        cols, rows = 2, 3
        cell_w = CW / cols
        cell_h = (top - 60) / rows
        for i, (a, b) in enumerate(problems):
            row, col = divmod(i, cols)
            x = ML + col * cell_w + cell_w * 0.25
            y = top - row * cell_h
            _draw_regroup_problem(c, x, y, a, b, op, fn, DK, T)

        _draw_nav_tabs(c, pcfg, fn, PW, PH, "addsub")
        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="ADD/SUB", next_lbl="ADD/SUB")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


# ---------------------------------------------------------------------------
# Multiplication facts (real correct facts + a real dot-array visual aid)
# ---------------------------------------------------------------------------

def _gen_mult_pages(pcfg):
    T, A, BG, DK = pcfg["theme"], pcfg["accent"], pcfg["bg"], pcfg["dark"]
    fn = _get_fn()
    chunks = []
    for pi, problems in enumerate(_MULT_PAGES):
        c, buf, PW, PH = _new_canvas()
        _page_bg(c, BG, PW, PH)
        _textured_bg(c, BG, PW, PH)
        _draw_binding(c, BG, PH)
        _gradient_header(c, "MULTIPLICATION FACTS", T, A, BG, fn, PW, PH,
                          sub=f"Page {pi + 1} of {len(_MULT_PAGES)} — count the dot array to solve")

        ML = CML
        CW = PW - ML - _MR
        top = PH - 58 - 30
        cell_h = (top - 60) / 3
        for i, (a, b) in enumerate(problems):
            row, col = divmod(i, 2)
            x = ML + col * (CW / 2)
            y = top - row * cell_h
            answer = a * b
            c.setFillColorRGB(*DK)
            c.setFont(fn("bold"), 20)
            c.drawString(x + 10, y - 36, f"{a} × {b} =")
            c.setStrokeColorRGB(*_bl(DK, 0.4))
            c.setLineWidth(1.2)
            c.roundRect(x + CW / 2 - 68, y - 58, 40, 30, 5, fill=0, stroke=1)
            # Real a-rows-by-b-columns dot array -- shows WHY the answer is
            # what it is (repeated groups), not just a count-to-N filler.
            dot_r = 4.5
            gap = 13
            gx = x + 10
            gy = y - 76
            for r in range(a):
                for col2 in range(b):
                    c.setFillColorRGB(*_bl(T, 0.3))
                    c.circle(gx + col2 * gap, gy - r * gap, dot_r, fill=1, stroke=0)

        _draw_nav_tabs(c, pcfg, fn, PW, PH, "mult")
        _smart_footer(c, T, A, BG, fn, PW, prev_lbl="MULT", next_lbl="MULT")
        c.showPage()
        c.save()
        chunks.append(buf.getvalue())
    return _merge_pdfs(*chunks)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def build_grade2_workbook():
    pcfg = EDU1003
    cover_cfg = {
        "name": pcfg["title"], "subtitle": pcfg["subtitle"], "year": pcfg.get("year"),
        "bg_rgb": pcfg["bg"], "theme_rgb": pcfg["theme"], "dark_rgb": pcfg["dark"],
    }
    cover_img_path = OUT_DIR / "new_product_covers" / "EDU1003_cursive_skills_ocean_breeze.png"
    cover_pdf_bytes = _make_cover_page(cover_cfg, str(cover_img_path) if cover_img_path.exists() else None)

    named_chunks = [
        ("cover", cover_pdf_bytes),
        ("welcome", _gen_welcome_page(pcfg)),
        ("dashboard", _gen_dashboard_page(pcfg)),
        ("index", _gen_index_page(pcfg)),
        ("parents", _gen_parents_page(pcfg)),
        ("cursive", _gen_cursive_letter_pages(pcfg)),
        ("spelling", _gen_sight_word_pages(pcfg)),
        ("sentences", _gen_sentence_pages(pcfg)),
        ("addsub", _gen_regroup_pages(pcfg)),
        ("mult", _gen_mult_pages(pcfg)),
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
    full = _stamp_nav_links(full, section_start_pages, section_of_page, nav_tabs=pcfg["nav_tabs"])
    out_path = OUT_DIR / "EDU1003.pdf"
    out_path.write_bytes(full)
    return out_path


def main():
    path = build_grade2_workbook()
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(path))
        print(f"EDU1003: {len(reader.pages)} pages, {path.stat().st_size / 1024:.0f} KB -> {path}")
    except Exception as e:
        print(f"EDU1003 saved to {path} (stats unavailable: {e})")


if __name__ == "__main__":
    main()
