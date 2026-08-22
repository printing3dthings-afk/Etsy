"""
Test for the 2026-08-14 flash-on-change addition (seventh and final item
from the visual-research pass): a brief scale+brightness pulse when a live
value genuinely changes, applied to shop-perf stat cells (setEl() inside
_renderShopPerf) and every notification badge setActionBadge() updates
(badge-actions, ptab-badge, ptab-today-badge, home-appr-badge,
home-today-badge -- all 5 mirror the same two counts to different mount
points, so this is scoped to all 5, not just the 2 the task named as
examples, matching the existing convention that all 5 already shared
identical logic before this pass).

_flashOnChange(el, newText) is the shared primitive: compares the element's
current textContent against the new value, sets it, and only adds the
.flash-update CSS class (forcing a reflow first so a rapid second change
retriggers the animation instead of no-opping) when the value actually
changed -- a routine 30s poll re-render returning the same number stays
silent instead of flashing every tick.

setActionBadge()'s 5 near-identical `if (n>0){...}else{...}` blocks were
extracted into a shared _setBadge(el, n, displayVal) helper that calls
_flashOnChange() internally, so all 5 badges get the same behavior from one
place rather than 5 copies that could drift.

Verified end-to-end in real headless Chrome (not just structurally here):
calling setActionBadge() with a new pending count adds .flash-update to
badge-actions; calling it again with the SAME count does not re-add the
class (no spurious flash); calling it a third time with a different count
flashes again. Same behavior confirmed directly on _flashOnChange() with a
plain element. No page-level JS errors.

Run: python tests/test_flash_on_change.py
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


def test_flash_on_change_only_flashes_on_a_real_change():
    source = _source()
    m = re.search(r"function _flashOnChange\(el, newText\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "could not find function _flashOnChange(el, newText)"
    body = m.group(1)
    check("if (!el) return;" in body, "_flashOnChange must be null-safe")
    check("const changed = el.textContent !== String(newText);" in body,
          "must compare against the CURRENT value before overwriting it, or every call would look changed")
    check("el.textContent = newText;" in body, "must still set the text unconditionally (changed or not)")
    check("if (changed) {" in body, "the flash class should only be added when the value actually changed")
    check("void el.offsetWidth;" in body,
          "must force a reflow between remove/add so a rapid second change retriggers the CSS animation "
          "instead of being a no-op (re-adding a class that's already present doesn't restart a CSS animation)")


def test_setel_in_shop_perf_uses_flash_on_change():
    source = _source()
    check("const setEl = (id, val) => _flashOnChange(document.getElementById(id), val);" in source,
          "_renderShopPerf's setEl() should delegate to _flashOnChange(), not set textContent directly")


def test_all_5_badge_mount_points_go_through_the_shared_set_badge_helper():
    source = _source()
    m = re.search(r"function _setBadge\(el, n, displayVal\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "could not find function _setBadge(el, n, displayVal)"
    body = m.group(1)
    check("_flashOnChange(el, n > 99 ? '99+' : n)" in body,
          "_setBadge must flash via _flashOnChange(), not set textContent directly")

    m2 = re.search(r"function setActionBadge\(summary, pending\) \{(.*?)\n\}\n", source, re.DOTALL)
    assert m2, "could not find function setActionBadge(summary, pending)"
    fn_body = m2.group(1)
    for target, display_val in (
        ("b, n, ''", None),
        ("pb, pc, 'flex'", None),
        ("tb, hc, 'flex'", None),
        ("hab, pc, 'flex'", None),
        ("htb, hc, 'flex'", None),
    ):
        check(f"_setBadge({target})" in fn_body, f"setActionBadge should call _setBadge({target})")


def test_flash_update_css_class_exists_with_reduced_motion_override():
    source = _source()
    check("@keyframes flash-update{0%{transform:scale(1.15);filter:brightness(1.3)}"
          "100%{transform:scale(1);filter:brightness(1)}}" in source,
          "missing the flash-update keyframe animation")
    check(".flash-update{animation:flash-update .4s cubic-bezier(.22,1,.36,1)}" in source,
          "missing the .flash-update class wiring the keyframe")
    check("@media (prefers-reduced-motion:reduce){.flash-update{animation:none}}" in source,
          "flash-update must be silenced under prefers-reduced-motion, matching every other motion "
          "affordance in this file")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FLASH ON CHANGE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FLASH ON CHANGE TESTS OK — _flashOnChange() only flashes on a real value change, setEl() and "
          "all 5 badge mount points (via the shared _setBadge() helper) use it, and the CSS animation "
          "has a reduced-motion override.")


if __name__ == "__main__":
    run()
