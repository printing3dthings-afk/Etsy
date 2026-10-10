#!/usr/bin/env python3
"""
tools/gcode_viewer_data.py -- turn a sliced G-code file into the compact
payload the print-playback viewer replays.

WHY A SEPARATE EXPORTER. virtual_printer.py already parses G-code, but it
parses it to COUNT things (support moves, overhang perimeters) and throws the
coordinates away. A viewer needs the opposite: every extrusion path, in order,
tagged by feature and grouped by layer, small enough to ship inside a web page.

THE SIZE PROBLEM, AND WHAT IT COSTS. A real plate is 150k-400k extrusion
moves. As JSON numbers that is 10-30MB. Two things fix it:
  * Chain consecutive extrusions into polylines. A perimeter loop is one
    polyline, not 400 segments. Roughly halves the point count and removes
    every duplicated shared endpoint.
  * Quantize XY to int16 hundredths of a millimetre. The bed is 256mm, so
    25600 fits inside int16's 32767 with room to spare, and 0.01mm is well
    under one tenth of a 0.42mm bead -- invisible at any zoom a browser will
    show. This is a real precision loss; it is the one place this file trades
    accuracy for size, and it trades it somewhere that cannot show.

Travel moves are dropped entirely. They are half the move count and the viewer
does not draw them.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import re
import struct
import sys
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p1s_motion  # noqa: E402

# Order matters -- it is the index written into the payload and the order the
# legend renders in. Keep new types appended, never inserted.
TYPES = [
    "External perimeter",
    "Perimeter",
    "Overhang perimeter",
    "Internal infill",
    "Solid infill",
    "Top solid infill",
    "Bridge infill",
    "Support material",
    "Support material interface",
    "Skirt/Brim",
    "Custom",
    "Other",
    # Appended, never inserted: the index IS the payload's type id, so putting a
    # new name anywhere but the end would silently repaint every archived job.
    "Wipe tower",
]
_TYPE_INDEX = {t: i for i, t in enumerate(TYPES)}
_OTHER = _TYPE_INDEX["Other"]

_NUM = r"([-+]?[0-9]*\.?[0-9]+)"
_G1 = re.compile(r"^G[01]\s")
_AXIS = {a: re.compile(rf"{a}{_NUM}") for a in "XYZEF"}
_EST_TIME = re.compile(r"estimated printing time \(normal mode\)\s*=\s*(.+)")
_TOOL = re.compile(r"^T(\d+)\s*$")
_ACC = {k: re.compile(rf"{k}{_NUM}") for k in "PSTR"}
_DUR = re.compile(r"(\d+)\s*([dhms])")


# A real plate does not run for two months. Anything past this is the slicer
# having overflowed, not a long print.
_MAX_PLAUSIBLE_SECONDS = 60 * 86400


def _seconds(text):
    """'6h 54m 56s' -> 24896.0. Returns None if nothing trustworthy parses.

    Rejects a negative or absurd duration rather than passing it on. A real
    multi-material slice here reported "estimated printing time (normal mode)
    = -2147483648s", and because the duration regex only matches digits the
    minus was silently dropped -- the caller then received 2147483648 seconds
    as a confident figure and scaled every layer time to land on it.
    """
    text = text.strip()
    mult = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    total = sum(int(n) * mult[u] for n, u in _DUR.findall(text))
    if not total or text.startswith("-") or total > _MAX_PLAUSIBLE_SECONDS:
        return None
    return float(total)


def _axis(line, a):
    m = _AXIS[a].search(line)
    return float(m.group(1)) if m else None


def parse(gcode_path):
    """Walk the G-code once, emitting (layer, polyline) structure.

    Returns a dict ready to be serialised. Raises on a file with no extrusion,
    which means the parse is wrong or the slice was empty -- never returns an
    empty job silently.
    """
    x = y = z = 0.0
    e = 0.0
    feed = 1800.0            # mm/min; PrusaSlicer always sets F before moving
    relative_e = False
    cur_type = _OTHER
    cur_tool = 0

    pts = []                 # flat int16 x,y pairs
    polys = []               # flat int32 triples: type, startPoint, nPoints
    speeds = []              # commanded mm/s, one per SEGMENT, in draw order
    poly_tool = []           # uint8 extruder index, one per POLYLINE
    layers = []              # [z_hundredths, polyStart, polyCount, time_s, filament_mm]

    run = []                 # current polyline as [(x, y), ...]
    run_speed = []           # mm/s for the segment ENDING at each run point
    run_type = _OTHER
    run_tool = 0
    layer_start_poly = 0
    layer_time = 0.0
    layer_filament = 0.0
    layer_z = None
    layer_h = None
    slicer_seconds = None
    tool_changes = 0
    # Every move goes through the P1S motion model (tools/p1s_motion.py), and
    # each one is owned by what the viewer shows it as: an extrusion segment
    # (owner >= 0, its index) or the gap before polyline p (owner -(p + 1)) --
    # travel, retraction, Z-hop, layer change, filament swap.
    planner = p1s_motion.Planner(p1s_motion.limits_from_gcode(gcode_path))
    owner = array("l")
    acc_p = acc_t = acc_r = 0.0
    # Measured from the moves, never from the footer. The reason first given
    # here was wrong (corrected 2026-09-26): an earlier slice's footer looked
    # 44% short of "11,200 mm actually extruded", but that 11,200 counted only
    # forward moves, so every reload after a tool-change unload was counted
    # as new filament. Counted net, the moves match the footer to within 2% on
    # four real four-filament plates. They are still measured here, since the
    # per-layer split has to come from the moves anyway.
    fil_by_tool = {}
    fil_by_type = {}
    # Per LAYER as well as per job. The viewer needs to say how much each slot
    # has used at any point in the replay, and interpolating that from the
    # layer total by segment index gets it badly wrong on a multi-colour plate:
    # the purge is a large extrusion over very few segments, so index-fraction
    # attributed 24.4 g to slot 1 against its real 17.0 g. Layer boundaries are
    # exact; only the layer being printed right now is estimated.
    layer_fil_tool = {}
    fil_tool_layers = []

    def flush_run():
        nonlocal run, run_speed
        if len(run) >= 2:
            polys.extend((run_type, len(pts) // 2, len(run)))
            poly_tool.append(run_tool)
            for px, py in run:
                pts.append(int(round(px * 100)))
                pts.append(int(round(py * 100)))
            speeds.extend(run_speed)
        run = []
        run_speed = []

    def flush_layer():
        nonlocal layer_start_poly, layer_time, layer_filament, layer_h, layer_fil_tool
        flush_run()
        n = len(polys) // 3 - layer_start_poly
        if n > 0:
            layers.append([
                int(round((layer_z if layer_z is not None else 0.0) * 100)),
                layer_start_poly, n,
                round(layer_time, 2), round(layer_filament, 2),
                round(layer_h if layer_h is not None else 0.2, 3),
            ])
            fil_tool_layers.append(dict(layer_fil_tool))
        layer_start_poly = len(polys) // 3
        layer_time = 0.0
        layer_filament = 0.0
        layer_h = None
        layer_fil_tool = {}

    with open(gcode_path, "r", errors="replace") as fh:
        for line in fh:
            if line.startswith(";"):
                if line.startswith(";TYPE:"):
                    name = line[6:].strip()
                    nt = _TYPE_INDEX.get(name, _OTHER)
                    if nt != cur_type:
                        flush_run()
                        cur_type = nt
                        run_type = nt
                elif line.startswith(";LAYER_CHANGE"):
                    flush_layer()
                elif line.startswith(";Z:"):
                    # PrusaSlicer states the layer's own Z here. Inferring it
                    # from the next G1 Z instead picks up the Z-hop on a
                    # travel and reports a layer 0.4mm higher than it is.
                    try:
                        layer_z = float(line[3:])
                    except ValueError:
                        pass
                elif line.startswith(";HEIGHT:"):
                    # PrusaSlicer emits ;HEIGHT: whenever the EXTRUSION height
                    # changes, not once per layer -- a bridge or a first pass
                    # over a print-in-place gap reports 0.4 inside a 0.2 layer.
                    # Verified: a plain 20mm cube gives 100 LAYER_CHANGE but 101
                    # HEIGHT lines. Take only the first after the layer change,
                    # which is the layer's own nominal height; keeping the last
                    # made those beads render at twice their real thickness.
                    if layer_h is None:
                        try:
                            layer_h = float(line[8:])
                        except ValueError:
                            pass
                elif "estimated printing time" in line:
                    m = _EST_TIME.search(line)
                    if m:
                        slicer_seconds = _seconds(m.group(1))
                continue
            m = _TOOL.match(line)
            if m:
                # A tool change ends the current path for the same reason a type
                # change does: one polyline must never span two filaments, or the
                # colour boundary lands in the wrong place.
                nt = int(m.group(1))
                if nt != cur_tool:
                    flush_run()
                    cur_tool = nt
                    run_tool = nt
                    tool_changes += 1
                    planner.add_fixed(p1s_motion.P1S_TOOLCHANGE_S)
                    owner.append(-(len(polys) // 3 + 1))
                continue
            if line.startswith("M204"):
                for k in "PSTR":
                    m = _ACC[k].search(line)
                    if not m:
                        continue
                    v = float(m.group(1))
                    if k in "PS":
                        acc_p = v
                    if k == "T" or (k == "S" and not acc_t):
                        acc_t = v
                    if k == "R":
                        acc_r = v
                continue
            if line.startswith("G4"):
                ms = re.search(r"P" + _NUM, line)
                sec = re.search(r"S" + _NUM, line)
                planner.add_fixed((float(ms.group(1)) / 1000 if ms else 0.0)
                                  + (float(sec.group(1)) if sec else 0.0))
                owner.append(-(len(polys) // 3 + (1 if run else 0) + 1))
                continue
            if line.startswith("M83"):
                relative_e = True
                continue
            if line.startswith("M82"):
                relative_e = False
                continue
            if line.startswith("G92"):
                ne = _axis(line, "E")
                if ne is not None:
                    e = ne
                continue
            if not _G1.match(line):
                continue

            nx, ny, nz, ne, nf = (_axis(line, a) for a in "XYZEF")
            if nf is not None:
                feed = nf
            pz = z
            if nz is not None:
                z = nz
            px, py = x, y
            if nx is not None:
                x = nx
            if ny is not None:
                y = ny

            de = 0.0
            if ne is not None:
                de = ne if relative_e else (ne - e)
                e = ne if not relative_e else e + ne

            dist = math.hypot(x - px, y - py)
            if dist > 0 and feed > 0:
                layer_time += dist / (feed / 60.0)
            moving = dist > 0 or z != pz
            kind = "print" if (de > 0 and dist > 0) else ("travel" if moving else "retract")
            blk = planner.add_move(x - px, y - py, z - pz, de, feed / 60.0,
                                   {"print": acc_p, "travel": acc_t or acc_p,
                                    "retract": acc_r}[kind], kind)

            # Filament is counted NET, every E move of either sign (2026-09-26).
            # Counting only forward moves that travel counted each filament
            # reload after a tool-change unload as fresh filament: the haunted
            # cemetery's wipe tower came to 76.5 m against 31.7 m net, and the
            # plate to 273 g against the slicer's 143 g. Net per tool matches
            # the slicer's own per-extruder footer to within 2%.
            if de:
                layer_filament += de
                fil_by_tool[cur_tool] = fil_by_tool.get(cur_tool, 0.0) + de
                fil_by_type[cur_type] = fil_by_type.get(cur_type, 0.0) + de
                layer_fil_tool[cur_tool] = layer_fil_tool.get(cur_tool, 0.0) + de

            if de > 0 and dist > 0:
                if not run:
                    run_type = cur_type
                    run_tool = cur_tool
                    run.append((px, py))
                elif run_type != cur_type or run_tool != cur_tool:
                    flush_run()
                    run_type = cur_type
                    run_tool = cur_tool
                    run.append((px, py))
                run.append((x, y))
                # Two bytes since 2026-10-10: Bambu's own P1S profile runs
                # inner walls at 300 mm/s, and one byte had clamped them to 255.
                run_speed.append(max(1, min(65535, int(round(feed / 60.0)))))
                if blk is not None:
                    owner.append(len(speeds) + len(run_speed) - 1)
            else:
                if dist > 0:
                    flush_run()      # a travel ends the current path
                if blk is not None:
                    owner.append(-(len(polys) // 3 + (1 if run else 0) + 1))

    flush_layer()

    times = planner.solve()
    seg_times = [0.0] * len(speeds)
    n_poly = len(polys) // 3
    gap_times = [0.0] * (n_poly + 1)
    for k, o in enumerate(owner):
        if o >= 0:
            seg_times[o] += times[k]
        else:
            gap_times[min(-o - 1, n_poly)] += times[k]

    if not layers:
        raise ValueError(
            f"{gcode_path}: parsed zero printable layers -- either the slice "
            "is empty or this G-code flavour is not the one this parser "
            "expects (it needs PrusaSlicer's ;TYPE: / ;LAYER_CHANGE tags).")

    xs = pts[0::2]
    ys = pts[1::2]

    # Positions ship as int16 hundredths of a millimetre, so anything past
    # +-327.67mm cannot be represented. That is not a packing detail to paper
    # over: a P1S bed is 256mm, so a toolpath out there is a model sitting off
    # the plate. Two "assembly" 3MFs in this repo lay their parts out side by
    # side for viewing -- one reaches X=819mm -- and the old failure for that
    # was a bare struct.error naming no file.
    lo, hi = min(min(xs), min(ys)), max(max(xs), max(ys))
    if lo < -32768 or hi > 32767:
        raise ValueError(
            f"{gcode_path}: toolpath spans {lo / 100:.1f} to {hi / 100:.1f} mm, "
            "which is off a 256mm bed. This is usually an assembly file that "
            "lays its parts out for viewing rather than a plate you can print.")
    assert len(speeds) == sum(polys[i + 2] - 1 for i in range(0, len(polys), 3)), \
        "speed array and segment count diverged -- the run/flush bookkeeping is wrong"
    assert len(poly_tool) == len(polys) // 3, \
        "tool array and polyline count diverged -- the run/flush bookkeeping is wrong"

    return {
        "pts": pts,
        "polys": polys,
        "speeds": speeds,
        "polyTool": poly_tool,
        "toolChanges": tool_changes,
        "filamentByTool": [round(fil_by_tool.get(i, 0.0), 1)
                           for i in range(max(fil_by_tool) + 1 if fil_by_tool else 1)],
        "filamentByType": {TYPES[t]: round(v, 1) for t, v in sorted(fil_by_type.items())},
        "filByToolLayer": fil_tool_layers,
        "layers": layers,
        "slicerSeconds": slicer_seconds,
        "segTimes": seg_times,
        # gapTimes[p] is everything between polyline p-1 ending and p starting;
        # the trailing entry is the end of the file, which the replay never shows.
        "gapTimes": gap_times[:n_poly],
        "bbox": [min(xs) / 100, min(ys) / 100, max(xs) / 100, max(ys) / 100],
    }


def simplify(raw, tol_mm=0.02):
    """Drop points whose removal shifts the path less than `tol_mm`.

    0.02mm is a twentieth of a 0.42mm bead -- below the 0.01mm quantization
    grid's own visible effect, let alone anything a browser renders. It removes
    8-30% of points on real plates.

    HARD CONSTRAINT: a point is never dropped where the SPEED changes. Merging
    two segments that ran at different feedrates would invent a speed for the
    merged one and move a colour boundary, and the speed view exists precisely
    to show where the slicer changed its mind. Geometry may be approximated;
    the slicer's decisions may not.
    """
    if tol_mm <= 0:
        return raw
    pts, polys, speeds = raw["pts"], raw["polys"], raw["speeds"]
    seg_times = raw.get("segTimes")
    tol = tol_mm * 100
    new_pts, new_polys, new_speeds, new_times = [], [], [], []
    seg_at = 0
    for pi in range(len(polys) // 3):
        t, s0, n = polys[pi * 3:pi * 3 + 3]
        keep = [0]
        anchor = 0
        for i in range(1, n - 1):
            # segment i-1 ends at point i, segment i starts at it
            if speeds[seg_at + i - 1] != speeds[seg_at + i]:
                keep.append(i)
                anchor = i
                continue
            ax, ay = pts[(s0 + anchor) * 2], pts[(s0 + anchor) * 2 + 1]
            bx, by = pts[(s0 + i) * 2], pts[(s0 + i) * 2 + 1]
            cx, cy = pts[(s0 + i + 1) * 2], pts[(s0 + i + 1) * 2 + 1]
            L = math.hypot(cx - ax, cy - ay)
            d = (abs((cx - ax) * (ay - by) - (ax - bx) * (cy - ay)) / L if L > 1e-9
                 else math.hypot(bx - ax, by - ay))
            if d > tol:
                keep.append(i)
                anchor = i
        keep.append(n - 1)
        start = len(new_pts) // 2
        for i in keep:
            new_pts.append(pts[(s0 + i) * 2])
            new_pts.append(pts[(s0 + i) * 2 + 1])
        # the merged segment inherits the speed of the run it replaces, which
        # is unambiguous precisely because a speed change is never merged over
        for k in range(len(keep) - 1):
            new_speeds.append(speeds[seg_at + keep[k]])
            # A merged segment takes exactly as long as the moves it replaces.
            if seg_times is not None:
                new_times.append(sum(seg_times[seg_at + keep[k]:seg_at + keep[k + 1]]))
        new_polys.extend((t, start, len(keep)))
        seg_at += n - 1
    raw = dict(raw)
    raw["pts"], raw["polys"], raw["speeds"] = new_pts, new_polys, new_speeds
    if seg_times is not None:
        raw["segTimes"] = new_times
    _refit_layers(raw, polys)
    return raw


def _refit_layers(raw, old_polys):
    """Polyline count per layer is unchanged by simplification -- only their
    point counts shrink -- so layer records still index the same polylines."""
    assert len(raw["polys"]) == len(old_polys), \
        "simplification must not add or remove polylines; layer records index them"


def _model_timing(raw):
    """Per-segment average speeds, per-polyline gap times and the total, from
    the motion model's times, measured against the quantised points the viewer
    will draw. Rewrites each layer's time to the modelled one."""
    pts, polys, layers = raw["pts"], raw["polys"], raw["layers"]
    seg_t, gaps = raw["segTimes"], raw["gapTimes"]
    seg_v = []
    eff = []          # the time the viewer will actually spend on each segment
    k = 0
    lost = 0.0
    for pi in range(len(polys) // 3):
        s0, n = polys[pi * 3 + 1], polys[pi * 3 + 2]
        for i in range(n - 1):
            ax, ay = pts[(s0 + i) * 2], pts[(s0 + i) * 2 + 1]
            bx, by = pts[(s0 + i + 1) * 2], pts[(s0 + i + 1) * 2 + 1]
            length = math.hypot(bx - ax, by - ay)            # 0.01 mm units
            t = seg_t[k]
            if length < 0.5 or t <= 0:
                # Collapsed to one quantised point: the viewer cannot spend time
                # on a segment it draws as nothing, so the time moves to the gap.
                seg_v.append(65535)
                eff.append(0.0)
                lost += t
            else:
                v = max(1, min(65535, int(round(length / t))))
                seg_v.append(v)
                eff.append(length / v)
            k += 1
        if lost and pi + 1 < len(gaps):
            gaps[pi + 1] += lost
            lost = 0.0
    total = 0.0
    seg_at = 0
    for layer in layers:
        p0, pc = layer[1], layer[2]
        lt = 0.0
        for pi in range(p0, p0 + pc):
            lt += gaps[pi]
            n = polys[pi * 3 + 2]
            lt += sum(eff[seg_at:seg_at + n - 1])
            seg_at += n - 1
        layer[3] = round(lt, 2)
        total += lt
    return seg_v, [float(g) for g in gaps], total


def _b64(values, fmt):
    return base64.b64encode(struct.pack(f"<{len(values)}{fmt}", *values)).decode()


def _modal_layer_height(layers):
    """Most common layer height across the job, to 3dp. A job is not one
    height -- supports and bridges vary it -- so the honest single number is
    the one the bulk of the layers actually use."""
    if not layers:
        return 0.2
    counts = {}
    for layer in layers:
        h = round(layer[5], 3)
        counts[h] = counts.get(h, 0) + 1
    return max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]


def build_job(gcode_path, name, notes="", tol_mm=0.02):
    raw = simplify(parse(gcode_path), tol_mm)
    layers = raw["layers"]
    slicer_total = raw["slicerSeconds"]

    # Time comes from the P1S motion model, move by move (tools/p1s_motion.py):
    # acceleration, cornering, travel, retraction and filament swaps. It used to
    # be each layer's feedrate sum scaled to the slicer's footer and spread
    # evenly over the layer; that is kept only as the comparison figure. On a
    # single-filament plate the model and PrusaSlicer's own estimator agree to
    # within a percent (they implement the same planner); on a multi-filament
    # one the slicer's figure is unreliable (it has printed -2147483648 s) and
    # has no swap time, so the model is the only honest number.
    seg_v, gap_t, total_time = _model_timing(raw)

    total_fil = sum(l[4] for l in layers)
    grams = total_fil * math.pi * (1.75 / 2) ** 2 / 1000 * 1.24
    # Per-type speed summary. This is the payload's own teaching point: the
    # slicer runs the outer wall at roughly half the inner wall, and the top
    # surface slowest of all. Reporting the real min/median/max per type beats
    # asserting it in prose.
    per_type = {}
    spd_by_type = {}
    seg = 0
    for i in range(0, len(raw["polys"]), 3):
        t, _s, n = raw["polys"][i:i + 3]
        # `tname`, not `name` -- `name` is this function's own parameter, and
        # shadowing it here silently stamped the last feature type onto every
        # job's label in index.js. Caught in the browser, not by reading this.
        tname = TYPES[t]
        per_type[tname] = per_type.get(tname, 0) + n - 1
        spd_by_type.setdefault(tname, []).extend(raw["speeds"][seg:seg + n - 1])
        seg += n - 1
    speed_summary = {}
    for tname, vals in spd_by_type.items():
        vals.sort()
        speed_summary[tname] = {"min": vals[0], "med": vals[len(vals) // 2],
                                "max": vals[-1], "n": len(vals)}
    all_spd = sorted(raw["speeds"])
    return {
        "name": name,
        "notes": notes,
        "types": TYPES,
        "bbox": raw["bbox"],
        # The MODAL layer height, not layers[0]'s -- the first layer is pinned
        # to 0.2 by first-layer-height, so reading index 0 reported "0.20 mm"
        # while showing a 0.28 mm job. Caught by looking at the panel next to
        # the render, not by reading this.
        "layerHeight": _modal_layer_height(layers),
        "firstLayerHeight": round(layers[0][5], 3) if layers else 0.2,
        "beadWidth": 0.42,
        "totalSeconds": round(total_time, 1),
        "timeFromSlicer": False,
        "timeModel": "P1S, Marlin classic-jerk planner (tools/p1s_motion.py)",
        "slicerSeconds": slicer_total,
        "filamentMm": round(total_fil, 1),
        "filamentG": round(grams, 1),
        "segmentsByType": per_type,
        "speedByType": speed_summary,
        "speedMin": all_spd[0],
        "speedMax": all_spd[-1],
        "layers": layers,
        "pts": _b64(raw["pts"], "h"),
        "polys": _b64(raw["polys"], "i"),
        "speeds": _b64(raw["speeds"], "H"),
        "speedBits": 16,
        # Per segment, its average speed under the motion model, in 0.01 mm/s:
        # the viewer divides the segment's own length by it, so the two always
        # agree on the quantised geometry it actually draws.
        "segV": _b64(seg_v, "H"),
        "gapT": _b64(gap_t, "f"),
        # One extruder index per polyline. Present even on a single-colour job,
        # where it is all zeros -- the AMS feeds the nozzle either way, and the
        # viewer should not need a special case to show that.
        "polyTool": _b64(raw["polyTool"], "B"),
        "toolChanges": raw["toolChanges"],
        "filamentByTool": raw["filamentByTool"],
        "filamentByType": raw["filamentByType"],
        # Flat rows, one per layer, nTools wide -- a list of dicts would more
        # than double the payload for a job with hundreds of layers.
        "filByToolLayer": [[round(row.get(t, 0.0), 2)
                            for t in range(len(raw["filamentByTool"]))]
                           for row in raw["filByToolLayer"]],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("gcode", nargs="+")
    ap.add_argument("-d", "--outdir", required=True,
                    help="directory to write one <stem>.js per job, plus index.js")
    ap.add_argument("--label", action="append", default=[],
                    help="STEM=Display Name -- repeatable")
    ap.add_argument("--note", action="append", default=[],
                    help="STEM=one line about what this job teaches -- repeatable")
    ap.add_argument("--source", action="append", default=[],
                    help="STEM=repo path of the file this was sliced from -- "
                         "repeatable. Shown in the viewer so the plate on screen "
                         "names the file you would actually print.")
    ap.add_argument("--max-mb", type=float, default=0, metavar="MB",
                    help="if a job's payload exceeds this, re-simplify it at a "
                         "coarser tolerance until it fits, and record the "
                         "tolerance actually used. 0 disables. The whole set has "
                         "to fit one page, and the honest way to buy that is a "
                         "coarser path on the heavy plates only -- not a quietly "
                         "coarser one everywhere.")
    ap.add_argument("--colours", action="append", default=[], metavar="STEM=#HEX,#HEX",
                    help="the plate's design colours, one per filament in tool "
                         "order; the viewer draws its beads and spools in them "
                         "instead of its placeholder palette -- repeatable")
    ap.add_argument("--append", action="store_true",
                    help="merge these jobs into the outdir's existing index.js "
                         "(same id replaced, the rest kept) instead of writing an "
                         "index of only these")
    ap.add_argument("--simplify", type=float, default=0.02, metavar="MM",
                    help="drop points that shift the path less than this "
                         "(default 0.02mm = 1/20 of a bead; 0 keeps every point)")
    a = ap.parse_args(argv)

    labels = dict(kv.split("=", 1) for kv in a.label)
    notes = dict(kv.split("=", 1) for kv in a.note)
    sources = dict(kv.split("=", 1) for kv in a.source)
    colours = {}
    for kv in a.colours:
        stem, hexes = kv.split("=", 1)
        cs = [h.strip() for h in hexes.split(",")]
        bad = [h for h in cs if not re.fullmatch(r"#[0-9A-Fa-f]{6}", h)]
        if bad:
            ap.error(f"--colours {stem}: not #RRGGBB: {', '.join(bad)}")
        colours[stem] = cs
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    index = []
    for g in a.gcode:
        p = Path(g)
        stem = p.stem
        tol = a.simplify
        job = build_job(p, labels.get(stem, stem), notes.get(stem, ""), tol)
        if a.max_mb:
            while (len(json.dumps(job, separators=(",", ":"))) / 1024 / 1024 > a.max_mb
                   and tol < 0.5):
                tol = round(tol * 2, 4)
                job = build_job(p, labels.get(stem, stem), notes.get(stem, ""), tol)
        job["simplifyMm"] = tol
        if stem in colours:
            job["toolColors"] = colours[stem]
        # Each job is its own script so the page loads one, not all of them.
        # Same-origin <script src> rather than fetch(): a script tag is the
        # one transport the artifact CSP is unambiguous about.
        dest = out / f"{stem}.js"
        dest.write_text("window.__JOB_LOADED("
                        + json.dumps(job, separators=(",", ":")) + ");\n")
        mb = dest.stat().st_size / 1024 / 1024
        segments = sum(job["segmentsByType"].values())
        index.append({
            "id": stem, "name": job["name"], "notes": job["notes"],
            "layers": len(job["layers"]), "segments": segments,
            "maxZ": job["layers"][-1][0] / 100,
            "totalSeconds": job["totalSeconds"], "filamentG": job["filamentG"],
            "bbox": job["bbox"], "sizeMB": round(mb, 2),
            "speedMin": job["speedMin"], "speedMax": job["speedMax"],
            "needsSupport": "Support material" in job["segmentsByType"],
            # In the index so the plate list can say "5 filaments" before the
            # job itself is fetched -- the whole point of loading on demand.
            "toolChanges": job["toolChanges"],
            "filamentByTool": job["filamentByTool"],
            "source": sources.get(stem, ""),
            "simplifyMm": job["simplifyMm"],
        })
        print(f"{stem:28s} {len(job['layers']):4d} layers  "
              f"{segments:9,d} segments  {job['filamentG']:7.1f}g  "
              f"{job['totalSeconds'] / 60:6.0f} min  "
              f"{job['speedMin']}-{job['speedMax']} mm/s  {mb:5.2f} MB")

    # Without --append the index is only this run's jobs: adding the Christmas
    # village to the 77-plate library would have dropped the other 77 from it.
    if a.append and (out / "index.js").exists():
        old = (out / "index.js").read_text()
        old = json.loads(old[old.index("["):old.rindex("]") + 1])
        # Replaced where it stood: the plate list's "Featured" order is this
        # order, and re-exporting a plate must not move it to the bottom.
        fresh = {j["id"]: j for j in index}
        old_ids = {j["id"] for j in old}
        index = [fresh.get(j["id"], j) for j in old] + [j for j in index if j["id"] not in old_ids]
    (out / "index.js").write_text(
        "window.__PRINT_INDEX = " + json.dumps(index, separators=(",", ":")) + ";\n")
    total = sum(i["sizeMB"] for i in index)
    print(f"\n{len(index)} jobs -> {out}  ({total:.2f} MB total, loaded on demand)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
