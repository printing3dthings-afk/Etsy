"""
Adds missing pages to the 4 live digital planners (DP1026–DP1029):
  • 3 new FRONT pages: Welcome/Setup, Dashboard/Home, Planner Index
  • Per-product BACK specialty pages (no OpenAI needed)

Run from project root:  python tools/planner_page_adder.py
"""
from __future__ import annotations
import io, os, sys, shutil
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

PRODUCT_FILES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data", "digital_products", "product_files",
)
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
FONTS_DIR  = os.path.join(ASSETS_DIR, "fonts")

# ── Planner configs ──────────────────────────────────────────────────────────

PLANNERS = {
    "DP1026": {
        "title":    "Ultimate Digital Life Planner 2026",
        "subtitle": "Lavender Dreams",
        "year":     2026,
        "theme":    (0.525, 0.400, 0.667),   # #8666AA
        "accent":   (0.769, 0.659, 0.831),   # #C4A8D4
        "bg":       (0.980, 0.969, 1.000),   # #FAF7FF
        "dark":     (0.176, 0.102, 0.247),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Yearly Overview", "Monthly Calendars × 12",
            "Monthly Reviews × 12", "Month at a Glance × 12",
            "Weekly Spreads × 52", "Habit Tracker",
            "Goals", "Budget Tracker", "Meal Planner",
            "Notes × 4", "Year in Pixels",
            "Sticker Library × 5",
        ],
        "specialty_pages": ["year_in_pixels"],
    },
    "DP1027": {
        "title":    "Kawaii Student Planner 2026",
        "subtitle": "Cotton Candy",
        "year":     2026,
        "theme":    (0.871, 0.592, 0.776),   # #DE97C6
        "accent":   (0.592, 0.776, 0.871),   # #97C6DE
        "bg":       (1.000, 0.965, 0.988),   # #FFF6FC
        "dark":     (0.259, 0.102, 0.200),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Yearly Overview", "Monthly Calendars × 12",
            "Monthly Reviews × 12", "Weekly Spreads × 52",
            "Habit Tracker", "Goals", "Notes × 4",
            "Class Schedule", "Brain Dump Pages × 4",
            "Priority Matrix", "Pomodoro Focus Tracker",
            "Sticker Library × 5",
        ],
        "specialty_pages": ["class_schedule", "brain_dump", "priority_matrix", "pomodoro"],
    },
    "DP1028": {
        "title":    "Digital Budget & Finance Planner 2026",
        "subtitle": "Midnight Blue",
        "year":     2026,
        "theme":    (0.106, 0.145, 0.408),   # #1B2568
        "accent":   (0.482, 0.655, 0.761),   # #7BA7C2
        "bg":       (0.941, 0.961, 1.000),   # #F0F5FF
        "dark":     (0.051, 0.067, 0.200),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Yearly Overview", "Monthly Calendars × 12",
            "Monthly Reviews × 12", "Month at a Glance × 12",
            "Weekly Spreads × 52", "Budget Tracker × 12",
            "Goals", "Debt Payoff Tracker",
            "Savings Goal Tracker", "Bill Payment Checklist",
            "Notes × 4", "Sticker Library × 5",
        ],
        "specialty_pages": ["debt_payoff", "savings_goal", "bill_checklist"],
    },
    "DP1029": {
        "title":    "Kawaii Fitness & Wellness Planner 2026",
        "subtitle": "Coral Peach",
        "year":     2026,
        "theme":    (0.992, 0.424, 0.286),   # #FD6C49
        "accent":   (0.961, 0.722, 0.471),   # #F5B878
        "bg":       (1.000, 0.973, 0.957),   # #FFF8F4
        "dark":     (0.380, 0.145, 0.090),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Yearly Overview", "Monthly Calendars × 12",
            "Monthly Reviews × 12", "Weekly Spreads × 52",
            "Habit Tracker", "Meal Planner",
            "Goals", "Progress Photos Log",
            "30-Day Water Tracker", "Sleep Quality Log",
            "Non-Scale Victories", "Notes × 4",
            "Sticker Library × 5",
        ],
        "specialty_pages": ["progress_photos", "water_tracker", "sleep_log", "nsv_journal"],
    },
}

SUPPORT_EMAIL = "Printing3dthings@outlook.com"
SHOP_NAME     = "OnBrandCraftz"

# ── ReportLab helpers ────────────────────────────────────────────────────────

def _get_canvas_and_fonts():
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.colors import Color
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_map = {}
    for fname, ffile in {
        "Poppins": "Poppins-Regular.ttf",
        "Poppins-Bold": "Poppins-Bold.ttf",
        "Poppins-SemiBold": "Poppins-SemiBold.ttf",
        "Poppins-Italic": "Poppins-Italic.ttf",
    }.items():
        fp = os.path.join(FONTS_DIR, ffile)
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont(fname, fp))
                font_map[fname] = fname
            except Exception:
                pass

    def fn(variant="regular"):
        v = variant.lower()
        if v in ("bold", "b"):
            return font_map.get("Poppins-Bold", "Helvetica-Bold")
        if v in ("semibold", "sb"):
            return font_map.get("Poppins-SemiBold", font_map.get("Poppins-Bold", "Helvetica-Bold"))
        if v in ("italic", "i"):
            return font_map.get("Poppins-Italic", "Helvetica-Oblique")
        return font_map.get("Poppins", "Helvetica")

    return pdf_canvas, LETTER, Color, fn


def _make_pages(cfg: dict, page_type: str, specialty: str = "") -> bytes:
    """Return a PDF (as bytes) containing requested new pages."""
    pdf_canvas, LETTER, Color, fn = _get_canvas_and_fonts()

    buf = io.BytesIO()
    PW, PH = LETTER
    T  = cfg["theme"]
    A  = cfg["accent"]
    BG = cfg["bg"]
    DK = cfg["dark"]

    c = pdf_canvas.Canvas(buf, pagesize=(PW, PH))

    def fill(rgb):   c.setFillColorRGB(*rgb)
    def stroke(rgb): c.setStrokeColorRGB(*rgb)
    def font(n, s):  c.setFont(n, s)
    def lw(w):       c.setLineWidth(w)

    def blend(rgb, f):
        return tuple(x + (1.0 - x) * f for x in rgb)

    TL = blend(T, 0.80)
    AL = blend(A, 0.70)
    ML = MR = 36.0
    MT = MB = 32.0
    CW = PW - ML - MR

    def header_band(label: str, y_top: float = PH - MT, h: float = 52):
        fill(T); c.rect(0, y_top - h, PW, h, fill=1, stroke=0)
        fill(BG); font(fn("bold"), 18)
        c.drawCentredString(PW / 2, y_top - h + 18, label)

    def footer_bar():
        fill(T); c.rect(0, 0, PW, 24, fill=1, stroke=0)
        fill(BG); font(fn("regular"), 8)
        c.drawCentredString(PW / 2, 8, f"© {SHOP_NAME} — Personal use only")

    def section_box(x, y, w, h, label, sublabel="", color=None):
        bc = color or T
        bl = blend(bc, 0.85)
        fill(bl); lw(0); c.roundRect(x, y, w, h, 6, fill=1, stroke=0)
        fill(bc); lw(0.5); c.roundRect(x, y, w, h, 6, fill=0, stroke=1)
        fill(DK); font(fn("bold"), 10)
        ty = y + h / 2 + (5 if sublabel else 0)
        c.drawCentredString(x + w / 2, ty, label)
        if sublabel:
            fill(DK); font(fn("regular"), 7.5)
            c.drawCentredString(x + w / 2, ty - 13, sublabel)

    def divider(y):
        fill(blend(T, 0.88)); lw(0); c.rect(ML, y, CW, 1, fill=1, stroke=0)

    # ════════════════════════════════════════════════════════════
    #  WELCOME PAGE
    # ════════════════════════════════════════════════════════════
    if page_type == "welcome":
        # Top accent bar
        fill(T); c.rect(0, PH - 8, PW, 8, fill=1, stroke=0)
        fill(A); c.rect(0, PH - 14, PW, 6, fill=1, stroke=0)

        # Title block
        y = PH - 72
        fill(T); font(fn("bold"), 28)
        c.drawCentredString(PW / 2, y, "Welcome!")
        y -= 24
        fill(DK); font(fn("semibold"), 13)
        c.drawCentredString(PW / 2, y, cfg["title"])
        y -= 16
        fill(T); font(fn("italic"), 10)
        c.drawCentredString(PW / 2, y, f"{cfg['subtitle']} — {cfg['year']} + Undated Edition")

        # Decorative line
        y -= 14
        fill(A); lw(0); c.rect(ML + CW * 0.2, y, CW * 0.6, 2, fill=1, stroke=0)
        y -= 22

        # ── Section 1: Download instructions ──
        fill(T); font(fn("bold"), 13); c.drawString(ML, y, "📥  HOW TO DOWNLOAD YOUR FILES")
        y -= 18; divider(y); y -= 14
        steps = [
            "1.  Go to your Etsy account → Purchases & Reviews",
            "2.  Find this order and click \"Download Files\"",
            "3.  Save the PDF and ZIP file to your device",
        ]
        for s in steps:
            fill(DK); font(fn("regular"), 10); c.drawString(ML + 12, y, s)
            y -= 16
        y -= 6

        # ── Section 2: GoodNotes import ──
        fill(T); font(fn("bold"), 13); c.drawString(ML, y, "📱  OPEN IN GOODNOTES 6")
        y -= 18; divider(y); y -= 14
        gn_steps = [
            "1.  Open GoodNotes 6 → tap the + button",
            "2.  Choose \"Import\" and select the PDF file",
            "3.  Tap any text box to type  ·  Use the side tabs to navigate",
        ]
        for s in gn_steps:
            fill(DK); font(fn("regular"), 10); c.drawString(ML + 12, y, s)
            y -= 16
        y -= 6

        # ── Section 3: Notability ──
        fill(T); font(fn("bold"), 13); c.drawString(ML, y, "📒  OPEN IN NOTABILITY")
        y -= 18; divider(y); y -= 14
        nb_steps = [
            "1.  Open Notability → tap + → Import",
            "2.  Select the PDF → it opens as a new note",
            "3.  Tap any field to type  ·  Annotate freely with Apple Pencil",
        ]
        for s in nb_steps:
            fill(DK); font(fn("regular"), 10); c.drawString(ML + 12, y, s)
            y -= 16
        y -= 6

        # ── Section 4: Sticker import ──
        fill(T); font(fn("bold"), 13); c.drawString(ML, y, "🎨  IMPORT YOUR STICKER PACK")
        y -= 18; divider(y); y -= 14
        st_steps = [
            "1.  Unzip the sticker pack ZIP file",
            "2.  In GoodNotes: Elements → Stickers tab → + → select all 5 PNG sheets",
            "3.  Stickers appear in your library — drag onto any page, unlimited times!",
        ]
        for s in st_steps:
            fill(DK); font(fn("regular"), 10); c.drawString(ML + 12, y, s)
            y -= 16
        y -= 6

        # ── Section 5: Compatible apps ──
        fill(T); font(fn("bold"), 13); c.drawString(ML, y, "✅  COMPATIBLE APPS")
        y -= 18; divider(y); y -= 14
        apps = ["GoodNotes 6  ·  Notability  ·  PDF Expert  ·  Xodo  ·  Adobe Acrobat Reader"]
        for s in apps:
            fill(DK); font(fn("regular"), 10); c.drawCentredString(PW / 2, y, s)
            y -= 16
        y -= 6

        # ── Support block ──
        fill(blend(T, 0.92))
        c.roundRect(ML, y - 38, CW, 44, 6, fill=1, stroke=0)
        fill(DK); font(fn("bold"), 10)
        c.drawCentredString(PW / 2, y - 10, "Questions? We're here to help!")
        font(fn("regular"), 9.5)
        c.drawCentredString(PW / 2, y - 24, f"Email: {SUPPORT_EMAIL}")
        font(fn("italic"), 8.5)
        c.drawCentredString(PW / 2, y - 36, "We reply within 24 hours, 7 days a week.")

        footer_bar()
        c.showPage()

    # ════════════════════════════════════════════════════════════
    #  DASHBOARD PAGE
    # ════════════════════════════════════════════════════════════
    elif page_type == "dashboard":
        # Full background
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

        # Top colored header band
        fill(T); c.rect(0, PH - 80, PW, 80, fill=1, stroke=0)
        fill(BG); font(fn("bold"), 24)
        c.drawCentredString(PW / 2, PH - 48, "🏠  DASHBOARD")
        fill(blend(BG, -0.1)); font(fn("italic"), 10)
        c.drawCentredString(PW / 2, PH - 66, f"{cfg['title']}  ·  {cfg['subtitle']}")

        y = PH - 80 - 22

        # Instruction note
        fill(DK); font(fn("italic"), 8.5)
        c.drawCentredString(PW / 2, y, "Use the side navigation tabs to jump to any section. Tap 🏠 HOME in the footer of any page to return here.")
        y -= 18

        # Section grid — 3 columns × rows
        sections_display = [s for s in cfg["sections"] if s not in ("Welcome & Setup", "Dashboard / Home", "Planner Index")]

        col_w = (CW - 16) / 3
        row_h = 52
        gap   = 8
        cols  = 3

        x_starts = [ML + i * (col_w + gap) for i in range(cols)]

        # Color cycle for section buttons
        colors = [T, A, blend(T, 0.3), blend(A, 0.3), blend(T, 0.6)]

        for idx, sect in enumerate(sections_display):
            col = idx % cols
            row = idx // cols
            bx  = x_starts[col]
            by  = y - (row + 1) * (row_h + gap)
            ci  = idx % len(colors)
            section_box(bx, by, col_w, row_h, sect, color=colors[ci])

        # Bottom "Sticker Library" full-width button
        n_rows = -(-len(sections_display) // cols)  # ceiling div
        bottom_y = y - n_rows * (row_h + gap) - gap

        # Contact + navigation reminder
        if bottom_y > MB + 60:
            fill(blend(T, 0.90))
            c.roundRect(ML, MB + 12, CW, 40, 6, fill=1, stroke=0)
            fill(DK); font(fn("bold"), 9)
            c.drawCentredString(PW / 2, MB + 36, "TIP: The side navigation tabs are always visible — tap any tab to jump to that section.")
            font(fn("regular"), 8.5)
            c.drawCentredString(PW / 2, MB + 22, f"Support: {SUPPORT_EMAIL}  ·  © {SHOP_NAME}")

        footer_bar()
        c.showPage()

    # ════════════════════════════════════════════════════════════
    #  PLANNER INDEX PAGE
    # ════════════════════════════════════════════════════════════
    elif page_type == "index":
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)

        header_band("PLANNER INDEX")
        y = PH - MT - 52 - 18

        fill(DK); font(fn("italic"), 9)
        c.drawCentredString(PW / 2, y, "Use the side navigation tabs or the 🏠 HOME button to jump to any section.")
        y -= 24

        # Two-column section list
        half_sections = len(cfg["sections"]) // 2 + len(cfg["sections"]) % 2
        col1 = cfg["sections"][:half_sections]
        col2 = cfg["sections"][half_sections:]
        col_w = CW / 2 - 8
        row_h_idx = 20

        for i in range(max(len(col1), len(col2))):
            row_y = y - i * row_h_idx
            # Left col
            if i < len(col1):
                sect = col1[i]
                num  = i + 1
                fill(T); font(fn("bold"), 9)
                c.drawString(ML, row_y, f"{num:02d}.")
                fill(DK); font(fn("regular"), 9.5)
                c.drawString(ML + 24, row_y, sect)
                fill(blend(T, 0.80))
                lw(0.3); c.line(ML + 24, row_y - 2, ML + col_w, row_y - 2)

            # Right col
            if i < len(col2):
                sect = col2[i]
                num  = half_sections + i + 1
                rx   = ML + CW / 2 + 8
                fill(T); font(fn("bold"), 9)
                c.drawString(rx, row_y, f"{num:02d}.")
                fill(DK); font(fn("regular"), 9.5)
                c.drawString(rx + 24, row_y, sect)
                fill(blend(T, 0.80))
                lw(0.3); c.line(rx + 24, row_y - 2, ML + CW, row_y - 2)

        # Bottom note
        bottom_note_y = y - max(len(col1), len(col2)) * row_h_idx - 16
        if bottom_note_y > MB + 30:
            fill(blend(T, 0.92))
            c.roundRect(ML, MB + 8, CW, 36, 6, fill=1, stroke=0)
            fill(DK); font(fn("italic"), 8.5)
            c.drawCentredString(PW / 2, MB + 25,
                "Both the 2026 Dated version AND the Undated Evergreen version are included in your download.")
            c.drawCentredString(PW / 2, MB + 12, f"© {SHOP_NAME} — Personal use only — {SUPPORT_EMAIL}")

        footer_bar()
        c.showPage()

    # ════════════════════════════════════════════════════════════
    #  SPECIALTY PAGES
    # ════════════════════════════════════════════════════════════
    elif page_type == "specialty":
        _draw_specialty_pages(c, cfg, specialty, PW, PH, ML, MR, MT, MB, CW, T, A, BG, DK, fn, lw, fill, stroke, blend, divider, header_band, footer_bar, section_box)

    c.save()
    return buf.getvalue()


def _draw_specialty_pages(c, cfg, specialty, PW, PH, ML, MR, MT, MB, CW,
                           T, A, BG, DK, fn, lw, fill, stroke, blend,
                           divider, header_band, footer_bar, section_box):
    """Draw one or more specialty pages on canvas c."""

    def cell_grid(x, y, cols, rows, cw, rh, labels_top=None, labels_left=None, color=None):
        """Draw a filled grid of cells."""
        bc = color or T
        bl = blend(bc, 0.88)
        for r in range(rows):
            for col in range(cols):
                cx = x + col * cw
                cy = y - r * rh
                fill(bl if (r + col) % 2 == 0 else (1, 1, 1))
                lw(0.3); stroke(blend(bc, 0.60))
                c.rect(cx, cy - rh, cw, rh, fill=1, stroke=1)
        # Column headers
        if labels_top:
            for i, lbl in enumerate(labels_top):
                fill(bc); c.rect(x + i * cw, y, cw, 14, fill=1, stroke=0)
                fill((1,1,1)); c.setFont(fn("bold"), 7)
                c.drawCentredString(x + i * cw + cw / 2, y + 4, str(lbl))
        # Row headers
        if labels_left:
            for i, lbl in enumerate(labels_left):
                fill(blend(bc, 0.70)); c.rect(x - 68, y - i * rh - rh, 68, rh, fill=1, stroke=0)
                fill(DK); c.setFont(fn("regular"), 7)
                c.drawString(x - 64, y - i * rh - rh + 5, str(lbl)[:12])

    # ── YEAR IN PIXELS (DP1026) ──────────────────────────────────────────────
    if specialty == "year_in_pixels":
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
        header_band("✨  YEAR IN PIXELS  —  2026")
        y = PH - MT - 52 - 16

        fill(DK); c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2, y, "Color one box per day based on your mood or theme. Create your own color key below!")
        y -= 20

        # Color key
        key_colors = [T, A, (0.576, 0.773, 0.576), (0.984, 0.757, 0.369), (0.800, 0.800, 0.800)]
        key_labels = ["Happy / Great", "Calm / Content", "Growing / Grateful", "Tired / Stressed", "Neutral / Rest"]
        kx = ML; ky = y
        for i, (kc, kl) in enumerate(zip(key_colors, key_labels)):
            fill(kc); c.rect(kx + i * (CW / 5), ky - 14, 14, 14, fill=1, stroke=0)
            fill(DK); c.setFont(fn("regular"), 7.5)
            c.drawString(kx + i * (CW / 5) + 17, ky - 9, kl)

        # "Add your own" row
        kx2 = ML; ky2 = ky - 24
        fill(DK); c.setFont(fn("italic"), 7.5)
        c.drawString(kx2, ky2 - 9, "Your colors:")
        for i in range(5):
            lw(0.5); stroke(blend(T, 0.60))
            c.rect(kx2 + 80 + i * 60, ky2 - 14, 40, 14, fill=0, stroke=1)
            c.setFont(fn("regular"), 7); fill(blend(DK, 0.40))
            c.drawString(kx2 + 80 + i * 60 + 42, ky2 - 8, "= ___________")

        y = ky2 - 30

        # 12-month pixel grid
        MONTHS_SHORT = ["JAN","FEB","MAR","APR","MAY","JUN",
                        "JUL","AUG","SEP","OCT","NOV","DEC"]
        DAYS_IN_MONTH = [31,28,29,31,30,31,30,31,31,30,31,30,31]  # 2026 (not a leap year)
        cell_w = (CW - 72) / 31
        cell_h = 14.0
        lx = ML + 72  # left edge of day cells

        for mi, (mon, days) in enumerate(zip(MONTHS_SHORT, DAYS_IN_MONTH[1:])):
            row_y = y - mi * (cell_h + 1)
            # Month label
            fill(T); c.rect(ML, row_y - cell_h, 68, cell_h, fill=1, stroke=0)
            fill((1,1,1)); c.setFont(fn("bold"), 8)
            c.drawCentredString(ML + 34, row_y - cell_h + 4, mon)
            # Day cells
            for d in range(31):
                cx = lx + d * (cell_w + 0)
                if d < days:
                    fill(blend(T, 0.93) if d % 2 == 0 else (1,1,1))
                else:
                    fill(blend(DK, 0.93))
                lw(0.3); stroke(blend(T, 0.70))
                c.rect(cx, row_y - cell_h, cell_w, cell_h, fill=1, stroke=1)
                if d < days:
                    fill(blend(DK, 0.50)); c.setFont(fn("regular"), 5.5)
                    c.drawCentredString(cx + cell_w / 2, row_y - cell_h + 2, str(d + 1))

        # Day number header
        hrow_y = y + cell_h / 2
        for d in range(31):
            cx = lx + d * cell_w
            fill(DK); c.setFont(fn("bold"), 5.5)
            c.drawCentredString(cx + cell_w / 2, hrow_y, str(d + 1))

        footer_bar()
        c.showPage()

    # ── CLASS SCHEDULE (DP1027) ──────────────────────────────────────────────
    elif specialty == "class_schedule":
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
        header_band("📚  CLASS SCHEDULE")
        y = PH - MT - 52 - 16

        # Semester selector
        fill(DK); c.setFont(fn("bold"), 10); c.drawString(ML, y, "Semester: ")
        for i, lbl in enumerate(["Fall 2026", "Spring 2027", "Summer 2027"]):
            bx = ML + 80 + i * 130
            fill(blend(T, 0.88)); c.roundRect(bx, y - 3, 115, 16, 4, fill=1, stroke=0)
            fill(T); lw(0.5); c.roundRect(bx, y - 3, 115, 16, 4, fill=0, stroke=1)
            fill(DK); c.setFont(fn("regular"), 9); c.drawCentredString(bx + 57, y + 5, lbl)

        y -= 30

        # Grid
        DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
        TIMES = ["8:00 AM","9:00 AM","10:00 AM","11:00 AM","12:00 PM",
                  "1:00 PM","2:00 PM","3:00 PM","4:00 PM","5:00 PM","6:00 PM"]
        tw = 52   # time col width
        dw = (CW - tw) / len(DAYS)
        rh = (PH - y - MB - 30) / len(TIMES)

        # Header
        fill(T); c.rect(ML, y - 18, CW, 18, fill=1, stroke=0)
        fill((1,1,1)); c.setFont(fn("bold"), 9)
        for i, d in enumerate(DAYS):
            c.drawCentredString(ML + tw + i * dw + dw / 2, y - 13, d)

        for ri, t in enumerate(TIMES):
            ry = y - 18 - (ri + 1) * rh
            # Time label
            fill(blend(T, 0.80)); c.rect(ML, ry, tw, rh, fill=1, stroke=0)
            fill(DK); c.setFont(fn("regular"), 7.5)
            c.drawCentredString(ML + tw / 2, ry + rh / 2 - 4, t)
            # Day cells
            for di in range(len(DAYS)):
                cx = ML + tw + di * dw
                fill(blend(T, 0.95) if (ri + di) % 2 == 0 else (1,1,1))
                lw(0.3); stroke(blend(T, 0.60))
                c.rect(cx, ry, dw, rh, fill=1, stroke=1)

        footer_bar()
        c.showPage()

    # ── BRAIN DUMP (DP1027) ──────────────────────────────────────────────────
    elif specialty == "brain_dump":
        for _ in range(4):  # 4 Brain Dump pages
            fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
            header_band("🧠  BRAIN DUMP")
            y = PH - MT - 52 - 14
            fill(DK); c.setFont(fn("italic"), 9)
            c.drawCentredString(PW / 2, y, "Get it all out of your head and onto paper. No order, no judgment — just dump everything here.")
            y -= 22
            fill(DK); c.setFont(fn("bold"), 9); c.drawString(ML, y, "Date: ________________   Topic / Context: ________________________________")
            y -= 20
            # Dot grid
            dot_spacing = 18
            cols_d = int(CW / dot_spacing)
            rows_d = int((y - MB - 30) / dot_spacing)
            for r in range(rows_d):
                for col_d in range(cols_d):
                    dx = ML + col_d * dot_spacing + dot_spacing / 2
                    dy = y - r * dot_spacing - dot_spacing / 2
                    fill(blend(T, 0.65)); c.circle(dx, dy, 1.2, fill=1, stroke=0)
            footer_bar()
            c.showPage()

    # ── PRIORITY MATRIX (DP1027) ─────────────────────────────────────────────
    elif specialty == "priority_matrix":
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
        header_band("⚡  PRIORITY MATRIX")
        y = PH - MT - 52 - 16
        fill(DK); c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2, y, "Urgent × Important quadrant — schedule, delegate, do now, or drop.")
        y -= 20
        fill(DK); c.setFont(fn("bold"), 9); c.drawString(ML, y, "Week of: ________________________")
        y -= 22

        qw = CW / 2 - 4; qh = (y - MB - 30) / 2
        quads = [
            ("DO FIRST\n(Urgent + Important)", T),
            ("SCHEDULE\n(Not Urgent + Important)", A),
            ("DELEGATE\n(Urgent + Not Important)", blend(T, 0.40)),
            ("DROP / LATER\n(Not Urgent + Not Important)", blend(A, 0.40)),
        ]
        positions = [
            (ML, y - qh),
            (ML + qw + 8, y - qh),
            (ML, y - 2 * qh - 4),
            (ML + qw + 8, y - 2 * qh - 4),
        ]

        # Axis labels
        fill(DK); c.setFont(fn("bold"), 8)
        c.drawCentredString(ML + CW / 4, y + 8, "URGENT")
        c.drawCentredString(ML + 3 * CW / 4, y + 8, "NOT URGENT")
        # Rotate for Y axis labels (draw as text blocks)
        c.saveState()
        c.translate(ML - 16, y - qh)
        c.rotate(90)
        c.drawCentredString(0, 0, "IMPORTANT")
        c.restoreState()
        c.saveState()
        c.translate(ML - 16, y - 2 * qh - 4)
        c.rotate(90)
        c.drawCentredString(0, 0, "NOT IMPORTANT")
        c.restoreState()

        for (qx, qy), (qlbl, qcol) in zip(positions, quads):
            fill(blend(qcol, 0.88)); lw(0)
            c.roundRect(qx, qy, qw, qh, 6, fill=1, stroke=0)
            fill(qcol); lw(0.8)
            c.roundRect(qx, qy, qw, qh, 6, fill=0, stroke=1)
            # Header
            fill(qcol); c.rect(qx, qy + qh - 22, qw, 22, fill=1, stroke=0)
            fill((1,1,1)); c.setFont(fn("bold"), 8)
            lines = qlbl.split("\n")
            c.drawCentredString(qx + qw / 2, qy + qh - 11 - (4 if len(lines) > 1 else 0), lines[0])
            if len(lines) > 1:
                c.setFont(fn("regular"), 7); c.drawCentredString(qx + qw / 2, qy + qh - 20, lines[1])
            # Lines for writing
            line_h = 16; lines_n = int((qh - 28) / line_h)
            for li in range(lines_n):
                ly = qy + qh - 28 - li * line_h - 4
                fill(blend(qcol, 0.60)); lw(0.3)
                c.line(qx + 8, ly, qx + qw - 8, ly)

        footer_bar()
        c.showPage()

    # ── POMODORO TRACKER (DP1027) ────────────────────────────────────────────
    elif specialty == "pomodoro":
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
        header_band("🍅  POMODORO FOCUS TRACKER")
        y = PH - MT - 52 - 16
        fill(DK); c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2, y, "25 min work · 5 min break · After 4 pomodoros take a 20–30 min break")
        y -= 22

        # 8 sessions × 4 rows = 32 pomodoro slots per page
        session_h = (y - MB - 30) / 8
        for si in range(8):
            sy = y - si * session_h
            # Session label
            fill(T); c.rect(ML, sy - session_h, 60, session_h, fill=1, stroke=0)
            fill((1,1,1)); c.setFont(fn("bold"), 8)
            c.drawCentredString(ML + 30, sy - session_h / 2 - 4, f"Session {si + 1}")
            # Task field
            fill(blend(T, 0.93)); c.rect(ML + 62, sy - session_h, CW * 0.40, session_h, fill=1, stroke=0)
            fill(DK); c.setFont(fn("italic"), 7.5)
            c.drawString(ML + 66, sy - session_h + 6, "Task: _______________________________")
            # 4 pomodoro circles
            for pi in range(4):
                px = ML + CW * 0.42 + 62 + pi * 44
                py = sy - session_h / 2
                fill(blend(T, 0.80)); lw(0.5); stroke(T)
                c.circle(px, py, 16, fill=1, stroke=1)
                fill(T); c.setFont(fn("bold"), 7); c.drawCentredString(px, py - 4, "25m")
            # Break checkbox
            bx = ML + CW - 40
            fill(blend(A, 0.80)); c.roundRect(bx, sy - session_h + 6, 34, 16, 3, fill=1, stroke=0)
            fill(DK); c.setFont(fn("regular"), 7)
            c.drawCentredString(bx + 17, sy - session_h + 13, "Break ✓")

        footer_bar()
        c.showPage()

    # ── DEBT PAYOFF TRACKER (DP1028) ─────────────────────────────────────────
    elif specialty == "debt_payoff":
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
        header_band("💳  DEBT PAYOFF TRACKER")
        y = PH - MT - 52 - 16
        fill(DK); c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2, y, "List each debt. Pay minimums on all, then throw every extra dollar at the smallest (Snowball) or highest-rate (Avalanche) debt.")
        y -= 22

        # Debt rows
        COLS = ["Debt Name", "Lender", "Balance", "Min Payment", "Interest %", "Target Date", "✓ Paid Off"]
        col_widths = [90, 70, 55, 65, 55, 60, 50]
        header_h = 18; row_h_debt = 24
        rows_n = int((y - MB - 50) / row_h_debt)

        # Header row
        hx = ML
        for cw2, cl in zip(col_widths, COLS):
            fill(T); c.rect(hx, y - header_h, cw2, header_h, fill=1, stroke=0)
            fill((1,1,1)); c.setFont(fn("bold"), 7.5)
            c.drawCentredString(hx + cw2 / 2, y - 13, cl)
            hx += cw2

        for ri in range(rows_n):
            rx = ML; ry = y - header_h - (ri + 1) * row_h_debt
            for cw2 in col_widths:
                fill(blend(T, 0.94) if ri % 2 == 0 else (1, 1, 1))
                lw(0.3); stroke(blend(T, 0.60))
                c.rect(rx, ry, cw2, row_h_debt, fill=1, stroke=1)
                rx += cw2

        # Total row
        total_y = y - header_h - (rows_n + 1) * row_h_debt
        fill(blend(T, 0.70)); c.rect(ML, total_y, sum(col_widths), row_h_debt, fill=1, stroke=0)
        fill(DK); c.setFont(fn("bold"), 9); c.drawString(ML + 8, total_y + 8, "TOTAL DEBT:")
        c.drawString(ML + sum(col_widths[:3]) - 30, total_y + 8, "$__________")

        # Victory box
        vby = total_y - 38
        fill(blend(A, 0.80)); c.roundRect(ML, vby, CW, 30, 6, fill=1, stroke=0)
        fill(DK); c.setFont(fn("bold"), 11)
        c.drawCentredString(PW / 2, vby + 16, "🎉  My Debt-Free Date Goal:  ________________________________")

        footer_bar()
        c.showPage()

    # ── SAVINGS GOAL TRACKER (DP1028) ────────────────────────────────────────
    elif specialty == "savings_goal":
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
        header_band("🏦  SAVINGS GOAL TRACKER")
        y = PH - MT - 52 - 16
        fill(DK); c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2, y, "Set your goal, color in each milestone as you hit it. Watch your savings grow!")
        y -= 20

        # 4 savings goals per page
        goal_h = (y - MB - 20) / 4 - 8
        for gi in range(4):
            gy = y - gi * (goal_h + 8)
            # Goal header
            fill(blend(T, 0.88)); c.roundRect(ML, gy - goal_h, CW, goal_h, 6, fill=1, stroke=0)
            fill(T); lw(0.8); c.roundRect(ML, gy - goal_h, CW, goal_h, 6, fill=0, stroke=1)
            fill(DK); c.setFont(fn("bold"), 9)
            c.drawString(ML + 8, gy - 16, f"Goal {gi + 1}: _______________________   Target: $____________   Date: ____________")
            # Thermometer bar (20 segments)
            seg_w = (CW - 40) / 20; seg_h = goal_h - 30; seg_x = ML + 20
            seg_y = gy - goal_h + 10
            for si in range(20):
                pct = (si + 1) * 5
                fill(blend(T, 0.88) if si < 10 else blend(A, 0.80))
                lw(0.4); stroke(T)
                c.rect(seg_x + si * seg_w, seg_y, seg_w - 1, seg_h, fill=1, stroke=1)
                fill(DK); c.setFont(fn("bold"), 6)
                c.drawCentredString(seg_x + si * seg_w + seg_w / 2, seg_y + 2, f"{pct}%")

        footer_bar()
        c.showPage()

    # ── BILL PAYMENT CHECKLIST (DP1028) ──────────────────────────────────────
    elif specialty == "bill_checklist":
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
        header_band("📋  MONTHLY BILL PAYMENT CHECKLIST")
        y = PH - MT - 52 - 16
        fill(DK); c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2, y, "Check off each bill as you pay it. Never miss a due date again.")
        y -= 22

        MONTHS_SHORT = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
        bill_col_w = 110; month_col_w = (CW - bill_col_w) / 12
        header_h2 = 16; bill_rows = int((y - MB - 20) / 20)

        # Header
        fill(T); c.rect(ML, y - header_h2, bill_col_w, header_h2, fill=1, stroke=0)
        fill((1,1,1)); c.setFont(fn("bold"), 8); c.drawCentredString(ML + bill_col_w / 2, y - 12, "Bill Name")
        for mi, mon in enumerate(MONTHS_SHORT):
            mx = ML + bill_col_w + mi * month_col_w
            fill(T if mi % 2 == 0 else blend(T, 0.30))
            c.rect(mx, y - header_h2, month_col_w, header_h2, fill=1, stroke=0)
            fill((1,1,1)); c.setFont(fn("bold"), 6.5)
            c.drawCentredString(mx + month_col_w / 2, y - 12, mon)

        for ri in range(bill_rows):
            ry = y - header_h2 - (ri + 1) * 20
            fill(blend(T, 0.94) if ri % 2 == 0 else (1, 1, 1))
            lw(0.3); stroke(blend(T, 0.60))
            c.rect(ML, ry, bill_col_w, 20, fill=1, stroke=1)
            for mi in range(12):
                mx = ML + bill_col_w + mi * month_col_w
                c.rect(mx, ry, month_col_w, 20, fill=1, stroke=1)

        footer_bar()
        c.showPage()

    # ── PROGRESS PHOTOS LOG (DP1029) ─────────────────────────────────────────
    elif specialty == "progress_photos":
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
        header_band("📸  PROGRESS PHOTOS LOG")
        y = PH - MT - 52 - 14
        fill(DK); c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2, y, "Take photos on the same day each month in the same lighting and pose. Progress is real even when the scale doesn't move!")
        y -= 22

        # 4 check-in blocks per page (3-month interval)
        block_h = (y - MB - 20) / 4 - 8
        checkpoints = ["Starting Point", "Month 3 Check-in", "Month 6 Check-in", "Month 9 Check-in"]
        for bi, label in enumerate(checkpoints):
            by = y - bi * (block_h + 8)
            fill(blend(T, 0.88)); c.roundRect(ML, by - block_h, CW, block_h, 6, fill=1, stroke=0)
            fill(T); lw(0.8); c.roundRect(ML, by - block_h, CW, block_h, 6, fill=0, stroke=1)
            # Title
            fill(T); c.rect(ML, by - 22, CW, 22, fill=1, stroke=0)
            fill((1,1,1)); c.setFont(fn("bold"), 10); c.drawString(ML + 10, by - 16, label)
            fill(blend(BG, -0.1)); c.setFont(fn("regular"), 8)
            c.drawString(ML + 160, by - 16, "Date: _________________")
            # Measurement fields (2 columns)
            fields_l = ["Weight:", "Chest:", "Waist:", "Hips:"]
            fields_r = ["Arms:", "Thighs:", "Energy (1–10):", "Mood (1–10):"]
            fh = (block_h - 26) / len(fields_l); fy = by - 26
            for fi, (fl, fr) in enumerate(zip(fields_l, fields_r)):
                field_y = fy - fi * fh
                fill(DK); c.setFont(fn("regular"), 8.5)
                c.drawString(ML + 10, field_y - fh + 5, f"{fl} ________________")
                c.drawString(ML + CW / 2 + 10, field_y - fh + 5, f"{fr} ________________")

        footer_bar()
        c.showPage()

    # ── 30-DAY WATER TRACKER (DP1029) ────────────────────────────────────────
    elif specialty == "water_tracker":
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
        header_band("💧  30-DAY WATER INTAKE TRACKER")
        y = PH - MT - 52 - 16
        fill(DK); c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2, y, "Color in one drop for each 8oz / 240ml glass of water. Goal: 8 glasses per day!")
        y -= 20

        fill(DK); c.setFont(fn("bold"), 9); c.drawString(ML, y, "Month: _________________________   Daily Goal: _______ oz / _______ glasses")
        y -= 24

        # 30 day rows, 8 drop cells each
        DROP_ROWS = 30; DROP_COLS = 8
        row_h_w = (y - MB - 30) / DROP_ROWS
        day_label_w = 40; cell_w_w = (CW - day_label_w) / DROP_COLS

        for di in range(DROP_ROWS):
            dy = y - di * row_h_w
            # Day label
            fill(blend(T, 0.80)); c.rect(ML, dy - row_h_w, day_label_w, row_h_w, fill=1, stroke=0)
            fill(DK); c.setFont(fn("bold"), 8)
            c.drawCentredString(ML + day_label_w / 2, dy - row_h_w + 4, f"Day {di + 1}")
            # Drop cells
            for gi in range(DROP_COLS):
                gx = ML + day_label_w + gi * cell_w_w
                fill(blend(A, 0.85) if di % 2 == 0 else blend(A, 0.70))
                lw(0.3); stroke(blend(T, 0.50))
                # Teardrop-ish: rounded rect
                c.roundRect(gx + 2, dy - row_h_w + 2, cell_w_w - 4, row_h_w - 4, 4, fill=1, stroke=1)
                fill(blend(T, 0.60)); c.setFont(fn("bold"), 6)
                c.drawCentredString(gx + cell_w_w / 2, dy - row_h_w + 4, "💧")

        footer_bar()
        c.showPage()

    # ── SLEEP LOG (DP1029) ───────────────────────────────────────────────────
    elif specialty == "sleep_log":
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
        header_band("🌙  SLEEP QUALITY LOG")
        y = PH - MT - 52 - 16
        fill(DK); c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2, y, "Track your sleep to find patterns. Consistent sleep is one of the highest-impact wellness habits.")
        y -= 22

        COLS_SL = ["Day", "Bedtime", "Wake Time", "Hours Slept", "Quality (1–5 ★)", "Notes / How I Felt"]
        col_ws = [30, 55, 60, 60, 70, 0]  # last col fills remaining
        remaining = CW - sum(col_ws[:-1])
        col_ws[-1] = remaining
        row_h_sl = (y - MB - 20) / 32
        header_h_sl = 18

        hx = ML
        for cw3, cl in zip(col_ws, COLS_SL):
            fill(T); c.rect(hx, y - header_h_sl, cw3, header_h_sl, fill=1, stroke=0)
            fill((1,1,1)); c.setFont(fn("bold"), 7.5)
            c.drawCentredString(hx + cw3 / 2, y - 13, cl)
            hx += cw3

        for ri in range(31):
            rx = ML; ry = y - header_h_sl - (ri + 1) * row_h_sl
            fill(blend(T, 0.94) if ri % 2 == 0 else (1,1,1))
            lw(0.3); stroke(blend(T, 0.60))
            for cw3 in col_ws:
                c.rect(rx, ry, cw3, row_h_sl, fill=1, stroke=1)
                rx += cw3
            fill(DK); c.setFont(fn("bold"), 7)
            c.drawCentredString(ML + col_ws[0] / 2, ry + row_h_sl / 2 - 3, str(ri + 1))

        footer_bar()
        c.showPage()

    # ── NON-SCALE VICTORIES (DP1029) ─────────────────────────────────────────
    elif specialty == "nsv_journal":
        fill(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
        header_band("🏆  NON-SCALE VICTORIES")
        y = PH - MT - 52 - 16
        fill(DK); c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2, y, "Progress is more than a number. Celebrate EVERY win — energy, strength, mood, confidence, habits.")
        y -= 22

        # Example prompts / blank entry boxes
        prompts = [
            "I ran/walked further than before →",
            "I chose the healthy option when I didn't have to →",
            "I feel stronger than I did →",
            "My clothes fit differently →",
            "I slept better than usual →",
            "I had more energy today →",
            "I said no to something that didn't serve me →",
            "I showed up even when I didn't feel like it →",
        ]

        box_h = (y - MB - 20) / len(prompts) - 4
        for pi, prompt in enumerate(prompts):
            py = y - pi * (box_h + 4)
            fill(blend(T, 0.90)); c.roundRect(ML, py - box_h, CW, box_h, 5, fill=1, stroke=0)
            fill(T); lw(0.5); c.roundRect(ML, py - box_h, CW, box_h, 5, fill=0, stroke=1)
            fill(DK); c.setFont(fn("bold"), 8); c.drawString(ML + 8, py - 14, prompt)
            fill(blend(DK, 0.40)); c.setFont(fn("regular"), 8)
            c.drawString(ML + 8, py - box_h + 8, "_" * 80)

        footer_bar()
        c.showPage()


# ── PDF merger ──────────────────────────────────────────────────────────────

def prepend_pdf_bytes(new_bytes: bytes, existing_path: str, output_path: str):
    """Prepend new_bytes pages before existing_path and write to output_path."""
    from PyPDF2 import PdfWriter, PdfReader
    import io as _io

    writer = PdfWriter()
    # Add new pages first
    new_reader = PdfReader(_io.BytesIO(new_bytes))
    for pg in new_reader.pages:
        writer.add_page(pg)
    # Add existing pages
    old_reader = PdfReader(existing_path)
    for pg in old_reader.pages:
        writer.add_page(pg)

    with open(output_path, "wb") as f:
        writer.write(f)


def append_pdf_bytes(existing_path: str, new_bytes: bytes, output_path: str):
    """Append new_bytes pages after existing_path and write to output_path."""
    from PyPDF2 import PdfWriter, PdfReader
    import io as _io

    writer = PdfWriter()
    old_reader = PdfReader(existing_path)
    for pg in old_reader.pages:
        writer.add_page(pg)
    new_reader = PdfReader(_io.BytesIO(new_bytes))
    for pg in new_reader.pages:
        writer.add_page(pg)

    with open(output_path, "wb") as f:
        writer.write(f)


# ── Main ─────────────────────────────────────────────────────────────────────

def process_planner(pid: str, cfg: dict, dry_run: bool = False):
    pdf_path = os.path.join(PRODUCT_FILES_DIR, f"{pid}.pdf")
    undated_path = os.path.join(PRODUCT_FILES_DIR, f"{pid}U.pdf")

    if not os.path.exists(pdf_path):
        print(f"  ⚠️  {pdf_path} not found — skipping")
        return

    for src_path in [pdf_path, undated_path]:
        if not os.path.exists(src_path):
            continue

        label = "undated" if src_path == undated_path else "dated"
        print(f"\n  [{label}] {os.path.basename(src_path)}")

        # 1. Backup original
        backup = src_path + ".orig_backup"
        if not os.path.exists(backup):
            shutil.copy2(src_path, backup)
            print(f"    Backed up original → {os.path.basename(backup)}")

        # 2. Build front pages (Welcome + Dashboard + Index)
        print("    Building Welcome page...")
        welcome_bytes = _make_pages(cfg, "welcome")
        print("    Building Dashboard page...")
        dashboard_bytes = _make_pages(cfg, "dashboard")
        print("    Building Planner Index page...")
        index_bytes = _make_pages(cfg, "index")

        # Merge: welcome → dashboard → index → existing
        tmp1 = src_path + ".tmp1"
        tmp2 = src_path + ".tmp2"
        tmp3 = src_path + ".tmp3"

        prepend_pdf_bytes(welcome_bytes, src_path, tmp1)
        prepend_pdf_bytes(dashboard_bytes, tmp1, tmp2)
        prepend_pdf_bytes(index_bytes, tmp2, tmp3)

        # 3. Append specialty pages
        current = tmp3
        for spec in cfg.get("specialty_pages", []):
            print(f"    Building specialty page: {spec}...")
            spec_bytes = _make_pages(cfg, "specialty", specialty=spec)
            tmp_spec = src_path + f".tmp_{spec}"
            append_pdf_bytes(current, spec_bytes, tmp_spec)
            if current not in (src_path, tmp1, tmp2, tmp3):
                try: os.remove(current)
                except: pass
            current = tmp_spec

        # 4. Write final
        if not dry_run:
            shutil.move(current, src_path)
            print(f"    ✅ Written: {os.path.basename(src_path)}")
        else:
            print(f"    DRY RUN — would write to {os.path.basename(src_path)}")
            os.remove(current)

        # Cleanup temps
        for tmp in [tmp1, tmp2, tmp3]:
            try: os.remove(tmp)
            except: pass


def main(dry_run: bool = False):
    print(f"{'='*60}")
    print(f"Planner Page Adder — {date.today()}")
    print(f"Adding: Welcome · Dashboard · Index + specialty pages")
    print(f"{'='*60}")

    for pid, cfg in PLANNERS.items():
        print(f"\n{'─'*50}")
        print(f"Processing {pid}: {cfg['title']}")
        process_planner(pid, cfg, dry_run=dry_run)

    print(f"\n{'='*60}")
    print("Done. Verify each PDF in GoodNotes before re-uploading to Etsy.")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Build pages but don't write to disk")
    args = p.parse_args()
    main(dry_run=args.dry_run)
