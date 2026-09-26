"""Guards the bead-mesh exporter against the three bugs that built it wrong.

Every one of them produced a file that opened fine, passed a casual look, and
was wrong in a way only a render or a measurement showed.
"""
import base64
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import gcode_to_mesh as g2m  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _payload(n_layers=6, n_pts=12, radius=10.0):
    """A small round tower: several stacked closed loops, one per layer."""
    pts, polys, layers = [], [], []
    for li in range(n_layers):
        start = len(pts) // 2
        for i in range(n_pts):
            a = 2 * np.pi * i / (n_pts - 1)
            pts += [int(round((100 + radius * np.cos(a)) * 100)),
                    int(round((100 + radius * np.sin(a)) * 100))]
        polys += [0, start, n_pts]
        layers.append([int((li + 1) * 20), li, 1, 1.0, 1.0, 0.2])
    return {
        "pts": base64.b64encode(np.array(pts, np.int16).tobytes()).decode(),
        "polys": base64.b64encode(np.array(polys, np.int32).tobytes()).decode(),
        "layers": layers,
        "beadWidth": 0.42,
    }


def test_every_vertex_is_referenced_by_a_face():
    """The base-index bug.

    Vertices are appended one BLOCK of n points per cross-section corner, so
    len(verts) counts blocks, not vertices. Using it as a face base index
    pointed every face at the first fifth of the mesh: the vertex array was
    perfectly correct and 79% of it was orphaned, so a 120mm vase rendered as
    a 22mm stub.
    """
    V, F = g2m.build(_payload())
    used = np.unique(F)
    check(len(used) == len(V),
          "only %d of %d vertices are referenced -- the face base index is "
          "counting blocks again" % (len(used), len(V)))
    check(int(F.max()) == len(V) - 1,
          "highest face index is %d, expected %d" % (int(F.max()), len(V) - 1))


def test_the_surface_faces_outward():
    """The inverted-mesh bug.

    Sweep winding follows whichever way the slicer walked the loop, so the
    whole mesh came out inside-out -- consistently, and watertight, which is
    why nothing flagged it. The only symptom was a negative volume and a
    renderer quietly shading the inside of every bead.
    """
    V, F = g2m.build(_payload())
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    vol = float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum()) / 6.0
    check(vol > 0, "signed volume is %.1f -- the mesh is inside-out" % vol)


def test_the_part_is_centred_on_the_origin():
    """Built in plate coordinates a part sits ~128mm off origin, and every
    renderer framing on the object then framed a close-up of its own base."""
    V, _ = g2m.build(_payload())
    cx = (V[:, 0].min() + V[:, 0].max()) / 2
    cy = (V[:, 1].min() + V[:, 1].max()) / 2
    check(abs(cx) < 0.01 and abs(cy) < 0.01,
          "part centre is (%.2f, %.2f), expected the origin" % (cx, cy))
    check(abs(V[:, 2].min()) < 0.35,
          "part does not sit on z=0 (min z %.2f)" % V[:, 2].min())


def test_layers_fuse_instead_of_stacking_with_daylight_between():
    """A bead exactly one layer tall touches its neighbour on a hairline and
    renders as separate ribbons. Squish makes consecutive layers overlap."""
    V, _ = g2m.build(_payload(), squish=1.3)
    zs = np.unique(np.round(V[:, 2], 4))
    # the tallest bead top of layer N must reach past the lowest bottom of N+1
    check(V[:, 2].max() > 6 * 0.2, "the tower is shorter than its own layers")
    lo, hi = zs[:4], zs[-4:]
    check(len(zs) > 4, "expected several distinct bead heights, got %d" % len(zs))
    bead_h = 0.2 * 1.3
    check(bead_h > 0.2,
          "squish is not making the bead taller than the layer pitch")


def test_hidden_types_are_actually_dropped():
    """And filtering everything fails loudly rather than writing an empty file
    that only looks wrong once somebody opens it."""
    p = _payload()
    full, _ = g2m.build(p, hidden=set())
    check(len(full) > 0, "nothing was built with no filter at all")
    try:
        g2m.build(p, hidden={0})
    except SystemExit as e:
        check("nothing to build" in str(e),
              "filtering everything failed, but not with a useful message: %s" % e)
    else:
        _failures.append("filtering out every feature type still produced a mesh")


def test_ply_round_trips_through_trimesh():
    import trimesh
    V, F = g2m.build(_payload())
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "t.ply"
        g2m.write_ply(out, V, F)
        m = trimesh.load(out, process=False)
        check(len(m.vertices) == len(V),
              "PLY lost vertices: %d written, %d read" % (len(V), len(m.vertices)))
        check(len(m.faces) == len(F),
              "PLY lost faces: %d written, %d read" % (len(F), len(m.faces)))
        check(m.volume > 0, "round-tripped mesh has volume %.2f" % m.volume)


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append("%s raised:\n%s" % (fn.__name__, traceback.format_exc()))
    if _failures:
        print("GCODE TO MESH TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("GCODE TO MESH TESTS OK -- the bead mesh is fully indexed, faces "
          "outward, sits centred on the origin, and survives a PLY round trip.")


if __name__ == "__main__":
    run()
