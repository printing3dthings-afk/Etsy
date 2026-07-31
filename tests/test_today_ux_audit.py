"""
Regression tests for the Today screen UX audit (2026-07-31, fifth screen in the
screen-by-screen audit after Login/Home/Ask-Chat/Approvals). Today
(renderPhoneToday()) is mobile-only with no desktop equivalent, so all of these
are pure frontend (frank_hud_mockup.py) source-substring checks in the same
style as test_approvals_ux_audit.py/test_tour_copy_accuracy.py, except finding
2's backend field (covered separately in test_products_file_integrity.py) and
finding 6's backend timestamp field (covered separately in
test_http_routes.py::test_listings_serves_stale_cache_when_etsy_unavailable).

Findings fixed (see ops_runbook.md 2026-07-31 entry for the full writeup):
  1. Alert `detail` text was fetched but discarded (sub:'' hardcoded) -- Frank's
     own remediation steps never reached the screen.
  2. product_file_integrity alerts (the single highest-severity alert type --
     "customer might receive nothing") could never be tapped to act on, and
     the "Let Frank fix it" button (Conversion Doctor -- title/tags/description
     only) has zero relationship to a missing file, so it's suppressed for
     this alert type; only "View on Etsy" shows.
  3. A same-day calendar reminder (severity 'info') rendered with a green
     "all good" dot inside a section titled "Needs attention" -- now reuses
     this app's existing cyan info convention instead.
  4. The 5 Today fetches ran sequentially instead of via Promise.all.
  5. Today never polled while open (unlike Approvals' 2026-07-30 fix), and its
     badge only ever reflected /api/actions, never /api/alerts -- a standing
     critical alert (credential leak, expired token, budget overage) could
     show a red dot on Today with zero corresponding badge nudge. Fixed via a
     30s active-tab poll plus a shared _alertsCritWarnCount folded into
     setActionBadge()'s own computation (not a one-shot DOM push, which would
     get clobbered back down by the independent 30s loadQueue() tick).
  6. Metrics/Star Seller tiles could silently render a stale cache-fallback
     payload (stale:true) as if it were live, with the count-up tile animation
     actively reinforcing the false impression. Fixed by skipping the
     animation and showing the existing _offlineNote() pattern.

Run: python tests/test_today_ux_audit.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def run() -> None:
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text(encoding="utf-8")

    today_start = src.index("async function renderPhoneToday()")
    today_end = src.index("function phoneNeedsSheet(i)")
    today_body = src[today_start:today_end]

    # ── 1. Alert detail -> sub threading ────────────────────────────────
    check("x.detail || ''" in today_body,
          "the alerts.forEach mapper should thread x.detail into sub instead of hardcoding ''")

    # ── 2. product_file_integrity tappable + View-only sheet ────────────
    check("listing_id: x.listing_id, url: x.url, source: x.source || 'alert'" in today_body,
          "the alerts.forEach mapper should copy listing_id/url/source through so a "
          "structured alert (e.g. product_file_integrity) can become tappable")
    check("source: 'action'" in today_body,
          "the acts.forEach mapper should tag recommendation-sourced items as source:'action' "
          "so setActionBadge()'s alerts-only count doesn't double-count them")
    sheet_start = src.index("function phoneNeedsSheet(i)")
    sheet_end = src.index("function phoneSheetClose()")
    sheet_body = src[sheet_start:sheet_end]
    check("product_file_integrity" in sheet_body and "phone-sheet-fix" in sheet_body,
          "phoneNeedsSheet() should suppress the Fix button for product_file_integrity alerts "
          "(the Conversion Doctor route it calls has no relationship to a missing file)")

    # ── 3. info-severity dot uses the existing cyan convention, not green ──
    check("s.includes('info') ? 'info'" in today_body,
          "sevOf() should map 'info' severity to its own bucket instead of falling through to 'good'")
    check(".palert.info .pdot{background:var(--cyan)}" in src,
          "expected a .palert.info rule reusing the existing --cyan info convention")

    # ── 4. Promise.all instead of sequential awaits ──────────────────────
    check("await Promise.all([" in today_body,
          "renderPhoneToday()'s 5 fetches should run via Promise.all, not one after another")

    # ── 5. 30s active-tab poll + badge shared state (not a one-shot DOM push) ──
    check("let _alertsCritWarnCount = 0;" in src,
          "expected a shared _alertsCritWarnCount variable that setActionBadge() folds into its "
          "own computation, so the count survives the independent 30s loadQueue() tick")
    badge_start = src.index("function setActionBadge(summary, pending)")
    badge_end = src.index("function simpleLineDiff(")
    badge_body = src[badge_start:badge_end]
    check("+ _alertsCritWarnCount" in badge_body,
          "setActionBadge()'s Today-badge (hc) computation should fold in _alertsCritWarnCount")
    check("_alertsCritWarnCount = needs.filter(" in today_body,
          "renderPhoneToday() should recompute _alertsCritWarnCount from the full needs array "
          "(not the 20-item slice) on every render")
    check("x.source !== 'action'" in today_body,
          "_alertsCritWarnCount should only count alert-sourced items, not recommendation-sourced "
          "ones already reflected in _actionsSummary (avoids double-counting)")
    printer_interval_idx = src.index("if (_activeScreen === 'cmd') loadPrinterStatus();")
    after_printer_interval = src[printer_interval_idx:printer_interval_idx + 1600]
    check("renderPhoneApprovals()" in after_printer_interval and "renderPhoneToday()" in after_printer_interval,
          "expected a second 30s setInterval block (after the Approvals one) that re-fires "
          "renderPhoneToday() while the pp-today panel is active")
    check("getElementById('pp-today')" in after_printer_interval,
          "the Today refresh interval should gate on the pp-today panel's own 'on' class")

    # ── 6. Stale-data indicator, animation skipped on stale ──────────────
    check("if (m.stale) html += _offlineNote(" in today_body,
          "a stale /api/metrics payload should render the existing _offlineNote() indicator")
    check("starSeller.stale ? _offlineNote(" in today_body,
          "a stale /api/star-seller payload should render the existing _offlineNote() indicator")
    check("if (m.stale) el.querySelectorAll('.ptiles [data-countup]')" in today_body,
          "the count-up animation should be skipped (value shown directly) when metrics are stale")


def main() -> None:
    run()
    if _failures:
        print("TODAY UX AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("TODAY UX AUDIT TESTS OK — alert detail threading, the product_file_integrity tap/sheet "
          "fix, the info-severity dot, parallelized fetches, the 30s poll + badge shared-state fix, "
          "and the stale-data indicator are all present in frank_hud_mockup.py.")


if __name__ == "__main__":
    main()
