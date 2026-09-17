#!/usr/bin/env python3
"""
tools/virtual_printer.py -- slice a model the way the P1S would, then report
what the SLICER decided rather than what the geometry looks like.

Scott, 2026-09-13: "build a virtual P1S... so you can see the layer lines, so
you can see where the sauce tray failed."

WHY THIS BEATS THE GEOMETRY CHECKS IT SITS NEXT TO. mesh_gate and product_gate
approximate a slicer with ray casts and face normals, and every one of those
approximations has been wrong at least once here (an overhang scan that flagged
base fillets; a thickness check that measured engraved grooves). This runs the
actual slicer and reads its actual output, so "does this need supports" stops
being an inference and becomes a fact.

CONFIRMED SETUP (Scott, 2026-09-13): stock 0.4mm brass nozzle, one AMS with 4
slots, textured PEI plate, stock 0.20mm Standard profile. He also has tuned
profiles of his own -- ask for them before claiming a time or quality number
matters.

HONEST LIMITS -- say these out loud rather than implying the sim is the printer:
  * This is PrusaSlicer, not Bambu Studio. They share an engine lineage
    (Bambu Studio and Orca are both PrusaSlicer forks), so the geometric
    decisions -- perimeters, overhang classification, bridges, supports -- track
    closely. Speeds and time estimates will NOT match Bambu's.
  * It models nothing thermal. Warping, bed adhesion, stringing, layer
    delamination and heat creep are invisible to it. A part can pass everything
    here and still fail on the plate for a reason this cannot see.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

# Bambu P1S, stock 0.4mm brass, 0.20mm Standard, PLA on textured PEI.
P1S = {
    "layer-height": "0.2", "first-layer-height": "0.2",
    "nozzle-diameter": "0.4", "filament-diameter": "1.75",
    "temperature": "220", "first-layer-temperature": "220",
    "bed-temperature": "55", "first-layer-bed-temperature": "55",
    "perimeters": "2", "top-solid-layers": "5", "bottom-solid-layers": "4",
    "fill-density": "15%", "fill-pattern": "grid",
    "support-material-threshold": "45",
    "bridge-flow-ratio": "1", "extrusion-width": "0.42",
    "bed-shape": "0x0,256x0,256x256,0x256", "max-print-height": "256",
}


# Multi-material, for a 3MF that already carries a per-part extruder (which is
# what tools/assemble_3mf.py writes into Metadata/Slic3r_PE_model.config).
# Two findings from getting a real 5-filament slice out of PrusaSlicer 2.7.2,
# both non-obvious and both verified here on 2026-09-17:
#   * The wipe tower REQUIRES relative E. Without it the slice refuses outright
#     with "The Wipe Tower is currently only supported with the relative
#     extruder addressing".
#   * Priming must be OFF. With it on, the priming block emitted 304 lines of
#     "G1 X-40263464.000" -- a garbage coordinate, not a real move. Turning it
#     off removed every one of them.
# The time estimate on an MMU slice is ALSO unreliable: it came back as
# "-2147483648s". gcode_viewer_data._seconds rejects that rather than passing
# it on, and the viewer falls back to its own measured sum.
MMU = {
    "single-extruder-multi-material": "1",
    "single-extruder-multi-material-priming": "0",
    "wipe-tower": "1", "wipe-tower-x": "180", "wipe-tower-y": "140",
    "use-relative-e-distances": "1",
}


def mmu_options(n_extruders):
    """Per-extruder settings PrusaSlicer wants as comma lists, n copies each."""
    per = {"nozzle-diameter": "0.4", "filament-diameter": "1.75",
           "temperature": "220", "first-layer-temperature": "220"}
    opts = dict(MMU)
    opts.update({k: ",".join([v] * n_extruders) for k, v in per.items()})
    return opts


class VirtualPrinterError(Exception):
    pass


def slice_model(mesh_path, gcode_path, supports=True, extra=None, timeout=1800):
    exe = shutil.which("prusa-slicer") or shutil.which("prusa-slicer-console")
    if not exe:
        raise VirtualPrinterError(
            "prusa-slicer is not installed (apt-get install -y prusa-slicer). "
            "It is the slicing engine this stands on -- without it there is "
            "nothing to read.")
    mesh_path, gcode_path = Path(mesh_path), Path(gcode_path)
    if not mesh_path.exists():
        raise VirtualPrinterError(f"mesh not found: {mesh_path}")
    gcode_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [exe, "--export-gcode"]
    # `--key=value`, not `--key value`: PrusaSlicer's boolean switches
    # (single-extruder-multi-material, wipe-tower) take no separate argument, so
    # the spaced form made the slicer read the "1" as a second input file and
    # fail with "No such file: 1". The = form is accepted for every option.
    for k, v in {**P1S, **(extra or {})}.items():
        cmd.append(f"--{k}={v}")
    if supports:
        cmd.append("--support-material")
    cmd += ["-o", str(gcode_path), str(mesh_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout)
    if not gcode_path.exists() or gcode_path.stat().st_size == 0:
        raise VirtualPrinterError(
            f"slicing produced nothing (exit {r.returncode}):\n"
            + ((r.stderr or r.stdout or "").strip()[-1500:]))
    return gcode_path


def analyse(gcode_path, model_height=None):
    """Read the slicer's own decisions back out of its G-code."""
    types = Counter()
    layers = 0
    max_z = 0.0
    filament_mm = 0.0
    cur = None
    x = y = z = e = 0.0
    for ln in open(gcode_path, errors="replace"):
        if ln.startswith(";TYPE:"):
            cur = ln[6:].strip(); continue
        if ln.startswith(";LAYER_CHANGE"):
            layers += 1; continue
        if not ln.startswith(("G1", "G0")):
            continue
        d = dict(re.findall(r"([XYZEF])([-\d.]+)", ln))
        nz = float(d.get("Z", z))
        ne = float(d["E"]) if "E" in d else e
        if "E" in d and ne > e:
            filament_mm += ne - e
            types[cur or "?"] += 1
            max_z = max(max_z, nz)
        x, y, z, e = float(d.get("X", x)), float(d.get("Y", y)), nz, ne
    vol_mm3 = filament_mm * 3.14159 * (1.75 / 2) ** 2
    out = {
        "layers": layers, "printed_height_mm": round(max_z, 2),
        "filament_mm": round(filament_mm, 1),
        "filament_g": round(vol_mm3 * 1.24 / 1000, 1),      # PLA 1.24 g/cm3
        "moves_by_type": dict(types.most_common()),
        "support_moves": types.get("Support material", 0)
                         + types.get("Support material interface", 0),
        "overhang_perimeters": types.get("Overhang perimeter", 0),
        "bridges": types.get("Bridge infill", 0),
    }
    if model_height:
        lost = model_height - max_z
        out["height_shortfall_mm"] = round(lost, 2)
        # More than one layer missing means the slicer DROPPED geometry -- a
        # feature thinner than it could represent simply is not in the G-code.
        out["geometry_dropped"] = lost > 0.25
    return out


def report(mesh_path, gcode_path=None, supports=True):
    import trimesh
    m = trimesh.load(mesh_path, force="mesh")
    gcode_path = Path(gcode_path or Path(mesh_path).with_suffix(".gcode"))
    slice_model(mesh_path, gcode_path, supports=supports)
    a = analyse(gcode_path, model_height=float(m.extents[2]))
    a["model_height_mm"] = round(float(m.extents[2]), 2)
    a["verdicts"] = []
    if a["support_moves"]:
        a["verdicts"].append(
            f"NEEDS SUPPORTS -- {a['support_moves']} support moves. For a retail "
            f"piece that means scarring where they break off.")
    if a["overhang_perimeters"]:
        a["verdicts"].append(
            f"{a['overhang_perimeters']} overhang perimeters: the slicer printed "
            f"that many wall segments into air.")
    if a.get("geometry_dropped"):
        a["verdicts"].append(
            f"GEOMETRY DROPPED -- model is {a['model_height_mm']}mm, the G-code only "
            f"reaches {a['printed_height_mm']}mm. A feature was too thin to survive.")
    if not a["verdicts"]:
        a["verdicts"].append("clean -- no supports, no overhang perimeters, full height")
    return a


def _cli():
    import argparse, json
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("mesh")
    ap.add_argument("-g", "--gcode")
    ap.add_argument("--no-supports", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        r = report(a.mesh, a.gcode, supports=not a.no_supports)
    except VirtualPrinterError as exc:
        print(f"ERROR: {exc}", file=sys.stderr); raise SystemExit(2)
    if a.json:
        print(json.dumps(r, indent=2)); raise SystemExit(0)
    print(f"{a.mesh}")
    print(f"  {r['layers']} layers, {r['printed_height_mm']}mm printed of "
          f"{r['model_height_mm']}mm modelled, {r['filament_g']}g PLA")
    for k, v in r["moves_by_type"].items():
        print(f"    {k}: {v:,}")
    for v in r["verdicts"]:
        print(f"  -> {v}")
    raise SystemExit(0)


if __name__ == "__main__":
    _cli()
