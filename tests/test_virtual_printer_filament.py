"""tools/virtual_printer.py reports the filament the slicer will actually use.

2026-09-30: the Victorian shop-house's slice reported 117.1 g where the
slicer's own total was 58.91 cm3 (73 g). PrusaSlicer writes absolute E with a
G92 E0 after every retraction, so each unretract that follows a reset read as
2 mm of new filament: 10,232 of them. The G-code below is the real pattern,
cut down: extrude, retract 2, reset, unretract 2, extrude.
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import virtual_printer as vp  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# 10 mm printed before the reset, 5 mm after: 15 mm of filament
_GCODE = """M82
G92 E0
;TYPE:Perimeter
G1 X10 Y10 E10
G1 E8 F2400
G92 E0
G1 X20 Y20 F7800
G1 E2 F2400
;TYPE:Perimeter
G1 X30 Y20 E7
G1 E5 F2400
G1 X40 Y40
G1 E7 F2400
"""


def _analyse(text):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "t.gcode"
        p.write_text(text)
        return vp.analyse(str(p))


def test_unretract_after_reset_is_not_counted():
    r = _analyse(_GCODE)
    check(abs(r["filament_mm"] - 15.0) < 1e-6, f"expected 15 mm, got {r['filament_mm']}")


def test_slicer_total_wins_when_present():
    r = _analyse(_GCODE + "; filament used [cm3] = 58.91\n")
    check(r["filament_g"] == round(58.91 * 1.24, 1), f"expected {round(58.91 * 1.24, 1)} g, got {r['filament_g']}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("VIRTUAL PRINTER FILAMENT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIRTUAL PRINTER FILAMENT TESTS OK — an unretract after an E reset is not counted twice, and the slicer's own total is used when it gives one.")


if __name__ == "__main__":
    run()
