#!/usr/bin/env python3
"""
Digital Planner Generator — creates complete planner PDFs from CLAUDE.md configs.

Generates:
  • Full planner PDF (dated 2026)
  • Undated evergreen version
  • Cover image via gpt-image-1 (requires OpenAI API key)
  • All pages via reportlab (cover, welcome, dashboard, index, monthly ×12,
    weekly ×52, specialty pages, habit tracker, goals, notes, sticker library)
  • Packages everything for Etsy upload

Usage:
  python tools/generate_planner.py DP1030             # ADHD Planner
  python tools/generate_planner.py DP1031             # Undated Life Planner
  python tools/generate_planner.py DP1032             # Dark Mode Bundle
  python tools/generate_planner.py DP1033             # Teacher Planner
  python tools/generate_planner.py --list             # show all configs
  python tools/generate_planner.py DP1030 --no-cover  # skip OpenAI, use placeholder
"""

from __future__ import annotations

import os
import sys
import json
import argparse
import io
import shutil
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
with open(_ENV_PATH) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

PRODUCT_FILES_DIR = Path(__file__).parent.parent / "data" / "digital_products" / "product_files"
PRODUCT_FILES_DIR.mkdir(parents=True, exist_ok=True)

# ── Planner configs (from CLAUDE.md theme catalog) ───────────────────────────

PLANNER_CONFIGS = {
    "DP1030": {
        "name":        "ADHD Digital Planner 2026",
        "subtitle":    "Matcha Serenity",
        "year":        2026,
        "specialty":   "adhd",
        "page_count":  110,
        "theme_rgb":   (0.420, 0.561, 0.369),   # #6B8F5E matcha green
        "accent_rgb":  (0.722, 0.800, 0.557),   # #B8CC8E pale chartreuse
        "bg_rgb":      (0.969, 0.976, 0.953),   # #F7F9F3 rice paper
        "dark_rgb":    (0.118, 0.176, 0.094),   # #1E2D18 deep forest
        "price":       12.99,
        "tags": [
            "adhd planner",      "digital planner",    "adhd digital",
            "goodnotes planner", "focus planner",      "ipad planner",
            "adhd tools adult",  "kawaii planner",     "fillable planner",
            "instant download",  "pomodoro planner",   "brain dump journal",
            "habit tracker pdf",
        ],
        "cover_prompt": (
            "Kawaii digital planner cover art, square 2400×2400px. "
            "Matcha green (#6B8F5E) background with soft rice paper texture. "
            "Center: large kawaii matcha cup with cream swirl and tiny steam curls, "
            "surrounded by zen garden elements — smooth stones, bamboo sprigs, tiny lotus flower. "
            "Small kawaii brain character with stars around it, calm sleepy expression. "
            "Typography: 'ADHD Digital Planner 2026' in rounded sans-serif font, "
            "Matcha Serenity theme label below. "
            "Soft kawaii illustration style, pastel palette, no harsh lines. "
            "Calming, focused, organized aesthetic."
        ),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Yearly Overview", "Monthly Calendars × 12",
            "Monthly Reviews × 12", "Weekly Spreads × 52",
            "Pomodoro Focus Sheets × 4", "Brain Dump Pages × 12",
            "Habit Tracker", "Priority Matrix", "Goals",
            "Notes × 4", "Sticker Library × 5",
        ],
        "description_hook": (
            "Your brain works differently — and your planner should too. "
            "Introducing the ADHD Digital Planner 2026, designed specifically "
            "for the ADHD brain: visual time-blocking, Pomodoro focus sheets, "
            "brain dump pages, and a priority matrix — all in a calming Matcha Serenity "
            "color palette that reduces overwhelm while keeping you on track."
        ),
        "listing_title": "ADHD Digital Planner 2026 | GoodNotes Focus Planner | Kawaii Instant Download",
    },
    "DP1031": {
        "name":        "Undated Life Planner",
        "subtitle":    "Sage Garden",
        "year":        None,  # undated — no year on cover
        "specialty":   "life",
        "page_count":  100,
        "theme_rgb":   (0.545, 0.659, 0.533),   # #8BA888 muted sage green
        "accent_rgb":  (0.784, 0.867, 0.710),   # #C8DDB5 soft fern
        "bg_rgb":      (0.965, 0.973, 0.949),   # #F6F8F2 morning dew
        "dark_rgb":    (0.173, 0.220, 0.157),   # #2C3828 deep forest
        "price":       12.99,
        "tags": [
            "undated planner",   "digital planner",    "goodnotes planner",
            "life planner",      "notability planner", "ipad planner",
            "kawaii planner",    "fillable planner",   "instant download",
            "printable planner", "daily planner pdf",  "habit tracker pdf",
            "evergreen planner",
        ],
        "cover_prompt": (
            "Kawaii digital planner cover art, square 2400×2400px. "
            "Sage green (#8BA888) background with soft morning dew texture. "
            "Center: kawaii garden scene — tiny mushrooms, watering can, herb sprigs, "
            "garden snail with bow, potted succulents, small bee. "
            "Cottagecore aesthetic, soft botanical illustration. "
            "Typography: 'Undated Life Planner' in flowing rounded font, "
            "'Sage Garden Edition' label. "
            "Kawaii illustration style, soft pastel green palette, cozy nature aesthetic."
        ),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Undated Monthly Calendars × 12", "Monthly Reviews × 12",
            "Month at a Glance × 12", "Undated Weekly Spreads × 52",
            "Habit Tracker", "Goals", "Budget Tracker",
            "Meal Planner", "Notes × 4", "Sticker Library × 5",
        ],
        "description_hook": (
            "No expiry date. No wasted pages. The Undated Life Planner in Sage Garden "
            "is your forever planner — start any month, any week, any time. "
            "Soft cottagecore botanical design meets practical kawaii planning in one "
            "beautiful digital download for GoodNotes and Notability."
        ),
        "listing_title": "Undated Digital Life Planner | GoodNotes Notability | Kawaii Instant Download",
    },
    "DP1032": {
        "name":        "Dark Mode Planner Bundle 2026",
        "subtitle":    "Midnight Kawaii",
        "year":        2026,
        "specialty":   "dark_mode",
        "page_count":  108,
        "theme_rgb":   (0.102, 0.102, 0.180),   # #1A1A2E deep midnight
        "accent_rgb":  (0.878, 0.251, 0.984),   # #E040FB electric violet
        "bg_rgb":      (0.176, 0.169, 0.333),   # #2D2B55 space purple (dark bg)
        "dark_rgb":    (0.941, 0.902, 1.000),   # #F0E6FF starlight (text on dark)
        "price":       14.99,
        "tags": [
            "dark mode planner", "digital planner",    "goodnotes dark",
            "dark planner pdf",  "kawaii dark",        "ipad planner",
            "night mode planner","fillable planner",   "instant download",
            "aesthetic planner", "y2k planner",        "dark kawaii",
            "goodnotes planner",
        ],
        "cover_prompt": (
            "Kawaii digital planner cover art, square 2400×2400px. "
            "Deep midnight navy (#1A1A2E) background with subtle star field. "
            "Center: kawaii space cat with neon violet glow, holographic elements, "
            "pixel art stars, glowing crescent moon, neon-outlined kawaii ghost. "
            "Electric violet (#E040FB) and neon aqua accent glows. "
            "Typography: 'Dark Mode Planner 2026' in neon glow font effect, "
            "'Midnight Kawaii Edition' subtitle. "
            "Y3K futuristic kawaii aesthetic, dark background, neon accents."
        ),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Yearly Overview", "Monthly Calendars × 12",
            "Monthly Reviews × 12", "Month at a Glance × 12",
            "Weekly Spreads × 52", "Night Owl Habit Tracker",
            "Goals", "Brain Dump × 4", "Notes × 4", "Sticker Library × 5",
        ],
        "description_hook": (
            "Finally — a planner for night owls, gamers, and dark aesthetic lovers. "
            "The Dark Mode Planner 2026 in Midnight Kawaii brings Y3K neon-on-dark "
            "design to your GoodNotes and Notability workflow. "
            "Cute goes dark — and it's incredibly satisfying to plan in."
        ),
        "listing_title": "Dark Mode Digital Planner 2026 | GoodNotes Dark Kawaii | Instant Download",
    },
    "DP1033": {
        "name":        "Teacher Planner 2026–2027",
        "subtitle":    "Sunflower Studio",
        "year":        2026,
        "specialty":   "teacher",
        "page_count":  115,
        "theme_rgb":   (0.957, 0.769, 0.188),   # #F4C430 sunflower yellow
        "accent_rgb":  (0.290, 0.486, 0.349),   # #4A7C59 stem green
        "bg_rgb":      (1.000, 0.992, 0.941),   # #FFFDF0 cream petal
        "dark_rgb":    (0.165, 0.102, 0.000),   # #2A1A00 seed brown
        "price":       14.99,
        "tags": [
            "teacher planner",   "digital planner",    "teacher goodnotes",
            "classroom planner", "teacher ipad",       "lesson plan pdf",
            "teacher gift",      "kawaii teacher",     "fillable planner",
            "instant download",  "academic planner",   "school year planner",
            "teacher organizer",
        ],
        "cover_prompt": (
            "Kawaii digital planner cover art, square 2400×2400px. "
            "Warm cream (#FFFDF0) background with subtle grid texture. "
            "Center: kawaii teacher scene — sunflowers in a mason jar, tiny apple, "
            "mini chalkboard with 'Hello Students', pencils in a cup, books stacked, "
            "kawaii bee with graduation cap, butterflies, small ruler. "
            "Sunflower yellow (#F4C430) and stem green (#4A7C59) color palette. "
            "Typography: 'Teacher Planner 2026–2027' in cheerful rounded font, "
            "'Sunflower Studio Edition' label. "
            "Bright botanical kawaii style, warm and energetic."
        ),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Academic Year at a Glance (Aug 2026–Jul 2027)",
            "Monthly Calendars × 12 (Aug–Jul)", "Monthly Reviews × 12",
            "Weekly Lesson Plans × 44", "Class Roster × 6 classes",
            "Seating Chart Templates", "Parent Communication Log",
            "Habit Tracker (self-care for teachers)", "Goals",
            "Sub Plans Template × 2", "Notes × 4", "Sticker Library × 5",
        ],
        "description_hook": (
            "The most complete teacher planner for GoodNotes and Notability — "
            "built around the academic year August 2026 through July 2027. "
            "Weekly lesson plans, class rosters, seating charts, parent communication log, "
            "and sub plan templates. The Sunflower Studio design keeps your planning "
            "bright, organized, and genuinely joyful."
        ),
        "listing_title": "Teacher Planner 2026-2027 | GoodNotes Digital | Kawaii Instant Download",
    },
}


# ── PDF generation ───────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def _make_cover_page(cfg: dict, cover_image_path: str | None) -> bytes:
    """Generate the cover page as PDF bytes."""
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.colors import Color
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=LETTER)
    PW, PH = LETTER

    bg = cfg["bg_rgb"]
    theme = cfg["theme_rgb"]
    dark = cfg["dark_rgb"]

    # Background
    c.setFillColorRGB(*bg)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)

    # Cover image (if available)
    if cover_image_path and os.path.exists(cover_image_path):
        from reportlab.lib.utils import ImageReader
        img = ImageReader(cover_image_path)
        margin = 40
        c.drawImage(img, margin, margin + 80, width=PW - 2*margin, height=PH - 2*margin - 160,
                    preserveAspectRatio=True, anchor="c", mask="auto")
    else:
        # Placeholder: colored rectangle with decorative border
        c.setFillColorRGB(*theme)
        c.rect(40, 120, PW - 80, PH - 200, fill=1, stroke=0)
        c.setFillColorRGB(*bg)
        c.setFont("Helvetica", 11)
        c.drawCentredString(PW / 2, PH / 2 + 20, "[Cover illustration — add via Canva or gpt-image-1]")

    # Title band at bottom
    c.setFillColorRGB(*dark)
    c.rect(0, 0, PW, 100, fill=1, stroke=0)
    c.setFillColorRGB(*bg)
    c.setFont("Helvetica-Bold", 16)
    year_label = str(cfg.get("year") or "")
    title_text = cfg["name"] + (f" {year_label}" if year_label and year_label not in cfg["name"] else "")
    c.drawCentredString(PW / 2, 68, title_text)
    c.setFont("Helvetica", 11)
    c.drawCentredString(PW / 2, 45, cfg["subtitle"])
    c.setFont("Helvetica", 9)
    c.drawCentredString(PW / 2, 22, "OnBrandCraftz · Instant Digital Download")

    c.showPage()
    c.save()
    return buf.getvalue()


def _make_planner_pages(cfg: dict, dated: bool = True) -> bytes:
    """Generate all non-cover planner pages using planner_page_adder infrastructure."""
    from tools.planner_page_adder import _make_pages, _get_canvas_and_fonts

    planner_cfg = {
        "title":    cfg["name"],
        "subtitle": cfg["subtitle"],
        "year":     cfg.get("year") if dated else None,
        "theme":    cfg["theme_rgb"],
        "accent":   cfg["accent_rgb"],
        "bg":       cfg["bg_rgb"],
        "dark":     cfg["dark_rgb"],
        "sections": cfg.get("sections", []),
        "specialty_pages": [cfg.get("specialty", "life")],
    }

    # Generate each page type and concatenate
    page_types = ["welcome", "dashboard", "index", "monthly", "weekly",
                  "habit", "goals", "notes", "sticker_library"]
    if cfg.get("specialty") == "adhd":
        page_types.insert(-2, "pomodoro")
        page_types.insert(-2, "brain_dump")
    elif cfg.get("specialty") == "teacher":
        page_types.insert(-2, "lesson_plan")
        page_types.insert(-2, "class_roster")

    all_bytes = b""
    for page_type in page_types:
        try:
            part = _make_pages(planner_cfg, page_type)
            all_bytes += part
        except Exception as e:
            print(f"    [generate_planner] Warning: skipped page type '{page_type}': {e}")

    return all_bytes


def _generate_cover_image(cfg: dict, out_path: str) -> bool:
    """Generate cover art using gpt-image-1. Returns True on success."""
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key:
        print("    [generate_planner] No OpenAI API key — skipping cover generation")
        return False

    try:
        import urllib.request
        import urllib.parse
        import base64

        prompt = cfg.get("cover_prompt", "Kawaii digital planner cover illustration")
        request_body = json.dumps({
            "model":   "gpt-image-1",
            "prompt":  prompt,
            "size":    "1024x1024",
            "quality": "high",
        }).encode()

        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=request_body,
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {openai_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())

        image_data = result["data"][0]
        if "b64_json" in image_data:
            img_bytes = base64.b64decode(image_data["b64_json"])
        elif "url" in image_data:
            with urllib.request.urlopen(image_data["url"], timeout=30) as r:
                img_bytes = r.read()
        else:
            return False

        with open(out_path, "wb") as f:
            f.write(img_bytes)
        print(f"    Cover image saved → {out_path}")
        return True

    except Exception as e:
        print(f"    [generate_planner] Cover generation failed: {e}")
        return False


def _merge_pdfs(*pdf_bytes_list: bytes) -> bytes:
    """Merge multiple PDF byte strings into one."""
    from PyPDF2 import PdfWriter, PdfReader
    writer = PdfWriter()
    for pdf_bytes in pdf_bytes_list:
        if pdf_bytes:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _create_undated_version(pdf_bytes: bytes) -> bytes:
    """Create an undated version by removing year references from page content.

    For now returns the same PDF — a proper undated version would need separate
    page generation with dated=False. This is the stub for that logic.
    """
    return pdf_bytes  # pages generated with dated=False are already undated


def generate_planner(pid: str, no_cover: bool = False) -> Path:
    cfg = PLANNER_CONFIGS.get(pid)
    if not cfg:
        print(f"Unknown planner ID '{pid}'. Run with --list to see options.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Generating {pid}: {cfg['name']}")
    print(f"  Theme: {cfg['subtitle']}")
    print(f"{'='*60}")

    out_dir = PRODUCT_FILES_DIR
    pid_lower = pid.lower()

    # ── Step 1: Generate cover image ─────────────────────────────────────
    cover_img_path = str(out_dir / f"{pid}_cover.png")
    if no_cover:
        cover_img_path = None
        print("  [1/5] Cover generation skipped (--no-cover)")
    else:
        print("  [1/5] Generating cover image with gpt-image-1...")
        if not _generate_cover_image(cfg, cover_img_path):
            cover_img_path = None
            print("        Continuing without cover image (add manually in Canva).")

    # ── Step 2: Generate cover page PDF ──────────────────────────────────
    print("  [2/5] Building cover page PDF...")
    try:
        cover_pdf_bytes = _make_cover_page(cfg, cover_img_path)
        print(f"        Cover page: OK")
    except Exception as e:
        print(f"        Cover page failed: {e}")
        cover_pdf_bytes = b""

    # ── Step 3: Generate content pages (dated) ───────────────────────────
    print("  [3/5] Building dated content pages...")
    try:
        content_bytes = _make_planner_pages(cfg, dated=True)
        print(f"        Content pages: OK")
    except Exception as e:
        print(f"        Content pages failed: {e}")
        content_bytes = b""

    # ── Step 4: Assemble and write dated PDF ─────────────────────────────
    print("  [4/5] Assembling dated PDF...")
    try:
        full_pdf = _merge_pdfs(cover_pdf_bytes, content_bytes)
        dated_path = out_dir / f"{pid}.pdf"
        with open(dated_path, "wb") as f:
            f.write(full_pdf)
        size_mb = len(full_pdf) / 1024 / 1024
        print(f"        Dated PDF → {dated_path}  ({size_mb:.1f} MB)")
    except Exception as e:
        print(f"        PDF assembly failed: {e}")
        dated_path = None

    # ── Step 5: Generate undated version ─────────────────────────────────
    print("  [5/5] Building undated (evergreen) version...")
    try:
        content_undated = _make_planner_pages(cfg, dated=False)
        undated_pdf = _merge_pdfs(cover_pdf_bytes, content_undated)
        undated_path = out_dir / f"{pid}U.pdf"
        with open(undated_path, "wb") as f:
            f.write(undated_pdf)
        size_mb = len(undated_pdf) / 1024 / 1024
        print(f"        Undated PDF → {undated_path}  ({size_mb:.1f} MB)")
    except Exception as e:
        print(f"        Undated PDF failed: {e}")

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n  {'─'*56}")
    print(f"  {pid} generation complete.")
    print(f"  Listing title: {cfg['listing_title']}")
    print(f"  Price: ${cfg['price']:.2f}")
    print(f"  Next steps:")
    print(f"    1. Review PDF in GoodNotes — verify all pages render correctly")
    print(f"    2. Generate sticker pack:  python tools/gen_sticker_sheet.py {pid}")
    print(f"    3. Generate listing photos: python tools/gen_planner_listing_photos.py --pid {pid}")
    print(f"    4. Create Etsy listing via the publisher pipeline")
    if not cover_img_path:
        print(f"    NOTE: Cover image was not generated — open Canva and add manually")
    print(f"  {'─'*56}\n")

    return dated_path


def list_configs() -> None:
    print("\nAvailable planner configs:\n")
    for pid, cfg in PLANNER_CONFIGS.items():
        year = cfg.get("year") or "Undated"
        print(f"  {pid}  {cfg['name']}  ({cfg['subtitle']})")
        print(f"        Price: ${cfg['price']:.2f}  ·  ~{cfg['page_count']} pages  ·  Year: {year}")
        print(f"        {cfg['description_hook'][:80]}...")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a new digital planner product")
    parser.add_argument("planner_id", nargs="?", help="e.g. DP1030")
    parser.add_argument("--list",     action="store_true", help="List all planner configs")
    parser.add_argument("--no-cover", action="store_true", help="Skip gpt-image-1 cover generation")
    args = parser.parse_args()

    if args.list or not args.planner_id:
        list_configs()
    else:
        generate_planner(args.planner_id.upper(), no_cover=args.no_cover)
