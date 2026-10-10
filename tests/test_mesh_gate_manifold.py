"""A hole and a flush contact are not the same defect, and the gate must say so.

Reproduces the exact false alarm found 2026-09-17: sweeping all 147 meshes in
openscad_models/ made mesh_gate fail seven of them with "open edges -- the
slicer will guess at the holes". Every one had ZERO boundary edges. They failed
only because some edges are shared by four faces, which is what two closed
solids touching flush looks like -- a plaque sitting on a tombstone, engraved
text meeting its tile. All seven then sliced cleanly through the real slicer
with sane filament figures, so the gate was about to send Scott to fix files
that were never broken.
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


def _result(mesh, tmp_name):
    p = ROOT / "tests" / tmp_name
    mesh.export(p)
    try:
        return {c["check"]: c for c in mesh_gate.gate(str(p))["checks"]}
    finally:
        p.unlink(missing_ok=True)


def _two_cubes_touching_flush():
    """Two closed boxes sharing an entire face: no holes, 4-face edges."""
    a = trimesh.creation.box(extents=(10, 10, 10))
    b = trimesh.creation.box(extents=(10, 10, 10))
    b.apply_translation((0, 0, 10))
    return trimesh.util.concatenate([a, b])


def test_flush_contact_is_not_a_hole():
    r = _result(_two_cubes_touching_flush(), "_tmp_flush.stl")
    check(r["no_holes"]["pass"],
          "two solids touching flush have no holes; got %r" % r["no_holes"]["detail"])
    check(not r["manifold_edges"]["pass"] or "more than two faces" in r["manifold_edges"]["detail"]
          or r["manifold_edges"]["detail"].startswith("every edge"),
          "the non-manifold edges should be reported somewhere")
    check("more than two faces" in r["manifold_edges"]["detail"],
          "flush contact should be reported as non-manifold edges, got %r"
          % r["manifold_edges"]["detail"])


def test_non_manifold_edges_never_fail_the_gate():
    r = _result(_two_cubes_touching_flush(), "_tmp_flush2.stl")
    check(r["manifold_edges"]["level"] == "INFO",
          "slicers repair flush contacts; this must not be a hard failure")


def test_a_closed_but_non_manifold_mesh_still_reports_its_volume():
    # Gating volume on trimesh's `is_volume` (which also demands manifold edges)
    # printed 0.00 cm3 for parts that are closed and perfectly printable.
    r = _result(_two_cubes_touching_flush(), "_tmp_flush3.stl")
    check(r["positive_volume"]["pass"],
          "a closed surface has a volume regardless of flush contacts")
    cm3 = float(r["positive_volume"]["detail"].split()[0])
    check(abs(cm3 - 2.0) < 0.01, "two 1 cm3 cubes should measure 2 cm3, got %s" % cm3)


def test_a_real_hole_still_fails():
    m = trimesh.creation.box(extents=(10, 10, 10))
    m.update_faces(np.arange(len(m.faces)) > 1)   # drop two faces -> a real hole
    r = _result(m, "_tmp_hole.stl")
    check(not r["no_holes"]["pass"], "a mesh missing faces must still fail")
    check("boundary edges" in r["no_holes"]["detail"],
          "the failure should name boundary edges, got %r" % r["no_holes"]["detail"])
    check(not r["positive_volume"]["pass"],
          "an open mesh has no trustworthy volume")


def test_a_clean_solid_passes_everything():
    r = _result(trimesh.creation.box(extents=(20, 20, 20)), "_tmp_clean.stl")
    for name in ("no_holes", "winding_consistent", "positive_volume", "no_degenerate_faces"):
        check(r[name]["pass"], "a plain box should pass %s" % name)
    check(r["manifold_edges"]["detail"].startswith("every edge"),
          "a plain box has no non-manifold edges, got %r" % r["manifold_edges"]["detail"])


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append("%s raised:\n%s" % (fn.__name__, traceback.format_exc()))
    if _failures:
        print("MESH GATE MANIFOLD TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("MESH GATE MANIFOLD TESTS OK -- a hole fails, two solids touching flush "
          "do not, and a closed non-manifold part still reports its real volume.")


if __name__ == "__main__":
    run()
