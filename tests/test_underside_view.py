"""
tools/underside_view.py reads bed-face text the way a buyer does (Brief A, 2026-11-14).

Calibrates the OBC verdicts against marks whose answer is known (the library mark, the
same turned 180 degrees, and plain text), then pins the three fixes the audit made:
the Label Tile reads PARTS from below, the Love Monster's back mark and the Day Pods
lids are no longer mirrored, and the Monogram Keychain stays readable turned side to side.

Run: python tests/test_underside_view.py
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import underside_view as uv  # noqa: E402

LIB = ROOT / "openscad_models" / "brand" / "obc_mark.scad"
_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _mark(transform: str) -> list[str]:
    with tempfile.TemporaryDirectory() as td:
        src, stl = Path(td) / "m.scad", Path(td) / "m.stl"
        src.write_text(f"include <{LIB}>\n{transform} obc_inlay(6);\n")
        env = dict(os.environ, OPENSCADPATH=str(ROOT / "assets" / "openscad_libs"))
        subprocess.run(["openscad", "-o", str(stl), str(src)], capture_output=True, env=env, timeout=300)
        return [m["verdict"] for m in uv.obc_marks(str(stl))]


def test_calibration():
    check(_mark("") == ["correct"], f"library mark should read correct, got {_mark('')}")
    rot = "mirror([1, 0, 0]) mirror([0, 1, 0])"
    check(_mark(rot) == ["upside down"], f"turned 180 should read upside down, got {_mark(rot)}")
    plain = "mirror([0, 1, 0])"          # undoes the library's mirror: plain text
    check(_mark(plain) == ["mirrored"], f"plain text should read mirrored, got {_mark(plain)}")


def test_label_tile_reads_parts_from_below():
    import numpy as np
    m = uv.load_parts(ROOT / "openscad_models" / "label_tile_text.stl")[0]
    p2, _ = m.section(plane_origin=[0, 0, 0.3], plane_normal=[0, 0, 1]).to_2D(to_2D=np.eye(4))
    holes = [len(g.interiors) for g in sorted(p2.polygons_full, key=lambda g: g.centroid.x)]
    # seen from ABOVE, mirrored text runs S T R A P: no holes, no holes, then R A P
    check(holes == [0, 0, 1, 1, 1], f"Label Tile text from above should run S-T-R-A-P, holes {holes}")


def test_fixed_marks_not_mirrored():
    for rel in ["openscad_models/valentine_2027/mailboxes/love_monster/love_monster_body.3mf",
                "openscad_models/monogram_keychain_J.3mf"]:
        vs = {m["verdict"] for m in uv.obc_marks(ROOT / rel)}
        check(vs and "mirrored" not in vs, f"{rel}: OBC mark verdicts {vs}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("UNDERSIDE VIEW TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("UNDERSIDE VIEW TESTS OK — the bed-face reader is calibrated and the Brief A fixes hold.")


if __name__ == "__main__":
    run()
