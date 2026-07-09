#!/usr/bin/env python3
"""
weekly_market_research.py

Runs every Saturday at 7am. Searches Etsy for the top-performing listings in
every product category OnBrandCraftz sells, then uses Claude to synthesize the
findings into actionable design and keyword intelligence.

Outputs:
  data/knowledge_base/market_research/YYYY-MM-DD_market_research.md  — full report
  data/knowledge_base/market_research/latest_insights.json           — machine-readable (read by other tools)

Usage:
  python tools/weekly_market_research.py
  python tools/weekly_market_research.py --dry-run     (skip Claude synthesis, save raw data only)
  python tools/weekly_market_research.py --category svg
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE))

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

# ── Search queries by category ────────────────────────────────────────────────

SEARCH_PLAN = {
    "wall_art": [
        "printable wall art instant download",
        "boho wall art digital print",
        "botanical wall art printable",
        "inspirational quote print wall art",
        "minimalist wall art instant download",
        "dark academia wall art print",
        "gallery wall set printable",
        "nursery wall art digital download",
        "watercolor wall art print",
        "abstract wall art printable",
    ],
    "svg": [
        "svg cut file bundle cricut",
        "western svg bundle silhouette",
        "floral svg bundle instant download",
        "mama svg bundle cricut",
        "teacher svg bundle",
        "farmhouse svg bundle",
        "motivational svg bundle cricut",
        "boho svg bundle",
        "retro svg bundle silhouette",
        "faith svg bundle cricut",
    ],
    "sublimation": [
        "sublimation tumbler wrap 20oz",
        "sublimation design bundle png",
        "teacher tumbler wrap sublimation",
        "mama tumbler wrap sublimation",
        "nurse tumbler sublimation wrap",
        "western sublimation design png",
        "floral tumbler wrap sublimation",
        "inspirational tumbler sublimation",
    ],
}

# Top N listings to fetch per query
RESULTS_PER_QUERY = 25


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


def search_category(client: EtsyAPIClient, category: str, queries: list[str]) -> dict:
    """Fetch top listings for every query in a category. Returns structured raw data."""
    print(f"\n  Searching '{category}' ({len(queries)} queries)...")
    all_listings: list[dict] = []
    seen_ids: set[int] = set()

    for query in queries:
        try:
            resp = client.search_listings(query, limit=RESULTS_PER_QUERY, sort_on="score")
            listings = resp.get("results", [])
            for listing in listings:
                lid = listing.get("listing_id")
                if lid and lid not in seen_ids:
                    seen_ids.add(lid)
                    all_listings.append({
                        "listing_id": lid,
                        "title": listing.get("title", ""),
                        "price": listing.get("price", {}).get("amount", 0) / max(listing.get("price", {}).get("divisor", 100), 1),
                        "currency": listing.get("price", {}).get("currency_code", "USD"),
                        "num_favorers": listing.get("num_favorers", 0),
                        "tags": listing.get("tags", []),
                        "shop_id": listing.get("shop_id"),
                        "query": query,
                    })
            print(f"    ✓ '{query}' → {len(listings)} results")
            time.sleep(0.3)  # respect rate limits
        except EtsyAPIError as e:
            print(f"    ✗ '{query}' failed: {e}")

    return {"category": category, "listings": all_listings}


def extract_patterns(category_data: dict) -> dict:
    """Derive frequency patterns from raw listing data."""
    listings = category_data["listings"]
    if not listings:
        return {}

    # Title word frequency (cleaned)
    SKIP_WORDS = {
        "and", "the", "a", "an", "for", "with", "to", "of", "in", "on",
        "is", "are", "be", "by", "at", "or", "from", "your", "you",
        "instant", "download", "digital", "printable", "print", "svg",
        "file", "bundle", "design", "cut", "files",
    }
    word_counter: Counter = Counter()
    for lst in listings:
        words = [w.lower().strip(".,|+&-") for w in lst["title"].split()]
        word_counter.update(w for w in words if w and w not in SKIP_WORDS and len(w) > 2)

    # Tag frequency
    tag_counter: Counter = Counter()
    for lst in listings:
        tag_counter.update(t.lower() for t in lst["tags"])

    # Price distribution
    prices = [lst["price"] for lst in listings if lst["price"] > 0]
    price_buckets = {"under_3": 0, "3_to_6": 0, "6_to_10": 0, "10_to_20": 0, "over_20": 0}
    for p in prices:
        if p < 3:
            price_buckets["under_3"] += 1
        elif p < 6:
            price_buckets["3_to_6"] += 1
        elif p < 10:
            price_buckets["6_to_10"] += 1
        elif p < 20:
            price_buckets["10_to_20"] += 1
        else:
            price_buckets["over_20"] += 1

    # Top performers by favorites
    top_by_favorites = sorted(listings, key=lambda x: x["num_favorers"], reverse=True)[:10]

    return {
        "category": category_data["category"],
        "total_listings_sampled": len(listings),
        "top_title_words": word_counter.most_common(30),
        "top_tags": tag_counter.most_common(30),
        "price_distribution": price_buckets,
        "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
        "median_price": round(sorted(prices)[len(prices) // 2], 2) if prices else 0,
        "top_performers": [
            {"title": l["title"], "price": l["price"], "favorites": l["num_favorers"]}
            for l in top_by_favorites
        ],
    }


def synthesize_with_claude(all_patterns: list[dict], today: str) -> str:
    """Call Claude to turn raw patterns into actionable design intelligence."""
    env = _parse_env()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "Claude synthesis skipped — ANTHROPIC_API_KEY not set."

    try:
        import urllib.request
        import urllib.error

        data_summary = json.dumps(all_patterns, indent=2)

        prompt = f"""You are the product strategy advisor for OnBrandCraftz, an Etsy shop selling:
- Digital printable wall art (instant download JPEGs/PNGs in multiple sizes)
- SVG cut file bundles (Cricut/Silhouette compatible)
- Sublimation tumbler wrap PNGs (20oz tumblers primarily)
- Digital kawaii planners (GoodNotes/Notability)

Today is {today}. I've collected market research from Etsy's search results.
Here is the raw pattern data extracted from the top-performing listings:

{data_summary}

Please analyze this and produce a structured market intelligence report with these sections:

## 1. TOP TRENDING THEMES RIGHT NOW
List the top 8-10 design themes that are clearly dominating search results based on title word frequency and tag frequency. For each theme, note which category it appears in (wall art / SVG / sublimation) and an estimated demand level (high/medium/low based on frequency).

## 2. UNDERSERVED NICHES (OPPORTUNITY GAPS)
Identify 3-5 niches where search demand is present (keywords appear) but the top performers have relatively fewer favorites — meaning less competition. These are our best bets for new products.

## 3. PRICE BENCHMARKS
What are the dominant price ranges for each category? Are there any pricing anomalies where high-favorite listings are priced differently than expected?

## 4. TAG STRATEGY INSIGHTS
What are the most common tags across top performers? Identify any tags we should be using that we might be missing.

## 5. RECOMMENDED DESIGNS TO CREATE THIS WEEK
Based on the data, give me a ranked list of the top 5 specific design concepts we should create next. Be specific — not just "floral" but "wildflower meadow botanical watercolor in sage green and cream" or "retro varsity mama bear SVG bundle with distressed font."

## 6. WHAT TO AVOID
Any over-saturated niches where competition is so high that a new listing has almost no chance of ranking?

## 7. SEASONAL ALERT
Based on today's date ({today}), are there any seasonal themes we should be creating NOW to be ready in 6-8 weeks?

Be specific and actionable. This report will be read by automation that creates actual products, so concrete details matter more than general observations."""

        body = json.dumps({
            "model": "claude-sonnet-4-6",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result["content"][0]["text"]

    except Exception as e:
        return f"Claude synthesis failed: {e}"


def save_results(report_md: str, latest_json: dict, today: str) -> tuple[Path, Path]:
    out_dir = BASE / "data" / "knowledge_base" / "market_research"
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / f"{today}_market_research.md"
    md_path.write_text(report_md, encoding="utf-8")

    json_path = out_dir / "latest_insights.json"
    json_path.write_text(json.dumps(latest_json, indent=2), encoding="utf-8")

    return md_path, json_path


def build_markdown(today: str, all_patterns: list[dict], synthesis: str) -> str:
    lines = [
        f"# OnBrandCraftz Weekly Market Research — {today}",
        "",
        "## Summary",
        f"Research date: {today}",
        "",
    ]

    for patterns in all_patterns:
        cat = patterns.get("category", "unknown")
        lines += [
            f"## Raw Patterns — {cat.replace('_', ' ').title()}",
            "",
            f"Listings sampled: **{patterns.get('total_listings_sampled', 0)}**  ",
            f"Average price: **${patterns.get('avg_price', 0):.2f}**  ",
            f"Median price: **${patterns.get('median_price', 0):.2f}**",
            "",
            "### Price Distribution",
        ]
        for bucket, count in (patterns.get("price_distribution") or {}).items():
            lines.append(f"- {bucket.replace('_', ' ')}: {count} listings")

        lines += ["", "### Top Title Keywords"]
        for word, freq in (patterns.get("top_title_words") or [])[:15]:
            lines.append(f"- `{word}` ({freq}×)")

        lines += ["", "### Top Tags"]
        for tag, freq in (patterns.get("top_tags") or [])[:15]:
            lines.append(f"- `{tag}` ({freq}×)")

        lines += ["", "### Top Performers (by favorites)"]
        for p in (patterns.get("top_performers") or [])[:5]:
            lines.append(f"- **{p['favorites']} ❤️** | ${p['price']:.2f} | {p['title'][:80]}")

        lines.append("")

    lines += [
        "---",
        "",
        "## Claude Market Intelligence Analysis",
        "",
        synthesis,
    ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly Etsy market research")
    parser.add_argument("--dry-run", action="store_true", help="Skip Claude synthesis")
    parser.add_argument("--category", choices=list(SEARCH_PLAN.keys()), help="Run one category only")
    args = parser.parse_args()

    today = date.today().isoformat()
    print(f"OnBrandCraftz Weekly Market Research — {today}")
    print("=" * 55)

    env = _parse_env()
    client_id = env.get("ETSY_CLIENT_ID", "")
    if not client_id:
        print("ERROR: ETSY_CLIENT_ID not set in .env")
        sys.exit(1)

    client = EtsyAPIClient()

    categories = {args.category: SEARCH_PLAN[args.category]} if args.category else SEARCH_PLAN

    all_patterns: list[dict] = []
    all_raw: list[dict] = []

    for category, queries in categories.items():
        raw = search_category(client, category, queries)
        all_raw.append(raw)
        patterns = extract_patterns(raw)
        if patterns:
            all_patterns.append(patterns)
            print(f"  → {patterns['total_listings_sampled']} unique listings, avg ${patterns['avg_price']:.2f}")

    if not all_patterns:
        print("\nNo data collected. Check Etsy API connection.")
        sys.exit(1)

    synthesis = ""
    if not args.dry_run:
        print("\nSynthesizing with Claude...")
        synthesis = synthesize_with_claude(all_patterns, today)
        print("  ✓ Synthesis complete")
    else:
        synthesis = "_Dry run — Claude synthesis skipped._"

    report_md = build_markdown(today, all_patterns, synthesis)

    # Build machine-readable JSON for other tools to consume
    latest_json = {
        "research_date": today,
        "categories": {p["category"]: p for p in all_patterns},
        "synthesis_available": not args.dry_run,
    }

    md_path, json_path = save_results(report_md, latest_json, today)

    print(f"\nSaved:")
    print(f"  Report : {md_path.relative_to(BASE)}")
    print(f"  JSON   : {json_path.relative_to(BASE)}")
    print("\nDone.")


if __name__ == "__main__":
    main()
