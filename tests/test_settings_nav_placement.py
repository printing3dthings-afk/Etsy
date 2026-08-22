"""
Regression test for Frank upgrade Wave 3 (usability), item 2, 2026-07-17.

Settings holds only everyday, non-technical preferences (Voice/Appearance/
Branding) but used to be miscategorized under the "Advanced ▸" nav
disclosure -- the section meant for genuinely engineering-level screens
(Tasks, Workflows, Security, AI Core, Agents). It was already one click away
via the header gear icon (onclick="showScreen('settings')"), but the sidebar
browse path buried it. Moved the Settings nav-item into the "Shop" section
(alongside Products/Brand Kit/Files/Connections) and dropped its
data-tier="advanced" attribute so it's no longer CSS-hidden behind the
Advanced disclosure toggle (body:not(.show-advanced) .nav-item[data-tier=
"advanced"]{display:none}). Also updated the onboarding tour: added a
dedicated Settings step in its new position and removed the stale mention of
Settings from the "Advanced" step's description.

This test guards against Settings silently drifting back under Advanced.

Run: python tests/test_settings_nav_placement.py
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
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text()

    # ── sidebar nav-item itself ─────────────────────────────────────────────
    m = re.search(r'<div class="nav-item"[^>]*data-screen="settings"[^>]*>', src)
    check(m is not None, "expected a Settings nav-item with no data-tier attribute")
    if m:
        check('data-tier="advanced"' not in m.group(0),
              f"the Settings nav-item must not carry data-tier=\"advanced\" anymore, got: {m.group(0)!r}")

    # There must be no OTHER settings nav-item left behind under data-tier="advanced"
    # (e.g. a stray duplicate from an incomplete move).
    advanced_settings = re.search(r'data-tier="advanced"[^>]*data-screen="settings"', src) or \
        re.search(r'data-screen="settings"[^>]*data-tier="advanced"', src)
    check(advanced_settings is None, "found a leftover advanced-tier Settings nav-item")

    # ── it must sit in the Shop section, before the Advanced toggle ────────
    shop_idx = src.index('<h2 class="nav-section nav-section-h2">Shop</h2>')
    advanced_toggle_idx = src.index('id="nav-advanced-toggle"')
    settings_item_idx = src.index('data-screen="settings"')
    check(shop_idx < settings_item_idx < advanced_toggle_idx,
          "the Settings nav-item must appear in the Shop section, before the Advanced toggle")

    # ── the Advanced items block must no longer contain Settings ───────────
    items_start = src.index('id="nav-advanced-items"')
    items_end = src.index('</div>', items_start)
    # nav-advanced-items itself is a container div; find its matching close by
    # scanning to the closing tag right before the voice-widget block instead,
    # since nested divs make a naive first "</div>" unreliable -- use the known
    # next sibling anchor instead.
    voice_widget_idx = src.index('class="voice-widget"')
    advanced_block = src[items_start:voice_widget_idx]
    check('data-screen="settings"' not in advanced_block,
          "Settings must no longer appear inside the Advanced items block")

    # ── tour copy ────────────────────────────────────────────────────────────
    check("const TOUR_STEPS = [" in src, "TOUR_STEPS array must exist")
    tour_start = src.index("const TOUR_STEPS = [")
    tour_end = src.index("];", tour_start)
    tour_block = src[tour_start:tour_end]

    check("data-screen=\"settings\"" in tour_block, "TOUR_STEPS should have a dedicated Settings step target")
    check("title: 'Settings'" in tour_block, "TOUR_STEPS should have a Settings step")

    advanced_step_idx = tour_block.index("title: 'Advanced'")
    advanced_step_body = tour_block[advanced_step_idx:advanced_step_idx + 300]
    check("Settings" not in advanced_step_body,
          f"the Advanced tour step must no longer mention Settings, got: {advanced_step_body[:200]!r}")

    if _failures:
        print("SETTINGS NAV PLACEMENT TEST FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("SETTINGS NAV PLACEMENT TEST OK — Settings lives in the Shop section (not "
          "Advanced), carries no data-tier=\"advanced\" hiding attribute, has its own "
          "tour step, and the Advanced tour step no longer references it.")


if __name__ == "__main__":
    run()
