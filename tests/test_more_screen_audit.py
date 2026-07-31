"""
Regression tests for the More screen UX audit (2026-07-31, seventh screen in the
screen-by-screen audit after Login/Home/Ask-Chat/Approvals/Today/Create). More
(_PHONE_MORE/renderPhoneMore()) is the mobile launcher menu -- pure frontend
source-substring checks, same style as test_approvals_ux_audit.py/
test_today_ux_audit.py, since there's no backend surface here (desktop has no
equivalent concept -- its sidebar lists these screens as flat nav items).

Findings fixed (see ops_runbook.md 2026-07-31 entry for the full writeup):
  1. 'settings' and 'files' sat under the mobile-only "Advanced" group,
     alongside genuinely engineering-tier screens -- a 2026-07-17 fix moved
     Settings out of that grouping on desktop specifically because it's
     "everyday, non-technical" (files was already in Shop on desktop from
     day one), but a docs claim that the fix covered mobile too was never
     actually true. Both now live in "Shop" on mobile, matching desktop.
  2. Two label mismatches: "Tools" -> "Tools & Skills", "Brand kit" ->
     "Brand Kit", matching the desktop nav-item and each destination
     screen's own title exactly.
  3. The list's icon/chevron spans had no aria-hidden, unlike every
     comparable icon elsewhere in the app (sidebar nav-items, tab bar
     buttons) since the 2026-07-08 accessibility pass -- _PHONE_MORE
     predates that pass and was missed.
  4. Two dead-code cleanups (archived via tools/trash.py, not deleted
     outright): a badge-conversations DOM lookup with no matching element
     anywhere, and a vestigial .more-row CSS selector that never matched
     any real element (the actual markup is .pmore-item/.pmore-grp).
  No live badges were added to the launcher -- Scott confirmed a badge-free
  list is fine, so this is deliberately NOT a finding to fix.

Run: python tests/test_more_screen_audit.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def run() -> None:
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text(encoding="utf-8")

    more_start = src.index("const _PHONE_MORE = [")
    more_end = src.index("\nfunction renderPhoneMore()")
    more_block = src[more_start:more_end]

    # ── 1. settings + files moved to Shop group ──────────────────────────
    shop_line = next(l for l in more_block.split("\n") if "['Shop'" in l)
    check("'settings'" in shop_line, "settings should now be in the Shop group")
    check("'files'" in shop_line, "files should now be in the Shop group")
    advanced_line = next(l for l in more_block.split("\n") if "'Advanced'" in l)
    check("'settings'" not in advanced_line, "settings should no longer be in the Advanced group")
    check("'files'" not in advanced_line, "files should no longer be in the Advanced group")

    # ── 2. Label fixes ────────────────────────────────────────────────────
    check("'tools','🛠','Tools & Skills'" in more_block,
          "the Tools entry should say 'Tools & Skills', matching the desktop nav-item and screen title")
    check("'Tools']]" not in more_block and ",'Tools']" not in more_block,
          "the old bare 'Tools' label should be gone")
    check("'brandkit','🎨','Brand Kit'" in more_block,
          "the Brand Kit entry should be capitalized, matching the desktop nav-item and screen title")
    check("'Brand kit'" not in more_block, "the old lowercase 'Brand kit' label should be gone")

    # ── 3. Every item still present (no accidental drop/duplicate) ───────
    expected_screens = [
        "listings", "products", "brandkit", "connections", "settings", "files",
        "knowledge", "conversations",
        "tasks", "calendar", "workflows", "tools", "core", "agents", "security",
    ]
    for s in expected_screens:
        check(f"['{s}'," in more_block, f"expected _PHONE_MORE to still contain an entry for '{s}'")
    check(more_block.count("['Shop'") == 1 and more_block.count("['Knowledge'") == 1 and more_block.count("['Advanced'") == 1,
          "expected exactly one Shop, one Knowledge, and one Advanced group")

    # ── 4. aria-hidden on decorative spans ────────────────────────────────
    render_start = src.index("function renderPhoneMore()")
    render_end = src.index("\n// Opening a screen from More")
    render_body = src[render_start:render_end]
    check('<span class="pmi" aria-hidden="true">' in render_body,
          "the .pmi icon span should carry aria-hidden, matching sidebar/tab-bar icons elsewhere")
    check('<span class="pmc" aria-hidden="true">' in render_body,
          "the .pmc chevron span should carry aria-hidden, matching sidebar/tab-bar icons elsewhere")

    # ── 5. Dead code removed ──────────────────────────────────────────────
    check("badge-conversations" not in src,
          "the dead badge-conversations DOM lookup should be removed (archived via trash.py)")
    check(".more-row" not in src,
          "the vestigial .more-row CSS selector should be removed (archived via trash.py); "
          "the real .nav-item[data-tier=\"advanced\"] rule must remain untouched")
    check('body:not(.show-advanced) .nav-item[data-tier="advanced"]{display:none}' in src,
          "the real (non-vestigial) nav-item advanced-tier CSS rule must still be present")

    # ── 6. The onboarding tour's own "More" step copy must match the new grouping ──
    # (found while implementing -- the tour body text explicitly narrated the OLD
    # grouping, listing Settings alongside Tasks/Calendar under "Advanced".)
    tour_more_start = src.index("target: '#pp-more-body', ptab: 'more'")
    tour_more_body = src[tour_more_start:tour_more_start + 600]
    check("Settings, and Files" in tour_more_body or ("Settings" in tour_more_body and "Shop" in tour_more_body.split("Advanced")[0]),
          f"the tour's More step should describe Settings/Files as part of Shop now, not Advanced: {tour_more_body[:400]!r}")
    check("Settings, Tasks, Calendar" not in tour_more_body,
          "the tour's More step should no longer group Settings with Tasks/Calendar under Advanced")


def main() -> None:
    run()
    if _failures:
        print("MORE SCREEN AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("MORE SCREEN AUDIT TESTS OK — settings/files moved to Shop, label mismatches fixed, "
          "aria-hidden added to decorative spans, dead code archived and removed, and every "
          "launcher item is still present with no group dropped or duplicated.")


if __name__ == "__main__":
    main()
