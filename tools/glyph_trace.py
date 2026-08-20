"""
glyph_trace.py — real dashed-outline letter/word tracing via actual font
glyph paths, for EDU1001 (Kawaii Interactive Tracing Workbook).

Built 2026-08-20 specifically because the research behind this product line
flagged kawaii kids' worksheets as a SATURATED category where kawaii styling
alone is not a real differentiator -- genuine interactivity is. A gray-filled
letter to color in is what every competitor already ships. A real dashed
outline extracted from the actual glyph shape (not a font-rendering trick or
an approximation) is a genuine step up, and turned out to be entirely
achievable: fontTools can extract a TTF glyph's real bezier outline and
reportlab can stroke it dashed. No other page in this codebase needed this,
so it lives in its own small module rather than bloating generate_planner.py.

Core technique:
  fontTools.pens.reportLabPen.ReportLabPen draws a glyph directly into a
  reportlab.graphics.shapes.Path. Set fillColor=None + strokeDashArray on
  that Path, wrap it in a Drawing, and render it onto a plain pdfgen.Canvas
  via reportlab.graphics.renderPDF.draw() at any position/scale.

Requires the `fonttools` package (not in requirements.txt -- optional/local-
build dependency, same pattern as requirements-sticker.txt's rembg).
"""
from pathlib import Path as _Path

from fontTools.ttLib import TTFont
from fontTools.pens.reportLabPen import ReportLabPen
from reportlab.graphics.shapes import Drawing, Group
from reportlab.graphics import renderPDF
from reportlab.lib.colors import Color

_BASE_DIR = _Path(__file__).resolve().parent.parent

# Font registry, keyed by the short name callers pass as font=. Added
# 2026-08-20 for EDU1003 (1st-2nd grade step-up workbook), which needs a
# second, cursive-style font (Caveat Bold, OFL-licensed) for its cursive
# tracing pages alongside the original Poppins Bold used for print-style
# tracing -- see EDU1001/EDU1002. Every public function below defaults to
# font="poppins" so existing callers that don't pass font= are unaffected.
_FONT_PATHS = {
    "poppins": _BASE_DIR / "assets" / "fonts" / "Poppins-Bold.ttf",
    "caveat": _BASE_DIR / "assets" / "fonts" / "Caveat-Bold.ttf",
}

_loaded: dict = {}


def _ensure_loaded(font: str = "poppins"):
    """Returns (font_obj, glyph_set, cmap, units_per_em) for `font`, loading
    and caching it on first use. Kept as a per-font cache (not a single set
    of globals) so multiple fonts can be in use across one document without
    reloading on every call."""
    if font not in _loaded:
        if font not in _FONT_PATHS:
            raise ValueError(f"unknown glyph_trace font {font!r} -- known: {sorted(_FONT_PATHS)}")
        f = TTFont(str(_FONT_PATHS[font]))
        _loaded[font] = (f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm)
    return _loaded[font]


def glyph_advance_width(char: str, size_pt: float, font: str = "poppins") -> float:
    """Real advance width (font design width, includes normal side bearings)
    for `char` at `size_pt`, in points -- used to lay out multi-char words."""
    _font_obj, glyph_set, cmap, upm = _ensure_loaded(font)
    if ord(char) not in cmap:
        return size_pt * 0.55  # sane fallback for a char with no glyph (space, etc.)
    glyph_name = cmap[ord(char)]
    return glyph_set[glyph_name].width * (size_pt / upm)


def dashed_glyph_group(char: str, size_pt: float, stroke_rgb=(0.2, 0.2, 0.2),
                        dash=(5, 4), stroke_w=2.2, font: str = "poppins"):
    """A reportlab Group containing `char`'s real outline, dashed, scaled to
    size_pt, with its origin at the glyph's own baseline/left-sidebearing --
    i.e. translate the returned group to (x, y) where (x,y) is where the
    character's baseline-left should sit on the page. Returns (group,
    advance_width_pt). Space/unmapped chars return an empty group."""
    _font_obj, glyph_set, cmap, upm = _ensure_loaded(font)
    g = Group()
    if ord(char) not in cmap or char == " ":
        return g, glyph_advance_width(char, size_pt, font=font)
    glyph_name = cmap[ord(char)]
    pen = ReportLabPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    p = pen.path
    scale = size_pt / upm
    # Real bug, confirmed by direct isolation test: strokeWidth/strokeDashArray
    # are geometric properties in the Path's OWN (pre-transform) coordinate
    # space -- Group.scale() later shrinks them right along with the glyph
    # outline. At size_pt=88 that's barely noticeable (3.0 requested -> ~0.26pt
    # actual), but at size_pt=22 (the "trace the word" bonus box) the same
    # "stroke_w=2.0" call ended up under 0.05pt actual, effectively invisible
    # both on screen and -- what Scott actually caught -- on a real printout.
    # Dividing by scale here means the value the CALLER passes is what
    # actually ends up on the page, regardless of glyph size.
    p.fillColor = None
    p.strokeColor = Color(*stroke_rgb)
    p.strokeWidth = stroke_w / scale
    # Dash length must scale by the SAME factor as strokeWidth (both are
    # geometric properties in the Path's pre-transform space, per the comment
    # above) -- confirmed live in two failed attempts before this one: leaving
    # dash un-compensated meant a big glyph (88pt) ends up with a fixed
    # ~3pt-wide stroke but a dash segment that shrank to a fraction of a
    # point, so the "dashes" merged into a dense, beady, near-solid line: the
    # dash length has to be a real multiple of the real stroke width to read
    # as a clean dashed line at ANY glyph size, not a value relative to the
    # glyph's own path length. Compensating both keeps that ratio intact.
    p.strokeDashArray = [d / scale for d in dash]
    g.add(p)
    g.scale(scale, scale)
    return g, glyph_set[glyph_name].width * scale


def draw_dashed_text(c, text: str, x: float, y: float, size_pt: float,
                      stroke_rgb=(0.2, 0.2, 0.2), dash=(5, 4), stroke_w=2.2,
                      letter_spacing=2.0, page_w=None, page_h=None,
                      font: str = "poppins"):
    """Draw `text` as a sequence of real dashed glyph outlines on canvas `c`,
    baseline starting at (x, y). Returns the total width consumed (points)."""
    _ensure_loaded(font)
    page_w = page_w or c._pagesize[0]
    page_h = page_h or c._pagesize[1]
    d = Drawing(page_w, page_h)
    cx = x
    for ch in text:
        grp, adv = dashed_glyph_group(ch, size_pt, stroke_rgb, dash, stroke_w, font=font)
        # A fresh outer group per char: translate must not land on the same
        # Group whose .scale() was already applied inside dashed_glyph_group
        # -- composing translate() onto an already-scaled Group scales the
        # translation too (confirmed live: "the" rendered with all 3 glyphs
        # almost stacked, each only offset by advance*scale instead of the
        # real point-width). Nesting in a positioning-only outer group keeps
        # the two transforms independent.
        positioned = Group(grp)
        positioned.translate(cx, y)
        d.add(positioned)
        cx += adv + letter_spacing
    renderPDF.draw(d, c, 0, 0)
    return cx - x - letter_spacing


def text_width(text: str, size_pt: float, letter_spacing: float = 2.0,
               font: str = "poppins") -> float:
    """Total rendered width of `text` at size_pt, matching draw_dashed_text's
    layout exactly -- use this to center/right-align before drawing."""
    total = 0.0
    for ch in text:
        total += glyph_advance_width(ch, size_pt, font=font) + letter_spacing
    return max(0.0, total - letter_spacing)
