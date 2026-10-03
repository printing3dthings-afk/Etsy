"""tools/print_fidelity.py against a block with known answers (2026-09-27).

The block carries features either side of what the P1S's slicer can make: ribs
0.05-0.2 mm wide, dots 0.3-1.0 mm across. Each assertion is a measured slicer
decision, checked by drawing the toolpath over the model section, not a guess:
Arachne walls print a 0.15 mm rib as one narrow bead and drop a 0.1 mm one,
and a 1.0 mm dot prints where a 0.5 mm one does not.

Two of the assertions pin bugs found in the tool itself while calibrating:
  * an opening filter meant to remove slivers deleted every miss under 0.1 mm
    wide, so a fully dropped 0.05 mm rib reported nothing;
  * aligning print to model by their outer bounds shifted the model toward a
    thin rib that printed short, and every wall on that side read as a miss.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import print_fidelity as pf  # noqa: E402

_failures: list[str] = []

SCAD = """
Wf = [0.05, 0.1, 0.15, 0.2];
D  = [0.3, 0.5, 1.0];
union() {
  cube([60, 10, 8]);
  for (i=[0:3]) translate([6+i*14, -1, 1]) cube([Wf[i], 1.01, 6]);
  for (i=[0:2]) translate([6+i*14, 3, 7.99]) cylinder(d=D[i], h=0.41, $fn=24);
}
"""
RIB_X = {0.05: 6, 0.1: 20, 0.15: 34, 0.2: 48}
DOT_X = {0.3: 6, 0.5: 20, 1.0: 34}


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# What each slicer actually does with the block -- measured, each one drawn
# with --zoom over the model section, not assumed from the other:
#   prusa  PrusaSlicer 2.7, Arachne walls: a 0.15 mm rib prints as one narrow
#          bead and a 0.1 mm one does not; a 1.0 mm dot prints, 0.5 does not.
#   bambu  Bambu Studio 02.08.02.61, stock P1S 0.20mm Standard, CLASSIC walls
#          (2026-09-27): no rib up to 0.2 mm gets a bead at all, but a 0.5 mm
#          dot does (a short gap-fill squiggle); 0.3 mm does not.
EXPECT = {
    "prusa": {"ribs_printed": {0.15, 0.2}, "dots_printed": {1.0}},
    "bambu": {"ribs_printed": set(), "dots_printed": {0.5, 1.0}},
}


def _slicers():
    import bambu_slicer
    out = []
    if shutil.which("prusa-slicer") or shutil.which("prusa-slicer-console"):
        out.append("prusa")
    if bambu_slicer.available():
        out.append("bambu")
    return out


def _run(slicer):
    td = Path(tempfile.mkdtemp(prefix=f"fidelity_test_{slicer}_"))
    (td / "b.scad").write_text(SCAD)
    subprocess.run(["openscad", "-o", str(td / "b.stl"), str(td / "b.scad")],
                   check=True, capture_output=True)
    old = os.environ.get("VIRTUAL_PRINTER_SLICER")
    os.environ["VIRTUAL_PRINTER_SLICER"] = slicer
    try:
        rep, _ = pf.compare([(str(td / "b.stl"), "#999999")], td, log=lambda *a: None)
    finally:
        if old is None:
            os.environ.pop("VIRTUAL_PRINTER_SLICER")
        else:
            os.environ["VIRTUAL_PRINTER_SLICER"] = old
    return rep


def _dropped_near(rep, x, zlo, zhi, tol=2.0):
    return sum(c["volume_mm3"] for c in rep["clusters"]
               if c["kind"] == "dropped" and abs(c["at_xy"][0] - x) < tol
               and c["z_mm"][0] >= zlo - 0.01 and c["z_mm"][1] <= zhi + 0.01)


def test_thin_ribs_and_small_dots_are_reported_and_printable_ones_are_not():
    slicers = _slicers() if shutil.which("openscad") else []
    if not slicers:
        print("  (skipped: openscad or both slicers missing)")
        return
    for slicer in slicers:
        _check_block(slicer, _run(slicer))


def _check_block(slicer, rep):
    exp = EXPECT[slicer]
    check(rep["slicer"] == slicer, f"asked for {slicer}, report says {rep['slicer']}")
    rib_vol = {w: w * 1.0 * 6.0 for w in RIB_X}          # width x 1 proud x 6 tall
    for w, x in RIB_X.items():
        got = _dropped_near(rep, x, 1.0, 7.0)
        if w not in exp["ribs_printed"]:
            check(got > 0.8 * rib_vol[w],
                  f"[{slicer}] a {w} mm rib does not print, so most of its {rib_vol[w]:.2f} mm3 "
                  f"must be reported dropped; got {got:.3f}")
        else:
            check(got < 0.2 * rib_vol[w],
                  f"[{slicer}] a {w} mm rib prints as a narrow bead; {got:.3f} mm3 reported dropped")
    for d, x in DOT_X.items():
        got = _dropped_near(rep, x, 8.0, 8.4)
        if d not in exp["dots_printed"]:
            check(got > 0.0, f"[{slicer}] a {d} mm dot is not printed and must be reported")
        else:
            check(got == 0.0, f"[{slicer}] a {d} mm dot prints; {got:.3f} mm3 reported dropped")
    # A dot that vanishes is detail you can see, and must be FLAGGED, not just
    # listed. A dropped 0.1 mm rib is listed above but not flagged: it is a
    # hairline, below what a render shows or an eye sees on the part.
    for d, x in DOT_X.items():
        if d not in exp["dots_printed"]:
            flagged = [c for c in rep["clusters"] if c["flag"] and abs(c["at_xy"][0] - x) < 2
                       and c["kind"] == "dropped"]
            check(flagged, f"[{slicer}] the {d} mm dot vanishes from the print and must be flagged")
    # The main walls print true. A shifted alignment made the whole front read
    # as tens of mm3 dropped -- on Bambu Studio, a 2 mm extruder_offset did
    # exactly that until the G-code was moved into plate coordinates.
    walls = sum(c["volume_mm3"] for c in rep["clusters"]
                if abs(c["at_xy"][1] - 0) < 0.3 and all(abs(c["at_xy"][0] - x) > 2 for x in RIB_X.values()))
    check(walls < 0.1, f"[{slicer}] the plain front wall must not read as a miss; got {walls:.3f} mm3")
    # Every bead is in the one filament. Bambu's T255/T1000 control codes read
    # as tool changes put the whole block in the "wrong colour" (2,080 mm3).
    check(rep.get("colour_mm3", 0) == 0,
          f"[{slicer}] a one-colour model printed {rep.get('colour_mm3')} mm3 in another filament")


def _box(x0, y0, x1, y1, z1=4.0):
    import trimesh
    b = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, z1 / 2])
    return b


def test_section_keeps_loops_that_touch_at_a_corner():
    """The post office's parcel top: three quadrants meeting at one corner.
    trimesh's Path2D alone returned two of them, and the check reported the
    printed third as 12 mm3 of material that was never modelled."""
    import trimesh
    m = trimesh.util.concatenate([_box(0, 0, 3, 3), _box(3, 3, 6, 6), _box(0, 3, 3, 6)])
    got = pf.section(m, 2.0)
    check(abs(got.area - 27.0) < 0.05, f"three 3x3 squares must section to 27 mm2, got {got.area:.2f}")


def test_section_keeps_a_thin_rib_joined_to_its_wall():
    """A 0.05 mm rib fused to a wall by OpenSCAD: GEOS build_area alone
    dropped it at z=3.19 and kept it at 3.01 and 3.21. Built from the real
    OpenSCAD mesh, because a hand-made pair of boxes does not reproduce it."""
    if not shutil.which("openscad"):
        return
    from shapely.geometry import box
    td = Path(tempfile.mkdtemp(prefix="fidelity_rib_"))
    (td / "b.scad").write_text(SCAD)
    subprocess.run(["openscad", "-o", str(td / "b.stl"), str(td / "b.scad")],
                   check=True, capture_output=True)
    m = pf._load(td / "b.stl")
    for z in (3.01, 3.19, 3.21):
        a = pf.section(m, z).intersection(box(5.9, -1.1, 6.1, 0)).area
        check(abs(a - 0.05) < 0.005, f"rib missing from the section at z={z}: {a:.4f} mm2 of 0.05")

def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PRINT FIDELITY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRINT FIDELITY TESTS OK — on every installed slicer, the ribs and dots it "
          "drops are reported and flagged, the ones it prints are not, and the plain "
          "walls read true.")


if __name__ == "__main__":
    run()
