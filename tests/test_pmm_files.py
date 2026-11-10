"""The shop's MakerWorld customizers stay PMM-safe (2026-11-06).

Both failed in production on 2026-11-05: the Name Ornament drew no name
(Dancing Script isn't on PMM) and its cloud slice failed, and the Love Letter
timed out. On 2026-11-10 Scott's preview showed the ornament off the plate's
corner: it had been moved to (128, 128) on a wrong reading that a 3MF's origin
is the plate's corner. PMM's preview centres the plate on (0, 0). These checks need no OpenSCAD, so they
run anywhere; tools/pmm_check.py does the render, time and slice checks.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import pmm_build as pb  # noqa: E402

FILES = [ROOT / "openscad_models/christmas_ornaments/name_ornament/pmm/name_ornament_pmm.scad",
         ROOT / "openscad_models/valentine_2027/mailboxes/love_letter/customizer/love_letter_pmm.scad"]

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_fonts_are_on_pmm():
    for f in FILES:
        bad = pb.check_fonts(f.read_text())
        check(not bad, f"{f.name}: fonts PMM doesn't have, which draw nothing there: {bad}")


def test_the_failed_fonts_are_really_missing():
    # so the font list is the real one and the check above means something
    have = pb.pmm_fonts()
    for f in ("Dancing Script:style=Bold", "Fredoka:style=SemiBold"):
        check(f not in have, f"{f} should not be on PMM's list")


def test_one_self_contained_file():
    for f in FILES:
        bad = pb.check_no_imports(f.read_text())
        check(not bad, f"{f.name}: includes or imports PMM can't resolve: {bad}")


def test_parameters_come_first_and_colours_are_hex():
    for f in FILES:
        s = f.read_text()
        first_module = re.search(r"^\s*(module|function)\s", s, re.M).start()
        check(re.search(r'^NAME = "', s[:first_module], re.M) is not None,
              f"{f.name}: NAME must be set before the first module, or the Customizer won't show it")
        colours = re.findall(r'^\w+ = "([^"]*)"; // color', s[:first_module], re.M)
        check(len(colours) >= 2 and all(re.fullmatch(r"#[0-9A-Fa-f]{6}", c) for c in colours),
              f"{f.name}: colour parameters must be hex strings with // color: {colours}")


def test_centred_on_the_plate():
    for f in FILES:
        s = f.read_text()
        check(re.search(r"PLATE_CENTRE = \[0, 0\];\ntranslate\(\[PLATE_CENTRE\[0\], PLATE_CENTRE\[1\], 0\]\)", s)
              is not None, f"{f.name}: the export must be centred on (0, 0), where PMM's preview centres the plate "
                           "(at (128, 128) it showed off the plate's corner)")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PMM FILE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PMM FILE TESTS OK: both customizers use only PMM's fonts, import nothing, "
          "show their parameters and sit on the plate.")


if __name__ == "__main__":
    run()
