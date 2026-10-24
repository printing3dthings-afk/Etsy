#!/usr/bin/env python3
"""Slice a model with Bambu Studio itself, for the P1S, to a printer-ready file.

    python3 tools/bambu_slice.py body.stl:#F4F1EA trim.stl:#C8312B + plate.stl:#2B5FA8 \\
        -o model.gcode.3mf --quality fine [--pause-at 4.2]

Scott, 2026-10-24: "I want you to be able to slice to the best print settings
and send to printer." The print checks (virtual_printer, print_fidelity) slice
with PrusaSlicer 2.7; this is the slicer Scott prints from. It writes the
.gcode.3mf the P1S runs, which the bridge (tools/relay/bambu_p1s_bridge.py)
uploads and starts once Scott approves the job in the Action Center.

THE SLICER. Bambu Studio 2.8.2.61 from Flathub (GitHub downloads are blocked
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
FLATPAK_RT = Path("/var/lib/flatpak/runtime/org.gnome.Platform/x86_64/50/active/files")
PROFILES = FLATPAK_APP / "share/BambuStudio/profiles/BBL"

MACHINE = "Bambu Lab P1S 0.4 nozzle"
PROCESS = {
    "standard": "0.20mm Standard @BBL X1C",
    "fine": "0.12mm Fine @BBL X1C",
    "extra_fine": "0.08mm Extra Fine @BBL X1C",
}
FILAMENT = "Bambu PLA Basic @BBL P1S 0.4 nozzle"

# CLAUDE.md "Production Quality Settings" -- the shop's own retail standard.
# "Customers only see the outside": the outer wall is slowed and printed first.
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


def _cmd() -> list[str]:
    loader = FLATPAK_RT / "lib/x86_64-linux-gnu/ld-linux-x86-64.so.2"
    libs = f"{FLATPAK_APP / 'lib'}:{FLATPAK_RT / 'lib/x86_64-linux-gnu'}:{FLATPAK_RT / 'lib'}"
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


def write_profiles(workdir: Path, quality: str, colours: list[str], retail: bool = True) -> tuple[str, str]:
    """Write the machine, process and filament files; returns the two CLI args."""
    machine = flatten("machine", MACHINE)
    process = flatten("process", PROCESS[quality])
    if retail:
        for k, v in RETAIL.items():
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
        f = flatten("filament", FILAMENT)
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
TOWER_SIZE = 35 + 2 * 3 + 6   # width, brim each side, and room for it to grow
GAP = 12.0


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
        raise ValueError(f"the objects need {total:.0f} mm in a row; the P1S plate is {BED:.0f}")
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


def build_bambu_3mf(groups: list[list[tuple[Path, str]]], out: Path) -> list[str]:
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
        settings.append(f'<object id="{oid}"><metadata key="name" value="{first}"/>'
                        f'<metadata key="extruder" value="{slots[g[0][1]]}"/>' + "".join(part_cfg) + "</object>")
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
                pause_zs: list[float] | None = None, retail: bool = True, log=print) -> dict:
    """Slice the given parts for the P1S. Returns the slice's own summary."""
    ensure_installed()
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bambu_slice_") as td:
        work = Path(td)
        model = work / "model.3mf"
        colours = build_bambu_3mf(groups, model)
        settings, filaments = write_profiles(work, quality, colours, retail)
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
        shutil.move(str(made), out)
    paused_at = add_pauses(out, pause_zs) if pause_zs else []
    s = summarise(out)
    s["paused_at_mm"] = paused_at
    s.update({"file": str(out), "quality": quality, "process": PROCESS[quality],
              "retail_settings": retail, "slot_colours": colours})
    if s["support_lines"]:
        log(f"WARNING: the slice contains support ({s['support_lines']} support sections) -- fix the model")
    if s.get("slots_used") is not None and len(s["slots_used"]) < len(colours):
        log(f"WARNING: {len(colours)} colours given, only slots {s['slots_used']} used in the G-code")
    return s


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("parts", nargs="+", help='mesh.stl:#RRGGBB per part; "+" starts a new object')
    ap.add_argument("-o", "--out", required=True, help="the .gcode.3mf to write")
    ap.add_argument("--quality", choices=sorted(PROCESS), default="standard")
    ap.add_argument("--pause-at", type=float, action="append", default=[], help="pause before this layer height (mm)")
    ap.add_argument("--bambu-defaults", action="store_true", help="Bambu's profile as-is, without the shop's retail settings")
    a = ap.parse_args()
    s = slice_parts(parse_parts(a.parts), Path(a.out), a.quality, a.pause_at, retail=not a.bambu_defaults)
    print(json.dumps(s, indent=1))
    if s["support_lines"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
