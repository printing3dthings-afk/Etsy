"""tools/small_parts.py against cases worked by hand on the 16 CFR 1501.4 cylinder
(31.7 mm bore, floor slanting from 25.4 to 57.1 mm deep), 2026-11-14."""
import sys
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import small_parts  # noqa: E402

_failures: list[str] = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


def pts(m):
    return m.convex_hull.vertices


def test_upright_puck_fits_by_the_slant_arithmetic():
    # 30 x 20 puck, upright and shifted 0.85 to the deep side: its shallow edge rests where
    # the floor is 25.4 + 1.7 = 27.1 deep, so its top is 7.1 below the rim
    ok, depth, _ = small_parts.fit(pts(trimesh.creation.cylinder(radius=15.0, height=20, sections=96)), 800)
    check(ok and abs(depth - 7.1) < 0.2, f"puck 30x20: expected fits at 7.1, got {ok} {depth}")


def test_wider_than_the_bore_never_fits():
    ok, depth, bore = small_parts.fit(pts(trimesh.creation.cylinder(radius=16.5, height=5, sections=96)), 800)
    check(not ok and depth is None and bore < 0, f"33 mm disc: expected never in the bore, got {ok} {depth} {bore}")


def test_one_inch_cube_never_fits():
    # its narrowest outline is 25.4 square, 35.9 across the corners: wider than 31.7
    ok, depth, _ = small_parts.fit(pts(trimesh.creation.box([25.4] * 3)), 800)
    check(not ok and depth is None, f"1 in cube: expected too big, got {ok} {depth}")


def test_long_stick_sticks_out():
    # 10 x 10 x 60: standing on the floor's shallow corner (45.0 deep) its top is 15 above
    ok, depth, _ = small_parts.fit(pts(trimesh.creation.box([10, 10, 60])), 800)
    check(not ok and depth < -10, f"60 mm stick: expected out by ~15, got {ok} {depth}")


def test_marble_is_a_small_part():
    ok, _, _ = small_parts.fit(pts(trimesh.creation.icosphere(radius=8)), 300)
    check(ok, "16 mm marble should be a small part")


def run():
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("SMALL PARTS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("SMALL PARTS TESTS OK -- the cylinder search agrees with five hand-worked cases.")


if __name__ == "__main__":
    run()
