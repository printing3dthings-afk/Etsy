#!/usr/bin/env python3
"""
review_monitor.py

Polls for new Etsy reviews, surfaces them for Scott, and drafts response templates.

New reviews are compared against data/reviews_seen.json so only genuinely new
reviews are shown. Saves drafted responses to data/message_drafts/ for Scott
to send manually from the Etsy dashboard.

Usage:
  python tools/review_monitor.py             -- show new reviews + draft responses
  python tools/review_monitor.py --all       -- show all reviews (ignore seen state)
  python tools/review_monitor.py --check     -- exit code 0=no new, 1=new reviews exist

Referenced by tools/api_server/main.py's _WEEKLY_MONITOR_SCRIPTS — restored
2026-07-15 after an unrelated declutter pass deleted this file thinking it
was unreferenced. If removing this file again, grep main.py first.
"""

from __future__ import annotations

import os
import sys
import json
import argparse
from datetime import date, datetime
from pathlib import Path

_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
with open(_env_path) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etsy_api import EtsyAPIClient, EtsyAPIError

SEEN_FILE = Path("data/reviews_seen.json")
DRAFTS_DIR = Path("data/message_drafts")
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)


def _load_seen() -> set:
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text()))
        except Exception:
            pass
    return set()


def _save_seen(seen: set) -> None:
    SEEN_FILE.write_text(json.dumps(sorted(seen), indent=2))


def _draft_response(review: dict) -> str:
    rating = review.get("rating", 5)
    text = (review.get("review") or "").strip()

    if rating == 5:
        if text:
            return (
                "Thank you so much for your kind words! 🙏 "
                "I'm so glad the planner is working well for you. "
                "Enjoy your planning! — Scott @ OnBrandCraftz"
            )
        else:
            return (
                "Thank you so much for your purchase and the 5-star review! "
                "It means everything to a small shop. Happy planning! — Scott @ OnBrandCraftz"
            )
    elif rating == 4:
        return (
            "Thank you for your review! I really appreciate the feedback. "
            "If there's anything I can improve, please don't hesitate to reach out — "
            "I'm always looking to make things better. — Scott @ OnBrandCraftz"
        )
    elif rating <= 3:
        # Negative review — flag for Scott to write a personal response
        return (
            "[PERSONAL RESPONSE NEEDED — do not send this template]\n"
            "This is a low-rating review. Please write a personal, empathetic response "
            "addressing the specific concern. Acknowledge the issue, offer to help, "
            "and keep it under 3 sentences. Tone: calm, professional, caring.\n"
            f"Review text: '{text}'"
        )
    return ""


def run(show_all: bool = False, check_only: bool = False) -> int:
    client = EtsyAPIClient()
    if not client.shop_id:
        print("ERROR: ETSY_SHOP_ID not set in .env")
        sys.exit(1)

    try:
        resp = client.get_reviews(limit=50)
    except EtsyAPIError as e:
        print(f"ERROR fetching reviews: {e}")
        sys.exit(1)

    reviews = resp.get("results", [])
    seen = _load_seen() if not show_all else set()

    new_reviews = []
    for r in reviews:
        rid = str(r.get("review_id") or r.get("listing_id", "") + "_" + str(r.get("create_timestamp", "")))
        if rid not in seen:
            new_reviews.append((rid, r))

    if check_only:
        return 1 if new_reviews else 0

    if not new_reviews:
        print("No new reviews since last check.")
        return 0

    print(f"\n{'='*65}")
    print(f"NEW REVIEWS — {date.today()} ({len(new_reviews)} new)")
    print(f"{'='*65}")

    drafts = []
    for rid, r in new_reviews:
        rating = r.get("rating", "?")
        text = (r.get("review") or "").strip() or "[no text]"
        listing_id = r.get("listing_id", "?")
        created = r.get("create_timestamp", "")
        stars = "★" * int(rating) + "☆" * (5 - int(rating)) if isinstance(rating, int) else str(rating)

        print(f"\n{stars} ({rating}/5)  Listing: {listing_id}")
        print(f"  '{text}'")

        draft = _draft_response(r)
        if "PERSONAL RESPONSE NEEDED" in draft:
            print("  ⚠️  LOW RATING — personal response required (see drafts file)")
        else:
            print(f"  Draft reply: {draft}")

        drafts.append({
            "review_id": rid,
            "rating": rating,
            "listing_id": listing_id,
            "review_text": text,
            "created": created,
            "draft_response": draft,
            "needs_personal_response": "PERSONAL RESPONSE NEEDED" in draft,
        })

    # Save drafts
    draft_path = DRAFTS_DIR / f"review_responses_{date.today()}.json"
    draft_path.write_text(json.dumps(drafts, indent=2))
    print(f"\n✓ Draft responses saved: {draft_path}")

    # Mark reviews as seen
    new_ids = {rid for rid, _ in new_reviews}
    _save_seen(seen | new_ids)

    ratings = [r.get("rating", 0) for _, r in new_reviews if isinstance(r.get("rating"), int)]
    if ratings:
        avg = sum(ratings) / len(ratings)
        low = [r for r in ratings if r <= 3]
        print(f"\nSummary: avg rating {avg:.1f} | {len(low)} low-rating review(s) need personal responses")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Check for new Etsy reviews and draft responses")
    parser.add_argument("--all", action="store_true", help="Show all reviews, not just new ones")
    parser.add_argument("--check", action="store_true", help="Exit 1 if new reviews exist, 0 if none")
    args = parser.parse_args()
    result = run(show_all=args.all, check_only=args.check)
    sys.exit(result)


if __name__ == "__main__":
    main()
