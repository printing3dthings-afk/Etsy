"""
product_gate's declared wall regions leave out only what they declare (2026-11-05).

The gingerbread tin's prints declare their thread teeth, the cookie's switch
socket and their raised colour detail to the 1.2 mm wall floor, because those
are thin by design and checked by other means (wall_regions.py,
CLICKERS_PRINTING.md). The floor must still hold everywhere else. This builds
a cup whose wall is 2.0 mm, with a 0.6 mm fin standing on its floor inside a
band, and a 0.6 mm fin outside it, and checks that:

  - with nothing declared, both fins count, and the numbers are exactly what
    they were before the hook existed (skip=None is the old code path);
  - declaring the band leaves out the fin inside it, and only that fin: the
    one outside still pulls the 1st percentile under the floor;
  - declaring a part (a mesh standing for raised detail) leaves out spans
    whose midpoint is inside it;
  - the report says how many spans were left out.
"""
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import mesh_gate  # noqa: E402
import product_gate  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _cup_with_fins(tmp):
    outer = trimesh.creation.cylinder(radius=20, height=20, sections=96)
    outer.apply_translation([0, 0, 10])
    inner = trimesh.creation.cylinder(radius=18, height=20, sections=96)
    inner.apply_translation([0, 0, 12])           # a 2.0 floor, a 2.0 wall
    cup = outer.difference(inner)
    fin_in = trimesh.creation.box([0.6, 6, 8])    # at r 5: inside the band
    fin_in.apply_translation([5, 0, 6])
    fin_out = trimesh.creation.box([0.6, 6, 8])   # at r 12: outside it
    fin_out.apply_translation([12, 0, 6])
    m = trimesh.boolean.union([cup, fin_in, fin_out])
    p = Path(tmp) / "cup.stl"
    m.export(p)
    d = Path(tmp) / "detail.stl"
    fin_out.export(d)
    return str(p), str(d)


def test_skip_leaves_out_only_what_is_declared():
    with tempfile.TemporaryDirectory() as tmp:
        cup, detail = _cup_with_fins(tmp)
        plain = mesh_gate.wall_thickness(cup)
        none = mesh_gate.wall_thickness(cup, skip=None)
        check(plain["samples"] == none["samples"] and plain["p1"] == none["p1"],
              f"skip=None changed the numbers: {plain} vs {none}")
        check(plain["p1"] < 1.2, f"the cup's two 0.6 fins should fail the floor, p1 {plain['p1']:.2f}")

        band = product_gate.wall_skipper(bands=[(3.0, 7.0, 1.5, 11.0)])
        b = mesh_gate.wall_thickness(cup, skip=band)
        check(b["skipped"] > 0, "the band left nothing out")
        check(b["samples"] == plain["samples"] - b["skipped"],
              f"samples {b['samples']} + skipped {b['skipped']} != {plain['samples']}")
        check(b["p1"] < 1.2, f"the fin outside the band must still fail the floor, p1 {b['p1']:.2f}")

        both = product_gate.wall_skipper(parts=[detail], bands=[(3.0, 7.0, 1.5, 11.0)])
        a = mesh_gate.wall_thickness(cup, skip=both)
        check(a["p1"] >= 1.2, f"with both fins declared the 2.0 cup should pass, p1 {a['p1']:.2f}")

        r = product_gate.gate(cup, wall_skip=both)
        wall = next(c for c in r["checks"] if c["check"] == "min_wall")
        check("not counted" in wall["detail"], f"the report doesn't say spans were left out: {wall['detail']}")
        r0 = product_gate.gate(cup)
        wall0 = next(c for c in r0["checks"] if c["check"] == "min_wall")
        check(not wall0["pass"] and "not counted" not in wall0["detail"],
              f"undeclared, the gate must fail and say nothing of skipping: {wall0['detail']}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PRODUCT GATE WALL SKIP TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRODUCT GATE WALL SKIP TESTS OK — declared regions leave out only what they declare; "
          "undeclared, the floor and its numbers are unchanged.")


if __name__ == "__main__":
    run()
