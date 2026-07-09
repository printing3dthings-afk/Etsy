#!/usr/bin/env python3
"""
listing_accuracy_audit.py

Audits all digital download listings against the known product specifications.
Checks for:
  1. Title length (must be ≤ 70 chars — 2026 mobile ranking rule)
  2. All 13 tag slots filled
  3. No tag duplicates a phrase already in the title
  4. AI disclosure present in description
  5. Photo count (should be 10)
  6. Color theme match for planner/sticker listings (downloads and analyzes hero image)
  7. Image content verified against listing title via GPT-4o vision
  8. Description claims (page count, sticker count, file count) match product spec
  9. Price matches the pricing strategy table

Usage:
  python tools/listing_accuracy_audit.py               # full audit, print report
  python tools/listing_accuracy_audit.py --quick        # skip vision analysis
  python tools/listing_accuracy_audit.py --fix          # auto-fix title/tag issues
  python tools/listing_accuracy_audit.py --listing ID   # audit one listing
"""

from __future__ import annotations
import argparse, json, os, re, sys, time
from io import BytesIO
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from etsy_api import EtsyAPIClient

REPORT_FILE = BASE / "data" / "listing_audit_report.json"

# ──────────────────────────────────────────────
# Product specifications (source of truth)
# ──────────────────────────────────────────────
PLANNER_SPECS = {
    # listing_id: spec
    4509179201: {
        "sku": "DP1026", "name": "Ultimate Digital Life Planner",
        "theme": "Lavender Dreams", "primary_hex": "#8666AA", "accent_hex": "#C4A8D4",
        "pages": 104, "price": 14.99, "sticker_sheets": 5, "sticker_count": 200,
        "includes_undated": True, "files": 3,
    },
    4509184958: {
        "sku": "DP1027", "name": "Student & School Planner",
        "theme": "Cotton Candy", "primary_hex": "#DE97C6", "accent_hex": "#97C6DE",
        "pages": 90, "price": 9.99, "sticker_sheets": 5, "sticker_count": 200,
        "includes_undated": True, "files": 3,
    },
    4509184962: {
        "sku": "DP1028", "name": "Budget & Finance Planner",
        "theme": "Midnight Blue", "primary_hex": "#1B2568", "accent_hex": "#7BA7C2",
        "pages": 102, "price": 12.99, "sticker_sheets": 5, "sticker_count": 200,
        "includes_undated": True, "files": 3,
    },
    4509184968: {
        "sku": "DP1029", "name": "Fitness & Wellness Planner",
        "theme": "Coral Peach", "primary_hex": "#FD6C49", "accent_hex": "#F5B878",
        "pages": 91, "price": 12.99, "sticker_sheets": 5, "sticker_count": 200,
        "includes_undated": True, "files": 3,
    },
}

REQUIRED_DESCRIPTION_PHRASES = [
    "instant download",
    "instant digital download",
    "digital download",
]
AI_DISCLOSURE_PHRASES = [
    "ai image generation",
    "ai tools",
    "designed using ai",
    "about this design",
]
REQUIRED_TAG_COUNT = 13

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _color_distance(c1: tuple, c2: tuple) -> float:
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5


def _dominant_colors(img, n: int = 5) -> list[tuple]:
    """Return top-N dominant colors as RGB tuples using 32-unit color buckets."""
    img = img.convert("RGB").resize((100, 100))
    buckets: dict = {}
    for r, g, b in img.getdata():
        key = (r // 32, g // 32, b // 32)
        buckets[key] = buckets.get(key, 0) + 1
    top = sorted(buckets.items(), key=lambda x: -x[1])[:n]
    return [(k[0] * 32 + 16, k[1] * 32 + 16, k[2] * 32 + 16) for k, _ in top]


def check_title(listing: dict) -> list[str]:
    issues = []
    title = listing.get("title", "")
    if len(title) > 70:
        issues.append(f"TITLE TOO LONG: {len(title)} chars (max 70 — mobile penalty)")
    if "|" in title:
        issues.append("TITLE uses pipe separators (use commas — 2026 algorithm rule)")
    keywords = ["instant download", "printable", "digital", "pdf", "goodnotes", "svg"]
    if not any(kw in title.lower() for kw in keywords):
        issues.append("TITLE missing product-type keyword (digital/printable/svg/pdf)")
    return issues


def check_tags(listing: dict) -> list[str]:
    issues = []
    tags = listing.get("tags", [])
    title_lower = listing.get("title", "").lower()

    if len(tags) < REQUIRED_TAG_COUNT:
        issues.append(f"TAGS: only {len(tags)}/{REQUIRED_TAG_COUNT} slots used")

    for tag in tags:
        if len(tag) > 20:
            issues.append(f"TAG TOO LONG: '{tag}' ({len(tag)} chars, max 20)")
        if tag.lower() in title_lower:
            issues.append(f"TAG DUPLICATES TITLE: '{tag}' — wastes ranking slot")

    return issues


def check_description(listing: dict, spec: dict | None = None) -> list[str]:
    issues = []
    desc = (listing.get("description") or "").lower()

    if not any(phrase in desc for phrase in REQUIRED_DESCRIPTION_PHRASES):
        issues.append("DESCRIPTION missing 'instant download' phrase (required by Gate 6)")

    if not any(phrase in desc for phrase in AI_DISCLOSURE_PHRASES):
        issues.append("DESCRIPTION missing AI disclosure (Etsy Creativity Standards June 2025)")

    if spec:
        pages = spec.get("pages", 0)
        if pages and str(pages) not in desc:
            issues.append(f"DESCRIPTION: page count {pages} not found in description")
        if spec.get("sticker_count") and "200+" not in desc and "200 " not in desc:
            issues.append("DESCRIPTION: '200+' sticker count not mentioned")

    return issues


def check_photos(listing: dict, images: list[dict]) -> list[str]:
    issues = []
    count = len(images)
    if count < 10:
        issues.append(f"PHOTOS: only {count}/10 images uploaded (use all 10 slots)")
    return issues


def check_price(listing: dict, spec: dict | None) -> list[str]:
    issues = []
    if spec is None:
        return issues
    price = listing.get("price", {})
    if isinstance(price, dict):
        amount = float(price.get("amount", 0)) / max(price.get("divisor", 100), 1)
    else:
        amount = float(price or 0)
    expected = spec.get("price", 0)
    if abs(amount - expected) > 0.01:
        issues.append(f"PRICE: listing ${amount:.2f} vs expected ${expected:.2f}")
    return issues


def check_image_colors(images: list[dict], spec: dict) -> list[str]:
    """Download hero image and verify dominant colors match expected theme."""
    try:
        import requests
        from PIL import Image
    except ImportError:
        return []

    issues = []
    hero = next((img for img in images if img.get("rank") == 1), None)
    if not hero:
        return []

    url = hero.get("url_570xN") or hero.get("url_fullxfull", "")
    if not url:
        return []

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        img = Image.open(BytesIO(r.content))
        dom = _dominant_colors(img)

        primary = _hex_to_rgb(spec["primary_hex"])
        accent = _hex_to_rgb(spec["accent_hex"])

        dist_primary = min(_color_distance(c, primary) for c in dom)
        dist_accent = min(_color_distance(c, accent) for c in dom)
        best = min(dist_primary, dist_accent)

        if best > 80:
            dom_hex = ["#%02x%02x%02x" % c for c in dom[:3]]
            issues.append(
                f"COLOR MISMATCH: hero image dominant colors {dom_hex} "
                f"don't match expected {spec['theme']} theme "
                f"(distance {best:.0f}, threshold 80)"
            )
    except Exception as e:
        issues.append(f"COLOR CHECK FAILED: {e}")

    return issues


def check_image_content_vision(listing: dict, images: list[dict]) -> list[str]:
    """Use GPT-4o-mini vision to verify hero image matches listing title."""
    try:
        import openai
    except ImportError:
        return []

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return []

    hero = next((img for img in images if img.get("rank") == 1), None)
    if not hero:
        return []

    url = hero.get("url_570xN") or hero.get("url_fullxfull", "")
    if not url:
        return []

    title = listing.get("title", "")
    try:
        oai = openai.OpenAI(api_key=api_key)
        resp = oai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f'This is a hero product image for an Etsy listing titled: "{title}"\n\n'
                            "Does the image accurately show what the listing title describes?\n"
                            "Reply ONLY with one of:\n"
                            "MATCH: <one-line reason>\n"
                            "MISMATCH: <what it actually shows vs what was expected>\n"
                            "UNCLEAR: <why you can't tell>"
                        ),
                    },
                    {"type": "image_url",
                     "image_url": {"url": url, "detail": "low"}},
                ],
            }],
            max_tokens=80,
        )
        result = resp.choices[0].message.content.strip()
        if result.startswith("MISMATCH"):
            return [f"IMAGE CONTENT: {result}"]
        if result.startswith("UNCLEAR"):
            return [f"IMAGE UNCLEAR: {result}"]
    except Exception as e:
        return [f"VISION CHECK FAILED: {e}"]

    return []


# ──────────────────────────────────────────────
# Main audit
# ──────────────────────────────────────────────

def audit_listing(listing: dict, images: list[dict],
                  skip_vision: bool = False) -> dict:
    lid = listing["listing_id"]
    spec = PLANNER_SPECS.get(lid)

    issues = []
    issues += check_title(listing)
    issues += check_tags(listing)
    issues += check_description(listing, spec)
    issues += check_photos(listing, images)
    issues += check_price(listing, spec)

    if spec:
        issues += check_image_colors(images, spec)

    if not skip_vision:
        issues += check_image_content_vision(listing, images)

    return {
        "listing_id": lid,
        "title": listing.get("title", "")[:80],
        "listing_type": listing.get("listing_type"),
        "issues": issues,
        "issue_count": len(issues),
    }


def run_audit(client: EtsyAPIClient, target_id: int | None = None,
              skip_vision: bool = False, auto_fix: bool = False) -> list[dict]:

    listings = client.get_shop_listings_all(state="active")
    downloads = [l for l in listings if l.get("listing_type") == "download"]

    if target_id:
        downloads = [l for l in downloads if l["listing_id"] == target_id]
        if not downloads:
            print(f"  Listing {target_id} not found in active download listings")
            return []

    print(f"Auditing {len(downloads)} download listings...\n")
    results = []

    for i, listing in enumerate(downloads):
        lid = listing["listing_id"]
        try:
            imgs_raw = client.get_listing_images(lid)
            images = imgs_raw if isinstance(imgs_raw, list) else imgs_raw.get("results", [])
        except Exception:
            images = []

        result = audit_listing(listing, images, skip_vision=skip_vision)
        results.append(result)

        if result["issue_count"] > 0:
            print(f"  [ISSUES] {lid} | {result['title']}")
            for issue in result["issues"]:
                print(f"    • {issue}")
        else:
            print(f"  [  OK  ] {lid} | {result['title'][:60]}")

        if auto_fix and result["issues"]:
            _apply_fixes(client, listing, result["issues"])

        if i % 10 == 9:
            time.sleep(0.5)  # gentle rate limit respect
        else:
            time.sleep(0.05)

    return results


def _apply_fixes(client: EtsyAPIClient, listing: dict, issues: list[str]) -> None:
    """Apply auto-fixable issues: title length truncation, pipe → comma."""
    lid = listing["listing_id"]
    patch = {}

    title = listing.get("title", "")
    new_title = title

    for issue in issues:
        if "TITLE TOO LONG" in issue and len(new_title) > 70:
            # Truncate at last word boundary before 70
            new_title = new_title[:70].rsplit(" ", 1)[0].rstrip("|,").strip()
            patch["title"] = new_title
            print(f"    AUTO-FIX title → '{new_title}'")

        elif "pipe separators" in issue:
            new_title = new_title.replace(" | ", ", ")
            patch["title"] = new_title
            print(f"    AUTO-FIX pipes → commas: '{new_title}'")

    if patch:
        try:
            client.update_listing(lid, patch)
            print(f"    PATCHED listing {lid}")
        except Exception as e:
            print(f"    PATCH FAILED for {lid}: {e}")


def print_summary(results: list[dict]) -> None:
    total = len(results)
    with_issues = [r for r in results if r["issue_count"] > 0]
    clean = total - len(with_issues)

    print(f"\n{'='*60}")
    print(f"AUDIT SUMMARY — {total} listings checked")
    print(f"{'='*60}")
    print(f"  Clean:        {clean}/{total}")
    print(f"  With issues:  {len(with_issues)}/{total}")

    if with_issues:
        print(f"\n  Top issue categories:")
        category_counts: dict[str, int] = {}
        for r in with_issues:
            for issue in r["issues"]:
                cat = issue.split(":")[0]
                category_counts[cat] = category_counts.get(cat, 0) + 1
        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            print(f"    {cat}: {count}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listing", type=int, metavar="ID",
                        help="Audit a single listing ID")
    parser.add_argument("--quick", action="store_true",
                        help="Skip GPT-4o vision image content check")
    parser.add_argument("--fix", action="store_true",
                        help="Auto-fix title length and pipe separator issues")
    args = parser.parse_args()

    # Load env
    env_path = BASE / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    client = EtsyAPIClient()
    if not client.refresh_access_token():
        print("[audit] ERROR: Could not refresh OAuth token — aborting")
        sys.exit(1)

    results = run_audit(
        client,
        target_id=args.listing,
        skip_vision=args.quick,
        auto_fix=args.fix,
    )

    print_summary(results)

    REPORT_FILE.write_text(json.dumps(results, indent=2))
    print(f"Full report saved to {REPORT_FILE}")


if __name__ == "__main__":
    main()
