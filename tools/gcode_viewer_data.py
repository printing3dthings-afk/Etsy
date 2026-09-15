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
from pathlib import Path

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
]
_TYPE_INDEX = {t: i for i, t in enumerate(TYPES)}
_OTHER = _TYPE_INDEX["Other"]

_NUM = r"([-+]?[0-9]*\.?[0-9]+)"
_G1 = re.compile(r"^G[01]\s")
_AXIS = {a: re.compile(rf"{a}{_NUM}") for a in "XYZEF"}
_EST_TIME = re.compile(r"estimated printing time \(normal mode\)\s*=\s*(.+)")
_DUR = re.compile(r"(\d+)\s*([dhms])")


def _seconds(text):
    """'6h 54m 56s' -> 24896.0. Returns None if nothing parses."""
    mult = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    total = sum(int(n) * mult[u] for n, u in _DUR.findall(text))
    return float(total) or None


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

    pts = []                 # flat int16 x,y pairs
    polys = []               # flat int32 triples: type, startPoint, nPoints
    layers = []              # [z_hundredths, polyStart, polyCount, time_s, filament_mm]

    run = []                 # current polyline as [(x, y), ...]
    run_type = _OTHER
    layer_start_poly = 0
    layer_time = 0.0
    layer_filament = 0.0
    layer_z = None
    layer_h = 0.2
    slicer_seconds = None

    def flush_run():
        nonlocal run
        if len(run) >= 2:
            polys.extend((run_type, len(pts) // 2, len(run)))
            for px, py in run:
                pts.append(int(round(px * 100)))
                pts.append(int(round(py * 100)))
        run = []

    def flush_layer():
        nonlocal layer_start_poly, layer_time, layer_filament
        flush_run()
        n = len(polys) // 3 - layer_start_poly
        if n > 0:
            layers.append([
                int(round((layer_z if layer_z is not None else 0.0) * 100)),
                layer_start_poly, n,
                round(layer_time, 2), round(layer_filament, 2),
                round(layer_h, 3),
            ])
        layer_start_poly = len(polys) // 3
        layer_time = 0.0
        layer_filament = 0.0

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
                    try:
                        layer_h = float(line[8:])
                    except ValueError:
                        pass
                elif "estimated printing time" in line:
                    m = _EST_TIME.search(line)
                    if m:
                        slicer_seconds = _seconds(m.group(1))
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

            if de > 0 and dist > 0:
                layer_filament += de
                if not run:
                    run_type = cur_type
                    run.append((px, py))
                elif run_type != cur_type:
                    flush_run()
                    run_type = cur_type
                    run.append((px, py))
                run.append((x, y))
            elif dist > 0:
                flush_run()      # a travel ends the current path

    flush_layer()

    if not layers:
        raise ValueError(
            f"{gcode_path}: parsed zero printable layers -- either the slice "
            "is empty or this G-code flavour is not the one this parser "
            "expects (it needs PrusaSlicer's ;TYPE: / ;LAYER_CHANGE tags).")

    xs = pts[0::2]
    ys = pts[1::2]
    return {
        "pts": pts,
        "polys": polys,
        "layers": layers,
        "slicerSeconds": slicer_seconds,
        "bbox": [min(xs) / 100, min(ys) / 100, max(xs) / 100, max(ys) / 100],
    }


def _b64(values, fmt):
    return base64.b64encode(struct.pack(f"<{len(values)}{fmt}", *values)).decode()


def build_job(gcode_path, name, notes=""):
    raw = parse(gcode_path)
    layers = raw["layers"]
    kinematic = sum(l[3] for l in layers)
    slicer_total = raw["slicerSeconds"]

    # The per-move estimate below ignores acceleration and travel, so it runs
    # ~5-10% short of the slicer's own figure. Rather than publish a number I
    # know is wrong, scale the per-layer distribution -- which IS accurate
    # relative to itself -- so the total lands on the slicer's estimate.
    if slicer_total and kinematic > 0:
        k = slicer_total / kinematic
        for l in layers:
            l[3] = round(l[3] * k, 2)
        total_time = slicer_total
    else:
        total_time = kinematic

    total_fil = sum(l[4] for l in layers)
    grams = total_fil * math.pi * (1.75 / 2) ** 2 / 1000 * 1.24
    per_type = {}
    for i in range(0, len(raw["polys"]), 3):
        t, _s, n = raw["polys"][i:i + 3]
        per_type[TYPES[t]] = per_type.get(TYPES[t], 0) + n - 1
    return {
        "name": name,
        "notes": notes,
        "types": TYPES,
        "bbox": raw["bbox"],
        "layerHeight": layers[0][5] if layers else 0.2,
        "beadWidth": 0.42,
        "totalSeconds": round(total_time, 1),
        "timeFromSlicer": bool(slicer_total),
        "filamentMm": round(total_fil, 1),
        "filamentG": round(grams, 1),
        "segmentsByType": per_type,
        "layers": layers,
        "pts": _b64(raw["pts"], "h"),
        "polys": _b64(raw["polys"], "i"),
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
    a = ap.parse_args(argv)

    labels = dict(kv.split("=", 1) for kv in a.label)
    notes = dict(kv.split("=", 1) for kv in a.note)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    index = []
    for g in a.gcode:
        p = Path(g)
        stem = p.stem
        job = build_job(p, labels.get(stem, stem), notes.get(stem, ""))
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
            "needsSupport": "Support material" in job["segmentsByType"],
        })
        print(f"{stem:28s} {len(job['layers']):4d} layers  "
              f"{segments:9,d} segments  {job['filamentG']:7.1f}g  "
              f"{job['totalSeconds'] / 60:6.0f} min  {mb:5.2f} MB")

    (out / "index.js").write_text(
        "window.__PRINT_INDEX = " + json.dumps(index, separators=(",", ":")) + ";\n")
    total = sum(i["sizeMB"] for i in index)
    print(f"\n{len(index)} jobs -> {out}  ({total:.2f} MB total, loaded on demand)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
