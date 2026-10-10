"""--views must look at the model's FRONT (2026-09-27).

The views were a fixed azimuth of 180, set for a tombstone whose front faced
+Y. Every Haunted Town building faces -Y, so its "front" and "three-quarter"
renders showed the back: no chapel door, no shop signs, no carved lettering.
This checks, from the camera formula in the render script itself, that each
front setting puts the camera on the side the front faces.
"""
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import blender_render as br  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _camera_y_sign(az_deg: float) -> float:
    # The same expression the Blender script uses for the camera's Y.
    src = (ROOT / "tools" / "blender_render.py").read_text()
    check("cam_y = -dist * math.cos(el) * math.cos(az)" in src,
          "the camera Y formula changed; re-derive this test from it")
    return math.copysign(1.0, -math.cos(math.radians(az_deg)))


def test_front_and_three_quarter_look_at_the_front():
    for front, want in (("-y", -1.0), ("+y", 1.0)):
        spec = dict((n, (az, el)) for n, az, el in br.VIEW_SPEC[front])
        for view in ("front", "three_quarter"):
            got = _camera_y_sign(spec[view][0])
            check(got == want, f"front {front}: the {view} camera is on the "
                               f"{'+' if got > 0 else '-'}Y side, the model's back")


def test_the_default_is_minus_y():
    # The documented convention (azimuth 0 = camera on -Y) and every Haunted
    # Town model. A +Y model has to say so.
    import inspect
    check(inspect.signature(br.render_views).parameters["front"].default == "-y",
          "render_views must default to a -Y front")
    src = (ROOT / "tools" / "blender_render.py").read_text()
    check(re.search(r'"--front".*default="-y"', src) is not None,
          "the --front CLI flag must default to -y")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("BLENDER VIEWS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("BLENDER VIEWS TESTS OK — the front and three-quarter cameras sit on the "
          "side the model's front faces, and the default is -Y.")


if __name__ == "__main__":
    run()
