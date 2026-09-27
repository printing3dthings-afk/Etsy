#!/usr/bin/env python3
"""
tools/bambu_slicer.py -- slice with Bambu Studio itself, the program Scott
prints from, and hand back G-code the rest of the print checks can read.

Scott, 2026-09-27: "a better slicer program than what you are using". The
checks sliced with PrusaSlicer 2.7.2. This drives Bambu Studio's own command
line with Bambu's own stock P1S presets instead. tools/virtual_printer.py
prefers it and falls back to PrusaSlicer when it is not installed.

INSTALL (the container is ephemeral, so every new session repeats this):
    tools/install_bambu_studio.sh
Bambu's GitHub release assets are not reachable from these sessions (the
session proxy refuses github.com release downloads; git clone of the public
repo does work, binaries do not), so it comes from Flathub:
com.bambulab.BambuStudio, ~1.4 GB installed. `flatpak run` needs a system
D-Bus the container does not have, so the binary is run directly under
bubblewrap with the Flatpak runtime mounted at /usr and the app at /app --
the same layout Flatpak itself builds.

FOUR THINGS THAT FAIL SILENTLY, each found and verified on 2026-09-27:
  * The CLI does not resolve a preset's `inherits` chain. Pointed at the
    stock "Bambu Lab P1S 0.4 nozzle.json" it sliced on a 200x200 bed with no
    nozzle temperature and still returned "Success". So every preset is
    flattened here, parent first, before the slicer sees it. The flattened
    file keeps "from": "system" -- the CLI checks process/printer
    compatibility by NAME for system presets, and a "User" preset without
    `inherits` is refused as incompatible.
  * A filament preset with no filament_colour makes the CLI build a
    one-entry colour list however many filaments are loaded. Filament 2+
    then maps to no extruder and every part assigned to it is silently left
    out of the G-code (a two-part test printed half its height). Each slot
    gets its own colour here.
  * Bambu Studio builds parts only from a 3MF's <components>. A single mesh
    with triangle ranges (the layout PrusaSlicer needs, and what
    assemble_3mf wrote by default) loads as ONE part on filament 1 -- the
    chapel sliced as 81 g of one colour. Hand this the "bambu" layout from
    assemble_3mf.assemble(..., layout="bambu").
  * The stock process has arc fitting on (29,855 G2/G3 arcs on the chapel)
    and every G-code reader here follows G0/G1 only. It is turned off for
    these slices: the toolpath is the same, written as straight segments.

The G-code is translated into PrusaSlicer's comment dialect (;LAYER_CHANGE,
;Z:, ;HEIGHT:, ;TYPE:, ;WIDTH:) with Bambu's feature names mapped onto
PrusaSlicer's, so print_fidelity, gcode_viewer_data, gcode_to_mesh and
virtual_printer.analyse read it unchanged. Bambu's untranslated file is kept
next to it as <name>.bambu.gcode.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from functools import lru_cache
from pathlib import Path

APP_ID = "com.bambulab.BambuStudio"

# Scott's confirmed setup (virtual_printer docstring): stock 0.4 brass,
# 0.20mm Standard, PLA, textured PEI. "0.20mm Standard @BBL X1C" is the name
# Bambu itself gives the P1S's standard process -- it lists the P1S 0.4 in
# its compatible_printers; there is no "@BBL P1S" process file.
MACHINE = "Bambu Lab P1S 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL X1C"
FILAMENT = "Bambu PLA Basic @BBL P1S 0.4 nozzle"

PROCESS_OVERRIDES = {
    "enable_arc_fitting": "0",          # see the docstring: readers follow G1 only
    "curr_bed_type": "Textured PEI Plate",
}

# Bambu feature name -> the PrusaSlicer name every reader here keys on.
# A name not listed passes through unchanged (gcode_viewer_data files it
# under "Other", print_fidelity counts it as part unless it is in NOT_PART).
FEATURES = {
    "Outer wall": "External perimeter",
    "Inner wall": "Perimeter",
    "Overhang wall": "Overhang perimeter",
    "Sparse infill": "Internal infill",
    "Internal solid infill": "Solid infill",
    "Bottom surface": "Solid infill",
    "Floating vertical shell": "Solid infill",
    "Top surface": "Top solid infill",
    "Bridge": "Bridge infill",
    "Internal Bridge": "Bridge infill",
    "Gap infill": "Gap fill",
    "Ironing": "Ironing",
    "Skirt": "Skirt/Brim",
    "Brim": "Skirt/Brim",
    "Support": "Support material",
    "Support transition": "Support material",
    "Support interface": "Support material interface",
    "Prime tower": "Wipe tower",
    "Custom": "Custom",
}

# Distinct greys for filament slots when the caller has no real colours: the
# slicer only needs them to differ, nothing here reads them back.
_FALLBACK_COLOURS = ["#808080", "#404040", "#C0C0C0", "#202020", "#A0A0A0",
                     "#606060", "#E0E0E0", "#303030"]


class BambuSlicerError(Exception):
    pass


def _flatpak_location(ref):
    exe = shutil.which("flatpak")
    if not exe:
        return None
    r = subprocess.run([exe, "info", "--show-location", ref],
                       capture_output=True, text=True)
    loc = r.stdout.strip()
    return Path(loc) / "files" if r.returncode == 0 and loc else None


def _runtime_ref(app_files):
    """The runtime the app was built against, from the app's own metadata."""
    meta = app_files.parent / "metadata"
    m = re.search(r"^runtime=(\S+)", meta.read_text(), re.M) if meta.exists() else None
    if not m:
        return None
    name, _arch, branch = m.group(1).split("/")
    return f"{name}//{branch}"


def locate():
    """(app_files, runtime_files) or None when Bambu Studio is not installed.
    BAMBU_STUDIO_APP / BAMBU_STUDIO_RUNTIME override the Flatpak lookup."""
    app = os.environ.get("BAMBU_STUDIO_APP")
    rt = os.environ.get("BAMBU_STUDIO_RUNTIME")
    if app and rt:
        return Path(app), Path(rt)
    app_files = _flatpak_location(APP_ID)
    if not app_files or not shutil.which("bwrap"):
        return None
    ref = _runtime_ref(app_files)
    rt_files = _flatpak_location(ref) if ref else None
    if not rt_files:
        return None
    return app_files, rt_files


def available():
    return locate() is not None


def _command(app_files, rt_files):
    return ["bwrap", "--bind", "/", "/", "--ro-bind", str(rt_files), "/usr",
            "--ro-bind", str(app_files), "/app", "--dev", "/dev", "--proc", "/proc",
            "--setenv", "LC_ALL", "C.UTF-8", "--setenv", "LD_LIBRARY_PATH", "/app/lib",
            "--", "/app/bin/bambu-studio"]


@lru_cache(maxsize=1)
def version():
    loc = locate()
    if not loc:
        return None
    # Run in a scratch directory: the CLI writes a result.json into its working
    # directory even for --help.
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run(_command(*loc) + ["--help"], capture_output=True, text=True,
                           errors="replace", timeout=120, cwd=td)
    m = re.search(r"BambuStudio-([\d.]+)", r.stdout + r.stderr)
    return m.group(1) if m else None


def flatten_preset(profiles_dir, kind, name):
    """A stock preset with its whole `inherits` chain merged in, parent first."""
    chain, seen = [], set()
    while name:
        if name in seen:
            raise BambuSlicerError(f"inherits loop at {kind}/{name}")
        seen.add(name)
        path = Path(profiles_dir) / kind / f"{name}.json"
        if not path.exists():
            raise BambuSlicerError(f"stock preset not found: {path}")
        d = json.loads(path.read_text())
        chain.append(d)
        name = d.get("inherits", "")
    merged = {}
    for d in reversed(chain):
        # `include` pulls in template files beside the preset -- the P1S's
        # real start, end and filament-change G-code live there. Without them
        # the slice carried fdm_machine_common's generic start G-code.
        for inc in d.get("include", []):
            ipath = Path(profiles_dir) / kind / f"{inc}.json"
            if not ipath.exists():
                raise BambuSlicerError(f"included preset not found: {ipath}")
            merged.update({k: v for k, v in json.loads(ipath.read_text()).items()
                           if k not in ("name", "instantiation")})
        merged.update(d)
    merged.pop("inherits", None)
    merged.pop("include", None)
    return merged


def write_presets(workdir, app_files, colours, layer_height=None, supports=False):
    """Flatten the stock presets into workdir; return (settings_arg, filaments_arg)."""
    profiles = app_files / "share" / "BambuStudio" / "profiles" / "BBL"
    workdir = Path(workdir)
    machine = flatten_preset(profiles, "machine", MACHINE)
    process = flatten_preset(profiles, "process", PROCESS)
    process.update(PROCESS_OVERRIDES)
    process["enable_support"] = "1" if supports else "0"
    if layer_height:
        process["layer_height"] = str(layer_height)
    filament = flatten_preset(profiles, "filament", FILAMENT)
    m, p = workdir / "bambu_machine.json", workdir / "bambu_process.json"
    m.write_text(json.dumps(machine, indent=1))
    p.write_text(json.dumps(process, indent=1))
    fils = []
    for i, colour in enumerate(colours):
        f = workdir / f"bambu_filament_{i + 1}.json"
        f.write_text(json.dumps(dict(filament, filament_colour=[colour]), indent=1))
        fils.append(str(f))
    return f"{m};{p}", ";".join(fils)


def filament_count(model_path):
    """Filament slots a model needs: 1 for a mesh, the highest extruder a 3MF
    assigns otherwise."""
    model_path = Path(model_path)
    if model_path.suffix.lower() != ".3mf":
        return 1
    with zipfile.ZipFile(model_path) as z:
        text = ""
        for n in ("Metadata/model_settings.config", "Metadata/Slic3r_PE_model.config"):
            if n in z.namelist():
                text += z.read(n).decode("utf-8", "replace")
    ex = [int(v) for v in re.findall(r'key="extruder" value="(\d+)"', text)]
    return max(ex) if ex else 1


_LAYER = "; CHANGE_LAYER"
_AXIS = re.compile(r"([XY])([-+]?\d*\.?\d+)")
_TOOL = re.compile(r"T(\d+)\s*(?:;|$)")
MAX_SLOTS = 16          # four AMS units of four


def extruder_offset(gcode_path):
    """The machine's extruder_offset from Bambu's own config block."""
    with open(gcode_path, "r", errors="replace") as fh:
        for line in fh:
            if line.startswith("; extruder_offset = "):
                x, _, y = line.split("=", 1)[1].split(";")[0].strip().partition("x")
                return float(x), float(y)
    return 0.0, 0.0


def translate_gcode(src, dst, header=None, offset=(0.0, 0.0)):
    """Bambu Studio's comment dialect -> PrusaSlicer's, with absolute XY moved
    by `offset` into plate coordinates.

    The offset (2026-09-27): the P1S profile carries extruder_offset = 0x2, and
    Bambu writes every Y 2 mm below where the part sits on the plate -- a
    20 mm cube Bambu reports at y 118-138 is printed at 116-136. The readers
    here compare the toolpath with the model on the plate, so the translated
    file is in plate coordinates; Bambu's own file keeps what the printer is
    sent."""
    ox, oy = offset
    shift = ox != 0.0 or oy != 0.0
    absolute = True

    def _move(m):
        v = float(m.group(2)) + (ox if m.group(1) == "X" else oy)
        return f"{m.group(1)}{v:.3f}"

    with open(src, "r", errors="replace") as fi, open(dst, "w") as fo:
        if header:
            fo.write(header.rstrip("\n") + "\n")
        for line in fi:
            # Bambu's start G-code indents the commands inside its M620 blocks,
            # including the first `T<n>`; every reader here matches commands at
            # column 0, so the chapel's first layer was read as printed on slot
            # 0 when it began on the trim's slot 2 (2026-09-27).
            if line[:1] in (" ", "\t"):
                stripped = line.lstrip()
                if stripped[:1] in ("G", "M", "T"):
                    line = stripped
            # T255 unloads to the AMS and T1000 is a nozzle-load code in the P1S
            # start G-code; neither is a filament slot (the AMS tops out at 16),
            # and read as one they put the whole print on a slot that does not
            # exist -- the calibration block came back 2,080 mm3 "wrong colour".
            m = _TOOL.match(line)
            if m and int(m.group(1)) >= MAX_SLOTS:
                fo.write(f"; {line.strip()} (Bambu control code, not a filament slot)\n")
                continue
            if shift and line[0] == "G":
                if line.startswith("G90"):
                    absolute = True
                elif line.startswith("G91"):
                    absolute = False
                elif absolute and line.startswith(("G0 ", "G1 ")):
                    code, sep, comment = line.partition(";")
                    line = _AXIS.sub(_move, code) + sep + comment
                    if not line.endswith("\n"):
                        line += "\n"
            if line.startswith("; "):
                if line.startswith(_LAYER):
                    fo.write(";LAYER_CHANGE\n"); continue
                if line.startswith("; Z_HEIGHT:"):
                    fo.write(f";Z:{line[11:].strip()}\n"); continue
                if line.startswith("; LAYER_HEIGHT:"):
                    fo.write(f";HEIGHT:{line[15:].strip()}\n"); continue
                if line.startswith("; FEATURE:"):
                    name = line[10:].strip()
                    fo.write(f";TYPE:{FEATURES.get(name, name)}\n"); continue
                if line.startswith("; LINE_WIDTH:"):
                    fo.write(f";WIDTH:{line[13:].strip()}\n"); continue
            fo.write(line)
    return Path(dst)


def slice_model(model_path, gcode_path, supports=False, layer_height=None, colours=None,
          timeout=1800):
    """Slice with Bambu Studio's stock P1S presets. Writes Prusa-dialect G-code
    to gcode_path (and Bambu's own beside it) and returns the slicer's summary."""
    loc = locate()
    if not loc:
        raise BambuSlicerError(
            "Bambu Studio is not installed -- run tools/install_bambu_studio.sh")
    app_files, rt_files = loc
    model_path, gcode_path = Path(model_path).resolve(), Path(gcode_path).resolve()
    if not model_path.exists():
        raise BambuSlicerError(f"model not found: {model_path}")
    n = filament_count(model_path)
    colours = list(colours or [])
    if len(colours) < n:
        colours += [c for c in _FALLBACK_COLOURS if c not in colours][: n - len(colours)]
    gcode_path.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="bambu_slice_", dir=gcode_path.parent))
    try:
        settings, filaments = write_presets(work, app_files, colours[:max(n, 1)],
                                            layer_height=layer_height, supports=supports)
        out = work / "out"
        cmd = _command(app_files, rt_files) + [
            "--debug", "1", "--slice", "0", "--outputdir", str(out),
            "--load-settings", settings, "--load-filaments", filaments, str(model_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                           timeout=timeout)
        result = {}
        if (out / "result.json").exists():
            result = json.loads((out / "result.json").read_text())
        plate = out / "plate_1.gcode"
        if r.returncode != 0 or result.get("return_code", -1) != 0 or not plate.exists():
            raise BambuSlicerError(
                f"Bambu Studio did not slice {model_path.name} (exit {r.returncode}): "
                f"{result.get('error_string') or (r.stderr or r.stdout).strip()[-1500:]}")
        raw = gcode_path.with_suffix(".bambu.gcode")
        shutil.move(str(plate), raw)
        off = extruder_offset(raw)
        translate_gcode(raw, gcode_path, offset=off, header=(
            f"; virtual_printer slicer = BambuStudio {version() or '?'} "
            f"({MACHINE} / {PROCESS} / {FILAMENT}; arc fitting off; "
            f"XY shifted by extruder_offset {off[0]:g}x{off[1]:g} into plate coordinates)"))
        return result
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--check"]:
        v = version()
        print(f"Bambu Studio {v}" if v else "Bambu Studio is NOT usable here")
        raise SystemExit(0 if v else 1)
    if len(sys.argv) != 3:
        print("usage: bambu_slicer.py MODEL.stl|MODEL.3mf OUT.gcode   |   --check")
        raise SystemExit(2)
    print(json.dumps(slice_model(sys.argv[1], sys.argv[2]), indent=1))
