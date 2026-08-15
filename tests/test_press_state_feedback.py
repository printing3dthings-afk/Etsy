"""
Test for the 2026-08-14 press-state (:active) feedback pass (fifth item from
the visual-research pass) on the primary tap targets that had none: .qc-btn
(Home quick actions), .pmore-item (More screen list rows), .psheet-btn
(mobile bottom-sheet buttons), .hub-toggle-btn / .hub-chip-btn (filter
toggles/chips), and .panel-title[role="button"] (the tappable Star Seller/
Ads/COGS/Printer panel titles that open their metric-detail modal).

Every target follows the same shape already established by .shop-spark-card/
.act-btn/.home-hero elsewhere in this file: a `transition:transform .12s
ease` on the base rule (or reuse an existing `transition:all` if the element
already had one) plus a `:active{transform:scale(...)}` rule, and a matching
`transform:none` override inside the existing prefers-reduced-motion block
so the press animation is silenced for users who've asked for it, same as
every other press-state affordance in this file.

Run: python tests/test_press_state_feedback.py
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


# selector -> expected scale value used in the :active rule
_TARGETS = {
    ".qc-btn": ".97",
    ".pmore-item": ".97",
    ".psheet-btn": ".97",
    ".hub-toggle-btn": ".97",
    ".hub-chip-btn": ".97",
    '.panel-title[role="button"]': ".98",
}


def test_every_target_has_an_active_scale_rule():
    source = _source()
    for selector, scale in _TARGETS.items():
        needle = selector + f":active{{transform:scale({scale})}}"
        check(needle in source, f"missing press-state rule: {needle!r}")


def test_every_target_has_a_transform_transition_somewhere():
    """Either a dedicated `transition:transform .12s ease` this pass added, or
    a pre-existing `transition:all ...` (like .hub-toggle-btn already had) --
    either way the scale must actually animate, not snap instantly."""
    source = _source()
    m = re.search(r"\.qc-btn\{([^}]*)\}", source)
    assert m, "could not find .qc-btn base rule"
    check("transition:transform .12s ease" in m.group(1), ".qc-btn needs a transform transition")

    m = re.search(r"\.hub-toggle-btn\{([^}]*)\}", source)
    assert m, "could not find .hub-toggle-btn base rule"
    check("transition:all .15s" in m.group(1),
          ".hub-toggle-btn already had transition:all before this pass -- should not be duplicated")

    m = re.search(r"\.hub-chip-btn\{([^}]*)\}", source)
    assert m, "could not find .hub-chip-btn base rule"
    check("transition:transform .12s ease" in m.group(1), ".hub-chip-btn needs a transform transition")

    m = re.search(r"\.pmore-item\{([^}]*)\}", source)
    assert m, "could not find .pmore-item base rule"
    check("transition:transform .12s ease" in m.group(1), ".pmore-item needs a transform transition")

    m = re.search(r"\.psheet-btn\{([^}]*?)\}", source, re.DOTALL)
    assert m, "could not find .psheet-btn base rule"
    check("transition:transform .12s ease" in re.sub(r"\s+", " ", m.group(1)),
          ".psheet-btn needs a transform transition")

    m = re.search(r'\.panel-title\[role="button"\]\{([^}]*)\}', source)
    assert m, 'could not find .panel-title[role="button"] base rule'
    check("transition:transform .12s ease" in m.group(1),
          # 2026-08-15: this rule's transition list grew a second property
          # (`,color .15s ease`) when a :hover rule was added for desktop
          # mouse users -- substring check so that legitimate addition
          # doesn't false-fail this exact-match assertion.
          '.panel-title[role="button"] needs its own transform transition rule')


def test_reduced_motion_block_silences_every_new_press_state():
    # There are several small, single-purpose @media (prefers-reduced-motion:reduce)
    # blocks scattered through this file -- anchor on the big general one specifically
    # (identified by its first rule, .status-pill .dot, which is unique to it) rather
    # than a bare first-match search that would silently grab the wrong block.
    source = _source()
    m = re.search(
        r"@media \(prefers-reduced-motion: reduce\)\{\n  \.status-pill \.dot\{animation:none\}(.*?)\n\}\n",
        source, re.DOTALL,
    )
    assert m, "could not find the general prefers-reduced-motion:reduce media block (anchored on .status-pill .dot)"
    block = re.sub(r"\s+", " ", m.group(1))
    check(".qc-btn:active,.pmore-item:active,.psheet-btn:active,.hub-toggle-btn:active, "
          '.hub-chip-btn:active,.panel-title[role="button"]:active{transform:none}' in block,
          "all 6 new press-state targets must be silenced together in the reduced-motion block, "
          "matching the existing convention (see .act-btn/.hub-act-btn's own line just above it)")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PRESS STATE FEEDBACK TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRESS STATE FEEDBACK TESTS OK — .qc-btn/.pmore-item/.psheet-btn/.hub-toggle-btn/"
          ".hub-chip-btn/.panel-title[role=\"button\"] all get a transform:scale press-state, "
          "each with a real transition and a matching reduced-motion override.")


if __name__ == "__main__":
    run()
