#!/usr/bin/env python3
"""
Smoke test for tools/listing_integrity_check.py's audit_listing() -- the
per-listing FAST-mode audit engine, also reused verbatim by
tools/listing_compliance_sweep.py's full-shop compliance sweep. Had zero
test coverage before this file (2026-07-09 go-live readiness pass): a
careless edit to any of its check_* functions could silently start passing
FAIL-worthy listings, or start failing clean ones, with nothing catching it
before it ran against the live shop again.

Dependency-light: builds a fake EtsyAPIClient whose _request() returns
canned fixture data instead of hitting the real Etsy API, matching the style
tests/test_staged_actions.py already uses for _validate_staged_action. No
network, no credentials, no PIL/full-mode photo hashing (that's the explicit
FAST-mode/full-mode split the module itself documents).

Run locally:  python tests/test_listing_integrity.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a regression (prints which).
"""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools", ROOT):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import listing_integrity_check as lic  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# A minimal type rule matching the shape of data/listing_rules.json entries.
_RULE = {
    "min_photos": 5,
    "required_description_sections": ["AI_DISCLOSURE"],
    "required_description_keywords": ["instant download"],
    "fulfillment": "digital",
}
_RULES = {"wall_art": _RULE, "unknown": _RULE}


class _FakeEtsyClient:
    """Serves canned _request() responses keyed by (method, path suffix) --
    just enough of EtsyAPIClient's surface for audit_listing() to run.
    `shop_id` is read directly by audit_listing's files-fetch call."""

    def __init__(self, listing: dict, files: list, images: list):
        self.shop_id = "12345"
        self._listing = listing
        self._files = files
        self._images = images

    def _request(self, method: str, path: str, params=None, body=None):
        if path.startswith("listings/") and path.endswith("/images"):
            return {"results": self._images}
        if path.startswith("listings/") and "/files" not in path and "images" not in path:
            return self._listing
        if "/files" in path:
            return {"results": self._files}
        raise AssertionError(f"unexpected _request path: {method} {path}")


_GOOD_LISTING = {
    "state": "active",
    "title": "Boho Sun Wall Art, Printable Poster, Instant Download",
    "description": (
        "Instant download printable wall art. This product was designed using AI "
        "image generation tools, with original prompts, curation, and finishing by "
        "the seller. All products are reviewed for quality before listing."
    ),
    "tags": [f"tag{i}" for i in range(13)],
}
_GOOD_FILES = [{"filename": "DP1001_print_sizes.zip"}]
_GOOD_IMAGES = [{"rank": i, "url_fullxfull": f"https://example.test/{i}.jpg"} for i in range(1, 6)]
_GOOD_ENTRY = {"dp_codes": ["DP1001"], "type": "wall_art", "expected_files": [], "expected_file_count": 1}


def test_audit_listing_passes_a_fully_compliant_listing():
    api = _FakeEtsyClient(_GOOD_LISTING, _GOOD_FILES, _GOOD_IMAGES)
    r = lic.audit_listing(api, "9990001", _GOOD_ENTRY, _RULES, {}, {}, full_mode=False)
    check(r["status"] == "PASS", f"expected PASS, got {r['status']}: {r['issues']}")
    check(r["file_count"] == 1, f"expected file_count 1, got {r['file_count']}")
    check(r["photo_count"] == 5, f"expected photo_count 5, got {r['photo_count']}")


def test_audit_listing_fails_an_oversized_title():
    bad = dict(_GOOD_LISTING, title="X" * 71)
    api = _FakeEtsyClient(bad, _GOOD_FILES, _GOOD_IMAGES)
    r = lic.audit_listing(api, "9990002", _GOOD_ENTRY, _RULES, {}, {}, full_mode=False)
    check(r["status"] == "FAIL", f"expected FAIL for a 71-char title, got {r['status']}")
    check(any(i["check"] == "title_length" for i in r["issues"]),
          f"expected a title_length issue, got {r['issues']}")


def test_audit_listing_fails_missing_expected_file():
    api = _FakeEtsyClient(_GOOD_LISTING, [{"filename": "wrong_file.zip"}], _GOOD_IMAGES)
    entry = dict(_GOOD_ENTRY, expected_files=["DP1001_print_sizes.zip"], expected_file_count=1)
    r = lic.audit_listing(api, "9990003", entry, _RULES, {}, {}, full_mode=False)
    check(r["status"] == "FAIL", f"expected FAIL for a missing expected file, got {r['status']}")
    check(any(i["check"] == "file_match" for i in r["issues"]),
          f"expected a file_match issue, got {r['issues']}")


def test_audit_listing_warns_on_too_few_tags():
    bad = dict(_GOOD_LISTING, tags=["only", "three", "tags"])
    api = _FakeEtsyClient(bad, _GOOD_FILES, _GOOD_IMAGES)
    r = lic.audit_listing(api, "9990004", _GOOD_ENTRY, _RULES, {}, {}, full_mode=False)
    check(r["status"] == "FAIL", f"expected FAIL for only 3 tags (below the 13 required), got {r['status']}")
    check(any(i["check"] == "tag_count" for i in r["issues"]),
          f"expected a tag_count issue, got {r['issues']}")


def test_audit_listing_fails_digital_listing_claiming_physical_shipping():
    bad = dict(_GOOD_LISTING, description=_GOOD_LISTING["description"] + " Ships to your door in 3-5 days.")
    api = _FakeEtsyClient(bad, _GOOD_FILES, _GOOD_IMAGES)
    r = lic.audit_listing(api, "9990005", _GOOD_ENTRY, _RULES, {}, {}, full_mode=False)
    check(r["status"] == "FAIL", f"expected FAIL for a digital listing claiming shipping, got {r['status']}")
    check(any(i["check"] == "fulfillment_mismatch" for i in r["issues"]),
          f"expected a fulfillment_mismatch issue, got {r['issues']}")


def test_audit_listing_fails_approval_drift_on_title_change():
    api = _FakeEtsyClient(_GOOD_LISTING, _GOOD_FILES, _GOOD_IMAGES)
    approvals = {"9990006": {"title": "A completely different approved title", "file_names": []}}
    r = lic.audit_listing(api, "9990006", _GOOD_ENTRY, _RULES, approvals, {}, full_mode=False)
    check(r["status"] == "FAIL", f"expected FAIL for title drift since approval, got {r['status']}")
    check(any(i["check"] == "approval_drift" for i in r["issues"]),
          f"expected an approval_drift issue, got {r['issues']}")


def test_audit_listing_handles_fetch_failure_as_fail_not_crash():
    class _BrokenClient:
        shop_id = "12345"

        def _request(self, *a, **kw):
            raise RuntimeError("simulated network failure")

    r = lic.audit_listing(_BrokenClient(), "9990007", _GOOD_ENTRY, _RULES, {}, {}, full_mode=False)
    check(r["status"] == "FAIL", f"a fetch failure must surface as FAIL, not raise, got {r['status']}")
    check(any(i["check"] == "listing_fetch" for i in r["issues"]),
          f"expected a listing_fetch issue, got {r['issues']}")
    check(r.get("fetch_error") is True,
          f"a fetch failure must set fetch_error=True (to be distinguished from a real "
          f"content FAIL by the manifest write-back and _quality_audit_iteration), "
          f"got {r.get('fetch_error')!r}")


def test_audit_listing_content_fail_does_not_set_fetch_error():
    bad = dict(_GOOD_LISTING, title="X" * 71)
    api = _FakeEtsyClient(bad, _GOOD_FILES, _GOOD_IMAGES)
    r = lic.audit_listing(api, "9990008", _GOOD_ENTRY, _RULES, {}, {}, full_mode=False)
    check(r["status"] == "FAIL", f"expected FAIL for a 71-char title, got {r['status']}")
    check(r.get("fetch_error") is False,
          f"a real content FAIL (listing was fetched fine) must NOT set fetch_error, "
          f"got {r.get('fetch_error')!r}")


def test_manifest_write_back_skips_last_verified_for_fetch_errors():
    manifest = {"L1": {"last_verified": "2020-01-01T00:00:00Z"},
                "L2": {"last_verified": "2020-01-01T00:00:00Z"}}
    results = [
        {"listing_id": "L1", "status": "FAIL", "fetch_error": True},
        {"listing_id": "L2", "status": "PASS", "fetch_error": False},
    ]
    lic._apply_manifest_updates(manifest, results)
    check(manifest["L1"]["last_verified"] == "2020-01-01T00:00:00Z",
          "fetch-error result must NOT stamp last_verified -- the listing was never "
          f"actually checked, got {manifest['L1']['last_verified']!r}")
    check(manifest["L2"]["last_verified"] != "2020-01-01T00:00:00Z",
          "a real (non-fetch-error) result must stamp last_verified")
    check(manifest["L1"]["last_status"] == "FAIL" and manifest["L2"]["last_status"] == "PASS",
          f"last_status is recorded regardless of fetch_error, got "
          f"{manifest['L1']['last_status']!r}/{manifest['L2']['last_status']!r}")


def test_render_report_flags_fetch_errors_separately_from_real_fails():
    results = [
        lic.audit_listing(_FakeEtsyClient(dict(_GOOD_LISTING, title="X" * 71), _GOOD_FILES, _GOOD_IMAGES),
                          "1", _GOOD_ENTRY, _RULES, {}, {}, full_mode=False),
    ]

    class _BrokenClient:
        shop_id = "12345"

        def _request(self, *a, **kw):
            raise RuntimeError("simulated network failure")

    results.append(lic.audit_listing(_BrokenClient(), "2", _GOOD_ENTRY, _RULES, {}, {}, full_mode=False))
    report = lic.render_report(results, elapsed=1.23)
    check("FAIL: 2" in report, f"expected both results counted as FAIL, got: {report.splitlines()[4]}")
    check("FETCH_ERR: 1" in report,
          f"expected exactly 1 fetch-error flagged separately, got: {report.splitlines()[4]}")


_TYPED_MANIFEST = {
    "A1": {"type": "wall_art"}, "A2": {"type": "wall_art"},
    "C1": {"type": "coloring_pages"}, "C2": {"type": "coloring_pages"},
}


def test_type_filter_narrows_ids_selection_instead_of_replacing_it():
    to_audit, missing = lic._select_manifest_entries(_TYPED_MANIFEST, None, "A1,C1", "wall_art")
    check(set(to_audit) == {"A1"}, f"expected only A1 (wall_art within the --ids set), got {to_audit}")
    check(missing == [], f"expected no missing ids, got {missing}")


def test_type_filter_narrows_single_id_selection():
    to_audit, missing = lic._select_manifest_entries(_TYPED_MANIFEST, "C1", None, "wall_art")
    check(to_audit == {}, f"C1 is coloring_pages, not wall_art -- expected empty, got {to_audit}")


def test_type_filter_alone_still_narrows_full_manifest():
    to_audit, missing = lic._select_manifest_entries(_TYPED_MANIFEST, None, None, "wall_art")
    check(set(to_audit) == {"A1", "A2"}, f"expected both wall_art listings, got {to_audit}")


def test_no_filters_returns_full_manifest():
    to_audit, missing = lic._select_manifest_entries(_TYPED_MANIFEST, None, None, None)
    check(set(to_audit) == set(_TYPED_MANIFEST), f"expected the full manifest, got {to_audit}")


def test_ids_filter_reports_missing_ids():
    to_audit, missing = lic._select_manifest_entries(_TYPED_MANIFEST, None, "A1,ZZZ", None)
    check(set(to_audit) == {"A1"}, f"expected only A1, got {to_audit}")
    check(missing == ["ZZZ"], f"expected ZZZ reported missing, got {missing}")


def test_render_report_runs_without_crashing_on_mixed_results():
    results = [
        lic.audit_listing(_FakeEtsyClient(_GOOD_LISTING, _GOOD_FILES, _GOOD_IMAGES),
                          "1", _GOOD_ENTRY, _RULES, {}, {}, full_mode=False),
        lic.audit_listing(_FakeEtsyClient(dict(_GOOD_LISTING, title="X" * 71), _GOOD_FILES, _GOOD_IMAGES),
                          "2", _GOOD_ENTRY, _RULES, {}, {}, full_mode=False),
    ]
    report = lic.render_report(results, elapsed=1.23)
    check(isinstance(report, str) and "LISTING INTEGRITY REPORT" in report,
          "render_report should produce a text report containing the header")
    check("PASS: 1" in report and "FAIL: 1" in report,
          f"report summary line should reflect 1 PASS / 1 FAIL, got: {report.splitlines()[4]}")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ran = 0
    for t in tests:
        try:
            t()
            ran += 1
        except Exception:
            _failures.append(f"{t.__name__} raised an unexpected error:\n" + traceback.format_exc())
    if _failures:
        print("LISTING INTEGRITY TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"LISTING INTEGRITY TESTS OK — {ran} tests passed "
          f"(audit_listing() fast-mode checks + render_report, via fixture data).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
