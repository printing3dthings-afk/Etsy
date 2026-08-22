"""Regression test: /api/metrics must serialize active_listing_goal (Home ticker,
2026-07-23). Standalone-script harness per .claude/rules/testing.md."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_home_ticker_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "home-ticker-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_active_listing_goal_serialized():
    out = server._build_metrics(
        {},
        {},
        {"listing_active_count": 42, "shop_name": "Test Shop", "transaction_sold_count": 1},
    )
    check(
        out["shop"].get("active_listing_goal") == server._ACTIVE_LISTING_GOAL,
        f"expected active_listing_goal={server._ACTIVE_LISTING_GOAL!r}, got {out['shop']!r}",
    )
    check(
        out["shop"].get("active_listing_count") == 42,
        "active_listing_count must still be present alongside the new field",
    )


def test_active_listing_goal_survives_shop_error():
    out = server._build_metrics({}, {}, Exception("etsy down"))
    check(
        "active_listing_goal" not in out["shop"],
        "when shop_r itself failed, out['shop'] should only carry the error, not a stray goal field",
    )
    check("error" in out["shop"], f"expected shop error to be recorded, got {out['shop']!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback

            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("HOME TICKER METRICS TEST FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("HOME TICKER METRICS TEST OK — /api/metrics exposes active_listing_goal for the Home ticker.")


if __name__ == "__main__":
    run()
