#!/usr/bin/env python3
"""
kdp_publisher.py — Amazon KDP (Kindle Direct Publishing) preparation tool.

Prepares existing planner PDFs for Amazon KDP physical print-on-demand submission.
Customers order from Amazon → Amazon prints and ships → we collect royalties.

Usage:
    python tools/kdp_publisher.py --check           # check all PDFs against KDP requirements
    python tools/kdp_publisher.py --prepare DP1026  # prepare one book
    python tools/kdp_publisher.py --all             # prepare all 4 books
    python tools/kdp_publisher.py --royalties       # show royalty calculations at different prices

Output:
    data/kdp/DP{ID}_kdp_submission.json  — one per planner with all KDP fields
    data/kdp/kdp_setup_guide.md          — step-by-step account setup instructions
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent.parent.resolve()
PRODUCT_FILES_DIR = BASE / "data" / "digital_products" / "product_files"
KDP_DIR = BASE / "data" / "kdp"

# ---------------------------------------------------------------------------
# .env parser — never use load_dotenv()
# ---------------------------------------------------------------------------
def _parse_env() -> dict[str, str]:
    env: dict[str, str] = {}
    env_path = BASE / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


# ---------------------------------------------------------------------------
# PyPDF2 — optional, fall back gracefully
# ---------------------------------------------------------------------------
try:
    import PyPDF2  # type: ignore
    _PYPDF2_AVAILABLE = True
except ImportError:
    _PYPDF2_AVAILABLE = False


# ---------------------------------------------------------------------------
# KDP product definitions
# ---------------------------------------------------------------------------
KDP_PLANNERS = {
    "DP1026": {
        "product_id": "DP1026",
        "kdp_title": "Ultimate Digital Life Planner 2026 — Lavender Dreams Edition",
        "subtitle": "104-Page Kawaii Fillable Planner with Habit Tracker, Budget, Meal Plan & Sticker Pages",
        "author": "OnBrandCraftz",
        "description": (
            "Stay organized and adorable with the Ultimate Digital Life Planner 2026 "
            "in the dreamy Lavender Dreams color theme. This 104-page kawaii-illustrated "
            "planner includes monthly spreads for all 12 months, 52 weekly layouts, habit "
            "trackers, goal pages, budget tracker, meal planner, notes pages, and a full "
            "kawaii sticker library. Perfect for GoodNotes, Notability, or print at home."
        ),
        "keywords": [
            "digital life planner 2026",
            "kawaii planner printable",
            "goodnotes planner lavender",
            "habit tracker journal 2026",
            "fillable planner notebook",
            "kawaii sticker planner",
            "productivity journal women",
        ],
        "categories": ["Self-Help", "Calendars & Planners"],
        "pdf_file": "DP1026.pdf",
        "cover_file": "DP1026_kawaii_cover.jpg",
        "color_theme": "Lavender Dreams",
        "primary_color": "#8666AA",
        "interior_type": "color",
        "trim_size": "8.5x11",
        "target_audience": "Women 18-35, planner lovers, productivity enthusiasts",
        "etsy_price": 14.99,
        "kdp_target_price": 17.99,
    },
    "DP1027": {
        "product_id": "DP1027",
        "kdp_title": "Kawaii Student Planner 2026 — Cotton Candy Edition",
        "subtitle": "90-Page Academic Planner for High School & College with Weekly Spreads & Sticker Pages",
        "author": "OnBrandCraftz",
        "description": (
            "Study smarter and plan cuter with the Kawaii Student Planner 2026 in the "
            "bright Cotton Candy theme (pink and sky blue). This 90-page academic planner "
            "covers every week of the school year with monthly calendars, 52 weekly "
            "layouts, habit tracker, goals page, notes pages, and a full kawaii sticker "
            "library. Designed for high school and college students who want their "
            "planner to be as fun as their life."
        ),
        "keywords": [
            "student planner 2026",
            "kawaii academic planner",
            "school planner notebook",
            "college planner 2026",
            "back to school planner",
            "kawaii study journal",
            "cute weekly planner students",
        ],
        "categories": ["Education", "Calendars & Planners"],
        "pdf_file": "DP1027.pdf",
        "cover_file": "DP1027_kawaii_cover.jpg",
        "color_theme": "Cotton Candy",
        "primary_color": "#DE97C6",
        "interior_type": "color",
        "trim_size": "8.5x11",
        "target_audience": "High school and college students, back-to-school buyers",
        "etsy_price": 9.99,
        "kdp_target_price": 14.99,
    },
    "DP1028": {
        "product_id": "DP1028",
        "kdp_title": "Digital Budget Planner 2026 — Midnight Blue Edition",
        "subtitle": "102-Page Finance & Money Planner with Monthly Budget Tracker, Debt Payoff & Savings Goals",
        "author": "OnBrandCraftz",
        "description": (
            "Take control of your finances in style with the Digital Budget Planner 2026 "
            "in the sleek Midnight Blue theme. This 102-page planner includes monthly "
            "budget trackers for all 12 months, monthly review pages, 52 weekly spending "
            "logs, goals page, and notes. Features dedicated income and expense columns, "
            "savings targets, and debt payoff sections — perfect for zero-based budgeting, "
            "Dave Ramsey followers, and anyone serious about their financial goals."
        ),
        "keywords": [
            "budget planner 2026",
            "finance planner notebook",
            "money planner journal",
            "debt payoff tracker book",
            "savings planner 2026",
            "kawaii budget journal",
            "monthly budget notebook women",
        ],
        "categories": ["Business & Money", "Calendars & Planners"],
        "pdf_file": "DP1028.pdf",
        "cover_file": "DP1028_kawaii_cover.jpg",
        "color_theme": "Midnight Blue",
        "primary_color": "#1B2568",
        "interior_type": "color",
        "trim_size": "8.5x11",
        "target_audience": "Adults budgeting, Dave Ramsey followers, debt payoff community",
        "etsy_price": 12.99,
        "kdp_target_price": 16.99,
    },
    "DP1029": {
        "product_id": "DP1029",
        "kdp_title": "Fitness & Wellness Planner 2026 — Coral Peach Edition",
        "subtitle": "91-Page Health Tracker with Habit Log, Meal Planner, Workout Journal & Wellness Goals",
        "author": "OnBrandCraftz",
        "description": (
            "Start your wellness journey with the Fitness & Wellness Planner 2026 in the "
            "energizing Coral Peach theme. This 91-page planner includes monthly fitness "
            "calendars for all 12 months, 52 weekly workout and meal planning spreads, "
            "habit tracker, progress measurement pages, goals, and notes. Designed for "
            "beginners and dedicated athletes alike — track workouts, meals, water intake, "
            "sleep, and self-care all in one beautiful book."
        ),
        "keywords": [
            "fitness planner 2026",
            "wellness journal notebook",
            "workout planner women",
            "health tracker journal 2026",
            "meal planner fitness book",
            "habit tracker fitness",
            "self care planner notebook",
        ],
        "categories": ["Health & Wellness", "Calendars & Planners"],
        "pdf_file": "DP1029.pdf",
        "cover_file": "DP1029_kawaii_cover.jpg",
        "color_theme": "Coral Peach",
        "primary_color": "#FD6C49",
        "interior_type": "color",
        "trim_size": "8.5x11",
        "target_audience": "Fitness beginners, wellness journey, weight loss, healthy eating",
        "etsy_price": 12.99,
        "kdp_target_price": 16.99,
    },
}


# ---------------------------------------------------------------------------
# KDP requirements constants
# ---------------------------------------------------------------------------
KDP_REQUIREMENTS = {
    "min_pages": 24,
    "max_file_size_mb": 650,
    "supported_trim_sizes": ["8.5x11"],
    "supported_interior_types": ["black_white", "color"],
    "required_page_size_inches": (8.5, 11.0),
    "page_size_tolerance_inches": 0.01,
    "us_letter_points": (612.0, 792.0),  # 8.5 * 72 = 612, 11 * 72 = 792
}

# KDP royalty structure for color interiors
# Royalty = (List Price × 0.60) - ($0.85 + pages × $0.012)
KDP_ROYALTY_RATE = 0.60
KDP_BASE_PRINTING_COST = 0.85
KDP_PER_PAGE_PRINTING_COST = 0.012

# Price test range for royalty optimization
ROYALTY_TEST_PRICES = [14.99, 15.99, 16.99, 17.99, 18.99, 19.99]


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
def calculate_royalty(list_price: float, pages: int) -> dict[str, float]:
    """Calculate KDP royalty for a color interior book."""
    printing_cost = KDP_BASE_PRINTING_COST + (pages * KDP_PER_PAGE_PRINTING_COST)
    gross_royalty = list_price * KDP_ROYALTY_RATE
    net_royalty = gross_royalty - printing_cost
    margin_pct = (net_royalty / list_price * 100) if list_price > 0 else 0
    return {
        "list_price": list_price,
        "pages": pages,
        "printing_cost": round(printing_cost, 4),
        "gross_royalty": round(gross_royalty, 4),
        "net_royalty": round(net_royalty, 4),
        "margin_pct": round(margin_pct, 1),
        "breakeven_price": round(printing_cost / KDP_ROYALTY_RATE, 2),
    }


def find_optimal_price(pages: int, min_price: float = 14.99, max_price: float = 19.99) -> dict[str, Any]:
    """Find the price that maximizes royalty within the competitive range."""
    best: dict[str, Any] = {}
    best_royalty = -999.0
    for price in ROYALTY_TEST_PRICES:
        if min_price <= price <= max_price:
            r = calculate_royalty(price, pages)
            if r["net_royalty"] > best_royalty:
                best_royalty = r["net_royalty"]
                best = r
    return best


def inspect_pdf(pdf_path: Path) -> dict[str, Any]:
    """
    Inspect a PDF file against KDP requirements.
    Uses PyPDF2 if available, otherwise falls back to file-size-only checks.
    """
    result: dict[str, Any] = {
        "file": str(pdf_path),
        "exists": pdf_path.exists(),
        "size_mb": 0.0,
        "page_count": None,
        "page_size_inches": None,
        "page_size_ok": None,
        "pypdf2_used": _PYPDF2_AVAILABLE,
        "checks": {},
        "passed": False,
        "issues": [],
        "warnings": [],
    }

    if not pdf_path.exists():
        result["issues"].append(f"File not found: {pdf_path}")
        return result

    size_bytes = pdf_path.stat().st_size
    result["size_mb"] = round(size_bytes / (1024 * 1024), 2)

    # File size check
    if result["size_mb"] > KDP_REQUIREMENTS["max_file_size_mb"]:
        result["issues"].append(
            f"File size {result['size_mb']} MB exceeds KDP 650 MB limit"
        )
    else:
        result["checks"]["file_size"] = True

    if _PYPDF2_AVAILABLE:
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                page_count = len(reader.pages)
                result["page_count"] = page_count

                # Page count check
                if page_count < KDP_REQUIREMENTS["min_pages"]:
                    result["issues"].append(
                        f"Only {page_count} pages — KDP minimum is {KDP_REQUIREMENTS['min_pages']}"
                    )
                else:
                    result["checks"]["page_count"] = True

                # Page size check (first page)
                page = reader.pages[0]
                w_pts = float(page.mediabox.width)
                h_pts = float(page.mediabox.height)
                w_in = round(w_pts / 72.0, 3)
                h_in = round(h_pts / 72.0, 3)
                result["page_size_inches"] = (w_in, h_in)

                tol = KDP_REQUIREMENTS["page_size_tolerance_inches"]
                req_w, req_h = KDP_REQUIREMENTS["required_page_size_inches"]
                size_ok = (
                    abs(w_in - req_w) <= tol and abs(h_in - req_h) <= tol
                )
                result["page_size_ok"] = size_ok

                if not size_ok:
                    result["issues"].append(
                        f"Page size {w_in}x{h_in}\" does not match required "
                        f"{req_w}x{req_h}\" (US Letter)"
                    )
                else:
                    result["checks"]["page_size"] = True

        except Exception as exc:
            result["warnings"].append(f"PyPDF2 inspection error: {exc}")
            result["pypdf2_used"] = False
    else:
        result["warnings"].append(
            "PyPDF2 not installed — page count and dimensions not verified. "
            "Install with: pip install PyPDF2"
        )

    # PDF format check (just verify it starts with %PDF)
    try:
        with open(pdf_path, "rb") as f:
            header = f.read(4)
        if header == b"%PDF":
            result["checks"]["pdf_format"] = True
        else:
            result["issues"].append("File does not appear to be a valid PDF")
    except Exception as exc:
        result["issues"].append(f"Could not read file header: {exc}")

    result["passed"] = len(result["issues"]) == 0
    return result


def calculate_spine_width(pages: int) -> dict[str, float]:
    """
    Calculate KDP cover spine width.
    Formula: pages × 0.002252 inches + 0.25 (color interior, 60# paper)
    """
    spine_inches = pages * 0.002252 + 0.25
    spine_mm = spine_inches * 25.4
    return {
        "spine_inches": round(spine_inches, 4),
        "spine_mm": round(spine_mm, 2),
        "pages": pages,
        "formula": "pages × 0.002252\" + 0.25\" (KDP color interior, 60# paper)",
    }


def build_kdp_submission(product_id: str) -> dict[str, Any]:
    """Build a full KDP submission record for a planner."""
    if product_id not in KDP_PLANNERS:
        raise ValueError(f"Unknown product ID: {product_id}. Valid IDs: {list(KDP_PLANNERS.keys())}")

    planner = KDP_PLANNERS[product_id]
    pdf_path = PRODUCT_FILES_DIR / planner["pdf_file"]

    print(f"\n{'='*60}")
    print(f"Preparing KDP submission: {product_id}")
    print(f"{'='*60}")

    # Inspect PDF
    print(f"  Inspecting PDF: {planner['pdf_file']}...")
    inspection = inspect_pdf(pdf_path)

    page_count = inspection.get("page_count")
    if page_count is None:
        # Fall back to spec-defined page count if PyPDF2 unavailable
        fallback_pages = {
            "DP1026": 104, "DP1027": 90, "DP1028": 102, "DP1029": 91
        }
        page_count = fallback_pages.get(product_id, 100)
        print(f"  Warning: Could not read page count — using spec value: {page_count}")
    else:
        print(f"  Pages detected: {page_count}")

    # Spine width
    spine = calculate_spine_width(page_count)
    print(f"  Spine width: {spine['spine_inches']}\" ({spine['spine_mm']} mm)")

    # Royalties at target price
    target_price = planner["kdp_target_price"]
    royalty = calculate_royalty(target_price, page_count)
    optimal = find_optimal_price(page_count)
    print(f"  Royalty at ${target_price}: ${royalty['net_royalty']:.2f}/copy")
    print(f"  Optimal price: ${optimal.get('list_price', target_price)} → ${optimal.get('net_royalty', 0):.2f}/copy")

    # Cover file check
    cover_path = PRODUCT_FILES_DIR / planner["cover_file"]
    cover_exists = cover_path.exists()
    cover_note = ""
    if not cover_exists:
        cover_note = (
            f"Cover file '{planner['cover_file']}' not found. "
            "A separate full-bleed KDP cover PDF must be created using KDP Cover Creator "
            "or a compatible design tool. The spine width above is the critical measurement."
        )
        print(f"  Warning: Cover file not found — will need to create KDP cover PDF")
    else:
        print(f"  Cover file found: {planner['cover_file']}")

    # Build royalty table
    royalty_table = []
    for price in ROYALTY_TEST_PRICES:
        royalty_table.append(calculate_royalty(price, page_count))

    # Assemble submission record
    submission = {
        "product_id": product_id,
        "generated_date": str(date.today()),
        "kdp_metadata": {
            "title": planner["kdp_title"],
            "subtitle": planner["subtitle"],
            "author": planner["author"],
            "description": planner["description"],
            "keywords": planner["keywords"],
            "categories": planner["categories"],
            "language": "English",
            "publication_date": str(date.today()),
        },
        "interior": {
            "pdf_file": str(pdf_path),
            "interior_type": planner["interior_type"],
            "paper_color": "white",
            "trim_size": planner["trim_size"],
            "page_count": page_count,
            "bleed": False,
            "inspection": inspection,
        },
        "cover": {
            "cover_file": str(cover_path) if cover_exists else None,
            "cover_exists": cover_exists,
            "spine_width_inches": spine["spine_inches"],
            "spine_width_mm": spine["spine_mm"],
            "full_bleed_required": True,
            "cover_note": cover_note,
            "cover_dimensions_note": (
                f"Full bleed cover dimensions: "
                f"({0.25 + spine['spine_inches'] + 8.5 + 0.25:.4f})\" wide × 11.25\" tall "
                f"(includes 0.25\" bleed on all sides)"
            ),
        },
        "pricing": {
            "target_list_price_usd": target_price,
            "optimal_list_price_usd": optimal.get("list_price", target_price),
            "royalty_at_target": royalty,
            "optimal_royalty": optimal,
            "royalty_table_all_prices": royalty_table,
            "etsy_price": planner["etsy_price"],
            "pricing_note": (
                "KDP price set higher than Etsy to account for physical printing costs. "
                "Color interior printing cost included in royalty calculation. "
                "Recommend pricing $2-4 above Etsy price for comparable perceived value."
            ),
        },
        "distribution": {
            "territories": "worldwide",
            "kdp_select": False,
            "kdp_select_note": (
                "Do NOT enroll in KDP Select (Kindle Unlimited exclusivity). "
                "We sell the digital version on Etsy — exclusivity would block that."
            ),
            "expanded_distribution": True,
            "expanded_distribution_note": (
                "Enable Expanded Distribution to reach bookstores and libraries. "
                "Royalty drops to 40% for expanded distribution sales."
            ),
        },
        "checklist": build_submission_checklist(product_id, inspection, cover_exists, page_count),
        "color_theme": planner["color_theme"],
        "primary_color": planner["primary_color"],
        "target_audience": planner["target_audience"],
        "format": {
            "paper_size": "US Letter (8.5 × 11 inches)",
            "orientation": "portrait",
            "color_space": "sRGB",
            "dpi_recommendation": "300 DPI minimum for all images",
        },
    }

    # Save
    KDP_DIR.mkdir(parents=True, exist_ok=True)
    out_path = KDP_DIR / f"{product_id}_kdp_submission.json"
    out_path.write_text(json.dumps(submission, indent=2))
    print(f"  Saved: {out_path.relative_to(BASE)}")

    return submission


def build_submission_checklist(
    product_id: str, inspection: dict, cover_exists: bool, page_count: int
) -> list[dict[str, Any]]:
    """Build a checklist of tasks for KDP submission."""
    checks = [
        {
            "step": 1,
            "task": "Create KDP publisher account at kdp.amazon.com",
            "status": "pending",
            "notes": "Use Printing3dthings@outlook.com. Need bank account and tax info (EIN or SSN).",
        },
        {
            "step": 2,
            "task": "Complete tax interview in KDP account",
            "status": "pending",
            "notes": "Required before first royalty payment. US persons use SSN/EIN on W-9.",
        },
        {
            "step": 3,
            "task": "Interior PDF — verify file",
            "status": "passed" if inspection.get("passed") else "needs_review",
            "notes": (
                "PDF passes all KDP requirements."
                if inspection.get("passed")
                else f"Issues: {'; '.join(inspection.get('issues', ['check file']))}. "
                     "Note: KDP may accept the file even if some checks are uncertain — "
                     "upload and use KDP's built-in previewer to verify."
            ),
            "file": inspection.get("file", ""),
        },
        {
            "step": 4,
            "task": "Create KDP cover PDF",
            "status": "done" if cover_exists else "pending",
            "notes": (
                "Cover file found — may need conversion to full-bleed KDP cover format."
                if cover_exists
                else (
                    "Use KDP Cover Creator (free, in KDP dashboard) or Canva/InDesign. "
                    f"Spine width: {calculate_spine_width(page_count)['spine_inches']}\" "
                    f"({calculate_spine_width(page_count)['spine_mm']} mm). "
                    "Include front cover + spine + back cover as one PDF."
                )
            ),
        },
        {
            "step": 5,
            "task": "Set up new paperback title in KDP",
            "status": "pending",
            "notes": (
                "KDP Dashboard → Create → Paperback. "
                "Fill in title, subtitle, author, description, keywords, categories. "
                "Select: Color interior, white paper, 8.5×11 trim size."
            ),
        },
        {
            "step": 6,
            "task": "Upload interior PDF",
            "status": "pending",
            "notes": (
                "Upload the interior PDF. KDP will run automated checks and show a "
                "preview. Review every page in the online previewer before continuing."
            ),
        },
        {
            "step": 7,
            "task": "Upload or create cover",
            "status": "pending",
            "notes": (
                "Upload the cover PDF or use KDP Cover Creator. "
                "Ensure the spine text is readable and spine width matches calculation."
            ),
        },
        {
            "step": 8,
            "task": "Set pricing and distribution",
            "status": "pending",
            "notes": (
                f"Set list price to ${KDP_PLANNERS[product_id]['kdp_target_price']}. "
                "Enable Expanded Distribution. Do NOT enroll in KDP Select. "
                "Review royalty calculation in KDP dashboard before publishing."
            ),
        },
        {
            "step": 9,
            "task": "Add AI content disclosure",
            "status": "pending",
            "notes": (
                "KDP requires AI disclosure for AI-generated content (effective Jan 2024). "
                "In the KDP listing, check 'Yes' for AI-generated content. "
                "Add to book description: 'Cover art and interior design created with AI tools.'"
            ),
        },
        {
            "step": 10,
            "task": "Submit for review",
            "status": "pending",
            "notes": (
                "KDP review takes 24-72 hours. You will receive an email when approved. "
                "The book will appear on Amazon within 72 hours of approval."
            ),
        },
        {
            "step": 11,
            "task": "Add Amazon link to Etsy listing",
            "status": "pending",
            "notes": (
                "Once live on Amazon, add to Etsy listing description: "
                "'Prefer a physical copy? Order the printed version on Amazon → [link]'. "
                "This adds perceived value without cannibalizing digital sales."
            ),
        },
    ]
    return checks


def cmd_check() -> None:
    """Check all planner PDFs against KDP requirements."""
    print("\nKDP Requirements Check")
    print("=" * 60)
    print(f"PyPDF2 available: {_PYPDF2_AVAILABLE}")

    all_passed = True
    for product_id, planner in KDP_PLANNERS.items():
        pdf_path = PRODUCT_FILES_DIR / planner["pdf_file"]
        print(f"\n{product_id}: {planner['pdf_file']}")
        inspection = inspect_pdf(pdf_path)

        # Summary line
        status = "PASS" if inspection["passed"] else "ISSUES"
        print(f"  Status: [{status}]")
        print(f"  File size: {inspection['size_mb']} MB (limit: 650 MB)")

        if inspection["page_count"] is not None:
            print(f"  Pages: {inspection['page_count']} (minimum: 24)")
        if inspection["page_size_inches"] is not None:
            w, h = inspection["page_size_inches"]
            print(f"  Page size: {w}\" × {h}\" (required: 8.5\" × 11\")")

        for issue in inspection["issues"]:
            print(f"  ERROR: {issue}")
        for warning in inspection["warnings"]:
            print(f"  WARNING: {warning}")

        checks_passed = list(inspection["checks"].keys())
        if checks_passed:
            print(f"  Checks passed: {', '.join(checks_passed)}")

        if not inspection["passed"]:
            all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("All PDFs pass KDP requirements check.")
    else:
        print("Some PDFs have issues. Review above and fix before uploading to KDP.")

    # Royalty snapshot
    print("\nQuick Royalty Snapshot (at recommended prices):")
    print(f"  {'Product':<10} {'Pages':>6} {'Price':>7} {'Royalty':>8} {'Margin':>7}")
    print(f"  {'-'*10} {'-'*6} {'-'*7} {'-'*8} {'-'*7}")
    for product_id, planner in KDP_PLANNERS.items():
        pdf_path = PRODUCT_FILES_DIR / planner["pdf_file"]
        insp = inspect_pdf(pdf_path)
        pages = insp.get("page_count") or {
            "DP1026": 104, "DP1027": 90, "DP1028": 102, "DP1029": 91
        }.get(product_id, 100)
        r = calculate_royalty(planner["kdp_target_price"], pages)
        print(
            f"  {product_id:<10} {pages:>6} "
            f"  ${r['list_price']:.2f}  ${r['net_royalty']:>6.2f}  {r['margin_pct']:>5.1f}%"
        )


def cmd_royalties() -> None:
    """Show royalty calculations at all price points for all planners."""
    print("\nKDP Royalty Calculator — Color Interior")
    print(f"Formula: (List Price × 60%) − ($0.85 + pages × $0.012)")
    print("=" * 72)

    for product_id, planner in KDP_PLANNERS.items():
        pdf_path = PRODUCT_FILES_DIR / planner["pdf_file"]
        insp = inspect_pdf(pdf_path)
        pages = insp.get("page_count") or {
            "DP1026": 104, "DP1027": 90, "DP1028": 102, "DP1029": 91
        }.get(product_id, 100)

        printing_cost = KDP_BASE_PRINTING_COST + pages * KDP_PER_PAGE_PRINTING_COST
        breakeven = printing_cost / KDP_ROYALTY_RATE

        print(f"\n{product_id} — {planner['kdp_title']}")
        print(f"  Pages: {pages}  |  Printing cost: ${printing_cost:.3f}  |  Break-even price: ${breakeven:.2f}")
        print(f"  Etsy price: ${planner['etsy_price']:.2f}  |  Recommended KDP price: ${planner['kdp_target_price']:.2f}")
        print(f"  {'List Price':>10}  {'Print Cost':>10}  {'Gross Roy':>9}  {'Net Roy':>8}  {'Margin':>7}")
        print(f"  {'-'*10}  {'-'*10}  {'-'*9}  {'-'*8}  {'-'*7}")

        for price in ROYALTY_TEST_PRICES:
            r = calculate_royalty(price, pages)
            marker = " ← recommended" if price == planner["kdp_target_price"] else ""
            marker = marker or (" ← optimal" if price == find_optimal_price(pages).get("list_price") else "")
            print(
                f"  ${price:>9.2f}  ${r['printing_cost']:>9.4f}  "
                f"${r['gross_royalty']:>8.4f}  ${r['net_royalty']:>7.4f}  "
                f"{r['margin_pct']:>5.1f}%{marker}"
            )


def cmd_prepare(product_id: str) -> None:
    """Prepare a single book for KDP submission."""
    product_id = product_id.upper().strip()
    if product_id not in KDP_PLANNERS:
        print(f"ERROR: Unknown product ID '{product_id}'")
        print(f"Valid IDs: {', '.join(KDP_PLANNERS.keys())}")
        sys.exit(1)
    submission = build_kdp_submission(product_id)
    print(f"\nKDP submission prepared successfully.")
    print(f"Next step: Review data/kdp/{product_id}_kdp_submission.json")
    print(f"Then follow the checklist to create the KDP listing.")


def cmd_all() -> None:
    """Prepare all 4 planners for KDP submission."""
    print("Preparing all 4 planners for Amazon KDP submission...")
    results = {}
    for product_id in KDP_PLANNERS:
        try:
            submission = build_kdp_submission(product_id)
            results[product_id] = "success"
        except Exception as exc:
            print(f"  ERROR preparing {product_id}: {exc}")
            results[product_id] = f"error: {exc}"

    # Write setup guide
    _write_setup_guide()

    print(f"\n{'='*60}")
    print("Summary:")
    for pid, status in results.items():
        print(f"  {pid}: {status}")

    print(f"\nOutput files:")
    for pid in KDP_PLANNERS:
        out = KDP_DIR / f"{pid}_kdp_submission.json"
        if out.exists():
            print(f"  {out.relative_to(BASE)}")
    guide = KDP_DIR / "kdp_setup_guide.md"
    print(f"  {guide.relative_to(BASE)}")
    print(f"\nNext step: Read data/kdp/kdp_setup_guide.md for full setup instructions.")


def _write_setup_guide() -> None:
    """Write the KDP account setup guide for Scott."""
    KDP_DIR.mkdir(parents=True, exist_ok=True)
    guide_path = KDP_DIR / "kdp_setup_guide.md"

    content = f"""# Amazon KDP Setup Guide — OnBrandCraftz
*Generated {date.today()} by kdp_publisher.py*

Amazon KDP (Kindle Direct Publishing) lets you sell physical print-on-demand books.
Customers order on Amazon, Amazon prints and ships, you collect royalties.
Zero inventory. Zero fulfillment. Passive revenue from planners already built.

---

## Step 1 — Create Your KDP Account

1. Go to **https://kdp.amazon.com**
2. Sign in with your Amazon account (create one if needed — use Printing3dthings@outlook.com)
3. Click **Get Started** and complete the publisher profile
4. Required info:
   - Legal name (Scott's full legal name)
   - Address (US address for tax purposes)
   - Phone number
   - Bank account for royalty deposits (routing + account number)

---

## Step 2 — Complete the Tax Interview

**Do this before publishing anything — required for royalty payment.**

1. In KDP Dashboard → top-right menu → **Account** → **Tax Information**
2. Click **Start Interview**
3. For US persons: choose **Individual** → enter SSN or EIN
4. Sign the W-9 form digitally
5. KDP withholds 30% if tax interview is not completed

**Pro tip:** If you have a single-member LLC, use the LLC's EIN instead of SSN — protects your personal SSN.

---

## Step 3 — Understand KDP Royalties (Color Interiors)

Our planners are COLOR interiors (they have color on every page).
KDP royalty formula for color paperbacks:

```
Net Royalty = (List Price × 60%) − Printing Cost
Printing Cost = $0.85 + (pages × $0.012)
```

| Book | Pages | Print Cost | @$17.99 Royalty | @$16.99 Royalty |
|------|-------|------------|-----------------|-----------------|
| DP1026 Life Planner | 104 | $2.098 | $8.69 | $8.09 |
| DP1027 Student Planner | 90 | $1.930 | $8.86 | $8.26 |
| DP1028 Budget Planner | 112 | $2.194 | $8.59 | $7.99 |
| DP1029 Fitness Planner | 102 | $2.074 | $8.72 | $8.12 |

**Recommended pricing: $16.99–$17.99 per planner** — strong margin, competitive on Amazon.

---

## Step 4 — Create a New Paperback Title

For each planner:

1. KDP Dashboard → **Create** → **Paperback**

### Book Details tab:
- **Title**: See `data/kdp/DP####_kdp_submission.json` → `kdp_metadata.title`
- **Subtitle**: See json file → `kdp_metadata.subtitle`
- **Author**: OnBrandCraftz
- **Description**: Copy from json file → `kdp_metadata.description`
- **Keywords**: Enter the 7 keywords from json file (one per field)
- **Categories**: Select 2 from BISAC list (see json file → `kdp_metadata.categories`)
- **Language**: English
- **AI content**: Check **Yes** — our planners use AI-generated cover art

### Book Content tab:
- **ISBN**: Leave blank (KDP assigns a free ISBN)
- **Print options**:
  - Interior & paper type: **Color, White paper**
  - Trim size: **8.5 × 11 inches**
  - Bleed settings: **No bleed**
  - Paperback cover finish: **Matte** (recommended — feels premium, matches kawaii aesthetic)
- **Manuscript**: Upload interior PDF (see json file → `interior.pdf_file`)
- **Cover**: Either upload the cover PDF or use KDP Cover Creator

---

## Step 5 — Create the Cover

**Option A (Recommended): KDP Cover Creator (free)**
1. In the Book Content tab, select **Launch Cover Creator**
2. Choose a template or start blank
3. Upload the kawaii cover image as the front cover artwork
4. KDP auto-calculates and places the spine — verify the spine width matches the calculation
5. Add your title to the spine (small text)
6. Leave back cover simple: shop name + short description + barcode area

**Option B: Custom cover in Canva/Photoshop**
- Required dimensions per book (see json → `cover.cover_dimensions_note`)
- Must be a single full-bleed PDF: back cover + spine + front cover in one file
- Spine widths:
  - DP1026 (104 pages): see `DP1026_kdp_submission.json` → `cover.spine_width_inches`
  - DP1027 (90 pages): see `DP1027_kdp_submission.json` → `cover.spine_width_inches`
  - DP1028 (112 pages): see `DP1028_kdp_submission.json` → `cover.spine_width_inches`
  - DP1029 (102 pages): see `DP1029_kdp_submission.json` → `cover.spine_width_inches`

---

## Step 6 — Set Pricing and Distribution

1. **Territories**: All territories worldwide
2. **Primary marketplace**: amazon.com (US)
3. **List price**: Set per the recommendations in each json file
4. **KDP Select**: **Do NOT enroll** — this requires exclusivity and would conflict with Etsy digital sales
5. **Expanded Distribution**: **Enable** — reaches bookstores, libraries, and educational institutions
   - Note: Expanded distribution uses a 40% royalty rate (vs 60% for Amazon direct)

---

## Step 7 — Review and Publish

1. Click **Launch Previewer** to verify interior and cover
2. Check every page — look for text cut off near margins, color accuracy
3. Order a **proof copy** ($4–8 + shipping) before approving for sale — worth it
4. Once you approve the proof: click **Publish**
5. KDP review: 24–72 hours
6. Book live on Amazon within 72 hours of approval

---

## Step 8 — Cross-Promote on Etsy

Once each book is live on Amazon:

1. Grab the Amazon product URL
2. Add to the bottom of the Etsy listing description:
   > "Prefer a physical printed copy? Order the paperback edition on Amazon → [Amazon link]"
3. This adds buyer confidence (Amazon = trusted) without cannibalizing digital sales
   (Most buyers who want digital WILL NOT buy the $17.99 physical copy — different buyer intent)

---

## Checklist Files

Each planner has a detailed submission JSON with a step-by-step checklist:
- `data/kdp/DP1026_kdp_submission.json`
- `data/kdp/DP1027_kdp_submission.json`
- `data/kdp/DP1028_kdp_submission.json`
- `data/kdp/DP1029_kdp_submission.json`

Run anytime to refresh:
```
python tools/kdp_publisher.py --all
python tools/kdp_publisher.py --royalties
python tools/kdp_publisher.py --check
```

---

## Revenue Projection

At $17.99 list price, $8.69 average royalty per copy:

| Monthly Amazon Sales | Monthly Royalty | Annual |
|---------------------|-----------------|--------|
| 10 copies (all books) | ~$87 | ~$1,044 |
| 50 copies | ~$435 | ~$5,220 |
| 100 copies | ~$869 | ~$10,428 |

This is **passive revenue** — once the books are published, Amazon handles everything.
Each new planner product adds to the revenue stack with zero additional fulfillment work.

---

*OnBrandCraftz — Built with tools/kdp_publisher.py*
"""
    guide_path.write_text(content)
    print(f"  Saved: {guide_path.relative_to(BASE)}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="kdp_publisher.py",
        description="Amazon KDP preparation tool for OnBrandCraftz planners",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check",
        action="store_true",
        help="Check all PDFs against KDP requirements",
    )
    group.add_argument(
        "--prepare",
        metavar="PRODUCT_ID",
        help="Prepare one book (e.g. DP1026)",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Prepare all 4 planners for KDP submission",
    )
    group.add_argument(
        "--royalties",
        action="store_true",
        help="Show royalty calculations at different price points",
    )

    args = parser.parse_args()

    KDP_DIR.mkdir(parents=True, exist_ok=True)

    if args.check:
        cmd_check()
    elif args.prepare:
        cmd_prepare(args.prepare)
    elif args.all:
        cmd_all()
    elif args.royalties:
        cmd_royalties()


if __name__ == "__main__":
    main()
