"""
Catalog reconciliation + product registration feature (2026-08-05).

Follow-up to the koozie/planner listing-mismatch bug: 3 live Etsy listings
existed with zero record in either of Frank's two local registries
(data/product_catalog.json and data/listing_manifest.json), and "Ask Frank
to Fix" blind-generated wrong titles for them because it had no grounding
on what the products actually were. This covers the follow-up feature
Scott asked for: a way to register physical 3D-print products, Frank
proactively detecting untracked live listings, and grounded (not
title-keyword-guessing) classification.

Covers:
  - _get_manifest_entry() / _read_manifest_entry_sync(): merges the
    git-tracked manifest file with the durable override sidecar, and a
    genuine git-file read failure still propagates (doesn't get silently
    swallowed into "unmapped").
  - _blind_fix_refusal(): the chat-tool counterpart to request_listing_
    fix()'s grounding gate -- blocks autofix_listing_tags/title for an
    unmapped listing with no reason, allows it once mapped or a reason is
    supplied.
  - classify_listing_structured() / classify_listings_batch() /
    classify_unmapped_listing(): structured-signal-first classification
    (physical vs. digital from Etsy's own type/shipping_profile_id, free,
    no LLM), fail-closed to uncategorized/low when the LLM pass is
    unavailable/inconclusive, never drops an input listing from the output.
  - register_product staged-action type: validator (product_id/name/
    category required, category must be known, price bounds, duplicate
    product_id rejected, duplicate etsy_listing_id rejected) and executor
    (writes BOTH sidecars, is_new_product flag so _find_catalog_product
    recognizes it, manifest entry only written when there's a real
    etsy_listing_id).
  - register_product_directly() (the Create screen's quick-add form
    endpoint): auto-classifies when no category given, auto-slugifies a
    product_id when none given, surfaces validator failures as HTTP 422.
  - _run_catalog_reconciliation_batch(): finds true orphans (in neither
    registry), stages register_product actions, skips listings already
    known or already pending, respects the per-run cap.

Run: python tests/test_catalog_registration.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_catalogreg_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "catalogreg-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import listing_integrity_check as lic  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _isolated_sidecars():
    """Context manager-ish helper: patches both override sidecar paths to a
    fresh temp dir so tests never touch the real data/*_overrides.json
    files. Returns the patch objects (caller uses `with`)."""
    tmpdir = tempfile.mkdtemp(prefix="frank_catalogreg_sidecars_")
    return (
        patch.object(server, "_PRODUCT_CATALOG_OVERRIDES_PATH", Path(tmpdir) / "product_catalog_overrides.json"),
        patch.object(server, "_LISTING_MANIFEST_OVERRIDES_PATH", Path(tmpdir) / "listing_manifest_overrides.json"),
    )


def _fake_listing(listing_id, title="Some Listing", price_cents=1699, physical=False):
    d = {"listing_id": listing_id, "title": title, "price": {"amount": price_cents, "divisor": 100},
         "description": "a description"}
    if physical:
        d["type"] = "physical"
        d["shipping_profile_id"] = 55555
    else:
        d["type"] = "download"
    return d


# ── _get_manifest_entry / _read_manifest_entry_sync ─────────────────────

def test_manifest_entry_checks_override_when_git_file_has_nothing():
    p1, p2 = _isolated_sidecars()
    with p1, p2, patch.object(lic, "_load_json", return_value={}):
        check(server._read_manifest_entry_sync(7001001) is None,
              "expected None before anything is registered")
        server._write_listing_manifest_override(7001001, {"dp_codes": ["X"], "type": "3d_print_physical"})
        entry = server._read_manifest_entry_sync(7001001)
        check(entry is not None and entry.get("dp_codes") == ["X"],
              f"expected the override entry to be found, got {entry!r}")
        entry2 = asyncio.run(server._get_manifest_entry(7001001))
        check(entry2 == entry, "async wrapper should return the same result as the sync core")


def test_manifest_entry_git_file_wins_over_override():
    p1, p2 = _isolated_sidecars()
    git_manifest = {"7001002": {"dp_codes": ["REAL"], "type": "planner"}}
    with p1, p2, patch.object(lic, "_load_json", return_value=git_manifest):
        server._write_listing_manifest_override(7001002, {"dp_codes": ["STALE"], "type": "uncategorized"})
        entry = server._read_manifest_entry_sync(7001002)
        check(entry.get("dp_codes") == ["REAL"],
              f"the real git-tracked manifest entry should win over a stale override, got {entry!r}")


def test_manifest_entry_git_read_failure_propagates():
    p1, p2 = _isolated_sidecars()
    with p1, p2, patch.object(lic, "_load_json", side_effect=RuntimeError("disk error")):
        try:
            server._read_manifest_entry_sync(7001003)
            check(False, "expected the git-manifest read failure to propagate, not be swallowed")
        except RuntimeError:
            pass


# ── _blind_fix_refusal ───────────────────────────────────────────────────

def test_blind_fix_refusal_blocks_unmapped_no_reason():
    with patch.object(lic, "_load_json", return_value={}), \
         patch.object(server, "_listing_manifest_overrides", return_value={}):
        result = server._blind_fix_refusal(7002001, "")
        check(result is not None and "error" in result,
              f"expected a refusal dict for an unmapped listing with no reason, got {result!r}")


def test_blind_fix_refusal_allows_with_reason():
    with patch.object(lic, "_load_json", return_value={}), \
         patch.object(server, "_listing_manifest_overrides", return_value={}):
        result = server._blind_fix_refusal(7002002, "Scott confirmed this is a planner")
        check(result is None, f"expected None (allowed) when a reason is supplied, got {result!r}")


def test_blind_fix_refusal_allows_when_mapped():
    with patch.object(lic, "_load_json", return_value={"7002003": {"type": "planner"}}):
        result = server._blind_fix_refusal(7002003, "")
        check(result is None, f"expected None (allowed) for a mapped listing, got {result!r}")


# ── classification ────────────────────────────────────────────────────────

def test_classify_structured_resolves_physical_for_free():
    listing = _fake_listing(1, physical=True)
    result = server._classify_listing_structured(listing)
    check(result is not None and result["category"] == "3d_print_physical",
          f"expected structured signals to resolve physical, got {result!r}")


def test_classify_structured_inconclusive_for_digital():
    listing = _fake_listing(1, physical=False)
    result = server._classify_listing_structured(listing)
    check(result is None, f"expected None (inconclusive) for a plain download listing, got {result!r}")


def test_classify_batch_falls_back_to_uncategorized_without_llm():
    with patch.object(server, "ANTHROPIC_KEY", ""):
        listings = [_fake_listing(1, title="Kawaii Digital Planner 2026"), _fake_listing(2, physical=True)]
        results = server.classify_listings_batch(listings)
        check(len(results) == 2, f"expected one result per input listing, got {len(results)}")
        by_id = {r["listing_id"]: r for r in results}
        check(by_id[1]["category"] == "uncategorized" and by_id[1]["confidence"] == "low",
              f"digital listing with no LLM available should fail closed to uncategorized/low, got {by_id[1]!r}")
        check(by_id[2]["category"] == "3d_print_physical",
              f"physical listing should still resolve via structured signals, got {by_id[2]!r}")


def test_classify_unmapped_listing_single_wrapper():
    result = server.classify_unmapped_listing(_fake_listing(1, physical=True))
    check(result["category"] == "3d_print_physical", f"got {result!r}")


# ── register_product staged action: validator ────────────────────────────

def test_register_product_validator_requires_fields():
    ok, msg = server._validate_staged_action({"type": "register_product", "payload": {}})
    check(not ok and "product_id" in msg, f"expected missing-product_id rejection, got ({ok}, {msg!r})")


def test_register_product_validator_rejects_unknown_category():
    payload = {"product_id": "P3D_X", "name": "X", "category": "not_a_real_category"}
    ok, msg = server._validate_staged_action({"type": "register_product", "payload": payload})
    check(not ok and "category" in msg, f"expected category rejection, got ({ok}, {msg!r})")


def test_register_product_validator_allows_no_etsy_listing_id():
    payload = {"product_id": "P3D_NOT_LISTED_YET_TEST", "name": "Not Listed Yet", "category": "3d_print_physical"}
    p1, p2 = _isolated_sidecars()
    with p1, p2:
        ok, msg = server._validate_staged_action({"type": "register_product", "payload": payload})
        check(ok, f"a physical product with no etsy_listing_id yet should validate fine, got ({ok}, {msg!r})")


def test_register_product_validator_rejects_duplicate_etsy_listing_id():
    p1, p2 = _isolated_sidecars()
    with p1, p2:
        server._write_listing_manifest_override(7003001, {"dp_codes": ["P3D_ALREADY"], "type": "3d_print_physical"})
        payload = {"product_id": "P3D_NEW_DUPLICATE_TEST", "name": "Dup", "category": "3d_print_physical",
                   "etsy_listing_id": 7003001}
        ok, msg = server._validate_staged_action({"type": "register_product", "payload": payload})
        check(not ok and "already mapped" in msg,
              f"expected a double-registration refusal, got ({ok}, {msg!r})")


# ── register_product staged action: executor ─────────────────────────────

def test_register_product_executor_writes_both_sidecars():
    p1, p2 = _isolated_sidecars()
    with p1, p2:
        payload = {"product_id": "P3D_EXECUTOR_TEST", "name": "Executor Test Widget",
                   "category": "3d_print_physical", "price": 22.5, "etsy_listing_id": 7004001}
        result = server._execute_register_product_staged_action({"payload": payload})
        check(result["manifest_entry_written"] is True, f"expected manifest_entry_written=True, got {result!r}")
        check(server._find_catalog_product("P3D_EXECUTOR_TEST") is not None,
              "the new product should be immediately findable via _find_catalog_product")
        entry = server._read_manifest_entry_sync(7004001)
        check(entry is not None and entry.get("dp_codes") == ["P3D_EXECUTOR_TEST"],
              f"expected a matching manifest entry, got {entry!r}")


def test_register_product_executor_no_listing_id_skips_manifest():
    p1, p2 = _isolated_sidecars()
    with p1, p2:
        payload = {"product_id": "P3D_EXECUTOR_NO_LISTING_TEST", "name": "No Listing Yet",
                   "category": "3d_print_physical", "price": None, "etsy_listing_id": None}
        result = server._execute_register_product_staged_action({"payload": payload})
        check(result["manifest_entry_written"] is False,
              f"expected manifest_entry_written=False with no etsy_listing_id, got {result!r}")
        check(server._find_catalog_product("P3D_EXECUTOR_NO_LISTING_TEST") is not None,
              "should still be findable in the catalog even with no Etsy listing yet")


def test_register_product_executor_duplicate_product_id_blocked_by_validator():
    p1, p2 = _isolated_sidecars()
    with p1, p2:
        payload = {"product_id": "P3D_DUPCHECK_TEST", "name": "Dup Check", "category": "3d_print_physical"}
        server._execute_register_product_staged_action({"payload": payload})
        ok, msg = server._validate_staged_action({"type": "register_product", "payload": payload})
        check(not ok and "already exists" in msg,
              f"expected the second registration attempt to be rejected, got ({ok}, {msg!r})")


# ── register_product_directly() endpoint ──────────────────────────────────

def test_register_directly_requires_name():
    p1, p2 = _isolated_sidecars()
    with p1, p2:
        try:
            asyncio.run(server.register_product_directly(body={}, _token="test"))
            check(False, "expected an HTTPException for missing name")
        except server.HTTPException as exc:
            check(exc.status_code == 400, f"expected 400, got {exc.status_code}")


def test_register_directly_auto_slugifies_and_defaults_category():
    p1, p2 = _isolated_sidecars()
    with p1, p2:
        result = asyncio.run(server.register_product_directly(
            body={"name": "Auto Slug Test Widget", "price": 12.0}, _token="test"))
        check(result["category"] == "3d_print_physical",
              f"with no listing to check, should default to 3d_print_physical, got {result!r}")
        check(result["product_id"].startswith("P3D_"), f"expected a P3D_ product_id, got {result['product_id']!r}")


def test_register_directly_surfaces_validator_failure_as_422():
    p1, p2 = _isolated_sidecars()
    with p1, p2:
        try:
            asyncio.run(server.register_product_directly(
                body={"name": "Bad Category Test", "category": "not_real"}, _token="test"))
            check(False, "expected an HTTPException for an invalid category")
        except server.HTTPException as exc:
            check(exc.status_code == 422, f"expected 422, got {exc.status_code}")


# ── reconciliation sweep ──────────────────────────────────────────────────

def test_reconciliation_finds_and_stages_true_orphans():
    p1, p2 = _isolated_sidecars()
    fake_listings = [
        _fake_listing(7005001, title="Kawaii Blue Orange Koozie SVG, 3D Print File", physical=True),
        _fake_listing(7005002, title="Kawaii Digital Planner 2026", physical=False),
    ]
    with p1, p2, patch.object(lic, "_load_json", return_value={}), \
         patch.object(server, "EtsyAPIClient",
                      return_value=MagicMock(get_shop_listings_all=lambda state="active": fake_listings)):
        result = server._run_catalog_reconciliation_batch()
        check(result["staged"] == 2, f"expected both orphans staged, got {result!r}")
        pending = server.db.list_actions("pending")
        staged_ids = {a["payload"].get("etsy_listing_id") for a in pending if a["type"] == "register_product"}
        check(7005001 in staged_ids and 7005002 in staged_ids,
              f"expected both listing_ids staged, got {staged_ids!r}")


def test_reconciliation_skips_already_known_listings():
    p1, p2 = _isolated_sidecars()
    fake_listings = [_fake_listing(7005003, title="Already Known Listing")]
    known_manifest = {"7005003": {"dp_codes": ["DP1026"], "type": "planner"}}
    with p1, p2, patch.object(lic, "_load_json", return_value=known_manifest), \
         patch.object(server, "EtsyAPIClient",
                      return_value=MagicMock(get_shop_listings_all=lambda state="active": fake_listings)):
        result = server._run_catalog_reconciliation_batch()
        check(result["staged"] == 0, f"a listing already in the manifest should not be staged, got {result!r}")


def test_reconciliation_skips_listings_with_pending_action_already():
    p1, p2 = _isolated_sidecars()
    fake_listings = [_fake_listing(7005004, title="Already Pending Listing")]
    with p1, p2, patch.object(lic, "_load_json", return_value={}), \
         patch.object(server, "EtsyAPIClient",
                      return_value=MagicMock(get_shop_listings_all=lambda state="active": fake_listings)):
        server.db.enqueue_action("register_product", "pre-existing stage",
                                  {"etsy_listing_id": 7005004, "product_id": "P3D_ALREADY_PENDING"})
        result = server._run_catalog_reconciliation_batch()
        check(result["staged"] == 0,
              f"a listing with an already-pending register_product action should not be re-staged, got {result!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("CATALOG REGISTRATION TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("CATALOG REGISTRATION TESTS OK — manifest override merging, the chat-tool grounding gate, "
          "structured+fail-closed classification, register_product's validator/executor (both sidecars, "
          "duplicate/collision checks), the manual registration endpoint, and the reconciliation sweep "
          "(finds true orphans, skips known/pending listings) all behave correctly.")


if __name__ == "__main__":
    run()
