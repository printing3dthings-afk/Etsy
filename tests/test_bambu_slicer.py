"""Tests for tools/bambu_slicer.py and the Bambu path through the print checks
(2026-09-27).

Every case here is a failure that returned "Success" and looked like a normal
slice. Each was found while switching the checks from PrusaSlicer to Bambu
Studio, and each would have made the checks report on something other than
what Scott prints:
  * the CLI ignores a preset's `inherits`: the stock P1S sliced on a 200 mm bed;
  * `include` holds the P1S's real start G-code: without it, a generic one;
  * no filament_colour: filament 2's parts left out, the plate half its height;
  * a single-mesh 3MF: Bambu reads one part, the chapel all one colour;
  * extruder_offset 0x2: every Y 2 mm off, walls read as misses;
  * T255/T1000 read as filaments: a one-colour block 2,080 mm3 "wrong colour";
  * the first T indented: the chapel's first layer read as the wrong slot.
The last test slices for real when Bambu Studio is installed.
"""
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import assemble_3mf  # noqa: E402
import bambu_slicer as bs  # noqa: E402
import print_fidelity as pf  # noqa: E402
import virtual_printer as vp  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


BAMBU_GCODE = """; HEADER_BLOCK_START
; extruder_offset = 0x2
G90
M620 S2A
    T2
M621 S2A
T1000
; CHANGE_LAYER
; Z_HEIGHT: 0.2
; LAYER_HEIGHT: 0.2
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 X10 Y10 F3000
M83
G1 X20 Y10 E1.0
G1 X20 Y20 E1.0
; FEATURE: Floating vertical shell
G1 X25 Y20 E0.5
G91
G1 Y5 F1200
G90
; FEATURE: Some future feature
G1 X30 Y30 E0.2
M620 S255
T255
"""


def _translated():
    td = Path(tempfile.mkdtemp(prefix="bambu_tr_"))
    (td / "b.gcode").write_text(BAMBU_GCODE)
    bs.translate_gcode(td / "b.gcode", td / "p.gcode",
                       offset=bs.extruder_offset(td / "b.gcode"))
    return (td / "p.gcode").read_text(), td / "p.gcode"


def test_comment_dialect_becomes_prusaslicers():
    text, _ = _translated()
    for want in (";LAYER_CHANGE", ";Z:0.2", ";HEIGHT:0.2", ";TYPE:External perimeter",
                 ";WIDTH:0.42", ";TYPE:Solid infill", ";TYPE:Some future feature"):
        check(want in text, f"translated G-code is missing {want!r}")
    check("; FEATURE:" not in text and "; CHANGE_LAYER" not in text,
          "Bambu comments left untranslated")


def test_absolute_moves_shift_into_plate_coordinates_and_relative_ones_do_not():
    text, _ = _translated()
    check("G1 X10.000 Y12.000" in text, "absolute Y must move by the 2 mm extruder_offset")
    check("G1 Y5 F1200" in text, "a G91 relative move must not be shifted")
    plain = Path(tempfile.mkdtemp(prefix="bambu_tr_")) / "plain.gcode"
    plain.write_text("G1 X1 Y1\n")
    check(bs.extruder_offset(plain) == (0.0, 0.0), "a file with no extruder_offset means no shift")


def test_control_t_codes_are_not_filaments_and_the_indented_first_t_is():
    text, path = _translated()
    check("\nT2\n" in text, "the indented first T must reach column 0")
    check("\nT1000\n" not in text and "\nT255\n" not in text,
          "T1000/T255 must not be left as tool changes")
    layers = pf.parse_gcode(path)
    tools = {t for L in layers for (t, _w) in L["beads"]}
    check(tools == {2}, f"every bead was laid by slot 2, parse saw tools {tools}")


def _profiles(td):
    for kind in ("machine", "process", "filament"):
        (td / kind).mkdir(parents=True, exist_ok=True)
    (td / "machine" / "base.json").write_text(json.dumps(
        {"name": "base", "printable_area": ["0x0", "200x0", "200x200", "0x200"],
         "machine_start_gcode": "GENERIC", "nozzle": "base"}))
    (td / "machine" / "tpl.json").write_text(json.dumps(
        {"name": "tpl", "instantiation": "false", "machine_start_gcode": "P1S REAL",
         "nozzle": "from include"}))
    (td / "machine" / "P1S.json").write_text(json.dumps(
        {"name": "P1S", "inherits": "base", "include": ["tpl"], "from": "system",
         "printable_area": ["0x0", "256x0", "256x256", "0x256"], "nozzle": "own"}))
    return td


def test_flatten_follows_inherits_and_include_and_keeps_the_presets_own_values():
    td = _profiles(Path(tempfile.mkdtemp(prefix="bambu_prof_")))
    m = bs.flatten_preset(td, "machine", "P1S")
    check(m["printable_area"][2] == "256x256", f"child must override parent: {m['printable_area']}")
    check(m["machine_start_gcode"] == "P1S REAL", "the included template must replace the generic start G-code")
    check(m["nozzle"] == "own", "a key the preset sets itself must beat its include")
    check(m["name"] == "P1S" and m["from"] == "system", "name/from must stay the preset's own")
    check("inherits" not in m and "include" not in m, "flattened preset must not point anywhere")


def test_flatten_refuses_a_missing_parent():
    td = _profiles(Path(tempfile.mkdtemp(prefix="bambu_prof_")))
    (td / "machine" / "orphan.json").write_text(json.dumps({"name": "orphan", "inherits": "nope"}))
    try:
        bs.flatten_preset(td, "machine", "orphan")
        check(False, "a broken inherits chain must raise, not slice on defaults")
    except bs.BambuSlicerError:
        pass


def _two_cubes(td):
    a = trimesh.creation.box(extents=[20, 20, 10]); a.apply_translation([0, 0, 5])
    b = trimesh.creation.box(extents=[20, 20, 10]); b.apply_translation([0, 0, 15])
    pa, pb = td / "two_a.stl", td / "two_b.stl"
    a.export(str(pa)); b.export(str(pb))
    return [(pa, "#77716B"), (pb, "#2B2F38")]


def test_bambu_layout_names_each_part_by_its_component_object():
    td = Path(tempfile.mkdtemp(prefix="bambu_asm_"))
    out = td / "two.3mf"
    r = assemble_3mf.assemble(out, [_two_cubes(td)], "assembly", layout="bambu")
    with zipfile.ZipFile(out) as z:
        model = z.read("3D/3dmodel.model").decode()
        cfg = z.read("Metadata/model_settings.config").decode()
        names = z.namelist()
    check(model.count("<component ") == 2, "the parent object must hold one component per part")
    check('<part id="1"' in cfg and '<part id="2"' in cfg,
          "model_settings parts must use the component objects' ids")
    check('key="extruder" value="2"' in cfg, "the second part must carry filament 2")
    check("Metadata/Slic3r_PE_model.config" not in names,
          "the Bambu layout must not carry triangle ranges that no longer match")
    check(bs.filament_count(out) == 2 and r["slicer_layout"] == "bambu",
          f"filament_count read {bs.filament_count(out)}")
    check(bs.filament_count(td / "two_a.stl") == 1, "a mesh needs one filament")


def test_the_prusa_layout_is_unchanged_by_default():
    td = Path(tempfile.mkdtemp(prefix="bambu_asm_"))
    out = td / "two.3mf"
    assemble_3mf.assemble(out, [_two_cubes(td)], "assembly")
    with zipfile.ZipFile(out) as z:
        check("<component " not in z.read("3D/3dmodel.model").decode(),
              "default layout must stay the single mesh PrusaSlicer reads")
        check("Metadata/Slic3r_PE_model.config" in z.namelist(), "default must keep triangle ranges")


def test_slicer_choice_can_be_pinned():
    for want in ("prusa", "bambu"):
        os.environ["VIRTUAL_PRINTER_SLICER"] = want
        try:
            check(vp.active_slicer() == want, f"VIRTUAL_PRINTER_SLICER={want} ignored")
        finally:
            os.environ.pop("VIRTUAL_PRINTER_SLICER", None)


def test_an_option_bambu_cannot_honour_is_refused_not_dropped():
    td = Path(tempfile.mkdtemp(prefix="bambu_opt_"))
    (td / "m.stl").write_text("solid x\nendsolid x\n")
    os.environ["VIRTUAL_PRINTER_SLICER"] = "bambu"
    try:
        vp.slice_model(td / "m.stl", td / "o.gcode", extra={"fuzzy-skin": "all"})
        check(False, "an unmapped option must raise")
    except vp.VirtualPrinterError as e:
        check("fuzzy-skin" in str(e), f"the error must name the option: {e}")
    finally:
        os.environ.pop("VIRTUAL_PRINTER_SLICER", None)


def test_analyse_counts_relative_extrusion():
    td = Path(tempfile.mkdtemp(prefix="bambu_an_"))
    g = td / "r.gcode"
    g.write_text("M83\n;LAYER_CHANGE\n;TYPE:Perimeter\nG1 X1 Y0 Z0.2 E1.0\n"
                 "G1 X2 Y0 E1.0\nG1 X3 Y0 E1.0\n")
    a = vp.analyse(g)
    check(abs(a["filament_mm"] - 3.0) < 1e-6,
          f"three relative pushes of 1 mm are 3 mm of filament, analyse read {a['filament_mm']}")
    check(a["moves_by_type"].get("Perimeter") == 3, f"all three moves extrude: {a['moves_by_type']}")


def test_a_real_two_colour_slice_keeps_both_parts():
    """Slices for real. Without per-slot colours the second cube was left out
    and the plate came back 10 mm tall on one filament."""
    if not bs.available():
        print("  (skipped real slice: Bambu Studio not installed)")
        return
    td = Path(tempfile.mkdtemp(prefix="bambu_real_"))
    src = td / "two.3mf"
    parts = _two_cubes(td)
    assemble_3mf.assemble(src, [parts], "assembly", layout="bambu")
    res = bs.slice_model(src, td / "two.gcode", colours=[c for _, c in parts])
    fil = res["sliced_plates"][0]["filaments"]
    check(len([f for f in fil if f["total_used_g"] > 0]) == 2,
          f"both filaments must be used: {fil}")
    a = vp.analyse(td / "two.gcode", model_height=20.0)
    check(not a["geometry_dropped"], f"the plate must reach 20 mm, reached {a['printed_height_mm']}")
    raw = (td / "two.bambu.gcode").read_text(errors="replace")
    check("printable_area = 0x0,256x0,256x256,0x256" in raw, "the P1S bed must be 256 x 256")
    check("machine: P1S" in raw, "the P1S's own start G-code must be in the file")
    check(vp.slicer_of(td / "two.gcode") == "bambu", "the header must name Bambu Studio")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("BAMBU SLICER TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("BAMBU SLICER TESTS OK — presets are flattened, parts reach their filaments, "
          "and the G-code is read in plate coordinates on the right slots.")


if __name__ == "__main__":
    run()
