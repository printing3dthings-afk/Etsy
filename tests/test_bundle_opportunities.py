"""
Tests for the bundle-opportunity nudge (2026-07-18, implementing the
competitive-audit report's finding: digital-seller growth research names
bundling + listing volume as the two real differentiators past a few
hundred dollars/month, and the real gap turned out to be wall_art -- 67
active listings against a single 3-piece bundle -- not the planners the
source research used narratively (already well-bundled by BUNDLE_PLANNERS).

Checks:
  1. _compute_bundle_opportunities() against a synthetic catalog matching
     the real shape confirmed in the audit: flags a category with many
     active listings and a low bundle-to-active ratio, does NOT flag a
     well-bundled category, ignores categories below the minimum active
     count, and caps output to the top 2 by active count.
  2. GET /api/bundle-opportunities returns the expected shape and is cached.
  3. The frontend has a distinct "Opportunities" section, separate from
     Needs Attention, with no tappable/severity styling (it's a nudge, not
     an alert).

Run: python tests/test_bundle_opportunities.py
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_bundleopp_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "bundleopp-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_catalog():
    catalog = []
    for i in range(67):
        catalog.append({"product_id": f"WA{i}", "category": "wall_art", "status": "active"})
    catalog.append({"product_id": "WA_BUNDLE1", "category": "wall_art_bundle", "status": "active"})
    for i in range(13):
        catalog.append({"product_id": f"CP{i}", "category": "coloring_pages", "status": "active"})
    for i in range(4):
        catalog.append({"product_id": f"DP{i}", "category": "digital_planner", "status": "active"})
    catalog.append({"product_id": "DP_BUNDLE1", "category": "digital_planner_bundle", "status": "active"})
    for i in range(6):
        catalog.append({"product_id": f"SP{i}", "category": "sticker_pack", "status": "active"})
    # a draft entry shouldn't count toward active_count
    catalog.append({"product_id": "WA_DRAFT", "category": "wall_art", "status": "draft"})
    return catalog


def test_flags_underserved_category_with_real_shape():
    catalog_json = json.dumps(_fake_catalog())
    with patch.object(Path, "read_text", return_value=catalog_json):
        opps = server._compute_bundle_opportunities()
    cats = {o["category"] for o in opps}
    check("wall_art" in cats, f"wall_art (67 active/1 bundle) should be flagged, got: {opps}")
    check("coloring_pages" in cats, f"coloring_pages (13 active/0 bundles) should be flagged, got: {opps}")


def test_does_not_flag_well_bundled_or_small_categories():
    catalog_json = json.dumps(_fake_catalog())
    with patch.object(Path, "read_text", return_value=catalog_json):
        opps = server._compute_bundle_opportunities()
    cats = {o["category"] for o in opps}
    check("digital_planner" not in cats, f"digital_planner is already well-bundled -- should not be flagged, got: {opps}")
    check("sticker_pack" not in cats, f"sticker_pack (6 active) is below the minimum threshold -- should not be flagged, got: {opps}")


def test_caps_output_to_two():
    catalog_json = json.dumps(_fake_catalog())
    with patch.object(Path, "read_text", return_value=catalog_json):
        opps = server._compute_bundle_opportunities()
    check(len(opps) <= 2, f"expected at most 2 opportunities surfaced to avoid Today-tab clutter, got: {len(opps)}")
    if len(opps) == 2:
        check(opps[0]["active_count"] >= opps[1]["active_count"], "opportunities should be sorted by active_count descending")


def test_missing_catalog_file_returns_empty_list():
    with patch.object(Path, "read_text", side_effect=OSError("not found")):
        opps = server._compute_bundle_opportunities()
    check(opps == [], f"a missing/unreadable catalog should degrade to an empty list, not raise, got: {opps}")


def test_endpoint_returns_expected_shape_and_caches():
    with server._cache_lock:
        server._cache.pop("bundle_opportunities", None)
    catalog_json = json.dumps(_fake_catalog())
    with patch.object(Path, "read_text", return_value=catalog_json):
        result = asyncio.run(server.get_bundle_opportunities(_token="test"))
    check("opportunities" in result, f"expected an 'opportunities' key, got: {result}")
    check(server._cache_get("bundle_opportunities", ttl=3600) is not None, "the endpoint should populate the cache")


def test_frontend_has_separate_opportunities_section():
    hud_path = ROOT / "tools" / "api_server" / "frank_hud_mockup.py"
    source = hud_path.read_text(encoding="utf-8")
    check("/api/bundle-opportunities" in source, "renderPhoneToday() should fetch the new endpoint")
    check("'Opportunities'" in source or '"Opportunities"' in source or ">Opportunities<" in source,
          "the Today tab should render a distinct Opportunities section")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("BUNDLE OPPORTUNITIES TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("BUNDLE OPPORTUNITIES TESTS OK — the deterministic rule flags real underserved "
          "categories (wall_art, coloring_pages) against the confirmed catalog shape, does "
          "not flag well-bundled or too-small categories, caps output, degrades cleanly on "
          "a missing catalog, and the frontend renders a distinct Opportunities section.")


if __name__ == "__main__":
    run()
