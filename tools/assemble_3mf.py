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
  assembly  one object with N parts, so a filament can be set per part.
            Written as one mesh with triangle ranges (--layout prusa, the
            default: what PrusaSlicer reads) or as <components> (--layout
            bambu: the only form Bambu Studio builds parts from).
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


def _object_xml(obj_id: int, meshes: list, names: list,
                extruders: list) -> tuple[str, str, str]:
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
        f'<volume firstid="{lo}" lastid="{hi}">{_volume_meta(n, e)}</volume>'
        for n, e, (lo, hi) in zip(names, extruders, ranges))
    slic3r = (f'<object id="{obj_id}" instances_count="1">'
              f'<metadata type="object" key="name" value="{names[0]}"/>{vols}</object>')

    # Bambu Studio / OrcaSlicer read model_settings.config, but NOT from this
    # layout: their importer builds parts only from <components>, so this
    # opens there as one part on filament 1 (verified in the Bambu Studio
    # 02.08.02.61 CLI, 2026-09-27; the GUI shares the importer). Use
    # layout="bambu" for a file meant for Bambu Studio.
    parts = "".join(
        f'<part id="{i+1}" subtype="normal_part">'
        f'<metadata key="name" value="{n}"/>'
        f'<metadata key="extruder" value="{e}"/></part>'
        for i, (n, e) in enumerate(zip(names, extruders)))
    bambu = (f'<object id="{obj_id}">'
             f'<metadata key="name" value="{names[0]}"/>'
             f'<metadata key="extruder" value="{extruders[0]}"/>{parts}</object>')
    return obj, slic3r, bambu


def _mesh_xml(obj_id: int, m) -> str:
    v = "".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in m.vertices)
    t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
    return (f'<object id="{obj_id}" type="model">'
            f'<mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')


def _bambu_object_xml(first_id: int, meshes: list, names: list,
                      extruders: list) -> tuple[str, int, str, int]:
    """The layout Bambu Studio can read parts from: one mesh object per part
    and a parent object of <components>.

    Bambu Studio builds parts ONLY from components -- its importer never calls
    the triangle-range path (bbs_3mf.cpp, _generate_volumes has no caller as of
    v02.08.02.61). Handed the single-mesh layout above, the chapel sliced as
    ONE part on filament 1; in this layout, four parts on four filaments
    (2026-09-27, tools/bambu_slicer.py). PrusaSlicer reads this layout as N
    separate objects instead (see _object_xml), which is why both exist.
    Returns (object xml, parent id, model_settings xml, next free id)."""
    objs, comps, parts = [], [], []
    for i, (m, n, e) in enumerate(zip(meshes, names, extruders)):
        oid = first_id + i
        objs.append(_mesh_xml(oid, m))
        comps.append(f'<component objectid="{oid}"/>')
        parts.append(f'<part id="{oid}" subtype="normal_part">'
                     f'<metadata key="name" value="{n}"/>'
                     f'<metadata key="extruder" value="{e}"/></part>')
    parent = first_id + len(meshes)
    objs.append(f'<object id="{parent}" type="model"><components>{"".join(comps)}'
                f'</components></object>')
    cfg = (f'<object id="{parent}"><metadata key="name" value="{names[0]}"/>'
           f'<metadata key="extruder" value="{extruders[0]}"/>{"".join(parts)}</object>')
    return "".join(objs), parent, cfg, parent + 1


def assemble(out_path: Path, groups: list[list[tuple[Path, str]]],
             mode: str = "assembly", gap: float = 6.0, layout: str = "prusa") -> dict:
    """groups: each inner list is one printed object, made of one or more
    colour parts. In assembly mode there is exactly one group.
    layout: "prusa" (one mesh, parts as triangle ranges) or "bambu" (parts as
    components) -- each slicer reads parts from only one of them."""
    if layout not in ("prusa", "bambu"):
        raise ValueError(f"layout must be prusa or bambu, not {layout!r}")
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

    # One filament slot per distinct colour across the WHOLE plate (2026-09-26).
    # Numbering restarted at 1 for every object, so the second object on a
    # plate always landed on slot 1: the haunted post office's slate lid came
    # out in the brick of the house, and the bayonet jar's orange lid in the
    # base's blue. Same colour, same slot; a box and its lid in one colour
    # share one.
    slot = {}
    extruders = [[slot.setdefault(c.upper(), len(slot) + 1) for _, c in g] for g in groups]

    objs, slic3rs, bambus, items = [], [], [], ""
    x = 0.0
    next_id = 1
    for gi, (ms, ns, ex) in enumerate(zip(loaded, names, extruders)):
        if layout == "bambu":
            o, item_id, bm, next_id = _bambu_object_xml(next_id, ms, ns, ex)
        else:
            o, sl, bm = _object_xml(gi + 1, ms, ns, ex)
            item_id = gi + 1
            slic3rs.append(sl)
        objs.append(o); bambus.append(bm)
        if mode == "assembly":
            items += f'<item objectid="{item_id}"/>'
        else:
            w = float(max(m.bounds[1][0] for m in ms) - min(m.bounds[0][0] for m in ms))
            if items:
                x += gap + w / 2.0
            items += (f'<item objectid="{item_id}" transform="1 0 0 0 1 0 0 0 1 '
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
        if slic3rs:
            z.writestr("Metadata/Slic3r_PE_model.config",
                       '<?xml version="1.0" encoding="UTF-8"?>\n<config>'
                       + "".join(slic3rs) + "</config>")
        z.writestr("Metadata/model_settings.config",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>'
                   + "".join(bambus) + "</config>")
    n_parts = sum(len(g) for g in groups)
    layout_text = (f"one object, {n_parts} parts" if mode == "assembly"
              else f"{len(groups)} separate objects on one plate ({n_parts} parts total)")
    return {"file": str(out_path), "mode": mode, "layout": layout_text,
            "slicer_layout": layout,
            "parts": flat_names, "colours": colours,
            "extruders": [e for ex in extruders for e in ex],
            "triangles": int(sum(len(m.faces) for ms in loaded for m in ms))}


def to_bambu_layout(src: Path, dst: Path) -> dict:
    """Rewrite a single-mesh 3MF (parts as triangle ranges, the layout
    PrusaSlicer reads) as components (the only layout Bambu Studio builds parts
    from), keeping every part's name and extruder and every item's transform.

    For 3MFs already in the repo: re-exporting them from OpenSCAD would need
    the original part STLs and colours, which not every one still has. The
    triangle ranges in Metadata/Slic3r_PE_model.config are the authority for
    where each part starts and ends."""
    import re
    import xml.etree.ElementTree as ET
    z = zipfile.ZipFile(src)
    root = ET.fromstring(z.read("3D/3dmodel.model"))
    ns = {"m": _NS}
    cfg = z.read("Metadata/Slic3r_PE_model.config").decode() \
        if "Metadata/Slic3r_PE_model.config" in z.namelist() else ""
    volumes = {}
    for oid, body in re.findall(r'<object id="(\d+)"[^>]*>(.*?)</object>', cfg, re.S):
        vs = []
        for lo, hi, meta in re.findall(r'<volume firstid="(\d+)" lastid="(\d+)">(.*?)</volume>', body, re.S):
            name = re.search(r'key="name" value="([^"]*)"', meta)
            ext = re.search(r'key="extruder" value="(\d+)"', meta)
            vs.append((int(lo), int(hi), name.group(1) if name else f"part{len(vs) + 1}",
                       int(ext.group(1)) if ext else 1))
        volumes[oid] = vs

    objs, cfgs, id_map, next_id, n_parts = [], [], {}, 1, 0
    for obj in root.find("m:resources", ns).findall("m:object", ns):
        oid = obj.get("id")
        mesh = obj.find("m:mesh", ns)
        if mesh is None:
            raise ValueError(f"{src}: object {oid} has no mesh (already components?)")
        verts = [(v.get("x"), v.get("y"), v.get("z"))
                 for v in mesh.find("m:vertices", ns).findall("m:vertex", ns)]
        tris = [(int(t.get("v1")), int(t.get("v2")), int(t.get("v3")))
                for t in mesh.find("m:triangles", ns).findall("m:triangle", ns)]
        vs = volumes.get(oid) or [(0, len(tris) - 1, f"object{oid}", 1)]
        comps, parts = [], []
        for lo, hi, name, ext in vs:
            sub = tris[lo:hi + 1]
            used = sorted({i for t in sub for i in t})
            remap = {o: n for n, o in enumerate(used)}
            v = "".join(f'<vertex x="{verts[i][0]}" y="{verts[i][1]}" z="{verts[i][2]}"/>' for i in used)
            t = "".join(f'<triangle v1="{remap[a]}" v2="{remap[b]}" v3="{remap[c]}"/>' for a, b, c in sub)
            objs.append(f'<object id="{next_id}" type="model"><mesh><vertices>{v}</vertices>'
                        f'<triangles>{t}</triangles></mesh></object>')
            comps.append(f'<component objectid="{next_id}"/>')
            parts.append(f'<part id="{next_id}" subtype="normal_part">'
                         f'<metadata key="name" value="{name}"/>'
                         f'<metadata key="extruder" value="{ext}"/></part>')
            next_id += 1
            n_parts += 1
        parent = next_id
        next_id += 1
        id_map[oid] = parent
        objs.append(f'<object id="{parent}" type="model"><components>{"".join(comps)}'
                    f'</components></object>')
        cfgs.append(f'<object id="{parent}"><metadata key="name" value="{vs[0][2]}"/>'
                    f'<metadata key="extruder" value="{vs[0][3]}"/>{"".join(parts)}</object>')

    items = ""
    for it in root.find("m:build", ns).findall("m:item", ns):
        tf = f' transform="{it.get("transform")}"' if it.get("transform") else ""
        items += f'<item objectid="{id_map[it.get("objectid")]}"{tf}/>'
    model = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
             f'<model unit="millimeter" xml:lang="en-US" xmlns="{_NS}">'
             f'<resources>{"".join(objs)}</resources><build>{items}</build></model>')
    dst.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as out:
        out.writestr("[Content_Types].xml", _CONTENT_TYPES)
        out.writestr("_rels/.rels", _RELS)
        out.writestr("3D/3dmodel.model", model)
        out.writestr("Metadata/model_settings.config",
                     '<?xml version="1.0" encoding="UTF-8"?>\n<config>' + "".join(cfgs) + "</config>")
    return {"objects": len(id_map), "parts": n_parts,
            "extruders": sorted({e for vs in volumes.values() for *_, e in vs} or {1})}


def main() -> None:
    ap = argparse.ArgumentParser(description="Assemble one print-ready 3MF.")
    ap.add_argument("out")
    ap.add_argument("parts", nargs="+",
                    help='mesh.stl[:#RRGGBB] per part; "+" starts a new object')
    ap.add_argument("--plate", action="store_true",
                    help="separate objects on one plate (a container and its lid) "
                         "instead of one assembled object")
    ap.add_argument("--gap", type=float, default=6.0)
    ap.add_argument("--layout", choices=("prusa", "bambu"), default="prusa",
                    help="which slicer's part layout to write (see the module docstring)")
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

    r = assemble(Path(a.out), groups, "plate" if a.plate else "assembly", a.gap, a.layout)
    print(f'{r["file"]}  --  {r["layout"]}')
    for n, c, e in zip(r["parts"], r["colours"], r["extruders"]):
        print(f'   {n:28s} {c}  slot {e}')
    print(f'   {r["triangles"]} triangles')


if __name__ == "__main__":
    main()
