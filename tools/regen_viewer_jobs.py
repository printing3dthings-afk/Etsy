#!/usr/bin/env python3
"""
tools/regen_viewer_jobs.py -- re-slice every plate in the viewer library from
its source model and re-export it, keeping its name, notes, colours and place
in the list.

Written 2026-10-10 when the slices moved to Bambu's own P1S speeds and
accelerations (virtual_printer.P1S_MOTION) and the payload gained per-move
timing (tools/p1s_motion.py): every existing plate had been sliced at
PrusaSlicer's defaults, roughly a third of the P1S's real pace, and none of
them carried move timing.

Each plate is sliced the way it was before, read off its existing payload:
its layer height, supports only if it printed any, and for a multi-filament plate the same filament count with
a wipe tower and no supports (see print_fidelity.compare for why). The source
path comes from the index's own "source" field, relative to openscad_models/.

    python3 tools/regen_viewer_jobs.py              # every plate
    python3 tools/regen_viewer_jobs.py vase sundial # just these
    python3 tools/regen_viewer_jobs.py --resume     # only plates not yet re-sliced
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gcode_viewer_data  # noqa: E402
import virtual_printer    # noqa: E402

JOBS = ROOT / "tools" / "viewer" / "jobs"
MODELS = ROOT / "openscad_models"
BED_CENTRE = "128,128"


def _payload(path):
    s = path.read_text()
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


def regen(ids=None, log=print, skip_done=False):
    s = (JOBS / "index.js").read_text()
    index = json.loads(s[s.index("["):s.rindex("]") + 1])
    done, failed = [], []
    for entry in index:
        jid = entry["id"]
        if ids and jid not in ids:
            continue
        src = MODELS / entry.get("source", "")
        if not entry.get("source") or not src.exists():
            failed.append((jid, f"source not found: {src}"))
            continue
        old = _payload(JOBS / f"{jid}.js")
        if skip_done and "segV" in old:
            continue
        extra = {}
        lh = old.get("layerHeight", 0.2)
        if abs(lh - 0.2) > 1e-6:
            extra["layer-height"] = str(lh)
        n_tools = len(old.get("filamentByTool") or [1])
        # Supports as before: a plate that printed none was sliced without
        # them (the pumpkins hold supports off on purpose, so layer height is
        # the only thing that differs between the three).
        supports = "Support material" in old.get("segmentsByType", {})
        if old.get("toolChanges", 0) > 0 and n_tools > 1:
            extra.update(virtual_printer.mmu_options(n_tools))
            extra["center"] = BED_CENTRE
            supports = False
        with tempfile.TemporaryDirectory() as td:
            g = Path(td) / f"{jid}.gcode"
            try:
                virtual_printer.slice_model(src, g, supports=supports, extra=extra)
            except Exception as e:  # report and carry on with the rest
                failed.append((jid, f"slice failed: {e}"))
                continue
            args = [str(g), "-d", str(JOBS), "--append", "--max-mb", "3",
                    "--label", f"{jid}={entry['name']}", "--note", f"{jid}={entry.get('notes', '')}",
                    "--source", f"{jid}={entry['source']}"]
            if old.get("toolColors"):
                args += ["--colours", f"{jid}={','.join(old['toolColors'])}"]
            try:
                gcode_viewer_data.main(args)
            except Exception as e:
                failed.append((jid, f"export failed: {e}"))
                continue
        new = _payload(JOBS / f"{jid}.js")
        done.append((jid, entry["totalSeconds"], new["totalSeconds"], new.get("slicerSeconds")))
        log(f"  {jid}: {entry['totalSeconds'] / 60:.0f} min -> {new['totalSeconds'] / 60:.0f} min "
            f"(slicer {new.get('slicerSeconds') and round(new['slicerSeconds'] / 60)} min)")
    return done, failed


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--resume"]
    done, failed = regen(set(args) or None, skip_done="--resume" in sys.argv)
    print(f"\n{len(done)} re-exported, {len(failed)} failed")
    for jid, why in failed:
        print(f"  FAILED {jid}: {why}")
    sys.exit(1 if failed else 0)
