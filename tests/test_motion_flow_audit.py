"""
Tests for the Motion & Flow Audit implementation (2026-07-18) — the follow-up to
the "Frank Against the Field" competitive audit, this time reviewing Frank's own
tap-through feel and shipping the top 5 findings from that pass, in order:

  F1. Sliding pill indicator behind the active bottom tab (was color-only)
  F2. Entrance/exit motion on the product review modal (was a hard display cut)
  F3. In-flight loading state on approve/bulk-approve (was silent up to 50s)
  F4. A haptic tick on tab switches and a successful approve
  F5. A finished (not skipped) tour hands off to one real pending item

F6 from the report ("leave top-level tab crossfade alone") was a reassurance,
not a change — nothing to test there.

These are structural checks against the real HUD source, matching how every
other frontend-only feature in this codebase is tested (e.g.
test_bulk_approve_low_risk.py, test_action_reasoning_panel.py) since there's no
backend endpoint for most of this pass.

Run: python tests/test_motion_flow_audit.py
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


# ── F1: sliding pill indicator ──────────────────────────────────────────────

def test_pill_element_present_in_tabbar_markup():
    source = _source()
    check('<div class="ptab-pill" id="ptab-pill"' in source,
          "the pill element should be the first child of #phone-tabbar, in the DOM")
    check(source.index('id="ptab-pill"') < source.index('data-ptab="ask"'),
          "the pill div should precede the tab buttons in the markup")


def test_pill_css_is_theme_aware_and_positioned():
    source = _source()
    check("#phone-tabbar .ptab-pill{" in source, "the pill needs its own CSS rule")
    m = re.search(r"#phone-tabbar \.ptab-pill\{([^}]*)\}", source)
    assert m, "could not find the .ptab-pill CSS block"
    block = m.group(1)
    check("position:absolute" in block, "the pill must be positioned absolutely to slide via transform")
    check("color-mix(in srgb" in block,
          "the pill's background should reference a theme CSS var via color-mix() so every color preset recolors it, not a hardcoded rgba")
    check("transition:transform" in block, "the slide must animate transform (not left/top, for GPU-accelerated motion)")


def test_pill_hidden_under_reduced_motion():
    source = _source()
    check("body.is-mobile #phone-tabbar .ptab-pill{transition:none}" in source,
          "the pill's transition should be silenced under prefers-reduced-motion")


def test_pill_positioning_uses_mutation_observer_not_scattered_calls():
    source = _source()
    check("new MutationObserver(schedulePillMove)" in source,
          "the pill should stay in sync via one observer, not a call added at every .ptab.on toggle site "
          "(phoneTab/openFrankPopup/phoneOpenScreen all mutate .on independently)")
    check("getBoundingClientRect()" in source.split("schedulePillMove")[0][-2000:] or
          "tRect.left" in source, "movePill() should compute the target's real position, not a hardcoded offset")


# ── F2: modal entrance/exit ─────────────────────────────────────────────────
# Redone 2026-08-14 (motion audit round 2) with @starting-style + transition-
# behavior:allow-discrete instead of the JS-driven .product-review-closing
# class + setTimeout -- allow-discrete lets `display` itself participate in
# the transition (the UA holds it at the pre-transition value until the rest
# of the transition finishes, then flips it), so open AND close are one real
# CSS transition each, no JS timing at all. Verified in real headless Chrome
# before shipping: display stays 'flex' throughout the close fade and only
# becomes 'none' once opacity/transform settle -- see ops_runbook.md.

def test_modal_has_starting_style_entrance_and_discrete_display_transition():
    source = _source()
    check("transition:opacity .15s cubic-bezier(.22,1,.36,1),transform .15s cubic-bezier(.22,1,.36,1),display .15s allow-discrete"
          in source,
          "the modal needs display in its own transition with allow-discrete, so display:none<->flex "
          "can now be a real transition instead of requiring a `@keyframes` + JS-timed reverse-animation class")
    check("@starting-style{\n  body.product-review-open #product-review-backdrop{opacity:0}\n"
          "  body.product-review-open #product-review-modal{opacity:0;transform:translate(-50%,-50%) scale(.94) translateY(6px)}\n}"
          in source,
          "@starting-style must provide the entrance 'from' state for the transition (transitions can't "
          "otherwise interpolate from a display:none starting point)")


def test_modal_close_is_a_single_class_removal_no_js_timing():
    source = _source()
    m = re.search(r"function productReviewClose\(\)\{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find productReviewClose()"
    body = m.group(1)
    check("product-review-closing" not in body,
          "the .closing workaround class is obsolete now that CSS handles the exit transition natively")
    check("setTimeout(" not in body,
          "no JS timing should be needed -- transition-behavior:allow-discrete keeps display:flex until "
          "the CSS transition itself finishes, natively")
    check("document.body.classList.remove('product-review-open')" in body,
          "close should be nothing more than removing the open class; the exit motion is pure CSS")


def test_modal_transition_disabled_under_reduced_motion():
    source = _source()
    check("@media (prefers-reduced-motion:reduce){\n  #product-review-backdrop,#product-review-modal{transition:none}\n}"
          in source,
          "the modal's open/close transition should be silenced under prefers-reduced-motion "
          "(display then flips instantly alongside the class change, no motion)")


def test_metric_detail_modal_got_the_same_treatment():
    # Cloned from #product-review-modal (see its own CSS comment) -- must not have drifted
    # back to the old .closing/setTimeout pattern independently.
    source = _source()
    m = re.search(r"function metricDetailClose\(\)\{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find metricDetailClose()"
    body = m.group(1)
    check("metric-detail-closing" not in body, "metricDetailClose should not use the obsolete .closing class either")
    check("setTimeout(" not in body, "metricDetailClose should need no JS timing either")
    check("#metric-detail-backdrop{display:none;position:fixed;inset:0;z-index:900;background:rgba(0,0,0,.6);\n"
          "  opacity:0;transition:opacity .12s ease,display .12s allow-discrete}" in source,
          "metric-detail-backdrop needs the same allow-discrete transition as product-review-backdrop")
    check("display .15s allow-discrete}\nbody.metric-detail-open" in source,
          "metric-detail-modal needs the same allow-discrete transition as product-review-modal")


# ── F3: in-flight approve state ─────────────────────────────────────────────

def test_set_approve_loading_helper_exists_and_disables_sibling_buttons():
    source = _source()
    m = re.search(r"function _setApproveLoading\(btnEl, loading\)\{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find _setApproveLoading(btnEl, loading)"
    body = m.group(1)
    check(".act-btns, .pp-acts" in body, "should walk to the shared button row so Reject/Fix can't be tapped mid-approve")
    check("disabled = loading" in body, "should disable (not just restyle) the buttons while a real write is in flight")


def test_approve_action_wires_loading_state_and_is_not_optimistic():
    source = _source()
    m = re.search(r"async function approveAction\(id, btnEl\) \{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find async function approveAction(id, btnEl)"
    body = m.group(1)
    check("_setApproveLoading(btnEl, true)" in body, "loading state should be set before the await, not after")
    check("_setApproveLoading(btnEl, false)" in body, "loading state should be cleared on the error path (success path re-renders the list instead)")
    check(body.index("_setApproveLoading(btnEl, true)") < body.index("await fetchWithTimeout"),
          "the loading state must be applied before the network call starts, not after it resolves -- "
          "that's the whole point (this is explicitly NOT optimistic completion, just an honest in-flight state)")


def test_approve_call_sites_pass_the_clicked_element():
    source = _source()
    check('onclick="approveAction(${a.id}, this)"' in source, "desktop Approve button should pass itself for the loading state")
    check('onclick="phoneApprove(${a.id}, this)"' in source, "mobile Approve button should pass itself for the loading state")
    check("async function phoneApprove(id, btnEl){ await approveAction(id, btnEl)" in source,
          "phoneApprove should forward the button element through to approveAction")


def test_bulk_approve_also_shows_in_flight_state():
    source = _source()
    m = re.search(r"async function bulkApproveLowRisk\(btnEl\) \{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find async function bulkApproveLowRisk(btnEl)"
    body = m.group(1)
    check("btnEl.disabled = true" in body, "the bulk-approve button should disable itself while the batch runs")
    check('onclick="bulkApproveLowRisk(this)"' in source, "the rendered bulk button should pass itself through")


# ── F4: haptics ──────────────────────────────────────────────────────────────

def test_haptic_helper_is_safe_and_used_on_tab_switch_and_approve():
    source = _source()
    m = re.search(r"function _hapticTick\(ms\)\{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find function _hapticTick(ms)"
    body = m.group(1)
    check("navigator.vibrate" in body, "should use the Vibration API")
    check("try" in body, "must be wrapped defensively -- iOS Safari has no Vibration API at all")
    check("_hapticTick()" in source.split("function phoneTab(which)")[1][:300],
          "phoneTab() should tick on an actual tab switch")
    check("_hapticTick(15)" in source, "approveAction() should tick on a confirmed successful approve")


# ── F5: tour finish hands off to a real task ────────────────────────────────

def test_end_tour_distinguishes_completed_from_skipped():
    source = _source()
    check("async function endTour(markSeen, completed)" in source,
          "endTour needs a second param distinct from markSeen -- Skip also sets markSeen=true, "
          "so markSeen alone can't tell a finished tour from an abandoned one")
    check("function tourNext(){\n  if (_tourIndex >= _activeTourSteps.length - 1) { endTour(true, true); return; }" in source,
          "reaching the real last step via Next should pass completed=true")
    check("function tourSkip(){ endTour(true, false); }" in source,
          "Skip should NOT trigger the real-task handoff -- the user opted out of hand-holding")


def test_end_tour_fetches_real_pending_items_not_stale_state():
    source = _source()
    m = re.search(r"async function endTour\(markSeen, completed\)\{(.*?)\n\}", source, re.DOTALL)
    assert m, "could not find async function endTour(markSeen, completed)"
    body = m.group(1)
    check("/api/queue?status=pending" in body,
          "should fetch fresh rather than trust _pendingActions, which is only populated once the "
          "Approvals screen has actually loaded and may still be empty this early in a first run")
    check("if (!completed) return;" in body, "should no-op entirely (not even fetch) when the tour wasn't genuinely completed")
    check(("phoneTab('appr')" in body or 'phoneTab("appr")' in body) and "showScreen('actions')" in body,
          "should route to Approvals on both mobile and desktop")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("MOTION FLOW AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("MOTION FLOW AUDIT TESTS OK — sliding pill indicator, modal entrance/exit, "
          "in-flight approve state (non-optimistic), haptics, and the tour's real-task "
          "handoff are all wired correctly.")


if __name__ == "__main__":
    run()
