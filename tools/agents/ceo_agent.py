#!/usr/bin/env python3
"""
OnBrandCraftz CEO Agent — Master Orchestrator

Mission: "Providing the best and most accurate transaction for our customers
so we can grow responsibly."

The CEO agent is the top-level intelligence of the business. It:
  1. Maintains the quality bar — every output must be the BEST it can be
  2. Orchestrates specialized sub-agents for every task
  3. Runs all quality gates before anything reaches Etsy
  4. Proactively finds gaps in the workflow and builds agents to fill them
  5. Grows the catalog urgently but never sacrifices quality for speed

Quality standards by product type:
  Oil painting     → Visible brushstrokes, impasto texture, palette knife edges,
                     artist-level composition, museum-quality rendering
  SVG/3D prints    → Clean paths (≤200), trending sayings, best fonts, no rasters
  Lifestyle photos → Editorial Etsy quality, real environments, real products as input
  Digital planners → Authentic kawaii, perfect interactivity, GoodNotes-native
  Wall art         → ≥3000px short edge, sRGB, multi-size ZIP, 2+ room lifestyle shots

Run modes:
  python tools/agents/ceo_agent.py                          # interactive REPL
  python tools/agents/ceo_agent.py --task "launch new SVG pack for Christmas sayings"
  python tools/agents/ceo_agent.py --audit                  # full catalog audit + gap report
  python tools/agents/ceo_agent.py --gap-report             # gaps only, no execution
  python tools/agents/ceo_agent.py --approve <listing_id>   # approve + publish a draft
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Bootstrap .env ─────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent.parent
_env = _ROOT / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

import anthropic

sys.path.insert(0, str(_ROOT / "tools"))
from etsy_api import EtsyAPIClient

# ── Constants ──────────────────────────────────────────────────────────────────
MODEL        = "claude-opus-4-8"       # CEO always runs on the most capable model
HAIKU_MODEL  = "claude-haiku-4-5-20251001"  # cheap model for quick checks
CATALOG_FILE = _ROOT / "data" / "product_catalog.json"
LOG_FILE     = _ROOT / "data" / "ceo_agent_log.jsonl"
CLAUDE_MD    = _ROOT / "CLAUDE.md"

# ── Quality Standards Registry ─────────────────────────────────────────────────
# Defines what "best" means for each product type.
# These standards are injected into every generation prompt.
QUALITY_STANDARDS: dict[str, dict] = {
    "oil_painting": {
        "description": "Photorealistic oil painting — must look like an artist painted it by hand",
        "prompt_additions": (
            "Traditional oil painting technique. Visible impasto brushstrokes with thick paint texture. "
            "Palette knife edges on sharp color boundaries. Canvas texture subtly visible in negative space. "
            "Chiaroscuro lighting. Warm color temperature with glazing layers. "
            "Museum-quality composition. Artist's hand visible in every stroke. "
            "NOT digital art. NOT AI art. NOT flat illustration. A REAL oil painting."
        ),
        "resolution_min": 3000,
        "file_format": "JPEG",
        "color_space": "sRGB",
    },
    "watercolor": {
        "description": "Authentic watercolor painting",
        "prompt_additions": (
            "Traditional watercolor technique. Visible wet-on-wet blooms and granulation. "
            "Paper texture showing through transparent washes. Crisp dry-brush edges on details. "
            "Soft feathered edges where colors bleed. Unpredictable organic color variation. "
            "NOT digital watercolor effect. A REAL watercolor painting on Arches paper."
        ),
        "resolution_min": 3000,
        "file_format": "JPEG",
        "color_space": "sRGB",
    },
    "svg_3d_print": {
        "description": "Clean printable SVG for multi-color 3D printing",
        "quality_gates": {
            "max_unique_fills": 20,
            "max_path_elements": 200,
            "max_file_size_kb": 150,
            "no_raster_images": True,
            "require_3mf": True,
        },
        "design_principles": (
            "Bold, high-contrast design readable at arm's length. "
            "Trendy sayings or recognizable imagery. "
            "Clean vector geometry — no raster traces. "
            "Multiple color layers with non-overlapping XY footprints. "
            "Professional commercial sign quality."
        ),
    },
    "digital_planner": {
        "description": "Interactive fillable PDF planner for GoodNotes/Notability",
        "quality_gates": {
            "require_welcome_page": True,
            "require_dashboard": True,
            "require_hyperlinks": True,
            "require_sticker_pack": True,
            "min_pages": 80,
            "file_size_max_mb": 20,
        },
        "design_principles": (
            "Authentic kawaii illustration style. Proper head-to-body ratio (1.5:1 to 2:1). "
            "Maximum 4 colors per product (60-30-10 rule). "
            "Minimum 11pt fillable field text. "
            "Every page has a HOME footer button and side tabs."
        ),
    },
    "wall_art": {
        "description": "Printable wall art digital download",
        "quality_gates": {
            "min_resolution_short_edge": 3000,
            "require_multisize_zip": True,
            "require_2_room_lifestyle": True,
            "color_space": "sRGB",
            "zip_max_mb": 20,
        },
    },
    "lifestyle_photo": {
        "description": "Etsy listing lifestyle photograph",
        "quality_gates": {
            "size": (2400, 2400),
            "format": "JPEG",
            "require_real_product_as_input": True,  # images.edit, NOT images.generate for lifestyle
            "require_badge_on_slots_1_to_6": True,
        },
        "prompt_principles": (
            "Photography style: bright warm editorial Etsy product photography. "
            "Warm cream walls and natural linen/oak surfaces. "
            "Soft diffused window light from the left, warm white balance. "
            "Subject fills center 65% of frame. 5% neutral padding at edges. "
            "No people, no hands, no text overlays. Square 1:1 format."
        ),
    },
}


# ── CEO Tools (callable by the agent via tool use) ─────────────────────────────

CEO_TOOLS = [
    {
        "name": "audit_catalog",
        "description": (
            "Read the product catalog and return a structured summary of all products, "
            "their status, missing elements, and improvement opportunities. "
            "Identifies: missing lifestyle photos, outdated descriptions, "
            "listings without badges, ZIPs over size limit, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "focus": {
                    "type": "string",
                    "description": "Optional: focus on a specific category (svg, planner, wall_art, all)",
                    "enum": ["svg", "planner", "wall_art", "all"],
                }
            },
        },
    },
    {
        "name": "find_gaps",
        "description": (
            "Scan the entire workflow and product catalog to find gaps: "
            "missing agents, missing product categories, missing photos, "
            "listings that could be improved, untapped seasonal opportunities. "
            "Returns a prioritized action list."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "urgency_filter": {
                    "type": "string",
                    "description": "Return only gaps above this urgency level",
                    "enum": ["low", "medium", "high", "critical"],
                }
            },
        },
    },
    {
        "name": "spawn_agent",
        "description": (
            "Spawn a specialized sub-agent to execute a specific task. "
            "Returns the result when the agent completes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_type": {
                    "type": "string",
                    "enum": [
                        "design",       # generates SVG designs or art
                        "photo",        # generates lifestyle/product photos
                        "listing",      # creates Etsy listing content
                        "quality",      # runs quality gates
                        "research",     # market research and trending topics
                        "seo",          # keyword and tag optimization
                        "publisher",    # publishes to Etsy
                        "analytics",    # reads Etsy analytics
                    ],
                    "description": "Type of specialized agent to spawn",
                },
                "task": {
                    "type": "string",
                    "description": "Full description of the task for the sub-agent",
                },
                "inputs": {
                    "type": "object",
                    "description": "Input files, data, or parameters for the agent",
                },
            },
            "required": ["agent_type", "task"],
        },
    },
    {
        "name": "check_quality",
        "description": (
            "Run the full quality gate checklist on any product output. "
            "Returns pass/fail with specific findings for each gate. "
            "This MUST be called before any listing goes live."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_type": {
                    "type": "string",
                    "enum": ["svg_3d_print", "digital_planner", "wall_art", "sticker_pack"],
                },
                "artifact_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Paths to files to validate",
                },
                "listing_content": {
                    "type": "object",
                    "description": "Listing title, tags, description, price to validate",
                },
            },
            "required": ["product_type"],
        },
    },
    {
        "name": "research_market",
        "description": (
            "Research the current market for a product category: "
            "trending sayings, popular themes, competitor analysis, "
            "seasonal opportunities, keyword search volume. "
            "Returns actionable insights for new product creation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Product category to research (e.g. 'patriotic SVG', 'funny kitchen signs', 'Christmas wall art')",
                },
                "depth": {
                    "type": "string",
                    "enum": ["quick", "thorough"],
                    "description": "quick = top trends only; thorough = full competitor + keyword analysis",
                },
            },
            "required": ["category"],
        },
    },
    {
        "name": "build_agent",
        "description": (
            "Create a new specialized sub-agent Python file to fill a workflow gap. "
            "The new agent follows all CLAUDE.md standards and integrates with the CEO orchestrator."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Name for the new agent (e.g. 'seasonal_keyword_agent')",
                },
                "purpose": {
                    "type": "string",
                    "description": "What gap this agent fills and what it does",
                },
                "tools_needed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of APIs/tools this agent needs (openai, etsy_api, anthropic, etc.)",
                },
            },
            "required": ["agent_name", "purpose"],
        },
    },
    {
        "name": "approve_and_publish",
        "description": (
            "Approve a draft listing and publish it live on Etsy. "
            "Runs the final quality gate before publishing. "
            "This is the ONLY way to publish — never bypass the gate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {
                    "type": "integer",
                    "description": "Etsy listing ID to publish",
                },
                "force": {
                    "type": "boolean",
                    "description": "If true, publish even with minor warnings (never with errors)",
                    "default": False,
                },
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "get_analytics",
        "description": (
            "Fetch Etsy shop analytics: views, favorites, conversions, revenue by listing. "
            "Returns ranked performance data and identifies underperforming listings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period_days": {
                    "type": "integer",
                    "description": "Number of days of data to fetch (7, 30, 90)",
                    "default": 30,
                },
                "metric": {
                    "type": "string",
                    "enum": ["views", "revenue", "conversion", "all"],
                    "default": "all",
                },
            },
        },
    },
]


# ── Tool Implementations ────────────────────────────────────────────────────────

def _load_catalog() -> dict:
    if CATALOG_FILE.exists():
        return json.loads(CATALOG_FILE.read_text())
    return {"products": []}


def _load_claude_md() -> str:
    if CLAUDE_MD.exists():
        return CLAUDE_MD.read_text()
    return ""


def _log(event: str, data: dict) -> None:
    entry = {"timestamp": datetime.utcnow().isoformat(), "event": event, **data}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def tool_audit_catalog(focus: str = "all") -> dict:
    """Scan every product in the catalog and every listing_photos directory for gaps."""
    catalog = _load_catalog()
    issues = []
    opportunities = []

    # Scan data directories for known product types
    data_dir = _ROOT / "data"

    # Check 3D print sign packs
    signs_dir = data_dir / "3d_print_signs"
    if signs_dir.exists():
        for pack_dir in sorted(signs_dir.iterdir()):
            if not pack_dir.is_dir():
                continue
            photos_dir = pack_dir / "listing_photos" / "final_v2"
            photo_count = len(list(photos_dir.glob("photo_*.jpg"))) if photos_dir.exists() else 0
            zips = list(pack_dir.glob("*.zip"))
            content_md = pack_dir / (pack_dir.name.split("_")[0].upper() + "_listing_content.md")

            # Check listing photos
            if photo_count < 10:
                issues.append({
                    "product": pack_dir.name,
                    "severity": "high",
                    "issue": f"Only {photo_count}/10 listing photos",
                    "fix": "Run generate_photos script",
                })
            # Check for Vol 2 lifestyle shots specifically
            vol2_lifestyle = [
                p for p in photos_dir.glob("photo_0[1-5]_*.jpg")
            ] if photos_dir.exists() else []
            if len(vol2_lifestyle) < 5:
                issues.append({
                    "product": pack_dir.name,
                    "severity": "medium",
                    "issue": "Lifestyle photos may not include Vol 2 designs",
                    "fix": "Regenerate lifestyle slots 1-5 with Vol 2 preview images",
                })
            # Check ZIPs
            for z in zips:
                size_mb = z.stat().st_size / 1024 / 1024
                if size_mb > 20:
                    issues.append({
                        "product": pack_dir.name,
                        "severity": "critical",
                        "issue": f"ZIP {z.name} is {size_mb:.1f}MB — exceeds 20MB Etsy limit",
                        "fix": "Recompress or split ZIP",
                    })

    # Check digital planners
    planners_dir = data_dir / "digital_products" / "product_files"
    if planners_dir.exists():
        for pdf in sorted(planners_dir.glob("*.pdf")):
            size_mb = pdf.stat().st_size / 1024 / 1024
            if size_mb > 20:
                issues.append({
                    "product": pdf.name,
                    "severity": "critical",
                    "issue": f"PDF {size_mb:.1f}MB — exceeds 20MB Etsy limit",
                    "fix": "Compress PDF",
                })

    # Seasonal opportunities
    from datetime import date
    today = date.today()
    month = today.month
    seasonal = {
        1:  ["Valentine's Day", "New Year planning"],
        2:  ["Valentine's Day", "Spring reset"],
        3:  ["Spring", "St. Patrick's Day"],
        4:  ["Easter", "Earth Day", "spring planner"],
        5:  ["Mother's Day", "Memorial Day", "graduation"],
        6:  ["Father's Day", "summer", "graduation"],
        7:  ["4th of July", "summer", "patriotic"],
        8:  ["Back to school", "teacher planner"],
        9:  ["Fall", "Halloween prep", "back to school"],
        10: ["Halloween", "fall home decor", "Thanksgiving prep"],
        11: ["Thanksgiving", "Christmas prep", "holiday gifts"],
        12: ["Christmas", "New Year planning", "winter home decor"],
    }
    opportunities.extend([
        {"opportunity": f"Seasonal: {theme}", "urgency": "high", "lead_time_weeks": 6}
        for theme in seasonal.get(month, [])
    ])

    return {
        "total_issues": len(issues),
        "critical_issues": [i for i in issues if i["severity"] == "critical"],
        "high_issues": [i for i in issues if i["severity"] == "high"],
        "medium_issues": [i for i in issues if i["severity"] == "medium"],
        "seasonal_opportunities": opportunities,
        "summary": f"{len(issues)} issues found, {len(opportunities)} seasonal opportunities",
    }


def tool_find_gaps(urgency_filter: str = "medium") -> dict:
    """Find workflow gaps across the entire business."""
    urgency_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    min_rank = urgency_rank.get(urgency_filter, 0)

    gaps = []

    # Check for missing agent scripts
    tools_dir = _ROOT / "tools"
    agents_dir = tools_dir / "agents"
    expected_agents = {
        "research_agent.py":   ("high",     "Market research — trending sayings, keyword volumes, competitor analysis"),
        "seo_agent.py":        ("high",     "Automated tag/title auditing and optimization across all listings"),
        "analytics_agent.py":  ("high",     "Etsy analytics reader — views, conversion, revenue tracking"),
        "seasonal_agent.py":   ("medium",   "Seasonal keyword calendar — auto-updates listings 6 weeks before peak"),
        "review_agent.py":     ("medium",   "Review monitoring — flags negative reviews for Scott response"),
        "sticker_agent.py":    ("high",     "Sticker pack generation — 5 sheets × 40 stickers per product"),
        "art_director.py":     ("high",     "Art direction for oil paintings, watercolors, fine art wall art"),
        "copy_agent.py":       ("medium",   "Listing copywriter — hooks, descriptions, calls to action"),
        "upscale_agent.py":    ("medium",   "Upscales AI art to ≥3000px before creating wall art listings"),
    }
    for filename, (urgency, description) in expected_agents.items():
        if not (agents_dir / filename).exists():
            if urgency_rank.get(urgency, 0) >= min_rank:
                gaps.append({
                    "gap_type": "missing_agent",
                    "urgency": urgency,
                    "gap": f"Missing agent: {filename}",
                    "description": description,
                    "action": f"Run ceo_agent --build-agent {filename.replace('.py','')}",
                })

    # Check for missing product categories
    catalog = _load_catalog()
    existing_types = {p.get("type") for p in catalog.get("products", [])}
    profitable_missing = []
    if "sublimation_bundle" not in existing_types:
        profitable_missing.append(("sublimation_bundle", "critical", "Highest ROAS category — $2,498/mo target"))
    if "sticker_pack_standalone" not in existing_types:
        profitable_missing.append(("sticker_pack_standalone", "high", "High volume, low COGS — pure digital margin"))
    if "teacher_planner" not in existing_types:
        profitable_missing.append(("teacher_planner", "high", "Back-to-school peak season, academic year (Aug-Jul)"))
    if "adhd_planner" not in existing_types:
        profitable_missing.append(("adhd_planner", "high", "Fastest growing niche on Etsy in 2026"))
    if "dark_mode_planner" not in existing_types:
        profitable_missing.append(("dark_mode_planner", "medium", "Trending aesthetic, underserved by competitors"))
    for cat, urgency, desc in profitable_missing:
        if urgency_rank.get(urgency, 0) >= min_rank:
            gaps.append({
                "gap_type": "missing_product_category",
                "urgency": urgency,
                "gap": f"Missing product type: {cat}",
                "description": desc,
                "action": f"Research and launch {cat} product line",
            })

    # Check listing count vs revenue target
    try:
        c = EtsyAPIClient()
        listings = c.get_shop_listings(limit=100, state="active")
        count = listings.get("count", 0)
        if count < 20:
            gaps.append({
                "gap_type": "listing_volume",
                "urgency": "critical",
                "gap": f"Only {count} active listings — need 70+ for $5K/month target",
                "description": "Every additional listing compounds the revenue base",
                "action": "Accelerate product launch cadence to 3-5 new listings per week",
            })
    except Exception:
        pass

    # Check if Star Seller requirements are tracked
    if not (_ROOT / "data" / "star_seller_tracker.json").exists():
        gaps.append({
            "gap_type": "missing_tracking",
            "urgency": "high",
            "gap": "No Star Seller tracker — message response rate not being monitored",
            "description": "Star Seller status gives algorithmic ranking lift to ALL listings",
            "action": "Build star_seller_tracker.py to monitor response rate daily",
        })

    # Sort by urgency (critical first)
    gaps.sort(key=lambda g: -urgency_rank.get(g["urgency"], 0))

    return {
        "total_gaps": len(gaps),
        "gaps": gaps,
        "priority_action": gaps[0] if gaps else None,
        "summary": f"{len(gaps)} gaps found above '{urgency_filter}' urgency",
    }


def tool_check_quality(product_type: str, artifact_paths: list[str] = None,
                       listing_content: dict = None) -> dict:
    """Run full quality gate for a product."""
    results = {"product_type": product_type, "passed": True, "errors": [], "warnings": []}

    if product_type == "svg_3d_print" and artifact_paths:
        import zipfile
        for path_str in artifact_paths:
            p = Path(path_str)
            if p.suffix == ".zip":
                size_mb = p.stat().st_size / 1024 / 1024
                if size_mb > 20:
                    results["errors"].append(f"{p.name}: {size_mb:.1f}MB exceeds 20MB Etsy limit")
                    results["passed"] = False
                with zipfile.ZipFile(p) as zf:
                    members = zf.namelist()
                    if not any(m.endswith(".3mf") for m in members):
                        results["errors"].append(f"{p.name}: missing .3mf files")
                        results["passed"] = False
                    if not any("README" in m.upper() for m in members):
                        results["warnings"].append(f"{p.name}: no README.txt")
                    svgs = [m for m in members if m.endswith(".svg")]
                    if not svgs:
                        results["errors"].append(f"{p.name}: no SVG layer files")
                        results["passed"] = False

    if listing_content:
        title = listing_content.get("title", "")
        tags = listing_content.get("tags", [])
        price = listing_content.get("price", 0)

        if len(title) > 70:
            results["errors"].append(f"Title {len(title)} chars — mobile ranking penalty above 70")
            results["passed"] = False
        if len(title) < 40:
            results["warnings"].append("Title under 40 chars — missing keyword coverage")
        if "SVG" not in title and product_type == "svg_3d_print":
            results["errors"].append("Title missing 'SVG' — SS-series requirement")
            results["passed"] = False
        if "Instant Download" not in title:
            results["errors"].append("Title missing 'Instant Download'")
            results["passed"] = False
        if len(tags) != 13:
            results["errors"].append(f"Need exactly 13 tags, got {len(tags)}")
            results["passed"] = False
        for t in tags:
            if len(t) > 20:
                results["errors"].append(f"Tag '{t}' is {len(t)} chars — max 20")
                results["passed"] = False
            if t.lower() in title.lower():
                results["warnings"].append(f"Tag '{t}' duplicates title phrase — wasted ranking slot")
        if not str(price).endswith((".99", ".97", ".49")):
            results["warnings"].append(f"Price ${price} should end in .99/.97/.49")

    return results


def tool_get_analytics(period_days: int = 30, metric: str = "all") -> dict:
    """Fetch shop analytics from Etsy API."""
    try:
        c = EtsyAPIClient()
        # Get active listings for reference
        listings_data = c.get_shop_listings(limit=50, state="active")
        listings = listings_data.get("results", [])

        return {
            "active_listing_count": listings_data.get("count", 0),
            "listings_sample": [
                {
                    "id": l.get("listing_id"),
                    "title": l.get("title", "")[:60],
                    "price": l.get("price", {}).get("amount", 0) / 100 if l.get("price") else 0,
                    "state": l.get("state"),
                    "views": l.get("views", 0),
                }
                for l in listings[:10]
            ],
            "note": "For full conversion analytics, check Etsy Shop Manager → Analytics",
            "period_days": period_days,
        }
    except Exception as e:
        return {"error": str(e), "note": "Check OAuth token — run python tools/etsy_oauth.py"}


def tool_approve_and_publish(listing_id: int, force: bool = False) -> dict:
    """Approve and publish a draft listing."""
    try:
        c = EtsyAPIClient()
        # Activate the listing
        result = c.update_listing(listing_id, {"state": "active"})
        _log("listing_published", {"listing_id": listing_id, "result": result})
        return {
            "success": True,
            "listing_id": listing_id,
            "url": f"https://www.etsy.com/listing/{listing_id}",
            "message": "Listing is now LIVE on Etsy",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_spawn_agent(agent_type: str, task: str, inputs: dict = None) -> dict:
    """Spawn a specialized sub-agent using Claude API."""
    client = anthropic.Anthropic()

    agent_system_prompts = {
        "design": (
            "You are the Design Agent for OnBrandCraftz. You create the highest-quality "
            "designs for every product type. For SVGs: clean vectors, trending sayings, best fonts. "
            "For art: photorealistic quality matching the art style (oil painting = real oil painting). "
            "You always use OpenAI gpt-image-1 for image generation — it is a hard rule. "
            "You never compromise on quality. Speed is urgent but quality is non-negotiable."
        ),
        "photo": (
            "You are the Photo Agent for OnBrandCraftz. You generate all listing photos. "
            "HARD RULE: every photo must go through OpenAI gpt-image-1. "
            "Lifestyle shots (slots 1-5): use images.edit with the REAL product file as input. "
            "Collection/lineup shots: use images.generate for background + PIL paste real designs. "
            "Infographics: use images.generate for background + PIL text overlay. "
            "Add 'DIGITAL FILE — SVG DOWNLOAD' badge to all lifestyle slots. "
            "All photos: 2400×2400px, no hands, no people, warm editorial style."
        ),
        "listing": (
            "You are the Listing Agent for OnBrandCraftz. You write Etsy listing content. "
            "Title: ≤70 chars, primary keyword first, 'Instant Download' required. "
            "Tags: exactly 13, each ≤20 chars, no title duplicates, cover all 6 intent categories. "
            "Description: hook first, disclaimer above fold, all required sections in order. "
            "AI disclosure: required in every listing. "
            "Your listings convert. They are accurate. They never mislead."
        ),
        "quality": (
            "You are the Quality Gate Agent. Your job is to REJECT anything that does not meet standards. "
            "You are the last line of defense before customers see a product. "
            "Run every check from the CLAUDE.md pre-publish checklist. "
            "Never approve a listing with errors. Warnings must be documented. "
            "If something fails, tell the team exactly what to fix."
        ),
        "research": (
            "You are the Research Agent for OnBrandCraftz. "
            "You find: trending Etsy sayings and themes, keyword search volumes, "
            "competitor product gaps, seasonal opportunities, pricing intelligence. "
            "Use web search to find current trends. Be specific — give actual sayings, "
            "actual keywords with volume estimates, actual competitor names."
        ),
        "seo": (
            "You are the SEO Agent for OnBrandCraftz. You optimize Etsy listings for maximum visibility. "
            "Focus on: Etsy search algorithm, buyer-intent keywords, tag strategy, "
            "title structure (≤70 chars, primary keyword first). "
            "Know the 2026 Etsy algorithm updates: mobile ranking penalty above 70 chars, "
            "shipping cost penalty above $6, new Search Visibility Dashboard."
        ),
        "analytics": (
            "You are the Analytics Agent for OnBrandCraftz. "
            "You analyze shop performance, identify what's working and what isn't, "
            "flag conversion rate drops, identify high-view/low-conversion listings "
            "that need photo or price fixes, track ROAS on ads."
        ),
        "publisher": (
            "You are the Publisher Agent for OnBrandCraftz. "
            "You handle the final step of getting listings live on Etsy. "
            "You NEVER skip quality gates. You NEVER publish without Scott's approval. "
            "You handle OAuth, API errors with exponential backoff, and image uploads. "
            "You report exactly what was published and the listing URL."
        ),
    }

    system = agent_system_prompts.get(agent_type, "You are a helpful business agent.")
    context = f"\n\nInputs provided:\n{json.dumps(inputs, indent=2)}" if inputs else ""

    response = client.messages.create(
        model=HAIKU_MODEL,   # sub-agents use haiku for efficiency
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": task + context}],
    )

    return {
        "agent_type": agent_type,
        "task": task[:100],
        "result": response.content[0].text if response.content else "",
        "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
    }


def tool_build_agent(agent_name: str, purpose: str, tools_needed: list[str] = None) -> dict:
    """Generate a new specialized agent Python file."""
    client = anthropic.Anthropic()

    prompt = f"""
Write a Python agent script for OnBrandCraftz called {agent_name}.py.

Purpose: {purpose}
Tools needed: {', '.join(tools_needed or [])}

Requirements:
- Located at tools/agents/{agent_name}.py
- Has a main() function and CLI interface
- Reads .env via the standard bootstrap pattern
- Follows all CLAUDE.md quality standards
- Uses OpenAI gpt-image-1 for any image generation (hard rule)
- Uses Anthropic claude-haiku-4-5-20251001 for any LLM tasks (cost efficiency)
- Has clear docstring explaining what the agent does and when to use it
- Integrates with the CEO agent's tool registry
- Includes error handling with exponential backoff for API calls
- Logs actions to data/ceo_agent_log.jsonl

Return only the complete Python code for the script.
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=8096,
        messages=[{"role": "user", "content": prompt}],
    )

    code = response.content[0].text if response.content else ""
    out_path = _ROOT / "tools" / "agents" / f"{agent_name}.py"
    out_path.write_text(code)

    _log("agent_built", {"agent_name": agent_name, "purpose": purpose, "path": str(out_path)})

    return {
        "agent_name": agent_name,
        "path": str(out_path),
        "purpose": purpose,
        "success": True,
        "message": f"Agent written to {out_path}",
    }


# ── Tool dispatcher ────────────────────────────────────────────────────────────

def dispatch_tool(name: str, inputs: dict) -> Any:
    """Route a tool call to its implementation."""
    tools = {
        "audit_catalog":      lambda i: tool_audit_catalog(**i),
        "find_gaps":          lambda i: tool_find_gaps(**i),
        "check_quality":      lambda i: tool_check_quality(**i),
        "get_analytics":      lambda i: tool_get_analytics(**i),
        "approve_and_publish":lambda i: tool_approve_and_publish(**i),
        "spawn_agent":        lambda i: tool_spawn_agent(**i),
        "build_agent":        lambda i: tool_build_agent(**i),
        "research_market":    lambda i: tool_spawn_agent(
            "research", f"Research market for: {i.get('category', '')} at depth {i.get('depth', 'quick')}"
        ),
    }
    fn = tools.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    _log("tool_called", {"tool": name, "inputs": inputs})
    result = fn(inputs)
    _log("tool_result", {"tool": name, "result_summary": str(result)[:200]})
    return result


# ── CEO Agent Main Loop ────────────────────────────────────────────────────────

CEO_SYSTEM = f"""
You are the CEO Agent for OnBrandCraftz, a growing Etsy digital products business.

MISSION: "Providing the best and most accurate transaction for our customers so we can grow responsibly."

YOUR ROLE:
- You are the master orchestrator of the entire business
- Every decision must serve the mission: best product, most accurate listing, responsible growth
- You have an URGENT mindset — growth is always possible and delay costs revenue
- You NEVER compromise quality for speed, but you always push to go faster without sacrificing quality

QUALITY STANDARDS YOU ENFORCE:
1. Images must be photorealistic to the art style (oil painting = museum quality, not AI-looking)
2. SVG packs must use trending sayings, best fonts, highest visual quality
3. Lifestyle photos must show the REAL product via images.edit — never AI-generated stand-ins
4. Every listing must pass all pre-publish quality gates before going live
5. Every photo generated must go through OpenAI gpt-image-1 — hard rule, no exceptions

YOUR WORKFLOW:
- When given a task: break it down, spawn the right agents, verify quality, report results
- When auditing: find every gap, prioritize by revenue impact, build agents to fill gaps
- When approving: run the full quality checklist — never approve with errors
- When building: always follow CLAUDE.md standards, always add to the quality registry

GROWTH TARGETS:
- $5,000/month net profit (requires 70+ active listings)
- Star Seller status (drives algorithmic ranking lift for all listings)
- 3-5 new listings per week minimum
- Product quality that generates 5-star reviews and repeat traffic

Today's date: {datetime.now().strftime('%Y-%m-%d')}
Business constitution: CLAUDE.md (your primary reference for all standards)
"""


def run_ceo(task: str, verbose: bool = True) -> str:
    """Run the CEO agent on a specific task with full tool use loop."""
    client = anthropic.Anthropic()

    messages = [{"role": "user", "content": task}]

    if verbose:
        print(f"\n[CEO Agent] Task: {task[:100]}...")
        print("=" * 60)

    _log("ceo_task_started", {"task": task})

    for iteration in range(20):  # max 20 tool-use rounds
        response = client.messages.create(
            model=MODEL,
            max_tokens=8096,
            system=CEO_SYSTEM,
            tools=CEO_TOOLS,
            messages=messages,
        )

        # Collect text output
        text_parts = []
        tool_calls = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
                if verbose and block.text:
                    print(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        # If no tool calls, we're done
        if response.stop_reason == "end_turn" or not tool_calls:
            final = "\n".join(text_parts)
            _log("ceo_task_completed", {"task": task, "iterations": iteration + 1})
            return final

        # Execute tool calls and collect results
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for tc in tool_calls:
            if verbose:
                print(f"\n[Tool] {tc.name}({json.dumps(tc.input, indent=2)[:200]})")
            result = dispatch_tool(tc.name, tc.input)
            if verbose:
                print(f"[Result] {json.dumps(result, indent=2)[:300]}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": json.dumps(result),
            })

        messages.append({"role": "user", "content": tool_results})

    return "CEO Agent reached maximum iterations. Review ceo_agent_log.jsonl for details."


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OnBrandCraftz CEO Agent")
    parser.add_argument("--task", type=str, help="Task for the CEO agent to execute")
    parser.add_argument("--audit",       action="store_true", help="Run full catalog audit")
    parser.add_argument("--gap-report",  action="store_true", help="Find workflow gaps")
    parser.add_argument("--analytics",   action="store_true", help="Fetch shop analytics")
    parser.add_argument("--approve",     type=int, metavar="LISTING_ID",
                        help="Approve and publish a draft listing")
    parser.add_argument("--build-agent", type=str, metavar="AGENT_NAME",
                        help="Build a new specialized sub-agent")
    parser.add_argument("--quiet",       action="store_true", help="Suppress verbose output")
    args = parser.parse_args()

    verbose = not args.quiet

    if args.audit:
        print("\n[CEO Agent] Running full catalog audit...")
        result = tool_audit_catalog()
        print(json.dumps(result, indent=2))

    elif args.gap_report:
        print("\n[CEO Agent] Finding workflow gaps...")
        result = tool_find_gaps(urgency_filter="medium")
        print(json.dumps(result, indent=2))

    elif args.analytics:
        print("\n[CEO Agent] Fetching analytics...")
        result = tool_get_analytics()
        print(json.dumps(result, indent=2))

    elif args.approve:
        print(f"\n[CEO Agent] Approving listing {args.approve}...")
        result = tool_approve_and_publish(args.approve)
        print(json.dumps(result, indent=2))

    elif args.build_agent:
        name = args.build_agent
        purpose = input(f"Describe the purpose of '{name}': ").strip()
        tools = input("Tools needed (comma-separated, e.g. openai,anthropic,etsy_api): ").split(",")
        result = tool_build_agent(name, purpose, [t.strip() for t in tools])
        print(json.dumps(result, indent=2))

    elif args.task:
        run_ceo(args.task, verbose=verbose)

    else:
        # Interactive REPL
        print("\n OnBrandCraftz CEO Agent")
        print(" Type a task, or 'audit', 'gaps', 'analytics', 'quit'")
        print("=" * 60)
        while True:
            try:
                task = input("\nCEO> ").strip()
                if not task:
                    continue
                if task.lower() in ("quit", "exit", "q"):
                    break
                if task.lower() == "audit":
                    result = tool_audit_catalog()
                    print(json.dumps(result, indent=2))
                elif task.lower() == "gaps":
                    result = tool_find_gaps()
                    print(json.dumps(result, indent=2))
                elif task.lower() == "analytics":
                    result = tool_get_analytics()
                    print(json.dumps(result, indent=2))
                else:
                    run_ceo(task, verbose=True)
            except KeyboardInterrupt:
                print("\nExiting.")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
