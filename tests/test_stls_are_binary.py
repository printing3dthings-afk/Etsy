"""Every committed STL is binary (2026-10-29).

283 ASCII STLs once cost this repo 1.0 GB, and binary is the same triangles in
a fifth of the space. The pre-commit hook (.githooks/pre-commit) converts them
as they are staged; this catches one that got in without it, e.g. a clone
where the hook was never switched on. data/trash/ is exempt: its copies are
byte-exact for --restore. Also checks the converter on a real ASCII file:
same facets, same order, a fifth of the size.
"""
import subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import stl_binary  # noqa: E402

_failures: list[str] = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


def test_no_tracked_ascii_stl():
    bad = [f for f in stl_binary.tracked_stls() if f.exists() and stl_binary.is_ascii(f)]
    check(not bad, f"{len(bad)} ASCII STLs committed, run tools/stl_binary.py --tracked: "
                   + ", ".join(str(f.relative_to(ROOT)) for f in bad[:5]))


def test_converter_keeps_every_facet():
    src = (b"solid t\n" + b"".join(
        b"facet normal 0 0 %d\nouter loop\nvertex %d 0 0\nvertex 1.5 %d 0\nvertex 0 1 123.456\nendloop\nendfacet\n"
        % (1 - 2 * (i % 2), i, i) for i in range(5)) + b"endsolid t\n")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "t.stl"
        p.write_bytes(src)
        check(stl_binary.is_ascii(p), "the ASCII sample was not recognised as ASCII")
        msg = stl_binary.convert(p)
        check(msg.startswith("ok"), f"conversion refused: {msg}")
        check(not stl_binary.is_ascii(p), "still ASCII after conversion")
        v = stl_binary.read_binary(p)
        check(v.shape == (5, 12), f"expected 5 facets, got {v.shape}")
        check(list(v[:, 3]) == [0, 1, 2, 3, 4], f"facet order changed: {v[:, 3]}")
        check(list(v[:, 2]) == [1, -1, 1, -1, 1], f"normals changed: {v[:, 2]}")
        check(abs(v[0, 11] - 123.456) < 1e-4, f"coordinate drifted: {v[0, 11]}")


def run():
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("STL BINARY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("STL BINARY TESTS OK -- no ASCII STL is committed, and the converter keeps every facet, its order and its normal.")


if __name__ == "__main__":
    run()
