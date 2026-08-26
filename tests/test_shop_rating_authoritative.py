#!/usr/bin/env python3
"""
Regression test for surfacing Etsy's own authoritative shop rating in
/api/metrics (main.py's `_build_metrics`, 2026-08-22).

Why this exists: `_build_metrics`'s "reviews.avg_rating" is a flat average
over only the last `limit` reviews fetched (a windowed proxy, not Etsy's
real public-facing shop rating -- which Etsy switched to a recency-weighted
formula on Mar 13, 2026, computed internally and returned as-is in the shop
object's `review_average` field). Before this fix, the live dashboard never
surfaced that authoritative field at all -- only the standalone
tools/shop_health_check.py script (which Scott has to run manually) read
it. `_build_metrics` now also copies `shop_r["review_average"]` into
`out["reviews"]["shop_rating"]` when present, so the live dashboard can show
the same number Etsy actually displays. This test locks that mapping down
and confirms it degrades cleanly (key simply absent, no crash) when the
shop object doesn't have the field.

Run locally: python tests/test_shop_rating_authoritative.py
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_shoprating_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "shoprating-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_shop_rating_copied_from_shop_review_average():
    orders_r = {"results": []}
    reviews_r = {"results": [{"rating": 5}, {"rating": 4}], "count": 2}
    shop_r = {
        "listing_active_count": 10, "shop_name": "Test Shop",
        "transaction_sold_count": 5, "is_vacation": False,
        "review_average": 4.87,
    }
    out = server._build_metrics(orders_r, reviews_r, shop_r)
    check(out["reviews"].get("avg_rating") == 4.5,
          f"windowed avg_rating wrong: {out['reviews'].get('avg_rating')!r}")
    check(out["reviews"].get("shop_rating") == 4.87,
          f"authoritative shop_rating missing/wrong: {out['reviews'].get('shop_rating')!r}")


def test_shop_rating_absent_when_field_missing():
    orders_r = {"results": []}
    reviews_r = {"results": [{"rating": 5}], "count": 1}
    shop_r = {
        "listing_active_count": 10, "shop_name": "Test Shop",
        "transaction_sold_count": 5, "is_vacation": False,
        # deliberately no "review_average" key
    }
    out = server._build_metrics(orders_r, reviews_r, shop_r)
    check("shop_rating" not in out["reviews"],
          "shop_rating should be absent (not None/crash) when the shop object lacks the field")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("SHOP RATING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("SHOP RATING TESTS OK — /api/metrics now surfaces Etsy's own authoritative "
          "review_average alongside the windowed avg_rating proxy.")


if __name__ == "__main__":
    run()
