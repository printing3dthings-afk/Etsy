"""
Test for the 2026-08-15 "Flow" motion pass, items 2-3: toast entrance and
the shared .ss-row data-arrival entrance (~13 panels, one CSS rule covers
all of them).

Both were previously zero-motion or flat: .toast used a bare `.12s
ease-out` slide with no spring character at all, and `.ss-row` (every
panel that replaces a skeleton with real rows -- Star Seller, Growth
Brief, Competitor Watch, etc.) had no entrance animation whatsoever, rows
just appeared instantly via innerHTML.

Both are DELIBERATELY calibrated by frequency, not just stamped with the
full "Flow" spring used elsewhere in this pass (e.g. the desktop nav
pill): toasts fire often but not constantly, so they get the real Flow
curve at a short duration (.22s); .ss-row panels auto-refresh every 30s
(setInterval(loadAll, 30000)) so something that repetitive stays plain
ease-out and short (.18s) rather than a dramatic reveal that would wear
out fast on repeat -- this file's own "delight scales inversely with
frequency" doctrine (see .toast-check's comment), matching
motion-principles' frequency rule.

Verified end-to-end in real headless Chrome (not just structurally here):
a real showToast() call renders with animationName 'toast-in', duration
0.22s, and the exact Flow cubic-bezier; real .ss-row elements in the Star
Seller panel show staggered animation-delay values and animationName
'row-in'; forcing `reduced_motion="reduce"` reports animationName 'none'
for both.

Run: python tests/test_flow_toast_and_row_entrance.py
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


def test_toast_entrance_uses_the_flow_curve_at_a_calibrated_short_duration():
    source = _source()
    m = re.search(r"\.toast\{([^}]*)\}", source)
    assert m, "could not find the .toast base rule"
    block = m.group(1)
    check("animation:toast-in .22s cubic-bezier(.34,1.56,.64,1)" in block,
          "the toast entrance must use the real Flow curve, not the old flat .12s ease-out")


def test_toast_animation_has_a_reduced_motion_guard():
    # Regression found during this pass: .toast's own animation had NO
    # prefers-reduced-motion guard at all before this fix (only .toast-check
    # and .toast:active were covered) -- a real pre-existing accessibility gap.
    source = _source()
    m = re.search(
        r"@media \(prefers-reduced-motion: reduce\)\{\n  \.status-pill \.dot\{animation:none\}(.*?)\n\}\n",
        source, re.S,
    )
    assert m, "could not find the general prefers-reduced-motion block"
    block = m.group(1)
    check(".toast,.toast.out{animation:none}" in block,
          "both the entrance and exit toast animations must be silenced under reduced motion")


def test_ss_row_has_a_staggered_short_entrance_not_the_full_spring():
    source = _source()
    m = re.search(r"\.ss-row\{([^}]*)\}", source)
    assert m, "could not find the .ss-row base rule"
    block = m.group(1)
    check("animation:row-in .18s ease-out both" in block,
          "the data-arrival entrance must be short and plain ease-out (not the bouncy Flow "
          "spring) -- this fires every 30s on an auto-refreshing panel, a dramatic reveal "
          "would wear out fast on repeat")
    check("cubic-bezier(.34,1.56,.64,1)" not in block,
          ".ss-row must NOT use the full spring curve -- unlike a one-shot moment (nav switch, "
          "modal open), this genuinely repeats every 30 seconds")

    check("@keyframes row-in{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}" in source,
          "expected the row-in keyframes to animate opacity+transform only (GPU-composited, "
          "never layout-triggering properties)")

    # At least a few nth-child stagger rules should exist, capped rather than unbounded.
    stagger_rules = re.findall(r"\.ss-row:nth-child\((\d+)\)\{animation-delay:(\d+)ms\}", source)
    check(len(stagger_rules) >= 5, f"expected a real staggered cascade across several rows, found: {stagger_rules}")
    delays = [int(d) for _, d in stagger_rules]
    check(delays == sorted(delays), "stagger delays must increase monotonically by position")
    check(max(delays) <= 200, "the stagger cap should stay short -- a long list must not push the "
          "total settle time past what's reasonable for something this frequent")


def test_ss_row_animation_has_a_reduced_motion_guard():
    source = _source()
    check("@media (prefers-reduced-motion:reduce){.ss-row{animation:none}}" in source,
          "the .ss-row entrance animation must be silenced under reduced motion")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FLOW TOAST AND ROW ENTRANCE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FLOW TOAST AND ROW ENTRANCE TESTS OK — toast entrance now uses the real Flow spring "
          "curve at a calibrated short duration with a reduced-motion guard that was previously "
          "missing entirely, and the shared .ss-row data-arrival entrance (covering ~13 panels) "
          "uses a short staggered plain ease-out appropriate for something that repeats every "
          "30 seconds, also reduced-motion-safe.")


if __name__ == "__main__":
    run()
