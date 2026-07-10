#!/usr/bin/env python3
"""
listing_integrity_check.py
Audits every active Etsy listing against data/listing_manifest.json.

FAST mode (default): API-only — title length, tag count, file names,
photo count, description keywords, and approval drift (title/files).
Completes in 2-5 minutes for the full shop.

FULL mode (--full): downloads EVERY listing photo, hashes each one, and
verifies the registered downloadable art appears in at least one photo
(art_match_threshold per listing type, default 80). Also detects approved
photos that have changed. This is the anti-mismatch guarantee: a listing
fails if the file you sell isn't shown in any of its photos.
Runs longer (~131 listings × ~10 photos of downloads).

Rules per listing type live in data/listing_rules.json.
Approved snapshots (locked by approve_listing.py) live in
data/listing_approvals.json. Source-art hashes live in
data/product_art_registry.json (built by build_art_registry.py).

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
import re
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
RULES_PATH = BASE_DIR / "data" / "listing_rules.json"
APPROVALS_PATH = BASE_DIR / "data" / "listing_approvals.json"
REGISTRY_PATH = BASE_DIR / "data" / "product_art_registry.json"
REPORT_DIR = BASE_DIR / "review_batches"

TITLE_MAX = 70
TAG_MAX_CHARS = 20
TAGS_REQUIRED = 13
DEFAULT_ART_THRESHOLD = 80   # Hamming distance; ≤ this means the art IS present in a photo
APPROVAL_DRIFT_TOLERANCE = 10  # photo hash distance above which an approved photo "changed"


def _load_json(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# Perceptual hash helpers
# ---------------------------------------------------------------------------

def dhash16(image_bytes: bytes) -> str | None:
    """
    Compute dhash16, square-normalizing first.
    Source art is portrait (2:3); listing photos are square (1:1). Without
    normalization, even correct art produces distances of 90-130. Center-cropping
    both to square before hashing gives 0-10 for matching art, 90+ for mismatches.
    Must match the implementation in build_art_registry.py exactly.
    """
    if not PIL_OK:
        return None
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            w, h = img.size
            s = min(w, h)
            left = (w - s) // 2
            top = (h - s) // 2
            img = img.crop((left, top, left + s, top + s))
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


_PHOTO_CACHE = None


def _get_photo_cache():
    global _PHOTO_CACHE
    if _PHOTO_CACHE is None:
        from tools.photo_hash_cache import PhotoHashCache
        _PHOTO_CACHE = PhotoHashCache()
    return _PHOTO_CACHE


def _photo_hashes(images: list[dict]) -> dict[str, str]:
    """Return {rank: hash} for every listing photo. --full mode only.

    Uses a persistent URL->hash cache so a photo is only downloaded the first time
    it is ever seen — repeat runs are near-instant and add no rate-limit pressure.
    """
    cache = _get_photo_cache()
    out: dict[str, str] = {}
    for img in sorted(images, key=lambda x: x.get("rank", 99)):
        rank = str(img.get("rank", "?"))
        url = img.get("url_fullxfull") or img.get("url_570xN") or ""
        if not url:
            continue
        was_cached = cache.get(url) is not None
        h = cache.get_or_compute(url, fetch_url, dhash16)
        if h:
            out[rank] = h
        if not was_cached:
            time.sleep(0.15)  # only pace real network fetches, not cache hits
    cache.save()
    return out


def check_art_in_photos(photo_hashes: dict[str, str], dp_codes: list[str],
                        registry: dict, threshold: int) -> list[dict]:
    """Verify the downloadable art appears in AT LEAST ONE listing photo.

    Cross-references the registered source-art hash for each DP code against
    EVERY listing photo. The art is "present" if any photo is within `threshold`
    Hamming distance of the source art. This is the core anti-mismatch check.
    """
    if not PIL_OK or not registry:
        return []
    # Only DP codes that actually have registered art can be checked
    checkable = [dp for dp in dp_codes if registry.get(dp, {}).get("source_hash")]
    if not checkable:
        return []
    if not photo_hashes:
        return [{"severity": "FAIL", "check": "art_in_photos",
                 "detail": "No listing photos could be downloaded to verify art"}]

    best_overall = 999
    best_dp = None
    best_slot = None
    # Each registered DP code must be found in at least one photo
    failures = []
    for dp in checkable:
        art_hash = registry[dp]["source_hash"]
        best_for_dp, best_slot_dp = 999, None
        for slot, ph in photo_hashes.items():
            d = hamming(ph, art_hash)
            if d < best_for_dp:
                best_for_dp, best_slot_dp = d, slot
        if best_for_dp < best_overall:
            best_overall, best_dp, best_slot = best_for_dp, dp, best_slot_dp
        if best_for_dp > threshold:
            failures.append(
                f"{dp} art not found in any of {len(photo_hashes)} photos "
                f"(closest: slot {best_slot_dp}, distance {best_for_dp} > {threshold})"
            )

    if failures:
        return [{"severity": "FAIL", "check": "art_in_photos",
                 "detail": "; ".join(failures)}]
    return [{"severity": "INFO", "check": "art_in_photos",
             "detail": f"Art verified in photos (best: {best_dp} slot {best_slot}, distance {best_overall})"}]


def check_approval(listing_id: str, title: str, tags: list, file_names: list,
                   photo_hashes: dict[str, str], approvals: dict) -> list[dict]:
    """If a listing was locked in as approved, FAIL on any drift from that snapshot."""
    rec = approvals.get(str(listing_id))
    if not rec:
        return []
    issues = []

    if rec.get("title") and title != rec["title"]:
        issues.append({"severity": "FAIL", "check": "approval_drift",
                       "detail": f"Title changed since approval. Approved: '{rec['title'][:50]}…' Now: '{title[:50]}…'"})

    approved_files = set(rec.get("file_names", []))
    current_files = set(file_names)
    if approved_files and approved_files != current_files:
        added = current_files - approved_files
        removed = approved_files - current_files
        detail = "Files changed since approval."
        if removed:
            detail += f" Removed: {sorted(removed)}."
        if added:
            detail += f" Added: {sorted(added)}."
        issues.append({"severity": "FAIL", "check": "approval_drift", "detail": detail})

    # Photo drift — only checkable in --full mode (photo_hashes populated)
    approved_hashes = rec.get("photo_hashes", {})
    if photo_hashes and approved_hashes:
        for slot, app_hash in approved_hashes.items():
            cur = photo_hashes.get(slot)
            if cur is None:
                issues.append({"severity": "FAIL", "check": "approval_drift",
                               "detail": f"Approved photo slot {slot} is missing"})
            elif hamming(cur, app_hash) > APPROVAL_DRIFT_TOLERANCE:
                issues.append({"severity": "FAIL", "check": "approval_drift",
                               "detail": f"Approved photo slot {slot} changed (distance {hamming(cur, app_hash)})"})
    return issues


# Unambiguous physical-fulfillment phrases. NOTE: deliberately excludes
# "physical item" — that appears in the standard digital FAQ line
# ("Q: Is this a physical item? A: No — digital download only") and would
# false-positive every correct listing.
PHYSICAL_PHRASES = [
    "physical print shipped", "shipped directly to you", "arrives at your door",
    "no printing or downloading", "no downloading needed", "ships in",
    "will be shipped", "shipped to you", "ships to your",
]

# Negated disclaimers ("No physical item will be shipped") correctly use
# shipping vocabulary to deny physical fulfillment -- strip these clauses
# before phrase-matching so they don't false-positive PHYSICAL_PHRASES.
# Found 2026-06-17: 24 paper_pack/coloring_pages/svg_bundle listings all use
# this exact disclaimer and were wrongly flagged before this fix.
_NEGATED_SHIPPING_RE = re.compile(
    r"(?:no physical (?:item|product|print|file)s?|nothing)\s+(?:will\s+be|is|are|gets?)\s+shipped"
    r"(?:\s+(?:to\s+\w+|directly))?",
    re.IGNORECASE,
)


def check_fulfillment_match(description: str, fulfillment: str) -> list[dict]:
    """For digital listings, FAIL if the description claims a physical/shipped item.
    This catches the #1 mismatch: a downloadable file sold under a 'ships to your
    door' description (guaranteed refunds + policy risk)."""
    if fulfillment != "digital":
        return []
    desc_lower = _NEGATED_SHIPPING_RE.sub("", description).lower()
    hits = [p for p in PHYSICAL_PHRASES if p in desc_lower]
    if hits:
        return [{"severity": "FAIL", "check": "fulfillment_mismatch",
                 "detail": (f"Digital listing but description claims physical/shipped item "
                            f"(matched: {hits}). Buyer gets a download, not a shipped print.")}]
    return []


def check_description_keywords(description: str, required: list[str]) -> list[dict]:
    desc_lower = description.lower()
    missing = [kw for kw in required if kw.lower() not in desc_lower]
    if missing:
        return [{"severity": "WARN", "check": "description_keywords",
                 "detail": f"Description missing expected keyword(s): {missing}"}]
    return []


# Catches "Set of 4", "pack of 10", "4 prints", "5 designs" etc. -- the exact
# failure mode found on the Four Seasons listing (4512784922): the title and
# description both claimed "all 4" coordinated prints, but the listing
# actually delivered a single design's DP1070_print_sizes.zip -- one design,
# not four, and not even one of the four named ones.
#
# Scoped to the TITLE only (not the full description). The description
# legitimately repeats internal item counts that have nothing to do with a
# "how many designs does this listing represent" claim -- e.g. "11 print-ready
# JPEG files at 300 DPI in one ZIP" (multiple SIZES of ONE design) or
# "10 original Class of 2026 designs" inside a single SVG bundle ZIP (true and
# fine, since the type's rule allows one ZIP to hold N designs). Matching the
# full description against this regex flagged 46 listings, nearly all false
# positives from that boilerplate. The title is where a true "Set of N" /
# "N-piece" marketing promise is actually made.
QUANTITY_CLAIM_RE = re.compile(
    r"\bset of (\d+)\b|\bpack of (\d+)\b|\b(\d+)[\s-]*(?:piece|design|print|watercolor print)s?\b",
    re.IGNORECASE,
)


def check_quantity_claims(title: str, live_file_count: int) -> list[dict]:
    """FAIL if the title claims a design/piece count that doesn't match the
    number of files actually attached to the listing right now. Deliberately
    compares against the LIVE file count fetched from the Etsy API (not any
    manifest field) -- the manifest's dp_codes/expected_file_count can go
    stale (confirmed on listing 4512784817: manifest listed 2 dp_codes, but
    the listing actually delivers 4 separate per-design ZIPs, correctly
    matching its "Set of 4" title -- a manifest-only comparison would have
    wrongly flagged a truthful listing). The live file count is the one
    number that always reflects what the customer is about to receive."""
    if not live_file_count:
        return []
    claims = set()
    for m in QUANTITY_CLAIM_RE.finditer(title):
        for g in m.groups():
            if g:
                n = int(g)
                if n > 1:
                    claims.add(n)
    mismatched = sorted(n for n in claims if n != live_file_count)
    if mismatched:
        return [{"severity": "FAIL", "check": "quantity_claim_mismatch",
                 "detail": (f"Title claims quantity {mismatched} but the listing currently "
                            f"has {live_file_count} file(s) attached. Verify the claim matches "
                            f"what the customer actually receives (Four Seasons failure mode).")}]
    return []


# ---------------------------------------------------------------------------
# Core audit function for a single listing
# ---------------------------------------------------------------------------

def audit_listing(api: EtsyAPIClient, listing_id: str, manifest_entry: dict,
                  rules: dict, approvals: dict, registry: dict,
                  full_mode: bool = False) -> dict:
    ptype = manifest_entry.get("type", "unknown")
    rule = rules.get(ptype, rules.get("unknown", {}))

    result = {
        "listing_id": listing_id,
        "dp_codes": manifest_entry["dp_codes"],
        "type": ptype,
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

    # AI disclosure only enforced when the rule requires it
    if "AI_DISCLOSURE" in rule.get("required_description_sections", []):
        result["issues"].extend(check_ai_disclosure(description))

    # Description keyword coverage (per-type rule)
    result["issues"].extend(
        check_description_keywords(description, rule.get("required_description_keywords", []))
    )

    # Fulfillment match — digital listing must not claim "shipped physical item"
    result["issues"].extend(
        check_fulfillment_match(description, rule.get("fulfillment", "digital"))
    )

    # -- Fetch files --
    try:
        files_resp = api._request("GET", f"shops/{api.shop_id}/listings/{listing_id}/files")
        files = files_resp.get("results", [])
    except Exception:
        files = []
    file_names = [f.get("filename", "") for f in files]

    result["file_count"] = len(files)
    result["issues"].extend(check_files(
        files,
        manifest_entry.get("expected_files", []),
        manifest_entry.get("expected_file_count", 0)
    ))

    # Quantity-claim match — title count claims ("Set of 4") must match the
    # LIVE file count just fetched above. Opt-in per type via
    # "quantity_claim_check" (currently gallery_set only — see notes there).
    if rule.get("quantity_claim_check"):
        result["issues"].extend(check_quantity_claims(title, len(files)))

    # -- Fetch images --
    # NOTE: shops/{shop_id}/listings/{lid}/images returns 404; use listing-level endpoint
    try:
        images_resp = api._request("GET", f"listings/{listing_id}/images")
        images = images_resp.get("results", [])
    except Exception:
        images = []

    result["photo_count"] = len(images)
    result["issues"].extend(check_photos(images, rule.get("min_photos", 3)))

    # -- Photo-dependent checks (full mode downloads & hashes every photo) --
    photo_hashes: dict[str, str] = {}
    if full_mode:
        photo_hashes = _photo_hashes(images)
        # Art-in-photos check (only for types that opt in, e.g. wall_art)
        if rule.get("art_photo_check"):
            threshold = rule.get("art_match_threshold", DEFAULT_ART_THRESHOLD)
            result["issues"].extend(
                check_art_in_photos(photo_hashes, result["dp_codes"], registry, threshold)
            )

    # -- Approval drift (title/files always; photos only in full mode) --
    result["issues"].extend(
        check_approval(listing_id, title, tags, file_names, photo_hashes, approvals)
    )

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
    parser.add_argument("--ids", metavar="ID1,ID2,...",
                        help="Audit a specific comma-separated set of listing IDs "
                             "(used by main.py's _quality_audit_loop to rotate a "
                             "subset of the catalog per day instead of auditing "
                             "everything every run — see ops_runbook.md 2026-07-10)")
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

    rules = _load_json(RULES_PATH)
    approvals = _load_json(APPROVALS_PATH)
    registry = _load_json(REGISTRY_PATH)

    if not rules:
        print("WARNING: data/listing_rules.json not found — using built-in defaults.")
    if args.full and not registry:
        print("WARNING: data/product_art_registry.json not found — art-in-photos check disabled.")
        print("         Run: python tools/build_art_registry.py")

    api = EtsyAPIClient()

    # Filter manifest entries
    to_audit: dict = manifest
    if args.id:
        to_audit = {args.id: manifest[args.id]} if args.id in manifest else {}
        if not to_audit:
            print(f"Listing ID {args.id} not in manifest.")
            sys.exit(1)
    if args.ids:
        wanted = [i.strip() for i in args.ids.split(",") if i.strip()]
        to_audit = {i: manifest[i] for i in wanted if i in manifest}
        missing = [i for i in wanted if i not in manifest]
        if missing:
            print(f"WARNING: {len(missing)} requested ID(s) not in manifest, skipping: {missing}")
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
        r = audit_listing(api, listing_id, entry, rules, approvals, registry,
                          full_mode=args.full)
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
