#!/usr/bin/env python3
"""Render a part as the printer will make it: from the toolpath, in its filaments.

    python3 tools/as_printed.py sliced.gcode -o chapel_as_printed.png \\
        --colour '#77716B' --colour '#2B2F38' --colour '#EFE6D2' --colour '#D4A96A'

Scott, 2026-09-27: "We need to make sure the images that are produced can be
recreated in a print." A render of the MODEL shows every edge the .scad has,
including ones the slicer drops or closes over. This renders the beads the
slicer actually emits -- one mesh per filament, coloured in the order the
filaments are loaded (slot 1 first) -- so what it shows is what the plate
will hold, layer lines included.

Two things it does differently from the viewer's stills, both for detail:
  * it reads the G-code at 0.02 mm, not a viewer payload. The detailed
    buildings' payloads are simplified at 0.64 mm to fit a web page, which
    rounds away exactly the lettering and trim a close-up is for;
  * every filament's mesh shares one centre, so the colours stay in register.

Supports, the purge tower, the prime line and sparse infill are left out: the
still is the finished part. Pair it with tools/print_fidelity.py, which says
in numbers where the print and the model differ.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gcode_to_mesh as g2m  # noqa: E402
import gcode_viewer_data as gvd  # noqa: E402

HIDDEN = set(g2m.DEFAULT_HIDDEN) | g2m.SUPPORT_TYPES | g2m.PURGE_TYPES


def _rgb(hexcol):
    h = hexcol.lstrip("#")
    return ",".join("%.3f" % (int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))


def meshes(gcode, out_dir, tol_mm=0.02):
    """One PLY per filament that prints part of the finished object."""
    payload = gvd.build_job(Path(gcode), "as_printed", tol_mm=tol_mm)
    pts = g2m._decode(payload["pts"], np.int16).reshape(-1, 2) / 100.0
    polys = g2m._decode(payload["polys"], np.int32).reshape(-1, 3)
    tools = g2m._decode(payload["polyTool"], np.uint8)
    keep = np.array([t not in HIDDEN for t in polys[:, 0]])
    used = sorted(set(tools[keep].tolist()))
    idx = np.concatenate([np.arange(s, s + n) for _, s, n in polys[keep]])
    p = pts[idx]
    centre = ((p[:, 0].min() + p[:, 0].max()) / 2, (p[:, 1].min() + p[:, 1].max()) / 2)
    out = {}
    for t in used:
        V, F = g2m.build(payload, hidden=HIDDEN, tool=t, centre=centre)
        f = Path(out_dir) / f"as_printed_T{t}.ply"
        g2m.write_ply(f, V, F)
        out[t] = f
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("gcode")
    ap.add_argument("-o", "--output", required=True, help="PNG; with --views, the stem")
    ap.add_argument("--colour", action="append", default=[],
                    help="filament colour, slot 1 first; repeat per filament")
    ap.add_argument("--views", action="store_true", help="front, three-quarter and top")
    ap.add_argument("--front", default="-y", choices=["-y", "+y"])
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--keep", help="keep the PLY meshes here")
    a = ap.parse_args(argv)
    work = Path(a.keep) if a.keep else Path(tempfile.mkdtemp(prefix="as_printed_"))
    work.mkdir(parents=True, exist_ok=True)
    got = meshes(a.gcode, work)
    args = []
    for t, f in got.items():
        col = a.colour[t] if t < len(a.colour) else "#9A9A9A"
        args += ["--part", f"{f}:{_rgb(col)}"]
    cmd = [sys.executable, str(Path(__file__).parent / "blender_render.py"), *args,
           "-o", a.output, "--samples", str(a.samples), "--no-cache"]
    if a.views:
        cmd += ["--views", f"--front={a.front}"]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
