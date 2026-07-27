#!/usr/bin/env python3
"""
tools/test_email_system.py

Email System Configuration & Verification Tool for Frank.

Tests SMTP configuration, verifies server connectivity, sends test emails,
and updates .env credentials.

Usage:
  python tools/test_email_system.py --user Printing3dthings@outlook.com --password "your_password"
  python tools/test_email_system.py --send-test
  python tools/test_email_system.py --status
"""

import os
import sys
import argparse
import smtplib
import ssl
from email.mime.text import MIMEText
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_env_path = _ROOT / ".env"


def load_env() -> dict:
    env_vars = {}
    if _env_path.exists():
        with open(_env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars


def update_env_file(key: str, value: str) -> None:
    if not _env_path.exists():
        _env_path.write_text(f"{key}={value}\n")
        return

    lines = _env_path.read_text().splitlines()
    found = False
    new_lines = []
    for line in lines:
        if line.strip() and not line.startswith("#") and "=" in line:
            k, _ = line.split("=", 1)
            if k.strip() == key:
                new_lines.append(f"{key}={value}")
                found = True
                continue
        new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={value}")

    _env_path.write_text("\n".join(new_lines) + "\n")


def infer_smtp_settings(email: str) -> tuple[str, int]:
    email_lower = email.lower()
    if "gmail" in email_lower:
        return "smtp.gmail.com", 587
    elif any(d in email_lower for d in ["outlook", "hotmail", "live", "office365"]):
        return "smtp-mail.outlook.com", 587
    elif "yahoo" in email_lower:
        return "smtp.mail.yahoo.com", 587
    return "smtp-mail.outlook.com", 587


def test_smtp_connection(host: str, port: int, user: str, password: str, recipient: str = "") -> tuple[bool, str]:
    if not user or not password:
        return False, "Missing SMTP username or password."

    recipient = recipient or user
    print(f"Connecting to {host}:{port} as {user}...", flush=True)

    try:
        if port == 465:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, timeout=15, context=ctx) as server:
                server.login(user, password)
                if recipient:
                    _send_sample_email(server, user, recipient)
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.login(user, password)
                if recipient:
                    _send_sample_email(server, user, recipient)

        return True, f"Successfully authenticated and sent test email to {recipient}!"
    except smtplib.SMTPAuthenticationError as exc:
        return False, (
            f"SMTP Authentication Failed: {exc}.\n"
            f"Tip: If using Outlook or Gmail, ensure 2-Factor Authentication is enabled "
            f"and you are using a generated 'App Password' instead of your main account password."
        )
    except Exception as exc:
        return False, f"SMTP Connection Failed: {exc}"


def _send_sample_email(server, sender: str, recipient: str):
    msg = MIMEText(
        "Hello Scott!\n\n"
        "This is a test notification from Frank Command Center.\n"
        "Your email system is now fully configured and functional!\n\n"
        "Frank will use this email connection for:\n"
        "  1. Daily Shop Briefs (6 AM UTC)\n"
        "  2. Urgent Order & Star Seller Alerts\n"
        "  3. Customer Follow-up Notifications\n\n"
        "— Frank 🤖",
        "plain",
        "utf-8"
    )
    msg["From"] = f"Frank AI <{sender}>"
    msg["To"] = recipient
    msg["Subject"] = "🤖 Frank Command Center — Email Test Successful!"
    server.send_message(msg)


def main():
    parser = argparse.ArgumentParser(description="Frank Email System Tester & Setup")
    parser.add_argument("--user", help="SMTP Username / Email address")
    parser.add_argument("--password", help="SMTP Password / App Password")
    parser.add_argument("--host", help="SMTP Host (auto-detected if omitted)")
    parser.add_argument("--port", type=int, help="SMTP Port (default 587)")
    parser.add_argument("--recipient", help="Recipient email address for test message")
    parser.add_argument("--send-test", action="store_true", help="Send a test email using saved credentials")
    parser.add_argument("--status", action="store_true", help="Show current SMTP config status")
    args = parser.parse_args()

    env = load_env()

    if args.status:
        user = env.get("SMTP_USER", "")
        host = env.get("SMTP_HOST", "smtp-mail.outlook.com")
        port = env.get("SMTP_PORT", "587")
        pass_set = bool(env.get("SMTP_PASSWORD"))
        print("\n============================================================")
        print(" Frank Email System Configuration Status")
        print("============================================================")
        print(f"  SMTP User     : {user if user else '(Not Configured)'}")
        print(f"  SMTP Host     : {host}")
        print(f"  SMTP Port     : {port}")
        print(f"  Password Set  : {'✓ YES' if pass_set else '✗ NO'}")
        print("============================================================\n")
        return

    user = args.user or os.getenv("SMTP_USER", "")
    password = args.password or os.getenv("SMTP_PASSWORD", "")
    recipient = args.recipient or user or "Printing3dthings@outlook.com"

    if not user or not password:
        print("\n[EMAIL SETUP] ⚠️ Missing credentials.")
        print("Usage to set up email:")
        print("  python tools/test_email_system.py --user Printing3dthings@outlook.com --password \"your_app_password\"\n")
        return

    host = args.host or env.get("SMTP_HOST")
    port = args.port or (int(env.get("SMTP_PORT")) if env.get("SMTP_PORT") else None)

    if not host or not port:
        inferred_host, inferred_port = infer_smtp_settings(user)
        host = host or inferred_host
        port = port or inferred_port

    success, msg = test_smtp_connection(host, port, user, password, recipient=recipient)

    print("\n" + ("✓ " if success else "✗ ") + msg + "\n")

    if success:
        update_env_file("SMTP_HOST", host)
        update_env_file("SMTP_PORT", str(port))
        update_env_file("SMTP_USER", user)
        update_env_file("SMTP_PASSWORD", password)
        print(f"[EMAIL SETUP] Updated .env with verified credentials for {user}!")


if __name__ == "__main__":
    main()
