#!/usr/bin/env python3
"""
listing_integrity_check.py
Audits every active Etsy listing against data/listing_manifest.json.

FAST mode (default): API-only — title length, tag count, file names,
photo count. Completes in 2-5 minutes for the full shop.

FULL mode (--full): also downloads the hero photo for each listing,
computes its perceptual hash, and compares it to the registered art
hash. Catches "wrong art in listing photo" at the pixel level.
Runs in 15-30 minutes depending on connection speed.

Usage:
    python tools/listing_integrity_check.py           # fast audit, all listings
    python tools/listing_integrity_check.py --full    # + photo hash check
    python tools/listing_integrity_check.py --id 4515674594   # single listing
    python tools/listing_integrity_check.py --fix-titles      # auto-fix titles >70 chars
    python tools/listing_integrity_check.py --save            # save report to review_batches/

Exit codes:
    0  All listings pass
    1  One or more FAIL items found
    2  Warnings only (no failures)
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
import io
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

from etsy_api import EtsyAPIClient

MANIFEST_PATH = BASE_DIR / "data" / "listing_manifest.json"
MAP_PATH = BASE_DIR / "data" / "dp_listing_map.json"
REPORT_DIR = BASE_DIR / "review_batches"

TITLE_MAX = 70
TAG_MAX_CHARS = 20
TAGS_REQUIRED = 13
HASH_TOLERANCE = 25   # Hamming distance threshold; <25 = same image


# ---------------------------------------------------------------------------
# Perceptual hash helpers
# ---------------------------------------------------------------------------

def dhash16(image_bytes: bytes) -> str | None:
    if not PIL_OK:
        return None
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            gray = img.convert("L").resize((17, 16), Image.Resampling.LANCZOS)
            pixels = list(gray.getdata())
            bits = []
            for row in range(16):
                for col in range(16):
                    bits.append("1" if pixels[row * 17 + col] > pixels[row * 17 + col + 1] else "0")
            return hex(int("".join(bits), 2))[2:].zfill(64)
    except Exception:
        return None


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(
        bin(int(a, 16))[2:].zfill(256),
        bin(int(b, 16))[2:].zfill(256)
    ))


def fetch_url(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def check_title(title: str) -> list[dict]:
    issues = []
    if len(title) > TITLE_MAX:
        issues.append({
            "severity": "FAIL",
            "check": "title_length",
            "detail": f"Title is {len(title)} chars (max {TITLE_MAX}): {title[:60]}…"
        })
    return issues


def check_tags(tags: list[str]) -> list[dict]:
    issues = []
    if len(tags) < TAGS_REQUIRED:
        issues.append({
            "severity": "FAIL",
            "check": "tag_count",
            "detail": f"Only {len(tags)} tags (need {TAGS_REQUIRED})"
        })
    for tag in tags:
        if len(tag) > TAG_MAX_CHARS:
            issues.append({
                "severity": "WARN",
                "check": "tag_length",
                "detail": f"Tag '{tag}' is {len(tag)} chars (max {TAG_MAX_CHARS})"
            })
    return issues


def check_files(actual_files: list[dict], expected_patterns: list[str],
                expected_count: int) -> list[dict]:
    issues = []
    actual_names = [f.get("filename", "") for f in actual_files]

    # Count check
    if len(actual_files) < expected_count:
        issues.append({
            "severity": "FAIL",
            "check": "file_count",
            "detail": f"Has {len(actual_files)} file(s), expected {expected_count}: {actual_names}"
        })
    elif len(actual_files) == 0 and expected_count == 0:
        pass  # OK — no files expected

    # Pattern check
    for pattern in expected_patterns:
        matched = any(pattern in name for name in actual_names)
        if not matched:
            issues.append({
                "severity": "FAIL",
                "check": "file_match",
                "detail": f"Expected file containing '{pattern}' not found. Actual: {actual_names}"
            })

    return issues


def check_photos(images: list[dict], min_count: int) -> list[dict]:
    issues = []
    if len(images) < min_count:
        issues.append({
            "severity": "WARN" if len(images) >= max(1, min_count - 2) else "FAIL",
            "check": "photo_count",
            "detail": f"Only {len(images)} photos (want ≥{min_count})"
        })
    return issues


def check_ai_disclosure(description: str) -> list[dict]:
    desc_lower = description.lower()
    has_disclosure = (
        "ai" in desc_lower and "design" in desc_lower
    ) or "ai image" in desc_lower or "ai tool" in desc_lower or "🤖" in description
    if not has_disclosure:
        return [{
            "severity": "WARN",
            "check": "ai_disclosure",
            "detail": "No AI disclosure found in description (required by Etsy June 2025 policy)"
        }]
    return []


def check_photo_hash(images: list[dict], art_hashes: dict) -> list[dict]:
    """Download hero image and compare hash to registered art. --full mode only."""
    if not PIL_OK or not art_hashes:
        return []
    if not images:
        return [{
            "severity": "FAIL",
            "check": "photo_hash",
            "detail": "No listing images to verify"
        }]

    # Get hero image (rank 1)
    hero = sorted(images, key=lambda x: x.get("rank", 99))[0]
    url = hero.get("url_fullxfull") or hero.get("url_570xN") or ""
    if not url:
        return []

    img_bytes = fetch_url(url)
    if not img_bytes:
        return [{"severity": "WARN", "check": "photo_hash", "detail": "Could not download hero image"}]

    actual_hash = dhash16(img_bytes)
    if not actual_hash:
        return []

    # Compare against each registered art hash
    best_distance = 999
    best_dp = None
    for dp_code, expected_hash in art_hashes.items():
        d = hamming(actual_hash, expected_hash)
        if d < best_distance:
            best_distance = d
            best_dp = dp_code

    if best_distance <= HASH_TOLERANCE:
        return []  # Match found — photo is correct

    return [{
        "severity": "FAIL",
        "check": "photo_hash",
        "detail": (f"Hero photo hash does not match registered art "
                   f"(best match {best_dp} has Hamming distance {best_distance}, "
                   f"threshold {HASH_TOLERANCE}). Wrong art in listing photo.")
    }]


# ---------------------------------------------------------------------------
# Core audit function for a single listing
# ---------------------------------------------------------------------------

def audit_listing(api: EtsyAPIClient, listing_id: str, manifest_entry: dict,
                  full_mode: bool = False) -> dict:
    result = {
        "listing_id": listing_id,
        "dp_codes": manifest_entry["dp_codes"],
        "type": manifest_entry["type"],
        "issues": [],
        "status": "PASS",
        "title": "",
        "photo_count": 0,
        "file_count": 0,
        "tag_count": 0,
    }

    # -- Fetch listing --
    try:
        listing = api._request("GET", f"listings/{listing_id}")
    except Exception as e:
        result["issues"].append({
            "severity": "FAIL",
            "check": "listing_fetch",
            "detail": f"Could not fetch listing: {e}"
        })
        result["status"] = "FAIL"
        return result

    # State check
    state = listing.get("state", "")
    if state not in ("active", "edit"):
        result["issues"].append({
            "severity": "INFO",
            "check": "state",
            "detail": f"Listing state is '{state}' (not active)"
        })

    title = listing.get("title", "")
    result["title"] = title
    description = listing.get("description", "")
    tags = listing.get("tags", [])
    result["tag_count"] = len(tags)

    result["issues"].extend(check_title(title))
    result["issues"].extend(check_tags(tags))
    result["issues"].extend(check_ai_disclosure(description))

    # -- Fetch files --
    try:
        files_resp = api._request("GET", f"shops/{api.shop_id}/listings/{listing_id}/files")
        files = files_resp.get("results", [])
    except Exception:
        files = []

    result["file_count"] = len(files)
    result["issues"].extend(check_files(
        files,
        manifest_entry.get("expected_files", []),
        manifest_entry.get("expected_file_count", 0)
    ))

    # -- Fetch images --
    # NOTE: shops/{shop_id}/listings/{lid}/images returns 404; use listing-level endpoint
    try:
        images_resp = api._request("GET", f"listings/{listing_id}/images")
        images = images_resp.get("results", [])
    except Exception:
        images = []

    result["photo_count"] = len(images)
    result["issues"].extend(check_photos(images, manifest_entry.get("min_photo_count", 3)))

    # -- Photo hash (full mode only) --
    if full_mode and manifest_entry.get("art_hashes"):
        result["issues"].extend(check_photo_hash(images, manifest_entry["art_hashes"]))
        time.sleep(0.3)  # Respectful pause after image download

    # Compute final status
    severities = [i["severity"] for i in result["issues"]]
    if "FAIL" in severities:
        result["status"] = "FAIL"
    elif "WARN" in severities:
        result["status"] = "WARN"

    return result


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

SEVERITY_ORDER = {"FAIL": 0, "WARN": 1, "INFO": 2}
SEVERITY_ICON = {"FAIL": "✗", "WARN": "⚠", "INFO": "ℹ", "PASS": "✓"}


def render_report(results: list[dict], elapsed: float) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append("LISTING INTEGRITY REPORT")
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("=" * 70)

    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    pass_count = sum(1 for r in results if r["status"] == "PASS")

    lines.append(f"\nSUMMARY: {len(results)} listings audited in {elapsed:.0f}s")
    lines.append(f"  ✓ PASS: {pass_count}   ⚠ WARN: {warn_count}   ✗ FAIL: {fail_count}")

    # Group by status
    for status_filter in ("FAIL", "WARN", "PASS"):
        group = [r for r in results if r["status"] == status_filter]
        if not group:
            continue
        lines.append(f"\n{'—'*70}")
        lines.append(f"{SEVERITY_ICON[status_filter]} {status_filter} ({len(group)} listings)")
        lines.append("—" * 70)

        for r in group:
            dp = ", ".join(r["dp_codes"]) if r["dp_codes"] else "?"
            title_short = r["title"][:55] + "…" if len(r["title"]) > 55 else r["title"]
            lines.append(f"\n  [{r['listing_id']}] {dp} — {title_short}")
            lines.append(f"  Type: {r['type']} | Photos: {r['photo_count']} | "
                         f"Files: {r['file_count']} | Tags: {r['tag_count']}")

            for issue in sorted(r["issues"], key=lambda x: SEVERITY_ORDER.get(x["severity"], 9)):
                icon = SEVERITY_ICON.get(issue["severity"], "?")
                lines.append(f"    {icon} [{issue['check']}] {issue['detail']}")

    lines.append("\n" + "=" * 70)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Audit Etsy listings against the manifest")
    parser.add_argument("--full", action="store_true",
                        help="Download hero photos and verify perceptual hashes")
    parser.add_argument("--id", metavar="LISTING_ID",
                        help="Audit a single listing ID only")
    parser.add_argument("--type", metavar="TYPE",
                        help="Audit only listings of a given type (e.g. wall_art)")
    parser.add_argument("--save", action="store_true",
                        help="Save report to review_batches/integrity_YYYYMMDD.txt")
    parser.add_argument("--fix-titles", action="store_true",
                        help="Auto-fix titles longer than 70 chars by truncating at last word boundary")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print("ERROR: data/listing_manifest.json not found.")
        print("Run: python tools/build_manifest.py")
        sys.exit(1)

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    api = EtsyAPIClient()

    # Filter manifest entries
    to_audit: dict = manifest
    if args.id:
        to_audit = {args.id: manifest[args.id]} if args.id in manifest else {}
        if not to_audit:
            print(f"Listing ID {args.id} not in manifest.")
            sys.exit(1)
    if args.type:
        to_audit = {k: v for k, v in manifest.items() if v.get("type") == args.type}

    print(f"Auditing {len(to_audit)} listings ({'full' if args.full else 'fast'} mode)…")
    if args.full:
        print("WARNING: full mode downloads hero images — this may take 15-30 minutes.")
    print()

    results = []
    start = time.time()
    failed_titles: list[tuple[str, str, str]] = []  # (listing_id, title, truncated)

    for i, (listing_id, entry) in enumerate(to_audit.items(), 1):
        r = audit_listing(api, listing_id, entry, full_mode=args.full)
        results.append(r)

        # Progress indicator
        icon = SEVERITY_ICON.get(r["status"], "?")
        dp = ", ".join(r["dp_codes"][:2]) if r["dp_codes"] else "?"
        print(f"  {icon} [{i}/{len(to_audit)}] {listing_id} ({dp}) — {r['status']}")
        for issue in r["issues"]:
            if issue["severity"] in ("FAIL",):
                print(f"      ↳ {issue['check']}: {issue['detail'][:80]}")

        # Collect titles needing fix
        if args.fix_titles and len(r["title"]) > TITLE_MAX:
            # Truncate at last space within limit
            truncated = r["title"][:TITLE_MAX].rsplit(" ", 1)[0]
            failed_titles.append((listing_id, r["title"], truncated))

        time.sleep(0.4)  # Respect API rate limits

    elapsed = time.time() - start
    report = render_report(results, elapsed)
    print("\n" + report)

    # Save report
    if args.save:
        REPORT_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        report_path = REPORT_DIR / f"integrity_{stamp}.txt"
        report_path.write_text(report)
        print(f"\nReport saved → {report_path}")

    # Update manifest with verification timestamps
    for r in results:
        if r["listing_id"] in manifest:
            manifest[r["listing_id"]]["last_verified"] = datetime.now(timezone.utc).isoformat()
            manifest[r["listing_id"]]["last_status"] = r["status"]
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    # Auto-fix titles if requested
    if args.fix_titles and failed_titles:
        print(f"\nAuto-fixing {len(failed_titles)} oversized titles…")
        for listing_id, old_title, new_title in failed_titles:
            print(f"  {listing_id}: {len(old_title)} → {len(new_title)} chars")
            print(f"    Before: {old_title}")
            print(f"    After:  {new_title}")
            try:
                api._request("PATCH", f"shops/{api.shop_id}/listings/{listing_id}",
                             body={"title": new_title})
                print(f"    ✓ Updated")
            except Exception as e:
                print(f"    ✗ Error: {e}")
            time.sleep(0.5)

    # Exit code
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    if fail_count:
        sys.exit(1)
    if warn_count:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
