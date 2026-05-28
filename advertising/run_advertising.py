#!/usr/bin/env python3
"""
Advertising Agent System
Full-service AI advertising team that produces 3 complete campaign packages per company.

Usage:
    python -m advertising.run_advertising
    python advertising/run_advertising.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import ANTHROPIC_API_KEY
from advertising.models import CompanyBrief
from advertising.agents.ad_ceo_agent import AdCEOAgent
from advertising.tools.package_store import PackageStore

BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          ADVERTISING AGENT SYSTEM                                ║
║          Powered by Claude AI — Full-Service Ad Agency           ║
║                                                                  ║
║  TEAM:  Market Research  •  Brand Strategy  •  Copywriting       ║
║         Creative Direction  •  Social Media  •  Digital Ads      ║
║         Quality Control  •  CEO Orchestrator                     ║
║                                                                  ║
║  OUTPUT: 3 Complete Packages — Launch / Scale / Dominate         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

SECTION_DIVIDER = "═" * 70
THIN_DIVIDER = "─" * 70

MASTER_PROMPT_TEMPLATE = """Create a complete advertising package for the following company.

COMPANY BRIEF:
{brief}

Follow the mandatory workflow — START with Phase 0:
  Phase 0: Company Intelligence (live web research of the actual company)
  Phase 1: Market Research → QC review
  Phase 2: Brand Strategy → QC review
  Phase 3: Copywriting + Creative Direction → QC review
  Phase 4: Social Media Content + Digital Marketing → QC review
  Phase 5: Web Design (landing page + full website)→ QC review
  Phase 6: Assemble all 3 packages (Launch, Scale, Dominate)

This is a real client. Produce the highest quality advertising work your team is capable of. \
Every deliverable should be specific to THIS company, THIS audience, and THESE goals — never generic."""


def check_env() -> bool:
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY is not set.")
        print("Copy .env.example to .env and fill in your key.")
        return False
    return True


def prompt(label: str, required: bool = True, default: str = "") -> str:
    while True:
        suffix = f" [{default}]" if default else (" (required)" if required else " (optional, press Enter to skip)")
        try:
            value = input(f"  {label}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if value:
            return value
        if default:
            return default
        if not required:
            return ""
        print("  This field is required.")


def collect_company_brief() -> CompanyBrief:
    print(f"\n{SECTION_DIVIDER}")
    print("  COMPANY INTAKE FORM")
    print(f"{SECTION_DIVIDER}")
    print("  Fill in the details below. The more specific, the better the output.\n")

    name = prompt("Company Name")
    industry = prompt("Industry / Niche", default="")
    products_services = prompt("What do you sell? (products/services, be specific)")
    target_audience = prompt("Target Audience (age, lifestyle, pain points)")
    tone = prompt("Brand Tone", default="confident, approachable, modern")
    primary_goals = prompt("Primary Advertising Goals", default="brand awareness and sales")
    competitors = prompt("Key Competitors (comma-separated)", required=False)
    budget_range = prompt("Monthly Ad Budget", default="medium ($1k–$10k/mo)")
    website = prompt("Website URL", required=False)
    existing_tagline = prompt("Existing Tagline (if any)", required=False)
    additional_notes = prompt("Anything else we should know?", required=False)

    return CompanyBrief(
        name=name,
        industry=industry,
        products_services=products_services,
        target_audience=target_audience,
        tone=tone,
        primary_goals=primary_goals,
        competitors=competitors,
        budget_range=budget_range,
        website=website or None,
        existing_tagline=existing_tagline or None,
        additional_notes=additional_notes or None,
    )


def run_agency(brief: CompanyBrief, output_dir: str | None = None) -> PackageStore:
    store = PackageStore()
    ceo = AdCEOAgent(store)

    master_task = MASTER_PROMPT_TEMPLATE.format(brief=brief.to_prompt_string())

    print(f"\n{SECTION_DIVIDER}")
    print(f"  AGENCY KICKOFF — {brief.name.upper()}")
    print(f"{SECTION_DIVIDER}")
    print("  CEO is coordinating the full team...\n")
    print("  Phase sequence:")
    print("    0 → Company Intel     1 → Market Research  2 → Brand Strategy")
    print("    3 → Copy + Creative   4 → Social + Digital 5 → Web Design")
    print("    6 → QC Reviews        7 → Package Assembly\n")

    start = time.time()
    result = ceo.run(master_task)
    elapsed = time.time() - start

    print(f"\n{THIN_DIVIDER}")
    print(f"  Agency work complete in {elapsed:.0f}s")
    print(f"  Sections generated: {len(store.list_sections())}")
    print(f"{THIN_DIVIDER}\n")

    if output_dir:
        _export_packages(store, brief, output_dir)

    _print_packages(store, brief)

    if result and result.strip():
        print(f"\n{SECTION_DIVIDER}")
        print("  CEO FINAL SUMMARY")
        print(f"{SECTION_DIVIDER}")
        print(result)

    return store


def _export_packages(store: PackageStore, brief: CompanyBrief, output_dir: str) -> None:
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in brief.name)
    company_dir = os.path.join(output_dir, safe_name)
    os.makedirs(company_dir, exist_ok=True)

    store.export_json(os.path.join(company_dir, "complete_package.json"))

    for tier in ("launch", "scale", "dominate"):
        key = f"package_{tier}"
        content = store.load(key)
        if not content.startswith("[Section"):
            path = os.path.join(company_dir, f"package_{tier}.txt")
            store.export_section(key, path)

    store.export_section(
        "company_intelligence",
        os.path.join(company_dir, "00_company_intelligence.txt"),
    )
    store.export_section(
        PackageStore.MARKET_RESEARCH,
        os.path.join(company_dir, "01_market_research.txt"),
    )
    store.export_section(
        PackageStore.BRAND_STRATEGY,
        os.path.join(company_dir, "02_brand_strategy.txt"),
    )
    store.export_section(
        PackageStore.COPYWRITING,
        os.path.join(company_dir, "03_copywriting.txt"),
    )
    store.export_section(
        PackageStore.CREATIVE_DIRECTION,
        os.path.join(company_dir, "04_creative_direction.txt"),
    )
    store.export_section(
        PackageStore.SOCIAL_MEDIA_CONTENT,
        os.path.join(company_dir, "05_social_media.txt"),
    )
    store.export_section(
        PackageStore.DIGITAL_MARKETING,
        os.path.join(company_dir, "06_digital_marketing.txt"),
    )

    # Export website HTML files — open directly in any browser
    for section_key, filename in (
        ("website_landing_page", "website_landing_page.html"),
        ("website_full", "website_full.html"),
    ):
        content = store.load(section_key)
        if not content.startswith("[Section"):
            store.export_section(section_key, os.path.join(company_dir, filename))

    print(f"\n  Output saved to: {company_dir}/")
    _print_file_tree(company_dir)


def _print_file_tree(company_dir: str) -> None:
    print(f"\n  Files generated:")
    try:
        for fname in sorted(os.listdir(company_dir)):
            fpath = os.path.join(company_dir, fname)
            size = os.path.getsize(fpath)
            unit = "KB" if size >= 1024 else "B"
            display_size = f"{size // 1024}{unit}" if size >= 1024 else f"{size}{unit}"
            icon = "🌐" if fname.endswith(".html") else "📄"
            print(f"    {icon}  {fname:<40} {display_size}")
    except OSError:
        pass


def _print_packages(store: PackageStore, brief: CompanyBrief) -> None:
    tiers = [
        ("launch",   "PACKAGE 1 — LAUNCH",   "Get In The Game"),
        ("scale",    "PACKAGE 2 — SCALE",     "Dominate Your Market"),
        ("dominate", "PACKAGE 3 — DOMINATE",  "Own the Entire Space"),
    ]

    for tier, title, subtitle in tiers:
        content = store.load(f"package_{tier}")
        if content.startswith("[Section"):
            continue
        print(f"\n{'█'*70}")
        print(f"  {title} — {subtitle}")
        print(f"{'█'*70}\n")
        print(content)
        print()


def run_batch(companies: list[CompanyBrief], output_dir: str = "output") -> None:
    print(f"\n  BATCH MODE — {len(companies)} companies queued\n")
    for i, brief in enumerate(companies, 1):
        print(f"\n{'█'*70}")
        print(f"  COMPANY {i}/{len(companies)}: {brief.name.upper()}")
        print(f"{'█'*70}")
        run_agency(brief, output_dir=output_dir)


def main():
    print(BANNER)

    if not check_env():
        sys.exit(1)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")

    print("  How many companies do you want to create packages for?")
    try:
        count_str = input("  Number of companies [1]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)

    try:
        count = int(count_str) if count_str else 1
        count = max(1, min(count, 10))
    except ValueError:
        count = 1

    companies: list[CompanyBrief] = []
    for i in range(count):
        if count > 1:
            print(f"\n  ──── COMPANY {i + 1} OF {count} ────")
        companies.append(collect_company_brief())

    if len(companies) == 1:
        run_agency(companies[0], output_dir=output_dir)
    else:
        run_batch(companies, output_dir=output_dir)

    print(f"\n{'═'*70}")
    print("  All packages complete. Check the output/ directory for saved files.")
    print(f"{'═'*70}\n")


if __name__ == "__main__":
    main()
