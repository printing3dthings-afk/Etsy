"""
Tools & Skills screen audit fixes (2026-08-05).

Covers:
- /api/tools/list now runs every tool description through
  _localize_identity() before returning it. Some AGENT_TOOLS descriptions
  (e.g. stage_action) bake the owner name in at Python import time as an
  f-string; the live chat system prompt + tool-call payloads already
  localize per-request via the same helper (_tools_with_cache()), but this
  screen previously built its display list straight from the raw
  AGENT_TOOLS entries -- so after a runtime rename via Settings, the
  screen kept showing the OLD name forever even though the model was
  already receiving the new one.
- The tool-count nav badge (badge-tools) was removed -- unlike every other
  badge in the nav (Tasks, Calendar, Actions), it counted something that
  never signals anything needing attention (a static total tool count).

Same monkeypatch style as tests/test_workflows_screen.py: direct module
attribute patch, not a mocking framework.
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_tools_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "tools-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_tools_list_localizes_owner_name_after_runtime_rename():
    baked_owner = server._IDENTITY_BAKED[2]
    with patch.object(server.business_config, "OWNER_NAME", "Jamie"):
        result = asyncio.run(server.get_tools_list(_token="test"))
    stage_action = next(t for t in result["tools"] if t["name"] == "stage_action")
    check(baked_owner not in stage_action["description"],
          f"expected the baked-in owner name {baked_owner!r} to be gone after "
          f"a runtime rename, got: {stage_action['description']!r}")
    check("Jamie" in stage_action["description"],
          f"expected the NEW owner name 'Jamie' in stage_action's description, "
          f"got: {stage_action['description']!r}")


def test_tools_list_unchanged_when_no_rename_happened():
    result = asyncio.run(server.get_tools_list(_token="test"))
    stage_action = next(t for t in result["tools"] if t["name"] == "stage_action")
    check(server._IDENTITY_BAKED[2] in stage_action["description"],
          f"with no rename, the original baked-in owner name should still be "
          f"present, got: {stage_action['description']!r}")


def test_tools_list_count_matches_registry_length():
    result = asyncio.run(server.get_tools_list(_token="test"))
    check(result["count"] == len(server.AGENT_TOOLS),
          f"count must always equal len(AGENT_TOOLS), got {result['count']} "
          f"vs {len(server.AGENT_TOOLS)}")
    check(len(result["tools"]) == result["count"],
          f"tools list length must match count, got {len(result['tools'])} vs {result['count']}")


def test_no_badge_tools_markup_in_hud():
    import frank_hud_mockup
    html = frank_hud_mockup._FRANK_HUD_MOCKUP
    check("badge-tools" not in html,
          "badge-tools was removed (2026-08-05 audit: it counted a static, "
          "never-actionable total tool count, unlike every other nav badge) "
          "-- no reference to it should remain in the HUD markup")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("TOOLS SCREEN TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("TOOLS SCREEN TESTS OK — /api/tools/list localizes owner/agent names "
          "after a runtime rename, and the non-actionable tool-count badge is gone.")


if __name__ == "__main__":
    run()
