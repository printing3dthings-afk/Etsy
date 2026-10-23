#!/usr/bin/env python3
"""
tools/make_color_3mf.py -- assemble several meshes into ONE 3MF with real
per-triangle colours and more than one object.

Added 2026-09-11, for a concrete reason. OpenSCAD's own 3MF export writes
geometry and nothing else: no <basematerials>, no colours, and every
top-level object merged into a single <object>. The tombstone assembly
exported that way came out as one fused shell (the plaque's back face is
coincident with its pocket floor, so CGAL unioned them) with the plaque
standing vertical inside the stone rather than on the bed -- an assembly
picture saved with a print file's extension. Verified by unzipping it:
`basematerials` 0, `object` 1.

This takes meshes that are ALREADY in print pose and already laid out on
the plate, and writes a 3MF that a slicer can actually open:

    python3 tools/make_color_3mf.py -o out.3mf \\
        --object stone  --region socle.stl:#2B2B2E --region body.stl:#8C8C86 \\
        --object plaque --region field.stl:#3A2A18 --region letters.stl:#C08A2E

Each --object starts a new printed object; the --region entries after it are
colour regions WITHIN that object, welded into one mesh whose triangles carry
per-triangle material indices. That distinction is the point: the socle and
the stone body are one printed object with a filament change partway up, not
two objects, and a 3MF that models them as two objects would let a slicer
move them apart.

Colours are sRGB hex (#RRGGBB or #RRGGBBAA). A slicer maps 3MF base materials
onto filament slots in order, so region order here is filament order there.

This writes the 3MF container by hand (it is a zip of three XML parts) rather
than taking a dependency; lib3mf is not installed in this image and the core
+ material spec needed here is small.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""


class ColorMeshError(Exception):
    pass


def _norm_hex(c: str) -> str:
    c = c.strip().lstrip("#").upper()
    if len(c) == 6:
        c += "FF"
    if len(c) != 8 or any(ch not in "0123456789ABCDEF" for ch in c):
        raise ColorMeshError(f"colour must be #RRGGBB or #RRGGBBAA, got {c!r}")
    return "#" + c


def build(objects, output_path: Path) -> Path:
    """objects is [(name, [(mesh_path, "#RRGGBBAA"), ...]), ...]."""
    import trimesh

    if not objects:
        raise ColorMeshError("no objects given")

    materials: list[tuple[str, str]] = []   # (name, hex) in filament order
    obj_xml: list[str] = []

    for obj_i, (name, regions) in enumerate(objects):
        if not regions:
            raise ColorMeshError(f"object {name!r} has no regions")
        verts: list[tuple[float, float, float]] = []
        tris: list[tuple[int, int, int, int]] = []   # v1,v2,v3,material index
        for mesh_path, color in regions:
            mp = Path(mesh_path)
            if not mp.exists():
                raise ColorMeshError(f"mesh not found: {mp}")
            m = trimesh.load(mp, force="mesh")
            if m.faces is None or len(m.faces) == 0:
                raise ColorMeshError(f"{mp} has no triangles")
            mat_index = len(materials)
            materials.append((f"{name}:{mp.stem}", color))
            base = len(verts)
            verts.extend((float(x), float(y), float(z)) for x, y, z in m.vertices)
            tris.extend((int(a) + base, int(b) + base, int(c) + base, mat_index)
                        for a, b, c in m.faces)

        v_xml = "".join(
            f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in verts)
        # pid points at the single basematerials group; p1 alone sets all three
        # corners, which is what a flat-shaded region wants.
        t_xml = "".join(
            f'<triangle v1="{a}" v2="{b}" v3="{c}" pid="1" p1="{m}"/>'
            for a, b, c, m in tris)
        obj_xml.append(
            f'<object id="{obj_i + 2}" name="{escape(name)}" type="model" '
            f'pid="1" pindex="{tris[0][3]}">'
            f"<mesh><vertices>{v_xml}</vertices>"
            f"<triangles>{t_xml}</triangles></mesh></object>")

    base_xml = "".join(
        f'<base name="{escape(n)}" displaycolor="{c}"/>' for n, c in materials)
    items = "".join(f'<item objectid="{i + 2}"/>' for i in range(len(objects)))
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">'
        f'<resources><basematerials id="1">{base_xml}</basematerials>'
        f'{"".join(obj_xml)}</resources>'
        f"<build>{items}</build></model>")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/3dmodel.model", model)
    return output_path


def _cli() -> None:
    ap = argparse.ArgumentParser(
        description="Assemble meshes into one 3MF with per-triangle colours.")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--object", action="append", default=[], metavar="NAME",
                    help="Start a new printed object. Regions that follow belong to it.")
    ap.add_argument("--region", action="append", default=[], metavar="PATH:#RRGGBB",
                    help="A colour region of the current object.")
    args, argv = ap.parse_known_args()
    if argv:
        ap.error(f"unexpected arguments: {argv}")

    # argparse loses the interleaving of --object and --region, so re-walk argv.
    objects: list[tuple[str, list]] = []
    it = iter(sys.argv[1:])
    for tok in it:
        if tok == "--object":
            objects.append((next(it), []))
        elif tok == "--region":
            if not objects:
                ap.error("--region before any --object")
            spec = next(it)
            path, _, color = spec.rpartition(":")
            if not path:
                ap.error(f"--region wants PATH:#RRGGBB, got {spec!r}")
            objects[-1][1].append((path, _norm_hex(color)))
    try:
        out = build(objects, Path(args.output))
    except (ColorMeshError, Exception) as exc:   # trimesh raises its own types
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"wrote -> {out}")


if __name__ == "__main__":
    _cli()
