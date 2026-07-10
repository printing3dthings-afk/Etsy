#!/usr/bin/env python3
"""
Quality-audit rotation tests — `main.py`'s `_select_quality_audit_ids()`.

Why this exists: as part of a 2026-07-10 Etsy-API-volume reduction pass,
`_quality_audit_loop` stopped auditing the full listing catalog every run
(~516 Etsy calls/day for 172 listings) and switched to a rotating ~1/3
subset per run, prioritized by oldest/missing `last_verified` timestamp so
every listing still gets covered at least once every 3 runs. A bug here
(e.g. an off-by-one that leaves a listing permanently unaudited, or a sort
that doesn't actually prioritize stale entries) would silently create a
blind spot in listing-quality monitoring with nothing to catch it.

Run locally:  python tests/test_quality_audit_rotation.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a regression (prints which).
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Must be set BEFORE importing main -- same constraint as the other HTTP-level
# tests (module-level code seeds accounts / reconciles tokens at import time).
_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_rotation_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "rotation-test-not-a-real-secret")

sys.path.insert(0, str(ROOT / "tools" / "api_server"))
sys.path.insert(0, str(ROOT / "tools"))

from main import _select_quality_audit_ids, _QUALITY_AUDIT_ROTATION_FRACTION  # noqa: E402

_passed = 0
_failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  PASS: {name}")
    else:
        _failed += 1
        print(f"  FAIL: {name} {detail}")


def _manifest(n: int, verified_prefix: str = "2026-01") -> dict:
    """n listings, each with a distinct last_verified so ordering is deterministic."""
    return {
        f"L{i:03d}": {"last_verified": f"{verified_prefix}-{i:02d}T00:00:00Z"}
        for i in range(1, n + 1)
    }


def test_subset_size_is_ceil_of_fraction():
    for n in (1, 2, 3, 4, 5, 9, 10, 172):
        manifest = _manifest(n)
        ids = _select_quality_audit_ids(manifest)
        expected = -(-n // _QUALITY_AUDIT_ROTATION_FRACTION)
        check(f"subset size for {n} listings is {expected}", len(ids) == expected,
              f"-- got {len(ids)}")


def test_empty_manifest_returns_empty():
    check("empty manifest -> empty subset", _select_quality_audit_ids({}) == [])


def test_never_verified_listings_come_first():
    manifest = _manifest(6)
    # L002 and L005 have never been audited (missing last_verified) -- they
    # must be prioritized over everything with a real timestamp.
    del manifest["L002"]["last_verified"]
    del manifest["L005"]["last_verified"]
    ids = _select_quality_audit_ids(manifest)  # ceil(6/3) = 2
    check("never-verified listings are selected first",
          set(ids) == {"L002", "L005"}, f"-- got {ids}")


def test_full_rotation_covers_every_listing_within_fraction_runs():
    """Simulate _QUALITY_AUDIT_ROTATION_FRACTION consecutive runs, marking each
    selected listing as freshly verified (as the real loop does via
    listing_integrity_check.py's manifest write-back) -- every listing must
    have been picked at least once by the end, proving no permanent blind spot."""
    n = 172
    manifest = _manifest(n)
    seen = set()
    for round_num in range(_QUALITY_AUDIT_ROTATION_FRACTION):
        ids = _select_quality_audit_ids(manifest)
        seen.update(ids)
        for lid in ids:
            manifest[lid]["last_verified"] = f"2099-{round_num:02d}-01T00:00:00Z"  # "just verified"
    check(f"all {n} listings covered within {_QUALITY_AUDIT_ROTATION_FRACTION} rotations",
          seen == set(manifest.keys()),
          f"-- missing {set(manifest.keys()) - seen}")


def test_small_manifest_never_returns_empty_subset():
    for n in (1, 2):
        ids = _select_quality_audit_ids(_manifest(n))
        check(f"manifest of {n} listing(s) yields a non-empty subset", len(ids) >= 1)


def main() -> int:
    print("Running quality-audit rotation tests...\n")
    for fn in (
        test_subset_size_is_ceil_of_fraction,
        test_empty_manifest_returns_empty,
        test_never_verified_listings_come_first,
        test_full_rotation_covers_every_listing_within_fraction_runs,
        test_small_manifest_never_returns_empty_subset,
    ):
        try:
            fn()
        except Exception:
            global _failed
            _failed += 1
            print(f"  FAIL: {fn.__name__} raised an exception")
            traceback.print_exc()
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
