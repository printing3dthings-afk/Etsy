#!/usr/bin/env python3
"""Write ONE print-ready 3MF from several meshes, keeping them separate parts.

    # parts that assemble into one object -- the default
    python3 tools/assemble_3mf.py out.3mf ring.stl:#2B2F38 rotor.stl:#F2F0E9 letter.stl:#E0553D

    # things that separate in use -- same plate, independent objects
    python3 tools/assemble_3mf.py --plate out.3mf box.stl:#2B2F38 lid.stl:#E0553D

WHY THIS EXISTS. OpenSCAD's own 3MF export merges everything into a SINGLE
object with no materials -- verified 2026-09-09 on monogram_keychain_J_all.3mf:
one <object>, one <item>, zero <basematerials>, 20,065 triangles fused. A
multi-colour model exported that way cannot have filaments assigned at all, so
the only way to ship it was several files the customer had to load and align
themselves. Scott's rule (2026-09-09): parts that go together ship as ONE file,
ready to print; a container and its lid stay separate parts but on one plate.

The two modes are exactly those two rules:
  assembly  one <object> built from <components>, so a slicer shows one object
            with N parts and a filament can be set per part.
  plate     N independent <item>s laid out side by side with a gap, so a slicer
            shows N objects already arranged on one plate.
"""
import argparse
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

import numpy as np
import trimesh

_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>"""
_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model"/>
</Relationships>"""


def _mesh_xml(obj_id: int, mesh: trimesh.Trimesh, name: str,
              pid: int, pindex: int) -> str:
    v = "".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>'
                for x, y, z in mesh.vertices)
    t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>'
                for a, b, c in mesh.faces)
    return (f'<object id="{obj_id}" type="model" name="{name}" '
            f'pid="{pid}" pindex="{pindex}">'
            f'<mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh>'
            f'</object>')


def assemble(out_path: Path, groups: list[list[tuple[Path, str]]],
             mode: str = "assembly", gap: float = 6.0) -> dict:
    """groups: each inner list is one printed object, made of one or more
    colour parts. In assembly mode there is exactly one group."""
    flat = [pc for g in groups for pc in g]
    meshes = []
    for path, _ in flat:
        m = trimesh.load(str(path), force="mesh")
        if isinstance(m, trimesh.Scene):
            m = trimesh.util.concatenate(tuple(m.geometry.values()))
        meshes.append(m)

    # Strip the shared prefix so the slicer's part list reads "ring / rotor /
    # letter" rather than three near-identical 30-character filenames. Picking
    # a part to recolour is the whole point of shipping it assembled.
    stems = [p.stem for p, _ in flat]
    prefix = ""
    if len(stems) > 1:
        first = stems[0]
        for i in range(len(first), 0, -1):
            if all(t.startswith(first[:i]) for t in stems):
                prefix = first[:i]
                break
    names = [(t[len(prefix):].strip("_-") or t) for t in stems] if prefix else stems
    colours = [c for _, c in flat]
    mat_id = 100
    bases = "".join(f'<base name="{n}" displaycolor="{c if c.startswith("#") else "#"+c}FF"/>'
                    for n, c in zip(names, colours))
    materials = f'<basematerials id="{mat_id}">{bases}</basematerials>'

    objs = [_mesh_xml(i + 1, m, n, mat_id, i)
            for i, (m, n) in enumerate(zip(meshes, names))]

    # Each group becomes one printed object. A group of one is that mesh; a
    # group of several is a <components> assembly, so every part keeps its own
    # coordinates and the object arrives already aligned.
    next_id = len(meshes) + 1
    group_ids, idx = [], 0
    for g in groups:
        ids = list(range(idx + 1, idx + 1 + len(g)))
        idx += len(g)
        if len(ids) == 1:
            group_ids.append(ids[0])
        else:
            comps = "".join(f'<component objectid="{i}"/>' for i in ids)
            objs.append(f'<object id="{next_id}" type="model" name="{out_path.stem}">'
                        f'<components>{comps}</components></object>')
            group_ids.append(next_id)
            next_id += 1

    if mode == "assembly":
        items = f'<item objectid="{group_ids[0]}"/>'
        layout = f"one object, {len(meshes)} parts"
    else:
        # Laid out left to right with a real gap, so they arrive arranged
        # rather than stacked on the origin.
        items, x, gi = "", 0.0, 0
        for g, oid in zip(groups, group_ids):
            gm = meshes[gi:gi + len(g)]
            gi += len(g)
            w = float(max(m.bounds[1][0] for m in gm) - min(m.bounds[0][0] for m in gm))
            if items:
                x += gap + w / 2.0
            items += (f'<item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 '
                      f'{x:.4f} 0 0"/>')
            x += w / 2.0
        layout = (f"{len(groups)} separate objects on one plate "
                  f"({len(meshes)} parts total)")

    model = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
             f'<model unit="millimeter" xml:lang="en-US" xmlns="{_NS}">'
             f'<resources>{materials}{"".join(objs)}</resources>'
             f'<build>{items}</build></model>')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("3D/3dmodel.model", model)
    return {"file": str(out_path), "mode": mode, "layout": layout,
            "parts": names, "colours": colours,
            "triangles": int(sum(len(m.faces) for m in meshes))}


def main() -> None:
    ap = argparse.ArgumentParser(description="Assemble one print-ready 3MF.")
    ap.add_argument("out")
    ap.add_argument("parts", nargs="+",
                    help='mesh.stl[:#RRGGBB] per part; "+" starts a new object')
    ap.add_argument("--plate", action="store_true",
                    help="separate objects on one plate (a container and its lid) "
                         "instead of one assembled object")
    ap.add_argument("--gap", type=float, default=6.0)
    a = ap.parse_args()

    palette = ["#2B2F38", "#F2F0E9", "#E0553D", "#7BA7C2", "#8BA888", "#D4A96A"]
    groups, cur, i = [], [], 0
    for spec in a.parts:
        if spec == "+":
            if cur:
                groups.append(cur); cur = []
            continue
        path, _, colour = spec.partition(":")
        if not Path(path).exists():
            print(f"no such mesh: {path}", file=sys.stderr)
            sys.exit(1)
        cur.append((Path(path), colour or palette[i % len(palette)]))
        i += 1
    if cur:
        groups.append(cur)
    if len(groups) > 1 and not a.plate:
        print('"+" groups only make sense with --plate; parts that assemble into '
              'ONE object need no separator', file=sys.stderr)
        sys.exit(1)

    r = assemble(Path(a.out), groups, "plate" if a.plate else "assembly", a.gap)
    print(f'{r["file"]}  --  {r["layout"]}')
    for n, c in zip(r["parts"], r["colours"]):
        print(f'   {n:28s} {c}')
    print(f'   {r["triangles"]} triangles')


if __name__ == "__main__":
    main()
