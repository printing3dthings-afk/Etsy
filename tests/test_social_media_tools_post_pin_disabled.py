"""
Regression test for Frank upgrade Wave 4, item D1 (2026-07-17 security fix).

tools/social_media_tools.py's `_post_pin()` used to call
`pinterest_api.PinterestClient.create_pin()` directly with zero staging or
approval -- a live Hard-Stop bypass (CLAUDE.md's Autonomy Boundaries: "Post
to social media accounts" always requires explicit review). It was dormant
only because this whole module was never imported by main.py's AGENT_TOOLS
-- a future casual wiring pass (the same way etsy_ads_tools.py was wired in)
could easily have reopened this exact hole. Defused at the source: the
function now unconditionally refuses and points at the real, staged,
already-tested path (stage_pinterest_post -> Action Center ->
_execute_pinterest_staged_action).

This test guards against the unsafe direct-post behavior ever coming back,
regardless of Pinterest's configured/unconfigured state, and regardless of
whether this module ever gets wired into AGENT_TOOLS in the future.

Run: python tests/test_social_media_tools_post_pin_disabled.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

for p in (ROOT, ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import social_media_tools as smt  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


_VALID_INPUT = {"listing_id": "DP1026", "board_name": "Digital Planners & Printables", "image_url": "https://example.com/x.jpg"}


def test_post_pin_always_refuses_regardless_of_input():
    import json
    result = json.loads(smt._post_pin(_VALID_INPUT, None))
    check("error" in result, f"post_pin must always return an error, got: {result}")
    check(result.get("use_instead") == "stage_pinterest_post",
          f"the refusal must point at the real staged tool, got: {result}")


def test_post_pin_never_calls_create_pin():
    # Even if pinterest_api reports "configured" and a real client would
    # succeed, _post_pin must never reach create_pin() -- patch it to raise
    # if called, proving the function returns before touching the API at all.
    import pinterest_api

    def _boom(*a, **kw):
        raise AssertionError("_post_pin must never call PinterestClient.create_pin()")

    orig_is_configured = pinterest_api.is_configured
    orig_get_client = pinterest_api.get_client
    pinterest_api.is_configured = lambda: True
    pinterest_api.get_client = lambda: type("FakeClient", (), {"create_pin": staticmethod(_boom), "get_board_id": staticmethod(_boom)})()
    try:
        smt._post_pin(_VALID_INPUT, None)
    except AssertionError:
        raise
    except Exception:
        pass  # any other failure mode is fine; the assertion above is what matters
    finally:
        pinterest_api.is_configured = orig_is_configured
        pinterest_api.get_client = orig_get_client


def test_post_pin_does_not_touch_the_store_argument():
    # A None store must not crash the function -- confirms it no longer
    # reads store.find_listing()/etc, another sign it can't accidentally
    # half-execute a post.
    try:
        smt._post_pin(_VALID_INPUT, None)
    except Exception as exc:  # noqa: BLE001
        _failures.append(f"_post_pin must not touch its store argument, raised: {exc!r}")


def test_post_pin_still_registered_in_execute_tool_dispatch():
    # Confirms the dispatcher still routes "post_pin" here (not silently
    # removed/orphaned) -- the tool itself is what's neutered, not the wiring.
    import json
    result = json.loads(smt.execute_tool("post_pin", _VALID_INPUT, None))
    check("error" in result, f"dispatching post_pin through execute_tool must still hit the refusal, got: {result}")


def test_module_is_still_unwired_from_agent_tools():
    # Sanity check on the broader finding: confirms social_media_tools is
    # still not imported by main.py, i.e. this defused function currently
    # has zero live callers either way. If a future change imports this
    # module into AGENT_TOOLS, this test intentionally does NOT block that
    # -- it only guards _post_pin's own behavior, which is safe regardless.
    main_py = (ROOT / "tools" / "api_server" / "main.py").read_text()
    check("social_media_tools" not in main_py or "import social_media_tools" not in main_py,
          "informational only: social_media_tools now appears imported in main.py -- "
          "if wired in, confirm post_pin is excluded from any registered tool list")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("POST_PIN DISABLED TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("POST_PIN DISABLED TESTS OK — _post_pin unconditionally refuses, never reaches "
          "PinterestClient.create_pin(), doesn't touch its store argument, and the "
          "dispatcher still routes to the (now-safe) refusal.")


if __name__ == "__main__":
    run()
