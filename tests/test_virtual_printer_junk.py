"""tools/virtual_printer.py never hands back a slice with junk coordinates.

2026-09-27: on four-filament plates PrusaSlicer 2.7 intermittently wrote moves
like X-877672384 into the wipe-tower tool changes -- 4,153 in one post office
slice, none in the next with identical options. A printer given that file would
try to travel 877 km. slice_model now re-slices on junk and refuses after three
tries. A stand-in slicer that writes junk a set number of times proves both.
"""
import os
import sys
import tempfile
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import virtual_printer as vp  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_slicer(td, junk_runs):
    cnt = td / "n"
    cnt.write_text("0")
    fake = td / "prusa-slicer"
    fake.write_text(f"""#!/bin/sh
n=$(cat {cnt}); n=$((n+1)); echo $n > {cnt}
out=""; while [ $# -gt 0 ]; do [ "$1" = "-o" ] && out=$2; shift; done
if [ $n -le {junk_runs} ]; then printf 'G1 X-877672384.000 Y164.5\\n' > "$out"; else printf 'G1 X10 Y10\\n' > "$out"; fi
""")
    fake.chmod(0o755)
    (td / "m.stl").write_text("solid x\nendsolid x\n")
    return cnt


def _with_fake(junk_runs):
    td = Path(tempfile.mkdtemp(prefix="vp_junk_"))
    cnt = _fake_slicer(td, junk_runs)
    old = os.environ["PATH"]
    os.environ["PATH"] = f"{td}:{old}"
    # Pinned: with Bambu Studio installed, slice_model would prefer it and
    # never run the fake PrusaSlicer on PATH.
    os.environ["VIRTUAL_PRINTER_SLICER"] = "prusa"
    try:
        try:
            vp.slice_model(td / "m.stl", td / "o.gcode")
            err = None
        except vp.VirtualPrinterError as e:
            err = e
    finally:
        os.environ["PATH"] = old
        os.environ.pop("VIRTUAL_PRINTER_SLICER", None)
    return int(cnt.read_text()), td / "o.gcode", err


def test_the_bambu_path_is_guarded_the_same_way():
    """The retry-and-refuse sits in slice_model, not in either slicer's runner,
    so Bambu Studio output gets it too."""
    import bambu_slicer
    td = Path(tempfile.mkdtemp(prefix="vp_junk_bambu_"))
    (td / "m.stl").write_text("solid x\nendsolid x\n")
    calls = []

    def fake(model, gcode, **kw):
        calls.append(1)
        Path(gcode).write_text("G1 X-877672384.000 Y164.5\n" if len(calls) < 3 else "G1 X10 Y10\n")

    os.environ["VIRTUAL_PRINTER_SLICER"] = "bambu"
    try:
        with patch.object(bambu_slicer, "slice_model", fake):
            vp.slice_model(td / "m.stl", td / "o.gcode")
    finally:
        os.environ.pop("VIRTUAL_PRINTER_SLICER", None)
    check(len(calls) == 3, f"two junk Bambu slices then a clean one: expected 3 runs, got {len(calls)}")
    check(vp.off_bed_moves(td / "o.gcode") == 0, "the returned Bambu G-code must be clean")


def test_a_junk_slice_is_retried_until_clean():
    runs, out, err = _with_fake(2)
    check(err is None, f"two junk runs then a clean one must succeed, got {err}")
    check(runs == 3, f"expected 3 slicer runs, got {runs}")
    check(vp.off_bed_moves(out) == 0, "the returned G-code must have no off-bed moves")


def test_persistent_junk_is_refused():
    runs, _, err = _with_fake(99)
    check(err is not None and "off-bed" in str(err), f"junk on every try must raise, got {err!r}")
    check(runs == 3, f"it must give up after 3 tries, ran {runs}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("VIRTUAL PRINTER JUNK TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIRTUAL PRINTER JUNK TESTS OK — a slice with off-bed moves is re-sliced, "
          "and refused after three tries; it is never returned.")


if __name__ == "__main__":
    run()
