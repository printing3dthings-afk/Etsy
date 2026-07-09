"""Business identity config — de-hardcodes the shop name/owner/agent name so this
codebase can be deployed as a fresh, independent instance for a different business.

Every default below matches OnBrandCraftz's current literal values, so an instance
with no new env vars set renders byte-identical output to before this module existed.
"""

import os

BUSINESS_NAME = os.getenv("BUSINESS_NAME", "OnBrandCraftz")
OWNER_NAME = os.getenv("OWNER_NAME", "Scott")
AGENT_NAME = os.getenv("AGENT_NAME", "Fucking Frank")
# Shorter form used in user-facing error toasts where the full AGENT_NAME reads
# oddly (e.g. "Fucking Frank's AI provider..."). Set AGENT_NAME_SHORT in .env for
# any deployment where AGENT_NAME doesn't start with "Fucking ".
AGENT_NAME_SHORT = os.getenv("AGENT_NAME_SHORT", "Frank")
BUSINESS_DESCRIPTION = os.getenv(
    "BUSINESS_DESCRIPTION",
    "an Etsy shop selling kawaii\ndigital planners, sticker packs, and 3D-print SVG files",
)

# ── LLM model tiers ───────────────────────────────────────────────────────────
# Centralized so the model choice is ONE edit, not ~8 scattered string literals,
# and so a deployment can change models by setting an env var (no code change).
#
# Frank's brain is Claude (kept — it leads on multi-turn tool use + policy
# adherence, and the long system prompt is built around Claude prompt caching).
# OpenAI is used ONLY for Whisper STT + TTS (see /api/voice in main.py) — it is
# NOT a reasoning brain, so there is no second brain to consolidate away.
#
# MODEL_PRIMARY is Frank's brain. Upgraded 2026-07-02 to Sonnet 5 (newer, stronger
# reasoning/tool-use at comparable price). If a deployment's Anthropic account does
# NOT have claude-sonnet-5 access, override back with MODEL_PRIMARY=claude-sonnet-4-6
# in the env — instant rollback, no code change. Same pattern lets any deployment
# pick its own tier.
MODEL_PRIMARY = os.getenv("MODEL_PRIMARY", "claude-sonnet-5")            # main agent + routine drafting
MODEL_CHEAP   = os.getenv("MODEL_CHEAP",   "claude-haiku-4-5-20251001")  # cheap/simple/high-volume tasks
MODEL_HARD    = os.getenv("MODEL_HARD",    "claude-opus-4-8")            # reserved for hard reasoning (opt-in)
