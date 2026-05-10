#!/usr/bin/env python3
import sys
import os

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


def check_env() -> bool:
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY is not set.")
        print("Copy .env.example to .env and add your API key.")
        return False
    return True


def main():
    if not check_env():
        sys.exit(1)

    print("\n" + "=" * 62)
    print("   OnBrandCraftz — Etsy Agent Hub")
    print("   Powered by Claude AI Agents")
    print("=" * 62)
    print("Type 'help' for commands, 'brief' for daily briefing,")
    print("or just ask anything about your shop.\n")

    ceo = CEOAgent()

    while True:
        try:
            user_input = input("Hub> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break
        if user_input.lower() == "brief":
            print("\n[CEO] Running daily briefing...\n")
            print(ceo.run(DAILY_BRIEFING_PROMPT))
            continue

        print("\n[CEO] Processing...\n")
        print(ceo.run(user_input))
        print("-" * 60)


if __name__ == "__main__":
    main()
