"""
Regression test for the 2026-08-06 scheduled-coloring crash reported via the
hourly health loop's ops_runbook.md entries:

    TypeError: list indices must be integers or slices, not str

Root cause: tools/post_scheduled_coloring.py's run_scheduled_coloring() called
gcp.PACKS[pack]["themes"] / gcp.PACKS[pack]["style"] and gcp.generate_pack(...).
Neither matches generate_coloring_pages.py's real API -- PACKS[pack] IS the
theme list directly (no "themes"/"style" sub-dict), and generate_pack() does
not exist as a function at all. This crashed every single scheduled run since
the script was written; nothing caught it because the crash happened before
any file was written, so there was no partial-success state to notice either.

Fix: generate each theme individually via generate_coloring_page(), the same
loop generate_coloring_pages.py's own main() uses.

Run: python tests/test_scheduled_coloring_pack_generation.py
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools",):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import post_scheduled_coloring as psc  # noqa: E402
import generate_coloring_pages as gcp  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_packs_pack_is_a_plain_list_not_a_themes_style_dict():
    # Documents the real shape run_scheduled_coloring() must work against --
    # this is exactly what the old code got wrong.
    for pack_name, pack_value in gcp.PACKS.items():
        check(isinstance(pack_value, list), f"PACKS[{pack_name!r}] should be a plain list, got {type(pack_value)}")
        if pack_value:
            check(isinstance(pack_value[0], dict) and "id" in pack_value[0] and "prompt" in pack_value[0],
                  f"PACKS[{pack_name!r}][0] should be a theme dict with id/prompt, got {pack_value[0]!r}")


def test_generate_pack_function_does_not_exist():
    # If this ever starts passing, generate_coloring_pages.py grew a
    # generate_pack() function and the old call site's mistaken assumption
    # accidentally became valid -- worth knowing either way.
    check(not hasattr(gcp, "generate_pack"),
          "generate_coloring_pages.py now has a generate_pack() function -- "
          "re-check whether run_scheduled_coloring() should call it directly instead")


def test_run_scheduled_coloring_generates_one_page_per_theme_without_crashing():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_state = Path(tmp) / "coloring_schedule.json"

        def _fake_generate(theme, output_dir, *a, **kw):
            p = Path(tmp) / f"{theme['id']}.png"
            p.write_bytes(b"fake png")
            return p

        with patch.object(psc, "STATE_FILE", tmp_state), \
             patch.object(gcp, "generate_coloring_page", side_effect=_fake_generate) as mock_gen, \
             patch.object(gcp, "build_sets", return_value=[Path(tmp) / "set1.zip"]) as mock_build, \
             patch.object(gcp, "generate_listing_json", return_value=Path(tmp) / "listing.json") as mock_listing:
            result = psc.run_scheduled_coloring(force=True, preview=False)

        check(result.get("status") == "success", f"expected success, got {result}")
        pack = result.get("pack")
        expected_theme_count = len(gcp.PACKS[pack])
        check(mock_gen.call_count == expected_theme_count,
              f"expected generate_coloring_page called once per theme ({expected_theme_count}), "
              f"got {mock_gen.call_count} calls")
        # Every call's first positional arg must be a real theme dict from PACKS[pack],
        # not the old (broken) themes["themes"]/style_dna call shape.
        for call in mock_gen.call_args_list:
            theme_arg = call.args[0] if call.args else call.kwargs.get("theme")
            check(isinstance(theme_arg, dict) and "id" in theme_arg,
                  f"generate_coloring_page should be called with a real theme dict, got {theme_arg!r}")
        check(mock_build.called, "build_sets() should be called after generation")
        check(mock_listing.called, "generate_listing_json() should be called after build_sets()")
        check(result.get("pages") == expected_theme_count,
              f"expected {expected_theme_count} pages reported, got {result.get('pages')}")


def test_run_scheduled_coloring_reports_failure_when_zero_pages_generated():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_state = Path(tmp) / "coloring_schedule.json"
        with patch.object(psc, "STATE_FILE", tmp_state), \
             patch.object(gcp, "generate_coloring_page", return_value=None):
            result = psc.run_scheduled_coloring(force=True, preview=False)
        check(result.get("status") == "failed", f"expected failed status when every generation returns None, got {result}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("SCHEDULED COLORING PACK GENERATION TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("SCHEDULED COLORING PACK GENERATION TESTS OK — run_scheduled_coloring() now generates "
          "one page per real PACKS[pack] theme dict via generate_coloring_page(), matching "
          "generate_coloring_pages.py's actual API instead of the nonexistent generate_pack() call "
          "that crashed every scheduled run.")


if __name__ == "__main__":
    run()
