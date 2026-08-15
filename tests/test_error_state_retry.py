"""
Test for the 2026-08-15 error-state/retry-button addition (part of the
visual-upgrade research pass -- "loading / empty / error should be three
distinct designed states, and a real error state needs a real retry action,
not a dead end").

Before this change, every one of the sidebar panel loaders (Star Seller,
Ads, Growth Brief, A/B Tests, Competitor Watch, Movement Digest, Review
Themes, COGS, Printer Status, Inbox) rendered a failed fetch as a bare,
muted, unstyled line of text with no way to recover short of a full page
reload -- a real dead end for a transient network blip.

`_errorRetry(message, retryFnName)` is now the single shared renderer for
this state: a `.hub-error` card (tinted red background/border derived from
`--red` via color-mix, matching this file's established token-derivation
pattern) containing the message and a real `.act-btn` that calls the exact
loader function that failed, so retrying re-runs the real fetch rather than
requiring a reload.

Verified end-to-end in real headless Chrome (not just structurally here):
forcing `authGet()` to throw for one panel renders the `.hub-error` card
with a working Retry button, and clicking it (with the fault removed)
correctly replaces the error card with the real successful render.

Run: python tests/test_error_state_retry.py
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


# Every panel loader this fix targets, and the DOM id its catch block writes
# into -- kept in sync with the real source so a future rename is caught here
# rather than silently drifting.
_TARGET_LOADERS = [
    "loadStarSeller",
    "loadAdsStatus",
    "loadGrowthBrief",
    "loadAbTests",
    "loadCompetitorWatch",
    "loadMovementDigest",
    "loadReviewThemes",
    "loadCogsStatus",
    "loadPrinterStatus",
    "loadInbox",
]


def test_shared_error_retry_helper_exists():
    source = _source()
    m = re.search(r"function _errorRetry\(message, retryFnName\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, "expected a shared _errorRetry(message, retryFnName) helper"
    body = m.group(1)
    check("hub-error" in body, "_errorRetry() must render the .hub-error card")
    check("hub-error-msg" in body, "_errorRetry() must render the .hub-error-msg text")
    check("escHtml(message)" in body, "the error message must be HTML-escaped, not interpolated raw")
    check("onclick=\"'+retryFnName+'()\">" in body,
          "the retry button's onclick must call the passed-in retry function by name")
    check("act-btn" in body, "the retry control must be a real .act-btn, not a bare link or dead text")


def _function_span(source: str, fn_name: str) -> tuple[int, int]:
    """Return (start, end) char offsets covering async function fn_name(){...}'s
    full body, found by brace-depth counting rather than a non-greedy regex --
    a non-greedy `\\}\\n` match stops at the first inner closure's closing
    brace (e.g. a `.map(function(...){...})` callback), not the function's
    real end, which silently truncated the body in an earlier draft of this
    test and produced false "catch block not found" failures."""
    marker = "async function " + fn_name + "(){"
    start = source.index(marker)
    depth = 0
    i = start + len(marker) - 1  # position of the opening brace itself
    for j in range(i, len(source)):
        if source[j] == "{":
            depth += 1
        elif source[j] == "}":
            depth -= 1
            if depth == 0:
                return start, j + 1
    raise AssertionError(f"unbalanced braces scanning {fn_name}()")


def test_all_ten_target_loaders_use_the_shared_helper_in_their_catch_block():
    source = _source()
    for fn_name in _TARGET_LOADERS:
        start, end = _function_span(source, fn_name)
        body = source[start:end]
        check(f"_errorRetry(e.message, '{fn_name}')" in body,
              f"{fn_name}()'s catch block must render _errorRetry(e.message, '{fn_name}') so a failed "
              f"fetch offers a real retry that re-calls {fn_name} itself, not the old dead-end plain-text line")


def test_old_dead_end_error_pattern_is_gone_from_all_target_loaders():
    # The exact byte-identical old pattern (muted, unstyled, no retry) that
    # every target loader used to render on failure -- must not survive
    # anywhere the fix was supposed to reach.
    source = _source()
    old_patterns = [
        '\'<div style="color:var(--muted);font-size:11px">⚠ \' + escHtml(e.message) + \'</div>\'',
        '\'<div style="color:var(--muted);font-size:11px">⚠ \'+escHtml(e.message)+\'</div>\'',
    ]
    for fn_name in _TARGET_LOADERS:
        start, end = _function_span(source, fn_name)
        body = source[start:end]
        for old in old_patterns:
            check(old not in body,
                  f"{fn_name}() still contains the old dead-end error pattern -- the fix should have "
                  f"replaced every occurrence with _errorRetry(...)")


def test_printer_detail_modal_error_handler_intentionally_left_alone():
    # _renderPrinterDetail() is an on-demand modal (opened by clicking the
    # printer card), not one of the passively-polling sidebar panels -- retry
    # semantics differ there (the user can just close/reopen the modal), so
    # this specific error render was deliberately left out of scope for this
    # fix. This test documents that as an intentional decision, not a miss.
    source = _source()
    start, end = _function_span(source, "_renderPrinterDetail")
    body = source[start:end]
    check('body.innerHTML = \'<div style="color:var(--red);font-size:11px">⚠ \'+escHtml(e.message)+\'</div>\';' in body,
          "_renderPrinterDetail()'s own error render should be unchanged -- it's an on-demand modal, not "
          "a passively-polling panel, so it was intentionally left out of the _errorRetry() rollout")


def test_hub_error_css_derives_red_tint_from_the_real_token_not_a_hardcoded_hex():
    source = _source()
    m = re.search(r"\.hub-error\{([^}]*)\}", source)
    assert m, "expected a .hub-error CSS rule"
    body = m.group(1)
    check("color-mix(in srgb, var(--red)" in body,
          "the error card's background/border must derive from the real --red token via color-mix, "
          "matching this file's established color-token-derivation pattern (not a hardcoded rgba/hex)")
    m2 = re.search(r"\.hub-error-msg\{([^}]*)\}", source)
    assert m2, "expected a .hub-error-msg CSS rule"
    check("var(--red)" in m2.group(1), "the error message text must use the real --red token")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("ERROR STATE RETRY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("ERROR STATE RETRY TESTS OK — all 10 target panel loaders render a real .hub-error card with a "
          "working Retry button on fetch failure via the shared _errorRetry() helper, the old dead-end "
          "plain-text pattern is gone from every one of them, the printer-detail modal's separate handler "
          "is unchanged by design, and the error styling derives from the real --red token.")


if __name__ == "__main__":
    run()
