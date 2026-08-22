"""
Tests for the one-tap bulk-approve for low-risk pending items (2026-07-18,
Scott's confirmed reframing of the audit report's "confidence-tiered
auto-apply" idea). Research found the Approvals screen's own banner text
already promises "nothing goes live without your tap," and the batch-limit
safety rail (10 edits / 5 price changes) is enforced only in the frontend,
not the server -- so this ships as a genuine convenience (one confirm() for
several items instead of N), never a policy change: every item still goes
through the exact same POST /api/queue/{id}/approve path, one call per item.

No new backend endpoint exists for this phase (deliberately -- see plan) so
these are structural checks against the real HUD source, mirroring how
other picker/config features in this codebase are tested (e.g.
test_frank_font_pairings.py), plus semantic checks on the type whitelist.

Run: python tests/test_bulk_approve_low_risk.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUD_PATH = ROOT / "tools" / "api_server" / "frank_hud_mockup.py"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_bulk_approve_types_is_narrow_and_excludes_dangerous_types():
    source = HUD_PATH.read_text(encoding="utf-8")
    m = re.search(r"const _BULK_APPROVE_TYPES = \[(.*?)\];", source)
    assert m, "could not find const _BULK_APPROVE_TYPES = [...]"
    types = [t.strip().strip("'\"") for t in m.group(1).split(",") if t.strip()]
    check(set(types) == {"update_tags", "update_title"},
          f"expected exactly update_tags/update_title, got: {types}")
    for dangerous in ("update_price", "publish_listing", "local_exec", "local_delete", "toggle_listing_state"):
        check(dangerous not in types, f"{dangerous} must never be bulk-approvable, got: {types}")


def test_bulk_approve_function_exists_and_uses_confirm():
    source = HUD_PATH.read_text(encoding="utf-8")
    m = re.search(r"async function bulkApproveLowRisk\([^)]*\)\s*\{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find async function bulkApproveLowRisk(...)"
    body = m.group(1)
    check("confirm(" in body, "bulk-approve must still confirm() once before applying anything (one tap, not zero)")
    check("/api/queue/" in body and "/approve" in body,
          "bulk-approve should call the SAME per-item approve endpoint as a single approval, not a new bulk endpoint")
    check("_BULK_APPROVE_TYPES" in body, "the function should filter pending items by the narrow type whitelist")


def test_bulk_button_gated_on_count_and_batch_limit():
    source = HUD_PATH.read_text(encoding="utf-8")
    check("bulkCandidates.length >= 2" in source,
          "the bulk button should require at least 2 qualifying items (no point batching 1)")
    check("bulkCandidates.length <= _APPROVAL_BATCH_LIMIT" in source,
          "the bulk button should defer to the existing over-limit warning rather than offering a shortcut past it")


def test_bulk_approve_referenced_from_render():
    source = HUD_PATH.read_text(encoding="utf-8")
    check("onclick=\"bulkApproveLowRisk(this)\"" in source,
          "the rendered button should wire up to bulkApproveLowRisk(this) -- the element ref "
          "is needed for the in-flight loading state added 2026-07-18")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("BULK APPROVE LOW RISK TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("BULK APPROVE LOW RISK TESTS OK — the low-risk whitelist is narrow and excludes "
          "price/publish/exec/delete, bulkApproveLowRisk() still confirm()s once and reuses "
          "the same per-item approve endpoint, and the button only renders for 2+ qualifying "
          "items within the existing batch-limit rail.")


if __name__ == "__main__":
    run()
