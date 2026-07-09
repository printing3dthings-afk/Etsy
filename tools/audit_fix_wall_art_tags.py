"""
audit_fix_wall_art_tags.py
Audit and fix tags for all wall art listings in the OnBrandCraftz Etsy shop.

Steps:
1. Fetch all active listings, filter to wall art only
2. Analyze tags for duplicates, single-word tags, invalid length, empty slots
3. Generate improved tags via Claude API for listings with issues
4. Stage tag updates in the Action Center for one-tap approval (NOT a direct
   Etsy write — this used to call client.update_listing() straight away,
   bypassing the same approval queue every other Etsy write in this system
   goes through; fixed 2026-07-09 as part of wiring this script into the
   automated weekly loop, since an unattended job must never write to a live
   listing without a human tap)
5. Print full report
"""

from __future__ import annotations

import os
import sys
import json
import time
import re
import urllib.request
import urllib.error
import urllib.parse

# ── Load .env ────────────────────────────────────────────────────────────────
env: dict[str, str] = {}
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
with open(_env_path) as _f:
    for _line in _f:
        _line = _line.strip()
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            env[_k.strip()] = _v.strip()
os.environ.update(env)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tools.etsy_api import EtsyAPIClient
from tools.api_server import db as _db

# ── Constants ─────────────────────────────────────────────────────────────────

# Keywords that identify NON-wall-art listings to exclude
EXCLUDE_TITLE_PATTERNS = [
    r"\bplanner\b",
    r"\bsticker\b",
    r"\b3d print",
    r"\bkoozie\b",
    r"\bvase\b",
    r"\blamp\b",
    r"\bcandle holder\b",
    r"\bcenterpiece\b",
    r"\bdesk pen holder\b",
    r"\bplant pot\b",
    r"\bfunny dog\b.*?\binstant download\b",  # just in case
    r"\bfree kawaii\b",
]

ANTHROPIC_API_KEY = env.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# ── Helpers ───────────────────────────────────────────────────────────────────

def is_wall_art(title: str) -> bool:
    """Return True if the listing looks like a wall art listing (not a planner/3D/sticker)."""
    t = title.lower()
    for pat in EXCLUDE_TITLE_PATTERNS:
        if re.search(pat, t):
            return False
    return True


def normalize_phrase(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tag_is_duplicate_of_title(tag: str, title_normalized: str) -> bool:
    """True if the tag phrase appears as a substring of the normalized title."""
    tag_norm = normalize_phrase(tag)
    return tag_norm in title_normalized


def analyze_tags(listing: dict) -> dict:
    """
    Return an analysis dict with keys:
      has_issues: bool
      issues: list[str]
      duplicate_tags: list[str]
      single_word_tags: list[str]
      invalid_length_tags: list[str]
      empty_slots: int
    """
    title = listing.get("title", "")
    tags: list[str] = listing.get("tags", [])
    title_norm = normalize_phrase(title)

    issues = []
    duplicate_tags = []
    single_word_tags = []
    invalid_length_tags = []

    for tag in tags:
        # Over 20 chars
        if len(tag) > 20:
            issues.append(f"Tag too long ({len(tag)} chars): '{tag}'")
            invalid_length_tags.append(tag)

        # Single word (< 2 words)
        words = tag.strip().split()
        if len(words) < 2:
            issues.append(f"Single-word tag: '{tag}'")
            single_word_tags.append(tag)

        # Exact duplicate of title phrase
        if tag_is_duplicate_of_title(tag, title_norm):
            issues.append(f"Tag duplicates title phrase: '{tag}'")
            duplicate_tags.append(tag)

    # Empty slots
    empty_slots = 13 - len(tags)
    if empty_slots > 0:
        issues.append(f"Only {len(tags)}/13 tags — {empty_slots} empty slots")

    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "duplicate_tags": duplicate_tags,
        "single_word_tags": single_word_tags,
        "invalid_length_tags": invalid_length_tags,
        "empty_slots": empty_slots,
    }


def call_claude_for_tags(title: str, current_tags: list[str]) -> list[str] | None:
    """
    Call the Claude API (claude-haiku-4-5-20251001) to generate 13 improved tags.
    Returns a list of 13 tags or None on failure.
    """
    prompt = f"""You are an Etsy SEO expert optimizing tags for digital printable wall art listings in 2026.

Listing title: {title}
Current tags: {json.dumps(current_tags)}
Art description (infer from title): {title}

Generate exactly 13 tags for this Etsy listing. Rules:
- Each tag must be 2-3 words, maximum 20 characters including spaces
- Tags must NOT repeat any phrase already in the title word-for-word
- Cover these intent categories: style/aesthetic, room type, occasion/use case, recipient, art medium/technique, color if relevant, size if relevant, digital/printable format
- Use buyer-intent phrases (what buyers type when searching)
- No special characters
- Return ONLY a JSON array of 13 strings, nothing else. Example: ["bedroom wall art", "boho home decor", ...]"""

    payload = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 300,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"    [Claude API error {e.code}]: {body[:200]}")
        return None
    except Exception as e:
        print(f"    [Claude API error]: {e}")
        return None

    # Extract text content from the response
    content = data.get("content", [])
    if not content:
        return None
    text = content[0].get("text", "").strip()

    # Parse JSON array from response
    # Find the first '[' and last ']'
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        print(f"    [Claude parse error]: could not find JSON array in: {text[:100]}")
        return None

    try:
        tags = json.loads(text[start : end + 1])
    except json.JSONDecodeError as e:
        print(f"    [Claude JSON parse error]: {e} in: {text[start:end+1][:100]}")
        return None

    if not isinstance(tags, list):
        return None

    # Validate and clean tags
    cleaned = []
    for tag in tags:
        tag = str(tag).strip()
        # Remove special chars
        tag = re.sub(r"[^a-zA-Z0-9 ]", "", tag).strip()
        # Truncate to 20 chars if somehow over
        if len(tag) > 20:
            tag = tag[:20].rsplit(" ", 1)[0].strip()
        if tag:
            cleaned.append(tag)

    # Pad to 13 if needed, cap at 13
    cleaned = cleaned[:13]
    if len(cleaned) < 13:
        print(f"    [Warning]: Claude returned only {len(cleaned)} valid tags")

    return cleaned if len(cleaned) >= 10 else None  # require at least 10


def fetch_all_wall_art_listings(client: EtsyAPIClient) -> list[dict]:
    """Fetch all active listings and filter to wall art only."""
    result = client.get_shop_listings(limit=100)
    all_listings = result.get("results", [])
    wall_art = [l for l in all_listings if is_wall_art(l.get("title", ""))]
    return wall_art


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("OnBrandCraftz — Wall Art Tag Audit & Fix")
    print("=" * 70)
    print()

    client = EtsyAPIClient()

    # ── Step 1: Fetch listings ────────────────────────────────────────────────
    print("Step 1: Fetching all active listings...")
    wall_art_listings = fetch_all_wall_art_listings(client)
    print(f"  Found {len(wall_art_listings)} wall art listings (non-planner/3D/sticker)")
    print()

    # ── Step 2: Analyze tags ──────────────────────────────────────────────────
    print("Step 2: Analyzing tags for issues...")
    analyses: list[dict] = []
    listings_with_issues: list[dict] = []

    for listing in wall_art_listings:
        analysis = analyze_tags(listing)
        analyses.append({
            "listing": listing,
            "analysis": analysis,
        })
        if analysis["has_issues"]:
            listings_with_issues.append({
                "listing": listing,
                "analysis": analysis,
            })

    total = len(wall_art_listings)
    with_issues = len(listings_with_issues)
    print(f"  Total audited: {total}")
    print(f"  With tag issues: {with_issues}")
    print(f"  Already optimized: {total - with_issues}")
    print()

    if not listings_with_issues:
        print("No tag issues found! All listings are optimized.")
        return

    # ── Step 3: Generate improved tags via Claude ─────────────────────────────
    print("Step 3: Generating improved tags via Claude API...")
    print(f"  Calling Claude for {with_issues} listing(s)...")
    print()

    update_plan: list[dict] = []  # {listing, old_tags, new_tags}
    example_updates: list[dict] = []  # for the final report (first 5)

    for i, item in enumerate(listings_with_issues):
        listing = item["listing"]
        analysis = item["analysis"]
        lid = listing["listing_id"]
        title = listing["title"]
        current_tags = listing.get("tags", [])

        print(f"  [{i+1}/{with_issues}] {title[:60]}")
        print(f"    Issues: {len(analysis['issues'])}")

        new_tags = call_claude_for_tags(title, current_tags)

        if new_tags is None:
            print(f"    [SKIP] Claude failed to generate tags — keeping current tags")
            time.sleep(0.5)
            continue

        print(f"    Old tags: {current_tags}")
        print(f"    New tags: {new_tags}")

        update_plan.append({
            "listing_id": lid,
            "title": title,
            "old_tags": current_tags,
            "new_tags": new_tags,
        })

        if len(example_updates) < 5:
            example_updates.append({
                "listing_id": lid,
                "title": title,
                "old_tags": current_tags,
                "new_tags": new_tags,
                "issues": analysis["issues"],
            })

        # Rate limit: 0.5s between calls
        time.sleep(0.5)

    print()
    print(f"  Generated new tags for {len(update_plan)} listing(s)")
    print()

    # ── Step 4: Stage updates for Scott's one-tap approval ───────────────────
    # NOT a direct Etsy write — every proposed tag change lands in the same
    # Action Center queue as any other Etsy change in this system. Nothing
    # here touches a live listing; approving or rejecting each one happens
    # in the dashboard, same as a chat-generated "Stage All Tag Fixes" run.
    print("Step 4: Staging tag updates for approval...")
    staged_count = 0
    fail_count = 0
    failed_ids: list[int] = []
    listing_lookup = {l["listing_id"]: l for l in wall_art_listings}

    for j, plan in enumerate(update_plan):
        lid = plan["listing_id"]
        title = plan["title"]
        new_tags = plan["new_tags"]
        listing = listing_lookup.get(lid, {})

        print(f"  [{j+1}/{len(update_plan)}] Staging listing {lid}: {title[:50]}...")
        try:
            payload = {"listing_id": lid, "tags": new_tags, "_state_at_staging": listing.get("state")}
            summary = f"Tag fix ({len(new_tags)}/13): {title[:50]}"
            _db.enqueue_action("update_tags", summary, payload)
            print(f"    ✓ Staged for approval")
            staged_count += 1
        except Exception as e:
            print(f"    ✗ Failed to stage: {e}")
            fail_count += 1
            failed_ids.append(lid)

        # Small pacing gap, consistent with the rest of this script's rate limiting
        time.sleep(0.1)

    print()

    # ── Step 5: Final Report ──────────────────────────────────────────────────
    print("=" * 70)
    print("REPORT: Wall Art Tag Audit & Fix")
    print("=" * 70)
    print()
    print(f"Total wall art listings audited : {total}")
    print(f"Listings with tag issues        : {with_issues}")
    print(f"Listings already optimized      : {total - with_issues}")
    print(f"Listings staged for approval    : {staged_count}")
    print(f"Staging failed                  : {fail_count}")
    if failed_ids:
        print(f"Failed listing IDs              : {failed_ids}")
    if staged_count:
        print(f"\n{staged_count} tag fix(es) are waiting in the Action Center for your one-tap approval.")
    print()

    # Breakdown of issue types
    dup_count = sum(1 for a in analyses if a["analysis"]["duplicate_tags"])
    single_word_count = sum(1 for a in analyses if a["analysis"]["single_word_tags"])
    invalid_len_count = sum(1 for a in analyses if a["analysis"]["invalid_length_tags"])
    empty_slot_count = sum(1 for a in analyses if a["analysis"]["empty_slots"] > 0)

    print("Issue type breakdown:")
    print(f"  Listings with duplicate title phrases in tags : {dup_count}")
    print(f"  Listings with single-word tags               : {single_word_count}")
    print(f"  Listings with over-20-char tags              : {invalid_len_count}")
    print(f"  Listings with empty tag slots (<13 tags)     : {empty_slot_count}")
    print()

    # Example before/after
    if example_updates:
        print(f"Example updates (up to 5):")
        print("-" * 70)
        for ex in example_updates:
            print(f"\nListing {ex['listing_id']}: {ex['title'][:65]}")
            print(f"  Issues detected:")
            for iss in ex["issues"]:
                print(f"    - {iss}")
            print(f"  OLD tags ({len(ex['old_tags'])}): {ex['old_tags']}")
            print(f"  NEW tags ({len(ex['new_tags'])}): {ex['new_tags']}")

    print()
    print("=" * 70)
    print("Done.")
    print("=" * 70)


if __name__ == "__main__":
    main()
