#!/usr/bin/env python3
"""Tests for tools/print_risk.py.

The defect this guards against is over-reporting risk: "longest bridge move"
is not "longest unsupported span". A straight extrusion can pass over ground
that is already printed. On this shop's sauce tray the longest bridge MOVE is
107.9mm while the longest genuinely unsupported run inside it is 5.6mm -- at
z=0.8mm, which is the ceiling of the engraved maker's mark on the underside,
independently the same place an earlier overhang investigation landed.

Reporting 107.9 would have made a clean part look unprintable.
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import print_risk  # noqa: E402
from gcode_viewer_data import parse  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# Layer 1 lays a bead from x=0 to x=10 at y=0.
# Layer 2 bridges from x=0 all the way to x=30 along the same line.
# The first 10mm sits on layer 1; the remaining 20mm spans open air.
FIXTURE = """\
M83
;LAYER_CHANGE
;Z:0.2
;HEIGHT:0.2
;TYPE:External perimeter
G1 X0 Y0 F9000
G1 X10 Y0 E1.0 F1800
;LAYER_CHANGE
;Z:0.4
;HEIGHT:0.2
;TYPE:Bridge infill
G1 X0 Y0 F9000
G1 X30 Y0 E3.0 F3600
; slowdown_below_layer_time = 5
; extrusion_width = 0.42
"""


def _write(text):
    fh = tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False)
    fh.write(text)
    fh.close()
    return Path(fh.name)


def test_unsupported_span_excludes_the_supported_part_of_a_bridge_move():
    path = _write(FIXTURE)
    try:
        span, z = print_risk.unsupported_spans(parse(path))
        check(15 <= span <= 21,
              f"unsupported span reported as {span}mm -- the move is 30mm long but "
              "its first 10mm sits on layer 1, so only ~20mm is unsupported. "
              "Reporting the whole move length overstates the risk.")
        check(z == 0.4, f"span should be found on the 0.4mm layer, got z={z}")
    finally:
        path.unlink(missing_ok=True)


def test_fully_supported_bridge_reports_nothing():
    supported = FIXTURE.replace("G1 X10 Y0 E1.0 F1800", "G1 X30 Y0 E3.0 F1800")
    path = _write(supported)
    try:
        span, _z = print_risk.unsupported_spans(parse(path))
        check(span < 1.0,
              f"a bridge laid entirely over existing extrusion reported {span}mm "
              "unsupported -- it is fully supported and should report ~0")
    finally:
        path.unlink(missing_ok=True)


def test_analyse_reads_the_profiles_own_cooling_threshold():
    path = _write(FIXTURE)
    try:
        r = print_risk.analyse(path)
        check(r["slowdown_threshold_s"] == 5.0,
              f"threshold should come from the file's own config, got "
              f"{r['slowdown_threshold_s']}")
        check(r["first_layer_area_mm2"] > 0, "first layer area should be positive")
        check(r["aspect_ratio"] is not None, "aspect ratio should be computed")
    finally:
        path.unlink(missing_ok=True)


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PRINT RISK TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRINT RISK TESTS OK -- an unsupported span measures the part of a "
          "bridge with nothing beneath it, not the whole move.")


if __name__ == "__main__":
    run()
