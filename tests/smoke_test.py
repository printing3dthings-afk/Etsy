#!/usr/bin/env python3
"""
Smoke test for the OnBrandCraftz "Frank" server — the minimum gate that must pass
before code auto-deploys to production.

Why this exists: main.py auto-deploys to Railway on every push, there is no other
test coverage, and the most common way to break production is an import-time crash
(a bad import, a NameError at module scope, a syntax error in a tool module that
main.py imports). Importing the server module here catches exactly that class of
failure — e.g. it would have caught the `from tools import ...` top-level import
bug that nearly shipped with the browser tools.

Deliberately dependency-light and secret-free: it imports the app and inspects the
in-memory tool registry + dispatcher. It does NOT start the ASGI server, fire
startup background loops, launch a browser, or make any network/API call — so it
runs fast and needs no API keys.

Run locally:  python tests/smoke_test.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = pass, non-zero = fail (prints what broke).
"""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Replicate main.py's own runtime sys.path (script dir + repo/tools) so its bare
# sibling imports (`import business_config`, `import browser_automation`, …) resolve.
for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)


def main() -> int:
    # 1. Import the server module — the load-bearing check. Any syntax error,
    #    bad import, or module-scope crash in main.py OR any module it imports
    #    (browser_automation, video_understanding, business_config, db, …) fails here.
    try:
        import main as server
    except Exception:
        print("SMOKE FAIL: importing the server module raised:", file=sys.stderr)
        traceback.print_exc()
        return 1

    failures: list[str] = []

    # 2. Build id is set (so /health can confirm which build is live).
    if not getattr(server, "_BUILD_ID", ""):
        failures.append("_BUILD_ID is empty/missing")

    # 3. The agent tool registry built and has a sane size.
    tools = getattr(server, "AGENT_TOOLS", None)
    if not isinstance(tools, list) or len(tools) < 25:
        failures.append(f"AGENT_TOOLS missing or too small: {type(tools).__name__} "
                        f"len={len(tools) if isinstance(tools, list) else 'n/a'}")
    names = {t.get("name") for t in tools} if isinstance(tools, list) else set()

    # 4. The capabilities we've wired this session are actually registered.
    required = {
        "render_page", "screenshot_url", "check_browser_status",
        "check_etsy_search_rank", "watch_video",
    }
    missing = required - names
    if missing:
        failures.append(f"expected agent tools not registered: {sorted(missing)}")

    # 5. The tool dispatcher exists and is callable.
    if not callable(getattr(server, "_execute_agent_tool", None)):
        failures.append("_execute_agent_tool is not callable")

    # 6. Every tool schema is well-formed (name + input_schema, except hosted tools
    #    like web_search which are typed and have no input_schema).
    if isinstance(tools, list):
        for t in tools:
            if "type" in t:  # hosted/server-side tool (e.g. web_search)
                continue
            if not t.get("name") or "input_schema" not in t:
                failures.append(f"malformed tool schema: {t.get('name') or t}")
                break

    if failures:
        print("SMOKE FAIL:", file=sys.stderr)
        for f in failures:
            print("  -", f, file=sys.stderr)
        return 1

    print(f"SMOKE OK — build {server._BUILD_ID}, {len(tools)} agent tools registered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
