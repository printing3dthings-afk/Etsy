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


def _volume_meta(name: str, extruder: int) -> str:
    return (f'<metadata type="volume" key="name" value="{name}"/>'
            f'<metadata type="volume" key="volume_type" value="ModelPart"/>'
            f'<metadata type="volume" key="extruder" value="{extruder}"/>')


def _object_xml(obj_id: int, meshes: list, names: list) -> tuple[str, str, str]:
    """One <object> holding every part, plus the two config flavours that name
    the parts as VOLUMES.

    This is the whole trick, and getting it wrong is invisible. A <components>
    assembly LOOKS right and round-trips through PrusaSlicer as N SEPARATE
    OBJECTS -- verified 2026-09-09: a 5-part dumpling clicker came back as
    "objects: 5, components: 0, items: 5", so the slicer offered five objects
    to arrange rather than one object with five colourable parts. A real
    multi-part object is ONE mesh whose parts are declared as triangle RANGES
    in Metadata/*.config. That is exactly how PrusaSlicer itself writes one.
    """
    verts, tris, ranges, base = [], [], [], 0
    for m in meshes:
        off = len(verts)
        verts.extend(m.vertices.tolist())
        for a, b, c in m.faces:
            tris.append((a + off, b + off, c + off))
        ranges.append((base, len(tris) - 1))
        base = len(tris)

    v = "".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in verts)
    t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
    obj = (f'<object id="{obj_id}" type="model">'
           f'<mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')

    vols = "".join(
        f'<volume firstid="{lo}" lastid="{hi}">{_volume_meta(n, i + 1)}</volume>'
        for i, (n, (lo, hi)) in enumerate(zip(names, ranges)))
    slic3r = (f'<object id="{obj_id}" instances_count="1">'
              f'<metadata type="object" key="name" value="{names[0]}"/>{vols}</object>')

    # Bambu Studio / OrcaSlicer read their own file. Parts are indexed 1..N and
    # carry the extruder directly, which is what makes the model open already
    # coloured instead of all one filament.
    parts = "".join(
        f'<part id="{i+1}" subtype="normal_part">'
        f'<metadata key="name" value="{n}"/>'
        f'<metadata key="extruder" value="{i+1}"/></part>'
        for i, n in enumerate(names))
    bambu = (f'<object id="{obj_id}">'
             f'<metadata key="name" value="{names[0]}"/>'
             f'<metadata key="extruder" value="1"/>{parts}</object>')
    return obj, slic3r, bambu


def assemble(out_path: Path, groups: list[list[tuple[Path, str]]],
             mode: str = "assembly", gap: float = 6.0) -> dict:
    """groups: each inner list is one printed object, made of one or more
    colour parts. In assembly mode there is exactly one group."""
    loaded = []
    for g in groups:
        ms = []
        for path, _ in g:
            m = trimesh.load(str(path), force="mesh")
            if isinstance(m, trimesh.Scene):
                m = trimesh.util.concatenate(tuple(m.geometry.values()))
            ms.append(m)
        loaded.append(ms)

    stems = [p.stem for g in groups for p, _ in g]
    # Only ever cut at an underscore. The naive longest-common-prefix found
    # "dumpling_clicker_ba" across bao/bao_eyes/basket and turned the parts into
    # "o", "o_eyes" and "sket".
    prefix = ""
    if len(stems) > 1:
        first = stems[0]
        for i in range(len(first), 0, -1):
            if all(t.startswith(first[:i]) for t in stems):
                prefix = first[:i]
                break
        prefix = prefix[:prefix.rfind("_") + 1] if "_" in prefix else ""
    flat_names = [(t[len(prefix):].strip("_-") or t) for t in stems] if prefix else stems
    colours = [c for g in groups for _, c in g]

    names, k = [], 0
    for g in groups:
        names.append(flat_names[k:k + len(g)])
        k += len(g)

    objs, slic3rs, bambus, items = [], [], [], ""
    x = 0.0
    for gi, (ms, ns) in enumerate(zip(loaded, names)):
        o, sl, bm = _object_xml(gi + 1, ms, ns)
        objs.append(o); slic3rs.append(sl); bambus.append(bm)
        if mode == "assembly":
            items += f'<item objectid="{gi+1}"/>'
        else:
            w = float(max(m.bounds[1][0] for m in ms) - min(m.bounds[0][0] for m in ms))
            if items:
                x += gap + w / 2.0
            items += (f'<item objectid="{gi+1}" transform="1 0 0 0 1 0 0 0 1 '
                      f'{x:.4f} 0 0"/>')
            x += w / 2.0

    model = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
             f'<model unit="millimeter" xml:lang="en-US" xmlns="{_NS}">'
             f'<resources>{"".join(objs)}</resources>'
             f'<build>{items}</build></model>')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("Metadata/Slic3r_PE_model.config",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>'
                   + "".join(slic3rs) + "</config>")
        z.writestr("Metadata/model_settings.config",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>'
                   + "".join(bambus) + "</config>")
    n_parts = sum(len(g) for g in groups)
    layout = (f"one object, {n_parts} parts" if mode == "assembly"
              else f"{len(groups)} separate objects on one plate ({n_parts} parts total)")
    return {"file": str(out_path), "mode": mode, "layout": layout,
            "parts": flat_names, "colours": colours,
            "triangles": int(sum(len(m.faces) for ms in loaded for m in ms))}


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
