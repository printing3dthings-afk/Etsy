"""
Tests for tools/assemble_3mf.py (2026-09-09).

Scott's rule: parts that go together ship as ONE print-ready file; a container
and its lid stay separate parts but on one plate.

The reason this tool exists is a silent failure worth pinning. OpenSCAD's own
3MF export MERGES every body into a single object with no materials -- verified
on a real export: 1 object, 1 item, 0 basematerials, 20,065 fused triangles.
That file opens fine and slices fine, and no filament can be assigned to any
part of it. A merged 3MF is indistinguishable from a good one unless something
actually counts the parts, which is what these tests do.
"""
import sys
import zipfile
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import assemble_3mf  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _cube(n, size, out_dir):
    m = trimesh.creation.box(extents=[size, size, size])
    p = Path(out_dir) / f"{n}.stl"
    m.export(str(p))
    return p


def _counts(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("3D/3dmodel.model").decode()
        cfg = z.read("Metadata/Slic3r_PE_model.config").decode()
    return {"object": xml.count("<object "), "item": xml.count("<item "),
            "volume": cfg.count("<volume ")}


def _parts_per_object(path):
    """How a PrusaSlicer-family slicer will actually list the parts."""
    import re
    with zipfile.ZipFile(path) as z:
        cfg = z.read("Metadata/Slic3r_PE_model.config").decode()
    out = []
    for _, body in re.findall(r'<object id="(\d+)"[^>]*>(.*?)</object>', cfg, re.S):
        out.append(re.findall(r'<volume[^>]*>.*?key="name" value="([^"]+)"', body, re.S))
    return out


def test_assembly_is_one_object_with_named_volumes():
    """Parts that go together: ONE object, parts declared as triangle ranges.

    A <components> assembly looks right and is not: PrusaSlicer flattens it into
    N separate objects, so the slicer offers N things to arrange instead of one
    object with N colourable parts. Verified on the real 5-part dumpling clicker
    -- it came back "objects: 5, components: 0, items: 5".
    """
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        parts = [(_cube("a", 10, td), "#111111"), (_cube("b", 8, td), "#222222")]
        out = Path(td) / "asm.3mf"
        assemble_3mf.assemble(out, [parts], "assembly")
        c = _counts(out)
        check(c["object"] == 1, f"assembly must be ONE object, got {c['object']}")
        check(c["item"] == 1, f"assembly must be ONE item, got {c['item']}")
        check(c["volume"] == 2, f"parts must be volumes, got {c['volume']}")
        check(_parts_per_object(out) == [["a", "b"]],
              f"parts must be named: {_parts_per_object(out)}")


def test_plate_is_separate_objects():
    """A container and its lid: two independent items, not one assembly."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        g1 = [(_cube("base", 20, td), "#111111")]
        g2 = [(_cube("lid", 18, td), "#222222")]
        out = Path(td) / "plate.3mf"
        assemble_3mf.assemble(out, [g1, g2], "plate")
        c = _counts(out)
        check(c["item"] == 2, f"plate must have one item per object, got {c['item']}")
        check(c["object"] == 2, f"plate must have one object per group, got {c['object']}")


def test_plated_objects_do_not_overlap():
    """Laid out with a real gap -- stacked on the origin is not 'arranged'."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        g1 = [(_cube("base", 20, td), "#111111")]
        g2 = [(_cube("lid", 20, td), "#222222")]
        out = Path(td) / "plate.3mf"
        assemble_3mf.assemble(out, [g1, g2], "plate", gap=6.0)
        sc = trimesh.load(str(out))
        # WORLD bounds, via the scene graph. A geometry's own .bounds are LOCAL
        # -- the 3MF item transform lives on the graph node, so comparing
        # g.bounds directly makes every object look stacked on the origin and
        # this test fail against a perfectly good file.
        xs = []
        for node in sc.graph.nodes_geometry:
            T, gname = sc.graph[node]
            world = trimesh.transform_points(sc.geometry[gname].bounds, T)
            xs.append((world[:, 0].min(), world[:, 0].max()))
        lo, hi = sorted(xs)
        check(lo[1] <= hi[0] + 1e-6,
              f"plated objects overlap in X: {lo} vs {hi}")


def test_a_plate_entry_may_itself_be_multipart():
    """The dumpling clicker: a 4-colour bun plus a separate basket."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        bun = [(_cube("bun", 20, td), "#111111"), (_cube("eyes", 4, td), "#000000")]
        basket = [(_cube("basket", 24, td), "#333333")]
        out = Path(td) / "plate.3mf"
        assemble_3mf.assemble(out, [bun, basket], "plate")
        check(c := _parts_per_object(out),
              "no parts listed at all")
        check(len(c) == 2, f"expected 2 objects on the plate, got {len(c)}")
        check(len(c[0]) == 2, f"the bun must keep its 2 parts, got {c[0]}")


def test_the_shipped_files_really_kept_their_parts():
    """The whole point. A merged 3MF slices fine and is silently useless."""
    # monogram_keychain_J went 4 -> 5 parts in 74c6837, which added the `mark`
    # part (the standing maker's-mark rule). The model was right and this
    # expectation was simply never updated, so the suite has been red since
    # 2026-09-09. Verified against the .scad's own part list before changing it:
    # ring, rotor, halo, letter, mark.
    for name, want in (("monogram_keychain_J", [5]), ("dumpling_clicker", [4, 1]),
                       ("snap_box", [1, 3])):
        f = ROOT / "openscad_models" / f"{name}.3mf"
        if not f.exists():
            continue
        got = [len(v) for v in _parts_per_object(f)]
        check(got == want, f"{name}.3mf lists parts per object as {got}, expected "
                           f"{want} -- a slicer can only colour what it lists")


def test_part_names_are_readable():
    """A prefix strip that cuts mid-word turned bao/bao_eyes/basket into
    "o"/"o_eyes"/"sket". Names are how a part is picked for recolouring."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        g1 = [(_cube("widget_bao", 10, td), "#111111"),
              (_cube("widget_bao_eyes", 4, td), "#222222")]
        g2 = [(_cube("widget_basket", 12, td), "#333333")]
        out = Path(td) / "n.3mf"
        assemble_3mf.assemble(out, [g1, g2], "plate")
        names = [n for grp in _parts_per_object(out) for n in grp]
        check(all("_" not in n[:1] and len(n) > 2 for n in names),
              f"part names look truncated: {names}")
        check("bao" in names and "basket" in names,
              f"expected whole words, got {names}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("ASSEMBLE 3MF TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("ASSEMBLE 3MF TESTS OK -- assembled parts are ONE object with named "
          "volumes (not components, which a slicer flattens into loose objects), "
          "a container and lid stay separate objects on one plate without "
          "overlapping, and every shipped 3MF lists the parts a slicer can colour.")


if __name__ == "__main__":
    run()
