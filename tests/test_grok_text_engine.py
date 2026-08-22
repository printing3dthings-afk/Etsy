#!/usr/bin/env python3
"""
Tests for the 2026-08-05 Grok/xAI text-provider integration: the
TEXT_ENGINE setting, _effective_text_engine()'s normalize/degrade rule,
the _xai_create()/_xai_client()/_grok_text() provider seam (mirrors
_anthropic_create() but for xAI's OpenAI-SDK-compatible endpoint), the
per-generation engine_override threaded through
_generate_product_listing_content_core() and its endpoint, and the
Settings screen's persistence path for text_engine.

Covers:
  - _effective_text_engine(): default, explicit grok w/ key, degrade to
    anthropic w/o key, override precedence over env, override degrade
  - _xai_create(): circuit-breaker gating, success path (breaker + usage
    logging), failure path records the breaker, an unclassified exception
    does NOT get recorded as a breaker failure (matches _anthropic_create's
    narrow except clause)
  - _grok_text(): default cheap model, custom model override, stripped
    response content
  - _generate_product_listing_content_core(): engine_override="grok" uses
    the grok path and never touches anthropic; engine_override="grok"
    without XAI_KEY degrades to anthropic
  - POST /api/products/{id}/generate-listing-content: rejects an invalid
    engine value, passes a valid override through to the core function
  - POST/GET /api/settings: text_engine validates against _TEXT_ENGINES,
    persists, and applies live to os.environ["TEXT_ENGINE"]

Self-contained -- no live Etsy/Anthropic/xAI calls. Run:
  python tests/test_grok_text_engine.py
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_grok_text_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "grok-text-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import httpx  # noqa: E402
import openai  # noqa: E402
import business_config  # noqa: E402
import main as server  # noqa: E402
from resilience import CircuitBreaker  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


class _FakeBreakerDB:
    """In-memory circuit-breaker store, same shape as tests/test_resilience.py's
    _FakeDB -- isolates each test's breaker state from the real (tempfile)
    sqlite-backed db.py so tests can't leak breaker state into each other."""

    def __init__(self):
        self._rows: dict[str, dict] = {}

    def get_circuit_breaker_state(self, dep_name: str):
        return self._rows.get(dep_name)

    def set_circuit_breaker_state(self, dep_name, state, consecutive_failures, opened_at):
        self._rows[dep_name] = {
            "state": state,
            "consecutive_failures": consecutive_failures,
            "opened_at": opened_at,
        }


def _fresh_xai_breaker(**kwargs) -> CircuitBreaker:
    return CircuitBreaker("test_xai", db_module=_FakeBreakerDB(), **kwargs)


def _fake_api_connection_error() -> openai.APIConnectionError:
    req = httpx.Request("POST", "https://api.x.ai/v1/chat/completions")
    return openai.APIConnectionError(request=req)


def _fake_grok_chat_response(text: str):
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = MagicMock(prompt_tokens=5, completion_tokens=7)
    return resp


# ── _effective_text_engine() ────────────────────────────────────────────

def test_effective_text_engine_defaults_to_anthropic():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("TEXT_ENGINE", None)
        engine = server._effective_text_engine()
    check(engine == "anthropic", f"expected default 'anthropic', got {engine!r}")


def test_effective_text_engine_respects_env_grok_when_key_present():
    with patch.object(server, "XAI_KEY", "fake-xai-key"), \
         patch.dict(os.environ, {"TEXT_ENGINE": "grok"}):
        engine = server._effective_text_engine()
    check(engine == "grok", f"expected 'grok' when env selects it and a key is present, got {engine!r}")


def test_effective_text_engine_degrades_grok_to_anthropic_without_key():
    with patch.object(server, "XAI_KEY", ""), \
         patch.dict(os.environ, {"TEXT_ENGINE": "grok"}):
        engine = server._effective_text_engine()
    check(engine == "anthropic", f"expected degrade to 'anthropic' with no XAI_KEY, got {engine!r}")


def test_effective_text_engine_override_takes_precedence_over_env():
    with patch.object(server, "XAI_KEY", "fake-xai-key"), \
         patch.dict(os.environ, {"TEXT_ENGINE": "anthropic"}):
        engine = server._effective_text_engine(override="grok")
    check(engine == "grok", f"expected the per-call override to win over the env default, got {engine!r}")


def test_effective_text_engine_override_degrades_without_key():
    with patch.object(server, "XAI_KEY", ""), \
         patch.dict(os.environ, {"TEXT_ENGINE": "anthropic"}):
        engine = server._effective_text_engine(override="grok")
    check(engine == "anthropic", f"expected override degrade to 'anthropic' with no key, got {engine!r}")


def test_effective_text_engine_override_none_falls_back_to_env():
    with patch.dict(os.environ, {"TEXT_ENGINE": "anthropic"}):
        engine = server._effective_text_engine(override=None)
    check(engine == "anthropic", f"expected a None override to fall back to the env default, got {engine!r}")


# ── _xai_create() ───────────────────────────────────────────────────────

def test_xai_create_raises_when_breaker_open():
    breaker = _fresh_xai_breaker(failure_threshold=1, cooldown_seconds=300.0)
    breaker.record_failure()  # trips it open
    client = MagicMock()
    with patch.object(server, "_xai_breaker", breaker):
        try:
            server._xai_create(client, model="grok-x", messages=[{"role": "user", "content": "hi"}])
            check(False, "expected CircuitBreakerOpenError when the breaker is open")
        except server.CircuitBreakerOpenError:
            pass
    check(not client.chat.completions.create.called, "an open breaker must short-circuit before ever calling the API")


def test_xai_create_success_records_breaker_success_and_logs_usage():
    breaker = _fresh_xai_breaker(failure_threshold=5)
    client = MagicMock()
    fake_resp = _fake_grok_chat_response("hello")
    client.chat.completions.create.return_value = fake_resp
    logged = {}

    def fake_log(caller, model, usage):
        logged["caller"] = caller
        logged["model"] = model
        logged["usage"] = usage

    with patch.object(server, "_xai_breaker", breaker), \
         patch.object(server, "_log_xai_usage", side_effect=fake_log):
        result = server._xai_create(client, model="grok-x", messages=[{"role": "user", "content": "hi"}])
    check(result is fake_resp, "should return the raw API response on success")
    row = breaker._load()
    check(row["state"] == "closed", f"a successful call should leave the breaker closed, got {row['state']!r}")
    check(row["consecutive_failures"] == 0, f"a success should not leave stale failures, got {row['consecutive_failures']}")
    check(logged.get("model") == "grok-x", f"usage log should record the model used, got {logged}")
    check(logged.get("usage") is fake_resp.usage, "usage log should pass through the raw usage object")


def test_xai_create_retryable_failure_records_breaker_and_reraises():
    breaker = _fresh_xai_breaker(failure_threshold=5)
    client = MagicMock()
    client.chat.completions.create.side_effect = _fake_api_connection_error()
    with patch.object(server, "_xai_breaker", breaker):
        try:
            server._xai_create(client, model="grok-x", messages=[])
            check(False, "expected APIConnectionError to propagate")
        except openai.APIConnectionError:
            pass
    row = breaker._load()
    check(row["consecutive_failures"] == 1, f"a retryable failure should be recorded on the breaker, got {row['consecutive_failures']}")


def test_xai_create_unclassified_exception_does_not_touch_breaker():
    # Mirrors _anthropic_create()'s narrow except clause: only the three
    # named openai exception types record a breaker failure. An
    # unclassified error (e.g. a bug in caller-supplied kwargs) should
    # propagate without being mistaken for a provider outage.
    breaker = _fresh_xai_breaker(failure_threshold=5)
    client = MagicMock()
    client.chat.completions.create.side_effect = ValueError("bad kwargs")
    with patch.object(server, "_xai_breaker", breaker):
        try:
            server._xai_create(client, model="grok-x", messages=[])
            check(False, "expected ValueError to propagate")
        except ValueError:
            pass
    row = breaker._load()
    check(row is None or row["consecutive_failures"] == 0,
          f"an unclassified exception must not be recorded as a breaker failure, got {row}")


# ── _grok_text() ─────────────────────────────────────────────────────────

def test_grok_text_uses_cheap_model_by_default_and_strips_content():
    captured = {}

    def fake_xai_create(client, **kwargs):
        captured.update(kwargs)
        return _fake_grok_chat_response("  hello world  ")

    with patch.object(server, "_xai_client", return_value=MagicMock()), \
         patch.object(server, "_xai_create", side_effect=fake_xai_create):
        result = server._grok_text("a prompt")
    check(result == "hello world", f"expected stripped content, got {result!r}")
    check(captured.get("model") == business_config.GROK_MODEL_CHEAP,
          f"expected the default cheap model, got {captured.get('model')!r}")
    check(captured.get("messages") == [{"role": "user", "content": "a prompt"}],
          f"expected the prompt wrapped as a single user message, got {captured.get('messages')}")


def test_grok_text_honors_custom_model_override():
    captured = {}

    def fake_xai_create(client, **kwargs):
        captured.update(kwargs)
        return _fake_grok_chat_response("ok")

    with patch.object(server, "_xai_client", return_value=MagicMock()), \
         patch.object(server, "_xai_create", side_effect=fake_xai_create):
        server._grok_text("a prompt", model="grok-custom-9")
    check(captured.get("model") == "grok-custom-9", f"expected the custom model to be used, got {captured.get('model')!r}")


def test_grok_text_empty_content_returns_empty_string_not_none():
    def fake_xai_create(client, **kwargs):
        return _fake_grok_chat_response(None)

    with patch.object(server, "_xai_client", return_value=MagicMock()), \
         patch.object(server, "_xai_create", side_effect=fake_xai_create):
        result = server._grok_text("a prompt")
    check(result == "", f"a None content should normalize to an empty string, got {result!r}")


# ── _generate_product_listing_content_core() engine routing ─────────────

_FAKE_ENTRY = {"category": "digital_planner", "name": "Test Planner", "files": []}
_FAKE_FACTS = {"product_id": "DP9999", "category": "digital_planner", "name": "Test Planner", "pdf_pages": 12}
_FILLER = (" Filled with fillable fields, hyperlinked tabs, and a kawaii cover design "
           "so it's ready to use the moment you download it.")
_GOOD_JSON = json.dumps({
    "title": "Digital Planner 2026 Undated, GoodNotes iPad, Instant Download",
    "description": "Pages: 12 total in this planner. A full grounded description." + _FILLER * 3,
    "tags": [f"tag{i}" for i in range(13)],
})


def _fake_anthropic_response(text: str):
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


def test_generator_uses_grok_engine_when_override_grok_and_key_present():
    with patch.object(server, "XAI_KEY", "fake-xai-key"), \
         patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_find_catalog_product", return_value=dict(_FAKE_ENTRY)), \
         patch.object(server, "_extract_grounding_facts", return_value=(dict(_FAKE_FACTS), [])), \
         patch.object(server, "_grok_text", return_value=_GOOD_JSON) as mock_grok, \
         patch.object(server, "_anthropic_create") as mock_anthropic, \
         patch.object(server, "_write_generated_listing_content") as mock_write:
        result = asyncio.run(server._generate_product_listing_content_core(
            "DP9999", max_attempts=3, engine_override="grok"))
    check("content" in result, f"expected success via grok, got {result}")
    check(mock_grok.called, "expected _grok_text to be called for the grok engine path")
    check(not mock_anthropic.called, "must not call anthropic when engine_override selects grok")
    check(mock_write.called, "a successful grok generation must still write to the durable sidecar")


def test_generator_grok_override_without_key_degrades_to_anthropic():
    with patch.object(server, "XAI_KEY", ""), \
         patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_find_catalog_product", return_value=dict(_FAKE_ENTRY)), \
         patch.object(server, "_extract_grounding_facts", return_value=(dict(_FAKE_FACTS), [])), \
         patch.object(server, "_grok_text") as mock_grok, \
         patch.object(server, "_anthropic_create", return_value=_fake_anthropic_response(_GOOD_JSON)) as mock_anthropic, \
         patch.object(server, "_write_generated_listing_content") as mock_write:
        result = asyncio.run(server._generate_product_listing_content_core(
            "DP9999", max_attempts=3, engine_override="grok"))
    check("content" in result, f"expected success via the anthropic fallback, got {result}")
    check(mock_anthropic.called, "expected fallback to anthropic when XAI_KEY is missing")
    check(not mock_grok.called, "must not call grok when the key is missing (should have degraded to anthropic)")
    check(mock_write.called, "the anthropic-fallback generation must still write to the sidecar")


def test_generator_no_override_still_defaults_to_anthropic():
    with patch.object(server, "XAI_KEY", "fake-xai-key"), \
         patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.dict(os.environ, {"TEXT_ENGINE": "anthropic"}), \
         patch.object(server, "_find_catalog_product", return_value=dict(_FAKE_ENTRY)), \
         patch.object(server, "_extract_grounding_facts", return_value=(dict(_FAKE_FACTS), [])), \
         patch.object(server, "_grok_text") as mock_grok, \
         patch.object(server, "_anthropic_create", return_value=_fake_anthropic_response(_GOOD_JSON)) as mock_anthropic, \
         patch.object(server, "_write_generated_listing_content"):
        result = asyncio.run(server._generate_product_listing_content_core("DP9999", max_attempts=3))
    check("content" in result, f"expected success via the shop-wide default, got {result}")
    check(mock_anthropic.called, "with no override and TEXT_ENGINE=anthropic, must use anthropic")
    check(not mock_grok.called, "must not call grok when neither override nor env selects it")


# ── POST /api/products/{id}/generate-listing-content ─────────────────────

def test_endpoint_rejects_invalid_engine_value():
    async def _run():
        try:
            await server.generate_product_listing_content("DP9999", body={"engine": "bogus"}, _token="test")
            return None
        except Exception as e:  # noqa: BLE001
            return e

    exc = asyncio.run(_run())
    check(exc is not None, "expected an exception for an invalid engine value")
    check(getattr(exc, "status_code", None) == 400, f"expected HTTP 400, got {getattr(exc, 'status_code', None)}")


def test_endpoint_absent_engine_passes_none_override():
    captured = {}

    async def fake_core(product_id, engine_override=None):
        captured["engine_override"] = engine_override
        return {"content": {"title": "t", "description": "d", "tags": [], "price": 1.0}, "attempts": 1}

    with patch.object(server, "_generate_product_listing_content_core", side_effect=fake_core), \
         patch.object(server, "_gather_product_review", return_value={"product_id": "DP9999", "has_content": True}):
        asyncio.run(server.generate_product_listing_content("DP9999", body=None, _token="test"))
    check(captured.get("engine_override") is None, f"expected no override when body omits engine, got {captured}")


def test_endpoint_passes_valid_engine_override_through_to_core():
    captured = {}

    async def fake_core(product_id, engine_override=None):
        captured["product_id"] = product_id
        captured["engine_override"] = engine_override
        return {"content": {"title": "t", "description": "d", "tags": [], "price": 1.0}, "attempts": 1}

    with patch.object(server, "_generate_product_listing_content_core", side_effect=fake_core), \
         patch.object(server, "_gather_product_review", return_value={"product_id": "DP9999", "has_content": True}):
        result = asyncio.run(server.generate_product_listing_content("DP9999", body={"engine": "grok"}, _token="test"))
    check(captured.get("product_id") == "DP9999", f"expected the product_id to reach the core call, got {captured}")
    check(captured.get("engine_override") == "grok", f"expected engine_override='grok' passed through, got {captured}")
    check(result.get("product_id") == "DP9999", f"expected the fresh review payload returned, got {result}")


def test_endpoint_engine_value_is_normalized_case_and_whitespace():
    captured = {}

    async def fake_core(product_id, engine_override=None):
        captured["engine_override"] = engine_override
        return {"content": {"title": "t", "description": "d", "tags": [], "price": 1.0}, "attempts": 1}

    with patch.object(server, "_generate_product_listing_content_core", side_effect=fake_core), \
         patch.object(server, "_gather_product_review", return_value={"product_id": "DP9999"}):
        asyncio.run(server.generate_product_listing_content("DP9999", body={"engine": "  GROK  "}, _token="test"))
    check(captured.get("engine_override") == "grok", f"expected normalized 'grok', got {captured}")


# ── /api/settings text_engine persistence ────────────────────────────────

def test_post_settings_rejects_invalid_text_engine():
    async def _run():
        try:
            await server.post_settings_endpoint({"text_engine": "not-a-real-engine"}, _token="test")
            return None
        except Exception as e:  # noqa: BLE001
            return e

    exc = asyncio.run(_run())
    check(exc is not None, "expected an exception for an invalid text_engine value")
    check(getattr(exc, "status_code", None) == 400, f"expected HTTP 400, got {getattr(exc, 'status_code', None)}")


def test_post_settings_text_engine_grok_persists_and_applies_live():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("TEXT_ENGINE", None)
        asyncio.run(server.post_settings_endpoint({"text_engine": "grok"}, _token="test"))
        applied = os.environ.get("TEXT_ENGINE")
    check(applied == "grok", f"expected POST /api/settings to apply TEXT_ENGINE=grok live via os.environ, got {applied!r}")
    stored = server.db.get_setting("text_engine")
    check(stored == "grok", f"expected the setting to persist in the db, got {stored!r}")


def test_get_settings_exposes_text_engine_options():
    settings = asyncio.run(server.get_settings_endpoint(_token="test"))
    check(settings.get("options", {}).get("text_engine") == ["anthropic", "grok"],
          f"expected the two known text engines listed as options, got {settings.get('options')}")
    check("text_engine" in settings, f"expected the current text_engine value in the payload, got {settings.keys()}")


# ── runner ────────────────────────────────────────────────────────────────

def run() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ran = 0
    for fn in tests:
        try:
            fn()
            ran += 1
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised an unexpected error:\n" + traceback.format_exc())
    if _failures:
        print("GROK TEXT ENGINE TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        sys.exit(1)
    print(f"GROK TEXT ENGINE TESTS OK — {ran} tests passed (_effective_text_engine normalize/degrade, "
          f"_xai_create breaker+logging, _grok_text model/content handling, per-generation engine_override "
          f"routing through the content generator and its endpoint, and text_engine settings persistence -- "
          f"no live xAI/Anthropic/Etsy calls).")


if __name__ == "__main__":
    run()
