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
import inspect
import io
import json
import mimetypes
import os
import random
import re as _re
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import uuid
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

if getattr(sys, "frozen", False):
    # PyInstaller desktop-app bundle (tools/desktop/backend.spec, 2026-07-08): the
    # frozen entry script's own __file__ no longer sits 3 directories under the repo
    # root (tools/api_server/main.py) the way it does when run from source. sys._MEIPASS
    # is PyInstaller's own documented attribute for "where the bundled data actually
    # is" -- NOT Path(sys.executable).parent, which in onedir mode (PyInstaller 6.x)
    # is one level too shallow: the executable sits in dist/frank-backend/, but the
    # bundled tools/ tree this spec collects via `datas` lands in
    # dist/frank-backend/_internal/tools/ (verified empirically -- a static-asset
    # 404 was the first sign sys.executable's parent was wrong).
    ROOT = Path(sys._MEIPASS).resolve()  # noqa: SLF001 -- documented PyInstaller API
else:
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


# Known-good fallback brain. If MODEL_PRIMARY (currently claude-sonnet-5) isn't
# available to this deploy's Anthropic account, _anthropic_create() drops to this
# once — so promoting the primary model can never hard-break Frank; it just logs
# and degrades gracefully. Keep this pointed at a model every account can reach.
_MODEL_FALLBACK = "claude-sonnet-4-6"


def _log_anthropic_usage(caller: str, model: str, usage) -> None:
    """Records every Anthropic call's token usage to activity_log -- confirmed
    2026-07-10 that nothing in this codebase logged this before now, which is
    why "what used the Anthropic money" couldn't be answered from Frank's own
    data (see ops_runbook.md). `usage` is the SDK's Usage object (input_tokens/
    output_tokens/cache_creation_input_tokens/cache_read_input_tokens); getattr
    defaults everything to 0 rather than raising, since usage can be None (e.g.
    a caught-but-swallowed edge case) and not every response carries every
    cache field. Logging failures are non-fatal -- must never break the actual
    Anthropic call this wraps."""
    try:
        db.log_activity(
            actor="system",
            action_type="anthropic_usage",
            detail=f"{caller} · {model}",
            payload={
                "caller": caller,
                "model": model,
                "input_tokens": getattr(usage, "input_tokens", 0) or 0,
                "output_tokens": getattr(usage, "output_tokens", 0) or 0,
                "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
                "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
            },
            outcome="ok",
        )
    except Exception as exc:
        print(f"[anthropic-usage] logging failed (non-fatal): {exc}", flush=True)


def _anthropic_create(client: "anthropic.Anthropic", **kwargs):
    """Routes an Anthropic messages.create() call through the shared circuit
    breaker so a real outage shows up in /api/system/dependencies instead of
    always reporting closed/healthy. Trips only on genuine transient infra
    errors (connection failure, rate limit, 5xx) -- a 400/401/403 means
    Anthropic responded and our request or key was the problem, not a
    dependency-health signal.

    Also self-heals a model-access gap: if the requested model is unavailable to
    this account (NotFound/PermissionDenied), it retries once with _MODEL_FALLBACK
    and logs it, rather than letting a model swap take the agent down."""
    if not _anthropic_breaker.allow_request():
        raise CircuitBreakerOpenError(
            "circuit breaker 'anthropic_api' is open -- skipping call until cooldown elapses"
        )
    try:
        result = client.messages.create(**kwargs)
    except (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.InternalServerError):
        _anthropic_breaker.record_failure()
        raise
    except (anthropic.NotFoundError, anthropic.PermissionDeniedError) as exc:
        # Requested model isn't available to this account. Fall back once so a
        # model-access gap (e.g. MODEL_PRIMARY not enabled) can't take Frank down.
        req_model = kwargs.get("model")
        if req_model and req_model != _MODEL_FALLBACK:
            print(f"[anthropic] model {req_model!r} unavailable ({type(exc).__name__}); "
                  f"falling back to {_MODEL_FALLBACK!r}", flush=True)
            kwargs["model"] = _MODEL_FALLBACK
            result = client.messages.create(**kwargs)
            _anthropic_breaker.record_success()
            _log_anthropic_usage(inspect.stack()[1].function, _MODEL_FALLBACK, getattr(result, "usage", None))
            return result
        raise
    else:
        _anthropic_breaker.record_success()
        _log_anthropic_usage(inspect.stack()[1].function, kwargs.get("model", "?"), getattr(result, "usage", None))
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
db.seed_correction_plan_todos()


# ── Runtime settings → live config sync ────────────────────────────────────────
# The Settings screen stores overrides in db.settings; this pushes them into the
# exact places the code reads them so they take effect without a redeploy:
#   • "env" targets  → os.environ (the per-call getenv flags: image/video engine, model)
#   • "cfg" targets  → business_config module attributes (read live at call time)
# The agent's self-identity strings (baked into _CEO_SYSTEM / AGENT_TOOLS at import)
# are refreshed separately by _refresh_identity() so a rename reaches the agent too.
_SETTINGS_APPLY = {
    "image_engine":     ("env", "IMAGE_ENGINE"),
    "video_engine":     ("env", "AI_VIDEO_ENGINE"),
    "image_model":      ("env", "IMAGE_MODEL"),
    "model_primary":    ("cfg", "MODEL_PRIMARY"),
    "agent_name":       ("cfg", "AGENT_NAME"),
    "agent_name_short": ("cfg", "AGENT_NAME_SHORT"),
    "owner_name":       ("cfg", "OWNER_NAME"),
}


def _apply_settings_overrides() -> None:
    """Sync stored runtime settings into env + business_config so they take effect
    live. Safe to call at startup and after every settings change."""
    try:
        stored = db.all_settings()
    except Exception as exc:
        print(f"[settings] could not load overrides: {exc}", flush=True)
        return
    for key, (kind, target) in _SETTINGS_APPLY.items():
        val = stored.get(key)
        if not val:
            continue
        if kind == "env":
            os.environ[target] = val
        else:
            setattr(business_config, target, val)


_apply_settings_overrides()

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
    "backup_hub_db": {
        "script": "tools/backup_hub_db.py",
        "description": (
            "Export non-secret hub.db state (todos, settings, action/activity history, "
            "user list) to data/hub_db_backups/hub_db_state.json -- the interim recovery "
            "path until a Railway Volume is attached, since the live DB currently wipes on "
            "every redeploy. Commit + push the output file to actually preserve it."
        ),
        "timeout": 30,
        "long_running": False,
        "requires_approval": True,
    },
    "check_digital_file_exposure": {
        "script": "tools/check_digital_file_exposure.py",
        "description": (
            "Read-only audit: flags any active Etsy listing with zero digital files "
            "attached, and any not-yet-published product whose listed source files are "
            "missing on disk. The check that would have caught the 2026-07-15 discovery "
            "that DP1030-1034's files existed nowhere durable, before it became a surprise."
        ),
        "timeout": 120,
        "long_running": False,
    },
    "listing_compliance_sweep": {
        "script": "tools/listing_compliance_sweep.py",
        "description": (
            "Full-shop compliance sweep -- audits EVERY active Etsy listing (not just "
            "manifest-mapped ones; unmapped listings fail closed). Stages a "
            f"deactivate_listing action for each FAIL and a todo for {business_config.OWNER_NAME}'s "
            "review; WARNs get a todo only. Must run in-process here (not from a dev "
            "sandbox) so its db.enqueue_action/add_todo calls land in the real "
            "persistent DB -- requires_approval=True since it queues real takedown "
            "candidates, even though nothing is deactivated until a second, separate "
            "approval on each staged action."
        ),
        "timeout": 400,  # measured ~211s for 140 listings against the real API; buffer for growth
        "long_running": False,
        "requires_approval": True,
    },
}

# Sidecar persistence for commands registered at runtime via the register_command
# chat tool (Phase 2 M3) — _EXEC_COMMANDS above is a static in-memory dict that
# would forget any approved registration on restart, so approved entries are also
# written here and reloaded on every startup. Git-tracked plain JSON, same
# "nothing we delete should be unrecoverable" spirit as data/trash/. Prefers the
# /data Volume so registrations survive a redeploy too, not just a restart —
# same resolver hub.db itself uses (db.resolve_persistent_path).
_REGISTERED_COMMANDS_FILE = db.resolve_persistent_path(
    "registered_commands.json",
    fallback=ROOT / "data" / "registered_commands.json",
    seed_from=ROOT / "data" / "registered_commands.json",
)


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
# trailing newline. APP_TOKEN is the server secret; it must NOT be injected into
# any inline JS string literal visible in page source. Auth uses session cookies.
APP_TOKEN = os.getenv("APP_SECRET_TOKEN", "").strip()
if not APP_TOKEN:
    raise RuntimeError("APP_SECRET_TOKEN is not set — refusing to start with no auth token.")
# If FRANK_USERNAME + FRANK_PASSWORD are both explicitly set in the environment,
# the owner account is seeded automatically at startup (headless / env-controlled
# deployments). Otherwise the table stays empty and the first visitor to /login
# is shown a one-time "Create Your Account" setup screen.
_FRANK_USERNAME_EXPLICIT = os.getenv("FRANK_USERNAME", "").strip().lower()
_FRANK_PASSWORD_EXPLICIT = os.getenv("FRANK_PASSWORD", "").strip()


_MIN_PASSWORD_LEN = 8  # enforced everywhere a password is set — setup, self-service change, admin create/reset


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return f"{salt}${dk.hex()}"


# Excludes visually-ambiguous characters (0/O, 1/I/L) so a handwritten copy of the
# code is never misread — this is meant to be written down once and typed back in,
# not memorized.
_RECOVERY_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def _generate_recovery_code() -> str:
    """A one-time account-recovery code, shown once at account creation and never
    again (only its pbkdf2 hash is stored — same format/strength as a password).
    No email dependency: this is the 'Forgot password?' mechanism for a
    single-operator system where email delivery isn't a given (2026-07-08)."""
    groups = ["".join(secrets.choice(_RECOVERY_ALPHABET) for _ in range(4)) for _ in range(3)]
    return "-".join(groups)


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

# ── Default tester login (Scott, July 2026) — always active, credentials are
# overridable env vars. SECURITY NOTE: there is no restricted/read-only role in
# this system (see _require_owner / "Add Admin" — role is only "owner" or "admin",
# and admins have full API access identical to the owner). This account is
# therefore full-access, not a sandboxed viewer. It's created idempotently (never
# overwrites an existing password on restart) and only for local/private testing —
# rotate TEST_LOGIN_PASSWORD (or disable by setting it to an empty string) before
# this deploy is ever meant to be hardened. ──
_TEST_LOGIN_USERNAME = os.getenv("TEST_LOGIN_USERNAME", "tester").strip().lower()
_TEST_LOGIN_PASSWORD = os.getenv("TEST_LOGIN_PASSWORD", "TesterOnly!2026").strip()
_ENABLE_TEST_LOGIN = os.getenv("ENABLE_TEST_LOGIN", "").strip().lower() in ("1", "true", "yes")


def _seed_test_user_if_missing() -> None:
    """Create the default tester account once, if it doesn't already exist — but
    ONLY when explicitly opted in via ENABLE_TEST_LOGIN=true. Reversed from
    active-by-default (2026-07-03) after the pre-launch security review flagged
    an always-on, full-admin, well-known-password account as a go-live blocker —
    said plainly here rather than silently: this was the right call for a quick
    private test, wrong for a system about to go live. Set TEST_LOGIN_PASSWORD=""
    to additionally hard-disable even if ENABLE_TEST_LOGIN is set."""
    if not _ENABLE_TEST_LOGIN or not _TEST_LOGIN_PASSWORD:
        return
    try:
        if not db.get_hub_user(_TEST_LOGIN_USERNAME):
            db.create_hub_user(_TEST_LOGIN_USERNAME, _hash_password(_TEST_LOGIN_PASSWORD), role="admin")
            print(f"[auth] seeded default tester account '{_TEST_LOGIN_USERNAME}' (full admin access — "
                  "see the security note in main.py if this deploy stops being just for testing)", flush=True)
    except Exception as exc:
        print(f"[auth] tester seed failed: {exc}", flush=True)


_seed_test_user_if_missing()

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
_SERVER_START = datetime.now(timezone.utc)
_BUILD_ID = "59dd421-v204"  # bump on each deploy to confirm Railway is using latest code

def _order_revenue(orders: list) -> float:
    """Shared revenue calculator: sum grandtotal across a list of Etsy order dicts."""
    total = 0.0
    for o in orders:
        gt = o.get("grandtotal", {})
        if isinstance(gt, dict):
            divisor = gt.get("divisor", 100) or 100
            total += gt.get("amount", 0) / divisor
    return round(total, 2)


print(f"[startup] BUILD={_BUILD_ID} PORT={os.getenv('PORT','?')} TOKEN_SET={bool(os.getenv('APP_SECRET_TOKEN'))} ETSY_TOKEN={bool(os.getenv('ETSY_ACCESS_TOKEN'))} ETSY_REFRESH={bool(os.getenv('ETSY_REFRESH_TOKEN'))} ANTHROPIC={bool(ANTHROPIC_KEY)} OPENAI={bool(OPENAI_KEY)}", flush=True)

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(title=f"{business_config.BUSINESS_NAME} Mobile API", version="1.0.0", docs_url=None, redoc_url=None)

# allow_origins=["*"] + allow_credentials=True is actually a no-op/invalid combo per the
# CORS spec for credentialed requests (browsers refuse to honor "*" once credentials are
# involved) — so this also fixes correctness, not just exposure. Native app traffic sends
# no browser Origin header at all, so tightening this list cannot break the mobile app.
# The only legitimate cross-origin caller is the web UI itself (same-origin, BASE = location.origin).
_RAILWAY_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
# Dev-only localhost origins are only included when NOT running on Railway (reuses
# the same signal already used for the prod domain above, rather than a second env
# var) — they were previously always allowed, which is unneeded surface in prod
# (2026-07-08 security review; low exploitability, still dead weight to close).
_CORS_ALLOWED_ORIGINS = [
    o for o in (
        (f"https://{_RAILWAY_DOMAIN}" if _RAILWAY_DOMAIN else None),
        (None if _RAILWAY_DOMAIN else "http://localhost:3000"),
        (None if _RAILWAY_DOMAIN else "http://localhost:8000"),
        (None if _RAILWAY_DOMAIN else "http://localhost:19006"),
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
    # 'unsafe-inline' is required because frank_hud_mockup.py is a single embedded
    # HTML string full of inline <script>/style= — a nonce-based strict CSP would require
    # extracting all inline JS/CSS to separate files first, which is a larger follow-up,
    # out of scope here. Even with 'unsafe-inline' this still blocks third-party
    # script/iframe injection, clickjacking, and MIME-sniffing — real wins over zero headers.
    # 'wasm-unsafe-eval' is required for the offline voice engines (Transformers.js/Whisper,
    # Piper-web TTS) — WebAssembly.compile()/instantiate() is blocked by CSP without it, even
    # though plain script loading and fetch() already worked under script-src 'self'.
    # media-src added 2026-07-10 -- this CSP had no media-src directive at all, so it fell
    # back to default-src 'self', which does NOT cover blob:/data: URLs (they have their own
    # opaque origin, not matched by 'self'). Every TTS playback path in the app (both the
    # local Piper engine and premium OpenAI voice) plays audio via
    # URL.createObjectURL(blob) -> new Audio(url) -- a blob: URL -- and the one-time silent
    # unlock element in _primeAudioPlayback() uses a data: URL. Both were being silently
    # blocked (audio.onerror fires with MEDIA_ERR_SRC_NOT_SUPPORTED, code 4, swallowed by the
    # existing .catch() handlers) -- confirmed live via Playwright: "Refused to load media
    # from 'blob:...' because it violates ... default-src 'self'". This is the actual root
    # cause of Frank's TTS reply being completely silent on every browser/device, not the
    # iOS-standalone-PWA Web Audio bug fixed earlier the same day (that fix was real but
    # wasn't the reason Scott heard nothing -- this was).
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
        "media-src 'self' blob: data:; "
        "connect-src 'self' wss: https:; frame-ancestors 'none'; object-src 'none'"
    )
    return response


# No compression existed anywhere before this — the /frank dashboard alone ships a
# ~314KB inline HTML/CSS/JS payload, and every JSON API response was uncompressed too
# (2026-07-08 performance pass). Registered after CORS/security-headers so it wraps
# them (Starlette's last-registered middleware becomes outermost) and compresses their
# final output as well.
app.add_middleware(GZipMiddleware, minimum_size=500)

# Found in the 2026-07-09 weakness audit: file-upload routes each enforce their own
# cap (_MAX_UPLOAD_BYTES = 30MB), but ordinary JSON-body POST routes (/api/settings,
# /api/account, /api/workflows/{id}/run, etc.) had NO body-size limit at any layer —
# FastAPI/Starlette buffer the entire body before parsing, so an arbitrarily large
# payload could be sent to any of them. This is a blanket outer safety net, not a
# replacement for the tighter per-route upload checks: the cap here (35MB) sits just
# above the largest existing upload limit so it never interferes with a legitimate
# upload — it only catches bodies no real client would ever send. Checked via
# Content-Length before the handler runs, so an oversized request never reaches
# route logic or gets buffered into memory at all.
_MAX_REQUEST_BODY_BYTES = 35 * 1024 * 1024


class _BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > _MAX_REQUEST_BODY_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"Request body exceeds {_MAX_REQUEST_BODY_BYTES // (1024*1024)}MB limit"},
                    )
            except ValueError:
                pass
        return await call_next(request)


app.add_middleware(_BodySizeLimitMiddleware)

# Serve PWA icons (pre-generated files committed to the repo — no runtime PIL).
_STATIC_DIR = ROOT / "tools" / "api_server" / "static"

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


class _CachedStaticFiles(StaticFiles):
    """Adds a Cache-Control header to vendored library assets (Three.js,
    onnxruntime-web, transformers.js, piper-tts) so browsers stop refetching them on
    every page load. Scoped to /vendor/ only -- these paths are NOT content-hashed, so
    a long immutable header would risk serving stale JS after an in-place vendor
    upgrade; 7 days is a safe compromise that still eliminates most of this weight
    from routine dashboard polling (2026-07-08 performance pass). privacy.html and the
    PWA icons are untouched (default browser heuristic caching)."""

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        path = str(args[0]).replace(os.sep, "/")
        if "/vendor/" in path:
            response.headers["Cache-Control"] = "public, max-age=604800"
        return response


if _STATIC_DIR.exists():
    app.mount("/static", _CachedStaticFiles(directory=str(_STATIC_DIR)), name="static")




def _auth_session_or_bearer(request: Request) -> str:
    """Accept any of: session cookie (HUD/PWA browsers), Bearer header (relay/mobile),
    or ?token= query param (file download links). Returns the validated token or raises 401."""
    # 1. Session cookie — browser sends this automatically (same-origin httpOnly)
    if _check_session(request):
        return APP_TOKEN
    # 2. Bearer header — relay process, React Native app
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:]
        if secrets.compare_digest(token, APP_TOKEN):
            return APP_TOKEN
    # 3. Query param — file download links (/api/files/download?token=...)
    token = request.query_params.get("token", "")
    if token and secrets.compare_digest(token, APP_TOKEN):
        return APP_TOKEN
    raise HTTPException(status_code=401, detail="Authentication required")


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

_login_fails: dict[str, list[float]] = {}  # username -> recent failure timestamps
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


# ── File-download tickets ───────────────────────────────────────────────────────
#
# Same problem as the WS tickets above, different trigger: handing a video URL to a
# third party (Instagram/Facebook's Graph API, which fetches it server-side) used to
# embed the long-lived master APP_SECRET_TOKEN in that URL — the same secret that
# authenticates almost every endpoint in this app — so it ended up in Meta's request
# logs on every single social post (2026-07-08 security review). A ticket here is
# scoped to exactly one root+path (not general API access like APP_TOKEN), single-use,
# and short-lived — worthless to anyone who intercepts it after the one fetch it was
# minted for.
_file_tickets: dict[str, tuple[float, str, str]] = {}  # ticket -> (expiry, root, path)
_file_tickets_lock = threading.Lock()
_FILE_TICKET_TTL = 600  # seconds — generous enough for a third party to fetch the file once


def _new_file_ticket(root: str, path: str) -> str:
    ticket = secrets.token_urlsafe(32)
    with _file_tickets_lock:
        _file_tickets[ticket] = (time.time() + _FILE_TICKET_TTL, root, path)
    return ticket


def _consume_file_ticket(ticket: str, root: str, path: str) -> bool:
    """Single-use and scoped to exactly one root+path — returns True and deletes the
    ticket iff it exists, hasn't expired, and matches the requested file exactly."""
    if not ticket:
        return False
    with _file_tickets_lock:
        entry = _file_tickets.pop(ticket, None)
    if entry is None:
        return False
    expiry, t_root, t_path = entry
    return time.time() <= expiry and t_root == root and t_path == path


def _new_session(username: str) -> str:
    sid = secrets.token_urlsafe(32)
    expiry = time.time() + SESSION_TTL
    with _sessions_lock:
        _sessions[sid] = (expiry, username)
    try:
        db.create_session(sid, username, expiry)
    except Exception:
        pass
    return sid


def _check_session(request: Request) -> bool:
    sid = request.cookies.get(SESSION_COOKIE, "")
    if not sid:
        return False
    with _sessions_lock:
        entry = _sessions.get(sid)
        if entry is not None:
            expiry, _ = entry
            if time.time() > expiry:
                del _sessions[sid]
                return False
            return True
    # not in memory — fall back to DB (survives Railway restart)
    try:
        row = db.get_session(sid)
    except Exception:
        return False
    if not row:
        return False
    expiry = datetime.fromisoformat(row["expires_at"]).timestamp()
    with _sessions_lock:
        _sessions[sid] = (expiry, row["username"])
    return True


def _get_session_user(request: Request) -> str:
    sid = request.cookies.get(SESSION_COOKIE, "")
    if not sid:
        return ""
    with _sessions_lock:
        entry = _sessions.get(sid)
        if entry is not None:
            expiry, username = entry
            if time.time() > expiry:
                del _sessions[sid]
                return ""
            return username
    # not in memory — fall back to DB (survives Railway restart)
    try:
        row = db.get_session(sid)
    except Exception:
        return ""
    if not row:
        return ""
    expiry = datetime.fromisoformat(row["expires_at"]).timestamp()
    with _sessions_lock:
        _sessions[sid] = (expiry, row["username"])
    return row["username"]


def _clear_session(request: Request) -> None:
    sid = request.cookies.get(SESSION_COOKIE, "")
    if sid:
        with _sessions_lock:
            _sessions.pop(sid, None)
        try:
            db.delete_session(sid)
        except Exception:
            pass


def _login_rate_limited(username: str) -> bool:
    """Keyed on the attempted username, not client IP — Railway's edge means
    X-Forwarded-For is attacker-supplied with no trusted-proxy validation in front
    of this app, so an IP-keyed lockout was trivially bypassed by sending a fresh
    fake IP on every request (2026-07-08 security review). Username-keyed lockout
    matches the real threat model (brute-forcing one known account) and isn't
    defeated by header spoofing."""
    with _login_fails_lock:
        fails = [t for t in _login_fails.get(username, []) if time.time() - t < LOGIN_WINDOW]
        if fails:
            _login_fails[username] = fails
        else:
            _login_fails.pop(username, None)  # prune empty entries to prevent unbounded growth
        return len(fails) >= LOGIN_MAX_FAILS


def _record_login_fail(username: str) -> None:
    with _login_fails_lock:
        _login_fails.setdefault(username, []).append(time.time())


def _reset_login_fails(username: str) -> None:
    with _login_fails_lock:
        _login_fails.pop(username, None)


# ── Generic per-user rate limiting for AI-spend / Etsy-mutating endpoints ───────
#
# Endpoints that call Anthropic/OpenAI (real $ per call) or mutate live Etsy/social
# state had no throttle beyond auth — a leaked token or scripted abuse could run up
# the bill or spam actions unbounded (2026-07-08 security review). This is a soft
# guardrail, not a hard product limit — generous enough for normal interactive use.
_rate_buckets: dict[str, list[float]] = {}
_rate_buckets_lock = threading.Lock()

_AI_SPEND_RATE_MAX = 30
_AI_SPEND_RATE_WINDOW = 3600  # 1 hour


def _rate_limited(key: str, max_calls: int, window_seconds: int) -> bool:
    """Generic sliding-window limiter — True if `key` already made max_calls within
    the last window_seconds (and does NOT record this call in that case, so a
    blocked caller doesn't get charged for the attempt that was rejected)."""
    now = time.time()
    with _rate_buckets_lock:
        calls = [t for t in _rate_buckets.get(key, []) if now - t < window_seconds]
        if len(calls) >= max_calls:
            _rate_buckets[key] = calls
            return True
        calls.append(now)
        _rate_buckets[key] = calls
        return False


def _rate_limited_auth(request: Request) -> str:
    """Drop-in replacement for _auth_session_or_bearer on endpoints that spend real
    API budget or mutate live Etsy/social state per call. Session users are limited
    per-username; bearer/token callers (relay, automation) share one bucket since
    this app has a single shared APP_SECRET_TOKEN, not per-caller credentials."""
    token = _auth_session_or_bearer(request)
    uname = _get_session_user(request) or "bearer"
    if _rate_limited(f"spend:{uname}", _AI_SPEND_RATE_MAX, _AI_SPEND_RATE_WINDOW):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded — max {_AI_SPEND_RATE_MAX} AI-generation/"
                   f"Etsy-mutating calls per hour. Try again later.",
        )
    return token


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
  .logo-sub{{font-size:12px;color:#708392;margin-top:1px}}
  label{{display:block;font-size:11px;font-weight:600;color:#708392;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px}}
  input[type=text],input[type=password]{{width:100%;padding:10px 12px;margin-bottom:16px;
    background:#0b0f14;border:1px solid #2a3744;border-radius:8px;color:#e8eef3;font-size:14px;outline:none;transition:border .15s}}
  input[type=text]:focus,input[type=password]:focus{{border-color:#2ec4c4}}
  button{{width:100%;padding:11px;background:#2ec4c4;border:none;border-radius:8px;
    color:#06222a;font-weight:700;font-size:14px;cursor:pointer;letter-spacing:.03em;margin-top:4px;transition:background .15s}}
  button:hover{{background:#38d8d8}}
  .err{{background:#1c0f0f;border:1px solid #4a1c1c;border-radius:7px;color:#ff8080;font-size:12px;padding:8px 10px;margin-bottom:14px}}
  .cross-link{{text-align:center;margin-top:16px}}
  .cross-link a{{color:#2ec4c4;font-size:12px;text-decoration:none}}
  .cross-link a:hover{{text-decoration:underline}}
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
    <div class="cross-link"><a href="/forgot-password">Forgot password?</a></div>
    {cross_link}
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
  .logo-sub{{font-size:12px;color:#708392;margin-top:1px}}
  .setup-heading{{font-size:15px;font-weight:700;color:#e8eef3;margin:18px 0 4px}}
  .setup-hint{{font-size:11px;color:#708392;margin-bottom:18px;line-height:1.5}}
  label{{display:block;font-size:11px;font-weight:600;color:#708392;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px}}
  input[type=text],input[type=password]{{width:100%;padding:10px 12px;margin-bottom:16px;
    background:#0b0f14;border:1px solid #2a3744;border-radius:8px;color:#e8eef3;font-size:14px;outline:none;transition:border .15s}}
  input[type=text]:focus,input[type=password]:focus{{border-color:#2ec4c4}}
  button{{width:100%;padding:11px;background:#2ec4c4;border:none;border-radius:8px;
    color:#06222a;font-weight:700;font-size:14px;cursor:pointer;letter-spacing:.03em;margin-top:4px;transition:background .15s}}
  button:hover{{background:#38d8d8}}
  .err{{background:#1c0f0f;border:1px solid #4a1c1c;border-radius:7px;color:#ff8080;font-size:12px;padding:8px 10px;margin-bottom:14px}}
  .warn{{background:#2a1206;border:1px solid #a33;border-radius:7px;color:#ffb27a;font-size:12px;padding:10px 12px;margin-bottom:16px;line-height:1.5}}
  .warn b{{color:#ff8a5c}}
  .once{{font-size:10px;color:#3a4a56;margin-top:14px;text-align:center}}
  .cross-link{{text-align:center;margin-top:16px}}
  .cross-link a{{color:#2ec4c4;font-size:12px;text-decoration:none}}
  .cross-link a:hover{{text-decoration:underline}}
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
    {persist_warning}
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
    {signin_link}
  </div>
</body>
</html>"""

# Shown exactly once, immediately after an account is created (setup or Add Admin).
# The code itself is never stored — only its pbkdf2 hash — so this is the only chance
# to see/save it. No email dependency: see _generate_recovery_code().
_RECOVERY_CODE_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{hub_title} — Save your recovery code</title>
<style>
  *{{box-sizing:border-box}}
  body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:#0b0f14;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
  .box{{width:380px;padding:36px 32px 28px;background:#121821;border:1px solid #1f2a36;border-radius:14px;box-shadow:0 8px 32px rgba(0,0,0,.5)}}
  .logo{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
  .logo-dot{{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#2ec4c4,#1a8f8f);display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;font-weight:700;flex-shrink:0}}
  .logo-text{{font-size:17px;font-weight:600;color:#e8eef3}}
  h1{{font-size:15px;font-weight:700;color:#e8eef3;margin:18px 0 4px}}
  .hint{{font-size:12px;color:#a8b4bf;margin-bottom:18px;line-height:1.6}}
  .warn{{background:#2a1206;border:1px solid #a33;border-radius:7px;color:#ffb27a;font-size:12px;padding:10px 12px;margin-bottom:16px;line-height:1.5}}
  .warn b{{color:#ff8a5c}}
  .code{{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:20px;font-weight:700;
    letter-spacing:2px;color:#7cf0f0;background:#0b0f14;border:1px solid #2a3744;border-radius:8px;
    padding:16px;text-align:center;margin-bottom:18px;user-select:all;word-break:break-all}}
  button,a.btn{{display:block;width:100%;padding:11px;background:#2ec4c4;border:none;border-radius:8px;
    color:#06222a;font-weight:700;font-size:14px;cursor:pointer;letter-spacing:.03em;text-align:center;
    text-decoration:none;box-sizing:border-box}}
  button:hover,a.btn:hover{{background:#38d8d8}}
</style>
</head>
<body>
  <div class="box">
    <div class="logo">
      <div class="logo-dot">F</div>
      <div class="logo-text">{hub_title}</div>
    </div>
    <h1>Save your account recovery code</h1>
    <div class="warn">⚠️ <b>This is shown ONE TIME only.</b> If you lose both your password and this code, the only way back in is wiping the account entirely. Write it down or save it in a password manager now.</div>
    <div class="code">{recovery_code}</div>
    <div class="hint">If you ever forget your password, use "Forgot password?" on the sign-in screen with the username <b>{username}</b> and this code to set a new one — no email needed.</div>
    <a class="btn" href="{next_path}">I've saved it — Continue</a>
  </div>
</body>
</html>"""

# "Forgot password?" — username + recovery code + new password, no email involved.
_FORGOT_PASSWORD_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{hub_title} — Reset your password</title>
<style>
  *{{box-sizing:border-box}}
  body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:#0b0f14;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
  .box{{width:340px;padding:36px 32px 28px;background:#121821;border:1px solid #1f2a36;border-radius:14px;box-shadow:0 8px 32px rgba(0,0,0,.5)}}
  .logo{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
  .logo-dot{{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#2ec4c4,#1a8f8f);display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;font-weight:700;flex-shrink:0}}
  .logo-text{{font-size:17px;font-weight:600;color:#e8eef3}}
  h1{{font-size:15px;font-weight:700;color:#e8eef3;margin:18px 0 4px}}
  .hint{{font-size:11px;color:#708392;margin-bottom:18px;line-height:1.5}}
  label{{display:block;font-size:11px;font-weight:600;color:#708392;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px}}
  input[type=text],input[type=password]{{width:100%;padding:10px 12px;margin-bottom:16px;
    background:#0b0f14;border:1px solid #2a3744;border-radius:8px;color:#e8eef3;font-size:14px;outline:none;transition:border .15s}}
  input[type=text]:focus,input[type=password]:focus{{border-color:#2ec4c4}}
  button{{width:100%;padding:11px;background:#2ec4c4;border:none;border-radius:8px;
    color:#06222a;font-weight:700;font-size:14px;cursor:pointer;letter-spacing:.03em;margin-top:4px}}
  button:hover{{background:#38d8d8}}
  .err{{background:#1c0f0f;border:1px solid #4a1c1c;border-radius:7px;color:#ff8080;font-size:12px;padding:8px 10px;margin-bottom:14px}}
  .cross-link{{text-align:center;margin-top:16px}}
  .cross-link a{{color:#2ec4c4;font-size:12px;text-decoration:none}}
  .cross-link a:hover{{text-decoration:underline}}
</style>
</head>
<body>
  <div class="box">
    <div class="logo">
      <div class="logo-dot">F</div>
      <div class="logo-text">{hub_title}</div>
    </div>
    <h1>Reset your password</h1>
    <div class="hint">Enter your username, the recovery code you saved when the account was created, and a new password.</div>
    {error_html}
    <form method="post" action="/forgot-password" autocomplete="off">
      <label for="fp-user">Username</label>
      <input type="text" id="fp-user" name="username" autofocus autocomplete="username" required>
      <label for="fp-code">Recovery code</label>
      <input type="text" id="fp-code" name="recovery_code" placeholder="XXXX-XXXX-XXXX" autocomplete="off" required>
      <label for="fp-pass">New password</label>
      <input type="password" id="fp-pass" name="new_password" autocomplete="new-password" required>
      <button type="submit">Reset password</button>
    </form>
    <div class="cross-link"><a href="/login">Back to sign in</a></div>
  </div>
</body>
</html>"""


def _safe_next(next_path: str) -> str:
    # Only allow same-site relative paths — never redirect off-site via the next param.
    if next_path and next_path.startswith("/") and not next_path.startswith("//"):
        return next_path
    return "/"


@app.get("/login", response_class=HTMLResponse)
def login_page(next: str = "/", error: str = "", mode: str = ""):
    safe_next = _safe_next(next)
    no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate"}
    empty = db.hub_users_empty()
    # mode=signin is the "Already have an account? Sign in instead" escape hatch on
    # the setup page — forces the plain sign-in form even while the table is empty,
    # so a account creation isn't the only path shown. If storage keeps getting
    # wiped (see the persist-warning below), setting FRANK_USERNAME/FRANK_PASSWORD
    # in Railway auto-recreates the real owner account on every restart, which is
    # the actual fix for repeatedly landing on the setup screen — this link is a
    # manual fallback, not a substitute for that.
    if empty and mode != "signin":
        error_html = f'<div class="err">{error}</div>' if error else ""
        # If storage is ephemeral, landing on this setup page usually means the DB was
        # wiped by a container restart (Railway has no /data volume) — not a genuine
        # first run. Say so loudly so the account you're about to create doesn't just
        # vanish on the next deploy.
        persist_warning = "" if db.is_persistent() else (
            '<div class="warn">⚠️ <b>Storage is not persistent.</b> You\'re seeing this '
            'setup screen because the database resets on every restart. Attach a Railway '
            'Volume mounted at <b>/data</b>, or the account you create here (and everything '
            'else) will be lost on the next deploy.</div>'
        )
        signin_link = (
            f'<div class="cross-link"><a href="/login?mode=signin&next={safe_next}">'
            'Already have an account? Sign in instead</a></div>'
        )
        return HTMLResponse(
            _SETUP_PAGE.format(error_html=error_html, next_path=safe_next, hub_title=business_config.BUSINESS_NAME,
                               persist_warning=persist_warning, signin_link=signin_link),
            headers=no_cache,
        )
    if error == "noaccount":
        error_html = '<div class="err">No account exists yet with that username. Use "Create one instead" below, or ask the owner to set one up.</div>'
    else:
        error_html = '<div class="err">Incorrect username or password. Try again.</div>' if error else ""
    cross_link = (
        f'<div class="cross-link"><a href="/login?next={safe_next}">First time? Create an account instead</a></div>'
        if empty else ""
    )
    return HTMLResponse(
        _LOGIN_PAGE.format(error_html=error_html, next_path=safe_next, hub_title=business_config.BUSINESS_NAME,
                           cross_link=cross_link),
        headers=no_cache,
    )


@app.post("/login")
def login_submit(
    username: str = Form(""),
    password: str = Form(""),
    confirm_password: str = Form(""),
    setup_mode: str = Form(""),
    next: str = Form("/"),
):
    safe_next = _safe_next(next)

    # ── First-run setup: create the owner account ──────────────────────────
    # Gated on the explicit setup_mode=1 hidden field (only _SETUP_PAGE's form sends
    # it) — NOT on db.hub_users_empty() alone. A plain login-form POST (no
    # confirm_password field) landing here while the table happens to be empty used
    # to fall into this branch and fail with a confusing "Passwords do not match"
    # (confirm_password arrives blank). That case is now handled explicitly below
    # with an accurate message instead.
    if setup_mode == "1":
        uname = username.strip().lower()
        pw = password.strip()
        cpw = confirm_password.strip()
        if not uname or not pw:
            return RedirectResponse(f"/login?error=Username+and+password+are+required&next={safe_next}", status_code=303)
        if pw != cpw:
            return RedirectResponse(f"/login?error=Passwords+do+not+match&next={safe_next}", status_code=303)
        if len(pw) < _MIN_PASSWORD_LEN:
            return RedirectResponse(f"/login?error=Password+must+be+at+least+8+characters&next={safe_next}", status_code=303)
        if not db.hub_users_empty():
            # Table was populated between GET and POST (race) — fall through to normal login
            pass
        else:
            recovery_code = _generate_recovery_code()
            db.create_hub_user(uname, _hash_password(pw), role="owner",
                                recovery_code_hash=_hash_password(recovery_code))
            print(f"[auth] owner account created: '{uname}'", flush=True)
            sid = _new_session(uname)
            no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate"}
            resp = HTMLResponse(
                _RECOVERY_CODE_PAGE.format(hub_title=business_config.BUSINESS_NAME,
                                           recovery_code=recovery_code, username=uname, next_path=safe_next),
                headers=no_cache,
            )
            resp.set_cookie(SESSION_COOKIE, sid, httponly=True, secure=True, samesite="lax")
            return resp

    # ── Normal login ────────────────────────────────────────────────────────
    # Someone used the "Already have an account? Sign in instead" link but the
    # table is genuinely empty (no account exists here right now) — say so plainly
    # rather than a generic "incorrect password", and keep them on the sign-in form
    # (mode=signin) instead of silently bouncing back to account creation.
    if db.hub_users_empty():
        return RedirectResponse(f"/login?mode=signin&error=noaccount&next={safe_next}", status_code=303)
    uname = username.strip().lower()
    if _login_rate_limited(uname):
        return Response(content="Too many failed attempts. Try again in a few minutes.", status_code=429)
    user_row = db.get_hub_user(uname)
    if user_row and _verify_password(user_row["pw_hash"], password.strip()):
        _reset_login_fails(uname)
        sid = _new_session(uname)
        resp = RedirectResponse(safe_next, status_code=303)
        resp.set_cookie(SESSION_COOKIE, sid, httponly=True, secure=True, samesite="lax")
        return resp
    _record_login_fail(uname)
    return RedirectResponse(f"/login?error=1&next={safe_next}", status_code=303)


@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(error: str = ""):
    error_html = ""
    if error == "badcode":
        error_html = '<div class="err">Username or recovery code is incorrect.</div>'
    elif error == "short":
        error_html = f'<div class="err">New password must be at least {_MIN_PASSWORD_LEN} characters.</div>'
    no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate"}
    return HTMLResponse(
        _FORGOT_PASSWORD_PAGE.format(hub_title=business_config.BUSINESS_NAME, error_html=error_html),
        headers=no_cache,
    )


@app.post("/forgot-password")
def forgot_password_submit(
    username: str = Form(""),
    recovery_code: str = Form(""),
    new_password: str = Form(""),
):
    # Same brute-force protection as normal login — a recovery code is exactly the
    # kind of secret someone could try to guess, and this reuses the identical
    # per-username lockout rather than inventing a second rate limiter.
    uname = username.strip().lower()
    if _login_rate_limited(uname):
        return Response(content="Too many attempts. Try again in a few minutes.", status_code=429)
    code = recovery_code.strip().upper()
    user_row = db.get_hub_user(uname)
    if (
        not user_row
        or not user_row.get("recovery_code_hash")
        or not _verify_password(user_row["recovery_code_hash"], code)
    ):
        _record_login_fail(uname)
        return RedirectResponse("/forgot-password?error=badcode", status_code=303)
    new_pw = new_password.strip()
    if len(new_pw) < _MIN_PASSWORD_LEN:
        return RedirectResponse("/forgot-password?error=short", status_code=303)
    _reset_login_fails(uname)
    db.update_hub_user_password(uname, _hash_password(new_pw))
    with _sessions_lock:
        to_remove = [sid for sid, (_, u) in _sessions.items() if u == uname]
        for sid in to_remove:
            del _sessions[sid]
    try:
        db.delete_sessions_for_user(uname)
    except Exception as exc:
        # This DB call is what makes a password reset actually revoke sessions that
        # survive a restart (the in-memory _sessions cleanup above only covers this
        # process's lifetime) -- silently swallowing a failure here would mean a
        # stale/compromised cookie could outlive the password change with zero trace
        # of why (2026-07-08 correction pass: previously bare `except Exception: pass`).
        print(f"[auth] delete_sessions_for_user({uname!r}) failed -- sessions may not be "
              f"fully revoked: {exc}", flush=True)
    return RedirectResponse("/login", status_code=303)


@app.get("/logout")
def logout(request: Request):
    """No longer clears the session — a bare GET is a state-changing action reachable
    by any cross-site link/redirect (2026-07-08 security review). The app's own UI
    already only ever logs out via POST /logout (doLogout() in the HUD). This route
    is kept only so an old bookmark/link lands somewhere sane instead of erroring."""
    return RedirectResponse("/login", status_code=303)


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


async def _fetch_with_degrade(cache_key: str | None, coro, *, timeout: float):
    """Await an Etsy-touching `coro` with a hard timeout, and degrade
    gracefully instead of ever bubbling a raw 500 or a bare-504 to the
    client: on a timeout, an `EtsyAPIError` (including the circuit
    breaker's fast "open" rejection), or any other exception, this serves
    the last cached value under `cache_key` even if it's past its normal
    TTL (tagged `stale: true`) when one exists in the in-process cache,
    otherwise raises a clean structured 503 with a retry hint.

    Added 2026-07-10: `/api/listings` was confirmed live to let
    `EtsyAPIError` (a fast circuit-breaker-open rejection) propagate
    completely unhandled into a raw 500 -- the only exception any of these
    routes used to catch was `asyncio.TimeoutError`. Separately, a
    concurrency bug in `resilience.CircuitBreaker.allow_request()` (fixed
    the same day) let several endpoints race through as duplicate
    half-open "probes" at once, each hanging on a real, slow, still-
    rate-limited Etsy call until its own internal timeout fired --
    `/api/metrics`, `/api/star-seller`, and `/api/credentials/status` were
    each confirmed live returning a bare "Etsy timeout" 504 with no
    fallback. See ops_runbook.md for the live traceback that diagnosed
    this. Does not touch a route's own on-success caching -- callers still
    call `_cache_set` themselves after a genuine live fetch."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except Exception as exc:
        stale = _cache_get(cache_key, ttl=float("inf")) if cache_key else None
        if stale is not None:
            if isinstance(stale, dict):
                stale = {**stale, "stale": True, "stale_reason": str(exc)[:200]}
            return stale
        raise HTTPException(
            status_code=503,
            detail={
                "error": "etsy_unavailable",
                "detail": str(exc)[:200],
                "retry_after_seconds": 60,
            },
        ) from exc


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
    fut: asyncio.Future = asyncio.get_running_loop().create_future()
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
#
# Found 2026-07-09: this used to be a plain ROOT-relative path, which is a
# SECOND persistence gap distinct from hub.db — attaching a Railway Volume at
# /data doesn't touch it. Now prefers /data/knowledge_base, seeded once from
# the repo copy baked into the image (see .dockerignore's data/knowledge_base
# negation — these .md files used to be excluded from the image entirely, so
# there wasn't even a baked-in copy to seed from until that was fixed too).
_OPS_RUNBOOK_PATH = db.resolve_persistent_path(
    "knowledge_base/ops_runbook.md",
    fallback=ROOT / "data" / "knowledge_base" / "ops_runbook.md",
    seed_from=ROOT / "data" / "knowledge_base" / "ops_runbook.md",
)


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
    "etsy_app_credentials_invalid": (
        f"Etsy rejected the app credentials themselves (not a token) -- ETSY_CLIENT_ID / ETSY_CLIENT_SECRET "
        f"don't match what Etsy has on file for this app. {business_config.OWNER_NAME} must open the Etsy "
        "Developer Console (etsy.com/developers/your-apps), open the app, and copy the current keystring + "
        "shared secret (the shared secret is hidden behind a reveal icon) into ETSY_CLIENT_ID / ETSY_CLIENT_SECRET "
        "in Railway's environment variables (and local .env), then redeploy. Re-running etsy_oauth.py will NOT "
        "fix this -- that only refreshes the access/refresh token pair, not the app's own client_id/secret."
    ),
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
        if status == 403 and ("api key not found" in text or "incorrect shared secret" in text):
            # Distinct from a generic 403 (which the circuit breaker deliberately does
            # NOT trip on -- see ops_runbook.md 2026-xx-xx "403 removed from
            # _BREAKER_TRIP_STATUSES"). This exact Etsy error text means the app's own
            # client_id/client_secret are being rejected, not an expired token -- a
            # completely different remediation from etsy_auth above.
            return "etsy_app_credentials_invalid"
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
# Same /data-preferring resolver as _OPS_RUNBOOK_PATH above — this file gets
# appended to at runtime (log_learning tool) just like the runbook does.

_CEO_LEARNINGS_PATH = db.resolve_persistent_path(
    "knowledge_base/ceo_learnings.md",
    fallback=ROOT / "data" / "knowledge_base" / "ceo_learnings.md",
    seed_from=ROOT / "data" / "knowledge_base" / "ceo_learnings.md",
)


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
            model=business_config.MODEL_CHEAP,
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
async def get_kb(q: str = "", _token: str = Depends(_auth_session_or_bearer)):
    if q.strip():
        results = await asyncio.to_thread(_kb_search, q.strip())
        return {"query": q.strip(), "results": results}
    docs = await asyncio.to_thread(_kb_docs)
    return {"docs": docs}


@app.get("/api/kb/{filename}")
async def get_kb_doc(filename: str, _token: str = Depends(_auth_session_or_bearer)):
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
async def get_memory(_token: str = Depends(_auth_session_or_bearer)):
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
4. tool_evaluations.md via read_knowledge_base_doc — "is X tool/repo/MCP server something I
   need?" has a repeatable process and its own log; see ceo_operating_playbook.md section 14
   (Tool & MCP Fit-Check Protocol) before re-researching a tool that sounds familiar.
5. The rest of data/knowledge_base/ via read_knowledge_base_doc, including CLAUDE.md.
6. A web search — for anything only the live internet knows (see WEB SEARCH above).
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

# The identity names baked into _CEO_SYSTEM/AGENT_TOOLS above, captured at import.
# (_apply_settings_overrides ran before this, so on a fresh process these already
# equal any stored override — the localize pass below is only for a RUNTIME rename.)
_IDENTITY_BAKED = (business_config.AGENT_NAME, business_config.AGENT_NAME_SHORT,
                   business_config.OWNER_NAME)


def _localize_identity(text: str) -> str:
    """Swap the baked-in agent/owner names for the CURRENT ones so a runtime rename
    reaches the agent's self-identity + tool descriptions without a restart. No-op
    (returns text unchanged, so prompt-cache still hits) when nothing changed.
    Replaces longest baked name first so 'Frank' inside 'Fucking Frank' is safe."""
    current = (business_config.AGENT_NAME, business_config.AGENT_NAME_SHORT,
               business_config.OWNER_NAME)
    if current == _IDENTITY_BAKED:
        return text
    out = text
    for baked, now in sorted(zip(_IDENTITY_BAKED, current), key=lambda p: -len(p[0] or "")):
        if baked and baked != now:
            out = out.replace(baked, now)
    return out


def _refresh_identity() -> None:
    """Called after a settings change: re-sync config and bust the HUD html cache so
    the renamed identity shows up on the next page load. The agent system prompt +
    tools localize per-request (see _system_block/_tools_with_cache), so they need
    no cache busting."""
    _apply_settings_overrides()
    try:
        import frank_hud_mockup
        frank_hud_mockup._frank_html_cache = None
    except Exception:
        pass


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
                        "update_tags", "update_title", "update_description", "publish_listing",
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
                "description": {
                    "type": "string",
                    "description": "Full replacement description text for update_description.",
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
        "name": "qc_check_product",
        "description": (
            "Run the pre-publish Quality Check on a product's files — the same gates "
            "used before anything is submitted for review: PDF page counts, sticker-pack "
            "transparency and individual-sticker count, ZIP integrity, and print-size "
            "folders. Returns a structured pass/warn/fail with per-file detail. "
            "Fully local and read-only — no external API call, no cost, changes nothing. "
            "Use this whenever asked to check, verify, or QC a product (e.g. 'is DP1030 "
            "ready to publish?')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pid": {"type": "string", "description": "Product code to check, e.g. 'DP1030'."},
            },
            "required": ["pid"],
        },
    },
    {
        "name": "generate_listing_photos",
        "description": (
            "Generate the full 10-photo Etsy listing set for a planner from its built PDF — "
            "real rendered pages in device mockups (satisfies the cardinal 'photos must show "
            "the REAL product' rule; no AI stand-ins). Local render, effectively no API cost. "
            "Writes into the product's <pid>_listing_images/ folder, openable from Files. "
            "Requires the planner PDF to already exist. The only AI touch is photo 7 (the "
            "app-compatibility graphic) when the shared asset is missing — rendered on the "
            "chosen engine (default Gemini). Use when asked to make or regenerate a product's "
            "listing photos."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pid": {"type": "string", "description": "Planner code, e.g. 'DP1030'."},
                "engine": {"type": "string", "enum": ["gemini", "openai", "gpt-image-2", "ideogram"],
                           "description": "Art engine for photo 7 if it must be generated. Default 'gemini'."},
            },
            "required": ["pid"],
        },
    },
    {
        "name": "build_planner",
        "description": (
            "Build a full digital planner from scratch — base dated + undated PDFs with an "
            "AI-generated kawaii cover, then finalized with hyperlinked navigation, a TOC, "
            "fillable form fields, and embedded sticker sheets. Runs in the BACKGROUND "
            "(~2-4 min); the finished <pid>.pdf and <pid>U.pdf appear in Files when done. "
            "The cover art is the only paid AI step (~a cent) — this is the one builder that "
            "spends money. Defaults to the Gemini art engine (no OpenAI needed). Use when "
            "asked to build or rebuild a planner. Only works for configured planner codes "
            "(DP1030-DP1034)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pid": {"type": "string", "description": "Planner code, e.g. 'DP1030'."},
                "engine": {"type": "string", "enum": ["gemini", "openai", "gpt-image-2", "ideogram"],
                           "description": "Art engine for the cover. Default 'gemini'."},
            },
            "required": ["pid"],
        },
    },
    {
        "name": "build_product",
        "description": (
            "Build an ENTIRE product from a single planner code, end to end: sticker pack → "
            "planner PDFs (dated + undated, with the sticker sheets embedded) → all 10 listing "
            "photos → a final Quality Check. Runs in the BACKGROUND (~6-10 min); each "
            "deliverable appears in Files as it finishes, and <pid>_product_build.log carries "
            "the live log + the QC verdict. Defaults to the Gemini art engine. Nothing is "
            "published (Scott-gated). Use when asked to build/make/produce a whole product or "
            "'everything' for a planner code. Only configured planner codes (DP1030-DP1034)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pid": {"type": "string", "description": "Planner code, e.g. 'DP1030'."},
                "engine": {"type": "string", "enum": ["gemini", "openai", "gpt-image-2", "ideogram"],
                           "description": "Art engine for cover + sticker sheets. Default 'gemini'."},
            },
            "required": ["pid"],
        },
    },
    {
        "name": "build_sticker_pack",
        "description": (
            "Build a planner's full kawaii sticker pack from scratch — generate the themed "
            "sheets (matching the planner's color palette), strip their backgrounds to "
            "transparent, segment every sticker into an individual PNG, and package "
            "<pid>_sticker_pack.zip (png_sheets/ + individual_stickers/). Runs in the "
            "BACKGROUND (~2-4 min); the ZIP appears in Files when done. Sheet art is the "
            "paid AI step. Reports a REAL measured sticker count, but the sheets still need "
            "a human eyeball for garbled in-image text before the count goes on a live "
            "listing. Defaults to the Gemini art engine (no OpenAI needed — the pack renders "
            "on a solid background and is stripped to transparent, so any engine works). Only "
            "works for codes with a sticker spec (DP1030-DP1034)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pid": {"type": "string", "description": "Planner code, e.g. 'DP1030'."},
                "sheets": {"type": "integer",
                           "description": "Optional: only build the first N sheets (default: all 9)."},
                "engine": {"type": "string", "enum": ["gemini", "openai", "gpt-image-2", "ideogram"],
                           "description": "Art engine for the sheets. Default 'gemini'."},
            },
            "required": ["pid"],
        },
    },
    {
        "name": "generate_print_zip",
        "description": (
            "Build a wall-art product's multi-size print ZIP from its source JPG — "
            "4×6/8×12/12×18/16×24, 8×10/16×20, A4/A3, and square, all at 300 DPI in sRGB, "
            "with a README. Pure local resize, no API cost. Rejects lifestyle-composite "
            "source files (only raw art). Writes print_zips/<pid>_print_sizes.zip. Use when "
            "asked to make the printable size set for a wall-art listing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pid": {"type": "string", "description": "Wall-art code, e.g. 'WA1030'."},
            },
            "required": ["pid"],
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
                "text": {"type": "string", "description": "The to-do item text, one short line."},
                "category": {
                    "type": "string",
                    "enum": ["question", "scott_only", "frank_can_do", "general"],
                    "description": (
                        f"How this shows up in the dashboard's category filter. 'question' gets a tap-to-answer "
                        f"UI — use it when you genuinely need {business_config.OWNER_NAME}'s decision, not just an "
                        f"FYI. 'scott_only' for something only he can physically do (a login only he has, a "
                        f"purchase, a manual re-auth). 'frank_can_do' for something you could do yourself but "
                        f"want on record. Defaults to 'general' (a plain FYI notice) if omitted."
                    ),
                },
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

# Wire in the Playwright browser tools so Frank can SEE rendered pages — verify his own
# live listings render correctly (the "never lie / show the real product" rule), screenshot
# them, and read JS-heavy research pages that the requests-based browse_web can't. Handlers
# live in tools/browser_automation.py (top-level import is cheap: playwright itself is lazy-
# imported only when a browser tool actually runs). Appended after web_search so the hosted
# tool keeps its slot; cache_control is applied to whatever ends up last by _tools_with_cache.
import browser_automation as _browser_automation  # tools/ is on sys.path (line 43)
AGENT_TOOLS.extend(_browser_automation.TOOL_DEFINITIONS)
_BROWSER_TOOL_NAMES = {t["name"] for t in _browser_automation.TOOL_DEFINITIONS}

# Video understanding — let Frank WATCH a video (local file or URL) via Gemini's native
# video model and get a text analysis back. Handlers in tools/video_understanding.py
# (google-genai + yt-dlp are lazy-imported only when watch_video runs). Needs GEMINI_API_KEY.
import video_understanding as _video_understanding
AGENT_TOOLS.extend(_video_understanding.TOOL_DEFINITIONS)
_VIDEO_TOOL_NAMES = {t["name"] for t in _video_understanding.TOOL_DEFINITIONS}

# Etsy Ads — let Frank discuss ad performance/ROAS/strategy in chat. Existed as a fully
# working module with its own TOOL_DEFINITIONS but was never registered here (2026-07-09
# tool audit). Etsy has no public Ads API for third-party apps, so every number here comes
# from tools/etsy_ads_tools.py's local DataStore log (log_ad_spend), never a live Etsy call
# — set_daily_budget/toggle_listing_ad only update that local tracking state too (each says
# so in its own response), so none of these need the Action Center approval gate. Fixed this
# module's own `from tools.X import Y` imports (same class of bug as task #189 — it was never
# actually importable from here before) while wiring it in.
import etsy_ads_tools as _etsy_ads_tools
AGENT_TOOLS.extend(_etsy_ads_tools.TOOL_DEFINITIONS)
_ETSY_ADS_TOOL_NAMES = {t["name"] for t in _etsy_ads_tools.TOOL_DEFINITIONS}

# TikTok — stage a video post for approval. tools/tiktok_poster.py is a real, working
# posting client, previously only reachable via manual CLI (command_center.py), never
# Frank's chat agent (2026-07-09 tool audit). "Post to social media accounts" is a Hard
# Stop in CLAUDE.md's Autonomy Boundaries, so — unlike the Etsy Ads tools above — this
# does NOT call tiktok_poster.post_video() directly. It only ever stages a post_tiktok
# action (see _SOCIAL_STAGED_ACTION_TYPES) for approval in the Action Center, same
# pattern as post_scheduled_art.py's fix in the previous session. Appended here as a
# single dict (not via .extend(), since this is main.py's own tool, not an external
# module) rather than in the main AGENT_TOOLS literal above, to keep this whole
# TikTok-wiring change in one place for review.
AGENT_TOOLS.append({
    "name": "stage_tiktok_post",
    "description": (
        "Stage a TikTok video post for approval in the Action Center — does NOT post "
        "directly. The video must already exist in the staged_videos folder. Rejecting "
        "the staged action never calls TikTok's API; only an explicit approval does."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "video_path": {
                "type": "string",
                "description": "Filename of the .mp4 within the staged_videos folder (max 50MB, TikTok's own limit).",
            },
            "caption": {
                "type": "string",
                "description": "Caption text, including any hashtags (max 2200 chars, TikTok's own limit).",
            },
        },
        "required": ["video_path", "caption"],
    },
})

# Pinterest — tools/pinterest_api.py + pinterest_batch_poster.py are a real, working
# posting client, previously only reachable via manual CLI, never Frank's chat agent
# (2026-07-17 capabilities audit — same "built but never wired" bug class as TikTok
# above; only reference in this whole file before this was a credential-status check).
# Same Hard Stop reasoning as TikTok: stages a post_pinterest action for approval,
# never calls pinterest_api.PinterestClient.create_pin() directly. The pin image comes
# from the listing's OWN already-public Etsy photo (EtsyAPIClient().get_listing_images,
# same rank-1 URL selection tools/pinterest_batch_poster.py already used) — no need for
# Frank to expose any file publicly, and it only works for a listing already live on
# Etsy (an unpublished draft has no public image URL to hand Pinterest).
# list_pinterest_boards is read-only (which boards exist to post into) and callable
# directly, same "Fully Autonomous" tier as every other read-only Etsy tool.
AGENT_TOOLS.append({
    "name": "stage_pinterest_post",
    "description": (
        "Stage a Pinterest pin for approval in the Action Center — does NOT post "
        "directly. Uses the listing's own rank-1 Etsy photo as the pin image (the "
        "listing must already be live/active on Etsy) and links the pin back to that "
        "listing. Rejecting the staged action never calls Pinterest's API; only an "
        "explicit approval does."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "listing_id": {"type": "integer", "description": "The live Etsy listing whose photo becomes the pin image."},
            "board_name": {"type": "string", "description": "Pinterest board to pin into (created if it doesn't exist yet)."},
            "title": {"type": "string", "description": "Pin title (max 100 chars, Pinterest's own limit)."},
            "description": {"type": "string", "description": "Pin description (max 500 chars, Pinterest's own limit)."},
        },
        "required": ["listing_id", "board_name", "title", "description"],
    },
})
AGENT_TOOLS.append({
    "name": "list_pinterest_boards",
    "description": "Read-only: list every Pinterest board already created on the connected account, with each board's id and pin count. Use this to see valid board_name values before staging a pin.",
    "input_schema": {"type": "object", "properties": {}},
})
_SOCIAL_TOOL_NAMES = {"stage_tiktok_post", "stage_pinterest_post", "list_pinterest_boards"}

# Prompt-cache constants — built once at import time, reused every chat turn.
# _CEO_SYSTEM (~2 100 tokens) + AGENT_TOOLS (~2 000 tokens) are completely static
# between turns; marking them ephemeral saves ~90% on those tokens after the first
# turn in each 5-minute cache window (cache-read: $0.30/MTok vs full $3/MTok).
_CACHED_SYSTEM_BLOCK = {
    "type": "text",
    "text": _CEO_SYSTEM,
    "cache_control": {"type": "ephemeral"},
}


def _system_block() -> dict:
    """The cached system block, with the current agent/owner name applied. Identical
    text (so same cache key) unless a runtime rename happened."""
    return {
        "type": "text",
        "text": _localize_identity(_CEO_SYSTEM),
        "cache_control": {"type": "ephemeral"},
    }


def _tools_with_cache() -> list:
    """Return AGENT_TOOLS with cache_control on the last entry, and the current
    agent/owner name applied to descriptions (no-op unless renamed at runtime).
    The Anthropic API caches all tools up to and including the last entry that
    carries cache_control, so tagging only the last entry is sufficient."""
    tools = [
        {**t, "description": _localize_identity(t["description"])} if t.get("description") else t
        for t in AGENT_TOOLS
    ]
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
        # Playwright browser tools return JSON strings; parse to the dict contract here.
        if name in _BROWSER_TOOL_NAMES:
            return json.loads(_browser_automation.execute_tool(name, tool_input or {}))
        # Video understanding (watch_video) — same JSON-string → dict reconciliation.
        if name in _VIDEO_TOOL_NAMES:
            return json.loads(_video_understanding.execute_tool(name, tool_input or {}))
        # Etsy Ads — same JSON-string → dict reconciliation. DataStore() is a singleton
        # (tools/data_store.py), safe to instantiate fresh on every call.
        if name in _ETSY_ADS_TOOL_NAMES:
            from data_store import DataStore
            return json.loads(_etsy_ads_tools.execute_tool(name, tool_input or {}, DataStore()))
        if name == "stage_tiktok_post":
            return _stage_tiktok_post(tool_input or {})
        if name == "stage_pinterest_post":
            return _stage_pinterest_post(tool_input or {})
        if name == "list_pinterest_boards":
            return _list_pinterest_boards()
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
            if ti.get("description") is not None:
                payload["description"] = ti["description"]
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
            category = ((tool_input or {}).get("category") or "general").strip().lower()
            if category not in db.TODO_CATEGORIES:
                category = "general"
            todo_id = db.add_todo(text, added_by="frank", category=category)
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
        if name == "qc_check_product":
            return _qc_check_product(tool_input or {})
        if name == "generate_listing_photos":
            return _produce_listing_photos(tool_input or {})
        if name == "generate_print_zip":
            return _produce_print_zip(tool_input or {})
        if name == "build_planner":
            return _produce_build_planner(tool_input or {})
        if name == "build_sticker_pack":
            return _produce_build_sticker_pack(tool_input or {})
        if name == "build_product":
            return _produce_build_product(tool_input or {})
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
            import browser_agent
            url = (tool_input or {}).get("url", "")
            if not url.startswith("https://") and not url.startswith("http://"):
                return {"error": "URL must start with https://"}
            text = browser_agent.get_page_text(url)
            return {"url": url, "text": text, "chars": len(text)}
        if name == "search_etsy":
            import browser_agent
            query = (tool_input or {}).get("query", "")
            limit = min(int((tool_input or {}).get("limit", 10)), 20)
            results = browser_agent.search_etsy(query, limit)
            return {"query": query, "count": len(results), "results": results}
        if name == "check_listing_quality":
            import listing_qc
            return listing_qc.check_listing(
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
        dynamic_block = "\n\nListings:\n" + "\n".join(rows)
        if reason:
            dynamic_block += (
                "\n\nREVIEWER REJECTED THE PREVIOUS TAG SET WITH THIS FEEDBACK — "
                f"fix this specifically:\n{reason}"
            )

        msg = _anthropic_create(
            client,
            model=business_config.MODEL_CHEAP,
            max_tokens=8000,
            # _BATCH_TAG_PROMPT is a fixed template repeated on every batch (up to 40
            # listings/call) -- split it into its own cached block, same pattern as the
            # CEO chat path, so only the per-batch listing rows are ever sent uncached.
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": _BATCH_TAG_PROMPT, "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": dynamic_block},
                ],
            }],
        )

        raw = msg.content[0].text.strip()
        batch_results = _extract_json_object(raw)
        if batch_results is None:
            raise ValueError(f"Could not parse tag-generation response: {raw[:200]!r}")
        results.extend(batch_results)

    return results




# FRANK Command Center — Step 2 is wiring this shell to real data (Build Order
# step 2). Served at a separate path so the live dashboard above is never at risk
# while this is built out panel by panel. See frank_hud_mockup.py for details.
from frank_hud_mockup import render_frank_hud  # noqa: E402


# There was never a route for the bare domain root -- FastAPI's default 404
# fired a raw {"detail":"Not Found"} JSON blob for anyone who just typed the
# domain (Scott's screenshot, 2026-07-10). /frank already redirects an
# unauthenticated visitor on to /login?next=/frank, so this one route fixes
# both the bare-URL 404 and the "logged in with no explicit next" case (POST
# /login defaults next="/", which used to 404 the same way).
@app.get("/")
def root_redirect():
    return RedirectResponse("/frank", status_code=307)


@app.get("/frank", response_class=HTMLResponse)
def frank_hud_mockup(request: Request):
    if not _check_session(request):
        return RedirectResponse(f"/login?next={request.url.path}", status_code=307)
    return HTMLResponse(
        content=render_frank_hud(),
        # private: browser may cache but not CDN/proxies (session-gated page)
        # no-cache: must revalidate with server before using cached copy (session check happens)
        headers={"Cache-Control": "private, no-cache"},
    )


@app.get("/api/me")
async def get_me(request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """Return the username and role associated with the current session."""
    uname = _get_session_user(request)
    if not uname:
        return {"username": "", "role": ""}
    user_row = db.get_hub_user(uname)
    # Fail CLOSED: a session whose user row is gone (deleted/reset) is NOT an owner.
    # (Matches _require_owner, which already 403s that case — this just stops the UI
    # from briefly showing owner-only controls to a stale session.)
    role = user_row["role"] if user_row else ""
    return {"username": uname, "role": role}


def _require_owner(request: Request) -> None:
    """Raise 403 unless the current session belongs to an owner-role user."""
    uname = _get_session_user(request)
    if not uname:
        raise HTTPException(status_code=403, detail="Owner role required")
    user_row = db.get_hub_user(uname)
    if not user_row or user_row["role"] != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")


def _require_owner_or_automation(request: Request) -> None:
    """For endpoints with a legitimate machine-to-machine caller (CI workflows using
    the shared APP_SECRET_TOKEN as a bearer token) that ALSO must not be casually
    browsable by any logged-in admin session — highest-sensitivity data (e.g. raw
    Etsy OAuth tokens) is the motivating case. A request with no session cookie is
    treated as the accepted automation path (already gated by the bearer secret
    upstream in _auth_session_or_bearer); a request WITH a session cookie must
    belong to the owner specifically, closing the "any admin, including the
    tester account, can just load this URL in a browser" gap flagged in the
    2026-07-08 security review."""
    uname = _get_session_user(request)
    if not uname:
        return  # bearer-only (CI) call — accepted, unchanged from before
    user_row = db.get_hub_user(uname)
    if not user_row or user_row["role"] != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")


@app.get("/api/admin/users")
async def admin_list_users(request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """List all hub users (username, role, created_at). Owner only."""
    _require_owner(request)
    return {"users": db.list_hub_users()}


class _UserCreate(BaseModel):
    username: str
    password: str
    role: str = "admin"


@app.post("/api/admin/users")
async def admin_create_user(request: Request, body: _UserCreate, _token: str = Depends(_auth_session_or_bearer)):
    """Create a new hub user. Owner only. Role must be 'admin' (owner cannot be created here)."""
    _require_owner(request)
    uname = body.username.strip().lower()
    if not uname or not body.password.strip():
        raise HTTPException(status_code=400, detail="username and password are required")
    if len(body.password.strip()) < _MIN_PASSWORD_LEN:
        raise HTTPException(status_code=400, detail=f"Password must be at least {_MIN_PASSWORD_LEN} characters")
    if body.role not in ("admin", "owner"):
        raise HTTPException(status_code=400, detail="role must be 'admin'")
    if body.role == "owner":
        raise HTTPException(status_code=400, detail="Cannot create a second owner account")
    if db.get_hub_user(uname):
        raise HTTPException(status_code=409, detail=f"User '{uname}' already exists")
    recovery_code = _generate_recovery_code()
    db.create_hub_user(uname, _hash_password(body.password.strip()), role="admin",
                        recovery_code_hash=_hash_password(recovery_code))
    # Shown once, same as the setup-page flow — never stored or logged in plaintext.
    return {"ok": True, "username": uname, "role": "admin", "recovery_code": recovery_code}


class _PasswordReset(BaseModel):
    password: str


@app.post("/api/admin/users/{username}/reset-password")
async def admin_reset_password(username: str, request: Request, body: _PasswordReset, _token: str = Depends(_auth_session_or_bearer)):
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
    if len(body.password.strip()) < _MIN_PASSWORD_LEN:
        raise HTTPException(status_code=400, detail=f"Password must be at least {_MIN_PASSWORD_LEN} characters")
    db.update_hub_user_password(uname, _hash_password(body.password.strip()))
    # Fix B: invalidate all existing sessions for this user so a compromised
    # cookie can't be used after a password reset
    with _sessions_lock:
        to_remove = [sid for sid, (_, u) in _sessions.items() if u == uname]
        for sid in to_remove:
            del _sessions[sid]
    try:
        db.delete_sessions_for_user(uname)
    except Exception as exc:
        # This DB call is what makes a password reset actually revoke sessions that
        # survive a restart (the in-memory _sessions cleanup above only covers this
        # process's lifetime) -- silently swallowing a failure here would mean a
        # stale/compromised cookie could outlive the password change with zero trace
        # of why (2026-07-08 correction pass: previously bare `except Exception: pass`).
        print(f"[auth] delete_sessions_for_user({uname!r}) failed -- sessions may not be "
              f"fully revoked: {exc}", flush=True)
    return {"ok": True}


@app.delete("/api/admin/users/{username}")
async def admin_delete_user(username: str, request: Request, _token: str = Depends(_auth_session_or_bearer)):
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
    # Localize the PWA name to the current agent name (was hardcoded "FRANK").
    short = business_config.AGENT_NAME_SHORT
    m = {**_FRANK_MANIFEST,
         "name": f"{short} Command Center",
         "short_name": short,
         "description": f"{short} — {business_config.BUSINESS_NAME} CEO agent command center."}
    return JSONResponse(m, media_type="application/manifest+json")


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
    """Public diagnostic endpoint — no auth."""
    return {"ok": True, "build": _BUILD_ID}


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


        o7 = [o for o in orders if o.get("create_timestamp", 0) > now - 7 * day]
        o30 = [o for o in orders if o.get("create_timestamp", 0) > now - 30 * day]
        today_start = now - (now % day)  # midnight UTC
        o_today = [o for o in orders if o.get("create_timestamp", 0) > today_start]
        recent = sorted(orders, key=lambda o: o.get("create_timestamp", 0), reverse=True)[:5]
        recent_sales = []
        for o in recent:
            amount = _order_revenue([o])
            txns = o.get("transactions", [])
            title = txns[0].get("title", "") if txns else ""
            recent_sales.append({
                "amount": amount,
                "ts": o.get("create_timestamp", 0),
                "title": title[:40] if title else f"Order #{o.get('receipt_id', '?')}",
            })
        out["orders"] = {
            "last_7_days": len(o7),
            "last_30_days": len(o30),
            "revenue_7d": _order_revenue(o7),
            "revenue_30d": _order_revenue(o30),
            "all_time_count": len(orders),
            "all_time_revenue": _order_revenue(orders),
            "today_count": len(o_today),
            "today_revenue": _order_revenue(o_today),
            "recent_sales": recent_sales,
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

    # Cheap local read (no extra Etsy calls) so the Fix button in the Listings
    # tab can flag a listing that's still `active` on Etsy but has a real
    # content problem the last compliance sweep caught (e.g. zero files
    # attached) -- 2026-07-15: the button used to only appear for
    # state=='inactive' listings, so an active-but-broken listing had no way
    # to get fixed at all. Missing/unreadable manifest just means no listing
    # gets flagged this way -- never a hard failure of the listings view.
    manifest: dict = {}
    try:
        import listing_integrity_check as lic
        manifest = lic._load_json(lic.MANIFEST_PATH) or {}
    except Exception as exc:
        print(f"[listings] manifest_status merge skipped: {exc}", flush=True)

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
        listing_id = l.get("listing_id")
        manifest_status = manifest.get(str(listing_id), {}).get("last_status")
        listings.append(
            {
                "listing_id": listing_id,
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
                "manifest_status": manifest_status,
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
async def get_metrics(_token: str = Depends(_auth_session_or_bearer)):
    """Live business snapshot. 3 Etsy calls in parallel; result cached 60 s."""
    cached = _cache_get("metrics", ttl=60)
    if cached is not None:
        return cached

    async def _fetch():
        orders_r, reviews_r, shop_r = await asyncio.gather(
            asyncio.to_thread(lambda: EtsyAPIClient().get_orders(limit=100)),
            asyncio.to_thread(lambda: EtsyAPIClient().get_reviews(limit=50)),
            asyncio.to_thread(lambda: EtsyAPIClient().get_shop()),
            return_exceptions=True,
        )
        return _build_metrics(orders_r, reviews_r, shop_r)

    out = await _fetch_with_degrade("metrics", _fetch(), timeout=10.0)
    if not (isinstance(out, dict) and out.get("stale")):
        _cache_set("metrics", out)
    return out


@app.get("/api/inbox")
async def get_inbox(_token: str = Depends(_auth_session_or_bearer)):
    """Etsy inbox: unread messages + recent reviews. Cached 90s."""
    cached = _cache_get("inbox", ttl=90)
    if cached is not None:
        return cached

    def _fetch():
        client = EtsyAPIClient()
        now = int(time.time())
        msgs_r = reviews_r = None
        try:
            msgs_r = client.get_messages(limit=25)
        except Exception as exc:
            msgs_r = exc
        try:
            reviews_r = client.get_reviews(limit=3)
        except Exception as exc:
            reviews_r = exc

        out: dict = {"unread_count": 0, "oldest_unread_hours": None, "recent_reviews": []}

        if not isinstance(msgs_r, Exception):
            convs = msgs_r.get("results", [])
            unread = [c for c in convs if c.get("unread_count", 0) > 0 or c.get("unread", False)]
            out["unread_count"] = len(unread)
            if unread:
                timestamps = [c.get("last_update_timestamp") or c.get("create_timestamp", now) for c in unread]
                oldest_ts = min(t for t in timestamps if t)
                out["oldest_unread_hours"] = round((now - oldest_ts) / 3600, 1)
        else:
            out["messages_error"] = str(msgs_r)

        if not isinstance(reviews_r, Exception):
            for r in reviews_r.get("results", []):
                out["recent_reviews"].append({
                    "rating": r.get("rating", 0),
                    "text": (r.get("review") or "")[:120],
                    "date": r.get("create_timestamp", 0),
                })
        else:
            out["reviews_error"] = str(reviews_r)

        return out

    try:
        result = await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout")
    _cache_set("inbox", result)
    return result


def _compute_star_seller_status() -> dict:
    """Star Seller progress metrics against CLAUDE.md's own thresholds (5
    orders / $300 revenue / 0 unread messages over trailing 90 days).
    Factored out of get_star_seller() (2026-07-15) so both the live endpoint
    (Home screen display) and _check_star_seller_status() (the new proactive
    alert below) share one implementation instead of drifting apart."""
    client = EtsyAPIClient()
    now = int(time.time())
    ninety_days_ago = now - (90 * 86_400)

    orders_r = reviews_r = msgs_r = None
    try:
        orders_r = client.get_orders(limit=100)
    except Exception as exc:
        orders_r = exc
    try:
        reviews_r = client.get_reviews(limit=50)
    except Exception as exc:
        reviews_r = exc
    try:
        msgs_r = client.get_messages(limit=25)
    except Exception as exc:
        msgs_r = exc

    out: dict = {"orders_90d": 0, "revenue_90d": 0.0, "avg_rating": 0.0,
                 "review_count": 0, "unread_messages": 0, "on_time_pct": 100}

    if not isinstance(orders_r, Exception):
        orders = orders_r.get("results", [])
        o90 = [o for o in orders if o.get("create_timestamp", 0) > ninety_days_ago]

        out["orders_90d"] = len(o90)
        out["revenue_90d"] = _order_revenue(o90)

    if not isinstance(reviews_r, Exception):
        reviews = reviews_r.get("results", [])
        ratings = [r["rating"] for r in reviews if r.get("rating")]
        out["avg_rating"] = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
        out["review_count"] = len(ratings)

    if not isinstance(msgs_r, Exception):
        convs = msgs_r.get("results", [])
        out["unread_messages"] = sum(1 for c in convs if c.get("unread_count", 0) > 0 or c.get("unread", False))

    orders_ok = out["orders_90d"] >= 5
    revenue_ok = out["revenue_90d"] >= 300.0
    msgs_ok = out["unread_messages"] == 0
    if orders_ok and revenue_ok and msgs_ok:
        out["status"] = "on_track"
    elif not orders_ok or not revenue_ok:
        out["status"] = "building"
    else:
        out["status"] = "at_risk"

    return out


@app.get("/api/star-seller")
async def get_star_seller(_token: str = Depends(_auth_session_or_bearer)):
    """Star Seller progress metrics. Cached 120s."""
    cached = _cache_get("star_seller", ttl=120)
    if cached is not None:
        return cached

    result = await _fetch_with_degrade(
        "star_seller", asyncio.to_thread(_compute_star_seller_status), timeout=15.0
    )
    if not (isinstance(result, dict) and result.get("stale")):
        _cache_set("star_seller", result)
    return result


_STAR_SELLER_NUDGE_COOLDOWN_DAYS = 7


def _check_star_seller_status() -> str:
    """Proactive alert — 2026-07-15. get_star_seller()'s status computation
    already existed and is already displayed on the Home screen, but nothing
    proactively told Scott when it crossed into 'at_risk'; he'd only find out
    by opening Frank and looking. Read-only, same weekly-cooldown pattern
    _check_ads_thresholds() already uses so this nudges at most once a week,
    not every day the condition holds."""
    out = _compute_star_seller_status()
    if out.get("status") != "at_risk":
        return f"status={out.get('status')} — nothing to flag"

    today = date.today()
    last_nudge_str = db.get_setting("star_seller_at_risk_nudge_date")
    last_nudge = date.fromisoformat(last_nudge_str) if last_nudge_str else None
    if last_nudge and (today - last_nudge).days < _STAR_SELLER_NUDGE_COOLDOWN_DAYS:
        return "at_risk but nudged recently — skipping"

    db.add_todo(
        f"Star Seller status is at risk — {out['orders_90d']} orders / "
        f"${out['revenue_90d']:.2f} revenue over the trailing 90 days "
        f"(need 5 / $300), {out['unread_messages']} unread message(s). "
        f"Check Home for the full breakdown.",
        added_by="frank", category="question",
    )
    db.set_setting("star_seller_at_risk_nudge_date", today.isoformat())
    return "at_risk — todo added"


@app.get("/api/listings")
async def get_listings(state: str = "active", _token: str = Depends(_auth_session_or_bearer)):
    """Return listings with thumbnail URLs. Result cached 30 s."""
    if state not in ("active", "draft", "inactive"):
        raise HTTPException(status_code=400, detail="state must be active, draft, or inactive")

    def _fetch():
        data = _listings_sync(state)
        if state == "active":  # drafts/inactive can't have sales
            _enrich_sales(data.get("listings", []))
        return data

    return await _fetch_with_degrade(f"listings_{state}", asyncio.to_thread(_fetch), timeout=20.0)


def _shop_sections_sync() -> list[dict]:
    """Shop section (category) id → title map. Sections change rarely; cached 1h."""
    cached = _cache_get("shop_sections", ttl=3600)
    if cached is not None:
        return cached
    try:
        sections = EtsyAPIClient().get_shop_sections()
    except Exception as exc:  # never let a sections lookup break the listings view
        print(f"[sections] fetch failed: {exc}", flush=True)
        # 2026-07-10 fix: this used to fall through to `sections = []` and then
        # cache THAT for the full 1h TTL below -- one transient Etsy failure
        # silently blanked the Listings filter chips for up to an hour even
        # after Etsy recovered. Serve the last known-good sections instead
        # (and, critically, don't re-cache the failure) so the very next call
        # retries live rather than being stuck on a cached empty list.
        stale = _cache_get("shop_sections", ttl=float("inf"))
        return stale if stale is not None else []
    result = [
        {"shop_section_id": s.get("shop_section_id"), "title": s.get("title", "")}
        for s in sections
    ]
    _cache_set("shop_sections", result)
    return result


@app.get("/api/shop-sections")
async def shop_sections(_token: str = Depends(_auth_session_or_bearer)):
    """Shop sections (Etsy's listing categories) for the Listings filter chips."""
    sections = await _fetch_with_degrade("shop_sections", asyncio.to_thread(_shop_sections_sync), timeout=15.0)
    return {"sections": sections}


@app.get("/api/listings/{listing_id}/files")
async def listing_files(listing_id: int, _token: str = Depends(_auth_session_or_bearer)):
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
async def set_listing_state(listing_id: int, new_state: str, _token: str = Depends(_rate_limited_auth)):
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


def _etsy_fetch_suggestion(exc: Exception) -> str:
    """The Action Center card's 'suggestion' line for a failed Etsy fetch. Reuses
    the same classification background loops use (_classify_known_failure) so a
    credential problem gets the SPECIFIC remediation (which .env var, which
    console) instead of the generic 'check /api/ping' hint that doesn't tell
    Scott what to actually go do."""
    category = _classify_known_failure(exc)
    if category:
        return _KNOWN_FAILURE_REMEDIATIONS[category]
    return "Retry shortly; if it persists, check the Etsy connection on /api/ping."


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
            _etsy_fetch_suggestion(exc))
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
            _etsy_fetch_suggestion(exc))

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
async def get_actions(_token: str = Depends(_auth_session_or_bearer)):
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


_SNAPSHOT_BASE_INTERVAL = 86_400


async def _maybe_prune_after_snapshot(delay: float, base_interval: float) -> None:
    """Run the daily trash + rate-limit-log prune only when the snapshot
    iteration that just completed succeeded (delay == base_interval).
    _run_loop_iteration() returns exactly `base_interval` on success or a
    shorter jittered backoff delay (capped below base_interval) on failure —
    so this equality is an exact success test, not a heuristic. Before this
    gate existed, a failing/backing-off snapshot loop (e.g. Etsy down) would
    still run both prune passes on every retry, far more than the intended
    once/day. Tolerant of its own errors either way — a prune failure must
    never affect the snapshot loop's own success/backoff timing."""
    if delay != base_interval:
        return
    try:
        import trash as _trash
        n = await asyncio.to_thread(_trash.prune)
        if n:
            print(f"[trash] pruned {n} expired entr{'y' if n == 1 else 'ies'}", flush=True)
    except Exception as exc:
        print(f"[trash] prune error: {exc}", flush=True)
    try:
        n = await asyncio.to_thread(db.prune_rate_limit_log)
        if n:
            print(f"[rate-limit-log] pruned {n} sample(s) older than 30 days", flush=True)
    except Exception as exc:
        print(f"[rate-limit-log] prune error: {exc}", flush=True)


async def _snapshot_loop() -> None:
    """Snapshot at startup, then once every 24h (sooner on a backoff retry
    after a failure). Upsert-by-day means repeated runs on the same calendar
    day just refresh that day's row (no duplicates)."""
    while True:
        delay = await _run_loop_iteration(
            "snapshot", "Snapshot", _take_snapshot,
            on_success_detail="Daily metric snapshot recorded",
            base_interval=_SNAPSHOT_BASE_INTERVAL,
        )
        # Daily recycle-bin + rate-limit-log prune piggyback on this already-daily
        # loop so expiry is time-based and durable on the live server — no separate
        # cron needed. Gated to success-only, see _maybe_prune_after_snapshot().
        await _maybe_prune_after_snapshot(delay, _SNAPSHOT_BASE_INTERVAL)
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

    async def _iteration(first_run: bool):
        # Skip the actual (paid) refresh if nobody's viewed the dashboard since the
        # last one -- this used to fire every ~4h unconditionally, forever, purely to
        # keep a cache warm nobody might be reading (~6 guaranteed Sonnet calls/day
        # regardless of usage; see ops_runbook.md 2026-07-10). Always run on the very
        # first boot iteration so a fresh deploy still avoids the cold-cache spinner —
        # only later refreshes are conditional on GET /api/suggestions having fired
        # (see dashboard_last_viewed, set there) within the last TTL window.
        if not first_run:
            last_viewed = db.get_setting("dashboard_last_viewed")
            age = None
            if last_viewed:
                try:
                    age = (datetime.now(timezone.utc) - datetime.fromisoformat(last_viewed)).total_seconds()
                except ValueError:
                    age = None
            if age is None or age > _SUGGESTIONS_TTL:
                return {"skipped": True}
        res = await _compute_suggestions()
        if res.get("error") == "parse_failed":
            # Not cached (see _compute_suggestions) — a TransientToolError so the
            # shared helper backs off quickly and retries, rather than waiting the
            # full refresh-before-TTL interval.
            raise TransientToolError("suggestions parse failed")
        return res

    first_run = True
    while True:
        delay = await _run_loop_iteration(
            "suggestion_warmer", "Suggestion Warmer", lambda: _iteration(first_run),
            on_success_detail=lambda res: (
                "Skipped -- dashboard hasn't been viewed recently" if res.get("skipped")
                else "CEO diagnostic cache primed"
            ),
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
        first_run = False
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
    last_expiry_check: date | None = None

    def _check_refresh_token_staleness() -> str | None:
        """Etsy rotates the refresh token (and resets its 90-day clock) on
        every successful access-token refresh — so the real risk isn't a
        calendar countdown, it's auto-refresh having silently stopped working
        for a long time. `etsy_tokens.updated_at` already records the last
        successful rotation; if it's gone stale for ~75+ days (a safety
        margin before the true 90-day cliff), auto-refresh has been broken
        for long enough that Scott should know before a 401 surprises him.
        Checked once/day (guarded by last_expiry_check in the enclosing
        scope), not every 60s poll."""
        tokens = db.get_etsy_tokens()
        if not tokens or not tokens.get("updated_at"):
            return None
        try:
            updated_at = datetime.fromisoformat(tokens["updated_at"])
        except (ValueError, TypeError):
            return None
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        days_stale = (datetime.now(timezone.utc) - updated_at).days
        if days_stale >= 75:
            db.add_todo(
                f"Etsy OAuth token hasn't rotated in {days_stale} days — the refresh token "
                f"expires after 90 days of no successful refresh. Run `python tools/etsy_oauth.py` "
                f"to re-authorize before it expires and Etsy calls start failing with 401.",
                added_by="frank", category="scott_only",
            )
            return f"refresh token stale ({days_stale}d, re-authorize soon)"
        return None

    async def _iteration():
        nonlocal last_expiry_check
        cur_access = os.getenv("ETSY_ACCESS_TOKEN", "").strip()
        cur_refresh = os.getenv("ETSY_REFRESH_TOKEN", "").strip()
        rotated = False
        if cur_access and cur_refresh and (cur_access != last_tokens["access"] or cur_refresh != last_tokens["refresh"]):
            await asyncio.to_thread(db.save_etsy_tokens, cur_access, cur_refresh, last_tokens["refresh"])
            print(f"[etsy-tokens] persisted rotated token to {db.DB_PATH}", flush=True)
            last_tokens["access"], last_tokens["refresh"] = cur_access, cur_refresh
            rotated = True

        today = datetime.now(timezone.utc).date()
        staleness_note = None
        if today != last_expiry_check:
            last_expiry_check = today
            staleness_note = await asyncio.to_thread(_check_refresh_token_staleness)

        if rotated:
            return "Etsy token rotation persisted" + (f" — {staleness_note}" if staleness_note else "")
        return staleness_note or "watching for token rotation"

    await asyncio.sleep(60)  # give the app a moment before the first poll
    while True:
        delay = await _run_loop_iteration(
            "token_sync", "Token Sync", _iteration,
            on_success_detail=lambda detail: detail,
            base_interval=60,
            max_interval=300,
        )
        await asyncio.sleep(delay)


# Trailing FETCH_ERR group is optional so this still matches
# listing_integrity_check.py's older summary-line format (before the
# fetch-error/content-FAIL distinction was added); group(4) is None if absent.
_QUALITY_AUDIT_SUMMARY_RE = _re.compile(
    r"PASS:\s*(\d+).*?WARN:\s*(\d+).*?FAIL:\s*(\d+)(?:.*?FETCH_ERR:\s*(\d+))?", _re.DOTALL
)


def _parse_quality_audit_summary(out: str) -> tuple[int, int, int, int]:
    """Parse listing_integrity_check.py's stdout summary line into
    (passed, warned, failed, fetch_errors). fetch_errors is 0 if the
    FETCH_ERR token is absent (older script output). Raises RuntimeError if no
    summary line is found at all (the script crashed or its output format
    changed)."""
    m = _QUALITY_AUDIT_SUMMARY_RE.search(out)
    if not m:
        raise RuntimeError(f"could not parse summary line; script output: {out[:300]!r}")
    passed, warned, failed = (int(g) for g in m.groups()[:3])
    fetch_errors = int(m.group(4)) if m.group(4) else 0
    return passed, warned, failed, fetch_errors


def _quality_audit_skip_result(reason: str) -> dict:
    """Shared shape for _quality_audit_iteration()'s early-exit skip paths
    (manifest missing / manifest empty) — was a duplicated dict literal at two
    call sites a few lines apart."""
    return {"skipped": True, "passed": 0, "warned": 0, "failed": 0, "reason": reason}


_QUALITY_AUDIT_ROTATION_FRACTION = 3  # audit ~1/N of the catalog per run


def _select_quality_audit_ids(manifest: dict) -> list[str]:
    """Pick a rotating ~1/3 subset of the catalog to audit this run, prioritizing
    listings with the oldest (or missing) `last_verified` timestamp so every
    listing is covered at least once every _QUALITY_AUDIT_ROTATION_FRACTION runs,
    and a never-audited listing always goes first. 2026-07-10: replaces auditing
    the full catalog every run (~516 Etsy calls/day for 172 listings) as part of
    a daily-Etsy-volume reduction pass Scott requested — see ops_runbook.md."""
    ids = sorted(manifest.keys(), key=lambda lid: manifest[lid].get("last_verified") or "")
    subset_size = -(-len(ids) // _QUALITY_AUDIT_ROTATION_FRACTION)  # ceil division
    return ids[:subset_size]


async def _quality_audit_iteration() -> dict:
    """One run of the daily quality audit: rotate oversized KB files, run the
    read-only listing integrity check against a rotating ~1/3 subset of the
    catalog (see _select_quality_audit_ids), record the trend, and escalate a
    FAIL finding to ops_runbook.md. Raises on a genuine run failure (subprocess
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
        return _quality_audit_skip_result("listing_manifest.json not found — run build_manifest.py first")

    def _load_manifest_and_select_ids() -> list[str]:
        with open(manifest_path) as f:
            manifest = json.load(f)
        return _select_quality_audit_ids(manifest)

    audit_ids = await asyncio.to_thread(_load_manifest_and_select_ids)
    if not audit_ids:
        print("[quality-audit] skipping — listing_manifest.json is empty", flush=True)
        return _quality_audit_skip_result("listing_manifest.json has no listings")
    print(f"[quality-audit] auditing rotating subset: {len(audit_ids)} listing(s)", flush=True)

    result = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, str(ROOT / "tools" / "listing_integrity_check.py"),
         "--ids", ",".join(audit_ids)],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=str(ROOT),
    )
    out = (result.stdout or "") + "\n" + (result.stderr or "")
    passed, warned, failed, fetch_errors = _parse_quality_audit_summary(out)
    # Fetch errors (Etsy unreachable for a listing — network/breaker/429) are
    # counted in `failed` by listing_integrity_check.py so a human running the
    # CLI directly still sees a non-zero exit code, but they are NOT a content
    # problem with the listing. real_failed isolates the signal that should
    # actually escalate. Before this distinction existed, an Etsy outage during
    # the audit produced a false "N listing(s) failing" alarm into the CEO
    # agent's ops_runbook.md context (58/58 false FAILs, 2026-07-10 incident).
    real_failed = failed - fetch_errors
    blocks = out.split("—" * 70)
    header_idx = next((i for i, b in enumerate(blocks) if "✗ FAIL (" in b), None)
    fail_block = blocks[header_idx + 1] if header_idx is not None and header_idx + 1 < len(blocks) else ""
    summary = fail_block.strip()[:1500]
    try:
        db.record_quality_audit(passed, warned, failed, summary, audited_count=len(audit_ids))
    except Exception as exc:
        print(f"[quality-audit] db record failed: {exc}", flush=True)
    print(f"[quality-audit] PASS:{passed} WARN:{warned} FAIL:{failed} (FETCH_ERR:{fetch_errors})", flush=True)
    if real_failed > 0:
        _append_ops_runbook_entry(
            f"Automated quality audit — {real_failed} listing(s) failing",
            f"Daily listing_integrity_check found {real_failed} FAIL (content problem) / {warned} WARN "
            f"out of {passed + warned + failed} listings audited"
            + (f". {fetch_errors} additional listing(s) could not be reached on Etsy this run "
               f"(transient, not a content failure)" if fetch_errors else "")
            + f". Details:\n{summary or '(see logs)'}",
        )
    elif fetch_errors > 0:
        # 100% of the "failures" were Etsy fetch errors, not real content
        # problems — do NOT escalate the alarming "N listing(s) failing" entry
        # into the CEO agent's context. Just log it.
        print(f"[quality-audit] {fetch_errors} listing(s) could not be fetched from Etsy this "
              f"run (transient — no content failures found, not escalating)", flush=True)
    return {"passed": passed, "warned": warned, "failed": failed,
            "fetch_errors": fetch_errors, "real_failed": real_failed}


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
            on_success_status=lambda r: "warning" if r.get("skipped") else (
                "error" if r.get("real_failed", r["failed"]) > 0 else "ok"
            ),
            on_success_detail=lambda r: r.get("reason", (
                f"PASS:{r['passed']} WARN:{r['warned']} FAIL:{r['failed']}"
                + (f" ({r['fetch_errors']} fetch error(s), not content failures)"
                   if r.get('fetch_errors') else "")
            )),
            base_interval=86_400,
        )
        await asyncio.sleep(delay)


#   A tracked build stuck running past this is treated as hung and killed.
#   Every build_planner/build_sticker_pack/build_product run finishes in 2-10
#   min per their own docstrings; 15 min gives real headroom without letting a
#   wedged process sit untracked forever (2026-07-17 reliability audit finding
#   -- this used to have no ceiling at all).
_LONG_RUNNING_PROC_TIMEOUT_S = 15 * 60


async def _health_check_iteration() -> dict:
    """One health-check pass: reap finished background processes, ping Etsy +
    confirm the Anthropic key is set, and escalate to ops_runbook.md if either
    dependency is down. Etsy/Anthropic outages are content-level findings (an
    "error" heartbeat status) rather than loop failures, so they don't trigger
    `_run_loop_iteration`'s own retry backoff -- the check itself ran fine.

    2026-07-17: crashed/hung tracked builds used to be silently swallowed --
    reaped with only a server-stdout print(), no ops_runbook entry, no /api/alerts
    surfacing, and no timeout for a process that never exits at all. Now: a
    non-zero exit gets an ops_runbook entry + an agent_heartbeat row (which
    /api/alerts already knows how to surface, same mechanism the 5 real
    background loops use) so it's visible in the HUD, not just server logs; a
    clean exit clears any prior error heartbeat for that same build so a retry
    that succeeds doesn't leave a stale alert behind; and anything still running
    past _LONG_RUNNING_PROC_TIMEOUT_S gets killed and logged as hung."""
    for pid, (proc, cmd_name, started_at) in list(_LONG_RUNNING_PROCS.items()):
        age_s = (datetime.now(timezone.utc) - started_at).total_seconds()
        finished = proc.poll() is not None
        hung = not finished and age_s > _LONG_RUNNING_PROC_TIMEOUT_S
        if not finished and not hung:
            continue  # still running, within the normal window -- leave it tracked

        heartbeat_name = f"build:{cmd_name}"
        if hung:
            proc.kill()
            print(f"[health-check] killed HUNG {cmd_name} (pid {pid}, ran {age_s:.0f}s > "
                  f"{_LONG_RUNNING_PROC_TIMEOUT_S}s ceiling)", flush=True)
            detail = f"Killed after running {age_s:.0f}s, past the {_LONG_RUNNING_PROC_TIMEOUT_S}s ceiling."
            _append_ops_runbook_entry(
                f"Background build hung: {cmd_name}",
                f"5-minute health loop killed a stuck background build: {cmd_name} (pid {pid}). {detail}",
            )
            await asyncio.to_thread(db.set_agent_heartbeat, heartbeat_name, cmd_name, "error", detail)
        else:
            print(
                f"[health-check] reaped {cmd_name} (pid {pid}, ran {age_s:.0f}s, "
                f"exit={proc.returncode})",
                flush=True,
            )
            if proc.returncode != 0:
                detail = f"Exited {proc.returncode} after {age_s:.0f}s — see {cmd_name}'s own log for detail."
                _append_ops_runbook_entry(
                    f"Background build failed: {cmd_name}",
                    f"5-minute health loop reaped a failed background build: {cmd_name} (pid {pid}). {detail}",
                )
                await asyncio.to_thread(db.set_agent_heartbeat, heartbeat_name, cmd_name, "error", detail)
            else:
                await asyncio.to_thread(
                    db.set_agent_heartbeat, heartbeat_name, cmd_name, "ok",
                    f"Finished cleanly in {age_s:.0f}s.",
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

    # 2026-07-17 broadening (reliability audit): the check above only ever looked
    # at Etsy + Anthropic. These three are genuinely informational -- worth
    # surfacing, but deliberately NOT folded into all_ok/_escalate_failure, since
    # that would change _run_loop_iteration's retry-backoff behavior for
    # conditions that aren't "the health check itself failed" (same reasoning
    # the existing docstring already applies to Etsy/Anthropic outages).
    openai_ok = bool(os.getenv("OPENAI_API_KEY"))
    gemini_ok = bool(os.getenv("GEMINI_API_KEY"))
    if not openai_ok or not gemini_ok:
        missing = ", ".join(n for n, ok in (("OPENAI_API_KEY", openai_ok), ("GEMINI_API_KEY", gemini_ok)) if not ok)
        # Heartbeat only (no ops_runbook entry -- this would fire every hourly tick
        # otherwise, since a missing key doesn't self-resolve). "warn" when at least
        # one engine key is present deliberately does NOT surface via /api/alerts
        # (that only checks status=="error") -- Gemini is the default art engine
        # (gpt-image-1 is being retired 2026-10-23), so having Gemini but not
        # OpenAI is a reduced-choice state, not a broken one. Both missing does
        # alert, since that's a genuine "no art generation works at all" outage.
        await asyncio.to_thread(
            db.set_agent_heartbeat, "health:art_keys", "Art engine keys",
            "warn" if (openai_ok or gemini_ok) else "error",
            f"Missing: {missing}. At least one image-engine key should be set.",
        )
    else:
        await asyncio.to_thread(db.set_agent_heartbeat, "health:art_keys", "Art engine keys", "ok", "")

    volume_detail = "no volume configured (sandbox/local)"
    if "volume" in _FILE_ROOTS:
        vol = _FILE_ROOTS["volume"]
        try:
            vol.mkdir(parents=True, exist_ok=True)
            probe = vol / ".health_check_write_probe"
            probe.write_text(datetime.now(timezone.utc).isoformat())
            probe.unlink()
            volume_detail = "ok"
            await asyncio.to_thread(db.set_agent_heartbeat, "health:volume", "Durable volume", "ok", "")
        except Exception as exc:  # noqa: BLE001
            volume_detail = f"error: {str(exc)[:200]}"
            _append_ops_runbook_entry(
                "Durable volume not writable",
                f"5-minute health loop found {vol} mounted but not writable: {exc}. "
                f"Product files and backups may not be landing durably.",
            )
            await asyncio.to_thread(db.set_agent_heartbeat, "health:volume", "Durable volume", "error", volume_detail)

    # hub_db_state.json staleness -- only meaningful now that item 2 gives it a
    # real weekly cadence (_WEEKLY_MONITOR_SCRIPTS); this is exactly the kind of
    # check that would have caught it going a week stale BEFORE the fact instead
    # of after. Deliberately NOT checking backup_digital_products.py the same way
    # -- that backup is event-triggered (fires per-build, item 1), not time-based,
    # so "no backup in N days" just means "no build in N days," not a real problem.
    try:
        import backup_hub_db
        if backup_hub_db.OUT_PATH.exists():
            age_days = (time.time() - backup_hub_db.OUT_PATH.stat().st_mtime) / 86400
            if age_days > 10:
                _append_ops_runbook_entry(
                    "hub_db_state.json backup is stale",
                    f"5-minute health loop found the hub.db snapshot at {backup_hub_db.OUT_PATH} "
                    f"is {age_days:.1f} days old (expected weekly refresh via _WEEKLY_MONITOR_SCRIPTS).",
                )
                await asyncio.to_thread(
                    db.set_agent_heartbeat, "health:hub_db_backup", "hub_db backup freshness",
                    "error", f"{age_days:.1f} days old.",
                )
            else:
                await asyncio.to_thread(
                    db.set_agent_heartbeat, "health:hub_db_backup", "hub_db backup freshness",
                    "ok", f"{age_days:.1f} days old.",
                )
    except Exception:  # noqa: BLE001
        pass  # never let a staleness check break the health loop itself

    detail = (f"{detail} | OpenAI key: {openai_ok} | Gemini key: {gemini_ok} | "
              f"Volume: {volume_detail}")
    return {"all_ok": all_ok, "detail": detail[:400]}


async def _health_check_loop() -> None:
    """Every hour: confirm Etsy + Anthropic credentials are actually live (the
    same checks /api/ping exposes manually, run here on a timer so a regression
    surfaces in ops_runbook.md without anyone needing to remember to hit that URL),
    and reap any long_running background processes (coloring page generation, etc.)
    started via _run_exec_command so a finished/crashed child never sits untracked
    forever in _LONG_RUNNING_PROCS.

    2026-07-10: slowed from every 5 min (288 Etsy calls/day) to every hour (24/day)
    as part of a daily-Etsy-volume reduction pass (see ops_runbook.md) — this is a
    pure liveness heartbeat with no user-facing data, so an outage now surfaces
    within an hour instead of 5 minutes, a tradeoff Scott confirmed."""
    await asyncio.sleep(60)  # let the app finish booting first
    while True:
        delay = await _run_loop_iteration(
            "health_check", "Health Check", _health_check_iteration,
            on_success_status=lambda r: "ok" if r["all_ok"] else "error",
            on_success_detail=lambda r: r["detail"],
            base_interval=3600,
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
        # Purge expired sessions on every hourly tick
        try:
            db.purge_expired_sessions()
        except Exception:
            pass
        # Prune old executed/rejected action_queue rows so the table doesn't grow
        # unbounded (2026-07-08 performance pass).
        try:
            db.prune_old_actions()
        except Exception:
            pass
        now = datetime.now(timezone.utc)
        if now.hour == 6 and now.date() != last_sent_date:
            db.set_agent_heartbeat("daily_brief", "Daily Brief", "running", "generating brief")
            try:
                import daily_brief as _daily_brief
                result = await asyncio.to_thread(_daily_brief.run_daily_brief)
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


# ── Calendar-gated tasks: weekly monitors, monthly/seasonal checks, ads
#    threshold watch (2026-07-09 automation-loop pass) ───────────────────────
#
# All four sub-tasks below are read-only or notify-only — none write to Etsy,
# none message buyers, none spend money. Confirmed by direct read of each
# script before wiring them in here (see ops_runbook.md 2026-07-09 entry for
# the audit). Findings/recommendations are surfaced as todos (db.add_todo) for
# Scott to act on — nothing here bypasses the one-tap-approval pattern the
# rest of this system uses for anything that actually changes Etsy.

#   Every path in this list is a LIVE reference — if grepping tools/ for a
#   script's usage before deleting it, grep THIS FILE too, not just other
#   tools/ scripts. A 2026-07-11 "declutter" pass deleted
#   listing_performance_monitor.py / listing_drop_monitor.py / review_monitor.py
#   as "zero references," missing that this exact list had wired all three
#   in two days earlier (2026-07-09) — the weekly digest silently ran 4/7
#   scripts for days with the other 3 swallowed into generic "ERROR:" lines
#   nobody was alerted to. Restored 2026-07-15 from data/trash/ (ids
#   20260711-051/052/053) — see ops_runbook.md for the full incident.
_WEEKLY_MONITOR_SCRIPTS = [
    "weekly_report.py",
    "listing_performance_monitor.py",
    "listing_drop_monitor.py",
    "review_monitor.py",
    "order_notifier.py",
    # Stages tag fixes for approval (refactored 2026-07-09 — no longer writes
    # to Etsy directly, see the script's own module docstring). Fits CLAUDE.md's
    # stated trigger ("run after any batch of new listings") well enough on a
    # weekly cadence without needing a dedicated "batch just published" hook.
    "audit_fix_wall_art_tags.py",
    # Added 2026-07-15 after discovering DP1030-1034's source files existed
    # nowhere durable (not on disk, never published to Etsy) — this catches
    # both halves of that failure class (a live listing losing its attached
    # file, or a draft product's local files going missing) on a weekly
    # cadence instead of by accident. Purely read-only, see its own docstring.
    "check_digital_file_exposure.py",
    # Added 2026-07-17 (reliability audit): was only reachable via an
    # approval-gated _EXEC_COMMANDS entry, which is exactly how it went a week
    # stale. Writes the hub.db state snapshot itself (a local sqlite export,
    # not an HTTP call) — has to run server-side to see the real live data,
    # which is exactly what this weekly loop already does. Purely a write to
    # its own output file (durable-volume-aware as of this same change), never
    # touches Etsy/buyers.
    "backup_hub_db.py",
]

# Fixed 2026-07-09 (weakness audit): this set used to be built to match CLAUDE.md's
# documented table, but the table itself didn't match tools/seasonal_keywords.py's
# real computed/hardcoded `update_by` deadlines — 2 of the 4 dates fired AFTER their
# season's actual deadline (Back to School's real deadline is Jul 4, not "mid-July";
# Valentine's is ~Jan 3, not Jan 5), and 2 of the script's 6 seasons (Mother's Day,
# Teacher Appreciation) had no trigger at all. Each date below now sits a few days to
# two weeks BEFORE that season's real deadline (computed the same way
# seasonal_keywords.py's own _build_calendar()/_update_by() do) so the check always
# fires with room to act, never after the window has already closed:
#   Back to School   — deadline Jul 4   -> trigger Jun 20
#   Holiday/New Year — deadline Nov 8   -> trigger Oct 15 (already early, unchanged)
#   Valentine's      — deadline ~Jan 3  -> trigger Dec 28 (of the prior year)
#   Spring Reset     — deadline ~Feb 6  -> trigger Jan 15 (already early, unchanged)
#   Mother's Day     — deadline Mar 30  -> trigger Mar 20 (new)
#   Teacher Appreciation — deadline Mar 25 -> trigger Mar 15 (new)
_SEASONAL_TRIGGER_DATES = {
    (6, 20), (10, 15), (12, 28), (1, 15), (3, 20), (3, 15),
}

_ADS_KILL_SPEND_USD = 30.0
_ADS_KILL_ROAS = 1.5
_ADS_SCALE_ROAS = 4.0
_ADS_STALE_LOG_DAYS = 7
_ADS_MIN_DAYS_FOR_MONTHLY_VERDICT = 20  # ~30 days of logging before judging monthly ROAS


def _run_weekly_monitors() -> str:
    """Runs the previously-orphaned weekly monitor scripts and posts one
    digest todo + ops_runbook entry. Most were built for exactly this purpose
    (each script's own docstring describes a weekly cadence) but were never
    wired into any cron/loop after the dead tools/agents/business_pipeline.py
    orchestrator that was meant to run them got archived (task #204). Each
    script's own failure is isolated so one broken script doesn't hide the
    others' results. 600s timeout (not 300s) because audit_fix_wall_art_tags.py
    makes one Claude API call per flagged listing with a 0.5s rate-limit gap —
    slower than the other scripts on a shop with many wall art listings."""
    lines = []
    for script in _WEEKLY_MONITOR_SCRIPTS:
        try:
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools" / script)],
                capture_output=True, text=True, timeout=600, cwd=str(ROOT),
            )
            out = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
            tail = out[-600:] if out else "(no output)"
            lines.append(f"### {script}\n{tail}")
        except Exception as exc:
            lines.append(f"### {script}\nERROR: {exc}")
    digest = "\n\n".join(lines)
    db.add_todo(
        "Weekly monitor digest ready — see this week's ops_runbook entry for "
        "weekly_report / listing_performance / listing_drop / review / order_notifier / "
        "digital_file_exposure output.",
        added_by="frank", category="general",
    )
    _append_ops_runbook_entry("Weekly monitor digest", digest[:4000])
    return f"ran {len(_WEEKLY_MONITOR_SCRIPTS)} scripts"


def _run_monthly_shop_health() -> str:
    """Runs shop_health_check.py — already existed with a chat-triggerable
    button, but CLAUDE.md's own Monthly checklist still required a human to
    remember to run it on the 1st. Read-only report, no Etsy writes."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "shop_health_check.py")],
        capture_output=True, text=True, timeout=300, cwd=str(ROOT),
    )
    out = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    db.add_todo("Monthly shop health check ready — see this month's ops_runbook entry.", added_by="frank", category="general")
    _append_ops_runbook_entry("Monthly shop health check", out[:4000])
    return "ran shop_health_check.py"


def _run_art_authenticity_check() -> str:
    """Runs listing_integrity_check.py --full once a month — the cardinal
    "real product in every photo" check (check_art_in_photos) already existed
    and is correct, but was never actually executed shop-wide: every routine
    FAST-mode sweep skips it (it downloads + hashes every photo, too slow for
    a frequent pass), so the anti-mismatch guarantee silently never ran at
    all. Read-only against Etsy; the only write is a local
    listing_manifest.json timestamp/status stamp (see the script's own module
    docstring) — same safe pattern as the other calendar-gated tasks in this
    file. Monthly (not weekly) and a long 30-minute timeout, since a
    full-catalog photo download+hash pass is inherently slow; scheduled for
    the 15th so it doesn't compete with the 1st-of-month shop health check."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "listing_integrity_check.py"), "--full"],
        capture_output=True, text=True, timeout=1800, cwd=str(ROOT),
    )
    out = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    db.add_todo(
        "Monthly art-authenticity sweep ready — see this month's ops_runbook entry "
        "for any listing whose photos don't actually show the real product/file.",
        added_by="frank", category="question",
    )
    _append_ops_runbook_entry("Monthly art-authenticity sweep (--full)", out[:4000])
    return "ran listing_integrity_check.py --full"


def _run_seasonal_keyword_check() -> str:
    """Runs seasonal_keywords.py --dry-run only on the 4 documented calendar
    dates. The --push step (which actually edits live listings) stays a
    manual, explicit action per Autonomy Boundaries — this only ever surfaces
    the recommendation as a todo for Scott to review and push himself."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "seasonal_keywords.py"), "--dry-run"],
        capture_output=True, text=True, timeout=300, cwd=str(ROOT),
    )
    out = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    db.add_todo(
        "Seasonal keyword window is open — dry-run recommendation ready for your review "
        "(run `python tools/seasonal_keywords.py --push` yourself once you've checked it).",
        added_by="frank", category="scott_only",
    )
    _append_ops_runbook_entry("Seasonal keyword dry-run", out[:4000])
    return "ran seasonal_keywords.py --dry-run"


def _check_ads_thresholds() -> str:
    """Read-only: flags a todo if the manually-logged Etsy Ads spend data
    (tools/etsy_ads_tools.py's spend_log, via tools/data_store.py's DataStore)
    crosses one of CLAUDE.md's documented kill/scale thresholds, or if the log
    itself has gone stale. Etsy's public Open API v3 has no ads/campaign/stats
    endpoint for third-party apps, so there is no live ad-performance data to
    pull — this can only ever check whatever Scott has manually logged via
    _log_ad_spend, which is why the stale-log check exists alongside the
    threshold check (2026-07-09, confirmed with Scott before building this).
    Never touches ad spend/budgets itself — flags only."""
    from data_store import DataStore  # tools/ is on sys.path (line 56), not the repo root

    store = DataStore()
    ads_data = store.get("etsy_ads", default={})
    spend_log = ads_data.get("spend_log", [])
    if not spend_log:
        # Found in the 2026-07-09 weakness audit: this used to just return silently
        # forever if ads were never turned on at all, with no separate signal telling
        # Scott that Ads is an available, unused growth lever — the monitor was built
        # to watch spend that doesn't exist, not to flag its absence. Nudge at most
        # once per quarter (db.get_setting/set_setting, same key-value store the
        # Settings screen uses) so this doesn't spam a daily todo.
        today = date.today()
        last_nudge_str = db.get_setting("ads_never_used_nudge_date")
        last_nudge = date.fromisoformat(last_nudge_str) if last_nudge_str else None
        if last_nudge is None or (today - last_nudge).days >= 90:
            db.add_todo(
                "Etsy Ads has never been used — consider a small test budget "
                "(CLAUDE.md's Etsy Ads Strategy: $3-5/day starting budget, only once a "
                "listing has some organic proof of life). Low priority, your call.",
                added_by="frank", category="question",
            )
            db.set_setting("ads_never_used_nudge_date", today.isoformat())
            return "no ad spend logged yet — quarterly nudge added"
        return "no ad spend logged yet — nothing to check (nudged recently)"

    today = date.today()

    def _safe_date(s):
        try:
            return date.fromisoformat(s)
        except (ValueError, TypeError):
            return date(2000, 1, 1)

    latest_entry_date = max((_safe_date(e.get("date", "")) for e in spend_log), default=date(2000, 1, 1))
    days_since_log = (today - latest_entry_date).days
    notes = []

    if days_since_log >= _ADS_STALE_LOG_DAYS:
        db.add_todo(
            f"Etsy Ads spend hasn't been logged in {days_since_log} days — log this week's "
            f"numbers from Etsy Shop Manager → Marketing → Etsy Ads so this automated "
            f"threshold check has current data to work with.",
            added_by="frank", category="scott_only",
        )
        notes.append(f"stale log ({days_since_log}d)")

    week_cutoff = today - timedelta(days=7)
    week_entries = [e for e in spend_log if _safe_date(e.get("date", "")) >= week_cutoff]
    week_spend = sum(e.get("spend_usd", 0) for e in week_entries)
    week_revenue = sum(e.get("revenue_from_ads", 0) for e in week_entries)
    if week_spend >= _ADS_KILL_SPEND_USD and week_revenue == 0:
        db.add_todo(
            f"Etsy Ads: ${week_spend:.2f} spent this week with $0 revenue — this crosses your "
            f"own kill rule (spend≥$30 / 0 orders). Consider pausing in Shop Manager.",
            added_by="frank", category="question",
        )
        notes.append(f"kill-signal (${week_spend:.2f}/$0)")

    month_cutoff = today.replace(day=1)
    month_entries = [e for e in spend_log if _safe_date(e.get("date", "")) >= month_cutoff]
    month_spend = sum(e.get("spend_usd", 0) for e in month_entries)
    month_revenue = sum(e.get("revenue_from_ads", 0) for e in month_entries)
    month_roas = round(month_revenue / month_spend, 2) if month_spend > 0 else 0
    if len(month_entries) >= _ADS_MIN_DAYS_FOR_MONTHLY_VERDICT:
        if month_roas < _ADS_KILL_ROAS:
            db.add_todo(
                f"Etsy Ads: this month's ROAS is {month_roas}x, below your 1.5x kill threshold "
                f"after 30 days of data — consider pausing underperforming ads.",
                added_by="frank", category="question",
            )
            notes.append(f"low ROAS ({month_roas}x)")
        elif month_roas > _ADS_SCALE_ROAS:
            db.add_todo(
                f"Etsy Ads: this month's ROAS is {month_roas}x, above your 4x scale threshold — "
                f"consider raising budget 20-30% per your own strategy.",
                added_by="frank", category="question",
            )
            notes.append(f"scale-eligible ({month_roas}x)")

    return "checked: " + (", ".join(notes) if notes else "no thresholds crossed")


def _compute_ads_status() -> dict:
    """Structured Ads/ROAS snapshot for the Home screen card — 2026-07-15.
    _check_ads_thresholds() and tools/etsy_ads_tools.py already compute this
    correctly (matching CLAUDE.md's thresholds exactly) but only ever surface
    it as todos indistinguishable from any other todo — there was no
    dedicated "what's ads doing right now" UI read. Reuses the exact same
    week/month spend+revenue+ROAS windowing as _check_ads_thresholds() so the
    card and the proactive todo never disagree about what "this week" means;
    kept as a separate function since that one's job is flagging todos and
    this one's job is a point-in-time read for display."""
    from data_store import DataStore  # tools/ is on sys.path (line 56), not the repo root

    store = DataStore()
    ads_data = store.get("etsy_ads", default={})
    spend_log = ads_data.get("spend_log", [])
    if not spend_log:
        return {"used": False}

    today = date.today()

    def _safe_date(s):
        try:
            return date.fromisoformat(s)
        except (ValueError, TypeError):
            return date(2000, 1, 1)

    latest_entry_date = max((_safe_date(e.get("date", "")) for e in spend_log), default=date(2000, 1, 1))
    days_since_log = (today - latest_entry_date).days

    week_cutoff = today - timedelta(days=7)
    week_entries = [e for e in spend_log if _safe_date(e.get("date", "")) >= week_cutoff]
    week_spend = sum(e.get("spend_usd", 0) for e in week_entries)
    week_revenue = sum(e.get("revenue_from_ads", 0) for e in week_entries)

    month_cutoff = today.replace(day=1)
    month_entries = [e for e in spend_log if _safe_date(e.get("date", "")) >= month_cutoff]
    month_spend = sum(e.get("spend_usd", 0) for e in month_entries)
    month_revenue = sum(e.get("revenue_from_ads", 0) for e in month_entries)
    month_roas = round(month_revenue / month_spend, 2) if month_spend > 0 else 0.0
    have_monthly_verdict = len(month_entries) >= _ADS_MIN_DAYS_FOR_MONTHLY_VERDICT

    if week_spend >= _ADS_KILL_SPEND_USD and week_revenue == 0:
        status = "kill_signal"
    elif have_monthly_verdict and month_roas < _ADS_KILL_ROAS:
        status = "low_roas"
    elif have_monthly_verdict and month_roas > _ADS_SCALE_ROAS:
        status = "scale_eligible"
    elif days_since_log >= _ADS_STALE_LOG_DAYS:
        status = "stale_log"
    else:
        status = "ok"

    return {
        "used": True, "status": status,
        "week_spend": round(week_spend, 2), "week_revenue": round(week_revenue, 2),
        "month_spend": round(month_spend, 2), "month_revenue": round(month_revenue, 2),
        "month_roas": month_roas, "have_monthly_verdict": have_monthly_verdict,
        "days_since_log": days_since_log,
    }


@app.get("/api/ads-status")
async def get_ads_status(_token: str = Depends(_auth_session_or_bearer)):
    """Ads/ROAS snapshot for the Home screen card. Cached 120s (same TTL as
    Star Seller — this is manually-logged data, it doesn't change fast)."""
    cached = _cache_get("ads_status", ttl=120)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute_ads_status)
    _cache_set("ads_status", result)
    return result


def _run_scheduled_art_check() -> str:
    """Runs post_scheduled_art.py with no flags every day — the script's own
    main() already self-gates on data/art_schedule.json's next_post_date, so
    this just needs to run daily and let it decide whether today is actually
    its every-other-day turn. As of 2026-07-09 the script no longer publishes
    live on its own — it generates the listing as a draft, uploads photos/file,
    then stages a publish_listing action for approval (see the script's module
    docstring). This function only ever runs the generation step; the actual
    Etsy activation always waits for a human tap in the Action Center."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "post_scheduled_art.py")],
        capture_output=True, text=True, timeout=900, cwd=str(ROOT),
    )
    out = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    if "[SCHEDULED] Not due yet" in out or "[SCHEDULED] Not due" in out:
        return "not due today"
    _append_ops_runbook_entry("Scheduled art run", out[:3000])
    return "ran (see ops_runbook for output)"


async def _calendar_tasks_loop() -> None:
    """Hourly-tick calendar-gated loop (same shape as _daily_brief_loop) for
    tasks that fire on a specific day/date rather than a fixed interval:
    weekly monitor digest (Sunday), monthly shop health check (1st), seasonal
    keyword dry-run (4 documented dates), a daily Etsy Ads threshold check,
    and a daily scheduled-art check (the script's own every-other-day gating
    decides whether it actually does anything). Each sub-task tracks its own
    "last ran" date so a missed hour (deploy, restart) doesn't skip that day
    entirely — it just fires the next time the loop wakes up and the date
    still matches."""
    db.set_agent_heartbeat("calendar_tasks", "Calendar Tasks", "started", "waiting for next scheduled check")
    last_weekly: date | None = None
    last_monthly: date | None = None
    last_seasonal: date | None = None
    last_ads_check: date | None = None
    last_art_check: date | None = None
    last_art_authenticity: date | None = None
    last_star_seller_check: date | None = None
    while True:
        await asyncio.sleep(3600)
        now = datetime.now(timezone.utc)
        today = now.date()
        ran = []
        if now.weekday() == 6 and today != last_weekly:  # Sunday
            try:
                await asyncio.to_thread(_run_weekly_monitors)
                last_weekly = today
                ran.append("weekly-monitors")
            except Exception as exc:
                print(f"[calendar-tasks] weekly monitors error: {exc}", flush=True)
        if today.day == 1 and today != last_monthly:
            try:
                await asyncio.to_thread(_run_monthly_shop_health)
                last_monthly = today
                ran.append("monthly-shop-health")
            except Exception as exc:
                print(f"[calendar-tasks] monthly shop health error: {exc}", flush=True)
        if today.day == 15 and today != last_art_authenticity:
            try:
                await asyncio.to_thread(_run_art_authenticity_check)
                last_art_authenticity = today
                ran.append("art-authenticity")
            except Exception as exc:
                print(f"[calendar-tasks] art authenticity check error: {exc}", flush=True)
        if (today.month, today.day) in _SEASONAL_TRIGGER_DATES and today != last_seasonal:
            try:
                await asyncio.to_thread(_run_seasonal_keyword_check)
                last_seasonal = today
                ran.append("seasonal-keywords")
            except Exception as exc:
                print(f"[calendar-tasks] seasonal keyword check error: {exc}", flush=True)
        if today != last_ads_check:
            try:
                detail = await asyncio.to_thread(_check_ads_thresholds)
                last_ads_check = today
                ran.append(f"ads-check:{detail}")
            except Exception as exc:
                print(f"[calendar-tasks] ads threshold check error: {exc}", flush=True)
        if today != last_star_seller_check:
            try:
                detail = await asyncio.to_thread(_check_star_seller_status)
                last_star_seller_check = today
                ran.append(f"star-seller:{detail}")
            except Exception as exc:
                print(f"[calendar-tasks] star seller check error: {exc}", flush=True)
        if today != last_art_check:
            try:
                detail = await asyncio.to_thread(_run_scheduled_art_check)
                last_art_check = today
                ran.append(f"scheduled-art:{detail}")
            except Exception as exc:
                print(f"[calendar-tasks] scheduled art check error: {exc}", flush=True)
        db.set_agent_heartbeat(
            "calendar_tasks", "Calendar Tasks", "ok",
            "; ".join(ran) if ran else (
                f"no scheduled task due today (last: weekly={last_weekly}, "
                f"monthly={last_monthly}, seasonal={last_seasonal}, ads={last_ads_check}, "
                f"art={last_art_check}, art_authenticity={last_art_authenticity}, "
                f"star_seller={last_star_seller_check})"
            ),
        )


_AGENT_LOOP_LABELS = {
    "snapshot": "Snapshot",
    "suggestion_warmer": "Suggestion Warmer",
    "token_sync": "Token Sync",
    "quality_audit": "Quality Audit",
    "health_check": "Health Check",
    "daily_brief": "Daily Brief",
    "calendar_tasks": "Calendar Tasks",
}


@app.on_event("startup")
async def _startup() -> None:
    try:
        db.init_db()
        print(f"[db] ready at {db.DB_PATH} (persistent={db.is_persistent()})", flush=True)
        if not db.is_persistent():
            print(
                "[db] " + "!" * 60 + "\n"
                "[db] ⚠️  EPHEMERAL STORAGE — the database is NOT on a durable volume.\n"
                "[db]     Every restart/redeploy WIPES all data (todos, settings, login\n"
                "[db]     accounts, sessions, saved files, metric history, Etsy tokens).\n"
                "[db]     FIX: attach a Railway Volume mounted at /data (code auto-uses it).\n"
                "[db] " + "!" * 60,
                flush=True,
            )
    except Exception as exc:
        print(f"[db] init failed: {exc}", flush=True)
    # Purge any stale sessions left from previous server runs
    try:
        removed = db.purge_expired_sessions()
        if removed:
            print(f"[sessions] purged {removed} expired sessions at startup", flush=True)
    except Exception as exc:
        print(f"[sessions] startup purge failed: {exc}", flush=True)
    etsy_api.set_circuit_breaker_hook(CircuitBreaker("etsy_api", db_module=db))
    etsy_api.set_rate_limit_sample_hook(db.record_rate_limit_sample)
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
    asyncio.create_task(_calendar_tasks_loop())


@app.post("/api/calendar-tasks/run")
async def run_calendar_tasks_now(request: Request):
    """Manually trigger each calendar-gated task once, ignoring its normal date
    gate (for testing). Requires X-App-Token header. Read-only/notify-only —
    see _run_weekly_monitors/_run_monthly_shop_health/_run_seasonal_keyword_check/
    _check_ads_thresholds docstrings for exactly what each one does."""
    token = request.headers.get("X-App-Token", "")
    if not token or not secrets.compare_digest(token, APP_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized")
    results = {}
    for name, fn in [
        ("weekly_monitors", _run_weekly_monitors),
        ("monthly_shop_health", _run_monthly_shop_health),
        ("seasonal_keywords", _run_seasonal_keyword_check),
        ("ads_threshold", _check_ads_thresholds),
        ("scheduled_art", _run_scheduled_art_check),
        ("star_seller", _check_star_seller_status),
    ]:
        try:
            results[name] = await asyncio.to_thread(fn)
        except Exception as exc:
            results[name] = f"ERROR: {exc}"
    return results


@app.post("/api/brief/run")
async def run_brief_now(request: Request):
    """Manually trigger the daily brief (for testing). Requires X-App-Token header."""
    token = request.headers.get("X-App-Token", "")
    if not token or not secrets.compare_digest(token, APP_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized")
    import daily_brief as _daily_brief
    result = await asyncio.to_thread(_daily_brief.run_daily_brief)
    return {"status": result}


@app.get("/api/analytics")
async def get_analytics(days: int = 30, _token: str = Depends(_auth_session_or_bearer)):
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
        raise HTTPException(status_code=502, detail=f"Could not gather shop data: {str(exc)[:200]}")

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
                    model=business_config.MODEL_PRIMARY,
                    max_tokens=4000,  # 8 detailed suggestions overrun 2400 and truncate
                    # _SUGGESTIONS_SYSTEM is a fixed template -- cache it like the CEO chat
                    # path already does (main.py's _run_agent_turn). _ops_runbook_block()
                    # stays uncached: it changes too often across a session (many appends)
                    # for a 5-min ephemeral cache to realistically hit.
                    system=[
                        {"type": "text", "text": _SUGGESTIONS_SYSTEM, "cache_control": {"type": "ephemeral"}},
                        {"type": "text", "text": _ops_runbook_block()},
                    ],
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
async def get_suggestions(_token: str = Depends(_auth_session_or_bearer)):
    """CEO agent synthesises a structured JSON suggestion report from live shop
    data (metrics + active + draft listings). A background loop keeps the cache
    warm so this is normally an instant hit. If the cache IS cold (the ~75s window
    right after a deploy), we do NOT block the request for a full minute — that's
    what made the dashboard spinner look stuck. Instead we make sure a synthesis is
    running and return 202 'warming' immediately; the frontend polls until ready."""
    # This route firing IS "the dashboard was viewed" -- _warm_suggestions reads this
    # timestamp to skip its own refresh when nobody's actually looking, instead of
    # spending an Anthropic call every ~4h forever regardless of usage.
    await asyncio.to_thread(db.set_setting, "dashboard_last_viewed", datetime.now(timezone.utc).isoformat())
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
async def conversion_targets(_token: str = Depends(_auth_session_or_bearer)):
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
        raise HTTPException(status_code=502, detail=f"Etsy: {str(exc)[:200]}")

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
                    model=business_config.MODEL_CHEAP,
                    max_tokens=2000,
                    system=[
                        {"type": "text", "text": _CONVERSION_DOCTOR_SYSTEM, "cache_control": {"type": "ephemeral"}},
                    ],
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
async def diagnose_listing(listing_id: int, _token: str = Depends(_rate_limited_auth)):
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
        raise HTTPException(status_code=502, detail=f"Etsy: {str(exc)[:200]}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch listing {listing_id}: {str(exc)[:200]}")


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
                    model=business_config.MODEL_CHEAP,
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


# CLAUDE.md Gate 6 (wall art): "the first sentence of every wall art listing
# description must contain the primary keyword naturally and state that this
# is an instant/digital download." This exact sentence is the documented
# required-or-close-variant preamble.
_WALL_ART_GATE6_LINE = (
    "Instant download printable wall art — digital download delivered "
    "immediately after purchase, ready to print at home or at any print shop."
)


def _description_needs_gate6_fix(description: str) -> bool:
    """Mirrors tools/listing_qc.py's _check_wall_art description check (first
    200 chars must signal instant/digital download), plus CLAUDE.md's Gate 6
    'printable' requirement anywhere in the description."""
    text = description or ""
    first_200 = text[:200].lower()
    has_download_signal = "instant download" in first_200 or "digital" in first_200
    has_printable = "printable" in text.lower()
    return not (has_download_signal and has_printable)


async def _autofix_description_core(
    listing_id: int, listing: dict | None = None, reason: str = "", assume_wall_art: bool = False,
) -> dict:
    """Deterministic (no AI call) fix for CLAUDE.md's wall-art Gate 6 rule:
    prepend the exact mandated opening line when a description doesn't already
    signal instant/digital download + printable. Only applies to wall_art-type
    listings — other product types are skipped rather than force-fit with
    wall-art copy, since the required preamble is wall-art-specific.

    Product type is detected via listing_qc._detect_product_type(title,
    description), a title-keyword heuristic ("wall art" or "printable" in the
    title) that under-detects real wall-art listings whose titles read e.g.
    "X Art Print" with neither phrase (confirmed 2026-07-15 sweeping the live
    catalog: MISC_BOTANICAL_HERBS_ART_PRINT and several siblings misdetected
    as digital_planner). Pass assume_wall_art=True when the caller already
    knows the true category from a more authoritative source (e.g.
    product_catalog.json's `category` field) to bypass the heuristic.

    Never raises — returns {"error": str} on failure, {"skipped": True, ...}
    when the listing isn't wall_art or is already compliant, so a caller
    sweeping many listings can tell "nothing to do here" apart from a real
    failure."""
    if listing is None:
        listing = await _fetch_listing_for_autofix(listing_id)

    title = listing.get("title", "")
    description = listing.get("description", "") or ""

    if assume_wall_art:
        product_type = "wall_art"
    else:
        import listing_qc
        product_type = listing_qc._detect_product_type(title, description)
    if product_type != "wall_art":
        return {
            "skipped": True, "listing_id": listing_id,
            "reason": f"not a wall_art listing (detected: {product_type})",
        }
    if not _description_needs_gate6_fix(description):
        return {"skipped": True, "listing_id": listing_id, "reason": "already compliant"}

    new_description = _WALL_ART_GATE6_LINE + "\n\n" + description

    try:
        payload = {
            "listing_id": listing_id, "description": new_description,
            "before_description": description,  # display-only, for the Action Center diff view
            "_state_at_staging": listing.get("state"),
        }
        candidate = {"type": "update_description", "payload": payload}
        ok, msg = _validate_staged_action(candidate)
        if not ok:
            return {"error": f"Quality gate: {msg}", "listing_id": listing_id}

        title_short = (title or f"Listing {listing_id}")[:50]
        prefix = "Reject-fix description" if reason else "Auto description fix (Gate 6: instant download/printable)"
        summary = f"{prefix}: {title_short}"
        action_id = db.enqueue_action("update_description", summary, payload)
    except Exception as exc:
        return {"error": f"Could not stage description fix: {exc}", "listing_id": listing_id}

    with _cache_lock:
        _cache.pop("actions", None)

    return {"action_id": action_id, "listing_id": listing_id, "added_line": _WALL_ART_GATE6_LINE}


@app.post("/api/autofix/tags/{listing_id}")
async def autofix_tags(listing_id: int, _token: str = Depends(_rate_limited_auth)):
    """Generate 13 correct tags for one listing and stage an update_tags action.

    Calls Claude once for this specific listing, validates the tags through
    the quality gate, then enqueues the action for Scott's one-tap approval.
    Nothing touches Etsy until Scott taps Approve in the Action Center."""
    result = await _autofix_tags_core(listing_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return {"staged": True, **result}


@app.post("/api/autofix/title/{listing_id}")
async def autofix_title(listing_id: int, _token: str = Depends(_rate_limited_auth)):
    """Generate a corrected ≤70-char title and stage an update_title action.

    Calls Claude once with the listing's full context, validates through the
    quality gate (hard ≤70-char rule), then enqueues for Scott's approval.
    Nothing touches Etsy until Scott taps Approve in the Action Center."""
    result = await _autofix_title_core(listing_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return {"staged": True, **result}


@app.get("/api/listings/{listing_id}/gate6-check")
async def gate6_check(listing_id: int, assume_wall_art: bool = False, _token: str = Depends(_auth_session_or_bearer)):
    """Read-only: does this listing need the wall-art Gate 6 description fix?
    No AI call, no staging, no budget spent against _rate_limited_auth's
    shared 30/hour cap (unlike the POST autofix routes below) — safe to sweep
    across the whole catalog to scope a fix before staging anything real."""
    listing = await _fetch_listing_for_autofix(listing_id)
    title = listing.get("title", "")
    description = listing.get("description", "") or ""
    if assume_wall_art:
        product_type = "wall_art"
    else:
        import listing_qc
        product_type = listing_qc._detect_product_type(title, description)
    if product_type != "wall_art":
        return {"listing_id": listing_id, "needs_fix": False, "reason": f"not a wall_art listing (detected: {product_type})"}
    needs_fix = _description_needs_gate6_fix(description)
    return {
        "listing_id": listing_id, "needs_fix": needs_fix,
        "reason": "missing instant-download/printable signal" if needs_fix else "already compliant",
    }


@app.post("/api/autofix/description/{listing_id}")
async def autofix_description(listing_id: int, assume_wall_art: bool = False, _token: str = Depends(_rate_limited_auth)):
    """Deterministically fix a wall-art listing's missing CLAUDE.md Gate 6
    preamble ('instant download'/'printable') by prepending the exact
    mandated line, then stage an update_description action. No AI call — the
    fix text is fixed, so this can't drift or hallucinate over existing copy.
    Returns {"staged": False, "skipped": True, ...} for a non-wall-art or
    already-compliant listing instead of an error, so a caller sweeping many
    listings can distinguish "nothing to fix" from a real failure.
    Nothing touches Etsy until Scott taps Approve in the Action Center."""
    result = await _autofix_description_core(listing_id, assume_wall_art=assume_wall_art)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    if result.get("skipped"):
        return {"staged": False, **result}
    return {"staged": True, **result}


@app.post("/api/autofix/draft/{listing_id}")
async def autofix_draft(listing_id: int, _token: str = Depends(_rate_limited_auth)):
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


# Checks that _autofix_title_core/_autofix_tags_core can actually resolve by
# regenerating the field. Anything else (photo count, missing files, quantity-claim
# mismatch, etc.) needs a human, not a title/tag rewrite -- surfaced as a todo
# instead of a false "fixed" claim (CLAUDE.md's CARDINAL CHECK: never lie to the
# customer, which extends to never lying to Scott about what got fixed).
_TITLE_TAG_FIXABLE_CHECKS = {"title_length", "tag_count", "tag_length"}


@app.post("/api/listings/{listing_id}/request-fix")
async def request_listing_fix(listing_id: int, body: dict | None = None, _token: str = Depends(_rate_limited_auth)):
    """'Ask Frank to Fix' — triggered from the Deactivated tab's listing detail
    popup. Diagnoses the listing with the same single-listing quality-gate engine
    listing_compliance_sweep.py runs shop-wide (if it's manifest-mapped), folds
    that together with anything Scott typed in the popup, and reuses the existing
    autofix_draft() building blocks to stage a corrected title/tags. Always also
    stages a publish_listing (reactivation) action so approving the fix(es) is
    immediately followed by a one-tap republish -- but if the diagnosis found an
    issue outside title/tags (e.g. photo count), that gets called out in the
    republish action's own summary so Scott doesn't blindly reactivate something
    still broken, plus a todo is added either way."""
    instructions = ((body or {}).get("instructions") or "").strip()
    listing = await _fetch_listing_for_autofix(listing_id)

    diagnosis = ""
    unfixable_issues: list[dict] = []
    try:
        import listing_integrity_check as lic

        manifest = await asyncio.to_thread(lic._load_json, lic.MANIFEST_PATH)
        entry = manifest.get(str(listing_id))
        if entry:
            rules = await asyncio.to_thread(lic._load_json, lic.RULES_PATH)
            approvals = await asyncio.to_thread(lic._load_json, lic.APPROVALS_PATH)
            api = EtsyAPIClient()
            result = await asyncio.wait_for(
                asyncio.to_thread(lic.audit_listing, api, str(listing_id), entry, rules, approvals, {}, False),
                timeout=20.0,
            )
            issues = result.get("issues", [])
            fixable_details = [i["detail"] for i in issues if i["check"] in _TITLE_TAG_FIXABLE_CHECKS]
            unfixable_issues = [i for i in issues if i["check"] not in _TITLE_TAG_FIXABLE_CHECKS and i["severity"] == "FAIL"]
            if fixable_details:
                diagnosis = "Quality-gate found: " + "; ".join(fixable_details)
    except Exception as exc:
        print(f"[request-fix] diagnosis lookup failed for {listing_id}: {exc}", flush=True)

    reason = " ".join(p for p in (diagnosis, instructions) if p).strip()
    if not reason:
        reason = "This listing was deactivated. Review the title and tags for anything that could be wrong and improve them."

    staged: list[dict] = []
    errors: list[str] = []

    tag_result = await _autofix_tags_core(listing_id, listing=listing, reason=reason)
    if "error" in tag_result:
        errors.append(f"tags: {tag_result['error']}")
    else:
        staged.append({"type": "update_tags", "action_id": tag_result["action_id"]})

    title_result = await _autofix_title_core(listing_id, listing=listing, reason=reason)
    if "error" in title_result:
        errors.append(f"title: {title_result['error']}")
    else:
        staged.append({
            "type": "update_title",
            "action_id": title_result["action_id"],
            "title": title_result["title"],
        })

    title_short = (listing.get("title") or f"Listing {listing_id}")[:50]
    republish_summary = f"Republish listing {listing_id} after Frank's fix ({title_short})"
    if unfixable_issues:
        unresolved = "; ".join(i["detail"] for i in unfixable_issues)
        republish_summary += f" — ⚠️ NOT fully fixed, still needs: {unresolved}"
    republish_id = await asyncio.to_thread(
        db.enqueue_action,
        "publish_listing",
        republish_summary,
        {"listing_id": listing_id, "_state_at_staging": listing.get("state")},
    )
    staged.append({"type": "publish_listing", "action_id": republish_id})

    todo_id = None
    if unfixable_issues:
        detail_text = "; ".join(f"{i['check']}: {i['detail']}" for i in unfixable_issues)
        todo_id = await asyncio.to_thread(
            db.add_todo,
            f"Listing {listing_id} needs manual fix before republishing (not auto-fixable): {detail_text}",
            "frank", None, "scott_only",
        )

    return {
        "staged": staged,
        "staged_count": len(staged),
        "errors": errors,
        "unfixable_issues": [i["detail"] for i in unfixable_issues],
        "todo_id": todo_id,
        "listing_id": listing_id,
    }


@app.post("/api/snapshot")
async def post_snapshot(_token: str = Depends(_auth_session_or_bearer)):
    """Force-capture a snapshot now (useful for testing / on-demand recording)."""
    try:
        d = await asyncio.wait_for(_take_snapshot(), timeout=25.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    return {"recorded": d, "db": db.db_info()}


# ── Staged actions (agent prepares → Scott approves → server executes) ────────────

_ETSY_STAGED_ACTION_TYPES = (
    "update_tags", "update_title", "update_description", "publish_listing",
    "deactivate_listing", "toggle_listing_state",
)
_LOCAL_STAGED_ACTION_TYPES = ("local_write_file", "local_delete", "local_exec")
_SCRIPT_STAGED_ACTION_TYPES = ("run_script",)
_PHOTO_STAGED_ACTION_TYPES = ("listing_photo",)
_VIDEO_STAGED_ACTION_TYPES = ("listing_video",)
_REGISTER_COMMAND_STAGED_ACTION_TYPES = ("register_command",)
# First non-Etsy publish-type action (2026-07-09 tool audit) — tools/tiktok_poster.py
# was a real, working posting client only reachable via manual CLI (command_center.py),
# never Frank's chat agent. CLAUDE.md's Autonomy Boundaries lists "Post to social media
# accounts" as a Hard Stop, so this goes through the exact same stage→approve→execute
# path as every Etsy write instead of posting directly.
# post_pinterest added 2026-07-17, same reasoning, same pattern.
_SOCIAL_STAGED_ACTION_TYPES = ("post_tiktok", "post_pinterest")
_STAGED_ACTION_TYPES = (
    _ETSY_STAGED_ACTION_TYPES + _LOCAL_STAGED_ACTION_TYPES
    + _SCRIPT_STAGED_ACTION_TYPES + _PHOTO_STAGED_ACTION_TYPES
    + _VIDEO_STAGED_ACTION_TYPES + _REGISTER_COMMAND_STAGED_ACTION_TYPES
    + _SOCIAL_STAGED_ACTION_TYPES
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
        if t == "update_description":
            description = p.get("description")
            if not isinstance(description, str) or not description.strip():
                return False, "description is empty"
            if len(description) > 100_000:
                return False, f"description is {len(description)} chars — implausibly long, refusing"
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
    if t == "post_tiktok":
        path = (p.get("video_path") or "").strip()
        if not path:
            return False, "missing video_path"
        try:
            target = _resolve_in_root("staged_videos", path)
        except HTTPException:
            return False, f"path escapes the staged_videos root: {path}"
        if not target.is_file():
            return False, f"staged video file not found: {path}"
        if target.suffix.lower() != ".mp4":
            return False, "TikTok requires an .mp4 file"
        if target.stat().st_size > 50 * 1024 * 1024:
            return False, "video exceeds TikTok's 50MB upload limit"
        caption = (p.get("caption") or "").strip()
        if not caption:
            return False, "missing caption"
        if len(caption) > 2200:
            return False, f"caption is {len(caption)} chars — TikTok's limit is 2200"
        if at_approval and not os.getenv("TIKTOK_ACCESS_TOKEN", "").strip():
            return False, "TIKTOK_ACCESS_TOKEN not set — run tools/tiktok_oauth.py to (re)authorize"
        return True, "ok"
    if t == "post_pinterest":
        if not p.get("listing_id"):
            return False, "missing listing_id"
        board_name = (p.get("board_name") or "").strip()
        if not board_name:
            return False, "missing board_name"
        title = (p.get("title") or "").strip()
        if not title:
            return False, "missing title"
        if len(title) > 100:
            return False, f"title is {len(title)} chars — Pinterest's limit is 100"
        description = (p.get("description") or "").strip()
        if not description:
            return False, "missing description"
        if len(description) > 500:
            return False, f"description is {len(description)} chars — Pinterest's limit is 500"
        if at_approval and not os.getenv("PINTEREST_ACCESS_TOKEN", "").strip():
            return False, "PINTEREST_ACCESS_TOKEN not set — run tools/pinterest_oauth.py to (re)authorize"
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
    elif t == "update_description":
        res = _retry(lambda: client.update_listing(lid, {"description": p["description"]}))
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
        img = _retry(lambda: client.upload_listing_image(
            lid, str(abs_path), rank=p.get("rank", 1), alt_text=p.get("alt_text")
        ))
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
    if t in ("update_tags", "update_title", "update_description"):
        # Ranking Recovery cooldown tracker (2026-07-15) — record at EXECUTION
        # time (not staging time), since that's when the content actually
        # changed on Etsy. Read back by db.enqueue_action() to warn against
        # compounding edits inside the ~2-3 week recovery window.
        db.note_listing_edited(lid)
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


def _stage_tiktok_post(tool_input: dict) -> dict:
    """Chat-tool handler for stage_tiktok_post — validates and enqueues, never posts.
    The video must already be sitting in the staged_videos folder (same folder Etsy
    listing videos get staged from) by the time this is called."""
    video_path = (tool_input.get("video_path") or "").strip()
    caption = (tool_input.get("caption") or "").strip()
    if not video_path:
        return {"error": "missing video_path"}
    if not caption:
        return {"error": "missing caption"}
    payload = {"video_path": video_path, "caption": caption}
    candidate = {"type": "post_tiktok", "payload": payload}
    ok, msg = _validate_staged_action(candidate)
    if not ok:
        return {"error": msg}
    summary = f"TikTok post: {caption[:60]}"
    action_id = db.enqueue_action("post_tiktok", summary, payload)
    with _cache_lock:
        _cache.pop("actions", None)
    return {"action_id": action_id, "video_path": video_path, "caption": caption, "staged": True}


def _execute_tiktok_staged_action(a: dict) -> dict:
    """Apply an approved post_tiktok action — the ONLY place tiktok_poster.post_video()
    is ever called from this server. Everything upstream (staging, validation) only
    ever prepares the video/caption; nothing posts until Scott approves here. Logged
    to activity_log regardless of outcome, same as the local/script executors."""
    p = a.get("payload", {}) or {}
    video_path = _resolve_in_root("staged_videos", p["video_path"])
    caption = p["caption"]
    token = os.getenv("TIKTOK_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TIKTOK_ACCESS_TOKEN not set — run tools/tiktok_oauth.py to (re)authorize")
    import tiktok_poster as _tiktok_poster
    result = _tiktok_poster.post_video(str(video_path), caption, token)
    outcome = "error" if result.get("error") else "ok"
    db.log_activity("frank", "post_tiktok", a.get("summary", ""), p, outcome=outcome)
    if result.get("error"):
        raise RuntimeError(result["error"])
    return result


def _list_pinterest_boards() -> dict:
    """Read-only — no staging needed, same tier as any other read-only Etsy tool.
    Lets the agent (or Scott, via chat) see valid board_name values before staging
    a pin, and confirms Pinterest is actually connected at all."""
    import pinterest_api as _pinterest_api
    if not _pinterest_api.is_configured():
        return {"error": "Pinterest not connected — run tools/pinterest_oauth.py to (re)authorize"}
    try:
        boards = _pinterest_api.get_client().get_boards()
    except Exception as exc:  # noqa: BLE001
        return {"error": f"could not list boards: {exc}"}
    return {
        "boards": [
            {"name": b.get("name"), "id": b.get("id"), "pin_count": b.get("pin_count")}
            for b in boards
        ]
    }


def _stage_pinterest_post(tool_input: dict) -> dict:
    """Chat-tool handler for stage_pinterest_post — validates and enqueues, never
    posts. The listing must already be live on Etsy by the time this is called
    (that's what makes its photo have a public URL Pinterest can fetch)."""
    listing_id = tool_input.get("listing_id")
    board_name = (tool_input.get("board_name") or "").strip()
    title = (tool_input.get("title") or "").strip()
    description = (tool_input.get("description") or "").strip()
    if not listing_id:
        return {"error": "missing listing_id"}
    if not board_name:
        return {"error": "missing board_name"}
    if not title:
        return {"error": "missing title"}
    if not description:
        return {"error": "missing description"}
    payload = {"listing_id": listing_id, "board_name": board_name, "title": title, "description": description}
    candidate = {"type": "post_pinterest", "payload": payload}
    ok, msg = _validate_staged_action(candidate)
    if not ok:
        return {"error": msg}
    summary = f"Pinterest pin ({board_name}): {title[:60]}"
    action_id = db.enqueue_action("post_pinterest", summary, payload)
    with _cache_lock:
        _cache.pop("actions", None)
    return {"action_id": action_id, "listing_id": listing_id, "board_name": board_name, "title": title, "staged": True}


def _execute_pinterest_staged_action(a: dict) -> dict:
    """Apply an approved post_pinterest action — the ONLY place
    pinterest_api.PinterestClient.create_pin() is ever called from this server.
    Everything upstream only ever prepares/validates the pin; nothing posts until
    Scott approves here. Logged to activity_log regardless of outcome, same as the
    TikTok executor."""
    p = a.get("payload", {}) or {}
    listing_id = p["listing_id"]
    board_name = p["board_name"]
    title = p["title"]
    description = p["description"]
    token = os.getenv("PINTEREST_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("PINTEREST_ACCESS_TOKEN not set — run tools/pinterest_oauth.py to (re)authorize")

    # The pin image is the listing's own rank-1 Etsy photo — already public, no
    # need for Frank to host anything. Same selection tools/pinterest_batch_poster.py
    # used, but via the shared hardened EtsyAPIClient (retry/backoff/circuit-breaker)
    # instead of that script's own raw urllib call.
    images = EtsyAPIClient().get_listing_images(listing_id)
    if not images:
        raise RuntimeError(f"listing {listing_id} has no images to pin")
    images.sort(key=lambda img: img.get("rank", 99))
    top = images[0]
    image_url = top.get("url_fullxfull") or top.get("url_570xN") or top.get("url_75x75")
    if not image_url:
        raise RuntimeError(f"listing {listing_id}'s rank-1 image has no usable URL")

    import pinterest_api as _pinterest_api
    client = _pinterest_api.PinterestClient(access_token=token)
    board_id = client.get_board_id(board_name)
    if not board_id:
        created = client.create_board(board_name)
        board_id = created.get("id")
    if not board_id:
        raise RuntimeError(f"could not find or create Pinterest board '{board_name}'")

    # create_pin() raises PinterestAPIError on failure (unlike tiktok_poster.post_video(),
    # which returns an {"error": ...} dict) -- wrap so a failure still gets logged to
    # activity_log before propagating, matching the TikTok executor's "log regardless
    # of outcome" behavior despite the different underlying client shape.
    try:
        result = client.create_pin(
            board_id, title, description, image_url,
            link=f"https://www.etsy.com/listing/{listing_id}",
        )
    except Exception:
        db.log_activity("frank", "post_pinterest", a.get("summary", ""), p, outcome="error")
        raise
    db.log_activity("frank", "post_pinterest", a.get("summary", ""), p, outcome="ok")
    return result


@app.get("/api/queue")
async def get_queue(status: str = "pending", _token: str = Depends(_auth_session_or_bearer)):
    """List staged actions. status=pending (default) or 'all'."""
    st = None if status == "all" else status
    actions = await asyncio.to_thread(db.list_actions, st)
    return {"actions": actions, "count": len(actions)}


@app.post("/api/queue/{action_id}/approve")
async def approve_action(action_id: int, _token: str = Depends(_auth_session_or_bearer)):
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
    is_social = a["type"] in _SOCIAL_STAGED_ACTION_TYPES
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
        elif is_social:
            # Two social types share the _SOCIAL_STAGED_ACTION_TYPES/is_social bucket
            # (post_tiktok, post_pinterest as of 2026-07-17) but each needs its own
            # executor -- dispatch by the action's own type rather than assuming TikTok.
            _social_executor = (
                _execute_pinterest_staged_action if a["type"] == "post_pinterest"
                else _execute_tiktok_staged_action
            )
            result = await asyncio.wait_for(
                asyncio.to_thread(_social_executor, a), timeout=120.0
            )
        else:
            result = await asyncio.wait_for(asyncio.to_thread(_execute_staged_action, a), timeout=45.0)
    except Exception as exc:
        await asyncio.to_thread(db.set_action_status, action_id, "failed", {"error": str(exc)})
        raise HTTPException(status_code=502, detail=f"execution failed: {str(exc)[:200]}")
    await asyncio.to_thread(db.set_action_status, action_id, "executed", result)
    return {"status": "executed", "id": action_id, "result": result}


@app.post("/api/queue/{action_id}/reject")
async def reject_action(action_id: int, body: dict | None = None, _token: str = Depends(_auth_session_or_bearer)):
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
        elif t == "update_description":
            result = await _autofix_description_core(listing_id, reason=reason)
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
    import listing_photo_pipeline

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
        listing_photo_pipeline.generate_verified_photo, design_paths, scene_prompt, str(out_path), physics,
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
    _token: str = Depends(_auth_session_or_bearer),
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
    _token: str = Depends(_auth_session_or_bearer),
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
async def studio_upload_image(request: Request, filename: str, _token: str = Depends(_auth_session_or_bearer)):
    """Accept a raw image body and store it under studio_uploads/ so it can be picked
    for video generation. Same convention as /api/files/upload.

    Validates the body actually decodes as an image before storing it (mirrors
    upload_brand_mark's check) — this endpoint is documented as accepting photos, and
    without this check an uploaded .svg with an embedded <script> would be stored and,
    if later opened inline, execute same-origin under the viewer's session
    (2026-07-08 security review). The original bytes are stored as-is (not
    re-encoded) since downstream video generation needs the real file, not a
    PIL-normalized copy."""
    safe_name = os.path.basename((filename or "").strip())
    if not safe_name:
        raise HTTPException(status_code=400, detail="filename query param is required")
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="empty body")
    if len(body) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {_human_size(_MAX_UPLOAD_BYTES)} limit")
    from PIL import Image

    def _validate_and_store() -> Path:
        Image.open(io.BytesIO(body)).load()
        root = _FILE_ROOTS["studio_uploads"]
        root.mkdir(parents=True, exist_ok=True)
        out_path = root / f"{uuid.uuid4().hex[:8]}_{safe_name}"
        out_path.write_bytes(body)
        return out_path

    # PIL decode + disk write are synchronous/CPU-bound; run off the event loop
    # so a large upload doesn't stall every other concurrent request (2026-07-08).
    try:
        out_path = await asyncio.to_thread(_validate_and_store)
    except Exception:
        raise HTTPException(status_code=400, detail="not a readable image")
    return {"ok": True, "path": out_path.name, "size": len(body), "size_human": _human_size(len(body))}


@app.post("/api/studio/convert-svg")
async def studio_convert_svg(request: Request, mode: str = "color", _token: str = Depends(_auth_session_or_bearer)):
    """Trace a raw reference-photo body into an SVG (Studio "SVG Converter" tool).
    Same raw-body convention as /api/studio/upload-image. mode is 'color'|'bw'|'silhouette'.
    Always runs the real clean-vector quality check (the same one that gates SS-series
    ZIP uploads) on the result and returns it, so the caller sees an honest pass/fail
    rather than assuming a traced photo is print-ready."""
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="empty body")
    if len(body) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {_human_size(_MAX_UPLOAD_BYTES)} limit")

    import svg_converter

    try:
        svg_text = await asyncio.to_thread(svg_converter.convert_to_svg, body, mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"conversion failed: {str(exc)[:200]}")

    quality = etsy_api.check_svg_quality(svg_text)

    root = _FILE_ROOTS["svg_conversions"]
    root.mkdir(parents=True, exist_ok=True)
    out_name = f"{uuid.uuid4().hex[:8]}_{mode}.svg"
    (root / out_name).write_text(svg_text, encoding="utf-8")

    return {
        "ok": True,
        "path": out_name,
        "mode": mode,
        "quality": quality,
    }


@app.post("/api/studio/generate-lifestyle-photo")
async def studio_generate_lifestyle_photo(body: dict, _token: str = Depends(_rate_limited_auth)):
    """Generate a real, self-verified lifestyle photo from actual uploaded product
    file(s) — wraps tools/listing_photo_pipeline.generate_verified_photo(), THE
    STANDARD LIFESTYLE METHOD documented in CLAUDE.md: the real downloadable file is
    passed as the edit-source image (never an AI-invented stand-in), the render is
    verified against that source with a vision model, and a failing render is retried
    (never silently returned as if it passed). design_paths are filenames already
    uploaded via /api/studio/upload-image (relative to studio_uploads/) — upload the
    real product file(s) first, then call this."""
    import listing_photo_pipeline

    design_names = body.get("design_paths") or []
    category = (body.get("category") or "sign_flat").strip()
    scene_prompt = (body.get("scene_prompt") or "").strip()
    # Capped at 2 by default (not the pipeline's own 3) -- this is an interactive,
    # pay-per-call tool (real image-gen API cost per attempt), not an unattended batch
    # script; 2 attempts is a deliberate cost/quality tradeoff for that context.
    max_attempts = max(1, min(int(body.get("max_attempts") or 2), 3))

    if not design_names:
        raise HTTPException(status_code=400, detail="design_paths is required — upload at least one real product file first")
    if not scene_prompt:
        raise HTTPException(status_code=400, detail="scene_prompt is required")
    if category not in listing_photo_pipeline.PHYSICS:
        raise HTTPException(status_code=400, detail=f"unknown category {category!r}, expected one of {sorted(listing_photo_pipeline.PHYSICS)}")

    design_paths = []
    for n in design_names:
        p = _resolve_in_root("studio_uploads", n)
        if not p.is_file():
            raise HTTPException(status_code=400, detail=f"uploaded file not found: {n}")
        design_paths.append(p)

    out_root = _FILE_ROOTS["lifestyle_photos"]
    out_root.mkdir(parents=True, exist_ok=True)
    out_name = f"{uuid.uuid4().hex[:8]}_lifestyle.jpg"
    out_path = out_root / out_name

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                listing_photo_pipeline.generate_verified_photo,
                design_paths, scene_prompt, out_path, category, max_attempts,
            ),
            timeout=280,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Generation timed out — try again, or simplify the scene prompt")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"generation failed: {str(exc)[:200]}")

    # Distinguish a transient image-service error (Gemini/OpenAI 5xx, timeouts —
    # goal_loop records these as "generation error:" / "verification error:") from a
    # real product-mismatch rejection, so the UI can tell the user "try again" vs
    # "the render didn't match your file." Without this, both read as a match failure.
    _issues = result.issues or []
    _svc = _issues and all(
        str(i).startswith(("generation error:", "verification error:")) for i in _issues
    )
    failure_kind = None if result.passed else ("service_error" if _svc else "mismatch")

    return {
        "ok": result.passed,
        "path": out_name if result.passed else None,
        "attempts": result.attempts,
        "issues": result.issues,
        "failure_kind": failure_kind,
    }


# ── Produce — one-tap production pipelines (the deterministic work Claude does by
# hand, exposed as buttons + agent tools). These run local Python only — NO external
# API calls, so they cost nothing to run and work in a fully closed/offline deploy.
# First up: Quality Check (the same pre-publish gates in tools/qc_sweep.py). ──
def _qc_check_product(inp: dict) -> dict:
    """Run the pre-publish QC gates on one product's files and return a structured
    pass/warn/fail. Fully local, zero API cost, read-only — safe to call anytime."""
    pid = str((inp or {}).get("pid", "")).strip()
    if not pid:
        return {"error": "pid is required (e.g. 'DP1030')"}
    try:
        import qc_sweep
        rows = qc_sweep.sweep(pid)
    except Exception as exc:  # noqa: BLE001 — surface any pipeline error as JSON
        return {"error": f"QC sweep failed: {exc}"}
    n_fail = sum(1 for r in rows if r["severity"] == "FAIL")
    n_warn = sum(1 for r in rows if r["severity"] == "WARN")
    n_pass = sum(1 for r in rows if r["severity"] == "PASS")
    files = sorted({r["file"] for r in rows})
    verdict = ("no_files" if not rows else "fail" if n_fail else "warn" if n_warn else "pass")
    return {
        "pid": pid,
        "verdict": verdict,
        "summary": {"pass": n_pass, "warn": n_warn, "fail": n_fail, "files": len(files)},
        "rows": rows,
        "message": (f"No deliverable files found for {pid}." if not rows
                    else f"{pid}: {n_fail} FAIL · {n_warn} WARN · {n_pass} PASS "
                         f"across {len(files)} file(s)."),
    }


@app.post("/api/produce/qc-check")
async def produce_qc_check(body: dict, _token: str = Depends(_rate_limited_auth)):
    """One-tap Quality Check for a product's files (PDF page counts, sticker
    transparency + count, ZIP integrity, print-size folders). Local-only, no API cost."""
    return await asyncio.to_thread(_qc_check_product, body or {})


def _produce_listing_photos(inp: dict) -> dict:
    """Generate a planner's full 10-photo listing set from its built PDF — real
    rendered pages in device mockups (the cardinal 'photos must show the real
    product' rule). Pure local render; the only possible AI touch is the shared
    app-compatibility graphic, which is reused if present. Writes into the
    product's <pid>_listing_images/ folder."""
    pid = str((inp or {}).get("pid", "")).strip().upper()
    if not pid:
        return {"error": "pid is required (e.g. 'DP1030')"}
    engine, eng_err = _resolve_art_engine(inp)
    if eng_err:
        return {"error": eng_err}
    try:
        import gen_planner_listing_photos as glp
    except Exception as exc:  # noqa: BLE001
        return {"error": f"photo pipeline unavailable: {exc}"}
    if pid not in glp.PLANNER_PAGES:
        return {"error": f"{pid} isn't a configured planner "
                         f"(have {', '.join(sorted(glp.PLANNER_PAGES))})."}
    from pathlib import Path as _P
    if not (_P(glp.ART_DIR) / f"{pid}.pdf").exists():
        return {"error": f"{pid}.pdf not found in product files — build/sync the planner PDF first."}
    try:
        # Photos are local composites of real pages; the ONLY AI touch is photo 7
        # (the app-compat graphic) when the shared asset is absent — passed the engine.
        _out_dir, photos = glp.generate_for_planner(pid, None, upload=False, engine=engine)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"photo generation failed: {exc}"}
    return {
        "pid": pid,
        "count": len(photos),
        "photos": photos,
        "engine": engine,
        "folder": f"product_files/{pid}_listing_images",
        "message": f"Generated {len(photos)} listing photos for {pid} → "
                   f"{pid}_listing_images/. Open them from the Files screen.",
    }


@app.post("/api/produce/listing-photos")
async def produce_listing_photos(body: dict, _token: str = Depends(_rate_limited_auth)):
    """Generate a planner's 10-photo listing set from its built PDF (local render,
    effectively no API cost). Can take ~20-40s for the full set."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_produce_listing_photos, body or {}), timeout=200)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Photo generation timed out — try again.")


def _produce_print_zip(inp: dict) -> dict:
    """Build a wall-art product's multi-size print ZIP (4×6/8×12/12×18/16×24,
    8×10/16×20, A4/A3, square @300dpi, sRGB) from its source JPG. Pure local
    resize, zero API cost. Rejects lifestyle-composite sources (only raw art)."""
    pid = str((inp or {}).get("pid", "")).strip().upper()
    if not pid:
        return {"error": "pid is required (e.g. 'WA1030')"}
    try:
        import generate_print_sizes as gps
    except Exception as exc:  # noqa: BLE001
        return {"error": f"print-size pipeline unavailable: {exc}"}
    up = gps.UPSCALED_DIR / f"{pid}.jpg"
    base = gps.PRODUCT_FILES_DIR / f"{pid}.jpg"
    src = up if up.exists() else base
    if not src.exists():
        return {"error": f"No source art for {pid} — looked for {pid}.jpg in product_files/ and upscaled/."}
    try:
        gps.PRINT_ZIPS_DIR.mkdir(parents=True, exist_ok=True)
        res = gps.process_file(src, pid, force=True)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"print-ZIP generation failed: {exc}"}
    if res.get("status") == "error":
        return {"pid": pid, "error": res.get("error", "unknown error")}
    size_mb = res.get("size_mb")
    size_mb = round(size_mb, 1) if isinstance(size_mb, (int, float)) else None
    return {
        "pid": pid,
        "status": res.get("status"),
        "zip": f"print_zips/{pid}_print_sizes.zip",
        "size_mb": size_mb,
        "message": f"Built the multi-size print ZIP for {pid}"
                   + (f" ({size_mb} MB)" if size_mb is not None else "")
                   + " — open it from the Files screen.",
    }


@app.post("/api/produce/print-zip")
async def produce_print_zip(body: dict, _token: str = Depends(_rate_limited_auth)):
    """Build a wall-art product's multi-size print ZIP from its source JPG
    (local resize, no API cost). Can take ~15-40s for large art."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_produce_print_zip, body or {}), timeout=200)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Print-ZIP build timed out — try again.")


# Approved image engines (mirrors tools/image_gen.py). Gemini ("Nano Banana") is
# the default for the produce builders: it needs only GEMINI_API_KEY (no OpenAI
# dependency — and gpt-image-1 shuts down 2026-10-23), and is a fully approved
# engine per CLAUDE.md. gpt-image-2 / ideogram remain selectable.
_APPROVED_ART_ENGINES = ("gemini", "openai", "gpt-image-2", "ideogram")
_DEFAULT_ART_ENGINE = "gemini"


def _resolve_art_engine(inp: dict) -> tuple[str | None, str | None]:
    """(engine, error). Reads inp['engine'], defaults to Gemini, validates against
    the approved list. A blank/absent value → the default."""
    eng = str((inp or {}).get("engine", "")).strip().lower()
    if not eng:
        return _DEFAULT_ART_ENGINE, None
    if eng not in _APPROVED_ART_ENGINES:
        return None, (f"unknown art engine {eng!r} — "
                      f"choose one of {', '.join(_APPROVED_ART_ENGINES)}")
    return eng, None


def _subprocess_env_with_engine(engine: str | None) -> dict:
    """os.environ plus IMAGE_ENGINE, so a spawned builder renders art with the
    chosen engine instead of the server's default."""
    env = dict(os.environ)
    if engine:
        env["IMAGE_ENGINE"] = engine
    return env


def _produce_build_planner(inp: dict) -> dict:
    """Kick off a full planner build in the BACKGROUND (base dated + undated PDFs +
    AI cover → finalized PDFs with nav/fillable fields/embedded stickers) via
    tools/build_planner.py. Long-running (~2-4 min), so it runs detached and the
    finished PDFs show up in Files. The cover art is the only paid AI step.
    This is the one produce pipeline that spends money — priced into the SaaS
    subscription; it is never triggered automatically, only on a deliberate call."""
    pid = str((inp or {}).get("pid", "")).strip().upper()
    if not pid:
        return {"error": "pid is required (e.g. 'DP1030')"}
    engine, eng_err = _resolve_art_engine(inp)
    if eng_err:
        return {"error": eng_err}
    try:
        import generate_planner_v2 as _gpv2
        configured = set(getattr(_gpv2, "_ALL_V2_PIDS", []) or [])
    except Exception as exc:  # noqa: BLE001
        return {"error": f"planner builder unavailable: {exc}"}
    if configured and pid not in configured:
        return {"error": f"{pid} isn't a configured planner (have {', '.join(sorted(configured))})."}
    script = ROOT / "tools" / "build_planner.py"
    if not script.exists():
        return {"error": "build_planner.py is missing from this deploy."}
    # Log to the volume so a failed detached build is diagnosable in Files.
    from pathlib import Path as _P
    try:
        base = _P(os.getenv("HUB_FILES_DIR", "").strip()
                  or ("/data/files" if _P("/data/files").is_dir()
                      else str(ROOT / "data" / "digital_products")))
        logdir = base / "product_files"
        logdir.mkdir(parents=True, exist_ok=True)
        _logf = open(logdir / f"{pid}_build.log", "w")  # noqa: SIM115 — handed to Popen
    except Exception:  # noqa: BLE001
        _logf = subprocess.DEVNULL
    proc = subprocess.Popen(
        [sys.executable, str(script), pid],
        stdout=_logf, stderr=subprocess.STDOUT, cwd=str(ROOT),
        env=_subprocess_env_with_engine(engine),
    )
    _LONG_RUNNING_PROCS[proc.pid] = (proc, f"build_planner:{pid}", datetime.now(timezone.utc))
    return {
        "pid": pid,
        "started": True,
        "os_pid": proc.pid,
        "engine": engine,
        "message": f"Building {pid} in the background (~2-4 min) with {engine} cover art. "
                   f"When it finishes, {pid}.pdf and {pid}U.pdf appear in Files "
                   f"(and {pid}_build.log has the run output).",
    }


@app.post("/api/produce/build-planner")
async def produce_build_planner(body: dict, _token: str = Depends(_rate_limited_auth)):
    """Kick off a full planner build in the background (base PDFs + AI cover →
    finalized PDFs). Returns immediately; the PDFs appear in Files when done."""
    return await asyncio.to_thread(_produce_build_planner, body or {})


def _produce_build_sticker_pack(inp: dict) -> dict:
    """Kick off a full sticker-pack build in the BACKGROUND via
    tools/build_sticker_pack.py: generate the 9 themed sheets on a solid
    background (any engine), strip + segment + package into <PID>_sticker_pack.zip.
    Long-running (~2-4 min for 9 sheets), so it runs detached; the ZIP + processed
    sheets show up in Files when done. Sheet art is the only paid AI step.

    Reality check that keeps us honest (top rule — NEVER LIE TO THE CUSTOMER): the
    build reports a REAL measured sticker count, but AI can still garble in-image
    text, which no file gate catches. So this returns needs_visual_qc:true — the
    pack must be eyeballed before its count/claims go on a live listing."""
    pid = str((inp or {}).get("pid", "")).strip().upper()
    if not pid:
        return {"error": "pid is required (e.g. 'DP1030')"}
    engine, eng_err = _resolve_art_engine(inp)
    if eng_err:
        return {"error": eng_err}
    try:
        import build_sticker_pack as _bsp
        configured = set(getattr(_bsp, "SPEC_MODULES", {}) or {})
    except Exception as exc:  # noqa: BLE001
        return {"error": f"sticker-pack builder unavailable: {exc}"}
    if configured and pid not in configured:
        return {"error": f"{pid} has no sticker spec (have {', '.join(sorted(configured))})."}
    script = ROOT / "tools" / "build_sticker_pack.py"
    if not script.exists():
        return {"error": "build_sticker_pack.py is missing from this deploy."}
    sheets = inp.get("sheets")
    args = [sys.executable, str(script), pid]
    if isinstance(sheets, int) and sheets > 0:
        args += ["--sheets", str(sheets)]
    # Log to the volume so a failed detached build is diagnosable in Files.
    from pathlib import Path as _P
    try:
        base = _P(os.getenv("HUB_FILES_DIR", "").strip()
                  or ("/data/files" if _P("/data/files").is_dir()
                      else str(ROOT / "data" / "digital_products")))
        logdir = base / "product_files"
        logdir.mkdir(parents=True, exist_ok=True)
        _logf = open(logdir / f"{pid}_stickers_build.log", "w")  # noqa: SIM115 — handed to Popen
    except Exception:  # noqa: BLE001
        _logf = subprocess.DEVNULL
    proc = subprocess.Popen(
        args, stdout=_logf, stderr=subprocess.STDOUT, cwd=str(ROOT),
        env=_subprocess_env_with_engine(engine),
    )
    _LONG_RUNNING_PROCS[proc.pid] = (proc, f"build_sticker_pack:{pid}", datetime.now(timezone.utc))
    return {
        "pid": pid,
        "started": True,
        "os_pid": proc.pid,
        "engine": engine,
        "needs_visual_qc": True,
        "message": f"Building {pid}'s sticker pack in the background (~2-4 min) with {engine} "
                   f"sheet art. When it finishes, {pid}_sticker_pack.zip appears in Files "
                   f"({pid}_stickers_build.log has the run output). "
                   f"Eyeball the sheets for garbled text before the count goes on a live listing.",
    }


@app.post("/api/produce/build-sticker-pack")
async def produce_build_sticker_pack(body: dict, _token: str = Depends(_rate_limited_auth)):
    """Kick off a full sticker-pack build in the background (themed sheets → strip →
    segment → ZIP). Returns immediately; the pack appears in Files when done."""
    return await asyncio.to_thread(_produce_build_sticker_pack, body or {})


def _produce_build_product(inp: dict) -> dict:
    """Kick off a FULL product build in the BACKGROUND via tools/build_product.py:
    stickers → planner → listing photos → Quality Check, in that one correct order
    (stickers first so the planner embeds real library pages). ~6-10 min total, so
    it runs detached; the ZIP, PDFs, and photos land in Files as each step finishes.
    Publishing stays Scott-gated — this only produces + QCs the files.

    Same honesty guard as the sticker builder (top rule — NEVER LIE): returns
    needs_visual_qc:true. The chained QC verifies structure, but AI can garble
    in-image text, so the sheets + photos must be eyeballed before publish."""
    pid = str((inp or {}).get("pid", "")).strip().upper()
    if not pid:
        return {"error": "pid is required (e.g. 'DP1030')"}
    engine, eng_err = _resolve_art_engine(inp)
    if eng_err:
        return {"error": eng_err}
    # Must be buildable as a planner (the core deliverable). Sticker spec is optional
    # — build_product logs and continues if a step can't run.
    try:
        import generate_planner_v2 as _gpv2
        configured = set(getattr(_gpv2, "_ALL_V2_PIDS", []) or [])
    except Exception as exc:  # noqa: BLE001
        return {"error": f"product builder unavailable: {exc}"}
    if configured and pid not in configured:
        return {"error": f"{pid} isn't a configured planner (have {', '.join(sorted(configured))})."}
    script = ROOT / "tools" / "build_product.py"
    if not script.exists():
        return {"error": "build_product.py is missing from this deploy."}
    from pathlib import Path as _P
    try:
        base = _P(os.getenv("HUB_FILES_DIR", "").strip()
                  or ("/data/files" if _P("/data/files").is_dir()
                      else str(ROOT / "data" / "digital_products")))
        logdir = base / "product_files"
        logdir.mkdir(parents=True, exist_ok=True)
        _logf = open(logdir / f"{pid}_product_build.log", "w")  # noqa: SIM115 — handed to Popen
    except Exception:  # noqa: BLE001
        _logf = subprocess.DEVNULL
    proc = subprocess.Popen(
        [sys.executable, str(script), pid],
        stdout=_logf, stderr=subprocess.STDOUT, cwd=str(ROOT),
        env=_subprocess_env_with_engine(engine),
    )
    _LONG_RUNNING_PROCS[proc.pid] = (proc, f"build_product:{pid}", datetime.now(timezone.utc))
    return {
        "pid": pid,
        "started": True,
        "os_pid": proc.pid,
        "engine": engine,
        "needs_visual_qc": True,
        "steps": ["sticker pack", "planner PDFs", "listing photos", "quality check"],
        "message": f"Building the FULL {pid} product in the background (~6-10 min) with {engine} "
                   f"art: sticker pack → planner PDFs → 10 listing photos → Quality Check. "
                   f"Files land in Files as each step finishes ({pid}_product_build.log has the "
                   f"live run log + the final QC verdict). Nothing is published. Eyeball the "
                   f"sheets + photos for garbled text before it goes live.",
    }


@app.post("/api/produce/build-product")
async def produce_build_product(body: dict, _token: str = Depends(_rate_limited_auth)):
    """Kick off a full product build (stickers → planner → photos → QC) in the
    background. Returns immediately; deliverables appear in Files as they finish."""
    return await asyncio.to_thread(_produce_build_product, body or {})


@app.post("/api/studio/generate")
async def studio_generate_video(body: dict, _token: str = Depends(_rate_limited_auth)):
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
                    8, aspect_ratio, _lid,
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
        print(f"studio_generate_video error: {type(exc).__name__}: {exc}", flush=True)
        raise HTTPException(status_code=500, detail=f"Video generation failed: {type(exc).__name__}: {str(exc)[:200]}")

    return {
        "ok": True,
        "path": out_path.name,
        "size": out_path.stat().st_size,
        "size_human": _human_size(out_path.stat().st_size),
    }


@app.get("/api/studio/videos")
async def studio_list_videos(_token: str = Depends(_auth_session_or_bearer)):
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


_PRODUCT_FILES_PREFIX = "data/digital_products/"


def _build_products_status(catalog: list[dict], file_exists_fn) -> list[dict]:
    """Pure function (no I/O of its own) so this is directly unit-testable:
    given the full product catalog and a file-existence checker, compute
    per-product/per-file status. `file_exists_fn` takes the same `rel`
    convention _product_file_exists() and sync_files_to_hub.py already use
    (e.g. "product_files/DP1026.pdf") -- catalog entries store the fuller
    "data/digital_products/product_files/DP1026.pdf", so the shared prefix
    is stripped here rather than teaching the checker a second convention."""
    products = []
    for p in catalog:
        files = p.get("files", []) or []
        file_status = []
        for f in files:
            rel = f[len(_PRODUCT_FILES_PREFIX):] if f.startswith(_PRODUCT_FILES_PREFIX) else f
            file_status.append({"name": Path(f).name, "exists": file_exists_fn(rel)})
        products.append({
            "id": p.get("product_id"),
            "title": p.get("name", ""),
            "listing_id": p.get("etsy_listing_id"),
            "category": p.get("category", "uncategorized"),
            "status": p.get("status", "active"),
            "price": p.get("price"),
            "files": file_status,
            "all_files_present": all(fs["exists"] for fs in file_status) if file_status else None,
        })
    return products


@app.get("/api/products")
async def get_products(_token: str = Depends(_auth_session_or_bearer)):
    """Return the full product catalog (data/product_catalog.json — 176
    products across 14 categories as of 2026-07-15) with on-disk file
    status for every file each product actually lists.

    Rebuilt 2026-07-15: previously hardcoded to only DP1026-DP1035 (a
    legacy ~5-product slice from when the shop only had a handful of
    planners, sourced from data/dp_listing_map.json's narrow DP-numeric-
    range filter) — it never grew with the catalog, so it looked broken/
    incomplete once the shop reached 176 products across wall art, SVG
    packs, sticker packs, coloring pages, paper packs, and physical 3D
    prints. product_catalog.json is the shop's real source of truth and
    already carries a `files` list per product, so no new file-tracking
    convention was needed -- just a broader data source feeding the
    existing _product_file_exists() checker (see its own docstring for why
    a file can correctly show missing here even when it's safe on Scott's
    machine/in the repo: it hasn't been synced to the server's persistent
    volume via tools/sync_files_to_hub.py yet, an operational step, not a
    code bug)."""
    try:
        catalog = json.loads(Path("data/product_catalog.json").read_text())
    except OSError:
        catalog = []
    products = _build_products_status(catalog, _product_file_exists)
    return {"products": products}



@app.post("/api/studio/post-instagram")
async def studio_post_instagram(body: dict, _token: str = Depends(_rate_limited_auth)):
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
    ticket = _new_file_ticket("videos", video_name)
    video_url = f"{railway_url}/api/files/download?root=videos&path={video_name}&ticket={ticket}&inline=1"

    client = instagram_api.get_client()
    try:
        result = await asyncio.to_thread(client.post_video, video_url, caption, is_reel)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Instagram post failed: {str(exc)[:200]}")
    db.log_activity("frank", "post_instagram", f"Posted {video_name} to Instagram", body, outcome="ok")
    return {"ok": True, "result": result}


@app.post("/api/studio/post-facebook")
async def studio_post_facebook(body: dict, _token: str = Depends(_rate_limited_auth)):
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
    ticket = _new_file_ticket("videos", video_name)
    video_url = f"{railway_url}/api/files/download?root=videos&path={video_name}&ticket={ticket}&inline=1"

    client = facebook_api.get_client()
    try:
        result = await asyncio.to_thread(client.post_video, video_url, description, title)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Facebook post failed: {str(exc)[:200]}")
    db.log_activity("frank", "post_facebook", f"Posted {video_name} to Facebook", body, outcome="ok")
    return {"ok": True, "result": result}


# ── Batch tag fix (one Claude call → staged approvals for every under-tagged listing) ─


@app.post("/api/batch/stage-tags")
async def batch_stage_tags(_token: str = Depends(_rate_limited_auth)):
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
        raise HTTPException(status_code=502, detail=f"Tag generation returned invalid JSON: {str(exc)[:200]}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tag generation failed: {str(exc)[:200]}")

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
async def credentials_status(_token: str = Depends(_auth_session_or_bearer)):
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

    data = await _fetch_with_degrade("credentials_status", asyncio.to_thread(_check), timeout=12.0)
    if not (isinstance(data, dict) and data.get("stale")):
        _cache_set("credentials_status", data)
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
async def get_etsy_tokens_endpoint(request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """Current lineage-true Etsy token pair, for the CI workflow to sync against.
    Returns raw Etsy OAuth credentials — restricted to the automation (bearer-only)
    path this was built for, or the owner specifically if loaded from a browser
    session (2026-07-08 security review: was reachable by any admin session)."""
    _require_owner_or_automation(request)
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
async def post_etsy_tokens_endpoint(payload: dict, request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """Accept a freshly-rotated token pair (e.g. from the GitHub Actions workflow)
    and make it the lineage-true pair: persist to the durable DB and adopt it into
    this process's own os.environ immediately, so this server's next Etsy call
    uses the same token CI just minted instead of a now-invalidated one. Same
    automation-or-owner restriction as the GET above — an admin session
    overwriting live Etsy tokens is exactly as sensitive as reading them."""
    _require_owner_or_automation(request)
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


@app.post("/api/core/refresh-etsy-token")
async def core_refresh_etsy_token(request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """Force an Etsy access-token refresh right now, instead of waiting for the
    next natural 401 or the daily staleness check. Does NOT do a full OAuth
    re-authorization (that needs Scott's own browser via `python
    tools/etsy_oauth.py` — a new refresh token can't be minted server-side);
    this only exercises the existing refresh_token to mint a fresh access
    token, confirming the refresh token itself is still good. Same
    owner-or-automation gate as the raw token endpoints above, since success
    here rotates the live credential."""
    _require_owner_or_automation(request)
    ok = await asyncio.to_thread(lambda: EtsyAPIClient().refresh_access_token())
    if not ok:
        raise HTTPException(status_code=502, detail=(
            "Refresh failed -- if the refresh token itself has expired (90 days with no "
            "successful rotation), run `python tools/etsy_oauth.py` on your own machine to "
            "fully re-authorize."
        ))
    tokens = await asyncio.to_thread(db.get_etsy_tokens)
    return {"ok": True, "updated_at": (tokens or {}).get("updated_at")}


@app.get("/api/core/recent-errors")
async def core_recent_errors(limit: int = 20, _token: str = Depends(_auth_session_or_bearer)):
    """Last N activity_log entries whose outcome wasn't a clean "ok" -- the
    direct answer to "show me what's been failing" without digging through
    ops_runbook.md by hand. Scans a generous window (limit*10, capped) since
    errors are typically a small fraction of total activity."""
    limit = max(1, min(limit, 100))
    rows = await asyncio.to_thread(db.list_activity, limit * 10)
    errors = [r for r in rows if str(r.get("outcome", "")).strip().lower() not in ("ok", "")][:limit]
    return {"count": len(errors), "errors": errors}


@app.post("/api/core/redeploy")
async def core_redeploy(request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """Trigger a fresh Railway redeploy of this exact service — the in-app
    equivalent of clicking Redeploy in the Railway dashboard. Uses this
    service's own injected RAILWAY_API_TOKEN/RAILWAY_ENVIRONMENT_ID/
    RAILWAY_SERVICE_ID (standard Railway-provided env vars — confirmed
    present on this deployment 2026-07-15), so no extra credential setup is
    needed. Causes a brief real outage while the new instance starts —
    gated to the owner (or bearer/automation) same as other infra-sensitive
    routes; the frontend also confirms before calling this.

    Reuses _railway_graphql() (defined below, used by _railway_cost_snapshot)
    rather than a hand-rolled urllib call -- the first version of this
    endpoint used raw urllib.request directly and 403'd every time: Railway's
    API sits behind Cloudflare, which blocks the default python-urllib
    User-Agent (already documented in ops_runbook.md from an earlier
    incident). _railway_graphql uses `requests`, whose default User-Agent
    already passes fine -- confirmed live 2026-07-15 fixing this exact bug."""
    _require_owner_or_automation(request)
    env_id = os.getenv("RAILWAY_ENVIRONMENT_ID", "").strip()
    svc_id = os.getenv("RAILWAY_SERVICE_ID", "").strip()
    if not (os.getenv("RAILWAY_API_TOKEN", "").strip() and env_id and svc_id):
        raise HTTPException(status_code=501, detail="Railway API token/environment/service id not configured on this deployment")

    mutation = "mutation($e:String!,$s:String!){ serviceInstanceRedeploy(environmentId:$e, serviceId:$s) }"
    try:
        result = await asyncio.to_thread(_railway_graphql, mutation, {"e": env_id, "s": svc_id})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Railway API call failed: {exc}")
    if not result.get("serviceInstanceRedeploy"):
        raise HTTPException(status_code=502, detail=f"Railway did not confirm the redeploy: {result}")
    await asyncio.to_thread(db.log_activity, "scott", "redeploy", "Triggered via AI Core screen", None, outcome="ok")
    return {"ok": True}


@app.get("/api/account")
async def get_account_endpoint(_token: str = Depends(_auth_session_or_bearer)):
    """Single-row operator profile for the Settings 'My Account' card."""
    return await asyncio.to_thread(db.get_user_profile)


@app.post("/api/account")
async def post_account_endpoint(payload: dict, _token: str = Depends(_auth_session_or_bearer)):
    name = ((payload or {}).get("name") or "").strip() or None
    email = ((payload or {}).get("email") or "").strip() or None
    phone = ((payload or {}).get("phone") or "").strip() or None
    tz = ((payload or {}).get("timezone") or "").strip() or None
    return await asyncio.to_thread(db.save_user_profile, name, email, phone, tz)


class _SelfPasswordChange(BaseModel):
    current_password: str
    new_password: str


@app.post("/api/me/change-password")
async def change_my_password(body: _SelfPasswordChange, request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """Self-service password change for the logged-in user (owner or admin) — Settings
    'My Account' card. Requires a real browser session (not just a bearer token) since
    "my own password" only means something for an identified user, and verifies the
    current password before changing anything, unlike the owner-only admin reset-
    password endpoint this deliberately does not reuse."""
    uname = _get_session_user(request)
    if not uname:
        raise HTTPException(status_code=401, detail="Log in with your account to change your password")
    user_row = db.get_hub_user(uname)
    if not user_row:
        raise HTTPException(status_code=404, detail="Account not found")
    if not _verify_password(user_row["pw_hash"], body.current_password.strip()):
        raise HTTPException(status_code=403, detail="Current password is incorrect")
    new_pw = body.new_password.strip()
    if len(new_pw) < _MIN_PASSWORD_LEN:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    db.update_hub_user_password(uname, _hash_password(new_pw))
    # Same session-invalidation as the admin reset-password endpoint: kill every
    # session for this user (including the one making this request) so a stale
    # cookie can't outlive a password the owner just changed. The caller re-logs in.
    with _sessions_lock:
        to_remove = [sid for sid, (_, u) in _sessions.items() if u == uname]
        for sid in to_remove:
            del _sessions[sid]
    try:
        db.delete_sessions_for_user(uname)
    except Exception as exc:
        # This DB call is what makes a password reset actually revoke sessions that
        # survive a restart (the in-memory _sessions cleanup above only covers this
        # process's lifetime) -- silently swallowing a failure here would mean a
        # stale/compromised cookie could outlive the password change with zero trace
        # of why (2026-07-08 correction pass: previously bare `except Exception: pass`).
        print(f"[auth] delete_sessions_for_user({uname!r}) failed -- sessions may not be "
              f"fully revoked: {exc}", flush=True)
    return {"ok": True}


# ── Runtime settings (agent name + AI engines) — Settings screen ────────────────
_VIDEO_ENGINES = ("sora", "veo")
_IMAGE_ENGINES = ("openai", "gpt-image-2", "gemini", "ideogram")


def _effective_settings() -> dict:
    """Current effective values (stored override already applied to env/config) plus
    the option lists the Settings dropdowns render from."""
    return {
        "agent_name": business_config.AGENT_NAME_SHORT,
        "video_engine": os.getenv("AI_VIDEO_ENGINE", "sora").lower(),
        "image_engine": os.getenv("IMAGE_ENGINE", "openai").lower(),
        "image_model": os.getenv("IMAGE_MODEL", "gemini-2.5-flash-image"),
        "model_primary": business_config.MODEL_PRIMARY,
        "brand_mark_data_url": db.get_setting("brand_mark_data_url"),
        "options": {
            "video_engine": list(_VIDEO_ENGINES),
            "image_engine": list(_IMAGE_ENGINES),
        },
    }


@app.get("/api/settings")
async def get_settings_endpoint(_token: str = Depends(_auth_session_or_bearer)):
    return _effective_settings()


@app.post("/api/settings")
async def post_settings_endpoint(payload: dict, _token: str = Depends(_auth_session_or_bearer)):
    """Persist runtime overrides for the agent name + AI engines, then apply them
    live (env + business_config) and bust the HUD cache so the rename shows up."""
    payload = payload or {}

    if "agent_name" in payload:
        name = (payload.get("agent_name") or "").strip()
        if not name or len(name) > 40:
            raise HTTPException(status_code=400, detail="agent_name must be 1–40 characters")
        # One field renames both the everyday and full forms (drops the old full name).
        db.set_setting("agent_name", name)
        db.set_setting("agent_name_short", name)

    if "video_engine" in payload:
        v = (payload.get("video_engine") or "").lower().strip()
        if v not in _VIDEO_ENGINES:
            raise HTTPException(status_code=400, detail=f"video_engine must be one of {_VIDEO_ENGINES}")
        db.set_setting("video_engine", v)

    if "image_engine" in payload:
        v = (payload.get("image_engine") or "").lower().strip()
        if v not in _IMAGE_ENGINES:
            raise HTTPException(status_code=400, detail=f"image_engine must be one of {_IMAGE_ENGINES}")
        db.set_setting("image_engine", v)

    if "image_model" in payload:
        db.set_setting("image_model", (payload.get("image_model") or "").strip())

    if "model_primary" in payload:
        db.set_setting("model_primary", (payload.get("model_primary") or "").strip())

    if "brand_mark_data_url" in payload and payload.get("brand_mark_data_url") is None:
        # Clear only — setting a real value goes through POST /api/settings/brand-mark below
        # (needs PIL validation/resize), not this generic JSON endpoint.
        db.set_setting("brand_mark_data_url", None)

    _refresh_identity()   # re-sync env + business_config, bust HUD cache
    return {"ok": True, "settings": _effective_settings()}


_MAX_BRAND_MARK_UPLOAD_BYTES = 8 * 1024 * 1024  # stored as a DB text blob, not a disk file — tighter cap than _MAX_UPLOAD_BYTES
_BRAND_MARK_MAX_SIDE = 320  # matches the orb canvas's own coordinate scale (R=108 on a 300x300 canvas)


@app.post("/api/settings/brand-mark")
async def upload_brand_mark(request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """Upload a custom image (e.g. a logo) to replace the orb's default particle-sphere
    shape. Raw-body upload, same convention as /api/relay/upload and
    /api/studio/upload-image. Validates + downsizes with PIL, re-encodes as PNG (keeps
    alpha for the client-side particle sampler), stores as a data URL via the existing
    runtime-settings store — same persistence tier as agent_name/image_engine, not a
    separate mechanism."""
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="empty body")
    if len(body) > _MAX_BRAND_MARK_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {_human_size(_MAX_BRAND_MARK_UPLOAD_BYTES)} limit")
    from PIL import Image

    def _decode_resize_encode():
        img = Image.open(io.BytesIO(body))
        img.load()
        img = img.convert("RGBA")
        img.thumbnail((_BRAND_MARK_MAX_SIDE, _BRAND_MARK_MAX_SIDE), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), img.width, img.height

    # Decode + LANCZOS resample + re-encode is CPU-bound; run off the event loop
    # so a logo upload doesn't stall every other concurrent request (2026-07-08).
    try:
        png_bytes, width, height = await asyncio.to_thread(_decode_resize_encode)
    except Exception:
        raise HTTPException(status_code=400, detail="not a readable image")
    data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
    db.set_setting("brand_mark_data_url", data_url)
    await asyncio.to_thread(db.log_activity, "scott", "brand_mark_upload", None, None, "ok")
    return {"ok": True, "data_url": data_url, "width": width, "height": height}


# ── Local Relay — status, kill switch, Allowed Folders ──────────────────────────


@app.get("/api/relay/status")
async def get_relay_status(_token: str = Depends(_auth_session_or_bearer)):
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
async def get_agents_status(_token: str = Depends(_auth_session_or_bearer)):
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


def _capability_report() -> list:
    """Availability of the optional capabilities that need a key/connection, so the
    HUD (and anyone testing) sees what's Ready vs Needs-setup instead of discovering
    it by trial-and-error. Reports booleans + a fix hint only — never a key VALUE."""
    gemini_ok = bool(os.getenv("GEMINI_API_KEY"))
    gemini_hint = None if gemini_ok else "needs GEMINI_API_KEY"

    # Browser: Playwright importable (Chromium is bundled in the image after
    # `playwright install`). is_available() is import-only, so it's cheap + safe.
    try:
        browser_ok = _browser_automation.is_available()
    except Exception:
        browser_ok = False
    browser_hint = None if browser_ok else "browser not installed in this image"

    # Video understanding needs BOTH the Gemini SDK and the key.
    try:
        video_ok = _video_understanding.is_available()
    except Exception:
        video_ok = False
    video_hint = None if video_ok else "needs GEMINI_API_KEY"

    # Relay: online only when connected and not kill-switched.
    try:
        rstate = db.get_relay_state()
        connected = _relay_ws is not None
        killed = bool(rstate.get("killed"))
        relay_ok = connected and not killed
        relay_hint = None if relay_ok else ("kill switch engaged" if killed else "relay offline — not connected")
    except Exception:
        relay_ok, relay_hint = False, "relay status unavailable"

    return [
        {"key": "video_understanding", "label": "Video analysis (watch_video)", "available": video_ok, "hint": video_hint},
        {"key": "image_engine_gemini", "label": "Gemini image engine (Nano Banana)", "available": gemini_ok, "hint": gemini_hint},
        {"key": "image_engine_gpt2", "label": "gpt-image-2 (no transparent bg)", "available": bool(OPENAI_KEY), "hint": None if OPENAI_KEY else "needs OPENAI_API_KEY"},
        {"key": "browser", "label": "Web browser (render/screenshot)", "available": browser_ok, "hint": browser_hint},
        {"key": "relay", "label": "Local relay (your PC)", "available": relay_ok, "hint": relay_hint},
    ]


@app.get("/api/system/dependencies")
async def get_system_dependencies(_token: str = Depends(_auth_session_or_bearer)):
    """Live circuit-breaker status for every tracked external dependency, plus a
    `capabilities` list (optional features that need a key/connection) — backs the
    HUD's Dependency Health panel. Replaced the old System Monitor CPU/RAM/DISK
    gauges, which were hardcoded CSS with zero backend. A dependency with no DB row
    yet has never tripped, so it reports the same default CircuitBreaker._load()
    uses: closed, 0 failures."""
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
    capabilities = await asyncio.to_thread(_capability_report)
    return {"dependencies": deps, "capabilities": capabilities}


@app.post("/api/system/recheck-credentials")
async def recheck_credentials(_token: str = Depends(_auth_session_or_bearer)):
    """Force an immediate Etsy + Anthropic credential check instead of waiting up to
    an hour for the next _health_check_loop tick -- lets Scott confirm a credential
    rotation actually worked right away (2026-07-08 correction pass). Reuses
    _health_check_iteration() exactly, so this is the same real Etsy API call
    (get_shop()) the background loop already makes, not a separate probe -- the
    circuit breaker updates as a normal side effect of that call via etsy_api.py's
    existing _circuit_breaker_hook, so the Dependency Health panel reflects the
    result immediately too."""
    result = await _health_check_iteration()
    return result


@app.get("/api/alerts")
async def get_alerts(_token: str = Depends(_auth_session_or_bearer)):
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

    # 2026-07-17 (reliability audit): the Etsy Client ID/Secret leak (flagged
    # 2026-06-26) and the TikTok credential leak (flagged 2026-07-09) were both
    # still confirmed unrotated as of the most recent full audit -- weeks open,
    # only ever surfaced as a one-off todo Scott could dismiss/scroll past once.
    # Neither can be fixed by Frank (rotation happens in Etsy's/TikTok's own
    # developer consoles, outside anything Frank can reach), so instead of a
    # dismissible reminder this is a STANDING alert: present every session until
    # explicitly resolved. Gated by a settings flag (not hardcoded forever) so
    # clearing it once Scott confirms rotation is a one-line db.set_setting()
    # call, not a code change -- see tools/api_server/db.py's get_setting/
    # set_setting. Two independent flags since the two credentials may get
    # rotated at different times.
    if not await asyncio.to_thread(db.get_setting, "etsy_credential_leak_resolved"):
        alerts.append({
            "severity": "critical",
            "source": "credential_leak",
            "title": "Etsy Client ID/Secret leaked — still unrotated",
            "detail": "Leaked via a pushed branch, flagged 2026-06-26. Rotate at the Etsy "
                      "Developer Console, update .env, then re-run python tools/etsy_oauth.py. "
                      "This alert clears once confirmed done.",
        })
    if not await asyncio.to_thread(db.get_setting, "tiktok_credential_leak_resolved"):
        alerts.append({
            "severity": "critical",
            "source": "credential_leak",
            "title": "TikTok Client Key/Secret leaked — still unrotated",
            "detail": "Leaked and flagged 2026-07-09. Generate NEW credentials at the TikTok "
                      "developer console (don't reuse the old ones), update .env. This alert "
                      "clears once confirmed done.",
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

    # API cost budget caps (Settings -> API Costs). Only checked for services
    # with a live cost figure available (Railway today) -- a cap saved for a
    # service Frank can't yet pull real spend for (Anthropic/OpenAI/Gemini,
    # pending their Admin keys) has nothing to compare against, so it's silently
    # skipped here rather than firing a false/meaningless alert.
    try:
        costs = await asyncio.to_thread(_all_service_costs)
        for svc, info in costs["services"].items():
            if not info.get("available"):
                continue
            cap = costs["budget_caps"].get(svc)
            if cap is None:
                continue
            spend = info.get("estimated_cost_usd")
            if spend is None:
                continue
            pct = (spend / cap * 100) if cap > 0 else 0
            if pct >= 100:
                alerts.append({
                    "severity": "critical",
                    "source": "budget_cap",
                    "title": f"{info['label']} spend is over its ${cap:.2f}/mo cap",
                    "detail": f"Estimated ${spend:.2f} this cycle ({pct:.0f}% of cap).",
                })
            elif pct >= 80:
                alerts.append({
                    "severity": "warning",
                    "source": "budget_cap",
                    "title": f"{info['label']} spend is nearing its ${cap:.2f}/mo cap",
                    "detail": f"Estimated ${spend:.2f} this cycle ({pct:.0f}% of cap).",
                })
    except Exception as exc:
        print(f"[alerts] budget-cap check failed: {exc}", flush=True)

    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 3))
    return {"alerts": alerts, "count": len(alerts)}


# ── API cost tracking (Settings -> API Costs) ────────────────────────────────

_RAILWAY_GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"


def _railway_graphql(query: str, variables: dict) -> dict:
    """Thin synchronous POST helper for Railway's GraphQL API -- a completely
    different provider/auth scheme (a personal account token) from etsy_api.py's
    OAuth client, so it gets its own tiny helper rather than being forced into
    that one. Raises on any non-2xx or a GraphQL 'errors' array so callers get a
    single clear failure path instead of silently returning partial data."""
    import requests
    token = os.getenv("RAILWAY_API_TOKEN", "").strip()
    if not token:
        raise RuntimeError("RAILWAY_API_TOKEN not configured")
    resp = requests.post(
        _RAILWAY_GRAPHQL_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"query": query, "variables": variables},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        raise RuntimeError("; ".join(e.get("message", "unknown") for e in data["errors"]))
    return data["data"]


def _railway_cost_snapshot() -> dict:
    """Best-effort Railway cost/usage snapshot for the current billing cycle.
    Railway's estimatedUsage query returns raw resource metrics (GB-hours,
    network GB) per project, not a single dollar figure -- confirmed by hand
    2026-07-09 (there is no estimatedCost/invoice-style field in their schema).
    Converts using Railway's published usage-based-plan rate card so Scott sees
    an actual number, but this is an ESTIMATE -- the linked Railway dashboard is
    always the authoritative source since these published rates can drift."""
    # dashboard_url is included on every branch (not just the success path) so the
    # Settings "Top Up" link still works even when the live cost figure isn't --
    # Scott can always get to the billing page, whether or not Frank can read it.
    dashboard_url = "https://railway.app/account/billing"
    project_id = os.getenv("RAILWAY_PROJECT_ID", "").strip()
    if not project_id:
        return {"available": False, "reason": "RAILWAY_PROJECT_ID not present in this environment", "dashboard_url": dashboard_url}
    query = """
    query($p: String!) {
      estimatedUsage(projectId: $p, measurements: [MEMORY_USAGE_GB, DISK_USAGE_GB, NETWORK_TX_GB, NETWORK_RX_GB, CPU_USAGE_2]) {
        estimatedValue
        measurement
      }
    }
    """
    try:
        data = _railway_graphql(query, {"p": project_id})
    except Exception as exc:
        return {"available": False, "reason": str(exc)[:200], "dashboard_url": dashboard_url}

    # Railway's published usage-based-plan rates (Pro tier list price, per
    # railway.app/pricing as of 2026-07). Verify against the dashboard if this
    # ever looks off -- Railway can change these without notice.
    _HOURS_PER_MONTH = 730
    rate_per_unit = {
        "MEMORY_USAGE_GB": 10.0 / _HOURS_PER_MONTH,   # $10/GB-month -> $/GB-hour
        "CPU_USAGE_2": 20.0 / _HOURS_PER_MONTH,        # $20/vCPU-month -> $/vCPU-hour
        "DISK_USAGE_GB": 0.25 / _HOURS_PER_MONTH,      # $0.25/GB-month volume storage
        "NETWORK_TX_GB": 0.05,                         # $0.05/GB egress
        "NETWORK_RX_GB": 0.0,                          # ingress is free
    }
    by_measurement = {u["measurement"]: u["estimatedValue"] for u in data.get("estimatedUsage", [])}
    estimated_cost = sum(by_measurement.get(k, 0) * rate for k, rate in rate_per_unit.items())
    return {
        "available": True,
        "estimated_cost_usd": round(estimated_cost, 2),
        "raw_usage": by_measurement,
        "note": (
            "Estimated from raw resource usage x Railway's published usage-based rate "
            "card -- Railway's API has no direct dollar-cost field. Verify against the "
            "Railway dashboard for the authoritative number."
        ),
        "dashboard_url": dashboard_url,
    }


# Published Anthropic per-model rate card, $ per million tokens (verify against
# console.anthropic.com/settings/billing if this ever looks off -- these can
# change without notice, same caveat as the Railway estimate above). Cache reads
# are priced at 10% of the base input rate, cache writes at 125%, per Anthropic's
# documented prompt-caching discount structure.
_ANTHROPIC_RATES = {
    "claude-sonnet-5":                 {"input": 3.00,  "output": 15.00},
    "claude-sonnet-4-6":                {"input": 3.00,  "output": 15.00},
    "claude-haiku-4-5-20251001":        {"input": 0.80,  "output": 4.00},
    "claude-opus-4-8":                  {"input": 15.00, "output": 75.00},
}
_ANTHROPIC_DEFAULT_RATE = {"input": 3.00, "output": 15.00}


def _anthropic_cost_snapshot() -> dict:
    """Best-effort Anthropic spend estimate from Frank's OWN logged calls
    (_log_anthropic_usage -> activity_log action_type='anthropic_usage') for the
    current calendar month (UTC) -- NOT the Anthropic Console's real billing,
    which needs an Admin API key that isn't wired up yet. This is real usage
    Frank has actually seen since usage logging shipped (2026-07-10); anything
    spent before that date is invisible here (see console.anthropic.com's Usage
    page for the authoritative historical number)."""
    try:
        month_start = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        rows = db.anthropic_usage_since(month_start)
    except Exception as exc:
        return {"available": False, "reason": str(exc)[:200]}

    if not rows:
        return {
            "available": True,
            "estimated_cost_usd": 0.0,
            "call_count": 0,
            "note": (
                "No Anthropic calls logged yet this month -- usage logging just shipped "
                "(2026-07-10), so this fills in going forward, not retroactively. Check "
                "console.anthropic.com's Usage page for spend from before that date."
            ),
        }

    by_model: dict = {}
    total_cost = 0.0
    for row in rows:
        model = row.get("model") or "?"
        rate = _ANTHROPIC_RATES.get(model, _ANTHROPIC_DEFAULT_RATE)
        input_tok = row.get("input_tokens", 0) or 0
        output_tok = row.get("output_tokens", 0) or 0
        cache_write_tok = row.get("cache_creation_input_tokens", 0) or 0
        cache_read_tok = row.get("cache_read_input_tokens", 0) or 0
        cost = (
            input_tok * rate["input"] / 1_000_000
            + output_tok * rate["output"] / 1_000_000
            + cache_write_tok * (rate["input"] * 1.25) / 1_000_000
            + cache_read_tok * (rate["input"] * 0.10) / 1_000_000
        )
        total_cost += cost
        m = by_model.setdefault(model, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})
        m["calls"] += 1
        m["input_tokens"] += input_tok
        m["output_tokens"] += output_tok
        m["cost_usd"] = round(m["cost_usd"] + cost, 4)

    return {
        "available": True,
        "estimated_cost_usd": round(total_cost, 2),
        "call_count": len(rows),
        "by_model": by_model,
        "note": (
            "Estimated from Frank's own logged Anthropic calls this month x Anthropic's "
            "published per-model rate card -- not official billing. Verify against "
            "console.anthropic.com/settings/billing for the authoritative number."
        ),
    }


# No provider (Railway, Anthropic, OpenAI, Google Cloud Billing) exposes a public
# API for a third-party app to charge a card / add funds -- confirmed by hand
# 2026-07-09, this is a deliberate security/PCI boundary none of them cross for
# external apps. So there is no "add money" endpoint here -- these dashboard_url
# values are the real, current billing/top-up page for each provider, surfaced
# as a one-tap link from Settings -> API Costs. Anthropic and OpenAI additionally
# support a one-time "Auto Recharge" setup (configured on their own dashboard,
# not triggerable by Frank) -- see has_auto_recharge below.
def _all_service_costs() -> dict:
    """Synchronous core shared by GET /api/system/costs and the alerts budget-cap
    check above (so both read the exact same numbers in the same request cycle)."""
    services = {"railway": {"label": "Railway (hosting)", "has_auto_recharge": False, **_railway_cost_snapshot()}}

    # Anthropic/OpenAI need Admin-scoped API keys (separate from the regular
    # ANTHROPIC_API_KEY/OPENAI_API_KEY already in use) to pull real spend; Gemini
    # needs Google Cloud Billing access (a service account + Billing Account ID,
    # not just a key). None of the three are wired up yet -- reported honestly
    # as unavailable with the exact setup step, never guessed at or faked.
    services["anthropic"] = {
        "label": "Anthropic (Claude)",
        "dashboard_url": "https://console.anthropic.com/settings/billing",
        "has_auto_recharge": True,
        **_anthropic_cost_snapshot(),
    }
    services["openai"] = {
        "label": "OpenAI (images/voice)",
        "available": False,
        "reason": "Needs an Organization Admin key with usage scope (platform.openai.com → Settings → Organization → Admin keys) -- not yet wired up.",
        "dashboard_url": "https://platform.openai.com/settings/organization/billing/overview",
        "has_auto_recharge": True,
    }
    services["gemini"] = {
        "label": "Gemini (Google)",
        "available": False,
        "reason": "Needs Google Cloud Billing access (service account with billing.viewer role + Billing Account ID) -- bigger setup than a single API key, not yet wired up.",
        "dashboard_url": "https://console.cloud.google.com/billing",
        "has_auto_recharge": False,
    }

    budget_caps = {}
    for svc in services:
        raw = db.get_setting(f"budget_cap_{svc}")
        budget_caps[svc] = float(raw) if raw else None

    return {"services": services, "budget_caps": budget_caps}


@app.get("/api/system/costs")
async def get_system_costs(_token: str = Depends(_auth_session_or_bearer)):
    """Live per-service API cost snapshot for the Settings 'API Costs' card."""
    return await asyncio.to_thread(_all_service_costs)


@app.post("/api/system/costs/budget-caps")
async def set_budget_caps(body: dict, _token: str = Depends(_auth_session_or_bearer)):
    """Save per-service monthly $ budget caps -- checked by GET /api/alerts so
    crossing 80%/100% shows up in the alert bell for services with live cost data."""
    allowed = {"railway", "anthropic", "openai", "gemini"}
    saved = {}
    for svc, val in (body or {}).items():
        if svc not in allowed:
            continue
        if val in (None, ""):
            await asyncio.to_thread(db.set_setting, f"budget_cap_{svc}", None)
            saved[svc] = None
            continue
        try:
            f = float(val)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail=f"budget cap for {svc} must be a number")
        if f < 0:
            raise HTTPException(status_code=400, detail=f"budget cap for {svc} must be >= 0")
        await asyncio.to_thread(db.set_setting, f"budget_cap_{svc}", str(f))
        saved[svc] = f
    return {"saved": saved}


@app.get("/api/tools/list")
async def get_tools_list(_token: str = Depends(_auth_session_or_bearer)):
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
async def get_workflows(_token: str = Depends(_auth_session_or_bearer)):
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
async def post_workflow_run(workflow_id: str, body: dict | None = None, _token: str = Depends(_auth_session_or_bearer)):
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
async def post_relay_kill(_token: str = Depends(_auth_session_or_bearer)):
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
async def post_relay_resume(_token: str = Depends(_auth_session_or_bearer)):
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
async def get_allowed_folders(_token: str = Depends(_auth_session_or_bearer)):
    """The relay polls this (or refreshes periodically) so folder changes take
    effect without restarting the relay process."""
    folders = await asyncio.to_thread(db.list_allowed_folders)
    return {"folders": folders}


@app.post("/api/relay/allowed-folders")
async def post_allowed_folder(payload: dict, _token: str = Depends(_auth_session_or_bearer)):
    path = (payload or {}).get("path", "").strip()
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    folder_id = await asyncio.to_thread(db.add_allowed_folder, path, "scott")
    await asyncio.to_thread(db.log_activity, "scott", "allowed_folder_add", path, None, "ok")
    return {"ok": True, "id": folder_id}


@app.delete("/api/relay/allowed-folders/{folder_id}")
async def delete_allowed_folder(folder_id: int, _token: str = Depends(_auth_session_or_bearer)):
    import trash
    folders = await asyncio.to_thread(db.list_allowed_folders)
    row = next((f for f in folders if f["id"] == folder_id), None)
    if row:
        await asyncio.to_thread(
            trash.archive_snippet, "db:allowed_folders", json.dumps(row, default=str),
            f"allowed folder removed via dashboard (id={folder_id})",
        )
    ok = await asyncio.to_thread(db.remove_allowed_folder, folder_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Folder not found")
    await asyncio.to_thread(db.log_activity, "scott", "allowed_folder_remove", str(folder_id), None, "ok")
    return {"ok": True}


@app.post("/api/relay/upload")
async def upload_to_relay(request: Request, path: str, _token: str = Depends(_auth_session_or_bearer)):
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
async def get_todos(_token: str = Depends(_auth_session_or_bearer)):
    items = await asyncio.to_thread(db.list_todos)
    return {"todos": items, "open_count": sum(1 for t in items if not t["done"])}


@app.post("/api/todos")
async def post_todo(payload: dict, _token: str = Depends(_auth_session_or_bearer)):
    text = (payload or {}).get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    added_by = (payload or {}).get("added_by", "scott").strip().lower()
    if added_by not in ("scott", "frank"):
        added_by = "scott"
    due_date = (payload or {}).get("due_date") or None
    category = (payload or {}).get("category", "general").strip().lower()
    if category not in db.TODO_CATEGORIES:
        category = "general"
    todo_id = await asyncio.to_thread(db.add_todo, text, added_by, due_date, category)
    return {"ok": True, "id": todo_id}


@app.post("/api/todos/{todo_id}/toggle")
async def toggle_todo(todo_id: int, payload: dict, _token: str = Depends(_auth_session_or_bearer)):
    done = bool((payload or {}).get("done", True))
    ok = await asyncio.to_thread(db.set_todo_done, todo_id, done)
    if not ok:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"ok": True}


@app.post("/api/todos/{todo_id}/category")
async def set_todo_category_endpoint(todo_id: int, payload: dict, _token: str = Depends(_auth_session_or_bearer)):
    category = ((payload or {}).get("category") or "").strip().lower()
    if category not in db.TODO_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"category must be one of {sorted(db.TODO_CATEGORIES)}")
    ok = await asyncio.to_thread(db.set_todo_category, todo_id, category)
    if not ok:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"ok": True}


@app.post("/api/todos/{todo_id}/answer")
async def answer_todo(todo_id: int, payload: dict, _token: str = Depends(_auth_session_or_bearer)):
    """Store Scott's answer to a question-category todo and push it into the
    ops runbook so Frank actually sees it on his next chat turn -- todos are
    never auto-injected into chat context (list_todos is a tool Frank must
    proactively call), but _ops_runbook_block() is unconditionally prepended
    to every turn's system prompt, so that's the real delivery mechanism, not
    just the DB column (2026-07-15 design note, see the plan this shipped
    from). Deliberately does not touch `done` -- an answer informs the next
    step, it doesn't mean the underlying task is resolved."""
    answer = ((payload or {}).get("answer") or "").strip()
    if not answer:
        raise HTTPException(status_code=400, detail="answer is required")
    todos = await asyncio.to_thread(db.list_todos)
    row = next((t for t in todos if t["id"] == todo_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")
    ok = await asyncio.to_thread(db.set_todo_answer, todo_id, answer)
    if not ok:
        raise HTTPException(status_code=404, detail="Todo not found")
    await asyncio.to_thread(
        _append_ops_runbook_entry, "Scott answered a todo question",
        f"Q: {row['text']}\nA: {answer}",
    )
    return {"ok": True}


@app.delete("/api/todos/{todo_id}")
async def remove_todo(todo_id: int, _token: str = Depends(_auth_session_or_bearer)):
    import trash
    todos = await asyncio.to_thread(db.list_todos)
    row = next((t for t in todos if t["id"] == todo_id), None)
    if row:
        await asyncio.to_thread(
            trash.archive_snippet, "db:todos", json.dumps(row, default=str),
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
async def get_cadence(_token: str = Depends(_auth_session_or_bearer)):
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
async def get_conversations(q: str = "", _token: str = Depends(_auth_session_or_bearer)):
    """Session list (most-recently-active first), or — when `q` is supplied —
    a cross-session substring search instead."""
    if q.strip():
        results = await asyncio.to_thread(db.search_chat_messages, q.strip())
        return {"query": q.strip(), "results": results}
    sessions = await asyncio.to_thread(db.list_chat_sessions)
    return {"sessions": sessions}


@app.get("/api/conversations/{session_id}")
async def get_conversation_detail(session_id: str, _token: str = Depends(_auth_session_or_bearer)):
    """Full message history for one session."""
    data = await asyncio.to_thread(db.get_chat_session, session_id)
    if not data["messages"]:
        raise HTTPException(status_code=404, detail="No messages for this session")
    return data


# ── File hub (browse/download product files + backups straight from the dashboard) ─

_FILE_ROOTS = {
    "products": ROOT / "data" / "digital_products",
    "backups": ROOT / "data" / "backups",
    "hub_db_backups": ROOT / "data" / "hub_db_backups",
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


def _product_file_exists(rel: str) -> bool:
    """Check a product file under BOTH the local data/ tree (works when running
    on Scott's own machine) and the persistent /data volume (where
    tools/sync_files_to_hub.py uploads real product files so they survive
    redeploys). Checking only the former always reported "missing" on the
    deployed Railway dashboard even for properly-synced files, since data/ is
    dockerignored (2026-07-14: every product on the Products screen showed a
    false FAIL for this reason). `rel` matches sync_files_to_hub.py's own
    upload-path convention, e.g. "product_files/DP1026.pdf"."""
    if (_FILE_ROOTS["products"] / rel).exists():
        return True
    vol = _FILE_ROOTS.get("volume")
    return bool(vol and (vol / rel).exists())

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
# SVG Converter tool output — regeneratable (re-run the conversion any time), not
# source-of-truth product assets, so same non-durable local dir as studio_uploads.
_FILE_ROOTS["svg_conversions"] = ROOT / "data" / "social" / "svg_conversions"
# Lifestyle Photo Generator output — same regeneratable-working-file reasoning as
# svg_conversions above. Passed products still go through the existing staged_photos
# root + Action Center approval, not this one — this is the standalone generation
# tool's own scratch output before anything is staged for a real listing.
_FILE_ROOTS["lifestyle_photos"] = ROOT / "data" / "social" / "lifestyle_photos"


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


# Ephemeral/regenerable runtime output -- already gitignored for the same reason
# (see .gitignore's "Generated social media videos" block) -- excluded from the
# full-backup ZIP so it stays a durable-content snapshot, not a dump of whatever
# transient files happen to be sitting in this container right now.
_FULL_BACKUP_EXCLUDE_DIR_NAMES = {
    "staged_photos", "staged_videos", "videos", "studio_uploads",
    "image_proofs", "_rejects", "svg_conversions", "lifestyle_photos",
    "browser_screenshots", "__pycache__",
}


@app.get("/api/backup/download-all")
async def download_full_backup(request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """Build and stream a ZIP of whatever's under data/ in THIS deployed
    container -- which, per .dockerignore's `data/*` blanket exclusion (kept
    deliberately narrow so Docker builds don't ship 4GB+ and time out, see
    that file's own comment), is only knowledge_base/ plus a handful of
    listed JSON configs (product_catalog.json, dp_listing_map.json, etc.).
    The real ~350MB of product assets (svg_pack/, faith_pack/, digital_products/,
    and friends) is NOT reachable from here at all -- it exists only in the git
    repo itself. This endpoint is the honest answer to "give me the small stuff
    as a hard copy"; the Files-screen UI links to GitHub's own repo-zip download
    for the rest, since that's the one place the full 350MB actually lives.
    No AI call, no Etsy call -- not rate-limited (see _rate_limited_auth,
    reserved for AI-spend/Etsy-mutating calls, neither of which this does).
    2026-07-15 security audit: previously used only the generic session-or-
    bearer check, unlike every other infra-sensitive route (etsy-tokens,
    redeploy) which additionally require owner role for a session caller.
    Matched to the redeploy endpoint's exact tier (_require_owner_or_automation,
    not the stricter owner-only _require_owner used by etsy-tokens) since
    this is the same risk class -- an infra/data action, not raw credential
    exposure -- and a bearer/automation caller is already trusted at that
    tier everywhere else in this file."""
    _require_owner_or_automation(request)

    def _build() -> str:
        tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        tmp.close()
        with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted((ROOT / "data").rglob("*")):
                if path.is_dir():
                    continue
                rel = path.relative_to(ROOT)
                if any(part in _FULL_BACKUP_EXCLUDE_DIR_NAMES for part in rel.parts):
                    continue
                zf.write(path, arcname=str(rel))
        return tmp.name

    try:
        zip_path = await asyncio.to_thread(_build)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not build backup: {exc}")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return FileResponse(
        zip_path,
        filename=f"frank_full_backup_{stamp}.zip",
        media_type="application/zip",
        background=BackgroundTask(lambda: Path(zip_path).unlink(missing_ok=True)),
    )


@app.get("/api/files")
async def list_files(_token: str = Depends(_auth_session_or_bearer)):
    """List every file under data/digital_products/ and data/backups/ so Scott can
    see, open, and download product source files straight from the dashboard —
    these directories are gitignored (machine-local) and have no other UI.

    For each ZIP we also expand its contents so individual files (PDFs, sticker
    PNGs, SVGs) can be opened directly on a phone WITHOUT downloading and
    unzipping first (Scott's request, 2026-06-17)."""

    # rglob + stat() + per-zip central-directory reads across every file root is
    # synchronous filesystem work that can take real wall-clock time with several
    # backup/product zips present -- run off the event loop so it doesn't freeze the
    # whole single-process app while it scans (2026-07-08 performance pass).
    def _scan() -> dict:
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
                "svg_conversions": "SVG Conversions",
                "lifestyle_photos": "Lifestyle Photos",
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

    return await asyncio.to_thread(_scan)


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
async def download_file(request: Request, root: str, path: str, token: str = "", ticket: str = "", inline: int = 0):
    """Stream a file from one of the allowed roots. Auth via session cookie, Bearer
    header, or ?token= query param — all accepted so browser links and direct
    file-open requests work without embedding a token in the URL. A single-use
    ?ticket= (see _new_file_ticket) is also accepted as a narrower alternative for
    handing a one-time link to a third party (e.g. Meta fetching a video to post) —
    checked first since it's more restrictive and self-invalidates.

    inline=1 serves with the real media type and an inline disposition so the phone
    browser previews it (PDF viewer, image) instead of downloading — except .svg/
    .html/.htm outside the svg_conversions root (server-generated, safe by
    construction), which always download as an attachment: an uploaded SVG can carry
    an embedded <script>, and this app's CSP allows inline scripts for its own single-
    page-app reasons, so inline-serving an arbitrary uploaded SVG would let it execute
    same-origin with the viewer's session (2026-07-08 security review)."""
    if not _consume_file_ticket(ticket, root, path):
        _auth_session_or_bearer(request)
    target = _resolve_in_root(root, path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    ext = target.suffix.lower()
    force_download = ext in (".svg", ".html", ".htm") and root != "svg_conversions"
    if inline and not force_download:
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
async def upload_to_volume(request: Request, path: str, _token: str = Depends(_auth_session_or_bearer)):
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

    def _write() -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)

    # Synchronous disk write for a payload up to 30MB -- run off the event loop so a
    # large sync upload doesn't stall every other request (2026-07-08 performance pass).
    await asyncio.to_thread(_write)
    return {"ok": True, "path": rel, "size": len(body), "size_human": _human_size(len(body))}


@app.get("/api/files/zip-entry")
async def open_zip_entry(request: Request, root: str, path: str, entry: str, token: str = "", inline: int = 1, _auth: str = Depends(_auth_session_or_bearer)):
    """Stream a single file OUT of a ZIP without the user unzipping anything.

    This is the core of Scott's 'open without unzip on a phone' request: tap a
    file inside a sticker pack / print-size ZIP and it opens directly. Default
    inline=1 so PDFs/PNGs preview in the phone browser."""
    target = _resolve_in_root(root, path)
    if not target.is_file() or target.suffix.lower() != ".zip":
        raise HTTPException(status_code=404, detail="ZIP not found")

    def _read_entry() -> bytes:
        with zipfile.ZipFile(target) as zf:
            return zf.read(entry)

    # Decompressing a ZIP entry (a multi-MB PDF/PNG) is synchronous I/O -- run off
    # the event loop so previewing a file doesn't stall every other request for the
    # duration (2026-07-08 performance pass). Exception mapping stays outside the
    # thread call, same convention as studio_upload_image/upload_brand_mark.
    try:
        data = await asyncio.to_thread(_read_entry)
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
async def post_ws_ticket(_token: str = Depends(_auth_session_or_bearer)):
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


_PII_TOOLS = frozenset({"get_orders"})  # tools whose results include a real buyer name


def _should_persist_chat_turn(session_id: str, pii_tools_used: frozenset[str]) -> bool:
    """False when this turn shouldn't be written to the durable, searchable
    chat_messages table -- either no session to persist to, or a buyer-data
    tool was used this turn (see _run_agent_turn's docstring). The in-memory
    `history` list is untouched either way -- Frank still remembers the
    exchange for the rest of this live connection; only the durable DB write
    is skipped. Pulled out as its own function so this decision is directly
    unit-testable without a full websocket integration test."""
    return bool(session_id) and not pii_tools_used


async def _run_agent_turn(websocket: WebSocket, ai_client, history: list[dict]) -> tuple[str, frozenset[str]]:
    """One user turn: stream text, run any tools the model requests, repeat until
    the model is done. Tool calls let the CEO agent read live shop data.

    The Anthropic SDK's stream is a *blocking* iterator — reading it directly inside
    this coroutine would tie up the whole shared asyncio event loop (every other
    concurrent /ws/chat session, every background loop) for as long as a chunk takes
    to arrive over the network. So the blocking read runs in a worker thread; chunks
    cross back into the event loop via call_soon_threadsafe onto an asyncio.Queue,
    bounded by a 90s per-chunk stall timeout so a frozen connection can't hang the
    shared loop forever.

    Returns (assistant_text, pii_tools_used) — the caller persists assistant_text to
    chat memory, but skips that persistence entirely when pii_tools_used is non-empty
    (2026-07-15 ADA/security audit: get_orders returns a real buyer name to the model
    for that turn, which it needs to answer naturally, but nothing should write that
    name into Frank's durable, searchable chat-history DB — Scott's explicit choice
    among the options presented, see ops_runbook.md). Raises on a stream/API failure
    or stall — the caller is responsible for rolling back this turn's additions to
    `history`."""
    assistant_text_parts: list[str] = []
    pii_tools_used: set[str] = set()
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
                    model=business_config.MODEL_PRIMARY,
                    max_tokens=1500,
                    system=[
                        _system_block(),
                        # Was uncached (~3,500 tok resent on every turn) -- within one
                        # active conversation these files realistically don't change
                        # turn-to-turn, so caching here has a real hit rate, unlike the
                        # once-every-~4h suggestions loop (left uncached on purpose).
                        {
                            "type": "text",
                            "text": _ops_runbook_block() + _ceo_learnings_block(),
                            "cache_control": {"type": "ephemeral"},
                        },
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
                _log_anthropic_usage("chat_stream", business_config.MODEL_PRIMARY, getattr(final_msg, "usage", None))
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
            return "".join(assistant_text_parts).strip(), frozenset(pii_tools_used)

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
                elif block.name == "render_page":
                    url = (block.input or {}).get("url", "")
                    status_msg = f"🌐 Rendering {url[:60]}…"
                elif block.name == "screenshot_url":
                    url = (block.input or {}).get("url", "")
                    status_msg = f"📸 Screenshotting {url[:50]}…"
                elif block.name == "check_browser_status":
                    status_msg = "🧭 Checking browser…"
                elif block.name == "check_etsy_search_rank":
                    kw = (block.input or {}).get("keyword", "")
                    status_msg = f"📈 Checking Etsy rank: {kw[:40]}…"
                elif block.name == "watch_video":
                    src = (block.input or {}).get("source", "")
                    status_msg = f"🎬 Watching {src[:50]}…"
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
                if block.name in _PII_TOOLS:
                    pii_tools_used.add(block.name)
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
    return "".join(assistant_text_parts).strip(), frozenset(pii_tools_used)


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
async def transcribe_voice(request: Request, _token: str = Depends(_rate_limited_auth)):
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
async def speak_text(payload: dict, _token: str = Depends(_rate_limited_auth)):
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
            model=business_config.MODEL_CHEAP,
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

    # Per-connection rate limit — a leaked/reused ws ticket shouldn't be able to spam
    # unlimited Anthropic calls through one long-lived socket (2026-07-08 security
    # review). Same budget as the REST AI-spend endpoints; kept local to this
    # connection (not the shared _rate_buckets store) since a ws ticket carries no
    # username to key a per-user bucket by.
    _chat_msg_times: list[float] = []

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

            now = time.time()
            _chat_msg_times[:] = [t for t in _chat_msg_times if now - t < _AI_SPEND_RATE_WINDOW]
            if len(_chat_msg_times) >= _AI_SPEND_RATE_MAX:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"Rate limit exceeded — max {_AI_SPEND_RATE_MAX} messages per "
                               f"hour on this connection. Try again later.",
                }))
                continue
            _chat_msg_times.append(now)

            # Snapshot length so a mid-turn failure can be rolled back cleanly.
            # Without this, a dangling user message (no assistant reply) leaves
            # the next turn sending two user turns back-to-back, which the API
            # rejects — wedging the chat until a full reload.
            base_len = len(history)
            history.append({"role": "user", "content": user_text})
            try:
                assistant_text, pii_tools_used = await _run_agent_turn(websocket, ai_client, history)
            except Exception as exc:
                print(f"[chat] turn failed: {exc}", flush=True)
                del history[base_len:]  # roll back this turn's additions
                await websocket.send_text(json.dumps({"type": "error", "content": _friendly_error_message(exc)}))
                continue

            # Persist only completed exchanges (text-only — see db.append_chat_message)
            # that didn't touch buyer data this turn (see _should_persist_chat_turn).
            if _should_persist_chat_turn(session_id, pii_tools_used):
                await asyncio.to_thread(db.append_chat_message, session_id, "user", user_text)
                if assistant_text:
                    await asyncio.to_thread(db.append_chat_message, session_id, "assistant", assistant_text)
                await asyncio.to_thread(_maybe_compact_chat_history, session_id)
            elif session_id and pii_tools_used:
                print(f"[chat] skipping persist for a turn that touched buyer data via {sorted(pii_tools_used)}",
                      flush=True)

    except WebSocketDisconnect:
        pass


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
