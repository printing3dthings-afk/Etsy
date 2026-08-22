"""
Tests for the "why Frank suggested this" reasoning panel (2026-07-18,
implementing the competitive-audit report's finding: _apply_conversion_
fixes_core already computed a real "finding -> fix" reason string per
autofix, but it was discarded before ever reaching the staged action's
payload or the Approvals screen -- Scott saw WHAT changed, never WHY).

Checks:
  1. _autofix_title_core / _autofix_tags_core stage payload["reason"] when
     called with a non-empty reason, and omit the key entirely when called
     with none (no fabricated reason for a plain "just refresh this" call).
  2. _autofix_description_core's Gate 6 path always sets a reason (it fires
     on a deterministic rule, so it has one even with no reason argument);
     its LLM hook-rewrite path (which requires reason to be non-empty to
     run at all) passes the given reason through unchanged.
  3. frank_hud_mockup.py's _actionPreviewHtml renders a reason block when
     payload.reason is present, via the _actionPreviewBody split.

Run: python tests/test_action_reasoning_panel.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_reasonpanel_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "reasonpanel-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_anthropic_response(text: str):
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


_LISTING = {
    "listing_id": 5551001,
    "title": "Some Listing Title",
    "price": {"amount": 1499, "divisor": 100},
    "tags": ["a", "b"],
    "description": "Opening hook line.\n\n━━━━━━━━━━━━━━━━━━━━━━━━\nWHAT'S INCLUDED\n━━━━━━━━━━━━━━━━━━━━━━━━\nA PDF.",
    "state": "active",
}

_WALL_ART_LISTING = {
    "listing_id": 5551002,
    "title": "Botanical Wall Art Print",
    "price": {"amount": 799, "divisor": 100},
    "description": "No download/printable signal anywhere in here.\n\n━━━━━━━━━━━━━━━━━━━━━━━━\nWHAT'S INCLUDED\n━━━━━━━━━━━━━━━━━━━━━━━━\nA JPG.",
    "state": "active",
}


def test_title_fix_stages_reason_when_given():
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"):
        with patch.object(server, "_anthropic_create", return_value=_fake_anthropic_response("New Title Here")):
            result = asyncio.run(server._autofix_title_core(
                _LISTING["listing_id"], listing=dict(_LISTING), reason="Title buries the keyword → move it up"
            ))
    check("action_id" in result, f"expected a successful stage, got: {result}")
    queued = server.db.get_action(result["action_id"])
    check(queued["payload"].get("reason") == "Title buries the keyword → move it up",
          f"expected the reason threaded into payload, got: {queued['payload'].get('reason')!r}")


def test_title_fix_omits_reason_key_when_none_given():
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"):
        with patch.object(server, "_anthropic_create", return_value=_fake_anthropic_response("New Title Here")):
            result = asyncio.run(server._autofix_title_core(_LISTING["listing_id"], listing=dict(_LISTING)))
    check("action_id" in result, f"expected a successful stage, got: {result}")
    queued = server.db.get_action(result["action_id"])
    check("reason" not in queued["payload"],
          f"no reason was given -- payload should not fabricate one, got: {queued['payload']}")


def test_tags_fix_stages_reason_when_given():
    fake_tags = [f"tag {i}" for i in range(13)]
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_generate_tags_for_listings", return_value=[{"tags": fake_tags}]):
        result = asyncio.run(server._autofix_tags_core(
            _LISTING["listing_id"], listing=dict(_LISTING), reason="Only 2/13 tags → fill all slots"
        ))
    if "action_id" not in result:
        check(False, f"expected a successful stage, got: {result}")
        return
    queued = server.db.get_action(result["action_id"])
    check(queued["payload"].get("reason") == "Only 2/13 tags → fill all slots",
          f"expected the reason threaded into payload, got: {queued['payload'].get('reason')!r}")


def test_tags_fix_omits_reason_key_when_none_given():
    fake_tags = [f"tag {i}" for i in range(13)]
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_generate_tags_for_listings", return_value=[{"tags": fake_tags}]):
        result = asyncio.run(server._autofix_tags_core(_LISTING["listing_id"], listing=dict(_LISTING)))
    if "action_id" not in result:
        check(False, f"expected a successful stage, got: {result}")
        return
    queued = server.db.get_action(result["action_id"])
    check("reason" not in queued["payload"],
          f"no reason was given -- payload should not fabricate one, got: {queued['payload']}")


def test_gate6_path_always_has_a_reason_even_with_none_given():
    result = asyncio.run(server._autofix_description_core(_WALL_ART_LISTING["listing_id"], listing=dict(_WALL_ART_LISTING)))
    check("action_id" in result, f"expected a successful stage, got: {result}")
    queued = server.db.get_action(result["action_id"])
    reason = queued["payload"].get("reason", "")
    check("Gate 6" in reason, f"Gate 6 path fires on a deterministic rule -- expected that rule named in the reason, got: {reason!r}")


def test_llm_hook_rewrite_passes_given_reason_through():
    fake_hook = "A punchier new hook."
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"):
        with patch.object(server, "_anthropic_create", return_value=_fake_anthropic_response(fake_hook)):
            result = asyncio.run(server._autofix_description_core(
                _LISTING["listing_id"], listing=dict(_LISTING), reason="hook doesn't carry the primary keyword"
            ))
    check("action_id" in result, f"expected a successful stage, got: {result}")
    queued = server.db.get_action(result["action_id"])
    check(queued["payload"].get("reason") == "hook doesn't carry the primary keyword",
          f"expected the given reason passed through unchanged, got: {queued['payload'].get('reason')!r}")


def test_frontend_renders_reason_block_when_present():
    hud_path = ROOT / "tools" / "api_server" / "frank_hud_mockup.py"
    source = hud_path.read_text(encoding="utf-8")
    check("function _actionPreviewBody(a)" in source,
          "_actionPreviewHtml's body should be split into _actionPreviewBody so a reason block can be prepended uniformly")
    check("p.reason" in source and "💡 Why:" in source,
          "the reason block should check payload.reason and render a labeled 'Why' block")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("ACTION REASONING PANEL TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("ACTION REASONING PANEL TESTS OK — title/tags/description autofix handlers thread "
          "a real diagnosis reason into the staged payload when given (and never fabricate one "
          "when not), and the Approvals screen renders it via _actionPreviewHtml/_actionPreviewBody.")


if __name__ == "__main__":
    run()
