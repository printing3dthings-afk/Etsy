"""tools/fragility.py on the failure Scott actually had (2026-09-27).

The first haunted chapel printed with its window bars standing free across the
openings, 1.2 mm thick, and they snapped. Checked against that chapel from git
history, the tool flags all nine bars and nothing else of note; against the
glazed chapel, where each bar stands on a pane, it flags none of them. This test
builds the same two situations small: a window with a free bar, and the same
window with the bar on a pane.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import fragility as fr  # noqa: E402

_failures: list[str] = []

WINDOW = """
pane = %s;
difference() { cube([30, 1.6, 30]); translate([10, -1, 6]) cube([10, 4, 18]); }
translate([14.4, 0.2, 5.9]) cube([1.2, 1.2, 18.2]);          // the bar
if (pane) translate([10, 1.1, 6]) cube([10, 0.5, 18]);       // the pane behind it
"""


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _window(pane):
    td = Path(tempfile.mkdtemp(prefix="frag_test_"))
    (td / "w.scad").write_text(WINDOW % ("true" if pane else "false"))
    subprocess.run(["openscad", "-o", str(td / "w.stl"), str(td / "w.scad")],
                   check=True, capture_output=True)
    return fr.check([td / "w.stl"], log=lambda *a: None)


def test_a_free_bar_is_flagged_and_a_bar_on_a_pane_is_not():
    if not shutil.which("openscad"):
        print("  (skipped: openscad missing)")
        return
    free = [f for f in _window(False) if f["flag"]]
    check(len(free) == 1, f"one free bar should be flagged, got {len(free)}: {free}")
    if free:
        check(abs(free[0]["at"][0] - 15.0) < 0.5, f"the flag should be on the bar at x=15, got {free[0]['at']}")
        check(free[0]["length_mm"] >= 16, f"the bar is 18 mm long, measured {free[0]['length_mm']}")
    glazed = [f for f in _window(True) if f["flag"]]
    check(not glazed, f"a bar standing on a pane is not free; flagged {glazed}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FRAGILITY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FRAGILITY TESTS OK — a bar standing free across a window is flagged, "
          "and the same bar on a pane is not.")


if __name__ == "__main__":
    run()
