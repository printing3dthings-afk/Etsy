"""
Tests for Frank upgrade Wave 4, item B3 retargeted (2026-07-17).

Original B3 plan targeted tools/etsy_listing_tools.py's optimize_listing_
content, discovered during B1 to be dead code (the whole module is never
imported by the live server). Retargeted to the real live gap:
_autofix_description_core (main.py) was "Deterministic (no AI call)" --
it only ever prepended one canned Gate-6 sentence for wall-art listings,
never touching the actual hook/prose -- unlike title/tags, which already
call Claude via _autofix_title_core/_generate_tags_for_listings.

Added a second path: when Gate 6 doesn't apply (not wall_art, or already
compliant) AND a `reason` is given (a Scott reject or a conversion-diagnosis
finding), a real Claude call rewrites ONLY the opening hook (first 1-2
sentences) -- the same narrow-blast-radius pattern Gate 6 itself uses,
touching the hook only and never the WHAT'S INCLUDED/factual body, to avoid
any Cardinal Rule risk of an LLM inventing or dropping a factual claim
mid-description.

Run: python tests/test_description_hook_autofix.py
"""
import asyncio
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_desc_hook_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "desc-hook-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


_WALL_ART_LISTING = {
    "title": "Botanical Wall Art Print",
    "description": "Some description that never mentions download or printable at all.\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\nWHAT'S INCLUDED\n━━━━━━━━━━━━━━━━━━━━━━━━\nA JPG file.",
    "state": "active",
}

_PLANNER_LISTING = {
    "title": "Digital Planner 2026 Undated, GoodNotes iPad, Instant Download",
    "description": "Meh hook that doesn't hook anyone.\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n📦 WHAT'S INCLUDED\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "✅ 143 pages, 328 stickers, 11 sheets.",
    "state": "active",
}


def _fake_anthropic_response(text: str):
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


# ── Gate 6 path (regression: must be fully unchanged) ───────────────────────
def test_gate6_path_unchanged_when_wall_art_noncompliant_no_reason():
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"):
        result = asyncio.run(server._autofix_description_core(999001, listing=dict(_WALL_ART_LISTING)))
    check("action_id" in result, f"Gate 6 fix should stage successfully, got: {result}")
    check(result.get("added_line") == server._WALL_ART_GATE6_LINE,
          f"Gate 6 path must still return added_line, got: {result}")
    queued = server.db.get_action(result["action_id"])
    check(queued["payload"]["description"].startswith(server._WALL_ART_GATE6_LINE),
          "the staged description must start with the exact Gate 6 line")


def test_gate6_path_wins_even_when_a_reason_is_also_given():
    # Gate 6 must always take priority when it applies -- a reject-reason or
    # diagnosis finding must not divert a wall-art Gate-6 case into the new
    # LLM path; this specific case is already cheap, exact, and well-tested.
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"):
        with patch("anthropic.Anthropic") as mock_anthropic:
            result = asyncio.run(server._autofix_description_core(
                999002, listing=dict(_WALL_ART_LISTING), reason="make it punchier"
            ))
            check(not mock_anthropic.called, "Gate 6 case must never call the LLM, even with a reason given")
    check(result.get("added_line") == server._WALL_ART_GATE6_LINE, f"expected the Gate 6 fix, got: {result}")


def test_gate6_compliant_and_no_reason_still_skips():
    compliant = dict(_WALL_ART_LISTING)
    compliant["description"] = "Instant download printable wall art already compliant.\n\nRest of description."
    result = asyncio.run(server._autofix_description_core(999003, listing=compliant))
    check(result.get("skipped") is True, f"an already-compliant wall-art listing with no reason must skip, got: {result}")


def test_non_wall_art_and_no_reason_still_skips():
    result = asyncio.run(server._autofix_description_core(999004, listing=dict(_PLANNER_LISTING)))
    check(result.get("skipped") is True, f"a non-wall-art listing with no reason must skip, got: {result}")
    check("not a wall_art listing" in result.get("reason", ""), f"got: {result}")


# ── New LLM hook-rewrite path ────────────────────────────────────────────────
def test_llm_hook_rewrite_fires_for_non_wall_art_with_reason():
    fake_hook = "The new, punchier hook that carries the keyword up front."
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"):
        with patch("anthropic.Anthropic") as mock_anthropic_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = _fake_anthropic_response(fake_hook)
            mock_anthropic_cls.return_value = mock_client
            with patch.object(server, "_anthropic_create", return_value=_fake_anthropic_response(fake_hook)):
                result = asyncio.run(server._autofix_description_core(
                    999005, listing=dict(_PLANNER_LISTING), reason="hook doesn't carry the primary keyword"
                ))
    check("action_id" in result, f"expected a successful stage, got: {result}")
    check(result.get("new_hook") == fake_hook, f"expected the generated hook returned, got: {result}")
    queued = server.db.get_action(result["action_id"])
    new_desc = queued["payload"]["description"]
    check(new_desc.startswith(fake_hook), f"staged description must start with the new hook, got: {new_desc[:100]!r}")
    check("328 stickers" in new_desc, "the factual WHAT'S INCLUDED body must be preserved byte-for-byte")
    check(queued["payload"]["before_description"] == _PLANNER_LISTING["description"],
          "before_description must carry the real original text for the Action Center diff view")


def test_llm_hook_rewrite_only_touches_hook_never_the_body():
    original_body = _PLANNER_LISTING["description"].split("\n\n", 1)[1]
    fake_hook = "A totally different hook sentence."
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"):
        with patch.object(server, "_anthropic_create", return_value=_fake_anthropic_response(fake_hook)):
            result = asyncio.run(server._autofix_description_core(
                999006, listing=dict(_PLANNER_LISTING), reason="test reason"
            ))
    queued = server.db.get_action(result["action_id"])
    new_desc = queued["payload"]["description"]
    check(new_desc.endswith(original_body), "everything after the hook must be byte-identical to the original")


def test_llm_hook_rewrite_requires_a_blank_line_separator():
    no_separator = {"title": "Some Product", "description": "Just one giant blob with no blank line anywhere.", "state": "active"}
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"):
        result = asyncio.run(server._autofix_description_core(999007, listing=no_separator, reason="test"))
    check("error" in result, f"a description with no isolable hook must refuse, not guess, got: {result}")


def test_llm_hook_rewrite_requires_anthropic_key():
    with patch.object(server, "ANTHROPIC_KEY", ""):
        result = asyncio.run(server._autofix_description_core(
            999008, listing=dict(_PLANNER_LISTING), reason="test"
        ))
    check(result.get("error") == "ANTHROPIC_API_KEY not configured", f"got: {result}")


def test_llm_hook_rewrite_empty_description_errors_cleanly():
    empty = {"title": "Some Product", "description": "", "state": "active"}
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"):
        result = asyncio.run(server._autofix_description_core(999009, listing=empty, reason="test"))
    check("error" in result, f"an empty description with a reason must error cleanly, not crash, got: {result}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("DESCRIPTION HOOK AUTOFIX TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("DESCRIPTION HOOK AUTOFIX TESTS OK — Gate 6 path fully unchanged (including "
          "always winning over a reason-driven LLM rewrite when it applies), the new "
          "LLM hook-rewrite path fires correctly for non-wall-art/already-compliant "
          "listings given a reason, preserves the factual body byte-for-byte, and "
          "handles missing-separator/missing-key/empty-description edge cases cleanly.")


if __name__ == "__main__":
    run()
