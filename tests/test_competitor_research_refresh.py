"""
Tests for Frank upgrade Wave 4, item C3 (2026-07-17): a monthly refresh job
for data/knowledge_base/competitor_research_2026.md.

The file was a static one-off snapshot (written May 2026, no refresh
mechanism) that Frank's chat agent reads on demand via read_knowledge_base_
doc -- meaning it silently fed increasingly stale market claims into every
conversation that touched pricing/positioning. _run_competitor_research_
refresh() combines two real signals: C1's live Etsy search_listings() data
for this shop's own core search terms, and the Anthropic-hosted web_search
tool (called directly in a single messages.create(), same tool already
wired into AGENT_TOOLS for chat) for broader trend/algorithm signal a pure
Etsy search can't see. Scheduled monthly (the 8th) in _calendar_tasks_loop,
alongside the existing 1st/15th-of-month jobs.

Run: python tests/test_competitor_research_refresh.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_competitor_refresh_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "competitor-refresh-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_report_response(report_body: str):
    block = MagicMock()
    block.type = "text"
    block.text = f"===BEGIN_REPORT===\n{report_body}\n===END_REPORT==="
    resp = MagicMock()
    resp.content = [block]
    return resp


def test_registered_in_calendar_tasks_manual_trigger():
    import inspect
    src = inspect.getsource(server.run_calendar_tasks_now)
    check("_run_competitor_research_refresh" in src,
          "the manual /api/calendar-tasks/run trigger must include the new job")


def test_calendar_loop_gates_on_day_8():
    import inspect
    src = inspect.getsource(server._calendar_tasks_loop)
    check("today.day == 8" in src, "the competitor research refresh must be gated to a specific day")
    check("_run_competitor_research_refresh" in src, "the calendar loop must call the refresh function")
    check("last_competitor_research" in src, "must track its own last-ran date like the other calendar tasks")


def test_skips_cleanly_without_anthropic_key():
    with patch.object(server, "ANTHROPIC_KEY", ""):
        result = server._run_competitor_research_refresh()
    check(result == "skipped -- ANTHROPIC_API_KEY not configured", f"got: {result}")


def test_pulls_real_comparable_data_and_writes_report():
    search_calls = []

    def fake_search(self, keywords, limit=10, sort_on="score", min_price=None, max_price=None):
        search_calls.append(keywords)
        return {"results": [
            {"listing_id": 1, "title": f"Sample listing for {keywords}", "price": {"amount": 999, "divisor": 100}, "tags": ["tag1", "tag2"]},
        ]}

    captured = {}

    def fake_anthropic_create(client, **kwargs):
        captured["kwargs"] = kwargs
        return _fake_report_response("# Refreshed Report\n\nResearch date: July 2026\n\nSome new content.")

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "competitor_research_2026.md"
        fake_path.write_text("# Old Report\n\nResearch date: May 2026\n\nStale content.", encoding="utf-8")
        with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
             patch.object(server, "_COMPETITOR_RESEARCH_PATH", fake_path), \
             patch.object(server.EtsyAPIClient, "search_listings", fake_search), \
             patch.object(server, "_anthropic_create", fake_anthropic_create):
            result = server._run_competitor_research_refresh()

        check("refreshed competitor_research_2026.md" in result, f"got: {result}")
        check(len(search_calls) == len(server._COMPETITOR_RESEARCH_SEARCH_TERMS),
              f"expected one search per configured term, got calls: {search_calls}")
        new_content = fake_path.read_text(encoding="utf-8")
        check("Refreshed Report" in new_content, f"the file must be overwritten with the new report, got: {new_content[:200]}")
        check("Old Report" not in new_content, "the stale report must be replaced, not appended")

    # The web_search hosted tool must actually be enabled on the call
    tools_used = captured["kwargs"].get("tools", [])
    check(any(t.get("name") == "web_search" for t in tools_used),
          f"web_search must be enabled on the refresh call, got tools: {tools_used}")
    # The real Etsy data must reach the prompt
    user_content = captured["kwargs"]["messages"][0]["content"]
    check("REAL LIVE ETSY DATA" in user_content, f"got: {user_content[:300]}")
    check("Sample listing for" in user_content, "the actual search results must be in the prompt")


def test_missing_markers_leaves_file_untouched_and_errors_cleanly():
    def fake_search(self, keywords, limit=10, sort_on="score", min_price=None, max_price=None):
        return {"results": []}

    def fake_bad_response(client, **kwargs):
        block = MagicMock()
        block.type = "text"
        block.text = "I refuse to use the markers you asked for."
        resp = MagicMock()
        resp.content = [block]
        return resp

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "competitor_research_2026.md"
        fake_path.write_text("# Original\n\nUnchanged.", encoding="utf-8")
        with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
             patch.object(server, "_COMPETITOR_RESEARCH_PATH", fake_path), \
             patch.object(server.EtsyAPIClient, "search_listings", fake_search), \
             patch.object(server, "_anthropic_create", fake_bad_response):
            result = server._run_competitor_research_refresh()

        check("error" in result, f"a missing-markers response must error cleanly, not crash, got: {result}")
        check(fake_path.read_text(encoding="utf-8") == "# Original\n\nUnchanged.",
              "the file must not be touched when the model response can't be parsed")


def test_etsy_search_failure_is_non_fatal_and_still_produces_a_report():
    def failing_search(self, keywords, limit=10, sort_on="score", min_price=None, max_price=None):
        raise RuntimeError("simulated network failure")

    def fake_anthropic_create(client, **kwargs):
        return _fake_report_response("# Report despite search failure")

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "competitor_research_2026.md"
        fake_path.write_text("# Old", encoding="utf-8")
        with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
             patch.object(server, "_COMPETITOR_RESEARCH_PATH", fake_path), \
             patch.object(server.EtsyAPIClient, "search_listings", failing_search), \
             patch.object(server, "_anthropic_create", fake_anthropic_create):
            result = server._run_competitor_research_refresh()

        check("refreshed" in result, f"an Etsy search failure must not block the whole refresh, got: {result}")
        check("Report despite search failure" in fake_path.read_text(encoding="utf-8"), "the report must still be written")


def test_anthropic_call_failure_errors_cleanly_without_writing():
    def fake_search(self, keywords, limit=10, sort_on="score", min_price=None, max_price=None):
        return {"results": []}

    def failing_anthropic(client, **kwargs):
        raise RuntimeError("simulated Anthropic outage")

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "competitor_research_2026.md"
        fake_path.write_text("# Original, must survive", encoding="utf-8")
        with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
             patch.object(server, "_COMPETITOR_RESEARCH_PATH", fake_path), \
             patch.object(server.EtsyAPIClient, "search_listings", fake_search), \
             patch.object(server, "_anthropic_create", failing_anthropic):
            result = server._run_competitor_research_refresh()

        check("error" in result, f"got: {result}")
        check(fake_path.read_text(encoding="utf-8") == "# Original, must survive",
              "a Claude API failure must leave the existing file untouched")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("COMPETITOR RESEARCH REFRESH TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COMPETITOR RESEARCH REFRESH TESTS OK — calendar-loop wiring (day-8 gate + manual "
          "trigger registration), clean skip without an API key, real comparable data reaching "
          "the prompt with web_search enabled, the file only overwritten on a well-formed "
          "response, and non-fatal degradation on both an Etsy search failure and a Claude "
          "API failure.")


if __name__ == "__main__":
    run()
