"""
mesh_gate.wall_thickness must never report AIR as a wall (2026-09-24).

It used to drop every ray hit more than 60 degrees off head-on, to stop
tangential grazes recording ~0 spans. A ray that genuinely CROSSES a steep
face then lost a hit, the in/out pairing slipped by one, and every air gap
further along that ray was reported as a wall. Found on haunted_bakery: 149 of
the 351 spans the gate called thinner than 1.2 mm had their midpoint outside
the solid -- enough, on its own, to fail the 1st-percentile floor.

The shape here reproduces it exactly: a prism whose underside is a 75 deg
face, a 0.6 mm air gap above it, and a block above that. The old code reported
the 0.6 mm gap as a wall.
"""
import sys
import tempfile
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


GAP = 0.6


def _steep_underside_under_a_gap():
    """A prism whose UNDERSIDE is a 75 deg face, a 0.6 mm gap, then a block.

    Rising from the plate, a vertical ray meets: the steep underside (the hit
    the old code dropped), the prism's flat top, the gap, the block's bottom
    and the block's top. With the first hit dropped it paired top-of-prism
    with bottom-of-block and reported the gap as a 0.6 mm wall.
    """
    run = 10 / np.tan(np.radians(75))
    prof = [[-10 + run, 0], [7, 0], [7, 10], [-10, 10]]
    v = [[x, y, z] for y in (-10, 10) for x, z in prof]
    f = [[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
         [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
         [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]]
    prism = trimesh.Trimesh(np.array(v, float), f, process=True)
    prism.fix_normals()
    block = trimesh.creation.box(extents=[17, 20, 4])
    block.apply_translation([-1.5, 0, 10 + GAP + 2])
    return trimesh.util.concatenate([prism, block])


def test_an_air_gap_is_never_measured_as_a_wall():
    m = _steep_underside_under_a_gap()
    check(m.is_watertight, "test shape is not watertight -- the test itself is broken")
    sp = mesh_gate._wall_spans(m, samples=64)
    as_gap = int((np.abs(sp - GAP) < 1e-3).sum())
    check(as_gap == 0, f"the {GAP} mm air gap was reported as a wall {as_gap} times")


def test_a_plain_hollow_box_still_measures_its_wall():
    outer = trimesh.creation.box(extents=[30, 30, 30])
    inner = trimesh.creation.box(extents=[26, 26, 26])
    shell = trimesh.Trimesh(np.vstack([outer.vertices, inner.vertices]),
                            np.vstack([outer.faces, inner.faces[:, ::-1] + len(outer.vertices)]))
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "m.stl"
        shell.export(p)
        r = mesh_gate.wall_thickness(str(p), samples=64)
    check("error" not in r, f"measurement failed: {r}")
    check(abs(r["p1"] - 2.0) < 0.05, f"a 2 mm shell measured p1 {r['p1']:.3f}, expected 2.0")


def test_corner_clips_are_still_not_walls():
    # The first fix kept every hit AND reported every span: the shipped sauce
    # tray's p1 fell from 3.48 to 0.04 on 0.03 mm corner clips. The grazing
    # filter has to survive, applied per span.
    r = mesh_gate.wall_thickness(str(ROOT / "openscad_models" / "sauce_tray.stl"))
    check("error" not in r, f"measurement failed: {r}")
    check(r.get("p1", 0) > 3.0, f"sauce_tray p1 {r.get('p1')}, expected ~3.48 -- grazes counted as walls")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("MESH GATE WALL PARITY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("MESH GATE WALL PARITY TESTS OK — an air gap behind a steep face is never "
          "counted as a wall, corner clips still are not, and a plain shell still "
          "measures its real thickness.")


if __name__ == "__main__":
    run()
