"""Full checks for the window glow coupon (2026-11-20). The panes are the feature under
test and are thinner than the gate's 1.2 mm wall floor on purpose, so they're declared."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
from model_checks import run_checks  # noqa: E402

CFG = dict(
    label="Window Glow Coupon",
    note="Test print for Explained Lesson 005: three windows at 0.8, 1.6 and 2.4 mm, lit from behind "
         "by one tea light. Not printed yet.",
    source="window_glow_coupon/window_coupon.scad",
    objects=[[("body", "#F4F1EA")]],
    unions=[HERE / "window_coupon.stl"],
    gate_args=["--wall-skip-part", str(HERE / "panes_region.stl")],
)

if __name__ == "__main__":
    run_checks(HERE, "window_coupon", CFG, sys.argv[1:] or None)
