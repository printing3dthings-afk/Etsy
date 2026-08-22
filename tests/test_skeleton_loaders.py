"""
Test for the 2026-08-14 skeleton-loader wiring (second item from the visual-
research pass, after the View Transitions foundation) -- the 13 Command
Center panels that used to show a static, un-animated "Loading…" text node
while their fetch was in flight now show the existing content-shaped shimmer
placeholder (_skeletonCards(), already used by 4 other loaders in this file
-- see .skel-card/.skel-bar CSS from the 2026-07-18 motion audit) instead.

Every one of these 13 loaders follows the same shape: `const el =
document.getElementById('X'); [if(!el) return;] try{ ...await fetch...;
el.innerHTML = <real content> }catch(e){...}`. The fix is one line inserted
between the element lookup and the fetch: `el.innerHTML = _skeletonCards(n)`
(guarded with `if(el)`/`if(list)` for the 3 loaders that don't already have
an early-return guard, so the skeleton-set can't throw on a null element).

Verified end-to-end in real headless Chrome (not just structurally here):
calling each of the 13 loader functions synchronously (before its fetch
promise settles) leaves the target element's innerHTML containing a real
skel-card/skel-bar node, confirming the skeleton actually paints before the
network response arrives, not just that the string exists somewhere in the
source. That live-browser check isn't part of this repo's standard non-
browser test harness, so this file locks in the structural contract instead.

Run: python tests/test_skeleton_loaders.py
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


# function name -> (getElementById target, min lines to search within the function body)
_TARGETS = {
    "loadStarSeller": "star-seller-body",
    "loadAdsStatus": "ads-status-body",
    "loadGrowthBrief": "growth-brief-body",
    "loadAbTests": "ab-tests-body",
    "loadCompetitorWatch": "competitor-watch-body",
    "loadMovementDigest": "movement-digest-body",
    "loadReviewThemes": "review-themes-body",
    "loadCogsStatus": "cogs-status-body",
    "loadPrinterStatus": "printer-status-body",
    "loadInbox": "inbox-body",
    "loadDependencyHealth": "dep-pill-row",
    "loadQueue": "feed-list",
    "loadMissionTimeline": "timeline-list",
}


def _function_body(source: str, fn_name: str) -> str:
    m = re.search(r"async function " + re.escape(fn_name) + r"\(\)\{(.*?)\n\}\n", source, re.DOTALL)
    assert m, f"could not find async function {fn_name}()"
    return m.group(1)


def test_all_13_panels_have_a_dedicated_loader_and_matching_element_id():
    source = _source()
    check(len(_TARGETS) == 13, f"expected exactly 13 target panels, got {len(_TARGETS)}")
    for fn_name, element_id in _TARGETS.items():
        check(f"async function {fn_name}()" in source, f"missing loader function {fn_name}()")
        check(f"getElementById('{element_id}')" in source, f"{fn_name} should look up #{element_id}")


def test_every_loader_sets_a_skeleton_before_its_fetch():
    source = _source()
    for fn_name, element_id in _TARGETS.items():
        body = _function_body(source, fn_name)
        check("_skeletonCards(" in body,
              f"{fn_name} does not call _skeletonCards() -- the panel will still show static text "
              f"while /api/... is in flight instead of the shimmer placeholder")
        skel_idx = body.find("_skeletonCards(")
        fetch_idx = min((i for i in (body.find("authGet("), body.find("fetchWithTimeout(")) if i != -1), default=-1)
        check(fetch_idx == -1 or skel_idx < fetch_idx,
              f"{fn_name} must set the skeleton BEFORE the fetch starts, not after -- "
              f"otherwise the loading window shows nothing/static text instead of the shimmer")


def test_skeleton_set_is_null_guarded_for_loaders_without_an_early_return():
    """loadDependencyHealth/loadQueue/loadMissionTimeline never had an early
    `if(!el) return;` guard (they still proceed to fetch even off-screen, same
    as loadStarSeller's own documented reason) -- their skeleton-set line must
    be defensively guarded (`if(el)`/`if(list)`) so it can't throw on a null
    element the way an unguarded `el.innerHTML = ...` would."""
    source = _source()
    for fn_name, needle in (
        ("loadDependencyHealth", "if (el) el.innerHTML = _skeletonCards("),
        ("loadQueue", "if (list) list.innerHTML = _skeletonCards("),
        ("loadMissionTimeline", "if (list) list.innerHTML = _skeletonCards("),
    ):
        body = _function_body(source, fn_name)
        check(needle in body, f"{fn_name}'s skeleton-set line should be null-guarded: expected {needle!r}")


def test_loadstarseller_skeleton_guard_matches_its_own_no_early_return_shape():
    """loadStarSeller deliberately has NO early `if(!el) return;` (2026-07-23
    fix -- it must keep fetching even when #star-seller-body isn't on screen,
    to keep the Home ticker's rating tile fresh) -- its skeleton-set must be
    guarded the same way, not assume el is non-null like the other 10."""
    source = _source()
    body = _function_body(source, "loadStarSeller")
    check("if (el) el.innerHTML = _skeletonCards(" in body,
          "loadStarSeller's skeleton-set must be null-guarded since this function has no early-return guard")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("SKELETON LOADER TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("SKELETON LOADER TESTS OK — all 13 Command Center panels set a content-shaped "
          "_skeletonCards() shimmer before their fetch starts, correctly null-guarded for the "
          "4 loaders that have no early-return element check.")


if __name__ == "__main__":
    run()
