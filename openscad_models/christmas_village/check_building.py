#!/usr/bin/env python3
"""Check a village building through tools/model_checks.py (2026-10-14).

    python3 check_building.py victorian/church [steps...]
    python3 check_building.py ../haunted_town/chapel [steps...]

The buildings were checked one command at a time when they were built; this
runs them through the shared steps instead, the way the accessories and
lanterns are, for the maker's-mark inlay that changed every building's
underside at once. It writes the one-body union the gate needs, reads each
part's filament colour from the building's own printing notes, and keeps the
label and note its viewer entry already has.

Default steps: parts gate cost 3mf fidelity viewer. The mark is underneath,
so the colour and as-printed renders (taken from above and the sides) do not
change; ask for them by name if they are wanted.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from model_checks import run_checks  # noqa: E402

PARTS = ("body", "roof", "trim", "accent")
DEFAULT_STEPS = ["parts", "gate", "cost", "3mf", "fidelity", "viewer"]


def colours(d):
    """{part: '#RRGGBB'} from the printing notes' part table."""
    notes = next(d.glob("*PRINTING*.md"))
    out = {}
    for line in notes.read_text().splitlines():
        # the part may follow an object column (the post office: | house | body | ...)
        m = re.match(r"\|\s*(?:\w+\s*\|\s*)?(body|roof|trim|accent)\s*\|.*`(#[0-9A-Fa-f]{6})`", line)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2).upper()
    return out


def viewer_entry(name):
    s = (ROOT / "tools/viewer/jobs/index.js").read_text()
    for e in json.loads(s[s.index("["):s.rindex("]") + 1]):
        if e["id"] == name:
            return e
    raise SystemExit(f"{name} has no viewer entry to keep the label and note of")


def union(d, name):
    env = dict(os.environ, OPENSCADPATH=str(ROOT / "assets/openscad_libs"))
    r = subprocess.run(["openscad", "-D", 'part="union"', "-o", f"{name}_union.stl", f"{name}.scad"],
                       cwd=d, capture_output=True, text=True, env=env)
    if r.returncode:
        raise SystemExit(f"union export failed:\n{r.stderr[-2000:]}")
    # CGAL writes two solids that touch along a line as one edge of four
    # faces; manifold's merge welds them without moving a vertex. With the
    # inlay added, the Victorian cottage's union kept two such edges where
    # the gable dives into the cone and failed watertight (2026-10-15).
    import part_mesh
    p = d / f"{name}_union.stl"
    part_mesh.to_trimesh(part_mesh.load(str(p))).export(p)


def export_parts(d, name):
    """The haunted town has no build.sh: export the colour parts here."""
    env = dict(os.environ, OPENSCADPATH=str(ROOT / "assets/openscad_libs"))
    for p in PARTS:                               # an empty part writes no file: never leave a stale one
        (d / f"{name}_{p}.stl").unlink(missing_ok=True)
    procs = [subprocess.Popen(["openscad", "-D", f'part="{p}"', "-o", f"{name}_{p}.stl", f"{name}.scad"],
                              cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env) for p in PARTS]
    for pr in procs:
        pr.wait()


if __name__ == "__main__":
    d = (HERE / sys.argv[1]).resolve()
    rel = d.relative_to(ROOT / "openscad_models")
    prefix = {"victorian": "victorian", "gingerbread": "gingerbread", "haunted_town": "haunted"}[d.parent.name]
    (scad,) = d.glob(f"{prefix}_*.scad")          # not the Santa's workshops' toys_lib.scad
    name = scad.stem
    if not (d / "build.sh").exists():
        export_parts(d, name)
    steps = sys.argv[2:] or DEFAULT_STEPS
    cols = colours(d)
    present = [p for p in PARTS if (d / f"{name}_{p}.stl").exists()]
    if missing := [p for p in present if p not in cols]:
        raise SystemExit(f"no colour in the printing notes for {missing}")
    # the v1 workshops' files share the current ones' names; their viewer
    # entries carry _v1, and so must everything else they write
    tag = "_v1" if d.name.endswith("_v1") else ""
    e = viewer_entry(name + tag)
    if "gate" in steps or not (d / f"{name}_union.stl").exists():
        union(d, name)
    run_checks(d, name, dict(label=e["name"], note=e.get("notes", ""),
                             objects=[[(p, cols[p]) for p in present]],
                             unions=[f"{name}_union.stl"],
                             tags=[tag], source=f"{rel}/{name}.3mf"), steps)
