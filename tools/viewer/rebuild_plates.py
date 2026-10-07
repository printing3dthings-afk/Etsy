#!/usr/bin/env python3
"""
tools/viewer/rebuild_plates.py -- re-slice every plate in the viewer with
Bambu Studio and rebuild the payloads, keeping each plate's id, name, note
and source.

    python3 tools/viewer/rebuild_plates.py --work /tmp/plates          # all plates
    python3 tools/viewer/rebuild_plates.py --work /tmp/plates --only haunted_chapel

Scott, 2026-10-07: re-slice the viewer's plates on Bambu Studio, the slicer he
prints with (they were PrusaSlicer slices). The manifest is the current
jobs/index.js -- every plate already names its source file -- plus
plate_settings.json for the multi-colour plates, so the rebuild can be rerun
whenever the slicer, the presets or a model changes.

Every 3MF goes through assemble_3mf.to_bambu_layout first: the repo's 3MFs
are in PrusaSlicer's single-mesh layout, which Bambu Studio reads as one part
on one filament.

A plate whose notes name no colours is sliced in the viewer's illustrative
palette and its G-code's filament_colour line is dropped before the payload is
built, so the page shows its own "illustrative" palette rather than presenting
made-up colours as the product's. Its time and grams are for that palette.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))

import assemble_3mf  # noqa: E402
import gcode_viewer_data  # noqa: E402
import virtual_printer  # noqa: E402

# The page's own illustrative palette (app.js, DEFAULT_FILAMENT).
ILLUSTRATIVE = ["#d9dbe0", "#24272d", "#8d939d", "#c08a5a", "#e0553d",
                "#6fa8dc", "#8bc34a", "#f2c14e"]


def load_index(jobs_dir):
    text = (jobs_dir / "index.js").read_text()
    return json.loads(re.search(r"=\s*(\[.*\])", text, re.S).group(1))


def resolve(source):
    """The repo file a plate's `source` names (it is stored relative to
    openscad_models/, and a bare name can match more than one file)."""
    for cand in (ROOT / "openscad_models" / source, ROOT / source):
        if cand.exists():
            return cand
    out = subprocess.run(["git", "ls-files", f"*{Path(source).name}"], cwd=ROOT,
                         capture_output=True, text=True).stdout.split()
    hits = [p for p in out if p.endswith(source) and "/trash/" not in p]
    if len(hits) != 1:
        raise FileNotFoundError(f"cannot resolve plate source {source!r}: {hits}")
    return ROOT / hits[0]


def slice_plate(plate, work, colours_cfg):
    pid = plate["id"]
    src = resolve(plate["source"])
    cfg = colours_cfg.get(pid, {})
    if src.suffix.lower() == ".3mf":
        model = work / f"{pid}.bambu.3mf"
        info = assemble_3mf.to_bambu_layout(src, model)
        n = max(info["extruders"])
    else:
        model, n = src, 1
    if n > 1 and not (cfg.get("colours") or cfg.get("illustrative")):
        raise ValueError(f"{pid}: {n} filaments but no entry in plate_settings.json")
    colours = ILLUSTRATIVE[:n] if cfg.get("illustrative") or n == 1 else cfg["colours"]
    if n > 1 and len(colours) < n:
        raise ValueError(f"{pid}: {n} filaments, {len(colours)} colours listed")
    gcode = work / f"{pid}.gcode"
    note = ""
    supports = cfg.get("supports", True)
    extra = {"layer-height": str(cfg["layer_height"])} if cfg.get("layer_height") else None
    try:
        virtual_printer.slice_model(model, gcode, supports=supports, colours=colours,
                                    slicer="bambu", extra=extra)
    except virtual_printer.VirtualPrinterError as exc:
        # Bambu refusing a plate is a finding about the plate (2026-10-07: the
        # mushroom lamp and sundial "not fully inside the print volume" with
        # supports on, the Glow downlight's two parts' paths colliding). Show
        # the PrusaSlicer slice and say why on the plate, never a support-free
        # slice of a model that needs support.
        reason = re.findall(r"\[error\]\s+(.*)", str(exc))
        reason = "; ".join(r for r in reason if "plate" in r or "conflict" in r)[:200] \
            or "see tools/viewer/rebuild_plates.py output"
        virtual_printer.slice_model(src, gcode, supports=supports, slicer="prusa", extra=extra)
        note = (f" Bambu Studio refused this plate with supports on ({reason}), "
                "so this is the PrusaSlicer slice.")
    if cfg.get("illustrative") or n == 1:
        # One-colour plates and plates with no chosen colours carry none: the
        # page then uses its labelled illustrative palette.
        text = gcode.read_text(errors="replace")
        gcode.write_text(re.sub(r"^; filament_colour = .*\n", "", text, flags=re.M))
    (work / f"{pid}.note").write_text(note)
    return gcode, note


def _base_note(note):
    """A note without a fallback sentence from an earlier rebuild."""
    return re.sub(r" Bambu Studio refused this plate.*?PrusaSlicer slice\.", "", note)


def _fallback_note(work, pid):
    f = work / f"{pid}.note"
    return f.read_text() if f.exists() else ""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--work", required=True, help="scratch directory for 3MFs and G-code")
    ap.add_argument("--jobs", default=str(HERE / "jobs"), help="payload directory to rebuild")
    ap.add_argument("--only", nargs="*", help="plate ids to re-slice (the index keeps the rest)")
    ap.add_argument("--no-slice", action="store_true",
                    help="rebuild payloads from the G-code already in --work")
    ap.add_argument("--max-mb", type=float, default=1.0)
    ap.add_argument("-j", type=int, default=3, help="slices in parallel")
    a = ap.parse_args(argv)
    work, jobs = Path(a.work), Path(a.jobs)
    work.mkdir(parents=True, exist_ok=True)
    index = load_index(jobs)
    colours_cfg = json.loads((HERE / "plate_settings.json").read_text())
    todo = [] if a.no_slice else [p for p in index if not a.only or p["id"] in a.only]

    failed, notes = {}, {}

    def one(p):
        try:
            g, note = slice_plate(p, work, colours_cfg)
            print(f"  sliced {p['id']}{' (PrusaSlicer fallback)' if note else ''}", flush=True)
            notes[p["id"]] = note
            return p, g
        except Exception as exc:          # reported below, never dropped silently
            failed[p["id"]] = str(exc)[:300]
            print(f"  FAILED {p['id']}: {str(exc)[:200]}", flush=True)
            return p, None

    with ThreadPoolExecutor(a.j) as ex:
        done = list(ex.map(one, todo))
    if failed:
        print(f"\n{len(failed)} plate(s) failed; nothing written:")
        for k, v in failed.items():
            print(f"  {k}: {v}")
        raise SystemExit(1)

    # The builder rewrites index.js from what it is given, so plates not being
    # re-sliced are rebuilt from their existing G-code in --work, or refused.
    sliced = {p["id"]: g for p, g in done}
    gcodes, opts = [], []
    for p in index:
        g = sliced.get(p["id"]) or work / f"{p['id']}.gcode"
        if not g.exists():
            raise SystemExit(f"{p['id']}: no G-code in {work}; re-slice it or run without --only")
        gcodes.append(str(g))
        # The builder's G-code list is one positional run; options after it.
        base = colours_cfg.get(p["id"], {}).get("note") or _base_note(p["notes"])
        opts += ["--label", f"{p['id']}={p['name']}",
                 "--note", f"{p['id']}={(base + _fallback_note(work, p['id'])).strip()}",
                 "--source", f"{p['id']}={p['source']}"]
    gcode_viewer_data.main(gcodes + opts + ["-d", str(jobs), "--max-mb", str(a.max_mb)])


if __name__ == "__main__":
    main()
