"""tools/bambu_gcode.py: Bambu Studio G-code read as PrusaSlicer-tagged G-code (2026-11-14).

The real failure: a Bambu slice fed to our readers came out as ONE layer (they look for
";LAYER_CHANGE"), and Bambu's G2/G3 arcs, 3,635 of them on one coupon, were skipped."""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import bambu_gcode as bg  # noqa: E402
import print_fidelity as pf  # noqa: E402

_failures: list[str] = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


SAMPLE = """M83 ; relative E
; CHANGE_LAYER
; Z_HEIGHT: 0.2
; LAYER_HEIGHT: 0.2
G1 Z.2
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 X10 Y0 F3000
G3 X-10 Y0 I-10 J0 E1.5708
G3 X10 Y0 I10 J0 E1.5708
; FEATURE: Prime tower
G1 X50 Y50 E1
; CHANGE_LAYER
; Z_HEIGHT: 0.4
; LAYER_HEIGHT: 0.2
; FEATURE: Outer wall
G1 X-10 Y0
G2 X10 Y0 I10 J0 E3.1416
""".splitlines()


def test_markers_become_prusa_markers():
    out = bg.convert(SAMPLE)
    check(out.count(";LAYER_CHANGE") == 2, f"layer changes: {out.count(';LAYER_CHANGE')}")
    check(";Z:0.2" in out and ";HEIGHT:0.2" in out and ";TYPE:External perimeter" in out and ";WIDTH:0.42" in out,
          "a marker was not translated")
    check(";TYPE:Wipe tower" in out, "Bambu's prime tower must read as the wipe tower (not part of the model)")
    import gcode_viewer_data as gvd
    for bambu, prusa in bg.FEATURES.items():
        check(prusa in gvd.TYPES or prusa == "Gap fill", f"{bambu} maps to {prusa}, which the viewer doesn't know")


def test_arcs_become_segments_on_the_circle_with_all_their_filament():
    out = bg.convert(SAMPLE)
    e = sum(float(s.split(" E")[1].split()[0]) for s in out if s.startswith("G1") and " E" in s and "X50" not in s)
    check(abs(e - (1.5708 * 2 + 3.1416)) < 1e-3, f"filament not conserved: {e}")
    pts = [s for s in out if s.startswith("G1 X") and "X50" not in s and "F3000" not in s and " E" in s]
    r = [math.hypot(float(s.split("X")[1].split()[0]), float(s.split("Y")[1].split()[0])) for s in pts]
    check(len(pts) > 200 and max(abs(v - 10) for v in r) < 1e-3, f"arc points off the r 10 circle ({len(pts)} pts)")


def test_readers_see_every_layer():
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as f:
        f.write("\n".join(bg.convert(SAMPLE)) + "\n")
    layers = pf.parse_gcode(f.name)
    check(len(layers) == 2 and layers[0]["z"] == 0.2 and layers[1]["z"] == 0.4, f"parse_gcode saw {len(layers)} layers")


def run():
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("BAMBU GCODE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("BAMBU GCODE TESTS OK -- Bambu's markers and arcs read as our readers expect, filament conserved.")


if __name__ == "__main__":
    run()
