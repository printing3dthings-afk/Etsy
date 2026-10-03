#!/usr/bin/env python3
"""
tools/colour_cost.py -- what each colour costs to print, measured by slicing
with Bambu Studio's stock P1S presets.

    python3 tools/colour_cost.py --part body.stl:#77716B --part roof.stl:#2B2F38 ...
    python3 tools/colour_cost.py ... --what-if      # also re-slice with each colour dropped

WHY (2026-10-03). The haunted chapel is 100 g of plastic. Bambu Studio's
slice of it uses 441 g and 32.1 h: 1,007 colour changes, each purging
120-530 mm3 depending on the pair (dark slate to cream is the worst at 528).
In one colour the same model is 81 g and 2.8 h. The trim is 7 g of plastic on
517 of 815 layers; the door and cross are 0.7 g on 229. A colour costs per
LAYER it appears on, not per gram, so a small detail spread over the model's
height can cost more printer time than everything else together. None of that
shows in a render or in print_fidelity, so this reports it.

--what-if re-slices once per colour with that colour's parts printed in the
first part's colour, so the saving from dropping or recolouring it is a
measured number, not an estimate.

Numbers are Bambu's stock presets (stock flush volumes, prime tower on, flush
multiplier 1). Scott's tuned presets will differ; the ranking between
colours is what to act on.
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

import trimesh

import assemble_3mf
import bambu_slicer
import print_fidelity

PLA_G_PER_MM3 = 1.26 / 1000     # Bambu PLA Basic's own filament_density


def _slice(parts, work, tag):
    """parts: [(path, '#hex')]. Returns (summary dict, translated gcode path)."""
    src = work / f"{tag}.3mf"
    assemble_3mf.assemble(src, [[(Path(p), c) for p, c in parts]], "assembly", layout="bambu")
    colours = list(dict.fromkeys(c.upper() for _, c in parts))
    gcode = work / f"{tag}.gcode"
    res = bambu_slicer.slice_model(src, gcode, colours=colours)
    plate = res["sliced_plates"][0]
    raw = gcode.with_suffix(".bambu.gcode")
    changes = sum(1 for ln in open(raw, errors="replace")
                  if re.match(r"^\s*T(\d+)\s*$", ln) and int(re.match(r"^\s*T(\d+)", ln).group(1)) < 16)
    return {
        "grams": sum(f["total_used_g"] for f in plate["filaments"]),
        "grams_by_slot": [f["total_used_g"] for f in plate["filaments"]],
        "hours": plate["total_predication"] / 3600,
        "colour_changes": changes,
        "colours": colours,
    }, gcode


def report(parts, what_if=False, log=print):
    with tempfile.TemporaryDirectory(prefix="colour_cost_") as td:
        work = Path(td)
        base, gcode = _slice(parts, work, "as_designed")
        colours = base["colours"]
        model_g = Counter()
        for p, c in parts:
            model_g[c.upper()] += trimesh.load(p, force="mesh").volume * PLA_G_PER_MM3
        layers = print_fidelity.parse_gcode(gcode)
        span = Counter(t for L in layers for t in {t for (t, _w) in L["beads"]})
        out = {"as_designed": base, "layers": len(layers), "per_colour": []}
        for i, c in enumerate(colours):
            out["per_colour"].append({
                "colour": c,
                "parts": [Path(p).stem for p, pc in parts if pc.upper() == c],
                "model_g": round(model_g[c], 1),
                "used_g": round(base["grams_by_slot"][i], 1),
                "layers": span.get(i, 0),
            })
        if what_if and len(colours) > 1:
            first = colours[0]
            for c in colours[1:]:
                log(f"  re-slicing with {c} printed as {first} ...")
                alt = [(p, first if pc.upper() == c else pc) for p, pc in parts]
                r, _ = _slice(alt, work, f"without_{c[1:]}")
                for row in out["per_colour"]:
                    if row["colour"] == c:
                        row["drop_saves_h"] = round(base["hours"] - r["hours"], 2)
                        row["drop_saves_g"] = round(base["grams"] - r["grams"], 1)
            mono, _ = _slice([(p, first) for p, _ in parts], work, "one_colour")
            out["one_colour"] = {"grams": round(mono["grams"], 1), "hours": round(mono["hours"], 2)}
        return out


def print_report(r):
    b = r["as_designed"]
    model = sum(row["model_g"] for row in r["per_colour"])
    print(f"\nCOLOUR COST  (Bambu Studio stock P1S, {r['layers']} layers)")
    print(f"  as designed: {b['grams']:.1f} g filament for {model:.1f} g if the model were solid, "
          f"{b['hours']:.2f} h, {b['colour_changes']} colour changes")
    if "one_colour" in r:
        o = r["one_colour"]
        print(f"  in one colour: {o['grams']} g, {o['hours']} h")
    print(f"  {'colour':9s} {'solid g':>8s} {'used g':>7s} {'layers':>7s} "
          f"{'drop saves':>14s}  parts")
    for row in r["per_colour"]:
        saves = (f"{row['drop_saves_h']:5.2f} h {row['drop_saves_g']:5.0f} g"
                 if "drop_saves_h" in row else "")
        print(f"  {row['colour']:9s} {row['model_g']:8.1f} {row['used_g']:7.1f} "
              f"{row['layers']:7d} {saves:>14s}  {', '.join(row['parts'])}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--part", action="append", required=True, metavar="PATH:#HEX")
    ap.add_argument("--what-if", action="store_true",
                    help="re-slice once per colour with it printed in the first part's colour")
    a = ap.parse_args(argv)
    if not bambu_slicer.available():
        print("Bambu Studio is not installed -- run tools/install_bambu_studio.sh", file=sys.stderr)
        raise SystemExit(2)
    parts = []
    for spec in a.part:
        path, _, col = spec.rpartition(":")
        parts.append((path, col if col.startswith("#") else "#" + col))
    print_report(report(parts, what_if=a.what_if))


if __name__ == "__main__":
    main()
