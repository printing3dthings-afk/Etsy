"""
Tests for tools/mesh_gate.py (2026-09-06), the pre-slice pass/fail gate.

These are regression tests for two real bugs found while writing that tool
against this shop's own already-verified models, not generic coverage:

  1. The overhang scan measured its angle from HORIZONTAL while the limit is
     stated from VERTICAL, inverting the test so it flagged the SAFEST
     surfaces. It reported a "failure" on all three verified, already-sliced
     models at once (sauce bowl, sauce tray, dumpling clicker).
  2. It counted the flat underside resting ON the build plate as an unsupported
     overhang. Every model has one, so every model failed.

And one deliberate design decision worth pinning: overhang is INFO, never a
FAIL. Every face it flags on sauce_tray.stl is the 0.7mm-deep ceiling of the
engraved maker's mark on the underside -- a bridge that short prints on any FDM
machine. Angle alone cannot separate that from a real unsupported span, so a
human judges it. If someone later makes overhang fatal, these tests fail and
say why.
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import mesh_gate  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _box(ext, at):
    b = trimesh.creation.box(extents=ext)
    b.apply_translation(at)
    return b


def test_plate_face_is_not_an_overhang():
    """A cube's flat underside sits ON the plate -- supported, not overhanging."""
    area, worst, _ = mesh_gate._overhang_report(_box([10, 10, 10], [0, 0, 5]))
    check(area == 0.0, f"cube reported {area} mm2 of overhang; its base is on the plate")
    check(worst == 0.0, f"cube worst angle {worst}, expected 0")


def test_self_supporting_cone_passes():
    """Apex-up cone: every layer is supported by a wider one below it."""
    area, _, _ = mesh_gate._overhang_report(trimesh.creation.cone(radius=10, height=10))
    check(area == 0.0, f"self-supporting cone reported {area} mm2 of overhang")


def test_45_degree_slope_is_under_the_limit():
    """A 45-degree slope is well inside the 55-degree structural limit."""
    cone = trimesh.creation.cone(radius=10, height=10)
    cone.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    cone.apply_translation([0, 0, 10])
    area, worst, _ = mesh_gate._overhang_report(cone)
    check(area == 0.0, f"45-degree slope flagged {area} mm2; limit is 55 degrees")
    check(44.0 < worst < 46.0, f"expected ~45 degrees from vertical, got {worst}")


def test_real_ceiling_is_caught():
    """A slab held up by a thin post: its underside is a true 90-degree ceiling."""
    t = trimesh.util.concatenate([_box([4, 4, 10], [0, 0, 5]), _box([40, 40, 2], [0, 0, 11])])
    area, worst, zr = mesh_gate._overhang_report(t)
    check(area > 1000.0, f"T-bracket ceiling only measured {area} mm2, expected >1000")
    check(worst > 89.0, f"a flat ceiling is 90 degrees from vertical, got {worst}")
    check(zr is not None and abs(zr[0] - 10.0) < 0.01,
          f"ceiling should sit at z=10, got {zr}")


def test_overhang_is_informational_never_fatal():
    """The three shipped models all carry flagged faces and must still PASS."""
    for name in ("sauce_tray", "sauce_bowl", "dumpling_clicker_bao"):
        stl = ROOT / "openscad_models" / f"{name}.stl"
        if not stl.exists():
            continue
        res = mesh_gate.gate(str(stl), expected_components=1, check_overhang=True)
        over = [c for c in res["checks"] if c["check"] == "overhang"]
        check(len(over) == 1, f"{name}: no overhang check emitted")
        check(over and over[0]["level"] == "INFO",
              f"{name}: overhang is fatal again -- it flags engraved-mark ceilings that print fine")
        check(res["passed"], f"{name} is verified and sliced but the gate now fails it: {res['checks']}")


def test_component_count_is_an_argument_not_an_assumption():
    """A multi-body model fails against the default and passes against the truth."""
    stl = ROOT / "openscad_models" / "axolotl.stl"
    if not stl.exists():
        return
    strict = mesh_gate.gate(str(stl), expected_components=1)
    check(not strict["passed"], "a 4-body model passed a 1-body expectation")
    honest = mesh_gate.gate(str(stl), expected_components=4)
    comp = [c for c in honest["checks"] if c["check"] == "component_count"][0]
    check(comp["pass"], f"4-body model failed an explicit -c 4: {comp['detail']}")


def test_unloadable_file_fails_closed():
    """A mesh that will not load is a gate failure, never a stack trace."""
    try:
        mesh_gate.gate(str(ROOT / "does_not_exist.stl"))
    except Exception:
        return  # main() converts this into exit 1; raising here is the contract
    _failures.append("a missing mesh loaded without error")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("MESH GATE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("MESH GATE TESTS OK -- overhang angle is measured from vertical, plate faces are "
          "excluded, and a verified model is never failed by an informational check.")


if __name__ == "__main__":
    run()
