"""
Tests for the COGS/profit-per-listing HUD panel (Frank upgrade Wave 2,
capabilities item 4, 2026-07-17).

Closes the capabilities-audit finding: "no COGS/profit-per-listing panel
exists." No real per-listing cost data exists anywhere in this codebase
(checked product_catalog.json, makerworld_specs.json, business_config.py --
confirmed empty by research before writing any code), so this is explicitly
an ESTIMATE: real Etsy fee math (6.5% transaction + 3%+$0.25 processing +
$0.20 listing, from CLAUDE.md's documented rates) and real recent units sold
(from the existing _sales_by_listing_sync(), sourced from actual paid
receipts) combined with an estimated product-type guess (title keywords,
reusing order_notifier.py's own classifier so the two never drift) and a
flat $7.50/unit COGS guess for 3D-print physical items (data/financial/
profit_loss.md's "Typical" figure) vs. $0 for digital. The endpoint's own
"note" field states this plainly rather than presenting a guess as fact.

Self-contained, mirrors tests/test_pinterest_wiring.py's pattern. Uses real
math verification (hand-computed expected fee/margin numbers), not just
"did it return something."

Run: python tests/test_cogs_status.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_cogs_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "cogs-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── product-type classification reuse ───────────────────────────────────────
def test_classifier_reuses_order_notifier_not_a_copy():
    import order_notifier
    for title in [
        "3D Printed Custom Vase Silk PLA Home Decor",
        "Digital Planner 2026 Undated, GoodNotes iPad",
        "Kawaii Sticker Pack GoodNotes Elements",
        "Boho Botanical Wall Art Printable Poster",
        "Random Untitled Product",
    ]:
        expected = order_notifier._classify(title)
        got = server._classify_product_type_for_cogs(title)
        check(got == expected, f"classification for {title!r} should match order_notifier._classify (got {got}, expected {expected})")


# ── fee/margin math ──────────────────────────────────────────────────────────
def test_digital_listing_has_zero_cogs():
    econ = server._estimate_listing_economics(14.99, "Digital Planner 2026 Undated, GoodNotes iPad, Instant Download")
    check(econ["is_physical_estimate"] is False, f"a planner title must not be classified physical, got: {econ}")
    check(econ["cogs_estimate"] == 0.0, f"digital COGS must be $0, got: {econ['cogs_estimate']}")


def test_physical_listing_has_positive_cogs():
    econ = server._estimate_listing_economics(19.99, "3D Printed Custom Vase Silk PLA Home Decor")
    check(econ["is_physical_estimate"] is True, f"a 3D print title must be classified physical, got: {econ}")
    check(econ["cogs_estimate"] == server._PHYSICAL_COGS_ESTIMATE_USD,
          f"physical COGS must equal the documented typical estimate, got: {econ['cogs_estimate']}")


def test_fee_math_matches_hand_computation():
    # $14.99 digital: transaction 14.99*.065=0.97435, processing 14.99*.03+.25=0.6997,
    # listing .20 -> fees = 0.97435+0.6997+0.20 = 1.87405 ~ 1.87
    econ = server._estimate_listing_economics(14.99, "Digital Planner 2026 Undated GoodNotes")
    expected_fees = round(14.99 * 0.065 + (14.99 * 0.03 + 0.25) + 0.20, 2)
    check(econ["fees_real"] == expected_fees, f"expected fees {expected_fees}, got {econ['fees_real']}")
    expected_net = round(14.99 - expected_fees - 0.0, 2)
    check(econ["net_estimate"] == expected_net, f"expected net {expected_net}, got {econ['net_estimate']}")
    expected_margin = round(expected_net / 14.99 * 100, 1)
    check(econ["margin_pct"] == expected_margin, f"expected margin {expected_margin}, got {econ['margin_pct']}")


def test_cheap_physical_listing_can_go_negative():
    # A $6.99 3D print: fees ~1.11, COGS 7.50 -> net should be negative,
    # proving the panel can actually surface a real pricing problem, not just
    # always-positive numbers.
    econ = server._estimate_listing_economics(6.99, "Cheap 3D Printed Koozie Holder")
    check(econ["net_estimate"] < 0, f"an underpriced physical item should show negative net, got: {econ}")
    check(econ["margin_pct"] < 0, f"and a negative margin, got: {econ['margin_pct']}")


def test_zero_price_does_not_divide_by_zero():
    econ = server._estimate_listing_economics(0, "Some Draft Listing With No Price Yet")
    check(econ["margin_pct"] == 0.0, f"a $0 price must not crash or produce a nonsense margin, got: {econ}")


# ── graceful degradation on a real Etsy failure (regression) ───────────────
def test_compute_cogs_status_survives_a_real_listings_fetch_failure():
    # Regression for a bug caught live via playwright_smoke.py, not by any
    # unit test (every other test here mocks _listings_sync to return data
    # directly, so none of them exercised the real failure path): this
    # sandbox has no Etsy OAuth token, so the REAL _listings_sync() raises
    # EtsyAPIError uncaught -- confirmed by calling it directly below. Before
    # the fix, _compute_cogs_status() let that propagate, which FastAPI
    # turned into a raw 500 (later 503 once wrapped in _fetch_with_degrade,
    # still a console error) on /api/cogs-status. It must instead report
    # used=False, the same "nothing to show" contract _compute_ads_status()
    # already uses -- not a crash, not a 503, an honest empty state.
    import etsy_api
    try:
        server._listings_sync("active")
        _failures.append(
            "expected _listings_sync to raise in this credential-less sandbox -- "
            "if this no longer raises, the regression this test guards against may "
            "no longer be reachable; revisit whether this test is still needed"
        )
    except etsy_api.EtsyAPIError:
        pass  # confirms the real unmocked call really does fail here, as expected

    result = server._compute_cogs_status()
    check(result == {"used": False},
          f"a real (unmocked) Etsy fetch failure must degrade to used=False, not raise or 500/503, got: {result}")


# ── shop-wide aggregation ────────────────────────────────────────────────────
def test_compute_cogs_status_with_no_listings_reports_unused():
    orig = server._listings_sync
    try:
        server._listings_sync = lambda state="active": {"listings": [], "count": 0, "state": "active"}
        result = server._compute_cogs_status()
        check(result == {"used": False}, f"zero active listings should report used=False, got: {result}")
    finally:
        server._listings_sync = orig


def test_compute_cogs_status_aggregates_correctly():
    orig_listings = server._listings_sync
    orig_sales = server._sales_by_listing_sync
    try:
        server._listings_sync = lambda state="active": {
            "listings": [
                {"listing_id": 1, "title": "Digital Planner 2026 Undated GoodNotes iPad Instant Download", "price": 14.99},
                {"listing_id": 2, "title": "3D Printed Custom Vase Silk PLA Home Decor", "price": 19.99},
                {"listing_id": 3, "title": "Cheap 3D Printed Koozie Holder", "price": 6.99},
            ],
            "count": 3, "state": "active",
        }
        server._sales_by_listing_sync = lambda: {1: 20, 2: 3, 3: 5}

        result = server._compute_cogs_status()
        check(result["used"] is True, f"with real listings this must report used=True, got: {result}")
        check(result["listing_count"] == 3, f"expected 3 listings counted, got: {result['listing_count']}")
        check(result["total_recent_units"] == 28, f"expected 20+3+5=28 units, got: {result['total_recent_units']}")

        # listing 3 (koozie) has a negative estimated net -> must appear in flagged_low_margin
        flagged_ids = [f["listing_id"] for f in result["flagged_low_margin"]]
        check(3 in flagged_ids, f"the underpriced koozie listing must be flagged low-margin, got flagged: {flagged_ids}")

        # listing 1 (digital, highest volume + highest margin) should be the top profit listing
        check(result["top_profit_listings"][0]["listing_id"] == 1,
              f"the digital planner (20 units, ~87% margin) should rank #1 by profit, got: {result['top_profit_listings']}")

        check("estimate" in result["note"].lower(), f"the note must call this an estimate, got: {result['note']!r}")
        check("real" in result["note"].lower(), f"the note should also say which parts ARE real, got: {result['note']!r}")
    finally:
        server._listings_sync = orig_listings
        server._sales_by_listing_sync = orig_sales


def test_flagged_low_margin_capped_at_five_and_sorted_ascending():
    orig_listings = server._listings_sync
    orig_sales = server._sales_by_listing_sync
    try:
        # 7 underpriced physical listings -- only the 5 worst should be flagged, sorted worst-first
        fake = {
            "listings": [
                {"listing_id": i, "title": f"3D Printed Item {i}", "price": 5.00 + i * 0.1}
                for i in range(1, 8)
            ],
            "count": 7, "state": "active",
        }
        server._listings_sync = lambda state="active": fake
        server._sales_by_listing_sync = lambda: {}

        result = server._compute_cogs_status()
        check(len(result["flagged_low_margin"]) == 5, f"expected at most 5 flagged, got {len(result['flagged_low_margin'])}")
        margins = [f["margin_pct"] for f in result["flagged_low_margin"]]
        check(margins == sorted(margins), f"flagged listings must be sorted worst-margin-first, got: {margins}")
    finally:
        server._listings_sync = orig_listings
        server._sales_by_listing_sync = orig_sales


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("COGS STATUS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COGS STATUS TESTS OK — classifier reuse, fee/margin math (hand-verified), "
          "zero-price guard, negative-margin detection, shop-wide aggregation, and the "
          "5-item flagged-listing cap/sort all verified.")


if __name__ == "__main__":
    run()
