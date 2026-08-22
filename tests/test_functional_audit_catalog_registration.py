"""
Functional audit -- catalog_registration key (2026-08-13).

Focus: GET /api/products/classify-listing/{listing_id}
(classify_listing_for_registration, main.py line ~15150) has ZERO existing
test coverage per tests/test_catalog_registration.py and
tests/test_listing_content_generator.py (both read first -- they cover
register_product_directly and set_product_listing_content thoroughly, and
also cover classify_unmapped_listing/_classify_listing_structured/
classify_listings_batch as bare functions, but never exercise the actual
route handler that wraps them: the EtsyAPIError 404/502 branches, the
generic-exception 502 branch, and the already_registered merge via
_get_manifest_entry).

Also spot-checks the "no duplicate/conflicting product_catalog.json entry"
requirement from api-conventions.md ("Durable state never touches a
git-tracked file at runtime") by confirming the real registration write
path goes through the volume-or-sidecar pattern (_PRODUCT_CATALOG_OVERRIDES_
PATH / _LISTING_MANIFEST_OVERRIDES_PATH), not a raw write to
data/product_catalog.json or data/listing_manifest.json -- this is the one
piece of the assignment's second focus area that test_catalog_registration.py
doesn't already nail down explicitly (it isolates the sidecars via patch but
never asserts the git-tracked files themselves stay untouched).

Run: python tests/test_functional_audit_catalog_registration.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import listing_integrity_check as lic  # noqa: E402
from etsy_api import EtsyAPIError  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


def _isolated_sidecars():
    tmpdir = tempfile.mkdtemp(prefix="frank_functional_audit_sidecars_")
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


# ── classify_listing_for_registration: 404 for a nonexistent listing ────

def test_classify_listing_404_for_nonexistent_listing():
    with patch.object(server, "EtsyAPIClient",
                       return_value=MagicMock(get_listing=MagicMock(
                           side_effect=EtsyAPIError(404, "Listing not found")))):
        try:
            asyncio.run(server.classify_listing_for_registration(9999999, _token="test"))
            check(False, "expected an HTTPException for a nonexistent listing_id")
        except server.HTTPException as exc:
            check(exc.status_code == 404, f"expected 404, got {exc.status_code}")
            check("9999999" in exc.detail, f"expected the listing_id named in the detail, got {exc.detail!r}")


# ── classify_listing_for_registration: non-404 EtsyAPIError -> 502, not 500 ──

def test_classify_listing_502_for_other_etsy_api_error():
    with patch.object(server, "EtsyAPIClient",
                       return_value=MagicMock(get_listing=MagicMock(
                           side_effect=EtsyAPIError(500, "Etsy internal error")))):
        try:
            asyncio.run(server.classify_listing_for_registration(1234567, _token="test"))
            check(False, "expected an HTTPException for a non-404 Etsy error")
        except server.HTTPException as exc:
            check(exc.status_code == 502, f"a non-404 EtsyAPIError should surface as 502, got {exc.status_code}")


# ── classify_listing_for_registration: generic exception (e.g. network) -> 502 ──

def test_classify_listing_502_for_generic_fetch_failure():
    with patch.object(server, "EtsyAPIClient",
                       return_value=MagicMock(get_listing=MagicMock(
                           side_effect=ConnectionError("network unreachable")))):
        try:
            asyncio.run(server.classify_listing_for_registration(1234567, _token="test"))
            check(False, "expected an HTTPException for a generic fetch failure")
        except server.HTTPException as exc:
            check(exc.status_code == 502, f"a generic fetch exception should surface as 502 (not 500), got {exc.status_code}")
            check("1234567" in exc.detail, f"expected the listing_id in the detail, got {exc.detail!r}")


# ── classify_listing_for_registration: happy path, physical listing ─────
# The route claims (docstring) it runs classify_unmapped_listing() against
# the REAL fetched listing and reports its actual category/confidence/
# reasoning -- verify the route doesn't silently ignore what came back from
# Etsy (e.g. always reporting a hardcoded category regardless of listing
# type, which would defeat the entire "preview before commit" purpose of
# this endpoint per CLAUDE.md's "never lie to the customer" spirit extended
# to Scott-facing tooling).

def test_classify_listing_physical_type_resolves_via_structured_signals():
    p1, p2 = _isolated_sidecars()
    listing = _fake_listing(5551111, title="Blue Koozie 3D Print", physical=True)
    with p1, p2, patch.object(server, "EtsyAPIClient", return_value=MagicMock(get_listing=lambda lid: listing)), \
         patch.object(lic, "_load_json", return_value={}):
        result = asyncio.run(server.classify_listing_for_registration(5551111, _token="test"))
    check(result["listing_id"] == 5551111, f"got {result}")
    check(result["title"] == "Blue Koozie 3D Print", f"got {result}")
    check(abs(result["price"] - 16.99) < 0.001, f"expected price 16.99, got {result['price']}")
    check(result["category"] == "3d_print_physical",
          f"a physical-typed listing must classify as 3d_print_physical via structured signals, got {result!r}")
    check(result["confidence"] == "high", f"structured-signal resolution should be high confidence, got {result!r}")
    check(result["already_registered"] is False, f"expected already_registered False for an unmapped listing, got {result!r}")
    check(result["already_registered_as"] is None, f"expected None, got {result!r}")


# ── classify_listing_for_registration: digital-typed listing, no LLM key ──
# This is the "listing_id ... belongs to a different product type than
# expected" case named in the assignment: a listing that is NOT physical
# (download type, no shipping profile) must NOT be misclassified as
# 3d_print_physical just because that's the only category the structured
# fast-path can resolve -- it must fall through to the LLM path, and with
# no LLM available, fail closed to uncategorized/low (never a confident
# wrong guess).

def test_classify_listing_digital_type_does_not_get_mislabeled_physical():
    p1, p2 = _isolated_sidecars()
    listing = _fake_listing(5552222, title="Kawaii Digital Planner 2026", physical=False)
    with p1, p2, patch.object(server, "EtsyAPIClient", return_value=MagicMock(get_listing=lambda lid: listing)), \
         patch.object(lic, "_load_json", return_value={}), \
         patch.object(server, "ANTHROPIC_KEY", ""):
        result = asyncio.run(server.classify_listing_for_registration(5552222, _token="test"))
    check(result["category"] != "3d_print_physical",
          f"a digital download-type listing must never be classified as 3d_print_physical, got {result!r}")
    check(result["category"] == "uncategorized" and result["confidence"] == "low",
          f"with no LLM available, a non-physical listing must fail closed to uncategorized/low "
          f"rather than guess, got {result!r}")


# ── classify_listing_for_registration: already_registered merge ─────────

def test_classify_listing_reports_already_registered_from_manifest_override():
    p1, p2 = _isolated_sidecars()
    listing = _fake_listing(5553333, title="Already Registered Widget", physical=True)
    with p1, p2, patch.object(server, "EtsyAPIClient", return_value=MagicMock(get_listing=lambda lid: listing)), \
         patch.object(lic, "_load_json", return_value={}):
        server._write_listing_manifest_override(5553333, {"dp_codes": ["P3D_EXISTING"], "type": "3d_print_physical"})
        result = asyncio.run(server.classify_listing_for_registration(5553333, _token="test"))
    check(result["already_registered"] is True, f"expected already_registered True, got {result!r}")
    check(result["already_registered_as"] == ["P3D_EXISTING"],
          f"expected the registered dp_codes surfaced, got {result!r}")


def test_classify_listing_git_manifest_entry_also_reports_already_registered():
    # The git-tracked manifest (not just the override sidecar) must also be
    # recognized -- _get_manifest_entry checks both, per
    # _read_manifest_entry_sync's documented precedence.
    p1, p2 = _isolated_sidecars()
    listing = _fake_listing(5554444, title="Already In Git Manifest", physical=True)
    git_manifest = {"5554444": {"dp_codes": ["DP1026"], "type": "planner"}}
    with p1, p2, patch.object(server, "EtsyAPIClient", return_value=MagicMock(get_listing=lambda lid: listing)), \
         patch.object(lic, "_load_json", return_value=git_manifest):
        result = asyncio.run(server.classify_listing_for_registration(5554444, _token="test"))
    check(result["already_registered"] is True, f"expected already_registered True from the git manifest, got {result!r}")
    check(result["already_registered_as"] == ["DP1026"], f"got {result!r}")


# ── auth wiring: read-only endpoint should use the lighter dependency ───

def test_classify_listing_route_uses_session_or_bearer_auth():
    route = next((r for r in server.app.routes
                  if getattr(r, "path", "") == "/api/products/classify-listing/{listing_id}"), None)
    check(route is not None, "the classify-listing route must be registered")
    if route is not None:
        deps = [d.call for d in route.dependant.dependencies]
        check(server._auth_session_or_bearer in deps,
              f"a read-only preview endpoint (never writes, per its own docstring) should use "
              f"_auth_session_or_bearer per api-conventions.md, got deps calling {deps}")


# ── Registration write path never touches the git-tracked catalog files ──
# api-conventions.md: "Durable state never touches a git-tracked file at
# runtime ... Anything that needs to persist a runtime change ... goes
# through the volume-or-local sidecar pattern". Confirm register_product's
# real executor writes ONLY the sidecar files and never touches
# data/product_catalog.json / data/listing_manifest.json themselves, even
# though _find_catalog_product's job is to make the new registration look
# indistinguishable from a real catalog entry (which is done by MERGING the
# override on read, not by mutating the git-tracked file).

def test_register_product_execution_never_writes_the_git_tracked_catalog_file():
    p1, p2 = _isolated_sidecars()
    real_catalog_path = ROOT / "data" / "product_catalog.json"
    real_manifest_path = ROOT / "data" / "listing_manifest.json"
    before_catalog = real_catalog_path.read_bytes() if real_catalog_path.exists() else None
    before_manifest = real_manifest_path.read_bytes() if real_manifest_path.exists() else None
    with p1, p2:
        payload = {"product_id": "P3D_AUDIT_NO_GIT_WRITE_TEST", "name": "Audit No Git Write",
                   "category": "3d_print_physical", "price": 19.99, "etsy_listing_id": 6001001}
        server._execute_register_product_staged_action({"payload": payload})
        overrides_path = server._PRODUCT_CATALOG_OVERRIDES_PATH
        manifest_overrides_path = server._LISTING_MANIFEST_OVERRIDES_PATH
        check(overrides_path.exists(), f"expected the sidecar override file to have been created at {overrides_path}")
        check(manifest_overrides_path.exists(),
              f"expected the manifest override sidecar to have been created at {manifest_overrides_path}")
    after_catalog = real_catalog_path.read_bytes() if real_catalog_path.exists() else None
    after_manifest = real_manifest_path.read_bytes() if real_manifest_path.exists() else None
    check(before_catalog == after_catalog,
          "the real git-tracked data/product_catalog.json must never be modified by register_product's executor")
    check(before_manifest == after_manifest,
          "the real git-tracked data/listing_manifest.json must never be modified by register_product's executor")


def test_register_product_rejects_duplicate_product_code_end_to_end():
    # register_product_directly() end-to-end (not just the validator in
    # isolation, which test_catalog_registration.py already covers): typing
    # the SAME product_id twice through the actual endpoint must reject the
    # second attempt with a 422, never silently overwrite/duplicate the
    # entry.
    p1, p2 = _isolated_sidecars()
    with p1, p2:
        body = {"product_id": "P3D_AUDIT_DUP_TEST", "name": "Dup Audit Widget", "category": "3d_print_physical"}
        first = asyncio.run(server.register_product_directly(body=dict(body), _token="test"))
        check(server._find_catalog_product("P3D_AUDIT_DUP_TEST") is not None, f"first registration should succeed, got {first}")
        try:
            asyncio.run(server.register_product_directly(body=dict(body), _token="test"))
            check(False, "a second registration with the identical product_id must be rejected, not silently duplicated")
        except server.HTTPException as exc:
            check(exc.status_code == 422, f"expected 422 for the duplicate product_id, got {exc.status_code}")


def run():
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FUNCTIONAL AUDIT TESTS OK -- classify_listing_for_registration correctly maps EtsyAPIError "
          "404/non-404 and generic fetch failures to 404/502 (never a bare 500), never mislabels a "
          "non-physical listing as 3d_print_physical, correctly surfaces already_registered from both "
          "the git manifest and the override sidecar, uses the lighter read-only auth dependency, and "
          "register_product's real write path never touches the git-tracked catalog/manifest files and "
          "rejects a duplicate product_id end-to-end.")


if __name__ == "__main__":
    run()
