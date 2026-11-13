#!/usr/bin/env python3
"""Re-slice a printer-ready .gcode.3mf for a different build plate, changing nothing else.

Why (2026-11-13): tools/bambu_slice.py never set the plate type, so Bambu Studio sliced
everything for its Cool Plate and heated the bed to 35 C. Scott's plates are PEI, where
PLA wants 55. This takes an existing file, sets only `curr_bed_type` in its own embedded
project settings, slices it again with Bambu Studio from those same settings and the same
embedded model, puts any pauses back at the heights they were, and prints old against new
so a change in anything but the bed shows.

    python3 tools/reslice_bed.py file.gcode.3mf [--bed textured] [--out new.gcode.3mf]

Without --out the file is replaced in place (after the new slice is checked).
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bambu_slice as bs  # noqa: E402


def pause_heights(gcode_3mf: Path) -> list[float]:
    """The layer heights a file pauses before: the Z of the layer each "M400 U1" sits in."""
    with zipfile.ZipFile(gcode_3mf) as z:
        g = z.read(next(n for n in z.namelist() if re.fullmatch(r"Metadata/plate_\d+\.gcode", n))).decode("utf-8", "replace")
    zs, z_now = [], None
    for line in g.splitlines():
        m = re.match(r"; Z_HEIGHT: ([\d.]+)", line)
        if m:
            z_now = float(m.group(1))
        elif line.startswith("M400 U1") and z_now is not None:
            zs.append(z_now)
    return zs


def bed_temps(gcode_3mf: Path) -> list[str]:
    with zipfile.ZipFile(gcode_3mf) as z:
        g = z.read(next(n for n in z.namelist() if re.fullmatch(r"Metadata/plate_\d+\.gcode", n))).decode("utf-8", "replace")
    return sorted(set(re.findall(r"^M1(?:40|90) S(\d+)", g, re.M)) - {"0"})


def reslice(src: Path, out: Path, bed: str) -> dict:
    bs.ensure_installed()
    old = bs.summarise(src)
    pauses = pause_heights(src)
    with tempfile.TemporaryDirectory(prefix="reslice_") as td:
        work = Path(td)
        model = work / "model.3mf"
        with zipfile.ZipFile(src) as zin, zipfile.ZipFile(model, "w", zipfile.ZIP_DEFLATED) as zout:
            for it in zin.infolist():
                if re.fullmatch(r"Metadata/plate_\d+\.gcode(\.md5)?", it.filename):
                    continue                                   # the old slice
                data = zin.read(it.filename)
                if it.filename == "Metadata/project_settings.config":
                    cfg = json.loads(data)
                    cfg["curr_bed_type"] = bs.BEDS[bed]
                    data = json.dumps(cfg, indent=4).encode()
                zout.writestr(it, data)
        outdir = work / "out"
        outdir.mkdir()
        cmd = bs._cmd() + ["--slice", "0", "--outputdir", str(outdir), "--export-3mf", "new.gcode.3mf", str(model)]
        r = subprocess.run(cmd, capture_output=True, text=True, env={"LC_ALL": "C.UTF-8", "PATH": "/usr/bin:/bin"},
                           timeout=3600)
        made = outdir / "new.gcode.3mf"
        if r.returncode != 0 or not made.exists():
            tail = "\n".join((r.stdout + r.stderr).splitlines()[-25:])
            raise RuntimeError(f"Bambu Studio re-slice failed (exit {r.returncode}):\n{tail}")
        if pauses:
            bs.add_pauses(made, pauses)
        new = bs.summarise(made)
        new_pauses = pause_heights(made)
        report = {"file": str(src), "bed": bs.BEDS[bed],
                  "old": {**old, "bed_temps": bed_temps(src), "pause_z": pauses},
                  "new": {**new, "bed_temps": bed_temps(made), "pause_z": new_pauses}}
        same = (old["layers"] == new["layers"] and old["support_lines"] == new["support_lines"]
                and old.get("slots_used") == new.get("slots_used") and pauses == new_pauses)
        report["only_the_bed_changed"] = same
        if not same:
            raise RuntimeError("the re-slice differs in more than the bed; not replacing:\n" + json.dumps(report, indent=1))
        out.write_bytes(made.read_bytes())
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file", type=Path)
    ap.add_argument("--bed", choices=sorted(bs.BEDS), default="textured")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    rep = reslice(a.file, a.out or a.file, a.bed)
    o, n = rep["old"], rep["new"]
    print(f"{a.file.name}: {rep['bed']}")
    print(f"  bed temps   {o['bed_temps']} -> {n['bed_temps']}")
    print(f"  time        {o.get('time')} -> {n.get('time')}")
    print(f"  filament g  {o.get('filament_g')} -> {n.get('filament_g')}")
    print(f"  layers {n['layers']}, supports {n['support_lines']}, slots {n.get('slots_used')}, pauses at {n['pause_z']}")


if __name__ == "__main__":
    main()
