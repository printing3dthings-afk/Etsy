"""
Automated listing quality checker — Maker/Checker pattern.

Runs machine-verifiable QC gates from CLAUDE.md against draft listing content
before it reaches Scott's review queue. Frank calls this after generating listing
content (Maker pass) and before presenting to Scott (human Checker). If errors > 0,
fix them first — don't surface content that fails automated gates.

Called via the check_listing_quality agent tool in main.py.
Standalone: from tools.listing_qc import check_listing; print(check_listing(...))
"""

from __future__ import annotations

import re
from typing import Literal

ProductType = Literal["digital_planner", "svg_pack", "wall_art"]

_PRICE_OK_CENTS = {99, 97, 49}

_REQUIRED_SECTIONS_PLANNER = [
    ("WHAT'S INCLUDED", "what's included"),
    ("COMPATIBLE APPS", "compatible apps"),
    ("HOW TO USE", "how to use"),
    ("TECHNICAL DETAILS", "technical details"),
    ("FAQ", "faq"),
    ("COPYRIGHT", "copyright"),
]

_REQUIRED_SECTIONS_SVG = [
    ("WHAT'S INCLUDED", "what's included"),
    ("HOW TO PRINT", "how to print"),
    ("TECHNICAL DETAILS", "technical details"),
    ("FAQ", "faq"),
    ("COPYRIGHT", "copyright"),
]

# Keyword signals for wall art tag category coverage
_WALL_ART_TAG_CATEGORIES: dict[str, list[str]] = {
    "style": ["boho", "minimalist", "bohemian", "cottagecore", "dark academia",
              "watercolor", "botanical", "abstract", "vintage", "modern"],
    "room": ["bedroom", "living room", "office", "kitchen", "bathroom",
              "nursery", "entryway", "hallway", "dining"],
    "medium": ["watercolor print", "line art", "digital art", "illustration",
               "photography", "oil painting"],
    "occasion": ["housewarming", "housewarming gift", "gallery wall", "new home", "wedding gift"],
    "recipient": ["gift for her", "gift for mom", "nature lover", "art lover",
                  "gift for women"],
    "format": ["printable", "instant download", "digital download", "downloadable art",
               "printable poster"],
}


def _detect_product_type(title: str, description: str) -> ProductType:
    title_l = title.lower()
    if "svg" in title_l or "3d print" in title_l or "bambu" in title_l:
        return "svg_pack"
    if "wall art" in title_l or ("printable" in title_l and "planner" not in title_l):
        return "wall_art"
    return "digital_planner"


def _price_suffix_ok(price: float) -> bool:
    return round(price * 100) % 100 in _PRICE_OK_CENTS


def _tag_has_special_chars(tag: str) -> bool:
    return bool(re.search(r'[,&|;:!@#$%^*+=<>{}[\]\\"\'\/]', tag))


def _tags_duplicating_title(title: str, tags: list[str]) -> list[str]:
    title_l = title.lower()
    return [t for t in tags if t.lower() in title_l]


# ── universal checks (all product types) ───────────────────────────────────────

def _check_universal(title: str, tags: list[str], price: float) -> list[dict]:
    f: list[dict] = []

    tlen = len(title)
    if tlen > 140:
        # 2026-08-10: raised from a flat 70-char cap to Etsy's real 140-char
        # platform max -- see etsy_api.py's pre_publish_gate() for the sourced
        # competitive research that contradicted the old unsourced 70-char claim.
        f.append({
            "check": "Title ≤ 140 chars",
            "severity": "error",
            "actual": f"{tlen} chars",
            "expected": "≤ 140 chars",
            "note": "Etsy's hard platform max for a listing title is 140 characters",
        })
    elif tlen < 20:
        f.append({
            "check": "Title ≥ 20 chars",
            "severity": "warning",
            "actual": f"{tlen} chars",
            "expected": "≥ 20 chars",
        })

    if len(tags) < 13:
        f.append({
            "check": "All 13 tags used",
            "severity": "error",
            "actual": f"{len(tags)} tags",
            "expected": "exactly 13",
            "note": "Every empty slot is a missed ranking opportunity",
        })
    elif len(tags) > 13:
        f.append({
            "check": "Max 13 tags",
            "severity": "error",
            "actual": f"{len(tags)} tags",
            "expected": "exactly 13",
        })

    long_tags = [t for t in tags if len(t) > 20]
    if long_tags:
        f.append({
            "check": "Each tag ≤ 20 chars",
            "severity": "error",
            "actual": f"{len(long_tags)} too long: {long_tags}",
            "expected": "all tags ≤ 20 chars (Etsy hard limit)",
        })

    bad_tags = [t for t in tags if _tag_has_special_chars(t)]
    if bad_tags:
        f.append({
            "check": "Tags: no special characters",
            "severity": "error",
            "actual": f"Special chars in: {bad_tags}",
            "expected": "alphanumeric and spaces only",
        })

    dupes = _tags_duplicating_title(title, tags)
    if dupes:
        f.append({
            "check": "No tags duplicate title phrases",
            "severity": "warning",
            "actual": f"Title overlap: {dupes}",
            "expected": "tags cover new keyword territory not already in the title",
        })

    if not _price_suffix_ok(price):
        cents = round(price * 100) % 100
        f.append({
            "check": "Price ends in .99 / .97 / .49",
            "severity": "error",
            "actual": f"${price:.2f} (ends .{cents:02d})",
            "expected": ".99, .97, or .49 — round numbers underperform",
        })

    return f


# ── digital planner checks ─────────────────────────────────────────────────────

def _check_digital_planner(title: str, description: str, price: float) -> list[dict]:
    f: list[dict] = []
    title_l = title.lower()
    desc_l = description.lower()

    if "instant download" not in title_l:
        f.append({
            "check": "Title: 'Instant Download'",
            "severity": "error",
            "actual": "missing",
            "expected": "required keyword for SEO and buyer expectation-setting",
        })

    has_year = bool(re.search(r'\b202[5-9]\b|\b203\d\b', title))
    if not has_year and "undated" not in title_l:
        f.append({
            "check": "Title: year (e.g. 2026) or 'Undated'",
            "severity": "warning",
            "actual": "neither found",
            "expected": "year anchors dated version; 'Undated' signals the evergreen version",
        })

    apps = ["goodnotes", "notability", "ipad"]
    if not any(a in title_l for a in apps):
        f.append({
            "check": "Title: app name (GoodNotes / Notability / iPad)",
            "severity": "warning",
            "actual": "none found",
            "expected": "app compatibility in title boosts match on buyer search queries",
        })

    first_200 = description[:200].lower()
    if "instant download" not in first_200 and "digital download" not in first_200:
        f.append({
            "check": "Description first 200 chars: 'instant download' or 'digital download'",
            "severity": "warning",
            "actual": "not found",
            "expected": "required for mobile fold visibility and Google indexing",
        })

    missing = [label for label, kw in _REQUIRED_SECTIONS_PLANNER if kw not in desc_l]
    if missing:
        f.append({
            "check": "Description: all required sections present",
            "severity": "error",
            "actual": f"Missing: {missing}",
            "expected": "WHAT'S INCLUDED · COMPATIBLE APPS · HOW TO USE · TECHNICAL DETAILS · FAQ · COPYRIGHT",
        })

    if price < 7.99 or price > 29.99:
        f.append({
            "check": "Price in expected range ($7.99–$29.99)",
            "severity": "warning",
            "actual": f"${price:.2f}",
            "expected": "DP1026 $14.99 · DP1027 $9.99 · DP1028–29 $12.99",
        })

    return f


# ── SVG pack checks ────────────────────────────────────────────────────────────

def _check_svg_pack(title: str, description: str, price: float) -> list[dict]:
    f: list[dict] = []
    title_l = title.lower()
    desc_l = description.lower()

    if "svg" not in title[:30].lower():
        f.append({
            "check": "Title: 'SVG' within first 30 chars",
            "severity": "error",
            "actual": f"SVG not found in '{title[:30]}'",
            "expected": "SVG near title start — Etsy weights first 30 chars most",
        })

    if "instant download" not in title_l:
        f.append({
            "check": "Title: 'Instant Download'",
            "severity": "error",
            "actual": "missing",
            "expected": "required",
        })

    has_disclaimer = (
        "not a physical" in desc_l
        or "no physical" in desc_l
        or "digital download" in desc_l
    )
    if not has_disclaimer:
        f.append({
            "check": "Description: physical item disclaimer",
            "severity": "error",
            "actual": "not found",
            "expected": "⚠️ DISCLAIMER above the fold: 'DIGITAL DOWNLOAD … NOT a physical sign'",
        })

    if "split by color" in desc_l:
        f.append({
            "check": "Description: no 'Split by Color'",
            "severity": "error",
            "actual": "'Split by Color' found in description",
            "expected": "Must describe Color Painting Fill tool (N key) — 'Split by Color' does not exist in Bambu Studio",
        })

    if "color painting" not in desc_l and "bambu studio" not in desc_l:
        f.append({
            "check": "Description: Bambu Studio Color Painting workflow",
            "severity": "warning",
            "actual": "not found",
            "expected": "HOW TO PRINT IN BAMBU STUDIO section required — use Color Painting Fill tool steps",
        })

    missing = [label for label, kw in _REQUIRED_SECTIONS_SVG if kw not in desc_l]
    if missing:
        f.append({
            "check": "Description: required sections",
            "severity": "error",
            "actual": f"Missing: {missing}",
            "expected": "WHAT'S INCLUDED · HOW TO PRINT · TECHNICAL DETAILS · FAQ · COPYRIGHT",
        })

    if price not in (9.99, 14.99):
        f.append({
            "check": "Price matches SVG tier ($9.99 / $14.99)",
            "severity": "warning",
            "actual": f"${price:.2f}",
            "expected": "$9.99 for 5-design packs · $14.99 for 10+ design packs",
        })

    return f


# ── wall art checks ────────────────────────────────────────────────────────────

def _check_wall_art(title: str, description: str, price: float, tags: list[str]) -> list[dict]:
    f: list[dict] = []
    title_l = title.lower()
    desc_l = description.lower()

    if len(title) < 55:
        f.append({
            "check": "Title ≥ 55 chars",
            "severity": "warning",
            "actual": f"{len(title)} chars",
            "expected": "55–140 chars for wall art listings (real top-favorited competitors cluster 100-140)",
        })

    if "printable" not in title_l:
        f.append({
            "check": "Title: 'printable'",
            "severity": "error",
            "actual": "missing",
            "expected": "required for wall art search category matching",
        })

    if "instant download" not in title_l:
        f.append({
            "check": "Title: 'instant download'",
            "severity": "error",
            "actual": "missing",
            "expected": "required for digital product clarity",
        })

    if "|" in title:
        f.append({
            "check": "Title: comma separators only (no pipes)",
            "severity": "error",
            "actual": "pipe '|' found",
            "expected": "commas only — pipes penalized in 2026 algorithm",
        })

    first_200 = description[:200].lower()
    if "instant download" not in first_200 and "digital" not in first_200:
        f.append({
            "check": "Description first 200 chars: digital/instant download signal",
            "severity": "warning",
            "actual": "not found",
            "expected": "required for mobile fold and Google indexing",
        })

    tag_text = " ".join(tags).lower()
    covered = [
        cat for cat, signals in _WALL_ART_TAG_CATEGORIES.items()
        if any(s in tag_text for s in signals)
    ]
    if len(covered) < 3:
        f.append({
            "check": "Tags: ≥ 3 of 6 intent categories covered",
            "severity": "warning",
            "actual": f"{len(covered)} covered: {covered or 'none'}",
            "expected": "style · room · medium · occasion · recipient · format",
        })

    return f


# ── public entry point ──────────────────────────────────────────────────────────

def check_listing(
    title: str,
    tags: list[str],
    description: str,
    price: float,
    product_type: str = "auto",
) -> dict:
    """
    Run automated QC gates against draft listing content.

    Returns:
      passed        bool   — True only if zero errors (warnings don't block)
      product_type  str    — detected or provided type
      score         str    — "N/M checks passed"
      errors        list   — blocking failures that must be fixed before showing Scott
      warnings      list   — advisory issues worth reviewing
      reminders     list   — human-only checks Frank should surface to Scott explicitly
      title_length  int    — for quick reference
      tag_count     int    — for quick reference
    """
    tags = [t.strip() for t in tags if t.strip()]

    if product_type == "auto":
        product_type = _detect_product_type(title, description)

    all_issues = _check_universal(title, tags, price)

    if product_type == "digital_planner":
        all_issues += _check_digital_planner(title, description, price)
        total_checks = 13
    elif product_type == "svg_pack":
        all_issues += _check_svg_pack(title, description, price)
        total_checks = 13
    elif product_type == "wall_art":
        all_issues += _check_wall_art(title, description, price, tags)
        total_checks = 13
    else:
        total_checks = 6

    errors = [i for i in all_issues if i["severity"] == "error"]
    warnings = [i for i in all_issues if i["severity"] == "warning"]
    passed_count = total_checks - len(errors)

    # Human-only checks — can't be automated, but Frank must surface these to Scott explicitly
    reminders = [
        "All 10 listing photos must show the REAL product — no AI-generated stand-ins",
        "Lifestyle photos must be generated via images.edit with the actual product file as input",
        "Verify all 10 photo slots are unique scenes (no duplicates)",
    ]
    if product_type == "svg_pack":
        reminders += [
            "Photo 7 (How-To) must show Color Painting Fill tool — NOT 'Split by Color'",
            "All 6 lifestyle photos must carry the 'DIGITAL FILE — SVG DOWNLOAD' badge",
            "Run validate_digital_file() on the ZIP — must pass with zero errors",
            "Confirm 3MF files are present (one per design, all color layers pre-assembled)",
        ]
    elif product_type == "digital_planner":
        reminders += [
            "Test PDF in GoodNotes and Notability — opens without errors",
            "Verify all hyperlinked tabs navigate correctly",
            "Sticker pack ZIP: confirm transparent backgrounds (not white fill)",
            "Page count in description matches actual PDF page count exactly",
        ]
    elif product_type == "wall_art":
        reminders += [
            "Master art file ≥ 3,000px on short edge (run tools/upscale_art.py if not)",
            "Multi-size ZIP created via tools/generate_print_sizes.py",
            "Art file is sRGB color space — not AdobeRGB or CMYK",
            "Minimum 2 different room types shown in listing photos",
            "Gallery wall grouping photo included (40% higher multi-purchase rate)",
        ]

    return {
        "passed": len(errors) == 0,
        "product_type": product_type,
        "score": f"{passed_count}/{total_checks} automated checks passed",
        "errors": errors,
        "warnings": warnings,
        "reminders": reminders,
        "title_length": len(title),
        "tag_count": len(tags),
    }
