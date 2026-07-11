"""
Cross-platform onboarding wizard for a fresh, self-hosted instance of this
framework — replaces the old Windows-only SETUP.bat / *.bat scripts (and
their unsafe `echo >> .env` pattern) with one interactive script.

Usage:
    python tools/installer/setup_wizard.py

Stdlib only (secrets, getpass, subprocess, urllib) — no new dependencies,
consistent with the rest of tools/. Reuses the same manual `.env`
read-and-rewrite pattern already used identically in tools/etsy_oauth.py
and tools/pinterest_oauth.py.

This script never touches Scott's live .env unless someone explicitly runs
it against his checkout — it only operates on whatever .env lives next to
the repo root it's invoked from.
"""

import os
import sys
import getpass
import secrets
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE = os.path.join(REPO_ROOT, ".env")
ENV_EXAMPLE = os.path.join(REPO_ROOT, ".env.example")


def _update_env(key: str, value: str) -> None:
    """Upsert a key=value line in .env — same pattern as the *_oauth.py scripts."""
    lines = []
    found = False
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            lines = f.readlines()
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}\n")
    with open(ENV_FILE, "w") as f:
        f.writelines(lines)


def _read_env() -> dict:
    """Parse the current .env into a dict, ignoring comments/blank lines."""
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


def _subprocess_env() -> dict:
    """Merge the current .env's values into a copy of os.environ.

    pinterest_oauth.py reads PINTEREST_APP_ID/SECRET via plain os.getenv()
    and never loads .env into os.environ itself (unlike etsy_oauth.py,
    which does this at import time) — so a freshly spawned subprocess
    won't see values this wizard just wrote to .env unless we merge them
    in explicitly here.
    """
    merged = os.environ.copy()
    merged.update(_read_env())
    return merged


def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def _prompt_secret(label: str) -> str:
    """Prompt without echoing to the terminal; falls back to input() if not a tty."""
    try:
        if sys.stdin.isatty():
            return getpass.getpass(f"{label}: ").strip()
    except Exception:
        pass
    return input(f"{label} (input not hidden — not a tty): ").strip()


def _confirm(label: str, default: bool = False) -> bool:
    suffix = "Y/n" if default else "y/N"
    answer = input(f"{label} ({suffix}): ").strip().lower()
    if not answer:
        return default
    return answer.startswith("y")


def _run(cmd: list) -> int:
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=REPO_ROOT, env=_subprocess_env()).returncode


# ── Step 1: ensure .env exists ───────────────────────────────────────────────


def ensure_env_file():
    if os.path.exists(ENV_FILE):
        print(f"Found existing .env at {ENV_FILE} — will update it in place.")
        return
    if not os.path.exists(ENV_EXAMPLE):
        print(f"ERROR: {ENV_EXAMPLE} not found — cannot create .env.")
        sys.exit(1)
    with open(ENV_EXAMPLE) as src, open(ENV_FILE, "w") as dst:
        dst.write(src.read())
    print(f"Created .env from .env.example at {ENV_FILE}")


# ── Step 2: required vars ────────────────────────────────────────────────────


def configure_required():
    print("\n== Required setup ==================================================")

    _update_env("APP_SECRET_TOKEN", secrets.token_urlsafe(32))
    print("Generated a new APP_SECRET_TOKEN (dashboard/API auth) — saved to .env.")

    anthropic_key = _prompt_secret("Anthropic API key (ANTHROPIC_API_KEY)")
    if anthropic_key:
        _update_env("ANTHROPIC_API_KEY", anthropic_key)
    else:
        print("Skipped — you must set ANTHROPIC_API_KEY in .env before the agent can run.")

    business_name = _prompt("Business name", "Your Business Name")
    _update_env("BUSINESS_NAME", business_name)

    owner_name = _prompt("Your name (owner)", "Your Name")
    _update_env("OWNER_NAME", owner_name)

    agent_name = _prompt("What should the agent call itself?", "Frank")
    _update_env("AGENT_NAME", agent_name)

    business_description = _prompt(
        "Short description of what your business sells",
        "a short description of what your business sells",
    )
    _update_env("BUSINESS_DESCRIPTION", business_description)

    return {"configured": ["APP_SECRET_TOKEN (auto)", "ANTHROPIC_API_KEY" if anthropic_key else None,
                            "BUSINESS_NAME", "OWNER_NAME", "AGENT_NAME", "BUSINESS_DESCRIPTION"]}


# ── Step 3: optional integrations ────────────────────────────────────────────


def configure_etsy(summary):
    if not _confirm("\nSet up Etsy now? (listing creation, order management)"):
        summary["skipped"].append("Etsy")
        return
    keystring = _prompt_secret("Etsy keystring (from etsy.com/developers -> your app)")
    if not keystring:
        print("No keystring entered — skipping Etsy.")
        summary["skipped"].append("Etsy")
        return
    _update_env("ETSY_API_KEY", keystring)
    _update_env("ETSY_CLIENT_ID", keystring)  # same value, used in two roles
    shop_id = _prompt("Etsy shop ID")
    if shop_id:
        _update_env("ETSY_SHOP_ID", shop_id)
    client_secret = _prompt_secret("Etsy Shared Secret (ETSY_CLIENT_SECRET)")
    if client_secret:
        _update_env("ETSY_CLIENT_SECRET", client_secret)

    if client_secret and _confirm("Run the Etsy OAuth flow now?"):
        _run([sys.executable, os.path.join(REPO_ROOT, "tools", "etsy_oauth.py")])
        callback_url = _prompt("Paste the full callback URL here (after clicking Allow)")
        if callback_url:
            _run([sys.executable, os.path.join(REPO_ROOT, "tools", "etsy_oauth.py"),
                  "--exchange", callback_url])
    else:
        print("Skipped OAuth — run `python tools/etsy_oauth.py` later to authorize.")
    summary["configured"].append("Etsy")


def configure_openai(summary):
    if not _confirm("\nSet up OpenAI now? (AI art generation, logo creation)"):
        summary["skipped"].append("OpenAI")
        return
    key = _prompt_secret("OpenAI API key (OPENAI_API_KEY)")
    if key:
        _update_env("OPENAI_API_KEY", key)
        summary["configured"].append("OpenAI")
    else:
        summary["skipped"].append("OpenAI")


def configure_email(summary):
    if not _confirm("\nSet up email/digital delivery now? (emails files to customers)"):
        summary["skipped"].append("Email/SMTP")
        return
    host = _prompt("SMTP host", "smtp.gmail.com")
    _update_env("SMTP_HOST", host)
    port = _prompt("SMTP port", "587")
    _update_env("SMTP_PORT", port)
    user = _prompt("SMTP username (your email address)")
    if user:
        _update_env("SMTP_USER", user)
    print("Gmail users: enable 2FA, then create an App Password at myaccount.google.com/apppasswords")
    password = _prompt_secret("SMTP password (App Password, not your login password)")
    if password:
        _update_env("SMTP_PASSWORD", password)
    sender_name = _prompt("Sender display name", env_default_or(summary, "BUSINESS_NAME"))
    _update_env("SENDER_NAME", sender_name)
    summary["configured"].append("Email/SMTP")


def env_default_or(summary, key, fallback="Your Business Name"):
    return _read_env().get(key, fallback)


def configure_pinterest(summary):
    if not _confirm("\nSet up Pinterest now? (direct pin posting)"):
        summary["skipped"].append("Pinterest")
        return
    app_id = _prompt_secret("Pinterest App ID")
    app_secret = _prompt_secret("Pinterest App Secret")
    if not app_id or not app_secret:
        print("Missing App ID/Secret — skipping Pinterest.")
        summary["skipped"].append("Pinterest")
        return
    _update_env("PINTEREST_APP_ID", app_id)
    _update_env("PINTEREST_APP_SECRET", app_secret)

    if _confirm("Run the Pinterest OAuth flow now? (opens a local server and waits for you)"):
        _run([sys.executable, os.path.join(REPO_ROOT, "tools", "pinterest_oauth.py")])
    else:
        print("Skipped OAuth — run `python tools/pinterest_oauth.py` later to authorize.")
    summary["configured"].append("Pinterest")


def configure_meta(summary):
    if not _confirm("\nSet up Instagram / Facebook now? (photo/video posting)"):
        summary["skipped"].append("Instagram/Facebook")
        return
    print("Instagram and Facebook access tokens are obtained manually via the Meta")
    print("Graph API Explorer — there's no OAuth script to automate this step. See")
    print("the setup steps in tools/instagram_api.py and tools/facebook_api.py.")
    ig_app_id = _prompt("Instagram App ID (blank to skip Instagram)")
    if ig_app_id:
        _update_env("INSTAGRAM_APP_ID", ig_app_id)
        ig_app_secret = _prompt_secret("Instagram App Secret")
        if ig_app_secret:
            _update_env("INSTAGRAM_APP_SECRET", ig_app_secret)
        ig_user_id = _prompt("Instagram numeric user ID (leave blank if not known yet)")
        if ig_user_id:
            _update_env("INSTAGRAM_USER_ID", ig_user_id)
        print("Generate INSTAGRAM_ACCESS_TOKEN manually, then add it to .env directly.")
        summary["configured"].append("Instagram (app credentials only)")
    fb_page_id = _prompt("Facebook Page ID (blank to skip Facebook)")
    if fb_page_id:
        _update_env("FACEBOOK_PAGE_ID", fb_page_id)
        if ig_app_id:
            print("Reusing the Instagram App ID/Secret for Facebook (same Meta App).")
            _update_env("FACEBOOK_APP_ID", ig_app_id)
        else:
            fb_app_id = _prompt("Facebook App ID")
            if fb_app_id:
                _update_env("FACEBOOK_APP_ID", fb_app_id)
            fb_app_secret = _prompt_secret("Facebook App Secret")
            if fb_app_secret:
                _update_env("FACEBOOK_APP_SECRET", fb_app_secret)
        print("Generate FACEBOOK_PAGE_ACCESS_TOKEN manually, then add it to .env directly.")
        summary["configured"].append("Facebook (app credentials only)")
    if not ig_app_id and not fb_page_id:
        summary["skipped"].append("Instagram/Facebook")


# ── Step 4: summary ───────────────────────────────────────────────────────────


def print_summary(summary):
    print("\n== Setup summary ====================================================")
    print("Configured:")
    for item in summary["configured"]:
        if item:
            print(f"  - {item}")
    if summary["skipped"]:
        print("Skipped (can be configured later by re-running this wizard, or by")
        print("editing .env directly):")
        for item in summary["skipped"]:
            print(f"  - {item}")
    print("\nNext steps:")
    print("  - Run locally:  uvicorn tools.api_server.main:app --reload")
    print("  - Then open the printed local URL and log in with the dashboard token")
    print("    shown in .env under APP_SECRET_TOKEN")


def main():
    print("== Self-hosted setup wizard =========================================")
    ensure_env_file()
    summary = {"configured": [], "skipped": []}
    required = configure_required()
    summary["configured"].extend(x for x in required["configured"] if x)

    configure_etsy(summary)
    configure_openai(summary)
    configure_email(summary)
    configure_pinterest(summary)
    configure_meta(summary)

    print_summary(summary)


if __name__ == "__main__":
    main()
