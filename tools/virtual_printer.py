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
  * Since 2026-09-27 the slicer is Bambu Studio itself (tools/bambu_slicer.py)
    with Bambu's STOCK P1S presets, when it is installed; PrusaSlicer 2.7 is the
    fallback, and its speeds and times do not match Bambu's. Stock is not
    Scott's tuned profile -- until he exports his preset bundle, a number that
    depends on tuning (time, seam, wall generator) is Bambu's default, not his.
    Stock 0.20mm Standard uses the CLASSIC wall generator, not Arachne, so thin
    features print differently from the PrusaSlicer slices these checks were
    first calibrated on.
  * It models nothing thermal. Warping, bed adhesion, stringing, layer
    delamination and heat creep are invisible to it. A part can pass everything
    here and still fail on the plate for a reason this cannot see.
"""
from __future__ import annotations

import os
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


def active_slicer():
    """"bambu" or "prusa": what slice_model will run. VIRTUAL_PRINTER_SLICER
    pins one; otherwise Bambu Studio when it is installed, PrusaSlicer if not."""
    want = os.environ.get("VIRTUAL_PRINTER_SLICER", "auto").lower()
    if want in ("bambu", "prusa"):
        return want
    import bambu_slicer
    return "bambu" if bambu_slicer.available() else "prusa"


# PrusaSlicer option names the callers pass that Bambu Studio's stock presets
# already cover (P1S geometry, the MMU wipe-tower workarounds) and so are not
# forwarded. Anything else in `extra` must be translated below or refused --
# silently dropping a setting would slice something other than what was asked.
_BAMBU_COVERED = set(P1S) | set(MMU) | {"nozzle-diameter", "filament-diameter",
                                         "temperature", "first-layer-temperature"}


def slice_model(mesh_path, gcode_path, supports=True, extra=None, timeout=1800,
                colours=None):
    """Slice to gcode_path in PrusaSlicer's comment dialect, whichever slicer
    runs. `colours`: one hex per filament slot (Bambu only; the slicer needs
    distinct filaments, nothing reads the colours back)."""
    mesh_path, gcode_path = Path(mesh_path), Path(gcode_path)
    if not mesh_path.exists():
        raise VirtualPrinterError(f"mesh not found: {mesh_path}")
    gcode_path.parent.mkdir(parents=True, exist_ok=True)
    if active_slicer() == "bambu":
        run = _bambu_runner(mesh_path, gcode_path, supports, extra, timeout, colours)
    else:
        run = _prusa_runner(mesh_path, gcode_path, supports, extra, timeout)
    # Re-slice on junk (2026-09-27). On multi-filament plates PrusaSlicer 2.7
    # intermittently writes coordinates like X-877672384 into the wipe-tower
    # tool changes: the same 3MF with the same options gave 4,153 junk moves in
    # one run and none in the next, and the cemetery 58 then none three times
    # running. A printer handed that file would try to travel 877 km, so a
    # junk slice is never returned -- it is retried, then refused. Kept for
    # Bambu Studio too: nothing has shown it does this, nothing has shown it
    # cannot.
    for attempt in range(3):
        gcode_path.unlink(missing_ok=True)
        run()
        if not gcode_path.exists() or gcode_path.stat().st_size == 0:
            raise VirtualPrinterError(f"slicing produced nothing for {mesh_path}")
        junk = off_bed_moves(gcode_path)
        if not junk:
            return gcode_path
    raise VirtualPrinterError(
        f"{gcode_path}: the slicer wrote {junk} off-bed moves on 3 attempts running; "
        "this G-code is not a real plate")


def _bambu_runner(mesh_path, gcode_path, supports, extra, timeout, colours):
    import bambu_slicer
    extra = dict(extra or {})
    layer_height = extra.pop("layer-height", None)
    centre = extra.pop("center", None)
    # Bambu Studio has no --center; it places a lone model at the middle of
    # the plate, which is exactly the one centre the callers ask for.
    if centre and centre.replace(" ", "") not in ("128,128", "128.0,128.0"):
        raise VirtualPrinterError(
            f"Bambu Studio slices centred on the plate (128,128); centre={centre} "
            "cannot be honoured")
    unknown = sorted(k for k in extra if k not in _BAMBU_COVERED)
    if unknown:
        raise VirtualPrinterError(
            f"no Bambu Studio equivalent wired up for {unknown}; set "
            "VIRTUAL_PRINTER_SLICER=prusa to slice with these")

    def run():
        try:
            bambu_slicer.slice_model(mesh_path, gcode_path, supports=supports,
                                     layer_height=layer_height, colours=colours,
                                     timeout=timeout)
        except bambu_slicer.BambuSlicerError as exc:
            raise VirtualPrinterError(str(exc)) from exc
    return run


def _prusa_runner(mesh_path, gcode_path, supports, extra, timeout):
    exe = shutil.which("prusa-slicer") or shutil.which("prusa-slicer-console")
    if not exe:
        raise VirtualPrinterError(
            "no slicer installed: tools/install_bambu_studio.sh for Bambu Studio "
            "(preferred), or apt-get install -y prusa-slicer. Without one there is "
            "nothing to read.")
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

    def run():
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                           timeout=timeout)
        if not gcode_path.exists() or gcode_path.stat().st_size == 0:
            raise VirtualPrinterError(
                f"slicing produced nothing (exit {r.returncode}):\n"
                + ((r.stderr or r.stdout or "").strip()[-1500:]))
    return run


def slicer_of(gcode_path):
    """Which slicer wrote a G-code file, from its own header."""
    with open(gcode_path, "r", errors="replace") as fh:
        head = "".join(next(fh, "") for _ in range(5))
    if "BambuStudio" in head:
        return "bambu"
    if "PrusaSlicer" in head:
        return "prusa"
    return "unknown"


_XY = re.compile(r"([XY])([-+]?\d*\.?\d+)")


def off_bed_moves(path, limit=400.0):
    """Moves further than `limit` mm from the origin: never a real plate."""
    n = 0
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            if line.startswith(("G0 ", "G1 ")):
                for _, v in _XY.findall(line.split(";", 1)[0]):
                    if abs(float(v)) > limit:
                        n += 1
                        break
    return n


def analyse(gcode_path, model_height=None):
    """Read the slicer's own decisions back out of its G-code."""
    types = Counter()
    layers = 0
    max_z = 0.0
    filament_mm = 0.0
    cur = None
    x = y = z = e = 0.0
    rel = False
    # Filament counts only what goes past the retraction still owed. Two fixes
    # met here:
    #   2026-09-30: summing every rise in E counted each unretract after a
    #     G92 E0 again -- 117 g for a model PrusaSlicer put at 58.9 cm3 (73 g).
    #   2026-09-27: Bambu Studio always writes relative E (M83), and so does
    #     PrusaSlicer's wipe-tower mode; read as absolute, E was nonsense.
    # One debt counter covers both: a retraction adds to it, the next pushes
    # pay it off before anything counts as new filament.
    owed = 0.0
    slicer_g = None
    for ln in open(gcode_path, errors="replace"):
        if ln.startswith(";TYPE:"):
            cur = ln[6:].strip(); continue
        if ln.startswith(";LAYER_CHANGE"):
            layers += 1; continue
        if ln.startswith("; filament used [cm3]"):           # PrusaSlicer
            slicer_g = float(ln.split("=")[1]) * 1.24; continue
        if ln.startswith("; total filament weight [g]"):     # Bambu Studio
            # Not its "volume [cm^3]" line: on the chapel that read
            # 143046.40 for 180 g, i.e. mm3 under a cm3 label.
            slicer_g = sum(float(v) for v in ln.split(":", 1)[1].split(",") if v.strip())
            continue
        if ln.startswith("M83"):
            rel = True; continue
        if ln.startswith("M82"):
            rel = False; continue
        if ln.startswith("G92"):
            m = re.search(r"E([-\d.]+)", ln)
            if m:
                e = float(m.group(1))
            continue
        if not ln.startswith(("G1", "G0")):
            continue
        d = dict(re.findall(r"([XYZEF])([-\d.]+)", ln.split(";", 1)[0]))
        nz = float(d.get("Z", z))
        de = 0.0
        if "E" in d:
            de = float(d["E"]) if rel else float(d["E"]) - e
            if not rel:
                e = float(d["E"])
        if de < 0:
            owed -= de
        elif de > 0:
            new = de - owed
            owed = max(0.0, -new)
            if new > 0:
                filament_mm += new
            types[cur or "?"] += 1
            max_z = max(max_z, nz)
        x, y, z = float(d.get("X", x)), float(d.get("Y", y)), nz
    grams = slicer_g if slicer_g is not None else \
        filament_mm * 3.14159 * (1.75 / 2) ** 2 * 1.24 / 1000   # PLA 1.24 g/cm3
    out = {
        "layers": layers, "printed_height_mm": round(max_z, 2),
        "filament_mm": round(filament_mm, 1),
        "filament_g": round(grams, 1),
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
