#!/usr/bin/env python3
"""
Test for Frank fix (2026-07-18): the mobile "Let Frank fix it" action-sheet
button.

Scott reported that tapping "Let Frank fix it" on a flagged listing sent
Frank into the chat panel, where he reliably diagnosed the problem but,
per Scott's own words, "he just diagnoses it" -- the chat model routinely
stopped after explaining the issue instead of also calling
apply_conversion_fixes (or the individual autofix tools) to actually stage
a fix. The diagnose-then-stage logic itself was already correct and
already tested (_apply_conversion_fixes_core, see
test_conversion_diagnosis_to_autofix_loop.py) -- it just wasn't reachable
deterministically. phoneSheetFix() in frank_hud_mockup.py routed through a
free-text chat prompt and hoped the model chained the right tool calls.

The fix: a real POST /api/conversion-targets/{listing_id}/fix REST route
that calls _apply_conversion_fixes_core directly, and phoneSheetFix() now
calls that route instead of going through chat. This guarantees the
diagnose-and-stage sequence runs every time, with zero dependency on model
judgment -- while remaining 100% staging-only, exactly like the chat tool
it wraps.

Run: python tests/test_conversion_target_fix_route.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_conv_fix_route_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "conv-fix-route-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(server.app, base_url="https://testserver")

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_route_requires_auth():
    resp = client.post("/api/conversion-targets/123/fix")
    check(resp.status_code == 401, f"unauthenticated POST should 401, got {resp.status_code}")


def test_route_calls_apply_conversion_fixes_core_and_returns_its_result():
    fake_result = {
        "listing_id": 4509179201,
        "primary_issue": "Title doesn't lead with the primary keyword.",
        "applied": [{"area": "title", "action_id": 1, "finding": "f", "fix": "x"}],
        "skipped": [],
        "errors": [],
        "message": "Diagnosed listing 4509179201 — staged 1 fix(es) for Scott's approval.",
    }
    captured = {}

    async def fake_apply(listing_id):
        captured["listing_id"] = listing_id
        return fake_result

    with patch.object(server, "_apply_conversion_fixes_core", fake_apply):
        resp = client.post(
            "/api/conversion-targets/4509179201/fix",
            headers={"Authorization": f"Bearer {os.environ['APP_SECRET_TOKEN']}"},
        )
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text[:300]}")
    check(captured.get("listing_id") == 4509179201,
          f"the route must call _apply_conversion_fixes_core with the path listing_id, got: {captured}")
    body = resp.json()
    check(body == fake_result, f"the route must return _apply_conversion_fixes_core's result verbatim, got: {body}")


def test_route_is_post_only():
    resp = client.get(
        "/api/conversion-targets/123/fix",
        headers={"Authorization": f"Bearer {os.environ['APP_SECRET_TOKEN']}"},
    )
    check(resp.status_code == 405, f"GET on a POST-only route should 405, got {resp.status_code}")


def test_route_rejects_non_integer_listing_id():
    resp = client.post(
        "/api/conversion-targets/not-a-number/fix",
        headers={"Authorization": f"Bearer {os.environ['APP_SECRET_TOKEN']}"},
    )
    check(resp.status_code == 422, f"a non-integer listing_id should 422, got {resp.status_code}")


def test_phone_sheet_fix_calls_the_rest_route_not_chat():
    import subprocess
    node = subprocess.run(["node", "--version"], capture_output=True, text=True)
    if node.returncode != 0:
        print("SKIP: node not available, skipping JS-source assertion")
        return
    js_src = server.render_frank_hud()
    check("async function phoneSheetFix" in js_src,
          "phoneSheetFix must be async now that it awaits a fetch call")
    check("/api/conversion-targets/'+it.listing_id+'/fix" in js_src,
          "phoneSheetFix must call the new deterministic REST route")
    # The old behavior (routing through the chat input + sendMsg()) must be gone
    # from this function -- otherwise the fix could silently regress back to
    # "just sends a prompt and hopes."
    fix_fn_start = js_src.index("async function phoneSheetFix")
    fix_fn_end = js_src.index("\n}", fix_fn_start)
    fix_fn_body = js_src[fix_fn_start:fix_fn_end]
    check("sendMsg()" not in fix_fn_body,
          f"phoneSheetFix must no longer delegate to the chat agent, got body containing sendMsg(): {fix_fn_body[:200]}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("CONVERSION TARGET FIX ROUTE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("CONVERSION TARGET FIX ROUTE TESTS OK — the new POST /api/conversion-targets/"
          "{listing_id}/fix route requires auth, calls _apply_conversion_fixes_core "
          "directly with the path listing_id and returns its result verbatim, rejects "
          "GET and non-integer IDs, and phoneSheetFix() now calls this route instead of "
          "delegating to the chat agent.")


if __name__ == "__main__":
    run()
