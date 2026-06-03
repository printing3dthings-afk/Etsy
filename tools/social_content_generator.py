#!/usr/bin/env python3
"""
social_content_generator.py

Builds a 30-day Reddit + Facebook content calendar from active Etsy listings.
Each product type maps to the subreddits and Facebook groups where its buyers live.

Output:
  data/social/content_calendar.md    — human-readable, copy-paste ready
  data/social/content_queue.json     — machine-readable queue for future automation

Usage:
  python tools/social_content_generator.py           # generate full 30-day calendar
  python tools/social_content_generator.py --today   # show only today's scheduled posts
  python tools/social_content_generator.py --preview # print calendar without saving
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE))

from tools.etsy_api import EtsyAPIClient

OUTPUT_MD   = BASE / "data" / "social" / "content_calendar.md"
OUTPUT_JSON = BASE / "data" / "social" / "content_queue.json"

SHOP_URL = "https://www.etsy.com/shop/OnBrandCraftz"

# ── Product category definitions ─────────────────────────────────────────────

CATEGORIES = {
    "digital_planner": {
        "keywords": ["Digital Planner", "Life Planner", "Student Planner",
                     "Budget Planner", "Fitness Planner", "GoodNotes"],
        "reddit": [
            ("r/digitalplanning",    "preview"),
            ("r/planneraddicts",     "community"),
            ("r/bujo",               "share"),
            ("r/GoodNotes",          "preview"),
        ],
        "facebook": [
            "Digital Planner Addicts",
            "GoodNotes Users & Tips",
            "Notability App Users",
        ],
        "hashtags": ["#digitalplanner #goodnotes #notability #kawaiiplanner "
                     "#ipadplanner #digitaldownload #planneraddict #kawaii"],
    },
    "svg_bundle": {
        "keywords": ["SVG Bundle", "SVG Cut File", "Sublimation", "Cricut"],
        "reddit": [
            ("r/cricut",              "share"),
            ("r/svgfiles",            "preview"),
            ("r/silhouettecameo",     "share"),
        ],
        "facebook": [
            "Cricut Crafters & Makers",
            "SVG Cut Files Free and Paid",
            "Silhouette Cameo Crafters",
        ],
        "hashtags": ["#svgfiles #cricut #silhouette #svgbundle "
                     "#cricutmaker #cutfiles #instantdownload"],
    },
    "sticker_pack": {
        "keywords": ["Kawaii Sticker", "Sticker Pack", "Sticker Book",
                     "GoodNotes Sticker", "Digital Sticker"],
        "reddit": [
            ("r/kawaii",              "share"),
            ("r/stationery",          "preview"),
            ("r/digitalplanning",     "community"),
        ],
        "facebook": [
            "Digital Stickers for Planners",
            "GoodNotes Stickers and Elements",
            "Kawaii Community",
        ],
        "hashtags": ["#kawaiistickers #digitalstickers #goodnotesstickers "
                     "#plannarstickers #kawaii #stickerpack #instantdownload"],
    },
    "wall_art": {
        "keywords": ["Wall Art", "Art Print", "Printable", "Wall Decor",
                     "Gallery Wall", "Nursery"],
        "reddit": [
            ("r/printables",          "share"),
            ("r/femalelivingspace",   "share"),
            ("r/HomeDecorating",      "share"),
        ],
        "facebook": [
            "Printable Art Lovers",
            "Home Decor DIY Ideas",
            "Etsy Finds Home Decor",
        ],
        "hashtags": ["#printableart #wallart #instantdownload #homedecor "
                     "#gallerywall #printablewalldecor #digitaldownload"],
    },
    "commercial_license": {
        "keywords": ["Commercial License"],
        "reddit": [
            ("r/Etsy",                "community"),
            ("r/smallbusiness",       "community"),
        ],
        "facebook": [
            "Etsy Sellers Community",
            "Digital Product Creators",
            "Small Business Owners Network",
        ],
        "hashtags": ["#commerciallicense #svglicense #smallbusiness "
                     "#cricutbusiness #digitalproducts"],
    },
    "coloring_page": {
        "keywords": ["Coloring Page", "Coloring Book", "Adult Coloring"],
        "reddit": [
            ("r/Coloring",            "preview"),
            ("r/coloringpages",       "share"),
        ],
        "facebook": [
            "Adult Coloring Pages",
            "Printable Coloring Pages Community",
        ],
        "hashtags": ["#coloringpage #adultcoloring #printablecoloring "
                     "#coloringbook #instantdownload"],
    },
    "physical_print": {
        "keywords": ["Physical Print", "Kawaii Wall Art", "Printify"],
        "reddit": [
            ("r/femalelivingspace",   "share"),
            ("r/malelivingspace",     "share"),
        ],
        "facebook": [
            "Home Decor DIY Ideas",
            "Etsy Finds Home Decor",
        ],
        "hashtags": ["#wallart #kawaii #homedecor #artprint #kawaiiart"],
    },
}

# ── Post templates ────────────────────────────────────────────────────────────

REDDIT_TEMPLATES = {
    "preview": [
        (
            "Just finished this — would love feedback from the community",
            "I've been working on {title} and finally feel good enough about it to share. "
            "It features {hook}. Happy to answer any questions about the design process!\n\n"
            "[Etsy link in comments — don't want to break sub rules]"
        ),
        (
            "Made a {category_label} — here's a preview",
            "Sharing a preview of {title}. {hook} "
            "Still learning as I go — any feedback is welcome!\n\n"
            "[Link in profile if interested]"
        ),
    ],
    "community": [
        (
            "Does anyone else use {category_label}? Sharing mine",
            "Been using digital tools for a while and finally made my own. "
            "{title} — {hook}\n\n"
            "Drop your setups/shops below, would love to see what others are making."
        ),
        (
            "Small shop owner here — sharing my {category_label}",
            "Trying to grow a small Etsy shop selling {category_label}. "
            "Latest release: {title}. {hook}\n\n"
            "Any tips from others who sell digital products here?"
        ),
    ],
    "share": [
        (
            "{title} — printable instant download",
            "{hook} Available as an instant download. "
            "Sized for home printing and print shops.\n\n"
            "[Etsy: {url}]"
        ),
        (
            "New to the shop: {title}",
            "Just listed this one. {hook}\n\n"
            "Full details and instant download at the link: {url}"
        ),
    ],
}

FACEBOOK_TEMPLATES = [
    (
        "✨ NEW DROP ✨\n\n"
        "{title} is now in the shop!\n\n"
        "{hook}\n\n"
        "Grab yours here → {url}\n\n"
        "{hashtags}"
    ),
    (
        "🎉 Just added to the shop!\n\n"
        "{title}\n\n"
        "{hook}\n\n"
        "Instant download — yours in seconds! 💌\n"
        "Shop: {url}\n\n"
        "{hashtags}"
    ),
    (
        "Did you know we just dropped {title}? 👀\n\n"
        "{hook}\n\n"
        "Perfect gift idea too! 🎁\n"
        "{url}\n\n"
        "{hashtags}"
    ),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def categorize(listing: dict) -> str:
    title = listing.get("title", "")
    desc  = listing.get("description", "")
    text  = (title + " " + desc).lower()
    for cat, cfg in CATEGORIES.items():
        if any(kw.lower() in text for kw in cfg["keywords"]):
            return cat
    return "wall_art"


def make_hook(listing: dict, category: str) -> str:
    title = listing.get("title", "")
    desc  = (listing.get("description") or "")[:200]
    hooks = {
        "digital_planner":   f"A kawaii-illustrated digital planner compatible with GoodNotes, Notability, and iPad.",
        "svg_bundle":        f"A ready-to-cut SVG bundle for Cricut and Silhouette machines.",
        "sticker_pack":      f"200+ kawaii digital stickers, GoodNotes Elements ready.",
        "wall_art":          f"Printable instant download — print at home or at any print shop.",
        "commercial_license": f"Includes a commercial license for use in your own products and resale.",
        "coloring_page":     f"Printable coloring page, instant download.",
        "physical_print":    f"Ships directly to your door — printed and fulfilled by Print Clever.",
    }
    return hooks.get(category, "Instant digital download.")


def etsy_url(listing: dict) -> str:
    return f"https://www.etsy.com/listing/{listing['listing_id']}"


def build_reddit_post(listing: dict, category: str, post_style: str) -> dict:
    cfg       = CATEGORIES[category]
    templates = REDDIT_TEMPLATES.get(post_style, REDDIT_TEMPLATES["share"])
    t_title, t_body = random.choice(templates)
    cat_label = category.replace("_", " ")
    hook      = make_hook(listing, category)
    url       = etsy_url(listing)
    title     = (listing.get("title") or "")[:60]
    subreddits = [r for r, s in cfg["reddit"] if s == post_style] or [cfg["reddit"][0][0]]
    subreddit  = random.choice(subreddits)

    return {
        "platform":   "reddit",
        "subreddit":  subreddit,
        "post_title": t_title.format(title=title, category_label=cat_label, url=url, hook=hook),
        "post_body":  t_body.format(title=title, category_label=cat_label, url=url, hook=hook),
        "listing_id": listing["listing_id"],
        "listing_title": title,
    }


def build_facebook_post(listing: dict, category: str) -> dict:
    cfg      = CATEGORIES[category]
    template = random.choice(FACEBOOK_TEMPLATES)
    hook     = make_hook(listing, category)
    url      = etsy_url(listing)
    title    = (listing.get("title") or "")[:60]
    group    = random.choice(cfg["facebook"])
    hashtags = cfg["hashtags"][0]

    return {
        "platform":    "facebook",
        "group":       group,
        "caption":     template.format(title=title, hook=hook, url=url, hashtags=hashtags),
        "listing_id":  listing["listing_id"],
        "listing_title": title,
    }


def build_calendar(listings: list[dict], days: int = 30) -> list[dict]:
    """Assign one post per day alternating reddit/facebook across the calendar."""
    # Group listings by category, deduplicate
    by_cat: dict[str, list] = {}
    seen_ids = set()
    for l in listings:
        lid = l["listing_id"]
        if lid in seen_ids:
            continue
        seen_ids.add(lid)
        cat = categorize(l)
        by_cat.setdefault(cat, []).append(l)

    # Flatten into posting pool: vary categories across the calendar
    pool = []
    all_cats = list(by_cat.keys())
    random.shuffle(all_cats)
    max_per_cat = max(1, days // max(len(all_cats), 1))
    for cat in all_cats:
        picks = by_cat[cat][:max_per_cat]
        for listing in picks:
            pool.append((listing, cat))
    random.shuffle(pool)
    pool = pool[:days]

    calendar = []
    today = date.today()
    styles = ["preview", "community", "share"]
    for i, (listing, cat) in enumerate(pool):
        post_date = today + timedelta(days=i)
        # Alternate reddit and facebook
        if i % 2 == 0:
            post = build_reddit_post(listing, cat, styles[i % len(styles)])
        else:
            post = build_facebook_post(listing, cat)
        post["date"] = post_date.isoformat()
        calendar.append(post)

    return calendar


def render_markdown(calendar: list[dict]) -> str:
    lines = [
        "# OnBrandCraftz — Social Content Calendar",
        f"Generated: {date.today().isoformat()}",
        f"Shop: {SHOP_URL}",
        "",
        "---",
        "",
        "> **Reddit rules**: Check each subreddit's self-promotion policy before posting.",
        "> Most allow 1 promotional post per 10 community posts. Build karma first.",
        "> Never post the same content to multiple subreddits on the same day.",
        "",
        "---",
        "",
    ]

    current_week = None
    for post in calendar:
        d = date.fromisoformat(post["date"])
        week_num = (d - date.today()).days // 7 + 1
        if week_num != current_week:
            current_week = week_num
            lines.append(f"## Week {week_num}")
            lines.append("")

        day_label = d.strftime("%A, %B %-d")
        lines.append(f"### {day_label}")
        lines.append("")

        if post["platform"] == "reddit":
            lines.append(f"**Platform:** Reddit — {post['subreddit']}")
            lines.append(f"**Listing:** [{post['listing_title']}](https://www.etsy.com/listing/{post['listing_id']})")
            lines.append("")
            lines.append(f"**Post Title:**")
            lines.append(f"> {post['post_title']}")
            lines.append("")
            lines.append(f"**Post Body:**")
            for body_line in post["post_body"].split("\n"):
                lines.append(f"> {body_line}" if body_line else ">")
        else:
            lines.append(f"**Platform:** Facebook — {post['group']}")
            lines.append(f"**Listing:** [{post['listing_title']}](https://www.etsy.com/listing/{post['listing_id']})")
            lines.append("")
            lines.append("**Caption:**")
            lines.append("```")
            lines.append(post["caption"])
            lines.append("```")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Reddit/Facebook content calendar")
    parser.add_argument("--today",   action="store_true", help="Show only today's post")
    parser.add_argument("--preview", action="store_true", help="Print to terminal, don't save")
    parser.add_argument("--days",    type=int, default=30, help="Days to generate (default 30)")
    args = parser.parse_args()

    with open(BASE / ".env") as f:
        import os
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    client = EtsyAPIClient()
    if not client.refresh_access_token():
        print("ERROR: Could not refresh OAuth token")
        sys.exit(1)

    print("Fetching active listings...")
    listings = client.get_shop_listings_all(state="active")
    print(f"Found {len(listings)} listings\n")

    random.seed(42)  # reproducible output
    calendar = build_calendar(listings, days=args.days)

    if args.today:
        today_str = date.today().isoformat()
        today_posts = [p for p in calendar if p["date"] == today_str]
        if not today_posts:
            print("No posts scheduled for today — run without --today to regenerate calendar")
        for p in today_posts:
            print(json.dumps(p, indent=2))
        return

    md = render_markdown(calendar)

    if args.preview:
        print(md)
        return

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(md)
    OUTPUT_JSON.write_text(json.dumps(calendar, indent=2))

    print(f"Calendar saved:")
    print(f"  {OUTPUT_MD}")
    print(f"  {OUTPUT_JSON}")
    print(f"\n{len(calendar)} posts across {args.days} days")

    # Quick breakdown
    reddit_count   = sum(1 for p in calendar if p["platform"] == "reddit")
    facebook_count = sum(1 for p in calendar if p["platform"] == "facebook")
    print(f"  Reddit: {reddit_count}  |  Facebook: {facebook_count}")


if __name__ == "__main__":
    main()
