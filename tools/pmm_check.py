#!/usr/bin/env python3
"""Check a MakerWorld PMM customizer the way MakerWorld will use it (2026-11-06).

    python3 tools/pmm_check.py file.scad --param NAME --values Olivia Mia "MARY-JO" \\
        [--slice Olivia] [--report out.txt]

For each value of the parameter:
- **render time** with a Manifold build of OpenSCAD (PMM's backend; its
  generator gives up after about 10 s, so anything over LIMIT_S fails);
- **on the plate:** the whole model inside a 256 mm plate, from z = 0;
- **the text draws:** some colour has more surface with the value than with
  the parameter empty (an inlay is flush, so volume can't show it). An unknown
  font draws nothing, and this is what catches it;
- the file's **fonts** are all in PMM's runtime list, and it **imports** nothing.

`--slice` slices the exported colour 3MF exactly as it comes out, with Bambu
Studio and `--arrange 0`, so nothing is moved: the stand-in for Handy's cloud
slice. A model off the plate fails here, as it failed in Handy.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import re
import zipfile

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bambu_slice as bs  # noqa: E402
import pmm_build as pb  # noqa: E402

LIMIT_S = 5.0          # half PMM's reported 10 s, for a slower server
PLATE = 256.0


def render(scad, out, defines):
    secs, log = pb.time_render(scad, out, defines)
    if not Path(out).exists():
        raise RuntimeError(f"render failed:\n{log[-2000:]}")
    return secs, log


def colour_areas(model_3mf):
    """Surface area per display colour in an OpenSCAD colour 3MF (mm²)."""
    with zipfile.ZipFile(model_3mf) as z:
        x = z.read("3D/3dmodel.model").decode()
    cols = re.findall(r'<base name="[^"]*" displaycolor="(#[0-9A-Fa-f]+)"', x)
    v = np.array([[float(a), float(b), float(c)] for a, b, c in
                  re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', x)])
    obj = re.search(r'<object [^>]*pindex="(\d+)"', x)
    default = int(obj.group(1)) if obj else 0
    out = {}
    for t in re.finditer(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"([^/]*)/>', x):
        i, j, k = int(t.group(1)), int(t.group(2)), int(t.group(3))
        m = re.search(r'p1="(\d+)"', t.group(4))
        c = cols[int(m.group(1)) if m else default].upper()[:7]
        out[c] = out.get(c, 0.0) + 0.5 * np.linalg.norm(np.cross(v[j] - v[i], v[k] - v[i]))
    return out


def raw_slice(model_3mf, out):
    """Bambu Studio on the 3MF as PMM writes it: no arranging, the default filament."""
    bs.ensure_installed()
    with tempfile.TemporaryDirectory(prefix="pmm_slice_") as td:
        work = Path(td)
        settings, filaments = bs.write_profiles(work, "standard", ["#C62F3A", "#F4F1EA", "#3B2A3A", "#D7263D"])
        outdir = work / "out"
        outdir.mkdir()
        cmd = bs._cmd() + ["--slice", "0", "--arrange", "0", "--load-settings", settings,
                           "--load-filaments", filaments, "--outputdir", str(outdir),
                           "--export-3mf", Path(out).name, str(model_3mf)]
        r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, LC_ALL="C.UTF-8"), timeout=3600)
        made = outdir / Path(out).name
        if r.returncode != 0 or not made.exists():
            return False, "\n".join((r.stdout + r.stderr).splitlines()[-12:])
        made.replace(out)
    s = bs.summarise(Path(out))
    return True, s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scad")
    ap.add_argument("--param", required=True)
    ap.add_argument("--values", nargs="+", required=True)
    ap.add_argument("--slice", nargs="*", default=[])
    ap.add_argument("--report")
    a = ap.parse_args()
    scad = Path(a.scad).resolve()
    lines, fails = [], []
    say = lambda s: (print(s), lines.append(s))
    text = scad.read_text()
    say(f"PMM check of {scad.name} ({len(text):,} bytes)")
    bad_f, bad_i = pb.check_fonts(text), pb.check_no_imports(text)
    say(f"- fonts not on PMM: {bad_f or 'none'}")
    say(f"- imports/includes PMM can't resolve: {bad_i or 'none'}")
    fails += [f"font {f}" for f in bad_f] + [f"import {i}" for i in bad_i]
    with tempfile.TemporaryDirectory(prefix="pmm_check_") as td:
        work = Path(td)
        render(scad, work / "empty.3mf", [f'{a.param}=""'])
        a0 = colour_areas(work / "empty.3mf")
        say(f"- with {a.param} empty, area by colour: " + ", ".join(f"{c} {v:,.0f} mm²" for c, v in a0.items()))
        for v in a.values:
            stl, m3 = work / "m.stl", work / "m.3mf"
            secs, log = render(scad, stl, [f'{a.param}="{v}"'])
            m = trimesh.load(stl, force="mesh")
            render(scad, m3, [f'{a.param}="{v}"'])
            av = colour_areas(m3)
            # the text's colour: the one whose area grows most with the value
            dv = max(av.get(c, 0) - a0.get(c, 0) for c in av)
            lo, hi = m.bounds
            on = lo[0] >= 0 and lo[1] >= 0 and hi[0] <= PLATE and hi[1] <= PLATE and abs(lo[2]) < 1e-3
            warn = [ln for ln in log.splitlines() if "WARNING" in ln]
            ok = secs <= LIMIT_S and on and dv > 20.0 and not warn
            say(f"- {v!r}: {secs:.1f} s; x {lo[0]:.1f}..{hi[0]:.1f}, y {lo[1]:.1f}..{hi[1]:.1f}, "
                f"z {lo[2]:.2f}..{hi[2]:.1f}; the text adds {dv:,.0f} mm² in its colour; {len(warn)} warnings"
                + ("" if ok else "  <-- FAIL"))
            for w in warn[:3]:
                say(f"    {w}")
            if not ok:
                fails.append(v)
            if v in a.slice:
                good, s = raw_slice(m3, work / "sliced.gcode.3mf")
                if good:
                    say(f"  sliced as exported (Bambu Studio, no arranging): {s.get('time')}, "
                        f"{s.get('filament_g')} g, support sections {s.get('support_lines')}")
                    if s.get("support_lines"):
                        fails.append(f"{v} support")
                else:
                    say(f"  slicing FAILED as exported:\n{s}")
                    fails.append(f"{v} slice")
    say("RESULT: " + ("PASS" if not fails else f"FAIL {fails}"))
    if a.report:
        Path(a.report).write_text("\n".join(lines) + "\n")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
