#!/usr/bin/env python3
"""
OnBrandCraftz Mobile API Server

FastAPI backend powering the mobile dashboard app. Read-only + streaming chat.

Start:
  pip install -r tools/api_server/requirements.txt
  uvicorn tools.api_server.main:app --host 0.0.0.0 --port 8000 --reload

Deploy to Railway / Render: set env vars + point start command to this file.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
import mimetypes
import os
import random
import re as _re
import secrets
import subprocess
import sys
import threading
import time
import uuid
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Request, Security, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

# Load .env before importing shop tools
_env = ROOT / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

import anthropic
import openai
import business_config
import db  # local persistence layer (tools/api_server/db.py)
import seasonal_keywords  # noqa: E402
import tax_compliance_tools  # noqa: E402
import etsy_api
from etsy_api import EtsyAPIClient, EtsyAPIError  # noqa: E402
from resilience import (  # noqa: E402
    classify_tool_exception,
    retry_with_backoff,
    TransientToolError,
    CircuitBreaker,
    CircuitBreakerOpenError,
)

# Shared breaker for every Anthropic call site -- main.py has no single chokepoint
# analogous to EtsyAPIClient._request(), so each of the ~7 call sites routes through
# _anthropic_create() below instead.
_anthropic_breaker = CircuitBreaker("anthropic_api", db_module=db)


def _anthropic_create(client: "anthropic.Anthropic", **kwargs):
    """Routes an Anthropic messages.create() call through the shared circuit
    breaker so a real outage shows up in /api/system/dependencies instead of
    always reporting closed/healthy. Trips only on genuine transient infra
    errors (connection failure, rate limit, 5xx) -- a 400/401/403 means
    Anthropic responded and our request or key was the problem, not a
    dependency-health signal."""
    if not _anthropic_breaker.allow_request():
        raise CircuitBreakerOpenError(
            "circuit breaker 'anthropic_api' is open -- skipping call until cooldown elapses"
        )
    try:
        result = client.messages.create(**kwargs)
    except (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.InternalServerError):
        _anthropic_breaker.record_failure()
        raise
    else:
        _anthropic_breaker.record_success()
        return result


def _reconcile_etsy_tokens() -> None:
    """Restore a rotated Etsy token from the durable /data DB if the env var is stale.

    Railway re-injects whatever ETSY_ACCESS_TOKEN/ETSY_REFRESH_TOKEN it has stored on
    every restart. But Etsy rotates the refresh token on every use and invalidates the
    old one — so if this server refreshed the token before a restart, the env var is
    now a dead token and the next refresh 401s with invalid_grant (diagnosed 2026-06-17,
    see ops_runbook.md). _token_sync_loop() below persists each rotation to the /data
    SQLite volume, which survives restarts; this function runs once at boot and prefers
    that row — but only when it's provably a forward rotation of the *current* env
    token (matched via parent_refresh_token lineage), so a genuine manual
    re-authorization (tools/etsy_oauth.py + a fresh dashboard update) always wins over
    a stale DB row left over from before that re-auth.
    """
    env_refresh = os.getenv("ETSY_REFRESH_TOKEN", "").strip()
    try:
        stored = db.get_etsy_tokens()
    except Exception as exc:
        print(f"[etsy-tokens] reconcile skipped: {exc}", flush=True)
        return
    if not stored:
        return
    if env_refresh and env_refresh not in (stored.get("refresh_token"), stored.get("parent_refresh_token")):
        print("[etsy-tokens] env refresh token doesn't match stored lineage — "
              "treating env as a fresh re-authorization, leaving it in place", flush=True)
        return
    if stored.get("access_token") and stored.get("refresh_token"):
        os.environ["ETSY_ACCESS_TOKEN"] = stored["access_token"]
        os.environ["ETSY_REFRESH_TOKEN"] = stored["refresh_token"]
        print(f"[etsy-tokens] restored rotated token from {db.DB_PATH} (persistent={db.is_persistent()})", flush=True)


_reconcile_etsy_tokens()
db.ensure_default_sandbox_folder()

# ── Executable command registry (CEO agent can invoke these) ───────────────────
_EXEC_COMMANDS: dict[str, dict] = {
    "shop_health_check": {
        "script": "tools/shop_health_check.py",
        "description": "Run a live shop health snapshot — metrics, listing quality, tag audit",
        "timeout": 150,  # measured ~118s against the full live catalog on 2026-06-18; 60s always timed out
        "long_running": False,
    },
    "generate_coloring_pages": {
        "script": "tools/generate_coloring_pages.py",
        "description": "Generate all 20 kawaii coloring pages via gpt-image-1 (takes ~15 min)",
        "timeout": 30,
        "long_running": True,
    },
    "generate_coloring_pages_preview": {
        "script": "tools/generate_coloring_pages.py",
        "args": ["--preview"],
        "description": "Preview coloring page listing JSON — no API calls, instant",
        "timeout": 30,
        "long_running": False,
    },
    "generate_coloring_pages_quick": {
        "script": "tools/generate_coloring_pages.py",
        "args": ["--themes", "3"],
        "description": "Generate first 3 coloring page themes only (~3 min)",
        "timeout": 30,
        "long_running": True,
    },
    # rebuild_sticker_pack.py removed from this registry on 2026-06-18 — it
    # DELETEs the live digital file, uploads a replacement, and PATCHes the
    # listing description directly against the Etsy API with no stage_action
    # approval step. That's a direct bypass of Scott's one-tap approval gate
    # and a violation of the autonomy boundaries in CLAUDE.md. It also requires
    # three CLI args (--pid/--sheets/--listing) with no safe defaults, so it
    # could never have completed via this zero-arg invocation anyway. Do not
    # re-add without first refactoring it to stage_action() instead of writing
    # directly.
    "qc_sweep": {
        "script": "tools/qc_sweep.py",
        "description": "Run quality-control sweep across all product files",
        "timeout": 90,
        "long_running": False,
    },
    "listing_integrity_check": {
        "script": "tools/listing_integrity_check.py",
        "description": (
            "Audit every live listing for truthfulness/quality violations "
            "(titles >70 chars, quantity-claim mismatches where a 'Set of N' "
            "title doesn't match the delivered files, etc.). Fast read-only mode. "
            "This is the check that surfaces 'something that needs fixing' — run it "
            f"first, then stage_action the corrections for {business_config.OWNER_NAME}'s approval."
        ),
        "timeout": 330,  # measured ~281.8s against the full live catalog on 2026-06-18; 180s always timed out
        "long_running": False,
    },
    # CLAUDE.md "Fully Autonomous" list explicitly grants "Run seasonal keyword
    # reports and dry-run previews" -- neither of these two writes to Etsy.
    # Pushing the swap for real (--push) stays gated: it's not in either args
    # list below, and _FORBIDDEN_EXEC_FLAGS already refuses it if ever passed
    # as extra_args, so the only path to actually changing a listing's tags
    # is Scott approving a stage_action in the Action Center.
    "seasonal_keywords_report": {
        "script": "tools/seasonal_keywords.py",
        "description": "Show which listings have an upcoming/overdue seasonal keyword swap (read-only)",
        "timeout": 60,
        "long_running": False,
    },
    "seasonal_keywords_preview": {
        "script": "tools/seasonal_keywords.py",
        "args": ["--dry-run"],
        "description": "Preview exactly which tags would be swapped on which listings, without applying anything",
        "timeout": 60,
        "long_running": False,
    },
    # requires_approval=True: this is the one Workflows-screen command that writes
    # a new file (a backup ZIP) rather than just reporting. It can't mutate Etsy or
    # destroy anything live, but it still routes through the run_script staged-action
    # type so that path gets exercised for real before any higher-risk script is
    # ever added to it (see _SCRIPT_STAGED_ACTION_TYPES below).
    "backup_digital_products": {
        "script": "tools/backup_digital_products.py",
        "args": ["--no-sync"],
        "description": "Create a timestamped ZIP backup of digital_products/ (local only, no Etsy mutation)",
        "timeout": 120,
        "long_running": False,
        "requires_approval": True,
    },
}

# Sidecar persistence for commands registered at runtime via the register_command
# chat tool (Phase 2 M3) — _EXEC_COMMANDS above is a static in-memory dict that
# would forget any approved registration on restart, so approved entries are also
# written here and reloaded on every startup. Git-tracked plain JSON, same
# "nothing we delete should be unrecoverable" spirit as data/trash/.
_REGISTERED_COMMANDS_FILE = ROOT / "data" / "registered_commands.json"


def _load_registered_commands() -> None:
    if not _REGISTERED_COMMANDS_FILE.is_file():
        return
    try:
        entries = json.loads(_REGISTERED_COMMANDS_FILE.read_text())
    except Exception as exc:
        print(f"[register_command] failed to load {_REGISTERED_COMMANDS_FILE}: {exc}", flush=True)
        return
    for name, cfg in entries.items():
        cfg = dict(cfg)
        cfg["requires_approval"] = True  # hardcoded regardless of what the sidecar says
        _EXEC_COMMANDS[name] = cfg


_load_registered_commands()

# extra_args that would let a direct command run mutate live Etsy data bypass the
# approval gate Scott requires. Frank stages listing edits for one-tap approval;
# he must never push them straight through via a CLI flag (and neither can a
# prompt-injected instruction). Any extra_arg containing one of these is refused.
_FORBIDDEN_EXEC_FLAGS = ("--fix", "--push", "--publish", "--apply", "--activate", "--delete", "--write")

# Local relay command registry for the local_exec tool — runs on Scott's own
# machine via the relay, not in this Railway container, so it is a separate
# registry from _EXEC_COMMANDS above (different filesystem entirely). Step 1
# scope is read-only diagnostics only (Scott's locked-in decision) — real
# mutating commands are not added until the approval gate has been proven
# safe over time. The relay re-validates against its own copy of this same
# whitelist before calling subprocess — this list is advisory until the relay
# agrees (see frank_relay.py).
_LOCAL_EXEC_COMMANDS: dict[str, str] = {
    "dir_listing": "List the contents of a directory on Scott's machine (read-only)",
    "disk_usage": "Report free/used disk space on Scott's machine (read-only)",
}
_LOCAL_FORBIDDEN_EXEC_FLAGS = ("--fix", "--push", "--publish", "--apply", "--activate", "--delete", "--write", "&&", "|", ";", ">", "<")

# .strip() is critical: Railway env vars set via the dashboard often carry a
# trailing newline. APP_TOKEN is injected into an inline JS string literal
# (const TOKEN = '...'); a newline inside it is a fatal SyntaxError that kills
# the ENTIRE dashboard script — the page renders but no JS runs (frozen spinner).
APP_TOKEN = os.getenv("APP_SECRET_TOKEN", "").strip()
if not APP_TOKEN:
    raise RuntimeError("APP_SECRET_TOKEN is not set — refusing to start with no auth token.")
# If FRANK_USERNAME + FRANK_PASSWORD are both explicitly set in the environment,
# the owner account is seeded automatically at startup (headless / env-controlled
# deployments). Otherwise the table stays empty and the first visitor to /login
# is shown a one-time "Create Your Account" setup screen.
_FRANK_USERNAME_EXPLICIT = os.getenv("FRANK_USERNAME", "").strip().lower()
_FRANK_PASSWORD_EXPLICIT = os.getenv("FRANK_PASSWORD", "").strip()


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return f"{salt}${dk.hex()}"


def _verify_password(stored_hash: str, password: str) -> bool:
    try:
        salt, dk_hex = stored_hash.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
        return secrets.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


def _seed_owner_if_empty() -> None:
    """Seed owner account only when both env vars are explicitly configured."""
    if not (_FRANK_USERNAME_EXPLICIT and _FRANK_PASSWORD_EXPLICIT):
        return
    try:
        if db.hub_users_empty():
            db.create_hub_user(_FRANK_USERNAME_EXPLICIT, _hash_password(_FRANK_PASSWORD_EXPLICIT), role="owner")
            print(f"[auth] seeded owner account '{_FRANK_USERNAME_EXPLICIT}'", flush=True)
    except Exception as exc:
        print(f"[auth] seed failed: {exc}", flush=True)


_seed_owner_if_empty()

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
_SERVER_START = datetime.now(timezone.utc)
_BUILD_ID = "b4d0e2c-v81"  # bump on each deploy to confirm Railway is using latest code

print(f"[startup] BUILD={_BUILD_ID} PORT={os.getenv('PORT','?')} TOKEN_SET={bool(os.getenv('APP_SECRET_TOKEN'))} ETSY_TOKEN={bool(os.getenv('ETSY_ACCESS_TOKEN'))} ETSY_REFRESH={bool(os.getenv('ETSY_REFRESH_TOKEN'))} ANTHROPIC={bool(ANTHROPIC_KEY)} OPENAI={bool(OPENAI_KEY)}", flush=True)

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(title=f"{business_config.BUSINESS_NAME} Mobile API", version="1.0.0", docs_url=None, redoc_url=None)

# allow_origins=["*"] + allow_credentials=True is actually a no-op/invalid combo per the
# CORS spec for credentialed requests (browsers refuse to honor "*" once credentials are
# involved) — so this also fixes correctness, not just exposure. Native app traffic sends
# no browser Origin header at all, so tightening this list cannot break the mobile app.
# The only legitimate cross-origin caller is the web UI itself (same-origin, BASE = location.origin).
_RAILWAY_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
_CORS_ALLOWED_ORIGINS = [
    o for o in (
        f"https://{_RAILWAY_DOMAIN}" if _RAILWAY_DOMAIN else None,
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:19006",
    )
    if o
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def _security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # 'unsafe-inline' is required because _WEB_UI / frank_hud_mockup.py are single embedded
    # HTML strings full of inline <script>/style= — a nonce-based strict CSP would require
    # extracting all inline JS/CSS to separate files first, which is a larger follow-up,
    # out of scope here. Even with 'unsafe-inline' this still blocks third-party
    # script/iframe injection, clickjacking, and MIME-sniffing — real wins over zero headers.
    # 'wasm-unsafe-eval' is required for the offline voice engines (Transformers.js/Whisper,
    # Piper-web TTS) — WebAssembly.compile()/instantiate() is blocked by CSP without it, even
    # though plain script loading and fetch() already worked under script-src 'self'.
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
        "connect-src 'self' wss: https:; frame-ancestors 'none'; object-src 'none'"
    )
    return response

# Serve PWA icons (pre-generated files committed to the repo — no runtime PIL).
_STATIC_DIR = Path(__file__).parent / "static"

# privacy.html is a plain static file with no templating layer, but its OAuth-app
# privacy-policy URL (registered with Pinterest/Etsy as /static/privacy.html — the path
# must stay stable) needs business-identity substitution. Registered before the mount
# below so this explicit route wins for this one path; every other /static/* file is
# still served raw by the mount.
_PRIVACY_HTML_PATH = _STATIC_DIR / "privacy.html"


@app.get("/static/privacy.html", response_class=HTMLResponse)
def privacy_policy():
    html = _PRIVACY_HTML_PATH.read_text(encoding="utf-8")
    shop_id = os.getenv("ETSY_SHOP_ID", "onbrandcraftz")
    html = html.replace("onbrandcraftz", shop_id)
    html = html.replace("OnBrandCraftz", business_config.BUSINESS_NAME)
    return HTMLResponse(content=html)


if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

security = HTTPBearer()


def _auth(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    if credentials.credentials != APP_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials


# ── Page login gate ─────────────────────────────────────────────────────────────
#
# /api/* and /ws/* stay protected by the bearer/query APP_TOKEN exactly as before.
# But GET / and GET /frank used to serve their full page (which embeds that same
# APP_TOKEN in the JS) to anyone, no auth at all — so the "API auth" above was
# theater for anyone who could just load the page. This adds a passphrase login
# (checked against the same APP_TOKEN — nothing new for Scott to manage) gating
# those two page routes, backed by an in-memory session + login-attempt store.
# Deliberately in-memory only (same tradeoff as _relay_pending below) — a redeploy
# clears sessions and Scott logs in again; no DB table needed for one operator.

_sessions: dict[str, tuple[float, str]] = {}  # session_id -> (expiry, username)
_sessions_lock = threading.Lock()
SESSION_TTL = 60 * 60 * 24 * 30          # 30 days

_login_fails: dict[str, list[float]] = {}  # ip -> recent failure timestamps
_login_fails_lock = threading.Lock()
LOGIN_MAX_FAILS = 5
LOGIN_WINDOW = 15 * 60                    # 15 minutes

SESSION_COOKIE = "frank_session"

# ── WS handshake tickets ────────────────────────────────────────────────────────
#
# Browser/React-Native WebSocket clients can't set a custom Authorization header on
# the handshake — the query string is the only channel available — so embedding the
# long-lived APP_TOKEN there leaks it into page source, browser history, and server
# access logs. Instead, an authenticated REST call mints a short-lived, single-use
# ticket that's spent immediately on the WS connect and then deleted.
_ws_tickets: dict[str, float] = {}      # ticket -> expiry (epoch seconds)
_ws_tickets_lock = threading.Lock()
_WS_TICKET_TTL = 60                      # seconds


def _new_ws_ticket() -> str:
    ticket = secrets.token_urlsafe(32)
    with _ws_tickets_lock:
        _ws_tickets[ticket] = time.time() + _WS_TICKET_TTL
    return ticket


def _consume_ws_ticket(ticket: str) -> bool:
    """Single-use: returns True and deletes the ticket iff it exists and hasn't expired."""
    with _ws_tickets_lock:
        expiry = _ws_tickets.pop(ticket, None)
    return expiry is not None and time.time() <= expiry


def _new_session(username: str) -> str:
    sid = secrets.token_urlsafe(32)
    with _sessions_lock:
        _sessions[sid] = (time.time() + SESSION_TTL, username)
    return sid


def _check_session(request: Request) -> bool:
    sid = request.cookies.get(SESSION_COOKIE, "")
    if not sid:
        return False
    with _sessions_lock:
        entry = _sessions.get(sid)
        if entry is None:
            return False
        expiry, _ = entry
        if time.time() > expiry:
            del _sessions[sid]
            return False
    return True


def _get_session_user(request: Request) -> str:
    sid = request.cookies.get(SESSION_COOKIE, "")
    if not sid:
        return ""
    with _sessions_lock:
        entry = _sessions.get(sid)
        if entry is None:
            return ""
        expiry, username = entry
        if time.time() > expiry:
            del _sessions[sid]
            return ""
    return username


def _clear_session(request: Request) -> None:
    sid = request.cookies.get(SESSION_COOKIE, "")
    if sid:
        with _sessions_lock:
            _sessions.pop(sid, None)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _login_rate_limited(ip: str) -> bool:
    with _login_fails_lock:
        fails = [t for t in _login_fails.get(ip, []) if time.time() - t < LOGIN_WINDOW]
        _login_fails[ip] = fails
        return len(fails) >= LOGIN_MAX_FAILS


def _record_login_fail(ip: str) -> None:
    with _login_fails_lock:
        _login_fails.setdefault(ip, []).append(time.time())


def _reset_login_fails(ip: str) -> None:
    with _login_fails_lock:
        _login_fails.pop(ip, None)


_LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{hub_title} — Sign in</title>
<style>
  *{{box-sizing:border-box}}
  body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:#0b0f14;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
  .box{{width:340px;padding:36px 32px 28px;background:#121821;border:1px solid #1f2a36;border-radius:14px;box-shadow:0 8px 32px rgba(0,0,0,.5)}}
  .logo{{display:flex;align-items:center;gap:10px;margin-bottom:20px}}
  .logo-dot{{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#2ec4c4,#1a8f8f);display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;font-weight:700;flex-shrink:0}}
  .logo-text{{font-size:17px;font-weight:600;color:#e8eef3}}
  .logo-sub{{font-size:12px;color:#5a6a78;margin-top:1px}}
  label{{display:block;font-size:11px;font-weight:600;color:#5a6a78;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px}}
  input[type=text],input[type=password]{{width:100%;padding:10px 12px;margin-bottom:16px;
    background:#0b0f14;border:1px solid #2a3744;border-radius:8px;color:#e8eef3;font-size:14px;outline:none;transition:border .15s}}
  input[type=text]:focus,input[type=password]:focus{{border-color:#2ec4c4}}
  button{{width:100%;padding:11px;background:#2ec4c4;border:none;border-radius:8px;
    color:#06222a;font-weight:700;font-size:14px;cursor:pointer;letter-spacing:.03em;margin-top:4px;transition:background .15s}}
  button:hover{{background:#38d8d8}}
  .err{{background:#1c0f0f;border:1px solid #4a1c1c;border-radius:7px;color:#ff8080;font-size:12px;padding:8px 10px;margin-bottom:14px}}
</style>
</head>
<body>
  <div class="box">
    <div class="logo">
      <div class="logo-dot">F</div>
      <div><div class="logo-text">{hub_title}</div><div class="logo-sub">Operations Hub</div></div>
    </div>
    {error_html}
    <form method="post" action="/login" autocomplete="on">
      <input type="hidden" name="next" value="{next_path}">
      <label for="li-user">Username</label>
      <input type="text" id="li-user" name="username" placeholder="Enter your username" autofocus autocomplete="username">
      <label for="li-pass">Password</label>
      <input type="password" id="li-pass" name="password" placeholder="Enter your password" autocomplete="current-password">
      <button type="submit">Sign in</button>
    </form>
  </div>
</body>
</html>"""

# Served on /login when the hub_users table is empty (first-ever startup).
# The owner creates their own credentials — no defaults, no env-var guessing.
_SETUP_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{hub_title} — Create your account</title>
<style>
  *{{box-sizing:border-box}}
  body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:#0b0f14;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
  .box{{width:360px;padding:36px 32px 28px;background:#121821;border:1px solid #1f2a36;border-radius:14px;box-shadow:0 8px 32px rgba(0,0,0,.5)}}
  .logo{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
  .logo-dot{{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#2ec4c4,#1a8f8f);display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;font-weight:700;flex-shrink:0}}
  .logo-text{{font-size:17px;font-weight:600;color:#e8eef3}}
  .logo-sub{{font-size:12px;color:#5a6a78;margin-top:1px}}
  .setup-heading{{font-size:15px;font-weight:700;color:#e8eef3;margin:18px 0 4px}}
  .setup-hint{{font-size:11px;color:#5a6a78;margin-bottom:18px;line-height:1.5}}
  label{{display:block;font-size:11px;font-weight:600;color:#5a6a78;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px}}
  input[type=text],input[type=password]{{width:100%;padding:10px 12px;margin-bottom:16px;
    background:#0b0f14;border:1px solid #2a3744;border-radius:8px;color:#e8eef3;font-size:14px;outline:none;transition:border .15s}}
  input[type=text]:focus,input[type=password]:focus{{border-color:#2ec4c4}}
  button{{width:100%;padding:11px;background:#2ec4c4;border:none;border-radius:8px;
    color:#06222a;font-weight:700;font-size:14px;cursor:pointer;letter-spacing:.03em;margin-top:4px;transition:background .15s}}
  button:hover{{background:#38d8d8}}
  .err{{background:#1c0f0f;border:1px solid #4a1c1c;border-radius:7px;color:#ff8080;font-size:12px;padding:8px 10px;margin-bottom:14px}}
  .once{{font-size:10px;color:#3a4a56;margin-top:14px;text-align:center}}
</style>
</head>
<body>
  <div class="box">
    <div class="logo">
      <div class="logo-dot">F</div>
      <div><div class="logo-text">{hub_title}</div><div class="logo-sub">Operations Hub</div></div>
    </div>
    <div class="setup-heading">Create your account</div>
    <div class="setup-hint">First-time setup — choose a username and password for the owner account. You won't see this screen again.</div>
    {error_html}
    <form method="post" action="/login" autocomplete="off">
      <input type="hidden" name="next" value="{next_path}">
      <input type="hidden" name="setup_mode" value="1">
      <label for="su-user">Username</label>
      <input type="text" id="su-user" name="username" placeholder="e.g. scott" autofocus autocomplete="off" required>
      <label for="su-pass">Password</label>
      <input type="password" id="su-pass" name="password" placeholder="Choose a strong password" autocomplete="new-password" required>
      <label for="su-conf">Confirm password</label>
      <input type="password" id="su-conf" name="confirm_password" placeholder="Repeat your password" autocomplete="new-password" required>
      <button type="submit">Create account &amp; sign in</button>
    </form>
    <div class="once">This is a one-time setup. After this, use your username and password to sign in.</div>
  </div>
</body>
</html>"""


def _safe_next(next_path: str) -> str:
    # Only allow same-site relative paths — never redirect off-site via the next param.
    if next_path and next_path.startswith("/") and not next_path.startswith("//"):
        return next_path
    return "/"


@app.get("/login", response_class=HTMLResponse)
def login_page(next: str = "/", error: str = ""):
    safe_next = _safe_next(next)
    no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate"}
    if db.hub_users_empty():
        error_html = f'<div class="err">{error}</div>' if error else ""
        return HTMLResponse(
            _SETUP_PAGE.format(error_html=error_html, next_path=safe_next, hub_title=business_config.BUSINESS_NAME),
            headers=no_cache,
        )
    error_html = '<div class="err">Incorrect username or password. Try again.</div>' if error else ""
    return HTMLResponse(
        _LOGIN_PAGE.format(error_html=error_html, next_path=safe_next, hub_title=business_config.BUSINESS_NAME),
        headers=no_cache,
    )


@app.post("/login")
def login_submit(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    confirm_password: str = Form(""),
    setup_mode: str = Form(""),
    next: str = Form("/"),
):
    ip = _client_ip(request)
    safe_next = _safe_next(next)

    # ── First-run setup: create the owner account ──────────────────────────
    if setup_mode == "1" or db.hub_users_empty():
        uname = username.strip().lower()
        pw = password.strip()
        cpw = confirm_password.strip()
        if not uname or not pw:
            return RedirectResponse(f"/login?error=Username+and+password+are+required&next={safe_next}", status_code=303)
        if pw != cpw:
            return RedirectResponse(f"/login?error=Passwords+do+not+match&next={safe_next}", status_code=303)
        if len(pw) < 8:
            return RedirectResponse(f"/login?error=Password+must+be+at+least+8+characters&next={safe_next}", status_code=303)
        if not db.hub_users_empty():
            # Table was populated between GET and POST (race) — fall through to normal login
            pass
        else:
            db.create_hub_user(uname, _hash_password(pw), role="owner")
            print(f"[auth] owner account created: '{uname}'", flush=True)
            sid = _new_session(uname)
            resp = RedirectResponse(safe_next, status_code=303)
            resp.set_cookie(SESSION_COOKIE, sid, httponly=True, secure=True, samesite="lax")
            return resp

    # ── Normal login ────────────────────────────────────────────────────────
    if _login_rate_limited(ip):
        return Response(content="Too many failed attempts. Try again in a few minutes.", status_code=429)
    uname = username.strip().lower()
    user_row = db.get_hub_user(uname)
    if user_row and _verify_password(user_row["pw_hash"], password.strip()):
        _reset_login_fails(ip)
        sid = _new_session(uname)
        resp = RedirectResponse(safe_next, status_code=303)
        resp.set_cookie(SESSION_COOKIE, sid, httponly=True, secure=True, samesite="lax")
        return resp
    _record_login_fail(ip)
    return RedirectResponse(f"/login?error=1&next={safe_next}", status_code=303)


@app.get("/logout")
def logout(request: Request):
    _clear_session(request)
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@app.post("/logout")
def logout_post(request: Request):
    _clear_session(request)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(SESSION_COOKIE)
    return resp


def _price_float(price_field) -> float:
    """Normalize Etsy price field (dict or raw float) to Python float."""
    if isinstance(price_field, dict):
        divisor = price_field.get("divisor", 100) or 100
        return price_field.get("amount", 0) / divisor
    try:
        return float(price_field)
    except (TypeError, ValueError):
        return 0.0


# ── In-process cache ───────────────────────────────────────────────────────────

_cache: dict = {}
_cache_lock = threading.Lock()

# How long the CEO diagnostic stays fresh. Shop data (listings, tags, sales)
# changes slowly, so a 4-hour-old report is fine — and a background loop re-warms
# it before it expires so the dashboard practically never hits the ~60s synthesis.
_SUGGESTIONS_TTL = 14400


def _cache_get(key: str, ttl: int = 60):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and time.time() - entry["ts"] < ttl:
            return entry["data"]
    return None


def _cache_set(key: str, data) -> None:
    with _cache_lock:
        _cache[key] = {"data": data, "ts": time.time()}


# ── Local Relay connection registry (Frank's hands/ears on Scott's machine) ─────
#
# The relay is a separate small process on Scott's own computer that holds open
# a /ws/relay WebSocket and executes local_* tool calls Frank requests during a
# /ws/chat conversation. One relay connects at a time — a second connect just
# replaces the registered reference below, no multi-relay routing needed.
# Requests are correlated to responses by reusing Anthropic's own tool_use_id
# (or a fresh uuid for non-tool calls) as the request id, via the pending dict.

_relay_ws: "WebSocket | None" = None
_relay_lock = threading.Lock()
_relay_pending: dict[str, "asyncio.Future"] = {}

# Instant, ungated AGENT_TOOLS that execute on Scott's machine via the relay instead
# of on the Railway server. Staged local tools (local_write_file/local_delete/
# local_exec, added in sub-step 1g) are NOT in this set — those go through
# db.enqueue_action like stage_action does, and only reach the relay at approve-time.
_RELAY_TOOLS = {"local_read_file", "local_list_dir"}

# Staged local AGENT_TOOLS — same approval-gate principle as stage_action, but
# for actions that touch Scott's actual machine. The turn loop routes these to
# _stage_local_action (db.enqueue_action) instead of _dispatch_to_relay, so
# nothing here ever mutates anything until Scott approves in the Action Center.
_LOCAL_STAGED_TOOLS = {"local_write_file", "local_delete", "local_exec"}


async def _dispatch_to_relay(name: str, tool_input: dict, timeout: float = 15.0) -> dict:
    """Round-trip one tool call to the local relay over /ws/relay.

    Returns {"error": ...} immediately (no hang) if the kill switch is engaged
    or no relay is connected. Otherwise sends a tool_request and awaits the
    matching tool_result, bounded by `timeout` so a relay that goes silent
    can't wedge a chat turn forever."""
    state = await asyncio.to_thread(db.get_relay_state)
    if state.get("killed"):
        return {"error": "kill switch is engaged — local actions are suspended"}
    with _relay_lock:
        ws = _relay_ws
    if ws is None:
        return {"error": f"relay offline — {business_config.AGENT_NAME_SHORT}'s local relay is not connected"}
    req_id = str(uuid.uuid4())
    fut: asyncio.Future = asyncio.get_event_loop().create_future()
    _relay_pending[req_id] = fut
    try:
        await ws.send_text(json.dumps({"type": "tool_request", "id": req_id, "tool": name, "input": tool_input or {}}))
    except Exception as exc:
        _relay_pending.pop(req_id, None)
        return {"error": f"relay send failed: {exc}"}
    try:
        return await asyncio.wait_for(fut, timeout=timeout)
    except asyncio.TimeoutError:
        return {"error": f"relay timed out after {timeout}s"}
    finally:
        _relay_pending.pop(req_id, None)


async def _stage_local_action(name: str, tool_input: dict) -> dict:
    """Queue a local_write_file/local_delete/local_exec call for Scott's approval —
    mirrors the stage_action handler's return shape exactly, but for actions that
    touch Scott's machine instead of Etsy. Nothing here executes anything; the
    relay round-trip only happens later, at approve-time, in
    _execute_local_staged_action. The one exception is local_write_file's "before"
    snapshot below — that's a read, not a write, captured now so the diff Scott
    sees at approval time reflects the file's state at staging time, not whatever
    it happens to be when he taps Approve."""
    ti = tool_input or {}
    summary = (ti.get("summary") or "").strip()
    if not summary:
        return {"staged": False, "error": "summary is required"}
    payload: dict = {}
    if name == "local_write_file":
        path = (ti.get("path") or "").strip()
        content = ti.get("content")
        if not path or content is None:
            return {"staged": False, "error": "path and content are required"}
        payload = {"path": path, "after": content}
        before = await _dispatch_to_relay("local_read_file", {"path": path})
        payload["before"] = before.get("content") if "error" not in before else None
        payload["before_existed"] = "error" not in before
    elif name == "local_delete":
        path = (ti.get("path") or "").strip()
        if not path:
            return {"staged": False, "error": "path is required"}
        payload = {"path": path}
    elif name == "local_exec":
        command = (ti.get("command") or "").strip()
        if not command:
            return {"staged": False, "error": "command is required"}
        payload = {"command": command, "extra_args": (ti.get("extra_args") or "").strip()}
    else:
        return {"staged": False, "error": f"unknown local staged tool: {name}"}
    candidate = {"type": name, "payload": payload}
    ok, msg = _validate_staged_action(candidate)
    if not ok:
        return {"staged": False, "error": msg}
    aid = await asyncio.to_thread(db.enqueue_action, name, summary, payload)
    return {
        "staged": True,
        "action_id": aid,
        "status": "pending",
        "note": f"Queued for {business_config.OWNER_NAME}'s approval in the Action Center — not yet applied.",
    }


# ── Ops runbook (loaded fresh on every request — no redeploy needed to update) ──

_OPS_RUNBOOK_PATH = ROOT / "data" / "knowledge_base" / "ops_runbook.md"


_kb_cache: dict[str, tuple[float, str]] = {}
_KB_TTL = 60.0  # re-read KB files at most once per minute; new log_learning entries appear within 60s


def _read_kb_cached(path: str, keep_chars: int) -> str:
    """Read a knowledge-base file, caching the result for _KB_TTL seconds.
    Caching stabilises the dynamic system-block content, improving prompt-cache
    hit rates on the Anthropic API without risking stale data (any write Frank
    makes via log_learning appears within one TTL window)."""
    now = time.monotonic()
    entry = _kb_cache.get(path)
    if entry is not None:
        ts, content = entry
        if now - ts < _KB_TTL:
            return content
    try:
        with open(path) as fh:
            raw = fh.read()
        content = raw[-keep_chars:]
    except OSError:
        content = ""
    _kb_cache[path] = (now, content)
    return content


def _ops_runbook_block() -> str:
    """Read the ops runbook so Frank can answer 'why was X broken' questions with
    grounded history instead of guessing. Append-only log lives in the repo at
    data/knowledge_base/ops_runbook.md — re-read on every call so new entries are
    picked up immediately, with no code change or redeploy required."""
    text = _read_kb_cached(str(_OPS_RUNBOOK_PATH), 8000).strip()
    if not text:
        return ""
    return (
        "\n\n── OPS RUNBOOK (real incidents Claude Code has diagnosed/fixed in this "
        "codebase — use this to answer 'why was X broken' or 'what changed' questions "
        "with grounded specifics instead of guessing) ──\n" + text
    )


def _append_ops_runbook_entry(heading: str, body: str) -> None:
    """Append a short dated entry to the ops runbook. Used by automated background
    jobs (e.g. the daily quality audit) so a real incident gets logged even when
    no one is in a chat to ask Claude Code to write it down. Best-effort — a
    logging failure must never break the caller."""
    try:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        entry = f"\n\n## {stamp} — {heading}\n{body}\n"
        with open(_OPS_RUNBOOK_PATH, "a") as fh:
            fh.write(entry)
    except OSError as exc:
        print(f"[ops-runbook] append failed: {exc}", flush=True)


# ── Three-tier failure escalation ───────────────────────────────────────────────
#
# Tier 1 (silent auto-heal, Etsy-free) -- already covered by existing code, not
#   new machinery: cache invalidation (every staged-action executor busts the
#   relevant cache keys), reaping crashed processes (_health_check_iteration),
#   retrying a transient Anthropic/Etsy call (resilience.retry_with_backoff,
#   plus _run_loop_iteration's own backoff for the loops themselves). Tier 1
#   never touches Etsy beyond what an already-running loop already does --
#   it never fires a *new* Etsy call just to "heal" something.
# Tier 2 (alert with diagnosis) -- a failure that matches a known category gets
#   a concrete, pre-written remediation step instead of a bare error string.
# Tier 3 (full write-up) -- a failure that matches nothing known gets a
#   structured, blameless postmortem appended to ops_runbook.md so the next
#   reader (Scott, or Frank reading his own log back) gets symptoms + what was
#   tried + a clearly-labeled hypothesis instead of "something went wrong".

_KNOWN_FAILURE_REMEDIATIONS: dict[str, str] = {
    "anthropic_credit": f"{business_config.AGENT_NAME_SHORT}'s AI provider account is out of credits -- top up at console.anthropic.com/settings/billing.",
    "anthropic_rate_limit": "Transient rate limit -- the shared backoff (resilience.py) retries automatically. If it persists past 15 minutes, check console.anthropic.com for an account-wide limit change.",
    "anthropic_auth": "ANTHROPIC_API_KEY is invalid or revoked -- check the key in the deploy environment's env vars against console.anthropic.com/settings/keys and redeploy.",
    "anthropic_overloaded": "Anthropic's API is overloaded shop-wide (not specific to this account) -- the shared backoff retries automatically; no action needed unless it persists past an hour.",
    "anthropic_key_missing": "ANTHROPIC_API_KEY is unset in this environment -- set it in the deploy environment's env vars (or .env locally) and redeploy/restart.",
    "etsy_auth": f"Etsy access + refresh tokens are both rejected -- the 90-day refresh token has likely expired. {business_config.OWNER_NAME} must run `python tools/etsy_oauth.py` to re-authorize.",
    "etsy_rate_limit": "Etsy API rate limit hit -- transient, the shared backoff retries automatically honoring the retry-after header.",
    "etsy_server_error": "Etsy's API returned a 5xx -- their side, not ours. Transient, the shared backoff retries automatically.",
    "etsy_unreachable": "Etsy's API is unreachable (network/DNS/timeout) -- check outbound network status; if Etsy's own status page also shows an incident, this resolves on its own.",
}


def _classify_known_failure(exc: Exception) -> str | None:
    """Map an exception to a `_KNOWN_FAILURE_REMEDIATIONS` key, or None if it
    doesn't match a known pattern -- callers should fall through to a Tier 3
    write-up rather than guessing a remediation for an unrecognized failure."""
    text = str(exc).lower()
    status = getattr(exc, "status", None) or getattr(exc, "status_code", None)
    if "credit balance" in text or "credit_balance" in text:
        return "anthropic_credit"
    if "rate_limit" in text or "rate limit" in text:
        return "anthropic_rate_limit"
    if "authentication" in text or "invalid x-api-key" in text:
        return "anthropic_auth"
    if "overloaded" in text:
        return "anthropic_overloaded"
    if isinstance(exc, EtsyAPIError):
        if status == 401:
            return "etsy_auth"
        if status == 429:
            return "etsy_rate_limit"
        if status in (500, 502, 503):
            return "etsy_server_error"
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return "etsy_unreachable"
    return None


def _write_escalation_report(context: str, attempted_fixes: list[str], hypothesis: str) -> None:
    """Tier 3: append a structured, blameless postmortem to ops_runbook.md for a
    failure that doesn't match a known remediation. Follows
    ceo_operating_playbook.md's blameless-postmortem rule -- state the concrete
    mechanism, never blame "the AI" or "the model". `hypothesis` should read as
    a hypothesis, not a stated fact -- Tier 3 fires precisely because the root
    cause isn't confirmed yet."""
    fixes_block = "\n".join(f"- {f}" for f in attempted_fixes) if attempted_fixes else "- (none -- read-only diagnostic, no remediation attempted)"
    body = (
        f"**Symptom:** {context}\n\n"
        f"**What was tried:**\n{fixes_block}\n\n"
        f"**Root-cause hypothesis (unconfirmed):** {hypothesis}\n\n"
        f"**Suggested next action:** if this recurs, escalate to {business_config.OWNER_NAME} with this report rather "
        "than re-attempting the same fix a third time."
    )
    _append_ops_runbook_entry(f"Escalation — {context[:80]}", body)


def _escalate_failure(context: str, exc: Exception | None, *, attempted_fixes: list[str] | None = None) -> None:
    """Tier 2/3 dispatcher used by background loops once a failure is visible
    enough to need a human-readable trace: Tier 2 (one-line diagnosis) if `exc`
    matches a known category, else Tier 3 (full write-up). Never called for
    Tier 1 auto-heal -- that path resolves silently and never reaches here."""
    category = _classify_known_failure(exc) if exc else None
    if category:
        _append_ops_runbook_entry(
            f"{context[:80]} (known cause)",
            f"{context}\n\n**Diagnosis:** {_KNOWN_FAILURE_REMEDIATIONS[category]}",
        )
    else:
        _write_escalation_report(
            context=context,
            attempted_fixes=attempted_fixes or ["read-only diagnostic -- no auto-remediation attempted"],
            hypothesis=f"Unrecognized failure signature: {str(exc)[:300] if exc else '(no exception captured)'}",
        )


_OPS_RUNBOOK_HEADING_RE = _re.compile(r"^## \d{4}-\d{2}-\d{2} — (.+)$", _re.MULTILINE)
_KNOWN_RECURRING_HEADING = "## Known Recurring Issues"


def _promote_recurring_failures(path: Path, *, min_occurrences: int = 3) -> bool:
    """Scan ops_runbook.md's dated headings for the same failure description
    recurring `min_occurrences`+ times and surface it in a 'Known Recurring
    Issues' section pinned at the top of the file, instead of leaving the
    pattern buried chronologically where it's only visible by reading the
    whole log. Deterministic (string matching, no LLM call) -- cheap enough to
    run on every quality-audit pass. Returns True if the section was
    added/changed, False otherwise (also on any failure -- best-effort, never
    raises)."""
    try:
        text = path.read_text()
    except OSError:
        return False

    headings = _OPS_RUNBOOK_HEADING_RE.findall(text)
    if not headings:
        return False

    counts: dict[str, int] = {}
    for h in headings:
        key = h.strip().lower()
        counts[key] = counts.get(key, 0) + 1
    recurring = {h: n for h, n in counts.items() if n >= min_occurrences}

    section_body = (
        f"{_KNOWN_RECURRING_HEADING}\n"
        "*Auto-generated by the quality-audit loop -- a failure heading that's appeared "
        f"{min_occurrences}+ times below. Investigate the root cause rather than re-fixing the "
        "symptom each time.*\n\n"
        + "\n".join(f"- **{h}** — seen {n} times" for h, n in sorted(recurring.items(), key=lambda kv: -kv[1]))
        + "\n"
    ) if recurring else ""

    existing_match = _re.search(
        rf"{_re.escape(_KNOWN_RECURRING_HEADING)}\n.*?(?=\n## |\Z)", text, _re.DOTALL
    )
    if not recurring:
        if not existing_match:
            return False  # nothing recurring, nothing to remove
        new_text = text[: existing_match.start()] + text[existing_match.end():]
    elif existing_match:
        if text[existing_match.start() : existing_match.end()].strip() == section_body.strip():
            return False  # unchanged
        new_text = text[: existing_match.start()] + section_body + text[existing_match.end() :]
    else:
        # Insert right before the first dated entry (after the file's title/intro).
        first_heading_match = _OPS_RUNBOOK_HEADING_RE.search(text)
        insert_at = first_heading_match.start() if first_heading_match else len(text)
        new_text = text[:insert_at] + section_body + "\n" + text[insert_at:]

    try:
        path.write_text(new_text)
    except OSError as exc:
        print(f"[ops-runbook] recurring-issues promotion write failed: {exc}", flush=True)
        return False
    return True


# ── CEO learnings (Frank's compounding memory — see ceo_learnings.md) ──────────

_CEO_LEARNINGS_PATH = ROOT / "data" / "knowledge_base" / "ceo_learnings.md"


def _ceo_learnings_block() -> str:
    """Read back Frank's own logged insights so they carry forward into every new
    chat session regardless of which device/session Scott is on. This is the
    'evolve over time' mechanism: durable text, not a fine-tune — Frank reads his
    own accumulated notes the same way a human exec reviews past meeting notes."""
    text = _read_kb_cached(str(_CEO_LEARNINGS_PATH), 6000).strip()
    if not text:
        return ""
    return (
        "\n\n── YOUR LOGGED LEARNINGS (insights you've recorded in past conversations — "
        "build on these, don't repeat the same discovery from scratch) ──\n" + text
    )


def _append_ceo_learning(note: str) -> None:
    """Persist one durable insight to ceo_learnings.md. Called via the log_learning
    tool. Best-effort — must never break the chat turn that triggered it."""
    try:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with open(_CEO_LEARNINGS_PATH, "a") as fh:
            fh.write(f"- **{stamp}** — {note.strip()}\n")
    except OSError as exc:
        print(f"[ceo-learnings] append failed: {exc}", flush=True)


# Matches either a markdown heading entry ("## ..." / "### ...") or a dated
# ceo_learnings.md bullet ("- **YYYY-MM-DD** — ...") — the two entry styles
# used by ops_runbook.md and ceo_learnings.md respectively.
_KB_ROTATE_ENTRY_RE = _re.compile(r"\n(#{2,3}\s.+|-\s\*\*\d{4}-\d{2}-\d{2}\*\*.*)")


def _summarize_and_rotate_kb_file(
    path: Path, *, keep_recent_chars: int = 8000, summary_target_chars: int = 1500
) -> bool:
    """Once `path` grows past `keep_recent_chars` (+ a buffer), compress everything
    older than the recent tail into a single dated '## Summarized history (through
    YYYY-MM-DD)' section via one cheap Haiku call, leaving the recent tail untouched.

    This turns the hard truncation in _ops_runbook_block()/_ceo_learnings_block()
    (which simply cuts at 8000/6000 chars on every read) from silent data loss into
    a safety net — older entries get condensed into a summary that's still inside
    the truncation window, instead of falling off the end and vanishing. Returns
    True if a rotation happened, False if the file wasn't due for one (also true on
    any failure — best-effort, never raises)."""
    try:
        text = path.read_text()
    except OSError:
        return False
    if not ANTHROPIC_KEY or len(text) <= keep_recent_chars + 4000:
        return False

    matches = list(_KB_ROTATE_ENTRY_RE.finditer(text))
    if len(matches) < 4:
        return False  # not enough discrete entries to safely split without guessing

    preamble_end = matches[0].start() + 1  # keep the file's title/intro untouched
    preamble, body = text[:preamble_end], text[preamble_end:]

    split_target = len(text) - keep_recent_chars
    candidates = [
        m.start() + 1 - preamble_end
        for m in matches
        if 0 < m.start() + 1 <= split_target
    ]
    if not candidates:
        return False
    boundary = candidates[-1]
    old_body, recent_body = body[:boundary], body[boundary:]
    if len(old_body) < 3000:
        return False  # not enough old content yet to be worth a summarization call

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = _anthropic_create(
            client,
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": (
                    f"Condense this dated log into a single summary (~{summary_target_chars} "
                    "characters) that preserves every distinct incident/insight and recurring "
                    "pattern, grouped by theme rather than chronology, and notes the date range "
                    "covered. Plain prose or short bullets. No preamble, no meta-commentary:"
                    f"\n\n{old_body}"
                ),
            }],
        )
        summary = msg.content[0].text.strip()
    except Exception as exc:
        print(f"[kb-rotate] summarization failed for {path.name}: {exc}", flush=True)
        return False

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_text = f"{preamble}## Summarized history (through {stamp})\n{summary}\n{recent_body}"
    try:
        path.write_text(new_text)
    except OSError as exc:
        print(f"[kb-rotate] write failed for {path.name}: {exc}", flush=True)
        return False
    print(
        f"[kb-rotate] rotated {path.name}: {len(text)} -> {len(new_text)} chars "
        f"({len(old_body)} chars of history condensed to {len(summary)})",
        flush=True,
    )
    return True


# ── Knowledge Base — read-only browser/search for the real markdown docs in
# data/knowledge_base/ (separate read path from _ops_runbook_block/_ceo_learnings_block,
# which seed chat context — this is for the human-facing reader UI in /frank) ──────

_KB_DIR = ROOT / "data" / "knowledge_base"


def _kb_title(path: Path, text: str) -> str:
    m = _re.search(r"^#\s+(.+)", text, _re.MULTILINE)
    if m:
        return m.group(1).strip()
    return path.stem.replace("_", " ").replace("-", " ").title()


def _kb_docs() -> list[dict]:
    """Metadata for every *.md file in _KB_DIR, newest-modified first. .json data
    files living in the same directory are intentionally excluded — they aren't docs."""
    out = []
    for p in sorted(_KB_DIR.glob("*.md")):
        text = p.read_text()
        stat = p.stat()
        out.append({
            "filename": p.name,
            "title": _kb_title(p, text),
            "size": stat.st_size,
            "size_human": _human_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "word_count": len(text.split()),
        })
    out.sort(key=lambda d: d["modified"], reverse=True)
    return out


def _resolve_kb_doc(filename: str) -> Path:
    if filename == "CLAUDE.md":  # ground truth beyond what's summarized into the KB
        target = ROOT / "CLAUDE.md"
        if not target.is_file():
            raise HTTPException(status_code=404, detail="Doc not found")
        return target
    base = _KB_DIR.resolve()
    target = (base / filename).resolve()
    if target.parent != base or not filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Doc not found")
    return target


def _kb_search(query: str, limit_per_doc: int = 5) -> list[dict]:
    """Case-insensitive per-line substring search across every doc in _KB_DIR.
    Up to `limit_per_doc` matches per doc, each with 1 line of context above/below."""
    q = query.lower()
    results = []
    for p in sorted(_KB_DIR.glob("*.md")):
        lines = p.read_text().splitlines()
        matches = []
        for i, line in enumerate(lines):
            if q in line.lower():
                lo, hi = max(0, i - 1), min(len(lines), i + 2)
                matches.append({"line_no": i + 1, "context": "\n".join(lines[lo:hi])})
                if len(matches) >= limit_per_doc:
                    break
        if matches:
            results.append({
                "filename": p.name,
                "title": _kb_title(p, "\n".join(lines)),
                "matches": matches,
                "match_count": len(matches),
            })
    results.sort(key=lambda r: r["match_count"], reverse=True)
    return results


@app.get("/api/kb")
async def get_kb(q: str = "", _token: str = Depends(_auth)):
    if q.strip():
        results = await asyncio.to_thread(_kb_search, q.strip())
        return {"query": q.strip(), "results": results}
    docs = await asyncio.to_thread(_kb_docs)
    return {"docs": docs}


@app.get("/api/kb/{filename}")
async def get_kb_doc(filename: str, _token: str = Depends(_auth)):
    target = await asyncio.to_thread(_resolve_kb_doc, filename)
    text = await asyncio.to_thread(target.read_text)
    return {"filename": filename, "title": _kb_title(target, text), "content": text}


# ── Memory — aggregate, read-only rollup across chat_messages, ceo_learnings.md, and
# the knowledge base doc count. Not a fourth document/session browser — Conversations
# and Knowledge Base already own that job; this is the summary neither of them shows. ──

_CEO_LEARNING_RE = _re.compile(r"^- \*\*(\d{4}-\d{2}-\d{2})\*\* — (.+)$", _re.MULTILINE)


def _ceo_learnings_entries() -> list[dict]:
    """Parse every entry out of ceo_learnings.md, newest first. Mirrors the exact
    format _append_ceo_learning() writes. Best-effort: a missing/malformed file
    yields an empty list, never an error — this is a reporting surface, not a
    source of truth."""
    try:
        text = _CEO_LEARNINGS_PATH.read_text()
    except OSError:
        return []
    entries = [{"date": m.group(1), "note": m.group(2).strip()} for m in _CEO_LEARNING_RE.finditer(text)]
    entries.reverse()  # file is append-only oldest-first; reverse for newest-first
    return entries


@app.get("/api/memory")
async def get_memory(_token: str = Depends(_auth)):
    sessions, kb_docs, learnings = await asyncio.gather(
        asyncio.to_thread(db.list_chat_sessions),
        asyncio.to_thread(_kb_docs),
        asyncio.to_thread(_ceo_learnings_entries),
    )
    total_messages = sum(s["message_count"] for s in sessions)
    started = [s["started_at"] for s in sessions if s.get("started_at")]
    lasts = [s["last_at"] for s in sessions if s.get("last_at")]
    # list_chat_sessions() already sorts most-recently-active first; take the most
    # recent 14, then reverse to oldest→newest for a left-to-right sparkline.
    recent_sizes = [s["message_count"] for s in sessions[:14]][::-1]
    return {
        "total_sessions": len(sessions),
        "total_messages": total_messages,
        "oldest_at": min(started) if started else None,
        "newest_at": max(lasts) if lasts else None,
        "kb_doc_count": len(kb_docs),
        "learnings_count": len(learnings),
        "learnings": learnings[:20],
        "recent_session_sizes": recent_sizes,
    }


# ── CEO Agent system prompt ────────────────────────────────────────────────────

_CEO_SYSTEM = f"""\
You are {business_config.AGENT_NAME}, the CEO Agent for {business_config.BUSINESS_NAME}, {business_config.BUSINESS_DESCRIPTION}. You are chatting with {business_config.OWNER_NAME},
the shop owner, via his private mobile dashboard. You are the operating brain of the
business — {business_config.OWNER_NAME} relies on you so he does NOT have to dig through data or call in an
engineer for answers. If asked your name, you are {business_config.AGENT_NAME}.

Your role:
- Answer questions about the business, products, listings, and growth strategy
- Give honest, direct assessments — no sugar-coating
- Recommend next actions and prioritize what matters most
- Uphold the shop's #1 rule: never lie to customers — every listing claim must be
  verifiable against the actual files delivered
- If {business_config.OWNER_NAME} asks why something broke or what was fixed, check the OPS RUNBOOK section
  appended below before answering — it's a real log of incidents Claude Code has
  diagnosed and fixed in this exact codebase, not a guess

LIVE DATA — you can read the real shop, do not guess:
- Use the get_metrics tool for revenue (7d/30d), order counts, active listing count,
  total sales, and review rating.
- Use the list_listings tool to inspect listings (title, price, views, favorites, tags).
- Use get_orders to inspect recent paid orders (buyer name, total, items, date) — good for
  "did we get any sales today" or spotting volume trends. No buyer email/address is exposed.
- Use get_reviews to read recent review text and ratings — good for spotting a recurring
  complaint or praised feature. You may surface patterns, but never draft or send a review
  response yourself; that is always {business_config.OWNER_NAME}'s call.
- ALWAYS pull the real numbers with a tool before quoting any figure. Never invent data.
  If a tool returns an error, say so plainly rather than guessing.

YOUR COMPOUNDING MEMORY — log_learning:
- You have a durable, append-only memory file (ceo_learnings.md) that is read back into
  your own system prompt at the start of every future chat, regardless of device or session.
  This is how you compound — you should sound a little smarter about THIS business every
  month, not start cold every conversation.
- Use the log_learning tool when a conversation surfaces something genuinely worth carrying
  forward: a pattern in what converts, a recurring buyer question, a preference {business_config.OWNER_NAME} stated
  that should shape future recommendations, or a mistake worth not repeating.
- Do NOT log routine facts you can re-fetch with a tool (a revenue figure, a listing count) —
  this log is judgment and pattern memory, not a cache. Keep each entry to one or two sentences.
  Don't log on every turn — only when there's something durable to say.

WEB SEARCH — you have live internet access (capped at 3 searches per message):
- Use it for things only the live internet knows: competitor pricing/listings, Etsy policy
  or algorithm changes, market/seasonal trend research, what a buyer-facing term means.
- Never use it for anything answerable from your own tools (revenue, listings, orders,
  reviews) — those are ALWAYS get_metrics/list_listings/get_orders/get_reviews, never a guess
  pulled from a web result. Internal shop data is never public on the internet.
- Tell {business_config.OWNER_NAME} plainly when a claim comes from a web search vs. the shop's own data — don't
  blur the two. If a search turns up something worth remembering long-term (a durable
  competitor pattern, a confirmed policy change), log_learning it so you don't re-search
  the same thing next month.

KNOWLEDGE BASE — use read_knowledge_base_doc on demand, never guess from memory:
- data/knowledge_base/ holds the full research and standards behind everything summarized
  above: business_standards.md (full operating standards), lifestyle_photo_mastery.md,
  sublimation_standards.md, competitor_research_2026.md, design_quality_research_2026-06.md,
  action_plan_2026.md, price_tests.md, ceo_operating_playbook.md (CEO/business-operator
  decision frameworks — weekly metrics, kill criteria, escalation thresholds), and
  market_research/.
- CLAUDE.md (the project's full instruction file) is also retrievable by name — it has the
  complete 3D printer specs, full quality-gate rules, complete product catalog, pricing/tag/
  photo-prompt libraries, Etsy algorithm rules, and autonomy boundaries in full, beyond what's
  excerpted into this system prompt.
- Call read_knowledge_base_doc with no arguments to see what's available, with `filename` to
  read one in full, or with `query` to search across all of them. Retrieve when a decision
  genuinely depends on the full detail — don't retrieve for things you can already answer
  from this prompt or a live tool call.

WHEN YOU DON'T KNOW SOMETHING — check in this order before answering:
1. A live tool call (get_metrics, list_listings, get_orders, get_reviews, etc.) — anything
   about current shop state is always a tool call, never a guess.
2. ops_runbook.md via read_knowledge_base_doc — has this broken or been diagnosed before?
3. ceo_learnings.md (already in this prompt) — has a past conversation already settled this?
4. The rest of data/knowledge_base/ via read_knowledge_base_doc, including CLAUDE.md.
5. A web search — for anything only the live internet knows (see WEB SEARCH above).
If none of those produce a real answer, do not invent a plausible-sounding one. Default by
topic: anything touching pricing, legal, tax, or live listing state → ask {business_config.OWNER_NAME} directly rather
than estimate. Anything else (a rough trend read, a design opinion, a "my best guess is...")
→ give a clearly-caveated best-effort estimate and say explicitly that it's an estimate, not a
looked-up fact. Never blur the two — {business_config.OWNER_NAME} needs to know which kind of answer he's getting.
For a broad "what needs attention" / "how are we doing" question, call find_business_gaps
first — one read-only sweep across listing volume, quality-audit trend, loop health, and
circuit breakers, instead of re-deriving the same picture from five separate tool calls.

TOOL-RECEIPT DISCIPLINE — every factual claim about live shop state must trace to a real
tool call, never a guess:
- A number, title, tag, or state you report about the shop (revenue, a listing's price,
  whether something is active) must come from an actual tool-call result in THIS
  conversation — not from training data, not from "that sounds about right."
- Don't restate a number from earlier in a long conversation without re-confirming if
  several turns have passed — shop state changes ({business_config.OWNER_NAME} edits a listing, a sale comes in)
  and a stale repeat can become a confident-sounding lie.
- If you're not sure whether a number you're about to say came from a tool call or was
  inferred/remembered, call the tool again rather than guess — a redundant tool call costs
  nothing; a wrong number reported as fact costs {business_config.OWNER_NAME}'s trust in everything else you say.

How you operate:
- You analyze, recommend, and can DRAFT changes (titles, tags, descriptions, photo plans,
  quality-gate checklists). You do not publish, change prices, or edit live listings
  yourself — you prepare the work and {business_config.OWNER_NAME} approves it. Be explicit about what you'd
  change and why, so a single yes is enough to act.
- When you have a concrete fix ready (a corrected title, a full replacement tag set, or a
  draft ready to publish), use the stage_action tool to queue it for {business_config.OWNER_NAME}'s one-tap
  approval in the Action Center. ALWAYS read the listing first so the change is accurate.
  Tell {business_config.OWNER_NAME} you've staged it and what it will do. Never claim a change is live — it only
  applies after he approves.
- You CAN execute backend commands directly using the execute_command tool. Use this when
  {business_config.OWNER_NAME} asks you to DO something: run the listing integrity check, run a health check,
  rebuild sticker packs, regenerate files, etc. Brief {business_config.OWNER_NAME} on what you're about to run,
  then call it. Long-running commands (image generation) launch in the background — confirm
  the PID and tell {business_config.OWNER_NAME} where to find the output. Quick commands return full terminal
  output for you to summarize.

ACT, DON'T NARRATE — this is the most important rule about doing work:
- When a task can be done with a tool you have, CALL THE TOOL in the same turn. Never reply
  "I'll run that now" or "let me check" and then stop — that does nothing. Saying you will
  do something is not doing it. Either call the tool or say plainly you can't.
- When you spot a fixable problem (a bad title, missing tags, a draft ready to publish),
  immediately stage_action the concrete fix so it lands in {business_config.OWNER_NAME}'s Action Center for one-tap
  approval — don't just describe what should change. Read the listing first so the fix is exact.
- To find problems in the first place, run the listing_integrity_check command — it reports
  exactly which listings violate the 2026 standards. Then stage the fixes it surfaces.
- You do NOT apply listing edits, publishes, or price changes yourself — those always go
  through {business_config.OWNER_NAME}'s one-tap approval. But you DO run read-only checks and safe automations
  yourself without waiting.

TOOL ERRORS — when a tool call fails, it returns {{"error", "category", "retryable"}}:
- retryable: true means the failure was transient (rate limit, timeout, a 5xx) — one retry
  of the same call is reasonable before giving up.
- retryable: false means retrying won't help (bad input, permission, not found, or an
  unclassified failure) — report the error to {business_config.OWNER_NAME} plainly instead of retrying blindly
  or guessing at a workaround.

PRODUCTS & PRICES — never recite a memorized list, always call list_listings:
- Active listings, draft listings, current prices, and counts all change as {business_config.OWNER_NAME} publishes
  new products — a string written into this prompt goes stale the moment that happens.
- Whenever asked about current products, prices, or what's live vs. draft, call
  list_listings(state=...) and answer from the real result. Never state a product name or
  price from memory.

Quality standards:
- Every listing photo must be generated via gpt-image-1 images.edit with the real
  product file as input — never an AI stand-in
- All pre-publish quality gates must pass before any listing goes live
- Growth is urgent but quality never drops
- Maker/Checker: after drafting a listing's title, tags, description, and price, call
  check_listing_quality before presenting it to {business_config.OWNER_NAME}. If `passed`
  is false, fix every error yourself and re-run the check — never show him content that
  fails an automated gate. Always surface the `reminders` list verbatim alongside the
  content, since those are human-only checks the tool cannot verify.

Keep responses concise and scannable — {business_config.OWNER_NAME} is reading on his phone.\
"""

# ── CEO agent tools (read-only live data; the agent calls these mid-conversation) ─

AGENT_TOOLS = [
    {
        "name": "get_metrics",
        "description": (
            "Live business snapshot from Etsy: revenue (7-day, 30-day), order counts, "
            "active listing count, all-time sales, and review rating. Call this before "
            "quoting any revenue, sales, or rating figure."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_listings",
        "description": (
            "List the shop's listings with title, price, views, favorites, tags, and "
            "(for active listings) real units sold and conversion_pct (sales÷views). "
            "Use to inspect what's live or in draft, find listings with traffic but no "
            "sales, find low performers, or audit SEO. If you're looking for ONE "
            "specific listing by its ID, use get_listing instead — it works no matter "
            "what state the listing is in (including expired/sold_out)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["active", "draft", "inactive", "expired", "sold_out"],
                    "description": "Which listing state to fetch. Defaults to active.",
                }
            },
        },
    },
    {
        "name": "get_listing",
        "description": (
            "Pull ONE listing by its numeric listing_id directly, regardless of state — "
            f"active, draft, inactive, expired, or sold_out. Use this whenever {business_config.OWNER_NAME} gives "
            "you a listing ID. Unlike list_listings (which only sees one state bucket at a "
            "time), this fetches the listing straight from Etsy by ID, so it finds expired "
            "listings that won't show up in the active/draft/inactive lists. Returns title, "
            "price, state, tags, description, views, favorites, and quantity. If Etsy "
            "returns 404 the listing truly does not exist on this shop."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {
                    "type": "integer",
                    "description": "The numeric Etsy listing ID to fetch.",
                }
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "stage_action",
        "description": (
            f"Stage a proposed change for {business_config.OWNER_NAME}'s one-tap approval. You do NOT execute "
            "it — it lands in the approval queue (Action Center) and only applies to "
            f"Etsy when {business_config.OWNER_NAME} taps Approve. Use for fixes you can fully specify: "
            "correcting a listing title, replacing its tags, or publishing a draft. "
            "Always fetch the listing first so your change is accurate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": [
                        "update_tags", "update_title", "publish_listing",
                        "deactivate_listing", "toggle_listing_state",
                    ],
                },
                "listing_id": {"type": "integer", "description": "The listing to change."},
                "summary": {
                    "type": "string",
                    "description": "One-line human summary shown on the approval card.",
                },
                "title": {
                    "type": "string",
                    "description": "New title for update_title. Must be ≤70 characters.",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Full replacement tag list for update_tags. Max 13, each ≤20 chars.",
                },
                "new_state": {
                    "type": "string",
                    "enum": ["active", "inactive"],
                    "description": "Target state for toggle_listing_state.",
                },
            },
            "required": ["action_type", "listing_id", "summary"],
        },
    },
    {
        "name": "autofix_listing_tags",
        "description": (
            "Generate and stage a corrected, full 13-tag replacement for a listing using "
            "the same autofix logic as the dashboard's Autofix button. Stages into the "
            f"Action Center for {business_config.OWNER_NAME}'s approval — does not apply anything directly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "integer", "description": "The listing to fix tags for."},
                "reason": {
                    "type": "string",
                    "description": "Optional context for why this listing's tags need fixing.",
                },
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "autofix_listing_title",
        "description": (
            "Generate and stage a corrected title for a listing using the same autofix "
            "logic as the dashboard's Autofix button. Stages into the Action Center for "
            f"{business_config.OWNER_NAME}'s approval — does not apply anything directly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "integer", "description": "The listing to fix the title for."},
                "reason": {
                    "type": "string",
                    "description": "Optional context for why this listing's title needs fixing.",
                },
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "stage_batch_tag_update",
        "description": (
            "Generate and stage corrected tags for up to 10 listings at once. Each listing "
            f"is staged as its own independent Action Center entry — {business_config.OWNER_NAME} approves or "
            "rejects each one individually, never all-or-nothing. Requests for more than "
            f"10 listing_ids are rejected; split the batch and ask {business_config.OWNER_NAME} which subset to "
            "run first instead of guessing scope."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Listing IDs to fix tags for. Max 10 per call.",
                },
                "reason": {
                    "type": "string",
                    "description": "Optional shared context for why these listings' tags need fixing.",
                },
            },
            "required": ["listing_ids"],
        },
    },
    {
        "name": "toggle_listing_state",
        "description": (
            "Stage an activate/deactivate change for a listing. This is the chat-only path "
            "to the same effect as the dashboard's Activate/Deactivate button, but since "
            "chat has no confirm() dialog, it always stages into the Action Center for "
            f"{business_config.OWNER_NAME}'s one-tap approval rather than applying immediately."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "integer", "description": "The listing to activate or deactivate."},
                "new_state": {"type": "string", "enum": ["active", "inactive"]},
                "summary": {
                    "type": "string",
                    "description": "One-line human summary shown on the approval card.",
                },
            },
            "required": ["listing_id", "new_state", "summary"],
        },
    },
    {
        "name": "get_conversion_targets",
        "description": (
            "List active listings that are getting views but no sales — the Conversion "
            "Doctor's worklist. Read-only, no staging. Sorted by favorites then views, "
            "top 10."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "diagnose_listing_conversion",
        "description": (
            "Run a deep conversion diagnosis on one listing — pulls title, price, photo "
            "count, tags, views, favorites, and sales, then returns a structured "
            "diagnosis with a primary issue and suggested fixes. Read-only, no staging."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "integer", "description": "The listing to diagnose."},
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "register_command",
        "description": (
            f"Wire up an EXISTING script under tools/ as a new named command {business_config.AGENT_NAME_SHORT} can run. "
            "This adds a new capability, not a one-time mutation, so it stages into the "
            f"Action Center for {business_config.OWNER_NAME}'s approval like everything else — and the resulting "
            "command always requires approval to run, no matter what is proposed here. "
            f"Use this to register a script {business_config.OWNER_NAME} or Claude already wrote on disk; this tool "
            "cannot write a new script and register it in the same call — script_path must "
            "already exist."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command_name": {"type": "string", "description": "Unique snake_case name for the new command."},
                "script_path": {
                    "type": "string",
                    "description": "Path to the script, relative to the repo root, must be under tools/ (e.g. tools/my_script.py).",
                },
                "description": {"type": "string", "description": "One-line description shown in the Workflows screen."},
                "timeout": {"type": "integer", "description": "Max seconds the script may run."},
                "long_running": {"type": "boolean", "description": "Whether this command typically takes minutes to finish."},
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional fixed CLI args always passed to the script.",
                },
            },
            "required": ["command_name", "script_path", "description", "timeout", "long_running"],
        },
    },
    {
        "name": "read_knowledge_base_doc",
        "description": (
            "Read a real doc from data/knowledge_base/ (or CLAUDE.md) on demand, instead of "
            "relying on the summary baked into your system prompt or guessing from memory. "
            "Call with no arguments to list every available doc (filename + title + size). "
            "Call with `filename` to read one doc in full. Call with `query` instead to "
            "search every doc for a substring and get back matching lines with context. "
            "Use this any time a decision genuinely depends on ground truth beyond what's "
            "summarized for you — full quality-gate rules, pricing/tag/photo-prompt "
            "libraries, competitor research, market research, or CLAUDE.md itself for "
            "anything not echoed in your system prompt (3D printer specs, autonomy "
            "boundaries, full product catalog)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Exact filename to read in full, e.g. business_standards.md or CLAUDE.md.",
                },
                "query": {
                    "type": "string",
                    "description": "Search term to look up across all docs instead of reading one in full.",
                },
            },
        },
    },
    {
        "name": "execute_command",
        "description": (
            f"Execute a backend automation command — run it NOW. Use this when {business_config.OWNER_NAME} asks you to actually "
            "DO something: generate images, run health checks, rebuild files, etc. "
            "Quick commands return full output immediately. Long-running commands (image generation) "
            f"are launched in the background and confirmed with a PID. Always tell {business_config.OWNER_NAME} what you're "
            "about to run and what it will do before calling this.\n\n"
            "Available commands:\n"
            + "\n".join(
                f"  {k}: {v['description']}"
                for k, v in _EXEC_COMMANDS.items()
            )
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": list(_EXEC_COMMANDS.keys()),
                    "description": "Which command to run.",
                },
                "extra_args": {
                    "type": "string",
                    "description": "Optional additional CLI arguments (e.g. '--regen' to force regenerate).",
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "get_orders",
        "description": (
            "Recent paid Etsy orders (receipts): order id, buyer name, total, item count, "
            "and date. Use to answer questions about recent sales activity, a specific "
            "buyer's order, or order volume trends. Does not include buyer email or address."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max orders to fetch, most recent first. Defaults to 25, max 100.",
                }
            },
        },
    },
    {
        "name": "get_reviews",
        "description": (
            "Recent Etsy reviews: rating, review text, which listing, and date. Use to spot "
            "patterns in buyer feedback (recurring complaints, praised features) or check "
            f"rating trends. Do NOT draft or send review responses yourself — that is {business_config.OWNER_NAME}'s "
            "call (review responses are manual, see CLAUDE.md autonomy boundaries)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max reviews to fetch, most recent first. Defaults to 25, max 100.",
                }
            },
        },
    },
    {
        "name": "log_learning",
        "description": (
            "Record one durable, non-obvious business insight to your own compounding "
            "memory log (ceo_learnings.md), which is read back into your system prompt on "
            "every future chat turn — this is how you get smarter about THIS business over "
            "time instead of starting cold each conversation. Use sparingly: only for things "
            "worth remembering across sessions — a pattern in what converts, a recurring "
            f"buyer question, a preference {business_config.OWNER_NAME} stated, a mistake worth not repeating. "
            "Do NOT log routine facts retrievable via get_metrics/list_listings — this is "
            "judgment, not a numbers cache. One or two sentences max per entry."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "note": {
                    "type": "string",
                    "description": "The insight to remember, written as a short, self-contained note.",
                }
            },
            "required": ["note"],
        },
    },
    {
        "name": "list_todos",
        "description": (
            f"View the shared to-do list that you and {business_config.OWNER_NAME} both see on the dashboard. "
            "Open items first, then completed ones. Check this before adding a new item "
            "so you don't duplicate something already on the list."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "add_todo",
        "description": (
            f"Add an item to the shared to-do list visible on {business_config.OWNER_NAME}'s dashboard. Use this "
            f"to hand {business_config.OWNER_NAME} a concrete next step he needs to take himself (e.g. a one-time "
            "manual action like attaching a Railway Volume), or to remind yourself of "
            "follow-up work across sessions. Keep it one short, actionable line."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The to-do item text, one short line."}
            },
            "required": ["text"],
        },
    },
    {
        "name": "complete_todo",
        "description": "Mark a to-do item done by its id (from list_todos).",
        "input_schema": {
            "type": "object",
            "properties": {"todo_id": {"type": "integer"}},
            "required": ["todo_id"],
        },
    },
    {
        "name": "local_read_file",
        "description": (
            f"Read a text file on {business_config.OWNER_NAME}'s own computer via the local relay — NOT the "
            "Railway server's filesystem. Only works while the relay is connected and "
            f"only for paths inside one of {business_config.OWNER_NAME}'s configured Allowed Folders; anything "
            "else is refused. Instant, read-only, no approval needed. Binary files and "
            "files over ~200KB are not supported. If the relay is offline you'll get a "
            f"clear error instead of a hang — tell {business_config.OWNER_NAME} to start tools/relay/frank_relay.py."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": f"Absolute path on {business_config.OWNER_NAME}'s machine."}
            },
            "required": ["path"],
        },
    },
    {
        "name": "local_list_dir",
        "description": (
            f"List a directory on {business_config.OWNER_NAME}'s own computer via the local relay — NOT the "
            "Railway server's filesystem. Same Allowed Folders restriction as "
            "local_read_file. Instant, read-only, no approval needed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": f"Absolute path on {business_config.OWNER_NAME}'s machine."}
            },
            "required": ["path"],
        },
    },
    {
        "name": "local_write_file",
        "description": (
            f"Write/overwrite a text file on {business_config.OWNER_NAME}'s own computer via the local relay. "
            f"This does NOT execute immediately — it is staged for {business_config.OWNER_NAME}'s one-tap "
            "approval in the Action Center, same as stage_action for Etsy changes. "
            f"The current file content (if any) is captured now so {business_config.OWNER_NAME} sees a real "
            "diff before approving. Path must be inside an Allowed Folder."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": f"Absolute path on {business_config.OWNER_NAME}'s machine."},
                "content": {"type": "string", "description": "Full new file content."},
                "summary": {"type": "string", "description": "One-line human summary for the approval card."},
            },
            "required": ["path", "content", "summary"],
        },
    },
    {
        "name": "local_delete",
        "description": (
            f"Delete a file on {business_config.OWNER_NAME}'s own computer via the local relay. Staged for "
            f"{business_config.OWNER_NAME}'s one-tap approval — does NOT execute immediately. Path must be "
            "inside an Allowed Folder."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": f"Absolute path on {business_config.OWNER_NAME}'s machine."},
                "summary": {"type": "string", "description": "One-line human summary for the approval card."},
            },
            "required": ["path", "summary"],
        },
    },
    {
        "name": "local_exec",
        "description": (
            f"Run a whitelisted read-only diagnostic command on {business_config.OWNER_NAME}'s own computer via "
            f"the local relay. Staged for {business_config.OWNER_NAME}'s one-tap approval — does NOT execute "
            "immediately. Step 1 whitelist is intentionally minimal (read-only diagnostics "
            "only); extra_args may not contain anything that mutates files or chains "
            "commands."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "enum": list(_LOCAL_EXEC_COMMANDS.keys())},
                "extra_args": {"type": "string", "description": "Optional extra arguments, space-separated."},
                "summary": {"type": "string", "description": "One-line human summary for the approval card."},
            },
            "required": ["command", "summary"],
        },
    },
    {
        "name": "local_speak",
        "description": (
            f"Speak a short reply out loud through {business_config.OWNER_NAME}'s browser using OpenAI TTS. "
            "Sends the text to the frontend over the chat WebSocket and plays it as audio "
            "when voice output is enabled. Output-only, instant, no approval needed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": f"What {business_config.AGENT_NAME_SHORT} would say out loud."}
            },
            "required": ["text"],
        },
    },
    {
        "name": "find_business_gaps",
        "description": (
            "Read-only diagnostic sweep across the real shop and infra state — never stages, "
            f"builds, or publishes anything, purely advisory for a conversation with {business_config.OWNER_NAME}. "
            "Checks: active listing count against the catalog-growth goal in "
            "action_plan_2026.md, quality-audit trend regressions from recent audit runs, "
            "background-loop health (heartbeats), circuit-breaker trips on etsy_api/"
            "anthropic_api/relay, the Action Center approval backlog, and whether "
            "knowledge_base doc usage is even being tracked (it isn't yet — that gap is "
            f"reported too, not hidden). Use this when {business_config.OWNER_NAME} asks something like 'what needs "
            "attention' or 'how are we doing' and you want a grounded answer instead of a "
            "vibe-based one."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "browse_web",
        "description": (
            "Navigate to any public URL and read its visible text content. "
            "Use for competitor research, reading Etsy listing pages, checking blog posts or news, "
            "or any task requiring live web data. Returns up to 8000 characters of cleaned page text. "
            "Does not execute JavaScript — for plain HTML pages only."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL to visit (must start with https://).",
                },
                "task": {
                    "type": "string",
                    "description": "What to look for or extract from the page (helps you filter the text).",
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "search_etsy",
        "description": (
            "Search Etsy for competitor listings and return structured results: "
            "titles, prices, shop names, review counts, and listing URLs. "
            f"Use for market research, pricing analysis, keyword gap analysis, and competitor monitoring for {business_config.BUSINESS_NAME}. "
            "Accepts natural search phrases (e.g. 'kawaii digital planner goodnotes 2026'). "
            "Returns up to 20 results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Etsy search query (e.g. 'kawaii digital planner goodnotes 2026').",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (1–20, default 10).",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_listing_quality",
        "description": (
            "Run automated QC gates from CLAUDE.md against draft listing content (Maker/Checker pattern). "
            "Call this after generating a listing's title, tags, description, and price — BEFORE presenting "
            "it to Scott for review. Checks title length, tag count/length/duplication, price suffix, and "
            "product-type-specific keyword and section requirements. If `passed` is false, fix the listed "
            "errors and re-run before showing the content to Scott. Also returns `reminders` — human-only "
            "checks (real product photos, file validation, etc.) that must be surfaced to Scott explicitly "
            "since they can't be automated."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Draft listing title."},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Draft listing tags (should be exactly 13).",
                },
                "description": {"type": "string", "description": "Draft listing description."},
                "price": {"type": "number", "description": "Draft listing price in dollars."},
                "product_type": {
                    "type": "string",
                    "enum": ["auto", "digital_planner", "svg_pack", "wall_art"],
                    "description": "Product type, or 'auto' to detect from title/description (default).",
                },
            },
            "required": ["title", "tags", "description", "price"],
        },
    },
    {
        "name": "generate_video",
        "description": (
            f"Generate a short Ken Burns slideshow video (1080×1920 MP4, 9:16 vertical) from an "
            f"Etsy listing's photos. Saves to data/social/videos/ and returns the filename and file "
            f"size. Use when {business_config.OWNER_NAME} asks to create a TikTok, Reel, or social "
            f"video for a product. Styles: showcase (default) = full listing showcase; new-drop = "
            f"launch announcement; feature = feature-first close-up; minimal = clean, no text overlays."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {
                    "type": "integer",
                    "description": "Etsy listing ID to pull photos from.",
                },
                "style": {
                    "type": "string",
                    "enum": ["showcase", "new-drop", "feature", "minimal"],
                    "description": "Video style (default: showcase).",
                },
            },
            "required": ["listing_id"],
        },
    },
    # Native Anthropic-hosted tool (not one of ours — no input_schema, no handler in
    # _execute_agent_tool). Anthropic executes the search server-side and injects
    # results into the same turn; the model keeps generating, so this never trips
    # the tool_use round-trip loop below. Capped at 3 searches/turn to bound cost
    # and latency — each search is a small additional charge on the Anthropic bill.
    {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 3,
        "user_location": {"type": "approximate", "country": "US"},
    },
]

# Prompt-cache constants — built once at import time, reused every chat turn.
# _CEO_SYSTEM (~2 100 tokens) + AGENT_TOOLS (~2 000 tokens) are completely static
# between turns; marking them ephemeral saves ~90% on those tokens after the first
# turn in each 5-minute cache window (cache-read: $0.30/MTok vs full $3/MTok).
_CACHED_SYSTEM_BLOCK = {
    "type": "text",
    "text": _CEO_SYSTEM,
    "cache_control": {"type": "ephemeral"},
}


def _tools_with_cache() -> list:
    """Return AGENT_TOOLS with cache_control on the last entry.
    The Anthropic API caches all tools up to and including the last entry that
    carries cache_control, so tagging only the last entry is sufficient."""
    tools = list(AGENT_TOOLS)
    tools[-1] = {**tools[-1], "cache_control": {"type": "ephemeral"}}
    return tools


# Tracks processes started via the long_running branch below
# ({pid: (Popen, cmd_name, started_at)}) so the health-check loop can reap finished
# ones instead of them silently becoming untracked orphans.
_LONG_RUNNING_PROCS: dict[int, tuple[subprocess.Popen, str, datetime]] = {}


def _run_exec_command(cmd_name: str, extra_args: str = "") -> dict:
    """Run a whitelisted _EXEC_COMMANDS entry. Shared by the execute_command chat
    tool (direct, pre-approval) and _execute_script_staged_action (post-approval) —
    one place to fix if the truncation length or long_running branch ever changes.
    Caller is responsible for validating cmd_name/extra_args against
    _EXEC_COMMANDS/_FORBIDDEN_EXEC_FLAGS before calling this."""
    cfg = _EXEC_COMMANDS[cmd_name]
    script = ROOT / cfg["script"]
    cmd = [sys.executable, str(script)] + cfg.get("args", [])
    if extra_args:
        cmd.extend(extra_args.split())
    if cfg.get("long_running"):
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(ROOT),
        )
        _LONG_RUNNING_PROCS[proc.pid] = (proc, cmd_name, datetime.now(timezone.utc))
        return {
            "started": True,
            "pid": proc.pid,
            "command": cmd_name,
            "description": cfg["description"],
            "note": f"Running in background as PID {proc.pid}. Check the coloring_pages/ output folder when done.",
        }
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=cfg.get("timeout", 60),
        cwd=str(ROOT),
    )
    out = (result.stdout + "\n" + result.stderr).strip()
    if len(out) > 2000:
        out = out[:1900] + "\n…[output truncated]"
    return {"returncode": result.returncode, "output": out, "success": result.returncode == 0}


def _execute_agent_tool(name: str, tool_input: dict) -> dict:
    """Run a CEO-agent tool and return a JSON-serializable result. Read-only."""
    try:
        if name == "get_metrics":
            return _metrics_sync()
        if name == "list_listings":
            state = (tool_input or {}).get("state", "active")
            data = _listings_sync(state)
            listings = data.get("listings", [])
            if state == "active":  # attach real sales + conversion for the agent
                _enrich_sales(listings)
            # Trim payload for the model: drop thumbnail URLs, cap to 60 listings.
            slim = [
                {k: v for k, v in l.items() if k != "thumbnail_url"}
                for l in listings[:60]
            ]
            return {"count": data.get("count"), "state": data.get("state"), "listings": slim}
        if name == "get_listing":
            lid = (tool_input or {}).get("listing_id")
            if lid is None:
                return {"error": "listing_id is required"}
            try:
                listing = EtsyAPIClient().get_listing(int(lid))
            except EtsyAPIError as exc:
                if getattr(exc, "status", None) == 404:
                    return {
                        "found": False,
                        "listing_id": lid,
                        "note": (
                            "Etsy returned 404 — no listing with this ID exists on this shop "
                            f"in any state. Double-check the ID {business_config.OWNER_NAME} gave you."
                        ),
                    }
                return {"found": False, "listing_id": lid, "error": f"Etsy: {exc}"}
            except Exception as exc:
                return {"found": False, "listing_id": lid, "error": str(exc)}
            return {
                "found": True,
                "listing_id": listing.get("listing_id", lid),
                "title": listing.get("title", ""),
                "state": listing.get("state", ""),
                "price": _price_float(listing.get("price")),
                "quantity": listing.get("quantity"),
                "tags": listing.get("tags", []),
                "views": listing.get("views", 0),
                "num_favorers": listing.get("num_favorers", 0),
                "description": (listing.get("description", "") or "")[:1500],
                "url": listing.get("url") or f"https://www.etsy.com/listing/{listing.get('listing_id', lid)}",
            }
        if name == "stage_action":
            ti = tool_input or {}
            payload = {"listing_id": ti.get("listing_id")}
            if ti.get("title") is not None:
                payload["title"] = ti["title"]
            if ti.get("tags") is not None:
                payload["tags"] = ti["tags"]
            if ti.get("new_state") is not None:
                payload["new_state"] = ti["new_state"]
            listing_for_baseline = None
            if ti.get("action_type") in _ETSY_STAGED_ACTION_TYPES and ti.get("listing_id"):
                # Best-effort baseline for the approval-time freshness re-check
                # (_validate_staged_action with at_approval=True) -- a fetch
                # failure here just means no baseline gets compared later, it
                # never blocks staging itself.
                try:
                    listing_for_baseline = EtsyAPIClient().get_listing(int(ti["listing_id"]))
                    payload["_state_at_staging"] = listing_for_baseline.get("state")
                except Exception as exc:
                    print(f"[stage:{name}] baseline fetch for listing {ti['listing_id']} failed (non-blocking): {exc}", flush=True)
            if ti.get("action_type") == "publish_listing" and ti.get("listing_id"):
                # Capture-now-render-later snapshot for the Detailed Action Review
                # mock listing preview — taken at staging time so the card Scott
                # sees doesn't depend on the listing still existing/unchanged later.
                try:
                    client = EtsyAPIClient()
                    listing = listing_for_baseline or client.get_listing(int(ti["listing_id"]))
                    images = client.get_listing_images(int(ti["listing_id"]))
                    thumb = ""
                    if images:
                        img = images[0]
                        thumb = img.get("url_570xN") or img.get("url_fullxfull") or img.get("url_75x75", "")
                    payload["preview"] = {
                        "title": payload.get("title") or listing.get("title", ""),
                        "price": _price_float(listing.get("price")),
                        "tags": payload.get("tags") or listing.get("tags", [])[:13],
                        "thumbnail_url": thumb,
                        "photo_count": len(images),
                    }
                except Exception as exc:
                    payload["preview"] = {"error": str(exc)}
            candidate = {"type": ti.get("action_type"), "payload": payload}
            ok, msg = _validate_staged_action(candidate)
            if not ok:
                return {"staged": False, "error": msg}
            aid = db.enqueue_action(ti.get("action_type"), ti.get("summary", ""), payload)
            return {
                "staged": True,
                "action_id": aid,
                "status": "pending",
                "note": f"Queued for {business_config.OWNER_NAME}'s approval in the Action Center — not yet applied.",
            }
        if name == "execute_command":
            ti = tool_input or {}
            cmd_name = ti.get("command", "")
            extra_args = ti.get("extra_args", "").strip()
            if cmd_name not in _EXEC_COMMANDS:
                return {"error": f"Unknown command '{cmd_name}'. Available: {list(_EXEC_COMMANDS.keys())}"}
            if extra_args:
                bad = [p for p in extra_args.split() if any(f in p.lower() for f in _FORBIDDEN_EXEC_FLAGS)]
                if bad:
                    return {
                        "error": (
                            f"Refused: extra_args {bad} would mutate live listings, which must go "
                            f"through {business_config.OWNER_NAME}'s approval. Run the read-only check, then use stage_action."
                        )
                    }
            return _run_exec_command(cmd_name, extra_args)
        if name == "local_speak":
            text = (tool_input or {}).get("text", "")
            db.log_activity("frank", "local_speak", text[:500], {"text": text}, outcome="ok")
            return {"spoken": True, "text": text}
        if name == "get_orders":
            limit = min(int((tool_input or {}).get("limit", 25) or 25), 100)
            data = EtsyAPIClient().get_orders(limit=limit)
            slim = []
            for r in data.get("results", []) or []:
                gt = r.get("grandtotal", {}) or {}
                divisor = gt.get("divisor", 100) or 100
                slim.append({
                    "order_id": r.get("receipt_id"),
                    "buyer_name": r.get("name"),
                    "total": round(gt.get("amount", 0) / divisor, 2),
                    "item_count": len(r.get("transactions", []) or []),
                    "created": datetime.fromtimestamp(
                        r.get("create_timestamp", 0), tz=timezone.utc
                    ).strftime("%Y-%m-%d") if r.get("create_timestamp") else None,
                })
            return {"count": len(slim), "orders": slim}
        if name == "get_reviews":
            limit = min(int((tool_input or {}).get("limit", 25) or 25), 100)
            data = EtsyAPIClient().get_reviews(limit=limit)
            slim = [
                {
                    "transaction_id": r.get("transaction_id"),
                    "listing_id": r.get("listing_id"),
                    "rating": r.get("rating"),
                    "review": r.get("review"),
                    "created": datetime.fromtimestamp(
                        r.get("create_timestamp", 0), tz=timezone.utc
                    ).strftime("%Y-%m-%d") if r.get("create_timestamp") else None,
                }
                for r in data.get("results", []) or []
            ]
            return {"count": len(slim), "reviews": slim}
        if name == "log_learning":
            note = ((tool_input or {}).get("note") or "").strip()
            if not note:
                return {"error": "note is required"}
            _append_ceo_learning(note)
            return {"logged": True}
        if name == "list_todos":
            return {"todos": db.list_todos()}
        if name == "add_todo":
            text = ((tool_input or {}).get("text") or "").strip()
            if not text:
                return {"error": "text is required"}
            todo_id = db.add_todo(text, added_by="frank")
            return {"added": True, "id": todo_id}
        if name == "complete_todo":
            todo_id = (tool_input or {}).get("todo_id")
            if todo_id is None:
                return {"error": "todo_id is required"}
            ok = db.set_todo_done(int(todo_id), True)
            return {"done": ok}
        if name == "autofix_listing_tags":
            ti = tool_input or {}
            lid = ti.get("listing_id")
            if lid is None:
                return {"error": "listing_id is required"}
            return asyncio.run(_autofix_tags_core(int(lid), reason=ti.get("reason", "")))
        if name == "autofix_listing_title":
            ti = tool_input or {}
            lid = ti.get("listing_id")
            if lid is None:
                return {"error": "listing_id is required"}
            return asyncio.run(_autofix_title_core(int(lid), reason=ti.get("reason", "")))
        if name == "stage_batch_tag_update":
            ti = tool_input or {}
            listing_ids = ti.get("listing_ids") or []
            if not listing_ids:
                return {"error": "listing_ids is required"}
            if len(listing_ids) > 10:
                return {
                    "error": (
                        f"Refused: {len(listing_ids)} listing_ids exceeds the 10-listing cap "
                        f"for a single batch. Split this into smaller batches and ask {business_config.OWNER_NAME} "
                        "which subset to run first."
                    )
                }
            client = EtsyAPIClient()
            listings = []
            fetch_errors = []
            for lid in listing_ids:
                try:
                    listings.append(client.get_listing(int(lid)))
                except Exception as exc:
                    fetch_errors.append({"listing_id": lid, "error": str(exc)})
            if not listings:
                return {"staged": [], "count": 0, "errors": fetch_errors}
            try:
                tag_results = _generate_tags_for_listings(listings, ti.get("reason", ""))
            except Exception as exc:
                return {"error": f"Tag generation failed: {exc}", "errors": fetch_errors}
            listing_map = {l["listing_id"]: l for l in listings}
            staged = []
            errors = list(fetch_errors)
            for res in tag_results:
                lid = res.get("listing_id")
                raw_tags = res.get("tags", [])
                listing = listing_map.get(lid, {})
                title_short = (listing.get("title") or f"Listing {lid}")[:50]
                tags = [_clean_tag(t) for t in raw_tags if str(t).strip()]
                seen: set[str] = set()
                tags = [t for t in tags if t and not (t in seen or seen.add(t))]
                payload = {"listing_id": lid, "tags": tags, "_state_at_staging": listing.get("state")}
                candidate = {"type": "update_tags", "payload": payload}
                ok, msg = _validate_staged_action(candidate)
                if not ok:
                    errors.append({"listing_id": lid, "title": title_short, "error": msg})
                    continue
                summary = f"Tag fix ({len(tags)}/13): {title_short}"
                aid = db.enqueue_action("update_tags", summary, payload)
                staged.append({"listing_id": lid, "action_id": aid, "tags": tags})
            with _cache_lock:
                _cache.pop("actions", None)
            return {"staged": staged, "count": len(staged), "errors": errors}
        if name == "toggle_listing_state":
            ti = tool_input or {}
            lid = ti.get("listing_id")
            new_state = ti.get("new_state")
            if lid is None:
                return {"error": "listing_id is required"}
            payload = {"listing_id": lid, "new_state": new_state}
            try:
                payload["_state_at_staging"] = EtsyAPIClient().get_listing(int(lid)).get("state")
            except Exception as exc:
                print(f"[stage:{name}] baseline fetch for listing {lid} failed (non-blocking): {exc}", flush=True)
            candidate = {"type": "toggle_listing_state", "payload": payload}
            ok, msg = _validate_staged_action(candidate)
            if not ok:
                return {"staged": False, "error": msg}
            aid = db.enqueue_action("toggle_listing_state", ti.get("summary", ""), payload)
            return {
                "staged": True,
                "action_id": aid,
                "status": "pending",
                "note": f"Queued for {business_config.OWNER_NAME}'s approval in the Action Center — not yet applied.",
            }
        if name == "get_conversion_targets":
            return asyncio.run(_get_conversion_targets_core())
        if name == "diagnose_listing_conversion":
            ti = tool_input or {}
            lid = ti.get("listing_id")
            if lid is None:
                return {"error": "listing_id is required"}
            return asyncio.run(_diagnose_listing_core(int(lid)))
        if name == "register_command":
            ti = tool_input or {}
            payload = {
                "command_name": ti.get("command_name"),
                "script_path": ti.get("script_path"),
                "description": ti.get("description", ""),
                "timeout": ti.get("timeout"),
                "long_running": bool(ti.get("long_running", False)),
            }
            if ti.get("args"):
                payload["args"] = ti["args"]
            candidate = {"type": "register_command", "payload": payload}
            ok, msg = _validate_staged_action(candidate)
            if not ok:
                return {"staged": False, "error": msg}
            aid = db.enqueue_action(
                "register_command",
                f"Register new command: {payload['command_name']} ({payload['script_path']})",
                payload,
            )
            return {
                "staged": True,
                "action_id": aid,
                "status": "pending",
                "note": f"Queued for {business_config.OWNER_NAME}'s approval in the Action Center — not yet registered.",
            }
        if name == "read_knowledge_base_doc":
            ti = tool_input or {}
            query = (ti.get("query") or "").strip()
            filename = (ti.get("filename") or "").strip()
            if query:
                return {"query": query, "results": _kb_search(query)}
            if filename:
                try:
                    target = _resolve_kb_doc(filename)
                except HTTPException as exc:
                    return {"error": exc.detail, "category": "not_found", "retryable": False}
                text = target.read_text()
                return {"filename": filename, "title": _kb_title(target, text), "content": text}
            docs = _kb_docs()
            docs.append({
                "filename": "CLAUDE.md",
                "title": "Project Instructions (CLAUDE.md)",
                "note": "Full operating rules: product specs, quality gates, autonomy boundaries, pricing tables.",
            })
            return {"docs": docs}
        if name == "find_business_gaps":
            return _find_business_gaps_impl()
        if name == "browse_web":
            from tools.browser_agent import get_page_text
            url = (tool_input or {}).get("url", "")
            if not url.startswith("https://") and not url.startswith("http://"):
                return {"error": "URL must start with https://"}
            text = get_page_text(url)
            return {"url": url, "text": text, "chars": len(text)}
        if name == "search_etsy":
            from tools.browser_agent import search_etsy
            query = (tool_input or {}).get("query", "")
            limit = min(int((tool_input or {}).get("limit", 10)), 20)
            results = search_etsy(query, limit)
            return {"query": query, "count": len(results), "results": results}
        if name == "check_listing_quality":
            from tools.listing_qc import check_listing
            return check_listing(
                title=(tool_input or {}).get("title", ""),
                tags=(tool_input or {}).get("tags", []),
                description=(tool_input or {}).get("description", ""),
                price=float((tool_input or {}).get("price", 0)),
                product_type=(tool_input or {}).get("product_type", "auto"),
            )
        if name == "generate_video":
            import video_generator
            ti = tool_input or {}
            listing_id = ti.get("listing_id")
            if not listing_id:
                return {"error": "listing_id is required"}
            style = ti.get("style", "showcase")
            if style not in video_generator.STYLES:
                return {"error": f"style must be one of {list(video_generator.STYLES)}"}
            client = EtsyAPIClient()
            imgs, listing = video_generator.fetch_listing_images(int(listing_id), client)
            title = listing.get("title", "")
            price = video_generator.get_price_str(listing)
            digital = video_generator.is_digital(listing)
            out_path = video_generator.generate_video(
                imgs, title, style, listing_id, price=price, digital=digital
            )
            return {
                "ok": True,
                "path": out_path.name,
                "size_human": _human_size(out_path.stat().st_size),
                "note": (
                    f"Video saved to data/social/videos/{out_path.name} — "
                    "ready to download or post via the Studio tab."
                ),
            }
        return {"error": f"unknown tool: {name}"}
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out (>{timeout}s)", "category": "transient", "retryable": True}
    except Exception as exc:
        category, retryable = classify_tool_exception(exc)
        return {"error": str(exc), "category": category, "retryable": retryable}


_ACTIVE_LISTING_GOAL = 60  # data/knowledge_base/action_plan_2026.md: "At 60-100 listings | $1,000-$3,000"


def _find_business_gaps_impl() -> dict:
    """Read-only diagnostic sweep, trimmed from ceo_agent.py's tool_find_gaps/tool_audit_catalog
    and adapted to this repo's real data. Never builds agents, never stages or executes anything --
    every finding here is for Scott to read and decide on, not for Frank to act on unilaterally."""
    gaps: list[dict] = []

    try:
        active = _listings_sync("active")
        count = active.get("count", 0)
        if count < _ACTIVE_LISTING_GOAL:
            gaps.append({
                "gap_type": "listing_volume",
                "urgency": "high" if count < _ACTIVE_LISTING_GOAL * 0.5 else "medium",
                "gap": f"{count} active listings vs the {_ACTIVE_LISTING_GOAL}+ goal in action_plan_2026.md",
                "detail": "action_plan_2026.md projects $1,000-$3,000/mo at 60-100 active listings.",
                "action": f"Review the product roadmap and launch cadence with {business_config.OWNER_NAME}.",
            })
    except Exception as exc:
        gaps.append({
            "gap_type": "diagnostic_error",
            "urgency": "low",
            "gap": f"Could not fetch active listing count: {exc}",
            "action": "Retry once the Etsy API is reachable.",
        })

    try:
        history = db.get_quality_audit_history(limit=7)
        if not history:
            gaps.append({
                "gap_type": "missing_data",
                "urgency": "low",
                "gap": "No quality-audit history yet -- the audit loop hasn't completed a run.",
                "action": "Check agent_heartbeats for the quality_audit loop's status.",
            })
        elif len(history) >= 2:
            latest = history[-1]
            prior = history[:-1]
            avg_prior_failed = sum(h.get("failed", 0) for h in prior) / len(prior)
            if latest.get("failed", 0) > avg_prior_failed:
                gaps.append({
                    "gap_type": "quality_regression",
                    "urgency": "high" if latest.get("failed", 0) >= 1 else "medium",
                    "gap": f"Latest quality audit: {latest.get('failed')} failed "
                           f"(avg of prior {len(prior)} runs: {avg_prior_failed:.1f})",
                    "detail": latest.get("summary", ""),
                    "action": "Review ops_runbook.md and the failing listings before the next publish.",
                })
    except Exception as exc:
        gaps.append({
            "gap_type": "diagnostic_error",
            "urgency": "low",
            "gap": f"Could not read quality-audit history: {exc}",
            "action": "Check that the database is reachable.",
        })

    try:
        heartbeats = db.list_agent_heartbeats()
        for h in heartbeats:
            if h.get("status") == "error":
                gaps.append({
                    "gap_type": "loop_health",
                    "urgency": "high",
                    "gap": f"Background loop '{h.get('label') or h.get('name')}' is in an error state",
                    "detail": h.get("detail", ""),
                    "action": "Check ops_runbook.md for the matching escalation entry.",
                })
    except Exception as exc:
        gaps.append({
            "gap_type": "diagnostic_error",
            "urgency": "low",
            "gap": f"Could not read agent heartbeats: {exc}",
            "action": "Check that the database is reachable.",
        })

    for dep in ("etsy_api", "anthropic_api", "relay"):
        try:
            cb = db.get_circuit_breaker_state(dep)
            if cb and cb.get("state") == "open":
                gaps.append({
                    "gap_type": "dependency_down",
                    "urgency": "critical",
                    "gap": f"Circuit breaker for '{dep}' is open ({cb.get('consecutive_failures')} consecutive failures)",
                    "detail": f"Opened at {cb.get('opened_at')}",
                    "action": f"Diagnose {dep} connectivity before relying on anything that depends on it.",
                })
        except Exception as exc:
            gaps.append({
                "gap_type": "diagnostic_error",
                "urgency": "low",
                "gap": f"Could not read circuit breaker state for '{dep}': {exc}",
                "action": "Check that the database is reachable.",
            })

    try:
        pending = db.list_actions(status="pending", limit=200)
        if len(pending) >= 10:
            gaps.append({
                "gap_type": "approval_backlog",
                "urgency": "medium",
                "gap": f"{len(pending)} staged actions awaiting {business_config.OWNER_NAME}'s approval in the Action Center",
                "action": "Review the Action Center -- a growing backlog delays publishing.",
            })
    except Exception as exc:
        gaps.append({
            "gap_type": "diagnostic_error",
            "urgency": "low",
            "gap": f"Could not read pending actions: {exc}",
            "action": "Check that the database is reachable.",
        })

    # Honest gap, not a guess: no usage tracking exists yet for read_knowledge_base_doc calls,
    # so "under-used KB docs" can only be reported as an inventory, not real usage data.
    try:
        docs = _kb_docs()
        gaps.append({
            "gap_type": "missing_tracking",
            "urgency": "low",
            "gap": "No usage tracking exists for knowledge_base doc reads via read_knowledge_base_doc.",
            "detail": f"{len(docs)} docs available; cannot tell which are actually consulted vs ignored.",
            "action": "Log each read_knowledge_base_doc call (filename, timestamp) if this becomes worth tracking.",
        })
    except Exception as exc:
        gaps.append({
            "gap_type": "diagnostic_error",
            "urgency": "low",
            "gap": f"Could not read knowledge base docs: {exc}",
            "action": "Check that the database is reachable.",
        })

    urgency_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    gaps.sort(key=lambda g: -urgency_rank.get(g.get("urgency"), 0))
    return {
        "total_gaps": len(gaps),
        "gaps": gaps,
        "priority_gap": gaps[0] if gaps else None,
        "note": f"Read-only diagnostic sweep -- does not stage, build, or publish anything. For discussion with {business_config.OWNER_NAME}.",
    }


# ── CEO Suggestions system prompt ─────────────────────────────────────────────────

_SUGGESTIONS_SYSTEM = """\
You are the CEO Agent for OnBrandCraftz running a FULL SHOP DIAGNOSTIC.

You are given the shop's real data inline in the user message: metrics (revenue,
orders, active listings, sales, rating), the full list of ACTIVE listings, and all
DRAFT listings. Analyze ALL of it carefully before answering.

Write your response as a single valid JSON object. No markdown, no prose outside
the JSON — just the object.

JSON format (follow exactly):
{
  "headline": "one-sentence summary of where the shop stands right now, citing actual numbers",
  "score": <integer 1–10 overall shop health>,
  "top_win": "the single strongest thing working in the shop right now, with specifics",
  "top_risk": "the single biggest gap or threat, with specifics",
  "suggestions": [
    {
      "priority": "critical|high|medium|low",
      "category": "seo|conversion|pricing|inventory|content|reviews|operations",
      "title": "short action title (under 60 chars)",
      "detail": "specific observation referencing actual data you just read — title, tag count, view count, revenue figure, etc.",
      "action": "exact concrete next step Scott should take",
      "impact": "what this unlocks — revenue, ranking, conversion",
      "listing_id": <listing id integer if this is about a specific listing, else null>
    }
  ]
}

Rules for suggestions:
- 5 to 8 suggestions total, ordered critical → high → medium → low
- Every detail field must reference real data you read from the tools
- No generic advice — name the specific listing, the specific tag count, the specific number
- Prioritize by revenue impact and urgency
- If a draft has been sitting unpublished, call it out specifically
- If listings have 0 views after 7+ days, identify which ones and why
- Tag gaps (<13 tags), title length violations (>70 chars), and zero-view listings are high priority
\
""".replace("OnBrandCraftz", business_config.BUSINESS_NAME).replace("Scott", business_config.OWNER_NAME)


# ── Conversion Doctor system prompt (single listing deep-dive) ────────────────────

_CONVERSION_DOCTOR_SYSTEM = """\
You are the Conversion Doctor for OnBrandCraftz, an Etsy shop. You are handed ONE
listing that gets traffic but is NOT selling. Your job: diagnose the single most
likely reason it isn't converting, then prescribe ranked, specific fixes.

You will be given the listing's real data: title, price, photo count, tag count
and the tags, views, favorites, real units sold, and the full description text.

Diagnose against Etsy's 2026 conversion standards:
- HERO PHOTO drives click-through; <10 photos is a red flag; lifestyle thumbnail
  beats flat white background. Photo problems are the #1 conversion killer.
- PRICE: psychology endings (.99/.97/.49) outperform round numbers. A price far
  from the product's tier can suppress conversion in either direction.
- TITLE: ≤70 chars, primary keyword in first 40 chars, comma separators not pipes.
- TAGS: all 13 used, multi-word buyer-intent phrases, no title duplication.
- DESCRIPTION: first 1-2 sentences must hook + carry the primary keyword (mobile
  shows only this above the fold). Needs What's Included, compatibility, FAQ.
- FAVORITES BUT NO SALES is a price/trust signal — people want it but won't buy.
- The #1 shop rule: never claim anything untrue. Never suggest a fix that would
  make the listing misrepresent the actual product.

Return ONLY a valid JSON object — no markdown, no prose outside it:
{
  "primary_issue": "the single biggest reason it isn't converting, one sentence with specifics",
  "summary": "one-line plain-English read on this listing's situation, citing its real numbers",
  "fixes": [
    {
      "area": "photos|price|title|description|tags|trust",
      "priority": "critical|high|medium|low",
      "finding": "the specific observation from THIS listing's data (cite the number/text)",
      "fix": "the exact concrete change to make",
      "impact": "what this is expected to unlock for conversion"
    }
  ]
}

Rules:
- 3 to 5 fixes, ordered critical → high → low by conversion impact.
- Every finding must cite this listing's actual data — its photo count, its price,
  its tag count, a phrase from its title or description. No generic advice.
- If the title is fine, say so and move on — do not invent problems.
- Be honest and direct; Scott reads this on his phone.

The standards above are a fast-path summary for this diagnosis. If anything here ever
conflicts with data/knowledge_base/business_standards.md, that file is the source of truth.
\
""".replace("OnBrandCraftz", business_config.BUSINESS_NAME).replace("Scott", business_config.OWNER_NAME)


# ── Batch tag generation (one Claude call → 13 tags for N listings) ──────────────

_BATCH_TAG_PROMPT = """\
You are the Etsy SEO specialist for OnBrandCraftz, a shop selling:
- Kawaii digital planners (fillable PDF for GoodNotes, Notability, iPad) — $9.99–$14.99
- Kawaii sticker packs (PNG sheets for GoodNotes Elements) — $4.99–$9.99
- 3D-print SVG/3MF packs (multi-color Bambu Lab files) — $9.99–$14.99
- Printable wall art & signs (instant download) — $2.99–$14.99

Generate exactly 13 Etsy search tags for each listing below.

STRICT TAG RULES (enforced by code — any violation is auto-rejected):
1. Exactly 13 tags per listing
2. Each tag: 2–4 words, MAXIMUM 20 characters including spaces
3. No special characters, symbols, or punctuation
4. Lowercase only
5. Every tag must be unique within the listing
6. Do NOT duplicate any phrase already in the listing title
7. Use multi-word buyer-intent phrases — no single-word tags
8. Cover all search angles: product type, style, app/tool, room/use case, occasion, format

CANONICAL TAG SETS (use these exactly when the listing title matches):
- Life/Ultimate planner → digital planner,goodnotes planner,notability planner,ipad planner,kawaii planner,fillable planner,2026 life planner,kawaii sticker pack,instant download,printable planner,daily planner pdf,planner bundle,habit tracker pdf
- Student/School planner → student planner,digital planner,school planner,goodnotes planner,notability planner,ipad planner,academic planner,study planner,kawaii planner,fillable planner,back to school,instant download,kawaii sticker pack
- Budget/Finance planner → budget planner,finance planner,digital planner,goodnotes planner,money planner,ipad planner,fillable planner,savings planner,debt payoff planner,kawaii planner,instant download,budget tracker,2026 budget plan
- Fitness/Wellness planner → fitness planner,wellness planner,digital planner,goodnotes planner,health planner,ipad planner,habit tracker,meal planner pdf,kawaii planner,fillable planner,instant download,self care planner,2026 fitness plan

PRODUCT-SPECIFIC GUIDANCE:
- Digital planners: always include goodnotes planner, ipad planner, fillable planner, instant download, kawaii sticker pack
- SVG packs / 3D prints: always include 3d print svg, svg cut file, digital download, bambu lab svg, multi color print + theme tags
- Printable wall art: always include printable wall art, instant download, digital download + room/style/occasion tags
- Sticker packs: always include goodnotes stickers, digital stickers, planner stickers, kawaii stickers, instant download

Respond with ONLY a valid JSON array — no markdown, no explanation, no code fences:
[{"listing_id": 123, "tags": ["tag one","tag two","tag three","tag four","tag five","tag six","tag seven","tag eight","tag nine","tag ten","tag eleven","tag twelve","tag thirteen"]}, ...]

Each tags array MUST contain exactly 13 strings. Each string MUST be 20 characters or fewer.

The canonical tag sets and product guidance above are a fast-path summary for batch tagging.
If they ever conflict with data/knowledge_base/business_standards.md, that file is the source of truth.\
""".replace("OnBrandCraftz", business_config.BUSINESS_NAME)


_TITLE_FIX_PROMPT = (
    "Generate a new Etsy listing title for " + business_config.BUSINESS_NAME + ". Shop sells: kawaii digital planners "
    "(GoodNotes/iPad), sticker packs, 3D-print SVG packs, printable wall art.\n\n"
    "TITLE RULES (code-enforced — violation = rejection):\n"
    "1. Maximum 70 characters — hard limit (mobile ranking penalty above 70)\n"
    "2. First 20-30 characters = primary search keyword buyers type\n"
    "3. Comma separators only (no pipes)\n"
    "4. Include 'Instant Download' and either '2026' or 'Undated' for planners\n"
    "5. No keyword stuffing — natural buyer language\n\n"
    "Current listing:\n"
    "TITLE: {title}\n"
    "PRICE: ${price}\n"
    "TAGS: {tags}\n"
    "DESCRIPTION (first 500 chars): {desc}\n\n"
    "Return ONLY the new title string — no quotes, no explanation, no JSON. "
    "Must be 70 characters or fewer."
)


def _clean_tag(tag: str) -> str:
    """Normalise a tag: lowercase, strip special chars, collapse spaces, enforce 20-char limit."""
    tag = str(tag).strip().lower()
    tag = _re.sub(r"[^a-z0-9 ]", "", tag)
    tag = _re.sub(r" +", " ", tag).strip()
    if len(tag) > 20:
        tag = tag[:20].rsplit(" ", 1)[0] if " " in tag[:20] else tag[:20]
    return tag


def _friendly_error_message(exc: Exception) -> str:
    """Turn a raw Anthropic/network exception into a short, human-readable message.
    Never surface str(exc) directly to the dashboard or chat UI — a 2026-06-23
    incident showed a raw 'credit balance is too low' API dump leaking into Frank's
    chat bubble and the Suggestion Warmer widget. Callers should still log str(exc)
    server-side for debugging."""
    text = str(exc).lower()
    if "credit balance" in text or "credit_balance" in text:
        return f"{business_config.AGENT_NAME_SHORT}'s AI provider account is out of credits — let {business_config.OWNER_NAME} know to top up Anthropic billing."
    if "rate_limit" in text or "rate limit" in text or "429" in text:
        return f"{business_config.AGENT_NAME_SHORT}'s AI is rate-limited right now — try again in a moment."
    if "authentication" in text or "invalid x-api-key" in text or "401" in text:
        return f"{business_config.AGENT_NAME_SHORT}'s AI provider rejected the API key — let {business_config.OWNER_NAME} know to check the Anthropic credentials."
    if "overloaded" in text or "529" in text:
        return f"{business_config.AGENT_NAME_SHORT}'s AI provider is overloaded right now — try again shortly."
    return "Something went wrong talking to the AI provider — try again shortly."


def _extract_json_object(text: str) -> dict | list | None:
    """Pull a JSON object/array out of an LLM response that may have conversational
    preamble before a fenced code block (e.g. "Compiling the report now.\n\n```json\n{...}\n```").
    Tries, in order: a fenced ```json block anywhere in the text, a bare fenced block,
    then the outermost {...} span. Returns None if nothing parses."""
    text = text.strip()

    fence_match = _re.search(r"```(?:json|JSON)?\s*\n?(.*?)```", text, _re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _generate_tags_for_listings(listings: list[dict], reason: str = "") -> list[dict]:
    """Call Claude once per batch-of-40 and return [{listing_id, tags:[13]}, ...].

    Uses a single structured prompt that outputs clean JSON — no streaming needed.
    Falls back to an empty list if no API key is set. `reason` is optional human
    feedback (e.g. a Scott reject reason) folded in as explicit corrective guidance —
    only meaningful when called with a single listing (the reject-fix path)."""
    if not ANTHROPIC_KEY or not listings:
        return []

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    results: list[dict] = []
    batch_size = 40

    for start in range(0, len(listings), batch_size):
        batch = listings[start : start + batch_size]
        rows = []
        for l in batch:
            ct = ",".join(l.get("tags", [])) or "(none)"
            rows.append(
                f'ID:{l["listing_id"]} TITLE:"{(l.get("title") or "")[:80]}" '
                f'PRICE:${round(l.get("price", 0), 2)} TAGS:[{ct}]'
            )
        prompt = _BATCH_TAG_PROMPT + "\n\nListings:\n" + "\n".join(rows)
        if reason:
            prompt += (
                "\n\nREVIEWER REJECTED THE PREVIOUS TAG SET WITH THIS FEEDBACK — "
                f"fix this specifically:\n{reason}"
            )

        msg = _anthropic_create(
            client,
            model="claude-sonnet-4-6",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = msg.content[0].text.strip()
        batch_results = _extract_json_object(raw)
        if batch_results is None:
            raise ValueError(f"Could not parse tag-generation response: {raw[:200]!r}")
        results.extend(batch_results)

    return results


# ── Web UI ─────────────────────────────────────────────────────────────────────

_WEB_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content=""" + '"' + business_config.BUSINESS_NAME + '"' + """>
<meta name="theme-color" content="#0D1B2A">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
<link rel="icon" type="image/png" href="/static/icon-192.png">
<title>""" + business_config.BUSINESS_NAME + """</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
:root{
  --bg:#0D1B2A;--card:#162033;--border:#1e2d42;--gold:#C9A84C;--gold2:#e8c96a;
  --text:#e8edf2;--muted:#6b7d91;--green:#4caf82;--red:#e05555;
  --hdr:calc(52px + env(safe-area-inset-top,0px));
  --nav:calc(60px + env(safe-area-inset-bottom,0px))
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;overflow:hidden}
header{position:fixed;top:0;left:0;right:0;z-index:200;height:var(--hdr);background:var(--card);border-bottom:1px solid var(--border);display:flex;align-items:flex-end;justify-content:space-between;padding:0 16px 14px}
header h1{font-size:17px;font-weight:700;color:var(--gold)}
header span{font-size:12px;color:var(--muted)}
nav{position:fixed;bottom:0;left:0;right:0;z-index:200;height:var(--nav);background:var(--card);border-top:1px solid var(--border);display:flex;align-items:flex-start;padding-top:8px}
nav button{flex:1;background:none;border:none;color:var(--muted);font-size:10px;font-weight:600;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;cursor:pointer;transition:color .15s;height:44px;-webkit-tap-highlight-color:rgba(201,168,76,.15)}
nav button.active{color:var(--gold)}
nav button svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.screen{position:fixed;top:var(--hdr);left:0;right:0;bottom:var(--nav);overflow-y:auto;-webkit-overflow-scrolling:touch;padding:16px;display:none;background:var(--bg)}
.screen.active{display:block}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:12px}
.card-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.metric{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px}
.metric .label{font-size:11px;color:var(--muted);margin-bottom:4px;text-transform:uppercase;letter-spacing:.4px}
.metric .value{font-size:24px;font-weight:700;color:var(--text)}
.metric .sub{font-size:11px;color:var(--muted);margin-top:2px}
.metric.gold .value{color:var(--gold)}
.section-title{font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin:16px 0 8px}
.banner{background:#1a2d1a;border:1px solid #2d5a2d;border-radius:10px;padding:12px 14px;margin-bottom:12px;font-size:13px;color:#7ec87e}
.listing-item{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--border)}
.listing-item:last-child{border-bottom:none}
.thumb{width:52px;height:52px;border-radius:8px;object-fit:cover;background:var(--border);flex-shrink:0}
.thumb-placeholder{width:52px;height:52px;border-radius:8px;background:var(--border);flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:20px}
.listing-info{flex:1;min-width:0}
.listing-title{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.listing-meta{font-size:11px;color:var(--muted);margin-top:3px}
.listing-price{font-size:14px;font-weight:700;color:var(--gold);flex-shrink:0}
.badge{display:inline-block;font-size:10px;font-weight:600;padding:2px 7px;border-radius:20px;margin-left:6px}
.badge.draft{background:#1a2030;color:#6b8ab5;border:1px solid #2a3d5a}
.badge.active{background:#1a2d1a;color:#4caf82;border:1px solid #2d5a2d}
.nav-badge{position:absolute;top:2px;margin-left:14px;background:var(--red);color:#fff;font-size:9px;font-weight:700;min-width:15px;height:15px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px}
.act-card{background:var(--card);border:1px solid var(--border);border-left-width:4px;border-radius:10px;padding:13px 14px;margin-bottom:10px}
.act-card.high{border-left-color:var(--red)}
.act-card.medium{border-left-color:var(--gold)}
.act-card.low{border-left-color:#4a6b8a}
.act-sev{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:2px 7px;border-radius:10px}
.act-sev.high{background:#2d1a1a;color:#e07070}
.act-sev.medium{background:#2d2a1a;color:var(--gold2)}
.act-sev.low{background:#1a2330;color:#7ba0c2}
.act-title{font-size:14px;font-weight:600;margin:7px 0 4px;line-height:1.35}
.act-detail{font-size:12px;color:var(--muted);line-height:1.45}
.act-sug{font-size:12px;color:var(--text);margin-top:7px;padding-top:7px;border-top:1px solid var(--border)}
.act-sug b{color:var(--gold2);font-weight:600}
.act-btns{display:flex;gap:8px;margin-top:9px}
.act-btn{flex:1;text-align:center;padding:7px;border-radius:7px;font-size:12px;font-weight:600;cursor:pointer;border:1px solid var(--border);background:none;color:var(--muted);text-decoration:none}
.act-btn.primary{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.act-card.approval{border-left-color:var(--green);background:#13241c}
.act-sev.approval{background:#13241c;color:#5fcf9e;border:1px solid #2d5a44}
.act-btn.approve{background:var(--green);color:#06140d;border-color:var(--green)}
.act-btn.reject{color:#e08585;border-color:#5a2d2d}
.toggle-row{display:flex;gap:8px;margin-bottom:12px}
.toggle-btn{flex:1;padding:8px;border-radius:8px;border:1px solid var(--border);background:none;color:var(--muted);font-size:13px;font-weight:600;cursor:pointer;transition:all .15s}
.toggle-btn.active{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.chip-row{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.chip-btn{padding:6px 12px;border-radius:20px;border:1px solid var(--border);background:none;color:var(--muted);font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap}
.chip-btn.active{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.listing-detail{padding:2px 14px 12px;margin:-2px 0 10px;background:var(--card);border:1px solid var(--border);border-top:none;border-radius:0 0 10px 10px;font-size:12px}
.listing-detail .drow{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid var(--border)}
.listing-detail .drow:last-child{border-bottom:none}
.listing-detail .drow span{color:var(--muted)}
.listing-detail .drow b{font-weight:600;text-align:right}
#chat-wrap{position:fixed;top:var(--hdr);left:0;right:0;bottom:var(--nav);z-index:100;display:none;flex-direction:column;background:var(--bg)}
#chat-wrap.active{display:flex}
#msgs{flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:12px 16px;display:flex;flex-direction:column;gap:10px;min-height:0}
.bubble{max-width:82%;padding:10px 14px;border-radius:16px;font-size:14px;line-height:1.5;word-break:break-word}
.bubble.user{align-self:flex-end;background:var(--gold);color:#0D1B2A;border-bottom-right-radius:4px}
.bubble.bot{align-self:flex-start;background:var(--card);border:1px solid var(--border);border-bottom-left-radius:4px;white-space:pre-wrap}
.bubble.typing{color:var(--muted);font-style:italic}
.chips{display:flex;gap:8px;overflow-x:auto;padding:8px 16px;scrollbar-width:none;flex-shrink:0;border-top:1px solid var(--border)}
.chips::-webkit-scrollbar{display:none}
.chip{flex-shrink:0;padding:7px 14px;border-radius:20px;border:1px solid var(--border);background:var(--card);color:var(--muted);font-size:12px;cursor:pointer;white-space:nowrap}
.chip:active{border-color:var(--gold);color:var(--gold)}
.input-row{display:flex;gap:8px;padding:10px 16px;border-top:1px solid var(--border);background:var(--bg);flex-shrink:0}
#msg-input{flex:1;background:var(--card);border:1px solid var(--border);border-radius:22px;padding:10px 16px;color:var(--text);font-size:15px;outline:none}
#msg-input:focus{border-color:var(--gold)}
#send-btn{width:40px;height:40px;border-radius:50%;background:var(--gold);border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
#send-btn svg{width:18px;height:18px;stroke:#0D1B2A;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
#speak-btn{width:40px;height:40px;border-radius:50%;background:var(--card);border:1px solid var(--border);cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:18px;transition:background .15s,border-color .15s}
#speak-btn.on{background:var(--gold);border-color:var(--gold)}
.spinner{display:block;width:20px;height:20px;border:2px solid var(--border);border-top-color:var(--gold);border-radius:50%;animation:spin .7s linear infinite;margin:40px auto}
@keyframes spin{to{transform:rotate(360deg)}}
.empty{text-align:center;color:var(--muted);padding:40px 0;font-size:14px}
.star{color:var(--gold)}
#fab-top{position:fixed;bottom:calc(var(--nav) + 16px);right:16px;width:46px;height:46px;border-radius:50%;background:var(--gold);color:#0D1B2A;border:none;font-size:20px;font-weight:700;cursor:pointer;display:none;align-items:center;justify-content:center;box-shadow:0 4px 16px rgba(0,0,0,.55);z-index:150;line-height:1}
#fab-top.visible{display:flex}
.sug-card{background:var(--card);border:1px solid var(--border);border-left-width:4px;border-radius:10px;padding:13px 14px;margin-bottom:10px}
.sug-card .sug-p{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:2px 7px;border-radius:10px;border:1px solid currentColor;display:inline-block}
.sug-card .sug-title{font-size:14px;font-weight:600;margin:7px 0 4px;line-height:1.35}
.sug-card .sug-detail{font-size:12px;color:var(--muted);line-height:1.45}
.sug-card .sug-action{font-size:12px;color:var(--text);margin-top:7px;padding-top:7px;border-top:1px solid var(--border)}
.sug-card .sug-impact{font-size:11px;color:var(--muted);margin-top:5px}
.ceo-btn{width:100%;background:linear-gradient(135deg,var(--card) 0%,#1a2440 100%);border:1px solid var(--gold);color:var(--gold);border-radius:12px;padding:14px;font-size:14px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;margin-top:4px}
.collapse-btn{display:block;width:100%;text-align:center;padding:7px;background:none;border:1px solid var(--border);border-radius:8px;color:var(--muted);font-size:12px;cursor:pointer;margin:6px 0 10px;transition:all .15s}
.collapse-btn:active{border-color:var(--gold);color:var(--gold)}
.hub-section-btn{flex:1;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 8px;color:var(--muted);font-size:12px;font-weight:600;cursor:pointer;transition:all .15s;text-align:center}
.hub-section-btn.active{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.swatch{display:inline-block;width:16px;height:16px;border-radius:4px;vertical-align:middle;margin-right:4px;flex-shrink:0;border:1px solid rgba(255,255,255,.15)}
.cred-row{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--border)}
.cred-row:last-child{border-bottom:none}
.cred-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.posture-row{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--border)}
.posture-row:last-child{border-bottom:none}
.prod-card{background:var(--card);border:1px solid var(--border);border-left-width:4px;border-radius:10px;padding:13px 14px;margin-bottom:10px}
</style>
</head>
<body>
  <header>
    <h1>""" + business_config.BUSINESS_NAME + """</h1>
    <div style="text-align:right;line-height:1.4">
      <span id="hdr-sub">Dashboard</span>
      <div style="font-size:9px;color:var(--border);margin-top:1px">""" + _BUILD_ID + """</div>
    </div>
  </header>

  <div id="persist-banner" style="display:none;position:fixed;top:0;left:0;right:0;z-index:300;background:#3a1414;border-bottom:1px solid var(--red);color:#ffb3b3;font-size:12px;font-weight:600;padding:8px 14px;text-align:center">
    ⚠️ No durable storage attached — data and synced files will be lost on next redeploy. Attach a Railway Volume at /data.
  </div>

  <div id="screen-dash" class="screen active">
    <div class="card" id="todo-card" style="margin-bottom:14px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
        <div style="font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px">📋 To-Do — Scott + Frank</div>
        <span id="todo-count" style="font-size:11px;color:var(--gold);font-weight:600"></span>
      </div>
      <div id="todo-list"><div class="spinner" style="margin:10px auto"></div></div>
      <div style="display:flex;gap:6px;margin-top:10px">
        <input id="todo-input" type="text" placeholder="Add a to-do…" onkeydown="if(event.key==='Enter')addTodoItem()"
          style="flex:1;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:9px 12px;font-size:13px;color:var(--text)">
        <button onclick="addTodoItem()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer">Add</button>
      </div>
    </div>
    <div style="margin-bottom:8px">
      <button id="ceo-analyze-btn" class="ceo-btn" onclick="getCeoSuggestions(false)" style="display:none">
        <span>🎯</span><span>Ask """ + business_config.AGENT_NAME + """ to Analyze</span>
      </button>
      <div id="ceo-suggestions"><div class="card" style="text-align:center;padding:28px 16px"><div class="spinner" style="margin:0 auto 14px"></div><div style="color:var(--text);font-size:14px;font-weight:600">""" + business_config.AGENT_NAME + """ is analyzing your shop…</div><div style="color:var(--muted);font-size:12px;margin-top:6px">Pulling metrics · scanning all listings · checking drafts</div></div></div>
    </div>
    <div id="dash-content"><div class="spinner"></div></div>
    <div id="conv-doctor-wrap" style="margin-top:10px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin:16px 0 8px">
        <div style="font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px">🩺 Conversion Doctor</div>
        <button id="conv-collapse-btn" onclick="toggleConvPanel(this)" style="font-size:11px;color:var(--muted);background:none;border:1px solid var(--border);border-radius:8px;padding:4px 10px;cursor:pointer">▼ Show</button>
      </div>
      <div id="conv-doctor" style="display:none"></div>
    </div>
  </div>

  <div id="screen-actions" class="screen">
    <div style="display:flex;gap:8px;margin-bottom:14px">
      <button id="batch-tag-btn" onclick="batchStageTags(this)" style="flex:1;background:var(--card);border:1px solid var(--gold);color:var(--gold);border-radius:10px;padding:11px 14px;font-size:13px;font-weight:600;cursor:pointer;text-align:center">⚡ Stage All Tag Fixes</button>
    </div>
    <div id="actions-content"><div class="spinner"></div></div>
  </div>

  <div id="screen-listings" class="screen">
    <div class="toggle-row">
      <button class="toggle-btn active" onclick="loadListings('active',this)">Active</button>
      <button class="toggle-btn" onclick="loadListings('draft',this)">Drafts</button>
    </div>
    <div id="listings-content"><div class="spinner"></div></div>
  </div>

  <div id="screen-analytics" class="screen">
    <div class="toggle-row" id="analytics-period-row">
      <button class="toggle-btn" onclick="loadAnalytics(7,this)">7 Days</button>
      <button class="toggle-btn active" onclick="loadAnalytics(30,this)">30 Days</button>
      <button class="toggle-btn" onclick="loadAnalytics(90,this)">90 Days</button>
    </div>
    <div id="analytics-content"><div class="spinner"></div></div>
  </div>

  <div id="screen-hub" class="screen">
    <div style="display:flex;gap:6px;margin-bottom:14px">
      <button class="hub-section-btn active" onclick="showHubSection(&apos;brand&apos;,this)">🎨 Brand</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;products&apos;,this)">📦 Products</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;files&apos;,this)">📁 Files</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;studio&apos;,this)">🎬 Studio</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;creds&apos;,this)">🔑 Creds</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;security&apos;,this)">🛡️ Security</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;relay&apos;,this)">🔌 Relay</button>
    </div>
    <div id="hub-content"><div class="spinner"></div></div>
  </div>

  <div id="chat-wrap">
    <div id="msgs"></div>
    <div class="chips">
      <span class="chip" onclick="sendChip(this)">What should I focus on?</span>
      <span class="chip" onclick="sendChip(this)">How are sales?</span>
      <span class="chip" onclick="sendChip(this)">What's my next listing?</span>
      <span class="chip" onclick="sendChip(this)">Pricing advice</span>
      <span class="chip" onclick="sendChip(this)">SEO tips</span>
    </div>
    <div class="input-row">
      <button id="speak-btn" onclick="toggleSpeak()" title="Toggle voice — Frank speaks replies aloud">🔇</button>
      <input id="msg-input" type="text" placeholder="Ask """ + business_config.AGENT_NAME + """…" autocomplete="off">
      <button id="send-btn" onclick="sendMsg()">
        <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
  </div>

  <button id="fab-top" aria-label="Back to top">↑</button>

  <nav>
    <button class="active" onclick="showTab('dash',this)">
      <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
      Dash
    </button>
    <button onclick="showTab('actions',this)">
      <svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg><span id="nav-badge" class="nav-badge" style="display:none">0</span>
      Actions
    </button>
    <button onclick="showTab('analytics',this)">
      <svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
      Analytics
    </button>
    <button onclick="showTab('chat',this)">
      <svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      Chat
    </button>
    <button onclick="showTab('listings',this)">
      <svg viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
      Listings
    </button>
    <button onclick="showTab('hub',this)">
      <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      Hub
    </button>
  </nav>

<script>
const BASE = location.origin;
const WS_BASE = BASE.replace(/^http/, 'ws');
const TOKEN = """ + json.dumps(APP_TOKEN) + """;

let ws = null, wsReady = false, pendingMsg = null;
let _wsHeartbeat = null, _wsReconnectTimer = null, _wsRetries = 0, _wsManualClose = false;
// Stable per-device chat session so Frank's memory survives reconnects & reloads.
const CHAT_SESSION = (function(){
  let s = null;
  try { s = localStorage.getItem('chatSession'); } catch(e) {}
  if (!s) {
    s = (window.crypto && crypto.randomUUID) ? crypto.randomUUID()
        : 'sess-' + Date.now() + '-' + Math.random().toString(36).slice(2);
    try { localStorage.setItem('chatSession', s); } catch(e) {}
  }
  return s;
})();
let _analyticsDays = 30;
let _onListings = false;

function showTab(tab, btn) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('chat-wrap').classList.remove('active');
  btn.classList.add('active');
  document.getElementById('hdr-sub').textContent = {dash:'Dashboard',actions:'Action Center',analytics:'Analytics',chat:'Chat',listings:'Listings',hub:'Hub'}[tab];
  _onListings = (tab === 'listings');
  if (!_onListings) { const fab=document.getElementById('fab-top'); if(fab)fab.classList.remove('visible'); }
  if (tab === 'chat') {
    document.getElementById('chat-wrap').classList.add('active');
    if (!ws) initWS();
  } else {
    document.getElementById('screen-' + tab).classList.add('active');
    if (tab === 'listings') loadListings('active', document.querySelector('.toggle-btn'));
    if (tab === 'actions') loadActions();
    if (tab === 'analytics') loadAnalytics(_analyticsDays);
    if (tab === 'hub') loadHub();
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function escHtml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function fetchWithTimeout(url, opts, ms=12000){
  const c=new AbortController();
  const t=setTimeout(()=>c.abort(),ms);
  return fetch(url,{...opts,signal:c.signal}).finally(()=>clearTimeout(t));
}

// ── Shared To-Do (Scott + Frank) ────────────────────────────────────────────
async function loadTodos(){
  try {
    const r = await fetchWithTimeout(BASE+'/api/todos', {headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    const d = await r.json();
    renderTodos(d.todos || []);
  } catch(e) {
    document.getElementById('todo-list').innerHTML = '<div style="color:var(--muted);font-size:12px">Could not load to-dos.</div>';
  }
}
function renderTodos(items){
  const wrap = document.getElementById('todo-list');
  const cnt = document.getElementById('todo-count');
  const openN = items.filter(t=>!t.done).length;
  cnt.textContent = items.length ? (openN ? openN+' open' : 'all done ✓') : '';
  if (!items.length) { wrap.innerHTML = '<div style="color:var(--muted);font-size:12px">Nothing on the list yet — add one below.</div>'; return; }
  wrap.innerHTML = items.map(t => {
    const who = t.added_by === 'frank' ? '🤖 Frank' : '🧑 Scott';
    return '<div style="display:flex;align-items:flex-start;gap:8px;padding:7px 0;border-bottom:1px solid var(--border)'+(t.done?';opacity:.5':'')+'">'+
      '<input type="checkbox" '+(t.done?'checked':'')+' onchange="toggleTodoItem('+t.id+',this.checked)" style="margin-top:3px;flex-shrink:0;width:16px;height:16px;accent-color:var(--gold)">'+
      '<div style="flex:1;font-size:13px;color:var(--text)'+(t.done?';text-decoration:line-through':'')+'">'+escHtml(t.text)+
        '<div style="font-size:10px;color:var(--muted);margin-top:2px">'+who+'</div></div>'+
      '<button onclick="deleteTodoItem('+t.id+')" style="background:none;border:none;color:var(--muted);font-size:14px;cursor:pointer;padding:2px 4px">✕</button>'+
    '</div>';
  }).join('');
}
async function addTodoItem(){
  const inp = document.getElementById('todo-input');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  try {
    await fetchWithTimeout(BASE+'/api/todos', {
      method:'POST',
      headers:{'Content-Type':'application/json',Authorization:'Bearer '+TOKEN},
      body: JSON.stringify({text, added_by:'scott'}),
    }, 15000);
  } catch(e) {}
  loadTodos();
}
async function toggleTodoItem(id, done){
  try {
    await fetchWithTimeout(BASE+'/api/todos/'+id+'/toggle', {
      method:'POST',
      headers:{'Content-Type':'application/json',Authorization:'Bearer '+TOKEN},
      body: JSON.stringify({done}),
    }, 15000);
  } catch(e) {}
  loadTodos();
}
async function deleteTodoItem(id){
  try {
    await fetchWithTimeout(BASE+'/api/todos/'+id, {method:'DELETE',headers:{Authorization:'Bearer '+TOKEN}}, 15000);
  } catch(e) {}
  loadTodos();
}

// ── Action Center ────────────────────────────────────────────────────────────
let _actions = [];
let _pendingActions = [];
let _actionsSummary = {high:0,medium:0,low:0};
let _actionFilter = null; // 'high' | 'medium' | 'low' | null (= all)
function setActionBadge(summary, pending) {
  const b = document.getElementById('nav-badge');
  if (!b) return;
  const n = ((summary && summary.high) || 0) + (pending || 0);  // urgent + awaiting approval
  if (n > 0) { b.textContent = n > 99 ? '99+' : n; b.style.display = ''; }
  else { b.style.display = 'none'; }
}
function simpleLineDiff(before, after) {
  const b = String(before == null ? '' : before).split('\\n');
  const a = String(after == null ? '' : after).split('\\n');
  const max = Math.max(b.length, a.length);
  let html = '';
  for (let i = 0; i < max; i++) {
    const bl = b[i], al = a[i];
    if (bl === al) {
      if (bl !== undefined) html += `<div style="color:#7a8a9a">&nbsp;&nbsp;${escHtml(bl)}</div>`;
    } else {
      if (bl !== undefined) html += `<div style="color:#e05555">-&nbsp;${escHtml(bl)}</div>`;
      if (al !== undefined) html += `<div style="color:#4ade80">+&nbsp;${escHtml(al)}</div>`;
    }
  }
  return html;
}
function renderApproval(a) {
  const p = a.payload || {};
  let preview = '';
  if (a.type === 'update_title') preview = 'New title: ' + escHtml(p.title || '');
  else if (a.type === 'update_tags') preview = 'New tags: ' + escHtml((p.tags || []).join(', '));
  else if (a.type === 'publish_listing') {
    const pv = p.preview || {};
    preview = `<div style="display:flex;gap:10px;align-items:flex-start">` +
      (pv.thumbnail_url
        ? `<img class="thumb" src="${escHtml(pv.thumbnail_url)}" loading="lazy" style="width:70px;height:70px;border-radius:8px;object-fit:cover;flex-shrink:0">`
        : `<div class="thumb-placeholder" style="width:70px;height:70px;flex-shrink:0">🏷️</div>`) +
      `<div><div>Publish draft listing ${escHtml(String(p.listing_id || ''))}</div>` +
      (pv.title ? `<div style="font-weight:600;margin-top:4px">${escHtml(pv.title)}</div>` : '') +
      (pv.price != null ? `<div>$${escHtml(String(pv.price))} · ${(pv.tags || []).length} tags · ${pv.photo_count || 0} photos</div>` : '') +
      (pv.error ? `<div style="color:#C9A84C">⚠️ Preview unavailable: ${escHtml(pv.error)}</div>` : '') +
      `</div></div>`;
  }
  else if (a.type === 'local_write_file') {
    const diffHtml = simpleLineDiff(p.before, p.after);
    preview = `<div style="margin-bottom:6px"><strong>File:</strong> ${escHtml(p.path || '')}</div>` +
      (p.before_existed === false ? `<div style="color:#C9A84C;margin-bottom:6px">⚠️ File does not currently exist — this will create it.</div>` : '') +
      `<div style="max-height:260px;overflow:auto;background:#0a1420;border-radius:8px;padding:8px;font-family:monospace;font-size:12px;white-space:pre-wrap">${diffHtml || '<span style="color:#7a8a9a">No changes</span>'}</div>`;
  }
  else if (a.type === 'local_delete') {
    preview = `<div style="color:#e05555">⚠️ This will permanently delete:</div><div style="font-family:monospace;margin-top:4px">${escHtml(p.path || '')}</div>`;
  }
  else if (a.type === 'local_exec') {
    preview = `<div><strong>Run:</strong> <span style="font-family:monospace">${escHtml(p.command || '')}${p.extra_args ? ' ' + escHtml(p.extra_args) : ''}</span></div>`;
  }
  return `<div class="act-card approval">
    <span class="act-sev approval">awaiting you</span>
    <div class="act-title">${escHtml(a.summary || a.type)}</div>
    <div class="act-detail">${preview}</div>
    <div class="act-btns">
      <button class="act-btn approve" onclick="approveAction(${a.id})">Approve &amp; Apply</button>
      ${a.type === 'publish_listing' ? `<button class="act-btn" onclick="fixDraftStage(${(p.listing_id||0)},${a.id},this)">🤖 Fix Draft</button>` : ''}
      <button class="act-btn reject" onclick="rejectAction(${a.id})">Reject</button>
    </div>
  </div>`;
}
const _APPROVE_CONFIRM_MSGS = {
  local_write_file: 'Approve and write this file on your computer now?',
  local_delete: 'Approve and PERMANENTLY DELETE this file on your computer now?',
  local_exec: 'Approve and run this command on your computer now?'
};
async function approveAction(id) {
  const act = (_pendingActions || []).find(x => x.id === id);
  const msg = (act && _APPROVE_CONFIRM_MSGS[act.type]) || 'Approve and apply this change to your live Etsy listing now?';
  if (!confirm(msg)) return;
  try {
    const r = await fetchWithTimeout(BASE+'/api/queue/'+id+'/approve', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 50000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    loadActions();
  } catch(e) { alert('Could not apply: ' + (e.message||e)); }
}
async function rejectAction(id) {
  try {
    const r = await fetchWithTimeout(BASE+'/api/queue/'+id+'/reject', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    if (!r.ok) { const d = await r.json().catch(()=>({})); throw new Error(d.detail||'HTTP '+r.status); }
    loadActions();
  } catch(e) { alert('Could not reject: ' + (e.message||e)); }
}
async function fixDraftStage(listingId, actionId, btn) {
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = '⏳ Fixing…';
  try {
    const r = await fetchWithTimeout(BASE+'/api/autofix/draft/'+listingId,{method:'POST',headers:{Authorization:'Bearer '+TOKEN}},120000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    const n = d.staged_count||0;
    btn.textContent = n > 0 ? n+' fix'+(n>1?'es':'')+' staged ✅' : '⚠️ No auto-fixes';
    if (n > 0) { btn.style.background='var(--green)'; btn.style.color='#06140d'; }
    const errNote = (d.errors&&d.errors.length) ? '\\n\\nErrors: '+d.errors.join(', ') : '';
    alert('Staged '+n+' fix'+(n!==1?'es':'')+'.\\nApprove the new fixes in Action Center, then come back to approve Publish.'+errNote);
    loadActions();
  } catch(e) {
    btn.disabled = false; btn.textContent = orig;
    alert('Could not fix draft: '+(e.message||e));
  }
}
async function loadActions() {
  const el = document.getElementById('actions-content');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const [ar, qr] = await Promise.all([
      fetchWithTimeout(BASE+'/api/actions', {headers:{Authorization:'Bearer '+TOKEN}}, 25000),
      fetchWithTimeout(BASE+'/api/queue?status=pending', {headers:{Authorization:'Bearer '+TOKEN}}, 15000).catch(()=>null)
    ]);
    if (!ar.ok) { const e = await ar.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+ar.status); }
    const d = await ar.json();
    let pending = [];
    if (qr && qr.ok) { const qd = await qr.json().catch(()=>({})); pending = qd.actions || []; }
    _actions = d.actions || [];
    _pendingActions = pending;
    _actionsSummary = d.summary || {high:0,medium:0,low:0};
    setActionBadge(_actionsSummary, pending.length);
    renderActionsContent();
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadActions()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}
function setActionFilter(sev) {
  _actionFilter = (_actionFilter === sev) ? null : sev; // tap again to clear
  renderActionsContent();
}
const _SEV_COLORS = {high:'#e05555', medium:'#C9A84C', low:'#7ba0c2'};
function renderActionsContent() {
  const el = document.getElementById('actions-content');
  if (!el) return;
  const pending = _pendingActions || [];
  const s = _actionsSummary || {high:0,medium:0,low:0};
  let html = '';
  if (pending.length) {
    html += `<div class="section-title">⏳ Awaiting your approval (${pending.length})</div>`;
    html += pending.map(renderApproval).join('');
  }
  if (!_actions.length && !pending.length) { el.innerHTML = html || '<div class="empty">✅ All clear — no action items right now.</div>'; return; }
  const sevBtn = sev => {
    const active = _actionFilter === sev;
    const c = _SEV_COLORS[sev];
    const style = active
      ? `flex:1;text-align:center;padding:10px 6px;cursor:pointer;border-color:${c};background:${c}26`
      : 'flex:1;text-align:center;padding:10px 6px;cursor:pointer';
    return `<div class="metric" style="${style}" onclick="setActionFilter('${sev}')"><div class="value" style="color:${c};font-size:20px">${s[sev]||0}</div><div class="sub">${sev}${active?' ✓':''}</div></div>`;
  };
  html += `<div class="section-title">Flagged by scan${_actionFilter?` — showing ${_actionFilter} only`:''}</div><div style="display:flex;gap:8px;margin-bottom:14px">`+
    sevBtn('high')+sevBtn('medium')+sevBtn('low')+
    `</div>`;
  const filtered = _actionFilter ? _actions.filter(a => a.severity === _actionFilter) : _actions;
  if (!filtered.length) {
    html += `<div class="empty">No ${escHtml(_actionFilter)} severity items.</div>`;
  } else {
    html += filtered.map(a => {
      const i = _actions.indexOf(a);
      return `
      <div class="act-card ${escHtml(a.severity)}">
        <span class="act-sev ${escHtml(a.severity)}">${escHtml(a.severity)}</span>
        <div class="act-title">${escHtml(a.title)}</div>
        <div class="act-detail">${escHtml(a.detail)}</div>
        <div class="act-sug"><b>💡 Fix:</b> ${escHtml(a.suggestion)}</div>
        <div class="act-btns">
          <button class="act-btn primary" onclick="askActionFix(${i})">Ask CEO</button>
          ${a.url ? `<a class="act-btn" href="${escHtml(a.url)}" target="_blank">Open on Etsy</a>` : ''}
        </div>
      </div>`;
    }).join('');
  }
  el.innerHTML = html;
}
function askActionFix(i) {
  const a = _actions[i];
  if (!a) return;
  const chatBtn = document.querySelectorAll('nav button')[3]; // dash, actions, analytics, chat, listings
  showTab('chat', chatBtn);
  const q = 'How should I fix this? ' + a.title + ' — ' + a.detail;
  const inp = document.getElementById('msg-input');
  inp.value = q;
  sendMsg();
}

// ── Dashboard ──────────────────────────────────────────────────────────────
function _dashSkeleton() {
  const hr = new Date().getHours();
  const greet = hr<12?'Good morning':hr<17?'Good afternoon':'Good evening';
  const ds = new Date().toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});
  return `<div style="margin-bottom:16px"><div style="font-size:22px;font-weight:700">${greet}, Scott 👋</div><div style="color:var(--muted);font-size:13px;margin-top:4px">${ds}</div></div><div id="dash-err"></div><div class="section-title">Revenue</div><div class="card-row"><div class="metric gold"><div class="label">7-Day</div><div class="value" id="v-rev7">…</div><div class="sub" id="s-rev7">loading</div></div><div class="metric gold"><div class="label">30-Day</div><div class="value" id="v-rev30">…</div><div class="sub" id="s-rev30">loading</div></div></div><div class="section-title">Shop</div><div class="card-row"><div class="metric"><div class="label">Active</div><div class="value" id="v-active">…</div><div class="sub">listings</div></div><div class="metric"><div class="label">All-Time</div><div class="value" id="v-sales">…</div><div class="sub">sales</div></div></div><div id="m-reviews"></div><div id="dash-retry" style="display:none;text-align:center;margin-top:8px"><button onclick="fetchDashData()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
}
async function fetchDashData() {
  const setId = (id,val)=>{const e=document.getElementById(id);if(e)e.textContent=val;};
  const setErr = msg=>{const e=document.getElementById('dash-err');if(e)e.innerHTML=msg?`<div style="background:#2d1a1a;border:1px solid #5a2d2d;border-radius:10px;padding:10px 14px;margin-bottom:12px;font-size:12px;color:#e07070">${msg}</div>`:''};
  const showRetry = v=>{const r=document.getElementById('dash-retry');if(r)r.style.display=v?'':'none';};
  try {
    const r = await fetchWithTimeout(BASE+'/api/metrics',{headers:{Authorization:'Bearer '+TOKEN}},15000);
    if (!r.ok){const err=await r.json().catch(()=>({}));throw new Error(err.detail||'HTTP '+r.status);}
    const d = await r.json();
    const o=d.orders||{},l=d.listings||{},rev=d.reviews||{},sh=d.shop||{};
    if(o.error||sh.error){setErr('⚠️ Etsy data partially unavailable');showRetry(true);}else{setErr('');showRetry(false);}
    setId('v-rev7','$'+(o.revenue_7d||0).toFixed(2));setId('s-rev7',(o.last_7_days||0)+' orders');
    setId('v-rev30','$'+(o.revenue_30d||0).toFixed(2));setId('s-rev30',(o.last_30_days||0)+' orders');
    setId('v-active',sh.active_listing_count||l.active_count||0);setId('v-sales',sh.total_sales||0);
    if(rev.avg_rating){const rEl=document.getElementById('m-reviews');if(rEl)rEl.innerHTML=`<div class="section-title">Reviews</div><div class="card"><div style="display:flex;align-items:center;gap:12px"><div style="font-size:36px;font-weight:700;color:var(--gold)">${rev.avg_rating}</div><div><div class="star">${'★'.repeat(Math.round(rev.avg_rating))}${'☆'.repeat(5-Math.round(rev.avg_rating))}</div><div style="font-size:12px;color:var(--muted);margin-top:3px">${rev.total_count||0} reviews · ${rev.five_star_pct||0}% five-star</div></div></div></div>`;}
  } catch(e) {
    setErr('⚠️ '+(e.name==='AbortError'?'Request timed out — check connection':escHtml(e.message||'Failed to load')));
    setId('v-rev7','—');setId('s-rev7','');setId('v-rev30','—');setId('s-rev30','');
    setId('v-active','—');setId('v-sales','—');
    showRetry(true);
  }
}
function loadDash() {
  document.getElementById('dash-content').innerHTML = _dashSkeleton();
  fetchDashData();
  getCeoSuggestions(false);
}

// ── Listings ───────────────────────────────────────────────────────────────
let _lastState = 'active';
let _listings = [];
let _listingState = 'active';
let _sectionFilter = null; // null = all categories
let _sectionsMap = null;   // {shop_section_id: title}, fetched once and cached client-side
let _openDetailId = null;
async function _ensureSectionsLoaded() {
  if (_sectionsMap) return;
  try {
    const r = await fetchWithTimeout(BASE+'/api/shop-sections', {headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    const d = await r.json();
    _sectionsMap = {};
    (d.sections||[]).forEach(s => { _sectionsMap[s.shop_section_id] = s.title; });
  } catch(e) { _sectionsMap = {}; }
}
function _sectionLabel(id) {
  if (!id) return 'Uncategorized';
  return (_sectionsMap && _sectionsMap[id]) || ('Section '+id);
}
async function loadListings(state, btn) {
  if (btn) { document.querySelectorAll('.toggle-btn').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); }
  _lastState = state; _listingState = state; _sectionFilter = null; _openDetailId = null;
  const el = document.getElementById('listings-content');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    await _ensureSectionsLoaded();
    const r = await fetchWithTimeout(BASE+'/api/listings?state='+state, {headers:{Authorization:'Bearer '+TOKEN}}, 20000);
    if (!r.ok) { const err = await r.json().catch(()=>({})); throw new Error(err.detail||'HTTP '+r.status); }
    const d = await r.json();
    _listings = d.listings || [];
    renderListings();
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load listings')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadListings(_lastState)" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}
function setSectionFilter(key) {
  _sectionFilter = key;
  _openDetailId = null;
  renderListings();
}
function renderListings() {
  const el = document.getElementById('listings-content');
  if (!_listings.length) { el.innerHTML = '<div class="empty">No '+_listingState+' listings</div>'; return; }
  const seen = {}; const cats = [];
  _listings.forEach(l => {
    const key = String(l.shop_section_id || 'none');
    if (!seen[key]) { seen[key] = true; cats.push({key: key, label: _sectionLabel(l.shop_section_id)}); }
  });
  cats.sort((a,b) => a.label.localeCompare(b.label));
  let html = '';
  if (cats.length > 1) {
    html += '<div class="chip-row">';
    html += `<button class="chip-btn${_sectionFilter===null?' active':''}" onclick="setSectionFilter(null)">All (${_listings.length})</button>`;
    cats.forEach(c => {
      const n = _listings.filter(l => String(l.shop_section_id||'none')===c.key).length;
      html += `<button class="chip-btn${_sectionFilter===c.key?' active':''}" onclick="setSectionFilter('${c.key}')">${escHtml(c.label)} (${n})</button>`;
    });
    html += '</div>';
  }
  const filtered = _sectionFilter===null ? _listings : _listings.filter(l => String(l.shop_section_id||'none')===_sectionFilter);
  if (!filtered.length) { html += '<div class="empty">No listings in this category</div>'; el.innerHTML = html; return; }
  html += filtered.map(l => `
    <div class="listing-item" style="cursor:pointer" onclick="toggleListingDetail(${l.listing_id})">
      ${l.thumbnail_url ? `<img class="thumb" src="${escHtml(l.thumbnail_url)}" loading="lazy">` : `<div class="thumb-placeholder">🏷️</div>`}
      <div class="listing-info">
        <div class="listing-title">${escHtml(l.title)}</div>
        <div class="listing-meta">${l.views} views · ${l.num_favorers} ♥${l.sales!=null?' · '+l.sales+' sold':''}<span id="badge-${l.listing_id}" class="badge ${l.state==='active'?'active':'draft'}">${escHtml(l.state)}</span></div>
      </div>
      <div class="listing-price">$${(+l.price||0).toFixed(2)}</div>
    </div>
    <div id="detail-${l.listing_id}" class="listing-detail" style="display:none"></div>`).join('');
  el.innerHTML = html;
}
async function toggleListingDetail(listingId) {
  const panel = document.getElementById('detail-'+listingId);
  if (!panel) return;
  if (_openDetailId !== null && _openDetailId !== listingId) {
    const prev = document.getElementById('detail-'+_openDetailId);
    if (prev) prev.style.display = 'none';
  }
  if (_openDetailId === listingId) { panel.style.display = 'none'; _openDetailId = null; return; }
  const l = _listings.find(x => x.listing_id === listingId);
  if (!l) return;
  panel.style.display = 'block';
  _openDetailId = listingId;
  panel.innerHTML =
    `<div class="drow"><span>Listing ID</span><b>${listingId}</b></div>`+
    `<div class="drow"><span>Category</span><b>${escHtml(_sectionLabel(l.shop_section_id))}</b></div>`+
    `<div class="drow"><span>Views</span><b>${l.views}</b></div>`+
    `<div class="drow"><span>Favorites</span><b>${l.num_favorers}</b></div>`+
    (l.sales!=null ? `<div class="drow"><span>Sold</span><b>${l.sales}</b></div>` : '')+
    (l.conversion_pct!=null ? `<div class="drow"><span>Conversion</span><b>${l.conversion_pct}%</b></div>` : '')+
    `<div class="drow"><span>Price</span><b>$${(+l.price||0).toFixed(2)}</b></div>`+
    `<div id="files-${listingId}"><div class="drow"><span>Digital files</span><b>loading…</b></div></div>`+
    `<div style="margin-top:8px;display:flex;justify-content:flex-end;align-items:center;gap:10px">`+
    ((l.state==='active'||l.state==='inactive') ? `<button id="state-btn-${listingId}" class="act-btn" style="font-size:12px;padding:6px 12px" onclick="event.stopPropagation();toggleListingState(${listingId},this)">${l.state==='active'?'⏸️ Deactivate':'▶️ Activate'}</button>` : '')+
    `<a href="${escHtml(l.url)}" target="_blank" style="color:var(--gold);font-size:12px;text-decoration:none" onclick="event.stopPropagation()">Open on Etsy ↗</a>`+
    `</div>`;
  try {
    const r = await fetchWithTimeout(BASE+'/api/listings/'+listingId+'/files', {headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    const slot = document.getElementById('files-'+listingId);
    if (!slot) return;
    if (!r.ok) { slot.innerHTML = '<div class="drow"><span>Digital files</span><b>unavailable</b></div>'; return; }
    const d = await r.json();
    const files = d.files || [];
    if (!files.length) { slot.innerHTML = '<div class="drow"><span>Digital files</span><b>none attached</b></div>'; return; }
    slot.innerHTML = files.map(f => `<div class="drow"><span>📄 ${escHtml(f.filename||'file')}</span><b>${escHtml(f.size_human||'')}</b></div>`).join('');
  } catch(e) {
    const slot = document.getElementById('files-'+listingId);
    if (slot) slot.innerHTML = '<div class="drow"><span>Digital files</span><b>failed to load</b></div>';
  }
}
async function toggleListingState(listingId, btn) {
  const l = _listings.find(x => x.listing_id === listingId);
  if (!l) return;
  const newState = l.state === 'active' ? 'inactive' : 'active';
  if (!confirm((newState==='inactive'?'Deactivate':'Activate')+' this listing on Etsy now?')) return;
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = '⏳ Working…';
  try {
    const r = await fetchWithTimeout(BASE+'/api/listings/'+listingId+'/state?new_state='+newState, {method:'POST', headers:{Authorization:'Bearer '+TOKEN}}, 25000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    l.state = d.state || newState;
    btn.textContent = l.state==='active' ? '⏸️ Deactivate' : '▶️ Activate';
    btn.disabled = false;
    const badge = document.getElementById('badge-'+listingId);
    if (badge) { badge.textContent = l.state; badge.className = 'badge ' + (l.state==='active'?'active':'draft'); }
  } catch(e) {
    btn.disabled = false; btn.textContent = orig;
    alert('Could not change listing state: ' + (e.message||e));
  }
}

// ── Chat ───────────────────────────────────────────────────────────────────
function _clearStreaming(fallback) {
  const s = document.getElementById('bot-streaming');
  if (!s) return;
  s.id = '';
  s.classList.remove('typing');
  if (!s.textContent.trim() && fallback) s.textContent = fallback;
}
function _stopHeartbeat() { if (_wsHeartbeat) { clearInterval(_wsHeartbeat); _wsHeartbeat = null; } }
async function initWS() {
  if (_wsReconnectTimer) { clearTimeout(_wsReconnectTimer); _wsReconnectTimer = null; }
  _wsManualClose = false;
  let ticket;
  try {
    const r = await fetchWithTimeout(BASE+'/api/ws-ticket', {method:'POST', headers:{Authorization:'Bearer '+TOKEN}}, 10000);
    if (!r.ok) throw new Error('ticket request failed: '+r.status);
    ticket = (await r.json()).ticket;
  } catch(e) {
    addBubble('⚠️ Could not start chat session — reload to retry', 'bot');
    return;
  }
  ws = new WebSocket(WS_BASE + '/ws/chat?ticket=' + encodeURIComponent(ticket) + '&session=' + encodeURIComponent(CHAT_SESSION));
  ws.onopen = () => {
    wsReady = true; _wsRetries = 0;
    // Heartbeat keeps the socket warm through mobile carrier/proxy idle timeouts
    // (otherwise an idle socket dies in ~30-60s and the next message hits a dead pipe).
    _stopHeartbeat();
    _wsHeartbeat = setInterval(() => { if (ws && ws.readyState === 1) ws.send(JSON.stringify({type:'ping'})); }, 25000);
    if (pendingMsg) { ws.send(JSON.stringify({message:pendingMsg, session:CHAT_SESSION})); pendingMsg=null; }
  };
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.type === 'pong') return;
    const bot = document.getElementById('bot-streaming');
    if (d.type === 'tool' && bot) {
      bot.classList.add('typing');
      if (!bot.dataset.real) bot.textContent = '⚙ ' + d.content;
      scrollMsgs();
    } else if (d.type === 'chunk' && bot) {
      if (!bot.dataset.real) { bot.textContent = ''; bot.dataset.real = '1'; bot.classList.remove('typing'); }
      bot.textContent += d.content; scrollMsgs();
    } else if (d.type === 'speak') {
      _speakCalled = true;
      if (_speakEnabled) speakText(d.text);
    } else if (d.type === 'done') {
      const finalText = bot ? bot.textContent : '';
      _clearStreaming(); scrollMsgs();
      if (_speakEnabled && !_speakCalled && finalText.trim()) speakText(finalText);
      _speakCalled = false;
    } else if (d.type === 'error') {
      _clearStreaming(); addBubble('⚠️ ' + d.content, 'bot');
      _speakCalled = false;
    }
  };
  ws.onerror = () => { _clearStreaming(); };
  ws.onclose = e => {
    wsReady = false; ws = null; _stopHeartbeat();
    _clearStreaming();
    if (e.code === 4001) { addBubble('Auth failed — reload to reconnect', 'bot'); return; }
    // Auto-reconnect with capped backoff. Frank's memory is server-side (keyed by
    // CHAT_SESSION), so reconnecting silently resumes the same thread — no context lost.
    if (!_wsManualClose) {
      _wsRetries = Math.min(_wsRetries + 1, 5);
      const delay = Math.min(1000 * Math.pow(2, _wsRetries - 1), 15000);
      _wsReconnectTimer = setTimeout(() => { if (!ws) initWS(); }, delay);
    }
  };
}
function addBubble(text, who) {
  const el = document.createElement('div');
  el.className = 'bubble ' + who;
  el.textContent = text;
  document.getElementById('msgs').appendChild(el);
  scrollMsgs();
  return el;
}
function scrollMsgs() { const m=document.getElementById('msgs'); m.scrollTop=m.scrollHeight; }
function sendMsg() {
  const inp = document.getElementById('msg-input');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  _speakCalled = false;
  addBubble(text, 'user');
  const bot = addBubble('', 'bot typing');
  bot.id = 'bot-streaming';
  bot.textContent = '';
  if (wsReady) { ws.send(JSON.stringify({message:text})); }
  else { pendingMsg = text; if(!ws) initWS(); }
}
function sendChip(el) { document.getElementById('msg-input').value = el.textContent; sendMsg(); }
document.getElementById('msg-input').addEventListener('keydown', e => { if(e.key==='Enter') sendMsg(); });

// ── Voice speak-back ────────────────────────────────────────────────────────
let _speakEnabled = (localStorage.getItem('frankSpeak') === '1');
let _speakCalled = false;  // true if local_speak tool fired this turn (avoid double-speak)
(function _initSpeakBtn() {
  const btn = document.getElementById('speak-btn');
  if (!btn) return;
  if (_speakEnabled) { btn.classList.add('on'); btn.textContent = '🔊'; }
})();
function toggleSpeak() {
  _speakEnabled = !_speakEnabled;
  localStorage.setItem('frankSpeak', _speakEnabled ? '1' : '0');
  const btn = document.getElementById('speak-btn');
  if (btn) { btn.classList.toggle('on', _speakEnabled); btn.textContent = _speakEnabled ? '🔊' : '🔇'; }
}
async function speakText(text) {
  if (!text || !text.trim()) return;
  try {
    const r = await fetch(BASE+'/api/voice/speak', {
      method: 'POST',
      headers: {Authorization: 'Bearer '+TOKEN, 'Content-Type': 'application/json'},
      body: JSON.stringify({text: text.slice(0, 4000)})
    });
    if (!r.ok) return;
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.onended = () => URL.revokeObjectURL(url);
    audio.play().catch(() => {});
  } catch(e) { /* best effort — audio is non-critical */ }
}

// ── Studio (video generation) ──────────────────────────────────────────────
async function loadStudio() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  var genFormHtml = '<div class="card" style="margin-bottom:12px">'+
    '<div style="font-size:14px;font-weight:700;margin-bottom:10px">Generate Marketing Video</div>'+
    '<div style="font-size:12px;color:var(--muted);margin-bottom:10px">Ken Burns slideshow from a listing\'s photos — generates an MP4 ready for social media.</div>'+
    '<div style="display:flex;flex-direction:column;gap:8px">'+
    '<input id="studio-listing-id" type="number" placeholder="Etsy Listing ID" style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 12px;color:var(--text);font-size:13px">'+
    '<select id="studio-style" style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 12px;color:var(--text);font-size:13px">'+
    '<option value="showcase">Showcase — smooth pan across listing photos</option>'+
    '<option value="new-drop">New Drop — bold title card reveal</option>'+
    '<option value="feature">Feature — close-up detail focus</option>'+
    '<option value="minimal">Minimal — clean, quiet aesthetic</option>'+
    '</select>'+
    '<button onclick="studioGenerate(this)" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:12px;font-size:14px;font-weight:700;cursor:pointer">Generate Video</button>'+
    '</div></div>';
  el.innerHTML = genFormHtml + '<div id="studio-result"></div><div id="studio-videos"></div>';
  loadStudioVideos();
}
async function studioGenerate(btn) {
  var listingId = document.getElementById('studio-listing-id').value.trim();
  var style = document.getElementById('studio-style').value;
  var out = document.getElementById('studio-result');
  if (!listingId) { alert('Enter a listing ID first'); return; }
  btn.disabled = true;
  btn.textContent = '⏳ Generating — takes ~30s…';
  out.innerHTML = '<div class="spinner"></div>';
  try {
    var r = await fetchWithTimeout(BASE+'/api/studio/generate', {
      method: 'POST',
      headers: {Authorization: 'Bearer '+TOKEN, 'Content-Type': 'application/json'},
      body: JSON.stringify({listing_id: parseInt(listingId), style})
    }, 200000);
    var d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    var vidUrl = BASE+'/api/files/download?root=videos&path='+encodeURIComponent(d.path)+'&token='+TOKEN+'&inline=1';
    out.innerHTML = '<div class="card" style="margin-bottom:12px">'+
      '<div style="font-size:13px;font-weight:700;color:var(--green);margin-bottom:8px">✅ Video ready — '+escHtml(d.size_human)+'</div>'+
      '<video controls style="width:100%;border-radius:8px;background:#000" src="'+escHtml(vidUrl)+'"></video>'+
      '<a href="'+escHtml(vidUrl)+'" download="'+escHtml(d.path)+'" style="display:block;text-align:center;margin-top:8px;color:var(--gold);font-size:13px;font-weight:600">⬇ Download MP4</a>'+
      '</div>';
    loadStudioVideos();
  } catch(e) {
    out.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out — try again':e.message||'Generation failed')+'</div>';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Video';
  }
}
async function loadStudioVideos() {
  var el = document.getElementById('studio-videos');
  if (!el) return;
  try {
    var r = await fetchWithTimeout(BASE+'/api/studio/videos',{headers:{Authorization:'Bearer '+TOKEN}},10000);
    var d = await r.json().catch(function(){return {};});
    if (!r.ok || !d.videos || !d.videos.length) { el.innerHTML = ''; return; }
    var html = '<div class="section-title">Previously Generated ('+d.videos.length+')</div><div class="card">';
    d.videos.forEach(function(v){
      var vidUrl = BASE+'/api/files/download?root=videos&path='+encodeURIComponent(v.name)+'&token='+TOKEN+'&inline=1';
      html += '<div class="listing-item" style="cursor:default">'+
        '<div class="thumb-placeholder">🎬</div>'+
        '<div class="listing-info">'+
          '<div class="listing-title" style="font-size:13px">'+escHtml(v.name)+'</div>'+
          '<div class="listing-meta">'+escHtml(v.size_human)+'</div>'+
        '</div>'+
        '<a href="'+escHtml(vidUrl)+'" target="_blank" style="color:var(--gold);font-size:18px;text-decoration:none">↗</a>'+
      '</div>';
    });
    html += '</div>';
    el.innerHTML = html;
  } catch(e) { /* non-critical */ }
}

// ── Analytics ──────────────────────────────────────────────────────────────
function buildSparkline(values, color, h) {
  h = h || 64;
  values = (values || []).filter(function(v){ return v != null && !isNaN(v); });
  if (values.length < 2) return '<div style="height:'+h+'px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:12px">📈 Accumulating daily data…</div>';
  var W=320,H=h,mn=Math.min.apply(null,values),mx=Math.max.apply(null,values),range=mx-mn||1,pad=4;
  var pts=values.map(function(v,i){return [pad+(i/(values.length-1))*(W-pad*2), H-pad-((v-mn)/range)*(H-pad*2)];});
  var poly=pts.map(function(p){return p[0].toFixed(1)+','+p[1].toFixed(1);}).join(' ');
  var area='M'+pts[0][0].toFixed(1)+','+H+' '+pts.map(function(p){return 'L'+p[0].toFixed(1)+','+p[1].toFixed(1);}).join(' ')+' L'+pts[pts.length-1][0].toFixed(1)+','+H+' Z';
  var gid='sg'+Math.random().toString(36).slice(2,8);
  return '<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;height:'+H+'px;display:block;overflow:visible">'+
    '<defs><linearGradient id="'+gid+'" x1="0" y1="0" x2="0" y2="1">'+
    '<stop offset="0%" stop-color="'+color+'" stop-opacity="0.25"/>'+
    '<stop offset="100%" stop-color="'+color+'" stop-opacity="0"/>'+
    '</linearGradient></defs>'+
    '<path d="'+area+'" fill="url(#'+gid+')"/>'+
    '<polyline points="'+poly+'" fill="none" stroke="'+color+'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'+
    '<circle cx="'+pts[pts.length-1][0].toFixed(1)+'" cy="'+pts[pts.length-1][1].toFixed(1)+'" r="3.5" fill="'+color+'"/>'+
    '</svg>';
}
function _deltaSpan(val, isMoney) {
  if (val == null || val === 0) return '<span style="color:var(--muted)">— stable</span>';
  var pos=val>0, c=pos?'var(--green)':'var(--red)', a=pos?'↑':'↓';
  var n=isMoney?('$'+Math.abs(val).toFixed(2)):String(Math.round(Math.abs(val)));
  return '<span style="color:'+c+'">'+a+' '+n+'</span>';
}
function _renderAnalytics(d) {
  var tr=d.trends||{}, lt=d.latest||{}, del=d.delta||{}, days=d.days||30;
  var n=d.snapshot_count||0, top=d.top_listings||[];
  var html='';
  if (n < 3) {
    html+='<div style="background:#1a2030;border:1px solid #2a3d5a;border-radius:10px;padding:11px 14px;margin-bottom:14px;font-size:12px;color:#7ba0c2">📅 '+(n===0?'No snapshots yet — the hub records one daily snapshot at startup and midnight.':n+' day'+(n>1?'s':'')+' of history recorded. Trend charts fill in each day automatically.')+'</div>';
  }
  // Revenue
  var rev=lt.revenue_30d;
  html+='<div class="section-title">Revenue — Rolling 30 Days</div><div class="card">';
  html+=buildSparkline(tr.revenue_30d,'var(--gold)');
  if (rev!=null) {
    html+='<div style="margin-top:10px;display:flex;justify-content:space-between;align-items:flex-end">'+
      '<div><div style="font-size:26px;font-weight:700;color:var(--gold)">$'+rev.toFixed(2)+'</div>'+
      '<div style="font-size:11px;color:var(--muted);margin-top:2px">current 30-day window</div></div>'+
      '<div style="text-align:right;font-size:12px">'+_deltaSpan(del.revenue_30d,true)+'<div style="color:var(--muted);font-size:10px;margin-top:2px">vs '+days+'d ago</div></div>'+
      '</div>';
  }
  html+='</div>';
  // Orders
  var ord=lt.orders_30d;
  html+='<div class="section-title">Orders — Rolling 30 Days</div><div class="card">';
  html+=buildSparkline(tr.orders_30d,'#5ca8d4');
  if (ord!=null) {
    html+='<div style="margin-top:10px;display:flex;justify-content:space-between;align-items:flex-end">'+
      '<div><div style="font-size:26px;font-weight:700;color:#5ca8d4">'+ord+'</div>'+
      '<div style="font-size:11px;color:var(--muted);margin-top:2px">orders in rolling 30 days</div></div>'+
      '<div style="text-align:right;font-size:12px">'+_deltaSpan(del.orders_30d,false)+'<div style="color:var(--muted);font-size:10px;margin-top:2px">vs '+days+'d ago</div></div>'+
      '</div>';
  }
  html+='</div>';
  // Shop growth cards
  var acNow=lt.active_listings, salNow=lt.total_sales;
  if (acNow!=null||salNow!=null) {
    html+='<div class="section-title">Shop Growth</div><div class="card-row">';
    if (acNow!=null) html+='<div class="metric"><div class="label">Listings</div><div class="value">'+acNow+'</div><div class="sub" style="margin-top:5px;font-size:11px">'+_deltaSpan(del.active_listings,false)+' in '+days+'d</div></div>';
    if (salNow!=null) html+='<div class="metric"><div class="label">Total Sales</div><div class="value">'+salNow+'</div><div class="sub" style="margin-top:5px;font-size:11px">'+_deltaSpan(del.total_sales,false)+' in '+days+'d</div></div>';
    html+='</div>';
  }
  // Listing trend mini-sparkline
  var acTrend=(tr.active_listings||[]).filter(function(v){return v!=null;});
  if (acTrend.length>=2) {
    html+='<div class="card" style="padding:12px 14px 10px">'+buildSparkline(tr.active_listings,'var(--green)',40)+'<div style="font-size:11px;color:var(--muted);margin-top:5px">Active listings over time</div></div>';
  }
  // Top listings
  if (top.length) {
    html+='<div class="section-title">Top Listings by Views</div><div class="card" style="padding:12px 14px">';
    html+=top.map(function(l,i){
      // Real buy rate (sales÷views). Etsy avg is ~1-3%; 0% with views = a problem.
      var cp=l.conversion_pct||0, sold=l.sales||0;
      var convColor=cp>=2?'var(--green)':cp>=1?'var(--gold)':sold>0?'#7ba0c2':'var(--red)';
      return '<div class="listing-item" onclick="window.open(&apos;'+escHtml(l.url)+'&apos;,&apos;_blank&apos;)">'+
        '<div style="width:22px;font-size:12px;font-weight:700;color:var(--muted);flex-shrink:0">#'+(i+1)+'</div>'+
        '<div class="listing-info">'+
          '<div class="listing-title">'+escHtml(l.title)+'</div>'+
          '<div class="listing-meta">'+l.views+' views · '+l.num_favorers+' ♥ · <span style="color:'+convColor+'">'+sold+' sold ('+cp+'%)</span></div>'+
        '</div>'+
        '<div class="listing-price">$'+(+l.price||0).toFixed(2)+'</div>'+
        '</div>';
    }).join('');
    html+='</div>';
  } else {
    html+='<div class="section-title">Top Listings</div><div class="empty">View data will appear here once listings are active</div>';
  }
  // Footer
  var ts=lt.ts?new Date(lt.ts).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}):null;
  html+='<div style="text-align:center;color:var(--muted);font-size:11px;padding:12px 0 4px">'+(ts?'Last snapshot: '+ts:'No snapshots yet')+' · '+n+' day'+(n!==1?'s':'')+' of history</div>';
  return html;
}
async function loadAnalytics(days, btn) {
  if (btn) { document.querySelectorAll('#analytics-period-row .toggle-btn').forEach(function(b){b.classList.remove('active');}); btn.classList.add('active'); }
  if (days) _analyticsDays = days;
  var el = document.getElementById('analytics-content');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    var r = await fetchWithTimeout(BASE+'/api/analytics?days='+_analyticsDays, {headers:{Authorization:'Bearer '+TOKEN}}, 20000);
    if (!r.ok) { var e=await r.json().catch(function(){return {};}); throw new Error(e.detail||'HTTP '+r.status); }
    var d = await r.json();
    el.innerHTML = _renderAnalytics(d);
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadAnalytics()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}

// ── CEO Analysis (structured suggestion report) ────────────────────────────
let _lastSuggestions = null;

// Silent background refresh — called after showing a cached report so the display
// updates to fresh data without ever showing a spinner. 30s timeout; fails silently.
async function _bgRefreshSuggestions() {
  try {
    var r = await fetchWithTimeout(BASE+'/api/suggestions',{method:'POST',headers:{Authorization:'Bearer '+TOKEN}},30000);
    var d = await r.json().catch(function(){return {};});
    // Only update if we received a real, complete report (not a 202 warming stub)
    if (r.status===200 && d && Array.isArray(d.suggestions) && d.suggestions.length && !d.error) {
      var newer = !_lastSuggestions || (d.generated_at && d.generated_at > (_lastSuggestions.generated_at||''));
      if (newer) {
        _lastSuggestions = d;
        try { sessionStorage.setItem('obc_sug', JSON.stringify(d)); } catch(e2) {}
        var el2 = document.getElementById('ceo-suggestions');
        if (el2) { el2.innerHTML = _renderSuggestions(d); updateChips(d); }
      }
    }
  } catch(e) {}
}
const _PCOLOR = {critical:'var(--red)',high:'#e08030',medium:'var(--gold)',low:'#7ba0c2'};
const _PRANK  = {critical:0,high:1,medium:2,low:3};
function _renderSuggestions(d) {
  if (!d) return '';
  if (d.raw) return '<div class="card" style="font-size:13px;white-space:pre-wrap;color:var(--muted)">'+escHtml(d.raw)+'</div>';
  const ts = d.generated_at ? new Date(d.generated_at).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}) : '';
  const score = d.score;
  const scoreColor = score >= 7 ? 'var(--green)' : score >= 4 ? 'var(--gold)' : 'var(--red)';
  const scoreBg = score >= 7 ? '#13241c' : score >= 4 ? '#2d2a1a' : '#241313';
  let html = '<div class="card" style="margin-bottom:10px">';
  html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">';
  html += '<div style="font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.4px">CEO Report · ' + ts + '</div>';
  if (score) html += '<div style="background:'+scoreBg+';border:1px solid '+scoreColor+';border-radius:20px;padding:2px 10px;font-size:13px;font-weight:700;color:'+scoreColor+'">'+score+'/10</div>';
  html += '</div>';
  if (d.headline) html += '<div style="font-size:14px;line-height:1.5">'+escHtml(d.headline)+'</div>';
  html += '</div>';
  if (d.top_win || d.top_risk) {
    html += '<div class="card-row">';
    if (d.top_win)  html += '<div class="metric" style="background:#13241c;border-color:#2d5a44"><div class="label" style="color:#5fcf9e">✅ TOP WIN</div><div style="font-size:12px;line-height:1.45;margin-top:4px">'+escHtml(d.top_win)+'</div></div>';
    if (d.top_risk) html += '<div class="metric" style="background:#241313;border-color:#5a2d2d"><div class="label" style="color:#e07070">⚠️ TOP RISK</div><div style="font-size:12px;line-height:1.45;margin-top:4px">'+escHtml(d.top_risk)+'</div></div>';
    html += '</div>';
  }
  const sugs = (d.suggestions || []).slice().sort(function(a,b){ return (_PRANK[a.priority]||9)-(_PRANK[b.priority]||9); });
  if (sugs.length) {
    html += '<div class="section-title">Priorities</div>';
    sugs.forEach(function(s,i) {
      const pc = _PCOLOR[s.priority] || 'var(--muted)';
      html += '<div class="sug-card" style="border-left-color:'+pc+'">';
      html += '<span class="sug-p" style="color:'+pc+'">'+escHtml(s.priority||'medium')+'</span>';
      if (s.category) html += '<span style="font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);margin-left:6px">'+escHtml(s.category)+'</span>';
      html += '<div class="sug-title">'+escHtml(s.title)+'</div>';
      html += '<div class="sug-detail">'+escHtml(s.detail)+'</div>';
      if (s.action) html += '<div class="sug-action"><b style="color:var(--gold2)">→ </b>'+escHtml(s.action)+'</div>';
      if (s.impact) html += '<div class="sug-impact">💡 '+escHtml(s.impact)+'</div>';
      html += '<div class="act-btns">';
      if (s.listing_id) html += '<a class="act-btn" href="https://www.etsy.com/listing/'+escHtml(String(s.listing_id))+'" target="_blank">Open Listing</a>';
      html += '<button class="act-btn primary" onclick="askSuggestionFix('+i+')">🤖 Fix It</button>';
      html += '</div></div>';
    });
  }
  html += '<div style="text-align:center;margin:8px 0 4px"><button onclick="getCeoSuggestions(true)" style="background:none;border:1px solid var(--border);border-radius:8px;padding:8px 20px;font-size:12px;color:var(--muted);cursor:pointer">↻ Refresh analysis</button></div>';
  return '<button class="collapse-btn" onclick="toggleCeoPanel(this)">▲ Collapse CEO Analysis</button><div id="ceo-body">'+html+'</div>';
}
function toggleCeoPanel(btn) {
  const el = document.getElementById('ceo-body');
  if (!el) return;
  const hidden = el.style.display === 'none';
  el.style.display = hidden ? '' : 'none';
  btn.textContent = hidden ? '▲ Collapse CEO Analysis' : '▼ Show CEO Analysis';
}
async function getCeoSuggestions(forceRefresh, _attempt) {
  const btn = document.getElementById('ceo-analyze-btn');
  const el  = document.getElementById('ceo-suggestions');
  if (!el) return;
  _attempt = _attempt || 0;
  // Show cached report immediately — no spinner. A silent background fetch
  // checks whether the server has a newer report and updates the display when
  // it arrives. This means the dashboard is instant on every page reload even
  // right after a Railway deploy (which wipes the server-side in-memory cache).
  if (_lastSuggestions && !forceRefresh && !_attempt) {
    if(btn)btn.style.display='none';
    el.innerHTML=_renderSuggestions(_lastSuggestions);
    updateChips(_lastSuggestions);
    setTimeout(_bgRefreshSuggestions, 1500); // silent background check for newer data
    return;
  }
  if (btn) btn.style.display = 'none';
  if (!_attempt) el.innerHTML = '<div class="card" style="text-align:center;padding:28px 16px"><div class="spinner" style="margin:0 auto 14px"></div><div style="color:var(--text);font-size:14px;font-weight:600">""" + business_config.AGENT_NAME + """ is analyzing your shop…</div><div style="color:var(--muted);font-size:12px;margin-top:6px">Pulling metrics · scanning all listings · checking drafts</div></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/suggestions', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 120000);
    const d = await r.json().catch(function(){return {};});
    // 202 = the report is still being computed (cold cache, e.g. just after an
    // update). Keep the spinner and poll — never block the request for a minute.
    if (r.status === 202 || (d && d.status === 'warming')) {
      if (_attempt >= 25) throw new Error('Analysis is taking longer than usual');
      setTimeout(function(){ getCeoSuggestions(forceRefresh, _attempt + 1); }, 4000);
      return;
    }
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    _lastSuggestions = d;
    try { sessionStorage.setItem('obc_sug', JSON.stringify(d)); } catch(e2) {}
    el.innerHTML = _renderSuggestions(d);
    updateChips(d);
  } catch(e) {
    const msg = e.name==='AbortError' ? 'Analysis timed out — try again' : escHtml(e.message||'Failed');
    el.innerHTML = '<div class="empty">'+msg+'</div><div style="text-align:center;margin-top:8px"><button onclick="getCeoSuggestions(true)" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Try Again</button></div>';
    if (btn) btn.style.display = '';
  }
}
function updateChips(data) {
  const el = document.querySelector('.chips');
  if (!el) return;
  const sugs = ((data && data.suggestions) || [])
    .slice()
    .sort(function(a,b){ return (_PRANK[a.priority]||9) - (_PRANK[b.priority]||9); })
    .slice(0, 2);
  const chips = [];
  sugs.forEach(function(s) {
    if (s.title) chips.push('Fix: ' + (s.title.length > 30 ? s.title.slice(0,28)+'…' : s.title));
  });
  const fallbacks = ["What's my next listing?", 'How are sales?', 'Pricing advice', 'SEO tips', 'What should I focus on?'];
  fallbacks.forEach(function(f) { if (chips.length < 5) chips.push(f); });
  el.innerHTML = chips.slice(0, 5).map(function(c) {
    return '<span class="chip" onclick="sendChip(this)">'+escHtml(c)+'</span>';
  }).join('');
}
function askSuggestionFix(i) {
  if (!_lastSuggestions) return;
  const s = (_lastSuggestions.suggestions||[])[i];
  if (!s) return;
  const chatBtn = document.querySelectorAll('nav button')[3]; // dash,actions,analytics,chat,listings
  showTab('chat', chatBtn);
  document.getElementById('msg-input').value = 'Help me fix this: '+s.title+' — '+s.detail;
  sendMsg();
}

// ── Conversion Doctor (views but no sales → ranked fixes) ───────────────────
const _DXCOLOR = {critical:'var(--red)',high:'#e08030',medium:'var(--gold)',low:'#7ba0c2',trust:'var(--gold)'};
const _AREA_ICON = {photos:'📸',price:'💲',title:'🏷️',description:'📝',tags:'🔖',trust:'🤝'};
let _convTargets = [];
let _convDiagnoses = {};
function toggleConvPanel(btn) {
  const el = document.getElementById('conv-doctor');
  if (!el) return;
  const hidden = el.style.display === 'none';
  el.style.display = hidden ? '' : 'none';
  btn.textContent = hidden ? '▲ Collapse' : '▼ Show';
}
function toggleDxBody(id, btn) {
  const el = document.getElementById('conv-dx-body-'+id);
  if (!el) return;
  const hidden = el.style.display === 'none';
  el.style.display = hidden ? '' : 'none';
  btn.textContent = hidden ? '▲ Collapse Diagnosis' : '▼ Show Diagnosis';
}
async function fixStage(listingId, fixIdx, btn) {
  const d = _convDiagnoses[listingId];
  if (!d) return;
  const f = (d._sortedFixes||[])[fixIdx];
  if (!f) return;
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = '⏳ Staging…';
  try {
    const r = await fetchWithTimeout(BASE+'/api/autofix/'+f.area+'/'+listingId,{method:'POST',headers:{Authorization:'Bearer '+TOKEN}},90000);
    const rd = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(rd.detail||'HTTP '+r.status);
    btn.textContent = '✅ Staged — check Action Center';
    btn.style.background = 'var(--green)'; btn.style.color = '#06140d';
    setTimeout(loadActions, 1500);
  } catch(e) {
    btn.disabled = false; btn.textContent = orig;
    alert('Could not stage fix: '+(e.message||e));
  }
}
function fixChat(listingId, fixIdx) {
  const d = _convDiagnoses[listingId];
  if (!d) return;
  const f = (d._sortedFixes||[])[fixIdx];
  if (!f) return;
  const title = (d.stats&&d.stats.title)||'';
  const chatBtn = document.querySelectorAll('nav button')[3];
  showTab('chat', chatBtn);
  const inp = document.getElementById('msg-input');
  inp.value = 'Fix the '+f.area+' for listing "'+title+'": '+f.finding+' — '+f.fix;
  sendMsg();
}
async function fixAllStageable(listingId, btn) {
  const d = _convDiagnoses[listingId];
  if (!d) return;
  const fixes = (d._sortedFixes||[]).filter(function(f){return f.area==='tags'||f.area==='title';});
  if (!fixes.length) return;
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = '⏳ Staging…';
  var staged = 0, failed = [];
  for (var i = 0; i < fixes.length; i++) {
    try {
      var r = await fetchWithTimeout(BASE+'/api/autofix/'+fixes[i].area+'/'+listingId,{method:'POST',headers:{Authorization:'Bearer '+TOKEN}},90000);
      var rd = await r.json().catch(function(){return {};});
      if (!r.ok) throw new Error(rd.detail||'HTTP '+r.status);
      staged++;
    } catch(e) {
      failed.push(fixes[i].area+': '+(e.message||e));
    }
  }
  btn.textContent = staged+'/'+fixes.length+' staged ✅';
  btn.style.background = 'var(--green)'; btn.style.color = '#06140d';
  if (failed.length) alert('Some fixes could not be staged:\\n'+failed.join('\\n'));
  setTimeout(loadActions, 1500);
}
function fixAllInChat(listingId) {
  const d = _convDiagnoses[listingId];
  if (!d) return;
  const fixes = (d._sortedFixes||[]).filter(function(f){return f.area!=='tags'&&f.area!=='title';});
  if (!fixes.length) return;
  const title = (d.stats&&d.stats.title)||('Listing '+listingId);
  const chatBtn = document.querySelectorAll('nav button')[3];
  showTab('chat', chatBtn);
  const inp = document.getElementById('msg-input');
  inp.value = 'Fix all issues for listing "'+title+'": '+fixes.map(function(f){return f.area+': '+f.finding+' → '+f.fix;}).join('; ');
  sendMsg();
}
async function loadConvTargets() {
  const el = document.getElementById('conv-doctor');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/conversion-targets', {headers:{Authorization:'Bearer '+TOKEN}}, 25000);
    const d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    _convTargets = d.targets||[];
    if (!_convTargets.length) { el.innerHTML = '<div class="empty" style="padding:20px 0">✅ Nothing to fix — every viewed listing is selling (or has no views yet).</div>'; return; }
    el.innerHTML = _convTargets.map(function(l){
      return '<div class="card" style="padding:12px 14px;margin-bottom:8px">'+
        '<div class="listing-info">'+
          '<div class="listing-title">'+escHtml(l.title)+'</div>'+
          '<div class="listing-meta">'+l.views+' views · '+l.num_favorers+' ♥ · <span style="color:var(--red)">0 sold</span> · $'+(+l.price||0).toFixed(2)+'</div>'+
        '</div>'+
        '<div class="act-btns">'+
          '<button class="act-btn primary" onclick="diagnoseConv('+l.listing_id+',this)">🩺 Diagnose</button>'+
          '<a class="act-btn" href="'+escHtml(l.url)+'" target="_blank">Open on Etsy</a>'+
        '</div>'+
        '<div id="conv-dx-'+l.listing_id+'"></div>'+
      '</div>';
    }).join('');
    const cBtn = document.getElementById('conv-collapse-btn');
    if (cBtn) cBtn.style.display = '';
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadConvTargets()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:8px 20px;font-size:13px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}
async function diagnoseConv(id, btn) {
  const out = document.getElementById('conv-dx-'+id);
  if (!out) return;
  if (btn) { btn.disabled = true; btn.textContent = '🩺 Diagnosing…'; }
  out.innerHTML = '<div class="card" style="text-align:center;padding:20px 12px;margin-top:8px"><div class="spinner" style="margin:0 auto 10px"></div><div style="color:var(--muted);font-size:12px">Reading title, price, photos, tags &amp; description…</div></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/diagnose/'+id, {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 90000);
    const d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    out.innerHTML = _renderDiagnosis(d);
  } catch(e) {
    out.innerHTML = '<div class="empty" style="padding:14px 0">'+escHtml(e.name==='AbortError'?'Diagnosis timed out — try again':e.message||'Failed')+'</div>';
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '🩺 Diagnose again'; }
  }
}
function _renderDiagnosis(d) {
  const listingId = d.listing_id;
  const dx = d.diagnosis||{}, st = d.stats||{};
  if (dx.raw && !(dx.fixes && dx.fixes.length)) return '<div class="card" style="font-size:13px;white-space:pre-wrap;color:var(--muted);margin-top:8px">'+escHtml(dx.raw)+'</div>';
  const fixes = (dx.fixes||[]).slice().sort(function(a,b){ return (_PRANK[a.priority]||9)-(_PRANK[b.priority]||9); });
  _convDiagnoses[listingId] = Object.assign({},d,{_sortedFixes:fixes});
  let inner = '';
  inner += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px;font-size:10px;color:var(--muted)">'+
    '<span>📸 '+(st.photo_count||0)+'/10</span><span>🔖 '+(st.tag_count||0)+'/13</span><span>🏷️ '+(st.title_length||0)+'/70</span><span>👁 '+(st.views||0)+'</span><span>♥ '+(st.favorites||0)+'</span><span style="color:var(--red)">🛒 '+(st.sales||0)+' sold</span></div>';
  if (dx.primary_issue) inner += '<div class="card" style="background:#241313;border-color:#5a2d2d;margin-bottom:8px"><div class="label" style="color:#e07070">⚠️ PRIMARY ISSUE</div><div style="font-size:13px;line-height:1.45;margin-top:4px">'+escHtml(dx.primary_issue)+'</div></div>';
  if (dx.summary) inner += '<div style="font-size:12px;color:var(--muted);line-height:1.45;margin-bottom:8px">'+escHtml(dx.summary)+'</div>';
  var stageableCount = fixes.filter(function(f){return f.area==='tags'||f.area==='title';}).length;
  var chatCount = fixes.filter(function(f){return f.area!=='tags'&&f.area!=='title';}).length;
  if (stageableCount > 0 || chatCount > 0) {
    inner += '<div class="act-btns" style="margin-bottom:14px">';
    if (stageableCount > 0) inner += '<button class="act-btn primary" style="font-size:13px;padding:9px" onclick="fixAllStageable('+listingId+',this)">🚀 Stage All ('+stageableCount+')</button>';
    if (chatCount > 0) inner += '<button class="act-btn" style="font-size:13px;padding:9px" onclick="fixAllInChat('+listingId+')">💬 Chat Fixes ('+chatCount+')</button>';
    inner += '</div>';
  }
  fixes.forEach(function(f,fIdx){
    const pc = _DXCOLOR[f.priority]||'var(--muted)';
    const icon = _AREA_ICON[f.area]||'•';
    const canStage = f.area==='tags'||f.area==='title';
    inner += '<div class="sug-card" style="border-left-color:'+pc+'">'+
      '<span class="sug-p" style="color:'+pc+'">'+escHtml(f.priority||'medium')+'</span>'+
      '<span style="font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);margin-left:6px">'+icon+' '+escHtml(f.area||'')+'</span>'+
      '<div class="sug-title">'+escHtml(f.finding||'')+'</div>'+
      (f.fix?'<div class="sug-action"><b style="color:var(--gold2)">→ </b>'+escHtml(f.fix)+'</div>':'')+
      (f.impact?'<div class="sug-impact">💡 '+escHtml(f.impact)+'</div>':'')+
      '<div class="act-btns" style="margin-top:8px">'+
      (canStage
        ? '<button class="act-btn primary" onclick="fixStage('+listingId+','+fIdx+',this)">⚡ Stage Fix</button>'
        : '<button class="act-btn" onclick="fixChat('+listingId+','+fIdx+')">💬 Fix in Chat</button>')+
      '</div>'+
    '</div>';
  });
  return '<div style="margin-top:8px">'+
    '<button class="collapse-btn" onclick="toggleDxBody('+listingId+',this)">▲ Collapse Diagnosis</button>'+
    '<div id="conv-dx-body-'+listingId+'">'+inner+'</div>'+
    '</div>';
}

// ── Hub (Brand Kit · Products · Creds · Security) ──────────────────────────
var _THEMES = [
  {id:'DP1026',name:'Lavender Dreams',primary:'#8666AA',accent:'#C4A8D4',neutral:'#FAF7FF',text:'#2C1A3A'},
  {id:'DP1027',name:'Cotton Candy',   primary:'#DE97C6',accent:'#97C6DE',neutral:'#FFF6FC',text:'#2C1A2A'},
  {id:'DP1028',name:'Midnight Blue',  primary:'#1B2568',accent:'#7BA7C2',neutral:'#F0F5FF',text:'#0D1525'},
  {id:'DP1029',name:'Coral Peach',    primary:'#FD6C49',accent:'#F5B878',neutral:'#FFF8F4',text:'#3A1A0D'}
];
var _PRODUCTS_STATIC = [
  {id:'DP1026',name:'Ultimate Life Planner',      price:'$14.99',pages:104},
  {id:'DP1027',name:'Student & School Planner',   price:'$9.99', pages:90},
  {id:'DP1028',name:'Budget & Finance Planner',   price:'$12.99',pages:102},
  {id:'DP1029',name:'Fitness & Wellness Planner', price:'$12.99',pages:91}
];
function _renderBrandKit() {
  var html = '<div class="section-title">Product Color Palettes</div>';
  _THEMES.forEach(function(t){
    html += '<div class="card" style="margin-bottom:10px">';
    html += '<div style="font-size:12px;font-weight:700;color:var(--muted);margin-bottom:8px">'+escHtml(t.id)+' — '+escHtml(t.name)+'</div>';
    html += '<div style="display:flex;gap:12px;flex-wrap:wrap">';
    [{label:'Primary',hex:t.primary},{label:'Accent',hex:t.accent},{label:'Neutral',hex:t.neutral},{label:'Text',hex:t.text}].forEach(function(c){
      html += '<div style="display:flex;align-items:center;gap:5px">'+
        '<span class="swatch" style="background:'+escHtml(c.hex)+'"></span>'+
        '<div style="font-size:11px"><div style="color:var(--muted)">'+escHtml(c.label)+'</div>'+
        '<div style="font-family:monospace;font-size:10px;color:var(--text)">'+escHtml(c.hex)+'</div></div>'+
        '</div>';
    });
    html += '</div></div>';
  });
  html += '<div class="section-title">Listing Standards</div><div class="card">';
  html += '<table style="width:100%;border-collapse:collapse;font-size:12px">';
  [['Title','≤70 chars · keyword first 40 · commas not pipes'],
   ['Tags','13 tags · each ≤20 chars · multi-word buyer phrases'],
   ['Photos','10 slots · 2400×2400px · lifestyle hero first'],
   ['Price','.99 / .97 / .49 endings — never round numbers'],
   ['AI disclosure','Required in description · who_made: i_did'],
   ['File limit','20 MB per file (PDF + ZIP · Etsy hard limit)']
  ].forEach(function(r){
    html += '<tr style="border-bottom:1px solid var(--border)">'+
      '<td style="padding:7px 0;padding-right:10px;color:var(--gold);font-weight:700;white-space:nowrap">'+escHtml(r[0])+'</td>'+
      '<td style="padding:7px 0;color:var(--muted);line-height:1.4">'+escHtml(r[1])+'</td></tr>';
  });
  html += '</table></div>';
  html += '<div class="section-title">Pricing Tiers</div><div class="card">';
  html += '<table style="width:100%;border-collapse:collapse;font-size:12px">';
  [['DP1026 Life Planner','$14.99','104 pages + sticker pack'],
   ['DP1027 Student','$9.99','90 pages · student budget'],
   ['DP1028 Budget','$12.99','102 pages · finance niche'],
   ['DP1029 Fitness','$12.99','91 pages · wellness niche'],
   ['SVG 5-pack','$9.99','5 designs · instant DL'],
   ['SVG 10+ pack','$14.99','10+ designs · instant DL']
  ].forEach(function(r){
    html += '<tr style="border-bottom:1px solid var(--border)">'+
      '<td style="padding:7px 0;padding-right:8px;font-weight:600">'+escHtml(r[0])+'</td>'+
      '<td style="padding:7px 0;padding-right:8px;color:var(--gold);font-weight:700;white-space:nowrap">'+escHtml(r[1])+'</td>'+
      '<td style="padding:7px 0;color:var(--muted)">'+escHtml(r[2])+'</td></tr>';
  });
  html += '</table></div>';
  return html;
}
function loadProductIndex() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  var html = '<div class="section-title">Core Products</div>';
  _PRODUCTS_STATIC.forEach(function(p,i){
    var t = _THEMES[i]||{};
    html += '<div class="prod-card" style="border-left-color:'+(t.primary||'var(--gold)')+'">'+
      '<div style="display:flex;justify-content:space-between;align-items:flex-start">'+
        '<div><div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.4px">'+escHtml(p.id)+'</div>'+
        '<div style="font-size:14px;font-weight:600;margin-top:3px">'+escHtml(p.name)+'</div></div>'+
        '<div style="font-size:16px;font-weight:700;color:var(--gold)">'+escHtml(p.price)+'</div>'+
      '</div>'+
      '<div style="display:flex;gap:12px;margin-top:8px;font-size:11px;color:var(--muted)">'+
        '<span>📄 '+p.pages+' pages</span><span>🔖 13 tags</span><span>Digital Download</span>'+
      '</div>'+
    '</div>';
  });
  html += '<div class="section-title" style="margin-top:8px">Platform Connections</div><div class="card">';
  [
    {name:'Etsy',      icon:'🛍️',status:'live',    note:'onbrandcraftz · authorized'},
    {name:'Pinterest', icon:'📌',        status:'roadmap',note:'API v5 — ready to integrate', steps:[
      'Create a Pinterest Developer app at developers.pinterest.com',
      'Add PINTEREST_APP_ID and PINTEREST_APP_SECRET to .env',
      'Run: python tools/pinterest_oauth.py — authorizes and saves tokens to .env automatically',
      'Claim the Etsy shop under Pinterest "Claimed accounts" to enable Rich Pins',
      'Done — the Social Media Agent can post via tools/pinterest_api.py'
    ]},
    {name:'Instagram', icon:'📷',        status:'roadmap',note:'Meta Graph API (app review needed)', steps:[
      'Create a Meta Business app at developers.facebook.com',
      'Add the "Instagram Graph API" product to the app',
      'Connect the Instagram Professional account via a Facebook Page',
      'Add INSTAGRAM_APP_ID / INSTAGRAM_APP_SECRET to .env',
      'Generate a long-lived access token (scopes: instagram_basic, instagram_content_publish, instagram_manage_insights, pages_show_list, pages_read_engagement)',
      'Add INSTAGRAM_USER_ID / INSTAGRAM_ACCESS_TOKEN to .env',
      'Submit the app for Meta App Review before posting publicly — tools/instagram_api.py is already built and waiting on this'
    ]},
    {name:'Facebook',  icon:'📘',        status:'roadmap',note:'Same Meta app as Instagram', steps:[
      'No separate app needed — reuse the Meta app created for Instagram',
      'Add the Facebook Page and Pages API permission to that same app',
      'Generate a Page Access Token with the pages_manage_posts scope',
      'Add FACEBOOK_PAGE_ID / FACEBOOK_ACCESS_TOKEN to .env once issued'
    ]},
    {name:'TikTok',    icon:'🎵',        status:'roadmap',note:'TikTok for Business API', steps:[
      'App credentials are already configured (TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET)',
      'Run: python tools/tiktok_oauth.py — log in as @onbrandcraftz and approve',
      'Tokens save to .env automatically (access token 24h, refresh token 365 days)',
      'Re-run tools/tiktok_oauth.py whenever the access token expires',
      'Done — post via tools/tiktok_poster.py'
    ]},
    {name:'OneDrive',  icon:'☁️',        status:'roadmap',note:'Microsoft Graph — source file storage', steps:[
      'Not yet built — no OneDrive code exists in the repo today',
      'Register an app in the Azure Portal (Microsoft Entra ID → App registrations)',
      'Grant the Microsoft Graph "Files.ReadWrite" delegated permission',
      'Add ONEDRIVE_CLIENT_ID / ONEDRIVE_CLIENT_SECRET to .env',
      'Build tools/onedrive_oauth.py to get access/refresh tokens (does not exist yet)',
      'Use the Graph API /me/drive/root:/path:/content endpoint to sync source files for backup'
    ]}
  ].forEach(function(p){
    var live = p.status==='live';
    var key = p.name.toLowerCase();
    html += '<div class="cred-row" style="flex-wrap:wrap">'+
      '<div style="display:flex;align-items:center;gap:10px;width:100%">'+
      '<div style="font-size:20px;flex-shrink:0;width:28px">'+p.icon+'</div>'+
      '<div style="flex:1"><div style="font-size:13px;font-weight:600">'+escHtml(p.name)+'</div>'+
      '<div style="font-size:11px;color:var(--muted)">'+escHtml(p.note)+'</div></div>'+
      (live
        ? '<div style="font-size:11px;font-weight:700;color:var(--green)">✅ Live</div>'
        : '<div style="font-size:11px;font-weight:700;color:var(--muted);cursor:pointer;white-space:nowrap" onclick="toggleCredSteps(\\''+key+'\\')">🗺️ Roadmap ›</div>')+
      '</div>'+
      (live ? '' :
        '<div id="cred-steps-'+key+'" style="display:none;width:100%;margin-top:10px;padding-top:10px;border-top:1px solid var(--border)">'+
          '<div style="font-size:11px;font-weight:700;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.4px">Steps to complete</div>'+
          '<ol style="margin:0;padding-left:18px;font-size:12px;line-height:1.6">'+
            (p.steps||[]).map(function(s){return '<li style="margin-bottom:4px">'+escHtml(s)+'</li>';}).join('')+
          '</ol>'+
        '</div>')+
      '</div>';
  });
  html += '</div>';
  el.innerHTML = html;
}
function toggleCredSteps(key) {
  var panel = document.getElementById('cred-steps-'+key);
  if (!panel) return;
  panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}
async function loadCredentials() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    var r = await fetchWithTimeout(BASE+'/api/credentials/status',{headers:{Authorization:'Bearer '+TOKEN}},15000);
    var d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    var html = '<div class="card" style="margin-bottom:12px">';
    if (d.etsy_live) {
      html += '<div style="color:var(--green);font-size:15px;font-weight:700">✅ Etsy Live</div>'+
        '<div style="font-size:12px;color:var(--muted);margin-top:4px">'+escHtml(d.shop_name||'onbrandcraftz')+' · token valid</div>';
    } else {
      html += '<div style="color:var(--red);font-size:15px;font-weight:700">⚠️ Etsy Ping Failed</div>'+
        '<div style="font-size:12px;color:var(--muted);margin-top:4px">'+escHtml(d.etsy_live_error||'Unknown error')+' — run python tools/etsy_oauth.py</div>';
    }
    html += '</div><div class="section-title">API Credentials</div><div class="card">';
    var et=d.etsy||{}, an=d.anthropic||{}, oa=d.openai||{}, sm=d.smtp||{}, pi=d.pinterest||{};
    [
      {label:'Etsy API Key',         ok:et.api_key,         note:'ETSY_API_KEY / ETSY_CLIENT_ID'},
      {label:'Etsy Access Token',    ok:et.access_token,    note:'Expires every 1 hour — auto-refreshed'},
      {label:'Etsy Refresh Token',   ok:et.refresh_token,   note:'90-day window — re-auth via etsy_oauth.py'},
      {label:'Anthropic (Claude)',   ok:an.api_key,         note:'""" + business_config.AGENT_NAME + """ (CEO) · Conversion Doctor · tag gen'},
      {label:'OpenAI (DALL-E)',      ok:oa.api_key,         note:'gpt-image-1 listing photo generation'},
      {label:'SMTP Email',           ok:sm.user,            note:'Post-purchase digital delivery'},
      {label:'Pinterest',            ok:pi.api_key,         note:'API v5 · roadmap'}
    ].forEach(function(c){
      var col = c.ok ? 'var(--green)' : 'var(--red)';
      html += '<div class="cred-row">'+
        '<div class="cred-dot" style="background:'+col+'"></div>'+
        '<div style="flex:1"><div style="font-size:13px;font-weight:600">'+escHtml(c.label)+'</div>'+
        '<div style="font-size:11px;color:var(--muted)">'+escHtml(c.note)+'</div></div>'+
        '<div style="font-size:12px;font-weight:700;color:'+col+'">'+escHtml(c.ok?'Set ✓':'Not set')+'</div>'+
      '</div>';
    });
    html += '</div><div style="font-size:11px;color:var(--muted);text-align:center;padding:10px 0">All tokens stored in .env — never committed to git</div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadCredentials()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}
function _renderSecurityPosture() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  var html = '<div class="section-title">Security Posture</div><div class="card">';
  [
    {ok:true, label:'.env not committed to git',           note:'Credentials stay local, never in version control'},
    {ok:true, label:'APP_SECRET_TOKEN set',                note:'Every dashboard request requires Bearer auth'},
    {ok:true, label:'Quality gate is code',                note:'Title ≤70 · tags ≤13 · validated at stage AND approve'},
    {ok:true, label:'Staged action queue',                 note:'Every Etsy change requires Scott one-tap approval'},
    {ok:null, label:'Etsy MFA enabled?',                   note:'Verify in Etsy → Account Settings → Security'},
    {ok:null, label:'Outlook 2FA active?',                 note:'Verify at account.microsoft.com → Security'},
    {ok:null, label:'Pinterest not integrated yet',        note:'No API exposure until keys are added'},
    {ok:false,label:'No per-IP rate limiting',             note:'Add nginx or Cloudflare for production hardening'},
    {ok:false,label:'Token rotation reminder needed',      note:'Etsy refresh tokens expire 90 days — set a calendar alert'}
  ].forEach(function(c){
    var icon = c.ok===true?'✅':c.ok===false?'⚠️':'❓';
    var col  = c.ok===true?'var(--green)':c.ok===false?'var(--red)':'var(--muted)';
    html += '<div class="posture-row">'+
      '<div style="font-size:16px;flex-shrink:0;width:24px">'+icon+'</div>'+
      '<div style="flex:1"><div style="font-size:13px;font-weight:600;color:'+col+'">'+escHtml(c.label)+'</div>'+
      '<div style="font-size:11px;color:var(--muted)">'+escHtml(c.note)+'</div></div>'+
    '</div>';
  });
  html += '</div>';
  html += '<div class="card" style="background:#1a2030;border-color:#2a3d5a;margin-top:4px">'+
    '<div style="font-size:12px;color:#7ba0c2;line-height:1.7">'+
    '<b style="color:var(--gold)">Re-authorize Etsy:</b> If any API call returns 401, run<br>'+
    '<code style="font-size:11px;background:#0d1525;padding:2px 8px;border-radius:4px;display:inline-block;margin-top:4px">python tools/etsy_oauth.py</code>'+
    '</div></div>';
  el.innerHTML = html;
}
function showHubSection(section, btn) {
  document.querySelectorAll('.hub-section-btn').forEach(function(b){b.classList.remove('active');});
  if (btn) btn.classList.add('active');
  if (section==='brand')         document.getElementById('hub-content').innerHTML = _renderBrandKit();
  else if (section==='products') loadProductIndex();
  else if (section==='files')    loadFiles();
  else if (section==='studio')   loadStudio();
  else if (section==='creds')    loadCredentials();
  else if (section==='security') _renderSecurityPosture();
  else if (section==='relay')    _renderRelayPanel();
}
async function _renderRelayPanel() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    var rs = await fetchWithTimeout(BASE+'/api/relay/status',{headers:{Authorization:'Bearer '+TOKEN}},15000);
    var status = await rs.json().catch(function(){return {};});
    if (!rs.ok) throw new Error(status.detail||'HTTP '+rs.status);
    var rf = await fetchWithTimeout(BASE+'/api/relay/allowed-folders',{headers:{Authorization:'Bearer '+TOKEN}},15000);
    var fd = await rf.json().catch(function(){return {};});
    if (!rf.ok) throw new Error(fd.detail||'HTTP '+rf.status);
    var folders = fd.folders || [];

    var badge, badgeCol;
    if (status.killed)            { badge = '⛔ Killed';   badgeCol = 'var(--red)'; }
    else if (status.connected)    { badge = '✅ Online';   badgeCol = 'var(--green)'; }
    else                          { badge = '⚪ Offline';  badgeCol = 'var(--muted)'; }

    var html = '<div class="card" style="margin-bottom:12px">';
    html += '<div style="display:flex;align-items:center;justify-content:space-between;gap:10px">'+
      '<div><div style="font-size:15px;font-weight:700;color:'+badgeCol+'">'+badge+'</div>'+
      '<div style="font-size:11px;color:var(--muted);margin-top:4px">'+
        (status.last_heartbeat ? 'Last heartbeat: '+escHtml(status.last_heartbeat) : 'No heartbeat received yet')+
      '</div></div>'+
      (status.killed
        ? '<button onclick="relayResume()" style="background:var(--green);color:#0D1B2A;border:none;border-radius:8px;padding:10px 18px;font-size:13px;font-weight:700;cursor:pointer">Resume</button>'
        : '<button onclick="relayKill()" style="background:var(--red);color:#fff;border:none;border-radius:8px;padding:10px 18px;font-size:13px;font-weight:700;cursor:pointer">Kill Switch</button>')+
      '</div>';
    if (status.killed && status.killed_at) {
      html += '<div style="font-size:11px;color:var(--muted);margin-top:8px">Killed at '+escHtml(status.killed_at)+
        (status.killed_by ? ' by '+escHtml(status.killed_by) : '')+'</div>';
    }
    html += '<div style="font-size:11px;color:var(--muted);margin-top:8px">'+
      'Kill switch blocks every local tool — including read-only file access — until resumed.'+
      '</div>';
    html += '</div>';

    html += '<div class="section-title">Allowed Folders</div><div class="card">';
    if (!folders.length) {
      html += '<div class="empty">No folders configured yet — the relay can\\'t read or write anything on Scott\\'s machine until at least one is added.</div>';
    } else {
      folders.forEach(function(f){
        html += '<div class="cred-row">'+
          '<div style="flex:1"><div style="font-size:13px;font-weight:600;word-break:break-all">'+escHtml(f.path)+'</div>'+
          '<div style="font-size:11px;color:var(--muted)">added by '+escHtml(f.added_by||'system')+' · '+escHtml(f.added_at||'')+'</div></div>'+
          '<button onclick="removeAllowedFolder('+f.id+')" style="background:none;color:var(--red);border:1px solid var(--red);border-radius:8px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer">Remove</button>'+
        '</div>';
      });
    }
    html += '<div style="display:flex;gap:8px;margin-top:12px">'+
      '<input id="relay-folder-input" type="text" placeholder="/data/workspace" style="flex:1;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 12px;color:var(--text);font-size:13px">'+
      '<button onclick="addAllowedFolder()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 18px;font-size:13px;font-weight:700;cursor:pointer">Add</button>'+
      '</div>';
    html += '</div>';

    html += '<div class="section-title">Upload File to Relay Workspace</div><div class="card">';
    html += '<input id="relay-upload-input" type="file" onchange="_relayUploadPicked()" style="width:100%;color:var(--text);font-size:13px">'+
      '<div style="display:flex;gap:8px;margin-top:10px">'+
      '<input id="relay-upload-path" type="text" placeholder="/data/workspace/yourfile.pdf" style="flex:1;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 12px;color:var(--text);font-size:13px">'+
      '<button onclick="uploadToRelay()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 18px;font-size:13px;font-weight:700;cursor:pointer">Upload</button>'+
      '</div>'+
      '<div id="relay-upload-status" style="font-size:11px;color:var(--muted);margin-top:8px"></div>'+
      '</div>';

    html += '<div style="font-size:11px;color:var(--muted);text-align:center;padding:10px 0">'+
      'The relay re-resolves every path with realpath before allowing access — this list is enforced on Scott\\'s machine, not just the server.'+
      '</div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="_renderRelayPanel()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}
async function relayKill() {
  if (!confirm('Engage the kill switch? This blocks ALL local relay actions, including reads, until resumed.')) return;
  try {
    await fetchWithTimeout(BASE+'/api/relay/kill', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 15000);
  } catch(e) { alert('Could not engage kill switch: ' + (e.message||e)); }
  _renderRelayPanel();
}
async function relayResume() {
  try {
    await fetchWithTimeout(BASE+'/api/relay/resume', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 15000);
  } catch(e) { alert('Could not resume: ' + (e.message||e)); }
  _renderRelayPanel();
}
async function addAllowedFolder() {
  var inp = document.getElementById('relay-folder-input');
  var path = (inp && inp.value || '').trim();
  if (!path) return;
  try {
    const r = await fetchWithTimeout(BASE+'/api/relay/allowed-folders', {
      method:'POST',
      headers:{'Content-Type':'application/json',Authorization:'Bearer '+TOKEN},
      body: JSON.stringify({path}),
    }, 15000);
    const d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
  } catch(e) { alert('Could not add folder: ' + (e.message||e)); }
  _renderRelayPanel();
}
async function removeAllowedFolder(id) {
  try {
    const r = await fetchWithTimeout(BASE+'/api/relay/allowed-folders/'+id, {method:'DELETE',headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    if (!r.ok) { const d = await r.json().catch(function(){return {};}); throw new Error(d.detail||'HTTP '+r.status); }
  } catch(e) { alert('Could not remove folder: ' + (e.message||e)); }
  _renderRelayPanel();
}
function _relayUploadPicked() {
  var input = document.getElementById('relay-upload-input');
  var pathInput = document.getElementById('relay-upload-path');
  var file = input && input.files[0];
  if (file && pathInput && !pathInput.value) pathInput.value = '/data/workspace/' + file.name;
}
async function uploadToRelay() {
  var input = document.getElementById('relay-upload-input');
  var pathInput = document.getElementById('relay-upload-path');
  var status = document.getElementById('relay-upload-status');
  var file = input.files[0];
  if (!file) { alert('Choose a file first'); return; }
  var path = (pathInput.value || '').trim();
  if (!path) { alert('Destination path is required'); return; }
  status.textContent = 'Uploading...';
  try {
    var res = await fetchWithTimeout(
      BASE+'/api/relay/upload?path=' + encodeURIComponent(path),
      { method: 'POST', headers: { 'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/octet-stream' }, body: file },
      120000
    );
    var data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Upload failed');
    status.textContent = 'Uploaded ' + data.bytes_written + ' bytes to ' + data.path;
    input.value = '';
  } catch (e) {
    status.textContent = '';
    alert(e.message || e);
  }
}
function _fileUrl(f, inline){
  return BASE+'/api/files/download?root='+encodeURIComponent(f.root)+'&path='+encodeURIComponent(f.path)+
    '&token='+encodeURIComponent(TOKEN)+(inline?'&inline=1':'');
}
function _zipEntryUrl(f, entryName){
  return BASE+'/api/files/zip-entry?root='+encodeURIComponent(f.root)+'&path='+encodeURIComponent(f.path)+
    '&entry='+encodeURIComponent(entryName)+'&token='+encodeURIComponent(TOKEN);
}
function _fileIcon(name){
  var n=(name||'').toLowerCase();
  if(n.match(/\\.(png|jpe?g|gif|webp|svg)$/)) return '🖼️';
  if(n.endsWith('.pdf')) return '📕';
  if(n.endsWith('.zip')) return '🗂️';
  if(n.match(/\\.(txt|md)$/)) return '📃';
  return '📄';
}
function toggleZip(id, btn){
  var el=document.getElementById(id);
  if(!el) return;
  var open=el.style.display==='none';
  el.style.display=open?'':'none';
  if(btn) btn.textContent=open?'▾':'▸';
}
function openFile(url){ window.open(url,'_blank'); }
async function loadFiles() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    var r = await fetchWithTimeout(BASE+'/api/files',{headers:{Authorization:'Bearer '+TOKEN}},20000);
    var d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    var groups = d.groups||[];
    if (!groups.length || groups.every(function(g){return !g.files.length;})) {
      el.innerHTML = '<div class="empty" style="line-height:1.6">'+
        escHtml(d.empty_reason||'No files yet.')+'</div>';
      return;
    }
    var html = '<div class="card" style="background:#1a2030;border-color:#2a3d5a;margin-bottom:12px">'+
      '<div style="font-size:12px;color:#7ba0c2;line-height:1.6">The actual product files living on the server '+
      '(data/digital_products/ and data/backups/). Tap a file to open it. Tap a ZIP to expand it and open any '+
      'file inside directly — no unzipping needed.</div></div>';
    var zipIdx=0;
    groups.forEach(function(g){
      if (!g.files.length) return;
      html += '<div class="section-title">'+escHtml(g.label)+' ('+g.files.length+')</div><div class="card">';
      g.files.forEach(function(f){
        var when = new Date(f.modified).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
        if (f.is_zip) {
          var zid='zip-'+(zipIdx++);
          var entries=f.entries||[];
          html += '<div class="listing-item" onclick="toggleZip(&apos;'+zid+'&apos;,this.querySelector(&apos;.zip-caret&apos;))" style="cursor:pointer">'+
            '<div class="thumb-placeholder">🗂️</div>'+
            '<div class="listing-info"><div class="listing-title">'+escHtml(f.path)+'</div>'+
            '<div class="listing-meta">'+escHtml(f.size_human)+' · '+escHtml(when)+' · '+entries.length+' files inside</div></div>'+
            '<div class="zip-caret" style="color:var(--gold);font-size:16px">▸</div>'+
          '</div>';
          html += '<div id="'+zid+'" style="display:none;margin:0 0 6px 14px;border-left:2px solid #2a3d5a;padding-left:8px">';
          if(!entries.length){
            html += '<div class="listing-meta" style="padding:8px 0">Could not read this ZIP\\'s contents.</div>';
          }
          entries.forEach(function(en){
            var eurl=_zipEntryUrl(f,en.name);
            html += '<div class="listing-item" onclick="openFile(&apos;'+eurl+'&apos;)" style="cursor:pointer;padding:7px 4px">'+
              '<div class="thumb-placeholder" style="font-size:16px">'+_fileIcon(en.name)+'</div>'+
              '<div class="listing-info"><div class="listing-title" style="font-size:13px">'+escHtml(en.name)+'</div>'+
              '<div class="listing-meta">'+escHtml(en.size_human)+(en.inline?' · tap to open':' · tap to download')+'</div></div>'+
              '<div style="color:var(--gold);font-size:15px">'+(en.inline?'↗':'⬇')+'</div>'+
            '</div>';
          });
          html += '</div>';
        } else {
          var url=_fileUrl(f, f.inline?1:0);
          html += '<div class="listing-item" onclick="openFile(&apos;'+url+'&apos;)" style="cursor:pointer">'+
            '<div class="thumb-placeholder">'+_fileIcon(f.path)+'</div>'+
            '<div class="listing-info"><div class="listing-title">'+escHtml(f.path)+'</div>'+
            '<div class="listing-meta">'+escHtml(f.size_human)+' · '+escHtml(when)+(f.inline?' · tap to open':' · tap to download')+'</div></div>'+
            '<div style="color:var(--gold);font-size:18px">'+(f.inline?'↗':'⬇')+'</div>'+
          '</div>';
        }
      });
      html += '</div>';
    });
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load files')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadFiles()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}
function loadHub() {
  var btns = document.querySelectorAll('.hub-section-btn');
  btns.forEach(function(b){b.classList.remove('active');});
  if (btns[0]) btns[0].classList.add('active');
  document.getElementById('hub-content').innerHTML = _renderBrandKit();
}

// ── Back to top (listings) ─────────────────────────────────────────────────
(function(){
  const fab = document.getElementById('fab-top');
  const screen = document.getElementById('screen-listings');
  if (!fab || !screen) return;
  screen.addEventListener('scroll', function(){ fab.classList.toggle('visible', _onListings && screen.scrollTop > 200); }, {passive:true});
  fab.addEventListener('click', function(){ screen.scrollTo({top:0,behavior:'smooth'}); });
})();

// ── Batch tag fix ──────────────────────────────────────────────────────────
async function batchStageTags(btn) {
  if (!confirm('Scan all active listings and stage tag fixes for every listing with fewer than 13 tags?\\n\\nThis may take up to 2 minutes. You review and approve each fix in this Action Center.')) return;
  btn.disabled = true;
  const orig = btn.textContent;
  btn.textContent = '⏳ Generating…';
  try {
    const r = await fetchWithTimeout(BASE+'/api/batch/stage-tags', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 180000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    const errNote = d.errors && d.errors.length ? `\n${d.errors.length} listing(s) had tag-length issues and were skipped.` : '';
    alert('✅ ' + d.message + errNote);
    loadActions();
  } catch(e) {
    alert('Error: ' + (e.name==='AbortError'?'Request timed out — the batch is still running server-side; check the Action Center in a moment':(e.message||e)));
  } finally {
    btn.disabled = false;
    btn.textContent = orig;
  }
}

// ── Init ───────────────────────────────────────────────────────────────────
if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/sw.js').catch(()=>{}); }
// Restore last CEO report from sessionStorage so the dashboard is instant on
// every page reload — no spinner needed when we already have recent data.
(function(){
  try {
    var _s = sessionStorage.getItem('obc_sug');
    if (_s) {
      var _p = JSON.parse(_s);
      if (_p && _p.generated_at && Array.isArray(_p.suggestions) && _p.suggestions.length && !_p.error) {
        var _age = Date.now() - new Date(_p.generated_at).getTime();
        if (_age < 4 * 3600 * 1000) _lastSuggestions = _p; // accept up to 4h old
      }
    }
  } catch(e) {}
})();
loadDash();
loadTodos();
setTimeout(loadActions, 1200);  // populate Action Center + nav badge without being asked
setTimeout(loadConvTargets, 1800);  // Conversion Doctor worklist on the dashboard

// Surface a loud warning the moment the durable /data volume isn't attached — this is
// silent otherwise (the server just falls back to ephemeral storage) and was previously
// only caught by manually hitting /health (diagnosed 2026-06-17, ops_runbook).
fetch(BASE + '/health').then(r => r.json()).then(h => {
  if (h && h.persistent === false) {
    const b = document.getElementById('persist-banner');
    b.style.display = 'block';
    document.documentElement.style.setProperty(
      '--hdr', 'calc(52px + ' + b.offsetHeight + 'px + env(safe-area-inset-top,0px))'
    );
  }
}).catch(() => {});
</script>
</body>
</html>""".replace("Scott", business_config.OWNER_NAME).replace("Frank", business_config.AGENT_NAME_SHORT)


@app.get("/", response_class=HTMLResponse)
def web_ui(request: Request):
    if not _check_session(request):
        return RedirectResponse(f"/login?next={request.url.path}", status_code=307)
    return HTMLResponse(
        content=_WEB_UI,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


# FRANK Command Center — Step 2 is wiring this shell to real data (Build Order
# step 2). Served at a separate path so the live dashboard above is never at risk
# while this is built out panel by panel. See frank_hud_mockup.py for details.
from frank_hud_mockup import render_frank_hud  # noqa: E402


@app.get("/frank", response_class=HTMLResponse)
def frank_hud_mockup(request: Request):
    if not _check_session(request):
        return RedirectResponse(f"/login?next={request.url.path}", status_code=307)
    return HTMLResponse(
        content=render_frank_hud(APP_TOKEN),
        # private: browser may cache, but not CDN/proxies (token is embedded in JS)
        # no-cache: must revalidate with server before using cached copy (session check happens)
        headers={"Cache-Control": "private, no-cache"},
    )


@app.get("/api/me")
async def get_me(request: Request, _token: str = Depends(_auth)):
    """Return the username and role associated with the current session."""
    uname = _get_session_user(request)
    if not uname:
        return {"username": "", "role": ""}
    user_row = db.get_hub_user(uname)
    role = user_row["role"] if user_row else "owner"
    return {"username": uname, "role": role}


def _require_owner(request: Request) -> None:
    """Raise 403 unless the current session belongs to an owner-role user."""
    uname = _get_session_user(request)
    if not uname:
        raise HTTPException(status_code=403, detail="Owner role required")
    user_row = db.get_hub_user(uname)
    if not user_row or user_row["role"] != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")


@app.get("/api/admin/users")
async def admin_list_users(request: Request, _token: str = Depends(_auth)):
    """List all hub users (username, role, created_at). Owner only."""
    _require_owner(request)
    return {"users": db.list_hub_users()}


class _UserCreate(BaseModel):
    username: str
    password: str
    role: str = "admin"


@app.post("/api/admin/users")
async def admin_create_user(request: Request, body: _UserCreate, _token: str = Depends(_auth)):
    """Create a new hub user. Owner only. Role must be 'admin' (owner cannot be created here)."""
    _require_owner(request)
    uname = body.username.strip().lower()
    if not uname or not body.password.strip():
        raise HTTPException(status_code=400, detail="username and password are required")
    if body.role not in ("admin", "owner"):
        raise HTTPException(status_code=400, detail="role must be 'admin'")
    if body.role == "owner":
        raise HTTPException(status_code=400, detail="Cannot create a second owner account")
    if db.get_hub_user(uname):
        raise HTTPException(status_code=409, detail=f"User '{uname}' already exists")
    db.create_hub_user(uname, _hash_password(body.password.strip()), role="admin")
    return {"ok": True, "username": uname, "role": "admin"}


class _PasswordReset(BaseModel):
    password: str


@app.post("/api/admin/users/{username}/reset-password")
async def admin_reset_password(username: str, request: Request, body: _PasswordReset, _token: str = Depends(_auth)):
    """Reset a user's password. Owner can reset any admin's password."""
    _require_owner(request)
    uname = username.strip().lower()
    user_row = db.get_hub_user(uname)
    if not user_row:
        raise HTTPException(status_code=404, detail=f"User '{uname}' not found")
    requester = _get_session_user(request)
    if user_row["role"] == "owner" and uname != requester:
        raise HTTPException(status_code=403, detail="Cannot reset another owner's password")
    if not body.password.strip():
        raise HTTPException(status_code=400, detail="password is required")
    db.update_hub_user_password(uname, _hash_password(body.password.strip()))
    return {"ok": True}


@app.delete("/api/admin/users/{username}")
async def admin_delete_user(username: str, request: Request, _token: str = Depends(_auth)):
    """Delete a hub user. Owner only. Cannot delete the owner account."""
    _require_owner(request)
    uname = username.strip().lower()
    user_row = db.get_hub_user(uname)
    if not user_row:
        raise HTTPException(status_code=404, detail=f"User '{uname}' not found")
    if user_row["role"] == "owner":
        raise HTTPException(status_code=403, detail="Cannot delete the owner account")
    db.delete_hub_user(uname)
    return {"ok": True}


# ── PWA: manifest + service worker (makes the hub installable to home screen) ─────

_MANIFEST = {
    "name": f"{business_config.BUSINESS_NAME} Hub",
    "short_name": business_config.BUSINESS_NAME,
    "description": f"{business_config.BUSINESS_NAME} Etsy operations hub — live metrics, action center, {business_config.AGENT_NAME} (CEO agent).",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "any",
    "background_color": "#0D1B2A",
    "theme_color": "#0D1B2A",
    "icons": [
        {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}

# Network-first SW: always fresh online; caches the app shell for offline launch.
# Cache name keyed to BUILD_ID so each deploy gets a clean cache (no stale shell).
_SW_JS = (
    "const CACHE='obc-shell-" + _BUILD_ID + "';\n"
    "self.addEventListener('install',e=>self.skipWaiting());\n"
    "self.addEventListener('activate',e=>e.waitUntil((async()=>{\n"
    "  const keys=await caches.keys();\n"
    "  await Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)));\n"
    "  await self.clients.claim();\n"
    "})()));\n"
    "self.addEventListener('fetch',e=>{\n"
    "  const req=e.request;\n"
    "  if(req.method!=='GET') return;\n"
    "  e.respondWith(fetch(req).then(r=>{\n"
    "    if(req.mode==='navigate'){const cp=r.clone();caches.open(CACHE).then(c=>c.put('/',cp));}\n"
    "    return r;\n"
    "  }).catch(()=>caches.match(req).then(m=>m||caches.match('/'))));\n"
    "});\n"
)


@app.get("/manifest.webmanifest")
def manifest():
    return JSONResponse(_MANIFEST, media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    return Response(
        content=_SW_JS,
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"},
    )


# FRANK gets its own manifest + service worker, scoped to /frank, so it installs as
# its own standalone app distinct from the root Hub above. A second SW can't share
# /sw.js (that's already registered at scope "/"), so it's served from a separate
# path; Service-Worker-Allowed widens the registerable scope to /frank since the
# script's own path (/frank-sw.js) isn't literally under /frank/.
_FRANK_MANIFEST = {
    "name": "FRANK Command Center",
    "short_name": "FRANK",
    "description": f"FRANK — {business_config.BUSINESS_NAME} CEO agent command center.",
    "start_url": "/frank",
    "scope": "/frank",
    "display": "standalone",
    "orientation": "any",
    "background_color": "#070d16",
    "theme_color": "#070d16",
    "icons": [
        {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}

_FRANK_SW_JS = (
    "const CACHE='obc-frank-shell-" + _BUILD_ID + "';\n"
    "self.addEventListener('install',e=>self.skipWaiting());\n"
    "self.addEventListener('activate',e=>e.waitUntil((async()=>{\n"
    "  const keys=await caches.keys();\n"
    "  await Promise.all(keys.filter(k=>k!==CACHE && k.startsWith('obc-frank-')).map(k=>caches.delete(k)));\n"
    "  await self.clients.claim();\n"
    "})()));\n"
    "self.addEventListener('fetch',e=>{\n"
    "  const req=e.request;\n"
    "  if(req.method!=='GET') return;\n"
    "  e.respondWith(fetch(req).then(r=>{\n"
    "    if(req.mode==='navigate'){const cp=r.clone();caches.open(CACHE).then(c=>c.put('/frank',cp));}\n"
    "    return r;\n"
    "  }).catch(()=>caches.match(req).then(m=>m||caches.match('/frank'))));\n"
    "});\n"
)


@app.get("/frank-manifest.webmanifest")
def frank_manifest():
    return JSONResponse(_FRANK_MANIFEST, media_type="application/manifest+json")


@app.get("/frank-sw.js")
def frank_service_worker():
    return Response(
        content=_FRANK_SW_JS,
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/frank"},
    )


# ── Health / Diagnostics ───────────────────────────────────────────────────────


@app.get("/health")
def health():
    # build + persistence are surfaced here so deploy version and durable-volume state
    # can be confirmed at a glance without auth. persistent=False means the /data
    # Railway Volume is NOT attached — the DB and the Files-area volume are running on
    # ephemeral storage that resets every redeploy (diagnosed 2026-06-17, ops_runbook).
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "build": _BUILD_ID,
        "persistent": db.is_persistent(),
        "files_volume": "volume" in _FILE_ROOTS,
    }


@app.get("/api/ping")
def ping():
    """Public diagnostic endpoint — no auth. Visit this URL to confirm server state."""
    uptime_s = round((datetime.now(timezone.utc) - _SERVER_START).total_seconds())
    etsy_shop_test: str
    try:
        shop = EtsyAPIClient().get_shop()
        etsy_shop_test = f"ok — {shop.get('shop_name', '?')}"
    except Exception as exc:
        etsy_shop_test = f"error: {str(exc)[:120]}"
    return {
        "build": _BUILD_ID,
        "uptime_seconds": uptime_s,
        "env": {
            "APP_SECRET_TOKEN": bool(os.getenv("APP_SECRET_TOKEN")),
            "ETSY_ACCESS_TOKEN": bool(os.getenv("ETSY_ACCESS_TOKEN")),
            "ETSY_REFRESH_TOKEN": bool(os.getenv("ETSY_REFRESH_TOKEN")),
            "ETSY_API_KEY": bool(os.getenv("ETSY_API_KEY")),
            "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
        },
        "etsy_shop_test": etsy_shop_test,
        "db": db.db_info(),
    }


# ── Data layer (shared by REST endpoints AND the CEO agent's tools) ──────────────


def _build_metrics(orders_r, reviews_r, shop_r) -> dict:
    """Pure transform of three raw Etsy responses into the dashboard snapshot.
    Each input may be an Exception (one call failed) — handled per-section."""
    now = int(time.time())
    day = 86_400
    out: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "listings": {},
        "orders": {},
        "reviews": {},
        "shop": {},
    }

    if isinstance(orders_r, Exception):
        out["orders"]["error"] = str(orders_r)
    else:
        orders = orders_r.get("results", [])

        def _revenue(order_list):
            total = 0.0
            for o in order_list:
                gt = o.get("grandtotal", {})
                if isinstance(gt, dict):
                    divisor = gt.get("divisor", 100) or 100
                    total += gt.get("amount", 0) / divisor
            return round(total, 2)

        o7 = [o for o in orders if o.get("create_timestamp", 0) > now - 7 * day]
        o30 = [o for o in orders if o.get("create_timestamp", 0) > now - 30 * day]
        out["orders"] = {
            "last_7_days": len(o7),
            "last_30_days": len(o30),
            "revenue_7d": _revenue(o7),
            "revenue_30d": _revenue(o30),
            "all_time_count": len(orders),
            "all_time_revenue": _revenue(orders),
        }

    if isinstance(reviews_r, Exception):
        out["reviews"]["error"] = str(reviews_r)
    else:
        reviews = reviews_r.get("results", [])
        ratings = [r["rating"] for r in reviews if r.get("rating")]
        out["reviews"] = {
            "total_count": reviews_r.get("count", len(reviews)),
            "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
            "five_star_pct": round(sum(1 for r in ratings if r == 5) / len(ratings) * 100) if ratings else 0,
        }

    if isinstance(shop_r, Exception):
        out["shop"]["error"] = str(shop_r)
    else:
        active_count = shop_r.get("listing_active_count", 0)
        out["shop"] = {
            "name": shop_r.get("shop_name", business_config.BUSINESS_NAME),
            "active_listing_count": active_count,
            "total_sales": shop_r.get("transaction_sold_count", 0),
            "on_vacation": shop_r.get("is_vacation", False),
        }
        out["listings"]["active_count"] = active_count

    return out


def _metrics_sync() -> dict:
    """Cached business snapshot, blocking. Shared by the agent tool and the
    async endpoint (which warms/uses the same 'metrics' cache key)."""
    cached = _cache_get("metrics", ttl=60)
    if cached is not None:
        return cached
    client = EtsyAPIClient()
    orders_r = reviews_r = shop_r = None
    try:
        orders_r = client.get_orders(limit=100)
    except Exception as exc:
        orders_r = exc
    try:
        reviews_r = client.get_reviews(limit=50)
    except Exception as exc:
        reviews_r = exc
    try:
        shop_r = client.get_shop()
    except Exception as exc:
        shop_r = exc
    out = _build_metrics(orders_r, reviews_r, shop_r)
    _cache_set("metrics", out)
    return out


def _listings_sync(state: str = "active") -> dict:
    """Cached listing list (title/price/views/favorites/tags), blocking."""
    if state not in ("active", "draft", "inactive", "expired", "sold_out"):
        raise ValueError("state must be active, draft, inactive, expired, or sold_out")
    cache_key = f"listings_{state}"
    cached = _cache_get(cache_key, ttl=30)
    if cached is not None:
        return cached

    raw = EtsyAPIClient().get_shop_listings_all(state=state)
    listings = []
    for l in raw:
        images = l.get("images", [])
        thumb = ""
        if images:
            thumb = (
                images[0].get("url_570xN")
                or images[0].get("url_fullxfull")
                or images[0].get("url_75x75", "")
            )
        listings.append(
            {
                "listing_id": l.get("listing_id"),
                "title": l.get("title", ""),
                "price": _price_float(l.get("price")),
                "state": l.get("state", state),
                "views": l.get("views", 0),
                "num_favorers": l.get("num_favorers", 0),
                "tags": l.get("tags", [])[:13],
                "thumbnail_url": thumb,
                "url": f"https://www.etsy.com/listing/{l.get('listing_id')}",
                "created_timestamp": l.get("creation_timestamp", 0),
                "shop_section_id": l.get("shop_section_id"),
            }
        )
    result = {"listings": listings, "count": len(listings), "state": state}
    _cache_set(cache_key, result)
    return result


def _sales_by_listing_sync() -> dict:
    """Map real per-listing sales from paid order receipts → transactions.

    Etsy receipts each carry a `transactions` array where every transaction has
    a `listing_id` and `quantity`. Summing these gives true units sold per
    listing — the honest denominator for conversion (favorites are NOT sales).
    Based on the 100 most recent paid receipts; cached 2 min. Returns
    {listing_id: units_sold}."""
    cached = _cache_get("sales_by_listing", ttl=120)
    if cached is not None:
        return cached
    out: dict = {}
    try:
        orders_r = EtsyAPIClient().get_orders(limit=100)
        for receipt in orders_r.get("results", []) or []:
            for t in receipt.get("transactions", []) or []:
                lid = t.get("listing_id")
                if lid is None:
                    continue
                try:
                    qty = int(t.get("quantity", 1) or 1)
                except (TypeError, ValueError):
                    qty = 1
                out[lid] = out.get(lid, 0) + qty
    except Exception as exc:  # never let a sales lookup break a listing fetch
        print(f"[sales] receipt mapping failed: {exc}", flush=True)
    _cache_set("sales_by_listing", out)
    return out


def _enrich_sales(listings: list[dict]) -> list[dict]:
    """Attach real `sales` count and sales-based `conversion_pct` to each listing.

    conversion_pct = units sold ÷ views × 100 (the true buy rate). Falls back to
    0 when there are no views yet. Mutates in place and returns the list."""
    sales = _sales_by_listing_sync()
    for l in listings:
        s = sales.get(l.get("listing_id"), 0)
        v = l.get("views", 0) or 0
        l["sales"] = s
        l["conversion_pct"] = round(s / v * 100, 2) if v else 0.0
    return listings


# ── REST endpoints (thin async wrappers over the data layer) ─────────────────────


@app.get("/api/metrics")
async def get_metrics(_token: str = Depends(_auth)):
    """Live business snapshot. 3 Etsy calls in parallel; result cached 60 s."""
    cached = _cache_get("metrics", ttl=60)
    if cached is not None:
        return cached
    try:
        orders_r, reviews_r, shop_r = await asyncio.wait_for(
            asyncio.gather(
                asyncio.to_thread(lambda: EtsyAPIClient().get_orders(limit=100)),
                asyncio.to_thread(lambda: EtsyAPIClient().get_reviews(limit=50)),
                asyncio.to_thread(lambda: EtsyAPIClient().get_shop()),
                return_exceptions=True,
            ),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    out = _build_metrics(orders_r, reviews_r, shop_r)
    _cache_set("metrics", out)
    return out


@app.get("/api/listings")
async def get_listings(state: str = "active", _token: str = Depends(_auth)):
    """Return listings with thumbnail URLs. Result cached 30 s."""
    if state not in ("active", "draft", "inactive"):
        raise HTTPException(status_code=400, detail="state must be active, draft, or inactive")

    def _fetch():
        data = _listings_sync(state)
        if state == "active":  # drafts/inactive can't have sales
            _enrich_sales(data.get("listings", []))
        return data

    try:
        return await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=20.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")


def _shop_sections_sync() -> list[dict]:
    """Shop section (category) id → title map. Sections change rarely; cached 1h."""
    cached = _cache_get("shop_sections", ttl=3600)
    if cached is not None:
        return cached
    try:
        sections = EtsyAPIClient().get_shop_sections()
    except Exception as exc:  # never let a sections lookup break the listings view
        print(f"[sections] fetch failed: {exc}", flush=True)
        sections = []
    result = [
        {"shop_section_id": s.get("shop_section_id"), "title": s.get("title", "")}
        for s in sections
    ]
    _cache_set("shop_sections", result)
    return result


@app.get("/api/shop-sections")
async def shop_sections(_token: str = Depends(_auth)):
    """Shop sections (Etsy's listing categories) for the Listings filter chips."""
    try:
        sections = await asyncio.wait_for(asyncio.to_thread(_shop_sections_sync), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    return {"sections": sections}


@app.get("/api/listings/{listing_id}/files")
async def listing_files(listing_id: int, _token: str = Depends(_auth)):
    """Digital files attached to a listing — powers the Listings tab expand-to-detail view."""
    cache_key = f"listing_files_{listing_id}"
    cached = _cache_get(cache_key, ttl=300)
    if cached is not None:
        return cached

    def _fetch():
        return EtsyAPIClient().get_listing_files(listing_id)

    try:
        raw = await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    files = []
    for f in raw:
        size_bytes = f.get("size_bytes")
        files.append(
            {
                "file_id": f.get("listing_file_id"),
                "filename": f.get("filename", ""),
                "size_human": _human_size(size_bytes) if size_bytes else "",
                "rank": f.get("rank"),
                "create_timestamp": f.get("create_timestamp"),
            }
        )
    result = {"listing_id": listing_id, "count": len(files), "files": files}
    _cache_set(cache_key, result)
    return result


@app.post("/api/listings/{listing_id}/state")
async def set_listing_state(listing_id: int, new_state: str, _token: str = Depends(_auth)):
    """Activate or deactivate a listing — powers the Activate/Deactivate button in the
    Listings tab detail panel. Scott clicks this directly; it is not something any
    agent calls autonomously."""
    if new_state not in ("active", "inactive"):
        raise HTTPException(status_code=400, detail="new_state must be active or inactive")

    def _update():
        client = EtsyAPIClient()
        # PATCH listings/{id} has a documented non-deterministic 403
        # ("listing is not editable") that's a server-side race condition,
        # not a real permission error — retry a couple times before giving up.
        return retry_with_backoff(
            lambda: client.update_listing(listing_id, {"state": new_state}),
            max_attempts=3,
            base_delay=2.0,
            max_delay=8.0,
            retryable=lambda e: isinstance(e, EtsyAPIError) and e.status == 403,
        )

    try:
        result = await asyncio.wait_for(asyncio.to_thread(_update), timeout=20.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    except EtsyAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    with _cache_lock:
        _cache.pop("listings_active", None)
        _cache.pop("listings_inactive", None)
    return {"listing_id": listing_id, "state": result.get("state", new_state)}


# ── Action Center (deterministic rules engine — surfaces priorities) ─────────────

# Severity ordering for sorting (lower = more urgent).
_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


def _compute_actions() -> dict:
    """Scan live drafts + active listings and return ranked action cards.

    Pure deterministic rules over data Etsy already gives us — no LLM, no
    guessing, so it is fast and never invents a problem. The CEO agent can be
    asked to expand on any card. Rules align with CLAUDE.md's 2026 standards.
    """
    now = int(time.time())
    day = 86_400
    cards: list[dict] = []

    def add(severity, category, title, detail, suggestion, listing=None):
        lid = listing.get("listing_id") if listing else None
        cards.append(
            {
                "id": f"{category}:{lid}" if lid else category,
                "severity": severity,
                "category": category,
                "title": title,
                "detail": detail,
                "suggestion": suggestion,
                "listing_id": lid,
                "url": listing.get("url") if listing else None,
                "impact": (listing or {}).get("views", 0),
            }
        )

    # Drafts awaiting publish — highest leverage, they earn nothing in draft.
    try:
        drafts = _listings_sync("draft").get("listings", [])
    except Exception as exc:
        drafts = []
        add("medium", "data_error",
            "Couldn't load drafts",
            f"Etsy draft fetch failed: {exc}",
            "Retry shortly; if it persists, check the Etsy connection on /api/ping.")
    for l in drafts:
        add("high", "draft_unpublished",
            f"Publish: {l['title'][:60]}" if l.get("title") else "Publish draft listing",
            "This listing is in draft and earning nothing while live.",
            "Run the pre-publish quality gate, then approve to publish.",
            l)

    # Active listings — SEO + conversion hygiene.
    try:
        active = _enrich_sales(_listings_sync("active").get("listings", []))
    except Exception as exc:
        active = []
        add("medium", "data_error",
            "Couldn't load active listings",
            f"Etsy active fetch failed: {exc}",
            "Retry shortly; if it persists, check the Etsy connection on /api/ping.")

    for l in active:
        title = l.get("title", "") or ""
        tags = l.get("tags", []) or []
        views = l.get("views", 0) or 0
        favs = l.get("num_favorers", 0) or 0
        sales = l.get("sales", 0) or 0
        created = l.get("created_timestamp", 0) or 0
        age_days = (now - created) / day if created else 0

        if len(title) > 70:
            add("high", "title_too_long",
                f"Title over 70 chars ({len(title)}): {title[:50]}",
                f"Title is {len(title)} characters. Etsy applies a mobile ranking "
                "penalty above 70, and 70%+ of traffic is mobile.",
                "Trim to ≤70 chars, keeping the primary keyword in the first 40.",
                l)

        if len(tags) < 13:
            add("medium", "tags_incomplete",
                f"Only {len(tags)}/13 tags: {title[:50]}",
                f"This listing uses {len(tags)} of 13 tag slots. Every empty slot "
                "is a missed ranking opportunity.",
                "Add multi-word buyer-intent tags to fill all 13 slots.",
                l)

        if views >= 25 and sales == 0:
            add("high", "low_conversion",
                f"{views} views, 0 sales: {title[:50]}",
                f"{views} people viewed this but nobody bought"
                + (f" ({favs} favorited it — interest is there)" if favs else "")
                + " — a photo, price, or description problem, not a traffic problem.",
                "Tap Diagnose in the Conversion Doctor for a ranked fix.",
                l)

        if views == 0 and age_days > 7:
            add("medium", "zero_views",
                f"No views in {int(age_days)} days: {title[:50]}",
                f"Live for {int(age_days)} days with 0 views — a visibility/SEO "
                "problem (tags or title not matching searches).",
                "Audit tags/title for buyer search terms; the agent can draft them.",
                l)

    cards.sort(key=lambda c: (_SEVERITY_RANK.get(c["severity"], 9), -c.get("impact", 0)))
    summary = {
        "high": sum(1 for c in cards if c["severity"] == "high"),
        "medium": sum(1 for c in cards if c["severity"] == "medium"),
        "low": sum(1 for c in cards if c["severity"] == "low"),
        "total": len(cards),
    }
    return {"summary": summary, "actions": cards, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/actions")
async def get_actions(_token: str = Depends(_auth)):
    """Ranked priorities computed from live listings. Cached 120 s."""
    cached = _cache_get("actions", ttl=120)
    if cached is not None:
        return cached
    try:
        data = await asyncio.wait_for(asyncio.to_thread(_compute_actions), timeout=25.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    _cache_set("actions", data)
    return data


# ── Shared background-loop retry/backoff/heartbeat helper ────────────────────────

_LOOP_FAILURE_COUNTS: dict[str, int] = {}
_LOOP_BACKOFF_BASE_DELAY = 5.0  # seconds -- seed for jittered exponential backoff


async def _run_loop_iteration(
    name: str,
    label: str,
    fn,
    *,
    on_success_detail="ok",
    on_success_status="ok",
    on_error_detail=None,
    base_interval: float,
    max_interval: float = 3600.0,
) -> float:
    """Run one iteration of a background loop with a shared heartbeat +
    jittered-exponential-backoff policy.

    Before this helper, each of the 5 background loops (`_snapshot_loop`,
    `_warm_suggestions`, `_token_sync_loop`, `_quality_audit_loop`,
    `_health_check_loop`) slept a fixed interval regardless of whether the
    last run failed -- a flaky dependency either got hammered every interval
    or, on the daily loops, sat broken for up to 24h before the next retry.
    This centralizes the resilience.py pattern (full-jitter exponential
    backoff, consecutive-failure tracking, reset on success) so every loop
    gets the same graceful-degradation behavior for free.

    `fn` is called with no arguments and may be async. On success, the
    failure counter for `name` resets to 0 and the heartbeat is recorded via
    `on_success_status`/`on_success_detail` (each may be a plain value or a
    callable taking fn()'s return value -- this lets a loop report "error"
    even on a clean run, e.g. a quality audit that ran fine but found
    failing listings). On an exception, the heartbeat is recorded "error"
    (detail via `on_error_detail(exc)` if given, else `str(exc)[:300]`) and
    the failure counter increments.

    Returns the number of seconds the caller should `await asyncio.sleep()`
    before the next iteration: `base_interval` on success, or a full-jitter
    backoff delay (seeded at `_LOOP_BACKOFF_BASE_DELAY`, doubling per
    consecutive failure, capped at `max_interval`) on failure. This never
    bypasses the Action Center approval gate -- it only changes how often a
    read-only/internal loop retries, never whether a mutation is allowed.
    """
    try:
        result = await fn()
        _LOOP_FAILURE_COUNTS[name] = 0
        detail = on_success_detail(result) if callable(on_success_detail) else on_success_detail
        status = on_success_status(result) if callable(on_success_status) else on_success_status
        db.set_agent_heartbeat(name, label, status, detail)
        return base_interval
    except Exception as exc:
        n = _LOOP_FAILURE_COUNTS.get(name, 0) + 1
        _LOOP_FAILURE_COUNTS[name] = n
        delay = min(max_interval, _LOOP_BACKOFF_BASE_DELAY * (2 ** (n - 1)))
        delay = random.uniform(0, delay)  # full jitter
        detail = on_error_detail(exc) if on_error_detail else str(exc)[:300]
        print(f"[{name}] error (attempt {n}, retrying in {delay:.0f}s): {exc}", flush=True)
        db.set_agent_heartbeat(name, label, "error", str(detail)[:300])
        return delay


# ── Persistence: daily snapshots + history ───────────────────────────────────────


async def _take_snapshot() -> str:
    """Capture today's metrics + active listings into the database (upsert/day)."""
    metrics = await asyncio.to_thread(_metrics_sync)
    listings = (await asyncio.to_thread(_listings_sync, "active")).get("listings", [])
    d = await asyncio.to_thread(db.record_metric_snapshot, metrics, listings)
    print(f"[snapshot] recorded {d}: {len(listings)} listings, persistent={db.is_persistent()}", flush=True)
    return d


async def _snapshot_loop() -> None:
    """Snapshot at startup, then once every 24h (sooner on a backoff retry
    after a failure). Upsert-by-day means repeated runs on the same calendar
    day just refresh that day's row (no duplicates)."""
    while True:
        delay = await _run_loop_iteration(
            "snapshot", "Snapshot", _take_snapshot,
            on_success_detail="Daily metric snapshot recorded",
            base_interval=86_400,
        )
        # Daily recycle-bin prune (tools/trash.py): drop deletions older than 30 days.
        # Piggybacks on this already-daily loop so expiry is time-based and durable on
        # the live server — no separate cron needed (and no harness-cron 7-day expiry).
        # Tolerant of its own errors -- a prune failure must never affect the
        # snapshot's own success/backoff timing above.
        try:
            from tools.trash import prune as _trash_prune
            n = await asyncio.to_thread(_trash_prune)
            if n:
                print(f"[trash] pruned {n} expired entr{'y' if n == 1 else 'ies'}", flush=True)
        except Exception as exc:
            print(f"[trash] prune error: {exc}", flush=True)
        await asyncio.sleep(delay)


async def _warm_suggestions() -> None:
    """Keep the CEO diagnostic cache permanently warm. The synthesis takes ~60s and
    the in-memory cache is wiped on every redeploy, so without this the dashboard
    user stares at the 'analyzing your shop…' spinner for a full minute every time
    the cache is cold (seen 2026-06-16). We prime it ~5s after boot, then refresh a
    little before the TTL expires so a visitor practically never lands on a cold
    cache — only the one-time ~60s window right after a fresh deploy remains."""
    if not ANTHROPIC_KEY:
        db.set_agent_heartbeat("suggestion_warmer", "Suggestion Warmer", "error", "ANTHROPIC_API_KEY not set")
        return
    await asyncio.sleep(5)  # let the app finish booting first

    async def _iteration():
        res = await _compute_suggestions()
        if res.get("error") == "parse_failed":
            # Not cached (see _compute_suggestions) — a TransientToolError so the
            # shared helper backs off quickly and retries, rather than waiting the
            # full refresh-before-TTL interval.
            raise TransientToolError("suggestions parse failed")
        return res

    while True:
        delay = await _run_loop_iteration(
            "suggestion_warmer", "Suggestion Warmer", _iteration,
            on_success_detail="CEO diagnostic cache primed",
            # HTTPExceptions from _compute_suggestions wrap the real cause in .detail
            # (e.g. "Could not gather shop data: <Etsy error>"). Passing them through
            # _friendly_error_message produces the generic "Something went wrong" fallback
            # which hides the actual cause. Extract .detail first; only call
            # _friendly_error_message for raw Anthropic errors that don't have .detail.
            on_error_detail=lambda exc: (
                str(getattr(exc, "detail", None) or exc)[:300]
                if hasattr(exc, "detail")
                else _friendly_error_message(exc)
            ),
            base_interval=_SUGGESTIONS_TTL - 120,  # refresh just before expiry
            max_interval=120,
        )
        await asyncio.sleep(delay)


async def _token_sync_loop() -> None:
    """Persist Etsy token rotations to the durable /data DB as they happen.

    tools/etsy_api.py's refresh_access_token() updates os.environ in-memory the
    moment it rotates, and tries to write .env — fine on Scott's machine, but
    Railway's filesystem is ephemeral so that write doesn't survive a restart.
    Polling os.environ here (instead of modifying etsy_api.py) keeps the fix
    isolated to this server and changes zero behavior for any other consumer
    (CI, Scott's local scripts) that imports etsy_api.py directly."""
    last_tokens = {
        "access": os.getenv("ETSY_ACCESS_TOKEN", "").strip(),
        "refresh": os.getenv("ETSY_REFRESH_TOKEN", "").strip(),
    }

    async def _iteration():
        cur_access = os.getenv("ETSY_ACCESS_TOKEN", "").strip()
        cur_refresh = os.getenv("ETSY_REFRESH_TOKEN", "").strip()
        if cur_access and cur_refresh and (cur_access != last_tokens["access"] or cur_refresh != last_tokens["refresh"]):
            await asyncio.to_thread(db.save_etsy_tokens, cur_access, cur_refresh, last_tokens["refresh"])
            print(f"[etsy-tokens] persisted rotated token to {db.DB_PATH}", flush=True)
            last_tokens["access"], last_tokens["refresh"] = cur_access, cur_refresh
            return "Etsy token rotation persisted"
        return "watching for token rotation"

    await asyncio.sleep(60)  # give the app a moment before the first poll
    while True:
        delay = await _run_loop_iteration(
            "token_sync", "Token Sync", _iteration,
            on_success_detail=lambda detail: detail,
            base_interval=60,
            max_interval=300,
        )
        await asyncio.sleep(delay)


_QUALITY_AUDIT_SUMMARY_RE = _re.compile(
    r"PASS:\s*(\d+).*?WARN:\s*(\d+).*?FAIL:\s*(\d+)", _re.DOTALL
)


async def _quality_audit_iteration() -> dict:
    """One run of the daily quality audit: rotate oversized KB files, run the
    read-only listing integrity check, record the trend, and escalate a FAIL
    finding to ops_runbook.md. Raises on a genuine run failure (subprocess
    error, unparseable output) so `_run_loop_iteration` backs off and retries
    sooner than the normal 24h cadence; returns a result dict on a clean run
    even if the audit itself found failing listings (that's a content-level
    signal surfaced via `on_success_status`, not a loop failure)."""
    for kb_path in (_OPS_RUNBOOK_PATH, _CEO_LEARNINGS_PATH):
        try:
            if await asyncio.to_thread(_summarize_and_rotate_kb_file, kb_path):
                print(f"[kb-rotate] condensed older history in {kb_path.name}", flush=True)
        except Exception as exc:
            print(f"[kb-rotate] check failed for {kb_path.name}: {exc}", flush=True)

    try:
        if await asyncio.to_thread(_promote_recurring_failures, _OPS_RUNBOOK_PATH):
            print("[ops-runbook] refreshed Known Recurring Issues section", flush=True)
    except Exception as exc:
        print(f"[ops-runbook] recurring-issues check failed: {exc}", flush=True)

    # data/ is excluded from the Docker build context (.dockerignore), so
    # listing_manifest.json won't exist in fresh Railway deployments until
    # build_manifest.py has been run at least once. Skip gracefully rather
    # than crashing the loop — the heartbeat will surface this as a warning.
    manifest_path = ROOT / "data" / "listing_manifest.json"
    if not await asyncio.to_thread(manifest_path.exists):
        print("[quality-audit] skipping — listing_manifest.json not found (run build_manifest.py)", flush=True)
        return {"skipped": True, "passed": 0, "warned": 0, "failed": 0,
                "reason": "listing_manifest.json not found — run build_manifest.py first"}

    result = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, str(ROOT / "tools" / "listing_integrity_check.py")],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=str(ROOT),
    )
    out = (result.stdout or "") + "\n" + (result.stderr or "")
    m = _QUALITY_AUDIT_SUMMARY_RE.search(out)
    if not m:
        raise RuntimeError(f"could not parse summary line; script output: {out[:300]!r}")
    passed, warned, failed = (int(g) for g in m.groups())
    blocks = out.split("—" * 70)
    header_idx = next((i for i, b in enumerate(blocks) if "✗ FAIL (" in b), None)
    fail_block = blocks[header_idx + 1] if header_idx is not None and header_idx + 1 < len(blocks) else ""
    summary = fail_block.strip()[:1500]
    try:
        db.record_quality_audit(passed, warned, failed, summary)
    except Exception as exc:
        print(f"[quality-audit] db record failed: {exc}", flush=True)
    print(f"[quality-audit] PASS:{passed} WARN:{warned} FAIL:{failed}", flush=True)
    if failed > 0:
        _append_ops_runbook_entry(
            f"Automated quality audit — {failed} listing(s) failing",
            f"Daily listing_integrity_check found {failed} FAIL / {warned} WARN out of "
            f"{passed + warned + failed} listings audited. Details:\n{summary or '(see logs)'}",
        )
    return {"passed": passed, "warned": warned, "failed": failed}


async def _quality_audit_loop() -> None:
    """Run the read-only listing integrity check once a day and log the trend.

    Uses fast mode (no --full, no --fix-titles) — this only reads from Etsy and
    writes to the local data/listing_manifest.json cache; it never touches a
    live listing, so it needs no approval gate. Results go to the quality_audits
    DB table for trend tracking, and — only when a FAIL is found — a short entry
    is auto-appended to ops_runbook.md so the regression surfaces to Frank/Scott
    without anyone needing to remember to run the check manually."""
    await asyncio.sleep(120)  # let the app finish booting first
    while True:
        delay = await _run_loop_iteration(
            "quality_audit", "Quality Audit", _quality_audit_iteration,
            on_success_status=lambda r: "warning" if r.get("skipped") else ("error" if r["failed"] > 0 else "ok"),
            on_success_detail=lambda r: r.get("reason", f"PASS:{r['passed']} WARN:{r['warned']} FAIL:{r['failed']}"),
            base_interval=86_400,
        )
        await asyncio.sleep(delay)


async def _health_check_iteration() -> dict:
    """One health-check pass: reap finished background processes, ping Etsy +
    confirm the Anthropic key is set, and escalate to ops_runbook.md if either
    dependency is down. Etsy/Anthropic outages are content-level findings (an
    "error" heartbeat status) rather than loop failures, so they don't trigger
    `_run_loop_iteration`'s own retry backoff -- the check itself ran fine."""
    for pid, (proc, cmd_name, started_at) in list(_LONG_RUNNING_PROCS.items()):
        if proc.poll() is not None:  # finished (crashed or completed)
            age_s = (datetime.now(timezone.utc) - started_at).total_seconds()
            print(
                f"[health-check] reaped {cmd_name} (pid {pid}, ran {age_s:.0f}s, "
                f"exit={proc.returncode})",
                flush=True,
            )
            del _LONG_RUNNING_PROCS[pid]

    etsy_ok = True
    etsy_detail = "ok"
    etsy_exc: Exception | None = None
    try:
        shop = await asyncio.to_thread(EtsyAPIClient().get_shop)
        etsy_detail = f"ok — {shop.get('shop_name', '?')}"
    except Exception as exc:
        etsy_ok = False
        etsy_detail = f"error: {str(exc)[:200]}"
        etsy_exc = exc

    anthropic_ok = bool(os.getenv("ANTHROPIC_API_KEY"))
    all_ok = etsy_ok and anthropic_ok
    detail = f"Etsy: {etsy_detail} | Anthropic key set: {anthropic_ok}"
    if not all_ok:
        context = f"5-minute health loop detected a problem: {detail}"
        if etsy_exc is not None:
            # Tier 2/3 -- classify the actual Etsy exception rather than just
            # logging its string. Anthropic-key-missing (no exception, just an
            # unset env var) is handled as its own known cause below.
            _escalate_failure(context, etsy_exc)
        elif not anthropic_ok:
            _append_ops_runbook_entry(
                "Automated health check failure (known cause)",
                f"{context}\n\n**Diagnosis:** {_KNOWN_FAILURE_REMEDIATIONS['anthropic_key_missing']}",
            )
        else:
            _append_ops_runbook_entry("Automated health check failure", context)
    return {"all_ok": all_ok, "detail": detail[:300]}


async def _health_check_loop() -> None:
    """Every 5 minutes: confirm Etsy + Anthropic credentials are actually live (the
    same checks /api/ping exposes manually, run here on a timer so a regression
    surfaces in ops_runbook.md without anyone needing to remember to hit that URL),
    and reap any long_running background processes (coloring page generation, etc.)
    started via _run_exec_command so a finished/crashed child never sits untracked
    forever in _LONG_RUNNING_PROCS."""
    await asyncio.sleep(60)  # let the app finish booting first
    while True:
        delay = await _run_loop_iteration(
            "health_check", "Health Check", _health_check_iteration,
            on_success_status=lambda r: "ok" if r["all_ok"] else "error",
            on_success_detail=lambda r: r["detail"],
            base_interval=300,
        )
        await asyncio.sleep(delay)


async def _daily_brief_loop() -> None:
    """Fire a daily shop-status email at 6 AM UTC. Checks once per hour.

    Does not use _run_loop_iteration because the timing logic is calendar-based
    (once per calendar day) rather than interval-based (every N seconds).
    Failures are logged but never crash the server.
    """
    db.set_agent_heartbeat("daily_brief", "Daily Brief", "started", "waiting for 6 AM UTC")
    last_sent_date: date | None = None
    while True:
        await asyncio.sleep(3600)
        now = datetime.utcnow()
        if now.hour == 6 and now.date() != last_sent_date:
            db.set_agent_heartbeat("daily_brief", "Daily Brief", "running", "generating brief")
            try:
                from tools.daily_brief import run_daily_brief
                result = await asyncio.to_thread(run_daily_brief)
                last_sent_date = now.date()
                db.set_agent_heartbeat("daily_brief", "Daily Brief", "ok", result)
                print(f"[daily_brief] {result}", flush=True)
            except Exception as exc:
                db.set_agent_heartbeat("daily_brief", "Daily Brief", "error", str(exc))
                print(f"[daily_brief] error: {exc}", flush=True)
        else:
            next_run = "today" if now.hour < 6 else "tomorrow"
            db.set_agent_heartbeat(
                "daily_brief", "Daily Brief", "ok",
                f"next brief {next_run} at 06:00 UTC (last sent: {last_sent_date or 'never'})"
            )


_AGENT_LOOP_LABELS = {
    "snapshot": "Snapshot",
    "suggestion_warmer": "Suggestion Warmer",
    "token_sync": "Token Sync",
    "quality_audit": "Quality Audit",
    "health_check": "Health Check",
    "daily_brief": "Daily Brief",
}


@app.on_event("startup")
async def _startup() -> None:
    try:
        db.init_db()
        print(f"[db] ready at {db.DB_PATH} (persistent={db.is_persistent()})", flush=True)
    except Exception as exc:
        print(f"[db] init failed: {exc}", flush=True)
    etsy_api.set_circuit_breaker_hook(CircuitBreaker("etsy_api", db_module=db))
    # Seed every loop's row immediately so the Agents registry always reports
    # all 5 from boot, rather than waiting on each loop's own startup delay
    # (some sleep minutes before their first real run).
    for _name, _label in _AGENT_LOOP_LABELS.items():
        try:
            db.set_agent_heartbeat(_name, _label, "started", "waiting for first run")
        except Exception as exc:
            print(f"[agent-heartbeat] seed failed for {_name}: {exc}", flush=True)
    asyncio.create_task(_snapshot_loop())
    asyncio.create_task(_warm_suggestions())
    asyncio.create_task(_token_sync_loop())
    asyncio.create_task(_quality_audit_loop())
    asyncio.create_task(_health_check_loop())
    asyncio.create_task(_daily_brief_loop())


@app.post("/api/brief/run")
async def run_brief_now(request: Request):
    """Manually trigger the daily brief (for testing). Requires X-App-Token header."""
    token = request.headers.get("X-App-Token", "")
    if not secrets.compare_digest(token.encode(), _APP_SECRET_TOKEN.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")
    from tools.daily_brief import run_daily_brief
    result = await asyncio.to_thread(run_daily_brief)
    return {"status": result}


@app.get("/api/analytics")
async def get_analytics(days: int = 30, _token: str = Depends(_auth)):
    """Trend data from daily snapshots + live top-listing performance.

    Returns parallel trend arrays (oldest→newest) for sparkline charting,
    period deltas (latest minus earliest in the window), and top 10 active
    listings ranked by all-time views with conversion rate.
    """
    days = max(7, min(days, 90))
    rows = await asyncio.to_thread(db.get_metric_history, days)

    trends = {
        "revenue_30d": [r.get("revenue_30d") for r in rows],
        "orders_30d": [r.get("orders_30d") for r in rows],
        "active_listings": [r.get("active_listings") for r in rows],
        "total_sales": [r.get("total_sales") for r in rows],
    }
    dates = [r.get("snapshot_date") for r in rows]

    delta: dict = {}
    if len(rows) >= 2:
        first, last = rows[0], rows[-1]
        for k in ("revenue_30d", "orders_30d", "active_listings", "total_sales", "avg_rating"):
            a, b = first.get(k), last.get(k)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                delta[k] = round(b - a, 4)

    top_listings: list[dict] = []
    try:
        listing_data = await asyncio.wait_for(
            asyncio.to_thread(_listings_sync, "active"), timeout=15.0
        )
        active = _enrich_sales(listing_data.get("listings", []))
        top = sorted(active, key=lambda l: l.get("views", 0), reverse=True)[:10]
        top_listings = [
            {
                "listing_id": l["listing_id"],
                "title": (l.get("title") or "")[:60],
                "views": l.get("views", 0),
                "num_favorers": l.get("num_favorers", 0),
                "sales": l.get("sales", 0),
                "price": l.get("price", 0),
                "url": l.get("url", ""),
                # True buy rate: units sold ÷ views (not favorites).
                "conversion_pct": l.get("conversion_pct", 0.0),
            }
            for l in top
            if l.get("views", 0) > 0
        ]
    except Exception as exc:
        print(f"[analytics] top_listings enrichment failed (non-blocking): {exc}", flush=True)

    return {
        "days": days,
        "snapshot_count": len(rows),
        "dates": dates,
        "trends": trends,
        "delta": delta,
        "latest": rows[-1] if rows else {},
        "top_listings": top_listings,
    }


# True while a CEO-diagnostic synthesis is in flight, so the endpoint and the warm
# loop never kick off two at once and the endpoint can answer "warming, poll again"
# instead of blocking a request for the full ~60s synthesis.
_suggestions_warming = False


async def _run_suggestions_safely() -> None:
    """Fire-and-forget wrapper: compute suggestions, swallow errors (they're logged
    elsewhere). Used to kick off a warm from the request path without blocking it."""
    try:
        await _compute_suggestions()
    except Exception as exc:  # noqa: BLE001
        print(f"[suggestions] background compute failed: {exc}", flush=True)


async def _compute_suggestions() -> dict:
    """Gather shop data + synthesise the CEO diagnostic JSON. Caches the result.
    Shared by the /api/suggestions endpoint and the startup cache-warmer so the
    dashboard never has to wait on a cold cache right after a deploy."""
    global _suggestions_warming
    if not ANTHROPIC_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    _suggestions_warming = True
    try:
        return await _compute_suggestions_inner()
    finally:
        _suggestions_warming = False


async def _compute_suggestions_inner() -> dict:
    """The actual data-gather + synthesis. Wrapped by _compute_suggestions which
    manages the _suggestions_warming flag."""
    # Gather the three data pulls DIRECTLY in Python instead of making the model
    # call them as tools. The old approach forced 3 sequential Claude round-trips
    # (call -> result -> call -> result -> call -> result -> synthesis) which took
    # ~80s on a cold cache — close enough to the frontend's 120s limit that the
    # dashboard spinner looked stuck, especially right after a deploy wiped the
    # cache (seen 2026-06-16, see ops runbook). We know exactly which 3 pulls we
    # need, so we run them concurrently and do ONE synthesis call — ~25s total.
    try:
        metrics, active, drafts = await asyncio.gather(
            asyncio.to_thread(_execute_agent_tool, "get_metrics", {}),
            asyncio.to_thread(_execute_agent_tool, "list_listings", {"state": "active"}),
            asyncio.to_thread(_execute_agent_tool, "list_listings", {"state": "draft"}),
        )
    except Exception as exc:  # noqa: BLE001 — surface a real message, not a bare 500
        raise HTTPException(status_code=502, detail=f"Could not gather shop data: {exc}")

    ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    user_payload = (
        "Here is the shop's real data. Analyze all of it and return the JSON report.\n\n"
        "=== METRICS ===\n" + json.dumps(metrics, default=str) + "\n\n"
        "=== ACTIVE LISTINGS ===\n" + json.dumps(active, default=str) + "\n\n"
        "=== DRAFT LISTINGS ===\n" + json.dumps(drafts, default=str)
    )

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: _anthropic_create(
                    ai_client,
                    model="claude-sonnet-4-6",
                    max_tokens=4000,  # 8 detailed suggestions overrun 2400 and truncate
                    system=_SUGGESTIONS_SYSTEM + _ops_runbook_block(),
                    messages=[{"role": "user", "content": user_payload}],
                )
            ),
            timeout=90.0,  # single call; comfortably under the frontend's 120s
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Anthropic took too long to respond. This usually self-resolves — tap Try Again.",
        )
    except anthropic.APIError as exc:
        print(f"[suggestions] Anthropic API error: {exc}", flush=True)
        raise HTTPException(status_code=502, detail=_friendly_error_message(exc))

    final_text = "".join(getattr(b, "text", "") for b in response.content)
    parsed = _extract_json_object(final_text)
    now = datetime.now(timezone.utc).isoformat()
    if not isinstance(parsed, dict):
        # Don't poison the 30-min cache with a broken parse (e.g. a truncated
        # response). Return the fallback to this caller but leave the cache cold
        # so the warm loop / next request recomputes instead of serving garbage.
        return {
            "headline": "Analysis complete",
            "suggestions": [],
            "raw": final_text,
            "error": "parse_failed",
            "generated_at": now,
        }

    parsed["generated_at"] = now
    _cache_set("suggestions", parsed)
    return parsed


@app.post("/api/suggestions")
async def get_suggestions(_token: str = Depends(_auth)):
    """CEO agent synthesises a structured JSON suggestion report from live shop
    data (metrics + active + draft listings). A background loop keeps the cache
    warm so this is normally an instant hit. If the cache IS cold (the ~75s window
    right after a deploy), we do NOT block the request for a full minute — that's
    what made the dashboard spinner look stuck. Instead we make sure a synthesis is
    running and return 202 'warming' immediately; the frontend polls until ready."""
    cached = _cache_get("suggestions", ttl=_SUGGESTIONS_TTL)
    if cached is not None:
        return cached

    if not _suggestions_warming:
        asyncio.create_task(_run_suggestions_safely())
    return JSONResponse(
        status_code=202,
        content={
            "status": "warming",
            "headline": "Analyzing your shop… first run after an update takes up to a minute.",
            "suggestions": [],
        },
    )


# ── Conversion Doctor: find traffic-but-no-sales listings + diagnose one ──────────


_CONV_TARGETS_TTL = 120  # 2-minute cache — fast enough to stay fresh, eliminates repeat Etsy API calls

async def _get_conversion_targets_core() -> dict:
    """Active listings getting views but no sales — the Conversion Doctor's worklist.

    Sorted by views descending (most wasted traffic first), top 10. Listings with
    favorites but zero sales rank as the strongest signal (proven interest, no buy).
    Shared by the REST route and the get_conversion_targets chat tool.
    """
    def _fetch():
        active = _enrich_sales(_listings_sync("active").get("listings", []))
        targets = [l for l in active if (l.get("views", 0) or 0) > 0 and (l.get("sales", 0) or 0) == 0]
        targets.sort(key=lambda l: (l.get("num_favorers", 0) or 0, l.get("views", 0) or 0), reverse=True)
        return targets[:10]

    try:
        targets = await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=20.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    return {
        "count": len(targets),
        "targets": [
            {
                "listing_id": l["listing_id"],
                "title": l.get("title", ""),
                "views": l.get("views", 0),
                "num_favorers": l.get("num_favorers", 0),
                "sales": l.get("sales", 0),
                "price": l.get("price", 0),
                "url": l.get("url", ""),
                "thumbnail_url": l.get("thumbnail_url", ""),
            }
            for l in targets
        ],
    }


@app.get("/api/conversion-targets")
async def conversion_targets(_token: str = Depends(_auth)):
    cached = _cache_get("conv_targets", ttl=_CONV_TARGETS_TTL)
    if cached is not None:
        return cached
    result = await _get_conversion_targets_core()
    _cache_set("conv_targets", result)
    return result


async def _diagnose_listing_core(listing_id: int) -> dict:
    """Deep conversion diagnosis of ONE listing. Pulls full listing detail (title,
    price, description, tags) + photo count + real sales, then a single focused
    Claude call returns a structured, listing-specific diagnosis. Shared by the REST
    route and the diagnose_listing_conversion chat tool — note this makes its own
    nested Claude call, same as _autofix_title_core."""
    if not ANTHROPIC_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    def _gather() -> dict:
        client = EtsyAPIClient()
        listing = client.get_listing(listing_id)
        try:
            photo_count = len(client.get_listing_images(listing_id))
        except Exception:
            photo_count = 0
        sales = _sales_by_listing_sync().get(listing_id, 0)
        return {"listing": listing, "photo_count": photo_count, "sales": sales}

    try:
        gathered = await asyncio.wait_for(asyncio.to_thread(_gather), timeout=20.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    except EtsyAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Etsy: {exc}")

    listing = gathered["listing"]
    title = listing.get("title", "") or ""
    tags = listing.get("tags", []) or []
    views = listing.get("views", 0) or 0
    favs = listing.get("num_favorers", 0) or 0
    sales = gathered["sales"]
    price = _price_float(listing.get("price"))
    desc = (listing.get("description", "") or "").strip()
    photo_count = gathered["photo_count"]

    stats = {
        "title": title,
        "title_length": len(title),
        "price": round(price, 2),
        "photo_count": photo_count,
        "tag_count": len(tags),
        "views": views,
        "favorites": favs,
        "sales": sales,
        "conversion_pct": round(sales / views * 100, 2) if views else 0.0,
    }

    user_payload = (
        "Diagnose why this listing isn't converting. Real data:\n\n"
        f"TITLE ({len(title)} chars): {title}\n"
        f"PRICE: ${price:.2f}\n"
        f"PHOTOS: {photo_count} of 10 recommended\n"
        f"TAGS ({len(tags)}/13): {', '.join(tags) if tags else '(none)'}\n"
        f"VIEWS: {views}   FAVORITES: {favs}   UNITS SOLD: {sales}\n\n"
        "FULL DESCRIPTION:\n"
        f"{desc[:6000] if desc else '(empty)'}\n"
    )

    ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: _anthropic_create(
                    ai_client,
                    model="claude-sonnet-4-6",
                    max_tokens=2000,
                    system=_CONVERSION_DOCTOR_SYSTEM,
                    messages=[{"role": "user", "content": user_payload}],
                )
            ),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Diagnosis timed out — try again")
    except anthropic.APIError as exc:
        print(f"[conversion_doctor] Anthropic API error: {exc}", flush=True)
        raise HTTPException(status_code=502, detail=_friendly_error_message(exc))

    text = "".join(getattr(b, "text", "") for b in response.content).strip()
    diagnosis = _extract_json_object(text)
    if diagnosis is None:
        diagnosis = {"primary_issue": "Analysis complete", "fixes": [], "raw": text}

    result = {
        "listing_id": listing_id,
        "url": f"https://www.etsy.com/listing/{listing_id}",
        "stats": stats,
        "diagnosis": diagnosis,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return result


@app.post("/api/diagnose/{listing_id}")
async def diagnose_listing(listing_id: int, _token: str = Depends(_auth)):
    cache_key = f"diagnose_{listing_id}"
    cached = _cache_get(cache_key, ttl=600)
    if cached is not None:
        return cached
    result = await _diagnose_listing_core(listing_id)
    _cache_set(cache_key, result)
    return result


async def _fetch_listing_for_autofix(listing_id: int) -> dict:
    """Shared Etsy fetch for the autofix helpers below — raises HTTPException
    with an actionable message on any failure, never a bare 500."""
    def _fetch():
        return EtsyAPIClient().get_listing(listing_id)

    try:
        return await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout")
    except EtsyAPIError as exc:
        if getattr(exc, "status", None) == 404:
            raise HTTPException(status_code=404, detail=f"Listing {listing_id} not found on Etsy (it may be expired/deleted)")
        raise HTTPException(status_code=502, detail=f"Etsy: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch listing {listing_id}: {exc}")


async def _autofix_tags_core(listing_id: int, listing: dict | None = None, reason: str = "") -> dict:
    """Generate a fresh 13-tag set for one listing and stage an update_tags action.

    `reason` is optional human feedback (a Scott reject reason) folded into the
    prompt as explicit corrective guidance. Never raises — returns {"error": str}
    on any failure so callers (an HTTP route or the reject-fix dispatcher) can
    decide how to surface it."""
    if not ANTHROPIC_KEY:
        return {"error": "ANTHROPIC_API_KEY not configured", "listing_id": listing_id}
    if listing is None:
        listing = await _fetch_listing_for_autofix(listing_id)

    listing_data = {
        "listing_id": listing_id,
        "title": listing.get("title", ""),
        "price": _price_float(listing.get("price")),
        "tags": listing.get("tags", []),
    }
    try:
        tag_results = await asyncio.wait_for(
            asyncio.to_thread(_generate_tags_for_listings, [listing_data], reason),
            timeout=60.0,
        )
    except Exception as exc:
        return {"error": f"Tag generation failed: {exc}", "listing_id": listing_id}
    if not tag_results:
        return {"error": "Tag generation returned no results", "listing_id": listing_id}

    # Everything below is local work (string cleaning, validation, DB enqueue).
    # It must never surface as a bare HTTP 500 — wrap it so any failure comes back
    # as a clear message the dashboard can show (this was the "tags: HTTP 500"
    # with no detail seen 2026-06-17, see ops_runbook.md).
    try:
        raw_tags = tag_results[0].get("tags", [])
        tags = [_clean_tag(t) for t in raw_tags if str(t).strip()]
        seen: set = set()
        tags = [t for t in tags if t and not (t in seen or seen.add(t))]

        payload = {"listing_id": listing_id, "tags": tags, "_state_at_staging": listing.get("state")}
        candidate = {"type": "update_tags", "payload": payload}
        ok, msg = _validate_staged_action(candidate)
        if not ok:
            return {"error": f"Quality gate: {msg}", "listing_id": listing_id}

        title_short = (listing.get("title") or f"Listing {listing_id}")[:50]
        prefix = "Reject-fix tag" if reason else "Auto tag fix"
        summary = f"{prefix} ({len(tags)}/13): {title_short}"
        action_id = db.enqueue_action("update_tags", summary, payload)
    except Exception as exc:
        return {"error": f"Could not stage tag fix: {exc}", "listing_id": listing_id}

    with _cache_lock:
        _cache.pop("actions", None)

    return {"action_id": action_id, "tags": tags, "listing_id": listing_id}


async def _autofix_title_core(listing_id: int, listing: dict | None = None, reason: str = "") -> dict:
    """Generate a corrected ≤70-char title for one listing and stage an
    update_title action. `reason` is optional human feedback (a Scott reject
    reason) appended to the prompt as explicit corrective guidance. Never
    raises — returns {"error": str} on any failure."""
    if not ANTHROPIC_KEY:
        return {"error": "ANTHROPIC_API_KEY not configured", "listing_id": listing_id}
    if listing is None:
        listing = await _fetch_listing_for_autofix(listing_id)

    title = listing.get("title", "")
    tags = ", ".join(listing.get("tags", []))
    price = _price_float(listing.get("price"))
    desc = (listing.get("description", "") or "")[:500]
    prompt = _TITLE_FIX_PROMPT.format(title=title, price=f"{price:.2f}", tags=tags, desc=desc)
    if reason:
        prompt += (
            "\n\nREVIEWER REJECTED THE PREVIOUS TITLE WITH THIS FEEDBACK — "
            f"fix this specifically:\n{reason}"
        )

    ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: _anthropic_create(
                    ai_client,
                    model="claude-haiku-4-5-20251001",
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}],
                )
            ),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        return {"error": "Title generation timed out", "listing_id": listing_id}
    except Exception as exc:
        return {"error": f"Title generation failed: {exc}", "listing_id": listing_id}

    try:
        new_title = "".join(getattr(b, "text", "") for b in response.content).strip().strip('"\'')

        payload = {"listing_id": listing_id, "title": new_title, "_state_at_staging": listing.get("state")}
        candidate = {"type": "update_title", "payload": payload}
        ok, msg = _validate_staged_action(candidate)
        if not ok:
            return {"error": f"Quality gate: {msg}", "listing_id": listing_id}

        prefix = "Reject-fix title" if reason else "Auto title fix"
        summary = f"{prefix}: {new_title[:50]}"
        action_id = db.enqueue_action("update_title", summary, payload)
    except Exception as exc:
        return {"error": f"Could not stage title fix: {exc}", "listing_id": listing_id}

    with _cache_lock:
        _cache.pop("actions", None)

    return {"action_id": action_id, "title": new_title, "listing_id": listing_id}


@app.post("/api/autofix/tags/{listing_id}")
async def autofix_tags(listing_id: int, _token: str = Depends(_auth)):
    """Generate 13 correct tags for one listing and stage an update_tags action.

    Calls Claude once for this specific listing, validates the tags through
    the quality gate, then enqueues the action for Scott's one-tap approval.
    Nothing touches Etsy until Scott taps Approve in the Action Center."""
    result = await _autofix_tags_core(listing_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return {"staged": True, **result}


@app.post("/api/autofix/title/{listing_id}")
async def autofix_title(listing_id: int, _token: str = Depends(_auth)):
    """Generate a corrected ≤70-char title and stage an update_title action.

    Calls Claude once with the listing's full context, validates through the
    quality gate (hard ≤70-char rule), then enqueues for Scott's approval.
    Nothing touches Etsy until Scott taps Approve in the Action Center."""
    result = await _autofix_title_core(listing_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return {"staged": True, **result}


@app.post("/api/autofix/draft/{listing_id}")
async def autofix_draft(listing_id: int, _token: str = Depends(_auth)):
    """Auto-fix a draft listing's title and tags in one shot.

    Generates a corrected ≤70-char title AND a full 13-tag set, validates both
    through the quality gate, and enqueues them as separate pending approvals.
    Nothing touches Etsy until Scott taps Approve on each fix. After approving
    the fixes, Scott can then approve the original publish_listing action."""
    listing = await _fetch_listing_for_autofix(listing_id)

    staged: list[dict] = []
    errors: list[str] = []

    tag_result = await _autofix_tags_core(listing_id, listing=listing)
    if "error" in tag_result:
        errors.append(f"tags: {tag_result['error']}")
    else:
        staged.append({"type": "update_tags", "action_id": tag_result["action_id"]})

    title_result = await _autofix_title_core(listing_id, listing=listing)
    if "error" in title_result:
        errors.append(f"title: {title_result['error']}")
    else:
        staged.append({
            "type": "update_title",
            "action_id": title_result["action_id"],
            "title": title_result["title"],
        })

    return {
        "staged": staged,
        "staged_count": len(staged),
        "errors": errors,
        "listing_id": listing_id,
    }


@app.post("/api/snapshot")
async def post_snapshot(_token: str = Depends(_auth)):
    """Force-capture a snapshot now (useful for testing / on-demand recording)."""
    try:
        d = await asyncio.wait_for(_take_snapshot(), timeout=25.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    return {"recorded": d, "db": db.db_info()}


# ── Staged actions (agent prepares → Scott approves → server executes) ────────────

_ETSY_STAGED_ACTION_TYPES = (
    "update_tags", "update_title", "publish_listing", "deactivate_listing", "toggle_listing_state",
)
_LOCAL_STAGED_ACTION_TYPES = ("local_write_file", "local_delete", "local_exec")
_SCRIPT_STAGED_ACTION_TYPES = ("run_script",)
_PHOTO_STAGED_ACTION_TYPES = ("listing_photo",)
_VIDEO_STAGED_ACTION_TYPES = ("listing_video",)
_REGISTER_COMMAND_STAGED_ACTION_TYPES = ("register_command",)
_STAGED_ACTION_TYPES = (
    _ETSY_STAGED_ACTION_TYPES + _LOCAL_STAGED_ACTION_TYPES
    + _SCRIPT_STAGED_ACTION_TYPES + _PHOTO_STAGED_ACTION_TYPES
    + _VIDEO_STAGED_ACTION_TYPES + _REGISTER_COMMAND_STAGED_ACTION_TYPES
)


_EXPECTED_LISTING_PHOTO_SIZE = (2400, 2400)  # CLAUDE.md standard listing photo spec


def _check_no_pale_background(path: Path) -> str | None:
    """Port of QualityGate.check_no_pale_background (business_pipeline.py) — samples the
    4 corners and rejects a washed-out/pale background (CARDINAL CHECK spirit: a listing
    photo that looks AI-blank or low-effort is always wrong). Returns an error message on
    failure, None on pass. Hard block, not a warning -- unlike the dimension check below."""
    try:
        from PIL import Image
        img = Image.open(path).convert("RGB")
        w, h = img.size
        s = 30
        corners = [
            img.crop((0, 0, s, s)),
            img.crop((w - s, 0, w, s)),
            img.crop((0, h - s, s, h)),
            img.crop((w - s, h - s, w, h)),
        ]
        for corner in corners:
            pixels = list(corner.getdata())
            avg_r = sum(p[0] for p in pixels) / len(pixels)
            avg_g = sum(p[1] for p in pixels) / len(pixels)
            avg_b = sum(p[2] for p in pixels) / len(pixels)
            luminance = 0.299 * avg_r + 0.587 * avg_g + 0.114 * avg_b
            if luminance > 217:  # ~85% of 255 -- too light/pale
                return f"photo background too pale (corner luminance {luminance:.0f}/255) -- looks washed out"
    except Exception as exc:
        print(f"[quality-gate] pale-background check skipped ({path.name}): {exc}", flush=True)
        return None
    return None


def _warn_if_unexpected_photo_dimensions(path: Path) -> None:
    """Port of QualityGate.check_image_dimensions, downgraded to a logged warning rather
    than a hard block -- legitimate photo slots can vary in source size before the listing
    pipeline resizes them, so this is informational, not gating."""
    try:
        from PIL import Image
        w, h = Image.open(path).size
        ew, eh = _EXPECTED_LISTING_PHOTO_SIZE
        if abs(w - ew) > 10 or abs(h - eh) > 10:
            print(f"[quality-gate] {path.name} is {w}x{h}, expected ~{ew}x{eh} square", flush=True)
    except Exception as exc:
        print(f"[quality-gate] dimension check skipped ({path.name}): {exc}", flush=True)


def _validate_staged_action(a: dict, *, at_approval: bool = False) -> tuple[bool, str]:
    """Quality gate run BOTH at stage time and again at approve time. The gate is
    code — a change that violates the 2026 standards can never be applied.

    `at_approval=True` additionally re-fetches the listing's live state from Etsy
    and refuses if it changed since the action was staged (e.g. Scott deactivated
    it manually in the meantime). Only the approval-time call pays for that
    network round trip -- staging stays a single fast local validation."""
    t = a.get("type")
    p = a.get("payload", {}) or {}
    if t not in _STAGED_ACTION_TYPES:
        return False, f"unsupported action type: {t}"
    if t in _ETSY_STAGED_ACTION_TYPES:
        if not p.get("listing_id"):
            return False, "missing listing_id"
        if t == "update_title":
            title = (p.get("title") or "").strip()
            if not title:
                return False, "title is empty"
            if len(title) > 70:
                return False, f"title is {len(title)} chars — max 70 (mobile ranking rule)"
        if t == "update_tags":
            tags = p.get("tags")
            if not isinstance(tags, list) or not tags:
                return False, "tags must be a non-empty list"
            if len(tags) > 13:
                return False, f"{len(tags)} tags — Etsy allows max 13"
            for tg in tags:
                if not isinstance(tg, str) or not tg.strip():
                    return False, "tags contain an empty value"
                if len(tg) > 20:
                    return False, f"tag '{tg}' exceeds 20 characters"
        if t == "toggle_listing_state":
            new_state = p.get("new_state")
            if new_state not in ("active", "inactive"):
                return False, "new_state must be 'active' or 'inactive'"
        if at_approval:
            try:
                current = EtsyAPIClient().get_listing(int(p["listing_id"]))
            except Exception as exc:
                return False, f"could not reconfirm listing {p['listing_id']} before applying: {exc}"
            staged_state = p.get("_state_at_staging")
            current_state = current.get("state")
            if staged_state is not None and current_state != staged_state:
                return False, (
                    f"listing {p['listing_id']} state changed since this action was staged "
                    f"(was '{staged_state}', now '{current_state}') -- review and re-stage"
                )
        return True, "ok"
    if t in _PHOTO_STAGED_ACTION_TYPES:
        if not p.get("listing_id"):
            return False, "missing listing_id"
        rank = p.get("rank")
        if not isinstance(rank, int) or isinstance(rank, bool) or not (1 <= rank <= 10):
            return False, "rank must be an integer 1-10"
        path = (p.get("path") or "").strip()
        if not path:
            return False, "missing path"
        try:
            target = _resolve_in_root("staged_photos", path)
        except HTTPException:
            return False, f"path escapes the staged_photos root: {path}"
        if not target.is_file():
            return False, f"staged photo file not found: {path}"
        pale_msg = _check_no_pale_background(target)
        if pale_msg:
            return False, pale_msg
        _warn_if_unexpected_photo_dimensions(target)
        return True, "ok"
    if t in _VIDEO_STAGED_ACTION_TYPES:
        if not p.get("listing_id"):
            return False, "missing listing_id"
        rank = p.get("rank")
        if rank is not None and (not isinstance(rank, int) or isinstance(rank, bool) or not (1 <= rank <= 10)):
            return False, "rank must be an integer 1-10 (or omitted)"
        path = (p.get("path") or "").strip()
        if not path:
            return False, "missing path"
        try:
            target = _resolve_in_root("staged_videos", path)
        except HTTPException:
            return False, f"path escapes the staged_videos root: {path}"
        if not target.is_file():
            return False, f"staged video file not found: {path}"
        return True, "ok"
    # Local types — the real security boundary is the relay's own realpath check
    # at execution time (it's the only thing with Scott's actual filesystem to
    # resolve against); this is fast UX feedback at staging time only.
    if t in ("local_write_file", "local_delete"):
        path = (p.get("path") or "").strip()
        if not path:
            return False, "missing path"
        if not db.is_path_allowed(path):
            return False, f"path not in an Allowed Folder: {path}"
        if t == "local_write_file" and p.get("after") is None:
            return False, "missing file content"
    elif t == "local_exec":
        command = p.get("command")
        if command not in _LOCAL_EXEC_COMMANDS:
            return False, f"unknown local command: {command}"
        extra_args = (p.get("extra_args") or "").strip()
        if extra_args:
            bad = [
                part for part in extra_args.split()
                if any(f in part.lower() for f in _LOCAL_FORBIDDEN_EXEC_FLAGS)
            ]
            if bad:
                return False, f"extra_args {bad} are not allowed on a local command"
    elif t == "run_script":
        command = p.get("command")
        if command not in _EXEC_COMMANDS:
            return False, f"unknown command: {command}"
        if not _EXEC_COMMANDS[command].get("requires_approval"):
            return False, f"{command} does not require approval — run it directly from Workflows"
        extra_args = (p.get("extra_args") or "").strip()
        if extra_args:
            bad = [pt for pt in extra_args.split() if any(f in pt.lower() for f in _FORBIDDEN_EXEC_FLAGS)]
            if bad:
                return False, f"extra_args {bad} are not allowed"
    elif t == "register_command":
        command_name = (p.get("command_name") or "").strip()
        script_path = (p.get("script_path") or "").strip()
        if not command_name:
            return False, "missing command_name"
        if command_name in _EXEC_COMMANDS:
            return False, f"command_name '{command_name}' is already registered — pick a different name"
        if not script_path:
            return False, "missing script_path"
        if ".." in script_path.replace("\\", "/").split("/"):
            return False, "script_path must not contain '..'"
        try:
            target = (ROOT / script_path).resolve()
        except Exception:
            return False, f"invalid script_path: {script_path}"
        tools_root = (ROOT / "tools").resolve()
        if tools_root != target and tools_root not in target.parents:
            return False, "script_path must resolve under tools/"
        if not target.is_file():
            return False, f"script_path does not exist on disk: {script_path}"
        timeout = p.get("timeout")
        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
            return False, "timeout must be a positive integer"
    return True, "ok"


def _retryable_etsy_error(exc: Exception) -> bool:
    """Rate limit / server-side hiccup worth one more try -- never a reason to
    re-issue a *new* mutation, only to retry the one already-approved call."""
    return isinstance(exc, EtsyAPIError) and exc.status in (429, 500, 502, 503)


def _execute_staged_action(a: dict) -> dict:
    """Apply an approved action to Etsy via update_listing, then bust caches.

    Every Etsy call is wrapped in retry_with_backoff -- this only retries an
    *already-approved* mutation on a transient 429/5xx, it never decides
    whether a mutation happens (that's still the Action Center approval gate,
    enforced by the caller before this function is ever invoked)."""
    t = a["type"]
    p = a.get("payload", {}) or {}
    lid = p["listing_id"]
    client = EtsyAPIClient()

    def _retry(fn):
        return retry_with_backoff(fn, max_attempts=3, base_delay=1.0, max_delay=10.0, retryable=_retryable_etsy_error)

    if t == "update_tags":
        res = _retry(lambda: client.update_listing(lid, {"tags": p["tags"]}))
    elif t == "update_title":
        res = _retry(lambda: client.update_listing(lid, {"title": p["title"].strip()}))
    elif t == "publish_listing":
        res = _retry(lambda: client.update_listing(lid, {"state": "active"}))
    elif t == "deactivate_listing":
        res = _retry(lambda: client.update_listing(lid, {"state": "inactive"}))
    elif t == "toggle_listing_state":
        res = _retry(lambda: client.update_listing(lid, {"state": p["new_state"]}))
    elif t == "listing_photo":
        abs_path = _resolve_in_root("staged_photos", p["path"])
        if not abs_path.is_file():
            raise FileNotFoundError(f"staged photo not found: {p['path']}")
        img = _retry(lambda: client.upload_listing_image(lid, str(abs_path), rank=p.get("rank", 1)))
        with _cache_lock:
            for k in ("listings_active", "listings_draft", "listings_inactive", "actions", "metrics"):
                _cache.pop(k, None)
        return {
            "listing_id": lid,
            "etsy": {
                "listing_image_id": img.get("listing_image_id"),
                "rank": img.get("rank"),
                "url": img.get("url_570xN") or img.get("url_fullxfull"),
            },
        }
    elif t == "listing_video":
        abs_path = _resolve_in_root("staged_videos", p["path"])
        if not abs_path.is_file():
            raise FileNotFoundError(f"staged video not found: {p['path']}")
        vid = _retry(lambda: client.upload_listing_video(lid, str(abs_path), rank=p.get("rank")))
        with _cache_lock:
            for k in ("listings_active", "listings_draft", "listings_inactive", "actions", "metrics"):
                _cache.pop(k, None)
        return {
            "listing_id": lid,
            "etsy": {
                "listing_video_id": vid.get("listing_video_id") or vid.get("video_id"),
                "rank": vid.get("rank"),
            },
        }
    else:
        raise ValueError(f"unsupported type {t}")
    with _cache_lock:
        for k in ("listings_active", "listings_draft", "listings_inactive", "actions", "metrics"):
            _cache.pop(k, None)
    return {
        "listing_id": lid,
        "etsy": {
            "listing_id": res.get("listing_id"),
            "state": res.get("state"),
            "title": res.get("title"),
        },
    }


def _execute_register_command_staged_action(a: dict) -> dict:
    """Apply an approved register_command action — writes the new command into
    the live _EXEC_COMMANDS dict and persists it to the registered_commands.json
    sidecar so it survives a restart. requires_approval is hardcoded True here
    too, not just at sidecar-load time, since this is the actual write path."""
    p = a.get("payload", {}) or {}
    command_name = p["command_name"]
    cfg = {
        "script": p["script_path"],
        "description": p.get("description", ""),
        "timeout": p["timeout"],
        "long_running": bool(p.get("long_running", False)),
        "requires_approval": True,
    }
    if p.get("args"):
        cfg["args"] = p["args"]

    try:
        existing = json.loads(_REGISTERED_COMMANDS_FILE.read_text()) if _REGISTERED_COMMANDS_FILE.is_file() else {}
    except Exception:
        existing = {}
    existing[command_name] = cfg
    _REGISTERED_COMMANDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _REGISTERED_COMMANDS_FILE.write_text(json.dumps(existing, indent=2))

    _EXEC_COMMANDS[command_name] = cfg
    return {"command_name": command_name, "script": cfg["script"], "registered": True}


async def _execute_local_staged_action(a: dict) -> dict:
    """Apply an approved local_write_file/local_delete/local_exec action — the
    actual mutation only ever happens here, after Scott's approval, via the same
    _dispatch_to_relay round-trip the instant tools use. Logged to activity_log
    (durable, separate from action_queue) regardless of outcome."""
    t = a["type"]
    p = a.get("payload", {}) or {}
    if t == "local_write_file":
        result = await _dispatch_to_relay("local_write_file", {"path": p["path"], "content": p["after"]})
    elif t == "local_delete":
        result = await _dispatch_to_relay("local_delete", {"path": p["path"]})
    elif t == "local_exec":
        result = await _dispatch_to_relay("local_exec", {"command": p["command"], "extra_args": p.get("extra_args", "")})
    else:
        raise ValueError(f"unsupported local type {t}")
    if "error" in result:
        await asyncio.to_thread(
            db.log_activity, "frank", t, a.get("summary", ""), p, outcome="error"
        )
        raise RuntimeError(result["error"])
    await asyncio.to_thread(db.log_activity, "frank", t, a.get("summary", ""), p, outcome="ok")
    return result


def _execute_script_staged_action(a: dict) -> dict:
    """Run an approved run_script action via the SAME in-process subprocess
    mechanism _EXEC_COMMANDS/execute_command already use — NOT the relay path
    local_exec uses. These scripts live on this server's filesystem, not
    Scott's machine. Logged to activity_log regardless of outcome."""
    p = a.get("payload", {}) or {}
    cmd_name = p["command"]
    result = _run_exec_command(cmd_name, (p.get("extra_args") or "").strip())
    db.log_activity(
        "frank", "run_script", a.get("summary", ""), p,
        outcome="ok" if result.get("success", True) else "error",
    )
    return result


@app.get("/api/queue")
async def get_queue(status: str = "pending", _token: str = Depends(_auth)):
    """List staged actions. status=pending (default) or 'all'."""
    st = None if status == "all" else status
    actions = await asyncio.to_thread(db.list_actions, st)
    return {"actions": actions, "count": len(actions)}


@app.post("/api/queue/{action_id}/approve")
async def approve_action(action_id: int, _token: str = Depends(_auth)):
    """Run the quality gate, then apply the change to Etsy. Records the result."""
    a = await asyncio.to_thread(db.get_action, action_id)
    if not a:
        raise HTTPException(status_code=404, detail="action not found")
    if a["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"action already {a['status']}")
    ok, msg = await asyncio.to_thread(_validate_staged_action, a, at_approval=True)
    if not ok:
        await asyncio.to_thread(db.set_action_status, action_id, "failed", {"error": f"gate failed: {msg}"})
        raise HTTPException(status_code=422, detail=f"quality gate failed: {msg}")
    is_local = a["type"] in _LOCAL_STAGED_ACTION_TYPES
    is_script = a["type"] in _SCRIPT_STAGED_ACTION_TYPES
    is_register_command = a["type"] in _REGISTER_COMMAND_STAGED_ACTION_TYPES
    if is_local:
        state = await asyncio.to_thread(db.get_relay_state)
        if state.get("killed"):
            raise HTTPException(status_code=409, detail="kill switch is engaged — local actions are suspended")
    # Mark "executing" before dispatch -- if the process crashes mid-execution, the
    # row is left at "executing" rather than "pending", so the `status != "pending"`
    # guard above blocks a retry-approval from firing a duplicate mutation.
    await asyncio.to_thread(db.set_action_status, action_id, "executing")
    try:
        if is_local:
            result = await asyncio.wait_for(_execute_local_staged_action(a), timeout=45.0)
        elif is_script:
            cfg_timeout = _EXEC_COMMANDS.get(a.get("payload", {}).get("command"), {}).get("timeout", 60)
            result = await asyncio.wait_for(
                asyncio.to_thread(_execute_script_staged_action, a), timeout=cfg_timeout + 5.0
            )
        elif is_register_command:
            result = await asyncio.wait_for(
                asyncio.to_thread(_execute_register_command_staged_action, a), timeout=15.0
            )
        else:
            result = await asyncio.wait_for(asyncio.to_thread(_execute_staged_action, a), timeout=45.0)
    except Exception as exc:
        await asyncio.to_thread(db.set_action_status, action_id, "failed", {"error": str(exc)})
        raise HTTPException(status_code=502, detail=f"execution failed: {exc}")
    await asyncio.to_thread(db.set_action_status, action_id, "executed", result)
    return {"status": "executed", "id": action_id, "result": result}


@app.post("/api/queue/{action_id}/reject")
async def reject_action(action_id: int, body: dict | None = None, _token: str = Depends(_auth)):
    """Reject a pending action. If `body` carries a non-empty `reason`, kick off the
    matching auto-fix in the background (fire-and-forget — the HTTP response doesn't
    wait on it) so the corrected replacement shows up as a new pending row shortly after."""
    a = await asyncio.to_thread(db.get_action, action_id)
    if not a:
        raise HTTPException(status_code=404, detail="action not found")
    if a["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"action already {a['status']}")
    reason = ((body or {}).get("reason") or "").strip()
    await asyncio.to_thread(db.set_action_status, action_id, "rejected", {"reason": reason} if reason else None)
    if reason:
        asyncio.create_task(_dispatch_reject_fix(a, reason))
    return {"status": "rejected", "id": action_id, "fix_started": bool(reason)}


async def _dispatch_reject_fix(action: dict, reason: str) -> None:
    """Best-effort auto-fix dispatcher run after a reject-with-reason. Never raises —
    any failure is logged to activity_log so it's visible in the ops runbook / activity
    feed instead of vanishing into a fire-and-forget task."""
    t = action.get("type")
    listing_id = (action.get("payload") or {}).get("listing_id")
    try:
        if t == "listing_photo":
            await _refix_listing_photo(action, reason)
        elif t == "update_title":
            result = await _autofix_title_core(listing_id, reason=reason)
            if "error" in result:
                raise RuntimeError(result["error"])
        elif t == "update_tags":
            result = await _autofix_tags_core(listing_id, reason=reason)
            if "error" in result:
                raise RuntimeError(result["error"])
        elif t == "publish_listing":
            title_result = await _autofix_title_core(listing_id, reason=reason)
            tags_result = await _autofix_tags_core(listing_id, reason=reason)
            errors = [r["error"] for r in (title_result, tags_result) if "error" in r]
            if errors:
                raise RuntimeError("; ".join(errors))
        else:
            # local_write_file, local_delete, local_exec, run_script, deactivate_listing —
            # no well-posed auto-retry from free-text feedback; the reason is already
            # recorded on the rejected action above.
            return
        db.log_activity("frank", "reject_fix", f"{t} #{action.get('id')}: {reason}", action, outcome="ok")
    except Exception as exc:
        db.log_activity("frank", "reject_fix", f"{t} #{action.get('id')}: {reason}", action,
                         outcome=f"error: {exc}")


async def _refix_listing_photo(action: dict, reason: str) -> dict:
    """Re-run generate_verified_photo() with the reject reason folded in as corrective
    feedback, then re-stage the result as a fresh listing_photo action chained to the
    original via fixes_action_id."""
    from tools.listing_photo_pipeline import generate_verified_photo

    p = action.get("payload") or {}
    sku = p.get("sku") or "unknown"
    physics = p.get("physics") or "sign_flat"
    design_paths = p.get("design_paths") or []
    scene_prompt = (p.get("scene_prompt") or "") + (
        f"\n\nADDITIONAL FEEDBACK FROM REVIEWER:\n{reason}"
    )

    safe_sku = _re.sub(r"[^A-Za-z0-9_.-]", "_", sku)
    out_dir = _FILE_ROOTS["staged_photos"] / safe_sku
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"photo_{uuid.uuid4().hex[:8]}.jpg"

    result = await asyncio.to_thread(
        generate_verified_photo, design_paths, scene_prompt, str(out_path), physics,
    )
    if not result.passed:
        raise RuntimeError(f"regeneration failed verification: {result.issues}")

    action_id = await _stage_photo_action(
        listing_id=p.get("listing_id"),
        rank=p.get("rank", 1),
        sku=sku,
        rel_path=f"{safe_sku}/{out_path.name}",
        summary=f"Reject-fix photo: {action.get('summary', '')}",
        physics=physics,
        scene_prompt=p.get("scene_prompt") or "",
        design_paths=design_paths,
        fixes_action_id=action.get("id"),
    )
    return {"action_id": action_id}


async def _stage_photo_action(
    listing_id, rank: int, sku: str, rel_path: str, summary: str,
    physics: str, scene_prompt: str, design_paths: list, fixes_action_id: int | None = None,
) -> int:
    """Validate and enqueue a listing_photo staged action. rel_path is relative to the
    staged_photos root (e.g. 'P3D_SCULPTURAL_MESH_LAMP/photo_ab12cd34.jpg')."""
    payload = {
        "listing_id": listing_id,
        "rank": rank,
        "path": rel_path,
        "sku": sku,
        "physics": physics,
        "scene_prompt": scene_prompt,
        "design_paths": design_paths,
    }
    if fixes_action_id is not None:
        payload["fixes_action_id"] = fixes_action_id
    fake_action = {"type": "listing_photo", "payload": payload}
    ok, msg = _validate_staged_action(fake_action)
    if not ok:
        raise ValueError(f"quality gate failed: {msg}")
    return await asyncio.to_thread(db.enqueue_action, "listing_photo", summary, payload)


async def _stage_video_action(listing_id, rel_path: str, summary: str, rank: int | None = None) -> int:
    """Validate and enqueue a listing_video staged action. rel_path is relative to the
    staged_videos root. Mirrors _stage_photo_action()'s pattern."""
    payload: dict = {"listing_id": listing_id, "path": rel_path}
    if rank is not None:
        payload["rank"] = rank
    fake_action = {"type": "listing_video", "payload": payload}
    ok, msg = _validate_staged_action(fake_action)
    if not ok:
        raise ValueError(f"quality gate failed: {msg}")
    return await asyncio.to_thread(db.enqueue_action, "listing_video", summary, payload)


@app.post("/api/queue/stage-photo")
async def stage_photo(
    request: Request,
    listing_id: int,
    rank: int,
    sku: str,
    summary: str = "",
    physics: str = "sign_flat",
    scene_prompt: str = "",
    design_paths: str = "[]",
    _token: str = Depends(_auth),
):
    """Stage a generated listing photo for Scott's approve/reject review. Body is the
    raw image bytes; everything else is a query param (same convention as
    /api/files/upload — this module has no multipart/UploadFile support).

    design_paths is a JSON-encoded list of source file paths used to generate the photo
    (kept on the action so a reject+reason can re-run generate_verified_photo() later
    without re-deriving anything)."""
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="empty body")
    if len(body) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {_human_size(_MAX_UPLOAD_BYTES)} limit")
    try:
        design_paths_list = json.loads(design_paths)
        if not isinstance(design_paths_list, list):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="design_paths must be a JSON-encoded list")

    safe_sku = _re.sub(r"[^A-Za-z0-9_.-]", "_", sku) or "unknown"
    out_dir = _FILE_ROOTS["staged_photos"] / safe_sku
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"photo_{uuid.uuid4().hex[:8]}.jpg"
    out_path.write_bytes(body)

    try:
        action_id = await _stage_photo_action(
            listing_id=listing_id,
            rank=rank,
            sku=sku,
            rel_path=f"{safe_sku}/{out_path.name}",
            summary=summary or f"Staged photo for listing {listing_id} (rank {rank})",
            physics=physics,
            scene_prompt=scene_prompt,
            design_paths=design_paths_list,
        )
    except ValueError as exc:
        out_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc))
    return {"action_id": action_id, "path": f"{safe_sku}/{out_path.name}"}


@app.post("/api/queue/stage-video")
async def stage_video(
    request: Request,
    listing_id: int,
    rank: int | None = None,
    summary: str = "",
    _token: str = Depends(_auth),
):
    """Stage a generated marketing video for Scott's approve/reject review before it's
    attached to an Etsy listing. Body is the raw video bytes (same convention as
    /api/queue/stage-photo — this module has no multipart/UploadFile support)."""
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="empty body")
    if len(body) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {_human_size(_MAX_UPLOAD_BYTES)} limit")

    out_dir = _FILE_ROOTS["staged_videos"] / str(listing_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"video_{uuid.uuid4().hex[:8]}.mp4"
    out_path.write_bytes(body)

    try:
        action_id = await _stage_video_action(
            listing_id=listing_id,
            rel_path=f"{listing_id}/{out_path.name}",
            summary=summary or f"Staged video for listing {listing_id}",
            rank=rank,
        )
    except ValueError as exc:
        out_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc))
    return {"action_id": action_id, "path": f"{listing_id}/{out_path.name}"}


# ── Studio tab (image-to-video generation + Instagram/Facebook posting) ───────────


@app.post("/api/studio/upload-image")
async def studio_upload_image(request: Request, filename: str, _token: str = Depends(_auth)):
    """Accept a raw image body and store it under studio_uploads/ so it can be picked
    for video generation. Same convention as /api/files/upload."""
    safe_name = os.path.basename((filename or "").strip())
    if not safe_name:
        raise HTTPException(status_code=400, detail="filename query param is required")
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="empty body")
    if len(body) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {_human_size(_MAX_UPLOAD_BYTES)} limit")
    root = _FILE_ROOTS["studio_uploads"]
    root.mkdir(parents=True, exist_ok=True)
    out_path = root / f"{uuid.uuid4().hex[:8]}_{safe_name}"
    out_path.write_bytes(body)
    return {"ok": True, "path": out_path.name, "size": len(body), "size_human": _human_size(len(body))}


@app.post("/api/studio/generate")
async def studio_generate_video(body: dict, _token: str = Depends(_auth)):
    """Generate a Ken Burns slideshow video either from an existing Etsy listing's
    photos (listing_id) or from previously-uploaded studio images (image_paths,
    filenames relative to studio_uploads/). Runs video_generator.generate_video()
    in-process — this is asset generation only (no Etsy mutation), so it needs no
    approval per CLAUDE.md's autonomy boundaries."""
    listing_id = body.get("listing_id")
    image_paths = body.get("image_paths") or []
    style = body.get("style", "showcase")
    title = (body.get("title") or "").strip()
    price = str(body.get("price") or "")
    digital = bool(body.get("digital", True))
    scene_prompt = (body.get("scene_prompt") or "").strip()
    aspect_ratio = (body.get("aspect_ratio") or "9:16").strip()

    if not listing_id and not image_paths:
        raise HTTPException(status_code=400, detail="provide either listing_id or image_paths")

    try:
        import video_generator          # inside try so ImportError surfaces as JSON 500
        from PIL import Image as _PILImage

        _ALL_STYLES = set(video_generator.STYLES) | {"ai-scene"}
        if style not in _ALL_STYLES:
            raise ValueError(f"style must be one of {sorted(_ALL_STYLES)}")

        if style == "ai-scene":
            import ai_video as _ai_video
            import tempfile as _tmp
            if listing_id:
                _eclient = EtsyAPIClient()
                _imgs_pil, _listing = video_generator.fetch_listing_images(int(listing_id), _eclient)
                _ai_imgs = []
                for _im in _imgs_pil:
                    _tf = _tmp.NamedTemporaryFile(suffix=".jpg", delete=False)
                    _im.save(_tf.name)
                    _ai_imgs.append(Path(_tf.name))
                _lid = str(listing_id)
                _sp = scene_prompt or f'Cinematic product video of "{title or _listing.get("title","product")}"'
            else:
                _ai_imgs = [_resolve_in_root("studio_uploads", n) for n in image_paths]
                for _p in _ai_imgs:
                    if not _p.is_file():
                        raise FileNotFoundError(f"studio upload not found: {_p.name}")
                _lid = "studio_" + uuid.uuid4().hex[:8]
                _sp = scene_prompt or f'Cinematic product video of "{title or "product"}"'
            out_path = await asyncio.wait_for(
                asyncio.to_thread(
                    _ai_video.generate_ai_video,
                    _ai_imgs, _sp, OPENAI_KEY,
                    10, aspect_ratio, _lid,
                ),
                timeout=300.0,
            )
        else:
            def _generate() -> Path:
                if listing_id:
                    client = EtsyAPIClient()
                    imgs, listing = video_generator.fetch_listing_images(int(listing_id), client)
                    t = title or listing.get("title", "")
                    p = price or video_generator.get_price_str(listing)
                    d = digital if "digital" in body else video_generator.is_digital(listing)
                    lid: int | str = listing_id
                else:
                    imgs = []
                    for name in image_paths:
                        target = _resolve_in_root("studio_uploads", name)
                        if not target.is_file():
                            raise FileNotFoundError(f"studio upload not found: {name}")
                        imgs.append(_PILImage.open(target).convert("RGB"))
                    t = title or "Product"
                    p = price
                    d = digital
                    lid = "studio_" + uuid.uuid4().hex[:8]
                return video_generator.generate_video(imgs, t, style, lid, price=p, digital=d)

            out_path = await asyncio.wait_for(asyncio.to_thread(_generate), timeout=180.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Video generation timed out")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("studio_generate_video error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Video generation failed: {type(exc).__name__}: {exc}")

    return {
        "ok": True,
        "path": out_path.name,
        "size": out_path.stat().st_size,
        "size_human": _human_size(out_path.stat().st_size),
    }


@app.get("/api/studio/videos")
async def studio_list_videos(_token: str = Depends(_auth)):
    """List generated videos under data/social/videos/ for the Studio sidebar."""
    root = _FILE_ROOTS["videos"]
    files = []
    if root.exists():
        for p in sorted(root.glob("*.mp4")):
            stat = p.stat()
            files.append({
                "path": p.name,
                "root": "videos",
                "size": stat.st_size,
                "size_human": _human_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
    files.sort(key=lambda f: f["modified"], reverse=True)
    return {"videos": files}


@app.get("/api/studio/diagnose")
async def studio_diagnose(_token: str = Depends(_auth)):
    """Probe Railway state: ffmpeg binary, directory writability, mini encode test."""
    import subprocess as _sp, os as _os, imageio_ffmpeg as _iio_ffmpeg
    r: dict = {"build_id": _BUILD_ID}

    # Use the same ffmpeg resolution logic as video_generator.py
    ffp = _iio_ffmpeg.get_ffmpeg_exe()
    r["ffmpeg_exe"] = ffp
    r["ffmpeg_exists"] = _os.path.exists(ffp)
    r["ffmpeg_executable"] = _os.access(ffp, _os.X_OK) if r["ffmpeg_exists"] else False
    try:
        v = _sp.run([ffp, "-version"], capture_output=True, text=True, timeout=10)
        r["ffmpeg_version_line"] = (v.stdout or v.stderr).split("\n")[0]
        r["ffmpeg_version_rc"] = v.returncode
    except Exception as _e:
        r["ffmpeg_version_error"] = str(_e)

    from pathlib import Path as _P
    for key, path in [("video_dir", _P("data/social/videos")), ("upload_dir", _P("studio_uploads"))]:
        try:
            path.mkdir(parents=True, exist_ok=True)
            (path / ".wtest").write_text("x")
            (path / ".wtest").unlink()
            r[f"{key}_writable"] = True
        except Exception as _e:
            r[f"{key}_writable"] = False
            r[f"{key}_error"] = str(_e)

    try:
        import numpy as _np, tempfile as _tf
        frame = _np.zeros((10, 10, 3), dtype=_np.uint8)
        with _tf.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            tmp = f.name
        cmd = [ffp, "-y", "-f", "rawvideo", "-vcodec", "rawvideo",  # ffp from get_ffmpeg_exe()
               "-s", "10x10", "-pix_fmt", "rgb24", "-r", "1", "-i", "pipe:0",
               "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-an", tmp]
        import threading as _th
        proc = _sp.Popen(cmd, stdin=_sp.PIPE, stderr=_sp.PIPE)
        frame_bytes = frame.tobytes()

        def _wr():
            try:
                proc.stdin.write(frame_bytes)
            except BrokenPipeError:
                pass
            finally:
                try: proc.stdin.close()
                except Exception: pass

        _wt = _th.Thread(target=_wr, daemon=True)
        _wt.start()
        stderr = proc.stderr.read()
        _wt.join(timeout=10)
        proc.wait(timeout=5)
        r["mini_encode_rc"] = proc.returncode
        if proc.returncode == 0:
            r["mini_encode_size"] = _os.path.getsize(tmp)
            r["mini_encode_ok"] = True
            _os.unlink(tmp)
        else:
            r["mini_encode_ok"] = False
            r["mini_encode_stderr"] = stderr.decode("utf-8", errors="replace")[-800:]
    except Exception as _e:
        r["mini_encode_ok"] = False
        r["mini_encode_error"] = str(_e)

    return r


@app.post("/api/studio/post-instagram")
async def studio_post_instagram(body: dict, _token: str = Depends(_auth)):
    """Post a generated video to Instagram as a Reel. Fires immediately on this call —
    there is no staging queue for social posts because, per CLAUDE.md, posting to
    social media is a Hard Stop that must always be an explicit, direct user action;
    the button click that triggers this request IS that explicit action."""
    import instagram_api

    if not instagram_api.is_configured():
        return {"error": "not configured", "detail": "INSTAGRAM_ACCESS_TOKEN is not set in .env"}

    video_name = (body.get("video") or "").strip()
    caption = body.get("caption", "")
    is_reel = bool(body.get("is_reel", True))
    target = _resolve_in_root("videos", video_name)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="video not found")

    railway_url = os.getenv("RAILWAY_APP_URL", "").rstrip("/")
    if not railway_url:
        return {"error": "not configured", "detail": "RAILWAY_APP_URL is not set — needed to serve the video to Instagram"}
    video_url = f"{railway_url}/api/files/download?root=videos&path={video_name}&token={APP_TOKEN}&inline=1"

    client = instagram_api.get_client()
    try:
        result = await asyncio.to_thread(client.post_video, video_url, caption, is_reel)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Instagram post failed: {exc}")
    db.log_activity("frank", "post_instagram", f"Posted {video_name} to Instagram", body, outcome="ok")
    return {"ok": True, "result": result}


@app.post("/api/studio/post-facebook")
async def studio_post_facebook(body: dict, _token: str = Depends(_auth)):
    """Post a generated video to the Facebook Page. Fires immediately on this call —
    same Hard Stop reasoning as studio_post_instagram() above: no staging queue,
    the button click itself is the required explicit action."""
    import facebook_api

    if not facebook_api.is_configured():
        return {"error": "not configured", "detail": "FACEBOOK_PAGE_ACCESS_TOKEN is not set in .env"}

    video_name = (body.get("video") or "").strip()
    description = body.get("caption", "")
    title = body.get("title", "")
    target = _resolve_in_root("videos", video_name)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="video not found")

    railway_url = os.getenv("RAILWAY_APP_URL", "").rstrip("/")
    if not railway_url:
        return {"error": "not configured", "detail": "RAILWAY_APP_URL is not set — needed to serve the video to Facebook"}
    video_url = f"{railway_url}/api/files/download?root=videos&path={video_name}&token={APP_TOKEN}&inline=1"

    client = facebook_api.get_client()
    try:
        result = await asyncio.to_thread(client.post_video, video_url, description, title)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Facebook post failed: {exc}")
    db.log_activity("frank", "post_facebook", f"Posted {video_name} to Facebook", body, outcome="ok")
    return {"ok": True, "result": result}


# ── Batch tag fix (one Claude call → staged approvals for every under-tagged listing) ─


@app.post("/api/batch/stage-tags")
async def batch_stage_tags(_token: str = Depends(_auth)):
    """Stage tag-fix actions for every active listing that has fewer than 13 tags.

    Calls Claude once (per batch of 40) to generate a corrected 13-tag set for
    each listing, validates each against the 2026 quality gate, and enqueues the
    passing ones as pending approvals. Scott reviews and approves from the Action
    Center — nothing touches Etsy until he taps Approve."""
    if not ANTHROPIC_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    # Fresh fetch — bypass cache so we see the real current state.
    with _cache_lock:
        _cache.pop("listings_active", None)

    try:
        data = await asyncio.wait_for(asyncio.to_thread(_listings_sync, "active"), timeout=25.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout fetching listings")

    listings = data.get("listings", [])
    to_fix = [l for l in listings if len(l.get("tags", [])) < 13]

    if not to_fix:
        return {
            "staged": 0,
            "skipped": 0,
            "total_checked": len(listings),
            "errors": [],
            "message": f"All {len(listings)} active listings already have 13 tags — nothing to fix!",
        }

    # One Claude API call per batch of 40 → structured JSON tag sets.
    try:
        tag_results = await asyncio.wait_for(
            asyncio.to_thread(_generate_tags_for_listings, to_fix),
            timeout=180.0,
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Tag generation returned invalid JSON: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tag generation failed: {exc}")

    listing_map = {l["listing_id"]: l for l in to_fix}
    staged = 0
    skipped = 0
    errors: list[dict] = []

    for res in tag_results:
        lid = res.get("listing_id")
        raw_tags = res.get("tags", [])
        listing = listing_map.get(lid, {})
        title_short = (listing.get("title") or f"Listing {lid}")[:50]

        # Normalise every tag: lowercase, strip specials, cap at 20 chars.
        tags = [_clean_tag(t) for t in raw_tags if str(t).strip()]
        # Deduplicate while preserving order.
        seen: set[str] = set()
        tags = [t for t in tags if t and not (t in seen or seen.add(t))]

        payload = {"listing_id": lid, "tags": tags, "_state_at_staging": listing.get("state")}
        candidate = {"type": "update_tags", "payload": payload}
        ok, msg_str = _validate_staged_action(candidate)
        if not ok:
            errors.append({"listing_id": lid, "title": title_short, "error": msg_str})
            skipped += 1
            continue

        summary = f"Tag fix ({len(tags)}/13): {title_short}"
        db.enqueue_action("update_tags", summary, payload)
        staged += 1

    # Bust cached action list so the Action Center refreshes.
    with _cache_lock:
        _cache.pop("actions", None)

    return {
        "staged": staged,
        "skipped": skipped,
        "total_checked": len(to_fix),
        "errors": errors,
        "message": f"Staged {staged} tag fixes — check the Action Center to approve them.",
    }


@app.get("/api/credentials/status")
async def credentials_status(_token: str = Depends(_auth)):
    """Check which API credentials are configured and live-test the Etsy connection."""
    def _check() -> dict:
        env = os.environ
        status: dict = {
            "etsy": {
                "api_key": bool(env.get("ETSY_API_KEY") or env.get("ETSY_CLIENT_ID")),
                "access_token": bool(env.get("ETSY_ACCESS_TOKEN")),
                "refresh_token": bool(env.get("ETSY_REFRESH_TOKEN")),
            },
            "anthropic": {"api_key": bool(env.get("ANTHROPIC_API_KEY"))},
            "openai":    {"api_key": bool(env.get("OPENAI_API_KEY"))},
            "smtp":      {"user":    bool(env.get("SMTP_USER")), "password": bool(env.get("SMTP_PASSWORD"))},
            "pinterest": {"api_key": bool(env.get("PINTEREST_API_KEY") or env.get("PINTEREST_ACCESS_TOKEN"))},
            "etsy_live": False,
            "etsy_live_error": None,
            "shop_name": "",
        }
        try:
            shop = EtsyAPIClient().get_shop()
            status["etsy_live"] = True
            status["shop_name"] = shop.get("shop_name", "")
        except Exception as exc:
            status["etsy_live_error"] = str(exc)[:120]
        return status

    try:
        data = await asyncio.wait_for(asyncio.to_thread(_check), timeout=12.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy ping timed out")
    return data


# ── Etsy token lineage sync (internal — lets the GitHub Actions daily workflow and
# this server agree on a single source of truth instead of rotating independently) ──
#
# Diagnosed 2026-06-17 (see ops_runbook.md): this server refreshes its Etsy access
# token reactively (on a 401) and the GitHub Actions integrity-check workflow
# refreshes proactively once a day from its OWN copy of ETSY_REFRESH_TOKEN stored as
# a repo secret. Etsy invalidates the previous refresh token on every use, so these
# were two independent rotation lineages with no shared state — whichever side
# refreshed most recently silently invalidated the other's copy, and the next time
# the stale side tried to refresh it got a hard invalid_grant requiring a manual
# tools/etsy_oauth.py re-auth. These two endpoints let either side fetch/post the
# current lineage-true pair through this server's durable /data DB (db.etsy_tokens),
# which already has lineage-aware reconciliation (_reconcile_etsy_tokens). Reuses
# the existing APP_SECRET_TOKEN bearer auth — no new secret to provision.
@app.get("/api/etsy-tokens")
async def get_etsy_tokens_endpoint(_token: str = Depends(_auth)):
    """Current lineage-true Etsy token pair, for the CI workflow to sync against."""
    stored = await asyncio.to_thread(db.get_etsy_tokens)
    if stored:
        return {
            "access_token": stored.get("access_token", ""),
            "refresh_token": stored.get("refresh_token", ""),
            "updated_at": stored.get("updated_at"),
        }
    return {
        "access_token": os.getenv("ETSY_ACCESS_TOKEN", ""),
        "refresh_token": os.getenv("ETSY_REFRESH_TOKEN", ""),
        "updated_at": None,
    }


@app.post("/api/etsy-tokens")
async def post_etsy_tokens_endpoint(payload: dict, _token: str = Depends(_auth)):
    """Accept a freshly-rotated token pair (e.g. from the GitHub Actions workflow)
    and make it the lineage-true pair: persist to the durable DB and adopt it into
    this process's own os.environ immediately, so this server's next Etsy call
    uses the same token CI just minted instead of a now-invalidated one."""
    access_token = (payload or {}).get("access_token", "").strip()
    refresh_token = (payload or {}).get("refresh_token", "").strip()
    if not access_token or not refresh_token:
        raise HTTPException(status_code=400, detail="access_token and refresh_token are required")
    parent = (payload or {}).get("parent_refresh_token") or os.getenv("ETSY_REFRESH_TOKEN", "")
    await asyncio.to_thread(db.save_etsy_tokens, access_token, refresh_token, parent)
    os.environ["ETSY_ACCESS_TOKEN"] = access_token
    os.environ["ETSY_REFRESH_TOKEN"] = refresh_token
    print("[etsy-tokens] adopted rotated token pair posted by CI", flush=True)
    return {"ok": True}


@app.get("/api/account")
async def get_account_endpoint(_token: str = Depends(_auth)):
    """Single-row operator profile for the Settings 'My Account' card."""
    return await asyncio.to_thread(db.get_user_profile)


@app.post("/api/account")
async def post_account_endpoint(payload: dict, _token: str = Depends(_auth)):
    name = ((payload or {}).get("name") or "").strip() or None
    email = ((payload or {}).get("email") or "").strip() or None
    phone = ((payload or {}).get("phone") or "").strip() or None
    tz = ((payload or {}).get("timezone") or "").strip() or None
    return await asyncio.to_thread(db.save_user_profile, name, email, phone, tz)


# ── Local Relay — status, kill switch, Allowed Folders ──────────────────────────


@app.get("/api/relay/status")
async def get_relay_status(_token: str = Depends(_auth)):
    """3-state status for the HUD badge: connected, killed, or offline. Connected
    and killed are independent — a killed relay can still be connected (it just
    refuses every tool_request), and an unkilled relay can be offline."""
    state = await asyncio.to_thread(db.get_relay_state)
    with _relay_lock:
        connected = _relay_ws is not None
    return {
        "connected": connected,
        "killed": bool(state.get("killed")),
        "killed_at": state.get("killed_at"),
        "killed_by": state.get("killed_by"),
        "last_heartbeat": state.get("last_heartbeat"),
    }


async def _agents_status_snapshot() -> dict:
    """The live-status registry for the FRANK HUD's Agents screen + Command
    Center tiles. Every entry maps to a real loop/process — per the plan's
    no-fake-tiles rule, an agent that hasn't been built yet is reported as
    'not_built', never given a fake 'running' status."""
    heartbeats = {h["name"]: h for h in await asyncio.to_thread(db.list_agent_heartbeats)}
    agents = []
    for name, label in _AGENT_LOOP_LABELS.items():
        hb = heartbeats.get(name)
        agents.append({
            "name": name,
            "label": label,
            "built": True,
            "status": hb["status"] if hb else "started",
            "detail": hb["detail"] if hb else "waiting for first run",
            "updated_at": hb["updated_at"] if hb else None,
        })

    relay_state = await asyncio.to_thread(db.get_relay_state)
    with _relay_lock:
        relay_connected = _relay_ws is not None
    if relay_state.get("killed"):
        relay_status, relay_detail = "error", "kill switch engaged"
    elif relay_connected:
        relay_status, relay_detail = "ok", "connected"
    else:
        relay_status, relay_detail = "offline", "no relay connected"
    agents.append({
        "name": "local_relay",
        "label": "Local Relay",
        "built": True,
        "status": relay_status,
        "detail": relay_detail,
        "updated_at": relay_state.get("last_heartbeat"),
    })

    cc_hb = heartbeats.get("context_compactor")
    summaries = await asyncio.to_thread(db.list_chat_summaries)
    agents.append({
        "name": "context_compactor",
        "label": "Context Compactor",
        "built": True,
        "status": cc_hb["status"] if cc_hb else "ok",
        "detail": cc_hb["detail"] if cc_hb else (
            f"{len(summaries)} session(s) compacted; most recent at {summaries[0]['updated_at']}"
            if summaries
            else "Built — no session has crossed the compaction threshold yet"
        ),
        "updated_at": cc_hb["updated_at"] if cc_hb else (summaries[0]["updated_at"] if summaries else None),
    })

    running = sum(1 for a in agents if a["built"] and a["status"] != "error")
    return {"agents": agents, "running_count": running, "total_count": len(agents)}


@app.get("/api/agents/status")
async def get_agents_status(_token: str = Depends(_auth)):
    return await _agents_status_snapshot()


async def _relay_dependency_status() -> dict:
    """Relay health in the dependency-pill vocabulary (closed/open), derived from
    the real connection-state signal (_relay_ws + db.get_relay_state()) -- the
    same data _agents_status_snapshot() already reads correctly. A websocket
    connection has no retry/backoff to drive a CircuitBreaker, so nothing ever
    writes a circuit_breaker_state row for 'relay'; querying that table for it
    (the old behavior) meant relay always reported the default closed/healthy
    row even while genuinely disconnected."""
    relay_state = await asyncio.to_thread(db.get_relay_state)
    with _relay_lock:
        relay_connected = _relay_ws is not None
    if relay_state.get("killed"):
        state = "open"  # kill switch engaged -- treat as a tripped dependency
    elif relay_connected:
        state = "closed"
    else:
        state = "open"  # offline is a real outage, not a healthy default
    return {
        "name": "relay",
        "state": state,
        "consecutive_failures": 0,
        "opened_at": None,
        "updated_at": relay_state.get("last_heartbeat"),
    }


@app.get("/api/system/dependencies")
async def get_system_dependencies(_token: str = Depends(_auth)):
    """Live circuit-breaker status for every tracked external dependency —
    backs the HUD's Dependency Health panel. Replaced the old System Monitor
    CPU/RAM/DISK gauges, which were hardcoded CSS with zero backend. A
    dependency with no DB row yet has never tripped, so it reports the same
    default CircuitBreaker._load() uses: closed, 0 failures."""
    deps = []
    for dep in ("etsy_api", "anthropic_api", "relay"):
        if dep == "relay":
            deps.append(await _relay_dependency_status())
            continue
        cb = await asyncio.to_thread(db.get_circuit_breaker_state, dep)
        deps.append({
            "name": dep,
            "state": cb["state"] if cb else "closed",
            "consecutive_failures": cb["consecutive_failures"] if cb else 0,
            "opened_at": cb["opened_at"] if cb else None,
            "updated_at": cb.get("updated_at") if cb else None,
        })
    return {"dependencies": deps}


@app.get("/api/alerts")
async def get_alerts(_token: str = Depends(_auth)):
    """Aggregates every real alert-worthy condition Frank already tracks into
    one list + count — backs the HUD's notification bell, which was previously
    a decorative badge frozen at '3' with no backend. One endpoint (rather than
    3 client-side fetches) keeps the badge count and dropdown list from ever
    disagreeing, since both read the same response."""
    alerts = []

    for dep in ("etsy_api", "anthropic_api"):
        cb = await asyncio.to_thread(db.get_circuit_breaker_state, dep)
        if cb and cb.get("state") == "open":
            alerts.append({
                "severity": "critical",
                "source": "dependency",
                "title": f"{dep.replace('_', ' ').title()} circuit breaker open",
                "detail": f"{cb.get('consecutive_failures')} consecutive failures, opened at {cb.get('opened_at')}",
            })

    relay = await _relay_dependency_status()
    if relay["state"] == "open":
        relay_state = await asyncio.to_thread(db.get_relay_state)
        detail = "kill switch engaged" if relay_state.get("killed") else "no relay connected"
        alerts.append({
            "severity": "critical",
            "source": "dependency",
            "title": "Relay disconnected" if not relay_state.get("killed") else "Relay kill switch engaged",
            "detail": detail,
        })

    tokens = await asyncio.to_thread(db.get_etsy_tokens)
    if tokens and tokens.get("updated_at"):
        try:
            updated = datetime.fromisoformat(tokens["updated_at"])
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - updated).days
            if age_days >= 90:
                alerts.append({
                    "severity": "critical",
                    "source": "etsy_token",
                    "title": "Etsy refresh token has expired",
                    "detail": f"Last rotated {age_days} days ago (90-day limit) — run python tools/etsy_oauth.py.",
                })
            elif age_days >= 75:
                alerts.append({
                    "severity": "warning",
                    "source": "etsy_token",
                    "title": "Etsy refresh token nearing expiry",
                    "detail": f"Last rotated {age_days} days ago — re-authorize before day 90.",
                })
        except (ValueError, TypeError):
            pass

    heartbeats = await asyncio.to_thread(db.list_agent_heartbeats)
    for h in heartbeats:
        if h.get("status") == "error":
            alerts.append({
                "severity": "warning",
                "source": "agent_heartbeat",
                "title": f"Loop '{h.get('label') or h.get('name')}' is in an error state",
                "detail": h.get("detail") or "",
            })

    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 3))
    return {"alerts": alerts, "count": len(alerts)}


@app.get("/api/tools/list")
async def get_tools_list(_token: str = Depends(_auth)):
    """Live registered AGENT_TOOLS — the Tools & Skills screen's source of
    truth. Badge count is always len(AGENT_TOOLS), so it grows automatically
    as local_* relay tools or new tools are added; never hardcoded."""
    tools = [
        {
            "name": t["name"],
            "description": t.get("description")
            or "Native Anthropic-hosted tool — executed server-side by Anthropic, not by our code.",
        }
        for t in AGENT_TOOLS
    ]
    return {"tools": tools, "count": len(tools)}


@app.get("/api/workflows")
async def get_workflows(_token: str = Depends(_auth)):
    """Runnable backend scripts for the Workflows screen — distinct from
    /api/tools/list (Frank's chat capabilities). Same _EXEC_COMMANDS registry
    execute_command already runs against."""
    workflows = [
        {
            "id": k,
            "name": k.replace("_", " ").title(),
            "description": v["description"],
            "requires_approval": v.get("requires_approval", False),
            "long_running": v.get("long_running", False),
        }
        for k, v in _EXEC_COMMANDS.items()
    ]
    return {"workflows": workflows, "count": len(workflows)}


@app.post("/api/workflows/{workflow_id}/run")
async def post_workflow_run(workflow_id: str, body: dict | None = None, _token: str = Depends(_auth)):
    """Run a workflow. Commands without requires_approval run immediately;
    backup_digital_products (the one command with requires_approval) stages
    through the same action_queue Action Center uses."""
    if workflow_id not in _EXEC_COMMANDS:
        raise HTTPException(status_code=404, detail=f"unknown workflow: {workflow_id}")
    cfg = _EXEC_COMMANDS[workflow_id]
    extra_args = ((body or {}).get("extra_args") or "").strip()
    if extra_args:
        bad = [p for p in extra_args.split() if any(f in p.lower() for f in _FORBIDDEN_EXEC_FLAGS)]
        if bad:
            raise HTTPException(status_code=400, detail=f"extra_args {bad} not allowed")
    if cfg.get("requires_approval"):
        payload = {"command": workflow_id, "extra_args": extra_args}
        summary = f"Run {workflow_id.replace('_', ' ')}" + (f" {extra_args}" if extra_args else "")
        aid = await asyncio.to_thread(db.enqueue_action, "run_script", summary, payload)
        return {"staged": True, "action_id": aid, "status": "pending"}
    result = await asyncio.to_thread(_run_exec_command, workflow_id, extra_args)
    return {"staged": False, **result}


@app.post("/api/relay/kill")
async def post_relay_kill(_token: str = Depends(_auth)):
    """Engage the kill switch. Blocks everything — including read-only
    local_read_file/local_list_dir — until /api/relay/resume is called.
    relay_state.killed is the source of truth (survives a server restart)."""
    await asyncio.to_thread(db.set_kill_switch, True, "scott")
    await asyncio.to_thread(db.log_activity, "scott", "kill_switch", "kill switch engaged", None, "ok")
    with _relay_lock:
        ws = _relay_ws
    if ws is not None:
        try:
            await ws.send_text(json.dumps({"type": "kill_switch", "active": True}))
        except Exception:
            pass
    return {"killed": True}


@app.post("/api/relay/resume")
async def post_relay_resume(_token: str = Depends(_auth)):
    await asyncio.to_thread(db.set_kill_switch, False, "scott")
    await asyncio.to_thread(db.log_activity, "scott", "kill_switch", "kill switch released", None, "ok")
    with _relay_lock:
        ws = _relay_ws
    if ws is not None:
        try:
            await ws.send_text(json.dumps({"type": "kill_switch", "active": False}))
        except Exception:
            pass
    return {"killed": False}


@app.get("/api/relay/allowed-folders")
async def get_allowed_folders(_token: str = Depends(_auth)):
    """The relay polls this (or refreshes periodically) so folder changes take
    effect without restarting the relay process."""
    folders = await asyncio.to_thread(db.list_allowed_folders)
    return {"folders": folders}


@app.post("/api/relay/allowed-folders")
async def post_allowed_folder(payload: dict, _token: str = Depends(_auth)):
    path = (payload or {}).get("path", "").strip()
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    folder_id = await asyncio.to_thread(db.add_allowed_folder, path, "scott")
    await asyncio.to_thread(db.log_activity, "scott", "allowed_folder_add", path, None, "ok")
    return {"ok": True, "id": folder_id}


@app.delete("/api/relay/allowed-folders/{folder_id}")
async def delete_allowed_folder(folder_id: int, _token: str = Depends(_auth)):
    from tools.trash import archive_snippet
    folders = await asyncio.to_thread(db.list_allowed_folders)
    row = next((f for f in folders if f["id"] == folder_id), None)
    if row:
        await asyncio.to_thread(
            archive_snippet, "db:allowed_folders", json.dumps(row, default=str),
            f"allowed folder removed via dashboard (id={folder_id})",
        )
    ok = await asyncio.to_thread(db.remove_allowed_folder, folder_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Folder not found")
    await asyncio.to_thread(db.log_activity, "scott", "allowed_folder_remove", str(folder_id), None, "ok")
    return {"ok": True}


@app.post("/api/relay/upload")
async def upload_to_relay(request: Request, path: str, _token: str = Depends(_auth)):
    """Push a raw binary file straight into the relay's workspace over the existing
    /ws/relay websocket — base64-encoded, since the relay protocol is JSON-only.

    Direct human-initiated dashboard action only, never an LLM tool call — local_write_binary_file
    is intentionally not in _LOCAL_STAGED_TOOLS, so it skips the Action Center approval gate.
    Body is the raw bytes (Content-Type application/octet-stream), path is a query param."""
    path = (path or "").strip()
    if not path:
        raise HTTPException(status_code=400, detail="path query param is required")
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="empty body")
    if len(body) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {_human_size(_MAX_UPLOAD_BYTES)} limit")
    content_b64 = base64.b64encode(body).decode("ascii")
    result = await _dispatch_to_relay(
        "local_write_binary_file", {"path": path, "content_b64": content_b64}, timeout=90.0,
    )
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    await asyncio.to_thread(db.log_activity, "scott", "relay_upload", path, None, "ok")
    return {"ok": True, "path": result.get("path"), "bytes_written": result.get("bytes_written")}


# ── Shared to-do list (Scott + Frank, always visible on the dashboard) ──────────────


@app.get("/api/todos")
async def get_todos(_token: str = Depends(_auth)):
    items = await asyncio.to_thread(db.list_todos)
    return {"todos": items, "open_count": sum(1 for t in items if not t["done"])}


@app.post("/api/todos")
async def post_todo(payload: dict, _token: str = Depends(_auth)):
    text = (payload or {}).get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    added_by = (payload or {}).get("added_by", "scott").strip().lower()
    if added_by not in ("scott", "frank"):
        added_by = "scott"
    due_date = (payload or {}).get("due_date") or None
    todo_id = await asyncio.to_thread(db.add_todo, text, added_by, due_date)
    return {"ok": True, "id": todo_id}


@app.post("/api/todos/{todo_id}/toggle")
async def toggle_todo(todo_id: int, payload: dict, _token: str = Depends(_auth)):
    done = bool((payload or {}).get("done", True))
    ok = await asyncio.to_thread(db.set_todo_done, todo_id, done)
    if not ok:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"ok": True}


@app.delete("/api/todos/{todo_id}")
async def remove_todo(todo_id: int, _token: str = Depends(_auth)):
    from tools.trash import archive_snippet
    todos = await asyncio.to_thread(db.list_todos)
    row = next((t for t in todos if t["id"] == todo_id), None)
    if row:
        await asyncio.to_thread(
            archive_snippet, "db:todos", json.dumps(row, default=str),
            f"todo deleted via dashboard (id={todo_id})",
        )
    ok = await asyncio.to_thread(db.delete_todo, todo_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"ok": True}


# ── Calendar — due-dated todos + recurring ops cadence + seasonal/tax calendar ──────

_CADENCE_CHECKLISTS = {
    "weekly": [
        "Check Etsy Search Visibility Dashboard — fix any flagged listings immediately",
        "Review 7-day conversion rate per listing (Etsy Analytics → Listings)",
        "Respond to any outstanding messages or reviews",
        "Check 3D print queue — what sold, what needs restocking",
    ],
    "monthly": [
        "Run `python tools/shop_health_check.py` — full snapshot",
        "Compare conversion rates, views, revenue vs. prior month",
        "Identify listings with high views but low conversion (photo or price problem)",
        "Update seasonal keywords in top 10 listings (update 6 weeks before peak season)",
        "Export orders for COGS/Craftybase reconciliation",
    ],
    "quarterly": [
        "Estimated tax payment (see tax_deadlines below for exact dates)",
        "New product launch or existing product upgrade decision",
        "Review competitor pricing in top 3 niches",
        "S-Corp salary draw if applicable",
    ],
}


@app.get("/api/cadence")
async def get_cadence(_token: str = Depends(_auth)):
    today = date.today()

    calendar = seasonal_keywords._build_calendar(today.year)
    for e in calendar:
        if e["update_by"] is None:
            e["update_by"] = seasonal_keywords._update_by(e["peak"])
    seasonal = [
        {
            "season": e["season"],
            "priority": e["priority"],
            "peak": e["peak"].isoformat(),
            "update_by": e["update_by"].isoformat(),
            "urgency": seasonal_keywords._urgency(e["update_by"], today),
            "listings_to_update": e["listings_to_update"],
        }
        for e in calendar
        if e["peak"] >= today or (e["update_by"] < today < e["peak"])
    ]
    seasonal.sort(key=lambda e: e["update_by"])

    tax = json.loads(tax_compliance_tools._get_tax_calendar())["tax_deadlines"]
    for t in tax:
        d = datetime.strptime(t["date"], "%b %d, %Y").date()
        t["date_iso"] = d.isoformat()
        t["urgency"] = seasonal_keywords._urgency(d, today)
    tax.sort(key=lambda t: t["date_iso"])

    todos = await asyncio.to_thread(db.list_todos)
    due_todos = sorted(
        (t for t in todos if t.get("due_date") and not t["done"]),
        key=lambda t: t["due_date"],
    )

    return {
        "seasonal": seasonal,
        "tax_deadlines": tax,
        "due_todos": due_todos,
        "checklists": _CADENCE_CHECKLISTS,
    }


# ── Conversations — read-only browser/search for persisted chat_messages history ──


@app.get("/api/conversations")
async def get_conversations(q: str = "", _token: str = Depends(_auth)):
    """Session list (most-recently-active first), or — when `q` is supplied —
    a cross-session substring search instead."""
    if q.strip():
        results = await asyncio.to_thread(db.search_chat_messages, q.strip())
        return {"query": q.strip(), "results": results}
    sessions = await asyncio.to_thread(db.list_chat_sessions)
    return {"sessions": sessions}


@app.get("/api/conversations/{session_id}")
async def get_conversation_detail(session_id: str, _token: str = Depends(_auth)):
    """Full message history for one session."""
    data = await asyncio.to_thread(db.get_chat_session, session_id)
    if not data["messages"]:
        raise HTTPException(status_code=404, detail="No messages for this session")
    return data


# ── File hub (browse/download product files + backups straight from the dashboard) ─

_FILE_ROOTS = {
    "products": ROOT / "data" / "digital_products",
    "backups": ROOT / "data" / "backups",
}

# On the hosted dashboard (Railway) the repo's data/ dir is ephemeral and gitignored,
# so files generated on Scott's machine never appear here. The /data Volume IS durable
# across redeploys — if a "files" folder is placed there it survives, so we scan it too.
# This is the realistic path to "every digital file should be openable from the phone":
# drop them into the persistent volume once (tools/sync_files_to_hub.py) and they stay
# browsable. HUB_FILES_DIR overrides the location (handy if the Volume mounts elsewhere,
# and lets this be tested locally). No-op locally when neither is present.
_vol_override = os.getenv("HUB_FILES_DIR", "").strip()
if _vol_override:
    _FILE_ROOTS["volume"] = Path(_vol_override)
elif Path("/data").is_dir():
    _FILE_ROOTS["volume"] = Path("/data") / "files"

# Staged listing photos awaiting Scott's approve/reject in the Action Center —
# durable under the Railway volume when mounted (survives redeploys, same reason
# "volume" exists above), else a local data/ dir for dev.
_FILE_ROOTS["staged_photos"] = (
    (_FILE_ROOTS["volume"] / "staged_photos") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "staged_photos")
)

# Studio tab — generated videos (video_generator.py's own OUTPUT_DIR), source images
# a user uploads before generation, and videos staged for Etsy/Instagram/Facebook
# review. Not placed under the durable volume: these are regeneratable working
# files, not source-of-truth product assets.
_FILE_ROOTS["videos"] = ROOT / "data" / "social" / "videos"
_FILE_ROOTS["studio_uploads"] = ROOT / "data" / "social" / "studio_uploads"
_FILE_ROOTS["staged_videos"] = ROOT / "data" / "social" / "staged_videos"


def _human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


# Extensions a phone browser can open inline (preview) instead of force-downloading.
# Everything else is served as a download. This is what lets a buyer-facing PDF or a
# sticker PNG open straight in the phone without a download+unzip dance.
_INLINE_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".txt", ".md", ".json", ".csv", ".mp4"}


def _media_type_for(name: str) -> str:
    guessed, _ = mimetypes.guess_type(name)
    return guessed or "application/octet-stream"


def _zip_entries(zip_path: Path) -> list[dict]:
    """List the openable (non-directory, non-empty) entries inside a ZIP."""
    out: list[dict] = []
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = info.filename
                if name.endswith("/") or name.startswith("__MACOSX/"):
                    continue
                ext = os.path.splitext(name)[1].lower()
                out.append(
                    {
                        "name": name,
                        "size": info.file_size,
                        "size_human": _human_size(info.file_size),
                        "inline": ext in _INLINE_EXTS,
                    }
                )
    except (zipfile.BadZipFile, OSError):
        return []
    out.sort(key=lambda e: e["name"])
    return out


@app.get("/api/files")
async def list_files(_token: str = Depends(_auth)):
    """List every file under data/digital_products/ and data/backups/ so Scott can
    see, open, and download product source files straight from the dashboard —
    these directories are gitignored (machine-local) and have no other UI.

    For each ZIP we also expand its contents so individual files (PDFs, sticker
    PNGs, SVGs) can be opened directly on a phone WITHOUT downloading and
    unzipping first (Scott's request, 2026-06-17)."""
    groups = []
    for root_key, root_path in _FILE_ROOTS.items():
        if not root_path.exists():
            continue
        files = []
        for p in sorted(root_path.rglob("*")):
            if not p.is_file():
                continue
            stat = p.stat()
            rel = str(p.relative_to(root_path))
            ext = p.suffix.lower()
            entry = {
                "path": rel,
                "root": root_key,
                "size": stat.st_size,
                "size_human": _human_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "inline": ext in _INLINE_EXTS,
                "is_zip": ext == ".zip",
            }
            if ext == ".zip":
                entry["entries"] = _zip_entries(p)
            files.append(entry)
        files.sort(key=lambda f: f["modified"], reverse=True)
        _labels = {
            "backups": "Backups", "volume": "Saved Files (persistent)", "products": "Product Files",
            "staged_photos": "Staged Photos (pending approval)",
            "videos": "Generated Videos", "studio_uploads": "Studio Uploads",
            "staged_videos": "Staged Videos (pending approval)",
        }
        groups.append({"root": root_key, "label": _labels.get(root_key, "Product Files"), "files": files})
    # Honest empty-state hint: on Railway these dirs are ephemeral + gitignored, so
    # nothing shows unless the files were produced/backed up on this same machine.
    has_any = any(g["files"] for g in groups)
    return {
        "groups": groups,
        "empty_reason": (
            None if has_any else
            "No product files are present on this server. data/digital_products/ and "
            "data/backups/ are machine-local (gitignored) and do not survive a redeploy "
            "on the hosted dashboard. Generate or restore them on the machine running "
            "this server, or run tools/backup_digital_products.py there, to see them here."
        ),
    }


def _resolve_in_root(root: str, path: str) -> Path:
    base = _FILE_ROOTS.get(root)
    if base is None:
        raise HTTPException(status_code=404, detail="Unknown root")
    base = base.resolve()
    target = (base / path).resolve()
    if base not in target.parents and target != base:
        raise HTTPException(status_code=400, detail="Invalid path")
    return target


@app.get("/api/files/download")
async def download_file(root: str, path: str, token: str = "", inline: int = 0):
    """Stream a file from one of the allowed roots. Auth via ?token= (query param,
    not header) so this URL works as a plain browser/PWA link.

    inline=1 serves with the real media type and an inline disposition so the phone
    browser previews it (PDF viewer, image) instead of downloading."""
    if token != APP_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    target = _resolve_in_root(root, path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if inline:
        return FileResponse(
            target,
            media_type=_media_type_for(target.name),
            headers={"Content-Disposition": f'inline; filename="{target.name}"'},
        )
    return FileResponse(target, filename=target.name, media_type="application/octet-stream")


# Upload cap — these are digital product deliverables (Etsy's own per-file limit is
# 20MB), so 30MB is a generous ceiling that still rejects accidental giant files.
_MAX_UPLOAD_BYTES = 30 * 1024 * 1024


@app.post("/api/files/upload")
async def upload_to_volume(request: Request, path: str, _token: str = Depends(_auth)):
    """Accept a raw file body and store it under the durable /data/files volume at the
    given relative path. This is how product files get onto the hosted dashboard so they
    show up (and open without unzip) in the phone Files area — tools/sync_files_to_hub.py
    walks the local data/digital_products/ and POSTs each file here.

    Body is the raw bytes (Content-Type application/octet-stream), path is a query param.
    Writes only inside the volume; path traversal is rejected."""
    vol_root = _FILE_ROOTS.get("volume")
    if vol_root is None:
        raise HTTPException(
            status_code=503,
            detail="No persistent /data volume on this server — uploads can't be stored durably. "
                   "Attach a Railway Volume mounted at /data.",
        )
    rel = (path or "").strip().lstrip("/")
    if not rel:
        raise HTTPException(status_code=400, detail="path query param is required")
    vroot = vol_root.resolve()
    target = (vroot / rel).resolve()
    if vroot not in target.parents and target != vroot:
        raise HTTPException(status_code=400, detail="Invalid path")
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="empty body")
    if len(body) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {_human_size(_MAX_UPLOAD_BYTES)} limit")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return {"ok": True, "path": rel, "size": len(body), "size_human": _human_size(len(body))}


@app.get("/api/files/zip-entry")
async def open_zip_entry(root: str, path: str, entry: str, token: str = "", inline: int = 1):
    """Stream a single file OUT of a ZIP without the user unzipping anything.

    This is the core of Scott's 'open without unzip on a phone' request: tap a
    file inside a sticker pack / print-size ZIP and it opens directly. Default
    inline=1 so PDFs/PNGs preview in the phone browser."""
    if token != APP_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    target = _resolve_in_root(root, path)
    if not target.is_file() or target.suffix.lower() != ".zip":
        raise HTTPException(status_code=404, detail="ZIP not found")
    try:
        with zipfile.ZipFile(target) as zf:
            try:
                data = zf.read(entry)
            except KeyError:
                raise HTTPException(status_code=404, detail="Entry not found in ZIP")
    except zipfile.BadZipFile:
        raise HTTPException(status_code=422, detail="File is not a valid ZIP")
    name = os.path.basename(entry) or "file"
    disposition = "inline" if inline else "attachment"
    return Response(
        content=data,
        media_type=_media_type_for(name),
        headers={"Content-Disposition": f'{disposition}; filename="{name}"'},
    )


@app.post("/api/ws-ticket")
async def post_ws_ticket(_token: str = Depends(_auth)):
    """Mint a short-lived, single-use ticket for the /ws/chat handshake. Browser/RN
    WebSocket clients can't send a Bearer header on connect, so this lets them prove
    they hold the real APP_TOKEN (via this normal authenticated REST call) without
    putting that long-lived secret in the WS URL itself."""
    return {"ticket": _new_ws_ticket(), "ttl": _WS_TICKET_TTL}


# ── WebSocket relay (Frank's local hands/ears process connects here) ───────────


@app.websocket("/ws/relay")
async def relay_ws(websocket: WebSocket):
    """The local relay process (tools/relay/frank_relay.py, running on Scott's own
    machine) connects here. This is a pure RPC executor for local_* tool calls —
    it owns no conversation, unlike /ws/chat. Auth via the Authorization header
    (the relay is a plain Python `websockets` client, so unlike a browser it can
    actually set one — no need for the URL-query workaround /ws/chat requires)."""
    global _relay_ws
    auth_header = websocket.headers.get("authorization", "")
    token = auth_header[7:] if auth_header.lower().startswith("bearer ") else ""
    if token != APP_TOKEN:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    with _relay_lock:
        _relay_ws = websocket
    await asyncio.to_thread(db.log_activity, "relay", "connect", "relay connected", None, "ok")

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            mtype = msg.get("type")

            if mtype == "tool_result":
                req_id = msg.get("id")
                fut = _relay_pending.get(req_id)
                if fut and not fut.done():
                    if msg.get("ok"):
                        fut.set_result(msg.get("result") or {})
                    else:
                        fut.set_result({"error": msg.get("error") or "relay reported failure"})

            elif mtype == "heartbeat":
                await asyncio.to_thread(db.set_relay_heartbeat, msg.get("cpu"), msg.get("ram_pct"))

            # "kill_switch" is server → relay only; nothing to receive for it here.
    except WebSocketDisconnect:
        pass
    finally:
        with _relay_lock:
            if _relay_ws is websocket:
                _relay_ws = None
        await asyncio.to_thread(db.log_activity, "relay", "disconnect", "relay disconnected", None, "ok")


# ── WebSocket chat ─────────────────────────────────────────────────────────────


async def _run_agent_turn(websocket: WebSocket, ai_client, history: list[dict]) -> str:
    """One user turn: stream text, run any tools the model requests, repeat until
    the model is done. Tool calls let the CEO agent read live shop data.

    The Anthropic SDK's stream is a *blocking* iterator — reading it directly inside
    this coroutine would tie up the whole shared asyncio event loop (every other
    concurrent /ws/chat session, every background loop) for as long as a chunk takes
    to arrive over the network. So the blocking read runs in a worker thread; chunks
    cross back into the event loop via call_soon_threadsafe onto an asyncio.Queue,
    bounded by a 90s per-chunk stall timeout so a frozen connection can't hang the
    shared loop forever.

    Returns the assistant's full visible text for the turn (so the caller can
    persist it to chat memory). Raises on a stream/API failure or stall — the caller
    is responsible for rolling back this turn's additions to `history`."""
    assistant_text_parts: list[str] = []
    loop = asyncio.get_running_loop()
    for _ in range(6):  # safety cap on tool round-trips per turn
        queue: asyncio.Queue = asyncio.Queue()

        def _produce() -> None:
            # Doesn't go through _anthropic_create() (that helper wraps a single
            # messages.create() call; this is a stream() context manager iterated
            # chunk-by-chunk) but still gates/records on the same shared breaker so
            # this highest-volume Anthropic call site -- every chat turn -- actually
            # shows up in /api/system/dependencies during a real outage instead of
            # only the lower-volume background call sites.
            if not _anthropic_breaker.allow_request():
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    (
                        "error",
                        CircuitBreakerOpenError(
                            "circuit breaker 'anthropic_api' is open -- skipping call until cooldown elapses"
                        ),
                    ),
                )
                return
            try:
                with ai_client.messages.stream(
                    model="claude-sonnet-4-6",
                    max_tokens=1500,
                    system=[
                        _CACHED_SYSTEM_BLOCK,
                        {"type": "text", "text": _ops_runbook_block() + _ceo_learnings_block()},
                    ],
                    tools=_tools_with_cache(),
                    messages=history,
                ) as stream:
                    for chunk in stream.text_stream:
                        loop.call_soon_threadsafe(queue.put_nowait, ("chunk", chunk))
                    final_msg = stream.get_final_message()
            except (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.InternalServerError) as exc:
                _anthropic_breaker.record_failure()
                loop.call_soon_threadsafe(queue.put_nowait, ("error", exc))
            except Exception as exc:  # surfaced to the consumer below, never swallowed
                loop.call_soon_threadsafe(queue.put_nowait, ("error", exc))
            else:
                _anthropic_breaker.record_success()
                loop.call_soon_threadsafe(queue.put_nowait, ("done", final_msg))

        producer = asyncio.create_task(asyncio.to_thread(_produce))
        final = None
        try:
            while final is None:
                kind, payload = await asyncio.wait_for(queue.get(), timeout=90)
                if kind == "chunk":
                    assistant_text_parts.append(payload)
                    try:
                        await websocket.send_text(json.dumps({"type": "chunk", "content": payload}))
                    except Exception:
                        pass  # best-effort; a flaky send shouldn't abort an otherwise-good stream
                elif kind == "done":
                    final = payload
                elif kind == "error":
                    raise payload
        except asyncio.TimeoutError:
            producer.cancel()  # can't kill the underlying thread, but stop awaiting it
            raise TimeoutError(f"{business_config.AGENT_NAME_SHORT}'s reply stalled (no response for 90s)") from None

        # Record the assistant turn (text + any tool_use blocks) verbatim.
        history.append({"role": "assistant", "content": final.content})

        if final.stop_reason != "tool_use":
            await websocket.send_text(json.dumps({"type": "done"}))
            return "".join(assistant_text_parts).strip()

        # Execute every requested tool, then feed results back for the next round.
        # IMPORTANT: every tool_use block above is now committed to `history`. The
        # Anthropic API requires a matching tool_result for each one in the very next
        # message — if anything below raises (e.g. a flaky websocket send on a mobile
        # connection) before we append `tool_results`, every later turn in this
        # session 400s forever ("tool_use ids were found without tool_result blocks").
        # So nothing here is allowed to propagate without first recording a result.
        tool_results = []
        for block in final.content:
            if getattr(block, "type", None) == "tool_use":
                if block.name == "local_speak":
                    speak_txt = (block.input or {}).get("text", "")
                    try:
                        await websocket.send_text(json.dumps({"type": "speak", "text": speak_txt}))
                    except Exception:
                        pass  # best-effort; never block the tool result
                    status_msg = "🔊 Speaking…"
                elif block.name == "execute_command":
                    cmd = (block.input or {}).get("command", "command")
                    status_msg = f"⚙ Running {cmd}…"
                elif block.name == "stage_action":
                    status_msg = "📋 Staging action for approval…"
                elif block.name == "browse_web":
                    url = (block.input or {}).get("url", "")
                    status_msg = f"🌐 Browsing {url[:60]}…"
                elif block.name == "search_etsy":
                    q = (block.input or {}).get("query", "")
                    status_msg = f"🔍 Searching Etsy: {q[:40]}…"
                elif block.name == "check_listing_quality":
                    status_msg = "🔍 Running listing QC checklist…"
                elif block.name in _RELAY_TOOLS:
                    status_msg = f"💻 Asking the relay to run {block.name}…"
                elif block.name in _LOCAL_STAGED_TOOLS:
                    status_msg = f"📋 Staging {block.name} for approval…"
                else:
                    status_msg = f"📊 Reading {block.name}…"
                try:
                    await websocket.send_text(json.dumps({"type": "tool", "content": status_msg}))
                except Exception:
                    pass  # status update is best-effort; never let it block the tool result
                try:
                    if block.name in _RELAY_TOOLS:
                        result = await _dispatch_to_relay(block.name, block.input)
                    elif block.name in _LOCAL_STAGED_TOOLS:
                        result = await _stage_local_action(block.name, block.input)
                    else:
                        result = await asyncio.to_thread(_execute_agent_tool, block.name, block.input)
                except Exception as exc:
                    result = {"error": str(exc)}
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    }
                )
        history.append({"role": "user", "content": tool_results})

    # Exhausted the round-trip cap — close out gracefully.
    await websocket.send_text(json.dumps({"type": "done"}))
    return "".join(assistant_text_parts).strip()


# ── Voice: OpenAI Whisper (speech-in) + OpenAI TTS (speech-out) ────────────────
# REST, not an extension of /ws/chat's JSON-text protocol — audio is binary and
# both operations are one-shot request/response, so the existing Bearer-auth REST
# pattern (same _auth dependency every other /api/* route uses) is simpler and
# lower-risk than adding binary framing to the chat socket.

_VOICE_CONTENT_TYPE_EXT = {
    "audio/webm": "webm",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
}


@app.post("/api/voice/transcribe")
async def transcribe_voice(request: Request, _token: str = Depends(_auth)):
    """Accepts a raw audio blob (Content-Type set by the client, e.g. audio/webm from
    the browser's MediaRecorder, or audio/m4a from the native app) and returns its
    transcript via OpenAI Whisper. Mirrors the raw-bytes body pattern already used by
    /api/files/upload — no multipart parsing needed for a single blob."""
    if not OPENAI_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="empty audio body")
    if len(body) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"audio exceeds {_human_size(_MAX_UPLOAD_BYTES)} limit")
    content_type = request.headers.get("content-type", "audio/webm").split(";")[0].strip()
    ext = _VOICE_CONTENT_TYPE_EXT.get(content_type, "webm")

    def _do_transcribe() -> str:
        client = openai.OpenAI(api_key=OPENAI_KEY)
        buf = io.BytesIO(body)
        buf.name = f"audio.{ext}"
        result = client.audio.transcriptions.create(model="whisper-1", file=buf)
        return result.text

    try:
        text = await asyncio.to_thread(_do_transcribe)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"transcription failed: {str(exc)[:200]}")
    return {"text": text}


@app.post("/api/voice/speak")
async def speak_text(payload: dict, _token: str = Depends(_auth)):
    """Accepts {"text": "..."} and returns MP3 audio bytes from OpenAI TTS — returned
    as a direct audio/mpeg response body (not base64/JSON) so the client can feed it
    straight into an <audio> element (web) or a Sound object (native)."""
    if not OPENAI_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    text = text[:4000]  # OpenAI TTS input cap safeguard

    def _do_speak() -> bytes:
        client = openai.OpenAI(api_key=OPENAI_KEY)
        resp = client.audio.speech.create(model="tts-1", voice="onyx", input=text)
        return resp.read()

    try:
        audio_bytes = await asyncio.to_thread(_do_speak)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"speech synthesis failed: {str(exc)[:200]}")
    return Response(content=audio_bytes, media_type="audio/mpeg")


_CONTEXT_COMPACT_TAIL_THRESHOLD = 60  # messages since last compaction before another pass runs
_CONTEXT_COMPACT_KEEP_RECENT = 30  # messages left untouched as the live replay tail


def _maybe_compact_chat_history(session_id: str) -> None:
    """The context_compactor agent: once a session's not-yet-summarized tail grows
    past _CONTEXT_COMPACT_TAIL_THRESHOLD messages, fold everything except the most
    recent _CONTEXT_COMPACT_KEEP_RECENT into one condensed summary via a cheap Haiku
    call (same pattern as _summarize_and_rotate_kb_file), so a long-running session
    keeps a real memory of earlier turns instead of load_chat_history's hard `limit`
    cutoff silently dropping them on reconnect. Best-effort: never raises, since a
    failed compaction just means the next pass tries again with a longer tail."""
    if not session_id or not ANTHROPIC_KEY:
        return
    try:
        existing = db.get_chat_summary(session_id)
        through_id = existing["through_id"] if existing else 0
        tail = db.load_chat_messages_since(session_id, after_id=through_id, limit=2000)
        if len(tail) <= _CONTEXT_COMPACT_TAIL_THRESHOLD:
            return
        # Walk the naive cut point back to the nearest boundary right after an
        # 'assistant' message, so the kept tail always resumes on a 'user' turn —
        # required for valid role alternation when the synthetic summary pair
        # (user, assistant) is spliced in ahead of it on the next reconnect.
        idx = len(tail) - _CONTEXT_COMPACT_KEEP_RECENT
        while idx > 0 and tail[idx - 1]["role"] != "assistant":
            idx -= 1
        if idx <= 0:
            return  # no safe pair boundary yet; try again once the tail grows more
        to_summarize = tail[:idx]
        new_through_id = to_summarize[-1]["id"]

        transcript = "\n\n".join(f"{m['role'].upper()}: {m['content']}" for m in to_summarize)
        prior_summary = existing["summary"] if existing else ""
        prompt = (
            f"Condense this chat transcript between {business_config.OWNER_NAME} (an Etsy shop owner) "
            f"and {business_config.AGENT_NAME_SHORT} (his "
            "CEO agent) into a single summary (~1500 characters) that preserves every concrete "
            "decision, number, and open question — not a vibe-based recap. Plain prose or short "
            "bullets, oldest-to-newest. No preamble, no meta-commentary."
        )
        if prior_summary:
            prompt += (
                "\n\nFold in this existing summary of everything before this transcript, "
                f"keeping the combined result around the same length:\n\n{prior_summary}"
            )
        prompt += f"\n\nTranscript:\n\n{transcript}"

        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = _anthropic_create(
            client,
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        new_summary = msg.content[0].text.strip()
        if not new_summary:
            return
        db.set_chat_summary(session_id, new_summary, new_through_id)
        print(
            f"[context-compactor] session {session_id}: folded {len(to_summarize)} messages "
            f"into a {len(new_summary)}-char summary through id {new_through_id}",
            flush=True,
        )
        db.set_agent_heartbeat(
            "context_compactor", "Context Compactor", "ok",
            f"folded {len(to_summarize)} messages into a {len(new_summary)}-char summary",
        )
    except Exception as exc:
        print(f"[context-compactor] compaction failed for session {session_id}: {exc}", flush=True)
        db.set_agent_heartbeat("context_compactor", "Context Compactor", "error", str(exc)[:300])


@app.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket):
    """Streaming CEO agent chat with live-data tools. Auth via a short-lived, single-use
    ?ticket= minted by POST /api/ws-ticket (browser/RN WebSocket clients can't set a
    Bearer header on the handshake, so the long-lived APP_TOKEN never goes in the URL).

    `?session=<id>` ties the connection to a persisted conversation. On connect
    the prior thread is loaded from SQLite, so Frank keeps full context across
    mobile socket drops and Railway restarts instead of starting amnesiac every
    time the WebSocket reconnects. A {"type":"ping"} from the client is answered
    with a pong to keep the socket warm through carrier/proxy idle timeouts."""
    ticket = websocket.query_params.get("ticket", "")
    if not ticket or not _consume_ws_ticket(ticket):
        await websocket.close(code=4001)
        return

    await websocket.accept()

    session_id = (websocket.query_params.get("session", "") or "").strip()[:64]

    ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    # Replay persisted text history so Frank resumes mid-thread after a reconnect.
    # If the context_compactor has already condensed everything before some point,
    # splice that summary in ahead of the still-live tail instead of using the raw
    # load_chat_history() window, which would just hard-cut anything older.
    history: list[dict] = []
    if session_id:
        summary = await asyncio.to_thread(db.get_chat_summary, session_id)
        if summary:
            tail = await asyncio.to_thread(db.load_chat_messages_since, session_id, summary["through_id"])
            history = [
                {
                    "role": "user",
                    "content": "[Context compactor — condensed summary of this conversation before this point:]\n"
                    + summary["summary"],
                },
                {"role": "assistant", "content": "Got it, I have the context from earlier in this conversation."},
            ] + [{"role": m["role"], "content": m["content"]} for m in tail]
        else:
            history = await asyncio.to_thread(db.load_chat_history, session_id)
    if history:
        await websocket.send_text(json.dumps({"type": "history", "messages": history}))

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            user_text = msg.get("message", "").strip()
            if not user_text:
                continue

            # Snapshot length so a mid-turn failure can be rolled back cleanly.
            # Without this, a dangling user message (no assistant reply) leaves
            # the next turn sending two user turns back-to-back, which the API
            # rejects — wedging the chat until a full reload.
            base_len = len(history)
            history.append({"role": "user", "content": user_text})
            try:
                assistant_text = await _run_agent_turn(websocket, ai_client, history)
            except Exception as exc:
                print(f"[chat] turn failed: {exc}", flush=True)
                del history[base_len:]  # roll back this turn's additions
                await websocket.send_text(json.dumps({"type": "error", "content": _friendly_error_message(exc)}))
                continue

            # Persist only completed exchanges (text-only — see db.append_chat_message).
            if session_id:
                await asyncio.to_thread(db.append_chat_message, session_id, "user", user_text)
                if assistant_text:
                    await asyncio.to_thread(db.append_chat_message, session_id, "assistant", assistant_text)
                await asyncio.to_thread(_maybe_compact_chat_history, session_id)

    except WebSocketDisconnect:
        pass


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
