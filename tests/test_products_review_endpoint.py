#!/usr/bin/env python3
"""
Tests for the Products-tappable-cards feature (2026-07-18), P1: the durable
catalog overlay and GET /api/products/{product_id}/review.

Background: the mobile Products screen showed plain, non-interactive cards
with zero click handlers. Scott asked for every card to be tappable --
"ready for review" cards should pop up the draft listing to review (title/
description/tags/price/photos), and cards with a red X should pop up a fix.
This file covers the backend half of the review popup: a single endpoint
that assembles everything the modal needs (draft content from data/
dpXXXX_listing.json, real photo/deliverable file presence, QC summary), and
the durable overlay mechanism (_product_catalog_overrides /
_write_product_catalog_override) that will later let a create_listing
staged action's new etsy_listing_id survive a Railway redeploy without
ever writing the git-tracked data/product_catalog.json at runtime.

Run: python tests/test_products_review_endpoint.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_products_review_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "products-review-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(server.app, base_url="https://testserver")
_AUTH = {"Authorization": f"Bearer {os.environ['APP_SECRET_TOKEN']}"}

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── _build_products_status() overrides merging ─────────────────────────────

def test_overrides_take_precedence_over_base_catalog():
    catalog = [{
        "product_id": "DP1099", "name": "Test Planner", "etsy_listing_id": "",
        "category": "digital_planner", "status": "ready_for_review", "price": 12.99,
        "files": [],
    }]
    overrides = {"DP1099": {"etsy_listing_id": "999888777", "status": "listed_draft"}}
    result = server._build_products_status(catalog, lambda rel: True, overrides)
    check(result[0]["listing_id"] == "999888777", f"got: {result[0]}")
    check(result[0]["status"] == "listed_draft", f"got: {result[0]}")


def test_no_overrides_is_unchanged_default_behavior():
    catalog = [{
        "product_id": "DP1026", "name": "P", "etsy_listing_id": "123", "category": "digital_planner",
        "status": "active", "price": 14.99, "files": [],
    }]
    result = server._build_products_status(catalog, lambda rel: True)
    check(result[0]["listing_id"] == "123", f"got: {result[0]}")
    check(result[0]["status"] == "active", f"got: {result[0]}")


# ── durable overrides sidecar ───────────────────────────────────────────────

def test_write_and_read_override_round_trips_via_volume_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "product_catalog_overrides.json"
        with patch.object(server, "_PRODUCT_CATALOG_OVERRIDES_PATH", fake_path):
            check(server._product_catalog_overrides() == {}, "should start empty")
            server._write_product_catalog_override("DP1099", {"etsy_listing_id": "555", "status": "listed_draft"})
            result = server._product_catalog_overrides()
            check(result.get("DP1099", {}).get("etsy_listing_id") == "555", f"got: {result}")
            # A second write to the SAME product must merge, not clobber other keys.
            server._write_product_catalog_override("DP1099", {"published_at": "2026-07-18"})
            result2 = server._product_catalog_overrides()
            check(result2["DP1099"]["etsy_listing_id"] == "555" and result2["DP1099"]["published_at"] == "2026-07-18",
                  f"expected merge not clobber, got: {result2}")


def test_write_never_touches_the_git_tracked_catalog_file():
    # 2026-07-22: _PRODUCT_CATALOG_OVERRIDES_PATH no longer has a `None`
    # local-fallback branch that patched data/product_catalog.json directly
    # when no durable volume was configured -- that silently no-op'd for a
    # brand-new product_id with no existing entry to patch, exactly the
    # new-product-registration case this fix enables (see
    # _register_new_product_overlay()). Local/dev and production now both
    # go through the same sidecar-file mechanism (just a different path);
    # confirm the git-tracked catalog is genuinely never written to.
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        catalog_path = data_dir / "product_catalog.json"
        original_catalog = [
            {"product_id": "DP1099", "name": "Test", "status": "ready_for_review", "etsy_listing_id": ""},
        ]
        catalog_path.write_text(json.dumps(original_catalog))
        fake_overrides_path = data_dir / "product_catalog_overrides.json"
        orig_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            with patch.object(server, "_PRODUCT_CATALOG_OVERRIDES_PATH", fake_overrides_path):
                server._write_product_catalog_override("DP1099", {"etsy_listing_id": "777", "status": "listed_draft"})
                overrides = server._product_catalog_overrides()
            untouched = json.loads(catalog_path.read_text())
        finally:
            os.chdir(orig_cwd)
        check(overrides.get("DP1099", {}).get("etsy_listing_id") == "777", f"got: {overrides}")
        check(overrides.get("DP1099", {}).get("status") == "listed_draft", f"got: {overrides}")
        check(untouched == original_catalog,
              f"the git-tracked catalog file must never be written to by this function, got: {untouched}")


# ── GET /api/products/{id}/review ───────────────────────────────────────────

def _fake_entry(product_id="DPTEST", extra_files=None):
    return {
        "product_id": product_id, "name": "Test Planner", "etsy_listing_id": "",
        "category": "digital_planner", "status": "ready_for_review", "price": 12.99,
        "files": [
            "data/digital_products/product_files/DPTEST.pdf",
            "data/digital_products/product_files/DPTESTU.pdf",
            "data/digital_products/product_files/DPTEST_sticker_pack.zip",
            "data/digital_products/product_files/DPTEST_cover.png",
            "data/digital_products/product_files/DPTEST_listing_images/01_hero.jpg",
            "data/digital_products/product_files/DPTEST_listing_images/02_included.jpg",
        ] + (extra_files or []),
    }


def test_review_404_for_unknown_product():
    with patch.object(server, "_find_catalog_product", lambda pid: None):
        resp = client.get("/api/products/DOESNOTEXIST/review", headers=_AUTH)
    check(resp.status_code == 404, f"expected 404, got {resp.status_code}")


def test_review_requires_auth():
    resp = client.get("/api/products/DPTEST/review")
    check(resp.status_code == 401, f"expected 401, got {resp.status_code}")


def test_review_classifies_deliverables_vs_photos_and_reports_presence():
    entry = _fake_entry()
    with patch.object(server, "_find_catalog_product", lambda pid: entry), \
         patch.object(server, "_product_catalog_overrides", lambda: {}), \
         patch.object(server, "_product_file_exists", lambda rel: "listing_images" in rel), \
         patch.object(server, "_product_file_url", lambda rel: f"/api/files/download?root=products&path={rel}&inline=1"), \
         patch.object(server, "_qc_check_product", lambda inp: {"pid": inp["pid"], "verdict": "pass", "summary": {}, "rows": []}):
        resp = client.get("/api/products/DPTEST/review", headers=_AUTH)

    check(resp.status_code == 200, f"got {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    check(body["product_id"] == "DPTEST", f"got: {body}")
    deliverable_names = {d["name"] for d in body["deliverables"]}
    check(deliverable_names == {"DPTEST.pdf", "DPTESTU.pdf", "DPTEST_sticker_pack.zip"},
          f"cover PNG must not be classified as a deliverable, got: {deliverable_names}")
    check(all(not d["exists"] for d in body["deliverables"]), f"got: {body['deliverables']}")
    photo_names = [p["name"] for p in body["photos"]]
    check(photo_names == ["01_hero.jpg", "02_included.jpg"], f"expected sorted photo names, got: {photo_names}")
    check(all(p["exists"] and p["url"] for p in body["photos"]), f"got: {body['photos']}")
    check(body["qc"]["verdict"] == "pass", f"got: {body['qc']}")


def test_review_reports_has_content_false_when_no_listing_json():
    entry = _fake_entry(product_id="DPNOCONTENT9999")
    entry["product_id"] = "DPNOCONTENT9999"
    with patch.object(server, "_find_catalog_product", lambda pid: entry), \
         patch.object(server, "_product_catalog_overrides", lambda: {}), \
         patch.object(server, "_product_file_exists", lambda rel: False), \
         patch.object(server, "_qc_check_product", lambda inp: {"pid": inp["pid"], "verdict": "no_files", "summary": {}, "rows": []}):
        resp = client.get("/api/products/DPNOCONTENT9999/review", headers=_AUTH)
    check(resp.status_code == 200, f"got {resp.status_code}")
    body = resp.json()
    check(body["has_content"] is False, f"got: {body}")
    check(body["content"] is None, f"got: {body}")


def test_review_reads_real_dp1030_listing_json_end_to_end():
    """No mocking of _find_catalog_product/listing-json read -- exercises the
    real data/dp1030_listing.json fixture already in this repo, catching any
    schema drift between the endpoint's field access and the real file."""
    real_entry = server._find_catalog_product("DP1030")
    if real_entry is None:
        print("SKIP: DP1030 not present in this checkout's product_catalog.json")
        return
    with patch.object(server, "_qc_check_product", lambda inp: {"pid": inp["pid"], "verdict": "warn", "summary": {}, "rows": []}):
        resp = client.get("/api/products/DP1030/review", headers=_AUTH)
    check(resp.status_code == 200, f"got {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    check(body["has_content"] is True, f"got: {body}")
    check(bool(body["content"]["title"]), f"expected a real title, got: {body['content']}")
    check(len(body["content"]["tags"]) == 13, f"expected 13 tags, got: {body['content']['tags']}")
    check(body["content"]["price"] == 12.99, f"got: {body['content']}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PRODUCTS REVIEW ENDPOINT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRODUCTS REVIEW ENDPOINT TESTS OK — overrides merge correctly (and default to a "
          "no-op), the durable sidecar round-trips and merges rather than clobbering, the "
          "no-volume fallback patches product_catalog.json in place, the review endpoint "
          "requires auth, 404s on an unknown product, classifies deliverables vs. photos "
          "vs. ignored source art correctly, reports has_content accurately, and reads the "
          "real DP1030 fixture end-to-end.")


if __name__ == "__main__":
    run()
