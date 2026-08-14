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
import codecs
import hashlib
import inspect
import io
import json
import mimetypes
import os
import random
import re as _re
import secrets
import shlex
import shutil
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
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
import oauth_providers  # Google / Apple Sign-In (tools/api_server/oauth_providers.py)
import seasonal_keywords  # noqa: E402
import tax_compliance_tools  # noqa: E402
import etsy_api
from etsy_api import EtsyAPIClient, EtsyAPIError  # noqa: E402
import business_tracker  # noqa: E402 — GET /api/business-tracker.xlsx workbook builder
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
# Same pattern, separate breaker, for xAI/Grok text calls (2026-08-05) -- one
# breaker per external text provider, same style as _anthropic_breaker above
# rather than trying to generalize a single breaker across two SDKs with
# different exception types.
_xai_breaker = CircuitBreaker("xai_api", db_module=db)


# Known-good fallback brain. If MODEL_PRIMARY (currently claude-sonnet-5) isn't
# available to this deploy's Anthropic account, _anthropic_create() drops to this
# once — so promoting the primary model can never hard-break Frank; it just logs
# and degrades gracefully. Keep this pointed at a model every account can reach.
_MODEL_FALLBACK = "claude-sonnet-4-6"

_SHOP_TZ_FALLBACK = "America/New_York"  # used until Settings' Timezone field is filled in


def _shop_now() -> datetime:
    """Current time in the shop's own local timezone, not the server's --
    Railway containers default to UTC (no TZ env var set anywhere in this
    repo's deploy config, confirmed 2026-08-04 Calendar screen audit). Every
    cadence/calendar-sync date comparison in this file used to call bare
    date.today()/datetime.now(timezone.utc), which rolls to the next
    calendar day several hours before local midnight for a US-based shop --
    misclassifying same-day items as OVERDUE, or as already-past for the
    sync loop's backfill guard, hours before they actually are locally
    (and, for _calendar_tasks_loop, misjudging which weekday/day-of-month
    "today" is for its Sunday/1st/8th/15th trigger checks). Reads Settings'
    user_profile.timezone; falls back to _SHOP_TZ_FALLBACK if unset or
    invalid."""
    tz_name = (db.get_user_profile().get("timezone") or "").strip() or _SHOP_TZ_FALLBACK
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        tz = ZoneInfo(_SHOP_TZ_FALLBACK)
    return datetime.now(tz)


def _shop_today() -> date:
    """'Today' in the shop's own local timezone -- see _shop_now()."""
    return _shop_now().date()


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


def _log_xai_usage(caller: str, model: str, usage) -> None:
    """xAI/Grok counterpart to _log_anthropic_usage() above -- same activity_log
    trail, different provider. xAI's API is OpenAI-SDK-compatible, so `usage`
    is an OpenAI-shaped CompletionUsage object (prompt_tokens/completion_tokens),
    not Anthropic's (input_tokens/output_tokens) -- logged under its own field
    names rather than force-fitting Anthropic's, so the two providers' spend
    stay honestly distinguishable in activity_log."""
    try:
        db.log_activity(
            actor="system",
            action_type="xai_usage",
            detail=f"{caller} · {model}",
            payload={
                "caller": caller,
                "model": model,
                "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
            },
            outcome="ok",
        )
    except Exception as exc:
        print(f"[xai-usage] logging failed (non-fatal): {exc}", flush=True)


def _xai_create(client: "openai.OpenAI", **kwargs):
    """xAI/Grok counterpart to _anthropic_create() above (2026-08-05) -- same
    circuit-breaker-wrapped, usage-logged shape, but calling xAI's OpenAI-SDK
    -compatible chat.completions.create() instead of Anthropic's messages
    .create(). No model-fallback self-heal (unlike _anthropic_create()'s
    _MODEL_FALLBACK) -- there's no established secondary Grok tier to fall
    back to yet; a model-access error just surfaces to the caller. UNPROVEN
    against a real xAI response at write time (XAI_API_KEY lives on Railway,
    not in this dev sandbox) -- confirm the exception types raised on a real
    failure match `openai.APIConnectionError`/`RateLimitError`/
    `InternalServerError` (they should, since this is the standard `openai`
    package hitting an OpenAI-compatible endpoint, but genuinely unverified)."""
    if not _xai_breaker.allow_request():
        raise CircuitBreakerOpenError(
            "circuit breaker 'xai_api' is open -- skipping call until cooldown elapses"
        )
    try:
        result = client.chat.completions.create(**kwargs)
    except (openai.APIConnectionError, openai.RateLimitError, openai.InternalServerError):
        _xai_breaker.record_failure()
        raise
    else:
        _xai_breaker.record_success()
        _log_xai_usage(inspect.stack()[1].function, kwargs.get("model", "?"), getattr(result, "usage", None))
        return result


def _xai_client() -> "openai.OpenAI":
    """One place that builds the xAI-pointed OpenAI SDK client -- base_url
    override is the entire integration surface (xAI's API is OpenAI-SDK
    -compatible per their own docs), confirmed 2026-08-05."""
    return openai.OpenAI(api_key=XAI_KEY, base_url="https://api.x.ai/v1")


def _effective_text_engine(override: str | None = None) -> str:
    """Current TEXT_ENGINE setting, normalized -- degrades to anthropic when
    grok is selected but XAI_API_KEY isn't configured, same "never hard-break,
    just fall back" pattern as _anthropic_create()'s model fallback (2026-08-05).
    Every one of the four TEXT_ENGINE-aware call sites reads the engine through
    this single function so "grok selected, no key" can never diverge into two
    different behaviors across call sites.

    `override` (2026-08-05, Scott: "swappable per-task, like images") lets a
    single call request a specific engine for just that one generation,
    without touching the shop-wide TEXT_ENGINE default -- same normalize/
    degrade rules apply to it as to the env-level default. Currently only
    threaded through _generate_product_listing_content_core() (the one call
    site with a natural per-generation "Advanced" UI affordance, the product
    review modal's "Generate listing content" button); the other three
    TEXT_ENGINE-aware call sites (tag/title autofix, classification) are
    reached from chat tools/background sweeps with no analogous per-call UI,
    so they stay governed by the global default only."""
    engine = (override or os.getenv("TEXT_ENGINE", "anthropic")).lower()
    if engine == "grok" and not XAI_KEY:
        return "anthropic"
    return engine


def _grok_text(prompt: str, max_tokens: int = 2000, model: str | None = None) -> str:
    """One-shot Grok text call shared by the TEXT_ENGINE=grok branch of
    _generate_tags_for_listings(), classify_listings_batch(),
    _autofix_title_core(), and _generate_product_listing_content_core().
    Concatenates whatever the Claude-side prompt would have sent as separate
    cache_control-split blocks into one plain user message -- xAI's OpenAI
    -compatible endpoint has no equivalent to Anthropic's explicit ephemeral
    cache_control blocks, so there's nothing to preserve there (2026-08-05).
    Raises on failure exactly like a raw _anthropic_create() call would --
    callers already wrap their Anthropic call in try/except and should treat
    this identically, not get a silent fallback to a provider Scott didn't
    select."""
    client = _xai_client()
    response = _xai_create(
        client, model=model or business_config.GROK_MODEL_CHEAP, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return (response.choices[0].message.content or "").strip()


def _reconcile_etsy_tokens() -> None:
    """Restore a rotated Etsy token from the durable /data DB if the env var is stale.

    Railway re-injects whatever ETSY_ACCESS_TOKEN/ETSY_REFRESH_TOKEN it has stored on
    every restart. But Etsy rotates the refresh token on every use and invalidates the
    old one — so if this server refreshed the token before a restart, the env var is
    now a dead token and the next refresh 401s with invalid_grant (diagnosed 2026-06-17,
    see ops_runbook.md). _token_sync_loop() below persists each rotation to the /data
    SQLite volume, which survives restarts; this function runs once at boot and prefers
    that row — but only when it's provably a forward rotation of the *current* env
    token (matched via the full parent_refresh_token lineage, not just the immediate
    parent — see db.parse_token_lineage()'s docstring for the 2026-07-18 bug this fixed:
    2+ reactive rotations without a restart used to lose track of anything more than
    one generation back, so a stale env var from 2+ rotations ago could be
    misidentified as a genuine fresh manual re-authorization), so a genuine manual
    re-authorization (tools/etsy_oauth.py + a fresh dashboard update) still always wins
    over a stale DB row left over from before that re-auth.
    """
    env_refresh = os.getenv("ETSY_REFRESH_TOKEN", "").strip()
    try:
        stored = db.get_etsy_tokens()
    except Exception as exc:
        print(f"[etsy-tokens] reconcile skipped: {exc}", flush=True)
        return
    if not stored:
        return
    known_lineage = [stored.get("refresh_token")] + db.parse_token_lineage(stored.get("parent_refresh_token"))
    if env_refresh and env_refresh not in known_lineage:
        print("[etsy-tokens] env refresh token doesn't match stored lineage — "
              "treating env as a fresh re-authorization, leaving it in place", flush=True)
        return
    if stored.get("access_token") and stored.get("refresh_token"):
        os.environ["ETSY_ACCESS_TOKEN"] = stored["access_token"]
        os.environ["ETSY_REFRESH_TOKEN"] = stored["refresh_token"]
        print(f"[etsy-tokens] restored rotated token from {db.DB_PATH} (persistent={db.is_persistent()})", flush=True)


def _reconcile_google_calendar_tokens() -> None:
    """Restore Google Calendar tokens from the durable /data DB if the env
    var copy is stale or missing -- same problem class _reconcile_etsy_tokens()
    exists for (Railway re-injects a static env var config on every restart,
    which can be older than what's actually in the persistent DB volume),
    but simpler: unlike Etsy, Google's refresh token doesn't get invalidated
    by use, so there's no rotation-lineage check needed here -- the DB row
    (written by both google_calendar_oauth.py and
    GoogleCalendarClient.refresh_access_token() on every successful refresh)
    is always at least as current as the env var, so it can just win
    outright whenever it's present.

    Bug fixed 2026-07-18: this reconcile step never existed at all, so a
    Railway restart could silently lose the Google Calendar connection even
    though the DB had a perfectly good, still-valid refresh token sitting
    right there -- the exact failure this same-shaped Etsy function exists
    to prevent, just never mirrored for the newer integration."""
    try:
        stored = db.get_google_calendar_tokens()
    except Exception as exc:
        print(f"[gcal-tokens] reconcile skipped: {exc}", flush=True)
        return
    if not stored or not stored.get("refresh_token"):
        return
    if stored.get("access_token"):
        os.environ["GOOGLE_CALENDAR_ACCESS_TOKEN"] = stored["access_token"]
    os.environ["GOOGLE_CALENDAR_REFRESH_TOKEN"] = stored["refresh_token"]
    print(f"[gcal-tokens] restored Google Calendar tokens from {db.DB_PATH} (persistent={db.is_persistent()})", flush=True)


_reconcile_etsy_tokens()
_reconcile_google_calendar_tokens()
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
    "text_engine":      ("env", "TEXT_ENGINE"),
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
    # 2026-07-17 (capabilities audit): order_notifier.py already ran weekly via
    # _WEEKLY_MONITOR_SCRIPTS but had no on-demand chat path -- Scott couldn't
    # ask Frank "check for new orders right now" mid-conversation. Uses
    # shops/{id}/receipts, a real working endpoint (unlike conversations, see
    # check_buyer_messages below) -- both entries are genuinely functional.
    "check_new_orders": {
        "script": "tools/order_notifier.py",
        "args": ["--dry"],
        "description": (
            "Preview new paid orders from the last 48h with their ready-to-send "
            "personalized buyer messages. Read-only: sends no email, marks nothing "
            "as notified. Safe to run as often as asked."
        ),
        "timeout": 60,
        "long_running": False,
        # 2026-07-19: order_notifier.py's stdout includes real buyer names and
        # personalized messages regardless of --dry -- this is the same PII class
        # _PII_TOOLS exists to flag, but _PII_TOOLS only ever matched on the
        # top-level tool name, which is always "execute_command" for anything
        # dispatched this way, so these turns were persisted to the durable chat
        # DB unflagged. _run_agent_turn checks this key when block.name ==
        # "execute_command" instead of assuming the wrapper tool name alone.
        "contains_pii": True,
    },
    "send_order_notifications": {
        "script": "tools/order_notifier.py",
        "description": (
            f"Email {business_config.OWNER_NAME} himself a digest of new paid orders "
            "(with personalized reply text for each) and mark them as notified so the "
            "weekly automatic run won't repeat them. Only emails the shop owner -- never "
            "contacts a buyer -- so this does not need approval, same as the existing "
            "automatic weekly run."
        ),
        "timeout": 60,
        "long_running": False,
        "contains_pii": True,  # same reasoning as check_new_orders above
    },
    # etsy_autoresponder.py's message-fetching pipeline hits shops/{id}/conversations,
    # which Etsy Open API v3 does NOT expose to third-party apps -- confirmed by a
    # live probe against this shop's own account (200 on receipts/listings, 404 on
    # conversations/messages; a real scope denial is 403, not 404) -- see
    # ops_runbook.md's 2026-06-19 entry. This is why CLAUDE.md's own Star Seller
    # section says API-driven buyer messaging isn't possible; only the Quick Reply /
    # Auto-Reply system in Shop Manager works. Registered anyway (draft-only, no
    # --send/--send-all) so a real ask surfaces this honestly through the script's
    # own clear "Could not fetch messages" output instead of Frank having no answer
    # at all -- and it becomes live for free the moment Etsy ships this endpoint.
    "check_buyer_messages": {
        "script": "tools/etsy_autoresponder.py",
        "description": (
            "Attempt to fetch new Etsy buyer messages and draft replies. KNOWN "
            "LIMITATION: Etsy's public API has no buyer-messaging endpoint for "
            "third-party apps (confirmed 2026-06-19) -- this will report 'Could not "
            f"fetch messages' every time. Tell {business_config.OWNER_NAME} to use Shop "
            "Manager's Quick Replies or built-in Auto-Reply instead — see CLAUDE.md's "
            "Customer Service section for the 5 ready-made templates."
        ),
        "timeout": 60,
        "long_running": False,
        # Currently always a no-op (see limitation above), but flagged now so a
        # future fix to the underlying API/limitation can't silently ship without
        # this same PII gap -- see check_new_orders' comment for the full reasoning.
        "contains_pii": True,
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


def _username_from_email(email: str) -> str:
    """Derive a hub_users.username candidate from an OAuth email's local-part —
    lowercased, non-alphanumeric stripped to '-'. Never returns empty (falls
    back to 'user' if the local-part strips to nothing, e.g. an all-emoji or
    all-CJK local-part)."""
    local = email.split("@", 1)[0].lower()
    slug = _re.sub(r"[^a-z0-9]+", "-", local).strip("-")
    return slug or "user"


def _find_or_create_oauth_user(provider: str, profile: dict) -> str:
    """Resolves a verified OAuth profile ({"sub","email","email_verified","name"})
    to a hub_users.username, creating an account or linking to an existing one as
    needed. Returns the username to open a session for.

    Linking rule (security-critical): a new OAuth identity is only ever
    auto-linked to an EXISTING password account when the provider says the
    email is verified. An unverified email is never trusted to silently gain
    access to somebody else's existing account — it just gets its own new
    account instead. (Google always verifies Gmail addresses; Apple verifies
    email ownership at the account level for every id_token it issues.)
    """
    sub = profile["sub"]
    email = profile["email"].strip().lower()

    existing_identity = db.get_oauth_identity(provider, sub)
    if existing_identity:
        return existing_identity["username"]

    if profile.get("email_verified"):
        existing_user = db.get_hub_user_by_email(email)
        if existing_user:
            db.create_oauth_identity(provider, sub, existing_user["username"], email)
            return existing_user["username"]

    base = _username_from_email(email)
    username = base
    suffix = 1
    while db.get_hub_user(username):
        suffix += 1
        username = f"{base}{suffix}"

    display_name = (profile.get("name") or "").strip() or None
    # No usable password exists for an OAuth-created account — a random,
    # never-shown 256-bit hash makes password login for it cryptographically
    # impossible rather than merely "not set up yet" (there is no UI to guess
    # against, and this is never displayed or emailed anywhere).
    unusable_pw_hash = _hash_password(secrets.token_urlsafe(32))
    db.create_hub_user(username, unusable_pw_hash, role="admin", email=email, display_name=display_name)
    db.create_oauth_identity(provider, sub, username, email)
    print(f"[auth] OAuth account created via {provider}: '{username}' <{email}>", flush=True)
    return username


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
XAI_KEY = os.getenv("XAI_API_KEY", "").strip()  # 2026-08-05, Grok text + image engine
_SERVER_START = datetime.now(timezone.utc)
_BUILD_ID = "a59c8a1-v340"  # bump on each deploy to confirm Railway is using latest code

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
# OAuth (Google/Apple Sign-In) redirect_uri must be an exact string match against
# whatever's registered in that provider's console — no trailing slash, no path
# drift. PUBLIC_BASE_URL lets a custom domain override the Railway one; falls back
# to localhost for local dev (never used in a real OAuth call there since neither
# provider is reachable from Railway's actual public domain in that case anyway).
_PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/") or (
    f"https://{_RAILWAY_DOMAIN}" if _RAILWAY_DOMAIN else "http://localhost:8000"
)
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


# ── OAuth CSRF state tokens (Google/Apple Sign-In) ──────────────────────────────
#
# Standard OAuth CSRF defense: mint an unguessable, single-use, short-lived token
# before redirecting to the provider, and require it back unchanged on the
# callback. Without this, an attacker could pre-generate their own valid
# authorization code and trick a victim's browser into completing the callback,
# logging the victim into the ATTACKER's account (a real login-CSRF vector for
# OAuth, not theoretical). Same pattern as _new_ws_ticket/_consume_ws_ticket
# above — single-use, in-memory, no need to survive a restart since a login in
# progress across a Railway redeploy is expected to just be retried.
_oauth_states: dict[str, tuple[float, str]] = {}   # state -> (expiry, next_path)
_oauth_states_lock = threading.Lock()
_OAUTH_STATE_TTL = 600  # seconds — generous enough for a slow consent screen


def _new_oauth_state(next_path: str) -> str:
    state = secrets.token_urlsafe(32)
    with _oauth_states_lock:
        _oauth_states[state] = (time.time() + _OAUTH_STATE_TTL, next_path)
    return state


def _consume_oauth_state(state: str) -> str | None:
    """Single-use: returns the original next_path iff state exists and hasn't
    expired, else None (caller must treat None as a hard failure, never fall
    back to a default next path — that would defeat the CSRF check)."""
    with _oauth_states_lock:
        entry = _oauth_states.pop(state, None)
    if entry is None:
        return None
    expiry, next_path = entry
    return next_path if time.time() <= expiry else None


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


def _new_session(username: str, user_agent: str | None = None) -> str:
    sid = secrets.token_urlsafe(32)
    expiry = time.time() + SESSION_TTL
    with _sessions_lock:
        _sessions[sid] = (expiry, username)
    try:
        db.create_session(sid, username, expiry, user_agent=user_agent)
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


# ── Shared auth-page CSS — the Studio Warm design tokens/typography copied
# straight from frank_hud_mockup.py's :root (2026-08-13; the auth pages below
# previously used an unrelated hardcoded teal-on-navy palette that didn't match
# the live app at all). Plain string, not a .format() template — its own braces
# never need escaping since it's substituted as a VALUE into the page templates
# below, not parsed as one. See frank_hud_mockup.py's :root comment for why
# these specific hex values (the 2026-07-15 WCAG-verified brightening pass).
_AUTH_PAGE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
@font-face{font-family:'Sora';font-weight:700;font-style:normal;font-display:swap;
  src:url('/static/vendor/fonts/Sora-700.woff2') format('woff2')}
@font-face{font-family:'IBM Plex Sans';font-weight:400;font-style:normal;font-display:swap;
  src:url('/static/vendor/fonts/IBMPlexSans-400.woff2') format('woff2')}
:root{
  --bg:#241c2e;--panel:#2d2438;--panel2:#372c42;--panel3:#42354e;--border:#3d3248;
  --cyan:#f2a0b5;--cyan2:#f7c3d0;--gold:#e4b155;--gold2:#f2cb8f;--text:#f5eef2;--muted:#bfa3b5;
  --green:#5cc48a;--red:#e2685f;--amber:#e8b868;
  --font-display:'Outfit','Sora',sans-serif;
  --font-body:'Manrope',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --r-sm:8px;--r-md:12px;--r-lg:16px;--r-pill:999px;
  --card-shadow:0 1px 0 rgba(255,255,255,.03) inset,0 2px 10px rgba(0,0,0,.16);
}
html,body{height:100%}
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
  background:var(--bg);color:var(--text);font-family:var(--font-body);padding:24px}
.box{width:380px;max-width:100%;padding:32px 28px 26px;background:var(--panel);
  border:1px solid var(--border);border-radius:var(--r-lg);box-shadow:var(--card-shadow);position:relative}
.box::before,.box::after{content:'';position:absolute;width:14px;height:14px;pointer-events:none;opacity:.55}
.box::before{top:-1px;left:-1px;border-top:2px solid var(--cyan);border-left:2px solid var(--cyan);border-top-left-radius:var(--r-sm)}
.box::after{bottom:-1px;right:-1px;border-bottom:2px solid var(--cyan);border-right:2px solid var(--cyan);border-bottom-right-radius:var(--r-sm)}
.logo{display:flex;align-items:center;gap:10px;margin-bottom:22px}
.logo .hex{width:34px;height:34px;border:2px solid var(--cyan);border-radius:var(--r-sm);display:flex;
  align-items:center;justify-content:center;color:var(--cyan2);font-size:17px;flex-shrink:0;
  box-shadow:0 0 10px rgba(242,160,181,.5)}
.logo .l1{font-family:var(--font-display);font-weight:600;letter-spacing:1px;color:var(--cyan2);font-size:17px;line-height:1.15;
  text-shadow:0 0 10px rgba(242,160,181,.4)}
.logo .l2{font-size:9px;letter-spacing:2px;color:var(--muted);margin-top:1px}
h1.heading{font-family:var(--font-display);font-size:15px;font-weight:700;color:var(--text);margin:0 0 4px}
.hint{font-size:11.5px;color:var(--muted);margin-bottom:18px;line-height:1.5}
label{display:block;font-size:10.5px;font-weight:700;color:var(--muted);text-transform:uppercase;
  letter-spacing:.06em;margin-bottom:6px}
input[type=text],input[type=email],input[type=password]{width:100%;padding:10px 12px;margin-bottom:15px;
  background:var(--bg);border:1px solid var(--border);border-radius:var(--r-sm);color:var(--text);
  font-family:var(--font-body);font-size:14px;outline:none;transition:border-color .15s,box-shadow .15s}
input:focus{border-color:var(--gold);box-shadow:0 0 0 2px rgba(228,177,85,.35)}
button.submit{width:100%;padding:11px;background:var(--gold);border:1px solid var(--gold);border-radius:var(--r-sm);
  color:#2c1a06;font-weight:700;font-size:14px;cursor:pointer;letter-spacing:.03em;margin-top:2px;
  font-family:var(--font-body);transition:background .15s,border-color .15s}
button.submit:hover{background:var(--gold2);border-color:var(--gold2)}
button.submit:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.err{background:rgba(226,104,95,.1);border:1px solid #5a2d3a;border-radius:var(--r-sm);color:#ff9d94;
  font-size:12px;padding:9px 11px;margin-bottom:14px;line-height:1.5}
.warn{background:rgba(232,184,104,.1);border:1px solid #6b501f;border-radius:var(--r-sm);color:var(--amber);
  font-size:12px;padding:10px 12px;margin-bottom:16px;line-height:1.5}
.warn b{color:var(--gold2)}
.cross-link{text-align:center;margin-top:16px}
.cross-link a{color:var(--cyan2);font-size:12px;text-decoration:none}
.cross-link a:hover,.cross-link a:focus-visible{text-decoration:underline}
.once{font-size:10px;color:var(--muted);margin-top:14px;text-align:center;opacity:.8}
.code{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:19px;font-weight:700;
  letter-spacing:2px;color:var(--cyan2);background:var(--bg);border:1px solid var(--border);border-radius:var(--r-sm);
  padding:16px;text-align:center;margin-bottom:18px;user-select:all;word-break:break-all}
a.btn{display:block;width:100%;padding:11px;background:var(--gold);border:1px solid var(--gold);border-radius:var(--r-sm);
  color:#2c1a06;font-weight:700;font-size:14px;text-align:center;text-decoration:none;box-sizing:border-box;
  font-family:var(--font-body)}
a.btn:hover{background:var(--gold2);border-color:var(--gold2)}
.oauth-row{display:flex;flex-direction:column;gap:10px;margin-bottom:18px}
.oauth-btn{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;padding:10px;
  background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-sm);color:var(--text);
  font-family:var(--font-body);font-size:13.5px;font-weight:600;text-decoration:none;cursor:pointer;
  transition:background .15s,border-color .15s}
.oauth-btn:hover,.oauth-btn:focus-visible{background:var(--panel3);border-color:var(--cyan)}
.oauth-btn svg{width:18px;height:18px;flex-shrink:0}
.divider{display:flex;align-items:center;gap:10px;margin:2px 0 18px;color:var(--muted);font-size:10.5px;
  letter-spacing:.06em;text-transform:uppercase}
.divider::before,.divider::after{content:'';flex:1;height:1px;background:var(--border)}
"""

_OAUTH_ICON_GOOGLE = (
    '<svg viewBox="0 0 18 18" aria-hidden="true"><path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481'
    'h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.874 2.684-6.615z"/><path fill="#34A853" d="M9 '
    '18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332'
    'A8.997 8.997 0 0 0 9 18z"/><path fill="#FBBC05" d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71'
    'V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"/><path fill="#EA4335" d="M9 3.58c1.3'
    '21 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163'
    ' 6.656 3.58 9 3.58z"/></svg>'
)
_OAUTH_ICON_APPLE = (
    '<svg viewBox="0 0 384 512" aria-hidden="true" fill="currentColor"><path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-'
    '84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141 4 184.8 4 273.'
    '5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 9'
    '0.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 '
    '34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg>'
)


def _oauth_buttons_html(next_path: str) -> str:
    """Conditionally rendered "Continue with Google/Apple" buttons — empty string
    (no divider either) when neither provider has real credentials configured, so
    the login/signup screens never show a button that would just 404. See
    oauth_providers.py's module docstring for what "configured" requires."""
    buttons = []
    if oauth_providers.GOOGLE_ENABLED:
        buttons.append(
            f'<a class="oauth-btn" href="/auth/google?next={next_path}">{_OAUTH_ICON_GOOGLE}<span>Continue with Google</span></a>'
        )
    if oauth_providers.APPLE_ENABLED:
        buttons.append(
            f'<a class="oauth-btn" href="/auth/apple?next={next_path}">{_OAUTH_ICON_APPLE}<span>Continue with Apple</span></a>'
        )
    if not buttons:
        return ""
    return f'<div class="oauth-row">{"".join(buttons)}</div><div class="divider">or</div>'


_LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{hub_title} — Sign in</title>
<style>{auth_css}</style>
</head>
<body>
  <div class="box">
    <div class="logo">
      <div class="hex" aria-hidden="true">⬡</div>
      <div><div class="l1">{hub_title}</div><div class="l2">OPERATIONS HUB</div></div>
    </div>
    {error_html}
    {oauth_html}
    <form method="post" action="/login" autocomplete="on">
      <input type="hidden" name="next" value="{next_path}">
      <label for="li-user">Username</label>
      <input type="text" id="li-user" name="username" placeholder="Enter your username" autofocus autocomplete="username">
      <label for="li-pass">Password</label>
      <input type="password" id="li-pass" name="password" placeholder="Enter your password" autocomplete="current-password">
      <button type="submit" class="submit">Sign in</button>
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
<style>{auth_css}</style>
</head>
<body>
  <div class="box">
    <div class="logo">
      <div class="hex" aria-hidden="true">⬡</div>
      <div><div class="l1">{hub_title}</div><div class="l2">OPERATIONS HUB</div></div>
    </div>
    <h1 class="heading">Create your account</h1>
    <div class="hint">First-time setup — choose a username and password for the owner account. You won't see this screen again.</div>
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
      <button type="submit" class="submit">Create account &amp; sign in</button>
    </form>
    <div class="once">This is a one-time setup. After this, use your username and password to sign in.</div>
    {signin_link}
  </div>
</body>
</html>"""

# Served on /signup — a normal, ALWAYS-available "create an account" screen, distinct
# from _SETUP_PAGE above (which only ever creates the one-time owner account, gated on
# hub_users being empty). Added 2026-07-18 per Scott: testers he sends the app to were
# hitting an existing-login-only wall with no way to create their own account (the
# owner-only admin panel that could create additional accounts had its UI removed
# 2026-07-11 when this was still a solo shop — see the "Multi-admin section removed"
# comment near the Settings screen). New accounts get role="admin" — the same real
# access level Scott's own account has (his explicit choice: testers should experience
# the real app, not a restricted view) — never "owner", which stays a one-per-shop role.
_SIGNUP_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{hub_title} — Create an account</title>
<style>{auth_css}</style>
</head>
<body>
  <div class="box">
    <div class="logo">
      <div class="hex" aria-hidden="true">⬡</div>
      <div><div class="l1">{hub_title}</div><div class="l2">OPERATIONS HUB</div></div>
    </div>
    <h1 class="heading">Create an account</h1>
    <div class="hint">You'll get full access to the same live shop dashboard, chat, and approvals as everyone else on this account.</div>
    {error_html}
    {oauth_html}
    <form method="post" action="/signup" autocomplete="on">
      <input type="hidden" name="next" value="{next_path}">
      <label for="su-email">Email</label>
      <input type="email" id="su-email" name="email" placeholder="you@example.com" autofocus autocomplete="email" required>
      <label for="su-name">Name</label>
      <input type="text" id="su-name" name="display_name" placeholder="Your name" autocomplete="name" required>
      <label for="su-user">Username</label>
      <input type="text" id="su-user" name="username" placeholder="Choose a username" autocomplete="username" required>
      <label for="su-pass">Password</label>
      <input type="password" id="su-pass" name="password" placeholder="Choose a strong password" autocomplete="new-password" required>
      <label for="su-conf">Confirm password</label>
      <input type="password" id="su-conf" name="confirm_password" placeholder="Repeat your password" autocomplete="new-password" required>
      <button type="submit" class="submit">Create account &amp; sign in</button>
    </form>
    <div class="cross-link"><a href="/login?next={next_path}">Already have an account? Sign in instead</a></div>
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
<style>{auth_css}</style>
</head>
<body>
  <div class="box">
    <div class="logo">
      <div class="hex" aria-hidden="true">⬡</div>
      <div><div class="l1">{hub_title}</div><div class="l2">OPERATIONS HUB</div></div>
    </div>
    <h1 class="heading">Save your account recovery code</h1>
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
<style>{auth_css}</style>
</head>
<body>
  <div class="box">
    <div class="logo">
      <div class="hex" aria-hidden="true">⬡</div>
      <div><div class="l1">{hub_title}</div><div class="l2">OPERATIONS HUB</div></div>
    </div>
    <h1 class="heading">Reset your password</h1>
    <div class="hint">Enter your username, the recovery code you saved when the account was created, and a new password.</div>
    {error_html}
    <form method="post" action="/forgot-password" autocomplete="off">
      <label for="fp-user">Username</label>
      <input type="text" id="fp-user" name="username" autofocus autocomplete="username" required>
      <label for="fp-code">Recovery code</label>
      <input type="text" id="fp-code" name="recovery_code" placeholder="XXXX-XXXX-XXXX" autocomplete="off" required>
      <label for="fp-pass">New password</label>
      <input type="password" id="fp-pass" name="new_password" autocomplete="new-password" required>
      <button type="submit" class="submit">Reset password</button>
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
                               persist_warning=persist_warning, signin_link=signin_link, auth_css=_AUTH_PAGE_CSS),
            headers=no_cache,
        )
    if error == "noaccount":
        error_html = '<div class="err">No account exists yet with that username. Use "Create one instead" below, or ask the owner to set one up.</div>'
    else:
        error_html = '<div class="err">Incorrect username or password. Try again.</div>' if error else ""
    # Always offer a way to create an account once an owner already exists (2026-07-18:
    # previously this only showed while hub_users was empty, i.e. only ever once —
    # afterward every new visitor hit a dead-end "existing login only" screen with no
    # way in, which is exactly what Scott's testers ran into). Points at /signup, the
    # always-available self-service flow, not this same /login setup-mode path.
    cross_link = (
        f'<div class="cross-link"><a href="/login?next={safe_next}">First time? Create an account instead</a></div>'
        if empty else
        f'<div class="cross-link"><a href="/signup?next={safe_next}">New here? Create an account</a></div>'
    )
    return HTMLResponse(
        _LOGIN_PAGE.format(error_html=error_html, next_path=safe_next, hub_title=business_config.BUSINESS_NAME,
                           cross_link=cross_link, oauth_html=_oauth_buttons_html(safe_next), auth_css=_AUTH_PAGE_CSS),
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
            sid = _new_session(uname, user_agent=request.headers.get("user-agent"))
            no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate"}
            resp = HTMLResponse(
                _RECOVERY_CODE_PAGE.format(hub_title=business_config.BUSINESS_NAME,
                                           recovery_code=recovery_code, username=uname, next_path=safe_next,
                                           auth_css=_AUTH_PAGE_CSS),
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
        sid = _new_session(uname, user_agent=request.headers.get("user-agent"))
        resp = RedirectResponse(safe_next, status_code=303)
        resp.set_cookie(SESSION_COOKIE, sid, httponly=True, secure=True, samesite="lax")
        return resp
    _record_login_fail(uname)
    return RedirectResponse(f"/login?error=1&next={safe_next}", status_code=303)


@app.get("/signup", response_class=HTMLResponse)
def signup_page(next: str = "/", error: str = ""):
    """Self-service account creation (2026-07-18) — always available once an owner
    account exists, unlike _SETUP_PAGE which is a strict one-time-only flow. If no
    owner exists yet, redirect to /login instead of creating an admin account with
    no owner ever having existed — the very first account on a fresh install must
    still go through the existing owner-setup flow."""
    safe_next = _safe_next(next)
    if db.hub_users_empty():
        return RedirectResponse(f"/login?next={safe_next}", status_code=303)
    no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate"}
    error_html = f'<div class="err">{error}</div>' if error else ""
    return HTMLResponse(
        _SIGNUP_PAGE.format(error_html=error_html, next_path=safe_next, hub_title=business_config.BUSINESS_NAME,
                            oauth_html=_oauth_buttons_html(safe_next), auth_css=_AUTH_PAGE_CSS),
        headers=no_cache,
    )


@app.post("/signup")
def signup_submit(
    request: Request,
    email: str = Form(""),
    display_name: str = Form(""),
    username: str = Form(""),
    password: str = Form(""),
    confirm_password: str = Form(""),
    next: str = Form("/"),
):
    safe_next = _safe_next(next)

    def _err(msg: str) -> RedirectResponse:
        return RedirectResponse(f"/signup?error={quote(msg)}&next={safe_next}", status_code=303)

    # Same "no owner yet" guard as the GET route -- a POST could arrive here from a
    # stale tab even after the table went from non-empty back to empty (e.g. the
    # owner account was somehow removed), so re-check rather than trusting the form.
    if db.hub_users_empty():
        return RedirectResponse(f"/login?next={safe_next}", status_code=303)

    email = email.strip().lower()
    display_name = display_name.strip()
    uname = username.strip().lower()
    pw = password.strip()
    cpw = confirm_password.strip()

    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return _err("Enter a valid email address")
    if not display_name:
        return _err("Enter your name")
    if not uname:
        return _err("Choose a username")
    if not pw:
        return _err("Choose a password")
    if pw != cpw:
        return _err("Passwords do not match")
    if len(pw) < _MIN_PASSWORD_LEN:
        return _err(f"Password must be at least {_MIN_PASSWORD_LEN} characters")
    if db.get_hub_user(uname):
        return _err(f"Username '{uname}' is already taken")

    # New self-service accounts get role="admin" -- the same real access level the
    # owner has (Scott's explicit choice, 2026-07-18: testers should experience the
    # real app, not a restricted view). "owner" stays a one-per-shop role, created
    # only via the first-run _SETUP_PAGE flow above.
    recovery_code = _generate_recovery_code()
    db.create_hub_user(uname, _hash_password(pw), role="admin",
                        recovery_code_hash=_hash_password(recovery_code),
                        email=email, display_name=display_name)
    print(f"[auth] self-service account created: '{uname}' <{email}>", flush=True)
    sid = _new_session(uname, user_agent=request.headers.get("user-agent"))
    no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate"}
    resp = HTMLResponse(
        _RECOVERY_CODE_PAGE.format(hub_title=business_config.BUSINESS_NAME,
                                   recovery_code=recovery_code, username=uname, next_path=safe_next,
                                   auth_css=_AUTH_PAGE_CSS),
        headers=no_cache,
    )
    resp.set_cookie(SESSION_COOKIE, sid, httponly=True, secure=True, samesite="lax")
    return resp


@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(error: str = ""):
    error_html = ""
    if error == "badcode":
        error_html = '<div class="err">Username or recovery code is incorrect.</div>'
    elif error == "short":
        error_html = f'<div class="err">New password must be at least {_MIN_PASSWORD_LEN} characters.</div>'
    no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate"}
    return HTMLResponse(
        _FORGOT_PASSWORD_PAGE.format(hub_title=business_config.BUSINESS_NAME, error_html=error_html,
                                     auth_css=_AUTH_PAGE_CSS),
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


def _oauth_login_error_redirect(next_path: str, message: str) -> RedirectResponse:
    # Deliberately generic in what's shown to the browser (message is a fixed,
    # non-leaky string from each call site below, never the raw provider/
    # exception text) -- the specific failure still goes to the server log via
    # the OAuthError callers already print before calling this.
    return RedirectResponse(f"/login?error={quote(message)}&next={_safe_next(next_path)}", status_code=303)


@app.get("/auth/google")
def auth_google_start(next: str = "/"):
    if not oauth_providers.GOOGLE_ENABLED:
        raise HTTPException(status_code=404, detail="Google Sign-In is not configured")
    state = _new_oauth_state(_safe_next(next))
    redirect_uri = _PUBLIC_BASE_URL + "/auth/google/callback"
    return RedirectResponse(oauth_providers.google_authorize_url(state, redirect_uri), status_code=303)


@app.get("/auth/google/callback")
def auth_google_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    next_path = _consume_oauth_state(state)
    if next_path is None:
        return _oauth_login_error_redirect("/", "Sign-in session expired or invalid. Please try again.")
    if error or not code:
        return _oauth_login_error_redirect(next_path, "Google sign-in was cancelled or failed.")
    redirect_uri = _PUBLIC_BASE_URL + "/auth/google/callback"
    try:
        profile = oauth_providers.google_exchange_code(code, redirect_uri)
    except oauth_providers.OAuthError as exc:
        print(f"[auth] Google OAuth failed: {exc}", flush=True)
        return _oauth_login_error_redirect(next_path, "Google sign-in failed. Please try again.")
    username = _find_or_create_oauth_user("google", profile)
    sid = _new_session(username, user_agent=request.headers.get("user-agent"))
    resp = RedirectResponse(next_path, status_code=303)
    resp.set_cookie(SESSION_COOKIE, sid, httponly=True, secure=True, samesite="lax")
    return resp


@app.get("/auth/apple")
def auth_apple_start(next: str = "/"):
    if not oauth_providers.APPLE_ENABLED:
        raise HTTPException(status_code=404, detail="Apple Sign-In is not configured")
    state = _new_oauth_state(_safe_next(next))
    redirect_uri = _PUBLIC_BASE_URL + "/auth/apple/callback"
    return RedirectResponse(oauth_providers.apple_authorize_url(state, redirect_uri), status_code=303)


@app.post("/auth/apple/callback")
def auth_apple_callback(
    request: Request,
    code: str = Form(""),
    state: str = Form(""),
    error: str = Form(""),
):
    # Apple requires response_mode=form_post whenever "name"/"email" scopes are
    # requested (see oauth_providers.apple_authorize_url) -- this callback is a
    # POST from appleid.apple.com's own server-rendered consent page, not a
    # link a browser navigated to directly.
    next_path = _consume_oauth_state(state)
    if next_path is None:
        return _oauth_login_error_redirect("/", "Sign-in session expired or invalid. Please try again.")
    if error or not code:
        return _oauth_login_error_redirect(next_path, "Apple sign-in was cancelled or failed.")
    redirect_uri = _PUBLIC_BASE_URL + "/auth/apple/callback"
    try:
        profile = oauth_providers.apple_exchange_code(code, redirect_uri)
    except oauth_providers.OAuthError as exc:
        print(f"[auth] Apple OAuth failed: {exc}", flush=True)
        return _oauth_login_error_redirect(next_path, "Apple sign-in failed. Please try again.")
    username = _find_or_create_oauth_user("apple", profile)
    sid = _new_session(username, user_agent=request.headers.get("user-agent"))
    resp = RedirectResponse(next_path, status_code=303)
    resp.set_cookie(SESSION_COOKIE, sid, httponly=True, secure=True, samesite="lax")
    return resp


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
                # 2026-07-31 (Today UX audit): stale/stale_reason were already threaded
                # this far but the frontend had no consumer for either -- confirmed via
                # a full-repo grep, zero live callers ever checked them, so a stale cache
                # payload rendered indistinguishably from a fresh one (worse: Today's
                # count-up tile animation actively sold it as "just measured"). Adding a
                # real as-of timestamp (not just a boolean) lets the frontend reuse its
                # existing _offlineNote(ts) pattern verbatim instead of inventing new copy.
                with _cache_lock:
                    stale_ts = (_cache.get(cache_key) or {}).get("ts")
                stale = {
                    **stale,
                    "stale": True,
                    "stale_reason": str(exc)[:200],
                    "stale_as_of": datetime.fromtimestamp(stale_ts, tz=timezone.utc).isoformat() if stale_ts else None,
                }
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

# ── Bambu P1S printer telemetry (2026-07-29) ────────────────────────────────
# This Railway container has no route to Scott's home LAN, so it can never
# open a direct MQTT connection to the printer itself. A small standalone
# bridge process (tools/relay/bambu_p1s_bridge.py — same deployment shape as
# frank_relay.py above) runs on Scott's own network, talks to the P1S over
# local MQTT, and pushes a JSON snapshot + occasional camera frame here via
# POST /api/printer/telemetry / /api/printer/camera-frame. In-memory only,
# same tradeoff as _relay_ws above: a redeploy just means "bridge offline"
# until its next push — no durability needed for live device state, and
# nothing here ever touches an Etsy listing or spends money, so this is
# read-only monitoring, not a staged action.
_printer_lock = threading.Lock()
_printer_telemetry: dict | None = None
_printer_telemetry_at: float = 0.0
_printer_frame: bytes | None = None
_printer_frame_at: float = 0.0
# 2026-07-30: was 30s, matching the HUD's old 30s poll cadence exactly -- zero
# margin, so any single missed poll (network jitter, a backgrounded browser tab
# getting its timers throttled, a slow Railway request) flipped the card to
# "BRIDGE OFFLINE" even though the bridge was still pushing every ~3s. 90s
# gives real headroom over both the bridge's push interval and the HUD's
# (now 5s-while-visible) poll cadence.
_PRINTER_STALE_SECS = 90
# Camera frames arrive much faster than telemetry once connected (many/sec,
# not debounced to 3s) -- a much tighter window here means a genuinely stuck
# camera relay is surfaced quickly instead of serving a very stale frame.
_PRINTER_CAMERA_STALE_SECS = 15
_PRINTER_MAX_FRAME_BYTES = 3_000_000

# 2026-07-21: _execute_agent_tool() dispatches to dozens of branches -- some are
# subprocess.run() calls bounded by their own _EXEC_COMMANDS timeout (max 400s
# today), but others call external SDKs/CLIs with NO bound at all (e.g.
# video_understanding.py's yt-dlp download and Gemini file-upload poll loop have
# zero timeout of their own). _dispatch_to_relay already can't hang past 15s and
# _stage_local_action's only blocking call IS _dispatch_to_relay, so both of those
# paths were already safe -- this is a ceiling for the third path
# (asyncio.to_thread(_execute_agent_tool, ...)), so a tool with a missing or
# misbehaving internal timeout can't wedge the whole chat turn (and the shared
# to_thread executor pool) forever. Sized above the longest known legitimate
# subprocess timeout (400s) with headroom.
_TOOL_DISPATCH_TIMEOUT_S = 480.0


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
    logging failure must never break the caller.

    Dedup guard (2026-07-18): every health-loop failure path funnels through
    this one function with zero dedup, which is how an unresolved, unchanged
    failure firing every 5 minutes turned into 428 byte-identical entries for
    a single issue (see ops_runbook.md's own 2026-07-18 cleanup entry). Before
    appending, check whether the LAST heading already in the file is this
    exact heading logged today (UTC) -- if so, skip the append entirely rather
    than writing a duplicate. Only the file's tail is read (a few KB) to keep
    this cheap on a hot path. Genuine day-over-day recurrence still surfaces
    via _promote_recurring_failures()'s "Known Recurring Issues" summary --
    this guard only kills same-day, same-heading spam."""
    try:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        expected_line = f"## {stamp} — {heading}"
        try:
            with open(_OPS_RUNBOOK_PATH, "rb") as fh:
                fh.seek(0, os.SEEK_END)
                size = fh.tell()
                fh.seek(max(0, size - 4000))
                tail = fh.read().decode("utf-8", errors="ignore")
            last_heading_line = None
            for line in tail.splitlines():
                if line.startswith("## ") and " — " in line:
                    last_heading_line = line
            if last_heading_line == expected_line:
                return  # identical heading already logged today -- skip the duplicate
        except OSError:
            pass  # file may not exist yet -- fall through and create it
        entry = f"\n\n{expected_line}\n{body}\n"
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
    return {
        "total_sessions": len(sessions),
        "total_messages": total_messages,
        "oldest_at": min(started) if started else None,
        "newest_at": max(lasts) if lasts else None,
        "kb_doc_count": len(kb_docs),
        "learnings_count": len(learnings),
        "learnings": learnings[:20],
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

IDENTIFIER LOOKUP — the instant {business_config.OWNER_NAME} sends you a bare identifier with little
or no other context — a numeric Etsy listing ID, an internal product code (DP1026, SS1001,
WA1030, CB001, etc.), or just a product name fragment — call get_product with it BEFORE
replying. Never say "I don't know what that is" or ask what he means without trying this
first; it cross-references the internal product catalog (files on disk, category, price,
past operational notes) AND the live Etsy listing in one call, so a bare ID alone is always
enough to identify the product. Use plain get_listing only when you already know for certain
you're dealing with a live Etsy listing_id and specifically need Etsy's raw fields.

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
        # 2026-08-06 ("Growth Brief", idea 2/3 of the Frank improvement roadmap):
        # synthesizes Ads/COGS/Star Seller/seasonal keywords/bundle opportunities/
        # Conversion Doctor into one ranked list instead of Scott having to check
        # 5+ separate panels and mentally combine them himself.
        "name": "get_growth_brief",
        "description": (
            "Ranked, dollar-impact-scored list of what to prioritize this week, "
            "synthesized from Ads/ROAS, COGS margin, Star Seller status, seasonal "
            "keyword windows, bundle opportunities, and Conversion Doctor listing "
            "issues. Each item's est_dollar_impact is either a REAL number (ad spend, "
            "logged revenue, Star Seller's trailing-90-day revenue at stake) or null "
            "with impact_basis explaining why no dollar figure was estimated -- never "
            "fabricated. Call this when asked 'what should I focus on' or similar."
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
        "name": "get_product",
        "description": (
            f"THE tool to reach for the instant {business_config.OWNER_NAME} pastes ANY product identifier "
            "with no other context — a bare Etsy listing_id number, an internal product code "
            "(DP1026, SS1001, WA1030, CB001, etc.), or a partial product name. Never respond "
            "'I don't know what that is' without calling this first. Unlike get_listing (Etsy's "
            "live fields only), this cross-references data/product_catalog.json — the shop's own "
            "source of truth — so it returns the internal product_id, category, price, which files "
            "exist on disk, and any operational note logged against this product (e.g. a past bug "
            "fix or re-upload reason), PLUS the live Etsy listing (title, state, price, tags, views, "
            "favorites) when the product has one. If the identifier isn't in the catalog but IS a "
            "real numeric Etsy listing_id, still returns the live Etsy data with in_catalog=false so "
            "you're never blind to an un-catalogued or newly-created listing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": (
                        "A numeric Etsy listing_id, an internal product code (e.g. 'DP1026'), or a "
                        "product name/fragment to search for."
                    ),
                }
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "stage_action",
        "description": (
            f"Stage a proposed change for {business_config.OWNER_NAME}'s one-tap approval. You do NOT execute "
            "it — it lands in the approval queue (Action Center) and only applies to "
            f"Etsy when {business_config.OWNER_NAME} taps Approve. Use for fixes you can fully specify: "
            "correcting a listing title, replacing its tags, or publishing a draft. "
            "Always fetch the listing first so your change is accurate.\n\n"
            "action_type='register_product' is different from the rest — it's a pure local "
            "catalog write (no Etsy API call at all), for a product whose files/photos already "
            "exist OUTSIDE the build_product pipeline (e.g. a physical/manually-produced item, "
            "or a listing that's live on Etsy but was never registered here). Use it when asked "
            "to register/add/catalog a product that isn't going through build_product."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": [
                        "update_tags", "update_title", "update_description", "publish_listing",
                        "deactivate_listing", "toggle_listing_state", "update_price",
                        "update_sku_and_category", "register_product",
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
                "price": {
                    "type": "number",
                    "description": (
                        "New price in dollars for update_price. Must end in .99, .97, or .49 "
                        "(OnBrandCraftz pricing convention) — CLAUDE.md hard-stops price "
                        f"changes on more than 5 listings in one session; for more than one "
                        "listing use stage_batch_price_update instead, which enforces that cap."
                    ),
                },
                "sku": {
                    "type": "string",
                    "description": (
                        "New SKU for update_sku_and_category — OnBrandCraftz convention is "
                        "the product's product_catalog.json product_id (e.g. 'DP1026')."
                    ),
                },
                "taxonomy_id": {
                    "type": "integer",
                    "description": "New Etsy taxonomy_id (category) for update_sku_and_category.",
                },
                "product_id": {
                    "type": "string",
                    "description": (
                        "For register_product: the internal product code (e.g. 'P3D0042'). "
                        "Optional — auto-generated from name + category convention if omitted."
                    ),
                },
                "name": {
                    "type": "string",
                    "description": "For register_product: the product's display name. Required.",
                },
                "category": {
                    "type": "string",
                    # Literal, not a reference to _KNOWN_CATEGORIES (main.py:5483) -- that set is
                    # defined well after AGENT_TOOLS is built, so a dynamic reference here would
                    # NameError at import time. Keep in sync by hand if _KNOWN_CATEGORIES changes.
                    "enum": [
                        "digital_planner", "digital_planner_bundle", "wall_art", "wall_art_bundle",
                        "sticker_pack", "sticker_pack_license", "svg_bundle", "svg_bundle_license",
                        "svg_3dprint_pack", "paper_pack", "coloring_pages", "sublimation",
                        "3d_print_physical", "uncategorized",
                    ],
                    "description": "For register_product: this shop's internal category. Required.",
                },
                "etsy_listing_id": {
                    "type": "integer",
                    "description": (
                        "For register_product: this product's live Etsy listing_id, if it "
                        "already has one. Omit for a not-yet-published product."
                    ),
                },
                "reason": {
                    "type": "string",
                    "description": (
                        "REQUIRED for update_title/update_tags/update_description when the "
                        f"listing_id has no entry in Frank's product manifest/registry -- state "
                        f"what's actually wrong with the listing (e.g. {business_config.OWNER_NAME}'s "
                        "own feedback, or a specific concrete defect you observed). Without this, "
                        "staging a content rewrite for an unmapped listing is refused, since Frank "
                        "has no grounding for what the product actually is and a rewrite would just "
                        "be a more confident-sounding guess."
                    ),
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
        "name": "run_catalog_reconciliation",
        "description": (
            "Check every live active Etsy listing against Frank's local catalog right now "
            "(instead of waiting for the automatic weekly pass) and stage a register_product "
            "action for any listing Frank has no local record of at all -- this is how the "
            "koozie/planner listing-mismatch bug (2026-08-05) was caught: 3 live listings "
            f"existed with zero local record. Never auto-registers anything; every stage is "
            f"{business_config.OWNER_NAME}'s to approve or correct in the Action Center. Capped at "
            "10 new stages per call (matches _RECONCILIATION_BATCH_SIZE) -- run it again to "
            "process more if there's a larger backlog."
        ),
        "input_schema": {"type": "object", "properties": {}},
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
        "name": "stage_batch_price_update",
        "description": (
            "Stage a price change across up to 5 listings at once — e.g. \"raise all "
            f"wall-art prices $2.\" Each listing is staged as its own independent Action "
            f"Center entry — {business_config.OWNER_NAME} approves or rejects each one "
            "individually, never all-or-nothing. Provide either new_price (same absolute "
            "price for every listing) or price_delta (added to each listing's current "
            "price — e.g. +2.00 or -1.00), never both. Every resulting price must still "
            "end in .99, .97, or .49 (OnBrandCraftz pricing convention) — a delta or "
            "absolute price that breaks this on a given listing is rejected for that "
            "listing only, the rest still stage. CLAUDE.md hard-caps price changes at 5 "
            "listings per session; requests for more listing_ids are refused outright — "
            f"split the batch and ask {business_config.OWNER_NAME} which subset to run "
            "first instead of guessing scope."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Listing IDs to reprice. Max 5 per call (CLAUDE.md hard cap).",
                },
                "new_price": {
                    "type": "number",
                    "description": (
                        "Absolute new price in dollars, applied to every listing. "
                        "Mutually exclusive with price_delta."
                    ),
                },
                "price_delta": {
                    "type": "number",
                    "description": (
                        "Dollar amount to add to (or, if negative, subtract from) each "
                        "listing's current live price. Mutually exclusive with new_price."
                    ),
                },
                "summary": {
                    "type": "string",
                    "description": "Optional shared context shown on each approval card.",
                },
            },
            "required": ["listing_ids"],
        },
    },
    {
        "name": "stage_batch_listing_state",
        "description": (
            "Stage an activate/deactivate change across up to 10 listings at once — e.g. "
            "\"republish the 6 expired planners.\" Setting new_state to 'active' on an "
            "expired listing is how Etsy renews it (restarts the 4-month listing clock, "
            "charges the $0.20 renewal fee, and republishes it in search — Etsy has no "
            "separate renew endpoint, this PATCH is the renewal). Each listing is staged "
            f"as its own independent Action Center entry — {business_config.OWNER_NAME} "
            "approves or rejects each one individually, never all-or-nothing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Listing IDs to activate/deactivate/renew. Max 10 per call.",
                },
                "new_state": {"type": "string", "enum": ["active", "inactive"]},
                "summary": {
                    "type": "string",
                    "description": "Optional shared context shown on each approval card.",
                },
            },
            "required": ["listing_ids", "new_state"],
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
        "name": "apply_conversion_fixes",
        "description": (
            "Diagnose a listing's conversion problem AND stage a fix for each "
            "actionable finding, in one call — closes the loop between "
            "diagnose_listing_conversion (which used to be read-only advice that "
            "went nowhere) and the title/tags/description autofix tools (each "
            "already real and reason-aware). For every diagnosis finding in the "
            "title/tags/description areas, stages the matching fix using that "
            "finding as corrective guidance — nothing is applied directly, every "
            f"fix lands in the Action Center for {business_config.OWNER_NAME}'s "
            "one-tap approval. Findings in the photos/price/trust areas are "
            "surfaced in the response but never auto-staged — no code path "
            "regenerates photos or changes price from a diagnosis finding, and "
            "price changes are separately hard-capped at 5/session regardless."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "integer", "description": "The listing to diagnose and fix."},
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "get_comparable_listings",
        "description": (
            "Search real, live Etsy listings by keyword — the shop's only source "
            "of real external market data (price/title/tag evidence from actual "
            "competitors), for backing a pricing or title/tag recommendation with "
            "real comparables instead of a static rule. Uses Etsy's real public "
            "search API (shops/{id}/listings replaced with the site-wide "
            "listings/active endpoint) — public API key only, no OAuth or "
            "scraping involved, no ToS risk. Read-only."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keywords": {"type": "string", "description": "Search keywords, e.g. 'kawaii digital planner goodnotes'."},
                "limit": {"type": "integer", "description": "Max results, default 10, capped at 25."},
                "min_price": {"type": "number", "description": "Optional minimum price filter in dollars."},
                "max_price": {"type": "number", "description": "Optional maximum price filter in dollars."},
            },
            "required": ["keywords"],
        },
    },
    {
        "name": "deep_research",
        "description": (
            "Iterative, multi-round web research on any topic — generates search "
            "queries, researches each via web search, extracts learnings, and goes "
            "deeper based on what it finds, then compiles a sourced markdown report "
            "saved to the Files tab. Use for open-ended research questions that need "
            "more than a single web search (e.g. 'research the top competitors "
            "selling ADHD planners on Etsy and their pricing strategies', or a "
            "general market/trend question with no Etsy-specific angle). Costs "
            "multiple LLM calls (breadth × depth + 1) and can take a minute or more "
            "to finish — use get_comparable_listings/search_etsy first for anything "
            "Etsy-specific and cheap; reserve this for broader research that "
            "genuinely needs multiple search rounds. Read-only — writes only an "
            "internal report file, touches no Etsy listing, contacts no buyer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The research question."},
                "breadth": {
                    "type": "integer",
                    "description": "How many distinct search queries to research per round. Default 4, max 6.",
                    "minimum": 2, "maximum": 6,
                },
                "depth": {
                    "type": "integer",
                    "description": "How many research rounds to run, each going deeper based on prior findings. Default 2, max 3.",
                    "minimum": 1, "maximum": 3,
                },
            },
            "required": ["query"],
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
            "Build an ENTIRE product end to end, in the BACKGROUND (each deliverable appears "
            "in Files as it finishes; <pid>_*_build.log carries the live log + final QC "
            "verdict). Nothing is published (Scott-gated). Dispatches by category — pass "
            "`category` explicitly, or omit it and it's looked up from product_catalog.json "
            "by `pid`:\n"
            "  • digital_planner (default when uncatalogued): sticker pack → planner PDFs "
            "(dated + undated) → all 10 listing photos → QC. Configured codes only "
            "(DP1030-DP1034) — pid required.\n"
            "  • wall_art: multi-size print ZIP → QC. If WA-code source art already exists on "
            "disk, just pass pid. For a BRAND-NEW wall-art product with no source art yet, "
            "also pass `description` (what to generate) — real new art is created first via "
            "the approved-engine pipeline, then QC'd; optionally pass `reference_image_id` "
            "(from the Reference Photos library) to steer the art's style.\n"
            "  • coloring_pages: for an EXISTING catalogued set, pass pid alone. For a NEW "
            "theme set, pid is optional (a fresh COLOR#### code is picked automatically) — "
            "pass `description` as ONE theme (e.g. 'ocean animals'), which expands into a "
            "full set of never-before-repeated individual subjects automatically. Optionally "
            "pass `difficulty` (standard/kids/adult — kids and adult use different line "
            "weight and engine defaults, never mix tiers in one set).\n"
            "  • wall_calendar: pid + `theme` (one of the configured calendar themes) + "
            "optional `year` (defaults to next year). Generates 12 header illustrations, "
            "dated + undated monthly-grid PDFs (both week-start variants), and a "
            "year-at-a-glance poster, then QC.\n"
            "Any category whose art is freshly AI-generated in this call returns "
            "needs_visual_qc:true — eyeball the result for garbled text/wrong subject before "
            "it goes further, no file-level gate catches that. Use when asked to build/make/"
            "produce a whole product, a new product idea, or 'everything' for a code — for "
            "any category, not just planners."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pid": {"type": "string",
                        "description": "Product code, e.g. 'DP1030', 'WA1030'. Optional only "
                                       "for a brand-new coloring_pages set (auto-assigned)."},
                "category": {"type": "string",
                             "enum": ["digital_planner", "wall_art", "coloring_pages", "wall_calendar"],
                             "description": "Explicit category. Omit to auto-detect from "
                                            "product_catalog.json via pid (falls back to "
                                            "digital_planner if pid isn't catalogued)."},
                "description": {"type": "string",
                                 "description": "Required to generate brand-new art: for "
                                                "wall_art, a description of the art to create; "
                                                "for coloring_pages, ONE theme to expand into a "
                                                "full new subject set. Not used for "
                                                "digital_planner or wall_calendar."},
                "theme": {"type": "string",
                          "description": "Required for wall_calendar — the calendar theme key "
                                         "(see the Color Design System theme catalog in "
                                         "CLAUDE.md/read_knowledge_base_doc for the live list)."},
                "year": {"type": "integer",
                         "description": "wall_calendar only. Defaults to next year if omitted."},
                "difficulty": {"type": "string", "enum": ["standard", "kids", "adult"],
                               "description": "coloring_pages only, new sets. Defaults to "
                                              "'standard'. Never mix tiers within one set."},
                "reference_image_id": {"type": "string",
                                        "description": "wall_art only, new art. Optional id from "
                                                       "the Reference Photos library — its style "
                                                       "(not its subject) guides the new art."},
                "engine": {"type": "string", "enum": ["gemini", "openai", "gpt-image-2", "ideogram", "grok"],
                           "description": "Art engine for whatever this call generates. Default "
                                          "'gemini' (coloring_pages instead defaults 'openai' "
                                          "for kids difficulty, 'grok' for teen/adult, unless "
                                          "set explicitly here)."},
            },
            "required": [],
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
        "name": "render_openscad_model",
        "description": (
            "Render a genuinely 3D (non-flat) printable object — write real OpenSCAD code "
            "yourself in this call and this renders it to a mesh file via the openscad CLI. "
            "For a real parametric shape (a vase, an organizer, a holder, a bracket — "
            "anything CAD-like), not for the flat multi-color signs the SS-series SVG-pack "
            "pipeline already covers (use that pipeline for signs instead). Output feeds the "
            "3d_print_physical catalog category — Scott prints and ships it himself on the "
            "Bambu P1S; this never touches Etsy or publishes anything. Write clean, "
            "parametric OpenSCAD (use variables for every dimension, not magic numbers) so "
            "the design is genuinely resizable later. Requires the `openscad` system binary "
            "on this deploy — if it isn't installed, this returns a clear error rather than "
            "a bare crash; tell Scott it needs `apt-get install openscad` if that happens. "
            "Use when asked to design/model/generate a 3D-printable object from a "
            "description, not just a flat sign."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scad_source": {
                    "type": "string",
                    "description": "The complete OpenSCAD script to render, written by you.",
                },
                "output_name": {
                    "type": "string",
                    "description": "Filename for the rendered mesh, e.g. 'desk_organizer_v1'. "
                                   "No extension — the format param picks it.",
                },
                "format": {
                    "type": "string", "enum": ["stl", "3mf", "off", "amf"],
                    "description": "Output mesh format. Default 'stl' (universal — every "
                                   "slicer including Bambu Studio imports it directly).",
                },
                "params": {
                    "type": "object",
                    "description": "Optional -D variable overrides, e.g. {\"height\": \"40\"}. "
                                   "Values are passed to OpenSCAD verbatim — a string variable "
                                   "needs literal quotes inside the value, e.g. '\"Custom Text\"'.",
                },
            },
            "required": ["scad_source", "output_name"],
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
        "name": "create_calendar_event",
        "description": (
            f"Create an event on {business_config.OWNER_NAME}'s connected Google Calendar — use this when "
            f"he asks conversationally to add something to his calendar. Requires Google "
            "Calendar to already be connected (run tools/google_calendar_oauth.py) — if "
            "not connected, this returns a clear error explaining that, not a crash. "
            "Low-risk and immediate, not staged through the Approvals system."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event title."},
                "when": {
                    "type": "string",
                    "description": (
                        "ISO date ('2026-07-25') for an all-day event, or ISO datetime "
                        "('2026-07-25T14:00:00-04:00') for a timed event."
                    ),
                },
                "description": {"type": "string", "description": "Optional event notes."},
            },
            "required": ["summary", "when"],
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

# Tax & Compliance -- tools/tax_compliance_tools.py already imported above for
# its _get_tax_calendar() helper (used by the Calendar screen). Its chat-tool
# layer (TOOL_DEFINITIONS/execute_tool()) was never wired in (2026-08-06
# full-system audit, same "real module, dead chat-tool layer" bug class
# etsy_ads_tools.py had before its own 2026-07-09 fix above). Originally only
# 4 of its 8 tools were wired here (log_deductible_expense/get_deductions_
# summary/check_copyright_guidance/get_tax_calendar -- these never needed
# real Etsy data). The other 4 (get_tax_overview, calculate_quarterly_tax,
# get_1099k_status, check_etsy_compliance) DID depend on DataStore's
# unpopulated shop_data.json analytics/listings and were left unwired --
# now rerouted (same day) to pull real numbers instead: gross_ytd from a
# real date-scoped Etsy receipts fetch (_get_ytd_orders_raw(), same shape as
# Movement Digest's own real receipts fetch) and real live listings for
# compliance checks. tax_compliance_tools.execute_tool() now REQUIRES a
# real_data dict for these 4 (raises rather than silently defaulting to
# zero) -- see that module's own comment on why.
_TAX_REAL_DATA_TOOL_NAMES = {"get_tax_overview", "calculate_quarterly_tax", "get_1099k_status", "check_etsy_compliance"}
_TAX_SAFE_TOOL_NAMES = {"log_deductible_expense", "get_deductions_summary", "check_copyright_guidance", "get_tax_calendar"} | _TAX_REAL_DATA_TOOL_NAMES
AGENT_TOOLS.extend([t for t in tax_compliance_tools.TOOL_DEFINITIONS if t["name"] in _TAX_SAFE_TOOL_NAMES])

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
# Review reply drafting (2026-08-06, "Instant Message Response Assistant") --
# on-demand counterpart to the hourly _review_reply_loop() background job, so
# Scott can ask "any new reviews?" mid-conversation instead of waiting for the
# next hourly pass or the digest email. Read-only from the agent's perspective
# (drafts + emails Scott himself; never posts anything to Etsy, which has no
# review-response endpoint to post to anyway -- see the loop's own comment).
AGENT_TOOLS.append({
    "name": "draft_review_replies",
    "description": (
        "Check Etsy for any new reviews since the last check, draft a personalized "
        f"reply for each with Claude, and email {business_config.OWNER_NAME} the drafts "
        "(same digest _review_reply_loop() sends hourly in the background). Read-only "
        "from Etsy's perspective -- Etsy has no review-response API to post to, so "
        "every draft is copy-paste only. Safe to run as often as asked; already-drafted "
        "or already-replied reviews are skipped."
    ),
    "input_schema": {"type": "object", "properties": {}},
})
# Title A/B testing (2026-08-06, "significantly improve Frank" idea 3/3) --
# see the full module comment above _AB_TESTS_PATH for the scope note (title
# only, not photo) and the ranking-recovery-driven minimum rotation window.
AGENT_TOOLS.append({
    "name": "start_ab_test",
    "description": (
        "Start a title A/B test on a live listing. Variant A is whatever the "
        "listing's REAL current title already is (fetched fresh from Etsy). "
        "Variant B is staged as a normal update_title approval once Variant A's "
        "rotation window closes -- it never applies automatically. rotation_days "
        "defaults to 21 and cannot go lower (shorter windows would compound "
        "title edits inside Etsy's own ranking-recovery period and hurt the "
        "listing). Only one active test per listing at a time."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "listing_id": {"type": "integer", "description": "The live Etsy listing to test."},
            "variant_b_title": {"type": "string", "description": "Proposed replacement title, ≤70 characters."},
            "rotation_days": {"type": "integer", "description": "Days per variant before rotating. Optional, default and floor is 21."},
        },
        "required": ["listing_id", "variant_b_title"],
    },
})
AGENT_TOOLS.append({
    "name": "get_ab_tests",
    "description": (
        "List every title A/B test (running, awaiting approval, completed, or "
        "cancelled) with real per-variant views/favorites/orders/revenue and an "
        "honest verdict -- 'inconclusive' when there isn't yet enough real data "
        "to call a winner, never a guessed one."
    ),
    "input_schema": {"type": "object", "properties": {}},
})
# Competitor Price & Listing Drift Watchdog (2026-08-06, "significantly
# improve Frank" idea 4/6, second batch) -- read-only over the weekly
# sweep's durable sidecar (data/competitor_snapshots.json), never a live
# Etsy call from the chat path.
AGENT_TOOLS.append({
    "name": "get_competitor_drift",
    "description": (
        "Real listings whose price has drifted meaningfully (20%+) from the "
        "live average of real comparable Etsy listings in their own niche, "
        "from the weekly competitor-watch sweep. Each item cites the real "
        "comparable-listing count and average it was computed from -- never "
        "a price recommendation, and price changes always need Scott's "
        "approval regardless."
    ),
    "input_schema": {"type": "object", "properties": {}},
})
# Weekly "What Changed" Movement Digest (2026-08-06, "significantly improve
# Frank" idea 5/6, second batch) -- real week-over-week winners/decliners by
# revenue delta, computed from already-collected daily snapshot data + one
# shared date-scoped receipts fetch.
AGENT_TOOLS.append({
    "name": "get_movement_digest",
    "description": (
        "Real week-over-week movement per listing -- views, favorites, "
        "orders, and revenue this week vs. last week, from Frank's own "
        "daily snapshot history plus real Etsy order receipts. Returns the "
        "top 5 real revenue winners and top 5 real revenue decliners. Use "
        "when asked 'what changed this week' or 'which listings are up or "
        "down'."
    ),
    "input_schema": {"type": "object", "properties": {}},
})
# Recurring Complaint / Review Theme Tracker (2026-08-06, "significantly
# improve Frank" idea 6/6, second batch) -- real buyer-authored review
# excerpts, so PII-flagged below same as draft_review_replies.
AGENT_TOOLS.append({
    "name": "get_review_themes",
    "description": (
        "Real recurring-complaint findings -- listings where the SAME "
        "significant word/phrase appears verbatim in 2+ distinct real "
        "negative (<=3 star) reviews, meaning multiple buyers "
        "independently flagged the same real problem. Includes the real "
        "unmodified review excerpts, never paraphrased or invented. Use "
        "when asked about recurring quality issues or review patterns."
    ),
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
        # 2026-08-01 (Workflows screen audit): key the already-running check on the
        # underlying script, not cmd_name -- generate_coloring_pages and
        # generate_coloring_pages_quick are separate registry entries that invoke the
        # same script and write into the same output folder, so a cmd_name-only guard
        # wouldn't stop them from colliding. Must also call proc.poll() here rather
        # than just checking dict membership: finished processes stay in
        # _LONG_RUNNING_PROCS unreaped for up to an hour until the health-check loop
        # cleans them up, so a membership-only check would falsely block re-runs.
        for other_pid, (other_proc, other_cmd, _started) in list(_LONG_RUNNING_PROCS.items()):
            if _EXEC_COMMANDS.get(other_cmd, {}).get("script") == cfg["script"] and other_proc.poll() is None:
                return {
                    "started": False,
                    "error": f"{other_cmd} is already running (PID {other_pid}) and uses the same script — wait for it to finish before starting another.",
                }
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
    # 2026-07-30 (Scott: ran qc_sweep + listing_integrity_check from Workflows,
    # "it said it ran but nothing was caught"): both scripts print their real
    # verdict LAST (qc_sweep's "RESULT: N FAIL/WARN/PASS" line, listing_integrity_
    # check's "SUMMARY:" block) -- but this used to keep only the FIRST ~1900
    # chars of stdout+stderr. Confirmed live: qc_sweep's output is already
    # ~2800 chars against a small local subset, so the verdict line was being
    # cut off and replaced with "[output truncated]" even in the small case --
    # against Scott's real ~176-product catalog it's far larger, so this was
    # ALWAYS true, not an edge case. A real FAIL/WARN always read as a clean run.
    # Now keeps a head chunk for context plus the FULL tail, so the actual
    # verdict is never lost regardless of total output length.
    _MAX_OUT, _TAIL_KEEP = 12000, 4000
    if len(out) > _MAX_OUT:
        head, tail = out[:_MAX_OUT - _TAIL_KEEP], out[-_TAIL_KEEP:]
        omitted = len(out) - len(head) - len(tail)
        out = f"{head}\n…[{omitted} chars omitted — verdict/summary preserved below]…\n{tail}"
    return {"returncode": result.returncode, "output": out, "success": result.returncode == 0}


def _resolve_product(identifier: str, catalog: list | None = None) -> dict:
    """Cross-reference a listing_id / internal product_id / name fragment against
    data/product_catalog.json -- the shop's own source of truth -- plus a live Etsy
    fetch when a listing_id is known. Backs the get_product agent tool (2026-07-30,
    Scott: "I put a listing id in his chat, he didn't know what the product was" --
    get_listing only ever queried Etsy directly, so it silently failed on anything
    that wasn't a bare numeric Etsy ID, e.g. an internal code like 'DP1026').

    Reuses _build_products_status() -- the exact function /api/products and the
    Files tab already call -- so this can never disagree with what those screens
    show (code-style.md: "reuse before you write"). Kept separate from
    _execute_agent_tool's dispatch branch so it's independently unit-testable.

    `catalog`: pass explicitly in tests to avoid touching real disk (mirrors
    _build_products_status()'s own explicit-catalog-argument design); defaults to
    loading the real data/product_catalog.json for the live tool-call path."""
    ident = (identifier or "").strip()
    if not ident:
        return {"error": "identifier is required"}
    if catalog is None:
        try:
            catalog = json.loads(Path("data/product_catalog.json").read_text())
        except OSError:
            catalog = []
    overrides = _product_catalog_overrides()
    rows = _build_products_status(catalog, _catalog_file_exists, overrides)

    ident_upper = ident.upper()
    match = next((r for r in rows if r.get("id") and r["id"].upper() == ident_upper), None)
    if not match and ident.isdigit():
        match = next((r for r in rows if str(r.get("listing_id") or "") == ident), None)
    candidates = []
    if not match:
        needle = ident.lower()
        candidates = [r for r in rows if needle in (r.get("title") or "").lower()]
        if len(candidates) == 1:
            match = candidates[0]

    if match:
        raw = next((p for p in catalog if p.get("product_id") == match.get("id")), {})
        result = {
            "found": True,
            "in_catalog": True,
            "product_id": match.get("id"),
            "name": match.get("title"),
            "category": match.get("category"),
            "status": match.get("status"),
            "price": match.get("price"),
            "files": match.get("files"),
            "all_files_present": match.get("all_files_present"),
            "note": raw.get("note"),
            "last_updated": raw.get("last_updated"),
        }
        lid = match.get("listing_id")
        if lid:
            try:
                listing = EtsyAPIClient().get_listing(int(lid))
                result["etsy"] = {
                    "listing_id": listing.get("listing_id", lid),
                    "title": listing.get("title", ""),
                    "state": listing.get("state", ""),
                    "price": _price_float(listing.get("price")),
                    "views": listing.get("views", 0),
                    "num_favorers": listing.get("num_favorers", 0),
                    "tags": listing.get("tags", []),
                    "url": listing.get("url") or f"https://www.etsy.com/listing/{listing.get('listing_id', lid)}",
                }
            except Exception as exc:
                result["etsy_fetch_error"] = str(exc)
        else:
            result["etsy"] = None
            result["etsy_note"] = "No etsy_listing_id on this catalog entry -- not yet published, or not linked."
        return result

    if len(candidates) > 1:
        return {
            "found": False,
            "identifier": ident,
            "note": f"{len(candidates)} products match '{ident}' by name -- ask which one before answering.",
            "candidates": [{"product_id": r.get("id"), "name": r.get("title")} for r in candidates[:8]],
        }

    if ident.isdigit():
        # Not in the local catalog -- still try Etsy directly so an un-catalogued
        # or newly-created listing is never reported as unknown.
        try:
            listing = EtsyAPIClient().get_listing(int(ident))
        except EtsyAPIError as exc:
            if getattr(exc, "status", None) == 404:
                return {
                    "found": False,
                    "identifier": ident,
                    "note": (
                        "No match in the product catalog by product_id/listing_id/name, and Etsy "
                        f"returned 404 for listing_id {ident} -- this ID doesn't exist on the shop "
                        "in any state."
                    ),
                }
            return {"found": False, "identifier": ident, "error": f"Etsy: {exc}"}
        except Exception as exc:
            return {"found": False, "identifier": ident, "error": str(exc)}
        return {
            "found": True,
            "in_catalog": False,
            "listing_id": listing.get("listing_id", ident),
            "name": listing.get("title", ""),
            "state": listing.get("state", ""),
            "price": _price_float(listing.get("price")),
            "tags": listing.get("tags", []),
            "description": (listing.get("description", "") or "")[:1500],
            "note": (
                "Found on Etsy but not in data/product_catalog.json -- likely un-catalogued or "
                "a duplicate-ID remap (see CLAUDE.md's dp_listing_map.json notes)."
            ),
        }

    return {
        "found": False,
        "identifier": ident,
        "note": "No match by product_id, listing_id, or name substring in the product catalog.",
    }


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
        if name in _TAX_SAFE_TOOL_NAMES:
            from data_store import DataStore
            real_data = None
            if name in _TAX_REAL_DATA_TOOL_NAMES:
                if name == "check_etsy_compliance":
                    real_data = {"listings": _get_active_listings_for_compliance()}
                else:
                    ytd_orders, ytd_capped = _get_ytd_orders_raw()
                    real_data = {"gross_ytd": _order_revenue(ytd_orders), "ytd_orders_capped": ytd_capped}
            return json.loads(tax_compliance_tools.execute_tool(name, tool_input or {}, DataStore(), real_data=real_data))
        if name == "stage_tiktok_post":
            return _stage_tiktok_post(tool_input or {})
        if name == "stage_pinterest_post":
            return _stage_pinterest_post(tool_input or {})
        if name == "list_pinterest_boards":
            return _list_pinterest_boards()
        if name == "get_metrics":
            return _metrics_sync()
        if name == "get_growth_brief":
            return asyncio.run(_compute_growth_brief())
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
        if name == "get_product":
            return _resolve_product((tool_input or {}).get("identifier", ""))
        if name == "stage_action":
            ti = tool_input or {}
            if ti.get("action_type") == "register_product":
                # Distinct payload shape from every other action_type below (no listing_id,
                # no Etsy call at all -- see _validate_staged_action's register_product branch
                # and register_product_directly, main.py ~15195, for the same shape) -- handled
                # in its own early branch rather than folded into the shared listing-mutation
                # payload builder below, which assumes a listing_id-centric shape throughout.
                payload = {
                    "product_id": (ti.get("product_id") or "").strip() or None,
                    "name": (ti.get("name") or "").strip(),
                    "category": ti.get("category"),
                    "price": ti.get("price"),
                    "etsy_listing_id": ti.get("etsy_listing_id"),
                }
                if not payload["product_id"]:
                    # Same auto-slug convention register_product_directly uses -- keeps both
                    # paths (chat-staged and Scott's Create-screen form) producing identical ids.
                    prefix = {"3d_print_physical": "P3D"}.get(payload["category"], "MISC")
                    payload["product_id"] = _slugify_product_id(payload["name"], prefix)
                candidate = {"type": "register_product", "payload": payload}
                ok, msg = _validate_staged_action(candidate)
                if not ok:
                    return {"staged": False, "error": msg}
                aid = db.enqueue_action("register_product", ti.get("summary", ""), payload)
                return {
                    "staged": True,
                    "action_id": aid,
                    "status": "pending",
                    "note": f"Queued for {business_config.OWNER_NAME}'s approval in the Action Center — not yet applied.",
                }
            if ti.get("action_type") in ("update_title", "update_tags", "update_description") and ti.get("listing_id") is not None:
                # Same grounding gate as autofix_listing_tags/autofix_listing_title (2026-08-05)
                # -- stage_action is the general-purpose tool and was the actual reachable path
                # for the koozie/planner bug class (a listing with no manifest entry getting a
                # confident-sounding but ungrounded rewrite), not just the two dedicated autofix
                # tools that already had this check.
                blocked = _blind_fix_refusal(int(ti["listing_id"]), ti.get("reason", ""))
                if blocked:
                    return blocked
            payload = {"listing_id": ti.get("listing_id")}
            if ti.get("title") is not None:
                payload["title"] = ti["title"]
            if ti.get("tags") is not None:
                payload["tags"] = ti["tags"]
            if ti.get("description") is not None:
                payload["description"] = ti["description"]
            if ti.get("new_state") is not None:
                payload["new_state"] = ti["new_state"]
            if ti.get("price") is not None:
                payload["price"] = ti["price"]
            if ti.get("sku") is not None:
                payload["sku"] = ti["sku"]
            if ti.get("taxonomy_id") is not None:
                payload["taxonomy_id"] = ti["taxonomy_id"]
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
            if _EXEC_COMMANDS[cmd_name].get("requires_approval"):
                # Mirrors /api/workflows/{id}/run exactly -- this command mutates
                # something (writes a file, etc.) so it must stage through the
                # Action Center like every other mutation, not run immediately
                # just because it was invoked from chat instead of the Workflows
                # screen. Caught 2026-07-17 while wiring in etsy_autoresponder --
                # this branch previously called _run_exec_command() unconditionally,
                # silently bypassing requires_approval for any chat-triggered call.
                payload = {"command": cmd_name, "extra_args": extra_args}
                summary = f"Run {cmd_name.replace('_', ' ')}" + (f" {extra_args}" if extra_args else "")
                aid = db.enqueue_action("run_script", summary, payload)
                return {
                    "staged": True,
                    "action_id": aid,
                    "status": "pending",
                    "note": f"Queued for {business_config.OWNER_NAME}'s approval in the Action Center — not yet applied.",
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
            todo_id = int(todo_id)
            ok = db.set_todo_done(todo_id, True)
            if ok:
                # 2026-08-01 (Tasks screen audit): the 2026-07-18 fix for orphaned
                # synced Google Calendar events (see _cleanup_synced_calendar_event's
                # docstring) only reached toggle_todo/remove_todo -- this is the
                # other place a todo gets marked done. _execute_agent_tool is a
                # plain sync function already running off the event loop (dispatched
                # via the caller's asyncio.to_thread), so this is a direct call, not
                # awaited.
                _cleanup_synced_calendar_event(f"todo:{todo_id}")
            return {"done": ok}
        if name == "create_calendar_event":
            summary = ((tool_input or {}).get("summary") or "").strip()
            when = ((tool_input or {}).get("when") or "").strip()
            description = ((tool_input or {}).get("description") or "").strip()
            if not summary or not when:
                return {"error": "summary and when are required"}
            try:
                import google_calendar_api as _gcal
            except ImportError:
                return {"error": "Google Calendar integration is not available."}
            try:
                event = _gcal.GoogleCalendarClient().create_event(summary, when, description)
            except _gcal.GoogleCalendarNotConnectedError:
                return {"error": "Google Calendar is not connected. Run python tools/google_calendar_oauth.py to authorize."}
            except _gcal.GoogleCalendarError as exc:
                return {"error": str(exc)}
            return {"created": True, "event_id": event.get("id"), "html_link": event.get("htmlLink", "")}
        if name == "autofix_listing_tags":
            ti = tool_input or {}
            lid = ti.get("listing_id")
            if lid is None:
                return {"error": "listing_id is required"}
            reason = ti.get("reason", "")
            blocked = _blind_fix_refusal(int(lid), reason)
            if blocked:
                return blocked
            return asyncio.run(_autofix_tags_core(int(lid), reason=reason))
        if name == "autofix_listing_title":
            ti = tool_input or {}
            lid = ti.get("listing_id")
            if lid is None:
                return {"error": "listing_id is required"}
            reason = ti.get("reason", "")
            blocked = _blind_fix_refusal(int(lid), reason)
            if blocked:
                return blocked
            return asyncio.run(_autofix_title_core(int(lid), reason=reason))
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
            # Same grounding gate as stage_action/autofix_listing_tags (2026-08-05) --
            # this batch tool used to be the one autofix sibling that skipped it
            # entirely, so a batch containing an unmapped orphan listing would still
            # get a confident-sounding blind tag rewrite for that one entry.
            reason = ti.get("reason", "")
            grounded_listings = []
            for l in listings:
                blocked = _blind_fix_refusal(int(l["listing_id"]), reason)
                if blocked:
                    fetch_errors.append({"listing_id": l["listing_id"], "error": blocked["error"]})
                else:
                    grounded_listings.append(l)
            listings = grounded_listings
            if not listings:
                return {"staged": [], "count": 0, "errors": fetch_errors}
            try:
                tag_results = _generate_tags_for_listings(listings, reason)
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
        if name == "run_catalog_reconciliation":
            return _run_catalog_reconciliation_batch()
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
        if name == "stage_batch_price_update":
            ti = tool_input or {}
            listing_ids = ti.get("listing_ids") or []
            if not listing_ids:
                return {"error": "listing_ids is required"}
            if len(listing_ids) > 5:
                return {
                    "error": (
                        f"Refused: {len(listing_ids)} listing_ids exceeds the 5-listing cap "
                        "for a single price-change batch (CLAUDE.md hard stop: no more than "
                        f"5 listing prices changed in one session). Split this into smaller "
                        f"batches and ask {business_config.OWNER_NAME} which subset to run first."
                    )
                }
            new_price = ti.get("new_price")
            price_delta = ti.get("price_delta")
            if (new_price is None) == (price_delta is None):
                return {"error": "provide exactly one of new_price or price_delta"}
            client = EtsyAPIClient()
            staged, errors = [], []
            for lid in listing_ids:
                try:
                    listing = client.get_listing(int(lid))
                except Exception as exc:
                    errors.append({"listing_id": lid, "error": f"could not fetch listing: {exc}"})
                    continue
                title_short = (listing.get("title") or f"Listing {lid}")[:50]
                if price_delta is not None:
                    current = _price_float(listing.get("price"))
                    target = round(current + float(price_delta), 2)
                else:
                    target = round(float(new_price), 2)
                payload = {"listing_id": lid, "price": target, "_state_at_staging": listing.get("state")}
                candidate = {"type": "update_price", "payload": payload}
                ok, msg = _validate_staged_action(candidate)
                if not ok:
                    errors.append({"listing_id": lid, "title": title_short, "error": msg})
                    continue
                summary = ti.get("summary") or f"Price change to ${target:.2f}: {title_short}"
                aid = db.enqueue_action("update_price", summary, payload)
                staged.append({"listing_id": lid, "action_id": aid, "new_price": target})
            with _cache_lock:
                _cache.pop("actions", None)
            return {"staged": staged, "count": len(staged), "errors": errors}
        if name == "stage_batch_listing_state":
            ti = tool_input or {}
            listing_ids = ti.get("listing_ids") or []
            new_state = ti.get("new_state")
            if not listing_ids:
                return {"error": "listing_ids is required"}
            if new_state not in ("active", "inactive"):
                return {"error": "new_state must be 'active' or 'inactive'"}
            if len(listing_ids) > 10:
                return {
                    "error": (
                        f"Refused: {len(listing_ids)} listing_ids exceeds the 10-listing cap "
                        f"for a single batch. Split this into smaller batches and ask "
                        f"{business_config.OWNER_NAME} which subset to run first."
                    )
                }
            client = EtsyAPIClient()
            staged, errors = [], []
            for lid in listing_ids:
                try:
                    listing = client.get_listing(int(lid))
                except Exception as exc:
                    errors.append({"listing_id": lid, "error": f"could not fetch listing: {exc}"})
                    continue
                title_short = (listing.get("title") or f"Listing {lid}")[:50]
                payload = {"listing_id": lid, "new_state": new_state, "_state_at_staging": listing.get("state")}
                candidate = {"type": "toggle_listing_state", "payload": payload}
                ok, msg = _validate_staged_action(candidate)
                if not ok:
                    errors.append({"listing_id": lid, "title": title_short, "error": msg})
                    continue
                verb = "Renew/republish" if new_state == "active" else "Deactivate"
                summary = ti.get("summary") or f"{verb}: {title_short}"
                aid = db.enqueue_action("toggle_listing_state", summary, payload)
                staged.append({"listing_id": lid, "action_id": aid, "new_state": new_state})
            with _cache_lock:
                _cache.pop("actions", None)
            return {"staged": staged, "count": len(staged), "errors": errors}
        if name == "qc_check_product":
            return _qc_check_product(tool_input or {})
        if name == "generate_listing_photos":
            return _produce_listing_photos(tool_input or {})
        if name == "generate_print_zip":
            return _produce_print_zip(tool_input or {})
        if name == "render_openscad_model":
            return _produce_openscad_render(tool_input or {})
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
        if name == "apply_conversion_fixes":
            ti = tool_input or {}
            lid = ti.get("listing_id")
            if lid is None:
                return {"error": "listing_id is required"}
            return asyncio.run(_apply_conversion_fixes_core(int(lid)))
        if name == "get_comparable_listings":
            return _get_comparable_listings(tool_input or {})
        if name == "draft_review_replies":
            return asyncio.run(_review_reply_iteration())
        if name == "start_ab_test":
            ti = tool_input or {}
            lid = ti.get("listing_id")
            if lid is None:
                return {"error": "listing_id is required"}
            return asyncio.run(_start_ab_test(int(lid), ti.get("variant_b_title", ""), ti.get("rotation_days")))
        if name == "get_ab_tests":
            tests = _load_ab_tests()
            return {"tests": sorted(tests.values(), key=lambda t: int(t["id"]), reverse=True)}
        if name == "get_competitor_drift":
            return {"items": _compute_competitor_drift_items()}
        if name == "get_movement_digest":
            return asyncio.run(_compute_movement_digest())
        if name == "get_review_themes":
            return asyncio.run(_compute_review_themes())
        if name == "deep_research":
            ti = tool_input or {}
            query = (ti.get("query") or "").strip()
            if not query:
                return {"error": "query is required"}
            result = asyncio.run(_run_deep_research_core(query, ti.get("breadth", 4), ti.get("depth", 2)))
            filename = _write_deep_research_report(result)
            return {
                "query": result["query"],
                "breadth": result["breadth"],
                "depth": result["depth"],
                "learning_count": len(result["learnings"]),
                "source_count": len(result["sources"]),
                "report_file": filename,
                "report_md": result["report_md"],
            }
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
    except subprocess.TimeoutExpired as exc:
        # exc.timeout is the actual configured limit that was exceeded (subprocess.run's
        # own attribute) -- a bare `timeout` name here was never defined in this scope
        # and raised NameError instead of this message every time a command genuinely
        # timed out, masking the real "transient, retryable" signal from the model.
        return {"error": f"Command timed out (>{exc.timeout}s)", "category": "transient", "retryable": True}
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
- Tag gaps (<13 tags), title length violations (>140 chars), and zero-view listings are high priority
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
  from the product's tier can suppress conversion in either direction. If REAL
  COMPARABLE LISTINGS data is provided below, use it as your primary price
  evidence instead of guessing at "the product's tier" — cite the real average/
  range directly (e.g. "comparable listings average $X, this is priced $Y above/
  below that") and let it override generic tier assumptions. If comparable data
  is not available, fall back to the static psychology-ending rule only.
- TITLE: 100-140 chars (Etsy's platform max is 140; real top-favorited competitors cluster
  100-140, not <=70 — a short title wastes searchable keyword slots), primary keyword in
  first 40 chars, comma separators not pipes.
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


_DESCRIPTION_HOOK_FIX_PROMPT = (
    "You are rewriting ONLY the opening hook (the first 1-2 sentences) of an "
    "Etsy listing description for " + business_config.BUSINESS_NAME + ". Mobile "
    "buyers see only this much before the fold, so it must hook the reader AND "
    "carry the primary keyword naturally.\n\n"
    "HARD RULES (violation = rejection):\n"
    "1. Rewrite ONLY the hook — the exact text given below as CURRENT HOOK. "
    "Do not touch, summarize, or reference anything else in the listing.\n"
    "2. Never invent, add, or imply any claim about page counts, file counts, "
    "sticker counts, included files, or features that isn't already stated in "
    "CURRENT HOOK or the feedback below — the #1 shop rule is never claim "
    "anything untrue about the product.\n"
    "3. 1-2 sentences, emotion-first, primary keyword in the first sentence.\n"
    "4. Keep the same core keyword/product identity as the current hook.\n\n"
    "TITLE: {title}\n"
    "CURRENT HOOK:\n{hook}\n\n"
    "REVIEWER/DIAGNOSIS FEEDBACK — fix this specifically:\n{reason}\n\n"
    "Return ONLY the new hook text — no quotes, no explanation, no JSON, no markdown."
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
    if not listings:
        return []
    engine = _effective_text_engine()
    if engine == "anthropic" and not ANTHROPIC_KEY:
        return []

    client = None if engine == "grok" else anthropic.Anthropic(api_key=ANTHROPIC_KEY)
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

        if engine == "grok":
            raw = _grok_text(_BATCH_TAG_PROMPT + "\n\n" + dynamic_block, max_tokens=8000)
        else:
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


# ── Product-category classification (2026-08-05) ───────────────────────────
# Built alongside the register_product feature (see the koozie/planner
# photo-mismatch fix above): before this, category guessing lived only in
# three separate, disagreeing title-keyword regex lists (listing_qc.py,
# order_notifier.py, and a deleted sync_product_catalog.py), none of which
# used Etsy's own structured signals. See data/knowledge_base/product_
# taxonomy.md for the full category reference this classifier is grounded
# against.
_TAXONOMY_DOC_PATH = ROOT / "data" / "knowledge_base" / "product_taxonomy.md"
_KNOWN_CATEGORIES = {
    "digital_planner", "digital_planner_bundle", "wall_art", "wall_art_bundle",
    "sticker_pack", "sticker_pack_license", "svg_bundle", "svg_bundle_license",
    "svg_3dprint_pack", "paper_pack", "coloring_pages", "sublimation",
    "3d_print_physical", "uncategorized",
}
_CLASSIFY_LISTING_PROMPT = """You are classifying Etsy listings for OnBrandCraftz into the shop's exact
internal product categories. Read the taxonomy reference below carefully --
it documents every real category, including two categories that look
similar and are easy to confuse (svg_3dprint_pack vs. 3d_print_physical --
read that section closely).

{taxonomy_doc}

For each listing below, return its category from EXACTLY this list:
digital_planner, digital_planner_bundle, wall_art, wall_art_bundle,
sticker_pack, sticker_pack_license, svg_bundle, svg_bundle_license,
svg_3dprint_pack, paper_pack, coloring_pages, sublimation,
3d_print_physical, uncategorized.

Use "uncategorized" whenever you are not genuinely confident -- a wrong
category is worse than an honest "don't know," and this decision gets
reviewed by a human before anything is committed. Never guess just to
avoid an empty answer.

Return ONLY a JSON array, one object per listing, each shaped exactly:
{{"listing_id": <id>, "category": "<one of the list above>",
"confidence": "high"|"medium"|"low", "reasoning": "<one short sentence>"}}
"""


def _taxonomy_doc_text() -> str:
    try:
        return _TAXONOMY_DOC_PATH.read_text()
    except OSError:
        return ""


def _classify_listing_structured(listing: dict) -> dict | None:
    """Free, no-LLM-call classification using Etsy's own structured signals
    (the raw listing object's `type` and `shipping_profile_id` fields --
    both unmodified passthroughs of Etsy's real API response, confirmed
    already exercised in production by listing_integrity_check.py's
    check_attributes()/check_shipping_cost()). Only ever confidently
    resolves the physical/digital split (3d_print_physical vs. everything
    else) -- every digital category shares `type: "download"`, so
    disambiguating those needs the LLM pass below. Returns None when
    inconclusive, never a low-confidence guess -- physical vs. digital is
    the one split these fields answer with certainty, so anything less
    than certain here should fall through, not half-guess."""
    listing_type = (listing.get("type") or "").lower()
    has_shipping_profile = bool(listing.get("shipping_profile_id"))
    if listing_type == "physical" or has_shipping_profile:
        return {
            "category": "3d_print_physical",
            "confidence": "high",
            "reasoning": "Etsy's own listing type/shipping profile marks this as a physical, shippable good.",
        }
    return None


def classify_listings_batch(listings: list[dict]) -> list[dict]:
    """Batched classifier for the reconciliation sweep and the manual
    registration form's category-prefill. Structured signals (see
    _classify_listing_structured) resolve the physical/digital split for
    free; only listings still ambiguous after that go into ONE batched LLM
    call per up-to-40 listings (mirrors _generate_tags_for_listings' same
    pattern), so a sweep with many orphans never fires one sequential LLM
    call per listing. Always returns exactly one result per input listing,
    in input order -- a parse failure or missing ANTHROPIC_KEY falls back
    to uncategorized/low confidence for the affected listings rather than
    dropping them or raising."""
    results: dict = {}
    needs_llm: list[dict] = []
    for l in listings:
        lid = l.get("listing_id")
        structured = _classify_listing_structured(l)
        if structured:
            results[lid] = {"listing_id": lid, **structured}
        else:
            needs_llm.append(l)

    engine = _effective_text_engine()
    if needs_llm and (engine == "grok" or ANTHROPIC_KEY):
        client = None if engine == "grok" else anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        taxonomy_doc = _taxonomy_doc_text()
        prompt_text = _CLASSIFY_LISTING_PROMPT.format(taxonomy_doc=taxonomy_doc)
        batch_size = 40
        for start in range(0, len(needs_llm), batch_size):
            batch = needs_llm[start : start + batch_size]
            rows = []
            for l in batch:
                rows.append(
                    f'ID:{l.get("listing_id")} TITLE:"{(l.get("title") or "")[:100]}" '
                    f'PRICE:${round(_price_float(l.get("price")), 2)} '
                    f'DESC:"{(l.get("description") or "")[:200]}"'
                )
            dynamic_block = "\n\nListings:\n" + "\n".join(rows)
            try:
                if engine == "grok":
                    raw = _grok_text(prompt_text + "\n\n" + dynamic_block, max_tokens=4000)
                else:
                    msg = _anthropic_create(
                        client, model=business_config.MODEL_CHEAP, max_tokens=4000,
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text, "cache_control": {"type": "ephemeral"}},
                                {"type": "text", "text": dynamic_block},
                            ],
                        }],
                    )
                    raw = msg.content[0].text.strip()
                parsed = _extract_json_object(raw)
                if isinstance(parsed, list):
                    for row in parsed:
                        lid = row.get("listing_id")
                        if lid is not None and row.get("category") in _KNOWN_CATEGORIES:
                            results[lid] = row
            except Exception as exc:
                print(f"[classify] LLM classification batch failed: {exc}", flush=True)
                # Unresolved listings fall through to the uncategorized default below --
                # never silently dropped from the output.

    out = []
    for l in listings:
        lid = l.get("listing_id")
        if lid in results:
            out.append(results[lid])
        else:
            out.append({
                "listing_id": lid, "category": "uncategorized", "confidence": "low",
                "reasoning": "Could not confidently classify -- no conclusive structured signal, "
                              "and the LLM pass was unavailable, failed, or wasn't confident enough.",
            })
    return out


def classify_unmapped_listing(listing: dict) -> dict:
    """Single-listing convenience wrapper (the manual registration form's
    category-prefill) built on classify_listings_batch()."""
    return classify_listings_batch([listing])[0]


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


@app.get("/cmd", response_class=HTMLResponse)
def desktop_command_center(request: Request):
    if not _check_session(request):
        return RedirectResponse(f"/login?next={request.url.path}", status_code=307)
    from jinja2 import Template
    from command_center import HTML, COMMANDS, OWNER_NAME
    sections = [{
        "id": s["category"].lower().replace(" ", "_").replace("&", "and"),
        "category": s["category"],
        "color": s["color"],
        "icon": s["icon"],
        "commands": s["commands"],
    } for s in COMMANDS]
    rendered = Template(HTML).render(commands=sections, cloud_mode=True, owner_name=OWNER_NAME, csrf_token="")
    return HTMLResponse(content=rendered, headers={"Cache-Control": "private, no-cache"})


@app.get("/run")
def api_run_command(request: Request, id: str = ""):
    if not _check_session(request):
        raise HTTPException(status_code=403, detail="Unauthorized")
    from command_center import _find_cmd, BASE_DIR
    from fastapi.responses import StreamingResponse
    cmd_def = _find_cmd(id)
    if not cmd_def:
        async def _not_found():
            yield 'data: {"done":true,"ok":false}\n\n'
        return StreamingResponse(_not_found(), media_type="text/event-stream")

    cmd = cmd_def.get("cmd")
    if not cmd:
        async def _empty():
            msg = json.dumps({"line": "No command defined.\n", "err": True})
            yield f"data: {msg}\n\n"
            yield f'data: {json.dumps({"done": True, "ok": False})}\n\n'
        return StreamingResponse(_empty(), media_type="text/event-stream")

    cmd_args = shlex.split(cmd)
    # Same fix as command_center.py's own run_command() (2026-07-29 audit) --
    # this is a separate, near-duplicate copy of that streaming-subprocess
    # logic used specifically for the Railway-hosted /cmd page, and had the
    # identical bug: a mismatched python3 resolved on PATH vs. the one
    # actually running this server.
    if cmd_args and cmd_args[0] in ("python3", "python", "./venv/bin/python3", "./venv/bin/python"):
        cmd_args[0] = sys.executable

    def generate():
        import select as sel
        proc = subprocess.Popen(
            cmd_args,
            shell=False,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        fds = {proc.stdout.fileno(): False, proc.stderr.fileno(): True}
        open_fds = set(fds.keys())
        # Incremental decoder per fd -- a raw os.read(fd, 4096).decode(errors=
        # "replace") corrupts multibyte UTF-8 characters (emoji, curly quotes)
        # that land split across two reads into `` replacement characters.
        decoders = {fd: codecs.getincrementaldecoder("utf-8")(errors="replace") for fd in open_fds}
        while open_fds:
            readable, _, _ = sel.select(list(open_fds), [], [], 0.1)
            for fd in readable:
                is_err = fds[fd]
                chunk = os.read(fd, 4096)
                if not chunk:
                    tail = decoders[fd].decode(b"", final=True)
                    if tail:
                        payload = json.dumps({"line": tail, "err": is_err})
                        yield f"data: {payload}\n\n"
                    open_fds.discard(fd)
                    continue
                line = decoders[fd].decode(chunk)
                if not line:
                    continue
                for ln in line.splitlines(keepends=True):
                    payload = json.dumps({"line": ln, "err": is_err})
                    yield f"data: {payload}\n\n"
        proc.wait()
        ok = proc.returncode == 0
        yield f"data: {json.dumps({'done': True, 'ok': ok})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})




@app.get("/api/me")
async def get_me(request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """Return the username/role/email/name associated with the current session.
    email/display_name added 2026-07-18 alongside self-service signup, so the
    Settings screen can show "who am I signed in as" -- both are None for any
    account created before that (first-run owner setup and the old admin-panel
    path never collected them; nothing backfills old rows)."""
    uname = _get_session_user(request)
    if not uname:
        return {"username": "", "role": "", "email": "", "display_name": ""}
    user_row = db.get_hub_user(uname)
    # Fail CLOSED: a session whose user row is gone (deleted/reset) is NOT an owner.
    # (Matches _require_owner, which already 403s that case — this just stops the UI
    # from briefly showing owner-only controls to a stale session.)
    role = user_row["role"] if user_row else ""
    return {
        "username": uname,
        "role": role,
        "email": (user_row or {}).get("email") or "",
        "display_name": (user_row or {}).get("display_name") or "",
    }


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
    # 2026-08-14 functional audit (round 2): this route used to delete the
    # hub_users row without revoking the user's existing sessions -- unlike
    # admin_reset_password just above and delete_my_account, which both do
    # this. Session validation only checks the session id (never re-checks
    # the underlying hub_users row still exists), so a just-deleted admin's
    # cookie kept authenticating successfully for up to SESSION_TTL (30
    # days). Same revocation pattern as admin_reset_password.
    with _sessions_lock:
        to_remove = [sid for sid, (_, u) in _sessions.items() if u == uname]
        for sid in to_remove:
            del _sessions[sid]
    try:
        db.delete_sessions_for_user(uname)
    except Exception as exc:
        print(f"[auth] delete_sessions_for_user({uname!r}) failed after admin_delete_user -- sessions "
              f"may not be fully revoked: {exc}", flush=True)
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
            "active_listing_goal": _ACTIVE_LISTING_GOAL,  # Home ticker (2026-07-23)
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


def _get_recent_orders_raw() -> list[dict]:
    """Raw recent paid Etsy receipts (last 100), cached 120s. Shared fetch
    point for everything that needs real order data — was previously
    duplicated independently by _sales_by_listing_sync() (its own
    "sales_by_listing" cache of the same underlying call) and _search_orders()
    (its own "orders_recent" cache) -- consolidated 2026-07-18 to one fetch,
    one cache key, so a new caller (the business-tracker Orders tab) doesn't
    need a third copy and the two existing ones stop hitting Etsy twice for
    identical data."""
    cached = _cache_get("orders_recent", ttl=120)
    if cached is not None:
        return cached
    try:
        raw = EtsyAPIClient().get_orders(limit=100).get("results", []) or []
    except Exception as exc:
        print(f"[orders] recent-receipts fetch failed: {exc}", flush=True)
        raw = []
    _cache_set("orders_recent", raw)
    return raw


def _get_ytd_orders_raw() -> tuple[list[dict], bool]:
    """Real paid Etsy receipts since Jan 1 of the current year, shop-local
    time -- built for the tax tools (get_tax_overview/calculate_quarterly_tax/
    get_1099k_status), 2026-08-06. Returns (orders, capped) where `capped` is
    True if the fetch hit Etsy's own single-call limit (100) -- if so, the
    real YTD order count is HIGHER than what's returned here, and callers
    MUST surface that honestly rather than silently under-reporting revenue
    (same "last 100 receipts" scope caveat _get_recent_orders_raw() already
    documents, just date-bounded to this year instead of "most recent").
    Cached 3600s: tax planning doesn't need sub-hour freshness."""
    cache_key = "orders_ytd"
    cached = _cache_get(cache_key, ttl=3600)
    if cached is not None:
        return cached["orders"], cached["capped"]
    try:
        now = _shop_now()
        jan_1 = datetime(now.year, 1, 1, tzinfo=now.tzinfo)
        raw = EtsyAPIClient().get_orders(limit=100, min_created=int(jan_1.timestamp())).get("results", []) or []
    except Exception as exc:
        print(f"[tax] YTD orders fetch failed: {exc}", flush=True)
        raw = []
    capped = len(raw) >= 100
    _cache_set(cache_key, {"orders": raw, "capped": capped})
    return raw, capped


def _get_active_listings_for_compliance() -> list[dict]:
    """Raw active Etsy listing dicts (full shape, including description/images)
    for tax_compliance_tools.check_etsy_compliance(). Built 2026-08-06 as a
    separate fetch from _listings_sync() on purpose: that function returns a
    trimmed shape (title/price/views/...) with no description or images field,
    cached under "listings_active" for the Listings/Products screens -- adding
    description/images to that shared cache would bloat a payload hit far more
    often just to serve this rarely-called chat tool. Cached 3600s under its
    own key instead."""
    cache_key = "listings_active_compliance_raw"
    cached = _cache_get(cache_key, ttl=3600)
    if cached is not None:
        return cached
    try:
        raw = EtsyAPIClient().get_shop_listings_all(state="active") or []
    except Exception as exc:
        print(f"[tax] active listings fetch for compliance check failed: {exc}", flush=True)
        raw = []
    _cache_set(cache_key, raw)
    return raw


def _sales_by_listing_sync() -> dict:
    """Map real per-listing sales from paid order receipts → transactions.

    Etsy receipts each carry a `transactions` array where every transaction has
    a `listing_id` and `quantity`. Summing these gives true units sold per
    listing — the honest denominator for conversion (favorites are NOT sales).
    Based on the 100 most recent paid receipts (via _get_recent_orders_raw()'s
    shared cache). Returns {listing_id: units_sold}."""
    out: dict = {}
    for receipt in _get_recent_orders_raw():
        for t in receipt.get("transactions", []) or []:
            lid = t.get("listing_id")
            if lid is None:
                continue
            try:
                qty = int(t.get("quantity", 1) or 1)
            except (TypeError, ValueError):
                qty = 1
            out[lid] = out.get(lid, 0) + qty
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


# ── Reviews-needing-reply radar (2026-07-18, audit-report fix) ─────────────────
# Etsy's v3 API has no seller-reply field on a review and no review-response
# endpoint at all (see EtsyAPIClient.get_reviews()'s own docstring, verified
# 2026-06-17) -- "has Scott replied to this review" cannot come from Etsy
# directly, so this tracks it locally, same pattern as tools/review_monitor.py's
# reviews_seen.json (which tracks "have we already notified about this review",
# a different question). A review has no dedicated review_id in the v3 response,
# but is 1:1 with the transaction it's attached to, so transaction_id is the
# stable identifier used here.
_REVIEWS_REPLIED_PATH = db.resolve_persistent_path(
    "reviews_replied.json",
    fallback=ROOT / "data" / "reviews_replied.json",
)


def _load_replied_review_ids() -> set:
    try:
        return set(json.loads(_REVIEWS_REPLIED_PATH.read_text()))
    except (OSError, ValueError):
        return set()


def _mark_review_replied(review_id: str) -> None:
    ids = _load_replied_review_ids()
    ids.add(str(review_id))
    _REVIEWS_REPLIED_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REVIEWS_REPLIED_PATH.write_text(json.dumps(sorted(ids), indent=2))


@app.post("/api/reviews/{review_id}/mark-replied")
async def mark_review_replied(review_id: str, _token: str = Depends(_auth_session_or_bearer)):
    """Scott (or a future Quick-Reply-adjacent flow) calls this once he's replied
    to a review on Etsy directly -- this cannot detect a reply automatically,
    only record that one happened."""
    _mark_review_replied(review_id)
    with _cache_lock:
        _cache.pop("inbox", None)
    return {"ok": True, "review_id": review_id}


# ── Review reply drafting (2026-08-06, "Instant Message Response Assistant") ──
# Etsy's v3 API has no review-response endpoint at all (see the radar comment
# above) and no third-party message-send endpoint either (get_messages() hits
# shops/{id}/conversations, confirmed 404 for this app -- see EtsyAPIClient.
# get_messages()'s own docstring) -- so "auto-reply to a buyer message" is not
# achievable at all, and "auto-post a review reply" isn't either. What IS
# achievable: detect a new review the moment it's fetchable (get_reviews() is
# real and working), draft a genuinely personalized reply with Claude, and get
# it in front of Scott fast (email + in-app) so he can paste it into Etsy
# himself in seconds instead of remembering to check. Runs hourly via
# _review_reply_loop(), same _run_loop_iteration() resilience pattern as
# _health_check_loop().
_REVIEW_DRAFTS_PATH = db.resolve_persistent_path(
    "review_drafts.json",
    fallback=ROOT / "data" / "review_drafts.json",
)


def _load_review_drafts() -> dict:
    try:
        return json.loads(_REVIEW_DRAFTS_PATH.read_text())
    except (OSError, ValueError):
        return {}


def _save_review_draft(review_id: str, draft: str, rating: int) -> None:
    drafts = _load_review_drafts()
    drafts[str(review_id)] = {
        "draft": draft, "rating": rating,
        "drafted_at": datetime.now(timezone.utc).isoformat(),
    }
    _REVIEW_DRAFTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REVIEW_DRAFTS_PATH.write_text(json.dumps(drafts, indent=2))


_REVIEW_REPLY_PROMPT = """You are drafting a reply to a real Etsy buyer review for OnBrandCraftz, a kawaii
digital planner / sticker / wall art / 3D-print shop run by Scott. Write ONE short,
warm, genuine-sounding reply (2-4 sentences) that:
- Thanks the buyer by referencing something SPECIFIC from their review (not generic)
- Matches Scott's real tone: professional, warm, no emoji, signed "— Scott"
- For a 4-5 star review: express genuine gratitude, maybe a light personal touch
- For a 1-3 star review: acknowledge the specific issue without being defensive,
  invite them to reach out so it can be made right, still signed "— Scott"
Never invent product details you don't have. Output ONLY the reply text, nothing else."""


def _draft_review_reply_text(rating: int, review_text: str) -> str | None:
    engine = _effective_text_engine()
    if engine == "anthropic" and not ANTHROPIC_KEY:
        return None
    prompt_input = f"Rating: {rating}/5 stars\nReview text: {review_text or '(no written review, star rating only)'}"
    try:
        if engine == "grok":
            raw = _grok_text(_REVIEW_REPLY_PROMPT + "\n\n" + prompt_input, max_tokens=300)
        else:
            client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
            msg = _anthropic_create(
                client, model=business_config.MODEL_CHEAP, max_tokens=300,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": _REVIEW_REPLY_PROMPT, "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": prompt_input},
                ]}],
            )
            raw = msg.content[0].text.strip()
        return raw or None
    except Exception:
        return None


async def _review_reply_iteration() -> dict:
    """Fetch real reviews, draft+persist+email anything new (not yet drafted AND
    not already marked replied). Full review text, not the 120-char slice
    /api/inbox uses for display -- drafting needs the whole thing."""
    reviews_r = await asyncio.to_thread(lambda: EtsyAPIClient().get_reviews(limit=50))
    results = reviews_r.get("results", [])
    replied_ids = _load_replied_review_ids()
    drafts = _load_review_drafts()
    new_drafts = []
    for r in results:
        review_id = str(r.get("transaction_id") or "")
        if not review_id or review_id in replied_ids or review_id in drafts:
            continue
        rating = r.get("rating", 0)
        text = r.get("review") or ""
        draft = await asyncio.to_thread(_draft_review_reply_text, rating, text)
        if not draft:
            continue
        _save_review_draft(review_id, draft, rating)
        new_drafts.append({"id": review_id, "rating": rating, "text": text[:200], "draft": draft})
    if new_drafts:
        with _cache_lock:
            _cache.pop("inbox", None)
        subject = f"{len(new_drafts)} new review reply draft{'s' if len(new_drafts) != 1 else ''} ready — OnBrandCraftz"
        body_lines = [
            f"{len(new_drafts)} new review{'s' if len(new_drafts) != 1 else ''} came in. "
            "Draft replies below -- copy, tweak if you'd like, and paste into Etsy.",
            "",
        ]
        for d in new_drafts:
            stars = "★" * d["rating"] + "☆" * (5 - d["rating"])
            body_lines += [
                stars,
                f'Review: "{d["text"]}"' if d["text"] else "(star rating only, no written review)",
                "",
                f'Draft reply: "{d["draft"]}"',
                "", "---", "",
            ]
        body_lines.append("— Frank 🤖")
        try:
            from daily_brief import _send_brief
            await asyncio.to_thread(_send_brief, subject, "\n".join(body_lines))
        except Exception:
            pass  # email is a bonus channel -- drafts are already persisted and shown in-app either way
    return {"new_drafts": len(new_drafts), "total_reviews_checked": len(results)}


async def _review_reply_loop() -> None:
    """Hourly: check for new reviews, draft a reply for each, email Scott a
    digest. Same resilience wrapper as _health_check_loop()."""
    await asyncio.sleep(90)  # let the app finish booting first
    while True:
        delay = await _run_loop_iteration(
            "review_reply_draft", "Review Reply Drafts", _review_reply_iteration,
            on_success_detail=lambda r: f"{r['new_drafts']} new draft(s) from {r['total_reviews_checked']} reviews checked",
            base_interval=3600,
        )
        await asyncio.sleep(delay)


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
            # 50, not 3 -- "reviews awaiting a reply" needs to look at real
            # history, not just the newest 3 (which is all the old fetch limit
            # gave the display). Matches _compute_star_seller_status()'s own
            # limit=50 review fetch, so this stays consistent across the two
            # dashboard cards that both read review history.
            reviews_r = client.get_reviews(limit=50)
        except Exception as exc:
            reviews_r = exc

        out: dict = {"unread_count": 0, "oldest_unread_hours": None, "recent_reviews": [],
                     "reviews_awaiting_reply": 0}

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
            replied_ids = _load_replied_review_ids()
            # 2026-08-06 ("Instant Message Response Assistant"): merge in any
            # AI-drafted reply _review_reply_loop() already generated for this
            # review, so the Inbox card can show real, ready-to-paste text
            # instead of just "N reviews awaiting a reply."
            drafts = _load_review_drafts()
            all_reviews = []
            for r in reviews_r.get("results", []):
                review_id = str(r.get("transaction_id") or "")
                all_reviews.append({
                    "id": review_id,
                    "rating": r.get("rating", 0),
                    "text": (r.get("review") or "")[:120],
                    "date": r.get("create_timestamp", 0),
                    "replied": bool(review_id) and review_id in replied_ids,
                    "draft": drafts.get(review_id, {}).get("draft"),
                })
            out["recent_reviews"] = all_reviews[:3]
            out["reviews_awaiting_reply"] = sum(1 for r in all_reviews if r["id"] and not r["replied"])
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

    today = _shop_today()  # 2026-08-06 (Today second-pass audit): shop-local, not server UTC — see _shop_today() docstring
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
    """Return listings with thumbnail URLs. Result cached 30 s.

    state="expired" (2026-07-31, Listings screen audit): _listings_sync() and the
    chat tools (list_listings/get_listing) already fully supported this state --
    only the screen's own tab set (Active/Drafts/Deactivated) didn't expose it,
    even though reactivating an expired listing IS Etsy's actual renewal
    mechanism (see stage_batch_listing_state's own docstring). Added as a 4th
    tab rather than left chat-only."""
    if state not in ("active", "draft", "inactive", "expired"):
        raise HTTPException(status_code=400, detail="state must be active, draft, inactive, or expired")

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

        if len(title) > 140:
            add("high", "title_too_long",
                f"Title over 140 chars ({len(title)}): {title[:50]}",
                f"Title is {len(title)} characters — Etsy's hard platform max is 140.",
                "Trim to ≤140 chars, keeping the primary keyword in the first 40.",
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

    # 2026-07-18: exclude any listing that already has a fix pending approval --
    # once Scott taps "Let Frank fix it" (phoneSheetFix() -> /api/conversion-
    # targets/{id}/fix) and a title/tags/description fix gets staged, the
    # underlying metric (views/sales) hasn't changed yet, so without this the
    # SAME card just kept reappearing here immediately after being "fixed",
    # which read as broken. If the pending action is later rejected, the card
    # naturally reappears (it's excluded only while genuinely pending).
    try:
        pending_listing_ids = {
            str(a["payload"]["listing_id"])
            for a in db.list_actions("pending", limit=200)
            if (a.get("payload") or {}).get("listing_id")
        }
    except Exception:
        pending_listing_ids = set()
    if pending_listing_ids:
        cards = [c for c in cards if str(c.get("listing_id") or "") not in pending_listing_ids]

    # 2026-07-18: the pending-only exclusion above was NOT enough on its own --
    # a real bug report (Scott approved a Conversion Doctor fix for a listing
    # and the identical card was back the moment the row left "pending"). None
    # of these four rules can ever be satisfied by a content edit: they read
    # views/sales/title/tags directly from Etsy, and per CLAUDE.md's Ranking
    # Recovery Playbook, Etsy takes ~2-3 weeks to re-index an edited listing
    # before those numbers can move. So instead of re-flagging "still needs
    # attention" the instant a fix executes, downgrade + reword the card using
    # the same edit-cooldown timestamp db.note_listing_edited() already writes
    # (built 2026-07-15 for a different purpose -- warning against compounding
    # edits -- but it's exactly the "was this recently fixed" signal needed
    # here too). Keep the card visible rather than hiding it outright: an
    # invisible card gives zero confirmation a fix was applied, which was the
    # other half of Scott's report ("I don't know if he actually fixed it").
    _CONTENT_FIXABLE_CATEGORIES = frozenset(
        {"title_too_long", "tags_incomplete", "low_conversion", "zero_views"}
    )
    for c in cards:
        if c["category"] not in _CONTENT_FIXABLE_CATEGORIES or not c.get("listing_id"):
            continue
        try:
            days = db.days_since_listing_edited(c["listing_id"])
        except Exception:
            days = None
        if days is not None and days < db._RANKING_RECOVERY_COOLDOWN_DAYS:
            c["severity"] = "low"
            c["recently_fixed_days_ago"] = days
            c["suggestion"] = (
                f"✅ A fix was applied {days}d ago — Etsy can take up to ~3 weeks "
                "to re-index and reflect it in views/sales. No further action "
                "needed yet."
            )

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


# ── Bundle-opportunity nudge (2026-07-18, audit-report fix) ────────────────────
# Deterministic rule (no LLM, just counting) surfacing categories with many
# active, individually-listed products and few/no bundle-type listings
# covering them. Confirmed against real catalog counts, not the planner
# example the source research used narratively -- planners are already
# well-bundled (BUNDLE_PLANNERS covers the 4 active DP10xx listings); the
# real gap is wall_art: 67 active listings against a single 3-piece bundle.
# Digital-seller growth research names bundling + listing volume as the two
# real differentiators past a few hundred dollars/month -- this is a
# proactive nudge, not a problem, so it's surfaced on the Today tab in its
# own "Opportunities" section, separate from Needs Attention.
_BUNDLE_OPPORTUNITY_MIN_ACTIVE = 10  # below this, a category isn't worth a bundle push yet
_BUNDLE_OPPORTUNITY_RATIO = 15  # active-per-bundle ratio above which a category reads "underserved"


def _compute_bundle_opportunities() -> list[dict]:
    """Reads data/product_catalog.json directly (same file GET /api/products
    reads) rather than round-tripping Etsy -- this is catalog structure, not
    live listing stats, so no API call is needed. Never raises -- an empty
    list on any read/parse failure, since this is a nudge, not a required
    signal."""
    try:
        catalog = json.loads((ROOT / "data" / "product_catalog.json").read_text())
    except (OSError, ValueError):
        return []

    active_counts: dict[str, int] = {}
    bundle_counts: dict[str, int] = {}
    for p in catalog:
        cat = str(p.get("category", ""))
        status = p.get("status", "")
        if cat.endswith("_bundle"):
            if status == "active":
                base = cat[: -len("_bundle")]
                bundle_counts[base] = bundle_counts.get(base, 0) + 1
        elif status == "active":
            active_counts[cat] = active_counts.get(cat, 0) + 1

    opportunities = []
    for cat, active_n in active_counts.items():
        if active_n < _BUNDLE_OPPORTUNITY_MIN_ACTIVE:
            continue
        bundled_n = bundle_counts.get(cat, 0)
        if bundled_n > 0 and active_n / bundled_n < _BUNDLE_OPPORTUNITY_RATIO:
            continue  # already has a reasonable number of bundles for its size
        label = cat.replace("_", " ")
        opportunities.append({
            "category": cat,
            "active_count": active_n,
            "bundle_count": bundled_n,
            "title": f"{active_n} {label} listings, only {bundled_n} bundle{'s' if bundled_n != 1 else ''}",
            "suggestion": f"Bundling is one of the biggest levers top digital sellers use to grow — "
                          f"worth building a {label} bundle listing.",
        })
    opportunities.sort(key=lambda o: -o["active_count"])
    return opportunities[:2]  # cap surfaced count to avoid Today-tab clutter


@app.get("/api/bundle-opportunities")
async def get_bundle_opportunities(_token: str = Depends(_auth_session_or_bearer)):
    """Today tab's Opportunities section. Cached 1h — catalog structure changes
    rarely enough that this doesn't need the shorter TTLs live-Etsy data uses."""
    cached = _cache_get("bundle_opportunities", ttl=3600)
    if cached is not None:
        return cached
    data = {"opportunities": await asyncio.to_thread(_compute_bundle_opportunities)}
    _cache_set("bundle_opportunities", data)
    return data


# ── Growth Brief (2026-08-06, "significantly improve Frank" idea 2/3) ──────────
# Frank had gotten data-rich but synthesis-poor: Ads/COGS/Star Seller/seasonal
# keywords/bundle opportunities/Conversion Doctor findings all already existed
# as separate panels/endpoints, but nothing combined them into one ranked
# "do this first" list. This does exactly that -- and is deliberate about
# NEVER fabricating a dollar figure it doesn't actually have (the top-priority
# "never lie" rule applies to Frank's own recommendations, not just listing
# copy): only ads spend/revenue, Star Seller's real trailing-90-day revenue,
# and COGS's already-labeled profit ESTIMATE carry a real est_dollar_impact.
# Conversion Doctor/seasonal/bundle items rank by their own existing native
# signal (severity/urgency/active_count) with est_dollar_impact left null and
# impact_basis saying so explicitly -- a null $ figure ranks below any item
# with a real one, but is never backfilled with an invented number just to
# make every row look equally precise.
def _score_growth_brief_items(ads: dict, cogs: dict, star_seller: dict, actions_data: dict,
                                bundle_opps: list, seasonal_entries: list,
                                competitor_drift_items: list | None = None,
                                review_theme_findings: list | None = None) -> list[dict]:
    """Pure merge/scoring over already-fetched data -- no I/O, so this is
    directly unit-testable with synthetic inputs. See _compute_growth_brief()
    for where each argument actually comes from."""
    items: list[dict] = []

    if ads.get("used"):
        st = ads.get("status")
        if st == "kill_signal":
            items.append({
                "category": "ads", "severity": "high",
                "title": "Ads are burning money with zero return",
                "detail": f"${ads['week_spend']:.2f} spent this week, $0 revenue back.",
                "suggestion": "Pause this campaign in Etsy Ads and re-evaluate targeting before spending more.",
                "est_dollar_impact": ads["week_spend"],
                "impact_basis": "real: this week's logged ad spend with zero logged revenue",
            })
        elif st == "low_roas":
            items.append({
                "category": "ads", "severity": "medium",
                "title": f"Ads ROAS is below target ({ads.get('month_roas', 0)}x)",
                "detail": f"${ads['month_spend']:.2f} spent this month, ${ads['month_revenue']:.2f} back.",
                "suggestion": "Consider narrowing targeting or pausing the weakest-performing listing.",
                "est_dollar_impact": max(ads["month_spend"] - ads["month_revenue"], 0),
                "impact_basis": "real: this month's logged spend minus logged revenue",
            })
        elif st == "scale_eligible":
            items.append({
                "category": "ads", "severity": "low",
                "title": f"Ads are outperforming target ({ads.get('month_roas', 0)}x ROAS)",
                "detail": f"${ads['month_revenue']:.2f} back on ${ads['month_spend']:.2f} spent this month.",
                "suggestion": "Consider raising budget 20-30% (never more than double at once) — this is a proven winner.",
                "est_dollar_impact": ads["month_revenue"],
                "impact_basis": "real: this month's logged ad revenue — a growth opportunity, not a problem",
            })

    if star_seller.get("status") == "at_risk":
        items.append({
            "category": "star_seller", "severity": "high",
            "title": "Star Seller status is at risk",
            "detail": f"{star_seller.get('orders_90d', 0)} orders / ${star_seller.get('revenue_90d', 0):.2f} "
                      "revenue over the trailing 90 days (need 5 orders / $300).",
            "suggestion": "Star Seller status drives catalog-wide ranking lift — closing this gap benefits every listing, not just one.",
            "est_dollar_impact": star_seller.get("revenue_90d", 0),
            "impact_basis": "real: trailing-90-day revenue already earned, shown as the stakes of losing Star Seller ranking lift",
        })

    if cogs.get("used") and cogs.get("flagged_low_margin"):
        n = len(cogs["flagged_low_margin"])
        items.append({
            "category": "cogs", "severity": "medium",
            "title": f"{n} listing{'s' if n != 1 else ''} running thin margins",
            "detail": f"Shop-wide average margin is an estimated {cogs.get('avg_margin_pct', 0)}%.",
            "suggestion": "Review pricing on these listings — even a small price increase compounds across every future sale.",
            "est_dollar_impact": None,
            "impact_basis": "estimate only (COGS is a flat-rate guess, not real accounting) — no forward dollar prediction made",
        })

    for card in (actions_data.get("actions") or [])[:5]:
        if card.get("severity") not in ("high", "medium"):
            continue
        items.append({
            "category": "listing_fix", "severity": card["severity"],
            "title": card.get("title", ""), "detail": card.get("detail", ""),
            "suggestion": card.get("suggestion", ""),
            "listing_id": card.get("listing_id"), "url": card.get("url"),
            "est_dollar_impact": None,
            "impact_basis": f"ranked by severity + {card.get('impact', 0)} views on this listing — no dollar figure fabricated",
        })

    for e in seasonal_entries:
        urg = e.get("urgency")
        items.append({
            "category": "seasonal", "severity": "medium" if urg == "OVERDUE" else "low",
            "title": f"{e.get('season', 'Seasonal')} keyword window is {str(urg).lower()}",
            "detail": f"Update by {e.get('update_by')} for listings: {', '.join(e.get('listings_to_update', []))}",
            "suggestion": "Update titles/tags before the seasonal search window opens.",
            "est_dollar_impact": None,
            "impact_basis": "timing opportunity — no dollar estimate available",
        })

    for bo in bundle_opps:
        items.append({
            "category": "bundle", "severity": "low",
            "title": bo.get("title", ""), "detail": "",
            "suggestion": bo.get("suggestion", ""),
            "est_dollar_impact": None,
            "impact_basis": "structural catalog gap — no dollar estimate available",
        })

    for cd in (competitor_drift_items or [])[:5]:
        gap = abs(cd["gap_pct"])
        items.append({
            "category": "competitor_drift", "severity": "medium" if gap >= 35 else "low",
            "title": f"Listing {cd['listing_id']} priced {gap}% {cd['direction']} the market",
            "detail": (
                f"${cd['my_price']:.2f} vs a ${cd['competitor_avg']:.2f} average across "
                f"{cd['competitor_count']} real live comparable listings (search: \"{cd['keywords']}\")."
            ),
            "suggestion": "Review pricing against these real comparables — Scott's call, never automatic.",
            "listing_id": cd["listing_id"], "url": cd.get("url"),
            "est_dollar_impact": None,
            "impact_basis": "real: live comparable-listing average pulled from Etsy's public search — no revenue prediction made",
        })

    for rt in (review_theme_findings or [])[:5]:
        items.append({
            "category": "review_theme", "severity": "medium" if rt["review_count"] >= 3 else "low",
            "title": f"\"{rt['shared_term']}\" mentioned in {rt['review_count']} reviews of \"{rt['title']}\"",
            "detail": f"{rt['review_count']} of {rt['total_negative_reviews']} negative reviews on this listing independently name the same issue.",
            "suggestion": "Read the real excerpts and check whether the file/description needs a fix — Scott's call.",
            "listing_id": rt["listing_id"],
            "est_dollar_impact": None,
            "impact_basis": f"real: the word \"{rt['shared_term']}\" appears verbatim in {rt['review_count']} distinct real reviews — no dollar estimate available",
        })

    _SEV_RANK = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda it: (
        0 if it["est_dollar_impact"] is not None else 1,
        -(it["est_dollar_impact"] or 0),
        _SEV_RANK.get(it["severity"], 9),
    ))
    return items


def _growth_brief_seasonal_entries(today: date) -> list[dict]:
    """Same filter/urgency logic GET /api/cadence already uses (main.py's own
    seasonal block) -- duplicated here rather than shared since /api/cadence's
    version is entangled with tax-deadline merging this doesn't need, and this
    is only the 2nd real caller (code-style.md's bar for extracting a shared
    helper), not worth the coupling risk of refactoring a working endpoint
    mid-sprint."""
    calendar = seasonal_keywords._build_calendar(today.year)
    for e in calendar:
        if e["update_by"] is None:
            e["update_by"] = seasonal_keywords._update_by(e["peak"])
    out = []
    for e in calendar:
        if not (e["peak"] >= today or (e["update_by"] < today < e["peak"])):
            continue
        urg = seasonal_keywords._urgency(e["update_by"], today)
        if urg not in ("OVERDUE", "THIS WEEK"):
            continue
        out.append({
            "season": e["season"], "update_by": e["update_by"].isoformat(),
            "listings_to_update": e["listings_to_update"], "urgency": urg,
        })
    return out


async def _get_or_compute_cached(cache_key: str, ttl: float, fn) -> object:
    """Reuses whatever another screen's own loader already populated under
    this exact cache key (e.g. Home's Ads/COGS/Star Seller panels) instead of
    re-fetching from Etsy -- Growth Brief can end up making ZERO extra Etsy
    calls if Scott just had Home open. Falls through to a fresh compute (and
    populates the same cache) on a real miss."""
    cached = _cache_get(cache_key, ttl=ttl)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(fn)
    _cache_set(cache_key, result)
    return result


async def _compute_growth_brief() -> dict:
    today = await asyncio.to_thread(_shop_today)
    ads, cogs, star_seller, actions_data, bundle_cached = await asyncio.gather(
        _get_or_compute_cached("ads_status", 120, _compute_ads_status),
        _get_or_compute_cached("cogs_status", 120, _compute_cogs_status),
        _get_or_compute_cached("star_seller", 120, _compute_star_seller_status),
        _get_or_compute_cached("actions", 120, _compute_actions),
        _get_or_compute_cached("bundle_opportunities", 3600, _compute_bundle_opportunities),
    )
    # bundle_opportunities' own endpoint wraps the raw list as {"opportunities":
    # [...]} before caching -- a fresh compute here (cache miss) returns the
    # bare list instead, so normalize both shapes rather than let a cache-hit
    # vs cache-miss race silently change this function's behavior.
    bundle_opps = bundle_cached.get("opportunities", []) if isinstance(bundle_cached, dict) else bundle_cached
    seasonal_entries = await asyncio.to_thread(_growth_brief_seasonal_entries, today)
    # _compute_competitor_drift_items() is a pure sidecar-file read (no Etsy
    # call, populated separately by the weekly _competitor_watch_loop()) --
    # cheap enough to call directly every time, no cache needed.
    competitor_drift_items = await asyncio.to_thread(_compute_competitor_drift_items)
    # Same sidecar-read pattern -- populated separately by the weekly
    # _review_theme_loop(). Only the shared_term/counts feed into this
    # non-PII-flagged brief, never the raw quoted review excerpts (those
    # stay behind the PII-flagged get_review_themes tool/dedicated panel).
    review_theme_findings = _load_review_themes().get("findings", [])
    items = _score_growth_brief_items(
        ads, cogs, star_seller, actions_data, bundle_opps, seasonal_entries,
        competitor_drift_items, review_theme_findings,
    )
    return {"items": items[:8], "generated_at": datetime.now(timezone.utc).isoformat()}


@app.get("/api/growth-brief")
async def get_growth_brief(_token: str = Depends(_auth_session_or_bearer)):
    """Ranked, dollar-impact-scored 'what to do this week' list synthesized
    from Ads/COGS/Star Seller/seasonal keywords/bundle opportunities/
    Conversion Doctor -- see _score_growth_brief_items()'s own comment for
    the scoring rules. Cached 60s (short -- this is a merge over other
    endpoints' own longer-TTL caches, so re-running it is cheap)."""
    cached = _cache_get("growth_brief", ttl=60)
    if cached is not None:
        return cached
    data = await _compute_growth_brief()
    _cache_set("growth_brief", data)
    return data


# ── Title A/B Testing (2026-08-06, "significantly improve Frank" idea 3/3) ──
# Scope note (same honest-correction pattern as idea 1's buyer-messaging scope
# fix): the brief was "Photo/Title A/B Testing" -- title testing is fully real
# and built below; photo A/B testing is NOT (Etsy has no per-listing-photo
# split-test mechanism to read results from, and a fabricated "photo B got
# more clicks" number with no real per-photo click data behind it would
# violate the top-priority never-lie rule). Title testing is the real,
# deliverable slice; scoped down rather than shipped fake.
#
# Design constraints this respects (both from CLAUDE.md, both hard rules):
# 1. "Nothing irreversible auto-executes" -- every title swap (A->B, and any
#    eventual revert) goes through the existing staged-action approval queue
#    exactly like a manual title edit. This code never calls
#    EtsyAPIClient().update_listing() directly.
# 2. Ranking Recovery guidance ("Do not edit the same listing again during
#    [the 2-3 week recovery] window -- compound edits extend the recovery
#    period") means a fast title-flip A/B test would actively fight Etsy's
#    own algorithm instead of helping the shop. Rotation windows are floored
#    at db._RANKING_RECOVERY_COOLDOWN_DAYS (21 days) -- the same number the
#    rest of the app already treats as the safe re-edit interval -- not a
#    marketing-textbook "run it for a week" default.
_AB_TESTS_PATH = db.resolve_persistent_path(
    "ab_tests.json",
    fallback=ROOT / "data" / "ab_tests.json",
)


def _load_ab_tests() -> dict:
    try:
        return json.loads(_AB_TESTS_PATH.read_text())
    except (OSError, ValueError):
        return {}


def _save_ab_tests(tests: dict) -> None:
    _AB_TESTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _AB_TESTS_PATH.write_text(json.dumps(tests, indent=2))


def _next_ab_test_id(tests: dict) -> str:
    return str(max((int(k) for k in tests), default=0) + 1)


async def _start_ab_test(listing_id: int, variant_b_title: str, rotation_days: int | None = None) -> dict:
    """Begin tracking a title A/B test. Variant A is whatever the listing's
    REAL title already is -- fetched fresh from Etsy, never assumed or typed
    in by the caller -- since it's already live and needs no staged action to
    "start". Variant B only goes live once Scott approves the staged
    update_title action _ab_test_loop() creates when Variant A's window closes."""
    variant_b_title = (variant_b_title or "").strip()
    if not variant_b_title:
        return {"error": "variant_b_title is empty"}
    if len(variant_b_title) > 140:
        return {"error": f"variant_b_title is {len(variant_b_title)} chars — max 140 (Etsy's platform limit)"}
    days = rotation_days or db._RANKING_RECOVERY_COOLDOWN_DAYS
    if days < db._RANKING_RECOVERY_COOLDOWN_DAYS:
        return {
            "error": f"rotation_days must be at least {db._RANKING_RECOVERY_COOLDOWN_DAYS} — "
                     "shorter windows would compound title edits inside Etsy's own ranking "
                     "recovery period (CLAUDE.md Ranking Recovery Playbook) and hurt the listing "
                     "instead of helping it."
        }
    try:
        listing = await asyncio.to_thread(lambda: EtsyAPIClient().get_listing(listing_id))
    except Exception as exc:
        return {"error": f"could not fetch listing {listing_id} from Etsy: {str(exc)[:200]}"}
    current_title = (listing.get("title") or "").strip()
    if not current_title:
        return {"error": f"listing {listing_id} has no title on Etsy — can't establish variant A"}
    if listing.get("state") != "active":
        return {"error": f"listing {listing_id} is '{listing.get('state')}', not active — can't A/B test a non-live listing"}
    tests = _load_ab_tests()
    for t in tests.values():
        if t["listing_id"] == listing_id and t["status"] not in ("completed", "cancelled"):
            return {"error": f"listing {listing_id} already has an active A/B test (id {t['id']}) — finish or cancel it first"}
    today = (await asyncio.to_thread(_shop_today)).isoformat()
    test_id = _next_ab_test_id(tests)
    test = {
        "id": test_id, "listing_id": listing_id,
        "variant_a_title": current_title, "variant_b_title": variant_b_title,
        "rotation_days": days, "status": "running_a",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "phase_started_at": datetime.now(timezone.utc).isoformat(),
        "variant_a_start_date": today, "variant_a_end_date": None,
        "variant_b_start_date": None, "variant_b_end_date": None,
        "pending_action_id": None, "result": None,
    }
    tests[test_id] = test
    _save_ab_tests(tests)
    return {"ok": True, "test": test}


def _stage_ab_test_title_change(test: dict, title: str) -> int:
    payload = {"listing_id": test["listing_id"], "title": title, "ab_test_id": test["id"]}
    summary = (
        f"A/B test #{test['id']}: switch listing {test['listing_id']} to Variant B — "
        f'"{title}" (Variant A window closed after {test["rotation_days"]} days)'
    )
    return db.enqueue_action("update_title", summary, payload)


async def _ab_test_iteration() -> dict:
    """Daily check: has any running test's current-phase window closed? If so,
    stage the next title change (never applied directly -- see module comment
    above) or, for a completed Variant B window, compute the real comparison
    and close the test out. Idempotent -- safe to run more than once a day."""
    tests = _load_ab_tests()
    if not tests:
        return {"checked": 0, "advanced": 0}
    today = await asyncio.to_thread(_shop_today)
    advanced = 0
    for test in tests.values():
        try:
            phase_started = datetime.fromisoformat(test["phase_started_at"])
        except (KeyError, ValueError):
            continue
        days_in_phase = (datetime.now(timezone.utc) - phase_started).days
        if test["status"] == "running_a" and days_in_phase >= test["rotation_days"]:
            test["variant_a_end_date"] = today.isoformat()
            action_id = await asyncio.to_thread(_stage_ab_test_title_change, test, test["variant_b_title"])
            test["status"] = "awaiting_approval_b"
            test["pending_action_id"] = action_id
            advanced += 1
        elif test["status"] == "running_b" and days_in_phase >= test["rotation_days"]:
            test["variant_b_end_date"] = today.isoformat()
            test["result"] = await asyncio.to_thread(_compute_ab_test_comparison, test)
            test["status"] = "completed"
            advanced += 1
    if advanced:
        _save_ab_tests(tests)
    return {"checked": len(tests), "advanced": advanced}


async def _ab_test_loop() -> None:
    """Daily: same cadence/resilience pattern as _snapshot_loop()."""
    while True:
        delay = await _run_loop_iteration(
            "ab_test", "A/B Tests", _ab_test_iteration,
            on_success_detail=lambda r: f"{r['advanced']} test(s) advanced out of {r['checked']} tracked",
            base_interval=86_400,
        )
        await asyncio.sleep(delay)


def _advance_ab_test(ab_test_id: str, applied_title: str) -> None:
    """Called right after a staged update_title action tagged with ab_test_id
    actually executes on Etsy (see POST /api/queue/{id}/approve) -- moves the
    test from 'awaiting_approval_b' into 'running_b' now that Variant B is
    genuinely live, not the moment it was merely staged. Best-effort: a
    failure here must never block the real Etsy mutation that already
    succeeded, so the caller wraps this and swallows any exception."""
    tests = _load_ab_tests()
    test = tests.get(str(ab_test_id))
    if not test or test["status"] != "awaiting_approval_b":
        return
    test["status"] = "running_b"
    test["phase_started_at"] = datetime.now(timezone.utc).isoformat()
    test["variant_b_start_date"] = _shop_today().isoformat()
    test["pending_action_id"] = None
    _save_ab_tests(tests)


def _cancel_ab_test_for_rejected_action(ab_test_id: str, reason: str) -> None:
    """Called when Scott rejects the staged Variant-B title swap -- the test
    can't silently sit in 'awaiting_approval_b' forever with no path forward,
    so it's marked cancelled with the reason attached rather than left stuck."""
    tests = _load_ab_tests()
    test = tests.get(str(ab_test_id))
    if not test or test["status"] != "awaiting_approval_b":
        return
    test["status"] = "cancelled"
    test["result"] = {"cancelled_reason": reason or "Variant B title change was rejected"}
    test["pending_action_id"] = None
    _save_ab_tests(tests)


def _compute_ab_test_comparison(test: dict) -> dict:
    """Real per-window comparison -- never fabricates a winner. Views/
    favorites come from listing_snapshots (accurately date-bounded daily data
    _snapshot_loop() already collects for every active listing). Orders/
    revenue come from a fresh, date-scoped get_orders() call rather than
    _get_recent_orders_raw()'s shared 100-receipt cache, because that cache
    is explicitly NOT date-bounded (see its own docstring) and can't be
    trusted to isolate one multi-week window from another."""
    listing_id = test["listing_id"]

    def _window_stats(start_date, end_date):
        if not start_date or not end_date:
            return {"views_gained": None, "favorites_gained": None, "days_tracked": 0,
                     "note": "window not closed yet"}
        rows = db.get_listing_snapshot_history(listing_id, start_date, end_date)
        if len(rows) < 2:
            return {"views_gained": None, "favorites_gained": None, "days_tracked": len(rows),
                     "note": "fewer than 2 daily snapshots landed in this window — not enough data"}
        return {
            "views_gained": rows[-1]["views"] - rows[0]["views"],
            "favorites_gained": rows[-1]["num_favorers"] - rows[0]["num_favorers"],
            "days_tracked": len(rows),
        }

    def _window_orders(start_date, end_date):
        if not start_date or not end_date:
            return {"orders": None, "revenue": None, "note": "window not closed yet"}
        try:
            start_ts = int(datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc).timestamp())
            end_ts = int(datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc).timestamp()) + 86_400
            r = EtsyAPIClient().get_orders(limit=100, status="paid", min_created=start_ts, max_created=end_ts)
            orders, revenue = 0, 0.0
            for receipt in r.get("results", []):
                for txn in receipt.get("transactions", []) or []:
                    if txn.get("listing_id") != listing_id:
                        continue
                    qty = txn.get("quantity", 1) or 1
                    price = txn.get("price") or {}
                    amt = (price.get("amount", 0) / price.get("divisor", 100)) if price.get("divisor") else 0
                    orders += qty
                    revenue += amt * qty
            return {"orders": orders, "revenue": round(revenue, 2)}
        except Exception as exc:
            return {"orders": None, "revenue": None, "note": f"order lookup failed: {str(exc)[:150]}"}

    a_stats = _window_stats(test.get("variant_a_start_date"), test.get("variant_a_end_date"))
    b_stats = _window_stats(test.get("variant_b_start_date"), test.get("variant_b_end_date"))
    a_orders = _window_orders(test.get("variant_a_start_date"), test.get("variant_a_end_date"))
    b_orders = _window_orders(test.get("variant_b_start_date"), test.get("variant_b_end_date"))

    verdict, verdict_basis = "inconclusive", "not enough real data to call a winner"
    a_views, b_views = a_stats.get("views_gained"), b_stats.get("views_gained")
    a_ord, b_ord = a_orders.get("orders"), b_orders.get("orders")
    if a_views and b_views and a_ord is not None and b_ord is not None:
        a_conv, b_conv = a_ord / a_views, b_ord / b_views
        if a_conv == b_conv:
            verdict = "tie"
        else:
            verdict = "variant_b" if b_conv > a_conv else "variant_a"
        verdict_basis = f"real conversion rate: A={a_conv:.2%} vs B={b_conv:.2%} (orders ÷ views gained, each window)"
    elif not a_views or not b_views:
        verdict_basis = "zero (or untracked) views gained in one window — conversion rate not computable"

    return {
        "variant_a": {"title": test["variant_a_title"], **a_stats, **a_orders},
        "variant_b": {"title": test["variant_b_title"], **b_stats, **b_orders},
        "verdict": verdict, "verdict_basis": verdict_basis,
    }


@app.get("/api/ab-tests")
async def get_ab_tests(_token: str = Depends(_auth_session_or_bearer)):
    """List every title A/B test, newest first."""
    tests = await asyncio.to_thread(_load_ab_tests)
    ordered = sorted(tests.values(), key=lambda t: int(t["id"]), reverse=True)
    return {"tests": ordered}


@app.post("/api/ab-tests")
async def create_ab_test(body: dict, _token: str = Depends(_rate_limited_auth)):
    """Start a new title A/B test. Body: {listing_id, variant_b_title, rotation_days?}."""
    listing_id = body.get("listing_id")
    variant_b_title = body.get("variant_b_title", "")
    rotation_days = body.get("rotation_days")
    if not listing_id:
        raise HTTPException(status_code=422, detail="listing_id is required")
    result = await _start_ab_test(int(listing_id), variant_b_title, rotation_days)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@app.post("/api/ab-tests/{test_id}/cancel")
async def cancel_ab_test(test_id: str, _token: str = Depends(_rate_limited_auth)):
    """Manually cancel a running test (e.g. Scott changes his mind mid-test).
    Does not revert any title already live -- that's a separate, ordinary
    update_title action if he wants the original title back."""
    tests = await asyncio.to_thread(_load_ab_tests)
    test = tests.get(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    if test["status"] in ("completed", "cancelled"):
        raise HTTPException(status_code=409, detail=f"test already {test['status']}")
    test["status"] = "cancelled"
    test["result"] = {"cancelled_reason": "manually cancelled"}
    await asyncio.to_thread(_save_ab_tests, tests)
    return {"ok": True, "test": test}


@app.get("/api/quality-audit/latest")
async def get_latest_quality_audit(_token: str = Depends(_auth_session_or_bearer)):
    """Today tab's 'View details' on the Quality Audit alert card (2026-07-31 —
    Scott: "Why don't these have the option fix? I know you can"). The card
    itself only ever shows the one-line aggregate ("PASS:0 WARN:36 FAIL:22")
    that _quality_audit_iteration() wrote into the heartbeat's detail string;
    the real per-listing FAIL text it also captured (`summary`, up to 1500
    chars of listing_integrity_check.py's own "✗ FAIL (" block) only ever
    lived in the quality_audits table and, when real_failed > 0, an
    ops_runbook.md entry — never surfaced in the app itself. This returns
    that same stored summary so Scott can see specifics without leaving Today.

    Caveat surfaced here rather than solved: `failed` in the stored row can
    include listings that errored fetching from Etsy that run (transient,
    not a content problem) — that per-run distinction (`fetch_errors`) is
    computed in-memory during the audit but never persisted to the
    quality_audits table, so it can't be reconstructed after the fact for a
    past run. Told to the caller as `may_include_fetch_errors` rather than
    silently presenting every FAIL as a confirmed content problem."""
    history = await asyncio.to_thread(db.get_quality_audit_history, 1)
    if not history:
        return {"found": False}
    row = history[-1]
    return {
        "found": True,
        "ts": row.get("ts"),
        "passed": row.get("passed"),
        "warned": row.get("warned"),
        "failed": row.get("failed"),
        "audited_count": row.get("audited_count"),
        "summary": row.get("summary") or "",
        "may_include_fetch_errors": bool(row.get("failed")),
    }


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
        try:
            db.set_agent_heartbeat(name, label, "error", str(detail)[:300])
        except Exception as hb_exc:
            # 2026-07-21: this write used to be unguarded -- every one of the 5
            # real background loops calls _run_loop_iteration() with nothing
            # wrapping it (`delay = await _run_loop_iteration(...)`), so a DB
            # hiccup right here (disk full, locked file, corrupted db) would
            # propagate out of this except block uncaught, killing the whole
            # loop's asyncio task permanently -- the ORIGINAL error (the thing
            # this heartbeat write exists to report) plus every future run of
            # that loop would then be silently gone until a full process
            # restart. A broken heartbeat write must degrade to "this one
            # iteration's status board update didn't happen," never to "this
            # loop stops running forever."
            print(f"[{name}] heartbeat write also failed (loop continues): {hb_exc}", flush=True)
        return delay


def _safe_set_agent_heartbeat(name: str, label: str, status: str, detail: str) -> None:
    """db.set_agent_heartbeat(), guarded the same way _run_loop_iteration()'s
    own heartbeat write already is (2026-08-05 full-Etsy-audit finding) -- for
    the two hand-rolled calendar-gated loops (_daily_brief_loop,
    _calendar_tasks_loop) that don't route through _run_loop_iteration at all
    (they're date-gated, not interval-based) and so never inherited that
    hardening. Without this, a DB hiccup on any of their several unguarded
    set_agent_heartbeat() calls raises straight out of their `while True:`
    body -- an unhandled exception inside an asyncio.create_task() coroutine
    silently ends that task forever, and _calendar_tasks_loop alone backs 10
    different sub-tasks (weekly monitors, monthly shop health, competitor
    research, seasonal keywords, ads threshold check, Star Seller check,
    scheduled art/coloring checks, Google Calendar sync, Etsy file
    inventory)."""
    try:
        db.set_agent_heartbeat(name, label, status, detail)
    except Exception as exc:
        print(f"[{name}] heartbeat write failed (loop continues): {exc}", flush=True)


# ── Persistence: daily snapshots + history ───────────────────────────────────────


async def _take_snapshot() -> str:
    """Capture today's metrics + active listings into the database (upsert/day)."""
    metrics = await asyncio.to_thread(_metrics_sync)
    listings = (await asyncio.to_thread(_listings_sync, "active")).get("listings", [])
    d = await asyncio.to_thread(db.record_metric_snapshot, metrics, listings)
    # 2026-07-22 Phase 3: piggyback Star Seller/Ads/COGS status history capture on
    # this same daily loop rather than a second scheduler. Built inline (not a
    # module-level constant) since _compute_ads_status()/_compute_cogs_status() are
    # defined further down this file -- a module-level tuple referencing them here
    # would NameError at import time; this list is only evaluated once _take_snapshot()
    # actually runs, well after the whole module has finished loading. Each panel
    # gets its own try/except -- _compute_star_seller_status()/_compute_cogs_status()
    # make real Etsy calls and can fail -- so one panel's failure never breaks the
    # metric_snapshots write above (already returned as `d`) or the other panels.
    for panel, compute_fn in (
        ("star_seller", _compute_star_seller_status),
        ("ads_roas", _compute_ads_status),
        ("cogs_margin", _compute_cogs_status),
    ):
        try:
            data = await asyncio.to_thread(compute_fn)
            await asyncio.to_thread(db.record_status_snapshot, panel, data)
        except Exception as exc:
            print(f"[snapshot] {panel} status snapshot failed (non-fatal): {exc}", flush=True)
    print(f"[snapshot] recorded {d}: {len(listings)} listings, persistent={db.is_persistent()}", flush=True)
    return d


_SNAPSHOT_BASE_INTERVAL = 86_400


async def _maybe_prune_after_snapshot(delay: float, base_interval: float) -> list[str]:
    """Run the daily trash + rate-limit-log prune only when the snapshot
    iteration that just completed succeeded (delay == base_interval).
    _run_loop_iteration() returns exactly `base_interval` on success or a
    shorter jittered backoff delay (capped below base_interval) on failure —
    so this equality is an exact success test, not a heuristic. Before this
    gate existed, a failing/backing-off snapshot loop (e.g. Etsy down) would
    still run both prune passes on every retry, far more than the intended
    once/day. Tolerant of its own errors either way — a prune failure must
    never affect the snapshot loop's own success/backoff timing.

    Returns a list of failure description strings (empty if both prunes ran
    clean or were skipped). 2026-07-21: these failures used to be print()-only
    — invisible outside server logs, so e.g. the trash vault silently failing
    to prune for weeks (data/trash/ growing unbounded) would never surface on
    the dashboard. The caller folds any returned failures into the snapshot
    loop's own heartbeat detail (as a "warning", not "error" — see caller)."""
    if delay != base_interval:
        return []
    failures: list[str] = []
    try:
        import trash as _trash
        n = await asyncio.to_thread(_trash.prune)
        if n:
            print(f"[trash] pruned {n} expired entr{'y' if n == 1 else 'ies'}", flush=True)
    except Exception as exc:
        print(f"[trash] prune error: {exc}", flush=True)
        failures.append(f"trash prune failed: {exc}")
    try:
        n = await asyncio.to_thread(db.prune_rate_limit_log)
        if n:
            print(f"[rate-limit-log] pruned {n} sample(s) older than 30 days", flush=True)
    except Exception as exc:
        print(f"[rate-limit-log] prune error: {exc}", flush=True)
        failures.append(f"rate-limit-log prune failed: {exc}")
    return failures


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
        prune_failures = await _maybe_prune_after_snapshot(delay, _SNAPSHOT_BASE_INTERVAL)
        if prune_failures:
            # Overwrite the "snapshot" heartbeat _run_loop_iteration just wrote with a
            # "warning" (not "error" -- the snapshot itself succeeded; only the
            # piggybacked prune failed, and per the docstring above that must never
            # affect this loop's own success/backoff timing) so the failure is
            # visible on the Agents screen instead of only in server stdout.
            _safe_set_agent_heartbeat(
                "snapshot", "Snapshot", "warning",
                "Daily metric snapshot recorded, but: " + "; ".join(prune_failures),
            )
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
        # 2026-07-19: the manual POST /api/suggestions path already checks
        # `_suggestions_warming` before spawning a compute (so a second visitor
        # hitting a cold cache doesn't kick off a redundant one), but this
        # scheduled tick never did -- if the loop's timer fired at the same
        # moment a dashboard request spawned _run_suggestions_safely(), both
        # could run _compute_suggestions_inner() concurrently: double the
        # Anthropic spend for that tick (3 Etsy pulls + a ~25s synthesis call,
        # twice). Same guard, same reasoning, just applied to the other caller.
        if _suggestions_warming:
            return {"skipped": True, "reason": "a compute is already in flight"}
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


def _quality_audit_skip_result(reason: str, subtask_failures: list[str] | None = None) -> dict:
    """Shared shape for _quality_audit_iteration()'s early-exit skip paths
    (manifest missing / manifest empty) — was a duplicated dict literal at two
    call sites a few lines apart. subtask_failures carries forward any of the
    pre-manifest-check subtasks (retention prune, KB rotation, etc.) that
    already failed before the early exit — see _quality_audit_iteration()."""
    return {
        "skipped": True, "passed": 0, "warned": 0, "failed": 0, "reason": reason,
        "subtask_failures": subtask_failures or [],
    }


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


_BUYER_DATA_RETENTION_DAYS = 90  # GDPR-motivated retention window (2026-07-18 compliance pass)
_ID_STATE_FILE_MAX_KEPT = 2000   # notified_orders.json / message_drafts/sent_log.json have no
                                  # per-entry timestamp (just a flat receipt/message-id set) --
                                  # capping to the highest-N ids approximates a recency window
                                  # without adding timestamp bookkeeping to a stable, simple file.


def _prune_buyer_data_retention() -> dict:
    """GDPR-motivated data-minimization pass (2026-07-18 compliance hardening):
    buyer-referencing local artifacts (drafted reply text that quotes or
    references a buyer's message or review, and per-order notification state)
    have no reason to outlive Etsy's own order/message history, which remains
    the authoritative record. Deletes dated draft files
    (data/message_drafts/*.json, e.g. `2026-07-18_drafts.json` from
    tools/etsy_autoresponder.py, `review_responses_2026-07-18.json` from
    tools/review_monitor.py) older than _BUYER_DATA_RETENTION_DAYS by file
    mtime, and caps the two ID-only state files (data/notified_orders.json,
    data/message_drafts/sent_log.json) to their most recent
    _ID_STATE_FILE_MAX_KEPT entries, since those carry no per-entry timestamp
    to prune by age. Never raises -- called from the daily quality-audit loop,
    and a partial failure here should not break the rest of that loop."""
    result = {"drafts_deleted": 0, "notified_orders_trimmed": 0, "sent_log_trimmed": 0}
    cutoff_ts = datetime.now(timezone.utc).timestamp() - (_BUYER_DATA_RETENTION_DAYS * 86400)

    drafts_dir = ROOT / "data" / "message_drafts"
    if drafts_dir.is_dir():
        for f in drafts_dir.glob("*.json"):
            if f.name == "sent_log.json":
                continue  # an ID list, not a dated draft file -- handled below
            try:
                if f.stat().st_mtime < cutoff_ts:
                    f.unlink()
                    result["drafts_deleted"] += 1
            except OSError as exc:
                print(f"[retention] could not prune {f}: {exc}", flush=True)

    # notified_orders.json: same resolver tools/order_notifier.py uses (mirrored
    # there since that script runs as a standalone subprocess, not importable
    # from this module) -- both must agree on the real path, or pruning here
    # would silently operate on a stale copy while order_notifier.py keeps
    # writing to the durable one (2026-08-06 full-system audit).
    _notified_orders_path = db.resolve_persistent_path(
        "notified_orders.json", fallback=ROOT / "data" / "notified_orders.json",
    )
    for path, key, id_key in (
        (_notified_orders_path, "notified_orders_trimmed", "notified"),
        (drafts_dir / "sent_log.json", "sent_log_trimmed", "sent_ids"),
    ):
        try:
            if not path.is_file():
                continue
            data = json.loads(path.read_text())
            ids = data.get(id_key, [])
            if len(ids) <= _ID_STATE_FILE_MAX_KEPT:
                continue
            try:
                ids_sorted = sorted(ids, key=lambda x: int(x))
            except (TypeError, ValueError):
                ids_sorted = ids  # non-numeric ids -- keep existing order, just truncate
            kept = ids_sorted[-_ID_STATE_FILE_MAX_KEPT:]
            path.write_text(json.dumps({id_key: kept}, indent=2))
            result[key] = len(ids) - len(kept)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[retention] could not prune {path}: {exc}", flush=True)

    if any(result.values()):
        print(f"[retention] pruned buyer-referencing data: {result}", flush=True)
    return result


async def _quality_audit_iteration() -> dict:
    """One run of the daily quality audit: rotate oversized KB files, run the
    read-only listing integrity check against a rotating ~1/3 subset of the
    catalog (see _select_quality_audit_ids), record the trend, and escalate a
    FAIL finding to ops_runbook.md. Raises on a genuine run failure (subprocess
    error, unparseable output) so `_run_loop_iteration` backs off and retries
    sooner than the normal 24h cadence; returns a result dict on a clean run
    even if the audit itself found failing listings (that's a content-level
    signal surfaced via `on_success_status`, not a loop failure).

    2026-07-21: the retention/KB-rotation/recurring-failures/db-record
    subtasks below used to be print()-only on failure -- invisible outside
    server logs. A silently-broken buyer-data retention pass in particular is
    a real compliance concern (CLAUDE.md's retention rule), not just
    maintenance trivia, so any subtask failure is now collected into
    `subtask_failures` and returned to the caller, which folds it into the
    "quality_audit" heartbeat as a warning without affecting the loop's own
    success/backoff timing (the audit itself still ran fine)."""
    subtask_failures: list[str] = []
    try:
        await asyncio.to_thread(_prune_buyer_data_retention)
    except Exception as exc:
        print(f"[retention] buyer-data retention pass failed: {exc}", flush=True)
        subtask_failures.append(f"buyer-data retention prune failed: {exc}")

    for kb_path in (_OPS_RUNBOOK_PATH, _CEO_LEARNINGS_PATH):
        try:
            if await asyncio.to_thread(_summarize_and_rotate_kb_file, kb_path):
                print(f"[kb-rotate] condensed older history in {kb_path.name}", flush=True)
        except Exception as exc:
            print(f"[kb-rotate] check failed for {kb_path.name}: {exc}", flush=True)
            subtask_failures.append(f"KB rotation failed for {kb_path.name}: {exc}")

    try:
        if await asyncio.to_thread(_promote_recurring_failures, _OPS_RUNBOOK_PATH):
            print("[ops-runbook] refreshed Known Recurring Issues section", flush=True)
    except Exception as exc:
        print(f"[ops-runbook] recurring-issues check failed: {exc}", flush=True)
        subtask_failures.append(f"recurring-issues promotion failed: {exc}")

    # data/ is excluded from the Docker build context (.dockerignore), so
    # listing_manifest.json won't exist in fresh Railway deployments until
    # build_manifest.py has been run at least once. Skip gracefully rather
    # than crashing the loop — the heartbeat will surface this as a warning.
    manifest_path = ROOT / "data" / "listing_manifest.json"
    if not await asyncio.to_thread(manifest_path.exists):
        print("[quality-audit] skipping — listing_manifest.json not found (run build_manifest.py)", flush=True)
        return _quality_audit_skip_result(
            "listing_manifest.json not found — run build_manifest.py first", subtask_failures
        )

    def _load_manifest_and_select_ids() -> list[str]:
        with open(manifest_path) as f:
            manifest = json.load(f)
        return _select_quality_audit_ids(manifest)

    audit_ids = await asyncio.to_thread(_load_manifest_and_select_ids)
    if not audit_ids:
        print("[quality-audit] skipping — listing_manifest.json is empty", flush=True)
        return _quality_audit_skip_result("listing_manifest.json has no listings", subtask_failures)
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
        subtask_failures.append(f"quality-audit db record failed: {exc}")
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
            "fetch_errors": fetch_errors, "real_failed": real_failed,
            "subtask_failures": subtask_failures}


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
            # A subtask failure (retention prune, KB rotation, etc.) never overrides
            # "error" (a real content FAIL always takes priority) but does bump an
            # otherwise-clean "ok" run up to "warning" -- see _quality_audit_iteration()'s
            # docstring for why these were previously invisible outside server logs.
            on_success_status=lambda r: (
                "error" if not r.get("skipped") and r.get("real_failed", r["failed"]) > 0
                else "warning" if r.get("skipped") or r.get("subtask_failures")
                else "ok"
            ),
            on_success_detail=lambda r: r.get("reason", (
                f"PASS:{r['passed']} WARN:{r['warned']} FAIL:{r['failed']}"
                + (f" ({r['fetch_errors']} fetch error(s), not content failures)"
                   if r.get('fetch_errors') else "")
            )) + (
                f" — subtask issue(s): {'; '.join(r['subtask_failures'])}"
                if r.get("subtask_failures") else ""
            ),
            base_interval=86_400,
        )
        await asyncio.sleep(delay)


async def _file_audit_iteration() -> dict:
    """One run of tools/audit_product_files.py's live-Etsy-verified file
    integrity audit -- the check that separates 'this product is missing its
    local backup copy' (verified_live, not urgent) from 'a customer could buy
    this and receive nothing' (genuinely_missing, the real compliance risk
    _product_file_integrity_alerts() escalates).

    2026-07-21 finding: this audit was fully built (the audit() function, the
    /api/alerts source, and the Products-screen per-card badge all shipped)
    but NOTHING ever called it automatically -- it only ran if someone
    manually typed `python tools/audit_product_files.py` from a machine with
    real Etsy credentials, which in practice never happened in production.
    data/file_audit_report.json never existed, so _file_audit_report() always
    returned None, so the critical alert and every Products-screen file_audit
    badge were silently dead from the day they shipped. This loop is the fix:
    the exact same audit_product_files.audit() logic, now actually scheduled.

    Imports audit_product_files lazily (not at module top level) -- that
    module itself does `import main as _main` to reuse this file's own
    _build_products_status()/_catalog_file_exists()/_product_catalog_overrides()
    helpers rather than duplicating them, which would be a circular import if
    done at main.py's top level. By the time this loop actually runs (well
    after startup), `main` is already fully initialized in sys.modules, so
    the nested import just reuses the live module -- no reinitialization,
    no cycle."""
    import audit_product_files as _fa
    result = await asyncio.to_thread(_fa.audit)
    result["audited_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path = _fa._report_path()

    def _write():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(result, indent=2))
        tmp.replace(path)

    await asyncio.to_thread(_write)
    return result


async def _file_audit_loop() -> None:
    """Run the live-Etsy file-integrity audit once a day (sooner on a backoff
    retry after a failure) so the file_audit_report.json backing
    _product_file_integrity_alerts() and every Products-screen file_audit
    badge is never more than a day stale. See _file_audit_iteration()'s
    docstring for why this loop needed to exist at all."""
    await asyncio.sleep(180)  # let the app finish booting; behind quality_audit's own 120s
    while True:
        delay = await _run_loop_iteration(
            "file_audit", "File Integrity Audit", _file_audit_iteration,
            on_success_status=lambda r: "error" if r.get("genuinely_missing") else (
                "warning" if r.get("skipped") else "ok"
            ),
            on_success_detail=lambda r: (
                f"verified_live:{len(r['verified_live'])} "
                f"genuinely_missing:{len(r['genuinely_missing'])} "
                f"skipped:{len(r['skipped'])}"
            ),
            base_interval=86_400,
        )
        await asyncio.sleep(delay)


def _run_sku_taxonomy_backfill_batch() -> dict:
    """One weekly batch of the SKU/category backfill sweep (2026-07-26,
    "every listing categorized and has a SKU" -- Scott). Builds the durable
    queue on first run (a real ~170-listing Etsy sweep, hence this whole
    function is dispatched via asyncio.to_thread from the loop below, never
    called directly on the event loop), then stages up to
    _BACKFILL_BATCH_SIZE new update_sku_and_category actions for approval --
    the pacing Scott asked for (~15-20/week) so this doesn't compound-edit
    the whole shop's search ranking at once (CLAUDE.md Ranking Recovery
    Playbook). Staging itself makes no Etsy calls and carries no ranking
    risk -- only Scott's own approval (via the normal Action Center flow,
    including bulk-approve) actually edits a listing, so the real pacing
    control is how many NEW actions appear here per run, not anything that
    blocks approval itself."""
    queue = _read_sku_taxonomy_backfill_queue()
    if not queue:
        queue = _build_sku_taxonomy_backfill_queue()
        _write_sku_taxonomy_backfill_queue(queue)
    needs_fix = [pid for pid, e in queue.items() if e["status"] == "needs_fix"]
    if not needs_fix:
        done = sum(1 for e in queue.values() if e["status"] in ("ok", "done"))
        return {"status": "ok", "staged": 0, "detail": f"backfill complete — {done}/{len(queue)} listings already correct or fixed"}

    pending = db.list_actions("pending")
    pending_listing_ids = {
        str((a.get("payload") or {}).get("listing_id"))
        for a in pending if a.get("type") == "update_sku_and_category"
    }
    staged = 0
    errors = []
    for pid in needs_fix:
        if staged >= _BACKFILL_BATCH_SIZE:
            break
        entry = queue[pid]
        lid = entry["listing_id"]
        if str(lid) in pending_listing_ids:
            continue  # already staged and awaiting approval -- don't duplicate
        payload = {"listing_id": lid}
        try:
            live = EtsyAPIClient().get_listing(lid)
        except Exception as exc:
            errors.append(f"{pid}: could not re-fetch listing {lid}: {exc}")
            continue
        if live.get("sku") != entry["target_sku"]:
            payload["sku"] = entry["target_sku"]
        if entry["target_taxonomy_id"] is not None and live.get("taxonomy_id") != entry["target_taxonomy_id"]:
            payload["taxonomy_id"] = entry["target_taxonomy_id"]
        if "sku" not in payload and "taxonomy_id" not in payload:
            entry["status"] = "ok"  # already correct on a re-check -- nothing to stage
            continue
        payload["_state_at_staging"] = live.get("state")
        candidate = {"type": "update_sku_and_category", "payload": payload}
        ok, msg = _validate_staged_action(candidate)
        if not ok:
            errors.append(f"{pid}: {msg}")
            continue
        parts = []
        if "sku" in payload:
            parts.append(f"sku→{payload['sku']}")
        if "taxonomy_id" in payload:
            parts.append(f"category→{payload['taxonomy_id']}")
        summary = f"SKU/category fix ({', '.join(parts)}): {pid} (listing {lid})"
        db.enqueue_action("update_sku_and_category", summary, payload)
        entry["status"] = "staged"
        staged += 1
    _write_sku_taxonomy_backfill_queue(queue)
    with _cache_lock:
        _cache.pop("actions", None)
    if staged:
        remaining = sum(1 for e in queue.values() if e["status"] == "needs_fix")
        db.add_todo(
            f"SKU/category backfill: staged {staged} listing fix(es) this week for your approval "
            f"in the Action Center — {remaining} still queued for future weeks.",
            added_by="frank", category="general",
        )
    detail = f"staged:{staged} errors:{len(errors)}"
    if errors:
        detail += f" ({'; '.join(errors[:3])}{'...' if len(errors) > 3 else ''})"
    return {"status": "warning" if errors else "ok", "staged": staged, "detail": detail}


def _get_interval_loop_last_run_at(name: str) -> datetime | None:
    """Persisted "when did this fixed-interval loop last actually complete a
    run" timestamp -- restart-safety companion to _get_calendar_task_last_run()
    (2026-08-05 full-Etsy-audit finding). _sku_taxonomy_backfill_loop and
    _catalog_reconciliation_loop each pace themselves purely via an in-process
    asyncio.sleep(base_interval) between runs -- that clock resets to zero on
    every restart (this app deploys often), and because each batch dedupes
    against already-staged actions rather than replaying the same work, a
    restart doesn't just re-run harmlessly, it stages the NEXT batch of up to
    _BACKFILL_BATCH_SIZE/_RECONCILIATION_BATCH_SIZE new items -- several
    redeploys in one day could put far more pending approvals in front of
    Scott than the weekly pacing he approved. Stored via the same db.settings
    table _get_calendar_task_last_run() uses, keyed distinctly."""
    val = db.get_setting(f"interval_loop_last_run_at_{name}")
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except ValueError:
        return None


def _set_interval_loop_last_run_at(name: str, when: datetime) -> None:
    db.set_setting(f"interval_loop_last_run_at_{name}", when.isoformat())


async def _wait_for_interval_loop_turn(name: str, base_interval: float) -> None:
    """Sleeps out whatever's left of base_interval since this loop's last
    completed run, so a restart mid-week can't re-trigger it early. A no-op
    (returns immediately) the first time a name has ever run."""
    last_run = _get_interval_loop_last_run_at(name)
    if last_run is None:
        return
    elapsed = (datetime.now(timezone.utc) - last_run).total_seconds()
    remaining = base_interval - elapsed
    if remaining > 0:
        await asyncio.sleep(remaining)


def _record_interval_loop_run_if_succeeded(name: str) -> None:
    """Call right after _run_loop_iteration(name, ...) returns. Only persists a
    "last run at" timestamp when that iteration actually succeeded (_run_loop_
    iteration resets _LOOP_FAILURE_COUNTS[name] to 0 on success, line ~6469) --
    a FAILED iteration must never advance the restart-safety clock, or a single
    transient error followed by a restart during its short backoff window would
    make _wait_for_interval_loop_turn() wait out the full weekly interval before
    retrying, silently disabling the loop for up to 7 days over one hiccup."""
    if _LOOP_FAILURE_COUNTS.get(name, 0) == 0:
        _set_interval_loop_last_run_at(name, datetime.now(timezone.utc))


async def _sku_taxonomy_backfill_loop() -> None:
    """Weekly pass staging SKU/taxonomy_id fixes for listings that are
    missing or wrong (see _run_sku_taxonomy_backfill_batch's docstring).
    base_interval=604_800 (7 days) is the pacing mechanism Scott approved
    for this ~170-listing sweep."""
    await asyncio.sleep(300)  # let the app finish booting, behind every other startup loop
    while True:
        await _wait_for_interval_loop_turn("sku_taxonomy_backfill", 604_800)
        delay = await _run_loop_iteration(
            "sku_taxonomy_backfill", "SKU + Category Backfill",
            lambda: asyncio.to_thread(_run_sku_taxonomy_backfill_batch),
            on_success_status=lambda r: r["status"],
            on_success_detail=lambda r: r["detail"],
            base_interval=604_800,
        )
        _record_interval_loop_run_if_succeeded("sku_taxonomy_backfill")
        await asyncio.sleep(delay)


_RECONCILIATION_BATCH_SIZE = 10  # same pacing philosophy as _BACKFILL_BATCH_SIZE -- a first-ever
                                  # backlog shouldn't dump dozens of approvals on Scott at once


def _known_etsy_listing_ids() -> set[str]:
    """Union of every etsy_listing_id Frank already has a local record of,
    across BOTH local registries (2026-08-05, catalog reconciliation
    feature) -- product_catalog.json + its override sidecar, and
    data/listing_manifest.json + its override sidecar. A live Etsy listing
    missing from ALL FOUR is a true orphan (the exact koozie/planner
    failure mode); being known to only one is a narrower partial-gap case
    this sweep deliberately does NOT try to fix (see the design plan's
    explicit scoping note -- that's a safer, no-guessing sync and a
    reasonable follow-up, not this pass)."""
    ids: set[str] = set()
    try:
        catalog = json.loads(Path("data/product_catalog.json").read_text())
    except (OSError, json.JSONDecodeError):
        # Matches _product_catalog_overrides()/_listing_manifest_overrides()'s own
        # error handling below -- a malformed (but readable) catalog file used to
        # raise an uncaught JSONDecodeError here, crashing this whole function for
        # every call site (2026-08-05 full-Etsy-audit finding).
        catalog = []
    for entry in catalog:
        lid = entry.get("etsy_listing_id")
        if lid:
            ids.add(str(lid))
    for ov in _product_catalog_overrides().values():
        lid = ov.get("etsy_listing_id")
        if lid:
            ids.add(str(lid))
    try:
        import listing_integrity_check as lic
        manifest = lic._load_json(lic.MANIFEST_PATH)
    except Exception:
        manifest = {}
    ids.update(str(k) for k in manifest.keys())
    ids.update(str(k) for k in _listing_manifest_overrides().keys())
    return ids


def _run_catalog_reconciliation_batch() -> dict:
    """One weekly pass of the catalog-reconciliation sweep (2026-08-05,
    the koozie/planner listing-mismatch follow-up -- Scott: "I need him to
    recognize things on Etsy not being in there and add them"). Walks
    every live Etsy listing and stages a register_product action for
    anything absent from BOTH local registries. Classification (see
    classify_listings_batch()) is never auto-committed -- every stage is
    Scott's to approve or correct in Approvals, same fail-closed
    philosophy as the manifest gate above. Capped at
    _RECONCILIATION_BATCH_SIZE new stages per run.

    Deliberately NOT coordinated with listing_compliance_sweep.py as a
    scheduling matter -- that sweep is Scott-triggered on demand (a Workflows
    command, not an automatic recurring loop; see _EXEC_COMMANDS
    ["listing_compliance_sweep"]), so there's no two-automatic-loops timing
    race to guard against. There WAS a real data-level gap here though
    (found in the 2026-08-05 full-Etsy-functionality audit, not just a
    timing concern): listing_compliance_sweep.py used to read only the
    git-tracked data/listing_manifest.json, never this loop's own
    listing_manifest_overrides.json sidecar writes -- so a listing this
    loop had just correctly registered would still fail the next compliance
    sweep as "unmapped" and get an incorrect deactivate_listing staged.
    Fixed by giving listing_integrity_check.py a single load_manifest_with_
    overrides() that both this loop's callers and listing_compliance_
    sweep.py's run_sweep() now use, so the two registries genuinely can't
    disagree on this specific question again."""
    client = EtsyAPIClient()
    # 2026-08-05 (full-Etsy-audit finding): this used to catch the fetch failure
    # and return {"status": "error", ...} as a normal return value. _run_loop_
    # iteration() only takes the exponential-backoff retry path when fn() RAISES
    # -- a normal return (even one carrying status="error" in its payload) looks
    # like success to it, resets the failure counter, and schedules the next
    # attempt a full 7 days out instead of retrying soon. Letting this raise
    # (matching _build_sku_taxonomy_backfill_queue()'s sibling pattern) gives a
    # transient Etsy outage the real fast-retry-then-backoff behavior instead of
    # a week-long stall.
    listings = client.get_shop_listings_all(state="active")

    known_ids = _known_etsy_listing_ids()
    pending = db.list_actions("pending")
    pending_listing_ids = {
        str((a.get("payload") or {}).get("etsy_listing_id"))
        for a in pending if a.get("type") == "register_product"
    }
    orphans = [
        l for l in listings
        if str(l.get("listing_id")) not in known_ids
        and str(l.get("listing_id")) not in pending_listing_ids
    ]
    if not orphans:
        return {"status": "ok", "staged": 0,
                "detail": f"no orphaned listings found ({len(listings)} live listings checked, all known)"}

    batch = orphans[:_RECONCILIATION_BATCH_SIZE]
    classifications = classify_listings_batch(batch)
    class_by_id = {c.get("listing_id"): c for c in classifications}

    staged = 0
    errors = []
    for listing in batch:
        lid = listing.get("listing_id")
        c = class_by_id.get(lid, {})
        category = c.get("category", "uncategorized")
        name = (listing.get("title") or f"Listing {lid}")[:100]
        prefix = {"3d_print_physical": "P3D"}.get(category, "MISC")
        product_id = _slugify_product_id(name, prefix)
        payload = {
            "product_id": product_id, "name": name, "category": category,
            "price": _price_float(listing.get("price")), "etsy_listing_id": lid,
            "confidence": c.get("confidence"), "reasoning": c.get("reasoning"),
        }
        ok, msg = _validate_staged_action({"type": "register_product", "payload": payload})
        if not ok:
            errors.append(f"{lid}: {msg}")
            continue
        summary = f"Register orphaned listing {lid} ({category}, {c.get('confidence', '?')} confidence): {name}"
        db.enqueue_action("register_product", summary, payload)
        staged += 1

    with _cache_lock:
        _cache.pop("actions", None)
    if staged:
        remaining = len(orphans) - len(batch)
        db.add_todo(
            f"Catalog reconciliation: found {len(orphans)} live Etsy listing(s) with no local "
            f"record -- staged {staged} for your review in Approvals"
            + (f" ({remaining} more queued for next week)." if remaining else "."),
            added_by="frank", category="general",
        )
    detail = f"orphans_found:{len(orphans)} staged:{staged} errors:{len(errors)}"
    if errors:
        detail += f" ({'; '.join(errors[:3])}{'...' if len(errors) > 3 else ''})"
    return {"status": "warning" if errors else "ok", "staged": staged, "detail": detail}


async def _catalog_reconciliation_loop() -> None:
    """Weekly pass staging register_product actions for orphaned listings
    (see _run_catalog_reconciliation_batch's docstring). base_interval=
    604_800 (7 days), same cadence as the SKU/category backfill loop this
    is modeled on -- including that loop's restart-safety fix (2026-08-05
    full-Etsy-audit finding): _wait_for_interval_loop_turn()/_record_
    interval_loop_run_if_succeeded() so a mid-week redeploy can't re-stage
    a fresh batch of register_product actions before a week has actually
    passed."""
    await asyncio.sleep(300)  # let the app finish booting, behind every other startup loop
    while True:
        await _wait_for_interval_loop_turn("catalog_reconciliation", 604_800)
        delay = await _run_loop_iteration(
            "catalog_reconciliation", "Catalog Reconciliation",
            lambda: asyncio.to_thread(_run_catalog_reconciliation_batch),
            on_success_status=lambda r: r["status"],
            on_success_detail=lambda r: r["detail"],
            base_interval=604_800,
        )
        _record_interval_loop_run_if_succeeded("catalog_reconciliation")
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
                f"hourly health loop killed a stuck background build: {cmd_name} (pid {pid}). {detail}",
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
                    f"hourly health loop reaped a failed background build: {cmd_name} (pid {pid}). {detail}",
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
        context = f"hourly health loop detected a problem: {detail}"
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
                f"hourly health loop found {vol} mounted but not writable: {exc}. "
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
                    f"hourly health loop found the hub.db snapshot at {backup_hub_db.OUT_PATH} "
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
    """Every hour: confirm Etsy is actually live (a real get_shop() call) and
    that ANTHROPIC_API_KEY is at least set (2026-08-04 AI Core screen audit --
    this docstring previously claimed Anthropic gets the same "actually live"
    treatment as Etsy; it doesn't, it's a bare env-var presence check, same gap
    the AI Core screen's own credentials display had). Same checks /api/ping
    exposes manually, run here on a timer so a regression surfaces in
    ops_runbook.md without anyone needing to remember to hit that URL,
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
    """Fire a daily shop-status email at the Settings 'Notifications' hour
    (default 6 AM), checked once per hour, in the SHOP'S LOCAL time -- not
    UTC. Checks db.get_setting("daily_brief_hour"/"daily_brief_enabled") live
    on every tick so a Settings change takes effect on the very next check,
    no restart needed.

    Does not use _run_loop_iteration because the timing logic is calendar-based
    (once per calendar day) rather than interval-based (every N seconds).
    Failures are logged but never crash the server.

    2026-08-06 Settings audit finding: this used to compare `datetime.now(
    timezone.utc).hour == 6` -- for a US shop (default timezone America/
    New_York) that fires the brief at 1-2 AM local time depending on DST, the
    middle of the night. Now uses _shop_now() (already used elsewhere in this
    file for exactly this class of bug) so the send hour is genuinely the
    hour Scott picks in Settings, correctly following DST with no separate
    UTC-offset math to maintain.

    2026-07-19: last_sent_date used to be a plain local variable, the exact
    "in-memory gate lost on restart" bug class _calendar_tasks_loop's
    _get_calendar_task_last_run()/_set_calendar_task_last_run() were built to
    fix elsewhere (2026-07-18) -- reintroduced here since this loop predates
    that fix and was never updated to match. Two redeploys landing inside the
    same configured-hour window on the same day could send the brief twice.
    Reusing those same persistence helpers (the setting-key prefix says
    "calendar_task" but the functions are generic date persistence, not
    specific to _calendar_tasks_loop) instead of duplicating the pattern."""
    _safe_set_agent_heartbeat("daily_brief", "Daily Brief", "started", "waiting for the configured send hour")
    last_sent_date: date | None = _get_calendar_task_last_run("daily_brief")
    while True:
        await asyncio.sleep(3600)
        try:
            # 2026-08-06 (full-system audit): this used to start with two bare
            # calls (db.get_setting()/_shop_now()) outside any try/except --
            # every OTHER step in this loop is individually guarded, but an
            # exception in either of those two would still kill the whole
            # asyncio.Task silently, with no heartbeat update, unlike loops
            # using _run_loop_iteration()'s whole-iteration wrapper. Wrapping
            # the entire tick closes that gap without changing any of the
            # existing fine-grained handling below.
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
            enabled = db.get_setting("daily_brief_enabled") != "0"
            if not enabled:
                _safe_set_agent_heartbeat("daily_brief", "Daily Brief", "ok", "disabled in Settings")
                continue
            try:
                configured_hour = int(db.get_setting("daily_brief_hour") or 6)
            except (TypeError, ValueError):
                configured_hour = 6
            now = _shop_now()
            if now.hour == configured_hour and now.date() != last_sent_date:
                _safe_set_agent_heartbeat("daily_brief", "Daily Brief", "running", "generating brief")
                try:
                    import daily_brief as _daily_brief
                    result = await asyncio.to_thread(_daily_brief.run_daily_brief)
                    last_sent_date = now.date()
                    _set_calendar_task_last_run("daily_brief", last_sent_date)
                    _safe_set_agent_heartbeat("daily_brief", "Daily Brief", "ok", result)
                    print(f"[daily_brief] {result}", flush=True)
                except Exception as exc:
                    _safe_set_agent_heartbeat("daily_brief", "Daily Brief", "error", str(exc))
                    print(f"[daily_brief] error: {exc}", flush=True)
            else:
                next_run = "today" if now.hour < configured_hour else "tomorrow"
                _safe_set_agent_heartbeat(
                    "daily_brief", "Daily Brief", "ok",
                    f"next brief {next_run} at {configured_hour:02d}:00 shop-local time (last sent: {last_sent_date or 'never'})"
                )
        except Exception as exc:
            _safe_set_agent_heartbeat("daily_brief", "Daily Brief", "error", f"tick failed: {exc}")
            print(f"[daily_brief] tick failed: {exc}", flush=True)


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


def _email_ops_summary(subject: str, body: str) -> None:
    """Emails a weekly/monthly ops-summary digest, reusing daily_brief.py's
    generic SMTP sender (_send_brief) rather than a third independent SMTP
    implementation (order_notifier.py already has its own). 2026-07-18:
    closes the gap where the weekly Sunday and monthly 1st-of-month
    automation already ran, but only ever landed as an in-app todo +
    ops_runbook entry -- Scott had to open Frank to see the results. Never
    raises: _send_brief() itself already returns False on failure (e.g. SMTP
    not configured) rather than throwing, and the import is wrapped too so a
    missing/broken daily_brief module can't break the caller's own
    todo/ops_runbook write, which must always happen regardless."""
    try:
        import daily_brief as _daily_brief
        _daily_brief._send_brief(subject, body)
    except Exception as exc:
        print(f"[ops-summary-email] send failed: {exc}", flush=True)


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
    _email_ops_summary(
        f"{business_config.BUSINESS_NAME} Weekly Ops Summary — {date.today().strftime('%a %b %-d')}",
        digest[:8000],
    )
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
    _email_ops_summary(
        f"{business_config.BUSINESS_NAME} Monthly Shop Health — {date.today().strftime('%b %Y')}",
        out[:8000],
    )
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


# 2026-07-17 (Wave 4, C3): data/knowledge_base/competitor_research_2026.md was a
# static one-off snapshot (written May 2026, ~10 weeks stale by this audit) with
# no refresh mechanism -- Frank's chat agent reads it on demand via
# read_knowledge_base_doc, so a stale file quietly fed stale market claims into
# every conversation that touched pricing/positioning. This job regenerates it
# monthly using two real signals: C1's live Etsy search_listings() data (actual
# current competitor titles/prices/tags for this shop's own core search terms)
# plus the Anthropic-hosted web_search tool (already wired into AGENT_TOOLS for
# chat; called directly here in a single messages.create() so this can run as a
# standalone background job outside a chat turn) for broader trend/algorithm
# signal a pure Etsy search can't see. Read-only against Etsy; the only write is
# this local knowledge-base file.
# 2026-08-06 (full-system audit): was a raw ROOT/"data" path -- the monthly
# refresh below silently vanished on every Railway redeploy, same durability
# gap already fixed for ceo_learnings.md/ops_runbook.md. Same resolver now.
_COMPETITOR_RESEARCH_PATH = db.resolve_persistent_path(
    "knowledge_base/competitor_research_2026.md",
    fallback=ROOT / "data" / "knowledge_base" / "competitor_research_2026.md",
    seed_from=ROOT / "data" / "knowledge_base" / "competitor_research_2026.md",
)
_COMPETITOR_RESEARCH_SEARCH_TERMS = [
    "printable wall art digital download",
    "digital planner goodnotes",
    "kawaii sticker pack goodnotes",
    # 2026-08-08: the refresh prompt below has always claimed to cover all 4 product
    # lines ("wall art, digital planners, kawaii sticker packs, 3D-print SVG packs"),
    # but this list only ever had 3 terms -- coloring pages had no search term at all,
    # and SVG packs were named in the prompt without ever being searched for. The live
    # competitor_research_2026.md doc stayed wall-art-titled/scoped as a result. Two
    # terms added to close the gap between what this refresh claims to do and what it
    # actually searches for.
    "coloring pages printable digital download",
    "3d print svg file bundle",
]


def _run_competitor_research_refresh() -> str:
    """Monthly: pulls real live Etsy comparable-listing data for this shop's core
    search terms (via EtsyAPIClient.search_listings, the same C1 method
    get_comparable_listings wraps), hands it plus the existing report to Claude
    with the hosted web_search tool enabled for current internet-only signal
    (algorithm changes, trend/pricing research), and overwrites
    competitor_research_2026.md with the refreshed markdown. Never touches Etsy's
    write API, never contacts buyers -- a pure internal research-doc refresh."""
    if not ANTHROPIC_KEY:
        return "skipped -- ANTHROPIC_API_KEY not configured"

    client = EtsyAPIClient()
    comparable_blocks = []
    for term in _COMPETITOR_RESEARCH_SEARCH_TERMS:
        try:
            resp = client.search_listings(term, limit=8, sort_on="score")
            results = resp.get("results") or []
            lines = [
                f"- \"{(r.get('title') or '')[:80]}\" — ${_price_float(r.get('price')):.2f} — "
                f"tags: {', '.join((r.get('tags') or [])[:5])}"
                for r in results
            ]
            comparable_blocks.append(
                f"### Live Etsy search: \"{term}\"\n" + ("\n".join(lines) if lines else "(no results)")
            )
        except Exception as exc:  # noqa: BLE001
            comparable_blocks.append(f"### Live Etsy search: \"{term}\"\n(search failed, non-fatal: {exc})")
    comparable_text = "\n\n".join(comparable_blocks)

    try:
        existing = _COMPETITOR_RESEARCH_PATH.read_text(encoding="utf-8")
    except Exception:
        existing = "(no existing report found)"

    user_payload = (
        f"Today is {date.today().isoformat()}. Refresh this shop's competitive intelligence "
        f"report for its digital product lines (wall art, digital planners, kawaii sticker "
        f"packs, 3D-print SVG packs, coloring pages). Use web_search for anything that needs "
        f"current internet data (Etsy algorithm changes, pricing/trend research, seasonal "
        f"shifts) and the REAL LIVE ETSY DATA below for actual current competitor listings.\n\n"
        f"REAL LIVE ETSY DATA (search_listings, today):\n{comparable_text}\n\n"
        f"EXISTING REPORT (may be stale -- verify, correct, and refresh it; keep the same "
        f"overall structure/section headers so the rest of the app that reads this file "
        f"continues to work, but update any numbers/claims that are now wrong or dated):\n"
        f"{existing[:8000]}\n\n"
        f"Return the COMPLETE updated markdown report between the exact markers "
        f"===BEGIN_REPORT=== and ===END_REPORT===, nothing else outside the markers. Update the "
        f"'Research date' line at the top to reflect today's refresh."
    )

    ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    try:
        response = _anthropic_create(
            ai_client,
            model=business_config.MODEL_PRIMARY,
            max_tokens=8000,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5,
                "user_location": {"type": "approximate", "country": "US"},
            }],
            system=[{"type": "text", "text": (
                "You are a market research analyst refreshing an internal competitive-"
                "intelligence document for an Etsy shop (OnBrandCraftz). Be accurate -- cite "
                "only things you actually found via web_search or the real Etsy data given to "
                "you, never invent statistics or case studies. Keep the document's existing "
                "structure and tone."
            )}],
            messages=[{"role": "user", "content": user_payload}],
        )
    except Exception as exc:  # noqa: BLE001
        return f"error: Claude call failed: {exc}"

    text = "".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text")
    match = _re.search(r"===BEGIN_REPORT===(.*?)===END_REPORT===", text, _re.DOTALL)
    if not match:
        return "error: model did not return a report between the expected markers -- file not updated"
    new_report = match.group(1).strip() + "\n"

    _COMPETITOR_RESEARCH_PATH.write_text(new_report, encoding="utf-8")
    db.add_todo(
        "Monthly competitor research refresh ready — data/knowledge_base/competitor_research_2026.md "
        "updated with real live Etsy data + web research. See this month's ops_runbook entry.",
        added_by="frank", category="general",
    )
    _append_ops_runbook_entry(
        "Monthly competitor research refresh",
        f"Refreshed competitor_research_2026.md ({len(new_report)} chars). "
        f"Live search terms used: {', '.join(_COMPETITOR_RESEARCH_SEARCH_TERMS)}.",
    )
    return f"refreshed competitor_research_2026.md ({len(new_report)} chars)"


# 2026-07-25 (deep_research tool): same shape as _run_competitor_research_refresh
# above (hosted web_search_20250305 tool, already proven in production there and
# permanently in AGENT_TOOLS), made iterative/recursive per dzhng/deep-research's
# own algorithm -- generate `breadth` queries, research each (concurrently, each
# with its own web_search-enabled call), fold the learnings into the next level's
# query generation, repeat for `depth` levels, then synthesize one sourced report.
# Total LLM calls = breadth*depth + 1 (query-gen once per level + 1 synthesis;
# see _run_deep_research_core). Scott chose this over dzhng/deep-research's own
# CLI (AskUserQuestion) specifically to avoid a new paid Firecrawl signup -- the
# Anthropic web_search tool is already configured and billed through the existing
# key.
_DEEP_RESEARCH_MAX_BREADTH = 6
_DEEP_RESEARCH_MAX_DEPTH = 3


def _generate_research_queries(
    query: str, breadth: int, prior_learnings: list[str] | None = None,
) -> list[str]:
    """One non-web_search call: ask the model for `breadth` distinct, non-
    overlapping search queries that would advance research on `query`. When
    `prior_learnings` is given (every level after the first), the new queries
    are informed by what's already been learned -- this is what makes the
    research "go deeper" instead of repeating the same searches each level."""
    if not ANTHROPIC_KEY:
        return [query][:breadth]

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    learnings_block = (
        f"\n\nLearnings so far from earlier research rounds:\n"
        + "\n".join(f"- {l}" for l in prior_learnings[-30:])
        if prior_learnings else ""
    )
    prompt = (
        f"Research goal: {query}{learnings_block}\n\n"
        f"Generate exactly {breadth} distinct, specific search queries that would "
        f"each surface different, non-overlapping information relevant to the "
        f"research goal above. "
        + ("Go deeper than the earlier rounds -- target gaps or open questions the "
           "learnings above didn't resolve, not the same ground again. "
           if prior_learnings else "")
        + 'Return ONLY a JSON array of strings, e.g. ["query one", "query two"], '
        f"nothing else."
    )
    try:
        response = _anthropic_create(
            client,
            model=business_config.MODEL_PRIMARY,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception:  # noqa: BLE001
        return [query][:breadth]

    text = "".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text")
    parsed = _extract_json_object(text)
    if not isinstance(parsed, list) or not parsed:
        return [query][:breadth]
    queries = [str(q).strip() for q in parsed if str(q).strip()]
    return queries[:breadth] or [query][:breadth]


def _research_one_query(q: str) -> dict:
    """One web_search-enabled call for a single query. Returns
    {"learnings": [...], "sources": [...]} -- never raises; a failed sub-query
    degrades to an empty result so one bad query can't sink the whole research
    run (same non-fatal-per-item pattern as _run_competitor_research_refresh's
    per-term search_listings loop above)."""
    if not ANTHROPIC_KEY:
        return {"learnings": [], "sources": []}

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    prompt = (
        f'Research this query using web search: "{q}"\n\n'
        f"Return ONLY a JSON object of the exact shape "
        f'{{"learnings": ["concise factual finding 1", "..."], "sources": '
        f'["https://...", "..."]}}. Learnings must be specific and information-'
        f"dense (include real numbers/names/dates where you found them), not "
        f"vague summaries. List every source URL you actually used."
    )
    try:
        response = _anthropic_create(
            client,
            model=business_config.MODEL_PRIMARY,
            max_tokens=2048,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 3,
                "user_location": {"type": "approximate", "country": "US"},
            }],
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:  # noqa: BLE001
        return {"learnings": [], "sources": [], "error": str(exc)}

    text = "".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text")
    parsed = _extract_json_object(text)
    if not isinstance(parsed, dict):
        return {"learnings": [], "sources": []}
    learnings = [str(l).strip() for l in (parsed.get("learnings") or []) if str(l).strip()]
    sources = [str(s).strip() for s in (parsed.get("sources") or []) if str(s).strip()]
    return {"learnings": learnings, "sources": sources}


def _synthesize_research_report(query: str, learnings: list[str], sources: list[str]) -> str:
    """Final non-web_search call: compile every learning gathered across all
    levels into one sourced markdown report. Same marker-delimited extraction
    idiom as _run_competitor_research_refresh -- returns the raw markdown
    string; the caller decides where (if anywhere) to persist it."""
    if not learnings:
        return f"# Deep Research: {query}\n\n_No learnings were gathered -- research produced no results._\n"
    if not ANTHROPIC_KEY:
        return (
            f"# Deep Research: {query}\n\n## Learnings (unsynthesized -- no API key)\n"
            + "\n".join(f"- {l}" for l in learnings)
            + "\n\n## Sources\n" + "\n".join(f"- {s}" for s in sources)
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    learnings_block = "\n".join(f"- {l}" for l in learnings)
    sources_block = "\n".join(f"- {s}" for s in sorted(set(sources)))
    prompt = (
        f"Research goal: {query}\n\n"
        f"All learnings gathered across this research run:\n{learnings_block}\n\n"
        f"All sources used:\n{sources_block}\n\n"
        f"Compile these into one well-organized markdown report answering the research "
        f"goal. Use headers to group related learnings, cite sources inline where a "
        f"specific claim came from a specific source, and include a final 'Sources' "
        f"section listing every URL. Do not invent facts not present in the learnings "
        f"above.\n\n"
        f"Return the COMPLETE report between the exact markers ===BEGIN_REPORT=== and "
        f"===END_REPORT===, nothing else outside the markers."
    )
    try:
        response = _anthropic_create(
            client,
            model=business_config.MODEL_PRIMARY,
            max_tokens=4096,
            system=[{"type": "text", "text": (
                "You are a research analyst compiling a sourced markdown report from "
                "raw research findings. Be accurate -- use only the learnings and "
                "sources given to you, never invent statistics or citations."
            )}],
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:  # noqa: BLE001
        return (
            f"# Deep Research: {query}\n\n_Synthesis call failed ({exc}) -- raw learnings below._\n\n"
            + "\n".join(f"- {l}" for l in learnings)
            + "\n\n## Sources\n" + "\n".join(f"- {s}" for s in sorted(set(sources)))
        )

    text = "".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text")
    match = _re.search(r"===BEGIN_REPORT===(.*?)===END_REPORT===", text, _re.DOTALL)
    if not match:
        return (
            f"# Deep Research: {query}\n\n_Model did not return the expected markers -- raw "
            f"learnings below._\n\n" + "\n".join(f"- {l}" for l in learnings)
            + "\n\n## Sources\n" + "\n".join(f"- {s}" for s in sorted(set(sources)))
        )
    return match.group(1).strip() + "\n"


async def _run_deep_research_core(query: str, breadth: int, depth: int) -> dict:
    """Orchestrates the full iterative research run (linear cost: breadth*depth
    LLM research calls + depth query-gen calls + 1 synthesis call). Runs each
    level's `breadth` per-query research calls concurrently via
    asyncio.gather(asyncio.to_thread(...)) -- the same bridge-into-async
    pattern used elsewhere for a blocking Anthropic call inside async code
    (see _dispatch_to_relay's docstring for the analogous relay-timeout
    reasoning). Called via asyncio.run() from the sync _execute_agent_tool
    dispatch branch, matching the existing _autofix_tags_core/
    _diagnose_listing_core precedent for bridging a sync tool-dispatch branch
    into async code -- _execute_agent_tool always runs inside its own worker
    thread (via asyncio.to_thread from the chat loop), so starting a fresh
    event loop here can never collide with the main loop."""
    breadth = max(1, min(int(breadth), _DEEP_RESEARCH_MAX_BREADTH))
    depth = max(1, min(int(depth), _DEEP_RESEARCH_MAX_DEPTH))

    learnings: list[str] = []
    sources: list[str] = []
    queries = await asyncio.to_thread(_generate_research_queries, query, breadth)

    for level in range(depth):
        results = await asyncio.gather(*[asyncio.to_thread(_research_one_query, q) for q in queries])
        for r in results:
            learnings.extend(r.get("learnings") or [])
            sources.extend(r.get("sources") or [])
        if level < depth - 1:
            queries = await asyncio.to_thread(_generate_research_queries, query, breadth, learnings)

    report_md = await asyncio.to_thread(_synthesize_research_report, query, learnings, sources)
    return {
        "query": query,
        "breadth": breadth,
        "depth": depth,
        "learnings": learnings,
        "sources": sorted(set(sources)),
        "report_md": report_md,
    }


def _write_deep_research_report(result: dict) -> str:
    """Writes a completed _run_deep_research_core() result to a new file under
    _FILE_ROOTS["deep_research"] (registered near :13934, alongside the other
    durable roots) and returns its filename. Each report is its own file keyed
    by a slug of the query plus today's date -- unlike competitor_research_2026.md
    (a single living reference doc this same web_search pattern refreshes in
    place), deep-research reports are ad-hoc one-offs Scott may run repeatedly
    with different queries, so nothing here should ever overwrite a prior run."""
    root = _FILE_ROOTS["deep_research"]
    root.mkdir(parents=True, exist_ok=True)
    slug = _re.sub(r"[^a-z0-9]+", "-", result["query"].lower()).strip("-")[:60] or "research"
    base_name = f"{slug}-{date.today().isoformat()}"
    filename = f"{base_name}.md"
    suffix = 2
    while (root / filename).exists():
        filename = f"{base_name}-{suffix}.md"
        suffix += 1
    (root / filename).write_text(result["report_md"], encoding="utf-8")
    return filename


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
        today = _shop_today()  # 2026-08-06 (Today second-pass audit): shop-local, not server UTC
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

    today = _shop_today()  # 2026-08-06 (Today second-pass audit): shop-local, not server UTC

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

    today = _shop_today()  # 2026-08-06 (Today second-pass audit): shop-local, not server UTC

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


# ── Bambu P1S printer telemetry (2026-07-29) ────────────────────────────────
# See the _printer_lock/_printer_telemetry block above for why this is
# in-memory only. The bridge (tools/relay/bambu_p1s_bridge.py) is the only
# writer of the POST endpoints; the HUD card is the only reader of the GET
# endpoints. No rate limiting beyond the shared session/bearer auth — a
# bridge pushing every few seconds is well under any real limit, same as
# every other internal, non-mutating, non-Etsy-costing endpoint here.
def _merge_printer_telemetry(existing: dict | None, incoming: dict) -> dict:
    """Merge one bridge push into the running printer-state snapshot instead
    of replacing it wholesale (2026-08-11 fix for Scott's "stats keep going
    away and random info pops up" -- confirmed live: bridge_seen=true,
    age_seconds<1, yet nearly every field null except whatever the single
    most recent MQTT message happened to mention).

    Root cause: Bambu's MQTT `print` topic mixes full "pushall" reports with
    small partial deltas that only carry the fields that changed. The old
    code (`_printer_telemetry = payload`) treated every push as a complete
    snapshot, so a delta that only reported a new bed temp wiped out every
    other field the HUD was showing a second earlier.

    Two independent old-bridge quirks handled defensively here so this fix
    takes effect the moment it deploys, without requiring Scott to update
    the bridge on his own machine first:
      - Scalar fields: the shipped bridge always sends every key, using
        None for "this delta didn't mention it" -- skip None on merge.
      - `ams`/`hms`: always sent as a list (never None) even when the delta
        didn't mention them at all, defaulting to `[]` -- skip an EMPTY
        list on merge so a real, non-empty tray/error list already known
        doesn't get silently cleared. (Tradeoff: a genuine HMS-just-cleared
        transition won't visibly clear until the next non-empty-driving
        push; a stale error notice is lower-risk than the constant-flicker
        bug this fix targets.)
    A rewritten bridge (this same commit) only includes a key in its
    payload at all when the raw MQTT message actually reported it, which
    makes this merge exactly correct for it too -- no second code path
    needed once Scott updates the bridge."""
    state = dict(existing) if existing else {}
    for key, value in incoming.items():
        if value is None:
            continue
        if key in ("ams", "hms") and isinstance(value, list) and not value:
            continue
        state[key] = value
    return state


def _printer_status_payload() -> dict:
    """Same shape GET /api/printer/status returns -- shared so the REST
    response and every /ws/printer push can never drift apart."""
    with _printer_lock:
        data = _printer_telemetry
        at = _printer_telemetry_at
    age = (time.time() - at) if at else None
    online = age is not None and age < _PRINTER_STALE_SECS
    if data is None:
        return {"online": False, "bridge_seen": False}
    return {"online": online, "bridge_seen": True, "age_seconds": round(age, 1), **data}


_printer_ws_clients: set = set()
_printer_ws_lock = threading.Lock()


async def _broadcast_printer_telemetry() -> None:
    """Push the current snapshot to every connected /ws/printer client —
    called right after a bridge push updates state, so the HUD updates the
    instant new data arrives instead of waiting for its next poll tick."""
    with _printer_ws_lock:
        clients = list(_printer_ws_clients)
    if not clients:
        return
    payload = json.dumps(_printer_status_payload())
    dead = []
    for ws in clients:
        try:
            await ws.send_text(payload)
        except Exception:  # noqa: BLE001
            dead.append(ws)
    if dead:
        with _printer_ws_lock:
            for ws in dead:
                _printer_ws_clients.discard(ws)


@app.post("/api/printer/telemetry")
async def post_printer_telemetry(payload: dict, _token: str = Depends(_auth_session_or_bearer)):
    global _printer_telemetry, _printer_telemetry_at
    with _printer_lock:
        _printer_telemetry = _merge_printer_telemetry(_printer_telemetry, payload)
        _printer_telemetry_at = time.time()
    await _broadcast_printer_telemetry()
    return {"ok": True}


@app.get("/api/printer/status")
async def get_printer_status(_token: str = Depends(_auth_session_or_bearer)):
    return _printer_status_payload()


@app.websocket("/ws/printer")
async def printer_ws(websocket: WebSocket):
    """Live push channel for the P1S printer card (2026-08-11) — the HUD
    connects here instead of relying solely on its 5s poll of GET
    /api/printer/status. Auth via the same short-lived, single-use ?ticket=
    mechanism /ws/chat uses (browsers can't set a Bearer header on a WS
    handshake). Sends the current snapshot immediately on connect, then
    again every time the bridge pushes new telemetry (see
    _broadcast_printer_telemetry(), called from post_printer_telemetry()).
    Server -> client only; the 5s poll stays in place client-side as a
    fallback so a dropped socket degrades to "slightly less instant," never
    to "no data.\""""
    ticket = websocket.query_params.get("ticket", "")
    if not ticket or not _consume_ws_ticket(ticket):
        await websocket.close(code=4001)
        return
    await websocket.accept()
    with _printer_ws_lock:
        _printer_ws_clients.add(websocket)
    try:
        await websocket.send_text(json.dumps(_printer_status_payload()))
        while True:
            await websocket.receive_text()  # only used to detect disconnect; no client->server messages expected
    except WebSocketDisconnect:
        pass
    finally:
        with _printer_ws_lock:
            _printer_ws_clients.discard(websocket)


@app.post("/api/printer/camera-frame")
async def post_printer_camera_frame(request: Request, _token: str = Depends(_auth_session_or_bearer)):
    global _printer_frame, _printer_frame_at
    body = await request.body()
    if len(body) > _PRINTER_MAX_FRAME_BYTES:
        raise HTTPException(status_code=413, detail="Camera frame too large")
    with _printer_lock:
        _printer_frame = body
        _printer_frame_at = time.time()
    return {"ok": True}


@app.get("/api/printer/camera.jpg")
async def get_printer_camera_frame(_token: str = Depends(_auth_session_or_bearer)):
    with _printer_lock:
        frame = _printer_frame
        at = _printer_frame_at
    age = (time.time() - at) if at else None
    if frame is None or age is None or age > _PRINTER_CAMERA_STALE_SECS:
        raise HTTPException(status_code=404, detail="No recent camera frame from the printer bridge")
    return Response(content=frame, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


# ── COGS / profit-per-listing (2026-07-17 capabilities audit item 4) ────────
# No real per-listing cost data exists anywhere in this codebase (checked:
# product_catalog.json, makerworld_specs.json, business_config.py -- none
# carry a cost field). The only cost numbers on record are the manually
# maintained estimates in data/financial/profit_loss.md's 3D-print COGS
# table (Low/Typical/High, filament+electricity+wear+packaging). This panel
# is therefore an ESTIMATE, not real accounting -- it says so explicitly in
# its own "note" field rather than presenting borrowed numbers as fact.
_ETSY_TRANSACTION_FEE_RATE = 0.065     # CLAUDE.md "Etsy Fees to Factor In"
_ETSY_PAYMENT_PROCESSING_RATE = 0.03
_ETSY_PAYMENT_PROCESSING_FLAT = 0.25
_ETSY_LISTING_FEE = 0.20
# data/financial/profit_loss.md "Typical" 3D-print COGS/unit (filament +
# electricity + printer wear + packaging). Excludes shipping -- CLAUDE.md's
# pricing guidance treats shipping as absorbed into price, not a separate
# per-sale line item here.
_PHYSICAL_COGS_ESTIMATE_USD = 7.50
_COGS_LOW_MARGIN_THRESHOLD_PCT = 40.0


def _classify_product_type_for_cogs(title: str) -> str:
    """Reuses order_notifier.py's own title-keyword product classifier
    (lazy-imported, not copied) so this estimate and the order-notification
    emails never silently drift on what counts as a physical 3d_print item --
    the exact "two copies of the same lookup logic" bug class already caught
    once this session (pinterest_batch_poster.py's own duplicated Etsy image
    lookup vs. the shared EtsyAPIClient). Lazy import so order_notifier's
    module-level .env load doesn't run at every main.py startup."""
    import order_notifier
    return order_notifier._classify(title)


def _estimate_listing_economics(price: float, title: str) -> dict:
    """Per-listing profit estimate: real, documented Etsy fee math (not an
    estimate) minus an ESTIMATED COGS based on a title-keyword product-type
    guess (digital ≈ $0 COGS, 3D-print physical ≈ $7.50/unit typical)."""
    kind = _classify_product_type_for_cogs(title)
    is_physical = kind == "3d_print"
    cogs = _PHYSICAL_COGS_ESTIMATE_USD if is_physical else 0.0
    transaction_fee = price * _ETSY_TRANSACTION_FEE_RATE
    payment_fee = price * _ETSY_PAYMENT_PROCESSING_RATE + _ETSY_PAYMENT_PROCESSING_FLAT
    fees = transaction_fee + payment_fee + _ETSY_LISTING_FEE
    net = price - fees - cogs
    margin_pct = round((net / price) * 100, 1) if price > 0 else 0.0
    return {
        "product_type": kind,
        "is_physical_estimate": is_physical,
        "cogs_estimate": round(cogs, 2),
        "fees_real": round(fees, 2),
        "net_estimate": round(net, 2),
        "margin_pct": margin_pct,
    }


def _compute_cogs_status() -> dict:
    """Shop-wide COGS/profit snapshot across all active listings, mirroring
    _compute_ads_status()'s shape (used/status/metrics). Real inputs: live
    price per listing (Etsy) and real recent units sold per listing (last 100
    paid receipts, via the existing _sales_by_listing_sync() -- true sales,
    not favorites). Estimated inputs: product type (title-keyword guess) and
    3D-print COGS (a flat typical estimate, not per-design real cost).

    A missing/invalid Etsy token means this can structurally never succeed,
    not a transient hiccup -- so it's caught here and reported as an honest
    "nothing to show" (used: False), the same contract _compute_ads_status()
    already uses when there's no ads data, rather than bubbling up to
    _fetch_with_degrade's 503 (that path is for real transient failures on a
    call that normally succeeds, matching _compute_star_seller_status()'s own
    per-call try/except-to-zero pattern for the identical situation)."""
    try:
        listings = _listings_sync("active").get("listings", [])
    except Exception as exc:
        print(f"[cogs-status] listings fetch failed: {exc}", flush=True)
        return {"used": False}
    if not listings:
        return {"used": False}
    try:
        sales = _sales_by_listing_sync()
    except Exception as exc:
        print(f"[cogs-status] sales fetch failed (non-fatal, treating as zero sales): {exc}", flush=True)
        sales = {}

    rows = []
    total_recent_profit = 0.0
    total_recent_units = 0
    for l in listings:
        price = l.get("price") or 0
        econ = _estimate_listing_economics(price, l.get("title", ""))
        units = sales.get(l.get("listing_id"), 0)
        recent_profit = round(econ["net_estimate"] * units, 2)
        total_recent_profit += recent_profit
        total_recent_units += units
        rows.append({
            "listing_id": l.get("listing_id"),
            "title": (l.get("title") or "")[:60],
            "price": price,
            "recent_units_sold": units,
            "recent_profit_estimate": recent_profit,
            **econ,
        })

    avg_margin = round(sum(r["margin_pct"] for r in rows) / len(rows), 1) if rows else 0.0
    flagged = sorted(
        (r for r in rows if r["margin_pct"] < _COGS_LOW_MARGIN_THRESHOLD_PCT),
        key=lambda r: r["margin_pct"],
    )[:5]
    top_profit = sorted(rows, key=lambda r: r["recent_profit_estimate"], reverse=True)[:5]

    return {
        "used": True,
        "listing_count": len(rows),
        "avg_margin_pct": avg_margin,
        "total_recent_profit_estimate": round(total_recent_profit, 2),
        "total_recent_units": total_recent_units,
        "flagged_low_margin": flagged,
        "top_profit_listings": top_profit,
        "note": (
            "Estimate, not real accounting: digital COGS assumed $0, physical "
            "(3D-print) COGS estimated at a flat $7.50/unit typical "
            "(data/financial/profit_loss.md), product type guessed from title "
            "keywords. Etsy fees (6.5% transaction + 3%+$0.25 processing + "
            "$0.20 listing) are real, documented rates, not estimates. Recent "
            "units sold are real (last 100 paid receipts)."
        ),
    }


@app.get("/api/cogs-status")
async def get_cogs_status(_token: str = Depends(_auth_session_or_bearer)):
    """COGS/profit-per-listing snapshot for the Home screen card. Cached 120s
    (same TTL as Ads/ROAS and Star Seller). Unlike Ads/ROAS (local-only data,
    no Etsy call), this one calls _listings_sync() -> a real Etsy fetch, so
    it must degrade the same way /api/star-seller and /api/listings already
    do -- caught live 2026-07-17 via playwright_smoke.py: an uncaught
    EtsyAPIError (e.g. no OAuth token configured) bubbled into a raw 500,
    the exact bug class _fetch_with_degrade was built to close on 2026-07-10
    for the other Etsy-touching status cards."""
    cached = _cache_get("cogs_status", ttl=120)
    if cached is not None:
        return cached
    result = await _fetch_with_degrade(
        "cogs_status", asyncio.to_thread(_compute_cogs_status), timeout=20.0
    )
    if not (isinstance(result, dict) and result.get("stale")):
        _cache_set("cogs_status", result)
    return result


@app.get("/api/business-tracker.xlsx")
async def get_business_tracker(_token: str = Depends(_auth_session_or_bearer)):
    """Live, multi-tab Business Tracker workbook — Products (from
    data/product_catalog.json, merged with any Create-screen "+ new one"
    products registered only in the product_catalog_overrides.json sidecar
    -- see the 2026-07-25 merge below), COGS & Profit and Orders (live Etsy
    data, same functions powering the HUD status cards), plus manual-fill
    inventory/supplier/expense templates. See tools/business_tracker.py for
    the sheet builders. Generated fresh in memory on every request, never
    written to disk (the archived one-off predecessor wrote to the
    gitignored data/backups/, so it never reached the hosted deploy).
    Best-effort on the live-data sheets: if Etsy is briefly unreachable,
    those sheets simply come back empty rather than failing the whole
    download — the same tolerance _sales_by_listing_sync() and
    _compute_cogs_status() already apply per-lookup."""
    def _gather_and_build() -> bytes:
        try:
            listings = _listings_sync("active").get("listings", [])
        except Exception as exc:
            print(f"[business-tracker] listings fetch failed: {exc}", flush=True)
            listings = []
        try:
            orders_raw = _get_recent_orders_raw()
        except Exception as exc:
            print(f"[business-tracker] orders fetch failed: {exc}", flush=True)
            orders_raw = []
        try:
            sales = _sales_by_listing_sync()
        except Exception as exc:
            print(f"[business-tracker] sales mapping failed: {exc}", flush=True)
            sales = {}
        try:
            catalog = json.loads(Path("data/product_catalog.json").read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[business-tracker] product_catalog.json read failed: {exc}", flush=True)
            catalog = []
        # (2026-07-25) A product built via the Create screen's "+ new one" flow
        # (e.g. a Coloring Pages new-theme listing) has no base-catalog entry --
        # it only ever exists in the product_catalog_overrides.json sidecar (see
        # _register_new_product_overlay()). Without this merge it silently never
        # appears in the downloaded workbook even though it's real, built, and
        # already visible in Products/Files. Mirrors the exact synthesis
        # _build_products_status() already does for /api/products
        # (main.py:_build_products_status), reshaped to the flatter row dict
        # business_tracker.py's _build_products() reads.
        overrides = _product_catalog_overrides()
        known_ids = {e.get("product_id") for e in catalog}
        for ov_pid, ov in overrides.items():
            if ov.get("is_new_product") and ov_pid not in known_ids:
                catalog.append({
                    "product_id": ov_pid,
                    "name": ov.get("name", ov_pid),
                    "category": ov.get("category", "uncategorized"),
                    "status": ov.get("status", "draft"),
                    "price": ov.get("price"),
                    "etsy_listing_id": ov.get("etsy_listing_id", ""),
                    "last_updated": ov.get("created_at", ""),
                    "note": "Built via Create screen — not yet published",
                })
        buf = business_tracker.build_workbook(
            listings, sales, orders_raw, catalog, _estimate_listing_economics
        )
        return buf.getvalue()

    content = await asyncio.to_thread(_gather_and_build)
    filename = f"OnBrandCraftz_Business_Tracker_{date.today().isoformat()}.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Global search (2026-07-17 Wave 3 usability) ─────────────────────────────
# The header search box's own placeholder claimed "Search listings, orders,
# tools, knowledge base" but the client-only implementation (frank_hud_
# mockup.py's old runGlobalSearch) never actually searched orders, never
# searched Products at all, only scanned whatever happened to already be
# cached in the browser from screens Scott had visited that session, and
# jumped straight to the first match instead of showing a real results list.
# This endpoint is the real, always-live backing search: every category is
# fetched fresh (or from the same short-TTL server cache other status cards
# already use), and each source degrades to an empty list on its own failure
# rather than taking the whole search down (the same lesson learned fixing
# /api/cogs-status the same day).
_SEARCH_RESULTS_PER_CATEGORY = 5


def _search_listings(query: str, limit: int = _SEARCH_RESULTS_PER_CATEGORY) -> list[dict]:
    try:
        listings = _listings_sync("active").get("listings", [])
    except Exception as exc:
        print(f"[search] listings failed: {exc}", flush=True)
        return []
    out = []
    for l in listings:
        if query in (l.get("title") or "").lower():
            price = l.get("price") or 0
            out.append({
                "category": "listing", "id": l.get("listing_id"),
                "title": l.get("title", ""), "subtitle": f"${price:.2f} · {l.get('state', '')}",
            })
            if len(out) >= limit:
                break
    return out


def _search_orders(query: str, limit: int = _SEARCH_RESULTS_PER_CATEGORY) -> list[dict]:
    """Real recent paid orders (last 100 receipts) via the shared
    _get_recent_orders_raw() cache. There is no dedicated Orders screen in
    the HUD, so a matched order links straight to its Etsy receipt page (the
    same URL order_notifier.py already uses)."""
    out = []
    for r in _get_recent_orders_raw():
        receipt_id = str(r.get("receipt_id", ""))
        buyer = r.get("name", "") or ""
        item_titles = " ".join(t.get("title", "") for t in (r.get("transactions") or []))
        haystack = f"{receipt_id} {buyer} {item_titles}".lower()
        if query not in haystack:
            continue
        total = r.get("grandtotal", {})
        if isinstance(total, dict):
            total_str = f"{float(total.get('amount', 0)) / max(total.get('divisor', 100), 1):.2f}"
        else:
            total_str = str(total)
        out.append({
            "category": "order", "id": receipt_id,
            "title": f"Order #{receipt_id} — {buyer}".strip(),
            "subtitle": f"${total_str}",
            "url": f"https://www.etsy.com/your/orders/{receipt_id}",
        })
        if len(out) >= limit:
            break
    return out


def _search_products(query: str, limit: int = _SEARCH_RESULTS_PER_CATEGORY) -> list[dict]:
    try:
        catalog = json.loads(Path("data/product_catalog.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[search] products failed: {exc}", flush=True)
        return []
    out = []
    for p in catalog:
        title = p.get("title") or p.get("name") or ""
        pid = str(p.get("product_id", ""))
        if query in title.lower() or (pid and query in pid.lower()):
            out.append({
                "category": "product", "id": pid,
                "title": title or pid, "subtitle": p.get("category", ""),
            })
            if len(out) >= limit:
                break
    return out


def _search_tools(query: str, limit: int = _SEARCH_RESULTS_PER_CATEGORY) -> list[dict]:
    out = []
    for t in AGENT_TOOLS:
        name = t.get("name", "")
        desc = t.get("description", "") or ""
        if query in name.lower() or query in desc.lower():
            out.append({"category": "tool", "id": name, "title": name, "subtitle": desc[:90]})
            if len(out) >= limit:
                break
    return out


def _search_tasks(query: str, limit: int = _SEARCH_RESULTS_PER_CATEGORY) -> list[dict]:
    try:
        todos = db.list_todos()
    except Exception as exc:
        print(f"[search] tasks failed: {exc}", flush=True)
        return []
    out = []
    for t in todos:
        text = t.get("text", "") or ""
        if query in text.lower():
            out.append({
                "category": "task", "id": t.get("id"),
                "title": text[:90], "subtitle": t.get("category", ""),
            })
            if len(out) >= limit:
                break
    return out


def _search_kb(query: str, limit: int = _SEARCH_RESULTS_PER_CATEGORY) -> list[dict]:
    try:
        docs = _kb_search(query, limit_per_doc=1)
    except Exception as exc:
        print(f"[search] kb failed: {exc}", flush=True)
        return []
    return [
        {
            "category": "kb", "id": d["filename"], "title": d["title"],
            "subtitle": f"{d['match_count']} match{'es' if d['match_count'] != 1 else ''}",
        }
        for d in docs[:limit]
    ]


@app.get("/api/search")
async def global_search(q: str = "", _token: str = Depends(_auth_session_or_bearer)):
    """Unified search across listings, orders, products, tools, tasks, and
    knowledge base docs -- the header search box's real backing endpoint.
    Every sub-search degrades to an empty list on its own failure, so one
    down data source (e.g. no Etsy credentials) never takes the whole search
    down; the endpoint itself is wrapped too as a final safety net."""
    query = (q or "").strip().lower()
    if not query:
        return {"query": q, "results": [], "count": 0}
    try:
        listings, orders, products, tools, tasks, kb = await asyncio.gather(
            asyncio.to_thread(_search_listings, query),
            asyncio.to_thread(_search_orders, query),
            asyncio.to_thread(_search_products, query),
            asyncio.to_thread(_search_tools, query),
            asyncio.to_thread(_search_tasks, query),
            asyncio.to_thread(_search_kb, query),
        )
        results = listings + orders + products + tools + tasks + kb
    except Exception as exc:
        print(f"[search] unexpected failure: {exc}", flush=True)
        return {"query": q, "results": [], "count": 0, "error": str(exc)[:200]}
    return {"query": q, "results": results, "count": len(results)}


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


def _run_scheduled_coloring_check() -> str:
    """Runs post_scheduled_coloring.py with no flags daily — self-gates on
    data/coloring_schedule.json's next_post_date (every 4 days). Generates draft
    pack (Adult, Kids, Kawaii) and stages action for approval."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "post_scheduled_coloring.py")],
        capture_output=True, text=True, timeout=900, cwd=str(ROOT),
    )
    out = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    if "[SCHEDULED COLORING] Not due yet" in out or "Not due yet" in out:
        return "not due today"
    _append_ops_runbook_entry("Scheduled coloring run", out[:3000])
    return "ran (see ops_runbook for output)"


def _sync_calendar_to_google() -> str:
    """Pushes Frank's own due-dated todos and imminent seasonal/tax
    deadlines onto a connected Google Calendar, so both directions live in
    one place (2026-07-18, the "read + write" half of the Calendar
    integration). Reuses the exact same data /api/cadence already computes
    -- no new data source. Each item gets a stable local key
    (google_calendar_synced_events table) so repeated daily runs never
    create a duplicate event; skips silently (no error surfaced, no
    ops_runbook noise) when Calendar isn't connected, matching every other
    step in this loop's tolerant-failure pattern."""
    try:
        import google_calendar_api as _gcal
    except ImportError:
        return "google_calendar_api not available"
    client = _gcal.GoogleCalendarClient()
    if not client.refresh_token:
        return "not connected"

    synced = 0
    today = _shop_today()  # 2026-08-04: shop-local, not server UTC — see _shop_today() docstring

    todos = db.list_todos()
    for t in todos:
        due = t.get("due_date")
        # Bug fixed 2026-07-18: this loop was missing the "already past" guard
        # the seasonal/tax loops below it both have, so connecting Calendar
        # for the first time backfilled every already-overdue open todo onto
        # the calendar dated in the past.
        if not due or t.get("done") or due < today.isoformat():
            continue
        item_key = f"todo:{t['id']}"
        if db.get_google_calendar_synced_event(item_key) is not None:
            continue
        try:
            event = client.create_event(t["text"][:200], due, "Synced from Frank's to-do list.")
            db.save_google_calendar_synced_event(item_key, event.get("id", ""))
            synced += 1
        except Exception as exc:
            print(f"[gcal-sync] todo {t['id']} sync failed: {exc}", flush=True)

    calendar = seasonal_keywords._build_calendar(today.year)
    for e in calendar:
        update_by = e["update_by"] or seasonal_keywords._update_by(e["peak"])
        if update_by < today:
            continue  # already past -- don't backfill stale deadlines onto the calendar
        item_key = f"seasonal:{e['season']}:{update_by.isoformat()}"
        if db.get_google_calendar_synced_event(item_key) is not None:
            continue
        try:
            event = client.create_event(
                f"Update seasonal keywords: {e['season']}", update_by.isoformat(),
                f"Peak {e['peak'].isoformat()}. Listings: {', '.join(e['listings_to_update'])}.",
            )
            db.save_google_calendar_synced_event(item_key, event.get("id", ""))
            synced += 1
        except Exception as exc:
            print(f"[gcal-sync] seasonal {e['season']} sync failed: {exc}", flush=True)

    tax = json.loads(tax_compliance_tools._get_tax_calendar())["tax_deadlines"]
    for t in tax:
        d = datetime.strptime(t["date"], "%b %d, %Y").date()
        if d < today:
            continue
        item_key = f"tax:{t['event']}:{d.isoformat()}"
        if db.get_google_calendar_synced_event(item_key) is not None:
            continue
        try:
            event = client.create_event(t["event"], d.isoformat(), "Tax deadline (see CLAUDE.md Business Structure & Tax).")
            db.save_google_calendar_synced_event(item_key, event.get("id", ""))
            synced += 1
        except Exception as exc:
            print(f"[gcal-sync] tax deadline {t['event']} sync failed: {exc}", flush=True)

    return f"synced {synced} new item(s)" if synced else "up to date, nothing new"


def _cleanup_synced_calendar_event(item_key: str) -> None:
    """Removes a todo's synced Google Calendar event (if any) and its local
    mapping row. Added 2026-07-18 to close a real gap: completing or
    deleting a todo never touched the calendar event
    _sync_calendar_to_google() had created for it, so those events were
    permanently orphaned on Scott's real calendar. Best-effort and silent —
    called from the todo toggle/delete endpoints, which must always succeed
    on the todo's own DB row regardless of Calendar's connection state or
    any transient Google API failure."""
    event_id = db.get_google_calendar_synced_event(item_key)
    if event_id is None:
        return  # never synced, nothing to clean up
    try:
        import google_calendar_api as _gcal
        client = _gcal.GoogleCalendarClient()
        if client.refresh_token and event_id:
            client.delete_event(event_id)
    except Exception as exc:
        print(f"[gcal-sync] cleanup of {item_key} (event {event_id!r}) failed, "
              f"removing local mapping anyway: {exc}", flush=True)
    db.delete_google_calendar_synced_event(item_key)


def _get_calendar_task_last_run(name: str) -> date | None:
    """Persisted "did this sub-task already run today" state for
    _calendar_tasks_loop, via the same db.settings table
    _check_star_seller_status()/_check_ads_thresholds() already use for
    their own cooldowns. Bug fixed 2026-07-18: this was previously a plain
    in-memory local variable, reset to None on every process restart. A
    same-day redeploy (this app deploys frequently) would then re-satisfy
    e.g. "today != last_weekly" and re-run that day's weekly monitors --
    duplicate email to Scott, duplicate ops_runbook entry, duplicate live
    Etsy API calls from re-running 7 scripts. Persisting survives a restart,
    so a same-day redeploy correctly still counts as "already ran today"."""
    val = db.get_setting(f"calendar_task_last_{name}")
    return date.fromisoformat(val) if val else None


def _set_calendar_task_last_run(name: str, when: date) -> None:
    db.set_setting(f"calendar_task_last_{name}", when.isoformat())


def _run_etsy_file_inventory_sweep() -> str:
    """Daily refresh of the Files tab's 'Etsy Listing Files' section
    (2026-07-19) -- sweeps every active listing's real Etsy file inventory
    (tools/etsy_file_inventory.py's sweep()) and writes the report the same
    atomic way its own CLI does, so GET /api/etsy-files always has a report
    less than a day stale without Scott needing to run the script by hand."""
    import etsy_file_inventory
    result = etsy_file_inventory.sweep()
    result["swept_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = etsy_file_inventory._report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, indent=2))
    tmp.replace(path)
    total_files = sum(len(l["files"]) for l in result["listings"])
    return f"{len(result['listings'])} listing(s), {total_files} file(s), {len(result['skipped'])} skipped"


async def _calendar_tasks_loop() -> None:
    """Hourly-tick calendar-gated loop (same shape as _daily_brief_loop) for
    tasks that fire on a specific day/date rather than a fixed interval:
    weekly monitor digest (Sunday), monthly shop health check (1st), monthly
    competitor research refresh (8th, offset from the 1st/15th so it doesn't
    compete with those), seasonal keyword dry-run (4 documented dates), a
    daily Etsy Ads threshold check, and a daily scheduled-art check (the
    script's own every-other-day gating decides whether it actually does
    anything). Each sub-task tracks its own "last ran" date, persisted (see
    _get_calendar_task_last_run()) so a missed hour (deploy, restart)
    doesn't skip that day entirely — it just fires the next time the loop
    wakes up and the date still matches — while a same-day restart doesn't
    cause a double-fire either."""
    _safe_set_agent_heartbeat("calendar_tasks", "Calendar Tasks", "started", "waiting for next scheduled check")
    last_weekly = _get_calendar_task_last_run("weekly")
    last_monthly = _get_calendar_task_last_run("monthly")
    last_competitor_research = _get_calendar_task_last_run("competitor_research")
    last_seasonal = _get_calendar_task_last_run("seasonal")
    last_ads_check = _get_calendar_task_last_run("ads_check")
    last_art_check = _get_calendar_task_last_run("art_check")
    last_coloring_check = _get_calendar_task_last_run("coloring_check")
    last_art_authenticity = _get_calendar_task_last_run("art_authenticity")
    last_star_seller_check = _get_calendar_task_last_run("star_seller_check")
    last_gcal_sync = _get_calendar_task_last_run("gcal_sync")
    last_etsy_file_inventory = _get_calendar_task_last_run("etsy_file_inventory")
    while True:
        await asyncio.sleep(3600)
        try:
            # 2026-08-06 (full-system audit): the whole-tick try/except below is
            # new -- previously `now`/`today` were computed outside any guard,
            # so an exception there (unlike every sub-task below, each already
            # individually try/excepted) would kill this asyncio.Task silently
            # with no heartbeat update, unlike loops using _run_loop_iteration()'s
            # whole-iteration wrapper.
            now = await asyncio.to_thread(_shop_now)  # 2026-08-04: shop-local, not server UTC
            today = now.date()
            ran = []
            # 2026-07-19: previously only `ran` existed, and the aggregate heartbeat
            # below always reported "ok" no matter what -- a sub-task's own `last_*`
            # var and its `ran.append(...)` both live inside the try block, so a
            # failure left BOTH untouched, and the final heartbeat couldn't tell the
            # difference between "nothing was due today" and "the one thing that was
            # due today failed." A real failure the one day it mattered would render
            # on the dashboard as "ok / no scheduled task due today" -- indistinguishable
            # from a quiet day. Track failures explicitly so the aggregate heartbeat can
            # never lie about that.
            failed = []
            if now.weekday() == 6 and today != last_weekly:  # Sunday
                try:
                    await asyncio.to_thread(_run_weekly_monitors)
                    last_weekly = today
                    _set_calendar_task_last_run("weekly", today)
                    ran.append("weekly-monitors")
                except Exception as exc:
                    print(f"[calendar-tasks] weekly monitors error: {exc}", flush=True)
                    failed.append(f"weekly-monitors:{exc}")
            if today.day == 1 and today != last_monthly:
                try:
                    await asyncio.to_thread(_run_monthly_shop_health)
                    last_monthly = today
                    _set_calendar_task_last_run("monthly", today)
                    ran.append("monthly-shop-health")
                except Exception as exc:
                    print(f"[calendar-tasks] monthly shop health error: {exc}", flush=True)
                    failed.append(f"monthly-shop-health:{exc}")
            if today.day == 15 and today != last_art_authenticity:
                try:
                    await asyncio.to_thread(_run_art_authenticity_check)
                    last_art_authenticity = today
                    _set_calendar_task_last_run("art_authenticity", today)
                    ran.append("art-authenticity")
                except Exception as exc:
                    print(f"[calendar-tasks] art authenticity check error: {exc}", flush=True)
                    failed.append(f"art-authenticity:{exc}")
            if today.day == 8 and today != last_competitor_research:
                try:
                    detail = await asyncio.to_thread(_run_competitor_research_refresh)
                    last_competitor_research = today
                    _set_calendar_task_last_run("competitor_research", today)
                    ran.append(f"competitor-research:{detail}")
                except Exception as exc:
                    print(f"[calendar-tasks] competitor research refresh error: {exc}", flush=True)
                    failed.append(f"competitor-research:{exc}")
            if (today.month, today.day) in _SEASONAL_TRIGGER_DATES and today != last_seasonal:
                try:
                    await asyncio.to_thread(_run_seasonal_keyword_check)
                    last_seasonal = today
                    _set_calendar_task_last_run("seasonal", today)
                    ran.append("seasonal-keywords")
                except Exception as exc:
                    print(f"[calendar-tasks] seasonal keyword check error: {exc}", flush=True)
                    failed.append(f"seasonal-keywords:{exc}")
            if today != last_ads_check:
                try:
                    detail = await asyncio.to_thread(_check_ads_thresholds)
                    last_ads_check = today
                    _set_calendar_task_last_run("ads_check", today)
                    ran.append(f"ads-check:{detail}")
                except Exception as exc:
                    print(f"[calendar-tasks] ads threshold check error: {exc}", flush=True)
                    failed.append(f"ads-check:{exc}")
            if today != last_star_seller_check:
                try:
                    detail = await asyncio.to_thread(_check_star_seller_status)
                    last_star_seller_check = today
                    _set_calendar_task_last_run("star_seller_check", today)
                    ran.append(f"star-seller:{detail}")
                except Exception as exc:
                    print(f"[calendar-tasks] star seller check error: {exc}", flush=True)
                    failed.append(f"star-seller:{exc}")
            if today != last_art_check:
                try:
                    detail = await asyncio.to_thread(_run_scheduled_art_check)
                    last_art_check = today
                    _set_calendar_task_last_run("art_check", today)
                    ran.append(f"scheduled-art:{detail}")
                except Exception as exc:
                    print(f"[calendar-tasks] scheduled art check error: {exc}", flush=True)
                    failed.append(f"scheduled-art:{exc}")
            if today != last_coloring_check:
                try:
                    detail = await asyncio.to_thread(_run_scheduled_coloring_check)
                    last_coloring_check = today
                    _set_calendar_task_last_run("coloring_check", today)
                    ran.append(f"scheduled-coloring:{detail}")
                except Exception as exc:
                    print(f"[calendar-tasks] scheduled coloring check error: {exc}", flush=True)
                    failed.append(f"scheduled-coloring:{exc}")
            if today != last_gcal_sync:
                try:
                    detail = await asyncio.to_thread(_sync_calendar_to_google)
                    last_gcal_sync = today
                    _set_calendar_task_last_run("gcal_sync", today)
                    ran.append(f"gcal-sync:{detail}")
                except Exception as exc:
                    print(f"[calendar-tasks] google calendar sync error: {exc}", flush=True)
                    failed.append(f"gcal-sync:{exc}")
            if today != last_etsy_file_inventory:
                try:
                    detail = await asyncio.to_thread(_run_etsy_file_inventory_sweep)
                    last_etsy_file_inventory = today
                    _set_calendar_task_last_run("etsy_file_inventory", today)
                    ran.append(f"etsy-file-inventory:{detail}")
                except Exception as exc:
                    print(f"[calendar-tasks] etsy file inventory sweep error: {exc}", flush=True)
                    failed.append(f"etsy-file-inventory:{exc}")
            status = "error" if failed else "ok"
            detail_parts = []
            if failed:
                detail_parts.append("FAILED: " + "; ".join(failed))
            if ran:
                detail_parts.append("ran: " + "; ".join(ran))
            if not detail_parts:
                detail_parts.append(
                    f"no scheduled task due today (last: weekly={last_weekly}, "
                    f"monthly={last_monthly}, seasonal={last_seasonal}, ads={last_ads_check}, "
                    f"art={last_art_check}, art_authenticity={last_art_authenticity}, "
                    f"star_seller={last_star_seller_check}, gcal_sync={last_gcal_sync}, "
                    f"etsy_file_inventory={last_etsy_file_inventory})"
                )
            _safe_set_agent_heartbeat("calendar_tasks", "Calendar Tasks", status, " | ".join(detail_parts))
        except Exception as exc:
            _safe_set_agent_heartbeat("calendar_tasks", "Calendar Tasks", "error", f"tick failed: {exc}")
            print(f"[calendar-tasks] tick failed: {exc}", flush=True)


_AGENT_LOOP_LABELS = {
    "snapshot": "Snapshot",
    "suggestion_warmer": "Suggestion Warmer",
    "token_sync": "Token Sync",
    "quality_audit": "Quality Audit",
    "health_check": "Health Check",
    "daily_brief": "Daily Brief",
    "calendar_tasks": "Calendar Tasks",
    "file_audit": "File Integrity Audit",
    "sku_taxonomy_backfill": "SKU + Category Backfill",
    "catalog_reconciliation": "Catalog Reconciliation",
    "review_reply_draft": "Review Reply Drafts",
    "ab_test": "A/B Tests",
    "competitor_watch": "Competitor Watchdog",
    "review_themes": "Review Theme Tracker",
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
    # all of _AGENT_LOOP_LABELS from boot, rather than waiting on each loop's
    # own startup delay (some sleep minutes before their first real run).
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
    asyncio.create_task(_file_audit_loop())
    asyncio.create_task(_sku_taxonomy_backfill_loop())
    asyncio.create_task(_catalog_reconciliation_loop())
    asyncio.create_task(_review_reply_loop())
    asyncio.create_task(_ab_test_loop())
    asyncio.create_task(_competitor_watch_loop())
    asyncio.create_task(_review_theme_loop())


@app.post("/api/calendar-tasks/run")
async def run_calendar_tasks_now(request: Request):
    """Manually trigger each calendar-gated task once, ignoring its normal date
    gate (for testing). Requires X-App-Token header. Read-only/notify-only —
    see _run_weekly_monitors/_run_monthly_shop_health/_run_seasonal_keyword_check/
    _check_ads_thresholds docstrings for exactly what each one does.

    2026-07-19: previously never updated _calendar_tasks_loop's own persisted
    last-run dates, so triggering this on the actual day a task was genuinely
    due (e.g. a Sunday) ran the real live task here AND left the loop's gate
    untouched -- its next hourly tick that same day would run the identical
    task again: duplicate email, duplicate ops_runbook entry, duplicate live
    Etsy calls. Persist the same date keys the loop checks, on success only
    (an error here means the task didn't actually complete, so the loop
    should still get its normal chance to run it for real)."""
    token = request.headers.get("X-App-Token", "")
    if not token or not secrets.compare_digest(token, APP_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized")
    results = {}
    # 2026-08-06 (Today second-pass audit): _calendar_tasks_loop's own gate
    # already uses _shop_now().date() (2026-08-04 fix) -- this manual-trigger
    # endpoint stamping bare date.today() (server UTC) instead could disagree
    # with the loop near a local-midnight boundary and reopen the exact
    # duplicate-run bug the docstring above describes.
    today = _shop_today()
    for name, task_key, fn in [
        ("weekly_monitors", "weekly", _run_weekly_monitors),
        ("monthly_shop_health", "monthly", _run_monthly_shop_health),
        ("competitor_research", "competitor_research", _run_competitor_research_refresh),
        ("seasonal_keywords", "seasonal", _run_seasonal_keyword_check),
        ("ads_threshold", "ads_check", _check_ads_thresholds),
        ("scheduled_art", "art_check", _run_scheduled_art_check),
        ("star_seller", "star_seller_check", _check_star_seller_status),
    ]:
        try:
            results[name] = await asyncio.to_thread(fn)
            _set_calendar_task_last_run(task_key, today)
        except Exception as exc:
            results[name] = f"ERROR: {exc}"
    return results


@app.post("/api/brief/run")
async def run_brief_now(request: Request):
    """Manually trigger the daily brief (for testing). Requires X-App-Token header.

    2026-07-19: previously never touched last_sent_date, so triggering this on
    the actual day (any time) didn't stop _daily_brief_loop's own 6 AM check
    from ALSO sending the brief later that day -- a guaranteed duplicate, not
    just a possible one. Persists the same date the loop itself checks."""
    token = request.headers.get("X-App-Token", "")
    if not token or not secrets.compare_digest(token, APP_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized")
    import daily_brief as _daily_brief
    result = await asyncio.to_thread(_daily_brief.run_daily_brief)
    # 2026-08-06 (Today second-pass audit): shop-local, same reason as above --
    # _daily_brief_loop's own gate already reads shop-local "today" (see its
    # docstring at line ~14273).
    _set_calendar_task_last_run("daily_brief", _shop_today())
    return {"status": result}


@app.post("/api/email/test")
async def test_email_system_endpoint(request: Request):
    """Test SMTP connection, verify credentials, update env if requested, and send test email."""
    token = request.headers.get("X-App-Token", "")
    if not token or not secrets.compare_digest(token, APP_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        body = await request.json()
    except Exception:
        body = {}

    import test_email_system
    user = body.get("user") or os.getenv("SMTP_USER", "")
    password = body.get("password") or os.getenv("SMTP_PASSWORD", "")
    host = body.get("host") or os.getenv("SMTP_HOST", "")
    port = int(body.get("port") or os.getenv("SMTP_PORT") or 587)
    recipient = body.get("recipient") or user or "Printing3dthings@outlook.com"

    if not host:
        host, port = test_email_system.infer_smtp_settings(user)

    success, msg = await asyncio.to_thread(
        test_email_system.test_smtp_connection, host, port, user, password, recipient
    )

    if success:
        os.environ["SMTP_HOST"] = host
        os.environ["SMTP_PORT"] = str(port)
        os.environ["SMTP_USER"] = user
        os.environ["SMTP_PASSWORD"] = password
        test_email_system.update_env_file("SMTP_HOST", host)
        test_email_system.update_env_file("SMTP_PORT", str(port))
        test_email_system.update_env_file("SMTP_USER", user)
        test_email_system.update_env_file("SMTP_PASSWORD", password)

    return {"success": success, "message": msg, "host": host, "port": port, "user": user}



@app.post("/api/file-audit/run")
async def run_file_audit_now(request: Request):
    """Manually trigger the live-Etsy file-integrity audit (for testing, or
    right after fixing a flagged listing so Scott doesn't have to wait up to
    24h for the badge to clear). Requires X-App-Token header. See
    _file_audit_iteration()'s docstring for why this loop exists at all --
    2026-07-21 finding: the audit logic and its /api/alerts + Products-screen
    consumers had shipped, but nothing ever actually ran it in production."""
    token = request.headers.get("X-App-Token", "")
    if not token or not secrets.compare_digest(token, APP_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized")
    result = await _file_audit_iteration()
    return {
        "verified_live": len(result["verified_live"]),
        "genuinely_missing": len(result["genuinely_missing"]),
        "skipped": len(result["skipped"]),
        "audited_at": result["audited_at"],
    }


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


# Panel -> the one representative numeric field pulled out of that panel's
# _compute_*_status() dict for charting (2026-07-22 Phase 3). These panels don't
# have a single obvious "the" number like Revenue/Orders do, so this is a
# deliberate choice per panel: Star Seller's own $300/90d threshold field,
# ROAS's headline ratio, and COGS's headline margin percentage.
_STATUS_PANEL_TREND_FIELD = {
    "star_seller": "revenue_90d",
    "ads_roas": "month_roas",
    "cogs_margin": "avg_margin_pct",
}


@app.get("/api/status-history")
async def get_status_history(panel: str, days: int = 30, _token: str = Depends(_auth_session_or_bearer)):
    """Daily-snapshot trend for one status panel (star_seller/ads_roas/cogs_margin),
    mirroring get_analytics()'s shape -- backs the Phase 3 metric-detail drill-down
    for panels that were previously live-recomputed per-request with no stored
    history. No caching (same reasoning as get_analytics(): a local SQLite read of
    rows already written by the daily snapshot loop has no external-call cost to
    shield against).
    """
    field = _STATUS_PANEL_TREND_FIELD.get(panel)
    if not field:
        raise HTTPException(
            status_code=400,
            detail="panel must be one of: " + ", ".join(_STATUS_PANEL_TREND_FIELD),
        )
    days = max(7, min(days, 90))
    rows = await asyncio.to_thread(db.get_status_history, panel, days)

    dates = [r.get("snapshot_date") for r in rows]
    trend: list = []
    latest_raw: dict = {}
    for r in rows:
        raw = json.loads(r["raw_json"]) if r.get("raw_json") else {}
        trend.append(raw.get(field))
        latest_raw = raw

    return {
        "panel": panel,
        "days": days,
        "snapshot_count": len(rows),
        "dates": dates,
        "trend": trend,
        "latest": latest_raw,
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
        # 2026-07-17 (Wave 4, C2): pull real comparable listings (this
        # listing's own title as the search query) so the diagnosis can cite
        # actual market data for pricing instead of only the static .99/.97/
        # .49-ending rule. Best-effort and non-fatal -- a search hiccup must
        # never break the diagnosis itself, it just runs without this signal.
        comparable = None
        try:
            comp_resp = client.search_listings(listing.get("title", "") or "", limit=8)
            comp_results = [r for r in (comp_resp.get("results") or []) if r.get("listing_id") != listing_id]
            comp_prices = [p for p in (_price_float(r.get("price")) for r in comp_results) if p]
            if comp_prices:
                comparable = {
                    "count": len(comp_results),
                    "price_min": round(min(comp_prices), 2),
                    "price_max": round(max(comp_prices), 2),
                    "price_avg": round(sum(comp_prices) / len(comp_prices), 2),
                    "sample_titles": [(r.get("title") or "")[:70] for r in comp_results[:5]],
                }
        except Exception as exc:  # noqa: BLE001
            print(f"[conversion_doctor] comparable-listings lookup failed (non-fatal): {exc}", flush=True)
        return {"listing": listing, "photo_count": photo_count, "sales": sales, "comparable": comparable}

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

    comparable = gathered.get("comparable")

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
        "comparable_listings": comparable,
    }

    user_payload = (
        "Diagnose why this listing isn't converting. Real data:\n\n"
        f"TITLE ({len(title)} chars): {title}\n"
        f"PRICE: ${price:.2f}\n"
        f"PHOTOS: {photo_count} of 10 recommended\n"
        f"TAGS ({len(tags)}/13): {', '.join(tags) if tags else '(none)'}\n"
        f"VIEWS: {views}   FAVORITES: {favs}   UNITS SOLD: {sales}\n\n"
    )
    if comparable:
        user_payload += (
            f"REAL COMPARABLE LISTINGS (live Etsy search on this listing's own title, "
            f"{comparable['count']} found): price range ${comparable['price_min']:.2f}"
            f"-${comparable['price_max']:.2f}, average ${comparable['price_avg']:.2f}. "
            f"Sample titles: {'; '.join(comparable['sample_titles'])}\n\n"
        )
    else:
        user_payload += "REAL COMPARABLE LISTINGS: not available for this diagnosis.\n\n"
    user_payload += (
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


# Diagnosis areas with a real, reason-aware autofix function to stage a fix
# with. "photos"/"price"/"trust" are real _CONVERSION_DOCTOR_SYSTEM areas but
# have no automated fix path: no code regenerates photos from a diagnosis
# finding (that's a deliberate, larger creative decision), and price changes
# are separately hard-capped at 5/session by CLAUDE.md regardless of source.
_CONVERSION_FIX_HANDLERS = {
    "title": lambda lid, reason: _autofix_title_core(lid, reason=reason),
    "tags": lambda lid, reason: _autofix_tags_core(lid, reason=reason),
    "description": lambda lid, reason: _autofix_description_core(lid, reason=reason),
}


async def _apply_conversion_fixes_core(listing_id: int) -> dict:
    """Closes the loop the original capabilities audit flagged: diagnose_
    listing_conversion (_diagnose_listing_core, above) already pulls real
    views/favorites/sales and produces a genuine per-listing diagnosis via
    Claude, but was read-only and dead-ended -- its findings never reached
    _autofix_title_core/_autofix_tags_core/_autofix_description_core, even
    though all three already accept a `reason` string (previously fed only
    by Scott's manual reject text). Runs a fresh diagnosis (never a stale
    cached one -- the listing may have changed since any earlier diagnosis),
    then for every finding in a fixable area (_CONVERSION_FIX_HANDLERS),
    stages the matching fix using "finding → fix" as the reason/corrective
    guidance. Every fix still lands in the Action Center for one-tap
    approval -- this connects two already-staging-gated systems, it does
    not bypass staging for either. Never raises.

    2026-08-05: gated on the listing being mapped in Frank's manifest/
    registry before any fix handler runs -- the diagnosis itself is grounded
    in the listing's own live Etsy title/tags/price, which for an unmapped
    listing may already be the wrong content (this is precisely how the
    koozie/planner listing-mismatch bug happened). A diagnosis produced from
    already-wrong content is not the same as real corrective guidance, so it
    does NOT count as the `reason` that would otherwise excuse a blind
    rewrite elsewhere in this file -- unlike Scott's own typed reject text,
    this is still ungrounded. The diagnosis (read-only) still runs and is
    still returned, since that's useful, lower-risk information either way."""
    diagnosis_result = await _diagnose_listing_core(listing_id)
    fixes = ((diagnosis_result.get("diagnosis") or {}).get("fixes")) or []

    if fixes and await _get_manifest_entry(listing_id) is None:
        return {
            "listing_id": listing_id,
            "primary_issue": (diagnosis_result.get("diagnosis") or {}).get("primary_issue"),
            "applied": [],
            "skipped": [{"area": "all", "reason": "listing is unmapped -- refusing blind rewrite"}],
            "errors": [],
            "message": (
                f"Diagnosed listing {listing_id} — found {len(fixes)} potential fix(es), but this "
                "listing has no entry in Frank's manifest or registration records, so there's no "
                "grounding for what the product actually is. Refusing to auto-stage title/tags/"
                "description rewrites for it (see the 2026-08-05 koozie/planner bug in "
                f"ops_runbook.md). Ask {business_config.OWNER_NAME} to map or register it first, "
                "or use autofix_listing_tags/autofix_listing_title with an explicit `reason` if "
                "you know specifically what's wrong."
            ),
        }

    applied: list[dict] = []
    skipped: list[dict] = []
    errors: list[dict] = []

    for fix in fixes:
        area = str(fix.get("area", "")).strip().lower()
        finding = str(fix.get("finding", "")).strip()
        fix_text = str(fix.get("fix", "")).strip()
        reason_text = f"{finding} → {fix_text}".strip(" →") if (finding or fix_text) else ""

        handler = _CONVERSION_FIX_HANDLERS.get(area)
        if handler is None:
            skipped.append({"area": area or "(unspecified)", "reason": "no automated fix exists for this area yet"})
            continue
        if not reason_text:
            skipped.append({"area": area, "reason": "diagnosis gave no actionable finding/fix text"})
            continue

        try:
            result = await handler(listing_id, reason_text)
        except Exception as exc:  # noqa: BLE001
            errors.append({"area": area, "error": str(exc)[:200]})
            continue

        if "error" in result:
            errors.append({"area": area, "error": result["error"]})
        elif result.get("skipped"):
            skipped.append({"area": area, "reason": result.get("reason", "already compliant")})
        else:
            applied.append({"area": area, "action_id": result.get("action_id"), "finding": finding, "fix": fix_text})

    message_parts = []
    if applied:
        message_parts.append(f"staged {len(applied)} fix(es) for {business_config.OWNER_NAME}'s approval")
    if skipped:
        message_parts.append(f"{len(skipped)} area(s) had nothing automated to do")
    if errors:
        message_parts.append(f"{len(errors)} area(s) failed")
    message = ("Diagnosed listing " + str(listing_id) + " — " + "; ".join(message_parts) + ".") if message_parts \
        else f"Diagnosed listing {listing_id} — no fixable findings in this diagnosis."

    return {
        "listing_id": listing_id,
        "primary_issue": (diagnosis_result.get("diagnosis") or {}).get("primary_issue"),
        "applied": applied,
        "skipped": skipped,
        "errors": errors,
        "message": message,
    }


@app.post("/api/conversion-targets/{listing_id}/fix")
async def conversion_target_fix(listing_id: int, _token: str = Depends(_auth_session_or_bearer)):
    """2026-07-18: deterministic REST path for the mobile 'Let Frank fix it'
    button (phoneSheetFix() in frank_hud_mockup.py). Previously that button
    only sent a natural-language prompt into chat asking Frank to diagnose
    AND fix the listing -- the chat agent reliably ran the diagnosis but,
    per Scott's report, routinely stopped there instead of also calling
    apply_conversion_fixes/the autofix tools, so nothing ever reached the
    Action Center. This route calls _apply_conversion_fixes_core directly,
    guaranteeing the diagnose-then-stage sequence actually runs every time
    instead of depending on the chat model choosing to chain the right
    tool calls. Still 100% staging-only -- _apply_conversion_fixes_core
    never touches the live listing, every fix lands in the Action Center
    for one-tap approval."""
    return await _apply_conversion_fixes_core(listing_id)


def _get_comparable_listings(tool_input: dict) -> dict:
    """2026-07-17 (Wave 4, C1): the shop's first real external market-data
    source. EtsyAPIClient.search_listings() (tools/etsy_api.py) already
    existed, already correctly hits the real public `listings/active` v3
    endpoint (public API key only, no OAuth, no scraping/ToS risk) — it was
    simply never exposed as an agent tool. tools/fetch_market_examples.py
    duplicated its own raw-requests version of the same call instead of
    reusing this one; this wraps the real client method directly, no new
    HTTP logic. Before this, every pricing/title/tag recommendation in this
    codebase came from a static rule (the .99/.97/.49 price-ending check,
    canonical tag sets) with zero live comparable-listing evidence behind
    it. Never raises — returns {"error": str} on failure."""
    keywords = str((tool_input or {}).get("keywords", "")).strip()
    if not keywords:
        return {"error": "keywords is required"}
    try:
        limit = max(1, min(int((tool_input or {}).get("limit") or 10), 25))
    except (TypeError, ValueError):
        limit = 10
    min_price = tool_input.get("min_price")
    max_price = tool_input.get("max_price")
    try:
        min_price = float(min_price) if min_price is not None else None
        max_price = float(max_price) if max_price is not None else None
    except (TypeError, ValueError):
        return {"error": "min_price/max_price must be numbers"}

    try:
        resp = EtsyAPIClient().search_listings(
            keywords, limit=limit, min_price=min_price, max_price=max_price,
        )
    except Exception as exc:  # noqa: BLE001
        return {"error": f"comparable-listing search failed: {str(exc)[:200]}"}

    listings = []
    for r in (resp.get("results") or []):
        listings.append({
            "listing_id": r.get("listing_id"),
            "title": r.get("title", ""),
            "price": _price_float(r.get("price")),
            "tags": (r.get("tags") or [])[:13],
            "url": f"https://www.etsy.com/listing/{r.get('listing_id')}",
        })

    prices = [l["price"] for l in listings if l["price"]]
    price_range = (
        {"min": round(min(prices), 2), "max": round(max(prices), 2), "avg": round(sum(prices) / len(prices), 2)}
        if prices else None
    )
    return {
        "keywords": keywords,
        "count": len(listings),
        "listings": listings,
        "price_range": price_range,
    }


# ── Competitor Price & Listing Drift Watchdog (2026-08-06, "significantly
# improve Frank" idea 4/6, second batch) ────────────────────────────────────
# Weekly sweep reusing _get_comparable_listings() -- the shop's only real
# external market-data source, already wired to Etsy's public listings/active
# search (public API key, no OAuth, no scraping/ToS risk) -- across every
# active listing's own tags. Logs a durable per-listing price-history
# snapshot and flags when Scott's price has drifted meaningfully out of step
# with the real, live comparable-listing average. Never changes price itself
# -- price changes always require Scott's approval (Autonomy Boundaries) --
# this only ever surfaces the real gap with real numbers.
_COMPETITOR_SNAPSHOTS_PATH = db.resolve_persistent_path(
    "competitor_snapshots.json",
    fallback=ROOT / "data" / "competitor_snapshots.json",
)
_COMPETITOR_DRIFT_THRESHOLD_PCT = 0.20  # 20% away from the real comparable average
_COMPETITOR_MIN_SAMPLE = 3  # need at least this many real comparables to trust the average
_COMPETITOR_SNAPSHOT_HISTORY_WEEKS = 12  # bounds the sidecar's per-listing history


def _load_competitor_snapshots() -> dict:
    try:
        return json.loads(_COMPETITOR_SNAPSHOTS_PATH.read_text())
    except (OSError, ValueError):
        return {}


def _save_competitor_snapshots(data: dict) -> None:
    _COMPETITOR_SNAPSHOTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _COMPETITOR_SNAPSHOTS_PATH.write_text(json.dumps(data, indent=2))


def _competitor_watch_keywords(listing: dict) -> str:
    """Real buyer-intent search phrase for this listing -- its own top 2 tags
    (already curated buyer-intent phrases per CLAUDE.md's tag rules), falling
    back to the title only when a listing has no tags."""
    tags = listing.get("tags") or []
    if tags:
        return " ".join(tags[:2])
    return (listing.get("title") or "")[:50]


async def _competitor_watch_iteration() -> dict:
    """One weekly sweep: for every active listing, pull real live comparable
    listings via the shop's own tags and log this week's real competitor
    average alongside Scott's real price. Never touches Etsy's write API --
    read-only search calls only."""
    listings_data = await asyncio.to_thread(_listings_sync, "active")
    active = listings_data.get("listings", [])
    own_ids = {l["listing_id"] for l in active}
    snapshots = await asyncio.to_thread(_load_competitor_snapshots)
    today = (await asyncio.to_thread(_shop_today)).isoformat()
    checked, flagged, skipped = 0, 0, 0
    for listing in active:
        listing_id = listing["listing_id"]
        my_price = listing.get("price")
        keywords = _competitor_watch_keywords(listing)
        if not my_price or not keywords:
            skipped += 1
            continue
        result = await asyncio.to_thread(_get_comparable_listings, {"keywords": keywords, "limit": 15})
        await asyncio.sleep(0.5)  # be considerate to Etsy's public search endpoint
        if "error" in result:
            skipped += 1
            continue
        comparables = [
            l for l in result.get("listings", [])
            if l.get("listing_id") not in own_ids and l.get("price")
        ]
        checked += 1
        if len(comparables) < _COMPETITOR_MIN_SAMPLE:
            continue
        comp_prices = [l["price"] for l in comparables]
        comp_avg = round(sum(comp_prices) / len(comp_prices), 2)
        history = snapshots.setdefault(str(listing_id), [])
        history.append({
            "date": today, "my_price": my_price, "competitor_avg": comp_avg,
            "competitor_count": len(comparables), "keywords": keywords,
        })
        snapshots[str(listing_id)] = history[-_COMPETITOR_SNAPSHOT_HISTORY_WEEKS:]
        if comp_avg > 0 and abs(my_price - comp_avg) / comp_avg >= _COMPETITOR_DRIFT_THRESHOLD_PCT:
            flagged += 1
    await asyncio.to_thread(_save_competitor_snapshots, snapshots)
    return {"checked": checked, "flagged": flagged, "skipped": skipped}


async def _competitor_watch_loop() -> None:
    """Weekly: same resilience/backoff pattern as _snapshot_loop()/_ab_test_loop()."""
    await asyncio.sleep(120)  # let the app finish booting first
    while True:
        delay = await _run_loop_iteration(
            "competitor_watch", "Competitor Watchdog", _competitor_watch_iteration,
            on_success_detail=lambda r: f"{r['flagged']} listing(s) flagged out of {r['checked']} checked ({r['skipped']} skipped)",
            base_interval=7 * 86_400,
        )
        await asyncio.sleep(delay)


def _compute_competitor_drift_items() -> list[dict]:
    """Pure read over the durable snapshot sidecar -- no I/O, no Etsy call --
    so GET /api/competitor-watch and Growth Brief can both call this cheaply
    without waiting on the weekly sweep. Only ever reports the MOST RECENT
    snapshot per listing; a listing that's since been fixed (or hasn't been
    swept yet) simply has nothing here."""
    snapshots = _load_competitor_snapshots()
    items = []
    for listing_id, history in snapshots.items():
        if not history:
            continue
        latest = history[-1]
        comp_avg = latest["competitor_avg"]
        my_price = latest["my_price"]
        if comp_avg <= 0:
            continue
        gap_pct = (my_price - comp_avg) / comp_avg
        if abs(gap_pct) < _COMPETITOR_DRIFT_THRESHOLD_PCT:
            continue
        items.append({
            "listing_id": int(listing_id), "my_price": my_price,
            "competitor_avg": comp_avg, "competitor_count": latest["competitor_count"],
            "keywords": latest["keywords"], "date": latest["date"],
            "gap_pct": round(gap_pct * 100, 1),
            "direction": "above" if gap_pct > 0 else "below",
            "url": f"https://www.etsy.com/listing/{listing_id}",
        })
    items.sort(key=lambda it: abs(it["gap_pct"]), reverse=True)
    return items


@app.get("/api/competitor-watch")
async def get_competitor_watch(_token: str = Depends(_auth_session_or_bearer)):
    """Today/Growth Brief's competitor price-drift findings. Reads the
    durable weekly-sweep sidecar -- never makes a live Etsy call itself, so
    this is always instant. Cached 300s (the underlying data only changes
    once a week; this just avoids re-reading the file on every poll)."""
    cached = _cache_get("competitor_watch", ttl=300)
    if cached is not None:
        return cached
    data = {"items": await asyncio.to_thread(_compute_competitor_drift_items)}
    _cache_set("competitor_watch", data)
    return data


# ── Weekly "What Changed" Movement Digest (2026-08-06, "significantly
# improve Frank" idea 5/6, second batch) ────────────────────────────────────
# Turns the CLAUDE.md-documented manual monthly ritual ("compare conversion
# rates... identify listings with high views but low conversion") into a
# standing digest computed from data Frank already collects daily -- real
# week-over-week views/favorites deltas from listing_snapshots (populated by
# the existing _snapshot_loop(), same table A/B testing's comparison logic
# reads) and real orders/revenue from ONE shared, date-scoped get_orders()
# call covering the full 14-day window (not per-listing -- a single receipts
# fetch bucketed by listing_id and by which 7-day half it falls in). Zero new
# Etsy calls beyond that one shared fetch; everything else is a local SQLite
# read. Real numbers only -- a listing with fewer than 2 daily snapshots in a
# window reports null views/favorites deltas rather than a misleading 0.
def _movement_window_delta(rows: list[dict]) -> tuple:
    if len(rows) < 2:
        return None, None
    return rows[-1]["views"] - rows[0]["views"], rows[-1]["num_favorers"] - rows[0]["num_favorers"]


async def _compute_movement_digest() -> dict:
    today = await asyncio.to_thread(_shop_today)
    try:
        listings_data = await asyncio.to_thread(_listings_sync, "active")
    except Exception as exc:
        # Same "never a bare 500" rule every other Growth-Brief-adjacent
        # compute function in this file follows (see _compute_star_seller_
        # status()'s own per-call try/except) -- an Etsy outage or missing
        # OAuth token must degrade to an honest empty digest, not crash the
        # endpoint. 2026-08-06: caught live in Playwright verification --
        # this was the one Etsy call in the whole function not wrapped.
        print(f"[movement_digest] listings fetch failed (non-fatal, empty digest returned): {exc}", flush=True)
        return {
            "winners": [], "decliners": [],
            "week_start": (today - timedelta(days=7)).isoformat(),
            "prior_week_start": (today - timedelta(days=14)).isoformat(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    active = listings_data.get("listings", [])
    id_to_title = {l["listing_id"]: l["title"] for l in active}

    this_week_start = today - timedelta(days=7)
    last_week_start = today - timedelta(days=14)
    this_week_start_iso = this_week_start.isoformat()

    view_stats: dict[int, dict] = {}
    for l in active:
        rows = await asyncio.to_thread(
            db.get_listing_snapshot_history, l["listing_id"],
            last_week_start.isoformat(), today.isoformat(),
        )
        this_week_rows = [r for r in rows if r["snapshot_date"] >= this_week_start_iso]
        last_week_rows = [r for r in rows if r["snapshot_date"] < this_week_start_iso]
        tw_views, tw_favs = _movement_window_delta(this_week_rows)
        lw_views, lw_favs = _movement_window_delta(last_week_rows)
        view_stats[l["listing_id"]] = {
            "this_week_views": tw_views, "this_week_favs": tw_favs,
            "last_week_views": lw_views, "last_week_favs": lw_favs,
        }

    order_stats: dict[int, dict] = {
        lid: {"this_week_orders": 0, "this_week_revenue": 0.0, "last_week_orders": 0, "last_week_revenue": 0.0}
        for lid in id_to_title
    }
    try:
        start_ts = int(datetime.fromisoformat(last_week_start.isoformat()).replace(tzinfo=timezone.utc).timestamp())
        this_week_start_ts = int(datetime.fromisoformat(this_week_start_iso).replace(tzinfo=timezone.utc).timestamp())
        r = await asyncio.to_thread(
            lambda: EtsyAPIClient().get_orders(limit=100, status="paid", min_created=start_ts)
        )
        for receipt in r.get("results", []) or []:
            bucket = "this_week" if receipt.get("create_timestamp", 0) >= this_week_start_ts else "last_week"
            for t in receipt.get("transactions", []) or []:
                lid = t.get("listing_id")
                if lid not in order_stats:
                    continue
                qty = int(t.get("quantity", 1) or 1)
                price = t.get("price") or {}
                amt = (price.get("amount", 0) / price.get("divisor", 100)) if price.get("divisor") else 0
                order_stats[lid][f"{bucket}_orders"] += qty
                order_stats[lid][f"{bucket}_revenue"] += amt * qty
    except Exception as exc:
        print(f"[movement_digest] order fetch failed (non-fatal, views/favorites still shown): {exc}", flush=True)

    items = []
    for lid, title in id_to_title.items():
        vs = view_stats.get(lid, {})
        os_ = order_stats.get(lid, {})
        revenue_delta = round(os_.get("this_week_revenue", 0) - os_.get("last_week_revenue", 0), 2)
        items.append({
            "listing_id": lid, "title": title,
            "this_week_views": vs.get("this_week_views"), "last_week_views": vs.get("last_week_views"),
            "this_week_favs": vs.get("this_week_favs"), "last_week_favs": vs.get("last_week_favs"),
            "this_week_orders": os_.get("this_week_orders", 0), "last_week_orders": os_.get("last_week_orders", 0),
            "this_week_revenue": round(os_.get("this_week_revenue", 0), 2),
            "last_week_revenue": round(os_.get("last_week_revenue", 0), 2),
            "revenue_delta": revenue_delta,
        })

    winners = sorted([it for it in items if it["revenue_delta"] > 0], key=lambda it: it["revenue_delta"], reverse=True)[:5]
    decliners = sorted([it for it in items if it["revenue_delta"] < 0], key=lambda it: it["revenue_delta"])[:5]
    return {
        "winners": winners, "decliners": decliners,
        "week_start": this_week_start_iso, "prior_week_start": last_week_start.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/movement-digest")
async def get_movement_digest(_token: str = Depends(_auth_session_or_bearer)):
    """Real week-over-week winners/decliners by revenue delta. Cached 1800s
    (30min) -- this is a weekly-cadence digest, not a live ticker, and the
    underlying receipts fetch is a real Etsy call worth not repeating on
    every poll."""
    cached = _cache_get("movement_digest", ttl=1800)
    if cached is not None:
        return cached
    data = await _compute_movement_digest()
    _cache_set("movement_digest", data)
    return data


# ── Recurring Complaint / Review Theme Tracker (2026-08-06, "significantly
# improve Frank" idea 6/6, second batch) ────────────────────────────────────
# CLAUDE.md's mission language: "every support message is a review that
# didn't happen." One critical review naming a problem is noise; several
# reviews on the SAME listing independently naming the SAME problem is a
# real, fixable defect getting missed because Frank (and Scott) only ever
# sees reviews one at a time. This mines the full text of real reviews
# (already fetched via EtsyAPIClient.get_reviews(), same source
# _review_reply_iteration()/Star Seller use) for genuinely recurring
# significant terms across 2+ distinct negative reviews on one listing --
# no LLM summarization, no paraphrasing, so nothing can be invented: every
# "theme" is a real word/phrase that appears verbatim in 2+ real reviews,
# and every excerpt shown is the real review text it came from, never
# reworded stronger or weaker than what the buyer actually wrote.
#
# Scope note (honest, matching _get_recent_orders_raw()'s own caveat
# pattern): get_reviews() is capped at 100 results per call (Etsy's own
# per-request limit) with no pagination wired here -- this covers the
# shop's most recent 100 reviews, not literally every review ever left,
# same scope as _compute_star_seller_status()'s own reviews call.
_REVIEW_THEME_STOPWORDS = frozenset({
    "about", "after", "again", "always", "another", "anything", "around",
    "because", "been", "before", "being", "better", "could", "didn",
    "doesn", "doing", "download", "downloaded", "each", "every", "even",
    "everything", "exactly", "first", "found", "from", "getting", "going",
    "great", "happy", "have", "having", "here", "however", "instead",
    "isn", "item", "just", "know", "like", "little", "love", "loved",
    "lovely", "make", "makes", "many", "more", "much", "myself", "never",
    "nice", "once", "only", "other", "over", "perfect", "planner",
    "pretty", "product", "purchase", "purchased", "quality", "quickly",
    "really", "received", "recommend", "should", "since", "some", "still",
    "such", "sure", "thank", "thanks", "that", "their", "them", "then",
    "there", "these", "they", "thing", "things", "think", "this", "those",
    "though", "through", "time", "took", "under", "using", "very", "wanted",
    "wasn", "were", "what", "when", "where", "which", "while", "will",
    "with", "wonderful", "won", "would", "your",
})


def _significant_review_terms(text: str) -> set[str]:
    """Real, verifiable term extraction -- no LLM, so nothing can be
    invented. Lowercased words of 5+ letters, common/generic words filtered
    out, so shared terms across 2+ negative reviews point at an actual
    recurring concern rather than filler language."""
    words = _re.findall(r"[a-zA-Z']+", (text or "").lower())
    return {w.strip("'") for w in words if len(w.strip("'")) >= 5} - _REVIEW_THEME_STOPWORDS


def _compute_review_theme_findings(reviews_result: dict, id_to_title: dict) -> list[dict]:
    """Pure function over an already-fetched reviews payload -- no I/O, so
    this is directly unit-testable with synthetic reviews. Flags a listing
    only when the SAME significant term appears in 2+ distinct negative
    (<=3 star) reviews with real text -- every excerpt attached is the
    real, unmodified review text it was found in."""
    by_listing: dict = {}
    for r in reviews_result.get("results", []) or []:
        rating = r.get("rating", 5)
        text = (r.get("review") or "").strip()
        if rating > 3 or not text:
            continue
        lid = r.get("listing_id")
        if lid is None:
            continue
        by_listing.setdefault(lid, []).append({
            "rating": rating, "text": text,
            "terms": _significant_review_terms(text),
        })

    findings = []
    for lid, entries in by_listing.items():
        if len(entries) < 2:
            continue
        term_counts: dict = {}
        for e in entries:
            for term in e["terms"]:
                term_counts.setdefault(term, set()).add(id(e))
        recurring = {t: idxs for t, idxs in term_counts.items() if len(idxs) >= 2}
        if not recurring:
            continue
        top_term = max(recurring, key=lambda t: len(recurring[t]))
        matching_entries = [e for e in entries if top_term in e["terms"]]
        findings.append({
            "listing_id": lid, "title": id_to_title.get(lid, f"Listing {lid}"),
            "shared_term": top_term, "review_count": len(matching_entries),
            "total_negative_reviews": len(entries),
            "excerpts": [{"rating": e["rating"], "text": e["text"][:300]} for e in matching_entries[:4]],
        })
    findings.sort(key=lambda f: f["review_count"], reverse=True)
    return findings[:5]


async def _compute_review_themes() -> dict:
    try:
        reviews_result = await asyncio.to_thread(lambda: EtsyAPIClient().get_reviews(limit=100))
    except Exception as exc:
        # Same "never a bare 500" rule as every sibling compute function --
        # see the real bug this pattern fixed in _compute_movement_digest().
        print(f"[review_themes] reviews fetch failed (non-fatal, empty result returned): {exc}", flush=True)
        return {"findings": [], "generated_at": datetime.now(timezone.utc).isoformat()}
    listings_data = await asyncio.to_thread(_listings_sync, "active")
    id_to_title = {l["listing_id"]: l["title"] for l in listings_data.get("listings", [])}
    findings = await asyncio.to_thread(_compute_review_theme_findings, reviews_result, id_to_title)
    return {"findings": findings, "generated_at": datetime.now(timezone.utc).isoformat()}


async def _review_theme_loop() -> None:
    """Weekly: same resilience/backoff pattern as _competitor_watch_loop()."""
    await asyncio.sleep(150)  # let the app finish booting first
    while True:
        delay = await _run_loop_iteration(
            "review_themes", "Review Theme Tracker", _review_theme_iteration,
            on_success_detail=lambda r: f"{len(r.get('findings', []))} recurring theme(s) found",
            base_interval=7 * 86_400,
        )
        await asyncio.sleep(delay)


_REVIEW_THEMES_PATH = db.resolve_persistent_path(
    "review_theme_findings.json",
    fallback=ROOT / "data" / "review_theme_findings.json",
)


async def _review_theme_iteration() -> dict:
    data = await _compute_review_themes()
    await asyncio.to_thread(
        lambda: _REVIEW_THEMES_PATH.parent.mkdir(parents=True, exist_ok=True) or
        _REVIEW_THEMES_PATH.write_text(json.dumps(data, indent=2))
    )
    return data


def _load_review_themes() -> dict:
    try:
        return json.loads(_REVIEW_THEMES_PATH.read_text())
    except (OSError, ValueError):
        return {"findings": [], "generated_at": None}


@app.get("/api/review-themes")
async def get_review_themes(_token: str = Depends(_auth_session_or_bearer)):
    """Recurring-complaint findings from the weekly sweep's durable sidecar
    -- reads the last computed result instantly rather than re-fetching
    reviews on every poll. Falls through to a live compute on first-ever
    load (empty sidecar) so the panel isn't blank for a full week."""
    cached = _load_review_themes()
    if cached.get("generated_at"):
        return cached
    data = await _review_theme_iteration()
    return data


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
        if reason:
            # Surfaced in the Approvals screen's detail panel (see _actionPreviewHtml,
            # 2026-07-18 audit-report fix) so Scott sees WHY Frank staged this, not just
            # what changed -- this "finding -> fix" text already existed
            # (_apply_conversion_fixes_core builds it) but was discarded before this fix.
            payload["reason"] = reason
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
    engine = _effective_text_engine()
    if engine == "anthropic" and not ANTHROPIC_KEY:
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

    try:
        if engine == "grok":
            new_title_raw = await asyncio.wait_for(
                asyncio.to_thread(lambda: _grok_text(prompt, max_tokens=100)),
                timeout=30.0,
            )
        else:
            ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
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
            new_title_raw = "".join(getattr(b, "text", "") for b in response.content)
    except asyncio.TimeoutError:
        return {"error": "Title generation timed out", "listing_id": listing_id}
    except Exception as exc:
        return {"error": f"Title generation failed: {exc}", "listing_id": listing_id}

    try:
        new_title = new_title_raw.strip().strip('"\'')

        payload = {"listing_id": listing_id, "title": new_title, "_state_at_staging": listing.get("state")}
        if reason:
            payload["reason"] = reason  # see the matching comment in _autofix_tags_core above
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
    """Two fix paths, tried in order:

    1. Deterministic (no AI call) fix for CLAUDE.md's wall-art Gate 6 rule:
       prepend the exact mandated opening line when a description doesn't
       already signal instant/digital download + printable. Only applies to
       wall_art-type listings. Always wins when it applies, regardless of
       `reason` — cheap, exact, and already proven; a general LLM rewrite
       should never override this specific, well-tested case.

    2. 2026-07-17 (Wave 4, B3 retargeted from dead code in etsy_listing_
       tools.py to the real live gap): when Gate 6 doesn't apply (not
       wall_art, or already compliant) AND a `reason` is given — either a
       Scott reject or a conversion-diagnosis finding — do a real Claude
       call rewriting ONLY the opening hook (first 1-2 sentences), the same
       narrow-blast-radius pattern Gate 6 itself uses (touch the hook, never
       the WHAT'S INCLUDED/factual body). Before this, description autofix
       was the one of the three (title/tags/description) with no real AI
       path at all — title and tags both already call Claude via
       _autofix_title_core/_generate_tags_for_listings.

    Product type is detected via listing_qc._detect_product_type(title,
    description), a title-keyword heuristic ("wall art" or "printable" in the
    title) that under-detects real wall-art listings whose titles read e.g.
    "X Art Print" with neither phrase (confirmed 2026-07-15 sweeping the live
    catalog: MISC_BOTANICAL_HERBS_ART_PRINT and several siblings misdetected
    as digital_planner). Pass assume_wall_art=True when the caller already
    knows the true category from a more authoritative source (e.g.
    product_catalog.json's `category` field) to bypass the heuristic.

    Never raises — returns {"error": str} on failure, {"skipped": True, ...}
    when there's nothing actionable, so a caller sweeping many listings can
    tell "nothing to do here" apart from a real failure."""
    if listing is None:
        listing = await _fetch_listing_for_autofix(listing_id)

    title = listing.get("title", "")
    description = listing.get("description", "") or ""

    if assume_wall_art:
        product_type = "wall_art"
    else:
        import listing_qc
        product_type = listing_qc._detect_product_type(title, description)

    if product_type == "wall_art" and _description_needs_gate6_fix(description):
        new_description = _WALL_ART_GATE6_LINE + "\n\n" + description
        try:
            payload = {
                "listing_id": listing_id, "description": new_description,
                "before_description": description,  # display-only, for the Action Center diff view
                "_state_at_staging": listing.get("state"),
                # This path fires on a deterministic rule, not an LLM diagnosis, so it
                # always has a concrete reason even when the caller passed none.
                "reason": reason or "CLAUDE.md Gate 6: wall art descriptions must open with an "
                                     "instant-download/printable disclosure — this listing's didn't.",
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

    if not reason:
        return {
            "skipped": True, "listing_id": listing_id,
            "reason": "already compliant" if product_type == "wall_art" else f"not a wall_art listing (detected: {product_type})",
        }

    if not ANTHROPIC_KEY:
        return {"error": "ANTHROPIC_API_KEY not configured", "listing_id": listing_id}
    if not description.strip():
        return {"error": "listing has no description to rewrite the hook of", "listing_id": listing_id}

    # The hook is everything before the first blank line (matches how every
    # description in this codebase is structured — one opening paragraph,
    # then a blank line, then the ━━━ WHAT'S INCLUDED section).
    hook, _, rest = description.partition("\n\n")
    if not rest:
        return {"error": "could not isolate the opening hook from the rest of the description "
                          "(no blank-line separator found) — refusing rather than rewriting the whole thing",
                "listing_id": listing_id}

    prompt = _DESCRIPTION_HOOK_FIX_PROMPT.format(title=title, hook=hook.strip(), reason=reason)
    ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: _anthropic_create(
                    ai_client,
                    model=business_config.MODEL_CHEAP,
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}],
                )
            ),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        return {"error": "Description hook generation timed out", "listing_id": listing_id}
    except Exception as exc:
        return {"error": f"Description hook generation failed: {exc}", "listing_id": listing_id}

    new_hook = "".join(getattr(b, "text", "") for b in response.content).strip().strip('"\'')
    if not new_hook:
        return {"error": "generated hook was empty", "listing_id": listing_id}
    new_description = new_hook + "\n\n" + rest

    try:
        payload = {
            "listing_id": listing_id, "description": new_description,
            "before_description": description,
            "_state_at_staging": listing.get("state"),
            "reason": reason,  # always non-empty here -- see the guard above
        }
        candidate = {"type": "update_description", "payload": payload}
        ok, msg = _validate_staged_action(candidate)
        if not ok:
            return {"error": f"Quality gate: {msg}", "listing_id": listing_id}

        title_short = (title or f"Listing {listing_id}")[:50]
        prefix = "Reject-fix description" if reason else "Conversion-fix description hook"
        summary = f"{prefix}: {title_short}"
        action_id = db.enqueue_action("update_description", summary, payload)
    except Exception as exc:
        return {"error": f"Could not stage description fix: {exc}", "listing_id": listing_id}

    with _cache_lock:
        _cache.pop("actions", None)

    return {"action_id": action_id, "listing_id": listing_id, "new_hook": new_hook}


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
    still broken, plus a todo is added either way.

    Three cases: mapped-and-clean (diagnosis runs, finds nothing -- title/tags
    still get a routine refresh, republish is unconditional), mapped-with-issues
    (diagnosis runs, non-title/tag FAILs surface as unfixable_issues), and
    unmapped (no data/listing_manifest.json entry -- the diagnosis literally
    cannot run, so it's fail-closed into its own unfixable_issues entry rather
    than silently defaulting to "looks fine," matching the same-shaped
    _unmapped_result() fail-closed handling listing_compliance_sweep.py already
    applies shop-wide; 2026-07-22, see ops_runbook.md)."""
    instructions = ((body or {}).get("instructions") or "").strip()
    listing = await _fetch_listing_for_autofix(listing_id)

    diagnosis = ""
    unfixable_issues: list[dict] = []
    is_mapped = False
    try:
        import listing_integrity_check as lic

        # 2026-08-05: was manifest.get(str(listing_id)) against the raw git
        # file only -- a listing registered via register_product (which can
        # only durably write the override sidecar, never the git-tracked
        # file itself) would look unmapped again here forever. _get_manifest_
        # entry() checks both.
        entry = await _get_manifest_entry(listing_id)
        if entry:
            is_mapped = True
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
        else:
            unfixable_issues = [{
                "severity": "FAIL",
                "check": "no_manifest_mapping",
                "detail": (
                    "This listing has no entry in data/listing_manifest.json or Frank's "
                    "registration records, so Frank has no record of what this product "
                    "actually is. Frank will NOT auto-generate "
                    "a title/tags fix here -- rewriting text with zero grounding just produces "
                    "a more confident-sounding WRONG title (this is exactly how 3 untracked "
                    "koozie/planner listings ended up with mismatched photos and titles, "
                    "caught 2026-08-05). Map this listing in the manifest first, or review and "
                    "fix it by hand on Etsy -- including checking the photos actually match "
                    "the title."
                ),
            }]
    except Exception as exc:
        print(f"[request-fix] diagnosis lookup failed for {listing_id}: {exc}", flush=True)
        unfixable_issues = [{
            "severity": "FAIL",
            "check": "diagnosis_lookup_failed",
            "detail": f"Frank couldn't check whether this listing is tracked ({exc}) -- review it manually rather than trusting an auto-generated fix.",
        }]

    reason = " ".join(p for p in (diagnosis, instructions) if p).strip()

    staged: list[dict] = []
    errors: list[str] = []

    # 2026-08-05: only generate/stage a title-tags rewrite when Frank has real
    # grounding -- either a manifest entry (audit_listing knows what this
    # product actually is) or Scott's own typed instructions describing what's
    # wrong. An unmapped listing with no instructions gets skipped entirely
    # (unfixable_issues above explains why) rather than silently producing a
    # confident-sounding rewrite of a title Frank has no way to verify.
    if is_mapped or instructions:
        if not reason:
            reason = "This listing was deactivated. Review the title and tags for anything that could be wrong and improve them."

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

    # Only stage a reactivation for listings that are actually inactive --
    # for an already-active listing, "publish_listing" is a harmless no-op
    # PATCH (client.update_listing(lid, {"state": "active"}), see
    # _execute_staged_action), so staging it there just puts a meaningless
    # "Republish..." approval in front of Scott for a listing that was never
    # taken down (2026-07-30, this endpoint used to be reachable only from
    # deactivated listings; the Listings-tab Fix button now offers it on
    # every listing regardless of state).
    if listing.get("state") != "active":
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
    "deactivate_listing", "toggle_listing_state", "update_price",
    "update_sku_and_category",
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
# create_listing (2026-07-18, Products-tappable-cards feature) can't share
# _ETSY_STAGED_ACTION_TYPES -- every branch there (both validation and
# _execute_staged_action) assumes an existing listing_id, and this is the
# one Etsy mutation that doesn't have one yet (it's what CREATES it). Own
# bucket + own validation branch + own executor, same shape as the social
# types above.
_LISTING_CREATE_STAGED_ACTION_TYPES = ("create_listing",)
# register_product (2026-08-05, catalog reconciliation feature) can't share
# _ETSY_STAGED_ACTION_TYPES either, for the SAME reason create_listing can't
# -- registering a physical product Scott hasn't listed on Etsy yet has no
# listing_id, and _execute_staged_action()'s shared dispatcher unconditionally
# pulls one out of the payload before any type-specific branch runs. Unlike
# every other action type, this one makes ZERO Etsy API calls -- it's a pure
# local write to the two override sidecars (product_catalog_overrides.json +
# listing_manifest_overrides.json), so it doesn't even need EtsyAPIClient.
_REGISTER_PRODUCT_STAGED_ACTION_TYPES = ("register_product",)
_STAGED_ACTION_TYPES = (
    _ETSY_STAGED_ACTION_TYPES + _LOCAL_STAGED_ACTION_TYPES
    + _SCRIPT_STAGED_ACTION_TYPES + _PHOTO_STAGED_ACTION_TYPES
    + _VIDEO_STAGED_ACTION_TYPES + _REGISTER_COMMAND_STAGED_ACTION_TYPES
    + _SOCIAL_STAGED_ACTION_TYPES + _LISTING_CREATE_STAGED_ACTION_TYPES
    + _REGISTER_PRODUCT_STAGED_ACTION_TYPES
)


_EXPECTED_LISTING_PHOTO_SIZE = (2400, 2400)  # CLAUDE.md standard listing photo spec


def _check_no_pale_background(path: Path, category: str = "") -> str | None:
    """Port of QualityGate.check_no_pale_background (business_pipeline.py) — samples the
    4 corners and rejects a washed-out/pale background (CARDINAL CHECK spirit: a listing
    photo that looks AI-blank or low-effort is always wrong). Returns an error message on
    failure, None on pass. Hard block, not a warning -- unlike the dimension check below.

    (2026-07-25) category="coloring_pages" skips this entirely -- a printable
    coloring page is legitimately mostly-white paper by design (that IS the
    real, honest product; not an AI-blank/low-effort render this check exists
    to catch). Confirmed with Scott after COLOR1003's real pack pages hit
    exactly this false-positive rejection when staged as listing photos."""
    if category == "coloring_pages":
        return None
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
            if len(title) > 140:
                return False, f"title is {len(title)} chars — max 140 (Etsy's platform limit)"
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
        if t == "update_price":
            price = p.get("price")
            if not isinstance(price, (int, float)) or isinstance(price, bool):
                return False, "price must be a number (dollars)"
            price = float(price)
            if price < 1.00:
                return False, f"price ${price:.2f} is implausibly low — refusing"
            if price > 500.00:
                return False, f"price ${price:.2f} is implausibly high — refusing"
            cents = round((price * 100) % 100)
            if cents not in (99, 97, 49):
                return False, (
                    f"price ${price:.2f} doesn't end in .99/.97/.49 — required OnBrandCraftz "
                    "pricing convention (CLAUDE.md)"
                )
        if t == "update_description":
            description = p.get("description")
            if not isinstance(description, str) or not description.strip():
                return False, "description is empty"
            if len(description) > 100_000:
                return False, f"description is {len(description)} chars — implausibly long, refusing"
        if t == "update_sku_and_category":
            sku = p.get("sku")
            taxonomy_id = p.get("taxonomy_id")
            if sku is None and taxonomy_id is None:
                return False, "must set at least one of sku or taxonomy_id"
            if sku is not None and (not isinstance(sku, str) or not sku.strip()):
                return False, "sku must be a non-empty string"
            if sku is not None and len(sku) > 100:
                return False, f"sku is {len(sku)} chars — implausibly long, refusing"
            if taxonomy_id is not None and (
                not isinstance(taxonomy_id, int) or isinstance(taxonomy_id, bool) or taxonomy_id <= 0
            ):
                return False, "taxonomy_id must be a positive integer"
        if at_approval:
            try:
                client = EtsyAPIClient()
                current = client.get_listing(int(p["listing_id"]))
            except Exception as exc:
                return False, f"could not reconfirm listing {p['listing_id']} before applying: {exc}"
            staged_state = p.get("_state_at_staging")
            current_state = current.get("state")
            if staged_state is not None and current_state != staged_state:
                return False, (
                    f"listing {p['listing_id']} state changed since this action was staged "
                    f"(was '{staged_state}', now '{current_state}') -- review and re-stage"
                )
            # 2026-08-05 (full-Etsy-audit finding): activation (publish_listing
            # always activates; toggle_listing_state's new_state=="active" does
            # too) previously had zero check that the listing has any photos at
            # all. _execute_create_listing_staged_action already tolerates a
            # partial photo-upload failure (writes the draft override anyway so
            # a real Etsy draft never gets "forgotten" and duplicate-created --
            # see its own docstring), which means a network blip during the
            # original photo upload could leave a listing with ZERO photos,
            # invisible to the "upload_errors" field unless Scott happens to
            # read it before tapping activate. This is the one gate every
            # activation path funnels through, so it's the right place to
            # refuse rather than relying on Scott catching it upstream.
            wants_active = (t == "publish_listing") or (t == "toggle_listing_state" and p.get("new_state") == "active")
            if wants_active:
                try:
                    images = client.get_listing_images(int(p["listing_id"]))
                except Exception as exc:
                    return False, f"could not confirm listing {p['listing_id']} has photos before activating: {exc}"
                if not images:
                    return False, (
                        f"listing {p['listing_id']} has zero photos -- refusing to activate a listing "
                        "with nothing for a buyer to see (a prior upload may have failed silently; "
                        "check upload_errors on the create_listing action, add photos, then retry)"
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
        pale_msg = _check_no_pale_background(target, category=p.get("category", ""))
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
    if t == "create_listing":
        product_id = (p.get("product_id") or "").strip()
        if not product_id:
            return False, "missing product_id"
        listing_data = p.get("listing_data")
        if not isinstance(listing_data, dict):
            return False, "missing listing_data"
        gate_failures = EtsyAPIClient.pre_publish_gate(listing_data)
        if gate_failures:
            return False, "pre-publish gate failed: " + "; ".join(gate_failures)
        photo_paths = p.get("photo_paths") or []
        file_paths = p.get("file_paths") or []
        if not file_paths:
            return False, "no deliverable files to attach"
        # 2026-07-25: photo_paths/file_paths are raw product_catalog.json "files"
        # strings verbatim (see _gather_product_review()'s `"rel": f`), which
        # ALWAYS carry the full "data/digital_products/..." prefix in real
        # catalog data -- confirmed on COLOR1003, but every product's catalog
        # entry has this shape, so this blocked every real publish attempt.
        # _product_file_abs_path() expects a path already relative to
        # _FILE_ROOTS["products"] (prefix stripped) -- joining it with the
        # still-prefixed rel double-nests the path and can never resolve, even
        # though the review endpoint (which correctly uses _catalog_file_abs_
        # path()) just confirmed the exact same file exists. Use the same
        # three-convention-aware resolver here instead of a second hand-rolled
        # check (api-conventions.md: "never re-implement a 'does this file
        # exist' check by hand, it will silently regress one of the three
        # conventions").
        for rel in list(photo_paths) + list(file_paths):
            if _catalog_file_abs_path(rel) is None:
                return False, f"file not found on disk: {rel}"
        if at_approval:
            # Re-confirm no listing exists yet -- guards against a race between
            # staging and approval (e.g. the same product staged twice, or
            # published through some other path in the meantime).
            entry = _find_catalog_product(product_id)
            if entry is None:
                return False, f"product {product_id} no longer exists in the catalog"
            overrides = _product_catalog_overrides()
            # (2026-07-25) _catalog_file_exists, not the older prefix-only
            # _product_file_exists -- this was the last caller still passing
            # the old resolver (harmless here since only listing_id is read,
            # but the COLOR1003 incident showed how these landmines go off).
            current = _build_products_status([entry], _catalog_file_exists, overrides)[0]
            if current.get("listing_id"):
                return False, (
                    f"product {product_id} already has an Etsy listing "
                    f"({current['listing_id']}) — refusing to create a duplicate"
                )
        return True, "ok"
    if t == "register_product":
        product_id = (p.get("product_id") or "").strip()
        if not product_id:
            return False, "missing product_id"
        name = (p.get("name") or "").strip()
        if not name:
            return False, "missing name"
        category = p.get("category")
        if category not in _KNOWN_CATEGORIES:
            return False, f"category must be one of {sorted(_KNOWN_CATEGORIES)}"
        price = p.get("price")
        if price is not None:
            if not isinstance(price, (int, float)) or isinstance(price, bool):
                return False, "price must be a number (dollars)"
            if price < 0:
                return False, f"price ${price:.2f} is negative — refusing"
            if price > 500.00:
                return False, f"price ${price:.2f} is implausibly high — refusing"
        etsy_listing_id = p.get("etsy_listing_id")
        if etsy_listing_id is not None and not str(etsy_listing_id).strip():
            return False, "etsy_listing_id, if provided, must not be blank"
        # Re-checked at both staging and approval time (unlike create_listing's
        # duplicate check, which is approval-only) -- this is a pure local
        # write with no network round trip either way, so there's no reason
        # to defer the check.
        if _find_catalog_product(product_id) is not None:
            return False, f"product_id {product_id} already exists in the catalog — refusing to overwrite"
        if etsy_listing_id is not None:
            existing_entry = _read_manifest_entry_sync(etsy_listing_id)
            if existing_entry:
                return False, (
                    f"Etsy listing {etsy_listing_id} is already mapped to "
                    f"{existing_entry.get('dp_codes')} — refusing to double-register the same listing"
                )
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
    else:
        # 2026-08-05 (full-Etsy-audit finding): every other bucket above
        # (_ETSY_STAGED_ACTION_TYPES, _PHOTO_STAGED_ACTION_TYPES, _VIDEO_
        # STAGED_ACTION_TYPES, _SOCIAL_STAGED_ACTION_TYPES, _LISTING_CREATE_
        # STAGED_ACTION_TYPES, _REGISTER_PRODUCT_STAGED_ACTION_TYPES) returns
        # from its own `if t in <bucket>:` block above, before execution ever
        # reaches here. This local/script/register_command chain was the only
        # one with no such guard -- a type added to _STAGED_ACTION_TYPES (so
        # it passes the top-of-function gate) but never added to any bucket
        # tuple or given its own branch here used to fall all the way through
        # to a bare `return True, "ok"`, validating it with ZERO checks. That
        # is structurally the exact same defect class as the register_product
        # bug this session already found and fixed on the execute side
        # (_execute_staged_action's shared listing_id-extraction assumption)
        # -- a declared-but-not-fully-wired type -- just on the validate side,
        # and dormant only because every current type happens to be fully
        # wired. Fail closed instead: an unrecognized type is refused, not
        # silently approved.
        return False, f"validation not implemented for type: {t}"
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
    elif t == "update_price":
        res = _retry(lambda: client.update_listing(lid, {"price": round(float(p["price"]), 2)}))
    elif t == "update_sku_and_category":
        # One PATCH combining both fields when both are present, not two
        # separate edits -- minimizes edit-count/ranking-signal cost per
        # listing (CLAUDE.md Ranking Recovery Playbook), which matters most
        # here given the SKU/category backfill sweep touches ~170 listings.
        updates = {k: v for k, v in (("sku", p.get("sku")), ("taxonomy_id", p.get("taxonomy_id"))) if v is not None}
        res = _retry(lambda: client.update_listing(lid, updates))
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
    if t in ("update_tags", "update_title", "update_description", "update_price", "update_sku_and_category"):
        # Ranking Recovery cooldown tracker (2026-07-15) — record at EXECUTION
        # time (not staging time), since that's when the content actually
        # changed on Etsy. Read back by db.enqueue_action() to warn against
        # compounding edits inside the ~2-3 week recovery window.
        db.note_listing_edited(lid)
        if t == "update_sku_and_category":
            _mark_backfill_queue_done(lid)
    return {
        "listing_id": lid,
        "etsy": {
            "listing_id": res.get("listing_id"),
            "state": res.get("state"),
            "title": res.get("title"),
        },
    }


def _execute_create_listing_staged_action(a: dict) -> dict:
    """Apply an approved create_listing action -- the one Etsy mutation this
    app has never had a wired path for before (Products-tappable-cards
    feature, 2026-07-18). client.create_listing() already omits `state`, so
    Etsy creates it as a DRAFT (not visible to buyers) -- this deliberately
    does NOT activate it; going live is a separate, deliberate step via the
    already-existing toggle_listing_state action, reusing machinery that's
    already shipped and tested rather than adding a second way to flip a
    listing live.

    If listing creation itself fails, this raises and nothing is recorded --
    no partial state to clean up. If creation succeeds but a photo/file
    upload fails partway through, the override is still written (a real
    draft now exists on Etsy and must not be "forgotten" -- a second
    create_listing attempt would otherwise duplicate it) and the failures
    are returned in upload_errors rather than swallowed."""
    p = a.get("payload", {}) or {}
    product_id = p["product_id"]
    listing_data = p["listing_data"]
    client = EtsyAPIClient()

    response = client.create_listing(listing_data)
    listing_id = response.get("listing_id")
    if not listing_id:
        raise RuntimeError(f"Etsy did not return a listing_id: {response}")

    upload_errors: list[dict] = []
    photo_results: list[dict] = []
    for rank, rel in enumerate(p.get("photo_paths") or [], start=1):
        # Same fix as _validate_staged_action's create_listing branch above
        # (2026-07-25): rel is a raw catalog "files" string, always carrying
        # the "data/digital_products/" prefix -- _catalog_file_abs_path() is
        # the resolver that actually understands it.
        abs_path = _catalog_file_abs_path(rel)
        if abs_path is None:
            upload_errors.append({"file": rel, "error": "file disappeared before upload"})
            continue
        try:
            img = client.upload_listing_image(listing_id, str(abs_path), rank=rank)
            photo_results.append({"file": rel, "listing_image_id": img.get("listing_image_id")})
        except Exception as exc:  # noqa: BLE001
            upload_errors.append({"file": rel, "error": str(exc)[:300]})

    file_results: list[dict] = []
    for rank, rel in enumerate(p.get("file_paths") or [], start=1):
        abs_path = _catalog_file_abs_path(rel)  # same fix as the photo loop above
        if abs_path is None:
            upload_errors.append({"file": rel, "error": "file disappeared before upload"})
            continue
        try:
            f = client.upload_listing_file(listing_id, str(abs_path), rank=rank)
            file_results.append({"file": rel, "listing_file_id": f.get("listing_file_id")})
        except Exception as exc:  # noqa: BLE001
            upload_errors.append({"file": rel, "error": str(exc)[:300]})

    _write_product_catalog_override(product_id, {
        "etsy_listing_id": str(listing_id),
        "status": "listed_draft",
        "published_at": datetime.now(timezone.utc).isoformat(),
    })
    with _cache_lock:
        for k in ("listings_active", "listings_draft", "listings_inactive", "actions", "metrics"):
            _cache.pop(k, None)

    result = {
        "product_id": product_id,
        "etsy_listing_id": listing_id,
        "state": "draft",
        "photos_uploaded": photo_results,
        "files_uploaded": file_results,
        "message": (
            f"Created Etsy listing {listing_id} for {product_id} as a DRAFT. "
            "Review it on Etsy, then activate it with the existing "
            "activate/deactivate action when ready."
        ),
    }
    if upload_errors:
        result["upload_errors"] = upload_errors
        result["message"] += f" {len(upload_errors)} photo/file upload(s) failed — see upload_errors."
    return result


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


# category (product_catalog.json's field) -> type (listing_manifest.json's
# field / listing_rules.json's rule key) -- these DIVERGE for exactly one
# category (digital_planner -> "planner"; confirmed by reading data/
# listing_rules.json's real keys, which has no "digital_planner" entry at
# all). Everything else not listed here maps to itself; audit_listing()
# falls back to a permissive "unknown" rule for anything with no exact
# match (listing_integrity_check.py:663), so an unmapped category here is
# safe, just less-precisely-checked, never a crash.
_CATALOG_CATEGORY_TO_MANIFEST_TYPE = {
    "digital_planner": "planner",
}


def _execute_register_product_staged_action(a: dict) -> dict:
    """Apply an approved register_product action (2026-08-05, catalog
    reconciliation feature) -- a PURE LOCAL write, zero Etsy API calls.
    Writes the full product record to the product_catalog_overrides.json
    sidecar (same one _register_new_product_overlay() already writes for
    Create-screen-built products) AND, when an etsy_listing_id was given, a
    manifest entry to listing_manifest_overrides.json -- closing the exact
    gap that caused the koozie/planner bug: a listing known to only ONE of
    Frank's two local registries still looked "unmapped" to whichever
    call site checked the other one. No manifest entry is written when
    there's no etsy_listing_id yet (a "printed but not listed" physical
    product) -- there's no live listing for request_listing_fix() or the
    compliance sweep to ever diagnose, so nothing to map."""
    p = a.get("payload", {}) or {}
    product_id = p["product_id"]
    category = p["category"]
    etsy_listing_id = p.get("etsy_listing_id")
    now = datetime.now(timezone.utc).isoformat()

    _write_product_catalog_override(product_id, {
        # is_new_product: True is what makes _find_catalog_product() and
        # _build_products_status() recognize an overlay-only entry with no
        # base data/product_catalog.json row at all (same flag
        # _register_new_product_overlay() sets) -- without it this entry is
        # invisible to /api/products, /api/products/{id}/review, and (just
        # as importantly) the duplicate-registration check in this same
        # action's own _validate_staged_action branch above, which relies
        # on _find_catalog_product() to detect a re-registration.
        "is_new_product": True,
        "product_id": product_id,
        "name": p["name"],
        "category": category,
        "price": p.get("price"),
        "status": "active" if etsy_listing_id else "not_listed",
        "etsy_listing_id": str(etsy_listing_id) if etsy_listing_id else "",
        "files": [],
        "created_at": now,
        "source": "frank_register",
    })

    manifest_written = False
    if etsy_listing_id:
        manifest_type = _CATALOG_CATEGORY_TO_MANIFEST_TYPE.get(category, category)
        _write_listing_manifest_override(etsy_listing_id, {
            "dp_codes": [product_id],
            "type": manifest_type,
            "expected_file_count": 0,
            "expected_files": [],
            "min_photo_count": 1,
            "art_hashes": {},
            "art_sources": {},
            "listing_roles": {product_id: "listing_id"},
            "baseline_captured": now,
            "baseline_source": "register_product_staged_action",
        })
        manifest_written = True

    with _cache_lock:
        for k in ("products", "listings_active", "listings_draft", "listings_inactive", "actions"):
            _cache.pop(k, None)

    return {
        "product_id": product_id,
        "category": category,
        "etsy_listing_id": str(etsy_listing_id) if etsy_listing_id else None,
        "manifest_entry_written": manifest_written,
        "message": (
            f"Registered {product_id} ({category}) into Frank's catalog"
            + (f", mapped to live listing {etsy_listing_id}." if etsy_listing_id
               else " with no Etsy listing yet -- map it once it's actually listed.")
        ),
    }


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
    is_create_listing = a["type"] in _LISTING_CREATE_STAGED_ACTION_TYPES
    is_register_product = a["type"] in _REGISTER_PRODUCT_STAGED_ACTION_TYPES
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
        elif is_create_listing:
            # Longer timeout than every other type -- this uploads up to 10
            # photos + 3 deliverable files sequentially over the network,
            # not a single PATCH.
            result = await asyncio.wait_for(
                asyncio.to_thread(_execute_create_listing_staged_action, a), timeout=180.0
            )
        elif is_register_product:
            # Pure local write, no network call -- short timeout is plenty.
            result = await asyncio.wait_for(
                asyncio.to_thread(_execute_register_product_staged_action, a), timeout=15.0
            )
        else:
            result = await asyncio.wait_for(asyncio.to_thread(_execute_staged_action, a), timeout=45.0)
    except Exception as exc:
        await asyncio.to_thread(db.set_action_status, action_id, "failed", {"error": str(exc)})
        raise HTTPException(status_code=502, detail=f"execution failed: {str(exc)[:200]}")
    await asyncio.to_thread(db.set_action_status, action_id, "executed", result)
    ab_test_id = (a.get("payload") or {}).get("ab_test_id")
    if ab_test_id:
        # Best-effort -- the real Etsy title change above already succeeded and
        # must be reported regardless of whether this bookkeeping step works.
        try:
            await asyncio.to_thread(_advance_ab_test, ab_test_id, a["payload"].get("title", ""))
        except Exception as exc:
            print(f"[ab-test] _advance_ab_test failed for test {ab_test_id}: {exc}", flush=True)
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
    ab_test_id = (a.get("payload") or {}).get("ab_test_id")
    if ab_test_id:
        # A rejected Variant-B swap can't sit forever in "awaiting_approval_b"
        # with no path forward -- close the test out honestly instead.
        await asyncio.to_thread(_cancel_ab_test_for_rejected_action, ab_test_id, reason)
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
            # Every type other than update_title/update_tags/update_description/
            # publish_listing above -- local_write_file, local_delete, local_exec,
            # run_script, deactivate_listing, toggle_listing_state, update_price,
            # update_sku_and_category, register_product, create_listing,
            # listing_video, post_tiktok, post_pinterest, register_command.
            # 2026-08-05 (full-Etsy-audit finding): this comment used to name
            # only the original 5 types, which drifted stale as 9 more staged-
            # action types were added since -- corrected to describe the actual
            # current behavior rather than a fixed enumeration that will only
            # drift again. None of these has an _autofix_*_core-style regenerator
            # a rejection reason could plausibly retry against; the reason is
            # already recorded on the rejected action above.
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
    category: str = "",
) -> int:
    """Validate and enqueue a listing_photo staged action. rel_path is relative to the
    staged_photos root (e.g. 'P3D_SCULPTURAL_MESH_LAMP/photo_ab12cd34.jpg').

    category (2026-07-25): threaded through to _validate_staged_action's
    pale-background check, which is category-aware (coloring_pages skips it --
    see _check_no_pale_background's docstring). Omit for every other product
    type -- the check applies normally."""
    payload = {
        "listing_id": listing_id,
        "rank": rank,
        "path": rel_path,
        "sku": sku,
        "physics": physics,
        "scene_prompt": scene_prompt,
        "design_paths": design_paths,
    }
    if category:
        payload["category"] = category
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
    out_path = out_dir / f"photo_{uuid.uuid4().hex[:8]}.jpg"

    # (2026-07-25) Up to _MAX_UPLOAD_BYTES (30 MB) written synchronously to
    # the network volume, previously inline on the event loop -- blocks every
    # other request while it runs. Same _write()+to_thread shape as
    # upload_to_volume below; the rollback unlink goes off-loop too.
    def _write() -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(body)

    await asyncio.to_thread(_write)

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
        await asyncio.to_thread(lambda: out_path.unlink(missing_ok=True))
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
    out_path = out_dir / f"video_{uuid.uuid4().hex[:8]}.mp4"

    # (2026-07-25) Same off-loop write as stage_photo above -- a 30 MB video
    # written synchronously on the event loop blocked every other request.
    def _write() -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(body)

    await asyncio.to_thread(_write)

    try:
        action_id = await _stage_video_action(
            listing_id=listing_id,
            rel_path=f"{listing_id}/{out_path.name}",
            summary=summary or f"Staged video for listing {listing_id}",
            rank=rank,
        )
    except ValueError as exc:
        await asyncio.to_thread(lambda: out_path.unlink(missing_ok=True))
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


# ── Reference Photos library (2026-07-22 Create-screen redesign) ──────────────────
# Scott's own inspiration/style-reference images (photos he took, screenshots,
# Pinterest finds), organized by product category for browsing. Originally scoped
# to upload + organize + browse + delete only, with nothing wired into an AI
# generation call. Wall Art's "new one" flow started using this on 2026-07-30
# (_reference_image_style_notes() below, folded into the wall_art branch of
# _produce_build_product()) -- other categories are still library-only until
# their generators support the same style-guidance distinction.


@app.post("/api/reference-images/upload")
async def upload_reference_image(
    request: Request, filename: str, category: str = "general", description: str = "",
    _token: str = Depends(_auth_session_or_bearer),
):
    """Accept a raw image body for the Reference Photos library. Same raw-body
    convention and PIL-decode validation as studio_upload_image above (blocks
    non-images and the SVG-with-<script> XSS vector) — no AI cost, so the
    plain auth dependency is enough, not the rate-limited one AI-spending
    routes use."""
    safe_name = os.path.basename((filename or "").strip())
    if not safe_name:
        raise HTTPException(status_code=400, detail="filename query param is required")
    cat = (category or "general").strip().lower()
    if cat not in _REFERENCE_IMAGE_CATEGORIES:
        cat = "general"
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="empty body")
    if len(body) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {_human_size(_MAX_UPLOAD_BYTES)} limit")

    from PIL import Image

    def _validate_and_store() -> tuple[str, int]:
        Image.open(io.BytesIO(body)).load()
        root = _FILE_ROOTS["reference_images"]
        root.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        (root / stored_name).write_bytes(body)
        return stored_name, len(body)

    try:
        stored_name, size = await asyncio.to_thread(_validate_and_store)
    except Exception:
        raise HTTPException(status_code=400, detail="not a readable image")

    entry = {
        "id": uuid.uuid4().hex[:12],
        "filename": stored_name,
        "category": cat,
        "description": (description or "").strip()[:300],
        "size": size,
        "size_human": _human_size(size),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

    def _append_meta() -> None:
        entries = _reference_images_meta()
        entries.insert(0, entry)
        _write_reference_images_meta(entries)

    await asyncio.to_thread(_append_meta)
    return entry


@app.get("/api/reference-images")
async def list_reference_images(category: str = "", _token: str = Depends(_auth_session_or_bearer)):
    """Browse the Reference Photos library, newest first. `category` filters
    server-side (the frontend also filters client-side via chips, same
    pattern as Products/Tasks — this param just saves a round-trip)."""
    entries = await asyncio.to_thread(_reference_images_meta)
    cat = category.strip().lower()
    if cat:
        entries = [e for e in entries if e.get("category") == cat]
    return {"images": entries, "categories": sorted(_REFERENCE_IMAGE_CATEGORIES)}


@app.delete("/api/reference-images/{ref_id}")
async def delete_reference_image(ref_id: str, _token: str = Depends(_auth_session_or_bearer)):
    """Remove a reference image — both the stored file and its metadata entry."""
    def _remove() -> bool:
        entries = _reference_images_meta()
        match = next((e for e in entries if e.get("id") == ref_id), None)
        if match is None:
            return False
        remaining = [e for e in entries if e.get("id") != ref_id]
        _write_reference_images_meta(remaining)
        try:
            (_FILE_ROOTS["reference_images"] / os.path.basename(match["filename"])).unlink(missing_ok=True)
        except OSError:
            pass
        return True

    removed = await asyncio.to_thread(_remove)
    if not removed:
        raise HTTPException(status_code=404, detail="reference image not found")
    return {"ok": True, "id": ref_id}


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
    out_name = f"{uuid.uuid4().hex[:8]}_{mode}.svg"

    def _save() -> None:
        root.mkdir(parents=True, exist_ok=True)
        (root / out_name).write_text(svg_text, encoding="utf-8")

    await asyncio.to_thread(_save)

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
    engine = (body.get("engine") or "").strip().lower() or None
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
    if engine == "ideogram":
        # This is an edit-style call (real product file(s) as input) -- Ideogram is
        # generate-only and cannot do edit/input-image calls at all (see
        # image_gen.edit_image()'s own error for the same case). Fail fast here with
        # a clear message instead of letting it surface as a generic 500 partway
        # through generation.
        raise HTTPException(status_code=400, detail="engine='ideogram' can't be used here — it has no image-edit mode. Choose Standard, gpt-image-2, or Gemini.")

    design_paths = []
    for n in design_names:
        p = _resolve_in_root("studio_uploads", n)
        if not p.is_file():
            raise HTTPException(status_code=400, detail=f"uploaded file not found: {n}")
        design_paths.append(p)

    out_root = _FILE_ROOTS["lifestyle_photos"]
    await asyncio.to_thread(lambda: out_root.mkdir(parents=True, exist_ok=True))
    out_name = f"{uuid.uuid4().hex[:8]}_lifestyle.jpg"
    out_path = out_root / out_name

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                listing_photo_pipeline.generate_verified_photo,
                design_paths, scene_prompt, out_path, category, max_attempts, None, engine,
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
    # 2026-07-31 (Create UX audit): a missing API key (ImageGenError's "...API_KEY
    # not set..." message, image_gen.py) previously fell into the generic
    # "generation error:" bucket below and rendered as "temporary error, try again"
    # -- false, since retrying with no key configured fails identically forever.
    # goal_loop.run_until_goal() has no distinct exception type for this (a single
    # flat ImageGenError covers both config and transient failures), but the
    # message text is a unique, greppable signature used only for missing-key
    # cases anywhere in the codebase -- a substring check is a safe, low-risk fix.
    _config = _issues and any("_API_KEY not set" in str(i) for i in _issues)
    _svc = _issues and all(
        str(i).startswith(("generation error:", "verification error:")) for i in _issues
    )
    failure_kind = None if result.passed else ("config_error" if _config else ("service_error" if _svc else "mismatch"))

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


_MAX_COLORING_LISTING_PHOTOS = 10  # Etsy's hard per-listing photo cap


def _extract_coloring_page_images(zip_path: Path, n: int) -> list[tuple[str, bytes]]:
    """Pick up to n individual page images straight from a coloring-pages
    product ZIP -- the exact "root-level PNG" file definition qc_sweep.
    coloring_zip_page_count() already uses (reused here, not re-derived).
    When the pack has more than n pages, samples n evenly across the whole
    set (not just the first n) so the listing photos represent the full
    pack. Returns (filename, bytes) pairs in page order."""
    with zipfile.ZipFile(zip_path) as zf:
        names = sorted(nm for nm in zf.namelist() if nm.lower().endswith(".png") and "/" not in nm)
        if len(names) > n:
            step = len(names) / n
            names = [names[int(i * step)] for i in range(n)]
        return [(name, zf.read(name)) for name in names]


def _produce_coloring_pages_listing_photos(pid: str) -> dict:
    """Stage up to _MAX_COLORING_LISTING_PHOTOS real individual coloring
    pages -- straight from the product's own delivered ZIP, the exact files
    the customer receives, never an AI-generated stand-in -- as this
    product's Etsy listing photos. Added 2026-07-25 after COLOR1003
    published with zero listing photos (coloring_pages has no AI photo
    pipeline like digital_planner's) -- Scott's direct instruction was to
    use the real pack images rather than build a lifestyle-photo pipeline.

    Requires the product to already have a real Etsy listing_id (there must
    be a listing to stage photos against) -- publish first via the Products
    review modal, then run this."""
    entry = _find_catalog_product(pid)
    if entry is None:
        return {"error": f"unknown product_id: {pid}"}
    if entry.get("category") != "coloring_pages":
        return {"error": f"{pid} is category '{entry.get('category')}', not coloring_pages"}

    review = _gather_product_review(pid)
    listing_id = review.get("listing_id") if review else None
    if not listing_id:
        return {"error": f"{pid} has no Etsy listing yet — publish it first, then stage photos"}

    zip_entry = next((f for f in (entry.get("files") or [])
                       if f.lower().endswith(".zip") and "_listing_images/" not in f), None)
    if zip_entry is None:
        return {"error": f"no coloring-pages ZIP found in {pid}'s catalog files"}
    zip_path = _catalog_file_abs_path(zip_entry)
    if zip_path is None:
        return {"error": f"coloring-pages ZIP not found on disk: {zip_entry}"}

    pages = _extract_coloring_page_images(zip_path, _MAX_COLORING_LISTING_PHOTOS)
    if not pages:
        return {"error": f"no individual page PNGs found in {zip_path.name}"}

    staged_root = _FILE_ROOTS["staged_photos"] / pid
    staged_root.mkdir(parents=True, exist_ok=True)
    staged: list[dict] = []
    stage_errors: list[dict] = []
    for rank, (name, data) in enumerate(pages, start=1):
        dest_name = f"page_{rank:02d}.png"
        (staged_root / dest_name).write_bytes(data)
        try:
            # asyncio.run here is safe ONLY because this sync function always
            # runs off the event loop (dispatched via asyncio.to_thread), so
            # it spins a fresh loop on the worker thread. It would deadlock/
            # break if _stage_photo_action ever awaited something bound to
            # the main server loop (today it only awaits its own to_thread).
            action_id = asyncio.run(_stage_photo_action(
                listing_id=listing_id, rank=rank, sku=pid,
                rel_path=f"{pid}/{dest_name}",
                summary=f"Coloring page {rank}/{len(pages)} listing photo: {pid} (from {Path(name).name})",
                physics="", scene_prompt="", design_paths=[zip_entry],
                category="coloring_pages",
            ))
            staged.append({"rank": rank, "action_id": action_id, "source": name})
        except Exception as exc:  # noqa: BLE001
            stage_errors.append({"rank": rank, "source": name, "error": str(exc)[:200]})

    message = (
        f"Staged {len(staged)}/{len(pages)} real coloring-page photos for {pid}'s Etsy listing "
        f"(#{listing_id}) — review and approve in the Action Center."
    )
    if stage_errors:
        message += f" {len(stage_errors)} failed to stage — see errors."
    return {
        "pid": pid, "listing_id": listing_id, "staged": staged,
        "errors": stage_errors, "message": message,
    }


def _produce_listing_photos(inp: dict) -> dict:
    """Generate a planner's full 10-photo listing set — real, self-verifying
    AI-rendered lifestyle photos via tools/listing_photo_pipeline.py (THE
    STANDARD LIFESTYLE METHOD documented in CLAUDE.md), not a plain local
    render. Rewritten 2026-07-17 (Wave 4 photo-pipeline audit): the previous
    version (gen_planner_listing_photos.generate_for_planner()) never called
    an AI image model at all — a hand-drawn iPad bezel composited onto a flat
    gradient, no real photography — which is the actual root cause behind
    "photos look AI-generated / not convincing": there was no photorealistic
    rendering happening, at all, for the shop's core product line.

    If the product already has a live/draft Etsy listing_id (gen_planner_
    listing_photos.PLANNER_PAGES[pid]['listing_id']), each passed photo is
    staged into the Action Center for one-tap approval, exactly like the
    SS-series photo path already does — closing the "zero automated QA gate
    on the photos Scott actually looks at" gap the same audit found. Products
    with no listing_id yet (e.g. DP1030-1034, still pre-publish drafts) have
    nowhere to stage a photo update TO, so those fall back to the existing
    Files-screen folder-drop UX unchanged.

    coloring_pages (2026-07-25): delegates entirely to
    _produce_coloring_pages_listing_photos() -- real pack pages, not an AI
    render, since this pipeline (below) is planner-specific."""
    pid = str((inp or {}).get("pid", "")).strip().upper()
    if not pid:
        return {"error": "pid is required (e.g. 'DP1030')"}
    entry = _find_catalog_product(pid)
    if entry and entry.get("category") == "coloring_pages":
        return _produce_coloring_pages_listing_photos(pid)
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
        out_dir, photos = glp.generate_ai_photos_for_planner(pid, engine=engine)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"photo generation failed: {exc}"}

    passed = [p for p in photos if p["passed"]]
    failed = [p for p in photos if not p["passed"]]
    realism_flags = [p for p in photos if p.get("realism_issues")]

    listing_id = glp.PLANNER_PAGES[pid].get("listing_id")
    staged: list[dict] = []
    stage_errors: list[dict] = []
    if listing_id and passed:
        staged_root = _FILE_ROOTS["staged_photos"] / pid
        staged_root.mkdir(parents=True, exist_ok=True)
        for rank, p in enumerate(photos, start=1):
            if not p["passed"]:
                continue
            src = _P(out_dir) / p["filename"]
            dest = staged_root / p["filename"]
            try:
                shutil.copy2(src, dest)
                summary = f"AI listing photo {rank}/10 ({p['slot']}): {pid}"
                if p.get("realism_issues"):
                    summary += " ⚠ realism notes"
                # Same asyncio.run-on-a-worker-thread caveat as
                # _produce_coloring_pages_listing_photos above.
                action_id = asyncio.run(_stage_photo_action(
                    listing_id=listing_id, rank=rank, sku=pid,
                    rel_path=f"{pid}/{p['filename']}", summary=summary,
                    physics=p.get("physics", ""), scene_prompt=p.get("scene_prompt", ""),
                    design_paths=p.get("design_paths", []),
                ))
                staged.append({"slot": p["slot"], "rank": rank, "action_id": action_id})
            except Exception as exc:  # noqa: BLE001
                stage_errors.append({"slot": p["slot"], "error": str(exc)[:200]})

    if staged:
        message = (
            f"Generated {len(passed)}/10 listing photos for {pid} and staged "
            f"{len(staged)} for your approval in the Action Center."
        )
    else:
        message = (
            f"Generated {len(passed)}/10 listing photos for {pid} → "
            f"{pid}_listing_images/. Open them from the Files screen."
        )
        if not listing_id:
            message += " (No Etsy listing_id yet for this product — nothing to stage against.)"
    if failed:
        message += f" {len(failed)} slot(s) failed verification — see 'failed' below."
    if realism_flags:
        message += f" {len(realism_flags)} photo(s) have non-blocking realism notes — see 'realism_flags'."

    return {
        "pid": pid,
        "count": len(passed),
        "photos": photos,
        "failed": failed,
        "realism_flags": realism_flags,
        "staged": staged,
        "stage_errors": stage_errors,
        "engine": engine,
        "folder": f"product_files/{pid}_listing_images",
        "message": message,
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


_OPENSCAD_OUTPUT_SUBDIR = "openscad_models"  # under _product_log_dir()'s base, alongside product_files/


def _produce_openscad_render(inp: dict) -> dict:
    """Render Claude-authored OpenSCAD source to a real mesh file (2026-08-14,
    render_openscad_model chat tool). Synchronous and can take a while on a
    complex script -- callers awaiting this via the HTTP route wrap it with
    a timeout, same pattern as _produce_print_zip above. Zero AI/API cost;
    the only external dependency is the openscad system binary, which
    openscad_render.check_openscad_available() reports on clearly rather
    than this failing with a bare subprocess error."""
    scad_source = str((inp or {}).get("scad_source", "")).strip()
    if not scad_source:
        return {"error": "scad_source is required — write the OpenSCAD script to render."}
    output_name = str((inp or {}).get("output_name", "")).strip()
    if not output_name:
        return {"error": "output_name is required (no extension, e.g. 'desk_organizer_v1')."}
    fmt = str((inp or {}).get("format", "stl")).strip().lower().lstrip(".")
    params = (inp or {}).get("params") or {}
    if not isinstance(params, dict):
        return {"error": "params must be an object of variable_name: value pairs."}

    try:
        import openscad_render as osr
    except Exception as exc:  # noqa: BLE001
        return {"error": f"openscad_render module unavailable: {exc}"}

    available, info = osr.check_openscad_available()
    if not available:
        return {"error": info}

    safe_name = _re.sub(r"[^A-Za-z0-9_-]", "_", output_name)[:80] or "model"
    out_dir = _product_log_dir().parent / _OPENSCAD_OUTPUT_SUBDIR
    output_path = out_dir / f"{safe_name}.{fmt}"
    try:
        osr.render_scad(scad_source, output_path, params={k: str(v) for k, v in params.items()}, fmt=fmt)
    except osr.OpenSCADError as exc:
        return {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"render failed: {exc}"}

    size_kb = round(output_path.stat().st_size / 1024, 1)
    return {
        "output_name": safe_name,
        "format": fmt,
        "path": f"{_OPENSCAD_OUTPUT_SUBDIR}/{safe_name}.{fmt}",
        "size_kb": size_kb,
        "message": f"Rendered {safe_name}.{fmt} ({size_kb} KB) — open it from the Files screen. "
                   f"Register it with stage_action (register_product, category="
                   f"'3d_print_physical') once Scott's confirmed it prints correctly.",
    }


@app.post("/api/produce/openscad-render")
async def produce_openscad_render(body: dict, _token: str = Depends(_rate_limited_auth)):
    """Render OpenSCAD source to a mesh file. Local subprocess only, no AI/API
    cost — timeout matches openscad_render.render_scad's own default plus
    a small margin for process overhead."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_produce_openscad_render, body or {}), timeout=140)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="OpenSCAD render timed out — try a lower-resolution script.")


def _produce_coloring_pack(inp: dict) -> dict:
    """Kick off a coloring_pages product's ZIP-set rebuild in the BACKGROUND via
    generate_coloring_pages.py --pack <pack>. Determines which of the two theme
    packs ('kawaii' vs 'fun_basic') to use from the product's OWN catalog filename
    convention (e.g. 'coloring_set_05.zip' -> kawaii, 'coloring_fun_basic_set_02.zip'
    -> fun_basic) so the caller never has to know that mapping. Long-running like
    the planner/sticker builds above (up to 20 gpt-image-1 calls for anything not
    already cached on disk -- generate_coloring_page() skips a theme's PNG if it
    already exists, so rebuilding one missing set doesn't re-pay for the other 19),
    so it runs detached the same way; the finished ZIPs show up in Files."""
    pid = str((inp or {}).get("pid", "")).strip().upper()
    if not pid:
        return {"error": "pid is required (e.g. 'COLOR_KAWAII_COLORING_PAGES_SET_05')"}
    try:
        catalog = json.loads(Path("data/product_catalog.json").read_text())
    except OSError:
        catalog = []
    entry = next((e for e in catalog if e.get("product_id") == pid), None)
    if entry is None:
        return {"error": f"{pid} not found in the catalog"}
    files = entry.get("files") or []
    if not files:
        return {"error": f"{pid} has no files listed in the catalog to infer a theme pack from"}
    pack = "fun_basic" if files[0].startswith("coloring_fun_basic_set_") else "kawaii"
    script = ROOT / "tools" / "generate_coloring_pages.py"
    if not script.exists():
        return {"error": "generate_coloring_pages.py is missing from this deploy."}
    from pathlib import Path as _P
    try:
        base = _P(os.getenv("HUB_FILES_DIR", "").strip()
                  or ("/data/files" if _P("/data/files").is_dir()
                      else str(ROOT / "data" / "digital_products")))
        logdir = base / "product_files"
        logdir.mkdir(parents=True, exist_ok=True)
        _logf = open(logdir / f"{pid}_coloring_build.log", "w")  # noqa: SIM115 — handed to Popen
    except Exception:  # noqa: BLE001
        _logf = subprocess.DEVNULL
    proc = subprocess.Popen(
        [sys.executable, str(script), "--pack", pack],
        stdout=_logf, stderr=subprocess.STDOUT, cwd=str(ROOT),
    )
    _LONG_RUNNING_PROCS[proc.pid] = (proc, f"build_coloring_pack:{pid}", datetime.now(timezone.utc))
    return {
        "pid": pid,
        "started": True,
        "os_pid": proc.pid,
        "pack": pack,
        "message": f"Rebuilding the '{pack}' coloring pack in the background (only uncached "
                   f"pages cost an AI call). When it finishes, the ZIP sets appear in Files "
                   f"({pid}_coloring_build.log has the run output).",
    }


@app.post("/api/produce/coloring-pack")
async def produce_coloring_pack(body: dict, _token: str = Depends(_rate_limited_auth)):
    """Kick off a coloring-pages product's ZIP-set rebuild in the background.
    Returns immediately; the ZIPs appear in Files when done."""
    return await asyncio.to_thread(_produce_coloring_pack, body or {})


def _register_prepublish_coloring_listing_images(pid: str, zip_path: Path) -> list[str]:
    """Sample real pages straight from a coloring-pages product's own
    delivered ZIP (never an AI stand-in) and register them into the
    catalog's `files` list BEFORE the listing is ever published -- so
    stage_product_publish()'s photo_paths (built from review["photos"],
    which reads catalog `files` entries containing "_listing_images/") picks
    them up automatically, and _execute_create_listing_staged_action()
    uploads them to Etsy in the SAME approval as the listing draft itself.
    No separate post-publish photo-staging round needed (2026-08-11, Scott:
    "make it so the photos are in there when the listing goes into drafts so
    we don't have to do work more than once").

    Distinct from _produce_coloring_pages_listing_photos() (which stages
    individual listing_photo actions against an ALREADY-LIVE listing_id, for
    refreshing photos on a listing that already exists) -- this one runs
    pre-publish, writing files + a catalog registration instead of staged
    actions. Returns the list of registered catalog paths (empty if the ZIP
    had no page images to sample)."""
    pages = _extract_coloring_page_images(zip_path, _MAX_COLORING_LISTING_PHOTOS)
    if not pages:
        return []
    img_dir = _product_log_dir() / f"{pid}_listing_images"
    img_dir.mkdir(parents=True, exist_ok=True)
    registered: list[str] = []
    for rank, (_name, data) in enumerate(pages, start=1):
        dest_name = f"page_{rank:02d}.png"
        (img_dir / dest_name).write_bytes(data)
        registered.append(f"data/digital_products/product_files/{pid}_listing_images/{dest_name}")
    entry = _find_catalog_product(pid) or {}
    existing_files = list(entry.get("files") or [])
    _write_product_catalog_override(pid, {"files": existing_files + registered})
    return registered


def _register_prepublish_calendar_listing_images(pid: str, zip_path: Path) -> list[str]:
    """WC-series analog of _register_prepublish_coloring_listing_images():
    pulls the real year-at-a-glance poster JPG straight out of the
    product's own delivered ZIP (never an AI stand-in) and registers it as
    this product's first listing photo before publish is ever staged, so it
    uploads in the same create_listing approval as the draft itself.

    Only registers the ONE real deliverable preview -- the remaining
    lifestyle-room photo slots (hero-on-wall, gallery grouping, etc.) still
    need the standard AI-photo pipeline, same as wall_art's existing "no
    lifestyle photos in the one-tap build" precedent (see _produce_build_
    product()'s own docstring) -- this just avoids leaving the listing at
    literally zero photos in the meantime."""
    try:
        with zipfile.ZipFile(zip_path) as zf:
            poster_name = next((n for n in zf.namelist() if "yearglance" in n.lower()
                                 and n.lower().endswith((".jpg", ".jpeg"))), None)
            if poster_name is None:
                return []
            poster_bytes = zf.read(poster_name)
    except (OSError, zipfile.BadZipFile):
        return []

    img_dir = _product_log_dir() / f"{pid}_listing_images"
    img_dir.mkdir(parents=True, exist_ok=True)
    dest_name = "photo_01_yearglance.jpg"
    (img_dir / dest_name).write_bytes(poster_bytes)
    registered = [f"data/digital_products/product_files/{pid}_listing_images/{dest_name}"]

    entry = _find_catalog_product(pid) or {}
    existing_files = list(entry.get("files") or [])
    _write_product_catalog_override(pid, {"files": existing_files + registered})
    return registered


def _produce_coloring_bundle(inp: dict) -> dict:
    """Combine several EXISTING coloring-pages products' real, already-
    generated ZIPs into one new bundle product's ZIP — zero AI spend, pure
    repackaging (2026-08-10, cost-effective-scale request). Synchronous and
    fast (disk I/O only, no subprocess) unlike the AI-generation produce
    endpoints above. See generate_coloring_pages.merge_existing_sets_into_
    bundle()'s docstring for the merge mechanics and why only new-pipeline
    (COLOR100x) sources are reachable — older pre-volume-fix products' source
    files were never migrated and aren't present to merge."""
    source_pids = (inp or {}).get("source_pids")
    if not isinstance(source_pids, list) or len(source_pids) < 2:
        return {"error": "source_pids must be a list of at least 2 existing coloring-pages product IDs"}
    source_pids = [str(p).strip().upper() for p in source_pids if str(p).strip()]
    description = str((inp or {}).get("description", "")).strip()
    if not description:
        return {"error": "description is required (short name for the new bundle product)"}
    bundle_pid = str((inp or {}).get("pid", "")).strip().upper()
    if not bundle_pid:
        bundle_pid = _next_coloring_pid()
    if _find_catalog_product(bundle_pid) is not None:
        return {"error": f"{bundle_pid} already exists in the catalog — pick a different pid"}

    import generate_coloring_pages as _gcp
    result = _gcp.merge_existing_sets_into_bundle(source_pids, bundle_pid)
    if result["total_pages"] == 0:
        return {"error": f"none of the requested source pids had a reachable ZIP on this deploy's "
                          f"volume: {', '.join(result['missing'])}"}

    rel_path = f"data/digital_products/coloring_pages/sets/coloring_{bundle_pid.lower()}_set_01.zip"
    _register_new_product_overlay(bundle_pid, "coloring_pages", description, None, [rel_path], description)

    photos_registered = _register_prepublish_coloring_listing_images(bundle_pid, result["zip_path"])

    missing_note = f" Could not find a ZIP for: {', '.join(result['missing'])}." if result["missing"] else ""
    photo_note = (f" {len(photos_registered)} listing photos pre-registered — they'll upload "
                  f"automatically with the listing draft, no separate staging step needed."
                  if photos_registered else " (no page images found to use as listing photos)")
    return {
        "pid": bundle_pid,
        "status": "merged",
        "zip": rel_path,
        "included": result["included"],
        "missing": result["missing"],
        "total_pages": result["total_pages"],
        "photos_registered": len(photos_registered),
        "message": f"Combined {len(result['included'])} existing product(s) into {result['total_pages']} "
                   f"real pages for {bundle_pid} — zero new AI spend.{missing_note}{photo_note} "
                   f"Open Products to author listing content and stage for review.",
    }


@app.post("/api/produce/coloring-bundle")
async def produce_coloring_bundle(body: dict, _token: str = Depends(_rate_limited_auth)):
    """Merge several existing coloring-pages products' real ZIPs into one new
    bundle listing's ZIP. Fast and synchronous (no background job) — see
    _produce_coloring_bundle()'s docstring."""
    return await asyncio.to_thread(_produce_coloring_bundle, body or {})


# Approved image engines (mirrors tools/image_gen.py's engine dispatch). Single
# source of truth for BOTH the produce-builders' engine validation below and
# the /api/settings image_engine validation further down this file (see
# _IMAGE_ENGINES = _APPROVED_ART_ENGINES) -- these were two separately-defined,
# unlinked tuples that happened to just be reordered copies of each other until
# 2026-08-05 (adding Grok surfaced the duplication; consolidated rather than
# adding a 5th engine to two places by hand). Gemini ("Nano Banana") is the
# default for the produce builders: it needs only GEMINI_API_KEY (no OpenAI
# dependency — and gpt-image-1 shuts down 2026-10-23), and is a fully approved
# engine per CLAUDE.md. gpt-image-2 / ideogram / grok remain selectable.
_APPROVED_ART_ENGINES = ("gemini", "openai", "gpt-image-2", "ideogram", "grok")
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


def _product_log_dir() -> Path:
    """Where a background build's log file (and other per-product artifacts)
    live: the persistent Railway volume's files dir when mounted, else the
    local data/digital_products dir. Extracted 2026-07-22 from 3 near-identical
    inline copies in _produce_build_planner/_produce_build_sticker_pack/
    _produce_build_product so the new GET /api/produce/status endpoint has one
    place to resolve the same path instead of a 4th copy."""
    base = Path(os.getenv("HUB_FILES_DIR", "").strip()
                or ("/data/files" if Path("/data/files").is_dir()
                    else str(ROOT / "data" / "digital_products")))
    logdir = base / "product_files"
    logdir.mkdir(parents=True, exist_ok=True)
    return logdir


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
    log_file = f"{pid}_build.log"
    try:
        _logf = open(_product_log_dir() / log_file, "w")  # noqa: SIM115 — handed to Popen
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
        "log_file": log_file,
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
    log_file = f"{pid}_stickers_build.log"
    try:
        _logf = open(_product_log_dir() / log_file, "w")  # noqa: SIM115 — handed to Popen
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
        "log_file": log_file,
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


def _resolve_build_category(pid: str, explicit: str | None) -> str:
    """category param if given, else looked up from product_catalog.json by pid,
    else falls back to 'digital_planner' (the pre-2026-07-18 default, so an
    unrecognized/uncataloged pid keeps behaving exactly like it always did)."""
    if explicit:
        return explicit
    try:
        catalog = json.loads(Path("data/product_catalog.json").read_text())
    except OSError:
        catalog = []
    entry = next((e for e in catalog if e.get("product_id") == pid), None)
    return (entry or {}).get("category") or "digital_planner"


def _produce_build_product(inp: dict) -> dict:
    """Kick off a FULL product build in the BACKGROUND. Dispatches by category
    (2026-07-18: generalized from the original digital-planner-only flow, per
    Scott's ask to have a one-tap build for other listing types too) --
    resolved from the explicit `category` field if given, else looked up from
    product_catalog.json by pid:

      digital_planner: stickers → planner PDFs → 10 listing photos → QC
                        (tools/build_product.py — unchanged from before).
      wall_art / wall_art_bundle: multi-size print ZIP → QC
                        (tools/build_wallart_product.py — no lifestyle photos
                        in this one-tap flow, see its own docstring for why).
      coloring_pages: coloring pages + ZIP sets → QC
                        (tools/build_coloring_product.py — same photos caveat).

    Every other category has no verified generator wired yet (2026-07-18
    scoping decision) and returns a clear error rather than silently doing
    nothing or guessing. Publishing always stays Scott-gated regardless of
    category — this only produces + QCs the files.

    Same honesty guard as the sticker builder (top rule — NEVER LIE): planner
    builds return needs_visual_qc:true (AI can garble in-image text, which no
    file gate catches) — wall_art/coloring_pages don't generate new AI art in
    this flow UNLESS a `description` is supplied for a genuinely new pid with
    no existing art/catalog entry (2026-07-22, see below), in which case the
    same honesty flag applies to them too.

    (2026-07-22) A genuinely new wall_art/coloring_pages pid with no existing
    source art / catalog entry can now actually be BUILT, not just cleanly
    rejected: pass `description` (free text describing the art) and this
    generates real new art via the same approved-engine pipeline every other
    AI image call in this app uses, before continuing into the existing
    build chain. On a clean exit, a background watcher thread durably
    registers the new product (as a `status: "draft"`, never auto-published)
    so it shows up in Products for review -- see _register_new_product_overlay().

    (2026-07-24) For coloring_pages specifically, `description` is now ONE
    general theme (e.g. "ocean animals"), not literal subject lines --
    _resolve_coloring_subjects() expands it into NEW_THEME_SET_SIZE distinct,
    never-before-used subjects itself, checked against a permanent
    cross-listing registry so no coloring-page subject is ever generated
    twice across the whole catalog (Scott: "It will be a set of individual
    coloring pages. Never to repeat a creation."). Packaged into exactly one
    ZIP. (2026-08-08: bumped 20->30 per Scott, "made in groups of 30" -- see
    generate_coloring_pages.NEW_THEME_SET_SIZE, the one place that size
    lives.) An optional `difficulty` (standard/kids/adult) picks one style
    tier for the whole group -- see generate_dynamic_theme_set()'s docstring.

    (2026-07-25) For coloring_pages specifically, `pid` is now OPTIONAL --
    Scott: "It should auto generate the code." Omit it (empty string) along
    with a `description` and Frank picks the next free COLOR#### code itself
    via _next_coloring_pid() before continuing exactly as if that code had
    been typed by hand. Every other category still requires an explicit pid,
    unchanged."""
    pid = str((inp or {}).get("pid", "")).strip().upper()
    category = _resolve_build_category(pid, (inp or {}).get("category"))
    description = str((inp or {}).get("description", "")).strip()
    if not pid:
        if category == "coloring_pages" and description:
            pid = _next_coloring_pid()
        elif category == "coloring_pages":
            import generate_coloring_pages as _gcp_err
            return {"error": f"Describe a theme first (e.g. 'ocean animals') and Frank "
                              f"will pick the code and generate {_gcp_err.NEW_THEME_SET_SIZE} "
                              f"subjects from it."}
        else:
            return {"error": "pid is required (e.g. 'DP1030', 'WA1030', or a coloring-pages product_id)"}
    extra_args: list[str] = []
    reg_name: str | None = None
    reg_price: float | None = None
    reg_files: list[str] | None = None

    if category in ("wall_art", "wall_art_bundle"):
        # Pre-flight check (2026-07-22, mirroring the digital_planner branch
        # below): build_wallart_product.py hard-requires a source JPG at
        # product_files/<PID>.jpg or upscaled/<PID>.jpg to already exist --
        # without this check a genuinely new pid spawned a doomed subprocess
        # that failed several minutes later with only a generic exit-code
        # shown in the polling UI, the real reason buried in the log tail.
        try:
            import generate_print_sizes as _gps
            has_source_art = (
                (_gps.UPSCALED_DIR / f"{pid}.jpg").exists()
                or (_gps.PRODUCT_FILES_DIR / f"{pid}.jpg").exists()
            )
        except Exception as exc:  # noqa: BLE001
            return {"error": f"wall-art builder unavailable: {exc}"}
        engine = None
        if not has_source_art:
            if not description:
                return {"error": f"No source art found for {pid}. Add {pid}.jpg to "
                                  f"product_files/ (or upscaled/) yourself, or describe the "
                                  f"art you want in the 'new one' box and I'll generate it."}
            engine, eng_err = _resolve_art_engine(inp)
            if eng_err:
                return {"error": eng_err}
            # (2026-07-30) Fold in a Reference Photos library selection, if given --
            # the "library only right now" gap Scott reported (uploading a reference
            # image did nothing). One cached vision call turns the image into style
            # notes appended to the prompt as guidance, not a literal copy target.
            ref_id = str((inp or {}).get("reference_image_id", "")).strip()
            if ref_id:
                style_notes, ref_err = _reference_image_style_notes(ref_id)
                if ref_err:
                    return {"error": ref_err}
                description = f"{description}\n\nStyle reference (match this look, not the subject): {style_notes}"
            extra_args = ["--description", description, "--engine", engine]
            reg_name, reg_price = description[:120] or pid, None
            reg_files = [f"data/digital_products/print_zips/{pid}_print_sizes.zip"]
        script_name, log_suffix, proc_label = "build_wallart_product.py", "wallart_build", "build_wallart_product"
        steps = (["generate art", "print-size ZIP", "quality check"] if extra_args
                  else ["print-size ZIP", "quality check"])
        needs_visual_qc = bool(extra_args)  # new AI art can garble details -- eyeball it
    elif category == "coloring_pages":
        # Pre-flight check (2026-07-22): build_coloring_product.py's own
        # _catalog_lookup() hard-requires the pid to already be a
        # product_catalog.json entry with a non-empty files list (that's how
        # it infers which theme pack to build) -- reuse that exact function
        # rather than duplicating its logic, and fail fast with the real
        # reason instead of spawning a subprocess that exits 2 minutes later.
        #
        # Check the REAL catalog state first, THEN fall back to `description`
        # -- not the other way around. A stale leftover description (typed
        # while "+ new one" was open, not cleared when switching back to the
        # picker) must never hijack a rebuild of an EXISTING product into
        # generating brand-new pages instead. Same ordering wall_art already
        # uses above (has_source_art checked before description is read).
        try:
            import build_coloring_product as _bcp
            catalog_hit = _bcp._catalog_lookup(pid)
        except Exception as exc:  # noqa: BLE001
            return {"error": f"coloring-pages builder unavailable: {exc}"}
        engine = None
        if catalog_hit is None:
            if not description:
                return {"error": f"{pid} isn't in the coloring-pages catalog yet (or has no "
                                  f"files listed). Pick an existing set from the list, or "
                                  f"describe a new theme in the 'new one' box and I'll build it."}
            # (2026-07-24) `description` is now ONE theme, not literal subjects -- Frank
            # expands it into NEW_THEME_SET_SIZE distinct, never-before-used subjects
            # itself, checked against the permanent cross-listing registry -- see
            # _resolve_coloring_subjects()'s docstring. Scott: "It will be a set of
            # individual coloring pages. Never to repeat a creation."
            #
            # subjects override (2026-08-09): _resolve_coloring_subjects()'s own
            # Anthropic call can be unusable (confirmed in production the same day --
            # "Your credit balance is too low to access the Anthropic API" on every
            # attempt, real vs. a registry collision, verified against server logs).
            # A caller (Claude, or any future non-chat integration) can supply the
            # already-expanded subject list directly via inp['subjects'] to skip the
            # LLM-expansion step entirely -- this is a different SOURCE for subjects,
            # never a bypass of the "never repeat a creation" guarantee: still exactly
            # NEW_THEME_SET_SIZE entries, still checked against the full registry, still
            # recorded via the same _record_used_coloring_subjects() call below.
            subjects_override = (inp or {}).get("subjects")
            if isinstance(subjects_override, list) and subjects_override:
                import generate_coloring_pages as _gcp_subj
                subjects = [str(s).strip() for s in subjects_override if str(s).strip()]
                if len(subjects) != _gcp_subj.NEW_THEME_SET_SIZE:
                    return {"error": f"subjects must contain exactly {_gcp_subj.NEW_THEME_SET_SIZE} "
                                      f"non-empty entries, got {len(subjects)}"}
                registry = _coloring_theme_registry()
                # 2026-08-10: exclude this SAME pid's own prior reservations from the
                # collision set. Subjects are recorded eagerly, before the subprocess
                # spawns (see _record_used_coloring_subjects()'s docstring) -- without
                # this exemption, a build interrupted partway through (container
                # restart, crash) can never be retried: its own already-reserved
                # subjects would permanently self-collide on every resubmission of the
                # same payload. Cross-pid collisions are still blocked as before.
                used_normalized = {e["normalized"] for e in registry if e.get("product_id") != pid}
                seen_this_batch: set[str] = set()
                dupes = []
                for s in subjects:
                    norm = _normalize_subject(s)
                    if norm in used_normalized or norm in seen_this_batch:
                        dupes.append(s)
                    seen_this_batch.add(norm)
                if dupes:
                    return {"error": f"{len(dupes)} supplied subject(s) already used (repeated "
                                      f"within this batch, or already in the shop-wide registry): "
                                      f"{'; '.join(dupes[:5])}{'...' if len(dupes) > 5 else ''}"}
            else:
                subjects, subj_err = _resolve_coloring_subjects(description)
                if subj_err:
                    return {"error": subj_err}
            # difficulty (2026-08-08, Scott: "make sure the kids coloring pages are
            # separate from the adult due to the adult being more detailed") -- one
            # explicit tier for this WHOLE build, never mixed within a group (see
            # generate_dynamic_theme_set()'s own docstring). Defaults to "standard"
            # (the pre-existing behavior) for any caller that doesn't send it.
            import generate_coloring_pages as _gcp
            difficulty = str((inp or {}).get("difficulty", "standard")).strip().lower()
            if difficulty not in _gcp.DIFFICULTY_CHOICES:
                difficulty = "standard"
            # engine default by difficulty (2026-08-09, Scott: "make grok more for
            # teen and adult coloring pages. open ai for kids") -- confirmed across 3
            # real side-by-side prompts (cabin/treehouse/monster truck) in the
            # Reference Photos library that Grok renders denser, more intricate
            # linework (teen/adult) and OpenAI renders simpler, thicker-lined art
            # (kids) from the identical prompt. Only kicks in when the caller left
            # engine blank -- the Create screen's dropdown always sends an explicit
            # value (defaulted client-side, see _syncColoringEngineDefault()), so
            # this mainly protects non-UI callers; an explicit engine choice always
            # wins over this default.
            engine_inp = dict(inp or {})
            if not str(engine_inp.get("engine", "")).strip():
                engine_inp["engine"] = "openai" if difficulty == "kids" else "grok"
            engine, eng_err = _resolve_art_engine(engine_inp)
            if eng_err:
                return {"error": eng_err}
            extra_args = ["--description", "\n".join(subjects), "--engine", engine,
                          "--difficulty", difficulty]
            reg_name, reg_price = description.splitlines()[0][:120] or pid, None
            # NEW_THEME_SET_SIZE always caps subjects at one fixed size -> always exactly one ZIP, deterministic.
            reg_files = [f"data/digital_products/coloring_pages/sets/coloring_{pid.lower()}_set_01.zip"]
            # Record the reservation NOW, before the subprocess spawns -- see
            # _record_used_coloring_subjects()'s own docstring for why eager (not
            # deferred-to-success) is the correct tradeoff for a permanent registry.
            _record_used_coloring_subjects(pid, description, subjects)
        script_name, log_suffix, proc_label = "build_coloring_product.py", "coloring_build", "build_coloring_product"
        steps = (["coloring pages (new theme)", "quality check"] if extra_args
                  else ["coloring pages", "quality check"])
        needs_visual_qc = bool(extra_args)
    elif category == "digital_planner":
        engine, eng_err = _resolve_art_engine(inp)
        if eng_err:
            return {"error": eng_err}
        try:
            import generate_planner_v2 as _gpv2
            configured = set(getattr(_gpv2, "_ALL_V2_PIDS", []) or [])
        except Exception as exc:  # noqa: BLE001
            return {"error": f"product builder unavailable: {exc}"}
        if configured and pid not in configured:
            return {"error": f"{pid} isn't a configured planner (have {', '.join(sorted(configured))})."}
        script_name, log_suffix, proc_label = "build_product.py", "product_build", "build_product"
        steps = ["sticker pack", "planner PDFs", "listing photos", "quality check"]
        needs_visual_qc = True
    elif category == "wall_calendar":
        # WC-series (2026-08-11) -- built from a real competitive-research +
        # adversarial-review workflow pass before any code shipped; see
        # generate_wall_calendar.py's own module docstring for the design
        # decisions (week-start as a real product axis, the undated-variant
        # date-leak fix, why the monthly PDF isn't run through generate_
        # print_sizes.py). No auto-pid generation (yet) -- explicit pid
        # required, same as wall_art.
        import generate_wall_calendar as _gwc
        theme = str((inp or {}).get("theme", "")).strip().lower()
        if theme not in _gwc.CALENDAR_THEMES:
            return {"error": f"theme is required for wall_calendar (have: "
                              f"{', '.join(sorted(_gwc.CALENDAR_THEMES))})"}
        engine, eng_err = _resolve_art_engine(inp)
        if eng_err:
            return {"error": eng_err}
        year = (inp or {}).get("year")
        try:
            year = int(year) if year else _gwc.NEW_YEAR
        except (TypeError, ValueError):
            return {"error": f"year must be an integer, got {year!r}"}
        extra_args = ["--theme", theme, "--year", str(year), "--engine", engine]
        reg_name = f"{_gwc.CALENDAR_THEMES[theme]['label']} {year} Wall Calendar"
        reg_price = None
        reg_files = [f"data/digital_products/wall_calendars/packs/{pid.lower()}_calendar_pack.zip"]
        description = reg_name
        script_name, log_suffix, proc_label = "generate_wall_calendar.py", "calendar_build", "build_wall_calendar"
        steps = ["header art (12 illustrations)", "monthly-grid PDFs", "year-at-a-glance poster", "quality check"]
        needs_visual_qc = True  # header art is freshly AI-generated -- same honesty flag as any fresh-art build
    else:
        return {"error": f"'{category}' has no verified one-tap build pipeline yet (have: "
                          f"digital_planner, wall_art, coloring_pages, wall_calendar). Use the "
                          f"individual Create-screen tools for this product instead."}

    script = ROOT / "tools" / script_name
    if not script.exists():
        return {"error": f"{script_name} is missing from this deploy."}
    log_file = f"{pid}_{log_suffix}.log"
    try:
        _logf = open(_product_log_dir() / log_file, "w")  # noqa: SIM115 — handed to Popen
    except Exception:  # noqa: BLE001
        _logf = subprocess.DEVNULL
    proc = subprocess.Popen(
        [sys.executable, str(script), pid] + extra_args,
        stdout=_logf, stderr=subprocess.STDOUT, cwd=str(ROOT),
        env=_subprocess_env_with_engine(engine) if engine else None,
    )
    _LONG_RUNNING_PROCS[proc.pid] = (proc, f"{proc_label}:{pid}", datetime.now(timezone.utc))
    if category in ("wall_art", "wall_art_bundle", "coloring_pages", "wall_calendar") and reg_files is not None:
        # A watcher thread, not inline registration: only a CLEAN exit (0)
        # means the files this record claims actually exist. Registering
        # eagerly (before the subprocess even finishes) would let a failed
        # build register a product whose deliverables don't exist -- exactly
        # the kind of thing CLAUDE.md's top-priority rule forbids.
        def _watch_and_register(_proc=proc, _pid=pid, _cat=category, _name=reg_name,
                                 _price=reg_price, _files=reg_files, _desc=description):
            rc = _proc.wait()
            if rc == 0:
                _register_new_product_overlay(_pid, _cat, _name or _pid, _price, _files, _desc)
                # (2026-08-11) Pre-register listing photos here too -- same fix as
                # the bundle-merge path (_register_prepublish_coloring_listing_
                # images's own docstring) so a standard new-theme coloring/
                # calendar build also has photos ready to upload the moment its
                # create_listing action is approved, not a separate manual round
                # after. Calendars only get the poster (a real deliverable, not
                # an AI stand-in) pre-registered this way -- the remaining
                # lifestyle-room photo slots still need the standard AI-photo
                # flow, same as wall_art's existing "no lifestyle photos in the
                # one-tap build" precedent, just not left at zero photos either.
                if _cat == "coloring_pages" and _files:
                    zip_path = _catalog_file_abs_path(_files[0])
                    if zip_path is not None:
                        _register_prepublish_coloring_listing_images(_pid, zip_path)
                elif _cat == "wall_calendar" and _files:
                    zip_path = _catalog_file_abs_path(_files[0])
                    if zip_path is not None:
                        _register_prepublish_calendar_listing_images(_pid, zip_path)
        threading.Thread(target=_watch_and_register, daemon=True).start()
    result = {
        "pid": pid,
        "category": category,
        "started": True,
        "os_pid": proc.pid,
        "steps": steps,
        "needs_visual_qc": needs_visual_qc,
        "log_file": log_file,
        "message": f"Building {pid} ({category}) in the background: {' → '.join(steps)}. "
                   f"Files land in Files as each step finishes "
                   f"({pid}_{log_suffix}.log has the live run log + the final QC verdict). "
                   f"Nothing is published.",
    }
    if engine:
        result["engine"] = engine
    return result


@app.post("/api/produce/build-product")
async def produce_build_product(body: dict, _token: str = Depends(_rate_limited_auth)):
    """Kick off a full product build (steps vary by category — see
    _produce_build_product()'s docstring) in the background. Returns
    immediately; deliverables appear in Files as they finish."""
    return await asyncio.to_thread(_produce_build_product, body or {})


# ── Retry a failed background build straight from its Today-tab alert ────────
#
# _health_check_iteration() (above) tracks every one-tap build in
# _LONG_RUNNING_PROCS keyed by f"{proc_label}:{pid}" (e.g.
# "build_coloring_product:COLOR1002") and, on a non-zero exit or a hang,
# records it as an agent_heartbeat row named f"build:{cmd_name}" with status
# "error" -- exactly the alert Scott saw on the Today tab with no way to act
# on it ("Why don't these have the option fix? I know you can", 2026-07-31).
# This dispatcher maps each proc_label prefix back to the exact same builder
# function its own one-tap Create-screen button already calls, so "Retry"
# is not a new mutation path -- it's the identical, already-approved action,
# just re-triggered from the alert instead of typed in again.
_LOOP_RETRY_BUILDERS = {
    "build_coloring_pack": _produce_coloring_pack,
    "build_planner": _produce_build_planner,
    "build_sticker_pack": _produce_build_sticker_pack,
    "build_product": _produce_build_product,
    "build_wallart_product": _produce_build_product,
    "build_coloring_product": _produce_build_product,
}


def _retry_build_loop(inp: dict) -> dict:
    """`name` is a build-loop's agent_heartbeat name/label, e.g.
    'build:build_coloring_product:COLOR1002' or the bare
    'build_coloring_product:COLOR1002' (the Today alert only has the label
    on hand) -- both accepted. Never touches Etsy; each target function is
    already a real, independently-callable endpoint with its own validation,
    so a bad pid still fails with that function's own clear error."""
    raw = str((inp or {}).get("name", "")).strip()
    if raw.startswith("build:"):
        raw = raw[len("build:"):]
    if ":" not in raw:
        return {"error": f"'{raw}' isn't a recognized build-loop name (expected '<builder>:<pid>')."}
    proc_label, _, pid = raw.partition(":")
    builder = _LOOP_RETRY_BUILDERS.get(proc_label)
    if builder is None:
        return {"error": f"'{proc_label}' has no retry handler (retriable: "
                          f"{', '.join(sorted(_LOOP_RETRY_BUILDERS))})."}
    return builder({"pid": pid})


@app.post("/api/loops/retry")
async def retry_build_loop(body: dict, _token: str = Depends(_rate_limited_auth)):
    """Today tab's Retry button on a failed background-build alert. See
    _retry_build_loop()'s docstring."""
    return await asyncio.to_thread(_retry_build_loop, body or {})


@app.get("/api/produce/status")
async def produce_status(os_pid: int, log_file: str = "", _token: str = Depends(_auth_session_or_bearer)):
    """Poll a background build kicked off by build-planner/build-sticker-pack/
    build-product. Reads _LONG_RUNNING_PROCS (the same registry the hourly
    health-check loop reaps from) and tails the build's own log file.

    2026-07-22 Create-screen redesign: previously tapping a build button gave a
    static ack and a "Check Files" link, with nothing telling you whether the
    build was still running, had crashed, or had actually finished — the single
    biggest gap for someone new to Frank. This is the endpoint that closes it.
    No AI/Etsy cost, so the plain auth dependency (not the rate-limited one the
    kickoff routes use) is enough.

    `known: false` means the process was already reaped (the health-check loop
    deletes finished entries once it's logged them, normally within an hour) --
    reported honestly rather than guessed at, per _LONG_RUNNING_PROCS's own
    "never misreport a fetch/auth problem as content-missing" precedent
    elsewhere in this codebase."""
    entry = _LONG_RUNNING_PROCS.get(os_pid)
    result: dict = {"os_pid": os_pid}
    if entry is None:
        result["known"] = False
    else:
        proc, label, started_at = entry
        exit_code = proc.poll()
        result["known"] = True
        result["label"] = label
        result["running"] = exit_code is None
        result["exit_code"] = exit_code
        result["elapsed_s"] = (datetime.now(timezone.utc) - started_at).total_seconds()
    if log_file:
        safe_name = os.path.basename(log_file)  # sanitize -- no path traversal
        log_path = await asyncio.to_thread(_product_log_dir)
        log_path = log_path / safe_name
        try:
            text = await asyncio.to_thread(log_path.read_text, encoding="utf-8", errors="replace")
            result["log_tail"] = "\n".join(text.splitlines()[-40:])
        except OSError:
            result["log_tail"] = None
    return result


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

    size = await asyncio.to_thread(lambda: out_path.stat().st_size)
    return {
        "ok": True,
        "path": out_path.name,
        "size": size,
        "size_human": _human_size(size),
    }


@app.get("/api/studio/videos")
async def studio_list_videos(_token: str = Depends(_auth_session_or_bearer)):
    """List generated videos under data/social/videos/ for the Studio sidebar."""
    # (2026-07-25) glob + per-file stat() ran inline in the async body -- real
    # filesystem I/O against large files on a network volume, blocking the
    # whole single-process server. Same _scan()+to_thread shape list_files()
    # already uses.
    def _scan() -> list[dict]:
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
        return files

    return {"videos": await asyncio.to_thread(_scan)}


_PRODUCT_FILES_PREFIX = "data/digital_products/"

# Categories that never carry a customer-downloaded design file in the first
# place: 3d_print_physical ships a physical object (no digital delivery), and
# the *_license categories grant a commercial-use license, not a design file
# of their own. Before 2026-07-18 these were still run through the "must have
# digital files" check, so every one of them rendered a confusing "no files
# listed in catalog" badge on the Products screen for a condition that was
# never actually a problem.
_NO_FILES_REQUIRED_CATEGORIES = {"3d_print_physical", "svg_bundle_license", "sticker_pack_license"}


def _build_products_status(catalog: list[dict], file_exists_fn, overrides: dict | None = None) -> list[dict]:
    """Pure function (no I/O of its own) so this is directly unit-testable:
    given the full product catalog and a file-existence checker, compute
    per-product/per-file status. `file_exists_fn` takes the RAW catalog path
    exactly as stored in product_catalog.json (e.g.
    "data/digital_products/product_files/DP1026.pdf",
    "data/svg_pack/Bundle.zip", or a bare "coloring_set_01.zip") and decides
    how to resolve it -- see _catalog_file_exists() for why a single
    prefix-strip convention (the pre-2026-07-18 behavior) isn't enough: most
    non-planner categories store paths that were never rooted under
    data/digital_products/ at all.

    `overrides` (2026-07-18, Products-tappable-cards feature): dict keyed by
    product_id -> {"etsy_listing_id": ..., "status": ...}, sourced from the
    durable product_catalog_overrides.json sidecar (see
    _product_catalog_overrides()). data/product_catalog.json itself is
    git-tracked and never written by this server -- a create_listing staged
    action's result (a brand-new etsy_listing_id) has to live somewhere that
    survives a Railway redeploy, so it's layered on top of the base catalog
    here instead. Optional and defaults to no overrides so every existing
    caller/test keeps working unchanged.

    (2026-07-22) An override entry can ALSO carry `is_new_product: true` --
    a full record for a product with no base-catalog entry at all, written
    by _register_new_product_overlay() once a Create-screen "+ new one"
    build for wall_art/coloring_pages finishes successfully. Those get
    synthesized into an extra row below so a freshly-built product actually
    shows up in Products/reviewable, without ever writing to the
    git-tracked catalog file."""
    overrides = overrides or {}
    products = [_product_status_row(p, file_exists_fn, overrides) for p in catalog]
    known_ids = {p.get("product_id") for p in catalog}
    for pid, ov in overrides.items():
        if ov.get("is_new_product") and pid not in known_ids:
            synthetic = {
                "product_id": pid,
                "name": ov.get("name", pid),
                "category": ov.get("category", "uncategorized"),
                "price": ov.get("price"),
                "files": ov.get("files", []),
                "status": ov.get("status", "draft"),
                "etsy_listing_id": ov.get("etsy_listing_id", ""),
            }
            products.append(_product_status_row(synthetic, file_exists_fn, overrides))
    return products


def _product_status_row(p: dict, file_exists_fn, overrides: dict) -> dict:
    """One catalog (or synthesized) entry -> a Products-screen row. Extracted
    from _build_products_status()'s loop body (2026-07-22) so the same
    per-entry computation applies identically to real catalog entries and to
    synthesized is_new_product rows."""
    files = p.get("files", []) or []
    file_status = [{"name": Path(f).name, "exists": file_exists_fn(f)} for f in files]
    ov = overrides.get(p.get("product_id"), {})
    no_files_required = p.get("category") in _NO_FILES_REQUIRED_CATEGORIES
    return {
        "id": p.get("product_id"),
        "title": p.get("name", ""),
        "listing_id": ov.get("etsy_listing_id") or p.get("etsy_listing_id"),
        "category": p.get("category", "uncategorized"),
        "status": ov.get("status") or p.get("status", "active"),
        "price": p.get("price"),
        "files": file_status,
        "all_files_present": (
            None if no_files_required
            else (all(fs["exists"] for fs in file_status) if file_status else None)
        ),
        "files_not_applicable": no_files_required,
    }


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
    overrides = await asyncio.to_thread(_product_catalog_overrides)
    products = await asyncio.to_thread(_build_products_status, catalog, _catalog_file_exists, overrides)
    audit_idx = await asyncio.to_thread(_file_audit_index)
    for p in products:
        p["file_audit"] = audit_idx.get(p["id"])
    return {"products": products}


def _find_catalog_product(product_id: str) -> dict | None:
    try:
        catalog = json.loads(Path("data/product_catalog.json").read_text())
    except OSError:
        catalog = []
    for entry in catalog:
        if entry.get("product_id") == product_id:
            return entry
    # (2026-07-22) Fall back to a registered is_new_product overlay entry --
    # a product built via the Create screen's "+ new one" flow for
    # wall_art/coloring_pages has no base-catalog entry at all (see
    # _register_new_product_overlay()). Without this, GET /api/products/{id}
    # /review and stage-publish would 404 for a real, freshly-built product.
    ov = _product_catalog_overrides().get(product_id)
    if ov and ov.get("is_new_product"):
        return {
            "product_id": product_id,
            "name": ov.get("name", product_id),
            "category": ov.get("category", "uncategorized"),
            "price": ov.get("price"),
            "status": ov.get("status", "draft"),
            "etsy_listing_id": ov.get("etsy_listing_id", ""),
            "files": ov.get("files", []),
        }
    return None


def _next_coloring_pid() -> str:
    """(2026-07-25) Scott: "It should auto generate the code" -- the Create
    screen's Coloring Pages new-theme panel no longer asks him to hand-type
    a code. Scans for the lowest unused COLOR#### numeric code (this
    generator's own naming convention -- distinct from the 2 legacy fixed
    packs' descriptive COLOR_* slugs, e.g. COLOR_KAWAII_COLORING_PAGES_SET_11,
    which never collide with a purely-numeric suffix). Reuses
    _find_catalog_product() -- the same base-catalog + overlay dual-source
    uniqueness check every other pid-collision guard in this file already
    uses -- so a collision with ANY category's existing pid, not just
    coloring_pages, is caught too."""
    n = 1001
    while _find_catalog_product(f"COLOR{n}") is not None:
        n += 1
    return f"COLOR{n}"


# Deliverable files are what a buyer actually downloads -- distinct from listing
# photos (path contains "_listing_images/") and from source art like a standalone
# cover PNG, neither of which gets uploaded as an Etsy digital file.
#
# (2026-07-25) Was (".pdf", "_sticker_pack.zip") -- found during the "Etsy Listing"
# tile planning pass to silently drop EVERY Wall Art (*_print_sizes.zip) and
# Coloring Pages (coloring_*_set_NN.zip) deliverable from both `photos` and
# `deliverables`, since neither matched this suffix tuple. stage_product_publish
# would always fail "no deliverable files found" for those categories even after
# their taxonomy gate was fixed. Broadened to any .zip -- confirmed safe by
# checking every .zip currently listed in product_catalog.json across every
# category (digital_planner, wall_art, coloring_pages, svg_bundle, paper_pack,
# svg_3dprint_pack): none are stray/backup files, all are real deliverables.
_PRODUCT_DELIVERABLE_SUFFIXES = (".pdf", ".zip")


def _gather_product_review(product_id: str) -> dict | None:
    """Sync core shared by GET /api/products/{id}/review and POST
    /api/products/{id}/stage-publish -- the latter re-derives the exact same
    content rather than trusting whatever the client last saw, so staging
    can never publish something the review endpoint didn't just confirm."""
    entry = _find_catalog_product(product_id)
    if entry is None:
        return None

    overrides = _product_catalog_overrides()
    catalog_status = _build_products_status([entry], _catalog_file_exists, overrides)[0]

    listing_json_path = Path("data") / f"{product_id.lower()}_listing.json"
    content = None
    try:
        content = json.loads(listing_json_path.read_text())
    except (OSError, json.JSONDecodeError):
        pass
    if content is None:
        # (2026-07-25) Fall back to AI-generated content saved via the "Etsy
        # Listing" tile's generate-listing-content endpoint. The hand-authored
        # git-tracked file above always wins when both exist -- it's presumably
        # human-vetted; this sidecar exists for the other 174+ products that
        # will never get one hand-written.
        content = _generated_listing_content().get(product_id)

    photos: list[dict] = []
    deliverables: list[dict] = []
    for f in (entry.get("files") or []):
        name = Path(f).name
        exists = _catalog_file_exists(f)
        if "_listing_images/" in f:
            photos.append({"name": name, "rel": f, "exists": exists,
                            "url": _catalog_file_url(f) if exists else None})
        elif f.lower().endswith(_PRODUCT_DELIVERABLE_SUFFIXES):
            deliverables.append({"name": name, "rel": f, "exists": exists})
    photos.sort(key=lambda p: p["name"])

    qc = _qc_check_product({"pid": product_id})

    return {
        "product_id": product_id,
        "category": entry.get("category", "uncategorized"),
        "status": catalog_status["status"],
        "listing_id": catalog_status["listing_id"],
        "catalog": catalog_status,
        "has_content": content is not None,
        "content": ({
            "title": content.get("title", ""),
            "description": content.get("description", ""),
            "tags": content.get("tags", []),
            "price": content.get("price"),
            "shop_section_id": content.get("shop_section_id"),
            "color_theme": content.get("color_theme"),
            "pages": content.get("pages"),
        } if content else None),
        "photos": photos,
        "deliverables": deliverables,
        "qc": qc,
    }


@app.get("/api/products/{product_id}/review")
async def get_product_review(product_id: str, _token: str = Depends(_auth_session_or_bearer)):
    """Everything the Products-screen review modal needs in one call: the draft
    listing content (title/description/tags/price) from data/dp<id>_listing.json
    if it's been authored, the actual rendered listing photos + deliverable files
    with real on-disk presence, and a QC pass/warn/fail summary -- so Scott can
    review a not-yet-published planner (or see exactly what's blocking a
    create_listing stage) without opening a single file by hand."""
    review = await asyncio.to_thread(_gather_product_review, product_id)
    if review is None:
        raise HTTPException(status_code=404, detail=f"unknown product_id: {product_id}")
    return review


def _slugify_product_id(name: str, prefix: str) -> str:
    """Auto-generates a product_id from a human-typed name for the
    registration form (2026-08-05) -- Scott typing a name shouldn't also
    require inventing a unique code by hand. Collision-checked against
    BOTH the base catalog and the overlay sidecar via _find_catalog_product
    (never silently returns a colliding id)."""
    slug = _re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").upper()[:40]
    candidate = f"{prefix}_{slug}" if slug else prefix
    if _find_catalog_product(candidate) is None:
        return candidate
    n = 2
    while _find_catalog_product(f"{candidate}_{n}") is not None:
        n += 1
    return f"{candidate}_{n}"


@app.get("/api/products/classify-listing/{listing_id}")
async def classify_listing_for_registration(listing_id: int, _token: str = Depends(_auth_session_or_bearer)):
    """Read-only preview for the physical-product registration form
    (2026-08-05) -- fetches the live Etsy listing and runs classify_
    unmapped_listing() against it, so Scott sees a suggested name/category
    before committing anything. Never writes. 404s with an actionable
    message if the listing doesn't exist rather than a bare Etsy error."""
    try:
        listing = await asyncio.to_thread(EtsyAPIClient().get_listing, listing_id)
    except EtsyAPIError as exc:
        if getattr(exc, "status", None) == 404:
            raise HTTPException(status_code=404, detail=f"Listing {listing_id} not found on Etsy")
        raise HTTPException(status_code=502, detail=f"Etsy: {str(exc)[:200]}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch listing {listing_id}: {str(exc)[:200]}")
    classification = await asyncio.to_thread(classify_unmapped_listing, listing)
    existing_entry = await _get_manifest_entry(listing_id)
    return {
        "listing_id": listing_id,
        "title": listing.get("title", ""),
        "price": _price_float(listing.get("price")),
        "category": classification.get("category"),
        "confidence": classification.get("confidence"),
        "reasoning": classification.get("reasoning"),
        "already_registered": bool(existing_entry),
        "already_registered_as": (existing_entry or {}).get("dp_codes") if existing_entry else None,
    }


@app.post("/api/products/register")
async def register_product_directly(body: dict | None = None, _token: str = Depends(_rate_limited_auth)):
    """Scott-initiated product registration (2026-08-05, the Create screen's
    physical-product quick-add form). Unlike every other product/listing
    mutation in this app, this does NOT go through the staged-action
    approval queue -- it's a pure local write (product_catalog_overrides
    .json + listing_manifest_overrides.json), no Etsy API call at all, and
    Scott typing the form and hitting Save already IS the approval (see
    api-conventions.md's "nothing irreversible auto-executes" -- this is
    trivially reversible, edit or delete the local record any time). Reuses
    the exact same validate()/execute() pair the autonomous reconciliation
    sweep's register_product staged action uses, so a product registered
    either way ends up in an identical shape -- see _validate_staged_action
    and _execute_register_product_staged_action's register_product
    branches above."""
    b = body or {}
    name = (b.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    price = b.get("price")
    etsy_listing_id = b.get("etsy_listing_id")
    if etsy_listing_id is not None and not str(etsy_listing_id).strip():
        etsy_listing_id = None

    category = (b.get("category") or "").strip()
    if not category:
        # Best-effort auto-classify if Scott didn't pick one -- the Create
        # screen only offers this form for 3d_print_physical today (see the
        # frontend tile config), so that's the fallback when there's no live
        # listing to check real signals against.
        if etsy_listing_id:
            try:
                listing = await asyncio.to_thread(EtsyAPIClient().get_listing, int(etsy_listing_id))
                classification = await asyncio.to_thread(classify_unmapped_listing, listing)
                category = classification.get("category") or "3d_print_physical"
            except Exception:
                category = "3d_print_physical"
        else:
            category = "3d_print_physical"

    product_id = (b.get("product_id") or "").strip()
    if not product_id:
        prefix = {"3d_print_physical": "P3D"}.get(category, "MISC")
        product_id = await asyncio.to_thread(_slugify_product_id, name, prefix)

    payload = {
        "product_id": product_id, "name": name, "category": category,
        "price": price, "etsy_listing_id": etsy_listing_id,
    }
    ok, msg = await asyncio.to_thread(_validate_staged_action, {"type": "register_product", "payload": payload})
    if not ok:
        raise HTTPException(status_code=422, detail=msg)
    result = await asyncio.to_thread(_execute_register_product_staged_action, {"payload": payload})
    with _cache_lock:
        _cache.pop("products", None)
    return result


def _extract_grounding_facts(product_id: str, entry: dict) -> tuple[dict, list[str]]:
    """Real, computed facts about product_id's actual deliverable files --
    the ONLY numbers _build_listing_content_prompt()'s prompt is allowed to
    state affirmatively (CLAUDE.md's "never lie to the customer" rule,
    enforced in code here rather than left to the model's discretion).
    Read-only, no LLM call, no network. Returns (facts, problems) --
    problems is non-empty when a deliverable this category needs is
    missing/unreadable, in which case the caller must refuse to generate
    rather than fall back to vague copy."""
    import qc_sweep
    category = entry.get("category", "")
    facts: dict = {"product_id": product_id, "category": category,
                   "name": entry.get("name", product_id)}
    problems: list[str] = []
    for f in (entry.get("files") or []):
        name = Path(f).name
        if "_listing_images/" in f:
            continue
        abs_path = _catalog_file_abs_path(f)
        if abs_path is None:
            continue
        if name.lower().endswith(".pdf"):
            try:
                pdf_facts = etsy_api.validate_digital_file(str(abs_path), expected_ext=".pdf")
                facts["pdf_pages"] = pdf_facts["pdf_pages"]
            except etsy_api.FileContentError as exc:
                problems.append(f"{name}: {exc}")
        elif name.lower().endswith(".zip"):
            try:
                zip_facts = etsy_api.validate_digital_file(str(abs_path), expected_ext=".zip")
                facts["zip_members"] = zip_facts["zip_members"]
            except etsy_api.FileContentError as exc:
                problems.append(f"{name}: {exc}")
                continue
            with zipfile.ZipFile(abs_path) as zf:
                names = zf.namelist()
            if name.endswith("_sticker_pack.zip"):
                counts = qc_sweep.sticker_zip_counts(names)
                facts["sticker_sheets"] = counts["sheet_count"]
                facts["individual_stickers"] = counts["individual_sticker_count"]
            elif category == "coloring_pages":
                facts["coloring_page_count"] = qc_sweep.coloring_zip_page_count(names)
    required = {"digital_planner": ("pdf_pages",), "wall_art": ("zip_members",),
                "coloring_pages": ("coloring_page_count",)}.get(category, ())
    for key in required:
        if key not in facts:
            problems.append(f"no readable {key.replace('_', ' ')} found for {product_id} — "
                             f"build/sync its deliverable file(s) first")
    return facts, problems


_CONTENT_PRICE_BY_CATEGORY = {
    # Code decides price, never the model -- mirrors pre_publish_gate()'s
    # existing philosophy that price format/floor is a hard code gate, not
    # prompt text. digital_planner: the niche-planner tier from CLAUDE.md's
    # pricing table (a freshly-generated planner is more likely niche than
    # a flagship, which has no single "default" price anyway). wall_art:
    # CLAUDE.md Gate 7 "Single print" tier ($4.99-$7.99) -- picks the tier
    # midpoint. coloring_pages: CLAUDE.md has NO documented price table for
    # this category at all (confirmed 2026-07-25) -- $6.99 is a code-level
    # judgment call for the dynamic sets, not invented by the LLM. (2026-08-08:
    # group size grew 20->30 pages -- data/knowledge_base/coloring_page_design_
    # and_market_research.md's own real market data puts 25+-page bundles at
    # $8-15, so this default is worth a pricing review; not auto-changed here.)
    # Scott can adjust any of these via a normal price-fix action after
    # a listing is generated -- this is a starting point, not gospel.
    "digital_planner": 12.99,
    "wall_art": 6.99,
    "coloring_pages": 6.99,
}


_PRODUCT_TAXONOMY_BY_CATEGORY = {
    # digital_planner: verified end-to-end against a real dpXXXX_listing.json
    # (data/dp1030_listing.json) -- matches both CLAUDE.md's own taxonomy
    # table and etsy_listing_tools.py's (unwired) TAXONOMY_BY_TYPE["planner"].
    # wall_art / coloring_pages (2026-07-25): CLAUDE.md documents 2078
    # ("Craft Supplies & Tools > Patterns & How To > Digital Files") for TWO
    # already-confirmed categories (Digital Planners and SS-Series SVG
    # Packs), so it's used here too rather than left unset -- but this
    # sandbox has no live Etsy credentials to verify against directly (see
    # _resolve_category_taxonomy_id()), so the value self-corrects against
    # a real live listing the first time each category actually stages,
    # instead of trusting the guess forever.
    "digital_planner": 2078,
    "wall_art": 2078,
    "coloring_pages": 2078,
    # svg_bundle/svg_bundle_license/sticker_pack/sticker_pack_license/
    # paper_pack (2026-07-26, SKU/category backfill): all digital-download
    # categories, so 2078 is the reasonable starting guess -- but every one
    # of these already has live listings on Etsy, so _resolve_category_
    # taxonomy_id() below will verify (and self-correct if wrong) against a
    # real listing the first time each category is actually processed.
    # Deliberately NOT guessed the same way: 3d_print_physical -- 2078 is a
    # digital-goods taxonomy and would be actively wrong for a physical
    # good (data/listing_rules.json already nulls this check for that exact
    # reason). Left out of this dict on purpose so it's discovered from a
    # real live listing instead (see the broadened live-check below, which
    # no longer requires a hardcoded default to attempt discovery).
    "svg_bundle": 2078,
    "svg_bundle_license": 2078,
    "sticker_pack": 2078,
    "sticker_pack_license": 2078,
    "paper_pack": 2078,
}

# In-process cache of RESOLVED (possibly live-corrected) taxonomy_id per
# category -- see _resolve_category_taxonomy_id(). Was a set[str] ("have we
# already checked") until 2026-07-26: that meant a live-discovered
# correction only ever applied to the ONE call that triggered it -- every
# subsequent call in the same process fell through to the stale hardcoded
# default again, since "already checked" short-circuited before the
# corrected value was ever consulted. Now caches the actual resolved value
# (which may be None if no default and no live listing exists yet).
_CATEGORY_TAXONOMY_RESOLVED: dict[str, int | None] = {}


def _resolve_category_taxonomy_id(category: str) -> int | None:
    """Returns the taxonomy_id to publish `category` under, self-correcting
    (or, for a category with no hardcoded guess at all, self-DISCOVERING)
    against a real live Etsy listing the first time this process ever needs
    that category -- at most one live-check attempt per category per
    process lifetime (_CATEGORY_TAXONOMY_RESOLVED), never blocking staging
    on the live check itself. If the live check disagrees with (or fills in
    a missing) hardcoded default, logs a clear ops_runbook-style message and
    uses the REAL value for every call in this process going forward
    (persisting it back into _PRODUCT_TAXONOMY_BY_CATEGORY in code is
    deliberately NOT done here -- a wrong guess should be visible in logs
    and fixed in code, not silently self-healing across deploys).

    2026-07-26: broadened to attempt the live check for ANY category with a
    live listing to check against, not just categories that already have a
    hardcoded default -- previously `if default is None: return default`
    skipped the live check entirely for exactly the categories that needed
    it most (svg_bundle, sticker_pack, paper_pack, 3d_print_physical, etc.,
    none of which had a guess in the dict at all)."""
    if category in _CATEGORY_TAXONOMY_RESOLVED:
        return _CATEGORY_TAXONOMY_RESOLVED[category]
    default = _PRODUCT_TAXONOMY_BY_CATEGORY.get(category)
    try:
        catalog = json.loads(Path("data/product_catalog.json").read_text())
    except OSError:
        _CATEGORY_TAXONOMY_RESOLVED[category] = default
        return default
    live_id = next((e.get("etsy_listing_id") for e in catalog
                     if e.get("category") == category and e.get("etsy_listing_id")), None)
    if not live_id:
        _CATEGORY_TAXONOMY_RESOLVED[category] = default
        return default  # nothing live yet in this category -- nothing to verify/discover against
    try:
        real_taxonomy = EtsyAPIClient().get_listing(live_id).get("taxonomy_id")
    except Exception as exc:
        print(f"[taxonomy] could not verify {category} against live listing {live_id}: {exc}", flush=True)
        _CATEGORY_TAXONOMY_RESOLVED[category] = default
        return default
    if real_taxonomy and real_taxonomy != default:
        verb = "MISMATCH" if default is not None else "DISCOVERED"
        print(
            f"[taxonomy] {verb} — {category}'s hardcoded taxonomy_id {default!r} disagrees "
            f"with (or was missing vs.) live listing {live_id}'s real taxonomy_id {real_taxonomy}. "
            f"Using the real value for this process; update _PRODUCT_TAXONOMY_BY_CATEGORY in code "
            f"to make this permanent.", flush=True
        )
        _CATEGORY_TAXONOMY_RESOLVED[category] = real_taxonomy
        return real_taxonomy
    _CATEGORY_TAXONOMY_RESOLVED[category] = default
    return default


def _build_listing_content_prompt(product_id: str, entry: dict, facts: dict,
                                   feedback: str = "") -> str:
    """Category-aware prompt for _generate_product_listing_content_core().
    Every fact interpolated below is real (from _extract_grounding_facts());
    the model is explicitly told it may NEVER state a page/sheet/sticker/
    coloring-page count that isn't one of these. `feedback` carries the
    prior attempt's grounding-check mismatches on a retry."""
    category = entry.get("category", "")
    name = entry.get("name", product_id)
    facts_block = "\n".join(f"- {k}: {v}" for k, v in facts.items()
                             if k not in ("product_id", "category", "name"))
    grounding_rule = (
        "GROUNDING RULE -- read carefully:\n"
        "The REAL FACTS above are the ONLY numbers you may state as counts in the description "
        "(page count, sticker sheet count, individual sticker count, coloring page count). "
        "If a fact isn't listed above, do NOT invent a number for it -- describe it qualitatively "
        "instead (e.g. 'a full kawaii sticker pack' rather than a made-up sheet count). "
        "This is a hard rule: OnBrandCraftz has zero tolerance for lying to the customer, and "
        "every numeric claim you make will be checked against these exact facts before this is saved."
    )
    if category == "digital_planner":
        template = (
            "Write a complete Etsy listing for a digital planner, following these EXACT "
            "9 description sections in order: Hook, WHAT'S INCLUDED, COMPATIBLE APPS, "
            "HOW TO USE STICKERS, HOW TO USE THE PLANNER, SECTIONS INCLUDED, TECHNICAL DETAILS, "
            "FAQ (min 5 Qs), COPYRIGHT. Use ━━━ emoji section dividers. First sentence must hook "
            "the buyer AND contain the primary keyword. Title: 100-140 chars (Etsy's real platform "
            "max is 140; real top-favorited competitors cluster 100-140, not <=70), must contain "
            "'Instant Download', comma-separated (never pipes), lead with the primary search "
            "keyword in the first 20-40 chars, then add further buyer-search phrases, mention "
            "GoodNotes/iPad compatibility. "
            "Tags: exactly 13, each ≤20 chars, no special characters, none may duplicate a "
            "title phrase, cover style/app/audience/format/use-case."
        )
    elif category == "wall_art":
        template = (
            "Write a complete Etsy listing for printable wall art. Description's first sentence "
            "MUST state (verbatim or close variant): \"Instant download printable wall art — "
            "digital download delivered immediately after purchase, ready to print at home or at "
            "any print shop.\" Title formula: [Primary search phrase] Printable Wall Art, Instant "
            "Download, [Style/room], [additional buyer-search phrases] -- 100-140 chars, lead with "
            "the primary keyword in the first 40 chars, comma-separated. Tags: exactly 13, each ≤20 "
            "chars, covering style/room-type/medium/occasion/recipient/format, none duplicating "
            "a title phrase."
        )
    elif category == "coloring_pages":
        # No CLAUDE.md template exists for this category (confirmed 2026-07-25) -- adapted
        # from the documented digital_planner 9-section shape, dropping app-compatibility
        # sections that don't apply to a printable PNG page set.
        template = (
            "Write a complete Etsy listing for a themed printable coloring page set, using "
            "these sections in order: Hook (primary keyword in sentence 1), WHAT'S INCLUDED "
            "(page count, format, theme), HOW TO USE (print at home or any print shop; screen "
            "coloring apps), THEME & SUBJECTS (what's depicted), TECHNICAL DETAILS (file "
            "format/size/page count), FAQ (min 5 Qs), COPYRIGHT (personal use only). Title: "
            "must include 'printable' and 'instant download', 100-140 chars, lead with the primary "
            "keyword in the first 40 chars, comma-separated. "
            "Tags: exactly 13, each ≤20 chars, covering theme/audience/occasion/format, none "
            "duplicating a title phrase."
        )
    else:
        raise ValueError(f"no content template for category {category!r}")

    prompt = (
        f"{template}\n\nPRODUCT: {name} (id: {product_id})\n\nREAL FACTS:\n{facts_block}\n\n"
        f"{grounding_rule}\n\n"
        "Respond with ONLY a JSON object: "
        '{"title": str, "description": str, "tags": [13 strings]}. No price -- price is fixed by us.'
    )
    if feedback:
        prompt += f"\n\nYOUR PREVIOUS ATTEMPT WAS REJECTED FOR THIS REASON — fix it:\n{feedback}"
    return prompt


_SHEET_CLAIM_RE = _re.compile(r"(\d{1,3})\s*(?:png\s+)?sticker\s+sheets?\b", _re.IGNORECASE)
_INDIV_STICKER_CLAIM_RE = _re.compile(r"(\d{1,4})\+?\s*(?:individual\s+)?stickers?\b", _re.IGNORECASE)
_COLORING_PAGE_CLAIM_RE = _re.compile(r"(\d{1,3})\s*(?:individual\s+)?coloring\s+pages?\b", _re.IGNORECASE)


def _check_generated_content_grounding(description: str, facts: dict) -> list[str]:
    """Extra generation-time checks layered ON TOP of etsy_api.
    check_description_count_claims() (which stays upload-time, PDF-page/
    zip-member-floor only, unchanged) -- these check sheet/individual-
    sticker/coloring-page-count claims against the REAL counts
    _extract_grounding_facts() just computed, which check_description_
    count_claims() has no concept of. Exact-match (not floor-check)
    because these ARE the ground-truth numbers at generation time, unlike
    upload time where only the file's existence is known. Returns [] when
    the description is clean."""
    problems: list[str] = []
    if "sticker_sheets" in facts:
        bad = {m for m in (int(x) for x in _SHEET_CLAIM_RE.findall(description))
               if m != facts["sticker_sheets"]}
        if bad:
            problems.append(f"claims {sorted(bad)} sticker sheet(s) but the real pack has "
                             f"{facts['sticker_sheets']}")
    if "individual_stickers" in facts:
        bad = {m for m in (int(x) for x in _INDIV_STICKER_CLAIM_RE.findall(description))
               if m > facts["individual_stickers"]}
        if bad:
            problems.append(f"claims up to {max(bad)}+ stickers but the real pack only has "
                             f"{facts['individual_stickers']}")
    if "coloring_page_count" in facts:
        bad = {m for m in (int(x) for x in _COLORING_PAGE_CLAIM_RE.findall(description))
               if m != facts["coloring_page_count"]}
        if bad:
            problems.append(f"claims {sorted(bad)} coloring page(s) but the ZIP has exactly "
                             f"{facts['coloring_page_count']}")
    return problems


@app.post("/api/products/{product_id}/stage-publish")
async def stage_product_publish(product_id: str, _token: str = Depends(_auth_session_or_bearer)):
    """The Products-screen review modal's "Publish to Etsy" button. Re-derives
    the review content fresh (never trusts stale client state), builds the
    listing_data Etsy needs, and stages a create_listing action -- the actual
    Etsy write only happens once Scott approves it in the Action Center, same
    as every other mutation in this app, even ones he triggers directly from
    a UI button rather than chat."""
    review = await asyncio.to_thread(_gather_product_review, product_id)
    if review is None:
        raise HTTPException(status_code=404, detail=f"unknown product_id: {product_id}")

    if review["listing_id"]:
        raise HTTPException(status_code=409, detail=f"{product_id} already has an Etsy listing ({review['listing_id']})")

    taxonomy_id = await asyncio.to_thread(_resolve_category_taxonomy_id, review["category"])
    if taxonomy_id is None:
        raise HTTPException(status_code=400, detail=f"publishing isn't supported yet for category '{review['category']}'")

    if not review["has_content"]:
        raise HTTPException(status_code=400, detail="no listing content authored yet — draft a title/description/tags first")

    if review["qc"]["verdict"] == "fail":
        raise HTTPException(status_code=400, detail=f"QC gate failed: {review['qc']['message']}")

    deliverables = [d for d in review["deliverables"] if d["exists"]]
    if len(deliverables) < len(review["deliverables"]):
        missing = [d["name"] for d in review["deliverables"] if not d["exists"]]
        raise HTTPException(status_code=400, detail=f"missing deliverable file(s): {', '.join(missing)}")
    if not deliverables:
        raise HTTPException(status_code=400, detail="no deliverable files found for this product")

    photos = [p for p in review["photos"] if p["exists"]]

    # Refuse a duplicate stage -- a second tap on "Publish" while the first
    # is still pending in Approvals must not create two competing actions.
    pending = await asyncio.to_thread(db.list_actions, "pending")
    if any(pa.get("type") == "create_listing" and (pa.get("payload") or {}).get("product_id") == product_id
           for pa in pending):
        raise HTTPException(status_code=409, detail=f"a publish for {product_id} is already pending approval")

    content = review["content"]
    listing_data = {
        "title": content["title"],
        "description": content["description"],
        "tags": content["tags"],
        "price": content["price"],
        "taxonomy_id": taxonomy_id,
        "quantity": 999,
        "type": "download",
        # SKU convention (2026-07-26, "every listing categorized and has a
        # SKU" -- Scott): reuse the catalog's own product_id, confirmed with
        # Scott rather than inventing a separate SKU scheme -- keeps every
        # new listing correct from creation instead of needing a later
        # backfill (see _sku_taxonomy_backfill_loop for the one-time sweep
        # over listings created before this).
        "sku": product_id,
    }
    if content.get("shop_section_id"):
        listing_data["shop_section_id"] = content["shop_section_id"]

    payload = {
        "product_id": product_id,
        "listing_data": listing_data,
        "photo_paths": [p["rel"] for p in photos],
        "file_paths": [d["rel"] for d in deliverables],
    }
    candidate = {"type": "create_listing", "payload": payload}
    ok, msg = await asyncio.to_thread(_validate_staged_action, candidate)
    if not ok:
        raise HTTPException(status_code=422, detail=f"pre-publish gate failed: {msg}")

    summary = f"Publish {product_id} — \"{content['title']}\" — ${content['price']}"
    action_id = await asyncio.to_thread(db.enqueue_action, "create_listing", summary, payload)
    with _cache_lock:
        _cache.pop("actions", None)
    return {"staged": True, "action_id": action_id, "product_id": product_id, "summary": summary}


@app.post("/api/products/{product_id}/generate-listing-content")
async def generate_product_listing_content(
    product_id: str, body: dict | None = None, _token: str = Depends(_rate_limited_auth),
):
    """The review modal's "✨ Generate listing content" button. Writes a real,
    grounded title/description/13 tags/price into the generated-content
    sidecar (never the git-tracked data/{id}_listing.json) for a product
    with no listing content yet. Costs LLM $ and writes durable state, so
    it's rate-limited auth like every other AI-spend endpoint. Returns the
    FRESH review payload (not just the raw generated content) so the
    frontend can re-render in one round trip.

    body.engine (2026-08-05, optional): per-generation TEXT_ENGINE override
    from the modal's Advanced picker -- see _effective_text_engine()'s
    docstring. Falls back to the shop-wide TEXT_ENGINE default when absent."""
    engine_override = (body or {}).get("engine")
    if engine_override is not None:
        engine_override = str(engine_override).lower().strip()
        if engine_override not in _TEXT_ENGINES:
            raise HTTPException(status_code=400, detail=f"engine must be one of {_TEXT_ENGINES}")
    result = await _generate_product_listing_content_core(product_id, engine_override=engine_override)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    review = await asyncio.to_thread(_gather_product_review, product_id)
    return review


@app.post("/api/products/{product_id}/set-listing-content")
async def set_product_listing_content(
    product_id: str, body: dict | None = None, _token: str = Depends(_rate_limited_auth),
):
    """Manually set title/description/tags/price for a product's listing
    content, bypassing _generate_product_listing_content_core()'s AI call
    entirely. Added 2026-08-09: BOTH text-generation paths were unusable in
    production the same day -- Anthropic's credit balance is exhausted
    (confirmed via real server logs), and the TEXT_ENGINE="grok" override
    silently degrades back to Anthropic because XAI_KEY is empty server-side
    (the real xAI key on Railway is stored under the variable name "Grok
    api", not XAI_API_KEY -- a separate already-logged bug). Scott: "I want
    you to build it. Don't use Frank. You complete it then put it in Frank."

    Hand-supplied content gets ZERO exemption from the checks the AI path
    runs -- same _extract_grounding_facts() real-file-count lookup, same
    etsy_api.check_description_count_claims() + _check_generated_content_
    grounding() numeric-claim checks, same EtsyAPIClient.pre_publish_gate().
    A caller who claims "50 coloring pages" for a 30-page ZIP fails exactly
    like the AI path would. Returns the fresh review payload, same shape as
    generate-listing-content, so the review modal renders identically
    regardless of which path populated the content."""
    entry = _find_catalog_product(product_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"unknown product_id: {product_id}")
    category = entry.get("category", "")
    if category not in _CONTENT_PRICE_BY_CATEGORY:
        raise HTTPException(status_code=400, detail=f"content generation isn't supported yet for category '{category}'")
    b = body or {}
    title = str(b.get("title", "")).strip()
    description = str(b.get("description", "")).strip()
    tags = [_clean_tag(t) for t in (b.get("tags") or []) if str(t).strip()]
    price = b.get("price")
    price = float(price) if price is not None else _CONTENT_PRICE_BY_CATEGORY[category]

    facts, problems = await asyncio.to_thread(_extract_grounding_facts, product_id, entry)
    if problems:
        raise HTTPException(status_code=400, detail="can't set content — " + "; ".join(problems))
    content = {"product_id": product_id, "title": title, "description": description,
               "tags": tags, "price": price}
    gate_problems = (etsy_api.check_description_count_claims(description, facts)
                      + _check_generated_content_grounding(description, facts)
                      + EtsyAPIClient.pre_publish_gate(content))
    if gate_problems:
        raise HTTPException(status_code=400, detail="; ".join(gate_problems))
    await asyncio.to_thread(_write_generated_listing_content, product_id, content)
    with _cache_lock:
        _cache.pop("products", None)
    review = await asyncio.to_thread(_gather_product_review, product_id)
    return review


# Allowlist for run_agent_tool_direct() below -- staging-only tools whose
# own existing validation/caps are trusted as-is (never extended here).
# stage_action: single listing, one field at a time (title/tags/description/
# price/state/sku). stage_batch_price_update / stage_batch_listing_state:
# multi-listing, hard-capped at 5 per call inside _execute_agent_tool()
# itself -- this endpoint does not, and must never, raise that cap.
_DIRECT_AGENT_TOOLS = frozenset({"stage_action", "stage_batch_price_update", "stage_batch_listing_state"})


@app.post("/api/agent-tools/{tool_name}")
async def run_agent_tool_direct(
    tool_name: str, body: dict | None = None, _token: str = Depends(_rate_limited_auth),
):
    """Direct HTTP path into _execute_agent_tool() for the small allowlisted
    subset of chat-agent tools that are pure staging operations (never an
    Etsy write themselves -- everything they do still lands as a pending
    Action Center entry). Added 2026-08-10: with production's Anthropic
    credit balance exhausted (logged 2026-08-09/10), the chat loop that
    normally decides to call these tools is dead, but the tools themselves
    are plain functions with zero LLM dependency -- this unblocks Scott's
    own explicit, already-confirmed instructions (e.g. "reprice these 91
    listings the way I just told you to") without touching the chat layer
    at all.

    Deliberately NOT a general-purpose "call any agent tool" endpoint --
    _execute_agent_tool() dispatches to dozens of branches, some of which
    assume they're only ever reached after an LLM has already reasoned
    about intent (e.g. content-generation tools). Every entry in
    _DIRECT_AGENT_TOOLS below is staging-only, keeps its own existing
    validation/caps completely intact (stage_batch_price_update still
    hard-caps at 5 listings per call -- this endpoint does not touch that),
    and never mutates a live Etsy listing on its own."""
    if tool_name not in _DIRECT_AGENT_TOOLS:
        raise HTTPException(status_code=404, detail=f"'{tool_name}' isn't available via this endpoint "
                                                      f"(have: {', '.join(sorted(_DIRECT_AGENT_TOOLS))})")
    result = await asyncio.to_thread(_execute_agent_tool, tool_name, body or {})
    with _cache_lock:
        _cache.pop("actions", None)
    return result


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
            "google_calendar": {
                "client_id":     bool(env.get("GOOGLE_CALENDAR_CLIENT_ID")),
                "client_secret": bool(env.get("GOOGLE_CALENDAR_CLIENT_SECRET")),
                "refresh_token": bool(env.get("GOOGLE_CALENDAR_REFRESH_TOKEN")),
            },
            "etsy_live": False,
            "etsy_live_error": None,
            "shop_name": "",
            "etsy_tokens_updated_at": None,
        }
        try:
            shop = EtsyAPIClient().get_shop()
            status["etsy_live"] = True
            status["shop_name"] = shop.get("shop_name", "")
        except Exception as exc:
            status["etsy_live_error"] = str(exc)[:120]
        # 2026-07-31 (Settings audit): sourced here, not from GET /api/etsy-tokens,
        # because that route is owner-only and every self-signup tester is
        # role="admin" -- Settings' Connections summary was 403ing for every
        # non-owner session just to read this one timestamp. This endpoint has
        # no owner gate, so it's reachable by the same sessions that need it.
        try:
            stored = db.get_etsy_tokens()
            status["etsy_tokens_updated_at"] = stored.get("updated_at") if stored else None
        except Exception:
            pass
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
    parent_refresh_token = os.getenv("ETSY_REFRESH_TOKEN", "")
    ok = await asyncio.to_thread(lambda: EtsyAPIClient().refresh_access_token())
    if not ok:
        raise HTTPException(status_code=502, detail=(
            "Refresh failed -- if the refresh token itself has expired (90 days with no "
            "successful rotation), run `python tools/etsy_oauth.py` on your own machine to "
            "fully re-authorize."
        ))
    # refresh_access_token() only updates os.environ in-memory + a best-effort
    # .env write (a no-op on Railway's ephemeral filesystem) -- it never
    # persisted to the durable db.etsy_tokens store, unlike the sibling
    # POST /api/etsy-tokens endpoint above. Etsy invalidates the OLD refresh
    # token the instant this rotation succeeds, so a restart/redeploy before
    # the separate ~60s background sync loop happens to persist it would
    # strand the shop on a dead refresh token (2026-08-13 functional audit).
    new_access = os.getenv("ETSY_ACCESS_TOKEN", "")
    new_refresh = os.getenv("ETSY_REFRESH_TOKEN", "")
    updated_at = None
    if new_access and new_refresh:
        # 2026-08-14 functional audit (round 2): the refresh itself already
        # succeeded and a live token is already in os.environ for this
        # process -- a DB failure here (locked file, disk full) must not turn
        # into a bare 500 that hides that success from the caller. The
        # background _token_sync_loop will retry this same persistence on
        # its own next tick, so a logged-and-swallowed failure here is safe,
        # not silent (api-conventions.md: never a bare exception, never a
        # silent swallow that changes what gets reported as true -- this
        # keeps "the refresh worked" true while being honest that durable
        # persistence specifically is not yet confirmed via updated_at).
        try:
            await asyncio.to_thread(db.save_etsy_tokens, new_access, new_refresh, parent_refresh_token)
            tokens = await asyncio.to_thread(db.get_etsy_tokens)
            updated_at = (tokens or {}).get("updated_at")
        except Exception as exc:
            print(f"[etsy-tokens] core_refresh_etsy_token: DB persistence failed after a successful "
                  f"Etsy refresh -- _token_sync_loop will retry: {exc}", flush=True)
    return {"ok": True, "updated_at": updated_at}


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
    result = await asyncio.to_thread(db.save_user_profile, name, email, phone, tz)
    # 2026-08-06 Settings audit finding: `owner_name` has been in _SETTINGS_APPLY
    # (-> business_config.OWNER_NAME) since it was written, but nothing ever
    # called db.set_setting("owner_name", ...) -- dead plumbing. This field
    # already looks like "change your name" to Scott; make it actually change
    # how the agent addresses him in chat/prompts, not just a redisplayed DB row.
    if name:
        await asyncio.to_thread(db.set_setting, "owner_name", name)
        _refresh_identity()
    return result


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


def _session_short_id(session_id: str) -> str:
    """Stable, one-way, non-reversible display id for a session -- the real
    session_id IS the bearer credential for that session, so it must never
    reach the client. Hashing lets the Settings 'Active sessions' card show
    and revoke a specific session without ever exposing the raw token."""
    return hashlib.sha256(session_id.encode()).hexdigest()[:12]


def _relative_time_str(iso_str: str) -> str:
    """Human-friendly '2 hours ago' style string for the Active sessions list."""
    try:
        then = datetime.fromisoformat(iso_str)
    except (TypeError, ValueError):
        return iso_str or ""
    delta = datetime.now(timezone.utc) - then
    seconds = delta.total_seconds()
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    return f"{int(seconds // 86400)}d ago"


@app.get("/api/account/sessions")
async def get_my_sessions(request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """List the signed-in user's own active sessions -- Settings 'Active
    sessions' card (2026-08-06 Settings audit finding: this genuinely didn't
    exist anywhere in the app). Self-service only, same _get_session_user()
    convention as change_my_password/delete_my_account -- no admin scope."""
    uname = _get_session_user(request)
    if not uname:
        return {"sessions": []}
    current_sid = request.cookies.get(SESSION_COOKIE, "")
    rows = await asyncio.to_thread(db.list_sessions_for_user, uname)
    return {"sessions": [
        {
            "session_id_short": _session_short_id(r["session_id"]),
            "created_at": r["created_at"],
            "created_at_relative": _relative_time_str(r["created_at"]),
            "user_agent": r.get("user_agent") or "",
            "is_current": r["session_id"] == current_sid,
        }
        for r in rows
    ]}


@app.delete("/api/account/sessions/{short_id}")
async def revoke_my_session(short_id: str, request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """Revoke one specific session by its short (hashed) id. Never allows
    revoking the current session through this endpoint -- that's what the
    'Log out everywhere else' button + the normal logout button are for."""
    uname = _get_session_user(request)
    if not uname:
        raise HTTPException(status_code=401, detail="Log in to manage your sessions")
    current_sid = request.cookies.get(SESSION_COOKIE, "")
    rows = await asyncio.to_thread(db.list_sessions_for_user, uname)
    match = next((r for r in rows if _session_short_id(r["session_id"]) == short_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Session not found")
    if match["session_id"] == current_sid:
        raise HTTPException(status_code=400, detail="Can't revoke your current session this way — use logout")
    await asyncio.to_thread(db.delete_session, match["session_id"])
    with _sessions_lock:
        _sessions.pop(match["session_id"], None)
    return {"ok": True}


@app.post("/api/account/sessions/revoke-others")
async def revoke_other_sessions(request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """'Log out everywhere else' — revokes every OTHER active session for the
    signed-in user, keeping the current device signed in."""
    uname = _get_session_user(request)
    if not uname:
        raise HTTPException(status_code=401, detail="Log in to manage your sessions")
    current_sid = request.cookies.get(SESSION_COOKIE, "")
    rows = await asyncio.to_thread(db.list_sessions_for_user, uname)
    others = [r["session_id"] for r in rows if r["session_id"] != current_sid]
    for sid in others:
        await asyncio.to_thread(db.delete_session, sid)
        with _sessions_lock:
            _sessions.pop(sid, None)
    return {"revoked": len(others)}


@app.delete("/api/account")
async def delete_my_account(request: Request, _token: str = Depends(_auth_session_or_bearer)):
    """Self-service account deletion (2026-07-18, Scott: a Settings 'delete my
    account' option for anyone who signed up via /signup). This is the account
    owner's own right-to-erasure request, not admin_delete_user's owner-deletes-
    someone-else path -- identity comes from the session, same as
    change_my_password above, and there's no username parameter to trust from the
    caller. The owner account can never be removed this way (mirrors the existing
    invariant in admin_delete_user): with a single owner per shop, self-deleting it
    would orphan the entire account with no one left who can manage other users or
    grant access back."""
    uname = _get_session_user(request)
    if not uname:
        raise HTTPException(status_code=401, detail="Log in with your account to delete it")
    user_row = db.get_hub_user(uname)
    if not user_row:
        raise HTTPException(status_code=404, detail="Account not found")
    if user_row["role"] == "owner":
        raise HTTPException(status_code=403, detail=(
            "The owner account can't be deleted this way -- it's the only account "
            "that can manage everyone else's access. Contact support if you need help."
        ))
    db.delete_hub_user(uname)
    with _sessions_lock:
        to_remove = [sid for sid, (_, u) in _sessions.items() if u == uname]
        for sid in to_remove:
            del _sessions[sid]
    try:
        db.delete_sessions_for_user(uname)
    except Exception as exc:
        print(f"[auth] delete_sessions_for_user({uname!r}) failed after account deletion -- "
              f"sessions may not be fully revoked: {exc}", flush=True)
    print(f"[auth] account self-deleted: '{uname}'", flush=True)
    return {"ok": True}


# ── Runtime settings (agent name + AI engines) — Settings screen ────────────────
_VIDEO_ENGINES = ("sora", "veo")
_IMAGE_ENGINES = _APPROVED_ART_ENGINES  # same list as _resolve_art_engine() above -- one source of truth (2026-08-05)
_TEXT_ENGINES = ("anthropic", "grok")  # Claude stays default/live-chat brain; grok is opt-in per business_config.py's comment (2026-08-05)


def _effective_settings() -> dict:
    """Current effective values (stored override already applied to env/config) plus
    the option lists the Settings dropdowns render from."""
    daily_brief_hour_raw = db.get_setting("daily_brief_hour")
    daily_brief_enabled_raw = db.get_setting("daily_brief_enabled")
    return {
        "agent_name": business_config.AGENT_NAME_SHORT,
        "video_engine": os.getenv("AI_VIDEO_ENGINE", "sora").lower(),
        "image_engine": os.getenv("IMAGE_ENGINE", "openai").lower(),
        "text_engine": os.getenv("TEXT_ENGINE", "anthropic").lower(),
        "image_model": os.getenv("IMAGE_MODEL", "gemini-2.5-flash-image"),
        "model_primary": business_config.MODEL_PRIMARY,
        "brand_mark_data_url": db.get_setting("brand_mark_data_url"),
        # 2026-08-06: daily brief send hour is in the SHOP'S LOCAL time (see
        # _shop_now()), not UTC -- _daily_brief_loop compares against shop-local
        # hour each tick so this never drifts across DST.
        "daily_brief_hour": int(daily_brief_hour_raw) if daily_brief_hour_raw is not None else 6,
        "daily_brief_enabled": daily_brief_enabled_raw != "0",  # default on
        "options": {
            "video_engine": list(_VIDEO_ENGINES),
            "image_engine": list(_IMAGE_ENGINES),
            "text_engine": list(_TEXT_ENGINES),
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

    if "text_engine" in payload:
        v = (payload.get("text_engine") or "").lower().strip()
        if v not in _TEXT_ENGINES:
            raise HTTPException(status_code=400, detail=f"text_engine must be one of {_TEXT_ENGINES}")
        db.set_setting("text_engine", v)

    if "daily_brief_hour" in payload:
        try:
            hour = int(payload.get("daily_brief_hour"))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="daily_brief_hour must be an integer 0-23")
        if not 0 <= hour <= 23:
            raise HTTPException(status_code=400, detail="daily_brief_hour must be 0-23")
        db.set_setting("daily_brief_hour", str(hour))

    if "daily_brief_enabled" in payload:
        db.set_setting("daily_brief_enabled", "1" if payload.get("daily_brief_enabled") else "0")

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

    # 2026-08-05 Agents screen audit: this used to count everything except
    # "error" as running -- so a loop that had never fired ("started",
    # seeded at boot) or a disconnected relay ("offline") both counted as
    # "running," letting the aggregate read e.g. "10/10 running" right after
    # a redeploy while every tile on screen still showed idle/grey. "warning"
    # and "running" (a loop actively mid-run) are genuinely active, not idle
    # -- only "started" and "offline" mean nothing has happened yet.
    _ACTIVE_AGENT_STATUSES = {"ok", "warning", "running"}
    running = sum(1 for a in agents if a["built"] and a["status"] in _ACTIVE_AGENT_STATUSES)
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
                # heartbeat_name (2026-07-31): the raw db row name, e.g.
                # "build:build_coloring_product:COLOR1002" or "quality_audit" --
                # lets the Today-tab card tell a retriable failed build apart
                # from the Quality Audit loop (which gets a View Details action
                # instead) without string-parsing the human-facing title.
                "heartbeat_name": h.get("name"),
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

    # Google Calendar reminders (2026-07-18): events happening today or
    # tomorrow surface here too, not just the Calendar tab -- this is the
    # literal "reminder" behavior Scott asked for. _get_upcoming_google_calendar_events()
    # already degrades to [] when not connected/on any API error, so this
    # never needs its own try/except.
    _alerts_today = await asyncio.to_thread(_shop_today)  # 2026-08-04: shop-local, not server UTC
    today_str = _alerts_today.isoformat()
    tomorrow_str = (_alerts_today + timedelta(days=1)).isoformat()
    for e in await asyncio.to_thread(_get_upcoming_google_calendar_events, 2):
        when_date = (e.get("when") or "")[:10]
        if when_date not in (today_str, tomorrow_str):
            continue
        alerts.append({
            "severity": "info",
            "source": "google_calendar",
            "title": e.get("title", "(untitled event)"),
            "detail": ("Today" if when_date == today_str else "Tomorrow")
                       + ("" if e.get("all_day") else f" at {(e.get('when') or '')[11:16]}"),
        })

    # Product file integrity (2026-07-18): tools/audit_product_files.py checks every
    # "active" catalog product with a missing-files flag directly against Etsy
    # (get_listing_files()) before anything is treated as urgent -- an active listing
    # with a real file live on Etsy is just a missing local backup, not a problem.
    # This surfaces only the confirmed-genuinely-missing bucket (neither Etsy nor local
    # disk has anything for a live listing) -- the real "customer might be getting
    # nothing" case per CLAUDE.md's top-priority rule. Degrades to nothing if the audit
    # has never been run (no report file yet) rather than erroring.
    for item in await asyncio.to_thread(_product_file_integrity_alerts):
        alerts.append(item)

    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 3))
    return {"alerts": alerts, "count": len(alerts)}


def _file_audit_report() -> dict | None:
    """Last result written by tools/audit_product_files.py, or None if it has
    never been run. Read-only, tolerant of a missing/corrupt file."""
    vol = _FILE_ROOTS.get("volume")
    path = (vol / "file_audit_report.json") if vol else (ROOT / "data" / "file_audit_report.json")
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _file_audit_index() -> dict[str, str]:
    """product_id -> 'verified_live' | 'genuinely_missing', from the last
    tools/audit_product_files.py run. Empty (product simply absent from the
    dict) if it's never been run, or the product hasn't been audited yet --
    callers must treat that as 'unknown', not as a third verdict."""
    report = _file_audit_report()
    if not report:
        return {}
    idx: dict[str, str] = {}
    for item in report.get("verified_live", []):
        idx[item["product_id"]] = "verified_live"
    for item in report.get("genuinely_missing", []):
        idx[item["product_id"]] = "genuinely_missing"
    return idx


def _product_file_integrity_alerts() -> list[dict]:
    report = _file_audit_report()
    if not report:
        return []
    return [
        {
            "severity": "critical",
            "source": "product_file_integrity",
            "title": f"{item['product_id']} — no digital file found on Etsy or locally",
            "detail": f"{item.get('title', '')} (Etsy #{item.get('listing_id', '?')}) — expected "
                      f"{', '.join(item.get('expected_files', [])) or 'a digital file'}. Run "
                      f"tools/audit_product_files.py to re-check.",
            # 2026-07-31 (Today UX audit): listing_id previously only lived inside the
            # `detail` string -- the frontend's Needs Attention card never had a
            # structured field to key a tap-to-act sheet off of, so this alert type
            # (arguably the most severe in the app -- a customer could receive
            # nothing) could never be tapped, unlike a same-severity /api/actions
            # recommendation for the identical listing.
            "listing_id": item.get("listing_id"),
        }
        for item in report.get("genuinely_missing", [])
    ]


def _etsy_file_inventory_report() -> dict | None:
    """Last result written by tools/etsy_file_inventory.py, or None if it has
    never been run. Read-only, tolerant of a missing/corrupt file."""
    vol = _FILE_ROOTS.get("volume")
    path = (vol / "etsy_file_inventory_report.json") if vol else (ROOT / "data" / "etsy_file_inventory_report.json")
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _build_etsy_files_response() -> dict:
    """Cross-reference every Etsy-reported filename against the local file
    index (_catalog_filename_index(), via _catalog_file_url()) so the Files
    tab can offer a real download where a same-named local copy happens to
    exist, and an honest 'view on Etsy' link otherwise -- NEVER claiming a
    local copy is what's actually live on Etsy right now (Etsy's API has no
    way to confirm that; it only hands back metadata, not content)."""
    report = _etsy_file_inventory_report()
    if not report:
        return {"listings": [], "swept_at": None, "skipped": []}
    listings = []
    for entry in report.get("listings", []):
        files = []
        for f in entry.get("files", []):
            name = f.get("filename") or ""
            local_url = _catalog_file_url(name) if name else None
            size = f.get("size_bytes")
            files.append({
                "filename": name,
                "size_bytes": size,
                "size_human": _human_size(size) if isinstance(size, int) else None,
                "rank": f.get("rank"),
                "local_match": local_url is not None,
                "local_url": local_url,
            })
        listings.append({
            "product_id": entry.get("product_id"),
            "title": entry.get("title"),
            "category": entry.get("category"),
            "listing_id": entry.get("listing_id"),
            "files": files,
        })
    return {"listings": listings, "swept_at": report.get("swept_at"), "skipped": report.get("skipped", [])}


@app.get("/api/etsy-files")
async def get_etsy_files(_token: str = Depends(_auth_session_or_bearer)):
    """Every file Etsy has on record for each active listing (2026-07-19) --
    kept fresh by a daily sweep in _calendar_tasks_loop(), see
    tools/etsy_file_inventory.py. Etsy's API exposes file metadata only, never
    content, so each entry is cross-checked against local storage:
    local_match/local_url when a same-named file happens to exist locally
    (real download), otherwise the caller should link out to the listing on
    Etsy -- that's the only place the actual bytes can be pulled from."""
    return await asyncio.to_thread(_build_etsy_files_response)


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


@app.post("/api/system/run-retention-cleanup")
async def run_retention_cleanup(_token: str = Depends(_rate_limited_auth)):
    """Manual trigger for the Settings 'Data & Privacy' card -- runs the exact
    same _prune_buyer_data_retention() pass that already fires automatically
    every day inside _quality_audit_iteration(), just on demand so Scott can
    see it happen and what it did instead of it being silent/backend-only.
    Rate-limited auth since it does real file I/O, matching every other
    mutating Settings action."""
    return await asyncio.to_thread(_prune_buyer_data_retention)


@app.get("/api/tools/list")
async def get_tools_list(_token: str = Depends(_auth_session_or_bearer)):
    """Live registered AGENT_TOOLS — the Tools & Skills screen's source of
    truth. count is always len(AGENT_TOOLS), so it grows automatically
    as local_* relay tools or new tools are added; never hardcoded.
    Descriptions are run through _localize_identity() (2026-08-05) --
    several tool descriptions bake the agent/owner name in at import time
    (e.g. stage_action's OWNER_NAME f-string), so without this a runtime
    rename via Settings would leave this screen showing the old name
    forever even though the live chat/tool-calls already switched."""
    tools = [
        {
            "name": t["name"],
            "description": _localize_identity(
                t.get("description")
                or "Native Anthropic-hosted tool — executed server-side by Anthropic, not by our code."
            ),
        }
        for t in AGENT_TOOLS
    ]
    return {"tools": tools, "count": len(tools)}


_WORKFLOW_NAME_ACRONYMS = {"Qc": "QC", "Db": "DB"}


def _workflow_display_name(cmd_name: str) -> str:
    """title() doesn't know acronyms -- 'qc_sweep'.title() -> 'Qc Sweep',
    'backup_hub_db'.title() -> 'Backup Hub Db'. Fix up the known ones."""
    words = cmd_name.replace("_", " ").title().split(" ")
    return " ".join(_WORKFLOW_NAME_ACRONYMS.get(w, w) for w in words)


@app.get("/api/workflows")
async def get_workflows(_token: str = Depends(_auth_session_or_bearer)):
    """Runnable backend scripts for the Workflows screen — distinct from
    /api/tools/list (Frank's chat capabilities). Same _EXEC_COMMANDS registry
    execute_command already runs against."""
    running_scripts = {
        _EXEC_COMMANDS[cmd]["script"]
        for _pid, (proc, cmd, _started) in _LONG_RUNNING_PROCS.items()
        if cmd in _EXEC_COMMANDS and proc.poll() is None
    }
    workflows = [
        {
            "id": k,
            "name": _workflow_display_name(k),
            "description": v["description"],
            "requires_approval": v.get("requires_approval", False),
            "long_running": v.get("long_running", False),
            "timeout": v.get("timeout", 60),
            "running": v["script"] in running_scripts,
        }
        for k, v in _EXEC_COMMANDS.items()
    ]
    return {"workflows": workflows, "count": len(workflows)}


@app.post("/api/workflows/{workflow_id}/run")
async def post_workflow_run(workflow_id: str, body: dict | None = None, _token: str = Depends(_rate_limited_auth)):
    """Run a workflow. Commands without requires_approval run immediately;
    commands with requires_approval: True (currently backup_digital_products,
    backup_hub_db, listing_compliance_sweep) stage through the same
    action_queue Action Center uses. Rate-limited (2026-08-01 Workflows audit)
    since generate_coloring_pages spends real gpt-image-1 budget per call --
    every other endpoint that directly triggers paid AI generation already
    uses _rate_limited_auth; this one was the one outlier."""
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
    if done:
        # 2026-07-18: completing a todo that was synced to Google Calendar
        # must also remove the real calendar event -- see
        # _cleanup_synced_calendar_event()'s docstring. Never blocks the
        # toggle itself, which has already succeeded above.
        await asyncio.to_thread(_cleanup_synced_calendar_event, f"todo:{todo_id}")
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
    # 2026-07-18: same orphaned-event gap as toggle_todo -- deleting a
    # synced todo must also remove its real calendar event.
    await asyncio.to_thread(_cleanup_synced_calendar_event, f"todo:{todo_id}")
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


def _get_upcoming_google_calendar_events(days_ahead: int = 14) -> list[dict]:
    """Upcoming events from a connected Google Calendar, formatted for the
    Calendar tab and /api/alerts. Degrades to an empty list both when Scott
    hasn't connected Calendar yet (GoogleCalendarNotConnectedError) and on
    any real API failure -- must never break /api/cadence or /api/alerts,
    same tolerance _sales_by_listing_sync()/_compute_cogs_status() apply to
    their own Etsy calls."""
    try:
        import google_calendar_api as _gcal
    except ImportError:
        return []
    try:
        raw = _gcal.GoogleCalendarClient().list_upcoming_events(days_ahead=days_ahead)
    except _gcal.GoogleCalendarNotConnectedError:
        return []
    except Exception as exc:
        print(f"[google-calendar] event fetch failed: {exc}", flush=True)
        return []
    out = []
    for e in raw:
        start = e.get("start", {})
        when = start.get("dateTime") or start.get("date") or ""
        out.append({
            "id": e.get("id"),
            "title": e.get("summary") or "(untitled event)",
            "when": when,
            "all_day": "date" in start and "dateTime" not in start,
            "html_link": e.get("htmlLink", ""),
        })
    return out


@app.get("/api/cadence")
async def get_cadence(_token: str = Depends(_auth_session_or_bearer)):
    today = await asyncio.to_thread(_shop_today)

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

    # 2026-08-04 (Calendar screen audit): unlike the seasonal block above, this
    # never filtered past dates -- 4 of the 6 fixed tax dates are past for most
    # of the year, sitting as permanent red "OVERDUE" cards until Dec 31.
    # _sync_calendar_to_google() already filters (`if d < today: continue`);
    # this read path just never got the same treatment.
    tax = json.loads(tax_compliance_tools._get_tax_calendar())["tax_deadlines"]
    for t in tax:
        d = datetime.strptime(t["date"], "%b %d, %Y").date()
        t["date_iso"] = d.isoformat()
        t["urgency"] = seasonal_keywords._urgency(d, today)
    tax = [t for t in tax if t["date_iso"] >= today.isoformat()]
    tax.sort(key=lambda t: t["date_iso"])

    todos = await asyncio.to_thread(db.list_todos)
    due_todos = sorted(
        (t for t in todos if t.get("due_date") and not t["done"]),
        key=lambda t: t["due_date"],
    )

    google_calendar = await asyncio.to_thread(_get_upcoming_google_calendar_events)

    return {
        "seasonal": seasonal,
        "tax_deadlines": tax,
        "due_todos": due_todos,
        "checklists": _CADENCE_CHECKLISTS,
        "google_calendar": google_calendar,
    }


# ── Conversations — read-only browser/search for persisted chat_messages history ──


@app.get("/api/conversations")
async def get_conversations(q: str = "", _token: str = Depends(_auth_session_or_bearer)):
    """Session list (most-recently-active first), or — when `q` is supplied —
    a cross-session substring search instead."""
    if q.strip():
        search = await asyncio.to_thread(db.search_chat_messages, q.strip())
        return {"query": q.strip(), "results": search["results"], "truncated": search["truncated"]}
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
    # Scoped to data/ (not the repo root) so the download route below can
    # never be pointed at .env or anything else outside data/ — see
    # _catalog_file_url()/_catalog_file_abs_path(), which are the only
    # callers that resolve against this root.
    "data": ROOT / "data",
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


def _product_file_abs_path(rel: str) -> Path | None:
    """Same dual-root check as _product_file_exists(), but returns the real
    Path so a caller can actually read/upload the file (review-endpoint
    photos, create_listing's photo/file uploads to Etsy)."""
    local = _FILE_ROOTS["products"] / rel
    if local.exists():
        return local
    vol = _FILE_ROOTS.get("volume")
    if vol and (vol / rel).exists():
        return vol / rel
    return None


def _product_file_url(rel: str) -> str | None:
    """Browser-loadable URL for a product file via the existing
    /api/files/download route. That route already accepts session-cookie
    auth, so a plain <img src=...> tag in the review modal works with no
    token plumbing -- no new auth path needed."""
    if (_FILE_ROOTS["products"] / rel).exists():
        return f"/api/files/download?root=products&path={quote(rel)}&inline=1"
    vol = _FILE_ROOTS.get("volume")
    if vol and (vol / rel).exists():
        return f"/api/files/download?root=volume&path={quote(rel)}&inline=1"
    return None


# ── Catalog file resolution (2026-07-18) ──
#
# product_catalog.json's per-product "files" entries use THREE different
# conventions depending on when/how that product was added, and the original
# _product_file_exists()/_product_file_url() pair above only understands the
# first one:
#   1. Prefixed:      "data/digital_products/product_files/DP1026.pdf"
#      (digital planners) -- handled by _product_file_exists() already.
#   2. Explicit path:  "data/svg_pack/FlowerBotanical_Bundle.zip"
#      (svg_bundle) -- lives outside data/digital_products/ entirely; the old
#      prefix-strip logic left this untouched and re-joined it under
#      _FILE_ROOTS["products"] anyway, producing a nonsense double-nested
#      path that could never resolve.
#   3. Bare filename:  "coloring_set_01.zip", "DP1063_print_sizes.zip"
#      (coloring_pages, wall_art, paper_pack, uncategorized,
#      svg_3dprint_pack -- audited 2026-07-18: ~147 of 176 products' file
#      references) -- carries no directory information at all, and the real
#      location varies unpredictably per product (e.g. SS1001's 3D-print ZIP
#      lives under data/3d_print_signs/america_250/, unrelated to its own
#      filename). A cached, briefly-TTL'd basename index is the only
#      reliable way to resolve these without teaching every generator script
#      a shared directory convention retroactively.
# The three helpers below (_catalog_file_exists/_abs_path/_url) are what
# _build_products_status() and _gather_product_review() now call instead of
# the old prefix-only pair, and they're strict supersets: convention 1 keeps
# working exactly as before.

_CATALOG_INDEX_EXCLUDE_DIRS = {
    "trash", "backups", "hub_db_backups", "knowledge_base", "message_drafts",
    "reports", "financial", "performance", "printify",
}
_catalog_filename_index_cache: dict = {"built_at": 0.0, "index": {}}
_CATALOG_FILENAME_INDEX_TTL_S = 300.0


def _build_catalog_filename_index() -> dict[str, Path]:
    """Map bare basename -> first matching Path found under data/ and the
    persistent volume (if configured), skipping ops/internal directories
    that happen to live under data/ too but were never product deliverables
    (trash vault, DB backups, drafts, financial reports). Synchronous/
    blocking (an rglob walk) -- callers must run this off the event loop."""
    index: dict[str, Path] = {}
    roots = [ROOT / "data"]
    vol = _FILE_ROOTS.get("volume")
    if vol:
        roots.append(vol)
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if any(part in _CATALOG_INDEX_EXCLUDE_DIRS for part in p.relative_to(root).parts[:-1]):
                continue
            index.setdefault(p.name, p)
    return index


def _catalog_filename_index() -> dict[str, Path]:
    now = time.time()
    if now - _catalog_filename_index_cache["built_at"] > _CATALOG_FILENAME_INDEX_TTL_S:
        _catalog_filename_index_cache["index"] = _build_catalog_filename_index()
        _catalog_filename_index_cache["built_at"] = now
    return _catalog_filename_index_cache["index"]


def _catalog_file_abs_path(f: str) -> Path | None:
    """Resolve a raw product_catalog.json 'files' entry to a real Path,
    handling all three conventions documented above. Superset of
    _product_file_abs_path(): convention-1 paths delegate straight to it."""
    if f.startswith(_PRODUCT_FILES_PREFIX):
        return _product_file_abs_path(f[len(_PRODUCT_FILES_PREFIX):])
    if "/" in f:
        local = ROOT / f
        if local.exists():
            return local
        vol = _FILE_ROOTS.get("volume")
        if vol and (vol / f).exists():
            return vol / f
        return None
    return _catalog_filename_index().get(f)


def _catalog_file_exists(f: str) -> bool:
    """Superset of _product_file_exists(): convention-1 (data/digital_products/-
    prefixed) paths delegate to it directly -- not via _catalog_file_abs_path(),
    so callers/tests that patch _product_file_exists() (e.g. to fake a file's
    presence without touching disk) keep working for the legacy convention."""
    if f.startswith(_PRODUCT_FILES_PREFIX):
        return _product_file_exists(f[len(_PRODUCT_FILES_PREFIX):])
    return _catalog_file_abs_path(f) is not None


def _catalog_file_url(f: str) -> str | None:
    """Browser-loadable URL for a catalog file via /api/files/download,
    covering all three conventions _catalog_file_abs_path() does."""
    if f.startswith(_PRODUCT_FILES_PREFIX):
        return _product_file_url(f[len(_PRODUCT_FILES_PREFIX):])
    abs_path = _catalog_file_abs_path(f)
    if abs_path is None:
        return None
    vol = _FILE_ROOTS.get("volume")
    if vol and vol in abs_path.parents:
        return f"/api/files/download?root=volume&path={quote(str(abs_path.relative_to(vol)))}&inline=1"
    return f"/api/files/download?root=data&path={quote(str(abs_path.relative_to(ROOT / 'data')))}&inline=1"


# Durable overlay for product_catalog.json fields that change at runtime
# (etsy_listing_id, status) once a create_listing staged action executes, and
# (2026-07-22) for registering a WHOLLY NEW product built via the Create
# screen's "+ new one" flow for wall_art/coloring_pages (see
# _register_new_product_overlay()). product_catalog.json itself is
# git-tracked and this server never writes it, in any environment -- a raw
# write would vanish on the next Railway redeploy (fresh git checkout) and
# risk a duplicate Etsy listing on a second publish attempt, and locally it
# would pollute a git-tracked file with test/dev scratch data. Same
# volume-or-local-data-dir pattern every other durable sidecar in this file
# uses (e.g. _FILE_ROOTS["reference_images"]) -- previously this constant's
# local fallback was `None`, which made _write_product_catalog_override()
# silently patch data/product_catalog.json directly instead (fine for its
# original patch-an-existing-entry use case, but a silent no-op for
# registering a pid with no existing entry -- exactly this feature's case).
_PRODUCT_CATALOG_OVERRIDES_PATH = (
    (_FILE_ROOTS["volume"] / "product_catalog_overrides.json") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "product_catalog_overrides.json")
)


def _product_catalog_overrides() -> dict:
    """dict keyed by product_id -> {"etsy_listing_id": ..., "status": ..., "published_at": ...}
    for a patch of an existing catalog entry, or (2026-07-22) the full record
    for an `is_new_product: true` entry with no base-catalog match at all."""
    try:
        return json.loads(_PRODUCT_CATALOG_OVERRIDES_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _write_product_catalog_override(product_id: str, updates: dict) -> None:
    """Safe read-modify-write (temp file + atomic replace) into the durable
    overrides sidecar -- same file/path in every environment now (2026-07-22;
    previously local/dev with no volume patched data/product_catalog.json
    directly instead, which silently no-op'd for a product_id with no
    existing entry to patch -- see _PRODUCT_CATALOG_OVERRIDES_PATH's own
    comment)."""
    overrides = _product_catalog_overrides()
    overrides.setdefault(product_id, {}).update(updates)
    _PRODUCT_CATALOG_OVERRIDES_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _PRODUCT_CATALOG_OVERRIDES_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(overrides, indent=2))
    tmp.replace(_PRODUCT_CATALOG_OVERRIDES_PATH)


# Same volume-or-local-data-dir pattern as _PRODUCT_CATALOG_OVERRIDES_PATH --
# 2026-08-05, register_product staged action. data/listing_manifest.json is
# ALSO git-tracked (same anti-pattern this whole comment block warns about),
# but that file already has its own writer (listing_integrity_check.py's
# _write_manifest_updates(), a pre-existing separate issue not introduced
# here) -- this feature must not add a SECOND instance of writing to it.
# Without this sidecar, a product registered via register_product would
# look "mapped" until the next Railway redeploy (fresh git checkout), then
# silently revert to unmapped with no error -- reintroducing the exact
# koozie/planner bug this feature exists to close. See _get_manifest_entry()
# below, which every "is this listing mapped" call site should use instead
# of reading data/listing_manifest.json directly.
_LISTING_MANIFEST_OVERRIDES_PATH = (
    (_FILE_ROOTS["volume"] / "listing_manifest_overrides.json") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "listing_manifest_overrides.json")
)


def _listing_manifest_overrides() -> dict:
    """dict keyed by str(listing_id) -> a manifest-shaped entry (same shape
    data/listing_manifest.json's own entries use, e.g. {"dp_codes": [...],
    "type": "3d_print_physical"})."""
    try:
        return json.loads(_LISTING_MANIFEST_OVERRIDES_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _write_listing_manifest_override(listing_id, entry: dict) -> None:
    """Atomic write (temp file + replace), same idiom as
    _write_product_catalog_override()."""
    overrides = _listing_manifest_overrides()
    overrides[str(listing_id)] = entry
    _LISTING_MANIFEST_OVERRIDES_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _LISTING_MANIFEST_OVERRIDES_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(overrides, indent=2))
    tmp.replace(_LISTING_MANIFEST_OVERRIDES_PATH)


def _read_manifest_entry_sync(listing_id) -> dict | None:
    """Sync core of _get_manifest_entry() below -- checks the git-tracked
    data/listing_manifest.json first, then the durable override sidecar.
    Exists as its own plain function (not just inlined in _get_manifest_
    entry) so a caller that's already in a sync context -- _validate_
    staged_action()'s register_product branch, which runs directly inside
    a coroutine in some call paths with no asyncio.to_thread wrapper --
    can call it without needing asyncio.run() (which crashes with 'cannot
    be called from a running event loop' from exactly those call paths).
    Deliberately NOT try/except around the git-manifest read -- a genuine
    read failure must propagate to callers that distinguish "unmapped"
    from "couldn't check" (request_listing_fix()'s try/except does this).
    Only the override sidecar's read is fail-soft (via _listing_manifest_
    overrides()'s own try/except), since a missing/corrupt override file
    just means "nothing registered yet," not "something is broken."."""
    import listing_integrity_check as lic
    manifest = lic._load_json(lic.MANIFEST_PATH)
    entry = manifest.get(str(listing_id))
    if entry:
        return entry
    return _listing_manifest_overrides().get(str(listing_id))


async def _get_manifest_entry(listing_id) -> dict | None:
    """Async wrapper around _read_manifest_entry_sync() for callers already
    running on the event loop (request_listing_fix() and the autofix_
    listing_tags/autofix_listing_title chat tools both use this, as of
    2026-08-05) -- otherwise a listing registered via register_product
    looks unmapped again to whichever call site skipped the override
    fallback."""
    return await asyncio.to_thread(_read_manifest_entry_sync, listing_id)


def _blind_fix_refusal(listing_id: int, reason: str) -> dict | None:
    """Chat-tool counterpart to request_listing_fix()'s is_mapped gate
    (2026-08-05) -- the autofix_listing_tags/autofix_listing_title
    AGENT_TOOLS used to call _autofix_tags_core/_autofix_title_core
    directly with no grounding check at all, so chat could bypass the
    Listings-tab button's fix entirely and still blind-generate wrong
    text for an untracked listing. Returns an {"error": ...} dict to
    return as-is when blocked, or None when it's safe to proceed (either
    the listing is mapped, or the caller supplied a real `reason`)."""
    if reason:
        return None
    entry = asyncio.run(_get_manifest_entry(listing_id))
    if entry:
        return None
    return {
        "error": (
            f"Refused: listing {listing_id} has no entry in Frank's manifest or "
            "registration records, so there's no grounding for what this product "
            "actually is -- a blind tag/title rewrite would just produce a more "
            "confident-sounding WRONG result (see the 2026-08-05 koozie/planner "
            f"bug in ops_runbook.md). Pass a `reason` describing what's actually "
            f"wrong with this listing, or ask {business_config.OWNER_NAME} to map "
            "it first."
        )
    }


# Same volume-or-local-data-dir pattern as _PRODUCT_CATALOG_OVERRIDES_PATH,
# but a DISTINCT file -- this holds AI-generated listing content, never the
# git-tracked, hand-authored data/{id}_listing.json files (see
# _gather_product_review()'s fallback logic). The server must never write
# to a git-tracked path at runtime -- it would vanish on the next Railway
# redeploy (fresh git checkout) and silently diverge from git history.
_GENERATED_LISTING_CONTENT_PATH = (
    (_FILE_ROOTS["volume"] / "generated_listing_content.json") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "generated_listing_content.json")
)


def _generated_listing_content() -> dict:
    """dict keyed by product_id -> {title, description, tags, price,
    generated_at}. Read via the same read-with-empty-dict-fallback
    convention as _product_catalog_overrides()."""
    try:
        return json.loads(_GENERATED_LISTING_CONTENT_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _write_generated_listing_content(product_id: str, content: dict) -> None:
    """Atomic write (temp file + replace), same idiom as
    _write_product_catalog_override()."""
    all_content = _generated_listing_content()
    all_content[product_id] = {**content, "generated_at": datetime.now(timezone.utc).isoformat()}
    _GENERATED_LISTING_CONTENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _GENERATED_LISTING_CONTENT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(all_content, indent=2))
    tmp.replace(_GENERATED_LISTING_CONTENT_PATH)


# Same volume-or-local-data-dir pattern as _PRODUCT_CATALOG_OVERRIDES_PATH --
# 2026-07-26, SKU/category backfill sweep. Tracks, per product_id, whether
# its live Etsy listing's sku/taxonomy_id already match the target (product_
# id-as-sku, _resolve_category_taxonomy_id(category)) so the weekly drip
# loop below (_sku_taxonomy_backfill_loop) knows what's left to stage
# without re-fetching all ~170 listings from Etsy every run.
_SKU_TAXONOMY_BACKFILL_QUEUE_PATH = (
    (_FILE_ROOTS["volume"] / "sku_taxonomy_backfill_queue.json") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "sku_taxonomy_backfill_queue.json")
)
_BACKFILL_BATCH_SIZE = 18  # Scott-approved pace: ~15-20 listings staged/week


def _read_sku_taxonomy_backfill_queue() -> dict:
    """dict keyed by product_id -> {listing_id, category, target_sku,
    target_taxonomy_id, status}. status is one of needs_fix/ok/staged/done."""
    try:
        return json.loads(_SKU_TAXONOMY_BACKFILL_QUEUE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _write_sku_taxonomy_backfill_queue(queue: dict) -> None:
    """Atomic write (temp file + replace), same idiom as
    _write_product_catalog_override()."""
    _SKU_TAXONOMY_BACKFILL_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _SKU_TAXONOMY_BACKFILL_QUEUE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(queue, indent=2))
    tmp.replace(_SKU_TAXONOMY_BACKFILL_QUEUE_PATH)


def _build_sku_taxonomy_backfill_queue() -> dict:
    """One-time (per queue-file lifetime) sweep of every live-Etsy catalog
    entry, comparing its real sku/taxonomy_id against the target. Excludes
    `uncategorized` entries -- those need a real category identified by a
    human before any target can be computed at all (see Phase G / the
    13-product proposal delivered separately). Never raises on a single
    listing's fetch failure -- that entry is just skipped this round and
    picked up the next time the queue is rebuilt (queue files aren't
    rebuilt once they exist, so a transient failure here would otherwise
    permanently drop that listing from tracking)."""
    try:
        catalog = json.loads(Path("data/product_catalog.json").read_text())
    except OSError:
        return {}
    client = EtsyAPIClient()
    queue: dict = {}
    for entry in catalog:
        pid = entry.get("product_id")
        lid = entry.get("etsy_listing_id")
        category = entry.get("category")
        if not pid or not lid or not category or category == "uncategorized":
            continue
        target_taxonomy_id = _resolve_category_taxonomy_id(category)
        try:
            live = client.get_listing(lid)
        except Exception as exc:
            print(f"[sku-backfill] could not fetch listing {lid} ({pid}) — skipping this round: {exc}", flush=True)
            continue
        current_sku = live.get("sku")
        current_taxonomy_id = live.get("taxonomy_id")
        needs_sku = current_sku != pid
        needs_taxonomy = target_taxonomy_id is not None and current_taxonomy_id != target_taxonomy_id
        queue[pid] = {
            "listing_id": lid,
            "category": category,
            "target_sku": pid,
            "target_taxonomy_id": target_taxonomy_id,
            "status": "needs_fix" if (needs_sku or needs_taxonomy) else "ok",
        }
    return queue


def _mark_backfill_queue_done(listing_id) -> None:
    """Called right after _execute_staged_action()'s update_sku_and_category
    branch succeeds -- marks the matching queue entry `done` so the weekly
    loop stops re-staging it. Non-fatal if the queue doesn't have this
    listing (e.g. a one-off manual sku/category fix via the chat tool that
    was never part of the automated sweep)."""
    queue = _read_sku_taxonomy_backfill_queue()
    for pid, e in queue.items():
        if str(e.get("listing_id")) == str(listing_id):
            e["status"] = "done"
            _write_sku_taxonomy_backfill_queue(queue)
            return


async def _generate_product_listing_content_core(
    product_id: str, max_attempts: int = 3, engine_override: str | None = None,
) -> dict:
    """Generate grounded title/description/13 tags for product_id and save to
    the durable sidecar. Never invents a count not in _extract_grounding_
    facts()'s real facts; regenerates with feedback (max `max_attempts`) if
    the model states a mismatched count. Returns {"error": str} on any
    failure -- never raises.

    engine_override (2026-08-05): optional per-call TEXT_ENGINE choice from
    the product review modal's Advanced picker -- see _effective_text_
    engine()'s docstring."""
    engine = _effective_text_engine(engine_override)
    if engine == "anthropic" and not ANTHROPIC_KEY:
        return {"error": "ANTHROPIC_API_KEY not configured"}
    entry = _find_catalog_product(product_id)
    if entry is None:
        return {"error": f"unknown product_id: {product_id}"}
    category = entry.get("category", "")
    if category not in _CONTENT_PRICE_BY_CATEGORY:
        return {"error": f"content generation isn't supported yet for category '{category}'"}
    facts, problems = _extract_grounding_facts(product_id, entry)
    if problems:
        return {"error": "can't generate grounded content — " + "; ".join(problems)}

    ai_client = None if engine == "grok" else anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    feedback = ""
    last_problems: list[str] = []
    for attempt in range(max_attempts):
        prompt = _build_listing_content_prompt(product_id, entry, facts, feedback)
        try:
            if engine == "grok":
                raw = await asyncio.wait_for(
                    asyncio.to_thread(lambda: _grok_text(prompt, max_tokens=3000)), timeout=60.0)
            else:
                response = await asyncio.wait_for(
                    asyncio.to_thread(lambda: _anthropic_create(
                        ai_client, model=business_config.MODEL_CHEAP, max_tokens=3000,
                        messages=[{"role": "user", "content": prompt}],
                    )), timeout=60.0)
                raw = "".join(getattr(b, "text", "") for b in response.content)
        except asyncio.TimeoutError:
            return {"error": "content generation timed out"}
        except Exception as exc:
            return {"error": f"content generation failed: {exc}"}
        parsed = _extract_json_object(raw)
        if not isinstance(parsed, dict) or not all(k in parsed for k in ("title", "description", "tags")):
            feedback = "your last response wasn't valid JSON with title/description/tags — return ONLY the JSON object"
            continue
        title = str(parsed["title"]).strip()
        description = str(parsed["description"]).strip()
        tags = [_clean_tag(t) for t in parsed.get("tags", []) if str(t).strip()]
        content = {"product_id": product_id, "title": title, "description": description,
                   "tags": tags, "price": _CONTENT_PRICE_BY_CATEGORY[category]}
        # 2026-07-25: this loop used to accept anything that passed the numeric-
        # grounding checks, but title/tag structural rules (13 tags, no tag
        # duplicating a title phrase, title length, etc.) were only enforced
        # later at actual Etsy publish time via EtsyAPIClient.pre_publish_gate()
        # -- so a listing could pass generation, get saved, and only fail when
        # Scott tapped Publish (confirmed on COLOR1002: generated tags included
        # "coloring pages", duplicating the title's "Coloring Pages"). Folding
        # the same gate in here means a violation gets fed back for a retry
        # within the existing max_attempts budget instead of surfacing as a
        # dead-end at publish time.
        last_problems = (etsy_api.check_description_count_claims(description, facts)
                          + _check_generated_content_grounding(description, facts)
                          + EtsyAPIClient.pre_publish_gate(content))
        if not last_problems:
            await asyncio.to_thread(_write_generated_listing_content, product_id, content)
            return {"content": content, "attempts": attempt + 1}
        feedback = "; ".join(last_problems)

    return {"error": f"could not generate content that matches the real facts after "
                      f"{max_attempts} attempts: {'; '.join(last_problems)}"}


def _register_new_product_overlay(product_id: str, category: str, name: str,
                                   price: float | None, files: list[str],
                                   description: str = "") -> None:
    """Durably registers a brand-new product built via the Create screen's
    '+ new one' flow for wall_art/coloring_pages (2026-07-22). Reuses the
    SAME sidecar _write_product_catalog_override() already writes for
    create_listing patches -- an is_new_product record is a superset shape,
    not a new file. Called ONLY after the build subprocess exits 0 (see
    _produce_build_product()'s watcher thread) so a failed/incomplete build
    never registers a product whose files don't actually exist.

    Never publishes anything -- status is always "draft", etsy_listing_id
    always "". Publishing stays exactly as Scott-gated as every other build
    on this page (existing stage-publish flow, untouched by this function).

    Refuses to ever shadow a real base-catalog entry -- a pid collision with
    an existing product must never silently get a synthetic overlay welded
    on top. Also idempotent: calling this twice for the same already-
    registered pid (e.g. Scott taps "Regenerate" later) is a safe no-op,
    since _find_catalog_product() returns truthy for an already-registered
    is_new_product entry too."""
    if _find_catalog_product(product_id) is not None:
        return
    _write_product_catalog_override(product_id, {
        "is_new_product": True,
        "product_id": product_id,
        "name": name,
        "category": category,
        "price": price,
        "status": "draft",
        "etsy_listing_id": "",
        "files": files,
        "description": description,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "create_screen_new_code",
    })


# ── Coloring-pages theme registry (2026-07-24) — Scott: "It will be a set of
# individual coloring pages. Never to repeat a creation." A permanent,
# catalog-wide, forward-only record of every individual coloring-page SUBJECT
# ever generated via the Create screen's dynamic new-theme path. Deliberately
# NOT retroactively seeded with the 40 prompts the 2 old fixed kawaii/
# fun_basic packs already reuse across all 13 live catalog listings
# (ops_runbook.md's "all 13 real catalog products were confirmed to be
# repackagings of those same 2 packs") -- those are explicitly out of scope
# (Scott: leave the old packs exactly as they are), and seeding them in would
# poison the registry with 40 already-shipped prompts on day one that were
# never meant to count against a "never generate again" rule. Same
# volume-or-local sidecar pattern as _PRODUCT_CATALOG_OVERRIDES_PATH above --
# never a git-tracked file (a Railway redeploy is a fresh git checkout). ──

def _normalize_subject(s: str) -> str:
    """Lowercased, whitespace-collapsed form used for exact-match dedup
    comparisons against the coloring-theme registry -- catches trivial
    formatting drift (extra spaces, casing) without fuzzy/semantic matching,
    which would need a second LLM call to judge and isn't worth the cost for
    what's fundamentally a literal-repeat guard."""
    return " ".join(s.strip().lower().split())


_COLORING_THEME_REGISTRY_PATH = (
    (_FILE_ROOTS["volume"] / "coloring_theme_registry.json") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "coloring_theme_registry.json")
)


def _coloring_theme_registry() -> list[dict]:
    """Each entry: {subject, normalized, product_id, theme, created_at}.
    Tolerant of a missing/corrupt file -- an empty registry (before the
    first-ever dynamic build) is valid, not an error."""
    try:
        data = json.loads(_COLORING_THEME_REGISTRY_PATH.read_text())
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write_coloring_theme_registry(entries: list[dict]) -> None:
    """Atomic write (temp file + replace) -- same pattern as
    _write_product_catalog_override()."""
    _COLORING_THEME_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _COLORING_THEME_REGISTRY_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(entries, indent=2))
    tmp.replace(_COLORING_THEME_REGISTRY_PATH)


def _record_used_coloring_subjects(product_id: str, theme: str, subjects: list[str]) -> None:
    """Appends one registry entry per finalized subject. Called from
    _produce_build_product()'s coloring_pages branch BEFORE the build
    subprocess spawns -- a subject reserved for a build that later fails is
    simply never reused again (mildly wasteful, never wrong); writing only
    after success would leave a window where two builds kicked off close
    together could both read an empty exclude-diff and land on the same
    subject, which is the worse failure under a "never repeat, permanent,
    catalog-wide" rule."""
    registry = _coloring_theme_registry()
    now = datetime.now(timezone.utc).isoformat()
    for s in subjects:
        registry.append({
            "subject": s, "normalized": _normalize_subject(s),
            "product_id": product_id, "theme": theme, "created_at": now,
        })
    _write_coloring_theme_registry(registry)


_COLORING_SUBJECT_PROMPT = (
    "You generate individual coloring-book PAGE SUBJECTS for an Etsy coloring-pages listing. "
    "Given ONE general theme typed by the shop owner, invent the requested number of distinct "
    "page subjects, each clearly on-theme, each meaningfully different from every other subject "
    "in this batch AND from every subject in the 'already used -- never repeat these' list "
    "(a genuinely different specific scene/subject, not just a reworded synonym of one already "
    "used). Each subject is a short, concrete single-page scene description, 5-20 words, e.g. "
    "'A sleepy fox curled under an oak tree'. "
    'Respond with ONLY a JSON object of the exact shape {"subjects": ["...", "..."]} '
    "containing exactly the requested number of strings -- no commentary, no markdown fence."
)
_COLORING_REGISTRY_PROMPT_CAP = 400  # most recent registry entries sent as "already used"
# context -- the registry grows unbounded over years of use; this bounds prompt/token cost
# while still covering everything recent. The defensive post-check in
# _resolve_coloring_subjects() below checks the FULL registry (cheap in-memory set, no
# token cost) so nothing older can slip through just because it aged out of this prompt
# window -- belt-and-suspenders per CLAUDE.md: code-verified gates, not trust in AI output.


def _generate_coloring_subjects(theme: str, exclude: list[str], count: int,
                                 already_accepted: list[str] | None = None) -> list[str]:
    """One Anthropic call: expand Scott's one-line theme into `count` distinct,
    on-theme coloring-page subjects, steered away from `exclude` (recent slice
    of the durable cross-listing registry) and from `already_accepted` (this
    call's own earlier accepted subjects, used by _resolve_coloring_subjects()'s
    retry pass). Returns [] on no API key / empty theme / call failure /
    unparseable response -- caller decides what an empty result means."""
    if not ANTHROPIC_KEY or not theme.strip() or count <= 0:
        return []
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    exclude_block = "\n".join(f"- {s}" for s in exclude[-_COLORING_REGISTRY_PROMPT_CAP:]) or "(none yet)"
    accepted_block = "\n".join(f"- {s}" for s in (already_accepted or [])) or "(none)"
    dynamic_block = (
        f"\n\nTHEME: {theme}\nREQUESTED COUNT: {count}\n\n"
        f"ALREADY USED -- NEVER REPEAT THESE:\n{exclude_block}\n\n"
        f"ALREADY ACCEPTED THIS BATCH -- must also differ from these:\n{accepted_block}"
    )
    try:
        msg = _anthropic_create(
            client, model=business_config.MODEL_CHEAP, max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": _COLORING_SUBJECT_PROMPT, "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": dynamic_block},
                ],
            }],
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[coloring-subjects] generation call failed: {exc}", flush=True)
        return []
    raw = msg.content[0].text.strip()
    parsed = _extract_json_object(raw)
    subjects = parsed.get("subjects") if isinstance(parsed, dict) else None
    if not isinstance(subjects, list):
        return []
    return [str(s).strip() for s in subjects if str(s).strip()]


def _resolve_coloring_subjects(theme: str) -> tuple[list[str], str | None]:
    """Turns Scott's one-line theme into exactly generate_coloring_pages.
    NEW_THEME_SET_SIZE subjects (30, as of 2026-08-08), never repeating
    anything in the durable, catalog-wide, forward-only registry (2026-07-24,
    "never repeat a creation"). Belt-and-suspenders: even though the prompt is given the
    exclude list, this ALSO code-verifies every returned subject against the
    FULL registry (normalized exact match) and silently drops anything that
    slips past the LLM, retrying once for the shortfall. Returns
    (subjects, error) -- error is None on success, else subjects is []."""
    if not ANTHROPIC_KEY:
        return [], ("Frank's AI provider isn't configured (ANTHROPIC_API_KEY unset), so it "
                     "can't turn a theme into subjects yet.")
    import generate_coloring_pages as gcp
    n_needed = gcp.NEW_THEME_SET_SIZE
    registry = _coloring_theme_registry()
    used_normalized = {e["normalized"] for e in registry}
    exclude_prompt = [e["subject"] for e in registry]
    accepted: list[str] = []
    accepted_normalized: set[str] = set()

    for _attempt in range(2):  # 1 initial + 1 retry for any shortfall
        shortfall = n_needed - len(accepted)
        if shortfall <= 0:
            break
        batch = _generate_coloring_subjects(theme, exclude=exclude_prompt, count=shortfall,
                                             already_accepted=accepted)
        for s in batch:
            norm = _normalize_subject(s)
            if norm in used_normalized or norm in accepted_normalized:
                continue  # the LLM slipped and repeated something -- drop it, don't trust it
            accepted.append(s)
            accepted_normalized.add(norm)
            if len(accepted) == n_needed:
                break

    if len(accepted) < n_needed:
        return [], (f"Could only generate {len(accepted)}/{n_needed} distinct new subjects for "
                     f"'{theme}' without repeating something already used shop-wide. Try a "
                     f"broader or different theme.")
    return accepted, None


# File-ownership index for the Files screen (2026-07-22) — lets /api/files
# group each file under "Attached to a Listing" vs "Not Attached to a
# Listing" using the REAL product catalog instead of guessing from the
# filename. Root cause it fixes: the old filename-regex grouping
# (_productKeyFromPath in frank_hud_mockup.py) mistook coloring_pages'
# internal per-page theme IDs (CB001, CB002, ... generate_coloring_pages.py)
# for individual products, while the real deliverable ZIPs customers
# actually receive (coloring_set_01.zip etc., genuinely attached to live
# listings) didn't match the regex at all and fell into a generic
# leftover bucket. Reuses _build_products_status() -- the exact same
# resolution /api/products already uses -- so the Files and Products
# screens can never disagree about what's real or attached.
_FILE_OWNER_INDEX_TTL_S = 300.0
_file_owner_index_cache: dict = {"built_at": 0.0, "index": {}}


def _build_file_owner_index() -> dict[str, dict]:
    """basename -> {"product_id", "category", "attached"} for every file any
    catalog product (or is_new_product overlay) lists. `attached` is true
    only when the product has a real Etsy listing_id (draft/unpublished
    products resolve to attached=False, same as the Products screen)."""
    try:
        catalog = json.loads(Path("data/product_catalog.json").read_text())
    except OSError:
        catalog = []
    overrides = _product_catalog_overrides()
    rows = _build_products_status(catalog, _catalog_file_exists, overrides)
    index: dict[str, dict] = {}
    for row in rows:
        for fs in row.get("files", []):
            index.setdefault(fs["name"], {
                "product_id": row["id"],
                "category": row.get("category", "uncategorized"),
                "attached": bool(row.get("listing_id")),
            })
    return index


def _file_owner_index() -> dict[str, dict]:
    now = time.time()
    if now - _file_owner_index_cache["built_at"] > _FILE_OWNER_INDEX_TTL_S:
        _file_owner_index_cache["index"] = _build_file_owner_index()
        _file_owner_index_cache["built_at"] = now
    return _file_owner_index_cache["index"]


# Staged listing photos awaiting Scott's approve/reject in the Action Center —
# durable under the Railway volume when mounted (survives redeploys, same reason
# "volume" exists above), else a local data/ dir for dev.
_FILE_ROOTS["staged_photos"] = (
    (_FILE_ROOTS["volume"] / "staged_photos") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "staged_photos")
)

# Studio tab — generated videos (video_generator.py's own OUTPUT_DIR), source images
# a user uploads before generation, and videos staged for Etsy/Instagram/Facebook
# review. (2026-07-25) Previously hardcoded to the ephemeral local dir on the theory
# that these are "regeneratable working files" — but staged_videos/{listing_id}/...
# is the sole copy of a video between "Stage for Approval" and Scott actually
# approving it in the Action Center, a window that can span a redeploy; when it did,
# the staged DB action survived but the file didn't, and approval hit a
# FileNotFoundError (main.py's listing_video action-apply handler). videos/ and
# studio_uploads/ carry the same risk for generate-now-post-to-social-later. Same
# fix as COLOR1001 (coloring pages) and the same reason staged_photos is durable.
_FILE_ROOTS["videos"] = (
    (_FILE_ROOTS["volume"] / "social" / "videos") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "social" / "videos")
)
_FILE_ROOTS["studio_uploads"] = (
    (_FILE_ROOTS["volume"] / "social" / "studio_uploads") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "social" / "studio_uploads")
)
_FILE_ROOTS["staged_videos"] = (
    (_FILE_ROOTS["volume"] / "social" / "staged_videos") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "social" / "staged_videos")
)
# SVG Converter tool output — regeneratable (re-run the conversion any time), not
# source-of-truth product assets, so same non-durable local dir as studio_uploads.
_FILE_ROOTS["svg_conversions"] = ROOT / "data" / "social" / "svg_conversions"
# Lifestyle Photo Generator output — same regeneratable-working-file reasoning as
# svg_conversions above. Passed products still go through the existing staged_photos
# root + Action Center approval, not this one — this is the standalone generation
# tool's own scratch output before anything is staged for a real listing.
_FILE_ROOTS["lifestyle_photos"] = ROOT / "data" / "social" / "lifestyle_photos"

# deep_research tool output (2026-07-25) — durable under the volume, same
# reasoning as reference_images below: a saved research report is a real
# artifact Scott may want to come back to later, not scratch/regeneratable
# working output. Registering the key here also makes every report
# browsable/downloadable from the Files screen for free via the GET
# /api/files scan below, with zero new UI needed.
_FILE_ROOTS["deep_research"] = (
    (_FILE_ROOTS["volume"] / "deep_research") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "deep_research")
)

# Reference Photos library (2026-07-22 Create-screen redesign) — Scott's own
# curated inspiration/style-reference images, organized by product category.
# Durable under the volume (same reasoning as staged_photos above: a real
# library built up over time, not scratch/regeneratable output) with a local
# data/ fallback for dev. Registering the key here also makes the library
# browsable/downloadable from the Files screen for free via the GET /api/files
# scan below.
_FILE_ROOTS["reference_images"] = (
    (_FILE_ROOTS["volume"] / "reference_images") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "reference_images")
)
_REFERENCE_IMAGES_META_PATH = (
    (_FILE_ROOTS["volume"] / "reference_images_meta.json") if "volume" in _FILE_ROOTS
    else (ROOT / "data" / "reference_images_meta.json")
)
# Matches the Create screen's 7 category tiles plus a general catch-all for
# "just inspiration, not tied to one line" — kept in sync manually with the
# frontend's tile list (frank_hud_mockup.py).
_REFERENCE_IMAGE_CATEGORIES = {
    "digital_planner", "wall_art", "coloring_pages", "sticker_pack",
    "svg_3dprint_pack", "sublimation", "3d_print_physical", "general",
}

# Every _FILE_ROOTS key now assembled. This is the subset the Files screen is
# actually designed to expose for browsing/downloading -- shared by list_files()
# and GET /api/files/download so the two can never disagree. "data" and
# "hub_db_backups" are deliberately excluded: they exist in _FILE_ROOTS for
# narrow, non-browsing purposes only (root="data" for _catalog_file_url()'s
# generated download links; "hub_db_backups" for a one-off internal retrieval),
# and iterating them here would leak data/hub.db, hub_db_backups/'s user PII
# export, data/financial/, and data/printify/ with no owner gate -- the exact
# bug closed 2026-07-31 (see the Files-screen ops_runbook entry).
_BROWSABLE_FILE_ROOTS = {
    "backups": "Backups", "volume": "Saved Files (persistent)", "products": "Product Files",
    "staged_photos": "Staged Photos (pending approval)",
    "videos": "Generated Videos", "studio_uploads": "Studio Uploads",
    "staged_videos": "Staged Videos (pending approval)",
    "svg_conversions": "SVG Conversions",
    "lifestyle_photos": "Lifestyle Photos",
    "reference_images": "Reference Photos",
}


def _is_known_catalog_data_path(target: Path) -> bool:
    """For GET /api/files/download?root=data — only allow paths this app itself
    hands out via _catalog_file_url(), never an arbitrary path under data/.
    Reuses _catalog_file_abs_path()'s own basename resolution (the same
    function that generates those links) so this can never drift from what
    URLs the app actually produces; a hub.db or data/financial/ path has no
    matching catalog basename and correctly resolves to False."""
    resolved = _catalog_file_abs_path(target.name)
    return resolved is not None and resolved.resolve() == target.resolve()


def _reference_images_meta() -> list[dict]:
    """List of {id, filename, category, description, size, size_human,
    uploaded_at}, newest first. Tolerant of a missing/corrupt file — an empty
    library is a valid, common state, never an error."""
    try:
        data = json.loads(_REFERENCE_IMAGES_META_PATH.read_text())
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write_reference_images_meta(entries: list[dict]) -> None:
    """Atomic write (temp file + replace) — same pattern as
    _write_product_catalog_override, avoids a torn read on a crash mid-write."""
    _REFERENCE_IMAGES_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _REFERENCE_IMAGES_META_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(entries, indent=2))
    tmp.replace(_REFERENCE_IMAGES_META_PATH)


def _reference_image_style_notes(ref_id: str) -> tuple[str | None, str | None]:
    """Resolve a Reference Photos library id into style-guidance text a
    generation prompt can use (main.py's Reference Photos card previously
    stored uploads with nothing downstream reading them -- see the "library
    only right now" disclaimer this replaces, 2026-07-30).

    Runs ONE vision call (image_gen.describe_reference_style()) per reference
    image, ever -- the resulting caption is cached onto the meta entry
    (style_notes field) so re-using the same reference on a later build never
    re-spends the vision API call. Returns (notes, error); never both set.
    """
    entries = _reference_images_meta()
    entry = next((e for e in entries if e.get("id") == ref_id), None)
    if entry is None:
        return None, f"reference image {ref_id!r} not found"
    cached = entry.get("style_notes")
    if cached:
        return cached, None
    img_path = _FILE_ROOTS["reference_images"] / entry["filename"]
    if not img_path.is_file():
        return None, f"reference image file missing on this deploy: {entry['filename']}"
    try:
        import image_gen
        notes = image_gen.describe_reference_style(img_path)
    except Exception as exc:  # noqa: BLE001 — a captioning failure shouldn't block the build
        return None, f"could not analyze reference image: {exc}"
    if not notes:
        return None, "reference image analysis returned nothing"
    entry["style_notes"] = notes
    _write_reference_images_meta(entries)
    return notes, None


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
        owner_index = _file_owner_index()
        refimg_categories = {m["filename"]: m.get("category") for m in _reference_images_meta()}
        # Iterating _BROWSABLE_FILE_ROOTS instead of _FILE_ROOTS means a root added
        # later for a narrow, non-browsing purpose (e.g. "data" for
        # _catalog_file_url(), "hub_db_backups" for a one-off retrieval) never
        # appears here unless someone deliberately adds it to that allowlist.
        # Iterating _FILE_ROOTS directly used to leak both of those roots' real
        # contents (hub.db, PII exports in hub_db_backups/, data/financial/,
        # data/printify/) under a wrong "Product Files" fallback label with no
        # owner gate -- closed 2026-07-31, same allowlist GET /api/files/download
        # now enforces.
        for root_key, label in _BROWSABLE_FILE_ROOTS.items():
            root_path = _FILE_ROOTS.get(root_key)
            if root_path is None or not root_path.exists():
                continue
            files = []
            for p in sorted(root_path.rglob("*")):
                if not p.is_file():
                    continue
                ext = p.suffix.lower()
                if ext == ".log":
                    # Plain-text build-script output -- never a customer-facing
                    # deliverable or a listing image, so it's excluded entirely
                    # rather than cluttering a real product's file group
                    # (Scott, 2026-07-22).
                    continue
                stat = p.stat()
                rel = str(p.relative_to(root_path))
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
                if root_key == "products":
                    entry["catalog_match"] = owner_index.get(p.name)
                elif root_key == "reference_images":
                    entry["category"] = refimg_categories.get(p.name)
                files.append(entry)
            files.sort(key=lambda f: f["modified"], reverse=True)
            groups.append({"root": root_key, "label": label, "files": files})
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
    # 2026-07-31: _resolve_in_root() alone only blocks path traversal within a
    # root -- it accepts ANY key present in _FILE_ROOTS, including "hub_db_backups"
    # (no legitimate external caller at all) and "data" (legitimate only for the
    # specific catalog files _catalog_file_url() generates, never an arbitrary path
    # under data/). Same allowlist list_files() now enforces, so a non-owner session
    # that already knows/guesses this URL can't reach data/hub.db, hub_db_backups/'s
    # PII export, data/financial/, or data/printify/ by root key alone.
    if root not in _BROWSABLE_FILE_ROOTS and root != "data":
        raise HTTPException(status_code=403, detail="This file root is not downloadable")
    target = _resolve_in_root(root, path)
    if root == "data" and not _is_known_catalog_data_path(target):
        raise HTTPException(status_code=403, detail="This file is not a registered product download")
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
    if target.is_dir():
        # Covers path="." (resolves to vroot itself, which slips past the
        # traversal guard above since target == vroot) and the case where an
        # earlier upload's target.parent.mkdir() auto-created a directory that
        # a later upload's path then collides with. Without this,
        # target.write_bytes(body) below raises an unhandled IsADirectoryError
        # -> bare 500 (2026-08-13 functional audit; api-conventions.md: "never
        # a bare exception that becomes a generic 500").
        raise HTTPException(status_code=400, detail=f"path '{rel}' is an existing directory, not a file")
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


_PII_TOOLS = frozenset({
    "get_orders",
    "draft_review_replies",  # 2026-08-06: returns real buyer-authored review text
    "get_review_themes",  # 2026-08-06: returns real buyer-authored review excerpts
})  # tools whose results include a real buyer name or their own written words


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
    _MAX_TOOL_ROUND_TRIPS = 6
    # 2026-07-19: previously `for _ in range(6)` with nothing after it -- if the 6th
    # round's response was ITSELF tool_use, the tools still got executed and their
    # results appended as a user-role message (below), but the loop then just ended
    # with no further LLM call to consume them. history was left ending in user-role,
    # so the NEXT real user turn appended a SECOND consecutive user-role message on
    # top -- Anthropic rejects that with a 400 ("roles must alternate"), permanently
    # wedging that session's chat, the same failure class as the 2026-06-17 incident
    # (ops_runbook.md) this loop's tool_result-append ordering was already hardened
    # against, just via a different trigger that incident's fix didn't cover. Fix:
    # one extra guaranteed round with no `tools` param offered at all, so the model
    # literally cannot request more tool use and must close out in plain text --
    # `final.stop_reason` can then never be "tool_use" on that round, so history is
    # guaranteed to end on an assistant-role turn no matter how the cap is hit.
    for round_idx in range(_MAX_TOOL_ROUND_TRIPS + 1):
        allow_tools = round_idx < _MAX_TOOL_ROUND_TRIPS
        queue: asyncio.Queue = asyncio.Queue()

        def _produce(allow_tools: bool = allow_tools) -> None:
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
                stream_kwargs = dict(
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
                    messages=history,
                )
                if allow_tools:
                    stream_kwargs["tools"] = _tools_with_cache()
                with ai_client.messages.stream(**stream_kwargs) as stream:
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
                elif block.name == "execute_command":
                    # 2026-07-19: several _EXEC_COMMANDS entries (check_new_orders,
                    # send_order_notifications, check_buyer_messages) return real
                    # buyer PII in their stdout, but the wrapper tool name here is
                    # always "execute_command" -- checking only `block.name` against
                    # _PII_TOOLS could never catch these. Check the underlying
                    # command's own "contains_pii" flag instead.
                    cmd_name = (block.input or {}).get("command")
                    if _EXEC_COMMANDS.get(cmd_name, {}).get("contains_pii"):
                        pii_tools_used.add(cmd_name)
                try:
                    if block.name in _RELAY_TOOLS:
                        result = await _dispatch_to_relay(block.name, block.input)
                    elif block.name in _LOCAL_STAGED_TOOLS:
                        result = await _stage_local_action(block.name, block.input)
                    else:
                        try:
                            result = await asyncio.wait_for(
                                asyncio.to_thread(_execute_agent_tool, block.name, block.input),
                                timeout=_TOOL_DISPATCH_TIMEOUT_S,
                            )
                        except asyncio.TimeoutError:
                            # The worker thread itself can't be killed (asyncio can't
                            # cancel a running thread), but the turn is freed instead
                            # of hanging forever -- same tradeoff _dispatch_to_relay
                            # already makes for the relay path.
                            result = {
                                "error": (
                                    f"{block.name} did not finish within "
                                    f"{int(_TOOL_DISPATCH_TIMEOUT_S)}s and was abandoned"
                                )
                            }
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

    # Should be unreachable: the final round_idx (_MAX_TOOL_ROUND_TRIPS) never offers
    # `tools`, so its stop_reason can never be "tool_use" and the loop above always
    # returns from inside that round. Kept as a defensive fallback only.
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
