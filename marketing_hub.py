#!/usr/bin/env python3
"""
Marketing Packages Hub
AI agent hub for managing small business marketing clients.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import ANTHROPIC_API_KEY
from agents.client_intake_agent import ClientIntakeAgent
from agents.copywriter_agent import CopywriterAgent
from agents.audit_agent import AuditAgent
from agents.seo_agent import SEOAgent
from agents.report_agent import ReportAgent
from agents.package_manager_agent import PackageManagerAgent

AGENTS = {
    "manager": ("Package Manager", PackageManagerAgent),
    "intake":  ("Client Intake Agent", ClientIntakeAgent),
    "copy":    ("Copywriter Agent", CopywriterAgent),
    "audit":   ("Audit Agent", AuditAgent),
    "seo":     ("SEO Agent", SEOAgent),
    "report":  ("Report Agent", ReportAgent),
}

HELP_TEXT = """
╔══════════════════════════════════════════════════════════════╗
║          Marketing Packages Hub                              ║
╠══════════════════════════════════════════════════════════════╣
║  COMMANDS                                                    ║
║  help           Show this help menu                          ║
║  clients        List all saved clients                       ║
║  agent <name>   Switch to a specific agent                   ║
║  quit / exit    Exit the hub                                 ║
║                                                              ║
║  AGENTS                                                      ║
║  manager  Package Manager — orchestrates full workflows      ║
║  intake   Client Intake Agent — onboard new clients          ║
║  audit    Audit Agent — digital presence gap analysis        ║
║  seo      SEO Agent — keyword research & local SEO           ║
║  copy     Copywriter Agent — social posts, newsletters, ads  ║
║  report   Report Agent — monthly/weekly client reports       ║
║                                                              ║
║  PACKAGES                                                    ║
║  starter  $299/mo  12 posts, 1 newsletter, audit, report     ║
║  growth   $599/mo  20 posts, 2 newsletters, SEO, report      ║
║  pro     $1,199/mo 30 posts, 4 newsletters, ads, weekly rpt  ║
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
    print("   Marketing Packages Hub")
    print("   Powered by Claude AI Agents")
    print("=" * 62)
    print("Type 'help' for commands, 'agent manager' to run a full workflow,")
    print("or 'agent intake' to onboard a new client.\n")


def list_clients_summary():
    import json
    clients_dir = os.path.join(os.path.dirname(__file__), "data", "clients")
    if not os.path.exists(clients_dir):
        print("No clients yet. Use 'agent intake' to onboard your first client.\n")
        return
    clients = []
    for fname in sorted(os.listdir(clients_dir)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(clients_dir, fname)) as f:
                data = json.load(f)
            clients.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    if not clients:
        print("No clients yet. Use 'agent intake' to onboard your first client.\n")
        return
    print(f"\n{'ID':<30} {'Business':<25} {'Package':<10} {'Location'}")
    print("-" * 80)
    for c in clients:
        print(f"{c.get('id',''):<30} {c.get('business_name',''):<25} {c.get('package',''):<10} {c.get('location','')}")
    print()


def run_agent(agent_name: str):
    display_name, AgentClass = AGENTS[agent_name]
    agent = AgentClass()
    print(f"\n[{display_name}] Ready. Type your request or 'back' to return to hub.\n")

    while True:
        try:
            user_input = input(f"{display_name}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in ("back", "exit", "quit"):
            break

        print("\nProcessing...\n")
        result = agent.run(user_input)
        print(f"\n{result}\n")
        print("-" * 60)


def main():
    if not check_env():
        sys.exit(1)

    print_banner()

    while True:
        try:
            user_input = input("Marketing Hub> ").strip()
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

        if cmd == "clients":
            list_clients_summary()
            continue

        if cmd.startswith("agent "):
            target = cmd.split(" ", 1)[1].strip()
            if target not in AGENTS:
                print(f"Unknown agent '{target}'. Available: {', '.join(AGENTS.keys())}")
                continue
            run_agent(target)
            continue

        print("Type 'help' for available commands.\n")


if __name__ == "__main__":
    main()
