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
import re as _re
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

# The core agent tools the dispatcher (`_execute_agent_tool`, main.py ~2350–2708) handles.
# Pinning these guards against a core tool being silently dropped/renamed out of the
# AGENT_TOOLS registry during a refactor — the registry could otherwise stay len>=25 (padded
# by the browser/video tools) while a core tool vanished, and nothing here would notice.
# NOTE (honest limit): this checks the REGISTRY only. It does NOT prove the dispatcher still
# ROUTES each name — the flat if-chain isn't introspectable. A follow-up (HANDLERS dict) is
# what makes routing itself testable. Keep this list in sync when core tools are added/removed.
EXPECTED_CORE_TOOLS = {
    "get_metrics", "list_listings", "get_listing", "get_product", "stage_action", "execute_command",
    "local_speak", "get_orders", "get_reviews", "log_learning", "list_todos", "add_todo",
    "complete_todo", "autofix_listing_tags", "autofix_listing_title", "stage_batch_tag_update",
    "toggle_listing_state", "get_conversion_targets", "diagnose_listing_conversion",
    "register_command", "read_knowledge_base_doc", "find_business_gaps", "browse_web",
    "search_etsy", "check_listing_quality", "generate_video",
}


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

    # 4b. Every core dispatcher tool is still present in the registry (see EXPECTED_CORE_TOOLS
    #     above). Registry-only check — a miss means a core tool was dropped/renamed.
    core_missing = EXPECTED_CORE_TOOLS - names
    if core_missing:
        failures.append(f"core agent tools missing from registry: {sorted(core_missing)}")

    # 4c. Every core tool is still ROUTED by the dispatcher. The dispatcher
    #     (`_execute_agent_tool`) is a flat `if name == "X":` chain, so a tool can be
    #     registered in AGENT_TOOLS (passes 4b) yet have no dispatch branch — the call would
    #     fall through to "unknown tool" at runtime. We can't invoke the dispatcher here
    #     (handlers hit Etsy/db/anthropic and have side effects), so instead we statically
    #     inspect its source and confirm each core name has a `name == "..."` branch. This is
    #     the safe substitute for extracting a HANDLERS dict: it makes a routing regression
    #     (a dropped/renamed branch) fail CI, with zero change to production code. If the
    #     dispatcher is ever refactored into a dict/registry, replace this with a direct
    #     `set(HANDLERS) == EXPECTED_CORE_TOOLS` assertion.
    import inspect
    dispatch = getattr(server, "_execute_agent_tool", None)
    if callable(dispatch):
        try:
            src = inspect.getsource(dispatch)
        except (OSError, TypeError):
            src = ""
        if src:
            unrouted = {n for n in EXPECTED_CORE_TOOLS if f'name == "{n}"' not in src}
            if unrouted:
                failures.append(
                    f"core agent tools registered but NOT routed by _execute_agent_tool "
                    f"(no `name == \"...\"` branch): {sorted(unrouted)}")

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

    # 7. No `from tools.X import Y` anywhere in main.py's source. That import form
    #    only resolves if the repo ROOT is on sys.path — main.py's real runtime
    #    sys.path only has tools/api_server (implicit script dir) + tools/ (explicit
    #    insert at startup), never the repo root, so `from tools.X import Y` raises
    #    ModuleNotFoundError the moment it actually runs. Import 2 (`import main`)
    #    can't catch this class of bug when the bad import is deferred inside a
    #    function body (lazy import) rather than at module top level — the function
    #    has to actually be CALLED to trigger it, and most of these are behind auth/
    #    request handling that this dependency-light smoke test never exercises.
    #    Found (and fixed) 9 real instances of this on 2026-07-08, all deferred
    #    imports inside route handlers/background loops — this check exists so the
    #    same mistake can't silently ship again. The fix is always the same: `import
    #    X` (bare — X is already importable since tools/ is on sys.path) instead of
    #    `from tools.X import Y`, then call `X.Y(...)`.
    main_py = ROOT / "tools" / "api_server" / "main.py"
    try:
        src_text = main_py.read_text()
        bad_imports = [
            line.strip() for line in src_text.splitlines()
            if _re.match(r"\s*from tools\.", line)
        ]
        if bad_imports:
            failures.append(
                "main.py has 'from tools.X import Y' imports that will fail in "
                f"production (repo root isn't on sys.path there): {bad_imports}"
            )
    except Exception as exc:
        failures.append(f"could not scan main.py for bad import pattern: {exc}")

    if failures:
        print("SMOKE FAIL:", file=sys.stderr)
        for f in failures:
            print("  -", f, file=sys.stderr)
        return 1

    print(f"SMOKE OK — build {server._BUILD_ID}, {len(tools)} agent tools registered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
