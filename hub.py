#!/usr/bin/env python3
"""
OnBrandCraftz Agent Hub — Interactive Terminal
================================================
Starts the OnBrandCraftz Agent Hub in an interactive terminal session.
This is a local-only command that provides a conversational interface
to all shop automation tools.

The hub delegates to the API server's agent infrastructure when available,
or falls back to a simple interactive menu.

Usage:
  python hub.py              # start interactive hub
  python hub.py --status     # show agent status only
"""
import os, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
_env_path = ROOT / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())


AGENT_NAME = os.environ.get("AGENT_NAME", "Frank")
OWNER_NAME = os.environ.get("OWNER_NAME", "Scott")
BUSINESS_NAME = os.environ.get("BUSINESS_NAME", "OnBrandCraftz")

TOOLS = {
    "1": ("Shop Health Check", "python3 tools/shop_health_check.py"),
    "2": ("Analytics Dashboard", "python3 tools/analytics_tracker.py"),
    "3": ("Tag Audit & Fix", "python3 tools/audit_fix_wall_art_tags.py"),
    "4": ("Art Schedule Status", "python3 tools/post_scheduled_art.py --status"),
    "5": ("Post Next Art (Preview)", "python3 tools/post_scheduled_art.py --preview"),
    "6": ("Shorten All Titles", "python3 tools/shorten_titles.py --dry-run"),
    "7": ("AI Disclosure Check", "python3 tools/add_ai_disclosure.py --dry-run"),
    "8": ("Check for New Orders", "python3 tools/order_notifier.py"),
    "9": ("Pinterest Batch Post", "python3 tools/pinterest_batch_poster.py"),
    "10": ("Generate Sticker Sheet", "python3 tools/gen_sticker_sheet.py"),
}


def show_status():
    """Show current agent/shop status."""
    from datetime import datetime
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"

    print(f"\n{'━' * 55}")
    print(f"  {BUSINESS_NAME} Agent Hub — {AGENT_NAME}")
    print(f"  {greeting}, {OWNER_NAME}!")
    print(f"{'━' * 55}\n")

    # Check API keys
    keys = {
        "Anthropic": bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()
                          and "your_" not in os.environ.get("ANTHROPIC_API_KEY", "")),
        "OpenAI": bool(os.environ.get("OPENAI_API_KEY", "").strip()
                       and "your_" not in os.environ.get("OPENAI_API_KEY", "")),
        "Etsy API": bool(os.environ.get("ETSY_API_KEY", "").strip()
                         and "your_" not in os.environ.get("ETSY_API_KEY", "")),
        "Etsy OAuth": bool(os.environ.get("ETSY_ACCESS_TOKEN", "").strip()),
        "Pinterest": bool(os.environ.get("PINTEREST_ACCESS_TOKEN", "").strip()),
    }

    print("  API STATUS")
    for name, configured in keys.items():
        status = "✓ configured" if configured else "✗ not set"
        print(f"    {name:15s}: {status}")

    print(f"\n  ENVIRONMENT")
    print(f"    Mode: Local")
    print(f"    Agent: {AGENT_NAME}")
    print(f"    Business: {BUSINESS_NAME}")
    print()


def interactive_menu():
    """Run the interactive tool menu."""
    import subprocess

    show_status()

    print("  AVAILABLE TOOLS")
    for key, (label, _) in sorted(TOOLS.items(), key=lambda x: int(x[0])):
        print(f"    [{key:>2}] {label}")
    print(f"    [ q] Quit")
    print()

    while True:
        try:
            choice = input(f"  {AGENT_NAME} > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye! 👋")
            break

        if choice in ('q', 'quit', 'exit'):
            print(f"\n  {AGENT_NAME} signing off. See you later, {OWNER_NAME}! 👋")
            break

        if choice == 'help' or choice == '?':
            for key, (label, _) in sorted(TOOLS.items(), key=lambda x: int(x[0])):
                print(f"    [{key:>2}] {label}")
            print(f"    [ q] Quit")
            continue

        if choice == 'status':
            show_status()
            continue

        if choice in TOOLS:
            label, cmd = TOOLS[choice]
            print(f"\n  Running: {label}")
            print(f"  $ {cmd}\n")
            try:
                subprocess.run(cmd, shell=True, cwd=str(ROOT))
            except KeyboardInterrupt:
                print("\n  (interrupted)")
            print()
        else:
            print(f"  Unknown command. Type a number (1-{len(TOOLS)}) or 'q' to quit.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description=f"{BUSINESS_NAME} Agent Hub")
    parser.add_argument('--status', action='store_true', help='Show status only')
    args = parser.parse_args()

    if args.status:
        show_status()
    else:
        interactive_menu()


if __name__ == '__main__':
    main()
