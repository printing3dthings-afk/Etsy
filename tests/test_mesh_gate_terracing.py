"""
Tests for mesh_gate's terracing check (2026-09-08).

Added after the first real printed sauce bowl came off the plate ringed with 27
concentric terraces while every existing check passed it: watertight, one body,
inside the envelope, no overhang. The gate had no concept of "this surface is
too shallow to print cleanly."

These pin the two ends of the band, which is where the check is easy to get
wrong in opposite directions:
  * a FLAT top face must score zero -- it is one clean surface with no steps at
    all, the thing to aim for, and a naive slope test calls it infinitely
    shallow and flags it hardest of anything.
  * a genuinely shallow dome must be caught, because that is the real defect.
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


def _dome(rise, radius, n=160):
    """A paraboloid cap rising `rise` over `radius` -- the bowl's old top face."""
    xs = np.linspace(-radius, radius, n)
    X, Y = np.meshgrid(xs, xs)
    R = np.hypot(X, Y)
    Z = rise * np.clip(R / radius, 0, 1) ** 2
    verts, faces = [], []
    idx = lambda i, j: i * n + j
    for i in range(n):
        for j in range(n):
            verts.append([X[i, j], Y[i, j], Z[i, j]])
    for i in range(n - 1):
        for j in range(n - 1):
            # Wound so the normals point UP. The check only looks at upward
            # faces -- correctly, since a real printed part's top surface does.
            # trimesh's invert() does not take on a process=False mesh, so get
            # the winding right here rather than loosening the check.
            faces += [[idx(i, j), idx(i + 1, j + 1), idx(i + 1, j)],
                      [idx(i, j), idx(i, j + 1), idx(i + 1, j + 1)]]
    return trimesh.Trimesh(np.array(verts), np.array(faces), process=False)


def test_flat_face_is_not_terracing():
    """The fix must not read as the defect. A flat top has no steps at all."""
    flat = trimesh.creation.box(extents=[100, 100, 10])
    area, worst = mesh_gate._terrace_report(flat)
    check(area == 0.0, f"a flat top face was flagged as terracing ({area} mm2)")
    check(worst == 0.0, f"flat face reported a {worst}mm terrace")


def test_shallow_dome_is_caught():
    """The real defect: 5.5mm of rise over 95mm of radius rang across 212mm."""
    area, worst = mesh_gate._terrace_report(_dome(5.5, 95.0))
    check(area > 5000.0, f"the bowl's old top face only measured {area:.0f} mm2")
    check(worst > 1.0, f"expected terraces well over a bead, got {worst:.2f}mm")


def test_steep_cone_is_not_flagged():
    """A 45-degree surface steps one layer height -- invisible, must not flag."""
    cone = trimesh.creation.cone(radius=20, height=20)   # 45 deg
    area, _ = mesh_gate._terrace_report(cone)
    check(area == 0.0, f"a 45-degree surface was flagged ({area:.1f} mm2)")


def test_the_shipped_bowls_score_zero():
    """Both bowls were re-cut to flat faces; a regression here means it came back."""
    for name in ("sauce_bowl", "sauce_bowl_1oz"):
        stl = ROOT / "openscad_models" / f"{name}.stl"
        if not stl.exists():
            continue
        res = mesh_gate.gate(str(stl), expected_components=1)
        row = [c for c in res["checks"] if c["check"] == "terracing"][0]
        check("no shallow upward surface" in row["detail"],
              f"{name} terraces again: {row['detail']}")
        check(res["passed"], f"{name} no longer passes the gate: {res['checks']}")


def test_terracing_is_reported_never_fatal():
    """An organic model may carry shallow area on purpose; this is INFO."""
    res = mesh_gate.gate(str(ROOT / "openscad_models" / "sauce_bowl.stl"))
    row = [c for c in res["checks"] if c["check"] == "terracing"][0]
    check(row["level"] == "INFO", "terracing became fatal -- it would fail organic models")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("MESH GATE TERRACING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("MESH GATE TERRACING TESTS OK -- a flat face scores zero, a 5.5mm-over-95mm "
          "dome is caught, and both shipped bowls stay clean.")


if __name__ == "__main__":
    run()
