"""
Regression tests for the Approvals screen UX audit (2026-07-30, fourth screen
in the screen-by-screen audit after Login/Home/Ask-Chat). All six fixes are
pure frontend (frank_hud_mockup.py) -- no backend payload/endpoint changed --
so these are source-substring checks in the same style as
test_tour_copy_accuracy.py, not a running-server test.

Findings fixed (see ops_runbook.md 2026-07-30 entry for the full writeup):
  1. Mobile Approvals cards had no way to expand detail (no "why Frank
     suggested this" reasoning, no type-specific preview) -- desktop-only
     before this pass.
  2. approveAction()'s confirm() dialog fell through to a generic "apply
     this change to your live Etsy listing" message for create_listing/
     post_tiktok/post_pinterest, which is inaccurate for all three.
  3. renderPhoneApprovals() only fetched once on tab-open -- the badge kept
     updating in the background (loadQueue(), always-on) but the list itself
     could silently go stale while the tab stayed open.
  4. _actionPreviewBody() had zero rendering branch for 6 action types
     (create_listing, post_tiktok, post_pinterest, update_sku_and_category,
     listing_video, register_command) -- tapping to expand any of them
     showed a completely blank panel, worst for create_listing (the
     highest-consequence write in the app).
  5. Those same 6 types had no _ACT_TYPE_GLYPH entry -- generic ❓ fallback.
  6. Today's tab/home badge (ptab-today-badge / home-today-badge) only
     counted summary.high, never summary.medium -- but every System-health/
     data_error card is always medium severity, and renderPhoneToday()'s own
     "Needs attention" list already includes both. A fresh infra alert could
     sit with zero badge nudge until Scott happened to open Today.
  Plus a "Action Center" -> "Approvals" cleanup for ~8 leftover user-facing
  strings (toasts/confirm dialogs/links) found during the same pass.

Run: python tests/test_approvals_ux_audit.py
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

    # ── 1. Mobile detail-expand wiring ──────────────────────────────────
    # renderPhoneApprovals()'s pcard template must now wire toggleActionDetail
    # (the same function/id convention desktop's renderApproval() uses, so
    # _actionPreviewHtml/_actionPreviewBody are reused unmodified).
    rpa_start = src.index("async function renderPhoneApprovals()")
    rpa_end = src.index("async function phoneApprove(")
    rpa_body = src[rpa_start:rpa_end]
    check("toggleActionDetail(" in rpa_body,
          "renderPhoneApprovals() pcard template should call toggleActionDetail() to expand detail")
    check('id="act-detail-' in rpa_body,
          "renderPhoneApprovals() pcard should emit an act-detail-{id} container matching toggleActionDetail()'s lookup")
    check(".pcard-tap{" in src, "expected a .pcard-tap CSS rule for the new tappable detail-expand area")

    # ── 2. Confirm-dialog wording for create_listing/post_tiktok/post_pinterest ──
    confirm_start = src.index("const _APPROVE_CONFIRM_MSGS")
    confirm_end = src.index("};", confirm_start)
    confirm_block = src[confirm_start:confirm_end]
    for t, must_contain in [
        ("create_listing", "NEW listing"),
        ("post_tiktok", "TikTok"),
        ("post_pinterest", "Pinterest"),
    ]:
        check(f"{t}:" in confirm_block, f"_APPROVE_CONFIRM_MSGS should have an entry for {t}")
        # crude but sufficient: the value string for this key should mention the platform/nature of the action
        key_idx = confirm_block.index(f"{t}:")
        val_slice = confirm_block[key_idx:key_idx + 200]
        check(must_contain in val_slice, f"{t}'s confirm message should mention {must_contain!r}, got: {val_slice!r}")

    # ── 3. Mobile 30s auto-refresh while the appr tab is active ─────────
    printer_interval_idx = src.index("if (_activeScreen === 'cmd') loadPrinterStatus();")
    after_printer_interval = src[printer_interval_idx:printer_interval_idx + 900]
    check("renderPhoneApprovals()" in after_printer_interval,
          "expected a new setInterval block shortly after the printer-status interval that re-fires renderPhoneApprovals()")
    check("getElementById('pp-appr')" in after_printer_interval and "classList.contains('on')" in after_printer_interval,
          "the mobile Approvals refresh interval should gate on the pp-appr panel's own 'on' class, not a new parallel state variable")

    # ── 4. Preview branches for the 6 previously-blank action types ─────
    preview_start = src.index("function _actionPreviewBody(a)")
    preview_end = src.index("\nfunction renderApproval(a)")
    preview_body = src[preview_start:preview_end]
    for t in ("create_listing", "post_tiktok", "post_pinterest",
              "update_sku_and_category", "listing_video", "register_command"):
        check(f"a.type === '{t}'" in preview_body,
              f"_actionPreviewBody() should have a rendering branch for {t} (was previously blank)")

    # ── 5. Glyphs for the same 6 types ───────────────────────────────────
    glyph_start = src.index("const _ACT_TYPE_GLYPH")
    glyph_end = src.index("};", glyph_start)
    glyph_block = src[glyph_start:glyph_end]
    for t in ("create_listing", "post_tiktok", "post_pinterest",
              "update_sku_and_category", "listing_video", "register_command"):
        check(f"{t}:" in glyph_block, f"_ACT_TYPE_GLYPH should have an entry for {t}")

    # ── 6. Today badge counts medium severity too ────────────────────────
    badge_start = src.index("function setActionBadge(summary, pending)")
    badge_end = src.index("\nfunction simpleLineDiff(")
    badge_body = src[badge_start:badge_end]
    check("summary.medium" in badge_body,
          "setActionBadge() should count summary.medium (not just summary.high) toward the Today badge, "
          "since every data_error/System-health card is always medium severity")

    # ── Naming cleanup: no user-facing 'Action Center' strings survive ──
    # (internal code comments documenting the old name are fine and excluded here --
    # only check the specific spots that were confirmed user-facing during the audit.)
    user_facing_needles = [
        "gated by the same approval queue as Action Center",
        "nothing goes live until you approve it in the Action Center.",
        "Approve the new fixes in Action Center",
        "check the Action Center in a moment",
        "review in Action Center",
        "Queued for Action Center approval.",
        "Staged ${d.staged_count} item(s) in the Action Center",
        "approval in the Action Center -- it will be created as a DRAFT",
        "it queues in the Action Center for your one-tap approval",
    ]
    for needle in user_facing_needles:
        check(needle not in src, f"found a leftover user-facing 'Action Center' string that should say 'Approvals': {needle!r}")


def main() -> None:
    run()
    if _failures:
        print("APPROVALS UX AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("APPROVALS UX AUDIT TESTS OK — mobile detail-expand, confirm-dialog wording, mobile "
          "auto-refresh, the 6 blank-preview/missing-glyph action types, the Today medium-severity "
          "badge fix, and the Action Center->Approvals string cleanup are all present in "
          "frank_hud_mockup.py.")


if __name__ == "__main__":
    main()
