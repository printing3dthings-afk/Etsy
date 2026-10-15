#!/usr/bin/env python3
"""
tools/print_risk.py -- measurable signals from a real sliced file that
correlate with real-world print failure.

WHAT THIS IS NOT. It is not a physics simulation. It models no gravity, no
melt rheology, no thermal contraction, no bed adhesion and no layer bonding.
Nothing here predicts warping. A part can pass every check below and still
fail on the plate.

WHAT IT IS. Five numbers pulled out of the actual G-code that are known to
correlate with known failure modes, so a risk is a measured quantity instead
of a guess:

  * unsupported_span_mm -- the longest CONTIGUOUS stretch of a bridge move
    with nothing printed beneath it. Reported by rasterizing the layer below
    and sampling along each bridge move, because "longest bridge move" badly
    overstates the risk: a straight move can pass over supported ground. On
    this shop's sauce tray the longest bridge MOVE is 107.9mm; the longest
    genuinely unsupported run inside it is a different, smaller number.

  * short_layers -- layers whose own print time falls under the profile's
    slowdown_below_layer_time. The slicer already slows these toward
    min_print_speed; the ones still under the threshold afterwards cannot be
    fixed by slowing further, and that is where droop and blobbing live.

  * first_layer_area_mm2 -- extruded area on layer 1, a proxy for how much
    grip the part has on the plate.

  * aspect_ratio -- height over the larger footprint dimension. Tall and
    narrow parts get knocked over by the toolhead.

  * overhang_mm -- total length of moves the slicer itself tagged as
    overhang perimeter.

THRESHOLDS ARE NOT CALIBRATED. The constants below are starting points, not
findings. The only thing that turns a signal into a prediction is a real
print on a real machine -- see `--record` for logging outcomes against them.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gcode_viewer_data import TYPES, parse  # noqa: E402

GRID_MM = 0.5          # occupancy raster cell; half a bead width
_CFG = re.compile(r"^;\s*([a-z_]+)\s*=\s*(.+?)\s*$")


def _config(gcode_path):
    """PrusaSlicer writes its whole config as trailing comments."""
    out = {}
    with open(gcode_path, "r", errors="replace") as fh:
        for line in fh:
            if line.startswith("; "):
                m = _CFG.match(line.rstrip("\n"))
                if m:
                    out[m.group(1)] = m.group(2)
    return out


def _layer_cells(raw, li, cells):
    """Stamp every extrusion in layer `li` into a set of occupancy cells."""
    pts, polys, L = raw["pts"], raw["polys"], raw["layers"][li]
    step = GRID_MM * 100
    for pi in range(L[1], L[1] + L[2]):
        s, n = polys[pi * 3 + 1], polys[pi * 3 + 2]
        for i in range(s, s + n - 1):
            x0, y0 = pts[i * 2], pts[i * 2 + 1]
            x1, y1 = pts[(i + 1) * 2], pts[(i + 1) * 2 + 1]
            d = math.hypot(x1 - x0, y1 - y0)
            steps = max(1, int(d / step))
            for k in range(steps + 1):
                t = k / steps
                cells.add((int((x0 + (x1 - x0) * t) / step),
                           int((y0 + (y1 - y0) * t) / step)))
    return cells


def _neighbourhood(cells, cx, cy):
    """A bead one cell wide supports a point within a cell of it."""
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if (cx + dx, cy + dy) in cells:
                return True
    return False


def unsupported_spans(raw):
    """Longest contiguous unsupported run inside any bridge move, in mm."""
    bridge = TYPES.index("Bridge infill")
    pts, polys = raw["pts"], raw["polys"]
    step = GRID_MM * 100
    worst = 0.0
    worst_at = None
    below = set()
    for li, L in enumerate(raw["layers"]):
        if li > 0:
            for pi in range(L[1], L[1] + L[2]):
                if polys[pi * 3] != bridge:
                    continue
                s, n = polys[pi * 3 + 1], polys[pi * 3 + 2]
                for i in range(s, s + n - 1):
                    x0, y0 = pts[i * 2], pts[i * 2 + 1]
                    x1, y1 = pts[(i + 1) * 2], pts[(i + 1) * 2 + 1]
                    d = math.hypot(x1 - x0, y1 - y0)
                    steps = max(1, int(d / step))
                    run = 0
                    for k in range(steps + 1):
                        t = k / steps
                        cx = int((x0 + (x1 - x0) * t) / step)
                        cy = int((y0 + (y1 - y0) * t) / step)
                        if _neighbourhood(below, cx, cy):
                            run = 0
                        else:
                            run += 1
                            span = run * (d / max(steps, 1)) / 100
                            if span > worst:
                                worst, worst_at = span, L[0] / 100
        below = _layer_cells(raw, li, set())
    return worst, worst_at


def analyse(gcode_path):
    gcode_path = Path(gcode_path)
    raw = parse(gcode_path)
    cfg = _config(gcode_path)
    layers = raw["layers"]
    pts, polys = raw["pts"], raw["polys"]

    threshold = float(cfg.get("slowdown_below_layer_time", 5) or 5)
    short = [(i + 1, round(l[3], 2)) for i, l in enumerate(layers) if l[3] < threshold]

    def poly_len(pi):
        s, n = polys[pi * 3 + 1], polys[pi * 3 + 2]
        return sum(math.hypot(pts[(i + 1) * 2] - pts[i * 2],
                              pts[(i + 1) * 2 + 1] - pts[i * 2 + 1]) / 100
                   for i in range(s, s + n - 1))

    L1 = layers[0]
    l1_len = sum(poly_len(pi) for pi in range(L1[1], L1[1] + L1[2]))
    over = TYPES.index("Overhang perimeter")
    over_len = sum(poly_len(pi) for pi in range(len(polys) // 3)
                   if polys[pi * 3] == over)

    xs = [p / 100 for p in pts[0::2]]
    ys = [p / 100 for p in pts[1::2]]
    width = max(max(xs) - min(xs), max(ys) - min(ys))
    height = layers[-1][0] / 100

    span, span_z = unsupported_spans(raw)
    return {
        "file": gcode_path.name,
        "layers": len(layers),
        "height_mm": round(height, 2),
        "unsupported_span_mm": round(span, 1),
        "unsupported_span_at_z": span_z,
        "short_layers": len(short),
        "shortest_layer_s": round(min(l[3] for l in layers), 2),
        "slowdown_threshold_s": threshold,
        "first_layer_area_mm2": round(l1_len * float(cfg.get("extrusion_width", 0.42) or 0.42)),
        "aspect_ratio": round(height / width, 2) if width else None,
        "overhang_mm": round(over_len),
        "worst_short_layers": short[:6],
    }


# Calibration log. Signals only become predictions when they are checked
# against what the machine actually did, so every real print outcome is
# recorded next to the numbers that were true before it ran. Written by this
# CLI only -- never by the server, which must not write git-tracked files.
OUTCOMES = Path(__file__).resolve().parent.parent / "data" / "print_outcomes.json"


def record(gcode_path, outcome, note="", failed_at_z=None):
    """Append one real-world result against the signals measured beforehand."""
    if outcome not in ("ok", "failed", "partial"):
        raise ValueError("outcome must be ok, failed or partial")
    signals = analyse(gcode_path)
    entry = {
        "recorded": __import__("datetime").date.today().isoformat(),
        "outcome": outcome,
        "note": note,
        "failed_at_z": failed_at_z,
        "signals": signals,
    }
    log = []
    if OUTCOMES.exists():
        log = json.loads(OUTCOMES.read_text())
    log.append(entry)
    OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
    OUTCOMES.write_text(json.dumps(log, indent=2) + "\n")
    return entry, len(log)


def calibration_report():
    """What the log can and cannot yet say about each threshold."""
    if not OUTCOMES.exists():
        return ("No outcomes recorded yet. Until real prints are logged against "
                "these signals, every threshold in this file is a guess.\n"
                "  python3 tools/print_risk.py plate.gcode --record failed "
                "--at-z 13.2 --note 'cap drooped'")
    log = json.loads(OUTCOMES.read_text())
    ok = [e for e in log if e["outcome"] == "ok"]
    bad = [e for e in log if e["outcome"] != "ok"]
    lines = [f"{len(log)} recorded print(s): {len(ok)} ok, {len(bad)} failed/partial"]
    if not bad or not ok:
        lines.append("A threshold needs examples on BOTH sides to mean anything. "
                     f"Have {len(ok)} good and {len(bad)} bad.")
        return "\n".join(lines)
    # Two prints that happen to differ is not a separation. Anything can look
    # like it "separates cleanly" at n=2, and calling that a finding is exactly
    # the kind of claim this whole tool exists to avoid making.
    MIN_EACH = 3
    thin = len(ok) < MIN_EACH or len(bad) < MIN_EACH
    if thin:
        lines.append(f"NOT ENOUGH DATA to separate anything -- {len(ok)} good and "
                     f"{len(bad)} bad, want at least {MIN_EACH} of each. Ranges "
                     "below are descriptive only.")
    for key in ("unsupported_span_mm", "short_layers", "aspect_ratio",
                "first_layer_area_mm2"):
        g = [e["signals"][key] for e in ok if e["signals"].get(key) is not None]
        b = [e["signals"][key] for e in bad if e["signals"].get(key) is not None]
        if not g or not b:
            continue
        sep = min(b) > max(g) or max(b) < min(g)
        if thin:
            verdict = ""
        elif sep:
            verdict = "   << separates cleanly"
        else:
            verdict = "   (overlapping -- not predictive)"
        lines.append(f"  {key:22s} ok: {min(g)}-{max(g)}   failed: {min(b)}-{max(b)}{verdict}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gcode", nargs="*")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--record", choices=("ok", "failed", "partial"),
                    help="log a REAL print outcome for this file")
    ap.add_argument("--at-z", type=float, default=None,
                    help="height in mm where a failure started")
    ap.add_argument("--note", default="", help="what actually happened")
    ap.add_argument("--calibration", action="store_true",
                    help="what the outcome log can so far support")
    a = ap.parse_args(argv)

    if a.calibration:
        print(calibration_report())
        return 0
    if not a.gcode:
        ap.error("a gcode file is required unless --calibration is given")
    if a.record:
        entry, n = record(a.gcode[0], a.record, a.note, a.at_z)
        print(f"recorded {a.record} for {entry['signals']['file']} "
              f"({n} outcome(s) on file)")
        print(calibration_report())
        return 0

    results = [analyse(g) for g in a.gcode]
    if a.json:
        print(json.dumps(results, indent=2))
        return 0
    print(f"{'file':26s} {'unsup_span':>11} {'short_layers':>13} "
          f"{'L1_area':>9} {'aspect':>7} {'overhang_mm':>12}")
    for r in results:
        at = f"@{r['unsupported_span_at_z']}mm" if r["unsupported_span_at_z"] else ""
        print(f"{r['file']:26s} {str(r['unsupported_span_mm']) + 'mm ' + at:>11} "
              f"{r['short_layers']:>13} {r['first_layer_area_mm2']:>9} "
              f"{r['aspect_ratio']:>7} {r['overhang_mm']:>12}")
    print("\nSignals, not predictions. Nothing here models gravity, heat, "
          "adhesion or warping.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
