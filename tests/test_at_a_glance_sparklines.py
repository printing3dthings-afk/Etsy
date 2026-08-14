"""
Test for the 2026-08-14 mini-sparkline addition to the Star Seller / Ads &
ROAS / COGS & Profit at-a-glance panels on Command Center (third item from
the visual-research pass, after View Transitions and skeleton loaders).

These 3 panels already fetch 30 days of trend history via /api/status-history
(loadStarSeller/loadAdsStatus/loadCogsStatus, stashed in _lastStatusHistory --
originally added 2026-07-22 Phase 3 to feed the bigger metric-detail modal's
chart) but never surfaced any of that data inline in the panel itself, only
behind a tap-to-open modal. This reuses the exact same already-fetched trend
array and the existing _miniSpark() helper (already used for the Shop
Performance cards and the metric-detail modal, just at a smaller 28px height
here) -- zero new network calls, zero new charting code.

Run: python tests/test_at_a_glance_sparklines.py
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


def _source() -> str:
    return HUD_PATH.read_text(encoding="utf-8")


def _function_body(source: str, fn_name: str) -> str:
    m = re.search(r"async function " + re.escape(fn_name) + r"\(\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, f"could not find async function {fn_name}()"
    return m.group(1)


# fn -> (history key, color, spark label substring)
_TARGETS = {
    "loadStarSeller": ("star_seller", "var(--gold)", "Revenue trend"),
    "loadAdsStatus": ("ads_roas", "var(--cyan2)", "ROAS trend"),
    "loadCogsStatus": ("cogs_margin", "var(--green)", "margin trend"),
}


def test_all_3_panels_render_a_sparkline_from_already_fetched_history():
    source = _source()
    for fn_name, (history_key, color, label_substr) in _TARGETS.items():
        body = _function_body(source, fn_name)
        check(f"_lastStatusHistory.{history_key}" in body,
              f"{fn_name} should already be stashing history under _lastStatusHistory.{history_key} "
              f"(pre-existing Phase 3 fetch) -- reused here, not a new endpoint")
        check("_miniSpark((_lastStatusHistory." + history_key + "||{}).trend, '" + color + "', 28)" in body,
              f"{fn_name} should render a 28px _miniSpark() from the already-fetched trend array in "
              f"color {color}, matching METRIC_DETAIL_CONFIG's color for the same metric")
        check(label_substr in body, f"{fn_name}'s sparkline row should be labeled with '{label_substr}'")
        check('class="ss-spark-row"' in body, f"{fn_name} should wrap its sparkline in .ss-spark-row")


def test_sparkline_row_uses_the_shared_null_safe_trend_lookup():
    """(_lastStatusHistory.X||{}).trend -- must tolerate history not having
    loaded yet (e.g. the panel's own fetch failed) without throwing, since
    _miniSpark() itself already handles an undefined/short values array via
    its own 'Accumulating daily data' fallback."""
    source = _source()
    for fn_name, (history_key, _color, _label) in _TARGETS.items():
        body = _function_body(source, fn_name)
        check(f"(_lastStatusHistory.{history_key}||{{}}).trend" in body,
              f"{fn_name}'s sparkline call must null-guard the history lookup with ||{{}} so a missing "
              f"fetch result can't throw on .trend")


def test_spark_row_css_exists_and_is_visually_separated_from_the_stat_rows():
    source = _source()
    check(".ss-spark-row{" in source, "missing .ss-spark-row CSS rule")
    check(".ss-spark-lab{" in source, "missing .ss-spark-lab CSS rule")
    m = re.search(r"\.ss-spark-row\{([^}]*)\}", source)
    assert m, "could not find .ss-spark-row CSS block"
    check("border-top" in m.group(1),
          "the sparkline row should have a visual divider from the stat rows above it, matching the "
          "existing .ss-row border-bottom convention used throughout this panel family")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("AT-A-GLANCE SPARKLINE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("AT-A-GLANCE SPARKLINE TESTS OK — Star Seller/Ads/COGS panels each render a null-safe "
          "28px _miniSpark() from their already-fetched status-history trend, with matching CSS.")


if __name__ == "__main__":
    run()
