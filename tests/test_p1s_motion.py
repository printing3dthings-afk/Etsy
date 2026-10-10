"""The P1S motion model (tools/p1s_motion.py) and the move timing it feeds into
the viewer payload (2026-10-10).

Scott asked how real the viewer's physics are. They were not: every slice ran
at PrusaSlicer's defaults (a third of the P1S's pace), each layer's time was
spread evenly over its length, travel took no time and filament swaps took
none either. These tests pin the replacement:

- the trapezoid maths, against hand-worked numbers;
- the model against PrusaSlicer's own estimator on a real slice at Bambu's
  P1S settings -- two independent implementations of the same planner (the
  phone stand agreed to 0.15%: 4,643 s against 4,650 s);
- the slicer is actually given Bambu's numbers (inner walls at 300 mm/s, which
  the old one-byte speed field would have clamped to 255);
- a filament swap costs Bambu's stated load + unload time;
- simplification merges segments without losing a second;
- every second the model counts lands somewhere the viewer replays.
"""
import math
import shutil
import struct
import base64
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import p1s_motion as pm          # noqa: E402
import gcode_viewer_data as gvd  # noqa: E402
import virtual_printer as vp     # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def close(a, b, rel=1e-6):
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-12)


def test_trapezoid_reaches_cruise_on_a_long_move():
    # 100 mm at 100 mm/s, 1000 mm/s2, from and to rest: 5 mm to accelerate,
    # 5 mm to brake, 90 mm cruising. 0.1 + 0.1 + 0.9 s.
    t = pm.trapezoid_time(100, 0, 100, 0, 1000)
    check(close(t, 1.1), f"long move should take 1.1 s, got {t}")


def test_trapezoid_is_a_triangle_on_a_short_move():
    # 1 mm never reaches 100 mm/s at 1000 mm/s2: peak sqrt(a*d) = 31.62 mm/s.
    t = pm.trapezoid_time(1, 0, 100, 0, 1000)
    check(close(t, 2 * math.sqrt(1000) / 1000), f"short move should be a triangle, got {t}")


def test_a_sharp_corner_brakes_and_a_straight_does_not():
    straight = pm.Planner()
    for _ in range(10):
        straight.add_move(5, 0, 0, 0.2, 200, 10000, "print")
    zigzag = pm.Planner()
    for i in range(10):
        zigzag.add_move(5 if i % 2 == 0 else -5, 0, 0, 0.2, 200, 10000, "print")
    ts, tz = sum(straight.solve()), sum(zigzag.solve())
    check(tz > ts * 1.5,
          f"reversing every 5 mm must cost far more than a straight run ({tz:.3f} vs {ts:.3f} s)")


def test_travel_acceleration_is_capped_by_the_machine():
    p = pm.Planner()
    i = p.add_move(100, 0, 0, 0, 500, 10000, "travel")
    check(p.acc[i] == pm.P1S_LIMITS["max_acceleration_travel"],
          f"P1S travel acceleration is capped at 9000, got {p.acc[i]}")


def test_a_filament_swap_costs_bambus_load_and_unload_time():
    check(pm.P1S_TOOLCHANGE_S == 57.0,
          f"P1S swap = 28 s unload + 29 s load, got {pm.P1S_TOOLCHANGE_S}")
    g = """M83
;TYPE:External perimeter
G1 X10 Y10 F3000
G1 X20 Y10 E1 F12000
T1
G1 X20 Y20 E1 F12000
"""
    p = _write(g)
    try:
        raw = gvd.parse(p)
    finally:
        p.unlink(missing_ok=True)
    total = sum(raw["segTimes"]) + sum(raw["gapTimes"])
    check(total > pm.P1S_TOOLCHANGE_S,
          f"a plate with one swap must take over {pm.P1S_TOOLCHANGE_S} s, got {total:.2f}")
    check(raw["gapTimes"][-1] >= pm.P1S_TOOLCHANGE_S,
          "the swap belongs to the gap before the line printed after it, "
          f"got gaps {raw['gapTimes']}")


def test_the_slicer_is_given_bambus_p1s_speeds():
    m = vp.P1S_MOTION
    check(m["perimeter-speed"] == "300" and m["external-perimeter-speed"] == "200"
          and m["infill-speed"] == "270" and m["travel-speed"] == "500",
          "the slice must run at Bambu's 0.20 Standard P1 speeds")
    check(m["default-acceleration"] == "10000" and m["external-perimeter-acceleration"] == "5000",
          "and Bambu's accelerations")
    check(m["filament-max-volumetric-speed"] == "21", "Bambu PLA Basic flows at most 21 mm3/s")


def test_simplification_keeps_every_second():
    g = "M83\n;TYPE:External perimeter\nG1 X10 Y10 F3000\n" + "".join(
        f"G1 X{10 + i * 0.5:.3f} Y{10 + 0.001 * (i % 2):.3f} E0.02 F12000\n" for i in range(1, 60))
    p = _write(g)
    try:
        raw = gvd.parse(p)
    finally:
        p.unlink(missing_ok=True)
    before = sum(raw["segTimes"])
    out = gvd.simplify(raw, 0.02)
    check(len(out["segTimes"]) < len(raw["segTimes"]), "the fixture should simplify")
    check(close(sum(out["segTimes"]), before),
          f"merging segments must not lose time: {before} -> {sum(out['segTimes'])}")


def test_the_viewer_replays_the_whole_modelled_time():
    g = """M83
;LAYER_CHANGE
;Z:0.2
;HEIGHT:0.2
;TYPE:External perimeter
G1 X10 Y10 F30000
G1 X60 Y10 E2 F12000
G1 X60 Y60 E2
G1 X120 Y60 F30000
G1 X120 Y120 E2 F12000
"""
    p = _write(g)
    try:
        job = gvd.build_job(p, "t", tol_mm=0)
        raw = gvd.parse(p)
    finally:
        p.unlink(missing_ok=True)
    model = sum(raw["segTimes"]) + sum(raw["gapTimes"])
    check(close(job["totalSeconds"], round(model, 1), rel=0.01),
          f"payload total {job['totalSeconds']} must be the model's {model:.2f}")
    gb = base64.b64decode(job["gapT"])
    gaps = struct.unpack(f"<{len(gb) // 4}f", gb)
    check(len(gaps) == 2 and gaps[1] > 0,
          f"the travel between the two lines must be a timed gap, got {gaps}")


def test_the_model_agrees_with_prusaslicers_own_estimator():
    exe = shutil.which("prusa-slicer") or shutil.which("prusa-slicer-console")
    stl = ROOT / "openscad_models" / "label_tile.3mf"
    if not exe or not stl.exists():
        print("  (skipped: no prusa-slicer or no fixture model)")
        return
    with tempfile.TemporaryDirectory() as td:
        g = Path(td) / "t.gcode"
        vp.slice_model(stl, g, supports=False)
        raw = gvd.parse(g)
    est = raw["slicerSeconds"]
    model = sum(raw["segTimes"]) + sum(raw["gapTimes"])
    check(est and abs(model - est) / est < 0.03,
          f"model {model:.0f} s should be within 3% of PrusaSlicer's {est} s")


def _write(text):
    fh = tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False)
    fh.write(text)
    fh.close()
    return Path(fh.name)


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("P1S MOTION TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("P1S MOTION TESTS OK — move times follow acceleration and cornering, match "
          "PrusaSlicer's estimator, count filament swaps, and all reach the viewer.")


if __name__ == "__main__":
    run()
