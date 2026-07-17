"""
Tests for the update_price action type and bulk price/renewal staging tools
(Frank upgrade Wave 2, capabilities item 2, 2026-07-17).

Capabilities audit finding: "No stage_action path exists to renew/republish
an expired listing... No bulk price-update or listing-renewal tool exists...
Scott can't ask Frank to 'raise all wall-art prices $2' or 'republish the 6
expired planners' in one tap." Investigation found single-listing renewal
already worked (toggle_listing_state with new_state='active' — Etsy has no
separate renew endpoint; PATCHing state:active on an expired listing IS the
renewal). The real gap was BULK: doing several listings in one tap. This adds:
  - update_price: a genuinely new action type (no existing type touched price)
  - stage_batch_price_update: bulk price tool, hard-capped at 5 listing_ids
    per call (CLAUDE.md Hard Stop: "Change prices on more than 5 listings in
    a single session")
  - stage_batch_listing_state: bulk activate/deactivate/renew tool, capped at
    10 per call (matching stage_batch_tag_update's existing convention)

Self-contained TestClient-against-the-real-app pattern, same as
tests/test_pinterest_wiring.py. This sandbox has no real Etsy credentials,
which is itself exercised as a real (not mocked) code path by the
fetch-failure tests below.

Run: python tests/test_price_renewal_actions.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_price_renewal_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "price-renewal-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def validate(action_type: str, payload: dict, **kwargs):
    return server._validate_staged_action({"type": action_type, "payload": payload}, **kwargs)


# ── update_price: type registration ─────────────────────────────────────────
def test_update_price_is_a_recognized_etsy_staged_action_type():
    check("update_price" in server._ETSY_STAGED_ACTION_TYPES,
          f"update_price must be in _ETSY_STAGED_ACTION_TYPES, got {server._ETSY_STAGED_ACTION_TYPES}")
    check("update_price" in server._STAGED_ACTION_TYPES,
          "update_price must be in the master _STAGED_ACTION_TYPES tuple")


# ── update_price: validation ────────────────────────────────────────────────
def test_update_price_valid_payload_passes():
    ok, msg = validate("update_price", {"listing_id": 4509179201, "price": 14.99})
    check(ok is True, f"a valid .99-ending price should pass, got: {msg!r}")


def test_update_price_missing_listing_id_rejected():
    ok, msg = validate("update_price", {"price": 14.99})
    check(ok is False, "missing listing_id must be rejected")


def test_update_price_non_numeric_rejected():
    ok, msg = validate("update_price", {"listing_id": 123, "price": "fourteen ninety nine"})
    check(ok is False, "a non-numeric price must be rejected")


def test_update_price_bool_rejected():
    # bool is technically an int subclass in Python -- must not sneak through isinstance(x, (int, float)).
    ok, msg = validate("update_price", {"listing_id": 123, "price": True})
    check(ok is False, "a bool price must be rejected despite being an int subclass")


def test_update_price_below_floor_rejected():
    ok, msg = validate("update_price", {"listing_id": 123, "price": 0.50})
    check(ok is False, "a price below $1.00 must be rejected as implausible")


def test_update_price_above_ceiling_rejected():
    ok, msg = validate("update_price", {"listing_id": 123, "price": 999.99})
    check(ok is False, "a price above $500 must be rejected as implausible")


def test_update_price_wrong_ending_rejected():
    ok, msg = validate("update_price", {"listing_id": 123, "price": 15.00})
    check(ok is False, "a price not ending in .99/.97/.49 must be rejected (CLAUDE.md pricing convention)")
    check(".99" in msg or ".97" in msg or ".49" in msg, f"rejection reason should explain the pricing rule, got: {msg!r}")


def test_update_price_97_and_49_endings_pass():
    ok1, msg1 = validate("update_price", {"listing_id": 123, "price": 9.97})
    check(ok1 is True, f"a .97-ending price should pass, got: {msg1!r}")
    ok2, msg2 = validate("update_price", {"listing_id": 123, "price": 4.49})
    check(ok2 is True, f"a .49-ending price should pass, got: {msg2!r}")


# ── update_price: executor ──────────────────────────────────────────────────
def test_update_price_executor_selects_price_field():
    # Don't actually hit the network (no real creds in this sandbox) -- just
    # confirm the dispatch branch exists and would build the right call by
    # checking the type is handled (not falling through to "unsupported type").
    import inspect
    src = inspect.getsource(server._execute_staged_action)
    check('elif t == "update_price":' in src, "the executor must have an update_price branch")
    check('"price": round(float(p["price"]), 2)' in src,
          "the update_price branch must PATCH the price field in dollars")


# ── generic stage_action tool: update_price support ─────────────────────────
def test_generic_stage_action_tool_lists_update_price():
    tool = next(t for t in server.AGENT_TOOLS if t["name"] == "stage_action")
    enum = tool["input_schema"]["properties"]["action_type"]["enum"]
    check("update_price" in enum, f"stage_action's action_type enum must include update_price, got {enum}")
    check("price" in tool["input_schema"]["properties"], "stage_action's input_schema must accept a price field")


def test_generic_stage_action_stages_a_single_price_update():
    payload_in = {"action_type": "update_price", "listing_id": 4509179201, "summary": "Test price bump", "price": 12.99}
    out = server._execute_agent_tool("stage_action", payload_in)
    check(out.get("staged") is True, f"staging a valid single price update should succeed, got: {out}")
    queued = server.db.get_action(out["action_id"])
    check(queued["type"] == "update_price", f"expected type=update_price, got: {queued['type']}")
    check(queued["payload"]["price"] == 12.99, f"expected payload price 12.99, got: {queued['payload']}")


# ── bulk tools: registration ────────────────────────────────────────────────
def test_bulk_tools_are_registered():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("stage_batch_price_update" in names, "stage_batch_price_update must be in AGENT_TOOLS")
    check("stage_batch_listing_state" in names, "stage_batch_listing_state must be in AGENT_TOOLS")


# ── stage_batch_price_update: caps and input validation ─────────────────────
def test_batch_price_update_requires_listing_ids():
    out = server._execute_agent_tool("stage_batch_price_update", {"new_price": 9.99})
    check("error" in out, f"missing listing_ids should error, got: {out}")


def test_batch_price_update_requires_exactly_one_of_new_price_or_delta():
    out1 = server._execute_agent_tool("stage_batch_price_update", {"listing_ids": [1, 2]})
    check("error" in out1, f"neither new_price nor price_delta given should error, got: {out1}")
    out2 = server._execute_agent_tool(
        "stage_batch_price_update", {"listing_ids": [1, 2], "new_price": 9.99, "price_delta": 2.0}
    )
    check("error" in out2, f"both new_price and price_delta given should error, got: {out2}")


def test_batch_price_update_rejects_over_5_listings():
    out = server._execute_agent_tool(
        "stage_batch_price_update", {"listing_ids": [1, 2, 3, 4, 5, 6], "new_price": 9.99}
    )
    check("error" in out, f"6 listing_ids must be refused outright (CLAUDE.md 5-listing price cap), got: {out}")
    check("5" in out["error"], f"the refusal should cite the 5-listing cap, got: {out['error']!r}")


def test_batch_price_update_at_5_listings_does_not_hit_the_cap_refusal():
    # No real Etsy creds in this sandbox -- every listing fetch will fail, but
    # that must surface as per-listing fetch errors, NOT the blanket "exceeds
    # the cap" refusal, proving the boundary is exactly >5, not >=5.
    out = server._execute_agent_tool(
        "stage_batch_price_update", {"listing_ids": [1, 2, 3, 4, 5], "new_price": 9.99}
    )
    check("error" not in out, f"exactly 5 listing_ids must not trigger the cap refusal, got: {out}")
    check(out.get("count") == 0, f"with no real creds every fetch should fail, got: {out}")
    check(len(out.get("errors", [])) == 5, f"expected 5 fetch errors (one per listing), got: {out}")


# ── stage_batch_listing_state: caps and input validation ────────────────────
def test_batch_listing_state_requires_listing_ids():
    out = server._execute_agent_tool("stage_batch_listing_state", {"new_state": "active"})
    check("error" in out, f"missing listing_ids should error, got: {out}")


def test_batch_listing_state_requires_valid_new_state():
    out = server._execute_agent_tool(
        "stage_batch_listing_state", {"listing_ids": [1, 2], "new_state": "expired"}
    )
    check("error" in out, f"an invalid new_state must be rejected, got: {out}")


def test_batch_listing_state_rejects_over_10_listings():
    out = server._execute_agent_tool(
        "stage_batch_listing_state",
        {"listing_ids": list(range(1, 12)), "new_state": "active"},
    )
    check("error" in out, f"11 listing_ids must be refused outright (10-listing cap), got: {out}")


def test_batch_listing_state_fetch_failures_are_partial_not_fatal():
    # No real creds -- confirms the "each listing staged independently,
    # never all-or-nothing" partial-failure pattern used by stage_batch_tag_update.
    out = server._execute_agent_tool(
        "stage_batch_listing_state", {"listing_ids": [111, 222], "new_state": "active"}
    )
    check("error" not in out, f"a well-formed request within caps must not itself error, got: {out}")
    check(out.get("count") == 0 and len(out.get("errors", [])) == 2,
          f"both listings should fail as individual fetch errors, got: {out}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PRICE/RENEWAL ACTION TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRICE/RENEWAL ACTION TESTS OK — update_price type, validation (range + "
          ".99/.97/.49 ending + bool guard), executor, generic stage_action support, "
          "and both bulk tools (caps + partial-failure semantics) all verified.")


if __name__ == "__main__":
    run()
