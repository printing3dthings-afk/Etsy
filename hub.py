#!/usr/bin/env python3
"""
CraftedWithLove - Etsy Agent Hub
Central command interface for managing your Etsy shop via AI agents.
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from config import ANTHROPIC_API_KEY
from agents import CEOAgent, SalesAgent, ProductAgent, MarketingAgent, AnalyticsAgent, CustomerServiceAgent, SocialMediaAgent

AGENTS = {
    "ceo": ("CEO Agent", lambda: CEOAgent()),
    "sales": ("Sales Agent", lambda: SalesAgent()),
    "product": ("Product Agent", lambda: ProductAgent()),
    "marketing": ("Marketing Agent", lambda: MarketingAgent()),
    "analytics": ("Analytics Agent", lambda: AnalyticsAgent()),
    "cs": ("Customer Service Agent", lambda: CustomerServiceAgent()),
    "social": ("Social Media Agent", lambda: SocialMediaAgent()),
}

DAILY_BRIEFING_PROMPT = """Run a complete daily briefing for the shop owner. Delegate to all relevant agents to cover:
1. Today's revenue and pending orders (Sales Agent)
2. Any low stock or inventory alerts (Product Agent)
3. Unread customer messages and unresponded reviews (Customer Service Agent)
4. This week's traffic and top-performing listings (Analytics Agent)
5. One key marketing opportunity for today (Marketing Agent)

Synthesize everything into an executive daily briefing. Lead with the most urgent items."""

HELP_TEXT = """
╔══════════════════════════════════════════════════════════════╗
║          CraftedWithLove — Etsy Agent Hub                    ║
╠══════════════════════════════════════════════════════════════╣
║  COMMANDS                                                    ║
║  help          Show this help menu                           ║
║  brief         Run daily briefing (all agents)              ║
║  agent <name>  Switch to a specific agent                    ║
║  quit / exit   Exit the hub                                  ║
║                                                              ║
║  AGENTS                                                      ║
║  ceo           CEO Agent (orchestrates all others)           ║
║  sales         Sales Agent (orders, revenue, shipping)       ║
║  product       Product Agent (listings, inventory)           ║
║  marketing     Marketing Agent (SEO, promotions, traffic)    ║
║  analytics     Analytics Agent (reports, dashboard)          ║
║  cs            Customer Service Agent (messages, reviews)    ║
║  social        Social Media Agent (Pinterest strategy)       ║
╚══════════════════════════════════════════════════════════════╝
"""


def check_env() -> bool:
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY is not set.")
        print("Copy .env.example to .env and add your API key.")
        return False
    return True


def print_banner():
    print("\n" + "=" * 62)
    print("   CraftedWithLove — Etsy Agent Hub")
    print("   Powered by Claude AI Agents")
    print("=" * 62)
    print("Type 'help' for commands, 'brief' for daily briefing,")
    print("or just ask anything about your shop.\n")


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
    current_agent_key = "ceo"
    current_agent = ceo

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

        if cmd.startswith("agent "):
            target = cmd.split(" ", 1)[1].strip()
            if target not in AGENTS:
                print(f"Unknown agent '{target}'. Available: {', '.join(AGENTS.keys())}")
                continue
            _, factory = AGENTS[target]
            agent_instance = factory()
            run_agent(target, agent_instance)
            continue

        # Default: route to current agent (CEO)
        print(f"\n[CEO] Processing...\n")
        result = current_agent.run(user_input)
        print(f"\n{result}\n")
        print("-" * 60)


if __name__ == "__main__":
    main()
