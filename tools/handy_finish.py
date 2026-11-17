#!/usr/bin/env python3
"""Make an already-sliced .gcode.3mf safe for Bambu Handy's cloud slicer, changing nothing
else (2026-11-17).

Benson, 2026-11-15: Handy failed to slice our files (0500-4014), because the plate in
them lists no objects (no <model_instance>). tools/bambu_slice.py now finishes every new
slice this way (`finish_for_handy`); this does the same to a file sliced before that fix.
It slices the file again from its own embedded project, adds the plate thumbnails, puts
back any pauses at the same heights, and refuses to write if the layers, supports, colour
slots or pauses came out different.

    python3 tools/handy_finish.py file.gcode.3mf [more.gcode.3mf ...] [--check]

--check only reports whether each file already has what Handy needs.
"""
import argparse
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bambu_slice as bs  # noqa: E402
from reslice_bed import pause_heights  # noqa: E402


def handy_ready(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        ms = z.read("Metadata/model_settings.config").decode("utf-8", "replace")
        si = z.read("Metadata/slice_info.config").decode("utf-8", "replace") if "Metadata/slice_info.config" in names else ""
    return {"model_instance": "<model_instance>" in ms, "identify_id": "identify_id" in si,
            "thumbnail": "Metadata/plate_1.png" in names}


def finish(path: Path) -> dict:
    bs.ensure_installed()
    old = bs.summarise(path)
    pauses = pause_heights(path)
    with tempfile.TemporaryDirectory(prefix="handy_finish_") as td:
        work = Path(td)
        made = work / "out.gcode.3mf"
        bs.finish_for_handy(path, made, work)
        if pauses:
            bs.add_pauses(made, pauses)
        new = bs.summarise(made)
        keys = ("layers", "support_lines", "slots_used")
        if [old.get(k) for k in keys] != [new.get(k) for k in keys] or pause_heights(made) != pauses:
            raise RuntimeError(f"{path}: the finished slice differs, not replacing\n  old {old}\n  new {new}")
        path.write_bytes(made.read_bytes())
    return {"time": f"{old.get('time')} -> {new.get('time')}", "grams": f"{old.get('filament_g')} -> {new.get('filament_g')}",
            "layers": new["layers"], "pauses": pauses, **handy_ready(path)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    bad = 0
    for f in a.files:
        try:
            r = handy_ready(f) if a.check else finish(f)
        except Exception as e:  # report every file, then fail
            print(f"FAIL {f}: {e}")
            bad += 1
            continue
        ok = r["model_instance"] and r["identify_id"] and r["thumbnail"]
        bad += not ok
        print(("ok   " if ok else "NO   ") + f"{f}: {r}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
