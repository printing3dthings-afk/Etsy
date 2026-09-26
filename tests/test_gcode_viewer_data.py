#!/usr/bin/env python3
"""Regression tests for tools/gcode_viewer_data.py.

Grounded in the two real defects found while building the print viewer, not
in generic coverage:

  * `build_job`'s `name` parameter was shadowed by a loop variable added for
    the speed summary, so every job in index.js was labelled with the last
    feature type iterated ("Top solid infill"). Nothing in the Python output
    looked wrong -- it only surfaced as the wrong text in a browser.
  * Layer Z must come from the slicer's own ;Z: comment. Tracking G1 Z
    instead picks up the Z-hop on a travel move and reports a layer higher
    than it is.
"""
import base64
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import gcode_viewer_data as gvd  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# Two layers. Layer 1 lays a square external perimeter at F1800 (30 mm/s) and
# one infill pass at F4800 (80 mm/s); a Z-hop travel sits between them, which
# is exactly the move that used to corrupt the reported layer height.
FIXTURE = """\
;TYPE:Custom
G1 Z5 F5000 ; lift nozzle
M83
;LAYER_CHANGE
;Z:0.2
;HEIGHT:0.2
;TYPE:External perimeter
G1 X10 Y10 F9000
G1 X20 Y10 E0.5 F1800
G1 X20 Y20 E0.5
G1 X10 Y20 E0.5
G1 X10 Y10 E0.5
G1 Z0.6 F9000 ; Z-hop on travel -- layer is still 0.2
G1 X12 Y12 F9000
G1 Z0.2 F9000
;TYPE:Internal infill
G1 X18 Y18 E0.4 F4800
;LAYER_CHANGE
;Z:0.4
;HEIGHT:0.2
;TYPE:External perimeter
G1 X10 Y10 E0.5 F1800
G1 X20 Y10 E0.5
; filament used [mm] = 3.4
; estimated printing time (normal mode) = 0h 2m 30s
"""


def _write_gcode(text):
    fh = tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False)
    fh.write(text)
    fh.close()
    return Path(fh.name)


def _parse_fixture():
    with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as fh:
        fh.write(FIXTURE)
        path = Path(fh.name)
    try:
        return gvd.parse(path), path
    finally:
        pass


def test_layer_z_comes_from_the_slicer_not_from_g1_z():
    raw, path = _parse_fixture()
    try:
        zs = [layer[0] for layer in raw["layers"]]
        check(zs == [20, 40],
              f"layer Z should be 0.20/0.40mm from ;Z:, got {[z / 100 for z in zs]} "
              "-- the 0.6mm Z-hop travel leaked into the layer height")
    finally:
        path.unlink(missing_ok=True)


def test_speed_array_has_exactly_one_entry_per_segment():
    raw, path = _parse_fixture()
    try:
        segs = sum(raw["polys"][i + 2] - 1 for i in range(0, len(raw["polys"]), 3))
        check(len(raw["speeds"]) == segs,
              f"{len(raw['speeds'])} speeds for {segs} segments -- these must match "
              "or every path is coloured by the wrong move's feedrate")
        check(set(raw["speeds"]) == {30, 80},
              f"expected 30 and 80 mm/s from F1800/F4800, got {sorted(set(raw['speeds']))}")
    finally:
        path.unlink(missing_ok=True)


def test_travel_move_breaks_the_polyline():
    raw, path = _parse_fixture()
    try:
        # The perimeter run and the infill run are separated by a travel, so
        # they must be two polylines -- never one path jumping across the gap.
        first_layer = raw["layers"][0]
        check(first_layer[2] == 2,
              f"layer 1 should hold 2 polylines (perimeter, infill), got {first_layer[2]}")
    finally:
        path.unlink(missing_ok=True)


# PrusaSlicer emits ;HEIGHT: whenever the EXTRUSION height changes, not once
# per layer -- a bridge inside a 0.2mm layer reports 0.4. A plain 20mm cube
# gives 100 ;LAYER_CHANGE and 101 ;HEIGHT lines.
BRIDGE_FIXTURE = """\
M83
;LAYER_CHANGE
;Z:0.2
;HEIGHT:0.2
;TYPE:External perimeter
G1 X10 Y10 F9000
G1 X20 Y10 E0.5 F1800
;HEIGHT:0.4
;TYPE:Bridge infill
G1 X20 Y20 E0.5 F3600
"""


def test_layer_height_is_the_layers_own_not_a_bridge_inside_it():
    with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as fh:
        fh.write(BRIDGE_FIXTURE)
        path = Path(fh.name)
    try:
        raw = gvd.parse(path)
        h = raw["layers"][0][5]
        check(abs(h - 0.2) < 1e-6,
              f"layer height reported as {h} -- a later ;HEIGHT: inside the layer "
              "(here a bridge at 0.4) overwrote the layer's own nominal height, "
              "which renders those beads at twice their real thickness")
    finally:
        path.unlink(missing_ok=True)


def test_build_job_keeps_the_label_it_was_given():
    """The exact shadowing bug: the label came back as a feature type."""
    with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as fh:
        fh.write(FIXTURE)
        path = Path(fh.name)
    try:
        job = gvd.build_job(path, "Sauce Tray (6-well)", "a note")
        check(job["name"] == "Sauce Tray (6-well)",
              f"job label was overwritten with {job['name']!r} -- a local variable "
              "is shadowing build_job's own `name` parameter again")
        check(job["notes"] == "a note", f"notes lost: {job['notes']!r}")
        check(set(job["speedByType"]) == {"External perimeter", "Internal infill"},
              f"unexpected speed summary keys: {sorted(job['speedByType'])}")
        check(job["speedByType"]["Internal infill"]["med"] == 80,
              "internal infill median speed should be 80 mm/s")
        check(job["speedMin"] == 30 and job["speedMax"] == 80,
              f"speed range should be 30-80, got {job['speedMin']}-{job['speedMax']}")
    finally:
        path.unlink(missing_ok=True)


def test_layer_height_reported_is_modal_not_the_first_layers():
    """first-layer-height is pinned to 0.2, so reading layers[0] reported a
    0.28mm job as '0.20 mm' in the printer panel."""
    layers = [[20, 0, 1, 1.0, 1.0, 0.2]] + [[20 + 28 * i, 0, 1, 1.0, 1.0, 0.28]
                                            for i in range(1, 12)]
    check(gvd._modal_layer_height(layers) == 0.28,
          f"modal layer height should be 0.28, got {gvd._modal_layer_height(layers)} "
          "-- the pinned first layer is being reported as the job's layer height")
    check(gvd._modal_layer_height([]) == 0.2, "empty layer list should fall back to 0.2")


# Four collinear points. Segments run 30, 30, then 80 mm/s. Collinearity alone
# would drop both interior points; the speed change at point 2 must save it,
# or the merged segment invents a feedrate and the speed view moves a colour
# boundary that the slicer never drew.
SPEED_BREAK_FIXTURE = """\
M83
;LAYER_CHANGE
;Z:0.2
;HEIGHT:0.2
;TYPE:Internal infill
G1 X0 Y0 F9000
G1 X10 Y0 E1.0 F1800
G1 X20 Y0 E1.0
G1 X30 Y0 E1.0 F4800
"""


def test_simplify_never_merges_across_a_speed_change():
    path = _write_gcode(SPEED_BREAK_FIXTURE)
    try:
        raw = gvd.parse(path)
        before = list(raw["speeds"])
        check(before == [30, 30, 80], f"fixture speeds should be 30,30,80 got {before}")
        out = gvd.simplify(raw, 0.02)
        check(out["speeds"] == [30, 80],
              f"expected the 30/30 pair to merge and the 80 to survive on its own, "
              f"got {out['speeds']} -- a merge across the speed change would lose it")
        check(len(out["pts"]) // 2 == 3,
              f"expected 3 surviving points (ends plus the speed break), got "
              f"{len(out['pts']) // 2}")
    finally:
        path.unlink(missing_ok=True)


def test_simplify_zero_tolerance_is_a_no_op():
    path = _write_gcode(SPEED_BREAK_FIXTURE)
    try:
        raw = gvd.parse(path)
        same = gvd.simplify(raw, 0)
        check(same["pts"] == raw["pts"] and same["speeds"] == raw["speeds"],
              "--simplify 0 must return the payload untouched")
    finally:
        path.unlink(missing_ok=True)


def test_payload_round_trips_through_base64():
    with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as fh:
        fh.write(FIXTURE)
        path = Path(fh.name)
    try:
        raw = gvd.parse(path)
        job = gvd.build_job(path, "x")
        pts = base64.b64decode(job["pts"])
        back = struct.unpack(f"<{len(pts) // 2}h", pts)
        check(list(back) == raw["pts"],
              "int16 point payload did not survive the base64 round trip")
        spd = list(base64.b64decode(job["speeds"]))
        check(spd == raw["speeds"],
              "uint8 speed payload did not survive the base64 round trip")
        # 0.01mm quantization: a 10.00mm coordinate must come back as 1000.
        check(1000 in back, f"expected a 10.00mm coordinate as 1000, got {back[:8]}")
    finally:
        path.unlink(missing_ok=True)


def test_empty_gcode_raises_instead_of_returning_an_empty_job():
    with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as fh:
        fh.write("; nothing here\nG1 Z5 F5000\n")
        path = Path(fh.name)
    try:
        try:
            gvd.parse(path)
            _failures.append("parse() silently accepted a G-code file with no "
                             "extrusion -- it must raise, not publish an empty job")
        except ValueError:
            pass
    finally:
        path.unlink(missing_ok=True)


_MULTI = """; generated by test
M83
;LAYER_CHANGE
;Z:0.2
;HEIGHT:0.2
T0
;TYPE:External perimeter
G1 X0 Y0 F1800
G1 X10 Y0 E0.5
G1 X20 Y0 E0.5
T1
G1 X30 Y0 E0.5
G1 X40 Y0 E0.5
;TYPE:Wipe tower
G1 X50 Y0 E0.5
; filament used [mm] = 12.5, 7.25
; estimated printing time (normal mode) = 0h 2m 30s
"""


def test_a_tool_change_breaks_the_polyline():
    # One polyline must never span two filaments or the colour boundary lands
    # in the wrong place -- the same rule a ;TYPE: change already obeyed.
    p = _write_gcode(_MULTI)
    try:
        raw = gvd.parse(p)
    finally:
        p.unlink(missing_ok=True)
    tools = raw["polyTool"]
    check(len(tools) == len(raw["polys"]) // 3,
          "one tool per polyline, got %d for %d polylines"
          % (len(tools), len(raw["polys"]) // 3))
    check(sorted(set(tools)) == [0, 1],
          "both filaments should appear, got %r" % sorted(set(tools)))
    # The split has to land ON the tool change, not merely exist. T0 lays
    # X0->X10->X20 and T1 picks up at X20 and lays X30, X40, so the first two
    # polylines are three points each -- a polyline spanning the change would
    # show up here as five.
    polys = raw["polys"]
    first_n, second_n = polys[2], polys[5]
    check((first_n, second_n) == (3, 3),
          "the tool change must break the polyline: got point counts %d and %d"
          % (first_n, second_n))
    check(tools[0] == 0 and tools[1] == 1,
          "the two polylines belong to tool 0 then tool 1, got %r" % (tools[:2],))
    check(raw["toolChanges"] == 1, "one tool change, got %r" % raw["toolChanges"])


def test_filament_per_extruder_is_measured_not_read_from_the_footer():
    # PrusaSlicer's own per-extruder footer left out the wipe tower and the
    # tool-change purge on a real MMU slice: 6314 mm claimed against 11,200 mm
    # actually extruded. Measuring the moves is the only number that sums to
    # the job total, which is what an AMS spool actually loses.
    p = _write_gcode(_MULTI)
    try:
        raw = gvd.parse(p)
    finally:
        p.unlink(missing_ok=True)
    by_tool = raw["filamentByTool"]
    check(len(by_tool) == 2, "two filaments expected, got %r" % (by_tool,))
    total = sum(l[4] for l in raw["layers"])
    check(abs(sum(by_tool) - total) < 0.01,
          "per-tool filament must sum to the job total: %r vs %r"
          % (sum(by_tool), total))
    check(by_tool != [12.5, 7.25],
          "these are the footer's numbers -- the measured ones must win")
    check(raw["filamentByType"].get("Wipe tower", 0) > 0,
          "the purge has to be attributed to the wipe tower, got %r"
          % (raw["filamentByType"],))


def test_single_colour_still_reports_a_tool_for_every_polyline():
    # The AMS feeds the nozzle on a single-colour job too, so the viewer must
    # not need a special case: the array is present and all zeros.
    raw, _ = _parse_fixture()
    check(raw["toolChanges"] == 0, "no tool changes expected, got %r" % raw["toolChanges"])
    check(len(raw["polyTool"]) == len(raw["polys"]) // 3,
          "every polyline needs a tool even with one filament")
    check(set(raw["polyTool"]) <= {0}, "single-colour job should be all tool 0")


def test_wipe_tower_is_appended_so_existing_type_ids_do_not_move():
    # The index IS the payload's type id. Inserting a name anywhere but the end
    # would silently repaint every archived job.
    check(gvd.TYPES[-1] == "Wipe tower",
          "Wipe tower must be last, got %r" % gvd.TYPES[-1])
    for i, name in enumerate(["External perimeter", "Perimeter", "Overhang perimeter",
                              "Internal infill", "Solid infill", "Top solid infill",
                              "Bridge infill", "Support material",
                              "Support material interface", "Skirt/Brim", "Custom",
                              "Other"]):
        check(gvd.TYPES[i] == name,
              "type id %d moved: expected %r, got %r" % (i, name, gvd.TYPES[i]))


def test_an_overflowed_time_estimate_is_never_trusted():
    # Real PrusaSlicer output on a multi-material slice:
    # "estimated printing time (normal mode) = -2147483648s". The duration
    # regex only matches digits, so the minus was dropped and the caller
    # received 2147483648 seconds as fact and scaled every layer time to it.
    check(gvd._seconds("-2147483648s") is None,
          "a negative estimate must be rejected, got %r" % gvd._seconds("-2147483648s"))
    check(gvd._seconds("2147483648s") is None,
          "an absurd estimate must be rejected, got %r" % gvd._seconds("2147483648s"))
    check(gvd._seconds("6h 54m 56s") == 24896.0,
          "a real estimate must still parse, got %r" % gvd._seconds("6h 54m 56s"))

    bad = _MULTI.replace("0h 2m 30s", "-2147483648s")
    p = _write_gcode(bad)
    try:
        job = gvd.build_job(p, "overflow")
    finally:
        p.unlink(missing_ok=True)
    check(job["timeFromSlicer"] is False,
          "an overflowed estimate must fall back to the measured sum")
    check(job["totalSeconds"] > 0,
          "the fallback total must still be positive, got %r" % job["totalSeconds"])


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("GCODE VIEWER DATA TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("GCODE VIEWER DATA TESTS OK -- job labels survive the speed summary, "
          "layer Z ignores Z-hops, and one speed is recorded per segment.")


if __name__ == "__main__":
    run()
