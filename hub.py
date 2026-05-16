#!/usr/bin/env python3
"""
OnBrandCraftz — Etsy Agent Hub
Central command interface for managing your Etsy shop via AI agents.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import ANTHROPIC_API_KEY
from agents import (
    CEOAgent, SalesAgent, ProductAgent, MarketingAgent,
    AnalyticsAgent, CustomerServiceAgent, SocialMediaAgent,
    ArtCreationAgent, PlannerDesignAgent, QualityCheckAgent, EtsyListingAgent,
    StoreManagerAgent, SalesProcessorAgent, BrandDesignAgent,
    FinancialAgent, PrintProductionAgent, EtsyAdsAgent,
    CompetitorIntelAgent, PromotionsAgent, TaxComplianceAgent,
    ReturnsAgent, SupplyChainAgent, EmailMarketingAgent, ABTestingAgent,
)

AGENTS = {
    # ── Orchestrator ────────────────────────────────────────────────────────
    "ceo":       ("CEO Agent",                lambda: CEOAgent()),

    # ── Digital Product Pipeline ─────────────────────────────────────────────
    "brand":     ("Brand Design Agent",       lambda: BrandDesignAgent()),
    "art":       ("Art Creation Agent",       lambda: ArtCreationAgent()),
    "planner":   ("Planner Design Agent",     lambda: PlannerDesignAgent()),
    "qc":        ("Quality Check Agent",      lambda: QualityCheckAgent()),
    "listing":   ("Etsy Listing Agent",       lambda: EtsyListingAgent()),
    "store":     ("Store Manager Agent",      lambda: StoreManagerAgent()),
    "delivery":  ("Sales Processor Agent",    lambda: SalesProcessorAgent()),

    # ── Shop Operations ──────────────────────────────────────────────────────
    "sales":     ("Sales Agent",              lambda: SalesAgent()),
    "product":   ("Product Agent",            lambda: ProductAgent()),
    "marketing": ("Marketing Agent",          lambda: MarketingAgent()),
    "analytics": ("Analytics Agent",          lambda: AnalyticsAgent()),
    "cs":        ("Customer Service Agent",   lambda: CustomerServiceAgent()),
    "social":    ("Social Media Agent",       lambda: SocialMediaAgent()),

    # ── Business Infrastructure ──────────────────────────────────────────────
    "finance":   ("Financial Agent",          lambda: FinancialAgent()),
    "print":     ("Print Production Agent",   lambda: PrintProductionAgent()),
    "ads":       ("Etsy Ads Agent",           lambda: EtsyAdsAgent()),
    "intel":     ("Competitor Intel Agent",   lambda: CompetitorIntelAgent()),
    "promos":    ("Promotions Agent",         lambda: PromotionsAgent()),
    "tax":       ("Tax Compliance Agent",     lambda: TaxComplianceAgent()),
    "returns":   ("Returns & Disputes Agent", lambda: ReturnsAgent()),
    "supply":    ("Supply Chain Agent",       lambda: SupplyChainAgent()),
    "email":     ("Email Marketing Agent",    lambda: EmailMarketingAgent()),
    "abt":       ("A/B Testing Agent",        lambda: ABTestingAgent()),
}

DAILY_BRIEFING_PROMPT = """Run a complete daily briefing for the shop owner. Delegate to all relevant agents:

DIGITAL PIPELINE:
1. Brand Design Agent — check if brand assets and guidelines are complete
2. Art Creation Agent — any new products in the pipeline?
3. Quality Check Agent — any files pending review?
4. Store Manager Agent — shop health: sold-out items, renewal alerts, listing performance

OPERATIONS:
5. Sales Processor Agent — any unfulfilled digital orders needing email delivery?
6. Sales Agent — today's revenue and pending physical orders
7. Customer Service Agent — unread messages and unresponded reviews
8. Returns & Disputes Agent — any open cases needing urgent response?
9. Analytics Agent — this week's traffic and top performers
10. Marketing Agent — one key marketing opportunity for today

INFRASTRUCTURE:
11. Supply Chain Agent — any materials running low?
12. Print Production Agent — print queue status and machine health

Synthesize everything into an executive daily briefing. Lead with the most urgent items first."""

HELP_TEXT = """
╔═════════════════════════════════════════════════════════════════════════╗
║            OnBrandCraftz — Etsy Agent Hub                               ║
╠═════════════════════════════════════════════════════════════════════════╣
║  COMMANDS                                                                ║
║  help          Show this help menu                                       ║
║  brief         Run daily briefing (all agents)                           ║
║  pipeline      Show digital product pipeline status                      ║
║  agent <name>  Switch to a specific agent                                ║
║  quit / exit   Exit the hub                                              ║
║                                                                          ║
║  AGENTS — Orchestrator                                                   ║
║  ceo           CEO Agent (orchestrates all 22 agents)                    ║
║                                                                          ║
║  AGENTS — Digital Product Pipeline                                       ║
║  brand         Brand Design Agent (logo, banner, brand identity)         ║
║  art           Art Creation Agent (wall art, clipart, illustrations)      ║
║  planner       Planner Design Agent (all digital planner categories)      ║
║  qc            Quality Check Agent (file review + approval)              ║
║  listing       Etsy Listing Agent (SEO + publish to Etsy)               ║
║  store         Store Manager Agent (shop health + announcements)         ║
║  delivery      Sales Processor Agent (email digital files)               ║
║                                                                          ║
║  AGENTS — Shop Operations                                                ║
║  sales         Sales Agent (physical orders, revenue, shipping)          ║
║  product       Product Agent (physical listings, inventory)              ║
║  marketing     Marketing Agent (SEO, promotions, traffic)                ║
║  analytics     Analytics Agent (reports, dashboard)                      ║
║  cs            Customer Service Agent (messages, reviews)                ║
║  social        Social Media Agent (Pinterest strategy)                   ║
║                                                                          ║
║  AGENTS — Business Infrastructure                                        ║
║  finance       Financial Agent (profit, fees, COGS, cash flow)          ║
║  print         Print Production Agent (print queue, machines, filament)  ║
║  ads           Etsy Ads Agent (budget, ROAS, promoted listings)          ║
║  intel         Competitor Intel Agent (research, gaps, trends)           ║
║  promos        Promotions Agent (sales events, coupons, discounts)       ║
║  tax           Tax Compliance Agent (taxes, deductions, copyright)       ║
║  returns       Returns & Disputes Agent (refunds, Etsy cases)            ║
║  supply        Supply Chain Agent (materials, suppliers, orders)         ║
║  email         Email Marketing Agent (newsletters, receipt messages)     ║
║  abt           A/B Testing Agent (listing experiments, CTR/conversion)   ║
╚═════════════════════════════════════════════════════════════════════════╝
"""

PIPELINE_PROMPT = """Check the complete digital product pipeline status. Ask:
1. Art Creation Agent: list all digital products and their statuses
2. Quality Check Agent: get QC summary (approved/rejected/pending counts)
3. Etsy Listing Agent: list digital listings showing which are live vs pending
4. Sales Processor Agent: any unfulfilled digital orders?

Give a clear pipeline report: what's in progress, what's blocked, what's ready to go live."""


def check_env() -> bool:
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY is not set.")
        print("Copy .env.example to .env and add your API key.")
        return False
    return True


def print_banner():
    print("\n" + "=" * 70)
    print("   OnBrandCraftz — Etsy Agent Hub")
    print("   Powered by Claude AI  |  22 Specialized Agents")
    print("=" * 70)
    print("Type 'help' for commands, 'brief' for daily briefing,")
    print("'pipeline' for digital product status, or ask anything.\n")


def run_agent(agent_name: str, agent_instance, interactive: bool = True):
    display_name, _ = AGENTS[agent_name]
    print(f"\n[{display_name}] Ready. Type your task or 'back' to return to CEO.\n")

    while interactive:
        try:
            user_input = input(f"{display_name}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in ("back", "exit", "quit"):
            break

        print(f"\nProcessing...\n")
        result = agent_instance.run(user_input)
        print(f"\n{result}\n")
        print("-" * 60)


def main():
    if not check_env():
        sys.exit(1)

    print_banner()

    ceo = CEOAgent()

    while True:
        try:
            user_input = input("Hub> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("quit", "exit"):
            print("Goodbye!")
            break

        if cmd == "help":
            print(HELP_TEXT)
            continue

        if cmd == "brief":
            print("\n[CEO] Running daily briefing — delegating to all agents...\n")
            result = ceo.run(DAILY_BRIEFING_PROMPT)
            print(f"\n{result}\n")
            print("=" * 60)
            continue

        if cmd == "pipeline":
            print("\n[CEO] Checking digital product pipeline...\n")
            result = ceo.run(PIPELINE_PROMPT)
            print(f"\n{result}\n")
            print("=" * 60)
            continue

        if cmd.startswith("agent "):
            target = cmd.split(" ", 1)[1].strip()
            if target not in AGENTS:
                print(f"Unknown agent '{target}'. Available: {', '.join(AGENTS.keys())}")
                continue
            _, factory = AGENTS[target]
            agent_instance = factory()
            run_agent(target, agent_instance)
            continue

        # Default: route to CEO
        print(f"\n[CEO] Processing...\n")
        result = ceo.run(user_input)
        print(f"\n{result}\n")
        print("-" * 60)


if __name__ == "__main__":
    main()
