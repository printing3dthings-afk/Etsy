"""
Web Research Tools — live market intelligence for data-driven agent decisions.
Fetches Etsy search results, design trends, keyword data, and competitor insights.
Every agent inherits these via BaseAgent and should use them before making decisions.
"""
from __future__ import annotations

import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT = 14

TOOL_NAMES = {
    "research_etsy_market",
    "fetch_url",
    "research_product_names",
    "research_design_trends",
    "find_best_keywords",
}

TOOL_DEFINITIONS = [
    {
        "name": "research_etsy_market",
        "description": (
            "Search live Etsy market data for a product type. Returns competitor titles, "
            "price ranges, and title pattern analysis. Use before pricing or naming any product."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query e.g. 'digital planner 2026' or '3d printed planter'",
                },
                "sort": {
                    "type": "string",
                    "enum": ["relevance", "price_asc", "price_desc", "most_recent"],
                    "default": "relevance",
                },
                "limit": {
                    "type": "integer",
                    "default": 15,
                    "description": "Results to return (max 30)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_url",
        "description": (
            "Fetch and extract readable text from any public URL. Use to research trend "
            "articles, blog posts, design inspiration, or competitor shop pages."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to fetch"},
                "max_chars": {
                    "type": "integer",
                    "default": 3000,
                    "description": "Max characters of text to return",
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "research_product_names",
        "description": (
            "Research winning product title patterns for a niche by analysing top Etsy sellers. "
            "Returns title formulas, power words, and keyword placement strategies."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_type": {
                    "type": "string",
                    "description": "e.g. 'digital art print', '3D printed planter', 'weekly planner PDF'",
                },
                "style": {
                    "type": "string",
                    "description": "Style modifier e.g. 'boho', 'minimalist', 'farmhouse'",
                },
            },
            "required": ["product_type"],
        },
    },
    {
        "name": "research_design_trends",
        "description": (
            "Research current design trends, color palettes, and aesthetic movements for a "
            "product category. Use before creating any new product to ensure market alignment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Product category e.g. 'home decor', 'wall art', 'planners'",
                },
                "season": {
                    "type": "string",
                    "description": "Target season e.g. 'summer 2026', 'fall 2026'",
                },
            },
            "required": ["category"],
        },
    },
    {
        "name": "find_best_keywords",
        "description": (
            "Research high-performing Etsy keywords for a niche. Returns tiered keywords "
            "(high-volume, medium intent, long-tail) and tag recommendations ready to paste."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "niche": {
                    "type": "string",
                    "description": "Niche to research e.g. 'boho wall art digital download'",
                },
                "include_long_tail": {
                    "type": "boolean",
                    "default": True,
                },
            },
            "required": ["niche"],
        },
    },
]


# ── HTTP helper ────────────────────────────────────────────────────────────────

def _get(url: str, params: dict = None) -> requests.Response | None:
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r
    except Exception:
        return None


# ── Tool dispatcher ────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "research_etsy_market":
        return _research_etsy_market(tool_input)
    if tool_name == "fetch_url":
        return _fetch_url(tool_input)
    if tool_name == "research_product_names":
        return _research_product_names(tool_input)
    if tool_name == "research_design_trends":
        return _research_design_trends(tool_input)
    if tool_name == "find_best_keywords":
        return _find_best_keywords(tool_input)
    return f"Unknown research tool: {tool_name}"


# ── research_etsy_market ───────────────────────────────────────────────────────

def _research_etsy_market(inp: dict) -> str:
    query = inp.get("query", "")
    sort = inp.get("sort", "relevance")
    limit = min(int(inp.get("limit", 15)), 30)

    sort_map = {
        "relevance": "score",
        "price_asc": "price_asc",
        "price_desc": "price_desc",
        "most_recent": "created",
    }
    resp = _get("https://www.etsy.com/search", params={"q": query, "order": sort_map.get(sort, "score")})

    if not resp:
        return json.dumps({
            "status": "offline",
            "query": query,
            "note": "Etsy not reachable — returning knowledge-based analysis.",
            "market_insights": _offline_insights(query),
        }, indent=2)

    soup = BeautifulSoup(resp.text, "lxml")
    cards = soup.find_all(attrs={"data-listing-id": True})

    listings = []
    for card in cards[:limit]:
        title_el = card.select_one("h3, [class*='title']")
        price_el = card.select_one("[class*='price'], .currency-value, [class*='Price']")
        reviews_el = card.select_one("[class*='review'], [class*='star-rating']")
        title = title_el.get_text(strip=True) if title_el else ""
        price = price_el.get_text(strip=True) if price_el else ""
        reviews = reviews_el.get_text(strip=True) if reviews_el else ""
        if title:
            listings.append({"title": title, "price": price, "reviews": reviews})

    if not listings:
        return json.dumps({
            "status": "anti_scrape",
            "query": query,
            "note": "Etsy returned page but listing data was blocked.",
            "market_insights": _offline_insights(query),
        }, indent=2)

    prices = []
    for l in listings:
        nums = re.findall(r"[\d.]+", l.get("price", "").replace(",", ""))
        if nums:
            try:
                prices.append(float(nums[0]))
            except ValueError:
                pass

    return json.dumps({
        "status": "live",
        "query": query,
        "total_found": len(listings),
        "listings": listings,
        "price_analysis": {
            "min": f"${min(prices):.2f}" if prices else "N/A",
            "max": f"${max(prices):.2f}" if prices else "N/A",
            "avg": f"${sum(prices)/len(prices):.2f}" if prices else "N/A",
            "sweet_spot": f"${sum(prices)/len(prices)*0.9:.2f}–${sum(prices)/len(prices)*1.1:.2f}" if prices else "N/A",
        },
        "title_patterns": _extract_title_patterns([l["title"] for l in listings]),
        "timestamp": datetime.now().isoformat(),
    }, indent=2)


def _offline_insights(query: str) -> dict:
    q = query.lower()
    if any(w in q for w in ["digital", "printable", "pdf", "planner", "art print", "wall art", "svg"]):
        return {
            "category": "digital_products",
            "price_range": "$2.99–$14.99",
            "sweet_spot": "$4.99–$9.99",
            "margin_after_fees": "~75%",
            "title_pattern": "[Style] [Product] | [Format] | Instant Download | [Use Case]",
            "top_tags": [
                "instant download", "printable pdf", "digital download", "wall art printable",
                "home decor digital", "boho art print", "minimalist print", "gallery wall art",
                "digital planner", "printable planner", "weekly planner pdf", "daily planner",
                "aesthetic printable",
            ],
            "power_words": ["Instant Download", "Printable", "Digital", "Bundle", "Set"],
        }
    elif any(w in q for w in ["3d", "printed", "planter", "vase", "figurine", "sculpture"]):
        return {
            "category": "3d_printed",
            "price_range": "$8.99–$34.99",
            "sweet_spot": "$12.99–$24.99",
            "margin_after_fees": "~40%",
            "title_pattern": "[Material/Style] [Product] | [Use] | Handmade | [Gift Angle]",
            "top_tags": [
                "3d printed decor", "unique planter", "modern home decor", "desk accessory",
                "unique gift", "geometric planter", "succulent planter", "minimalist decor",
                "office decor", "3d print art", "modern sculpture", "gift for her", "handmade decor",
            ],
            "power_words": ["3D Printed", "Handmade", "Unique", "Modern", "Geometric"],
        }
    return {
        "category": "general",
        "price_range": "$5.99–$29.99",
        "sweet_spot": "$9.99–$19.99",
        "title_pattern": "[Adjective] [Product] | [Use Case] | [Style] | Gift",
        "top_tags": [
            "handmade gift", "unique home decor", "modern art", "boho decor",
            "minimalist style", "gift for her", "gift for him", "home office decor",
        ],
    }


def _extract_title_patterns(titles: list) -> dict:
    if not titles:
        return {}
    power_words = [
        "instant download", "printable", "digital", "handmade", "custom", "personalized",
        "unique", "boho", "minimalist", "modern", "vintage", "rustic", "farmhouse",
        "aesthetic", "trendy", "gift", "bundle", "set of", "pdf",
    ]
    found = set()
    for t in titles:
        tl = t.lower()
        for pw in power_words:
            if pw in tl:
                found.add(pw)
    separators = [sep for sep in ["|", "-", ","] if sum(1 for t in titles if sep in t) > 2]
    first_words: dict = {}
    for t in titles:
        w = t.split()[0].lower() if t.split() else ""
        first_words[w] = first_words.get(w, 0) + 1
    top_openers = dict(sorted(first_words.items(), key=lambda x: x[1], reverse=True)[:6])
    return {
        "avg_length": int(sum(len(t) for t in titles) / len(titles)),
        "common_separators": separators,
        "power_words_seen": sorted(found),
        "top_opening_words": top_openers,
    }


# ── fetch_url ──────────────────────────────────────────────────────────────────

def _fetch_url(inp: dict) -> str:
    url = inp.get("url", "")
    max_chars = int(inp.get("max_chars", 3000))
    if not url.startswith("http"):
        return "Error: URL must start with http:// or https://"
    resp = _get(url)
    if not resp:
        return f"Could not fetch: {url}"
    soup = BeautifulSoup(resp.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()
    lines = [ln.strip() for ln in soup.get_text(separator="\n").splitlines() if ln.strip()]
    text = "\n".join(lines)
    return text[:max_chars] + ("…" if len(text) > max_chars else "")


# ── research_product_names ─────────────────────────────────────────────────────

def _research_product_names(inp: dict) -> str:
    product_type = inp.get("product_type", "")
    style = inp.get("style", "")
    query = f"{style} {product_type}".strip()
    market_raw = _research_etsy_market({"query": query, "limit": 20})
    try:
        market = json.loads(market_raw)
    except (json.JSONDecodeError, TypeError):
        market = {}

    result = {
        "product_type": product_type,
        "style": style,
        "title_formulas": [
            f"[Style Adj] {product_type} | [Specific Use] | Instant Download | [Buyer Intent]",
            f"{product_type} | [Style] [Adj] | Gift for [Person] | Digital Download",
            f"[Trend Word] {product_type} | [Format] | [Size] | [Style] | Printable",
        ],
        "title_rules": [
            "First 5 words must make product obvious to someone who reads nothing else",
            "Lead with the word buyers search — not the shop name",
            "Include format early: 'Printable PDF', 'Digital Download', 'SVG'",
            "Use | as separator — buyers scan left to right",
            "Put 'Instant Download' in title for digital products (trust signal)",
            "NO ALL CAPS except abbreviations (PDF, SVG, DXF, A4)",
        ],
        "high_converting_openers": [
            "Printable", "Digital", "Boho", "Minimalist", "Modern", "Aesthetic",
            "Handmade", "Unique", "Personalized", "Premium",
        ],
        "power_words": [
            "Instant Download", "Printable", "Digital Download", "Bundle",
            "Set", "Gift", "Custom", "Modern", "Boho", "Handmade",
        ],
        "title_structure": {
            "chars_1_40": "Primary keyword — highest search volume phrase",
            "chars_41_80": "Secondary keyword + style/format",
            "chars_81_140": "Use case + size + delivery method or gift angle",
        },
        "market_data": market,
    }
    if "title_patterns" in market:
        result["live_competitor_patterns"] = market["title_patterns"]
    return json.dumps(result, indent=2)


# ── research_design_trends ─────────────────────────────────────────────────────

TREND_DB: dict = {
    "home decor": {
        "dominant_styles": [
            "Japandi (Japanese + Scandinavian fusion) — warm minimalism",
            "Quiet luxury — understated, premium, no logos",
            "Biophilic design — nature-inspired, plants, organic shapes",
            "Coastal grandmother — linen, rattan, soft blues and whites",
            "Dark academia — rich wood tones, deep greens, vintage feel",
        ],
        "color_palettes": [
            {"name": "Warm Neutrals", "hex": ["#F5F0E8", "#E8DCC8", "#C4A882", "#8B7355"], "trend": "peak"},
            {"name": "Sage + Cream", "hex": ["#9CAF88", "#F2EDE4", "#7A9B6C", "#D4C5A9"], "trend": "rising"},
            {"name": "Terracotta", "hex": ["#C17A4A", "#E8C4A0", "#A65C3C", "#F0DEC0"], "trend": "established"},
            {"name": "Dusty Rose", "hex": ["#D4A0A0", "#C08080", "#E8C0C0", "#F5E8E8"], "trend": "established"},
            {"name": "Forest Green", "hex": ["#2D5016", "#4A7C2F", "#7BAE5C", "#C8D8B8"], "trend": "rising"},
        ],
        "product_trends": [
            "Mushroom + cottagecore motifs",
            "Wavy/organic blob shapes",
            "Abstract faces and figures",
            "Botanical and floral line art",
            "Sun, moon, celestial themes",
            "Maximalist gallery walls",
            "Vintage-modern hybrid decor",
        ],
        "avoid": ["Chevron patterns", "Mason jar everything", "Word art ('Live Laugh Love')"],
    },
    "wall art": {
        "dominant_styles": [
            "Minimalist line art — single continuous line drawings",
            "Abstract expressionism — bold brush strokes, color blocks",
            "Vintage botanical — detailed plant illustrations",
            "Japandi landscape — muted, serene nature scenes",
            "Maximalist gallery walls — mix of frames and styles",
        ],
        "color_palettes": [
            {"name": "Moody Neutrals", "hex": ["#3D3028", "#8B7355", "#C4A882", "#F5F0E8"], "trend": "peak"},
            {"name": "Sage Green", "hex": ["#9CAF88", "#7A9B6C", "#5B7A4E", "#C8D8C0"], "trend": "rising"},
            {"name": "Warm Beige", "hex": ["#F0E8D8", "#D4C4A8", "#B8A888", "#9C8C70"], "trend": "established"},
        ],
        "formats_in_demand": ["8x10", "5x7", "11x14", "16x20", "A4", "A3", "4x6 set"],
        "product_trends": [
            "Printable gallery wall sets (3-piece, 4-piece)",
            "Digital art with physical matting guides",
            "Seasonal swap art (same frame, different print)",
            "Affirmation + quote art (clean typography)",
            "Abstract face + figure art",
        ],
    },
    "planners": {
        "dominant_styles": [
            "Minimalist clean — white space, thin lines, no illustrations",
            "Aesthetic pastel — soft colors, decorative headers",
            "Functional system — GTD-style, structured blocks",
            "Bullet journal inspired — dotted grid, flexible layout",
        ],
        "color_palettes": [
            {"name": "Neutral Greige", "hex": ["#F0EDE8", "#D8D0C8", "#B8B0A8"], "trend": "peak"},
            {"name": "Pastel Sage", "hex": ["#D8E8D0", "#B8CCB0", "#98B090"], "trend": "rising"},
            {"name": "Black + Gold", "hex": ["#1A1A1A", "#C4A84A", "#F5F0E8"], "trend": "established"},
        ],
        "features_in_demand": [
            "Daily + weekly + monthly views all in one bundle",
            "Goal setting + habit tracker pages",
            "Financial budget + savings tracker",
            "Undated (reusable year after year)",
            "iPad/GoodNotes compatible (hyperlinked tabs)",
            "A4 + US Letter sizes included",
        ],
        "pricing_tiers": [
            "Single page template: $2–4",
            "Weekly planner bundle (12 pages): $5–9",
            "Annual planner complete system (50+ pages): $12–18",
        ],
    },
}


def _research_design_trends(inp: dict) -> str:
    category = inp.get("category", "home decor").lower()
    season = inp.get("season", "2026")

    matched = {}
    for key, data in TREND_DB.items():
        if any(w in category for w in key.split()):
            matched = data
            break
    if not matched:
        matched = TREND_DB["home decor"]

    result = {
        "category": category,
        "season": season,
        "timestamp": datetime.now().isoformat(),
        "trends": matched,
        "action_plan": [
            f"Pick ONE dominant style from the list — don't mix styles in a single product",
            f"Use the top-trending color palette for {season}; buyers search by aesthetic",
            "Verify your product could appear on a '{style}' Pinterest board — if yes, it will sell",
            f"Include the style name as an Etsy tag: 'japandi', 'boho', 'minimalist', etc.",
            "If trend is 'rising': move fast, competition is still low",
            "If trend is 'peak': need stronger SEO + thumbnail quality to compete",
        ],
    }
    return json.dumps(result, indent=2)


# ── find_best_keywords ─────────────────────────────────────────────────────────

KEYWORD_DB: dict = {
    "digital": {
        "primary": "digital download",
        "secondary": "instant download wall art",
        "tertiary": "home decor printable gift for her",
        "high_volume": [
            "digital download", "instant download", "printable wall art",
            "digital art print", "wall art printable", "home decor digital",
        ],
        "medium_intent": [
            "boho wall art printable", "minimalist art print digital",
            "aesthetic room decor print", "gallery wall art set digital",
            "modern home decor print", "botanical art printable",
        ],
        "long_tail": [
            "sage green botanical wall art printable instant download",
            "minimalist line art print digital download 8x10",
            "boho aesthetic art print gallery wall set printable",
            "terracotta abstract digital print home decor instant",
            "japandi wall art printable neutral tones digital",
        ],
        "tags": [
            "instant download", "printable wall art", "digital download",
            "home decor print", "boho art print", "minimalist print",
            "gallery wall art", "botanical print", "digital art print",
            "wall art printable", "abstract art print", "gift for her",
            "modern home decor",
        ],
    },
    "planner": {
        "primary": "printable planner",
        "secondary": "digital planner 2026",
        "tertiary": "weekly planner pdf undated",
        "high_volume": [
            "digital planner", "printable planner", "planner pdf",
            "weekly planner printable", "daily planner digital", "2026 planner",
        ],
        "medium_intent": [
            "minimalist planner pdf", "undated weekly planner printable",
            "aesthetic planner digital", "goal planner printable",
            "habit tracker pdf", "budget planner printable",
        ],
        "long_tail": [
            "minimalist undated weekly planner printable pdf instant download",
            "aesthetic daily planner 2026 digital download goodnotes",
            "boho habit tracker printable pdf weekly planner bundle",
            "minimalist goal planner annual printable letter size",
        ],
        "tags": [
            "digital planner", "printable planner", "weekly planner",
            "daily planner", "undated planner", "planner pdf",
            "habit tracker", "goal planner", "budget planner",
            "planner printable", "2026 planner", "goodnotes planner",
            "instant download",
        ],
    },
    "3d": {
        "primary": "3d printed decor",
        "secondary": "unique home decor handmade",
        "tertiary": "modern desk accessory gift",
        "high_volume": [
            "3d printed decor", "unique home decor", "modern planter",
            "desk accessory", "3d print gift", "geometric decor",
        ],
        "medium_intent": [
            "geometric planter 3d printed", "succulent planter modern",
            "3d printed home decor unique", "abstract sculpture desk",
            "minimalist planter small", "3d printed gift unique",
        ],
        "long_tail": [
            "3d printed geometric succulent planter minimalist modern decor",
            "unique 3d print home decor desk accessory handmade gift",
            "modern abstract planter small indoor 3d printed minimalist",
        ],
        "tags": [
            "3d printed decor", "unique planter", "modern home decor",
            "desk accessory", "unique gift", "geometric planter",
            "succulent planter", "minimalist decor", "office decor",
            "3d print art", "modern sculpture", "gift for her",
            "handmade decor",
        ],
    },
}


def _find_best_keywords(inp: dict) -> str:
    niche = inp.get("niche", "")
    include_long_tail = inp.get("include_long_tail", True)
    n = niche.lower()

    kb = {}
    for key, data in KEYWORD_DB.items():
        if key in n:
            kb = data
            break
    if not kb:
        kb = KEYWORD_DB["digital"] if "art" in n or "print" in n else KEYWORD_DB["3d"]

    market_raw = _research_etsy_market({"query": niche, "limit": 20})
    try:
        market = json.loads(market_raw)
    except (json.JSONDecodeError, TypeError):
        market = {}

    result = {
        "niche": niche,
        "keyword_tiers": {
            "tier_1_high_volume": kb.get("high_volume", []),
            "tier_2_medium_high_intent": kb.get("medium_intent", []),
            "tier_3_long_tail": kb.get("long_tail", []) if include_long_tail else [],
        },
        "title_placement": {
            "chars_1_40": kb.get("primary", ""),
            "chars_41_80": kb.get("secondary", ""),
            "chars_81_140": kb.get("tertiary", ""),
        },
        "etsy_tags_ready_to_paste": kb.get("tags", [])[:13],
        "market_data": market.get("price_analysis", {}),
        "competition": _estimate_competition(market),
        "opportunity": _calc_opportunity(market),
        "timestamp": datetime.now().isoformat(),
    }
    return json.dumps(result, indent=2)


def _estimate_competition(market: dict) -> str:
    n = market.get("total_found", 0)
    if n >= 20:
        return "HIGH — strong SEO and superior thumbnails required to rank"
    if n >= 10:
        return "MEDIUM — good opportunity with solid optimization"
    if n > 0:
        return "LOW — move fast, limited competition"
    return "UNKNOWN — insufficient live data"


def _calc_opportunity(market: dict) -> str:
    avg_str = market.get("price_analysis", {}).get("avg", "$0")
    nums = re.findall(r"[\d.]+", avg_str)
    avg = float(nums[0]) if nums else 0
    if avg > 15:
        return "HIGH — strong avg price, premium positioning viable"
    if avg > 8:
        return "MEDIUM — decent price point, focus on volume"
    if avg > 0:
        return "LOW — low price point, prioritize digital for margin"
    return "UNKNOWN"
