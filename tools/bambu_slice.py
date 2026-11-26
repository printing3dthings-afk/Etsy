#!/usr/bin/env python3
"""Slice a model with Bambu Studio itself, for the P1S, to a printer-ready file.

    python3 tools/bambu_slice.py body.stl:#F4F1EA trim.stl:#C8312B + plate.stl:#2B5FA8 \\
        -o model.gcode.3mf --quality fine [--pause-at 4.2]

Scott, 2026-10-24: "I want you to be able to slice to the best print settings
and send to printer." The print checks (virtual_printer, print_fidelity) slice
with PrusaSlicer 2.7; this is the slicer Scott prints from. It writes the
.gcode.3mf the P1S runs, which the bridge (tools/relay/bambu_p1s_bridge.py)
uploads and starts once Scott approves the job in the Action Center.

THE SLICER. Bambu Studio from Flathub (2.8.2.61 to Nov 2026, 2.9.2 since) (GitHub downloads are blocked
from these containers; Flathub is not). `flatpak run` cannot start its
sandbox in a container, so the binary is run directly with the GNOME runtime's
own loader and libraries -- `ensure_installed()` sets this up, and the CLI
runs headless under xvfb.

THE SETTINGS. Bambu's own system profiles for the P1S 0.4 nozzle, flattened
(each profile inherits from parents; the CLI wants complete files):
  machine   Bambu Lab P1S 0.4 nozzle
  process   0.20mm Standard / 0.12mm Fine / 0.08mm Extra Fine @BBL X1C
            (the X1C processes list the P1S 0.4 as compatible)
  filament  Bambu PLA Basic @BBL P1S 0.4 nozzle, one per colour slot
with the shop's production-quality settings over them (CLAUDE.md, "Production
Quality Settings"): outer wall 50 mm/s at 5,000 mm/s², outer wall first,
Arachne walls, precise wall, aligned seam, avoid crossing walls, ironing on
top surfaces. Supports stay OFF: every model here is designed support-free and
checked to be, and a support the slicer decides to add is a defect to fix in
the model, not something to print around.

HANDY (2026-11-17). Every slice is passed through Bambu Studio a second time from
its own project file, and given plate thumbnails (`finish_for_handy`), so the plate
lists its objects as a GUI-saved file does. Without that, Bambu Handy's cloud slicer
failed on our files (0500-4014, Benson, 2026-11-15). tools/handy_finish.py does the
same to a file sliced before this.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

FLATPAK_APP = Path("/var/lib/flatpak/app/com.bambulab.BambuStudio/current/active/files")
FLATPAK_RT_ROOT = Path("/var/lib/flatpak/runtime/org.gnome.Platform/x86_64")
PROFILES = FLATPAK_APP / "share/BambuStudio/profiles/BBL"

MACHINE = "Bambu Lab P1S 0.4 nozzle"
PROCESS = {
    "standard": "0.20mm Standard @BBL X1C",
    "fine": "0.12mm Fine @BBL X1C",
    "extra_fine": "0.08mm Extra Fine @BBL X1C",
}
FILAMENTS = {"pla_basic": "Bambu PLA Basic @BBL P1S 0.4 nozzle",
             # the village builds print in matte white (Scott, 2026-10-24)
             "pla_matte": "Bambu PLA Matte @BBL P1S 0.4 nozzle",
             # Bambu's support material that doesn't bond to PLA (Scott has it, 2026-11-14):
             # the second material for zero-gap two-material joints
             "support_pla": "Bambu Support For PLA @BBL X1C"}

# CLAUDE.md "Production Quality Settings" -- the shop's own retail standard.
# "Customers only see the outside": the outer wall is slowed and printed first.
BEDS = {"textured": "Textured PEI Plate", "smooth": "High Temp Plate", "cool": "Cool Plate",
        "engineering": "Engineering Plate"}

RETAIL = {
    "outer_wall_speed": 50,
    "outer_wall_acceleration": 5000,
    "wall_sequence": "outer wall/inner wall",
    "wall_generator": "arachne",
    "precise_outer_wall": 1,
    "seam_position": "aligned",
    "reduce_crossing_wall": 1,
    "ironing_type": "top",
    "enable_support": 0,
    # Scott, 2026-11-12: "3 walls and 15% infill is how our prints are set in the
    # slicer." Bambu's stock process is 2 walls, so until 2026-11-18 every slice
    # this made (and every time and weight quoted from one) was a 2-wall print.
    "wall_loops": 3,
    "sparse_infill_density": "15%",
}


# Scott, 2026-11-18, for the Urban Kid: "a split print and a solid one piece with tree
# supports". A figure posed as a person (chin, elbows, cap brim) can't be printed whole
# without support, so `--supports tree` is the one deliberate exception to the
# supports-off rule above. Organic trees reach round the figure from the plate and
# break away cleanly; 0.2 mm gap and two interface layers under each overhang.
TREE_SUPPORTS = {
    "enable_support": 1,
    "support_type": "tree(auto)",
    "support_style": "tree_organic",
    "support_threshold_angle": 30,
    "support_top_z_distance": 0.2,
    "support_interface_top_layers": 2,
}


def ensure_installed() -> None:
    """Install Bambu Studio from Flathub if this container doesn't have it."""
    if not (FLATPAK_APP / "bin/bambu-studio").exists():
        if not shutil.which("flatpak"):
            subprocess.run(["apt-get", "install", "-y", "flatpak"], check=True, capture_output=True)
        subprocess.run(["flatpak", "remote-add", "--if-not-exists", "flathub",
                        "https://dl.flathub.org/repo/flathub.flatpakrepo"], check=True)
        subprocess.run(["flatpak", "install", "-y", "--noninteractive", "flathub",
                        "com.bambulab.BambuStudio"], check=True)
    # Outside its sandbox the binary still looks for its system profiles under
    # /app, where flatpak would have mounted it; without this every process
    # profile reads as "not compatible" with the P1S
    app = Path("/app")
    if not app.exists():
        app.symlink_to(FLATPAK_APP)


def _runtime() -> Path:
    # 2026-11-26: Flathub moved Bambu Studio (2.9.2) onto GNOME runtime 51, and the path this
    # used to hard-code (.../50/) no longer existed on a fresh install: every slice failed with
    # "ld-linux-x86-64.so.2: not found". Use the newest runtime flatpak installed.
    vers = sorted((d for d in FLATPAK_RT_ROOT.glob("*") if (d / "active/files").is_dir()),
                  key=lambda d: int(d.name) if d.name.isdigit() else -1)
    if not vers:
        raise RuntimeError(f"no GNOME runtime under {FLATPAK_RT_ROOT}: run ensure_installed() first")
    return vers[-1] / "active/files"


def _cmd() -> list[str]:
    rt = _runtime()
    loader = rt / "lib/x86_64-linux-gnu/ld-linux-x86-64.so.2"
    libs = f"{FLATPAK_APP / 'lib'}:{rt / 'lib/x86_64-linux-gnu'}:{rt / 'lib'}"
    return ["xvfb-run", "-a", str(loader), "--library-path", libs, str(FLATPAK_APP / "bin/bambu-studio")]


_by_name: dict[str, dict[str, Path]] = {}


def _profile_path(kind: str, name: str) -> Path:
    if kind not in _by_name:
        idx = {}
        for f in glob.glob(str(PROFILES / kind / "*.json")):
            try:
                n = json.loads(Path(f).read_text()).get("name")
            except (OSError, json.JSONDecodeError):
                continue
            if n:
                idx[n] = Path(f)
        _by_name[kind] = idx
    if name not in _by_name[kind]:
        raise KeyError(f"no {kind} profile named {name!r} in {PROFILES / kind}")
    return _by_name[kind][name]


def flatten(kind: str, name: str) -> dict:
    """A profile with its inheritance chain merged in, parent first."""
    d = json.loads(_profile_path(kind, name).read_text())
    parent = d.get("inherits")
    out = flatten(kind, parent) if parent else {}
    out.update(d)
    out.pop("inherits", None)
    return out


def _set(cfg: dict, key: str, value) -> None:
    """Set a value keeping the profile's own shape: some keys are lists, one
    entry per extruder, and a bare value where a list is expected is ignored."""
    cur = cfg.get(key)
    v = str(value)
    cfg[key] = [v] * len(cur) if isinstance(cur, list) else v


def write_profiles(workdir: Path, quality: str, colours: list[str], retail: bool = True,
                   filament: str = "pla_basic", brim: float | None = None,
                   bed: str = "textured", extra: dict | None = None,
                   slot_filaments: dict[int, str] | None = None) -> tuple[str, str]:
    """Write the machine, process and filament files; returns the two CLI args."""
    machine = flatten("machine", MACHINE)
    process = flatten("process", PROCESS[quality])
    if retail:
        for k, v in RETAIL.items():
            _set(process, k, v)
    # 2026-11-12: with no plate type set, Bambu Studio sliced for its Cool Plate, bed
    # 35 C. Scott's plates are PEI, where PLA wants 55 (textured and smooth alike).
    _set(process, "curr_bed_type", BEDS[bed])
    # 2026-11-12: Bambu's auto brim judged the printed 6 mm balls (each on a 3 mm flat)
    # needed none. A forced outer brim is for small footprints like that.
    if brim:
        _set(process, "brim_type", "outer_only")
        _set(process, "brim_width", brim)
    # --set key=value (2026-11-14): any process setting by its Bambu Studio name, for
    # testing a slicer feature (fuzzy skin noise, spiral vase, interlocking beams) from here
    for k, v in (extra or {}).items():
        _set(process, k, v)
    # the prime tower in the corner layout() keeps clear (a project setting the
    # CLI otherwise defaults)
    process["wipe_tower_x"] = [f"{TOWER[0]:.0f}"]
    process["wipe_tower_y"] = [f"{TOWER[1]:.0f}"]
    for cfg in (machine, process):
        cfg["from"] = "system"
    machine_f, process_f = workdir / "machine.json", workdir / "process.json"
    machine_f.write_text(json.dumps(machine, indent=1))
    process_f.write_text(json.dumps(process, indent=1))
    fils = []
    for i, c in enumerate(colours or ["#F4F1EA"]):
        f = flatten("filament", FILAMENTS[(slot_filaments or {}).get(i + 1, filament)])
        f["from"] = "system"
        _set(f, "filament_colour", c.upper())
        p = workdir / f"filament_{i + 1}.json"
        p.write_text(json.dumps(f, indent=1))
        fils.append(str(p))
    return f"{machine_f};{process_f}", ";".join(fils)


def add_pauses(gcode_3mf: Path, pause_zs: list[float]) -> list[float]:
    """Pause the sliced print before each given height, rewriting the plate
    G-code in place: "; PAUSE_PRINT" and the P1S's own machine_pause_gcode
    (M400 U1) right after that layer's layer-change notice, where Bambu Studio
    puts a pause added from its layer slider, then the G-code's md5 updated so
    the printer accepts the file. Returns the layer heights actually paused at.

    Bambu's own route, Metadata/custom_gcode_per_layer.xml in the input 3MF,
    is read only from a 3MF its own generator wrote, and declaring that
    generator on ours crashes the CLI on load (both found 2026-10-24, the
    LELAND plaque's purple-to-white swap at 4.2 mm)."""
    with zipfile.ZipFile(gcode_3mf) as z:
        items = [(it, z.read(it.filename)) for it in z.infolist()]
    data = dict((it.filename, b) for it, b in items)
    gname = next(n for n in data if re.fullmatch(r"Metadata/plate_\d+\.gcode", n))
    lines = data[gname].decode("utf-8").split("\n")
    layer_z = [(k, float(m.group(1))) for k, ln in enumerate(lines)
               if (m := re.fullmatch(r"; Z_HEIGHT: ([0-9.]+)", ln))]
    inserts, done = [], []
    for z in sorted(pause_zs):
        hit = next(((k, lz) for k, lz in layer_z if lz >= z - 1e-6), None)
        if hit is None:
            raise ValueError(f"no layer at or above {z} mm to pause at")
        k = next(n for n in range(hit[0], len(lines)) if lines[n].startswith("M991 S0 P"))
        inserts.append(k + 1)
        done.append(hit[1])
    for k in sorted(inserts, reverse=True):
        lines[k:k] = ["; PAUSE_PRINT", "M400 U1"]
    g = "\n".join(lines).encode("utf-8")
    data[gname] = g
    if gname + ".md5" in data:
        data[gname + ".md5"] = hashlib.md5(g).hexdigest().upper().encode()
    tmp = Path(gcode_3mf).with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for it, _ in items:
            zout.writestr(it, data[it.filename])
    tmp.replace(gcode_3mf)
    return done


def summarise(gcode_3mf: Path) -> dict:
    """What the slice says about itself: time, filament, supports, pauses."""
    with zipfile.ZipFile(gcode_3mf) as z:
        names = z.namelist()
        gname = next((n for n in names if re.fullmatch(r"Metadata/plate_\d+\.gcode", n)), None)
        if not gname:
            raise RuntimeError(f"{gcode_3mf}: no plate G-code inside -- the slice did not produce one")
        g = z.read(gname).decode("utf-8", errors="replace")
    head = g[:200_000]
    out = {"plate_gcode": gname, "layers": g.count("; CHANGE_LAYER"),
           "support_lines": len(re.findall(r"^; FEATURE: Support", g, re.M)),
           "pauses": len(re.findall(r"^M400 U1", g, re.M)),
           # every filament the G-code loads: M620 S<n>A is Bambu's AMS change
           "slots_used": sorted({int(n) + 1 for n in re.findall(r"^M620 S(\d+)A", g, re.M)})}
    # Grams of support: Bambu extrudes relative (M83), so the E of every move inside a
    # Support feature block is filament length; 1.75 mm PLA at 1.24 g/cm³.
    e_sup, in_sup = 0.0, False
    if out["support_lines"]:
        for line in g.splitlines():
            if line.startswith("; FEATURE:"):
                in_sup = line.startswith("; FEATURE: Support")
            elif in_sup and line[:3] in ("G1 ", "G2 ", "G3 "):
                m = re.search(r" E([\d.]+)", line)
                if m:
                    e_sup += float(m.group(1))
    out["support_g"] = round(e_sup * 3.14159 * 0.875 ** 2 * 1.24 / 1000, 1)
    for key, pat in (("time", r"total estimated time: ([^\n;]+)"),
                     ("filament_g", r"total filament weight \[g\] : ([\d.,]+)"),
                     ("filament_mm", r"total filament length \[mm\] : ([\d.,]+)")):
        m = re.search(pat, head)
        if m:
            out[key] = m.group(1).strip()
    return out


def parse_parts(args: list[str]) -> list[list[tuple[Path, str]]]:
    """`mesh.stl:#RRGGBB ... + mesh.stl:#RRGGBB`, as tools/assemble_3mf.py takes them."""
    groups, cur = [], []
    for a in args:
        if a == "+":
            if cur:
                groups.append(cur)
            cur = []
            continue
        path, _, colour = a.partition(":")
        cur.append((Path(path), (colour or "#F4F1EA").upper()))
    if cur:
        groups.append(cur)
    return groups


BED = 256.0
TOWER = (205.0, 205.0)        # prime tower's corner: the back right, out of the objects' way
EXCLUDE = (18.0, 28.0)        # the P1S's bed_exclude_area, front left (the purge corner): an object
                              # placed there fails the slice (2026-11-15, the windlass test plate)
TOWER_SIZE = 35 + 2 * 3 + 6   # width, brim each side, and room for it to grow
GAP = 12.0


def _layout_rows(boxes) -> list[tuple[float, float, float]]:
    """More than one row, when one won't fit (2026-11-15: three birch logs 72-86 mm across
    needed 256 mm in a row). Rows fill front to back, each centred across the plate; the
    front row stays right of the keep-out corner and the back row left of the prime tower."""
    rows, cur, used = [], [], 0.0
    for i, (lo, hi) in enumerate(boxes):
        w = hi[0] - lo[0]
        room = BED - 2 * GAP - (EXCLUDE[0] if not rows else 0)   # the front row loses the keep-out corner
        if cur and used + GAP + w > room:
            rows.append(cur)
            cur, used = [], 0.0
        used += (GAP if cur else 0) + w
        cur.append(i)
    rows.append(cur)
    depths = [max(boxes[i][1][1] - boxes[i][0][1] for i in r) for r in rows]
    if sum(depths) + GAP * (len(rows) + 1) > BED:
        raise ValueError(f"the objects need {sum(depths) + GAP * (len(rows) + 1):.0f} mm front to back; "
                         f"the P1S plate is {BED:.0f}")
    out = [None] * len(boxes)
    y = GAP
    for r, depth in zip(rows, depths):
        widths = [boxes[i][1][0] - boxes[i][0][0] for i in r]
        total = sum(widths) + GAP * (len(r) - 1)
        x = (BED - total) / 2
        if y < EXCLUDE[1] + GAP:                       # the front row: clear of the purge corner
            x = max(x, EXCLUDE[0] + GAP)
            if x + total > BED - GAP:
                raise ValueError("the front row runs into the P1S's front-left keep-out area")
        if y + depth > TOWER[1] - GAP:                 # level with the tower: stay left of it
            x = min(x, TOWER[0] - GAP - total)
            if x < GAP:
                raise ValueError("the back row runs into the prime tower")
        for i, w in zip(r, widths):
            lo, hi = boxes[i]
            out[i] = (x - lo[0], y + depth / 2 - (lo[1] + hi[1]) / 2, -lo[2])
            x += w + GAP
        y += depth + GAP
    return out


def layout(groups: list[list[tuple[Path, str]]]) -> list[tuple[float, float, float]]:
    """Where each object goes: in a row across the middle of the plate, each
    standing on the bed, the prime tower left in the back-right corner.
    Bambu Studio's own --arrange pushed the rocket against the back edge, and
    the prime tower then printed off the plate ("G-code outside the printable
    area", 2026-10-24); placed here, the tower's corner is always clear."""
    import trimesh
    boxes = []
    for g in groups:
        lo = [1e9, 1e9, 1e9]
        hi = [-1e9, -1e9, -1e9]
        for path, _ in g:
            b_lo, b_hi = trimesh.load(path, force="mesh").bounds
            lo = [min(a, c) for a, c in zip(lo, b_lo)]
            hi = [max(a, c) for a, c in zip(hi, b_hi)]
        boxes.append((lo, hi))
    widths = [hi[0] - lo[0] for lo, hi in boxes]
    total = sum(widths) + GAP * (len(widths) - 1)
    if total > BED - 2 * GAP:
        return _layout_rows(boxes)
    x = (BED - total) / 2
    out = []
    for (lo, hi), w in zip(boxes, widths):
        depth = hi[1] - lo[1]
        cy = min(BED / 2, TOWER[1] - GAP - depth / 2) if x + w > TOWER[0] - GAP else BED / 2
        if cy - depth / 2 < GAP:
            raise ValueError("an object is too deep to fit in front of the prime tower")
        out.append((x - lo[0], cy - (lo[1] + hi[1]) / 2, -lo[2]))
        x += w + GAP
    return out


def build_bambu_3mf(groups: list[list[tuple[Path, str]]], out: Path,
                    object_settings: dict[int, dict[str, str]] | None = None) -> list[str]:
    """A 3MF the way Bambu Studio reads multi-part objects: each part its own
    mesh object, each printed object a component object over its parts, and
    Metadata/model_settings.config giving every part its filament slot.
    Returns the slot colours in slot order.

    The shop's 3MFs (tools/assemble_3mf.py) keep all of an object's parts in
    one mesh, split by triangle ranges -- PrusaSlicer's convention. Bambu
    Studio 2.8 read only the first part of each such object: the rocket
    sliced in white and blue only, its red and yellow parts gone (2026-10-24).
    Colours become slots in first-seen order, the same rule as assemble_3mf."""
    import trimesh
    slots: dict[str, int] = {}
    for g in groups:
        for _, c in g:
            slots.setdefault(c, len(slots) + 1)
    res, build, settings = [], [], []
    oid = 0
    places = layout(groups)
    for gi, g in enumerate(groups):
        part_ids, part_cfg = [], []
        for path, colour in g:
            m = trimesh.load(path, force="mesh")
            oid += 1
            v = "".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in m.vertices)
            t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
            res.append(f'<object id="{oid}" type="model"><mesh><vertices>{v}</vertices>'
                       f'<triangles>{t}</triangles></mesh></object>')
            part_ids.append(oid)
            name = path.stem
            part_cfg.append(f'<part id="{oid}" subtype="normal_part"><metadata key="name" value="{name}"/>'
                            f'<metadata key="extruder" value="{slots[colour]}"/></part>')
        oid += 1
        comps = "".join(f'<component objectid="{p}"/>' for p in part_ids)
        res.append(f'<object id="{oid}" type="model"><components>{comps}</components></object>')
        dx, dy, dz = places[gi]
        build.append(f'<item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 {dx:.4f} {dy:.4f} {dz:.4f}" printable="1"/>')
        first = g[0][0].stem
        # --object-set (2026-11-14): settings for this object only, as Bambu Studio
        # stores a per-object override (one texture per swatch on a sampler plate)
        own = "".join(f'<metadata key="{k}" value="{v}"/>' for k, v in (object_settings or {}).get(gi + 1, {}).items())
        settings.append(f'<object id="{oid}"><metadata key="name" value="{first}"/>'
                        f'<metadata key="extruder" value="{slots[g[0][1]]}"/>' + own + "".join(part_cfg) + "</object>")
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources>{"".join(res)}</resources><build>{"".join(build)}</build></model>')
    ctypes = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ctypes)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("Metadata/model_settings.config",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>' + "".join(settings) + "</config>")
    return list(slots)


def slice_parts(groups: list[list[tuple[Path, str]]], out: Path, quality: str = "standard",
                pause_zs: list[float] | None = None, retail: bool = True, log=print,
                filament: str = "pla_basic", brim: float | None = None, bed: str = "textured",
                extra: dict | None = None, object_settings: dict | None = None,
                slot_filaments: dict | None = None, supports: str | None = None) -> dict:
    """Slice the given parts for the P1S. Returns the slice's own summary."""
    ensure_installed()
    if supports == "tree":
        extra = {**TREE_SUPPORTS, **(extra or {})}
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bambu_slice_") as td:
        work = Path(td)
        model = work / "model.3mf"
        colours = build_bambu_3mf(groups, model, object_settings)
        settings, filaments = write_profiles(work, quality, colours, retail, filament, brim, bed, extra, slot_filaments)
        outdir = work / "out"
        outdir.mkdir()
        cmd = _cmd() + ["--slice", "0", "--arrange", "0",
                        "--load-settings", settings, "--load-filaments", filaments,
                        "--outputdir", str(outdir), "--export-3mf", out.name, str(model)]
        env = dict(os.environ, LC_ALL="C.UTF-8")
        r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=3600)
        made = outdir / out.name
        if r.returncode != 0 or not made.exists():
            tail = "\n".join((r.stdout + r.stderr).splitlines()[-25:])
            raise RuntimeError(f"Bambu Studio slice failed (exit {r.returncode}):\n{tail}")
        first = summarise(made)
        finish_for_handy(made, out, work)
        again = summarise(out)
        # Tree supports are grown afresh on each pass and come out slightly different
        # (2026-11-18: 1,611 vs 1,587 support sections on the Urban Kid), so with
        # supports on only the layers and colours must match; the file kept is the second.
        keys = ("layers", "slots_used") if supports else ("layers", "support_lines", "slots_used")
        if [first.get(k) for k in keys] != [again.get(k) for k in keys]:
            raise RuntimeError(f"the second Bambu Studio pass sliced differently: {first} vs {again}")
    paused_at = add_pauses(out, pause_zs) if pause_zs else []
    s = summarise(out)
    s["paused_at_mm"] = paused_at
    s.update({"file": str(out), "quality": quality, "process": PROCESS[quality],
              "retail_settings": retail, "filament": FILAMENTS[filament], "slot_colours": colours,
              "brim_mm": brim, "bed": BEDS[bed]})
    s["supports"] = supports or "off"
    if s["support_lines"] and not supports:
        log(f"WARNING: the slice contains support ({s['support_lines']} support sections) -- fix the model")
    if s.get("slots_used") is not None and len(s["slots_used"]) < len(colours):
        log(f"WARNING: {len(colours)} colours given, only slots {s['slots_used']} used in the G-code")
    return s


def _mat(t: str):
    import numpy as np
    v = [float(x) for x in t.split()]
    return np.array([v[0:3] + [0], v[3:6] + [0], v[6:9] + [0], v[9:12] + [1]])   # 3MF: p' = [p 1] M


def plate_parts(gcode_3mf: Path) -> list:
    """The meshes on a Bambu project's plate, placed, with their filament colours: from the
    file itself, so a file sliced earlier can be finished without its source parts."""
    import xml.etree.ElementTree as ET
    import numpy as np
    import trimesh
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    P = "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path"
    with zipfile.ZipFile(gcode_3mf) as z:
        root = ET.fromstring(z.read("3D/3dmodel.model"))
        cfg = json.loads(z.read("Metadata/project_settings.config"))
        ms = ET.fromstring(z.read("Metadata/model_settings.config"))
        meshes = {}
        for name in z.namelist():
            if name.startswith("3D/Objects/") and name.endswith(".model"):
                for o in ET.fromstring(z.read(name)).iter(f"{{{ns['m']}}}object"):
                    mesh = o.find("m:mesh", ns)
                    if mesh is None:
                        continue
                    v = np.array([[float(e.get(k)) for k in "xyz"] for e in mesh.find("m:vertices", ns)])
                    t = np.array([[int(e.get(k)) for k in ("v1", "v2", "v3")] for e in mesh.find("m:triangles", ns)])
                    meshes[("/" + name, o.get("id"))] = (v, t)
    colours = cfg.get("filament_colour") or ["#F4F1EA"]
    extruder = {}
    for o in ms.iter("object"):
        own = next((m.get("value") for m in o.findall("metadata") if m.get("key") == "extruder"), "1")
        for p in o.iter("part"):
            e = next((m.get("value") for m in p.findall("metadata") if m.get("key") == "extruder"), own)
            extruder[(o.get("id"), p.get("id"))] = int(e)
    objs = {o.get("id"): o for o in root.find("m:resources", ns).findall("m:object", ns)}
    parts = []
    for item in root.find("m:build", ns).findall("m:item", ns):
        oid = item.get("objectid")
        top = _mat(item.get("transform", "1 0 0 0 1 0 0 0 1 0 0 0"))
        comps = objs[oid].find("m:components", ns)
        for c in (comps if comps is not None else []):
            v, t = meshes[(c.get(P), c.get("objectid"))]
            M = _mat(c.get("transform", "1 0 0 0 1 0 0 0 1 0 0 0")) @ top
            vv = np.c_[v, np.ones(len(v))] @ M
            col = colours[min(extruder.get((oid, c.get("objectid")), 1), len(colours)) - 1]
            parts.append((trimesh.Trimesh(vv[:, :3], t, process=False), col))
    return parts


def thumbnail(parts, size: int) -> bytes:
    """A plate thumbnail like the one Bambu Studio's GUI saves: the objects from the front,
    looking down, shaded in their filament colours. The CLI can't draw one in a container
    (its OpenGL window fails to open, 2026-11-17), so this ray-casts the real meshes, one
    ray per pixel."""
    import io
    import numpy as np
    import trimesh
    from PIL import Image
    meshes, cols = [], []
    for m, colour in parts:
        meshes.append(m)
        cols.append(np.repeat([[int(colour[i:i + 2], 16) for i in (1, 3, 5)]], len(m.faces), 0))
    mesh, C = trimesh.util.concatenate(meshes), np.concatenate(cols).astype(float)
    az, el = np.radians(-30), np.radians(35)              # from the front left, looking down
    view = np.array([np.sin(az) * np.cos(el), -np.cos(az) * np.cos(el), np.sin(el)])   # towards the camera
    right = np.array([np.cos(az), np.sin(az), 0.0])
    up = np.cross(view, right)
    pts = mesh.vertices
    u, v = pts @ right, pts @ up
    half = 0.55 * max(u.max() - u.min(), v.max() - v.min())
    cu, cv = (u.max() + u.min()) / 2, (v.max() + v.min()) / 2
    gx, gy = np.meshgrid(np.linspace(-half, half, size), np.linspace(half, -half, size))
    far = (pts @ view).max() + 10
    origins = (cu + gx.ravel())[:, None] * right + (cv + gy.ravel())[:, None] * up + far * view
    hit = mesh.ray.intersects_first(origins, np.tile(-view, (len(origins), 1)))
    light = np.array([-0.4, -0.6, 0.7]) / np.linalg.norm([-0.4, -0.6, 0.7])
    shade = 0.45 + 0.55 * np.clip(mesh.face_normals @ light, 0, 1)
    img = np.zeros((size * size, 4), np.uint8)
    ok = hit >= 0
    img[ok, :3] = np.clip(C[hit[ok]] * shade[hit[ok], None], 0, 255)
    img[ok, 3] = 255
    buf = io.BytesIO()
    Image.fromarray(img.reshape(size, size, 4)).save(buf, "PNG")
    return buf.getvalue()


def finish_for_handy(made: Path, out: Path, work: Path) -> None:
    """Pass the slice through Bambu Studio once more, from its own project file, and add
    the plate thumbnails. Benson, 2026-11-15: Bambu Handy's cloud slicer rejected our files
    (0500-4014, the 6 mm balls). The first pass loads a plain 3MF, and its export puts no
    <model_instance> on the plate, so the plate lists no objects; slice_info names none,
    and there are no thumbnails. Loaded back from its own export, Bambu Studio writes the
    plate's objects and their identify_ids, as a file saved from the GUI has (checked
    2026-11-17 on the Plinko test print: the same G-code apart from progress lines)."""
    project = work / "project.3mf"
    with zipfile.ZipFile(made) as zin, zipfile.ZipFile(project, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            if re.fullmatch(r"Metadata/plate_\d+\.gcode(\.md5)?", it.filename):
                continue                                   # the first pass's G-code
            data = zin.read(it.filename)
            if it.filename == "Metadata/project_settings.config":
                cfg = json.loads(data)
                cfg["default_filament_colour"] = list(cfg.get("filament_colour", []))   # was [""] (Benson's note)
                data = json.dumps(cfg, indent=4).encode()
            zout.writestr(it, data)
    outdir = work / "out2"
    outdir.mkdir()
    r = subprocess.run(_cmd() + ["--slice", "0", "--outputdir", str(outdir), "--export-3mf", "final.gcode.3mf",
                                 str(project)], capture_output=True, text=True,
                       env=dict(os.environ, LC_ALL="C.UTF-8"), timeout=3600, cwd=work)   # it writes result.json to its cwd
    final = outdir / "final.gcode.3mf"
    if r.returncode != 0 or not final.exists():
        tail = "\n".join((r.stdout + r.stderr).splitlines()[-25:])
        raise RuntimeError(f"Bambu Studio's second pass failed (exit {r.returncode}):\n{tail}")
    with zipfile.ZipFile(final) as z:
        items = [(it, z.read(it.filename)) for it in z.infolist()]
    names = {it.filename for it, _ in items}
    settings = next(b for it, b in items if it.filename == "Metadata/model_settings.config").decode()
    if "<model_instance>" not in settings:
        raise RuntimeError("the second pass still put no <model_instance> on the plate")
    parts = plate_parts(final)
    thumbs = {"Metadata/plate_1.png": thumbnail(parts, 512),
              "Metadata/plate_1_small.png": thumbnail(parts, 128)}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for it, data in items:
            if it.filename == "[Content_Types].xml" and b'Extension="png"' not in data:
                data = data.replace(b"</Types>", b'<Default Extension="png" ContentType="image/png"/></Types>')
            zout.writestr(it, data)
        for name, data in thumbs.items():
            if name not in names:
                zout.writestr(name, data)


def _object_sets(items: list[str]) -> dict[int, dict[str, str]]:
    """--object-set N:KEY=VALUE, as {N: {KEY: VALUE}}."""
    out: dict[int, dict[str, str]] = {}
    for it in items:
        n, _, kv = it.partition(":")
        k, _, v = kv.partition("=")
        out.setdefault(int(n), {})[k] = v
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("parts", nargs="+", help='mesh.stl:#RRGGBB per part; "+" starts a new object')
    ap.add_argument("-o", "--out", required=True, help="the .gcode.3mf to write")
    ap.add_argument("--quality", choices=sorted(PROCESS), default="standard")
    ap.add_argument("--filament", choices=sorted(FILAMENTS), default="pla_basic")
    ap.add_argument("--pause-at", type=float, action="append", default=[], help="pause before this layer height (mm)")
    ap.add_argument("--bambu-defaults", action="store_true", help="Bambu's profile as-is, without the shop's retail settings")
    ap.add_argument("--brim", type=float, metavar="MM", help="force an outer brim this wide (default: Bambu's auto brim)")
    ap.add_argument("--bed", choices=sorted(BEDS), default="textured", help="the build plate (sets the bed temperature)")
    ap.add_argument("--supports", choices=["tree"], help="print with organic tree supports (a figure printed whole)")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="any process setting by its Bambu Studio name, e.g. fuzzy_skin=external")
    ap.add_argument("--slot-filament", action="append", default=[], metavar="N:KIND",
                    help=f"a different filament in AMS slot N (slots follow the colours' order): {', '.join(FILAMENTS)}")
    ap.add_argument("--object-set", action="append", default=[], metavar="N:KEY=VALUE",
                    help="a setting for object N only (1 = the first, objects split by +)")
    a = ap.parse_args()
    s = slice_parts(parse_parts(a.parts), Path(a.out), a.quality, a.pause_at, retail=not a.bambu_defaults,
                    filament=a.filament, brim=a.brim, bed=a.bed,
                    extra=dict(kv.split("=", 1) for kv in a.set), object_settings=_object_sets(a.object_set),
                    slot_filaments={int(n): k for n, k in (x.split(":", 1) for x in a.slot_filament)},
                    supports=a.supports)
    print(json.dumps(s, indent=1))
    if s["support_lines"] and not a.supports:
        sys.exit(2)


if __name__ == "__main__":
    main()
