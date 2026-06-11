#!/usr/bin/env python3
"""
Build SS1001 Vol 2 customer download ZIP:
  5 additional America 250th Anniversary 3D sign designs

Output: data/3d_print_signs/america_250/SS1001_america250_3dprint_pack_vol2.zip

Run:  python tools/build_ss1001_vol2_zip.py
"""

from __future__ import annotations
import io
import re
import zipfile
from pathlib import Path

import cairosvg
import numpy as np
import trimesh
from PIL import Image

ROOT = Path(__file__).parent.parent
DESIGNS_DIR = ROOT / "data" / "3d_print_signs" / "america_250"
OUT_ZIP = DESIGNS_DIR / "SS1001_america250_3dprint_pack_vol2.zip"

DESIGNS = [
    ("01_america250_flag_plaque",  "Flag Plaque"),
    ("02_america250_medallion",    "Medallion"),
    ("03_america250_freedom",      "Freedom"),
    ("04_america250_4th_of_july",  "4th of July"),
    ("06_america250_shield",       "Shield"),
]

Z_BASE  = (0.0, 4.0)
Z_RAISE = (4.0, 6.0)
PPM_BASE   = 0.5
PPM_DESIGN = 1.5


def svg_to_mesh(svg_path: Path, z_bottom: float, z_top: float,
                px_per_mm: float = 1.0) -> trimesh.Trimesh | None:
    content = svg_path.read_text(encoding="utf-8")
    vb = re.search(r'viewBox="0 0 (\S+) (\S+)"', content)
    if not vb:
        print(f"  WARNING: no viewBox in {svg_path.name}")
        return None
    W_mm, H_mm = float(vb.group(1)), float(vb.group(2))
    W_px = max(1, int(W_mm * px_per_mm))
    H_px = max(1, int(H_mm * px_per_mm))

    png_bytes = cairosvg.svg2png(bytestring=content.encode(),
                                  output_width=W_px, output_height=H_px)
    arr = np.array(Image.open(io.BytesIO(png_bytes)).convert("RGBA"))
    mask = arr[:, :, 3] > 128

    if not np.any(mask):
        return None

    mm_per_px = 1.0 / px_per_mm
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    v_idx: dict[tuple, int] = {}

    def v(ix: int, iy: int, z: float) -> int:
        k = (ix, iy, z)
        if k not in v_idx:
            v_idx[k] = len(vertices)
            vertices.append([ix * mm_per_px, iy * mm_per_px, z])
        return v_idx[k]

    def quad(a: int, b: int, c: int, d: int) -> None:
        faces.append([a, b, c])
        faces.append([a, c, d])

    ys, xs = np.where(mask)
    filled: set[tuple[int, int]] = set(zip(xs.tolist(), ys.tolist()))

    for ix, iy in filled:
        a = v(ix,   iy,   z_top);    b = v(ix+1, iy,   z_top)
        c = v(ix+1, iy+1, z_top);    d = v(ix,   iy+1, z_top)
        e = v(ix,   iy,   z_bottom); f = v(ix+1, iy,   z_bottom)
        g = v(ix+1, iy+1, z_bottom); h = v(ix,   iy+1, z_bottom)

        quad(a, b, c, d)
        quad(h, g, f, e)
        if (ix-1, iy) not in filled: quad(a, d, h, e)
        if (ix+1, iy) not in filled: quad(b, f, g, c)
        if (ix,   iy-1) not in filled: quad(e, f, b, a)
        if (ix,   iy+1) not in filled: quad(d, c, g, h)

    return trimesh.Trimesh(
        vertices=np.array(vertices, dtype=np.float32),
        faces=np.array(faces, dtype=np.int32),
        process=True,
    )


_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    '</Types>'
)
_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
    '</Relationships>'
)


def _build_3mf_xml(named_meshes: list[tuple[str, trimesh.Trimesh]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'unit="millimeter" xml:lang="en-US">',
        "  <resources>",
    ]
    build_items: list[str] = []
    for obj_id, (name, mesh) in enumerate(named_meshes, 1):
        lines += [
            f'    <object id="{obj_id}" name="{name}" type="model">',
            "      <mesh>",
            "        <vertices>",
        ]
        for x, y, z in mesh.vertices:
            lines.append(f'          <vertex x="{x:.2f}" y="{y:.2f}" z="{z:.2f}"/>')
        lines += ["        </vertices>", "        <triangles>"]
        for v0, v1, v2 in mesh.faces:
            lines.append(f'          <triangle v1="{v0}" v2="{v1}" v3="{v2}"/>')
        lines += ["        </triangles>", "      </mesh>", "    </object>"]
        build_items.append(f'    <item objectid="{obj_id}"/>')

    lines += ["  </resources>", "  <build>"] + build_items + ["  </build>", "</model>"]
    return "\n".join(lines)


def build_3mf_bytes(named_meshes: list[tuple[str, trimesh.Trimesh]]) -> bytes:
    xml = _build_3mf_xml(named_meshes)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("3D/3dmodel.model", xml)
    return buf.getvalue()


README_VOL2 = """\
SS1001 Vol 2 — America 250th Anniversary 3D Print Sign Pack (Designs 6–10)
OnBrandCraftz — Personal use + gifts only. Not for commercial printing/resale.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DESIGNS IN THIS VOLUME
━━━━━━━━━━━━━━━━━━━━━━
6. Flag Plaque     — American flag layout, "250 YEARS · AMERICA 1776–2026"
7. Medallion       — Circular "AMERICA · 250 · 1776–2026" with star ring
8. Freedom         — "LET FREEDOM RING" bold blue and red block layout
9. 4th of July     — "HAPPY 4TH OF JULY" in patriotic band layout
10. Shield         — Pentagon/shield shape, "AMERICA 250 · 1776–2026"

For designs 1–5 see the companion file: SS1001_america250_3dprint_pack_vol1.zip

━━━━━━━━━━━━━━━━━━
WHAT'S IN THIS ZIP
━━━━━━━━━━━━━━━━━━
5 design folders, each containing:
  • [design].3mf  — EASIEST: all color layers pre-assembled, Z-heights set.
                    Open in Bambu Studio, assign AMS slots, slice, print.
  • layer01_base_WHITE.svg  — White base plate  (prints at 4mm tall)
  • layer02_[COLOR].svg     — First design color  (prints at 2mm on top)
  • layer03_[COLOR].svg     — Second design color (prints at 2mm on top)

Note: Shield design has layer02_blue_BLUE + layer03_red_RED (reversed from other designs).
The .3mf handles this automatically — just assign White/Red/Blue to the correct parts.

━━━━━━━━━━━━━━━━━━
OPTION 1 — EASIEST: USE THE .3MF FILE
━━━━━━━━━━━━━━━━━━
1. Open Bambu Studio
2. File → Open → select [design].3mf
3. Three parts appear pre-positioned: base (0–4mm), color layer 1 (4–6mm), color layer 2 (4–6mm)
4. In the Filament list (left panel), click "+" to add 3 colors
5. Click each part in the Objects panel → assign to its filament color:
     base_WHITE → White or Cream PLA
     layer_RED  → Deep Red PLA
     layer_BLUE → Navy Blue PLA
6. Slice and print!

━━━━━━━━━━━━━━━━━━
OPTION 2 — SVG LAYERS (for custom sizing or other slicers)
━━━━━━━━━━━━━━━━━━
1. In Bambu Studio, drag & drop layer01_base_WHITE.svg → set height 4mm
2. Right-click the model → Add Part → drag the second layer SVG → set height 2mm
   → In Object panel, set Z-offset to 4mm (so it sits on top of the base)
3. Repeat for the third layer SVG: height 2mm, Z-offset 4mm
4. Add 3 colors in Filament list, assign one color per SVG part
5. Use the Color Painting tool (press N) if needed → Fill tool to refine regions
6. Slice and print!

Scale tip: select all 3 parts (Ctrl+A) before scaling to keep them aligned.

━━━━━━━━━━━━━━━━━━
PRINTING TIPS
━━━━━━━━━━━━━━━━━━
• FLIP THE MODEL so the design face is DOWN on a textured PEI plate.
  This gives a perfectly smooth, layer-line-free front face.
  In Bambu Studio: right-click → Place on Face → select the top face.

• Recommended filaments:
    White/Cream PLA for the base
    Deep Red PLA for the red layer
    Navy Blue PLA for the blue layer

• Layer height: 0.2mm recommended. Outer wall speed: 50mm/s for best quality.

• No AMS? Use filament swaps at layer 4mm (the slicer will prompt you).

━━━━━━━━━━━━━━━━━━
SUPPORT
━━━━━━━━━━━━━━━━━━
Questions? Message us on Etsy: OnBrandCraftz
Printing3dthings@outlook.com

© OnBrandCraftz. Personal use + gifts only.
Not for resale, commercial printing, or redistribution.
"""


def main() -> None:
    print("SS1001 Vol 2 ZIP Builder")
    print("=" * 60)

    zip_contents: list[tuple[str, bytes]] = []
    ok = 0
    errors: list[str] = []

    for slug, display_name in DESIGNS:
        design_dir = DESIGNS_DIR / slug
        if not design_dir.exists():
            errors.append(f"Missing design dir: {design_dir}")
            continue

        layers = sorted(design_dir.glob("layer*.svg"))
        if not layers:
            errors.append(f"No layer SVGs in {slug}")
            continue

        print(f"\n  Building {display_name} ({slug}) — {len(layers)} layers")

        named_meshes: list[tuple[str, trimesh.Trimesh]] = []
        for i, lf in enumerate(layers):
            is_base = (i == 0)
            ppm = PPM_BASE if is_base else PPM_DESIGN
            zb, zt = Z_BASE if is_base else Z_RAISE

            m = svg_to_mesh(lf, zb, zt, px_per_mm=ppm)
            if m is None:
                errors.append(f"  Empty mesh: {lf}")
                continue
            named_meshes.append((lf.stem, m))
            print(f"    {lf.name}: {len(m.vertices)} verts, {len(m.faces)} faces")

        if not named_meshes:
            errors.append(f"No meshes built for {slug}")
            continue

        # ZIP folder name — use design number 6-10 for vol2
        vol2_nums = {
            "01_america250_flag_plaque": 6,
            "02_america250_medallion":   7,
            "03_america250_freedom":     8,
            "04_america250_4th_of_july": 9,
            "06_america250_shield":      10,
        }
        num = vol2_nums.get(slug, 0)
        short_name = slug.split("america250_", 1)[-1]
        folder = f"SS1001_{num}_{short_name}"

        threemf_name = f"SS1001_{short_name}.3mf"
        threemf_bytes = build_3mf_bytes(named_meshes)
        zip_contents.append((f"{folder}/{threemf_name}", threemf_bytes))
        print(f"    3MF: {len(threemf_bytes)//1024} KB")

        for lf in layers:
            svg_data = lf.read_bytes()
            zip_contents.append((f"{folder}/{lf.name}", svg_data))

        ok += 1

    zip_contents.append(("README_vol2.txt", README_VOL2.encode("utf-8")))

    print(f"\n  Writing ZIP: {OUT_ZIP}")
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for arcname, data in zip_contents:
            zf.writestr(arcname, data)

    zip_size_mb = OUT_ZIP.stat().st_size / 1024 / 1024
    print(f"  ZIP size: {zip_size_mb:.1f} MB")

    if zip_size_mb > 20:
        print(f"  ✗ ERROR: ZIP exceeds Etsy 20MB limit! ({zip_size_mb:.1f} MB)")
    else:
        print(f"  ✓ ZIP under 20MB limit")

    print(f"\n  ✓ {ok}/{len(DESIGNS)} designs built")
    if errors:
        for e in errors:
            print(f"  ✗ {e}")

    print("=" * 60)


if __name__ == "__main__":
    main()
